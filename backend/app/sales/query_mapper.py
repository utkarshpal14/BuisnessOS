"""
SalesQueryMapper: plain keyword matching from a natural-language query string onto a
SalesAnalyticsService method name. No LLM involved -- first matching rule wins.
"""
from typing import List, Tuple

# (keywords, SalesAnalyticsService method name) -- order matters, first match wins.
QUERY_RULES: List[Tuple[List[str], str]] = [
    (["summary", "overview"], "summary"),
    (["average order value", "aov"], "average_order_value"),
    (["total revenue", "revenue"], "total_revenue"),
    (["total orders", "order count", "number of orders", "orders"], "total_orders"),
    (["top product", "top products", "best product", "best selling"], "top_products"),
    (["top customer", "top customers", "best customer"], "top_customers"),
    (["region", "regional"], "sales_by_region"),
    (["monthly", "month over month", "per month"], "monthly_revenue"),
    (["daily", "per day", "day over day"], "daily_sales"),
    (["growth", "trend"], "revenue_growth"),
]

DEFAULT_INTENT = "summary"


class SalesQueryMapper:
    """Maps a raw query string to a SalesAnalyticsService method name via keyword matching."""

    def resolve(self, query: str) -> str:
        normalized = (query or "").lower()
        for keywords, intent in QUERY_RULES:
            if any(keyword in normalized for keyword in keywords):
                return intent
        return DEFAULT_INTENT
