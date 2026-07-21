# BusinessOS AI — Agent Design Document

## Common agent interface
Every agent (Planner, Sales, Finance, HR, Marketing, Support, Ops) should implement the same basic shape so the Planner can call any of them interchangeably:

```
handle(task: Task, role: Role) -> AgentResult

Task = {
  id: string
  source: "user" | "sentinel"
  content: string          # the question or investigation prompt
  context: dict             # any relevant prior context
}

AgentResult = {
  summary: string
  evidence: [ { source: string, data_point: string } ]
  confidence: "low" | "medium" | "high"
}
```

## Planner Agent
**Responsibilities**
- Receive a `Task` from either entry point (user query or Enterprise Intelligence Engine).
- Decompose it into sub-tasks and decide which specialized agent(s) are relevant.
- Call agents (in parallel where possible) via LangGraph-managed steps.
- Merge `AgentResult`s from each agent into one final response with a combined evidence trail.
- If `source == "sentinel"`, hand the final response to the Alert Engine instead of (or in addition to) the dashboard.

**Built with**: Claude API (reasoning) + LangGraph (step/state orchestration) + LangChain (chaining agent calls).

**Failure handling**: if a sub-agent errors or times out, Planner proceeds with remaining results and flags the gap in the response.

## Specialized Agents
Each specialized agent is intentionally "dumb" about anything outside its domain — it does not store data, it retrieves it fresh via MCP each time.

| Agent | Domain examples | Data accessed via MCP |
|---|---|---|
| Sales Agent | Pipeline value, deal count, forecast, capacity | CRM (simulated) |
| Finance Agent | Revenue, costs, budget variance | ERP/finance data (simulated) |
| HR Agent | Headcount, attrition rate, hiring capacity | HRMS (simulated) |
| Marketing Agent | Campaign performance, lead volume | Marketing tool data (simulated) |
| Support Agent | Ticket volume, resolution time | Support tool data (simulated) |
| Operations Agent | Fulfillment/process metrics | ERP/ops data (simulated) |

*MVP note*: implement Sales, Finance, and HR fully; stub the rest with a minimal placeholder implementation so the Planner's multi-agent routing logic can still be demonstrated.

## Enterprise Intelligence Engine
**Responsibilities**
- On a scheduled interval, pull current values for a configured list of KPIs (e.g. weekly revenue, attrition rate, pipeline value).
- Compare against thresholds/trend baselines (start simple: percentage change over a rolling window).
- On breach, construct a `Task` with `source: "sentinel"`, a severity level, and a description of what looks abnormal, and pass it to the Planner (same call as the reactive entry point).

**Configuration**: KPI list, thresholds, and check interval should be stored in the database (not hardcoded), so an Administrator can adjust them.

**Failure handling**: if a KPI data source is unavailable, log it and skip that check rather than failing the whole run.

## Alert Engine
**Responsibilities**
- Receive the Planner's merged result when `source == "sentinel"`.
- Determine severity (from the Engine's flag or Planner's assessment).
- Determine recipient list using the RBAC matrix (see `03_SRS.md` section 4) — e.g. company-wide anomalies go to CEO + relevant department head; department-specific anomalies go to that department's manager and above.
- Create notification record(s) (dashboard badge for MVP; email/Slack as future scope).

## Reasoning/evidence requirement (applies to all agents)
Every `AgentResult` and every Planner-merged response must include the `evidence` list — this is what the "Explainable AI" requirement (FR-013) is built on, and it's part of your USP, so it should not be treated as optional/cosmetic.
