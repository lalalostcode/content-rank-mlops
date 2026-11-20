# Source and release policy

The internship starter dictionary describes 30,000 items, 44 fields, 32 clients and a trailing 90-day snapshot. Its code license and data terms have different scopes. Record owner approval, purpose, release identifier, checksum, observation cutoff, transform revision and retention date in a private manifest before ingest. Store inputs and derived row artifacts outside this Git tree. Restrict local volumes to the operator. Remove derived caches when approval expires. Review logs, notebooks, MLflow artifacts and built frontend assets for disclosure.

Identifiers serve joins, grouped splits and stable ordering only. Prohibit re-identification and third-party processing outside approved terms. Public builds consume independently generated fixtures with invented clients, dates and identifiers. Maintain separate synthetic and restricted run namespaces. Publish aggregate research results only after release review.

The warehouse card lists 78,835,655 daily records and requires acceptance of access conditions. Authorization for this project remains unverified. Temporal experiments depend on that authorization. [Warehouse terms](https://huggingface.co/datasets/FlyRank/internship-warehouse) · [Starter rules](https://github.com/lalalostcode/FlyrankAI_ML/blob/main/DATA_USE.md)
