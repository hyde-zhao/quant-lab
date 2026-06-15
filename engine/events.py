"""事件 available_at 存储与校验。"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Mapping

import pandas as pd

from engine.diagnostics import start_diagnostic
from engine.source_registry import require_resolved_registry_key, SourceRegistryError


class EventStoreError(Exception):
    """事件数据错误。"""


@dataclass(frozen=True, slots=True)
class EventGateResult:
    """CR011-S03 事件 available_at gate 结果。"""

    status: str
    event_blocked: bool
    reasons: tuple[str, ...] = ()
    matched_events: tuple[dict[str, Any], ...] = ()
    details: dict[str, Any] | None = None

    @property
    def blocked_reason(self) -> str:
        return self.reasons[0] if self.reasons else ""

    @property
    def can_buy(self) -> bool:
        return self.status == "available"

    @property
    def can_sell(self) -> bool:
        return self.status == "available"

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "event_blocked": self.event_blocked,
            "blocked_reason": self.blocked_reason,
            "blocked_reasons": list(self.reasons),
            "matched_events": list(self.matched_events),
            "details": dict(self.details or {}),
        }


@dataclass(slots=True)
class EventStore:
    frame: pd.DataFrame
    enabled: bool = False

    def __post_init__(self) -> None:
        diag = start_diagnostic("events", "STORY-011", {"rows": len(self.frame), "enabled": self.enabled})
        try:
            if self.enabled:
                try:
                    require_resolved_registry_key("events")
                except SourceRegistryError as exc:
                    raise EventStoreError(str(exc)) from exc
            if self.frame.empty:
                diag.warning("empty_targets", reason="empty_events_frame")
                diag.end("empty")
                return
            for field in ("event_date", "symbol", "event_type", "available_at"):
                if field not in self.frame.columns:
                    raise EventStoreError(f"事件数据缺少字段: {field}")
            self.frame["event_date"] = pd.to_datetime(self.frame["event_date"], errors="coerce").dt.date
            self.frame["available_at"] = pd.to_datetime(self.frame["available_at"], errors="coerce").dt.date
            diag.end("success")
        except Exception as exc:
            diag.error(exc)
            raise

    def available_events(self, as_of_date: str | date) -> pd.DataFrame:
        target = pd.to_datetime(as_of_date).date()
        if self.frame.empty:
            return self.frame.copy()
        return self.frame[self.frame["available_at"] <= target].copy()


def evaluate_event_gate(
    row: Mapping[str, Any],
    events_result: Any,
    *,
    decision_time: str | date | datetime | None = None,
) -> EventGateResult:
    """评估事件 explicit available_at gate。

    缺 reader result、缺 explicit `available_at` 或 source/interface 未冻结时
    返回 `required_missing`；future available_at 的事件以 blocked 暴露，避免
    用日期推导事件可得性。
    """

    intent = _intent(row, decision_time)
    issue = _reader_required_issue(events_result, "events")
    if issue:
        return _event_gate_missing(issue, intent)
    frame = getattr(events_result, "frame", None)
    if frame is None:
        return _event_gate_missing("events_required_missing", intent)
    required_columns = ("event_date", "symbol", "event_type", "available_at", "source_interface")
    missing_columns = [column for column in required_columns if column not in frame.columns]
    if missing_columns:
        reason = "available_at_missing" if "available_at" in missing_columns else "source_unresolved" if "source_interface" in missing_columns else "events_schema_missing"
        return _event_gate_missing(reason, intent, {"missing_columns": missing_columns})
    if frame.empty:
        return EventGateResult(
            status="available",
            event_blocked=False,
            details={"trade_date": intent["trade_date"], "symbol": intent["symbol"], "empty_events": True},
        )

    work = frame.copy()
    symbol_mask = work["symbol"].astype(str).eq(str(intent["symbol"]))
    event_dates = pd.to_datetime(work["event_date"], errors="coerce").dt.date
    trade_date = _parse_date(intent["trade_date"])
    decision = _parse_date(intent["decision_time"]) or trade_date
    if trade_date is not None:
        symbol_mask = symbol_mask & (event_dates <= trade_date)
    matched = work.loc[symbol_mask].copy()
    if matched.empty:
        return EventGateResult(
            status="available",
            event_blocked=False,
            details={"trade_date": intent["trade_date"], "symbol": intent["symbol"], "matched_event_count": 0},
        )
    available_at = pd.to_datetime(matched["available_at"], errors="coerce").dt.date
    if available_at.isna().any():
        return _event_gate_missing("available_at_missing", intent)
    if decision is None:
        return _event_gate_missing("decision_time_missing", intent)
    future_mask = available_at > decision
    if future_mask.any():
        future = matched.loc[future_mask].to_dict(orient="records")
        return EventGateResult(
            status="blocked",
            event_blocked=True,
            reasons=("event_future_available_at",),
            matched_events=tuple(_event_payload(item) for item in future),
            details={"trade_date": intent["trade_date"], "symbol": intent["symbol"], "decision_time": intent["decision_time"]},
        )

    blocking_mask = matched.apply(_is_blocking_event, axis=1)
    blocking = matched.loc[blocking_mask].to_dict(orient="records")
    if blocking:
        return EventGateResult(
            status="blocked",
            event_blocked=True,
            reasons=("event_blocked",),
            matched_events=tuple(_event_payload(item) for item in blocking),
            details={"trade_date": intent["trade_date"], "symbol": intent["symbol"], "decision_time": intent["decision_time"]},
        )
    return EventGateResult(
        status="available",
        event_blocked=False,
        matched_events=tuple(_event_payload(item) for item in matched.to_dict(orient="records")),
        details={"trade_date": intent["trade_date"], "symbol": intent["symbol"], "matched_event_count": int(len(matched))},
    )


def _intent(row: Mapping[str, Any], decision_time: str | date | datetime | None) -> dict[str, str]:
    trade_date = str(row.get("trade_date") or row.get("date") or "")
    effective_decision = row.get("decision_time") or decision_time or trade_date
    return {
        "trade_date": trade_date,
        "symbol": str(row.get("symbol") or ""),
        "decision_time": str(effective_decision or ""),
    }


def _reader_required_issue(result: Any, dataset: str) -> str:
    if result is None:
        return f"{dataset}_required_missing"
    status = str(getattr(result, "status", "") or "")
    for issue in getattr(result, "issues", []) or []:
        code = str(issue.get("code") or "")
        if code in {"available_at_missing", "w3_required_fields_missing"}:
            return "available_at_missing"
        if code in {"w3_source_unresolved", "source_unresolved"}:
            return "source_unresolved"
    if status != "available":
        return status or f"{dataset}_required_missing"
    frame = getattr(result, "frame", None)
    entry = getattr(result, "catalog_entry", None)
    source_interface = str(getattr(entry, "source_interface", "") or "").strip().upper()
    if source_interface in {"", "UNKNOWN", "UNRESOLVED"}:
        if frame is None or "source_interface" not in frame.columns or frame.empty:
            return "source_unresolved"
    if frame is not None and "source_interface" in frame.columns and not frame.empty:
        values = {str(value).strip().upper() for value in frame["source_interface"].dropna().unique() if str(value).strip()}
        if not values or values & {"UNKNOWN", "UNRESOLVED"}:
            return "source_unresolved"
    return ""


def _event_gate_missing(reason: str, intent: Mapping[str, Any], details: Mapping[str, Any] | None = None) -> EventGateResult:
    return EventGateResult(
        status="required_missing",
        event_blocked=False,
        reasons=(reason,),
        details={
            "trade_date": intent.get("trade_date", ""),
            "symbol": intent.get("symbol", ""),
            "decision_time": intent.get("decision_time", ""),
            **dict(details or {}),
        },
    )


def _parse_date(value: Any) -> date | None:
    if value is None or pd.isna(value):
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    parsed = pd.to_datetime(pd.Series([value]), errors="coerce")
    if parsed.isna().iloc[0]:
        return None
    return parsed.dt.date.iloc[0]


def _is_blocking_event(row: pd.Series) -> bool:
    if _truthy(row.get("is_blocking")) or _truthy(row.get("event_blocked")):
        return True
    event_type = str(row.get("event_type") or "").strip().lower()
    return event_type in {"suspension", "halt", "risk_warning", "st", "delist", "pause", "paused"}


def _event_payload(row: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "symbol": str(row.get("symbol") or ""),
        "event_type": str(row.get("event_type") or ""),
        "event_date": str(row.get("event_date") or ""),
        "available_at": str(row.get("available_at") or ""),
        "source_run_id": str(row.get("source_run_id") or ""),
    }


def _truthy(value: Any) -> bool:
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "t", "yes", "y"}
    return bool(value)


__all__ = (
    "EventGateResult",
    "EventStore",
    "EventStoreError",
    "evaluate_event_gate",
)
