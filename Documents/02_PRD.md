# BusinessOS AI — Product Requirements Document (PRD)

## 1. Overview
BusinessOS AI is a multi-agent, dual-mode enterprise intelligence platform. See `01_Project_Vision.md` for the full narrative; this document defines *what* gets built.

## 2. Goals
- Let a business user ask a natural-language question spanning multiple departments and get one coherent answer.
- Continuously monitor business metrics and proactively flag anomalies before a human asks about them.
- Enforce role-based access so each user only sees data relevant/permitted to their role.
- Provide an auditable trail of what data was accessed and what alerts were generated, and why.

## 3. Target users / personas
| Persona | Needs |
|---|---|
| CEO | Company-wide visibility, high-severity alerts only, cross-department summaries |
| Finance Head | Financial metrics, cost/revenue anomalies, budget-related queries |
| Sales Manager | Pipeline, deal capacity, sales-specific anomalies |
| HR Manager | Staffing, attrition, hiring capacity |
| Employee (basic) | Limited, task-relevant access only — no company-wide financials |
| Administrator | Configures monitoring thresholds, manages roles/users, views audit logs |

## 4. MVP Scope (workshop build — 5 day target)
**In scope:**
- Login + role-based access (RBAC)
- Natural-language query → Planner Agent → specialized agent(s) → merged answer, shown on a dashboard
- At least 3 specialized agents functioning: Sales, Finance, HR
- Enterprise Intelligence Engine running on a schedule, checking at least 2–3 KPIs for anomalies (e.g. revenue trend, attrition rate)
- Alert Engine that filters notifications by role and severity
- Simulated CRM/ERP/HRMS data sourced from public datasets (e.g. Kaggle) loaded into the database
- Basic dashboard: ask a question, view answer, view alerts inbox

**Out of scope for MVP (Future Scope, see `09_Development_Roadmap.md`):**
- Real CRM/ERP integrations
- Slack/mobile notifications
- Predictive analytics / simulation engine
- Voice assistant

## 5. Functional Requirements
| ID | Requirement |
|---|---|
| FR-001 | Users can log in and are assigned a role at login |
| FR-002 | System enforces role-based access at the data-access layer (MCP), not just the UI |
| FR-003 | Users can submit a natural-language business question |
| FR-004 | Planner Agent decomposes the question into sub-tasks and routes them to relevant specialized agents |
| FR-005 | Sales Agent can answer sales-pipeline/capacity questions using simulated CRM data |
| FR-006 | Finance Agent can answer cost/revenue/budget questions using simulated ERP/finance data |
| FR-007 | HR Agent can answer staffing/attrition/hiring questions using simulated HRMS data |
| FR-008 | Enterprise Intelligence Engine runs on a schedule and checks defined KPIs for anomalies |
| FR-009 | On anomaly detection, the Engine creates an investigation task and passes it to the Planner Agent (same code path as a user question) |
| FR-010 | Alert Engine determines which users should be notified of a given alert, based on role and severity |
| FR-011 | Dashboard displays answers to user questions and a list of active alerts |
| FR-012 | System stores an audit log of queries, data accessed, and alerts generated |
| FR-013 | Every answer/alert includes the reasoning/evidence behind it (which agents were consulted, what data was used) |

## 6. Non-Functional Requirements
| Category | Requirement |
|---|---|
| Performance | Reactive query should return an answer within a few seconds for the MVP dataset size |
| Security | RBAC enforced server-side (MCP layer); no direct client access to raw data |
| Explainability | Every AI-generated answer/alert shows what data/agents informed it |
| Reliability | If one specialized agent fails, the Planner should still return partial results rather than fail entirely |
| Maintainability | New specialized agents should be addable without changing the Planner's core logic |
| Scalability (design intent, not MVP requirement) | Architecture should allow adding new data sources (via new MCP connectors) without redesigning agents |

## 7. Success Criteria (for workshop demo)
- A user can ask a cross-department question and get a correct, explainable answer.
- The Enterprise Intelligence Engine can detect an injected anomaly (e.g. artificially drop revenue in the sample dataset) and generate a correct, correctly-routed alert.
- Two different user roles see visibly different levels of access/alerts for the same underlying data.
