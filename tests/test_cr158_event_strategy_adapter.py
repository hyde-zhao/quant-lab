from __future__ import annotations

from engine.strategy_type_adapters import (
    ADAPTER_STATUS_BLOCKED,
    ADAPTER_STATUS_PASS,
    EventAdapterExtension,
    STRATEGY_TYPE_EVENT,
    StrategyTypeAdapterCore,
    validate_event_adapter_extension,
    zero_adapter_operation_counts,
)


def _ref(name: str) -> dict[str, str]:
    return {"ref": f"artifact://fixture/cr158/event/{name}", "description": name}


def _core() -> StrategyTypeAdapterCore:
    return StrategyTypeAdapterCore(
        adapter_id="event-adapter-fixture",
        strategy_type=STRATEGY_TYPE_EVENT,
        input_refs=(_ref("input"),),
        output_signal_refs=(_ref("signal"),),
        evidence_refs=(_ref("evidence"),),
        blocked_reason_refs=(),
        authorization_flags={
            "no_runtime": True,
            "no_feed": True,
            "no_training": True,
            "no_registry": True,
            "no_publish": True,
        },
        handoff_refs=(_ref("handoff"),),
    )


def _extension(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "event_source_ref": _ref("source"),
        "event_time_ref": _ref("time"),
        "payload_schema_ref": _ref("payload-schema"),
        "alignment_policy_ref": _ref("alignment-policy"),
        "signal_output_ref": _ref("signal-output"),
        "blocked_reason_refs": (),
    }
    payload.update(overrides)
    return payload


def test_cr158_s02_event_extension_passes_complete_static_fixture() -> None:
    result = validate_event_adapter_extension(_core(), EventAdapterExtension(**_extension()))
    payload = result.to_dict()

    assert payload["status"] == ADAPTER_STATUS_PASS
    assert payload["strategy_type"] == STRATEGY_TYPE_EVENT
    assert len(payload["evidence_refs"]) >= 5
    assert all(value == 0 for value in payload["operation_counts"].values())


def test_cr158_s02_missing_alignment_policy_blocks() -> None:
    extension = _extension(alignment_policy_ref={})

    result = validate_event_adapter_extension(_core(), extension)

    assert result.to_dict()["status"] == ADAPTER_STATUS_BLOCKED
    assert any(reason["field"] == "alignment_policy_ref" for reason in result.to_dict()["blocked_reasons"])


def test_cr158_s02_live_listener_counter_blocks() -> None:
    counters = zero_adapter_operation_counts()
    counters["live_event_listener"] = 1

    result = validate_event_adapter_extension(_core(), _extension(), operation_counts=counters)

    assert result.to_dict()["status"] == ADAPTER_STATUS_BLOCKED
    assert any(reason["field"] == "live_event_listener" for reason in result.to_dict()["blocked_reasons"])


def test_cr158_s02_ml_private_field_in_event_extension_blocks() -> None:
    extension = _extension(model_artifact_ref=_ref("ml-model-artifact"))

    result = validate_event_adapter_extension(_core(), extension)

    assert result.to_dict()["status"] == ADAPTER_STATUS_BLOCKED
    assert any(reason["field"] == "model_artifact_ref" for reason in result.to_dict()["blocked_reasons"])
