"""Tests for task execution and management."""
import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, AsyncMock
from crewai import Task

from src.agents.task import TaskManager, TaskExecutionError

@pytest.fixture
def task_manager():
    return TaskManager(max_rpm=10)

@pytest.fixture
def mock_task():
    return Task(
        description="Test task",
        expected_output="A test result with status",
        context=[{
            "description": "Test context",
            "expected_output": "Test data",
            "test": "data"
        }]
    )

@pytest.fixture
def mock_crew_agent():
    agent = Mock()
    agent.execute = AsyncMock()
    return agent

@pytest.mark.asyncio
async def test_task_manager_initialization(task_manager):
    """Test task manager initialization."""
    assert task_manager.current_task is None
    assert task_manager._rate_limiter._value == 10

@pytest.mark.asyncio
async def test_successful_task_execution(task_manager, mock_task, mock_crew_agent):
    """Test successful task execution."""
    # Setup mock return value
    mock_crew_agent.execute.return_value = {"status": "success", "result": "test result"}
    
    # Execute task
    result = await task_manager.execute_task(mock_task, mock_crew_agent)
    
    # Verify task execution
    assert result["task"] == mock_task.description
    assert result["result"] == {"status": "success", "result": "test result"}
    assert result["status"] == "success"
    assert isinstance(result["start_time"], datetime)
    assert isinstance(result["end_time"], datetime)
    
    # Verify mock was called correctly
    mock_crew_agent.execute.assert_called_once_with(mock_task)

@pytest.mark.asyncio
async def test_failed_task_execution(task_manager, mock_task, mock_crew_agent):
    """Test handling of failed task execution."""
    # Setup mock to raise exception
    mock_crew_agent.execute.side_effect = Exception("Test error")
    
    # Execute task and verify exception
    with pytest.raises(TaskExecutionError) as exc_info:
        await task_manager.execute_task(mock_task, mock_crew_agent)
    
    # Verify error details
    error_result = exc_info.value.error_result
    assert error_result["task"] == mock_task.description
    assert error_result["error"] == "Test error"
    assert error_result["status"] == "failed"
    assert isinstance(error_result["start_time"], datetime)
    assert isinstance(error_result["end_time"], datetime)

@pytest.mark.asyncio
async def test_current_task_tracking(task_manager, mock_task, mock_crew_agent):
    """Test current task tracking."""
    # Setup mock to delay execution
    async def delayed_execution(*args):
        await asyncio.sleep(0.1)
        return {"status": "success", "result": "test result"}
    
    mock_crew_agent.execute.side_effect = delayed_execution
    
    # Start task execution
    task_future = asyncio.create_task(
        task_manager.execute_task(mock_task, mock_crew_agent)
    )
    
    # Allow task to start
    await asyncio.sleep(0.05)
    
    # Verify current task is set
    assert task_manager.current_task == mock_task.description
    
    # Wait for task completion
    await task_future
    
    # Verify current task is cleared
    assert task_manager.current_task is None

@pytest.mark.asyncio
async def test_rate_limiting(task_manager, mock_task, mock_crew_agent):
    """Test task execution rate limiting."""
    # Setup mock with delay
    async def delayed_execution(*args):
        await asyncio.sleep(0.1)
        return {"status": "success", "result": "test result"}
    
    mock_crew_agent.execute.side_effect = delayed_execution
    
    # Execute multiple tasks simultaneously
    start_time = datetime.now()
    tasks = [
        task_manager.execute_task(mock_task, mock_crew_agent)
        for _ in range(3)
    ]
    
    # Wait for all tasks
    await asyncio.gather(*tasks)
    
    # Verify execution time indicates rate limiting
    execution_time = (datetime.now() - start_time).total_seconds()
    # Each task takes ~0.25s with rate limiting and execution
    # 3 tasks should take at least 0.25s total
    assert execution_time >= 0.25
    # Also verify tasks don't execute too quickly (would indicate no rate limiting)
    assert execution_time > 0.2

def test_cleanup(task_manager):
    """Test task manager cleanup."""
    task_manager.cleanup()
    # Verify executor is shut down
    assert task_manager._executor._shutdown
