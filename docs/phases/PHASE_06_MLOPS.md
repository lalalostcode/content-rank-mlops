# Phase 6 · MLOPS

## Iteration 6.1 · Track and promote models

- **Objective and scope** — Track and promote models.
- **Prerequisite** — Phase 5 exit gate.
- **Tasks** — Wrap training CLI with MLflow logging and Optuna grouped development search. Evaluate promotion policy and register immutable version.
- **Expected files and deliverable** — pipeline/experiments/, tests/registry/.
- **Verification command** — `uv run pytest tests/registry` from project root in PowerShell.
- **Automated test and acceptance criterion** — Artifact reload reproduces predictions and failed gate leaves prior champion.
- **Risk** — Registry alias changes during run.
- **Definition of done and exit gate** — Record the command result and review evidence against the acceptance criterion before proceeding.

## Iteration 6.2 · Automate atomic batch publication

- **Objective and scope** — Automate atomic batch publication.
- **Prerequisite** — 6.1.
- **Tasks** — Compose Prefect ingestion/scoring tasks, stage rows, check counts and advance published pointer transactionally. Exercise manual trigger, schedule, retries and older run completion.
- **Expected files and deliverable** — pipeline/flows/, tests/publication/.
- **Verification command** — `uv run pytest tests/publication` from project root in PowerShell.
- **Automated test and acceptance criterion** — Crash, retry and concurrent publish preserve one complete current queue.
- **Risk** — Older run supersedes fresh results.
- **Definition of done and exit gate** — Record the command result and review evidence against the acceptance criterion before proceeding.
