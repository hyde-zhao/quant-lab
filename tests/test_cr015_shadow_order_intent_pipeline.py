from __future__ import annotations

import builtins
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path

import pytest

from market_data.contracts import ADJUSTMENT_POLICY_QFQ, ADJUSTMENT_POLICY_RAW
from trading.broker_lake import BrokerLakePlanStatus
from trading.oms import OmsEvent, OrderState
from trading.pretrade_risk import RawPriceRef, RiskBlockedReason, RiskRuleId
from trading.shadow_pipeline import (
    FixtureSnapshots,
    build_safety_counters,
    shadow_run,
    validate_shadow_mode,
)


NOW = datetime(2026, 5, 28, 9, 30, tzinfo=UTC)


def _target_row(**overrides: object) -> dict[str, object]:
    row: dict[str, object] = {
        "symbol": "000001.SZ",
        "side": "buy",
        "target_qty": 200,
        "target_trade_date": "2026-05-29",
        "signal_date": "2026-05-28",
    }
    row.update(overrides)
    return row


def _policy(**overrides: object) -> dict[str, object]:
    metadata: dict[str, object] = {
        "research_adjustment_policy": ADJUSTMENT_POLICY_QFQ,
        "view_id": "prices_qfq",
        "source_run_id": "run-cr017-s04",
        "quality_status": "pass",
        "execution_price_policy": ADJUSTMENT_POLICY_RAW,
    }
    metadata.update(overrides)
    return metadata


def _run_context(**overrides: object) -> dict[str, object]:
    context: dict[str, object] = {
        "shadow_run_id": "shadow-run-cr015-s06",
        "strategy_id": "strategy-alpha",
        "run_id": "run-cr015-s06",
        "risk_profile_id": "risk-profile-shadow",
        "mode": "mock",
        "broker_lake_root_label": "BROKER_LAKE_ROOT",
        "max_single_symbol_notional": "100000",
        "max_portfolio_notional": "200000",
        "target_trade_date": "2026-05-29",
    }
    context.update(overrides)
    return context


def _snapshots(**overrides: object) -> FixtureSnapshots:
    snapshot = FixtureSnapshots(
        cash_available="100000",
        positions_available={"000001.SZ": 1000},
        t1_sellable={"000001.SZ": 1000},
        raw_price_refs={
            "000001.SZ": RawPriceRef(
                symbol="000001.SZ",
                price="10",
                price_policy=ADJUSTMENT_POLICY_RAW,
                status="available",
                reference_price="10",
                evidence_ref="raw-price-fixture",
            )
        },
        existing_intent_keys=frozenset(),
        portfolio_current_notional="0",
        source_kind="fixture",
        cash_available_ref="fixture-cash-snapshot",
        position_available_ref="fixture-position-snapshot",
        evidence_ref="shadow-fixture-snapshot",
    )
    return replace(snapshot, **overrides)


def _assert_safety_counters_zero(counters: object) -> None:
    current = dict(counters)  # type: ignore[arg-type]
    expected = {
        "qmt_api_call": 0,
        "real_order_call": 0,
        "real_cancel_call": 0,
        "account_query_call": 0,
        "account_write_call": 0,
        "credential_read": 0,
        "real_broker_lake_write": 0,
        "real_lake_write": 0,
        "provider_fetch": 0,
        "publish": 0,
        "dependency_change": 0,
        "adapter_calls_on_block": 0,
        "non_raw_execution_pass_count": 0,
        "activation_mode_pass_count": 0,
        "real_qmt_process_invocation": 0,
        "real_order": 0,
        "real_cancel": 0,
        "account_query": 0,
        "account_write": 0,
        "open_write_call": 0,
        "sensitive_raw_value_output": 0,
        "adjusted_execution_price_pass_count": 0,
    }
    assert {key: current.get(key, 0) for key in expected} == expected


def test_shadow_run_outputs_four_foundation_artifacts_and_zero_safety_counts() -> None:
    result = shadow_run(
        [_target_row()],
        _policy(),
        _snapshots(),
        _run_context(mode="mock"),
        now=NOW,
    )

    assert result.status == "pass"
    assert result.mode == "mock"
    assert result.policy_metadata["research_adjustment_policy"] == ADJUSTMENT_POLICY_QFQ
    assert result.policy_metadata["view_id"] == "prices_qfq"
    assert result.policy_metadata["source_run_id"] == "run-cr017-s04"
    assert result.policy_metadata["quality_status"] == "pass"
    assert result.policy_metadata["execution_price_policy"] == ADJUSTMENT_POLICY_RAW
    assert result.policy_metadata["adjusted_execution_price_pass_count"] == 0
    assert len(result.intents) == 1
    assert result.intents[0].state is OrderState.ACCEPTED
    assert len(result.risk_results) == 1
    assert result.risk_results[0].passed
    assert len(result.broker_events) == 1
    assert {event.event for event in result.state_transitions} == {
        OmsEvent.RISK_PASS,
        OmsEvent.ADAPTER_ACCEPTED,
    }
    assert result.dry_run_plans
    assert all(plan.real_write is False for plan in result.dry_run_plans)
    assert all(plan.status is BrokerLakePlanStatus.PLANNED for plan in result.dry_run_plans)
    assert {plan.event_type for plan in result.dry_run_plans} == {
        "order_intent",
        "broker_order",
    }
    assert result.audit_summary["intent_count"] == 1
    assert result.audit_summary["risk_pass_count"] == 1
    assert result.audit_summary["mock_broker_event_count"] == 1
    assert result.audit_summary["broker_lake_dry_run_plan_count"] == len(
        result.dry_run_plans
    )
    assert result.adapter_call_count == 1
    _assert_safety_counters_zero(result.safety_counters)


@pytest.mark.parametrize(
    "mode",
    ["simulation", "live_readonly", "small_live", "scale_up"],
)
def test_activation_modes_are_blocked_without_intents_or_adapter_calls(mode: str) -> None:
    gate = validate_shadow_mode(mode)
    assert gate.passed is False
    assert gate.blocked_reason == "activation_not_authorized"

    result = shadow_run(
        [_target_row()],
        _policy(),
        _snapshots(),
        _run_context(mode=mode),
        now=NOW,
    )

    assert result.status == "blocked"
    assert result.blocked_reasons == ("activation_not_authorized",)
    assert result.intents == ()
    assert result.risk_results == ()
    assert result.broker_events == ()
    assert result.adapter_call_count == 0
    assert result.audit_summary["adapter_calls"] == 0
    assert result.audit_summary["activation_mode_pass_count"] == 0
    assert len(result.dry_run_plans) == 1
    assert result.dry_run_plans[0].real_write is False
    _assert_safety_counters_zero(result.safety_counters)


def test_non_raw_execution_policy_blocks_and_pass_count_remains_zero() -> None:
    result = shadow_run(
        [_target_row()],
        _policy(execution_price_policy="qfq"),
        _snapshots(),
        _run_context(mode="mock"),
        now=NOW,
    )

    assert result.status == "blocked"
    assert result.blocked_reasons == ("non_raw_execution_price_blocked",)
    assert result.intents == ()
    assert result.risk_results == ()
    assert result.broker_events == ()
    assert result.adapter_call_count == 0
    assert result.safety_counters["non_raw_execution_pass_count"] == 0
    assert result.audit_summary["non_raw_execution_pass_count"] == 0
    assert result.dry_run_plans[0].real_write is False
    _assert_safety_counters_zero(result.safety_counters)


def test_risk_fail_does_not_call_adapter_or_generate_mock_event_but_outputs_audit() -> None:
    result = shadow_run(
        [_target_row()],
        _policy(),
        _snapshots(cash_available="100"),
        _run_context(mode="mock"),
        now=NOW,
    )

    assert result.status == "blocked"
    assert len(result.intents) == 1
    assert result.intents[0].state is OrderState.BLOCKED
    assert len(result.risk_results) == 1
    assert result.risk_results[0].blocked
    assert result.risk_results[0].adapter_calls == 0
    assert result.adapter_results == ()
    assert result.broker_events == ()
    assert result.adapter_call_count == 0
    assert result.audit_summary["adapter_calls"] == 0
    assert result.audit_summary["risk_blocked_count"] == 1
    assert RiskBlockedReason.CASH_INSUFFICIENT.value in result.blocked_reasons
    assert {event.event for event in result.state_transitions} == {OmsEvent.RISK_BLOCKED}
    assert result.dry_run_plans
    assert all(plan.real_write is False for plan in result.dry_run_plans)
    assert result.safety_counters["adapter_calls_on_block"] == 0
    _assert_safety_counters_zero(result.safety_counters)


def test_broker_lake_dry_run_plan_does_not_open_mkdir_or_write(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = {"open": 0, "mkdir": 0, "write_text": 0}

    def fail_open(*args: object, **kwargs: object) -> object:
        calls["open"] += 1
        raise AssertionError("shadow_run broker lake plan must not open files")

    def fail_mkdir(*args: object, **kwargs: object) -> object:
        calls["mkdir"] += 1
        raise AssertionError("shadow_run broker lake plan must not mkdir")

    def fail_write_text(*args: object, **kwargs: object) -> object:
        calls["write_text"] += 1
        raise AssertionError("shadow_run broker lake plan must not write files")

    monkeypatch.setattr(builtins, "open", fail_open)
    monkeypatch.setattr(Path, "mkdir", fail_mkdir)
    monkeypatch.setattr(Path, "write_text", fail_write_text)

    result = shadow_run(
        [_target_row()],
        _policy(),
        _snapshots(),
        _run_context(mode="mock"),
        now=NOW,
    )

    assert result.status == "pass"
    assert result.safety_counters["real_broker_lake_write"] == 0
    assert all(plan.safety_counters["open_write_call"] == 0 for plan in result.dry_run_plans)
    assert calls == {"open": 0, "mkdir": 0, "write_text": 0}


def test_target_weight_sizing_uses_fixture_and_non_lot_reaches_risk_block() -> None:
    result = shadow_run(
        [_target_row(target_qty="", target_weight="0.333", side="")],
        _policy(),
        _snapshots(cash_available="10000", positions_available={"000001.SZ": 0}),
        _run_context(mode="mock"),
        now=NOW,
    )

    assert result.status == "blocked"
    assert len(result.intents) == 1
    assert result.intents[0].target_qty == 333
    assert result.risk_results[0].blocked
    assert {
        rule.rule_id
        for rule in result.risk_results[0].blocked_rules
    } >= {RiskRuleId.LOT_SIZE}
    assert RiskBlockedReason.LOT_SIZE_INVALID.value in result.blocked_reasons
    assert result.adapter_call_count == 0
    assert result.broker_events == ()
    _assert_safety_counters_zero(build_safety_counters())
    _assert_safety_counters_zero(result.safety_counters)
