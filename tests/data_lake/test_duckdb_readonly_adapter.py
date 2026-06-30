from pathlib import Path

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
        latest_manifest_run_id="run-cr139-s13",
        lineage_checksum="lineage-fixture",
        published_at="2026-05-27T00:00:00+00:00",
        known_limitations=[],
        universe_scope=CR014_UNIVERSE_SCOPE_ALL_A_SHARE,
        as_of_trade_date="2026-05-26",
        published_path=str(layout.published_dataset_root(DATASET_PRICES, SCHEMA_VERSION)),
        quality_status=QUALITY_STATUS_PASS,
        readiness_status=READINESS_STATUS_AVAILABLE,
    )


def test_s13_duckdb_readonly_adapter_uses_fallback_without_dependency_change(tmp_path: Path) -> None:
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
    assert result.engine == ENGINE_FALLBACK
    assert result.fallback_reason == DUCKDB_DEPENDENCY_UNAVAILABLE
    assert result.rows == ({"trade_date": "20260526", "symbol": "000001.SZ", "close": 10.0},)
    assert result.permission_counters.dependency_changes == 0
    assert result.permission_counters.duckdb_writes == 0
    assert result.publish_count == 0
    assert result.source_of_truth_updates == 0
    assert not list(tmp_path.rglob("*.duckdb"))


def test_s13_duckdb_readonly_adapter_rejects_forbidden_sql_before_execution(tmp_path: Path) -> None:
    layout = LakeLayout(tmp_path)
    pointer = _pointer(layout)

    result = read_dataset_via_duckdb_contract(
        DATASET_PRICES,
        pointer,
        sql_template_id="write_template",
        policy=ReadOnlyQueryPolicy(
            sql_templates={"write_template": "CREATE TABLE x AS SELECT * FROM read_parquet({source_path})"},
            allowed_published_paths=(pointer.published_path,),
        ),
    )

    assert isinstance(result, DuckDBBoundaryError)
    assert result.code == FORBIDDEN_SQL
    assert result.permission_counters.duckdb_writes == 0


def test_s13_duckdb_dependency_is_not_declared_in_pyproject() -> None:
    pyproject = Path("pyproject.toml").read_text(encoding="utf-8")

    assert "duckdb" not in pyproject.lower()
