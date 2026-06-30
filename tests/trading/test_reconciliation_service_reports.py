from __future__ import annotations

import builtins
import json
from pathlib import Path

import pytest

from trading.reconciliation import (
    RECONCILIATION_SCHEMA_VERSION,
    RECON_DIMENSIONS,
    DiffRow,
    ReconPhase,
    ReconciliationErrorCode,
    ReconciliationInput,
    ReconciliationStatus,
    ThresholdConfig,
    build_report_candidate,
    evaluate_thresholds,
    reconcile,
    reconciliation_safety_counters,
    sensitive_raw_value_output_count,
    to_kill_switch_candidate,
)


REQUIRED_ZERO_COUNTERS = {
    "qmt_api_call",
    "real_order_call",
    "real_cancel_call",
    "account_query_call",
    "account_write_call",
    "credential_read",
    "real_broker_lake_write",
    "real_lake_write",
    "provider_fetch",
    "publish",
    "dependency_change",
    "simulation_run",
    "real_snapshot_pull",
    "old_report_overwrite",
    "continue_order_allowed_after_threshold_breach",
    "sensitive_raw_value_output",
}


def _thresholds(**overrides: object) -> ThresholdConfig:
    warn = {dimension: 0.1 for dimension in RECON_DIMENSIONS}
    manual = {dimension: 2.0 for dimension in RECON_DIMENSIONS}
    kill = {dimension: 10.0 for dimension in RECON_DIMENSIONS}
    for dimension, value in overrides.get("warn", {}).items():  # type: ignore[union-attr]
        warn[str(dimension)] = float(value)
    for dimension, value in overrides.get("manual_review", {}).items():  # type: ignore[union-attr]
        manual[str(dimension)] = float(value)
    for dimension, value in overrides.get("kill_switch", {}).items():  # type: ignore[union-attr]
        kill[str(dimension)] = float(value)
    return ThresholdConfig(
        warn=warn,
        manual_review=manual,
        kill_switch=kill,
    )


def _local_state(**overrides: object) -> dict[str, object]:
    state: dict[str, object] = {
        "orders": {"count": 1, "ref": "local:orders"},
        "fills": {"count": 1, "ref": "local:fills"},
        "positions": {"count": 10, "symbol": "000001.SZ", "ref": "local:positions"},
        "assets": {"value": 1000.0, "ref": "local:assets"},
        "cash": {"value": 100.0, "ref": "local:cash"},
        "broker_lake_facts": {"count": 6, "ref": "local:broker-lake-facts"},
    }
    state.update(overrides)
    return state


def _broker_facts(**overrides: object) -> dict[str, object]:
    facts: dict[str, object] = {
        "orders": {"count": 1, "ref": "broker:orders"},
        "fills": {"count": 1, "ref": "broker:fills"},
        "positions": {"count": 10, "symbol": "000001.SZ", "ref": "broker:positions"},
        "assets": {"value": 1000.0, "ref": "broker:assets"},
        "cash": {"value": 100.0, "ref": "broker:cash"},
    }
    facts.update(overrides)
    return facts


def _broker_lake_facts(**overrides: object) -> dict[str, object]:
    facts: dict[str, object] = {"count": 6, "ref": "broker-lake:facts"}
    facts.update(overrides)
    return facts


def _input(
    phase: ReconPhase | str,
    *,
    local_state: dict[str, object] | None = None,
    broker_facts: dict[str, object] | None = None,
    broker_lake_facts: dict[str, object] | None = None,
    threshold_config: ThresholdConfig | None = None,
) -> ReconciliationInput:
    return ReconciliationInput(
        phase=phase,
        local_state_ref="fixture:local-state",
        broker_snapshot_ref="fixture:broker-snapshot",
        broker_lake_ref="BROKER_LAKE_ROOT_LABEL",
        local_state=local_state if local_state is not None else _local_state(),
        broker_facts=broker_facts if broker_facts is not None else _broker_facts(),
        broker_lake_facts=(
            broker_lake_facts if broker_lake_facts is not None else _broker_lake_facts()
        ),
        threshold_config=threshold_config if threshold_config is not None else _thresholds(),
        owner="ops",
        action="none",
        input_source="fixture",
        report_label="simulation-recon",
    )


def _assert_zero_counters(counters: object) -> None:
    current = dict(counters)  # type: ignore[arg-type]
    assert {key: current.get(key) for key in REQUIRED_ZERO_COUNTERS} == {
        key: 0 for key in REQUIRED_ZERO_COUNTERS
    }


@pytest.mark.parametrize("phase", list(ReconPhase))
def test_reconcile_supports_three_phases_with_pass_report(phase: ReconPhase) -> None:
    report = reconcile(_input(phase))

    assert report.schema_version == RECONCILIATION_SCHEMA_VERSION
    assert report.phase is phase
    assert report.status is ReconciliationStatus.PASS
    assert report.broker_snapshot_ref == "fixture:broker-snapshot"
    assert report.local_state_ref == "fixture:local-state"
    assert report.broker_lake_ref == "BROKER_LAKE_ROOT_LABEL"
    assert {row.diff_type for row in report.diff_rows} == set(RECON_DIMENSIONS)
    assert report.thresholds.keys() == set(RECON_DIMENSIONS)
    assert report.owner == "ops"
    assert report.action == "none"
    assert report.redaction_status == "pass"
    assert report.new_order_allowed is True
    assert report.continue_order_allowed_count == 0
    _assert_zero_counters(report.safety_counters)


def test_threshold_evaluator_maps_warn_without_blocking_new_orders() -> None:
    evaluation = evaluate_thresholds(
        (
            DiffRow(
                diff_type="orders",
                symbol="000001.SZ",
                local_value_ref="local:orders",
                broker_value_ref="broker:orders",
                diff_value=1.0,
            ),
        ),
        _thresholds(
            warn={"orders": 0.1},
            manual_review={"orders": 2.0},
            kill_switch={"orders": 10.0},
        ),
    )

    assert evaluation == "warn"
    assert evaluation.status is ReconciliationStatus.WARN
    assert evaluation.diff_rows[0].status is ReconciliationStatus.WARN
    assert evaluation.new_order_allowed is True
    assert evaluation.continue_order_allowed_count == 0


def test_intraday_manual_review_blocks_new_orders_and_continue_count() -> None:
    report = reconcile(
        _input(
            ReconPhase.INTRADAY,
            broker_facts=_broker_facts(
                positions={
                    "count": 13,
                    "symbol": "000001.SZ",
                    "ref": "broker:positions:manual-review",
                }
            ),
            threshold_config=_thresholds(
                warn={"positions": 0.1},
                manual_review={"positions": 2.0},
                kill_switch={"positions": 10.0},
            ),
        )
    )

    assert report.status is ReconciliationStatus.MANUAL_REVIEW
    assert report.action == "manual_review"
    assert report.new_order_allowed is False
    assert report.continue_order_allowed_count == 0
    assert report.error_code is None

    candidate = to_kill_switch_candidate(report)
    assert candidate["trigger_required"] is True
    assert candidate["trigger_status"] == "manual_review"
    assert candidate["action"] == "manual_review"
    assert candidate["new_order_allowed"] is False
    assert candidate["continue_order_allowed_count"] == 0
    _assert_zero_counters(candidate["safety_counters"])


def test_post_market_kill_switch_candidate_blocks_all_new_order_continuation() -> None:
    report = reconcile(
        _input(
            ReconPhase.POST_MARKET,
            broker_facts=_broker_facts(cash={"value": 500.0, "ref": "broker:cash:kill"}),
            threshold_config=_thresholds(
                warn={"cash": 10.0},
                manual_review={"cash": 100.0},
                kill_switch={"cash": 200.0},
            ),
        )
    )

    assert report.status is ReconciliationStatus.KILL_SWITCH
    assert report.action == "trigger_kill_switch"
    assert report.new_order_allowed is False
    assert report.continue_order_allowed_count == 0

    candidate = to_kill_switch_candidate(report)
    assert candidate["trigger_required"] is True
    assert candidate["trigger_status"] == "kill_switch"
    assert candidate["action"] == "trigger_kill_switch"
    assert candidate["incident_ref"].startswith("incident-candidate:")
    assert candidate["new_order_allowed"] is False
    assert candidate["continue_order_allowed_count"] == 0
    _assert_zero_counters(report.safety_counters)


def test_missing_broker_facts_returns_stable_required_missing_error() -> None:
    report = reconcile(
        ReconciliationInput(
            phase=ReconPhase.PRE_MARKET,
            local_state_ref="fixture:local-state",
            broker_snapshot_ref="",
            broker_lake_ref="BROKER_LAKE_ROOT_LABEL",
            local_state=_local_state(),
            broker_facts=None,
            broker_lake_facts=_broker_lake_facts(),
            threshold_config=_thresholds(),
        )
    )

    assert report.status is ReconciliationStatus.REQUIRED_MISSING
    assert report.error_code is ReconciliationErrorCode.BROKER_FACTS_REQUIRED_MISSING
    assert report.action == "provide_required_broker_facts"
    assert report.new_order_allowed is False
    assert report.continue_order_allowed_count == 0
    assert report.diff_rows == ()
    _assert_zero_counters(report.safety_counters)


def test_missing_thresholds_returns_stable_required_missing_error() -> None:
    report = reconcile(
        ReconciliationInput(
            phase=ReconPhase.PRE_MARKET,
            local_state_ref="fixture:local-state",
            broker_snapshot_ref="fixture:broker-snapshot",
            broker_lake_ref="BROKER_LAKE_ROOT_LABEL",
            local_state=_local_state(),
            broker_facts=_broker_facts(),
            broker_lake_facts=_broker_lake_facts(),
            threshold_config=None,
        )
    )

    assert report.status is ReconciliationStatus.REQUIRED_MISSING
    assert report.error_code is ReconciliationErrorCode.THRESHOLD_REQUIRED_MISSING
    assert report.action == "provide_required_input"
    assert report.new_order_allowed is False
    assert report.continue_order_allowed_count == 0
    assert all(row.status is ReconciliationStatus.REQUIRED_MISSING for row in report.diff_rows)
    _assert_zero_counters(report.safety_counters)


def test_report_candidate_is_versioned_and_does_not_write_or_overwrite_reports(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = {"open": 0, "mkdir": 0, "write_text": 0}

    def fail_open(*args: object, **kwargs: object) -> object:
        calls["open"] += 1
        raise AssertionError("build_report_candidate must not open files")

    def fail_mkdir(*args: object, **kwargs: object) -> object:
        calls["mkdir"] += 1
        raise AssertionError("build_report_candidate must not mkdir")

    def fail_write_text(*args: object, **kwargs: object) -> object:
        calls["write_text"] += 1
        raise AssertionError("build_report_candidate must not write files")

    monkeypatch.setattr(builtins, "open", fail_open)
    monkeypatch.setattr(Path, "mkdir", fail_mkdir)
    monkeypatch.setattr(Path, "write_text", fail_write_text)

    report = reconcile(_input(ReconPhase.PRE_MARKET))
    candidate = build_report_candidate(report)

    assert candidate["candidate_id"] == f"candidate:{report.report_id}"
    assert candidate["schema_version"] == RECONCILIATION_SCHEMA_VERSION
    assert candidate["storage_policy"] == "candidate_only_no_file_write"
    assert candidate["target_ref"] == f"candidate:{report.report_id}"
    assert candidate["old_report_overwrite"] is False
    assert candidate["reports_path"] == ""
    assert "reports/" not in json.dumps(candidate, sort_keys=True, default=str)
    assert calls == {"open": 0, "mkdir": 0, "write_text": 0}
    _assert_zero_counters(candidate["safety_counters"])


def test_sensitive_raw_values_are_not_rendered_and_real_operation_counts_stay_zero() -> None:
    sensitive_values = [
        "fixture-token-value",
        "fixture-password-value",
        "6222000000000000",
        "/home/test-user/private/broker-snapshot",
    ]
    report = reconcile(
        _input(
            ReconPhase.INTRADAY,
            local_state=_local_state(
                cash={
                    "value": 100.0,
                    "token_hint": sensitive_values[0],
                    "ref": "local:cash",
                }
            ),
            broker_facts=_broker_facts(
                cash={
                    "value": 100.0,
                    "password_hint": sensitive_values[1],
                    "account_id": sensitive_values[2],
                    "private_path": sensitive_values[3],
                    "ref": "broker:cash",
                }
            ),
        )
    )
    candidate = build_report_candidate(report)

    assert report.redaction_status == "redacted"
    assert sensitive_raw_value_output_count(report, sensitive_values) == 0
    assert sensitive_raw_value_output_count(candidate, sensitive_values) == 0
    _assert_zero_counters(report.safety_counters)
    _assert_zero_counters(reconciliation_safety_counters())
