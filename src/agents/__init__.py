"""Agent package initialization.

This package contains agent implementations and related functionality.
"""

from .strategy_analyst import StrategyAnalyst
from .strategy_skeptic import MarketSkeptic
from .adapters import (
    StrategyAnalystAdapter,
    MarketSkepticAdapter,
    DebateSessionManager
)
from .orchestrator import DebateOrchestrator

__all__ = [
    'StrategyAnalyst',
    'MarketSkeptic',
    'StrategyAnalystAdapter',
    'MarketSkepticAdapter',
    'DebateSessionManager',
    'DebateOrchestrator'
]
