# Ownership and deployment

React renders analyst views behind a typed adapter. Spring controllers scope every request to an allowed client, services enforce transitions, JPA repositories persist review transactions. Flyway owns the complete SQL schema. Python has write grants to ingestion and ranking tables only. PostgreSQL is the source for application reads. DuckDB handles bounded analytical transforms on local files. MLflow holds model bundles and lineage. Prefect calls independently testable Python functions.

Local deployment binds the application to loopback. Compose uses a private network, persistent Postgres and MLflow volumes, a migration job before API readiness and a batch profile for workers. Public hosting serves static Vite output and synthetic fixtures. Cloud infrastructure is deferred.
