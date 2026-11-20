# ADR-004 · Introduce Prefect after a repeatable CLI

Status: proposed for architecture review.

## Context

The Product MVP needs repeatable scoring and trustworthy model lineage before the team takes on a scheduler, worker and registry. Scheduled operations later need bounded retries and visibility into failed runs.

## Alternatives

- Keep a version-pinned CLI through Phase 5 and add Prefect and MLflow Registry in Phase 6.
- Provision Prefect and MLflow Registry before the first model-generated publication.
- Use a manually invoked CLI as the long-term operational workflow.

## Decision and rationale

Start with a repeatable local CLI that validates the input manifest, immutable model artifact and feature contract and records publication metadata. Phase 6 adds MLflow Registry for model versions and Prefect for scheduling, retry policy and run visibility. The flow uses the same tested scorer and publication path. This ordering lets the team validate deterministic scoring and idempotence before introducing orchestration.

## Consequences

An operator invokes the CLI manually through Phase 5. Phase 6 adds worker and registry availability as operational dependencies. Resolve any registry alias once when preparing a run, verify the resulting immutable artifact and record the concrete version and digest with the run. Verify that automated and manual invocations preserve the same transactional guarantees.

## Revisit conditions

Reopen the sequencing decision if an agreed day-one production requirement needs unattended retries or controlled model promotion before the application can ship. Review worker topology when measured job concurrency or deployment requirements exceed the local worker's capacity.
