# BusinessOS AI — Frontend Design (MVP)

*Kept intentionally light since frontend logic is not the project's core complexity — the goal here is a clear, functional interface, largely Claude-scaffolded.*

## Stack
Next.js + React + TypeScript + Tailwind CSS.

## Pages / views

**1. Login**
- Simple email/password form → calls `POST /login` → stores token + role.

**2. Dashboard (home)**
- KPI snapshot cards (role-appropriate — CEO sees company-wide, Sales Manager sees sales-only, etc.)
- Active alerts count/badge
- "Ask a question" input box (primary interaction)

**3. Ask / Answer view**
- Text input → submits to `POST /ask`
- Displays: answer text, "how I got this" evidence trail (collapsible), confidence indicator
- History of past questions (from audit log) accessible below

**4. Alerts inbox**
- List from `GET /alerts`, sortable by severity/date
- Click into an alert → full detail view (`GET /alerts/{id}`) showing root-cause evidence trail, same structure as the Ask/Answer view
- Acknowledge button

**5. Admin panel** (Administrator role only)
- KPI threshold configuration (`POST /sentinel/config`)
- Manual sentinel trigger button (`POST /sentinel/run`) — useful for demoing the proactive flow live
- Audit log viewer (`GET /reports`)

## Role-aware rendering rule
The frontend should never decide what data a user can see — it only renders what the backend already filtered. Do not implement client-side hiding of sensitive fields as a security measure; treat it purely as UX (the backend/MCP layer is the actual gate, per `03_SRS.md`).

## Component reuse
The "answer/evidence" display component should be shared between the Ask view and the Alert detail view — they're structurally the same data (Planner's merged response), which is a direct visual expression of the "one Planner, two entry points" architecture decision.
