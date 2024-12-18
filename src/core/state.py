"""State management system."""
from typing import Dict, Any, Type, Optional
from enum import Enum
from loguru import logger

class StateTransitionError(Exception):
    """Error for invalid state transitions."""
    pass

class DebateStatus(str, Enum):
    """Debate status states."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    CONSENSUS_REACHED = "consensus_reached"
    FAILED = "failed"
    TERMINATED = "terminated"

class WorkflowStatus(str, Enum):
    """Workflow status states."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    TERMINATED = "terminated"

class TaskStatus(str, Enum):
    """Task status states."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    TERMINATED = "terminated"

class StateManager:
    """Manages system state transitions."""
    
    # Valid state transitions
    VALID_TRANSITIONS = {
        DebateStatus: {
            DebateStatus.PENDING: [DebateStatus.IN_PROGRESS, DebateStatus.FAILED],
            DebateStatus.IN_PROGRESS: [
                DebateStatus.CONSENSUS_REACHED,
                DebateStatus.FAILED,
                DebateStatus.TERMINATED
            ],
            DebateStatus.CONSENSUS_REACHED: [DebateStatus.TERMINATED],
            DebateStatus.FAILED: [DebateStatus.TERMINATED],
            DebateStatus.TERMINATED: []
        },
        WorkflowStatus: {
            WorkflowStatus.PENDING: [WorkflowStatus.IN_PROGRESS, WorkflowStatus.FAILED],
            WorkflowStatus.IN_PROGRESS: [
                WorkflowStatus.COMPLETED,
                WorkflowStatus.FAILED,
                WorkflowStatus.TERMINATED
            ],
            WorkflowStatus.COMPLETED: [WorkflowStatus.TERMINATED],
            WorkflowStatus.FAILED: [WorkflowStatus.TERMINATED],
            WorkflowStatus.TERMINATED: []
        },
        TaskStatus: {
            TaskStatus.PENDING: [TaskStatus.IN_PROGRESS, TaskStatus.FAILED],
            TaskStatus.IN_PROGRESS: [
                TaskStatus.COMPLETED,
                TaskStatus.FAILED,
                TaskStatus.TERMINATED
            ],
            TaskStatus.COMPLETED: [TaskStatus.TERMINATED],
            TaskStatus.FAILED: [TaskStatus.TERMINATED],
            TaskStatus.TERMINATED: []
        }
    }
    
    def __init__(self, event_emitter: Any):
        """Initialize state manager.
        
        Args:
            event_emitter: System event emitter
        """
        self.event_emitter = event_emitter
        self._states = {
            "workflow": {},  # workflow_id -> status
            "debate": {},    # debate_id -> status
            "task": {}       # task_id -> status
        }
    
    def _validate_transition(
        self,
        current_state: str,
        new_state: str,
        state_type: Type[Enum]
    ) -> None:
        """Validate state transition.
        
        Args:
            current_state: Current state
            new_state: New state
            state_type: Type of state (DebateStatus, WorkflowStatus, TaskStatus)
            
        Raises:
            StateTransitionError: If transition is invalid
        """
        if current_state == new_state:
            return
            
        current = state_type(current_state)
        new = state_type(new_state)
        
        valid_transitions = self.VALID_TRANSITIONS[state_type].get(current, [])
        if new not in valid_transitions:
            raise StateTransitionError(
                f"Invalid transition from {current_state} to {new_state}"
            )
    
    async def set_workflow_state(self, workflow_id: str, status: str) -> None:
        """Set workflow state.
        
        Args:
            workflow_id: Workflow ID
            status: New status
        """
        current_state = self._states["workflow"].get(workflow_id, WorkflowStatus.PENDING)
        self._validate_transition(current_state, status, WorkflowStatus)
        self._states["workflow"][workflow_id] = status
        logger.info(f"Workflow {workflow_id} state changed to {status}")
    
    async def set_debate_state(self, debate_id: str, status: str) -> None:
        """Set debate state.
        
        Args:
            debate_id: Debate ID
            status: New status
        """
        current_state = self._states["debate"].get(debate_id, DebateStatus.PENDING)
        self._validate_transition(current_state, status, DebateStatus)
        self._states["debate"][debate_id] = status
        logger.info(f"Debate {debate_id} state changed to {status}")
    
    async def set_task_state(self, task_id: str, status: str) -> None:
        """Set task state.
        
        Args:
            task_id: Task ID
            status: New status
        """
        current_state = self._states["task"].get(task_id, TaskStatus.PENDING)
        self._validate_transition(current_state, status, TaskStatus)
        self._states["task"][task_id] = status
        logger.info(f"Task {task_id} state changed to {status}")
    
    def get_workflow_state(self, workflow_id: str) -> Optional[str]:
        """Get workflow state.
        
        Args:
            workflow_id: Workflow ID
            
        Returns:
            Current workflow state if found, None otherwise
        """
        return self._states["workflow"].get(workflow_id)
    
    def get_debate_state(self, debate_id: str) -> Optional[str]:
        """Get debate state.
        
        Args:
            debate_id: Debate ID
            
        Returns:
            Current debate state if found, None otherwise
        """
        return self._states["debate"].get(debate_id)
    
    def get_task_state(self, task_id: str) -> Optional[str]:
        """Get task state.
        
        Args:
            task_id: Task ID
            
        Returns:
            Current task state if found, None otherwise
        """
        return self._states["task"].get(task_id)
    
    def clear_states(self) -> None:
        """Clear all states."""
        self._states = {
            "workflow": {},
            "debate": {},
            "task": {}
        }
