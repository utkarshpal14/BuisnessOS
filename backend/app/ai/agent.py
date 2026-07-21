"""
AIAgent: the Planner-facing entry point for AI-generated business recommendations.

Implements app.agents.base.BaseAgent so the PlannerService/AgentRegistry can invoke it
exactly like any other agent. Never touches a dataset or dataframe -- it only reads the
BusinessSnapshot the Enterprise Agent already produced earlier in the same Planner run,
handed to it generically via task.metadata["upstream_results"]["enterprise"] (the same
hand-off mechanism the Enterprise Agent itself relies on for Sales/Finance).

Enterprise has no knowledge that an AI Agent exists -- this agent depends on it, never
the reverse. Prompt construction is delegated to AIIntelligenceService and completion
generation to whichever LLMAdapter is injected (a MockLLMAdapter by default), so this
agent has no LLM-provider-specific logic of its own.
"""
from typing import Any, Dict, Optional

from app.agents.base import BaseAgent
from app.ai.intelligence_service import AIIntelligenceService
from app.ai.llm_adapter import LLMAdapter, MockLLMAdapter
from app.enterprise.models import BusinessSnapshot
from app.planner.models import AgentResult, EvidenceItem, PlannerTask


class AIAgent(BaseAgent):
    """Generates an AI-reasoned business analysis from the Enterprise Agent's snapshot."""

    def __init__(
        self,
        intelligence_service: Optional[AIIntelligenceService] = None,
        llm_adapter: Optional[LLMAdapter] = None,
    ):
        self._intelligence_service = intelligence_service or AIIntelligenceService()
        self._llm_adapter = llm_adapter or MockLLMAdapter()

    @property
    def name(self) -> str:
        return "ai"

    def execute(self, task: PlannerTask) -> AgentResult:
        upstream: Dict[str, dict] = task.metadata.get("upstream_results", {})
        enterprise_result = upstream.get("enterprise")

        if not enterprise_result or enterprise_result.get("status") != "success":
            return self._error_result(
                "AI analysis requires a successful Enterprise Agent result, but none was available."
            )

        snapshot_dict = enterprise_result.get("data", {}).get("snapshot")
        if not snapshot_dict:
            return self._error_result("Enterprise result did not include a BusinessSnapshot.")

        snapshot = BusinessSnapshot(**snapshot_dict)
        prompt = self._intelligence_service.generate_prompt(snapshot)
        analysis = self._llm_adapter.generate(prompt)

        evidence = [
            EvidenceItem(source="enterprise_snapshot", data_point=f"health_status={snapshot.health_status or 'Unknown'}")
        ]
        evidence.extend(
            EvidenceItem(source=f"enterprise_snapshot:{domain}", data_point="Used as input to the AI analysis.")
            for domain in snapshot.domains
        )

        return AgentResult(
            agent_name=self.name,
            status="success",
            summary=analysis,
            evidence=evidence,
            # "medium", not "high" -- MockLLMAdapter (and, later, a real LLM's
            # free-text narrative) is a heuristic/generative summary of the
            # snapshot, not a directly-verified computation like Sales/Finance.
            confidence="medium",
            data={
                "agent": "ai",
                "status": "success",
                "summary": analysis,
                "prompt": prompt,
                "snapshot": snapshot_dict,
            },
        )

    def _error_result(self, message: str) -> AgentResult:
        return AgentResult(
            agent_name=self.name,
            status="error",
            summary="AI analysis unavailable.",
            confidence="low",
            error_message=message,
            data={"agent": "ai", "status": "error", "summary": "AI analysis unavailable."},
        )
