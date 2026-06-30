from trading.broker_lake import (
    BROKER_LAKE_SCHEMA_VERSION,
    BrokerLakeEventType,
    BrokerLakePlanStatus,
    REDACTED_VALUE,
    build_broker_lake_audit_chain,
    build_schema_audit_summary,
    dry_run_write_plan,
    sensitive_raw_value_output_count,
)


RUN_ID = "cr139-w2-broker_lake-qmt-20260526-audit"
STRATEGY_ID = "strategy-alpha"
ORDER_INTENT_ID = "intent-001"


def _event(event_type: str, **overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "event_type": event_type,
        "strategy_id": STRATEGY_ID,
        "run_id": RUN_ID,
        "order_intent_id": ORDER_INTENT_ID,
        "trade_date": "2026-05-26",
        "symbol": "000001.SZ",
    }
    payload.update(overrides)
    return payload


def test_s20_broker_lake_schema_registry_covers_runid_partitioned_audit_events() -> None:
    summary = build_schema_audit_summary()

    assert summary["schema_version"] == BROKER_LAKE_SCHEMA_VERSION
    assert summary["event_type_count"] == 8
    for event_type in BrokerLakeEventType:
        schema = summary["schemas"][event_type.value]
        assert "run_id" in schema["required_fields"]
        assert schema["partition_keys"] == ("trade_date", "run_id")


def test_s20_broker_lake_audit_chain_is_dry_run_and_runid_consistent() -> None:
    chain = build_broker_lake_audit_chain(
        (
            _event(
                "order_intent",
                side="buy",
                target_qty=100,
                target_trade_date="2026-05-26",
                execution_price_policy="raw_close",
            ),
            _event("broker_order", broker_order_status="accepted", oms_event="submitted"),
            _event("fill", filled_qty=100, fill_price_policy="broker_reported"),
            _event("position", position_qty=100),
        ),
        root_label="BROKER_LAKE_ROOT",
    )

    assert chain.passed
    assert chain.run_id == RUN_ID
    assert chain.strategy_id == STRATEGY_ID
    assert chain.order_intent_id == ORDER_INTENT_ID
    assert chain.real_write is False
    assert len(chain.event_plans) == 4
    assert all(plan.status is BrokerLakePlanStatus.PLANNED for plan in chain.event_plans)
    assert all(plan.real_write is False for plan in chain.event_plans)
    assert all(value == 0 for value in chain.safety_counters.values())


def test_s20_broker_lake_real_path_target_is_blocked_without_write() -> None:
    plan = dry_run_write_plan(
        _event(
            "order_intent",
            side="buy",
            target_qty=100,
            target_trade_date="2026-05-26",
            execution_price_policy="raw_close",
        ),
        root_label="data/broker_lake",
    )

    assert plan.status is BrokerLakePlanStatus.BLOCKED
    assert plan.real_write is False
    assert plan.safety_counters["real_broker_lake_write"] == 0
    assert plan.safety_counters["open_write_call"] == 0


def test_s20_broker_lake_sensitive_values_are_not_emitted() -> None:
    sensitive_values = ("account=123456", "session:abc", "/home/test-user/broker")
    plan = dry_run_write_plan(
        _event(
            "broker_order",
            broker_order_status="accepted",
            oms_event="submitted",
            account_id=sensitive_values[0],
            session_cookie=sensitive_values[1],
            broker_root=sensitive_values[2],
        ),
        root_label="BROKER_LAKE_ROOT",
    )

    assert plan.status is BrokerLakePlanStatus.PLANNED
    assert plan.sanitized_event["account_id"] == REDACTED_VALUE
    assert plan.sanitized_event["session_cookie"] == REDACTED_VALUE
    assert plan.sanitized_event["broker_root"] == REDACTED_VALUE
    assert sensitive_raw_value_output_count(plan, sensitive_values) == 0
