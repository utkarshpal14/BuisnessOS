import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from fastapi.testclient import TestClient

from app.ai.agent import AIAgent
from app.api.deps import get_planner
from app.enterprise.agent import EnterpriseAgent
from app.finance.agent import FinanceAgent
from app.main import app
from app.planner.registry import AgentRegistry
from app.planner.router import SimpleTaskRouter
from app.planner.service import PlannerService
from app.sales.agent import SalesAgent

FIXTURES_VALID_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "fixtures", "sales", "valid"))
FIXTURES_FINANCE_VALID_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "fixtures", "finance", "valid"))


def build_fixture_planner() -> PlannerService:
    """A deterministic PlannerService backed by fixture datasets, for API tests."""
    registry = AgentRegistry()
    registry.register(SalesAgent(dataset_dir=FIXTURES_VALID_DIR))
    registry.register(FinanceAgent(dataset_dir=FIXTURES_FINANCE_VALID_DIR))
    registry.register(EnterpriseAgent())
    registry.register(AIAgent())
    return PlannerService(registry=registry, router=SimpleTaskRouter())


class TestBusinessOSAPI(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.fixture_planner = build_fixture_planner()
        app.dependency_overrides[get_planner] = lambda: cls.fixture_planner
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls):
        app.dependency_overrides.clear()

    # -- infrastructure ---------------------------------------------------

    def test_root_endpoint(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("message", response.json())

    def test_health_endpoint_reports_registered_agents(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["status"], "ok")
        self.assertEqual(body["agents_registered"], 4)

    def test_agents_endpoint_lists_registered_agent_names(self):
        response = self.client.get("/agents")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["agents"], ["sales", "finance", "enterprise", "ai"])

    def test_openapi_docs_are_available(self):
        docs_response = self.client.get("/docs")
        self.assertEqual(docs_response.status_code, 200)

        schema_response = self.client.get("/openapi.json")
        self.assertEqual(schema_response.status_code, 200)
        paths = schema_response.json()["paths"]
        for path in ("/health", "/agents", "/query", "/enterprise", "/advisor"):
            self.assertIn(path, paths)

    # -- /query -------------------------------------------------------------

    def test_query_sales_success(self):
        response = self.client.post("/query", json={"task_type": "sales", "query": "Total revenue"})
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["status"], "success")
        self.assertEqual(body["participating_agents"], ["sales"])
        self.assertIn("$725.00", body["summary"])

    def test_query_finance_success(self):
        response = self.client.post("/query", json={"task_type": "finance", "query": "Net profit"})
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["status"], "success")
        self.assertIn("$2,300.00", body["summary"])

    def test_query_business_aggregates_sales_and_finance(self):
        response = self.client.post("/query", json={"task_type": "business", "query": "Comprehensive report"})
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["participating_agents"], ["sales", "finance"])

    def test_query_unknown_task_type_returns_400(self):
        response = self.client.post("/query", json={"task_type": "marketing", "query": "Campaign CTR"})
        self.assertEqual(response.status_code, 400)
        body = response.json()
        self.assertEqual(body["status"], "failed")
        self.assertIn("No routing defined", body["errors"][0])

    def test_query_empty_query_returns_400(self):
        response = self.client.post("/query", json={"task_type": "sales", "query": ""})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["status"], "failed")

    def test_query_missing_field_returns_422(self):
        # FastAPI/Pydantic request validation, before PlannerService ever runs.
        response = self.client.post("/query", json={"query": "Total revenue"})
        self.assertEqual(response.status_code, 422)

    # -- /enterprise ----------------------------------------------------

    def test_enterprise_default_query_excludes_ai_agent(self):
        response = self.client.post("/enterprise", json={})
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["participating_agents"], ["sales", "finance", "enterprise"])
        self.assertIn("$725.00", body["raw_results"][0]["summary"])

    def test_enterprise_recommendation_phrasing_includes_ai_agent(self):
        response = self.client.post("/enterprise", json={"query": "Give me recommendations for the business"})
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["participating_agents"], ["sales", "finance", "enterprise", "ai"])

    # -- /advisor -------------------------------------------------------

    def test_advisor_default_query_invokes_all_four_agents(self):
        response = self.client.post("/advisor", json={})
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["participating_agents"], ["sales", "finance", "enterprise", "ai"])
        ai_result = body["raw_results"][-1]
        self.assertEqual(ai_result["agent_name"], "ai")
        self.assertIn("Executive Summary:", ai_result["summary"])
        self.assertIn("Key Risks:", ai_result["summary"])
        self.assertIn("Opportunities:", ai_result["summary"])
        self.assertIn("Recommended Actions:", ai_result["summary"])

    def test_advisor_guarantees_ai_agent_even_without_recommendation_wording(self):
        # "How is the business doing?" contains no RECOMMENDATION_KEYWORDS on its own --
        # /advisor must still route through the AI Agent.
        response = self.client.post("/advisor", json={"query": "How is the business doing?"})
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertIn("ai", body["participating_agents"])

    def test_advisor_uses_the_real_planner_query_field(self):
        response = self.client.post("/advisor", json={"query": "Give us your recommendation"})
        self.assertEqual(response.status_code, 200)
        # Response is the untouched PlannerResponse shape -- has a task_id, not an
        # API-layer-invented field.
        self.assertIn("task_id", response.json())


if __name__ == "__main__":
    unittest.main()
