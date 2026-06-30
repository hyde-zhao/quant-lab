from market_data.catalog import (
    CatalogEntry,
    build_catalog_manifest_pair,
    validate_catalog_manifest_consistency,
)
from market_data.contracts import QUALITY_STATUS_PASS, READINESS_STATUS_AVAILABLE


def test_catalog_manifest_are_derived_from_one_source_of_truth():
    entry = CatalogEntry(
        dataset="prices",
        start_date="2026-01-01",
        end_date="2026-01-31",
        quality_status=QUALITY_STATUS_PASS,
        readiness_status=READINESS_STATUS_AVAILABLE,
        latest_manifest_run_id="cr139-w2-prices-tushare-20260131-canonical",
        source="tushare",
        source_interface="daily",
        lineage_checksum="sha256:lineage",
        canonical_path="/lake/published/prices",
        coverage_denominator=21,
        published_at="2026-02-01T00:00:00+08:00",
        known_limitations=[],
        universe_scope="all_a",
        as_of_trade_date="2026-01-31",
    )

    pair = build_catalog_manifest_pair(
        entry,
        manifest_ref="manifest/prices.jsonl",
        triggered_by_cr="CR139",
    )
    check = validate_catalog_manifest_consistency(entry, pair["manifest_record"])

    assert pair["source_of_truth"] == "catalog"
    assert pair["catalog_writes"] == 0
    assert pair["manifest_writes"] == 0
    assert check.passed
