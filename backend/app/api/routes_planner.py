"""
Planner-facing API routes for BusinessOS AI.

Every endpoint here is a thin HTTP wrapper around the existing PlannerService --
task_type/query construction is the only logic in this file, mirroring what demo.py
already does for the CLI entry point. No KPI calculation, routing decision, or agent
behavior is duplicated: PlannerResponse is returned as-is, and routing to Sales/
Finance/Enterprise/AI Agents is decided entirely by the existing SimpleTaskRouter.
"""
from fastapi import APIRouter, Depends, Response
from pydantic import BaseModel, Field
from typing import List

from app.api.deps import get_planner
from app.planner.models import PlannerResponse, PlannerTask
from app.planner.router import RECOMMENDATION_KEYWORDS
from app.planner.service import PlannerService

router = APIRouter(prefix="", tags=["planner"])


class HealthResponse(BaseModel):
    status: str
    agents_registered: int


class AgentsResponse(BaseModel):
    agents: List[str]


class QueryRequest(BaseModel):
    task_type: str = Field(..., description="One of: sales, finance, business, enterprise")
    query: str


class EnterpriseRequest(BaseModel):
    query: str = Field(default="Overall business summary")


class AdvisorRequest(BaseModel):
    query: str = Field(default="Give me recommendations for the business")


def _status_code_for(result: PlannerResponse) -> int:
    """Maps a PlannerResponse's own status/errors onto an HTTP status code."""
    if result.status in ("success", "partial_success"):
        return 200
    # status == "failed": distinguish client-caused failures (bad task_type, empty
    # query) -- both raised by PlannerService's own validation/routing -- from
    # anything else, which points at a server-side misconfiguration.
    if any("No routing defined" in e or "Invalid task" in e for e in result.errors):
        return 400
    return 500


def _ensure_recommendation_signal(query: str) -> str:
    """
    Guarantees /advisor always routes through the AI Agent, by making sure the query
    text contains one of SimpleTaskRouter's own RECOMMENDATION_KEYWORDS -- reusing that
    list rather than re-implementing the keyword check here.
    """
    normalized = query.lower()
    if any(keyword in normalized for keyword in RECOMMENDATION_KEYWORDS):
        return query
    return f"{query.rstrip('.')}. Please provide your recommendation."


@router.get("/health", response_model=HealthResponse)
def health(planner: PlannerService = Depends(get_planner)) -> HealthResponse:
    return HealthResponse(status="ok", agents_registered=len(planner.registry.list_agents()))


@router.get("/agents", response_model=AgentsResponse)
def list_agents(planner: PlannerService = Depends(get_planner)) -> AgentsResponse:
    return AgentsResponse(agents=planner.registry.list_agents())


@router.post("/query", response_model=PlannerResponse)
def run_query(
    request: QueryRequest,
    response: Response,
    planner: PlannerService = Depends(get_planner),
) -> PlannerResponse:
    task = PlannerTask(task_type=request.task_type, query=request.query)
    result = planner.execute_task(task)
    response.status_code = _status_code_for(result)
    return result


@router.post("/enterprise", response_model=PlannerResponse)
def run_enterprise(
    request: EnterpriseRequest,
    response: Response,
    planner: PlannerService = Depends(get_planner),
) -> PlannerResponse:
    task = PlannerTask(task_type="enterprise", query=request.query)
    result = planner.execute_task(task)
    response.status_code = _status_code_for(result)
    return result


@router.post("/advisor", response_model=PlannerResponse)
def run_advisor(
    request: AdvisorRequest,
    response: Response,
    planner: PlannerService = Depends(get_planner),
) -> PlannerResponse:
    task = PlannerTask(task_type="enterprise", query=_ensure_recommendation_signal(request.query))
    result = planner.execute_task(task)
    response.status_code = _status_code_for(result)
    return result
