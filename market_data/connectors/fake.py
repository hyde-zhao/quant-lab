"""默认 fake/offline connector。"""

from __future__ import annotations

import hashlib
import random
from datetime import date, datetime, timedelta, timezone
from typing import Any, Mapping

from ..contracts import INTERFACE_PRICES_DAILY, SOURCE_FAKE
from .protocol import ConnectorError, ConnectorRequest, ConnectorResult

CN_TZ = timezone(timedelta(hours=8))


def _parse_date(value: object) -> date:
    if isinstance(value, date):
        return value
    return datetime.strptime(str(value), "%Y-%m-%d").date()


def _date_range(params: Mapping[str, Any]) -> list[date]:
    if "date_range" in params:
        start, end = params["date_range"]
    else:
        start = params.get("start_date")
        end = params.get("end_date")
    start_date = _parse_date(start)
    end_date = _parse_date(end)
    if start_date > end_date:
        return []
    days = (end_date - start_date).days
    return [start_date + timedelta(days=offset) for offset in range(days + 1)]


def _stable_close(seed: int, symbol: str, trade_date: date) -> float:
    payload = f"{seed}|{symbol}|{trade_date.isoformat()}".encode("utf-8")
    digest = hashlib.sha256(payload).hexdigest()
    cents = int(digest[:8], 16) % 10000
    return round(10.0 + cents / 100.0, 2)


class FakeConnector:
    source = SOURCE_FAKE

    def __init__(
        self,
        seed: int = 0,
        failure_plan: Mapping[str, object] | None = None,
    ) -> None:
        self.seed = seed
        self.failure_plan = dict(failure_plan or {})
        self._attempts: dict[str, int] = {}

    def _planned_failure(self, request: ConnectorRequest) -> object | None:
        plan = self.failure_plan.get(request.batch_id)
        if plan is None:
            return None
        attempt = self._attempts.get(request.batch_id, 0)
        if isinstance(plan, (list, tuple)):
            if attempt >= len(plan):
                return None
            return plan[attempt]
        if attempt == 0:
            return plan
        return None

    def fetch(self, request: ConnectorRequest) -> ConnectorResult | ConnectorError:
        attempt = self._attempts.get(request.batch_id, 0)
        planned = self._planned_failure(request)
        self._attempts[request.batch_id] = attempt + 1
        if planned == "retryable_error":
            return ConnectorError(
                "provider_error",
                "fake retryable error",
                True,
                request.source,
                request.interface,
            )
        if planned == "non_retryable_error":
            return ConnectorError(
                "contract_error",
                "fake non-retryable error",
                False,
                request.source,
                request.interface,
            )

        rows = self._build_rows(request)
        if planned == "partial_success":
            partial_rows = rows[: max(1, len(rows) // 2)]
            return ConnectorResult(
                source=request.source,
                interface=request.interface,
                rows=partial_rows,
                metadata=self._metadata(request, partial_rows),
                partial_errors=[
                    ConnectorError(
                        "provider_error",
                        "fake partial success",
                        True,
                        request.source,
                        request.interface,
                    )
                ],
            )
        return ConnectorResult(
            source=request.source,
            interface=request.interface,
            rows=rows,
            metadata=self._metadata(request, rows),
        )

    def _build_rows(self, request: ConnectorRequest) -> list[dict[str, Any]]:
        if request.interface != INTERFACE_PRICES_DAILY:
            return []
        params = request.params
        seed = int(params.get("seed", self.seed))
        symbols = tuple(params.get("symbols", ()))
        rows: list[dict[str, Any]] = []
        # 本地 random 实例保留确定性边界，不使用全局 random。
        random.Random(seed)
        adjustment_policy = str(params.get("adjustment_policy", "none"))
        for trade_date in _date_range(params):
            available_at = datetime.combine(
                trade_date,
                datetime.strptime("16:00:00", "%H:%M:%S").time(),
                tzinfo=CN_TZ,
            ).isoformat()
            for symbol in symbols:
                rows.append(
                    {
                        "trade_date": trade_date.isoformat(),
                        "symbol": str(symbol),
                        "close": _stable_close(seed, str(symbol), trade_date),
                        "source": SOURCE_FAKE,
                        "source_run_id": request.run_id,
                        "adjustment_policy": adjustment_policy,
                        "available_at": available_at,
                    }
                )
        return rows

    def _metadata(
        self,
        request: ConnectorRequest,
        rows: list[dict[str, Any]],
    ) -> dict[str, Any]:
        return {
            "run_id": request.run_id,
            "source": request.source,
            "interface": request.interface,
            "row_count": len(rows),
            "adjustment_policy": request.params.get("adjustment_policy", "none"),
            "available_at_rule": "trade_date_16:00:00+08:00",
        }


__all__ = ["FakeConnector"]
