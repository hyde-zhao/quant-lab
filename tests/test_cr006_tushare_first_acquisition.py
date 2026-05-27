import csv
import hashlib
import json

import pandas as pd
import pytest

from market_data.catalog import CatalogEntry, CatalogStore
from market_data.cli import (
    TushareFirstRunSpec,
    build_tushare_first_plan,
    emit_tushare_first_runbook_summary,
    main,
)
from market_data.connectors.protocol import ConnectorResult
from market_data.contracts import (
    DATASET_HS300_INDEX,
    INTERFACE_HS300_INDEX_DAILY,
    SOURCE_TUSHARE,
)
from market_data.lake_layout import LakeLayout
from market_data.normalization import normalize_run
from market_data.runtime import RuntimeContext, RuntimePolicy, execute_batches
from market_data.storage import ManifestWriter
from market_data.validation import QualityThresholds, validate_hs300_index, write_quality_reports


def run_cli(capsys, *args):
    code = main(list(args))
    captured = capsys.readouterr()
    stdout = json.loads(captured.out) if captured.out else {}
    stderr = json.loads(captured.err) if captured.err else {}
    return code, stdout, stderr


def test_tushare_first_plan_requires_explicit_external_lake_and_has_no_side_effect(capsys, tmp_path):
    code, payload, stderr = run_cli(
        capsys,
        "tushare-first-acquire",
        "--dataset",
        DATASET_HS300_INDEX,
        "--lake-root",
        "data/market_data",
        "--start-date",
        "2026-01-02",
        "--end-date",
        "2026-01-05",
    )
    assert code == 2
    assert payload == {}
    assert stderr["error_type"] == "old_data_reference_only"

    code, payload, stderr = run_cli(
        capsys,
        "tushare-first-acquire",
        "--dataset",
        DATASET_HS300_INDEX,
        "--lake-root",
        str(tmp_path),
        "--start-date",
        "2026-01-02",
        "--end-date",
        "2026-01-05",
        "--run-id",
        "run-cr006",
        "--batch-id",
        "b1",
    )
    assert code == 0
    assert stderr == {}
    assert payload["dataset"] == DATASET_HS300_INDEX
    assert payload["source"] == SOURCE_TUSHARE
    assert payload["interface"] == INTERFACE_HS300_INDEX_DAILY
    assert payload["lake_root"] == "<configured-lake-root>"
    assert payload["dry_run"] is True
    assert payload["network_calls"] == 0
    assert payload["writes"] == 0
    assert payload["runtime_consumers_for_raw_manifest"] == []
    assert payload["old_data_operations"] == {
        "read": 0,
        "list": 0,
        "migrate": 0,
        "copy": 0,
        "compare": 0,
        "delete": 0,
    }
    assert payload["runbook_summary"]["old_data_reference_only"] is True
    assert not list(tmp_path.rglob("*"))


def test_tushare_first_plan_rejects_unknown_interface_date_and_real_gate(capsys, tmp_path, monkeypatch):
    code, _, stderr = run_cli(
        capsys,
        "tushare-first-acquire",
        "--dataset",
        DATASET_HS300_INDEX,
        "--interface",
        "index_daily",
        "--lake-root",
        str(tmp_path),
        "--start-date",
        "2026-01-02",
        "--end-date",
        "2026-01-05",
    )
    assert code == 2
    assert stderr["error_type"] == "interface_not_allowed"

    code, _, stderr = run_cli(
        capsys,
        "tushare-first-acquire",
        "--dataset",
        DATASET_HS300_INDEX,
        "--lake-root",
        str(tmp_path),
        "--start-date",
        "2026-13-02",
        "--end-date",
        "2026-01-05",
    )
    assert code == 2
    assert stderr["error_type"] == "invalid_date_range"

    code, _, stderr = run_cli(
        capsys,
        "tushare-first-acquire",
        "--dataset",
        DATASET_HS300_INDEX,
        "--lake-root",
        str(tmp_path),
        "--start-date",
        "2026-01-02",
        "--end-date",
        "2026-01-05",
        "--dry-run",
        "false",
    )
    assert code == 2
    assert stderr["error_type"] == "source_disabled"
    assert not list(tmp_path.rglob("*"))

    monkeypatch.delenv("TUSHARE_TOKEN", raising=False)
    code, _, stderr = run_cli(
        capsys,
        "tushare-first-acquire",
        "--dataset",
        DATASET_HS300_INDEX,
        "--lake-root",
        str(tmp_path),
        "--start-date",
        "2026-01-02",
        "--end-date",
        "2026-01-05",
        "--dry-run",
        "false",
        "--enable-real-source",
    )
    assert code == 2
    assert stderr["error_type"] == "missing_credential"
    assert "TUSHARE_TOKEN" in stderr["error_message"]
    assert not list(tmp_path.rglob("*"))


class FakeTushareConnector:
    def fetch(self, request):
        return ConnectorResult(
            source=request.source,
            interface=request.interface,
            rows=[
                {
                    "ts_code": "399300.SZ",
                    "trade_date": "20260102",
                    "close": 4000.0,
                    "pre_close": 3990.0,
                    "pct_chg": 0.25,
                    "open": 3991.0,
                    "high": 4010.0,
                    "low": 3980.0,
                    "vol": 100.0,
                    "amount": 200.0,
                }
            ],
            metadata={"target_dataset": DATASET_HS300_INDEX},
        )


def test_raw_manifest_to_canonical_quality_catalog_lineage(tmp_path):
    spec = TushareFirstRunSpec(
        dataset=DATASET_HS300_INDEX,
        start_date="2026-01-02",
        end_date="2026-01-02",
        lake_root=str(tmp_path),
        run_id="run-cr006",
        batch_id="b1",
        dry_run=False,
    )
    plan = build_tushare_first_plan(spec)
    request = {
        "source": SOURCE_TUSHARE,
        "interface": plan["interface"],
        "params": {
            **plan["params"],
            "explicit_real_execution": True,
            "offline": False,
        },
        "run_id": plan["run_id"],
        "batch_id": plan["batch_id"],
    }
    results = execute_batches(
        [request],
        FakeTushareConnector(),
        LakeLayout(tmp_path),
        RuntimePolicy(max_retries=0, throttle_seconds=0.0),
        context=RuntimeContext("run-cr006"),
    )
    assert results[0].status == "success"

    layout = LakeLayout(tmp_path)
    manifest_record = results[0].manifest_record
    assert manifest_record["source"] == SOURCE_TUSHARE
    assert manifest_record["interface"] == INTERFACE_HS300_INDEX_DAILY
    assert manifest_record["raw_checksum"]
    assert manifest_record["raw_row_count"] == 1

    normalized = normalize_run(layout.manifest_path(), tmp_path, dataset=DATASET_HS300_INDEX)
    frame = pd.read_parquet(normalized.canonical_paths[0])
    assert frame.iloc[0]["source_interface"] == INTERFACE_HS300_INDEX_DAILY
    assert frame.iloc[0]["source_run_id"] == "run-cr006"
    assert frame.iloc[0]["lineage_raw_checksum"] == manifest_record["raw_checksum"]

    trade_calendar = pd.DataFrame(
        [{"trade_date": "2026-01-02", "exchange": "SSE", "is_open": True}]
    )
    quality = validate_hs300_index(
        tmp_path,
        "399300.SZ",
        ("2026-01-02", "2026-01-02"),
        trade_calendar,
        QualityThresholds(),
        canonical_paths=normalized.canonical_paths,
    )
    csv_path, md_path = write_quality_reports(quality, layout)
    row = next(csv.DictReader(csv_path.open("r", encoding="utf-8")))
    assert row["quality_status"] == "pass"
    assert row["source_interface"] == INTERFACE_HS300_INDEX_DAILY
    assert row["lineage_raw_checksum"] == manifest_record["raw_checksum"]

    CatalogStore(layout).upsert(
        CatalogEntry(
            dataset=DATASET_HS300_INDEX,
            coverage=quality.to_csv_row(),
            quality_status=quality.quality_status,
            dataset_status=quality.dataset_status,
            latest_manifest_run_id=quality.manifest_run_id,
            source=quality.source_name,
            source_interface=quality.source_interface,
            lineage_raw_checksum=quality.lineage_raw_checksum,
            canonical_path=str(normalized.canonical_paths[0].relative_to(layout.lake_root)),
            quality_csv_path=str(csv_path.relative_to(layout.lake_root)),
            quality_path=str(md_path.relative_to(layout.lake_root)),
        )
    )
    catalog_entry = CatalogStore(layout).get(DATASET_HS300_INDEX)
    assert catalog_entry.quality_status == "pass"
    assert catalog_entry.latest_manifest_run_id == "run-cr006"
    assert catalog_entry.lineage_raw_checksum == manifest_record["raw_checksum"]


def test_runbook_summary_and_manifest_guard_do_not_expose_sensitive_values(tmp_path, monkeypatch):
    monkeypatch.setenv("TUSHARE_TOKEN", "secret-value")
    plan = build_tushare_first_plan(
        TushareFirstRunSpec(
            dataset=DATASET_HS300_INDEX,
            start_date="2026-01-02",
            end_date="2026-01-02",
            lake_root=str(tmp_path),
            run_id="run-cr006",
        )
    )
    summary = emit_tushare_first_runbook_summary(plan)
    serialized = json.dumps({"plan": plan, "summary": summary}, ensure_ascii=False)
    assert "secret-value" not in serialized
    assert str(tmp_path) not in serialized
    assert summary["safe_lake_root"] == "<configured-lake-root>"

    layout = LakeLayout(tmp_path)
    unsafe_record = {
        "schema_version": "1.0",
        "run_id": "run-cr006",
        "batch_id": "b1",
        "idempotency_key": hashlib.sha256(b"x").hexdigest(),
        "source": SOURCE_TUSHARE,
        "interface": INTERFACE_HS300_INDEX_DAILY,
        "params": {"token": "secret-value"},
        "params_hash": hashlib.sha256(b"params").hexdigest(),
        "requested_at": "2026-05-19T00:00:00+00:00",
        "started_at": "2026-05-19T00:00:00+00:00",
        "finished_at": "2026-05-19T00:00:00+00:00",
        "attempts": 1,
        "status": "failed",
        "raw_path": None,
        "raw_checksum": None,
        "raw_row_count": None,
        "canonical_path": None,
        "error_type": "missing_credential",
        "error_message": "safe error",
        "retryable": False,
    }
    with pytest.raises(ValueError, match="敏感"):
        ManifestWriter().append(unsafe_record, layout)
    assert not layout.manifest_path().exists()
