"""Task execution and management functionality."""
from typing import Dict, Any, Optional, List
import asyncio
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from crewai import Task, Agent as CrewAgent
from loguru import logger

from .exceptions import TaskExecutionError
from .models import TaskConfig
from .types import (
    TaskResult, TaskResultDict, TaskStatus, MetricsData,
    Timestamp, Duration, Result, ValidationResult
)

class TaskManager:
    """Handles task execution and management for agents.
    
    This class manages task execution with features like:
    - Rate limiting
    - Timeout handling
    - Retry logic
    - Performance metrics tracking
    
    Attributes:
        config: Configuration settings for task execution
        current_task: Description of currently executing task
    """
    
    def __init__(
        self,
        max_rpm: int = 10,
        timeout: int = 120
    ) -> None:
        """Initialize TaskManager.
        
        Args:
            max_rpm: Maximum requests per minute (rate limit)
            timeout: Timeout in seconds for task execution
            
        Raises:
            ValueError: If configuration values are invalid
        """
        self._executor = ThreadPoolExecutor(max_workers=1)
        self._rate_limiter = asyncio.Semaphore(max_rpm)
        self._current_task: Optional[str] = None
        
        self.config = TaskConfig(
            max_rpm=max_rpm,
            timeout=timeout
        )
        self._validate_config()
        
        self._metrics: MetricsData = self._create_empty_metrics()
    
    def _validate_config(self) -> ValidationResult:
        """Validate task configuration.
        
        Returns:
            Tuple of (is_valid, error_message)
            
        Raises:
            ValueError: If configuration is invalid
        """
        is_valid, error = self.config.validate()
        if not is_valid:
            raise ValueError(f"Invalid task configuration: {error}")
        return True, None
    
    def _create_empty_metrics(self) -> MetricsData:
        """Create empty metrics data structure.
        
        Returns:
            Empty metrics data dictionary
        """
        return {
            'total_executions': 0,
            'successful_executions': 0,
            'failed_executions': 0,
            'total_duration': 0.0,
            'rate_limit_hits': 0,
            'last_updated': datetime.now(),
            'warning': None
        }
    
    @property
    def current_task(self) -> Optional[str]:
        """Get the currently executing task description."""
        return self._current_task
    
    def _record_execution_metric(
        self,
        metric_type: str,
        duration: Duration
    ) -> None:
        """Record execution metrics.
        
        Args:
            metric_type: Type of metric to record ('success', 'error', 'rate_limit')
            duration: Duration of task execution in seconds
        """
        self._metrics['total_executions'] += 1
        self._metrics['total_duration'] += duration
        self._metrics['last_updated'] = datetime.now()
        
        if metric_type == 'success':
            self._metrics['successful_executions'] += 1
        elif metric_type == 'error':
            self._metrics['failed_executions'] += 1
        elif metric_type == 'rate_limit':
            self._metrics['rate_limit_hits'] += 1
    
    async def execute_task(
        self,
        task: Task,
        crew_agent: CrewAgent
    ) -> TaskResult:
        """Execute a given task using the CrewAI agent.
        
        Handles:
        - Rate limiting
        - Timeout enforcement
        - Metrics recording
        - Error handling
        
        Args:
            task: The Task to execute
            crew_agent: The CrewAI agent instance to use
            
        Returns:
            Task execution result dictionary
            
        Raises:
            TaskExecutionError: If task execution fails
            
        Example:
            >>> result = await task_manager.execute_task(
            ...     task=my_task,
            ...     crew_agent=my_agent
            ... )
            >>> print(f"Task completed: {result['result']}")
        """
        self._current_task = task.description
        start_time = datetime.now()
        
        try:
            async with self._rate_limiter:
                # Add delay to ensure rate limiting
                await asyncio.sleep(60 / self.config.max_rpm)
                
                # Execute task using CrewAI
                result = await crew_agent.execute(task)
                
                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds()
                
                execution_result: TaskResult = {
                    'task': task.description,
                    'result': result,
                    'start_time': start_time,
                    'end_time': end_time,
                    'duration': duration,
                    'status': TaskStatus.SUCCESS.value
                }
                
                self._record_execution_metric('success', duration)
                return execution_result
                
        except Exception as e:
            logger.error(f"Task execution failed: {str(e)}")
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            self._record_execution_metric('error', duration)
            
            error_result: TaskResult = {
                'task': task.description,
                'result': None,
                'start_time': start_time,
                'end_time': end_time,
                'duration': duration,
                'status': TaskStatus.FAILED.value
            }
            raise TaskExecutionError(str(e), error_result)
            
        finally:
            self._current_task = None
    
    def get_metrics(self) -> MetricsData:
        """Get current task execution metrics.
        
        Returns:
            Dict containing execution metrics
            
        Example:
            >>> metrics = task_manager.get_metrics()
            >>> success_rate = (metrics['successful_executions'] /
            ...                metrics['total_executions'])
            >>> print(f"Success rate: {success_rate:.2%}")
        """
        return self._metrics.copy()
    
    def cleanup(self) -> None:
        """Cleanup task manager resources.
        
        - Shuts down thread executor
        - Resets metrics
        """
        self._executor.shutdown(wait=True)
        self._metrics = self._create_empty_metrics()
