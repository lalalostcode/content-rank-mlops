# Phase 8 · PUBLIC DEMO

## Iteration 8.1 · Build synthetic demo adapter

- **Objective and scope** — Build synthetic demo adapter.
- **Prerequisite** — Phase 7 exit gate.
- **Tasks** — Generate invented clients and observations, implement memory-only actions, label simulated data and run shared adapter tests. Inspect bundle and network trace.
- **Expected files and deliverable** — frontend/src/demo/, frontend/tests/demo/.
- **Verification command** — `cd frontend; npm run build; npm run test:demo` from project root in PowerShell.
- **Automated test and acceptance criterion** — Built static journey runs with zero backend requests and resets on reload.
- **Risk** — Restricted identifiers embedded in fixture.
- **Definition of done and exit gate** — Record the command result and review evidence against the acceptance criterion before proceeding.

## Iteration 8.2 · Prepare public handoff

- **Objective and scope** — Prepare public handoff.
- **Prerequisite** — 8.1.
- **Tasks** — Review tracked files, license scopes and artifacts. Publish reviewed static build and public repo, verify links, screenshots, walkthrough, API docs, limitations and setup from clean clone.
- **Expected files and deliverable** — README.md, docs/handoff/, frontend/e2e/.
- **Verification command** — `cd frontend; npm run test:e2e` from project root in PowerShell.
- **Automated test and acceptance criterion** — New developer reproduces setup and visitor completes published demo without credentials.
- **Risk** — Public release includes private history.
- **Definition of done and exit gate** — Record the command result and review evidence against the acceptance criterion before proceeding.
