# Phase acceptance matrix

These rows specify required evidence for future exit decisions. Phase 5 acceptance is pending.

|Phase|Exit evidence required|Evidence location|
|---|---|---|
|0|Pinned source revision and tool probes recorded.|docs/architecture/REFERENCE_ARCHITECTURE_AUDIT.md|
|1|Reviewer accepts ownership, data access and evaluation protocol.|docs/architecture/, docs/adr/|
|2|Two runs match digests. Forbidden fields and overlapping time windows fail tests.|pipeline/features/, tests/features/, docs/data-dictionary.md|
|3|Fresh per-client evaluation records the holdout decision and approved learned candidate. The local CLI verifies the immutable artifact digest and feature schema and reproduces ordered ranks.|pipeline/scoring/, reports/evaluation.md, tests/scoring/|
|4|The CLI publishes scored rows and provenance to PostgreSQL. Spring returns the same run, metadata and rank order. Integration tests cover rollback, replay, review case conflicts and immutable history.|backend/src/test/, pipeline/scoring/, tests/publication/|
|5|The authorized snapshot passes feature engineering, trained-model batch scoring, PostgreSQL publication, live Spring REST reads, React rendering and persistent analyst review. Browser reload and API restart preserve history. With one snapshot, follow-up is unavailable.|[Product MVP test](../phases/PHASE_05_DASHBOARD.md#product-mvp-end-to-end-acceptance-test), private run receipt and test report|
|6|MLflow registers and resolves an immutable model version. Prefect orchestrates the local scoring path. Crash, retry and concurrent publish preserve one complete current queue.|pipeline/flows/, tests/registry/, tests/publication/|
|7|CI and clean-machine runbook reproduce recovery, history integrity and isolation tests.| .github/workflows/, tests/recovery/, docs/runbook.md|
|8|New developer reproduces setup and visitor completes published demo without credentials.|README.md, docs/handoff/, frontend/e2e/|
