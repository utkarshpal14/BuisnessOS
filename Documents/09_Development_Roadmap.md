# BusinessOS AI — Development Roadmap

## 5-day workshop plan

**Day 1 — Foundation**
- Set up repo structure (backend/frontend split), FastAPI skeleton, Next.js skeleton.
- Set up PostgreSQL schema (`07_Database_Design.md`) and seed with a simulated dataset (Kaggle sales/HR/finance data).
- Implement login + role model (FR-001, FR-002).

**Day 2 — Reactive flow, core**
- Implement Planner Agent skeleton (LangGraph/LangChain + Claude API call).
- Implement MCP-style data access layer with RBAC enforcement.
- Implement Sales Agent and Finance Agent (real logic), HR Agent stubbed.
- Wire `POST /ask` end-to-end for a simple single-agent question.

**Day 3 — Reactive flow, multi-agent + Proactive flow foundation**
- Extend Planner to handle multi-agent decomposition/merging (a question needing 2+ agents).
- Implement HR Agent fully.
- Build Enterprise Intelligence Engine: scheduler + KPI threshold checks against `business_metrics`.
- Confirm sentinel-created tasks flow through the *same* Planner code path as user tasks (this is the architectural point to explicitly test).

**Day 4 — Alerts + End-to-end integration**
- Implement Alert Engine (recipient selection via RBAC + severity).
- Wire `GET /alerts`, `GET /alerts/{id}`.
- Frontend: Ask view, Alerts inbox, shared evidence-display component.
- End-to-end test: inject an anomaly into the seeded dataset, confirm the Engine detects it, Planner investigates, correct role(s) get alerted.

**Day 5 — Polish + demo readiness**
- Admin panel (config + manual sentinel trigger for live demo).
- Audit log viewer.
- UI polish pass.
- Rehearse: one reactive demo question + one live-triggered proactive alert, showing evidence trails and RBAC differences across two roles.

## Definition of done (MVP)
- A user can log in as at least two different roles and see different data/alerts.
- A cross-department question returns a correct, evidence-backed answer.
- An injected anomaly is detected, investigated, and correctly routed to the right role(s) — demonstrably through the same Planner used for reactive queries.

## Future scope (post-workshop / not required for demo)
- Real CRM/ERP/HRMS integrations replacing simulated datasets
- Slack and email notification channels
- Predictive analytics (forecasting instead of pure anomaly detection)
- Simulation/"what-if" engine
- Mobile app
- Voice assistant interface
- AI decision-coach layer (personalized recommendations per leader, per the earlier USP brainstorm)

## Risks to watch
| Risk | Mitigation |
|---|---|
| Alert fatigue / false positives | Keep thresholds conservative for MVP; tune during Day 3–4 testing |
| API cost (Claude calls) | Cache repeated queries where reasonable; keep agent calls lean |
| Scope creep (adding agents/features late) | Anything not in MVP scope (`02_PRD.md` §4) goes to Future Scope, not this sprint |
| Team member unclear on architecture | Refer to `04_System_Architecture.md` and `11_Decision_Log.md` before improvising new structure |
