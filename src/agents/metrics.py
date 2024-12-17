"""Performance metrics tracking and analysis."""
from typing import List, Optional, Dict, Any
from datetime import datetime

from .types import (
    MetricsData, ActionRecord, ActionStatus, ActionRecordDict,
    Timestamp, Duration, Result, ValidationResult,
    is_metrics_data
)
from .models import MetricsConfig

class AgentMetrics:
    """Handles agent performance metrics and analysis.
    
    This class tracks and analyzes agent performance by recording actions,
    calculating success rates, monitoring response times, and providing
    performance insights.
    
    Attributes:
        config: Configuration settings for metrics collection
        action_history: Complete history of recorded actions
        latest_metrics: Most recent performance metrics
    """
    
    def __init__(self, config: Optional[MetricsConfig] = None) -> None:
        """Initialize metrics tracking.
        
        Args:
            config: Optional metrics configuration settings. If not provided,
                   default settings will be used.
                   
        Raises:
            ValueError: If configuration is invalid
        """
        self.config = config or MetricsConfig()
        self._validate_config()
        self._action_history: List[ActionRecord] = []
        self._performance_metrics: MetricsData = self._create_empty_metrics()
    
    def _validate_config(self) -> ValidationResult:
        """Validate metrics configuration.
        
        Returns:
            Tuple of (is_valid, error_message)
            
        Raises:
            ValueError: If configuration is invalid
        """
        is_valid, error = self.config.validate()
        if not is_valid:
            raise ValueError(f"Invalid metrics configuration: {error}")
        return True, None
    
    def _create_empty_metrics(self) -> MetricsData:
        """Create empty metrics data structure.
        
        Returns:
            Empty metrics data dictionary
        """
        return {
            'total_actions': 0,
            'successful_actions': 0,
            'failed_actions': 0,
            'total_duration': 0.0,
            'average_response_time': 0.0,
            'success_rate': 0.0,
            'error_rate': 0.0,
            'last_action': None,
            'last_status': None,
            'last_updated': datetime.now(),
            'warning': None
        }
    
    def log_action(
        self,
        action_name: str,
        status: str,
        start_time: Optional[Timestamp] = None,
        duration: Optional[Duration] = None,
        error: Optional[str] = None,
        **kwargs: Any
    ) -> Result[ActionRecord]:
        """Log an agent action with timing and status information.
        
        Args:
            action_name: Name of the action performed
            status: Status of the action ('success' or 'failed')
            start_time: Optional start time of the action
            duration: Optional duration of the action in seconds
            error: Optional error message if action failed
            **kwargs: Additional action metadata
            
        Returns:
            Result containing the recorded action or error message
            
        Example:
            >>> metrics.log_action(
            ...     action_name="process_data",
            ...     status="success",
            ...     duration=1.5,
            ...     metadata={"items_processed": 100}
            ... )
        """
        try:
            now = datetime.now()
            timestamp = start_time or now
            action_duration = duration or 0.0
            if start_time and not duration:
                action_duration = (now - start_time).total_seconds()
            
            action_record: ActionRecord = {
                'action': action_name,
                'timestamp': timestamp,
                'duration': action_duration,
                'status': status,
                'error': error,
                'metadata': kwargs.get('metadata', {})
            }
            
            # Add to front of list (most recent first)
            self._action_history.insert(0, action_record)
            
            # Maintain history size limit
            while len(self._action_history) > self.config.history_size:
                self._action_history.pop()
                
            self._update_metrics(action_record)
            return Result.ok(action_record)
            
        except Exception as e:
            return Result.err(f"Failed to log action: {str(e)}")
    
    def _update_metrics(self, action_record: ActionRecord) -> None:
        """Update performance metrics with new action.
        
        Args:
            action_record: Record of the action performed
        """
        metrics: MetricsData = {}
        metrics['last_action'] = action_record['action']
        metrics['last_status'] = action_record['status']
        metrics['total_actions'] = len(self._action_history)
        
        successful = sum(1 for a in self._action_history 
                        if a['status'] == ActionStatus.SUCCESS.value)
        failed = sum(1 for a in self._action_history 
                    if a['status'] == ActionStatus.FAILED.value)
        total = len(self._action_history)
        
        metrics['successful_actions'] = successful
        metrics['failed_actions'] = failed
        metrics['success_rate'] = successful / total if total > 0 else 0.0
        metrics['error_rate'] = failed / total if total > 0 else 0.0
        
        durations = [a['duration'] for a in self._action_history 
                    if 'duration' in a]
        metrics['total_duration'] = sum(durations)
        metrics['average_response_time'] = (sum(durations) / len(durations) 
                                          if durations else 0.0)
        metrics['last_updated'] = datetime.now()
        
        self._performance_metrics = metrics
    
    def analyze_performance(self) -> Result[MetricsData]:
        """Analyze agent's performance metrics.
        
        Calculates comprehensive performance metrics including:
        - Success and error rates
        - Response times
        - Performance warnings
        
        Returns:
            Result containing performance metrics or error message
            
        Example:
            >>> result = metrics.analyze_performance()
            >>> if result.success:
            ...     performance = result.value
            ...     print(f"Success rate: {performance['success_rate']:.2%}")
        """
        try:
            if not self._action_history:
                return Result.ok(self._create_empty_metrics())
            
            successful = sum(1 for a in self._action_history 
                           if a['status'] == ActionStatus.SUCCESS.value)
            failed = sum(1 for a in self._action_history 
                        if a['status'] == ActionStatus.FAILED.value)
            total = len(self._action_history)
            durations = [a['duration'] for a in self._action_history 
                        if 'duration' in a]
            
            metrics: MetricsData = {
                'total_actions': total,
                'successful_actions': successful,
                'failed_actions': failed,
                'success_rate': successful / total if total > 0 else 0.0,
                'error_rate': failed / total if total > 0 else 0.0,
                'total_duration': sum(durations),
                'average_response_time': (sum(durations) / len(durations) 
                                        if durations else 0.0),
                'last_updated': datetime.now(),
                'warning': None
            }
            
            # Check performance threshold
            if metrics['success_rate'] < self.config.performance_threshold:
                metrics['warning'] = (
                    f"Success rate {metrics['success_rate']:.2%} below "
                    f"threshold {self.config.performance_threshold:.2%}"
                )
            
            if not is_metrics_data(metrics):
                return Result.err("Invalid metrics data format")
            
            self._performance_metrics = metrics
            return Result.ok(metrics)
            
        except Exception as e:
            return Result.err(f"Failed to analyze performance: {str(e)}")
    
    @property
    def action_history(self) -> List[ActionRecord]:
        """Get the complete action history."""
        return self._action_history.copy()
    
    @property
    def latest_metrics(self) -> MetricsData:
        """Get the most recent performance metrics."""
        return self._performance_metrics.copy()
    
    def clear_history(self) -> None:
        """Clear action history and reset metrics."""
        self._action_history.clear()
        self._performance_metrics = self._create_empty_metrics()
