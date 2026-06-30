from __future__ import annotations

from argparse import Namespace
from datetime import date

import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

from experiments.run_experiment_turnover_factor import (
    calculate_abnormal_turnover,
    resolve_output_roots,
    run_experiment_a,
    run_experiment_b,
    run_experiment_c,
)


def _sorting_fixture() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, list[date]]:
    dates = list(pd.bdate_range("2024-01-02", periods=4).date)
    symbols = [f"00000{i}.SZ" for i in range(1, 10)]
    factor = pd.DataFrame(index=dates, columns=symbols, dtype="float64")
    forward = pd.DataFrame(index=dates, columns=symbols, dtype="float64")
    size = pd.DataFrame(index=dates, columns=symbols, dtype="float64")
    for date_idx, trade_date in enumerate(dates):
        for symbol_idx, symbol in enumerate(symbols):
            factor.loc[trade_date, symbol] = symbol_idx + date_idx * 0.1
            forward.loc[trade_date, symbol] = symbol_idx * 0.01 + date_idx * 0.001
            size.loc[trade_date, symbol] = 1000.0 + symbol_idx * 100.0 + date_idx
    valid_mask = pd.DataFrame(True, index=dates, columns=symbols)
    valid_mask.iloc[1, 0] = False
    return factor, forward, size, valid_mask, dates


def test_abnormal_turnover_uses_engine_calculator_with_legacy_window_and_clip_semantics() -> None:
    turnover = pd.DataFrame(
        {
            "a": [1, 2, 3, 4, 5, 6, 1000],
            "b": [2, 2, 2, 2, 2, 2, 2],
        },
        dtype="float64",
    )

    actual = calculate_abnormal_turnover(
        turnover,
        short_window=2,
        long_window=4,
        short_min_periods=2,
        long_min_periods=3,
    )
    expected = (
        turnover.rolling(2, min_periods=2).mean()
        / turnover.rolling(4, min_periods=3).mean()
    ).clip(lower=0.01, upper=10.0)

    assert_frame_equal(actual, expected)


def test_turnover_sorting_adapter_matches_frozen_legacy_logic_on_synthetic_fixture() -> None:
    factor, forward, size, valid_mask, rebalance_dates = _sorting_fixture()

    actual_a = run_experiment_a(factor, forward, valid_mask, rebalance_dates, group_count=3).group_returns_ts
    actual_b = run_experiment_b(factor, size, forward, valid_mask, rebalance_dates, group_count=3).cell_returns
    actual_c = run_experiment_c(factor, size, forward, valid_mask, rebalance_dates, group_count=3).cell_returns

    assert_frame_equal(
        _sorted(actual_a),
        _sorted(_legacy_single_sort(factor, forward, valid_mask, rebalance_dates, group_count=3)),
        check_like=True,
    )
    assert_frame_equal(
        _sorted(actual_b),
        _sorted(_legacy_double_sort(factor, size, forward, valid_mask, rebalance_dates, group_count=3, conditional=False)),
        check_like=True,
    )
    assert_frame_equal(
        _sorted(actual_c),
        _sorted(_legacy_double_sort(factor, size, forward, valid_mask, rebalance_dates, group_count=3, conditional=True)),
        check_like=True,
    )


def test_turnover_sorting_adapter_keeps_all_constant_quantile_as_no_data() -> None:
    factor, forward, _size, valid_mask, rebalance_dates = _sorting_fixture()
    constant = factor * 0 + 1.0

    with pytest.raises(RuntimeError, match="无有效分组数据"):
        run_experiment_a(constant, forward, valid_mask, rebalance_dates, group_count=3)


def test_turnover_output_root_also_derives_process_dir(tmp_path) -> None:
    output_root = tmp_path / "reports" / "turnover"
    args = Namespace(
        output_root=str(output_root),
        process_dir=None,
        run_id="run-unit-turnover",
    )

    reports_base, process_dir = resolve_output_roots(args)

    assert reports_base == output_root
    assert process_dir == output_root / "run-unit-turnover" / "process"


def test_turnover_sorting_adapter_keeps_low_sample_quantile_as_no_data() -> None:
    factor, forward, _size, valid_mask, rebalance_dates = _sorting_fixture()
    low_sample_mask = valid_mask.copy()
    low_sample_mask.loc[:, :] = False
    low_sample_mask.iloc[:, :4] = True

    with pytest.raises(RuntimeError, match="无有效分组数据"):
        run_experiment_a(factor, forward, low_sample_mask, rebalance_dates, group_count=5)


def test_turnover_sorting_adapter_matches_legacy_logic_with_repeated_values() -> None:
    factor, forward, size, valid_mask, rebalance_dates = _sorting_fixture()
    repeated_values = [1.0, 2.0, 3.0] * 3
    repeated = factor.copy()
    for trade_date in repeated.index:
        repeated.loc[trade_date] = repeated_values

    actual_a = run_experiment_a(repeated, forward, valid_mask, rebalance_dates, group_count=3).group_returns_ts
    actual_b = run_experiment_b(repeated, size, forward, valid_mask, rebalance_dates, group_count=3).cell_returns
    actual_c = run_experiment_c(repeated, size, forward, valid_mask, rebalance_dates, group_count=3).cell_returns

    assert_frame_equal(
        _sorted(actual_a),
        _sorted(_legacy_single_sort(repeated, forward, valid_mask, rebalance_dates, group_count=3)),
        check_like=True,
    )
    assert_frame_equal(
        _sorted(actual_b),
        _sorted(_legacy_double_sort(repeated, size, forward, valid_mask, rebalance_dates, group_count=3, conditional=False)),
        check_like=True,
    )
    assert_frame_equal(
        _sorted(actual_c),
        _sorted(_legacy_double_sort(repeated, size, forward, valid_mask, rebalance_dates, group_count=3, conditional=True)),
        check_like=True,
    )


def _legacy_quantile_groups(values: pd.Series, group_count: int) -> pd.Series:
    clean = values.dropna()
    if len(clean) < group_count or clean.nunique() < 2:
        return pd.Series([pd.NA] * len(values), index=values.index, dtype="Int64")
    ranks = clean.rank(method="first")
    groups = pd.qcut(ranks, q=group_count, labels=range(1, group_count + 1))
    return groups.reindex(values.index).astype("Int64")


def _legacy_single_sort(
    factor: pd.DataFrame,
    forward: pd.DataFrame,
    valid_mask: pd.DataFrame,
    rebalance_dates: list[date],
    *,
    group_count: int,
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for trade_date in rebalance_dates:
        valid = pd.DataFrame({"factor": factor.loc[trade_date], "forward_return": forward.loc[trade_date]})
        valid = valid[valid_mask.loc[trade_date].reindex(valid.index, fill_value=False)].dropna()
        if len(valid) < group_count * 2:
            continue
        valid["group"] = _legacy_quantile_groups(valid["factor"], group_count)
        for group_id, group in valid.dropna(subset=["group"]).groupby("group"):
            rows.append(
                {
                    "date": trade_date,
                    "group": int(group_id),
                    "mean_return": float(group["forward_return"].mean()),
                    "n_stocks": len(group),
                }
            )
    return pd.DataFrame(rows)


def _legacy_double_sort(
    factor: pd.DataFrame,
    size: pd.DataFrame,
    forward: pd.DataFrame,
    valid_mask: pd.DataFrame,
    rebalance_dates: list[date],
    *,
    group_count: int,
    conditional: bool,
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for trade_date in rebalance_dates:
        valid = pd.DataFrame(
            {
                "factor": factor.loc[trade_date],
                "market_cap": size.loc[trade_date],
                "forward_return": forward.loc[trade_date],
            }
        )
        valid = valid[valid_mask.loc[trade_date].reindex(valid.index, fill_value=False)].dropna()
        if len(valid) < group_count * 2:
            continue
        valid["size_group"] = _legacy_quantile_groups(valid["market_cap"], group_count)
        valid = valid.dropna(subset=["size_group"])
        if conditional:
            valid["turnover_group"] = pd.NA
            for size_group in range(1, group_count + 1):
                idx = valid.index[valid["size_group"] == size_group]
                if len(idx) < group_count:
                    continue
                valid.loc[idx, "turnover_group"] = _legacy_quantile_groups(valid.loc[idx, "factor"], group_count)
        else:
            valid["turnover_group"] = _legacy_quantile_groups(valid["factor"], group_count)
        valid = valid.dropna(subset=["turnover_group"])
        valid["size_group"] = valid["size_group"].astype(int)
        valid["turnover_group"] = valid["turnover_group"].astype(int)
        for (size_group, turnover_group), group in valid.groupby(["size_group", "turnover_group"]):
            rows.append(
                {
                    "date": trade_date,
                    "size_group": int(size_group),
                    "turnover_group": int(turnover_group),
                    "mean_return": float(group["forward_return"].mean()),
                    "n_stocks": len(group),
                }
            )
    return pd.DataFrame(rows)


def _sorted(frame: pd.DataFrame) -> pd.DataFrame:
    return frame.sort_values(list(frame.columns)).reset_index(drop=True)
