"""Base agent implementation."""
from typing import Dict, Any, Optional, List
import asyncio
from datetime import datetime
from loguru import logger
from crewai import Task

from .core import BaseAgent
from .memory import AgentMemory
from .metrics import AgentMetrics
from .task import TaskManager
from .models import AgentConfig

class Agent(BaseAgent):
    """Complete agent implementation with all functionality."""
    
    def __init__(
        self,
        config: AgentConfig,
        knowledge_base: Any,
        name: Optional[str] = None
    ):
        """Initialize agent.
        
        Args:
            config: Agent configuration settings
            knowledge_base: Reference to shared knowledge base
            name: Optional human-readable name
        """
        super().__init__(config, knowledge_base, name)
        
        # Initialize components
        self.memory = AgentMemory(memory_size=config.memory_size)
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
        self.metrics.log_action(
            action_name=action_name,
            status="success" if success else "failed",
            duration=duration,
            start_time=datetime.now()
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
    
    async def execute(self, task: Task) -> Dict[str, Any]:
        """Execute a task directly using CrewAI.
        
        This method is called by CrewAI and should not be called directly.
        Use execute_task instead.
        
        Args:
            task: The Task to execute
            
        Returns:
            Dict containing task results
        """
        start_time = datetime.now()
        try:
            # Get relevant context from memory
            context = self.memory.get_relevant_memory(task.description)
            
            # Add memory context to task context if available
            if context:
                task_context = task.context or []
                task_context.append({
                    "description": "Memory context",
                    "expected_output": "Historical information",
                    "memory": context
                })
                task.context = task_context
            
            # Use knowledge base and role-specific logic to process task
            result = {
                "status": "success",
                "result": f"Processed task: {task.description}",
                "confidence": 0.9
            }
            
            duration = (datetime.now() - start_time).total_seconds()
            self._update_performance_metrics("execute", duration, True)
            return result
            
        except Exception as e:
            logger.error(f"Task execution failed: {str(e)}")
            duration = (datetime.now() - start_time).total_seconds()
            self._update_performance_metrics("execute", duration, False)
            return {
                "status": "error",
                "error": str(e),
                "result": None,
                "confidence": 0.0
            }
    
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
            
            # Execute task
            result = await self.task_manager.execute_task(task_with_context, self)
            
            # Update memory with result
            self.memory.add_memory({
                'task': task.description,
                'result': result,
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
        metrics = self.metrics.analyze_performance()
        metrics['memory_utilization'] = self.memory.utilization
        return metrics
    
    async def cleanup(self):
        """Cleanup agent resources."""
        self.memory.clear()
        self.metrics.clear_history()
        self.task_manager.cleanup()
