"""
Agents package for BusinessOS AI
"""
from app.agents.base import BaseAgent
from app.agents.mock_agents import FinanceAgent
from app.sales.agent import SalesAgent

__all__ = ["BaseAgent", "SalesAgent", "FinanceAgent"]
