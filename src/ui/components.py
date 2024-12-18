"""Streamlit UI components for the debate protocol dashboard."""
import streamlit as st
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime

from src.core import (
    Event,
    EventType,
    WorkflowStatus,
    DebateStatus,
    TaskStatus
)

class EventStreamComponent:
    """Component for displaying the event stream."""
    
    def __init__(self):
        """Initialize the event stream component."""
        if "events" not in st.session_state:
            st.session_state.events = []

    def add_event(self, event: Event) -> None:
        """Add a new event to the stream.
        
        Args:
            event: Event to add
        """
        st.session_state.events.append(event)
        # Keep only last 100 events
        if len(st.session_state.events) > 100:
            st.session_state.events = st.session_state.events[-100:]

    def render(self) -> None:
        """Render the event stream component."""
        st.subheader("Event Stream")
        
        # Add filters
        col1, col2 = st.columns(2)
        with col1:
            selected_types = st.multiselect(
                "Filter by event type",
                options=[e.value for e in EventType],
                default=[]
            )
        
        with col2:
            show_count = st.slider("Show events", 1, 100, 20)

        # Filter and display events
        events = st.session_state.events
        if selected_types:
            events = [e for e in events if e.event_type in selected_types]
        
        events = events[-show_count:]  # Show only selected number of events
        
        # Display events
        for event in reversed(events):  # Show newest first
            with st.expander(
                f"{event.event_type} - {event.timestamp.strftime('%H:%M:%S')}",
                expanded=False
            ):
                st.json({
                    "event_id": event.event_id,
                    "event_type": event.event_type,
                    "workflow_id": event.workflow_id,
                    "step_id": event.step_id,
                    "agent_id": event.agent_id,
                    "timestamp": event.timestamp.isoformat(),
                    "data": event.data
                })

class StateViewComponent:
    """Component for visualizing system state."""
    
    def __init__(self):
        """Initialize the state view component."""
        pass

    def render(
        self,
        workflow_states: Dict[str, WorkflowStatus],
        debate_states: Dict[str, DebateStatus],
        task_states: Dict[str, TaskStatus]
    ) -> None:
        """Render the state view component.
        
        Args:
            workflow_states: Current workflow states
            debate_states: Current debate states
            task_states: Current task states
        """
        st.subheader("System State")
        
        # Create tabs for different state types
        tab1, tab2, tab3 = st.tabs(["Workflows", "Debates", "Tasks"])
        
        with tab1:
            if workflow_states:
                for wf_id, state in workflow_states.items():
                    st.metric(
                        label=f"Workflow {wf_id}",
                        value=state.value
                    )
            else:
                st.info("No active workflows")
        
        with tab2:
            if debate_states:
                for debate_id, state in debate_states.items():
                    st.metric(
                        label=f"Debate {debate_id}",
                        value=state.value
                    )
            else:
                st.info("No active debates")
        
        with tab3:
            if task_states:
                for task_id, state in task_states.items():
                    st.metric(
                        label=f"Task {task_id}",
                        value=state.value
                    )
            else:
                st.info("No active tasks")

class ControlPanelComponent:
    """Component for system controls."""
    
    DEBATE_TOPICS = [
        "Market Entry Strategy",
        "Product Development",
        "Marketing Campaign",
        "Competitive Analysis",
        "Customer Segmentation",
        "Pricing Strategy",
        "Distribution Channels",
        "Brand Positioning"
    ]
    
    def __init__(self):
        """Initialize the control panel component."""
        if "selected_topic" not in st.session_state:
            st.session_state.selected_topic = None
        if "market_context" not in st.session_state:
            st.session_state.market_context = {}

    def render(
        self,
        on_start_debate: Optional[Callable] = None,
        on_pause_debate: Optional[Callable] = None,
        on_resume_debate: Optional[Callable] = None,
        on_stop_debate: Optional[Callable] = None
    ) -> None:
        """Render the control panel component.
        
        Args:
            on_start_debate: Callback for starting a debate
            on_pause_debate: Callback for pausing a debate
            on_resume_debate: Callback for resuming a debate
            on_stop_debate: Callback for stopping a debate
        """
        st.subheader("Control Panel")
        
        # Topic Selection
        st.write("### Topic Selection")
        selected_topic = st.selectbox(
            "Select Debate Topic",
            options=self.DEBATE_TOPICS,
            index=None,
            placeholder="Choose a topic..."
        )
        
        # Market Context
        st.write("### Market Context")
        with st.expander("Market Information", expanded=True):
            market_size = st.number_input(
                "Market Size (USD Millions)",
                min_value=1,
                value=100
            )
            growth_rate = st.slider(
                "Annual Growth Rate (%)",
                min_value=0,
                max_value=100,
                value=10
            )
            competition_level = st.select_slider(
                "Competition Level",
                options=["Low", "Medium", "High"],
                value="Medium"
            )
            target_segment = st.multiselect(
                "Target Segments",
                options=["B2B", "B2C", "Enterprise", "SMB", "Consumer"],
                default=["B2B"]
            )
            
            # Additional context
            custom_context = st.text_area(
                "Additional Context",
                placeholder="Enter any additional market information..."
            )
        
        # Store context
        if selected_topic:
            st.session_state.selected_topic = selected_topic
            st.session_state.market_context = {
                "topic": selected_topic,
                "market_size": market_size,
                "growth_rate": growth_rate,
                "competition_level": competition_level,
                "target_segment": target_segment,
                "additional_context": custom_context
            }
        
        # Debate Controls
        st.write("### Debate Controls")
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button(
                "Start Debate",
                type="primary",
                disabled=not selected_topic
            ):
                if on_start_debate:
                    on_start_debate()
            
            if st.button("Pause Debate"):
                if on_pause_debate:
                    on_pause_debate()
        
        with col2:
            if st.button("Resume Debate"):
                if on_resume_debate:
                    on_resume_debate()
            
            if st.button("Stop Debate", type="secondary"):
                if on_stop_debate:
                    on_stop_debate()
        
        # Settings
        st.write("### Settings")
        st.slider("Response Delay (ms)", 0, 1000, 100)
        st.checkbox("Auto-scroll Events", value=True)
        st.checkbox("Show Debug Info", value=False)

class DebateViewComponent:
    """Component for viewing debate progress and results."""
    
    def __init__(self):
        """Initialize the debate view component."""
        pass

    def render(
        self,
        debate_results: Optional[Dict[str, Any]] = None,
        allow_feedback: bool = True
    ) -> None:
        """Render the debate view component.
        
        Args:
            debate_results: Current debate results
            allow_feedback: Whether to allow human feedback
        """
        st.subheader("Debate Progress")
        
        if not debate_results:
            st.info("No active debate. Select a topic and start a debate.")
            return
        
        # Show topic and context
        st.write("#### Topic:", debate_results.get("topic", "N/A"))
        
        # Initial Analysis
        with st.expander("Initial Analysis", expanded=True):
            st.json(debate_results["initial_analysis"])
            if allow_feedback:
                st.text_area(
                    "Your Feedback on Initial Analysis",
                    key="feedback_initial"
                )
        
        # Challenge
        with st.expander("Skeptic's Challenge", expanded=True):
            st.json(debate_results["challenge"])
            if allow_feedback:
                st.text_area(
                    "Your Feedback on Challenge",
                    key="feedback_challenge"
                )
        
        # Final Analysis
        with st.expander("Final Analysis", expanded=True):
            st.json(debate_results["final_analysis"])
            if allow_feedback:
                st.text_area(
                    "Your Feedback on Final Analysis",
                    key="feedback_final"
                )
        
        # Overall Feedback
        if allow_feedback:
            st.write("#### Overall Feedback")
            quality_score = st.slider(
                "Debate Quality",
                min_value=1,
                max_value=5,
                value=3,
                help="Rate the overall quality of the debate"
            )
            feedback = st.text_area(
                "Additional Comments",
                placeholder="Share your thoughts on the debate..."
            )
            if st.button("Submit Feedback"):
                # TODO: Handle feedback submission
                st.success("Feedback submitted!")
