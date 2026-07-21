from app.agents.base import BaseAgent
from app.planner.models import PlannerTask, AgentResult

class FinanceAgent(BaseAgent):
    """Mock Finance Agent for orchestration verification."""

    @property
    def name(self) -> str:
        return "finance"

    def execute(self, task: PlannerTask) -> AgentResult:
        return AgentResult(
            agent_name=self.name,
            status="success",
            summary="Mock finance response",
            data={
                "agent": "finance",
                "status": "success",
                "summary": "Mock finance response"
            }
        )
