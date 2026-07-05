from __future__ import annotations

from engine.strategy_type_adapters import (
    ADAPTER_NO_RUNTIME_LIMITATIONS,
    ADAPTER_STATUS_BLOCKED,
    ADAPTER_STATUS_PASS,
    CR158_FORBIDDEN_OPERATION_COUNTERS,
    adapter_no_runtime_summary,
    validate_adapter_operation_counters,
    zero_adapter_operation_counts,
)


def test_cr158_s05_zero_operation_counters_pass_and_include_all_names() -> None:
    counters = zero_adapter_operation_counts()

    result = validate_adapter_operation_counters(counters)

    assert result.to_dict()["status"] == ADAPTER_STATUS_PASS
    assert set(CR158_FORBIDDEN_OPERATION_COUNTERS) == set(result.to_dict()["operation_counts"])
    assert all(value == 0 for value in result.to_dict()["operation_counts"].values())


def test_cr158_s05_single_nonzero_feed_counter_blocks_with_unlock_condition() -> None:
    counters = zero_adapter_operation_counts()
    counters["real_event_feed"] = 1

    result = validate_adapter_operation_counters(counters)
    reasons = result.to_dict()["blocked_reasons"]

    assert result.to_dict()["status"] == ADAPTER_STATUS_BLOCKED
    assert any(reason["field"] == "real_event_feed" for reason in reasons)
    assert all("runtime_authorization" in reason["unlock_condition"] for reason in reasons)


def test_cr158_s05_single_nonzero_registry_counter_blocks() -> None:
    counters = zero_adapter_operation_counts()
    counters["model_registry_write"] = 1

    summary = adapter_no_runtime_summary(counters)

    assert summary["status"] == ADAPTER_STATUS_BLOCKED
    assert summary["nonzero_counters"] == {"model_registry_write": 1}
    assert summary["nonzero_counter_count"] == 1


def test_cr158_s05_counter_family_coverage_and_limitations_are_explicit() -> None:
    assert len(CR158_FORBIDDEN_OPERATION_COUNTERS) >= 12
    assert "real_event_feed" in CR158_FORBIDDEN_OPERATION_COUNTERS
    assert "real_model_training" in CR158_FORBIDDEN_OPERATION_COUNTERS
    assert "model_registry_write" in CR158_FORBIDDEN_OPERATION_COUNTERS
    assert "trading_operation" in CR158_FORBIDDEN_OPERATION_COUNTERS
    assert "git_remote_write" in CR158_FORBIDDEN_OPERATION_COUNTERS
    assert "no_real_event_feed" in ADAPTER_NO_RUNTIME_LIMITATIONS
    assert "no_real_model_training" in ADAPTER_NO_RUNTIME_LIMITATIONS
    assert "no_catalog_store_registry_or_publish" in ADAPTER_NO_RUNTIME_LIMITATIONS
