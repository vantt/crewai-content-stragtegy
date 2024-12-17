"""Tests for strategy agents."""
import pytest
from datetime import datetime
from unittest.mock import Mock, patch

from src.agents.strategy import (
    StrategyAgent,
    StrategyAnalyst,
    MarketSkeptic,
    StrategyDebate
)
from src.agents.models import AgentConfig
from src.agents.types import AgentRole, AgentType
from src.models.strategy import (
    TargetAudience,
    ValueProposition,
    StrategyAnalysis,
    MarketAssumption,
    CompetitiveAnalysis,
    MarketChallenge
)

# Test data
MOCK_MARKET_DATA = {
    "market_size": 1000000,
    "growth_rate": 0.15,
    "competitors": [
        {"name": "CompA", "market_share": 0.3},
        {"name": "CompB", "market_share": 0.2}
    ],
    "demographics": {
        "age_range": [25, 45],
        "income_level": "middle-high"
    }
}

@pytest.fixture
def mock_knowledge_base():
    return Mock()

@pytest.fixture
def strategy_agent(mock_knowledge_base):
    return StrategyAgent(
        AgentConfig(
            role=AgentRole.STRATEGY,
            agent_type=AgentType.PRIMARY
        ),
        mock_knowledge_base
    )

@pytest.fixture
def strategy_analyst(mock_knowledge_base):
    return StrategyAnalyst(mock_knowledge_base)

@pytest.fixture
def market_skeptic(mock_knowledge_base):
    return MarketSkeptic(mock_knowledge_base)

class TestStrategyAgent:
    """Tests for base StrategyAgent class."""
    
    @pytest.mark.asyncio
    async def test_analyze_market_validates_input(self, strategy_agent):
        """Should validate market data input."""
        with pytest.raises(ValueError):
            await strategy_agent.analyze_market("invalid")
            
        with pytest.raises(ValueError):
            await strategy_agent.analyze_market({"market_size": "invalid"})
    
    @pytest.mark.asyncio
    async def test_analyze_market_returns_analysis(self, strategy_agent):
        """Should return market analysis results."""
        result = await strategy_agent.analyze_market(MOCK_MARKET_DATA)
        
        assert result["status"] == "success"
        assert "market_analysis" in result
        assert "recommendations" in result
        assert isinstance(result["confidence_score"], float)

class TestStrategyAnalyst:
    """Tests for StrategyAnalyst class."""
    
    @pytest.mark.asyncio
    async def test_analyze_target_audience(self, strategy_analyst):
        """Should analyze target audience from market data."""
        audience = await strategy_analyst.analyze_target_audience(MOCK_MARKET_DATA)
        
        assert isinstance(audience, TargetAudience)
        assert audience.demographics == MOCK_MARKET_DATA["demographics"]
    
    @pytest.mark.asyncio
    async def test_develop_value_proposition(self, strategy_analyst):
        """Should develop value proposition from audience analysis."""
        audience = TargetAudience(
            segments=[{"type": "primary", "description": "test"}],
            pain_points=["test pain point"],
            goals=["test goal"],
            demographics=MOCK_MARKET_DATA["demographics"],
            behavioral_traits=["test trait"]
        )
        
        value_prop = await strategy_analyst.develop_value_proposition(audience)
        
        assert isinstance(value_prop, ValueProposition)
        assert len(value_prop.core_benefits) > 0
        assert len(value_prop.unique_factors) > 0
    
    @pytest.mark.asyncio
    async def test_conduct_strategy_analysis(self, strategy_analyst):
        """Should conduct complete strategy analysis."""
        analysis = await strategy_analyst.conduct_strategy_analysis(MOCK_MARKET_DATA)
        
        assert isinstance(analysis, StrategyAnalysis)
        assert isinstance(analysis.target_audience, TargetAudience)
        assert isinstance(analysis.value_proposition, ValueProposition)
        assert len(analysis.market_opportunities) > 0
        assert len(analysis.risk_factors) > 0
        assert len(analysis.recommendations) > 0
        assert 0 <= analysis.confidence_score <= 1

class TestMarketSkeptic:
    """Tests for MarketSkeptic class."""
    
    @pytest.mark.asyncio
    async def test_challenge_assumptions(self, market_skeptic):
        """Should challenge analysis assumptions."""
        analysis = StrategyAnalysis(
            analysis_id="test",
            target_audience=TargetAudience(),
            value_proposition=ValueProposition(),
            market_opportunities=[],
            risk_factors=[],
            recommendations=[],
            confidence_score=0.8
        )
        
        assumptions = await market_skeptic.challenge_assumptions(analysis)
        
        assert isinstance(assumptions, list)
        assert all(isinstance(a, MarketAssumption) for a in assumptions)
    
    @pytest.mark.asyncio
    async def test_analyze_competition(self, market_skeptic):
        """Should analyze competition from analysis."""
        analysis = StrategyAnalysis(
            analysis_id="test",
            target_audience=TargetAudience(),
            value_proposition=ValueProposition(),
            market_opportunities=[],
            risk_factors=[],
            recommendations=[],
            confidence_score=0.8
        )
        
        comp_analysis = await market_skeptic.analyze_competition(analysis)
        
        assert isinstance(comp_analysis, CompetitiveAnalysis)
        assert len(comp_analysis.competitors) > 0
        assert len(comp_analysis.strengths) > 0
        assert len(comp_analysis.weaknesses) > 0
    
    @pytest.mark.asyncio
    async def test_generate_challenge(self, market_skeptic):
        """Should generate comprehensive challenge."""
        analysis = StrategyAnalysis(
            analysis_id="test",
            target_audience=TargetAudience(),
            value_proposition=ValueProposition(),
            market_opportunities=[],
            risk_factors=[],
            recommendations=[],
            confidence_score=0.8
        )
        
        challenge = await market_skeptic.generate_challenge(analysis)
        
        assert isinstance(challenge, MarketChallenge)
        assert len(challenge.assumptions) > 0
        assert isinstance(challenge.competitive_analysis, CompetitiveAnalysis)
        assert len(challenge.market_risks) > 0
        assert len(challenge.alternative_approaches) > 0

class TestStrategyDebate:
    """Tests for StrategyDebate class."""
    
    @pytest.mark.asyncio
    async def test_conduct_debate(self, strategy_analyst, market_skeptic):
        """Should conduct strategy debate."""
        debate = StrategyDebate(strategy_analyst, market_skeptic)
        result = await debate.conduct_debate(MOCK_MARKET_DATA)
        
        assert "final_analysis" in result
        assert "debate_history" in result
        assert "consensus_reached" in result
        assert isinstance(result["debate_history"], list)
        assert len(result["debate_history"]) > 0
        
        for round in result["debate_history"]:
            assert "round" in round
            assert "analysis" in round
            assert "challenge" in round
            assert "status" in round
            assert "timestamp" in round
