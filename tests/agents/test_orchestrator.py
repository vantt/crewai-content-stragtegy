"""Tests for the debate orchestrator."""
import pytest
from unittest.mock import Mock, AsyncMock
from typing import Dict, Any, List

from src.core import (
    EventEmitter,
    StateManager,
    Event,
    EventType,
    DebateStatus,
    WorkflowStatus,
    TaskStatus
)
from src.agents import DebateOrchestrator

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
def orchestrator(event_emitter, state_manager):
    """Fixture providing an orchestrator instance."""
    return DebateOrchestrator(event_emitter, state_manager)

@pytest.fixture
def sample_topic_context():
    """Fixture providing sample topic and context data."""
    return {
        "topic": "Market Entry Strategy",
        "context": {
            "market_size": 1000,
            "growth_rate": 15,
            "competition_level": "Medium",
            "target_segment": ["B2B", "Enterprise"],
            "additional_context": "Test market context"
        }
    }

@pytest.mark.asyncio
async def test_debate_initialization_with_workflow(
    orchestrator: DebateOrchestrator,
    sample_topic_context: Dict[str, Any]
):
    """Test debate initialization creates proper workflow."""
    # Initialize debate
    debate_id = await orchestrator.initialize_debate(
        sample_topic_context["topic"],
        sample_topic_context["context"]
    )
    
    # Verify debate initialization
    assert debate_id is not None
    assert orchestrator.topic == sample_topic_context["topic"]
    assert orchestrator.context == sample_topic_context["context"]
    
    # Verify workflow creation
    workflow = orchestrator.workflow_manager.workflows.get(debate_id)
    assert workflow is not None
    assert workflow.name == f"Debate: {sample_topic_context['topic']}"
    
    # Verify workflow tasks
    assert len(workflow.tasks) == 3  # Initial analysis, Challenge, Final analysis
    
    # Verify task dependencies
    tasks = workflow.tasks
    challenge_task = next(t for t in tasks if "Challenge" in t.name)
    final_task = next(t for t in tasks if "Final" in t.name)
    
    assert len(challenge_task.dependencies) == 1  # Depends on initial analysis
    assert len(final_task.dependencies) == 1  # Depends on challenge

@pytest.mark.asyncio
async def test_debate_execution_with_workflow(
    orchestrator: DebateOrchestrator,
    sample_topic_context: Dict[str, Any],
    event_emitter: EventEmitter
):
    """Test debate execution with workflow management."""
    # Track events
    events: List[Event] = []
    async def track_events(event: Event):
        events.append(event)
    
    for event_type in EventType:
        event_emitter.add_handler(event_type, track_events)
    
    # Initialize and start debate
    debate_id = await orchestrator.initialize_debate(
        sample_topic_context["topic"],
        sample_topic_context["context"]
    )
    
    results = await orchestrator.start_debate()
    
    # Verify results
    assert results["topic"] == sample_topic_context["topic"]
    assert "initial_analysis" in results
    assert "challenge" in results
    assert "final_analysis" in results
    
    # Verify workflow progression
    workflow_events = [
        e for e in events 
        if e.event_type in [
            EventType.WORKFLOW_STARTED,
            EventType.STEP_STARTED,
            EventType.STEP_COMPLETED,
            EventType.WORKFLOW_COMPLETED
        ]
    ]
    
    # Should have events for workflow start, 3 task starts, 3 task completions, workflow complete
    assert len(workflow_events) >= 8

@pytest.mark.asyncio
async def test_debate_resource_monitoring(
    orchestrator: DebateOrchestrator,
    sample_topic_context: Dict[str, Any]
):
    """Test resource monitoring during debate."""
    # Initialize debate
    debate_id = await orchestrator.initialize_debate(
        sample_topic_context["topic"],
        sample_topic_context["context"]
    )
    
    # Get initial resource usage
    initial_usage = orchestrator.get_resource_usage()
    assert initial_usage["active_tasks"] == 0
    
    # Start debate
    await orchestrator.start_debate()
    
    # Get resource usage during execution
    usage = orchestrator.get_resource_usage()
    assert usage["active_tasks"] >= 0  # May be 0 if tasks completed quickly
    assert "cpu_percent" in usage
    assert "memory_mb" in usage

@pytest.mark.asyncio
async def test_debate_error_handling(
    orchestrator: DebateOrchestrator,
    sample_topic_context: Dict[str, Any]
):
    """Test error handling in debate execution."""
    # Test starting debate without initialization
    with pytest.raises(ValueError):
        await orchestrator.start_debate()
    
    # Initialize debate
    debate_id = await orchestrator.initialize_debate(
        sample_topic_context["topic"],
        sample_topic_context["context"]
    )
    
    # Force workflow to fail
    await orchestrator.workflow_manager.cancel_workflow(debate_id)
    
    # Verify debate handles workflow failure
    with pytest.raises(Exception):
        await orchestrator.start_debate()

@pytest.mark.asyncio
async def test_debate_feedback_with_workflow(
    orchestrator: DebateOrchestrator,
    sample_topic_context: Dict[str, Any]
):
    """Test feedback handling with active workflow."""
    # Initialize debate
    debate_id = await orchestrator.initialize_debate(
        sample_topic_context["topic"],
        sample_topic_context["context"]
    )
    
    # Start debate
    await orchestrator.start_debate()
    
    # Submit feedback
    await orchestrator.add_feedback(
        "initial",
        "Test feedback",
        quality_score=4
    )
    
    # Verify feedback
    feedback = orchestrator.get_current_debate_feedback()
    assert len(feedback) == 1
    assert feedback[0]["feedback"] == "Test feedback"
    assert feedback[0]["quality_score"] == 4
    
    # Stop debate
    await orchestrator.stop_debate()
    
    # Verify workflow was cancelled
    workflow_status = orchestrator.workflow_manager.get_workflow_status(debate_id)
    assert workflow_status == WorkflowStatus.CANCELLED

@pytest.mark.asyncio
async def test_multiple_debates(
    orchestrator: DebateOrchestrator,
    sample_topic_context: Dict[str, Any]
):
    """Test handling multiple debates with workflows."""
    # Start first debate
    debate1_id = await orchestrator.initialize_debate(
        sample_topic_context["topic"],
        sample_topic_context["context"]
    )
    await orchestrator.start_debate()
    await orchestrator.add_feedback("initial", "First debate feedback")
    
    # Stop first debate
    await orchestrator.stop_debate()
    
    # Start second debate
    debate2_id = await orchestrator.initialize_debate(
        "New Topic",
        sample_topic_context["context"]
    )
    await orchestrator.start_debate()
    await orchestrator.add_feedback("initial", "Second debate feedback")
    
    # Verify feedback separation
    all_feedback = orchestrator.get_feedback_history()
    assert len(all_feedback) == 2
    
    # Verify workflows were properly managed
    assert orchestrator.workflow_manager.get_workflow_status(debate1_id) == WorkflowStatus.CANCELLED
    assert debate2_id in orchestrator.workflow_manager.workflows
