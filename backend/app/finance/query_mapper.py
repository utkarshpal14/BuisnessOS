"""
FinanceQueryMapper: plain keyword matching from a natural-language query string onto a
FinanceAnalyticsService method name. No LLM involved -- first matching rule wins.

Rule order matters: more specific phrases ("profit margin", "monthly profit",
"revenue vs expenses") must be checked before the generic "profit"/"expenses" keywords
that would otherwise shadow them.

The matching mechanism is shared (app.common.keyword_mapper.KeywordMapper) with
Sales' and Enterprise's query mappers; only this rules table is finance-specific.
"""
from typing import List, Tuple

from app.common.keyword_mapper import KeywordMapper

QUERY_RULES: List[Tuple[List[str], str]] = [
    (["summary", "overview", "dashboard", "health"], "summary"),
    (["profit margin", "margin"], "profit_margin"),
    (["revenue vs expenses", "revenue and expenses", "revenue versus expenses"], "revenue_vs_expenses"),
    (["profit growth", "growth", "trend"], "profit_growth"),
    (["daily profit", "daily"], "daily_profit"),
    (["monthly profit", "monthly"], "monthly_profit"),
    (["profit by region", "region"], "profit_by_region"),
    (["top expense categories", "expense categories", "top categories", "category"], "top_expense_categories"),
    (["total expenses", "expenses", "cost"], "total_expenses"),
    (["net profit", "profit"], "net_profit"),
]

DEFAULT_INTENT = "unknown"


class FinanceQueryMapper:
    """Maps a raw query string to a FinanceAnalyticsService method name via keyword matching."""

    def __init__(self):
        self._mapper = KeywordMapper(QUERY_RULES, DEFAULT_INTENT)

    def resolve(self, query: str) -> str:
        return self._mapper.resolve(query)
