import ast
import json
from pathlib import Path

import pandas as pd

from experiments.run_experiment_10 import apply_benchmark_metadata_experiment_10
from experiments.run_experiment_12 import apply_benchmark_metadata_experiment_12
from market_data.benchmarks import (
    BenchmarkPolicy,
    build_hs300_remediation_spec,
    build_next_action,
    resolve_hs300_benchmark,
)
from market_data.catalog import CatalogEntry, CatalogStore
from market_data.contracts import (
    DATASET_HS300_INDEX,
    DATASET_TRADE_CALENDAR,
    INTERFACE_HS300_INDEX_DAILY,
    INTERFACE_TRADE_CALENDAR_DAILY,
    SOURCE_TUSHARE,
)
from market_data.lake_layout import LakeLayout


def write_canonical(lake_root: Path, dataset: str, frame: pd.DataFrame, run_id: str = "run-s04") -> Path:
    path = LakeLayout(lake_root).canonical_dataset_root(dataset) / f"run_id={run_id}" / "part.parquet"
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_parquet(path, index=False)
    return path


def hs300_frame() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "trade_date": "2026-01-02",
                "index_code": "399300.SZ",
                "close": 4000.0,
                "pre_close": 3990.0,
                "pct_chg": 0.25,
                "open": 3991.0,
                "high": 4010.0,
                "low": 3980.0,
                "volume": 100.0,
                "amount": 200.0,
                "benchmark_kind": "price_index",
                "source": SOURCE_TUSHARE,
                "source_interface": INTERFACE_HS300_INDEX_DAILY,
                "source_run_id": "run-s04",
                "schema_version": "1.0",
                "available_at": "2026-01-02T16:00:00+08:00",
                "lineage_raw_checksum": "checksum-hs300",
            },
            {
                "trade_date": "2026-01-05",
                "index_code": "399300.SZ",
                "close": 4010.0,
                "pre_close": 4000.0,
                "pct_chg": 0.25,
                "open": 4001.0,
                "high": 4020.0,
                "low": 3990.0,
                "volume": 101.0,
                "amount": 201.0,
                "benchmark_kind": "price_index",
                "source": SOURCE_TUSHARE,
                "source_interface": INTERFACE_HS300_INDEX_DAILY,
                "source_run_id": "run-s04",
                "schema_version": "1.0",
                "available_at": "2026-01-05T16:00:00+08:00",
                "lineage_raw_checksum": "checksum-hs300",
            },
        ]
    )


def trade_calendar_frame() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "trade_date": "2026-01-02",
                "exchange": "SSE",
                "is_open": True,
                "pretrade_date": "2025-12-31",
                "source": SOURCE_TUSHARE,
                "source_interface": INTERFACE_TRADE_CALENDAR_DAILY,
                "source_run_id": "run-s04",
                "schema_version": "1.0",
                "lineage_raw_checksum": "checksum-calendar",
            },
            {
                "trade_date": "2026-01-03",
                "exchange": "SSE",
                "is_open": False,
                "pretrade_date": "2026-01-02",
                "source": SOURCE_TUSHARE,
                "source_interface": INTERFACE_TRADE_CALENDAR_DAILY,
                "source_run_id": "run-s04",
                "schema_version": "1.0",
                "lineage_raw_checksum": "checksum-calendar",
            },
            {
                "trade_date": "2026-01-05",
                "exchange": "SSE",
                "is_open": True,
                "pretrade_date": "2026-01-02",
                "source": SOURCE_TUSHARE,
                "source_interface": INTERFACE_TRADE_CALENDAR_DAILY,
                "source_run_id": "run-s04",
                "schema_version": "1.0",
                "lineage_raw_checksum": "checksum-calendar",
            },
        ]
    )


def write_available_lake(lake_root: Path) -> None:
    hs300_path = write_canonical(lake_root, DATASET_HS300_INDEX, hs300_frame())
    calendar_path = write_canonical(lake_root, DATASET_TRADE_CALENDAR, trade_calendar_frame())
    store = CatalogStore(lake_root)
    store.upsert(
        CatalogEntry(
            dataset=DATASET_HS300_INDEX,
            start_date="2026-01-02",
            end_date="2026-01-05",
            coverage={"numerator": 2, "denominator": 2, "ratio": 1.0},
            quality_status="pass",
            dataset_status="available",
            latest_manifest_run_id="run-s04",
            source=SOURCE_TUSHARE,
            source_interface=INTERFACE_HS300_INDEX_DAILY,
            lineage_raw_checksum="checksum-hs300",
            canonical_path=str(hs300_path.relative_to(lake_root)),
            quality_csv_path="quality/run-s04/hs300_index_quality.csv",
        )
    )
    store.upsert(
        CatalogEntry(
            dataset=DATASET_TRADE_CALENDAR,
            start_date="2026-01-02",
            end_date="2026-01-05",
            coverage={"numerator": 2, "denominator": 2, "ratio": 1.0},
            quality_status="pass",
            dataset_status="available",
            latest_manifest_run_id="run-s04",
            source=SOURCE_TUSHARE,
            source_interface=INTERFACE_TRADE_CALENDAR_DAILY,
            lineage_raw_checksum="checksum-calendar",
            canonical_path=str(calendar_path.relative_to(lake_root)),
        )
    )


def confirmed_policy(required: bool = False) -> BenchmarkPolicy:
    return BenchmarkPolicy.from_config(
        {"benchmark_kind": "price_index", "confirmed": True, "required": required},
        required=required,
    )


def files_under(root: Path) -> list[str]:
    return sorted(str(path.relative_to(root)) for path in root.rglob("*") if path.is_file())


def test_available_result_schema_and_no_write(tmp_path):
    write_available_lake(tmp_path)
    before = files_under(tmp_path)

    result = resolve_hs300_benchmark(
        tmp_path,
        "2026-01-02",
        "2026-01-05",
        confirmed_policy(),
    )
    after = files_under(tmp_path)
    metadata = result.to_metadata()

    assert result.status == "available"
    assert result.available
    assert result.frame is not None
    assert before == after
    for field in (
        "status",
        "dataset",
        "source",
        "index_code",
        "interface",
        "start_date",
        "end_date",
        "available_start_date",
        "available_end_date",
        "coverage",
        "quality_status",
        "missing_reason",
        "required",
        "benchmark_kind",
        "next_action",
        "remediation_job_spec",
        "catalog_entry",
        "run_id",
        "lineage",
    ):
        assert field in metadata
    assert metadata["dataset"] == "hs300_index"
    assert metadata["source"] == "tushare"
    assert metadata["interface"] == "hs300_index.daily"
    assert metadata["coverage"]["denominator"] == 2
    assert metadata["lineage"]["lineage_raw_checksum"] == "checksum-hs300"


def test_unavailable_required_missing_policy_and_remediation_spec(tmp_path, monkeypatch):
    monkeypatch.setenv("TUSHARE_TOKEN", "secret-token-value")

    optional = resolve_hs300_benchmark(
        tmp_path,
        "2026-01-02",
        "2026-01-05",
        confirmed_policy(required=False),
    )
    required = resolve_hs300_benchmark(
        tmp_path,
        "2026-01-02",
        "2026-01-05",
        confirmed_policy(required=True),
    )
    policy_missing = resolve_hs300_benchmark(
        tmp_path,
        "2026-01-02",
        "2026-01-05",
        BenchmarkPolicy.from_config({"benchmark_kind": "policy_unconfirmed", "required": True}, required=True),
    )

    assert optional.status == "unavailable"
    assert optional.missing_reason == "missing_dataset"
    assert required.status == "required_missing"
    assert policy_missing.status == "required_missing"
    assert policy_missing.missing_reason == "policy_unconfirmed"
    for result in (optional, required, policy_missing):
        payload = result.to_metadata()
        spec = payload["remediation_job_spec"]
        assert payload["next_action"]["auto_execute"] is False
        assert spec["dataset"] == "hs300_index"
        assert spec["source"] == "tushare"
        assert spec["interface"] == "hs300_index.daily"
        assert spec["provider_interface"] == "index_daily"
        assert spec["index_code"] == "399300.SZ"
        assert spec["dry_run"] is True
        assert "source_disabled" in spec["error_enum"]
        assert "interface_not_allowed" in spec["error_enum"]
        assert "missing_credential" in spec["error_enum"]
        assert "lake_root_invalid" in spec["error_enum"]
        assert "quality_failed" in spec["error_enum"]
        assert "resume_conflict" in spec["error_enum"]
        assert "secret-token-value" not in json.dumps(payload, ensure_ascii=False)


def test_quality_failed_and_coverage_gap_are_typed(tmp_path):
    write_available_lake(tmp_path)
    CatalogStore(tmp_path).upsert(
        CatalogEntry(
            dataset=DATASET_HS300_INDEX,
            quality_status="fail",
            dataset_status="quality_failed",
            source=SOURCE_TUSHARE,
            source_interface=INTERFACE_HS300_INDEX_DAILY,
        )
    )
    failed = resolve_hs300_benchmark(tmp_path, "2026-01-02", "2026-01-05", confirmed_policy())
    assert failed.status == "quality_failed"
    assert failed.quality_status == "fail"

    gap_root = tmp_path / "gap"
    hs300_path = write_canonical(gap_root, DATASET_HS300_INDEX, hs300_frame().iloc[[0]].reset_index(drop=True))
    calendar_path = write_canonical(gap_root, DATASET_TRADE_CALENDAR, trade_calendar_frame())
    store = CatalogStore(gap_root)
    store.upsert(
        CatalogEntry(
            dataset=DATASET_HS300_INDEX,
            quality_status="pass",
            dataset_status="available",
            latest_manifest_run_id="run-s04",
            source=SOURCE_TUSHARE,
            source_interface=INTERFACE_HS300_INDEX_DAILY,
            lineage_raw_checksum="checksum-hs300",
            canonical_path=str(hs300_path.relative_to(gap_root)),
        )
    )
    store.upsert(
        CatalogEntry(
            dataset=DATASET_TRADE_CALENDAR,
            quality_status="pass",
            dataset_status="available",
            canonical_path=str(calendar_path.relative_to(gap_root)),
        )
    )
    gap = resolve_hs300_benchmark(gap_root, "2026-01-02", "2026-01-05", confirmed_policy(required=True))
    assert gap.status == "required_missing"
    assert gap.missing_reason == "coverage_gap"
    assert gap.coverage.missing_trade_dates == ["2026-01-05"]


def test_remediation_and_next_action_builders_do_not_execute(tmp_path):
    action = build_next_action("coverage_gap", required=True)
    spec = build_hs300_remediation_spec(
        start_date="2026-01-02",
        end_date="2026-01-05",
        lake_root_hint=tmp_path,
        reason="coverage_gap",
    )

    assert action.type == "run_data_layer_backfill"
    assert action.auto_execute is False
    assert spec.dry_run is True
    assert spec.raw_path is not None
    assert spec.manifest_path is not None
    assert spec.canonical_path is not None
    assert not list((tmp_path / "raw").glob("*"))
    assert not (tmp_path / "manifest").exists()


def test_experiment_metadata_keeps_hs300_and_proxy_baseline_separate(tmp_path):
    write_available_lake(tmp_path)
    available = resolve_hs300_benchmark(tmp_path, "2026-01-02", "2026-01-05", confirmed_policy())
    missing = resolve_hs300_benchmark(tmp_path / "missing", "2026-01-02", "2026-01-05", confirmed_policy())

    exp10 = apply_benchmark_metadata_experiment_10(available, {"initial_cash": 1000.0})
    exp12 = apply_benchmark_metadata_experiment_12(missing, {"proxy_baseline": {"name": "legacy_proxy"}})

    assert exp10["benchmark_result"]["dataset"] == "hs300_index"
    assert exp10["hs300_index"]["status"] == "available"
    assert exp12["benchmark_result"]["status"] == "unavailable"
    assert "hs300_index" not in exp12
    assert exp12["proxy_baseline"] == {"name": "legacy_proxy"}
    assert exp12["hs300_relative_return_enabled"] is False


def test_benchmark_and_experiment_import_boundaries():
    forbidden_exact = {
        "market_data.runtime",
        "market_data.storage",
        "requests",
        "urllib",
        "httpx",
        "aiohttp",
        "socket",
    }
    for source_path in (
        "market_data/benchmarks.py",
        "experiments/run_experiment_10.py",
        "experiments/run_experiment_12.py",
    ):
        tree = ast.parse(Path(source_path).read_text(encoding="utf-8"))
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.append(node.module)
        assert not any(name.startswith("market_data.connectors") for name in imports)
        assert not any(name in forbidden_exact for name in imports)
