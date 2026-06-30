from market_data.catalog import CatalogPointer
from market_data.contracts import (
    CR014_FORBIDDEN_OPERATION_COUNTERS,
    CR014_UNIVERSE_SCOPE_ALL_A_SHARE,
    DATASET_PRICES,
    QUALITY_STATUS_PASS,
    READINESS_STATUS_AVAILABLE,
    SCHEMA_VERSION,
)
from market_data.incremental import (
    INCREMENTAL_ACTION_PLAN_NEW,
    INCREMENTAL_ACTION_RETRY,
    INCREMENTAL_ACTION_SKIP,
    plan_incremental_refresh,
)
from market_data.replay import (
    PARAMS_HASH_CONFLICT,
    REPLAY_CANDIDATE_UNPUBLISHED,
    REPLAY_SOURCE_MISSING,
    ReplayRequest,
    assert_no_replay_side_effects,
    detect_resume_conflict,
    run_replay_from_manifest,
)
from market_data.retention import (
    AUDIT_REF_PROTECTED,
    PUBLISHED_TRUTH_PROTECTED,
    RETENTION_ACTION_BLOCKED,
    RETENTION_ACTION_RECOMMEND_DELETE,
    RETENTION_DRY_RUN_RECOMMENDATION,
    RETENTION_EXECUTE_NOT_AUTHORIZED,
    evaluate_candidate_retention,
)


def _pointer() -> CatalogPointer:
    return CatalogPointer(
        dataset=DATASET_PRICES,
        schema_version=SCHEMA_VERSION,
        coverage_start="1990-12-19",
        coverage_end="2026-05-26",
        coverage_denominator=2,
        latest_manifest_run_id="manifest-run-current",
        lineage_checksum="lineage-fixture",
        published_at="2026-05-27T00:00:00+00:00",
        known_limitations=[],
        universe_scope=CR014_UNIVERSE_SCOPE_ALL_A_SHARE,
        as_of_trade_date="2026-05-26",
        published_path="published://prices/current",
        quality_status=QUALITY_STATUS_PASS,
        readiness_status=READINESS_STATUS_AVAILABLE,
    )


def _calendar() -> list[dict[str, object]]:
    return [
        {"trade_date": "2026-05-20", "is_open": True},
        {"trade_date": "2026-05-21", "is_open": True},
        {"trade_date": "2026-05-22", "is_open": False},
        {"trade_date": "2026-05-25", "is_open": True},
        {"trade_date": "2026-05-26", "is_open": True},
    ]


def _manifest() -> dict[str, object]:
    return {
        "run_id": "run-cr014-s06",
        "batch_id": "p0-01",
        "dataset": DATASET_PRICES,
        "manifest_ref": "manifest://run-cr014-s06/p0-01",
        "raw_path": "raw://run-cr014-s06/p0-01.jsonl",
        "candidate_path": "candidate://run-cr014-s06/prices",
        "params_hash": "old-hash",
    }


def test_incremental_plan_outputs_recent_affected_partitions_actions_and_stable_key() -> None:
    policy = {
        "dataset": DATASET_PRICES,
        "schema_version": SCHEMA_VERSION,
        "exchanges": ["SSE", "SZSE"],
    }

    first = plan_incremental_refresh(
        _pointer(),
        _calendar(),
        policy,
        recent_n=3,
        success_batches=[f"{DATASET_PRICES}:2026-05-21"],
        failed_batches=[f"{DATASET_PRICES}:2026-05-25"],
    )
    second = plan_incremental_refresh(
        _pointer(),
        _calendar(),
        policy,
        recent_n=3,
        success_batches=[f"{DATASET_PRICES}:2026-05-21"],
        failed_batches=[f"{DATASET_PRICES}:2026-05-25"],
    )
    actions = {item.trade_date: item.action for item in first.batch_actions}

    assert first.recent_n == 3
    assert first.recent_trade_dates == ("2026-05-21", "2026-05-25", "2026-05-26")
    assert len(first.affected_partitions) == 6
    assert actions == {
        "2026-05-21": INCREMENTAL_ACTION_SKIP,
        "2026-05-25": INCREMENTAL_ACTION_RETRY,
        "2026-05-26": INCREMENTAL_ACTION_PLAN_NEW,
    }
    assert first.idempotency_key == second.idempotency_key
    assert first.provider_fetches == 0
    assert first.lake_writes == 0
    assert first.credential_reads == 0
    assert first.permission_counters["provider_fetches"] == 0
    assert first.permission_counters["lake_writes"] == 0
    assert first.permission_counters["credential_reads"] == 0


def test_replay_derives_candidate_and_evidence_without_provider_raw_or_pointer_side_effects() -> None:
    result = run_replay_from_manifest(
        ReplayRequest(
            run_id="run-cr014-s06",
            batch_id="p0-01",
            dataset=DATASET_PRICES,
            manifest_refs=(_manifest(),),
        )
    )
    side_effects = assert_no_replay_side_effects(result)

    assert result.status == REPLAY_CANDIDATE_UNPUBLISHED
    assert result.candidate is not None
    assert result.candidate.candidate_path == "candidate://run-cr014-s06/prices"
    assert {item["type"] for item in result.evidence} == {
        "manifest_ref",
        "raw_ref",
        "replay_boundary",
    }
    assert side_effects.passed is True
    assert side_effects.counters == {
        "provider_fetches": 0,
        "credential_reads": 0,
        "raw_writes": 0,
        "current_pointer_changes": 0,
    }
    assert result.permission_counters["provider_fetches"] == 0
    assert result.permission_counters["credential_reads"] == 0
    assert result.permission_counters["raw_writes"] == 0
    assert result.permission_counters["current_pointer_changes"] == 0


def test_replay_source_missing_returns_structured_error_and_never_backfills() -> None:
    missing_manifest = run_replay_from_manifest(
        ReplayRequest(
            run_id="missing-run",
            batch_id="missing-batch",
            dataset=DATASET_PRICES,
            manifest_refs=(),
        )
    )
    missing_raw = run_replay_from_manifest(
        ReplayRequest(
            run_id="run-cr014-s06",
            batch_id="p0-01",
            dataset=DATASET_PRICES,
            manifest_refs=({**_manifest(), "raw_path": ""},),
        )
    )

    for result in (missing_manifest, missing_raw):
        assert result.status == REPLAY_SOURCE_MISSING
        assert result.error_codes == (REPLAY_SOURCE_MISSING,)
        assert result.provider_fetches == 0
        assert result.credential_reads == 0
        assert result.raw_writes == 0
        assert result.current_pointer_changes == 0
        assert result.permission_counters["provider_fetches"] == 0
        assert result.permission_counters["credential_reads"] == 0


def test_resume_conflict_returns_structured_conflict_without_silent_overwrite() -> None:
    conflict = detect_resume_conflict(
        "run-cr014-s06",
        [_manifest()],
        {"dataset": DATASET_PRICES, "trade_date": "2026-05-26", "params_hash": "new-hash"},
    )

    assert conflict.has_conflict is True
    assert conflict.conflict is not None
    assert conflict.conflict.conflict_type == PARAMS_HASH_CONFLICT
    assert conflict.conflict.existing_ref == "manifest://run-cr014-s06/p0-01"
    assert conflict.conflict.existing_params_hash == "old-hash"
    assert conflict.conflict.requested_params_hash == "new-hash"
    assert "silent_overwrite" in conflict.conflict.blocked_side_effects
    assert "manual_review_required" in conflict.conflict.resolution_options
    assert conflict.provider_fetches == 0
    assert conflict.raw_writes == 0
    assert conflict.current_pointer_changes == 0


def test_retention_default_dry_run_recommends_without_delete_archive_or_migration() -> None:
    candidates = [
        {
            "candidate_ref": "candidate://published",
            "dataset": DATASET_PRICES,
            "run_id": "run-published",
            "age_days": 120,
        },
        {
            "candidate_ref": "candidate://audit",
            "dataset": DATASET_PRICES,
            "run_id": "run-audit",
            "age_days": 120,
        },
        {
            "candidate_ref": "candidate://old",
            "dataset": DATASET_PRICES,
            "run_id": "run-old",
            "age_days": 120,
        },
    ]

    result = evaluate_candidate_retention(
        candidates,
        publish_status={"candidate://published": "published"},
        audit_refs={"candidate://audit": ["quality-audit"]},
    )
    by_ref = {item.target_ref: item for item in result}

    assert by_ref["candidate://published"].reason_code == PUBLISHED_TRUTH_PROTECTED
    assert by_ref["candidate://published"].protected_by_publish is True
    assert by_ref["candidate://audit"].reason_code == AUDIT_REF_PROTECTED
    assert by_ref["candidate://audit"].protected_by_audit is True
    assert by_ref["candidate://old"].action == RETENTION_ACTION_RECOMMEND_DELETE
    assert by_ref["candidate://old"].reason_code == RETENTION_DRY_RUN_RECOMMENDATION
    assert by_ref["candidate://old"].requires_execute_authorization is True
    for item in result:
        assert item.dry_run is True
        assert item.delete_count == 0
        assert item.archive_count == 0
        assert item.migrate_count == 0
        assert item.lake_writes == 0
        assert item.current_pointer_changes == 0


def test_retention_execute_without_authorization_blocks_operation() -> None:
    result = evaluate_candidate_retention(
        [
            {
                "candidate_ref": "candidate://old",
                "dataset": DATASET_PRICES,
                "run_id": "run-old",
                "age_days": 120,
            }
        ],
        dry_run=False,
    )[0]

    assert result.action == RETENTION_ACTION_BLOCKED
    assert result.reason_code == RETENTION_EXECUTE_NOT_AUTHORIZED
    assert result.recommended_action == "delete"
    assert result.requires_execute_authorization is True
    assert result.delete_count == 0
    assert result.archive_count == 0
    assert result.migrate_count == 0


def test_cr014_s06_forbidden_real_operation_counters_remain_zero() -> None:
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
