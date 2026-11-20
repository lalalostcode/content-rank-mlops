import json

import numpy as np
import pandas as pd
import pytest

from pipeline.features import build_features
from pipeline.features.schema import load_feature_schema
from pipeline.ingest.snapshot import load_snapshot
from pipeline.io import ContractError, digest
from pipeline.model_bundle import BUNDLE_FILENAME, load_verified_bundle
from pipeline.ranker import Rankers, encoded_columns, fit_encoding, model_matrix
from pipeline.training.fit import query_layout
from pipeline.training.run import develop, evaluate_final
from pipeline.training.selection import GATE_CRITERIA, evaluate_gate


def read_json(path):
    return json.loads(path.read_bytes())


def test_query_layout_keeps_client_items_contiguous():
    frame = pd.DataFrame({"client_id": ["b", "a", "a", "c", "b"], "content_id": ["1", "2", "1", "1", "2"]})
    order, starts, sizes = query_layout(frame)
    assert order.tolist() == [2, 1, 0, 4, 3]
    assert starts.tolist() == [0, 2, 4]
    assert sizes.tolist() == [2, 2, 1]


def test_encoding_fits_only_supplied_rows_and_distinguishes_missing_and_unseen(evaluated_bundle):
    frame = build_features(load_snapshot(evaluated_bundle["snapshot"]))
    schema = load_feature_schema()
    training = frame[frame["content_type"].eq("keyword article")]
    encoding = fit_encoding(training, schema)
    assert encoding["levels"]["content_type"] == ["keyword article"]
    comparison = frame[frame["content_type"].eq("feedly article")].iloc[:2].copy()
    comparison.iloc[1, comparison.columns.get_loc("content_type")] = None
    names = [name for name, *_ in encoded_columns(schema, "base", encoding)]
    output = model_matrix(comparison, schema, "base", encoding)
    assert output[:, names.index("content_type__unseen")].tolist() == [1, 0]
    assert output[:, names.index("content_type__missing")].tolist() == [0, 1]
    assert np.isnan(output[:, names.index("search_volume")]).all()
    assert {"content_id", "client_id", "trend_direction"}.isdisjoint(names)


def test_development_replay_is_byte_identical(evaluated_bundle, tmp_path):
    rerun = tmp_path / "development-repeat"
    develop(evaluated_bundle["snapshot"], rerun, seed=42)
    for name in ("split.json", "development.json", BUNDLE_FILENAME, "frozen-model-manifest.json"):
        assert (rerun / name).read_bytes() == (evaluated_bundle["frozen"] / name).read_bytes()


def test_holdout_labels_are_unused_during_development_and_required_at_final(
    evaluated_bundle, generated_rows, make_snapshot, tmp_path,
):
    original = evaluated_bundle["frozen"]
    held_out = set(read_json(original / "split.json")["final_clients"])
    rows, clients = generated_rows
    unlabelled = [{**row, "trend_direction": None} if row["client_id"] in held_out else row for row in rows]
    path = make_snapshot(unlabelled, clients)
    frozen = tmp_path / "development-unlabelled-holdout"
    develop(path, frozen, seed=42)
    assert (frozen / "split.json").read_bytes() == (original / "split.json").read_bytes()
    changed = read_json(frozen / "development.json")
    expected = read_json(original / "development.json")
    assert changed["methods"] == expected["methods"]
    assert changed["frozen_selection"] == expected["frozen_selection"]
    assert read_json(frozen / BUNDLE_FILENAME)["models"] == read_json(original / BUNDLE_FILENAME)["models"]
    with pytest.raises(ContractError, match="label on every eligible row"):
        evaluate_final(path, frozen / "frozen-model-manifest.json", frozen, tmp_path / "failed-final")
    assert not (tmp_path / "failed-final").exists()


def test_final_pass_uses_frozen_model_and_linked_evidence(evaluated_bundle):
    bundle = load_verified_bundle(evaluated_bundle["model_manifest"], evaluated_bundle["frozen"], stage="final")
    final_report = evaluated_bundle["final"] / "final-evaluation.json"
    final = read_json(final_report)
    assert final["frozen_candidate"] == bundle.training["freeze"]["candidate"]
    assert set(final["methods"]) == {"rule", final["frozen_candidate"]}
    assert set(final["methods"]["rule"]["clients"]) == set(bundle.training["split"]["final_clients"])
    assert set(bundle.rankers.models) == {"base", "engineered"}
    assert bundle.manifest["release"]["evaluation_sha256"] == digest(final_report.read_bytes())
    assert bundle.manifest["release"]["learned_gate_passed"]


def test_final_regression_retains_rule(evaluated_bundle, generated_rows, monkeypatch, tmp_path):
    rows, _ = generated_rows
    labels = {(row["client_id"], row["content_id"]): row["trend_direction"] == "down" for row in rows}

    def rank_negatives_first(self, frame, strategy):
        return np.array([not labels[key] for key in zip(frame["client_id"], frame["content_id"], strict=True)])

    monkeypatch.setattr(Rankers, "predict", rank_negatives_first)
    frozen = evaluated_bundle["frozen"]
    manifest = evaluate_final(evaluated_bundle["snapshot"], frozen / "frozen-model-manifest.json", frozen,
                              tmp_path / "failing-candidate")
    assert not manifest["release"]["learned_gate_passed"]
    assert manifest["release"]["strategy"] == "rule"


def test_candidate_can_lose_on_client_regressions_despite_macro_lift():
    method = {
        "macro_delta_vs_rule": {"50": {"precision": 0.1}}, "coverage": {"eligible_rows": 9},
        "clients": {"a": {"positives": 2, "eligible_rows": 9, "at_k": {"50": {"precision_delta_vs_rule": -0.11}}}},
    }
    values = evaluate_gate(method, GATE_CRITERIA)
    assert not values["passed"]
    assert values["checks"]["beats_rule"]
    assert values["clients_over_regression_limit"] == ["a"]
