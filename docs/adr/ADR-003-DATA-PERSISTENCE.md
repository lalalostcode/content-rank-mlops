# ADR-003 · Postgres for operational state, DuckDB for file transforms

Status: proposed for architecture review.

## Context

Feature engineering works with analytical files. The application needs concurrent review writes, repeatable ranking reads and provenance that connects each publication to its input and model.

## Alternatives

- DuckDB for file transforms and PostgreSQL for application state and published rankings.
- PostgreSQL for both feature preparation and operational persistence.
- DuckDB and flat files as the primary application store.

## Decision and rationale

Use DuckDB for local analytical transforms and PostgreSQL for ranking publication and review persistence. PostgreSQL transactions let readers see one complete published queue and preserve review history under concurrent writes. DuckDB keeps source preparation repeatable outside the application database.

## Consequences

Flyway owns the operational schema. Python gets grants for ingestion and ranking publication. Spring owns review transactions. Publish the model identifier, verified artifact digest, feature schema version and scoring run alongside the scores. The application follows a published run pointer and keeps observation cutoffs and provenance for comparisons. The file-to-database boundary needs validation of lineage, tenant keys and completeness.

## Revisit conditions

Revisit the analytical storage approach if the representative authorized batch exceeds the documented runtime or memory budget after profiling, or if deployment requires concurrent clients to operate on shared analytical inputs.
