import numpy as np
import pandas as pd

from pipeline.ingest.contract import KEYS
from pipeline.io import ContractError


COMPONENTS = ("base", "engineered")
LEARNED_STRATEGIES = (*COMPONENTS, "blend")
BLEND_WEIGHTS = {"base": 0.5, "engineered": 0.5}


def finite_scores(values, length):
    scores = np.asarray(values, dtype=float)
    if scores.shape != (length,) or not np.isfinite(scores).all():
        raise ContractError("ranking requires one finite score per eligible item")
    return scores


def blend_scores(frame, base, engineered):
    """Average tie-aware ascending percentiles over each eligible client inventory."""
    clients = frame["client_id"].to_numpy()
    base_groups = pd.Series(finite_scores(base, len(frame))).groupby(clients)
    base_ranks = base_groups.rank(method="average")
    engineered_ranks = pd.Series(finite_scores(engineered, len(frame))).groupby(clients).rank(method="average")
    # Both ranks have the same denominator. Divide after averaging so exact ties stay tied.
    average_rank = BLEND_WEIGHTS["base"] * base_ranks + BLEND_WEIGHTS["engineered"] * engineered_ranks
    return (average_rank / base_groups.transform("size")).to_numpy()


def ordered_ranks(frame, scores):
    ranked = frame.loc[:, list(KEYS)].reset_index(drop=True).assign(score=finite_scores(scores, len(frame)))
    ranked = ranked.sort_values(["client_id", "score", "content_id"], ascending=[True, False, True])
    ranked["position"] = ranked.groupby("client_id", sort=False).cumcount() + 1
    return ranked[[*KEYS, "position", "score"]]
