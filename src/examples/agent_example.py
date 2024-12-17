# src/examples/agent_example.py
import asyncio
from loguru import logger

async def example_usage():
    """Example of how to use the agent system."""
    try:
        # Initialize knowledge base (assuming it's already implemented)
        knowledge_base = object()  # placeholder
        
        # Create primary and adversary strategy agents
        strategy_agent = StrategyAgent(knowledge_base)
        strategy_critic = StrategyAgent(knowledge_base, is_adversary=True)
        
        # Execute market analysis
        market_data = {
            "market_size": 1000000,
            "competitors": ["CompA", "CompB"],
            "growth_rate": 0.15
        }
        
        analysis = await strategy_agent.analyze_market(market_data)
        critique = await strategy_critic.analyze_market(analysis)
        
        # Analyze performance
        performance = strategy_agent.analyze_performance()
        logger.info(f"Agent performance metrics: {performance}")
        
    except Exception as e:
        logger.error(f"Example usage failed: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(example_usage())