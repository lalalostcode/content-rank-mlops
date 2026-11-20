# Phase 3 · MACHINE LEARNING

## Iteration 3.1 · Establish grouped benchmark

- **Objective and scope** — Establish grouped benchmark.
- **Prerequisite** — Phase 2 exit gate.
- **Tasks** — Freeze split manifest. Implement transparent rule, metrics and small-client policy. Hand-check ties, empty clients and zero positives.
- **Expected files and deliverable** — pipeline/evaluation/, tests/metrics/.
- **Verification command** — `uv run pytest tests/metrics` from project root in PowerShell.
- **Automated test and acceptance criterion** — Hand-calculated P@K and NDCG agree and clients never cross splits.
- **Risk** — Fold pooling inflates performance.
- **Definition of done and exit gate** — Record the command result and review evidence against the acceptance criterion before proceeding.

## Iteration 3.2 · Train and select candidate

- **Objective and scope** — Train and select candidate.
- **Prerequisite** — 3.1.
- **Tasks** — Fit base and engineered LambdaRank, compare equal-rank blend, log per-client misses, freeze candidate and evaluate once. Export bundle and evaluation report.
- **Expected files and deliverable** — pipeline/training/, reports/evaluation.md, tests/training/.
- **Verification command** — `uv run pytest tests/training` from project root in PowerShell.
- **Automated test and acceptance criterion** — Replay reproduces rankings and records holdout decision including rule fallback.
- **Risk** — Retuning against final results.
- **Definition of done and exit gate** — Record the command result and review evidence against the acceptance criterion before proceeding.
