"""Verify a local model manifest and write one complete client ranking batch."""

from datetime import UTC, datetime
from time import perf_counter

from pipeline.evaluation.ranking import ordered_ranks
from pipeline.features import build_features
from pipeline.ingest.snapshot import load_snapshot
from pipeline.io import ContractError, digest, iso_utc, json_bytes, new_output_directory
from pipeline.model_bundle import load_verified_bundle


RANKS_FILE = "rankings.csv"
RECEIPT_FILE = "run-receipt.json"


def score_local(manifest, model_manifest, artifact_dir, output_dir):
    started = perf_counter()
    receipt = {"receipt_version": 1, "started_at": iso_utc(datetime.now(UTC))}
    failure = None
    with new_output_directory(output_dir) as staging:
        try:
            bundle = load_verified_bundle(model_manifest, artifact_dir, stage="final")
            pinned = bundle.manifest
            strategy = pinned["release"]["strategy"]
            receipt["model"] = {
                "model_id": pinned["model_id"], "manifest_sha256": bundle.manifest_sha256,
                "bundle_sha256": pinned["bundle_sha256"], "strategy": strategy,
                "training_kind": pinned["training"]["input"]["kind"],
            }
            receipt["features"] = {name: pinned[name] for name in (
                "feature_schema_version", "feature_schema_sha256", "transform_version", "transform_sha256",
            )}
            snapshot = load_snapshot(manifest, expected_kind=receipt["model"]["training_kind"])
            receipt["input"] = snapshot.identity
            receipt["input_rows"] = len(snapshot.rows)
            frame = build_features(snapshot)
            ranked = ordered_ranks(frame, bundle.rankers.predict(frame, strategy))
            payload = ranked.to_csv(index=False, lineterminator="\n", float_format="%.17g").encode()
            (staging / RANKS_FILE).write_bytes(payload)
            clients = ranked["client_id"].nunique()
            run_key = {
                "input_manifest": snapshot.identity["manifest_sha256"], "bundle": pinned["bundle_sha256"],
                "strategy": strategy, "transform": pinned["transform_sha256"],
            }
            receipt.update(
                status="succeeded", run_id=digest(json_bytes(run_key)), eligible_rows=len(ranked),
                scored_clients=int(clients), empty_clients=len(snapshot.clients) - clients,
                output_filename=RANKS_FILE, output_sha256=digest(payload),
            )
        except ContractError as error:
            failure = error
            receipt.update(status="failed", error=str(error))
        receipt["finished_at"] = iso_utc(datetime.now(UTC))
        receipt["duration_seconds"] = round(perf_counter() - started, 6)
        (staging / RECEIPT_FILE).write_bytes(json_bytes(receipt))
    if failure is not None:
        raise failure
    return receipt
