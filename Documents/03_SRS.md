# BusinessOS AI — Software Requirements Specification (SRS)

## 1. Introduction
This document specifies functional and non-functional requirements for BusinessOS AI in implementation-ready detail, building on the PRD (`02_PRD.md`) and the finalized architecture (`04_System_Architecture.md`).

## 2. Scope
Covers backend (FastAPI + Planner + specialized agents + MCP + Enterprise Intelligence Engine + Alert Engine), data layer (PostgreSQL, Redis, ChromaDB), and frontend dashboard (Next.js/React/TypeScript/Tailwind), for the workshop MVP.

## 3. Stakeholders
- CEO / executive leadership
- Department managers (Sales, Finance, HR, Marketing, Ops)
- Individual employees (limited access)
- IT/System Administrator
- Development team (you and your teammates)
- Workshop evaluators (grading the demo/viva)

## 4. User Roles & Permissions (RBAC matrix)
| Role | Can query | Data visibility | Receives alerts |
|---|---|---|---|
| CEO | All departments | Full company-wide | All severities |
| Finance Head | Finance-focused, can see sales/HR summaries | Finance detail, others summarized | Finance + high-severity company-wide |
| Sales Manager | Sales-focused | Sales detail, others summarized | Sales-related only |
| HR Manager | HR-focused | HR detail, others summarized | HR-related only |
| Employee | Own-task-relevant only | Minimal | None (or only directly relevant) |
| Administrator | System configuration | N/A (config, not business data) | System/config alerts only |

Enforcement point: **Tool Access Layer (MCP)**, not the frontend. The frontend simply reflects what the backend permits.

## 5. Functional Requirements (detailed)
Mirrors FR-001 through FR-013 in the PRD; below adds acceptance-level detail.

- **FR-001 Login**: Email/password (or workshop-simplified auth) → returns a session/token carrying the user's role.
- **FR-002 RBAC enforcement**: Every MCP data request includes the requesting user's role; MCP rejects or redacts data outside that role's permission.
- **FR-003 Natural language query**: Free-text input on the dashboard, sent to `POST /ask`.
- **FR-004 Planner Agent**: Receives a task object `{source: "user"|"sentinel", role, content}`, decomposes it, and calls one or more specialized agents.
- **FR-005–007 Specialized Agents**: Each agent exposes a consistent internal interface (`handle(task, role) -> result`) so the Planner can call any of them uniformly.
- **FR-008–009 Enterprise Intelligence Engine**: Runs via scheduler; checks configured KPI thresholds; on breach, creates a task with `source: "sentinel"` and severity, and calls the same Planner entry point as FR-004.
- **FR-010 Alert Engine**: Given a Planner result with `source: "sentinel"`, determines recipient list via the RBAC matrix + severity, and creates notification records.
- **FR-011 Dashboard**: Two main views — Ask (query + answer) and Alerts (list of active alerts, filterable).
- **FR-012 Audit log**: Every query and every alert is persisted with timestamp, user/role, data sources touched, and result summary.
- **FR-013 Explainability**: Planner's merged response includes a short "how I got this answer" trace (agents consulted + data sources).

## 6. Non-Functional Requirements (detailed)
- **Security**: No agent or frontend component queries CRM/ERP/HRMS data directly — only through MCP. Secrets/API keys are never exposed to the frontend.
- **Explainability**: Required on every answer/alert (not optional) — this is core to the product's trust story.
- **Reliability**: Partial-failure handling — if a specialized agent errors out, the Planner returns available results with a note on what's missing, rather than a full failure.
- **Availability**: Not a 24/7 production requirement for MVP, but the Enterprise Intelligence Engine's scheduler should run reliably during the demo window.
- **Maintainability**: New agents register with the Planner via a simple interface/config, not by modifying Planner internals.

## 7. Constraints
- Workshop timeline: ~5 days for a working prototype.
- Budget: simulated (workshop credits), so external paid tools should be avoided beyond what's already decided (Claude API).
- Data: public/simulated datasets only, no real company data.

## 8. Assumptions
- Claude API is available and usable within workshop credit limits.
- Team has basic familiarity with Python/FastAPI and React/Next.js, or is comfortable using Claude to scaffold both ("vibe coding") while understanding the architecture conceptually.
