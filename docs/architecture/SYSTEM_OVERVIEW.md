# Ownership and deployment

React renders analyst views behind a typed adapter. Spring controllers scope every request to an allowed client, services enforce case transitions, and JPA repositories persist review transactions. Flyway owns the complete SQL schema. Python has write grants to ingestion and ranking tables only. PostgreSQL is the source for application reads. DuckDB handles bounded analytical transforms on local files.

Through Phase 5, the operator runs the verified local Python scorer and publisher. The artifact digest and feature schema are checked before scoring. Phase 6 adds MLflow for model bundles and lineage and Prefect for orchestration of the same Python entry points.

Local deployment binds the application to loopback. Phase 4–5 use local PostgreSQL, Flyway and the application processes. Phase 7 Compose uses a private network, persistent Postgres and MLflow volumes, a migration job before API readiness and a batch profile for workers. Public hosting serves static Vite output and synthetic fixtures. Cloud infrastructure is deferred. [Local bootstrap](../LOCAL_BOOTSTRAP.md)
