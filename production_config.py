#!/usr/bin/env python3
"""
Production Configuration Manager for Deep Tree Echo
Replaces development configurations with production-ready, environment-aware configuration system
"""

import os
import json
import yaml
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Union, List
from dataclasses import dataclass, asdict, field
from enum import Enum
import socket
import platform
import psutil

class Environment(Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TESTING = "testing"

@dataclass
class DatabaseConfig:
    """Database configuration"""
    host: str
    port: int
    database: str
    username: str
    password_env_var: str
    ssl_enabled: bool = True
    connection_timeout: int = 30
    max_connections: int = 20

@dataclass
class RedisConfig:
    """Redis configuration"""
    host: str
    port: int
    database: int = 0
    password_env_var: Optional[str] = None
    ssl_enabled: bool = False
    connection_timeout: int = 10

@dataclass
class ServiceConfig:
    """Service endpoint configuration"""
    name: str
    host: str
    port: int
    protocol: str = "https"
    api_version: str = "v1"
    timeout: int = 30
    retry_count: int = 3
    health_check_path: str = "/health"

@dataclass
class SecurityConfig:
    """Security configuration"""
    encryption_key_env_var: str
    jwt_secret_env_var: str
    session_timeout: int = 3600  # 1 hour
    max_login_attempts: int = 5
    password_min_length: int = 12
    require_2fa: bool = True
    allowed_origins: List[str] = field(default_factory=list)

@dataclass
class LoggingConfig:
    """Logging configuration"""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    max_file_size: int = 10485760  # 10MB
    backup_count: int = 5
    log_dir: str = "/var/log/deep-tree-echo"
    structured_logging: bool = True

@dataclass
class MonitoringConfig:
    """Monitoring and alerting configuration"""
    metrics_enabled: bool = True
    metrics_port: int = 8080
    health_check_interval: int = 30
    alert_email: Optional[str] = None
    alert_webhook: Optional[str] = None
    prometheus_endpoint: str = "/metrics"

@dataclass
class PerformanceConfig:
    """Performance and scaling configuration"""
    max_cpu_percent: float = 80.0
    max_memory_percent: float = 80.0
    max_disk_percent: float = 85.0
    auto_scaling_enabled: bool = False
    min_instances: int = 1
    max_instances: int = 10
    scale_up_threshold: float = 75.0
    scale_down_threshold: float = 25.0

@dataclass
class ProductionConfig:
    """Complete production configuration"""
    environment: Environment
    app_name: str
    version: str
    host: str
    port: int
    debug: bool
    database: DatabaseConfig
    redis: RedisConfig
    services: Dict[str, ServiceConfig]
    security: SecurityConfig
    logging: LoggingConfig
    monitoring: MonitoringConfig
    performance: PerformanceConfig
    custom_settings: Dict[str, Any] = field(default_factory=dict)

class ConfigurationManager:
    """Production-ready configuration management system"""
    
    def __init__(self, config_dir: Optional[str] = None, environment: Optional[str] = None):
        self.logger = logging.getLogger(__name__)
        
        # Determine environment
        self.environment = Environment(environment or os.getenv('DEEP_TREE_ECHO_ENV', 'development'))
        
        # Set up configuration directories
        self.config_dir = Path(config_dir or os.getenv('DEEP_TREE_ECHO_CONFIG_DIR', '/etc/deep-tree-echo'))
        self.local_config_dir = Path.home() / '.deep_tree_echo' / 'config'
        
        # Create directories
        self.local_config_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize configuration
        self.config: Optional[ProductionConfig] = None
        self._load_configuration()
        
    def _load_configuration(self):
        """Load configuration from multiple sources with precedence"""
        try:
            # Start with default configuration
            config_data = self._get_default_config()
            
            # Override with environment-specific config file
            env_config = self._load_environment_config()
            if env_config:
                config_data = self._deep_merge(config_data, env_config)
            
            # Override with local config file
            local_config = self._load_local_config()
            if local_config:
                config_data = self._deep_merge(config_data, local_config)
            
            # Override with environment variables
            env_overrides = self._load_environment_variables()
            if env_overrides:
                config_data = self._deep_merge(config_data, env_overrides)
            
            # Create configuration object
            self.config = self._create_config_object(config_data)
            
            # Validate configuration
            self._validate_configuration()
            
            self.logger.info(f"Configuration loaded for environment: {self.environment.value}")
            
        except Exception as e:
            self.logger.error(f"Error loading configuration: {e}")
            raise
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration values"""
        hostname = socket.gethostname()
        
        return {
            'environment': self.environment.value,
            'app_name': 'deep-tree-echo',
            'version': '1.0.0',
            'host': '0.0.0.0',
            'port': 8000,
            'debug': self.environment == Environment.DEVELOPMENT,
            'database': {
                'host': 'localhost',
                'port': 5432,
                'database': 'deep_tree_echo',
                'username': 'deep_tree_echo',
                'password_env_var': 'DB_PASSWORD',
                'ssl_enabled': self.environment == Environment.PRODUCTION,
                'connection_timeout': 30,
                'max_connections': 20
            },
            'redis': {
                'host': 'localhost',
                'port': 6379,
                'database': 0,
                'password_env_var': 'REDIS_PASSWORD' if self.environment == Environment.PRODUCTION else None,
                'ssl_enabled': self.environment == Environment.PRODUCTION,
                'connection_timeout': 10
            },
            'services': {
                'openai': {
                    'name': 'OpenAI API',
                    'host': 'api.openai.com',
                    'port': 443,
                    'protocol': 'https',
                    'api_version': 'v1',
                    'timeout': 60,
                    'retry_count': 3,
                    'health_check_path': '/v1/models'
                },
                'github': {
                    'name': 'GitHub API',
                    'host': 'api.github.com',
                    'port': 443,
                    'protocol': 'https',
                    'api_version': 'v3',
                    'timeout': 30,
                    'retry_count': 3,
                    'health_check_path': '/rate_limit'
                }
            },
            'security': {
                'encryption_key_env_var': 'ENCRYPTION_KEY',
                'jwt_secret_env_var': 'JWT_SECRET',
                'session_timeout': 3600,
                'max_login_attempts': 5,
                'password_min_length': 12,
                'require_2fa': self.environment == Environment.PRODUCTION,
                'allowed_origins': self._get_default_allowed_origins()
            },
            'logging': {
                'level': 'DEBUG' if self.environment == Environment.DEVELOPMENT else 'INFO',
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                'max_file_size': 10485760,  # 10MB
                'backup_count': 5,
                'log_dir': str(self.local_config_dir / 'logs'),
                'structured_logging': self.environment == Environment.PRODUCTION
            },
            'monitoring': {
                'metrics_enabled': True,
                'metrics_port': 8080,
                'health_check_interval': 30,
                'alert_email': os.getenv('ALERT_EMAIL'),
                'alert_webhook': os.getenv('ALERT_WEBHOOK'),
                'prometheus_endpoint': '/metrics'
            },
            'performance': {
                'max_cpu_percent': 80.0,
                'max_memory_percent': 80.0,
                'max_disk_percent': 85.0,
                'auto_scaling_enabled': self.environment == Environment.PRODUCTION,
                'min_instances': 1,
                'max_instances': 10 if self.environment == Environment.PRODUCTION else 3,
                'scale_up_threshold': 75.0,
                'scale_down_threshold': 25.0
            },
            'custom_settings': {}
        }
    
    def _get_default_allowed_origins(self) -> List[str]:
        """Get default allowed origins based on environment"""
        if self.environment == Environment.DEVELOPMENT:
            return ['http://localhost:3000', 'http://localhost:8000', 'http://127.0.0.1:3000']
        elif self.environment == Environment.STAGING:
            return ['https://staging.deep-tree-echo.com']
        elif self.environment == Environment.PRODUCTION:
            return ['https://deep-tree-echo.com', 'https://app.deep-tree-echo.com']
        else:
            return ['http://localhost:3000']
    
    def _load_environment_config(self) -> Optional[Dict[str, Any]]:
        """Load environment-specific configuration file"""
        try:
            config_file = self.config_dir / f"{self.environment.value}.yaml"
            if config_file.exists():
                with open(config_file) as f:
                    return yaml.safe_load(f)
            
            # Try local environment config
            local_config_file = self.local_config_dir / f"{self.environment.value}.yaml"
            if local_config_file.exists():
                with open(local_config_file) as f:
                    return yaml.safe_load(f)
                    
        except Exception as e:
            self.logger.warning(f"Error loading environment config: {e}")
        
        return None
    
    def _load_local_config(self) -> Optional[Dict[str, Any]]:
        """Load local configuration file"""
        try:
            local_config_file = self.local_config_dir / 'local.yaml'
            if local_config_file.exists():
                with open(local_config_file) as f:
                    return yaml.safe_load(f)
        except Exception as e:
            self.logger.warning(f"Error loading local config: {e}")
        
        return None
    
    def _load_environment_variables(self) -> Dict[str, Any]:
        """Load configuration from environment variables"""
        env_config = {}
        
        # Map environment variables to configuration paths
        env_mappings = {
            'DEEP_TREE_ECHO_HOST': 'host',
            'DEEP_TREE_ECHO_PORT': 'port',
            'DEEP_TREE_ECHO_DEBUG': 'debug',
            'DB_HOST': 'database.host',
            'DB_PORT': 'database.port',
            'DB_NAME': 'database.database',
            'DB_USER': 'database.username',
            'REDIS_HOST': 'redis.host',
            'REDIS_PORT': 'redis.port',
            'LOG_LEVEL': 'logging.level',
            'METRICS_PORT': 'monitoring.metrics_port',
        }
        
        for env_var, config_path in env_mappings.items():
            value = os.getenv(env_var)
            if value is not None:
                self._set_nested_value(env_config, config_path, self._convert_env_value(value))
        
        return env_config
    
    def _convert_env_value(self, value: str) -> Union[str, int, float, bool]:
        """Convert environment variable string to appropriate type"""
        # Boolean conversion
        if value.lower() in ('true', 'false'):
            return value.lower() == 'true'
        
        # Integer conversion
        try:
            if '.' not in value:
                return int(value)
        except ValueError:
            pass
        
        # Float conversion
        try:
            return float(value)
        except ValueError:
            pass
        
        # Return as string
        return value
    
    def _set_nested_value(self, config: Dict, path: str, value: Any):
        """Set nested configuration value using dot notation"""
        keys = path.split('.')
        current = config
        
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        current[keys[-1]] = value
    
    def _deep_merge(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Deep merge two dictionaries"""
        result = base.copy()
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def _create_config_object(self, config_data: Dict[str, Any]) -> ProductionConfig:
        """Create configuration object from dictionary"""
        try:
            return ProductionConfig(
                environment=Environment(config_data['environment']),
                app_name=config_data['app_name'],
                version=config_data['version'],
                host=config_data['host'],
                port=int(config_data['port']),
                debug=bool(config_data['debug']),
                database=DatabaseConfig(**config_data['database']),
                redis=RedisConfig(**config_data['redis']),
                services={
                    name: ServiceConfig(name=name, **service_config)
                    for name, service_config in config_data['services'].items()
                },
                security=SecurityConfig(**config_data['security']),
                logging=LoggingConfig(**config_data['logging']),
                monitoring=MonitoringConfig(**config_data['monitoring']),
                performance=PerformanceConfig(**config_data['performance']),
                custom_settings=config_data.get('custom_settings', {})
            )
        except Exception as e:
            self.logger.error(f"Error creating configuration object: {e}")
            raise
    
    def _validate_configuration(self):
        """Validate configuration values"""
        if not self.config:
            raise ValueError("Configuration not loaded")
        
        # Validate required environment variables exist
        required_env_vars = [
            self.config.database.password_env_var,
            self.config.security.encryption_key_env_var,
            self.config.security.jwt_secret_env_var
        ]
        
        if self.config.redis.password_env_var:
            required_env_vars.append(self.config.redis.password_env_var)
        
        missing_vars = [var for var in required_env_vars if not os.getenv(var)]
        if missing_vars:
            self.logger.warning(f"Missing environment variables: {missing_vars}")
        
        # Validate port ranges
        if not (1 <= self.config.port <= 65535):
            raise ValueError(f"Invalid port number: {self.config.port}")
        
        # Create log directory
        log_dir = Path(self.config.logging.log_dir)
        log_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger.info("Configuration validation completed")
    
    def get_config(self) -> ProductionConfig:
        """Get the current configuration"""
        if not self.config:
            raise RuntimeError("Configuration not loaded")
        return self.config
    
    def get_database_url(self) -> str:
        """Get database connection URL"""
        if not self.config:
            raise RuntimeError("Configuration not loaded")
        
        password = os.getenv(self.config.database.password_env_var, '')
        ssl_mode = 'require' if self.config.database.ssl_enabled else 'disable'
        
        return (f"postgresql://{self.config.database.username}:{password}@"
                f"{self.config.database.host}:{self.config.database.port}/"
                f"{self.config.database.database}?sslmode={ssl_mode}")
    
    def get_redis_url(self) -> str:
        """Get Redis connection URL"""
        if not self.config:
            raise RuntimeError("Configuration not loaded")
        
        password = ""
        if self.config.redis.password_env_var:
            password = f":{os.getenv(self.config.redis.password_env_var, '')}@"
        
        protocol = 'rediss' if self.config.redis.ssl_enabled else 'redis'
        
        return (f"{protocol}://{password}{self.config.redis.host}:"
                f"{self.config.redis.port}/{self.config.redis.database}")
    
    def get_service_url(self, service_name: str) -> str:
        """Get service URL"""
        if not self.config or service_name not in self.config.services:
            raise ValueError(f"Service {service_name} not configured")
        
        service = self.config.services[service_name]
        return f"{service.protocol}://{service.host}:{service.port}"
    
    def save_config_template(self, filename: str = None):
        """Save configuration template for reference"""
        if not filename:
            filename = f"{self.environment.value}-template.yaml"
        
        template_file = self.local_config_dir / filename
        
        try:
            config_dict = asdict(self.config) if self.config else self._get_default_config()
            
            with open(template_file, 'w') as f:
                yaml.dump(config_dict, f, default_flow_style=False, indent=2)
            
            self.logger.info(f"Configuration template saved to: {template_file}")
            
        except Exception as e:
            self.logger.error(f"Error saving configuration template: {e}")
    
    def get_system_info(self) -> Dict[str, Any]:
        """Get current system information"""
        return {
            'hostname': socket.gethostname(),
            'platform': platform.platform(),
            'python_version': platform.python_version(),
            'cpu_count': psutil.cpu_count(),
            'memory_total': psutil.virtual_memory().total,
            'disk_usage': dict(psutil.disk_usage('/'))._asdict(),
            'environment': self.environment.value,
            'config_dir': str(self.config_dir),
            'local_config_dir': str(self.local_config_dir)
        }

# Global configuration manager instance
config_manager = ConfigurationManager()

def get_config() -> ProductionConfig:
    """Get the global configuration"""
    return config_manager.get_config()

def get_config_manager() -> ConfigurationManager:
    """Get the global configuration manager"""
    return config_manager