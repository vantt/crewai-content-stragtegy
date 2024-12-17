"""Decorators for agent functionality."""
from datetime import datetime
from functools import wraps
from typing import Any, TypeVar, cast
from loguru import logger

from .exceptions import ExecutionError

T = TypeVar('T')

def log_action(func):
    """Decorator to log and track agent actions.
    
    This decorator:
    1. Records action start time
    2. Executes the action
    3. Records action completion/failure
    4. Updates metrics
    5. Logs the result
    
    Args:
        func: The async function to decorate
        
    Returns:
        Decorated function that includes logging and tracking
    """
    @wraps(func)
    async def wrapper(self: 'BaseAgent', *args: Any, **kwargs: Any) -> T:
        """Wrapper function that adds logging and tracking."""
        action_start = datetime.now()
        action_name = func.__name__
        action_record = None
        
        try:
            # Execute the action
            result = await func(self, *args, **kwargs)
            action_end = datetime.now()
            duration = (action_end - action_start).total_seconds()
            
            # Record successful action
            action_record = {
                'action': action_name,
                'timestamp': action_start,
                'duration': duration,
                'status': 'success',
                'args': str(args),
                'kwargs': str(kwargs)
            }
            
            # Update metrics
            self._update_performance_metrics(action_name, duration, True)
            
            # Log success
            logger.info(f"Agent {self.name} completed {action_name} in {duration:.2f}s")
            
            return cast(T, result)
            
        except Exception as e:
            action_end = datetime.now()
            duration = (action_end - action_start).total_seconds()
            
            # Record failed action
            action_record = {
                'action': action_name,
                'timestamp': action_start,
                'duration': duration,
                'status': 'failed',
                'error': str(e),
                'args': str(args),
                'kwargs': str(kwargs)
            }
            
            # Update metrics
            self._update_performance_metrics(action_name, duration, False)
            
            # Log error
            logger.error(f"Agent {self.name} failed {action_name}: {str(e)}")
            
            # Ensure error propagation
            if isinstance(e, (ExecutionError, ValueError, TypeError)):
                raise
            raise ExecutionError(f"Action failed: {str(e)}")
            
        finally:
            if action_record:
                # Record action in agent state
                self.record_action(action_record)
    
    # Preserve the method binding
    wrapper.__get__ = lambda self, obj, objtype=None: wrapper.__class__(self, obj) if obj is not None else wrapper
    
    return wrapper
