from __future__ import annotations

import pandas as pd

from engine.factor_model_validation import (
    FACTOR_MODEL_VALIDATION_SCHEMA,
    build_factor_model_validation_report,
)


def _fixtures(*, reversed_oos: bool = False) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    dates = pd.bdate_range("2024-01-02", periods=12).strftime("%Y-%m-%d").tolist()
    symbols = [f"{index:06d}.SZ" for index in range(40)]
    panel_rows = []
    label_rows = []
    universe_rows = []
    for date_index, trade_date in enumerate(dates):
        for symbol_index, symbol in enumerate(symbols):
            score = (symbol_index - 20) / 20.0
            sign = -1.0 if reversed_oos and date_index >= 10 else 1.0
            forward = sign * score * 0.01 + 0.002
            panel_rows.append(
                {
                    "trade_date": trade_date,
                    "symbol": symbol,
                    "factor_id": "momentum_20d",
                    "zscore_value": score,
                    "available_at": f"{trade_date}T15:30:00+08:00",
                }
            )
            label_rows.append(
                {
                    "trade_date": trade_date,
                    "symbol": symbol,
                    "forward_return": forward,
                    "label_available_at": f"{trade_date}T16:30:00+08:00",
                }
            )
            universe_rows.append(
                {
                    "trade_date": trade_date,
                    "symbol": symbol,
                    "industry_name": f"industry-{symbol_index % 5}",
                    "market_cap": 1_000_000_000 + symbol_index * 10_000_000,
                    "adv20_amount": 20_000_000 + symbol_index * 100_000,
                    "listed_days": 800,
                    "is_st": False,
                    "close": 10.0 + symbol_index / 10.0,
                }
            )
    portfolio = pd.DataFrame(
        {
            "trade_date": dates[:-1],
            "net_forward_return": [0.006] * (len(dates) - 1),
            "turnover": [0.2] * (len(dates) - 1),
        }
    )
    return pd.DataFrame(panel_rows), pd.DataFrame(label_rows), pd.DataFrame(universe_rows), portfolio


def test_factor_model_validation_report_builds_full_layered_report() -> None:
    panel, labels, universe, portfolio = _fixtures()

    report = build_factor_model_validation_report(
        run_id="validation-unit",
        factor_panel=panel,
        labels=labels,
        portfolio_path=portfolio,
        universe_frame=universe,
        config={"cost_bps": 10.0, "label_horizon": 20},
    )
    payload = report.to_dict()

    assert report.schema_version == FACTOR_MODEL_VALIDATION_SCHEMA
    assert report.status in {"pass", "pass_with_risk"}
    assert payload["factor_premium_significance"]["summary"][0]["t_stat"] is not None
    assert payload["economic_significance"]["mean_net_return"] > 0
    assert payload["short_feasibility"]["status"] == "not_applicable"
    assert payload["operation_counts"]["provider_fetch"] == 0


def test_factor_model_validation_blocks_negative_economic_significance() -> None:
    panel, labels, universe, portfolio = _fixtures()
    portfolio["net_forward_return"] = -0.01

    report = build_factor_model_validation_report(
        run_id="validation-negative-economics",
        factor_panel=panel,
        labels=labels,
        portfolio_path=portfolio,
        universe_frame=universe,
    )

    assert report.status == "blocked"
    assert report.economic_significance["status"] == "blocked"


def test_factor_model_validation_blocks_out_of_sample_reversal() -> None:
    panel, labels, universe, portfolio = _fixtures(reversed_oos=True)

    report = build_factor_model_validation_report(
        run_id="validation-oos-reversal",
        factor_panel=panel,
        labels=labels,
        portfolio_path=portfolio,
        universe_frame=universe,
    )

    assert report.status == "blocked"
    assert report.out_of_sample_validation["status"] == "blocked"


def test_factor_model_validation_detects_shell_value_concentration() -> None:
    panel, labels, universe, portfolio = _fixtures()
    universe["market_cap"] = 1_000_000.0
    universe["adv20_amount"] = 1_000.0
    universe["listed_days"] = 20

    report = build_factor_model_validation_report(
        run_id="validation-shell",
        factor_panel=panel,
        labels=labels,
        portfolio_path=portfolio,
        universe_frame=universe,
    )

    assert report.shell_value_control["status"] == "pass_with_risk"
    assert report.shell_value_control["shell_proxy_observation_share"] > 0.35


def test_factor_model_validation_blocks_long_short_without_shortable_universe() -> None:
    panel, labels, universe, portfolio = _fixtures()

    report = build_factor_model_validation_report(
        run_id="validation-short",
        factor_panel=panel,
        labels=labels,
        portfolio_path=portfolio,
        universe_frame=universe,
        tradability_frame=pd.DataFrame({"symbol": ["000001.SZ"], "is_tradable": [True]}),
        config={"strategy_type": "long_short"},
    )

    assert report.short_feasibility["status"] == "blocked"
    assert any(item["gate_id"] == "short_feasibility" for item in report.risk_warnings)
