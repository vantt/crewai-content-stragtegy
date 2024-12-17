# Phase B1: Strategy Agents Technical Specification

## 1. Overview
### 1.1 Purpose
This specification details the implementation of the Strategy Agent pair (Strategy Analyst and Market Skeptic) in the CrewAI Content Marketing System.

### 1.2 Dependencies
```python
from typing import Dict, List, Optional, Union, Any
from pydantic import BaseModel, Field
from datetime import datetime
from loguru import logger
from crewai import Agent, Task
import asyncio
```

## 2. Data Models

### 2.1 Strategy Analysis Models
```python
class TargetAudience(BaseModel):
    segments: List[Dict[str, Any]]
    pain_points: List[str]
    goals: List[str]
    demographics: Dict[str, Any]
    behavioral_traits: List[str]

class ValueProposition(BaseModel):
    core_benefits: List[str]
    unique_factors: List[str]
    proof_points: List[Dict[str, Any]]
    competitive_advantages: List[str]

class StrategyAnalysis(BaseModel):
    analysis_id: str
    timestamp: datetime
    target_audience: TargetAudience
    value_proposition: ValueProposition
    market_opportunities: List[Dict[str, Any]]
    risk_factors: List[Dict[str, Any]]
    recommendations: List[Dict[str, Any]]
    confidence_score: float
```

### 2.2 Market Challenge Models
```python
class MarketAssumption(BaseModel):
    assumption: str
    evidence: List[str]
    confidence_level: float
    potential_risks: List[str]

class CompetitiveAnalysis(BaseModel):
    competitors: List[Dict[str, Any]]
    market_share: Dict[str, float]
    strengths: List[str]
    weaknesses: List[str]
    opportunities: List[str]
    threats: List[str]

class MarketChallenge(BaseModel):
    challenge_id: str
    timestamp: datetime
    assumptions: List[MarketAssumption]
    competitive_analysis: CompetitiveAnalysis
    market_risks: List[Dict[str, Any]]
    alternative_approaches: List[Dict[str, Any]]
    validation_metrics: Dict[str, Any]
```

## 3. Strategy Analyst Implementation

### 3.1 Core Class
```python
class StrategyAnalyst(BaseAgent):
    def __init__(self, knowledge_base: Any):
        config = AgentConfig(
            role=AgentRole.STRATEGY,
            agent_type=AgentType.PRIMARY,
            temperature=0.7,
            max_iterations=3,
            context_window=4000
        )
        super().__init__(config, knowledge_base, name="StrategyAnalyst")
        
        self.analysis_history: List[StrategyAnalysis] = []
        self._init_agent_capabilities()
    
    def _init_agent_capabilities(self):
        self.crew_agent.add_capability("market_research")
        self.crew_agent.add_capability("competitive_analysis")
        self.crew_agent.add_capability("strategic_planning")
```

### 3.2 Analysis Methods
```python
class StrategyAnalyst(StrategyAnalyst):
    @BaseAgent.log_action
    async def analyze_target_audience(self, market_data: Dict[str, Any]) -> TargetAudience:
        """Analyze and segment target audience."""
        task = Task(
            description="Analyze market data to identify and segment target audience",
            context=market_data
        )
        result = await self.execute_task(task)
        return TargetAudience(**result)
    
    @BaseAgent.log_action
    async def develop_value_proposition(self, audience: TargetAudience) -> ValueProposition:
        """Develop value proposition based on audience analysis."""
        task = Task(
            description="Develop comprehensive value proposition",
            context=audience.dict()
        )
        result = await self.execute_task(task)
        return ValueProposition(**result)
    
    @BaseAgent.log_action
    async def conduct_strategy_analysis(
        self,
        market_data: Dict[str, Any],
        constraints: Optional[Dict[str, Any]] = None
    ) -> StrategyAnalysis:
        """Conduct complete strategy analysis."""
        try:
            # Analyze target audience
            audience = await self.analyze_target_audience(market_data)
            
            # Develop value proposition
            value_prop = await self.develop_value_proposition(audience)
            
            # Analyze market opportunities and risks
            opportunities_task = Task(
                description="Identify market opportunities and risks",
                context={
                    "market_data": market_data,
                    "audience": audience.dict(),
                    "constraints": constraints or {}
                }
            )
            opportunities_result = await self.execute_task(opportunities_task)
            
            # Generate final analysis
            analysis = StrategyAnalysis(
                analysis_id=str(uuid.uuid4()),
                timestamp=datetime.now(),
                target_audience=audience,
                value_proposition=value_prop,
                market_opportunities=opportunities_result["opportunities"],
                risk_factors=opportunities_result["risks"],
                recommendations=opportunities_result["recommendations"],
                confidence_score=self._calculate_confidence_score(opportunities_result)
            )
            
            self.analysis_history.append(analysis)
            return analysis
            
        except Exception as e:
            logger.error(f"Strategy analysis failed: {str(e)}")
            raise
```

## 4. Market Skeptic Implementation

### 4.1 Core Class
```python
class MarketSkeptic(BaseAgent):
    def __init__(self, knowledge_base: Any):
        config = AgentConfig(
            role=AgentRole.STRATEGY,
            agent_type=AgentType.ADVERSARY,
            temperature=0.8,  # Higher temperature for more creative challenges
            max_iterations=3,
            context_window=4000
        )
        super().__init__(config, knowledge_base, name="MarketSkeptic")
        
        self.challenge_history: List[MarketChallenge] = []
        self._init_agent_capabilities()
    
    def _init_agent_capabilities(self):
        self.crew_agent.add_capability("risk_analysis")
        self.crew_agent.add_capability("market_validation")
        self.crew_agent.add_capability("competitive_intelligence")
```

### 4.2 Challenge Methods
```python
class MarketSkeptic(MarketSkeptic):
    @BaseAgent.log_action
    async def challenge_assumptions(
        self,
        analysis: StrategyAnalysis
    ) -> List[MarketAssumption]:
        """Challenge key assumptions in the strategy analysis."""
        task = Task(
            description="Identify and challenge key market assumptions",
            context=analysis.dict()
        )
        result = await self.execute_task(task)
        return [MarketAssumption(**assumption) for assumption in result]
    
    @BaseAgent.log_action
    async def analyze_competition(
        self,
        analysis: StrategyAnalysis
    ) -> CompetitiveAnalysis:
        """Perform detailed competitive analysis."""
        task = Task(
            description="Conduct thorough competitive analysis",
            context=analysis.dict()
        )
        result = await self.execute_task(task)
        return CompetitiveAnalysis(**result)
    
    @BaseAgent.log_action
    async def generate_challenge(
        self,
        analysis: StrategyAnalysis
    ) -> MarketChallenge:
        """Generate comprehensive challenge to strategy analysis."""
        try:
            # Challenge assumptions
            assumptions = await self.challenge_assumptions(analysis)
            
            # Analyze competition
            competitive_analysis = await self.analyze_competition(analysis)
            
            # Identify risks and alternatives
            validation_task = Task(
                description="Identify market risks and alternative approaches",
                context={
                    "analysis": analysis.dict(),
                    "assumptions": [a.dict() for a in assumptions],
                    "competitive_analysis": competitive_analysis.dict()
                }
            )
            validation_result = await self.execute_task(validation_task)
            
            # Generate final challenge
            challenge = MarketChallenge(
                challenge_id=str(uuid.uuid4()),
                timestamp=datetime.now(),
                assumptions=assumptions,
                competitive_analysis=competitive_analysis,
                market_risks=validation_result["risks"],
                alternative_approaches=validation_result["alternatives"],
                validation_metrics=validation_result["metrics"]
            )
            
            self.challenge_history.append(challenge)
            return challenge
            
        except Exception as e:
            logger.error(f"Challenge generation failed: {str(e)}")
            raise
```

## 5. Interaction Protocol

### 5.1 Debate Process
```python
class StrategyDebate:
    def __init__(
        self,
        analyst: StrategyAnalyst,
        skeptic: MarketSkeptic,
        max_rounds: int = 3
    ):
        self.analyst = analyst
        self.skeptic = skeptic
        self.max_rounds = max_rounds
        self.debate_history: List[Dict[str, Any]] = []
    
    async def conduct_debate(
        self,
        market_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Conduct strategy debate between analyst and skeptic."""
        try:
            # Initial analysis
            analysis = await self.analyst.conduct_strategy_analysis(market_data)
            
            for round in range(self.max_rounds):
                # Generate challenge
                challenge = await self.skeptic.generate_challenge(analysis)
                
                # Record debate round
                debate_round = {
                    "round": round + 1,
                    "analysis": analysis.dict(),
                    "challenge": challenge.dict(),
                    "timestamp": datetime.now()
                }
                
                # Check if consensus is reached
                if self._check_consensus(analysis, challenge):
                    debate_round["status"] = "consensus"
                    self.debate_history.append(debate_round)
                    break
                
                # Refine analysis based on challenge
                analysis = await self.analyst.conduct_strategy_analysis(
                    market_data,
                    constraints={"previous_challenge": challenge.dict()}
                )
                
                debate_round["status"] = "ongoing"
                self.debate_history.append(debate_round)
            
            return {
                "final_analysis": analysis.dict(),
                "debate_history": self.debate_history,
                "consensus_reached": self._check_consensus(analysis, challenge)
            }
            
        except Exception as e:
            logger.error(f"Strategy debate failed: {str(e)}")
            raise
```

## 6. Example Usage
```python
async def example_strategy_analysis():
    # Initialize knowledge base
    knowledge_base = KnowledgeBase()
    
    # Create agents
    analyst = StrategyAnalyst(knowledge_base)
    skeptic = MarketSkeptic(knowledge_base)
    
    # Initialize debate
    debate = StrategyDebate(analyst, skeptic)
    
    # Example market data
    market_data = {
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
    
    # Conduct debate
    result = await debate.conduct_debate(market_data)
    
    # Process results
    print(f"Consensus reached: {result['consensus_reached']}")
    print(f"Number of debate rounds: {len(result['debate_history'])}")
    
    return result

if __name__ == "__main__":
    asyncio.run(example_strategy_analysis())
```
