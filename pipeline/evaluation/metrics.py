from statistics import fmean

import numpy as np

from pipeline.evaluation.ranking import ordered_ranks
from pipeline.ingest.contract import KEYS
from pipeline.io import ContractError


CUTOFFS = (10, 25, 50)


def labels_for(frame, snapshot):
    if "trend_direction" not in snapshot.rows:
        raise ContractError("evaluation requires observed trend_direction labels")
    rows = frame.loc[:, list(KEYS)].merge(
        snapshot.rows.loc[:, [*KEYS, "trend_direction"]], on=list(KEYS), how="left", validate="one_to_one",
    )
    if rows["trend_direction"].isna().any():
        raise ContractError("evaluation requires a label on every eligible row")
    return rows["trend_direction"].eq("down").to_numpy(dtype=int)


def client_metrics(ordered_labels):
    count = len(ordered_labels)
    positives = int(ordered_labels.sum())
    at_k = {}
    for k in CUTOFFS:
        limit = min(k, count)
        relevance = ordered_labels[:limit]
        hits = int(relevance.sum())
        discount = 1 / np.log2(np.arange(2, limit + 2))
        ideal = discount[:min(positives, limit)].sum()
        at_k[str(k)] = {
            "effective_k": limit, "precision": hits / limit,
            "ndcg": float(relevance @ discount / ideal) if positives else 0.0,
            "nonrelevant_in_queue": limit - hits, "positives_below_queue": positives - hits,
        }
    return {"eligible_rows": count, "positives": positives, "at_k": at_k}


def summarize(frame, labels, scores, roster):
    target = np.asarray(labels)
    if target.shape != (len(frame),) or not np.isin(target, [0, 1]).all():
        raise ContractError("metrics require one binary label per eligible item")
    ranked = ordered_ranks(frame, scores)
    ranked["label"] = target[ranked.index]
    by_client = {
        client: client_metrics(rows["label"].to_numpy())
        for client, rows in ranked.groupby("client_id", sort=False)
    }
    if not by_client.keys() <= set(roster):
        raise ContractError("evaluated client is outside the split roster")
    clients = list(by_client.values())
    macro = {
        str(k): {metric: fmean(row["at_k"][str(k)][metric] for row in clients) if clients else None
                 for metric in ("precision", "ndcg")}
        for k in CUTOFFS
    }
    return {
        "coverage": {
            "eligible_rows": len(frame), "included_clients": len(clients),
            "empty_clients": len(set(roster)) - len(clients),
            "zero_positive_clients": sum(row["positives"] == 0 for row in clients),
            "undersized_clients": {str(k): sum(row["eligible_rows"] < k for row in clients) for k in CUTOFFS},
        },
        "macro": macro,
        "clients": {client: by_client.get(client, {"eligible_rows": 0, "positives": 0, "at_k": {}})
                    for client in sorted(roster)},
    }


def evaluate_methods(frame, labels, scores_by_method, roster):
    report = {name: summarize(frame, labels, scores, roster) for name, scores in scores_by_method.items()}
    rule = report["rule"]
    for name, result in report.items():
        if name == "rule":
            continue
        for client, values in result["clients"].items():
            for k, measures in values["at_k"].items():
                baseline = rule["clients"][client]["at_k"][k]
                for metric in ("precision", "ndcg"):
                    measures[f"{metric}_delta_vs_rule"] = measures[metric] - baseline[metric]
        result["macro_delta_vs_rule"] = {
            k: {metric: value - rule["macro"][k][metric] if value is not None else None
                for metric, value in measures.items()}
            for k, measures in result["macro"].items()
        }
    return report
