# Phase B2: Marketing Agents Technical Specification

## 1. Overview
### 1.1 Purpose
This specification details the implementation of the Marketing Agent pair (Marketing Specialist and Marketing Critic) in the CrewAI Content Marketing System.

### 1.2 Dependencies
```python
from typing import Dict, List, Optional, Union, Any
from pydantic import BaseModel, Field
from datetime import datetime
from loguru import logger
from crewai import Agent, Task
import asyncio
from enum import Enum
```

## 2. Data Models

### 2.1 Marketing Plan Models
```python
class MarketingChannel(BaseModel):
    channel_id: str
    name: str
    type: str
    priority: int
    estimated_reach: int
    estimated_cost: float
    expected_roi: float
    kpis: Dict[str, Any]

class MarketingTactic(BaseModel):
    tactic_id: str
    name: str
    description: str
    channels: List[str]  # References to channel_ids
    timeline: Dict[str, Any]
    budget: float
    expected_outcomes: Dict[str, Any]
    success_metrics: Dict[str, Any]

class ContentCalendar(BaseModel):
    calendar_id: str
    start_date: datetime
    end_date: datetime
    entries: List[Dict[str, Any]]
    content_distribution: Dict[str, int]
    milestone_dates: Dict[str, datetime]

class MarketingPlan(BaseModel):
    plan_id: str
    timestamp: datetime
    objectives: List[Dict[str, Any]]
    target_metrics: Dict[str, Any]
    channels: List[MarketingChannel]
    tactics: List[MarketingTactic]
    content_calendar: ContentCalendar
    total_budget: float
    resource_allocation: Dict[str, Any]
    risk_mitigation: Dict[str, Any]
```

### 2.2 Marketing Review Models
```python
class ChannelAssessment(BaseModel):
    channel_id: str
    effectiveness_score: float
    cost_efficiency: float
    audience_fit: float
    recommendations: List[str]
    risks: List[str]

class TacticReview(BaseModel):
    tactic_id: str
    feasibility_score: float
    resource_requirements: Dict[str, Any]
    implementation_challenges: List[str]
    alternative_approaches: List[Dict[str, Any]]

class MarketingReview(BaseModel):
    review_id: str
    timestamp: datetime
    plan_id: str  # Reference to original marketing plan
    channel_assessments: List[ChannelAssessment]
    tactic_reviews: List[TacticReview]
    budget_analysis: Dict[str, Any]
    timeline_feasibility: Dict[str, Any]
    resource_gaps: List[Dict[str, Any]]
    overall_risk_assessment: Dict[str, float]
```

## 3. Marketing Specialist Implementation

### 3.1 Core Class
```python
class MarketingSpecialist(BaseAgent):
    def __init__(self, knowledge_base: Any):
        config = AgentConfig(
            role=AgentRole.MARKETING,
            agent_type=AgentType.PRIMARY,
            temperature=0.7,
            max_iterations=3,
            context_window=4000
        )
        super().__init__(config, knowledge_base, name="MarketingSpecialist")
        
        self.plan_history: List[MarketingPlan] = []
        self._init_agent_capabilities()
    
    def _init_agent_capabilities(self):
        self.crew_agent.add_capability("channel_planning")
        self.crew_agent.add_capability("budget_allocation")
        self.crew_agent.add_capability("campaign_design")
        self.crew_agent.add_capability("content_calendar_planning")
```

### 3.2 Planning Methods
```python
class MarketingSpecialist(MarketingSpecialist):
    @BaseAgent.log_action
    async def design_channel_strategy(
        self,
        strategy_data: Dict[str, Any]
    ) -> List[MarketingChannel]:
        """Design multi-channel marketing strategy."""
        task = Task(
            description="Design optimal channel mix based on strategy",
            context=strategy_data
        )
        result = await self.execute_task(task)
        return [MarketingChannel(**channel) for channel in result]
    
    @BaseAgent.log_action
    async def develop_tactics(
        self,
        channels: List[MarketingChannel],
        constraints: Optional[Dict[str, Any]] = None
    ) -> List[MarketingTactic]:
        """Develop marketing tactics for each channel."""
        task = Task(
            description="Develop detailed marketing tactics",
            context={
                "channels": [c.dict() for c in channels],
                "constraints": constraints or {}
            }
        )
        result = await self.execute_task(task)
        return [MarketingTactic(**tactic) for tactic in result]
    
    @BaseAgent.log_action
    async def create_content_calendar(
        self,
        tactics: List[MarketingTactic],
        timeframe: Dict[str, datetime]
    ) -> ContentCalendar:
        """Create detailed content calendar."""
        task = Task(
            description="Create content calendar with distribution plan",
            context={
                "tactics": [t.dict() for t in tactics],
                "timeframe": timeframe
            }
        )
        result = await self.execute_task(task)
        return ContentCalendar(**result)
    
    @BaseAgent.log_action
    async def develop_marketing_plan(
        self,
        strategy_data: Dict[str, Any],
        constraints: Optional[Dict[str, Any]] = None
    ) -> MarketingPlan:
        """Develop comprehensive marketing plan."""
        try:
            # Design channel strategy
            channels = await self.design_channel_strategy(strategy_data)
            
            # Develop tactics
            tactics = await self.develop_tactics(channels, constraints)
            
            # Create content calendar
            calendar = await self.create_content_calendar(
                tactics,
                timeframe={
                    "start_date": datetime.now(),
                    "end_date": datetime.now() + timedelta(days=90)
                }
            )
            
            # Calculate budget and resource allocation
            allocation_task = Task(
                description="Calculate budget and resource allocation",
                context={
                    "channels": [c.dict() for c in channels],
                    "tactics": [t.dict() for t in tactics],
                    "calendar": calendar.dict()
                }
            )
            allocation_result = await self.execute_task(allocation_task)
            
            # Create final marketing plan
            plan = MarketingPlan(
                plan_id=str(uuid.uuid4()),
                timestamp=datetime.now(),
                objectives=strategy_data.get("objectives", []),
                target_metrics=strategy_data.get("target_metrics", {}),
                channels=channels,
                tactics=tactics,
                content_calendar=calendar,
                total_budget=allocation_result["total_budget"],
                resource_allocation=allocation_result["resource_allocation"],
                risk_mitigation=allocation_result["risk_mitigation"]
            )
            
            self.plan_history.append(plan)
            return plan
            
        except Exception as e:
            logger.error(f"Marketing plan development failed: {str(e)}")
            raise
```

## 4. Marketing Critic Implementation

### 4.1 Core Class
```python
class MarketingCritic(BaseAgent):
    def __init__(self, knowledge_base: Any):
        config = AgentConfig(
            role=AgentRole.MARKETING,
            agent_type=AgentType.ADVERSARY,
            temperature=0.8,
            max_iterations=3,
            context_window=4000
        )
        super().__init__(config, knowledge_base, name="MarketingCritic")
        
        self.review_history: List[MarketingReview] = []
        self._init_agent_capabilities()
    
    def _init_agent_capabilities(self):
        self.crew_agent.add_capability("marketing_analysis")
        self.crew_agent.add_capability("risk_assessment")
        self.crew_agent.add_capability("resource_planning")
        self.crew_agent.add_capability("budget_analysis")
```

### 4.2 Review Methods
```python
class MarketingCritic(MarketingCritic):
    @BaseAgent.log_action
    async def assess_channels(
        self,
        channels: List[MarketingChannel]
    ) -> List[ChannelAssessment]:
        """Assess effectiveness and efficiency of marketing channels."""
        task = Task(
            description="Assess marketing channel selection and mix",
            context={"channels": [c.dict() for c in channels]}
        )
        result = await self.execute_task(task)
        return [ChannelAssessment(**assessment) for assessment in result]
    
    @BaseAgent.log_action
    async def review_tactics(
        self,
        tactics: List[MarketingTactic]
    ) -> List[TacticReview]:
        """Review marketing tactics for feasibility and effectiveness."""
        task = Task(
            description="Review marketing tactics and implementation plan",
            context={"tactics": [t.dict() for t in tactics]}
        )
        result = await self.execute_task(task)
        return [TacticReview(**review) for review in result]
    
    @BaseAgent.log_action
    async def generate_marketing_review(
        self,
        plan: MarketingPlan
    ) -> MarketingReview:
        """Generate comprehensive marketing plan review."""
        try:
            # Assess channels
            channel_assessments = await self.assess_channels(plan.channels)
            
            # Review tactics
            tactic_reviews = await self.review_tactics(plan.tactics)
            
            # Analyze budget and resources
            analysis_task = Task(
                description="Analyze budget allocation and resource planning",
                context={
                    "plan": plan.dict(),
                    "channel_assessments": [a.dict() for a in channel_assessments],
                    "tactic_reviews": [r.dict() for r in tactic_reviews]
                }
            )
            analysis_result = await self.execute_task(analysis_task)
            
            # Generate final review
            review = MarketingReview(
                review_id=str(uuid.uuid4()),
                timestamp=datetime.now(),
                plan_id=plan.plan_id,
                channel_assessments=channel_assessments,
                tactic_reviews=tactic_reviews,
                budget_analysis=analysis_result["budget_analysis"],
                timeline_feasibility=analysis_result["timeline_feasibility"],
                resource_gaps=analysis_result["resource_gaps"],
                overall_risk_assessment=analysis_result["risk_assessment"]
            )
            
            self.review_history.append(review)
            return review
            
        except Exception as e:
            logger.error(f"Marketing review generation failed: {str(e)}")
            raise
```

## 5. Interaction Protocol

### 5.1 Review Process
```python
class MarketingReviewProcess:
    def __init__(
        self,
        specialist: MarketingSpecialist,
        critic: MarketingCritic,
        max_iterations: int = 3
    ):
        self.specialist = specialist
        self.critic = critic
        self.max_iterations = max_iterations
        self.review_history: List[Dict[str, Any]] = []
    
    async def conduct_review(
        self,
        strategy_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Conduct marketing plan review process."""
        try:
            # Initial plan development
            plan = await self.specialist.develop_marketing_plan(strategy_data)
            
            for iteration in range(self.max_iterations):
                # Generate review
                review = await self.critic.generate_marketing_review(plan)
                
                # Record review iteration
                review_iteration = {
                    "iteration": iteration + 1,
                    "plan": plan.dict(),
                    "review": review.dict(),
                    "timestamp": datetime.now()
                }
                
                # Check if plan meets quality threshold
                if self._check_quality_threshold(plan, review):
                    review_iteration["status"] = "approved"
                    self.review_history.append(review_iteration)
                    break
                
                # Refine plan based on review
                plan = await self.specialist.develop_marketing_plan(
                    strategy_data,
                    constraints={"previous_review": review.dict()}
                )
                
                review_iteration["status"] = "revision_required"
                self.review_history.append(review_iteration)
            
            return {
                "final_plan": plan.dict(),
                "final_review": review.dict(),
                "review_history": self.review_history,
                "approved": self._check_quality_threshold(plan, review)
            }
            
        except Exception as e:
            logger.error(f"Marketing review process failed: {str(e)}")
            raise
```

## 6. Example Usage
```python
async def example_marketing_planning():
    # Initialize knowledge base
    knowledge_base = KnowledgeBase()
    
    # Create agents
    specialist = MarketingSpecialist(knowledge_base)
    critic = MarketingCritic(knowledge_base)
    
    # Initialize review process
    review_process = MarketingReviewProcess(specialist, critic)
    
    # Example strategy data
    strategy_data = {
        "objectives": [
            {"type": "awareness", "target": "Increase brand awareness by 30%"},
            {"type": "engagement", "target": "Achieve 25% engagement rate"}
        ],
        "target_metrics": {
            "roi": 2.5,
            "cac": 50.0,
            "conversion_rate": 0.03
        },
        "budget_constraints": {
            "total": 100000,
            "monthly": 8333
        }
    }
    
    # Conduct review process
    result = await review_process.conduct_review(strategy_data)
    
    # Process results
    print(f"Plan approved: {result['approved']}")
    print(f"Number of iterations: {len(result['review_history'])}")
    
    return result

if __name__ == "__main__":
    asyncio.run(example_marketing_planning())
```