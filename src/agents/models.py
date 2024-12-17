"""Data models for agent configuration and state."""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum
from datetime import datetime

class AgentRole(str, Enum):
    """Defines possible agent roles."""
    STRATEGY = "strategy"
    MARKETING = "marketing"
    CONTENT = "content"
    PLANNING = "planning"
    EXECUTION = "execution"
    CRITIC = "critic"

class AgentType(str, Enum):
    """Defines possible agent types."""
    PRIMARY = "primary"
    ADVERSARY = "adversary"
    ASSISTANT = "assistant"

@dataclass
class TaskConfig:
    """Configuration settings for task execution."""
    max_rpm: int = 10
    timeout: int = 120
    retry_attempts: int = 3
    retry_delay: float = 1.0
    batch_size: int = 5

@dataclass
class AgentConfig:
    """Configuration settings for an agent."""
    role: AgentRole
    agent_type: AgentType
    temperature: float = 0.7
    max_iterations: int = 3
    max_rpm: int = 10
    timeout: int = 120
    context_window: int = 4000
    memory_size: int = 5

@dataclass
class AgentState:
    """Maintains agent state information."""
    action_history: List[Dict[str, Any]] = field(default_factory=list)
    last_action: Optional[str] = None
    last_action_time: Optional[datetime] = None
    error_count: int = 0
    success_count: int = 0
    
    def add_action(self, action: Dict[str, Any]) -> None:
        """Add an action to history.
        
        Args:
            action: Dictionary containing action details
        """
        self.action_history.append(action)
        self.last_action = action.get('action')
        self.last_action_time = action.get('timestamp')
        
        if action.get('status') == 'success':
            self.success_count += 1
        else:
            self.error_count += 1
    
    def clear(self) -> None:
        """Clear agent state."""
        self.action_history.clear()
        self.last_action = None
        self.last_action_time = None
        self.error_count = 0
        self.success_count = 0

@dataclass
class MemoryConfig:
    """Configuration settings for agent memory."""
    memory_size: int = 100
    relevance_threshold: float = 0.5
    max_context_length: int = 2000
    ttl_seconds: int = 3600  # Time to live for memories

@dataclass
class MetricsConfig:
    """Configuration settings for metrics collection."""
    enabled: bool = True
    history_size: int = 1000
    aggregation_interval: int = 60  # seconds
    performance_threshold: float = 0.8
