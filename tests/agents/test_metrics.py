"""Tests for agent metrics tracking functionality."""
import pytest
from datetime import datetime, timedelta
from src.agents.metrics import AgentMetrics
from src.agents.models import MetricsConfig

@pytest.fixture
def metrics_config():
    """Test metrics configuration."""
    return MetricsConfig(
        enabled=True,
        history_size=5,
        aggregation_interval=60,
        performance_threshold=0.8
    )

@pytest.fixture
def metrics(metrics_config):
    """Test metrics instance."""
    return AgentMetrics(config=metrics_config)

def test_metrics_initialization(metrics, metrics_config):
    """Test metrics initialization."""
    assert metrics.config == metrics_config
    assert len(metrics.action_history) == 0
    assert metrics.latest_metrics['total_actions'] == 0
    assert metrics.latest_metrics['success_rate'] == 0.0

def test_log_action(metrics):
    """Test logging actions."""
    start_time = datetime.now()
    metrics.log_action(
        action_name="test_action",
        start_time=start_time,
        status="success",
        duration=1.0
    )
    
    history = metrics.action_history
    assert len(history) == 1
    assert history[0]['action'] == "test_action"
    assert history[0]['status'] == "success"
    assert history[0]['duration'] == 1.0
    assert history[0]['timestamp'] == start_time

def test_history_size_limit(metrics):
    """Test action history size limitation."""
    # Add more actions than history_size
    for i in range(6):
        metrics.log_action(
            action_name=f"action{i}",
            status="success"
        )
    
    history = metrics.action_history
    assert len(history) == 5  # Limited by history_size
    # Verify we kept most recent actions
    assert [h['action'] for h in history] == [
        "action5", "action4", "action3", "action2", "action1"
    ]

def test_performance_metrics_calculation(metrics):
    """Test performance metrics calculation."""
    # Add mix of successful and failed actions
    metrics.log_action("action1", status="success", duration=1.0)
    metrics.log_action("action2", status="failed", duration=2.0)
    metrics.log_action("action3", status="success", duration=3.0)
    
    performance = metrics.analyze_performance()
    assert performance['total_actions'] == 3
    assert performance['successful_actions'] == 2
    assert performance['failed_actions'] == 1
    assert performance['success_rate'] == 2/3
    assert performance['error_rate'] == 1/3
    assert performance['total_duration'] == 6.0
    assert performance['average_response_time'] == 2.0

def test_performance_threshold_warning(metrics):
    """Test performance threshold warning."""
    # Add mostly failed actions
    metrics.log_action("action1", status="failed", duration=1.0)
    metrics.log_action("action2", status="failed", duration=1.0)
    metrics.log_action("action3", status="success", duration=1.0)
    
    performance = metrics.analyze_performance()
    assert 'warning' in performance
    assert performance['success_rate'] < metrics.config.performance_threshold
    assert "below threshold" in performance['warning']

def test_clear_history(metrics):
    """Test clearing metrics history."""
    metrics.log_action("action1", status="success")
    assert len(metrics.action_history) == 1
    
    metrics.clear_history()
    assert len(metrics.action_history) == 0
    assert metrics.latest_metrics['total_actions'] == 0
    assert metrics.latest_metrics['success_rate'] == 0.0

def test_error_logging(metrics):
    """Test logging actions with errors."""
    metrics.log_action(
        action_name="failed_action",
        status="failed",
        error="Test error message"
    )
    
    history = metrics.action_history
    assert history[0]['status'] == "failed"
    assert history[0]['error'] == "Test error message"
    
    performance = metrics.analyze_performance()
    assert performance['error_rate'] == 1.0
    assert performance['success_rate'] == 0.0

def test_metrics_timestamps(metrics):
    """Test metrics timestamp handling."""
    # Add action without start_time
    metrics.log_action("action1", status="success")
    history = metrics.action_history
    assert 'timestamp' in history[0]
    assert isinstance(history[0]['timestamp'], datetime)
    
    # Add action with start_time
    start_time = datetime.now() - timedelta(minutes=1)
    metrics.log_action(
        "action2",
        start_time=start_time,
        status="success"
    )
    assert metrics.action_history[0]['timestamp'] == start_time

def test_metrics_config_defaults():
    """Test metrics configuration defaults."""
    metrics = AgentMetrics()  # No config provided
    assert metrics.config.enabled is True
    assert metrics.config.history_size == 1000
    assert metrics.config.aggregation_interval == 60
    assert metrics.config.performance_threshold == 0.8

def test_latest_metrics_copy(metrics):
    """Test latest_metrics returns a copy."""
    original = metrics.latest_metrics
    original['test'] = 'value'
    assert 'test' not in metrics.latest_metrics

def test_action_history_copy(metrics):
    """Test action_history returns a copy."""
    metrics.log_action("action1", status="success")
    original = metrics.action_history
    original.append({'fake': 'action'})
    assert len(metrics.action_history) == 1
