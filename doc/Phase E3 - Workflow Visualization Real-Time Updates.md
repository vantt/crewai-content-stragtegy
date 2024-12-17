# Phase E3: Workflow Visualization Real-Time Updates Technical Specification

## 1. Overview
### 1.1 Purpose
This specification details the implementation of real-time updates for workflow visualizations in the CrewAI Content Marketing System.

### 1.2 Dependencies
```python
from typing import Dict, List, Optional, Union, Any, Callable
from pydantic import BaseModel, Field
import streamlit as st
import asyncio
import websockets
import json
from enum import Enum
from datetime import datetime
from loguru import logger
from concurrent.futures import ThreadPoolExecutor
```

## 2. Data Models

### 2.1 Update Models
```python
class UpdateType(str, Enum):
    """Types of visualization updates."""
    NODE_UPDATE = "node_update"
    EDGE_UPDATE = "edge_update"
    LAYOUT_UPDATE = "layout_update"
    STYLE_UPDATE = "style_update"
    COMPLETE_REFRESH = "complete_refresh"

class UpdatePriority(str, Enum):
    """Priority levels for updates."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class VisualUpdate(BaseModel):
    """Model for visualization updates."""
    update_id: str
    update_type: UpdateType
    timestamp: datetime
    priority: UpdatePriority
    target_id: str  # Node or edge ID
    changes: Dict[str, Any]
    metadata: Dict[str, Any] = Field(default_factory=dict)

class UpdateBatch(BaseModel):
    """Model for batched updates."""
    batch_id: str
    updates: List[VisualUpdate]
    timestamp: datetime
    requires_layout_update: bool = False
```

## 3. Core Implementation

### 3.1 Update Manager
```python
class VisualizationUpdateManager:
    """Manages real-time updates for workflow visualizations."""
    
    def __init__(
        self,
        visualizer: Any,
        batch_size: int = 10,
        batch_interval: float = 0.1
    ):
        self.visualizer = visualizer
        self.batch_size = batch_size
        self.batch_interval = batch_interval
        
        # Update queues for different priorities
        self.update_queues = {
            UpdatePriority.HIGH: asyncio.Queue(),
            UpdatePriority.MEDIUM: asyncio.Queue(),
            UpdatePriority.LOW: asyncio.Queue()
        }
        
        # Background tasks
        self.tasks = []
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        # Update handlers
        self.update_handlers = {
            UpdateType.NODE_UPDATE: self._handle_node_update,
            UpdateType.EDGE_UPDATE: self._handle_edge_update,
            UpdateType.LAYOUT_UPDATE: self._handle_layout_update,
            UpdateType.STYLE_UPDATE: self._handle_style_update,
            UpdateType.COMPLETE_REFRESH: self._handle_complete_refresh
        }
    
    async def start(self):
        """Start update processing."""
        self.tasks = [
            asyncio.create_task(self._process_updates(priority))
            for priority in UpdatePriority
        ]
        self.tasks.append(asyncio.create_task(self._monitor_update_queues()))
    
    async def stop(self):
        """Stop update processing."""
        for task in self.tasks:
            task.cancel()
        await asyncio.gather(*self.tasks, return_exceptions=True)
        self.executor.shutdown(wait=True)
    
    async def queue_update(self, update: VisualUpdate):
        """Queue a visualization update."""
        await self.update_queues[update.priority].put(update)
```

### 3.2 Update Processing
```python
class VisualizationUpdateManager(VisualizationUpdateManager):
    async def _process_updates(self, priority: UpdatePriority):
        """Process updates for a specific priority level."""
        queue = self.update_queues[priority]
        
        while True:
            try:
                # Collect updates for batching
                updates = []
                try:
                    while len(updates) < self.batch_size:
                        update = await asyncio.wait_for(
                            queue.get(),
                            timeout=self.batch_interval
                        )
                        updates.append(update)
                except asyncio.TimeoutError:
                    if not updates:
                        continue
                
                # Create update batch
                batch = UpdateBatch(
                    batch_id=str(uuid.uuid4()),
                    updates=updates,
                    timestamp=datetime.now(),
                    requires_layout_update=any(
                        update.update_type == UpdateType.LAYOUT_UPDATE
                        for update in updates
                    )
                )
                
                # Process batch
                await self._process_batch(batch)
                
                # Mark updates as done
                for _ in updates:
                    queue.task_done()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error processing updates: {str(e)}")
                await asyncio.sleep(1)
    
    async def _process_batch(self, batch: UpdateBatch):
        """Process a batch of updates."""
        try:
            # Sort updates by type
            updates_by_type = {}
            for update in batch.updates:
                if update.update_type not in updates_by_type:
                    updates_by_type[update.update_type] = []
                updates_by_type[update.update_type].append(update)
            
            # Process updates by type
            for update_type, updates in updates_by_type.items():
                handler = self.update_handlers[update_type]
                await handler(updates)
            
            # Update layout if needed
            if batch.requires_layout_update:
                await self._update_layout()
            
            # Trigger visualization refresh
            await self._refresh_visualization()
            
        except Exception as e:
            logger.error(f"Error processing batch {batch.batch_id}: {str(e)}")
```

### 3.3 Update Handlers
```python
class VisualizationUpdateManager(VisualizationUpdateManager):
    async def _handle_node_update(self, updates: List[VisualUpdate]):
        """Handle node updates."""
        for update in updates:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                self.executor,
                self.visualizer.update_node,
                update.target_id,
                update.changes
            )
    
    async def _handle_edge_update(self, updates: List[VisualUpdate]):
        """Handle edge updates."""
        for update in updates:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                self.executor,
                self.visualizer.update_edge,
                update.target_id,
                update.changes
            )
    
    async def _handle_layout_update(self, updates: List[VisualUpdate]):
        """Handle layout updates."""
        # Collect all layout changes
        layout_changes = {}
        for update in updates:
            layout_changes.update(update.changes)
        
        # Apply layout changes
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            self.executor,
            self.visualizer.update_layout,
            layout_changes
        )
    
    async def _handle_style_update(self, updates: List[VisualUpdate]):
        """Handle style updates."""
        for update in updates:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                self.executor,
                self.visualizer.update_style,
                update.target_id,
                update.changes
            )
    
    async def _handle_complete_refresh(self, updates: List[VisualUpdate]):
        """Handle complete visualization refresh."""
        # Only use the most recent complete refresh
        update = updates[-1]
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            self.executor,
            self.visualizer.refresh,
            update.changes
        )
```

### 3.4 WebSocket Support
```python
class VisualizationWebSocket:
    """WebSocket handler for real-time visualization updates."""
    
    def __init__(self, update_manager: VisualizationUpdateManager):
        self.update_manager = update_manager
        self.connections = set()
    
    async def handler(self, websocket, path):
        """Handle WebSocket connection."""
        try:
            # Register connection
            self.connections.add(websocket)
            
            async for message in websocket:
                try:
                    # Parse update message
                    data = json.loads(message)
                    update = VisualUpdate(
                        update_id=str(uuid.uuid4()),
                        update_type=UpdateType(data["type"]),
                        timestamp=datetime.now(),
                        priority=UpdatePriority(data.get("priority", "medium")),
                        target_id=data["target_id"],
                        changes=data["changes"],
                        metadata=data.get("metadata", {})
                    )
                    
                    # Queue update
                    await self.update_manager.queue_update(update)
                    
                    # Send acknowledgment
                    await websocket.send(json.dumps({
                        "status": "accepted",
                        "update_id": update.update_id
                    }))
                    
                except Exception as e:
                    # Send error response
                    await websocket.send(json.dumps({
                        "status": "error",
                        "error": str(e)
                    }))
        
        finally:
            # Unregister connection
            self.connections.remove(websocket)
    
    async def broadcast_update(self, update: Dict[str, Any]):
        """Broadcast update to all connected clients."""
        if not self.connections:
            return
        
        message = json.dumps(update)
        await asyncio.gather(
            *(
                connection.send(message)
                for connection in self.connections
            ),
            return_exceptions=True
        )
```

### 3.5 Integration with Streamlit
```python
class RealtimeVisualizationComponent:
    """Streamlit component for real-time visualization."""
    
    def __init__(self, dashboard: Any):
        self.dashboard = dashboard
        self.update_manager = VisualizationUpdateManager(
            self.dashboard.visualizer
        )
        self.websocket = VisualizationWebSocket(self.update_manager)
    
    async def start(self):
        """Start real-time visualization component."""
        # Start update manager
        await self.update_manager.start()
        
        # Start WebSocket server
        server = await websockets.serve(
            self.websocket.handler,
            "localhost",
            8765
        )
        
        return server
    
    def render(self):
        """Render visualization component."""
        st.header("Real-time Workflow Visualization")
        
        # Connection status
        if st.session_state.get("websocket_connected"):
            st.success("Real-time updates connected")
        else:
            st.warning("Real-time updates disconnected")
        
        # Visualization container
        viz_container = st.empty()
        
        # JavaScript for WebSocket connection
        js_code = """
        <script>
            const ws = new WebSocket('ws://localhost:8765');
            
            ws.onopen = () => {
                window.parent.postMessage({type: 'websocket_status', connected: true}, '*');
            };
            
            ws.onclose = () => {
                window.parent.postMessage({type: 'websocket_status', connected: false}, '*');
            };
            
            ws.onmessage = (event) => {
                const update = JSON.parse(event.data);
                window.parent.postMessage({type: 'visualization_update', data: update}, '*');
            };
        </script>
        """
        st.components.v1.html(js_code, height=0)
        
        # Update handler
        if st.session_state.get("_visualization_update"):
            update = st.session_state._visualization_update
            viz_container.plotly_chart(
                self.dashboard.visualizer.create_visualization(
                    update["visualization_type"],
                    update["config"]
                ),
                use_container_width=True
            )
```

## 4. Example Usage
```python
async def run_realtime_visualization():
    # Initialize dashboard
    dashboard = Dashboard(orchestrator)
    
    # Create and initialize real-time visualization component
    viz_component = RealtimeVisualizationComponent(dashboard)
    
    # Start WebSocket server
    server = await viz_component.start()
    
    try:
        # Configure Streamlit page
        st.set_page_config(
            page_title="Real-time Workflow Visualization",
            page_icon="📊",
            layout="wide"
        )
        
        # Render visualization component
        viz_component.render()
        
        # Keep server running
        await asyncio.Future()  # run forever
        
    finally:
        server.close()
        await server.wait_closed()

if __name__ == "__main__":
    asyncio.run(run_realtime_visualization())
```

## 5. Testing
```python
import pytest
import asyncio

@pytest.mark.asyncio
async def test_update_manager():
    """Test visualization update manager."""
    visualizer = MockVisualizer()
    manager = VisualizationUpdateManager(visualizer)
    
    # Start update manager
    await manager.start()
    
    try:
        # Queue test updates
        updates = [
            VisualUpdate(
                update_id=str(uuid.uuid4()),
                update_type=UpdateType.NODE_UPDATE,
                timestamp=datetime.now(),
                priority=UpdatePriority.HIGH,
                target_id=f"node_{i}",
                changes={"status": "completed"}
            )
            for i in range(5)
        ]
        
        for update in updates:
            await manager.queue_update(update)
        
        # Wait for updates to process
        await asyncio.sleep(0.5)
        
        # Verify updates were processed
        assert visualizer.update_count == 5
        assert all(
            node["status"] == "completed"
            for node in visualizer.nodes.values()
        )
        
    finally:
        await manager.stop()

@pytest.mark.asyncio
async def test_websocket_connection():
    """Test WebSocket connection and updates."""
    visualizer = MockVisualizer()
    manager = VisualizationUpdateManager(visualizer)
    websocket = VisualizationWebSocket(manager)
    
    # Start update manager
    await manager.start()
    
    try:
        # Start WebSocket server
        server = await websockets.serve(
            websocket.handler,
            "localhost",
            8765
        )
        
        # Connect test client
        async with websockets.connect("ws://localhost:8765") as ws:
            # Send test update
            await ws.send(json.dumps({
                "type": "node_update",
                "target_id": "test_node",
                "changes": {"status": "completed"}
            }))
            
            # Verify response
            response = json.loads(await ws.recv())
            assert response["status"] == "accepted"
            
            # Verify update was processed
            await asyncio.sleep(0.5)
            assert visualizer.nodes["test_node"]["status"] == "completed"
        
        server.close()
        await server.wait_closed()
        
    finally: