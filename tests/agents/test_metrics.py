"""Tests for agent performance metrics."""
import pytest
from datetime import datetime, timedelta
from src.agents.metrics import AgentMetrics

@pytest.fixture
def metrics():
    return AgentMetrics()

def test_metrics_initialization(metrics):
    """Test metrics initialization."""
    assert metrics.action_history == []
    assert metrics.latest_metrics == {}

def test_log_action(metrics):
    """Test action logging."""
    start_time = datetime.now()
    metrics.log_action(
        action_name="test_action",
        start_time=start_time,
        status="success",
        extra_data="test"
    )
    
    history = metrics.action_history
    assert len(history) == 1
    assert history[0]["action"] == "test_action"
    assert history[0]["status"] == "success"
    assert history[0]["extra_data"] == "test"
    assert isinstance(history[0]["duration"], float)

def test_log_failed_action(metrics):
    """Test logging failed actions."""
    start_time = datetime.now()
    metrics.log_action(
        action_name="failed_action",
        start_time=start_time,
        status="failed",
        error="Test error"
    )
    
    history = metrics.action_history
    assert len(history) == 1
    assert history[0]["status"] == "failed"
    assert history[0]["error"] == "Test error"

def test_analyze_performance_empty(metrics):
    """Test performance analysis with no actions."""
    performance = metrics.analyze_performance()
    
    assert performance["total_actions"] == 0
    assert performance["success_rate"] == 0.0
    assert performance["average_response_time"] == 0.0
    assert performance["error_rate"] == 0.0
    assert "last_updated" in performance

def test_analyze_performance_mixed_actions(metrics):
    """Test performance analysis with mixed success/failure actions."""
    # Add some test actions
    start_time = datetime.now()
    
    # Success actions
    metrics.log_action("action1", start_time - timedelta(minutes=2), "success")
    metrics.log_action("action2", start_time - timedelta(minutes=1), "success")
    
    # Failed action
    metrics.log_action("action3", start_time, "failed", error="Test error")
    
    performance = metrics.analyze_performance()
    
    assert performance["total_actions"] == 3
    assert performance["success_rate"] == 2/3
    assert performance["error_rate"] == 1/3
    assert performance["average_response_time"] > 0

def test_clear_history(metrics):
    """Test clearing metrics history."""
    # Add some actions
    start_time = datetime.now()
    metrics.log_action("action1", start_time, "success")
    metrics.log_action("action2", start_time, "failed")
    
    # Verify actions were added
    assert len(metrics.action_history) == 2
    assert metrics.latest_metrics != {}
    
    # Clear history
    metrics.clear_history()
    
    # Verify everything was cleared
    assert len(metrics.action_history) == 0
    assert metrics.latest_metrics == {}
    
    # Verify new performance analysis starts fresh
    performance = metrics.analyze_performance()
    assert performance["total_actions"] == 0
    assert performance["success_rate"] == 0.0

def test_metrics_immutability(metrics):
    """Test that returned metrics data is immutable."""
    start_time = datetime.now()
    metrics.log_action("action1", start_time, "success")
    
    # Try to modify returned data
    history = metrics.action_history
    latest = metrics.latest_metrics
    
    history.append({"fake": "action"})
    latest["fake"] = "metric"
    
    # Verify internal data wasn't modified
    assert len(metrics.action_history) == 1
    assert "fake" not in metrics.latest_metrics
