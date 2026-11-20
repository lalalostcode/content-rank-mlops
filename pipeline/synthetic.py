"""Generate an invented snapshot for local pipeline verification."""

import argparse
import csv
import random
from datetime import UTC, datetime
from pathlib import Path

from pipeline.ingest.contract import CATEGORIES, INPUT_SCHEMA, RATE_UNITS, TRANSFORM_VERSION
from pipeline.ingest.snapshot import windows_at
from pipeline.io import ContractError, digest, iso_utc, json_bytes, new_output_directory


DEFAULT_SEED = 20261120
CUTOFF = datetime(2025, 2, 1, tzinfo=UTC)
CLIENT_SIZES = (8, 19, 37, 51, 65, 81, 95, 106, 14, 28, 46, 56, 73, 84, 109, 124)
BENCHMARK_CLIENT_SIZES = (938,) * 16 + (937,) * 16


def fixture_rows(seed, *, benchmark=False):
    rng = random.Random(seed)
    rows = []
    sizes = BENCHMARK_CLIENT_SIZES if benchmark else CLIENT_SIZES
    clients = [f"demo-client-{index:02d}" for index in range(len(sizes))]
    for index, (client, size) in enumerate(zip(clients, sizes, strict=True)):
        client_shift = rng.uniform(-0.09, 0.09)
        for item in range(size):
            latent = rng.random()
            declining = index != 0 and latent + client_shift + rng.uniform(-0.16, 0.16) < 0.45
            impressions = rng.randint(160, 6_800)
            prev = impressions // 3
            recent = round(prev * (rng.uniform(0.45, 0.76) if declining else rng.uniform(0.83, 1.37)))
            trend = 100 * (recent - prev) / prev
            clicks = round(impressions * rng.uniform(0.006, 0.12))
            sessions = rng.randint(0, 750)
            engaged = round(sessions * (0.16 + 0.68 * latent + rng.uniform(-0.08, 0.08)))
            content_type = rng.choice(CATEGORIES["content_type"])
            keyword = content_type != "feedly article"
            age = rng.randint(90, 790)
            staleness = rng.randint(0, age)
            word_count = rng.randint(600, 4_500) if rng.random() > 0.17 else None
            position = round(rng.uniform(1, 74), 1) if rng.random() > 0.08 else 0
            rows.append({
                "client_id": client, "content_id": f"demo-page-{item:04d}", "content_type": content_type,
                "search_volume": rng.randint(0, 2_500) if keyword else None,
                "competition": round(rng.random(), 3) if keyword else None,
                "competition_level": rng.choice(CATEGORIES["competition_level"]) if keyword else None,
                "main_intent": rng.choice(CATEGORIES["main_intent"]) if keyword else None,
                "cpc": round(rng.uniform(0, 4), 2) if keyword else None,
                "word_count": word_count, "char_count": word_count * 6 if word_count is not None else None,
                "content_age_days": age, "days_since_last_update": staleness,
                "age_tier": tier(age, (90, 180, 365), CATEGORIES["age_tier"][2:]),
                "freshness_tier": tier(staleness, (30, 90, 180), CATEGORIES["freshness_tier"][1:]),
                "word_count_tier": (tier(word_count, (999, 1999, 3499), CATEGORIES["word_count_tier"])
                                    if word_count is not None else None),
                "impressions_90d": impressions, "clicks_90d": clicks, "sessions_90d": sessions,
                "engaged_sessions_90d": engaged, "ai_sessions_90d": round(sessions * rng.random() / 4),
                "days_with_impressions": rng.randint(5, 90), "days_with_sessions": rng.randint(1, 90) if sessions else 0,
                "impression_tier": tier(impressions, (299, 2999, 29999), CATEGORIES["impression_tier"][2:]),
                "position_tier": tier(position, (0, 3, 10, 20, 50), CATEGORIES["position_tier"]),
                "ctr": round(100 * clicks / impressions, 2), "avg_position": position,
                "engagement_rate": round(100 * engaged / sessions, 2) if sessions else None,
                "scroll_rate": round(rng.uniform(15, 130), 2) if sessions else None,
                "ai_traffic_pct": None,
                "impressions_last_30d": recent, "impressions_prev_30d": prev, "trend_pct": round(trend, 1),
                "trend_direction": "down" if trend < -20 else "up" if trend > 20 else "stable",
            })
            row = rows[-1]
            if sessions:
                row["ai_traffic_pct"] = round(100 * row["ai_sessions_90d"] / sessions, 2)
    if benchmark:
        return rows, clients
    # A declared client without rows and a client with a too-young page exercise separate coverage cases.
    rows.append({**rows[0], "client_id": "demo-client-ineligible", "content_age_days": 45, "age_tier": "31-90",
                 "days_since_last_update": 20, "freshness_tier": "0-30"})
    return rows, [*clients, "demo-client-empty", "demo-client-ineligible"]


def tier(value, cutoffs, categories):
    return categories[sum(value > bound for bound in cutoffs)]


def write_snapshot(directory, rows, clients, *, snapshot_id, source_release, columns=None):
    dataset = directory / "snapshot.csv"
    with dataset.open("w", encoding="utf-8", newline="") as stream:
        fields = sorted(rows[0]) if columns is None else columns
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    manifest = {
        "manifest_version": 1, "kind": "synthetic", "snapshot_id": snapshot_id, "source_release": source_release,
        "input_schema": INPUT_SCHEMA, "transform_version": TRANSFORM_VERSION,
        "dataset": dataset.name, "sha256": digest(dataset.read_bytes()), "row_count": len(rows), "client_ids": clients,
        "cutoff": iso_utc(CUTOFF), "windows": windows_at(CUTOFF), "rate_units": RATE_UNITS,
    }
    path = directory / "input-manifest.json"
    path.write_bytes(json_bytes(manifest))
    return path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--seed", default=DEFAULT_SEED, type=int)
    parser.add_argument("--benchmark", action="store_true", help="Generate 30,000 eligible items across 32 clients.")
    args = parser.parse_args()
    rows, clients = fixture_rows(args.seed, benchmark=args.benchmark)
    snapshot_id = f"synthetic-benchmark-seed-{args.seed}" if args.benchmark else f"synthetic-seed-{args.seed}"
    try:
        with new_output_directory(args.output_dir) as directory:
            write_snapshot(directory, rows, clients, snapshot_id=snapshot_id,
                           source_release="generated-fixtures-v1")
    except ContractError as error:
        parser.exit(1, f"Fixture generation failed: {error}\n")


if __name__ == "__main__":
    main()
