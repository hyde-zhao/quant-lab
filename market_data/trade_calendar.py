"""CR139-S24 cross-source trade calendar and timezone consistency helpers."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import date, datetime
from typing import Any, Mapping, Sequence
from zoneinfo import ZoneInfo

import pandas as pd


@dataclass(frozen=True, slots=True)
class CalendarSourceSnapshot:
    source: str
    open_dates: tuple[str, ...]
    timezone: str = "Asia/Shanghai"
    normalized_timestamps: tuple[str, ...] = ()
    issues: tuple[dict[str, Any], ...] = ()
    row_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class CalendarConsistencyResult:
    passed: bool
    canonical_open_dates: tuple[str, ...]
    source_snapshots: tuple[CalendarSourceSnapshot, ...]
    mismatches: tuple[dict[str, Any], ...] = ()
    operation_counts: dict[str, int] = field(
        default_factory=lambda: {
            "provider_fetch": 0,
            "lake_write": 0,
            "catalog_write": 0,
            "manifest_write": 0,
            "pointer_advance": 0,
            "nas_operation": 0,
            "runtime_operation": 0,
            "git_remote_write": 0,
        }
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "canonical_open_dates": list(self.canonical_open_dates),
            "source_snapshots": [item.to_dict() for item in self.source_snapshots],
            "mismatches": [dict(item) for item in self.mismatches],
            "operation_counts": dict(self.operation_counts),
        }


def normalize_calendar_rows(
    source: str,
    rows: Sequence[Mapping[str, Any]] | pd.DataFrame,
    *,
    timezone: str = "Asia/Shanghai",
) -> CalendarSourceSnapshot:
    """Normalize one source calendar into sorted open dates and timezone-aware timestamps."""

    source_text = str(source).strip()
    zone = ZoneInfo(timezone)
    payload_rows = _rows(rows)
    open_dates: set[str] = set()
    normalized_timestamps: list[str] = []
    issues: list[dict[str, Any]] = []
    for index, row in enumerate(payload_rows):
        trade_date = _normalize_trade_date(row.get("trade_date") or row.get("date"))
        if not trade_date:
            issues.append({"code": "calendar_trade_date_missing", "source": source_text, "row_index": index})
            continue
        if _truthy_open(row.get("is_open", True)):
            open_dates.add(trade_date)
        timestamp_value = row.get("timestamp") or row.get("available_at") or row.get("updated_at")
        if timestamp_value not in (None, ""):
            normalized = _normalize_timestamp(timestamp_value, zone)
            if normalized is None:
                issues.append(
                    {
                        "code": "calendar_timestamp_unparseable",
                        "source": source_text,
                        "row_index": index,
                        "trade_date": trade_date,
                    }
                )
            else:
                normalized_timestamps.append(normalized)
    return CalendarSourceSnapshot(
        source=source_text,
        open_dates=tuple(sorted(open_dates)),
        timezone=timezone,
        normalized_timestamps=tuple(normalized_timestamps),
        issues=tuple(issues),
        row_count=len(payload_rows),
    )


def validate_cross_source_calendar(
    sources: Mapping[str, Sequence[Mapping[str, Any]] | pd.DataFrame],
    *,
    timezone: str = "Asia/Shanghai",
) -> CalendarConsistencyResult:
    """Compare open trade dates across sources without touching storage or providers."""

    snapshots = tuple(
        normalize_calendar_rows(source, rows, timezone=timezone)
        for source, rows in sorted(sources.items(), key=lambda item: str(item[0]))
    )
    canonical_dates = tuple(sorted({date_value for snapshot in snapshots for date_value in snapshot.open_dates}))
    mismatches: list[dict[str, Any]] = []
    for snapshot in snapshots:
        missing = sorted(set(canonical_dates) - set(snapshot.open_dates))
        extra = sorted(set(snapshot.open_dates) - set(canonical_dates))
        if missing:
            mismatches.append(
                {"code": "calendar_missing_open_date", "source": snapshot.source, "missing_open_dates": missing}
            )
        if extra:
            mismatches.append({"code": "calendar_extra_open_date", "source": snapshot.source, "extra_open_dates": extra})
        mismatches.extend(snapshot.issues)
    return CalendarConsistencyResult(
        passed=not mismatches and bool(snapshots),
        canonical_open_dates=canonical_dates,
        source_snapshots=snapshots,
        mismatches=tuple(mismatches),
    )


def _rows(rows: Sequence[Mapping[str, Any]] | pd.DataFrame) -> list[dict[str, Any]]:
    if isinstance(rows, pd.DataFrame):
        return [dict(item) for item in rows.to_dict("records")]
    return [dict(item) for item in rows]


def _normalize_trade_date(value: Any) -> str:
    if value in (None, ""):
        return ""
    text = str(value).strip()
    if len(text) == 8 and text.isdigit():
        return f"{text[:4]}-{text[4:6]}-{text[6:]}"
    parsed = pd.to_datetime(text, errors="coerce")
    if pd.isna(parsed):
        return ""
    return parsed.date().isoformat()


def _normalize_timestamp(value: Any, zone: ZoneInfo) -> str | None:
    parsed = pd.to_datetime(value, utc=False, errors="coerce")
    if pd.isna(parsed):
        return None
    timestamp = parsed.to_pydatetime() if hasattr(parsed, "to_pydatetime") else parsed
    if isinstance(timestamp, date) and not isinstance(timestamp, datetime):
        timestamp = datetime.combine(timestamp, datetime.min.time())
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=zone)
    return timestamp.astimezone(zone).isoformat()


def _truthy_open(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    return text not in {"0", "false", "n", "no", "closed", "close"}


__all__ = (
    "CalendarConsistencyResult",
    "CalendarSourceSnapshot",
    "normalize_calendar_rows",
    "validate_cross_source_calendar",
)
