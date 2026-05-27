"""CR014 最近已闭市交易日合同。"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time
from typing import Any, Mapping, Sequence

from .contracts import (
    CR014_CLAIM_FULL_A_SINCE_INCEPTION,
    CR014_CURRENT_TRADE_DATE_POLICY_LAST_CLOSED,
    CR014_CURRENT_TRADE_DATE_UNAVAILABLE,
    CR014_REQUIRED_MISSING_CALENDAR,
)
from .lifecycle import BlockedClaim, RequiredMissingItem


@dataclass(frozen=True, slots=True)
class CurrentTruthAsOf:
    as_of_trade_date: str | None
    current_trade_date_policy: str
    calendar_source: str | None
    required_missing: tuple[RequiredMissingItem, ...]
    blocked_claims: tuple[BlockedClaim, ...]
    allowed_claims: dict[str, bool]

    @property
    def passed(self) -> bool:
        return self.as_of_trade_date is not None and not self.required_missing

    @property
    def full_a_allowed_claim_count(self) -> int:
        return int(bool(self.allowed_claims.get(CR014_CLAIM_FULL_A_SINCE_INCEPTION)))


def _parse_close_time(value: str | time) -> time:
    if isinstance(value, time):
        return value
    return time.fromisoformat(value)


def _parse_iso_date(value: object) -> date:
    if not isinstance(value, str) or not value:
        raise ValueError("trade_date must be YYYY-MM-DD")
    return date.fromisoformat(value)


def _is_open(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return value == 1
    if isinstance(value, str):
        return value.lower() in {"1", "true", "t", "yes", "y"}
    return False


def _blocked_calendar(code: str, field: str, now: datetime) -> CurrentTruthAsOf:
    missing = RequiredMissingItem(
        code=code,
        field=field,
        as_of_trade_date=now.date().isoformat(),
        unblock_condition="provide_closed_open_trade_calendar",
    )
    blocked = BlockedClaim(
        claim=CR014_CLAIM_FULL_A_SINCE_INCEPTION,
        reason_code=code,
        field=field,
        as_of_trade_date=now.date().isoformat(),
        unblock_condition="resolve_calendar_before_current_truth_claim",
    )
    return CurrentTruthAsOf(
        as_of_trade_date=None,
        current_trade_date_policy=CR014_CURRENT_TRADE_DATE_POLICY_LAST_CLOSED,
        calendar_source=None,
        required_missing=(missing,),
        blocked_claims=(blocked,),
        allowed_claims={CR014_CLAIM_FULL_A_SINCE_INCEPTION: False},
    )


def resolve_current_truth_as_of(
    calendar_rows: Sequence[Mapping[str, Any]],
    now: datetime,
    market_close_time: str | time = "15:00:00",
) -> CurrentTruthAsOf:
    """返回最近已闭市且 is_open=true 的交易日；盘中当日不作为 current truth。"""

    if not calendar_rows:
        return _blocked_calendar(CR014_REQUIRED_MISSING_CALENDAR, "calendar_rows", now)

    close_time = _parse_close_time(market_close_time)
    candidates: list[tuple[date, Mapping[str, Any]]] = []
    for row in calendar_rows:
        if "trade_date" not in row or "is_open" not in row:
            return _blocked_calendar(CR014_REQUIRED_MISSING_CALENDAR, "trade_date/is_open", now)
        trade_date = _parse_iso_date(row["trade_date"])
        if not _is_open(row.get("is_open")):
            continue
        if trade_date > now.date():
            continue
        if trade_date == now.date() and now.time() < close_time:
            continue
        candidates.append((trade_date, row))

    if not candidates:
        return _blocked_calendar(CR014_CURRENT_TRADE_DATE_UNAVAILABLE, "market_close_time", now)

    trade_date, row = max(candidates, key=lambda item: item[0])
    return CurrentTruthAsOf(
        as_of_trade_date=trade_date.isoformat(),
        current_trade_date_policy=CR014_CURRENT_TRADE_DATE_POLICY_LAST_CLOSED,
        calendar_source=str(row.get("calendar_source") or row.get("source") or "in_memory_calendar"),
        required_missing=(),
        blocked_claims=(),
        allowed_claims={CR014_CLAIM_FULL_A_SINCE_INCEPTION: True},
    )


__all__ = [
    "CurrentTruthAsOf",
    "resolve_current_truth_as_of",
]
