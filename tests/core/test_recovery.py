"""Tests for the error handling and recovery system."""
import pytest
import asyncio
from datetime import datetime
import json
from pathlib import Path
from typing import Dict, Any
import logging

from src.core.recovery import (
    RecoveryManager,
    SystemState,
    RecoveryLevel,
    ErrorCategory,
    RecoveryAction,
    with_recovery
)

class MockError(Exception):
    """Mock error for testing."""
    pass

class ConnectionError(Exception):
    """Mock connection error."""
    pass

class StateTransitionError(Exception):
    """Mock state transition error."""
    pass

class ResourceError(Exception):
    """Mock resource error."""
    pass

@pytest.fixture
def temp_dir(tmp_path):
    """Fixture providing temporary directory."""
    return tmp_path

@pytest.fixture
def recovery_manager(temp_dir):
    """Fixture providing recovery manager instance."""
    checkpoint_dir = temp_dir / "checkpoints"
    log_dir = temp_dir / "logs"
    return RecoveryManager(
        checkpoint_dir=str(checkpoint_dir),
        log_dir=str(log_dir)
    )

@pytest.fixture
def sample_state():
    """Fixture providing sample system state."""
    return SystemState(
        workflow_states={"workflow1": "running"},
        debate_states={"debate1": "active"},
        task_states={"task1": "pending"},
        resources={"cpu": 50, "memory": 500}
    )

@pytest.mark.asyncio
async def test_error_categorization(recovery_manager: RecoveryManager):
    """Test error categorization."""
    # Test known error types
    assert recovery_manager.categorize_error(ConnectionError()) == ErrorCategory.TRANSIENT
    assert recovery_manager.categorize_error(StateTransitionError()) == ErrorCategory.STATE
    assert recovery_manager.categorize_error(ResourceError()) == ErrorCategory.RESOURCE
    
    # Test unknown error type
    assert recovery_manager.categorize_error(MockError()) == ErrorCategory.UNKNOWN

@pytest.mark.asyncio
async def test_checkpoint_creation_and_restoration(
    recovery_manager: RecoveryManager,
    sample_state: SystemState
):
    """Test checkpoint creation and restoration."""
    # Create checkpoint
    checkpoint_id = await recovery_manager.create_checkpoint(sample_state)
    
    # Verify checkpoint file exists
    checkpoint_path = Path(recovery_manager.checkpoint_dir) / f"{checkpoint_id}.json"
    assert checkpoint_path.exists()
    
    # Restore checkpoint
    restored_state = await recovery_manager.restore_checkpoint({
        "checkpoint_id": checkpoint_id
    })
    
    # Verify restored state
    assert restored_state.workflow_states == sample_state.workflow_states
    assert restored_state.debate_states == sample_state.debate_states
    assert restored_state.task_states == sample_state.task_states
    assert restored_state.resources == sample_state.resources

@pytest.mark.asyncio
async def test_recovery_actions(recovery_manager: RecoveryManager):
    """Test recovery actions for different error categories."""
    # Test retry action
    action = recovery_manager.recovery_actions[ErrorCategory.TRANSIENT]
    assert action.level == RecoveryLevel.RETRY
    assert action.max_retries == 3
    
    # Test rollback action
    action = recovery_manager.recovery_actions[ErrorCategory.STATE]
    assert action.level == RecoveryLevel.ROLLBACK
    assert action.max_retries == 1
    
    # Test checkpoint action
    action = recovery_manager.recovery_actions[ErrorCategory.RESOURCE]
    assert action.level == RecoveryLevel.CHECKPOINT
    assert action.max_retries == 2

@pytest.mark.asyncio
async def test_error_handling_with_retries(recovery_manager: RecoveryManager):
    """Test error handling with retries."""
    context = {"error_id": "test_error"}
    
    # Test handling transient error
    error = ConnectionError("Test connection error")
    
    # Should not raise on first attempts
    for _ in range(3):
        await recovery_manager.handle_error(error, context)
        assert recovery_manager.recovery_attempts[context["error_id"]] > 0
    
    # Should raise on exceeding max retries
    with pytest.raises(ConnectionError):
        await recovery_manager.handle_error(error, context)

@pytest.mark.asyncio
async def test_recovery_decorator():
    """Test recovery decorator."""
    class TestClass:
        def __init__(self):
            self.recovery_manager = RecoveryManager()
            self.call_count = 0
        
        @with_recovery({"test_context": "value"})
        async def test_method(self):
            self.call_count += 1
            if self.call_count < 3:
                raise ConnectionError("Test error")
            return "success"
    
    test_obj = TestClass()
    result = await test_obj.test_method()
    assert result == "success"
    assert test_obj.call_count == 3

@pytest.mark.asyncio
async def test_logging(recovery_manager: RecoveryManager, temp_dir: Path):
    """Test logging functionality."""
    # Verify log files are created
    system_log = temp_dir / "logs" / "system.log"
    error_log = temp_dir / "logs" / "error.log"
    
    # Generate some logs
    error = MockError("Test error")
    try:
        await recovery_manager.handle_error(
            error,
            {"test": "context"}
        )
    except MockError:
        pass
    
    # Verify logs were written
    assert system_log.exists()
    assert error_log.exists()
    
    # Check error log content
    error_content = error_log.read_text()
    assert "Test error" in error_content
    assert "context" in error_content

@pytest.mark.asyncio
async def test_state_serialization(sample_state: SystemState):
    """Test system state serialization."""
    # Convert to dict
    state_dict = sample_state.to_dict()
    
    # Verify dict structure
    assert "workflow_states" in state_dict
    assert "debate_states" in state_dict
    assert "task_states" in state_dict
    assert "resources" in state_dict
    assert "timestamp" in state_dict
    
    # Test deserialization
    restored_state = SystemState.from_dict(state_dict)
    assert restored_state.workflow_states == sample_state.workflow_states
    assert restored_state.debate_states == sample_state.debate_states
    assert restored_state.task_states == sample_state.task_states
    assert restored_state.resources == sample_state.resources

@pytest.mark.asyncio
async def test_emergency_shutdown(recovery_manager: RecoveryManager):
    """Test emergency shutdown procedure."""
    cleanup_called = False
    
    async def cleanup():
        nonlocal cleanup_called
        cleanup_called = True
    
    # Test emergency shutdown
    await recovery_manager.emergency_shutdown({
        "cleanup_func": cleanup
    })
    
    assert cleanup_called

@pytest.mark.asyncio
async def test_recovery_with_invalid_checkpoint(recovery_manager: RecoveryManager):
    """Test recovery with invalid checkpoint."""
    with pytest.raises(ValueError):
        await recovery_manager.restore_checkpoint({})
    
    with pytest.raises(FileNotFoundError):
        await recovery_manager.restore_checkpoint({
            "checkpoint_id": "nonexistent"
        })

@pytest.mark.asyncio
async def test_concurrent_recovery(
    recovery_manager: RecoveryManager,
    sample_state: SystemState
):
    """Test concurrent recovery operations."""
    # Create multiple checkpoints concurrently
    checkpoint_tasks = [
        recovery_manager.create_checkpoint(sample_state)
        for _ in range(5)
    ]
    
    checkpoint_ids = await asyncio.gather(*checkpoint_tasks)
    assert len(checkpoint_ids) == 5
    assert len(set(checkpoint_ids)) == 5  # All IDs should be unique
