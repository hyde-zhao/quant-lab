"""CR-168 C3 到 Gate4 的局部安全 projection。

Gate4 是 C3+C4 联合门禁。CR-168 只拥有 fixture/static C3 evidence，C4 必须以
``typed_unavailable`` 表达。canonical Gate4 允许 C4 ref 缺失时带 N/A reason，
因此本 adapter 在调用前拒绝该 reason escape，在调用后只接受确定的三项 C4
missing claims。它不是 aggregate orchestration，也不会修改 canonical Gate4。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Mapping

from engine.cross_strategy_reliability_gates import (
    ReliabilityGateStatus,
    ReliabilityGateSummary,
    normalize_forbidden_operation_counts,
    validate_gate4_capacity_impact,
)
from engine.economic_cost_evidence import EconomicCostEvidenceV1
from engine.strategy_evidence import EvidenceAvailability


GATE4_C3_ALLOWLIST = (
    "impact_model_family",
    "impact_model_ref",
    "cost_underestimation_status",
    "no_real_tca_claim",
)
GATE4_C4_REASON_DENYLIST = (
    "adv_participation_ref_na_reason",
    "adv_participation_ref_n_a_reason",
    "capacity_dollars_ref_na_reason",
    "capacity_dollars_ref_n_a_reason",
    "liquidity_sizing_refs_na_reason",
    "liquidity_sizing_refs_n_a_reason",
    "na_reason",
    "n_a_reason",
)
GATE4_C4_REF_KEYS = (
    "adv_participation_ref",
    "capacity_dollars_ref",
    "liquidity_sizing_refs",
)
GATE4_EXPECTED_C4_MISSING_CLAIMS = (
    "adv_participation_missing",
    "capacity_dollars_missing",
    "liquidity_sizing_missing",
)
GATE4_RELEASE_PROFILE = "candidate-release"

Gate4Validator = Callable[..., ReliabilityGateSummary]


@dataclass(frozen=True, slots=True)
class C3Gate4ProjectionOutcome:
    """adapter 的唯一输出；任何路径均不把 Gate4 PASS 暴露给调用方。"""

    status: ReliabilityGateStatus
    reason_code: str
    canonical_invoked: bool
    payload: Mapping[str, Any]
    canonical_summary: ReliabilityGateSummary | None = None

    @property
    def is_pass(self) -> bool:
        """安全不变量：CR-168 C3-only projection 永远不产生 PASS。"""

        return False


def project_economic_cost_to_gate4(
    evidence: EconomicCostEvidenceV1 | None,
    c4_availability: EvidenceAvailability | str | Mapping[str, Any],
    operation_counts: Mapping[str, Any] | None,
    *,
    gate4_validator: Gate4Validator | None = None,
) -> C3Gate4ProjectionOutcome:
    """投影 present C3，并在 C4 unavailable 时安全调用 public Gate4 validator。

    ``gate4_validator`` 仅用于窄依赖注入：生产路径保持 ``None``，测试可传入只
    返回 public :class:`ReliabilityGateSummary` 的 fake。不得 monkeypatch canonical
    module，亦不得依赖其 private helper。
    """

    normalized_counts = normalize_forbidden_operation_counts(operation_counts)
    if any(value != 0 for value in normalized_counts.values()):
        return _blocked("external_operation_forbidden")

    if not isinstance(evidence, EconomicCostEvidenceV1) or evidence.availability is not EvidenceAvailability.PRESENT:
        return _blocked("economic_cost_evidence_unavailable")

    marker, marker_mapping = _c4_marker(c4_availability)
    if any(key in marker_mapping for key in GATE4_C4_REASON_DENYLIST):
        return _blocked("gate4_reason_escape_rejected")
    if marker is EvidenceAvailability.PRESENT or any(key in marker_mapping for key in GATE4_C4_REF_KEYS):
        return _rejected("c4_present_out_of_scope")
    if marker is not EvidenceAvailability.TYPED_UNAVAILABLE:
        return _blocked("c4_availability_not_typed_unavailable")

    payload = _build_gate4_payload(evidence)
    validator = validate_gate4_capacity_impact if gate4_validator is None else gate4_validator
    canonical_summary = validator(
        payload,
        release_profile=GATE4_RELEASE_PROFILE,
        operation_counts=normalized_counts,
    )
    return _postcondition(payload, canonical_summary)


def _build_gate4_payload(evidence: EconomicCostEvidenceV1) -> dict[str, Any]:
    """以精确四键重建 payload，绝不透传任意调用方 mapping。"""

    return {
        "impact_model_family": evidence.impact_model_family,
        "impact_model_ref": evidence.impact_model_ref,
        "cost_underestimation_status": evidence.cost_underestimation_status,
        "no_real_tca_claim": evidence.no_real_tca_claim,
    }


def _postcondition(
    payload: Mapping[str, Any],
    canonical_summary: ReliabilityGateSummary,
) -> C3Gate4ProjectionOutcome:
    """只接受 clean C3 + C4 safe-absent 的预期 BLOCKED 结果。"""

    if not isinstance(canonical_summary, ReliabilityGateSummary):
        return _blocked("gate4_postcondition_violation", payload, canonical_summary=None)

    status = _status_value(canonical_summary.status)
    if status is ReliabilityGateStatus.PASS:
        return _blocked("gate4_unexpected_pass", payload, canonical_summary)

    claim_ids = tuple(_claim_id(item) for item in canonical_summary.blocked_claims)
    if status is not ReliabilityGateStatus.BLOCKED or claim_ids != GATE4_EXPECTED_C4_MISSING_CLAIMS:
        return _blocked("gate4_postcondition_violation", payload, canonical_summary)

    return C3Gate4ProjectionOutcome(
        status=ReliabilityGateStatus.BLOCKED,
        reason_code="gate4_c4_typed_unavailable",
        canonical_invoked=True,
        payload=dict(payload),
        canonical_summary=canonical_summary,
    )


def _c4_marker(
    c4_availability: EvidenceAvailability | str | Mapping[str, Any],
) -> tuple[EvidenceAvailability | None, Mapping[str, Any]]:
    if isinstance(c4_availability, Mapping):
        mapping = dict(c4_availability)
        raw_marker = mapping.get("availability")
    else:
        mapping = {}
        raw_marker = c4_availability
    try:
        return EvidenceAvailability(str(getattr(raw_marker, "value", raw_marker))), mapping
    except ValueError:
        return None, mapping


def _status_value(value: ReliabilityGateStatus | str) -> ReliabilityGateStatus | None:
    try:
        return ReliabilityGateStatus(str(getattr(value, "value", value)).upper())
    except ValueError:
        return None


def _claim_id(item: Any) -> str:
    if isinstance(item, Mapping):
        return str(item.get("claim_id") or "")
    return str(getattr(item, "claim_id", ""))


def _blocked(
    reason_code: str,
    payload: Mapping[str, Any] | None = None,
    canonical_summary: ReliabilityGateSummary | None = None,
) -> C3Gate4ProjectionOutcome:
    return C3Gate4ProjectionOutcome(
        status=ReliabilityGateStatus.BLOCKED,
        reason_code=reason_code,
        canonical_invoked=canonical_summary is not None,
        payload=dict(payload or {}),
        canonical_summary=canonical_summary,
    )


def _rejected(reason_code: str) -> C3Gate4ProjectionOutcome:
    return C3Gate4ProjectionOutcome(
        status=ReliabilityGateStatus.BLOCKED,
        reason_code=reason_code,
        canonical_invoked=False,
        payload={},
        canonical_summary=None,
    )


__all__ = [
    "C3Gate4ProjectionOutcome",
    "GATE4_C3_ALLOWLIST",
    "GATE4_C4_REASON_DENYLIST",
    "GATE4_C4_REF_KEYS",
    "GATE4_EXPECTED_C4_MISSING_CLAIMS",
    "GATE4_RELEASE_PROFILE",
    "project_economic_cost_to_gate4",
]
