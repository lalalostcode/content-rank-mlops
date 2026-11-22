import os
from uuid import uuid4

import pandas as pd
import psycopg
import pytest

from pipeline.ingest.snapshot import Snapshot
from pipeline.io import ContractError, digest
from pipeline.scoring.publication import publish_rankings


pytestmark = pytest.mark.skipif(
    os.environ.get("RUN_POSTGRES_INTEGRATION") != "1",
    reason="requires a disposable Flyway-migrated PostgreSQL database configured via PG variables",
)


def batch(clients, *, snapshot_id, manifest, cutoff):
    manifest_sha = digest(manifest.encode())
    identity = {
        "snapshot_id": snapshot_id, "source_release": "publication-test", "cutoff": cutoff,
        "manifest_sha256": manifest_sha,
        "windows": {"snapshot_90d": {"start": "2024-11-01T00:00:00Z", "end": cutoff}},
    }
    ranking = pd.DataFrame({
        "client_id": clients, "content_id": ["one"] * len(clients),
        "position": [1] * len(clients), "score": [0.25] * len(clients),
    })
    rows = ranking[["client_id", "content_id"]].assign(impressions_90d=1000)
    artifact = digest(b"publication-test-model")
    receipt = {
        "input": identity, "run_id": manifest_sha, "started_at": "2026-11-20T00:00:00Z",
        "features": {"transform_sha256": digest(b"test-sql"), "feature_schema_version": "rank-features-v1"},
        "model": {"model_id": f"lambdarank-{artifact}", "bundle_sha256": artifact},
    }
    return Snapshot(identity, rows, tuple(clients)), ranking, receipt


def test_idempotent_publication_and_full_batch_rollback():
    prefix = f"pg-test-{uuid4().hex}"
    first, last = f"{prefix}-a", f"{prefix}-z"
    previous = batch([last], snapshot_id="current", manifest=prefix, cutoff="2025-02-01T00:00:00Z")
    assert publish_rankings(*previous) == {"published_clients": 1, "replayed_clients": 0}
    assert publish_rankings(*previous) == {"published_clients": 0, "replayed_clients": 1}

    # The transaction stages this batch for first before discovering the stale cutoff for last.
    stale = batch([first, last], snapshot_id="stale", manifest=f"{prefix}-stale", cutoff="2025-01-31T00:00:00Z")
    with pytest.raises(ContractError, match="newer observation cutoff"):
        publish_rankings(*stale)

    with psycopg.connect() as connection:
        assert connection.execute("SELECT 1 FROM client WHERE id = %s", (first,)).fetchone() is None
        assert connection.execute("SELECT published_run_id FROM client WHERE id = %s", (last,)).fetchone() == (
            previous[2]["run_id"],
        )
        assert connection.execute(
            "SELECT count(*) FROM rank_item WHERE client_id = %s AND run_id = %s",
            (last, previous[2]["run_id"]),
        ).fetchone() == (1,)
