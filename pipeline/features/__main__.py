import argparse
from pathlib import Path

from pipeline.features import build_features
from pipeline.features.schema import feature_identity, load_feature_schema
from pipeline.ingest.snapshot import load_snapshot
from pipeline.io import ContractError, digest, json_bytes, new_output_directory


def main():
    parser = argparse.ArgumentParser(description="Build versioned features from a verified local snapshot.")
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    try:
        snapshot = load_snapshot(args.manifest)
        frame = build_features(snapshot)
        payload = frame.to_csv(index=False, lineterminator="\n").encode()
        receipt = {
            "input": snapshot.identity, **feature_identity(load_feature_schema()),
            "input_rows": len(snapshot.rows), "eligible_rows": len(frame), "features_sha256": digest(payload),
        }
        with new_output_directory(args.output_dir) as directory:
            (directory / "features.csv").write_bytes(payload)
            (directory / "feature-receipt.json").write_bytes(json_bytes(receipt))
    except ContractError as error:
        parser.exit(1, f"Feature build failed: {error}\n")


if __name__ == "__main__":
    main()
