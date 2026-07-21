"""
Interactive BusinessOS AI sales demo.

Run with: python demo_sales.py
"""
import os
import sys
from typing import Optional

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "backend")))

from app.planner.models import PlannerTask
from app.planner.registry import AgentRegistry
from app.planner.router import SimpleTaskRouter
from app.planner.service import PlannerService
from app.sales.agent import SalesAgent
from app.sales.data_loader import DEFAULT_DATASET_DIR

REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
FIXTURE_DATASET_DIR = os.path.join(REPO_ROOT, "tests", "fixtures", "sales", "valid")


def resolve_dataset_dir() -> str:
    has_real_dataset = os.path.isdir(DEFAULT_DATASET_DIR) and any(
        f.endswith(".csv") for f in os.listdir(DEFAULT_DATASET_DIR)
    )
    if has_real_dataset:
        print(f"[dataset] Using real dataset found in: {DEFAULT_DATASET_DIR}")
        return str(DEFAULT_DATASET_DIR)

    print(f"[dataset] No CSV found in '{DEFAULT_DATASET_DIR}'.")
    print(f"[dataset] Falling back to the bundled sample dataset for this demo: {FIXTURE_DATASET_DIR}")
    print("[dataset] Drop a real Kaggle sales CSV into datasets/sales/ to use real data instead.\n")
    return FIXTURE_DATASET_DIR


def print_welcome_screen() -> None:
    print("\n" + "=" * 70)
    print("BusinessOS AI - Sales Intelligence Demo")
    print("=" * 70)
    print("Enter a sales-related question to query the planner.")
    print("Type 'exit' to quit.\n")


def print_response(response) -> None:
    print("\n" + "-" * 70)
    print("Planner Response")
    print("-" * 70)
    print(f"Status               : {response.status}")
    print(f"Task ID              : {response.task_id}")
    print(f"Participating Agents : {response.participating_agents}")
    print(f"Summary              : {response.summary}")
    print(f"Execution Time (ms)  : {response.execution_time_ms:.2f}")

    if response.errors:
        print("Errors               :")
        for error in response.errors:
            print(f"  - {error}")

    if response.raw_results:
        print("Raw Results          :")
        for index, raw in enumerate(response.raw_results, start=1):
            print(f"  {index}. {raw.get('summary', '')}")


def build_planner() -> PlannerService:
    dataset_dir = resolve_dataset_dir()
    registry = AgentRegistry()
    registry.register(SalesAgent(dataset_dir=dataset_dir))
    return PlannerService(registry=registry, router=SimpleTaskRouter())


def main() -> None:
    print_welcome_screen()
    planner = build_planner()

    while True:
        try:
            query = input("BusinessOS AI > ").strip()
        except KeyboardInterrupt:
            print("\nGoodbye.")
            break

        if not query:
            print("Please enter a question or type 'exit' to quit.\n")
            continue

        if query.lower() == "exit":
            print("Goodbye.")
            break

        task = PlannerTask(task_type="sales", query=query)
        response = planner.execute_task(task)
        print_response(response)


if __name__ == "__main__":
    main()
