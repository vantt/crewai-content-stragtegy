"""Strategy debate implementation with enhanced metrics and monitoring."""
from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid
from loguru import logger
from pydantic import BaseModel, Field

from src.core import (
    Event,
    EventType,
    EventEmitter,
    StateManager,
    DebateStatus
)
from .metrics import (
    AgentMetricsCollector,
    AgentMetrics
)

class Evidence(BaseModel):
    """Model for debate evidence."""
    evidence_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: str
    source: str
    content: Dict[str, Any]
    confidence_score: float
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class DebateRoundMetrics(BaseModel):
    """Model for debate round metrics."""
    argument_count: int = 0
    evidence_count: int = 0
    agent_metrics: Dict[str, AgentMetrics] = Field(default_factory=dict)
    round_duration: float = 0.0  # in seconds

class DebateRound(BaseModel):
    """Model for debate rounds."""
    round_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    round_number: int
    arguments: List[Dict[str, Any]] = Field(default_factory=list)
    evidence: List[Evidence] = Field(default_factory=list)
    metrics: Optional[DebateRoundMetrics] = None
    start_time: datetime = Field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    status: str = "pending"

class StrategyDebate:
    """Manages debate between strategy agents with enhanced metrics."""
    
    def __init__(
        self,
        event_emitter: EventEmitter,
        state_manager: StateManager,
        max_rounds: int = 5,
        consensus_threshold: float = 0.8
    ):
        """Initialize debate.
        
        Args:
            event_emitter: System event emitter
            state_manager: System state manager
            max_rounds: Maximum number of rounds
            consensus_threshold: Threshold for consensus
        """
        self.event_emitter = event_emitter
        self.state_manager = state_manager
        self.max_rounds = max_rounds
        self.consensus_threshold = consensus_threshold
        
        self.debate_id = str(uuid.uuid4())
        self.rounds: List[DebateRound] = []
        self.current_round: Optional[DebateRound] = None
        
        # Initialize metrics
        self.metrics_collector = AgentMetricsCollector()
        
        logger.info(f"Strategy debate initialized - ID: {self.debate_id}")

    async def start_round(self) -> DebateRound:
        """Start a new debate round.
        
        Returns:
            New debate round
            
        Raises:
            ValueError: If max rounds reached
        """
        if len(self.rounds) >= self.max_rounds:
            raise ValueError("Maximum rounds reached")
        
        round_number = len(self.rounds) + 1
        self.current_round = DebateRound(round_number=round_number)
        self.rounds.append(self.current_round)
        
        await self.event_emitter.emit(Event(
            event_type=EventType.ROUND_COMPLETED,
            data={
                "debate_id": self.debate_id,
                "round_number": round_number,
                "status": "started"
            }
        ))
        
        logger.info(f"Started round {round_number} - Debate ID: {self.debate_id}")
        return self.current_round

    async def add_argument(
        self,
        agent_id: str,
        argument_type: str,
        content: Dict[str, Any],
        evidence: List[Dict[str, Any]]
    ) -> None:
        """Add an argument to the current round.
        
        Args:
            agent_id: ID of arguing agent
            argument_type: Type of argument
            content: Argument content
            evidence: Supporting evidence
            
        Raises:
            ValueError: If no active round
        """
        if not self.current_round:
            raise ValueError("No active debate round")
        
        try:
            start_time = datetime.now()
            
            # Create evidence entries
            evidence_entries = []
            for e in evidence:
                evidence_entry = Evidence(
                    type=e["type"],
                    source=e["source"],
                    content=e["content"],
                    confidence_score=e.get("confidence", 0.8),
                    metadata=e.get("metadata", {})
                )
                evidence_entries.append(evidence_entry)
            
            # Add argument
            argument = {
                "agent_id": agent_id,
                "type": argument_type,
                "content": content,
                "evidence_ids": [e.evidence_id for e in evidence_entries],
                "timestamp": datetime.now().isoformat()
            }
            
            self.current_round.arguments.append(argument)
            self.current_round.evidence.extend(evidence_entries)
            
            # Record metrics
            duration = (datetime.now() - start_time).total_seconds()
            self.metrics_collector.record_task(
                agent_id,
                argument_type,
                duration,
                True
            )
            
            # Update round metrics
            if not self.current_round.metrics:
                self.current_round.metrics = DebateRoundMetrics()
            
            self.current_round.metrics.argument_count += 1
            self.current_round.metrics.evidence_count += len(evidence_entries)
            self.current_round.metrics.agent_metrics[agent_id] = (
                self.metrics_collector.get_or_create_metrics(agent_id)
            )
            
            # Emit event
            await self.event_emitter.emit(Event(
                event_type=EventType.ARGUMENT_SUBMITTED,
                data={
                    "debate_id": self.debate_id,
                    "round_number": self.current_round.round_number,
                    "argument": argument,
                    "metrics": self.metrics_collector.get_system_summary()
                }
            ))
            
            logger.info(
                f"Added argument from {agent_id} - "
                f"Round: {self.current_round.round_number}, "
                f"Type: {argument_type}"
            )
            
        except Exception as e:
            logger.error(f"Failed to add argument: {str(e)}")
            self.metrics_collector.record_error(agent_id, str(type(e).__name__))
            raise

    async def end_round(self) -> DebateRoundMetrics:
        """End the current round and calculate metrics.
        
        Returns:
            Round metrics
            
        Raises:
            ValueError: If no active round
        """
        if not self.current_round:
            raise ValueError("No active round to end")
        
        try:
            self.current_round.end_time = datetime.now()
            self.current_round.status = "completed"
            
            # Calculate round duration
            duration = (
                self.current_round.end_time - self.current_round.start_time
            ).total_seconds()
            
            if not self.current_round.metrics:
                self.current_round.metrics = DebateRoundMetrics()
            
            self.current_round.metrics.round_duration = duration
            
            # Emit round completion event
            await self.event_emitter.emit(Event(
                event_type=EventType.ROUND_COMPLETED,
                data={
                    "debate_id": self.debate_id,
                    "round_number": self.current_round.round_number,
                    "metrics": self.current_round.metrics.dict(),
                    "status": "completed"
                }
            ))
            
            logger.info(
                f"Ended round {self.current_round.round_number} - "
                f"Duration: {duration:.2f}s"
            )
            
            metrics = self.current_round.metrics
            self.current_round = None
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to end round: {str(e)}")
            raise

    def get_round_history(self) -> List[DebateRound]:
        """Get debate round history.
        
        Returns:
            List of debate rounds
        """
        return self.rounds

    def get_evidence(self, evidence_id: str) -> Optional[Evidence]:
        """Get evidence by ID.
        
        Args:
            evidence_id: Evidence ID to find
            
        Returns:
            Evidence if found, None otherwise
        """
        for round in self.rounds:
            for evidence in round.evidence:
                if evidence.evidence_id == evidence_id:
                    return evidence
        return None

    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics.
        
        Returns:
            Current metrics summary
        """
        return self.metrics_collector.get_system_summary()
