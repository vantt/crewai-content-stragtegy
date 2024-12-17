# src/config/settings.py
from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from typing import Optional
import os
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    """System configuration settings."""
    
    # Environment
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # API Keys
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    ANTHROPIC_API_KEY: Optional[str] = os.getenv("ANTHROPIC_API_KEY")
    
    # System Settings
    MAX_RETRIES: int = 3
    TIMEOUT: int = 30
    
    # Using ConfigDict instead of class Config
    model_config = ConfigDict(case_sensitive=True)

settings = Settings()