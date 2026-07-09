from __future__ import annotations

from engine.strategy_type_adapters import (
    ADAPTER_STATUS_BLOCKED,
    ADAPTER_STATUS_PASS,
    AdapterTypedEvidenceRef,
    STRATEGY_TYPE_EVENT,
    STRATEGY_TYPE_ML,
    StrategyTypeAdapterCore,
    adapter_handoff_summary,
    build_adapter_evidence_refs,
    validate_adapter_evidence_refs,
    validate_event_adapter_extension,
    validate_ml_adapter_extension,
)


def _ref(prefix: str, name: str) -> dict[str, str]:
    return {"ref": f"artifact://fixture/cr158/{prefix}/{name}", "description": name}


def _core(strategy_type: str) -> StrategyTypeAdapterCore:
    prefix = strategy_type
    return StrategyTypeAdapterCore(
        adapter_id=f"{prefix}-adapter-fixture",
        strategy_type=strategy_type,
        input_refs=(_ref(prefix, "input"),),
        output_signal_refs=(_ref(prefix, "signal"),),
        evidence_refs=(_ref(prefix, "evidence"),),
        blocked_reason_refs=(),
        authorization_flags={
            "no_runtime": True,
            "no_feed": True,
            "no_training": True,
            "no_registry": True,
            "no_publish": True,
        },
        handoff_refs=(_ref(prefix, "handoff"),),
    )


def _event_extension() -> dict[str, object]:
    return {
        "event_source_ref": _ref("event", "source"),
        "event_time_ref": _ref("event", "time"),
        "payload_schema_ref": _ref("event", "payload-schema"),
        "alignment_policy_ref": _ref("event", "alignment"),
        "signal_output_ref": _ref("event", "signal-output"),
        "blocked_reason_refs": (),
    }


def _ml_extension() -> dict[str, object]:
    return {
        "training_snapshot_ref": _ref("ml", "training-snapshot"),
        "feature_set_ref": _ref("ml", "feature-set"),
        "label_policy_ref": _ref("ml", "label-policy"),
        "model_artifact_ref": _ref("ml", "model-artifact"),
        "validation_report_ref": _ref("ml", "validation-report"),
        "prediction_signal_ref": _ref("ml", "prediction-signal"),
        "blocked_reason_refs": (),
    }


def test_cr158_s04_builds_event_and_ml_evidence_refs_without_body_copy() -> None:
    event_result = validate_event_adapter_extension(_core(STRATEGY_TYPE_EVENT), _event_extension())
    ml_result = validate_ml_adapter_extension(_core(STRATEGY_TYPE_ML), _ml_extension())

    refs = build_adapter_evidence_refs((event_result, ml_result))
    validation = validate_adapter_evidence_refs(refs)

    assert validation.to_dict()["status"] == ADAPTER_STATUS_PASS
    assert {ref.kind for ref in refs} == {"event_adapter", "ml_adapter"}
    assert all(ref.body_copy_count == 0 for ref in refs)
    assert all(ref.private_payload_included is False for ref in refs)


def test_cr158_s04_body_copy_attempt_blocks_evidence_ref_validation() -> None:
    refs = (
        AdapterTypedEvidenceRef(
            ref_id="event-adapter-fixture:event:evidence:1",
            kind="event_adapter",
            path_or_id="artifact://fixture/cr158/event/report",
            status=ADAPTER_STATUS_PASS,
            body_copy_count=1,
        ),
    )

    result = validate_adapter_evidence_refs(refs)

    assert result.to_dict()["status"] == ADAPTER_STATUS_BLOCKED
    assert any(reason["field"] == "body_copy_count" for reason in result.to_dict()["blocked_reasons"])


def test_cr158_s04_handoff_summary_hides_private_payload_surface() -> None:
    event_result = validate_event_adapter_extension(_core(STRATEGY_TYPE_EVENT), _event_extension())
    refs = build_adapter_evidence_refs((event_result,))

    summary = adapter_handoff_summary(_core(STRATEGY_TYPE_EVENT), refs)

    assert summary["status"] == ADAPTER_STATUS_PASS
    assert "event_payload_body" not in summary
    assert "model_binary" not in summary
    assert summary["evidence_refs"][0]["body_copy_count"] == 0
    assert summary["handoff_refs"]
