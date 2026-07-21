"""
SalesAgent: the Planner-facing entry point for sales intelligence.

Implements app.agents.base.BaseAgent so the PlannerService/AgentRegistry can invoke it
exactly like any other agent -- the Planner has no idea a CSV or pandas is involved.

Stateless by design: every execute() call re-loads the dataset via SalesDataLoader
rather than caching a DataFrame on the instance, per the project's no-agent-caching rule.
"""
from typing import Any, Dict, Optional

from app.agents.base import BaseAgent
from app.planner.models import AgentResult, PlannerTask
from app.sales.analytics_service import SalesAnalyticsService
from app.sales.data_loader import SalesDataLoader
from app.sales.exceptions import SalesDataError
from app.sales.query_mapper import SalesQueryMapper


class SalesAgent(BaseAgent):
    """Real Sales Intelligence Agent: dataset-backed KPI analysis, no LLM calls."""

    def __init__(self, dataset_dir: Optional[str] = None):
        self._data_loader = SalesDataLoader(dataset_dir=dataset_dir)
        self._query_mapper = SalesQueryMapper()

    @property
    def name(self) -> str:
        return "sales"

    def execute(self, task: PlannerTask) -> AgentResult:
        try:
            clean_data = self._data_loader.load()
        except SalesDataError as e:
            return self._error_result(str(e))
        except Exception as e:  # never let a dataset problem crash the Planner
            return self._error_result(f"Unexpected error loading sales dataset: {e}")

        intent = self._query_mapper.resolve(task.query)
        if intent == "unknown":
            summary = (
                "I couldn't understand the requested sales KPI. "
                "Try queries like 'Total revenue', 'Sales by region', or 'Top products'."
            )
            return AgentResult(
                agent_name=self.name,
                status="success",
                summary=summary,
                data={
                    "agent": "sales",
                    "status": "success",
                    "summary": summary,
                    "kpi": intent,
                },
            )

        service = SalesAnalyticsService(clean_data)

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
                "agent": "sales",
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
            summary="Sales analysis unavailable.",
            error_message=message,
            data={"agent": "sales", "status": "error", "summary": "Sales analysis unavailable."},
        )

    def _build_summary(self, intent: str, data: Dict[str, Any]) -> str:
        if intent == "total_revenue":
            return f"Total revenue is ${data['total_revenue']:,.2f}."
        if intent == "total_orders":
            return f"Total orders: {data['total_orders']:,}."
        if intent == "average_order_value":
            return f"Average order value is ${data['average_order_value']:,.2f}."
        if intent == "monthly_revenue":
            months = data["monthly_revenue"]
            if not months:
                return "No monthly revenue data available."
            latest = months[-1]
            return f"Monthly revenue tracked across {len(months)} month(s); latest ({latest['month']}) is ${latest['revenue']:,.2f}."
        if intent == "daily_sales":
            return f"Daily sales tracked across {data['days_covered']} day(s)."
        if intent == "sales_by_region":
            if not data.get("available"):
                return data.get("message", "Regional breakdown unavailable.")
            top = data["sales_by_region"][0]
            return f"Top region by revenue is {top['region']} (${top['revenue']:,.2f})."
        if intent == "top_products":
            if not data.get("available"):
                return data.get("message", "Top products unavailable.")
            top = data["top_products"][0]
            return f"Top product by revenue is {top['product']} (${top['revenue']:,.2f})."
        if intent == "top_customers":
            if not data.get("available"):
                return data.get("message", "Top customers unavailable.")
            top = data["top_customers"][0]
            return f"Top customer by revenue is {top['customer']} (${top['revenue']:,.2f})."
        if intent == "revenue_growth":
            growth = [m for m in data["revenue_growth"] if m["growth_pct"] is not None]
            if not growth:
                return "Not enough monthly history to compute revenue growth yet."
            latest = growth[-1]
            direction = "up" if latest["growth_pct"] >= 0 else "down"
            return f"Revenue is {direction} {abs(latest['growth_pct'])}% in {latest['month']} vs. the prior month."
        if intent == "summary":
            parts = [
                f"Total revenue is ${data['total_revenue']:,.2f}",
                f"across {data['total_orders']:,} orders",
                f"(avg order value ${data['average_order_value']:,.2f}).",
            ]
            if "top_region" in data:
                parts.append(f"Top region: {data['top_region']['region']}.")
            if "top_product" in data:
                parts.append(f"Top product: {data['top_product']['product']}.")
            return " ".join(parts)
        return "Sales KPI computed."
