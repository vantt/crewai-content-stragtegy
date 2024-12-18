"""Tests for the event system implementation."""
import pytest
import asyncio
from datetime import datetime
from typing import List

from src.core.events import EventType, Event, EventEmitter

@pytest.fixture
async def event_emitter():
    """Fixture providing an event emitter instance."""
    emitter = EventEmitter()
    async with emitter:
        yield emitter

@pytest.mark.asyncio
async def test_event_creation():
    """Test event creation with default and custom values."""
    # Test with minimal required fields
    event = Event(event_type=EventType.DEBATE_STARTED)
    assert event.event_id is not None
    assert event.timestamp is not None
    assert event.data == {}
    
    # Test with all fields
    custom_data = {"key": "value"}
    event = Event(
        event_type=EventType.ARGUMENT_SUBMITTED,
        workflow_id="workflow123",
        step_id="step456",
        agent_id="agent789",
        data=custom_data
    )
    assert event.workflow_id == "workflow123"
    assert event.step_id == "step456"
    assert event.agent_id == "agent789"
    assert event.data == custom_data

@pytest.mark.asyncio
async def test_event_handler_registration(event_emitter: EventEmitter):
    """Test adding and removing event handlers."""
    events_received: List[Event] = []
    
    async def test_handler(event: Event):
        events_received.append(event)
    
    # Add handler
    event_emitter.add_handler(EventType.DEBATE_STARTED, test_handler)
    
    # Emit event
    test_event = Event(event_type=EventType.DEBATE_STARTED)
    await event_emitter.emit(test_event)
    
    # Wait for event processing
    await asyncio.sleep(0.1)
    
    assert len(events_received) == 1
    assert events_received[0].event_type == EventType.DEBATE_STARTED
    
    # Remove handler
    event_emitter.remove_handler(EventType.DEBATE_STARTED, test_handler)
    
    # Emit another event
    await event_emitter.emit(test_event)
    await asyncio.sleep(0.1)
    
    # Should still be only one event
    assert len(events_received) == 1

@pytest.mark.asyncio
async def test_multiple_handlers(event_emitter: EventEmitter):
    """Test multiple handlers for the same event type."""
    events_received_1: List[Event] = []
    events_received_2: List[Event] = []
    
    async def handler_1(event: Event):
        events_received_1.append(event)
    
    async def handler_2(event: Event):
        events_received_2.append(event)
    
    # Add both handlers
    event_emitter.add_handler(EventType.DEBATE_STARTED, handler_1)
    event_emitter.add_handler(EventType.DEBATE_STARTED, handler_2)
    
    # Emit event
    test_event = Event(event_type=EventType.DEBATE_STARTED)
    await event_emitter.emit(test_event)
    
    # Wait for event processing
    await asyncio.sleep(0.1)
    
    assert len(events_received_1) == 1
    assert len(events_received_2) == 1

@pytest.mark.asyncio
async def test_event_queue_processing(event_emitter: EventEmitter):
    """Test events are processed in order."""
    processed_events: List[Event] = []
    
    async def test_handler(event: Event):
        processed_events.append(event)
        await asyncio.sleep(0.1)  # Simulate some processing time
    
    event_emitter.add_handler(EventType.DEBATE_STARTED, test_handler)
    
    # Emit multiple events
    events = [
        Event(event_type=EventType.DEBATE_STARTED, data={"order": i})
        for i in range(3)
    ]
    
    for event in events:
        await event_emitter.emit(event)
    
    # Wait for processing
    await asyncio.sleep(0.5)
    
    assert len(processed_events) == 3
    for i, event in enumerate(processed_events):
        assert event.data["order"] == i

@pytest.mark.asyncio
async def test_error_handling(event_emitter: EventEmitter):
    """Test error handling in event processing."""
    events_processed: List[Event] = []
    
    async def failing_handler(event: Event):
        raise Exception("Test error")
    
    async def working_handler(event: Event):
        events_processed.append(event)
    
    # Add both handlers
    event_emitter.add_handler(EventType.DEBATE_STARTED, failing_handler)
    event_emitter.add_handler(EventType.DEBATE_STARTED, working_handler)
    
    # Emit event
    test_event = Event(event_type=EventType.DEBATE_STARTED)
    await event_emitter.emit(test_event)
    
    # Wait for processing
    await asyncio.sleep(0.1)
    
    # Working handler should still process event
    assert len(events_processed) == 1
