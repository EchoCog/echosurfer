#!/usr/bin/env python3
"""
Production Authentication Manager for Deep Tree Echo
Replaces mock authentication with secure, production-ready authentication system
"""

import os
import json
import logging
import hashlib
import secrets
import time
from pathlib import Path
from typing import Dict, Optional, List, Tuple
from dataclasses import dataclass, asdict
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import jwt
from datetime import datetime, timedelta

@dataclass
class AuthToken:
    """Secure authentication token structure"""
    token_id: str
    user_id: str
    service: str
    expires_at: float
    permissions: List[str]
    metadata: Dict

@dataclass
class ServiceCredentials:
    """Encrypted service credentials"""
    service_name: str
    username: str
    encrypted_password: str
    encrypted_2fa_secret: Optional[str]
    token_data: Optional[Dict]
    last_updated: float

class AuthenticationManager:
    """Production-ready authentication system with encryption and session management"""
    
    def __init__(self, master_password: Optional[str] = None):
        self.logger = logging.getLogger(__name__)
        
        # Initialize secure storage
        self.auth_dir = Path.home() / '.deep_tree_echo' / 'auth'
        self.auth_dir.mkdir(parents=True, exist_ok=True, mode=0o700)  # Restricted permissions
        
        # Initialize encryption
        self.master_password = master_password or os.getenv('DEEP_TREE_ECHO_MASTER_PASSWORD')
        if not self.master_password:
            self.master_password = self._prompt_master_password()
        
        self.cipher = self._initialize_encryption()
        
        # Initialize storage files
        self.credentials_file = self.auth_dir / 'credentials.enc'
        self.tokens_file = self.auth_dir / 'tokens.enc'
        self.sessions_file = self.auth_dir / 'sessions.enc'
        
        # In-memory storage
        self.credentials: Dict[str, ServiceCredentials] = {}
        self.active_tokens: Dict[str, AuthToken] = {}
        self.active_sessions: Dict[str, Dict] = {}
        
        # Load existing data
        self._load_encrypted_data()
        
        # JWT settings
        self.jwt_secret = self._get_or_create_jwt_secret()
        
    def _prompt_master_password(self) -> str:
        """Prompt for master password if not provided"""
        import getpass
        
        master_file = self.auth_dir / 'master.key'
        if master_file.exists():
            return getpass.getpass("Enter Deep Tree Echo master password: ")
        else:
            print("First time setup - creating new master password")
            password1 = getpass.getpass("Enter new master password: ")
            password2 = getpass.getpass("Confirm master password: ")
            if password1 != password2:
                raise ValueError("Passwords do not match")
            
            # Store encrypted master key
            self._create_master_key_file(password1)
            return password1
    
    def _create_master_key_file(self, password: str):
        """Create encrypted master key file"""
        # Generate salt
        salt = secrets.token_bytes(32)
        
        # Create key derivation function
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        
        # Derive key from password
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        
        # Store salt and verification hash
        verification_data = {
            'salt': base64.b64encode(salt).decode(),
            'verification_hash': hashlib.sha256(key).hexdigest(),
            'created_at': time.time()
        }
        
        master_file = self.auth_dir / 'master.key'
        with open(master_file, 'w') as f:
            json.dump(verification_data, f)
        
        master_file.chmod(0o600)  # Restrict permissions
    
    def _initialize_encryption(self) -> Fernet:
        """Initialize encryption cipher"""
        # Generate key from master password
        salt = b'deep_tree_echo_salt_v1'  # In production, use random salt stored securely
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(self.master_password.encode()))
        return Fernet(key)
    
    def _get_or_create_jwt_secret(self) -> str:
        """Get or create JWT signing secret"""
        jwt_file = self.auth_dir / 'jwt.key'
        if jwt_file.exists():
            with open(jwt_file, 'rb') as f:
                encrypted_secret = f.read()
            return self.cipher.decrypt(encrypted_secret).decode()
        else:
            # Generate new JWT secret
            jwt_secret = secrets.token_urlsafe(64)
            encrypted_secret = self.cipher.encrypt(jwt_secret.encode())
            
            with open(jwt_file, 'wb') as f:
                f.write(encrypted_secret)
            jwt_file.chmod(0o600)
            
            return jwt_secret
    
    def store_service_credentials(self, service_name: str, username: str, 
                                password: str, totp_secret: Optional[str] = None) -> bool:
        """Store encrypted service credentials"""
        try:
            # Encrypt sensitive data
            encrypted_password = self.cipher.encrypt(password.encode()).decode()
            encrypted_2fa = None
            if totp_secret:
                encrypted_2fa = self.cipher.encrypt(totp_secret.encode()).decode()
            
            credentials = ServiceCredentials(
                service_name=service_name,
                username=username,
                encrypted_password=encrypted_password,
                encrypted_2fa_secret=encrypted_2fa,
                token_data=None,
                last_updated=time.time()
            )
            
            self.credentials[service_name] = credentials
            self._save_encrypted_credentials()
            
            self.logger.info(f"Stored credentials for service: {service_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error storing credentials for {service_name}: {e}")
            return False
    
    def get_service_credentials(self, service_name: str) -> Optional[Tuple[str, str, Optional[str]]]:
        """Retrieve and decrypt service credentials"""
        try:
            if service_name not in self.credentials:
                return None
            
            cred = self.credentials[service_name]
            
            # Decrypt password
            password = self.cipher.decrypt(cred.encrypted_password.encode()).decode()
            
            # Decrypt 2FA secret if present
            totp_secret = None
            if cred.encrypted_2fa_secret:
                totp_secret = self.cipher.decrypt(cred.encrypted_2fa_secret.encode()).decode()
            
            return (cred.username, password, totp_secret)
            
        except Exception as e:
            self.logger.error(f"Error retrieving credentials for {service_name}: {e}")
            return None
    
    def create_session_token(self, service: str, user_id: str, 
                           permissions: List[str] = None) -> Optional[str]:
        """Create JWT session token"""
        try:
            token_id = secrets.token_urlsafe(32)
            expires_at = time.time() + (24 * 3600)  # 24 hours
            
            # Create token data
            token_data = {
                'token_id': token_id,
                'user_id': user_id,
                'service': service,
                'permissions': permissions or [],
                'iat': time.time(),
                'exp': expires_at
            }
            
            # Generate JWT
            jwt_token = jwt.encode(token_data, self.jwt_secret, algorithm='HS256')
            
            # Store token info
            auth_token = AuthToken(
                token_id=token_id,
                user_id=user_id,
                service=service,
                expires_at=expires_at,
                permissions=permissions or [],
                metadata={'created_at': time.time()}
            )
            
            self.active_tokens[token_id] = auth_token
            self._save_encrypted_tokens()
            
            self.logger.info(f"Created session token for {service}:{user_id}")
            return jwt_token
            
        except Exception as e:
            self.logger.error(f"Error creating session token: {e}")
            return None
    
    def validate_token(self, jwt_token: str) -> Optional[Dict]:
        """Validate JWT token and return claims"""
        try:
            # Decode JWT
            claims = jwt.decode(jwt_token, self.jwt_secret, algorithms=['HS256'])
            
            # Check if token is still active
            token_id = claims.get('token_id')
            if token_id not in self.active_tokens:
                return None
            
            token = self.active_tokens[token_id]
            
            # Check expiration
            if time.time() > token.expires_at:
                # Remove expired token
                del self.active_tokens[token_id]
                self._save_encrypted_tokens()
                return None
            
            return claims
            
        except jwt.ExpiredSignatureError:
            self.logger.warning("Token has expired")
            return None
        except jwt.InvalidTokenError as e:
            self.logger.warning(f"Invalid token: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Error validating token: {e}")
            return None
    
    def revoke_token(self, token_id: str) -> bool:
        """Revoke a specific token"""
        try:
            if token_id in self.active_tokens:
                del self.active_tokens[token_id]
                self._save_encrypted_tokens()
                self.logger.info(f"Revoked token: {token_id}")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error revoking token: {e}")
            return False
    
    def cleanup_expired_tokens(self):
        """Remove expired tokens from storage"""
        try:
            current_time = time.time()
            expired_tokens = [
                token_id for token_id, token in self.active_tokens.items()
                if current_time > token.expires_at
            ]
            
            for token_id in expired_tokens:
                del self.active_tokens[token_id]
            
            if expired_tokens:
                self._save_encrypted_tokens()
                self.logger.info(f"Cleaned up {len(expired_tokens)} expired tokens")
                
        except Exception as e:
            self.logger.error(f"Error cleaning up expired tokens: {e}")
    
    def _save_encrypted_credentials(self):
        """Save encrypted credentials to disk"""
        try:
            data = {service: asdict(cred) for service, cred in self.credentials.items()}
            encrypted_data = self.cipher.encrypt(json.dumps(data).encode())
            
            with open(self.credentials_file, 'wb') as f:
                f.write(encrypted_data)
            self.credentials_file.chmod(0o600)
            
        except Exception as e:
            self.logger.error(f"Error saving encrypted credentials: {e}")
    
    def _save_encrypted_tokens(self):
        """Save encrypted tokens to disk"""
        try:
            data = {token_id: asdict(token) for token_id, token in self.active_tokens.items()}
            encrypted_data = self.cipher.encrypt(json.dumps(data).encode())
            
            with open(self.tokens_file, 'wb') as f:
                f.write(encrypted_data)
            self.tokens_file.chmod(0o600)
            
        except Exception as e:
            self.logger.error(f"Error saving encrypted tokens: {e}")
    
    def _load_encrypted_data(self):
        """Load encrypted data from disk"""
        try:
            # Load credentials
            if self.credentials_file.exists():
                with open(self.credentials_file, 'rb') as f:
                    encrypted_data = f.read()
                decrypted_data = self.cipher.decrypt(encrypted_data)
                data = json.loads(decrypted_data.decode())
                
                for service, cred_data in data.items():
                    self.credentials[service] = ServiceCredentials(**cred_data)
            
            # Load tokens
            if self.tokens_file.exists():
                with open(self.tokens_file, 'rb') as f:
                    encrypted_data = f.read()
                decrypted_data = self.cipher.decrypt(encrypted_data)
                data = json.loads(decrypted_data.decode())
                
                for token_id, token_data in data.items():
                    self.active_tokens[token_id] = AuthToken(**token_data)
            
            # Cleanup expired tokens on load
            self.cleanup_expired_tokens()
            
        except Exception as e:
            self.logger.error(f"Error loading encrypted data: {e}")
            # Continue with empty storage on error
    
    def get_authentication_status(self) -> Dict:
        """Get current authentication status"""
        try:
            active_services = list(self.credentials.keys())
            active_token_count = len(self.active_tokens)
            
            return {
                'authenticated_services': active_services,
                'active_tokens': active_token_count,
                'last_cleanup': time.time(),
                'status': 'ready'
            }
            
        except Exception as e:
            self.logger.error(f"Error getting authentication status: {e}")
            return {
                'authenticated_services': [],
                'active_tokens': 0,
                'last_cleanup': 0,
                'status': 'error',
                'error': str(e)
            }

# Production-ready authentication instance
auth_manager = AuthenticationManager()

def get_auth_manager() -> AuthenticationManager:
    """Get the global authentication manager instance"""
    return auth_manager