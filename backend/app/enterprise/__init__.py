"""
Enterprise Intelligence package for BusinessOS AI.

Layers:
- analytics_service.py : aggregates already-computed Sales/Finance KPI dicts
- query_mapper.py       : keyword-based query -> enterprise view mapping
- agent.py              : EnterpriseAgent, the Planner-facing BaseAgent implementation

Never reads a dataset or dataframe -- it only combines the structured AgentResult
outputs that Sales and Finance already produced earlier in the same Planner run.
"""

__all__ = ["EnterpriseAgent"]
