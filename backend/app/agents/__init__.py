"""
Shared agent contract for BusinessOS AI.

Holds only base.py: the BaseAgent interface every domain agent (SalesAgent in
app.sales, FinanceAgent in app.finance, EnterpriseAgent in app.enterprise, AIAgent
in app.ai) implements. Domain agents live in their own per-domain package, not here.
"""

__all__ = ["BaseAgent"]
