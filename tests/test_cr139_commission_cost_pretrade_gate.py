from trading.qmt_gateway_contracts import (
    COST_MODEL_REF_MISSING,
    COST_PRETRADE_GATE_ALLOWED,
    COST_SCHEDULE_VERSION_MISSING,
    LIQUIDITY_REF_MISSING,
    TRADABILITY_UNAVAILABLE,
    CommissionSchedule,
    CostPretradeGateInput,
    evaluate_cost_pretrade_gate,
)


def _schedule(**overrides) -> CommissionSchedule:
    payload = {
        "instrument_type": "stock",
        "rate": 0.0003,
        "min_fee": 5.0,
        "source": "configured",
        "version": "commission-config-v1",
        "effective_from": "2026-06-30",
        "release_id": "config-facts-cr139-v1",
        "slippage_bps": 8.0,
        "stamp_duty_rate": 0.001,
        "transfer_fee_rate": 0.00001,
    }
    payload.update(overrides)
    return CommissionSchedule(**payload)


def test_s21_cost_pretrade_gate_allows_versioned_cost_and_liquidity_refs() -> None:
    decision = evaluate_cost_pretrade_gate(
        CostPretradeGateInput(
            order_intent_ref="intent:redacted",
            notional=10_000.0,
            side="sell",
            tradability_status="available",
            schedule=_schedule(),
            cost_model_ref="config_facts/commission/stock/config-facts-cr139-v1",
            liquidity_ref="readiness/liquidity/prices/20260102",
        )
    )

    assert decision.status == COST_PRETRADE_GATE_ALLOWED
    assert decision.allowed is True
    assert decision.blocked_reasons == ()
    assert decision.schedule_version == "commission-config-v1"
    assert decision.schedule_release_id == "config-facts-cr139-v1"
    assert decision.estimated_total_cost == 23.1


def test_s21_cost_pretrade_gate_blocks_missing_schedule_version_metadata() -> None:
    decision = evaluate_cost_pretrade_gate(
        {
            "order_intent_ref": "intent:redacted",
            "notional": 10_000.0,
            "side": "buy",
            "tradability_status": "available",
            "schedule": _schedule(version="", release_id=""),
            "cost_model_ref": "config_facts/commission/stock/config-facts-cr139-v1",
            "liquidity_ref": "readiness/liquidity/prices/20260102",
        }
    )

    assert decision.allowed is False
    assert COST_SCHEDULE_VERSION_MISSING in decision.blocked_reasons
    assert decision.estimated_total_cost == 0.0


def test_s21_cost_pretrade_gate_blocks_missing_refs_and_unavailable_tradability() -> None:
    decision = evaluate_cost_pretrade_gate(
        CostPretradeGateInput(
            order_intent_ref="intent:redacted",
            notional=10_000.0,
            side="buy",
            tradability_status="halted",
            schedule=_schedule(),
        )
    )

    assert decision.allowed is False
    assert {
        COST_MODEL_REF_MISSING,
        LIQUIDITY_REF_MISSING,
        TRADABILITY_UNAVAILABLE,
    } <= set(decision.blocked_reasons)


def test_s21_cost_pretrade_gate_real_operation_counters_are_zero() -> None:
    decision = evaluate_cost_pretrade_gate(
        CostPretradeGateInput(
            order_intent_ref="intent:redacted",
            notional=10_000.0,
            side="sell",
            tradability_status="available",
            schedule=_schedule(),
            cost_model_ref="config_facts/commission/stock/config-facts-cr139-v1",
            liquidity_ref="readiness/liquidity/prices/20260102",
        )
    )

    assert decision.operation_counters
    assert all(value == 0 for value in decision.operation_counters.values())
