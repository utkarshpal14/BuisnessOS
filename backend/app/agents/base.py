from abc import ABC, abstractmethod
from app.planner.models import PlannerTask, AgentResult

class BaseAgent(ABC):
    """
    Abstract Base Class that every business agent must implement.
    Exposes a single execution method contract and an agent name.
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
