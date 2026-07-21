"""
FinanceQueryMapper: plain keyword matching from a natural-language query string onto a
FinanceAnalyticsService method name. No LLM involved -- first matching rule wins.

Rule order matters: more specific phrases ("profit margin", "monthly profit",
"revenue vs expenses") must be checked before the generic "profit"/"expenses" keywords
that would otherwise shadow them.
"""
from typing import List, Tuple

QUERY_RULES: List[Tuple[List[str], str]] = [
    (["summary", "overview"], "summary"),
    (["profit margin", "margin"], "profit_margin"),
    (["revenue vs expenses", "revenue and expenses", "revenue versus expenses"], "revenue_vs_expenses"),
    (["monthly profit", "monthly"], "monthly_profit"),
    (["total expenses", "expenses", "cost"], "total_expenses"),
    (["net profit", "profit"], "net_profit"),
]

DEFAULT_INTENT = "summary"


class FinanceQueryMapper:
    """Maps a raw query string to a FinanceAnalyticsService method name via keyword matching."""

    def resolve(self, query: str) -> str:
        normalized = (query or "").lower()
        for keywords, intent in QUERY_RULES:
            if any(keyword in normalized for keyword in keywords):
                return intent
        return DEFAULT_INTENT
