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
