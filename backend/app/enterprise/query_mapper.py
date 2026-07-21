"""
EnterpriseQueryMapper: plain keyword matching from a natural-language query string onto
an enterprise-level view name. No LLM involved -- first matching rule wins.

The matching mechanism is shared (app.common.keyword_mapper.KeywordMapper) with
Sales' and Finance's query mappers; only this rules table is enterprise-specific.
"""
from typing import List, Tuple

from app.common.keyword_mapper import KeywordMapper

# (keywords, view name) -- order matters, first match wins.
QUERY_RULES: List[Tuple[List[str], str]] = [
    (["executive dashboard", "dashboard"], "executive_dashboard"),
    (["health report", "business health", "health"], "health_report"),
    (["business summary", "overall business", "summary", "overview"], "summary"),
]

DEFAULT_INTENT = "summary"


class EnterpriseQueryMapper:
    """Maps a raw query string to an enterprise view name via keyword matching."""

    def __init__(self):
        self._mapper = KeywordMapper(QUERY_RULES, DEFAULT_INTENT)

    def resolve(self, query: str) -> str:
        return self._mapper.resolve(query)
