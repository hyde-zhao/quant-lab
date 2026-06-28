from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pandas as pd

from engine.mature_multifactor_research import (
    build_mature_admission_package,
    build_stage3_factor_model_validation_report,
    stage3_artifacts,
    stage3_evidence_refs,
)


def _valid_stage3_frame() -> pd.DataFrame:
    dates = pd.bdate_range("2024-01-02", periods=12).strftime("%Y-%m-%d").tolist()
    rows = []
    for date_index, trade_date in enumerate(dates):
        for symbol_index in range(40):
            symbol = f"{symbol_index:06d}.SZ"
            score = (symbol_index - 20) / 20.0
            rows.append(
                {
                    "trade_date": trade_date,
                    "symbol": symbol,
                    "available_at": f"{trade_date}T15:30:00+08:00",
                    "momentum_20d": score,
                    "reversal_5d": score * 0.8,
                    "volatility_20d": score * 0.5,
                    "liquidity_adv20": score * 0.3,
                    "value_pb_inverse": score * 0.2,
                    "composite_score": score,
                    "label_return": score * 0.01 + 0.003,
                    "label_start_date": trade_date,
                    "label_end_date": pd.Timestamp(trade_date) + pd.Timedelta(days=1),
                    "industry_name": f"industry-{symbol_index % 5}",
                    "market_cap": 1_000_000_000 + symbol_index * 10_000_000,
                    "pb": 1.0 + symbol_index / 100.0,
                    "adv20_amount": 20_000_000 + symbol_index * 100_000,
                    "listed_days": 800,
                    "is_st": False,
                    "is_suspended": False,
                    "close": 10.0,
                }
            )
    return pd.DataFrame(rows)


def test_stage3_builds_factor_model_validation_report_for_mature_admission() -> None:
    valid = _valid_stage3_frame()
    turnover = pd.DataFrame(
        {
            "trade_date": sorted(valid["trade_date"].unique())[:-1],
            "net_forward_return": [0.006] * 11,
            "turnover": [0.2] * 11,
        }
    )

    report = build_stage3_factor_model_validation_report(
        "stage3-validation-unit",
        valid,
        turnover,
        cost_bps=15.0,
        label_horizon=20,
    )

    assert report.status in {"pass", "pass_with_risk"}
    assert report.short_feasibility["status"] == "not_applicable"
    assert any(item.gate_id == "factor_premium_significance" for item in report.gate_decisions)


def test_stage3_evidence_refs_include_factor_model_validation_report(tmp_path: Path) -> None:
    artifacts = stage3_artifacts("stage3-validation-unit", tmp_path / "research", tmp_path / "process")

    refs = stage3_evidence_refs(artifacts, "stage3-validation-unit")

    assert refs["factor_model_validation_report_ref"].endswith("/FACTOR-MODEL-VALIDATION-REPORT.json")


def test_stage3_mature_admission_blocks_insufficient_data_validation() -> None:
    report = SimpleNamespace(
        status="insufficient_data",
        gate_decisions=(),
        risk_warnings=(),
        blocked_reasons=(),
    )
    admission = build_mature_admission_package(
        "stage3-insufficient-data-unit",
        strategy_candidate=SimpleNamespace(admission="admission_ready", to_dict=lambda: {"strategy_id": "unit"}),
        signal_set=SimpleNamespace(signal_set_id="signal-set-unit"),
        evidence_index=SimpleNamespace(index_id="evidence-index-unit"),
        risk_policy=SimpleNamespace(policy_id="risk-policy-unit"),
        factor_specs=(SimpleNamespace(factor_id="momentum_20d", version="stage3-v1"),),
        portfolio=pd.DataFrame({"symbol": ["000001.SZ"]}),
        turnover=pd.DataFrame({"net_forward_return": [0.001]}),
        factor_model_validation_report=report,
        factor_model_validation_report_ref="artifact://stage3/unit/FACTOR-MODEL-VALIDATION-REPORT.json",
        limitations=(),
    )

    assert admission["status"] == "BLOCKED"
    assert admission["allowed_claims"] == []
    assert admission["blocked_reasons"][0]["gate_id"] == "factor_model_validation"
