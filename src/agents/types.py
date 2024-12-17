"""Type definitions and enums for the agent system."""
from enum import Enum, auto
from typing import (
    Dict, List, Any, Optional, TypeVar, Union, Callable,
    Protocol, TypedDict, Generic, runtime_checkable
)
from datetime import datetime

# Type variables for generic operations
T = TypeVar('T')
KT = TypeVar('KT')  # Key type
VT = TypeVar('VT')  # Value type

class AgentRole(str, Enum):
    """Defines possible agent roles."""
    STRATEGY = "strategy"
    MARKETING = "marketing"
    CONTENT = "content"
    PLANNING = "planning"
    EXECUTION = "execution"
    CRITIC = "critic"

class AgentType(str, Enum):
    """Defines possible agent types."""
    PRIMARY = "primary"
    ADVERSARY = "adversary"
    ASSISTANT = "assistant"

class TaskStatus(str, Enum):
    """Task execution status."""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"  # Changed from COMPLETED to match test expectations
    FAILED = "failed"

class ActionStatus(str, Enum):
    """Action execution status."""
    SUCCESS = "success"
    FAILED = "failed"

# Structured type definitions
class TaskResultDict(TypedDict):
    """Type definition for task execution results."""
    task: str
    result: Any
    start_time: datetime
    end_time: datetime
    duration: float
    status: str  # Uses TaskStatus string values

class MemoryItemDict(TypedDict):
    """Type definition for memory items."""
    content: Any
    timestamp: datetime
    ttl: float
    metadata: Dict[str, Any]

class ActionRecordDict(TypedDict):
    """Type definition for action records."""
    action: str
    timestamp: datetime
    duration: float
    status: str  # Uses ActionStatus string values
    error: Optional[str]
    metadata: Dict[str, Any]

class MetricsDataDict(TypedDict):
    """Type definition for metrics data."""
    total_actions: int
    successful_actions: int
    failed_actions: int
    success_rate: float
    error_rate: float
    total_duration: float
    average_response_time: float
    last_updated: datetime
    warning: Optional[str]

class ContextDict(TypedDict):
    """Type definition for context information."""
    source: str
    content: Any
    timestamp: datetime
    relevance: float

# Type aliases using structured definitions
TaskResult = TaskResultDict
MemoryItem = MemoryItemDict
ActionRecord = ActionRecordDict
MetricsData = MetricsDataDict
Context = List[ContextDict]

# Protocol definitions for callbacks
@runtime_checkable
class MetricsCallbackProtocol(Protocol):
    """Protocol for metrics callback functions."""
    def __call__(self, metrics: MetricsData) -> None: ...

@runtime_checkable
class ErrorHandlerProtocol(Protocol):
    """Protocol for error handler functions."""
    def __call__(self, error: Exception, context: Dict[str, Any]) -> None: ...

# Callback type hints using protocols
MetricsCallback = Optional[MetricsCallbackProtocol]
ErrorHandler = Optional[ErrorHandlerProtocol]

# Validation types
ValidationResult = tuple[bool, Optional[str]]

# Generic container types
class Result(Generic[T]):
    """Generic result container with success/failure status."""
    def __init__(self, success: bool, value: Optional[T] = None, error: Optional[str] = None):
        self.success = success
        self.value = value
        self.error = error

    @classmethod
    def ok(cls, value: T) -> 'Result[T]':
        """Create successful result."""
        return cls(True, value=value)

    @classmethod
    def err(cls, error: str) -> 'Result[T]':
        """Create failed result."""
        return cls(False, error=error)

    def unwrap(self) -> T:
        """Get value if success, raise error if failure."""
        if not self.success:
            raise ValueError(self.error or "Operation failed")
        return self.value

    def __len__(self) -> int:
        """Get length of value if success."""
        if not self.success or self.value is None:
            return 0
        return len(self.value)

    def __getitem__(self, key: Any) -> Any:
        """Access value item if success."""
        if not self.success or self.value is None:
            raise ValueError(self.error or "Cannot access result of failed operation")
        return self.value[key]

    def __iter__(self):
        """Iterate over value if success."""
        if not self.success or self.value is None:
            return iter([])
        return iter(self.value)

    def __bool__(self) -> bool:
        """Convert to boolean."""
        return self.success

# Type aliases for common patterns
Timestamp = datetime
Duration = float
JsonDict = Dict[str, Any]
MetadataDict = Dict[str, Any]
ValidationFunction = Callable[[Any], ValidationResult]

# Type guards
def is_task_result(obj: Any) -> bool:
    """Type guard for TaskResult."""
    return (
        isinstance(obj, dict) and
        all(k in obj for k in TaskResultDict.__annotations__)
    )

def is_memory_item(obj: Any) -> bool:
    """Type guard for MemoryItem."""
    return (
        isinstance(obj, dict) and
        all(k in obj for k in MemoryItemDict.__annotations__)
    )

def is_metrics_data(obj: Any) -> bool:
    """Type guard for MetricsData."""
    return (
        isinstance(obj, dict) and
        all(k in obj for k in MetricsDataDict.__annotations__ if k != 'warning')
    )
