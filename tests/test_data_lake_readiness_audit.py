from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from experiments.run_data_lake_readiness_audit import (
    AuditConfig,
    INDEX_MEMBERS_AUDIT_MODE_DAILY_MATERIALIZED,
    INDEX_MEMBERS_AUDIT_MODE_SNAPSHOT_ASOF,
    STATUS_BLOCKED,
    STATUS_LIMITED,
    STATUS_RESEARCH_ONLY,
    _is_legacy_data_path,
    run_audit,
)
from market_data.catalog import CatalogEntry, CatalogStore
from market_data.contracts import (
    DATASET_ADJ_FACTOR,
    DATASET_EVENTS,
    DATASET_HS300_INDEX,
    DATASET_INDEX_MEMBERS,
    DATASET_INDEX_WEIGHTS,
    DATASET_PRICES,
    DATASET_PRICES_LIMIT,
    DATASET_STOCK_BASIC,
    DATASET_TRADE_CALENDAR,
    DATASET_TRADE_STATUS,
    INTERFACE_EVENTS_DISCLOSURE,
    INTERFACE_HS300_INDEX_DAILY,
    INTERFACE_INDEX_MEMBERS_SNAPSHOT,
    INTERFACE_INDEX_WEIGHTS_SNAPSHOT,
    INTERFACE_PRICES_ADJ_FACTOR,
    INTERFACE_PRICES_DAILY,
    INTERFACE_PRICES_LIMIT_DAILY,
    INTERFACE_STOCK_BASIC_SNAPSHOT,
    INTERFACE_TRADE_CALENDAR_DAILY,
    INTERFACE_TRADE_STATUS_DAILY,
    PIT_STATUS_AVAILABLE,
    SOURCE_TUSHARE,
)
from market_data.lake_layout import LakeLayout


def _prices_frame() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "trade_date": "2026-01-02",
                "symbol": "000001.SZ",
                "open": 10.0,
                "high": 11.0,
                "low": 9.5,
                "close": 10.5,
                "adj_factor": 1.0,
                "adjusted_open": 10.0,
                "adjusted_high": 11.0,
                "adjusted_low": 9.5,
                "adjusted_close": 10.5,
                "adjustment_policy": "qfq",
                "source": SOURCE_TUSHARE,
                "source_interface": INTERFACE_PRICES_DAILY,
                "source_run_id": "run-limited",
                "schema_version": "1.0",
                "available_at": "2026-01-02T16:00:00+08:00",
                "available_at_rule": "daily_close_fact",
                "lineage_raw_checksum": "checksum-prices",
            }
        ]
    )


def _full_prices_rows(dates: list[str], symbols: list[str]) -> list[dict]:
    rows: list[dict] = []
    for trade_date in dates:
        for symbol in symbols:
            rows.append(
                {
                    "trade_date": trade_date,
                    "symbol": symbol,
                    "open": 10.0,
                    "high": 11.0,
                    "low": 9.5,
                    "close": 10.5,
                    "volume": 1000.0,
                    "amount": 10500.0,
                    "adj_factor": 1.0,
                    "adjusted_open": 10.0,
                    "adjusted_high": 11.0,
                    "adjusted_low": 9.5,
                    "adjusted_close": 10.5,
                    "adjustment_policy": "qfq",
                    "source": SOURCE_TUSHARE,
                    "source_interface": INTERFACE_PRICES_DAILY,
                    "source_run_id": "run-prices",
                    "schema_version": "1.0",
                    "available_at": f"{trade_date}T16:00:00+08:00",
                    "available_at_rule": "daily_close_fact",
                    "lineage_raw_checksum": "checksum-prices",
                }
            )
    return rows


def _write_dataset(
    lake: Path,
    dataset: str,
    frame: pd.DataFrame,
    *,
    source_interface: str,
    start_date: str,
    end_date: str,
    run_id: str | None = None,
    pit_status: str = "not_applicable",
    available_at_rule: str = "daily_close_fact",
) -> None:
    layout = LakeLayout(lake)
    run_id = run_id or f"run-{dataset}"
    path = layout.canonical_dataset_root(dataset) / f"run_id={run_id}" / "part.parquet"
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_parquet(path, index=False)
    CatalogStore(lake).upsert(
        CatalogEntry(
            dataset=dataset,
            start_date=start_date,
            end_date=end_date,
            quality_status="pass",
            dataset_status="available",
            latest_manifest_run_id=run_id,
            source=SOURCE_TUSHARE,
            source_interface=source_interface,
            canonical_path=str(path.relative_to(lake)),
            published=True,
            readiness_status="available",
            pit_status=pit_status,
            available_at_rule=available_at_rule,
        )
    )


def _calendar_frame(
    dates: list[str],
    *,
    available_at_rule: str = "calendar_known",
    available_at: str | None = None,
) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "trade_date": trade_date,
                "exchange": "SSE",
                "is_open": True,
                "pretrade_date": "",
                "source": SOURCE_TUSHARE,
                "source_interface": INTERFACE_TRADE_CALENDAR_DAILY,
                "source_run_id": "run-calendar",
                "available_at": available_at or f"{trade_date}T00:00:00+08:00",
                "available_at_rule": available_at_rule,
                "schema_version": "1.0",
                "lineage_raw_checksum": "checksum-calendar",
            }
            for trade_date in dates
        ]
    )


def _snapshot_members_frame(symbols: list[str], effective_date: str = "2026-01-02") -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "trade_date": effective_date,
                "index_code": "399300.SZ",
                "con_code": symbol,
                "in_date": effective_date,
                "out_date": "",
                "is_member": True,
                "effective_date": effective_date,
                "available_date": "2026-01-01",
                "available_at": "2026-01-01T09:00:00+08:00",
                "available_at_rule": "explicit_timestamp",
                "is_pit_universe": True,
                "pit_status": PIT_STATUS_AVAILABLE,
                "readiness_status": "available",
                "source": SOURCE_TUSHARE,
                "source_interface": INTERFACE_INDEX_MEMBERS_SNAPSHOT,
                "source_run_id": "run-members",
                "schema_version": "1.0",
                "lineage_raw_checksum": "checksum-members",
                "derived_from": "fixture",
            }
            for symbol in symbols
        ]
    )


def _stock_basic_frame(symbols: list[str], *, late_symbol: str | None = None) -> pd.DataFrame:
    rows: list[dict] = []
    for symbol in symbols:
        list_date = "2026-01-06" if symbol == late_symbol else "2020-01-01"
        rows.append(
            {
                "symbol": symbol,
                "name": symbol,
                "market": "SSE",
                "list_status": "L",
                "list_date": list_date,
                "delist_date": "",
                "effective_date": list_date,
                "available_date": list_date,
                "available_at": f"{list_date}T09:00:00+08:00",
                "available_at_rule": "security_master_list_delist_date",
                "pit_status": PIT_STATUS_AVAILABLE,
                "readiness_status": "available",
                "source": SOURCE_TUSHARE,
                "source_interface": INTERFACE_STOCK_BASIC_SNAPSHOT,
                "source_run_id": "run-stock-basic",
                "schema_version": "1.0",
                "lineage_raw_checksum": "checksum-stock-basic",
            }
        )
    return pd.DataFrame(rows)


def test_readiness_audit_missing_lake_outputs_all_reports_without_env_fallback(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    env_lake = tmp_path / "env_lake"
    lake = tmp_path / "explicit_empty_lake"
    output = tmp_path / "reports"
    monkeypatch.setenv("MARKET_DATA_LAKE_ROOT", str(env_lake))

    result = run_audit(
        AuditConfig(
            lake_root=lake,
            start_date="2020-01-01",
            end_date="2020-01-03",
            output_dir=output,
            max_workers=1,
        )
    )

    assert result["overall_status"] == "blocked"
    assert result["env_fallback_reads"] == 0
    assert result["legacy_data_reads"] == 0
    assert result["lake_writes"] == 0
    assert not lake.exists()
    assert not env_lake.exists()

    expected = {
        "readiness_matrix.csv",
        "readiness_summary.md",
        "dataset_contract_snapshot.json",
        "dataset_coverage_detail.csv",
        "source_interface_matrix.csv",
        "schema_quality_audit.csv",
        "pit_w3_audit.csv",
        "execution_price_audit.csv",
        "unsupported_data_register.csv",
        "blocking_gaps.md",
    }
    assert expected == {path.name for path in output.iterdir()}

    matrix = pd.read_csv(output / "readiness_matrix.csv")
    assert len(matrix) == 10
    assert set(matrix["final_status"]) == {STATUS_BLOCKED}
    assert set(matrix["reader_status"]) == {"required_missing"}
    assert matrix["issue_code"].str.contains("catalog_missing").all()

    unsupported = pd.read_csv(output / "unsupported_data_register.csv")
    industry = unsupported[unsupported["data_item"] == "industry_classification"].iloc[0]
    assert industry["status"] == STATUS_RESEARCH_ONLY


def test_readiness_audit_marks_target_window_gap_as_limited_window_only(tmp_path: Path) -> None:
    lake = tmp_path / "lake"
    output = tmp_path / "reports"
    layout = LakeLayout(lake)
    path = layout.canonical_dataset_root(DATASET_PRICES) / "run_id=run-limited" / "part.parquet"
    path.parent.mkdir(parents=True, exist_ok=True)
    _prices_frame().to_parquet(path, index=False)
    CatalogStore(lake).upsert(
        CatalogEntry(
            dataset=DATASET_PRICES,
            start_date="2026-01-02",
            end_date="2026-01-02",
            quality_status="pass",
            dataset_status="available",
            latest_manifest_run_id="run-limited",
            source=SOURCE_TUSHARE,
            source_interface=INTERFACE_PRICES_DAILY,
            canonical_path=str(path.relative_to(lake)),
            published=True,
            readiness_status="available",
            available_at_rule="daily_close_fact",
        )
    )

    result = run_audit(
        AuditConfig(
            lake_root=lake,
            start_date="2020-01-01",
            end_date="2024-12-31",
            output_dir=output,
            max_workers=1,
        )
    )

    assert result["overall_status"] == "blocked"
    matrix = pd.read_csv(output / "readiness_matrix.csv")
    prices = matrix[matrix["dataset"] == DATASET_PRICES].iloc[0]
    assert prices["final_status"] == STATUS_LIMITED
    assert "target_window_not_covered" in prices["issue_code"]
    assert prices["date_min"] == "2026-01-02"
    assert prices["date_max"] == "2026-01-02"


def test_readiness_audit_rejects_repo_legacy_data_root() -> None:
    assert _is_legacy_data_path(Path("data"), cwd=Path.cwd())
    with pytest.raises(ValueError, match="旧 data"):
        run_audit(AuditConfig(lake_root=Path("data"), output_dir=Path("reports/test-readiness")))


def test_snapshot_index_members_expand_to_open_trade_dates(tmp_path: Path) -> None:
    lake = tmp_path / "lake"
    output = tmp_path / "reports"
    dates = ["2026-01-02", "2026-01-05", "2026-01-06"]
    symbols = ["000001.SZ"]
    _write_dataset(
        lake,
        DATASET_TRADE_CALENDAR,
        _calendar_frame(dates),
        source_interface=INTERFACE_TRADE_CALENDAR_DAILY,
        start_date=dates[0],
        end_date=dates[-1],
        available_at_rule="calendar_known",
    )
    _write_dataset(
        lake,
        DATASET_INDEX_MEMBERS,
        _snapshot_members_frame(symbols),
        source_interface=INTERFACE_INDEX_MEMBERS_SNAPSHOT,
        start_date=dates[0],
        end_date=dates[-1],
        pit_status=PIT_STATUS_AVAILABLE,
        available_at_rule="explicit_timestamp",
    )

    run_audit(
        AuditConfig(
            lake_root=lake,
            start_date=dates[0],
            end_date=dates[-1],
            output_dir=output,
            max_workers=1,
            index_members_audit_mode=INDEX_MEMBERS_AUDIT_MODE_SNAPSHOT_ASOF,
        )
    )

    matrix = pd.read_csv(output / "readiness_matrix.csv")
    members = matrix[matrix["dataset"] == DATASET_INDEX_MEMBERS].iloc[0]
    assert members["membership_audit_mode"] == INDEX_MEMBERS_AUDIT_MODE_SNAPSHOT_ASOF
    assert members["coverage_denominator"] == 3
    assert members["coverage_numerator"] == 3
    assert members["coverage_ratio"] == pytest.approx(1.0)
    assert "coverage_gap" not in str(members["issue_code"])


def test_daily_materialized_index_members_does_not_expand_snapshots(tmp_path: Path) -> None:
    lake = tmp_path / "lake"
    output = tmp_path / "reports"
    dates = ["2026-01-02", "2026-01-05", "2026-01-06"]
    _write_dataset(
        lake,
        DATASET_TRADE_CALENDAR,
        _calendar_frame(dates),
        source_interface=INTERFACE_TRADE_CALENDAR_DAILY,
        start_date=dates[0],
        end_date=dates[-1],
        available_at_rule="calendar_known",
    )
    _write_dataset(
        lake,
        DATASET_INDEX_MEMBERS,
        _snapshot_members_frame(["000001.SZ"]),
        source_interface=INTERFACE_INDEX_MEMBERS_SNAPSHOT,
        start_date=dates[0],
        end_date=dates[-1],
        pit_status=PIT_STATUS_AVAILABLE,
        available_at_rule="explicit_timestamp",
    )

    run_audit(
        AuditConfig(
            lake_root=lake,
            start_date=dates[0],
            end_date=dates[-1],
            output_dir=output,
            max_workers=1,
            index_members_audit_mode=INDEX_MEMBERS_AUDIT_MODE_DAILY_MATERIALIZED,
        )
    )

    matrix = pd.read_csv(output / "readiness_matrix.csv")
    members = matrix[matrix["dataset"] == DATASET_INDEX_MEMBERS].iloc[0]
    assert members["membership_audit_mode"] == INDEX_MEMBERS_AUDIT_MODE_DAILY_MATERIALIZED
    assert members["coverage_denominator"] == 3
    assert members["coverage_numerator"] == 1
    assert "audit_mode_mismatch" in members["issue_code"]
    assert "audit_mode_mismatch" in members["issue_category"]


def test_index_weights_align_to_membership_without_proving_daily_universe(tmp_path: Path) -> None:
    lake = tmp_path / "lake"
    output = tmp_path / "reports"
    dates = ["2026-01-02", "2026-01-05", "2026-01-06"]
    symbol = "000001.SZ"
    _write_dataset(
        lake,
        DATASET_TRADE_CALENDAR,
        _calendar_frame(dates),
        source_interface=INTERFACE_TRADE_CALENDAR_DAILY,
        start_date=dates[0],
        end_date=dates[-1],
        available_at_rule="calendar_known",
    )
    _write_dataset(
        lake,
        DATASET_INDEX_MEMBERS,
        _snapshot_members_frame([symbol]),
        source_interface=INTERFACE_INDEX_MEMBERS_SNAPSHOT,
        start_date=dates[0],
        end_date=dates[-1],
        pit_status=PIT_STATUS_AVAILABLE,
        available_at_rule="explicit_timestamp",
    )
    weights = pd.DataFrame(
        [
            {
                "trade_date": dates[0],
                "index_code": "399300.SZ",
                "con_code": symbol,
                "weight": 0.2,
                "effective_date": dates[0],
                "available_date": "2026-01-01",
                "available_at": "2026-01-01T09:00:00+08:00",
                "available_at_rule": "explicit_timestamp",
                "pit_status": PIT_STATUS_AVAILABLE,
                "readiness_status": "available",
                "source": SOURCE_TUSHARE,
                "source_interface": INTERFACE_INDEX_WEIGHTS_SNAPSHOT,
                "source_run_id": "run-weights",
                "schema_version": "1.0",
                "lineage_raw_checksum": "checksum-weights",
            }
        ]
    )
    _write_dataset(
        lake,
        DATASET_INDEX_WEIGHTS,
        weights,
        source_interface=INTERFACE_INDEX_WEIGHTS_SNAPSHOT,
        start_date=dates[0],
        end_date=dates[-1],
        pit_status=PIT_STATUS_AVAILABLE,
        available_at_rule="explicit_timestamp",
    )

    run_audit(
        AuditConfig(
            lake_root=lake,
            start_date=dates[0],
            end_date=dates[-1],
            output_dir=output,
            max_workers=1,
        )
    )

    matrix = pd.read_csv(output / "readiness_matrix.csv")
    weights_row = matrix[matrix["dataset"] == DATASET_INDEX_WEIGHTS].iloc[0]
    assert weights_row["coverage_denominator"] == 1
    assert weights_row["coverage_numerator"] == 1
    assert "coverage_gap" not in str(weights_row["issue_code"])


def test_trade_calendar_next_open_rule_is_semantics_gap_not_future_false_positive(tmp_path: Path) -> None:
    lake = tmp_path / "lake"
    output = tmp_path / "reports"
    _write_dataset(
        lake,
        DATASET_TRADE_CALENDAR,
        _calendar_frame(
            ["2026-01-02"],
            available_at_rule="date_only_next_open",
            available_at="2026-01-05T00:00:00+08:00",
        ),
        source_interface=INTERFACE_TRADE_CALENDAR_DAILY,
        start_date="2026-01-02",
        end_date="2026-01-02",
        available_at_rule="date_only_next_open",
    )

    run_audit(
        AuditConfig(
            lake_root=lake,
            start_date="2026-01-02",
            end_date="2026-01-02",
            output_dir=output,
            max_workers=1,
        )
    )

    matrix = pd.read_csv(output / "readiness_matrix.csv")
    calendar = matrix[matrix["dataset"] == DATASET_TRADE_CALENDAR].iloc[0]
    assert calendar["future_available_at_count"] == 0
    assert calendar["available_at_semantics_gap_count"] == 1
    assert "future_available_at" not in str(calendar["issue_code"])
    assert "calendar_available_at_rule_semantics_gap" in calendar["issue_code"]


def test_true_future_trade_calendar_available_at_still_fails(tmp_path: Path) -> None:
    lake = tmp_path / "lake"
    output = tmp_path / "reports"
    _write_dataset(
        lake,
        DATASET_TRADE_CALENDAR,
        _calendar_frame(
            ["2026-01-02"],
            available_at_rule="calendar_known",
            available_at="2026-01-05T00:00:00+08:00",
        ),
        source_interface=INTERFACE_TRADE_CALENDAR_DAILY,
        start_date="2026-01-02",
        end_date="2026-01-02",
        available_at_rule="calendar_known",
    )

    run_audit(
        AuditConfig(
            lake_root=lake,
            start_date="2026-01-02",
            end_date="2026-01-02",
            output_dir=output,
            max_workers=1,
        )
    )

    matrix = pd.read_csv(output / "readiness_matrix.csv")
    calendar = matrix[matrix["dataset"] == DATASET_TRADE_CALENDAR].iloc[0]
    assert calendar["future_available_at_count"] == 1
    assert "future_available_at" in calendar["issue_code"]


def test_adj_factor_future_available_at_keeps_blocked_pit_adjustment_claim(tmp_path: Path) -> None:
    lake = tmp_path / "lake"
    output = tmp_path / "reports"
    frame = pd.DataFrame(
        [
            {
                "trade_date": "2026-01-02",
                "symbol": "000001.SZ",
                "adj_factor": 1.0,
                "adjustment_policy": "qfq",
                "source": SOURCE_TUSHARE,
                "source_interface": INTERFACE_PRICES_ADJ_FACTOR,
                "source_run_id": "run-adj",
                "available_at": "2026-01-03T09:00:00+08:00",
                "available_at_rule": "daily_close_fact",
                "schema_version": "1.0",
                "lineage_raw_checksum": "checksum-adj",
            }
        ]
    )
    _write_dataset(
        lake,
        DATASET_ADJ_FACTOR,
        frame,
        source_interface=INTERFACE_PRICES_ADJ_FACTOR,
        start_date="2026-01-02",
        end_date="2026-01-02",
        available_at_rule="daily_close_fact",
    )

    run_audit(
        AuditConfig(
            lake_root=lake,
            start_date="2026-01-02",
            end_date="2026-01-02",
            output_dir=output,
            max_workers=1,
        )
    )

    matrix = pd.read_csv(output / "readiness_matrix.csv")
    adj = matrix[matrix["dataset"] == DATASET_ADJ_FACTOR].iloc[0]
    assert adj["future_available_at_count"] == 1
    assert "adj_factor_pit_available_at_blocked_claim" in adj["issue_code"]
    assert "pit_adjustment_no_leakage" in adj["blocked_claims"]
    assert "unsupported_claim" in adj["issue_category"]


def test_prices_gap_attribution_uses_tradability_and_lifecycle_gates(tmp_path: Path) -> None:
    lake = tmp_path / "lake"
    output = tmp_path / "reports"
    dates = ["2026-01-02", "2026-01-05"]
    symbols = ["000001.SZ", "000002.SZ", "000003.SZ"]
    _write_dataset(
        lake,
        DATASET_TRADE_CALENDAR,
        _calendar_frame(dates),
        source_interface=INTERFACE_TRADE_CALENDAR_DAILY,
        start_date=dates[0],
        end_date=dates[-1],
        available_at_rule="calendar_known",
    )
    _write_dataset(
        lake,
        DATASET_INDEX_MEMBERS,
        _snapshot_members_frame(symbols),
        source_interface=INTERFACE_INDEX_MEMBERS_SNAPSHOT,
        start_date=dates[0],
        end_date=dates[-1],
        pit_status=PIT_STATUS_AVAILABLE,
        available_at_rule="explicit_timestamp",
    )
    _write_dataset(
        lake,
        DATASET_STOCK_BASIC,
        _stock_basic_frame(symbols, late_symbol="000003.SZ"),
        source_interface=INTERFACE_STOCK_BASIC_SNAPSHOT,
        start_date=dates[0],
        end_date=dates[-1],
        pit_status=PIT_STATUS_AVAILABLE,
        available_at_rule="security_master_list_delist_date",
    )
    trade_status = pd.DataFrame(
        [
            {
                "trade_date": "2026-01-05",
                "symbol": "000002.SZ",
                "is_tradable": False,
                "is_suspended": True,
                "is_st": False,
                "status_reason": "suspended",
                "source": SOURCE_TUSHARE,
                "source_interface": INTERFACE_TRADE_STATUS_DAILY,
                "source_run_id": "run-trade-status",
                "available_at": "2026-01-05T09:30:00+08:00",
                "available_at_rule": "explicit_timestamp",
                "schema_version": "1.0",
                "lineage_raw_checksum": "checksum-trade-status",
            }
        ]
    )
    _write_dataset(
        lake,
        DATASET_TRADE_STATUS,
        trade_status,
        source_interface=INTERFACE_TRADE_STATUS_DAILY,
        start_date=dates[0],
        end_date=dates[-1],
        available_at_rule="explicit_timestamp",
    )
    prices = pd.DataFrame(_full_prices_rows(["2026-01-02"], ["000001.SZ", "000002.SZ"]))
    _write_dataset(
        lake,
        DATASET_PRICES,
        prices,
        source_interface=INTERFACE_PRICES_DAILY,
        start_date=dates[0],
        end_date=dates[-1],
        available_at_rule="daily_close_fact",
    )

    run_audit(
        AuditConfig(
            lake_root=lake,
            start_date=dates[0],
            end_date=dates[-1],
            output_dir=output,
            max_workers=1,
        )
    )

    matrix = pd.read_csv(output / "readiness_matrix.csv")
    prices_row = matrix[matrix["dataset"] == DATASET_PRICES].iloc[0]
    assert prices_row["coverage_denominator"] == 6
    assert prices_row["missing_price_count"] == 1
    assert prices_row["untradable_or_suspended_count"] == 1
    assert prices_row["not_listed_or_delisted_count"] == 2
    assert prices_row["denominator_excluded_count"] == 3
    assert "coverage_gap" in prices_row["issue_code"]
    assert "data_gap" in prices_row["issue_category"]


def test_execution_feed_requires_volume_amount_and_does_not_infer_real_vwap(tmp_path: Path) -> None:
    lake = tmp_path / "lake"
    output = tmp_path / "reports"
    _write_dataset(
        lake,
        DATASET_PRICES,
        _prices_frame(),
        source_interface=INTERFACE_PRICES_DAILY,
        start_date="2026-01-02",
        end_date="2026-01-02",
        available_at_rule="daily_close_fact",
    )

    run_audit(
        AuditConfig(
            lake_root=lake,
            start_date="2026-01-02",
            end_date="2026-01-02",
            output_dir=output,
            max_workers=1,
        )
    )

    execution = pd.read_csv(output / "execution_price_audit.csv").iloc[0]
    assert execution["execution_price_status"] == "required_missing"
    assert "volume" in execution["missing_ohlcv_columns"]
    assert "amount" in execution["missing_ohlcv_columns"]
    assert "real_vwap_execution" in execution["blocked_claims"]
