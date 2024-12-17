"""Tests for agent memory management functionality."""
import pytest
from datetime import datetime, timedelta
from src.agents.memory import AgentMemory
from src.agents.models import MemoryConfig

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
def memory(memory_config):
    """Test memory instance."""
    return AgentMemory(config=memory_config)

def test_memory_initialization(memory, memory_config):
    """Test memory initialization."""
    assert memory.size == 0
    assert not memory.is_full
    assert memory.utilization == 0.0
    assert memory.config == memory_config

def test_add_memory(memory):
    """Test adding items to memory."""
    memory.add_memory({"content": "test1"})
    memory.add_memory({"content": "test2"})
    
    assert memory.size == 2
    assert not memory.is_full
    assert memory.utilization == 0.4  # 2/5
    
    memories = memory.get_relevant_memory("test")
    assert len(memories) == 2
    assert memories[0]["content"] == "test2"  # Most recent first
    assert memories[1]["content"] == "test1"

def test_memory_size_limit(memory):
    """Test memory size limitation."""
    # Add more items than memory_size
    for i in range(6):
        memory.add_memory({"content": f"test{i}"})
    
    assert memory.size == 5  # Limited by memory_size
    assert memory.is_full
    assert memory.utilization == 1.0
    
    # Verify we kept most recent items
    memories = memory.get_relevant_memory("test")
    contents = [m["content"] for m in memories]
    assert contents == ["test5", "test4", "test3", "test2", "test1"]

def test_memory_ttl(memory):
    """Test memory time-to-live functionality."""
    # Add an expired memory
    old_time = datetime.now() - timedelta(seconds=memory.config.ttl_seconds + 1)
    memory.add_memory({
        "content": "expired",
        "timestamp": old_time,
        "ttl": old_time.timestamp() + memory.config.ttl_seconds
    })
    
    # Add a current memory
    memory.add_memory({"content": "current"})
    
    # Get memories - expired one should be filtered
    memories = memory.get_relevant_memory("test")
    assert len(memories) == 1
    assert memories[0]["content"] == "current"

def test_memory_context_length(memory):
    """Test memory context length limitation."""
    # Add memories with known lengths
    long_content = "x" * 600  # Each memory dict adds some overhead
    memory.add_memory({"content": long_content})
    memory.add_memory({"content": long_content})
    
    # Get memories - should be limited by max_context_length
    memories = memory.get_relevant_memory("test")
    assert len(memories) == 1  # Only one fits within max_context_length

def test_clear_memory(memory):
    """Test clearing memory."""
    memory.add_memory({"content": "test1"})
    memory.add_memory({"content": "test2"})
    assert memory.size == 2
    
    memory.clear()
    assert memory.size == 0
    assert not memory.is_full
    assert memory.utilization == 0.0

def test_memory_timestamp(memory):
    """Test memory timestamp handling."""
    # Add memory with timestamp
    custom_time = datetime.now() - timedelta(hours=1)
    memory.add_memory({
        "content": "test1",
        "timestamp": custom_time
    })
    
    # Add memory without timestamp
    memory.add_memory({"content": "test2"})
    
    memories = memory.get_relevant_memory("test")
    assert len(memories) == 2
    assert memories[0]["content"] == "test2"  # Most recent first
    assert memories[1]["content"] == "test1"  # Older memory second
    assert memories[1]["timestamp"] == custom_time

def test_relevance_scoring(memory):
    """Test memory relevance scoring."""
    # Add memories with different ages
    old_time = datetime.now() - timedelta(seconds=memory.config.ttl_seconds // 2)
    memory.add_memory({
        "content": "old content",
        "timestamp": old_time
    })
    memory.add_memory({
        "content": "new content"
    })
    
    # Get memories - should be ordered by relevance (recency)
    memories = memory.get_relevant_memory("test")
    assert len(memories) == 2
    assert memories[0]["content"] == "new content"
    assert memories[1]["content"] == "old content"

def test_memory_config_defaults():
    """Test memory configuration defaults."""
    memory = AgentMemory()  # No config provided
    assert memory.config.memory_size == 100
    assert memory.config.relevance_threshold == 0.5
    assert memory.config.max_context_length == 2000
    assert memory.config.ttl_seconds == 3600
