from pathlib import Path

from market_data.audit import (
    PARITY_MISMATCH,
    PARITY_MISMATCH_ERROR,
    assert_no_source_of_truth_side_effects,
    compare_duckdb_with_pandas_pyarrow,
    run_fallback_audit,
    run_readonly_audit,
)
from market_data.catalog import CatalogPointer
from market_data.contracts import (
    CR014_FORBIDDEN_OPERATION_COUNTERS,
    CR014_UNIVERSE_SCOPE_ALL_A_SHARE,
    DATASET_PRICES,
    QUALITY_STATUS_PASS,
    READINESS_STATUS_AVAILABLE,
    SCHEMA_VERSION,
)
from market_data.duckdb_query import (
    CANDIDATE_PATH_REJECTED,
    CLAIM_EFFECT_EVIDENCE_ONLY,
    DUCKDB_DEPENDENCY_UNAVAILABLE,
    ENGINE_FALLBACK,
    FORBIDDEN_SQL,
    READONLY_OPEN_FAILED,
    READ_MODE_CANDIDATE_AUDIT,
    READ_MODE_PUBLISHED_CURRENT_TRUTH,
    DuckDBBoundaryError,
    DuckDBReadOnlyOpenError,
    ReadOnlyQueryPolicy,
    build_readonly_query_request,
    run_candidate_audit_query,
    run_published_current_truth_query,
)
from market_data.lake_layout import LakeLayout


class ReadOnlyOpenFailingAdapter:
    def execute_readonly(self, request):  # pragma: no cover - forbidden path
        raise DuckDBReadOnlyOpenError(f"read-only open failed for {request.source_path}")


def _pointer(layout: LakeLayout) -> CatalogPointer:
    return CatalogPointer(
        dataset=DATASET_PRICES,
        schema_version=SCHEMA_VERSION,
        coverage_start="1990-12-19",
        coverage_end="2026-05-26",
        coverage_denominator=2,
        latest_manifest_run_id="run-cr014-s04",
        lineage_checksum="lineage-fixture",
        published_at="2026-05-27T00:00:00+00:00",
        known_limitations=[],
        universe_scope=CR014_UNIVERSE_SCOPE_ALL_A_SHARE,
        as_of_trade_date="2026-05-26",
        published_path=str(layout.published_dataset_root(DATASET_PRICES, SCHEMA_VERSION)),
        quality_status=QUALITY_STATUS_PASS,
        readiness_status=READINESS_STATUS_AVAILABLE,
    )


def _published_request(layout: LakeLayout):
    pointer = _pointer(layout)
    request = build_readonly_query_request(
        mode=READ_MODE_PUBLISHED_CURRENT_TRUTH,
        dataset=DATASET_PRICES,
        sql_template_id="projection_scan",
        catalog_pointer=pointer,
        projections=("trade_date", "ts_code", "close"),
        partition_filters={"trade_date": "20260526"},
        policy=ReadOnlyQueryPolicy(allowed_published_paths=(pointer.published_path,)),
    )
    assert not isinstance(request, DuckDBBoundaryError)
    return request


def _candidate_request(layout: LakeLayout):
    candidate_path = layout.candidate_audit_path(DATASET_PRICES, "run-cr014-s04", "parity")
    request = build_readonly_query_request(
        mode=READ_MODE_CANDIDATE_AUDIT,
        dataset=DATASET_PRICES,
        sql_template_id="row_count",
        candidate_path=candidate_path,
        manifest_refs=({"run_id": "run-cr014-s04"},),
        projections=("trade_date", "ts_code"),
        partition_filters={},
        policy=ReadOnlyQueryPolicy(candidate_audit_paths=(candidate_path,)),
    )
    assert not isinstance(request, DuckDBBoundaryError)
    return request


def test_published_current_truth_readonly_uses_pointer_published_path(tmp_path: Path) -> None:
    layout = LakeLayout(tmp_path)
    request = _published_request(layout)
    result = run_published_current_truth_query(
        request,
        fallback_rows=({"trade_date": "20260526", "ts_code": "000001.SZ", "close": 10.0},),
    )

    assert result.engine == ENGINE_FALLBACK
    assert result.fallback_reason == DUCKDB_DEPENDENCY_UNAVAILABLE
    assert request.source_path == _pointer(layout).published_path
    assert request.source_of_truth == "catalog_current_pointer"
    assert request.claim_effect == CLAIM_EFFECT_EVIDENCE_ONLY
    assert "trade_date" in request.rendered_sql
    assert result.publish_count == 0
    assert result.source_of_truth_updates == 0
    assert result.permission_counters.lake_writes == 0
    assert not list(tmp_path.rglob("*.duckdb"))


def test_candidate_audit_reads_controlled_path_without_current_truth_side_effect(tmp_path: Path) -> None:
    layout = LakeLayout(tmp_path)
    request = _candidate_request(layout)
    result = run_candidate_audit_query(
        request,
        fallback_rows=({"trade_date": "20260526", "ts_code": "000001.SZ"},),
    )
    evidence = run_fallback_audit(
        request,
        rows=result.rows,
        reason=result.fallback_reason or DUCKDB_DEPENDENCY_UNAVAILABLE,
    )

    assert result.engine == ENGINE_FALLBACK
    assert request.mode == READ_MODE_CANDIDATE_AUDIT
    assert request.candidate_path == str(layout.candidate_audit_path(DATASET_PRICES, "run-cr014-s04", "parity"))
    assert evidence.candidate_unpublished is True
    assert evidence.source_of_truth == "candidate_audit_evidence"
    assert evidence.publish_count == 0
    assert evidence.current_pointer_changes == 0


def test_forbidden_sql_template_is_rejected_before_execution(tmp_path: Path) -> None:
    layout = LakeLayout(tmp_path)
    pointer = _pointer(layout)
    request = build_readonly_query_request(
        mode=READ_MODE_PUBLISHED_CURRENT_TRUTH,
        dataset=DATASET_PRICES,
        sql_template_id="write_template",
        catalog_pointer=pointer,
        policy=ReadOnlyQueryPolicy(
            sql_templates={"write_template": "CREATE TABLE x AS SELECT * FROM read_parquet({source_path})"},
            allowed_published_paths=(pointer.published_path,),
        ),
    )

    assert isinstance(request, DuckDBBoundaryError)
    assert request.code == FORBIDDEN_SQL
    assert request.permission_counters.duckdb_writes == 0


def test_candidate_path_must_be_explicitly_allowlisted(tmp_path: Path) -> None:
    layout = LakeLayout(tmp_path)
    candidate_path = layout.candidate_dataset_root(DATASET_PRICES, SCHEMA_VERSION, "run-cr014-s04")
    request = build_readonly_query_request(
        mode=READ_MODE_CANDIDATE_AUDIT,
        dataset=DATASET_PRICES,
        sql_template_id="row_count",
        candidate_path=candidate_path,
        policy=ReadOnlyQueryPolicy(candidate_audit_paths=()),
    )

    assert isinstance(request, DuckDBBoundaryError)
    assert request.code == CANDIDATE_PATH_REJECTED


def test_duckdb_unavailable_uses_fallback_contract_without_dependency_change(tmp_path: Path) -> None:
    request = _published_request(LakeLayout(tmp_path))
    evidence = run_readonly_audit(
        request,
        fallback_rows=({"trade_date": "20260526", "ts_code": "000001.SZ"},),
    )

    assert evidence.engine == ENGINE_FALLBACK
    assert evidence.fallback_reason == DUCKDB_DEPENDENCY_UNAVAILABLE
    assert evidence.permission_counters.dependency_changes == 0
    assert evidence.permission_counters.duckdb_writes == 0
    assert evidence.row_count == 1


def test_readonly_open_failed_falls_back_without_write_mode_retry(tmp_path: Path) -> None:
    request = _published_request(LakeLayout(tmp_path))
    policy = ReadOnlyQueryPolicy(
        duckdb_dependency_approved=True,
        allowed_published_paths=(request.source_path,),
    )
    evidence = run_readonly_audit(
        request,
        policy=policy,
        adapter=ReadOnlyOpenFailingAdapter(),
        fallback_rows=({"trade_date": "20260526", "ts_code": "000001.SZ"},),
    )

    assert evidence.engine == ENGINE_FALLBACK
    assert evidence.fallback_reason == READONLY_OPEN_FAILED
    assert evidence.error_codes == (READONLY_OPEN_FAILED,)
    assert evidence.permission_counters.duckdb_writes == 0
    assert evidence.publish_count == 0


def test_parity_mismatch_is_evidence_only_and_never_publishes(tmp_path: Path) -> None:
    request = _candidate_request(LakeLayout(tmp_path))
    parity = compare_duckdb_with_pandas_pyarrow(
        request,
        duckdb_rows=({"ts_code": "000001.SZ", "close": 10.0},),
        fallback_rows=({"ts_code": "000001.SZ", "close": 11.0},),
        key_fields=("ts_code",),
    )

    assert parity.parity_status == PARITY_MISMATCH
    assert PARITY_MISMATCH_ERROR in parity.error_codes
    assert "checksum" in parity.mismatch_fields
    assert parity.claim_effect == CLAIM_EFFECT_EVIDENCE_ONLY
    assert parity.publish_count == 0
    assert parity.source_of_truth_updates == 0
    assert parity.current_pointer_changes == 0


def test_no_source_of_truth_side_effect_and_dependency_change_zero(tmp_path: Path) -> None:
    published = run_readonly_audit(
        _published_request(LakeLayout(tmp_path)),
        fallback_rows=({"trade_date": "20260526", "ts_code": "000001.SZ"},),
    )
    candidate = run_readonly_audit(
        _candidate_request(LakeLayout(tmp_path)),
        fallback_rows=({"trade_date": "20260526", "ts_code": "000001.SZ"},),
    )
    side_effects = assert_no_source_of_truth_side_effects(published, candidate)

    assert side_effects.passed is True
    assert side_effects.counters["provider_fetches"] == 0
    assert side_effects.counters["lake_writes"] == 0
    assert side_effects.counters["credential_reads"] == 0
    assert side_effects.counters["dependency_changes"] == 0
    assert side_effects.counters["duckdb_writes"] == 0
    assert side_effects.counters["publish_count"] == 0
    assert side_effects.counters["source_of_truth_updates"] == 0
    assert CR014_FORBIDDEN_OPERATION_COUNTERS["duckdb_dependency_change"] == 0
    assert CR014_FORBIDDEN_OPERATION_COUNTERS["duckdb_write"] == 0
    assert CR014_FORBIDDEN_OPERATION_COUNTERS["catalog_current_pointer_publish"] == 0
    assert not list(tmp_path.rglob("*.duckdb"))
