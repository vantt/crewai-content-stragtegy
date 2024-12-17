# Phase A1: Project Initialization Technical Specification

## 1. Project Structure
```
content_marketing_system/
├── .env                      # Environment variables
├── .gitignore               # Git ignore file
├── README.md                # Project documentation
├── requirements.txt         # Project dependencies
├── setup.py                 # Package setup file
├── pyproject.toml          # Project metadata and build config
├── tests/                  # Test directory
│   ├── __init__.py
│   └── test_initialization.py
└── src/                    # Source code
    ├── __init__.py
    ├── config/            # Configuration files
    │   ├── __init__.py
    │   └── settings.py
    ├── core/             # Core functionality
    │   ├── __init__.py
    │   └── initialization.py
    └── utils/            # Utility functions
        ├── __init__.py
        └── logger.py
```

## 2. Dependencies
### 2.1 Core Dependencies
```toml
[project]
name = "content_marketing_system"
version = "0.1.0"
dependencies = [
    "crewai>=0.1.0",
    "streamlit>=1.24.0",
    "llmlingua>=0.1.0",
    "python-dotenv>=1.0.0",
    "pydantic>=2.0.0",
    "loguru>=0.7.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "black>=23.0.0",
    "isort>=5.0.0",
    "flake8>=6.0.0",
    "mypy>=1.0.0",
]
```

### 2.2 Requirements File
```
# requirements.txt
crewai>=0.1.0
streamlit>=1.24.0
llmlingua>=0.1.0
python-dotenv>=1.0.0
pydantic>=2.0.0
loguru>=0.7.0

# Development dependencies
pytest>=7.0.0
black>=23.0.0
isort>=5.0.0
flake8>=6.0.0
mypy>=1.0.0
```

## 3. Configuration Setup
### 3.1 Environment Variables
```python
# .env
OPENAI_API_KEY=your-api-key
ANTHROPIC_API_KEY=your-api-key
LOG_LEVEL=INFO
ENVIRONMENT=development
```

### 3.2 Settings Configuration
```python
# src/config/settings.py
from pydantic import BaseSettings
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
    
    class Config:
        case_sensitive = True

settings = Settings()
```

## 4. Initialization Implementation
### 4.1 Core Initialization
```python
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
```

### 4.2 Utility Functions
```python
# src/utils/logger.py
from loguru import logger
from functools import wraps
from time import time

def log_execution_time(func):
    """Decorator to log function execution time."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time()
        result = func(*args, **kwargs)
        end_time = time()
        
        logger.debug(
            f"Function '{func.__name__}' executed in {end_time - start_time:.2f} seconds"
        )
        return result
    return wrapper
```

## 5. Testing Setup
### 5.1 Test Configuration
```python
# tests/test_initialization.py
import pytest
from src.core.initialization import SystemInitializer
from src.config.settings import Settings

@pytest.fixture
def system_initializer():
    return SystemInitializer()

def test_environment_validation(system_initializer):
    """Test environment validation."""
    assert system_initializer.validate_environment() is True

def test_system_initialization(system_initializer):
    """Test complete system initialization."""
    assert system_initializer.initialize_system() is True
```

## 6. Installation and Setup Instructions

### 6.1 Development Setup
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows
./venv/Scripts/activate

# or for Unix/MacOS
source venv/bin/activate

# Install dependencies with development packages
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

### 6.2 Production Setup
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows
venv\Scripts\activate
# Unix/MacOS
source venv/bin/activate

# Install production dependencies
pip install -e .
```

## 7. Usage Example
```python
from src.core.initialization import SystemInitializer

def main():
    # Initialize system
    initializer = SystemInitializer()
    
    # Check if initialization was successful
    if initializer.initialize_system():
        print("System initialized successfully")
    else:
        print("System initialization failed")

if __name__ == "__main__":
    main()
```

## 8. Next Steps
After completing Phase A1:
1. Verify all dependencies are installed correctly
2. Ensure logging is working as expected
3. Validate environment variables are set properly
4. Run test suite to confirm setup
5. Proceed to Phase A2: Knowledge Base Implementation