import platform
from dataclasses import dataclass
from importlib.metadata import version
from pathlib import Path

import lightgbm as lgb

from pipeline.evaluation.ranking import COMPONENTS, LEARNED_STRATEGIES
from pipeline.features.schema import feature_identity, load_feature_schema
from pipeline.ingest.snapshot import validate_retention
from pipeline.io import (
    ContractError, SHA256, digest, json_bytes, local_filename, matches, outside_git, parse_object, read_bytes, utc_timestamp,
)
from pipeline.ranker import RANKING_CONFIG, Rankers, encoded_columns, validate_encoding


BUNDLE_FILENAME = "ranker-bundle.json"
BUNDLE_VERSION = "lambdarank-bundle-v1"
LOCK_PATH = Path(__file__).resolve().parents[1] / "uv.lock"
RUNTIME_PACKAGES = ("duckdb", "lightgbm", "numpy", "pandas", "scikit-learn", "scipy")


@dataclass(frozen=True)
class VerifiedBundle:
    manifest: dict
    manifest_sha256: str
    training: dict
    rankers: Rankers


def runtime_identity():
    return {
        "dependency_lock_sha256": digest(LOCK_PATH.read_text(encoding="utf-8").encode()),
        "runtime": {"python": platform.python_version(), **{name: version(name) for name in RUNTIME_PACKAGES}},
    }


def provenance(training):
    return {
        "input": training["input"], "seed": training["split"]["seed"],
        "split_sha256": digest(json_bytes(training["split"])),
        "development_sha256": training["development_sha256"],
    }


def export_frozen_bundle(rankers, training):
    identity = {**feature_identity(rankers.schema), **runtime_identity()}
    payload = json_bytes({
        "bundle_version": BUNDLE_VERSION, **identity,
        "feature_schema": rankers.schema, "preprocessing": rankers.encoding, "ranking": RANKING_CONFIG,
        "training": training, "models": {name: rankers.models[name].model_to_string() for name in COMPONENTS},
    })
    checksum = digest(payload)
    manifest = {
        "manifest_version": 1, "bundle_filename": BUNDLE_FILENAME,
        "model_id": f"lambdarank-{checksum}", "bundle_sha256": checksum, **identity,
        "training": provenance(training),
        "release": {"stage": "frozen", "strategy": training["freeze"]["candidate"]},
    }
    return payload, manifest


def verify_release(manifest, training, stage):
    freeze = training["freeze"]
    candidate = freeze["candidate"]
    if candidate not in LEARNED_STRATEGIES or type(freeze["development_passed"]) is not bool:
        raise ContractError("invalid frozen ranking candidate")
    release = manifest["release"]
    if stage == "frozen":
        expected_strategy = candidate
    else:
        passed = release.get("learned_gate_passed")
        if type(passed) is not bool or not matches(SHA256, release.get("evaluation_sha256")):
            raise ContractError("final model manifest requires a holdout decision and evidence digest")
        if passed and not freeze["development_passed"]:
            raise ContractError("candidate failed the frozen development gate")
        expected_strategy = candidate if passed else "rule"
    if release.get("strategy") != expected_strategy:
        raise ContractError("model manifest strategy differs from the frozen ranking decision")


def load_verified_bundle(model_manifest, artifact_dir, *, stage):
    manifest_bytes = read_bytes(outside_git(model_manifest), "trusted model manifest")
    manifest = parse_object(manifest_bytes, "model manifest")
    if (type(manifest.get("manifest_version")) is not int or manifest["manifest_version"] != 1
            or manifest.get("bundle_filename") != BUNDLE_FILENAME):
        raise ContractError("unsupported model manifest or bundle filename")
    release = manifest.get("release")
    if not isinstance(release, dict) or release.get("stage") != stage:
        raise ContractError(f"model manifest must be from the {stage} stage")
    schema = load_feature_schema()
    features = feature_identity(schema)
    runtime = runtime_identity()
    if any(manifest.get(name) != value for name, value in features.items()):
        raise ContractError("model manifest feature schema or transform is incompatible")
    if any(manifest.get(name) != value for name, value in runtime.items()):
        raise ContractError("model manifest dependency lock or runtime is incompatible")
    checksum = manifest.get("bundle_sha256")
    if not matches(SHA256, checksum) or manifest.get("model_id") != f"lambdarank-{checksum}":
        raise ContractError("model manifest requires a valid bundle digest and matching model ID")

    path = local_filename(outside_git(artifact_dir), manifest["bundle_filename"])
    payload = read_bytes(path, "model bundle")
    if digest(payload) != checksum:
        raise ContractError("model bundle SHA-256 differs from trusted manifest")
    bundle = parse_object(payload, "model bundle")
    if bundle.get("bundle_version") != BUNDLE_VERSION:
        raise ContractError("unsupported model bundle format")
    if bundle.get("feature_schema") != schema or any(bundle.get(key) != value for key, value in features.items()):
        raise ContractError("embedded feature schema or transform is incompatible")
    if any(bundle.get(name) != value for name, value in runtime.items()) or bundle.get("ranking") != RANKING_CONFIG:
        raise ContractError("embedded runtime or ranking configuration is incompatible")
    try:
        training = bundle["training"]
        if provenance(training) != manifest.get("training") or training["input"]["kind"] not in ("synthetic", "restricted"):
            raise ContractError("model manifest and bundle disagree on training provenance")
        if training["input"]["kind"] == "restricted":
            validate_retention(training["input"]["retention_until"], minimum=utc_timestamp(training["input"]["cutoff"]).date())
        verify_release(manifest, training, stage)
    except (KeyError, TypeError):
        raise ContractError("model bundle requires complete training provenance and a frozen candidate") from None
    encoding = bundle.get("preprocessing")
    validate_encoding(encoding, schema)
    texts = bundle.get("models")
    if not isinstance(texts, dict) or texts.keys() != set(COMPONENTS):
        raise ContractError("model bundle requires both trained LambdaRank components")
    models = {}
    for name in COMPONENTS:
        model_text = texts[name]
        if not isinstance(model_text, str) or not model_text.startswith("tree\n"):
            raise ContractError("invalid LightGBM text model")
        try:
            model = lgb.Booster(model_str=model_text)
        except lgb.basic.LightGBMError:
            raise ContractError("LightGBM could not reload the verified text model") from None
        expected_names = [column for column, *_ in encoded_columns(schema, name, encoding)]
        if model.feature_name() != expected_names:
            raise ContractError("LightGBM model columns differ from the verified preprocessing schema")
        models[name] = model
    return VerifiedBundle(manifest, digest(manifest_bytes), training, Rankers(schema, encoding, models))
