import pytest

from market_data.adjustment_contracts import (
    FACTOR_BASE_DATE_POLICY_PROVIDER_BASE,
    PROVIDER_FACTOR_DIRECTION_QFQ_RATIO,
)
from market_data.adjustment_derivation import DerivationInput, derive_qfq
from market_data.validation import (
    ADJUSTMENT_GATE_STATUS_FAIL,
    ADJUSTMENT_GATE_STATUS_PASS,
    ADJUSTMENT_GATE_STATUS_REQUIRED_MISSING,
    ADJUSTMENT_GATE_STATUS_WARN,
    CR017_MISSING_AS_OF_TRADE_DATE,
    CR017_MISSING_FACTOR_DIRECTION,
    CR017_PARITY_MISMATCH,
    CR017_REASON_REQUIRED_MISSING,
    CR017_S05_FORBIDDEN_OPERATION_COUNTERS,
    CR017_UNEXPLAINED_ADJUSTMENT_JUMP,
    CR017_WARNING_NOT_PRODUCTION_PASS,
    adjustment_quality_gate,
    check_adjustment_parity,
)


def _raw_row(trade_date: str, close: float) -> dict[str, object]:
    return {
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


def _factor_rows() -> tuple[dict[str, object], ...]:
    return (
        _factor_row("2026-01-01", 1.0),
        _factor_row("2026-01-02", 1.2),
        _factor_row("2026-01-03", 1.5),
    )


def _derivation_input(**overrides: object) -> DerivationInput:
    values = {
        "raw_rows": _raw_rows(),
        "factor_rows": _factor_rows(),
        "as_of_trade_date": "2026-01-02",
        "input_snapshot_id": "snapshot-cr017-s05",
        "source_run_id": "derived-run-s05",
        "base_trade_date": "2026-01-01",
        "base_date_policy": FACTOR_BASE_DATE_POLICY_PROVIDER_BASE,
    }
    values.update(overrides)
    return DerivationInput(**values)


def _quality_metadata(**overrides: object) -> dict[str, object]:
    metadata: dict[str, object] = {
        "view_id": "adj_factor",
        "source_run_id": "run-factor",
        "lineage_checksum": "sha256:factor",
        "quality_status": "pass",
        "provider_factor_direction": PROVIDER_FACTOR_DIRECTION_QFQ_RATIO,
        "adjustment_jump_ratio": 0.02,
    }
    metadata.update(overrides)
    return metadata


def test_ts017_01_quality_lineage_pass() -> None:
    result = adjustment_quality_gate(_quality_metadata())

    assert result.status == ADJUSTMENT_GATE_STATUS_PASS
    assert result.passed is True
    assert result.production_pass is True
    assert result.reason_code == ""
    assert result.operation_counts == CR017_S05_FORBIDDEN_OPERATION_COUNTERS


def test_ts017_01_missing_direction_is_required_missing() -> None:
    result = adjustment_quality_gate(_quality_metadata(provider_factor_direction=""))

    assert result.status == ADJUSTMENT_GATE_STATUS_REQUIRED_MISSING
    assert result.passed is False
    assert result.production_pass is False
    assert result.reason_code == CR017_REASON_REQUIRED_MISSING
    assert result.reason_detail == CR017_MISSING_FACTOR_DIRECTION
    assert result.missing_fields == ("provider_factor_direction",)
    assert result.issues[0]["code"] == CR017_REASON_REQUIRED_MISSING


def test_ts017_01_warning_is_not_production_pass() -> None:
    result = adjustment_quality_gate(_quality_metadata(quality_status="warn"))

    assert result.status == ADJUSTMENT_GATE_STATUS_WARN
    assert result.passed is False
    assert result.production_pass is False
    assert result.reason_code == CR017_WARNING_NOT_PRODUCTION_PASS
    assert CR017_WARNING_NOT_PRODUCTION_PASS in result.warnings


def test_ts017_01_unexplained_adjustment_jump_fails() -> None:
    result = adjustment_quality_gate(_quality_metadata(adjustment_jump_ratio=0.75))

    assert result.status == ADJUSTMENT_GATE_STATUS_FAIL
    assert result.passed is False
    assert result.reason_code == CR017_UNEXPLAINED_ADJUSTMENT_JUMP
    assert result.issues[0]["code"] == CR017_UNEXPLAINED_ADJUSTMENT_JUMP


def test_ts017_02_qfq_asof_parity_pass() -> None:
    candidate = derive_qfq(_derivation_input())
    expected = [
        {
            "trade_date": "2026-01-01",
            "symbol": "000001.SZ",
            "view_id": "prices_qfq",
            "research_adjustment_policy": "qfq",
            "as_of_trade_date": "2026-01-02",
            "adjusted_close": 10.0 * 1.0 / 1.2,
        },
        {
            "trade_date": "2026-01-02",
            "symbol": "000001.SZ",
            "view_id": "prices_qfq",
            "research_adjustment_policy": "qfq",
            "as_of_trade_date": "2026-01-02",
            "adjusted_close": 12.0,
        },
        {
            "trade_date": "2026-01-03",
            "symbol": "000001.SZ",
            "view_id": "prices_qfq",
            "research_adjustment_policy": "qfq",
            "as_of_trade_date": "2026-01-02",
            "adjusted_close": 15.0 * 1.5 / 1.2,
        },
    ]

    result = check_adjustment_parity(
        candidate,
        expected,
        value_fields=("adjusted_close",),
    )

    assert result.status == ADJUSTMENT_GATE_STATUS_PASS
    assert result.passed is True
    assert result.reason_code == ""
    assert result.expected_count == 3
    assert result.actual_count == 3


def test_ts017_02_missing_asof_fails() -> None:
    candidate = derive_qfq(_derivation_input())
    actual = [
        {key: value for key, value in row.items() if key != "as_of_trade_date"}
        for row in candidate.rows
    ]

    result = check_adjustment_parity(
        actual,
        candidate.rows,
        value_fields=("adjusted_close",),
        view_id="prices_qfq",
    )

    assert result.status == ADJUSTMENT_GATE_STATUS_REQUIRED_MISSING
    assert result.passed is False
    assert result.reason_code == CR017_MISSING_AS_OF_TRADE_DATE
    assert result.mismatch_reason["field"] == "as_of_trade_date"


def test_ts017_02_parity_mismatch_reason_is_structured() -> None:
    candidate = derive_qfq(_derivation_input())
    expected = [dict(row) for row in candidate.rows]
    expected[0]["adjusted_close"] = float(expected[0]["adjusted_close"]) + 0.01

    result = check_adjustment_parity(
        candidate.rows,
        expected,
        value_fields=("adjusted_close",),
    )

    assert result.status == ADJUSTMENT_GATE_STATUS_FAIL
    assert result.passed is False
    assert result.reason_code == CR017_PARITY_MISMATCH
    assert result.mismatch_reason["code"] == CR017_PARITY_MISMATCH
    assert result.mismatch_reason["field"] == "adjusted_close"
    assert result.mismatch_reason["expected"] == pytest.approx(expected[0]["adjusted_close"])
