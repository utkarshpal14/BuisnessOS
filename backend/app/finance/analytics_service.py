"""
FinanceAnalyticsService: all business KPI calculations live here. Mirrors
app/sales/analytics_service.py.

Operates only on the canonical DataFrame produced by FinanceDataLoader -- no CSV/file
awareness, no Planner/agent awareness. Every public method returns a plain,
JSON-serializable dict so callers can drop it straight into AgentResult.data.
"""
from typing import Any, Dict, List

import pandas as pd


class FinanceAnalyticsService:
    """Business calculations over a cleaned finance DataFrame."""

    def __init__(self, data: pd.DataFrame):
        self._df = data

    def _has(self, column: str) -> bool:
        return column in self._df.columns and not self._df[column].empty

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

    def daily_profit(self) -> Dict[str, Any]:
        grouped = (
            self._df.assign(day=self._df["date"].dt.strftime("%Y-%m-%d"))
            .groupby("day")["profit"]
            .sum()
            .sort_index()
        )
        daily = [{"date": day, "profit": round(float(profit), 2)} for day, profit in grouped.items()]
        return {"daily_profit": daily, "days_covered": len(daily)}

    def profit_by_region(self) -> Dict[str, Any]:
        if not self._has("region"):
            return {"available": False, "message": "Dataset has no region column."}
        grouped = self._df.groupby("region")["profit"].sum().sort_values(ascending=False)
        return {
            "available": True,
            "profit_by_region": [
                {"region": region, "profit": round(float(profit), 2)} for region, profit in grouped.items()
            ],
        }

    def top_expense_categories(self, n: int = 5) -> Dict[str, Any]:
        if not self._has("category"):
            return {"available": False, "message": "Dataset has no category column."}
        grouped = self._df.groupby("category")["expenses"].sum().sort_values(ascending=False).head(n)
        return {
            "available": True,
            "top_expense_categories": [
                {"category": category, "expenses": round(float(expenses), 2)} for category, expenses in grouped.items()
            ],
        }

    def profit_growth(self) -> Dict[str, Any]:
        months: List[Dict[str, Any]] = self.monthly_profit()["monthly_profit"]
        growth = []
        previous_profit = None
        for entry in months:
            profit = entry["profit"]
            if previous_profit in (None, 0):
                growth_pct = None
            else:
                growth_pct = round(((profit - previous_profit) / previous_profit) * 100, 2)
            growth.append({"month": entry["month"], "profit": profit, "growth_pct": growth_pct})
            previous_profit = profit
        return {"profit_growth": growth}

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

        growth_data = self.profit_growth()["profit_growth"]
        latest_with_growth = next(
            (m for m in reversed(growth_data) if m["growth_pct"] is not None), None
        )
        if latest_with_growth:
            result["latest_month_growth"] = latest_with_growth

        region_data = self.profit_by_region()
        if region_data.get("available") and region_data["profit_by_region"]:
            result["top_region"] = region_data["profit_by_region"][0]

        category_data = self.top_expense_categories(n=1)
        if category_data.get("available") and category_data["top_expense_categories"]:
            result["top_expense_category"] = category_data["top_expense_categories"][0]

        return result
