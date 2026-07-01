from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from market_data.catalog import CatalogEntry, CatalogStore
from market_data.contracts import SCHEMA_VERSION
from market_data.lake_layout import LakeLayout
from scripts.data_lake.execute_physical_partition_migration import execute_physical_partition_migration
from scripts.data_lake.plan_physical_partition_migration import build_physical_migration_plan


def _lake_with_legacy_current(tmp_path: Path) -> tuple[Path, Path]:
    lake = tmp_path / "data-lake"
    layout = LakeLayout(lake)
    _add_legacy_catalog_dataset(
        layout,
        dataset="prices",
        run_id="run-a",
        frame=pd.DataFrame({"symbol": ["000001.SZ"], "trade_date": ["20260102"], "close": [1.0]}),
    )
    plan_path = tmp_path / "plan.json"
    plan_path.write_text(json.dumps(build_physical_migration_plan(lake), ensure_ascii=False), encoding="utf-8")
    return lake, plan_path


def _lake_with_two_legacy_current(tmp_path: Path) -> tuple[Path, Path]:
    lake = tmp_path / "data-lake"
    layout = LakeLayout(lake)
    _add_legacy_catalog_dataset(
        layout,
        dataset="prices",
        run_id="run-a",
        frame=pd.DataFrame({"symbol": ["000001.SZ"], "trade_date": ["20260102"], "close": [1.0]}),
    )
    _add_legacy_catalog_dataset(
        layout,
        dataset="bse_code_mapping",
        run_id="run-b",
        frame=pd.DataFrame({"symbol": ["430001.BJ"], "exchange": ["BSE"]}),
    )
    plan_path = tmp_path / "plan.json"
    plan_path.write_text(json.dumps(build_physical_migration_plan(lake), ensure_ascii=False), encoding="utf-8")
    return lake, plan_path


def _add_legacy_catalog_dataset(layout: LakeLayout, *, dataset: str, run_id: str, frame: pd.DataFrame) -> None:
    lake = layout.lake_root
    source = layout.canonical_dataset_root(dataset) / f"run_id={run_id}" / "part.parquet"
    source.parent.mkdir(parents=True, exist_ok=True)
    frame.to_parquet(source, index=False)
    CatalogStore(layout).upsert(
        CatalogEntry(
            dataset=dataset,
            schema_version=SCHEMA_VERSION,
            published=True,
            readiness_status="available",
            quality_status="pass",
            latest_manifest_run_id=run_id,
            canonical_path=str(source.relative_to(lake)),
        )
    )


def test_physical_migration_execute_defaults_to_dry_run(tmp_path: Path) -> None:
    lake, plan_path = _lake_with_legacy_current(tmp_path)
    out = tmp_path / "execution.json"

    result = execute_physical_partition_migration(plan_path=plan_path, out_path=out)

    target = lake / "canonical/prices/1.0/current/part.parquet"
    assert result["mode"] == "dry_run"
    assert result["operation_counts"]["lake_write"] == 0
    assert result["operation_counts"]["catalog_write"] == 0
    assert not target.exists()


def test_physical_migration_requires_approval_for_real_actions(tmp_path: Path) -> None:
    _, plan_path = _lake_with_legacy_current(tmp_path)

    try:
        execute_physical_partition_migration(
            plan_path=plan_path,
            out_path=tmp_path / "execution.json",
            execute_copy=True,
        )
    except ValueError as exc:
        assert "approval_id is required" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("expected approval failure")


def test_physical_migration_requires_created_at_for_real_actions(tmp_path: Path) -> None:
    _, plan_path = _lake_with_legacy_current(tmp_path)

    try:
        execute_physical_partition_migration(
            plan_path=plan_path,
            out_path=tmp_path / "execution.json",
            approval_id="APPROVED-TEST",
            execute_copy=True,
        )
    except ValueError as exc:
        assert "created_at is required" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("expected created_at failure")


def test_physical_migration_execute_copy_and_catalog_update(tmp_path: Path) -> None:
    lake, plan_path = _lake_with_legacy_current(tmp_path)
    out = tmp_path / "execution.json"

    result = execute_physical_partition_migration(
        plan_path=plan_path,
        out_path=out,
        approval_id="APPROVED-TEST",
        created_at="2026-07-01T08:50:00+08:00",
        execute_copy=True,
        update_catalog=True,
    )

    target = lake / "canonical/prices/1.0/current/part.parquet"
    catalog = json.loads((lake / "catalog/catalog.json").read_text(encoding="utf-8"))
    assert result["status"] == "pass"
    assert result["operation_counts"]["lake_write"] == 1
    assert result["operation_counts"]["catalog_write"] == 1
    assert result["operation_counts"]["current_pointer_publish"] == 1
    assert result["post_copy_verifications"][0]["passed"] is True
    assert result["post_copy_verifications"][0]["source_sha256"] == result["post_copy_verifications"][0]["target_sha256"]
    assert result["created_at"] == "2026-07-01T08:50:00+08:00"
    assert target.exists()
    assert catalog["datasets"]["prices"]["canonical_path"] == "canonical/prices/1.0/current/part.parquet"
    assert catalog["datasets"]["prices"]["updated_at"] == "2026-07-01T08:50:00+08:00"
    assert result["legacy_cleanup_executed"] is False
    assert result["nas_sync_executed"] is False


def test_physical_migration_dataset_filter_updates_only_selected_dataset(tmp_path: Path) -> None:
    lake, plan_path = _lake_with_two_legacy_current(tmp_path)
    out = tmp_path / "execution.json"

    result = execute_physical_partition_migration(
        plan_path=plan_path,
        out_path=out,
        approval_id="APPROVED-TEST",
        created_at="2026-07-01T08:50:00+08:00",
        execute_copy=True,
        update_catalog=True,
        datasets=["bse_code_mapping"],
    )

    bse_target = lake / "canonical/bse_code_mapping/1.0/current/part.parquet"
    prices_target = lake / "canonical/prices/1.0/current/part.parquet"
    catalog = json.loads((lake / "catalog/catalog.json").read_text(encoding="utf-8"))
    assert result["status"] == "pass"
    assert result["dataset_filter"] == ["bse_code_mapping"]
    assert result["operation_counts"]["lake_write"] == 1
    assert result["operation_counts"]["catalog_write"] == 1
    assert result["operation_counts"]["current_pointer_publish"] == 1
    assert [item["dataset"] for item in result["copied"]] == ["bse_code_mapping"]
    assert {"dataset": "prices", "reason": "dataset_filter_not_selected"} in result["skipped"]
    assert bse_target.exists()
    assert not prices_target.exists()
    assert catalog["datasets"]["bse_code_mapping"]["canonical_path"] == "canonical/bse_code_mapping/1.0/current/part.parquet"
    assert catalog["datasets"]["prices"]["canonical_path"] == "canonical/prices/1.0/run_id=run-a/part.parquet"


def test_physical_migration_dataset_filter_blocks_unknown_dataset(tmp_path: Path) -> None:
    lake, plan_path = _lake_with_legacy_current(tmp_path)

    result = execute_physical_partition_migration(
        plan_path=plan_path,
        out_path=tmp_path / "execution.json",
        approval_id="APPROVED-TEST",
        created_at="2026-07-01T08:50:00+08:00",
        execute_copy=True,
        update_catalog=True,
        datasets=["missing_dataset"],
    )

    catalog = json.loads((lake / "catalog/catalog.json").read_text(encoding="utf-8"))
    assert result["status"] == "failed"
    assert result["operation_counts"]["catalog_write"] == 0
    assert result["errors"] == [{"dataset": "missing_dataset", "reason": "dataset_not_found_in_plan"}]
    assert catalog["datasets"]["prices"]["canonical_path"] == "canonical/prices/1.0/run_id=run-a/part.parquet"


def test_physical_migration_blocks_catalog_update_when_existing_target_fails_verify(tmp_path: Path) -> None:
    lake, plan_path = _lake_with_legacy_current(tmp_path)
    target = lake / "canonical/prices/1.0/current/part.parquet"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(b"not a valid parquet copy")

    result = execute_physical_partition_migration(
        plan_path=plan_path,
        out_path=tmp_path / "execution.json",
        approval_id="APPROVED-TEST",
        created_at="2026-07-01T08:50:00+08:00",
        update_catalog=True,
    )

    catalog = json.loads((lake / "catalog/catalog.json").read_text(encoding="utf-8"))
    assert result["status"] == "failed"
    assert result["operation_counts"]["catalog_write"] == 0
    assert result["catalog_updates"] == []
    assert result["errors"][0]["reason"] == "pre_catalog_switch_verify_failed"
    assert result["post_copy_verifications"][0]["passed"] is False
    assert catalog["datasets"]["prices"]["canonical_path"] == "canonical/prices/1.0/run_id=run-a/part.parquet"
