import csv
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from io import BytesIO, TextIOWrapper
from pathlib import Path

import duckdb
import pandas as pd

from pipeline.ingest.contract import (
    INPUT_SCHEMA, KEYS, NUMERIC, RATE_UNITS, TRANSFORM_VERSION,
    validate_header, validate_rows, validate_whole_numbers,
)
from pipeline.io import (
    ContractError, IDENTIFIER, SHA256, digest, iso_utc, local_filename, matches, outside_git,
    parse_object, read_bytes, utc_timestamp,
)


@dataclass(frozen=True)
class Snapshot:
    identity: dict
    rows: pd.DataFrame
    clients: tuple[str, ...]


def windows_at(cutoff):
    return {
        name: {"start": iso_utc(cutoff - timedelta(days=start)), "end": iso_utc(cutoff - timedelta(days=end))}
        for name, start, end in (("snapshot_90d", 90, 0), ("previous_30d", 60, 30), ("recent_30d", 30, 0))
    }


def validate_windows(windows, cutoff):
    try:
        expected = windows_at(cutoff)
    except OverflowError:
        raise ContractError("cutoff is out of range for the observation windows") from None
    if not isinstance(windows, dict) or windows.keys() != expected.keys():
        raise ContractError("manifest must declare all three observation windows")
    for name, bounds in windows.items():
        if not isinstance(bounds, dict) or bounds.keys() != {"start", "end"}:
            raise ContractError("observation windows require start and end")
        normalized = {bound: iso_utc(utc_timestamp(value)) for bound, value in bounds.items()}
        if normalized != expected[name]:
            raise ContractError("observation windows are shifted, overlapping comparisons, or past the cutoff")
    return expected


def validate_retention(value, *, minimum):
    try:
        retention = date.fromisoformat(value)
    except (TypeError, ValueError):
        raise ContractError("retention date must be an ISO date") from None
    if retention < max(minimum, datetime.now(UTC).date()):
        raise ContractError("restricted input approval has expired")


def validate_approval(approval, cutoff):
    if not isinstance(approval, dict) or set(approval) != {"reference", "purpose", "retention_until"}:
        raise ContractError("restricted input requires an approval reference, purpose and retention date")
    if not all(isinstance(approval[key], str) and approval[key].strip() for key in approval):
        raise ContractError("restricted input approval fields must be nonempty")
    validate_retention(approval["retention_until"], minimum=cutoff.date())


def validate_manifest(manifest, path):
    if manifest.get("status") == "pending" and "draft_input_manifest" in manifest:
        raise ContractError("input manifest is pending source cutoff and release approval")
    required = {
        "manifest_version", "snapshot_id", "source_release", "kind", "input_schema", "transform_version",
        "dataset", "sha256", "row_count", "cutoff", "windows", "rate_units",
    }
    if required - manifest.keys() or manifest.keys() - required - {"client_ids", "approval"}:
        raise ContractError("input manifest has missing or unexpected fields")
    if (type(manifest["manifest_version"]) is not int or manifest["manifest_version"] != 1
            or manifest["input_schema"] != INPUT_SCHEMA or manifest["transform_version"] != TRANSFORM_VERSION):
        raise ContractError("unsupported input manifest, schema or transform version")
    if not all(matches(IDENTIFIER, manifest[key]) for key in ("snapshot_id", "source_release")):
        raise ContractError("invalid snapshot or source release identifier")
    if not matches(SHA256, manifest["sha256"]):
        raise ContractError("manifest requires a lowercase SHA-256")
    if type(manifest["row_count"]) is not int or manifest["row_count"] < 0:
        raise ContractError("manifest requires a nonnegative integer row count")
    if manifest["rate_units"] != RATE_UNITS:
        raise ContractError("manifest rate units do not match the input schema")
    if manifest["cutoff"] is None:
        raise ContractError("snapshot cutoff is unknown. Obtain the source observation cutoff before ingestion")
    cutoff = utc_timestamp(manifest["cutoff"])
    windows = validate_windows(manifest["windows"], cutoff)
    if manifest["kind"] == "restricted":
        validate_approval(manifest.get("approval"), cutoff)
        outside_git(path)
    elif manifest["kind"] != "synthetic" or "approval" in manifest:
        raise ContractError("input kind must be synthetic or restricted with approval")
    dataset_path = local_filename(path.parent, manifest["dataset"])
    if dataset_path.suffix.lower() != ".csv":
        raise ContractError("snapshot dataset must be a CSV file")
    if manifest["kind"] == "restricted":
        outside_git(dataset_path)
    roster = manifest.get("client_ids")
    if "client_ids" in manifest:
        if (not isinstance(roster, list) or not all(matches(IDENTIFIER, name) for name in roster)
                or len(roster) != len(set(roster))):
            raise ContractError("client inventory must contain unique client identifiers")
    return dataset_path, cutoff, windows, None if roster is None else set(roster)


def read_rows(payload, row_count, roster):
    try:
        with TextIOWrapper(BytesIO(payload), encoding="utf-8-sig", newline="") as stream:
            reader = csv.reader(stream, strict=True)
            columns = next(reader)
            validate_header(columns)
            records = list(reader)
    except (StopIteration, UnicodeError, csv.Error):
        raise ContractError("malformed CSV or missing UTF-8 header") from None
    if any(len(record) != len(columns) for record in records):
        raise ContractError("malformed CSV or incompatible row width")
    validate_whole_numbers(columns, records)
    text_columns = [f"nullif(trim({name}), '') as {name}" for name in columns if name not in KEYS]
    typed_columns = [
        f"try_cast({name} as double) as {name}, {name} as text_{name}" if name in NUMERIC else name
        for name in columns
    ]
    try:
        with duckdb.connect(config={"threads": 1}) as db:
            db.register("input_rows", pd.DataFrame(records, columns=columns, dtype="str"))
            db.execute(f"create temp view normalized as select {', '.join((*KEYS, *text_columns))} from input_rows")
            db.execute(f"create temp table typed_rows as select {', '.join(typed_columns)} from normalized")
            clients = validate_rows(db, columns, row_count, roster)
            rows = db.execute(f"select {', '.join(sorted(columns))} from typed_rows order by client_id, content_id").df()
    except duckdb.Error:
        raise ContractError("snapshot could not be typed in DuckDB") from None
    # Preserve VARCHAR types when an entire column is null or the snapshot has no data rows.
    return rows.astype(dict.fromkeys(set(columns) - NUMERIC.keys(), "string")), clients


def load_snapshot(path, *, expected_kind=None):
    path = Path(path).resolve()
    manifest_bytes = read_bytes(path, "input manifest")
    manifest = parse_object(manifest_bytes, "input manifest")
    if expected_kind is not None and manifest.get("kind") != expected_kind:
        raise ContractError("snapshot and bundle must both be synthetic or both be restricted")
    dataset_path, cutoff, windows, roster = validate_manifest(manifest, path)
    payload = read_bytes(dataset_path, "snapshot CSV")
    if digest(payload) != manifest["sha256"]:
        raise ContractError("snapshot SHA-256 differs from input manifest")
    rows, clients = read_rows(payload, manifest["row_count"], roster)
    identity = {
        "snapshot_id": manifest["snapshot_id"], "source_release": manifest["source_release"],
        "kind": manifest["kind"], "input_schema": INPUT_SCHEMA, "dataset_sha256": manifest["sha256"],
        "manifest_sha256": digest(manifest_bytes), "cutoff": iso_utc(cutoff), "windows": windows,
    }
    if manifest["kind"] == "restricted":
        identity["retention_until"] = manifest["approval"]["retention_until"]
    return Snapshot(identity, rows, clients)
