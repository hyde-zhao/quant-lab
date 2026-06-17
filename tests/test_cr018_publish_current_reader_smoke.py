from __future__ import annotations

from market_data.catalog import CR018_CURRENT_POINTER_PLAN_PLANNED
from market_data.dataset_groups import PRIORITY_P0, list_dataset_groups
from market_data.publish import (
    AUTO_PUBLISH_FORBIDDEN,
    AUTO_PUBLISH_PRODUCERS,
    PUBLISH_BLOCKED_INCOMPLETE_EVIDENCE,
    PUBLISH_BLOCKED_MISSING_APPROVAL,
    PUBLISH_BLOCKED_P0_READINESS_FAILED,
    PUBLISH_BLOCKED_ROLLBACK_TARGET_MISSING,
    ReleasePublishRequest,
    explicit_publish_gate,
    forbid_auto_publish_guard,
)
from market_data.readers import (
    CURRENT_READER_CANDIDATE_READ_FORBIDDEN,
    CURRENT_READER_CATALOG_NOT_PUBLISHED,
    CURRENT_READER_STATUS_PASS,
    current_reader_smoke,
)
from market_data.validation import build_release_readiness_audit_report


RELEASE_ID = "cr018-prod-20260528"
PREVIOUS_RELEASE_ID = "cr018-prod-previous"
P0_DATASET_IDS = tuple(entry.dataset_id for entry in list_dataset_groups(PRIORITY_P0))
REAL_OPERATION_COUNTER_KEYS = (
    "current_pointer_publish",
    "real_lake_write",
    "credential_read",
    "provider_fetch",
    "qmt_operation",
    "duckdb_dependency_change",
)


def _p0_rows(passed: bool = True) -> list[dict[str, object]]:
    return [
        {
            "dataset_id": dataset_id,
            "priority": PRIORITY_P0,
            "readiness_status": "available" if passed else "required_missing",
            "passed": passed,
            "required_missing_count": 0 if passed else 1,
            "quality_status": "pass",
        }
        for dataset_id in P0_DATASET_IDS
    ]


def _evidence_refs(complete: bool = True) -> dict[str, str]:
    refs = {
        "raw": f"fixture://raw/{RELEASE_ID}",
        "manifest": f"fixture://manifest/{RELEASE_ID}",
        "candidate": f"fixture://candidate/{RELEASE_ID}",
        "quality": f"fixture://quality/{RELEASE_ID}",
        "release_history": f"fixture://release-history/{RELEASE_ID}",
    }
    if complete:
        return refs
    return {"raw": refs["raw"]}


def _rollback_target() -> dict[str, str]:
    return {"scope": "release", "target_release_id": PREVIOUS_RELEASE_ID}


def _readiness_report(
    *,
    p0_passed: bool = True,
    evidence_complete: bool = True,
    rollback_present: bool = True,
):
    return build_release_readiness_audit_report(
        RELEASE_ID,
        _p0_rows(passed=p0_passed),
        quality={"quality_status": "pass"},
        rollback_target=_rollback_target() if rollback_present else None,
        evidence_refs=_evidence_refs(complete=evidence_complete),
    )


def _dataset_details() -> tuple[dict[str, object], ...]:
    return tuple(
        {
            "dataset_id": dataset_id,
            "release_id": RELEASE_ID,
            "row_count": index + 10,
            "lineage_checksum": f"sha256:{index:02d}",
        }
        for index, dataset_id in enumerate(P0_DATASET_IDS)
    )


def _published_current_pointers() -> dict[str, dict[str, object]]:
    return {
        dataset_id: {
            "dataset_id": dataset_id,
            "release_id": RELEASE_ID,
            "published": True,
            "status": "published",
            "published_path": f"fixture://published/{RELEASE_ID}/{dataset_id}",
            "row_count": index + 10,
        }
        for index, dataset_id in enumerate(P0_DATASET_IDS)
    }


def _reason_codes(decision) -> set[str]:
    return {str(item["reason_code"]) for item in decision.blocked_reasons}


def _assert_real_operation_counts_zero(operation_counts: dict[str, int]) -> None:
    assert {key: operation_counts.get(key, 0) for key in REAL_OPERATION_COUNTER_KEYS} == {
        key: 0 for key in REAL_OPERATION_COUNTER_KEYS
    }


def test_missing_approval_id_blocks_publish_and_pointer_plan() -> None:
    decision = explicit_publish_gate(
        ReleasePublishRequest(
            release_id=RELEASE_ID,
            readiness_report=_readiness_report(),
            approval_id=None,
            rollback_target=_rollback_target(),
            dataset_details=_dataset_details(),
        )
    )

    assert decision.allowed is False
    assert decision.production_publish_allowed_count == 0
    assert decision.current_pointer_update_plan == {}
    assert PUBLISH_BLOCKED_MISSING_APPROVAL in _reason_codes(decision)
    _assert_real_operation_counts_zero(decision.operation_counts or {})


def test_readiness_evidence_or_rollback_failures_block_pointer_plan() -> None:
    cases = [
        (_readiness_report(p0_passed=False), PUBLISH_BLOCKED_P0_READINESS_FAILED),
        (_readiness_report(evidence_complete=False), PUBLISH_BLOCKED_INCOMPLETE_EVIDENCE),
        (_readiness_report(rollback_present=False), PUBLISH_BLOCKED_ROLLBACK_TARGET_MISSING),
    ]
    for report, expected_reason in cases:
        decision = explicit_publish_gate(
            ReleasePublishRequest(
                release_id=RELEASE_ID,
                readiness_report=report,
                approval_id="approval-cr018-s07-fixture",
                dataset_details=_dataset_details(),
            )
        )

        assert decision.allowed is False
        assert decision.production_publish_allowed_count == 0
        assert decision.current_pointer_update_plan == {}
        assert expected_reason in _reason_codes(decision)
        _assert_real_operation_counts_zero(decision.operation_counts or {})


def test_complete_explicit_publish_gate_builds_plan_without_real_publish() -> None:
    decision = explicit_publish_gate(
        ReleasePublishRequest(
            release_id=RELEASE_ID,
            readiness_report=_readiness_report(),
            approval_id="approval-cr018-s07-fixture",
            rollback_target=_rollback_target(),
            approved_by="fixture-approver",
            approved_at="2026-05-29T10:30:00+08:00",
            dataset_details=_dataset_details(),
        )
    )

    assert decision.allowed is True
    assert decision.production_publish_allowed_count == 1
    assert decision.auto_publish_count == 0
    assert decision.current_pointer_update_plan["status"] == CR018_CURRENT_POINTER_PLAN_PLANNED
    assert decision.current_pointer_update_plan["current_pointer_update_planned_count"] == len(P0_DATASET_IDS)
    assert decision.current_pointer_update_plan["current_pointer_publish_count"] == 0
    assert decision.current_pointer_update_plan["catalog_current_pointer_publish_count"] == 0
    assert decision.publish_evidence["release_id"] == RELEASE_ID
    assert decision.publish_evidence["approval"]["approval_id"] == "approval-cr018-s07-fixture"
    assert decision.publish_evidence["checksum"].startswith("sha256:")
    _assert_real_operation_counts_zero(decision.operation_counts or {})


def test_validate_parity_quality_and_duckdb_pass_do_not_auto_publish() -> None:
    for producer in AUTO_PUBLISH_PRODUCERS:
        result = forbid_auto_publish_guard(producer, producer_status="pass")

        assert result.auto_publish_allowed is False
        assert result.auto_publish_count == 0
        assert result.reason_code == AUTO_PUBLISH_FORBIDDEN
        _assert_real_operation_counts_zero(result.operation_counts or {})


def test_current_reader_smoke_covers_p0_group_from_published_current_pointer() -> None:
    smoke = current_reader_smoke(
        RELEASE_ID,
        p0_dataset_ids=P0_DATASET_IDS,
        current_pointers=_published_current_pointers(),
    )

    assert smoke.status == CURRENT_READER_STATUS_PASS
    assert set(smoke.covered_datasets) == set(P0_DATASET_IDS)
    assert smoke.policy_metadata["published_current_pointer_only"] is True
    assert smoke.policy_metadata["candidate_fallback_allowed"] is False
    assert smoke.policy_metadata["p0_dataset_group_covered"] is True
    assert set(smoke.row_counts) == set(P0_DATASET_IDS)
    _assert_real_operation_counts_zero(smoke.operation_counts)


def test_missing_current_pointer_returns_not_published_and_blocks_candidate_fallback() -> None:
    missing_dataset = P0_DATASET_IDS[0]
    current = _published_current_pointers()
    current.pop(missing_dataset)
    candidate = {
        missing_dataset: {
            "dataset_id": missing_dataset,
            "release_id": RELEASE_ID,
            "status": "candidate_unpublished",
            "candidate_path": f"fixture://candidate/{RELEASE_ID}/{missing_dataset}",
        }
    }

    smoke = current_reader_smoke(
        RELEASE_ID,
        p0_dataset_ids=P0_DATASET_IDS,
        current_pointers=current,
        candidate_pointers=candidate,
    )
    issue_codes = {item["code"] for item in smoke.issues}

    assert smoke.status == CURRENT_READER_CATALOG_NOT_PUBLISHED
    assert CURRENT_READER_CATALOG_NOT_PUBLISHED in issue_codes
    assert CURRENT_READER_CANDIDATE_READ_FORBIDDEN in issue_codes
    assert smoke.candidate_fallback_blocked is True
    assert smoke.candidate_fallback_blocked_count == 1
    assert smoke.candidate_read_count == 0
    assert smoke.unpublished_lake_scan_count == 0
    _assert_real_operation_counts_zero(smoke.operation_counts)


def test_current_reader_blocks_candidate_substitute_for_current_pointer() -> None:
    candidate_dataset = P0_DATASET_IDS[0]
    current = _published_current_pointers()
    current[candidate_dataset] = {
        **current[candidate_dataset],
        "published_path": f"fixture://candidate/{RELEASE_ID}/{candidate_dataset}",
    }

    smoke = current_reader_smoke(
        RELEASE_ID,
        p0_dataset_ids=P0_DATASET_IDS,
        current_pointers=current,
    )

    assert smoke.status == CURRENT_READER_CANDIDATE_READ_FORBIDDEN
    assert CURRENT_READER_CANDIDATE_READ_FORBIDDEN in {item["code"] for item in smoke.issues}
    assert smoke.candidate_read_count == 0
    _assert_real_operation_counts_zero(smoke.operation_counts)
