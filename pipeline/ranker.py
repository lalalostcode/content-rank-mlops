from dataclasses import dataclass

import numpy as np

from pipeline.evaluation.baseline import RULE_WEIGHTS, rule_scores
from pipeline.evaluation.ranking import BLEND_WEIGHTS, blend_scores
from pipeline.features.schema import feature_fields
from pipeline.ingest.contract import CATEGORIES
from pipeline.io import ContractError


ENCODING_VERSION = "native-numeric-null-with-one-hot-v1"
RANKING_CONFIG = {
    "version": "client-rank-v1", "client_scope": "complete-eligible-inventory",
    "tie_breaker": "content_id-ascending", "score_order": "descending",
    "blend_percentile": "ascending-average-rank-over-eligible-count",
    "blend_weights": BLEND_WEIGHTS, "rule_weights": RULE_WEIGHTS,
}


def fit_encoding(frame, schema):
    levels = {
        field["name"]: sorted(frame[field["name"]].dropna().unique())
        for field in feature_fields(schema, "base") if field["dtype"] == "string"
    }
    return {"version": ENCODING_VERSION, "levels": levels}


def validate_encoding(encoding, schema):
    categories = {field["name"] for field in feature_fields(schema, "base") if field["dtype"] == "string"}
    if (not isinstance(encoding, dict) or encoding.get("version") != ENCODING_VERSION
            or not isinstance(encoding.get("levels"), dict) or encoding["levels"].keys() != categories):
        raise ContractError("model preprocessing does not match the feature schema")
    for name, levels in encoding["levels"].items():
        if (not isinstance(levels, list) or not all(level in CATEGORIES.get(name, ()) for level in levels)
                or levels != sorted(set(levels))):
            raise ContractError("model preprocessing contains invalid category levels")


def encoded_columns(schema, variant, encoding):
    for field in feature_fields(schema, variant):
        name = field["name"]
        if field["dtype"] == "float64":
            yield name, name, "numeric", None
        else:
            for index, level in enumerate(encoding["levels"][name]):
                yield f"{name}__{index:02d}", name, "known", level
            yield f"{name}__missing", name, "missing", None
            yield f"{name}__unseen", name, "unseen", None


def model_matrix(frame, schema, variant, encoding):
    values = []
    for _, name, kind, level in encoded_columns(schema, variant, encoding):
        column = frame[name]
        if kind == "known":
            column = column.eq(level).fillna(False)
        elif kind == "missing":
            column = column.isna()
        elif kind == "unseen":
            column = column.notna() & ~column.isin(encoding["levels"][name])
        values.append(column.to_numpy(dtype=float, na_value=np.nan))
    return np.column_stack(values)


@dataclass(frozen=True)
class Rankers:
    schema: dict
    encoding: dict
    models: dict

    def predict_component(self, frame, variant):
        if frame.empty:
            return np.empty(0, dtype=float)
        matrix = model_matrix(frame, self.schema, variant, self.encoding)
        return self.models[variant].predict(matrix, num_threads=1)

    def predict(self, frame, strategy):
        if strategy == "rule":
            return rule_scores(frame)
        if strategy == "blend":
            return blend_scores(frame, self.predict_component(frame, "base"), self.predict_component(frame, "engineered"))
        return self.predict_component(frame, strategy)
