import logging
from browser_interface import DeepTreeEchoBrowser

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def main():
    """Test container configuration for Deep Tree Echo's browser"""
    browser = DeepTreeEchoBrowser()
    
    try:
        # Initialize browser
        if not browser.init():
            logging.error("Failed to initialize browser")
            return
        
        # Configure each container
        containers = ['Personal', 'Development', 'Work', 'Social']
        
        for container in containers:
            # Add custom settings for Development container
            if container == 'Development':
                custom_settings = {
                    'bookmarks': [
                        {'name': 'GitHub', 'url': 'https://github.com'},
                        {'name': 'Stack Overflow', 'url': 'https://stackoverflow.com'},
                        {'name': 'ChatGPT', 'url': 'https://chat.openai.com'},
                        {'name': 'CodePen', 'url': 'https://codepen.io'},
                        {'name': 'Dev.to', 'url': 'https://dev.to'}
                    ]
                }
                success = browser.configure_container(container, custom_settings)
            else:
                success = browser.configure_container(container)
                
            if success:
                logging.info(f"Successfully configured {container} container")
                
                # Get and display current settings
                settings = browser.get_container_settings(container)
                if settings:
                    logging.info(f"{container} container settings:")
                    logging.info(f"Homepage: {settings['homepage']}")
                    if settings.get('bookmarks'):
                        logging.info("Bookmarks:")
                        for bookmark in settings['bookmarks']:
                            logging.info(f"  - {bookmark['name']}: {bookmark['url']}")
            else:
                logging.error(f"Failed to configure {container} container")
        
        # Keep browser open for interaction
        input("Press Enter to close browser...")
        
    finally:
        browser.close()

if __name__ == "__main__":
    main()
