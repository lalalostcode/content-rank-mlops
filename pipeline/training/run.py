from pipeline.evaluation.baseline import rule_scores
from pipeline.evaluation.development import out_of_fold_scores
from pipeline.evaluation.metrics import evaluate_methods, labels_for
from pipeline.evaluation.ranking import COMPONENTS
from pipeline.evaluation.splits import make_split
from pipeline.features import build_features
from pipeline.features.schema import feature_identity, load_feature_schema
from pipeline.ingest.snapshot import load_snapshot
from pipeline.io import ContractError, digest, json_bytes, new_output_directory
from pipeline.model_bundle import BUNDLE_FILENAME, export_frozen_bundle, load_verified_bundle
from pipeline.training.fit import BOOST_ROUNDS, PARAMETERS, fit_rankers
from pipeline.training.selection import GATE_CRITERIA, evaluate_gate, freeze_candidate


def develop(manifest, output_dir, *, seed):
    snapshot = load_snapshot(manifest)
    features = build_features(snapshot)
    schema = load_feature_schema()
    split = make_split(features, snapshot.clients, seed)
    development = features[features["client_id"].isin(split["development_clients"])]
    labels = labels_for(development, snapshot)

    def score_fold(train, validation):
        rankers = fit_rankers(train, labels_for(train, snapshot), schema, seed=seed)
        return {name: rankers.predict_component(validation, name) for name in COMPONENTS}

    with new_output_directory(output_dir) as directory:
        (directory / "split.json").write_bytes(json_bytes(split))
        scored = {"rule": rule_scores(development), **out_of_fold_scores(development, split, score_fold)}
        results = evaluate_methods(development, labels, scored, split["development_clients"])
        freeze = freeze_candidate(results)
        report = json_bytes({
            "stage": "development", "input": snapshot.identity, **feature_identity(schema),
            "split_sha256": digest(json_bytes(split)), "methods": results, "frozen_selection": freeze,
        })
        (directory / "development.json").write_bytes(report)
        training = {
            "input": snapshot.identity, "split": split, "freeze": freeze, "development_sha256": digest(report),
            "learning": {"parameters": {**PARAMETERS, "seed": seed}, "boost_rounds": BOOST_ROUNDS},
        }
        models = fit_rankers(development, labels, schema, seed=seed)
        payload, model_manifest = export_frozen_bundle(models, training)
        (directory / BUNDLE_FILENAME).write_bytes(payload)
        (directory / "frozen-model-manifest.json").write_bytes(json_bytes(model_manifest))
    return model_manifest


def evaluate_final(manifest, frozen_manifest, artifact_dir, output_dir):
    frozen = load_verified_bundle(frozen_manifest, artifact_dir, stage="frozen")
    snapshot = load_snapshot(manifest)
    if frozen.training["input"] != snapshot.identity:
        raise ContractError("final evaluation requires the exact frozen input snapshot and manifest")
    freeze = frozen.training["freeze"]
    if freeze.get("gate_criteria") != GATE_CRITERIA:
        raise ContractError("incompatible frozen acceptance criteria")
    features = build_features(snapshot)
    split = frozen.training["split"]
    if split != make_split(features, snapshot.clients, split["seed"]):
        raise ContractError("final client membership differs from the frozen split")
    candidate = freeze["candidate"]
    roster = split["final_clients"]
    held_out = features[features["client_id"].isin(roster)]

    with new_output_directory(output_dir) as directory:
        labels = labels_for(held_out, snapshot)
        scores = {"rule": rule_scores(held_out), candidate: frozen.rankers.predict(held_out, candidate)}
        results = evaluate_methods(held_out, labels, scores, roster)
        gate = evaluate_gate(results[candidate], freeze["gate_criteria"])
        passed = freeze["development_passed"] and gate["passed"]
        release = {
            "stage": "final", "strategy": candidate if passed else "rule", "learned_gate_passed": passed,
        }
        report = json_bytes({
            "stage": "final", "training": frozen.manifest["training"], "model_id": frozen.manifest["model_id"],
            "frozen_manifest_sha256": frozen.manifest_sha256, "frozen_candidate": candidate,
            "gate_criteria": freeze["gate_criteria"], "development_passed": freeze["development_passed"],
            "methods": results, "holdout_gate": gate, "decision": release,
        })
        verified_manifest = {**frozen.manifest, "release": {**release, "evaluation_sha256": digest(report)}}
        (directory / "final-evaluation.json").write_bytes(report)
        (directory / "model-manifest.json").write_bytes(json_bytes(verified_manifest))
    return verified_manifest
