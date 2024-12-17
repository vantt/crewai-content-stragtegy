"""Tests for core agent functionality."""
import pytest
from src.agents.core import BaseAgent
from src.agents.models import AgentConfig
from src.agents.types import AgentRole, AgentType

@pytest.fixture
def base_config():
    return AgentConfig(
        role=AgentRole.STRATEGY,
        agent_type=AgentType.PRIMARY
    )

@pytest.fixture
def mock_knowledge_base():
    # Mock knowledge base for testing
    return object()

def test_base_agent_initialization(base_config, mock_knowledge_base):
    """Test basic agent initialization."""
    agent = BaseAgent(base_config, mock_knowledge_base)
    
    assert agent.config == base_config
    assert agent.knowledge_base == mock_knowledge_base
    assert agent.agent_id is not None
    assert agent.name.startswith(f"{base_config.role.value}_{base_config.agent_type.value}")

def test_agent_goal_generation(base_config, mock_knowledge_base):
    """Test agent goal generation based on role and type."""
    agent = BaseAgent(base_config, mock_knowledge_base)
    goal = agent._get_agent_goal()
    
    assert isinstance(goal, str)
    assert len(goal) > 0
    assert "marketing strategies" in goal.lower()

def test_agent_backstory_generation(base_config, mock_knowledge_base):
    """Test agent backstory generation based on role and type."""
    agent = BaseAgent(base_config, mock_knowledge_base)
    backstory = agent._get_agent_backstory()
    
    assert isinstance(backstory, str)
    assert len(backstory) > 0
    assert "strategist" in backstory.lower()

def test_custom_name_assignment(base_config, mock_knowledge_base):
    """Test custom name assignment."""
    custom_name = "TestAgent"
    agent = BaseAgent(base_config, mock_knowledge_base, name=custom_name)
    
    assert agent.name == custom_name

def test_crew_agent_initialization(base_config, mock_knowledge_base):
    """Test CrewAI agent initialization."""
    agent = BaseAgent(base_config, mock_knowledge_base)
    
    assert agent.crew_agent is not None
    assert agent.crew_agent.role == base_config.role.value
    assert not agent.crew_agent.allow_delegation
