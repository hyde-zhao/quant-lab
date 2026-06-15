"""CR016-S03 monitoring heartbeat 离线合同。

本模块只处理调用方传入的 fixture heartbeat event，不读取真实账户、凭据、
broker lake root，也不执行任何 QMT / broker / lake / publish 操作。
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Mapping


HEARTBEAT_SCHEMA_VERSION = "heartbeat_status_v1"
HEARTBEAT_INCIDENT_KIND = "heartbeat_incident_candidate"

_SENSITIVE_TEXT_PATTERNS = (
    re.compile(r"(?i)\b(token|password|passwd|session|cookie|secret)\b"),
    re.compile(r"(?i)\bapi[_-]?key\b"),
    re.compile(r"(?i)\baccount[_-]?(id|no|number)?\b"),
    re.compile(r"(?i)\bholdings?\b"),
    re.compile(r"(?i)begin [a-z ]*private key"),
    re.compile(r"(?i)\bprivate[_ -]?key\b"),
    re.compile(r"(?i)(^|[/\\])\.env($|[./\\])"),
    re.compile(r"(?i)^/home/[^/]+/.+"),
    re.compile(r"(?i)^/users/[^/]+/.+"),
    re.compile(r"(?i)^/root/.+"),
    re.compile(r"(?i)^[a-z]:\\users\\[^\\]+\\.+"),
    re.compile(r"\d{12,}"),
)


class HeartbeatStatus(str, Enum):
    """heartbeat 检查稳定状态。"""

    PASS = "pass"
    FAIL = "fail"
    REQUIRED_MISSING = "required_missing"


class HeartbeatErrorCode(str, Enum):
    """heartbeat 异常路径稳定错误码。"""

    HEARTBEAT_TIMEOUT = "heartbeat_timeout"
    HEARTBEAT_MISSING = "heartbeat_missing"
    HEARTBEAT_STATUS_FAIL = "heartbeat_status_fail"


@dataclass(frozen=True, slots=True)
class HeartbeatEvent:
    """fixture heartbeat event。

    字段只允许传入 source / ref / stage 这类可脱敏引用，不承载账户、token、
    session、真实 broker root 或真实持仓。
    """

    source: str
    observed_at: datetime
    stage: str
    status_ref: str = "ok"
    heartbeat_ref: str = ""
    deadline_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class HeartbeatDeadlinePolicy:
    """heartbeat deadline 策略。

    `deadline_at` 优先；未提供时使用 `max_age_seconds` 与检查时间计算。
    """

    deadline_at: datetime | None = None
    max_age_seconds: int | None = None
    required: bool = True
    policy_ref: str = "heartbeat-deadline-policy"


@dataclass(frozen=True, slots=True)
class HeartbeatIncidentCandidate:
    """heartbeat 异常 incident candidate；不持久化，不含敏感原值。"""

    incident_id: str
    incident_kind: str
    reason: str
    stage: str
    source_ref: str
    heartbeat_ref: str
    evidence_ref: str
    redaction_status: str
    storage_policy: str = "candidate_only_no_persist"
    safety_counters: Mapping[str, int] = field(
        default_factory=lambda: monitoring_safety_counters()
    )


@dataclass(frozen=True, slots=True)
class HeartbeatCheckResult:
    """`heartbeat_check()` 输出合同。"""

    status: HeartbeatStatus
    schema_version: str
    stage: str
    heartbeat_ref: str
    deadline_at: datetime | None
    observed_at: datetime | None
    error_code: HeartbeatErrorCode | None = None
    incident_candidate: HeartbeatIncidentCandidate | None = None
    safety_counters: Mapping[str, int] = field(
        default_factory=lambda: monitoring_safety_counters()
    )

    @property
    def passed(self) -> bool:
        return self.status is HeartbeatStatus.PASS

    @property
    def failed(self) -> bool:
        return self.status in {
            HeartbeatStatus.FAIL,
            HeartbeatStatus.REQUIRED_MISSING,
        }


def heartbeat_check(
    event: HeartbeatEvent | Mapping[str, object] | None,
    deadline_policy: HeartbeatDeadlinePolicy | Mapping[str, object],
    *,
    now: datetime | None = None,
) -> HeartbeatCheckResult:
    """对 fixture heartbeat 做 deadline 检查。

    返回 `pass`、`fail` 或 `required_missing`；异常路径只生成 incident
    candidate，不执行任何真实 broker 操作。
    """

    observed_now = _observed_at(now)
    policy = _coerce_deadline_policy(deadline_policy)
    if event is None:
        if not policy.required:
            return HeartbeatCheckResult(
                status=HeartbeatStatus.PASS,
                schema_version=HEARTBEAT_SCHEMA_VERSION,
                stage="",
                heartbeat_ref="",
                deadline_at=_deadline_from_policy(None, policy, observed_now),
                observed_at=None,
                safety_counters=monitoring_safety_counters(),
            )
        incident = _build_incident_candidate(
            reason=HeartbeatErrorCode.HEARTBEAT_MISSING.value,
            stage="",
            source="",
            heartbeat_ref="",
            policy_ref=policy.policy_ref,
            observed_at=observed_now,
        )
        return HeartbeatCheckResult(
            status=HeartbeatStatus.REQUIRED_MISSING,
            schema_version=HEARTBEAT_SCHEMA_VERSION,
            stage="",
            heartbeat_ref="",
            deadline_at=_deadline_from_policy(None, policy, observed_now),
            observed_at=None,
            error_code=HeartbeatErrorCode.HEARTBEAT_MISSING,
            incident_candidate=incident,
            safety_counters=monitoring_safety_counters(),
        )

    heartbeat = _coerce_event(event)
    deadline_at = _deadline_from_policy(heartbeat, policy, observed_now)
    heartbeat_ref = _safe_ref(heartbeat.heartbeat_ref or _heartbeat_ref(heartbeat))
    status_ref = _safe_label(heartbeat.status_ref).lower()

    if status_ref in {"fail", "failed", "down", "missing"}:
        incident = _build_incident_candidate(
            reason=HeartbeatErrorCode.HEARTBEAT_STATUS_FAIL.value,
            stage=heartbeat.stage,
            source=heartbeat.source,
            heartbeat_ref=heartbeat_ref,
            policy_ref=policy.policy_ref,
            observed_at=observed_now,
        )
        return HeartbeatCheckResult(
            status=HeartbeatStatus.FAIL,
            schema_version=HEARTBEAT_SCHEMA_VERSION,
            stage=_safe_label(heartbeat.stage),
            heartbeat_ref=heartbeat_ref,
            deadline_at=deadline_at,
            observed_at=_observed_at(heartbeat.observed_at),
            error_code=HeartbeatErrorCode.HEARTBEAT_STATUS_FAIL,
            incident_candidate=incident,
            safety_counters=monitoring_safety_counters(),
        )

    observed_at = _observed_at(heartbeat.observed_at)
    if _heartbeat_deadline_failed(heartbeat, policy, observed_at, deadline_at):
        incident = _build_incident_candidate(
            reason=HeartbeatErrorCode.HEARTBEAT_TIMEOUT.value,
            stage=heartbeat.stage,
            source=heartbeat.source,
            heartbeat_ref=heartbeat_ref,
            policy_ref=policy.policy_ref,
            observed_at=observed_now,
        )
        return HeartbeatCheckResult(
            status=HeartbeatStatus.FAIL,
            schema_version=HEARTBEAT_SCHEMA_VERSION,
            stage=_safe_label(heartbeat.stage),
            heartbeat_ref=heartbeat_ref,
            deadline_at=deadline_at,
            observed_at=observed_at,
            error_code=HeartbeatErrorCode.HEARTBEAT_TIMEOUT,
            incident_candidate=incident,
            safety_counters=monitoring_safety_counters(),
        )

    return HeartbeatCheckResult(
        status=HeartbeatStatus.PASS,
        schema_version=HEARTBEAT_SCHEMA_VERSION,
        stage=_safe_label(heartbeat.stage),
        heartbeat_ref=heartbeat_ref,
        deadline_at=deadline_at,
        observed_at=observed_at,
        safety_counters=monitoring_safety_counters(),
    )


def monitoring_safety_counters() -> dict[str, int]:
    """返回 CR016-S03 heartbeat 合同必须保持为 0 的安全计数。"""

    return {
        "qmt_api_call": 0,
        "real_order_call": 0,
        "real_cancel_call": 0,
        "account_query_call": 0,
        "account_write_call": 0,
        "credential_read": 0,
        "real_broker_operation": 0,
        "real_broker_lake_write": 0,
        "real_lake_write": 0,
        "provider_fetch": 0,
        "publish": 0,
        "dependency_change": 0,
        "simulation_run": 0,
        "real_snapshot_pull": 0,
        "incident_persisted": 0,
        "cancel_plan_executed": 0,
        "new_order_allowed_after_freeze": 0,
        "sensitive_raw_value_output": 0,
    }


def _coerce_event(event: HeartbeatEvent | Mapping[str, object]) -> HeartbeatEvent:
    if isinstance(event, HeartbeatEvent):
        return event
    observed = event.get("observed_at")
    return HeartbeatEvent(
        source=_string_value(event.get("source")),
        observed_at=_observed_at(observed if isinstance(observed, datetime) else None),
        stage=_string_value(event.get("stage")),
        status_ref=_string_value(event.get("status_ref")) or "ok",
        heartbeat_ref=_string_value(event.get("heartbeat_ref")),
        deadline_at=(
            _observed_at(event.get("deadline_at"))
            if isinstance(event.get("deadline_at"), datetime)
            else None
        ),
    )


def _coerce_deadline_policy(
    policy: HeartbeatDeadlinePolicy | Mapping[str, object],
) -> HeartbeatDeadlinePolicy:
    if isinstance(policy, HeartbeatDeadlinePolicy):
        return policy
    deadline = policy.get("deadline_at")
    return HeartbeatDeadlinePolicy(
        deadline_at=_observed_at(deadline) if isinstance(deadline, datetime) else None,
        max_age_seconds=_optional_int(policy.get("max_age_seconds")),
        required=_bool_value(policy.get("required"), default=True),
        policy_ref=_string_value(policy.get("policy_ref")) or "heartbeat-deadline-policy",
    )


def _deadline_from_policy(
    event: HeartbeatEvent | None,
    policy: HeartbeatDeadlinePolicy,
    now: datetime,
) -> datetime | None:
    if event is not None and event.deadline_at is not None:
        return _observed_at(event.deadline_at)
    if policy.deadline_at is not None:
        return _observed_at(policy.deadline_at)
    if event is not None and policy.max_age_seconds is not None:
        return now - timedelta(seconds=max(policy.max_age_seconds, 0))
    return None


def _heartbeat_deadline_failed(
    event: HeartbeatEvent,
    policy: HeartbeatDeadlinePolicy,
    observed_at: datetime,
    deadline_at: datetime | None,
) -> bool:
    if deadline_at is None:
        return False
    if event.deadline_at is not None or policy.deadline_at is not None:
        return observed_at > deadline_at
    if policy.max_age_seconds is not None:
        return observed_at < deadline_at
    return False


def _build_incident_candidate(
    *,
    reason: str,
    stage: str,
    source: str,
    heartbeat_ref: str,
    policy_ref: str,
    observed_at: datetime,
) -> HeartbeatIncidentCandidate:
    safe_stage = _safe_label(stage)
    safe_source = _safe_ref(source)
    safe_heartbeat_ref = _safe_ref(heartbeat_ref)
    safe_policy_ref = _safe_ref(policy_ref)
    payload = "|".join(
        [
            reason,
            safe_stage,
            safe_source,
            safe_heartbeat_ref,
            safe_policy_ref,
            observed_at.isoformat(),
        ]
    )
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    redacted = any(
        value.startswith("redacted:")
        for value in (safe_source, safe_heartbeat_ref, safe_policy_ref)
    )
    return HeartbeatIncidentCandidate(
        incident_id=f"incident-candidate:{digest[:16]}",
        incident_kind=HEARTBEAT_INCIDENT_KIND,
        reason=reason,
        stage=safe_stage,
        source_ref=safe_source,
        heartbeat_ref=safe_heartbeat_ref,
        evidence_ref=f"heartbeat:{digest[:12]}",
        redaction_status="redacted" if redacted else "pass",
        safety_counters=monitoring_safety_counters(),
    )


def _heartbeat_ref(event: HeartbeatEvent) -> str:
    payload = f"{event.source}|{event.stage}|{_observed_at(event.observed_at).isoformat()}"
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    return f"heartbeat:{digest[:16]}"


def _safe_label(value: object) -> str:
    raw = _string_value(value)
    if not raw:
        return ""
    if _is_sensitive_text(raw):
        return _redacted_ref(raw)
    allowed = []
    for char in raw:
        if char.isalnum() or char in {"_", "-", ".", ":", "#"}:
            allowed.append(char)
        elif char.isspace():
            allowed.append("-")
    return "".join(allowed)[:96] or _redacted_ref(raw)


def _safe_ref(value: object) -> str:
    raw = _string_value(value)
    if not raw:
        return ""
    if _is_sensitive_text(raw):
        return _redacted_ref(raw)
    return _safe_label(raw)


def _is_sensitive_text(value: str) -> bool:
    return any(pattern.search(value) for pattern in _SENSITIVE_TEXT_PATTERNS)


def _redacted_ref(value: str) -> str:
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()
    return f"redacted:{digest[:12]}"


def _observed_at(value: datetime | None) -> datetime:
    if value is None:
        return datetime.now(tz=UTC)
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _string_value(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, Enum):
        return str(value.value)
    return str(value).strip()


def _optional_int(value: object) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _bool_value(value: object, *, default: bool) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}
