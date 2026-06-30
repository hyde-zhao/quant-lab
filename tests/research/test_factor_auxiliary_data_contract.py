from __future__ import annotations

import ast
import json
from argparse import Namespace
from pathlib import Path
from typing import Any

import pandas as pd

from engine.research_dataset import (
    ResearchDataset,
    ResearchDatasetStatus,
    apply_auxiliary_data_contract,
    build_auxiliary_availability,
    evaluate_allowed_claims,
    merge_auxiliary_claims_into_metadata,
)
from experiments.run_factor_framework_exp15 import load_local_frames, run_factor_framework
from market_data.readers import AuxiliaryInputRequest, ReaderResult, read_auxiliary_inputs


TARGET_FILES = (
    Path("engine/research_dataset.py"),
    Path("market_data/readers.py"),
    Path("experiments/run_factor_framework_exp15.py"),
)


def test_t01_missing_industry_blocks_industry_claims() -> None:
    matrix = build_auxiliary_availability({}, {"capabilities": ["industry_classification"]})
    result = evaluate_allowed_claims(matrix, ["industry_neutral", "industry_attribution", "industry_group_ic"])

    blocked = {item["claim"]: item for item in result.blocked_claims}
    assert set(blocked) == {"industry_neutral", "industry_attribution", "industry_group_ic"}
    assert all(item["missing_capability"] == "industry_classification" for item in blocked.values())
    assert all(item["reason"] for item in blocked.values())
    assert "industry_neutral" not in result.allowed_claims


def test_t02_missing_market_cap_blocks_size_and_capacity_claims() -> None:
    matrix = build_auxiliary_availability({}, {"capabilities": ["market_cap", "liquidity"]})
    result = evaluate_allowed_claims(matrix, ["size_neutral", "market_cap_weighted_ic", "capacity_analysis"])

    blocked = {item["claim"]: item for item in result.blocked_claims}
    assert {"size_neutral", "market_cap_weighted_ic", "capacity_analysis"} <= set(blocked)
    assert blocked["size_neutral"]["missing_capability"] == "market_cap"
    assert blocked["capacity_analysis"]["missing_capability"] in {"market_cap", "liquidity"}
    assert "capacity_analysis" not in result.allowed_claims


def test_t03_missing_tradability_blocks_real_execution_claims() -> None:
    matrix = build_auxiliary_availability({}, {"capabilities": ["tradability"]})
    result = evaluate_allowed_claims(matrix, ["real_tradable_execution", "tradability_screened", "true_fillability"])

    blocked = {item["claim"]: item for item in result.blocked_claims}
    assert set(blocked) == {"real_tradable_execution", "tradability_screened", "true_fillability"}
    assert all(item["missing_capability"] == "tradability" for item in blocked.values())
    assert "framework_validation" in result.allowed_claims


def test_t04_missing_style_exposure_blocks_pure_alpha_claims() -> None:
    matrix = build_auxiliary_availability({}, {"capabilities": ["style_exposure"]})
    result = evaluate_allowed_claims(matrix, ["pure_alpha", "style_neutral", "risk_model_adjusted_alpha"])

    blocked = {item["claim"]: item for item in result.blocked_claims}
    assert set(blocked) == {"pure_alpha", "style_neutral", "risk_model_adjusted_alpha"}
    assert all(item["missing_capability"] == "style_exposure" for item in blocked.values())
    assert "pure_alpha" not in result.allowed_claims


def test_t05_partial_ohlcv_vwap_blocks_open_vwap_but_keeps_conservative_claims() -> None:
    matrix = build_auxiliary_availability(
        {
            "prices": {
                "status": "available",
                "observed_columns": ["trade_date", "symbol", "close", "volume"],
            }
        },
        {"capabilities": ["ohlcv_vwap"]},
    )
    result = evaluate_allowed_claims(
        matrix,
        ["vwap_execution", "open_execution", "intraday_range_factor", "close_only_exploration", "volume_only_exploration"],
        base_allowed_claims=["framework_validation", "close_only_exploration", "volume_only_exploration"],
    )

    assert matrix.entries["ohlcv_vwap"].status == "partial"
    assert "vwap" in matrix.entries["ohlcv_vwap"].missing_columns
    blocked = {item["claim"] for item in result.blocked_claims}
    assert {"vwap_execution", "open_execution", "intraday_range_factor"} <= blocked
    assert "close_only_exploration" in result.allowed_claims
    assert "volume_only_exploration" in result.allowed_claims


def test_t06_missing_adjustment_audit_blocks_corporate_action_audit_claims() -> None:
    matrix = build_auxiliary_availability(
        {
            "prices": {
                "status": "available",
                "observed_columns": ["trade_date", "symbol", "close", "adjustment_policy"],
            }
        },
        {"capabilities": ["adjustment_audit"]},
    )
    result = evaluate_allowed_claims(matrix, ["corporate_action_audited", "auditable_adjustment_chain"])

    blocked = {item["claim"]: item for item in result.blocked_claims}
    assert set(blocked) == {"corporate_action_audited", "auditable_adjustment_chain"}
    assert all(item["missing_capability"] == "adjustment_audit" for item in blocked.values())
    assert all("required_columns_missing" in item["reason"] for item in blocked.values())


def test_t07_metadata_merge_covers_every_blocked_reason_without_duplicates() -> None:
    matrix = build_auxiliary_availability({}, {"capabilities": ["industry_classification", "market_cap", "tradability"]})
    result = evaluate_allowed_claims(matrix, ["industry_neutral", "size_neutral", "real_tradable_execution"])
    metadata = merge_auxiliary_claims_into_metadata(
        {"known_limitations": [{"code": "existing"}], "allowed_claims": ["framework_validation"]},
        result,
    )
    merged_again = merge_auxiliary_claims_into_metadata(metadata, result)

    assert set(metadata["auxiliary_availability"]) == {"industry_classification", "market_cap", "tradability"}
    assert len(metadata["blocked_claims"]) == 3
    assert all({"claim", "missing_capability", "reason", "severity"} <= set(item) for item in metadata["blocked_claims"])
    limitation_claims = {item.get("claim") for item in metadata["known_limitations"] if isinstance(item, dict)}
    assert {"industry_neutral", "size_neutral", "real_tradable_execution"} <= limitation_claims
    assert len(json.dumps(merged_again["known_limitations"], ensure_ascii=False)) == len(
        json.dumps(metadata["known_limitations"], ensure_ascii=False)
    )


def test_t08_reader_helper_returns_typed_missing_and_never_auto_executes(tmp_path: Path) -> None:
    calls: list[str] = []

    def forbidden_reader(*_: Any, **__: Any) -> ReaderResult:
        calls.append("called")
        raise AssertionError("missing or unregistered auxiliary capability must not call reader")

    missing = read_auxiliary_inputs(AuxiliaryInputRequest(lake_root=None), reader=forbidden_reader)
    unknown = read_auxiliary_inputs(
        {"lake_root": tmp_path / "lake", "capabilities": ("industry_classification",)},
        reader=forbidden_reader,
    )

    assert calls == []
    assert all(result.status == "required_missing" for result in missing.values())
    assert unknown["industry_classification"].status == "unavailable"
    assert_all_auto_execute_false({**{key: value.remediation_spec for key, value in missing.items()}, "unknown": unknown["industry_classification"].remediation_spec})


def test_t09_security_boundaries_static_and_secret_safe(monkeypatch) -> None:
    fake_secret = "CR008_S06_FAKE_SECRET_SHOULD_NOT_APPEAR"
    monkeypatch.setenv("FACTOR_RESEARCH_FAKE_TOKEN", fake_secret)
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
        assert "reports/data_quality_report.csv" not in source
        assert "TUSHARE_TOKEN" not in source
        assert "market_data.connectors" not in source
        assert "market_data.runtime" not in source
        assert "market_data.storage" not in source

    matrix = build_auxiliary_availability({}, {"capabilities": ["industry_classification"]})
    result = evaluate_allowed_claims(matrix, ["industry_neutral"])
    combined = json.dumps(result.to_dict(), ensure_ascii=False, default=str)
    assert fake_secret not in combined


def test_t10_s04_s05_upstream_limitations_are_inherited_by_claim_gate() -> None:
    dataset = ResearchDataset(
        status=ResearchDatasetStatus.AVAILABLE_WITH_WARNINGS.value,
        metadata={
            "universe": {
                "universe_mode": "fixed_snapshot",
                "is_pit_universe": False,
                "pit_status": "non_pit_snapshot",
                "survivorship_bias_note": "fixed snapshot index_members; not PIT",
            },
            "label_window": {
                "label_status": "truncated",
                "label_available_end": "2026-01-07",
                "forward_return_horizon": 3,
            },
            "known_limitations": [],
            "allowed_claims": ["framework_validation", "pit_factor_research", "complete_forward_return_label"],
        },
        allowed_claims=["framework_validation", "pit_factor_research", "complete_forward_return_label"],
    )

    contracted = apply_auxiliary_data_contract(
        dataset,
        requirements={"capabilities": ["pit_universe", "label_quality"]},
        requested_claims=["pit_factor_research", "complete_forward_return_label"],
    )

    blocked = {item["claim"]: item for item in contracted.blocked_claims}
    assert set(blocked) == {"pit_factor_research", "complete_forward_return_label"}
    assert blocked["pit_factor_research"]["missing_capability"] == "pit_universe"
    assert blocked["complete_forward_return_label"]["missing_capability"] == "label_quality"
    assert "pit_factor_research" not in contracted.allowed_claims
    assert "complete_forward_return_label" not in contracted.allowed_claims


def test_t11_experiment_15_schema_report_and_summary_include_auxiliary_contract(tmp_path: Path) -> None:
    write_factor_dataset(tmp_path)

    result = run_factor_framework(args_for(tmp_path))

    schema = json.loads(result.factor_schema_path.read_text(encoding="utf-8"))
    summary = pd.read_csv(result.backtest_summary_path).iloc[0].to_dict()
    report = result.report_path.read_text(encoding="utf-8")

    assert schema["auxiliary_availability"]
    assert schema["allowed_claims"] == schema["research_input_metadata"]["allowed_claims"]
    blocked_claims = {item["claim"]: item for item in schema["blocked_claims"]}
    assert {
        "industry_neutral",
        "size_neutral",
        "real_tradable_execution",
        "pure_alpha",
        "capacity_analysis",
        "auditable_adjustment_chain",
    } <= set(blocked_claims)
    assert all(item["reason"] for item in blocked_claims.values())
    assert "raw_factor_performance" in schema["allowed_claims"]
    assert summary["auxiliary_blocked_claim_count"] >= 6
    assert "辅助数据合同" in report
    assert "Availability" in report
    assert "Blocked Claims" in report
    for unsupported_phrase in ("行业中性", "size neutral", "真实可成交", "纯 alpha", "容量可交易", "公司行动链路可审计"):
        assert unsupported_phrase not in report


def write_factor_dataset(root: Path, *, days: int = 45, symbols: tuple[str, ...] = ("AAA", "BBB", "CCC")) -> None:
    data_dir = root / "data"
    data_dir.mkdir(parents=True)
    dates = pd.date_range("2024-01-02", periods=days, freq="B").strftime("%Y-%m-%d").tolist()
    price_rows = []
    for day_index, trade_date in enumerate(dates):
        for symbol_index, symbol in enumerate(symbols):
            close = 10.0 + symbol_index * 3.0 + day_index * 0.05
            price_rows.append(
                {
                    "trade_date": trade_date,
                    "symbol": symbol,
                    "close": close,
                    "volume": 1000.0 + day_index * 10.0 + symbol_index * 100.0,
                    "amount": close * 1000.0,
                    "adjustment_policy": "qfq",
                }
            )
    members = pd.DataFrame(
        [
            {"symbol": symbol, "snapshot_date": dates[-1], "is_member": True, "index_code": "LOCAL"}
            for symbol in symbols
        ]
    )
    calendar = pd.DataFrame([{"trade_date": trade_date, "is_open": True} for trade_date in dates])
    pd.DataFrame(price_rows).to_parquet(data_dir / "prices.parquet", index=False)
    members.to_parquet(data_dir / "index_members.parquet", index=False)
    calendar.to_parquet(data_dir / "trade_calendar.parquet", index=False)


def args_for(root: Path, **overrides: Any) -> Namespace:
    values = {
        "data_dir": str(root / "data"),
        "lake_root": str(root / "lake"),
        "as_of": "2024-12-31T23:59:59+08:00",
        "quality_policy": "require_pass",
        "fixture_frames": load_local_frames(root / "data"),
        "output_dir": str(root / "reports" / "experiment_15"),
        "start_date": None,
        "end_date": None,
        "factors": ["momentum_5d", "volume_ratio_5d"],
        "strategy_factor": "momentum_5d",
        "rebalance_freq": 5,
        "top_fraction": 0.5,
        "initial_cash": 100_000.0,
        "preview_rows": 20,
    }
    values.update(overrides)
    return Namespace(**values)


def assert_all_auto_execute_false(value: Any) -> None:
    if isinstance(value, dict):
        if "auto_execute" in value:
            assert value["auto_execute"] is False
        for item in value.values():
            assert_all_auto_execute_false(item)
    elif isinstance(value, list | tuple):
        for item in value:
            assert_all_auto_execute_false(item)


def imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
    return modules
