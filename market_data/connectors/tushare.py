"""Tushare adapter fail-fast 与显式真实写湖边界。"""

from __future__ import annotations

import json
import os
from collections.abc import Callable
from datetime import date, datetime, timedelta
from typing import Any

from ..contracts import (
    DATASET_EVENTS,
    DATASET_INDEX_MEMBERS,
    DATASET_PRICES_LIMIT,
    DATASET_TRADE_STATUS,
    INTERFACE_EVENTS_DISCLOSURE,
    INTERFACE_HS300_INDEX_DAILY,
    INTERFACE_INDEX_MEMBERS_SNAPSHOT,
    INTERFACE_INDEX_WEIGHTS_SNAPSHOT,
    INTERFACE_PRICES_LIMIT_DAILY,
    INTERFACE_PRICES_ADJ_FACTOR,
    INTERFACE_PRICES_DAILY,
    INTERFACE_STOCK_BASIC_SNAPSHOT,
    INTERFACE_TRADE_STATUS_DAILY,
    INTERFACE_TRADE_CALENDAR_DAILY,
    PIT_STATUS_AVAILABLE,
    READINESS_STATUS_AVAILABLE,
)
from .protocol import AdapterConfig, ConnectorError, ConnectorRequest, ConnectorResult

ProviderFactory = Callable[[str], object]


def _compact_date(value: object) -> str:
    text = str(value)
    if len(text) == 8 and text.isdigit():
        return text
    if len(text) >= 10 and text[4] == "-" and text[7] == "-":
        return text[:10].replace("-", "")
    return text


def _parse_date(value: object) -> date:
    text = str(value).strip()
    if len(text) == 8 and text.isdigit():
        return datetime.strptime(text, "%Y%m%d").date()
    if len(text) >= 10 and text[4] == "-" and text[7] == "-":
        return date.fromisoformat(text[:10])
    raise ValueError(f"invalid date: {value}")


def _date_text(value: object) -> str:
    return _parse_date(value).isoformat()


def _date_values(start: object, end: object) -> list[str]:
    cursor = _parse_date(start)
    final = _parse_date(end)
    values: list[str] = []
    while cursor <= final:
        values.append(cursor.isoformat())
        cursor += timedelta(days=1)
    return values


def _timestamp_at(day: object, time_text: str) -> str:
    return f"{_date_text(day)}T{time_text}+08:00"


def _value(row: dict[str, Any], *names: str, default: object = None) -> object:
    for name in names:
        value = row.get(name)
        if value not in (None, ""):
            return value
    return default


def _float_value(value: object) -> float | None:
    if value in (None, ""):
        return None
    return float(value)


def _bool_value(value: object, *, default: bool = False) -> bool:
    if value in (None, ""):
        return default
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if text in {"1", "true", "yes", "y", "t", "st", "s", "suspend", "suspended"}:
        return True
    if text in {"0", "false", "no", "n", "f", "r", "resume", "resumed"}:
        return False
    return default


def _symbol_value(row: dict[str, Any]) -> str:
    return str(_value(row, "symbol", "ts_code", "con_code", default="")).strip().upper()


def _symbols_from_params(params: dict[str, Any]) -> list[str]:
    symbols = params.get("symbols")
    if isinstance(symbols, str):
        values = [item.strip().upper() for item in symbols.split(",") if item.strip()]
    elif isinstance(symbols, (list, tuple, set)):
        values = [str(item).strip().upper() for item in symbols if str(item).strip()]
    else:
        values = []
    single = params.get("symbol") or params.get("ts_code")
    if single:
        values.append(str(single).strip().upper())
    return sorted(set(values))


def _rows_from_provider_result(value: object) -> list[dict[str, Any]]:
    if hasattr(value, "to_dict"):
        records = value.to_dict("records")  # pandas DataFrame 兼容路径
        return [dict(item) for item in records]
    if isinstance(value, list):
        return [dict(item) for item in value]
    if isinstance(value, tuple):
        return [dict(item) for item in value]
    return []


class TushareAdapter:
    source = "tushare"

    def __init__(
        self,
        config: AdapterConfig | None = None,
        *,
        provider_factory: ProviderFactory | None = None,
    ) -> None:
        self.config = config or AdapterConfig(
            source=self.source,
            credential_env_vars=("TUSHARE_TOKEN",),
        )
        self._provider_factory = provider_factory
        self._provider_instance: object | None = None

    def fetch(self, request: ConnectorRequest) -> ConnectorResult | ConnectorError:
        if not self.config.enabled:
            return ConnectorError(
                "source_disabled",
                "tushare source is disabled by default",
                False,
                request.source,
                request.interface,
            )
        if bool(request.params.get("offline", False)):
            return ConnectorError(
                "source_disabled",
                "tushare real fetch requires offline=false",
                False,
                request.source,
                request.interface,
            )
        if request.interface not in self.config.allow_interfaces:
            return ConnectorError(
                "interface_not_allowed",
                "tushare interface is not allowlisted",
                False,
                request.source,
                request.interface,
            )
        missing = [
            name for name in self.config.credential_env_vars if not os.environ.get(name)
        ]
        if missing:
            return ConnectorError(
                "missing_credential",
                f"missing credential env var: {','.join(missing)}",
                False,
                request.source,
                request.interface,
            )
        if not request.params.get("explicit_real_execution"):
            return ConnectorError(
                "source_disabled",
                "tushare real fetch requires explicit_real_execution=true",
                False,
                request.source,
                request.interface,
            )
        try:
            rows = self._fetch_provider_rows(request)
        except RuntimeError as exc:
            text = str(exc).lower()
            error_type = (
                "quota_or_rate_limited"
                if any(marker in text for marker in ("rate", "quota", "积分", "limit"))
                else "remote_error"
            )
            return ConnectorError(
                error_type,
                "tushare provider call failed; see controlled runtime logs",
                True,
                request.source,
                request.interface,
            )
        except Exception:
            return ConnectorError(
                "remote_error",
                "tushare provider call failed; see controlled runtime logs",
                True,
                request.source,
                request.interface,
            )
        return ConnectorResult(
            source=request.source,
            interface=request.interface,
            rows=rows,
            metadata={
                "provider": "tushare",
                "provider_interface": self._provider_method(request.interface),
                "target_dataset": request.params.get("target_dataset"),
            },
        )

    def _provider(self) -> object:
        if self._provider_instance is not None:
            return self._provider_instance
        token_env = self.config.credential_env_vars[0] if self.config.credential_env_vars else ""
        if self._provider_factory is not None:
            self._provider_instance = self._provider_factory(token_env)
            return self._provider_instance
        import importlib

        module = importlib.import_module("tushare")
        token = os.environ.get(token_env) if token_env else None
        if hasattr(module, "pro_api"):
            self._provider_instance = module.pro_api(token)
            return self._provider_instance
        error = ConnectorError(
            "remote_error",
            "tushare provider does not expose pro_api",
            True,
            self.source,
            "",
        )
        self._provider_instance = error
        return error

    def _provider_method(self, interface: str) -> str:
        return {
            INTERFACE_HS300_INDEX_DAILY: "index_daily",
            INTERFACE_PRICES_DAILY: "daily",
            INTERFACE_PRICES_ADJ_FACTOR: "adj_factor",
            INTERFACE_TRADE_CALENDAR_DAILY: "trade_cal",
            INTERFACE_INDEX_MEMBERS_SNAPSHOT: "index_weight",
            INTERFACE_INDEX_WEIGHTS_SNAPSHOT: "index_weight",
            INTERFACE_STOCK_BASIC_SNAPSHOT: "stock_basic",
            INTERFACE_TRADE_STATUS_DAILY: "suspend_d+stock_st+daily",
            INTERFACE_PRICES_LIMIT_DAILY: "stk_limit",
            INTERFACE_EVENTS_DISCLOSURE: "stock_st",
        }.get(interface, interface)

    def _fetch_provider_rows(self, request: ConnectorRequest) -> list[dict[str, Any]]:
        provider = self._provider()
        if isinstance(provider, ConnectorError):
            raise RuntimeError(provider.error_message)
        if request.interface == INTERFACE_TRADE_STATUS_DAILY:
            return self._fetch_trade_status(provider, request)
        if request.interface == INTERFACE_PRICES_LIMIT_DAILY:
            return self._fetch_prices_limit(provider, request)
        if request.interface == INTERFACE_EVENTS_DISCLOSURE:
            return self._fetch_events(provider, request)
        method_name = self._provider_method(request.interface)
        method = getattr(provider, method_name)
        params = dict(request.params)
        if request.interface == INTERFACE_HS300_INDEX_DAILY:
            value = method(
                ts_code=str(params.get("index_code", "399300.SZ")).strip().upper(),
                start_date=_compact_date(params.get("start_date")),
                end_date=_compact_date(params.get("end_date")),
            )
        elif request.interface == INTERFACE_PRICES_DAILY:
            value = method(
                ts_code=params.get("symbol") or params.get("ts_code"),
                start_date=_compact_date(params.get("start_date")),
                end_date=_compact_date(params.get("end_date")),
            )
        elif request.interface == INTERFACE_PRICES_ADJ_FACTOR:
            value = method(
                ts_code=params.get("symbol") or params.get("ts_code"),
                start_date=_compact_date(params.get("start_date")),
                end_date=_compact_date(params.get("end_date")),
            )
        elif request.interface == INTERFACE_TRADE_CALENDAR_DAILY:
            value = method(
                exchange=params.get("exchange", "SSE"),
                start_date=_compact_date(params.get("start_date")),
                end_date=_compact_date(params.get("end_date")),
            )
        elif request.interface in {INTERFACE_INDEX_MEMBERS_SNAPSHOT, INTERFACE_INDEX_WEIGHTS_SNAPSHOT}:
            value = method(
                index_code=str(params.get("index_code", "399300.SZ")).strip().upper(),
                start_date=_compact_date(params.get("start_date")),
                end_date=_compact_date(params.get("end_date")),
            )
        elif request.interface == INTERFACE_STOCK_BASIC_SNAPSHOT:
            call_params = {
                "exchange": params.get("exchange", ""),
                "list_status": params.get("list_status", "L"),
            }
            if params.get("fields"):
                call_params["fields"] = params.get("fields")
            value = method(**call_params)
        else:
            raise RuntimeError("interface is not mapped to tushare provider")
        return _rows_from_provider_result(value)

    def _provider_rows_for_symbol_range(
        self,
        provider: object,
        method_name: str,
        symbols: list[str],
        start: str,
        end: str,
    ) -> list[dict[str, Any]]:
        method = getattr(provider, method_name)
        rows: list[dict[str, Any]] = []
        for symbol in symbols:
            value = method(
                ts_code=symbol,
                start_date=_compact_date(start),
                end_date=_compact_date(end),
            )
            rows.extend(_rows_from_provider_result(value))
        return rows

    def _fetch_trade_status(self, provider: object, request: ConnectorRequest) -> list[dict[str, Any]]:
        params = dict(request.params)
        start = _date_text(params.get("start_date"))
        end = _date_text(params.get("end_date"))
        symbols = _symbols_from_params(params)
        if not symbols:
            raise RuntimeError("trade_status requires explicit symbols")

        daily_rows = self._provider_rows_for_symbol_range(provider, "daily", symbols, start, end)
        suspend_rows = self._provider_rows_for_symbol_range(provider, "suspend_d", symbols, start, end)
        st_rows = self._provider_rows_for_symbol_range(provider, "stock_st", symbols, start, end)

        keys: set[tuple[str, str]] = set()
        for row in [*daily_rows, *suspend_rows, *st_rows]:
            symbol = _symbol_value(row)
            raw_day = _value(row, "trade_date", "date", "cal_date", "start_date")
            if symbol and raw_day not in (None, ""):
                keys.add((_date_text(raw_day), symbol))

        st_lookup = self._st_status_lookup(st_rows, symbols, start, end)
        suspended_lookup: dict[tuple[str, str], bool] = {}
        for row in suspend_rows:
            symbol = _symbol_value(row)
            raw_day = _value(row, "trade_date", "date", "suspend_date", "ann_date")
            if not symbol or raw_day in (None, ""):
                continue
            suspend_type = _value(row, "suspend_type", "status", "type", default="")
            is_suspended = _bool_value(
                _value(row, "is_suspended", "suspend", default=suspend_type),
                default=str(suspend_type).strip().upper() != "R",
            )
            suspended_lookup[(_date_text(raw_day), symbol)] = is_suspended

        rows: list[dict[str, Any]] = []
        for day, symbol in sorted(keys):
            is_suspended = suspended_lookup.get((day, symbol), False)
            is_st = st_lookup.get((day, symbol), False)
            reasons = [
                label
                for label, active in (("suspended", is_suspended), ("st", is_st))
                if active
            ]
            rows.append(
                {
                    "trade_date": day,
                    "symbol": symbol,
                    "is_tradable": not is_suspended,
                    "is_suspended": is_suspended,
                    "is_st": is_st,
                    "status_reason": ",".join(reasons) if reasons else "normal",
                    "available_at": _timestamp_at(day, "09:30:00"),
                    "available_at_rule": "tushare_suspend_d_09:30_stock_st_09:20_daily",
                }
            )
        return rows

    def _fetch_prices_limit(self, provider: object, request: ConnectorRequest) -> list[dict[str, Any]]:
        params = dict(request.params)
        start = _date_text(params.get("start_date"))
        end = _date_text(params.get("end_date"))
        symbols = _symbols_from_params(params)
        if not symbols:
            raise RuntimeError("prices_limit requires explicit symbols")
        raw_rows = self._provider_rows_for_symbol_range(provider, "stk_limit", symbols, start, end)
        rows: list[dict[str, Any]] = []
        for row in raw_rows:
            trade_date = _date_text(_value(row, "trade_date", "date"))
            symbol = _symbol_value(row)
            limit_up = _float_value(_value(row, "limit_up", "up_limit", "high_limit"))
            limit_down = _float_value(_value(row, "limit_down", "down_limit", "low_limit"))
            if not symbol or limit_up is None or limit_down is None:
                continue
            rows.append(
                {
                    "trade_date": trade_date,
                    "symbol": symbol,
                    "limit_up": limit_up,
                    "limit_down": limit_down,
                    "available_at": _timestamp_at(trade_date, "08:40:00"),
                    "available_at_rule": "tushare_stk_limit_08:40",
                }
            )
        return rows

    def _fetch_events(self, provider: object, request: ConnectorRequest) -> list[dict[str, Any]]:
        params = dict(request.params)
        start = _date_text(params.get("start_date"))
        end = _date_text(params.get("end_date"))
        symbols = _symbols_from_params(params)
        if not symbols:
            raise RuntimeError("events requires explicit symbols")
        st_rows = self._provider_rows_for_symbol_range(provider, "stock_st", symbols, start, end)
        interval_events = self._events_from_st_intervals(st_rows, start, end)
        if interval_events:
            return interval_events
        lookup = self._st_status_lookup(st_rows, symbols, start, end, daily_only=True)
        rows: list[dict[str, Any]] = []
        previous: dict[str, bool] = {}
        for symbol in symbols:
            for day in _date_values(start, end):
                key = (day, symbol)
                if key not in lookup:
                    continue
                is_st = lookup[key]
                if symbol in previous and previous[symbol] == is_st:
                    continue
                if symbol not in previous and not is_st:
                    previous[symbol] = is_st
                    continue
                event_type = "st_enter" if is_st else "st_exit"
                rows.append(self._st_event_row(symbol, event_type, day, {"source_event": "stock_st", "is_st": is_st}))
                previous[symbol] = is_st
        return rows

    def _st_status_lookup(
        self,
        st_rows: list[dict[str, Any]],
        symbols: list[str],
        start: str,
        end: str,
        *,
        daily_only: bool = False,
    ) -> dict[tuple[str, str], bool]:
        lookup: dict[tuple[str, str], bool] = {}
        for row in st_rows:
            symbol = _symbol_value(row)
            if not symbol:
                continue
            if row.get("trade_date") not in (None, ""):
                lookup[(_date_text(row["trade_date"]), symbol)] = _bool_value(
                    _value(row, "is_st", "st", "status", default=True),
                    default=True,
                )
                continue
            if daily_only:
                continue
            start_date = _date_text(_value(row, "start_date", "in_date", "ann_date", default=start))
            raw_end = _value(row, "end_date", "out_date", default=end)
            end_date = _date_text(raw_end) if raw_end not in (None, "") else end
            for day in _date_values(max(start, start_date), min(end, end_date)):
                lookup[(day, symbol)] = True
        for symbol in symbols:
            for day in _date_values(start, end):
                lookup.setdefault((day, symbol), False)
        return lookup

    def _events_from_st_intervals(self, st_rows: list[dict[str, Any]], start: str, end: str) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for row in st_rows:
            symbol = _symbol_value(row)
            if not symbol or row.get("start_date") in (None, ""):
                continue
            start_date = _date_text(row["start_date"])
            if start <= start_date <= end:
                rows.append(self._st_event_row(symbol, "st_enter", start_date, {"source_event": "stock_st", "raw": row}))
            raw_end = _value(row, "end_date", "out_date")
            if raw_end not in (None, ""):
                end_date = _date_text(raw_end)
                if start <= end_date <= end:
                    rows.append(self._st_event_row(symbol, "st_exit", end_date, {"source_event": "stock_st", "raw": row}))
        return sorted(rows, key=lambda item: (item["symbol"], item["event_date"], item["event_type"]))

    def _st_event_row(
        self,
        symbol: str,
        event_type: str,
        event_date: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            "symbol": symbol,
            "event_type": event_type,
            "event_date": event_date,
            "available_at": _timestamp_at(event_date, "09:20:00"),
            "available_at_rule": "tushare_stock_st_09:20",
            "payload": json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str),
        }

__all__ = ["TushareAdapter"]
