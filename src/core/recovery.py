"""Enhanced error handling and recovery system."""
import asyncio
from typing import Dict, Any, Optional, Callable, Awaitable, List, Type
from datetime import datetime
import traceback
from enum import Enum
import json
from pathlib import Path
import logging
from functools import wraps
from loguru import logger
import uuid

class RecoveryLevel(str, Enum):
    """Recovery action levels."""
    RETRY = "retry"  # Simple retry
    ROLLBACK = "rollback"  # Rollback to previous state
    CHECKPOINT = "checkpoint"  # Restore from checkpoint
    TERMINATE = "terminate"  # Graceful termination
    EMERGENCY = "emergency"  # Emergency shutdown

class ErrorCategory(str, Enum):
    """Categories of errors for appropriate handling."""
    TRANSIENT = "transient"  # Temporary failures (network, etc.)
    STATE = "state"  # State-related errors
    RESOURCE = "resource"  # Resource availability issues
    VALIDATION = "validation"  # Data validation errors
    AGENT = "agent"  # Agent-specific errors
    SYSTEM = "system"  # System-level errors
    UNKNOWN = "unknown"  # Uncategorized errors

class RecoveryAction:
    """Defines a recovery action for an error."""
    def __init__(
        self,
        level: RecoveryLevel,
        max_retries: int = 3,
        delay: float = 1.0,
        cleanup_func: Optional[Callable] = None
    ):
        """Initialize recovery action.
        
        Args:
            level: Recovery level to apply
            max_retries: Maximum retry attempts
            delay: Delay between retries in seconds
            cleanup_func: Optional cleanup function
        """
        self.level = level
        self.max_retries = max_retries
        self.delay = delay
        self.cleanup_func = cleanup_func

class SystemState:
    """Captures system state for recovery."""
    def __init__(
        self,
        workflow_states: Dict[str, str],
        debate_states: Dict[str, str],
        task_states: Dict[str, str],
        resources: Dict[str, Any]
    ):
        """Initialize system state.
        
        Args:
            workflow_states: Current workflow states
            debate_states: Current debate states
            task_states: Current task states
            resources: Current resource states
        """
        self.workflow_states = workflow_states
        self.debate_states = debate_states
        self.task_states = task_states
        self.resources = resources
        self.timestamp = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Convert state to dictionary.
        
        Returns:
            State as dictionary
        """
        return {
            "workflow_states": self.workflow_states,
            "debate_states": self.debate_states,
            "task_states": self.task_states,
            "resources": self.resources,
            "timestamp": self.timestamp.isoformat()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SystemState':
        """Create state from dictionary.
        
        Args:
            data: State dictionary
            
        Returns:
            SystemState instance
        """
        return cls(
            workflow_states=data["workflow_states"],
            debate_states=data["debate_states"],
            task_states=data["task_states"],
            resources=data["resources"]
        )

class RecoveryManager:
    """Manages system recovery and error handling."""
    
    def __init__(
        self,
        checkpoint_dir: str = "checkpoints",
        log_dir: str = "logs"
    ):
        """Initialize recovery manager.
        
        Args:
            checkpoint_dir: Directory for checkpoints
            log_dir: Directory for logs
        """
        self.checkpoint_dir = Path(checkpoint_dir)
        self.log_dir = Path(log_dir)
        self.checkpoint_dir.mkdir(exist_ok=True)
        self.log_dir.mkdir(exist_ok=True)
        
        # Configure logging
        self.setup_logging()
        
        # Recovery actions for error categories
        self.recovery_actions: Dict[ErrorCategory, RecoveryAction] = {
            ErrorCategory.TRANSIENT: RecoveryAction(
                RecoveryLevel.RETRY,
                max_retries=3,
                delay=1.0
            ),
            ErrorCategory.STATE: RecoveryAction(
                RecoveryLevel.ROLLBACK,
                max_retries=1,
                delay=0.0
            ),
            ErrorCategory.RESOURCE: RecoveryAction(
                RecoveryLevel.CHECKPOINT,
                max_retries=2,
                delay=2.0
            ),
            ErrorCategory.VALIDATION: RecoveryAction(
                RecoveryLevel.TERMINATE,
                max_retries=0,
                delay=0.0
            ),
            ErrorCategory.AGENT: RecoveryAction(
                RecoveryLevel.RETRY,
                max_retries=2,
                delay=1.0
            ),
            ErrorCategory.SYSTEM: RecoveryAction(
                RecoveryLevel.EMERGENCY,
                max_retries=0,
                delay=0.0
            )
        }
        
        # Track recovery attempts
        self.recovery_attempts: Dict[str, int] = {}

    def setup_logging(self) -> None:
        """Configure logging system."""
        # Configure loguru logger
        logger.add(
            self.log_dir / "system.log",
            rotation="1 day",
            retention="30 days",
            level="INFO"
        )
        logger.add(
            self.log_dir / "error.log",
            rotation="1 day",
            retention="30 days",
            level="ERROR"
        )

    def categorize_error(self, error: Exception) -> ErrorCategory:
        """Categorize an error for appropriate handling.
        
        Args:
            error: Exception to categorize
            
        Returns:
            Error category
        """
        error_type = type(error).__name__
        
        # Map error types to categories
        category_mapping = {
            "ConnectionError": ErrorCategory.TRANSIENT,
            "TimeoutError": ErrorCategory.TRANSIENT,
            "StateTransitionError": ErrorCategory.STATE,
            "ResourceError": ErrorCategory.RESOURCE,
            "ValidationError": ErrorCategory.VALIDATION,
            "AgentError": ErrorCategory.AGENT,
            "SystemError": ErrorCategory.SYSTEM
        }
        
        return category_mapping.get(error_type, ErrorCategory.UNKNOWN)

    async def handle_error(
        self,
        error: Exception,
        context: Dict[str, Any]
    ) -> None:
        """Handle an error with appropriate recovery action.
        
        Args:
            error: Exception to handle
            context: Error context
        """
        # Log error
        logger.error(
            f"Error occurred: {str(error)}\nContext: {context}\n"
            f"Traceback: {traceback.format_exc()}"
        )
        
        # Categorize error
        category = self.categorize_error(error)
        action = self.recovery_actions[category]
        
        # Get error ID for tracking
        error_id = context.get("error_id", str(uuid.uuid4()))
        
        # Check retry attempts
        attempts = self.recovery_attempts.get(error_id, 0)
        if attempts >= action.max_retries:
            logger.error(f"Max retries ({action.max_retries}) exceeded for {error_id}")
            raise error
        
        # Increment attempts
        self.recovery_attempts[error_id] = attempts + 1
        
        # Execute recovery action
        await self.execute_recovery(action, context)

    async def execute_recovery(
        self,
        action: RecoveryAction,
        context: Dict[str, Any]
    ) -> None:
        """Execute a recovery action.
        
        Args:
            action: Recovery action to execute
            context: Recovery context
        """
        logger.info(f"Executing recovery action: {action.level}")
        
        if action.level == RecoveryLevel.RETRY:
            await asyncio.sleep(action.delay)
            # Retry will be handled by caller
            
        elif action.level == RecoveryLevel.ROLLBACK:
            await self.rollback_state(context)
            
        elif action.level == RecoveryLevel.CHECKPOINT:
            await self.restore_checkpoint(context)
            
        elif action.level == RecoveryLevel.TERMINATE:
            await self.terminate_gracefully(context)
            
        elif action.level == RecoveryLevel.EMERGENCY:
            await self.emergency_shutdown(context)

    async def create_checkpoint(
        self,
        state: SystemState,
        checkpoint_id: Optional[str] = None
    ) -> str:
        """Create a system state checkpoint.
        
        Args:
            state: System state to checkpoint
            checkpoint_id: Optional checkpoint ID
            
        Returns:
            Checkpoint ID
        """
        checkpoint_id = checkpoint_id or str(uuid.uuid4())
        checkpoint_path = self.checkpoint_dir / f"{checkpoint_id}.json"
        
        # Save checkpoint
        with open(checkpoint_path, 'w') as f:
            json.dump(state.to_dict(), f)
        
        logger.info(f"Created checkpoint: {checkpoint_id}")
        return checkpoint_id

    async def restore_checkpoint(
        self,
        context: Dict[str, Any]
    ) -> SystemState:
        """Restore system state from checkpoint.
        
        Args:
            context: Recovery context
            
        Returns:
            Restored system state
            
        Raises:
            FileNotFoundError: If checkpoint not found
        """
        checkpoint_id = context.get("checkpoint_id")
        if not checkpoint_id:
            raise ValueError("No checkpoint ID provided")
            
        checkpoint_path = self.checkpoint_dir / f"{checkpoint_id}.json"
        
        # Load checkpoint
        with open(checkpoint_path, 'r') as f:
            state_dict = json.load(f)
        
        state = SystemState.from_dict(state_dict)
        logger.info(f"Restored checkpoint: {checkpoint_id}")
        return state

    async def rollback_state(self, context: Dict[str, Any]) -> None:
        """Rollback system to previous state.
        
        Args:
            context: Recovery context
        """
        logger.info("Rolling back system state")
        # Implementation depends on state management system
        pass

    async def terminate_gracefully(self, context: Dict[str, Any]) -> None:
        """Perform graceful system termination.
        
        Args:
            context: Recovery context
        """
        logger.warning("Initiating graceful termination")
        # Cleanup and shutdown
        if context.get("cleanup_func"):
            await context["cleanup_func"]()

    async def emergency_shutdown(self, context: Dict[str, Any]) -> None:
        """Perform emergency system shutdown.
        
        Args:
            context: Recovery context
        """
        logger.critical("Initiating emergency shutdown")
        # Emergency cleanup and shutdown
        if context.get("cleanup_func"):
            await context["cleanup_func"]()

def with_recovery(error_context: Dict[str, Any] = None):
    """Decorator for functions that need error recovery.
    
    Args:
        error_context: Additional context for error handling
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get recovery manager instance
            recovery_manager = args[0].recovery_manager if hasattr(args[0], 'recovery_manager') else None
            if not recovery_manager:
                raise ValueError("No recovery manager available")
            
            context = {
                "function": func.__name__,
                "args": args,
                "kwargs": kwargs,
                **(error_context or {})
            }
            
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                await recovery_manager.handle_error(e, context)
                # Re-raise if recovery failed
                raise
        return wrapper
    return decorator
