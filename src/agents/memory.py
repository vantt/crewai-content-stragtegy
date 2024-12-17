"""Memory management functionality for agents."""
from typing import Dict, List, Any
from datetime import datetime

class AgentMemory:
    """Handles agent memory management and retrieval."""
    
    def __init__(self, memory_size: int = 10):
        self.memory_size = memory_size
        self._memory: List[Dict[str, Any]] = []
    
    def add_memory(self, item: Dict[str, Any]) -> None:
        """Add new item to memory with timestamp."""
        memory_item = {
            **item,
            'timestamp': item.get('timestamp', datetime.now())
        }
        
        # Add to front of list (most recent first)
        self._memory.insert(0, memory_item)
        
        # Maintain memory size limit by removing oldest items
        if len(self._memory) > self.memory_size:
            self._memory.pop()
    
    def get_relevant_memory(self, context: str) -> List[Dict[str, Any]]:
        """Retrieve relevant memories based on context.
        
        Args:
            context: The context to find relevant memories for
            
        Returns:
            List of relevant memory items, most recent first
        """
        # TODO: Implement similarity/relevance scoring
        # For now return all memories (already in chronological order, most recent first)
        return self._memory.copy()
    
    def clear(self) -> None:
        """Clear all memories."""
        self._memory.clear()
    
    @property
    def size(self) -> int:
        """Get current memory size."""
        return len(self._memory)
    
    @property
    def is_full(self) -> bool:
        """Check if memory is at capacity."""
        return len(self._memory) >= self.memory_size
    
    @property
    def utilization(self) -> float:
        """Get memory utilization percentage."""
        return self.size / self.memory_size if self.memory_size > 0 else 0.0
