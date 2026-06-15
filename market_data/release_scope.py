"""CR018-S01 production current truth release scope 合同。"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import date
from typing import Any, Mapping

CR018_RELEASE_SCOPE_START_DATE = "2015-01-05"
CR018_SCOPE_KIND = "scoped_release"
CR018_COVERAGE_DENOMINATOR_POLICY = "open_trade_dates_within_scoped_release"
CR018_PRE_2015_STATUS = "blocked/future_backfill"

CLAIM_PRODUCTION_CURRENT_TRUTH = "production_current_truth_scoped_release"
CLAIM_SINCE_INCEPTION_CURRENT_TRUTH = "since_inception_current_truth"

ERROR_INVALID_RELEASE_SCOPE = "invalid_release_scope"
ERROR_CALENDAR_SOURCE_MISSING = "calendar_source_missing"
ERROR_PERMISSION_COUNTER_VIOLATION = "permission_counter_violation"
REASON_PRE_2015_FUTURE_BACKFILL = "pre_2015_future_backfill"

FORBIDDEN_OPERATION_COUNTER_KEYS: tuple[str, ...] = (
    "provider_fetch",
    "lake_write",
    "credential_read",
    "current_pointer_publish",
    "current_truth_publish",
    "qmt_operation",
    "duckdb_dependency_change",
)


@dataclass(frozen=True, slots=True)
class ReleaseScope:
    """CR018 第一版 production current truth 的固定发布范围。"""

    release_id: str
    scope_kind: str
    requested_start_date: str
    requested_end_date: str
    start_date: str
    end_date: str
    latest_closed_trade_date: str
    as_of_trade_date: str
    calendar_source: str
    coverage_denominator_policy: str = CR018_COVERAGE_DENOMINATOR_POLICY
    pre_2015_status: str = CR018_PRE_2015_STATUS
    pre_2015_reason_code: str = REASON_PRE_2015_FUTURE_BACKFILL
    since_inception_allowed_claim_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class ReleaseScopeResult:
    """release scope resolver 的 JSON-ready 输出。"""

    release_scope: ReleaseScope | None
    passed: bool
    allowed_claims: tuple[dict[str, Any], ...] = ()
    blocked_claims: tuple[dict[str, Any], ...] = ()
    error_codes: tuple[str, ...] = ()
    permission_counters: dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "release_scope": self.release_scope.to_dict() if self.release_scope else None,
            "passed": self.passed,
            "allowed_claims": [dict(item) for item in self.allowed_claims],
            "blocked_claims": [dict(item) for item in self.blocked_claims],
            "error_codes": list(self.error_codes),
            "permission_counters": dict(self.permission_counters),
        }


def default_permission_counters() -> dict[str, int]:
    """返回本 Story 授权边界下必须保持为 0 的真实操作计数。"""

    return {key: 0 for key in FORBIDDEN_OPERATION_COUNTER_KEYS}


def normalise_permission_counters(counters: Mapping[str, Any] | None = None) -> dict[str, int]:
    """把外部计数快照归一化；无法解析的值按违规处理为 1。"""

    normalised = default_permission_counters()
    for key, value in dict(counters or {}).items():
        try:
            normalised[str(key)] = int(value)
        except (TypeError, ValueError):
            normalised[str(key)] = 1
    return normalised


def permission_counters_are_zero(counters: Mapping[str, Any] | None = None) -> bool:
    return all(value == 0 for value in normalise_permission_counters(counters).values())


def _parse_iso_date(value: str | date | None, field_name: str) -> tuple[date | None, dict[str, Any] | None]:
    if isinstance(value, date):
        return value, None
    if not value:
        return None, {"code": ERROR_INVALID_RELEASE_SCOPE, "field": field_name, "value": value}
    try:
        return date.fromisoformat(str(value)), None
    except ValueError:
        return None, {"code": ERROR_INVALID_RELEASE_SCOPE, "field": field_name, "value": str(value)}


def _pre_2015_blocked_claim(requested_start_date: str) -> dict[str, Any]:
    return {
        "claim": CLAIM_SINCE_INCEPTION_CURRENT_TRUTH,
        "status": CR018_PRE_2015_STATUS,
        "reason_code": REASON_PRE_2015_FUTURE_BACKFILL,
        "requested_start_date": requested_start_date,
        "supported_start_date": CR018_RELEASE_SCOPE_START_DATE,
        "remediation": "future_backfill_before_2015_and_repeat_cp5_publish_gate",
    }


def _invalid_scope_blocked_claim(details: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "claim": CLAIM_PRODUCTION_CURRENT_TRUTH,
        "status": "blocked",
        "reason_code": ERROR_INVALID_RELEASE_SCOPE,
        "details": [dict(item) for item in details],
    }


def resolve_release_scope(
    release_id: str,
    *,
    latest_closed_trade_date: str | date,
    start_date: str | date = CR018_RELEASE_SCOPE_START_DATE,
    end_date: str | date | None = None,
    calendar_source: str = "explicit_latest_closed_trade_date",
    permission_counters: Mapping[str, Any] | None = None,
) -> ReleaseScopeResult:
    """解析 CR018 第一版 scoped release，不读取 provider、lake、catalog 或凭据。"""

    counters = normalise_permission_counters(permission_counters)
    min_date, _ = _parse_iso_date(CR018_RELEASE_SCOPE_START_DATE, "release_scope_start_date")
    requested_start, start_error = _parse_iso_date(start_date, "start_date")
    latest_closed, latest_error = _parse_iso_date(latest_closed_trade_date, "latest_closed_trade_date")
    requested_end, end_error = _parse_iso_date(
        end_date if end_date is not None else latest_closed_trade_date,
        "end_date",
    )

    details = [item for item in (start_error, latest_error, end_error) if item]
    error_codes: list[str] = []
    if details:
        error_codes.append(ERROR_INVALID_RELEASE_SCOPE)
    if not str(calendar_source or "").strip():
        error_codes.append(ERROR_CALENDAR_SOURCE_MISSING)
        details.append({"code": ERROR_CALENDAR_SOURCE_MISSING, "field": "calendar_source"})
    if any(value != 0 for value in counters.values()):
        error_codes.append(ERROR_PERMISSION_COUNTER_VIOLATION)
        details.append({"code": ERROR_PERMISSION_COUNTER_VIOLATION, "permission_counters": dict(counters)})

    if min_date and requested_start and requested_start > min_date:
        error_codes.append(ERROR_INVALID_RELEASE_SCOPE)
        details.append(
            {
                "code": ERROR_INVALID_RELEASE_SCOPE,
                "field": "start_date",
                "expected": CR018_RELEASE_SCOPE_START_DATE,
                "actual": requested_start.isoformat(),
            }
        )
    if min_date and latest_closed and latest_closed < min_date:
        error_codes.append(ERROR_INVALID_RELEASE_SCOPE)
        details.append(
            {
                "code": ERROR_INVALID_RELEASE_SCOPE,
                "field": "latest_closed_trade_date",
                "minimum": CR018_RELEASE_SCOPE_START_DATE,
                "actual": latest_closed.isoformat(),
            }
        )
    if latest_closed and requested_end and requested_end != latest_closed:
        error_codes.append(ERROR_INVALID_RELEASE_SCOPE)
        details.append(
            {
                "code": ERROR_INVALID_RELEASE_SCOPE,
                "field": "end_date",
                "expected": latest_closed.isoformat(),
                "actual": requested_end.isoformat(),
            }
        )

    error_codes = list(dict.fromkeys(error_codes))
    if error_codes or min_date is None or requested_start is None or latest_closed is None or requested_end is None:
        blocked = [_pre_2015_blocked_claim(str(start_date)), _invalid_scope_blocked_claim(details)]
        return ReleaseScopeResult(
            release_scope=None,
            passed=False,
            allowed_claims=(),
            blocked_claims=tuple(blocked),
            error_codes=tuple(error_codes or [ERROR_INVALID_RELEASE_SCOPE]),
            permission_counters=counters,
        )

    scope = ReleaseScope(
        release_id=str(release_id),
        scope_kind=CR018_SCOPE_KIND,
        requested_start_date=requested_start.isoformat(),
        requested_end_date=requested_end.isoformat(),
        start_date=CR018_RELEASE_SCOPE_START_DATE,
        end_date=latest_closed.isoformat(),
        latest_closed_trade_date=latest_closed.isoformat(),
        as_of_trade_date=latest_closed.isoformat(),
        calendar_source=str(calendar_source),
    )
    return ReleaseScopeResult(
        release_scope=scope,
        passed=True,
        allowed_claims=(
            {
                "claim": CLAIM_PRODUCTION_CURRENT_TRUTH,
                "scope_kind": CR018_SCOPE_KIND,
                "start_date": scope.start_date,
                "end_date": scope.end_date,
            },
        ),
        blocked_claims=(_pre_2015_blocked_claim(scope.requested_start_date),),
        error_codes=(),
        permission_counters=counters,
    )


__all__ = [
    "CLAIM_PRODUCTION_CURRENT_TRUTH",
    "CLAIM_SINCE_INCEPTION_CURRENT_TRUTH",
    "CR018_COVERAGE_DENOMINATOR_POLICY",
    "CR018_PRE_2015_STATUS",
    "CR018_RELEASE_SCOPE_START_DATE",
    "CR018_SCOPE_KIND",
    "ERROR_CALENDAR_SOURCE_MISSING",
    "ERROR_INVALID_RELEASE_SCOPE",
    "ERROR_PERMISSION_COUNTER_VIOLATION",
    "FORBIDDEN_OPERATION_COUNTER_KEYS",
    "REASON_PRE_2015_FUTURE_BACKFILL",
    "ReleaseScope",
    "ReleaseScopeResult",
    "default_permission_counters",
    "normalise_permission_counters",
    "permission_counters_are_zero",
    "resolve_release_scope",
]
