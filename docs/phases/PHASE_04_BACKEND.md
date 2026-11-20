# Phase 4 · BACKEND

## Iteration 4.1 · Persist scoped ranking reads

- **Objective and scope** — Persist scoped ranking reads.
- **Prerequisite** — Phase 3 exit gate.
- **Tasks** — Create Spring Maven wrapper, Flyway DDL and JPA repositories. Implement health, clients, overview, queue, details, observations and provenance. Load synthetic run fixture.
- **Expected files and deliverable** — backend/pom.xml, backend/src/, backend/mvnw.cmd.
- **Verification command** — `cd backend; ./mvnw.cmd verify` from project root in PowerShell.
- **Automated test and acceptance criterion** — PostgreSQL integration tests apply migrations and deny cross-client reads.
- **Risk** — Unstable pagination during publication.
- **Definition of done and exit gate** — Record the command result and review evidence against the acceptance criterion before proceeding.

## Iteration 4.2 · Implement review writes

- **Objective and scope** — Implement review writes.
- **Prerequisite** — 4.1.
- **Tasks** — Add transactional service, idempotency, version checks, event history, DTO validation, OpenAPI and controller advice.
- **Expected files and deliverable** — backend/src/main/, backend/src/test/.
- **Verification command** — `cd backend; ./mvnw.cmd verify` from project root in PowerShell.
- **Automated test and acceptance criterion** — JUnit/Mockito and PostgreSQL tests cover conflict, rollback, replay and immutable history.
- **Risk** — Concurrent write loses event.
- **Definition of done and exit gate** — Record the command result and review evidence against the acceptance criterion before proceeding.
