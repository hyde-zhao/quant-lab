"""涨跌停交易约束。"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any, Mapping

import pandas as pd

from engine.diagnostics import start_diagnostic
from engine.source_registry import require_resolved_registry_key, SourceRegistryError


class TradingConstraintError(Exception):
    """交易约束错误。"""


@dataclass(frozen=True, slots=True)
class PriceLimitGateResult:
    """CR011-S03 涨跌停 gate 结果。"""

    status: str
    can_buy: bool
    can_sell: bool
    reasons: tuple[str, ...] = ()
    limit_up: float | None = None
    limit_down: float | None = None
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
            "limit_up": self.limit_up,
            "limit_down": self.limit_down,
            "details": dict(self.details or {}),
        }


@dataclass(slots=True)
class LimitPriceProvider:
    frame: pd.DataFrame
    require_registry: bool = True

    def __post_init__(self) -> None:
        diag = start_diagnostic(
            "trading_constraints",
            "STORY-011",
            {"rows": len(self.frame), "require_registry": self.require_registry},
        )
        try:
            if self.require_registry:
                try:
                    require_resolved_registry_key("prices_limit")
                except SourceRegistryError as exc:
                    raise TradingConstraintError(str(exc)) from exc
            for field in ("trade_date", "symbol", "limit_up", "limit_down"):
                if field not in self.frame.columns:
                    raise TradingConstraintError(f"涨跌停数据缺少字段: {field}")
            self.frame["trade_date"] = pd.to_datetime(self.frame["trade_date"], errors="coerce").dt.date
            diag.end("success")
        except Exception as exc:
            diag.error(exc)
            raise

    def can_execute_trade(self, symbol: str, trade_date: date, side: str) -> tuple[bool, str]:
        row = self.frame[(self.frame["trade_date"] == trade_date) & (self.frame["symbol"].astype(str) == str(symbol))]
        if row.empty:
            return True, ""
        latest = row.iloc[-1]
        price = latest.get("close", None)
        if price is None or pd.isna(price):
            return True, ""
        if side == "buy" and float(price) >= float(latest["limit_up"]):
            return False, "limit_up_blocked_buy"
        if side == "sell" and float(price) <= float(latest["limit_down"]):
            return False, "limit_down_blocked_sell"
        return True, ""


def evaluate_price_limit_gate(row: Mapping[str, Any], prices_limit_result: Any) -> PriceLimitGateResult:
    """评估 planned side 与涨跌停约束。

    prices_limit 缺 source/interface、空表、缺行或缺 `limit_up/limit_down`
    时返回 `required_missing`，不得沿用旧 Provider 的缺行默认可交易行为。
    """

    intent = _intent(row)
    issue = _reader_required_issue(prices_limit_result, "prices_limit")
    if issue:
        return _price_gate_missing(issue, intent)
    frame = getattr(prices_limit_result, "frame", None)
    if frame is None or frame.empty:
        return _price_gate_missing("prices_limit_empty", intent)
    missing_columns = [column for column in ("trade_date", "symbol", "limit_up", "limit_down", "available_at", "source_interface") if column not in frame.columns]
    if missing_columns:
        reason = "available_at_missing" if "available_at" in missing_columns else "source_unresolved" if "source_interface" in missing_columns else "prices_limit_schema_missing"
        return _price_gate_missing(reason, intent, {"missing_columns": missing_columns})
    match = _match_price_row(frame, intent["trade_date"], intent["symbol"])
    if match is None:
        return _price_gate_missing("prices_limit_row_missing", intent)

    limit_up = _float_or_none(match.get("limit_up"))
    limit_down = _float_or_none(match.get("limit_down"))
    if limit_up is None or limit_down is None:
        return _price_gate_missing("prices_limit_schema_missing", intent, {"missing_columns": ["limit_up", "limit_down"]})
    can_buy = _bool_or_default(match.get("can_buy"), True)
    can_sell = _bool_or_default(match.get("can_sell"), True)
    reasons: list[str] = []
    if can_buy is False:
        reasons.append("limit_up_blocked_buy")
    if can_sell is False:
        reasons.append("limit_down_blocked_sell")

    side = intent["side"]
    execution_price = _float_or_none(row.get("execution_price", row.get("price", match.get("close"))))
    if side in {"buy", "sell"} and execution_price is None and not reasons:
        return _price_gate_missing("execution_price_missing", intent)
    if side == "buy" and execution_price is not None and execution_price >= limit_up:
        can_buy = False
        reasons.append("limit_up_blocked_buy")
    if side == "sell" and execution_price is not None and execution_price <= limit_down:
        can_sell = False
        reasons.append("limit_down_blocked_sell")

    normalized_reasons = tuple(dict.fromkeys(reasons))
    return PriceLimitGateResult(
        status="blocked" if normalized_reasons else "available",
        can_buy=can_buy,
        can_sell=can_sell,
        reasons=normalized_reasons,
        limit_up=limit_up,
        limit_down=limit_down,
        details={
            "trade_date": intent["trade_date"],
            "symbol": intent["symbol"],
            "side": side,
            "execution_price": execution_price,
        },
    )


def _intent(row: Mapping[str, Any]) -> dict[str, str]:
    return {
        "trade_date": str(row.get("trade_date") or row.get("date") or ""),
        "symbol": str(row.get("symbol") or ""),
        "side": str(row.get("side") or "hold").strip().lower(),
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


def _price_gate_missing(reason: str, intent: Mapping[str, Any], details: Mapping[str, Any] | None = None) -> PriceLimitGateResult:
    return PriceLimitGateResult(
        status="required_missing",
        can_buy=False,
        can_sell=False,
        reasons=(reason,),
        details={"trade_date": intent.get("trade_date", ""), "symbol": intent.get("symbol", ""), **dict(details or {})},
    )


def _match_price_row(frame: pd.DataFrame, trade_date: str, symbol: str) -> Mapping[str, Any] | None:
    work = frame.copy()
    dates = pd.to_datetime(work["trade_date"], errors="coerce").dt.strftime("%Y-%m-%d")
    mask = dates.eq(str(trade_date)) & work["symbol"].astype(str).eq(str(symbol))
    if not mask.any():
        return None
    return dict(work.loc[mask].iloc[-1])


def _float_or_none(value: Any) -> float | None:
    if value is None or pd.isna(value):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


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


__all__ = (
    "LimitPriceProvider",
    "PriceLimitGateResult",
    "TradingConstraintError",
    "evaluate_price_limit_gate",
)
