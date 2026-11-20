from copy import deepcopy

import pandas as pd
import pytest

from pipeline.features import build_features
from pipeline.features.schema import load_feature_schema, validate_feature_frame, validate_feature_schema
from pipeline.ingest.snapshot import load_snapshot
from pipeline.io import ContractError, digest


def test_immutable_input_has_identical_feature_digests(generated_rows, make_snapshot):
    rows, clients = generated_rows
    path = make_snapshot(rows, clients)
    first = build_features(load_snapshot(path))
    second = build_features(load_snapshot(path))
    assert digest(first.to_csv(index=False).encode()) == digest(second.to_csv(index=False).encode())
    assert len(first) == len(rows) - 1
    assert first.duplicated(["client_id", "content_id"]).sum() == 0
    feedly = first[first["content_type"].eq("feedly article")]
    assert feedly["search_volume"].isna().all()
    assert feedly["has_keyword_data"].eq(0).all()
    assert first["avg_position"].isna().equals(first["missing_position_flag"].eq(1))


def test_trend_and_comparison_windows_cannot_change_features(generated_rows, make_snapshot):
    rows, clients = generated_rows
    first = build_features(load_snapshot(make_snapshot(rows, clients)))
    changed = [{**row, "trend_direction": "down", "trend_pct": -76,
                "impressions_last_30d": 16, "impressions_prev_30d": 65} for row in rows]
    second = build_features(load_snapshot(make_snapshot(changed, clients)))
    pd.testing.assert_frame_equal(first, second)


@pytest.mark.parametrize("forbidden", [
    "client_id", "trend_direction", "trend_pct", "impressions_last_30d", "impressions_prev_30d", "health_score",
])
def test_schema_rejects_forbidden_lineage_even_with_alias(forbidden):
    schema = load_feature_schema()
    schema["engineered"].append({"name": "renamed", "dtype": "float64", "sources": [forbidden]})
    with pytest.raises(ContractError, match="forbidden lineage"):
        validate_feature_schema(schema)


def test_shifted_or_overlapping_window_is_rejected(generated_rows, make_snapshot):
    rows, clients = generated_rows
    windows = deepcopy(load_snapshot(make_snapshot(rows[:1], clients)).identity["windows"])
    windows["previous_30d"]["end"] = "2025-01-03T00:00:00Z"
    path = make_snapshot(rows[:1], clients, changes={"windows": windows})
    with pytest.raises(ContractError, match="overlapping comparisons"):
        load_snapshot(path)


def test_features_are_client_local(generated_rows, make_snapshot):
    rows, clients = generated_rows
    first = build_features(load_snapshot(make_snapshot(rows[:8], [clients[0]])))
    full = build_features(load_snapshot(make_snapshot(rows, clients)))
    pd.testing.assert_frame_equal(first, full[full["client_id"].eq(clients[0])].reset_index(drop=True))


def test_feature_frame_rejects_extra_columns(generated_rows, make_snapshot):
    rows, clients = generated_rows
    frame = build_features(load_snapshot(make_snapshot(rows[:1], clients)))
    frame["trend_pct"] = 0.5
    with pytest.raises(ContractError, match="versioned schema"):
        validate_feature_frame(frame, load_feature_schema())


def test_empty_input_preserves_feature_schema(generated_rows, make_snapshot):
    rows, clients = generated_rows
    snapshot = load_snapshot(make_snapshot([], clients, columns=sorted(rows[0])))
    assert snapshot.clients == tuple(sorted(clients))
    assert build_features(snapshot).empty
