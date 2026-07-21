from abc import ABC, abstractmethod
from typing import List
from app.planner.models import PlannerTask
from app.planner.exceptions import UnknownTaskTypeException

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
        else:
            raise UnknownTaskTypeException(task.task_type)
