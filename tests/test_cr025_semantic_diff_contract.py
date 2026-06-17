from __future__ import annotations

import ast
from pathlib import Path

import pytest

import engine.semantic_diff as semantic_diff
from engine.semantic_diff import (
    REQUIRED_FIELD_GROUPS,
    SCHEMA_VERSION,
    SemanticDiffPathError,
    build_semantic_diff,
    resolve_semantic_diff_path,
    scan_semantic_diff_claims,
    validate_semantic_diff_artifact,
    zero_forbidden_operation_counts,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _baseline_fixture(**overrides):
    result = {
        "run_id": "run-semantic-fixture",
        "lineage": {"source": "lightweight-fixture"},
        "metrics": {
            "starting_cash": 1_000_000.0,
            "ending_cash": 999_850.0,
            "final_value": 1_002_500.0,
            "total_return": 0.0025,
            "max_drawdown": -0.003,
            "turnover": 0.12,
        },
        "fills": [
            {"trade_date": "2026-01-05", "symbol": "000001.SZ", "price": 10.0, "quantity": 1000},
        ],
        "commission": 10.0,
        "tax": 0.0,
        "slippage": 5.0,
        "holdings_delta": {"000001.SZ": 1000},
        "position_sizing_delta": {"000001.SZ": 0.1},
        "timeline": [{"date": "2026-01-05", "event": "baseline_fill"}],
    }
    result.update(overrides)
    return result


def _reference_fixture(**overrides):
    result = {
        "run_id": "run-semantic-fixture-reference",
        "lineage": {"source": "reference-fixture"},
        "metrics": {
            "starting_cash": 1_000_000.0,
            "ending_cash": 999_830.0,
            "final_value": 1_002_100.0,
            "total_return": 0.0021,
            "max_drawdown": -0.004,
            "turnover": 0.13,
        },
        "fills": [
            {"trade_date": "2026-01-05", "symbol": "000001.SZ", "price": 10.02, "quantity": 1000},
            {"trade_date": "2026-01-06", "symbol": "000001.SZ", "price": 10.03, "quantity": 200, "status": "partial"},
        ],
        "commission": 12.0,
        "tax": 0.0,
        "slippage": 7.0,
        "holdings_delta": {"000001.SZ": 1200},
        "position_sizing_delta": {"000001.SZ": 0.12},
        "timeline": [{"date": "2026-01-06", "event": "reference_partial_fill"}],
    }
    result.update(overrides)
    return result


def _selection_available():
    return {
        "selected_backend": "backtrader",
        "availability_status": "available",
        "lineage": {"selector": "fixture"},
        "limitations": [{"code": "fixture_only"}],
        "forbidden_operation_counts": zero_forbidden_operation_counts(),
    }


def test_schema_builder_covers_required_field_groups_and_reasons() -> None:
    artifact = build_semantic_diff(
        _baseline_fixture(),
        _reference_fixture(),
        _selection_available(),
        {"generated_at": "2026-06-02T08:15:00+08:00", "source_run_id": "run-semantic-fixture"},
    )
    artifact_dict = artifact.to_dict()
    validation = validate_semantic_diff_artifact(artifact)

    assert validation.passed is True
    assert len(REQUIRED_FIELD_GROUPS) >= 10
    assert set(REQUIRED_FIELD_GROUPS).issubset(artifact_dict)
    assert artifact_dict["schema_version"] == SCHEMA_VERSION
    assert artifact_dict["artifact_type"] == "research_comparison"
    for group_name in ("fills", "cash_cost", "portfolio", "performance", "timeline"):
        assert artifact_dict[group_name]["reason"]
    assert artifact_dict["explanation"]["diff_reason"]


def test_reference_unavailable_is_valid_state_with_reasons_and_limitations() -> None:
    selection_result = {
        "selected_backend": "none",
        "availability_status": "backend_unavailable",
        "blocked_reasons": ("backend_unavailable:dependency_missing",),
        "limitations": [{"code": "optional_reference_not_installed"}],
        "forbidden_operation_counts": zero_forbidden_operation_counts(),
    }

    artifact = build_semantic_diff(
        _baseline_fixture(),
        None,
        selection_result,
        {"generated_at": "2026-06-02T08:16:00+08:00", "source_run_id": "run-reference-unavailable"},
    )
    data = artifact.to_dict()
    validation = validate_semantic_diff_artifact(data)

    assert validation.passed is True
    assert data["availability"]["baseline_available"] is True
    assert data["availability"]["reference_available"] is False
    assert data["metadata"]["reference_backend"] == "unavailable"
    assert "backend_unavailable:dependency_missing" in data["availability"]["blocked_reasons"]
    assert data["availability"]["limitations"]
    assert data["fills"]["unavailable"] is True
    assert data["explanation"]["diff_reason"] == ["reference_unavailable"]


def test_baseline_and_reference_tracks_are_kept_separate() -> None:
    baseline = _baseline_fixture(metrics={**_baseline_fixture()["metrics"], "final_value": 1_010_000.0})
    reference = _reference_fixture(metrics={**_reference_fixture()["metrics"], "final_value": 990_000.0})

    artifact = build_semantic_diff(
        baseline,
        reference,
        _selection_available(),
        {"generated_at": "2026-06-02T08:17:00+08:00", "source_run_id": "run-separation"},
    ).to_dict()

    assert artifact["metadata"]["baseline_backend"] == "lightweight"
    assert artifact["metadata"]["reference_backend"] == "backtrader_optional_reference"
    assert artifact["portfolio"]["net_value_delta"]["baseline"] == 1_010_000.0
    assert artifact["portfolio"]["net_value_delta"]["reference"] == 990_000.0
    assert artifact["portfolio"]["net_value_delta"]["baseline"] != artifact["portfolio"]["net_value_delta"]["reference"]
    assert validate_semantic_diff_artifact(artifact).passed is True


def test_claim_guard_blocks_forbidden_report_claims_and_scope_terms() -> None:
    scan = scan_semantic_diff_claims(
        "production truth, simulation-ready, QMT admission pass, "
        "factor tear sheet, IC / RankIC report, strategy admission package, "
        "completed multifactor research framework, FactorSpec, FactorRunSpec, Qlib, Alphalens, vnpy.alpha"
    )

    assert scan.passed is False
    assert scan.forbidden_claim_counts["production truth"] == 1
    assert scan.forbidden_claim_counts["simulation-ready"] == 1
    assert scan.forbidden_claim_counts["qmt admission pass"] == 1
    assert scan.forbidden_claim_counts["factor tear sheet"] == 1
    assert scan.scope_term_counts["FactorSpec"] == 1
    assert scan.scope_term_counts["Qlib"] == 1


def test_path_guard_limits_outputs_to_reports_semantic_diff() -> None:
    path = resolve_semantic_diff_path("run/../semantic fixture")

    assert path.relative_to(PROJECT_ROOT).as_posix().startswith("reports/semantic_diff/")
    assert path.suffix == ".json"
    assert "semantic-fixture" in path.name

    nested = resolve_semantic_diff_path("run-01", output_root="reports/semantic_diff/contracts")
    assert nested.relative_to(PROJECT_ROOT).as_posix().startswith("reports/semantic_diff/contracts/")

    with pytest.raises(SemanticDiffPathError):
        resolve_semantic_diff_path("run-01", output_root="reports/not-semantic-diff")

    with pytest.raises(SemanticDiffPathError):
        resolve_semantic_diff_path("run-01", output_root=PROJECT_ROOT / "market_data" / "catalog")


def test_forbidden_operation_counters_remain_zero_and_nonzero_blocks() -> None:
    artifact = build_semantic_diff(
        _baseline_fixture(),
        _reference_fixture(),
        _selection_available(),
        {"generated_at": "2026-06-02T08:18:00+08:00", "source_run_id": "run-counters"},
    ).to_dict()
    validation = validate_semantic_diff_artifact(artifact)

    assert validation.passed is True
    assert set(validation.forbidden_operation_counts) == set(semantic_diff.FORBIDDEN_OPERATION_COUNTERS)
    assert all(value == 0 for value in validation.forbidden_operation_counts.values())

    artifact["metadata"]["forbidden_operation_counts"]["lake_write"] = 1
    failed = validate_semantic_diff_artifact(artifact)

    assert failed.passed is False
    assert any(violation.code == "forbidden_operation_nonzero" for violation in failed.violations)


def test_semantic_diff_module_static_import_boundary() -> None:
    tree = ast.parse((PROJECT_ROOT / "engine" / "semantic_diff.py").read_text(encoding="utf-8"))
    imports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.append(node.module)

    forbidden_import_roots = {
        "backtrader",
        "market_data.connectors",
        "market_data.runtime",
        "market_data.storage",
        "requests",
        "httpx",
        "aiohttp",
        "socket",
        "subprocess",
        "tushare",
        "xtquant",
    }
    assert not [name for name in imports if any(name == item or name.startswith(f"{item}.") for item in forbidden_import_roots)]
