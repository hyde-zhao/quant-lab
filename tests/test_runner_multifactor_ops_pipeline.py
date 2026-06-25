from __future__ import annotations

import json

from trading.reconciliation import RECON_DIMENSIONS, ThresholdConfig
from trading.strategy_runner import (
    SimulationExecutionAction,
    SimulationExecutionEngineResult,
    SimulationReconciliationRequest,
    SimulationRunbookStep,
    build_deferred_live_switch_scenario_pack,
    build_simulation_operational_runbook,
    reconcile_simulation_run,
)


def test_simulation_reconciliation_passes_with_redacted_summary_only() -> None:
    result = reconcile_simulation_run(
        SimulationReconciliationRequest(
            run_id="run-p4-recon",
            target_portfolio_ref="target-portfolio:fixture",
            pre_positions_digest="positions:pre-digest",
            post_positions_digest="positions:post-digest",
            execution_result=_execution_result(),
            local_state=_state(position_count=2),
            broker_facts=_state(position_count=2),
            broker_lake_facts={"count": 6, "ref": "broker-lake:facts"},
            thresholds=_thresholds(),
        )
    )

    assert result.passed is True
    assert result.drift_bucket == "drift:pass"
    assert result.unresolved_count == 0
    assert result.manual_takeover_required is False
    rendered = json.dumps(result.to_dict(), ensure_ascii=False, sort_keys=True)
    assert "000001.SZ" not in rendered
    assert "000002.SZ" not in rendered
    assert "account-fixture" not in rendered
    assert result.safety_counters["credential_read"] == 0
    assert result.safety_counters["qmt_api_call"] == 0


def test_simulation_reconciliation_blocks_next_run_when_unresolved_order_exists() -> None:
    execution = SimulationExecutionEngineResult(
        status="blocked",
        run_id="run-p4-unresolved",
        stage_gate_status="pass",
        actions=(
            SimulationExecutionAction(
                operation="submit",
                order_intent_id="intent-unknown",
                status="unknown",
                instrument_ref="instrument:abc",
            ),
        ),
        unknown_count=1,
        manual_takeover_required=True,
    )

    result = reconcile_simulation_run(
        SimulationReconciliationRequest(
            run_id="run-p4-unresolved",
            target_portfolio_ref="target-portfolio:fixture",
            pre_positions_digest="positions:pre-digest",
            post_positions_digest="positions:post-digest",
            execution_result=execution,
            local_state=_state(position_count=2),
            broker_facts=_state(position_count=2),
            broker_lake_facts={"count": 6, "ref": "broker-lake:facts"},
            thresholds=_thresholds(),
        )
    )

    assert result.blocked is True
    assert result.blocked_reason == "unresolved_orders_present"
    assert result.unresolved_count == 1
    assert result.manual_takeover_required is True


def test_simulation_operational_runbook_requires_all_p5_steps() -> None:
    runbook = build_simulation_operational_runbook(
        runbook_ref="process/runbooks/RUNNER-QMT-SIMULATION-MULTIFACTOR-STRATEGY-RUNTIME-RUNBOOK-2026-06-25.md",
        steps=_runbook_steps(),
    )

    assert runbook.passed is True
    rendered = json.dumps(runbook.to_dict(), ensure_ascii=False, sort_keys=True)
    assert "not_runtime_authorization" in rendered
    assert runbook.safety_counters["simulation_or_live_run"] == 0

    blocked = build_simulation_operational_runbook(
        runbook_ref="process/runbooks/RUNNER-QMT-SIMULATION-MULTIFACTOR-STRATEGY-RUNTIME-RUNBOOK-2026-06-25.md",
        steps=tuple(step for step in _runbook_steps() if step.step_id != "reconciliation"),
    )
    assert blocked.blocked is True
    assert "reconciliation" in blocked.blocked_reason


def test_deferred_live_switch_pack_records_p6_without_authorizing_live() -> None:
    pack = build_deferred_live_switch_scenario_pack(
        simulation_readiness_ref="process/checks/RUNNER-QMT-SIMULATION-MULTIFACTOR-STRATEGY-RUNTIME-P5-OPERATIONAL-RUNBOOK-2026-06-25.md"
    )

    assert pack.passed is True
    assert pack.target_id == "DEFERRED-SIMULATION-TO-LIVE-SWITCH"
    assert len(pack.decision_items) >= 4
    assert pack.live_runtime_authorization_granted is False
    assert pack.not_implementation is True
    assert pack.safety_counters["small_live_or_live_run"] == 0


def _execution_result() -> SimulationExecutionEngineResult:
    return SimulationExecutionEngineResult(
        status="executed",
        run_id="run-p4-recon",
        stage_gate_status="pass",
        actions=(
            SimulationExecutionAction(
                operation="cancel",
                order_intent_id="intent-old",
                status="accepted",
                instrument_ref="instrument:old",
                broker_order_ref="broker-order:redacted",
                cancel_ref="cancel-ref:old",
            ),
            SimulationExecutionAction(
                operation="submit",
                order_intent_id="intent-buy",
                status="accepted",
                instrument_ref="instrument:buy",
                broker_order_ref="broker-order:redacted",
                cancel_ref="cancel-ref:buy",
            ),
        ),
        submitted_count=1,
        cancelled_count=1,
    )


def _state(*, position_count: int) -> dict[str, object]:
    return {
        "orders": {"count": 1, "ref": "state:orders"},
        "fills": {"count": 1, "ref": "state:fills"},
        "positions": {"count": position_count, "symbol": "000001.SZ", "ref": "state:positions"},
        "assets": {"value": 1000.0, "ref": "state:assets"},
        "cash": {"value": 100.0, "ref": "state:cash"},
        "broker_lake_facts": {"count": 6, "ref": "state:broker-lake"},
    }


def _thresholds() -> ThresholdConfig:
    return ThresholdConfig(
        warn={dimension: 0.1 for dimension in RECON_DIMENSIONS},
        manual_review={dimension: 2.0 for dimension in RECON_DIMENSIONS},
        kill_switch={dimension: 10.0 for dimension in RECON_DIMENSIONS},
    )


def _runbook_steps() -> tuple[SimulationRunbookStep, ...]:
    refs = {
        "pre_market_check": "evidence:p4-pre-market",
        "gateway_health": "evidence:p0-runtime-profile",
        "runtime_profile_check": "evidence:p0-runtime-profile",
        "target_portfolio_generation": "evidence:p1-target-portfolio",
        "order_plan_review": "evidence:p2-order-plan",
        "simulation_submit_cancel": "evidence:p3-execution",
        "reconciliation": "evidence:p4-reconciliation",
        "exception_recovery": "evidence:p4-kill-switch-candidate",
        "eod_cancel_unfinished": "evidence:p3-cancel-open-orders",
    }
    return tuple(
        SimulationRunbookStep(step_id=step_id, title=step_id.replace("_", " "), evidence_ref=ref)
        for step_id, ref in refs.items()
    )
