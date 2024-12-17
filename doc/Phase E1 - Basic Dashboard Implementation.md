# Phase E1: Basic Dashboard Technical Specification

## 1. Overview
### 1.1 Purpose
This specification details the implementation of the Basic Dashboard component for the CrewAI Content Marketing System, providing a user interface for workflow monitoring and control.

### 1.2 Dependencies
```python
from typing import Dict, List, Optional, Union, Any
from pydantic import BaseModel, Field
import streamlit as st
from datetime import datetime
import asyncio
from enum import Enum
import plotly.graph_objects as go
import plotly.express as px
from loguru import logger
```

## 2. Data Models

### 2.1 Dashboard Models
```python
class DashboardState(BaseModel):
    """Model for tracking dashboard state."""
    selected_workflow: Optional[str] = None
    selected_view: str = "overview"
    filters: Dict[str, Any] = Field(default_factory=dict)
    refresh_interval: int = 30  # seconds
    last_update: Optional[datetime] = None

class WorkflowSummary(BaseModel):
    """Summary statistics for workflows."""
    total_workflows: int
    active_workflows: int
    completed_workflows: int
    failed_workflows: int
    average_completion_time: float
    success_rate: float

class AgentMetrics(BaseModel):
    """Performance metrics for agents."""
    agent_id: str
    tasks_completed: int
    success_rate: float
    average_response_time: float
    current_status: str
    last_active: datetime
```

## 3. Core Dashboard Implementation

### 3.1 Base Class
```python
class Dashboard:
    def __init__(self, orchestrator: Any):
        self.orchestrator = orchestrator
        self.state = DashboardState()
        self._setup_session_state()
    
    def _setup_session_state(self):
        """Initialize Streamlit session state."""
        if 'dashboard_state' not in st.session_state:
            st.session_state.dashboard_state = self.state
        
        if 'workflows' not in st.session_state:
            st.session_state.workflows = {}
        
        if 'agent_metrics' not in st.session_state:
            st.session_state.agent_metrics = {}
    
    def render(self):
        """Main rendering method for the dashboard."""
        st.title("Content Marketing System Dashboard")
        
        # Sidebar
        self._render_sidebar()
        
        # Main content
        if self.state.selected_view == "overview":
            self._render_overview()
        elif self.state.selected_view == "workflows":
            self._render_workflow_view()
        elif self.state.selected_view == "agents":
            self._render_agent_view()
        elif self.state.selected_view == "analytics":
            self._render_analytics()
```

### 3.2 Sidebar Implementation
```python
class Dashboard(Dashboard):
    def _render_sidebar(self):
        """Render the dashboard sidebar."""
        with st.sidebar:
            st.header("Navigation")
            
            # View selection
            selected_view = st.selectbox(
                "Select View",
                ["overview", "workflows", "agents", "analytics"],
                key="view_selector"
            )
            self.state.selected_view = selected_view
            
            # Workflow filter
            if selected_view in ["workflows", "analytics"]:
                st.subheader("Filters")
                status_filter = st.multiselect(
                    "Status",
                    ["pending", "in_progress", "completed", "failed"],
                    default=["in_progress", "pending"]
                )
                self.state.filters["status"] = status_filter
            
            # Refresh rate
            st.subheader("Settings")
            refresh_rate = st.slider(
                "Refresh Interval (seconds)",
                min_value=5,
                max_value=300,
                value=self.state.refresh_interval
            )
            self.state.refresh_interval = refresh_rate
            
            # Manual refresh button
            if st.button("Refresh Data"):
                self._refresh_data()
```

### 3.3 Overview Section
```python
class Dashboard(Dashboard):
    def _render_overview(self):
        """Render the overview section."""
        # Summary statistics
        summary = self._get_workflow_summary()
        
        # Display metrics in columns
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                label="Active Workflows",
                value=summary.active_workflows,
                delta=f"{summary.success_rate:.1%} Success Rate"
            )
        
        with col2:
            st.metric(
                label="Completed Workflows",
                value=summary.completed_workflows,
                delta=f"{summary.average_completion_time:.1f} min avg time"
            )
        
        with col3:
            st.metric(
                label="Failed Workflows",
                value=summary.failed_workflows
            )
        
        # Recent activity chart
        st.subheader("Recent Activity")
        fig = self._create_activity_chart()
        st.plotly_chart(fig, use_container_width=True)
        
        # Active workflows table
        st.subheader("Active Workflows")
        active_workflows = self._get_active_workflows()
        if active_workflows:
            self._render_workflow_table(active_workflows)
        else:
            st.info("No active workflows")
    
    def _create_activity_chart(self) -> go.Figure:
        """Create activity timeline chart."""
        activity_data = self._get_activity_data()
        
        fig = go.Figure()
        
        # Add trace for each activity type
        for activity_type in ["started", "completed", "failed"]:
            fig.add_trace(
                go.Scatter(
                    x=[a["timestamp"] for a in activity_data if a["type"] == activity_type],
                    y=[a["count"] for a in activity_data if a["type"] == activity_type],
                    name=activity_type.capitalize(),
                    mode="lines+markers"
                )
            )
        
        fig.update_layout(
            title="Workflow Activity (Last 24 Hours)",
            xaxis_title="Time",
            yaxis_title="Count",
            hovermode="x unified"
        )
        
        return fig
```

### 3.4 Workflow View
```python
class Dashboard(Dashboard):
    def _render_workflow_view(self):
        """Render the workflow management view."""
        st.header("Workflow Management")
        
        # Workflow creation section
        with st.expander("Create New Workflow"):
            self._render_workflow_creation_form()
        
        # Workflow list
        st.subheader("Workflow List")
        workflows = self._get_filtered_workflows()
        
        if not workflows:
            st.info("No workflows match the current filters")
            return
        
        # Render workflow cards
        for workflow in workflows:
            with st.container():
                self._render_workflow_card(workflow)
    
    def _render_workflow_card(self, workflow: Dict[str, Any]):
        """Render a single workflow card."""
        with st.container():
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.subheader(workflow["name"])
                st.text(f"Status: {workflow['status']}")
                st.progress(workflow["progress"])
                
                # Display steps
                for step in workflow["steps"]:
                    st.text(f"• {step['name']}: {step['status']}")
            
            with col2:
                # Action buttons
                if workflow["status"] == "in_progress":
                    if st.button("Pause", key=f"pause_{workflow['id']}"):
                        self._pause_workflow(workflow["id"])
                
                if workflow["status"] == "paused":
                    if st.button("Resume", key=f"resume_{workflow['id']}"):
                        self._resume_workflow(workflow["id"])
                
                if st.button("Details", key=f"details_{workflow['id']}"):
                    self.state.selected_workflow = workflow["id"]
```

### 3.5 Agent View
```python
class Dashboard(Dashboard):
    def _render_agent_view(self):
        """Render the agent monitoring view."""
        st.header("Agent Monitoring")
        
        # Agent metrics summary
        metrics = self._get_agent_metrics()
        
        # Display agent cards in grid
        cols = st.columns(2)
        for idx, agent in enumerate(metrics):
            with cols[idx % 2]:
                self._render_agent_card(agent)
    
    def _render_agent_card(self, agent: AgentMetrics):
        """Render a single agent monitoring card."""
        with st.container():
            st.subheader(f"Agent: {agent.agent_id}")
            
            # Status indicator
            status_color = {
                "idle": "🟢",
                "working": "🟡",
                "error": "🔴"
            }.get(agent.current_status, "⚪")
            st.write(f"Status: {status_color} {agent.current_status}")
            
            # Metrics
            col1, col2 = st.columns(2)
            with col1:
                st.metric(
                    label="Tasks Completed",
                    value=agent.tasks_completed,
                    delta=f"{agent.success_rate:.1%} Success"
                )
            
            with col2:
                st.metric(
                    label="Avg Response Time",
                    value=f"{agent.average_response_time:.2f}s"
                )
            
            # Last active timestamp
            st.text(f"Last Active: {agent.last_active.strftime('%Y-%m-%d %H:%M:%S')}")
```

### 3.6 Analytics View
```python
class Dashboard(Dashboard):
    def _render_analytics(self):
        """Render the analytics view."""
        st.header("System Analytics")
        
        # Time period selector
        time_period = st.selectbox(
            "Time Period",
            ["Last 24 Hours", "Last 7 Days", "Last 30 Days", "All Time"]
        )
        
        # Performance metrics
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Workflow Performance")
            workflow_metrics = self._get_workflow_metrics(time_period)
            fig = self._create_workflow_performance_chart(workflow_metrics)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("Agent Performance")
            agent_metrics = self._get_agent_performance_metrics(time_period)
            fig = self._create_agent_performance_chart(agent_metrics)
            st.plotly_chart(fig, use_container_width=True)
        
        # Detailed analytics tables
        st.subheader("Detailed Analytics")
        tabs = st.tabs(["Workflow Analytics", "Agent Analytics", "System Metrics"])
        
        with tabs[0]:
            self._render_workflow_analytics_table()
        
        with tabs[1]:
            self._render_agent_analytics_table()
        
        with tabs[2]:
            self._render_system_metrics()
```

### 3.7 Data Refresh Methods
```python
class Dashboard(Dashboard):
    def _refresh_data(self):
        """Refresh all dashboard data."""
        try:
            # Update workflows
            st.session_state.workflows = self.orchestrator.get_all_workflows()
            
            # Update agent metrics
            st.session_state.agent_metrics = self.orchestrator.get_agent_metrics()
            
            # Update last refresh time
            self.state.last_update = datetime.now()
            
            # Show success message
            st.success("Data refreshed successfully")
            
        except Exception as e:
            logger.error(f"Failed to refresh dashboard data: {str(e)}")
            st.error("Failed to refresh data. Please try again.")
    
    async def _auto_refresh(self):
        """Auto-refresh loop for dashboard data."""
        while True:
            await asyncio.sleep(self.state.refresh_interval)
            self._refresh_data()
```

## 4. Example Usage
```python
def run_dashboard():
    # Initialize orchestrator (assuming it's already implemented)
    orchestrator = Orchestrator(knowledge_base)
    
    # Create and run dashboard
    dashboard = Dashboard(orchestrator)
    
    # Configure page
    st.set_page_config(
        page_title="Content Marketing System",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Start auto-refresh in background
    asyncio.create_task(dashboard._auto_refresh())
    
    # Render dashboard
    dashboard.render()

if __name__ == "__main__":
    run_dashboard()
```

## 5. Styling and Configuration
```python
# Custom CSS for dashboard styling
custom_css = """
<style>
    .stMetric {
        background-color: #f0f2f6;
        padding: 10px;
        border-radius: 5px;
    }
    
    .workflow-card {
        border: 1px solid #e6e6e6;
        border-radius: 5px;
        padding: 15px;
        margin: 10px 0;
    }
    
    .agent-card {
        background-color: #ffffff;
        border: 1px solid #e6e6e6;
        border-radius: 5px;
        padding: 15px;
        margin: 10px 0;
    }
    
    .status-indicator {
        display: inline-block;
        width: 10px;
        height: 10px;
        border-radius: 50%;
        margin-right: 5px;
    }
</style>
"""

# Dashboard configuration
dashboard_config = {
    "theme": {
        "primaryColor": "#FF4B4B",
        "backgroundColor": "#FFFFFF",
        "secondaryBackgroundColor": "#F0F2F6",
        "textColor": "#31333F",
        "font": "sans-serif"
    },
    "charts": {
        "colorway": ["#FF4B4B", "#45B7E8", "#FFBF00", "#32CD32"],
        "template": "plotly_white"
    }
}
```

## 6. Error Handling
```python
class DashboardError(Exception):
    """Base exception for dashboard errors."""
    pass

class DataRefreshError(DashboardError):
    """Exception raised when data refresh fails."""
    pass

class RenderError(DashboardError):
    """Exception raised when rendering fails."""
    pass

def handle_dashboard_error(func):
    """Decorator for handling dashboard errors."""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except DashboardError as e:
            st.error(f"Dashboard error: {str(e)}")
            logger.error(f"Dashboard error in {func.__name__}: {str(e)}")
        except Exception as e:
            st.error("An unexpected error occurred. Please try again.")
            logger.exception(f"Unexpected error in {func.__name__}: {str(e)}")
    return wrapper
```