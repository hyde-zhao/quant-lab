from __future__ import annotations

from market_data.contracts import (
    CR018_FORBIDDEN_OPERATION_COUNTERS,
    CR018_REASON_ACTIVE_DENOMINATOR_MISSING,
    CR018_REASON_AS_OF_JOIN_VIOLATION,
    CR018_REASON_CODE_CHANGE_REQUIRED_MISSING,
    CR018_REASON_CURRENT_SNAPSHOT_NOT_PIT,
    CR018_REASON_LIFECYCLE_FIELD_MISSING,
    CR018_REASON_LIMIT_TRADE_ASSUMPTION_BLOCKED,
    CR018_REASON_PIT_AVAILABLE_FIELD_MISSING,
    CR018_REASON_PRICES_LIMIT_REQUIRED_MISSING,
    CR018_REASON_ST_SUSPEND_REQUIRED_MISSING,
    CR018_REASON_TRADE_STATUS_REQUIRED_MISSING,
    CR018_REASON_UNPUBLISHED_READINESS_SOURCE,
)
from market_data.readers import read_pit_tradability_readiness
from market_data.validation import (
    validate_lifecycle_readiness,
    validate_pit_universe_readiness,
    validate_tradability_readiness,
)


def test_missing_pit_available_fields_fail_closed_with_zero_publish_allowed() -> None:
    result = validate_pit_universe_readiness(
        [
            {
                "trade_date": "2026-01-05",
                "symbol": "000001.SZ",
                "effective_date": "2026-01-05",
                "available_date": "2026-01-05",
            }
        ],
        decision_time="2026-01-05T15:00:00+08:00",
    )

    assert result.passed is False
    assert result.production_publish_allowed_count == 0
    assert result.operation_counts == dict(CR018_FORBIDDEN_OPERATION_COUNTERS)
    assert CR018_REASON_PIT_AVAILABLE_FIELD_MISSING in _reason_codes(result.issues)
    assert "available_at" in result.missing_fields


def test_current_snapshot_cannot_replace_historical_pit_universe() -> None:
    result = validate_pit_universe_readiness(
        [
            {
                "snapshot_date": "2026-05-29",
                "symbol": "000001.SZ",
                "is_current_snapshot": True,
                "effective_date": "2026-01-05",
                "available_date": "2026-01-05",
                "available_at": "2026-01-05T08:30:00+08:00",
            }
        ],
        decision_time="2026-01-05T15:00:00+08:00",
    )

    assert result.passed is False
    assert result.current_snapshot_used is True
    assert result.current_snapshot_not_pit_count == 1
    assert result.production_publish_allowed_count == 0
    assert CR018_REASON_CURRENT_SNAPSHOT_NOT_PIT in _reason_codes(result.issues)


def test_pit_as_of_join_violation_is_counted_and_blocks_publish() -> None:
    result = validate_pit_universe_readiness(
        [
            {
                "trade_date": "2026-01-05",
                "symbol": "000001.SZ",
                "effective_date": "2026-01-05",
                "available_date": "2026-01-06",
                "available_at": "2026-01-06T08:30:00+08:00",
            }
        ],
        decision_time="2026-01-05T15:00:00+08:00",
    )

    assert result.passed is False
    assert result.as_of_join_violation_count == 1
    assert result.production_publish_allowed_count == 0
    assert CR018_REASON_AS_OF_JOIN_VIOLATION in _reason_codes(result.issues)


def test_lifecycle_missing_fields_or_denominator_fail_closed() -> None:
    result = validate_lifecycle_readiness(
        [{"symbol": "000001.SZ", "list_date": "1991-04-03"}],
        as_of_trade_date="2026-01-05",
    )

    reasons = _reason_codes(result.issues)
    assert result.passed is False
    assert result.production_publish_allowed_count == 0
    assert result.active_denominator == 0
    assert CR018_REASON_LIFECYCLE_FIELD_MISSING in reasons
    assert CR018_REASON_CODE_CHANGE_REQUIRED_MISSING in reasons
    assert CR018_REASON_ACTIVE_DENOMINATOR_MISSING in reasons


def test_lifecycle_with_code_change_and_active_denominator_can_pass_offline() -> None:
    result = validate_lifecycle_readiness(
        [
            {
                "symbol": "000001.SZ",
                "list_date": "1991-04-03",
                "delist_date": "2099-12-31",
                "code_change_mapping": "none",
            }
        ],
        as_of_trade_date="2026-01-05",
    )

    assert result.passed is True
    assert result.active_denominator == 1
    assert result.production_publish_allowed_count == 1
    assert result.code_change_ready is True


def test_tradability_missing_status_limit_or_st_suspend_fails_closed() -> None:
    result = validate_tradability_readiness(
        trade_status_rows=[{"trade_date": "2026-01-05", "symbol": "000001.SZ"}],
        prices_limit_rows=[],
    )

    reasons = _reason_codes(result.issues)
    assert result.passed is False
    assert result.production_publish_allowed_count == 0
    assert result.trade_status_ready is False
    assert result.prices_limit_ready is False
    assert result.st_suspend_ready is False
    assert CR018_REASON_TRADE_STATUS_REQUIRED_MISSING in reasons
    assert CR018_REASON_PRICES_LIMIT_REQUIRED_MISSING in reasons
    assert CR018_REASON_ST_SUSPEND_REQUIRED_MISSING in reasons
    assert CR018_REASON_LIMIT_TRADE_ASSUMPTION_BLOCKED in reasons


def test_limit_up_buy_and_limit_down_sell_are_not_assumed_fillable() -> None:
    result = validate_tradability_readiness(
        trade_status_rows=[
            {
                "trade_date": "2026-01-05",
                "symbol": "000001.SZ",
                "is_tradable": True,
                "is_st": False,
                "is_suspended": False,
            },
            {
                "trade_date": "2026-01-05",
                "symbol": "000002.SZ",
                "is_tradable": True,
                "is_st": False,
                "is_suspended": False,
            },
        ],
        prices_limit_rows=[
            {
                "trade_date": "2026-01-05",
                "symbol": "000001.SZ",
                "limit_up": 11.0,
                "limit_down": 9.0,
            },
            {
                "trade_date": "2026-01-05",
                "symbol": "000002.SZ",
                "limit_up": 22.0,
                "limit_down": 18.0,
            },
        ],
        trade_intents=[
            {"trade_date": "2026-01-05", "symbol": "000001.SZ", "side": "buy", "execution_price": 11.0},
            {"trade_date": "2026-01-05", "symbol": "000002.SZ", "side": "sell", "execution_price": 18.0},
        ],
    )

    assert result.passed is False
    assert result.can_buy_ready is False
    assert result.can_sell_ready is False
    assert result.production_publish_allowed_count == 0
    assert CR018_REASON_LIMIT_TRADE_ASSUMPTION_BLOCKED in _reason_codes(result.issues)


def test_reader_defaults_to_published_only_and_never_scans_unpublished_lake() -> None:
    result = read_pit_tradability_readiness("cr018-release-fixture")

    assert result["published_only"] is True
    assert result["explicit_metadata_only"] is True
    assert result["scan_unpublished_lake"] is False
    assert result["unpublished_lake_scan_count"] == 0
    assert result["production_publish_allowed_count"] == 0
    assert result["provider_fetch"] == 0
    assert result["lake_write"] == 0
    assert result["credential_read"] == 0
    assert result["current_pointer_publish"] == 0
    assert result["qmt_operation"] == 0
    assert result["duckdb_dependency_change"] == 0
    assert {item["reason_code"] for item in result["blocked_reasons"]} == {
        CR018_REASON_UNPUBLISHED_READINESS_SOURCE
    }


def test_reader_allows_explicit_published_fixture_results_without_real_operations() -> None:
    pit = validate_pit_universe_readiness(
        [
            {
                "trade_date": "2026-01-05",
                "symbol": "000001.SZ",
                "effective_date": "2026-01-05",
                "available_date": "2026-01-05",
                "available_at": "2026-01-05T08:30:00+08:00",
            }
        ],
        decision_time="2026-01-05T15:00:00+08:00",
    )
    lifecycle = validate_lifecycle_readiness(
        [
            {
                "symbol": "000001.SZ",
                "list_date": "1991-04-03",
                "delist_date": "2099-12-31",
                "code_change_mapping": "none",
            }
        ],
        as_of_trade_date="2026-01-05",
    )
    tradability = validate_tradability_readiness(
        trade_status_rows=[
            {
                "trade_date": "2026-01-05",
                "symbol": "000001.SZ",
                "is_tradable": True,
                "is_st": False,
                "is_suspended": False,
            }
        ],
        prices_limit_rows=[
            {
                "trade_date": "2026-01-05",
                "symbol": "000001.SZ",
                "limit_up": 11.0,
                "limit_down": 9.0,
            }
        ],
    )

    result = read_pit_tradability_readiness(
        "cr018-release-fixture",
        readiness_results=(pit, lifecycle, tradability),
        release_metadata={"published": True},
    )

    assert result["production_publish_allowed_count"] == 1
    assert result["blocked_reasons"] == []
    assert all(value == 0 for value in result["permission_counters"].values())


def _reason_codes(issues: tuple[dict[str, object], ...]) -> set[str]:
    return {str(item.get("reason_code")) for item in issues}
