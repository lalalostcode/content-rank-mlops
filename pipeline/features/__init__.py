"""Build the label-isolated, versioned feature frame in DuckDB."""

import duckdb

from pipeline.features.schema import SQL_PATH, feature_fields, load_feature_schema, validate_feature_frame
from pipeline.ingest.contract import KEYS
from pipeline.io import ContractError


def build_features(snapshot):
    schema = load_feature_schema()
    fields = feature_fields(schema, "engineered")
    sources = sorted({source for field in fields for source in field["sources"]})
    # IDs serve joins and within-client windows. Auditing/trend fields are outside SQL scope.
    try:
        with duckdb.connect(config={"threads": 1}) as db:
            db.register("snapshot_signals", snapshot.rows.loc[:, [*KEYS, *sources]])
            frame = db.execute(SQL_PATH.read_text(encoding="utf-8")).df()
    except (duckdb.Error, KeyError):
        raise ContractError("DuckDB feature transform failed against the input contract") from None
    ordered = [*KEYS, *(field["name"] for field in fields)]
    if len(frame.columns) != len(ordered) or set(frame) != set(ordered):
        raise ContractError("DuckDB produced undeclared or missing features")
    frame = frame.loc[:, ordered]
    validate_feature_frame(frame, schema)
    return frame
