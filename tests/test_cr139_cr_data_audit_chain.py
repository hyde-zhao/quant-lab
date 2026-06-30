from market_data.catalog import CatalogEntry, build_catalog_manifest_pair
from market_data.contracts import QUALITY_STATUS_PASS, READINESS_STATUS_AVAILABLE


def test_cr_data_audit_chain_keeps_cr_and_lineage_refs_together():
    lineage = {
        "source_run_id": "source-run",
        "data_run_id": "data-run",
        "publish_run_id": "publish-run",
        "manifest_ref": "manifest/ref.jsonl",
        "triggered_by_cr": "CR139",
        "lineage_checksum": "sha256:lineage",
    }
    entry = CatalogEntry(
        dataset="prices",
        start_date="2026-01-01",
        end_date="2026-01-31",
        quality_status=QUALITY_STATUS_PASS,
        readiness_status=READINESS_STATUS_AVAILABLE,
        latest_manifest_run_id="data-run",
        source="tushare",
        source_interface="daily",
        lineage_checksum=lineage["lineage_checksum"],
        canonical_path="/lake/published/prices",
        coverage_denominator=21,
        published_at="2026-02-01T00:00:00+08:00",
        known_limitations=[],
        universe_scope="all_a",
        as_of_trade_date="2026-01-31",
        manifest_ref="manifest/ref.jsonl",
        triggered_by_cr="CR139",
        run_lineage=lineage,
        audit_refs=["process/evidence/STORY-CR139-S39.CP6.index.json"],
    )

    pair = build_catalog_manifest_pair(entry, triggered_by_cr="CR139")

    assert pair["manifest_record"]["metadata"]["triggered_by_cr"] == "CR139"
    assert pair["manifest_record"]["metadata"]["run_lineage"]["data_run_id"] == "data-run"
    assert pair["current_pointer_publish_count"] == 0
