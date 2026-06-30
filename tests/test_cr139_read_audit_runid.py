from __future__ import annotations

import pandas as pd

from market_data.catalog import CatalogEntry
from market_data.contracts import DATASET_PRICES, QUALITY_STATUS_PASS, READINESS_STATUS_AVAILABLE, SCHEMA_VERSION
from market_data.readers import ReaderResult, build_reader_audit_record
from trading.strategy_runner.evidence_index import RunEvidenceIndex


def test_s27_read_audit_records_available_reader_run_ids() -> None:
    result = ReaderResult(
        status="available",
        frame=pd.DataFrame(
            {
                "symbol": ["000001", "000002"],
                "trade_date": ["20260102", "20260102"],
                "source_run_id": ["run-cr139-s27-data", "run-cr139-s27-data"],
            }
        ),
        catalog_entry=_catalog_entry(),
    )

    audit = build_reader_audit_record(
        DATASET_PRICES,
        result,
        reader_name="read_dataset",
        requested_as_of="2026-01-03T09:30:00+08:00",
        strategy_run_id="strategy-run-s27",
    )
    payload = audit.to_dict()

    assert payload["dataset"] == DATASET_PRICES
    assert payload["status"] == "available"
    assert payload["catalog_run_id"] == "run-cr139-s27-data"
    assert payload["source_run_ids"] == ["run-cr139-s27-data"]
    assert payload["row_count"] == 2
    assert payload["audit_id"].startswith("read-audit-")


def test_s27_read_audit_payload_can_feed_run_evidence_index_lineage() -> None:
    result = ReaderResult(
        status="available",
        frame=pd.DataFrame({"source_run_id": ["run-cr139-s27-data"]}),
        catalog_entry=_catalog_entry(),
    )
    audit = build_reader_audit_record(DATASET_PRICES, result, reader_name="read_dataset")

    index = RunEvidenceIndex(
        run_id="strategy-run-s27",
        status="pass",
        passed=True,
        package_id="pkg",
        data_run_id=audit.catalog_run_id or "",
        source_run_id=audit.source_run_ids[0],
        lineage_status=audit.status,
    )
    payload = index.to_dict()

    assert payload["data_lineage"]["data_run_id"] == "run-cr139-s27-data"
    assert payload["data_lineage"]["source_run_id"] == "run-cr139-s27-data"
    assert payload["qmt_allowed"] is False
    assert payload["not_authorization"] is True


def test_s27_read_audit_records_blocked_reader_issue_codes() -> None:
    result = ReaderResult(
        status="required_missing",
        issues=[{"code": "catalog_missing", "dataset": DATASET_PRICES}],
        remediation_spec={"action": "run_explicit_market_data_job", "dataset": DATASET_PRICES},
    )

    audit = build_reader_audit_record(DATASET_PRICES, result, reader_name="read_dataset")

    assert audit.status == "required_missing"
    assert audit.issue_codes == ("catalog_missing",)
    assert audit.row_count == 0
    assert audit.remediation_action == "run_explicit_market_data_job"


def _catalog_entry() -> CatalogEntry:
    return CatalogEntry(
        dataset=DATASET_PRICES,
        schema_version=SCHEMA_VERSION,
        start_date="20260102",
        end_date="20260102",
        quality_status=QUALITY_STATUS_PASS,
        dataset_status="available",
        latest_manifest_run_id="run-cr139-s27-data",
        source="fixture",
        source_interface="fixture.prices.daily",
        canonical_path=f"canonical/{DATASET_PRICES}/{SCHEMA_VERSION}/run_id=run-cr139-s27-data",
        published=True,
        published_at="2026-06-30T11:55:00+08:00",
        readiness_status=READINESS_STATUS_AVAILABLE,
        coverage_denominator=2,
        coverage_ratio=1.0,
        coverage_start="20260102",
        coverage_end="20260102",
        lineage_checksum="lineage-fixture",
        as_of_trade_date="20260102",
    )
