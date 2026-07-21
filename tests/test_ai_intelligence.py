import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.ai.intelligence_service import AIIntelligenceService
from app.ai.llm_adapter import ClaudeAdapter, LLMAdapter, OpenAIAdapter
from app.enterprise.agent import EnterpriseAgent
from app.enterprise.models import BusinessSnapshot
from app.finance.agent import FinanceAgent
from app.planner.models import PlannerTask
from app.planner.registry import AgentRegistry
from app.planner.router import SimpleTaskRouter
from app.planner.service import PlannerService
from app.sales.agent import SalesAgent

FIXTURES_VALID_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "fixtures", "sales", "valid"))
FIXTURES_FINANCE_VALID_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "fixtures", "finance", "valid"))


class TestBusinessSnapshotModel(unittest.TestCase):

    def test_construction_and_defaults(self):
        snapshot = BusinessSnapshot(task_id="t1", query="Overall business summary")
        self.assertEqual(snapshot.domains, {})
        self.assertEqual(snapshot.flags, [])
        self.assertEqual(snapshot.gaps, [])
        self.assertIsNone(snapshot.health_status)

    def test_serializes_to_plain_dict(self):
        snapshot = BusinessSnapshot(
            task_id="t1",
            query="Overall business summary",
            domains={"sales": {"total_revenue": 725.0}},
            health_status="Healthy",
            flags=["No major red flags detected."],
        )
        dumped = snapshot.model_dump()
        self.assertEqual(dumped["domains"]["sales"]["total_revenue"], 725.0)
        self.assertEqual(dumped["health_status"], "Healthy")


class TestEnterpriseAgentReturnsSnapshot(unittest.TestCase):

    def test_execute_attaches_business_snapshot(self):
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
                "status": "success",
                "summary": "Net profit is $2,300.00.",
                "data": {"net_profit": 2300.0, "profit_margin_pct": 20.0},
            },
        }
        result = agent.execute(task)

        self.assertIn("snapshot", result.data)
        snapshot_dict = result.data["snapshot"]
        self.assertEqual(snapshot_dict["task_id"], task.task_id)
        self.assertEqual(snapshot_dict["domains"]["sales"]["total_revenue"], 725.0)
        self.assertEqual(snapshot_dict["domains"]["finance"]["net_profit"], 2300.0)
        self.assertEqual(snapshot_dict["health_status"], "Healthy")

    def test_full_workflow_through_planner_carries_snapshot(self):
        registry = AgentRegistry()
        registry.register(SalesAgent(dataset_dir=FIXTURES_VALID_DIR))
        registry.register(FinanceAgent(dataset_dir=FIXTURES_FINANCE_VALID_DIR))
        registry.register(EnterpriseAgent())
        planner = PlannerService(registry=registry, router=SimpleTaskRouter())

        response = planner.execute_task(PlannerTask(task_type="enterprise", query="Overall business summary"))
        enterprise_raw = response.raw_results[-1]

        self.assertIn("snapshot", enterprise_raw["data"])
        self.assertEqual(enterprise_raw["data"]["snapshot"]["domains"]["sales"]["total_revenue"], 725.0)
        self.assertEqual(enterprise_raw["data"]["snapshot"]["domains"]["finance"]["net_profit"], 2300.0)


class TestAIIntelligenceService(unittest.TestCase):

    def setUp(self):
        self.service = AIIntelligenceService()

    def test_generate_prompt_includes_query_and_metrics(self):
        snapshot = BusinessSnapshot(
            task_id="t1",
            query="Overall business summary",
            domains={"sales": {"total_revenue": 725.0}, "finance": {"net_profit": 2300.0}},
            health_status="Healthy",
            flags=["No major red flags detected."],
        )
        prompt = self.service.generate_prompt(snapshot)

        self.assertIsInstance(prompt, str)
        self.assertIn("Overall business summary", prompt)
        self.assertIn("Healthy", prompt)
        self.assertIn("total_revenue", prompt)
        self.assertIn("net_profit", prompt)
        self.assertIn("No major red flags detected.", prompt)

    def test_generate_prompt_reflects_gaps(self):
        snapshot = BusinessSnapshot(
            task_id="t1",
            query="Overall business summary",
            domains={"sales": {"total_revenue": 725.0}, "finance": {}},
            gaps=["Finance data unavailable."],
        )
        prompt = self.service.generate_prompt(snapshot)

        self.assertIn("Finance data unavailable.", prompt)
        self.assertIn("(no data available)", prompt)

    def test_generate_prompt_never_calls_an_adapter(self):
        # AIIntelligenceService has no dependency on LLMAdapter at all -- prompt
        # construction is fully independent of any provider.
        self.assertNotIn("LLMAdapter", dir(self.service))


class TestLLMAdapterPlaceholders(unittest.TestCase):

    def test_adapters_implement_the_interface(self):
        self.assertTrue(issubclass(ClaudeAdapter, LLMAdapter))
        self.assertTrue(issubclass(OpenAIAdapter, LLMAdapter))

    def test_claude_adapter_generate_is_not_wired_up(self):
        adapter = ClaudeAdapter()
        with self.assertRaises(NotImplementedError):
            adapter.generate("some prompt")

    def test_openai_adapter_generate_is_not_wired_up(self):
        adapter = OpenAIAdapter()
        with self.assertRaises(NotImplementedError):
            adapter.generate("some prompt")

    def test_llm_adapter_cannot_be_instantiated_directly(self):
        with self.assertRaises(TypeError):
            LLMAdapter()


if __name__ == "__main__":
    unittest.main()
