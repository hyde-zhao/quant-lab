from __future__ import annotations

import inspect

import pandas as pd
import pytest

from market_data import readers
from market_data.readers import ReaderBoundaryError, ReaderResult, UnknownDatasetError, read_panel


def test_read_panel_joins_as_of_datasets_with_prefixed_columns() -> None:
    result = read_panel(
        ["prices", "financial_pit", "market_cap", "industry_classification"],
        as_of="2026-01-05",
        reader=_mapping_reader(
            {
                "prices": pd.DataFrame(
                    {
                        "symbol": ["000001", "000001"],
                        "trade_date": ["20260102", "20260105"],
                        "close": [10.0, 11.0],
                        "available_at": ["2026-01-02", "2026-01-05"],
                    }
                ),
                "financial_pit": pd.DataFrame(
                    {
                        "symbol": ["000001", "000001"],
                        "report_period": ["20250930", "20251231"],
                        "net_profit": [100.0, 999.0],
                        "available_at": ["2025-10-31", "2026-01-06"],
                    }
                ),
                "market_cap": pd.DataFrame(
                    {
                        "symbol": ["000001"],
                        "trade_date": ["20260105"],
                        "pe": [12.5],
                        "available_at": ["2026-01-05"],
                    }
                ),
                "industry_classification": pd.DataFrame(
                    {
                        "symbol": ["000001"],
                        "effective_date": ["20250101"],
                        "industry_code": ["801010"],
                        "available_at": ["2025-01-01"],
                    }
                ),
            }
        ),
    )

    assert result.status == "available"
    assert result.frame is not None
    row = result.frame.iloc[0].to_dict()
    assert row["symbol"] == "000001"
    assert row["prices__close"] == 11.0
    assert row["financial_pit__net_profit"] == 100.0
    assert row["market_cap__pe"] == 12.5
    assert row["industry_classification__industry_code"] == "801010"
    assert "999.0" not in result.frame.to_string()


def test_read_panel_records_unpublished_dataset_without_reading_candidate() -> None:
    result = read_panel(
        ["prices", "market_cap"],
        as_of="2026-01-05",
        reader=_mapping_reader(
            {
                "prices": pd.DataFrame(
                    {
                        "symbol": ["000001"],
                        "trade_date": ["20260105"],
                        "close": [11.0],
                        "available_at": ["2026-01-05"],
                    }
                )
            },
            unavailable={"market_cap": "catalog_not_published"},
        ),
    )

    assert result.status == "available"
    assert result.frame is not None
    assert "prices__close" in result.frame.columns
    assert not any(column.startswith("market_cap__") for column in result.frame.columns)
    assert result.issues == [{"code": "catalog_not_published", "dataset": "market_cap"}]


def test_read_panel_raises_for_unknown_dataset_without_reader() -> None:
    with pytest.raises(UnknownDatasetError):
        read_panel(["nonexistent"], as_of="2026-01-05")


def test_read_panel_rejects_mixed_adjustment_policy() -> None:
    with pytest.raises(ReaderBoundaryError):
        read_panel(
            ["prices"],
            as_of="2026-01-05",
            adjustment_policy={"prices": "qfq"},  # type: ignore[arg-type]
            reader=_mapping_reader(
                {
                    "prices": pd.DataFrame(
                        {
                            "symbol": ["000001"],
                            "trade_date": ["20260105"],
                            "close": [11.0],
                            "available_at": ["2026-01-05"],
                        }
                    )
                }
            ),
        )


def test_read_panel_composes_s05_reader_and_does_not_write_catalog() -> None:
    source = inspect.getsource(readers.read_panel)

    assert "read_panel_as_of" in source
    assert "read_dataset" in source
    assert "CatalogStore" not in source
    assert ".upsert(" not in source
    assert "write_text(" not in source


def _mapping_reader(frames: dict[str, pd.DataFrame], *, unavailable: dict[str, str] | None = None):
    unavailable = dict(unavailable or {})

    def _reader(
        dataset: str,
        lake_root=None,
        filters=None,
        quality_policy=None,
        required: bool = True,
    ) -> ReaderResult:
        del lake_root, filters, quality_policy, required
        if dataset in unavailable:
            return ReaderResult(status="unavailable", issues=[{"code": unavailable[dataset], "dataset": dataset}])
        return ReaderResult(status="available", frame=frames[dataset].copy())

    return _reader
