# src/agents/types.py
from enum import Enum

class AgentRole(str, Enum):
    """Define possible roles for agents."""
    STRATEGY = "strategy"
    MARKETING = "marketing"
    CONTENT = "content"
    PLANNING = "planning"
    EXECUTION = "execution"
    CRITIC = "critic"

class AgentType(str, Enum):
    """Define types of agents."""
    PRIMARY = "primary"
    ADVERSARY = "adversary"

