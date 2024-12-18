"""Debate visualization components for Streamlit UI."""
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, Any, List, Optional
from datetime import datetime

class DebateVisualizerComponent:
    """Component for visualizing debate progress and results."""
    
    def __init__(self):
        """Initialize debate visualizer component."""
        if "selected_round" not in st.session_state:
            st.session_state.selected_round = None
        if "show_details" not in st.session_state:
            st.session_state.show_details = False

    def _plot_overall_metrics(self, metrics: Dict[str, Any]) -> None:
        """Plot overall debate metrics.
        
        Args:
            metrics: Overall metrics to plot
        """
        if not metrics:
            st.info("No metrics available")
            return
            
        # Create columns for key metrics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "Success Rate",
                f"{metrics.get('success_rate', 0):.1f}%"
            )
        
        with col2:
            st.metric(
                "Average Response Time",
                f"{metrics.get('avg_response_time', 0):.2f}s"
            )
        
        with col3:
            st.metric(
                "Total Tasks",
                metrics.get('total_tasks', 0)
            )
        
        # Plot consensus metrics if available
        consensus_data = {
            'Initial Analysis': metrics.get('initial_consensus', 0),
            'Challenge Phase': metrics.get('challenge_consensus', 0),
            'Final Decision': metrics.get('final_consensus', 0)
        }
        
        if any(consensus_data.values()):
            fig = go.Figure(data=[
                go.Bar(
                    x=list(consensus_data.keys()),
                    y=list(consensus_data.values()),
                    marker_color=['#1f77b4', '#ff7f0e', '#2ca02c']
                )
            ])
            
            fig.update_layout(
                title="Consensus Levels by Phase",
                yaxis_title="Consensus Level (%)",
                showlegend=False
            )
            
            st.plotly_chart(fig)

    def _plot_round_metrics(self, round_data: Dict[str, Any]) -> None:
        """Plot metrics for a specific round.
        
        Args:
            round_data: Round data to plot
        """
        if not round_data:
            return
            
        # Plot argument distribution
        argument_types = round_data.get('argument_types', {})
        if argument_types:
            fig = px.pie(
                values=list(argument_types.values()),
                names=list(argument_types.keys()),
                title="Argument Distribution"
            )
            st.plotly_chart(fig)
        
        # Plot evidence strength
        evidence_data = round_data.get('evidence_strength', [])
        if evidence_data:
            fig = go.Figure(data=[
                go.Box(
                    y=evidence_data,
                    name="Evidence Strength",
                    boxpoints='all'
                )
            ])
            
            fig.update_layout(
                title="Evidence Strength Distribution",
                yaxis_title="Strength Score"
            )
            
            st.plotly_chart(fig)

    def _show_round_details(self, round_data: Dict[str, Any]) -> None:
        """Show detailed information for a debate round.
        
        Args:
            round_data: Round data to display
        """
        if not round_data:
            return
            
        st.write("### Round Details")
        
        # Arguments section
        st.write("#### Arguments")
        for arg in round_data.get('arguments', []):
            with st.expander(f"{arg.get('type', 'Unknown')} - {arg.get('agent_id', 'Unknown')}"):
                st.write(arg.get('content', 'No content available'))
                
                # Evidence subsection
                if 'evidence' in arg:
                    st.write("**Evidence:**")
                    for evidence in arg['evidence']:
                        st.write(f"- {evidence.get('description', 'No description')}")
                        st.write(f"  Confidence: {evidence.get('confidence', 0):.2f}")
        
        # Metrics section
        if 'metrics' in round_data:
            st.write("#### Round Metrics")
            metrics = round_data['metrics']
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric(
                    "Arguments",
                    metrics.get('argument_count', 0)
                )
            with col2:
                st.metric(
                    "Evidence",
                    metrics.get('evidence_count', 0)
                )

    def render(
        self,
        rounds: Optional[List[Dict[str, Any]]] = None,
        overall_metrics: Optional[Dict[str, Any]] = None
    ) -> None:
        """Render the debate visualization.
        
        Args:
            rounds: Optional list of debate rounds
            overall_metrics: Optional overall debate metrics
        """
        st.subheader("Debate Analysis")
        
        # Overall metrics
        st.write("### Overall Metrics")
        self._plot_overall_metrics(overall_metrics or {})
        
        # Round selection
        if rounds:
            st.write("### Round Analysis")
            selected_round = st.selectbox(
                "Select Round",
                range(len(rounds)),
                format_func=lambda x: f"Round {x + 1}"
            )
            
            if selected_round is not None:
                round_data = rounds[selected_round]
                
                # Plot round metrics
                self._plot_round_metrics(round_data)
                
                # Show round details
                if st.checkbox("Show Round Details"):
                    self._show_round_details(round_data)
        
        # No rounds available
        elif not overall_metrics:
            st.info("No debate data available")
