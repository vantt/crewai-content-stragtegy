"""Strategy-related data models."""
from typing import Dict, List, Any
from datetime import datetime
from pydantic import BaseModel, Field

class TargetAudience(BaseModel):
    """Target audience analysis model."""
    segments: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Market segments with detailed characteristics"
    )
    pain_points: List[str] = Field(
        default_factory=list,
        description="Key pain points of target audience"
    )
    goals: List[str] = Field(
        default_factory=list,
        description="Primary goals and objectives of target audience"
    )
    demographics: Dict[str, Any] = Field(
        default_factory=dict,
        description="Demographic information"
    )
    behavioral_traits: List[str] = Field(
        default_factory=list,
        description="Key behavioral characteristics"
    )

class ValueProposition(BaseModel):
    """Value proposition model."""
    core_benefits: List[str] = Field(
        default_factory=list,
        description="Core benefits offered to customers"
    )
    unique_factors: List[str] = Field(
        default_factory=list,
        description="Unique differentiating factors"
    )
    proof_points: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Evidence supporting value claims"
    )
    competitive_advantages: List[str] = Field(
        default_factory=list,
        description="Key competitive advantages"
    )

class StrategyAnalysis(BaseModel):
    """Complete strategy analysis model."""
    analysis_id: str = Field(
        description="Unique identifier for analysis"
    )
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="Time of analysis"
    )
    target_audience: TargetAudience = Field(
        description="Target audience analysis"
    )
    value_proposition: ValueProposition = Field(
        description="Value proposition analysis"
    )
    market_opportunities: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Identified market opportunities"
    )
    risk_factors: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Identified risk factors"
    )
    recommendations: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Strategic recommendations"
    )
    confidence_score: float = Field(
        ge=0.0,
        le=1.0,
        description="Confidence score for analysis"
    )

class MarketAssumption(BaseModel):
    """Market assumption model."""
    assumption: str = Field(
        description="The assumption being made"
    )
    evidence: List[str] = Field(
        default_factory=list,
        description="Supporting evidence"
    )
    confidence_level: float = Field(
        ge=0.0,
        le=1.0,
        description="Confidence level in assumption"
    )
    potential_risks: List[str] = Field(
        default_factory=list,
        description="Potential risks if assumption is wrong"
    )

class CompetitiveAnalysis(BaseModel):
    """Competitive analysis model."""
    competitors: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Competitor details"
    )
    market_share: Dict[str, float] = Field(
        default_factory=dict,
        description="Market share by competitor"
    )
    strengths: List[str] = Field(
        default_factory=list,
        description="Competitive strengths"
    )
    weaknesses: List[str] = Field(
        default_factory=list,
        description="Competitive weaknesses"
    )
    opportunities: List[str] = Field(
        default_factory=list,
        description="Market opportunities"
    )
    threats: List[str] = Field(
        default_factory=list,
        description="Market threats"
    )

class MarketChallenge(BaseModel):
    """Market challenge model."""
    challenge_id: str = Field(
        description="Unique identifier for challenge"
    )
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="Time of challenge"
    )
    assumptions: List[MarketAssumption] = Field(
        default_factory=list,
        description="Challenged assumptions"
    )
    competitive_analysis: CompetitiveAnalysis = Field(
        description="Competitive analysis"
    )
    market_risks: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Identified market risks"
    )
    alternative_approaches: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Alternative strategic approaches"
    )
    validation_metrics: Dict[str, Any] = Field(
        default_factory=dict,
        description="Metrics for validation"
    )
