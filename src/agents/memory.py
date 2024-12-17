"""Memory management functionality for agents."""
from typing import List, Optional, Dict, Any
from datetime import datetime

from .types import (
    MemoryItem, MemoryItemDict, Context, Timestamp,
    Result, ValidationResult, is_memory_item
)
from .models import MemoryConfig

class AgentMemory:
    """Handles agent memory management and retrieval.
    
    This class manages an agent's memory by storing, retrieving, and filtering
    memory items based on relevance and recency. It handles memory size limits,
    TTL-based expiration, and context-based retrieval.
    
    Attributes:
        config: Configuration settings for memory management
        size: Current number of memory items
        is_full: Whether memory has reached capacity
        utilization: Current memory utilization percentage
    """
    
    def __init__(self, config: Optional[MemoryConfig] = None) -> None:
        """Initialize memory management.
        
        Args:
            config: Optional memory configuration settings. If not provided,
                   default settings will be used.
                   
        Raises:
            ValueError: If configuration is invalid
        """
        self.config = config or MemoryConfig()
        self._validate_config()
        self._memory: List[MemoryItem] = []
    
    def _validate_config(self) -> ValidationResult:
        """Validate memory configuration.
        
        Returns:
            Tuple of (is_valid, error_message)
            
        Raises:
            ValueError: If configuration is invalid
        """
        is_valid, error = self.config.validate()
        if not is_valid:
            raise ValueError(f"Invalid memory configuration: {error}")
        return True, None
    
    def add_memory(self, item: Dict[str, Any]) -> Result[MemoryItem]:
        """Add new item to memory with timestamp and TTL.
        
        Args:
            item: Memory item to store. Must contain at least a 'content' field.
                 Optional fields: timestamp, ttl, metadata
                 
        Returns:
            Result containing the stored memory item or error message
            
        Example:
            >>> result = memory.add_memory({
            ...     'content': 'Important information',
            ...     'metadata': {'source': 'user_input'}
            ... })
            >>> if result.success:
            ...     print(f"Stored memory: {result.value['content']}")
        """
        try:
            current_time = datetime.now()
            
            # Construct properly typed memory item
            memory_item: MemoryItem = {
                'content': item.get('content'),
                'timestamp': item.get('timestamp', current_time),
                'ttl': item.get('ttl', current_time.timestamp() + self.config.ttl_seconds),
                'metadata': item.get('metadata', {})
            }
            
            # Validate memory item
            if not is_memory_item(memory_item):
                return Result.err("Invalid memory item format")
            
            # Add to front of list (most recent first)
            self._memory.insert(0, memory_item)
            
            # Maintain memory size limit
            while len(self._memory) > self.config.memory_size:
                self._memory.pop()
                
            # Clean expired memories
            self._cleanup_expired()
            
            return Result.ok(memory_item)
            
        except Exception as e:
            return Result.err(f"Failed to add memory: {str(e)}")
    
    def _cleanup_expired(self) -> None:
        """Remove expired memory items based on TTL."""
        current_time = datetime.now().timestamp()
        self._memory = [m for m in self._memory 
                       if m.get('ttl', 0) > current_time]
    
    def _calculate_relevance(self, memory: MemoryItem, context: str) -> float:
        """Calculate relevance score for a memory item.
        
        Args:
            memory: Memory item to score
            context: Context to compare against
            
        Returns:
            Relevance score between 0 and 1
            
        Note:
            Current implementation returns high relevance for all memories.
            This should be enhanced with proper relevance calculation.
        """
        # TODO: Implement proper relevance scoring
        # For now, return high relevance for all memories
        return 1.0
    
    def get_relevant_memory(self, context: str) -> Result[List[MemoryItem]]:
        """Retrieve relevant memories based on context.
        
        Retrieves memories that are:
        1. Not expired (based on TTL)
        2. Relevant to the given context (above threshold)
        3. Within the max context length limit
        
        Args:
            context: The context to find relevant memories for
            
        Returns:
            Result containing list of relevant memory items or error message
            
        Example:
            >>> result = memory.get_relevant_memory("task planning")
            >>> if result.success:
            ...     memories = result.value
            ...     for mem in memories:
            ...         print(mem['content'])
        """
        try:
            self._cleanup_expired()
            
            # Score memories
            scored_memories = [
                (self._calculate_relevance(m, context), m)
                for m in self._memory
            ]
            
            # Filter by relevance threshold
            relevant_memories = [
                m for score, m in scored_memories
                if score >= self.config.relevance_threshold
            ]
            
            # Sort by timestamp (most recent first)
            relevant_memories.sort(
                key=lambda x: x['timestamp'],
                reverse=True
            )
            
            # Limit context length
            total_length = 0
            filtered_memories = []
            for memory in relevant_memories:
                mem_length = len(str(memory))
                if total_length + mem_length <= self.config.max_context_length:
                    filtered_memories.append(memory)
                    total_length += mem_length
                else:
                    break
                    
            return Result.ok(filtered_memories)
            
        except Exception as e:
            return Result.err(f"Failed to retrieve memories: {str(e)}")
    
    def clear(self) -> None:
        """Clear all memories and reset state."""
        self._memory.clear()
    
    @property
    def size(self) -> int:
        """Get current number of memory items."""
        return len(self._memory)
    
    @property
    def is_full(self) -> bool:
        """Check if memory is at capacity."""
        return len(self._memory) >= self.config.memory_size
    
    @property
    def utilization(self) -> float:
        """Get memory utilization percentage (0-1)."""
        return (self.size / self.config.memory_size 
                if self.config.memory_size > 0 else 0.0)
