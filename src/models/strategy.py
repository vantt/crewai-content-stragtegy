"""Strategy-related data models."""
from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid
from pydantic import BaseModel, Field

class TargetAudience(BaseModel):
    """Target audience model."""
    segments: List[Dict[str, str]]
    pain_points: List[str]
    goals: List[str]
    demographics: Dict[str, Any]
    behavioral_traits: List[str]

class ValueProposition(BaseModel):
    """Value proposition model."""
    key_benefits: List[str]
    unique_advantages: List[str]
    solution_features: List[Dict[str, str]]
    target_outcomes: List[str]
    competitive_differentiators: List[str]

class MarketValidation(BaseModel):
    """Market validation model."""
    data_sources: List[str]
    validation_methods: List[str]
    findings: List[Dict[str, Any]]
    confidence_level: float
    recommendations: List[Dict[str, str]]

class RiskAssessment(BaseModel):
    """Risk assessment model."""
    risk_factors: List[Dict[str, Any]]
    impact_levels: Dict[str, float]
    mitigation_strategies: List[Dict[str, str]]
    contingency_plans: List[Dict[str, str]]
    overall_risk_level: float

class Challenge(BaseModel):
    """Challenge model for strategy analysis."""
    challenge_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=datetime.now)
    challenged_assumptions: List[Dict[str, Any]]
    market_validation: MarketValidation
    risk_assessment: RiskAssessment
    confidence_score: float

class StrategyAnalysis(BaseModel):
    """Strategy analysis model."""
    analysis_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=datetime.now)
    target_audience: TargetAudience
    value_proposition: ValueProposition
    market_opportunities: List[Dict[str, Any]]
    risk_factors: List[Dict[str, Any]]
    recommendations: List[Dict[str, Any]]
    confidence_score: float
