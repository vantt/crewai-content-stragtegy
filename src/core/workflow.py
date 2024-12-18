"""Workflow management system for coordinating debates and tasks.

This module implements workflow management capabilities including:
- Task scheduling
- Dependency management
- Resource monitoring
- Workflow execution tracking
"""
from typing import Dict, List, Optional, Set, Any
from datetime import datetime
import asyncio
import uuid
from pydantic import BaseModel, Field

from .events import EventEmitter, Event, EventType
from .state import StateManager, WorkflowStatus, TaskStatus

class ResourceUsage(BaseModel):
    """Model for tracking resource usage."""
    cpu_percent: float = 0.0
    memory_mb: float = 0.0
    active_tasks: int = 0
    queued_tasks: int = 0

class TaskDefinition(BaseModel):
    """Model for defining workflow tasks."""
    task_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    agent_pair_id: str
    dependencies: List[str] = Field(default_factory=list)
    estimated_duration: Optional[int] = None  # in seconds
    required_resources: Dict[str, float] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class WorkflowDefinition(BaseModel):
    """Model for defining workflows."""
    workflow_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    tasks: List[TaskDefinition]
    max_parallel_tasks: int = 1
    timeout: Optional[int] = None  # in seconds
    metadata: Dict[str, Any] = Field(default_factory=dict)

class WorkflowManager:
    """Manages workflow execution and resource allocation."""
    
    def __init__(
        self,
        event_emitter: EventEmitter,
        state_manager: StateManager,
        max_concurrent_workflows: int = 5
    ):
        """Initialize workflow manager.
        
        Args:
            event_emitter: System event emitter
            state_manager: System state manager
            max_concurrent_workflows: Maximum number of concurrent workflows
        """
        self.event_emitter = event_emitter
        self.state_manager = state_manager
        self.max_concurrent_workflows = max_concurrent_workflows
        
        # Workflow tracking
        self.workflows: Dict[str, WorkflowDefinition] = {}
        self.active_workflows: Set[str] = set()
        self.task_queue: asyncio.PriorityQueue = asyncio.PriorityQueue()
        
        # Resource tracking
        self.resource_usage = ResourceUsage()
        self._resource_lock = asyncio.Lock()

    async def create_workflow(
        self,
        name: str,
        description: str,
        tasks: List[TaskDefinition],
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Create a new workflow definition.
        
        Args:
            name: Workflow name
            description: Workflow description
            tasks: List of task definitions
            metadata: Optional metadata
            
        Returns:
            Workflow ID
        """
        workflow = WorkflowDefinition(
            name=name,
            description=description,
            tasks=tasks,
            metadata=metadata or {}
        )
        
        self.workflows[workflow.workflow_id] = workflow
        return workflow.workflow_id

    async def validate_workflow(self, workflow_id: str) -> bool:
        """Validate workflow configuration.
        
        Args:
            workflow_id: Workflow to validate
            
        Returns:
            True if valid
            
        Raises:
            ValueError: If validation fails
        """
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow {workflow_id} not found")
        
        # Check for dependency cycles
        task_ids = {task.task_id for task in workflow.tasks}
        for task in workflow.tasks:
            for dep_id in task.dependencies:
                if dep_id not in task_ids:
                    raise ValueError(
                        f"Task {task.task_id} depends on non-existent task {dep_id}"
                    )
        
        # Validate resource requirements
        total_resources = {
            resource: sum(task.required_resources.get(resource, 0.0)
                        for task in workflow.tasks)
            for resource in set().union(
                *(task.required_resources.keys() for task in workflow.tasks)
            )
        }
        
        # Could add more validation here
        
        return True

    async def start_workflow(self, workflow_id: str) -> None:
        """Start executing a workflow.
        
        Args:
            workflow_id: Workflow to start
            
        Raises:
            ValueError: If workflow not found or invalid
            RuntimeError: If too many workflows running
        """
        if len(self.active_workflows) >= self.max_concurrent_workflows:
            raise RuntimeError("Maximum concurrent workflows reached")
        
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow {workflow_id} not found")
        
        # Validate workflow
        await self.validate_workflow(workflow_id)
        
        # Set initial state
        await self.state_manager.set_workflow_state(
            workflow_id,
            WorkflowStatus.IN_PROGRESS
        )
        
        self.active_workflows.add(workflow_id)
        
        # Queue initial tasks (those with no dependencies)
        initial_tasks = [
            task for task in workflow.tasks
            if not task.dependencies
        ]
        
        for task in initial_tasks:
            await self._queue_task(workflow_id, task)
        
        # Start execution if not already running
        asyncio.create_task(self._execute_tasks())

    async def _queue_task(
        self,
        workflow_id: str,
        task: TaskDefinition,
        priority: int = 1
    ) -> None:
        """Queue a task for execution.
        
        Args:
            workflow_id: Workflow ID
            task: Task to queue
            priority: Task priority (lower is higher priority)
        """
        await self.task_queue.put((
            priority,
            workflow_id,
            task
        ))
        
        async with self._resource_lock:
            self.resource_usage.queued_tasks += 1

    async def _execute_tasks(self) -> None:
        """Execute queued tasks."""
        while True:
            try:
                # Get next task
                priority, workflow_id, task = await self.task_queue.get()
                
                # Update resource tracking
                async with self._resource_lock:
                    self.resource_usage.queued_tasks -= 1
                    self.resource_usage.active_tasks += 1
                
                try:
                    # Set task state
                    await self.state_manager.set_task_state(
                        task.task_id,
                        TaskStatus.IN_PROGRESS
                    )
                    
                    # Emit task started event
                    await self.event_emitter.emit(Event(
                        event_type=EventType.STEP_STARTED,
                        workflow_id=workflow_id,
                        step_id=task.task_id,
                        data={
                            "task_name": task.name,
                            "agent_pair": task.agent_pair_id
                        }
                    ))
                    
                    # Execute task (implementation will vary)
                    # For now, just simulate task execution
                    if task.estimated_duration:
                        await asyncio.sleep(task.estimated_duration)
                    
                    # Update task state
                    await self.state_manager.set_task_state(
                        task.task_id,
                        TaskStatus.COMPLETED
                    )
                    
                    # Emit completion event
                    await self.event_emitter.emit(Event(
                        event_type=EventType.STEP_COMPLETED,
                        workflow_id=workflow_id,
                        step_id=task.task_id,
                        data={"status": "completed"}
                    ))
                    
                    # Queue dependent tasks
                    workflow = self.workflows[workflow_id]
                    completed_tasks = {
                        t.task_id for t in workflow.tasks
                        if self.state_manager.get_task_state(t.task_id) == TaskStatus.COMPLETED
                    }
                    
                    for next_task in workflow.tasks:
                        if (next_task.task_id != task.task_id and
                            all(dep in completed_tasks for dep in next_task.dependencies)):
                            await self._queue_task(workflow_id, next_task)
                    
                    # Check if workflow is complete
                    if completed_tasks == {t.task_id for t in workflow.tasks}:
                        await self.state_manager.set_workflow_state(
                            workflow_id,
                            WorkflowStatus.COMPLETED
                        )
                        self.active_workflows.remove(workflow_id)
                
                except Exception as e:
                    # Handle task failure
                    await self.state_manager.set_task_state(
                        task.task_id,
                        TaskStatus.FAILED
                    )
                    
                    await self.event_emitter.emit(Event(
                        event_type=EventType.STEP_FAILED,
                        workflow_id=workflow_id,
                        step_id=task.task_id,
                        data={"error": str(e)}
                    ))
                
                finally:
                    # Update resource tracking
                    async with self._resource_lock:
                        self.resource_usage.active_tasks -= 1
                    
                    # Mark task as done
                    self.task_queue.task_done()
            
            except Exception as e:
                print(f"Error in task execution loop: {str(e)}")
                await asyncio.sleep(1)

    async def pause_workflow(self, workflow_id: str) -> None:
        """Pause a running workflow.
        
        Args:
            workflow_id: Workflow to pause
        """
        if workflow_id not in self.active_workflows:
            raise ValueError(f"Workflow {workflow_id} not active")
        
        await self.state_manager.set_workflow_state(
            workflow_id,
            WorkflowStatus.PAUSED
        )

    async def resume_workflow(self, workflow_id: str) -> None:
        """Resume a paused workflow.
        
        Args:
            workflow_id: Workflow to resume
        """
        current_state = self.state_manager.get_workflow_state(workflow_id)
        if current_state != WorkflowStatus.PAUSED:
            raise ValueError(f"Workflow {workflow_id} not paused")
        
        await self.state_manager.set_workflow_state(
            workflow_id,
            WorkflowStatus.IN_PROGRESS
        )

    async def cancel_workflow(self, workflow_id: str) -> None:
        """Cancel a workflow.
        
        Args:
            workflow_id: Workflow to cancel
        """
        if workflow_id not in self.workflows:
            raise ValueError(f"Workflow {workflow_id} not found")
        
        await self.state_manager.set_workflow_state(
            workflow_id,
            WorkflowStatus.CANCELLED
        )
        
        if workflow_id in self.active_workflows:
            self.active_workflows.remove(workflow_id)

    def get_resource_usage(self) -> ResourceUsage:
        """Get current resource usage.
        
        Returns:
            Current resource usage stats
        """
        return self.resource_usage

    def get_workflow_status(self, workflow_id: str) -> Optional[WorkflowStatus]:
        """Get workflow status.
        
        Args:
            workflow_id: Workflow to check
            
        Returns:
            Current workflow status or None if not found
        """
        return self.state_manager.get_workflow_state(workflow_id)
