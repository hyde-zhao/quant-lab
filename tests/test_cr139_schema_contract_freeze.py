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
