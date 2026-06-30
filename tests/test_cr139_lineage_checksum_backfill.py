from market_data.manifest import (
    build_run_lineage,
    compute_lineage_checksum,
    validate_lineage_checksum,
)


def test_lineage_checksum_is_stable_and_embedded_in_run_lineage():
    payload = {
        "source_run_id": "src-1",
        "data_run_id": "data-1",
        "publish_run_id": "pub-1",
        "manifest_ref": "manifest/ref.jsonl",
        "triggered_by_cr": "CR139",
    }

    checksum = compute_lineage_checksum(payload)
    lineage = build_run_lineage(**payload)

    assert checksum == lineage["lineage_checksum"]
    assert validate_lineage_checksum(lineage, checksum)
