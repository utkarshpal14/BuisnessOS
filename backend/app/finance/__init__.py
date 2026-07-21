"""
Finance Intelligence package for BusinessOS AI.

Mirrors the Sales module's layering (see app/sales/):
- data_loader.py       : low-level CSV loading, schema normalization, cleaning
- data_access.py       : Data Access Layer gateway -- the only thing FinanceAgent
                          depends on for data; where RBAC will plug in later
- analytics_service.py : business KPI calculations over clean data
- query_mapper.py      : keyword-based query -> KPI intent mapping
- agent.py              : FinanceAgent, the Planner-facing BaseAgent implementation
- exceptions.py         : domain-specific error types
"""

__all__ = ["FinanceAgent"]
