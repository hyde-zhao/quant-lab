"""CR016-S03 kill switch 离线合同。

本模块只生成冻结结果、planned-only cancel plan、incident candidate 和 recovery
gate 状态；不触发真实撤单、真实发单、账户查询、broker lake 写入或 incident
持久化。
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any, Iterable, Mapping, Sequence


KILL_SWITCH_SCHEMA_VERSION = "kill_switch_result_v1"
CANCEL_PLAN_SCHEMA_VERSION = "cancel_plan_v1"
INCIDENT_SCHEMA_VERSION = "incident_candidate_v1"
RECOVERY_GATE_SCHEMA_VERSION = "recovery_gate_v1"

FREEZE_STATUS_FROZEN = "frozen"
CANCEL_PLAN_STATUS_PLANNED_ONLY = "planned_only"
RECOVERY_GATE_STATUS_BLOCKED = "blocked"
RECOVERY_GATE_STATUS_RECOVERABLE = "recoverable"

_TERMINAL_STATES = frozenset({"filled", "canceled", "rejected", "failed", "blocked"})
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


class KillSwitchReason(str, Enum):
    """kill switch 触发原因稳定枚举。"""

    HEARTBEAT_FAIL = "heartbeat_fail"
    HEARTBEAT_MISSING = "heartbeat_missing"
    RECON_DIFF = "recon_diff"
    RECON_MANUAL_REVIEW = "recon_manual_review"
    RECON_KILL_SWITCH = "recon_kill_switch"
    MANUAL_TRIGGER = "manual_trigger"
    RISK_BLOCKED = "risk_blocked"
    RECOVERY_REQUIRED = "recovery_required"


@dataclass(frozen=True, slots=True)
class KillSwitchRequest:
    """kill switch trigger 输入合同。"""

    reason: KillSwitchReason | str
    stage: str
    request_ref: str = ""
    open_intents_ref: str = ""
    recon_report_ref: str = ""
    reconciliation_status: str = ""
    manual_trigger_ref: str = ""
    heartbeat_event_ref: str = ""
    risk_event_ref: str = ""
    manual_takeover_status: str = ""
    owner: str = "ops"
    action: str = "freeze_and_plan_cancel"
    evidence_refs: tuple[str, ...] = ()

    @classmethod
    def from_reconciliation_candidate(
        cls,
        candidate: Mapping[str, object],
        *,
        stage: str,
        open_intents_ref: str = "",
        manual_takeover_status: str = "",
    ) -> "KillSwitchRequest":
        """消费 CR016-S02 `to_kill_switch_candidate()` 输出。"""

        status = _string_value(candidate.get("trigger_status"))
        if status == "kill_switch":
            reason: KillSwitchReason = KillSwitchReason.RECON_KILL_SWITCH
        elif status == "manual_review":
            reason = KillSwitchReason.RECON_MANUAL_REVIEW
        else:
            reason = KillSwitchReason.RECON_DIFF
        source_report_id = _string_value(candidate.get("source_report_id"))
        return cls(
            reason=reason,
            stage=stage,
            request_ref=_string_value(candidate.get("candidate_id")),
            open_intents_ref=open_intents_ref,
            recon_report_ref=source_report_id,
            reconciliation_status=status,
            manual_takeover_status=manual_takeover_status,
            owner=_string_value(candidate.get("owner")) or "ops",
            action=_string_value(candidate.get("action")) or "manual_review",
            evidence_refs=(_string_value(candidate.get("candidate_id")),),
        )


@dataclass(frozen=True, slots=True)
class CancelPlanRef:
    """planned-only 撤单引用，不代表真实撤单。"""

    order_ref: str
    owner: str
    action: str


@dataclass(frozen=True, slots=True)
class CancelPlan:
    """planned-only cancel plan；真实撤单必须后续授权。"""

    plan_id: str
    schema_version: str
    stage: str
    plan_status: str
    cancelable_order_refs: tuple[str, ...]
    plan_items: tuple[CancelPlanRef, ...]
    requires_authorization: bool = True
    executed: bool = False
    real_cancel_call: int = 0
    safety_counters: Mapping[str, int] = field(
        default_factory=lambda: kill_switch_safety_counters()
    )


@dataclass(frozen=True, slots=True)
class IncidentCandidate:
    """kill switch incident candidate；不持久化，不输出敏感原值。"""

    incident_id: str
    schema_version: str
    incident_kind: str
    reason: KillSwitchReason
    stage: str
    owner: str
    action: str
    evidence_refs: tuple[str, ...]
    redaction_status: str
    storage_policy: str = "candidate_only_no_persist"
    persisted: bool = False
    safety_counters: Mapping[str, int] = field(
        default_factory=lambda: kill_switch_safety_counters()
    )


@dataclass(frozen=True, slots=True)
class RecoveryGateResult:
    """恢复门合同。"""

    schema_version: str
    recovery_gate_status: str
    reconciliation_status: str
    manual_takeover_status: str
    required_conditions: tuple[str, ...]
    missing_conditions: tuple[str, ...]
    new_order_allowed: bool
    blocked_reason: str = ""
    safety_counters: Mapping[str, int] = field(
        default_factory=lambda: kill_switch_safety_counters()
    )


@dataclass(frozen=True, slots=True)
class KillSwitchResult:
    """kill switch trigger 输出合同。"""

    schema_version: str
    request_id: str
    kill_switch_reason: KillSwitchReason
    stop_new_orders: bool
    new_order_allowed: bool
    freeze_status: str
    freeze_strategy: str
    cancel_plan_status: str
    cancel_plan: CancelPlan
    incident: IncidentCandidate
    recovery_gate_status: str
    recovery_gate: RecoveryGateResult
    safety_counters: Mapping[str, int] = field(
        default_factory=lambda: kill_switch_safety_counters()
    )


def build_cancel_plan(
    open_state: object,
    stage: str,
    *,
    owner: str = "ops",
    action: str = "cancel_when_authorized",
    now: datetime | None = None,
) -> CancelPlan:
    """从 open state 生成 planned-only refs，不执行真实撤单。"""

    observed_at = _observed_at(now)
    safe_stage = _safe_label(stage)
    safe_owner = _safe_label(owner) or "ops"
    safe_action = _safe_label(action) or "cancel_when_authorized"
    items = tuple(
        CancelPlanRef(order_ref=ref, owner=safe_owner, action=safe_action)
        for ref in _cancelable_order_refs(open_state)
    )
    plan_payload = "|".join(
        [safe_stage, safe_owner, safe_action, ",".join(item.order_ref for item in items)]
    )
    digest = hashlib.sha256(
        f"{plan_payload}|{observed_at.isoformat()}".encode("utf-8")
    ).hexdigest()
    return CancelPlan(
        plan_id=f"cancel-plan:{digest[:16]}",
        schema_version=CANCEL_PLAN_SCHEMA_VERSION,
        stage=safe_stage,
        plan_status=CANCEL_PLAN_STATUS_PLANNED_ONLY,
        cancelable_order_refs=tuple(item.order_ref for item in items),
        plan_items=items,
        requires_authorization=True,
        executed=False,
        real_cancel_call=0,
        safety_counters=kill_switch_safety_counters(),
    )


def kill_switch_trigger(
    request: KillSwitchRequest | Mapping[str, object],
    open_state: object,
    *,
    now: datetime | None = None,
) -> KillSwitchResult:
    """触发 kill switch，返回冻结、撤单计划、incident 和恢复门合同。"""

    observed_at = _observed_at(now)
    req = _coerce_request(request)
    reason = _normalize_reason(req)
    safe_stage = _safe_label(req.stage)
    request_id = _request_id(req, reason, observed_at)
    plan = build_cancel_plan(
        open_state,
        safe_stage,
        owner=req.owner,
        action="cancel_when_authorized",
        now=observed_at,
    )
    incident = _build_incident(req, reason, plan, observed_at)
    gate = recovery_gate(
        req.reconciliation_status,
        req.manual_takeover_status,
        evidence_ref=request_id,
    )

    return KillSwitchResult(
        schema_version=KILL_SWITCH_SCHEMA_VERSION,
        request_id=request_id,
        kill_switch_reason=reason,
        stop_new_orders=True,
        new_order_allowed=False,
        freeze_status=FREEZE_STATUS_FROZEN,
        freeze_strategy="local_freeze_only_no_broker_side_effect",
        cancel_plan_status=plan.plan_status,
        cancel_plan=plan,
        incident=incident,
        recovery_gate_status=gate.recovery_gate_status,
        recovery_gate=gate,
        safety_counters=kill_switch_safety_counters(),
    )


def recovery_gate(
    reconciliation_status: object,
    manual_takeover_status: object,
    *,
    evidence_ref: str = "",
) -> RecoveryGateResult:
    """恢复门：必须同时满足 reconciliation pass 与 manual takeover recorded。"""

    recon = _safe_label(reconciliation_status).lower()
    takeover = _safe_label(manual_takeover_status).lower()
    missing: list[str] = []
    if recon != "pass":
        missing.append("reconciliation_status=pass")
    if takeover != "recorded":
        missing.append("manual_takeover_status=recorded")

    if missing:
        return RecoveryGateResult(
            schema_version=RECOVERY_GATE_SCHEMA_VERSION,
            recovery_gate_status=RECOVERY_GATE_STATUS_BLOCKED,
            reconciliation_status=recon,
            manual_takeover_status=takeover,
            required_conditions=(
                "reconciliation_status=pass",
                "manual_takeover_status=recorded",
            ),
            missing_conditions=tuple(missing),
            new_order_allowed=False,
            blocked_reason="recovery_requirements_missing",
            safety_counters=kill_switch_safety_counters(),
        )

    return RecoveryGateResult(
        schema_version=RECOVERY_GATE_SCHEMA_VERSION,
        recovery_gate_status=RECOVERY_GATE_STATUS_RECOVERABLE,
        reconciliation_status="pass",
        manual_takeover_status="recorded",
        required_conditions=(
            "reconciliation_status=pass",
            "manual_takeover_status=recorded",
        ),
        missing_conditions=(),
        new_order_allowed=True,
        safety_counters=kill_switch_safety_counters(),
    )


def kill_switch_safety_counters() -> dict[str, int]:
    """返回 CR016-S03 必须保持为 0 的真实操作和安全计数。"""

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


def read_kill_switch_result(
    kill_context: KillSwitchResult | RecoveryGateResult | Mapping[str, object] | None,
) -> dict[str, object]:
    """把 heartbeat / kill-switch result 归一化为只读 gate view。"""

    if kill_context is None:
        return {
            "gate_name": "kill_switch",
            "passed": False,
            "status": "missing",
            "blocked_reason": KillSwitchReason.HEARTBEAT_MISSING.value,
            "required_evidence": ("kill_switch_result",),
            "safety_counters": kill_switch_safety_counters(),
        }

    if isinstance(kill_context, KillSwitchResult):
        counters = dict(kill_context.safety_counters)
        passed = not kill_context.stop_new_orders and kill_context.new_order_allowed
        status = "pass" if passed else "active"
        blocked_reason = "" if passed else kill_context.kill_switch_reason.value
        required_evidence = () if passed else ("kill_switch_recovery_gate",)
    elif isinstance(kill_context, RecoveryGateResult):
        counters = dict(kill_context.safety_counters)
        passed = (
            kill_context.recovery_gate_status == RECOVERY_GATE_STATUS_RECOVERABLE
            and kill_context.new_order_allowed
        )
        status = kill_context.recovery_gate_status
        blocked_reason = "" if passed else (kill_context.blocked_reason or "recovery_required")
        required_evidence = tuple(kill_context.missing_conditions)
    else:
        counters = dict(kill_context.get("safety_counters") or kill_switch_safety_counters())
        active = bool(kill_context.get("kill_switch_active", False))
        status = _string_value(
            kill_context.get("status")
            or kill_context.get("kill_switch_status")
            or ("active" if active else "pass")
        ).lower()
        passed = status in {"pass", "passed", "clear", "inactive", "recoverable"} and not active
        blocked_reason = _string_value(kill_context.get("blocked_reason"))
        if not passed and not blocked_reason:
            blocked_reason = _string_value(kill_context.get("reason")) or "kill_switch_active"
        required_evidence = tuple(
            _string_value(item)
            for item in (kill_context.get("required_evidence") or ())
            if _string_value(item)
        )

    nonzero_counters = tuple(
        key for key, value in counters.items() if int(value) != 0
    )
    if nonzero_counters:
        passed = False
        blocked_reason = "real_operation_forbidden"
        required_evidence = nonzero_counters
    return {
        "gate_name": "kill_switch",
        "passed": passed and not blocked_reason,
        "status": status,
        "blocked_reason": blocked_reason,
        "required_evidence": required_evidence,
        "safety_counters": counters,
    }


def sensitive_raw_value_output_count(
    rendered: object,
    sensitive_values: Iterable[str],
) -> int:
    """统计敏感原值在结构化输出中的出现次数。"""

    text = _render_for_scan(rendered)
    return sum(text.count(value) for value in sensitive_values if value)


def _coerce_request(request: KillSwitchRequest | Mapping[str, object]) -> KillSwitchRequest:
    if isinstance(request, KillSwitchRequest):
        return request
    evidence = request.get("evidence_refs", ())
    return KillSwitchRequest(
        reason=_string_value(request.get("reason")),
        stage=_string_value(request.get("stage")),
        request_ref=_string_value(request.get("request_ref")),
        open_intents_ref=_string_value(request.get("open_intents_ref")),
        recon_report_ref=_string_value(request.get("recon_report_ref")),
        reconciliation_status=_string_value(request.get("reconciliation_status")),
        manual_trigger_ref=_string_value(request.get("manual_trigger_ref")),
        heartbeat_event_ref=_string_value(request.get("heartbeat_event_ref")),
        risk_event_ref=_string_value(request.get("risk_event_ref")),
        manual_takeover_status=_string_value(request.get("manual_takeover_status")),
        owner=_string_value(request.get("owner")) or "ops",
        action=_string_value(request.get("action")) or "freeze_and_plan_cancel",
        evidence_refs=tuple(_string_value(item) for item in _sequence_value(evidence)),
    )


def _normalize_reason(request: KillSwitchRequest) -> KillSwitchReason:
    raw_reason = _string_value(request.reason).lower()
    recon_status = _string_value(request.reconciliation_status).lower()
    if recon_status == "kill_switch" or raw_reason in {"kill_switch", "recon_kill"}:
        return KillSwitchReason.RECON_KILL_SWITCH
    if recon_status == "manual_review" or raw_reason in {
        "manual_review",
        "recon_manual_review",
    }:
        return KillSwitchReason.RECON_MANUAL_REVIEW
    aliases = {
        "heartbeat_timeout": KillSwitchReason.HEARTBEAT_FAIL,
        "heartbeat_status_fail": KillSwitchReason.HEARTBEAT_FAIL,
        "heartbeat_missing": KillSwitchReason.HEARTBEAT_MISSING,
        "risk_fail": KillSwitchReason.RISK_BLOCKED,
        "risk_block": KillSwitchReason.RISK_BLOCKED,
        "manual": KillSwitchReason.MANUAL_TRIGGER,
        "manual_triggered": KillSwitchReason.MANUAL_TRIGGER,
    }
    if raw_reason in aliases:
        return aliases[raw_reason]
    try:
        return KillSwitchReason(raw_reason)
    except ValueError:
        return KillSwitchReason.MANUAL_TRIGGER if request.manual_trigger_ref else KillSwitchReason.RECON_DIFF


def _request_id(
    request: KillSwitchRequest,
    reason: KillSwitchReason,
    observed_at: datetime,
) -> str:
    safe_request_ref = _safe_ref(request.request_ref)
    if safe_request_ref:
        return safe_request_ref
    payload = "|".join(
        [
            reason.value,
            _safe_label(request.stage),
            _safe_ref(request.open_intents_ref),
            _safe_ref(request.recon_report_ref),
            _safe_ref(request.manual_trigger_ref),
            _safe_ref(request.heartbeat_event_ref),
            _safe_ref(request.risk_event_ref),
            observed_at.isoformat(),
        ]
    )
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    return f"kill-switch-request:{digest[:16]}"


def _build_incident(
    request: KillSwitchRequest,
    reason: KillSwitchReason,
    plan: CancelPlan,
    observed_at: datetime,
) -> IncidentCandidate:
    evidence_refs = tuple(
        ref
        for ref in (
            _safe_ref(request.request_ref),
            _safe_ref(request.open_intents_ref),
            _safe_ref(request.recon_report_ref),
            _safe_ref(request.manual_trigger_ref),
            _safe_ref(request.heartbeat_event_ref),
            _safe_ref(request.risk_event_ref),
            *(_safe_ref(item) for item in request.evidence_refs),
            plan.plan_id,
        )
        if ref
    )
    payload = "|".join(
        [
            reason.value,
            _safe_label(request.stage),
            _safe_label(request.owner),
            _safe_label(request.action),
            ",".join(evidence_refs),
            observed_at.isoformat(),
        ]
    )
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    redacted = any(ref.startswith("redacted:") for ref in evidence_refs)
    return IncidentCandidate(
        incident_id=f"incident-candidate:{digest[:16]}",
        schema_version=INCIDENT_SCHEMA_VERSION,
        incident_kind="kill_switch_incident_candidate",
        reason=reason,
        stage=_safe_label(request.stage),
        owner=_safe_label(request.owner) or "ops",
        action=_safe_label(request.action) or "freeze_and_plan_cancel",
        evidence_refs=evidence_refs,
        redaction_status="redacted" if redacted else "pass",
        persisted=False,
        safety_counters=kill_switch_safety_counters(),
    )


def _cancelable_order_refs(open_state: object) -> tuple[str, ...]:
    refs: list[str] = []
    for item in _iter_open_items(open_state):
        if _is_terminal_item(item):
            continue
        ref = _order_ref(item)
        if ref:
            refs.append(ref)
    return tuple(dict.fromkeys(refs))


def _iter_open_items(open_state: object) -> tuple[object, ...]:
    if open_state is None:
        return ()
    if isinstance(open_state, Mapping):
        for key in (
            "open_intents",
            "open_orders",
            "intents",
            "orders",
            "cancelable_orders",
            "cancelable_order_refs",
        ):
            value = open_state.get(key)
            if value is not None:
                if _is_sequence(value):
                    return tuple(value)  # type: ignore[arg-type]
                return (value,)
        return (open_state,)
    if _is_sequence(open_state):
        return tuple(open_state)  # type: ignore[arg-type]
    return (open_state,)


def _is_terminal_item(item: object) -> bool:
    state = _item_value(item, "state", _item_value(item, "order_state", ""))
    return _string_value(state).lower() in _TERMINAL_STATES


def _order_ref(item: object) -> str:
    if isinstance(item, str):
        return _safe_ref(item)
    for key in (
        "cancel_plan_ref",
        "broker_order_ref",
        "order_ref",
        "order_intent_id",
        "intent_id",
        "ref",
    ):
        value = _item_value(item, key, "")
        ref = _safe_ref(value)
        if ref:
            return ref
    digest = hashlib.sha256(_render_for_scan(item).encode("utf-8")).hexdigest()
    return f"open-item:{digest[:16]}"


def _item_value(item: object, key: str, default: object) -> object:
    if isinstance(item, Mapping):
        return item.get(key, default)
    return getattr(item, key, default)


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


def _render_for_scan(rendered: object) -> str:
    def default(value: object) -> str:
        if isinstance(value, Enum):
            return str(value.value)
        if hasattr(value, "__dataclass_fields__"):
            return str(asdict(value))
        return str(value)

    return json.dumps(rendered, sort_keys=True, default=default, ensure_ascii=False)


def _sequence_value(value: object) -> tuple[object, ...]:
    if value is None:
        return ()
    if _is_sequence(value):
        return tuple(value)  # type: ignore[arg-type]
    return (value,)


def _is_sequence(value: object) -> bool:
    return isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray))


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
