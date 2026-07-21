# BusinessOS AI — Project Context & Decision Log

*Purpose: preserve the reasoning behind architectural decisions, not just the decisions themselves, so the project doesn't have to be "re-explained" to a new session or teammate.*

| # | Decision | Why |
|---|---|---|
| 1 | Product is a cross-department platform, not a single-department tool | Original problem statement: departments run on disconnected software; the goal is unified visibility, not another single-purpose tool. |
| 2 | One Planner Agent with two entry points, instead of two separate reactive/proactive architectures | Simpler to build and reason about; mirrors how real systems (e.g. Gmail: user-composed vs. received mail) share one core engine regardless of trigger source. Rejected the two-diagram version because it implied two systems, which isn't true — the middle of the pipeline is identical either way. |
| 3 | Renamed "Business Sentinel Agent" → "Enterprise Intelligence Engine" | The original name made it sound like just another specialized agent. Renaming it signals it's an architectural layer with a distinct responsibility (continuous monitoring), which is also the project's USP. |
| 4 | Role-based access enforced at the MCP/data-access layer, not the frontend | A professor flagged basic RBAC as "not a differentiator" when described as a UI feature. Moving enforcement to the data-access layer makes it a real security architecture decision, not a cosmetic one, and it's also just correct practice regardless of grading. |
| 5 | Agents hold no persistent business data themselves | Keeps agents stateless and simple; all real data always comes fresh from MCP, avoiding sync/staleness issues between an agent's internal state and the source of truth. |
| 6 | Alerts are filtered by role + severity before delivery | Directly prevents "alert fatigue" (identified as a risk) — the proactive mode is only valuable if it's trustworthy signal, not noise. |
| 7 | Simulated CRM/ERP/HRMS via public datasets (e.g. Kaggle) for the workshop build | No real company data available; simulated data lets the architecture be fully demonstrated without needing real integrations, which are explicitly out of scope for the 5-day MVP. |
| 8 | Explainability/evidence trail is a required field on every answer/alert, not optional | Chosen as part of the USP brainstorm (Explainable AI) — addresses a real, common failure mode of AI adoption (users don't trust black-box outputs). |
| 9 | 5-day build plan sequences DB → MCP/RBAC → Planner → agents (Sales, Finance, HR) → Sentinel/Alerts → frontend | Backend-first, and specifically access-control-first, so RBAC isn't retrofitted at the end; frontend is scaffolded last since it carries the least unique logic. |

## Open questions / not yet decided
- Exact anomaly-detection method for the Enterprise Intelligence Engine (simple percentage-threshold vs. something more statistical) — currently planned as simple % change over a rolling window for MVP; can be revisited if time allows.
- Whether Marketing/Support/Operations agents get real implementations or remain stubs for the workshop demo — currently planned as stubs (see `02_PRD.md` MVP scope).
- Long-term data strategy for real CRM/ERP integration — deferred to Future Scope (`09_Development_Roadmap.md`).

## How to use this log going forward
Any time a new significant decision is made (e.g. changing the anomaly-detection approach, adding a new agent, changing the RBAC model), add a row here with the decision and the reasoning — not just an update to the architecture diagram. This is what lets any teammate, or a new Claude session, understand *why* the system looks the way it does, not just what it looks like.
