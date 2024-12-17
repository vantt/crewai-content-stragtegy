"""Tests for task execution and management functionality."""
import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, patch
from crewai import Task

from src.agents.task import TaskManager
from src.agents.models import TaskConfig
from src.agents.exceptions import TaskExecutionError

@pytest.fixture
def task_config():
    """Test task configuration."""
    return TaskConfig(
        max_rpm=10,
        timeout=120,
        retry_attempts=3,
        retry_delay=1.0,
        batch_size=5
    )

@pytest.fixture
def task_manager(task_config):
    """Test task manager instance."""
    return TaskManager(
        max_rpm=task_config.max_rpm,
        timeout=task_config.timeout
    )

@pytest.fixture
def mock_task():
    """Mock CrewAI task."""
    return Task(
        description="Test task",
        expected_output="Test output"
    )

@pytest.fixture
def mock_crew_agent():
    """Mock CrewAI agent."""
    agent = Mock()
    async def mock_execute(task):
        return {"result": "Success"}
    agent.execute = mock_execute
    return agent

@pytest.mark.asyncio
async def test_task_initialization(task_manager, task_config):
    """Test task manager initialization."""
    assert task_manager.config.max_rpm == task_config.max_rpm
    assert task_manager.config.timeout == task_config.timeout
    assert task_manager.current_task is None
    
    metrics = task_manager.get_metrics()
    assert metrics['total_executions'] == 0
    assert metrics['successful_executions'] == 0
    assert metrics['failed_executions'] == 0

@pytest.mark.asyncio
async def test_successful_task_execution(task_manager, mock_task, mock_crew_agent):
    """Test successful task execution."""
    result = await task_manager.execute_task(mock_task, mock_crew_agent)
    
    assert result['status'] == 'success'
    assert 'result' in result
    assert 'start_time' in result
    assert 'end_time' in result
    
    metrics = task_manager.get_metrics()
    assert metrics['total_executions'] == 1
    assert metrics['successful_executions'] == 1
    assert metrics['failed_executions'] == 0

@pytest.mark.asyncio
async def test_failed_task_execution(task_manager, mock_task):
    """Test failed task execution."""
    # Mock agent that raises an exception
    agent = Mock()
    async def mock_execute(task):
        raise Exception("Test error")
    agent.execute = mock_execute
    
    with pytest.raises(TaskExecutionError) as exc_info:
        await task_manager.execute_task(mock_task, agent)
    
    assert "Test error" in str(exc_info.value)
    metrics = task_manager.get_metrics()
    assert metrics['total_executions'] == 1
    assert metrics['successful_executions'] == 0
    assert metrics['failed_executions'] == 1

@pytest.mark.asyncio
async def test_rate_limiting(task_manager, mock_task, mock_crew_agent):
    """Test task rate limiting."""
    start_time = datetime.now()
    
    # Execute multiple tasks quickly
    tasks = []
    for _ in range(3):
        tasks.append(task_manager.execute_task(mock_task, mock_crew_agent))
    
    # Wait for all tasks to complete
    results = await asyncio.gather(*tasks)
    end_time = datetime.now()
    
    # Verify rate limiting added some delay
    duration = (end_time - start_time).total_seconds()
    # Each task should take at least 60/max_rpm seconds
    min_delay = 60 / task_manager.config.max_rpm  # 6 seconds for max_rpm=10
    min_expected_duration = (len(tasks) - 1) * min_delay  # 12 seconds for 3 tasks
    
    # Allow some flexibility in timing (50% of expected minimum)
    assert duration >= min_expected_duration * 0.5
    
    # Verify all tasks succeeded
    assert all(r['status'] == 'success' for r in results)
    
    metrics = task_manager.get_metrics()
    assert metrics['total_executions'] == 3
    assert metrics['successful_executions'] == 3

@pytest.mark.asyncio
async def test_current_task_tracking(task_manager, mock_task, mock_crew_agent):
    """Test current task tracking."""
    assert task_manager.current_task is None
    
    # Start task execution
    task_future = asyncio.create_task(
        task_manager.execute_task(mock_task, mock_crew_agent)
    )
    
    # Allow task to start
    await asyncio.sleep(0.1)
    
    # Verify current task is set
    assert task_manager.current_task == mock_task.description
    
    # Wait for task to complete
    await task_future
    
    # Verify current task is cleared
    assert task_manager.current_task is None

@pytest.mark.asyncio
async def test_cleanup(task_manager, mock_task, mock_crew_agent):
    """Test task manager cleanup."""
    await task_manager.execute_task(mock_task, mock_crew_agent)
    assert task_manager.get_metrics()['total_executions'] == 1
    
    task_manager.cleanup()
    metrics = task_manager.get_metrics()
    assert metrics['total_executions'] == 0
    assert metrics['successful_executions'] == 0
    assert metrics['failed_executions'] == 0

@pytest.mark.asyncio
async def test_metrics_recording(task_manager, mock_task, mock_crew_agent):
    """Test metrics recording."""
    await task_manager.execute_task(mock_task, mock_crew_agent)
    
    metrics = task_manager.get_metrics()
    assert metrics['total_executions'] == 1
    assert metrics['successful_executions'] == 1
    assert metrics['total_duration'] > 0
    assert 'last_updated' in metrics

@pytest.mark.asyncio
async def test_task_result_format(task_manager, mock_task, mock_crew_agent):
    """Test task result format."""
    result = await task_manager.execute_task(mock_task, mock_crew_agent)
    
    # Verify result structure
    assert isinstance(result, dict)
    assert 'task' in result
    assert 'result' in result
    assert 'start_time' in result
    assert 'end_time' in result
    assert 'status' in result
    
    # Verify timestamps
    assert isinstance(result['start_time'], datetime)
    assert isinstance(result['end_time'], datetime)
    assert result['end_time'] > result['start_time']
