from __future__ import annotations

import ast
from argparse import Namespace
from datetime import date
from pathlib import Path
from typing import Any

import pandas as pd
import pytest

from engine.portfolio import (
    DEFAULT_COST_GRID_BPS,
    CAPACITY_REPORT_REQUIRED_FIELDS,
    CAPACITY_STRONG_CLAIMS,
    build_capacity_report,
    evaluate_capacity_cost_claims,
    run_cost_sensitivity_grid,
)
from engine.research_dataset import build_liquidity_capacity_inputs, merge_capacity_cost_metadata
from experiments.run_experiment_15_factor_framework import FactorFrameworkError
from experiments.run_experiment_17_21_factor_suite import (
    _ensure_not_legacy_report_output_path,
    build_experiment_capacity_cost_metadata,
)


TARGET_FILES = (
    Path("engine/research_dataset.py"),
    Path("engine/portfolio.py"),
    Path("experiments/run_experiment_17_21_factor_suite.py"),
)


def test_fixed_cost_grid_outputs_four_ordered_scenarios_and_monotonic_cost() -> None:
    report = run_cost_sensitivity_grid({"gross_return": 0.12, "turnover": 1.5})

    assert report["cost_grid_bps"] == list(DEFAULT_COST_GRID_BPS)
    assert report["cost_sensitivity_status"] == "pass"
    assert [row["cost_scenario_id"] for row in report["cost_scenarios"]] == [
        "cost_0bps",
        "cost_5bps",
        "cost_10bps",
        "cost_20bps",
    ]
    after_returns = [row["cost_after_return"] for row in report["cost_scenarios"]]
    assert after_returns == sorted(after_returns, reverse=True)


def test_capacity_report_contains_required_five_field_classes() -> None:
    liquidity = build_liquidity_capacity_inputs(available_liquidity_payload())
    cost_report = run_cost_sensitivity_grid({"gross_return": 0.12, "turnover": 0.8})

    report = build_capacity_report(
        trades_fixture(),
        holdings_fixture(),
        liquidity,
        portfolio_returns={"gross_return": 0.12, "turnover": 0.8, "initial_cash": 1_000_000.0},
        cost_sensitivity_report=cost_report,
    )

    for field in CAPACITY_REPORT_REQUIRED_FIELDS:
        assert field in report
    assert report["capacity_report_status"] == "pass"
    assert report["liquidity_capacity_status"] == "available"
    assert report["amount_participation_rate"] == pytest.approx(0.02)
    assert report["holding_count"] == 2
    assert report["sample_loss_count"] == 0


def test_missing_liquidity_blocks_capacity_claims_and_metadata_merges_reason() -> None:
    liquidity = build_liquidity_capacity_inputs({"amount": 1_000_000.0, "volume": 100_000.0, "adv20": 2_000_000.0})
    cost_report = run_cost_sensitivity_grid({"gross_return": 0.10, "turnover": 1.0})
    capacity_report = build_capacity_report(trades_fixture(), holdings_fixture(), liquidity, cost_sensitivity_report=cost_report)
    claims = evaluate_capacity_cost_claims(capacity_report, cost_report)
    metadata = merge_capacity_cost_metadata(base_metadata(), capacity_report, cost_report, claims)

    assert liquidity["liquidity_capacity_status"] == "blocked_missing_liquidity"
    assert "missing_liquidity_capacity_input:turnover" in liquidity["missing_reasons"]
    assert claims["blocked_capacity_claim_count"] >= 3
    assert set(CAPACITY_STRONG_CLAIMS[:3]).isdisjoint(set(claims["allowed_claims"]))
    assert metadata["liquidity_capacity_status"] == "blocked_missing_liquidity"
    assert metadata["capacity_cost_status"] == "blocked_missing_liquidity"
    assert metadata["network_calls"] == 0
    assert metadata["lake_writes"] == 0
    assert metadata["credential_reads"] == 0
    assert metadata["legacy_data_operations"] == 0
    assert metadata["old_report_overwrites"] == 0


def test_single_cost_point_and_invalid_grid_fail_closed() -> None:
    single = run_cost_sensitivity_grid({"gross_return": 0.10, "turnover": 1.0}, cost_grid_bps=(10,))
    invalid = run_cost_sensitivity_grid({"gross_return": 0.10, "turnover": 1.0}, cost_grid_bps=(0, 10, 20))

    assert single["cost_sensitivity_status"] == "fail"
    assert any(item["reason"] == "single_cost_point_not_allowed" for item in single["blocked_claims"])
    assert invalid["cost_sensitivity_status"] == "fail"
    assert any(item["reason"] == "invalid_cost_grid" for item in invalid["blocked_claims"])


def test_upstream_blocked_claims_are_preserved_and_not_reallowed() -> None:
    liquidity = build_liquidity_capacity_inputs(available_liquidity_payload())
    cost_report = run_cost_sensitivity_grid({"gross_return": 0.12, "turnover": 0.8})
    capacity_report = build_capacity_report(trades_fixture(), holdings_fixture(), liquidity, cost_sensitivity_report=cost_report)
    upstream = {
        "allowed_claims": ["real_tradable_execution", "real_vwap_execution", "pure_alpha", "framework_validation"],
        "blocked_claims": [
            blocked("real_tradable_execution", "tradability", "upstream_tradability_blocked", "CR011-S03"),
            blocked("real_vwap_execution", "execution_price", "execution_price_degraded", "CR011-S04"),
            blocked("pure_alpha", "style_exposure", "exposure_capacity_claim_blocked", "CR011-S06"),
        ],
    }

    claims = evaluate_capacity_cost_claims(capacity_report, cost_report, upstream)

    blocked_names = {item["claim"] for item in claims["blocked_claims"]}
    assert {"real_tradable_execution", "real_vwap_execution", "pure_alpha"} <= blocked_names
    assert "real_tradable_execution" not in claims["allowed_claims"]
    assert "real_vwap_execution" not in claims["allowed_claims"]
    assert "pure_alpha" not in claims["allowed_claims"]
    assert "capacity_tradable" in claims["allowed_claims"]


def test_experiment_metadata_uses_s07_contract_without_old_report_overwrite() -> None:
    cost_report = run_cost_sensitivity_grid({"gross_return": 0.12, "turnover": 0.8})
    capacity_report = build_capacity_report(
        trades_fixture(),
        holdings_fixture(),
        build_liquidity_capacity_inputs(available_liquidity_payload()),
        cost_sensitivity_report=cost_report,
    )
    claims = evaluate_capacity_cost_claims(capacity_report, cost_report)
    strategy_summary = pd.DataFrame(
        [
            {
                "strategy_name": "multifactor_top10",
                "model_type": "multi_factor",
                "status": "success",
                "annual_return_with_cost": 0.08,
                "capacity_report": capacity_report,
                "cost_sensitivity_report": cost_report,
                "capacity_cost_claims": claims,
            }
        ]
    )

    metadata = build_experiment_capacity_cost_metadata(base_metadata(), strategy_summary)

    assert metadata["cost_grid_bps"] == [0, 5, 10, 20]
    assert metadata["capacity_report"]["sample_loss_count"] == 0
    assert metadata["cost_sensitivity_report"]["cost_sensitivity_status"] == "pass"
    assert metadata["old_report_overwrites"] == 0
    with pytest.raises(FactorFrameworkError, match="禁止覆盖旧实验 17-21 baseline 报告"):
        _ensure_not_legacy_report_output_path(Namespace(output_dir="reports/experiment_17_21"))


def test_s07_forbidden_boundaries_are_static_and_no_secret_leakage() -> None:
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


def available_liquidity_payload() -> dict[str, Any]:
    return {
        "amount": 2_000_000.0,
        "volume": 200_000.0,
        "turnover": 0.8,
        "adv20": 5_000_000.0,
        "lineage": {"source": "fixture", "manifest_run_id": "run-liquidity"},
        "network_calls": 0,
        "lake_writes": 0,
        "credential_reads": 0,
        "legacy_data_operations": 0,
        "old_report_overwrites": 0,
    }


def trades_fixture() -> list[dict[str, Any]]:
    return [
        {
            "signal_date": date(2026, 1, 2),
            "execution_date": date(2026, 1, 5),
            "symbol": "AAA",
            "side": "buy",
            "price": 10.0,
            "quantity": 5_000.0,
            "notional": 50_000.0,
            "cost": 250.0,
            "status": "filled",
        },
        {
            "signal_date": date(2026, 1, 2),
            "execution_date": date(2026, 1, 5),
            "symbol": "BBB",
            "side": "buy",
            "price": 12.0,
            "quantity": 4_166.6667,
            "notional": 50_000.0,
            "cost": 250.0,
            "status": "filled",
        },
    ]


def holdings_fixture() -> list[dict[str, Any]]:
    return [{"holdings": {"AAA": 5_000.0, "BBB": 4_166.6667}}]


def blocked(claim: str, missing_capability: str, reason: str, source_story: str) -> dict[str, Any]:
    return {
        "claim": claim,
        "missing_capability": missing_capability,
        "reason": reason,
        "severity": "BLOCKING",
        "source_story": source_story,
    }


def base_metadata() -> dict[str, Any]:
    return {
        "schema_name": "research_input_v1",
        "report_kind": "experiment_17_21_v2",
        "coverage_start": "2026-01-02",
        "coverage_end": "2026-01-05",
        "benchmark_status": "required_missing",
        "benchmark_kind": "proxy_baseline",
        "universe_mode": "fixed_snapshot",
        "adjustment_policy": "qfq",
        "forward_return_horizon": 20,
        "label_available_end": "2026-01-05",
        "quality_status": "pass",
        "readiness_status": "research_ready",
        "legacy_report_policy": "legacy_only_not_current_truth",
        "lineage": {"manifest_run_id": "run-research"},
        "known_limitations": ["fixture"],
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
