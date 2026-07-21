from typing import List
from app.agents.base_agent import BaseAgent, Task, AgentResult, EvidenceItem

class PlannerAgent(BaseAgent):
    """
    Planner Agent: Decomposes tasks and routes them to specialized agents.
    Handles both reactive (user) and proactive (sentinel) entry points uniformly.
    """

    def __init__(self, specialized_agents: List[BaseAgent] = None):
        self.specialized_agents = specialized_agents or []

    def handle(self, task: Task, role: str) -> AgentResult:
        # Skeleton implementation - will be expanded with LangGraph / Claude API calls
        return AgentResult(
            summary=f"Planner processed task '{task.content}' from source '{task.source}' for role '{role}'.",
            evidence=[
                EvidenceItem(source="planner_agent", data_point="Task decomposed and routed to sub-agents.")
            ],
            confidence="high"
        )
