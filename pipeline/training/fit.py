import lightgbm as lgb
import numpy as np

from pipeline.evaluation.ranking import COMPONENTS
from pipeline.features.schema import validate_feature_frame
from pipeline.io import ContractError
from pipeline.ranker import Rankers, encoded_columns, fit_encoding, model_matrix


BOOST_ROUNDS = 100
PARAMETERS = {
    "objective": "lambdarank", "metric": "ndcg", "label_gain": [0, 1],
    "ndcg_eval_at": [10, 25, 50], "lambdarank_truncation_level": 53,
    "learning_rate": 0.05, "num_leaves": 15, "min_data_in_leaf": 12,
    "deterministic": True, "force_col_wise": True, "num_threads": 1, "verbosity": -1,
}


def query_layout(frame):
    clients = frame["client_id"].to_numpy(dtype=str)
    items = frame["content_id"].to_numpy(dtype=str)
    order = np.lexsort((items, clients))
    ordered_clients = clients[order]
    starts = np.r_[0, np.flatnonzero(ordered_clients[1:] != ordered_clients[:-1]) + 1]
    sizes = np.diff(np.r_[starts, len(order)])
    return order, starts, sizes


def fit_rankers(frame, labels, schema, *, seed):
    validate_feature_frame(frame, schema)
    target = np.asarray(labels)
    if frame.empty or target.shape != (len(frame),) or not np.isin(target, [0, 1]).all():
        raise ContractError("ranker fitting requires nonempty rows and aligned binary labels")
    order, starts, sizes = query_layout(frame)
    training = frame.iloc[order]
    target = target[order]
    positives = np.add.reduceat(target, starts)
    if not ((positives > 0) & (positives < sizes)).any():
        raise ContractError("ranker training needs a client query with both observed label values")
    encoding = fit_encoding(training, schema)
    models = {}
    for variant in COMPONENTS:
        names = [name for name, *_ in encoded_columns(schema, variant, encoding)]
        dataset = lgb.Dataset(model_matrix(training, schema, variant, encoding), label=target,
                              group=sizes.tolist(), feature_name=names)
        try:
            models[variant] = lgb.train({**PARAMETERS, "seed": seed}, dataset, num_boost_round=BOOST_ROUNDS)
        except lgb.basic.LightGBMError:
            raise ContractError("LightGBM could not fit the declared client queries") from None
    return Rankers(schema, encoding, models)
