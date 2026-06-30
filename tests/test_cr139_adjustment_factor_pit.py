from __future__ import annotations

import pandas as pd
import pytest

from market_data.contracts import INTERFACE_PRICES_DAILY, SOURCE_TUSHARE
from market_data.normalization import _canonical_rows, build_pit_adj_factor_lookup


def test_s23_adj_factor_pit_excludes_future_factor_and_applies_visible_factor() -> None:
    # STD-S29-PIT-01/02: the future 1.5 factor is invisible at the decision time.
    lookup = build_pit_adj_factor_lookup(_factor_frame(), as_of="2026-01-05T09:30:00+08:00")

    rows, lineage_filled = _canonical_rows(
        _price_record(),
        {"run_id": "run-cr139-s23-prices"},
        [
            {
                "trade_date": "20260105",
                "symbol": "000001",
                "open": 9.0,
                "high": 11.0,
                "low": 8.0,
                "close": 10.0,
                "adjustment_policy": "qfq",
                "source_run_id": "run-cr139-s23-prices",
            }
        ],
        lookup,
    )

    assert lineage_filled is False
    assert rows[0]["adj_factor"] == 1.2
    assert rows[0]["adjusted_close"] == 12.0
    assert rows[0]["adjusted_open"] == pytest.approx(10.8)
    assert rows[0]["adjusted_close"] != 15.0


def test_s23_adj_factor_breakpoint_regression_uses_latest_visible_factor() -> None:
    lookup = build_pit_adj_factor_lookup(_breakpoint_factor_frame(), as_of="2026-01-07T09:30:00+08:00")

    rows, _ = _canonical_rows(
        _price_record(),
        {"run_id": "run-cr139-s23-prices"},
        [
            {
                "trade_date": "20260104",
                "symbol": "000001",
                "close": 10.0,
                "adjustment_policy": "qfq",
                "source_run_id": "run-cr139-s23-prices",
            },
            {
                "trade_date": "20260105",
                "symbol": "000001",
                "close": 10.0,
                "adjustment_policy": "qfq",
                "source_run_id": "run-cr139-s23-prices",
            },
        ],
        lookup,
    )

    assert [row["adj_factor"] for row in rows] == [1.0, 1.2]
    assert [row["adjusted_close"] for row in rows] == [10.0, 12.0]


def _factor_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "trade_date": ["2026-01-05", "2026-01-05", "2026-01-05"],
            "symbol": ["000001", "000001", "000001"],
            "adj_factor": [1.1, 1.2, 1.5],
            "adjustment_policy": ["qfq", "qfq", "qfq"],
            "available_at": [
                "2026-01-03T16:00:00+08:00",
                "2026-01-04T16:00:00+08:00",
                "2026-01-06T16:00:00+08:00",
            ],
        }
    )


def _breakpoint_factor_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "trade_date": ["2026-01-04", "2026-01-05", "2026-01-05"],
            "symbol": ["000001", "000001", "000001"],
            "adj_factor": [1.0, 1.2, 1.5],
            "adjustment_policy": ["qfq", "qfq", "qfq"],
            "available_at": [
                "2026-01-04T16:00:00+08:00",
                "2026-01-05T16:00:00+08:00",
                "2026-01-08T16:00:00+08:00",
            ],
        }
    )


def _price_record() -> dict[str, object]:
    return {
        "run_id": "run-cr139-s23-prices",
        "source": SOURCE_TUSHARE,
        "interface": INTERFACE_PRICES_DAILY,
        "raw_checksum": "fixture-raw-checksum",
    }
