# Phase 3 · MACHINE LEARNING

## Iteration 3.1 · Establish grouped benchmark

- **Objective and scope** — Establish grouped benchmark.
- **Prerequisite** — Phase 2 exit gate.
- **Tasks** — Freeze the client holdout and development splits. Implement the rule and the per-client evaluation protocol below. Hand-check ties, empty and undersized clients, zero positives and folds containing clients with different inventory sizes.
- **Expected files and deliverable** — pipeline/evaluation/, tests/metrics/.
- **Verification command** — `uv run pytest tests/metrics` from project root in PowerShell.
- **Automated test and acceptance criterion** — Hand-calculated P@K and NDCG agree. Test client disjointness, one out-of-fold score per eligible item and a sample where pooled fold P@50 differs from the per-client macro mean.
- **Risk** — Fold pooling inflates performance.
- **Definition of done and exit gate** — Record the command result and review evidence against the acceptance criterion before proceeding.

## Iteration 3.2 · Train and select candidate

- **Objective and scope** — Train and select candidate.
- **Prerequisite** — 3.1.
- **Tasks** — Fit both LambdaRank models and compare the within-client percentile blend. Freeze the learned candidate and final acceptance criteria before opening the holdout. Export the selected model and preprocessing bundle, evaluation report and trusted manifest. Implement a local scoring CLI that uses the Phase 2 feature pipeline, checks the manifest and writes ordered rank rows and an auditable run receipt.
- **Expected files and deliverable** — pipeline/training/, pipeline/scoring/, reports/evaluation.md, tests/training/ and tests/scoring/. Keep real artifacts and row-level outputs in an approved local directory outside Git.
- **Verification command** — `uv run pytest tests/training tests/scoring` from project root in PowerShell.
- **Automated test and acceptance criterion** — With fixed dependencies and input, two invocations produce the same ordered ranks and output digest. A changed artifact digest or incompatible feature schema fails before scoring. Record the final evaluation without further tuning on held-out clients.
- **Risk** — Retuning against final results.
- **Definition of done and exit gate** — Record fresh evaluation evidence, an approved learned candidate and repeatable scores from its verified local bundle. If the learned candidate fails acceptance, keep the rule as a fallback and record the learned model as a Product MVP blocker. Any further selection requires a fresh holdout.

## Evaluation protocol

- **Historical reference.** The capstone took the top 50 items in each of five pooled held-out folds, then averaged those five P@50 values. The reported blend and rule means were 92.4% and 46.4%, respectively. The capstone used a fixed 50/50 blend of the two component percentile ranks across each fold. Results under the platform protocol require fresh validation. Claim reproduction of the historical figure only after running and verifying its original protocol. [Capstone report](https://github.com/lalalostcode/FlyrankAI_ML/blob/main/work/capstone_report.md) · [Fold-percentile implementation](https://github.com/lalalostcode/FlyrankAI_ML/blob/main/work/scripts/advanced_ranking_experiment.py)
- **Splits and eligibility.** Record input checksum, snapshot cutoff, seeds, split and feature revisions. Choose eligible rows and binary observed-decline labels before evaluation. Reserve final clients before development and use five GroupKFold splits on the remaining clients. Fit preprocessing and tuning only in development. Use contiguous per-client LambdaRank query groups. If using the starter snapshot from the capstone, disclose prior exposure to that cohort. The holdout is untouched by new model selection and shares the historical source.
- **Ranking.** On the same eligible items per client, compare the fixed rule, base and engineered LambdaRank and their equal blend. For each component, compute ascending average ranks divided by eligible count within that client, with higher scores assigned higher percentiles. Average both percentiles equally, sort descending and break final ties by stable content ID. Use the same transform in evaluation and batch scoring. Verify that adding a second client leaves the first client's blend scores and order unchanged.
- **Metrics.** At K=10, 25 and 50, compute hits divided by `min(K, eligible count)` on each nonempty client, then give each client equal weight. Compute binary NDCG with the same effective K and a zero score for clients with no positives. Report included, undersized, empty and zero-positive client counts, client-level misses and deltas versus the rule. On development folds aggregate one out-of-fold value per client. Report the final holdout separately with coverage and limitations.
- **Reporting.** Freeze the candidate, rule comparison checks and error-review criteria before scoring the final holdout once. Document observed-decline proxy results as current-snapshot ranking evidence. Label a future authorized temporal backtest as a separate experiment with outcome windows after the feature cutoff.

## Local scoring handoff

The trusted model manifest pins a stable model ID, bundle filename and SHA-256, feature schema version, dependency lock and training provenance. The immutable bundle is a single file containing the trained model, preprocessing and ranking configuration. Verify its bytes against the independently supplied manifest and match the feature schema before loading model contents. The authorized input manifest supplies the snapshot ID, input checksum and cutoff. The run receipt records both manifests' identities, the transform revision, counts, timestamps, status and output digest. The Phase 3 CLI writes a receipt and ranks to a local directory using the Phase 5 invocation with file output only. Phase 4 adds `--publish` for PostgreSQL. Phase 6 wraps the same scorer with Prefect and MLflow Registry. [CLI invocation](PHASE_05_DASHBOARD.md#product-mvp-end-to-end-acceptance-test)
