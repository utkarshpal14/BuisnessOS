from fastapi import APIRouter
from typing import List
from pydantic import BaseModel

router = APIRouter(prefix="", tags=["alerts"])

class AlertSummary(BaseModel):
    id: str
    severity: str
    summary: str
    created_at: str
    acknowledged: bool

@router.get("/alerts", response_model=List[AlertSummary])
def get_alerts():
    return []

@router.get("/alerts/{id}")
def get_alert_detail(id: str):
    return {"id": id, "detail": "Alert evidence trail"}
