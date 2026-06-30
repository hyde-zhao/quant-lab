from __future__ import annotations

from datetime import date
import json
import logging

import pandas as pd
import pytest

from engine.backtest import BacktestConfig, build_rebalance_schedule, run_backtest
from engine.bias_audit import AuditComparableRun, run_bias_audit
from engine.candidates import select_candidates
from engine.charts import ChartGenerationError, generate_backtest_charts, generate_report_charts, generate_sweep_charts
from engine.contracts import STANDARD_PARQUET_FILES
from engine.data_loader import DataContractError, LoaderConfig, load_backtest_data
from engine.diagnostics import LOGGER_NAME
from engine.data_prep import DataPrepSourceRegistryError, plan_batches
from engine.events import EventStore, EventStoreError
from engine.portfolio import PortfolioConfig, RebalanceSignal, run_portfolio
from engine.reporting import sanitize_tabular_text
from engine.scanner import SweepParameter, build_default_grid, run_parameter_sweep
from engine.source_registry import SourceRegistryError, require_resolved_registry_key
from engine.trade_status import TradeStatusError, load_trade_status
from engine.trading_constraints import LimitPriceProvider, TradingConstraintError
from engine.universe import UniverseError, load_universe
from experiments.run_momentum_rsi_backtest_exp06_07 import build_equal_weight_benchmark
from experiments.run_strategy_parameter_sensitivity_exp09 import calculate_win_rate, run_queue_scan
from experiments.run_out_of_sample_overfit_risk_exp10 import rank_overfit_risk
from experiments.run_market_regime_segments_exp12 import MarketSegment, build_summary_row
from experiments.run_strategy_comparison_exp13 import build_comparison_table, calculate_cost_erosion, calculate_profit_loss_ratio
from strategies.base import StrategyInput, run_strategy
from strategies.momentum import MomentumConfig, build_momentum_targets
from strategies.rsi import build_rsi_targets


def write_story004_manifest_and_quality(data_dir, reports_dir, *, quality_status="pass", dataset_status="available"):
    manifest_dir = data_dir / "manifests"
    manifest_dir.mkdir(parents=True, exist_ok=True)
    (manifest_dir / "data_prep_manifest.jsonl").write_text(
        '{"run_id":"run-1","status":"success"}\n',
        encoding="utf-8",
    )
    (reports_dir / "data_quality_report.csv").write_text(
        "dataset,quality_status,fetch_status,dataset_status,missing_rate,failed_batch_count,"
        "manifest_run_id,coverage_denominator,denominator_mode,thresholds_json,input_config_hash,"
        "last_successful_update_at,data_freshness_trade_days,data_freshness_calendar_days\n"
        f"overall,{quality_status},success,{dataset_status},0,0,run-1,4,"
        'open_trade_dates_in_requested_range_x_target_symbols,"{}",hash-1,2020-01-03,0,0\n',
        encoding="utf-8",
    )


def test_story_004_loader_reads_offline_parquet_and_quality_gate(tmp_path):
    data_dir = tmp_path / "data"
    reports_dir = tmp_path / "reports"
    data_dir.mkdir()
    reports_dir.mkdir()
    prices = pd.DataFrame(
        {
            "trade_date": ["2020-01-02", "2020-01-03", "2020-01-02", "2020-01-03"],
            "symbol": ["000001", "000001", "000002", "000002"],
            "close": [10.0, 11.0, 20.0, 19.0],
            "adjustment_policy": ["qfq", "qfq", "qfq", "qfq"],
        }
    )
    members = pd.DataFrame({"symbol": ["000001", "000002"], "is_pit_universe": [False, False]})
    calendar = pd.DataFrame({"trade_date": ["2020-01-02", "2020-01-03"], "is_open": [True, True]})
    for dataset, frame in {"prices": prices, "index_members": members, "trade_calendar": calendar}.items():
        frame.to_parquet(data_dir / STANDARD_PARQUET_FILES[dataset], index=False)
    write_story004_manifest_and_quality(data_dir, reports_dir)
    loaded = load_backtest_data(
        LoaderConfig(
            data_dir=data_dir,
            quality_report_path=reports_dir / "data_quality_report.csv",
            start_date="2020-01-02",
            end_date="2020-01-03",
        )
    )
    assert loaded.universe == ["000001", "000002"]
    assert list(loaded.close_df.columns) == ["000001", "000002"]
    assert loaded.metadata["quality_status"] == "pass"
    assert loaded.metadata["dataset_status"] == "available"
    assert loaded.metadata["quality_policy"] == "fail_on_warn_or_fail"
    assert loaded.metadata["allow_warn"] is False
    assert loaded.metadata["quality_source"] == "csv_report"


def test_story_004_loader_missing_quality_report_fails(tmp_path):
    with pytest.raises(DataContractError):
        load_backtest_data(LoaderConfig(data_dir=tmp_path, start_date="2020-01-01", end_date="2020-01-02"))


def test_story_005_portfolio_accounting_identity_and_t1_buy():
    idx = [date(2020, 1, 2), date(2020, 1, 3), date(2020, 1, 6)]
    close_df = pd.DataFrame({"000001": [10.0, 11.0, 12.0]}, index=idx)
    result = run_portfolio(
        close_df,
        [RebalanceSignal(signal_date=idx[0], execution_date=idx[1], target_symbols=["000001"])],
        PortfolioConfig(initial_cash=1000.0, commission_rate=0.0, slippage_rate=0.0, sell_tax_rate=0.0),
    )
    assert result.trades[0].status == "filled"
    assert result.trades[0].execution_date == idx[1]
    for snapshot in result.daily_snapshots:
        assert snapshot.total_value == pytest.approx(snapshot.cash + snapshot.position_value)


def test_story_006_schedule_boundaries_2019_2025():
    calendar = [item.date() for item in pd.bdate_range("2019-01-01", "2025-12-31")]
    schedule = build_rebalance_schedule(calendar, lookback_days=20, rebalance_freq=5)
    assert schedule[0].signal_date == calendar[20]
    assert schedule[0].execution_date == calendar[21]
    assert schedule[-1].execution_date <= date(2025, 12, 31)
    assert all(item.execution_date > item.signal_date for item in schedule)


def test_story_006_run_backtest_returns_metrics():
    idx = [item.date() for item in pd.bdate_range("2020-01-01", periods=12)]
    close_df = pd.DataFrame({"A": range(10, 22), "B": range(20, 8, -1)}, index=idx)
    result = run_backtest(close_df, BacktestConfig(lookback_days=3, rebalance_freq=3, top_fraction=0.5))
    assert result.schedule
    assert "max_drawdown" in result.metrics


def test_story_007_008_scanner_candidates_and_formula_sanitize():
    assert len(build_default_grid()) == 60
    assert sanitize_tabular_text("=cmd") == "'=cmd"
    idx = [item.date() for item in pd.bdate_range("2020-01-01", periods=10)]
    close_df = pd.DataFrame({"A": range(10, 20), "B": range(20, 10, -1)}, index=idx)
    sweep = run_parameter_sweep(
        close_df,
        backtest_runner=lambda _frame, _cfg: type(
            "FakeBacktest",
            (),
            {
                "metrics": {
                    "cumulative_return": 0.1,
                    "annual_return": 0.2,
                    "max_drawdown": -0.05,
                    "sharpe": 1.2,
                    "turnover": 0.3,
                },
                "metadata": {"quality_status": "pass"},
            },
        )(),
    )
    assert sweep.success_count == 60
    selected = select_candidates(sweep.rows)
    assert 1 <= len(selected.rows) <= 4
    assert selected.rows[0]["selection_reason"]


def test_story_009_010_011_unresolved_registry_fail_fast(tmp_path):
    pit_spec = require_resolved_registry_key("index_members_pit")
    assert (pit_spec.source, pit_spec.interface) == ("tushare", "index_weight")
    with pytest.raises(DataPrepSourceRegistryError):
        plan_batches(
            "UNRESOLVED",
            "UNRESOLVED",
            {"target_dataset": "index_members", "is_pit_universe": True},
        )
    missing = tmp_path / "missing.csv"
    with pytest.raises(TradeStatusError):
        load_trade_status(missing)
    with pytest.raises(TradingConstraintError):
        LimitPriceProvider(pd.DataFrame())
    events = EventStore(pd.DataFrame({"event_date": []}), enabled=True)
    assert events.frame.empty


def test_story_012_bias_audit_object_first_and_rank_warning():
    baseline = [
        AuditComparableRun("base-1", {"strategy_name": "momentum", "lookback": 5}, {"total_return": 0.1, "max_drawdown": -0.2, "sharpe": 1.0})
    ]
    enhanced = [
        AuditComparableRun("enh-1", {"strategy_name": "momentum", "lookback": 5}, {"total_return": 0.12, "max_drawdown": -0.1, "sharpe": 1.1})
    ]
    result = run_bias_audit(baseline, enhanced)
    assert result.rows[0]["return_delta"] == pytest.approx(0.02)
    assert result.rows[0]["candidate_rank_delta_status"] == "not_available"
    assert result.warnings


def test_story_013_rsi_macd_strategy_contracts():
    idx = [item.date() for item in pd.bdate_range("2020-01-01", periods=60)]
    close_df = pd.DataFrame({"A": range(10, 70), "B": range(70, 10, -1)}, index=idx)
    rsi = run_strategy("rsi", StrategyInput(close_df, idx[-1], {"period": 14, "top_fraction": 0.5}))
    macd_idx = [item.date() for item in pd.bdate_range("2020-01-01", periods=80)]
    macd_close = pd.DataFrame(
        {
            "A": ([100.0] * 30) + [float(value) for value in range(100, 80, -1)] + [float(value) for value in range(80, 110)],
            "B": [float(value) for value in range(100, 180)],
        },
        index=macd_idx,
    )
    macd = run_strategy("macd", StrategyInput(macd_close, macd_idx[54], {"fast": 12, "slow": 26, "signal": 9, "top_fraction": 1.0}))
    assert rsi.target_symbols
    assert macd.target_symbols == ["A"]
    with pytest.raises(ValueError):
        run_strategy("macd", StrategyInput(close_df, idx[-1], {"fast": 26, "slow": 12}))


def test_momentum_sell_buffer_keeps_holdings_until_rank_boundary():
    idx = [item.date() for item in pd.bdate_range("2020-01-01", periods=4)]
    close_df = pd.DataFrame(
        {
            "A": [10.0, 12.0, 13.0, 14.0],
            "B": [10.0, 11.0, 12.0, 13.0],
            "C": [10.0, 10.5, 11.0, 11.5],
            "D": [10.0, 10.1, 10.2, 10.3],
        },
        index=idx,
    )
    signal = build_momentum_targets(
        close_df,
        idx[-1],
        MomentumConfig(lookback_days=3, top_fraction=0.25, sell_buffer=1.0),
        current_holdings=["B"],
    )
    assert signal.target_symbols == ["A", "B"]


def test_rsi_targets_buy_oversold_and_sell_overbought():
    rsi_today = pd.Series({"KEEP": 55.0, "SELL": 75.0, "BUY": 20.0, "WAIT": 45.0})
    targets = build_rsi_targets(
        rsi_today,
        top_fraction=1.0,
        oversold=30,
        overbought=70,
        current_holdings=["KEEP", "SELL"],
    )
    assert targets == ["BUY", "KEEP"]


def test_experiment_benchmark_equal_weight_buy_hold_metrics():
    idx = [item.date() for item in pd.bdate_range("2020-01-01", periods=3)]
    close_df = pd.DataFrame({"A": [10.0, 11.0, 12.0], "B": [20.0, 20.0, 20.0]}, index=idx)
    benchmark = build_equal_weight_benchmark(close_df, initial_cash=1000.0)
    equity = benchmark["equity"]

    assert benchmark["name"] == "equal_weight_buy_hold_same_universe"
    assert equity["nav"].iloc[-1] == pytest.approx(1.1)
    assert benchmark["metrics"]["total_return"] == pytest.approx(0.1)


def test_experiment_09_win_rate_and_queue_scan():
    returns = pd.Series([0.1, -0.05, 0.0, 0.02])
    assert calculate_win_rate(returns) == pytest.approx(2 / 3)

    idx = [item.date() for item in pd.bdate_range("2020-01-01", periods=20)]
    close_df = pd.DataFrame({"A": range(10, 30), "B": range(30, 10, -1)}, index=idx)
    tasks = [
        {
            "strategy_name": "momentum",
            "lookback": 3,
            "rebalance_freq": 3,
            "period": "",
            "oversold": "",
            "overbought": "",
            "fast": "",
            "slow": "",
            "signal": "",
            "config": BacktestConfig(lookback_days=3, rebalance_freq=3, top_fraction=0.5),
        }
    ]
    rows = run_queue_scan(close_df, {}, tasks)
    assert len(rows) == 1
    assert rows[0]["status"] == "success"
    assert rows[0]["win_rate"] is not None


def test_experiment_10_rank_overfit_risk_orders_by_decay():
    rows = [
        {"strategy_name": "A", "decay": 0.1},
        {"strategy_name": "B", "decay": 0.3},
        {"strategy_name": "C", "decay": -0.1},
    ]
    ranked = rank_overfit_risk(rows)

    assert [row["strategy_name"] for row in ranked] == ["B", "A", "C"]
    assert [row["overfit_risk"] for row in ranked] == ["高", "中", "低"]


def test_experiment_12_summary_selects_best_strategy_and_skips_empty_segment():
    segment = MarketSegment("seg", "测试段", "震荡", "n/a", "fixture", "2020-01-01", "2020-01-31")
    idx = [item.date() for item in pd.bdate_range("2020-01-01", periods=3)]
    close_df = pd.DataFrame({"A": [1, 2, 3]}, index=idx)
    details = [
        {"strategy_name": "momentum", "status": "success", "total_return": 0.1},
        {"strategy_name": "rsi", "status": "success", "total_return": 0.2},
        {"strategy_name": "macd", "status": "failed", "total_return": ""},
    ]
    row = build_summary_row(segment, close_df, details)
    skipped = build_summary_row(segment, close_df.iloc[:0], [
        {"strategy_name": "momentum", "status": "skipped_no_local_data", "total_return": ""},
        {"strategy_name": "rsi", "status": "skipped_no_local_data", "total_return": ""},
        {"strategy_name": "macd", "status": "skipped_no_local_data", "total_return": ""},
    ])

    assert row["best_strategy"] == "rsi"
    assert row["status"] == "partial"
    assert skipped["status"] == "skipped_no_local_data"


def test_experiment_13_profit_loss_ratio_cost_erosion_and_table():
    returns = pd.Series([0.02, -0.01, 0.03, -0.02, 0.0])
    assert calculate_profit_loss_ratio(returns) == pytest.approx(0.025 / 0.015)
    assert calculate_profit_loss_ratio(pd.Series([0.01, 0.0])) is None
    assert calculate_cost_erosion(0.10, 0.08) == pytest.approx(0.2)
    assert calculate_cost_erosion(-0.10, -0.12) == pytest.approx(0.2)
    assert calculate_cost_erosion(0.0, -0.01) is None

    rows = build_comparison_table(
        {"annual_return": 0.05, "sharpe": 0.8, "max_drawdown": -0.2},
        [
            {
                "strategy_name": "momentum",
                "annual_return_no_cost": 0.10,
                "annual_return_with_cost": 0.08,
                "sharpe": 1.0,
                "max_drawdown": -0.3,
                "win_rate": 0.5,
                "profit_loss_ratio": 1.2,
                "monthly_trade_count": 2.0,
                "cost_erosion": 0.2,
            },
            {
                "strategy_name": "rsi",
                "annual_return_no_cost": 0.06,
                "annual_return_with_cost": 0.05,
                "sharpe": 0.9,
                "max_drawdown": -0.25,
                "win_rate": 0.48,
                "profit_loss_ratio": 1.1,
                "monthly_trade_count": 1.0,
                "cost_erosion": 0.1667,
            },
            {
                "strategy_name": "macd",
                "annual_return_no_cost": 0.04,
                "annual_return_with_cost": 0.02,
                "sharpe": 0.7,
                "max_drawdown": -0.35,
                "win_rate": 0.45,
                "profit_loss_ratio": 0.9,
                "monthly_trade_count": 8.0,
                "cost_erosion": 0.5,
            },
        ],
        {"momentum": 0.3, "rsi": 0.2, "macd": 0.1},
    )
    assert rows[0]["对比维度"] == "年化收益率"
    assert rows[1]["动量"] == pytest.approx(0.05)
    assert rows[7]["MACD"] == pytest.approx(0.1)
    assert rows[-1]["RSI"] == "震荡市"


def test_report_charts_generate_png_and_markdown_index(tmp_path):
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()
    dates = pd.bdate_range("2020-01-01", periods=45)
    nav = [1.0 + index * 0.002 for index in range(len(dates))]
    equity = pd.DataFrame(
        {
            "trade_date": dates.strftime("%Y-%m-%d"),
            "total_value": [1_000_000 * value for value in nav],
            "nav": nav,
            "drawdown": [0.0 if index < 20 else -0.01 for index in range(len(dates))],
            "turnover_amount": [index * 1000.0 for index in range(len(dates))],
            "holding_count": [0 if index < 5 else 2 for index in range(len(dates))],
        }
    )
    equity.to_csv(reports_dir / "equity_curve.csv", index=False)
    sweep = pd.DataFrame(
        [
            {
                "run_id": "sweep-001",
                "strategy_name": "momentum",
                "lookback": lookback,
                "rebalance_freq": freq,
                "fraction": 0.1,
                "status": "success",
                "sharpe": 1.0 + lookback / 100 + freq / 100,
                "cumulative_return": 0.1 + lookback / 1000 + freq / 1000,
            }
            for lookback in (5, 10)
            for freq in (5, 10)
        ]
    )
    sweep.to_csv(reports_dir / "momentum_param_sweep_local.csv", index=False)
    candidates = pd.DataFrame(
        [
            {
                "candidate_id": "CAND-01",
                "local_sharpe": 1.2,
                "local_cumulative_return": 0.2,
                "local_max_drawdown": -0.08,
                "local_turnover": 0.5,
            },
            {
                "candidate_id": "CAND-02",
                "local_sharpe": 0.9,
                "local_cumulative_return": 0.15,
                "local_max_drawdown": -0.05,
                "local_turnover": 0.3,
            },
        ]
    )
    candidates.to_csv(reports_dir / "momentum_candidates_local.csv", index=False)

    artifacts = generate_report_charts(reports_dir)

    assert len(artifacts) >= 7
    assert (reports_dir / "charts" / "index.md").exists()
    assert "![Equity Curve]" in (reports_dir / "charts" / "index.md").read_text(encoding="utf-8")
    for filename in (
        "equity_curve.png",
        "drawdown.png",
        "param_heatmap_sharpe_top10.png",
        "param_heatmap_cumulative_return_top10.png",
        "candidates_compare.png",
    ):
        assert (reports_dir / "charts" / filename).stat().st_size > 0
    assert (reports_dir / "equity_curve.csv").read_text(encoding="utf-8") == equity.to_csv(index=False)


def test_report_charts_accept_dataframe_records_and_readable_failures(tmp_path):
    reports_dir = tmp_path / "reports"
    charts_dir = reports_dir / "charts"
    equity = pd.DataFrame(
        {
            "trade_date": ["2020-01-02", "2020-01-03", "2020-01-06"],
            "total_value": [1_000_000, 1_010_000, 1_005_000],
        }
    )

    backtest_artifacts = generate_backtest_charts(equity, charts_dir)

    assert {artifact.kind for artifact in backtest_artifacts}.issuperset({"backtest_equity", "backtest_drawdown"})
    assert (charts_dir / "equity_curve.png").stat().st_size > 0
    assert (charts_dir / "drawdown.png").stat().st_size > 0

    sweep_rows = [
        {
            "lookback_days": lookback,
            "rebalance_freq": freq,
            "top_fraction": 0.2,
            "status": "success",
            "sharpe": 1.0 + lookback / 100 + freq / 100,
            "annual_return": 0.2 + lookback / 1000 + freq / 1000,
        }
        for lookback in (5, 10)
        for freq in (5, 10)
    ]
    sweep_artifacts = generate_sweep_charts(sweep_rows, charts_dir, metrics=("sharpe", "annual_return"))

    assert len(sweep_artifacts) == 2
    assert (charts_dir / "param_heatmap_sharpe_top20.png").stat().st_size > 0
    assert (charts_dir / "param_heatmap_annual_return_top20.png").stat().st_size > 0
    with pytest.raises(ChartGenerationError, match="缺少字段: status"):
        generate_sweep_charts([{"lookback": 5, "rebalance_freq": 5, "fraction": 0.1, "sharpe": 1.0}], charts_dir)
    with pytest.raises(ChartGenerationError, match="没有 status=success"):
        generate_sweep_charts(
            [
                {
                    "lookback": 5,
                    "rebalance_freq": 5,
                    "fraction": 0.1,
                    "status": "failed",
                    "sharpe": 1.0,
                    "cumulative_return": 0.1,
                }
            ],
            charts_dir,
        )


def test_t_logging_minimal_01_cli_diagnostics(caplog, tmp_path):
    caplog.set_level(logging.INFO, logger=LOGGER_NAME)

    data_dir = tmp_path / "data"
    reports_dir = tmp_path / "reports"
    data_dir.mkdir()
    reports_dir.mkdir()
    prices = pd.DataFrame(
        {
            "trade_date": ["2020-01-02", "2020-01-03", "2020-01-02", "2020-01-03"],
            "symbol": ["000001", "000001", "000002", "000002"],
            "close": [10.0, 11.0, 20.0, 19.0],
            "adjustment_policy": ["qfq", "qfq", "qfq", "qfq"],
        }
    )
    members = pd.DataFrame({"symbol": ["000001", "000002"], "is_pit_universe": [False, False]})
    calendar = pd.DataFrame({"trade_date": ["2020-01-02", "2020-01-03"], "is_open": [True, True]})
    for dataset, frame in {"prices": prices, "index_members": members, "trade_calendar": calendar}.items():
        frame.to_parquet(data_dir / STANDARD_PARQUET_FILES[dataset], index=False)
    write_story004_manifest_and_quality(data_dir, reports_dir)
    load_backtest_data(
        LoaderConfig(
            data_dir=data_dir,
            quality_report_path=reports_dir / "data_quality_report.csv",
            start_date="2020-01-02",
            end_date="2020-01-03",
        )
    )

    idx = [item.date() for item in pd.bdate_range("2020-01-01", periods=60)]
    close_df = pd.DataFrame({"A": range(10, 70), "B": range(70, 10, -1)}, index=idx)
    run_portfolio(
        close_df.iloc[:3],
        [RebalanceSignal(signal_date=idx[0], execution_date=idx[1], target_symbols=["MISSING"])],
        PortfolioConfig(initial_cash=1000.0, commission_rate=0.0, slippage_rate=0.0, sell_tax_rate=0.0),
    )
    run_backtest(close_df, BacktestConfig(lookback_days=3, rebalance_freq=10, top_fraction=0.5))
    run_parameter_sweep(
        close_df,
        config=type("Cfg", (), {"parameters": [SweepParameter(5, 5, 0.5)], "continue_on_error": True})(),
        backtest_runner=lambda _frame, _cfg: (_ for _ in ()).throw(RuntimeError("fake scan failure")),
    )
    select_candidates([])
    with pytest.raises(UniverseError):
        load_universe(tmp_path / "missing.csv", mode="pit")
    with pytest.raises(TradeStatusError):
        load_trade_status(tmp_path / "trade_status.csv")
    with pytest.raises(TradingConstraintError):
        LimitPriceProvider(pd.DataFrame())
    empty_events = EventStore(pd.DataFrame({"event_date": []}), enabled=True)
    assert empty_events.frame.empty
    run_bias_audit(
        [AuditComparableRun("base-1", {"strategy_name": "momentum", "lookback": 5}, {"total_return": 0.1})],
        [AuditComparableRun("enh-1", {"strategy_name": "momentum", "lookback": 5}, {"total_return": 0.2})],
    )
    run_strategy("rsi", StrategyInput(close_df, idx[-1], {"period": 14, "top_fraction": 0.5}))
    with pytest.raises(ValueError):
        run_strategy("macd", StrategyInput(close_df, idx[-1], {"fast": 26, "slow": 12}))

    events = [
        json.loads(record.getMessage())
        for record in caplog.records
        if record.name == LOGGER_NAME and record.getMessage().startswith("{")
    ]
    required_fields = {"event_name", "run_id", "module", "story_id", "status", "params_summary", "elapsed_seconds"}
    assert events
    assert all(required_fields.issubset(event) for event in events)
    assert all(event["run_id"] for event in events)
    assert {event["story_id"] for event in events}.issuperset(
        {
            "STORY-004",
            "STORY-005",
            "STORY-006",
            "STORY-007",
            "STORY-008",
            "STORY-009",
            "STORY-010",
            "STORY-011",
            "STORY-012",
            "STORY-013",
        }
    )
    assert any(event["event_name"] == "start" for event in events)
    assert any(event["event_name"] == "end" for event in events)
    assert any(event["status"] in {"unfilled", "single_group_failed", "no_candidate", "missing_candidate_rank"} for event in events)
    errors = [event for event in events if event["event_name"] == "structured_error"]
    assert errors
    assert all("structured_error" in event for event in errors)
