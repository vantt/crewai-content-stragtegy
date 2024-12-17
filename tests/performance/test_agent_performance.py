"""Performance tests for agent components."""
import pytest
from datetime import datetime
from unittest.mock import Mock

from src.agents.core import BaseAgent
from src.agents.models import AgentConfig
from src.agents.types import AgentRole, AgentType

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
        memory_size=500  # Match test size
    )

@pytest.mark.asyncio
async def test_agent_memory_performance(agent_config, mock_knowledge_base):
    """Test memory management under load."""
    agent = BaseAgent(agent_config, mock_knowledge_base)
    
    # Add many memories rapidly
    start_time = datetime.now()
    for i in range(500):
        agent.memory.add_memory({
            'content': f'Memory item {i}',
            'timestamp': datetime.now()
        })
    duration = (datetime.now() - start_time).total_seconds()
    
    # Verify performance
    assert duration < 1.0  # Should handle 500 items in under 1 second
    assert agent.memory.size == agent_config.memory_size
    
    # Test retrieval performance
    start_time = datetime.now()
    memories = agent.memory.get_relevant_memory("test")
    duration = (datetime.now() - start_time).total_seconds()
    
    # Verify retrieval performance
    assert duration < 0.1  # Should retrieve and sort in under 100ms
    assert len(memories) > 0
    
    # Test memory cleanup performance
    start_time = datetime.now()
    agent.memory.clear()
    duration = (datetime.now() - start_time).total_seconds()
    
    # Verify cleanup performance
    assert duration < 0.1  # Should cleanup in under 100ms
    assert agent.memory.size == 0
