# REST contract draft

Base /api/v1. Local trusted analyst identity supplied by server configuration. Before shared deployment require authenticated identity and client grants. Never accept actor from request JSON. Health exposes readiness only. JSON errors carry code, message and correlationId. Use 400 for invalid input, 401 for missing identity in shared mode, 404 for missing or inaccessible resources and 409 for conflict.

|Method and suffix|Inputs and result|
|---|---|
|GET /health|200 ready or 503 unavailable|
|GET /clients|200 array of {id,label}|
|GET /clients/{c}/overview|optional snapshotId, returns cutoff, itemCount, decliningCount, coverage|
|GET /clients/{c}/rankings|optional runId, status, cursor, limit 1–100 (default 50). Returns runId, items, nextCursor. No publication returns empty items and pending state|
|GET /clients/{c}/rankings/{run}/items/{i}|position, score, reason codes, observed value/unit/window, current review version|
|GET /clients/{c}/items/{i}/observations|ordered snapshots with cutoff, metric values and units|
|POST /clients/{c}/items/{i}/actions|decision enum, optional note up to 1000 chars, expectedVersion. Idempotency-Key required. 201 event, replay 200, different body under same key 409|
|PATCH /clients/{c}/items/{i}/status|target status and expectedVersion, same request-key semantics. 200 updated status/version|
|GET /clients/{c}/items/{i}/actions|cursor pagination, chronological events with actor and UTC timestamp|
|GET /clients/{c}/runs/{run}|state, cutoff, publishedAt, modelVersion, input digest|
|GET /clients/{c}/models/{version}|metadata for model referenced by accessible client run, registry version, feature contract|

Example review body `{"decision":"defer","expectedVersion":3,"note":"Recheck next window"}`. A decision records evidence context and leaves status unchanged. Status updates use the separate transition endpoint. Both increment the review version.
