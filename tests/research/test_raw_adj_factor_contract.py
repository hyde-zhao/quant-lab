from market_data.adjustment_contracts import (
    CONTRACT_STATUS_FAIL,
    CONTRACT_STATUS_PASS,
    CONTRACT_STATUS_REQUIRED_MISSING,
    FACTOR_BASE_DATE_POLICY_AS_OF,
    PROVIDER_FACTOR_DIRECTION_QFQ_RATIO,
    build_required_field_sets,
    validate_adj_factor_contract,
    validate_derived_view_isolated,
    validate_prices_raw_contract,
    validate_source_lineage,
    zero_operation_counts,
)
from market_data.contracts import (
    CR017_ADJ_FACTOR_REQUIRED_FIELDS,
    CR017_PRICES_RAW_REQUIRED_FIELDS,
    CR017_VIEW_PRICES_HFQ,
    CR017_VIEW_PRICES_QFQ,
    CR017_VIEW_PRICES_RAW,
)
from market_data.validation import (
    CR017_DERIVED_OVERWRITES_RAW,
    CR017_INVALID_RAW_OHLC,
    CR017_MISSING_FACTOR_DIRECTION,
    CR017_MISSING_LINEAGE,
)


def _raw_row(**overrides: object) -> dict[str, object]:
    row: dict[str, object] = {
        "trade_date": "2026-01-02",
        "symbol": "000001.SZ",
        "open": 10.0,
        "high": 10.5,
        "low": 9.8,
        "close": 10.2,
        "volume": 1000,
        "amount": 10200.0,
        "source": "fixture",
        "source_interface": "prices.daily",
        "source_run_id": "run-raw",
        "batch_id": "batch-raw",
        "available_at": "2026-01-02T16:00:00+08:00",
        "available_at_rule": "after_close",
        "lineage_checksum": "sha256:raw",
        "quality_status": "pass",
    }
    row.update(overrides)
    return row


def _factor_row(**overrides: object) -> dict[str, object]:
    row: dict[str, object] = {
        "trade_date": "2026-01-02",
        "symbol": "000001.SZ",
        "adj_factor": 1.25,
        "provider_factor_direction": PROVIDER_FACTOR_DIRECTION_QFQ_RATIO,
        "factor_base_date_policy": FACTOR_BASE_DATE_POLICY_AS_OF,
        "source_run_id": "run-factor",
        "batch_id": "batch-factor",
        "available_at": "2026-01-02T16:00:00+08:00",
        "as_of_trade_date": "2026-01-02",
        "lineage_checksum": "sha256:factor",
        "quality_status": "pass",
    }
    row.update(overrides)
    return row


def test_required_field_sets_cover_raw_and_adj_factor() -> None:
    fields = build_required_field_sets()

    assert fields[CR017_VIEW_PRICES_RAW] == CR017_PRICES_RAW_REQUIRED_FIELDS
    assert fields["adj_factor"] == CR017_ADJ_FACTOR_REQUIRED_FIELDS
    assert set(CR017_PRICES_RAW_REQUIRED_FIELDS) >= {
        "trade_date",
        "symbol",
        "open",
        "high",
        "low",
        "close",
        "source_run_id",
        "batch_id",
        "lineage_checksum",
        "quality_status",
    }
    assert set(CR017_ADJ_FACTOR_REQUIRED_FIELDS) >= {
        "adj_factor",
        "provider_factor_direction",
        "factor_base_date_policy",
        "source_run_id",
        "lineage_checksum",
    }


def test_prices_raw_required_fields_pass() -> None:
    result = validate_prices_raw_contract([_raw_row()])

    assert result.status == CONTRACT_STATUS_PASS
    assert result.passed is True
    assert result.derivation_allowed is True
    assert result.operation_counts == zero_operation_counts()


def test_invalid_raw_price_fails() -> None:
    result = validate_prices_raw_contract([_raw_row(close=0)])

    assert result.status == CONTRACT_STATUS_FAIL
    assert result.reason_code == CR017_INVALID_RAW_OHLC
    assert result.field == "close"
    assert result.derivation_allowed is False


def test_missing_factor_direction_blocks_derivation() -> None:
    result = validate_adj_factor_contract([_factor_row(provider_factor_direction="")])

    assert result.status == CONTRACT_STATUS_REQUIRED_MISSING
    assert result.reason_code == CR017_MISSING_FACTOR_DIRECTION
    assert result.field == "provider_factor_direction"
    assert result.derivation_allowed is False


def test_missing_lineage_is_required_missing() -> None:
    result = validate_source_lineage(
        {"source_run_id": "run", "batch_id": "", "lineage_checksum": "sha256:raw"}
    )

    assert result.status == CONTRACT_STATUS_REQUIRED_MISSING
    assert result.reason_code == CR017_MISSING_LINEAGE
    assert result.field == "batch_id"
    assert result.derivation_allowed is False


def test_adj_factor_contract_passes_with_explicit_direction_and_lineage() -> None:
    result = validate_adj_factor_contract([_factor_row()])

    assert result.status == CONTRACT_STATUS_PASS
    assert result.passed is True
    assert result.derivation_allowed is True
    assert result.operation_counts == zero_operation_counts()


def test_derived_view_does_not_overwrite_raw() -> None:
    assert validate_derived_view_isolated(CR017_VIEW_PRICES_QFQ).passed is True
    assert validate_derived_view_isolated(CR017_VIEW_PRICES_HFQ).passed is True

    result = validate_derived_view_isolated(CR017_VIEW_PRICES_RAW)
    assert result.status == CONTRACT_STATUS_FAIL
    assert result.reason_code == CR017_DERIVED_OVERWRITES_RAW
    assert result.derivation_allowed is False


def test_s02_operation_counts_are_zero() -> None:
    assert zero_operation_counts() == {
        "provider_fetch": 0,
        "lake_write": 0,
        "credential_read": 0,
        "current_pointer_publish": 0,
        "dependency_change": 0,
        "legacy_qfq_overwrite": 0,
    }
