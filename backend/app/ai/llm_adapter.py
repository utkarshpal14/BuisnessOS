"""
LLMAdapter: common interface for pluggable LLM providers.

Every implementation here is a placeholder -- none of them call a real API. The point
of the interface is that AIIntelligenceService (and anything else that needs a
completion) can depend on `LLMAdapter` alone; swapping in a live Claude/OpenAI call
later is purely a change inside one adapter's generate() method.
"""
from abc import ABC, abstractmethod
from typing import List, Optional


class LLMAdapter(ABC):
    """Abstract interface every LLM provider adapter must implement."""

    @abstractmethod
    def generate(self, prompt: str) -> str:
        """Return a completion for the given prompt. Not implemented by placeholders."""
        pass


class ClaudeAdapter(LLMAdapter):
    """Placeholder adapter for Anthropic Claude. Not yet wired to a real API call."""

    def __init__(self, model: str = "claude-sonnet-5", api_key: Optional[str] = None):
        self.model = model
        self.api_key = api_key

    def generate(self, prompt: str) -> str:
        raise NotImplementedError(
            "ClaudeAdapter is a placeholder -- no live Anthropic API call is wired up yet."
        )


class OpenAIAdapter(LLMAdapter):
    """Placeholder adapter for OpenAI. Not yet wired to a real API call."""

    def __init__(self, model: str = "gpt-4", api_key: Optional[str] = None):
        self.model = model
        self.api_key = api_key

    def generate(self, prompt: str) -> str:
        raise NotImplementedError(
            "OpenAIAdapter is a placeholder -- no live OpenAI API call is wired up yet."
        )


class MockLLMAdapter(LLMAdapter):
    """
    Deterministic stand-in for a real LLM provider -- the only adapter that actually
    returns something from generate(). It reads the plain-text sections
    AIIntelligenceService already put in the prompt (Health Status / Flags / Data Gaps)
    and reflects them back inside a realistic four-section business analysis, without
    any network call. This lets the AI Agent pipeline be exercised end-to-end before a
    real provider is wired up.
    """

    def generate(self, prompt: str) -> str:
        health_status = self._extract_line_value(prompt, "Health Status:") or "Unknown"
        flags = self._extract_bulleted_section(prompt, "Flags:")
        gaps = self._extract_bulleted_section(prompt, "Data Gaps:")

        risks = list(flags) if flags else ["No significant risks identified in the current snapshot."]
        risks.extend(f"Incomplete data: {gap}" for gap in gaps)

        sections = [
            "Executive Summary:",
            f"  Overall business health is assessed as '{health_status}' based on the latest "
            "aggregated Sales and Finance data.",
            "",
            "Key Risks:",
            *(f"  - {risk}" for risk in risks),
            "",
            "Opportunities:",
            "  - Sustain performance in the top-performing regions and products already identified.",
            "  - Improve profit margin further by tightening cost discipline where expenses are rising.",
            "",
            "Recommended Actions:",
            "  - Review the flagged risk areas with the relevant domain owners this week.",
            "  - Re-run this analysis next reporting cycle to confirm the trend direction.",
            "  - Close the identified data gaps so future recommendations rest on complete data.",
        ]
        return "\n".join(sections)

    def _extract_line_value(self, text: str, prefix: str) -> Optional[str]:
        for line in text.splitlines():
            if line.startswith(prefix):
                return line[len(prefix):].strip()
        return None

    def _extract_bulleted_section(self, text: str, header: str) -> List[str]:
        lines = text.splitlines()
        items: List[str] = []
        collecting = False
        for line in lines:
            if line.strip() == header.strip():
                collecting = True
                continue
            if collecting:
                if line.startswith("  - "):
                    items.append(line[4:].strip())
                else:
                    break
        return items
