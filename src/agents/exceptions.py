# src/agents/exceptions.py
class AgentError(Exception):
    """Base exception for agent-related errors."""
    pass

class ConfigurationError(AgentError):
    """Raised when there's an issue with agent configuration."""
    pass

class ExecutionError(AgentError):
    """Raised when task execution fails."""
    pass

class TaskExecutionError(ExecutionError):
    """Raised when a specific task execution fails.
    
    Attributes:
        error_result (dict): Contains details about the failed task execution
    """
    def __init__(self, message: str, error_result: dict):
        super().__init__(message)
        self.error_result = error_result
