"""
AIIntelligenceService: turns a BusinessSnapshot into an LLM-ready prompt.

Pure prompt construction -- it never calls an LLMAdapter or any external API itself.
That separation is deliberate: this service can be fully unit tested without network
access, and wiring a real model later is purely an LLMAdapter change.
"""
from app.enterprise.models import BusinessSnapshot


class AIIntelligenceService:
    """Builds a natural-language prompt from a BusinessSnapshot. No API calls."""

    def generate_prompt(self, snapshot: BusinessSnapshot) -> str:
        lines = [
            "You are a business intelligence analyst for BusinessOS AI.",
            "Analyze the following aggregated business snapshot and provide insights.",
            "",
            f"Query: {snapshot.query}",
            f"Health Status: {snapshot.health_status or 'Unknown'}",
        ]

        if snapshot.flags:
            lines.append("Flags:")
            lines.extend(f"  - {flag}" for flag in snapshot.flags)

        if snapshot.gaps:
            lines.append("Data Gaps:")
            lines.extend(f"  - {gap}" for gap in snapshot.gaps)

        lines.append("")
        lines.append("Domain Metrics:")
        for domain, metrics in snapshot.domains.items():
            lines.append(f"  {domain.capitalize()}:")
            if metrics:
                for key, value in metrics.items():
                    lines.append(f"    {key}: {value}")
            else:
                lines.append("    (no data available)")

        lines.append("")
        lines.append(
            "Provide a concise executive-level narrative summarizing performance, "
            "risks, and recommended actions."
        )

        return "\n".join(lines)
