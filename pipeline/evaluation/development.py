import numpy as np

from pipeline.evaluation.ranking import COMPONENTS, blend_scores, finite_scores
from pipeline.io import ContractError


def out_of_fold_scores(frame, split, score_fold):
    scores = {name: np.empty(len(frame), dtype=float) for name in COMPONENTS}
    covered = np.zeros(len(frame), dtype=bool)
    for fold in split["folds"]:
        training = frame["client_id"].isin(fold["train_clients"]).to_numpy()
        validation = frame["client_id"].isin(fold["validation_clients"]).to_numpy()
        if (training & validation).any() or covered[validation].any():
            raise ContractError("development folds overlap or assign multiple predictions to an item")
        predicted = score_fold(frame.loc[training], frame.loc[validation])
        for name in COMPONENTS:
            scores[name][validation] = finite_scores(predicted[name], int(validation.sum()))
        covered[validation] = True
    if not covered.all():
        raise ContractError("every development item must receive an out-of-fold prediction")
    return {**scores, "blend": blend_scores(frame, scores["base"], scores["engineered"])}
