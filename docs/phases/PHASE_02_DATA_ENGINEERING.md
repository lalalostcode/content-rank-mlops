# Phase 2 · DATA ENGINEERING

## Iteration 2.1 · Validate a snapshot

- **Objective and scope** — Validate a snapshot.
- **Prerequisite** — Phase 1 exit gate.
- **Tasks** — Implement manifest loader and DuckDB ingestion. Profile grain, nulls, units and ranges by content type. Reject duplicate keys and missing cutoffs.
- **Expected files and deliverable** — pipeline/ingest/, tests/data/, reports/profile.md.
- **Verification command** — `uv run pytest tests/data` from project root in PowerShell.
- **Automated test and acceptance criterion** — Synthetic valid input passes. Duplicate, wrong-unit and missing-key fixtures fail before publication.
- **Risk** — Percentage units mistaken for fractions.
- **Definition of done and exit gate** — Record the command result and review evidence against the acceptance criterion before proceeding.

## Iteration 2.2 · Produce model features

- **Objective and scope** — Produce model features.
- **Prerequisite** — 2.1.
- **Tasks** — Version SQL transformations and feature allowlist. Record availability and prohibit label reconstruction. Re-run against immutable input.
- **Expected files and deliverable** — pipeline/features/, tests/features/, docs/data-dictionary.md.
- **Verification command** — `uv run pytest tests/features` from project root in PowerShell.
- **Automated test and acceptance criterion** — Two runs match digests. Forbidden fields and overlapping time windows fail tests.
- **Risk** — Systematic missingness encoded as zero.
- **Definition of done and exit gate** — Record the command result and review evidence against the acceptance criterion before proceeding.
