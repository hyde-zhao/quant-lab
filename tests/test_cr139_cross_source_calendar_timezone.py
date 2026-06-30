from __future__ import annotations

from market_data.trade_calendar import normalize_calendar_rows, validate_cross_source_calendar


def test_s24_cross_source_calendar_passes_when_open_dates_align() -> None:
    rows = [
        {"trade_date": "20260102", "is_open": True},
        {"trade_date": "2026-01-05", "is_open": True},
        {"trade_date": "2026-01-06", "is_open": False},
    ]

    result = validate_cross_source_calendar({"tushare": rows, "jqdata": rows, "qmt": rows})

    assert result.passed is True
    assert result.canonical_open_dates == ("2026-01-02", "2026-01-05")
    assert result.mismatches == ()
    assert result.operation_counts["provider_fetch"] == 0
    assert result.operation_counts["lake_write"] == 0


def test_s24_cross_source_calendar_blocks_missing_open_date() -> None:
    result = validate_cross_source_calendar(
        {
            "tushare": [{"trade_date": "20260102"}, {"trade_date": "20260105"}],
            "jqdata": [{"trade_date": "20260102"}],
            "qmt": [{"trade_date": "20260102"}, {"trade_date": "20260105"}],
        }
    )

    assert result.passed is False
    assert {
        "code": "calendar_missing_open_date",
        "source": "jqdata",
        "missing_open_dates": ["2026-01-05"],
    } in result.mismatches


def test_s24_calendar_timestamp_normalizes_to_asia_shanghai() -> None:
    snapshot = normalize_calendar_rows(
        "tushare",
        [{"trade_date": "20260102", "timestamp": "2026-01-02T07:00:00+00:00"}],
    )

    assert snapshot.normalized_timestamps == ("2026-01-02T15:00:00+08:00",)
    assert snapshot.timezone == "Asia/Shanghai"


def test_s24_calendar_blocks_missing_trade_date_field() -> None:
    result = validate_cross_source_calendar({"tushare": [{"is_open": True}], "jqdata": [{"trade_date": "20260102"}]})

    assert result.passed is False
    assert any(issue["code"] == "calendar_trade_date_missing" for issue in result.mismatches)
