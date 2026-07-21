from app.agents.base_agent import BaseAgent, Task, AgentResult, EvidenceItem

class HRAgent(BaseAgent):
    """
    HR Agent: Responsible for headcount, attrition rate, and hiring capacity.
    """

    def handle(self, task: Task, role: str) -> AgentResult:
        return AgentResult(
            summary="HR metrics analyzed.",
            evidence=[
                EvidenceItem(source="hr_hrms_sim", data_point="Staffing and attrition data evaluated via MCP access layer.")
            ],
            confidence="high"
        )
