# Content Ranking MLOps

Local-first editorial decision support. The Python pipeline builds DuckDB features, evaluates client-grouped LambdaRank models and publishes verified batch scores to PostgreSQL. The React dashboard reads rankings and evidence through Spring Boot and saves review actions in PostgreSQL.

Run the [local dashboard setup](docs/LOCAL_BOOTSTRAP.md). The [MVP execution report](docs/reports/MVP_EXECUTION_REPORT.md) records the tested synthetic preview and the FlyRank acceptance requirements.

## Reproduce the synthetic run

Run from the repository root in PowerShell with `uv`. Use a fresh sibling directory for each experiment. The input manifest and trained artifacts stay outside the checkout.

```powershell
uv sync --locked --python 3.13.9
uv run --locked pytest

$cycleRoot = '../cycle-01-local'
$manifest = "$cycleRoot/input/input-manifest.json"
$development = "$cycleRoot/development"
$final = "$cycleRoot/final"
uv run --locked python -m pipeline.synthetic --output-dir "$cycleRoot/input"
uv run --locked python -m pipeline.ingest --manifest $manifest --output-dir "$cycleRoot/profile"
uv run --locked python -m pipeline.features --manifest $manifest --output-dir "$cycleRoot/features"
uv run --locked python -m pipeline.training develop --manifest $manifest --output-dir $development --seed 42
uv run --locked python -m pipeline.training evaluate-final --manifest $manifest --frozen-manifest "$development/frozen-model-manifest.json" --artifact-dir $development --output-dir $final
uv run --locked python -m pipeline.scoring --manifest $manifest --model-manifest "$final/model-manifest.json" --artifact-dir $development --output-dir "$cycleRoot/scoring"
```

`rankings.csv` contains the client ID, content ID, position and score. `run-receipt.json` records version, digest, row count and timing evidence. Supply the scoring manifest from a trusted source independent of the bundle bytes. Supply each client's complete eligible inventory because within-client features and blend ranks depend on it. [Input and feature contracts](docs/data-dictionary.md)

The published engineering evidence uses generated snapshots. Restricted snapshots require a verified cutoff, documented data-owner approval and an approved storage location. [Data governance](docs/governance/DATA_GOVERNANCE.md)

- [Master PRD](docs/prd/MASTER_PRD.md) and [iteration roadmap](docs/roadmap/IMPLEMENTATION_ROADMAP.md)
- [Cycle 1 execution report](docs/reports/CYCLE_01_EXECUTION_REPORT.md), [snapshot quality profile](reports/profile.md) and [model selection report](reports/evaluation.md)
- [Environment audit](docs/phases/PHASE_00_REPOSITORY_AUDIT.md) and [local bootstrap](docs/LOCAL_BOOTSTRAP.md)
- [REST contract](docs/architecture/API_CONTRACT.md) and [OpenAPI specification](docs/architecture/openapi.yaml)
