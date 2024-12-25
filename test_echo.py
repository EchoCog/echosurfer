from selenium_interface import SeleniumInterface
import logging
import time

def main():
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    # Initialize interface
    interface = SeleniumInterface()
    
    try:
        # Initialize browser
        if not interface.init():
            logger.error("Failed to initialize browser")
            return
        
        # Test message
        test_message = "What are the key principles of recursive algorithms?"
        
        # Send message and get response with echo analysis
        response, echo_analysis = interface.send_message(test_message)
        
        if response and echo_analysis:
            logger.info("Response received successfully")
            logger.info(f"Echo Analysis Results:")
            logger.info(f"Total Nodes: {echo_analysis['total_nodes']}")
            logger.info(f"Average Echo: {echo_analysis['avg_echo']:.3f}")
            logger.info(f"Maximum Echo: {echo_analysis['max_echo']:.3f}")
            logger.info(f"Resonant Nodes: {echo_analysis['resonant_nodes']}")
            logger.info(f"Tree Depth: {echo_analysis['depth']}")
        else:
            logger.error("Failed to get response or analyze echoes")
            
    except Exception as e:
        logger.error(f"Error in test: {str(e)}")
        
    finally:
        # Don't close the browser to keep the session alive
        pass

if __name__ == "__main__":
    main()
