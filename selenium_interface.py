import os
import time
import logging
import cv2
from playwright.sync_api import sync_playwright
import numpy as np
from PIL import Image
import io
import base64
from dotenv import load_dotenv
from deep_tree_echo import DeepTreeEcho, TreeNode

# Create templates directory
os.makedirs('templates', exist_ok=True)

load_dotenv()

class SeleniumInterface:
    def __init__(self):
        """Initialize the ChatGPT interface"""
        self.browser = None
        self.page = None
        self.context = None
        self.playwright = None
        self.echo_system = DeepTreeEcho(echo_threshold=0.75)
        
        # Set up logging
        logging.basicConfig(level=logging.DEBUG)
        self.logger = logging.getLogger(__name__)
        
    def find_existing_browser(self):
        """Try to find an existing browser with ChatGPT open"""
        try:
            # Try different debugging ports
            ports = [9222, 9223, 9224, 9225]
            for port in ports:
                try:
                    browser = self.playwright.chromium.connect_over_cdp(f"http://localhost:{port}")
                    for context in browser.contexts:
                        for page in context.pages:
                            if "chatgpt.com" in page.url:
                                self.browser = browser
                                self.page = page
                                self.logger.info(f"Connected to existing ChatGPT session on port {port}")
                                return True
                except Exception:
                    continue
        except Exception as e:
            self.logger.debug(f"Error finding existing browser: {str(e)}")
        return False
    
    def init(self):
        """Initialize the browser"""
        try:
            self.playwright = sync_playwright().start()
            
            # First try to find existing browser
            if self.find_existing_browser():
                return True
            
            self.logger.info("No existing browser session found, creating new one...")
            
            # Use the original browser data directory
            user_data_dir = os.path.join(os.getcwd(), 'browser_data')
            os.makedirs(user_data_dir, exist_ok=True)
            
            # Create new browser context with more robust settings
            self.browser = self.playwright.chromium.launch_persistent_context(
                user_data_dir=user_data_dir,
                headless=False,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--window-size=1920,1080',
                    '--start-maximized',
                    '--disable-dev-shm-usage',
                    '--disable-blink-features=AutomationControlled',  # Hide automation
                    '--remote-debugging-port=9222'
                ]
            )
            
            # Get or create page
            self.page = self.browser.pages[0] if self.browser.pages else self.browser.new_page()
            
            # Set default timeout and viewport
            self.page.set_default_timeout(60000)
            self.page.set_viewport_size({"width": 1920, "height": 1080})
            
            # Add stealth scripts to avoid detection
            self.page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5]
                });
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['en-US', 'en']
                });
                window.chrome = {
                    runtime: {}
                };
            """)
            
            # Navigate to chat page only if needed
            if "chat.openai.com" not in self.page.url:
                self.logger.info("Navigating to chat page...")
                
                # Try navigation with retries
                max_retries = 3
                for attempt in range(max_retries):
                    try:
                        self.page.goto("https://chat.openai.com", wait_until="networkidle")
                        self.logger.info(f"Current URL: {self.page.url}")
                        
                        # Handle Cloudflare
                        if not self.wait_for_cloudflare():
                            if attempt < max_retries - 1:
                                self.logger.warning(f"Cloudflare challenge failed, attempt {attempt + 1}/{max_retries}")
                                time.sleep(5)
                                continue
                            else:
                                self.logger.error("Failed to pass Cloudflare challenge after all retries")
                                return False
                        
                        # Additional waits for page stability
                        self.page.wait_for_load_state("networkidle")
                        self.page.wait_for_load_state("domcontentloaded")
                        self.page.wait_for_load_state("load")
                        time.sleep(5)  # Extra time for dynamic content
                        
                        break  # Success
                        
                    except Exception as e:
                        self.logger.error(f"Navigation attempt {attempt + 1} failed: {str(e)}")
                        if attempt < max_retries - 1:
                            time.sleep(5)
                        else:
                            raise
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize browser: {str(e)}")
            if self.page:
                self.page.screenshot(path="init_error.png")
            return False
            
    def find_element_by_image(self, template_path, threshold=0.8):
        """Find an element on the page by matching a template image
        
        Args:
            template_path (str): Path to the template image file
            threshold (float): Matching threshold (0-1), higher is more strict
            
        Returns:
            tuple: (x, y) coordinates of the match, or None if not found
        """
        try:
            # Take screenshot of the page
            screenshot_path = "current_screen.png"
            self.page.screenshot(path=screenshot_path)
            
            # Load the screenshot and template
            screenshot = cv2.imread(screenshot_path)
            template = cv2.imread(template_path)
            
            if template is None:
                self.logger.error(f"Could not load template image: {template_path}")
                return None
                
            # Perform template matching
            result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            
            if max_val >= threshold:
                # Get the center point of the match
                h, w = template.shape[:2]
                center_x = max_loc[0] + w//2
                center_y = max_loc[1] + h//2
                
                self.logger.info(f"Found match for {template_path} at ({center_x}, {center_y}) with confidence {max_val}")
                return (center_x, center_y)
            else:
                self.logger.debug(f"No match found for {template_path} (best match: {max_val})")
                return None
                
        except Exception as e:
            self.logger.error(f"Error in visual search: {str(e)}")
            return None
            
    def click_by_vision(self, template_path, threshold=0.8):
        """Click an element using computer vision
        
        Args:
            template_path (str): Path to the template image
            threshold (float): Matching threshold (0-1)
            
        Returns:
            bool: True if clicked successfully, False otherwise
        """
        try:
            coords = self.find_element_by_image(template_path, threshold)
            if coords:
                x, y = coords
                self.page.mouse.click(x, y)
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error clicking by vision: {str(e)}")
            return False
            
    def authenticate(self):
        """Authenticate with ChatGPT using username and password"""
        try:
            username = os.getenv("CHAT_USERNAME")
            password = os.getenv("CHAT_PASSWORD")
            
            if not username or not password:
                self.logger.error("CHAT_USERNAME or CHAT_PASSWORD not found in environment")
                return False
                
            # Load login page directly
            self.page.goto("https://auth0.openai.com/u/login/identifier", wait_until="networkidle")
            self.logger.info("Loaded login page")
            time.sleep(2)
            
            # Fill in email
            email_input = self.page.wait_for_selector('input[name="username"]', timeout=10000)
            email_input.fill(username)
            self.logger.info("Entered email")
            
            # Click continue button
            self.page.click('button[type="submit"]')
            self.logger.info("Clicked continue")
            
            time.sleep(2)
            
            # Fill in password
            password_input = self.page.wait_for_selector('input[name="password"]', timeout=10000)
            password_input.fill(password)
            self.logger.info("Entered password")
            
            # Click login button
            self.page.click('button[type="submit"]')
            self.logger.info("Clicked login")
            
            # Wait for chat interface
            self.page.wait_for_selector('[data-testid="chat-input"]', timeout=30000)
            self.logger.info("Successfully logged in")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Authentication error: {str(e)}")
            self.page.screenshot(path="auth_error.png")
            return False
            
    def wait_for_cloudflare(self, max_retries=3):
        """Wait for Cloudflare challenge to complete"""
        try:
            self.logger.info("Checking for Cloudflare challenge...")
            
            # Check if we're on a Cloudflare page
            if "challenge" not in self.page.title().lower() and "cloudflare" not in self.page.content().lower():
                return True
                
            self.logger.info("Detected Cloudflare challenge, waiting...")
            
            # Wait for the challenge to complete
            for attempt in range(max_retries):
                try:
                    # Wait for title to change from Cloudflare challenge
                    self.page.wait_for_function(
                        """() => {
                            return !document.title.toLowerCase().includes('cloudflare') && 
                                   !document.title.toLowerCase().includes('challenge') &&
                                   !document.title.toLowerCase().includes('checking');
                        }""",
                        timeout=30000
                    )
                    
                    # Additional wait for page to stabilize
                    self.page.wait_for_load_state("networkidle")
                    self.page.wait_for_load_state("domcontentloaded")
                    self.page.wait_for_load_state("load")
                    time.sleep(2)  # Small delay to ensure everything is ready
                    
                    self.logger.info("Cloudflare challenge completed")
                    return True
                    
                except Exception as e:
                    self.logger.warning(f"Cloudflare wait attempt {attempt + 1} failed: {str(e)}")
                    if attempt < max_retries - 1:
                        time.sleep(5)  # Wait before retrying
                    else:
                        raise
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error waiting for Cloudflare: {str(e)}")
            return False
    
    def send_message(self, message):
        """Send a message to the chat"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # Get current URL and check if we need to navigate
                self.logger.info(f"Current URL before sending message: {self.page.url}")
                if not self.page.url.startswith("https://chat.openai.com"):
                    self.logger.info("Not on chat page, navigating...")
                    self.page.goto("https://chat.openai.com", wait_until="networkidle")
                    self.logger.info(f"Navigated to: {self.page.url}")
                    
                    # Handle Cloudflare if needed
                    if not self.wait_for_cloudflare():
                        if attempt < max_retries - 1:
                            self.logger.warning(f"Cloudflare challenge failed, attempt {attempt + 1}/{max_retries}")
                            time.sleep(5)
                            continue
                        else:
                            self.logger.error("Failed to pass Cloudflare challenge after all retries")
                            return False
                
                self.logger.info("Waiting for page to be ready...")
                self.page.wait_for_load_state("networkidle")
                self.page.wait_for_load_state("domcontentloaded")
                self.page.wait_for_load_state("load")
                time.sleep(3)  # Give extra time for dynamic content
                
                # Log page content for debugging
                self.logger.info("Looking for chat input...")
                
                # Try different selectors for the chat input
                input_selectors = [
                    'textarea[placeholder*="Message"]',
                    'textarea[placeholder*="Send a message"]',
                    '[contenteditable="true"]',
                    '[role="textbox"]',
                    'div[class*="input"]',
                    'div[class*="chat"] textarea',
                    'div[class*="chat"] [contenteditable]',
                    '#prompt-textarea'
                ]
                
                chat_input = None
                for selector in input_selectors:
                    try:
                        self.logger.info(f"Trying selector: {selector}")
                        chat_input = self.page.wait_for_selector(selector, timeout=10000, state="visible")
                        if chat_input:
                            self.logger.info(f"Found input using selector: {selector}")
                            break
                    except Exception as e:
                        self.logger.info(f"Selector {selector} failed: {str(e)}")
                
                if not chat_input:
                    if attempt < max_retries - 1:
                        self.logger.warning(f"Could not find chat input, attempt {attempt + 1}/{max_retries}")
                        self.page.screenshot(path=f"chat_input_error_{attempt + 1}.png")
                        time.sleep(5)
                        continue
                    else:
                        self.logger.error("Could not find chat input after all retries")
                        return False
                
                # Clear any existing text
                chat_input.click()
                chat_input.press("Control+A")
                chat_input.press("Backspace")
                
                # Type the message
                chat_input.fill(message)
                time.sleep(1)  # Small delay for stability
                
                # Send the message
                chat_input.press("Enter")
                
                # Wait for response to start
                try:
                    self.page.wait_for_selector('[data-message-author="assistant"]', timeout=30000)
                except Exception as e:
                    self.logger.warning(f"Could not detect response start: {str(e)}")
                
                # Wait for the response to complete
                try:
                    self.page.wait_for_function(
                        """() => {
                            const buttons = document.querySelectorAll('button');
                            return Array.from(buttons).some(button => 
                                button.textContent.includes('Regenerate') || 
                                button.textContent.includes('Continue')
                            );
                        }""",
                        timeout=60000
                    )
                except Exception as e:
                    self.logger.warning(f"Could not detect response completion: {str(e)}")
                
                return True
                
            except Exception as e:
                self.logger.error(f"Error in send_message attempt {attempt + 1}: {str(e)}")
                self.page.screenshot(path=f"send_error_{attempt + 1}.png")
                if attempt < max_retries - 1:
                    time.sleep(5)
                else:
                    return False
        
        return False
    
    def close(self):
        """Close the browser"""
        if self.page:
            self.page.close()
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()

def main():
    chat = SeleniumInterface()
    if not chat.init():
        print("Failed to initialize browser")
        return
        
    if not chat.authenticate():
        print("Authentication failed")
        chat.close()
        return
        
    print("Successfully authenticated")
    chat.close()

if __name__ == "__main__":
    main()
