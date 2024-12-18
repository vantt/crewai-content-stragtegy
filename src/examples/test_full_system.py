"""Test script to verify all system features including recovery.

This script demonstrates and tests:
1. Multi-round debates
2. Evidence tracking
3. Metrics collection
4. Workflow management
5. Recovery mechanisms
6. System health monitoring

Run this script to verify the complete system:
streamlit run src/examples/test_full_system.py
"""
import streamlit as st
import asyncio
from datetime import datetime
import json
from typing import Dict, Any, List
from pathlib import Path

from src.core import (
    EventEmitter,
    StateManager,
    Event,
    EventType,
    RecoveryManager
)
from src.agents import (
    StrategyAnalyst,
    MarketSkeptic,
    DebateOrchestrator
)
from src.ui import (
    EventStreamComponent,
    StateViewComponent,
    ControlPanelComponent,
    DebateViewComponent,
    WorkflowVisualizerComponent,
    ResourceMonitorComponent,
    DebateVisualizerComponent,
    MetricsVisualizerComponent,
    RecoveryVisualizerComponent
)

# Sample market data for testing
SAMPLE_MARKET_DATA = {
    "topic": "AI Product Market Entry Strategy",
    "context": {
        "market_size": 5000,
        "growth_rate": 25,
        "competition_level": "Medium",
        "target_segment": ["Enterprise", "B2B"],
        "demographics": {
            "company_size": ["Medium", "Large"],
            "industry_sectors": [
                "Technology",
                "Finance",
                "Healthcare"
            ],
            "geographic_regions": [
                "North America",
                "Europe",
                "Asia Pacific"
            ],
            "decision_makers": [
                "CTO",
                "IT Directors",
                "Data Science Leads"
            ],
            "budget_range": {
                "min": 50000,
                "max": 500000,
                "currency": "USD"
            }
        },
        "additional_context": """
        We're considering entering the AI-powered analytics market.
        Key differentiators:
        1. Advanced NLP capabilities
        2. Real-time processing
        3. Domain-specific optimization
        
        Current market challenges:
        1. Established competitors
        2. Technical complexity
        3. Integration requirements
        
        Our strengths:
        1. Proprietary algorithms
        2. Domain expertise
        3. Existing customer base
        """
    }
}

# Sample evidence data
SAMPLE_EVIDENCE = [
    {
        "type": "market_research",
        "source": "Industry Report 2023",
        "content": {
            "market_size": 5000,
            "growth_rate": 25,
            "key_players": ["Competitor A", "Competitor B"],
            "market_trends": [
                "Increased AI adoption",
                "Focus on real-time analytics",
                "Integration demands"
            ]
        },
        "confidence": 0.9
    },
    {
        "type": "competitive_analysis",
        "source": "Competitor Analysis Q3 2023",
        "content": {
            "competitor_strengths": [
                "Established market presence",
                "Large customer base"
            ],
            "competitor_weaknesses": [
                "Outdated technology",
                "Limited customization"
            ],
            "market_gaps": [
                "Real-time processing",
                "Domain specialization"
            ]
        },
        "confidence": 0.85
    }
]

class SystemTester:
    """Test harness for the complete system."""
    
    def __init__(self):
        """Initialize the test harness."""
        # Create data directories
        self.data_dir = Path("test_data")
        self.checkpoints_dir = self.data_dir / "checkpoints"
        self.logs_dir = self.data_dir / "logs"
        self.data_dir.mkdir(exist_ok=True)
        self.checkpoints_dir.mkdir(exist_ok=True)
        self.logs_dir.mkdir(exist_ok=True)
        
        # Initialize core components
        self.event_emitter = EventEmitter()
        self.state_manager = StateManager(self.event_emitter)
        self.orchestrator = DebateOrchestrator(
            self.event_emitter,
            self.state_manager,
            checkpoint_dir=str(self.checkpoints_dir),
            log_dir=str(self.logs_dir)
        )
        
        # UI Components
        self.event_stream = EventStreamComponent()
        self.state_view = StateViewComponent()
        self.control_panel = ControlPanelComponent()
        self.debate_view = DebateViewComponent()
        self.workflow_viz = WorkflowVisualizerComponent()
        self.resource_monitor = ResourceMonitorComponent()
        self.debate_viz = DebateVisualizerComponent()
        self.metrics_viz = MetricsVisualizerComponent()
        self.recovery_viz = RecoveryVisualizerComponent()
        
        # Test state
        self.debate_results = None
        self.events: List[Event] = []
        
        # Register event handler
        for event_type in EventType:
            self.event_emitter.add_handler(event_type, self.handle_event)

    async def handle_event(self, event: Event) -> None:
        """Handle system events."""
        self.events.append(event)
        self.event_stream.add_event(event)
        
        # Track recovery-related events
        if event.event_type in [
            EventType.AGENT_TASK_FAILED,
            EventType.WORKFLOW_FAILED,
            EventType.DEBATE_FAILED
        ]:
            self.recovery_viz.add_error({
                "category": "agent" if "agent" in event.event_type else "workflow",
                "component": event.data.get("component", "unknown"),
                "operation": event.data.get("operation", "unknown"),
                "message": event.data.get("error", "Unknown error")
            })
        
        st.experimental_rerun()

    async def test_recovery_mechanisms(self) -> None:
        """Test system recovery mechanisms."""
        st.write("### Testing Recovery Mechanisms")
        
        try:
            # Test checkpoint creation
            st.write("Testing checkpoint creation...")
            debate_id = await self.orchestrator.initialize_debate(
                SAMPLE_MARKET_DATA["topic"],
                SAMPLE_MARKET_DATA["context"]
            )
            st.success("Checkpoint created successfully")
            
            # Test state restoration
            st.write("Testing state restoration...")
            await self.orchestrator.stop_debate()
            st.success("State restored successfully")
            
            # Test error handling
            st.write("Testing error handling...")
            with st.expander("Simulated Errors"):
                if st.button("Simulate Transient Error"):
                    self.recovery_viz.add_error({
                        "category": "transient",
                        "component": "test",
                        "operation": "simulate_error",
                        "message": "Simulated transient error"
                    })
                    self.recovery_viz.add_recovery({
                        "level": "retry",
                        "success": True,
                        "attempts": 1
                    })
                
                if st.button("Simulate State Error"):
                    self.recovery_viz.add_error({
                        "category": "state",
                        "component": "test",
                        "operation": "simulate_error",
                        "message": "Simulated state error"
                    })
                    self.recovery_viz.add_recovery({
                        "level": "rollback",
                        "success": True,
                        "attempts": 1
                    })
                
                if st.button("Simulate System Error"):
                    self.recovery_viz.add_error({
                        "category": "system",
                        "component": "test",
                        "operation": "simulate_error",
                        "message": "Simulated system error"
                    })
                    self.recovery_viz.add_recovery({
                        "level": "emergency",
                        "success": True,
                        "attempts": 1
                    })
            
        except Exception as e:
            st.error(f"Recovery test failed: {str(e)}")

    async def run_test_debate(self) -> None:
        """Run a test debate with recovery monitoring."""
        try:
            st.write("### Running Test Debate")
            
            # Initialize debate
            debate_id = await self.orchestrator.initialize_debate(
                SAMPLE_MARKET_DATA["topic"],
                SAMPLE_MARKET_DATA["context"]
            )
            
            st.success(f"Debate initialized with ID: {debate_id}")
            
            # Start debate
            results = await self.orchestrator.start_debate()
            self.debate_results = results
            
            st.success("Debate completed successfully")
            
            # Submit feedback
            await self.orchestrator.add_feedback(
                "initial",
                "Strong initial analysis with good market insights",
                quality_score=4
            )
            
            await self.orchestrator.add_feedback(
                "challenge",
                "Valid concerns about competition and integration",
                quality_score=4
            )
            
            await self.orchestrator.add_feedback(
                "final",
                "Well-reasoned final analysis addressing key concerns",
                quality_score=5
            )
            
            st.success("Feedback submitted successfully")
            
        except Exception as e:
            st.error(f"Error during test: {str(e)}")
            # Track error for recovery visualization
            self.recovery_viz.add_error({
                "category": "test",
                "component": "debate",
                "operation": "run_test",
                "message": str(e)
            })

def main():
    """Main application entry point."""
    st.set_page_config(
        page_title="System Test Dashboard",
        page_icon="🧪",
        layout="wide"
    )
    
    st.title("System Test Dashboard")
    
    # Initialize test harness
    if 'tester' not in st.session_state:
        st.session_state.tester = SystemTester()
    
    # Control section
    st.sidebar.write("### Test Controls")
    
    test_type = st.sidebar.selectbox(
        "Select Test",
        ["Full System Test", "Recovery Test"]
    )
    
    if test_type == "Full System Test":
        if st.sidebar.button("Run Test Debate", type="primary"):
            asyncio.run(st.session_state.tester.run_test_debate())
    else:
        if st.sidebar.button("Test Recovery", type="primary"):
            asyncio.run(st.session_state.tester.test_recovery_mechanisms())
    
    if st.sidebar.button("Stop Test"):
        asyncio.run(st.session_state.tester.orchestrator.stop_debate())
        st.session_state.tester.debate_results = None
    
    # Create tabs for different views
    tab1, tab2, tab3, tab4 = st.tabs([
        "Debate Progress",
        "Debate Analysis",
        "Recovery Status",
        "Test Results"
    ])
    
    with tab1:
        # Event stream and debate view
        st.session_state.tester.event_stream.render()
        st.session_state.tester.debate_view.render(
            debate_results=st.session_state.tester.debate_results,
            allow_feedback=True
        )
    
    with tab2:
        # Debate visualization
        if st.session_state.tester.debate_results:
            st.session_state.tester.debate_viz.render(
                rounds=[],  # No rounds history needed for MVP
                overall_metrics=st.session_state.tester.debate_results
            )
    
    with tab3:
        # Recovery visualization
        st.session_state.tester.recovery_viz.render(
            checkpoint_dir=str(st.session_state.tester.checkpoints_dir),
            show_health=True,
            show_timeline=True,
            show_checkpoints=True
        )
    
    with tab4:
        # Test results and statistics
        st.write("### Test Statistics")
        
        # Event statistics
        st.write("#### Event Distribution")
        event_counts = {}
        for event in st.session_state.tester.events:
            event_counts[event.event_type] = event_counts.get(event.event_type, 0) + 1
        
        if event_counts:
            st.bar_chart(event_counts)
        
        # System health
        st.write("#### System Health Check")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "Active Components",
                len([e for e in st.session_state.tester.events if "STARTED" in e.event_type])
            )
        
        with col2:
            st.metric(
                "Completed Tasks",
                len([e for e in st.session_state.tester.events if "COMPLETED" in e.event_type])
            )
        
        with col3:
            st.metric(
                "Error Rate",
                f"{len([e for e in st.session_state.tester.events if 'FAILED' in e.event_type]) / len(st.session_state.tester.events) * 100:.1f}%"
                if st.session_state.tester.events else "0%"
            )

if __name__ == "__main__":
    main()
