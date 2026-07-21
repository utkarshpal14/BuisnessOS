"""
Planner dependency wiring for the API layer.

This is dependency injection wiring only -- delegating to the shared
app.planner.bootstrap.build_planner(), the same function demo.py uses. No KPI
calculation, routing decision, or agent behavior lives here. Tests override
`get_planner` (via FastAPI's `app.dependency_overrides`) to point agents at fixture
datasets instead of the real ones, without touching any route or Planner code.
"""
from functools import lru_cache

from app.planner.bootstrap import build_planner
from app.planner.service import PlannerService


@lru_cache(maxsize=1)
def get_planner() -> PlannerService:
    """Builds the single production PlannerService instance, cached for the app's lifetime."""
    return build_planner()
