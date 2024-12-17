"""Marketing-focused agent implementation."""
from typing import Any, Dict
from loguru import logger

from .base import Agent
from .models import AgentConfig
from .types import AgentRole, AgentType
from .decorators import log_action
from .exceptions import ExecutionError
from crewai import Task

class MarketingAgent(Agent):
    """Marketing-focused agent implementation."""
    
    def __init__(self, config: AgentConfig, knowledge_base: Any):
        """Initialize marketing agent.
        
        Args:
            config: Agent configuration
            knowledge_base: Reference to knowledge base
        """
        if not isinstance(config, AgentConfig):
            config = AgentConfig(
                role=AgentRole.MARKETING,
                agent_type=AgentType.PRIMARY if not getattr(config, 'is_adversary', False) else AgentType.ADVERSARY,
                temperature=0.8 if getattr(config, 'is_adversary', False) else 0.7
            )
        super().__init__(config, knowledge_base)
    
    async def execute(self, task: Task) -> Dict[str, Any]:
        """Execute a marketing-focused task.
        
        Args:
            task: The Task to execute
            
        Returns:
            Dict containing task results
            
        Raises:
            ValueError: If campaign brief is invalid
        """
        try:
            # Extract campaign brief from task context
            brief = {}
            for context_item in task.context:
                if isinstance(context_item, dict):
                    brief.update(context_item.get('brief', {}))
            
            # Process the task based on brief
            result = {
                "status": "success",
                "campaign_plan": {
                    "name": "Strategic Growth Campaign",
                    "objectives": [
                        "Increase market share",
                        "Enhance brand awareness",
                        "Drive customer engagement"
                    ],
                    "channels": [
                        "Social media",
                        "Content marketing",
                        "Email campaigns"
                    ]
                },
                "target_audience": [
                    "Primary: Young professionals",
                    "Secondary: Small business owners"
                ],
                "budget_allocation": {
                    "social_media": 0.4,
                    "content": 0.3,
                    "email": 0.2,
                    "other": 0.1
                },
                "timeline": {
                    "planning": "2 weeks",
                    "execution": "3 months",
                    "evaluation": "1 month"
                },
                "success_metrics": [
                    "Engagement rate",
                    "Conversion rate",
                    "ROI"
                ]
            }
            
            return result
            
        except ValueError as e:
            # Re-raise validation errors
            raise
        except Exception as e:
            logger.error(f"Error executing campaign creation task: {str(e)}")
            return {
                "status": "error",
                "campaign_plan": {},
                "target_audience": [],
                "budget_allocation": {},
                "timeline": {},
                "success_metrics": [],
                "error": str(e)
            }
    
    @log_action
    async def create_campaign(self, brief: Dict[str, Any]) -> Dict[str, Any]:
        """Create a marketing campaign based on brief.
        
        Args:
            brief: Campaign brief dictionary
            
        Returns:
            Dict containing campaign plan
            
        Raises:
            ValueError: If brief is invalid
            ExecutionError: If campaign creation fails
        """
        # Validate input data
        if not isinstance(brief, dict):
            raise ValueError("Campaign brief must be a dictionary")
        
        # Create task for campaign creation
        task = Task(
            description="Create a marketing campaign based on provided brief",
            expected_output="Campaign plan with target audience, budget allocation, timeline, and success metrics",
            context=[{
                "description": "Campaign brief and requirements",
                "expected_output": "Detailed campaign plan",
                "brief": brief
            }]
        )
        
        try:
            result = await self.execute_task(task)
            if result["status"] == "error":
                raise ExecutionError(result.get("error", "Unknown error in campaign creation"))
            return result
        except (ValueError, ExecutionError) as e:
            # Re-raise validation and execution errors
            raise
        except Exception as e:
            logger.error(f"Error executing campaign creation task: {str(e)}")
            raise ExecutionError(f"Campaign creation failed: {str(e)}")
