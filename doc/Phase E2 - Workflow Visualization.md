# Phase E2: Workflow Visualization Technical Specification

## 1. Overview
### 1.1 Purpose
This specification details the implementation of the Workflow Visualization component for the CrewAI Content Marketing System, providing interactive visualizations of workflow states, dependencies, and progress.

### 1.2 Dependencies
```python
from typing import Dict, List, Optional, Union, Any
from pydantic import BaseModel, Field
import streamlit as st
import networkx as nx
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
from enum import Enum
from loguru import logger
```

## 2. Data Models

### 2.1 Visualization Models
```python
class VisualizationType(str, Enum):
    """Types of workflow visualizations."""
    GRAPH = "graph"
    GANTT = "gantt"
    TIMELINE = "timeline"
    SANKEY = "sankey"
    HEATMAP = "heatmap"

class NodeStyle(BaseModel):
    """Style configuration for workflow nodes."""
    color: str
    size: int
    shape: str
    border_color: str = Field(alias="borderColor")
    border_width: int = Field(alias="borderWidth")
    label_position: str = Field(alias="labelPosition")
    font_size: int = Field(alias="fontSize")

class EdgeStyle(BaseModel):
    """Style configuration for workflow edges."""
    color: str
    width: int
    style: str  # "solid", "dashed", "dotted"
    arrow_size: int = Field(alias="arrowSize")
    curve_style: str = Field(alias="curveStyle")

class VisualElement(BaseModel):
    """Base model for visual elements."""
    id: str
    type: str
    position: Dict[str, float]
    data: Dict[str, Any]
    style: Dict[str, Any]
    
class VisualizationLayout(BaseModel):
    """Layout configuration for visualizations."""
    algorithm: str
    spacing: int
    padding: int
    orientation: str
    node_spacing: int = Field(alias="nodeSpacing")
    layer_spacing: int = Field(alias="layerSpacing")
    fit_padding: int = Field(alias="fitPadding")
```

## 3. Core Implementation

### 3.1 Visualization Manager
```python
class WorkflowVisualizer:
    def __init__(self, workflow_data: Dict[str, Any]):
        self.workflow_data = workflow_data
        self.graph = nx.DiGraph()
        self.layout_engine = LayoutEngine()
        self.style_manager = StyleManager()
        self._initialize_graph()
    
    def _initialize_graph(self):
        """Initialize the graph structure from workflow data."""
        # Add nodes
        for task in self.workflow_data["tasks"]:
            self.graph.add_node(
                task["id"],
                **{
                    "label": task["name"],
                    "status": task["status"],
                    "type": task["type"],
                    "duration": task["duration"],
                    "progress": task["progress"]
                }
            )
        
        # Add edges
        for task in self.workflow_data["tasks"]:
            for dep in task.get("dependencies", []):
                self.graph.add_edge(
                    dep,
                    task["id"],
                    **{
                        "type": "dependency",
                        "status": "active"
                    }
                )
    
    def create_visualization(
        self,
        viz_type: VisualizationType,
        config: Optional[Dict[str, Any]] = None
    ) -> go.Figure:
        """Create a visualization based on the specified type."""
        if viz_type == VisualizationType.GRAPH:
            return self._create_graph_visualization(config)
        elif viz_type == VisualizationType.GANTT:
            return self._create_gantt_visualization(config)
        elif viz_type == VisualizationType.TIMELINE:
            return self._create_timeline_visualization(config)
        elif viz_type == VisualizationType.SANKEY:
            return self._create_sankey_visualization(config)
        elif viz_type == VisualizationType.HEATMAP:
            return self._create_heatmap_visualization(config)
        else:
            raise ValueError(f"Unsupported visualization type: {viz_type}")
```

### 3.2 Graph Visualization
```python
class WorkflowVisualizer(WorkflowVisualizer):
    def _create_graph_visualization(
        self, 
        config: Optional[Dict[str, Any]] = None
    ) -> go.Figure:
        """Create an interactive graph visualization."""
        # Get layout
        pos = self.layout_engine.compute_layout(self.graph, config)
        
        # Create figure
        fig = go.Figure()
        
        # Add edges
        edge_trace = go.Scatter(
            x=[],
            y=[],
            line=dict(width=1, color="#888"),
            hoverinfo="none",
            mode="lines"
        )
        
        for edge in self.graph.edges():
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            edge_trace["x"] += (x0, x1, None)
            edge_trace["y"] += (y0, y1, None)
        
        fig.add_trace(edge_trace)
        
        # Add nodes
        node_trace = go.Scatter(
            x=[pos[node][0] for node in self.graph.nodes()],
            y=[pos[node][1] for node in self.graph.nodes()],
            mode="markers+text",
            hoverinfo="text",
            text=[self.graph.nodes[node]["label"] for node in self.graph.nodes()],
            marker=dict(
                size=20,
                color=[self.style_manager.get_node_color(
                    self.graph.nodes[node]["status"]
                ) for node in self.graph.nodes()],
                line=dict(width=2)
            )
        )
        
        fig.add_trace(node_trace)
        
        # Update layout
        fig.update_layout(
            showlegend=False,
            hovermode="closest",
            margin=dict(b=20, l=5, r=5, t=40),
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
        )
        
        return fig
```

### 3.3 Gantt Chart Visualization
```python
class WorkflowVisualizer(WorkflowVisualizer):
    def _create_gantt_visualization(
        self,
        config: Optional[Dict[str, Any]] = None
    ) -> go.Figure:
        """Create a Gantt chart visualization."""
        tasks = []
        
        for node in self.graph.nodes():
            node_data = self.graph.nodes[node]
            
            # Calculate start and end dates
            start_date = node_data.get("start_time", datetime.now())
            duration = node_data.get("duration", 0)
            end_date = start_date + timedelta(seconds=duration)
            
            tasks.append(dict(
                Task=node_data["label"],
                Start=start_date,
                Finish=end_date,
                Status=node_data["status"],
                Progress=node_data.get("progress", 0),
                Dependencies=",".join(
                    self.graph.nodes[pred]["label"]
                    for pred in self.graph.predecessors(node)
                )
            ))
        
        fig = go.Figure()
        
        # Add bars
        for task in tasks:
            fig.add_trace(go.Bar(
                x=[task["Finish"] - task["Start"]],
                y=[task["Task"]],
                orientation="h",
                marker=dict(
                    color=self.style_manager.get_node_color(task["Status"]),
                    pattern=dict(
                        shape="/"*int(task["Progress"]/10),
                        solidity=0.5
                    )
                ),
                showlegend=False
            ))
        
        # Update layout
        fig.update_layout(
            title="Workflow Gantt Chart",
            height=400,
            xaxis=dict(
                title="Time",
                showgrid=True,
                zeroline=True,
                type="date"
            ),
            yaxis=dict(
                title="Tasks",
                showgrid=True,
                zeroline=True
            ),
            barmode="stack"
        )
        
        return fig
```

### 3.4 Timeline Visualization
```python
class WorkflowVisualizer(WorkflowVisualizer):
    def _create_timeline_visualization(
        self,
        config: Optional[Dict[str, Any]] = None
    ) -> go.Figure:
        """Create a timeline visualization."""
        events = []
        
        # Collect all events
        for node in self.graph.nodes():
            node_data = self.graph.nodes[node]
            
            # Add task start
            events.append(dict(
                Task=node_data["label"],
                Time=node_data.get("start_time", datetime.now()),
                Event="start",
                Status=node_data["status"]
            ))
            
            # Add task completion
            if node_data["status"] in ["completed", "failed"]:
                events.append(dict(
                    Task=node_data["label"],
                    Time=node_data.get("end_time", datetime.now()),
                    Event="end",
                    Status=node_data["status"]
                ))
        
        # Sort events by time
        events.sort(key=lambda x: x["Time"])
        
        fig = go.Figure()
        
        # Add events
        fig.add_trace(go.Scatter(
            x=[event["Time"] for event in events],
            y=[event["Task"] for event in events],
            mode="markers+text",
            marker=dict(
                size=10,
                symbol=[
                    "circle" if event["Event"] == "start" else "square"
                    for event in events
                ],
                color=[
                    self.style_manager.get_node_color(event["Status"])
                    for event in events
                ]
            ),
            text=[
                f"{event['Event'].capitalize()}: {event['Status']}"
                for event in events
            ],
            textposition="top center"
        ))
        
        # Update layout
        fig.update_layout(
            title="Workflow Timeline",
            height=400,
            xaxis=dict(
                title="Time",
                showgrid=True,
                zeroline=True,
                type="date"
            ),
            yaxis=dict(
                title="Tasks",
                showgrid=True,
                zeroline=True
            )
        )
        
        return fig
```

### 3.5 Layout Engine
```python
class LayoutEngine:
    """Handles graph layout calculations."""
    
    def compute_layout(
        self,
        graph: nx.DiGraph,
        config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, tuple]:
        """Compute node positions for visualization."""
        config = config or {}
        algorithm = config.get("algorithm", "sugiyama")
        
        if algorithm == "sugiyama":
            return self._compute_sugiyama_layout(graph, config)
        elif algorithm == "spring":
            return self._compute_spring_layout(graph, config)
        elif algorithm == "circular":
            return self._compute_circular_layout(graph, config)
        else:
            raise ValueError(f"Unsupported layout algorithm: {algorithm}")
    
    def _compute_sugiyama_layout(
        self,
        graph: nx.DiGraph,
        config: Dict[str, Any]
    ) -> Dict[str, tuple]:
        """Compute hierarchical layout using Sugiyama algorithm."""
        return nx.multipartite_layout(
            graph,
            subset_key="layer",
            scale=config.get("scale", 1.0),
            align=config.get("align", "horizontal")
        )
    
    def _compute_spring_layout(
        self,
        graph: nx.DiGraph,
        config: Dict[str, Any]
    ) -> Dict[str, tuple]:
        """Compute force-directed layout."""
        return nx.spring_layout(
            graph,
            k=config.get("k", None),
            iterations=config.get("iterations", 50)
        )
    
    def _compute_circular_layout(
        self,
        graph: nx.DiGraph,
        config: Dict[str, Any]
    ) -> Dict[str, tuple]:
        """Compute circular layout."""
        return nx.circular_layout(
            graph,
            scale=config.get("scale", 1.0),
            center=config.get("center", None)
        )
```

### 3.6 Style Manager
```python
class StyleManager:
    """Manages visual styling for workflow elements."""
    
    def __init__(self):
        self.status_colors = {
            "pending": "#808080",
            "in_progress": "#FFA500",
            "completed": "#008000",
            "failed": "#FF0000",
            "blocked": "#000000"
        }
        
        self.node_styles = {
            "default": NodeStyle(
                color="#FFFFFF",
                size=30,
                shape="circle",
                borderColor="#000000",
                borderWidth=2,
                labelPosition="center",
                fontSize=12
            )
        }
        
        self.edge_styles = {
            "default": EdgeStyle(
                color="#888888",
                width=1,
                style="solid",
                arrowSize=10,
                curveStyle="bezier"
            )
        }
    
    def get_node_color(self, status: str) -> str:
        """Get color for node based on status."""
        return self.status_colors.get(status, self.status_colors["pending"])
    
    def get_node_style(self, node_type: str) -> NodeStyle:
        """Get style configuration for node."""
        return self.node_styles.get(node_type, self.node_styles["default"])
    
    def get_edge_style(self, edge_type: str) -> EdgeStyle:
        """Get style configuration for edge."""
        return self.edge_styles.get(edge_type, self.edge_styles["default"])
```

## 4. Integration with Dashboard

### 4.1 Visualization Component
```python
class WorkflowVisualizationComponent:
    def __init__(self, dashboard: Any):
        self.dashboard = dashboard
        self.visualizer = None
    
    def render(self):
        """Render workflow visualization component."""
        st.header("Workflow Visualization")
        
        # Visualization type selector
        viz_type = st.selectbox(
            "Visualization Type",
            options=[v.value for v in VisualizationType]
        )
        
        # Configuration options
        with st.expander("Visualization Settings"):
            config = self._render_config_options(viz_type)
        
        # Get current workflow data
        workflow_data = self._get_workflow_data()
        
        if workflow_data:
            # Initialize visualizer if needed
            if not self.visualizer:
                self.visualizer = WorkflowVisualizer(workflow_data)
            
            # Create and display visualization
            fig = self.visualizer.create_visualization(
                VisualizationType(viz_type),
                config
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No workflow data available for visualization")