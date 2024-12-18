"""Event system implementation for the DebateProtocol.

This module implements the core event system used by the DebateProtocol to handle
asynchronous communication between components.
"""
from enum import Enum
from typing import Dict, List, Callable, Awaitable, Any, Optional
from datetime import datetime
from collections import defaultdict
import asyncio
import uuid
from pydantic import BaseModel, Field

class EventType(str, Enum):
    """Types of events that can be emitted in the system."""
    # Workflow events
    WORKFLOW_STARTED = "workflow_started"
    WORKFLOW_COMPLETED = "workflow_completed"
    WORKFLOW_FAILED = "workflow_failed"
    
    # Step events
    STEP_STARTED = "step_started"
    STEP_COMPLETED = "step_completed"
    STEP_FAILED = "step_failed"
    
    # Agent events
    AGENT_TASK_STARTED = "agent_task_started"
    AGENT_TASK_COMPLETED = "agent_task_completed"
    AGENT_TASK_FAILED = "agent_task_failed"
    
    # Debate events
    DEBATE_STARTED = "debate_started"
    ARGUMENT_SUBMITTED = "argument_submitted"
    EVIDENCE_PRESENTED = "evidence_presented"
    ROUND_COMPLETED = "round_completed"
    CONSENSUS_REACHED = "consensus_reached"
    DEBATE_ENDED = "debate_ended"

class Event(BaseModel):
    """Model representing a system event."""
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_type: EventType
    workflow_id: Optional[str] = None
    step_id: Optional[str] = None
    agent_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)
    data: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        """Pydantic model configuration."""
        arbitrary_types_allowed = True

# Type alias for event handlers
EventHandler = Callable[[Event], Awaitable[None]]

class EventEmitter:
    """Event emitter for handling system events.
    
    This class manages event emission and handling throughout the system.
    It supports asynchronous event handling and maintains an event queue
    for processing events in order.
    """
    
    def __init__(self):
        """Initialize the event emitter."""
        # Dictionary mapping event types to their handlers
        self.handlers: Dict[EventType, List[EventHandler]] = defaultdict(list)
        # Queue for processing events in order
        self.event_queue: asyncio.Queue[Event] = asyncio.Queue()
        # Flag to control event processing
        self._processing: bool = False
        # Task for the event processor
        self._processor_task: Optional[asyncio.Task] = None

    def add_handler(self, event_type: EventType, handler: EventHandler) -> None:
        """Register a new event handler.
        
        Args:
            event_type: Type of event to handle
            handler: Async function to handle the event
        """
        self.handlers[event_type].append(handler)

    def remove_handler(self, event_type: EventType, handler: EventHandler) -> None:
        """Remove an event handler.
        
        Args:
            event_type: Type of event the handler was registered for
            handler: Handler to remove
        """
        if event_type in self.handlers:
            self.handlers[event_type] = [h for h in self.handlers[event_type] if h != handler]

    async def emit(self, event: Event) -> None:
        """Emit an event to all registered handlers.
        
        Args:
            event: Event to emit
        """
        await self.event_queue.put(event)
        
        # Start processing if not already started
        if not self._processing:
            await self.start_processing()

    async def start_processing(self) -> None:
        """Start processing events from the queue."""
        if self._processing:
            return

        self._processing = True
        self._processor_task = asyncio.create_task(self._process_events())

    async def stop_processing(self) -> None:
        """Stop processing events."""
        self._processing = False
        if self._processor_task:
            await self._processor_task

    async def _process_events(self) -> None:
        """Process events from the queue."""
        while self._processing:
            try:
                # Get next event with timeout
                try:
                    event = await asyncio.wait_for(self.event_queue.get(), timeout=1.0)
                except asyncio.TimeoutError:
                    continue

                # Process event
                handlers = self.handlers[event.event_type]
                await asyncio.gather(
                    *(handler(event) for handler in handlers),
                    return_exceptions=True
                )

                # Mark task as done
                self.event_queue.task_done()

            except Exception as e:
                # Log error but continue processing
                print(f"Error processing event: {str(e)}")
                continue

    async def __aenter__(self) -> 'EventEmitter':
        """Async context manager entry."""
        await self.start_processing()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.stop_processing()
