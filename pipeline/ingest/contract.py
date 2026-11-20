from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

from pipeline.io import ContractError


INPUT_SCHEMA = "content-snapshot-v1"
TRANSFORM_VERSION = "snapshot-features-v1"
KEYS = ("client_id", "content_id")

# Comparison fields are admitted for input auditing only. See the feature allowlist.
COMPARISON_FIELDS = {
    f"{metric}_{window}_30d"
    for metric in ("impressions", "clicks", "sessions")
    for window in ("last", "prev")
}
RATE_UNITS = {
    "competition": "fraction",
    "ctr": "percent",
    "engagement_rate": "percent",
    "scroll_rate": "percent",
    "ai_traffic_pct": "percent",
    "trend_pct": "percent",
}


@dataclass(frozen=True)
class Numeric:
    minimum: float = 0
    maximum: float | None = None
    whole: bool = False


COUNT = Numeric(maximum=2**53 - 1, whole=True)
NUMERIC = {
    **dict.fromkeys(
        (
            "search_volume", "word_count", "char_count", "content_age_days",
            "days_since_last_update", "impressions_90d", "clicks_90d", "pageviews_90d",
            "sessions_90d", "users_90d", "engaged_sessions_90d", "ai_sessions_90d", "scroll_events_90d",
            *sorted(COMPARISON_FIELDS),
        ),
        COUNT,
    ),
    **dict.fromkeys(("days_with_impressions", "days_with_sessions"), Numeric(maximum=90, whole=True)),
    **dict.fromkeys(("ctr", "engagement_rate"), Numeric(maximum=100)),
    **dict.fromkeys(("cpc", "avg_position", "scroll_rate", "ai_traffic_pct"), Numeric()),
    "competition": Numeric(maximum=1),
    "trend_pct": Numeric(minimum=-100),
    "age_tier_order": Numeric(minimum=1, maximum=6, whole=True),
}
CATEGORIES = {
    "content_type": ("keyword article", "feedly article", "comparison article"),
    "competition_level": ("LOW", "MEDIUM", "HIGH"),
    "main_intent": ("informational", "transactional", "commercial", "navigational"),
    "age_tier": ("0-14", "15-30", "31-90", "91-180", "181-365", "365+"),
    "freshness_tier": ("never", "0-30", "31-90", "91-180", "181+"),
    "word_count_tier": ("<1000", "1000-2000", "2000-3500", "3500+"),
    "char_count_tier": ("<8000", "8000-15000", "15000-25000", "25000+"),
    "impression_tier": ("no_data", "none", "low", "moderate", "good", "excellent"),
    "position_tier": ("no_data", "top_3", "page_1", "striking", "page_3_5", "deep"),
    "trend_direction": ("new", "flat", "up", "down", "stable"),
}
OPTIONAL_COLUMNS = {
    "trend_direction", "trend_pct", "age_tier_order", "char_count_tier", "provider_used", "model_used",
    "pageviews_90d", "users_90d", "engaged_sessions_90d", "scroll_events_90d", *COMPARISON_FIELDS,
}
INPUT_COLUMNS = set(KEYS) | NUMERIC.keys() | CATEGORIES.keys() | {"provider_used", "model_used"}
REQUIRED_COLUMNS = INPUT_COLUMNS - OPTIONAL_COLUMNS
REQUIRED_VALUES = (*KEYS, "content_type", "content_age_days")


def validate_header(columns):
    column_set = set(columns)
    if len(columns) != len(column_set):
        raise ContractError("duplicate CSV headers")
    if column_set - INPUT_COLUMNS:
        raise ContractError("unexpected or forbidden CSV fields")
    if missing := REQUIRED_COLUMNS - column_set:
        raise ContractError(f"missing required CSV fields: {', '.join(sorted(missing))}")


def is_whole_number(value):
    try:
        number = Decimal(value)
    except InvalidOperation:
        return False
    return number.is_finite() and number == number.to_integral_value()


def validate_whole_numbers(columns, records):
    # Check the source text because conversion to DOUBLE can erase a fractional part.
    invalid = []
    for index, name in enumerate(columns):
        bounds = NUMERIC.get(name)
        if bounds is None or not bounds.whole:
            continue
        values = (record[index].strip() for record in records)
        if any(value and not is_whole_number(value) for value in values):
            invalid.append(name)
    if invalid:
        raise ContractError(f"invalid row fields: {', '.join(invalid)}")


def validate_rows(db, columns, row_count, clients):
    checks = {}
    for key in KEYS:
        checks[key] = f"{key} is null or not regexp_full_match({key}, '[A-Za-z0-9][A-Za-z0-9_.-]{{0,127}}')"
    for name in REQUIRED_VALUES[2:]:
        checks[f"missing {name}"] = f"{name} is null"
    for name, bounds in NUMERIC.items():
        if name not in columns:
            continue
        conditions = [f"{name} is null", f"not isfinite({name})", f"{name} < {bounds.minimum}"]
        if bounds.maximum is not None:
            conditions.append(f"{name} > {bounds.maximum}")
        checks[name] = f"text_{name} is not null and ({' or '.join(conditions)})"
    for name, values in CATEGORIES.items():
        if name in columns:
            choices = ", ".join(f"'{value}'" for value in values)
            checks[name] = f"{name} is not null and {name} not in ({choices})"
    checks["CTR percent reconciliation"] = """ctr is not null and (
        impressions_90d is null or clicks_90d is null
        or (impressions_90d = 0 and (clicks_90d <> 0 or ctr <> 0))
        or abs(ctr - 100 * clicks_90d / nullif(impressions_90d, 0)) > 0.0050001
    )"""
    checks["average position sentinel"] = "avg_position > 0 and avg_position < 1"
    expressions = ", ".join(f"count(*) filter (where {predicate})" for predicate in checks.values())
    count, *violations = db.execute(f"select count(*), {expressions} from typed_rows").fetchone()
    if count != row_count:
        raise ContractError("CSV row count differs from manifest")
    invalid = [name for name, n in zip(checks, violations, strict=True) if n]
    if invalid:
        raise ContractError(f"invalid row fields: {', '.join(invalid)}")
    duplicates = db.execute("""
        select 1 from typed_rows group by client_id, content_id having count(*) > 1 limit 1
    """).fetchone()
    if duplicates:
        raise ContractError("duplicate client/content key")
    observed = {row[0] for row in db.execute("select distinct client_id from typed_rows").fetchall()}
    if clients is not None and not observed.issubset(clients):
        raise ContractError("CSV contains clients outside the declared inventory")
    return tuple(sorted(observed if clients is None else clients))
