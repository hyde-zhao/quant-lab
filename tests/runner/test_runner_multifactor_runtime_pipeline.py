from __future__ import annotations

import json

from trading.pretrade_risk import RawPriceRef, RiskInputSnapshot, RiskProfile
from trading.qmt_gateway_contracts import (
    QMT_SIMULATION_CANCEL_ENDPOINT_ID,
    QMT_SIMULATION_SUBMIT_ENDPOINT_ID,
    QmtGatewayResult,
    QmtSimulationCancelRequest,
    QmtSimulationOperationPayload,
    QmtSimulationOrderRequest,
    build_simulation_operation_result,
)
from trading.stage_gate import AuthorizationSummary, Stage, StageEvidence, StageGateRequest
from trading.strategy_runner import (
    FunctionSimulationGateway,
    MultifactorSignalRow,
    SimulationExecutionEngineRequest,
    SimulationOpenOrderRef,
    SimulationOrderPlanRequest,
    build_multifactor_target_portfolio,
    build_simulation_order_plan,
    execute_simulation_order_plan,
)


def test_multifactor_target_order_plan_and_simulation_execution_stay_redacted() -> None:
    target = build_multifactor_target_portfolio(
        strategy_id="strategy-alpha",
        source_run_id="run-multifactor-p1",
        target_trade_date="2026-06-25",
        signal_rows=(
            MultifactorSignalRow("000001.SZ", "0.90", "2026-06-24"),
            MultifactorSignalRow("000002.SZ", "0.80", "2026-06-24"),
            MultifactorSignalRow("000003.SZ", "0.10", "2026-06-24", eligible=False),
        ),
        top_n=2,
        weighting="equal",
        max_weight="0.60",
        universe_symbols=("000001.SZ", "000002.SZ", "000003.SZ"),
        score_refs={"model": "multifactor:fixture"},
        lineage_refs={"signals": "fixture:multifactor-signal"},
    )

    assert target.passed is True
    assert target.snapshot is not None
    assert target.selected_count == 2
    rendered_target = json.dumps(target.to_dict(), ensure_ascii=False, sort_keys=True)
    assert "000001.SZ" not in rendered_target
    assert "000002.SZ" not in rendered_target

    plan = build_simulation_order_plan(
        SimulationOrderPlanRequest(
            strategy_id="strategy-alpha",
            run_id="run-multifactor-p2",
            target_trade_date="2026-06-25",
            target_rows=tuple(target.snapshot.rows()),
            capital_base="100000",
            current_positions={"000001.SZ": 1000, "000002.SZ": 3000},
            risk_snapshot=_risk_snapshot(cash_available="50000"),
            risk_profile=_risk_profile(),
            max_turnover_notional="100000",
        )
    )

    assert plan.passed is True
    assert len(plan.orders) == 2
    assert {item.side for item in plan.orders} == {"buy", "sell"}
    rendered_plan = json.dumps(plan.to_dict(), ensure_ascii=False, sort_keys=True)
    assert "000001.SZ" not in rendered_plan
    assert "000002.SZ" not in rendered_plan

    submitted: list[QmtSimulationOrderRequest] = []
    cancelled: list[QmtSimulationCancelRequest] = []

    def submit(request: QmtSimulationOrderRequest) -> QmtGatewayResult:
        submitted.append(request)
        return build_simulation_operation_result(
            QMT_SIMULATION_SUBMIT_ENDPOINT_ID,
            QmtSimulationOperationPayload(
                operation="submit",
                run_id=request.run_id,
                order_intent_id=request.order_intent_id,
                accepted=True,
                broker_order_ref="broker-new-" + str(len(submitted)),
                cancel_ref="cancel-ref-new-" + str(len(submitted)),
                adapter_status="fixture-simulation-submit-accepted",
            ),
        )

    def cancel(request: QmtSimulationCancelRequest) -> QmtGatewayResult:
        cancelled.append(request)
        return build_simulation_operation_result(
            QMT_SIMULATION_CANCEL_ENDPOINT_ID,
            QmtSimulationOperationPayload(
                operation="cancel",
                run_id=request.run_id,
                order_intent_id=request.order_intent_id,
                accepted=True,
                broker_order_ref=request.broker_order_ref,
                cancel_ref="cancelled-fixture",
                adapter_status="fixture-simulation-cancel-accepted",
            ),
        )

    execution = execute_simulation_order_plan(
        SimulationExecutionEngineRequest(
            strategy_id="strategy-alpha",
            run_id="run-multifactor-p3",
            target_trade_date="2026-06-25",
            order_plan=plan,
            stage_request=_stage_request(),
            stage_evidence=_stage_evidence(),
            authorization_ref="auth-simulation-fixture",
            expected_runtime_mode="simulation",
            expected_runtime_profile="cr138-simulation",
            cancel_open_orders=(
                SimulationOpenOrderRef(
                    order_intent_id="intent-existing",
                    broker_order_ref="broker-existing-001",
                    symbol="000001.SZ",
                ),
            ),
        ),
        FunctionSimulationGateway(submit, cancel),
    )

    assert execution.passed is True
    assert execution.status == "executed"
    assert execution.cancelled_count == 1
    assert execution.submitted_count == 2
    assert len(cancelled) == 1
    assert len(submitted) == 2
    assert all(request.price > 0 for request in submitted)
    rendered_execution = json.dumps(execution.to_dict(), ensure_ascii=False, sort_keys=True)
    assert "000001.SZ" not in rendered_execution
    assert "000002.SZ" not in rendered_execution
    assert "broker-existing-001" not in rendered_execution


def test_multifactor_target_portfolio_blocks_invalid_weight_cap_without_runtime() -> None:
    result = build_multifactor_target_portfolio(
        strategy_id="strategy-alpha",
        source_run_id="run-invalid-cap",
        target_trade_date="2026-06-25",
        signal_rows=(MultifactorSignalRow("000001.SZ", "0.90", "2026-06-24"),),
        top_n=1,
        max_weight="0.50",
    )

    assert result.blocked is True
    assert "max_weight" in result.blocked_reason
    assert result.safety_counters["qmt_operation"] == 0


def test_order_plan_blocks_before_execution_when_cash_is_insufficient() -> None:
    target = build_multifactor_target_portfolio(
        strategy_id="strategy-alpha",
        source_run_id="run-cash-block",
        target_trade_date="2026-06-25",
        signal_rows=(MultifactorSignalRow("000001.SZ", "0.90", "2026-06-24"),),
        top_n=1,
    )

    assert target.snapshot is not None
    plan = build_simulation_order_plan(
        SimulationOrderPlanRequest(
            strategy_id="strategy-alpha",
            run_id="run-cash-block",
            target_trade_date="2026-06-25",
            target_rows=tuple(target.snapshot.rows()),
            capital_base="100000",
            risk_snapshot=_risk_snapshot(cash_available="100"),
            risk_profile=_risk_profile(),
        )
    )

    assert plan.blocked is True
    assert plan.blocked_reason == "pretrade_risk_blocked"
    rendered = json.dumps(plan.to_dict(), ensure_ascii=False, sort_keys=True)
    assert "000001.SZ" not in rendered


def test_execution_engine_blocks_runtime_profile_mismatch_before_gateway() -> None:
    target = build_multifactor_target_portfolio(
        strategy_id="strategy-alpha",
        source_run_id="run-runtime-block",
        target_trade_date="2026-06-25",
        signal_rows=(MultifactorSignalRow("000001.SZ", "0.90", "2026-06-24"),),
        top_n=1,
    )
    assert target.snapshot is not None
    plan = build_simulation_order_plan(
        SimulationOrderPlanRequest(
            strategy_id="strategy-alpha",
            run_id="run-runtime-block",
            target_trade_date="2026-06-25",
            target_rows=tuple(target.snapshot.rows()),
            capital_base="100000",
            risk_snapshot=_risk_snapshot(cash_available="100000"),
            risk_profile=_risk_profile(),
        )
    )
    calls = 0

    def submit(request: QmtSimulationOrderRequest) -> QmtGatewayResult:
        nonlocal calls
        calls += 1
        raise AssertionError("gateway must not be called")

    result = execute_simulation_order_plan(
        SimulationExecutionEngineRequest(
            strategy_id="strategy-alpha",
            run_id="run-runtime-block",
            target_trade_date="2026-06-25",
            order_plan=plan,
            stage_request=_stage_request(),
            stage_evidence=_stage_evidence(),
            authorization_ref="auth-simulation-fixture",
            expected_runtime_mode="live",
            expected_runtime_profile="cr138-simulation",
        ),
        FunctionSimulationGateway(submit),
    )

    assert result.blocked is True
    assert result.blocked_reason == "runtime_profile_mismatch"
    assert result.manual_takeover_required is True
    assert calls == 0


def _risk_snapshot(*, cash_available: str) -> RiskInputSnapshot:
    return RiskInputSnapshot(
        cash_available=cash_available,
        positions_available={"000001.SZ": 1000, "000002.SZ": 3000},
        t1_sellable={"000001.SZ": 1000, "000002.SZ": 3000},
        raw_price_refs={
            "000001.SZ": RawPriceRef(symbol="000001.SZ", price="10", evidence_ref="price-ref-1"),
            "000002.SZ": RawPriceRef(symbol="000002.SZ", price="20", evidence_ref="price-ref-2"),
        },
        source_kind="sanitized_snapshot",
        evidence_ref="risk-snapshot-ref",
    )


def _risk_profile() -> RiskProfile:
    return RiskProfile(
        risk_profile_id="risk-profile-simulation",
        max_single_symbol_notional="100000",
        max_portfolio_notional="200000",
        price_deviation_limit_pct="0.20",
        fee_buffer_pct="0.01",
        lot_size=100,
        evidence_ref="risk-profile-ref",
    )


def _stage_request() -> StageGateRequest:
    return StageGateRequest(
        current_stage=Stage.SHADOW,
        target_stage=Stage.SIMULATION,
        authorization_summary=AuthorizationSummary(
            authorization_id="auth-simulation-fixture",
            mode="simulation",
            strategy_id="strategy-alpha",
            run_id="run-multifactor-p3",
            target_stage=Stage.SIMULATION,
            target_trade_date="2026-06-25",
            capital_limit="100000",
            order_scope=("order_intent_submit", "simulation_submit", "simulation_cancel"),
            approver="user",
            approved_at="2026-06-25T09:00:00+08:00",
            expires_at="2026-06-25T23:59:00+08:00",
            rollback_plan_ref="rollback:simulation-fixture",
        ),
        request_ref="request:simulation-execution",
    )


def _stage_evidence() -> StageEvidence:
    return StageEvidence(
        cr015_verified=True,
        runbook_ref="docs/QMT-SIMULATION-LIVE-RUNBOOK.md#simulation",
        cr017_consumer_boundary_ref="docs/QMT-ADJUSTMENT-CONSUMER.md",
        reconciliation_policy_ref="reconciliation:simulation",
        kill_switch_readiness_ref="kill-switch:simulation",
        cr017_verified=True,
    )
