import math
import random

from sklearn.model_selection import GroupKFold

from pipeline.io import ContractError


FOLDS = 5
FINAL_FRACTION = 0.20
DEFAULT_SPLIT_SEED = 42
SPLIT_VERSION = "client-group-kfold-v1"


def make_split(frame, roster, seed=DEFAULT_SPLIT_SEED):
    eligible_clients = sorted(frame["client_id"].unique())
    if len(eligible_clients) < FOLDS + 1:
        raise ContractError("five development folds and a holdout require at least six eligible clients")
    final_count = min(math.ceil(len(eligible_clients) * FINAL_FRACTION), len(eligible_clients) - FOLDS)
    final = sorted(random.Random(seed).sample(eligible_clients, final_count))
    development = frame.loc[~frame["client_id"].isin(final)]
    groups = development["client_id"]
    folds = []
    for train, validation in GroupKFold(n_splits=FOLDS).split(development, groups=groups):
        folds.append({
            "train_clients": sorted(groups.iloc[train].unique()),
            "validation_clients": sorted(groups.iloc[validation].unique()),
        })
    return {
        "version": SPLIT_VERSION, "seed": seed, "final_clients": final,
        "development_clients": sorted(set(roster) - set(final)), "folds": folds,
    }
