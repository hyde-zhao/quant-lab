from __future__ import annotations

import ast
import json
from pathlib import Path
from typing import Any

import pandas as pd
import pytest

from engine.portfolio import DEFAULT_COST_GRID_BPS
from engine.research_dataset import evaluate_robust_validation_claims, merge_factor_audit_metadata
from experiments.run_experiment_15_factor_framework import FactorFrameworkError
from experiments.run_experiment_17_21_factor_suite import (
    FactorDefinition,
    build_factor_panel_audit,
    build_parameter_grid,
    build_robust_validation_views,
    resolve_cr011_validation_output_dir,
    write_factor_panel_audit_outputs,
    write_robust_validation_outputs,
)


TARGET_FILES = (
    Path("engine/research_dataset.py"),
    Path("experiments/run_experiment_17_21_factor_suite.py"),
)


def test_factor_panel_audit_outputs_four_exact_stages_and_manifest(tmp_path: Path) -> None:
    raw_matrices = factor_matrices()
    zscore_matrices = zscore_fixture()
    panel_by_stage, manifest = build_factor_panel_audit(
        raw_matrices,
        zscore_matrices,
        preprocessing_summary_fixture(),
        factor_definitions_fixture(),
        run_metadata={"run_id": "unit-s08"},
    )

    assert tuple(panel_by_stage) == ("raw", "directional", "winsorized", "zscore")
    assert manifest["stages"] == ["raw", "directional", "winsorized", "zscore"]
    assert manifest["factor_audit_status"] == "pass"
    assert manifest["row_counts"] == {"raw": 8, "directional": 8, "winsorized": 8, "zscore": 8}

    directional = panel_by_stage["directional"]
    rsi_row = directional[
        (directional["factor_name"] == "rsi_14")
        & (directional["trade_date"] == "2026-01-02")
        & (directional["symbol"] == "AAA")
    ].iloc[0]
    assert rsi_row["directional_value"] == pytest.approx(-70.0)

    written = write_factor_panel_audit_outputs(tmp_path, panel_by_stage, manifest)
    assert set(written["stage_files"]) == {"raw", "directional", "winsorized", "zscore"}
    assert Path(written["manifest_path"]).exists()
    saved = json.loads(Path(written["manifest_path"]).read_text(encoding="utf-8"))
    assert saved["factor_panel_manifest_path"] == written["manifest_path"]
    assert all(Path(path).exists() for path in saved["stage_files"].values())


def test_robust_validation_views_preserve_upstream_blocked_claim_priority(tmp_path: Path) -> None:
    panel_by_stage, manifest = build_factor_panel_audit(
        factor_matrices(),
        zscore_fixture(),
        preprocessing_summary_fixture(),
        factor_definitions_fixture(),
        run_metadata={"run_id": "unit-s08"},
    )
    manifest = write_factor_panel_audit_outputs(tmp_path, panel_by_stage, manifest)
    capacity_metadata = capacity_cost_metadata_fixture()
    strategy_summary = strategy_summary_fixture()

    validation = build_robust_validation_views(
        manifest,
        strategy_summary,
        {"multifactor_top10_equity": tmp_path / "multifactor_top10_equity.csv"},
        capacity_metadata,
        market_state_labels=market_state_fixture(),
        parameter_grid=build_parameter_grid([0.1, 0.2], 0.3, 20),
    )
    assert validation["view_names"] == ["rolling", "annual", "market_state", "parameter_grid", "cost_grid"]
    assert validation["robust_validation_status"] == "pass"
    assert {name: payload["status"] for name, payload in validation["views"].items()} == {
        "rolling": "pass",
        "annual": "pass",
        "market_state": "pass",
        "parameter_grid": "pass",
        "cost_grid": "pass",
    }

    validation = write_robust_validation_outputs(tmp_path, validation)
    claims = evaluate_robust_validation_claims(validation, capacity_metadata)

    blocked_names = {item["claim"] for item in claims["blocked_claims"]}
    assert claims["robust_validation_status"] == "pass"
    assert claims["claim_gate_status"] == "blocked_upstream_claims"
    assert "robust_factor_validation_supported" in blocked_names
    assert "robust_factor_validation_supported" not in claims["allowed_claims"]

    metadata = merge_factor_audit_metadata(base_metadata(), manifest, validation, claims)
    assert metadata["factor_panel_stage_count"] == 4
    assert metadata["factor_panel_stages"] == ["raw", "directional", "winsorized", "zscore"]
    assert metadata["robust_validation_views"] == ["rolling", "annual", "market_state", "parameter_grid", "cost_grid"]
    assert metadata["claim_gate_status"] == "blocked_upstream_claims"
    assert "robust_factor_validation_supported" not in metadata["allowed_claims"]
    for field in ("network_calls", "lake_writes", "credential_reads", "legacy_data_operations", "old_report_overwrites"):
        assert metadata[field] == 0


def test_s08_forbidden_boundaries_are_static_and_legacy_report_fails_fast() -> None:
    with pytest.raises(FactorFrameworkError, match="禁止覆盖旧实验 17-21 baseline 报告"):
        resolve_cr011_validation_output_dir("reports/experiment_17_21")

    forbidden_imports = {
        "market_data.connectors",
        "market_data.runtime",
        "market_data.storage",
        "requests",
        "urllib",
        "httpx",
        "aiohttp",
        "socket",
        "subprocess",
    }
    for source_path in TARGET_FILES:
        source = source_path.read_text(encoding="utf-8")
        tree = ast.parse(source)
        imports = imports_for(tree)
        assert not any(name == item or name.startswith(f"{item}.") for name in imports for item in forbidden_imports), source_path
        assert not calls_env_or_credentials(tree), source_path
    experiment_source = Path("experiments/run_experiment_17_21_factor_suite.py").read_text(encoding="utf-8")
    assert "LEGACY_EXPERIMENT_17_21_REPORT.write_text" not in experiment_source
    assert "LEGACY_EXPERIMENT_17_21_REPORT.open" not in experiment_source


def factor_matrices() -> dict[str, pd.DataFrame]:
    dates = pd.to_datetime(["2026-01-02", "2026-01-05"]).date
    return {
        "rsi_14": pd.DataFrame({"AAA": [70.0, 30.0], "BBB": [40.0, 60.0]}, index=dates),
        "momentum_20d": pd.DataFrame({"AAA": [0.10, 0.20], "BBB": [0.05, 0.15]}, index=dates),
    }


def zscore_fixture() -> dict[str, pd.DataFrame]:
    dates = pd.to_datetime(["2026-01-02", "2026-01-05"]).date
    return {
        "rsi_14": pd.DataFrame({"AAA": [-1.0, 1.0], "BBB": [1.0, -1.0]}, index=dates),
        "momentum_20d": pd.DataFrame({"AAA": [1.0, 1.0], "BBB": [-1.0, -1.0]}, index=dates),
    }


def preprocessing_summary_fixture() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"factor_name": "rsi_14", "direction_sign": -1, "winsor_lower": 0.0, "winsor_upper": 1.0},
            {"factor_name": "momentum_20d", "direction_sign": 1, "winsor_lower": 0.0, "winsor_upper": 1.0},
        ]
    )


def factor_definitions_fixture() -> list[FactorDefinition]:
    return [
        FactorDefinition("rsi_14", "experiment_17", "fixture", "低 RSI", "实验七", -1, "原始值越低越看多"),
        FactorDefinition("momentum_20d", "baseline", "fixture", "动量", "基线", 1, "原始值越大越看多"),
    ]


def strategy_summary_fixture() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "strategy_name": "multifactor",
                "model_type": "multi_factor",
                "top_fraction": 0.1,
                "exit_fraction": 0.3,
                "status": "success",
                "first_signal_date": "2026-01-02",
                "last_signal_date": "2026-12-31",
                "annual_return_with_cost": 0.12,
                "sharpe_with_cost": 1.1,
                "max_drawdown_with_cost": -0.08,
                "turnover_with_cost": 0.9,
            },
            {
                "strategy_name": "multifactor",
                "model_type": "multi_factor",
                "top_fraction": 0.2,
                "exit_fraction": 0.3,
                "status": "success",
                "first_signal_date": "2026-01-02",
                "last_signal_date": "2026-12-31",
                "annual_return_with_cost": 0.09,
                "sharpe_with_cost": 0.8,
                "max_drawdown_with_cost": -0.06,
                "turnover_with_cost": 0.7,
            },
        ]
    )


def market_state_fixture() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"trade_date": "2026-01-02", "market_state": "up", "market_return": 0.01},
            {"trade_date": "2026-01-05", "market_state": "down", "market_return": -0.02},
        ]
    )


def capacity_cost_metadata_fixture() -> dict[str, Any]:
    return {
        "cost_grid_bps": list(DEFAULT_COST_GRID_BPS),
        "cost_sensitivity_status": "pass",
        "cost_sensitivity_report": {
            "cost_grid_bps": list(DEFAULT_COST_GRID_BPS),
            "cost_sensitivity_status": "pass",
            "cost_scenarios": [
                {"view": "cost_grid", "cost_scenario_id": f"cost_{bps}bps", "cost_bps": bps}
                for bps in DEFAULT_COST_GRID_BPS
            ],
        },
        "allowed_claims": ["framework_validation", "robust_factor_validation_supported"],
        "blocked_claims": [
            {
                "claim": "robust_factor_validation_supported",
                "missing_capability": "upstream_fixture",
                "reason": "upstream_blocked_claim_must_win",
                "severity": "BLOCKING",
                "source_story": "CR011-S07",
            }
        ],
        "known_limitations": [],
        "network_calls": 0,
        "lake_writes": 0,
        "credential_reads": 0,
        "legacy_data_operations": 0,
        "old_report_overwrites": 0,
    }


def base_metadata() -> dict[str, Any]:
    return {
        "schema_name": "research_input_v1",
        "report_kind": "experiment_17_21_v2",
        "coverage_start": "2026-01-02",
        "coverage_end": "2026-01-05",
        "benchmark_status": "proxy_baseline",
        "benchmark_kind": "proxy_baseline",
        "universe_mode": "fixed_snapshot",
        "adjustment_policy": "qfq",
        "forward_return_horizon": 20,
        "label_available_end": "2026-01-05",
        "quality_status": "pass",
        "readiness_status": "research_ready",
        "legacy_report_policy": "legacy_only_not_current_truth",
        "known_limitations": [],
        "allowed_claims": ["framework_validation"],
        "blocked_claims": [],
        "network_calls": 0,
        "lake_writes": 0,
        "credential_reads": 0,
        "legacy_data_operations": 0,
        "old_report_overwrites": 0,
    }


def imports_for(tree: ast.AST) -> list[str]:
    imports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.append(node.module)
    return imports


def calls_env_or_credentials(tree: ast.AST) -> bool:
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if node.func.attr in {"getenv", "environ"}:
                return True
        if isinstance(node, ast.ImportFrom) and node.module and "dotenv" in node.module:
            return True
    return False
