import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.planner.bootstrap import build_planner
from app.planner.models import PlannerTask
from app.planner.service import PlannerService

FIXTURES_SALES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "fixtures", "sales", "valid"))
FIXTURES_FINANCE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "fixtures", "finance", "valid"))


class TestBuildPlanner(unittest.TestCase):
    """
    build_planner() is the single place demo.py and app/api/deps.py both delegate
    to for agent registration -- these tests exist so a future agent addition (or
    removal) only has to be correct in one function, not re-verified per caller.
    """

    def test_returns_a_planner_service_with_all_four_agents_registered(self):
        planner = build_planner(sales_dataset_dir=FIXTURES_SALES_DIR, finance_dataset_dir=FIXTURES_FINANCE_DIR)
        self.assertIsInstance(planner, PlannerService)
        self.assertEqual(planner.registry.list_agents(), ["sales", "finance", "enterprise", "ai"])

    def test_built_planner_answers_a_sales_query_end_to_end(self):
        planner = build_planner(sales_dataset_dir=FIXTURES_SALES_DIR, finance_dataset_dir=FIXTURES_FINANCE_DIR)
        response = planner.execute_task(PlannerTask(task_type="sales", query="Total revenue"))
        self.assertEqual(response.status, "success")
        self.assertIn("$725.00", response.summary)

    def test_dataset_dirs_default_to_none_for_production_use(self):
        # No dataset dirs passed -- each agent falls back to its own
        # DEFAULT_DATASET_DIR, exactly like app/api/deps.py's production usage.
        planner = build_planner()
        self.assertEqual(planner.registry.list_agents(), ["sales", "finance", "enterprise", "ai"])


if __name__ == "__main__":
    unittest.main()
