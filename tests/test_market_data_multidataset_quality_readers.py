import ast
import csv
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from market_data.catalog import CatalogEntry, CatalogStore
from market_data.contracts import (
    DATASET_HS300_INDEX,
    DATASET_INDEX_WEIGHTS,
    DATASET_PRICES,
    DATASET_TRADE_CALENDAR,
    INTERFACE_HS300_INDEX_DAILY,
    INTERFACE_PRICES_DAILY,
    INTERFACE_TRADE_CALENDAR_DAILY,
    SOURCE_TUSHARE,
)
from market_data.lake_layout import LakeLayout
from market_data.readers import QualityPolicy, read_dataset, read_factor_panel
from market_data.validation import (
    QualityThresholds,
    validate_adjustment_consistency,
    validate_dataset,
    validate_hs300_index,
    validate_pit_asof,
    write_quality_reports,
)


def fixed_clock():
    return datetime(2026, 5, 17, 6, 0, tzinfo=timezone.utc)


def write_canonical(lake_root: Path, dataset: str, frame: pd.DataFrame, run_id: str = "run-s03") -> Path:
    path = LakeLayout(lake_root).canonical_dataset_root(dataset) / f"run_id={run_id}" / "part.parquet"
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_parquet(path, index=False)
    return path


def trade_calendar() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "trade_date": "2026-01-02",
                "exchange": "SSE",
                "is_open": True,
                "pretrade_date": "2025-12-31",
                "source": SOURCE_TUSHARE,
                "source_interface": INTERFACE_TRADE_CALENDAR_DAILY,
                "source_run_id": "run-s03",
                "schema_version": "1.0",
                "available_at": "2026-01-02T00:00:00+08:00",
                "available_at_rule": "date_only_next_open",
                "lineage_raw_checksum": "checksum-calendar",
            },
            {
                "trade_date": "2026-01-03",
                "exchange": "SSE",
                "is_open": False,
                "pretrade_date": "2026-01-02",
                "source": SOURCE_TUSHARE,
                "source_interface": INTERFACE_TRADE_CALENDAR_DAILY,
                "source_run_id": "run-s03",
                "schema_version": "1.0",
                "available_at": "2026-01-03T00:00:00+08:00",
                "available_at_rule": "date_only_next_open",
                "lineage_raw_checksum": "checksum-calendar",
            },
            {
                "trade_date": "2026-01-05",
                "exchange": "SSE",
                "is_open": True,
                "pretrade_date": "2026-01-02",
                "source": SOURCE_TUSHARE,
                "source_interface": INTERFACE_TRADE_CALENDAR_DAILY,
                "source_run_id": "run-s03",
                "schema_version": "1.0",
                "available_at": "2026-01-05T00:00:00+08:00",
                "available_at_rule": "date_only_next_open",
                "lineage_raw_checksum": "checksum-calendar",
            },
        ]
    )


def hs300_frame(rows: list[dict] | None = None) -> pd.DataFrame:
    base_rows = rows or [
        {
            "trade_date": "2026-01-02",
            "index_code": "399300.SZ",
            "close": 4000.0,
            "pre_close": 3990.0,
            "pct_chg": 0.25,
            "open": 3991.0,
            "high": 4010.0,
            "low": 3980.0,
            "volume": 100.0,
            "amount": 200.0,
            "benchmark_kind": "price_index",
            "source": SOURCE_TUSHARE,
            "source_interface": INTERFACE_HS300_INDEX_DAILY,
            "source_run_id": "run-s03",
            "schema_version": "1.0",
            "available_at": "2026-01-02T16:00:00+08:00",
            "available_at_rule": "daily_close_fact",
            "lineage_raw_checksum": "checksum-hs300",
        },
        {
            "trade_date": "2026-01-05",
            "index_code": "399300.SZ",
            "close": 4010.0,
            "pre_close": 4000.0,
            "pct_chg": 0.25,
            "open": 4001.0,
            "high": 4020.0,
            "low": 3990.0,
            "volume": 101.0,
            "amount": 201.0,
            "benchmark_kind": "price_index",
            "source": SOURCE_TUSHARE,
            "source_interface": INTERFACE_HS300_INDEX_DAILY,
            "source_run_id": "run-s03",
            "schema_version": "1.0",
            "available_at": "2026-01-05T16:00:00+08:00",
            "available_at_rule": "daily_close_fact",
            "lineage_raw_checksum": "checksum-hs300",
        },
    ]
    return pd.DataFrame(base_rows)


def prices_frame(policy: str = "qfq") -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "trade_date": "2026-01-02",
                "symbol": "000001.SZ",
                "open": 10.0,
                "high": 11.0,
                "low": 9.5,
                "close": 10.5,
                "adj_factor": 2.0,
                "adjusted_open": 20.0,
                "adjusted_high": 22.0,
                "adjusted_low": 19.0,
                "adjusted_close": 21.0,
                "adjustment_policy": policy,
                "source": SOURCE_TUSHARE,
                "source_interface": INTERFACE_PRICES_DAILY,
                "source_run_id": "run-s03",
                "schema_version": "1.0",
                "available_at": "2026-01-02T16:00:00+08:00",
                "available_at_rule": "daily_close_fact",
                "lineage_raw_checksum": "checksum-prices",
            }
        ]
    )


def test_quality_csv_fields_status_split_and_hs300_denominator(tmp_path):
    hs300_path = write_canonical(tmp_path, DATASET_HS300_INDEX, hs300_frame())
    result = validate_hs300_index(
        tmp_path,
        "399300.SZ",
        ("2026-01-02", "2026-01-05"),
        trade_calendar(),
        QualityThresholds(),
        canonical_paths=[hs300_path],
        clock=fixed_clock,
    )
    csv_path, _ = write_quality_reports(result, tmp_path)
    row = next(csv.DictReader(csv_path.open("r", encoding="utf-8")))

    assert len(row) >= 20
    assert row["fetch_status"] == "not_applicable"
    assert row["dataset_status"] == "available"
    assert row["quality_status"] == "pass"
    assert row["coverage_denominator"] == "2"
    assert row["coverage_numerator"] == "2"
    assert row["benchmark_kind"] == "price_index"
    assert row["index_code"] == "399300.SZ"
    assert row["calendar_source"] == DATASET_TRADE_CALENDAR
    assert row["source_interface"] == INTERFACE_HS300_INDEX_DAILY
    assert row["lineage_raw_checksum"] == "checksum-hs300"
    assert row["missing_trade_dates_json"] == "[]"
    assert row["quality_thresholds_json"]


def test_hs300_missing_duplicate_lineage_and_policy_gate(tmp_path):
    missing_path = write_canonical(
        tmp_path / "missing",
        DATASET_HS300_INDEX,
        hs300_frame().iloc[[0]].reset_index(drop=True),
    )
    missing = validate_hs300_index(
        tmp_path / "missing",
        "399300.SZ",
        ("2026-01-02", "2026-01-05"),
        trade_calendar(),
        canonical_paths=[missing_path],
        clock=fixed_clock,
    )
    assert missing.quality_status == "fail"
    assert missing.dataset_status == "required_missing"
    assert missing.missing_trade_dates == ["2026-01-05"]
    assert "coverage_gap" in missing.issue_codes

    duplicate = pd.concat([hs300_frame(), hs300_frame().iloc[[0]]], ignore_index=True)
    dup_path = write_canonical(tmp_path / "duplicate", DATASET_HS300_INDEX, duplicate)
    dup = validate_hs300_index(
        tmp_path / "duplicate",
        "399300.SZ",
        ("2026-01-02", "2026-01-05"),
        trade_calendar(),
        canonical_paths=[dup_path],
    )
    assert dup.quality_status == "fail"
    assert dup.duplicate_key_count == 1
    assert dup.dataset_status == "duplicate_key"

    no_lineage = hs300_frame().drop(columns=["lineage_raw_checksum"])
    lineage_path = write_canonical(tmp_path / "lineage", DATASET_HS300_INDEX, no_lineage)
    lineage = validate_hs300_index(
        tmp_path / "lineage",
        "399300.SZ",
        ("2026-01-02", "2026-01-05"),
        trade_calendar(),
        canonical_paths=[lineage_path],
    )
    assert lineage.quality_status == "fail"
    assert "lineage_unavailable" in lineage.issue_codes

    policy = validate_hs300_index(
        tmp_path,
        "399300.SZ",
        ("2026-01-02", "2026-01-05"),
        trade_calendar(),
        canonical_paths=[write_canonical(tmp_path / "policy", DATASET_HS300_INDEX, hs300_frame())],
        benchmark_policy_confirmed=False,
    )
    assert policy.quality_status == "warn"
    assert "policy_unconfirmed" in policy.issue_codes


def test_catalog_upsert_get_list_records_four_p0_datasets(tmp_path):
    store = CatalogStore(tmp_path)
    for dataset, status in (
        (DATASET_PRICES, "pass"),
        (DATASET_HS300_INDEX, "pass"),
        (DATASET_TRADE_CALENDAR, "pass"),
        (DATASET_INDEX_WEIGHTS, "warn"),
    ):
        store.upsert(
            CatalogEntry(
                dataset=dataset,
                start_date="2026-01-02",
                end_date="2026-01-05",
                coverage={"numerator": 2, "denominator": 2, "ratio": 1.0},
                quality_status=status,
                dataset_status="available",
                latest_manifest_run_id="run-s03",
                source=SOURCE_TUSHARE,
                source_interface=f"{dataset}.daily",
                lineage_raw_checksum=f"checksum-{dataset}",
                canonical_path=f"canonical/{dataset}/1.0/run_id=run-s03/part.parquet",
                quality_csv_path=f"quality/run-s03/{dataset}_quality.csv",
            )
        )

    assert store.get(DATASET_PRICES).latest_manifest_run_id == "run-s03"
    assert len(store.list()) == 4
    assert {entry.dataset for entry in store.list()} >= {
        DATASET_PRICES,
        DATASET_HS300_INDEX,
        DATASET_TRADE_CALENDAR,
        DATASET_INDEX_WEIGHTS,
    }


def test_reader_structured_quality_policy_and_no_writes(tmp_path):
    prices_path = write_canonical(tmp_path, DATASET_PRICES, prices_frame())
    store = CatalogStore(tmp_path)
    store.upsert(
        CatalogEntry(
            dataset=DATASET_PRICES,
            quality_status="pass",
            dataset_status="available",
            canonical_path=str(prices_path.relative_to(tmp_path)),
            latest_manifest_run_id="run-s03",
            source=SOURCE_TUSHARE,
            source_interface=INTERFACE_PRICES_DAILY,
        )
    )
    before = sorted(path.relative_to(tmp_path) for path in tmp_path.rglob("*") if path.is_file())
    result = read_dataset(
        DATASET_PRICES,
        tmp_path,
        filters={"start": "2026-01-02", "end": "2026-01-02", "symbols": ["000001.SZ"]},
    )
    after = sorted(path.relative_to(tmp_path) for path in tmp_path.rglob("*") if path.is_file())

    assert result.status == "available"
    assert result.frame is not None
    assert len(result.frame) == 1
    assert before == after

    store.upsert(CatalogEntry(dataset=DATASET_HS300_INDEX, quality_status="fail", dataset_status="quality_failed"))
    failed = read_dataset(DATASET_HS300_INDEX, tmp_path)
    assert failed.status == "quality_failed"
    assert failed.frame is None

    warn_path = write_canonical(tmp_path, DATASET_INDEX_WEIGHTS, pd.DataFrame({"trade_date": ["2026-01-02"]}))
    store.upsert(
        CatalogEntry(
            dataset=DATASET_INDEX_WEIGHTS,
            quality_status="warn",
            dataset_status="available",
            canonical_path=str(warn_path.relative_to(tmp_path)),
        )
    )
    assert read_dataset(DATASET_INDEX_WEIGHTS, tmp_path).status == "unavailable"
    allowed = read_dataset(DATASET_INDEX_WEIGHTS, tmp_path, quality_policy=QualityPolicy(allow_warn=True))
    assert allowed.status == "available"
    assert allowed.issues == [{"code": "quality_warn", "dataset": DATASET_INDEX_WEIGHTS}]


def test_reader_missing_lake_root_is_structured(monkeypatch):
    monkeypatch.delenv("MARKET_DATA_LAKE_ROOT", raising=False)
    result = read_dataset(DATASET_PRICES, None, required=True)
    assert result.status == "required_missing"
    assert result.issues == [{"code": "lake_root_missing", "dataset": DATASET_PRICES}]


def test_pit_asof_gate_blocks_future_availability_and_missing_fields():
    good = pd.DataFrame(
        {
            "index_code": ["399300.SZ"],
            "con_code": ["000001.SZ"],
            "available_at": ["2026-01-02T09:00:00+08:00"],
            "decision_time": ["2026-01-02T16:00:00+08:00"],
        }
    )
    assert validate_pit_asof(good, dataset=DATASET_INDEX_WEIGHTS, keys=("index_code", "con_code")).passed

    future = good.copy()
    future["available_at"] = "2026-01-03T09:00:00+08:00"
    blocked = validate_pit_asof(future, dataset=DATASET_INDEX_WEIGHTS, keys=("index_code", "con_code"))
    assert blocked.status == "pit_failed"
    assert blocked.issues[0]["code"] == "future_availability"

    missing = validate_pit_asof(good.drop(columns=["available_at"]), dataset=DATASET_INDEX_WEIGHTS)
    assert missing.issues[0]["code"] == "pit_field_missing"


def test_adjustment_gate_and_clean_factor_panel_output():
    clean = prices_frame()
    assert validate_adjustment_consistency(clean, "qfq").passed
    result = read_factor_panel({DATASET_PRICES: clean}, adjustment_policy="qfq")
    assert result.status == "available"
    assert result.frame is not None
    assert result.frame.iloc[0]["close"] == 21.0

    conflict = pd.concat([prices_frame("qfq"), prices_frame("hfq")], ignore_index=True)
    assert validate_adjustment_consistency(conflict, "qfq").status == "adjustment_failed"
    assert read_factor_panel({DATASET_PRICES: conflict}, adjustment_policy="qfq").status == "adjustment_failed"

    missing = prices_frame().drop(columns=["adj_factor"])
    assert validate_adjustment_consistency(missing, "qfq").issues[0]["code"] == "adjusted_price_missing"


def test_generic_dataset_quality_fetch_status_is_separate_from_dataset_status(tmp_path):
    path = write_canonical(tmp_path, DATASET_INDEX_WEIGHTS, pd.DataFrame(
        [
            {
                "trade_date": "2026-01-02",
                "index_code": "399300.SZ",
                "con_code": "000001.SZ",
                "weight": 1.0,
                "effective_date": "2026-01-02",
                    "available_date": "2026-01-02",
                    "available_at": "2026-01-02T09:00:00+08:00",
                    "available_at_rule": "explicit_timestamp",
                    "pit_status": "pit_available",
                    "readiness_status": "available",
                    "source": SOURCE_TUSHARE,
                "source_interface": "index_weights.snapshot",
                "source_run_id": "run-s03",
                "schema_version": "1.0",
                "lineage_raw_checksum": "checksum-weights",
            }
        ]
    ))
    result = validate_dataset(
        DATASET_INDEX_WEIGHTS,
        tmp_path,
        ("2026-01-02", "2026-01-02"),
        validation_context={
            "canonical_paths": [path],
            "expected_dates": ["2026-01-02"],
            "fetch_status": "failed",
        },
    )
    assert result.fetch_status == "failed"
    assert result.dataset_status == "available"
    assert result.quality_status == "pass"


def test_readers_validation_catalog_have_no_connector_runtime_imports():
    for path in ("market_data/readers.py", "market_data/validation.py", "market_data/catalog.py"):
        tree = ast.parse(Path(path).read_text(encoding="utf-8"))
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.append(node.module)
        assert not any(name.startswith("market_data.connectors") for name in imports)
        assert "market_data.runtime" not in imports
