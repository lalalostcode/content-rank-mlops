import argparse
from pathlib import Path

from pipeline.ingest.profile import profile_snapshot
from pipeline.ingest.snapshot import load_snapshot
from pipeline.io import ContractError, json_bytes, new_output_directory


def main():
    parser = argparse.ArgumentParser(description="Validate and profile a local content snapshot.")
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    try:
        profile = profile_snapshot(load_snapshot(args.manifest))
        with new_output_directory(args.output_dir) as directory:
            (directory / "profile.json").write_bytes(json_bytes(profile))
    except ContractError as error:
        parser.exit(1, f"Ingestion failed: {error}\n")


if __name__ == "__main__":
    main()
