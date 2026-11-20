# Snapshot and feature contracts

`content-snapshot-v1` accepts a UTF-8 CSV with one row per `(client_id, content_id)` for a single observation cutoff. Keys contain letters, digits, `_`, `-` or `.` and begin with a letter or digit. Raw field types, bounds, category values and optional headers are defined in [the input contract](../pipeline/ingest/contract.py). Required headers are the identifiers and the inputs needed for the versioned feature transform. Missing measurements are empty CSV cells. An average position of zero is a source sentinel and becomes null in the feature table.

| Measurement | Unit and validation |
|---|---|
| `competition` | Fraction in `[0, 1]` |
| `ctr` | Percentage in `[0, 100]`, reconciled with clicks divided by impressions × 100 within source rounding |
| `engagement_rate` | Percentage in `[0, 100]` |
| `scroll_rate`, `ai_traffic_pct` | Nonnegative percentages that may exceed 100 |
| `trend_pct` | Optional signed percentage, at least −100, used for audit |
| Counts and age | Nonnegative whole values. Active-day counts are at most 90 |

## Input manifest

Run `python -m pipeline.synthetic --output-dir <new-directory>` for a complete generated CSV and manifest example. Use paths outside the Git checkout.

| Field | Requirement |
|---|---|
| `manifest_version`, `input_schema`, `transform_version` | `1`, `content-snapshot-v1`, `snapshot-features-v1` |
| `snapshot_id`, `source_release`, `kind` | Stable identifiers. `kind` is `synthetic` or `restricted` |
| `dataset`, `sha256`, `row_count` | CSV filename beside the manifest, lowercase SHA-256 of its bytes and exact data-row count |
| `cutoff`, `windows` | ISO date-times with offsets. Declare `snapshot_90d` as `[cutoff−90d, cutoff)`, `previous_30d` as `[cutoff−60d, cutoff−30d)` and `recent_30d` as `[cutoff−30d, cutoff)` |
| `rate_units` | Exact `RATE_UNITS` mapping from the input contract |
| `client_ids` | Optional complete roster, including clients with zero rows. Without it, the roster comes from observed rows |
| `approval` | Required for restricted input. Supply `reference`, `purpose` and an inclusive ISO date `retention_until`. Keep it private and obtain authorization before constructing the manifest |

Numeric and categorical validation runs over the same bytes that were hashed. Each caller receives a cutoff and the digest of the original manifest in addition to the CSV digest. A roster or source checksum establishes input identity. The operator must also confirm that the input contains each client's full inventory at the declared cutoff.

## Eligible inventory and features

The queue includes pages at least 90 days old with positive measured impressions. The observed label is `trend_direction == "down"`. Training requires a valid label on every eligible row. Batch inference can use a snapshot with the label fields omitted. This keeps both paths on the same eligible inventory.

The [ordered feature schema](../pipeline/features/feature-schema-v1.json) lists names, types and source dependencies for 26 base fields and 17 engineered fields. [DuckDB SQL](../pipeline/features/snapshot-v1.sql) adds availability flags, active-day intensities, interactions and within-client median deltas. Absent measurements stay null, including divisions with no exposure. Keys are carried alongside features for alignment, within-client computation and tie-breaking.

The V1 task ranks observed decline at the snapshot cutoff. It uses the same-cutoff 90-day aggregates as context under the capstone-based PRD. These totals overlap the label period in time. The transform has access to the approved context and metadata only. It excludes the recent and previous 30-day constituents, the trend fields, product decisions and prior scores, including use through aliases. Feature source allowlists and manifest window checks enforce this boundary. A future temporal experiment requires a distinct contract with windows ending before its outcome period. [Evaluation protocol](phases/PHASE_03_MACHINE_LEARNING.md#evaluation-protocol)

Feature receipts pin the schema version and SHA-256, the transform version and SQL SHA-256, input identities and the ordered feature CSV digest. Bump the applicable revision when changing inputs, eligibility, schema or transform semantics.
