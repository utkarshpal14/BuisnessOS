class PlannerException(Exception):
    """Base exception for all Planner framework errors."""
    pass

class AgentNotFoundException(PlannerException):
    """Raised when requesting an unregistered agent."""
    def __init__(self, agent_name: str):
        super().__init__(f"Agent '{agent_name}' is not registered in the AgentRegistry.")
        self.agent_name = agent_name

class DuplicateAgentException(PlannerException):
    """Raised when registering an agent that is already registered."""
    def __init__(self, agent_name: str):
        super().__init__(f"Agent '{agent_name}' is already registered in the AgentRegistry.")
        self.agent_name = agent_name

class UnknownTaskTypeException(PlannerException):
    """Raised when a task_type cannot be routed."""
    def __init__(self, task_type: str):
        super().__init__(f"No routing defined for task_type '{task_type}'.")
        self.task_type = task_type

class InvalidTaskException(PlannerException):
    """Raised when task input fails validation."""
    def __init__(self, reason: str):
        super().__init__(f"Invalid task: {reason}")
        self.reason = reason
