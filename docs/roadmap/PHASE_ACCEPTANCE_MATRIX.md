# Phase acceptance matrix

|Phase|Exit evidence required|Evidence location|
|---|---|---|
|0|Pinned source revision and tool probes recorded.|docs/architecture/REFERENCE_ARCHITECTURE_AUDIT.md|
|1|Reviewer accepts ownership, data access and evaluation protocol.|docs/architecture/, docs/adr/|
|2|Two runs match digests. Forbidden fields and overlapping time windows fail tests.|pipeline/features/, tests/features/, docs/data-dictionary.md|
|3|Replay reproduces rankings and records holdout decision including rule fallback.|pipeline/training/, reports/evaluation.md, tests/training/|
|4|JUnit/Mockito and PostgreSQL tests cover conflict, rollback, replay and immutable history.|backend/src/main/, backend/src/test/|
|5|One analyst completes FR-01 through FR-08 and sees review history after reload.|frontend/e2e/, frontend/src/review/|
|6|Crash, retry and concurrent publish preserve one complete current queue.|pipeline/flows/, tests/publication/|
|7|CI and clean-machine runbook reproduce recovery, history integrity and isolation tests.| .github/workflows/, tests/recovery/, docs/runbook.md|
|8|New developer reproduces setup and visitor completes published demo without credentials.|README.md, docs/handoff/, frontend/e2e/|
