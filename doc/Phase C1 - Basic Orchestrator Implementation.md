# Phase C1: Basic Orchestrator Technical Specification

## 1. Overview
### 1.1 Purpose
This specification details the implementation of the Basic Orchestrator component in the CrewAI Content Marketing System, responsible for coordinating agent interactions and workflow management.

### 1.2 Dependencies
```python
from typing import Dict, List, Optional, Union, Any, Callable
from pydantic import BaseModel, Field
from datetime import datetime
from loguru import logger
from crewai import Agent, Task
import asyncio
from enum import Enum
import uuid
from collections import deque
```

## 2. Data Models

### 2.1 Workflow Models
```python
class WorkflowStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"

class AgentPair(BaseModel):
    primary: Agent
    adversary: Agent
    role: str
    status: str = Field(default="idle")
    current_task: Optional[str] = None

class WorkflowStep(BaseModel):
    step_id: str
    name: str
    description: str
    agent_pair: str  # Reference to agent pair
    dependencies: List[str]  # List of step_ids that must complete before this step
    status: WorkflowStatus = WorkflowStatus.PENDING
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

class Workflow(BaseModel):
    workflow_id: str
    name: str
    description: str
    steps: List[WorkflowStep]
    status: WorkflowStatus = WorkflowStatus.PENDING
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any] = Field(default_factory=dict)
```

### 2.2 Event Models
```python
class EventType(str, Enum):
    WORKFLOW_STARTED = "workflow_started"
    WORKFLOW_COMPLETED = "workflow_completed"
    WORKFLOW_FAILED = "workflow_failed"
    STEP_STARTED = "step_started"
    STEP_COMPLETED = "step_completed"
    STEP_FAILED = "step_failed"
    AGENT_TASK_STARTED = "agent_task_started"
    AGENT_TASK_COMPLETED = "agent_task_completed"
    AGENT_TASK_FAILED = "agent_task_failed"

class Event(BaseModel):
    event_id: str
    event_type: EventType
    workflow_id: str
    step_id: Optional[str]
    agent_id: Optional[str]
    timestamp: datetime
    data: Dict[str, Any]
```

## 3. Core Orchestrator Implementation

### 3.1 Base Class
```python
class Orchestrator:
    def __init__(self, knowledge_base: Any):
        self.knowledge_base = knowledge_base
        self.agent_pairs: Dict[str, AgentPair] = {}
        self.workflows: Dict[str, Workflow] = {}
        self.event_handlers: Dict[EventType, List[Callable]] = {}
        self.event_queue = deque()
        
        self._setup_default_event_handlers()
        self._init_agent_pairs()
    
    def _setup_default_event_handlers(self):
        """Initialize default event handlers."""
        for event_type in EventType:
            self.event_handlers[event_type] = []
        
        # Add default handlers
        self.add_event_handler(EventType.WORKFLOW_STARTED, self._log_workflow_start)
        self.add_event_handler(EventType.WORKFLOW_COMPLETED, self._log_workflow_completion)
        self.add_event_handler(EventType.WORKFLOW_FAILED, self._log_workflow_failure)
    
    def _init_agent_pairs(self):
        """Initialize agent pairs for different roles."""
        # Strategy agents
        self.register_agent_pair(
            "strategy",
            StrategyAnalyst(self.knowledge_base),
            MarketSkeptic(self.knowledge_base)
        )
        
        # Marketing agents
        self.register_agent_pair(
            "marketing",
            MarketingSpecialist(self.knowledge_base),
            MarketingCritic(self.knowledge_base)
        )
        
        # Content agents
        self.register_agent_pair(
            "content",
            ContentCreator(self.knowledge_base),
            ContentReviewer(self.knowledge_base)
        )
```

### 3.2 Agent Management Methods
```python
class Orchestrator(Orchestrator):
    def register_agent_pair(
        self,
        role: str,
        primary: Agent,
        adversary: Agent
    ) -> str:
        """Register a new agent pair."""
        pair_id = str(uuid.uuid4())
        self.agent_pairs[pair_id] = AgentPair(
            primary=primary,
            adversary=adversary,
            role=role
        )
        return pair_id
    
    def get_agent_pair(self, role: str) -> Optional[AgentPair]:
        """Get agent pair by role."""
        for pair in self.agent_pairs.values():
            if pair.role == role:
                return pair
        return None
    
    async def assign_task_to_pair(
        self,
        pair_id: str,
        task: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Assign a task to an agent pair."""
        pair = self.agent_pairs.get(pair_id)
        if not pair:
            raise ValueError(f"Agent pair {pair_id} not found")
        
        pair.status = "working"
        pair.current_task = task.get("description")
        
        try:
            # Primary agent execution
            primary_result = await pair.primary.execute_task(task)
            
            # Adversary review
            review_task = {
                "description": f"Review output: {task['description']}",
                "context": primary_result
            }
            review_result = await pair.adversary.execute_task(review_task)
            
            pair.status = "idle"
            pair.current_task = None
            
            return {
                "primary_result": primary_result,
                "review_result": review_result
            }
            
        except Exception as e:
            pair.status = "error"
            logger.error(f"Task execution failed for pair {pair_id}: {str(e)}")
            raise
```

### 3.3 Workflow Management Methods
```python
class Orchestrator(Orchestrator):
    def create_workflow(
        self,
        name: str,
        description: str,
        steps: List[Dict[str, Any]]
    ) -> str:
        """Create a new workflow."""
        workflow_steps = []
        for step_data in steps:
            step = WorkflowStep(
                step_id=str(uuid.uuid4()),
                name=step_data["name"],
                description=step_data["description"],
                agent_pair=step_data["agent_pair"],
                dependencies=step_data.get("dependencies", [])
            )
            workflow_steps.append(step)
        
        workflow = Workflow(
            workflow_id=str(uuid.uuid4()),
            name=name,
            description=description,
            steps=workflow_steps,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        self.workflows[workflow.workflow_id] = workflow
        return workflow.workflow_id
    
    async def execute_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """Execute a workflow."""
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow {workflow_id} not found")
        
        workflow.status = WorkflowStatus.IN_PROGRESS
        self._emit_event(EventType.WORKFLOW_STARTED, workflow_id=workflow_id)
        
        try:
            # Track completed steps
            completed_steps = set()
            
            while len(completed_steps) < len(workflow.steps):
                for step in workflow.steps:
                    if step.step_id in completed_steps:
                        continue
                    
                    # Check dependencies
                    if not all(dep in completed_steps for dep in step.dependencies):
                        continue
                    
                    # Execute step
                    try:
                        step.status = WorkflowStatus.IN_PROGRESS
                        step.started_at = datetime.now()
                        self._emit_event(
                            EventType.STEP_STARTED,
                            workflow_id=workflow_id,
                            step_id=step.step_id
                        )
                        
                        result = await self.assign_task_to_pair(
                            step.agent_pair,
                            {"description": step.description}
                        )
                        
                        step.status = WorkflowStatus.COMPLETED
                        step.completed_at = datetime.now()
                        step.result = result
                        completed_steps.add(step.step_id)
                        
                        self._emit_event(
                            EventType.STEP_COMPLETED,
                            workflow_id=workflow_id,
                            step_id=step.step_id,
                            data=result
                        )
                        
                    except Exception as e:
                        step.status = WorkflowStatus.FAILED
                        step.error = str(e)
                        self._emit_event(
                            EventType.STEP_FAILED,
                            workflow_id=workflow_id,
                            step_id=step.step_id,
                            data={"error": str(e)}
                        )
                        raise
            
            workflow.status = WorkflowStatus.COMPLETED
            self._emit_event(
                EventType.WORKFLOW_COMPLETED,
                workflow_id=workflow_id
            )
            
            return {
                "workflow_id": workflow_id,
                "status": "completed",
                "steps": [step.dict() for step in workflow.steps]
            }
            
        except Exception as e:
            workflow.status = WorkflowStatus.FAILED
            self._emit_event(
                EventType.WORKFLOW_FAILED,
                workflow_id=workflow_id,
                data={"error": str(e)}
            )
            raise
```

### 3.4 Event Handling Methods
```python
class Orchestrator(Orchestrator):
    def add_event_handler(
        self,
        event_type: EventType,
        handler: Callable
    ):
        """Add an event handler."""
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        self.event_handlers[event_type].append(handler)
    
    def _emit_event(
        self,
        event_type: EventType,
        workflow_id: str,
        step_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None
    ):
        """Emit an event."""
        event = Event(
            event_id=str(uuid.uuid4()),
            event_type=event_type,
            workflow_id=workflow_id,
            step_id=step_id,
            agent_id=agent_id,
            timestamp=datetime.now(),
            data=data or {}
        )
        
        # Add to event queue
        self.event_queue.append(event)
        
        # Process handlers
        for handler in self.event_handlers.get(event_type, []):
            try:
                handler(event)
            except Exception as e:
                logger.error(f"Event handler failed: {str(e)}")
```

## 4. Example Usage
```python
async def example_orchestration():
    # Initialize knowledge base and orchestrator
    knowledge_base = KnowledgeBase()
    orchestrator = Orchestrator(knowledge_base)
    
    # Create a simple workflow
    workflow_id = orchestrator.create_workflow(
        name="Content Creation Pipeline",
        description="Create and review content",
        steps=[
            {
                "name": "Strategy Development",
                "description": "Develop content strategy",
                "agent_pair": "strategy",
                "dependencies": []
            },
            {
                "name": "Marketing Plan",
                "description": "Create marketing plan",
                "agent_pair": "marketing",
                "dependencies": ["strategy"]
            },
            {
                "name": "Content Creation",
                "description": "Generate content",
                "agent_pair": "content",
                "dependencies": ["marketing"]
            }
        ]
    )
    
    # Execute workflow
    try:
        result = await orchestrator.execute_workflow(workflow_id)
        print(f"Workflow completed: {result}")
    except Exception as e:
        print(f"Workflow failed: {str(e)}")

if __name__ == "__main__":
    asyncio.run(example_orchestration())
```

## 5. Error Handling and Recovery
```python
class WorkflowRecovery:
    @staticmethod
    async def recover_workflow(
        orchestrator: Orchestrator,
        workflow_id: str
    ) -> bool:
        """Attempt to recover a failed workflow."""
        workflow = orchestrator.workflows.get(workflow_id)
        if not workflow or workflow.status != WorkflowStatus.FAILED:
            return False
        
        # Find failed step
        failed_step = next(
            (step for step in workflow.steps if step.status == WorkflowStatus.FAILED),
            None
        )
        
        if not failed_step:
            return False
        
        try:
            # Reset failed step
            failed_step.status = WorkflowStatus.PENDING
            failed_step.error = None
            
            # Resume workflow
            await orchestrator.execute_workflow(workflow_id)
            return True
            
        except Exception as e:
            logger.error(f"Workflow recovery failed: {str(e)}")
            return False
```