# tests/performance/test_agent_performance.py
import pytest
import asyncio
from src.agents.base import BaseAgent

async def test_agent_memory_performance(mock_knowledge_base):
    # Test memory management under load
    agent = BaseAgent(config, mock_knowledge_base)
    for i in range(1000):
        agent._update_memory({"test": f"data_{i}"})
    assert len(agent.state.memory) <= agent.config.memory_size