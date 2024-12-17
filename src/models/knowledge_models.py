# models/knowledge_models.py
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Dict, List, Optional, Any

class DebateRecord(BaseModel):
    """Model for storing debate interactions between agents."""
    model_config = ConfigDict(arbitrary_types_allowed=True)  # New style config
    
    debate_id: str
    timestamp: datetime
    primary_agent: str
    adversary_agent: str
    topic: str
    proposal: Dict[str, Any]
    challenges: List[Dict[str, Any]]
    resolutions: List[Dict[str, Any]]
    final_consensus: Optional[Dict[str, Any]]

class Template(BaseModel):
    """Model for storing reusable templates."""
    template_id: str
    category: str
    content: str
    parameters: List[str]
    usage_count: int = 0
    last_used: Optional[datetime]
    metadata: Dict[str, Any] = Field(default_factory=dict)

class KnowledgeItem(BaseModel):
    """Model for storing core knowledge items."""
    item_id: str
    category: str
    content: Any
    source: str
    timestamp: datetime
    version: int = 1
    metadata: Dict[str, Any] = Field(default_factory=dict)