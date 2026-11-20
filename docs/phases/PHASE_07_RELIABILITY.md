# Phase 7 · RELIABILITY

## Iteration 7.1 · Package and observe local stack

- **Objective and scope** — Package and observe local stack.
- **Prerequisite** — Phase 6 exit gate.
- **Tasks** — Build Compose profiles, health checks and structured logs. Measure stage duration, coverage and drift. Add Evidently or Grafana only for a defined operator decision.
- **Expected files and deliverable** — compose.yaml, ops/, tests/ops/.
- **Verification command** — `docker compose config; docker compose up --wait` from project root in PowerShell.
- **Automated test and acceptance criterion** — Clean deployment passes health and smoke checks, failed batch visible by run ID.
- **Risk** — Missing daemon or secrets.
- **Definition of done and exit gate** — Record the command result and review evidence against the acceptance criterion before proceeding.

## Iteration 7.2 · Verify reliability and recovery

- **Objective and scope** — Verify reliability and recovery.
- **Prerequisite** — 7.1.
- **Tasks** — Wire GitHub Actions for backend, Python, UI and synthetic E2E. Restore backup, inject faults, inspect role grants and benchmark NFRs.
- **Expected files and deliverable** — .github/workflows/, tests/recovery/, docs/runbook.md.
- **Verification command** — `uv run pytest tests/recovery` from project root in PowerShell.
- **Automated test and acceptance criterion** — CI and clean-machine runbook reproduce recovery, history integrity and isolation tests.
- **Risk** — CI privileges mask production mistakes.
- **Definition of done and exit gate** — Record the command result and review evidence against the acceptance criterion before proceeding.
