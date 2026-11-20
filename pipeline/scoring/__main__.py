import argparse
from pathlib import Path

from pipeline.io import ContractError
from pipeline.scoring import score_local


def main():
    parser = argparse.ArgumentParser(description="Score a verified local model against a content snapshot.")
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--model-manifest", required=True, type=Path)
    parser.add_argument("--artifact-dir", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    try:
        score_local(args.manifest, args.model_manifest, args.artifact_dir, args.output_dir)
    except ContractError as error:
        parser.exit(1, f"Scoring failed: {error}\n")


if __name__ == "__main__":
    main()
