"""CR014-S08 unsupported / blocked capability decision matrix."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from .contracts import CR014_FORBIDDEN_OPERATION_COUNTERS

CAPABILITY_W3_SOURCE_INTERFACE = "w3_source_interface"
CAPABILITY_MINUTE_BAR = "minute_bar"
CAPABILITY_TICK_TRADE = "tick_trade"
CAPABILITY_LEVEL2_ORDER_BOOK = "level2_order_book"
CAPABILITY_ORDER_BOOK = "order_book"
CAPABILITY_ORDER_MATCH_EXECUTION = "order_match_execution"
CAPABILITY_EXECUTION_DETAIL = "execution_detail"
CAPABILITY_REAL_VWAP_EXECUTION = "real_vwap_execution"
CAPABILITY_VWAP_FILL_CLAIM = "vwap_fill_claim"
CAPABILITY_MICROSTRUCTURE_IMPACT_COST = "microstructure_impact_cost"

CR014_UNSUPPORTED_CAPABILITY_ORDER: tuple[str, ...] = (
    CAPABILITY_W3_SOURCE_INTERFACE,
    CAPABILITY_MINUTE_BAR,
    CAPABILITY_TICK_TRADE,
    CAPABILITY_LEVEL2_ORDER_BOOK,
    CAPABILITY_ORDER_BOOK,
    CAPABILITY_ORDER_MATCH_EXECUTION,
    CAPABILITY_EXECUTION_DETAIL,
    CAPABILITY_REAL_VWAP_EXECUTION,
    CAPABILITY_VWAP_FILL_CLAIM,
    CAPABILITY_MICROSTRUCTURE_IMPACT_COST,
)
CR014_UNSUPPORTED_CAPABILITY_SET = frozenset(CR014_UNSUPPORTED_CAPABILITY_ORDER)

CR014_BASE_RELEASE_CONDITIONS: tuple[str, ...] = (
    "source_interface_confirmed",
    "new_story_defined",
    "cp5_approved",
    "user_authorized",
)
CR014_REAL_VWAP_RELEASE_CONDITIONS: tuple[str, ...] = (
    *CR014_BASE_RELEASE_CONDITIONS,
    "vwap_field_present",
    "vwap_status=available",
    "execution_audit_passed",
)

CR014_REAL_VWAP_CAPABILITIES = frozenset(
    {
        CAPABILITY_REAL_VWAP_EXECUTION,
        CAPABILITY_VWAP_FILL_CLAIM,
    }
)

CR014_REAL_VWAP_PRODUCTION_CLAIMS: tuple[str, ...] = (
    "real_vwap_execution",
    "vwap_fill_claim",
    "vwap_execution",
    "real_fill_execution",
    "true_fillability",
)
CR014_MICROSTRUCTURE_PRODUCTION_CLAIMS: tuple[str, ...] = (
    "w3_source_interface_production",
    "minute_execution",
    "tick_execution",
    "level2_execution",
    "order_book_execution",
    "order_match_execution",
    "execution_detail_available",
    "microstructure_impact_cost",
)
CR014_UNSUPPORTED_PRODUCTION_CLAIMS = frozenset(
    (*CR014_REAL_VWAP_PRODUCTION_CLAIMS, *CR014_MICROSTRUCTURE_PRODUCTION_CLAIMS)
)

CR014_DENIED_REAL_VWAP_SUBSTITUTES = frozenset(
    {
        "close_proxy",
        "close_price_proxy",
        "amount/volume",
        "amount_volume_derived_vwap",
        "derived_vwap",
        "derived_vwap_from_amount_volume",
    }
)

ERROR_MISSING_RELEASE_CONDITION = "missing_release_condition"
ERROR_DERIVED_VWAP_CLAIM_ATTEMPT = "derived_vwap_claim_attempt"
ERROR_CLOSE_PROXY_REAL_EXECUTION_CLAIM_ATTEMPT = "close_proxy_real_execution_claim_attempt"

_CAPABILITY_BLOCKED_CLAIMS: dict[str, tuple[str, ...]] = {
    CAPABILITY_W3_SOURCE_INTERFACE: ("w3_source_interface_production",),
    CAPABILITY_MINUTE_BAR: ("minute_execution",),
    CAPABILITY_TICK_TRADE: ("tick_execution",),
    CAPABILITY_LEVEL2_ORDER_BOOK: ("level2_execution",),
    CAPABILITY_ORDER_BOOK: ("order_book_execution",),
    CAPABILITY_ORDER_MATCH_EXECUTION: ("order_match_execution",),
    CAPABILITY_EXECUTION_DETAIL: ("execution_detail_available",),
    CAPABILITY_REAL_VWAP_EXECUTION: ("real_vwap_execution", "vwap_execution"),
    CAPABILITY_VWAP_FILL_CLAIM: ("vwap_fill_claim", "real_fill_execution"),
    CAPABILITY_MICROSTRUCTURE_IMPACT_COST: ("microstructure_impact_cost",),
}

_CAPABILITY_STATUSES: dict[str, str] = {
    CAPABILITY_W3_SOURCE_INTERFACE: "blocked",
    CAPABILITY_REAL_VWAP_EXECUTION: "blocked",
    CAPABILITY_VWAP_FILL_CLAIM: "blocked",
}


@dataclass(frozen=True, slots=True)
class UnsupportedCapabilityDecision:
    capability: str
    status: str
    production_allowed_claim: bool
    blocked_claims: tuple[str, ...]
    required_missing: tuple[dict[str, Any], ...]
    release_condition: tuple[str, ...]
    denied_substitutes: tuple[str, ...] = ()
    evidence_refs: tuple[str, ...] = ()
    reason_code: str = "cr014_s08_unsupported_capability"
    severity: str = "P0"

    def to_dict(self) -> dict[str, Any]:
        return {
            "capability": self.capability,
            "status": self.status,
            "production_allowed_claim": self.production_allowed_claim,
            "blocked_claims": list(self.blocked_claims),
            "required_missing": [dict(item) for item in self.required_missing],
            "release_condition": list(self.release_condition),
            "denied_substitutes": list(self.denied_substitutes),
            "evidence_refs": list(self.evidence_refs),
            "reason_code": self.reason_code,
            "severity": self.severity,
        }


@dataclass(frozen=True, slots=True)
class UnsupportedDecisionMatrix:
    decisions: tuple[UnsupportedCapabilityDecision, ...]
    as_of_trade_date: str = ""
    permission_counters: dict[str, int] | None = None

    @property
    def capability_set(self) -> frozenset[str]:
        return frozenset(decision.capability for decision in self.decisions)

    @property
    def production_allowed_claim_count(self) -> int:
        return sum(1 for decision in self.decisions if decision.production_allowed_claim)

    def to_dict(self) -> dict[str, Any]:
        counters = self.permission_counters or CR014_FORBIDDEN_OPERATION_COUNTERS
        return {
            "as_of_trade_date": self.as_of_trade_date,
            "capabilities": [decision.capability for decision in self.decisions],
            "production_allowed_claim_count": self.production_allowed_claim_count,
            "decisions": [decision.to_dict() for decision in self.decisions],
            "permission_counters": dict(counters),
        }


@dataclass(frozen=True, slots=True)
class ReleaseConditionValidationResult:
    passed: bool
    error_codes: tuple[str, ...] = ()
    details: tuple[dict[str, Any], ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "error_codes": list(self.error_codes),
            "details": [dict(item) for item in self.details],
        }


def get_cr014_unsupported_decision_matrix(
    as_of_trade_date: str | None = None,
    s05_claim_summary: Mapping[str, Any] | None = None,
) -> UnsupportedDecisionMatrix:
    """返回 CR014-S08 exact unsupported capability matrix，不访问外部数据。"""

    _ = s05_claim_summary
    decisions = tuple(_decision(capability) for capability in CR014_UNSUPPORTED_CAPABILITY_ORDER)
    return UnsupportedDecisionMatrix(
        decisions=decisions,
        as_of_trade_date=str(as_of_trade_date or ""),
        permission_counters=dict(CR014_FORBIDDEN_OPERATION_COUNTERS),
    )


def get_unsupported_decision(
    capability: str,
    matrix: UnsupportedDecisionMatrix | Mapping[str, Any] | Sequence[Any] | None = None,
) -> UnsupportedCapabilityDecision:
    """按 exact capability identifier 返回决策；不做 substring / fuzzy 匹配。"""

    decisions = _coerce_matrix(matrix).decisions
    for decision in decisions:
        if decision.capability == capability:
            return decision
    raise KeyError(capability)


def resolve_unsupported_capabilities(
    requested_capabilities: Sequence[str],
    matrix: UnsupportedDecisionMatrix | Mapping[str, Any] | Sequence[Any] | None = None,
) -> tuple[UnsupportedCapabilityDecision, ...]:
    """解析请求的 unsupported capability；仅 exact 命中才返回。"""

    by_capability = {decision.capability: decision for decision in _coerce_matrix(matrix).decisions}
    return tuple(
        by_capability[capability]
        for capability in requested_capabilities
        if capability in by_capability
    )


def coerce_unsupported_decision_matrix(
    matrix: UnsupportedDecisionMatrix | Mapping[str, Any] | Sequence[Any] | None = None,
) -> UnsupportedDecisionMatrix:
    """把 dict / sequence 输入转换为 unsupported decision matrix。"""

    return _coerce_matrix(matrix)


def validate_release_conditions_complete(
    matrix: UnsupportedDecisionMatrix | Mapping[str, Any] | Sequence[Any] | None = None,
) -> ReleaseConditionValidationResult:
    """校验每个 release condition 都包含 Story / CP5 / user authorization 等门控。"""

    errors: list[str] = []
    details: list[dict[str, Any]] = []
    for decision in _coerce_matrix(matrix).decisions:
        required = set(CR014_BASE_RELEASE_CONDITIONS)
        if decision.capability in CR014_REAL_VWAP_CAPABILITIES:
            required.update(CR014_REAL_VWAP_RELEASE_CONDITIONS)
        missing = tuple(condition for condition in required if condition not in decision.release_condition)
        if missing:
            errors.append(ERROR_MISSING_RELEASE_CONDITION)
            details.append(
                {
                    "capability": decision.capability,
                    "missing_release_condition": list(missing),
                }
            )
    return ReleaseConditionValidationResult(
        passed=not errors,
        error_codes=tuple(dict.fromkeys(errors)),
        details=tuple(details),
    )


def blocked_claim_rows(
    matrix: UnsupportedDecisionMatrix | Mapping[str, Any] | Sequence[Any] | None = None,
) -> tuple[dict[str, Any], ...]:
    """导出可并入 S05 `blocked_claims` 的结构化行。"""

    rows: list[dict[str, Any]] = []
    for decision in _coerce_matrix(matrix).decisions:
        for claim in decision.blocked_claims:
            rows.append(
                {
                    "claim": claim,
                    "claim_scope": "unsupported_capability_production",
                    "capability": decision.capability,
                    "gap_code": f"{decision.capability}_unsupported",
                    "evidence_path": f"unsupported://cr014-s08/{decision.capability}",
                    "remediation": "route_to_future_source_interface_story_cp5_user_authorization",
                    "release_condition": list(decision.release_condition),
                    "production_allowed_claim": False,
                    "unsupported_status": decision.status,
                    "denied_substitutes": list(decision.denied_substitutes),
                    "reason_code": decision.reason_code,
                    "severity": decision.severity,
                }
            )
    return tuple(rows)


def required_missing_rows(
    matrix: UnsupportedDecisionMatrix | Mapping[str, Any] | Sequence[Any] | None = None,
) -> tuple[dict[str, Any], ...]:
    """导出可并入 S05 `required_missing` 的结构化行。"""

    rows: list[dict[str, Any]] = []
    for decision in _coerce_matrix(matrix).decisions:
        rows.extend(dict(item) for item in decision.required_missing)
    return tuple(rows)


def assert_no_derived_real_vwap_claim(
    *,
    execution_policy: str | None = None,
    available_fields: Sequence[str] = (),
    requested_claims: Sequence[str] = (),
    fail_on_error: bool = False,
) -> dict[str, Any]:
    """阻断 close proxy 或 amount/volume 派生真实 VWAP claim。"""

    requested = tuple(str(item) for item in requested_claims if str(item))
    requested_set = set(requested)
    fields = {str(item) for item in available_fields if str(item)}
    errors: list[dict[str, Any]] = []
    if (
        execution_policy == "close_proxy"
        and requested_set.intersection(CR014_REAL_VWAP_PRODUCTION_CLAIMS)
    ):
        errors.append(
            {
                "code": ERROR_CLOSE_PROXY_REAL_EXECUTION_CLAIM_ATTEMPT,
                "execution_policy": execution_policy,
                "claims": sorted(requested_set.intersection(CR014_REAL_VWAP_PRODUCTION_CLAIMS)),
            }
        )
    if requested_set.intersection(CR014_DENIED_REAL_VWAP_SUBSTITUTES):
        errors.append(
            {
                "code": ERROR_DERIVED_VWAP_CLAIM_ATTEMPT,
                "claims": sorted(requested_set.intersection(CR014_DENIED_REAL_VWAP_SUBSTITUTES)),
            }
        )
    if {"amount", "volume"}.issubset(fields) and requested_set.intersection(CR014_REAL_VWAP_PRODUCTION_CLAIMS):
        errors.append(
            {
                "code": ERROR_DERIVED_VWAP_CLAIM_ATTEMPT,
                "available_fields": sorted(fields.intersection({"amount", "volume"})),
                "claims": sorted(requested_set.intersection(CR014_REAL_VWAP_PRODUCTION_CLAIMS)),
            }
        )
    if errors and fail_on_error:
        raise ValueError(errors[0]["code"])
    return {
        "passed": not errors,
        "errors": errors,
        "derived_vwap_allowed_claim_count": 0,
        "real_vwap_allowed_claim_count": 0,
        "vwap_fill_allowed_claim_count": 0,
        "production_allowed_claim": False,
    }


def _decision(capability: str) -> UnsupportedCapabilityDecision:
    release_condition = (
        CR014_REAL_VWAP_RELEASE_CONDITIONS
        if capability in CR014_REAL_VWAP_CAPABILITIES
        else CR014_BASE_RELEASE_CONDITIONS
    )
    denied_substitutes = (
        tuple(sorted(CR014_DENIED_REAL_VWAP_SUBSTITUTES))
        if capability in CR014_REAL_VWAP_CAPABILITIES
        else ()
    )
    return UnsupportedCapabilityDecision(
        capability=capability,
        status=_CAPABILITY_STATUSES.get(capability, "unsupported"),
        production_allowed_claim=False,
        blocked_claims=_CAPABILITY_BLOCKED_CLAIMS[capability],
        required_missing=(
            {
                "dataset": "unsupported",
                "capability": capability,
                "gap_code": f"{capability}_required_missing",
                "evidence_path": f"unsupported://cr014-s08/{capability}",
                "remediation": "route_to_future_source_interface_story_cp5_user_authorization",
                "release_condition": list(release_condition),
                "production_allowed_claim": False,
            },
        ),
        release_condition=release_condition,
        denied_substitutes=denied_substitutes,
        evidence_refs=(
            "process/HLD-DATA-LAKE.md#17",
            "process/HLD.md#30",
            "process/ARCHITECTURE-DECISION.md#ADR-045",
            "process/ARCHITECTURE-DECISION.md#ADR-046",
            "process/ARCHITECTURE-DECISION.md#ADR-050",
            "process/ARCHITECTURE-DECISION.md#ADR-051",
        ),
    )


def _coerce_matrix(
    matrix: UnsupportedDecisionMatrix | Mapping[str, Any] | Sequence[Any] | None,
) -> UnsupportedDecisionMatrix:
    if matrix is None:
        return get_cr014_unsupported_decision_matrix()
    if isinstance(matrix, UnsupportedDecisionMatrix):
        return matrix
    if isinstance(matrix, Mapping):
        decisions = matrix.get("decisions", ())
        if not decisions:
            return get_cr014_unsupported_decision_matrix(str(matrix.get("as_of_trade_date") or ""))
        as_of_trade_date = str(matrix.get("as_of_trade_date") or "")
        counters = dict(matrix.get("permission_counters") or CR014_FORBIDDEN_OPERATION_COUNTERS)
    else:
        decisions = matrix
        as_of_trade_date = ""
        counters = dict(CR014_FORBIDDEN_OPERATION_COUNTERS)
    return UnsupportedDecisionMatrix(
        decisions=tuple(_coerce_decision(item) for item in decisions),
        as_of_trade_date=as_of_trade_date,
        permission_counters=counters,
    )


def _coerce_decision(value: Any) -> UnsupportedCapabilityDecision:
    if isinstance(value, UnsupportedCapabilityDecision):
        return value
    if not isinstance(value, Mapping):
        raise TypeError("unsupported decision must be a Mapping or UnsupportedCapabilityDecision")
    capability = str(value.get("capability") or "")
    if capability not in CR014_UNSUPPORTED_CAPABILITY_SET:
        raise ValueError(f"unsupported_capability_unknown: {capability}")
    return UnsupportedCapabilityDecision(
        capability=capability,
        status=str(value.get("status") or _CAPABILITY_STATUSES.get(capability, "unsupported")),
        production_allowed_claim=bool(value.get("production_allowed_claim")),
        blocked_claims=tuple(str(item) for item in value.get("blocked_claims") or _CAPABILITY_BLOCKED_CLAIMS[capability]),
        required_missing=tuple(dict(item) for item in value.get("required_missing") or ()),
        release_condition=tuple(str(item) for item in value.get("release_condition") or ()),
        denied_substitutes=tuple(str(item) for item in value.get("denied_substitutes") or ()),
        evidence_refs=tuple(str(item) for item in value.get("evidence_refs") or ()),
        reason_code=str(value.get("reason_code") or "cr014_s08_unsupported_capability"),
        severity=str(value.get("severity") or "P0"),
    )


__all__ = [
    "CAPABILITY_EXECUTION_DETAIL",
    "CAPABILITY_LEVEL2_ORDER_BOOK",
    "CAPABILITY_MICROSTRUCTURE_IMPACT_COST",
    "CAPABILITY_MINUTE_BAR",
    "CAPABILITY_ORDER_BOOK",
    "CAPABILITY_ORDER_MATCH_EXECUTION",
    "CAPABILITY_REAL_VWAP_EXECUTION",
    "CAPABILITY_TICK_TRADE",
    "CAPABILITY_VWAP_FILL_CLAIM",
    "CAPABILITY_W3_SOURCE_INTERFACE",
    "CR014_BASE_RELEASE_CONDITIONS",
    "CR014_DENIED_REAL_VWAP_SUBSTITUTES",
    "CR014_MICROSTRUCTURE_PRODUCTION_CLAIMS",
    "CR014_REAL_VWAP_CAPABILITIES",
    "CR014_REAL_VWAP_PRODUCTION_CLAIMS",
    "CR014_REAL_VWAP_RELEASE_CONDITIONS",
    "CR014_UNSUPPORTED_CAPABILITY_ORDER",
    "CR014_UNSUPPORTED_CAPABILITY_SET",
    "CR014_UNSUPPORTED_PRODUCTION_CLAIMS",
    "ERROR_CLOSE_PROXY_REAL_EXECUTION_CLAIM_ATTEMPT",
    "ERROR_DERIVED_VWAP_CLAIM_ATTEMPT",
    "ERROR_MISSING_RELEASE_CONDITION",
    "ReleaseConditionValidationResult",
    "UnsupportedCapabilityDecision",
    "UnsupportedDecisionMatrix",
    "assert_no_derived_real_vwap_claim",
    "blocked_claim_rows",
    "coerce_unsupported_decision_matrix",
    "get_cr014_unsupported_decision_matrix",
    "get_unsupported_decision",
    "required_missing_rows",
    "resolve_unsupported_capabilities",
    "validate_release_conditions_complete",
]
