import csv
import hashlib
import importlib
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import pytest

from market_data.catalog import CatalogEntry, CatalogStore
from market_data.connectors.fake import FakeConnector
from market_data.connectors.protocol import ConnectorRequest
from market_data.contracts import DATASET_PRICES
from market_data.lake_layout import LakeLayout
from market_data.normalization import (
    CanonicalSchemaError,
    DatasetMappingError,
    ManifestLineageError,
    map_raw_to_dataset,
    normalize_run,
)
from market_data.readers import ReaderBoundaryError, read_canonical
from market_data.runtime import RuntimeContext, RuntimePolicy, execute_batches
from market_data.storage import read_manifest_records
from market_data.validation import (
    DENOMINATOR_MODE_PRICES,
    QualityThresholds,
    validate_dataset,
    write_quality_reports,
)


def fixed_clock():
    return datetime(2026, 5, 17, 5, 0, tzinfo=timezone.utc)


def batch(batch_id="b1", params=None):
    return ConnectorRequest(
        source="fake",
        interface="prices.daily",
        params=params
        or {
            "symbols": ["000001.SZ", "000002.SZ"],
            "start_date": "2026-01-02",
            "end_date": "2026-01-03",
            "seed": 7,
            "target_dataset": "prices",
        },
        run_id="run-1",
        batch_id=batch_id,
    )


def build_success_lake(tmp_path):
    layout = LakeLayout(tmp_path)
    execute_batches(
        [batch()],
        FakeConnector(seed=7),
        layout,
        RuntimePolicy(),
        context=RuntimeContext("run-1"),
        clock=fixed_clock,
    )
    return layout


def test_normalize_run_writes_canonical_and_preserves_lineage(tmp_path):
    layout = build_success_lake(tmp_path)

    result = normalize_run(layout.manifest_path(), tmp_path, dataset=DATASET_PRICES)

    assert result.row_count == 4
    assert result.run_id == "run-1"
    assert len(result.canonical_paths) == 1
    frame = pd.read_parquet(result.canonical_paths[0])
    assert set(frame.columns) >= {
        "trade_date",
        "symbol",
        "close",
        "source",
        "source_run_id",
        "adjustment_policy",
        "available_at",
    }
    assert set(frame["source_run_id"]) == {"run-1"}
    assert str(result.canonical_paths[0]).endswith(
        "canonical/prices/1.0/run_id=run-1/part-b1.parquet"
    )


def test_normalize_skips_non_success_terminal_status(tmp_path):
    layout = LakeLayout(tmp_path)
    execute_batches(
        [batch("b1"), batch("b2")],
        FakeConnector(seed=7, failure_plan={"b2": "partial_success"}),
        layout,
        RuntimePolicy(),
        context=RuntimeContext("run-1"),
        clock=fixed_clock,
    )

    result = normalize_run(layout.manifest_path(), tmp_path, dataset=DATASET_PRICES)

    assert result.row_count == 4
    assert result.skipped_status_counts == {"partial_success": 1}


def test_raw_to_dataset_mapping_is_explicit_or_exact_only():
    assert (
        map_raw_to_dataset({"params": {"target_dataset": "prices"}, "interface": "other"})
        == "prices"
    )
    assert map_raw_to_dataset({"params": {}, "interface": "prices.daily"}) == "prices"

    with pytest.raises(DatasetMappingError):
        map_raw_to_dataset({"params": {"target_dataset": "Prices"}, "interface": "prices.daily"})
    with pytest.raises(DatasetMappingError):
        map_raw_to_dataset({"params": {}, "interface": "daily_prices"})
    with pytest.raises(DatasetMappingError):
        map_raw_to_dataset({"params": {}, "interface": "PRICES.DAILY"})


def test_checksum_row_count_and_source_run_id_are_verified(tmp_path):
    layout = build_success_lake(tmp_path)
    record = read_manifest_records(layout)[0]
    raw_path = tmp_path / record["raw_path"]
    raw_path.write_text(raw_path.read_text(encoding="utf-8") + "\n", encoding="utf-8")

    with pytest.raises(ManifestLineageError, match="checksum"):
        normalize_run(layout.manifest_path(), tmp_path, dataset=DATASET_PRICES)

    build_success_lake(tmp_path / "second")
    layout2 = LakeLayout(tmp_path / "second")
    record2 = read_manifest_records(layout2)[0]
    raw2 = tmp_path / "second" / record2["raw_path"]
    lines = raw2.read_text(encoding="utf-8").splitlines()
    row = json.loads(lines[1])
    row["source_run_id"] = "other-run"
    lines[1] = json.dumps(row, ensure_ascii=False, sort_keys=True)
    raw2.write_text("\n".join(lines) + "\n", encoding="utf-8")
    checksum = hashlib.sha256(raw2.read_bytes()).hexdigest()
    manifest_path = layout2.manifest_path()
    manifest = read_manifest_records(layout2)[0]
    manifest["raw_checksum"] = checksum
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False) + "\n", encoding="utf-8")

    with pytest.raises(ManifestLineageError, match="source_run_id"):
        normalize_run(layout2.manifest_path(), tmp_path / "second", dataset=DATASET_PRICES)


def test_missing_raw_required_field_fails_schema(tmp_path):
    layout = build_success_lake(tmp_path)
    record = read_manifest_records(layout)[0]
    raw_path = tmp_path / record["raw_path"]
    lines = raw_path.read_text(encoding="utf-8").splitlines()
    row = json.loads(lines[1])
    row.pop("available_at")
    lines[1] = json.dumps(row, ensure_ascii=False, sort_keys=True)
    raw_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    record["raw_checksum"] = hashlib.sha256(raw_path.read_bytes()).hexdigest()
    layout.manifest_path().write_text(json.dumps(record, ensure_ascii=False) + "\n", encoding="utf-8")

    with pytest.raises(CanonicalSchemaError, match="available_at"):
        normalize_run(layout.manifest_path(), tmp_path, dataset=DATASET_PRICES)


def test_validate_dataset_outputs_coverage_statuses_thresholds_and_reports(tmp_path):
    layout = build_success_lake(tmp_path)
    norm = normalize_run(layout.manifest_path(), tmp_path, dataset=DATASET_PRICES)

    quality = validate_dataset(
        DATASET_PRICES,
        tmp_path,
        ("2026-01-02", "2026-01-03"),
        ["000001.SZ", "000002.SZ"],
        QualityThresholds(),
        {
            "canonical_paths": norm.canonical_paths,
            "manifest_records": list(norm.manifest_records),
            "open_trade_dates": ["2026-01-02", "2026-01-03"],
        },
        clock=fixed_clock,
    )
    csv_path, md_path = write_quality_reports(quality, layout)

    row = next(csv.DictReader(csv_path.open("r", encoding="utf-8")))
    assert row["run_id"] == "run-1"
    assert row["fetch_status"] == "success"
    assert row["dataset_status"] in {"pass", "warn"}
    assert row["quality_status"] in {"pass", "warn"}
    assert row["denominator_mode"] == DENOMINATOR_MODE_PRICES
    assert row["expected_rows"] == "4"
    assert row["actual_rows"] == "4"
    assert row["missing_rows"] == "0"
    assert row["source_name"] == "fake"
    assert row["source_interface"] == "prices.daily"
    assert row["target_dataset"] == "prices"
    assert row["input_config_hash"]
    assert row["is_pit_universe"] == "False"
    assert row["universe_mode"] == "non_pit_static"
    assert row["pit_status"] == "non_pit_disclosed"
    for name in (
        "thresholds_json",
        "missing_required_fields_json",
        "duplicate_keys_json",
        "negative_price_rows_json",
        "coverage_gaps_json",
        "manifest_inconsistencies_json",
        "warnings_json",
    ):
        assert name.endswith("_json")
        json.loads(row[name])
    assert "Markdown 仅供人工阅读" in md_path.read_text(encoding="utf-8")


def test_validation_detects_schema_duplicate_negative_price_and_coverage(tmp_path):
    layout = LakeLayout(tmp_path)
    canonical_dir = layout.canonical_dataset_root("prices") / "run_id=run-1"
    canonical_dir.mkdir(parents=True)
    bad = pd.DataFrame(
        [
            {
                "trade_date": "2026-01-02",
                "symbol": "000001.SZ",
                "close": -1.0,
                "source": "fake",
                "source_run_id": "run-1",
                "adjustment_policy": "none",
                "available_at": "2026-01-02T16:00:00+08:00",
            },
            {
                "trade_date": "2026-01-02",
                "symbol": "000001.SZ",
                "close": 10.0,
                "source": "fake",
                "source_run_id": "run-1",
                "adjustment_policy": "none",
                "available_at": "2026-01-02T16:00:00+08:00",
            },
        ]
    )
    path = canonical_dir / "part-bad.parquet"
    bad.to_parquet(path, index=False)

    quality = validate_dataset(
        "prices",
        tmp_path,
        ("2026-01-02", "2026-01-03"),
        ["000001.SZ", "000002.SZ"],
        validation_context={
            "canonical_paths": [path],
            "manifest_records": [
                {
                    "run_id": "run-1",
                    "source": "fake",
                    "interface": "prices.daily",
                    "status": "success",
                }
            ],
            "open_trade_dates": ["2026-01-02", "2026-01-03"],
        },
        clock=fixed_clock,
    )

    assert quality.quality_status == "fail"
    assert quality.dataset_status == "fail"
    assert quality.duplicate_keys
    assert quality.negative_price_rows
    assert quality.coverage.expected_rows == 4
    assert quality.coverage.missing_rows == 2

    missing_path = canonical_dir / "part-missing.parquet"
    bad.drop(columns=["available_at"]).to_parquet(missing_path, index=False)
    missing_quality = validate_dataset(
        "prices",
        tmp_path,
        ("2026-01-02", "2026-01-02"),
        ["000001.SZ"],
        validation_context={"canonical_paths": [missing_path], "open_trade_dates": ["2026-01-02"]},
        clock=fixed_clock,
    )
    assert "available_at" in missing_quality.missing_required_fields
    assert missing_quality.quality_status == "fail"


def test_catalog_upsert_read_and_reader_filters_without_writes(tmp_path):
    layout = build_success_lake(tmp_path)
    norm = normalize_run(layout.manifest_path(), tmp_path, dataset=DATASET_PRICES)
    quality = validate_dataset(
        "prices",
        tmp_path,
        ("2026-01-02", "2026-01-03"),
        ["000001.SZ", "000002.SZ"],
        validation_context={
            "canonical_paths": norm.canonical_paths,
            "manifest_records": list(norm.manifest_records),
            "open_trade_dates": ["2026-01-02", "2026-01-03"],
        },
        clock=fixed_clock,
    )
    csv_path, _ = write_quality_reports(quality, layout)
    store = CatalogStore(layout)
    store.upsert(
        CatalogEntry(
            dataset="prices",
            coverage=quality.to_csv_row(),
            quality_status=quality.quality_status,
            latest_manifest_run_id=quality.run_id,
            canonical_path=str(norm.canonical_paths[0].relative_to(tmp_path)),
            quality_csv_path=str(csv_path.relative_to(tmp_path)),
            generated_at=quality.generated_at,
        )
    )

    entry = store.get("prices")
    assert entry.latest_manifest_run_id == "run-1"
    before = {path: path.stat().st_mtime_ns for path in tmp_path.rglob("*") if path.is_file()}
    frame = read_canonical(
        "prices",
        tmp_path,
        start="2026-01-03",
        end="2026-01-03",
        symbols=["000001.SZ"],
        columns=["trade_date", "symbol", "close"],
    )
    after = {path: path.stat().st_mtime_ns for path in tmp_path.rglob("*") if path.is_file()}
    assert before == after
    assert list(frame.columns) == ["trade_date", "symbol", "close"]
    assert len(frame) == 1
    assert frame.iloc[0]["symbol"] == "000001.SZ"

    with pytest.raises(ReaderBoundaryError):
        read_canonical("Prices", tmp_path)


def test_reader_module_has_no_connector_runtime_storage_imports(monkeypatch):
    def deny_connect(*args, **kwargs):
        raise AssertionError("network must not be used")

    monkeypatch.setattr("socket.socket.connect", deny_connect)
    module = importlib.import_module("market_data.readers")
    source = Path(module.__file__).read_text(encoding="utf-8")
    assert "market_data.connectors" not in source
    assert "market_data.runtime" not in source
    assert "market_data.storage" not in source
    assert "connectors" not in source
    assert "runtime" not in source
    assert "storage" not in source
