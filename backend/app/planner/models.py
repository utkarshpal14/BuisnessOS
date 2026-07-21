from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
import uuid

class EvidenceItem(BaseModel):
    """
    One citation backing a claim in an AgentResult/PlannerResponse summary --
    "where did this number/statement come from." Required (as a list, possibly
    empty) on every AgentResult per the explainability requirement -- see
    CLAUDE.md's "Non-negotiable design constraints".
    """
    source: str
    data_point: str

class PlannerTask(BaseModel):
    """
    Standardized task input model for the Planner Service.
    Extensible with arbitrary metadata.
    """
    task_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    task_type: str
    source: str = "user"
    query: str
    # Caller's role, once auth exists. None today (no auth is implemented yet) --
    # this field exists now so RBAC can be added at the Data Access Layer later
    # without changing this model or any agent's method signature. Agents and
    # Data Access Layer gateways must treat `None` as "no restriction" for now.
    role: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class AgentResult(BaseModel):
    """
    Standardized result returned by individual agents.
    """
    agent_name: str
    status: str = "success"  # "success" | "error"
    summary: str
    evidence: List[EvidenceItem] = Field(default_factory=list)
    confidence: str = "medium"  # "low" | "medium" | "high"
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
    # Concatenation of every participating agent's evidence, in agent-invocation
    # order -- the "every Planner-merged response must include the evidence
    # list" requirement, satisfied at the merge step rather than only per-agent.
    evidence: List[EvidenceItem] = Field(default_factory=list)
    raw_results: List[Dict[str, Any]] = Field(default_factory=list)
    execution_time_ms: float = 0.0
    errors: List[str] = Field(default_factory=list)
