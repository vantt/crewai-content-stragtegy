"""Agent metrics and performance tracking."""
from typing import Dict, Any, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field
import uuid

class AgentMetrics(BaseModel):
    """Metrics for tracking agent performance."""
    agent_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    success_rate: float = 0.0
    response_times: List[float] = Field(default_factory=list)
    task_counts: Dict[str, int] = Field(default_factory=dict)
    error_counts: Dict[str, int] = Field(default_factory=dict)
    resource_usage: Dict[str, float] = Field(default_factory=dict)
    last_updated: datetime = Field(default_factory=datetime.now)
    action_history: List[Dict[str, Any]] = Field(default_factory=list)

    def log_action(
        self,
        action_name: str,
        duration: float,
        success: bool,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Log an agent action.
        
        Args:
            action_name: Name of the action
            duration: Time taken to complete action
            success: Whether action was successful
            metadata: Optional additional information
            
        Returns:
            Action record
        """
        action_record = {
            "action_name": action_name,
            "duration": duration,
            "success": success,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        
        self.action_history.append(action_record)
        
        # Update task counts
        self.task_counts[action_name] = self.task_counts.get(action_name, 0) + 1
        
        # Update response times
        self.response_times.append(duration)
        if len(self.response_times) > 100:  # Keep last 100 times
            self.response_times = self.response_times[-100:]
        
        # Update success rate
        total_tasks = sum(self.task_counts.values())
        total_errors = sum(self.error_counts.values())
        self.success_rate = (total_tasks - total_errors) / total_tasks if total_tasks > 0 else 0.0
        
        self.last_updated = datetime.now()
        return action_record

    def add_task_completion(self, task_type: str, duration: float, success: bool) -> None:
        """Record task completion metrics.
        
        Args:
            task_type: Type of task completed
            duration: Time taken to complete task
            success: Whether task was successful
        """
        # Update task counts
        self.task_counts[task_type] = self.task_counts.get(task_type, 0) + 1
        
        # Update response times
        self.response_times.append(duration)
        if len(self.response_times) > 100:  # Keep last 100 times
            self.response_times = self.response_times[-100:]
        
        # Update success rate
        total_tasks = sum(self.task_counts.values())
        total_errors = sum(self.error_counts.values())
        self.success_rate = (total_tasks - total_errors) / total_tasks if total_tasks > 0 else 0.0
        
        self.last_updated = datetime.now()

    def add_error(self, error_type: str) -> None:
        """Record an error occurrence.
        
        Args:
            error_type: Type of error encountered
        """
        self.error_counts[error_type] = self.error_counts.get(error_type, 0) + 1
        
        # Update success rate
        total_tasks = sum(self.task_counts.values())
        total_errors = sum(self.error_counts.values())
        self.success_rate = (total_tasks - total_errors) / total_tasks if total_tasks > 0 else 0.0
        
        self.last_updated = datetime.now()

    def update_resource_usage(
        self,
        cpu_percent: float,
        memory_mb: float,
        active_tasks: int
    ) -> None:
        """Update resource usage metrics.
        
        Args:
            cpu_percent: CPU usage percentage
            memory_mb: Memory usage in MB
            active_tasks: Number of active tasks
        """
        self.resource_usage.update({
            "cpu_percent": cpu_percent,
            "memory_mb": memory_mb,
            "active_tasks": active_tasks
        })
        self.last_updated = datetime.now()

    def get_average_response_time(self) -> float:
        """Get average response time.
        
        Returns:
            Average response time in seconds
        """
        return sum(self.response_times) / len(self.response_times) if self.response_times else 0.0

    def get_error_rate(self) -> float:
        """Get error rate.
        
        Returns:
            Error rate as percentage
        """
        total_tasks = sum(self.task_counts.values())
        total_errors = sum(self.error_counts.values())
        return (total_errors / total_tasks * 100) if total_tasks > 0 else 0.0

    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get summary of all metrics.
        
        Returns:
            Dictionary of metric summaries
        """
        return {
            "agent_id": self.agent_id,
            "success_rate": self.success_rate,
            "avg_response_time": self.get_average_response_time(),
            "error_rate": self.get_error_rate(),
            "total_tasks": sum(self.task_counts.values()),
            "total_errors": sum(self.error_counts.values()),
            "resource_usage": self.resource_usage,
            "last_updated": self.last_updated.isoformat()
        }

class AgentMetricsCollector:
    """Collector for managing multiple agents' metrics."""
    
    def __init__(self):
        """Initialize metrics collector."""
        self.agent_metrics: Dict[str, AgentMetrics] = {}

    def get_or_create_metrics(self, agent_id: str) -> AgentMetrics:
        """Get or create metrics for an agent.
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            Agent metrics instance
        """
        if agent_id not in self.agent_metrics:
            self.agent_metrics[agent_id] = AgentMetrics(agent_id=agent_id)
        return self.agent_metrics[agent_id]

    def record_task(
        self,
        agent_id: str,
        task_type: str,
        duration: float,
        success: bool
    ) -> None:
        """Record task completion for an agent.
        
        Args:
            agent_id: Agent identifier
            task_type: Type of task completed
            duration: Time taken to complete task
            success: Whether task was successful
        """
        metrics = self.get_or_create_metrics(agent_id)
        metrics.add_task_completion(task_type, duration, success)

    def record_error(self, agent_id: str, error_type: str) -> None:
        """Record error for an agent.
        
        Args:
            agent_id: Agent identifier
            error_type: Type of error encountered
        """
        metrics = self.get_or_create_metrics(agent_id)
        metrics.add_error(error_type)

    def update_resources(
        self,
        agent_id: str,
        cpu_percent: float,
        memory_mb: float,
        active_tasks: int
    ) -> None:
        """Update resource usage for an agent.
        
        Args:
            agent_id: Agent identifier
            cpu_percent: CPU usage percentage
            memory_mb: Memory usage in MB
            active_tasks: Number of active tasks
        """
        metrics = self.get_or_create_metrics(agent_id)
        metrics.update_resource_usage(cpu_percent, memory_mb, active_tasks)

    def get_all_metrics(self) -> Dict[str, Dict[str, Any]]:
        """Get metrics for all agents.
        
        Returns:
            Dictionary of agent metrics summaries
        """
        return {
            agent_id: metrics.get_metrics_summary()
            for agent_id, metrics in self.agent_metrics.items()
        }

    def get_system_summary(self) -> Dict[str, Any]:
        """Get system-wide metrics summary.
        
        Returns:
            System metrics summary
        """
        all_metrics = self.get_all_metrics()
        if not all_metrics:
            return {}
            
        total_tasks = sum(m["total_tasks"] for m in all_metrics.values())
        total_errors = sum(m["total_errors"] for m in all_metrics.values())
        avg_success_rate = sum(m["success_rate"] for m in all_metrics.values()) / len(all_metrics)
        avg_response_time = sum(m["avg_response_time"] for m in all_metrics.values()) / len(all_metrics)
        
        return {
            "total_agents": len(all_metrics),
            "total_tasks": total_tasks,
            "total_errors": total_errors,
            "avg_success_rate": avg_success_rate,
            "avg_response_time": avg_response_time,
            "active_agents": sum(
                1 for m in all_metrics.values()
                if m["resource_usage"].get("active_tasks", 0) > 0
            )
        }
