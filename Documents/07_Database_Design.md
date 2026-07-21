# BusinessOS AI — Database Design

## Storage split (why three different stores)
- **PostgreSQL** — structured, relational data that needs integrity and relationships (users, roles, alerts, metrics, logs).
- **Redis** — fast cache for frequently-read, less-critical data (dashboard snapshots, session lookups) to reduce repeated Postgres hits.
- **ChromaDB** — vector store for RAG: semantic search over unstructured knowledge (policy docs, past reports, historical Q&A) so agents can retrieve relevant context by meaning, not just keyword.

## Core PostgreSQL tables (MVP)

**users**
| column | type | notes |
|---|---|---|
| id | uuid | PK |
| email | text | unique |
| password_hash | text | |
| role_id | uuid | FK → roles |
| department | text | e.g. Sales, Finance, HR |
| created_at | timestamp | |

**roles**
| column | type | notes |
|---|---|---|
| id | uuid | PK |
| name | text | CEO, Finance Head, Sales Manager, HR Manager, Employee, Administrator |
| permissions | jsonb | scopes this role can access, referenced by MCP |

**departments**
| column | type | notes |
|---|---|---|
| id | uuid | PK |
| name | text | |

**business_metrics** *(simulated CRM/ERP/HRMS data lives here for MVP)*
| column | type | notes |
|---|---|---|
| id | uuid | PK |
| department | text | |
| metric_name | text | e.g. "weekly_revenue", "attrition_rate" |
| value | numeric | |
| recorded_at | timestamp | |
| source | text | "sales_crm_sim", "finance_erp_sim", "hr_hrms_sim" |

**agent_logs**
| column | type | notes |
|---|---|---|
| id | uuid | PK |
| task_id | uuid | groups one full Planner run |
| agent_name | text | |
| input | jsonb | |
| output | jsonb | |
| created_at | timestamp | |

**alerts**
| column | type | notes |
|---|---|---|
| id | uuid | PK |
| task_id | uuid | FK → agent_logs.task_id (root cause trace) |
| severity | text | low / medium / high |
| summary | text | |
| recipients | jsonb | list of user_ids notified |
| acknowledged | boolean | default false |
| created_at | timestamp | |

**audit_logs**
| column | type | notes |
|---|---|---|
| id | uuid | PK |
| user_id | uuid | nullable (null = system/sentinel-initiated) |
| action | text | "query", "alert_generated", "data_access" |
| detail | jsonb | |
| created_at | timestamp | |

**knowledge_base** *(metadata table; actual vectors live in ChromaDB, this table stores source-of-truth text + reference id)*
| column | type | notes |
|---|---|---|
| id | uuid | PK |
| title | text | |
| content | text | |
| chroma_ref_id | text | pointer into ChromaDB collection |
| department | text | |

## Relationships (high level)
```
roles 1───* users
users 1───* audit_logs
agent_logs.task_id ── groups ── alerts, audit_logs (via task_id)
business_metrics ── read by ── Enterprise Intelligence Engine, specialized agents (via MCP)
```

## Notes
- `permissions` on `roles` is what MCP checks before returning any `business_metrics` or `knowledge_base` data — this is the concrete implementation of the RBAC matrix in `03_SRS.md`.
- `business_metrics.source` values map directly to which simulated dataset (Kaggle CSV, etc.) was loaded — keep this explicit so it's easy to swap in a real CRM/ERP connector later without changing the schema.
