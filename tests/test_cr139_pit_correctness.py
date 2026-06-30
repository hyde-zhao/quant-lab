from __future__ import annotations

from pathlib import Path

import pandas as pd

from market_data.contracts import PIT_STATUS_AVAILABLE
from market_data.readers import ReaderResult, read_panel_as_of


def test_s29_pit_standard_excludes_future_financial_report_rows() -> None:
    # STD-S29-PIT-01/02: future available rows are invisible; latest visible row wins.
    result = read_panel_as_of(
        "financial_report",
        as_of="2026-01-05T09:30:00+08:00",
        keys=("symbol", "report_period"),
        reader=_fixture_reader(
            pd.DataFrame(
                {
                    "symbol": ["000001", "000001", "000001"],
                    "report_period": ["2025Q4", "2025Q4", "2025Q4"],
                    "eps": [1.00, 1.08, 99.00],
                    "available_at": [
                        "2026-01-03T18:00:00+08:00",
                        "2026-01-04T18:00:00+08:00",
                        "2026-01-06T18:00:00+08:00",
                    ],
                    "pit_status": [PIT_STATUS_AVAILABLE] * 3,
                }
            )
        ),
    )

    assert result.status == "available"
    assert result.frame is not None
    assert result.frame[["symbol", "report_period", "eps"]].to_dict("records") == [
        {"symbol": "000001", "report_period": "2025Q4", "eps": 1.08}
    ]
    assert 99.00 not in set(result.frame["eps"])


def _fixture_reader(frame: pd.DataFrame):
    def _reader(
        dataset: str,
        lake_root: str | Path | None = None,
        filters=None,
        quality_policy=None,
        required: bool = True,
    ) -> ReaderResult:
        del dataset, lake_root, filters, quality_policy, required
        return ReaderResult(status="available", frame=frame.copy())

    return _reader
