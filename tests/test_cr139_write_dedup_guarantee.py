import pandas as pd
import pytest

from market_data.normalization import (
    CanonicalDeduplicationError,
    validate_canonical_write_dedup,
)


def test_write_dedup_fail_closed_on_duplicate_key():
    frame = pd.DataFrame(
        [
            {"trade_date": "2026-01-02", "symbol": "000001.SZ", "close": 10.0},
            {"trade_date": "2026-01-02", "symbol": "000001.SZ", "close": 10.1},
        ]
    )

    with pytest.raises(CanonicalDeduplicationError):
        validate_canonical_write_dedup(
            frame,
            dataset="prices",
            primary_key=("trade_date", "symbol"),
            policy="fail_on_duplicate",
        )


def test_write_dedup_can_be_deterministic_when_policy_explicit():
    frame = pd.DataFrame(
        [
            {
                "trade_date": "2026-01-02",
                "symbol": "000001.SZ",
                "close": 10.0,
                "source_run_id": "run_a",
            },
            {
                "trade_date": "2026-01-02",
                "symbol": "000001.SZ",
                "close": 10.1,
                "source_run_id": "run_b",
            },
        ]
    )

    result = validate_canonical_write_dedup(
        frame,
        dataset="prices",
        primary_key=("trade_date", "symbol"),
        policy="deduplicate_deterministic",
    )

    assert result.passed
    assert result.dropped_count == 1
    assert result.frame.loc[0, "source_run_id"] == "run_b"
