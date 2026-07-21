"""
Unified BusinessOS AI demo entry point.

This CLI routes every user query through the existing PlannerService,
so it exercises the same architecture used by the backend workflow.
"""
import os
import sys
from typing import List

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "backend")))

from app.common.keyword_mapper import matches_any
from app.finance.data_loader import DEFAULT_DATASET_DIR as FINANCE_DEFAULT_DATASET_DIR
from app.planner.bootstrap import build_planner
from app.planner.models import PlannerTask
from app.planner.service import PlannerService
from app.sales.data_loader import DEFAULT_DATASET_DIR as SALES_DEFAULT_DATASET_DIR

REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
FIXTURE_SALES_DIR = os.path.join(REPO_ROOT, "tests", "fixtures", "sales", "valid")
FIXTURE_FINANCE_DIR = os.path.join(REPO_ROOT, "tests", "fixtures", "finance", "valid")


def resolve_dataset_dir(default_dir: str, fixture_dir: str, label: str) -> str:
    has_real_dataset = os.path.isdir(default_dir) and any(
        f.endswith(".csv") for f in os.listdir(default_dir)
    )
    if has_real_dataset:
        print(f"[{label}] Using real dataset found in: {default_dir}")
        return str(default_dir)

    print(f"[{label}] No CSV found in '{default_dir}'.")
    print(f"[{label}] Falling back to bundled sample data: {fixture_dir}")
    return fixture_dir


def infer_task_type(query: str) -> str:
    sales_terms = [
        "sales",
        "revenue",
        "orders",
        "customer",
        "product",
        "region",
        "monthly",
        "daily",
        "growth",
        "aov",
    ]
    finance_terms = [
        "finance",
        "profit",
        "expense",
        "margin",
        "cost",
        "expenses",
    ]
    enterprise_terms = [
        "enterprise",
        "overall business",
        "business summary",
        "executive dashboard",
        "business health",
        "health report",
        "recommend",
        "recommendation",
        "advisor",
        "advice",
        "action plan",
        "next steps",
    ]

    has_enterprise = matches_any(query, enterprise_terms)
    has_sales = matches_any(query, sales_terms)
    has_finance = matches_any(query, finance_terms)

    if has_enterprise:
        return "enterprise"
    if has_sales and has_finance:
        return "business"
    if has_sales:
        return "sales"
    if has_finance:
        return "finance"
    return "business"


def print_welcome_screen() -> None:
    print("\n" + "=" * 70)
    print("BusinessOS AI")
    print("=" * 70)
    print("Unified console for Sales and Finance intelligence.")
    print("Type 'help' to see supported queries.")
    print("Type 'exit' to quit.\n")


def print_help() -> None:
    print("\nSupported Sales queries:")
    for item in [
        "summary / overview",
        "total revenue",
        "total orders",
        "average order value",
        "top products",
        "top customers",
        "sales by region",
        "monthly revenue",
        "daily sales",
        "revenue growth",
    ]:
        print(f"  - {item}")

    print("\nSupported Finance queries:")
    for item in [
        "summary / overview",
        "net profit",
        "total expenses",
        "profit margin",
        "monthly profit",
        "revenue vs expenses",
    ]:
        print(f"  - {item}")

    print("\nSupported Enterprise queries:")
    for item in [
        "overall business summary",
        "executive dashboard",
        "business health report",
        "business recommendations / advice (adds AI analysis: risks, opportunities, actions)",
    ]:
        print(f"  - {item}")

    print("\nExamples:")
    print("  - Show sales summary")
    print("  - Top products")
    print("  - Net profit")
    print("  - Revenue vs expenses")
    print("  - Overall business summary")
    print("  - Executive dashboard")
    print("  - Business health report")
    print("  - Give me recommendations for the business")
    print()


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

    if response.evidence:
        print("Evidence             :")
        for item in response.evidence:
            print(f"  - [{item.source}] {item.data_point}")


def build_cli_planner() -> PlannerService:
    """
    CLI-specific dataset resolution (falls back to bundled fixtures when no real
    CSV is present) on top of the shared app.planner.bootstrap.build_planner() --
    the same function app/api/deps.py uses, so both entry points register the
    exact same set of agents with no duplicated registration code.
    """
    sales_dir = resolve_dataset_dir(SALES_DEFAULT_DATASET_DIR, FIXTURE_SALES_DIR, "sales")
    finance_dir = resolve_dataset_dir(FINANCE_DEFAULT_DATASET_DIR, FIXTURE_FINANCE_DIR, "finance")
    return build_planner(sales_dataset_dir=sales_dir, finance_dataset_dir=finance_dir)


def main() -> None:
    print_welcome_screen()
    planner = build_cli_planner()

    while True:
        try:
            query = input("BusinessOS AI > ").strip()
        except KeyboardInterrupt:
            print("\nGoodbye.")
            break

        if not query:
            print("Please enter a question or type 'exit' to quit.\n")
            continue

        if query.lower() in {"exit", "quit"}:
            print("Goodbye.")
            break

        if query.lower() == "help":
            print_help()
            continue

        task_type = infer_task_type(query)
        task = PlannerTask(task_type=task_type, query=query)
        response = planner.execute_task(task)
        print_response(response)


if __name__ == "__main__":
    main()
