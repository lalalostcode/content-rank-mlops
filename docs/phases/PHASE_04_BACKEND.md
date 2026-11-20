# Phase 4 · BACKEND

## Iteration 4.1 · Persist scoped ranking reads

- **Objective and scope** — Persist scoped ranking reads.
- **Prerequisite** — Phase 3 exit gate.
- **Tasks** — Create Spring Maven wrapper, Flyway DDL and JPA repositories. Implement health, clients, overview, queue, details, observations and provenance. Add the local scoring CLI's PostgreSQL publication path using the Flyway schema. Persist score rows, model ID, SHA-256 digest, feature schema version, run ID, snapshot ID, input checksum, cutoff, transform revision, counts, status and timestamps. Advance the current run pointer only after validating a complete client queue. Keep registry references optional until Phase 6.
- **Expected files and deliverable** — backend/pom.xml, backend/src/, backend/mvnw.cmd, backend/.mvn/wrapper/, pipeline/scoring/ and tests/publication/. See the [local bootstrap](../LOCAL_BOOTSTRAP.md).
- **Verification commands** — Run `.\mvnw.cmd verify` in `backend/` and `uv run --locked pytest tests/publication` from the project root with the integration database configured.
- **Automated test and acceptance criterion** — PostgreSQL integration tests apply migrations and deny cross-client reads. A verified artifact scores test input via the local CLI. After publication, API queue order and model/run metadata match the CLI receipt and database rows. Test duplicate runs, rollback and preservation of the last good queue after a failed publish.
- **Risk** — Unstable pagination during publication.
- **Definition of done and exit gate** — Record the command result and review evidence against the acceptance criterion before proceeding.

## Iteration 4.2 · Implement review writes

- **Objective and scope** — Implement review writes.
- **Prerequisite** — 4.1.
- **Tasks** — Add transactional case service, idempotency, version checks, immutable event history, DTO validation, OpenAPI and controller advice. Carry active cases forward and show a fresh Open candidate for a qualifying issue at a strictly newer cutoff after a terminal case. Implement follow-up availability from comparable observations and their provenance.
- **Expected files and deliverable** — backend/src/main/, backend/src/test/.
- **Verification command** — Run `.\mvnw.cmd verify` in `backend/`.
- **Automated test and acceptance criterion** — JUnit/Mockito and PostgreSQL tests cover conflict, rollback, replay, concurrent first writes, immutable history and fresh candidates after terminal cases. Cover single-snapshot follow-up and dated comparison eligibility.
- **Risk** — Concurrent write loses event.
- **Definition of done and exit gate** — Record the command result and review evidence against the acceptance criterion before proceeding.
