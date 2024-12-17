"""Performance metrics tracking and analysis."""
from typing import Dict, List, Any, Optional
from datetime import datetime

from .types import MetricsData, ActionRecord
from .models import MetricsConfig

class AgentMetrics:
    """Handles agent performance metrics and analysis."""
    
    def __init__(self, config: Optional[MetricsConfig] = None):
        """Initialize metrics tracking.
        
        Args:
            config: Optional metrics configuration
        """
        self.config = config or MetricsConfig()
        self._action_history: List[ActionRecord] = []
        self._performance_metrics: MetricsData = {
            'total_actions': 0,
            'successful_actions': 0,
            'failed_actions': 0,
            'total_duration': 0.0,
            'average_response_time': 0.0,
            'success_rate': 0.0,
            'error_rate': 0.0,
            'last_action': None,
            'last_status': None,
            'last_updated': datetime.now()
        }
    
    def log_action(self, action_name: str, start_time: Optional[datetime] = None,
                  status: str = 'success', error: Optional[str] = None,
                  **kwargs) -> None:
        """Log an agent action with timing and status information.
        
        Args:
            action_name: Name of the action performed
            start_time: Optional start time of the action
            status: Status of the action ('success' or 'failed')
            error: Optional error message if action failed
            **kwargs: Additional action metadata
        """
        now = datetime.now()
        timestamp = start_time or now
        duration = kwargs.get('duration', 0.0)
        if start_time:
            duration = (now - start_time).total_seconds()
        
        action_record: ActionRecord = {
            'action': action_name,
            'timestamp': timestamp,
            'duration': duration,
            'status': status,
            **kwargs
        }
        
        if error:
            action_record['error'] = error
            
        # Add to front of list (most recent first)
        self._action_history.insert(0, action_record)
        
        # Maintain history size limit
        while len(self._action_history) > self.config.history_size:
            self._action_history.pop()
            
        self._update_metrics(action_record)
    
    def _update_metrics(self, action_record: ActionRecord) -> None:
        """Update performance metrics with new action.
        
        Args:
            action_record: Record of the action performed
        """
        metrics: MetricsData = {}
        metrics['last_action'] = action_record['action']
        metrics['last_status'] = action_record['status']
        metrics['total_actions'] = len(self._action_history)
        
        successful = sum(1 for a in self._action_history if a['status'] == 'success')
        failed = sum(1 for a in self._action_history if a['status'] == 'failed')
        total = len(self._action_history)
        
        metrics['successful_actions'] = successful
        metrics['failed_actions'] = failed
        metrics['success_rate'] = successful / total if total > 0 else 0.0
        metrics['error_rate'] = failed / total if total > 0 else 0.0
        
        durations = [a['duration'] for a in self._action_history if 'duration' in a]
        metrics['total_duration'] = sum(durations)
        metrics['average_response_time'] = sum(durations) / len(durations) if durations else 0.0
        metrics['last_updated'] = datetime.now()
        
        self._performance_metrics = metrics
    
    def analyze_performance(self) -> MetricsData:
        """Analyze agent's performance metrics.
        
        Returns:
            Dict containing performance metrics and analysis
        """
        if not self._action_history:
            return {
                'total_actions': 0,
                'successful_actions': 0,
                'failed_actions': 0,
                'success_rate': 0.0,
                'error_rate': 0.0,
                'total_duration': 0.0,
                'average_response_time': 0.0,
                'last_updated': datetime.now()
            }
        
        successful = sum(1 for a in self._action_history if a['status'] == 'success')
        failed = sum(1 for a in self._action_history if a['status'] == 'failed')
        total = len(self._action_history)
        durations = [a['duration'] for a in self._action_history if 'duration' in a]
        
        metrics: MetricsData = {
            'total_actions': total,
            'successful_actions': successful,
            'failed_actions': failed,
            'success_rate': successful / total if total > 0 else 0.0,
            'error_rate': failed / total if total > 0 else 0.0,
            'total_duration': sum(durations),
            'average_response_time': sum(durations) / len(durations) if durations else 0.0,
            'last_updated': datetime.now()
        }
        
        # Check performance threshold
        if metrics['success_rate'] < self.config.performance_threshold:
            metrics['warning'] = f"Success rate {metrics['success_rate']:.2%} below threshold {self.config.performance_threshold:.2%}"
        
        self._performance_metrics = metrics
        return metrics
    
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
        self._performance_metrics = {
            'total_actions': 0,
            'successful_actions': 0,
            'failed_actions': 0,
            'success_rate': 0.0,
            'error_rate': 0.0,
            'total_duration': 0.0,
            'average_response_time': 0.0,
            'last_updated': datetime.now()
        }
