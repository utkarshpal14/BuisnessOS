"""
Finance Intelligence package for BusinessOS AI.

Mirrors the Sales module's layering (see app/sales/):
- data_loader.py       : dataset access (CSV loading, schema normalization, cleaning)
- analytics_service.py : business KPI calculations over clean data
- query_mapper.py      : keyword-based query -> KPI intent mapping
- agent.py              : FinanceAgent, the Planner-facing BaseAgent implementation
- exceptions.py         : domain-specific error types
"""
from app.finance.agent import FinanceAgent

__all__ = ["FinanceAgent"]
