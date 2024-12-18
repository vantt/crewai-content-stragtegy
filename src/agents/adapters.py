"""Adapters for integrating existing agents with the new debate protocol.

This module provides adapter classes that bridge the existing agent implementations
with the new event-based protocol system.
"""
from typing import Dict, Any, Optional
from datetime import datetime
import uuid

from src.core import (
    Event,
    EventType,
    EventEmitter,
    StateManager,
    DebateStatus
)
from .strategy_analyst import StrategyAnalyst
from .strategy_skeptic import MarketSkeptic
from .models import AgentConfig

class BaseAgentAdapter:
    """Base adapter class for agent integration."""
    
    def __init__(
        self,
        event_emitter: EventEmitter,
        state_manager: StateManager,
        debate_id: str
    ):
        """Initialize the base adapter.
        
        Args:
            event_emitter: System event emitter
            state_manager: System state manager
            debate_id: ID of the debate this agent is part of
        """
        self.event_emitter = event_emitter
        self.state_manager = state_manager
        self.debate_id = debate_id
        self.agent_id = str(uuid.uuid4())

    async def emit_agent_event(
        self,
        event_type: EventType,
        data: Optional[Dict[str, Any]] = None
    ) -> None:
        """Emit an agent-related event.
        
        Args:
            event_type: Type of event to emit
            data: Optional event data
        """
        await self.event_emitter.emit(Event(
            event_type=event_type,
            agent_id=self.agent_id,
            data={
                "debate_id": self.debate_id,
                **(data or {})
            }
        ))

class StrategyAnalystAdapter(BaseAgentAdapter):
    """Adapter for the StrategyAnalyst agent."""
    
    def __init__(
        self,
        analyst: StrategyAnalyst,
        event_emitter: EventEmitter,
        state_manager: StateManager,
        debate_id: str
    ):
        """Initialize the analyst adapter.
        
        Args:
            analyst: StrategyAnalyst instance to adapt
            event_emitter: System event emitter
            state_manager: System state manager
            debate_id: ID of the debate this agent is part of
        """
        super().__init__(event_emitter, state_manager, debate_id)
        self.analyst = analyst

    async def analyze_market(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Conduct market analysis through the adapted analyst.
        
        Args:
            market_data: Market data to analyze
            
        Returns:
            Analysis results
        """
        try:
            # Emit start event
            await self.emit_agent_event(
                EventType.AGENT_TASK_STARTED,
                {"task": "market_analysis"}
            )
            
            # Conduct analysis
            analysis = await self.analyst.conduct_strategy_analysis(market_data)
            
            # Convert to event-friendly format
            result = analysis.model_dump()
            
            # Emit completion event
            await self.emit_agent_event(
                EventType.AGENT_TASK_COMPLETED,
                {
                    "task": "market_analysis",
                    "result": result
                }
            )
            
            # Emit argument submission event
            await self.emit_agent_event(
                EventType.ARGUMENT_SUBMITTED,
                {
                    "type": "analysis",
                    "content": result
                }
            )
            
            return result
            
        except Exception as e:
            # Emit failure event
            await self.emit_agent_event(
                EventType.AGENT_TASK_FAILED,
                {
                    "task": "market_analysis",
                    "error": str(e)
                }
            )
            raise

class MarketSkepticAdapter(BaseAgentAdapter):
    """Adapter for the MarketSkeptic agent."""
    
    def __init__(
        self,
        skeptic: MarketSkeptic,
        event_emitter: EventEmitter,
        state_manager: StateManager,
        debate_id: str
    ):
        """Initialize the skeptic adapter.
        
        Args:
            skeptic: MarketSkeptic instance to adapt
            event_emitter: System event emitter
            state_manager: System state manager
            debate_id: ID of the debate this agent is part of
        """
        super().__init__(event_emitter, state_manager, debate_id)
        self.skeptic = skeptic

    async def challenge_analysis(
        self,
        analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate challenges for an analysis through the adapted skeptic.
        
        Args:
            analysis: Analysis to challenge
            
        Returns:
            Challenge results
        """
        try:
            # Emit start event
            await self.emit_agent_event(
                EventType.AGENT_TASK_STARTED,
                {"task": "generate_challenge"}
            )
            
            # Generate challenge
            challenge = await self.skeptic.generate_challenge(analysis)
            
            # Convert to event-friendly format
            result = challenge.model_dump()
            
            # Emit completion event
            await self.emit_agent_event(
                EventType.AGENT_TASK_COMPLETED,
                {
                    "task": "generate_challenge",
                    "result": result
                }
            )
            
            # Emit argument submission event
            await self.emit_agent_event(
                EventType.ARGUMENT_SUBMITTED,
                {
                    "type": "challenge",
                    "content": result
                }
            )
            
            return result
            
        except Exception as e:
            # Emit failure event
            await self.emit_agent_event(
                EventType.AGENT_TASK_FAILED,
                {
                    "task": "generate_challenge",
                    "error": str(e)
                }
            )
            raise

class DebateSessionManager:
    """Manages a debate session between adapted agents."""
    
    def __init__(
        self,
        analyst_adapter: StrategyAnalystAdapter,
        skeptic_adapter: MarketSkepticAdapter,
        event_emitter: EventEmitter,
        state_manager: StateManager
    ):
        """Initialize the debate session manager.
        
        Args:
            analyst_adapter: Adapted strategy analyst
            skeptic_adapter: Adapted market skeptic
            event_emitter: System event emitter
            state_manager: System state manager
        """
        self.analyst = analyst_adapter
        self.skeptic = skeptic_adapter
        self.event_emitter = event_emitter
        self.state_manager = state_manager
        self.debate_id = analyst_adapter.debate_id

    async def conduct_debate(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Conduct a debate session between the agents.
        
        Args:
            market_data: Initial market data for analysis
            
        Returns:
            Debate results
        """
        try:
            # Set initial debate state
            await self.state_manager.set_debate_state(
                self.debate_id,
                DebateStatus.IN_PROGRESS
            )
            
            # Initial analysis
            analysis = await self.analyst.analyze_market(market_data)
            
            # Generate challenge
            challenge = await self.skeptic.challenge_analysis(analysis)
            
            # Revised analysis with constraints
            final_analysis = await self.analyst.analyze_market({
                **market_data,
                "previous_challenge": challenge
            })
            
            # Set final state
            await self.state_manager.set_debate_state(
                self.debate_id,
                DebateStatus.CONSENSUS_REACHED
            )
            
            return {
                "initial_analysis": analysis,
                "challenge": challenge,
                "final_analysis": final_analysis,
                "debate_id": self.debate_id
            }
            
        except Exception as e:
            await self.state_manager.set_debate_state(
                self.debate_id,
                DebateStatus.FAILED
            )
            raise
