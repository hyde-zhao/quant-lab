from __future__ import annotations

from dataclasses import replace

import pytest

from trading.qmt_adapter import (
    AdapterBlockedReason,
    AdapterResultStatus,
    precheck_stage_gate_result,
)
from trading.qmt_environment import AdapterMode
from trading.stage_gate import (
    AuthorizationSummary,
    REQUIRED_AUTHORIZATION_FIELDS,
    Stage,
    StageEvidence,
    StageGateBlockedReason,
    StageGateRequest,
    evaluate_stage_gate,
    simulation_order_enable,
    validate_authorization_summary,
)


REQUIRED_ZERO_COUNTERS = {
    "qmt_api_call",
    "real_order_call",
    "real_cancel_call",
    "account_query_call",
    "account_write_call",
    "credential_read",
    "real_broker_lake_write",
    "real_lake_write",
    "provider_fetch",
    "publish",
    "dependency_change",
    "simulation_run",
    "live_activation",
    "adapter_call_on_block",
    "scale_up_allowed_without_cr017",
    "adapter_calls",
}


def _authorization(target_stage: Stage = Stage.SIMULATION) -> AuthorizationSummary:
    return AuthorizationSummary(
        authorization_id="auth-cr016-s01-fixture",
        mode=target_stage.value,
        strategy_id="strategy-alpha",
        run_id="run-cr016-s01-fixture",
        target_stage=target_stage,
        target_trade_date="2026-05-29",
        capital_limit="100000",
        order_scope=("order_intent_submit",),
        approver="fixture-approver",
        approved_at="2026-05-28T09:30:00+08:00",
        expires_at="2026-05-28T15:00:00+08:00",
        rollback_plan_ref="runbook:rollback:simulation",
    )


def _evidence(*, cr015_verified: bool = True, cr017_verified: bool = True) -> StageEvidence:
    return StageEvidence(
        cr015_verified=cr015_verified,
        runbook_ref="docs/QMT-TRADING-RUNBOOK.md#5.3",
        cr017_consumer_boundary_ref=(
            "process/checks/"
            "CP7-CR017-S06-research-qmt-consumer-docs-and-migration-guide-"
            "VERIFICATION-DONE.md"
        ),
        reconciliation_policy_ref="runbook:reconciliation:simulation",
        kill_switch_readiness_ref="runbook:kill-switch:simulation",
        cr017_verified=cr017_verified,
    )


def _request(
    current_stage: Stage = Stage.SHADOW,
    target_stage: Stage = Stage.SIMULATION,
    authorization: AuthorizationSummary | None = None,
) -> StageGateRequest:
    return StageGateRequest(
        current_stage=current_stage,
        target_stage=target_stage,
        authorization_summary=authorization or _authorization(target_stage),
        request_ref="fixture:cr016-s01",
    )


def _assert_zero_counters(counters: object) -> None:
    current = dict(counters)  # type: ignore[arg-type]
    assert {key: current.get(key) for key in REQUIRED_ZERO_COUNTERS} == {
        key: 0 for key in REQUIRED_ZERO_COUNTERS
    }


def test_shadow_to_simulation_gate_passes_with_required_evidence_and_authorization() -> None:
    result = evaluate_stage_gate(_request(), _evidence(cr017_verified=False))

    assert result.gate_status == "pass"
    assert result.current_stage is Stage.SHADOW
    assert result.target_stage is Stage.SIMULATION
    assert result.blocked_reason is None
    assert result.missing_fields == ()
    assert result.authorization_id == "auth-cr016-s01-fixture"
    _assert_zero_counters(result.safety_counters)

    enable_result = simulation_order_enable(result, AdapterMode.SIMULATION)
    assert enable_result.enabled is True
    assert enable_result.gate_status == "pass"
    assert enable_result.adapter_mode == "simulation"
    _assert_zero_counters(enable_result.safety_counters)


def test_stage_skip_is_blocked_with_stable_reason_and_zero_counters() -> None:
    result = evaluate_stage_gate(
        _request(Stage.SHADOW, Stage.SMALL_LIVE, _authorization(Stage.SMALL_LIVE)),
        _evidence(),
    )

    assert result.gate_status == "blocked"
    assert result.blocked_reason is StageGateBlockedReason.STAGE_SKIP_BLOCKED
    assert result.missing_fields == ()
    _assert_zero_counters(result.safety_counters)


def test_missing_authorization_fields_block_simulation_gate() -> None:
    authorization = replace(_authorization(), approver="", expires_at="")
    result = evaluate_stage_gate(
        _request(authorization=authorization),
        _evidence(),
    )

    assert result.gate_status == "blocked"
    assert result.blocked_reason is (
        StageGateBlockedReason.AUTHORIZATION_REQUIRED_MISSING
    )
    assert {"approver", "expires_at"} <= set(result.missing_fields)
    assert set(validate_authorization_summary(None, Stage.SIMULATION)) == set(
        REQUIRED_AUTHORIZATION_FIELDS
    )
    _assert_zero_counters(result.safety_counters)


def test_cr015_not_verified_blocks_simulation_gate() -> None:
    result = evaluate_stage_gate(_request(), _evidence(cr015_verified=False))

    assert result.gate_status == "blocked"
    assert result.blocked_reason is StageGateBlockedReason.CR015_NOT_VERIFIED
    assert result.missing_fields == ("cr015_verified",)
    _assert_zero_counters(result.safety_counters)


@pytest.mark.parametrize(
    ("field_name", "reason"),
    [
        ("runbook_ref", StageGateBlockedReason.RUNBOOK_REQUIRED_MISSING),
        (
            "cr017_consumer_boundary_ref",
            StageGateBlockedReason.CR017_CONSUMER_BOUNDARY_REQUIRED_MISSING,
        ),
        (
            "reconciliation_policy_ref",
            StageGateBlockedReason.RECONCILIATION_POLICY_MISSING,
        ),
        (
            "kill_switch_readiness_ref",
            StageGateBlockedReason.KILL_SWITCH_READINESS_MISSING,
        ),
    ],
)
def test_missing_runbook_reconciliation_or_kill_switch_blocks_gate(
    field_name: str,
    reason: StageGateBlockedReason,
) -> None:
    result = evaluate_stage_gate(
        _request(),
        replace(_evidence(), **{field_name: ""}),
    )

    assert result.gate_status == "blocked"
    assert result.blocked_reason is reason
    assert field_name in result.missing_fields
    _assert_zero_counters(result.safety_counters)


def test_blocked_gate_precheck_stops_adapter_before_any_operation() -> None:
    gate_result = evaluate_stage_gate(
        _request(authorization=replace(_authorization(), authorization_id="")),
        _evidence(),
    )

    enable_result = simulation_order_enable(gate_result, AdapterMode.SIMULATION)
    assert enable_result.enabled is False
    assert enable_result.blocked_reason is (
        StageGateBlockedReason.AUTHORIZATION_REQUIRED_MISSING
    )
    _assert_zero_counters(enable_result.safety_counters)

    adapter_result = precheck_stage_gate_result(
        gate_result,
        AdapterMode.SIMULATION,
        intent_id="intent-cr016-s01-blocked",
        evidence_ref="fixture:blocked-gate",
    )
    assert adapter_result is not None
    assert adapter_result.status is AdapterResultStatus.BLOCKED
    assert adapter_result.blocked_reason is AdapterBlockedReason.STAGE_GATE_BLOCKED
    assert adapter_result.detail_code == "authorization_required_missing"
    assert adapter_result.safety_counters["adapter_calls"] == 0
    assert adapter_result.safety_counters["adapter_call_on_block"] == 0
    _assert_zero_counters(adapter_result.safety_counters)


def test_cr017_unverified_blocks_scale_up_even_with_valid_authorization() -> None:
    result = evaluate_stage_gate(
        _request(
            Stage.SMALL_LIVE,
            Stage.SCALE_UP,
            _authorization(Stage.SCALE_UP),
        ),
        _evidence(cr017_verified=False),
    )

    assert result.gate_status == "blocked"
    assert result.blocked_reason is StageGateBlockedReason.CR017_SCALE_UP_NOT_VERIFIED
    assert result.missing_fields == ("cr017_verified",)
    assert result.safety_counters["scale_up_allowed_without_cr017"] == 0
    _assert_zero_counters(result.safety_counters)
