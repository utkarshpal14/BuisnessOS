# BusinessOS AI — Claude Development Guide

*Read this first in any new Claude session working on this project. It tells Claude how to build, not just what to build.*

## Project context to always assume
- This is **BusinessOS AI**, a dual-mode (reactive + proactive) multi-agent enterprise intelligence platform.
- The architecture is **finalized** — see `04_System_Architecture.md`. Do not propose a redesign (e.g. separate reactive/proactive systems) unless explicitly asked to reconsider it; that debate is already resolved.
- One Planner Agent, two entry points (user query, Enterprise Intelligence Engine). This is the core design constraint — respect it in all backend code.

## Recommended folder structure
```
/backend
  /app
    /agents
      planner.py
      sales_agent.py
      finance_agent.py
      hr_agent.py
      base_agent.py        # shared interface (see 05_Agent_Design.md)
    /mcp
      access_layer.py       # RBAC-enforced data access
      connectors/
        crm_sim.py
        erp_sim.py
        hrms_sim.py
    /sentinel
      scheduler.py
      engine.py              # Enterprise Intelligence Engine
    /alerts
      alert_engine.py
    /api
      routes_auth.py
      routes_ask.py
      routes_alerts.py
      routes_admin.py
    /db
      models.py
      seed_data.py
    main.py
/frontend
  /app or /pages
    login/
    dashboard/
    ask/
    alerts/
    admin/
  /components
    EvidenceTrail.tsx        # shared between Ask and Alert detail views
/docs                          # this document set
```

## Coding conventions
- Python: FastAPI + Pydantic models for all request/response shapes. Type hints throughout.
- Every specialized agent implements the shared `handle(task, role) -> AgentResult` interface from `05_Agent_Design.md` — don't special-case agents in the Planner.
- All business-data access goes through `mcp/access_layer.py`. No agent or route should query `business_metrics` directly.
- TypeScript on the frontend; shared types for API responses should mirror the shapes in `06_API_Specification.md`.

## Build order (what to ask Claude to do, in sequence)
1. Scaffold DB schema from `07_Database_Design.md` and seed with a chosen Kaggle-style dataset.
2. Build MCP access layer with RBAC checks against `roles.permissions`.
3. Build Planner Agent skeleton (accepts a `Task`, no agents wired yet — return a stub).
4. Build one specialized agent end-to-end (Sales) and wire it into the Planner.
5. Repeat for Finance, HR.
6. Build Enterprise Intelligence Engine + scheduler, confirm it creates `Task(source="sentinel")` objects consumed by the *same* Planner method used in step 3–5.
7. Build Alert Engine.
8. Build frontend views per `08_Frontend_Design.md`.
9. Wire audit logging across all of the above.

## What NOT to do
- Don't build two separate orchestration paths for reactive vs. proactive — they must share the Planner.
- Don't implement RBAC filtering only in the frontend.
- Don't let specialized agents cache/store business data themselves — always fetch fresh via MCP.
- Don't skip the evidence/explainability field on responses — it's a functional requirement (FR-013), not decoration.

## When starting a new Claude session on this project
Paste or reference: this guide, `04_System_Architecture.md`, and `11_Decision_Log.md`. That's usually enough context for Claude to continue consistently without re-deriving the architecture from scratch.
