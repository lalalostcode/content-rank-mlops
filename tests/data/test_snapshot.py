import json
from copy import deepcopy

import pytest

from pipeline.ingest.profile import profile_snapshot
from pipeline.ingest.snapshot import load_snapshot
from pipeline.io import ContractError, digest, json_bytes


def test_valid_fixture_and_profile(generated_rows, make_snapshot):
    rows, clients = generated_rows
    path = make_snapshot(rows, clients)
    snapshot = load_snapshot(path)
    profile = profile_snapshot(snapshot)
    assert len(snapshot.rows) == len(rows)
    assert snapshot.clients == tuple(sorted(clients))
    assert profile["input"]["manifest_sha256"] == digest(path.read_bytes())
    assert profile["input"]["cutoff"] == "2025-02-01T00:00:00Z"
    assert profile["by_content_type"]["feedly article"]["fields"]["search_volume"]["missing_fraction"] == 1
    assert profile["zero_position_sentinels"] > 0
    assert "demo-page-" not in json.dumps(profile)


@pytest.mark.parametrize(("changes", "error"), [
    ({"client_id": None}, "client_id"),
    ({"content_id": "as/a/path"}, "content_id"),
    ({"health_score": 0.9}, "forbidden CSV fields"),
    ({"competition": 25}, "competition"),
    ({"ctr": 0.5, "clicks_90d": 10, "impressions_90d": 20}, "CTR percent reconciliation"),
    ({"content_age_days": 90.2}, "content_age_days"),
    ({"content_age_days": None}, "missing content_age_days"),
    ({"days_with_sessions": 91}, "days_with_sessions"),
    ({"word_count": "nan"}, "word_count"),
    ({"content_type": None}, "missing content_type"),
    ({"trend_direction": "future"}, "trend_direction"),
])
def test_invalid_input_rows_are_rejected(generated_rows, make_snapshot, changes, error):
    rows, clients = generated_rows
    path = make_snapshot([{**rows[0], **changes}], clients)
    with pytest.raises(ContractError, match=error):
        load_snapshot(path)


@pytest.mark.parametrize(("changes", "error"), [
    ({"sha256": "0" * 64}, "snapshot SHA-256"),
    ({"row_count": 4}, "row count"),
    ({"cutoff": "2025-02-01T00:00:00"}, "UTC offset"),
    ({"rate_units": {"ctr": "fraction"}}, "rate units"),
    ({"kind": "restricted"}, "requires an approval"),
    ({"client_ids": []}, "declared inventory"),
    ({"dataset": "../snapshot.csv"}, "plain local filename"),
])
def test_manifest_fails_closed(generated_rows, make_snapshot, changes, error):
    rows, clients = generated_rows
    path = make_snapshot(rows[:1], clients, changes=changes)
    with pytest.raises(ContractError, match=error):
        load_snapshot(path)


def test_expired_approval_precedes_input_read(generated_rows, make_snapshot):
    rows, clients = generated_rows
    approval = {"reference": "invented", "purpose": "contract test", "retention_until": "2024-01-01"}
    path = make_snapshot(rows[:1], clients, changes={"kind": "restricted", "approval": approval})
    path.with_name("snapshot.csv").unlink()
    with pytest.raises(ContractError, match="approval has expired"):
        load_snapshot(path)


def test_keys_must_be_unique_within_clients(generated_rows, make_snapshot):
    rows, clients = generated_rows
    path = make_snapshot([rows[0], {**rows[0], "client_id": clients[1]}], clients)
    assert len(load_snapshot(path).rows) == 2
    duplicate = make_snapshot([rows[0], rows[0]], clients)
    with pytest.raises(ContractError, match="duplicate client/content key"):
        load_snapshot(duplicate)


def test_missing_header_fails(generated_rows, make_snapshot):
    rows, clients = generated_rows
    row = deepcopy(rows[0])
    del row["content_id"]
    path = make_snapshot([row], clients)
    with pytest.raises(ContractError, match="missing required CSV fields: content_id"):
        load_snapshot(path)


def test_extra_value_is_rejected_even_with_matching_digest(generated_rows, make_snapshot):
    rows, clients = generated_rows
    path = make_snapshot(rows[:2], clients)
    manifest = json.loads(path.read_bytes())
    data = path.with_name("snapshot.csv")
    payload = data.read_bytes().rstrip(b"\n") + b",extra\n"
    data.write_bytes(payload)
    path.write_bytes(json_bytes({**manifest, "sha256": digest(payload)}))
    with pytest.raises(ContractError, match="malformed CSV|row count"):
        load_snapshot(path)
