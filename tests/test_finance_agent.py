import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.planner.models import PlannerTask
from app.finance.agent import FinanceAgent
from app.finance.analytics_service import FinanceAnalyticsService
from app.finance.data_access import FinanceDataAccess
from app.finance.data_loader import FinanceDataLoader
from app.finance.exceptions import DatasetNotFoundError, EmptyDatasetError, SchemaValidationError
from app.finance.query_mapper import FinanceQueryMapper

FIXTURES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "fixtures", "finance"))
VALID_DIR = os.path.join(FIXTURES_DIR, "valid")
INVALID_SCHEMA_DIR = os.path.join(FIXTURES_DIR, "invalid_schema")
EMPTY_DIR = os.path.join(FIXTURES_DIR, "empty")
MALFORMED_DIR = os.path.join(FIXTURES_DIR, "malformed_rows")
MISSING_DIR = os.path.join(FIXTURES_DIR, "does_not_exist")


class TestFinanceDataLoader(unittest.TestCase):

    def test_loads_and_cleans_valid_dataset(self):
        df = FinanceDataLoader(dataset_dir=VALID_DIR).load()
        self.assertEqual(len(df), 4)
        self.assertIn("profit", df.columns)
        self.assertAlmostEqual(float(df["profit"].sum()), 2300.0, places=2)

    def test_missing_dataset_directory_raises(self):
        with self.assertRaises(DatasetNotFoundError):
            FinanceDataLoader(dataset_dir=MISSING_DIR).load()

    def test_invalid_schema_raises(self):
        with self.assertRaises(SchemaValidationError):
            FinanceDataLoader(dataset_dir=INVALID_SCHEMA_DIR).load()

    def test_empty_csv_raises(self):
        with self.assertRaises(EmptyDatasetError):
            FinanceDataLoader(dataset_dir=EMPTY_DIR).load()

    def test_malformed_rows_are_dropped_not_crashed(self):
        df = FinanceDataLoader(dataset_dir=MALFORMED_DIR).load()
        # 4 rows in the fixture; 2 are malformed (bad date, non-numeric expenses) and dropped.
        self.assertEqual(len(df), 2)
        self.assertAlmostEqual(float(df["profit"].sum()), 1200.0, places=2)


class TestFinanceDataAccess(unittest.TestCase):
    """The gateway FinanceAgent depends on -- never FinanceDataLoader directly."""

    def test_load_returns_same_data_as_the_underlying_loader(self):
        gateway = FinanceDataAccess(dataset_dir=VALID_DIR)
        df = gateway.load()
        self.assertEqual(len(df), 4)
        self.assertAlmostEqual(float(df["profit"].sum()), 2300.0, places=2)

    def test_load_accepts_a_role_without_erroring(self):
        gateway = FinanceDataAccess(dataset_dir=VALID_DIR)
        df_no_role = gateway.load()
        df_with_role = gateway.load(role="CFO")
        self.assertEqual(len(df_no_role), len(df_with_role))

    def test_load_propagates_missing_dataset_error(self):
        gateway = FinanceDataAccess(dataset_dir=MISSING_DIR)
        with self.assertRaises(DatasetNotFoundError):
            gateway.load()


class TestFinanceAnalyticsService(unittest.TestCase):

    def setUp(self):
        self.df = FinanceDataLoader(dataset_dir=VALID_DIR).load()
        self.service = FinanceAnalyticsService(self.df)

    def test_total_revenue(self):
        self.assertAlmostEqual(self.service.total_revenue()["total_revenue"], 5500.0, places=2)

    def test_total_expenses(self):
        self.assertAlmostEqual(self.service.total_expenses()["total_expenses"], 3200.0, places=2)

    def test_net_profit(self):
        self.assertAlmostEqual(self.service.net_profit()["net_profit"], 2300.0, places=2)

    def test_profit_margin(self):
        self.assertAlmostEqual(self.service.profit_margin()["profit_margin_pct"], 41.82, places=2)

    def test_monthly_profit(self):
        months = self.service.monthly_profit()["monthly_profit"]
        self.assertEqual([m["month"] for m in months], ["2023-01", "2023-02"])
        self.assertAlmostEqual(months[0]["profit"], 1000.0, places=2)
        self.assertAlmostEqual(months[1]["profit"], 1300.0, places=2)

    def test_revenue_vs_expenses(self):
        rows = self.service.revenue_vs_expenses()["revenue_vs_expenses"]
        self.assertEqual(rows[0]["month"], "2023-01")
        self.assertAlmostEqual(rows[0]["revenue"], 2500.0, places=2)
        self.assertAlmostEqual(rows[0]["expenses"], 1500.0, places=2)
        self.assertAlmostEqual(rows[1]["revenue"], 3000.0, places=2)
        self.assertAlmostEqual(rows[1]["expenses"], 1700.0, places=2)

    def test_summary(self):
        summary = self.service.summary()
        self.assertAlmostEqual(summary["net_profit"], 2300.0, places=2)
        self.assertEqual(summary["latest_month_profit"]["month"], "2023-02")


class TestFinanceQueryMapper(unittest.TestCase):

    def setUp(self):
        self.mapper = FinanceQueryMapper()

    def test_known_query_mappings(self):
        cases = {
            "Show finance summary": "summary",
            "Net profit": "net_profit",
            "Total expenses": "total_expenses",
            "Profit margin": "profit_margin",
            "Monthly profit": "monthly_profit",
            "Revenue vs expenses": "revenue_vs_expenses",
        }
        for query, expected_intent in cases.items():
            self.assertEqual(self.mapper.resolve(query), expected_intent)

    def test_unknown_query_falls_back_to_summary(self):
        self.assertEqual(self.mapper.resolve("What's the weather today?"), "summary")


class TestFinanceAgent(unittest.TestCase):

    def test_execute_returns_success_result_for_valid_dataset(self):
        agent = FinanceAgent(dataset_dir=VALID_DIR)
        task = PlannerTask(task_type="finance", query="Net profit")
        result = agent.execute(task)

        self.assertEqual(result.agent_name, "finance")
        self.assertEqual(result.status, "success")
        self.assertIn("$2,300.00", result.summary)
        self.assertEqual(result.data["agent"], "finance")
        self.assertEqual(result.data["kpi"], "net_profit")
        self.assertEqual(result.confidence, "high")
        self.assertTrue(len(result.evidence) >= 1)
        self.assertIn("net_profit", result.evidence[0].source)

    def test_execute_handles_missing_dataset_gracefully(self):
        agent = FinanceAgent(dataset_dir=MISSING_DIR)
        task = PlannerTask(task_type="finance", query="Net profit")
        result = agent.execute(task)

        self.assertEqual(result.status, "error")
        self.assertIsNotNone(result.error_message)
        self.assertEqual(result.confidence, "low")
        self.assertEqual(result.evidence, [])

    def test_execute_handles_invalid_schema_gracefully(self):
        agent = FinanceAgent(dataset_dir=INVALID_SCHEMA_DIR)
        task = PlannerTask(task_type="finance", query="Net profit")
        result = agent.execute(task)

        self.assertEqual(result.status, "error")

    def test_execute_handles_empty_dataset_gracefully(self):
        agent = FinanceAgent(dataset_dir=EMPTY_DIR)
        task = PlannerTask(task_type="finance", query="Net profit")
        result = agent.execute(task)

        self.assertEqual(result.status, "error")

    def test_agent_depends_on_the_data_access_gateway_not_the_raw_loader(self):
        agent = FinanceAgent(dataset_dir=VALID_DIR)
        self.assertTrue(hasattr(agent, "_data_access"))
        self.assertIsInstance(agent._data_access, FinanceDataAccess)
        self.assertFalse(hasattr(agent, "_data_loader"))

    def test_execute_is_stateless_across_calls(self):
        agent = FinanceAgent(dataset_dir=VALID_DIR)
        task = PlannerTask(task_type="finance", query="Net profit")
        first = agent.execute(task)
        second = agent.execute(task)
        self.assertEqual(first.data["net_profit"], second.data["net_profit"])


class TestFinanceAgentPlannerIntegration(unittest.TestCase):

    def test_full_workflow_through_planner(self):
        from app.planner.registry import AgentRegistry
        from app.planner.service import PlannerService

        registry = AgentRegistry()
        registry.register(FinanceAgent(dataset_dir=VALID_DIR))
        planner = PlannerService(registry=registry)

        task = PlannerTask(task_type="finance", query="Show finance summary")
        response = planner.execute_task(task)

        self.assertEqual(response.status, "success")
        self.assertEqual(response.participating_agents, ["finance"])
        self.assertIn("Net profit is $2,300.00", response.summary)
        self.assertEqual(response.raw_results[0]["data"]["kpi"], "summary")


if __name__ == "__main__":
    unittest.main()
