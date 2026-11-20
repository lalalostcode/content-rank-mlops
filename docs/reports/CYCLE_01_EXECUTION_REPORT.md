# Cycle 1 execution report

20 November 2026 · Local branch `cycle-01`

## Exit decisions

| Phase | Status | Exit evidence |
|---|---|---|
| 2 · Data engineering | **PASS** on synthetic fixtures | Iterations 2.1 and 2.2 passed. The validated fixture produced 996 eligible feature rows. Two builds matched by SHA-256 and tests rejected invalid input, forbidden lineage and overlapping comparison windows. Authorized FlyRank input acceptance remains pending. [Quality profile](../../reports/profile.md) |
| 3 · Machine learning | **PARTIAL** | Iteration 3.1 passed the synthetic grouped benchmark. Iteration 3.2 delivered and verified the bundle, holdout evaluation and scorer on synthetic data. An authorized evaluation cohort and owner approval of a learned release remain open. [Model selection and holdout](../../reports/evaluation.md) |

The Phase 0–1 check found the PRD, data-flow contracts, ADRs and acceptance matrix at baseline `6ac53a9`. The sibling Paul reference was available at `65ae242adf4c00c80a5c151444fc412d205826af`. The adjacent FlyRank capstone and data-use documentation supplied historical protocol and field definitions. The FlyRank data-use sign-off was open, so all data and artifact execution used the independent fixture generator. The Windows Store Python alias failed, and the managed Python 3.13.9 interpreter supplied the locked runtime. [Repository audit](../phases/PHASE_00_REPOSITORY_AUDIT.md) · [PRD review decisions](../PRD_REVIEW_CHANGELOG.md)

## Requirements and evidence

| Iteration | Requirement | Evidence |
|---|---|---|
| 2.1 | Reproducible ingestion, provenance and data contracts | The parser verifies the CSV SHA-256 and types the verified input in DuckDB. `test_valid_fixture_and_profile` checks manifest lineage. Invalid-key, duplicate, row-width, wrong-unit, wrong-digest, missing-cutoff and approval tests reject input before output. [Snapshot tests](../../tests/data/test_snapshot.py) |
| 2.1 | Quality and missingness profile | `pipeline.ingest` produced local `profile/profile.json` with field counts, ranges and missingness by content type for 997 rows. The Markdown profile records the systematic keyword-field gap and position sentinel counts. [Quality profile](../../reports/profile.md) |
| 2.2 | Versioned feature schema and deterministic DuckDB SQL | `rank-features-v1` specifies 26 base and 17 additional features. `features-a` and `features-b` matched by independent SHA-256. The receipts record input, schema and transform digests. [Schema](../../pipeline/features/feature-schema-v1.json) · [SQL](../../pipeline/features/snapshot-v1.sql) |
| 2.2 | Leakage prevention | Tests vary target and comparison values without changing features, reject forbidden source fields even behind aliases, reject a shifted comparison window, and verify client-local context and all-null categories. [Feature tests](../../tests/features/test_features.py) |
| 3.1 | Transparent rule, correct metrics and client isolation | Hand calculations cover ties, effective K, NDCG, empty and zero-positive clients, and a pooled precision example that differs from the client macro mean. Split tests prove five groups of validation clients, holdout disjointness and exactly one out-of-fold score per eligible development item. [Metric and split tests](../../tests/metrics/) |
| 3.2 | Both LambdaRank models, equal client-percentile blend and reproducible development | The development CLI compared four methods. Tests verify contiguous queries, training-only vocabularies and byte-identical training replay. Removing final labels leaves the development scores, candidate and model text identical. [Training tests](../../tests/training/test_training.py) · [Development metrics](../../reports/evaluation.md#development-and-selection) |
| 3.2 | Frozen candidate, separate holdout and per-client metrics | The final CLI checked the frozen input and split, then evaluated the engineered candidate and rule. The local JSON reports contain per-client P@10, P@25, P@50, binary NDCG, misses and deltas. A regression test confirms the fallback decision. [Final metrics](../../reports/evaluation.md#final-holdout) |
| 3.2 | Reloadable bundle, trusted SHA-256 manifest and deterministic scoring | The scoring CLI loaded two verified LightGBM models with saved preprocessing, schema and ranking settings. Tests rejected a tampered bundle, incompatible feature schema, lock mismatch, mixed input scopes and expired training provenance. Two CLI runs yielded byte-identical ranks. A failed verification emits a failed receipt without ranks. [Scoring tests](../../tests/scoring/test_scoring.py) |
| 3.2 | Approved model release and real-data evidence | Pending data-owner authorization and ML-owner review. The verified manifest is scoped to synthetic scoring. [Data governance](../governance/DATA_GOVERNANCE.md) · [Acceptance matrix](../roadmap/PHASE_ACCEPTANCE_MATRIX.md) |

## Evaluation and artifact verification

The snapshot cutoff was `2025-02-01T00:00:00Z`, the fixture seed was `20261120` and the split and model seed was `42`. Development used five client-grouped folds over 816 eligible items across 12 included clients. The holdout contained 180 items across four clients, one of which had zero positives. The frozen gate required higher macro P@50 than the rule, both label values and no individual P@50 regression above 10 percentage points. Engineered LambdaRank had the highest qualifying development P@50 (62.70% versus 43.70%) and scored 44.00% versus 37.00% on the separate final group. Each holdout client matched or exceeded the rule at P@50. The earlier 92.4% capstone number was a historical pooled fold-level metric. [All macro metrics and protocol](../../reports/evaluation.md)

Local evidence is in the sibling directory `../cycle-01-evidence/synthetic/`. `input/`, `profile/` and `features-a/` contain the fixture, profile and feature receipt. `development-a/` and `development-b/` hold the repeat development outputs. `final/` holds the separate final report and the trusted scoring manifest. `scoring-a/` and `scoring-b/` each contain `rankings.csv` and `run-receipt.json`.

| Evidence | Verified SHA-256 |
|---|---|
| Feature CSV, both runs | `314a59fdb49e007d965c5f27019331fb83552f5d1190c9046ee1f0ab931964ec` |
| Feature schema | `1b2c948517a705c1430468962a887ad6be6fe97a5ddc46230d69f78182c3959e` |
| DuckDB SQL transform | `0cebae645f0743aa1df0c7a58846e91fcbf76ba7bab2895a4079bc50ec20fa67` |
| Development split, both runs | `926b409aecb63615fa49237156cd24e3ba9ce8af2016cbae114e557bbca5087e` |
| Development report, both runs | `9fe6418746bbde54c222254c80d828c559a37df8b14d8d56f08d1a72e5d92cc2` |
| Trained bundle, both runs | `9cb933fed08e51046022cefc00a029478e6fd74af74d8a7869fc231f072d4c5e` |
| Frozen candidate manifest, both runs | `25f2f552d75d5f34efb2cace08cedab576140cdb2005b2089dcda11916afd7cf` |
| Final evaluation | `41fbb0c411d1e3ffcd0b5709c20d7b86f25a5c325ef4107c2817ede6e10116fa` |
| Final model manifest | `e2b6308203a593b5741fdcdb11e39e418f0ffb7642089b77357a0874c0021d19` |
| Dependency lock | `44d8da162c977cff02f30f56986b6465b9368e7f8e9748ce9bf4ed42e3f6bcf9` |
| Ranking CSV, both runs | `79e4e0a026dd554a0e58065a6ae84d7a5189c2093a0bd277d494b735a86e5395` |

Both receipts report 996 ordered rows, 16 scored clients, two empty queues and the same run ID `f6cee4cdbfb147a51a57b56314f3aa4c84fd3f9ed370bb1c342604ead3d39f70`. Receipt durations were 0.174 s and 0.181 s within the CLI process. Receipt timestamps reflect each attempt. Independent `Get-FileHash` checks agreed with the expected bundle, final report and rank digests.

## Commands and test results

These are the successful verification commands, shown from the repository root. Network access for `uv lock` and `uv sync` used the approved network-enabled shell. The resulting local environment and cache supported offline tests.

```powershell
git status --short --branch
git ls-files docs/architecture
git -C ../paul-reference rev-parse HEAD
git switch -c cycle-01
$pipelinePython = uv --no-cache python find --managed-python 3.13
& $pipelinePython --version
$env:UV_CACHE_DIR = '../.cycle1-uv-cache'
uv lock --quiet --python $pipelinePython --no-progress
uv sync --locked --python $pipelinePython --no-progress

$cycleEvidence = '../cycle-01-evidence/synthetic'
$snapshot = "$cycleEvidence/input/input-manifest.json"
$development = "$cycleEvidence/development-a"
$modelManifest = "$cycleEvidence/final/model-manifest.json"
uv run --locked --offline python -m pipeline.synthetic --output-dir "$cycleEvidence/input"
uv run --locked --offline python -m pipeline.ingest --manifest $snapshot --output-dir "$cycleEvidence/profile"
uv run --locked --offline python -m pipeline.features --manifest $snapshot --output-dir "$cycleEvidence/features-a"
uv run --locked --offline python -m pipeline.features --manifest $snapshot --output-dir "$cycleEvidence/features-b"
uv run --locked --offline python -m pipeline.training develop --manifest $snapshot --output-dir $development --seed 42
uv run --locked --offline python -m pipeline.training develop --manifest $snapshot --output-dir "$cycleEvidence/development-b" --seed 42
uv run --locked --offline python -m pipeline.training evaluate-final --manifest $snapshot --frozen-manifest "$development/frozen-model-manifest.json" --artifact-dir $development --output-dir "$cycleEvidence/final"
uv run --locked --offline python -m pipeline.scoring --manifest $snapshot --model-manifest $modelManifest --artifact-dir $development --output-dir "$cycleEvidence/scoring-a"
uv run --locked --offline python -m pipeline.scoring --manifest $snapshot --model-manifest $modelManifest --artifact-dir $development --output-dir "$cycleEvidence/scoring-b"
uv run --locked --offline pytest tests/data tests/features -q --tb=short
uv run --locked --offline pytest tests/metrics -q --tb=short
uv run --locked --offline pytest tests/training tests/scoring -q --tb=short
uv run --locked --offline pytest -q --tb=short
git diff --check
```

| Test scope | Result |
|---|---|
| Snapshot contracts and features | 35 passed |
| Metrics and splits | 14 passed |
| Training and scoring | 17 passed |
| Full locked suite | **66 passed** in 29.63 s on Windows |

The initial restricted-shell dependency resolution failed at PyPI DNS. Approved installation recovered it. The first ingestion tests exposed the DuckDB file-like CSV dependency, so the pipeline now parses verified UTF-8 CSV bytes and uses DuckDB for typed validation. A single-row feature test exposed all-null category dtype inference, which is covered by the explicit string typing and empty-snapshot test. A metric test caught rounding across mathematically tied blend scores, which now share one division and sort by content ID. Git initially ignored `tests/data/`. The source-directory exception preserves the CSV ignore rule. Every corrected suite was rerun.

## Commits and files

| Commit | Files |
|---|---|
| `7d8faf88e852608ef49dd2a0d63f0ec055966db0` | `.gitignore`, `.python-version`, `pyproject.toml`, `uv.lock`, `pipeline/__init__.py`, `pipeline/io.py`, `pipeline/synthetic.py`, `pipeline/ingest/`, `pipeline/features/`, `tests/conftest.py`, `tests/data/`, `tests/features/`, `docs/data-dictionary.md`, `reports/profile.md` |
| `fa98c89808da7b1c8f2f03c57f272f34fcbca9f6` | `.gitignore`, `pyproject.toml`, `uv.lock`, `pipeline/io.py`, `pipeline/ingest/snapshot.py`, `pipeline/evaluation/`, `pipeline/training/`, `pipeline/model_bundle.py`, `pipeline/ranker.py`, `pipeline/scoring/`, `tests/conftest.py`, `tests/metrics/`, `tests/training/`, `tests/scoring/` |
| Evidence report commit | `README.md`, `reports/evaluation.md`, `docs/reports/CYCLE_01_EXECUTION_REPORT.md`. Git identifies this commit with `git log -1 -- docs/reports/CYCLE_01_EXECUTION_REPORT.md`. |

The branch contains implementation, tests and aggregate synthetic evidence. Raw fixture CSVs, manifests, trained models and item outputs are stored outside the checkout. The approved data owner still needs to provide the usable release, terms, cutoff and retention for a restricted run.

## Readiness and owner review

The local rank and receipt contracts are ready for integration review. Product MVP acceptance remains blocked on the authorized snapshot, a reviewed learned model and the Phase 4–5 end-to-end test. The previously documented Docker Engine and Maven wrapper work belongs to the later integration cycle. [Dependency map](../roadmap/DEPENDENCY_MAP.md) · [Local bootstrap](../LOCAL_BOOTSTRAP.md)

The real release schema and its rounding conventions remain unverified. The CLI materializes one CSV snapshot in memory. Runtime and peak memory at the 30,000-row target, cross-platform byte equality, and temporal performance remain unmeasured. DuckDB lineage guards enforce the declared source boundary. A real-cohort review still needs to examine whether contemporaneous aggregates act as proxies for the observed label. Four synthetic holdout clients provide limited coverage. [Quality budgets](../prd/NON_FUNCTIONAL_REQUIREMENTS.md)

1. Review the two phase decisions and verify the local manifest and receipt digests above.
2. Obtain data-owner approval, prepare a private manifest and confirm the real source field mappings and windows. Agree on the model acceptance and client-regression thresholds before opening the approved holdout.
3. Run Cycle 1 against the approved release, document any exposure to the historical cohort, and review per-client misses and regressions. Keep a fresh holdout for any subsequent selection.
4. Authorize Cycle 2 separately after reviewing the exit evidence. Cycle 1 ends at Phase 3.
