"""
Planner Framework Package
"""
from importlib import import_module

__all__ = [
    "PlannerTask",
    "PlannerResponse",
    "AgentResult",
    "PlannerException",
    "AgentNotFoundException",
    "DuplicateAgentException",
    "UnknownTaskTypeException",
    "InvalidTaskException",
    "AgentRegistry",
    "TaskRouter",
    "SimpleTaskRouter",
    "PlannerService",
]


def __getattr__(name: str):
    module_map = {
        "PlannerTask": "app.planner.models",
        "PlannerResponse": "app.planner.models",
        "AgentResult": "app.planner.models",
        "PlannerException": "app.planner.exceptions",
        "AgentNotFoundException": "app.planner.exceptions",
        "DuplicateAgentException": "app.planner.exceptions",
        "UnknownTaskTypeException": "app.planner.exceptions",
        "InvalidTaskException": "app.planner.exceptions",
        "AgentRegistry": "app.planner.registry",
        "TaskRouter": "app.planner.router",
        "SimpleTaskRouter": "app.planner.router",
        "PlannerService": "app.planner.service",
    }
    if name in module_map:
        module = import_module(module_map[name])
        return getattr(module, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
