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