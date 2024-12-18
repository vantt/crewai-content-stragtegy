"""Tests for the workflow management system."""
import pytest
import asyncio
from typing import List, Dict, Any
from datetime import datetime

from src.core.events import EventEmitter, Event, EventType
from src.core.state import StateManager, WorkflowStatus, TaskStatus
from src.core.workflow import (
    WorkflowManager,
    TaskDefinition,
    WorkflowDefinition,
    ResourceUsage
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
def workflow_manager(event_emitter, state_manager):
    """Fixture providing a workflow manager instance."""
    return WorkflowManager(event_emitter, state_manager)

@pytest.fixture
def sample_tasks():
    """Fixture providing sample task definitions."""
    return [
        TaskDefinition(
            name="Task 1",
            description="First task",
            agent_pair_id="pair1",
            estimated_duration=1,
            required_resources={"cpu": 1.0, "memory": 100}
        ),
        TaskDefinition(
            name="Task 2",
            description="Second task",
            agent_pair_id="pair1",
            dependencies=[],  # Will be set in tests
            estimated_duration=1,
            required_resources={"cpu": 1.0, "memory": 100}
        ),
        TaskDefinition(
            name="Task 3",
            description="Third task",
            agent_pair_id="pair2",
            dependencies=[],  # Will be set in tests
            estimated_duration=1,
            required_resources={"cpu": 1.0, "memory": 100}
        )
    ]

@pytest.mark.asyncio
async def test_workflow_creation(workflow_manager: WorkflowManager, sample_tasks: List[TaskDefinition]):
    """Test workflow creation."""
    # Create workflow
    workflow_id = await workflow_manager.create_workflow(
        name="Test Workflow",
        description="Test workflow description",
        tasks=sample_tasks
    )
    
    # Verify workflow was created
    assert workflow_id in workflow_manager.workflows
    workflow = workflow_manager.workflows[workflow_id]
    assert workflow.name == "Test Workflow"
    assert len(workflow.tasks) == len(sample_tasks)

@pytest.mark.asyncio
async def test_workflow_validation(workflow_manager: WorkflowManager, sample_tasks: List[TaskDefinition]):
    """Test workflow validation."""
    # Create workflow with valid dependencies
    tasks = sample_tasks.copy()
    tasks[1].dependencies = [tasks[0].task_id]
    tasks[2].dependencies = [tasks[1].task_id]
    
    workflow_id = await workflow_manager.create_workflow(
        name="Test Workflow",
        description="Test workflow description",
        tasks=tasks
    )
    
    # Validation should pass
    assert await workflow_manager.validate_workflow(workflow_id)
    
    # Test invalid dependencies
    tasks = sample_tasks.copy()
    tasks[0].dependencies = ["non_existent_task"]
    
    workflow_id = await workflow_manager.create_workflow(
        name="Invalid Workflow",
        description="Workflow with invalid dependencies",
        tasks=tasks
    )
    
    # Validation should fail
    with pytest.raises(ValueError):
        await workflow_manager.validate_workflow(workflow_id)

@pytest.mark.asyncio
async def test_workflow_execution(
    workflow_manager: WorkflowManager,
    sample_tasks: List[TaskDefinition],
    event_emitter: EventEmitter
):
    """Test workflow execution."""
    # Track events
    events: List[Event] = []
    async def track_events(event: Event):
        events.append(event)
    
    for event_type in EventType:
        event_emitter.add_handler(event_type, track_events)
    
    # Create workflow with sequential tasks
    tasks = sample_tasks.copy()
    tasks[1].dependencies = [tasks[0].task_id]
    tasks[2].dependencies = [tasks[1].task_id]
    
    workflow_id = await workflow_manager.create_workflow(
        name="Sequential Workflow",
        description="Workflow with sequential tasks",
        tasks=tasks
    )
    
    # Start workflow
    await workflow_manager.start_workflow(workflow_id)
    
    # Wait for completion (3 tasks * 1 second each)
    await asyncio.sleep(4)
    
    # Verify workflow completed
    status = workflow_manager.get_workflow_status(workflow_id)
    assert status == WorkflowStatus.COMPLETED
    
    # Verify events
    start_events = [e for e in events if e.event_type == EventType.STEP_STARTED]
    complete_events = [e for e in events if e.event_type == EventType.STEP_COMPLETED]
    
    assert len(start_events) == 3
    assert len(complete_events) == 3
    
    # Verify execution order
    task_order = [e.step_id for e in start_events]
    assert task_order.index(tasks[0].task_id) < task_order.index(tasks[1].task_id)
    assert task_order.index(tasks[1].task_id) < task_order.index(tasks[2].task_id)

@pytest.mark.asyncio
async def test_concurrent_workflows(
    workflow_manager: WorkflowManager,
    sample_tasks: List[TaskDefinition]
):
    """Test concurrent workflow execution."""
    # Create multiple workflows
    workflow_ids = []
    for i in range(workflow_manager.max_concurrent_workflows + 1):
        workflow_id = await workflow_manager.create_workflow(
            name=f"Workflow {i}",
            description=f"Test workflow {i}",
            tasks=sample_tasks
        )
        workflow_ids.append(workflow_id)
    
    # Start workflows up to limit
    for i in range(workflow_manager.max_concurrent_workflows):
        await workflow_manager.start_workflow(workflow_ids[i])
    
    # Attempting to start another should fail
    with pytest.raises(RuntimeError):
        await workflow_manager.start_workflow(workflow_ids[-1])

@pytest.mark.asyncio
async def test_workflow_control(
    workflow_manager: WorkflowManager,
    sample_tasks: List[TaskDefinition]
):
    """Test workflow control operations."""
    workflow_id = await workflow_manager.create_workflow(
        name="Test Workflow",
        description="Test workflow description",
        tasks=sample_tasks
    )
    
    # Start workflow
    await workflow_manager.start_workflow(workflow_id)
    assert workflow_manager.get_workflow_status(workflow_id) == WorkflowStatus.IN_PROGRESS
    
    # Pause workflow
    await workflow_manager.pause_workflow(workflow_id)
    assert workflow_manager.get_workflow_status(workflow_id) == WorkflowStatus.PAUSED
    
    # Resume workflow
    await workflow_manager.resume_workflow(workflow_id)
    assert workflow_manager.get_workflow_status(workflow_id) == WorkflowStatus.IN_PROGRESS
    
    # Cancel workflow
    await workflow_manager.cancel_workflow(workflow_id)
    assert workflow_manager.get_workflow_status(workflow_id) == WorkflowStatus.CANCELLED

@pytest.mark.asyncio
async def test_resource_tracking(
    workflow_manager: WorkflowManager,
    sample_tasks: List[TaskDefinition]
):
    """Test resource usage tracking."""
    workflow_id = await workflow_manager.create_workflow(
        name="Test Workflow",
        description="Test workflow description",
        tasks=sample_tasks
    )
    
    # Check initial resource usage
    usage = workflow_manager.get_resource_usage()
    assert usage.active_tasks == 0
    assert usage.queued_tasks == 0
    
    # Start workflow
    await workflow_manager.start_workflow(workflow_id)
    
    # Wait briefly for task to start
    await asyncio.sleep(0.1)
    
    # Check resource usage during execution
    usage = workflow_manager.get_resource_usage()
    assert usage.active_tasks > 0 or usage.queued_tasks > 0

@pytest.mark.asyncio
async def test_error_handling(
    workflow_manager: WorkflowManager,
    sample_tasks: List[TaskDefinition]
):
    """Test error handling."""
    # Test non-existent workflow
    with pytest.raises(ValueError):
        await workflow_manager.start_workflow("non_existent_workflow")
    
    # Test invalid state transitions
    workflow_id = await workflow_manager.create_workflow(
        name="Test Workflow",
        description="Test workflow description",
        tasks=sample_tasks
    )
    
    # Cannot pause non-running workflow
    with pytest.raises(ValueError):
        await workflow_manager.pause_workflow(workflow_id)
    
    # Cannot resume non-paused workflow
    with pytest.raises(ValueError):
        await workflow_manager.resume_workflow(workflow_id)
