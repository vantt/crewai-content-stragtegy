# Phase B3: Content Agents Technical Specification

## 1. Overview
### 1.1 Purpose
This specification details the implementation of the Content Agent pair (Content Creator and Content Reviewer) in the CrewAI Content Marketing System.

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

### 2.1 Content Creation Models
```python
class ContentFormat(str, Enum):
    BLOG_POST = "blog_post"
    SOCIAL_MEDIA = "social_media"
    EMAIL = "email"
    VIDEO_SCRIPT = "video_script"
    INFOGRAPHIC = "infographic"
    WHITEPAPER = "whitepaper"

class ContentMetadata(BaseModel):
    target_audience: List[str]
    keywords: List[str]
    seo_metadata: Dict[str, str]
    tone: str
    readability_level: str
    content_pillars: List[str]

class ContentPiece(BaseModel):
    content_id: str
    title: str
    format: ContentFormat
    main_content: str
    metadata: ContentMetadata
    version: int
    created_at: datetime
    modified_at: datetime
    status: str
    word_count: int
    estimated_reading_time: int
    associated_assets: List[Dict[str, str]]
    distribution_channels: List[str]

class ContentBatch(BaseModel):
    batch_id: str
    timestamp: datetime
    content_pieces: List[ContentPiece]
    content_brief: Dict[str, Any]
    target_metrics: Dict[str, Any]
    theme: str
    campaign_association: Optional[str]
```

### 2.2 Content Review Models
```python
class QualityMetrics(BaseModel):
    grammar_score: float
    readability_score: float
    seo_score: float
    originality_score: float
    brand_alignment_score: float
    engagement_potential: float

class ContentSuggestion(BaseModel):
    section: str
    current_text: str
    suggested_text: str
    justification: str
    priority: int

class ContentReview(BaseModel):
    review_id: str
    content_id: str
    timestamp: datetime
    reviewer: str
    quality_metrics: QualityMetrics
    suggestions: List[ContentSuggestion]
    overall_score: float
    approval_status: str
    required_revisions: bool
    comments: List[Dict[str, Any]]
```

## 3. Content Creator Implementation

### 3.1 Core Class
```python
class ContentCreator(BaseAgent):
    def __init__(self, knowledge_base: Any):
        config = AgentConfig(
            role=AgentRole.CONTENT,
            agent_type=AgentType.PRIMARY,
            temperature=0.7,
            max_iterations=3,
            context_window=8000  # Larger context for content creation
        )
        super().__init__(config, knowledge_base, name="ContentCreator")
        
        self.content_history: List[ContentBatch] = []
        self._init_agent_capabilities()
    
    def _init_agent_capabilities(self):
        self.crew_agent.add_capability("content_writing")
        self.crew_agent.add_capability("seo_optimization")
        self.crew_agent.add_capability("audience_targeting")
        self.crew_agent.add_capability("brand_voice_alignment")
```

### 3.2 Content Creation Methods
```python
class ContentCreator(ContentCreator):
    @BaseAgent.log_action
    async def generate_content_piece(
        self,
        brief: Dict[str, Any],
        format: ContentFormat
    ) -> ContentPiece:
        """Generate a single piece of content."""
        task = Task(
            description=f"Create {format.value} content based on brief",
            context=brief
        )
        result = await self.execute_task(task)
        
        metadata = ContentMetadata(
            target_audience=brief["target_audience"],
            keywords=brief["keywords"],
            seo_metadata=result["seo_metadata"],
            tone=brief["tone"],
            readability_level=brief["readability_level"],
            content_pillars=brief["content_pillars"]
        )
        
        return ContentPiece(
            content_id=str(uuid.uuid4()),
            title=result["title"],
            format=format,
            main_content=result["content"],
            metadata=metadata,
            version=1,
            created_at=datetime.now(),
            modified_at=datetime.now(),
            status="draft",
            word_count=len(result["content"].split()),
            estimated_reading_time=self._calculate_reading_time(result["content"]),
            associated_assets=result.get("assets", []),
            distribution_channels=brief["distribution_channels"]
        )
    
    @BaseAgent.log_action
    async def optimize_content(
        self,
        content: ContentPiece,
        optimization_goals: Dict[str, Any]
    ) -> ContentPiece:
        """Optimize content based on specific goals."""
        task = Task(
            description="Optimize content for specified goals",
            context={
                "content": content.dict(),
                "goals": optimization_goals
            }
        )
        result = await self.execute_task(task)
        
        content.main_content = result["optimized_content"]
        content.version += 1
        content.modified_at = datetime.now()
        content.metadata.seo_metadata = result["seo_metadata"]
        
        return content
    
    @BaseAgent.log_action
    async def create_content_batch(
        self,
        content_brief: Dict[str, Any]
    ) -> ContentBatch:
        """Create a batch of related content pieces."""
        try:
            content_pieces = []
            
            for format_spec in content_brief["formats"]:
                format_type = ContentFormat(format_spec["type"])
                piece = await self.generate_content_piece(
                    brief={**content_brief, **format_spec},
                    format=format_type
                )
                
                # Optimize content if required
                if format_spec.get("optimization_goals"):
                    piece = await self.optimize_content(
                        piece,
                        format_spec["optimization_goals"]
                    )
                
                content_pieces.append(piece)
            
            batch = ContentBatch(
                batch_id=str(uuid.uuid4()),
                timestamp=datetime.now(),
                content_pieces=content_pieces,
                content_brief=content_brief,
                target_metrics=content_brief.get("target_metrics", {}),
                theme=content_brief.get("theme", ""),
                campaign_association=content_brief.get("campaign_id")
            )
            
            self.content_history.append(batch)
            return batch
            
        except Exception as e:
            logger.error(f"Content batch creation failed: {str(e)}")
            raise
```

## 4. Content Reviewer Implementation

### 4.1 Core Class
```python
class ContentReviewer(BaseAgent):
    def __init__(self, knowledge_base: Any):
        config = AgentConfig(
            role=AgentRole.CONTENT,
            agent_type=AgentType.ADVERSARY,
            temperature=0.8,
            max_iterations=3,
            context_window=8000
        )
        super().__init__(config, knowledge_base, name="ContentReviewer")
        
        self.review_history: List[ContentReview] = []
        self._init_agent_capabilities()
    
    def _init_agent_capabilities(self):
        self.crew_agent.add_capability("content_analysis")
        self.crew_agent.add_capability("quality_assessment")
        self.crew_agent.add_capability("brand_guidelines_verification")
        self.crew_agent.add_capability("seo_validation")
```

### 4.2 Review Methods
```python
class ContentReviewer(ContentReviewer):
    @BaseAgent.log_action
    async def assess_quality(
        self,
        content: ContentPiece
    ) -> QualityMetrics:
        """Assess content quality metrics."""
        task = Task(
            description="Assess content quality across multiple dimensions",
            context=content.dict()
        )
        result = await self.execute_task(task)
        return QualityMetrics(**result)
    
    @BaseAgent.log_action
    async def generate_suggestions(
        self,
        content: ContentPiece,
        quality_metrics: QualityMetrics
    ) -> List[ContentSuggestion]:
        """Generate improvement suggestions based on quality assessment."""
        task = Task(
            description="Generate detailed content improvement suggestions",
            context={
                "content": content.dict(),
                "metrics": quality_metrics.dict()
            }
        )
        result = await self.execute_task(task)
        return [ContentSuggestion(**suggestion) for suggestion in result]
    
    @BaseAgent.log_action
    async def review_content(
        self,
        content: ContentPiece
    ) -> ContentReview:
        """Generate comprehensive content review."""
        try:
            # Assess quality metrics
            quality_metrics = await self.assess_quality(content)
            
            # Generate improvement suggestions
            suggestions = await self.generate_suggestions(content, quality_metrics)
            
            # Calculate overall score
            overall_score = self._calculate_overall_score(quality_metrics)
            
            # Determine approval status
            approval_status = "approved" if overall_score >= 0.8 else "needs_revision"
            
            # Create review
            review = ContentReview(
                review_id=str(uuid.uuid4()),
                content_id=content.content_id,
                timestamp=datetime.now(),
                reviewer=self.name,
                quality_metrics=quality_metrics,
                suggestions=suggestions,
                overall_score=overall_score,
                approval_status=approval_status,
                required_revisions=overall_score < 0.8,
                comments=self._generate_review_comments(quality_metrics, suggestions)
            )
            
            self.review_history.append(review)
            return review
            
        except Exception as e:
            logger.error(f"Content review failed: {str(e)}")
            raise
```

## 5. Content Review Process

### 5.1 Review Workflow
```python
class ContentReviewProcess:
    def __init__(
        self,
        creator: ContentCreator,
        reviewer: ContentReviewer,
        max_revisions: int = 3
    ):
        self.creator = creator
        self.reviewer = reviewer
        self.max_revisions = max_revisions
        self.review_history: List[Dict[str, Any]] = []
    
    async def review_content_batch(
        self,
        content_brief: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute content creation and review process."""
        try:
            # Initial content creation
            batch = await self.creator.create_content_batch(content_brief)
            
            for piece in batch.content_pieces:
                revision_count = 0
                
                while revision_count < self.max_revisions:
                    # Review content
                    review = await self.reviewer.review_content(piece)
                    
                    # Record review iteration
                    review_iteration = {
                        "content_id": piece.content_id,
                        "revision": revision_count + 1,
                        "content": piece.dict(),
                        "review": review.dict(),
                        "timestamp": datetime.now()
                    }
                    
                    # Check if content meets quality threshold
                    if review.approval_status == "approved":
                        review_iteration["status"] = "approved"
                        self.review_history.append(review_iteration)
                        break
                    
                    # Revise content based on review
                    piece = await self.creator.optimize_content(
                        piece,
                        {"suggestions": [s.dict() for s in review.suggestions]}
                    )
                    
                    review_iteration["status"] = "revised"
                    self.review_history.append(review_iteration)
                    revision_count += 1
            
            return {
                "batch": batch.dict(),
                "review_history": self.review_history,
                "all_approved": all(r["status"] == "approved" 
                                  for r in self.review_history[-len(batch.content_pieces):])
            }
            
        except Exception as e:
            logger.error(f"Content review process failed: {str(e)}")
            raise
```

## 6. Example Usage
```python
async def example_content_creation():
    # Initialize knowledge base
    knowledge_base = KnowledgeBase()
    
    # Create agents
    creator = ContentCreator(knowledge_base)
    reviewer = ContentReviewer(knowledge_base)
    
    # Initialize review process
    review_process = ContentReviewProcess(creator, reviewer)
    
    # Example content brief
    content_brief = {
        "theme": "AI in Marketing",
        "formats": [
            {
                "type": "blog_post",
                "word_count": 1500,
                "optimization_goals": {
                    "seo": True,
                    "readability": "advanced"
                }
            },
            {
                "type": "social_media",
                "platform": "LinkedIn",
                "post_count": 5
            }
        ],
        "target_audience": ["Marketing Managers", "Digital Strategists"],
        "keywords": ["AI marketing", "marketing automation", "MarTech"],
        "tone": "professional",
        "readability_level": "advanced",
        "content_pillars": ["Innovation", "Efficiency", "ROI"],
        "distribution_channels": ["blog", "social_media", "newsletter"],
        "target_metrics": {
            "engagement_rate": 0.05,
            "conversion_rate": 0.02,
            "time_on_page": 180
        }
    }
    
    # Execute review process
    result = await review_process.review_content_batch(content_brief)
    
    # Process results
    print(f"All content approved: {result['all_approved']}")
    print(f"Total revisions: {len(result['review_history'])}")
    
    return result

if __name__ == "__main__":
    asyncio.run(example_content_creation())
```