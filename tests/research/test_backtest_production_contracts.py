from __future__ import annotations

from engine.backtest_production_contracts import (
    BacktestFoundationAssetMap,
    Phase3ScopeGuard,
    build_backtest_foundation_asset_map,
    validate_backtest_foundation_asset_map,
    validate_phase3_scope_guard,
)


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
    assert asset_map.gap_count == 3
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
