"""Core agent functionality and base classes."""
from typing import Any, Dict, Optional
import uuid
from datetime import datetime
from crewai import Agent, Task
from loguru import logger

from .types import (
    AgentRole, AgentType, TaskResult, ActionStatus,
    TaskStatus, Result, MetricsData
)
from .models import AgentConfig, AgentState, MemoryConfig, MetricsConfig, TaskConfig
from .memory import AgentMemory
from .metrics import AgentMetrics
from .task import TaskManager

class BaseAgent:
    """Base agent implementation with core functionality."""
    
    # Role-specific goals
    ROLE_GOALS = {
        AgentRole.STRATEGY: "Develop effective marketing strategies",
        AgentRole.MARKETING: "Create engaging marketing campaigns",
        AgentRole.CONTENT: "Produce high-quality content",
        AgentRole.PLANNING: "Create detailed execution plans",
        AgentRole.EXECUTION: "Execute tasks efficiently and accurately",
        AgentRole.CRITIC: "Provide constructive feedback and improvements"
    }
    
    # Role-specific backstories
    ROLE_BACKSTORIES = {
        AgentRole.STRATEGY: "Expert marketing strategist with years of experience",
        AgentRole.MARKETING: "Seasoned marketing professional skilled in campaign management",
        AgentRole.CONTENT: "Creative content producer with expertise in multiple formats",
        AgentRole.PLANNING: "Detail-oriented planner with strong project management skills",
        AgentRole.EXECUTION: "Efficient executor with focus on delivering results",
        AgentRole.CRITIC: "Analytical reviewer with keen eye for improvement"
    }
    
    def __init__(
        self,
        config: AgentConfig,
        knowledge_base: Any,  # Reference to KnowledgeBase instance
        name: Optional[str] = None
    ):
        """Initialize base agent."""
        # Validate configuration
        if not 0 <= config.temperature <= 1:
            raise ValueError("Temperature must be between 0 and 1")
        if config.max_rpm <= 0:
            raise ValueError("max_rpm must be positive")
        
        self.agent_id = str(uuid.uuid4())
        self.name = name or f"{config.role.value}_{config.agent_type.value}_{self.agent_id[:8]}"
        self.config = config
        self.knowledge_base = knowledge_base
        self.state = AgentState()
        
        # Initialize components with their respective configs
        memory_config = MemoryConfig(memory_size=config.memory_size)
        self.memory = AgentMemory(config=memory_config)
        
        metrics_config = MetricsConfig()
        self.metrics = AgentMetrics(config=metrics_config)
        
        task_config = TaskConfig(
            max_rpm=config.max_rpm,
            timeout=config.timeout
        )
        self.task_manager = TaskManager(
            max_rpm=task_config.max_rpm,
            timeout=task_config.timeout
        )
        
        # Initialize CrewAI agent
        self.crew_agent = Agent(
            role=self.config.role.value,
            goal=self._get_agent_goal(),
            backstory=self._get_agent_backstory(),
            allow_delegation=False,
            verbose=True
        )
    
    def _get_agent_goal(self) -> str:
        """Generate agent's goal based on role and type."""
        return self.ROLE_GOALS.get(self.config.role, "Support marketing operations")
    
    def _get_agent_backstory(self) -> str:
        """Generate agent's backstory based on role and type."""
        base_backstory = self.ROLE_BACKSTORIES.get(
            self.config.role,
            "Experienced professional in marketing"
        )
        
        if self.config.agent_type == AgentType.ADVERSARY:
            base_backstory += " with a focus on identifying potential issues"
        elif self.config.agent_type == AgentType.ASSISTANT:
            base_backstory += " specializing in supporting and enhancing team capabilities"
        
        return base_backstory
    
    async def execute_task(self, task: Task) -> TaskResult:
        """Execute a task and update memory/metrics."""
        try:
            # Execute task
            result = await self.task_manager.execute_task(task, self.crew_agent)
            
            # Log successful execution to metrics
            metrics_result = self.metrics.log_action(
                action_name=task.description,
                status=ActionStatus.SUCCESS.value,
                start_time=result['start_time'],
                duration=result['duration'],
                result=result['result']
            )
            
            # Record successful action in state
            self.state.add_action({
                'action': task.description,
                'timestamp': result['start_time'],
                'status': ActionStatus.SUCCESS.value,
                'duration': result['duration'],
                'result': result['result']
            })
            
            # Update memory with result
            memory_result = self.memory.add_memory({
                'content': {
                    'task': task.description,
                    'result': result
                },
                'timestamp': result['end_time']
            })
            
            return result
            
        except Exception as e:
            # Get error result from task manager
            error_result = e.args[1] if len(e.args) > 1 else None
            error_time = datetime.now()
            error_duration = 0.0
            
            if error_result:
                error_time = error_result['start_time']
                error_duration = error_result['duration']
            
            # Log failed execution to metrics
            metrics_result = self.metrics.log_action(
                action_name=task.description,
                status=ActionStatus.FAILED.value,
                start_time=error_time,
                duration=error_duration,
                error=str(e)
            )
            
            # Record failed action in state
            self.state.add_action({
                'action': task.description,
                'timestamp': error_time,
                'status': ActionStatus.FAILED.value,
                'duration': error_duration,
                'error': str(e)
            })
            
            raise
    
    def record_action(self, action_record: Dict[str, Any]) -> None:
        """Record an action in the agent's state."""
        self.state.add_action(action_record)
        
        # Extract fields for metrics
        action_name = action_record.get('action', 'unknown')
        status = action_record.get('status', 'unknown')
        start_time = action_record.get('timestamp')
        duration = action_record.get('duration', 0.0)
        
        # Remove fields that would conflict with log_action kwargs
        metrics_record = action_record.copy()
        metrics_record.pop('action', None)
        metrics_record.pop('status', None)
        metrics_record.pop('timestamp', None)
        metrics_record.pop('duration', None)
        
        # Log to metrics
        metrics_result = self.metrics.log_action(
            action_name=action_name,
            status=status,
            start_time=start_time,
            duration=duration,
            **metrics_record
        )
    
    def analyze_performance(self) -> MetricsData:
        """Analyze agent's performance metrics."""
        result = self.metrics.analyze_performance()
        if result.success:
            return result.value
        raise ValueError(result.error or "Failed to analyze performance")
    
    async def cleanup(self) -> None:
        """Cleanup agent resources."""
        self.memory.clear()
        self.metrics.clear_history()
        self.task_manager.cleanup()
        self.state.clear()
