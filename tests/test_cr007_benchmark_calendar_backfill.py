import ast
import hashlib
import json
from pathlib import Path

import pandas as pd

from market_data.benchmarks import BenchmarkPolicy, resolve_hs300_benchmark
from market_data.catalog import CatalogEntry, CatalogStore
from market_data.cli import main
from market_data.contracts import (
    DATASET_HS300_INDEX,
    DATASET_TRADE_CALENDAR,
    INTERFACE_HS300_INDEX_DAILY,
    INTERFACE_TRADE_CALENDAR_DAILY,
    SOURCE_TUSHARE,
)
from market_data.lake_layout import LakeLayout
from market_data.readers import QualityPolicy, read_dataset
from market_data.storage import compute_idempotency_key, compute_params_hash


def run_cli(capsys, *args):
    code = main(list(args))
    captured = capsys.readouterr()
    stdout = json.loads(captured.out) if captured.out else {}
    stderr = json.loads(captured.err) if captured.err else {}
    return code, stdout, stderr


def write_canonical(lake_root: Path, dataset: str, frame: pd.DataFrame, run_id: str = "run-s02") -> Path:
    path = LakeLayout(lake_root).canonical_dataset_root(dataset) / f"run_id={run_id}" / "part.parquet"
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_parquet(path, index=False)
    return path


def append_raw_manifest(
    lake_root: Path,
    *,
    interface: str,
    run_id: str,
    batch_id: str,
    start_date: str,
    params: dict,
    rows: list[dict],
) -> None:
    layout = LakeLayout(lake_root)
    raw_path = layout.raw_batch_path(SOURCE_TUSHARE, interface, start_date, batch_id)
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    raw_payload = [
        {
            "_metadata": {
                "run_id": run_id,
                "batch_id": batch_id,
                "source": SOURCE_TUSHARE,
                "interface": interface,
                "params": params,
                "row_count": len(rows),
            }
        },
        *rows,
    ]
    raw_path.write_text(
        "\n".join(json.dumps(item, ensure_ascii=False, sort_keys=True) for item in raw_payload)
        + "\n",
        encoding="utf-8",
    )
    checksum = hashlib.sha256(raw_path.read_bytes()).hexdigest()
    params_hash = compute_params_hash(params)
    record = {
        "schema_version": "1.0",
        "run_id": run_id,
        "batch_id": batch_id,
        "idempotency_key": compute_idempotency_key(
            run_id,
            batch_id,
            SOURCE_TUSHARE,
            interface,
            params_hash,
        ),
        "source": SOURCE_TUSHARE,
        "interface": interface,
        "params": params,
        "params_hash": params_hash,
        "requested_at": "2026-05-21T00:00:00+00:00",
        "started_at": "2026-05-21T00:00:00+00:00",
        "finished_at": "2026-05-21T00:00:00+00:00",
        "attempts": 1,
        "status": "success",
        "raw_path": str(raw_path.relative_to(lake_root)),
        "raw_checksum": checksum,
        "raw_row_count": len(rows),
        "canonical_path": None,
        "error_type": None,
        "error_message": None,
        "retryable": None,
    }
    layout.manifest_path().parent.mkdir(parents=True, exist_ok=True)
    with layout.manifest_path().open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")


def calendar_raw_rows() -> list[dict]:
    return [
        {"cal_date": "20260102", "exchange": "SSE", "is_open": 1, "pretrade_date": "20251231"},
        {"cal_date": "20260103", "exchange": "SSE", "is_open": 0, "pretrade_date": "20260102"},
        {"cal_date": "20260104", "exchange": "SSE", "is_open": 0, "pretrade_date": "20260102"},
        {"cal_date": "20260105", "exchange": "SSE", "is_open": 1, "pretrade_date": "20260102"},
    ]


def hs300_raw_rows() -> list[dict]:
    return [
        {
            "ts_code": "399300.SZ",
            "trade_date": "20260102",
            "open": 3991.0,
            "high": 4010.0,
            "low": 3980.0,
            "close": 4000.0,
            "pre_close": 3990.0,
            "pct_chg": 0.25,
            "vol": 100.0,
            "amount": 200.0,
        },
        {
            "ts_code": "399300.SZ",
            "trade_date": "20260105",
            "open": 4001.0,
            "high": 4020.0,
            "low": 3990.0,
            "close": 4010.0,
            "pre_close": 4000.0,
            "pct_chg": 0.25,
            "vol": 101.0,
            "amount": 201.0,
        },
    ]


def canonical_calendar_frame() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "trade_date": "2026-01-02",
                "exchange": "SSE",
                "is_open": True,
                "pretrade_date": "2025-12-31",
                "source": SOURCE_TUSHARE,
                "source_interface": INTERFACE_TRADE_CALENDAR_DAILY,
                "source_run_id": "run-s02",
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
                "source_run_id": "run-s02",
                "schema_version": "1.0",
                "available_at": "2026-01-03T00:00:00+08:00",
                "available_at_rule": "date_only_next_open",
                "lineage_raw_checksum": "checksum-calendar",
            },
            {
                "trade_date": "2026-01-04",
                "exchange": "SSE",
                "is_open": False,
                "pretrade_date": "2026-01-02",
                "source": SOURCE_TUSHARE,
                "source_interface": INTERFACE_TRADE_CALENDAR_DAILY,
                "source_run_id": "run-s02",
                "schema_version": "1.0",
                "available_at": "2026-01-04T00:00:00+08:00",
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
                "source_run_id": "run-s02",
                "schema_version": "1.0",
                "available_at": "2026-01-05T00:00:00+08:00",
                "available_at_rule": "date_only_next_open",
                "lineage_raw_checksum": "checksum-calendar",
            },
        ]
    )


def canonical_hs300_frame(rows: list[dict] | None = None) -> pd.DataFrame:
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
            "source_run_id": "run-s02",
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
            "source_run_id": "run-s02",
            "schema_version": "1.0",
            "available_at": "2026-01-05T16:00:00+08:00",
            "available_at_rule": "daily_close_fact",
            "lineage_raw_checksum": "checksum-hs300",
        },
    ]
    return pd.DataFrame(base_rows)


def confirmed_policy(required: bool = False) -> BenchmarkPolicy:
    return BenchmarkPolicy.from_config(
        {"benchmark_kind": "price_index", "confirmed": True, "required": required},
        required=required,
    )


def write_available_lake(lake_root: Path, hs300_frame: pd.DataFrame | None = None) -> None:
    hs300_path = write_canonical(
        lake_root,
        DATASET_HS300_INDEX,
        hs300_frame if hs300_frame is not None else canonical_hs300_frame(),
    )
    calendar_path = write_canonical(lake_root, DATASET_TRADE_CALENDAR, canonical_calendar_frame())
    store = CatalogStore(lake_root)
    store.upsert(
        CatalogEntry(
            dataset=DATASET_HS300_INDEX,
            start_date="2026-01-02",
            end_date="2026-01-05",
            coverage={"numerator": 2, "denominator": 2, "ratio": 1.0},
            quality_status="pass",
            dataset_status="available",
            latest_manifest_run_id="run-s02",
            source=SOURCE_TUSHARE,
            source_interface=INTERFACE_HS300_INDEX_DAILY,
            lineage_raw_checksum="checksum-hs300",
            canonical_path=str(hs300_path.relative_to(lake_root)),
        )
    )
    store.upsert(
        CatalogEntry(
            dataset=DATASET_TRADE_CALENDAR,
            start_date="2026-01-02",
            end_date="2026-01-05",
            coverage={"numerator": 4, "denominator": 4, "ratio": 1.0},
            quality_status="pass",
            dataset_status="available",
            latest_manifest_run_id="run-s02",
            source=SOURCE_TUSHARE,
            source_interface=INTERFACE_TRADE_CALENDAR_DAILY,
            lineage_raw_checksum="checksum-calendar",
            canonical_path=str(calendar_path.relative_to(lake_root)),
        )
    )


def test_benchmark_calendar_backfill_plan_is_dry_run_and_zero_side_effect(tmp_path, capsys, monkeypatch):
    monkeypatch.setenv("TUSHARE_TOKEN", "secret-token-value")
    before = list(tmp_path.rglob("*"))

    code, payload, stderr = run_cli(
        capsys,
        "benchmark-calendar-backfill",
        "--lake-root",
        str(tmp_path),
        "--start-date",
        "2026-01-02",
        "--end-date",
        "2026-01-05",
        "--run-id",
        "run-s02-plan",
    )

    assert code == 0
    assert stderr == {}
    assert payload["command"] == "benchmark-calendar-backfill"
    assert payload["network_calls"] == 0
    assert payload["writes"] == 0
    assert payload["coverage_gate"]["denominator_mode"] == "trade_calendar_open_dates"
    assert payload["coverage_gate"]["denominator_filter"] == "trade_calendar.is_open == true"
    assert payload["coverage_gate"]["natural_day_denominator_allowed"] is False
    assert [item["dataset"] for item in payload["dataset_plans"]] == [
        DATASET_TRADE_CALENDAR,
        DATASET_HS300_INDEX,
    ]
    assert payload["old_data_operations"] == {
        "read": 0,
        "list": 0,
        "migrate": 0,
        "copy": 0,
        "compare": 0,
        "delete": 0,
    }
    assert "secret-token-value" not in json.dumps(payload, ensure_ascii=False)
    assert list(tmp_path.rglob("*")) == before


def test_trade_calendar_normalize_validate_catalog_and_read_feed_hs300_open_denominator(tmp_path, capsys):
    append_raw_manifest(
        tmp_path,
        interface=INTERFACE_TRADE_CALENDAR_DAILY,
        run_id="run-s02-calendar",
        batch_id="trade-calendar-b1",
        start_date="2026-01-02",
        params={
            "target_dataset": DATASET_TRADE_CALENDAR,
            "start_date": "2026-01-02",
            "end_date": "2026-01-05",
            "exchange": "SSE",
        },
        rows=calendar_raw_rows(),
    )
    append_raw_manifest(
        tmp_path,
        interface=INTERFACE_HS300_INDEX_DAILY,
        run_id="run-s02-hs300",
        batch_id="hs300-index-b1",
        start_date="2026-01-02",
        params={
            "target_dataset": DATASET_HS300_INDEX,
            "start_date": "2026-01-02",
            "end_date": "2026-01-05",
            "index_code": "399300.SZ",
        },
        rows=hs300_raw_rows(),
    )

    code, calendar_norm, _ = run_cli(
        capsys,
        "normalize",
        "--lake-root",
        str(tmp_path),
        "--dataset",
        DATASET_TRADE_CALENDAR,
        "--run-id",
        "run-s02-calendar",
    )
    assert code == 0
    assert calendar_norm["row_count"] == 4

    code, hs300_norm, _ = run_cli(
        capsys,
        "normalize",
        "--lake-root",
        str(tmp_path),
        "--dataset",
        DATASET_HS300_INDEX,
        "--run-id",
        "run-s02-hs300",
    )
    assert code == 0
    assert hs300_norm["row_count"] == 2

    code, calendar_quality, _ = run_cli(
        capsys,
        "validate",
        "--lake-root",
        str(tmp_path),
        "--dataset",
        DATASET_TRADE_CALENDAR,
        "--exchange",
        "SSE",
        "--start-date",
        "2026-01-02",
        "--end-date",
        "2026-01-05",
    )
    assert code == 0
    assert calendar_quality["quality_status"] == "pass"
    assert calendar_quality["denominator_mode"] == "calendar_days_in_requested_range_x_exchange"
    assert calendar_quality["coverage"]["expected_rows"] == 4
    code, calendar_publish, _ = run_cli(
        capsys,
        "publish",
        "--lake-root",
        str(tmp_path),
        "--dataset",
        DATASET_TRADE_CALENDAR,
    )
    assert code == 0
    assert calendar_publish["publish_status"] == "published"

    code, hs300_quality, _ = run_cli(
        capsys,
        "validate",
        "--lake-root",
        str(tmp_path),
        "--dataset",
        DATASET_HS300_INDEX,
        "--index-code",
        "399300.SZ",
        "--start-date",
        "2026-01-02",
        "--end-date",
        "2026-01-05",
    )
    assert code == 0
    assert hs300_quality["quality_status"] == "pass"
    assert hs300_quality["denominator_mode"] == "trade_calendar_open_dates"
    assert hs300_quality["coverage"]["expected_rows"] == 2
    assert hs300_quality["coverage"]["actual_rows"] == 2

    code, read_payload, _ = run_cli(
        capsys,
        "read",
        "--lake-root",
        str(tmp_path),
        "--dataset",
        DATASET_TRADE_CALENDAR,
        "--exchange",
        "SSE",
        "--start-date",
        "2026-01-02",
        "--end-date",
        "2026-01-05",
    )
    assert code == 0
    assert read_payload["row_count"] == 4
    assert {row["exchange"] for row in read_payload["sample"]} == {"SSE"}


def test_hs300_gap_and_calendar_missing_are_typed_by_open_calendar_denominator(tmp_path):
    gap_root = tmp_path / "gap"
    missing_hs300 = canonical_hs300_frame().iloc[[0]].reset_index(drop=True)
    write_available_lake(gap_root, missing_hs300)
    gap = resolve_hs300_benchmark(
        gap_root,
        "2026-01-02",
        "2026-01-05",
        confirmed_policy(required=True),
    )
    assert gap.status == "required_missing"
    assert gap.missing_reason == "coverage_gap"
    assert gap.coverage.denominator_mode == "trade_calendar_open_dates"
    assert gap.coverage.denominator == 2
    assert gap.coverage.missing_trade_dates == ["2026-01-05"]

    calendar_missing_root = tmp_path / "calendar-missing"
    hs300_path = write_canonical(calendar_missing_root, DATASET_HS300_INDEX, canonical_hs300_frame())
    CatalogStore(calendar_missing_root).upsert(
        CatalogEntry(
            dataset=DATASET_HS300_INDEX,
            quality_status="pass",
            dataset_status="available",
            latest_manifest_run_id="run-s02",
            source=SOURCE_TUSHARE,
            source_interface=INTERFACE_HS300_INDEX_DAILY,
            lineage_raw_checksum="checksum-hs300",
            canonical_path=str(hs300_path.relative_to(calendar_missing_root)),
        )
    )
    missing_calendar = resolve_hs300_benchmark(
        calendar_missing_root,
        "2026-01-02",
        "2026-01-05",
        confirmed_policy(required=True),
    )
    assert missing_calendar.status == "required_missing"
    assert missing_calendar.missing_reason == "calendar_missing"
    assert missing_calendar.coverage.denominator == 0


def test_resolver_requires_price_benchmark_overlap_when_price_trade_dates_are_supplied(tmp_path):
    write_available_lake(tmp_path)

    no_overlap = resolve_hs300_benchmark(
        tmp_path,
        "2026-01-02",
        "2026-01-05",
        confirmed_policy(required=True),
        price_trade_dates=["2026-01-03"],
    )
    assert no_overlap.status == "required_missing"
    assert no_overlap.missing_reason == "price_benchmark_overlap_missing"
    assert no_overlap.coverage.price_trade_dates_count == 1
    assert no_overlap.coverage.price_overlap_count == 0
    assert no_overlap.next_action is not None
    assert no_overlap.next_action.auto_execute is False

    available = resolve_hs300_benchmark(
        tmp_path,
        "2026-01-02",
        "2026-01-05",
        confirmed_policy(required=True),
        price_trade_dates=["2026-01-02"],
    )
    assert available.status == "available"
    assert available.coverage.price_overlap_count == 1


def test_reader_filters_exchange_quality_gate_and_import_boundaries(tmp_path):
    write_available_lake(tmp_path)
    calendar = read_dataset(
        DATASET_TRADE_CALENDAR,
        tmp_path,
        filters={"start": "2026-01-02", "end": "2026-01-05", "exchange": "SSE"},
        quality_policy=QualityPolicy(allow_warn=True),
        required=True,
    )
    assert calendar.available
    assert calendar.frame is not None
    assert calendar.frame["exchange"].unique().tolist() == ["SSE"]

    CatalogStore(tmp_path).upsert(
        CatalogEntry(
            dataset=DATASET_TRADE_CALENDAR,
            quality_status="fail",
            dataset_status="quality_failed",
            source=SOURCE_TUSHARE,
            source_interface=INTERFACE_TRADE_CALENDAR_DAILY,
        )
    )
    blocked = read_dataset(DATASET_TRADE_CALENDAR, tmp_path, required=True)
    assert blocked.status == "quality_failed"

    for source_path in ("market_data/readers.py", "market_data/benchmarks.py"):
        tree = ast.parse(Path(source_path).read_text(encoding="utf-8"))
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.append(node.module)
        assert not any(name.startswith("market_data.connectors") for name in imports)
        assert "market_data.runtime" not in imports
        assert "market_data.storage" not in imports
