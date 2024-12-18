"""Tests for agent adapters."""
import pytest
from unittest.mock import Mock, AsyncMock
from typing import Dict, Any, List

from src.core import (
    EventEmitter,
    StateManager,
    Event,
    EventType,
    DebateStatus
)
from src.agents.adapters import (
    StrategyAnalystAdapter,
    MarketSkepticAdapter,
    DebateSessionManager
)

@pytest.fixture
async def event_emitter():
    """Fixture providing an event emitter instance."""
    emitter = EventEmitter()
    async with emitter:
        yield emitter

@pytest.fixture
def state_manager(event_emitter):
    """Fixture providing a state manager instance."""
    return StateManager(event_emitter)

@pytest.fixture
def mock_analyst():
    """Fixture providing a mock strategy analyst."""
    analyst = Mock()
    analyst.conduct_strategy_analysis = AsyncMock(return_value=Mock(
        model_dump=lambda: {"analysis": "test"}
    ))
    return analyst

@pytest.fixture
def mock_skeptic():
    """Fixture providing a mock market skeptic."""
    skeptic = Mock()
    skeptic.generate_challenge = AsyncMock(return_value=Mock(
        model_dump=lambda: {"challenge": "test"}
    ))
    return skeptic

@pytest.mark.asyncio
async def test_analyst_adapter(
    event_emitter: EventEmitter,
    state_manager: StateManager,
    mock_analyst: Mock
):
    """Test the strategy analyst adapter."""
    # Track emitted events
    events: List[Event] = []
    async def track_events(event: Event):
        events.append(event)
    
    # Register event tracker
    for event_type in EventType:
        event_emitter.add_handler(event_type, track_events)
    
    # Create adapter
    adapter = StrategyAnalystAdapter(
        mock_analyst,
        event_emitter,
        state_manager,
        "test_debate"
    )
    
    # Test market analysis
    result = await adapter.analyze_market({"test": "data"})
    
    # Verify result
    assert result == {"analysis": "test"}
    
    # Verify events were emitted
    assert len(events) == 3  # start, complete, argument
    assert events[0].event_type == EventType.AGENT_TASK_STARTED
    assert events[1].event_type == EventType.AGENT_TASK_COMPLETED
    assert events[2].event_type == EventType.ARGUMENT_SUBMITTED

@pytest.mark.asyncio
async def test_skeptic_adapter(
    event_emitter: EventEmitter,
    state_manager: StateManager,
    mock_skeptic: Mock
):
    """Test the market skeptic adapter."""
    # Track emitted events
    events: List[Event] = []
    async def track_events(event: Event):
        events.append(event)
    
    # Register event tracker
    for event_type in EventType:
        event_emitter.add_handler(event_type, track_events)
    
    # Create adapter
    adapter = MarketSkepticAdapter(
        mock_skeptic,
        event_emitter,
        state_manager,
        "test_debate"
    )
    
    # Test challenge generation
    result = await adapter.challenge_analysis({"analysis": "test"})
    
    # Verify result
    assert result == {"challenge": "test"}
    
    # Verify events were emitted
    assert len(events) == 3  # start, complete, argument
    assert events[0].event_type == EventType.AGENT_TASK_STARTED
    assert events[1].event_type == EventType.AGENT_TASK_COMPLETED
    assert events[2].event_type == EventType.ARGUMENT_SUBMITTED

@pytest.mark.asyncio
async def test_debate_session(
    event_emitter: EventEmitter,
    state_manager: StateManager,
    mock_analyst: Mock,
    mock_skeptic: Mock
):
    """Test the debate session manager."""
    # Create adapters
    analyst_adapter = StrategyAnalystAdapter(
        mock_analyst,
        event_emitter,
        state_manager,
        "test_debate"
    )
    
    skeptic_adapter = MarketSkepticAdapter(
        mock_skeptic,
        event_emitter,
        state_manager,
        "test_debate"
    )
    
    # Create session manager
    session = DebateSessionManager(
        analyst_adapter,
        skeptic_adapter,
        event_emitter,
        state_manager
    )
    
    # Track debate state changes
    states: List[DebateStatus] = []
    async def track_state_change(event: Event):
        if "debate_id" in event.data:
            state = await state_manager.get_debate_state(event.data["debate_id"])
            if state:
                states.append(state)
    
    # Register state tracker
    for event_type in EventType:
        event_emitter.add_handler(event_type, track_state_change)
    
    # Conduct debate
    result = await session.conduct_debate({"test": "data"})
    
    # Verify result structure
    assert "initial_analysis" in result
    assert "challenge" in result
    assert "final_analysis" in result
    assert "debate_id" in result
    
    # Verify state transitions
    assert DebateStatus.IN_PROGRESS in states
    assert DebateStatus.CONSENSUS_REACHED in states

@pytest.mark.asyncio
async def test_debate_session_failure(
    event_emitter: EventEmitter,
    state_manager: StateManager,
    mock_analyst: Mock,
    mock_skeptic: Mock
):
    """Test debate session failure handling."""
    # Make analyst fail
    mock_analyst.conduct_strategy_analysis.side_effect = Exception("Test error")
    
    # Create adapters
    analyst_adapter = StrategyAnalystAdapter(
        mock_analyst,
        event_emitter,
        state_manager,
        "test_debate"
    )
    
    skeptic_adapter = MarketSkepticAdapter(
        mock_skeptic,
        event_emitter,
        state_manager,
        "test_debate"
    )
    
    # Create session manager
    session = DebateSessionManager(
        analyst_adapter,
        skeptic_adapter,
        event_emitter,
        state_manager
    )
    
    # Conduct debate and expect failure
    with pytest.raises(Exception):
        await session.conduct_debate({"test": "data"})
    
    # Verify debate failed
    state = await state_manager.get_debate_state(session.debate_id)
    assert state == DebateStatus.FAILED
