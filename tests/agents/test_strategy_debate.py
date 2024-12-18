"""Tests for the enhanced strategy debate implementation."""
import pytest
from unittest.mock import Mock, AsyncMock
from datetime import datetime, timedelta
from typing import Dict, Any, List

from src.core import (
    EventEmitter,
    StateManager,
    Event,
    EventType,
    DebateStatus
)
from src.agents.strategy_debate import (
    StrategyDebate,
    Evidence,
    DebateRound,
    DebateRoundMetrics
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

@pytest.fixture
def debate(event_emitter, state_manager, mock_analyst, mock_skeptic):
    """Fixture providing a debate instance."""
    return StrategyDebate(
        mock_analyst,
        mock_skeptic,
        event_emitter,
        state_manager
    )

@pytest.fixture
def sample_evidence():
    """Fixture providing sample evidence data."""
    return {
        "type": "market_research",
        "source": "industry_report",
        "content": {
            "market_size": 1000,
            "growth_rate": 15
        },
        "confidence": 0.9
    }

@pytest.mark.asyncio
async def test_debate_initialization(debate: StrategyDebate):
    """Test debate initialization."""
    assert debate.debate_id is not None
    assert len(debate.rounds) == 0
    assert debate.current_round is None
    assert debate.max_rounds == 5
    assert debate.consensus_threshold == 0.8

@pytest.mark.asyncio
async def test_round_management(debate: StrategyDebate):
    """Test debate round management."""
    # Start first round
    round1 = await debate.start_round()
    assert round1.round_number == 1
    assert debate.current_round == round1
    
    # End round
    metrics = await debate.end_round()
    assert isinstance(metrics, DebateRoundMetrics)
    assert debate.current_round is None
    
    # Start second round
    round2 = await debate.start_round()
    assert round2.round_number == 2
    
    # Verify round history
    history = debate.get_round_history()
    assert len(history) == 2
    assert history[0].round_number == 1
    assert history[1].round_number == 2

@pytest.mark.asyncio
async def test_evidence_tracking(debate: StrategyDebate, sample_evidence: Dict[str, Any]):
    """Test evidence tracking."""
    # Start round
    await debate.start_round()
    
    # Add argument with evidence
    await debate.add_argument(
        agent_id="test_agent",
        argument_type="analysis",
        content={"analysis": "test"},
        evidence=[sample_evidence]
    )
    
    # Verify evidence was added
    assert len(debate.current_round.evidence) == 1
    evidence = debate.current_round.evidence[0]
    assert isinstance(evidence, Evidence)
    assert evidence.type == sample_evidence["type"]
    assert evidence.source == sample_evidence["source"]
    
    # Test evidence retrieval
    retrieved = debate.get_evidence(evidence.evidence_id)
    assert retrieved == evidence

@pytest.mark.asyncio
async def test_metrics_calculation(
    debate: StrategyDebate,
    sample_evidence: Dict[str, Any]
):
    """Test metrics calculation."""
    # Start round
    await debate.start_round()
    
    # Add arguments
    await debate.add_argument(
        agent_id="analyst",
        argument_type="analysis",
        content={
            "analysis": "test",
            "response_points": [
                {"addresses": "concern1"}
            ]
        },
        evidence=[sample_evidence]
    )
    
    await debate.add_argument(
        agent_id="skeptic",
        argument_type="challenge",
        content={
            "concerns": [
                {"id": "concern1", "description": "test"}
            ]
        },
        evidence=[sample_evidence]
    )
    
    # End round and get metrics
    metrics = await debate.end_round()
    
    # Verify round metrics
    assert metrics.argument_count == 2
    assert metrics.evidence_count == 2
    assert metrics.average_confidence > 0
    assert metrics.round_duration > 0
    assert metrics.consensus_score > 0
    
    # Calculate overall metrics
    overall = debate.calculate_overall_metrics()
    assert overall["total_rounds"] == 1
    assert overall["total_arguments"] == 2
    assert overall["total_evidence"] == 2
    assert overall["average_consensus"] > 0

@pytest.mark.asyncio
async def test_consensus_calculation(debate: StrategyDebate):
    """Test consensus score calculation."""
    # Test full consensus
    score = debate._calculate_consensus_score(
        analysis={
            "response_points": [
                {"addresses": "concern1"},
                {"addresses": "concern2"}
            ]
        },
        challenge={
            "concerns": [
                {"id": "concern1"},
                {"id": "concern2"}
            ]
        }
    )
    assert score == 1.0
    
    # Test partial consensus
    score = debate._calculate_consensus_score(
        analysis={
            "response_points": [
                {"addresses": "concern1"}
            ]
        },
        challenge={
            "concerns": [
                {"id": "concern1"},
                {"id": "concern2"}
            ]
        }
    )
    assert score == 0.5

@pytest.mark.asyncio
async def test_max_rounds_limit(debate: StrategyDebate):
    """Test maximum rounds enforcement."""
    # Start max_rounds number of rounds
    for i in range(debate.max_rounds):
        round = await debate.start_round()
        await debate.end_round()
    
    # Attempting to start another round should fail
    with pytest.raises(ValueError):
        await debate.start_round()

@pytest.mark.asyncio
async def test_event_emission(
    debate: StrategyDebate,
    event_emitter: EventEmitter
):
    """Test event emission during debate."""
    events: List[Event] = []
    async def track_events(event: Event):
        events.append(event)
    
    # Register event tracker
    for event_type in EventType:
        event_emitter.add_handler(event_type, track_events)
    
    # Conduct debate activities
    await debate.start_round()
    await debate.add_argument(
        agent_id="test_agent",
        argument_type="analysis",
        content={"test": "content"},
        evidence=[]
    )
    await debate.end_round()
    
    # Verify events
    round_events = [e for e in events if e.event_type == EventType.ROUND_COMPLETED]
    argument_events = [e for e in events if e.event_type == EventType.ARGUMENT_SUBMITTED]
    
    assert len(round_events) == 2  # start and end events
    assert len(argument_events) == 1

@pytest.mark.asyncio
async def test_error_handling(debate: StrategyDebate):
    """Test error handling in debate."""
    # Test ending round without starting
    with pytest.raises(ValueError):
        await debate.end_round()
    
    # Test adding argument without active round
    with pytest.raises(ValueError):
        await debate.add_argument(
            agent_id="test",
            argument_type="analysis",
            content={},
            evidence=[]
        )
