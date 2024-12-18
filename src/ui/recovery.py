"""Recovery visualization components for Streamlit UI."""
import streamlit as st
from typing import Dict, Any, List, Optional
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
from pathlib import Path

from src.core.recovery import (
    RecoveryLevel,
    ErrorCategory,
    SystemState
)

class RecoveryVisualizerComponent:
    """Component for visualizing system recovery and health."""
    
    def __init__(self):
        """Initialize recovery visualizer component."""
        if "error_history" not in st.session_state:
            st.session_state.error_history = []
        if "recovery_history" not in st.session_state:
            st.session_state.recovery_history = []

    def _plot_error_distribution(self) -> None:
        """Plot error category distribution."""
        if not st.session_state.error_history:
            return
            
        # Count errors by category
        error_counts = {}
        for error in st.session_state.error_history:
            category = error.get("category", ErrorCategory.UNKNOWN)
            error_counts[category] = error_counts.get(category, 0) + 1
        
        fig = go.Figure(data=[
            go.Bar(
                x=list(error_counts.keys()),
                y=list(error_counts.values()),
                marker_color=[
                    'yellow' if k == ErrorCategory.TRANSIENT else
                    'orange' if k == ErrorCategory.STATE else
                    'red' if k == ErrorCategory.SYSTEM else
                    'blue'
                    for k in error_counts.keys()
                ]
            )
        ])
        
        fig.update_layout(
            title="Error Distribution by Category",
            xaxis_title="Error Category",
            yaxis_title="Count"
        )
        
        st.plotly_chart(fig)

    def _plot_recovery_timeline(self) -> None:
        """Plot recovery action timeline."""
        if not st.session_state.recovery_history:
            return
            
        # Create timeline data
        times = [r["timestamp"] for r in st.session_state.recovery_history]
        levels = [r["level"] for r in st.session_state.recovery_history]
        success = [r["success"] for r in st.session_state.recovery_history]
        
        fig = go.Figure()
        
        # Add successful recoveries
        success_times = [t for t, s in zip(times, success) if s]
        success_levels = [l for l, s in zip(levels, success) if s]
        if success_times:
            fig.add_trace(go.Scatter(
                x=success_times,
                y=success_levels,
                mode='markers',
                name='Successful',
                marker=dict(
                    color='green',
                    symbol='circle'
                )
            ))
        
        # Add failed recoveries
        failed_times = [t for t, s in zip(times, success) if not s]
        failed_levels = [l for l, s in zip(levels, success) if not s]
        if failed_times:
            fig.add_trace(go.Scatter(
                x=failed_times,
                y=failed_levels,
                mode='markers',
                name='Failed',
                marker=dict(
                    color='red',
                    symbol='x'
                )
            ))
        
        fig.update_layout(
            title="Recovery Actions Timeline",
            xaxis_title="Time",
            yaxis_title="Recovery Level"
        )
        
        st.plotly_chart(fig)

    def _plot_system_health(self) -> None:
        """Plot system health metrics."""
        # Calculate health score based on recent history
        recent_errors = len([
            e for e in st.session_state.error_history
            if (datetime.now() - e["timestamp"]) < timedelta(minutes=5)
        ])
        
        recent_recoveries = len([
            r for r in st.session_state.recovery_history
            if (datetime.now() - r["timestamp"]) < timedelta(minutes=5)
        ])
        
        successful_recoveries = len([
            r for r in st.session_state.recovery_history
            if r["success"]
        ])
        
        total_recoveries = len(st.session_state.recovery_history)
        recovery_rate = successful_recoveries / total_recoveries if total_recoveries > 0 else 1.0
        
        # Calculate health metrics
        metrics = {
            "System Health": max(0, 1 - (recent_errors * 0.1)),
            "Recovery Rate": recovery_rate,
            "Error Rate": max(0, 1 - (recent_errors / 10 if recent_errors > 0 else 0)),
            "Stability": max(0, 1 - (recent_recoveries * 0.1))
        }
        
        # Create gauge charts
        for metric, value in metrics.items():
            fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=value * 100,
                domain={'x': [0, 1], 'y': [0, 1]},
                title={'text': metric},
                gauge={
                    'axis': {'range': [0, 100]},
                    'bar': {'color': 'green' if value > 0.7 else 'orange' if value > 0.4 else 'red'},
                    'steps': [
                        {'range': [0, 40], 'color': 'lightgray'},
                        {'range': [40, 70], 'color': 'gray'},
                        {'range': [70, 100], 'color': 'darkgray'}
                    ]
                }
            ))
            
            st.plotly_chart(fig)

    def _display_checkpoint_info(self, checkpoint_dir: str) -> None:
        """Display checkpoint information.
        
        Args:
            checkpoint_dir: Directory containing checkpoints
        """
        checkpoint_path = Path(checkpoint_dir)
        if not checkpoint_path.exists():
            st.warning("Checkpoint directory not found")
            return
        
        checkpoints = list(checkpoint_path.glob("*.json"))
        if not checkpoints:
            st.info("No checkpoints available")
            return
        
        st.write("### System Checkpoints")
        
        # Show checkpoint statistics
        st.metric("Total Checkpoints", len(checkpoints))
        
        # List recent checkpoints
        st.write("#### Recent Checkpoints")
        recent_checkpoints = sorted(
            checkpoints,
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )[:5]
        
        for cp in recent_checkpoints:
            with st.expander(f"Checkpoint: {cp.stem}"):
                st.write(f"Created: {datetime.fromtimestamp(cp.stat().st_mtime)}")
                st.write(f"Size: {cp.stat().st_size / 1024:.1f} KB")
                
                if st.button(f"Restore {cp.stem}"):
                    st.session_state.restore_checkpoint = cp.stem

    def add_error(self, error_data: Dict[str, Any]) -> None:
        """Add error to history.
        
        Args:
            error_data: Error information
        """
        error_data["timestamp"] = datetime.now()
        st.session_state.error_history.append(error_data)
        
        # Keep last 100 errors
        if len(st.session_state.error_history) > 100:
            st.session_state.error_history = st.session_state.error_history[-100:]

    def add_recovery(self, recovery_data: Dict[str, Any]) -> None:
        """Add recovery action to history.
        
        Args:
            recovery_data: Recovery information
        """
        recovery_data["timestamp"] = datetime.now()
        st.session_state.recovery_history.append(recovery_data)
        
        # Keep last 100 recoveries
        if len(st.session_state.recovery_history) > 100:
            st.session_state.recovery_history = st.session_state.recovery_history[-100:]

    def render(
        self,
        checkpoint_dir: Optional[str] = None,
        show_health: bool = True,
        show_timeline: bool = True,
        show_checkpoints: bool = True
    ) -> None:
        """Render the recovery visualization.
        
        Args:
            checkpoint_dir: Optional checkpoint directory
            show_health: Whether to show health metrics
            show_timeline: Whether to show recovery timeline
            show_checkpoints: Whether to show checkpoint info
        """
        st.subheader("System Recovery & Health")
        
        # Create tabs for different views
        tab1, tab2, tab3 = st.tabs([
            "System Health",
            "Error Analysis",
            "Recovery Actions"
        ])
        
        with tab1:
            if show_health:
                self._plot_system_health()
        
        with tab2:
            # Error distribution
            self._plot_error_distribution()
            
            # Recent errors
            st.write("### Recent Errors")
            for error in reversed(st.session_state.error_history[-5:]):
                with st.expander(
                    f"{error['category']} - {error['timestamp'].strftime('%H:%M:%S')}",
                    expanded=False
                ):
                    st.write(f"**Component:** {error.get('component', 'Unknown')}")
                    st.write(f"**Operation:** {error.get('operation', 'Unknown')}")
                    st.write(f"**Message:** {error.get('message', 'No message')}")
        
        with tab3:
            if show_timeline:
                self._plot_recovery_timeline()
            
            if show_checkpoints and checkpoint_dir:
                self._display_checkpoint_info(checkpoint_dir)
            
            # Recovery statistics
            total_recoveries = len(st.session_state.recovery_history)
            if total_recoveries > 0:
                successful = len([r for r in st.session_state.recovery_history if r["success"]])
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Recoveries", total_recoveries)
                with col2:
                    st.metric("Successful", successful)
                with col3:
                    st.metric(
                        "Success Rate",
                        f"{(successful/total_recoveries)*100:.1f}%"
                    )
