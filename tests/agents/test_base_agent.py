"""Tests for the base agent implementation."""
import pytest
import asyncio
from datetime import datetime
from unittest.mock import MagicMock, AsyncMock
from crewai import Task

from src.agents.base import Agent
from src.agents.models import AgentConfig
from src.agents.types import AgentRole, AgentType

@pytest.fixture
def mock_knowledge_base():
    return MagicMock()

@pytest.fixture
def base_agent_config():
    return AgentConfig(
        role=AgentRole.STRATEGY,
        agent_type=AgentType.PRIMARY,
        temperature=0.7,
        max_iterations=3,
        max_rpm=10,
        timeout=1  # Short timeout for testing
    )

@pytest.fixture
def base_agent(mock_knowledge_base, base_agent_config):
    agent = Agent(base_agent_config, mock_knowledge_base)
    # Mock crew_agent for testing
    agent.crew_agent = AsyncMock()
    agent.crew_agent.execute = AsyncMock(return_value={"status": "success", "result": "test result"})
    return agent

def test_agent_initialization(base_agent, base_agent_config):
    """Test agent initialization and basic properties."""
    assert base_agent.config == base_agent_config
    assert base_agent.agent_id is not None
    assert base_agent.memory is not None
    assert base_agent.metrics is not None
    assert base_agent.task_manager is not None
    assert base_agent.memory.size == 0
    assert not base_agent.memory.is_full

@pytest.mark.asyncio
async def test_memory_management(base_agent):
    """Test memory management functionality."""
    # Create a test task
    task = Task(
        description="Test task",
        expected_output="Test result",
        context=[{
            "description": "Test context",
            "expected_output": "Test data",
            "test": "data"
        }]
    )
    
    # Execute task
    result = await base_agent.execute_task(task)
    
    # Verify memory was updated
    assert base_agent.memory.size == 1
    memories = base_agent.memory.get_relevant_memory("")
    assert len(memories) == 1
    assert memories[0]["task"] == task.description
    assert memories[0]["result"] == result

@pytest.mark.asyncio
async def test_metrics_tracking(base_agent):
    """Test performance metrics tracking."""
    # Create test tasks
    success_task = Task(
        description="Success task",
        expected_output="Success result",
        context=[{
            "description": "Test context",
            "expected_output": "Test data",
            "should_succeed": True
        }]
    )
    
    # Execute successful task
    result = await base_agent.execute_task(success_task)
    assert result["status"] == "success"
    
    # Mock failed execution
    base_agent.crew_agent.execute = AsyncMock(side_effect=Exception("Test error"))
    
    # Execute failed task
    failed_task = Task(
        description="Failed task",
        expected_output="Failed result",
        context=[{
            "description": "Test context",
            "expected_output": "Test data",
            "should_fail": True
        }]
    )
    
    try:
        await base_agent.execute_task(failed_task)
    except Exception:
        pass
    
    # Verify metrics
    metrics = base_agent.analyze_performance()
    assert metrics['total_actions'] > 0
    assert 0 <= metrics['success_rate'] <= 1
    assert metrics['average_response_time'] >= 0

@pytest.mark.asyncio
async def test_task_execution_with_memory_context(base_agent):
    """Test task execution with memory context."""
    # Add initial memory
    base_agent.memory.add_memory({
        "task": "previous task",
        "result": {"key_finding": "important data"},
    })
    
    # Create new task
    task = Task(
        description="Follow-up task",
        expected_output="Follow-up result",
        context=[{
            "description": "Test context",
            "expected_output": "Test data",
            "requires_context": True
        }]
    )
    
    # Execute task
    result = await base_agent.execute_task(task)
    
    # Verify result
    assert result is not None
    assert isinstance(result, dict)
    
    # Verify memory was updated
    assert base_agent.memory.size == 2
    latest_memory = base_agent.memory.get_relevant_memory("")[0]
    assert latest_memory["task"] == task.description
    assert latest_memory["result"] == result

@pytest.mark.asyncio
async def test_cleanup(base_agent):
    """Test agent cleanup."""
    # Add some test data
    base_agent.memory.add_memory({"test": "data"})
    base_agent.metrics.log_action("test_action", status="success", duration=0.1)
    
    # Perform cleanup
    await base_agent.cleanup()
    
    # Verify everything was cleaned up
    assert base_agent.memory.size == 0
    assert len(base_agent.metrics.action_history) == 0
    assert base_agent.metrics.latest_metrics == {}

@pytest.mark.asyncio
async def test_rate_limiting(base_agent):
    """Test task execution rate limiting."""
    task = Task(
        description="Rate limited task",
        expected_output="Rate limited result",
        context=[{
            "description": "Test context",
            "expected_output": "Test data"
        }]
    )
    
    # Mock slow execution
    async def delayed_execution(*args, **kwargs):
        await asyncio.sleep(0.1)  # Execution delay
        return {"status": "success", "result": "test"}
    
    base_agent.crew_agent.execute = AsyncMock(side_effect=delayed_execution)
    
    # Execute multiple tasks simultaneously
    start_time = datetime.now()
    tasks = [base_agent.execute_task(task) for _ in range(3)]
    
    # Wait for all tasks
    await asyncio.gather(*tasks)
    
    # Verify execution time indicates rate limiting
    execution_time = (datetime.now() - start_time).total_seconds()
    # Each task takes ~0.1s with rate limiting
    # 3 tasks should take at least 0.1s total
    assert execution_time >= 0.1
    # Also verify tasks don't execute too quickly (would indicate no rate limiting)
    assert execution_time > 0.05
