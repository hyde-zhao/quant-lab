from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pandas as pd

from market_data.catalog import CatalogEntry, CatalogStore
from market_data.contracts import SCHEMA_VERSION
from market_data.lake_layout import LakeLayout
from scripts.data_lake.plan_physical_partition_migration import build_physical_migration_plan


def test_physical_migration_plan_marks_legacy_copy_first_without_writes(tmp_path: Path) -> None:
    lake = tmp_path / "data-lake"
    layout = LakeLayout(lake)
    legacy_path = layout.canonical_dataset_root("prices") / "run_id=run-a" / "part.parquet"
    legacy_path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame({"symbol": ["000001.SZ"], "trade_date": ["20260102"], "close": [1.0]}).to_parquet(
        legacy_path,
        index=False,
    )
    CatalogStore(layout).upsert(
        CatalogEntry(
            dataset="prices",
            schema_version=SCHEMA_VERSION,
            published=True,
            readiness_status="available",
            quality_status="pass",
            latest_manifest_run_id="run-a",
            data_run_id="run-a",
            canonical_path=str(legacy_path.relative_to(lake)),
            lineage_checksum="sha256:test",
        )
    )

    plan = build_physical_migration_plan(lake)

    assert plan["operation_counts"]["lake_write"] == 0
    assert plan["operation_counts"]["physical_partition_migration"] == 0
    assert plan["summary"]["copy_first_candidate_count"] == 1
    prices = plan["datasets"][0]
    assert prices["layout_status"] == "legacy_run_id"
    assert prices["planned_action"] == "copy_first_to_current"
    assert prices["execution_gate_required"] is True
    assert prices["catalog_pointer_update_required"] is True
    assert prices["target_current_path"] == "canonical/prices/1.0/current/part.parquet"
    assert not (layout.canonical_current_root("prices") / "part.parquet").exists()


def test_physical_migration_plan_cli_rejects_output_inside_lake_root(tmp_path: Path) -> None:
    lake = tmp_path / "data-lake"
    layout = LakeLayout(lake)
    CatalogStore(layout).upsert(CatalogEntry(dataset="prices", canonical_path="canonical/prices/1.0/current/part.parquet"))
    out = lake / "plan.json"

    result = subprocess.run(
        [
            sys.executable,
            "scripts/data_lake/plan_physical_partition_migration.py",
            "--lake-root",
            str(lake),
            "--out",
            str(out),
        ],
        cwd=Path(__file__).resolve().parents[2],
        text=True,
        capture_output=True,
    )

    assert result.returncode != 0
    assert "physical migration plan output不能位于 lake_root 内" in result.stderr
    assert not out.exists()


def test_physical_migration_plan_cli_writes_json_outside_lake_root(tmp_path: Path) -> None:
    lake = tmp_path / "data-lake"
    layout = LakeLayout(lake)
    CatalogStore(layout).upsert(CatalogEntry(dataset="prices", canonical_path="canonical/prices/1.0/current/part.parquet"))
    out = tmp_path / "plan.json"

    result = subprocess.run(
        [
            sys.executable,
            "scripts/data_lake/plan_physical_partition_migration.py",
            "--lake-root",
            str(lake),
            "--out",
            str(out),
        ],
        cwd=Path(__file__).resolve().parents[2],
        text=True,
        capture_output=True,
    )

    assert result.returncode == 0
    assert json.loads(out.read_text(encoding="utf-8"))["mode"] == "read_only_plan_no_lake_write"
