"""
Shared keyword-matching primitives.

Every domain's *rules* (which phrases mean what) are genuinely domain-specific and
stay in that domain's own query_mapper.py. What was duplicated across
Sales/Finance/Enterprise was the *mechanism* -- "walk an ordered list of
(keywords, label) rules, first match wins, else a default" -- which now lives here
once. `matches_any` is the even simpler "does this text contain one of these
keywords" check, shared between app.planner.router's recommendation detection and
demo.py's task-type inference.
"""
from typing import List, Tuple


class KeywordMapper:
    """Resolves a raw query string to a label via ordered keyword matching."""

    def __init__(self, rules: List[Tuple[List[str], str]], default: str):
        self._rules = rules
        self._default = default

    def resolve(self, query: str) -> str:
        normalized = (query or "").lower()
        for keywords, label in self._rules:
            if any(keyword in normalized for keyword in keywords):
                return label
        return self._default


def matches_any(text: str, keywords: List[str]) -> bool:
    """True if `text` contains any of `keywords` (case-insensitive)."""
    normalized = (text or "").lower()
    return any(keyword in normalized for keyword in keywords)
