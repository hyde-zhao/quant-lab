"""JQData adapter for limited PIT window market-data snapshots."""

from __future__ import annotations

import importlib
import json
import os
from collections.abc import Callable, Mapping
from datetime import date, datetime, timedelta, timezone
from typing import Any

from ..contracts import (
    INTERFACE_EVENTS_DISCLOSURE,
    INTERFACE_INDEX_MEMBERS_SNAPSHOT,
    INTERFACE_INDEX_WEIGHTS_SNAPSHOT,
    INTERFACE_PRICES_LIMIT_DAILY,
    INTERFACE_STOCK_BASIC_SNAPSHOT,
    INTERFACE_TRADE_STATUS_DAILY,
    PIT_STATUS_AVAILABLE,
    READINESS_STATUS_AVAILABLE,
    SOURCE_JQDATA,
)
from .protocol import AdapterConfig, ConnectorError, ConnectorRequest, ConnectorResult

ProviderFactory = Callable[[str, str], object]
Clock = Callable[[], datetime]

_PERMISSION_MARKERS = (
    "permission",
    "permission_denied",
    "unauthorized",
    "not authorized",
    "auth",
    "login",
    "权限",
    "无权限",
    "认证",
    "登录",
)
_RATE_MARKERS = ("rate", "quota", "limit", "频率", "配额", "次数", "限制")


class JQDataRequestError(ValueError):
    """请求参数无法映射到 JQData 调用。"""


def _parse_date(value: object) -> date:
    text = str(value).strip()
    try:
        if len(text) == 8 and text.isdigit():
            return datetime.strptime(text, "%Y%m%d").date()
        if len(text) >= 10 and text[4] == "-" and text[7] == "-":
            return date.fromisoformat(text[:10])
    except ValueError as exc:
        raise JQDataRequestError(f"invalid date: {text}") from exc
    raise JQDataRequestError(f"invalid date: {text}")


def _date_range(start: object, end: object) -> list[date]:
    start_date = _parse_date(start)
    end_date = _parse_date(end)
    if start_date > end_date:
        raise JQDataRequestError("start_date cannot be later than end_date")
    return [
        start_date + timedelta(days=offset)
        for offset in range((end_date - start_date).days + 1)
    ]


def _default_clock() -> datetime:
    return datetime.now(timezone.utc)


def _iso(clock: Clock) -> str:
    value = clock()
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.isoformat()


def _jq_index_code(value: object) -> str:
    code = str(value or "399300.SZ").strip().upper()
    hs300_aliases = {"399300.SZ", "000300.SH", "000300.XSHG"}
    if code in hs300_aliases:
        return "000300.XSHG"
    if code.endswith(".SH"):
        return f"{code[:-3]}.XSHG"
    if code.endswith(".SZ"):
        return f"{code[:-3]}.XSHE"
    return code


def _jq_security_code(value: object) -> str:
    code = str(value or "").strip().upper()
    if code.endswith(".SZ"):
        return f"{code[:-3]}.XSHE"
    if code.endswith(".SH"):
        return f"{code[:-3]}.XSHG"
    return code


def _canonical_security_code(value: object) -> str:
    code = str(value or "").strip().upper()
    if code.endswith(".XSHE"):
        return f"{code[:-5]}.SZ"
    if code.endswith(".XSHG"):
        return f"{code[:-5]}.SH"
    return code


def _code_from_mapping(item: Mapping[str, Any]) -> object:
    for key in (
        "code",
        "con_code",
        "stock_code",
        "security",
        "symbol",
        "ts_code",
        "index",
    ):
        value = item.get(key)
        if value not in (None, ""):
            return value
    return ""


def _stock_codes_from_provider_result(value: object) -> list[str]:
    if hasattr(value, "to_dict"):
        records = value.to_dict("records")
        return [
            str(_code_from_mapping(item))
            for item in records
            if isinstance(item, Mapping)
        ]
    if isinstance(value, Mapping):
        return [str(_code_from_mapping(value))]
    if isinstance(value, (list, tuple, set)):
        codes: list[str] = []
        for item in value:
            code = _code_from_mapping(item) if isinstance(item, Mapping) else item
            if code not in (None, ""):
                codes.append(str(code))
        return codes
    if hasattr(value, "tolist"):
        return [str(item) for item in value.tolist() if item not in (None, "")]
    return []


def _provider_records(value: object) -> list[dict[str, Any]]:
    if hasattr(value, "reset_index") and hasattr(value, "to_dict"):
        try:
            return [dict(item) for item in value.reset_index().to_dict("records")]
        except Exception:
            return [dict(item) for item in value.to_dict("records")]
    if hasattr(value, "to_dict"):
        try:
            records = value.to_dict("records")
            return [dict(item) for item in records if isinstance(item, Mapping)]
        except Exception:
            pass
    if isinstance(value, Mapping):
        return [dict(value)]
    if isinstance(value, (list, tuple, set)):
        return [dict(item) for item in value if isinstance(item, Mapping)]
    return []


def _matrix_records(value: object, value_name: str) -> list[dict[str, Any]]:
    if not hasattr(value, "to_dict"):
        return _provider_records(value)
    try:
        columns = [str(item) for item in value.columns]
        index_values = list(value.index)
    except Exception:
        return _provider_records(value)
    rows: list[dict[str, Any]] = []
    for row_index, day_value in enumerate(index_values):
        day = _parse_date(day_value).isoformat()
        for column in columns:
            cell = value.iloc[row_index][column]
            rows.append(
                {
                    "trade_date": day,
                    "symbol": _canonical_security_code(column),
                    value_name: cell,
                }
            )
    return rows


def _value(item: Mapping[str, Any], *keys: str, default: object = "") -> object:
    for key in keys:
        if key in item and item[key] not in (None, ""):
            return item[key]
    return default


def _date_text(value: object) -> str:
    return _parse_date(value).isoformat()


def _day_available_at(day: str) -> str:
    return f"{day}T16:00:00+08:00"


def _security_master_available_at(list_date: str, delist_date: str = "") -> str:
    base = delist_date or list_date
    return f"{base}T09:00:00+08:00"


def _is_missing_cell(value: object) -> bool:
    if value is None:
        return True
    return str(value).strip().lower() in {"", "nat", "nan", "none"}


def _market_from_symbol(symbol: str) -> str:
    if symbol.endswith(".SZ"):
        return "SZSE"
    if symbol.endswith(".SH"):
        return "SSE"
    return "stock"


def _bool_cell(value: object) -> bool:
    if value in (None, ""):
        return False
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    text = str(value).strip().lower()
    return text in {"1", "true", "t", "yes", "y", "st"}


def _float_cell(value: object) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _symbols_from_params(params: Mapping[str, Any]) -> list[str]:
    value = params.get("symbols")
    if value is None:
        symbol = params.get("symbol")
        value = [symbol] if symbol else []
    if isinstance(value, str):
        symbols = [item.strip() for item in value.split(",") if item.strip()]
    else:
        symbols = [str(item).strip() for item in value if str(item).strip()]
    if not symbols:
        raise JQDataRequestError("symbols required")
    return [item.upper() for item in symbols]


def _call_get_price(
    provider: object,
    symbols: list[str],
    start: str,
    end: str,
    fields: list[str],
) -> object:
    method = getattr(provider, "get_price")
    jq_symbols = [_jq_security_code(symbol) for symbol in symbols]
    kwargs = {
        "start_date": start,
        "end_date": end,
        "frequency": "daily",
        "fields": fields,
        "skip_paused": False,
        "panel": False,
        "fill_paused": False,
        "fq": None,
    }
    try:
        return method(jq_symbols, **kwargs)
    except TypeError:
        kwargs.pop("fq", None)
        try:
            return method(jq_symbols, **kwargs)
        except TypeError:
            kwargs.pop("fill_paused", None)
            return method(jq_symbols, **kwargs)


def _call_get_extras(
    provider: object,
    info: str,
    symbols: list[str],
    start: str,
    end: str,
) -> object:
    method = getattr(provider, "get_extras")
    jq_symbols = [_jq_security_code(symbol) for symbol in symbols]
    return method(info, jq_symbols, start_date=start, end_date=end, df=True)


def _price_rows(value: object) -> list[dict[str, Any]]:
    if isinstance(value, Mapping):
        matrix_keys = [key for key, item in value.items() if hasattr(item, "to_dict")]
        if matrix_keys:
            merged: dict[tuple[str, str], dict[str, Any]] = {}
            for key in matrix_keys:
                for row in _matrix_records(value[key], str(key)):
                    record_key = (str(row["trade_date"]), str(row["symbol"]))
                    merged.setdefault(
                        record_key,
                        {"trade_date": row["trade_date"], "symbol": row["symbol"]},
                    )
                    merged[record_key][str(key)] = row[str(key)]
            return list(merged.values())
    rows: list[dict[str, Any]] = []
    for item in _provider_records(value):
        day_value = _value(item, "time", "date", "trade_date", "index")
        code_value = _value(item, "code", "symbol", "security", "ts_code")
        if day_value in (None, "") or code_value in (None, ""):
            continue
        row = dict(item)
        row["trade_date"] = _date_text(day_value)
        row["symbol"] = _canonical_security_code(code_value)
        rows.append(row)
    return rows


def _provider_error_type(exc: Exception) -> str:
    text = str(exc).lower()
    if any(marker in text for marker in _PERMISSION_MARKERS):
        return "permission_denied"
    if any(marker in text for marker in _RATE_MARKERS):
        return "quota_or_rate_limited"
    return "remote_error"


def _provider_error_message(error_type: str) -> str:
    if error_type == "permission_denied":
        return "jqdata provider permission denied or subscription window unavailable"
    if error_type == "quota_or_rate_limited":
        return "jqdata provider quota or rate limit reached"
    return "jqdata provider call failed; see controlled runtime logs"


class JQDataAdapter:
    source = SOURCE_JQDATA

    def __init__(
        self,
        config: AdapterConfig | None = None,
        *,
        provider_factory: ProviderFactory | None = None,
        clock: Clock | None = None,
    ) -> None:
        self.config = config or AdapterConfig(
            source=self.source,
            credential_env_vars=("JQDATA_USERNAME", "JQDATA_PASSWORD"),
        )
        self._provider_factory = provider_factory
        self._clock = clock or _default_clock

    def fetch(self, request: ConnectorRequest) -> ConnectorResult | ConnectorError:
        if not self.config.enabled:
            return ConnectorError(
                "source_disabled",
                "jqdata source is disabled by default",
                False,
                request.source,
                request.interface,
            )
        if bool(request.params.get("offline", False)):
            return ConnectorError(
                "source_disabled",
                "jqdata real fetch requires offline=false",
                False,
                request.source,
                request.interface,
            )
        if request.interface not in self.config.allow_interfaces:
            return ConnectorError(
                "interface_not_allowed",
                "jqdata interface is not allowlisted",
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
                "jqdata real fetch requires explicit_real_execution=true",
                False,
                request.source,
                request.interface,
            )
        supported = {
            INTERFACE_INDEX_MEMBERS_SNAPSHOT,
            INTERFACE_INDEX_WEIGHTS_SNAPSHOT,
            INTERFACE_STOCK_BASIC_SNAPSHOT,
            INTERFACE_TRADE_STATUS_DAILY,
            INTERFACE_PRICES_LIMIT_DAILY,
            INTERFACE_EVENTS_DISCLOSURE,
        }
        if request.interface not in supported:
            return ConnectorError(
                "interface_not_allowed",
                "jqdata interface is not supported by this adapter",
                False,
                request.source,
                request.interface,
            )
        try:
            rows, provider_calls = self._fetch_provider_rows(request)
        except JQDataRequestError:
            return ConnectorError(
                "schema_mismatch",
                "jqdata request date, symbols or index code is invalid",
                False,
                request.source,
                request.interface,
            )
        except Exception as exc:
            error_type = _provider_error_type(exc)
            return ConnectorError(
                error_type,
                _provider_error_message(error_type),
                error_type in {"remote_error", "quota_or_rate_limited"},
                request.source,
                request.interface,
            )
        return ConnectorResult(
            source=request.source,
            interface=request.interface,
            rows=rows,
            metadata={
                "provider": "jqdata",
                "provider_interface": self._provider_interface(request.interface),
                "target_dataset": request.params.get("target_dataset"),
                "provider_network_calls": provider_calls,
            },
        )

    def _provider(self) -> object:
        username_env = (
            self.config.credential_env_vars[0]
            if self.config.credential_env_vars
            else "JQDATA_USERNAME"
        )
        password_env = (
            self.config.credential_env_vars[1]
            if len(self.config.credential_env_vars) > 1
            else "JQDATA_PASSWORD"
        )
        if self._provider_factory is not None:
            return self._provider_factory(username_env, password_env)
        module = importlib.import_module("jqdatasdk")
        username = os.environ.get(username_env)
        password = os.environ.get(password_env)
        module.auth(username, password)
        return module

    def _provider_interface(self, interface: str) -> str:
        return {
            INTERFACE_INDEX_MEMBERS_SNAPSHOT: "get_index_stocks",
            INTERFACE_INDEX_WEIGHTS_SNAPSHOT: "get_index_weights",
            INTERFACE_STOCK_BASIC_SNAPSHOT: "get_all_securities",
            INTERFACE_TRADE_STATUS_DAILY: "get_price+get_extras",
            INTERFACE_PRICES_LIMIT_DAILY: "get_price",
            INTERFACE_EVENTS_DISCLOSURE: "get_extras",
        }.get(interface, interface)

    def _fetch_provider_rows(
        self,
        request: ConnectorRequest,
    ) -> tuple[list[dict[str, Any]], int]:
        if request.interface == INTERFACE_INDEX_MEMBERS_SNAPSHOT:
            return self._fetch_index_members(request)
        if request.interface == INTERFACE_INDEX_WEIGHTS_SNAPSHOT:
            return self._fetch_index_weights(request)
        if request.interface == INTERFACE_STOCK_BASIC_SNAPSHOT:
            return self._fetch_stock_basic(request)
        if request.interface == INTERFACE_TRADE_STATUS_DAILY:
            return self._fetch_trade_status(request)
        if request.interface == INTERFACE_PRICES_LIMIT_DAILY:
            return self._fetch_prices_limit(request)
        if request.interface == INTERFACE_EVENTS_DISCLOSURE:
            return self._fetch_events(request)
        raise JQDataRequestError(f"unsupported interface: {request.interface}")

    def _fetch_index_members(
        self,
        request: ConnectorRequest,
    ) -> tuple[list[dict[str, Any]], int]:
        params = dict(request.params)
        requested_index_code = str(params.get("index_code", "399300.SZ")).strip().upper()
        jq_index_code = _jq_index_code(requested_index_code)
        dates = _date_range(params.get("start_date"), params.get("end_date"))
        available_at = _iso(self._clock)
        provider = self._provider()
        method = getattr(provider, "get_index_stocks")
        rows: list[dict[str, Any]] = []
        provider_calls = 0
        for query_date in dates:
            provider_calls += 1
            value = method(jq_index_code, date=query_date.isoformat())
            for con_code in _stock_codes_from_provider_result(value):
                rows.append(
                    {
                        "trade_date": query_date.isoformat(),
                        "index_code": requested_index_code,
                        "con_code": _canonical_security_code(con_code),
                        "in_date": None,
                        "out_date": None,
                        "is_member": True,
                        "effective_date": query_date.isoformat(),
                        "available_date": query_date.isoformat(),
                        "available_at": available_at,
                        "available_at_rule": "explicit_timestamp",
                        "is_pit_universe": True,
                        "pit_status": PIT_STATUS_AVAILABLE,
                        "readiness_status": READINESS_STATUS_AVAILABLE,
                    }
                )
        return rows, provider_calls

    def _fetch_index_weights(
        self,
        request: ConnectorRequest,
    ) -> tuple[list[dict[str, Any]], int]:
        params = dict(request.params)
        requested_index_code = str(params.get("index_code", "399300.SZ")).strip().upper()
        jq_index_code = _jq_index_code(requested_index_code)
        dates = _date_range(params.get("start_date"), params.get("end_date"))
        provider = self._provider()
        method = getattr(provider, "get_index_weights")
        rows: list[dict[str, Any]] = []
        provider_calls = 0
        for query_date in dates:
            provider_calls += 1
            value = method(jq_index_code, date=query_date.isoformat())
            for item in _provider_records(value):
                con_code = _canonical_security_code(_code_from_mapping(item))
                if not con_code:
                    continue
                effective_date = _date_text(
                    _value(item, "date", "trade_date", default=query_date.isoformat())
                )
                trade_date = query_date.isoformat()
                rows.append(
                    {
                        "trade_date": trade_date,
                        "index_code": requested_index_code,
                        "con_code": con_code,
                        "weight": _value(item, "weight", "i_weight", "index_weight"),
                        "effective_date": effective_date,
                        "available_date": trade_date,
                        "available_at": str(
                            _value(
                                item,
                                "available_at",
                                default=_day_available_at(trade_date),
                            )
                        ),
                        "available_at_rule": "daily_close_fact",
                        "pit_status": PIT_STATUS_AVAILABLE,
                        "readiness_status": READINESS_STATUS_AVAILABLE,
                    }
                )
        return rows, provider_calls

    def _fetch_stock_basic(
        self,
        request: ConnectorRequest,
    ) -> tuple[list[dict[str, Any]], int]:
        params = dict(request.params)
        snapshot_date = _parse_date(
            params.get("snapshot_date") or params.get("end_date")
        ).isoformat()
        window_start = _parse_date(params.get("start_date") or snapshot_date).isoformat()
        provider = self._provider()
        method = getattr(provider, "get_all_securities")
        try:
            value = method(types=["stock"], date=snapshot_date)
        except TypeError:
            value = method("stock", date=snapshot_date)
        rows: list[dict[str, Any]] = []
        for item in _provider_records(value):
            symbol = _canonical_security_code(_code_from_mapping(item))
            if not symbol:
                continue
            list_date = _date_text(
                _value(item, "start_date", "list_date", default=snapshot_date)
            )
            if list_date > snapshot_date:
                continue
            raw_end_date = _value(item, "end_date", "delist_date", default="")
            delist_date = ""
            if not _is_missing_cell(raw_end_date):
                raw_end_text = _date_text(raw_end_date)
                if (
                    raw_end_text not in {"2200-01-01", "9999-12-31"}
                    and raw_end_text <= snapshot_date
                ):
                    delist_date = raw_end_text
            if delist_date and delist_date < window_start:
                continue
            list_status = "D" if delist_date and delist_date <= snapshot_date else "L"
            rows.append(
                {
                    "symbol": symbol,
                    "name": str(_value(item, "display_name", "name", default=symbol)),
                    "market": str(_value(item, "market", default=_market_from_symbol(symbol))),
                    "list_status": str(_value(item, "list_status", default=list_status)),
                    "list_date": list_date,
                    "delist_date": delist_date,
                    "effective_date": list_date,
                    "available_date": list_date,
                    "available_at": str(
                        _value(
                            item,
                            "available_at",
                            default=_security_master_available_at(list_date, delist_date),
                        )
                    ),
                    "available_at_rule": "security_master_list_delist_date",
                    "pit_status": PIT_STATUS_AVAILABLE,
                    "readiness_status": READINESS_STATUS_AVAILABLE,
                }
            )
        return rows, 1

    def _fetch_trade_status(
        self,
        request: ConnectorRequest,
    ) -> tuple[list[dict[str, Any]], int]:
        params = dict(request.params)
        start = _parse_date(params.get("start_date")).isoformat()
        end = _parse_date(params.get("end_date")).isoformat()
        symbols = _symbols_from_params(params)
        provider = self._provider()
        price = _call_get_price(provider, symbols, start, end, ["paused"])
        price_rows = _price_rows(price)
        st_lookup: dict[tuple[str, str], bool] = {}
        provider_calls = 1
        if hasattr(provider, "get_extras"):
            st_rows = _matrix_records(
                _call_get_extras(provider, "is_st", symbols, start, end),
                "is_st",
            )
            provider_calls += 1
            st_lookup = {
                (str(row["trade_date"]), str(row["symbol"])): _bool_cell(row.get("is_st"))
                for row in st_rows
            }
        rows: list[dict[str, Any]] = []
        for item in price_rows:
            day = str(item["trade_date"])
            symbol = str(item["symbol"])
            is_suspended = _bool_cell(_value(item, "paused", default=False))
            is_st = st_lookup.get((day, symbol), _bool_cell(item.get("is_st")))
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
                    "available_at": _day_available_at(day),
                    "available_at_rule": "daily_close_fact",
                }
            )
        return rows, provider_calls

    def _fetch_prices_limit(
        self,
        request: ConnectorRequest,
    ) -> tuple[list[dict[str, Any]], int]:
        params = dict(request.params)
        start = _parse_date(params.get("start_date")).isoformat()
        end = _parse_date(params.get("end_date")).isoformat()
        symbols = _symbols_from_params(params)
        provider = self._provider()
        price = _call_get_price(provider, symbols, start, end, ["high_limit", "low_limit"])
        rows: list[dict[str, Any]] = []
        for item in _price_rows(price):
            day = str(item["trade_date"])
            limit_up = _float_cell(_value(item, "high_limit", "limit_up"))
            limit_down = _float_cell(_value(item, "low_limit", "limit_down"))
            if limit_up is None or limit_down is None:
                continue
            rows.append(
                {
                    "trade_date": day,
                    "symbol": str(item["symbol"]),
                    "limit_up": limit_up,
                    "limit_down": limit_down,
                    "available_at": _day_available_at(day),
                    "available_at_rule": "daily_close_fact",
                }
            )
        return rows, 1

    def _fetch_events(
        self,
        request: ConnectorRequest,
    ) -> tuple[list[dict[str, Any]], int]:
        params = dict(request.params)
        start = _parse_date(params.get("start_date")).isoformat()
        end = _parse_date(params.get("end_date")).isoformat()
        symbols = _symbols_from_params(params)
        provider = self._provider()
        st_rows = sorted(
            _matrix_records(_call_get_extras(provider, "is_st", symbols, start, end), "is_st"),
            key=lambda item: (str(item["symbol"]), str(item["trade_date"])),
        )
        rows: list[dict[str, Any]] = []
        previous: dict[str, bool] = {}
        for item in st_rows:
            symbol = str(item["symbol"])
            day = str(item["trade_date"])
            is_st = _bool_cell(item.get("is_st"))
            if symbol not in previous and not is_st:
                previous[symbol] = is_st
                continue
            if symbol not in previous or previous[symbol] != is_st:
                event_type = "st_enter" if is_st else "st_exit"
                rows.append(
                    {
                        "symbol": symbol,
                        "event_type": event_type,
                        "event_date": day,
                        "available_at": _day_available_at(day),
                        "available_at_rule": "daily_close_fact",
                        "payload": json.dumps(
                            {"source_event": "is_st", "is_st": is_st},
                            ensure_ascii=False,
                            sort_keys=True,
                        ),
                    }
                )
            previous[symbol] = is_st
        return rows, 1


__all__ = ["JQDataAdapter"]
