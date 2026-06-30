from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime

from market_data.contracts import (
    ADJUSTMENT_POLICY_HFQ,
    ADJUSTMENT_POLICY_QFQ,
    ADJUSTMENT_POLICY_RAW,
)
from trading.oms import (
    OmsResultStatus,
    OrderIntent,
    OrderState,
    apply_risk_result,
    create_order_intent,
)
from trading.pretrade_risk import (
    RawPriceRef,
    RiskBlockedReason,
    RiskInputSnapshot,
    RiskProfile,
    RiskRuleId,
    evaluate_intent,
    evaluate_many,
    pretrade_risk_safety_counters,
    validate_execution_price_policy,
)


NOW = datetime(2026, 5, 28, 9, 30, tzinfo=UTC)
RISK_PROFILE_ID = "risk-profile-shadow"


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
        "execution_price_policy": ADJUSTMENT_POLICY_RAW,
    }
    metadata.update(overrides)
    return metadata


def _run_context(**overrides: object) -> dict[str, object]:
    context: dict[str, object] = {
        "strategy_id": "strategy-alpha",
        "run_id": "run-cr015-s04",
        "risk_profile_id": RISK_PROFILE_ID,
    }
    context.update(overrides)
    return context


def _intent(**overrides: object) -> OrderIntent:
    result = create_order_intent(
        _target_row(**overrides),
        _policy(),
        _run_context(),
        now=NOW,
    )
    assert result.ok
    assert result.intent is not None
    return result.intent


def _profile(**overrides: object) -> RiskProfile:
    profile = RiskProfile(
        risk_profile_id=RISK_PROFILE_ID,
        max_single_symbol_notional="100000",
        max_portfolio_notional="200000",
        price_deviation_limit_pct="0.20",
        fee_buffer_pct="0",
        lot_size=100,
        evidence_ref="risk-profile-fixture",
    )
    return replace(profile, **overrides)


def _snapshot(**overrides: object) -> RiskInputSnapshot:
    snapshot = RiskInputSnapshot(
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
        evidence_ref="risk-input-fixture",
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
        "adapter_calls": 0,
        "adapter_calls_on_block": 0,
    }
    assert {key: current.get(key, 0) for key in expected} == expected


def _assert_blocked_rule(
    result: object,
    rule_id: RiskRuleId,
    reason: RiskBlockedReason,
) -> None:
    current = result  # type: ignore[assignment]
    assert current.blocked
    assert current.adapter_calls == 0
    _assert_safety_counters_zero(current.safety_counters)
    matches = [rule for rule in current.blocked_rules if rule.rule_id is rule_id]
    assert matches, current.blocked_rules
    rule = matches[0]
    assert rule.blocked_reason == reason.value
    assert rule.intent_id
    assert rule.risk_profile_id == RISK_PROFILE_ID
    assert rule.evidence_ref


def test_risk_pass_uses_fixture_snapshot_only_and_exposes_all_rules() -> None:
    result = evaluate_intent(_intent(), _snapshot(), _profile())

    assert result.passed
    assert result.status == "pass"
    assert result.intent_id
    assert result.risk_profile_id == RISK_PROFILE_ID
    assert result.adapter_calls == 0
    assert len(result.rule_results) == 9
    assert {rule.rule_id for rule in result.rule_results} == set(RiskRuleId)
    assert result.blocked_rules == ()
    _assert_safety_counters_zero(result.safety_counters)


def test_cash_insufficient_hard_blocks_before_adapter() -> None:
    result = evaluate_intent(
        _intent(),
        _snapshot(cash_available="100"),
        _profile(),
    )

    _assert_blocked_rule(
        result,
        RiskRuleId.CASH,
        RiskBlockedReason.CASH_INSUFFICIENT,
    )
    assert "fixture-cash-snapshot" in result.blocked_rules[0].details.values()


def test_non_100_share_lot_hard_blocks() -> None:
    result = evaluate_intent(_intent(target_qty=99), _snapshot(), _profile())

    _assert_blocked_rule(
        result,
        RiskRuleId.LOT_SIZE,
        RiskBlockedReason.LOT_SIZE_INVALID,
    )


def test_t1_sellable_and_position_available_are_separate_sell_rules() -> None:
    sell_intent = _intent(side="sell", target_qty=200)

    t1_blocked = evaluate_intent(
        sell_intent,
        _snapshot(t1_sellable={"000001.SZ": 100}),
        _profile(),
    )
    _assert_blocked_rule(
        t1_blocked,
        RiskRuleId.T1_SELLABLE,
        RiskBlockedReason.T1_NOT_SELLABLE,
    )

    position_blocked = evaluate_intent(
        sell_intent,
        _snapshot(positions_available={"000001.SZ": 100}),
        _profile(),
    )
    _assert_blocked_rule(
        position_blocked,
        RiskRuleId.POSITION_AVAILABLE,
        RiskBlockedReason.POSITION_INSUFFICIENT,
    )


def test_price_policy_blocks_non_raw_execution_and_qfq_hfq_price_refs() -> None:
    base_intent = _intent()
    non_raw_intent = replace(
        base_intent,
        execution_price_policy=ADJUSTMENT_POLICY_QFQ,
    )
    non_raw = evaluate_intent(non_raw_intent, _snapshot(), _profile())
    _assert_blocked_rule(
        non_raw,
        RiskRuleId.PRICE_POLICY,
        RiskBlockedReason.NON_RAW_EXECUTION_PRICE_BLOCKED,
    )

    qfq_price = evaluate_intent(
        base_intent,
        _snapshot(
            raw_price_refs={
                "000001.SZ": RawPriceRef(
                    symbol="000001.SZ",
                    price="10",
                    price_policy=ADJUSTMENT_POLICY_QFQ,
                    status="available",
                    reference_price="10",
                    evidence_ref="qfq-price-fixture",
                )
            }
        ),
        _profile(),
    )
    _assert_blocked_rule(
        qfq_price,
        RiskRuleId.PRICE_POLICY,
        RiskBlockedReason.NON_RAW_EXECUTION_PRICE_BLOCKED,
    )

    hfq_guard = validate_execution_price_policy(
        base_intent,
        RawPriceRef(
            symbol="000001.SZ",
            price="10",
            price_policy=ADJUSTMENT_POLICY_HFQ,
        ),
        risk_profile_id=RISK_PROFILE_ID,
        evidence_ref="hfq-price-fixture",
    )
    assert hfq_guard.blocked
    assert hfq_guard.blocked_reason == (
        RiskBlockedReason.NON_RAW_EXECUTION_PRICE_BLOCKED.value
    )


def test_duplicate_intent_hard_blocks_by_run_id_and_idempotency_key() -> None:
    intent = _intent()
    duplicate_key = f"{intent.run_id}:{intent.idempotency_key}"

    result = evaluate_intent(
        intent,
        _snapshot(existing_intent_keys=frozenset({duplicate_key})),
        _profile(),
    )

    _assert_blocked_rule(
        result,
        RiskRuleId.DUPLICATE_INTENT,
        RiskBlockedReason.DUPLICATE_INTENT,
    )


def test_single_symbol_and_portfolio_limits_hard_block() -> None:
    single = evaluate_intent(
        _intent(),
        _snapshot(),
        _profile(max_single_symbol_notional="1000"),
    )
    _assert_blocked_rule(
        single,
        RiskRuleId.SINGLE_SYMBOL_LIMIT,
        RiskBlockedReason.SINGLE_SYMBOL_LIMIT_EXCEEDED,
    )

    first = _intent(target_qty=100)
    second = _intent(target_qty=300)
    batch = evaluate_many(
        (first, second),
        _snapshot(),
        _profile(max_portfolio_notional="3000"),
    )
    assert not batch.passed
    assert batch.adapter_calls == 0
    _assert_safety_counters_zero(batch.safety_counters)
    assert {
        rule.blocked_reason
        for rule in batch.blocked_rules
        if rule.rule_id is RiskRuleId.PORTFOLIO_LIMIT
    } == {RiskBlockedReason.PORTFOLIO_LIMIT_EXCEEDED.value}


def test_abnormal_price_hard_blocks() -> None:
    result = evaluate_intent(
        _intent(),
        _snapshot(
            raw_price_refs={
                "000001.SZ": RawPriceRef(
                    symbol="000001.SZ",
                    price="15",
                    price_policy=ADJUSTMENT_POLICY_RAW,
                    status="available",
                    reference_price="10",
                    evidence_ref="abnormal-price-fixture",
                )
            }
        ),
        _profile(price_deviation_limit_pct="0.20"),
    )

    _assert_blocked_rule(
        result,
        RiskRuleId.ABNORMAL_PRICE,
        RiskBlockedReason.ABNORMAL_PRICE,
    )


def test_snapshot_source_must_be_fixture_or_sanitized_contract() -> None:
    result = evaluate_intent(
        _intent(),
        _snapshot(source_kind="real_account"),
        _profile(),
    )

    _assert_blocked_rule(
        result,
        RiskRuleId.PRICE_POLICY,
        RiskBlockedReason.UNSUPPORTED_SNAPSHOT_SOURCE,
    )


def test_oms_apply_risk_result_consumes_s04_dataclass_without_state_semantic_change() -> None:
    intent = _intent()
    blocked_risk = evaluate_intent(
        intent,
        _snapshot(cash_available="100"),
        _profile(),
    )

    blocked = apply_risk_result(intent, blocked_risk, now=NOW)
    assert blocked.status is OmsResultStatus.APPLIED
    assert blocked.intent is not None
    assert blocked.intent.state is OrderState.BLOCKED
    assert blocked.transition_event is not None
    assert blocked.transition_event.reason == RiskBlockedReason.CASH_INSUFFICIENT.value
    _assert_safety_counters_zero(blocked_risk.safety_counters)

    passed = apply_risk_result(_intent(), evaluate_intent(_intent(), _snapshot(), _profile()))
    assert passed.status is OmsResultStatus.APPLIED
    assert passed.intent is not None
    assert passed.intent.state is OrderState.RISK_PASSED


def test_pretrade_safety_counters_keep_all_real_operations_at_zero() -> None:
    _assert_safety_counters_zero(pretrade_risk_safety_counters())
