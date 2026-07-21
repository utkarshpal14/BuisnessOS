# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project state

This repository has a working backend: a Planner-orchestrated multi-agent core (Sales, Finance, Enterprise, AI Agents), a FastAPI layer over it, and a test suite (`tests/`, run with `python -m unittest discover -s tests`). There is **no frontend yet, and none of Postgres/Redis/ChromaDB/Scheduler/Sentinel/Alert Engine/full RBAC exist yet** — those are deliberately deferred (see "Deferred, seam-only" below). Read order for a new session: this file → `Documents/11_Decision_Log.md` (why things are the way they are) → `Documents/04_System_Architecture.md` / `05_Agent_Design.md` (original target vision — read with the deltas below in mind, since some details there predate what actually shipped).

## What this is

BusinessOS AI: a multi-agent enterprise intelligence platform with **one Planner and multiple entry points**:
- **Reactive** — a user asks a question (CLI `demo.py`, or the FastAPI layer).
- **Proactive** *(deferred, not yet built)* — a scheduled Enterprise Intelligence Engine would detect a KPI anomaly and create a task itself.

Both entry points hand the Planner a `PlannerTask` of identical shape; the Planner does not branch on source except to route the final result differently (reactive → caller; proactive → an Alert Engine, once built). This unification is the core, non-negotiable architectural decision — see "What not to do" below. The reactive path is fully implemented today; the proactive path is intentionally not built yet, but nothing about `PlannerService` needs to change to add it later — see "Deferred, seam-only" below for exactly what plugs in where.

## Architecture (the part that spans files)

```
Interface Layer (not yet built)         Scheduler (not yet built)
        │ user question                          │ anomaly → Task(source="sentinel")
        ▼                                          ▼
        └──────────────────► PLANNER SERVICE ◄────────┘
                                   │ routes, invokes, aggregates
                     ┌─────────────┼─────────────┬─────────────┐
                  Sales Agent  Finance Agent  Enterprise Agent  AI Agent
                     └─────────────┴──────┬──────┴─────────────┘
                                          │ all data access goes through here
                                 Data Access Layer (per-domain gateway)
                                          │
                              Enterprise Data (CSV datasets today;
                              simulated CRM/ERP, real ones later)
                                          │
                                 (results flow back through Planner)
                                          │
                          PlannerResponse (evidence-bearing, role-aware)
                          ┌───────────────┴────────────────┐
                     Caller (CLI/API)          Alert Engine (not yet built)
```

Full original narrative diagram (predates the Enterprise/AI Agents and the current module layout): `Documents/04_System_Architecture.md`.

### Non-negotiable design constraints
- **One Planner, all entry points.** Never build a separate orchestration path for a new entry point (proactive, Slack, etc.) — every entry point must construct a `PlannerTask` and call `PlannerService.execute_task()`, the same method the reactive path uses.
- **Agents never access a dataset/file/DB directly.** All data access goes through that domain's Data Access Layer gateway (`app/<domain>/data_access.py`, e.g. `SalesDataAccess`, `FinanceDataAccess`). This is the seam RBAC will later enforce against — see "Deferred, seam-only" below.
- **Agents are stateless.** Specialized agents hold no business data themselves — they retrieve fresh via their Data Access Layer gateway on every call, never cache/store it internally.
- **Every agent implements the same interface** (`app/agents/base.py: BaseAgent`) so the Planner can call any of them interchangeably:
  ```python
  class BaseAgent(ABC):
      name: str                                        # @property
      def execute(self, task: PlannerTask) -> AgentResult: ...

  PlannerTask = {
    task_id, task_type, source: "user" | "sentinel", query,
    role: Optional[str],       # caller's role; None until auth exists — agents/gateways must accept None
    metadata: dict,             # includes upstream_results, populated generically by PlannerService
    timestamp,
  }

  AgentResult = {
    agent_name, status: "success" | "error", summary,
    evidence: List[EvidenceItem],   # [{source, data_point}] — required, may be empty list, never omitted
    confidence: "low" | "medium" | "high",
    data: dict,                     # domain-specific structured payload
    error_message: Optional[str],
  }
  ```
- **The `evidence` field is required, not optional**, on every `AgentResult` — this is the explainability requirement (FR-013) and a core USP, not decoration. An agent with nothing to cite returns `evidence: []`, not a missing field.
- **New agents register with the Planner via `app/planner/bootstrap.py`** — never special-case an agent inside `PlannerService`/`SimpleTaskRouter` internals beyond the `task_type → agent names` mapping already there.
- **Partial failure is expected behavior**: if a sub-agent errors or a data source is unavailable, the Planner proceeds with what it has and flags the gap, rather than failing the whole request.

### Deferred, seam-only (do not fully implement yet)
These are explicitly **not** to be built out yet, but the live code already has (or Step 4/5 of the current refactor adds) the seam each one will plug into without a rewrite:
- **PostgreSQL / Redis / ChromaDB** — no persistence exists yet. Seam: `PlannerResponse.task_id` is already the join key every future `agent_logs`/`alerts`/`audit_logs` row would use.
- **Scheduler / Enterprise Intelligence Engine (Sentinel)** — no proactive monitoring exists yet. Seam: it would build a `PlannerTask(source="sentinel", ...)` and call the *same* `build_planner().execute_task()` the reactive path uses — no `PlannerService` change needed.
- **Alert Engine** — no notification routing exists yet. Seam: it would consume a `PlannerResponse` where `task.source == "sentinel"`, exactly like a caller consumes one today.
- **Full RBAC enforcement** — not implemented. Seam: `PlannerTask.role` and each domain's Data Access Layer gateway already exist so a role check can be added inside the gateway later without touching any agent or the Planner.
- **Frontend** — do not start frontend work until the backend refactor checklist in `Documents/11_Decision_Log.md` is complete (explicit project instruction, not just a suggestion).

### Recommended folder structure (current, not aspirational)
```
/backend/app
  /common      keyword_mapper.py                (shared keyword-matching mechanism only)
  /planner     models.py, registry.py, router.py, service.py, bootstrap.py, exceptions.py
  /agents      base.py                          (shared BaseAgent contract only)
  /sales       agent.py, analytics_service.py, data_access.py, query_mapper.py, exceptions.py
  /finance     agent.py, analytics_service.py, data_access.py, query_mapper.py, exceptions.py
  /enterprise  agent.py, analytics_service.py, models.py (BusinessSnapshot), query_mapper.py
  /ai          agent.py, intelligence_service.py, llm_adapter.py
  /api         deps.py, routes_planner.py
  main.py
/frontend      (not started)
```
`/mcp`, `/sentinel`, `/alerts`, `/db` do not exist yet — see "Deferred, seam-only" above for where that logic will attach when built, and `Documents/11_Decision_Log.md` for why the folder layout moved from CLAUDE.md's original `/agents`-centric structure to one-folder-per-domain.

### Build order (what's actually happened, and what's next)
Done: Planner skeleton → Sales Agent → Finance Agent → Enterprise Agent → AI Agent → FastAPI layer → contract redesign (role/evidence/confidence) → Data Access Layer seam → shared bootstrap → generic Enterprise aggregation → consolidated query/routing logic.
Next (in order, before frontend): none currently blocking — frontend may begin once `Documents/11_Decision_Log.md`'s refactor checklist shows complete.
Future (post-frontend or as needed): DB/Redis/ChromaDB persistence, Scheduler + Sentinel, Alert Engine, full RBAC enforcement, auth/login.

## Coding conventions
- Python backend: FastAPI + Pydantic models for every request/response shape; type hints throughout.
- TypeScript frontend (once started): types for API responses should mirror the FastAPI `response_model`s exactly (not `Documents/06_API_Specification.md`, which predates the live endpoint surface — see Decision Log).
- New specialized agents register with the Planner via `app/planner/bootstrap.py` — never special-case an agent inside Planner internals.
- Keep each domain's Data Access Layer gateway (`data_access.py`) as the only file in that domain allowed to touch a filesystem/CSV/future DB connection.

## Commands
```bash
# Backend
cd backend && pip install -r requirements.txt && uvicorn app.main:app --reload

# Tests
python -m unittest discover -s tests

# Unified CLI
python demo.py
```
No `.env`/API keys are required yet — nothing in the live code calls an external API or a real database. `backend/requirements.txt` reflects only what's actually imported; add a dependency there only when you start using it.

## What NOT to do
- Don't build a separate orchestration path for a new entry point — it must call `PlannerService.execute_task()`.
- Don't let an agent read a CSV/file/DB directly — go through that domain's Data Access Layer gateway.
- Don't let specialized agents cache or store business data themselves.
- Don't skip the `evidence`/`confidence` fields on an `AgentResult` — return `evidence: []` if there's genuinely nothing to cite, never omit the field.
- Don't hardcode another domain's field names inside `EnterpriseAgent`/`EnterpriseAnalyticsService` — it must aggregate whatever domains are present in `upstream_results` generically.
- Don't duplicate agent-registry construction — always build a `PlannerService` via `app/planner/bootstrap.py`.
- Don't implement Postgres/Redis/ChromaDB/Scheduler/Sentinel/Alert Engine/full RBAC without a corresponding Decision Log entry explaining why the deferral ended.
- Don't start frontend work before the current backend refactor checklist is complete.

## When a significant new decision is made
Add a row to `Documents/11_Decision_Log.md` (decision + reasoning), not just a diagram update — this is what lets a future session understand *why*, not just *what*.
