# Phase 5 · DASHBOARD

## Iteration 5.1 · Build queue and detail views

- **Objective and scope** — Build queue and detail views.
- **Prerequisite** — Phase 4 exit gate.
- **Tasks** — Build Vite shell, typed API adapter, client picker, overview, filters, cursor list and reason panel.
- **Expected files and deliverable** — frontend/src/, frontend/tests/.
- **Verification command** — `cd frontend; npm test` from project root in PowerShell.
- **Automated test and acceptance criterion** — UI fixtures cover loading, errors, empty clients, stale run and keyboard detail navigation.
- **Risk** — Late response renders previous tenant.
- **Definition of done and exit gate** — Record the command result and review evidence against the acceptance criterion before proceeding.

## Iteration 5.2 · Complete review journey

- **Objective and scope** — Complete review journey.
- **Prerequisite** — 5.1.
- **Tasks** — Wire actions, status, conflict recovery, history and dated follow-up. Exercise browser against local Spring and seeded database.
- **Expected files and deliverable** — frontend/e2e/, frontend/src/review/.
- **Verification command** — `cd frontend; npm run test:e2e` from project root in PowerShell.
- **Automated test and acceptance criterion** — One analyst completes FR-01 through FR-08 and sees review history after reload.
- **Risk** — Demo mocks hide contract mismatch.
- **Definition of done and exit gate** — Record the command result and review evidence against the acceptance criterion before proceeding.
