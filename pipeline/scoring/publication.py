"""Publish complete client queues through the Flyway-owned PostgreSQL schema."""

from datetime import datetime

import pandas as pd
import psycopg
from psycopg.types.json import Jsonb

from pipeline.io import ContractError


METRICS = {
    "impressions": "impressions_90d", "clicks": "clicks_90d", "ctr": "ctr",
    "avgPosition": "avg_position", "sessions": "sessions_90d", "engagementRate": "engagement_rate",
    "daysSinceLastUpdate": "days_since_last_update", "trendPercent": "trend_pct",
}


def observation(row):
    metrics = {metric: None if pd.isna(row.get(source)) else float(row[source])
               for metric, source in METRICS.items()}
    if metrics["avgPosition"] == 0:
        metrics["avgPosition"] = None
    trend = row.get("trend_direction")
    declining = None if pd.isna(trend) else trend == "down"
    return metrics, declining


def reason_codes(metrics, declining):
    reasons = []
    if declining and metrics["trendPercent"] is not None:
        reasons.append(("OBSERVED_DECLINE", "trendPercent", "percent"))
    if (metrics["impressions"] or 0) >= 100 and metrics["ctr"] is not None and metrics["ctr"] < 1:
        reasons.append(("LOW_CTR", "ctr", "percent"))
    if (metrics["daysSinceLastUpdate"] or 0) >= 90:
        reasons.append(("STALE_CONTENT", "daysSinceLastUpdate", "days"))
    if not reasons:
        reasons.append(("SEARCH_VISIBILITY", "impressions", "count"))
    return [{"code": code, "metric": metric, "value": metrics[metric], "unit": unit}
            for code, metric, unit in reasons]


def publish_client(cursor, client, observations, ranks, receipt):
    identity = receipt["input"]
    run_id = receipt["run_id"]
    snap = identity["snapshot_id"]
    cutoff = datetime.fromisoformat(identity["cutoff"])
    checksum = identity["manifest_sha256"]
    period = identity["windows"]["snapshot_90d"]

    cursor.execute("INSERT INTO client (id, label) VALUES (%s, %s) ON CONFLICT DO NOTHING",
                   (client, client.replace("-", " ").title()))
    cursor.execute("SELECT published_run_id FROM client WHERE id = %s FOR UPDATE", (client,))
    prior_run, = cursor.fetchone()
    cursor.execute("SELECT 1 FROM scoring_run WHERE client_id = %s AND id = %s", (client, run_id))
    if cursor.fetchone():
        return False
    if prior_run is not None:
        cursor.execute("SELECT observation_cutoff FROM scoring_run WHERE client_id = %s AND id = %s",
                       (client, prior_run))
        if cursor.fetchone()[0] > cutoff:
            raise ContractError("publication would replace a newer observation cutoff")
    cursor.execute("""SELECT 1 FROM scoring_run WHERE client_id = %s AND snapshot_id = %s
                      AND input_digest <> %s LIMIT 1""", (client, snap, checksum))
    if cursor.fetchone():
        raise ContractError("snapshot ID already identifies a different input manifest")

    cursor.execute("""
        INSERT INTO scoring_run (client_id, id, snapshot_id, input_digest, observation_cutoff,
            transform_revision, model_id, status, input_rows, eligible_rows, started_at, finished_at, published_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, 'succeeded', %s, %s, %s, clock_timestamp(), clock_timestamp())
        """, (client, run_id, snap, checksum, cutoff, receipt["features"]["transform_sha256"],
              receipt["model"]["model_id"], len(observations), len(ranks), receipt["started_at"]))
    values = {row["content_id"]: observation(row) for row in observations}
    cursor.executemany("INSERT INTO content (client_id, id) VALUES (%s, %s) ON CONFLICT DO NOTHING",
                       [(client, item) for item in values])
    cursor.executemany("""
        INSERT INTO observation (client_id, content_id, snapshot_id, cutoff, source_release, input_digest,
            window_start, window_end, metrics, declining)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) ON CONFLICT DO NOTHING
        """, [(client, item, snap, cutoff, identity["source_release"], checksum, period["start"], period["end"],
               Jsonb(metrics), declining) for item, (metrics, declining) in values.items()])
    cursor.executemany("""
        INSERT INTO rank_item (client_id, run_id, content_id, snapshot_id, position, score, reason_codes)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, [(client, run_id, rank.content_id, snap, rank.position, rank.score,
               Jsonb(reason_codes(*values[rank.content_id]))) for rank in ranks])
    cursor.execute("UPDATE client SET published_run_id = %s WHERE id = %s", (run_id, client))
    return True


def publish_rankings(snapshot, ranking, receipt):
    model = receipt["model"]
    schema = receipt["features"]["feature_schema_version"]
    observations = {client: rows.to_dict("records") for client, rows in snapshot.rows.groupby("client_id")}
    ranks = {client: list(rows.itertuples(index=False)) for client, rows in ranking.groupby("client_id")}
    published = 0
    try:
        with psycopg.connect(connect_timeout=5) as connection, connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO model_version (id, artifact_sha256, feature_schema_version)
                VALUES (%s, %s, %s) ON CONFLICT DO NOTHING
                """, (model["model_id"], model["bundle_sha256"], schema))
            cursor.execute("SELECT artifact_sha256, feature_schema_version FROM model_version WHERE id = %s",
                           (model["model_id"],))
            if cursor.fetchone() != (model["bundle_sha256"], schema):
                raise ContractError("stored model provenance differs from the verified bundle")
            for client in sorted(snapshot.clients):
                published += publish_client(cursor, client, observations.get(client, []), ranks.get(client, []), receipt)
    except psycopg.Error:
        raise ContractError("PostgreSQL publication failed and the transaction was rolled back") from None
    return {"published_clients": published, "replayed_clients": len(snapshot.clients) - published}
