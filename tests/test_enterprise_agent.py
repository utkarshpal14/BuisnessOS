import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.enterprise.agent import EnterpriseAgent
from app.enterprise.analytics_service import EnterpriseAnalyticsService
from app.enterprise.query_mapper import EnterpriseQueryMapper
from app.finance.agent import FinanceAgent
from app.planner.models import PlannerTask
from app.planner.registry import AgentRegistry
from app.planner.router import SimpleTaskRouter
from app.planner.service import PlannerService
from app.sales.agent import SalesAgent

FIXTURES_VALID_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "fixtures", "sales", "valid"))
FIXTURES_FINANCE_VALID_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "fixtures", "finance", "valid"))


class TestEnterpriseQueryMapper(unittest.TestCase):

    def setUp(self):
        self.mapper = EnterpriseQueryMapper()

    def test_known_query_mappings(self):
        cases = {
            "Overall business summary": "summary",
            "Executive dashboard": "executive_dashboard",
            "Business health report": "health_report",
        }
        for query, expected_intent in cases.items():
            self.assertEqual(self.mapper.resolve(query), expected_intent)

    def test_unknown_query_defaults_to_summary(self):
        self.assertEqual(self.mapper.resolve("What's the weather today?"), "summary")


class TestEnterpriseAnalyticsService(unittest.TestCase):

    def test_combined_summary_merges_sales_and_finance(self):
        service = EnterpriseAnalyticsService(domains={
            "sales": {"total_revenue": 725.0, "top_region": {"region": "North", "revenue": 475.0}},
            "finance": {"net_profit": 2300.0, "profit_margin_pct": 20.0},
        })
        result = service.combined_summary()
        self.assertEqual(result["sales_revenue"], 725.0)
        self.assertEqual(result["net_profit"], 2300.0)
        self.assertEqual(result["profit_margin_pct"], 20.0)
        self.assertEqual(result["top_region"]["region"], "North")

    def test_health_assessment_flags_thin_margin_and_decline(self):
        service = EnterpriseAnalyticsService(domains={
            "sales": {"latest_month_growth": {"month": "2023-02", "growth_pct": -5.0}},
            "finance": {"profit_margin_pct": 2.0},
        })
        result = service.health_assessment()
        self.assertEqual(result["health_status"], "At Risk")
        self.assertIn("Profit margin is thin.", result["flags"])
        self.assertIn("Revenue declined month-over-month.", result["flags"])

    def test_health_assessment_healthy_with_no_flags(self):
        service = EnterpriseAnalyticsService(domains={
            "sales": {"latest_month_growth": {"month": "2023-02", "growth_pct": 7.0}},
            "finance": {"profit_margin_pct": 25.0},
        })
        result = service.health_assessment()
        self.assertEqual(result["health_status"], "Healthy")
        self.assertIn("No major red flags detected.", result["flags"])

    def test_unregistered_domain_is_aggregated_via_namespaced_fallback(self):
        # "hr" is not in DOMAIN_FIELD_LABELS -- correctness must not depend on
        # every domain being explicitly registered there.
        service = EnterpriseAnalyticsService(domains={"hr": {"headcount": 42, "attrition_rate": 0.05}})
        result = service.combined_summary()
        self.assertEqual(result["hr_headcount"], 42)
        self.assertEqual(result["hr_attrition_rate"], 0.05)

    def test_no_domains_returns_empty_summary(self):
        service = EnterpriseAnalyticsService()
        self.assertEqual(service.combined_summary(), {})
        self.assertEqual(service.health_assessment()["health_status"], "Unknown")


class TestEnterpriseAgent(unittest.TestCase):

    def test_execute_without_upstream_results_returns_error(self):
        agent = EnterpriseAgent()
        task = PlannerTask(task_type="enterprise", query="Overall business summary")
        result = agent.execute(task)

        self.assertEqual(result.status, "error")
        self.assertIsNotNone(result.error_message)

    def test_execute_aggregates_upstream_sales_and_finance_results(self):
        agent = EnterpriseAgent()
        task = PlannerTask(task_type="enterprise", query="Overall business summary")
        task.metadata["upstream_results"] = {
            "sales": {
                "agent_name": "sales",
                "status": "success",
                "summary": "Total revenue is $725.00.",
                "data": {"total_revenue": 725.0, "top_region": {"region": "North", "revenue": 475.0}},
            },
            "finance": {
                "agent_name": "finance",
                "status": "success",
                "summary": "Net profit is $2,300.00.",
                "data": {"net_profit": 2300.0, "profit_margin_pct": 20.0},
            },
        }
        result = agent.execute(task)

        self.assertEqual(result.agent_name, "enterprise")
        self.assertEqual(result.status, "success")
        self.assertIn("$725.00", result.summary)
        self.assertIn("$2,300.00", result.summary)
        self.assertEqual(result.data["kpi"], "summary")
        self.assertEqual(result.confidence, "high")
        sources = [item.source for item in result.evidence]
        self.assertIn("sales_agent", sources)
        self.assertIn("finance_agent", sources)

    def test_execute_flags_gap_when_one_upstream_agent_failed(self):
        agent = EnterpriseAgent()
        task = PlannerTask(task_type="enterprise", query="Overall business summary")
        task.metadata["upstream_results"] = {
            "sales": {
                "agent_name": "sales",
                "status": "success",
                "summary": "Total revenue is $725.00.",
                "data": {"total_revenue": 725.0},
            },
            "finance": {
                "agent_name": "finance",
                "status": "error",
                "summary": "Finance analysis unavailable.",
                "error_message": "Dataset not found.",
                "data": {},
            },
        }
        result = agent.execute(task)

        self.assertEqual(result.status, "success")
        self.assertIn("Finance data unavailable.", result.summary)
        self.assertEqual(result.confidence, "medium")
        self.assertEqual([item.source for item in result.evidence], ["sales_agent"])

    def test_execute_aggregates_a_brand_new_domain_with_no_agent_code_changes(self):
        # Proof of the generic-aggregation refactor: "hr" is not sales/finance and
        # is not registered in DOMAIN_FIELD_LABELS, yet EnterpriseAgent.execute()
        # needs zero changes to pick it up.
        agent = EnterpriseAgent()
        task = PlannerTask(task_type="enterprise", query="Overall business summary")
        task.metadata["upstream_results"] = {
            "hr": {
                "agent_name": "hr",
                "status": "success",
                "summary": "Headcount analyzed.",
                "data": {"headcount": 42, "attrition_rate": 0.05},
            },
        }
        result = agent.execute(task)

        self.assertEqual(result.status, "success")
        self.assertEqual(result.confidence, "high")
        self.assertEqual([item.source for item in result.evidence], ["hr_agent"])
        snapshot = result.data["snapshot"]
        self.assertEqual(snapshot["domains"]["hr"], {"headcount": 42, "attrition_rate": 0.05})


class TestEnterpriseAgentPlannerIntegration(unittest.TestCase):

    def test_full_enterprise_workflow_through_planner(self):
        registry = AgentRegistry()
        registry.register(SalesAgent(dataset_dir=FIXTURES_VALID_DIR))
        registry.register(FinanceAgent(dataset_dir=FIXTURES_FINANCE_VALID_DIR))
        registry.register(EnterpriseAgent())
        planner = PlannerService(registry=registry, router=SimpleTaskRouter())

        task = PlannerTask(task_type="enterprise", query="Overall business summary")
        response = planner.execute_task(task)

        self.assertEqual(response.status, "success")
        self.assertEqual(response.participating_agents, ["sales", "finance", "enterprise"])
        self.assertEqual(len(response.raw_results), 3)

        enterprise_raw = response.raw_results[-1]
        self.assertEqual(enterprise_raw["agent_name"], "enterprise")
        self.assertIn("$725.00", enterprise_raw["summary"])
        self.assertIn("$2,300.00", enterprise_raw["summary"])

    def test_executive_dashboard_and_health_report_intents(self):
        registry = AgentRegistry()
        registry.register(SalesAgent(dataset_dir=FIXTURES_VALID_DIR))
        registry.register(FinanceAgent(dataset_dir=FIXTURES_FINANCE_VALID_DIR))
        registry.register(EnterpriseAgent())
        planner = PlannerService(registry=registry, router=SimpleTaskRouter())

        dashboard_response = planner.execute_task(
            PlannerTask(task_type="enterprise", query="Executive dashboard")
        )
        self.assertEqual(dashboard_response.status, "success")
        self.assertIn("Executive Dashboard:", dashboard_response.raw_results[-1]["summary"])

        health_response = planner.execute_task(
            PlannerTask(task_type="enterprise", query="Business health report")
        )
        self.assertEqual(health_response.status, "success")
        self.assertIn("Business health status:", health_response.raw_results[-1]["summary"])


if __name__ == "__main__":
    unittest.main()
