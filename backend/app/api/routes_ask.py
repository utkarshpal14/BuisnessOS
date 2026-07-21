from fastapi import APIRouter
from typing import List
from pydantic import BaseModel
from app.agents.base_agent import EvidenceItem

router = APIRouter(prefix="", tags=["reactive"])

class AskRequest(BaseModel):
    question: str

class AskResponse(BaseModel):
    answer: str
    agents_used: List[str]
    evidence: List[EvidenceItem]
    confidence: str
    task_id: str

@router.post("/ask", response_model=AskResponse)
def ask_question(request: AskRequest):
    return AskResponse(
        answer="Sample response summary",
        agents_used=["sales_agent", "finance_agent"],
        evidence=[EvidenceItem(source="sales_crm_sim", data_point="Sample sales data point")],
        confidence="high",
        task_id="t_1001"
    )
