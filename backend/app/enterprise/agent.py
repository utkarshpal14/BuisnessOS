"""
EnterpriseAgent: the Planner-facing entry point for enterprise-level intelligence.

Implements app.agents.base.BaseAgent so the PlannerService/AgentRegistry can invoke it
exactly like any other agent. Unlike SalesAgent/FinanceAgent, this agent never touches a
dataset directly -- it only reads whatever AgentResults already ran earlier in the same
Planner run, handed to it generically via task.metadata["upstream_results"] (populated
by PlannerService, not by this agent).

Aggregation here is domain-agnostic: it iterates every entry actually present in
upstream_results rather than hardcoding "sales"/"finance" -- adding a new domain agent
(HR, Marketing, ...) to the Planner's route list means this agent picks it up
automatically, with no code change here. No domain agent has any knowledge that an
Enterprise Agent exists -- this agent depends on them, never the reverse.
"""
from typing import Any, Dict, List

from app.agents.base import BaseAgent
from app.enterprise.analytics_service import EnterpriseAnalyticsService
from app.enterprise.models import BusinessSnapshot
from app.enterprise.query_mapper import EnterpriseQueryMapper
from app.planner.models import AgentResult, EvidenceItem, PlannerTask


class EnterpriseAgent(BaseAgent):
    """Aggregates any number of upstream domain AgentResults into an enterprise-level view."""

    def __init__(self):
        self._query_mapper = EnterpriseQueryMapper()

    @property
    def name(self) -> str:
        return "enterprise"

    def execute(self, task: PlannerTask) -> AgentResult:
        upstream: Dict[str, dict] = task.metadata.get("upstream_results", {})

        gaps: List[str] = []
        domains: Dict[str, Dict[str, Any]] = {}
        for domain, result in upstream.items():
            if result and result.get("status") == "success":
                domains[domain] = result.get("data", {})
            else:
                gaps.append(f"{domain.capitalize()} data unavailable.")

        if not any(domains.values()):
            return self._error_result(
                "Enterprise report requires at least one successful upstream agent result, but none were available."
            )

        intent = self._query_mapper.resolve(task.query)
        service = EnterpriseAnalyticsService(domains=domains)

        # Computed once regardless of which text view was requested, so the structured
        # BusinessSnapshot always reflects the full aggregated picture -- independent of
        # which human-readable phrasing (summary/dashboard/health) the query mapped to.
        health = service.health_assessment()

        if intent == "health_report":
            view_data = health
            summary = self._build_health_summary(health, gaps)
        elif intent == "executive_dashboard":
            view_data = service.combined_summary()
            summary = self._build_dashboard_summary(view_data, gaps)
        else:
            view_data = service.combined_summary()
            summary = self._build_overview_summary(view_data, gaps)

        snapshot = BusinessSnapshot(
            task_id=task.task_id,
            query=task.query,
            domains=domains,
            health_status=health.get("health_status"),
            flags=health.get("flags", []),
            gaps=gaps,
        )

        evidence = [
            EvidenceItem(source=f"{domain}_agent", data_point=f"Contributed fields: {sorted(domain_data.keys())}")
            for domain, domain_data in domains.items()
            if domain_data
        ]
        confidence = "high" if not gaps else "medium"

        return AgentResult(
            agent_name=self.name,
            status="success",
            summary=summary,
            evidence=evidence,
            confidence=confidence,
            data={
                "agent": "enterprise",
                "status": "success",
                "summary": summary,
                "kpi": intent,
                # AgentResult.data is the only extensible field on the shared Planner
                # schema, so the BusinessSnapshot travels here rather than as a new
                # top-level field -- keeps app.planner.models untouched.
                "snapshot": snapshot.model_dump(),
                **view_data,
            },
        )

    def _error_result(self, message: str) -> AgentResult:
        return AgentResult(
            agent_name=self.name,
            status="error",
            summary="Enterprise report unavailable.",
            confidence="low",
            error_message=message,
            data={"agent": "enterprise", "status": "error", "summary": "Enterprise report unavailable."},
        )

    def _build_overview_summary(self, data: Dict[str, Any], gaps: List[str]) -> str:
        parts = []
        if "sales_revenue" in data:
            parts.append(f"sales revenue is ${data['sales_revenue']:,.2f}")
        if "net_profit" in data:
            parts.append(f"net profit is ${data['net_profit']:,.2f}")
        if "profit_margin_pct" in data:
            parts.append(f"profit margin is {data['profit_margin_pct']}%")
        if "top_region" in data:
            parts.append(f"top region is {data['top_region']['region']}")

        summary = ("Overall business summary: " + ", ".join(parts) + ".") if parts else "No enterprise data available."
        if gaps:
            summary += " (" + " ".join(gaps) + ")"
        return summary

    def _build_dashboard_summary(self, data: Dict[str, Any], gaps: List[str]) -> str:
        lines = ["Executive Dashboard:"]
        if "sales_revenue" in data:
            lines.append(f"  Revenue: ${data['sales_revenue']:,.2f}")
        if "net_profit" in data:
            lines.append(f"  Net Profit: ${data['net_profit']:,.2f}")
        if "profit_margin_pct" in data:
            lines.append(f"  Margin: {data['profit_margin_pct']}%")
        if "total_orders" in data:
            lines.append(f"  Orders: {data['total_orders']:,}")
        if "top_product" in data:
            lines.append(f"  Top Product: {data['top_product']['product']}")
        if gaps:
            lines.append("  Gaps: " + " ".join(gaps))
        return "\n".join(lines)

    def _build_health_summary(self, data: Dict[str, Any], gaps: List[str]) -> str:
        status = data.get("health_status", "Unknown")
        flags = data.get("flags", [])
        summary = f"Business health status: {status}."
        if flags:
            summary += " " + " ".join(flags)
        if gaps:
            summary += " (" + " ".join(gaps) + ")"
        return summary
