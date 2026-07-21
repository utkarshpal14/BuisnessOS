# BusinessOS AI — Project Vision

## What this is
BusinessOS AI is a multi-agent enterprise intelligence platform. It gives business leaders (CEO, department heads, managers) one place to ask questions about how their company is doing, and it also watches business data continuously so it can warn them *before* a problem becomes serious — instead of only answering when asked.

## The problem
Companies run on disconnected tools: a CRM for sales, an ERP for operations/finance, an HRMS for people data, separate support tools for customers. To get a full picture of the business, someone has to log into each tool, pull numbers manually, and stitch together a report. This is slow, error-prone, and reactive — problems are usually noticed only after they've already hurt the business (e.g. revenue decline is spotted a month later in a report, not the week it started).

## The solution, in one sentence
One AI Planner Agent that (a) answers cross-department questions on demand by coordinating specialist agents, and (b) continuously monitors business metrics on its own and proactively investigates and alerts the right people when something looks wrong.

## Who this is for
Internal business users — not customers. Specifically: CEOs, Finance Heads, Sales Managers, HR Managers, and other leadership/management roles who need cross-department visibility to make decisions, but shouldn't have to become power-users of five different tools to get it.

## What makes it different (USP)
1. **Dual-mode operation** — most AI business assistants are purely reactive (ask a question, get an answer). BusinessOS AI also runs a proactive Enterprise Intelligence Engine that detects anomalies before anyone asks.
2. **One shared reasoning core** — the same Planner Agent handles both modes, rather than being two disconnected products bolted together. This keeps the system simple and lets the reasoning logic improve once and benefit both flows.
3. **Governed, role-aware data access** — every piece of data any agent touches goes through a single access layer (MCP) that enforces who is allowed to see what. Role-based access isn't a UI toggle here — it's a structural security decision.
4. **Alert discipline** — the system doesn't broadcast every anomaly to everyone. Alerts are filtered by role and severity, so leaders get signal, not noise.

## Long-term vision (beyond the workshop MVP)
Grow from "detects and alerts" to "detects, investigates, recommends, and eventually simulates" — becoming closer to a continuous AI business advisor than a static dashboard. Future scope includes predictive analytics, a simulation engine for "what if" scenarios, and real ERP/CRM integrations rather than simulated datasets.

## Non-goals (explicitly out of scope for now)
- This is not a customer-facing product — no customer logins, no customer support chatbot.
- This is not trying to replace CRM/ERP/HRMS systems — it sits on top of them and reads from them (via MCP), not the other way around.
- No real production company data is used in the workshop build — public datasets simulate CRM/ERP/HRMS.
