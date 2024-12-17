# src/models/task.py
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

class Task(BaseModel):
    description: str
    context: List[Dict[str, Any]] = Field(default_factory=list)
    expected_output: Dict[str, Any] = Field(default_factory=dict)