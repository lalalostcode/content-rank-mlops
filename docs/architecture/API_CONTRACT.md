# REST contract draft

Base /api/v1. Local trusted analyst identity supplied by server configuration. Before shared deployment require authenticated identity and client grants. Never accept actor from request JSON. Health exposes readiness only. JSON errors carry code, message and correlationId. Use 400 for invalid input, 401 for missing identity in shared mode, 404 for missing or inaccessible resources and 409 for conflict.

|Method and suffix|Inputs and result|
|---|---|
|GET /health|200 ready or 503 unavailable|
|GET /clients|200 array of {id,label}|
|GET /clients/{c}/overview|optional snapshotId, returns cutoff, itemCount, decliningCount, coverage|
|GET /clients/{c}/rankings|optional runId, status, cursor, q (case-insensitive content ID search, up to 128 characters), limit 1–100 (default 50). Returns runId, items, nextCursor and pending. The status filter uses the effective case at the requested run's cutoff. No publication returns empty items and pending state|
|GET /clients/{c}/rankings/{run}/items/{i}|position, score, reason codes and observed value, unit, window and snapshot ID. Current items include issue type, review status, version and either caseId or candidateRunId. Historical details retain their recorded evidence and link to item history|
|GET /clients/{c}/items/{i}/observations|ordered observations with snapshot ID, UTC cutoff, source provenance, metric definition, values, units and window bounds. Optional caseId returns follow-up availability and comparable measurements linked to that case's action event|
|POST /clients/{c}/items/{i}/actions|caseId, reviewed run ID, decision, optional note up to 1000 chars and expectedVersion. Idempotency-Key required. 201 event and resulting state, matching replay 200. Conflicting reuse, stale version or invalid transition returns 409|
|PATCH /clients/{c}/items/{i}/status|caseId and reviewed run ID for an existing case, or candidateRunId to start a new case. Requires target status, expectedVersion and Idempotency-Key. 200 updated case ID, status, version and event ID. Conflicting reuse, stale candidate/version or invalid transition returns 409|
|GET /clients/{c}/items/{i}/actions|optional caseId and cursor. Chronological immutable events contain case ID and resulting version, actor, UTC timestamp, event type, reviewed evidence run, prior/new status and decision when applicable|
|GET /clients/{c}/runs/{run}|run ID, status, snapshot ID, input digest, observation cutoff, transform revision, modelId, row counts and start, finish and publication timestamps|
|GET /clients/{c}/models/{modelId}|immutable model ID, artifact SHA-256 and featureSchemaVersion for an accessible run. Registry URI and version can be null for local artifacts|

### Review lifecycle

Review state belongs to a client/item/issue case. V1 uses the `DECLINE_PRIORITY` issue type. The cases for an item form its review history. The effective case for an eligible item in the current queue follows the publication rules in the database design. Analysts use the current queue to start a case and can continue an active case through item history. [Case persistence and cutoff rules](DATABASE_DESIGN.md#review-cases-and-audit)

Read-only historical ranking lists use the latest case opened at or before the requested run's cutoff. An eligible item outside that case's cutoff range displays Open for historical filtering. A cursor retains the run ID and rank position. Analyst updates can change the statuses used by subsequent page requests.

|Status|Meaning|Allowed transitions|
|---|---|---|
|Open (`OPEN`)|An eligible issue awaits triage. The new candidate has version 0 and a candidateRunId until first write|PATCH to `IN_REVIEW`|
|In Review (`IN_REVIEW`)|An analyst is assessing evidence|POST `act`, `defer` or `no_action`|
|Action Taken (`ACTION_TAKEN`)|`act` confirms an action already occurred. The server records the event time and reviewed snapshot|PATCH to `RESOLVED`|
|Resolved (`RESOLVED`)|The analyst has closed the case after an action. Resolution records review completion and leaves measured outcomes to observation data|Terminal|
|Deferred (`DEFERRED`)|`defer` pauses the case pending another review|PATCH to `IN_REVIEW`|
|No Action (`NO_ACTION`)|`no_action` closes the case without an intervention|Terminal|

Example decision body `{"caseId":"case-123","runId":"run-456","decision":"defer","expectedVersion":3,"note":"Recheck next window"}`. POST records an analyst decision and its resulting status in one immutable event. PATCH records a status transition without a decision. Each successful mutation increments the case version. An exact request replay returns the original result even after the version advances. The Spring service derives the actor and validates run, item and case ownership.

### Follow-up availability

Return `AVAILABLE` only when the reviewed baseline cutoff and metric window end are on or before the recorded action time. Require a distinct observation for the same client/item with cutoff strictly after the recorded action and baseline cutoff, and a metric window that starts on or after the recorded action. Require source release/snapshot provenance and compatible metric definitions, units, window lengths and aggregation. Return both cutoffs and window bounds with the values. The comparison reports observed change.

Return `UNAVAILABLE` with `NO_RECORDED_ACTION`, `NO_LATER_OBSERVATION` or `INCOMPARABLE_OBSERVATIONS` when its prerequisite fails. A later snapshot whose metric window starts before the action is incomparable. An item with only the baseline snapshot has no later observation. Unavailable follow-up responses omit comparison values and deltas.
