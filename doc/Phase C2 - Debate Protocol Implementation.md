Phase C2: Debate Protocol Technical Specification

This specification details the implementation of the Debate Protocol component
in the CrewAI Content Marketing System, responsible for managing structured
debates between agent pairs.
"""

from typing import Dict, List, Optional, Union, Any, Callable
from pydantic import BaseModel, Field
from datetime import datetime
from loguru import logger
import asyncio
from enum import Enum
import uuid

# Data Models
class DebateStatus(str, Enum):
    """Status states for debates."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    CONSENSUS_REACHED = "consensus_reached"
    DEADLOCKED = "deadlocked"
    TERMINATED = "terminated"
    FAILED = "failed"

class ArgumentType(str, Enum):
    """Types of arguments in a debate."""
    PROPOSAL = "proposal"
    CHALLENGE = "challenge"
    DEFENSE = "defense"
    COUNTER = "counter"
    RESOLUTION = "resolution"

class Argument(BaseModel):
    """Model for debate arguments."""
    argument_id: str
    debate_id: str
    type: ArgumentType
    content: Dict[str, Any]
    agent_id: str
    timestamp: datetime
    references: List[str] = Field(default_factory=list)  # References to previous arguments
    evidence: List[Dict[str, Any]] = Field(default_factory=list)
    confidence_score: float
    impact_areas: List[str]

class ConsensusMetrics(BaseModel):
    """Metrics for evaluating debate consensus."""
    agreement_score: float
    resolution_quality: float
    evidence_strength: float
    implementation_feasibility: float
    risk_assessment: Dict[str, float]

class DebateRound(BaseModel):
    """Model for a single debate round."""
    round_id: str
    debate_id: str
    round_number: int
    arguments: List[Argument]
    consensus_metrics: Optional[ConsensusMetrics] = None
    started_at: datetime
    ended_at: Optional[datetime] = None
    status: str

class Debate(BaseModel):
    """Model for a complete debate."""
    debate_id: str
    topic: str
    description: str
    primary_agent_id: str
    adversary_agent_id: str
    status: DebateStatus
    rounds: List[DebateRound]
    current_round: int
    max_rounds: int
    consensus_threshold: float
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any] = Field(default_factory=dict)

# Core Protocol Implementation

```python
class DebateProtocol:
    """Core implementation of the debate protocol."""
    
    def __init__(
        self,
        knowledge_base: Any,
        max_rounds: int = 3,
        consensus_threshold: float = 0.8
    ):
        self.knowledge_base = knowledge_base
        self.max_rounds = max_rounds
        self.consensus_threshold = consensus_threshold
        self.debates: Dict[str, Debate] = {}
        self.consensus_evaluators: List[Callable] = []
        self._setup_default_evaluators()
    
    def _setup_default_evaluators(self):
        """Initialize default consensus evaluators."""
        self.consensus_evaluators.extend([
            self._evaluate_agreement_score,
            self._evaluate_evidence_strength,
            self._evaluate_implementation_feasibility
        ])
    
    async def create_debate(
        self,
        topic: str,
        description: str,
        primary_agent_id: str,
        adversary_agent_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Create a new debate session."""
        debate_id = str(uuid.uuid4())
        
        debate = Debate(
            debate_id=debate_id,
            topic=topic,
            description=description,
            primary_agent_id=primary_agent_id,
            adversary_agent_id=adversary_agent_id,
            status=DebateStatus.PENDING,
            rounds=[],
            current_round=0,
            max_rounds=self.max_rounds,
            consensus_threshold=self.consensus_threshold,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            metadata=metadata or {}
        )
        
        self.debates[debate_id] = debate
        return debate_id
    
    async def start_debate(self, debate_id: str) -> Debate:
        """Initialize and start a debate."""
        debate = self.debates.get(debate_id)
        if not debate:
            raise ValueError(f"Debate {debate_id} not found")
        
        try:
            debate.status = DebateStatus.IN_PROGRESS
            
            # Create initial round
            round_id = str(uuid.uuid4())
            initial_round = DebateRound(
                round_id=round_id,
                debate_id=debate_id,
                round_number=1,
                arguments=[],
                started_at=datetime.now(),
                status="active"
            )
            
            debate.rounds.append(initial_round)
            debate.current_round = 1
            debate.updated_at = datetime.now()
            
            return debate
            
        except Exception as e:
            logger.error(f"Failed to start debate {debate_id}: {str(e)}")
            debate.status = DebateStatus.FAILED
            raise
    
    async def submit_argument(
        self,
        debate_id: str,
        agent_id: str,
        argument_type: ArgumentType,
        content: Dict[str, Any],
        references: Optional[List[str]] = None,
        evidence: Optional[List[Dict[str, Any]]] = None
    ) -> Argument:
        """Submit a new argument in the debate."""
        debate = self.debates.get(debate_id)
        if not debate or debate.status != DebateStatus.IN_PROGRESS:
            raise ValueError(f"Invalid debate {debate_id}")
        
        current_round = debate.rounds[debate.current_round - 1]
        
        # Validate argument sequence
        self._validate_argument_sequence(
            current_round.arguments,
            argument_type,
            agent_id
        )
        
        # Create argument
        argument = Argument(
            argument_id=str(uuid.uuid4()),
            debate_id=debate_id,
            type=argument_type,
            content=content,
            agent_id=agent_id,
            timestamp=datetime.now(),
            references=references or [],
            evidence=evidence or [],
            confidence_score=self._calculate_confidence_score(content, evidence),
            impact_areas=self._identify_impact_areas(content)
        )
        
        current_round.arguments.append(argument)
        
        # Check for round completion
        if self._is_round_complete(current_round):
            await self._evaluate_round(debate, current_round)
        
        return argument
    
    async def _evaluate_round(
        self,
        debate: Debate,
        round: DebateRound
    ) -> ConsensusMetrics:
        """Evaluate a completed round for consensus."""
        try:
            # Calculate consensus metrics
            metrics = ConsensusMetrics(
                agreement_score=await self._evaluate_agreement_score(round),
                resolution_quality=await self._evaluate_resolution_quality(round),
                evidence_strength=await self._evaluate_evidence_strength(round),
                implementation_feasibility=await self._evaluate_implementation_feasibility(round),
                risk_assessment=await self._evaluate_risks(round)
            )
            
            round.consensus_metrics = metrics
            round.ended_at = datetime.now()
            
            # Check if consensus reached
            if metrics.agreement_score >= debate.consensus_threshold:
                debate.status = DebateStatus.CONSENSUS_REACHED
                return metrics
            
            # Check if max rounds reached
            if debate.current_round >= debate.max_rounds:
                debate.status = DebateStatus.DEADLOCKED
                return metrics
            
            # Create new round
            await self._create_new_round(debate)
            return metrics
            
        except Exception as e:
            logger.error(f"Round evaluation failed: {str(e)}")
            debate.status = DebateStatus.FAILED
            raise
    
    async def _create_new_round(self, debate: Debate):
        """Initialize a new debate round."""
        round_id = str(uuid.uuid4())
        new_round = DebateRound(
            round_id=round_id,
            debate_id=debate.debate_id,
            round_number=debate.current_round + 1,
            arguments=[],
            started_at=datetime.now(),
            status="active"
        )
        
        debate.rounds.append(new_round)
        debate.current_round += 1
        debate.updated_at = datetime.now()
    
    def _validate_argument_sequence(
        self,
        arguments: List[Argument],
        new_type: ArgumentType,
        agent_id: str
    ):
        """Validate the sequence of arguments."""
        if not arguments and new_type != ArgumentType.PROPOSAL:
            raise ValueError("First argument must be a proposal")
        
        if arguments:
            last_arg = arguments[-1]
            valid_sequences = {
                ArgumentType.PROPOSAL: [ArgumentType.CHALLENGE],
                ArgumentType.CHALLENGE: [ArgumentType.DEFENSE],
                ArgumentType.DEFENSE: [ArgumentType.COUNTER, ArgumentType.RESOLUTION],
                ArgumentType.COUNTER: [ArgumentType.RESOLUTION],
                ArgumentType.RESOLUTION: []
            }
            
            if new_type not in valid_sequences[last_arg.type]:
                raise ValueError(f"Invalid argument sequence: {last_arg.type} -> {new_type}")
            
            if last_arg.agent_id == agent_id:
                raise ValueError("Consecutive arguments must be from different agents")
    
    def _calculate_confidence_score(
        self,
        content: Dict[str, Any],
        evidence: List[Dict[str, Any]]
    ) -> float:
        """Calculate confidence score for an argument."""
        # Implement confidence scoring logic
        evidence_score = len(evidence) * 0.1  # Simple scoring for example
        content_score = 0.5  # Placeholder for content evaluation
        return min(1.0, evidence_score + content_score)
    
    def _identify_impact_areas(self, content: Dict[str, Any]) -> List[str]:
        """Identify areas impacted by the argument."""
        # Implement impact area identification logic
        return ["strategy", "implementation", "resources"]  # Example areas
    
    def _is_round_complete(self, round: DebateRound) -> bool:
        """Check if a round is complete."""
        if not round.arguments:
            return False
        
        last_arg = round.arguments[-1]
        return last_arg.type == ArgumentType.RESOLUTION
    
    # Consensus Evaluation Methods
    async def _evaluate_agreement_score(self, round: DebateRound) -> float:
        """Evaluate the level of agreement in the round."""
        # Implement agreement evaluation logic
        return 0.85  # Example score
    
    async def _evaluate_resolution_quality(self, round: DebateRound) -> float:
        """Evaluate the quality of the resolution."""
        # Implement resolution quality evaluation logic
        return 0.75  # Example score
    
    async def _evaluate_evidence_strength(self, round: DebateRound) -> float:
        """Evaluate the strength of evidence presented."""
        # Implement evidence evaluation logic
        return 0.90  # Example score
    
    async def _evaluate_implementation_feasibility(self, round: DebateRound) -> float:
        """Evaluate the feasibility of implementation."""
        # Implement feasibility evaluation logic
        return 0.80  # Example score
    
    async def _evaluate_risks(self, round: DebateRound) -> Dict[str, float]:
        """Evaluate risks identified in the debate."""
        # Implement risk evaluation logic
        return {
            "technical": 0.3,
            "resource": 0.4,
            "market": 0.2
        }
```

# Example Usage

```python
async def example_debate_session():
    """Example of using the debate protocol."""
    # Initialize knowledge base (placeholder)
    knowledge_base = object()
    
    # Create debate protocol instance
    protocol = DebateProtocol(knowledge_base)
    
    # Create a new debate
    debate_id = await protocol.create_debate(
        topic="Q4 Marketing Strategy",
        description="Determine the optimal marketing strategy for Q4",
        primary_agent_id="strategy_analyst_1",
        adversary_agent_id="market_skeptic_1",
        metadata={
            "department": "marketing",
            "priority": "high",
            "target_completion": "2024-01-15"
        }
    )
    
    # Start debate
    debate = await protocol.start_debate(debate_id)
    
    # Submit initial proposal
    proposal = await protocol.submit_argument(
        debate_id=debate_id,
        agent_id="strategy_analyst_1",
        argument_type=ArgumentType.PROPOSAL,
        content={
            "strategy": "Increase focus on content marketing",
            "budget": 100000,
            "timeline": "3 months",
            "expected_roi": 2.5
        },
        evidence=[
            {"type": "market_research", "data": {"source": "industry_report_2023"}},
            {"type": "historical_performance", "data": {"period": "Q1-Q3_2023"}}
        ]
    )
    
    # Submit challenge
    challenge = await protocol.submit_argument(
        debate_id=debate_id,
        agent_id="market_skeptic_1",
        argument_type=ArgumentType.CHALLENGE,
        content={
            "concern": "Market saturation",
            "risk_factors": ["competitive_pressure", "audience_fatigue"],
            "alternative_suggestion": "Hybrid approach with paid advertising"
        },
        references=[proposal.argument_id],
        evidence=[
            {"type": "competitor_analysis", "data": {"market_share": 0.45}},
            {"type": "audience_metrics", "data": {"engagement_trend": "declining"}}
        ]
    )
    
    return debate

if __name__ == "__main__":
    asyncio.run(example_debate_session())
```
