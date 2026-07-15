from __future__ import annotations

from dataclasses import fields
import inspect
import json
from pathlib import Path

from engine.capacity_liquidity_evidence import (
    C3C4CorrelationHeaderV1,
    CapacityLiquidityEvidenceInput,
    build_capacity_liquidity_evidence,
)
from engine.capacity_liquidity_gate4_projection import (
    C3C4CorrelationContextV1,
    GATE4_JOINT_PAYLOAD_KEYS,
    evaluate_c3_c4_gate4_fixture_compatibility,
)
from engine.cross_strategy_reliability_gates import (
    AdmissionGateMode,
    AdmissionPolicyResult,
    ArtifactRef,
    GATE_IDS,
    GATE_1_STATISTICAL,
    GATE_2_CV,
    GATE_3_PIT_UNIVERSE,
    GATE_4_CAPACITY_IMPACT,
    GATE_5_REGIME_ATTRIBUTION_RECONCILIATION,
    GATE_6_ADMISSION_POLICY,
    ReliabilityGateStatus,
    ReliabilityGateSummary,
    build_shared_gate_summary,
    evaluate_gate1_statistical_reliability,
    resolve_admission_policy,
    validate_gate2_cv_governance,
    validate_gate3_pit_universe,
    validate_gate4_capacity_impact,
    validate_gate5_slots,
)
from engine.economic_cost_evidence import EconomicCostEvidenceInput, build_economic_cost_evidence
from engine.economic_cost_gate4_projection import (
    GATE4_EXPECTED_C4_MISSING_CLAIMS,
    project_economic_cost_to_gate4,
)
from engine.strategy_evidence import EvidenceAvailability


def _c3_result():
    return build_economic_cost_evidence(
        EconomicCostEvidenceInput(
            manifest_ref="fixture://manifest/cr170",
            run_ref="fixture://run/cr170",
            strategy_ref="fixture://strategy/cr170",
            package_ref="fixture://package/cr170",
            gross_pnl="100",
            performance_notional="1000",
            traded_notional="500",
            sell_notional="250",
            turnover="0.5",
            cost_model_version="fixture-cost-v1",
            fee_rate="0.001",
            fee_fixed_amount="0",
            tax_rate="0.0005",
            tax_fixed_amount="0",
            effective_spread_rate="0.0002",
            effective_slippage_rate="0.0003",
            impact_model_family="square_root",
            impact_model_version="square-root-v1",
            impact_model_ref="fixture://impact/square-root-v1",
            impact_coefficient="0.01",
            static_reference_notional="10000",
            currency="CNY",
            currency_minor_unit="0.01",
            calendar="CN-TRADING-DAY",
            price_basis="adjusted_close",
            notional_basis="market_value",
            lineage_refs=("fixture://lineage/c3",),
            provenance_refs=("fixture://provenance/c3",),
            authorization_refs=("fixture://authorization/static-only",),
            limitations=("fixture_static_only",),
            cost_underestimation_status="PASS",
            no_real_tca_claim=True,
        )
    )


def _c4_result():
    return build_capacity_liquidity_evidence(
        CapacityLiquidityEvidenceInput(
            manifest_ref="fixture://manifest/cr170",
            run_ref="fixture://run/cr170",
            strategy_ref="fixture://strategy/cr170",
            package_ref="fixture://package/cr170",
            price_basis="adjusted_close",
            notional_basis="market_value",
            currency="CNY",
            calendar="CN-TRADING-DAY",
            as_of="2026-07-10",
            horizon_start="2026-01-01",
            horizon_end="2026-06-30",
            lineage_context_ref="fixture://context/lineage/shared",
            authorization_context_ref="fixture://context/authorization/static-only",
            synthetic_adv="1000000",
            requested_notional="50000",
            turnover_notional="250000",
            participation_cap="0.10",
            currency_minor_unit="0.01",
            method="static_adv_cap_v1",
            model_version="fixture-static-adv-cap-v1",
            lineage_refs=("fixture://lineage/c4",),
            provenance_refs=("fixture://provenance/c4",),
            authorization_refs=("fixture://authorization/static-only",),
            limitations=("fixture_static_only",),
        )
    )


def test_public_gate_and_admission_surface_is_compatible() -> None:
    expected_params = {
        build_shared_gate_summary: ("gate_id", "artifact_refs", "blocked_claims", "release_blocking_reason", "operation_counts", "evidence_completeness", "limitations"),
        evaluate_gate1_statistical_reliability: ("artifacts", "strategy_class", "release_profile", "claim_types", "gate3_summary", "gate4_summary", "operation_counts", "family_lineage_projection"),
        validate_gate2_cv_governance: ("evidence", "strategy_class", "release_profile", "operation_counts"),
        validate_gate3_pit_universe: ("evidence", "release_profile", "operation_counts"),
        validate_gate4_capacity_impact: ("evidence", "release_profile", "operation_counts"),
        validate_gate5_slots: ("evidence", "release_profile", "operation_counts"),
        resolve_admission_policy: ("strategy_class", "release_profile", "gate_summaries", "requested_claims", "operation_counts"),
    }
    for callable_, names in expected_params.items():
        assert tuple(inspect.signature(callable_).parameters) == names

    assert GATE_IDS == (
        GATE_1_STATISTICAL,
        GATE_2_CV,
        GATE_3_PIT_UNIVERSE,
        GATE_4_CAPACITY_IMPACT,
        GATE_5_REGIME_ATTRIBUTION_RECONCILIATION,
        GATE_6_ADMISSION_POLICY,
    )
    assert {item.value for item in ReliabilityGateStatus} == {"PASS", "FAIL", "NEEDS_REVIEW", "BLOCKED"}
    assert {item.value for item in AdmissionGateMode} == {"opt-in", "default-required", "release-blocking", "not-authorized"}
    assert tuple(field.name for field in fields(ReliabilityGateSummary)) == (
        "gate_id", "status", "artifact_refs", "blocked_claims", "release_blocking_reason", "evidence_completeness", "operation_counts", "limitations", "family_lineage_projection", "evidence_identity", "schema_version"
    )
    assert tuple(field.name for field in fields(AdmissionPolicyResult)) == (
        "tier", "gate_mode", "status", "release_wording", "blocked_claims", "release_blocking_reason", "fallback_reason", "source_rule_id", "readiness_disclaimers", "schema_version"
    )


def test_cr168_c3_only_adapter_still_contains_c4_unavailable_and_reason_escape() -> None:
    c3 = _c3_result()
    assert c3.evidence is not None
    unavailable = {"availability": EvidenceAvailability.TYPED_UNAVAILABLE.value}
    outcome = project_economic_cost_to_gate4(c3.evidence, unavailable, {})
    assert outcome.status is ReliabilityGateStatus.BLOCKED
    assert outcome.reason_code == "gate4_c4_typed_unavailable"
    assert outcome.canonical_summary is not None
    assert tuple(claim.claim_id for claim in outcome.canonical_summary.blocked_claims) == GATE4_EXPECTED_C4_MISSING_CLAIMS

    escape = project_economic_cost_to_gate4(
        c3.evidence,
        {**unavailable, "na_reason": "C4 not built"},
        {},
    )
    assert escape.status is ReliabilityGateStatus.BLOCKED
    assert escape.reason_code == "gate4_reason_escape_rejected"
    assert escape.canonical_invoked is False


def test_cr169_strict_joint_adapter_still_passes_only_bounded_fixture_contract() -> None:
    c3 = _c3_result()
    c4 = _c4_result()
    assert c3.evidence is not None and c4.evidence is not None
    c3_header = C3C4CorrelationHeaderV1(**c4.header.to_dict())
    outcome = evaluate_c3_c4_gate4_fixture_compatibility(
        economic_cost=c3.evidence,
        economic_cost_attachment=c3.attachment_context,
        capacity_liquidity=c4.evidence,
        capacity_liquidity_attachment=c4.attachment_context,
        correlation_context=C3C4CorrelationContextV1(c3_header=c3_header, c4_header=c4.header),
        operation_counts={},
    )
    assert tuple(outcome.payload) == GATE4_JOINT_PAYLOAD_KEYS
    assert outcome.status is ReliabilityGateStatus.PASS
    assert outcome.reason_code == "gate4_fixture_contract_pass"
    assert outcome.aggregate_admission_pass is False
    assert outcome.capacity_scalable_claim is False
    assert outcome.real_capacity_ready is False
    assert outcome.stage3_entry_ready is False


def test_public_evidence_to_gate_merge_to_t1_admission_is_fail_closed() -> None:
    boundary = {
        "reason": "fixture PIT evidence is explicitly unavailable",
        "owner": GATE_3_PIT_UNIVERSE,
        "scope": "G3-P01",
        "release_profile": "candidate-release",
        "authorization_ref": "",
    }
    local_gate = validate_gate3_pit_universe(
        {
            "n_a_boundaries": {"G3-P01": boundary},
            "cr153_slot_lifecycle": "delegated_to_cr154",
        },
        release_profile="candidate-release",
    )
    assert local_gate.status is ReliabilityGateStatus.NEEDS_REVIEW

    merged = build_shared_gate_summary(
        gate_id=GATE_3_PIT_UNIVERSE,
        artifact_refs=local_gate.artifact_refs,
        blocked_claims=local_gate.blocked_claims,
    )
    assert merged.status is ReliabilityGateStatus.NEEDS_REVIEW
    summaries = tuple(
        merged
        if gate_id == GATE_3_PIT_UNIVERSE
        else build_shared_gate_summary(
            gate_id=gate_id,
            artifact_refs=(ArtifactRef("contract_ref", f"fixture://cr170/{gate_id}", owner_gate=gate_id),),
        )
        for gate_id in GATE_IDS[:5]
    )
    admission = resolve_admission_policy(
        strategy_class="ml",
        release_profile="candidate-release",
        gate_summaries=summaries,
    )
    assert admission.status is ReliabilityGateStatus.BLOCKED
    assert admission.source_rule_id == "cr170-t1-mandatory-needs-review-blocked"


def test_claim_ceiling_cr155_and_current_runner_boundaries_remain_closed() -> None:
    cr155 = json.loads(Path("process/changes/summaries/CR-155.summary.json").read_text(encoding="utf-8"))
    assert cr155["admission_package_status"] == "BLOCKED"
    assert cr155["paper_candidate"] is False

    cr170 = Path("process/changes/CR-170.md").read_text(encoding="utf-8")
    for exact_claim in (
        "stage3_started: false",
        "stage3_entry_ready: false",
        "current_stage3_runner_integrated: false",
        "aggregate_orchestration_implemented: false",
        "cr155_promoted: false",
        "real_evidence_available: false",
        "runtime_ready: false",
    ):
        assert exact_claim in cr170

    for path in (
        Path("engine/mature_multifactor_research.py"),
        Path("engine/mature_multifactor_framework.py"),
    ):
        source = path.read_text(encoding="utf-8")
        assert "resolve_admission_policy" not in source
        assert "validate_gate1" not in source
        assert "validate_gate2" not in source
        assert "validate_gate3" not in source
        assert "validate_gate4" not in source
        assert "validate_gate5" not in source

    aggregate_source = Path("engine/strategy_admission_package.py").read_text(encoding="utf-8")
    assert "reliability_na_policy" not in aggregate_source
    assert "CR-170" not in aggregate_source


def test_adapter_guards_and_future_verifier_disclosure_are_still_present() -> None:
    cr168_source = Path("engine/economic_cost_gate4_projection.py").read_text(encoding="utf-8")
    cr169_source = Path("engine/capacity_liquidity_gate4_projection.py").read_text(encoding="utf-8")
    assert "GATE4_C4_REASON_DENYLIST" in cr168_source
    assert "gate4_postcondition_violation" in cr168_source
    assert "_payload_has_reason_or_extra_escape" in cr169_source
    assert "gate4_fixture_postcondition_violation" in cr169_source

    verifier_contract = Path(
        "process/archive/design-cr-docs/HLD-CANONICAL-RELIABILITY-NA-SEMANTICS-ADMISSION.md"
    ).read_text(encoding="utf-8")
    cp5_contract = Path("process/checkpoints/CP5-CR170-ALL-STORIES-LLD-BATCH.md").read_text(
        encoding="utf-8"
    )
    assert "R-CR170-VERIFIER-INDEPENDENCE" in verifier_contract
    assert "FU-CR161-006" in verifier_contract
    assert "CP8 必须显式披露" in cp5_contract
