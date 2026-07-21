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
from app.planner.models import AgentResult, EvidenceItem, PlannerTask
from app.finance.analytics_service import FinanceAnalyticsService
from app.finance.data_access import FinanceDataAccess
from app.finance.exceptions import FinanceDataError
from app.finance.query_mapper import FinanceQueryMapper


class FinanceAgent(BaseAgent):
    """Real Finance Intelligence Agent: dataset-backed KPI analysis, no LLM calls."""

    def __init__(self, dataset_dir: Optional[str] = None):
        self._data_access = FinanceDataAccess(dataset_dir=dataset_dir)
        self._query_mapper = FinanceQueryMapper()

    @property
    def name(self) -> str:
        return "finance"

    def execute(self, task: PlannerTask) -> AgentResult:
        try:
            # Never touches FinanceDataLoader/pandas/the filesystem directly --
            # goes through the Data Access Layer gateway, which is where a role
            # check will be added once RBAC exists.
            clean_data = self._data_access.load(role=task.role)
        except FinanceDataError as e:
            return self._error_result(str(e))
        except Exception as e:  # never let a dataset problem crash the Planner
            return self._error_result(f"Unexpected error loading finance dataset: {e}")

        intent = self._query_mapper.resolve(task.query)
        if intent == "unknown":
            summary = (
                "I couldn't understand the requested finance KPI. "
                "Try queries like 'Net profit', 'Profit margin', or 'Revenue vs expenses'."
            )
            return AgentResult(
                agent_name=self.name,
                status="success",
                summary=summary,
                evidence=[EvidenceItem(source="finance_query_mapper", data_point="Query did not match a known finance KPI.")],
                confidence="low",
                data={
                    "agent": "finance",
                    "status": "success",
                    "summary": summary,
                    "kpi": intent,
                },
            )

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
            evidence=[EvidenceItem(source=f"finance_dataset:{intent}", data_point=summary)],
            confidence="high",
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
            confidence="low",
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
        if intent == "daily_profit":
            return f"Daily profit tracked across {data['days_covered']} day(s)."
        if intent == "profit_by_region":
            if not data.get("available"):
                return data.get("message", "Regional breakdown unavailable.")
            top = data["profit_by_region"][0]
            return f"Top region by profit is {top['region']} (${top['profit']:,.2f})."
        if intent == "top_expense_categories":
            if not data.get("available"):
                return data.get("message", "Top expense categories unavailable.")
            top = data["top_expense_categories"][0]
            return f"Top expense category is {top['category']} (${top['expenses']:,.2f})."
        if intent == "profit_growth":
            growth = [m for m in data["profit_growth"] if m["growth_pct"] is not None]
            if not growth:
                return "Not enough monthly history to compute profit growth yet."
            latest = growth[-1]
            direction = "up" if latest["growth_pct"] >= 0 else "down"
            return f"Profit is {direction} {abs(latest['growth_pct'])}% in {latest['month']} vs. the prior month."
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
            if "top_region" in data:
                parts.append(f"Top region: {data['top_region']['region']}.")
            if "top_expense_category" in data:
                parts.append(f"Top expense category: {data['top_expense_category']['category']}.")
            return " ".join(parts)
        return "Finance KPI computed."
