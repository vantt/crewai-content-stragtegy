"""Integration tests for agent interactions."""
import pytest
from typing import Any, Dict, List
import asyncio
from datetime import datetime

from src.agents.models import AgentConfig
from src.agents.strategy import StrategyAgent
from src.agents.marketing import MarketingAgent
from src.agents.types import AgentRole, AgentType

@pytest.fixture
def mock_knowledge_base() -> Any:
    """Create a mock knowledge base for testing."""
    class MockKnowledgeBase:
        def __init__(self):
            self.data = {}
        
        def add_knowledge_item(self, item: Dict[str, Any]) -> bool:
            self.data[item["id"]] = item
            return True
        
        def get_knowledge_item(self, item_id: str) -> Dict[str, Any]:
            return self.data.get(item_id, {})
        
        def search_knowledge(self, query: str) -> List[Dict[str, Any]]:
            return [item for item in self.data.values() 
                   if query.lower() in str(item).lower()]
    
    return MockKnowledgeBase()

@pytest.fixture
def strategy_config():
    return AgentConfig(
        role=AgentRole.STRATEGY,
        agent_type=AgentType.PRIMARY,
        temperature=0.7,
        max_rpm=10,
        memory_size=5
    )

@pytest.fixture
def marketing_config():
    return AgentConfig(
        role=AgentRole.MARKETING,
        agent_type=AgentType.PRIMARY,
        temperature=0.7,
        max_rpm=10,
        memory_size=5
    )

@pytest.mark.asyncio
async def test_strategy_marketing_workflow(
    mock_knowledge_base: Any,
    strategy_config: AgentConfig,
    marketing_config: AgentConfig
):
    """Test complete workflow between strategy and marketing agents."""
    # Create agents with config
    strategy_agent = StrategyAgent(strategy_config, mock_knowledge_base)
    marketing_agent = MarketingAgent(marketing_config, mock_knowledge_base)
    
    try:
        # Test data
        market_data = {
            "market_size": 1000000,
            "growth_rate": 0.15,
            "competitors": ["CompA", "CompB"],
            "target_audience": "Young professionals",
            "budget": 50000
        }
        
        # Execute strategy analysis
        strategy_result = await strategy_agent.analyze_market(market_data)
        
        # Verify strategy analysis
        assert isinstance(strategy_result, dict)
        assert strategy_result["status"] == "success"
        
        # Check strategy agent metrics
        strategy_metrics = strategy_agent.analyze_performance()
        assert strategy_metrics['total_actions'] > 0
        assert strategy_metrics['success_rate'] > 0
        
        # Create marketing campaign based on strategy
        campaign = await marketing_agent.create_campaign(strategy_result)
        
        # Verify campaign creation
        assert isinstance(campaign, dict)
        assert campaign["status"] == "success"
        
        # Check marketing agent metrics
        marketing_metrics = marketing_agent.analyze_performance()
        assert marketing_metrics['total_actions'] > 0
        assert marketing_metrics['success_rate'] > 0
        
        # Verify memory updates
        strategy_memory = strategy_agent.memory.get_relevant_memory("market analysis")
        marketing_memory = marketing_agent.memory.get_relevant_memory("campaign")
        
        assert len(strategy_memory) > 0
        assert len(marketing_memory) > 0
    
    finally:
        # Cleanup
        await strategy_agent.cleanup()
        await marketing_agent.cleanup()

@pytest.mark.asyncio
async def test_concurrent_agent_operations(
    mock_knowledge_base: Any,
    strategy_config: AgentConfig,
    marketing_config: AgentConfig
):
    """Test concurrent operations between multiple agents."""
    # Create agents with config
    strategy_agent = StrategyAgent(strategy_config, mock_knowledge_base)
    marketing_agent = MarketingAgent(marketing_config, mock_knowledge_base)
    
    try:
        # Create multiple market analysis tasks
        markets = [
            {"market_size": 1000000, "growth_rate": 0.15, "region": "North"},
            {"market_size": 800000, "growth_rate": 0.12, "region": "South"},
            {"market_size": 1200000, "growth_rate": 0.18, "region": "East"}
        ]
        
        # Execute market analyses concurrently
        analysis_tasks = [
            strategy_agent.analyze_market(market) for market in markets
        ]
        analysis_results = await asyncio.gather(*analysis_tasks)
        
        # Verify all analyses completed
        assert len(analysis_results) == len(markets)
        assert all(result["status"] == "success" for result in analysis_results)
        
        # Create campaigns concurrently
        campaign_tasks = [
            marketing_agent.create_campaign(analysis) for analysis in analysis_results
        ]
        campaign_results = await asyncio.gather(*campaign_tasks)
        
        # Verify all campaigns completed
        assert len(campaign_results) == len(markets)
        assert all(result["status"] == "success" for result in campaign_results)
        
        # Check rate limiting metrics
        strategy_metrics = strategy_agent.analyze_performance()
        marketing_metrics = marketing_agent.analyze_performance()
        
        assert strategy_metrics['total_actions'] >= len(markets)
        assert marketing_metrics['total_actions'] >= len(markets)
    
    finally:
        # Cleanup
        await strategy_agent.cleanup()
        await marketing_agent.cleanup()

@pytest.mark.asyncio
async def test_error_handling_and_recovery(
    mock_knowledge_base: Any,
    strategy_config: AgentConfig,
    marketing_config: AgentConfig
):
    """Test error handling and recovery in agent interactions."""
    # Create agents with config
    strategy_agent = StrategyAgent(strategy_config, mock_knowledge_base)
    marketing_agent = MarketingAgent(marketing_config, mock_knowledge_base)
    
    try:
        # Test with invalid data
        invalid_data = {"market_size": "invalid"}
        
        # Expect error from strategy agent
        with pytest.raises(Exception):
            await strategy_agent.analyze_market(invalid_data)
        
        # Verify error was logged
        strategy_metrics = strategy_agent.analyze_performance()
        assert strategy_metrics['success_rate'] < 1.0
        
        # Test recovery with valid data
        valid_data = {
            "market_size": 1000000,
            "growth_rate": 0.15
        }
        
        # Should succeed
        result = await strategy_agent.analyze_market(valid_data)
        assert result["status"] == "success"
        
        # Verify recovery in metrics
        updated_metrics = strategy_agent.analyze_performance()
        assert updated_metrics['total_actions'] > strategy_metrics['total_actions']
    
    finally:
        # Cleanup
        await strategy_agent.cleanup()
        await marketing_agent.cleanup()

@pytest.mark.asyncio
async def test_memory_context_sharing(
    mock_knowledge_base: Any,
    strategy_config: AgentConfig,
    marketing_config: AgentConfig
):
    """Test memory context sharing between agents."""
    # Create agents with config
    strategy_agent = StrategyAgent(strategy_config, mock_knowledge_base)
    marketing_agent = MarketingAgent(marketing_config, mock_knowledge_base)
    
    try:
        # Initial market analysis
        market_data = {
            "market_size": 1000000,
            "growth_rate": 0.15,
            "key_trend": "Sustainability focus"
        }
        
        # Perform initial analysis
        analysis = await strategy_agent.analyze_market(market_data)
        
        # Create first campaign
        campaign1 = await marketing_agent.create_campaign(analysis)
        
        # Update market data
        market_data["key_trend"] = "Digital transformation"
        
        # Perform second analysis
        analysis2 = await strategy_agent.analyze_market(market_data)
        
        # Create second campaign
        campaign2 = await marketing_agent.create_campaign(analysis2)
        
        # Verify memory retention and context awareness
        strategy_memory = strategy_agent.memory.get_relevant_memory("market analysis")
        marketing_memory = marketing_agent.memory.get_relevant_memory("campaign")
        
        # Check that both analyses are in memory
        assert len(strategy_memory) >= 2
        assert len(marketing_memory) >= 2
        
        # Verify chronological order (most recent first)
        assert strategy_memory[0]['timestamp'] > strategy_memory[1]['timestamp']
        assert marketing_memory[0]['timestamp'] > marketing_memory[1]['timestamp']
    
    finally:
        # Cleanup
        await strategy_agent.cleanup()
        await marketing_agent.cleanup()
