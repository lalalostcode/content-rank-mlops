import math

import numpy as np
import pandas as pd
import pytest

from pipeline.evaluation.baseline import rule_components, rule_scores
from pipeline.evaluation.metrics import CUTOFFS, summarize
from pipeline.evaluation.ranking import blend_scores, ordered_ranks
from pipeline.io import ContractError


def test_ties_empty_client_and_binary_ndcg():
    frame = pd.DataFrame({"client_id": ["a"] * 3 + ["b"], "content_id": ["03", "01", "02", "01"]})
    labels = [1, 1, 0, 0]
    scores = [0.5, 0.5, 0.7, 0.1]
    ranked = ordered_ranks(frame, scores)
    assert ranked["content_id"].tolist() == ["02", "01", "03", "01"]
    assert ranked["position"].tolist() == [1, 2, 3, 1]
    report = summarize(frame, labels, scores, ("a", "b", "empty"))
    precision = report["clients"]["a"]["at_k"]["10"]["precision"]
    ndcg = (1 / math.log2(3) + 1 / math.log2(4)) / (1 + 1 / math.log2(3))
    assert precision == pytest.approx(2 / 3)
    assert report["macro"]["10"]["ndcg"] == pytest.approx(ndcg / 2)
    assert report["macro"]["10"]["precision"] == pytest.approx(1 / 3)
    assert report["clients"]["b"]["at_k"]["10"]["ndcg"] == 0
    assert report["clients"]["empty"]["at_k"] == {}
    assert report["coverage"]["zero_positive_clients"] == 1
    assert report["coverage"]["empty_clients"] == 1


@pytest.mark.parametrize("k", CUTOFFS)
@pytest.mark.parametrize("offset", [-1, 1])
def test_metric_cutoff_denominator_and_ideal_gain(k, offset):
    size = k + offset
    frame = pd.DataFrame({"client_id": "a", "content_id": [f"{i:03d}" for i in range(size)]})
    labels = np.ones(size, dtype=int)
    labels[:2] = 0
    result = summarize(frame, labels, np.zeros(size), ["a"])
    metric = result["clients"]["a"]["at_k"][str(k)]
    effective = min(size, k)
    discount = [1 / math.log2(position + 1) for position in range(1, effective + 1)]
    assert metric["effective_k"] == effective
    assert metric["precision"] == pytest.approx((effective - 2) / effective)
    assert metric["ndcg"] == pytest.approx(sum(discount[2:]) / sum(discount[:min(size - 2, k)]))
    assert metric["positives_below_queue"] == max(0, offset)
    assert result["coverage"]["undersized_clients"][str(k)] == int(offset < 0)


def test_pooled_precision_differs_from_client_macro():
    frame = pd.DataFrame({"client_id": ["large"] * 60 + ["small"], "content_id": [f"{i:03d}" for i in range(61)]})
    labels = np.array([0] * 60 + [1])
    scores = np.array([1] * 60 + [0])
    assert labels[np.argsort(-scores)[:50]].mean() == 0
    assert summarize(frame, labels, scores, ["large", "small"])["macro"]["50"]["precision"] == 0.5


def test_blend_average_ties_and_client_invariance():
    first = pd.DataFrame({"client_id": ["a"] * 3, "content_id": ["03", "02", "01"]})
    extra = pd.DataFrame({"client_id": ["b"] * 2, "content_id": ["03", "01"]})
    base, engineered = [1, 3, 1], [5, 2, 5]
    alone = blend_scores(first, base, engineered)
    combined = blend_scores(pd.concat([first, extra]), [*base, 99, 999], [*engineered, 80, 90])
    np.testing.assert_allclose(alone, [2 / 3] * 3)
    np.testing.assert_array_equal(alone, combined[:3])
    assert ordered_ranks(first, alone)["content_id"].tolist() == ["01", "02", "03"]


def test_rule_weights_and_missing_contributions():
    frame = pd.DataFrame({"client_id": ["a", "a"], "log_impressions_90d": [1.0, 4.0],
                          "days_since_last_update": [10.0, 30.0], "avg_position": [None, 2.0],
                          "word_count": [500.0, 1000.0]})
    assert rule_components(frame)["position_opportunity"].tolist() == [0.0, 1.0]
    np.testing.assert_allclose(rule_scores(frame), [0.40 * 0.5 + 0.30 * 0.5 + 0.05 * 0.25, 0.95])


def test_rejects_nonfinite_scores():
    frame = pd.DataFrame({"client_id": ["a"], "content_id": ["01"]})
    with pytest.raises(ContractError, match="one finite score"):
        ordered_ranks(frame, [np.nan])
