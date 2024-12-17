"""Core agent functionality and base classes.

This module provides the foundational agent architecture used throughout the system.
It defines the BaseAgent class which implements core functionality like:
- Agent initialization and configuration
- Basic lifecycle management
- Goal and backstory generation
- Integration with CrewAI

Example:
    ```python
    from src.agents.models import AgentConfig
    from src.agents.types import AgentRole, AgentType

    # Create agent configuration
    config = AgentConfig(
        role=AgentRole.STRATEGY,
        agent_type=AgentType.PRIMARY,
        temperature=0.7
    )

    # Initialize base agent
    agent = BaseAgent(config, knowledge_base)

    # Use the agent
    result = await agent.execute_task(task)
    ```
"""
from typing import Any, Dict, Optional
import uuid
from crewai import Agent
from loguru import logger

from .models import AgentConfig, AgentState
from .memory import AgentMemory
from .metrics import AgentMetrics
from .task import TaskManager

class BaseAgent:
    """Base agent implementation with core functionality.
    
    This class provides the foundation for all specialized agents in the system.
    It handles basic initialization, configuration management, and integration
    with the CrewAI framework.
    
    Attributes:
        agent_id: Unique identifier for the agent
        name: Human-readable name for the agent
        config: Agent configuration settings
        knowledge_base: Reference to shared knowledge base
        crew_agent: CrewAI agent instance
        state: Agent state tracking
        memory: Agent memory management
        metrics: Performance metrics tracking
        task_manager: Task execution management
    """
    
    def __init__(
        self,
        config: AgentConfig,
        knowledge_base: Any,  # Reference to KnowledgeBase instance
        name: Optional[str] = None
    ):
        """Initialize base agent.
        
        Args:
            config: Agent configuration settings
            knowledge_base: Reference to shared knowledge base
            name: Optional human-readable name
        """
        self.agent_id = str(uuid.uuid4())
        self.name = name or f"{config.role.value}_{config.agent_type.value}_{self.agent_id[:8]}"
        self.config = config
        self.knowledge_base = knowledge_base
        self.state = AgentState()
        
        # Initialize components
        self.memory = AgentMemory(memory_size=config.memory_size)
        self.metrics = AgentMetrics()
        self.task_manager = TaskManager(
            max_rpm=config.max_rpm,
            timeout=config.timeout
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
        """Generate agent's goal based on role and type.
        
        Returns:
            String describing the agent's primary goal
        """
        if self.config.role.value == "strategy":
            return "Develop effective marketing strategies"
        elif self.config.role.value == "marketing":
            return "Create engaging marketing campaigns"
        elif self.config.role.value == "content":
            return "Produce high-quality content"
        else:
            return "Support marketing operations"
    
    def _get_agent_backstory(self) -> str:
        """Generate agent's backstory based on role and type.
        
        Returns:
            String describing the agent's background and expertise
        """
        role_backstories = {
            "strategy": "Expert marketing strategist with years of experience",
            "marketing": "Seasoned marketing professional skilled in campaign management",
            "content": "Creative content producer with expertise in multiple formats",
            "planning": "Detail-oriented planner with strong project management skills",
            "execution": "Efficient executor with focus on delivering results",
            "critic": "Analytical reviewer with keen eye for improvement"
        }
        
        base_backstory = role_backstories.get(
            self.config.role.value,
            "Experienced professional in marketing"
        )
        
        if self.config.agent_type.value == "adversary":
            base_backstory += " with a focus on identifying potential issues"
        
        return base_backstory
    
    def record_action(self, action_record: Dict[str, Any]) -> None:
        """Record an action in the agent's state.
        
        Args:
            action_record: Dictionary containing action details
        """
        self.state.add_action(action_record)
    
    def analyze_performance(self) -> Dict[str, Any]:
        """Analyze agent's performance metrics.
        
        Returns:
            Dict containing performance metrics
        """
        return self.metrics.analyze_performance()
    
    async def cleanup(self) -> None:
        """Cleanup agent resources."""
        self.memory.clear()
        self.metrics.clear_history()
        self.task_manager.cleanup()
        self.state.clear()
