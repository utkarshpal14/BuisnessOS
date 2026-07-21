"""
SalesAnalyticsService: all business KPI calculations live here.

Operates only on the canonical DataFrame produced by SalesDataLoader -- no CSV/file
awareness, no Planner/agent awareness. Every public method returns a plain,
JSON-serializable dict so callers can drop it straight into AgentResult.data.
"""
from typing import Any, Dict, List

import pandas as pd


class SalesAnalyticsService:
    """Business calculations over a cleaned sales DataFrame."""

    def __init__(self, data: pd.DataFrame):
        self._df = data

    def _has(self, column: str) -> bool:
        return column in self._df.columns and not self._df[column].empty

    def total_revenue(self) -> Dict[str, Any]:
        return {"total_revenue": round(float(self._df["revenue"].sum()), 2)}

    def total_orders(self) -> Dict[str, Any]:
        if self._has("order_id"):
            count = int(self._df["order_id"].nunique())
        else:
            count = int(len(self._df))
        return {"total_orders": count}

    def average_order_value(self) -> Dict[str, Any]:
        total_orders = self.total_orders()["total_orders"]
        total_revenue = self.total_revenue()["total_revenue"]
        avg = round(total_revenue / total_orders, 2) if total_orders else 0.0
        return {"average_order_value": avg}

    def monthly_revenue(self) -> Dict[str, Any]:
        grouped = (
            self._df.assign(month=self._df["order_date"].dt.strftime("%Y-%m"))
            .groupby("month")["revenue"]
            .sum()
            .sort_index()
        )
        return {
            "monthly_revenue": [
                {"month": month, "revenue": round(float(rev), 2)} for month, rev in grouped.items()
            ]
        }

    def daily_sales(self) -> Dict[str, Any]:
        grouped = (
            self._df.assign(day=self._df["order_date"].dt.strftime("%Y-%m-%d"))
            .groupby("day")["revenue"]
            .sum()
            .sort_index()
        )
        daily = [{"date": day, "revenue": round(float(rev), 2)} for day, rev in grouped.items()]
        return {"daily_sales": daily, "days_covered": len(daily)}

    def sales_by_region(self) -> Dict[str, Any]:
        if not self._has("region"):
            return {"available": False, "message": "Dataset has no region column."}
        grouped = self._df.groupby("region")["revenue"].sum().sort_values(ascending=False)
        return {
            "available": True,
            "sales_by_region": [
                {"region": region, "revenue": round(float(rev), 2)} for region, rev in grouped.items()
            ],
        }

    def top_products(self, n: int = 5) -> Dict[str, Any]:
        if not self._has("product"):
            return {"available": False, "message": "Dataset has no product column."}
        grouped = self._df.groupby("product")["revenue"].sum().sort_values(ascending=False).head(n)
        return {
            "available": True,
            "top_products": [
                {"product": product, "revenue": round(float(rev), 2)} for product, rev in grouped.items()
            ],
        }

    def top_customers(self, n: int = 5) -> Dict[str, Any]:
        if not self._has("customer"):
            return {"available": False, "message": "Dataset has no customer column."}
        grouped = self._df.groupby("customer")["revenue"].sum().sort_values(ascending=False).head(n)
        return {
            "available": True,
            "top_customers": [
                {"customer": customer, "revenue": round(float(rev), 2)} for customer, rev in grouped.items()
            ],
        }

    def revenue_growth(self) -> Dict[str, Any]:
        months: List[Dict[str, Any]] = self.monthly_revenue()["monthly_revenue"]
        growth = []
        previous_revenue = None
        for entry in months:
            revenue = entry["revenue"]
            if previous_revenue in (None, 0):
                growth_pct = None
            else:
                growth_pct = round(((revenue - previous_revenue) / previous_revenue) * 100, 2)
            growth.append({"month": entry["month"], "revenue": revenue, "growth_pct": growth_pct})
            previous_revenue = revenue
        return {"revenue_growth": growth}

    def summary(self) -> Dict[str, Any]:
        result: Dict[str, Any] = {}
        result.update(self.total_revenue())
        result.update(self.total_orders())
        result.update(self.average_order_value())

        region_data = self.sales_by_region()
        if region_data.get("available") and region_data["sales_by_region"]:
            result["top_region"] = region_data["sales_by_region"][0]

        product_data = self.top_products(n=1)
        if product_data.get("available") and product_data["top_products"]:
            result["top_product"] = product_data["top_products"][0]

        growth_data = self.revenue_growth()["revenue_growth"]
        latest_with_growth = next(
            (m for m in reversed(growth_data) if m["growth_pct"] is not None), None
        )
        if latest_with_growth:
            result["latest_month_growth"] = latest_with_growth

        return result
