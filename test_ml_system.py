import logging
from browser_interface import DeepTreeEchoBrowser
import time
import cv2
import numpy as np
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_visual_detection(browser):
    """Test ML-enhanced visual element detection"""
    try:
        # Get Development container page
        page = browser.get_or_create_page('Development')
        if not page:
            logging.error("Failed to get Development container page")
            return False
            
        # Test 1: Navigate to Python.org and detect logo
        logging.info("Testing visual element detection...")
        page.goto('https://www.python.org')
        time.sleep(2)  # Let the page load
        
        # Capture logo template
        logo_selector = 'img[alt="python™"]'
        logo_element = page.locator(logo_selector)
        bbox = logo_element.bounding_box()
        
        if bbox:
            # Capture logo template
            screenshot = browser.sensory.capture_screen()
            template = screenshot[
                int(bbox['y']):int(bbox['y'] + bbox['height']),
                int(bbox['x']):int(bbox['x'] + bbox['width'])
            ]
            
            # Save template for future use
            template_dir = Path.home() / '.deep_tree_echo' / 'templates'
            template_dir.mkdir(parents=True, exist_ok=True)
            cv2.imwrite(
                str(template_dir / 'python_logo.png'),
                template
            )
            
            # Test detection
            element = browser.sensory.wait_for_element(
                template,
                timeout=10
            )
            
            if element:
                logging.info("Successfully detected Python logo")
                
                # Test clicking the detected element
                x = element['location'][0] + element['size'][0] // 2
                y = element['location'][1] + element['size'][1] // 2
                
                browser.sensory.move_mouse(x, y)
                time.sleep(1)
                browser.sensory.click()
                
                return True
            else:
                logging.error("Failed to detect Python logo")
                return False
                
        else:
            logging.error("Failed to get logo bounding box")
            return False
            
    except Exception as e:
        logging.error(f"Error in visual detection test: {str(e)}")
        return False

def test_movement_learning(browser):
    """Test ML-enhanced movement patterns"""
    try:
        # Get Development container page
        page = browser.get_or_create_page('Development')
        if not page:
            logging.error("Failed to get Development container page")
            return False
            
        logging.info("Testing movement learning...")
        
        # Test repeated movements to train the model
        start_pos = (100, 100)
        end_positions = [
            (500, 500),
            (300, 200),
            (700, 400),
            (200, 600)
        ]
        
        for end_pos in end_positions:
            # Move to start position
            browser.sensory.move_mouse(
                start_pos[0],
                start_pos[1],
                human_like=False
            )
            time.sleep(0.5)
            
            # Move to end position with learning
            browser.sensory.move_mouse(
                end_pos[0],
                end_pos[1],
                human_like=True
            )
            time.sleep(0.5)
            
        # Analyze movement patterns
        patterns = browser.sensory.ml.analyze_patterns(
            browser.sensory.ml.interaction_history[-4:]
        )
        
        logging.info("Movement patterns:")
        logging.info(f"Mean distance: {patterns['movement'].get('mean_distance')}")
        logging.info(f"Mean speed: {patterns['movement'].get('mean_speed')}")
        
        return True
        
    except Exception as e:
        logging.error(f"Error in movement learning test: {str(e)}")
        return False

def main():
    """Test Deep Tree Echo's ML capabilities"""
    browser = DeepTreeEchoBrowser()
    
    try:
        # Initialize browser
        if not browser.init():
            logging.error("Failed to initialize browser")
            return
            
        # Run visual detection test
        if test_visual_detection(browser):
            logging.info("Successfully completed visual detection test")
        else:
            logging.error("Failed to complete visual detection test")
            
        # Run movement learning test
        if test_movement_learning(browser):
            logging.info("Successfully completed movement learning test")
        else:
            logging.error("Failed to complete movement learning test")
            
        # Keep browser open for observation
        input("Press Enter to close browser...")
        
    finally:
        browser.close()

if __name__ == "__main__":
    main()
