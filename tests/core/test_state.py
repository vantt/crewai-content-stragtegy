"""Tests for the state management system."""
import pytest
import asyncio
from typing import List

from src.core.events import EventEmitter, Event, EventType
from src.core.state import (
    StateManager,
    WorkflowStatus,
    DebateStatus,
    TaskStatus,
    StateTransitionError
)

@pytest.fixture
async def event_emitter():
    """Fixture providing an event emitter instance."""
    emitter = EventEmitter()
    async with emitter:
        yield emitter

@pytest.fixture
async def state_manager(event_emitter):
    """Fixture providing a state manager instance."""
    return StateManager(event_emitter)

@pytest.mark.asyncio
async def test_workflow_state_transitions(state_manager: StateManager):
    """Test workflow state transitions."""
    workflow_id = "test_workflow"
    
    # Initial state should be None
    assert state_manager.get_workflow_state(workflow_id) is None
    
    # Set initial state
    await state_manager.set_workflow_state(workflow_id, WorkflowStatus.PENDING)
    assert state_manager.get_workflow_state(workflow_id) == WorkflowStatus.PENDING
    
    # Valid transition
    await state_manager.set_workflow_state(workflow_id, WorkflowStatus.IN_PROGRESS)
    assert state_manager.get_workflow_state(workflow_id) == WorkflowStatus.IN_PROGRESS
    
    # Invalid transition should raise error
    with pytest.raises(StateTransitionError):
        await state_manager.set_workflow_state(workflow_id, WorkflowStatus.PENDING)

@pytest.mark.asyncio
async def test_debate_state_transitions(state_manager: StateManager):
    """Test debate state transitions."""
    debate_id = "test_debate"
    
    # Set initial state
    await state_manager.set_debate_state(debate_id, DebateStatus.PENDING)
    assert state_manager.get_debate_state(debate_id) == DebateStatus.PENDING
    
    # Valid transitions
    await state_manager.set_debate_state(debate_id, DebateStatus.IN_PROGRESS)
    assert state_manager.get_debate_state(debate_id) == DebateStatus.IN_PROGRESS
    
    await state_manager.set_debate_state(debate_id, DebateStatus.CONSENSUS_REACHED)
    assert state_manager.get_debate_state(debate_id) == DebateStatus.CONSENSUS_REACHED
    
    # Invalid transition
    with pytest.raises(StateTransitionError):
        await state_manager.set_debate_state(debate_id, DebateStatus.IN_PROGRESS)

@pytest.mark.asyncio
async def test_task_state_transitions(state_manager: StateManager):
    """Test task state transitions."""
    task_id = "test_task"
    
    # Set initial state
    await state_manager.set_task_state(task_id, TaskStatus.PENDING)
    assert state_manager.get_task_state(task_id) == TaskStatus.PENDING
    
    # Valid transitions
    await state_manager.set_task_state(task_id, TaskStatus.READY)
    assert state_manager.get_task_state(task_id) == TaskStatus.READY
    
    await state_manager.set_task_state(task_id, TaskStatus.IN_PROGRESS)
    assert state_manager.get_task_state(task_id) == TaskStatus.IN_PROGRESS
    
    # Invalid transition
    with pytest.raises(StateTransitionError):
        await state_manager.set_task_state(task_id, TaskStatus.PENDING)

@pytest.mark.asyncio
async def test_state_events(event_emitter: EventEmitter, state_manager: StateManager):
    """Test state change events are emitted correctly."""
    events_received: List[Event] = []
    
    async def test_handler(event: Event):
        events_received.append(event)
    
    # Register handler for all event types
    for event_type in EventType:
        event_emitter.add_handler(event_type, test_handler)
    
    # Test workflow events
    workflow_id = "test_workflow"
    await state_manager.set_workflow_state(workflow_id, WorkflowStatus.PENDING)
    await state_manager.set_workflow_state(workflow_id, WorkflowStatus.IN_PROGRESS)
    
    # Test debate events
    debate_id = "test_debate"
    await state_manager.set_debate_state(debate_id, DebateStatus.PENDING)
    await state_manager.set_debate_state(debate_id, DebateStatus.IN_PROGRESS)
    
    # Wait for event processing
    await asyncio.sleep(0.1)
    
    # Verify events were emitted
    workflow_events = [e for e in events_received if e.workflow_id == workflow_id]
    debate_events = [e for e in events_received if "debate_id" in e.data and e.data["debate_id"] == debate_id]
    
    assert len(workflow_events) > 0
    assert len(debate_events) > 0

@pytest.mark.asyncio
async def test_concurrent_state_changes(state_manager: StateManager):
    """Test concurrent state changes are handled correctly."""
    workflow_id = "test_workflow"
    
    async def change_state(new_state: WorkflowStatus):
        await state_manager.set_workflow_state(workflow_id, new_state)
    
    # Initialize state
    await state_manager.set_workflow_state(workflow_id, WorkflowStatus.PENDING)
    
    # Try concurrent state changes
    await asyncio.gather(
        change_state(WorkflowStatus.IN_PROGRESS),
        change_state(WorkflowStatus.IN_PROGRESS)
    )
    
    assert state_manager.get_workflow_state(workflow_id) == WorkflowStatus.IN_PROGRESS

@pytest.mark.asyncio
async def test_cleanup(state_manager: StateManager):
    """Test state cleanup."""
    entity_id = "test_entity"
    
    # Set some states
    await state_manager.set_workflow_state(entity_id, WorkflowStatus.PENDING)
    await state_manager.set_debate_state(entity_id, DebateStatus.PENDING)
    await state_manager.set_task_state(entity_id, TaskStatus.PENDING)
    
    # Cleanup
    state_manager.cleanup(entity_id)
    
    # Verify states are cleaned up
    assert state_manager.get_workflow_state(entity_id) is None
    assert state_manager.get_debate_state(entity_id) is None
    assert state_manager.get_task_state(entity_id) is None
