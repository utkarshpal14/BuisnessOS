from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
import uuid

class PlannerTask(BaseModel):
    """
    Standardized task input model for the Planner Service.
    Extensible with arbitrary metadata.
    """
    task_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    task_type: str
    source: str = "user"
    query: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class AgentResult(BaseModel):
    """
    Standardized result returned by individual agents.
    """
    agent_name: str
    status: str = "success"  # "success" | "error"
    summary: str
    data: Dict[str, Any] = Field(default_factory=dict)
    error_message: Optional[str] = None

class PlannerResponse(BaseModel):
    """
    Standardized aggregated response returned by PlannerService.
    """
    task_id: str
    status: str  # "success" | "partial_success" | "failed"
    participating_agents: List[str] = Field(default_factory=list)
    summary: str
    raw_results: List[Dict[str, Any]] = Field(default_factory=list)
    execution_time_ms: float = 0.0
    errors: List[str] = Field(default_factory=list)
