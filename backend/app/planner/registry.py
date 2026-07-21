from typing import Dict, List
from app.agents.base import BaseAgent
from app.planner.exceptions import AgentNotFoundException, DuplicateAgentException

class AgentRegistry:
    """
    Registry for managing business agent instances.
    Enforces uniqueness and provides agent lookup capabilities.
    """

    def __init__(self):
        self._agents: Dict[str, BaseAgent] = {}

    def register(self, agent: BaseAgent) -> None:
        """Register a new agent instance."""
        if agent.name in self._agents:
            raise DuplicateAgentException(agent.name)
        self._agents[agent.name] = agent

    def unregister(self, agent_name: str) -> None:
        """Unregister an existing agent by name."""
        if agent_name not in self._agents:
            raise AgentNotFoundException(agent_name)
        del self._agents[agent_name]

    def get(self, agent_name: str) -> BaseAgent:
        """Retrieve a registered agent by name."""
        if agent_name not in self._agents:
            raise AgentNotFoundException(agent_name)
        return self._agents[agent_name]

    def list_agents(self) -> List[str]:
        """List all registered agent names."""
        return list(self._agents.keys())
