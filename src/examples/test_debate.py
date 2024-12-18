"""Example script to test the debate system functionality.

This script demonstrates how to:
1. Initialize the system
2. Start a debate with a sample topic
3. Monitor events and state changes
4. Submit feedback
5. View results

Run this script to verify your setup:
python src/examples/test_debate.py
"""
import asyncio
import json
from datetime import datetime
from typing import Dict, Any, List

from src.core import EventEmitter, StateManager, Event, EventType
from src.agents import DebateOrchestrator

async def handle_event(event: Event) -> None:
    """Print events in a readable format.
    
    Args:
        event: Event to display
    """
    print(f"\n=== {event.event_type} ===")
    print(f"Timestamp: {event.timestamp.strftime('%H:%M:%S')}")
    if event.agent_id:
        print(f"Agent: {event.agent_id}")
    print("Data:")
    print(json.dumps(event.data, indent=2))
    print("=" * 40)

async def main():
    """Run a sample debate."""
    print("\n🤖 Starting Debate System Test\n")
    
    # Initialize core components
    event_emitter = EventEmitter()
    state_manager = StateManager(event_emitter)
    orchestrator = DebateOrchestrator(event_emitter, state_manager)
    
    # Register event handler
    for event_type in EventType:
        event_emitter.add_handler(event_type, handle_event)
    
    try:
        # Sample topic and context
        topic = "Market Entry Strategy"
        context = {
            "market_size": 1000,
            "growth_rate": 15,
            "competition_level": "Medium",
            "target_segment": ["B2B", "Enterprise"],
            "additional_context": """
            We're considering entering the AI-powered analytics market.
            Our target customers are medium to large enterprises.
            Key competitors include established analytics firms.
            We have unique ML capabilities and domain expertise.
            """
        }
        
        print(f"Topic: {topic}")
        print("\nContext:")
        print(json.dumps(context, indent=2))
        print("\nInitializing debate...")
        
        # Initialize and start debate
        debate_id = await orchestrator.initialize_debate(topic, context)
        print(f"\nDebate ID: {debate_id}")
        
        print("\nStarting debate...")
        results = await orchestrator.start_debate()
        
        print("\n📊 Debate Results:")
        print("\n1. Initial Analysis:")
        print(json.dumps(results["initial_analysis"], indent=2))
        
        print("\n2. Skeptic's Challenge:")
        print(json.dumps(results["challenge"], indent=2))
        
        print("\n3. Final Analysis:")
        print(json.dumps(results["final_analysis"], indent=2))
        
        # Submit some feedback
        print("\n✍️ Submitting feedback...")
        await orchestrator.add_feedback(
            "initial",
            "The initial analysis covers key market aspects but could consider technological trends more.",
            quality_score=4
        )
        
        await orchestrator.add_feedback(
            "challenge",
            "Valid concerns about competition, but perhaps underestimates our technical advantages.",
            quality_score=4
        )
        
        await orchestrator.add_feedback(
            "final",
            "Good synthesis of initial analysis and challenges. Clear action items.",
            quality_score=5
        )
        
        # Show feedback history
        print("\n📝 Feedback History:")
        feedback_history = orchestrator.get_feedback_history()
        for entry in feedback_history:
            print(f"\nStage: {entry['stage']}")
            print(f"Score: {entry['quality_score']}")
            print(f"Feedback: {entry['feedback']}")
        
        # Stop debate
        print("\nStopping debate...")
        await orchestrator.stop_debate()
        
        print("\n✅ Test completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Error during test: {str(e)}")
        raise
    finally:
        # Cleanup
        await event_emitter.stop_processing()

if __name__ == "__main__":
    asyncio.run(main())
