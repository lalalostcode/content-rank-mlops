# Synthetic snapshot quality profile

The generated fixture uses seed `20261120`, source release `generated-fixtures-v1`, and cutoff `2025-02-01T00:00:00Z`. Ingestion accepted 997 rows with unique composite keys and a declared roster of 18 clients. There were 996 eligible rows. One client had zero rows and one had a single page younger than 90 days. [Snapshot contract](../docs/data-dictionary.md)

| Content type | Rows | Missing search volume | Missing word count | Missing average position | CTR range (%) |
|---|---:|---:|---:|---:|---:|
| Comparison article | 362 | 0 | 73 | 19 | 0.73–11.95 |
| Feedly article | 308 | 308 | 49 | 22 | 0.63–12.00 |
| Keyword article | 327 | 0 | 64 | 30 | 0.61–12.00 |

The profile counted 71 zero-position sentinels as missing. The largest observed scroll rate was 129.96%, which the contract permits because a pageview can have multiple scroll events. In this fixture, absent keyword context is systematic by content type. The transform preserves those nulls and records availability explicitly.

| SHA-256 | Value |
|---|---|
| Snapshot CSV | `370a0c359c950ae9e1c713cf83ad0ab8f0d23a4868bf698c193515364ff38c30` |
| Input manifest | `7361cd7949968be33e8f978e757c60a73788138de15320d48095ad708260e8ff` |
| Feature CSV, both runs | `314a59fdb49e007d965c5f27019331fb83552f5d1190c9046ee1f0ab931964ec` |

The local `profile.json` records null counts, fractions and observed numeric ranges per field and content type. Tests rejected duplicate keys, invalid types and units, inconsistent CTR, mismatched checksums, missing cutoffs, unapproved restricted inputs, forbidden lineage and overlapping comparison windows. The same feature rows survived mutations to the labels and audited comparison metrics. [Data tests](../tests/data/) · [Feature tests](../tests/features/)

All results describe fabricated data. FlyRank starter schema compatibility, observed missingness and real-data quality require an approved snapshot and owner review. [Data governance](../docs/governance/DATA_GOVERNANCE.md)
