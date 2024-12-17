"""Strategy-focused agent implementation."""
from typing import Any, Dict
from loguru import logger

from .base import Agent
from .models import AgentConfig
from .types import AgentRole, AgentType
from .decorators import log_action
from .exceptions import ExecutionError
from crewai import Task

class StrategyAgent(Agent):
    """Strategy-focused agent implementation."""
    
    def __init__(self, config: AgentConfig, knowledge_base: Any):
        """Initialize strategy agent.
        
        Args:
            config: Agent configuration
            knowledge_base: Reference to knowledge base
        """
        if not isinstance(config, AgentConfig):
            config = AgentConfig(
                role=AgentRole.STRATEGY,
                agent_type=AgentType.PRIMARY if not getattr(config, 'is_adversary', False) else AgentType.ADVERSARY,
                temperature=0.8 if getattr(config, 'is_adversary', False) else 0.7
            )
        super().__init__(config, knowledge_base)
    
    async def execute(self, task: Task) -> Dict[str, Any]:
        """Execute a strategy-focused task.
        
        Args:
            task: The Task to execute
            
        Returns:
            Dict containing task results
            
        Raises:
            ValueError: If market data is invalid
        """
        try:
            # Extract market data from task context
            market_data = {}
            for context_item in task.context:
                if isinstance(context_item, dict):
                    market_data.update(context_item.get('data', {}))
            
            # Validate market data
            if "market_size" in market_data:
                if not isinstance(market_data["market_size"], (int, float)):
                    raise ValueError("Invalid market size value")
            
            # Process the task based on market data
            result = {
                "status": "success",
                "market_analysis": {
                    "market_size": market_data.get("market_size", 0),
                    "growth_rate": market_data.get("growth_rate", 0),
                    "competitors": market_data.get("competitors", []),
                    "target_audience": market_data.get("target_audience", "")
                },
                "recommendations": [
                    "Focus on market expansion",
                    "Invest in digital transformation",
                    "Enhance customer experience"
                ],
                "confidence_score": 0.85
            }
            
            return result
            
        except ValueError as e:
            # Re-raise validation errors
            raise
        except Exception as e:
            logger.error(f"Error executing market analysis task: {str(e)}")
            return {
                "status": "error",
                "market_analysis": {},
                "recommendations": [],
                "confidence_score": 0.0,
                "error": str(e)
            }
    
    @log_action
    async def analyze_market(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze market data and provide insights.
        
        Args:
            data: Market data dictionary
            
        Returns:
            Dict containing analysis results
            
        Raises:
            ValueError: If market data is invalid
            ExecutionError: If analysis fails
        """
        # Validate input data
        if not isinstance(data, dict):
            raise ValueError("Market data must be a dictionary")
            
        # Validate market size
        if "market_size" in data and not isinstance(data["market_size"], (int, float)):
            raise ValueError("Invalid market size value")
            
        # Create task for market analysis
        task = Task(
            description="Analyze market data and provide strategic insights",
            expected_output="Market analysis with recommendations and confidence score",
            context=[{
                "description": "Market data for analysis",
                "expected_output": "Analyzed market insights",
                "data": data
            }]
        )
        
        try:
            result = await self.execute_task(task)
            if result["status"] == "error":
                raise ExecutionError(result.get("error", "Unknown error in market analysis"))
            return result
        except (ValueError, ExecutionError) as e:
            # Re-raise validation and execution errors
            raise
        except Exception as e:
            logger.error(f"Error executing market analysis task: {str(e)}")
            raise ExecutionError(f"Market analysis failed: {str(e)}")
