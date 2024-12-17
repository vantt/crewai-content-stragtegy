"""Market skeptic agent implementation."""
from typing import Any, Dict, List
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
    MarketValidationTool,
    CompetitiveIntelligenceTool
)

from ..models.strategy import (
    StrategyAnalysis,
    MarketAssumption,
    CompetitiveAnalysis,
    MarketChallenge
)

# Initialize skeptic tools
SKEPTIC_TOOLS = [
    RiskAnalysisTool(),
    MarketValidationTool(),
    CompetitiveIntelligenceTool()
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
            temperature=0.8,
            max_iterations=3,
            context_window=4000
        )
        super().__init__(config, knowledge_base)
        
        # Override CrewAI agent for skeptic role with capabilities
        self.crew_agent = CrewAgent(
            role="Market Skeptic",
            goal="Develop effective marketing strategies",
            backstory="Expert marketing strategist with years of experience with a focus on identifying potential issues",
            allow_delegation=False,
            verbose=True,
            tools=SKEPTIC_TOOLS
        )
        
        self.challenge_history: List[MarketChallenge] = []
    
    async def execute(self, task: Task) -> Dict[str, Any]:
        """Execute a task and generate appropriate mock data.
        
        Args:
            task: The Task to execute
            
        Returns:
            Dict containing task results
        """
        if "challenge" in task.description.lower() or "assumptions" in task.description.lower():
            return MockDataProvider.get_assumptions_data()
        elif "competitive analysis" in task.description.lower():
            return MockDataProvider.get_competitive_analysis_data()
        elif "risks" in task.description.lower() or "alternatives" in task.description.lower():
            return {
                "risks": [{"name": "test risk", "severity": "high"}],
                "alternatives": [{"approach": "test approach", "viability": "medium"}],
                "metrics": {"risk_score": 0.7, "market_fit": 0.8}
            }
        else:
            return {"status": "success", "result": f"Processed task: {task.description}"}
    
    @log_action
    async def challenge_assumptions(self, analysis: StrategyAnalysis) -> List[MarketAssumption]:
        """Challenge key assumptions in the strategy analysis.
        
        Args:
            analysis: Strategy analysis to challenge
            
        Returns:
            List of challenged assumptions
        """
        task = Task(
            description="Identify and challenge key market assumptions",
            expected_output="List of challenged assumptions with evidence",
            context=[{
                "description": "Strategy analysis to challenge",
                "expected_output": "List of challenged assumptions",
                "data": analysis.model_dump()
            }]
        )
        result = await self.execute_task(task)
        return [MarketAssumption(**assumption) for assumption in result]
    
    @log_action
    async def analyze_competition(self, analysis: StrategyAnalysis) -> CompetitiveAnalysis:
        """Perform detailed competitive analysis.
        
        Args:
            analysis: Strategy analysis to analyze
            
        Returns:
            CompetitiveAnalysis model
        """
        task = Task(
            description="Conduct thorough competitive analysis",
            expected_output="Competitive analysis with SWOT assessment",
            context=[{
                "description": "Strategy analysis for competitive review",
                "expected_output": "Competitive analysis details",
                "data": analysis.model_dump()
            }]
        )
        result = await self.execute_task(task)
        return CompetitiveAnalysis(**result)
    
    @log_action
    async def generate_challenge(self, analysis: StrategyAnalysis) -> MarketChallenge:
        """Generate comprehensive challenge to strategy analysis.
        
        Args:
            analysis: Strategy analysis to challenge
            
        Returns:
            MarketChallenge model
        """
        try:
            # Challenge assumptions
            assumptions = await self.challenge_assumptions(analysis)
            
            # Analyze competition
            competitive_analysis = await self.analyze_competition(analysis)
            
            # Identify risks and alternatives
            validation_task = Task(
                description="Identify market risks and alternative approaches",
                expected_output="Market risks, alternatives, and validation metrics",
                context=[{
                    "description": "Analysis and assumptions data",
                    "expected_output": "Risk assessment and alternatives",
                    "data": {
                        "analysis": analysis.model_dump(),
                        "assumptions": [a.model_dump() for a in assumptions],
                        "competitive_analysis": competitive_analysis.model_dump()
                    }
                }]
            )
            validation_result = await self.execute_task(validation_task)
            
            # Generate final challenge
            challenge = MarketChallenge(
                challenge_id=str(uuid.uuid4()),
                timestamp=datetime.now(),
                assumptions=assumptions,
                competitive_analysis=competitive_analysis,
                market_risks=validation_result["risks"],
                alternative_approaches=validation_result["alternatives"],
                validation_metrics=validation_result["metrics"]
            )
            
            self.challenge_history.append(challenge)
            return challenge
            
        except Exception as e:
            logger.error(f"Challenge generation failed: {str(e)}")
            raise
