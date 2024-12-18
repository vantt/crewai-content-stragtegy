"""Strategy skeptic agent implementation."""
from typing import Any, Dict, List, Optional
import uuid
from datetime import datetime
from loguru import logger
from crewai import Task, Agent as CrewAgent

from .strategy_base import StrategyAgent
from .models import AgentConfig
from .types import AgentRole, AgentType
from .decorators import log_action
from .mock_data import MockDataProvider
from .tools import (
    RiskAnalysisTool,
    CompetitiveAnalysisTool,
    MarketValidationTool
)

from ..models.strategy import (
    Challenge,
    RiskAssessment,
    MarketValidation,
    StrategyAnalysis
)

# Initialize skeptic tools
SKEPTIC_TOOLS = [
    RiskAnalysisTool(),
    CompetitiveAnalysisTool(),
    MarketValidationTool()
]

class MarketSkeptic(StrategyAgent):
    """Market skeptic agent implementation."""
    
    def __init__(self, knowledge_base: Any):
        """Initialize market skeptic.
        
        Args:
            knowledge_base: Reference to knowledge base
        """
        config = AgentConfig(
            role=AgentRole.STRATEGY,
            agent_type=AgentType.ADVERSARY,
            temperature=0.7,
            max_iterations=3,
            context_window=4000
        )
        super().__init__(config, knowledge_base)
        
        # Override CrewAI agent for skeptic role with capabilities
        self.crew_agent = CrewAgent(
            role="Market Skeptic",
            goal="Challenge assumptions and identify risks",
            backstory="Critical analyst focused on risk assessment",
            allow_delegation=False,
            verbose=True,
            tools=SKEPTIC_TOOLS
        )
        
        self.challenge_history: List[Challenge] = []
    
    def calculate_confidence_score(self, challenge_result: Dict[str, Any]) -> float:
        """Calculate confidence score based on challenge results."""
        # Implementation depends on specific metrics and criteria
        return 0.85  # Default confidence score
    
    async def execute(self, task: Task) -> Dict[str, Any]:
        """Execute a task and generate appropriate mock data.
        
        Args:
            task: The Task to execute
            
        Returns:
            Dict containing task results
        """
        # Extract context data
        context_data = {}
        for context_item in task.context:
            if isinstance(context_item, dict):
                data = self._extract_context_data(context_item)
                context_data.update(data)
        
        # Generate appropriate mock data based on task
        if "risk" in task.description.lower():
            return MockDataProvider.get_risk_assessment_data()
        elif "market validation" in task.description.lower():
            return MockDataProvider.get_market_validation_data()
        elif "challenge" in task.description.lower():
            return MockDataProvider.get_challenge_data()
        else:
            return context_data  # Return raw context data for other tasks
    
    @log_action
    async def challenge_assumptions(self, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Challenge strategy analysis assumptions.
        
        Args:
            analysis: Strategy analysis to challenge
            
        Returns:
            List of challenged assumptions
        """
        task = Task(
            description="Challenge key assumptions in strategy analysis",
            expected_output="List of challenged assumptions with justifications",
            context=[{
                "description": "Strategy analysis for review",
                "expected_output": "Challenged assumptions",
                "data": analysis
            }]
        )
        result = await self.execute_task(task)
        return result["assumptions"]
    
    @log_action
    async def validate_market_data(self, analysis: Dict[str, Any]) -> MarketValidation:
        """Validate market data and assumptions.
        
        Args:
            analysis: Strategy analysis to validate
            
        Returns:
            MarketValidation model
        """
        task = Task(
            description="Validate market data and assumptions",
            expected_output="Market validation results",
            context=[{
                "description": "Strategy analysis for validation",
                "expected_output": "Market validation details",
                "data": analysis
            }]
        )
        result = await self.execute_task(task)
        
        # Get mock validation data
        validation_data = MockDataProvider.get_market_validation_data()
        return MarketValidation(**validation_data)
    
    @log_action
    async def assess_risks(self, analysis: Dict[str, Any]) -> RiskAssessment:
        """Assess risks in strategy analysis.
        
        Args:
            analysis: Strategy analysis to assess
            
        Returns:
            RiskAssessment model
        """
        task = Task(
            description="Assess risks in strategy analysis",
            expected_output="Risk assessment results",
            context=[{
                "description": "Strategy analysis for risk assessment",
                "expected_output": "Risk assessment details",
                "data": analysis
            }]
        )
        result = await self.execute_task(task)
        
        # Get mock risk data
        risk_data = MockDataProvider.get_risk_assessment_data()
        return RiskAssessment(**risk_data)
    
    @log_action
    async def generate_challenge(
        self,
        analysis: Dict[str, Any],
        constraints: Optional[Dict[str, Any]] = None
    ) -> Challenge:
        """Generate complete challenge to strategy analysis.
        
        Args:
            analysis: Strategy analysis to challenge
            constraints: Optional constraints from previous rounds
            
        Returns:
            Challenge model
        """
        try:
            # Challenge assumptions
            assumptions = await self.challenge_assumptions(analysis)
            
            # Validate market data
            validation = await self.validate_market_data(analysis)
            
            # Assess risks
            risks = await self.assess_risks(analysis)
            
            # Generate final challenge
            challenge = Challenge(
                challenge_id=str(uuid.uuid4()),
                timestamp=datetime.now(),
                challenged_assumptions=assumptions,
                market_validation=validation,
                risk_assessment=risks,
                confidence_score=self.calculate_confidence_score({
                    "assumptions": assumptions,
                    "validation": validation.dict(),
                    "risks": risks.dict()
                })
            )
            
            self.challenge_history.append(challenge)
            return challenge
            
        except Exception as e:
            logger.error(f"Challenge generation failed: {str(e)}")
            raise
