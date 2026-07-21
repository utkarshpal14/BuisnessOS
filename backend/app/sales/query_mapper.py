"""
SalesQueryMapper: plain keyword matching from a natural-language query string onto a
SalesAnalyticsService method name. No LLM involved -- first matching rule wins.

The matching mechanism is shared (app.common.keyword_mapper.KeywordMapper) with
Finance's and Enterprise's query mappers; only this rules table is sales-specific.
"""
from typing import List, Tuple

from app.common.keyword_mapper import KeywordMapper

# (keywords, SalesAnalyticsService method name) -- order matters, first match wins.
QUERY_RULES: List[Tuple[List[str], str]] = [
    (["summary", "overview", "dashboard", "health"], "summary"),
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

DEFAULT_INTENT = "unknown"


class SalesQueryMapper:
    """Maps a raw query string to a SalesAnalyticsService method name via keyword matching."""

    def __init__(self):
        self._mapper = KeywordMapper(QUERY_RULES, DEFAULT_INTENT)

    def resolve(self, query: str) -> str:
        return self._mapper.resolve(query)
