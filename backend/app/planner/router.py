from abc import ABC, abstractmethod
from typing import List
from app.common.keyword_mapper import matches_any
from app.planner.models import PlannerTask
from app.planner.exceptions import UnknownTaskTypeException

# Keyword signal that an "enterprise" query wants AI-generated recommendations, not
# just an aggregated view -- first match triggers routing through the AI Agent too.
RECOMMENDATION_KEYWORDS = [
    "recommend",
    "recommendation",
    "advice",
    "advisor",
    "action plan",
    "next steps",
    "what should we do",
]

class TaskRouter(ABC):
    """Abstract interface for routing tasks to candidate agent names."""

    @abstractmethod
    def route(self, task: PlannerTask) -> List[str]:
        pass

class SimpleTaskRouter(TaskRouter):
    """
    Rule-based task router mapping task types to agent names.
    Can be replaced by an AI Router in future features.
    """

    def route(self, task: PlannerTask) -> List[str]:
        task_type = task.task_type.lower()
        if task_type == "sales":
            return ["sales"]
        elif task_type == "finance":
            return ["finance"]
        elif task_type == "business":
            return ["sales", "finance"]
        elif task_type == "enterprise":
            if self._requests_recommendations(task.query):
                return ["sales", "finance", "enterprise", "ai"]
            return ["sales", "finance", "enterprise"]
        else:
            raise UnknownTaskTypeException(task.task_type)

    def _requests_recommendations(self, query: str) -> bool:
        return matches_any(query, RECOMMENDATION_KEYWORDS)
