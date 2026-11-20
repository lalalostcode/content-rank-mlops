import json
import subprocess
import sys

import pandas as pd
import pytest

from pipeline.io import ContractError, digest, json_bytes
from pipeline.model_bundle import BUNDLE_FILENAME, load_verified_bundle
from pipeline.scoring import RANKS_FILE, RECEIPT_FILE, score_local


def score_cli(bundle, output_dir):
    return subprocess.run([
        sys.executable, "-m", "pipeline.scoring", "--manifest", str(bundle["snapshot"]),
        "--model-manifest", str(bundle["model_manifest"]), "--artifact-dir", str(bundle["frozen"]),
        "--output-dir", str(output_dir),
    ], capture_output=True, text=True, timeout=60)


def test_cli_reloads_pinned_model_and_writes_deterministic_rankings(evaluated_bundle, tmp_path):
    first, second = tmp_path / "first", tmp_path / "second"
    for target in (first, second):
        result = score_cli(evaluated_bundle, target)
        assert result.returncode == 0, result.stderr
    first_receipt = json.loads((first / RECEIPT_FILE).read_bytes())
    second_receipt = json.loads((second / RECEIPT_FILE).read_bytes())
    a, b = (first / RANKS_FILE).read_bytes(), (second / RANKS_FILE).read_bytes()
    assert a == b
    assert first_receipt["output_sha256"] == second_receipt["output_sha256"] == digest(a)
    assert first_receipt["run_id"] == second_receipt["run_id"]
    assert first_receipt["model"]["manifest_sha256"] == digest(evaluated_bundle["model_manifest"].read_bytes())
    assert first_receipt["input"]["manifest_sha256"] == digest(evaluated_bundle["snapshot"].read_bytes())
    assert first_receipt["empty_clients"] == 2
    assert first_receipt["stage_duration_seconds"].keys() == {"verify_model", "load_snapshot", "build_features", "rank_and_write"}
    assert all(seconds >= 0 for seconds in first_receipt["stage_duration_seconds"].values())
    ranks = pd.read_csv(first / RANKS_FILE)
    assert len(ranks) == first_receipt["eligible_rows"] == 996
    assert not ranks.duplicated(["client_id", "content_id"]).any()
    assert ranks["position"].equals(ranks.groupby("client_id").cumcount() + 1)
    expected = ranks.sort_values(["client_id", "score", "content_id"], ascending=[True, False, True])
    pd.testing.assert_frame_equal(ranks, expected)
    with pytest.raises(ContractError, match="output directory already exists"):
        score_local(evaluated_bundle["snapshot"], evaluated_bundle["model_manifest"], evaluated_bundle["frozen"], first)
    assert (first / RANKS_FILE).read_bytes() == a


def test_tampered_bundle_cli_exits_with_failed_receipt_only(evaluated_bundle, tmp_path):
    artifacts = tmp_path / "wrong-artifact"
    artifacts.mkdir()
    bundle = evaluated_bundle["frozen"] / BUNDLE_FILENAME
    (artifacts / BUNDLE_FILENAME).write_bytes(bundle.read_bytes() + b" ")
    output = tmp_path / "failed-run"
    result = score_cli({**evaluated_bundle, "frozen": artifacts}, output)
    assert result.returncode == 1
    assert "SHA-256 differs" in result.stderr
    assert list(output.iterdir()) == [output / RECEIPT_FILE]
    receipt = json.loads((output / RECEIPT_FILE).read_bytes())
    assert receipt["status"] == "failed"
    assert set(receipt["stage_duration_seconds"]) == {"verify_model"}


@pytest.mark.parametrize(("change", "message"), [
    ({"feature_schema_version": "old-schema"}, "feature schema or transform"),
    ({"feature_schema_sha256": "a" * 64}, "feature schema or transform"),
    ({"dependency_lock_sha256": "a" * 64}, "dependency lock or runtime"),
])
def test_mismatched_manifest_is_rejected_before_bundle_read(evaluated_bundle, tmp_path, change, message):
    metadata = json.loads(evaluated_bundle["model_manifest"].read_bytes())
    manifest = tmp_path / "mismatch.json"
    manifest.write_bytes(json_bytes({**metadata, **change}))
    with pytest.raises(ContractError, match=message):
        load_verified_bundle(manifest, tmp_path / "nonexistent", stage="final")


def test_changed_embedded_schema_fails_even_with_matching_hash(evaluated_bundle, tmp_path):
    contents = json.loads((evaluated_bundle["frozen"] / BUNDLE_FILENAME).read_bytes())
    contents["feature_schema"]["base"].reverse()
    payload = json_bytes(contents)
    checksum = digest(payload)
    (tmp_path / BUNDLE_FILENAME).write_bytes(payload)
    metadata = json.loads(evaluated_bundle["model_manifest"].read_bytes())
    path = tmp_path / "test-manifest.json"
    path.write_bytes(json_bytes({**metadata, "bundle_sha256": checksum, "model_id": f"lambdarank-{checksum}"}))
    with pytest.raises(ContractError, match="embedded feature schema"):
        load_verified_bundle(path, tmp_path, stage="final")


def test_inference_accepts_unlabelled_input(evaluated_bundle, generated_rows, make_snapshot, tmp_path):
    rows, clients = generated_rows
    without_labels = [{key: value for key, value in row.items() if key not in {"trend_direction", "trend_pct"}}
                      for row in rows]
    manifest = make_snapshot(without_labels, clients)
    artifact = (evaluated_bundle["model_manifest"], evaluated_bundle["frozen"])
    expected = score_local(evaluated_bundle["snapshot"], *artifact, tmp_path / "labeled")
    actual = score_local(manifest, *artifact, tmp_path / "unlabelled")
    assert expected["output_sha256"] == actual["output_sha256"]
    assert expected["run_id"] != actual["run_id"]


def test_all_empty_batch_succeeds_with_header_and_no_positions(evaluated_bundle, generated_rows, make_snapshot, tmp_path):
    rows, clients = generated_rows
    path = make_snapshot([], clients, columns=sorted(rows[0]))
    output = tmp_path / "empty-batch"
    receipt = score_local(path, evaluated_bundle["model_manifest"], evaluated_bundle["frozen"], output)
    assert receipt["eligible_rows"] == 0
    assert receipt["empty_clients"] == len(clients)
    assert (output / RANKS_FILE).read_text() == "client_id,content_id,position,score\n"


def test_scope_mismatch_stops_before_reading_snapshot_csv(evaluated_bundle, generated_rows, make_snapshot, tmp_path):
    rows, clients = generated_rows
    path = make_snapshot(rows[:1], clients, changes={"kind": "restricted"})
    path.with_name("snapshot.csv").unlink()
    with pytest.raises(ContractError, match="must both be synthetic or both be restricted"):
        score_local(path, evaluated_bundle["model_manifest"], evaluated_bundle["frozen"], tmp_path / "wrong-scope")


def test_expired_training_provenance_blocks_an_otherwise_matching_bundle(evaluated_bundle, tmp_path):
    contents = json.loads((evaluated_bundle["frozen"] / BUNDLE_FILENAME).read_bytes())
    inputs = {**contents["training"]["input"], "kind": "restricted", "retention_until": "2025-02-01"}
    contents["training"]["input"] = inputs
    payload = json_bytes(contents)
    checksum = digest(payload)
    (tmp_path / BUNDLE_FILENAME).write_bytes(payload)
    manifest = json.loads(evaluated_bundle["model_manifest"].read_bytes())
    manifest["training"]["input"] = inputs
    manifest.update(bundle_sha256=checksum, model_id=f"lambdarank-{checksum}")
    path = tmp_path / "expired.json"
    path.write_bytes(json_bytes(manifest))
    with pytest.raises(ContractError, match="approval has expired"):
        load_verified_bundle(path, tmp_path, stage="final")
