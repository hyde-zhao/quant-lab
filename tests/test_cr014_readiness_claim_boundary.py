from pathlib import Path

from market_data.catalog import CatalogPointer
from market_data.claims import (
    CLAIM_ALLOWED_WHILE_BLOCKED,
    CLAIM_FULL_A_SINCE_INCEPTION_PRODUCTION,
    CLAIM_PERMISSION_COUNTER_VIOLATION,
    CLAIM_REQUIRED_FIELD_MISSING,
    assert_no_readiness_side_effects,
    build_claim_boundary,
    validate_claim_boundary,
)
from market_data.contracts import (
    CR014_CLAIM_FULL_A_SINCE_INCEPTION,
    CR014_FORBIDDEN_OPERATION_COUNTERS,
    CR014_UNIVERSE_SCOPE_ALL_A_SHARE,
    DATASET_PRICES,
    QUALITY_STATUS_PASS,
    READINESS_STATUS_AVAILABLE,
    SCHEMA_VERSION,
)
from market_data.manifest import ManifestRecord
from market_data.readiness import (
    CR014_S05_P0_DATASETS,
    GAP_CANDIDATE_UNPUBLISHED,
    GAP_LIFECYCLE_REQUIRED_MISSING,
    GAP_P0_DATASET_MISSING,
    GAP_PERMISSION_COUNTER_VIOLATION,
    PUBLISH_STATUS_PUBLISHED,
    READINESS_SOURCE_S01_LIFECYCLE,
    build_gap_register,
    build_readiness_matrix,
    merge_audit_evidence,
)


def _lifecycle() -> dict[str, object]:
    return {
        "as_of_trade_date": "2026-05-26",
        "lifecycle_denominator_ref": "s01://lifecycle-denominator/current-truth",
        "coverage_denominator": 2,
    }


def _pointer(dataset: str = DATASET_PRICES) -> CatalogPointer:
    return CatalogPointer(
        dataset=dataset,
        schema_version=SCHEMA_VERSION,
        coverage_start="1990-12-19",
        coverage_end="2026-05-26",
        coverage_denominator=2,
        latest_manifest_run_id=f"manifest-{dataset}",
        lineage_checksum=f"lineage-{dataset}",
        published_at="2026-05-27T00:00:00+00:00",
        known_limitations=[],
        universe_scope=CR014_UNIVERSE_SCOPE_ALL_A_SHARE,
        as_of_trade_date="2026-05-26",
        published_path=f"published://{dataset}/current",
        quality_status=QUALITY_STATUS_PASS,
        readiness_status=READINESS_STATUS_AVAILABLE,
    )


def _manifest(dataset: str = DATASET_PRICES) -> ManifestRecord:
    return ManifestRecord(
        run_id=f"manifest-{dataset}",
        dataset=dataset,
        source="fixture",
        source_interface=f"fixture.{dataset}",
        schema_hash=f"schema-{dataset}",
        row_count=2,
        quality_status=QUALITY_STATUS_PASS,
        readiness_status=READINESS_STATUS_AVAILABLE,
        lineage_checksum=f"lineage-{dataset}",
        lifecycle_denominator_ref="s01://lifecycle-denominator/current-truth",
        candidate_path=f"candidate://{dataset}/manifest",
    )


def _audit(dataset: str = DATASET_PRICES) -> dict[str, object]:
    return {
        "dataset": dataset,
        "run_id": f"audit-{dataset}",
        "evidence_path": f"audit://cr014-s04/{dataset}/parity",
        "parity_status": "pass",
        "candidate_unpublished": False,
        "publish_count": 0,
        "current_pointer_changes": 0,
    }


def _published_inputs() -> tuple[dict[str, CatalogPointer], dict[str, ManifestRecord], dict[str, dict[str, object]]]:
    pointers = {dataset: _pointer(dataset) for dataset in CR014_S05_P0_DATASETS}
    manifests = {dataset: _manifest(dataset) for dataset in CR014_S05_P0_DATASETS}
    audits = {dataset: _audit(dataset) for dataset in CR014_S05_P0_DATASETS}
    return pointers, manifests, audits


def test_readiness_uses_s01_lifecycle_denominator_and_blocks_missing_p0_dataset() -> None:
    matrix = build_readiness_matrix(
        lifecycle_denominator=_lifecycle(),
        datasets=(DATASET_PRICES,),
    )
    register = build_gap_register(matrix)
    summary = build_claim_boundary(register, publish_status={DATASET_PRICES: "missing_required"})

    assert matrix.denominator_ref == "s01://lifecycle-denominator/current-truth"
    assert matrix.denominator_source == READINESS_SOURCE_S01_LIFECYCLE
    assert matrix.rows[0].denominator_ref == matrix.denominator_ref
    assert GAP_P0_DATASET_MISSING in {row.gap_code for row in register.rows}
    assert summary.full_a_allowed_claim_count == 0
    assert summary.allowed_claims == ()
    for blocked in summary.blocked_claims:
        assert blocked["gap_code"]
        assert blocked["evidence_path"]
        assert blocked["remediation"]
        assert blocked["release_condition"]


def test_lifecycle_denominator_missing_blocks_full_history_claim() -> None:
    matrix = build_readiness_matrix(
        lifecycle_denominator={},
        catalog_pointers={DATASET_PRICES: _pointer()},
        manifest_refs={DATASET_PRICES: _manifest()},
        audit_evidence_refs={DATASET_PRICES: _audit()},
        datasets=(DATASET_PRICES,),
    )
    register = build_gap_register(matrix)
    summary = build_claim_boundary(register, publish_status={DATASET_PRICES: PUBLISH_STATUS_PUBLISHED})

    assert matrix.denominator_ref == ""
    assert GAP_LIFECYCLE_REQUIRED_MISSING in matrix.rows[0].gap_codes
    assert summary.full_a_allowed_claim_count == 0
    assert CR014_CLAIM_FULL_A_SINCE_INCEPTION not in {
        item["claim"] for item in summary.allowed_claims
    }


def test_candidate_audit_pass_but_unpublished_is_blocked_not_current_truth() -> None:
    candidate = {
        "dataset": DATASET_PRICES,
        "status": "candidate_unpublished",
        "candidate_path": "candidate://cr014-s05/prices",
        "quality_status": QUALITY_STATUS_PASS,
        "readiness_status": READINESS_STATUS_AVAILABLE,
    }
    audit = {
        "dataset": DATASET_PRICES,
        "evidence_path": "audit://cr014-s04/prices/parity-pass",
        "parity_status": "pass",
        "candidate_unpublished": True,
        "publish_count": 0,
        "current_pointer_changes": 0,
    }

    matrix = build_readiness_matrix(
        lifecycle_denominator=_lifecycle(),
        manifest_refs={DATASET_PRICES: _manifest()},
        quality_candidates={DATASET_PRICES: candidate},
        audit_evidence_refs={DATASET_PRICES: audit},
        datasets=(DATASET_PRICES,),
    )
    register = build_gap_register(matrix)
    summary = build_claim_boundary(register, publish_status={DATASET_PRICES: "candidate_unpublished"})
    validation = validate_claim_boundary(summary)

    assert GAP_CANDIDATE_UNPUBLISHED in matrix.rows[0].gap_codes
    assert GAP_CANDIDATE_UNPUBLISHED in {item["gap_code"] for item in summary.blocked_claims}
    assert summary.full_a_allowed_claim_count == 0
    assert summary.allowed_claims == ()
    assert validation.passed is True


def test_all_p0_gates_published_allow_single_full_a_production_claim() -> None:
    pointers, manifests, audits = _published_inputs()
    matrix = build_readiness_matrix(
        lifecycle_denominator=_lifecycle(),
        catalog_pointers=pointers,
        manifest_refs=manifests,
        audit_evidence_refs=audits,
    )
    register = build_gap_register(matrix)
    summary = build_claim_boundary(
        register,
        publish_status={dataset: PUBLISH_STATUS_PUBLISHED for dataset in CR014_S05_P0_DATASETS},
    )
    validation = validate_claim_boundary(summary)

    assert matrix.p0_gate_passed is True
    assert register.rows == ()
    assert summary.full_a_allowed_claim_count == 1
    assert summary.allowed_claims[0]["claim"] == CR014_CLAIM_FULL_A_SINCE_INCEPTION
    assert summary.allowed_claims[0]["claim_scope"] == CLAIM_FULL_A_SINCE_INCEPTION_PRODUCTION
    assert validation.passed is True


def test_old_evidence_refs_are_reference_only_strings_and_counters_remain_zero() -> None:
    legacy_refs = ("legacy-report://cr013/readiness-summary", "legacy-evidence://cr010/catalog")
    matrix = build_readiness_matrix(
        lifecycle_denominator=_lifecycle(),
        catalog_pointers={DATASET_PRICES: _pointer()},
        manifest_refs={DATASET_PRICES: _manifest()},
        audit_evidence_refs={
            DATASET_PRICES: {
                "dataset": DATASET_PRICES,
                "evidence_path": legacy_refs[0],
                "parity_status": "pass",
            }
        },
        legacy_baseline_refs=legacy_refs,
        datasets=(DATASET_PRICES,),
    )
    register = build_gap_register(matrix)
    summary = build_claim_boundary(register, publish_status={DATASET_PRICES: PUBLISH_STATUS_PUBLISHED})
    side_effects = assert_no_readiness_side_effects(summary)

    assert matrix.legacy_baseline_refs == legacy_refs
    assert summary.legacy_baseline_refs == legacy_refs
    assert matrix.rows[0].audit_evidence_path == legacy_refs[0]
    assert side_effects.passed is True
    assert side_effects.counters["provider_fetch"] == 0
    assert side_effects.counters["lake_write"] == 0
    assert side_effects.counters["credential_read"] == 0
    assert side_effects.counters["old_report_overwrite"] == 0


def test_permission_counter_violation_blocks_claim_boundary() -> None:
    pointers, manifests, audits = _published_inputs()
    matrix = build_readiness_matrix(
        lifecycle_denominator=_lifecycle(),
        catalog_pointers=pointers,
        manifest_refs=manifests,
        audit_evidence_refs=audits,
        permission_counters={"lake_write": 1},
    )
    register = build_gap_register(matrix)
    summary = build_claim_boundary(
        register,
        publish_status={dataset: PUBLISH_STATUS_PUBLISHED for dataset in CR014_S05_P0_DATASETS},
    )
    validation = validate_claim_boundary(summary)
    side_effects = assert_no_readiness_side_effects(summary)

    assert GAP_PERMISSION_COUNTER_VIOLATION in {row.gap_code for row in register.rows}
    assert summary.full_a_allowed_claim_count == 0
    assert CLAIM_PERMISSION_COUNTER_VIOLATION in validation.error_codes
    assert side_effects.passed is False
    assert side_effects.counters["lake_write"] == 1


def test_claim_boundary_validator_rejects_unstructured_blocked_claims() -> None:
    result = validate_claim_boundary(
        {
            "allowed_claims": [{"claim": CR014_CLAIM_FULL_A_SINCE_INCEPTION}],
            "blocked_claims": [{"gap_code": GAP_CANDIDATE_UNPUBLISHED}],
            "required_missing": [{"gap_code": GAP_CANDIDATE_UNPUBLISHED}],
            "permission_counters": {},
            "full_a_allowed_claim_count": 1,
        }
    )

    assert result.passed is False
    assert CLAIM_REQUIRED_FIELD_MISSING in result.error_codes
    assert CLAIM_ALLOWED_WHILE_BLOCKED in result.error_codes


def test_claim_boundary_blocks_when_publish_status_is_missing() -> None:
    summary = build_claim_boundary({"rows": (), "permission_counters": {}})
    validation = validate_claim_boundary(summary)

    assert summary.full_a_allowed_claim_count == 0
    assert summary.allowed_claims == ()
    assert summary.blocked_claims[0]["gap_code"] == "catalog_pointer_missing"
    assert validation.passed is True


def test_merge_audit_evidence_keeps_candidate_evidence_from_becoming_truth() -> None:
    merged = merge_audit_evidence(
        {},
        {
            DATASET_PRICES: {
                "evidence_path": "audit://candidate/prices",
                "parity_status": "pass",
                "candidate_unpublished": True,
                "publish_count": 0,
                "current_pointer_changes": 0,
            }
        },
    )

    assert merged == (
        {
            "dataset": DATASET_PRICES,
            "evidence_path": "audit://candidate/prices",
            "parity_status": "pass",
            "candidate_unpublished": True,
            "claim_effect": "evidence_only",
            "publish_count": 0,
            "current_pointer_changes": 0,
        },
    )


def test_cr014_s05_forbidden_real_operation_counters_remain_zero() -> None:
    assert CR014_FORBIDDEN_OPERATION_COUNTERS == {
        "provider_fetch": 0,
        "lake_write": 0,
        "credential_read": 0,
        "legacy_data_operation": 0,
        "old_report_overwrite": 0,
        "duckdb_dependency_change": 0,
        "duckdb_write": 0,
        "catalog_current_pointer_publish": 0,
        "s09_real_execution": 0,
    }


def test_s05_modules_do_not_import_or_call_forbidden_boundaries() -> None:
    forbidden_fragments = tuple(
        "".join(parts)
        for parts in (
            ("market_data.", "runtime"),
            ("market_data.", "connectors"),
            ("market_data.", "storage"),
            ("import ", "duckdb"),
            ("from ", "duckdb"),
            ("os", ".environ"),
            ("dot", "env"),
            ("publish_current_", "pointer"),
            (".write_", "text("),
            (".", "op", "en("),
        )
    )

    module_paths = (
        Path("".join(("market_", "data", "/readiness.py"))),
        Path("".join(("market_", "data", "/claims.py"))),
    )
    for path in module_paths:
        text = path.read_bytes().decode("utf-8")
        for fragment in forbidden_fragments:
            assert fragment not in text
