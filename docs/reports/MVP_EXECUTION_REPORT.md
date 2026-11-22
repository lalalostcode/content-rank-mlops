# Content Ranking MLOps execution report

**22 November 2026.** The local dashboard runs a learned ranking queue and persists analyst reviews through Spring Boot and PostgreSQL. The verified preview uses a synthetic snapshot. FlyRank data acceptance remains pending.

## Repository and phase status

The [canonical repository](https://github.com/lalalostcode/content-rank-mlops) branch is `feat/content-ranking-mvp`, based on `main` at `53358f9d11c596e5f520892a33bcd1912c1bc79c`. The tested implementation revision is `608e5d85da08ad053484f5fc7d7fd3c46931d41e`.

[Draft pull request #2](https://github.com/lalalostcode/content-rank-mlops/pull/2) targets `main` and awaits owner review.

| Phase | Status | Verification or remaining gate |
|---|---|---|
| 2 · Data engineering | PARTIAL | The starter file matches its documented 30,000 rows, 44 columns and 32 pseudonymized clients. The CSV checksum and source references are recorded in the ignored local manifest. Ingestion and deterministic features pass with synthetic inputs. The exact FlyRank source cutoff and release approval remain open. |
| 3 · Machine learning | PARTIAL | Client-grouped development and frozen synthetic holdout evaluation selected the engineered LambdaRank model. The verified bundle reproduced the same rankings in independent scoring runs. FlyRank cohort evaluation and its learned release decision remain open. |
| 4 · Backend | PASS | Flyway and Spring started against PostgreSQL 16.13. The CLI published complete learned queues. Replay reused the run, and a stale batch rolled back without changing the current queue. Review changes, idempotency and concurrency passed integration tests. |
| 5 · Dashboard | PARTIAL | The live browser opened a model-ranked queue, displayed evidence, recorded a review and recovered the same history after a browser reload. The earlier browser review survived a Spring and PostgreSQL restart. The authorized FlyRank Product MVP test remains pending. |

| Implementation revision | Scope |
|---|---|
| `3d120b95ce6aa1acbe76f3d8cb19885cf08933bd` | Inherited Cycle 1 data validation, scoring receipts and benchmark fixture |
| `1096b07ca0a3faf680ae2f9c76611a8235aace3a` | Explicit rejection of pending or undated inputs before CSV ingestion |
| `cdfdfda503494ea33dc7930eae466507f7df8ffb` | Atomic PostgreSQL publication, Flyway, Spring API, JPA reviews and database tests |
| `608e5d85da08ad053484f5fc7d7fd3c46931d41e` | React dashboard, live browser verification, and search contract |

## Data, model and publication evidence

The original FlyRank starter stays in the internship checkout. The pending local manifest is `data/manifests/flyrank-starter.pending.json`. It records the actual local SHA-256, source release, schema and unknown cutoff. The documented trailing 90-day period is relative to export time. Date-dependent ingestion requires an authoritative cutoff and observation bounds, plus the release approval reference and retention terms. [Input manifest contract](../data-dictionary.md#input-manifest) · [Data governance](../governance/DATA_GOVERNANCE.md)

The verified synthetic snapshot contained 997 rows and the published run scored 996 eligible items across 16 clients. PostgreSQL stored 18 client queues including two empty ones. The frozen holdout had 180 items across four clients. Metrics below average clients equally. The internship's historical 92.4% P@50 averaged held-out folds and remains a separate result. [Evaluation protocol](../phases/PHASE_03_MACHINE_LEARNING.md#evaluation-protocol) · [Cycle 1 execution report](CYCLE_01_EXECUTION_REPORT.md)

| Method | P@10 | P@25 | P@50 | NDCG@10 | NDCG@25 | NDCG@50 |
|---|---:|---:|---:|---:|---:|---:|
| Engineered LambdaRank | 0.7500 | 0.6500 | 0.4400 | 0.7500 | 0.7097 | 0.7401 |
| Fixed rule | 0.2750 | 0.4000 | 0.3700 | 0.2978 | 0.3986 | 0.5239 |

| Verified artifact | Value |
|---|---|
| Model bundle SHA-256 | `ef2c63a230bc22e74068d036ac45e1bcac85afa45e7418d2027353abd9c37e86` |
| Feature schema | `rank-features-v1` |
| Published run ID | `bb00d92f527f9496463fb8ece314d52fd1749efbed71a4686e03e2f61bcbae68` |
| Ranking CSV SHA-256, both runs | `79e4e0a026dd554a0e58065a6ae84d7a5189c2093a0bd277d494b735a86e5395` |
| Publish and replay | 18 queues published, then 18 replayed and zero new publications |
| Spring API | Readiness `UP`. All 65 rows for the verified client matched the scoring CSV by identity, order and score. The REST model digest and run input digest matched the scoring receipt. |
| Persisted browser review | Event `5970b062-17ef-49ff-8111-503d96a4eaf2` returned exactly once after restart, with status `ACTION_TAKEN`. Follow-up returned `UNAVAILABLE` with reason `NO_LATER_OBSERVATION`. |

The browser screenshot and verified run receipts are in the local `../cycle-01-evidence/mvp-runtime/` directory. The screenshot is `dashboard-verified.png`. Tests and artifacts show engineering behavior on generated observations. Evaluation against actual future outcomes is a separate experiment.

## Tests and requirement traceability

| Command | Actual result |
|---|---|
| `uv run --locked --offline pytest -q --tb=short` with `RUN_POSTGRES_INTEGRATION=1` | 72 passed, including pending manifest rejection, grouped evaluation, reproducible scoring, publication replay and transaction rollback |
| `./mvnw.cmd --offline --batch-mode --no-transfer-progress verify` with `RANKING_TEST_DATABASE=true` and the local Maven cache | 7 passed, zero skipped. Flyway migration validated and the executable JAR built. |
| `npm.cmd run build` | TypeScript and Vite build passed |
| `npm.cmd run test` | 3 Playwright component tests passed, covering loading, empty data, error recovery, keyboard navigation and search |
| `npm.cmd run test:e2e:mvp` with the published run ID on the live dashboard | 1 passed. Verified ordering, evidence, review entry, unavailable follow-up and a single saved note after reload. |

| Requirements | Evidence |
|---|---|
| FR-01 to FR-04 · Client, snapshot, queue and evidence | Synthetic dashboard, run-pinned pagination test, CSV-to-API comparison and keyboard detail test |
| FR-05 to FR-08 · Review, state, history and follow-up | PostgreSQL integration tests for replay, stale conflicts, concurrent review starts and immutable events. Browser reload and server restart recovered the saved action. |
| FR-09 and FR-10 · Batch and provenance | Verified local bundle, repeated publication, rollback test, and matching run/model metadata at the API |
| FR-11 · Static public demo | Phase 8 deliverable |

## Local startup and known limits

Use the [local bootstrap](../LOCAL_BOOTSTRAP.md) for PostgreSQL role creation and the [synthetic commands](../../README.md#reproduce-the-synthetic-run) to generate a snapshot and train the bundle. Use fresh output directories for every CLI run. The test host used native PostgreSQL 16.13 on port 55432 because Docker Engine was unavailable. Configure the backend with `SPRING_DATASOURCE_URL=jdbc:postgresql://127.0.0.1:55432/content_ranking`, set the application and Flyway credentials as described in the bootstrap, then run the following from `backend`.

```powershell
$env:SERVER_PORT = '58080'
$env:SPRING_DATASOURCE_HIKARI_MAXIMUM_POOL_SIZE = '4'
.\mvnw.cmd spring-boot:run
```

Starting Spring before crash recovery finished initially failed with PostgreSQL's startup response. Wait for a SQL readiness check to pass before starting Spring. The recovered cluster and restarted API retained the existing review data.

For scoring, use the `PG*` environment variables from the bootstrap with `PGPORT=55432`. From the repository root, publish the local verified bundle using the paths from the synthetic run.

```powershell
uv run --locked python -m pipeline.scoring --manifest $manifest --model-manifest "$final/model-manifest.json" --artifact-dir $development --output-dir "$cycleRoot/published" --publish
```

From `frontend`, install the locked packages and start the live API proxy.

```powershell
$env:DASHBOARD_API_TARGET = 'http://127.0.0.1:58080'
npm.cmd ci
npm.cmd run dev
```

Open [the local dashboard](http://127.0.0.1:5173/?client=demo-client-04). Vite, Spring and PostgreSQL listen on loopback. The [OpenAPI specification](../architecture/openapi.yaml) documents the REST interface.

The next acceptance run needs the verified FlyRank cutoff, source approval and retention terms. Evaluate a learned release on that cohort and repeat the publication, API, browser and persistence checks. After Product MVP acceptance, Phase 6 can register the immutable model in MLflow and schedule the same verified CLI through Prefect. [Phase 5 acceptance](../phases/PHASE_05_DASHBOARD.md#product-mvp-end-to-end-acceptance-test) · [Phase 6 scope](../phases/PHASE_06_MLOPS.md)
