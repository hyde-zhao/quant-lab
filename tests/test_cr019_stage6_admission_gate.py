from __future__ import annotations

from dataclasses import replace

from engine.stage6_admission import (
    AdmissionStatus,
    BlockedClaim,
    GateResult,
    GateStatus,
    Stage6GateId,
    build_stage6_gate_matrix,
    collect_admission_safety_counters,
    evaluate_stage6_admission,
    serialize_admission_package,
)
from trading.stage_gate import (
    AuthorizationSummary,
    Stage,
    StageEvidence,
    StageGateRequest,
    attach_admission_ref_to_stage_gate,
    evaluate_stage_gate,
    summarize_admission_blocked_reasons,
)


REQUIRED_ZERO_COUNTERS = {
    "qmt_api_call",
    "provider_fetch",
    "lake_write",
    "broker_lake_write",
    "publish",
    "simulation_or_live_run",
    "credential_read",
    "real_order_call",
    "real_cancel_call",
    "account_query_call",
    "account_write_call",
    "service_start",
    "dependency_change",
    "xtquant_import",
}


def _gate_evidence() -> dict[str, dict[str, str]]:
    return {
        gate.value: {
            "status": "pass",
            "evidence_ref": f"fixture:stage6:{gate.value}",
            "source_ref": f"experiments:49-66:{gate.value}",
        }
        for gate in Stage6GateId
    }


def _dry_run_refs(count: int = 5) -> tuple[str, ...]:
    return tuple(f"fixture:dry-run:2026-05-{20 + index}" for index in range(count))


def _complete_matrix() -> tuple[GateResult, ...]:
    return build_stage6_gate_matrix(
        "stage6-mf-49-66",
        _gate_evidence(),
        research_rerun_summary={
            "status": "pass",
            "evidence_ref": "reports/production_current_truth/run-fixture.md",
        },
        benchmark_evidence_ref="fixture:benchmark:primary",
        dry_run_evidence_refs=_dry_run_refs(),
        pre_sim_ref="fixture:pre-sim:stage6",
        stage_gate_ref="fixture:cr016-stage-gate",
    )


def _stage_gate_context() -> dict[str, str]:
    return {"stage_gate_ref": "process/checks/CP7-CR016-S04-fixture.md"}


def _admission_package(matrix: tuple[GateResult, ...] | None = None):
    return evaluate_stage6_admission(
        matrix or _complete_matrix(),
        old_strategy_evidence={},
        stage_gate_context=_stage_gate_context(),
        run_id="run-cr019-s01-fixture",
        strategy_id="stage6-mf-49-66",
        research_rerun_ref="reports/production_current_truth/run-fixture.md",
        benchmark_ref="fixture:benchmark:primary",
        dry_run_5day_ref="fixture:dry-run:5day",
        pre_sim_ref="fixture:pre-sim:stage6",
    )


def _assert_zero_counters(counters: object) -> None:
    current = dict(counters)  # type: ignore[arg-type]
    assert {key: current.get(key) for key in REQUIRED_ZERO_COUNTERS} == {
        key: 0 for key in REQUIRED_ZERO_COUNTERS
    }


def _authorization(target_stage: Stage = Stage.SIMULATION) -> AuthorizationSummary:
    return AuthorizationSummary(
        authorization_id="auth-cr019-stage-gate-fixture",
        mode=target_stage.value,
        strategy_id="stage6-mf-49-66",
        run_id="run-cr019-s01-fixture",
        target_stage=target_stage,
        target_trade_date="2026-05-29",
        capital_limit="100000",
        order_scope=("simulation_submit",),
        approver="fixture-approver",
        approved_at="2026-05-29T09:30:00+08:00",
        expires_at="2026-05-29T15:00:00+08:00",
        rollback_plan_ref="docs/QMT-SIMULATION-LIVE-RUNBOOK.md#rollback",
    )


def _cr016_evidence() -> StageEvidence:
    return StageEvidence(
        cr015_verified=True,
        runbook_ref="docs/QMT-SIMULATION-LIVE-RUNBOOK.md#simulation",
        cr017_consumer_boundary_ref="process/checks/CP7-CR017-S06-fixture.md",
        reconciliation_policy_ref="docs/QMT-TRADING-RUNBOOK.md#reconciliation",
        kill_switch_readiness_ref="docs/QMT-INCIDENT-PLAYBOOK.md#kill-switch",
        cr017_verified=True,
    )


def test_build_stage6_gate_matrix_covers_all_10_p0_gates() -> None:
    matrix = _complete_matrix()

    assert {gate.gate_id for gate in matrix} == set(Stage6GateId)
    assert len(matrix) == 10
    assert all(gate.status == GateStatus.PASS for gate in matrix)

    package = _admission_package(matrix)
    assert package.admission_status == AdmissionStatus.PASS
    assert package.blocked_claims == ()
    _assert_zero_counters(package.permission_counters)


def test_any_p0_gate_fail_blocks_admission() -> None:
    evidence = _gate_evidence()
    evidence[Stage6GateId.COST_MODEL.value] = {
        "status": "blocked",
        "evidence_ref": "fixture:cost-model:failed",
        "reason_code": "p0_gate_failed",
        "unlock_condition": "refresh_cost_model_slippage_and_fee_assumptions",
    }
    matrix = build_stage6_gate_matrix(
        "stage6-mf-49-66",
        evidence,
        benchmark_evidence_ref="fixture:benchmark:primary",
        dry_run_evidence_refs=_dry_run_refs(),
        pre_sim_ref="fixture:pre-sim:stage6",
    )
    package = _admission_package(matrix)

    assert package.admission_status == AdmissionStatus.BLOCKED
    assert any(
        claim.source_gate_id == Stage6GateId.COST_MODEL.value
        and claim.reason_code == "p0_gate_failed"
        for claim in package.blocked_claims
    )
    _assert_zero_counters(package.permission_counters)


def test_old_failed_strategy_never_becomes_simulation_ready() -> None:
    package = evaluate_stage6_admission(
        _complete_matrix(),
        old_strategy_evidence={
            "rerun_status": "failed",
            "requested_claims": ("simulation_ready",),
            "evidence_ref": "reports/production_current_truth/old-failed.md",
        },
        stage_gate_context=_stage_gate_context(),
        run_id="run-cr019-old-strategy-fixture",
        strategy_id="old-low-volatility-strategy",
        research_rerun_ref="reports/production_current_truth/old-failed.md",
        benchmark_ref="fixture:benchmark:primary",
        dry_run_5day_ref="fixture:dry-run:5day",
        pre_sim_ref="fixture:pre-sim:stage6",
    )
    serialized = serialize_admission_package(package)

    assert package.admission_status == AdmissionStatus.BLOCKED
    assert package.old_failed_strategy_simulation_ready_count == 0
    assert serialized["old_failed_strategy_simulation_ready_count"] == 0
    assert any(
        claim.claim_id == "simulation_ready"
        and claim.reason_code == "old_strategy_failed_rerun"
        for claim in package.blocked_claims
    )
    assert "old_strategy_failed_rerun" in summarize_admission_blocked_reasons(
        serialized
    )


def test_missing_five_consecutive_dry_run_evidence_blocks_package() -> None:
    matrix = build_stage6_gate_matrix(
        "stage6-mf-49-66",
        _gate_evidence(),
        benchmark_evidence_ref="fixture:benchmark:primary",
        dry_run_evidence_refs=_dry_run_refs(4),
        pre_sim_ref="fixture:pre-sim:stage6",
    )
    package = _admission_package(matrix)

    assert package.admission_status == AdmissionStatus.BLOCKED
    assert "dry_run_evidence_refs" in package.missing_evidence
    assert any(
        claim.reason_code == "dry_run_5day_missing"
        and claim.source_gate_id == Stage6GateId.PRESIM_AND_5DAY_DRY_RUN.value
        for claim in package.blocked_claims
    )


def test_missing_and_unknown_gate_ids_fail_closed() -> None:
    matrix = _complete_matrix()[1:] + (
        GateResult(
            gate_id="unknown_stage6_gate",
            status="pass",
            evidence_ref="fixture:unknown",
        ),
    )
    package = _admission_package(matrix)

    reason_codes = {claim.reason_code for claim in package.blocked_claims}
    assert package.admission_status == AdmissionStatus.BLOCKED
    assert {"missing_required_gate", "unknown_gate_id"} <= reason_codes
    assert Stage6GateId.DATA_QUALITY.value in package.missing_evidence


def test_stage_gate_ref_is_readonly_and_does_not_change_cr016_status() -> None:
    gate_result = evaluate_stage_gate(
        StageGateRequest(
            current_stage=Stage.SHADOW,
            target_stage=Stage.SIMULATION,
            authorization_summary=_authorization(),
            request_ref="fixture:cr019-stage-gate-readonly",
        ),
        _cr016_evidence(),
    )
    before_evidence_refs = dict(gate_result.evidence_refs)
    package = _admission_package()

    view = attach_admission_ref_to_stage_gate(
        gate_result,
        "reports/stage6_admission/package-schema-fixture.json",
        package.admission_status,
        summarize_admission_blocked_reasons(package),
    )

    assert gate_result.gate_status == "pass"
    assert gate_result.evidence_refs == before_evidence_refs
    assert view["gate_status"] == gate_result.gate_status
    assert view["stage6_admission"] == {
        "admission_package_ref": "reports/stage6_admission/package-schema-fixture.json",
        "admission_status": "pass",
        "blocked_reasons": (),
    }
    assert view["evidence_refs"]["stage6_admission_package_ref"].endswith(
        "package-schema-fixture.json"
    )


def test_forbidden_operation_counters_remain_zero_and_nonzero_blocks() -> None:
    counters = collect_admission_safety_counters()
    _assert_zero_counters(counters)

    package = _admission_package()
    _assert_zero_counters(package.permission_counters)

    blocked = evaluate_stage6_admission(
        _complete_matrix(),
        old_strategy_evidence={},
        stage_gate_context=_stage_gate_context(),
        permission_counters=collect_admission_safety_counters(
            {"qmt_api_call": 1}
        ),
    )
    assert blocked.admission_status == AdmissionStatus.BLOCKED
    assert any(
        claim.reason_code == "real_operation_forbidden"
        for claim in blocked.blocked_claims
    )


def test_stage_gate_helper_summarizes_claims_from_object_without_side_effects() -> None:
    package = replace(
        _admission_package(),
        blocked_claims=(
            BlockedClaim(
                claim_id="stage6_cost_model",
                reason_code="p0_gate_failed",
                evidence_ref="fixture:cost-model:failed",
                unlock_condition="refresh_cost_model",
            ),
            BlockedClaim(
                claim_id="stage6_cost_model_duplicate",
                reason_code="p0_gate_failed",
                evidence_ref="fixture:cost-model:failed",
                unlock_condition="refresh_cost_model",
            ),
        ),
    )

    assert summarize_admission_blocked_reasons(package) == ("p0_gate_failed",)
