"""
EnterpriseAnalyticsService: combines the plain KPI dicts already computed by any
number of domain agents (Sales, Finance, and future ones such as HR/Marketing) into
enterprise-level views.

Operates only on whatever domain data dicts it's handed -- no dataset, dataframe, or
file awareness. Adding a new domain agent requires zero changes to the aggregation
logic below: any domain present in `domains` is folded into combined_summary()
automatically. DOMAIN_FIELD_LABELS is a purely cosmetic, optional rename table (so
existing output keys like "sales_revenue"/"net_profit" read naturally) -- a domain
absent from it still gets aggregated correctly, just under namespaced key names.
"""
from typing import Any, Dict, List, Optional

# Domain -> {raw KPI field name: display key in the combined view}. Registering a
# new domain here is optional prettification, never required for correctness --
# see the fallback branch in combined_summary().
DOMAIN_FIELD_LABELS: Dict[str, Dict[str, str]] = {
    "sales": {
        "total_revenue": "sales_revenue",
        "total_orders": "total_orders",
        "average_order_value": "average_order_value",
        "top_region": "top_region",
        "top_product": "top_product",
        "latest_month_growth": "latest_month_growth",
    },
    "finance": {
        "total_revenue": "finance_revenue",
        "total_expenses": "total_expenses",
        "net_profit": "net_profit",
        "profit_margin_pct": "profit_margin_pct",
    },
}


class EnterpriseAnalyticsService:
    """Aggregation over an arbitrary set of already-computed domain KPI dicts."""

    def __init__(self, domains: Optional[Dict[str, Dict[str, Any]]] = None):
        self._domains = domains or {}

    def combined_summary(self) -> Dict[str, Any]:
        result: Dict[str, Any] = {}
        for domain, data in self._domains.items():
            if not data:
                continue
            field_labels = DOMAIN_FIELD_LABELS.get(domain)
            if field_labels:
                for field, display_key in field_labels.items():
                    if field in data:
                        result[display_key] = data[field]
            else:
                # Unregistered domain (e.g. a brand-new agent nobody has added to
                # DOMAIN_FIELD_LABELS yet): still surface its fields, namespaced,
                # rather than silently dropping them.
                result.update({f"{domain}_{field}": value for field, value in data.items()})
        return result

    def health_assessment(self) -> Dict[str, Any]:
        summary = self.combined_summary()
        margin = summary.get("profit_margin_pct")
        growth_entry = summary.get("latest_month_growth")
        growth_pct = growth_entry.get("growth_pct") if growth_entry else None

        if margin is None:
            status = "Unknown"
        elif margin >= 15:
            status = "Healthy"
        elif margin >= 5:
            status = "Stable"
        else:
            status = "At Risk"

        flags: List[str] = []
        if margin is not None and margin < 5:
            flags.append("Profit margin is thin.")
        if growth_pct is not None and growth_pct < 0:
            flags.append("Revenue declined month-over-month.")
        if not flags:
            flags.append("No major red flags detected.")

        return {**summary, "health_status": status, "flags": flags}
