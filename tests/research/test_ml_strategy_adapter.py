from __future__ import annotations

from engine.strategy_type_adapters import (
    ADAPTER_STATUS_BLOCKED,
    ADAPTER_STATUS_PASS,
    MLAdapterExtension,
    STRATEGY_TYPE_ML,
    StrategyTypeAdapterCore,
    validate_ml_adapter_extension,
    zero_adapter_operation_counts,
)


def _ref(name: str) -> dict[str, str]:
    return {"ref": f"artifact://fixture/cr158/ml/{name}", "description": name}


def _core() -> StrategyTypeAdapterCore:
    return StrategyTypeAdapterCore(
        adapter_id="ml-adapter-fixture",
        strategy_type=STRATEGY_TYPE_ML,
        input_refs=(_ref("input"),),
        output_signal_refs=(_ref("prediction-signal"),),
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
        "training_snapshot_ref": _ref("training-snapshot"),
        "feature_set_ref": _ref("feature-set"),
        "label_policy_ref": _ref("label-policy"),
        "model_artifact_ref": _ref("model-artifact"),
        "validation_report_ref": _ref("validation-report"),
        "prediction_signal_ref": _ref("prediction-signal"),
        "blocked_reason_refs": (),
    }
    payload.update(overrides)
    return payload


def test_cr158_s03_ml_extension_passes_complete_static_fixture() -> None:
    result = validate_ml_adapter_extension(_core(), MLAdapterExtension(**_extension()))
    payload = result.to_dict()

    assert payload["status"] == ADAPTER_STATUS_PASS
    assert payload["strategy_type"] == STRATEGY_TYPE_ML
    assert len(payload["evidence_refs"]) >= 6
    assert all(value == 0 for value in payload["operation_counts"].values())


def test_cr158_s03_missing_validation_report_blocks() -> None:
    extension = _extension(validation_report_ref={})

    result = validate_ml_adapter_extension(_core(), extension)

    assert result.to_dict()["status"] == ADAPTER_STATUS_BLOCKED
    assert any(reason["field"] == "validation_report_ref" for reason in result.to_dict()["blocked_reasons"])


def test_cr158_s03_model_registry_counter_blocks() -> None:
    counters = zero_adapter_operation_counts()
    counters["model_registry_write"] = 1

    result = validate_ml_adapter_extension(_core(), _extension(), operation_counts=counters)

    assert result.to_dict()["status"] == ADAPTER_STATUS_BLOCKED
    assert any(reason["field"] == "model_registry_write" for reason in result.to_dict()["blocked_reasons"])


def test_cr158_s03_event_private_field_in_ml_extension_blocks() -> None:
    extension = _extension(event_source_ref=_ref("event-source"))

    result = validate_ml_adapter_extension(_core(), extension)

    assert result.to_dict()["status"] == ADAPTER_STATUS_BLOCKED
    assert any(reason["field"] == "event_source_ref" for reason in result.to_dict()["blocked_reasons"])
