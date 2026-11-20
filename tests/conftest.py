import json

import pytest

from pipeline.io import json_bytes
from pipeline.synthetic import DEFAULT_SEED, fixture_rows, write_snapshot


@pytest.fixture(scope="session")
def generated_rows():
    return fixture_rows(DEFAULT_SEED)


@pytest.fixture
def make_snapshot(tmp_path):
    def write(rows, clients, *, changes=None, columns=None):
        path = write_snapshot(tmp_path, rows, clients, snapshot_id="fixture", source_release="pytest", columns=columns)
        if changes:
            obj = json.loads(path.read_bytes())
            path.write_bytes(json_bytes({**obj, **changes}))
        return path

    return write


@pytest.fixture(scope="session")
def evaluated_bundle(tmp_path_factory, generated_rows):
    from pipeline.training.run import develop, evaluate_final

    root = tmp_path_factory.mktemp("verified-model")
    rows, clients = generated_rows
    snapshot = write_snapshot(root, rows, clients, snapshot_id="fixture", source_release="pytest")
    frozen = root / "development"
    final = root / "final"
    develop(snapshot, frozen, seed=42)
    evaluate_final(snapshot, frozen / "frozen-model-manifest.json", frozen, final)
    return {"snapshot": snapshot, "frozen": frozen, "final": final,
            "model_manifest": final / "model-manifest.json"}
