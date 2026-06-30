from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pandas as pd

from market_data.catalog import CatalogEntry, CatalogStore
from market_data.contracts import SCHEMA_VERSION
from market_data.lake_layout import LakeLayout
from market_data.remediation_baseline import (
    ALLOWED_ATTRIBUTIONS,
    BASELINE_FILENAME,
    MINIMUM_METRIC_IDS,
    compare_golden_baselines,
    freeze_golden_baseline,
    load_baseline_snapshot,
)
from market_data.remediation_inventory import build_inventory


def test_freeze_covers_all_minimum_metric_specs_and_s01_inventory_contract(tmp_path: Path) -> None:
    lake = _mini_lake(tmp_path)
    inventory = build_inventory(lake, scanned_at="2026-06-28T20:40:58+08:00")
    snapshot = freeze_golden_baseline(lake, inventory=inventory)

    metric_ids = {metric["metric_id"] for dataset in snapshot.to_dict()["datasets"] for metric in dataset["metrics"]}
    assert set(MINIMUM_METRIC_IDS).issubset(metric_ids)
    assert snapshot.source_inventory_id
    assert len(snapshot.source_inventory_id) == 64
    assert snapshot.operation_counts == {
        "provider_fetch": 0,
        "lake_write": 0,
        "catalog_write": 0,
        "current_pointer_publish": 0,
        "credential_read": 0,
    }


def test_freeze_is_bitwise_deterministic_for_same_lake_state(tmp_path: Path) -> None:
    lake = _mini_lake(tmp_path)
    first = freeze_golden_baseline(lake).to_json()
    second = freeze_golden_baseline(lake).to_json()
    assert first == second


def test_freeze_does_not_modify_catalog_or_lake_files(tmp_path: Path) -> None:
    lake = _mini_lake(tmp_path)
    layout = LakeLayout(lake)
    before = _tree_hash(lake)
    catalog_before = _sha256(layout.catalog_root / "catalog.json")

    freeze_golden_baseline(lake, out_dir=tmp_path / "baseline")

    assert _sha256(layout.catalog_root / "catalog.json") == catalog_before
    after_without_out = _tree_hash(lake)
    assert after_without_out == before


def test_compare_structural_fix_attribution_for_dedup_metric(tmp_path: Path) -> None:
    lake = _mini_lake(tmp_path)
    baseline = freeze_golden_baseline(lake)
    _write_dataset(
        LakeLayout(lake),
        "prices",
        pd.DataFrame(
            {
                "symbol": ["000001", "000002"],
                "trade_date": ["20260101", "20260102"],
                "close": [1.0, 2.0],
            }
        ),
    )
    current = freeze_golden_baseline(lake)

    report = compare_golden_baselines(baseline, current, structural_changes=["CR139-S07"])
    dedup_diffs = [diff for diff in report.diffs if diff.metric_id == "unique_key_dup_count"]
    assert dedup_diffs
    assert {diff.attribution for diff in dedup_diffs} == {"structural_fix"}
    assert report.ambiguous_rate <= 0.05


def test_compare_historical_window_change_attribution(tmp_path: Path) -> None:
    lake = _mini_lake(tmp_path)
    baseline = freeze_golden_baseline(lake)
    _write_dataset(
        LakeLayout(lake),
        "hs300_index",
        pd.DataFrame(
            {
                "symbol": ["000300", "000905"],
                "trade_date": ["20260101", "20260102"],
                "close": [1.0, 2.0],
            }
        ),
    )
    current = freeze_golden_baseline(lake)

    report = compare_golden_baselines(baseline, current)
    benchmark = [diff for diff in report.diffs if diff.metric_id == "benchmark_window_symbol_set"]
    assert benchmark
    assert {diff.attribution for diff in benchmark} == {"historical_data_change"}


def test_compare_report_has_allowed_attributions_and_warns_on_ambiguous_rate(tmp_path: Path) -> None:
    lake = _mini_lake(tmp_path)
    baseline = freeze_golden_baseline(lake)
    _write_dataset(
        LakeLayout(lake),
        "market_cap",
        pd.DataFrame(
            {
                "symbol": ["000001", "000002", "000003"],
                "trade_date": ["20260101", "20260102", "20260103"],
                "available_at": ["20260101", "20260102", "20260103"],
                "value": [10.0, 20.0, 30.0],
            }
        ),
    )
    current = freeze_golden_baseline(lake)

    report = compare_golden_baselines(baseline, current)
    assert {diff.attribution for diff in report.diffs}.issubset(set(ALLOWED_ATTRIBUTIONS))
    assert report.status in {"PASS", "WARN"}


def test_cli_freeze_and_compare_outputs_json(tmp_path: Path) -> None:
    lake = _mini_lake(tmp_path)
    baseline_dir = tmp_path / "baseline"
    current_dir = tmp_path / "current"
    root = Path(__file__).resolve().parents[2]

    freeze_result = subprocess.run(
        [
            sys.executable,
            "scripts/lake_golden_baseline.py",
            "freeze",
            "--lake-root",
            str(lake),
            "--out",
            str(baseline_dir),
        ],
        cwd=root,
        check=True,
        text=True,
        capture_output=True,
    )
    assert json.loads(freeze_result.stdout)["schema_version"] == "golden_baseline_v1"
    assert (baseline_dir / BASELINE_FILENAME).exists()

    freeze_golden_baseline(lake, out_dir=current_dir)
    compare_result = subprocess.run(
        [
            sys.executable,
            "scripts/lake_golden_baseline.py",
            "compare",
            "--baseline",
            str(baseline_dir),
            "--current",
            str(current_dir),
            "--structural-changes",
            '["CR139-S07"]',
        ],
        cwd=root,
        check=True,
        text=True,
        capture_output=True,
    )
    assert json.loads(compare_result.stdout)["schema_version"] == "golden_diff_v1"


def test_cli_freeze_rejects_output_inside_lake_root(tmp_path: Path) -> None:
    lake = _mini_lake(tmp_path)
    result = subprocess.run(
        [
            sys.executable,
            "scripts/lake_golden_baseline.py",
            "freeze",
            "--lake-root",
            str(lake),
            "--out",
            str(lake / "baseline"),
        ],
        cwd=Path(__file__).resolve().parents[2],
        text=True,
        capture_output=True,
    )
    assert result.returncode != 0
    assert "输出路径不能位于 lake_root 内" in result.stderr
    assert not (lake / "baseline").exists()


def test_cli_compare_rejects_output_inside_lake_root(tmp_path: Path) -> None:
    lake = _mini_lake(tmp_path)
    baseline_dir = tmp_path / "baseline"
    current_dir = tmp_path / "current"
    freeze_golden_baseline(lake, out_dir=baseline_dir)
    freeze_golden_baseline(lake, out_dir=current_dir)

    result = subprocess.run(
        [
            sys.executable,
            "scripts/lake_golden_baseline.py",
            "compare",
            "--baseline",
            str(baseline_dir),
            "--current",
            str(current_dir),
            "--lake-root",
            str(lake),
            "--out",
            str(lake / "golden-diff-report.json"),
        ],
        cwd=Path(__file__).resolve().parents[2],
        text=True,
        capture_output=True,
    )
    assert result.returncode != 0
    assert "输出路径不能位于 lake_root 内" in result.stderr
    assert not (lake / "golden-diff-report.json").exists()


def test_load_snapshot_accepts_output_directory(tmp_path: Path) -> None:
    lake = _mini_lake(tmp_path)
    out_dir = tmp_path / "baseline"
    freeze_golden_baseline(lake, out_dir=out_dir)
    snapshot = load_baseline_snapshot(out_dir)
    assert snapshot.schema_version == "golden_baseline_v1"


def _mini_lake(tmp_path: Path) -> Path:
    lake = tmp_path / "lake"
    layout = LakeLayout(lake)
    store = CatalogStore(layout)
    for dataset, frame in _frames().items():
        store.upsert(
            CatalogEntry(
                dataset=dataset,
                schema_version=SCHEMA_VERSION,
                published=False,
                pit_status="pit_available" if dataset in {"financial_pit", "market_cap", "events"} else None,
                latest_manifest_run_id="run-a",
                quality_status="unknown",
                readiness_status=None,
                canonical_path=f"canonical/{dataset}/{SCHEMA_VERSION}",
            )
        )
        _write_dataset(layout, dataset, frame)
    return lake


def _frames() -> dict[str, pd.DataFrame]:
    return {
        "prices": pd.DataFrame(
            {
                "symbol": ["000001", "000001", "000002"],
                "trade_date": ["20260101", "20260101", "20260102"],
                "close": [1.0, 1.1, 2.0],
            }
        ),
        "financial_pit": pd.DataFrame(
            {
                "symbol": ["000001", "000002"],
                "trade_date": ["20260101", "20260102"],
                "available_at": ["20260101", "20260105"],
                "value": [100.0, 200.0],
            }
        ),
        "market_cap": pd.DataFrame(
            {
                "symbol": ["000001", "000002"],
                "trade_date": ["20260101", "20260102"],
                "available_at": ["20260101", "20260102"],
                "value": [10.0, 20.0],
            }
        ),
        "events": pd.DataFrame(
            {
                "symbol": ["000001"],
                "trade_date": ["20260101"],
                "available_at": ["20260103"],
                "event": ["dividend"],
            }
        ),
        "hs300_index": pd.DataFrame(
            {
                "symbol": ["000300"],
                "trade_date": ["20260101"],
                "close": [1.0],
            }
        ),
        "feature_panel": pd.DataFrame(
            {
                "symbol": ["000001"],
                "trade_date": ["20260101"],
                "feature": [0.5],
            }
        ),
    }


def _write_dataset(layout: LakeLayout, dataset: str, frame: pd.DataFrame) -> None:
    root = layout.canonical_dataset_root(dataset) / "run_id=run-a"
    root.mkdir(parents=True, exist_ok=True)
    frame.to_parquet(root / "part.parquet", index=False)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _tree_hash(root: Path) -> str:
    rows = []
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        rows.append(f"{path.relative_to(root)}:{_sha256(path)}")
    return hashlib.sha256("\n".join(rows).encode("utf-8")).hexdigest()
