from __future__ import annotations

import json

from engine.factor_panel_contracts import (
    MF_ADJUSTMENT_POLICY_MIXED,
    MF_AVAILABLE_AT_VIOLATION,
    MF_EXTERNAL_PIT_LABEL_TRUTH_FORBIDDEN,
    MF_FORBIDDEN_PERMISSION_COUNTER,
    MF_LABEL_OVERLAP_RISK,
    MF_LINEAGE_MISSING,
    MF_PANEL_LAYER_INCOMPLETE,
    MF_QUALITY_GATE_FAILED,
    FactorPanelContract,
    LabelWindowSpec,
    PanelGateResult,
    assert_no_external_pit_label_truth,
    combine_panel_label_gate,
    to_blocked_claims,
    validate_factor_panel,
    validate_label_window,
)
from engine.multifactor_contracts import (
    FactorRunSpec,
    PermissionCounters,
    compute_config_hash,
)


def _reason_codes(result: PanelGateResult) -> set[str]:
    return {reason.code for reason in result.blocked_reasons}


def _valid_run_spec(**overrides: object) -> FactorRunSpec:
    base = {
        "run_id": "run-cr030-s03-fixture",
        "factor_id": "momentum_20d",
        "factor_version": "v1",
        "date_range": {"start": "2020-01-01", "end": "2024-12-31"},
        "dataset_release": "research_input_v1_fixture_release",
        "benchmark": {"benchmark_id": "hs300", "policy": "hs300_required"},
        "label_window": {
            "horizon": 5,
            "return_kind": "forward_return",
            "adjustment_policy": "qfq",
        },
        "cost_config": {"cost_policy": "research_cost_v1", "commission_bps": 3, "slippage_bps": 5},
        "seed": 42,
        "code_version": "cr030-s03-fixture",
        "config_hash": "",
        "output_root": "reports/cr030_s03_fixture",
        "permission_counters": PermissionCounters(),
        "failure_policy": "fail_closed",
        "strategy_id": "strategy-cr030-s03-fixture",
        "experiment_group": "cr030-s03",
        "combination_config": {"weighting_policy": "single_factor"},
    }
    base.update(overrides)
    base["config_hash"] = compute_config_hash({key: value for key, value in base.items() if key != "config_hash"})
    return FactorRunSpec(**base)


def _valid_lineage() -> dict[str, object]:
    return {
        "source_dataset": "research_input_v1",
        "research_input_schema": "research_input_v1",
        "dataset_release": "fixture-release",
        "evidence_refs": ["tests/fixtures/cr030_s03_factor_panel_fixture"],
    }


def _valid_panel(**overrides: object) -> FactorPanelContract:
    base = {
        "trade_date": "2024-01-03",
        "symbol": "000001.SZ",
        "factor_id": "momentum_20d",
        "factor_version": "v1",
        "raw_value": 0.12,
        "directional_value": 0.12,
        "winsorized_value": 0.11,
        "zscore_value": 0.78,
        "available_at": "2024-01-03T08:30:00",
        "decision_time": "2024-01-03T09:30:00",
        "source_dataset": "research_input_v1",
        "quality_status": "pass",
        "preprocessing_metadata": {
            "adjustment_policy": "qfq",
            "winsorize": [0.01, 0.99],
            "zscore": True,
        },
        "data_lineage": _valid_lineage(),
    }
    base.update(overrides)
    return FactorPanelContract(**base)


def _valid_label(**overrides: object) -> LabelWindowSpec:
    base = {
        "label_id": "forward_return_5d",
        "trade_date": "2024-01-03",
        "symbol": "000001.SZ",
        "decision_time": "2024-01-03T09:30:00",
        "label_window_start": "2024-01-04T09:30:00",
        "label_window_end": "2024-01-10T15:00:00",
        "label_available_at": "2024-01-10T16:00:00",
        "return_kind": "forward_return",
        "adjustment_policy": "qfq",
        "cost_policy": "research_cost_v1",
        "benchmark_policy": "hs300_required",
        "data_lineage": _valid_lineage(),
    }
    base.update(overrides)
    return LabelWindowSpec(**base)


def test_ts_s03_01_available_at_lookahead_blocks_all_downstream() -> None:
    result = validate_factor_panel(
        _valid_panel(available_at="2024-01-03T10:00:00"),
        _valid_run_spec(),
    )

    assert result.status == "blocked"
    assert MF_AVAILABLE_AT_VIOLATION in _reason_codes(result)
    assert result.downstream_allowed.evaluation is False
    assert result.downstream_allowed.combo is False
    assert result.downstream_allowed.admission is False


def test_ts_s03_02_label_overlap_blocks_all_downstream() -> None:
    result = validate_label_window(
        _valid_label(label_window_start="2024-01-03T09:30:00"),
        _valid_run_spec(),
    )

    assert result.status == "blocked"
    assert MF_LABEL_OVERLAP_RISK in _reason_codes(result)
    assert result.downstream_allowed.evaluation is False
    assert result.downstream_allowed.combo is False
    assert result.downstream_allowed.admission is False


def test_ts_s03_03_panel_layer_missing_fails_closed() -> None:
    panel = _valid_panel().to_dict()
    panel.pop("zscore_value")

    result = validate_factor_panel(panel, _valid_run_spec())

    assert result.status == "blocked"
    assert MF_PANEL_LAYER_INCOMPLETE in _reason_codes(result)


def test_ts_s03_04_lineage_quality_and_adjustment_policy_fail_closed() -> None:
    missing_lineage = _valid_panel(data_lineage={"source_dataset": "research_input_v1"})
    result = validate_factor_panel(missing_lineage, _valid_run_spec())
    assert result.status == "blocked"
    assert MF_LINEAGE_MISSING in _reason_codes(result)

    quality_failed = _valid_panel(quality_status="failed")
    result = validate_factor_panel(quality_failed, _valid_run_spec())
    assert result.status == "blocked"
    assert MF_QUALITY_GATE_FAILED in _reason_codes(result)

    mixed_panel = _valid_panel(
        preprocessing_metadata={
            "adjustment_policy": "qfq",
            "adjustment_policy_set": ["qfq", "hfq"],
        }
    )
    result = validate_factor_panel(mixed_panel, _valid_run_spec())
    assert result.status == "blocked"
    assert MF_ADJUSTMENT_POLICY_MIXED in _reason_codes(result)

    mixed_label = _valid_label(adjustment_policy="hfq")
    result = validate_label_window(mixed_label, _valid_run_spec())
    assert result.status == "blocked"
    assert MF_ADJUSTMENT_POLICY_MIXED in _reason_codes(result)


def test_ts_s03_05_combined_gate_and_blocked_claims_keep_continue_count_zero() -> None:
    panel_result = validate_factor_panel(
        _valid_panel(available_at="2024-01-03T10:00:00"),
        _valid_run_spec(),
    )
    label_result = validate_label_window(_valid_label(), _valid_run_spec())

    combined = combine_panel_label_gate(panel_result, label_result)
    claims = to_blocked_claims(combined)

    assert label_result.status == "pass"
    assert combined.status == "blocked"
    assert combined.downstream_allowed.to_dict() == {
        "evaluation": False,
        "combo": False,
        "admission": False,
    }
    assert len(claims) == len(combined.blocked_reasons)
    assert claims[0]["code"] == MF_AVAILABLE_AT_VIOLATION
    assert claims[0]["downstream_allowed"]["evaluation"] is False
    assert sum(int(allowed) for allowed in combined.downstream_allowed.to_dict().values()) == 0
    json.dumps(combined.to_dict(), sort_keys=True)
    json.dumps(claims, sort_keys=True)


def test_ts_s03_06_external_truth_and_forbidden_permission_counters_are_blocked() -> None:
    external_result = assert_no_external_pit_label_truth(
        {
            "source_id": "qlib-alpha158",
            "source_of_truth": "Qlib provider_uri external PIT label truth",
        }
    )

    assert external_result.status == "blocked"
    assert MF_EXTERNAL_PIT_LABEL_TRUTH_FORBIDDEN in _reason_codes(external_result)
    assert external_result.downstream_allowed.to_dict() == {
        "evaluation": False,
        "combo": False,
        "admission": False,
    }

    run_spec = _valid_run_spec(
        permission_counters=PermissionCounters(
            provider_fetch=1,
            lake_write=1,
            credential_read=1,
            qmt_operation=1,
        )
    )
    result = validate_factor_panel(_valid_panel(), run_spec)

    assert result.status == "blocked"
    assert MF_FORBIDDEN_PERMISSION_COUNTER in _reason_codes(result)
    assert result.permission_counters["provider_fetch"] == 1
    assert result.permission_counters["lake_write"] == 1
    assert result.permission_counters["credential_read"] == 1
    assert result.permission_counters["qmt_operation"] == 1
