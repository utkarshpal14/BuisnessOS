# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project state

This repository currently contains **only the specification/design docs** in `Documents/` — no `backend/` or `frontend/` code exists yet. Treat this as a from-scratch build against a finalized spec, not an existing codebase to explore for patterns.

Read order for a new session: `Documents/01_Project_Vision.md` → `Documents/04_System_Architecture.md` → `Documents/10_Claude_Development_Guide.md` → `Documents/11_Decision_Log.md`. That combination is enough context to build consistently without re-deriving the architecture.

## What this is

BusinessOS AI: a multi-agent enterprise intelligence platform with **one Planner Agent and two entry points**:
- **Reactive** — a user asks a question via the dashboard.
- **Proactive** — a scheduled Enterprise Intelligence Engine detects a KPI anomaly and creates a task itself.

Both entry points hand the Planner a `Task` of identical shape; the Planner does not branch on source except to route the final result to the dashboard (reactive) or the Alert Engine (proactive, `source == "sentinel"`). This unification is the core, non-negotiable architectural decision — see "What not to do" below.

## Architecture (the part that spans files)

```
Interface Layer (Next.js/React/TS/Tailwind)
        │ user question                    Scheduler → Enterprise Intelligence Engine
        ▼                                          │ anomaly → creates Task(source="sentinel")
        └──────────────────► PLANNER AGENT ◄────────┘
                                   │ decomposes, routes, merges
                     ┌─────────────┼─────────────┬─────────────┐
                  Sales Agent  Finance Agent   HR Agent   (Marketing/Support/Ops — stubs)
                     └─────────────┴─────────────┴─────────────┘
                                   │ all data access goes through here
                          Tool Access Layer (MCP servers) — RBAC enforced HERE
                                   │
                     Enterprise Data (CRM/ERP/HRMS, simulated via Kaggle-style datasets)
                                   │
                        Response Assembly (Planner merges AgentResults)
                          ┌────────┴────────┐
                     Dashboard          Alert Engine (proactive only — RBAC + severity routing)
```

Full diagram and worked examples: `Documents/04_System_Architecture.md`.

### Non-negotiable design constraints
- **One Planner, two entry points.** Never build separate orchestration paths for reactive vs. proactive flows — both must call the same Planner method.
- **RBAC is enforced at the MCP/Tool Access Layer, not the frontend or in agents.** The frontend only reflects what the backend permits; agents/routes never query `business_metrics` or other business tables directly.
- **Agents are stateless.** Specialized agents hold no business data themselves — they retrieve fresh via MCP on every call, never cache/store it internally.
- **Every agent implements the same interface** so the Planner can call any of them interchangeably (see `Documents/05_Agent_Design.md`):
  ```
  handle(task: Task, role: Role) -> AgentResult
  Task = { id, source: "user"|"sentinel", content, context }
  AgentResult = { summary, evidence: [{source, data_point}], confidence: "low"|"medium"|"high" }
  ```
- **The `evidence` field is required, not optional**, on every `AgentResult` and every Planner-merged response — this is the explainability requirement (FR-013) and a core USP, not decoration.
- **Partial failure is expected behavior**: if a sub-agent errors or a KPI data source is unavailable, the Planner/Engine proceeds with what it has and flags the gap, rather than failing the whole request/run.

### Recommended folder structure
```
/backend/app
  /agents      planner.py, sales_agent.py, finance_agent.py, hr_agent.py, base_agent.py
  /mcp         access_layer.py (RBAC-enforced), connectors/{crm,erp,hrms}_sim.py
  /sentinel    scheduler.py, engine.py   (Enterprise Intelligence Engine)
  /alerts      alert_engine.py
  /api         routes_auth.py, routes_ask.py, routes_alerts.py, routes_admin.py
  /db          models.py, seed_data.py
  main.py
/frontend/app  login/, dashboard/, ask/, alerts/, admin/
/frontend/components  EvidenceTrail.tsx  (shared between Ask and Alert detail views)
```

### Build order
DB schema → MCP access layer + RBAC → Planner skeleton → Sales Agent end-to-end → Finance/HR agents → Enterprise Intelligence Engine + scheduler → Alert Engine → frontend views → audit logging wired across all of the above. Access control is built before the agents that depend on it, deliberately — see decision #9 in `Documents/11_Decision_Log.md`.

## Coding conventions
- Python backend: FastAPI + Pydantic models for every request/response shape; type hints throughout.
- TypeScript frontend: types for API responses should mirror `Documents/06_API_Specification.md` exactly.
- New specialized agents register with the Planner via the shared interface/config — never special-case an agent inside Planner internals.
- `business_metrics.source` values (e.g. `"sales_crm_sim"`) map to which simulated dataset backs them — keep this explicit so a real CRM/ERP connector can later replace the simulation without a schema change.

## Data layer
Three stores, each for a distinct reason (see `Documents/07_Database_Design.md` for full schema):
- **PostgreSQL** — users, roles (with `permissions` jsonb checked by MCP), alerts, `business_metrics`, `agent_logs`, `audit_logs`, `knowledge_base` metadata.
- **Redis** — cache for frequent reads (dashboard, sessions).
- **ChromaDB** — vector store for RAG over unstructured knowledge; `knowledge_base` table holds the source-of-truth text and a `chroma_ref_id` pointer.

`agent_logs.task_id` is the thread that ties one full Planner run together with its resulting `alerts` and `audit_logs` rows — preserve this linkage in any new table that records a Planner-triggered side effect.

## Commands (once code exists)
```bash
# Backend
cd backend && pip install -r requirements.txt && uvicorn app.main:app --reload

# Frontend
cd frontend && npm install && npm run dev
```
Required `backend/.env`: `ANTHROPIC_API_KEY`, `DATABASE_URL`, `REDIS_URL`, `CHROMA_DB_PATH`.

No test/lint/build tooling is defined yet — establish it (pytest for backend, the frontend framework's standard lint/test scripts) as part of scaffolding, and update this file once commands exist.

## What NOT to do
- Don't build two separate orchestration paths for reactive vs. proactive — they must share the Planner.
- Don't implement RBAC filtering only in the frontend, or fetch data as a generic "system" identity and filter afterward — filter at the MCP source using the caller's actual role.
- Don't let specialized agents cache or store business data themselves.
- Don't skip the evidence/explainability field on responses.
- Don't propose a redesign of the reactive/proactive split — it's finalized (see `Documents/11_Decision_Log.md` for why) unless explicitly asked to revisit it.

## When a significant new decision is made
Add a row to `Documents/11_Decision_Log.md` (decision + reasoning), not just a diagram update — this is what lets a future session understand *why*, not just *what*.
