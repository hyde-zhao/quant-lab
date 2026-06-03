from __future__ import annotations

import builtins
from datetime import UTC, datetime
from pathlib import Path

import pytest

from market_data.contracts import ADJUSTMENT_POLICY_QFQ, ADJUSTMENT_POLICY_RAW
from trading.broker_lake import (
    BROKER_LAKE_SCHEMA_VERSION,
    BROKER_LAKE_SCHEMAS,
    REDACTED_VALUE,
    BrokerLakeErrorCode,
    BrokerLakeEventType,
    BrokerLakePlanStatus,
    RedactionStatus,
    broker_lake_safety_counters,
    build_schema_audit_summary,
    dry_run_write_plan,
    redact_event_payload,
    schema_for_event,
    sensitive_raw_value_output_count,
    validate_broker_lake_target,
)
from trading.oms import (
    OmsEvent,
    OrderState,
    apply_risk_result,
    create_order_intent,
    order_intent_to_broker_lake_event,
    state_transition_to_broker_lake_event,
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
        "execution_price_policy": ADJUSTMENT_POLICY_RAW,
    }
    metadata.update(overrides)
    return metadata


def _run_context(**overrides: object) -> dict[str, object]:
    context: dict[str, object] = {
        "strategy_id": "strategy-alpha",
        "run_id": "run-cr015-s05",
        "risk_profile_id": "risk-profile-shadow",
    }
    context.update(overrides)
    return context


def _intent_event() -> dict[str, object]:
    created = create_order_intent(_target_row(), _policy(), _run_context(), now=NOW)
    assert created.ok
    assert created.intent is not None
    return order_intent_to_broker_lake_event(created.intent)


def test_broker_lake_schema_covers_eight_event_types() -> None:
    summary = build_schema_audit_summary()

    assert summary["schema_version"] == BROKER_LAKE_SCHEMA_VERSION
    assert summary["event_type_count"] == 8
    assert set(summary["event_types"]) == {
        "order_intent",
        "broker_order",
        "fill",
        "position",
        "asset",
        "error",
        "reconciliation",
        "incident",
    }

    schemas = summary["schemas"]
    assert isinstance(schemas, dict)
    for event_type in BrokerLakeEventType:
        schema = schema_for_event(event_type)
        assert BROKER_LAKE_SCHEMAS[event_type] == schema
        assert schema.schema_version == BROKER_LAKE_SCHEMA_VERSION
        assert schema.required_fields
        assert schema.partition_keys
        assert schema.retention_policy
        assert schema.redaction_status == "required"
        schema_summary = schemas[event_type.value]
        assert schema_summary["schema_version"] == BROKER_LAKE_SCHEMA_VERSION
        assert schema_summary["required_fields"] == schema.required_fields
        assert schema_summary["partition_keys"] == schema.partition_keys


def test_dry_run_write_plan_uses_no_open_mkdir_or_write(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = {"open": 0, "mkdir": 0, "write_text": 0}

    def fail_open(*args: object, **kwargs: object) -> object:
        calls["open"] += 1
        raise AssertionError("dry_run_write_plan must not open files")

    def fail_mkdir(*args: object, **kwargs: object) -> object:
        calls["mkdir"] += 1
        raise AssertionError("dry_run_write_plan must not mkdir")

    def fail_write_text(*args: object, **kwargs: object) -> object:
        calls["write_text"] += 1
        raise AssertionError("dry_run_write_plan must not write files")

    monkeypatch.setattr(builtins, "open", fail_open)
    monkeypatch.setattr(Path, "mkdir", fail_mkdir)
    monkeypatch.setattr(Path, "write_text", fail_write_text)

    plan = dry_run_write_plan(
        _intent_event(),
        root_label="BROKER_LAKE_ROOT",
        retention_policy="3y",
    )

    assert plan.status is BrokerLakePlanStatus.PLANNED
    assert not plan.blocked
    assert plan.real_write is False
    assert plan.event_type == BrokerLakeEventType.ORDER_INTENT.value
    assert plan.schema_version == BROKER_LAKE_SCHEMA_VERSION
    assert plan.root_label == "BROKER_LAKE_ROOT"
    assert plan.partition == {"trade_date": "2026-05-29", "run_id": "run-cr015-s05"}
    assert plan.retention_policy == "3y"
    assert plan.redaction_status is RedactionStatus.PASS
    assert plan.target_path_preview.startswith("<BROKER_LAKE_ROOT>::event_type=order_intent::")
    assert calls == {"open": 0, "mkdir": 0, "write_text": 0}
    assert plan.safety_counters["open_write_call"] == 0
    assert plan.safety_counters["real_broker_lake_write"] == 0


def test_forbidden_repository_targets_are_blocked_without_raw_path_preview() -> None:
    event = _intent_event()

    data_target = dry_run_write_plan(event, root_label="data/broker_lake")
    assert data_target.status is BrokerLakePlanStatus.BLOCKED
    assert data_target.target_path_preview == "<blocked-target>"
    assert data_target.root_label == "<blocked-root-label>"
    assert "data/broker_lake" not in repr(data_target)
    assert {
        error.error_code for error in data_target.errors
    } >= {BrokerLakeErrorCode.ROOT_LABEL_NOT_A_LABEL}

    reports_target = validate_broker_lake_target(
        "BROKER_LAKE_ROOT",
        target_path="reports/broker_lake",
    )
    assert not reports_target.allowed
    assert reports_target.target_path_preview == "<blocked-target>"
    assert reports_target.error is not None
    assert reports_target.error.error_code is BrokerLakeErrorCode.FORBIDDEN_TARGET
    assert "reports/broker_lake" not in repr(reports_target)


def test_redaction_gate_redacts_sensitive_payload_values_and_outputs_zero_raw_values() -> None:
    sensitive_values = [
        "fixture-token-value",
        "fixture-password-value",
        "fixture-session-cookie",
        "6222000000000000",
        "/home/test-user/private/broker_lake_root",
    ]
    payload = {
        **_intent_event(),
        "token_value": sensitive_values[0],
        "password_hint": sensitive_values[1],
        "session_cookie": sensitive_values[2],
        "account_id": sensitive_values[3],
        "audit_note": sensitive_values[4],
    }

    redaction = redact_event_payload(payload)
    assert redaction.redaction_status is RedactionStatus.REDACTED
    assert redaction.sanitized_payload["token_value"] == REDACTED_VALUE
    assert redaction.sanitized_payload["password_hint"] == REDACTED_VALUE
    assert redaction.sanitized_payload["session_cookie"] == REDACTED_VALUE
    assert redaction.sanitized_payload["account_id"] == REDACTED_VALUE
    assert redaction.sanitized_payload["audit_note"] == REDACTED_VALUE
    assert sensitive_raw_value_output_count(redaction, sensitive_values) == 0

    plan = dry_run_write_plan(payload, root_label="BROKER_LAKE_ROOT")
    assert plan.status is BrokerLakePlanStatus.PLANNED
    assert plan.redaction_status is RedactionStatus.REDACTED
    assert plan.sanitized_event["account_id"] == REDACTED_VALUE
    assert sensitive_raw_value_output_count(plan, sensitive_values) == 0
    assert plan.safety_counters["sensitive_raw_value_output"] == 0


def test_unknown_event_type_blocks_with_structured_error() -> None:
    with pytest.raises(ValueError, match=BrokerLakeErrorCode.UNKNOWN_EVENT_TYPE.value):
        schema_for_event("unknown")

    plan = dry_run_write_plan(
        {
            "event_type": "unknown",
            "strategy_id": "strategy-alpha",
            "run_id": "run-cr015-s05",
            "trade_date": "2026-05-29",
        },
        root_label="BROKER_LAKE_ROOT",
    )

    assert plan.status is BrokerLakePlanStatus.BLOCKED
    assert plan.real_write is False
    assert plan.errors
    assert plan.errors[0].error_code is BrokerLakeErrorCode.UNKNOWN_EVENT_TYPE
    assert plan.safety_counters["real_broker_lake_write"] == 0


def test_oms_s05_event_dicts_feed_broker_lake_without_state_semantic_change() -> None:
    created = create_order_intent(_target_row(), _policy(), _run_context(), now=NOW)
    assert created.ok
    assert created.intent is not None
    assert created.intent.state is OrderState.CREATED

    intent_event = order_intent_to_broker_lake_event(created.intent)
    intent_plan = dry_run_write_plan(intent_event, root_label="BROKER_LAKE_ROOT")
    assert intent_plan.status is BrokerLakePlanStatus.PLANNED
    assert intent_plan.event_type == BrokerLakeEventType.ORDER_INTENT.value

    risk_passed = apply_risk_result(created.intent, {"status": "pass"}, now=NOW)
    assert risk_passed.ok
    assert risk_passed.intent is not None
    assert risk_passed.transition_event is not None
    assert risk_passed.intent.state is OrderState.RISK_PASSED
    assert risk_passed.transition_event.event is OmsEvent.RISK_PASS

    transition_event = state_transition_to_broker_lake_event(
        risk_passed.intent,
        risk_passed.transition_event,
    )
    transition_plan = dry_run_write_plan(
        transition_event,
        root_label="BROKER_LAKE_ROOT",
    )

    assert transition_plan.status is BrokerLakePlanStatus.PLANNED
    assert transition_plan.event_type == BrokerLakeEventType.BROKER_ORDER.value
    assert transition_plan.sanitized_event["broker_order_status"] == "risk_passed"
    assert transition_plan.sanitized_event["oms_event"] == "risk_pass"
    assert transition_plan.partition == {
        "trade_date": "2026-05-29",
        "run_id": "run-cr015-s05",
    }


def test_broker_lake_safety_counters_keep_all_forbidden_operations_at_zero() -> None:
    counters = broker_lake_safety_counters()
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
        "open_write_call": 0,
        "sensitive_raw_value_output": 0,
    }
    assert {key: counters.get(key) for key in expected} == expected
