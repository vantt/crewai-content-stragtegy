"""Strategy debate implementation."""
from typing import Dict, Any, List
from datetime import datetime
from loguru import logger
from crewai import Agent as CrewAgent

from .strategy_analyst import StrategyAnalyst
from .strategy_skeptic import MarketSkeptic
from .decorators import log_action
from .models import AgentConfig, MemoryConfig
from .types import AgentRole, AgentType
from .base import BaseAgent
from .memory import AgentMemory
from .metrics import AgentMetrics

class StrategyDebate(BaseAgent):
    """Manages debate between strategy analyst and skeptic."""
    
    def __init__(self, analyst: StrategyAnalyst, skeptic: MarketSkeptic):
        """Initialize debate.
        
        Args:
            analyst: Strategy analyst agent
            skeptic: Market skeptic agent
        """
        # Initialize base agent with debate configuration
        config = AgentConfig(
            role=AgentRole.STRATEGY,
            agent_type=AgentType.PRIMARY,
            temperature=0.7,
            max_iterations=3,
            context_window=4000
        )
        super().__init__(config, None, "strategy_debate")  # No knowledge base needed for debate
        
        # Override CrewAI agent for debate role
        self.crew_agent = CrewAgent(
            role="Strategy Debate",
            goal="Facilitate effective strategy debates",
            backstory="Expert debate facilitator with experience in strategy analysis",
            allow_delegation=False,
            verbose=True
        )
        
        # Initialize components
        memory_config = MemoryConfig(memory_size=config.memory_size)
        self.memory = AgentMemory(config=memory_config)
        self.metrics = AgentMetrics()
        
        self.analyst = analyst
        self.skeptic = skeptic
        self.debate_history: List[Dict[str, Any]] = []
    
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
    
    def _record_debate_round(
        self,
        round_num: int,
        analysis: Any,
        challenge: Any,
        status: str
    ) -> None:
        """Record a debate round.
        
        Args:
            round_num: Round number
            analysis: Strategy analysis
            challenge: Market challenge
            status: Round status
        """
        self.debate_history.append({
            "round": round_num,
            "analysis": analysis.model_dump(),
            "challenge": challenge.model_dump(),
            "status": status,
            "timestamp": datetime.now()
        })
    
    @log_action
    async def conduct_debate(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Conduct strategy debate.
        
        Args:
            market_data: Market data for analysis
            
        Returns:
            Dict containing debate results
        """
        try:
            # Initial analysis
            analysis = await self.analyst.conduct_strategy_analysis(market_data)
            
            # Initial challenge
            challenge = await self.skeptic.generate_challenge(analysis)
            
            # Record first round
            self._record_debate_round(1, analysis, challenge, "initial")
            
            # Revised analysis with constraints
            analysis = await self.analyst.conduct_strategy_analysis(
                market_data,
                constraints={"previous_challenge": challenge.model_dump()}
            )
            
            # Final challenge
            challenge = await self.skeptic.generate_challenge(analysis)
            
            # Record final round
            self._record_debate_round(2, analysis, challenge, "final")
            
            # Return debate results
            return {
                "final_analysis": analysis.model_dump(),
                "debate_history": self.debate_history,
                "consensus_reached": True
            }
            
        except Exception as e:
            logger.error(f"Strategy debate failed: {str(e)}")
            raise
