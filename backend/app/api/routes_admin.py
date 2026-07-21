from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="", tags=["admin"])

class SentinelConfig(BaseModel):
    kpi: str
    threshold_pct: float
    window_days: int

@router.post("/sentinel/run")
def trigger_sentinel():
    return {"anomalies_found": 0, "tasks_created": []}

@router.post("/sentinel/config")
def update_config(config: SentinelConfig):
    return {"status": "updated", "config": config}

@router.get("/reports")
def get_audit_logs():
    return []
