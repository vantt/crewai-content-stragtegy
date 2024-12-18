"""Main Streamlit application for the debate protocol dashboard."""
import streamlit as st
import asyncio
from typing import Optional, Dict, Any
import uuid
from datetime import datetime
from pathlib import Path

from src.core import (
    EventEmitter,
    StateManager,
    Event,
    EventType,
    DebateStatus,
    WorkflowStatus,
    TaskStatus
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
from src.agents.orchestrator import DebateOrchestrator

# Initialize session state
if 'initialized' not in st.session_state:
    st.session_state.initialized = False
    
    # Core components
    st.session_state.event_emitter = EventEmitter()
    st.session_state.state_manager = StateManager(st.session_state.event_emitter)
    
    # Create data directories
    data_dir = Path("data")
    checkpoints_dir = data_dir / "checkpoints"
    logs_dir = data_dir / "logs"
    data_dir.mkdir(exist_ok=True)
    checkpoints_dir.mkdir(exist_ok=True)
    logs_dir.mkdir(exist_ok=True)
    
    # Initialize orchestrator
    st.session_state.orchestrator = DebateOrchestrator(
        st.session_state.event_emitter,
        st.session_state.state_manager,
        checkpoint_dir=str(checkpoints_dir),
        log_dir=str(logs_dir)
    )
    
    # UI Components
    st.session_state.event_stream = EventStreamComponent()
    st.session_state.state_view = StateViewComponent()
    st.session_state.control_panel = ControlPanelComponent()
    st.session_state.debate_view = DebateViewComponent()
    st.session_state.workflow_viz = WorkflowVisualizerComponent()
    st.session_state.resource_monitor = ResourceMonitorComponent()
    st.session_state.debate_viz = DebateVisualizerComponent()
    st.session_state.metrics_viz = MetricsVisualizerComponent()
    st.session_state.recovery_viz = RecoveryVisualizerComponent()
    
    # State
    st.session_state.debate_results = None

# Page config
st.set_page_config(
    page_title="Debate Protocol Dashboard",
    page_icon="🤖",
    layout="wide"
)

async def handle_event(event: Event) -> None:
    """Handle incoming events.
    
    Args:
        event: Event to handle
    """
    st.session_state.event_stream.add_event(event)
    
    # Track recovery-related events
    if event.event_type in [
        EventType.AGENT_TASK_FAILED,
        EventType.WORKFLOW_FAILED,
        EventType.DEBATE_FAILED
    ]:
        st.session_state.recovery_viz.add_error({
            "category": "agent" if "agent" in event.event_type else "workflow",
            "component": event.data.get("component", "unknown"),
            "operation": event.data.get("operation", "unknown"),
            "message": event.data.get("error", "Unknown error")
        })
    
    st.experimental_rerun()

async def start_debate() -> None:
    """Start a new debate using the selected topic and context."""
    try:
        # Get topic and context from session state
        topic = st.session_state.selected_topic
        context = st.session_state.market_context
        
        if not topic or not context:
            st.error("Please select a topic and provide market context")
            return
        
        # Initialize debate
        debate_id = await st.session_state.orchestrator.initialize_debate(
            topic,
            context
        )
        
        # Start debate
        results = await st.session_state.orchestrator.start_debate()
        
        # Store results
        st.session_state.debate_results = results
        
        # Track successful recovery if this was a retry
        if "retry_count" in st.session_state:
            st.session_state.recovery_viz.add_recovery({
                "level": "retry",
                "success": True,
                "attempts": st.session_state.retry_count
            })
            del st.session_state.retry_count
        
    except Exception as e:
        st.error(f"Failed to start debate: {str(e)}")
        
        # Track retry attempts
        if "retry_count" not in st.session_state:
            st.session_state.retry_count = 1
        else:
            st.session_state.retry_count += 1
        
        # Track failed recovery attempt
        st.session_state.recovery_viz.add_recovery({
            "level": "retry",
            "success": False,
            "attempts": st.session_state.retry_count
        })

async def stop_debate() -> None:
    """Stop the current debate."""
    try:
        await st.session_state.orchestrator.stop_debate()
        st.session_state.debate_results = None
    except Exception as e:
        st.error(f"Failed to stop debate: {str(e)}")

async def handle_feedback(
    stage: str,
    feedback: str,
    quality_score: Optional[int] = None
) -> None:
    """Handle feedback submission.
    
    Args:
        stage: Debate stage
        feedback: Feedback text
        quality_score: Quality rating
    """
    try:
        await st.session_state.orchestrator.add_feedback(
            stage,
            feedback,
            quality_score
        )
        st.success("Feedback submitted successfully!")
    except Exception as e:
        st.error(f"Failed to submit feedback: {str(e)}")

def main():
    """Main application entry point."""
    st.title("Debate Protocol Dashboard")
    
    # Initialize event handler if not already done
    if not st.session_state.initialized:
        for event_type in EventType:
            st.session_state.event_emitter.add_handler(
                event_type,
                handle_event
            )
        st.session_state.initialized = True
    
    # Create tabs for different views
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "Debate & Controls",
        "Debate Analysis",
        "Metrics & Analytics",
        "Workflow Monitor",
        "System Health",
        "Recovery Status"
    ])
    
    with tab1:
        # Main debate view
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Event stream
            st.session_state.event_stream.render()
            
            # Debate view with results and feedback
            st.session_state.debate_view.render(
                debate_results=st.session_state.debate_results,
                allow_feedback=True
            )
            
            # Handle feedback submission
            if st.session_state.debate_results:
                for key in ["feedback_initial", "feedback_challenge", "feedback_final"]:
                    if key in st.session_state and st.session_state[key]:
                        stage = key.split("_")[1]
                        asyncio.run(handle_feedback(
                            stage,
                            st.session_state[key],
                            st.session_state.get("quality_score")
                        ))
                        # Clear feedback after submission
                        st.session_state[key] = ""
        
        with col2:
            # Control panel
            st.session_state.control_panel.render(
                on_start_debate=lambda: asyncio.run(start_debate()),
                on_stop_debate=lambda: asyncio.run(stop_debate())
            )
            
            # State view
            st.session_state.state_view.render(
                workflow_states=st.session_state.state_manager._states["workflow"],
                debate_states=st.session_state.state_manager._states["debate"],
                task_states=st.session_state.state_manager._states["task"]
            )
    
    with tab2:
        # Debate visualization
        if st.session_state.debate_results:
            current_debate = st.session_state.orchestrator.current_session
            if current_debate:
                st.session_state.debate_viz.render(
                    rounds=current_debate.get_round_history(),
                    overall_metrics=current_debate.calculate_overall_metrics()
                )
        else:
            st.info("Start a debate to see analysis")
    
    with tab3:
        # Metrics visualization
        if st.session_state.debate_results:
            current_debate = st.session_state.orchestrator.current_session
            if current_debate:
                current_round = current_debate.current_round
                if current_round and current_round.metrics:
                    st.session_state.metrics_viz.render(
                        consensus_metrics=current_round.metrics.consensus_metrics,
                        evidence_metrics=current_round.metrics.evidence_metrics,
                        performance_metrics=[current_round.metrics.performance_metrics] if current_round.metrics.performance_metrics else None,
                        overall_metrics=current_debate.calculate_overall_metrics()
                    )
                else:
                    st.info("Waiting for round metrics...")
        else:
            st.info("Start a debate to see metrics")
    
    with tab4:
        # Workflow visualization
        if st.session_state.debate_results:
            workflow = st.session_state.orchestrator.workflow_manager.workflows.get(
                st.session_state.orchestrator.debate_id
            )
            task_states = {
                task.task_id: st.session_state.state_manager.get_task_state(task.task_id)
                for task in workflow.tasks
            } if workflow else {}
            
            st.session_state.workflow_viz.render(
                workflow=workflow,
                task_states=task_states,
                resource_usage=st.session_state.orchestrator.workflow_manager.get_resource_usage()
            )
        else:
            st.info("Start a debate to see workflow visualization")
    
    with tab5:
        # Resource monitoring
        st.session_state.resource_monitor.render(
            current_usage=st.session_state.orchestrator.workflow_manager.get_resource_usage()
        )
        
        # Show feedback history
        if st.checkbox("Show Feedback History"):
            st.write("### Feedback History")
            feedback_history = st.session_state.orchestrator.get_feedback_history()
            if feedback_history:
                for entry in feedback_history:
                    with st.expander(
                        f"{entry['stage'].title()} - {entry['timestamp']}",
                        expanded=False
                    ):
                        st.write(f"**Quality Score:** {entry.get('quality_score', 'N/A')}")
                        st.write(f"**Feedback:** {entry['feedback']}")
            else:
                st.info("No feedback history available")
    
    with tab6:
        # Recovery visualization
        st.session_state.recovery_viz.render(
            checkpoint_dir=str(Path("data/checkpoints")),
            show_health=True,
            show_timeline=True,
            show_checkpoints=True
        )

if __name__ == "__main__":
    main()
