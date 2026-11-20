import re
from pathlib import Path

import numpy as np
from pandas.api.types import is_string_dtype

from pipeline.ingest.contract import COMPARISON_FIELDS, KEYS, TRANSFORM_VERSION
from pipeline.io import ContractError, digest, json_bytes, matches, parse_object


SCHEMA_VERSION = "rank-features-v1"
SCHEMA_PATH = Path(__file__).with_name("feature-schema-v1.json")
SQL_PATH = Path(__file__).with_name("snapshot-v1.sql")
FIELD_NAME = re.compile(r"[a-z][a-z0-9_]{0,63}")
OBSERVATION_POLICY = "contemporaneous-snapshot"
METADATA_SIGNALS = {
    "search_volume", "competition", "cpc", "word_count", "char_count", "content_age_days",
    "days_since_last_update", "competition_level", "content_type", "main_intent", "age_tier",
    "freshness_tier", "word_count_tier",
}
SNAPSHOT_SIGNALS = {
    "impressions_90d", "clicks_90d", "sessions_90d", "ai_sessions_90d", "days_with_impressions",
    "days_with_sessions", "ctr", "avg_position", "engagement_rate", "scroll_rate", "ai_traffic_pct",
    "impression_tier", "position_tier",
}
FORBIDDEN = set(KEYS) | COMPARISON_FIELDS | {
    "trend_direction", "trend_pct", "is_declining_label", "health_score", "quick_win", "is_quick_win",
    "needs_ctr_fix", "needs_attention", "baseline_refresh_score", "action_score",
}


def validate_feature_schema(schema):
    if (schema.get("schema_version") != SCHEMA_VERSION or schema.get("observation_policy") != OBSERVATION_POLICY
            or set(schema) != {"schema_version", "observation_policy", "base", "engineered"}):
        raise ContractError("unsupported feature schema or observation policy")
    names = set()
    allowed = METADATA_SIGNALS | SNAPSHOT_SIGNALS
    for group in ("base", "engineered"):
        if not isinstance(schema[group], list) or not schema[group]:
            raise ContractError("feature schema requires two nonempty feature groups")
        for field in schema[group]:
            if not isinstance(field, dict) or field.keys() != {"name", "dtype", "sources"}:
                raise ContractError("invalid feature declaration")
            name, dtype, sources = field["name"], field["dtype"], field["sources"]
            if not matches(FIELD_NAME, name) or name in FORBIDDEN or name in names:
                raise ContractError("forbidden, invalid or duplicate feature name")
            if dtype not in ("float64", "string"):
                raise ContractError("invalid feature type")
            if (not isinstance(sources, list) or not sources
                    or not all(isinstance(source, str) and source in allowed for source in sources)):
                raise ContractError("forbidden lineage, including label sources and overlapping comparison windows")
            names.add(name)


def load_feature_schema():
    schema = parse_object(SCHEMA_PATH.read_bytes(), "feature schema")
    validate_feature_schema(schema)
    return schema


def feature_fields(schema, variant):
    if variant == "base":
        return schema["base"]
    if variant == "engineered":
        return [*schema["base"], *schema["engineered"]]
    raise ContractError("unsupported feature variant")


def feature_identity(schema):
    return {
        "feature_schema_version": schema["schema_version"],
        "feature_schema_sha256": digest(json_bytes(schema)),
        "transform_version": TRANSFORM_VERSION,
        "transform_sha256": digest(SQL_PATH.read_text(encoding="utf-8").encode()),
    }


def validate_feature_frame(frame, schema):
    fields = feature_fields(schema, "engineered")
    if list(frame) != [*KEYS, *(field["name"] for field in fields)]:
        raise ContractError("feature frame fields or ordering differ from the versioned schema")
    for field in fields:
        values = frame[field["name"]]
        if field["dtype"] == "float64":
            if values.dtype != np.dtype("float64") or np.isinf(values).any():
                raise ContractError("feature frame has an invalid numeric type or nonfinite value")
        elif not is_string_dtype(values.dtype) or (values.notna().any() and not is_string_dtype(values.dropna())):
            raise ContractError("feature frame has an invalid string type")
