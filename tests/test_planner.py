import os
import sys
import unittest

# Ensure backend package directory is on Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.planner.models import PlannerTask, PlannerResponse, AgentResult
from app.planner.registry import AgentRegistry
from app.planner.router import SimpleTaskRouter
from app.planner.service import PlannerService
from app.planner.exceptions import (
    AgentNotFoundException,
    DuplicateAgentException,
    UnknownTaskTypeException,
    InvalidTaskException,
)
from app.agents.base import BaseAgent
from app.agents.mock_agents import SalesAgent, FinanceAgent

class FaultyAgent(BaseAgent):
    """Agent that raises an exception during execution for testing error handling."""
    @property
    def name(self) -> str:
        return "faulty"

    def execute(self, task: PlannerTask) -> AgentResult:
        raise RuntimeError("Simulated agent runtime crash")

class ErrorStatusAgent(BaseAgent):
    """Agent that returns status='error'."""
    @property
    def name(self) -> str:
        return "error_status"

    def execute(self, task: PlannerTask) -> AgentResult:
        return AgentResult(
            agent_name=self.name,
            status="error",
            summary="Failed due to external dependency",
            error_message="Connection timed out"
        )


class TestPlannerFramework(unittest.TestCase):

    def test_agent_registry_operations(self):
        registry = AgentRegistry()
        sales = SalesAgent()
        finance = FinanceAgent()

        # Register
        registry.register(sales)
        registry.register(finance)

        self.assertEqual(registry.list_agents(), ["sales", "finance"])
        self.assertEqual(registry.get("sales"), sales)

        # Duplicate registration
        with self.assertRaises(DuplicateAgentException):
            registry.register(SalesAgent())

        # Unregister
        registry.unregister("sales")
        self.assertNotIn("sales", registry.list_agents())

        # Unregister non-existent
        with self.assertRaises(AgentNotFoundException):
            registry.unregister("sales")

        # Get non-existent
        with self.assertRaises(AgentNotFoundException):
            registry.get("non_existent")

    def test_mock_agents_execution(self):
        task = PlannerTask(task_type="sales", query="Show Q3 pipeline")
        
        sales = SalesAgent()
        res_sales = sales.execute(task)
        self.assertEqual(res_sales.agent_name, "sales")
        self.assertEqual(res_sales.status, "success")
        self.assertEqual(res_sales.summary, "Mock sales response")

        finance = FinanceAgent()
        res_fin = finance.execute(task)
        self.assertEqual(res_fin.agent_name, "finance")
        self.assertEqual(res_fin.status, "success")
        self.assertEqual(res_fin.summary, "Mock finance response")

    def test_simple_task_router(self):
        router = SimpleTaskRouter()
        
        task_sales = PlannerTask(task_type="sales", query="Q3 sales")
        self.assertEqual(router.route(task_sales), ["sales"])

        task_finance = PlannerTask(task_type="finance", query="Q3 revenue")
        self.assertEqual(router.route(task_finance), ["finance"])

        task_business = PlannerTask(task_type="business", query="Overall performance")
        self.assertEqual(router.route(task_business), ["sales", "finance"])

        task_unknown = PlannerTask(task_type="marketing", query="Campaign CTR")
        with self.assertRaises(UnknownTaskTypeException):
            router.route(task_unknown)

    def test_planner_service_single_agent_success(self):
        registry = AgentRegistry()
        registry.register(SalesAgent())
        planner = PlannerService(registry=registry)

        task = PlannerTask(task_type="sales", query="Get sales report")
        response = planner.execute_task(task)

        self.assertEqual(response.task_id, task.task_id)
        self.assertEqual(response.status, "success")
        self.assertEqual(response.participating_agents, ["sales"])
        self.assertEqual(response.summary, "Mock sales response")
        self.assertEqual(len(response.raw_results), 1)
        self.assertGreaterEqual(response.execution_time_ms, 0)
        self.assertEqual(len(response.errors), 0)

    def test_planner_service_multi_agent_aggregation(self):
        registry = AgentRegistry()
        registry.register(SalesAgent())
        registry.register(FinanceAgent())
        planner = PlannerService(registry=registry)

        task = PlannerTask(task_type="business", query="Comprehensive company report")
        response = planner.execute_task(task)

        self.assertEqual(response.status, "success")
        self.assertEqual(response.participating_agents, ["sales", "finance"])
        self.assertIn("Mock sales response", response.summary)
        self.assertIn("Mock finance response", response.summary)
        self.assertEqual(len(response.raw_results), 2)
        self.assertEqual(len(response.errors), 0)

    def test_planner_service_unknown_task_type(self):
        registry = AgentRegistry()
        planner = PlannerService(registry=registry)

        task = PlannerTask(task_type="hr", query="Headcount count")
        response = planner.execute_task(task)

        self.assertEqual(response.status, "failed")
        self.assertEqual(response.participating_agents, [])
        self.assertEqual(len(response.errors), 1)
        self.assertIn("No routing defined for task_type 'hr'", response.errors[0])

    def test_planner_service_missing_registered_agent(self):
        registry = AgentRegistry()
        # "sales" is not registered in registry
        planner = PlannerService(registry=registry)

        task = PlannerTask(task_type="sales", query="Check deals")
        response = planner.execute_task(task)

        self.assertEqual(response.status, "failed")
        self.assertEqual(response.participating_agents, [])
        self.assertEqual(len(response.errors), 1)
        self.assertIn("Agent 'sales' is not registered", response.errors[0])

    def test_planner_service_partial_agent_failure(self):
        registry = AgentRegistry()
        registry.register(SalesAgent())
        registry.register(FaultyAgent())

        class PartialRouter(SimpleTaskRouter):
            def route(self, task: PlannerTask):
                return ["sales", "faulty"]

        planner = PlannerService(registry=registry, router=PartialRouter())
        task = PlannerTask(task_type="business", query="Check overall status")
        response = planner.execute_task(task)

        self.assertEqual(response.status, "partial_success")
        self.assertEqual(response.participating_agents, ["sales", "faulty"])
        self.assertEqual(len(response.errors), 1)
        self.assertIn("Unhandled exception in agent 'faulty'", response.errors[0])

    def test_planner_service_invalid_task_empty_query(self):
        registry = AgentRegistry()
        planner = PlannerService(registry=registry)

        task = PlannerTask(task_type="sales", query="")
        response = planner.execute_task(task)

        self.assertEqual(response.status, "failed")
        self.assertIn("Query content cannot be empty", response.errors[0])


if __name__ == "__main__":
    unittest.main()
