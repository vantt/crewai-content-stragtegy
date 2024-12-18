"""Metrics visualization components for Streamlit UI."""
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, Any, List, Optional
from datetime import datetime

from src.agents.metrics import (
    AgentMetrics,
    AgentMetricsCollector
)

class MetricsVisualizerComponent:
    """Component for visualizing system metrics."""
    
    def __init__(self):
        """Initialize the metrics visualizer component."""
        if "selected_metric" not in st.session_state:
            st.session_state.selected_metric = None
        if "show_details" not in st.session_state:
            st.session_state.show_details = False

    def _plot_agent_metrics_radar(self, metrics: AgentMetrics) -> None:
        """Plot agent metrics as a radar chart.
        
        Args:
            metrics: Agent metrics to plot
        """
        categories = [
            'Success Rate',
            'Response Time',
            'Error Rate',
            'Resource Usage'
        ]
        
        values = [
            metrics.success_rate,
            metrics.get_average_response_time(),
            metrics.get_error_rate() / 100,  # Convert to 0-1 scale
            max(m / 100 for m in metrics.resource_usage.values()) if metrics.resource_usage else 0
        ]
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatterpolar(
            r=values,
            theta=categories,
            fill='toself',
            name='Agent Metrics'
        ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 1]
                )
            ),
            showlegend=False,
            title="Agent Performance Analysis"
        )
        
        st.plotly_chart(fig)

    def _plot_performance_trends(
        self,
        metrics: AgentMetrics
    ) -> None:
        """Plot performance metric trends.
        
        Args:
            metrics: Agent metrics to plot
        """
        if not metrics.response_times:
            return
            
        # Response time trend
        fig1 = go.Figure()
        fig1.add_trace(go.Scatter(
            y=metrics.response_times,
            mode='lines+markers',
            name='Response Time'
        ))
        
        fig1.update_layout(
            title="Response Time Trend",
            yaxis_title="Response Time (s)"
        )
        
        st.plotly_chart(fig1)
        
        # Resource usage trend
        if metrics.resource_usage:
            fig2 = go.Figure()
            
            for resource, value in metrics.resource_usage.items():
                fig2.add_trace(go.Bar(
                    name=resource,
                    x=[resource],
                    y=[value]
                ))
            
            fig2.update_layout(
                title="Resource Usage",
                yaxis_title="Usage (%)"
            )
            
            st.plotly_chart(fig2)

    def _plot_error_distribution(self, metrics: AgentMetrics) -> None:
        """Plot error distribution.
        
        Args:
            metrics: Agent metrics to plot
        """
        if not metrics.error_counts:
            return
            
        fig = go.Figure(data=[
            go.Bar(
                x=list(metrics.error_counts.keys()),
                y=list(metrics.error_counts.values())
            )
        ])
        
        fig.update_layout(
            title="Error Distribution",
            xaxis_title="Error Type",
            yaxis_title="Count"
        )
        
        st.plotly_chart(fig)

    def _plot_task_distribution(self, metrics: AgentMetrics) -> None:
        """Plot task type distribution.
        
        Args:
            metrics: Agent metrics to plot
        """
        if not metrics.task_counts:
            return
            
        fig = go.Figure(data=[
            go.Pie(
                labels=list(metrics.task_counts.keys()),
                values=list(metrics.task_counts.values())
            )
        ])
        
        fig.update_layout(title="Task Distribution")
        
        st.plotly_chart(fig)

    def render(
        self,
        metrics_collector: Optional[AgentMetricsCollector] = None,
        show_performance: bool = True,
        show_errors: bool = True,
        show_tasks: bool = True
    ) -> None:
        """Render the metrics visualization.
        
        Args:
            metrics_collector: Metrics collector instance
            show_performance: Whether to show performance metrics
            show_errors: Whether to show error metrics
            show_tasks: Whether to show task metrics
        """
        st.subheader("System Metrics Analysis")
        
        if not metrics_collector:
            st.info("No metrics available")
            return
        
        # Get system summary
        system_summary = metrics_collector.get_system_summary()
        
        # System overview
        st.write("### System Overview")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Total Agents",
                system_summary.get("total_agents", 0)
            )
        
        with col2:
            st.metric(
                "Active Agents",
                system_summary.get("active_agents", 0)
            )
        
        with col3:
            st.metric(
                "Total Tasks",
                system_summary.get("total_tasks", 0)
            )
        
        with col4:
            st.metric(
                "Success Rate",
                f"{system_summary.get('avg_success_rate', 0):.1f}%"
            )
        
        # Create tabs for different views
        tab1, tab2, tab3 = st.tabs([
            "Performance",
            "Errors",
            "Tasks"
        ])
        
        with tab1:
            if show_performance:
                st.write("### Performance Metrics")
                
                # Agent selection
                all_metrics = metrics_collector.get_all_metrics()
                selected_agent = st.selectbox(
                    "Select Agent",
                    options=list(all_metrics.keys()),
                    format_func=lambda x: f"Agent {x[:8]}..."
                )
                
                if selected_agent:
                    agent_metrics = metrics_collector.get_or_create_metrics(selected_agent)
                    self._plot_agent_metrics_radar(agent_metrics)
                    self._plot_performance_trends(agent_metrics)
        
        with tab2:
            if show_errors:
                st.write("### Error Analysis")
                
                # Overall error rate
                total_errors = sum(
                    sum(m["error_counts"].values())
                    for m in metrics_collector.get_all_metrics().values()
                )
                
                st.metric("Total Errors", total_errors)
                
                # Error distribution by agent
                for agent_id, metrics in metrics_collector.get_all_metrics().items():
                    with st.expander(f"Agent {agent_id[:8]}..."):
                        agent_metrics = metrics_collector.get_or_create_metrics(agent_id)
                        self._plot_error_distribution(agent_metrics)
        
        with tab3:
            if show_tasks:
                st.write("### Task Analysis")
                
                # Task completion stats
                total_tasks = system_summary.get("total_tasks", 0)
                if total_tasks > 0:
                    success_rate = system_summary.get("avg_success_rate", 0)
                    st.metric(
                        "Task Success Rate",
                        f"{success_rate:.1f}%",
                        delta=f"{success_rate - 50:.1f}%" if success_rate != 50 else None
                    )
                
                # Task distribution by agent
                for agent_id, metrics in metrics_collector.get_all_metrics().items():
                    with st.expander(f"Agent {agent_id[:8]}..."):
                        agent_metrics = metrics_collector.get_or_create_metrics(agent_id)
                        self._plot_task_distribution(agent_metrics)
