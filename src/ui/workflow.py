"""Workflow visualization components for Streamlit UI."""
import streamlit as st
import networkx as nx
import matplotlib.pyplot as plt
from typing import Dict, Any, List, Optional
from datetime import datetime

from src.core.state import TaskStatus, WorkflowStatus

class WorkflowVisualizerComponent:
    """Component for visualizing workflow status."""
    
    # Status colors for visualization
    STATUS_COLORS = {
        TaskStatus.PENDING: "#808080",     # Gray
        TaskStatus.IN_PROGRESS: "#0000FF", # Blue
        TaskStatus.COMPLETED: "#00FF00",   # Green
        TaskStatus.FAILED: "#FF0000",      # Red
        TaskStatus.TERMINATED: "#000000"   # Black
    }
    
    def __init__(self):
        """Initialize workflow visualizer component."""
        if "selected_workflow" not in st.session_state:
            st.session_state.selected_workflow = None
    
    def _create_workflow_graph(
        self,
        workflow: Any,
        task_states: Dict[str, str]
    ) -> nx.DiGraph:
        """Create networkx graph for workflow visualization.
        
        Args:
            workflow: Workflow to visualize
            task_states: Task states
            
        Returns:
            NetworkX directed graph
        """
        G = nx.DiGraph()
        
        # Add nodes for tasks
        for task in workflow.tasks:
            state = task_states.get(task.task_id, TaskStatus.PENDING)
            G.add_node(
                task.task_id,
                label=task.description[:20] + "...",
                color=self.STATUS_COLORS[state]
            )
        
        # Add edges for dependencies
        for task in workflow.tasks:
            for dep in task.dependencies:
                G.add_edge(dep, task.task_id)
        
        return G
    
    def _plot_workflow_graph(self, G: nx.DiGraph) -> None:
        """Plot workflow graph using matplotlib.
        
        Args:
            G: NetworkX directed graph
        """
        plt.figure(figsize=(10, 6))
        pos = nx.spring_layout(G)
        
        # Draw nodes
        nx.draw_networkx_nodes(
            G,
            pos,
            node_color=[G.nodes[node]["color"] for node in G.nodes()],
            node_size=1000
        )
        
        # Draw edges
        nx.draw_networkx_edges(G, pos, edge_color='gray', arrows=True)
        
        # Draw labels
        nx.draw_networkx_labels(
            G,
            pos,
            {node: G.nodes[node]["label"] for node in G.nodes()}
        )
        
        plt.title("Workflow Status")
        st.pyplot(plt)
        plt.close()
    
    def _show_task_details(
        self,
        workflow: Any,
        task_states: Dict[str, str]
    ) -> None:
        """Show detailed task information.
        
        Args:
            workflow: Workflow to show details for
            task_states: Task states
        """
        st.write("### Task Details")
        
        for task in workflow.tasks:
            state = task_states.get(task.task_id, TaskStatus.PENDING)
            with st.expander(f"{task.description} ({state})"):
                st.write(f"**ID:** {task.task_id}")
                st.write(f"**State:** {state}")
                st.write("**Dependencies:**")
                for dep in task.dependencies:
                    st.write(f"- {dep}")
    
    def _show_resource_usage(self, resource_usage: Dict[str, Any]) -> None:
        """Show resource usage metrics.
        
        Args:
            resource_usage: Resource usage metrics
        """
        st.write("### Resource Usage")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "CPU Usage",
                f"{resource_usage.get('cpu_percent', 0):.1f}%"
            )
        
        with col2:
            st.metric(
                "Memory Usage",
                f"{resource_usage.get('memory_mb', 0):.1f} MB"
            )
        
        with col3:
            st.metric(
                "Active Tasks",
                resource_usage.get('active_tasks', 0)
            )
    
    def render(
        self,
        workflow: Optional[Any] = None,
        task_states: Optional[Dict[str, str]] = None,
        resource_usage: Optional[Dict[str, Any]] = None
    ) -> None:
        """Render the workflow visualization.
        
        Args:
            workflow: Optional workflow to visualize
            task_states: Optional task states
            resource_usage: Optional resource usage metrics
        """
        st.subheader("Workflow Monitor")
        
        if workflow and task_states:
            # Create and plot workflow graph
            G = self._create_workflow_graph(workflow, task_states)
            self._plot_workflow_graph(G)
            
            # Show task details
            self._show_task_details(workflow, task_states)
            
            # Show resource usage if available
            if resource_usage:
                self._show_resource_usage(resource_usage)
                
        else:
            st.info("No active workflow to visualize")

class ResourceMonitorComponent:
    """Component for monitoring system resources."""
    
    def render(self, current_usage: Dict[str, Any]) -> None:
        """Render the resource monitor.
        
        Args:
            current_usage: Current resource usage metrics
        """
        st.subheader("Resource Monitor")
        
        if current_usage:
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric(
                    "CPU Usage",
                    f"{current_usage.get('cpu_percent', 0):.1f}%",
                    delta=f"{current_usage.get('cpu_delta', 0):.1f}%"
                )
            
            with col2:
                st.metric(
                    "Memory Usage",
                    f"{current_usage.get('memory_mb', 0):.1f} MB",
                    delta=f"{current_usage.get('memory_delta', 0):.1f} MB"
                )
            
            with col3:
                st.metric(
                    "Active Tasks",
                    current_usage.get('active_tasks', 0),
                    delta=current_usage.get('tasks_delta', 0)
                )
            
            # Show history if available
            if 'history' in current_usage:
                st.write("### Resource History")
                st.line_chart(current_usage['history'])
                
        else:
            st.info("No resource usage data available")
