# BusinessOS AI — Finalized System Architecture

> **Status note (see `Documents/11_Decision_Log.md`):** this document is the original target vision and is still correct on the *why* (one Planner/two entry points, RBAC at the data layer, stateless agents, evidence-first). For the *current, as-built* module layout, agent interface, and what's deliberately deferred vs. done, read `CLAUDE.md` first — some specifics below (folder names, MCP-as-a-literal-server, "Business Sentinel Agent") predate the Enterprise/AI Agents and the per-domain module structure that actually shipped.

*This document locks down the architecture that was being debated in the earlier discussion (reactive vs. proactive flows, Business Sentinel Agent, etc.) into one final, unambiguous design. Use this as the single source of truth going forward — including when briefing Claude/your team to start building.*

---

## 1. What the product actually is

**BusinessOS AI** is a **multi-agent enterprise intelligence platform** with one job: give business leaders (CEO, department heads, managers) a single place to ask questions about the company *and* get warned automatically when something is going wrong — instead of digging through separate CRM/ERP/HRMS tools or waiting for a monthly report.

It has two modes of use, but **one underlying engine**:

- **Reactive mode** — a person asks a question, the system answers it.
- **Proactive mode** — the system notices a problem on its own and alerts the right person.

The key architectural decision (finalized below) is that these two modes are **not two separate systems**. They both feed into the **same Planner Agent**. This was the "unified architecture" idea from the discussion, and it's the version you should build — it's simpler, more defensible in a viva, and closer to how real enterprise systems (Gmail, monitoring platforms, etc.) are actually built.

---

## 2. The one core principle

> **The Planner Agent doesn't care where a task comes from. It only cares that it received one.**

There are two "entry points" that create tasks for the Planner:

| Entry Point | Who/what triggers it | Example task created |
|---|---|---|
| 1. User Query | A human asks a question in the dashboard | "Why did sales drop this month?" |
| 2. Enterprise Intelligence Engine | A scheduled monitoring job detects an anomaly | "Investigate: revenue down 22% week-over-week" |

Both entry points hand the Planner a task in the same shape. The Planner doesn't run different code depending on the source — it just plans, delegates, and merges results either way. This is what makes the system extensible later (Slack, email, mobile app, external API can all become new entry points without touching the Planner's logic).

---

## 3. Finalized Layer-by-Layer Architecture

```
                         ┌─────────────────────────┐
                         │      INTERFACE LAYER     │
                         │  Dashboard (Next.js/React)│
                         │  Alerts inbox, chat query │
                         └────────────┬─────────────┘
                                      │  (user asks a question)
                                      ▼
┌───────────────┐            ┌───────────────────┐
│   SCHEDULER    │──trigger──▶│ ENTERPRISE         │
│ (cron / timer) │            │ INTELLIGENCE ENGINE│
└───────────────┘            │ (monitors KPIs,     │
                              │  detects anomalies) │
                              └─────────┬───────────┘
                                        │ (anomaly found → creates task)
                                        ▼
                         ┌─────────────────────────┐
                         │      PLANNER AGENT        │  ◀── single brain,
                         │  (task decomposition,     │      two entry points
                         │   agent routing,          │      converge here
                         │   response merging)        │
                         └────────────┬─────────────┘
                                      │ delegates sub-tasks
                       ┌──────────────┼──────────────┬─────────────┐
                       ▼              ▼              ▼             ▼
                 ┌──────────┐  ┌───────────┐  ┌──────────┐  ┌───────────┐
                 │  Sales    │  │  Finance   │  │   HR      │  │ Marketing/│
                 │  Agent    │  │  Agent     │  │  Agent    │  │ Ops Agent │
                 └────┬──────┘  └─────┬──────┘  └────┬─────┘  └─────┬─────┘
                      │               │              │              │
                      └───────────────┴──────┬───────┴──────────────┘
                                              ▼
                                   ┌────────────────────┐
                                   │  TOOL ACCESS LAYER   │
                                   │   (MCP servers)       │
                                   │  secure, governed,    │
                                   │  role-aware access    │
                                   └──────────┬─────────────┘
                                              ▼
                                   ┌────────────────────┐
                                   │   ENTERPRISE DATA     │
                                   │  CRM · ERP · HRMS ·   │
                                   │  Support tools         │
                                   │  (simulated w/ Kaggle  │
                                   │   datasets for now)    │
                                   └────────────────────┘

              (results flow back up through agents → Planner)
                                      │
                                      ▼
                         ┌─────────────────────────┐
                         │  RESPONSE ASSEMBLY        │
                         │  Planner merges agent      │
                         │  outputs into one answer   │
                         └────────────┬─────────────┘
                                      │
                       ┌──────────────┴───────────────┐
                       ▼                               ▼
              ┌──────────────┐               ┌────────────────────┐
              │  Dashboard     │               │  ALERT ENGINE        │
              │  (reactive      │               │  (proactive path      │
              │  answer shown)  │               │  only — decides WHO    │
              │                │               │  should be notified,   │
              │                │               │  based on RBAC,        │
              │                │               │  severity)              │
              └──────────────┘               └──────────┬─────────┘
                                                          ▼
                                                ┌──────────────────┐
                                                │  Notified users    │
                                                │  (dashboard badge,  │
                                                │   email — Slack     │
                                                │   later)             │
                                                └──────────────────┘
```

**How to read this:** the *top half* differs depending on whether a human asked something or the system detected something. The *bottom half* — Planner → specialized agents → MCP → enterprise data → back up — is completely identical either way. That shared middle section is your actual product. The two entry points are just two doors into the same building.

---

## 4. Component responsibilities (final naming — use these terms consistently)

| Component | Responsibility | Notes |
|---|---|---|
| **Interface Layer** | Where a human interacts with the system: ask questions, view dashboard, see alerts | Next.js + React + TypeScript + Tailwind. No business logic lives here — it only displays what the backend sends. |
| **Scheduler** | Fires the Enterprise Intelligence Engine at fixed intervals (e.g. hourly) | A simple cron/timer job in the backend. |
| **Enterprise Intelligence Engine** *(replaces the earlier "Business Sentinel Agent" name)* | Continuously watches business metrics (revenue, attrition, pipeline, costs) and flags anomalies | This is your USP layer. Its only job is "is something abnormal?" — it does NOT investigate why. It just creates an investigation task and hands it to the Planner. |
| **Planner Agent** | Receives a task (from a user or from the Intelligence Engine), breaks it into sub-tasks, decides which specialized agent(s) to call, and merges their answers into one coherent response | This is the "brain." Built with Claude API + LangGraph (for step orchestration) + LangChain (for chaining agent calls). |
| **Specialized Agents** (Sales, Finance, HR, Marketing, Support, Operations) | Each knows *how* to answer questions in its domain, but holds no data itself | They don't store sales numbers — they know how to ask the Tool Access Layer for sales numbers and interpret the result. |
| **Tool Access Layer (MCP servers)** | The single, secure gateway between agents and real business systems | Enforces role-based access control (RBAC) here — this is where "employee vs CEO see different things" actually gets enforced, not in the frontend. |
| **Enterprise Data** | CRM, ERP, HRMS, support tools — real systems in production; simulated with public datasets (Kaggle etc.) for the workshop build | You are not storing "the company's data" yourself; you're building the layer that would plug into it. |
| **Response Assembly** | Planner's final merge step — turns multiple agent outputs into one clear answer or report | Same code path for both reactive and proactive flows. |
| **Alert Engine** | Only fires on the proactive path. Decides *who* should be notified (based on role and severity) and *how* (dashboard, email, later Slack) | This is what stops the Intelligence Engine from spamming everyone every time a number moves. |
| **Database Layer** | PostgreSQL (structured data — users, roles, alerts, metrics, audit logs), Redis (fast cache), ChromaDB (vector store for RAG / knowledge base) | Three different tools because they solve three different problems: relational storage, speed, and semantic search. |

---

## 5. Why each core technology exists (backend focus, since that's what you asked about)

| Technology | Role in this architecture | Plain-language reason |
|---|---|---|
| **FastAPI** | Backend framework — receives requests from the frontend, routes them to the Planner | The "front desk" of your backend. Every request (ask a question, view alerts, login) passes through it. |
| **Claude API** | The actual reasoning engine inside the Planner and each specialized agent | This is what reads a question, decides what's needed, and writes the answer. |
| **LangChain** | Chains multiple AI calls together in sequence | If answering a question needs 3 steps (ask Sales agent → ask Finance agent → summarize), LangChain handles passing outputs from one step into the next. |
| **LangGraph** | Manages the *order and branching* of those steps as a graph/state machine | Where LangChain is "do step A then B," LangGraph is "if condition X, go to agent Y; otherwise go to agent Z" — needed once you have multiple agents and two entry points (reactive/proactive) instead of one straight line. |
| **MCP servers** | Standardized, secure protocol for agents to call external tools/data sources | Instead of every agent writing custom code to talk to a CRM, ERP, HRMS, etc., they all speak through one consistent, governed interface. This is also where RBAC is enforced. |
| **PostgreSQL** | Stores structured, relational data: users, roles, alerts, business metrics, audit logs | The permanent record of "who did what, what happened, what was flagged." |
| **Redis** | Fast in-memory cache | Speeds up repeated lookups (e.g., a dashboard that refreshes often) without hitting Postgres every time. |
| **ChromaDB** | Vector database for RAG (Retrieval-Augmented Generation) | Lets agents search unstructured knowledge (policies, past reports, documentation) by meaning, not just exact keyword match. |

---

## 6. Two worked examples, using the finalized flow

**Reactive example**
1. Sales Manager types: *"Can we handle a new client needing 20% more capacity?"*
2. Interface Layer sends this to FastAPI → Planner Agent.
3. Planner decomposes: needs sales pipeline capacity + HR staffing availability.
4. Planner calls Sales Agent and HR Agent.
5. Each agent goes through the Tool Access Layer (MCP) to fetch the relevant data (respecting the Sales Manager's role — they can't see full company payroll, only staffing counts).
6. Agents return answers → Planner merges them → "Yes, current staffing supports this, but sales capacity is tight — recommend hiring 2 more reps."
7. Interface Layer displays this in the dashboard.

**Proactive example**
1. Scheduler fires the Enterprise Intelligence Engine at the top of the hour.
2. It checks KPIs and finds revenue is down 22% week-over-week — flags it as anomalous.
3. It creates a task: *"Investigate revenue anomaly"* → hands it to the Planner (same Planner as above).
4. Planner delegates to Sales Agent (pipeline check) and Finance Agent (cost check) via MCP.
5. Planner merges findings into a root-cause summary.
6. Instead of going to the dashboard for everyone, it's handed to the **Alert Engine**, which checks RBAC + severity and decides: notify the CEO and the Finance Head only.
7. Those two users see a badge/notification; everyone else sees nothing (no alert fatigue).

---

## 7. What this finalizes (decisions made, not open for further debate)

- ✅ One Planner Agent, two entry points (user query, Enterprise Intelligence Engine) — not two separate architectures.
- ✅ Renamed "Business Sentinel Agent" → **Enterprise Intelligence Engine** for clarity and to sound like a genuine architectural layer rather than "just another agent."
- ✅ RBAC is enforced at the **Tool Access Layer (MCP)**, not the frontend — this is what makes the earlier "role-based access" idea actually defensible as more than "yeh to masti hai": it's a security-layer design decision, not just a UI toggle.
- ✅ Agents hold no data themselves — they are reasoning + retrieval logic only. All real data access goes through MCP.
- ✅ Alerts are filtered by role and severity before reaching anyone — this is what prevents your proactive mode from becoming spam, and it's a genuine differentiator worth mentioning as your USP.
- ✅ For the workshop build, "Enterprise Data" = public datasets (e.g. Kaggle) standing in for CRM/ERP/HRMS. This is explicitly a simulation, not a limitation you need to apologize for — real companies would plug in their own CRM/ERP later.

---

## 8. Recommended next document

With this architecture locked, the next useful artifact is a short **Project Context & Decision Log** (one page) recording *why* these choices were made — so if you hand this to Claude in a new session, or a teammate picks it up later, the reasoning survives, not just the diagram. Happy to draft that next if useful.
