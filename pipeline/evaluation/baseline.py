import pandas as pd


RULE_WEIGHTS = {"visibility": 0.40, "freshness": 0.30, "position_opportunity": 0.25, "depth_gap": 0.05}


def rule_components(frame):
    """Apply the capstone rule's fixed weights to client-local review signals."""
    clients = frame["client_id"]
    visibility = frame["log_impressions_90d"].groupby(clients).rank(method="average", pct=True)
    freshness = frame["days_since_last_update"].groupby(clients).rank(method="average", pct=True)
    position = frame["avg_position"].clip(1, 50)
    positions = position.groupby(clients)
    lowest = positions.transform("min")
    span = positions.transform("max") - lowest
    relative_position = ((position - lowest) / span.where(span.gt(0))).fillna(0)
    opportunity = (1 - relative_position) * visibility * position.notna()
    depth = (1 - frame["word_count"].groupby(clients).rank(method="average", pct=True)) * visibility
    return pd.DataFrame({
        "visibility": visibility, "freshness": freshness,
        "position_opportunity": opportunity, "depth_gap": depth,
    }).fillna(0)


def rule_scores(frame):
    return (rule_components(frame) * pd.Series(RULE_WEIGHTS)).sum(axis="columns").to_numpy()
