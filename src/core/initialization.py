# src/core/initialization.py
from loguru import logger
from pathlib import Path
from typing import Optional
import sys

from ..config.settings import settings

class SystemInitializer:
    """Initialize the content marketing system."""
    
    def __init__(self):
        self.settings = settings
        self._setup_logging()
        
    def _setup_logging(self):
        """Configure logging system."""
        logger.remove()  # Remove default handler
        logger.add(
            sys.stderr,
            level=self.settings.LOG_LEVEL,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
        )
        
        # Add file logging
        log_path = Path("logs")
        log_path.mkdir(exist_ok=True)
        logger.add(
            log_path / "system.log",
            rotation="500 MB",
            retention="10 days",
            level=self.settings.LOG_LEVEL
        )
    
    def validate_environment(self) -> bool:
        """Validate required environment variables and settings."""
        required_vars = ["OPENAI_API_KEY", "ANTHROPIC_API_KEY"]
        missing_vars = [var for var in required_vars if not getattr(self.settings, var)]
        
        if missing_vars:
            logger.error(f"Missing required environment variables: {missing_vars}")
            return False
        
        return True
    
    def initialize_system(self) -> bool:
        """Initialize the complete system."""
        try:
            logger.info("Starting system initialization...")
            
            # Validate environment
            if not self.validate_environment():
                return False
            
            # Additional initialization steps can be added here
            
            logger.info("System initialization completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"System initialization failed: {str(e)}")
            return False