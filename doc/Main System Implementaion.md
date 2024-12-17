from typing import Dict, List, Optional, Any
from loguru import logger
import asyncio
from datetime import datetime
import os
from dotenv import load_dotenv

# Import core components
from src.core.initialization import SystemInitializer
from src.core.knowledge_base import KnowledgeBase
from src.core.orchestrator import Orchestrator

# Import agent pairs
from src.agents.strategy import StrategyAnalyst, MarketSkeptic
from src.agents.marketing import MarketingSpecialist, MarketingCritic
from src.agents.content import ContentCreator, ContentReviewer

class ContentMarketingSystem:
    """Main system class that coordinates all components."""
    
    def __init__(self):
        # Initialize core system
        self.initializer = SystemInitializer()
        if not self.initializer.initialize_system():
            raise RuntimeError("System initialization failed")
            
        # Initialize components
        self.knowledge_base = KnowledgeBase()
        self.orchestrator = Orchestrator(self.knowledge_base)
        
        # Initialize agent pairs
        self._init_agent_pairs()
        
        logger.info("Content Marketing System initialized successfully")
    
    def _init_agent_pairs(self):
        """Initialize all agent pairs."""
        # Strategy agents
        self.strategy_analyst = StrategyAnalyst(self.knowledge_base)
        self.market_skeptic = MarketSkeptic(self.knowledge_base)
        
        # Marketing agents
        self.marketing_specialist = MarketingSpecialist(self.knowledge_base)
        self.marketing_critic = MarketingCritic(self.knowledge_base)
        
        # Content agents
        self.content_creator = ContentCreator(self.knowledge_base)
        self.content_reviewer = ContentReviewer(self.knowledge_base)
        
        # Register pairs with orchestrator
        self.orchestrator.register_agent_pair("strategy", self.strategy_analyst, self.market_skeptic)
        self.orchestrator.register_agent_pair("marketing", self.marketing_specialist, self.marketing_critic)
        self.orchestrator.register_agent_pair("content", self.content_creator, self.content_reviewer)
    
    async def create_content_strategy(
        self,
        market_data: Dict[str, Any],
        constraints: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create a comprehensive content strategy."""
        try:
            # Create workflow for strategy development
            workflow_id = self.orchestrator.create_workflow(
                name="Content Strategy Development",
                description="Develop comprehensive content strategy",
                steps=[
                    {
                        "name": "Market Analysis",
                        "description": "Analyze market and audience",
                        "agent_pair": "strategy",
                        "dependencies": []
                    },
                    {
                        "name": "Marketing Planning",
                        "description": "Create marketing plan",
                        "agent_pair": "marketing",
                        "dependencies": ["Market Analysis"]
                    },
                    {
                        "name": "Content Planning",
                        "description": "Plan content creation",
                        "agent_pair": "content",
                        "dependencies": ["Marketing Planning"]
                    }
                ]
            )
            
            # Execute workflow
            result = await self.orchestrator.execute_workflow(workflow_id)
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to create content strategy: {str(e)}")
            raise
    
    async def generate_content(
        self,
        strategy_result: Dict[str, Any],
        content_brief: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate content based on strategy."""
        try:
            # Create workflow for content generation
            workflow_id = self.orchestrator.create_workflow(
                name="Content Generation",
                description="Generate and review content",
                steps=[
                    {
                        "name": "Content Creation",
                        "description": "Create content based on brief",
                        "agent_pair": "content",
                        "dependencies": []
                    },
                    {
                        "name": "Content Review",
                        "description": "Review and optimize content",
                        "agent_pair": "content",
                        "dependencies": ["Content Creation"]
                    },
                    {
                        "name": "Marketing Alignment",
                        "description": "Verify marketing alignment",
                        "agent_pair": "marketing",
                        "dependencies": ["Content Review"]
                    }
                ]
            )
            
            # Execute workflow
            result = await self.orchestrator.execute_workflow(workflow_id)
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to generate content: {str(e)}")
            raise
    
    async def optimize_content(
        self,
        content: Dict[str, Any],
        optimization_goals: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Optimize existing content."""
        try:
            # Create workflow for content optimization
            workflow_id = self.orchestrator.create_workflow(
                name="Content Optimization",
                description="Optimize content performance",
                steps=[
                    {
                        "name": "Performance Analysis",
                        "description": "Analyze content performance",
                        "agent_pair": "marketing",
                        "dependencies": []
                    },
                    {
                        "name": "Content Optimization",
                        "description": "Optimize content",
                        "agent_pair": "content",
                        "dependencies": ["Performance Analysis"]
                    },
                    {
                        "name": "Strategy Alignment",
                        "description": "Verify strategy alignment",
                        "agent_pair": "strategy",
                        "dependencies": ["Content Optimization"]
                    }
                ]
            )
            
            # Execute workflow
            result = await self.orchestrator.execute_workflow(workflow_id)
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to optimize content: {str(e)}")
            raise

async def main():
    """Main entry point for the system."""
    try:
        # Initialize system
        system = ContentMarketingSystem()
        
        # Example usage
        market_data = {
            "target_audience": ["Marketing Managers", "Digital Strategists"],
            "industry": "Technology",
            "competitors": ["CompA", "CompB"],
            "goals": ["Increase brand awareness", "Generate leads"]
        }
        
        # Create content strategy
        strategy_result = await system.create_content_strategy(market_data)
        
        # Generate content based on strategy
        content_brief = {
            "content_type": "blog_post",
            "topic": "AI in Marketing",
            "target_length": 1500,
            "keywords": ["AI marketing", "marketing automation"]
        }
        
        content_result = await system.generate_content(strategy_result, content_brief)
        
        # Optimize content
        optimization_goals = {
            "metrics": ["engagement", "conversion"],
            "target_improvements": {"engagement": 0.2, "conversion": 0.1}
        }
        
        optimization_result = await system.optimize_content(
            content_result["content"],
            optimization_goals
        )
        
        logger.info("System execution completed successfully")
        
    except Exception as e:
        logger.error(f"System execution failed: {str(e)}")
        raise

if __name__ == "__main__":
    # Load environment variables
    load_dotenv()
    
    # Run system
    asyncio.run(main())