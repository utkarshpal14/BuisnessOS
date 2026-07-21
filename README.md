# BusinessOS AI

A multi-agent, dual-mode enterprise intelligence platform. It lets business leaders ask cross-department questions in plain language **and** continuously monitors business metrics on its own — proactively investigating and alerting the right people before a problem becomes critical.

Built for a Claude-assisted workshop build ("vibe coding") — this repo/doc set is written so a fresh Claude session can pick it up and build consistently without re-deriving the architecture.

---

## The core idea

One **Planner Agent**, two ways of triggering it:

- **Reactive** — a user asks a question → Planner coordinates specialist agents → answer.
- **Proactive** — a scheduled **Enterprise Intelligence Engine** detects an anomaly on its own → creates a task → same Planner investigates → **Alert Engine** notifies only the right people.

Both flows share the same reasoning core, the same specialized agents, and the same governed data-access layer (MCP). See `docs/04_System_Architecture.md` for the full diagram.

## Why it's different (USP)

- **Dual-mode** — not just Q&A, also proactive detection.
- **One shared Planner** — not two bolted-together systems.
- **Role-based access enforced at the data layer (MCP)**, not the UI — a real security decision, not a cosmetic one.
- **Explainable by default** — every answer/alert includes the evidence and agents behind it.
- **Alert discipline** — alerts are filtered by role + severity, so leaders get signal, not noise.

## Tech stack

| Layer | Technology | Why |
|---|---|---|
| Frontend | Next.js, React, TypeScript, Tailwind | Dashboard, ask/answer UI, alerts inbox |
| Backend | FastAPI | Request routing, coordination between frontend and agents |
| AI reasoning | Claude API | Powers the Planner and each specialized agent |
| Agent orchestration | LangChain, LangGraph | Chains and branches multi-step, multi-agent reasoning |
| Data access | MCP servers | Single, governed, role-aware gateway to CRM/ERP/HRMS data |
| Structured data | PostgreSQL | Users, roles, alerts, metrics, audit logs |
| Cache | Redis | Fast repeated lookups (dashboard, sessions) |
| Vector store | ChromaDB | RAG / semantic search over unstructured knowledge |
| Data source (MVP) | Public datasets (e.g. Kaggle) | Simulates CRM/ERP/HRMS since no real company data is used |

## Repository / doc structure

```
/docs
  01_Project_Vision.md          — what & why
  02_PRD.md                     — features & scope
  03_SRS.md                     — detailed requirements + RBAC matrix
  04_System_Architecture.md     — finalized architecture (start here)
  05_Agent_Design.md            — Planner, specialized agents, Sentinel, Alert Engine
  06_API_Specification.md       — endpoints, request/response formats
  07_Database_Design.md         — schema, ER relationships
  08_Frontend_Design.md         — pages, components
  09_Development_Roadmap.md     — 5-day build plan, risks, future scope
  10_Claude_Development_Guide.md— how Claude should build this (folder structure, build order, conventions)
  11_Decision_Log.md            — why each architecture decision was made
/backend    (FastAPI app — see 10_Claude_Development_Guide.md for structure)
/frontend   (Next.js app)
```

**Start here if you're new to the project:** `docs/01_Project_Vision.md` → `docs/04_System_Architecture.md` → `docs/10_Claude_Development_Guide.md`.

## MVP scope (workshop build)

- Login + role-based access (CEO, Finance Head, Sales Manager, HR Manager, Employee, Administrator)
- Natural-language query → multi-agent answer, with evidence trail
- Sales, Finance, and HR agents fully implemented (others stubbed)
- Enterprise Intelligence Engine checking 2–3 KPIs on a schedule
- Alert Engine with role/severity-based routing
- Simulated CRM/ERP/HRMS data from public datasets

Full detail: `docs/02_PRD.md`. Out-of-scope items (real integrations, Slack/mobile, predictive analytics, simulation engine) are tracked as Future Scope in `docs/09_Development_Roadmap.md`.

## Getting started (once code exists)

```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```

Environment variables needed (create `.env` in `/backend`):
```
ANTHROPIC_API_KEY=...
DATABASE_URL=postgresql://...
REDIS_URL=redis://...
CHROMA_DB_PATH=...
```

## Team / roles reference

| Role | Sees |
|---|---|
| CEO | Full company-wide data, all-severity alerts |
| Finance Head | Finance detail + company summaries, finance + high-severity alerts |
| Sales Manager | Sales detail + summaries, sales alerts |
| HR Manager | HR detail + summaries, HR alerts |
| Employee | Minimal, task-relevant only |
| Administrator | System config, audit logs, no business data |

Full RBAC matrix: `docs/03_SRS.md` §4.

## License

Workshop / academic project — license TBD.
