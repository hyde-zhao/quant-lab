"""CR-169 的 strict C3+C4 Gate4 fixture compatibility adapter。

该模块只组合已经 self-validated 的 C3/C4 typed evidence，并调用公开
``validate_gate4_capacity_impact``。它不修改 canonical Gate4、不复用其私有
helper、不写 admission package，也不把 fixture PASS 提升为 aggregate/real claim。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Protocol

from engine.capacity_liquidity_evidence import (
    C3C4CorrelationHeaderV1,
    CapacityLiquidityAttachmentContext,
    CapacityLiquidityEvidenceV1,
    validate_c3_c4_correlation_headers,
    validate_capacity_liquidity_evidence,
)
from engine.cross_strategy_reliability_gates import (
    GATE_4_CAPACITY_IMPACT,
    ReliabilityGateStatus,
    ReliabilityGateSummary,
    normalize_forbidden_operation_counts,
    validate_gate4_capacity_impact,
)
from engine.economic_cost_evidence import (
    EconomicCostAttachmentContext,
    EconomicCostEvidenceV1,
    validate_economic_cost_evidence,
)
from engine.strategy_evidence import EvidenceAvailability, canonical_hash, canonical_json_value


GATE4_JOINT_PAYLOAD_KEYS = (
    "impact_model_family",
    "impact_model_ref",
    "cost_underestimation_status",
    "no_real_tca_claim",
    "adv_participation_ref",
    "capacity_dollars_ref",
    "liquidity_sizing_refs",
)
GATE4_RELEASE_PROFILE = "candidate-release"
GATE4_JOINT_PAYLOAD_HASH_DOMAIN = "quant-lab.capacity-liquidity-gate4-fixture-payload.v1"
_REASON_KEY_SUFFIXES = ("_na_reason", "_n_a_reason")
_GENERIC_REASON_KEYS = ("na_reason", "n_a_reason")


class Gate4Validator(Protocol):
    def __call__(
        self,
        evidence: Mapping[str, Any],
        *,
        release_profile: str = GATE4_RELEASE_PROFILE,
        operation_counts: Mapping[str, Any] | None = None,
    ) -> ReliabilityGateSummary: ...


@dataclass(frozen=True, slots=True)
class C3C4CorrelationContextV1:
    """两个显式 13-field views；不创建第三个 hash domain。"""

    c3_header: C3C4CorrelationHeaderV1
    c4_header: C3C4CorrelationHeaderV1


@dataclass(frozen=True, slots=True)
class Gate4FixtureCompatibilityOutcome:
    status: ReliabilityGateStatus | str
    reason_code: str
    canonical_invocations: int
    payload: Mapping[str, Any]
    payload_hash: str
    canonical_summary: ReliabilityGateSummary | None
    aggregate_admission_pass: bool = False
    capacity_scalable_claim: bool = False
    real_capacity_ready: bool = False
    stage3_entry_ready: bool = False

    @property
    def is_fixture_pass(self) -> bool:
        return (
            self.status is ReliabilityGateStatus.PASS
            and self.reason_code == "gate4_fixture_contract_pass"
            and not self.aggregate_admission_pass
            and not self.capacity_scalable_claim
            and not self.real_capacity_ready
            and not self.stage3_entry_ready
        )


def evaluate_c3_c4_gate4_fixture_compatibility(
    *,
    economic_cost: EconomicCostEvidenceV1,
    economic_cost_attachment: EconomicCostAttachmentContext,
    capacity_liquidity: CapacityLiquidityEvidenceV1,
    capacity_liquidity_attachment: CapacityLiquidityAttachmentContext,
    correlation_context: C3C4CorrelationContextV1,
    operation_counts: Mapping[str, Any] | None = None,
    gate4_validator: Gate4Validator = validate_gate4_capacity_impact,
) -> Gate4FixtureCompatibilityOutcome:
    """执行 typed precheck→13-field join→exact payload→public call→postcondition。"""

    counts = normalize_forbidden_operation_counts(operation_counts)
    if any(value != 0 for value in counts.values()):
        return _blocked("external_operation_forbidden")
    if not isinstance(economic_cost, EconomicCostEvidenceV1):
        return _blocked("economic_cost_evidence_unavailable")
    if not isinstance(capacity_liquidity, CapacityLiquidityEvidenceV1):
        return _blocked("capacity_liquidity_evidence_unavailable")
    if not isinstance(economic_cost_attachment, EconomicCostAttachmentContext) or not isinstance(
        capacity_liquidity_attachment, CapacityLiquidityAttachmentContext
    ):
        return _blocked("c4_c3_c4_correlation_header_mismatch")
    if not isinstance(correlation_context, C3C4CorrelationContextV1):
        return _blocked("c4_c3_c4_correlation_header_mismatch")

    c3_validation = validate_economic_cost_evidence(economic_cost)
    c4_validation = validate_capacity_liquidity_evidence(capacity_liquidity)
    if c3_validation.availability is not EvidenceAvailability.PRESENT:
        return _blocked("c4_component_or_envelope_hash_tampered")
    if c4_validation.availability is not EvidenceAvailability.PRESENT:
        reason = "c4_gate4_ref_not_typed_present" if any(
            issue.code == "c4_gate4_ref_not_typed_present" for issue in c4_validation.issues
        ) else "c4_component_or_envelope_hash_tampered"
        return _blocked(reason)

    c3_header = correlation_context.c3_header
    c4_header = correlation_context.c4_header
    if not _attachment_matches_header(economic_cost_attachment, c3_header):
        return _blocked("c4_c3_c4_correlation_header_mismatch")
    if not _attachment_matches_header(capacity_liquidity_attachment, c4_header):
        return _blocked("c4_c3_c4_correlation_header_mismatch")
    header_validation = validate_c3_c4_correlation_headers(c3_header, c4_header)
    if not header_validation.passed or not _c4_payload_basis_matches_header(capacity_liquidity, c4_header):
        return _blocked("c4_c3_c4_correlation_header_mismatch")

    payload = _build_joint_payload(economic_cost, capacity_liquidity)
    if _payload_has_reason_or_extra_escape(payload):
        return _rejected("c4_projection_reason_escape_or_postcondition_violation")
    validator = gate4_validator
    summary = validator(payload, release_profile=GATE4_RELEASE_PROFILE, operation_counts=counts)
    return _postcondition(payload, summary)


def _build_joint_payload(
    economic_cost: EconomicCostEvidenceV1,
    capacity_liquidity: CapacityLiquidityEvidenceV1,
) -> dict[str, Any]:
    return {
        "impact_model_family": economic_cost.impact_model_family,
        "impact_model_ref": economic_cost.impact_model_ref,
        "cost_underestimation_status": economic_cost.cost_underestimation_status,
        "no_real_tca_claim": economic_cost.no_real_tca_claim,
        "adv_participation_ref": capacity_liquidity.adv_participation_ref,
        "capacity_dollars_ref": capacity_liquidity.capacity_dollars_ref,
        "liquidity_sizing_refs": list(capacity_liquidity.liquidity_sizing_refs),
    }


def _payload_has_reason_or_extra_escape(payload: Mapping[str, Any]) -> bool:
    """本地 denylist；测试通过此私有 seam 覆盖 reason/extra mapping。"""

    keys = tuple(payload)
    if keys != GATE4_JOINT_PAYLOAD_KEYS or len(keys) != 7:
        return True
    for key in keys:
        lowered = key.lower()
        if lowered in _GENERIC_REASON_KEYS or lowered.endswith(_REASON_KEY_SUFFIXES):
            return True
    return any(payload.get(key) in (None, "", (), []) for key in GATE4_JOINT_PAYLOAD_KEYS)


def _postcondition(
    payload: Mapping[str, Any],
    summary: ReliabilityGateSummary,
) -> Gate4FixtureCompatibilityOutcome:
    payload_hash = canonical_hash(
        canonical_json_value(payload),
        domain=GATE4_JOINT_PAYLOAD_HASH_DOMAIN,
    )
    if not isinstance(summary, ReliabilityGateSummary):
        return _rejected("gate4_fixture_postcondition_violation", payload, payload_hash)
    status = _status_value(summary.status)
    if status is ReliabilityGateStatus.PASS:
        valid_pass = (
            summary.gate_id == GATE_4_CAPACITY_IMPACT
            and not summary.blocked_claims
            and all(value == 0 for value in summary.operation_counts.values())
            and not _payload_has_reason_or_extra_escape(payload)
        )
        if not valid_pass:
            return _rejected("gate4_fixture_postcondition_violation", payload, payload_hash, summary)
        return Gate4FixtureCompatibilityOutcome(
            status=ReliabilityGateStatus.PASS,
            reason_code="gate4_fixture_contract_pass",
            canonical_invocations=1,
            payload=dict(payload),
            payload_hash=payload_hash,
            canonical_summary=summary,
        )
    if status in {
        ReliabilityGateStatus.BLOCKED,
        ReliabilityGateStatus.NEEDS_REVIEW,
        ReliabilityGateStatus.FAIL,
    }:
        return Gate4FixtureCompatibilityOutcome(
            status=status,
            reason_code=_canonical_reason(summary),
            canonical_invocations=1,
            payload=dict(payload),
            payload_hash=payload_hash,
            canonical_summary=summary,
        )
    return _rejected("gate4_fixture_postcondition_violation", payload, payload_hash, summary)


def _attachment_matches_header(
    attachment: EconomicCostAttachmentContext | CapacityLiquidityAttachmentContext,
    header: C3C4CorrelationHeaderV1,
) -> bool:
    return all(
        getattr(attachment, field_name) == getattr(header, field_name)
        for field_name in ("manifest_ref", "run_ref", "strategy_ref", "package_ref")
    )


def _c4_payload_basis_matches_header(
    evidence: CapacityLiquidityEvidenceV1,
    header: C3C4CorrelationHeaderV1,
) -> bool:
    if len(evidence.ref_payloads) != 3:
        return False
    expected = {
        "price_basis": header.price_basis,
        "notional_basis": header.notional_basis,
        "currency": header.currency,
        "calendar": header.calendar,
        "as_of": header.as_of,
        "horizon_start": header.horizon_start,
        "horizon_end": header.horizon_end,
    }
    return all(all(payload.basis.get(key) == value for key, value in expected.items()) for payload in evidence.ref_payloads)


def _status_value(value: ReliabilityGateStatus | str) -> ReliabilityGateStatus | None:
    try:
        return ReliabilityGateStatus(str(getattr(value, "value", value)).upper())
    except ValueError:
        return None


def _canonical_reason(summary: ReliabilityGateSummary) -> str:
    reason = summary.release_blocking_reason
    if reason is not None and reason.reason_id:
        return reason.reason_id
    if summary.blocked_claims:
        return summary.blocked_claims[0].claim_id
    return "gate4_canonical_non_pass"


def _blocked(reason_code: str) -> Gate4FixtureCompatibilityOutcome:
    return Gate4FixtureCompatibilityOutcome(
        status=ReliabilityGateStatus.BLOCKED,
        reason_code=reason_code,
        canonical_invocations=0,
        payload={},
        payload_hash="",
        canonical_summary=None,
    )


def _rejected(
    reason_code: str,
    payload: Mapping[str, Any] | None = None,
    payload_hash: str = "",
    summary: ReliabilityGateSummary | None = None,
) -> Gate4FixtureCompatibilityOutcome:
    return Gate4FixtureCompatibilityOutcome(
        status="REJECTED",
        reason_code=reason_code,
        canonical_invocations=0 if summary is None else 1,
        payload=dict(payload or {}),
        payload_hash=payload_hash,
        canonical_summary=summary,
    )


__all__ = [
    "C3C4CorrelationContextV1",
    "GATE4_JOINT_PAYLOAD_HASH_DOMAIN",
    "GATE4_JOINT_PAYLOAD_KEYS",
    "GATE4_RELEASE_PROFILE",
    "Gate4FixtureCompatibilityOutcome",
    "Gate4Validator",
    "evaluate_c3_c4_gate4_fixture_compatibility",
]
