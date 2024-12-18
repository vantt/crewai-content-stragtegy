"""Base agent implementation."""
from typing import Dict, Any, Optional, List, Union
import asyncio
from datetime import datetime
from loguru import logger
from crewai import Task, Agent as CrewAgent

from .core import BaseAgent
from .memory import AgentMemory
from .metrics import AgentMetrics
from .task import TaskManager
from .models import AgentConfig, MemoryConfig

class Agent(BaseAgent):
    """Base agent implementation with core functionality."""
    
    def __init__(
        self,
        config: AgentConfig,
        knowledge_base: Any,
        name: Optional[str] = None
    ):
        """Initialize agent.
        
        Args:
            config: Agent configuration settings
            knowledge_base: Reference to knowledge base
            name: Optional human-readable name
        """
        super().__init__(config, knowledge_base, name)
        
        # Initialize CrewAI agent
        self.crew_agent = CrewAgent(
            role=config.role.value,
            goal=f"Develop effective {config.role.value} strategies",
            backstory=f"Expert {config.role.value} strategist with years of experience",
            allow_delegation=False,
            verbose=True
        )
        
        # Initialize components with proper configuration
        memory_config = MemoryConfig(memory_size=config.memory_size)
        self.memory = AgentMemory(config=memory_config)
        self.metrics = AgentMetrics()
        self.task_manager = TaskManager(
            max_rpm=config.max_rpm,
            timeout=config.timeout
        )
    
    def _update_performance_metrics(self, action_name: str, duration: float, success: bool) -> None:
        """Update performance metrics for an action.
        
        Args:
            action_name: Name of the action
            duration: Duration of the action in seconds
            success: Whether the action was successful
        """
        metadata = {
            "success": success,
            "start_time": datetime.now().isoformat()
        }
        
        self.metrics.log_action(
            action_name=action_name,
            duration=duration,
            success=success,
            metadata=metadata
        )
    
    def _create_task_context(self, task_description: str, original_context: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Create task context with memory.
        
        Args:
            task_description: Description of the task
            original_context: Original task context
            
        Returns:
            Updated context with memory
        """
        # Get relevant memory
        memory_context = self.memory.get_relevant_memory(task_description)
        
        # Create new context list
        context = original_context.copy() if original_context else []
        
        # Add memory context as a new item if we have relevant memories
        if memory_context:
            context.append({
                "description": "Relevant memory context",
                "expected_output": "Historical context for the task",
                "memory": memory_context
            })
        
        return context
    
    def _extract_context_data(self, context_item: Dict[str, Any]) -> Dict[str, Any]:
        """Extract data from context item, handling both nested and direct data.
        
        Args:
            context_item: Context item to extract data from
            
        Returns:
            Extracted data
        """
        data = context_item.get('data', {})
        if isinstance(data, dict):
            # Handle both direct and nested market data
            if "market_data" in data:
                return data["market_data"]
            return data
        return {}
    
    async def execute(self, task: Task) -> Dict[str, Any]:
        """Execute a task directly using CrewAI.
        
        This method should be overridden by specific agent implementations
        to provide their own mock data and handle their specific data structures.
        
        Args:
            task: The Task to execute
            
        Returns:
            Dict containing task results
            
        Raises:
            NotImplementedError: If not overridden by subclass
        """
        raise NotImplementedError("Subclasses must implement execute()")
    
    async def execute_task(self, task: Task) -> Dict[str, Any]:
        """Execute a task and update memory/metrics.
        
        Args:
            task: The Task to execute
            
        Returns:
            Dict containing task results
        """
        start_time = datetime.now()
        try:
            # Create new task with memory context
            task_with_context = Task(
                description=task.description,
                expected_output=task.expected_output,
                context=self._create_task_context(task.description, task.context)
            )
            
            # Execute task directly instead of using task manager
            result = await self.execute(task_with_context)
            
            # Update memory with result
            self.memory.add_memory({
                'content': {
                    'task': task.description,
                    'result': result,
                }
            })
            
            duration = (datetime.now() - start_time).total_seconds()
            self._update_performance_metrics("execute_task", duration, True)
            return result
            
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            self._update_performance_metrics("execute_task", duration, False)
            raise
    
    def analyze_performance(self) -> Dict[str, Any]:
        """Analyze agent's performance metrics."""
        return self.metrics.get_metrics_summary()
    
    async def cleanup(self):
        """Cleanup agent resources."""
        self.memory.clear()
        self.task_manager.cleanup()
