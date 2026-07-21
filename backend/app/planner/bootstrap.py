"""
build_planner(): the single place that knows which agents exist and how to wire
them into a PlannerService.

Every caller that needs a working PlannerService -- the CLI (demo.py), the FastAPI
layer (app/api/deps.py), and any future entry point (Scheduler/Sentinel included) --
calls this function instead of independently constructing an AgentRegistry. Adding a
new agent means editing this one function, not every caller.
"""
from typing import Optional

from app.ai.agent import AIAgent
from app.enterprise.agent import EnterpriseAgent
from app.finance.agent import FinanceAgent
from app.planner.registry import AgentRegistry
from app.planner.router import SimpleTaskRouter
from app.planner.service import PlannerService
from app.sales.agent import SalesAgent


def build_planner(
    sales_dataset_dir: Optional[str] = None,
    finance_dataset_dir: Optional[str] = None,
) -> PlannerService:
    """
    Constructs the standard PlannerService with every live agent registered.

    `sales_dataset_dir`/`finance_dataset_dir` default to each agent's own
    DEFAULT_DATASET_DIR when omitted (real datasets). Callers that need a
    deterministic/fixture-backed PlannerService (tests, or a CLI falling back to
    bundled sample data) pass them explicitly.
    """
    registry = AgentRegistry()
    registry.register(SalesAgent(dataset_dir=sales_dataset_dir))
    registry.register(FinanceAgent(dataset_dir=finance_dataset_dir))
    registry.register(EnterpriseAgent())
    registry.register(AIAgent())
    return PlannerService(registry=registry, router=SimpleTaskRouter())
