from pathlib import Path

from market_data.catalog import (
    CATALOG_POINTER_INCOMPLETE,
    CR014_CATALOG_POINTER_REQUIRED_FIELDS,
    DUCKDB_GLOB_NOT_ALLOWED,
    CatalogPointer,
    validate_catalog_pointer,
    validate_duckdb_read_path,
)
from market_data.contracts import (
    CR014_FORBIDDEN_OPERATION_COUNTERS,
    CR014_UNIVERSE_SCOPE_ALL_A_SHARE,
    DATASET_PRICES,
    QUALITY_STATUS_PASS,
    READINESS_STATUS_AVAILABLE,
    SCHEMA_VERSION,
)
from market_data.lake_layout import LakeLayout, is_duckdb_read_path_allowed
from market_data.manifest import MANIFEST_INCOMPLETE, ManifestRecord, validate_manifest_record
from market_data.publish import (
    PUBLISH_NOT_AUTHORIZED,
    PublishIntent,
    publish_current_pointer,
    validate_publish_candidate,
)


def _pointer(layout: LakeLayout) -> CatalogPointer:
    published_path = layout.published_dataset_root(DATASET_PRICES, SCHEMA_VERSION)
    return CatalogPointer(
        dataset=DATASET_PRICES,
        schema_version=SCHEMA_VERSION,
        coverage_start="1990-12-19",
        coverage_end="2026-05-26",
        coverage_denominator=2,
        latest_manifest_run_id="run-cr014-s02",
        lineage_checksum="lineage-fixture",
        published_at="2026-05-27T00:00:00+00:00",
        known_limitations=[],
        universe_scope=CR014_UNIVERSE_SCOPE_ALL_A_SHARE,
        as_of_trade_date="2026-05-26",
        published_path=str(published_path),
        quality_status=QUALITY_STATUS_PASS,
        readiness_status=READINESS_STATUS_AVAILABLE,
    )


def _manifest(layout: LakeLayout) -> ManifestRecord:
    candidate_path = layout.candidate_dataset_root(
        DATASET_PRICES,
        SCHEMA_VERSION,
        "run-cr014-s02",
    )
    return ManifestRecord(
        run_id="run-cr014-s02",
        dataset=DATASET_PRICES,
        source="fixture",
        source_interface="fixture.prices.daily",
        schema_hash="schema-fixture",
        row_count=2,
        quality_status=QUALITY_STATUS_PASS,
        readiness_status=READINESS_STATUS_AVAILABLE,
        lineage_checksum="lineage-fixture",
        lifecycle_denominator_ref="cr014-s01-denominator-fixture",
        candidate_path=str(candidate_path),
    )


def test_catalog_pointer_required_fields_complete_and_missing_blocks_current_truth(tmp_path: Path) -> None:
    layout = LakeLayout(tmp_path)
    pointer = _pointer(layout)

    assert set(CR014_CATALOG_POINTER_REQUIRED_FIELDS) == {
        "dataset",
        "schema_version",
        "coverage_start",
        "coverage_end",
        "coverage_denominator",
        "latest_manifest_run_id",
        "lineage_checksum",
        "published_at",
        "known_limitations",
        "universe_scope",
        "as_of_trade_date",
    }
    passed = validate_catalog_pointer(pointer)
    assert passed.passed is True
    assert passed.current_truth_visible is True

    payload = pointer.to_dict()
    payload.pop("coverage_denominator")
    failed = validate_catalog_pointer(payload)

    assert failed.passed is False
    assert failed.current_truth_visible is False
    assert failed.missing_fields == ("coverage_denominator",)
    assert CATALOG_POINTER_INCOMPLETE in failed.error_codes


def test_manifest_record_completeness_blocks_publish_when_required_field_missing(tmp_path: Path) -> None:
    manifest = _manifest(LakeLayout(tmp_path))

    passed = validate_manifest_record(manifest)
    assert passed.passed is True
    assert passed.publish_allowed is True

    payload = manifest.to_dict()
    payload["schema_hash"] = ""
    failed = validate_manifest_record(payload)
    assert failed.passed is False
    assert failed.publish_allowed is False
    assert failed.missing_fields == ("schema_hash",)
    assert MANIFEST_INCOMPLETE in failed.error_codes


def test_validate_pass_without_publish_intent_never_changes_current_pointer(tmp_path: Path) -> None:
    layout = LakeLayout(tmp_path)
    pointer = _pointer(layout)
    manifest = _manifest(layout)

    result = validate_publish_candidate(
        pointer,
        quality={
            "quality_status": QUALITY_STATUS_PASS,
            "readiness_status": READINESS_STATUS_AVAILABLE,
        },
        manifest=manifest,
        lifecycle={
            "coverage_denominator": pointer.coverage_denominator,
            "lifecycle_denominator_ref": manifest.lifecycle_denominator_ref,
        },
        intent=PublishIntent(publish=False),
    )

    assert result.publish_allowed is False
    assert result.pointer_changes == 0
    assert result.manifest_complete is True
    assert result.catalog_pointer_complete is True
    assert PUBLISH_NOT_AUTHORIZED in result.error_codes


def test_explicit_dry_run_publish_reports_pointer_change_without_real_write(tmp_path: Path) -> None:
    layout = LakeLayout(tmp_path)
    pointer = _pointer(layout)
    manifest = _manifest(layout)
    before = sorted(path.relative_to(tmp_path) for path in tmp_path.rglob("*"))

    result = publish_current_pointer(
        store=None,
        candidate=pointer,
        intent=PublishIntent(
            publish=True,
            approval_token="fixture-approval-token",
            approved_by="user",
            reason="fixture dry-run publish",
        ),
        dry_run=True,
        quality={
            "quality_status": QUALITY_STATUS_PASS,
            "readiness_status": READINESS_STATUS_AVAILABLE,
        },
        manifest=manifest,
        lifecycle={
            "coverage_denominator": pointer.coverage_denominator,
            "lifecycle_denominator_ref": manifest.lifecycle_denominator_ref,
        },
    )
    after = sorted(path.relative_to(tmp_path) for path in tmp_path.rglob("*"))

    assert result.publish_allowed is True
    assert result.dry_run is True
    assert result.pointer_changes == 1
    assert result.catalog_writes == 0
    assert result.real_lake_writes == 0
    assert before == after


def test_candidate_path_published_path_and_audit_path_are_separated(tmp_path: Path) -> None:
    layout = LakeLayout(tmp_path)

    candidate = layout.candidate_dataset_root(DATASET_PRICES, SCHEMA_VERSION, "run-cr014-s02")
    published = layout.published_dataset_root(DATASET_PRICES, SCHEMA_VERSION)
    candidate_partition = layout.candidate_partition_path(
        DATASET_PRICES,
        SCHEMA_VERSION,
        "run-cr014-s02",
        trade_date="2026-05-26",
        exchange="SSE",
        board="main",
    )
    audit = layout.candidate_audit_path(DATASET_PRICES, "run-cr014-s02", "parity")

    assert candidate != published
    assert "candidate" in candidate.parts
    assert "published" in published.parts
    assert "run_id=run-cr014-s02" in candidate.parts
    assert "run_id=run-cr014-s02" not in published.parts
    assert candidate_partition == candidate / "trade_date=20260526" / "exchange=SSE" / "board=main"
    assert "audit_id=parity" in audit.parts
    assert not candidate.exists()
    assert not published.exists()
    assert not audit.exists()


def test_duckdb_readonly_path_whitelist_rejects_arbitrary_glob(tmp_path: Path) -> None:
    layout = LakeLayout(tmp_path)
    pointer_path = layout.catalog_current_pointer_path(DATASET_PRICES, SCHEMA_VERSION)
    audit_path = layout.candidate_audit_path(DATASET_PRICES, "run-cr014-s02", "parity")
    arbitrary_glob = tmp_path / "candidate" / "parquet" / "dataset=prices" / "*" / "*.parquet"
    unpublished_candidate = layout.candidate_dataset_root(DATASET_PRICES, SCHEMA_VERSION, "run-cr014-s02")

    assert is_duckdb_read_path_allowed(
        pointer_path,
        catalog_pointer_paths=(pointer_path,),
        candidate_audit_paths=(audit_path,),
    )
    assert validate_duckdb_read_path(
        audit_path,
        catalog_pointer_path=pointer_path,
        candidate_audit_paths=(audit_path,),
    ).allowed

    glob_result = validate_duckdb_read_path(
        arbitrary_glob,
        catalog_pointer_path=pointer_path,
        candidate_audit_paths=(audit_path,),
    )
    assert glob_result.allowed is False
    assert glob_result.error_code == DUCKDB_GLOB_NOT_ALLOWED

    candidate_result = validate_duckdb_read_path(
        unpublished_candidate,
        catalog_pointer_path=pointer_path,
        candidate_audit_paths=(audit_path,),
    )
    assert candidate_result.allowed is False


def test_cr014_s02_forbidden_real_operation_counters_remain_zero() -> None:
    assert CR014_FORBIDDEN_OPERATION_COUNTERS["provider_fetch"] == 0
    assert CR014_FORBIDDEN_OPERATION_COUNTERS["lake_write"] == 0
    assert CR014_FORBIDDEN_OPERATION_COUNTERS["credential_read"] == 0
    assert CR014_FORBIDDEN_OPERATION_COUNTERS["duckdb_dependency_change"] == 0
    assert CR014_FORBIDDEN_OPERATION_COUNTERS["catalog_current_pointer_publish"] == 0
