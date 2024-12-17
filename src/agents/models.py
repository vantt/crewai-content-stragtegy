"""Data models for agent configuration and state."""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime

from .types import (
    AgentRole, AgentType, ActionRecord, ActionStatus,
    Timestamp, Duration, MetadataDict, ValidationResult
)

@dataclass
class TaskConfig:
    """Configuration settings for task execution.
    
    Attributes:
        max_rpm: Maximum requests per minute for rate limiting
        timeout: Maximum time in seconds to wait for task completion
        retry_attempts: Number of retry attempts for failed tasks
        retry_delay: Delay in seconds between retry attempts
        batch_size: Maximum number of concurrent tasks
    """
    max_rpm: int = 10
    timeout: int = 120
    retry_attempts: int = 3
    retry_delay: float = 1.0
    batch_size: int = 5

    def validate(self) -> ValidationResult:
        """Validate configuration values.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        if self.max_rpm <= 0:
            return False, "max_rpm must be positive"
        if self.timeout <= 0:
            return False, "timeout must be positive"
        if self.retry_attempts < 0:
            return False, "retry_attempts cannot be negative"
        if self.retry_delay < 0:
            return False, "retry_delay cannot be negative"
        if self.batch_size <= 0:
            return False, "batch_size must be positive"
        return True, None

@dataclass
class AgentConfig:
    """Configuration settings for an agent.
    
    Attributes:
        role: Agent's role in the system
        agent_type: Type of agent (primary, adversary, assistant)
        temperature: Sampling temperature for agent decisions (0-1)
        max_iterations: Maximum iterations for task attempts
        max_rpm: Maximum requests per minute
        timeout: Operation timeout in seconds
        context_window: Size of context window in tokens
        memory_size: Maximum number of memory items to retain
    """
    role: AgentRole
    agent_type: AgentType
    temperature: float = 0.7
    max_iterations: int = 3
    max_rpm: int = 10
    timeout: int = 120
    context_window: int = 4000
    memory_size: int = 5

    def validate(self) -> ValidationResult:
        """Validate configuration values.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not isinstance(self.role, AgentRole):
            return False, f"Invalid role: {self.role}"
        if not isinstance(self.agent_type, AgentType):
            return False, f"Invalid agent type: {self.agent_type}"
        if not 0 <= self.temperature <= 1:
            return False, "Temperature must be between 0 and 1"
        if self.max_iterations <= 0:
            return False, "max_iterations must be positive"
        if self.max_rpm <= 0:
            return False, "max_rpm must be positive"
        if self.timeout <= 0:
            return False, "timeout must be positive"
        if self.context_window <= 0:
            return False, "context_window must be positive"
        if self.memory_size <= 0:
            return False, "memory_size must be positive"
        return True, None

@dataclass
class AgentState:
    """Maintains agent state information.
    
    Attributes:
        action_history: List of past actions with metadata
        last_action: Description of most recent action
        last_action_time: Timestamp of most recent action
        error_count: Count of failed actions
        success_count: Count of successful actions
    """
    action_history: List[ActionRecord] = field(default_factory=list)
    last_action: Optional[str] = None
    last_action_time: Optional[Timestamp] = None
    error_count: int = 0
    success_count: int = 0
    
    def add_action(self, action: ActionRecord) -> None:
        """Add an action to history.
        
        Args:
            action: Dictionary containing action details including status
        """
        self.action_history.append(action)
        self.last_action = action.get('action')
        self.last_action_time = action.get('timestamp')
        
        if action.get('status') == ActionStatus.SUCCESS.value:
            self.success_count += 1
        else:
            self.error_count += 1
    
    def clear(self) -> None:
        """Clear agent state and reset counters."""
        self.action_history.clear()
        self.last_action = None
        self.last_action_time = None
        self.error_count = 0
        self.success_count = 0

    @property
    def total_actions(self) -> int:
        """Get total number of actions performed."""
        return len(self.action_history)

    @property
    def success_rate(self) -> float:
        """Get success rate of actions."""
        total = self.total_actions
        return self.success_count / total if total > 0 else 0.0

@dataclass
class MemoryConfig:
    """Configuration settings for agent memory.
    
    Attributes:
        memory_size: Maximum number of memory items to retain
        relevance_threshold: Minimum relevance score for memory retrieval
        max_context_length: Maximum length of context in tokens
        ttl_seconds: Time-to-live for memory items in seconds
    """
    memory_size: int = 100
    relevance_threshold: float = 0.5
    max_context_length: int = 2000
    ttl_seconds: int = 3600

    def validate(self) -> ValidationResult:
        """Validate configuration values.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        if self.memory_size <= 0:
            return False, "memory_size must be positive"
        if not 0 <= self.relevance_threshold <= 1:
            return False, "relevance_threshold must be between 0 and 1"
        if self.max_context_length <= 0:
            return False, "max_context_length must be positive"
        if self.ttl_seconds <= 0:
            return False, "ttl_seconds must be positive"
        return True, None

@dataclass
class MetricsConfig:
    """Configuration settings for metrics collection.
    
    Attributes:
        enabled: Whether metrics collection is enabled
        history_size: Maximum number of metrics records to retain
        aggregation_interval: Interval in seconds for metrics aggregation
        performance_threshold: Minimum acceptable success rate
    """
    enabled: bool = True
    history_size: int = 1000
    aggregation_interval: int = 60
    performance_threshold: float = 0.8

    def validate(self) -> ValidationResult:
        """Validate configuration values.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        if self.history_size <= 0:
            return False, "history_size must be positive"
        if self.aggregation_interval <= 0:
            return False, "aggregation_interval must be positive"
        if not 0 <= self.performance_threshold <= 1:
            return False, "performance_threshold must be between 0 and 1"
        return True, None
