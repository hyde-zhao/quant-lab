from __future__ import annotations

"""Schema contracts tests.

Provenance is machine tracked in tests/PROVENANCE.yaml.
"""


# --- Merged from tests/data_lake/test_schema_contracts.py ---
import pandas as pd
import pytest

from engine.contracts import FallbackRule, SchemaChangeKind, SchemaContractFreeze
from market_data.readers import (
    SchemaCompatibilityError,
    apply_reader_fallback,
    evaluate_reader_schema_contract,
)


def test_schema_contract_blocks_missing_required_without_fallback():
    contract = SchemaContractFreeze(
        dataset="prices",
        required_fields=("trade_date", "symbol", "close", "available_at"),
        field_types={"close": "float"},
        primary_key=("trade_date", "symbol"),
        breaking_changes=({"field": "old_available_at", "replacement": "available_at"},),
        frozen_at="2026-06-29T00:00:00+08:00",
        owner_feature="FEAT-02",
    )

    payload = contract.to_dict()
    assert payload["breaking_changes"][0]["replacement"] == "available_at"
    assert payload["frozen_at"] == "2026-06-29T00:00:00+08:00"
    assert payload["owner_feature"] == "FEAT-02"

    with pytest.raises(SchemaCompatibilityError):
        evaluate_reader_schema_contract(
            {
                "fields": {"trade_date": "object", "symbol": "object", "close": "float64"},
                "primary_key": ("trade_date", "symbol"),
            },
            contract,
        )


def test_schema_contract_allows_explicit_reader_fallback():
    contract = SchemaContractFreeze(
        dataset="prices",
        required_fields=("trade_date", "symbol", "close", "available_at"),
        primary_key=("trade_date", "symbol"),
        allowed_reader_fallbacks=(
            FallbackRule(
                field="available_at",
                fallback_kind="default",
                value="2026-01-02T16:00:00+08:00",
            ),
        ),
    )
    frame = pd.DataFrame(
        [{"trade_date": "2026-01-02", "symbol": "000001.SZ", "close": 10.0}]
    )

    result = evaluate_reader_schema_contract(
        {
            "fields": {column: str(dtype) for column, dtype in frame.dtypes.items()},
            "primary_key": ("trade_date", "symbol"),
        },
        contract,
    )
    repaired = apply_reader_fallback(frame, result)

    assert result.change_kind == SchemaChangeKind.READER_FALLBACK
    assert repaired.loc[0, "available_at"] == "2026-01-02T16:00:00+08:00"

# --- Merged from tests/data_lake/test_schema_contracts.py ---
import pandas as pd

from market_data.contracts import CANONICAL_EVENTS_COLUMNS
from market_data.normalization import repair_events_schema


def test_events_schema_repair_fills_available_at_and_lineage_fields():
    frame = pd.DataFrame(
        [
            {
                "symbol": "000001.SZ",
                "event_type": "disclosure",
                "event_date": "2026-01-02",
            }
        ]
    )

    result = repair_events_schema(
        frame,
        source="tushare",
        source_interface="events_disclosure",
        source_run_id="cr139-w2-events-tushare-20260102-canonical",
        lineage_raw_checksum="sha256:abc",
    )

    assert list(result.frame.columns) == list(CANONICAL_EVENTS_COLUMNS)
    assert result.frame.loc[0, "available_at"] == "2026-01-02T09:20:00+08:00"
    assert result.frame.loc[0, "source_run_id"] == "cr139-w2-events-tushare-20260102-canonical"
    assert "available_at" in result.repaired_fields

# --- Merged from tests/data_lake/test_schema_contracts.py ---

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
