"""
FinanceAnalyticsService: all business KPI calculations live here. Mirrors
app/sales/analytics_service.py.

Operates only on the canonical DataFrame produced by FinanceDataLoader -- no CSV/file
awareness, no Planner/agent awareness. Every public method returns a plain,
JSON-serializable dict so callers can drop it straight into AgentResult.data.
"""
from typing import Any, Dict

import pandas as pd


class FinanceAnalyticsService:
    """Business calculations over a cleaned finance DataFrame."""

    def __init__(self, data: pd.DataFrame):
        self._df = data

    def total_revenue(self) -> Dict[str, Any]:
        return {"total_revenue": round(float(self._df["revenue"].sum()), 2)}

    def total_expenses(self) -> Dict[str, Any]:
        return {"total_expenses": round(float(self._df["expenses"].sum()), 2)}

    def net_profit(self) -> Dict[str, Any]:
        return {"net_profit": round(float(self._df["profit"].sum()), 2)}

    def profit_margin(self) -> Dict[str, Any]:
        total_revenue = self.total_revenue()["total_revenue"]
        net_profit = self.net_profit()["net_profit"]
        margin = round((net_profit / total_revenue) * 100, 2) if total_revenue else 0.0
        return {"profit_margin_pct": margin}

    def monthly_profit(self) -> Dict[str, Any]:
        grouped = (
            self._df.assign(month=self._df["date"].dt.strftime("%Y-%m"))
            .groupby("month")["profit"]
            .sum()
            .sort_index()
        )
        return {
            "monthly_profit": [
                {"month": month, "profit": round(float(profit), 2)} for month, profit in grouped.items()
            ]
        }

    def revenue_vs_expenses(self) -> Dict[str, Any]:
        grouped = (
            self._df.assign(month=self._df["date"].dt.strftime("%Y-%m"))
            .groupby("month")[["revenue", "expenses"]]
            .sum()
            .sort_index()
        )
        breakdown = [
            {
                "month": month,
                "revenue": round(float(row["revenue"]), 2),
                "expenses": round(float(row["expenses"]), 2),
            }
            for month, row in grouped.iterrows()
        ]
        return {"revenue_vs_expenses": breakdown}

    def summary(self) -> Dict[str, Any]:
        result: Dict[str, Any] = {}
        result.update(self.total_revenue())
        result.update(self.total_expenses())
        result.update(self.net_profit())
        result.update(self.profit_margin())

        monthly = self.monthly_profit()["monthly_profit"]
        if monthly:
            result["latest_month_profit"] = monthly[-1]

        return result
