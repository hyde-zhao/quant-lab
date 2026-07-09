from __future__ import annotations

from engine.strategy_type_adapters import (
    ADAPTER_STATUS_BLOCKED,
    ADAPTER_STATUS_PASS,
    CORE_REQUIRED_FIELD_GROUPS,
    STRATEGY_TYPE_EVENT,
    StrategyTypeAdapterCore,
    validate_strategy_type_adapter_core,
    zero_adapter_operation_counts,
)


def _ref(name: str) -> dict[str, str]:
    return {"ref": f"artifact://fixture/cr158/{name}", "description": name}


def _event_core(**overrides: object) -> StrategyTypeAdapterCore:
    payload = {
        "adapter_id": "event-adapter-fixture",
        "strategy_type": STRATEGY_TYPE_EVENT,
        "input_refs": (_ref("event-input"),),
        "output_signal_refs": (_ref("event-signal"),),
        "evidence_refs": (_ref("event-evidence"),),
        "blocked_reason_refs": (),
        "authorization_flags": {
            "no_runtime": True,
            "no_feed": True,
            "no_training": True,
            "no_registry": True,
            "no_publish": True,
        },
        "handoff_refs": (_ref("event-handoff"),),
    }
    payload.update(overrides)
    return StrategyTypeAdapterCore(**payload)


def _codes(result) -> set[str]:
    return {reason["code"] for reason in result.to_dict()["blocked_reasons"]}


def test_cr158_s01_core_contract_passes_complete_static_fixture() -> None:
    result = validate_strategy_type_adapter_core(_event_core())
    payload = result.to_dict()

    assert result.passed is True
    assert payload["status"] == ADAPTER_STATUS_PASS
    assert payload["strategy_type"] == STRATEGY_TYPE_EVENT
    assert all(value == 0 for value in payload["operation_counts"].values())
    assert set(CORE_REQUIRED_FIELD_GROUPS) <= set(_event_core().to_dict())


def test_cr158_s01_missing_shared_ref_group_blocks() -> None:
    core_payload = _event_core().to_dict()
    core_payload.pop("handoff_refs")

    result = validate_strategy_type_adapter_core(core_payload)

    assert result.to_dict()["status"] == ADAPTER_STATUS_BLOCKED
    assert "adapter_core_required_field_missing" in _codes(result)


def test_cr158_s01_event_private_key_leakage_in_core_blocks() -> None:
    core_payload = _event_core().to_dict()
    core_payload["event_payload_schema_ref"] = _ref("private-event-schema")

    result = validate_strategy_type_adapter_core(core_payload)

    assert result.to_dict()["status"] == ADAPTER_STATUS_BLOCKED
    assert any(reason["field"] == "event_payload_schema_ref" for reason in result.to_dict()["blocked_reasons"])


def test_cr158_s01_ml_private_key_leakage_in_core_blocks() -> None:
    core_payload = _event_core().to_dict()
    core_payload["model_artifact_ref"] = _ref("private-model-artifact")

    result = validate_strategy_type_adapter_core(core_payload)

    assert result.to_dict()["status"] == ADAPTER_STATUS_BLOCKED
    assert any(reason["field"] == "model_artifact_ref" for reason in result.to_dict()["blocked_reasons"])


def test_cr158_s01_nonzero_forbidden_counter_blocks_static_fixture() -> None:
    counters = zero_adapter_operation_counts()
    counters["real_event_feed"] = 1

    result = validate_strategy_type_adapter_core(_event_core(), operation_counts=counters)

    assert result.to_dict()["status"] == ADAPTER_STATUS_BLOCKED
    assert any(reason["field"] == "real_event_feed" for reason in result.to_dict()["blocked_reasons"])
