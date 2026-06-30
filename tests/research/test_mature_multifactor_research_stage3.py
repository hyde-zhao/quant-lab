from __future__ import annotations

from pathlib import Path

import pandas as pd

from engine.factor_registry import STAGE3_MATURE_MULTIFACTOR_FACTOR_IDS, stage3_factor_catalog_entries
from engine.multifactor_contracts import validate_factor_spec
from engine.mature_multifactor_research import (
    FORBIDDEN_OPERATION_COUNTS,
    add_cross_sectional_scores,
    apply_composite_score_policy,
    build_factor_specs,
    build_latest_signal_rows,
    build_risk_policy,
    build_runner_offline_preflight,
    build_signal_set,
    compute_ic_rankic,
    compute_portfolio_exposure,
    stage3_artifacts,
    _read_dataset,
)


def _scored_frame(rows: int = 30) -> pd.DataFrame:
    frame = pd.DataFrame(
        {
            "trade_date": ["2026-05-28"] * rows,
            "symbol": [f"{index:06d}.SZ" for index in range(rows)],
            "momentum_20d": [index / 100.0 for index in range(rows)],
            "reversal_5d": [(rows - index) / 100.0 for index in range(rows)],
            "volatility_20d": [-index / 1000.0 for index in range(rows)],
            "liquidity_adv20": [16.0 + index / 100.0 for index in range(rows)],
            "value_pb_inverse": [-1.0 - index / 100.0 for index in range(rows)],
            "label_return": [index / 1000.0 for index in range(rows)],
            "eligible": [True] * rows,
        }
    )
    return add_cross_sectional_scores(
        frame,
        factor_columns=("momentum_20d", "reversal_5d", "volatility_20d", "liquidity_adv20", "value_pb_inverse"),
    )


def test_stage3_scores_are_cross_sectional_and_finite() -> None:
    scored = _scored_frame()

    assert scored["composite_score"].notna().all()
    assert scored["momentum_20d_z"].notna().all()
    assert abs(float(scored["momentum_20d_z"].mean())) < 1e-12


def test_stage3_composite_score_policy_can_use_explicit_factor_weights() -> None:
    scored = _scored_frame()

    weighted = apply_composite_score_policy(
        scored,
        factor_columns=STAGE3_MATURE_MULTIFACTOR_FACTOR_IDS,
        factor_weights={"value_pb_inverse": -1.0},
    )

    assert weighted["composite_score"].equals(-scored["value_pb_inverse_z"])


def test_stage3_portfolio_exposure_uses_real_weighted_market_cap() -> None:
    portfolio = pd.DataFrame(
        {
            "trade_date": ["2026-05-28", "2026-05-28"],
            "industry_name": ["A", "B"],
            "weight": [0.25, 0.75],
            "market_cap": [100.0, 10000.0],
            "adv20_amount": [30_000_000.0, 40_000_000.0],
        }
    )

    exposure = compute_portfolio_exposure(portfolio)

    assert exposure.loc[0, "top_industry"] == "B"
    assert exposure.loc[0, "top_industry_weight"] == 0.75
    assert exposure.loc[0, "weighted_log_market_cap"] > 0
    assert exposure.loc[0, "median_adv20_amount"] == 35_000_000.0


def test_stage3_rank_ic_does_not_require_scipy() -> None:
    scored = _scored_frame()

    ic = compute_ic_rankic(scored, factor_columns=("momentum_20d", "composite_score"))

    assert set(ic["factor_id"]) == {"momentum_20d", "composite_score"}
    assert ic["rank_ic"].notna().all()


def test_stage3_factor_specs_are_sourced_from_factor_registry() -> None:
    specs = build_factor_specs("stage3-unit", {})
    catalog_entries = {entry.factor_id: entry for entry in stage3_factor_catalog_entries()}

    assert tuple(spec.factor_id for spec in specs) == STAGE3_MATURE_MULTIFACTOR_FACTOR_IDS
    for spec in specs:
        entry = catalog_entries[spec.factor_id]
        assert spec.name == entry.name
        assert spec.params["catalog_status"] == "stage3_active"
        assert spec.params["calculator_status"].startswith("runner_local:")
        assert spec.data_lineage["source_of_truth"] == "project_factor_registry"
        assert validate_factor_spec(spec).passed


def test_stage3_runner_offline_preflight_is_not_runtime_authorization(tmp_path: Path) -> None:
    run_id = "stage3-unit"
    artifacts = stage3_artifacts(run_id, tmp_path / "research", tmp_path / "process")
    scored = _scored_frame()
    latest = build_latest_signal_rows(scored, "2026-05-28", top_n=10)
    signal_set = build_signal_set(run_id, latest, artifacts, "2026-05-28")
    risk_policy = build_risk_policy(
        run_id,
        top_n=10,
        max_weight=0.2,
        turnover_limit=0.35,
        min_adv_amount=20_000_000.0,
        fee_slippage_ref="artifact://stage3-unit/runner-preflight",
    )

    preflight = build_runner_offline_preflight(
        run_id,
        signal_set=signal_set,
        risk_policy=risk_policy,
        latest_signals=latest,
        artifacts=artifacts,
        top_n=10,
        max_weight=0.2,
    )

    assert preflight["status"] == "PASS"
    assert preflight["not_runtime_authorization"] is True
    assert preflight["not_gateway_or_qmt_operation"] is True
    assert preflight["operation_counts"] == FORBIDDEN_OPERATION_COUNTS
    assert preflight["target_portfolio_result"]["target_portfolio"]["not_authorization"] is True


def test_stage3_reader_prefers_complete_canonical_root_over_catalog_file(tmp_path: Path) -> None:
    lake = tmp_path / "lake"
    root = lake / "canonical" / "sample" / "1.0" / "run_id=new"
    old = lake / "canonical" / "sample" / "1.0" / "run_id=old"
    root.mkdir(parents=True)
    old.mkdir(parents=True)
    pd.DataFrame({"trade_date": ["2026-01-02"], "symbol": ["000001.SZ"], "value": [2]}).to_parquet(root / "part.parquet", index=False)
    pd.DataFrame({"trade_date": ["2025-01-02"], "symbol": ["000001.SZ"], "value": [1]}).to_parquet(old / "part.parquet", index=False)
    catalog = {"sample": {"canonical_path": "canonical/sample/1.0/run_id=old/part.parquet"}}

    frame = _read_dataset(
        lake,
        catalog,
        "sample",
        columns=("trade_date", "symbol", "value"),
        start="2026-01-01",
        end="2026-12-31",
    )

    assert frame.to_dict("records") == [{"trade_date": "2026-01-02", "symbol": "000001.SZ", "value": 2}]
