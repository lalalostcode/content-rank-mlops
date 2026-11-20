import hashlib
import json
import re
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from tempfile import TemporaryDirectory


class ContractError(ValueError):
    """A validation failure safe to print without source records or paths."""


IDENTIFIER = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,127}")
SHA256 = re.compile(r"[a-f0-9]{64}")


def matches(pattern, value):
    return isinstance(value, str) and pattern.fullmatch(value) is not None


def digest(payload):
    return hashlib.sha256(payload).hexdigest()


def json_bytes(value):
    return (json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n").encode()


def read_bytes(path, kind):
    try:
        return path.read_bytes()
    except OSError:
        raise ContractError(f"could not read {kind}") from None


def parse_object(payload, kind):
    def unique_pairs(pairs):
        obj = dict(pairs)
        if len(obj) != len(pairs):
            raise ValueError("duplicate JSON key")
        return obj

    def invalid_constant(token):
        raise ValueError(f"invalid JSON constant {token}")

    try:
        obj = json.loads(payload, object_pairs_hook=unique_pairs, parse_constant=invalid_constant)
    except (UnicodeError, ValueError):
        raise ContractError(f"invalid {kind} JSON") from None
    if not isinstance(obj, dict):
        raise ContractError(f"{kind} must be a JSON object")
    return obj


def utc_timestamp(value):
    try:
        if not isinstance(value, str) or "T" not in value:
            raise ValueError
        stamp = datetime.fromisoformat(value)
        if stamp.utcoffset() is None:
            raise ValueError
        return stamp.astimezone(UTC)
    except (ValueError, OverflowError):
        raise ContractError("timestamps must include a date, time and UTC offset") from None


def iso_utc(stamp):
    return stamp.astimezone(UTC).isoformat().replace("+00:00", "Z")


def local_filename(directory, name):
    if not matches(IDENTIFIER, name):
        raise ContractError("expected a plain local filename")
    resolved = (directory / name).resolve()
    if resolved.parent != directory.resolve():
        raise ContractError("file must resolve beside its manifest or artifact directory")
    return resolved


def outside_git(path):
    path = Path(path).resolve()
    if any((parent / ".git").exists() for parent in (path, *path.parents)):
        raise ContractError("data and run artifacts must be stored outside Git working trees")
    return path


@contextmanager
def new_output_directory(path):
    """Publish all files together at a fresh path on the same filesystem."""
    target = outside_git(path)
    if target.exists():
        raise ContractError("output directory already exists; specify a fresh directory")
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        with TemporaryDirectory(prefix=".ranking-", dir=target.parent) as temporary:
            staging = Path(temporary) / "run"
            staging.mkdir()
            yield staging
            staging.rename(target)
    except OSError:
        raise ContractError("could not publish the local output directory") from None
