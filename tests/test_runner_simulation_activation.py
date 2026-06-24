from __future__ import annotations

import json
from decimal import Decimal

from trading.pretrade_risk import RawPriceRef, RiskInputSnapshot, RiskProfile
from trading.qmt_gateway_contracts import (
    QMT_SIMULATION_SUBMIT_ENDPOINT_ID,
    QmtGatewayResult,
    QmtSimulationOperationPayload,
    QmtSimulationOrderRequest,
    build_simulation_operation_result,
)
from trading.stage_gate import AuthorizationSummary, Stage, StageEvidence, StageGateRequest
from trading.strategy_runner.simulation_activation import (
    FunctionSimulationGateway,
    SimulationActivationRequest,
    activate_simulation_orders,
    blocked_simulation_gateway,
)


def test_activate_simulation_orders_submits_target_portfolio_after_gates_pass() -> None:
    submitted: list[QmtSimulationOrderRequest] = []

    def submit(request: QmtSimulationOrderRequest) -> QmtGatewayResult:
        submitted.append(request)
        return build_simulation_operation_result(
            QMT_SIMULATION_SUBMIT_ENDPOINT_ID,
            QmtSimulationOperationPayload(
                operation="submit",
                run_id=request.run_id,
                order_intent_id=request.order_intent_id,
                accepted=True,
                broker_order_ref="broker-order-runtime-001",
                adapter_status="xtquant-simulation-submit-accepted",
            ),
            counters={"qmt_operation": 1, "qmt_api_call": 1, "real_order": 1},
        )

    result = activate_simulation_orders(
        _activation_request(cash_available="100000"),
        FunctionSimulationGateway(submit),
    )

    assert result.passed is True
    assert result.status == "submitted"
    assert result.submitted_count == 1
    assert len(submitted) == 1
    assert submitted[0].symbol == "000001.SZ"
    assert submitted[0].quantity == 2000
    assert submitted[0].authorization_ref == "auth-simulation-fixture"
    assert result.orders[0].gateway_status == "allowed"
    assert result.orders[0].risk_status == "pass"
    rendered = json.dumps(result.to_dict(), ensure_ascii=False, sort_keys=True)
    assert "000001.SZ" not in rendered
    assert result.orders[0].symbol_ref.startswith("symbol:")


def test_activate_simulation_orders_blocks_before_gateway_when_stage_gate_missing() -> None:
    request = _activation_request(cash_available="100000", runbook_ref="")

    result = activate_simulation_orders(request, blocked_simulation_gateway())

    assert result.blocked is True
    assert result.blocked_reason == "runbook_required_missing"
    assert result.submitted_count == 0
    assert result.orders == ()


def test_activate_simulation_orders_blocks_before_gateway_when_risk_fails() -> None:
    calls = 0

    def submit(request: QmtSimulationOrderRequest) -> QmtGatewayResult:
        nonlocal calls
        calls += 1
        raise AssertionError("gateway must not be called when pretrade risk blocks")

    result = activate_simulation_orders(
        _activation_request(cash_available="1000"),
        FunctionSimulationGateway(submit),
    )

    assert result.blocked is True
    assert result.blocked_reason == "pretrade_risk_blocked"
    assert result.submitted_count == 0
    assert calls == 0
    assert result.orders[0].risk_status == "blocked"
    assert "cash_insufficient" in result.orders[0].blocked_reason


def _activation_request(
    *,
    cash_available: str,
    runbook_ref: str = "docs/QMT-SIMULATION-LIVE-RUNBOOK.md#simulation",
) -> SimulationActivationRequest:
    return SimulationActivationRequest(
        strategy_id="strategy-alpha",
        run_id="run-simulation-activation",
        target_trade_date="2026-06-24",
        target_rows=(
            {
                "symbol": "000001.SZ",
                "side": "buy",
                "target_weight": Decimal("0.20"),
                "signal_date": "2026-06-23",
            },
        ),
        capital_base="100000",
        risk_snapshot=RiskInputSnapshot(
            cash_available=cash_available,
            raw_price_refs={
                "000001.SZ": RawPriceRef(
                    symbol="000001.SZ",
                    price="10",
                    evidence_ref="raw-price-ref",
                )
            },
            source_kind="sanitized_snapshot",
            evidence_ref="risk-snapshot-ref",
        ),
        risk_profile=RiskProfile(
            risk_profile_id="risk-profile-simulation",
            max_single_symbol_notional="50000",
            max_portfolio_notional="100000",
            price_deviation_limit_pct="0.20",
            fee_buffer_pct="0.01",
            lot_size=100,
            evidence_ref="risk-profile-ref",
        ),
        stage_request=StageGateRequest(
            current_stage=Stage.SHADOW,
            target_stage=Stage.SIMULATION,
            authorization_summary=AuthorizationSummary(
                authorization_id="auth-simulation-fixture",
                mode="simulation",
                strategy_id="strategy-alpha",
                run_id="run-simulation-activation",
                target_stage=Stage.SIMULATION,
                target_trade_date="2026-06-24",
                capital_limit="100000",
                order_scope=("order_intent_submit", "simulation_submit"),
                approver="user",
                approved_at="2026-06-24T19:00:00+08:00",
                expires_at="2026-06-24T23:59:00+08:00",
                rollback_plan_ref="rollback:simulation-fixture",
            ),
            request_ref="request:simulation-activation",
        ),
        stage_evidence=StageEvidence(
            cr015_verified=True,
            runbook_ref=runbook_ref,
            cr017_consumer_boundary_ref="docs/QMT-ADJUSTMENT-CONSUMER.md",
            reconciliation_policy_ref="reconciliation:simulation",
            kill_switch_readiness_ref="kill-switch:simulation",
            cr017_verified=True,
        ),
        authorization_ref="auth-simulation-fixture",
    )
