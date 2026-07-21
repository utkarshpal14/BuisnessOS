from app.agents.base_agent import BaseAgent, Task, AgentResult, EvidenceItem

class FinanceAgent(BaseAgent):
    """
    Finance Agent: Responsible for revenue, cost analysis, and budget variance.
    """

    def handle(self, task: Task, role: str) -> AgentResult:
        return AgentResult(
            summary="Financial metrics analyzed.",
            evidence=[
                EvidenceItem(source="finance_erp_sim", data_point="Revenue and cost variance evaluated via MCP access layer.")
            ],
            confidence="high"
        )
