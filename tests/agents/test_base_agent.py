"""Tests for core agent functionality."""
import pytest
from unittest.mock import Mock
from datetime import datetime

from src.agents.core import BaseAgent
from src.agents.models import AgentConfig
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
def base_agent(agent_config, mock_knowledge_base):
    """Test base agent instance."""
    return BaseAgent(
        config=agent_config,
        knowledge_base=mock_knowledge_base,
        name="test_agent"
    )

def test_agent_initialization(base_agent, agent_config, mock_knowledge_base):
    """Test agent initialization."""
    assert base_agent.name == "test_agent"
    assert base_agent.config == agent_config
    assert base_agent.knowledge_base == mock_knowledge_base
    assert base_agent.state is not None
    assert base_agent.memory is not None
    assert base_agent.metrics is not None
    assert base_agent.task_manager is not None
    assert base_agent.crew_agent is not None

def test_agent_id_generation(agent_config, mock_knowledge_base):
    """Test unique agent ID generation."""
    agent1 = BaseAgent(agent_config, mock_knowledge_base)
    agent2 = BaseAgent(agent_config, mock_knowledge_base)
    assert agent1.agent_id != agent2.agent_id

def test_default_agent_name(agent_config, mock_knowledge_base):
    """Test default agent name generation."""
    agent = BaseAgent(agent_config, mock_knowledge_base)
    expected_prefix = f"{agent_config.role.value}_{agent_config.agent_type.value}"
    assert agent.name.startswith(expected_prefix)
    assert len(agent.name.split('_')[2]) == 8  # UUID prefix length

def test_agent_goal_generation(base_agent):
    """Test agent goal generation."""
    # Test for each role
    for role in AgentRole:
        base_agent.config.role = role
        goal = base_agent._get_agent_goal()
        assert isinstance(goal, str)
        assert len(goal) > 0
        assert goal in BaseAgent.ROLE_GOALS.values()

def test_agent_backstory_generation(base_agent):
    """Test agent backstory generation."""
    # Test for each role and type combination
    for role in AgentRole:
        for agent_type in AgentType:
            base_agent.config.role = role
            base_agent.config.agent_type = agent_type
            backstory = base_agent._get_agent_backstory()
            assert isinstance(backstory, str)
            assert len(backstory) > 0
            
            # Verify role-specific content
            base_role_story = BaseAgent.ROLE_BACKSTORIES[role]
            assert base_role_story in backstory
            
            # Verify type-specific modifications
            if agent_type == AgentType.ADVERSARY:
                assert "identifying potential issues" in backstory
            elif agent_type == AgentType.ASSISTANT:
                assert "supporting and enhancing" in backstory

def test_record_action(base_agent):
    """Test action recording."""
    action = {
        'action': 'test_action',
        'timestamp': datetime.now(),
        'status': 'success'
    }
    base_agent.record_action(action)
    
    assert base_agent.state.last_action == 'test_action'
    assert base_agent.state.success_count == 1
    assert base_agent.state.error_count == 0

def test_analyze_performance(base_agent):
    """Test performance analysis."""
    # Record actions in metrics directly
    base_agent.metrics.log_action(
        action_name='action1',
        status='success',
        duration=1.0,
        start_time=datetime.now()
    )
    base_agent.metrics.log_action(
        action_name='action2',
        status='failed',
        duration=1.0,
        start_time=datetime.now()
    )
    
    performance = base_agent.analyze_performance()
    assert isinstance(performance, dict)
    assert performance['total_actions'] == 2
    assert performance['success_rate'] == 0.5
    assert performance['error_rate'] == 0.5

@pytest.mark.asyncio
async def test_cleanup(base_agent):
    """Test agent cleanup."""
    # Add some data to clean up
    base_agent.record_action({
        'action': 'test_action',
        'timestamp': datetime.now(),
        'status': 'success'
    })
    base_agent.memory.add_memory({'content': 'test'})
    base_agent.metrics.log_action('test_action', status='success')
    
    await base_agent.cleanup()
    
    assert base_agent.state.action_history == []
    assert base_agent.state.success_count == 0
    assert base_agent.memory.size == 0
    assert base_agent.metrics.latest_metrics['total_actions'] == 0

def test_crew_agent_initialization(base_agent):
    """Test CrewAI agent initialization."""
    crew_agent = base_agent.crew_agent
    assert crew_agent.role == base_agent.config.role.value
    assert crew_agent.goal == base_agent._get_agent_goal()
    assert crew_agent.backstory == base_agent._get_agent_backstory()
    assert crew_agent.allow_delegation is False
    assert crew_agent.verbose is True

def test_agent_configuration_validation(mock_knowledge_base):
    """Test agent configuration validation."""
    # Test with invalid temperature
    config = AgentConfig(
        role=AgentRole.STRATEGY,
        agent_type=AgentType.PRIMARY,
        temperature=2.0  # Invalid: should be between 0 and 1
    )
    with pytest.raises(ValueError):
        BaseAgent(config, mock_knowledge_base)
    
    # Test with invalid max_rpm
    config = AgentConfig(
        role=AgentRole.STRATEGY,
        agent_type=AgentType.PRIMARY,
        max_rpm=0  # Invalid: should be positive
    )
    with pytest.raises(ValueError):
        BaseAgent(config, mock_knowledge_base)
