"""
Demo: Real Finance Intelligence Agent, end to end through the Planner Framework.

    User Query -> Planner -> Task Router -> Finance Intelligence Agent
               -> Finance Dataset -> Business KPI Analysis -> PlannerResponse

Run with:  python demo_finance.py
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "backend")))

from app.planner.models import PlannerTask
from app.planner.registry import AgentRegistry
from app.planner.router import SimpleTaskRouter
from app.planner.service import PlannerService
from app.finance.agent import FinanceAgent
from app.finance.data_loader import DEFAULT_DATASET_DIR

REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
FIXTURE_DATASET_DIR = os.path.join(REPO_ROOT, "tests", "fixtures", "finance", "valid")

SAMPLE_QUERIES = [
    "Show finance summary",
    "Net profit",
    "Total expenses",
    "Profit margin",
    "Monthly profit",
    "Revenue vs expenses",
]


def resolve_dataset_dir() -> str:
    has_real_dataset = os.path.isdir(DEFAULT_DATASET_DIR) and any(
        f.endswith(".csv") for f in os.listdir(DEFAULT_DATASET_DIR)
    )
    if has_real_dataset:
        print(f"[dataset] Using real dataset found in: {DEFAULT_DATASET_DIR}")
        return str(DEFAULT_DATASET_DIR)

    print(f"[dataset] No CSV found in '{DEFAULT_DATASET_DIR}'.")
    print(f"[dataset] Falling back to the bundled sample dataset for this demo: {FIXTURE_DATASET_DIR}")
    print("[dataset] Drop a real Kaggle finance CSV into datasets/finance/ to use real data instead.\n")
    return FIXTURE_DATASET_DIR


def print_section(title: str) -> None:
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)


def run_query(planner: PlannerService, query: str) -> None:
    print_section(f"INCOMING QUERY: \"{query}\"")

    task = PlannerTask(task_type="finance", query=query)
    print(f"[Planner]      received task_id={task.task_id} (source={task.source})")
    print(f"[Task Router]  task_type='{task.task_type}' -> routed to agent(s): finance")

    response = planner.execute_task(task)

    print(f"[Finance Agent] executed against dataset -> status={response.status}")
    if response.raw_results:
        kpi = response.raw_results[0]["data"].get("kpi")
        print(f"[KPI Analysis]  computed KPI: '{kpi}'")

    print_section("PLANNER RESPONSE")
    print(f"  status               : {response.status}")
    print(f"  participating_agents : {response.participating_agents}")
    print(f"  summary              : {response.summary}")
    print(f"  execution_time_ms    : {response.execution_time_ms:.2f}")
    if response.errors:
        print(f"  errors               : {response.errors}")


def main() -> None:
    dataset_dir = resolve_dataset_dir()

    registry = AgentRegistry()
    registry.register(FinanceAgent(dataset_dir=dataset_dir))
    planner = PlannerService(registry=registry, router=SimpleTaskRouter())

    for query in SAMPLE_QUERIES:
        run_query(planner, query)

    print("\nDemo complete.\n")


if __name__ == "__main__":
    main()
