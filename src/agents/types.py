"""Type definitions and enums for the agent system."""
from enum import Enum
from typing import Dict, List, Any, Optional, TypeVar, Union
from datetime import datetime

# Type variables
T = TypeVar('T')

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

# Common type aliases
TaskResult = Dict[str, Any]
MemoryItem = Dict[str, Any]
MetricsData = Dict[str, Union[int, float, str, datetime]]
ActionRecord = Dict[str, Any]
Context = List[Dict[str, Any]]

# Callback type hints
MetricsCallback = Optional[callable]
ErrorHandler = Optional[callable]
