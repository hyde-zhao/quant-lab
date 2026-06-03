import pytest

from market_data.adjustment_contracts import (
    FACTOR_BASE_DATE_POLICY_PROVIDER_BASE,
    PROVIDER_FACTOR_DIRECTION_QFQ_RATIO,
)
from market_data.adjustment_derivation import (
    DERIVATION_STATUS_FAIL,
    DERIVATION_STATUS_REQUIRED_MISSING,
    MISSING_BASE_TRACE,
    MIXED_ADJUSTMENT_POLICY,
    DerivationInput,
    derive_hfq,
    derive_qfq,
    derive_returns_adjusted,
    zero_operation_counts,
)
from market_data.contracts import (
    CR017_PRICES_HFQ_REQUIRED_FIELDS,
    CR017_PRICES_QFQ_REQUIRED_FIELDS,
    CR017_REQUIRED_FIELD_SETS,
    CR017_RETURNS_ADJUSTED_REQUIRED_FIELDS,
    CR017_VIEW_PRICES_HFQ,
    CR017_VIEW_PRICES_QFQ,
    CR017_VIEW_RETURNS_ADJUSTED,
)
from market_data.normalization import normalize_adjustment_derivation_candidate
from market_data.validation import CR017_MISSING_FACTOR_DIRECTION


def _raw_row(trade_date: str, close: float, **overrides: object) -> dict[str, object]:
    row: dict[str, object] = {
        "trade_date": trade_date,
        "symbol": "000001.SZ",
        "open": close - 0.2,
        "high": close + 0.5,
        "low": close - 0.5,
        "close": close,
        "volume": 1000,
        "amount": close * 1000,
        "source": "fixture",
        "source_interface": "prices.daily",
        "source_run_id": "run-raw",
        "batch_id": "batch-raw",
        "available_at": f"{trade_date}T16:00:00+08:00",
        "available_at_rule": "after_close",
        "lineage_checksum": f"sha256:raw:{trade_date}",
        "quality_status": "pass",
    }
    row.update(overrides)
    return row


def _factor_row(trade_date: str, factor: float, **overrides: object) -> dict[str, object]:
    row: dict[str, object] = {
        "trade_date": trade_date,
        "symbol": "000001.SZ",
        "adj_factor": factor,
        "provider_factor_direction": PROVIDER_FACTOR_DIRECTION_QFQ_RATIO,
        "factor_base_date_policy": FACTOR_BASE_DATE_POLICY_PROVIDER_BASE,
        "source_run_id": "run-factor",
        "batch_id": "batch-factor",
        "available_at": f"{trade_date}T16:00:00+08:00",
        "as_of_trade_date": "2026-01-03",
        "lineage_checksum": f"sha256:factor:{trade_date}",
        "quality_status": "pass",
    }
    row.update(overrides)
    return row


def _raw_rows() -> tuple[dict[str, object], ...]:
    return (
        _raw_row("2026-01-01", 10.0),
        _raw_row("2026-01-02", 12.0),
        _raw_row("2026-01-03", 15.0),
    )


def _factor_rows(**overrides: object) -> tuple[dict[str, object], ...]:
    return (
        _factor_row("2026-01-01", 1.0, **overrides),
        _factor_row("2026-01-02", 1.2, **overrides),
        _factor_row("2026-01-03", 1.5, **overrides),
    )


def _input(**overrides: object) -> DerivationInput:
    values = {
        "raw_rows": _raw_rows(),
        "factor_rows": _factor_rows(),
        "as_of_trade_date": "2026-01-02",
        "input_snapshot_id": "snapshot-cr017-s03",
        "source_run_id": "derived-run-s03",
        "base_trade_date": "2026-01-01",
        "base_date_policy": FACTOR_BASE_DATE_POLICY_PROVIDER_BASE,
    }
    values.update(overrides)
    return DerivationInput(**values)


def test_derived_field_sets_cover_three_candidate_views() -> None:
    assert CR017_REQUIRED_FIELD_SETS[CR017_VIEW_PRICES_QFQ] == CR017_PRICES_QFQ_REQUIRED_FIELDS
    assert CR017_REQUIRED_FIELD_SETS[CR017_VIEW_PRICES_HFQ] == CR017_PRICES_HFQ_REQUIRED_FIELDS
    assert (
        CR017_REQUIRED_FIELD_SETS[CR017_VIEW_RETURNS_ADJUSTED]
        == CR017_RETURNS_ADJUSTED_REQUIRED_FIELDS
    )
    assert {"as_of_trade_date", "input_snapshot_id"} <= set(CR017_PRICES_QFQ_REQUIRED_FIELDS)
    assert {"base_trade_date", "factor_base_date_policy"} <= set(CR017_PRICES_HFQ_REQUIRED_FIELDS)
    assert {"return_type", "start_price_ref", "end_price_ref"} <= set(
        CR017_RETURNS_ADJUSTED_REQUIRED_FIELDS
    )


def test_qfq_same_asof_is_deterministic() -> None:
    first = derive_qfq(_input())
    second = derive_qfq(_input())

    assert first.passed is True
    assert first.to_dict() == second.to_dict()
    assert first.view_id == CR017_VIEW_PRICES_QFQ
    assert first.operation_counts == zero_operation_counts()
    assert {row["as_of_trade_date"] for row in first.rows} == {"2026-01-02"}
    assert {row["input_snapshot_id"] for row in first.rows} == {"snapshot-cr017-s03"}
    by_date = {row["trade_date"]: row for row in first.rows}
    assert by_date["2026-01-01"]["adjusted_close"] == pytest.approx(10.0 * 1.0 / 1.2)
    assert by_date["2026-01-02"]["adjusted_close"] == pytest.approx(12.0)


def test_qfq_asof_changes_lineage() -> None:
    asof_0102 = derive_qfq(_input(as_of_trade_date="2026-01-02"))
    asof_0103 = derive_qfq(_input(as_of_trade_date="2026-01-03"))

    assert asof_0102.passed is True
    assert asof_0103.passed is True
    assert asof_0102.lineage_checksum != asof_0103.lineage_checksum
    row_0102 = {row["trade_date"]: row for row in asof_0102.rows}["2026-01-01"]
    row_0103 = {row["trade_date"]: row for row in asof_0103.rows}["2026-01-01"]
    assert row_0102["adjusted_close"] == pytest.approx(10.0 * 1.0 / 1.2)
    assert row_0103["adjusted_close"] == pytest.approx(10.0 * 1.0 / 1.5)


def test_hfq_requires_traceable_base() -> None:
    missing = derive_hfq(_input(base_trade_date=""))
    assert missing.status == DERIVATION_STATUS_REQUIRED_MISSING
    assert missing.reason_code == MISSING_BASE_TRACE
    assert missing.rows == ()

    candidate = derive_hfq(_input(base_trade_date="2026-01-01"))
    assert candidate.passed is True
    assert candidate.view_id == CR017_VIEW_PRICES_HFQ
    assert {row["base_trade_date"] for row in candidate.rows} == {"2026-01-01"}
    assert {row["factor_base_date_policy"] for row in candidate.rows} == {
        FACTOR_BASE_DATE_POLICY_PROVIDER_BASE
    }
    by_date = {row["trade_date"]: row for row in candidate.rows}
    assert by_date["2026-01-02"]["adjusted_close"] == pytest.approx(12.0 * 1.2 / 1.0)


def test_returns_adjusted_from_single_adjusted_view() -> None:
    qfq = derive_qfq(_input())
    returns = derive_returns_adjusted(
        DerivationInput(
            adjusted_rows=qfq.rows,
            input_snapshot_id="snapshot-cr017-s03",
            source_run_id="returns-run-s03",
        )
    )

    assert returns.passed is True
    assert returns.view_id == CR017_VIEW_RETURNS_ADJUSTED
    assert {row["research_adjustment_policy"] for row in returns.rows} == {"qfq"}
    assert {row["return_type"] for row in returns.rows} == {"simple"}
    by_date = {row["trade_date"]: row for row in returns.rows}
    assert by_date["2026-01-02"]["adjusted_return"] == pytest.approx(
        (12.0 / (10.0 * 1.0 / 1.2)) - 1.0
    )
    assert by_date["2026-01-02"]["start_price_ref"].startswith("prices_qfq:")
    assert by_date["2026-01-02"]["end_price_ref"].startswith("prices_qfq:")


def test_returns_mixed_policy_fails() -> None:
    qfq = derive_qfq(_input()).rows[0]
    hfq = derive_hfq(_input()).rows[0]

    result = derive_returns_adjusted(
        DerivationInput(
            adjusted_rows=(qfq, hfq),
            input_snapshot_id="snapshot-cr017-s03",
            source_run_id="returns-run-s03",
        )
    )

    assert result.status == DERIVATION_STATUS_FAIL
    assert result.reason_code == MIXED_ADJUSTMENT_POLICY
    assert result.rows == ()
    assert result.operation_counts == zero_operation_counts()


def test_missing_factor_direction_blocks_derivation() -> None:
    candidate = derive_qfq(
        _input(factor_rows=_factor_rows(provider_factor_direction=""))
    )

    assert candidate.status == DERIVATION_STATUS_REQUIRED_MISSING
    assert candidate.reason_code == CR017_MISSING_FACTOR_DIRECTION
    assert candidate.rows == ()
    assert candidate.operation_counts == zero_operation_counts()


def test_normalization_entry_keeps_candidate_unpublished() -> None:
    candidate = derive_qfq(_input())
    normalized = normalize_adjustment_derivation_candidate(candidate)

    assert normalized.dataset == CR017_VIEW_PRICES_QFQ
    assert normalized.status == "candidate_unpublished"
    assert normalized.candidate_layer == "derived_view"
    assert normalized.current_pointer_changes == 0
    assert normalized.provider_fetches == 0
    assert normalized.credential_reads == 0
    assert normalized.raw_writes == 0
    assert normalized.publish_count == 0
