"""
BusinessSnapshot: the structured hand-off point between the Enterprise Agent and the
AI Intelligence layer.

Represents an aggregated, domain-agnostic view of business metrics -- today that's
Sales and Finance, but any future domain (HR, Marketing, ...) plugs in the same way:
one more entry in `domains`, no schema change. AIIntelligenceService consumes this
model to build an LLM prompt without needing to know how any individual domain
computed its numbers.
"""
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class BusinessSnapshot(BaseModel):
    """Aggregated, structured snapshot of business metrics across domains."""

    task_id: str
    query: str
    domains: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    health_status: Optional[str] = None
    flags: List[str] = Field(default_factory=list)
    gaps: List[str] = Field(default_factory=list)
