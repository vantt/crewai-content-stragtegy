"""Tests for enhanced metrics system."""
import pytest
from datetime import datetime, timedelta
from typing import Dict, Any, List

from src.agents.metrics import (
    MetricsAnalyzer,
    MetricType,
    ConsensusMetric,
    EvidenceMetric,
    PerformanceMetric
)

@pytest.fixture
def metrics_analyzer():
    """Fixture providing a metrics analyzer instance."""
    return MetricsAnalyzer()

@pytest.fixture
def sample_analysis():
    """Fixture providing sample analysis data."""
    return {
        "response_points": [
            {
                "addresses": "concern1",
                "details": ["point1", "point2", "point3"],
                "addresses_risk": "market",
                "mitigation_strength": 0.3
            },
            {
                "addresses": "concern2",
                "details": ["point1", "point2"],
                "addresses_risk": "technical",
                "mitigation_strength": 0.4
            }
        ],
        "implementation_factors": {
            "technical": {"score": 0.8},
            "resource": {"score": 0.7},
            "timeline": {"score": 0.6},
            "risk": {"score": 0.5}
        }
    }

@pytest.fixture
def sample_challenge():
    """Fixture providing sample challenge data."""
    return {
        "concerns": [
            {
                "id": "concern1",
                "description": "Market competition",
                "risk_type": "market",
                "severity": 0.7
            },
            {
                "id": "concern2",
                "description": "Technical complexity",
                "risk_type": "technical",
                "severity": 0.6
            },
            {
                "id": "concern3",
                "description": "Resource requirements",
                "risk_type": "resource",
                "severity": 0.5
            }
        ]
    }

@pytest.fixture
def sample_evidence():
    """Fixture providing sample evidence data."""
    return {
        "type": "market_research",
        "source": "Industry Report 2023",
        "timestamp": datetime.now() - timedelta(days=15),
        "content": {
            "market_size": 1000,
            "growth_rate": 15,
            "competition_analysis": "Strong",
            "market_trends": ["trend1", "trend2"]
        },
        "confidence": 0.9,
        "verified_source": True,
        "peer_reviewed": True,
        "multiple_sources": True,
        "data_validated": False
    }

def test_consensus_metrics_calculation(
    metrics_analyzer: MetricsAnalyzer,
    sample_analysis: Dict[str, Any],
    sample_challenge: Dict[str, Any],
    sample_evidence: Dict[str, Any]
):
    """Test consensus metrics calculation."""
    metrics = metrics_analyzer.calculate_consensus_metrics(
        sample_analysis,
        sample_challenge,
        [sample_evidence]
    )
    
    assert isinstance(metrics, ConsensusMetric)
    assert 0 <= metrics.agreement_score <= 1
    assert 0 <= metrics.resolution_quality <= 1
    assert 0 <= metrics.point_coverage <= 1
    assert 0 <= metrics.evidence_strength <= 1
    assert 0 <= metrics.implementation_feasibility <= 1
    
    # Verify risk assessment
    assert "technical" in metrics.risk_assessment
    assert "market" in metrics.risk_assessment
    assert all(0 <= score <= 1 for score in metrics.risk_assessment.values())

def test_evidence_metrics_calculation(
    metrics_analyzer: MetricsAnalyzer,
    sample_evidence: Dict[str, Any]
):
    """Test evidence metrics calculation."""
    metrics = metrics_analyzer.calculate_evidence_metrics(sample_evidence)
    
    assert isinstance(metrics, EvidenceMetric)
    assert 0 <= metrics.source_reliability <= 1
    assert 0 <= metrics.data_freshness <= 1
    assert 0 <= metrics.relevance_score <= 1
    assert 0 <= metrics.verification_level <= 1
    assert 0 <= metrics.confidence_score <= 1
    
    # Test data freshness calculation
    old_evidence = sample_evidence.copy()
    old_evidence["timestamp"] = datetime.now() - timedelta(days=400)
    old_metrics = metrics_analyzer.calculate_evidence_metrics(old_evidence)
    assert old_metrics.data_freshness < metrics.data_freshness

def test_performance_metrics_recording(metrics_analyzer: MetricsAnalyzer):
    """Test performance metrics recording."""
    start_time = datetime.now() - timedelta(seconds=2)
    end_time = datetime.now()
    
    metrics = metrics_analyzer.record_performance_metrics(
        start_time,
        end_time,
        memory_mb=100.0,
        cpu_percent=50.0
    )
    
    assert isinstance(metrics, PerformanceMetric)
    assert metrics.response_time >= 2.0
    assert metrics.memory_usage == 100.0
    assert metrics.cpu_usage == 50.0
    
    # Verify metrics were recorded
    assert len(metrics_analyzer.metrics_history[MetricType.PERFORMANCE]) > 0

def test_metrics_summary(
    metrics_analyzer: MetricsAnalyzer,
    sample_analysis: Dict[str, Any],
    sample_challenge: Dict[str, Any],
    sample_evidence: Dict[str, Any]
):
    """Test metrics summary generation."""
    # Record some metrics
    metrics_analyzer.calculate_consensus_metrics(
        sample_analysis,
        sample_challenge,
        [sample_evidence]
    )
    
    metrics_analyzer.record_performance_metrics(
        datetime.now() - timedelta(seconds=1),
        datetime.now(),
        memory_mb=100.0,
        cpu_percent=50.0
    )
    
    summary = metrics_analyzer.get_metrics_summary()
    
    # Verify summary structure
    assert "consensus" in summary
    assert "performance" in summary
    
    # Verify consensus metrics
    consensus = summary["consensus"]
    assert "average_agreement" in consensus
    assert "average_quality" in consensus
    assert "average_evidence" in consensus
    
    # Verify performance metrics
    performance = summary["performance"]
    assert "average_response_time" in performance
    assert "average_memory" in performance
    assert "average_cpu" in performance

def test_addressed_points_counting(
    metrics_analyzer: MetricsAnalyzer,
    sample_analysis: Dict[str, Any],
    sample_challenge: Dict[str, Any]
):
    """Test counting of addressed points."""
    count = metrics_analyzer._count_addressed_points(
        sample_analysis,
        sample_challenge
    )
    
    # Should have addressed 2 out of 3 concerns
    assert count == 2

def test_resolution_quality_calculation(
    metrics_analyzer: MetricsAnalyzer,
    sample_analysis: Dict[str, Any],
    sample_challenge: Dict[str, Any]
):
    """Test resolution quality calculation."""
    quality = metrics_analyzer._calculate_resolution_quality(
        sample_analysis["response_points"],
        sample_challenge["concerns"]
    )
    
    assert 0 <= quality <= 1
    # First response has 3 details, second has 2, average should be 0.83
    assert 0.8 <= quality <= 0.9

def test_implementation_feasibility(
    metrics_analyzer: MetricsAnalyzer,
    sample_analysis: Dict[str, Any]
):
    """Test implementation feasibility calculation."""
    feasibility = metrics_analyzer._calculate_implementation_feasibility(
        sample_analysis
    )
    
    assert 0 <= feasibility <= 1
    # Based on the sample data, should be around 0.65
    assert 0.6 <= feasibility <= 0.7

def test_risk_assessment(
    metrics_analyzer: MetricsAnalyzer,
    sample_analysis: Dict[str, Any],
    sample_challenge: Dict[str, Any]
):
    """Test risk assessment calculation."""
    risks = metrics_analyzer._assess_risks(
        sample_analysis,
        sample_challenge
    )
    
    assert all(0 <= score <= 1 for score in risks.values())
    assert "market" in risks
    assert "technical" in risks
    assert "resource" in risks
    
    # Market risk should be reduced by mitigation
    assert risks["market"] == 0.4  # 0.7 - 0.3
    # Technical risk should be reduced by mitigation
    assert risks["technical"] == 0.2  # 0.6 - 0.4
