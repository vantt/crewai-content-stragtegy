"""
Phase C3: Workflow Management Technical Specification

This specification details the implementation of the Workflow Management component
in the CrewAI Content Marketing System, responsible for orchestrating and managing
complex workflows across agent pairs.
"""

from typing import Dict, List, Optional, Union, Any, Callable, Set
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
from loguru import logger
import asyncio
from enum import Enum
import uuid
from dataclasses import dataclass
from collections import defaultdict

# Data Models
class WorkflowStatus(str, Enum):
    """Status states for workflows."""
    PENDING = "pending"
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class TaskPriority(str, Enum):
    """Priority levels for workflow tasks."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class TaskStatus(str, Enum):
    """Status states for individual tasks."""
    PENDING = "pending"
    READY = "ready"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"
    SKIPPED = "skipped"

class WorkflowTask(BaseModel):
    """Model for individual workflow tasks."""
    task_id: str
    workflow_id: str
    name: str
    description: str
    agent_pair_id: str
    priority: TaskPriority
    dependencies: List[str] = Field(default_factory=list)
    status: TaskStatus = TaskStatus.PENDING
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    timeout: Optional[int] = None  # in seconds
    retry_count: int = 0
    max_retries: int = 3
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class WorkflowTemplate(BaseModel):
    """Model for workflow templates."""
    template_id: str
    name: str
    description: str
    tasks: List[WorkflowTask]
    default_timeout: int = 3600  # Default 1 hour timeout
    metadata: Dict[str, Any] = Field(default_factory=dict)

class Workflow(BaseModel):
    """Model for workflow instances."""
    workflow_id: str
    template_id: Optional[str]
    name: str
    description: str
    status: WorkflowStatus
    tasks: List[WorkflowTask]
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    priority: TaskPriority
    timeout: int  # in seconds
    execution_context: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class WorkflowEvent(BaseModel):
    """Model for workflow-related events."""
    event_id: str
    workflow_id: str
    task_id: Optional[str]
    event_type: str
    timestamp: datetime
    data: Dict[str, Any]

# Workflow Manager Implementation
class WorkflowManager:
    """Core workflow management system."""
    
    def __init__(
        self,
        knowledge_base: Any,
        orchestrator: Any,
        max_concurrent_workflows: int = 10
    ):
        self.knowledge_base = knowledge_base
        self.orchestrator = orchestrator
        self.max_concurrent_workflows = max_concurrent_workflows
        
        # Storage
        self.templates: Dict[str, WorkflowTemplate] = {}
        self.workflows: Dict[str, Workflow] = {}
        self.task_queue: asyncio.PriorityQueue = asyncio.PriorityQueue()
        self.running_workflows: Set[str] = set()
        
        # Event handling
        self.event_handlers: Dict[str, List[Callable]] = defaultdict(list)
        self.event_queue: asyncio.Queue = asyncio.Queue()
        
        # Task execution
        self.task_executors: Dict[str, Callable] = {}
        self._register_default_executors()
    
    def _register_default_executors(self):
        """Register default task executors."""
        self.task_executors.update({
            "strategy_analysis": self._execute_strategy_task,
            "marketing_plan": self._execute_marketing_task,
            "content_creation": self._execute_content_task,
            "debate_session": self._execute_debate_task
        })
    
    async def create_workflow_template(
        self,
        name: str,
        description: str,
        tasks: List[Dict[str, Any]],
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Create a new workflow template."""
        template_id = str(uuid.uuid4())
        
        # Convert task dictionaries to WorkflowTask objects
        workflow_tasks = []
        for task_data in tasks:
            task = WorkflowTask(
                task_id=str(uuid.uuid4()),
                workflow_id="",  # Will be set when workflow is created
                name=task_data["name"],
                description=task_data["description"],
                agent_pair_id=task_data["agent_pair_id"],
                priority=TaskPriority(task_data.get("priority", "medium")),
                dependencies=task_data.get("dependencies", []),
                timeout=task_data.get("timeout"),
                max_retries=task_data.get("max_retries", 3),
                metadata=task_data.get("metadata", {})
            )
            workflow_tasks.append(task)
        
        template = WorkflowTemplate(
            template_id=template_id,
            name=name,
            description=description,
            tasks=workflow_tasks,
            metadata=metadata or {}
        )
        
        self.templates[template_id] = template
        return template_id
    
    async def create_workflow(
        self,
        name: str,
        description: str,
        template_id: Optional[str] = None,
        tasks: Optional[List[Dict[str, Any]]] = None,
        priority: TaskPriority = TaskPriority.MEDIUM,
        timeout: int = 3600,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Create a new workflow instance."""
        if not template_id and not tasks:
            raise ValueError("Either template_id or tasks must be provided")
        
        workflow_id = str(uuid.uuid4())
        
        if template_id:
            template = self.templates.get(template_id)
            if not template:
                raise ValueError(f"Template {template_id} not found")
            workflow_tasks = [
                task.copy(update={"workflow_id": workflow_id})
                for task in template.tasks
            ]
        else:
            workflow_tasks = [
                WorkflowTask(
                    task_id=str(uuid.uuid4()),
                    workflow_id=workflow_id,
                    **task
                )
                for task in tasks
            ]
        
        workflow = Workflow(
            workflow_id=workflow_id,
            template_id=template_id,
            name=name,
            description=description,
            status=WorkflowStatus.PENDING,
            tasks=workflow_tasks,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            priority=priority,
            timeout=timeout,
            metadata=metadata or {}
        )
        
        self.workflows[workflow_id] = workflow
        await self._emit_event("workflow_created", workflow_id=workflow_id)
        
        return workflow_id
    
    async def start_workflow(self, workflow_id: str) -> Workflow:
        """Start executing a workflow."""
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow {workflow_id} not found")
        
        if workflow.status != WorkflowStatus.PENDING:
            raise ValueError(f"Workflow {workflow_id} is not in PENDING state")
        
        if len(self.running_workflows) >= self.max_concurrent_workflows:
            raise RuntimeError("Maximum concurrent workflows reached")
        
        try:
            workflow.status = WorkflowStatus.IN_PROGRESS
            workflow.updated_at = datetime.now()
            self.running_workflows.add(workflow_id)
            
            # Queue initial tasks (those with no dependencies)
            initial_tasks = [
                task for task in workflow.tasks
                if not task.dependencies
            ]
            
            for task in initial_tasks:
                await self._queue_task(task)
            
            await self._emit_event("workflow_started", workflow_id=workflow_id)
            
            # Start task execution loop if not already running
            asyncio.create_task(self._execute_tasks())
            
            return workflow
            
        except Exception as e:
            workflow.status = WorkflowStatus.FAILED
            await self._emit_event(
                "workflow_failed",
                workflow_id=workflow_id,
                data={"error": str(e)}
            )
            raise
    
    async def _queue_task(self, task: WorkflowTask):
        """Queue a task for execution."""
        # Priority tuple: (priority value, timestamp)
        priority_values = {
            TaskPriority.LOW: 3,
            TaskPriority.MEDIUM: 2,
            TaskPriority.HIGH: 1,
            TaskPriority.CRITICAL: 0
        }
        
        await self.task_queue.put(
            (priority_values[task.priority], datetime.now().timestamp(), task)
        )
    
    async def _execute_tasks(self):
        """Main task execution loop."""
        while True:
            try:
                _, _, task = await self.task_queue.get()
                
                workflow = self.workflows[task.workflow_id]
                if workflow.status != WorkflowStatus.IN_PROGRESS:
                    continue
                
                # Execute task
                try:
                    task.status = TaskStatus.IN_PROGRESS
                    task.start_time = datetime.now()
                    
                    executor = self.task_executors.get(
                        task.metadata.get("executor", "default"),
                        self._execute_default_task
                    )
                    
                    result = await asyncio.wait_for(
                        executor(task),
                        timeout=task.timeout or workflow.timeout
                    )
                    
                    task.status = TaskStatus.COMPLETED
                    task.end_time = datetime.now()
                    task.result = result
                    
                    await self._emit_event(
                        "task_completed",
                        workflow_id=workflow.workflow_id,
                        task_id=task.task_id,
                        data={"result": result}
                    )
                    
                    # Queue dependent tasks
                    await self._queue_dependent_tasks(workflow, task)
                    
                except Exception as e:
                    task.status = TaskStatus.FAILED
                    task.error = str(e)
                    task.end_time = datetime.now()
                    
                    if task.retry_count < task.max_retries:
                        task.retry_count += 1
                        task.status = TaskStatus.PENDING
                        await self._queue_task(task)
                    else:
                        await self._handle_task_failure(workflow, task)
                
                finally:
                    self.task_queue.task_done()
                    
            except Exception as e:
                logger.error(f"Task execution loop error: {str(e)}")
                await asyncio.sleep(1)
    
    async def _queue_dependent_tasks(self, workflow: Workflow, completed_task: WorkflowTask):
        """Queue tasks that depend on the completed task."""
        for task in workflow.tasks:
            if completed_task.task_id in task.dependencies:
                # Check if all dependencies are completed
                dependencies_met = all(
                    any(t.task_id == dep and t.status == TaskStatus.COMPLETED
                        for t in workflow.tasks)
                    for dep in task.dependencies
                )
                
                if dependencies_met:
                    task.status = TaskStatus.READY
                    await self._queue_task(task)
    
    async def _handle_task_failure(self, workflow: Workflow, failed_task: WorkflowTask):
        """Handle task failure and workflow implications."""
        await self._emit_event(
            "task_failed",
            workflow_id=workflow.workflow_id,
            task_id=failed_task.task_id,
            data={"error": failed_task.error}
        )
        
        # Mark dependent tasks as blocked
        for task in workflow.tasks:
            if failed_task.task_id in task.dependencies:
                task.status = TaskStatus.BLOCKED
        
        # Check workflow completion status
        incomplete_tasks = [
            task for task in workflow.tasks
            if task.status not in (TaskStatus.COMPLETED, TaskStatus.SKIPPED)
        ]
        
        if not incomplete_tasks:
            await self._complete_workflow(workflow)
        elif all(task.status in (TaskStatus.FAILED, TaskStatus.BLOCKED)
                for task in incomplete_tasks):
            workflow.status = WorkflowStatus.FAILED
            await self._emit_event(
                "workflow_failed",
                workflow_id=workflow.workflow_id,
                data={"failed_task": failed_task.task_id}
            )
    
    async def _complete_workflow(self, workflow: Workflow):
        """Mark workflow as completed and perform cleanup."""
        workflow.status = WorkflowStatus.COMPLETED
        workflow.completed_at = datetime.now()
        workflow.updated_at = datetime.now()
        
        self.running_workflows.remove(workflow.workflow_id)
        
        await self._emit_event(
            "workflow_completed",
            workflow_id=workflow.workflow_id
        )
    
    async def _emit_event(
        self,
        event_type: str,
        workflow_id: str,
        task_id: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None
    ):
        """Emit a workflow event."""
        event = WorkflowEvent(
            event_id=str(uuid.uuid4()),
            workflow_id=workflow_id,
            task_id=task_id,
            event_type=event_type,
            timestamp=datetime.now(),
            data=data or {}
        )
        
        await self.event_queue.put(event)
        
        # Process handlers
        for handler in self.event_handlers[event_type]:
            try:
                await handler(event)
            except Exception as e:
                logger.error(f"Event handler error: {str(e)}")
    
    # Task Executors
    async def _execute_default_task(self, task: WorkflowTask) -> Dict[str, Any]:
        """Default task executor."""
        return await self.orchestrator.execute_agent_task(
            task.agent_pair_id,
            {
                "task_id": task.task_id,
                "name": task.name,
                "description": task.description,
                "metadata": task.metadata
            }
        )
    
    async def _execute_strategy_task(self, task: WorkflowTask) -> Dict[str, Any]:
        """Execute strategy-related task."""
        return await self.orchestrator.execute_strategy_analysis(
            task.agent_pair_id,
            task.metadata.get("analysis_parameters", {})
        )
    
    async def _execute_marketing_task