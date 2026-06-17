from __future__ import annotations

from datetime import datetime
from pathlib import Path

from market_data.calendar import resolve_current_truth_as_of
from market_data.contracts import (
    CR014_CLAIM_FULL_A_SINCE_INCEPTION,
    CR014_CODE_CHANGE_CHAIN_CONFLICT,
    CR014_FORBIDDEN_OPERATION_COUNTERS,
    CR014_LIFECYCLE_REQUIRED_FIELDS,
    CR014_REQUIRED_MISSING_CALENDAR,
    CR014_REQUIRED_MISSING_LIFECYCLE,
    CR014_SECURITY_IDENTITY_FIELDS,
    CR014_UNIVERSE_METADATA_FIELDS,
)
from market_data.lifecycle import (
    build_full_a_blocked_claims,
    build_universe_denominator,
    validate_code_change_chain,
    validate_lifecycle_records,
)


TARGET_FILES = (
    Path("market_data/contracts.py"),
    Path("market_data/lifecycle.py"),
    Path("market_data/calendar.py"),
)


def test_cr014_contract_constants_freeze_required_fields_and_counters() -> None:
    assert CR014_LIFECYCLE_REQUIRED_FIELDS == (
        "list_date",
        "delist_date",
        "list_status",
        "code_change_mapping",
        "exchange",
        "board",
        "effective_date",
        "available_at",
        "source_interface",
        "run_id",
    )
    assert len(CR014_LIFECYCLE_REQUIRED_FIELDS) == 10
    assert {"security_id", "symbol", "valid_from", "valid_to"} <= set(CR014_SECURITY_IDENTITY_FIELDS)
    assert {
        "universe_scope",
        "coverage_start_policy",
        "current_trade_date_policy",
        "as_of_trade_date",
        "calendar_source",
    } <= set(CR014_UNIVERSE_METADATA_FIELDS)
    assert CR014_FORBIDDEN_OPERATION_COUNTERS == {
        "provider_fetch": 0,
        "lake_write": 0,
        "credential_read": 0,
        "legacy_data_operation": 0,
        "old_report_overwrite": 0,
        "duckdb_dependency_change": 0,
        "duckdb_write": 0,
        "catalog_current_pointer_publish": 0,
        "s09_real_execution": 0,
    }


def test_lifecycle_required_fields_complete_allow_contract_claim() -> None:
    result = validate_lifecycle_records([lifecycle_record()])

    assert result.passed is True
    assert result.required_missing == ()
    assert result.full_a_allowed_claim_count == 1
    assert result.allowed_claims[CR014_CLAIM_FULL_A_SINCE_INCEPTION] is True


def test_lifecycle_missing_field_blocks_full_a_allowed_claim() -> None:
    broken = lifecycle_record()
    broken.pop("available_at")

    lifecycle_result = validate_lifecycle_records([broken])
    claim_result = build_full_a_blocked_claims(lifecycle_result)

    assert lifecycle_result.passed is False
    assert lifecycle_result.full_a_allowed_claim_count == 0
    assert claim_result.full_a_allowed_claim_count == 0
    assert claim_result.allowed_claims[CR014_CLAIM_FULL_A_SINCE_INCEPTION] is False
    assert any(item.code == CR014_REQUIRED_MISSING_LIFECYCLE and item.field == "available_at" for item in claim_result.required_missing)
    assert any(item.claim == CR014_CLAIM_FULL_A_SINCE_INCEPTION for item in claim_result.blocked_claims)


def test_universe_denominator_uses_stable_security_id_and_keeps_delisted_trace() -> None:
    records = [
        lifecycle_record(
            security_id="SEC-0001",
            symbol="600001.SH",
            list_date="2001-01-01",
            delist_date="2020-12-31",
            list_status="delisted",
        ),
        lifecycle_record(security_id="SEC-0002", symbol="000002.SZ", list_date="2005-01-01"),
    ]

    before_delist = build_universe_denominator(records, "2019-01-02")
    after_delist = build_universe_denominator(records, "2021-01-04")

    assert before_delist.denominator == 2
    assert {member.security_id for member in before_delist.members} == {"SEC-0001", "SEC-0002"}
    assert before_delist.members[0].security_id == "SEC-0001"

    assert after_delist.denominator == 1
    assert {member.security_id for member in after_delist.members} == {"SEC-0002"}
    trace = {member.security_id: member.lifecycle_status for member in after_delist.trace_records}
    assert trace["SEC-0001"] == "delisted"
    assert after_delist.full_a_allowed_claim_count == 1


def test_code_change_chain_preserves_identity_and_blocks_same_day_multi_mapping() -> None:
    valid = validate_code_change_chain(
        [
            {
                "security_id": "SEC-0001",
                "predecessor_id": "SEC-0001",
                "successor_id": "SEC-0001",
                "old_symbol": "600001.SH",
                "new_symbol": "600101.SH",
                "effective_date": "2010-01-04",
            },
            {
                "security_id": "SEC-0001",
                "predecessor_id": "SEC-0001",
                "successor_id": "SEC-0001",
                "old_symbol": "600101.SH",
                "new_symbol": "600201.SH",
                "effective_date": "2018-06-01",
            },
        ]
    )

    conflict = validate_code_change_chain(
        [
            {
                "security_id": "SEC-0001",
                "predecessor_id": "SEC-0001",
                "successor_id": "SEC-0001",
                "old_symbol": "600001.SH",
                "new_symbol": "600101.SH",
                "effective_date": "2010-01-04",
            },
            {
                "security_id": "SEC-0001",
                "predecessor_id": "SEC-0001",
                "successor_id": "SEC-0001",
                "old_symbol": "600001.SH",
                "new_symbol": "600102.SH",
                "effective_date": "2010-01-04",
            },
        ]
    )

    assert valid.passed is True
    assert valid.full_a_allowed_claim_count == 1
    assert conflict.passed is False
    assert conflict.full_a_allowed_claim_count == 0
    assert {item.code for item in conflict.required_missing} >= {CR014_CODE_CHANGE_CHAIN_CONFLICT}
    assert any(item.claim == CR014_CLAIM_FULL_A_SINCE_INCEPTION for item in conflict.blocked_claims)


def test_unclosed_trade_day_cannot_be_current_truth() -> None:
    result = resolve_current_truth_as_of(
        [{"trade_date": "2026-05-27", "is_open": True, "calendar_source": "fixture"}],
        datetime.fromisoformat("2026-05-27T14:59:00"),
        market_close_time="15:00:00",
    )

    assert result.passed is False
    assert result.as_of_trade_date is None
    assert result.full_a_allowed_claim_count == 0
    assert result.required_missing[0].code != CR014_REQUIRED_MISSING_CALENDAR
    assert result.blocked_claims[0].claim == CR014_CLAIM_FULL_A_SINCE_INCEPTION


def test_last_closed_open_trade_day_is_selected_without_real_calendar_fetch() -> None:
    result = resolve_current_truth_as_of(
        [
            {"trade_date": "2026-05-26", "is_open": True, "calendar_source": "fixture"},
            {"trade_date": "2026-05-27", "is_open": True, "calendar_source": "fixture"},
            {"trade_date": "2026-05-28", "is_open": True, "calendar_source": "fixture"},
        ],
        datetime.fromisoformat("2026-05-27T15:30:00"),
        market_close_time="15:00:00",
    )

    assert result.passed is True
    assert result.as_of_trade_date == "2026-05-27"
    assert result.calendar_source == "fixture"
    assert result.full_a_allowed_claim_count == 1


def test_cr014_modules_do_not_import_forbidden_runtime_boundaries() -> None:
    forbidden_fragments = (
        "market_data.connectors",
        "market_data.storage",
        "market_data.runtime",
        "import duckdb",
        "from duckdb",
        "os.environ",
        "dotenv",
        "data/",
        "reports/",
    )

    for path in TARGET_FILES:
        text = path.read_text(encoding="utf-8")
        for fragment in forbidden_fragments:
            assert fragment not in text


def lifecycle_record(**overrides):
    record = {
        "security_id": "SEC-0001",
        "symbol": "600001.SH",
        "exchange": "SSE",
        "board": "main",
        "list_date": "2001-01-01",
        "delist_date": None,
        "list_status": "listed",
        "code_change_mapping": [],
        "effective_date": "2001-01-01",
        "available_at": "2001-01-01T18:00:00",
        "source_interface": "fixture.stock_lifecycle",
        "run_id": "fixture-run",
        "valid_from": "2001-01-01",
        "valid_to": None,
        "predecessor_id": None,
        "successor_id": None,
    }
    record.update(overrides)
    return record
