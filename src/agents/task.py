"""Task execution and management functionality."""
from typing import Dict, Any, Optional, TypeVar, cast
import asyncio
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from crewai import Task
from loguru import logger

from .exceptions import TaskExecutionError
from .models import TaskConfig

T = TypeVar('T')

class TaskManager:
    """Handles task execution and management for agents."""
    
    def __init__(self, max_rpm: int = 10, timeout: int = 120):
        """Initialize TaskManager.
        
        Args:
            max_rpm: Maximum requests per minute (rate limit)
            timeout: Timeout in seconds for task execution
        """
        self._executor = ThreadPoolExecutor(max_workers=1)
        self._rate_limiter = asyncio.Semaphore(max_rpm)
        self._current_task: Optional[str] = None
        self.config = TaskConfig(
            max_rpm=max_rpm,
            timeout=timeout
        )
        self._metrics: Dict[str, Any] = {
            'total_executions': 0,
            'successful_executions': 0,
            'failed_executions': 0,
            'total_duration': 0.0,
            'rate_limit_hits': 0
        }
    
    @property
    def current_task(self) -> Optional[str]:
        """Get the currently executing task description."""
        return self._current_task
    
    def _record_execution_metric(self, metric_type: str, duration: float) -> None:
        """Record execution metrics."""
        self._metrics['total_executions'] += 1
        self._metrics['total_duration'] += duration
        
        if metric_type == 'rate_limit':
            self._metrics['successful_executions'] += 1
        elif metric_type == 'rate_limit_timeout':
            self._metrics['rate_limit_hits'] += 1
        elif metric_type == 'rate_limit_error':
            self._metrics['failed_executions'] += 1
    
    async def execute_task(self, task: Task, crew_agent: Any) -> Dict[str, Any]:
        """Execute a given task using the CrewAI agent.
        
        Args:
            task: The Task to execute
            crew_agent: The CrewAI agent instance to use
            
        Returns:
            Dict containing task results
            
        Raises:
            TaskExecutionError: If task execution fails
        """
        self._current_task = task.description
        start_time = datetime.now()
        
        try:
            async with self._rate_limiter:
                # Add delay to ensure rate limiting
                await asyncio.sleep(0.15)  # Increased delay
                
                # Execute task using CrewAI
                result = await crew_agent.execute(task)
                
                execution_result = {
                    'task': task.description,
                    'result': result,
                    'start_time': start_time,
                    'end_time': datetime.now(),
                    'status': 'success'
                }
                
                self._record_execution_metric('rate_limit', (datetime.now() - start_time).total_seconds())
                return execution_result
                
        except Exception as e:
            logger.error(f"Task execution failed: {str(e)}")
            error_result = {
                'task': task.description,
                'error': str(e),
                'start_time': start_time,
                'end_time': datetime.now(),
                'status': 'failed'
            }
            self._record_execution_metric('rate_limit_error', (datetime.now() - start_time).total_seconds())
            raise TaskExecutionError(str(e), error_result)
            
        finally:
            self._current_task = None
    
    def cleanup(self):
        """Cleanup task manager resources."""
        self._executor.shutdown(wait=True)
        self._metrics.clear()
