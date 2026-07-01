from __future__ import annotations

from engine.backtest_production_contracts import (
    build_backtest_cost_risk_attribution_pack,
    build_backtest_report_pack,
    build_backtest_run_spec,
    validate_backtest_cost_risk_attribution_pack,
    validate_backtest_report_pack,
    validate_backtest_run_spec,
)
from engine.mature_multifactor_framework import (
    build_stage2_portfolio_risk_policy,
    build_stage2_research_evidence_index,
    build_stage2_signal_set,
)
from engine.mature_multifactor_research import (
    CR150_FORBIDDEN_OPERATION_COUNTS,
    CR150_LINKAGE_NODE_ORDER,
    build_cr150_multifactor_framework_completion_map,
    validate_cr150_multifactor_framework_completion_map,
)
from engine.multifactor_contracts import BLOCKED_CLAIMS_DEFAULT, FactorDirection, FactorSpec


def _factor_spec() -> FactorSpec:
    return FactorSpec(
        factor_id="momentum_20d",
        name="Momentum 20D",
        version="cr150-v1",
        direction=FactorDirection.POSITIVE,
        input_fields=("adjusted_close",),
        window=20,
        params={"lookback": 20},
        preprocessing={"winsorize": [0.01, 0.99], "zscore": True},
        universe={"mode": "pit_required"},
        availability_policy={"available_at": "decision_time", "policy": "no_lookahead"},
        data_lineage={
            "source_dataset": "catalog://prices/1.0/run_id=cr150-fixture",
            "research_input_schema": "research_input_v1",
            "evidence_refs": ["artifact://cr150/factor-spec/momentum_20d.json"],
        },
        blocked_claims=BLOCKED_CLAIMS_DEFAULT,
        failure_policy="fail_closed",
        auxiliary_requirements=("pit_universe", "label_window_gate"),
    )


def _completion_inputs() -> dict[str, object]:
    run_id = "cr150-local-linkage-fixture"
    signal_set = build_stage2_signal_set(
        strategy_id="stage3_mature_multifactor_v1",
        trade_date="2026-06-26",
        universe_ref="catalog://stock_basic+prices/1.0/run_id=cr150-fixture",
        scores={"000001.SZ": 0.8, "000002.SZ": 0.2},
        lineage_ref="artifact://cr150/factor-panel/factor_panel.parquet",
        evidence_refs=(
            "artifact://cr150/factor-panel/factor_panel.parquet",
            "artifact://cr150/ic-rankic/ic_rankic.csv",
            "artifact://cr150/layered-returns/layered_returns.csv",
        ),
        available_at="2026-06-26T15:00:00+08:00",
    )
    evidence_index = build_stage2_research_evidence_index(
        index_id="cr150-research-evidence-index",
        data_release_ref="catalog://market-data/stage3-data-update/2026-06-26",
        run_manifest_ref="artifact://cr150/run-manifest.json",
        metric_refs={
            "factor_panel_ref": "artifact://cr150/factor-panel/factor_panel.parquet",
            "label_window_ref": "artifact://cr150/label-window/label_window.parquet",
            "ic_rankic_ref": "artifact://cr150/ic-rankic/ic_rankic.csv",
            "layered_returns_ref": "artifact://cr150/layered-returns/layered_returns.csv",
            "turnover_ref": "artifact://cr150/turnover/turnover.csv",
            "exposure_ref": "artifact://cr150/exposure/exposure.csv",
        },
        lineage_refs={
            "pit_universe": "catalog://stock_basic+prices/1.0/run_id=cr150-fixture",
            "benchmark": "catalog://hs300_index/1.0/run_id=cr150-fixture#index_code=000985.SH",
        },
    )
    risk_policy = build_stage2_portfolio_risk_policy(
        policy_id="cr150-portfolio-risk-policy",
        top_n=80,
        max_weight=0.025,
        turnover_limit=0.2,
        fee_slippage_ref="artifact://cr150/cost/fee-slippage-model.json",
        industry_limit={"max_industry_active_weight": 0.12, "ref": "catalog://industry/1.0/run_id=cr150-fixture"},
        style_limit={"max_style_zscore": 0.8, "ref": "artifact://cr150/style-exposure.json"},
        capacity_assumption={"adv_participation_cap": 0.05, "ref": "catalog://liquidity/1.0/run_id=cr150-fixture"},
    )
    run_spec = build_backtest_run_spec(
        run_id=run_id,
        experiment_id="experiment-cr150-local-linkage",
        strategy_id="stage3_mature_multifactor_v1",
        dataset_snapshot_ref="catalog://market-data/stage3-data-update/2026-06-26",
        signal_set_ref=signal_set.signal_set_id,
        portfolio_policy_ref=risk_policy.policy_id,
        benchmark_ref="catalog://hs300_index/1.0/run_id=cr150-fixture#index_code=000985.SH",
        cost_model_ref="artifact://cr150/cost/cost-model.json",
        slippage_model_ref="artifact://cr150/cost/slippage-model.json",
        start_date="2021-01-01",
        end_date="2026-06-26",
        as_of="2026-07-01T15:31:58+08:00",
        code_version="git:cr150-local-test",
        backtest_config={"rebalance": "weekly", "top_n": 80, "max_weight": 0.025},
    )
    metrics = {
        "total_return": 0.12,
        "annual_return": 0.03,
        "max_drawdown": -0.08,
        "sharpe": 1.1,
        "turnover": 0.18,
        "final_nav": 1.12,
    }
    report_pack = build_backtest_report_pack(
        run_spec=run_spec,
        metrics=metrics,
        artifact_refs=("artifact://cr150/report/report.json", "artifact://cr150/report/report.md"),
    )
    attribution_pack = build_backtest_cost_risk_attribution_pack(
        run_spec=run_spec,
        metrics=metrics,
        cost_summary={"total_cost": 0.006, "commission_rate": 0.0003, "slippage_rate": 0.0005, "sell_tax_rate": 0.001},
        risk_summary={"volatility": 0.19, "tracking_error": 0.07, "beta": 0.9},
        attribution_refs=("artifact://cr150/attribution/cost-risk.json",),
        risk_policy_ref=risk_policy.policy_id,
    )
    admission_package = {
        "schema_version": "stage3_mature_strategy_admission_package_v1",
        "run_id": run_id,
        "status": "PASS",
        "signal_set_ref": signal_set.signal_set_id,
        "research_evidence_index_ref": evidence_index.index_id,
        "portfolio_risk_policy_ref": risk_policy.policy_id,
        "backtest_run_spec_ref": run_spec.config_hash,
        "backtest_report_pack_ref": report_pack.report_pack_ref,
        "cost_risk_attribution_ref": attribution_pack.attribution_ref,
        "not_qmt_authorization": True,
        "not_simulation_authorization": True,
        "not_live_authorization": True,
        "not_broker_order": True,
        "operation_counts": CR150_FORBIDDEN_OPERATION_COUNTS,
    }
    return {
        "run_id": run_id,
        "factor_specs": (_factor_spec(),),
        "factor_run_refs": ("artifact://cr150/factor-run/momentum_20d.json",),
        "factor_panel_ref": "artifact://cr150/factor-panel/factor_panel.parquet",
        "label_window_ref": "artifact://cr150/label-window/label_window.parquet",
        "signal_set": signal_set,
        "evidence_index": evidence_index,
        "risk_policy": risk_policy,
        "run_spec": run_spec,
        "report_pack": report_pack,
        "attribution_pack": attribution_pack,
        "admission_package": admission_package,
    }


def test_cr150_completion_map_links_multifactor_chain_without_runtime_authorization() -> None:
    items = _completion_inputs()
    assert validate_backtest_run_spec(items["run_spec"]) == ()
    assert validate_backtest_report_pack(items["report_pack"]) == ()
    assert validate_backtest_cost_risk_attribution_pack(items["attribution_pack"]) == ()

    completion = build_cr150_multifactor_framework_completion_map(
        run_id=str(items["run_id"]),
        factor_specs=items["factor_specs"],  # type: ignore[arg-type]
        factor_run_refs=items["factor_run_refs"],  # type: ignore[arg-type]
        factor_panel_ref=str(items["factor_panel_ref"]),
        label_window_ref=str(items["label_window_ref"]),
        signal_set=items["signal_set"],  # type: ignore[arg-type]
        evidence_index=items["evidence_index"],  # type: ignore[arg-type]
        risk_policy=items["risk_policy"],  # type: ignore[arg-type]
        backtest_run_spec=items["run_spec"],
        backtest_report_pack=items["report_pack"],
        cost_risk_attribution_pack=items["attribution_pack"],
        admission_package=items["admission_package"],  # type: ignore[arg-type]
        operation_counts=CR150_FORBIDDEN_OPERATION_COUNTS,
        external_basis_refs={
            "qlib": "https://github.com/microsoft/qlib",
            "alphalens": "https://github.com/quantopian/alphalens",
            "pyfolio_reloaded": "https://github.com/stefan-jansen/pyfolio-reloaded",
        },
    )
    rebuilt = build_cr150_multifactor_framework_completion_map(
        run_id=str(items["run_id"]),
        factor_specs=items["factor_specs"],  # type: ignore[arg-type]
        factor_run_refs=items["factor_run_refs"],  # type: ignore[arg-type]
        factor_panel_ref=str(items["factor_panel_ref"]),
        label_window_ref=str(items["label_window_ref"]),
        signal_set=items["signal_set"],  # type: ignore[arg-type]
        evidence_index=items["evidence_index"],  # type: ignore[arg-type]
        risk_policy=items["risk_policy"],  # type: ignore[arg-type]
        backtest_run_spec=items["run_spec"],
        backtest_report_pack=items["report_pack"],
        cost_risk_attribution_pack=items["attribution_pack"],
        admission_package=items["admission_package"],  # type: ignore[arg-type]
        operation_counts=CR150_FORBIDDEN_OPERATION_COUNTS,
        external_basis_refs={
            "qlib": "https://github.com/microsoft/qlib",
            "alphalens": "https://github.com/quantopian/alphalens",
            "pyfolio_reloaded": "https://github.com/stefan-jansen/pyfolio-reloaded",
        },
    )

    assert completion["status"] == "PASS"
    assert tuple(completion["node_order"]) == CR150_LINKAGE_NODE_ORDER
    assert tuple(node["node_id"] for node in completion["nodes"]) == CR150_LINKAGE_NODE_ORDER
    assert completion["hash_chain"]["chain_hash"] == rebuilt["hash_chain"]["chain_hash"]
    assert completion["operation_counts"] == CR150_FORBIDDEN_OPERATION_COUNTS
    assert set(completion["deferred_routes"]) >= {
        "machine_learning",
        "event_driven",
        "runtime_live_trading",
        "nas_sync",
        "external_framework_execution",
    }
    assert validate_cr150_multifactor_framework_completion_map(completion) == ()


def test_cr150_completion_map_blocks_missing_report_pack_linkage() -> None:
    items = _completion_inputs()

    completion = build_cr150_multifactor_framework_completion_map(
        run_id=str(items["run_id"]),
        factor_specs=items["factor_specs"],  # type: ignore[arg-type]
        factor_run_refs=items["factor_run_refs"],  # type: ignore[arg-type]
        factor_panel_ref=str(items["factor_panel_ref"]),
        label_window_ref=str(items["label_window_ref"]),
        signal_set=items["signal_set"],  # type: ignore[arg-type]
        evidence_index=items["evidence_index"],  # type: ignore[arg-type]
        risk_policy=items["risk_policy"],  # type: ignore[arg-type]
        backtest_run_spec=items["run_spec"],
        backtest_report_pack=None,
        cost_risk_attribution_pack=items["attribution_pack"],
        admission_package=items["admission_package"],  # type: ignore[arg-type]
        operation_counts=CR150_FORBIDDEN_OPERATION_COUNTS,
    )

    assert completion["status"] == "BLOCKED"
    assert any(gap["node_id"] == "backtest_report_pack" for gap in completion["linkage_gaps"])
    issues = validate_cr150_multifactor_framework_completion_map(completion)
    assert any(issue["code"] == "cr150_completion_required_node_not_passed" for issue in issues)
