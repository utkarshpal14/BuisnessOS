from app.agents.base_agent import BaseAgent, Task, AgentResult, EvidenceItem

class SalesAgent(BaseAgent):
    """
    Sales Agent: Responsible for sales pipeline, deal metrics, and capacity analysis.
    """

    def handle(self, task: Task, role: str) -> AgentResult:
        return AgentResult(
            summary="Sales metrics analyzed.",
            evidence=[
                EvidenceItem(source="sales_crm_sim", data_point="Pipeline value evaluated via MCP access layer.")
            ],
            confidence="high"
        )
