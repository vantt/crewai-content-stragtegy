"""Performance metrics tracking and analysis."""
from typing import Dict, List, Any, Optional
from datetime import datetime

class AgentMetrics:
    """Handles agent performance metrics and analysis."""
    
    def __init__(self):
        self._action_history: List[Dict[str, Any]] = []
        self._performance_metrics: Dict[str, Any] = {}
    
    def log_action(self, action_name: str, start_time: Optional[datetime] = None,
                  status: str = 'success', error: Optional[str] = None,
                  **kwargs) -> None:
        """Log an agent action with timing and status information."""
        now = datetime.now()
        duration = (now - start_time).total_seconds() if start_time else kwargs.get('duration', 0.0)
        
        action_record = {
            'action': action_name,
            'timestamp': start_time or now,
            'duration': duration,
            'status': status,
            **kwargs
        }
        
        if error:
            action_record['error'] = error
            
        self._action_history.append(action_record)
        self._update_metrics(action_record)
    
    def _update_metrics(self, action_record: Dict[str, Any]) -> None:
        """Update performance metrics with new action."""
        metrics = {}
        metrics['last_action'] = action_record['action']
        metrics['last_status'] = action_record['status']
        metrics['total_actions'] = len(self._action_history)
        
        successful = sum(1 for a in self._action_history if a['status'] == 'success')
        failed = sum(1 for a in self._action_history if a['status'] == 'failed')
        total = len(self._action_history)
        
        metrics['success_rate'] = successful / total if total > 0 else 0.0
        metrics['error_rate'] = failed / total if total > 0 else 0.0
        
        durations = [a['duration'] for a in self._action_history if 'duration' in a]
        metrics['average_response_time'] = sum(durations) / len(durations) if durations else 0.0
        metrics['last_updated'] = datetime.now()
        
        self._performance_metrics = metrics
    
    def analyze_performance(self) -> Dict[str, Any]:
        """Analyze agent's performance metrics."""
        if not self._action_history:
            return {
                'total_actions': 0,
                'success_rate': 0.0,
                'average_response_time': 0.0,
                'error_rate': 0.0,
                'last_updated': datetime.now()
            }
        
        successful = sum(1 for a in self._action_history if a['status'] == 'success')
        failed = sum(1 for a in self._action_history if a['status'] == 'failed')
        total = len(self._action_history)
        durations = [a['duration'] for a in self._action_history if 'duration' in a]
        
        metrics = {
            'total_actions': total,
            'success_rate': successful / total if total > 0 else 0.0,
            'error_rate': failed / total if total > 0 else 0.0,
            'average_response_time': sum(durations) / len(durations) if durations else 0.0,
            'last_updated': datetime.now()
        }
        
        self._performance_metrics = metrics
        return metrics
    
    @property
    def action_history(self) -> List[Dict[str, Any]]:
        """Get the complete action history."""
        return self._action_history.copy()
    
    @property
    def latest_metrics(self) -> Dict[str, Any]:
        """Get the most recent performance metrics."""
        return self._performance_metrics.copy()
    
    def clear_history(self) -> None:
        """Clear action history and reset metrics."""
        self._action_history.clear()
        self._performance_metrics.clear()
