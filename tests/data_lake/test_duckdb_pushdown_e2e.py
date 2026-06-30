from pathlib import Path

from market_data.audit import (
    CLAIM_EFFECT_EVIDENCE_ONLY,
    assert_no_source_of_truth_side_effects,
    evidence_from_query_result,
)
from market_data.catalog import CatalogPointer
from market_data.contracts import (
    CR014_UNIVERSE_SCOPE_ALL_A_SHARE,
    DATASET_PRICES,
    QUALITY_STATUS_PASS,
    READINESS_STATUS_AVAILABLE,
    SCHEMA_VERSION,
)
from market_data.duckdb_query import (
    DUCKDB_DEPENDENCY_UNAVAILABLE,
    ENGINE_FALLBACK,
    FORBIDDEN_SQL,
    DuckDBBoundaryError,
    ReadOnlyQueryPolicy,
)
from market_data.lake_layout import LakeLayout
from market_data.readers import read_dataset_via_duckdb_contract


def _pointer(layout: LakeLayout) -> CatalogPointer:
    return CatalogPointer(
        dataset=DATASET_PRICES,
        schema_version=SCHEMA_VERSION,
        coverage_start="1990-12-19",
        coverage_end="2026-05-26",
        coverage_denominator=2,
        latest_manifest_run_id="run-cr139-s36-s37",
        lineage_checksum="lineage-fixture",
        published_at="2026-05-27T00:00:00+00:00",
        known_limitations=[],
        universe_scope=CR014_UNIVERSE_SCOPE_ALL_A_SHARE,
        as_of_trade_date="2026-05-26",
        published_path=str(layout.published_dataset_root(DATASET_PRICES, SCHEMA_VERSION)),
        quality_status=QUALITY_STATUS_PASS,
        readiness_status=READINESS_STATUS_AVAILABLE,
    )


def test_s36_projection_and_predicate_pushdown_are_preserved(tmp_path: Path) -> None:
    layout = LakeLayout(tmp_path)
    pointer = _pointer(layout)

    result = read_dataset_via_duckdb_contract(
        DATASET_PRICES,
        pointer,
        projections=("trade_date", "symbol", "close"),
        partition_filters={"trade_date": "20260526"},
        policy=ReadOnlyQueryPolicy(allowed_published_paths=(pointer.published_path,)),
        fallback_rows=({"trade_date": "20260526", "symbol": "000001.SZ", "close": 10.0},),
    )

    assert not isinstance(result, DuckDBBoundaryError)
    assert result.request.projections == ("trade_date", "symbol", "close")
    assert result.request.partition_filters == {"trade_date": "20260526"}
    assert "SELECT trade_date, symbol, close" in result.request.rendered_sql
    assert "WHERE trade_date = '20260526'" in result.request.rendered_sql
    assert result.engine == ENGINE_FALLBACK
    assert result.fallback_reason == DUCKDB_DEPENDENCY_UNAVAILABLE
    assert result.permission_counters.to_dict() == {
        "provider_fetches": 0,
        "lake_writes": 0,
        "credential_reads": 0,
        "dependency_changes": 0,
        "duckdb_writes": 0,
        "publish_count": 0,
        "source_of_truth_updates": 0,
        "current_pointer_changes": 0,
        "legacy_data_operations": 0,
        "old_report_overwrites": 0,
    }
    assert not list(tmp_path.rglob("*.duckdb"))


def test_s36_forbidden_sql_template_is_blocked_before_execution(tmp_path: Path) -> None:
    layout = LakeLayout(tmp_path)
    pointer = _pointer(layout)

    result = read_dataset_via_duckdb_contract(
        DATASET_PRICES,
        pointer,
        sql_template_id="write_template",
        projections=("trade_date", "symbol"),
        partition_filters={"trade_date": "20260526"},
        policy=ReadOnlyQueryPolicy(
            sql_templates={"write_template": "CREATE TABLE x AS SELECT * FROM read_parquet({source_path})"},
            allowed_published_paths=(pointer.published_path,),
        ),
    )

    assert isinstance(result, DuckDBBoundaryError)
    assert result.code == FORBIDDEN_SQL
    assert result.permission_counters.duckdb_writes == 0
    assert result.permission_counters.source_of_truth_updates == 0
    assert not list(tmp_path.rglob("*.duckdb"))


def test_s37_readonly_e2e_audit_has_no_source_of_truth_side_effects(tmp_path: Path) -> None:
    layout = LakeLayout(tmp_path)
    pointer = _pointer(layout)

    result = read_dataset_via_duckdb_contract(
        DATASET_PRICES,
        pointer,
        projections=("trade_date", "symbol", "close"),
        partition_filters={"trade_date": "20260526"},
        policy=ReadOnlyQueryPolicy(allowed_published_paths=(pointer.published_path,)),
        fallback_rows=(
            {"trade_date": "20260526", "symbol": "000001.SZ", "close": 10.0},
            {"trade_date": "20260526", "symbol": "000002.SZ", "close": 12.5},
        ),
    )

    assert not isinstance(result, DuckDBBoundaryError)
    evidence = evidence_from_query_result(result, run_id="cr139-s37-readonly-e2e")
    side_effect_check = assert_no_source_of_truth_side_effects(result, evidence)

    assert result.ok is True
    assert result.engine == ENGINE_FALLBACK
    assert result.fallback_reason == DUCKDB_DEPENDENCY_UNAVAILABLE
    assert evidence.claim_effect == CLAIM_EFFECT_EVIDENCE_ONLY
    assert evidence.engine == ENGINE_FALLBACK
    assert evidence.row_count == 2
    assert evidence.publish_count == 0
    assert evidence.source_of_truth_updates == 0
    assert evidence.current_pointer_changes == 0
    assert side_effect_check.passed is True
    assert all(value == 0 for value in side_effect_check.counters.values())
    assert not list(tmp_path.rglob("*.duckdb"))
