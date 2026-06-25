"""非交易窗口可验证的 simulation operator evidence 合同。"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping, Sequence


SIMULATION_OPERATOR_EVIDENCE_SCHEMA_VERSION = "runner-simulation-operator-evidence-v1"

REQUIRED_OPERATOR_EVIDENCE_SECTIONS: tuple[str, ...] = (
    "schema_version",
    "status",
    "run_id",
    "authorization_ref",
    "runtime_authorization_granted",
    "small_live_or_live_authorized",
    "pre_positions",
    "target",
    "order_plan",
    "execution",
    "post_positions",
    "reconciliation",
    "stability_window",
    "persistence_policy",
    "redaction_policy",
)

REQUIRED_REDACTION_FLAGS: tuple[str, ...] = (
    "raw_payload_saved",
    "raw_account_saved",
    "raw_symbol_saved",
    "raw_broker_order_ref_saved",
    "secret_or_token_saved",
    "fund_detail_saved",
)

ALLOWED_EVIDENCE_MODES: tuple[str, ...] = (
    "runtime",
    "fixture",
    "preflight-only",
    "plan-only",
    "reconcile-only",
)


@dataclass(frozen=True, slots=True)
class SimulationEvidenceValidationResult:
    """evidence schema 检查结果；只返回字段名和原因，不复制 evidence 全文。"""

    status: str
    missing_sections: tuple[str, ...] = ()
    forbidden_flags: tuple[str, ...] = ()
    blocked_reason: str = ""
    mode: str = "fixture"
    schema_version: str = SIMULATION_OPERATOR_EVIDENCE_SCHEMA_VERSION
    safety_counters: Mapping[str, int] = field(default_factory=lambda: _zero_safety_counters())

    @property
    def passed(self) -> bool:
        return self.status == "pass"

    @property
    def blocked(self) -> bool:
        return self.status == "blocked"

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "status": self.status,
            "passed": self.passed,
            "blocked": self.blocked,
            "mode": self.mode,
            "missing_sections": list(self.missing_sections),
            "forbidden_flags": list(self.forbidden_flags),
            "blocked_reason": self.blocked_reason,
            "safety_counters": dict(self.safety_counters),
        }


def validate_operator_evidence(
    payload: Mapping[str, object],
    *,
    mode: str = "fixture",
) -> SimulationEvidenceValidationResult:
    """验证 P0-P4 operator evidence 是否只包含允许的脱敏结构。"""

    normalized_mode = mode if mode in ALLOWED_EVIDENCE_MODES else "fixture"
    missing = tuple(
        section for section in REQUIRED_OPERATOR_EVIDENCE_SECTIONS if section not in payload
    )
    if missing:
        return _blocked(
            normalized_mode,
            "missing_required_sections:" + ",".join(missing),
            missing_sections=missing,
        )
    redaction = _mapping(payload.get("redaction_policy"))
    forbidden = tuple(
        flag for flag in REQUIRED_REDACTION_FLAGS if redaction.get(flag) is not False
    )
    forbidden += _forbidden_persistence_flags(_mapping(payload.get("persistence_policy")))
    forbidden += _forbidden_position_flags(
        _mapping(payload.get("pre_positions")),
        _mapping(payload.get("post_positions")),
    )
    if payload.get("small_live_or_live_authorized") is not False:
        forbidden += ("small_live_or_live_authorized",)
    if normalized_mode != "runtime" and payload.get("runtime_authorization_granted") is not False:
        forbidden += ("runtime_authorization_granted_non_runtime",)
    if forbidden:
        return _blocked(
            normalized_mode,
            "forbidden_evidence_flags:" + ",".join(forbidden),
            forbidden_flags=forbidden,
        )
    return SimulationEvidenceValidationResult(status="pass", mode=normalized_mode)


def build_operator_evidence_index(
    payload: Mapping[str, object],
    *,
    evidence_ref: str,
    mode: str,
) -> dict[str, object]:
    """生成轻量 evidence index，供 runbook / checklist 引用。"""

    validation = validate_operator_evidence(payload, mode=mode)
    return {
        "schema_version": "runner-simulation-operator-evidence-index-v1",
        "status": "pass" if validation.passed else "blocked",
        "mode": mode,
        "run_id": str(payload.get("run_id") or ""),
        "evidence_ref": evidence_ref,
        "operator_schema_version": str(payload.get("schema_version") or ""),
        "sections": [
            section for section in REQUIRED_OPERATOR_EVIDENCE_SECTIONS if section in payload
        ],
        "validation": validation.to_dict(),
        "redaction_summary": {
            "raw_payload_saved": False,
            "raw_account_saved": False,
            "raw_symbol_saved": False,
            "raw_broker_order_ref_saved": False,
            "secret_or_token_saved": False,
            "fund_detail_saved": False,
        },
    }


def allowed_evidence_data_classes() -> tuple[dict[str, object], ...]:
    """返回文档和测试共用的允许 evidence 数据类型。"""

    return (
        {
            "data_class": "authorization",
            "allowed_fields": ("authorization_ref", "scope", "expiry", "operator_ref", "digest"),
        },
        {
            "data_class": "position_snapshot",
            "allowed_fields": ("digest", "bucket", "count", "instrument_ref", "redaction_status"),
        },
        {
            "data_class": "target_portfolio",
            "allowed_fields": ("target_count", "weight_bucket", "risk_summary", "instrument_ref"),
        },
        {
            "data_class": "order_plan",
            "allowed_fields": ("buy_count", "sell_count", "turnover_bucket", "intent_ref"),
        },
        {
            "data_class": "submit_cancel",
            "allowed_fields": ("accepted_count", "rejected_count", "unknown_count", "redacted_refs"),
        },
        {
            "data_class": "reconciliation",
            "allowed_fields": ("diff_count", "status", "manual_takeover_reason", "digest_refs"),
        },
    )


def _blocked(
    mode: str,
    reason: str,
    *,
    missing_sections: Sequence[str] = (),
    forbidden_flags: Sequence[str] = (),
) -> SimulationEvidenceValidationResult:
    return SimulationEvidenceValidationResult(
        status="blocked",
        mode=mode,
        blocked_reason=reason,
        missing_sections=tuple(missing_sections),
        forbidden_flags=tuple(forbidden_flags),
    )


def _mapping(value: object) -> dict[str, object]:
    return dict(value) if isinstance(value, Mapping) else {}


def _forbidden_persistence_flags(policy: Mapping[str, object]) -> tuple[str, ...]:
    flags = (
        "raw_payload_allowed",
        "broker_lake_write_allowed",
        "raw_account_allowed",
        "raw_symbol_allowed",
        "raw_broker_order_ref_allowed",
    )
    return tuple(flag for flag in flags if policy.get(flag) is not False)


def _forbidden_position_flags(
    pre_positions: Mapping[str, object],
    post_positions: Mapping[str, object],
) -> tuple[str, ...]:
    flags: list[str] = []
    for prefix, payload in (("pre", pre_positions), ("post", post_positions)):
        if payload.get("raw_payload_emitted") is True:
            flags.append(prefix + "_positions_raw_payload_emitted")
        if payload.get("redaction_status") not in {"pass", "redacted", "", None}:
            flags.append(prefix + "_positions_redaction_status")
    return tuple(flags)


def _zero_safety_counters() -> dict[str, int]:
    return {
        "credential_read": 0,
        "qmt_operation": 0,
        "qmt_api_call": 0,
        "real_order": 0,
        "real_cancel": 0,
        "account_query": 0,
        "account_write": 0,
        "provider_fetch": 0,
        "lake_write": 0,
        "publish": 0,
        "small_live_or_live": 0,
    }
