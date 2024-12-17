"""Strategy analyst agent implementation."""
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
    MarketResearchTool,
    CompetitiveAnalysisTool,
    StrategicPlanningTool
)

from ..models.strategy import (
    TargetAudience,
    ValueProposition,
    StrategyAnalysis
)

# Initialize analyst tools
ANALYST_TOOLS = [
    MarketResearchTool(),
    CompetitiveAnalysisTool(),
    StrategicPlanningTool()
]

class StrategyAnalyst(StrategyAgent):
    """Strategy analyst agent implementation."""
    
    def __init__(self, knowledge_base: Any):
        """Initialize strategy analyst.
        
        Args:
            knowledge_base: Reference to knowledge base
        """
        config = AgentConfig(
            role=AgentRole.STRATEGY,
            agent_type=AgentType.PRIMARY,
            temperature=0.7,
            max_iterations=3,
            context_window=4000
        )
        super().__init__(config, knowledge_base)
        
        # Override CrewAI agent for analyst role with capabilities
        self.crew_agent = CrewAgent(
            role="Strategy Analyst",
            goal="Develop effective marketing strategies",
            backstory="Expert marketing strategist with years of experience",
            allow_delegation=False,
            verbose=True,
            tools=ANALYST_TOOLS
        )
        
        self.analysis_history: List[StrategyAnalysis] = []
    
    def calculate_confidence_score(self, analysis_result: Dict[str, Any]) -> float:
        """Calculate confidence score based on analysis results."""
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
        if "value proposition" in task.description.lower():
            return MockDataProvider.get_value_proposition_data()
        elif "opportunities" in task.description.lower() or "risks" in task.description.lower():
            return MockDataProvider.get_opportunities_data()
        elif "market analysis" in task.description.lower():
            return MockDataProvider.get_market_analysis_data(context_data)
        else:
            return context_data  # Return raw context data for other tasks
    
    @log_action
    async def analyze_target_audience(self, market_data: Dict[str, Any]) -> TargetAudience:
        """Analyze and segment target audience.
        
        Args:
            market_data: Market data for analysis
            
        Returns:
            TargetAudience model
        """
        # Generate target audience data directly from market data
        result = {
            "segments": [{"type": "primary", "description": "test"}],
            "pain_points": ["test pain point"],
            "goals": ["test goal"],
            "demographics": market_data["demographics"],  # Use demographics directly from market data
            "behavioral_traits": ["test trait"]
        }
        return TargetAudience(**result)
    
    @log_action
    async def develop_value_proposition(self, audience: TargetAudience) -> ValueProposition:
        """Develop value proposition based on audience analysis.
        
        Args:
            audience: Target audience analysis
            
        Returns:
            ValueProposition model
        """
        task = Task(
            description="Develop comprehensive value proposition",
            expected_output="Value proposition with benefits and advantages",
            context=[{
                "description": "Target audience analysis",
                "expected_output": "Value proposition details",
                "data": audience.model_dump()
            }]
        )
        result = await self.execute_task(task)
        return ValueProposition(**result)
    
    @log_action
    async def conduct_strategy_analysis(
        self,
        market_data: Dict[str, Any],
        constraints: Optional[Dict[str, Any]] = None
    ) -> StrategyAnalysis:
        """Conduct complete strategy analysis.
        
        Args:
            market_data: Market data for analysis
            constraints: Optional constraints from previous challenges
            
        Returns:
            StrategyAnalysis model
        """
        try:
            # Analyze target audience
            audience = await self.analyze_target_audience(market_data)
            
            # Develop value proposition
            value_prop = await self.develop_value_proposition(audience)
            
            # Analyze market opportunities and risks
            opportunities_task = Task(
                description="Identify market opportunities and risks",
                expected_output="Market opportunities, risks, and recommendations",
                context=[{
                    "description": "Market and audience analysis",
                    "expected_output": "Opportunities and risks assessment",
                    "data": {
                        "market_data": market_data,
                        "audience": audience.model_dump(),
                        "constraints": constraints or {}
                    }
                }]
            )
            opportunities_result = await self.execute_task(opportunities_task)
            
            # Generate final analysis
            analysis = StrategyAnalysis(
                analysis_id=str(uuid.uuid4()),
                timestamp=datetime.now(),
                target_audience=audience,
                value_proposition=value_prop,
                market_opportunities=[{"name": opp["name"], "impact": opp["impact"]} for opp in opportunities_result["opportunities"]],
                risk_factors=[{"name": risk["name"], "severity": risk["severity"]} for risk in opportunities_result["risks"]],
                recommendations=[{"action": rec["action"], "priority": rec["priority"]} for rec in opportunities_result["recommendations"]],
                confidence_score=self.calculate_confidence_score(opportunities_result)
            )
            
            self.analysis_history.append(analysis)
            return analysis
            
        except Exception as e:
            logger.error(f"Strategy analysis failed: {str(e)}")
            raise
