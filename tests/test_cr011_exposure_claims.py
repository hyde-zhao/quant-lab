from __future__ import annotations

import ast
import json
from pathlib import Path
from typing import Any

import pandas as pd

from engine.research_dataset import (
    build_exposure_availability_matrix,
    evaluate_neutralization_claims,
    merge_exposure_claims_into_metadata,
)
from market_data.readers import ExposureInputRequest, ReaderResult, read_exposure_inputs


TARGET_FILES = (
    Path("market_data/readers.py"),
    Path("engine/research_dataset.py"),
)


def test_read_exposure_inputs_missing_lake_root_is_typed_and_does_not_call_reader() -> None:
    calls: list[str] = []

    result = read_exposure_inputs(
        ExposureInputRequest(lake_root=None, symbols=("AAA", "BBB")),
        reader=lambda dataset, *_args, **_kwargs: calls.append(dataset),
    )

    assert calls == []
    assert set(result) == {"industry_classification", "market_cap", "float_market_cap", "style_exposure"}
    for capability, reader_result in result.items():
        assert reader_result.status == "required_missing"
        assert reader_result.issues[0]["code"] == "lake_root_missing"
        assert reader_result.issues[0]["capability"] == capability
        assert reader_result.remediation_spec["auto_execute"] is False
        assert reader_result.remediation_spec["dry_run_default"] is True


def test_pit_exposures_allow_neutralization_claims_and_metadata(tmp_path: Path) -> None:
    reader_results = exposure_reader_results(tmp_path)
    matrix = build_exposure_availability_matrix(
        reader_results,
        factor_sample(),
        universe_metadata=pit_metadata(),
        decision_time="2026-01-05",
        requested_style_factors=("beta", "size"),
    )
    gate = evaluate_neutralization_claims(
        matrix,
        factor_metrics={
            "raw_ic": 0.12,
            "industry_neutral_ic": 0.08,
            "market_cap_neutral_ic": 0.06,
            "style_neutral_ic": 0.04,
            "pure_alpha": 0.03,
            "risk_model_adjusted_alpha": 0.02,
        },
    )
    metadata = merge_exposure_claims_into_metadata(
        {
            "allowed_claims": ["framework_validation"],
            "blocked_claims": [],
            "known_limitations": [],
            "auxiliary_availability": {"tradability": {"status": "available"}},
        },
        gate,
    )

    assert all(entry["status"] == "available" for entry in metadata["exposure_availability"].values())
    assert metadata["industry_availability"]["coverage_ratio"] == 1.0
    assert metadata["market_cap_availability"]["coverage_ratio"] == 1.0
    assert metadata["float_market_cap_availability"]["coverage_ratio"] == 1.0
    assert metadata["float_market_cap"] == metadata["float_market_cap_availability"]
    assert metadata["style_exposure_availability"]["coverage_ratio"] == 1.0
    assert metadata["neutralization_status"] == "pass"
    assert metadata["raw_ic"] == 0.12
    assert metadata["industry_neutral_ic"] == 0.08
    assert metadata["market_cap_neutral_ic"] == 0.06
    assert metadata["style_neutral_ic"] == 0.04
    assert {"industry_neutral_ic", "market_cap_neutral_ic", "style_neutral_ic", "pure_alpha"} <= set(metadata["allowed_claims"])
    assert metadata["blocked_claims"] == []
    assert metadata["auxiliary_availability"]["tradability"]["status"] == "available"


def test_missing_industry_blocks_industry_neutral_claims(tmp_path: Path) -> None:
    reader_results = exposure_reader_results(
        tmp_path,
        overrides={
            "industry_classification": ReaderResult(
                status="required_missing",
                issues=[{"code": "industry_source_unresolved"}],
                remediation_spec={"auto_execute": False},
            )
        },
    )

    gate = evaluate_neutralization_claims(
        build_exposure_availability_matrix(reader_results, factor_sample(), universe_metadata=pit_metadata()),
        requested_claims=(
            "industry_neutral_ic",
            "industry_neutral",
            "industry_attribution",
            "industry_zscore",
            "industry_group_ic",
        ),
        factor_metrics={"industry_neutral_ic": 0.08},
    )

    blocked_claims = {item["claim"] for item in gate.blocked_claims}
    assert gate.neutralization_status == "blocked_missing_industry"
    assert blocked_claims == {
        "industry_neutral_ic",
        "industry_neutral",
        "industry_attribution",
        "industry_zscore",
        "industry_group_ic",
    }
    assert not blocked_claims & set(gate.allowed_claims)
    assert {item["missing_capability"] for item in gate.blocked_claims} == {"industry_classification"}


def test_missing_float_cap_blocks_size_market_cap_and_capacity_claims(tmp_path: Path) -> None:
    cap_without_float = market_cap_frame().drop(columns=["float_market_cap"])
    reader_results = exposure_reader_results(
        tmp_path,
        overrides={"market_cap": ReaderResult(status="available", frame=cap_without_float)},
    )

    gate = evaluate_neutralization_claims(
        build_exposure_availability_matrix(reader_results, factor_sample(), universe_metadata=pit_metadata()),
        requested_claims=(
            "market_cap_neutral_ic",
            "market_cap_neutral",
            "size_neutral",
            "market_cap_weighted_ic",
            "capacity_size_supported",
        ),
        factor_metrics={"market_cap_neutral_ic": 0.06},
    )

    blocked_claims = {item["claim"] for item in gate.blocked_claims}
    assert gate.neutralization_status == "blocked_missing_market_cap"
    assert blocked_claims == {
        "market_cap_neutral_ic",
        "market_cap_neutral",
        "size_neutral",
        "market_cap_weighted_ic",
        "capacity_size_supported",
    }
    assert {item["missing_capability"] for item in gate.blocked_claims} == {"float_market_cap"}
    assert "market_cap_weighted_ic" not in gate.allowed_claims


def test_missing_style_blocks_pure_alpha_and_risk_model_claims(tmp_path: Path) -> None:
    reader_results = exposure_reader_results(
        tmp_path,
        overrides={
            "style_exposure": ReaderResult(
                status="source_unresolved",
                issues=[{"code": "style_exposure_source_unresolved"}],
                remediation_spec={"auto_execute": False},
            )
        },
    )

    gate = evaluate_neutralization_claims(
        build_exposure_availability_matrix(reader_results, factor_sample(), universe_metadata=pit_metadata()),
        requested_claims=("style_neutral_ic", "style_neutral", "pure_alpha", "risk_model_adjusted_alpha"),
        factor_metrics={"style_neutral_ic": 0.04, "pure_alpha": 0.03, "risk_model_adjusted_alpha": 0.02},
    )

    blocked_claims = {item["claim"] for item in gate.blocked_claims}
    assert gate.neutralization_status == "blocked_missing_style"
    assert blocked_claims == {"style_neutral_ic", "style_neutral", "pure_alpha", "risk_model_adjusted_alpha"}
    assert {item["missing_capability"] for item in gate.blocked_claims} == {"style_exposure"}
    assert gate.style_neutral_ic is None


def test_current_snapshot_future_asof_and_pit_gate_cannot_prove_pit_exposure(tmp_path: Path) -> None:
    snapshot_results = exposure_reader_results(
        tmp_path,
        overrides={"industry_classification": ReaderResult(status="available", frame=industry_frame(pit_status="non_pit_snapshot"))},
    )
    snapshot_matrix = build_exposure_availability_matrix(
        snapshot_results,
        factor_sample(),
        universe_metadata=pit_metadata(),
        decision_time="2026-01-05",
    )
    assert snapshot_matrix.entries["industry_classification"].status == "blocked_non_pit"
    assert snapshot_matrix.entries["industry_classification"].missing_reason == "current_snapshot_not_pit_exposure"

    future_results = exposure_reader_results(
        tmp_path,
        overrides={"market_cap": ReaderResult(status="available", frame=market_cap_frame(available_at="2026-01-08"))},
    )
    future_matrix = build_exposure_availability_matrix(
        future_results,
        factor_sample(),
        universe_metadata=pit_metadata(),
        decision_time="2026-01-05",
    )
    assert future_matrix.entries["market_cap"].status == "pit_incomplete"
    assert future_matrix.entries["market_cap"].as_of_join_violation_count == 2

    non_pit_gate = evaluate_neutralization_claims(
        build_exposure_availability_matrix(
            exposure_reader_results(tmp_path),
            factor_sample(),
            universe_metadata={
                "universe": {"is_pit_universe": False, "pit_status": "fixed_snapshot", "as_of_join_violation_count": 0},
                "lifecycle": {"lifecycle_status": "pass"},
            },
            decision_time="2026-01-05",
        ),
        requested_claims=("industry_neutral_ic", "market_cap_neutral_ic", "style_neutral_ic"),
        factor_metrics={"industry_neutral_ic": 0.08, "market_cap_neutral_ic": 0.06, "style_neutral_ic": 0.04},
    )
    assert non_pit_gate.neutralization_status == "blocked_non_pit"
    assert not {"industry_neutral_ic", "market_cap_neutral_ic", "style_neutral_ic"} & set(non_pit_gate.allowed_claims)


def test_metric_missing_does_not_fabricate_neutralized_values(tmp_path: Path) -> None:
    gate = evaluate_neutralization_claims(
        build_exposure_availability_matrix(
            exposure_reader_results(tmp_path),
            factor_sample(),
            universe_metadata=pit_metadata(),
            decision_time="2026-01-05",
        ),
        requested_claims=("industry_neutral_ic", "market_cap_neutral_ic", "style_neutral_ic"),
        factor_metrics={"raw_ic": 0.12},
    )

    assert gate.neutralization_status == "metric_missing"
    assert gate.raw_ic == 0.12
    assert gate.industry_neutral_ic is None
    assert gate.market_cap_neutral_ic is None
    assert gate.style_neutral_ic is None
    assert {item["reason"] for item in gate.blocked_claims} == {"neutralization_metric_missing"}


def test_s06_forbidden_boundaries_are_static_and_no_secret_leakage(monkeypatch) -> None:
    fake_secret = "CR011_S06_FAKE_SECRET_SHOULD_NOT_APPEAR"
    monkeypatch.setenv("CR011_S06_FAKE_SECRET", fake_secret)
    forbidden_modules = {
        "market_data.connectors",
        "market_data.runtime",
        "market_data.storage",
        "requests",
        "httpx",
        "aiohttp",
        "socket",
    }
    for path in TARGET_FILES:
        imports = imported_modules(path)
        assert not any(module == forbidden or module.startswith(forbidden + ".") for module in imports for forbidden in forbidden_modules)
        source = path.read_text(encoding="utf-8")
        assert "reports/experiment_17_21/factor_strategy_report.md" not in source
        assert "TUSHARE_TOKEN" not in source
        assert ".env" not in source

    gate = evaluate_neutralization_claims(
        build_exposure_availability_matrix(
            {
                "industry_classification": ReaderResult(status="required_missing", issues=[{"code": "industry_missing"}]),
                "market_cap": ReaderResult(status="required_missing", issues=[{"code": "market_cap_missing"}]),
                "float_market_cap": ReaderResult(status="required_missing", issues=[{"code": "float_market_cap_missing"}]),
                "style_exposure": ReaderResult(status="required_missing", issues=[{"code": "style_exposure_missing"}]),
            },
            factor_sample(),
        )
    )
    metadata = merge_exposure_claims_into_metadata({"allowed_claims": [], "blocked_claims": []}, gate)
    combined = json.dumps(metadata, ensure_ascii=False, default=str)
    assert fake_secret not in combined
    assert metadata["network_calls"] == 0
    assert metadata["lake_writes"] == 0
    assert metadata["credential_reads"] == 0
    assert metadata["legacy_data_operations"] == 0


def exposure_reader_results(
    tmp_path: Path,
    *,
    overrides: dict[str, ReaderResult] | None = None,
) -> dict[str, ReaderResult]:
    source = {
        "industry_classification": ReaderResult(status="available", frame=industry_frame()),
        "market_cap": ReaderResult(status="available", frame=market_cap_frame()),
        "style_exposure": ReaderResult(status="available", frame=style_exposure_frame()),
    }
    source.update(overrides or {})
    return read_exposure_inputs(
        ExposureInputRequest(
            lake_root=tmp_path / "lake",
            symbols=("AAA", "BBB"),
            start_date="2026-01-02",
            end_date="2026-01-05",
            style_factors=("beta", "size"),
        ),
        reader=source,
    )


def factor_sample() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"trade_date": "2026-01-02", "symbol": "AAA", "factor_value": 1.0},
            {"trade_date": "2026-01-05", "symbol": "BBB", "factor_value": -0.5},
        ]
    )


def industry_frame(*, pit_status: str = "pass") -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "symbol": "AAA",
                "effective_date": "2025-12-31",
                "available_at": "2026-01-01",
                "classification_standard": "SW",
                "industry_code": "801010",
                "pit_status": pit_status,
                "source_run_id": "industry-run",
            },
            {
                "symbol": "BBB",
                "effective_date": "2025-12-31",
                "available_at": "2026-01-01",
                "classification_standard": "SW",
                "industry_code": "801020",
                "pit_status": pit_status,
                "source_run_id": "industry-run",
            },
        ]
    )


def market_cap_frame(*, available_at: str = "2026-01-05") -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "trade_date": "2026-01-02",
                "symbol": "AAA",
                "market_cap": 100.0,
                "float_market_cap": 80.0,
                "available_at": available_at,
                "source_run_id": "cap-run",
            },
            {
                "trade_date": "2026-01-05",
                "symbol": "BBB",
                "market_cap": 120.0,
                "float_market_cap": 90.0,
                "available_at": available_at,
                "source_run_id": "cap-run",
            },
        ]
    )


def style_exposure_frame() -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for trade_date, symbol in (("2026-01-02", "AAA"), ("2026-01-05", "BBB")):
        for style_factor, value in (("beta", 1.1), ("size", -0.2)):
            rows.append(
                {
                    "trade_date": trade_date,
                    "symbol": symbol,
                    "style_factor": style_factor,
                    "exposure_value": value,
                    "model_version": "style-v1",
                    "available_at": "2026-01-05",
                    "source_run_id": "style-run",
                }
            )
    return pd.DataFrame(rows)


def pit_metadata() -> dict[str, Any]:
    return {
        "universe": {"is_pit_universe": True, "pit_status": "pass", "as_of_join_violation_count": 0},
        "lifecycle": {"lifecycle_status": "pass"},
        "as_of_join_violation_count": 0,
    }


def imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
    return modules
