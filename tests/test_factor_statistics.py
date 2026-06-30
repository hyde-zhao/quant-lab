from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from engine.factor_statistics import (
    build_forward_return_matrix,
    calculate_information_coefficient_timeseries,
    conditional_double_sort_returns,
    fama_macbeth_regression,
    independent_double_sort_returns,
    long_short_summary,
    long_short_summary_from_double_sort,
    newey_west_t_stat,
    single_sort_returns,
    spearman_rank_correlation,
    summarize_information_coefficient,
)


def _statistics_fixture(days: int = 24, symbols: int = 8) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    calendar = pd.bdate_range("2024-01-02", periods=days).date
    symbol_list = [f"00000{i + 1}.SZ" for i in range(symbols)]
    factor = pd.DataFrame(index=calendar, columns=symbol_list, dtype="float64")
    size = pd.DataFrame(index=calendar, columns=symbol_list, dtype="float64")
    close = pd.DataFrame(index=calendar, columns=symbol_list, dtype="float64")
    weights = pd.DataFrame(index=calendar, columns=symbol_list, dtype="float64")
    for symbol_index, symbol in enumerate(symbol_list):
        factor[symbol] = symbol_index + np.arange(days) * 0.01
        size[symbol] = 1000.0 + symbol_index * 100.0
        close[symbol] = 10.0 + symbol_index + np.arange(days) * (0.05 + symbol_index * 0.01)
        weights[symbol] = size[symbol]
    forward_returns = build_forward_return_matrix(close, horizon=5)
    return factor, size, forward_returns, weights


def test_sorting_statistics_support_equal_and_value_weighted_returns() -> None:
    factor, size, forward_returns, weights = _statistics_fixture()

    single = single_sort_returns(factor, forward_returns, weights=weights, weight_method="value", quantiles=4, min_cross_section=8)
    summary = long_short_summary(single)
    double = independent_double_sort_returns(
        factor,
        size,
        forward_returns,
        weights=weights,
        weight_method="market_cap",
        groups=2,
        min_cross_section=8,
    )
    double_summary = long_short_summary_from_double_sort(double, high_minus_low=True)

    assert not single.empty
    assert set(single["weight_method"]) == {"value"}
    assert summary["status"] == "pass"
    assert not double.empty
    assert {"size_group", "factor_group", "mean_forward_return"} <= set(double.columns)
    assert double_summary["status"] == "pass"


def test_conditional_double_sort_newey_west_and_fama_macbeth() -> None:
    factor, size, forward_returns, _weights = _statistics_fixture()

    conditional = conditional_double_sort_returns(size, factor, forward_returns, groups=2, min_cross_section=8)
    fmb = fama_macbeth_regression(
        forward_returns,
        {"factor": factor, "size": size},
        min_cross_section=8,
    )

    assert not conditional.empty
    assert {"conditioning_group", "factor_group", "mean_forward_return"} <= set(conditional.columns)
    assert newey_west_t_stat(pd.Series([0.01, 0.02, 0.00, 0.03])) is not None
    assert set(fmb["coefficient"]) == {"intercept", "factor", "size"}


def test_factor_statistics_validate_invalid_arguments() -> None:
    factor, _size, forward_returns, _weights = _statistics_fixture()

    with pytest.raises(ValueError, match="quantiles"):
        single_sort_returns(factor, forward_returns, quantiles=1)
    with pytest.raises(ValueError, match="horizon"):
        build_forward_return_matrix(factor, horizon=0)
    with pytest.raises(ValueError, match="factors"):
        fama_macbeth_regression(forward_returns, {})


def test_information_coefficient_matches_experiment_16_golden_fixture() -> None:
    factor_panel = pd.DataFrame(
        [
            {"factor_name": "momentum_5d", "date": "2024-01-02", "symbol": "AAA", "factor_value": 1.0, "forward_return_1d": 0.01},
            {"factor_name": "momentum_5d", "date": "2024-01-02", "symbol": "BBB", "factor_value": 2.0, "forward_return_1d": 0.02},
            {"factor_name": "momentum_5d", "date": "2024-01-02", "symbol": "CCC", "factor_value": 3.0, "forward_return_1d": 0.03},
            {"factor_name": "momentum_5d", "date": "2024-01-03", "symbol": "AAA", "factor_value": 3.0, "forward_return_1d": 0.01},
            {"factor_name": "momentum_5d", "date": "2024-01-03", "symbol": "BBB", "factor_value": 2.0, "forward_return_1d": 0.02},
            {"factor_name": "momentum_5d", "date": "2024-01-03", "symbol": "CCC", "factor_value": 1.0, "forward_return_1d": 0.03},
            {"factor_name": "momentum_20d", "date": "2024-01-02", "symbol": "AAA", "factor_value": 1.0, "forward_return_1d": 0.02},
            {"factor_name": "momentum_20d", "date": "2024-01-02", "symbol": "BBB", "factor_value": 1.0, "forward_return_1d": 0.01},
            {"factor_name": "momentum_20d", "date": "2024-01-02", "symbol": "CCC", "factor_value": 1.0, "forward_return_1d": 0.03},
        ]
    )

    ic = calculate_information_coefficient_timeseries(
        factor_panel,
        min_cross_section=3,
        forward_return_columns={"1d": "forward_return_1d"},
    )
    summary = summarize_information_coefficient(ic)

    first = ic[(ic["factor_name"] == "momentum_5d") & (ic["date"] == "2024-01-02")].iloc[0]
    second = ic[(ic["factor_name"] == "momentum_5d") & (ic["date"] == "2024-01-03")].iloc[0]
    constant = ic[ic["factor_name"] == "momentum_20d"].iloc[0]
    row = summary[summary["factor_name"] == "momentum_5d"].iloc[0]

    assert first["rank_ic"] == pytest.approx(1.0)
    assert second["rank_ic"] == pytest.approx(-1.0)
    assert pd.isna(constant["rank_ic"])
    assert row["valid_ic_days"] == 2
    assert row["rank_ic_mean"] == pytest.approx(0.0)
    assert row["rank_ic_std"] == pytest.approx(np.sqrt(2.0))
    assert row["positive_rank_ic_ratio"] == pytest.approx(0.5)


def test_information_coefficient_handles_low_sample_and_duplicate_ranks() -> None:
    assert spearman_rank_correlation(pd.Series([1.0, 1.0, 2.0]), pd.Series([0.1, 0.2, 0.3])) is not None
    assert spearman_rank_correlation(pd.Series([1.0, 1.0]), pd.Series([0.1, 0.2])) is None

    factor_panel = pd.DataFrame(
        [
            {"factor_name": "low_sample", "date": "2024-01-02", "factor_value": 1.0, "forward_return_1d": 0.01},
            {"factor_name": "low_sample", "date": "2024-01-02", "factor_value": 2.0, "forward_return_1d": 0.02},
        ]
    )
    ic = calculate_information_coefficient_timeseries(factor_panel, min_cross_section=3)

    assert len(ic) == 1
    assert pd.isna(ic.iloc[0]["ic"])
    assert pd.isna(ic.iloc[0]["rank_ic"])
    assert ic.iloc[0]["cross_section_n"] == 2
