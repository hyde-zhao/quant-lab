from __future__ import annotations

from engine.backtest_production_contracts import (
    BacktestFoundationAssetMap,
    Phase3ScopeGuard,
    build_backtest_cost_risk_attribution_pack,
    build_backtest_foundation_asset_map,
    build_backtest_report_pack,
    build_backtest_run_spec,
    validate_backtest_cost_risk_attribution_pack,
    validate_backtest_foundation_asset_map,
    validate_backtest_report_pack,
    validate_backtest_run_spec,
    validate_phase3_scope_guard,
)
from engine.backtest import BacktestConfig


def test_cr148_backtest_foundation_asset_map_covers_existing_assets_without_runtime() -> None:
    asset_map = build_backtest_foundation_asset_map()

    asset_ids = {asset.asset_id for asset in asset_map.assets}
    assert {
        "lightweight_backtest_engine",
        "mature_multifactor_framework",
        "experiment_manifest_registry",
        "strategy_admission_package",
        "backtest_report_row",
        "portfolio_and_metrics_core",
    }.issubset(asset_ids)
    assert asset_map.gap_count == 0
    assert asset_map.gate_required_gap_count == 0
    assert asset_map.scope_guard.phase3_exit_strategy_families == ("multifactor",)
    assert {"machine_learning", "event_driven"}.issubset(set(asset_map.scope_guard.deferred_strategy_families))
    assert all(value == 0 for value in asset_map.operation_counts.values())
    assert validate_backtest_foundation_asset_map(asset_map) == ()


def test_cr148_backtest_foundation_asset_map_validation_blocks_duplicate_ids() -> None:
    asset_map = build_backtest_foundation_asset_map()
    duplicated = BacktestFoundationAssetMap(
        assets=(asset_map.assets[0], asset_map.assets[0]),
        scope_guard=asset_map.scope_guard,
        operation_counts=asset_map.operation_counts,
    )

    codes = {issue["code"] for issue in validate_backtest_foundation_asset_map(duplicated)}
    assert "backtest_asset_id_duplicate" in codes


def test_cr148_phase3_scope_guard_blocks_ml_event_or_runtime_scope_creep() -> None:
    guard = Phase3ScopeGuard(
        baseline_scope="all_strategy_families",
        phase3_exit_strategy_families=("multifactor", "machine_learning", "event_driven"),
        deferred_strategy_families=("machine_learning",),
        deferred_runtime_capabilities=("broker_write",),
        nas_scope="nas_sync_allowed",
    )

    codes = {issue["code"] for issue in validate_phase3_scope_guard(guard)}
    assert "phase3_scope_baseline_invalid" in codes
    assert "phase3_exit_strategy_family_scope_invalid" in codes
    assert "phase3_deferred_strategy_family_missing" in codes
    assert "phase3_deferred_runtime_capability_missing" in codes
    assert "phase3_nas_scope_invalid" in codes


def test_cr148_backtest_foundation_asset_map_blocks_nonzero_operations() -> None:
    payload = build_backtest_foundation_asset_map().to_dict()
    payload["operation_counts"]["simulation_or_live"] = 1

    codes = {issue["code"] for issue in validate_backtest_foundation_asset_map(payload)}
    assert "backtest_asset_map_operation_counter_nonzero" in codes


def _run_spec(**overrides: object):
    payload = {
        "run_id": "bt-alpha-core-20260528-v1",
        "experiment_id": "exp-alpha-core-20260528",
        "strategy_id": "daily_multifactor_alpha_core",
        "dataset_snapshot_ref": "research-dataset-snapshot://snapshot-alpha-core-20260528-v1",
        "signal_set_ref": "signal-set://alpha-core/20260528",
        "portfolio_policy_ref": "portfolio-policy://equal-weight-top-decile/v1",
        "benchmark_ref": "benchmark://hs300/daily/v1",
        "cost_model_ref": "cost-model://cn-a-share-basic/v1",
        "slippage_model_ref": "slippage-model://close-proxy/v1",
        "start_date": "2020-01-01",
        "end_date": "2026-05-28",
        "as_of": "2026-05-28",
        "code_version": "test-tree",
        "backtest_config": BacktestConfig(lookback_days=20, rebalance_freq=5, top_fraction=0.1),
    }
    payload.update(overrides)
    return build_backtest_run_spec(**payload)  # type: ignore[arg-type]


def test_cr148_backtest_run_spec_is_stable_and_metadata_only() -> None:
    first = _run_spec()
    second = _run_spec()

    assert first.config_hash == second.config_hash
    assert first.config_hash.startswith("sha256:")
    assert first.backtest_engine == "lightweight"
    assert first.frequency == "daily"
    assert first.report_pack_ref == "report-pack://bt-alpha-core-20260528-v1"
    assert {"total_return", "max_drawdown", "turnover"}.issubset(set(first.metrics_schema))
    assert all(value == 0 for value in first.operation_counts.values())
    assert validate_backtest_run_spec(first) == ()


def test_cr148_backtest_run_spec_blocks_mutable_refs_runtime_scope_and_missing_fields() -> None:
    spec = _run_spec(dataset_snapshot_ref="research-dataset-snapshot://current")
    payload = spec.to_dict()
    payload["strategy_id"] = ""
    payload["backtest_engine"] = "backtrader"
    payload["frequency"] = "minute"
    payload["metrics_schema"] = ["sharpe"]
    payload["operation_counts"] = {"simulation_or_live": 1}

    codes = {issue["code"] for issue in validate_backtest_run_spec(payload)}
    assert "backtest_run_spec_required_field_missing" in codes
    assert "backtest_run_spec_mutable_ref_forbidden" in codes
    assert "backtest_run_spec_backtrader_deep_integration_deferred" in codes
    assert "backtest_run_spec_frequency_not_phase3_daily" in codes
    assert "backtest_run_spec_metric_required" in codes
    assert "backtest_run_spec_operation_counter_nonzero" in codes


def _report_pack(**overrides: object):
    payload = {
        "run_spec": _run_spec(),
        "metrics": {
            "total_return": 0.184,
            "annual_return": 0.071,
            "max_drawdown": -0.083,
            "sharpe": 1.21,
            "turnover": 0.37,
            "final_nav": 1.184,
        },
        "metadata": {
            "strategy_name": "=alpha_formula",
            "quality_status": "pass",
        },
    }
    payload.update(overrides)
    return build_backtest_report_pack(**payload)  # type: ignore[arg-type]


def test_cr148_backtest_report_pack_is_stable_metadata_only_and_sanitized() -> None:
    first = _report_pack()
    second = _report_pack()

    assert first.content_hash == second.content_hash
    assert first.content_hash.startswith("sha256:")
    assert first.run_spec_hash.startswith("sha256:")
    assert first.row_count == 1
    assert first.artifact_refs == ("inline://backtest-report-row/bt-alpha-core-20260528-v1",)
    assert {"total_return", "max_drawdown", "turnover"}.issubset(set(first.metric_names))
    assert first.report_rows[0]["strategy_name"] == "'=alpha_formula"
    assert all(value == 0 for value in first.operation_counts.values())
    assert validate_backtest_report_pack(first) == ()


def test_cr148_backtest_report_pack_blocks_mutable_refs_missing_metrics_and_operations() -> None:
    pack = _report_pack(metrics={"sharpe": 1.2}, artifact_refs=("artifact://current/report",))
    payload = pack.to_dict()
    payload["report_pack_ref"] = ""
    payload["content_hash"] = "bad"
    payload["operation_counts"] = {"reports_overwrite": 1}

    codes = {issue["code"] for issue in validate_backtest_report_pack(payload)}
    assert "backtest_report_pack_required_field_missing" in codes
    assert "backtest_report_pack_content_hash_invalid" in codes
    assert "backtest_report_pack_mutable_ref_forbidden" in codes
    assert "backtest_report_pack_metric_required" in codes
    assert "backtest_report_pack_operation_counter_nonzero" in codes


def _cost_risk_pack(**overrides: object):
    payload = {
        "run_spec": _run_spec(),
        "metrics": {
            "total_return": 0.184,
            "annual_return": 0.071,
            "max_drawdown": -0.083,
            "sharpe": 1.21,
            "turnover": 0.37,
            "final_nav": 1.184,
        },
        "cost_summary": {
            "total_cost": 1840.0,
            "commission_rate": 0.0003,
            "slippage_rate": 0.0002,
            "sell_tax_rate": 0.001,
        },
        "risk_summary": {
            "volatility": 0.142,
            "tracking_error": 0.061,
            "beta": 0.91,
        },
    }
    payload.update(overrides)
    return build_backtest_cost_risk_attribution_pack(**payload)  # type: ignore[arg-type]


def test_cr148_cost_risk_attribution_pack_is_stable_and_metadata_only() -> None:
    first = _cost_risk_pack()
    second = _cost_risk_pack()

    assert first.content_hash == second.content_hash
    assert first.content_hash.startswith("sha256:")
    assert first.run_spec_hash.startswith("sha256:")
    assert first.attribution_ref == "cost-risk-attribution://bt-alpha-core-20260528-v1"
    assert {"cost_model_ref", "slippage_model_ref", "turnover", "total_cost"} <= set(first.cost_fields)
    assert {"benchmark_ref", "max_drawdown", "sharpe", "volatility"} <= set(first.risk_metrics)
    assert first.attribution_refs == ("attribution://backtest-cost-risk/bt-alpha-core-20260528-v1",)
    assert all(value == 0 for value in first.operation_counts.values())
    assert validate_backtest_cost_risk_attribution_pack(first) == ()


def test_cr148_cost_risk_attribution_pack_blocks_mutable_refs_missing_coverage_and_operations() -> None:
    pack = _cost_risk_pack(attribution_refs=("attribution://current/cost-risk",))
    payload = pack.to_dict()
    payload["risk_policy_ref"] = ""
    payload["content_hash"] = "bad"
    payload["cost_fields"] = ["cost_model_ref"]
    payload["risk_metrics"] = ["sharpe"]
    payload["operation_counts"] = {"simulation_or_live": 1}

    codes = {issue["code"] for issue in validate_backtest_cost_risk_attribution_pack(payload)}
    assert "backtest_cost_risk_required_field_missing" in codes
    assert "backtest_cost_risk_content_hash_invalid" in codes
    assert "backtest_cost_risk_mutable_ref_forbidden" in codes
    assert "backtest_cost_risk_cost_field_required" in codes
    assert "backtest_cost_risk_metric_required" in codes
    assert "backtest_cost_risk_operation_counter_nonzero" in codes
