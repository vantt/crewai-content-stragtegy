"""Integration tests for agent component interactions."""
import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, patch
from crewai import Task

from src.agents.core import BaseAgent
from src.agents.models import AgentConfig, MemoryConfig, MetricsConfig, TaskConfig
from src.agents.types import AgentRole, AgentType

@pytest.fixture
def mock_knowledge_base():
    """Mock knowledge base."""
    return Mock()

@pytest.fixture
def agent_config():
    """Test agent configuration."""
    return AgentConfig(
        role=AgentRole.STRATEGY,
        agent_type=AgentType.PRIMARY,
        temperature=0.7,
        max_iterations=3,
        max_rpm=10,
        timeout=120,
        context_window=4000,
        memory_size=5
    )

@pytest.fixture
def memory_config():
    """Test memory configuration."""
    return MemoryConfig(
        memory_size=5,
        relevance_threshold=0.5,
        max_context_length=1000,
        ttl_seconds=3600
    )

@pytest.fixture
def metrics_config():
    """Test metrics configuration."""
    return MetricsConfig(
        enabled=True,
        history_size=5,
        aggregation_interval=60,
        performance_threshold=0.8
    )

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

class MockCrewAgent:
    """Mock CrewAI agent that allows setting execute method."""
    def __init__(self, role, goal, backstory, allow_delegation=False, verbose=True):
        self.role = role
        self.goal = goal
        self.backstory = backstory
        self.allow_delegation = allow_delegation
        self.verbose = verbose
        self._execute = None
    
    async def execute(self, task):
        if self._execute:
            return await self._execute(task)
        return {"result": "Success"}
    
    def set_execute(self, func):
        self._execute = func

@pytest.fixture
def test_agent(agent_config, memory_config, metrics_config, task_config, mock_knowledge_base):
    """Create test agent with all components configured."""
    with patch('src.agents.core.Agent', MockCrewAgent):
        agent = BaseAgent(agent_config, mock_knowledge_base)
        agent.memory.config = memory_config
        agent.metrics.config = metrics_config
        agent.task_manager.config = task_config
        return agent

@pytest.mark.asyncio
async def test_task_execution_with_memory_context(test_agent):
    """Test task execution using relevant memory context."""
    # Add some memories that should be relevant to the task
    test_agent.memory.add_memory({
        'content': 'Previous marketing strategy focused on social media',
        'context': 'strategy planning',
        'timestamp': datetime.now()
    })
    
    # Create a task
    task = Task(
        description="Develop new marketing strategy",
        expected_output="Marketing strategy document"
    )
    
    # Execute task
    result = await test_agent.execute_task(task)
    
    # Verify task execution was recorded in metrics
    assert test_agent.metrics.latest_metrics['total_actions'] == 1
    assert test_agent.metrics.latest_metrics['success_rate'] == 1.0
    
    # Verify new memory was created from result
    memories = test_agent.memory.get_relevant_memory("marketing strategy")
    assert any("Previous marketing strategy" in str(m.get('content')) for m in memories)

@pytest.mark.asyncio
async def test_performance_monitoring_integration(test_agent):
    """Test integration of performance monitoring across components."""
    task = Task(
        description="Test task",
        expected_output="Test output"
    )
    
    # Execute successful task
    result = await test_agent.execute_task(task)
    assert result['status'] == 'success'
    
    # Mock failed execution
    async def mock_failure(task):
        raise Exception("Test error")
    test_agent.crew_agent.set_execute(mock_failure)
    
    # Execute failed task
    with pytest.raises(Exception):
        await test_agent.execute_task(task)
    
    # Verify metrics were updated
    metrics = test_agent.metrics.analyze_performance()
    assert metrics['total_actions'] == 2
    assert metrics['success_rate'] == 0.5
    assert metrics['error_rate'] == 0.5
    assert 'warning' in metrics  # Should warn about performance threshold

@pytest.mark.asyncio
async def test_memory_metrics_interaction(test_agent):
    """Test interaction between memory management and metrics tracking."""
    # Add memories and verify metrics
    for i in range(3):
        test_agent.memory.add_memory({
            'content': f'Memory {i}',
            'timestamp': datetime.now()
        })
        test_agent.metrics.log_action(
            action_name="add_memory",
            status="success",
            memory_id=i
        )
    
    # Verify memory state
    assert test_agent.memory.size == 3
    assert test_agent.memory.utilization == 0.6  # 3/5
    
    # Verify metrics
    metrics = test_agent.metrics.analyze_performance()
    assert metrics['total_actions'] == 3
    assert metrics['success_rate'] == 1.0
    
    # Add memories beyond capacity
    for i in range(3):
        test_agent.memory.add_memory({
            'content': f'Overflow Memory {i}',
            'timestamp': datetime.now()
        })
    
    # Verify memory management
    assert test_agent.memory.size == 5  # Capped at memory_size
    assert test_agent.memory.is_full
    
    # Verify most recent memories were kept
    memories = test_agent.memory.get_relevant_memory("")
    assert all('Overflow Memory' in m['content'] for m in memories[:3])

@pytest.mark.asyncio
async def test_cleanup_integration(test_agent):
    """Test integrated cleanup across all components."""
    # Add data to all components
    test_agent.memory.add_memory({'content': 'test'})
    test_agent.metrics.log_action("test_action", status="success")
    
    task = Task(
        description="Test task",
        expected_output="Test output"
    )
    
    await test_agent.execute_task(task)
    
    # Verify data was added
    assert test_agent.memory.size > 0
    assert len(test_agent.metrics.action_history) > 0
    assert test_agent.task_manager.get_metrics()['total_executions'] > 0
    
    # Perform cleanup
    await test_agent.cleanup()
    
    # Verify all components were cleaned
    assert test_agent.memory.size == 0
    assert len(test_agent.metrics.action_history) == 0
    assert test_agent.task_manager.get_metrics()['total_executions'] == 0
    assert test_agent.state.action_history == []

@pytest.mark.asyncio
async def test_rate_limiting_integration(test_agent):
    """Test rate limiting integration across components."""
    task = Task(
        description="Rate limited task",
        expected_output="Test output"
    )
    
    # Execute tasks rapidly
    start_time = datetime.now()
    tasks = []
    for _ in range(3):
        tasks.append(test_agent.execute_task(task))
    
    # Wait for all tasks
    await asyncio.gather(*tasks)
    duration = (datetime.now() - start_time).total_seconds()
    
    # Verify rate limiting
    min_delay = 60 / test_agent.task_manager.config.max_rpm
    min_expected_duration = (len(tasks) - 1) * min_delay
    assert duration >= min_expected_duration * 0.5
    
    # Verify metrics captured rate-limited execution
    metrics = test_agent.metrics.analyze_performance()
    assert metrics['total_actions'] == 3
    assert metrics['success_rate'] == 1.0

@pytest.mark.asyncio
async def test_error_handling_integration(test_agent):
    """Test error handling integration across components."""
    task = Task(
        description="Error test task",
        expected_output="Test output"
    )
    
    # Mock an error
    async def mock_error(task):
        raise ValueError("Test error")
    test_agent.crew_agent.set_execute(mock_error)
    
    # Execute task and verify error handling
    with pytest.raises(Exception):
        await test_agent.execute_task(task)
    
    # Verify error was recorded in metrics
    metrics = test_agent.metrics.analyze_performance()
    assert metrics['error_rate'] > 0
    assert metrics['total_actions'] == 1
    
    # Verify error was added to agent state
    assert test_agent.state.error_count == 1
    assert len(test_agent.state.action_history) == 1
    assert test_agent.state.action_history[0]['status'] == 'failed'
