from abc import ABC, abstractmethod
from typing import List, Dict, Any, Literal
from pydantic import BaseModel, Field

class Task(BaseModel):
    id: str
    source: Literal["user", "sentinel"]
    content: str
    context: Dict[str, Any] = Field(default_factory=dict)

class EvidenceItem(BaseModel):
    source: str
    data_point: str

class AgentResult(BaseModel):
    summary: str
    evidence: List[EvidenceItem]
    confidence: Literal["low", "medium", "high"]

class BaseAgent(ABC):
    """
    Abstract base class for all BusinessOS AI agents.
    Every agent must implement the handle method returning an AgentResult with evidence.
    """
    
    @abstractmethod
    def handle(self, task: Task, role: str) -> AgentResult:
        pass
