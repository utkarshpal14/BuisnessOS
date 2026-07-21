# BusinessOS AI — API Specification (MVP)

Base URL (dev): `http://localhost:8000`
Auth: bearer token in `Authorization` header after login (token encodes user id + role).

## Auth

### `POST /login`
Request:
```json
{ "email": "ceo@demo.com", "password": "demo123" }
```
Response:
```json
{ "token": "jwt...", "role": "CEO", "user_id": "u_001" }
```

## Reactive flow

### `POST /ask`
Request:
```json
{ "question": "Why did sales decrease this month?" }
```
Response:
```json
{
  "answer": "Sales dropped 12% mainly due to a slowdown in the Enterprise segment...",
  "agents_used": ["sales_agent", "finance_agent"],
  "evidence": [
    { "source": "sales_agent", "data_point": "Enterprise deal count down 30% MoM" },
    { "source": "finance_agent", "data_point": "Revenue -12% MoM" }
  ],
  "confidence": "high",
  "task_id": "t_1024"
}
```

## Proactive flow

### `POST /sentinel/run`
Manually triggers an Enterprise Intelligence Engine check (useful for demos instead of waiting for the scheduler).
Response:
```json
{ "anomalies_found": 1, "tasks_created": ["t_1025"] }
```

### `GET /alerts`
Returns alerts visible to the current user's role.
Response:
```json
[
  {
    "id": "a_501",
    "severity": "high",
    "summary": "Revenue anomaly detected: -22% week-over-week",
    "created_at": "2026-07-20T09:00:00Z",
    "acknowledged": false
  }
]
```

### `GET /alerts/{id}`
Full detail for one alert, including the Planner's full evidence trail (same shape as `/ask` response).

## Dashboard support

### `GET /dashboard`
Returns a summary view appropriate to the user's role (recent queries, active alert count, key KPI snapshot).

## Admin

### `GET /reports`
Returns historical query/alert audit log (Administrator/CEO only).

### `POST /sentinel/config`
Update KPI thresholds/check interval (Administrator only).
```json
{ "kpi": "revenue", "threshold_pct": 15, "window_days": 7 }
```

## Notes for implementation
- Every endpoint that touches business data must pass the caller's role down to the MCP layer — do not fetch data as a generic "system" identity and filter afterward; filter at the source.
- `task_id` in `/ask` and `/sentinel/run` responses should map to the same underlying audit log table (FR-012), since both flows go through the same Planner.
