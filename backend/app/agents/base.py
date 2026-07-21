from abc import ABC, abstractmethod
from app.planner.models import PlannerTask, AgentResult

class BaseAgent(ABC):
    """
    Abstract Base Class that every business agent must implement.
    Exposes a single execution method contract and an agent name.

    Contract every implementation must honor (see CLAUDE.md's "Non-negotiable
    design constraints" for the full rationale):
    - Never read a dataset/file/DB directly -- go through that domain's Data
      Access Layer gateway.
    - Stay stateless -- fetch fresh data on every execute() call.
    - `task.role` may be None (no auth exists yet); treat that as "unrestricted",
      never as an error.
    - Always return `evidence` (a list, possibly empty -- never omit the field)
      and a genuine `confidence`, not a constant default, on every AgentResult.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique identifier name for the agent."""
        pass

    @abstractmethod
    def execute(self, task: PlannerTask) -> AgentResult:
        """
        Execute agent logic for the given PlannerTask.
        Must return a standardized AgentResult.
        """
        pass
