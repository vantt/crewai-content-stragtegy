"""Tests for agent memory management."""
import pytest
from datetime import datetime, timedelta
from src.agents.memory import AgentMemory

@pytest.fixture
def memory():
    return AgentMemory(memory_size=3)

def test_memory_initialization(memory):
    """Test memory initialization."""
    assert memory.size == 0
    assert not memory.is_full
    assert memory.memory_size == 3
    assert memory.utilization == 0.0

def test_add_memory(memory):
    """Test adding items to memory."""
    memory.add_memory({"action": "test1"})
    assert memory.size == 1
    assert not memory.is_full
    assert memory.utilization == 1/3

def test_memory_size_limit(memory):
    """Test memory size limit enforcement."""
    # Add more items than memory size
    for i in range(5):
        memory.add_memory({"action": f"test{i}"})
    
    assert memory.size == 3  # Should maintain max size
    assert memory.is_full
    assert memory.utilization == 1.0
    
    # Check that only most recent items are kept
    memories = memory.get_relevant_memory("")
    actions = [m["action"] for m in memories]
    assert actions == ["test4", "test3", "test2"]

def test_get_relevant_memory(memory):
    """Test memory retrieval."""
    # Add test memories with different timestamps
    now = datetime.now()
    
    memory.add_memory({
        "action": "test1",
        "timestamp": now - timedelta(minutes=2)
    })
    memory.add_memory({
        "action": "test2",
        "timestamp": now - timedelta(minutes=1)
    })
    memory.add_memory({
        "action": "test3",
        "timestamp": now
    })
    
    # Get memories and verify chronological order
    memories = memory.get_relevant_memory("test context")
    actions = [m["action"] for m in memories]
    assert actions == ["test3", "test2", "test1"]

def test_clear_memory(memory):
    """Test memory clearing."""
    # Add some memories
    memory.add_memory({"action": "test1"})
    memory.add_memory({"action": "test2"})
    
    assert memory.size == 2
    
    # Clear memory
    memory.clear()
    
    assert memory.size == 0
    assert not memory.is_full
    assert memory.utilization == 0.0
    assert memory.get_relevant_memory("") == []

def test_memory_timestamp_addition(memory):
    """Test timestamp is added to memories."""
    memory.add_memory({"action": "test"})
    memories = memory.get_relevant_memory("")
    
    assert len(memories) == 1
    assert "timestamp" in memories[0]
    assert isinstance(memories[0]["timestamp"], datetime)

def test_zero_memory_size():
    """Test handling of zero memory size."""
    memory = AgentMemory(memory_size=0)
    
    # Should handle zero size gracefully
    memory.add_memory({"action": "test"})
    assert memory.size == 0
    assert memory.is_full
    assert memory.utilization == 0.0
