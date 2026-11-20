from pipeline.ingest.contract import KEYS, NUMERIC, RATE_UNITS


def profile_snapshot(snapshot):
    breakdown = {}
    for name, rows in snapshot.rows.groupby("content_type", sort=True):
        fields = {}
        for field in sorted(set(rows) - set(KEYS) - {"content_type"}):
            values = rows[field]
            missing = values.isna()
            if field == "avg_position":
                missing |= values.eq(0)
            stats = {"missing": int(missing.sum()), "missing_fraction": float(missing.mean())}
            observed = values[~missing]
            if field in NUMERIC and not observed.empty:
                stats.update(min=float(observed.min()), max=float(observed.max()))
            fields[field] = stats
        breakdown[name] = {"rows": len(rows), "fields": fields}
    return {
        "input": snapshot.identity, "grain": list(KEYS), "rows": len(snapshot.rows),
        "declared_or_observed_clients": len(snapshot.clients), "rate_units": RATE_UNITS,
        "zero_position_sentinels": int(snapshot.rows["avg_position"].eq(0).sum()),
        "by_content_type": breakdown,
    }
