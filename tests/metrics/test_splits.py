from collections import Counter
from copy import deepcopy

import numpy as np
import pandas as pd
import pytest

from pipeline.evaluation.development import out_of_fold_scores
from pipeline.evaluation.splits import make_split
from pipeline.io import ContractError


def test_five_folds_with_one_validation_appearance_and_disjoint_holdout():
    groups = [f"client-{group}" for group in range(14) for _ in range(group + 1)]
    frame = pd.DataFrame({"client_id": groups})
    roster = sorted(set(groups)) + ["no-eligible-items"]
    plan = make_split(frame, roster, seed=42)
    assert plan == make_split(frame, roster, seed=42)
    assert len(plan["folds"]) == 5
    final = set(plan["final_clients"])
    final_count = len(final)
    assert final_count == 3
    assert not final.intersection(plan["development_clients"])
    assert "no-eligible-items" in plan["development_clients"]
    valid = Counter()
    for fold in plan["folds"]:
        assert not set(fold["train_clients"]).intersection(fold["validation_clients"])
        assert not final.intersection(fold["train_clients"] + fold["validation_clients"])
        valid.update(fold["validation_clients"])
    assert valid == Counter({client: 1 for client in set(groups) - final})


def test_insufficient_clients_reports_gate():
    frame = pd.DataFrame({"client_id": list("abcde")})
    with pytest.raises(ContractError, match="at least six eligible clients"):
        make_split(frame, list("abcde"))


def test_exactly_one_out_of_fold_prediction_per_development_row():
    groups = [group for group in "abcdefghijkl" for _ in range(ord(group) - 96)]
    frame = pd.DataFrame({"client_id": groups, "row": range(len(groups))})
    split = make_split(frame, sorted(set(groups)))
    development = frame[frame["client_id"].isin(split["development_clients"])]
    seen = Counter()

    def record(training, validation):
        assert set(training["client_id"]).isdisjoint(validation["client_id"])
        assert set(training["client_id"]).isdisjoint(split["final_clients"])
        seen.update(validation["row"])
        return {"base": validation["row"], "engineered": -validation["row"]}

    scores = out_of_fold_scores(development, split, record)
    assert seen == Counter(development["row"])
    np.testing.assert_array_equal(scores["base"], development["row"])
    broken = deepcopy(split)
    broken["folds"].append(broken["folds"][0])
    with pytest.raises(ContractError, match="multiple predictions"):
        out_of_fold_scores(development, broken, record)
