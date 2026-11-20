# ADR-003 · Postgres for operational state, DuckDB for file transforms

Status: proposed for architecture review.

Transactional publication and review concurrency require shared state. Separate analytical files add a lineage boundary tracked by digest.

Revisit if the deployment audience, batch cadence or data access conditions change.
