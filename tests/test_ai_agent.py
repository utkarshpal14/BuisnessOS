import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.ai.agent import AIAgent
from app.ai.intelligence_service import AIIntelligenceService
from app.ai.llm_adapter import LLMAdapter, MockLLMAdapter
from app.enterprise.agent import EnterpriseAgent
from app.enterprise.models import BusinessSnapshot
from app.finance.agent import FinanceAgent
from app.planner.models import AgentResult, PlannerTask
from app.planner.registry import AgentRegistry
from app.planner.router import SimpleTaskRouter
from app.planner.service import PlannerService
from app.sales.agent import SalesAgent

FIXTURES_VALID_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "fixtures", "sales", "valid"))
FIXTURES_FINANCE_VALID_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "fixtures", "finance", "valid"))


def make_enterprise_result(snapshot: BusinessSnapshot, status: str = "success") -> dict:
    return {
        "agent_name": "enterprise",
        "status": status,
        "summary": "Overall business summary: ...",
        "data": {"agent": "enterprise", "status": status, "snapshot": snapshot.model_dump()},
    }


class TestMockLLMAdapter(unittest.TestCase):

    def setUp(self):
        self.adapter = MockLLMAdapter()
        self.intelligence_service = AIIntelligenceService()

    def test_is_an_llm_adapter(self):
        self.assertIsInstance(self.adapter, LLMAdapter)

    def test_generate_returns_all_four_sections(self):
        snapshot = BusinessSnapshot(
            task_id="t1",
            query="Give me recommendations for the business",
            domains={"sales": {"total_revenue": 725.0}, "finance": {"net_profit": 2300.0}},
            health_status="Healthy",
            flags=["No major red flags detected."],
        )
        prompt = self.intelligence_service.generate_prompt(snapshot)
        analysis = self.adapter.generate(prompt)

        self.assertIn("Executive Summary:", analysis)
        self.assertIn("Key Risks:", analysis)
        self.assertIn("Opportunities:", analysis)
        self.assertIn("Recommended Actions:", analysis)
        self.assertIn("Healthy", analysis)
        self.assertIn("No major red flags detected.", analysis)

    def test_generate_reflects_data_gaps_as_risks(self):
        snapshot = BusinessSnapshot(
            task_id="t1",
            query="What should we do next?",
            domains={"sales": {"total_revenue": 725.0}, "finance": {}},
            gaps=["Finance data unavailable."],
        )
        prompt = self.intelligence_service.generate_prompt(snapshot)
        analysis = self.adapter.generate(prompt)

        self.assertIn("Key Risks:", analysis)
        self.assertIn("Incomplete data: Finance data unavailable.", analysis)

    def test_generate_never_raises_not_implemented(self):
        # Unlike ClaudeAdapter/OpenAIAdapter, MockLLMAdapter actually returns text.
        try:
            self.adapter.generate("any prompt")
        except NotImplementedError:
            self.fail("MockLLMAdapter.generate() should not raise NotImplementedError")


class TestAIAgentUnit(unittest.TestCase):

    def test_execute_returns_error_when_no_enterprise_result(self):
        agent = AIAgent()
        task = PlannerTask(task_type="enterprise", query="Give me recommendations")
        result = agent.execute(task)

        self.assertEqual(result.status, "error")
        self.assertIsNotNone(result.error_message)

    def test_execute_returns_error_when_enterprise_result_failed(self):
        agent = AIAgent()
        task = PlannerTask(task_type="enterprise", query="Give me recommendations")
        task.metadata["upstream_results"] = {
            "enterprise": {"agent_name": "enterprise", "status": "error", "summary": "unavailable", "data": {}}
        }
        result = agent.execute(task)

        self.assertEqual(result.status, "error")

    def test_execute_returns_error_when_snapshot_missing(self):
        agent = AIAgent()
        task = PlannerTask(task_type="enterprise", query="Give me recommendations")
        task.metadata["upstream_results"] = {
            "enterprise": {"agent_name": "enterprise", "status": "success", "summary": "ok", "data": {}}
        }
        result = agent.execute(task)

        self.assertEqual(result.status, "error")
        self.assertIn("BusinessSnapshot", result.error_message)

    def test_execute_uses_injected_intelligence_service_and_adapter(self):
        captured_prompts = []

        class RecordingAdapter(LLMAdapter):
            def generate(self, prompt: str) -> str:
                captured_prompts.append(prompt)
                return "Executive Summary:\n  stub\nKey Risks:\n  - none\nOpportunities:\n  - none\nRecommended Actions:\n  - none"

        agent = AIAgent(intelligence_service=AIIntelligenceService(), llm_adapter=RecordingAdapter())
        snapshot = BusinessSnapshot(task_id="t1", query="Give me recommendations", domains={"sales": {"total_revenue": 100.0}})
        task = PlannerTask(task_type="enterprise", query="Give me recommendations")
        task.metadata["upstream_results"] = {"enterprise": make_enterprise_result(snapshot)}

        result = agent.execute(task)

        self.assertEqual(result.status, "success")
        self.assertEqual(result.agent_name, "ai")
        self.assertEqual(len(captured_prompts), 1)
        self.assertIn("Give me recommendations", captured_prompts[0])
        self.assertIn("Executive Summary:", result.summary)
        self.assertEqual(result.data["prompt"], captured_prompts[0])
        self.assertEqual(result.confidence, "medium")
        sources = [item.source for item in result.evidence]
        self.assertIn("enterprise_snapshot", sources)
        self.assertIn("enterprise_snapshot:sales", sources)

    def test_execute_is_stateless_across_calls(self):
        agent = AIAgent()
        snapshot = BusinessSnapshot(task_id="t1", query="Give me recommendations", domains={"sales": {"total_revenue": 100.0}})
        task = PlannerTask(task_type="enterprise", query="Give me recommendations")
        task.metadata["upstream_results"] = {"enterprise": make_enterprise_result(snapshot)}

        first = agent.execute(task)
        second = agent.execute(task)
        self.assertEqual(first.summary, second.summary)


class TestRouterRecommendationDetection(unittest.TestCase):

    def setUp(self):
        self.router = SimpleTaskRouter()

    def test_plain_enterprise_query_excludes_ai_agent(self):
        task = PlannerTask(task_type="enterprise", query="Overall business summary")
        self.assertEqual(self.router.route(task), ["sales", "finance", "enterprise"])

    def test_recommendation_query_includes_ai_agent(self):
        cases = [
            "Give me recommendations for the business",
            "What advice do you have for us?",
            "Act as our business advisor",
            "What should we do next?",
            "Suggest an action plan",
        ]
        for query in cases:
            task = PlannerTask(task_type="enterprise", query=query)
            self.assertEqual(
                self.router.route(task),
                ["sales", "finance", "enterprise", "ai"],
                msg=f"query={query!r}",
            )

    def test_sales_and_finance_and_business_routing_unaffected(self):
        self.assertEqual(self.router.route(PlannerTask(task_type="sales", query="Q3 sales")), ["sales"])
        self.assertEqual(self.router.route(PlannerTask(task_type="finance", query="Q3 revenue")), ["finance"])
        self.assertEqual(
            self.router.route(PlannerTask(task_type="business", query="Overall performance")),
            ["sales", "finance"],
        )


class TestAIAgentPlannerIntegration(unittest.TestCase):

    def _build_planner(self):
        registry = AgentRegistry()
        registry.register(SalesAgent(dataset_dir=FIXTURES_VALID_DIR))
        registry.register(FinanceAgent(dataset_dir=FIXTURES_FINANCE_VALID_DIR))
        registry.register(EnterpriseAgent())
        registry.register(AIAgent())
        return PlannerService(registry=registry, router=SimpleTaskRouter())

    def test_recommendation_query_invokes_all_four_agents_in_order(self):
        planner = self._build_planner()
        response = planner.execute_task(
            PlannerTask(task_type="enterprise", query="Give me recommendations for the business")
        )

        self.assertEqual(response.status, "success")
        self.assertEqual(response.participating_agents, ["sales", "finance", "enterprise", "ai"])
        self.assertEqual(len(response.raw_results), 4)

        ai_raw = response.raw_results[-1]
        self.assertEqual(ai_raw["agent_name"], "ai")
        self.assertEqual(ai_raw["status"], "success")
        self.assertIn("Executive Summary:", ai_raw["summary"])
        self.assertIn("Key Risks:", ai_raw["summary"])
        self.assertIn("Opportunities:", ai_raw["summary"])
        self.assertIn("Recommended Actions:", ai_raw["summary"])

    def test_non_recommendation_enterprise_query_does_not_invoke_ai_agent(self):
        planner = self._build_planner()
        response = planner.execute_task(PlannerTask(task_type="enterprise", query="Overall business summary"))

        self.assertEqual(response.status, "success")
        self.assertEqual(response.participating_agents, ["sales", "finance", "enterprise"])
        self.assertNotIn("ai", response.participating_agents)

    def test_ai_agent_analysis_is_grounded_in_real_kpi_numbers(self):
        planner = self._build_planner()
        response = planner.execute_task(
            PlannerTask(task_type="enterprise", query="Give me a business summary and your recommendation")
        )

        ai_raw = response.raw_results[-1]
        # The mock adapter's output is derived from the prompt, which is derived from
        # the real BusinessSnapshot -- confirm the KPI numbers actually flowed through.
        self.assertIn("Healthy", ai_raw["summary"])
        self.assertIn("$725.00", response.raw_results[0]["summary"])
        self.assertIn("$2,300.00", response.raw_results[1]["summary"])


if __name__ == "__main__":
    unittest.main()
