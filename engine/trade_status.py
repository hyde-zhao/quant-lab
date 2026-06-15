"""交易状态约束 Provider。"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, Mapping

import pandas as pd

from engine.diagnostics import start_diagnostic
from engine.source_registry import require_resolved_registry_key, SourceRegistryError


class TradeStatusError(Exception):
    """交易状态数据错误。"""


@dataclass(slots=True)
class TradeStatusRecord:
    trade_date: date
    symbol: str
    can_buy: bool
    can_sell: bool
    reason: str = ""


@dataclass(frozen=True, slots=True)
class TradeStatusGateResult:
    """CR011-S03 交易状态 gate 结果。"""

    status: str
    can_buy: bool
    can_sell: bool
    reasons: tuple[str, ...] = ()
    suspended: bool = False
    st_status: bool = False
    no_trade: bool = False
    min_listing_days: bool = False
    delist_or_paused: bool = False
    details: dict[str, Any] | None = None

    @property
    def blocked_reason(self) -> str:
        return self.reasons[0] if self.reasons else ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "can_buy": self.can_buy,
            "can_sell": self.can_sell,
            "blocked_reason": self.blocked_reason,
            "blocked_reasons": list(self.reasons),
            "suspended": self.suspended,
            "st_status": self.st_status,
            "no_trade": self.no_trade,
            "min_listing_days": self.min_listing_days,
            "delist_or_paused": self.delist_or_paused,
            "details": dict(self.details or {}),
        }


@dataclass(slots=True)
class TradeStatusProvider:
    records: dict[tuple[date, str], TradeStatusRecord]
    missing_policy: str = "fail_closed"

    def get_trade_status(self, symbol: str, trade_date: date) -> TradeStatusRecord | None:
        return self.records.get((trade_date, symbol))

    def can_execute_trade(self, symbol: str, trade_date: date, side: str) -> tuple[bool, str]:
        record = self.get_trade_status(symbol, trade_date)
        if record is None:
            return (False, "trade_status_missing") if self.missing_policy == "fail_closed" else (True, "")
        if side == "buy" and not record.can_buy:
            return False, record.reason or "buy_suspended"
        if side == "sell" and not record.can_sell:
            return False, record.reason or "sell_suspended"
        return True, ""


def evaluate_trade_status_gate(
    row: Mapping[str, Any],
    trade_status_result: Any,
    lifecycle_result: Any | None = None,
    *,
    min_listing_days: int = 0,
) -> TradeStatusGateResult:
    """评估停牌、ST、无成交、上市天数和生命周期 gate。

    缺 reader result、缺 source/interface、空表、缺行或缺必需字段均 fail
    closed；不得把缺 trade_status / lifecycle 输入默认解释为可交易。
    """

    intent = _intent(row)
    required_issue = _reader_required_issue(trade_status_result, "trade_status")
    if required_issue:
        return _trade_gate_missing(required_issue, intent)
    frame = getattr(trade_status_result, "frame", None)
    if frame is None or frame.empty:
        return _trade_gate_missing("trade_status_empty", intent)
    work = frame.copy()
    missing_columns = [column for column in ("trade_date", "symbol", "available_at", "source_interface") if column not in work.columns]
    if missing_columns:
        reason = "available_at_missing" if "available_at" in missing_columns else "source_unresolved" if "source_interface" in missing_columns else "trade_status_schema_missing"
        return _trade_gate_missing(reason, intent, {"missing_columns": missing_columns})
    match = _match_trade_row(work, intent["trade_date"], intent["symbol"])
    if match is None:
        return _trade_gate_missing("trade_status_row_missing", intent)

    reasons: list[str] = []
    suspended = _truthy(match.get("is_suspended", match.get("suspended", False)))
    st_status = _truthy(match.get("is_st", match.get("st_status", False)))
    is_tradable = match.get("is_tradable", match.get("tradable", True))
    no_trade = _truthy(match.get("no_trade", False)) or _falsey(is_tradable) or _zero_value(match.get("volume")) or _zero_value(match.get("amount"))
    if suspended:
        reasons.append("suspended")
    if st_status:
        reasons.append("st_status")
    if no_trade:
        reasons.append("no_trade")

    lifecycle_reasons, lifecycle_details = _lifecycle_reasons(
        intent,
        lifecycle_result,
        min_listing_days=min_listing_days,
    )
    reasons.extend(lifecycle_reasons)
    can_buy = _bool_or_default(match.get("can_buy"), True)
    can_sell = _bool_or_default(match.get("can_sell"), True)
    if reasons:
        can_buy = False
        can_sell = False
    status = "blocked" if reasons else "available"
    return TradeStatusGateResult(
        status=status,
        can_buy=can_buy,
        can_sell=can_sell,
        reasons=tuple(dict.fromkeys(reasons)),
        suspended=suspended,
        st_status=st_status,
        no_trade=no_trade,
        min_listing_days="min_listing_days" in reasons,
        delist_or_paused="delist_or_paused" in reasons,
        details={
            "trade_date": intent["trade_date"],
            "symbol": intent["symbol"],
            "status_reason": str(match.get("status_reason") or match.get("reason") or ""),
            **lifecycle_details,
        },
    )


def _intent(row: Mapping[str, Any]) -> dict[str, str]:
    return {
        "trade_date": str(row.get("trade_date") or row.get("date") or ""),
        "symbol": str(row.get("symbol") or ""),
    }


def _reader_required_issue(result: Any, dataset: str) -> str:
    if result is None:
        return f"{dataset}_required_missing"
    status = str(getattr(result, "status", "") or "")
    if status != "available":
        for issue in getattr(result, "issues", []) or []:
            code = str(issue.get("code") or "")
            if code in {"w3_source_unresolved", "source_unresolved"}:
                return "source_unresolved"
            if code:
                return code
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


def _trade_gate_missing(reason: str, intent: Mapping[str, Any], details: Mapping[str, Any] | None = None) -> TradeStatusGateResult:
    return TradeStatusGateResult(
        status="required_missing",
        can_buy=False,
        can_sell=False,
        reasons=(reason,),
        details={"trade_date": intent.get("trade_date", ""), "symbol": intent.get("symbol", ""), **dict(details or {})},
    )


def _match_trade_row(frame: pd.DataFrame, trade_date: str, symbol: str) -> Mapping[str, Any] | None:
    work = frame.copy()
    dates = pd.to_datetime(work["trade_date"], errors="coerce").dt.strftime("%Y-%m-%d")
    mask = dates.eq(str(trade_date)) & work["symbol"].astype(str).eq(str(symbol))
    if not mask.any():
        return None
    return dict(work.loc[mask].iloc[-1])


def _lifecycle_reasons(
    intent: Mapping[str, str],
    lifecycle_result: Any | None,
    *,
    min_listing_days: int,
) -> tuple[list[str], dict[str, Any]]:
    if lifecycle_result is None:
        return [], {}
    missing = _reader_required_issue(lifecycle_result, "stock_lifecycle")
    if missing:
        return [missing], {"lifecycle_status": missing}
    frame = getattr(lifecycle_result, "frame", None)
    if frame is None or frame.empty:
        return ["lifecycle_missing"], {"lifecycle_status": "lifecycle_missing"}
    work = frame.copy()
    if "ts_code" in work.columns and "symbol" not in work.columns:
        work["symbol"] = work["ts_code"]
    missing_columns = [column for column in ("symbol", "list_date", "list_status", "available_at") if column not in work.columns]
    if missing_columns:
        return ["lifecycle_missing"], {"lifecycle_status": "lifecycle_missing", "missing_columns": missing_columns}
    mask = work["symbol"].astype(str).eq(str(intent["symbol"]))
    if not mask.any():
        return ["lifecycle_missing"], {"lifecycle_status": "lifecycle_missing"}
    latest = dict(work.loc[mask].iloc[-1])
    trade_date = _parse_date(intent["trade_date"])
    list_date = _parse_date(latest.get("list_date"))
    delist_date = _parse_date(latest.get("delist_date"))
    available_at = _parse_date(latest.get("available_at"))
    reasons: list[str] = []
    listing_days = None
    status_text = _normalize_lifecycle_status(latest.get("list_status"))
    if trade_date is None or list_date is None or available_at is None:
        reasons.append("lifecycle_missing")
    if trade_date is not None and available_at is not None and available_at > trade_date:
        reasons.append("source_unresolved")
    if status_text != "active":
        reasons.append("delist_or_paused")
    if trade_date is not None and list_date is not None:
        listing_days = (trade_date - list_date).days
        if listing_days < int(min_listing_days):
            reasons.append("min_listing_days")
    if trade_date is not None and delist_date is not None and delist_date <= trade_date:
        reasons.append("delist_or_paused")
    return reasons, {
        "lifecycle_status": "blocked" if reasons else "pass",
        "listing_days": listing_days,
        "min_listing_days": int(min_listing_days),
        "list_status": str(latest.get("list_status") or ""),
    }


def _parse_date(value: Any) -> date | None:
    if value is None or pd.isna(value):
        return None
    if isinstance(value, date):
        return value
    parsed = pd.to_datetime(pd.Series([value]), errors="coerce")
    if parsed.isna().iloc[0]:
        return None
    return parsed.dt.date.iloc[0]


def _normalize_lifecycle_status(value: Any) -> str:
    text = str(value or "").strip().lower()
    if text in {"l", "listed", "active", "上市"}:
        return "active"
    if text in {"d", "delisted", "退市", "p", "paused", "暂停", "暂停上市"}:
        return "blocked"
    return "unknown"


def _truthy(value: Any) -> bool:
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "t", "yes", "y", "是", "st", "suspended"}
    return bool(value)


def _falsey(value: Any) -> bool:
    if isinstance(value, str):
        return value.strip().lower() in {"0", "false", "f", "no", "n", "否", "停牌", "suspended"}
    return value is False


def _zero_value(value: Any) -> bool:
    if value is None or pd.isna(value):
        return False
    try:
        return float(value) == 0.0
    except (TypeError, ValueError):
        return False


def _bool_or_default(value: Any, default: bool) -> bool:
    if value is None or pd.isna(value):
        return default
    if isinstance(value, str):
        text = value.strip().lower()
        if text in {"1", "true", "t", "yes", "y"}:
            return True
        if text in {"0", "false", "f", "no", "n"}:
            return False
    return bool(value)


def load_trade_status(path: str | Path, *, require_registry: bool = True) -> TradeStatusProvider:
    diag = start_diagnostic(
        "trade_status",
        "STORY-010",
        {"path": Path(path), "require_registry": require_registry},
    )
    try:
        if require_registry:
            _require_registry()
        try:
            frame = pd.read_parquet(path, engine="pyarrow") if str(path).endswith(".parquet") else pd.read_csv(path)
        except FileNotFoundError as exc:
            raise TradeStatusError(f"交易状态文件不存在: {Path(path)}") from exc
        required = ("trade_date", "symbol", "can_buy", "can_sell")
        missing = [field for field in required if field not in frame.columns]
        if missing:
            raise TradeStatusError("交易状态缺少字段: " + ", ".join(missing))
        records: dict[tuple[date, str], TradeStatusRecord] = {}
        for row in frame.to_dict(orient="records"):
            trade_date = pd.to_datetime(row["trade_date"]).date()
            symbol = str(row["symbol"])
            records[(trade_date, symbol)] = TradeStatusRecord(
                trade_date=trade_date,
                symbol=symbol,
                can_buy=bool(row["can_buy"]),
                can_sell=bool(row["can_sell"]),
                reason=str(row.get("reason") or row.get("status") or ""),
            )
        diag.end("success", record_count=len(records))
        return TradeStatusProvider(records)
    except Exception as exc:
        diag.error(exc)
        raise


def _require_registry() -> None:
    try:
        require_resolved_registry_key("trade_status")
    except SourceRegistryError as exc:
        raise TradeStatusError(str(exc)) from exc


__all__ = (
    "TradeStatusError",
    "TradeStatusGateResult",
    "TradeStatusProvider",
    "TradeStatusRecord",
    "evaluate_trade_status_gate",
    "load_trade_status",
)
