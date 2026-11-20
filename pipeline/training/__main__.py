import argparse
from pathlib import Path

from pipeline.evaluation.splits import DEFAULT_SPLIT_SEED
from pipeline.io import ContractError
from pipeline.training.run import develop, evaluate_final


def main():
    parser = argparse.ArgumentParser(description="Train and evaluate client-grouped rankers locally.")
    commands = parser.add_subparsers(dest="stage", required=True)
    development = commands.add_parser("develop", help="Run grouped development and freeze the candidate.")
    final = commands.add_parser("evaluate-final", help="Evaluate the verified frozen candidate on the final clients.")
    for command in (development, final):
        command.add_argument("--manifest", required=True, type=Path)
        command.add_argument("--output-dir", required=True, type=Path)
    development.add_argument("--seed", default=DEFAULT_SPLIT_SEED, type=int)
    final.add_argument("--frozen-manifest", required=True, type=Path)
    final.add_argument("--artifact-dir", required=True, type=Path)
    args = parser.parse_args()
    try:
        if args.stage == "develop":
            if not 0 <= args.seed < 2**31:
                parser.error("--seed must be between 0 and 2147483647")
            develop(args.manifest, args.output_dir, seed=args.seed)
        else:
            evaluate_final(args.manifest, args.frozen_manifest, args.artifact_dir, args.output_dir)
    except ContractError as error:
        parser.exit(1, f"Training or evaluation failed: {error}\n")


if __name__ == "__main__":
    main()
