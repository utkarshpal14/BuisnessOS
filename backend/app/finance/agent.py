"""
FinanceAgent: the Planner-facing entry point for finance intelligence. Mirrors
app/sales/agent.py.

Implements app.agents.base.BaseAgent so the PlannerService/AgentRegistry can invoke it
exactly like any other agent -- the Planner has no idea a CSV or pandas is involved.

Stateless by design: every execute() call re-loads the dataset via FinanceDataLoader
rather than caching a DataFrame on the instance, per the project's no-agent-caching rule.
"""
from typing import Any, Dict, Optional

from app.agents.base import BaseAgent
from app.planner.models import AgentResult, PlannerTask
from app.finance.analytics_service import FinanceAnalyticsService
from app.finance.data_loader import FinanceDataLoader
from app.finance.exceptions import FinanceDataError
from app.finance.query_mapper import FinanceQueryMapper


class FinanceAgent(BaseAgent):
    """Real Finance Intelligence Agent: dataset-backed KPI analysis, no LLM calls."""

    def __init__(self, dataset_dir: Optional[str] = None):
        self._data_loader = FinanceDataLoader(dataset_dir=dataset_dir)
        self._query_mapper = FinanceQueryMapper()

    @property
    def name(self) -> str:
        return "finance"

    def execute(self, task: PlannerTask) -> AgentResult:
        try:
            clean_data = self._data_loader.load()
        except FinanceDataError as e:
            return self._error_result(str(e))
        except Exception as e:  # never let a dataset problem crash the Planner
            return self._error_result(f"Unexpected error loading finance dataset: {e}")

        intent = self._query_mapper.resolve(task.query)
        service = FinanceAnalyticsService(clean_data)

        try:
            kpi_data = getattr(service, intent)()
        except Exception as e:
            return self._error_result(f"Failed computing '{intent}' KPI: {e}")

        summary = self._build_summary(intent, kpi_data)
        return AgentResult(
            agent_name=self.name,
            status="success",
            summary=summary,
            data={
                "agent": "finance",
                "status": "success",
                "summary": summary,
                "kpi": intent,
                **kpi_data,
            },
        )

    def _error_result(self, message: str) -> AgentResult:
        return AgentResult(
            agent_name=self.name,
            status="error",
            summary="Finance analysis unavailable.",
            error_message=message,
            data={"agent": "finance", "status": "error", "summary": "Finance analysis unavailable."},
        )

    def _build_summary(self, intent: str, data: Dict[str, Any]) -> str:
        if intent == "net_profit":
            return f"Net profit is ${data['net_profit']:,.2f}."
        if intent == "total_expenses":
            return f"Total expenses are ${data['total_expenses']:,.2f}."
        if intent == "profit_margin":
            return f"Profit margin is {data['profit_margin_pct']}%."
        if intent == "monthly_profit":
            months = data["monthly_profit"]
            if not months:
                return "No monthly profit data available."
            latest = months[-1]
            return f"Monthly profit tracked across {len(months)} month(s); latest ({latest['month']}) is ${latest['profit']:,.2f}."
        if intent == "revenue_vs_expenses":
            rows = data["revenue_vs_expenses"]
            if not rows:
                return "No revenue vs. expenses data available."
            latest = rows[-1]
            return (
                f"Latest month ({latest['month']}): revenue ${latest['revenue']:,.2f} "
                f"vs. expenses ${latest['expenses']:,.2f}."
            )
        if intent == "summary":
            parts = [
                f"Net profit is ${data['net_profit']:,.2f}",
                f"on revenue of ${data['total_revenue']:,.2f}",
                f"and expenses of ${data['total_expenses']:,.2f}",
                f"({data['profit_margin_pct']}% margin).",
            ]
            if "latest_month_profit" in data:
                latest = data["latest_month_profit"]
                parts.append(f"Latest month ({latest['month']}) profit: ${latest['profit']:,.2f}.")
            return " ".join(parts)
        return "Finance KPI computed."
