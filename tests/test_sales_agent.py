import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.planner.models import PlannerTask
from app.sales.agent import SalesAgent
from app.sales.analytics_service import SalesAnalyticsService
from app.sales.data_access import SalesDataAccess
from app.sales.data_loader import SalesDataLoader
from app.sales.exceptions import DatasetNotFoundError, EmptyDatasetError, SchemaValidationError
from app.sales.query_mapper import SalesQueryMapper

FIXTURES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "fixtures", "sales"))
VALID_DIR = os.path.join(FIXTURES_DIR, "valid")
INVALID_SCHEMA_DIR = os.path.join(FIXTURES_DIR, "invalid_schema")
EMPTY_DIR = os.path.join(FIXTURES_DIR, "empty")
MALFORMED_DIR = os.path.join(FIXTURES_DIR, "malformed_rows")
MISSING_DIR = os.path.join(FIXTURES_DIR, "does_not_exist")


class TestSalesDataLoader(unittest.TestCase):

    def test_loads_and_cleans_valid_dataset(self):
        df = SalesDataLoader(dataset_dir=VALID_DIR).load()
        self.assertEqual(len(df), 6)
        self.assertIn("revenue", df.columns)
        self.assertAlmostEqual(float(df["revenue"].sum()), 725.0, places=2)

    def test_missing_dataset_directory_raises(self):
        with self.assertRaises(DatasetNotFoundError):
            SalesDataLoader(dataset_dir=MISSING_DIR).load()

    def test_invalid_schema_raises(self):
        with self.assertRaises(SchemaValidationError):
            SalesDataLoader(dataset_dir=INVALID_SCHEMA_DIR).load()

    def test_empty_csv_raises(self):
        with self.assertRaises(EmptyDatasetError):
            SalesDataLoader(dataset_dir=EMPTY_DIR).load()

    def test_malformed_rows_are_dropped_not_crashed(self):
        df = SalesDataLoader(dataset_dir=MALFORMED_DIR).load()
        # 4 rows in the fixture; 2 are malformed (bad date, non-numeric quantity) and dropped.
        self.assertEqual(len(df), 2)
        self.assertAlmostEqual(float(df["revenue"].sum()), 150.0, places=2)


class TestSalesDataAccess(unittest.TestCase):
    """The gateway SalesAgent depends on -- never SalesDataLoader directly."""

    def test_load_returns_same_data_as_the_underlying_loader(self):
        gateway = SalesDataAccess(dataset_dir=VALID_DIR)
        df = gateway.load()
        self.assertEqual(len(df), 6)
        self.assertAlmostEqual(float(df["revenue"].sum()), 725.0, places=2)

    def test_load_accepts_a_role_without_erroring(self):
        # No RBAC exists yet -- role is accepted and currently ignored, but the
        # gateway must not reject or require it.
        gateway = SalesDataAccess(dataset_dir=VALID_DIR)
        df_no_role = gateway.load()
        df_with_role = gateway.load(role="CEO")
        self.assertEqual(len(df_no_role), len(df_with_role))

    def test_load_propagates_missing_dataset_error(self):
        gateway = SalesDataAccess(dataset_dir=MISSING_DIR)
        with self.assertRaises(DatasetNotFoundError):
            gateway.load()


class TestSalesAnalyticsService(unittest.TestCase):

    def setUp(self):
        self.df = SalesDataLoader(dataset_dir=VALID_DIR).load()
        self.service = SalesAnalyticsService(self.df)

    def test_total_revenue(self):
        self.assertAlmostEqual(self.service.total_revenue()["total_revenue"], 725.0, places=2)

    def test_total_orders(self):
        self.assertEqual(self.service.total_orders()["total_orders"], 6)

    def test_average_order_value(self):
        self.assertAlmostEqual(self.service.average_order_value()["average_order_value"], 120.83, places=2)

    def test_monthly_revenue(self):
        months = self.service.monthly_revenue()["monthly_revenue"]
        self.assertEqual([m["month"] for m in months], ["2023-01", "2023-02"])
        self.assertAlmostEqual(months[0]["revenue"], 350.0, places=2)
        self.assertAlmostEqual(months[1]["revenue"], 375.0, places=2)

    def test_sales_by_region(self):
        result = self.service.sales_by_region()
        self.assertTrue(result["available"])
        self.assertEqual(result["sales_by_region"][0]["region"], "North")
        self.assertAlmostEqual(result["sales_by_region"][0]["revenue"], 475.0, places=2)

    def test_top_products(self):
        result = self.service.top_products()
        self.assertTrue(result["available"])
        self.assertEqual(result["top_products"][0]["product"], "Widget A")
        self.assertAlmostEqual(result["top_products"][0]["revenue"], 300.0, places=2)

    def test_top_customers(self):
        result = self.service.top_customers()
        self.assertTrue(result["available"])
        self.assertEqual(result["top_customers"][0]["customer"], "Alice")

    def test_revenue_growth(self):
        growth = self.service.revenue_growth()["revenue_growth"]
        self.assertIsNone(growth[0]["growth_pct"])
        self.assertAlmostEqual(growth[1]["growth_pct"], 7.14, places=2)

    def test_daily_sales(self):
        result = self.service.daily_sales()
        self.assertEqual(result["days_covered"], 6)


class TestSalesQueryMapper(unittest.TestCase):

    def setUp(self):
        self.mapper = SalesQueryMapper()

    def test_known_query_mappings(self):
        cases = {
            "Show sales summary": "summary",
            "Total revenue": "total_revenue",
            "Top products": "top_products",
            "Sales by region": "sales_by_region",
            "Monthly sales": "monthly_revenue",
            "Daily sales": "daily_sales",
            "Average order value": "average_order_value",
        }
        for query, expected_intent in cases.items():
            self.assertEqual(self.mapper.resolve(query), expected_intent)

    def test_unknown_query_returns_unknown_intent(self):
        self.assertEqual(self.mapper.resolve("What's the weather today?"), "unknown")


class TestSalesAgent(unittest.TestCase):

    def test_execute_returns_success_result_for_valid_dataset(self):
        agent = SalesAgent(dataset_dir=VALID_DIR)
        task = PlannerTask(task_type="sales", query="Total revenue")
        result = agent.execute(task)

        self.assertEqual(result.agent_name, "sales")
        self.assertEqual(result.status, "success")
        self.assertIn("$725.00", result.summary)
        self.assertEqual(result.data["agent"], "sales")
        self.assertEqual(result.data["kpi"], "total_revenue")
        self.assertEqual(result.confidence, "high")
        self.assertTrue(len(result.evidence) >= 1)
        self.assertIn("total_revenue", result.evidence[0].source)

    def test_execute_handles_missing_dataset_gracefully(self):
        agent = SalesAgent(dataset_dir=MISSING_DIR)
        task = PlannerTask(task_type="sales", query="Total revenue")
        result = agent.execute(task)

        self.assertEqual(result.status, "error")
        self.assertIsNotNone(result.error_message)
        self.assertEqual(result.confidence, "low")
        self.assertEqual(result.evidence, [])

    def test_execute_handles_invalid_schema_gracefully(self):
        agent = SalesAgent(dataset_dir=INVALID_SCHEMA_DIR)
        task = PlannerTask(task_type="sales", query="Total revenue")
        result = agent.execute(task)

        self.assertEqual(result.status, "error")

    def test_execute_handles_empty_dataset_gracefully(self):
        agent = SalesAgent(dataset_dir=EMPTY_DIR)
        task = PlannerTask(task_type="sales", query="Total revenue")
        result = agent.execute(task)

        self.assertEqual(result.status, "error")

    def test_execute_returns_guidance_for_unknown_intent(self):
        agent = SalesAgent(dataset_dir=VALID_DIR)
        task = PlannerTask(task_type="sales", query="What's the weather today?")
        result = agent.execute(task)

        self.assertEqual(result.status, "success")
        self.assertEqual(result.data["kpi"], "unknown")
        self.assertIn("I couldn't understand the requested sales KPI", result.summary)
        self.assertEqual(result.confidence, "low")

    def test_agent_depends_on_the_data_access_gateway_not_the_raw_loader(self):
        agent = SalesAgent(dataset_dir=VALID_DIR)
        self.assertTrue(hasattr(agent, "_data_access"))
        self.assertIsInstance(agent._data_access, SalesDataAccess)
        self.assertFalse(hasattr(agent, "_data_loader"))

    def test_execute_is_stateless_across_calls(self):
        agent = SalesAgent(dataset_dir=VALID_DIR)
        task = PlannerTask(task_type="sales", query="Total revenue")
        first = agent.execute(task)
        second = agent.execute(task)
        self.assertEqual(first.data["total_revenue"], second.data["total_revenue"])


class TestSalesAgentPlannerIntegration(unittest.TestCase):

    def test_full_workflow_through_planner(self):
        from app.planner.registry import AgentRegistry
        from app.planner.service import PlannerService

        registry = AgentRegistry()
        registry.register(SalesAgent(dataset_dir=VALID_DIR))
        planner = PlannerService(registry=registry)

        task = PlannerTask(task_type="sales", query="Show sales summary")
        response = planner.execute_task(task)

        self.assertEqual(response.status, "success")
        self.assertEqual(response.participating_agents, ["sales"])
        self.assertIn("Total revenue is $725.00", response.summary)
        self.assertEqual(response.raw_results[0]["data"]["kpi"], "summary")


if __name__ == "__main__":
    unittest.main()
