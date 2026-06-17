from argparse import Namespace

from market_data.catalog import CatalogPointer
from market_data.cli import cmd_p0_run
from market_data.contracts import (
    CR014_FORBIDDEN_OPERATION_COUNTERS,
    CR014_UNIVERSE_SCOPE_ALL_A_SHARE,
    DATASET_PRICES,
    QUALITY_STATUS_PASS,
    READINESS_STATUS_AVAILABLE,
    SCHEMA_VERSION,
)
from market_data.manifest import ManifestRecord
from market_data.normalization import (
    CANDIDATE_UNPUBLISHED,
    REPLAY_SOURCE_MISSING,
    normalize_p0_candidate,
    replay_p0_candidate,
)
from market_data.publish import PUBLISH_NOT_AUTHORIZED, PublishIntent
from market_data.runtime import (
    AUTHORIZATION_REQUIRED,
    CR014_P0_DATASETS,
    DEV_GATE_UNSATISFIED,
    RUN_NOT_ALLOWED,
    SOURCE_INTERFACE_UNRESOLVED,
    DevGate,
    P0DatasetPlanRequest,
    RunAuthorization,
    build_p0_plan,
    run_p0_batches,
)
from market_data.validation import (
    P0_CURRENT_POINTER_REQUIRED,
    VALIDATE_DOES_NOT_PUBLISH,
    publish_p0_candidate,
    read_p0_current_truth,
    validate_p0_candidate,
)


class CountingConnector:
    def __init__(self) -> None:
        self.call_count = 0

    def fetch(self, request):  # pragma: no cover - forbidden path
        self.call_count += 1
        raise AssertionError(f"connector must not be called: {request!r}")


def _lifecycle_contract() -> dict[str, str]:
    return {
        "as_of_trade_date": "2026-05-26",
        "coverage_denominator_ref": "cr014-s01-denominator-fixture",
        "lifecycle_denominator_ref": "cr014-s01-denominator-fixture",
    }


def _plan():
    return build_p0_plan(
        P0DatasetPlanRequest(
            start_date="1990-12-19",
            end_date="2026-05-26",
            as_of_trade_date="2026-05-26",
            coverage_denominator_ref="cr014-s01-denominator-fixture",
        ),
        lifecycle_contract=_lifecycle_contract(),
    )


def _manifest() -> ManifestRecord:
    return ManifestRecord(
        run_id="run-cr014-s03",
        dataset=DATASET_PRICES,
        source="fixture",
        source_interface="fixture.prices.daily",
        schema_hash="schema-fixture",
        row_count=2,
        quality_status=QUALITY_STATUS_PASS,
        readiness_status=READINESS_STATUS_AVAILABLE,
        lineage_checksum="lineage-fixture",
        lifecycle_denominator_ref="cr014-s01-denominator-fixture",
        candidate_path="candidate://cr014-s03/prices/run-cr014-s03",
        metadata={"batch_id": "p0-01"},
    )


def _pointer() -> CatalogPointer:
    return CatalogPointer(
        dataset=DATASET_PRICES,
        schema_version=SCHEMA_VERSION,
        coverage_start="1990-12-19",
        coverage_end="2026-05-26",
        coverage_denominator=2,
        latest_manifest_run_id="run-cr014-s03",
        lineage_checksum="lineage-fixture",
        published_at="2026-05-27T00:00:00+00:00",
        known_limitations=[],
        universe_scope=CR014_UNIVERSE_SCOPE_ALL_A_SHARE,
        as_of_trade_date="2026-05-26",
        published_path="published://cr014-s03/prices",
        quality_status=QUALITY_STATUS_PASS,
        readiness_status=READINESS_STATUS_AVAILABLE,
    )


def test_plan_before_cp5_is_dry_run_and_real_counts_are_zero() -> None:
    plan = _plan()

    assert plan.status == "dry_run"
    assert plan.datasets == CR014_P0_DATASETS
    assert len(plan.batch_list) == 7
    assert plan.authorization_needed is True
    assert plan.permission_counters["provider_fetches"] == 0
    assert plan.permission_counters["lake_writes"] == 0
    assert plan.permission_counters["credential_reads"] == 0
    assert plan.permission_counters["current_pointer_changes"] == 0
    assert plan.permission_counters["duckdb_dependency_change"] == 0


def test_run_gate_fail_closed_before_cp5_and_user_authorization_calls_no_connector() -> None:
    plan = _plan()
    connector = CountingConnector()

    result = run_p0_batches(plan, connector=connector)
    error_codes = {error.code for error in result.errors}

    assert result.run_allowed is False
    assert result.connector_call_count == 0
    assert connector.call_count == 0
    assert {DEV_GATE_UNSATISFIED, AUTHORIZATION_REQUIRED, RUN_NOT_ALLOWED} <= error_codes
    assert result.permission_counters["provider_fetches"] == 0
    assert result.permission_counters["lake_writes"] == 0
    assert result.permission_counters["credential_reads"] == 0


def test_run_gate_requires_exact_source_and_interface_allowlist() -> None:
    plan = _plan()
    connector = CountingConnector()

    result = run_p0_batches(
        plan,
        connector=connector,
        authorization=RunAuthorization(authorization_id="auth-cr014-s03-fixture"),
        dev_gate=DevGate(
            cp5_approved=True,
            lld_confirmed=True,
            dependencies_satisfied=True,
            file_conflict_free=True,
        ),
    )
    error_codes = {error.code for error in result.errors}

    assert result.run_allowed is False
    assert SOURCE_INTERFACE_UNRESOLVED in error_codes
    assert result.connector_call_count == 0
    assert connector.call_count == 0


def test_normalize_and_replay_only_emit_unpublished_candidate_without_pointer_change() -> None:
    manifest = _manifest().to_dict()
    manifest["batch_id"] = "p0-01"

    candidate = normalize_p0_candidate(manifest, raw_ref="raw://fixture")
    replay = replay_p0_candidate(
        "run-cr014-s03",
        "p0-01",
        [manifest],
        dataset=DATASET_PRICES,
    )

    assert candidate.status == CANDIDATE_UNPUBLISHED
    assert candidate.current_pointer_changes == 0
    assert candidate.provider_fetches == 0
    assert candidate.credential_reads == 0
    assert candidate.raw_writes == 0
    assert replay.status == CANDIDATE_UNPUBLISHED
    assert replay.current_pointer_changes == 0
    assert replay.provider_fetches == 0
    assert replay.credential_reads == 0
    assert replay.raw_writes == 0


def test_replay_source_missing_is_terminal_and_does_not_provider_backfill() -> None:
    replay = replay_p0_candidate("missing-run", "missing-batch", None, dataset=DATASET_PRICES)

    assert replay.status == "blocked"
    assert replay.error_codes == (REPLAY_SOURCE_MISSING,)
    assert replay.provider_fetches == 0
    assert replay.credential_reads == 0
    assert replay.raw_writes == 0
    assert replay.current_pointer_changes == 0


def test_validate_pass_does_not_publish_or_change_current_pointer() -> None:
    candidate = normalize_p0_candidate(_manifest(), raw_ref="raw://fixture")

    validation = validate_p0_candidate(candidate, lifecycle=_lifecycle_contract())

    assert validation.passed is True
    assert validation.quality_status == QUALITY_STATUS_PASS
    assert validation.candidate_unpublished is True
    assert validation.publish_count == 0
    assert validation.current_pointer_changes == 0
    assert validation.details[0]["code"] == VALIDATE_DOES_NOT_PUBLISH


def test_publish_without_explicit_intent_delegates_to_s02_gate_and_changes_no_pointer() -> None:
    pointer = _pointer()
    manifest = _manifest()
    validation = validate_p0_candidate(pointer, lifecycle=_lifecycle_contract())

    result = publish_p0_candidate(
        pointer,
        validation,
        PublishIntent(publish=False),
        manifest=manifest,
        lifecycle={
            "coverage_denominator": pointer.coverage_denominator,
            "lifecycle_denominator_ref": manifest.lifecycle_denominator_ref,
        },
    )

    assert result.publish_allowed is False
    assert result.pointer_changes == 0
    assert PUBLISH_NOT_AUTHORIZED in result.error_codes


def test_read_query_only_accepts_published_pointer_or_controlled_candidate_audit() -> None:
    blocked = read_p0_current_truth(DATASET_PRICES)
    published = read_p0_current_truth(DATASET_PRICES, _pointer())
    audit = read_p0_current_truth(
        DATASET_PRICES,
        read_scope="candidate_audit",
        candidate_audit_evidence={"candidate_audit_path": "audit://cr014-s03/parity"},
    )

    assert blocked.allowed is False
    assert blocked.error_codes == (P0_CURRENT_POINTER_REQUIRED,)
    assert published.allowed is True
    assert published.current_truth_visible is True
    assert audit.allowed is True
    assert audit.current_truth_visible is False
    assert audit.unpublished_lake_scans == 0


def test_cli_p0_run_returns_structured_unblock_conditions_without_real_operations() -> None:
    result = cmd_p0_run(
        Namespace(
            datasets=None,
            dataset=DATASET_PRICES,
            start_date="1990-12-19",
            end_date="2026-05-26",
            as_of_trade_date="2026-05-26",
            coverage_denominator_ref="cr014-s01-denominator-fixture",
            authorization_id=None,
            approved_by=None,
            allowed_sources=None,
            allowed_interfaces=None,
            cp5_approved=False,
            lld_confirmed=False,
            dependencies_satisfied=False,
            file_conflict_free=False,
        )
    )

    assert result["ok"] is False
    assert result["command"] == "p0-run"
    assert result["connector_call_count"] == 0
    assert {item["code"] for item in result["errors"]} >= {
        DEV_GATE_UNSATISFIED,
        AUTHORIZATION_REQUIRED,
        RUN_NOT_ALLOWED,
    }
    assert result["permission_counters"]["provider_fetches"] == 0


def test_cr014_s03_forbidden_real_operation_counters_remain_zero() -> None:
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
