from src.core.initialization import SystemInitializer
from loguru import logger

def main():
    """Main entry point for the system."""
    try:
        # Initialize system
        initializer = SystemInitializer()
        
        # Check if initialization was successful
        if initializer.initialize_system():
            logger.info("System initialized successfully")
            return True
        else:
            logger.error("System initialization failed")
            return False
            
    except Exception as e:
        logger.error(f"System initialization failed: {str(e)}")
        return False

if __name__ == "__main__":
    main()