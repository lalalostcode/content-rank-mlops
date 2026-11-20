# Phase 5 · DASHBOARD

## Iteration 5.1 · Build queue and detail views

- **Objective and scope** — Build queue and detail views.
- **Prerequisite** — Phase 4 exit gate.
- **Tasks** — Build Vite shell, typed API adapter, client picker, overview, filters, cursor list and reason panel. Use the live API to display the published ranking, source cutoff and model/run metadata.
- **Expected files and deliverable** — frontend/src/, frontend/tests/.
- **Verification command** — `cd frontend; npm test` from project root in PowerShell.
- **Automated test and acceptance criterion** — UI fixtures cover loading, errors, empty clients, stale run and keyboard detail navigation.
- **Risk** — Late response renders previous tenant.
- **Definition of done and exit gate** — Record the command result and review evidence against the acceptance criterion before proceeding.

## Iteration 5.2 · Complete review journey

- **Objective and scope** — Complete review journey.
- **Prerequisite** — 5.1, authorized local snapshot and Phase 3 verified learned model bundle.
- **Tasks** — Wire review case actions, status, conflict recovery, history and follow-up availability. Run and record the Product MVP acceptance test below.
- **Expected files and deliverable** — frontend/e2e/, frontend/src/review/.
- **Verification command** — From `frontend/`, run the planned `npm.cmd run test:e2e:mvp` against the local API after publishing a run with the scoring CLI.
- **Automated test and acceptance criterion** — The analyst opens an item from the model-generated queue, records a decision and sees the persisted state and immutable event after reload and API restart.
- **Risk** — Demo mocks hide contract mismatch.
- **Definition of done and exit gate** — Pass the Product MVP end-to-end acceptance test on authorized local data, retaining the run receipt and test evidence. Use synthetic ranking fixtures for development, tests of isolated behavior and the public demo.

## Product MVP end-to-end acceptance test

**Planned test.** Requires Phase 2 feature code, the Phase 3 approved learned bundle and manifest, Phase 4 migrations and publisher, and Phase 5 frontend. Use an authorized local snapshot with at least one client and one reviewable item. Start from a dedicated local test database with no seeded queue or reviews. Store inputs, bundle, outputs and review evidence in approved local paths. Run React in live API mode. [Local bootstrap](../LOCAL_BOOTSTRAP.md)

|Step|Action|Pass evidence|
|---|---|---|
|1|Supply an authorized snapshot manifest and run the local scoring CLI. Run Phase 2 features from the snapshot, validate the model manifest and apply the loaded learned model to the features.|Receipt contains snapshot ID, input checksum, cutoff, model ID, verified SHA-256, feature schema version, transform revision and positive scored count for a client.|
|2|Publish that run to PostgreSQL through the CLI. Read the run, model and first queue page through Spring Boot.|Row order, top item and score match the CLI output for the same run. PostgreSQL's published pointer, run metadata and API IDs agree.|
|3|Select that client in React, inspect the ranked item and evidence, move the Open candidate to In Review and record an Act decision for a review action made during the test.|Browser requests hit the live Spring API and return that run. Queue order and detail match the API. The review write returns the case and immutable decision event IDs.|
|4|Reload the browser and restart the API using the same PostgreSQL database. Reopen the item and its review history.|Case status is Action Taken. The persisted decision appears exactly once with the same ID, actor, timestamp and original ranking context.|
|5|Open follow-up with only the original snapshot available.|The dashboard reports follow-up unavailable and omits a numerical delta. Where comparable later observations are authorized, separately verify the real pair and its cutoffs, measurement windows, units and provenance before showing the delta.|

Planned PowerShell commands. Set `$manifest`, `$modelManifest`, `$bundle` and `$outputDir` to approved local paths and configure PostgreSQL connection variables for the CLI. Copy the target client's run ID from the receipt.

```powershell
uv run --locked python -m pipeline.scoring --manifest $manifest --model-manifest $modelManifest --artifact-dir $bundle --output-dir $outputDir --publish
$env:MVP_RUN_ID = '<published-client-run-id>'
Set-Location frontend
npm.cmd run test:e2e:mvp
```

The Phase 5 browser suite verifies the live workflow and reports the review event ID for the restart check. Record the restart check alongside the suite result. Keep run receipts and any item-level evidence private. Retain a shareable pass or fail summary with code revision and sanitized provenance. Phase 6 services are outside the prerequisites for this test.
