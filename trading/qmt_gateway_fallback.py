"""CR019-S08 的 QMT gateway fallback 离线合同。

本模块只构造 fail-closed decision、manual-only dry-run payload 和脱敏 incident
candidate，不启动服务、不打开网络、不触发真实 QMT / broker 操作。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Mapping

from trading.qmt_gateway_contracts import (
    QmtBlockedReason,
    QmtGatewayResult,
    build_blocked_result,
    collect_qmt_gateway_contract_counters,
)
from trading.qmt_redaction import redact_qmt_mapping, scan_for_qmt_sensitive_leaks


QMT_GATEWAY_FALLBACK_SCHEMA_VERSION = "cr019-s08-qmt-gateway-fallback-v1"
SIGNED_DRY_RUN_SCHEMA_VERSION = "cr019.signed-dry-run.v1"
SIGNED_DRY_RUN_MODE = "manual_dry_run_only"

_REQUEST_CONTEXT_PUBLIC_KEYS = frozenset(
    {
        "run_id",
        "intent_id",
        "request_ref",
        "endpoint_id",
        "stage",
        "mode",
        "event_ref",
        "heartbeat_ref",
        "deployment_ref",
        "client_id_hash",
        "redaction_status",
    }
)
_VALID_SIGNING_STATUS = "test_signed"
_FORBIDDEN_TRUE_FIELDS = (
    "auto_execute",
    "real_qmt_allowed",
    "operation_authorized",
    "broker_lake_write_allowed",
    "simulation_live_allowed",
)
_FORBIDDEN_ACTION_FIELDS = (
    "execute",
    "submit_order",
    "place_order",
    "cancel_order",
    "query_account",
    "adapter_call",
    "qmt_api_call",
    "provider_fetch",
    "lake_write",
    "broker_lake_write",
    "publish",
    "run_simulation",
)
_FALLBACK_COUNTER_FIELDS = (
    "real_order_call",
    "real_cancel_call",
    "cancel_order_call",
    "account_query_call",
    "account_write_call",
    "real_lake_write",
    "real_broker_lake_write",
    "real_broker_operation",
    "simulation_run",
    "live_run",
    "small_live_run",
    "scale_up_run",
    "adapter_call",
    "adapter_calls",
    "incident_persisted",
    "fallback_real_qmt_attempt",
    "signed_file_auto_execute_claim",
)


class FallbackTrigger(str, Enum):
    """S08 固定支持的 fail-closed fallback 触发类型。"""

    GATEWAY_UNREACHABLE = "gateway_unreachable"
    AUTH_FAILED = "auth_failed"
    HEARTBEAT_FAILED = "heartbeat_failed"
    DEPLOYMENT_NOT_READY = "deployment_not_ready"
    RUN_GATE_BLOCKED = "run_gate_blocked"


class SignedDryRunSigningStatus(str, Enum):
    """manual-only payload 的离线签名状态。"""

    UNSIGNED = "unsigned"
    TEST_SIGNED = "test_signed"
    SIGNATURE_REQUIRED = "signature_required"
    EXPIRED = "expired"


@dataclass(frozen=True, slots=True)
class FallbackPolicy:
    """fallback policy 只控制是否允许人工 dry-run 文件候选。"""

    manual_dry_run_allowed: bool = False


@dataclass(frozen=True, slots=True)
class FallbackDecision:
    """fallback 决策固定为 blocked，不包含任何真实执行授权。"""

    trigger: FallbackTrigger
    blocked_reason: str
    incident_candidate: Mapping[str, object]
    manual_dry_run_allowed: bool = False
    safety_counters: Mapping[str, int] = field(
        default_factory=lambda: collect_qmt_gateway_fallback_safety_counters()
    )
    next_action: str = "return_typed_blocked_result"
    upstream_reason: str = ""
    redaction_status: str = "redacted"
    status: str = "blocked"
    schema_version: str = QMT_GATEWAY_FALLBACK_SCHEMA_VERSION

    @property
    def blocked(self) -> bool:
        return self.status == "blocked"

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "status": self.status,
            "blocked": self.blocked,
            "trigger": self.trigger.value,
            "blocked_reason": self.blocked_reason,
            "upstream_reason": self.upstream_reason,
            "incident_candidate": dict(self.incident_candidate),
            "manual_dry_run_allowed": self.manual_dry_run_allowed,
            "safety_counters": dict(self.safety_counters),
            "next_action": self.next_action,
            "redaction_status": self.redaction_status,
        }

    def to_blocked_result(self, endpoint_id: str = "qmt_fallback") -> QmtGatewayResult:
        """转换为 S06 typed blocked result，供 gateway / client 聚合层消费。"""

        return build_blocked_result(
            endpoint_id,
            QmtBlockedReason.FALLBACK_BLOCKED,
            f"fallback blocked by {self.blocked_reason}",
            detail={
                "fallback_trigger": self.trigger.value,
                "fallback_schema_version": self.schema_version,
                "manual_dry_run_allowed": self.manual_dry_run_allowed,
                "next_action": self.next_action,
                "incident_candidate": dict(self.incident_candidate),
            },
            counters=self.safety_counters,
            redaction_status=self.redaction_status,
        )


@dataclass(frozen=True, slots=True)
class SignedDryRunValidationResult:
    """signed dry-run payload 校验结果；失败时仍 fail closed。"""

    valid: bool
    blocked_reason: str = ""
    message: str = ""
    payload_summary: Mapping[str, object] = field(default_factory=dict)
    safety_counters: Mapping[str, int] = field(
        default_factory=lambda: collect_qmt_gateway_fallback_safety_counters()
    )
    schema_version: str = QMT_GATEWAY_FALLBACK_SCHEMA_VERSION

    @property
    def status(self) -> str:
        return "valid" if self.valid else "blocked"

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "status": self.status,
            "valid": self.valid,
            "blocked": not self.valid,
            "blocked_reason": self.blocked_reason,
            "message": self.message,
            "payload_summary": dict(self.payload_summary),
            "safety_counters": dict(self.safety_counters),
        }

    def to_blocked_result(self, endpoint_id: str = "signed_dry_run_payload") -> QmtGatewayResult:
        """把 invalid payload 暴露为 S06 typed blocked result。"""

        reason = self.blocked_reason or "payload_validation_blocked"
        return build_blocked_result(
            endpoint_id,
            QmtBlockedReason.FALLBACK_BLOCKED,
            self.message or f"signed dry-run payload blocked: {reason}",
            detail={
                "validation_status": self.status,
                "validation_reason": reason,
                "payload_summary": dict(self.payload_summary),
                "fallback_schema_version": self.schema_version,
            },
            counters=self.safety_counters,
        )


def build_fallback_decision(
    trigger: FallbackTrigger | str,
    request_context: Mapping[str, object] | None = None,
    upstream_result: Mapping[str, object] | object | None = None,
    policy: FallbackPolicy | Mapping[str, object] | None = None,
) -> FallbackDecision:
    """生成 fail-closed fallback decision；不触达任何真实 adapter。"""

    resolved_trigger = _coerce_trigger(trigger)
    public_context, redaction_status = _public_request_context(request_context or {})
    upstream_reason = _upstream_reason(upstream_result)
    blocked_reason = _blocked_reason_for(resolved_trigger, upstream_reason)
    manual_allowed = _policy_allows_manual_dry_run(policy)
    counters = collect_qmt_gateway_fallback_safety_counters()
    incident_candidate = _incident_candidate_from_parts(
        trigger=resolved_trigger,
        blocked_reason=blocked_reason,
        public_context=public_context,
        manual_dry_run_allowed=manual_allowed,
        counters=counters,
        redaction_status=redaction_status,
    )
    return FallbackDecision(
        trigger=resolved_trigger,
        blocked_reason=blocked_reason,
        upstream_reason=upstream_reason,
        incident_candidate=incident_candidate,
        manual_dry_run_allowed=manual_allowed,
        safety_counters=counters,
        next_action=(
            "manual_dry_run_file_candidate_only"
            if manual_allowed
            else "return_typed_blocked_result"
        ),
        redaction_status=redaction_status,
    )


def build_signed_dry_run_payload(
    decision: FallbackDecision,
    *,
    intent_ref: str,
    now: datetime | None = None,
    ttl_seconds: int = 300,
    signing_status: SignedDryRunSigningStatus | str = SignedDryRunSigningStatus.TEST_SIGNED,
) -> dict[str, object]:
    """构造 manual-only dry-run payload；不写文件、不提交真实 QMT 操作。"""

    current = _coerce_datetime(now)
    expires_at = _add_seconds(current, ttl_seconds)
    signing_value = _enum_value(signing_status)
    return {
        "schema_version": SIGNED_DRY_RUN_SCHEMA_VERSION,
        "fallback_schema_version": decision.schema_version,
        "payload_id": f"manual-dry-run:{decision.trigger.value}:{intent_ref}",
        "mode": SIGNED_DRY_RUN_MODE,
        "status": "blocked",
        "fallback_trigger": decision.trigger.value,
        "blocked_reason": decision.blocked_reason,
        "intent_ref": str(intent_ref),
        "incident_candidate_ref": decision.incident_candidate.get("incident_candidate_ref", ""),
        "created_at": current.isoformat(),
        "expires_at": expires_at.isoformat(),
        "signing_status": signing_value,
        "manual_handling_required": True,
        "auto_execute": False,
        "real_qmt_allowed": False,
        "operation_authorized": False,
        "broker_lake_write_allowed": False,
        "simulation_live_allowed": False,
        "next_action": "manual_review_only",
        "redaction_status": "redacted",
        "safety_counters": dict(decision.safety_counters),
    }


def validate_signed_dry_run_payload(
    payload: Mapping[str, object] | object,
    *,
    now: datetime | None = None,
) -> SignedDryRunValidationResult:
    """校验 manual-only payload；任何异常都返回 blocked。"""

    current = _coerce_datetime(now)
    counters = collect_qmt_gateway_fallback_safety_counters()
    if not isinstance(payload, Mapping):
        return _invalid_payload("payload_schema_invalid", "payload must be a mapping", {}, counters)

    summary = _payload_summary(payload)
    if payload.get("schema_version") != SIGNED_DRY_RUN_SCHEMA_VERSION:
        return _invalid_payload(
            "payload_schema_invalid",
            "signed dry-run payload schema version is invalid",
            summary,
            counters,
        )
    if payload.get("mode") != SIGNED_DRY_RUN_MODE:
        return _invalid_payload(
            "payload_mode_not_manual_only",
            "signed dry-run payload mode must be manual_dry_run_only",
            summary,
            counters,
        )
    for field_name in _FORBIDDEN_TRUE_FIELDS:
        if field_name not in payload or payload.get(field_name) is not False:
            return _invalid_payload(
                "auto_execution_field_enabled",
                f"{field_name} must remain false",
                summary,
                counters,
            )
    if payload.get("manual_handling_required") is not True:
        return _invalid_payload(
            "manual_handling_required_missing",
            "manual handling must be explicitly required",
            summary,
            counters,
        )
    forbidden_action = _first_forbidden_action_field(payload)
    if forbidden_action:
        return _invalid_payload(
            "auto_execution_field_present",
            f"{forbidden_action} cannot be present as an enabled action field",
            summary,
            counters,
        )

    signing_status = str(payload.get("signing_status") or "")
    if signing_status != _VALID_SIGNING_STATUS:
        return _invalid_payload(
            "signature_not_valid",
            "signed dry-run payload is not in test_signed status",
            summary,
            counters,
        )

    expires_at = _parse_datetime(payload.get("expires_at"))
    if expires_at is None:
        return _invalid_payload(
            "payload_expiry_invalid",
            "expires_at is required and must be an ISO timestamp",
            summary,
            counters,
        )
    if expires_at <= current:
        return _invalid_payload(
            "payload_expired",
            "signed dry-run payload is expired",
            summary,
            counters,
        )

    leak_report = scan_for_qmt_sensitive_leaks(payload)
    if leak_report.leak_count:
        return _invalid_payload(
            "sensitive_payload_field",
            "signed dry-run payload contains visible sensitive content",
            {
                **summary,
                "redaction_status": leak_report.redaction_status,
                "matched_categories": list(leak_report.matched_categories),
            },
            counters,
        )

    non_zero = _non_zero_counters(payload.get("safety_counters"))
    if non_zero:
        return _invalid_payload(
            "forbidden_counter_nonzero",
            "signed dry-run payload contains non-zero forbidden counters",
            {**summary, "non_zero_counters": non_zero},
            counters,
        )

    return SignedDryRunValidationResult(
        valid=True,
        payload_summary=summary,
        safety_counters=counters,
    )


def format_incident_candidate(
    decision: FallbackDecision,
    payload: Mapping[str, object] | None = None,
) -> dict[str, object]:
    """返回脱敏 incident candidate；不持久化真实 incident。"""

    candidate: dict[str, object] = {
        **dict(decision.incident_candidate),
        "status": "candidate_only",
        "incident_persisted": False,
        "broker_lake_write": False,
        "real_qmt_allowed": False,
        "safety_counters": dict(decision.safety_counters),
    }
    if payload is not None:
        candidate["payload_summary"] = _payload_summary(payload)
    redacted, report = redact_qmt_mapping(candidate)
    redacted["redaction_status"] = report.redaction_status
    redacted["sensitive_raw_value_output"] = report.leak_count
    return redacted


def collect_qmt_gateway_fallback_safety_counters(
    counters: Mapping[str, int] | None = None,
) -> dict[str, int]:
    """返回 S08 禁止操作计数；默认全部为 0。"""

    normalized = collect_qmt_gateway_contract_counters()
    normalized.update({key: 0 for key in _FALLBACK_COUNTER_FIELDS})
    if counters is None:
        return normalized
    for key, value in counters.items():
        normalized[str(key)] = int(value)
    return normalized


def _incident_candidate_from_parts(
    *,
    trigger: FallbackTrigger,
    blocked_reason: str,
    public_context: Mapping[str, object],
    manual_dry_run_allowed: bool,
    counters: Mapping[str, int],
    redaction_status: str,
) -> dict[str, object]:
    run_id = str(public_context.get("run_id") or "run-ref-unset")
    intent_id = str(public_context.get("intent_id") or "intent-ref-unset")
    return {
        "schema_version": QMT_GATEWAY_FALLBACK_SCHEMA_VERSION,
        "incident_candidate_ref": f"incident-candidate:{trigger.value}:{run_id}:{intent_id}",
        "trigger": trigger.value,
        "blocked_reason": blocked_reason,
        "request_context": dict(public_context),
        "manual_dry_run_allowed": manual_dry_run_allowed,
        "manual_handling_required": manual_dry_run_allowed,
        "status": "candidate_only",
        "incident_persisted": False,
        "broker_lake_write": False,
        "real_qmt_allowed": False,
        "next_action": (
            "manual_dry_run_file_candidate_only"
            if manual_dry_run_allowed
            else "return_typed_blocked_result"
        ),
        "redaction_status": redaction_status,
        "safety_counters": dict(counters),
    }


def _public_request_context(context: Mapping[str, object]) -> tuple[dict[str, object], str]:
    public = {
        str(key): value
        for key, value in context.items()
        if str(key) in _REQUEST_CONTEXT_PUBLIC_KEYS
    }
    redacted, report = redact_qmt_mapping(public)
    return redacted, report.redaction_status


def _coerce_trigger(trigger: FallbackTrigger | str) -> FallbackTrigger:
    if isinstance(trigger, FallbackTrigger):
        return trigger
    try:
        return FallbackTrigger(str(trigger))
    except ValueError as exc:
        raise ValueError(f"unsupported fallback trigger: {trigger}") from exc


def _policy_allows_manual_dry_run(
    policy: FallbackPolicy | Mapping[str, object] | None,
) -> bool:
    if policy is None:
        return False
    if isinstance(policy, FallbackPolicy):
        return policy.manual_dry_run_allowed
    return bool(policy.get("manual_dry_run_allowed", False))


def _blocked_reason_for(trigger: FallbackTrigger, upstream_reason: str) -> str:
    if trigger is FallbackTrigger.RUN_GATE_BLOCKED and upstream_reason:
        return upstream_reason
    defaults = {
        FallbackTrigger.GATEWAY_UNREACHABLE: QmtBlockedReason.TRANSPORT_UNAVAILABLE.value,
        FallbackTrigger.AUTH_FAILED: QmtBlockedReason.AUTH_BLOCKED.value,
        FallbackTrigger.HEARTBEAT_FAILED: "heartbeat_failed",
        FallbackTrigger.DEPLOYMENT_NOT_READY: "deployment_not_ready",
        FallbackTrigger.RUN_GATE_BLOCKED: QmtBlockedReason.QMT_OPERATION_NOT_AUTHORIZED.value,
    }
    return defaults[trigger]


def _upstream_reason(upstream_result: Mapping[str, object] | object | None) -> str:
    if upstream_result is None:
        return ""
    if isinstance(upstream_result, Mapping):
        for key in ("blocked_reason", "reason_code", "blocked_by", "status"):
            value = upstream_result.get(key)
            if value:
                return _enum_value(value)
        error = upstream_result.get("error")
        if isinstance(error, Mapping):
            value = error.get("blocked_reason") or error.get("code")
            return _enum_value(value) if value else ""
        return ""
    for attr in ("blocked_reason", "reason_code", "blocked_by", "status"):
        value = getattr(upstream_result, attr, None)
        if value:
            return _enum_value(value)
    return ""


def _payload_summary(payload: Mapping[str, object]) -> dict[str, object]:
    return {
        "schema_version": payload.get("schema_version", ""),
        "payload_id": payload.get("payload_id", ""),
        "mode": payload.get("mode", ""),
        "fallback_trigger": payload.get("fallback_trigger", ""),
        "blocked_reason": payload.get("blocked_reason", ""),
        "signing_status": payload.get("signing_status", ""),
        "expires_at": payload.get("expires_at", ""),
        "auto_execute": payload.get("auto_execute", None),
        "real_qmt_allowed": payload.get("real_qmt_allowed", None),
        "manual_handling_required": payload.get("manual_handling_required", None),
    }


def _invalid_payload(
    reason: str,
    message: str,
    summary: Mapping[str, object],
    counters: Mapping[str, int],
) -> SignedDryRunValidationResult:
    return SignedDryRunValidationResult(
        valid=False,
        blocked_reason=reason,
        message=message,
        payload_summary=summary,
        safety_counters=counters,
    )


def _first_forbidden_action_field(payload: Mapping[str, object]) -> str:
    for field_name in _FORBIDDEN_ACTION_FIELDS:
        if field_name in payload and _truthy(payload.get(field_name)):
            return field_name
    return ""


def _non_zero_counters(value: object) -> dict[str, int]:
    if not isinstance(value, Mapping):
        return {}
    counters = collect_qmt_gateway_fallback_safety_counters(value)  # type: ignore[arg-type]
    return {key: count for key, count in counters.items() if int(count) != 0}


def _parse_datetime(value: object) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return _coerce_datetime(parsed)


def _add_seconds(value: datetime, seconds: int) -> datetime:
    return datetime.fromtimestamp(int(value.timestamp()) + int(seconds), tz=timezone.utc)


def _coerce_datetime(value: datetime | None) -> datetime:
    current = value or datetime.now(timezone.utc)
    if current.tzinfo is None:
        return current.replace(tzinfo=timezone.utc)
    return current.astimezone(timezone.utc)


def _truthy(value: object) -> bool:
    if isinstance(value, str):
        return value.strip().lower() not in {"", "0", "false", "no", "none", "null"}
    return bool(value)


def _enum_value(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, Enum):
        return str(value.value)
    return str(value)
