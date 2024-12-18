"""Orchestrator agent implementation with enhanced recovery and logging."""
from typing import Dict, Any, Optional, List
from datetime import datetime
import uuid
from loguru import logger

from src.core import (
    Event,
    EventType,
    EventEmitter,
    StateManager,
    DebateStatus
)
from src.core.recovery import (
    RecoveryManager,
    SystemState,
    with_recovery,
    ErrorCategory
)
from .strategy_analyst import StrategyAnalyst
from .strategy_skeptic import MarketSkeptic
from .adapters import (
    StrategyAnalystAdapter,
    MarketSkepticAdapter,
    DebateSessionManager
)
from .metrics import AgentMetricsCollector

class DebateOrchestrator:
    """Orchestrates debates with enhanced recovery and monitoring."""
    
    def __init__(
        self,
        event_emitter: EventEmitter,
        state_manager: StateManager,
        checkpoint_dir: str = "checkpoints",
        log_dir: str = "logs"
    ):
        """Initialize orchestrator.
        
        Args:
            event_emitter: System event emitter
            state_manager: System state manager
            checkpoint_dir: Directory for checkpoints
            log_dir: Directory for logs
        """
        self.event_emitter = event_emitter
        self.state_manager = state_manager
        
        # Initialize recovery and monitoring
        self.recovery_manager = RecoveryManager(checkpoint_dir, log_dir)
        self.metrics_collector = AgentMetricsCollector()
        
        # Debate state
        self.current_session: Optional[DebateSessionManager] = None
        self.debate_id: Optional[str] = None
        self.topic: Optional[str] = None
        self.context: Dict[str, Any] = {}
        self.feedback_history: List[Dict[str, Any]] = []
        
        logger.info("Orchestrator initialized")

    async def _create_checkpoint(self) -> str:
        """Create system state checkpoint.
        
        Returns:
            Checkpoint ID
        """
        current_state = SystemState(
            workflow_states=self.state_manager._states["workflow"],
            debate_states=self.state_manager._states["debate"],
            task_states=self.state_manager._states["task"],
            resources=self.metrics_collector.get_system_summary()
        )
        
        checkpoint_id = await self.recovery_manager.create_checkpoint(current_state)
        logger.info(f"Created checkpoint: {checkpoint_id}")
        return checkpoint_id

    async def _restore_checkpoint(self, checkpoint_id: str) -> None:
        """Restore system from checkpoint.
        
        Args:
            checkpoint_id: Checkpoint to restore
        """
        state = await self.recovery_manager.restore_checkpoint({
            "checkpoint_id": checkpoint_id
        })
        
        # Restore states
        for workflow_id, status in state.workflow_states.items():
            await self.state_manager.set_workflow_state(workflow_id, status)
        
        for debate_id, status in state.debate_states.items():
            await self.state_manager.set_debate_state(debate_id, status)
        
        for task_id, status in state.task_states.items():
            await self.state_manager.set_task_state(task_id, status)
        
        logger.info(f"Restored from checkpoint: {checkpoint_id}")

    @with_recovery({"component": "orchestrator", "operation": "initialize_debate"})
    async def initialize_debate(
        self,
        topic: str,
        context: Dict[str, Any]
    ) -> str:
        """Initialize a new debate session.
        
        Args:
            topic: Debate topic
            context: Market context information
            
        Returns:
            Debate ID
        """
        try:
            logger.info(f"Initializing debate - Topic: {topic}")
            
            # Create checkpoint before initialization
            checkpoint_id = await self._create_checkpoint()
            
            # Store topic and context
            self.topic = topic
            self.context = context
            
            # Create debate ID
            self.debate_id = str(uuid.uuid4())
            
            # Create agents
            analyst = StrategyAnalyst(None)  # No knowledge base for MVP
            skeptic = MarketSkeptic(None)
            
            # Create adapters
            analyst_adapter = StrategyAnalystAdapter(
                analyst,
                self.event_emitter,
                self.state_manager,
                self.debate_id
            )
            
            skeptic_adapter = MarketSkepticAdapter(
                skeptic,
                self.event_emitter,
                self.state_manager,
                self.debate_id
            )
            
            # Create debate session
            self.current_session = DebateSessionManager(
                analyst_adapter,
                skeptic_adapter,
                self.event_emitter,
                self.state_manager
            )
            
            # Initialize metrics tracking
            self.metrics_collector.get_or_create_metrics(analyst_adapter.agent_id)
            self.metrics_collector.get_or_create_metrics(skeptic_adapter.agent_id)
            
            logger.info(f"Debate initialized successfully - ID: {self.debate_id}")
            return self.debate_id
            
        except Exception as e:
            logger.error(f"Failed to initialize debate: {str(e)}")
            # Restore from checkpoint on failure
            await self._restore_checkpoint(checkpoint_id)
            raise

    @with_recovery({"component": "orchestrator", "operation": "start_debate"})
    async def start_debate(self) -> Dict[str, Any]:
        """Start the debate session.
        
        Returns:
            Debate results
            
        Raises:
            ValueError: If debate not initialized
        """
        if not self.current_session or not self.debate_id:
            raise ValueError("Debate not initialized")
        
        try:
            logger.info(f"Starting debate - ID: {self.debate_id}")
            
            # Create checkpoint before starting
            checkpoint_id = await self._create_checkpoint()
            
            start_time = datetime.now()
            
            # Prepare market data
            market_data = {
                "topic": self.topic,
                "market_size": self.context.get("market_size", 0),
                "growth_rate": self.context.get("growth_rate", 0),
                "competition_level": self.context.get("competition_level", "Medium"),
                "target_segments": self.context.get("target_segment", []),
                "additional_context": self.context.get("additional_context", ""),
                "timestamp": datetime.now().isoformat()
            }
            
            # Conduct debate
            results = await self.current_session.conduct_debate(market_data)
            
            # Record metrics
            duration = (datetime.now() - start_time).total_seconds()
            for agent_id in [
                self.current_session.analyst.agent_id,
                self.current_session.skeptic.agent_id
            ]:
                self.metrics_collector.record_task(
                    agent_id,
                    "debate",
                    duration,
                    True
                )
            
            # Add topic and context to results
            results.update({
                "topic": self.topic,
                "context": self.context,
                "metrics": self.metrics_collector.get_system_summary()
            })
            
            logger.info(f"Debate completed successfully - ID: {self.debate_id}")
            return results
            
        except Exception as e:
            logger.error(f"Failed to conduct debate: {str(e)}")
            # Record error metrics
            for agent_id in [
                self.current_session.analyst.agent_id,
                self.current_session.skeptic.agent_id
            ]:
                self.metrics_collector.record_error(agent_id, str(type(e).__name__))
            # Restore from checkpoint on failure
            await self._restore_checkpoint(checkpoint_id)
            raise

    @with_recovery({"component": "orchestrator", "operation": "add_feedback"})
    async def add_feedback(
        self,
        stage: str,
        feedback: str,
        quality_score: Optional[int] = None
    ) -> None:
        """Add human feedback for a debate stage.
        
        Args:
            stage: Debate stage (initial, challenge, final)
            feedback: Human feedback text
            quality_score: Optional quality rating (1-5)
        """
        if not self.debate_id:
            raise ValueError("No active debate")
        
        try:
            logger.info(f"Adding feedback - Stage: {stage}, Debate ID: {self.debate_id}")
            
            feedback_entry = {
                "debate_id": self.debate_id,
                "stage": stage,
                "feedback": feedback,
                "quality_score": quality_score,
                "timestamp": datetime.now().isoformat()
            }
            
            self.feedback_history.append(feedback_entry)
            
            # Emit feedback event
            await self.event_emitter.emit(Event(
                event_type=EventType.ARGUMENT_SUBMITTED,
                agent_id="human",
                data={
                    "debate_id": self.debate_id,
                    "type": "feedback",
                    "content": feedback_entry
                }
            ))
            
            logger.info(f"Feedback added successfully - Stage: {stage}")
            
        except Exception as e:
            logger.error(f"Failed to add feedback: {str(e)}")
            raise

    @with_recovery({"component": "orchestrator", "operation": "stop_debate"})
    async def stop_debate(self) -> None:
        """Stop the current debate session."""
        if self.debate_id:
            try:
                logger.info(f"Stopping debate - ID: {self.debate_id}")
                
                # Create checkpoint before stopping
                checkpoint_id = await self._create_checkpoint()
                
                await self.state_manager.set_debate_state(
                    self.debate_id,
                    DebateStatus.TERMINATED
                )
                
                # Clear current session
                self.current_session = None
                self.debate_id = None
                self.topic = None
                self.context = {}
                
                logger.info("Debate stopped successfully")
                
            except Exception as e:
                logger.error(f"Failed to stop debate: {str(e)}")
                # Restore from checkpoint on failure
                await self._restore_checkpoint(checkpoint_id)
                raise

    def get_feedback_history(self) -> List[Dict[str, Any]]:
        """Get the feedback history for all debates.
        
        Returns:
            List of feedback entries
        """
        return self.feedback_history

    def get_current_debate_feedback(self) -> List[Dict[str, Any]]:
        """Get feedback for the current debate.
        
        Returns:
            List of feedback entries for current debate
            
        Raises:
            ValueError: If no active debate
        """
        if not self.debate_id:
            raise ValueError("No active debate")
            
        return [
            entry for entry in self.feedback_history
            if entry["debate_id"] == self.debate_id
        ]

    def get_metrics(self) -> Dict[str, Any]:
        """Get current system metrics.
        
        Returns:
            Current metrics
        """
        return self.metrics_collector.get_system_summary()
