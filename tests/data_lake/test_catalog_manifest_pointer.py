from __future__ import annotations

"""Catalog manifest pointer tests.

Provenance is machine tracked in tests/PROVENANCE.yaml.
"""


# --- Merged from tests/data_lake/test_catalog_manifest_pointer.py ---
from market_data.catalog import (
    CatalogEntry,
    build_catalog_manifest_pair,
    validate_catalog_manifest_consistency,
)
from market_data.contracts import QUALITY_STATUS_PASS, READINESS_STATUS_AVAILABLE


def test_catalog_manifest_are_derived_from_one_source_of_truth():
    entry = CatalogEntry(
        dataset="prices",
        start_date="2026-01-01",
        end_date="2026-01-31",
        quality_status=QUALITY_STATUS_PASS,
        readiness_status=READINESS_STATUS_AVAILABLE,
        latest_manifest_run_id="cr139-w2-prices-tushare-20260131-canonical",
        source="tushare",
        source_interface="daily",
        lineage_checksum="sha256:lineage",
        canonical_path="/lake/published/prices",
        coverage_denominator=21,
        published_at="2026-02-01T00:00:00+08:00",
        known_limitations=[],
        universe_scope="all_a",
        as_of_trade_date="2026-01-31",
    )

    pair = build_catalog_manifest_pair(
        entry,
        manifest_ref="manifest/prices.jsonl",
        triggered_by_cr="CR139",
    )
    check = validate_catalog_manifest_consistency(entry, pair["manifest_record"])

    assert pair["source_of_truth"] == "catalog"
    assert pair["catalog_writes"] == 0
    assert pair["manifest_writes"] == 0
    assert check.passed

# --- Merged from tests/data_lake/test_catalog_manifest_pointer.py ---
from market_data.incremental import AffectedPartition, build_incremental_append_plan
from market_data.publish import build_pointer_advance_plan


def test_incremental_append_plan_and_pointer_plan_are_non_executing():
    current_pointer = {
        "dataset": "prices",
        "schema_version": "1.0",
        "latest_manifest_run_id": "run-old",
        "coverage_end": "2026-01-30",
    }
    append_plan = build_incremental_append_plan(
        current_pointer=current_pointer,
        source_run_id="run-source",
        target_run_id="run-target",
        affected_partitions=(
            AffectedPartition(
                dataset="prices",
                schema_version="1.0",
                trade_date="2026-01-31",
            ),
        ),
    )
    pointer_plan = build_pointer_advance_plan(
        dataset="prices",
        from_run_id="run-old",
        to_run_id="run-target",
        manifest_ref="manifest/ref.jsonl",
        lineage_checksum="sha256:lineage",
        approval_id="approval-record-only",
    )

    assert append_plan.status == "planned"
    assert append_plan.execute_allowed is False
    assert append_plan.lake_write_count == 0
    assert pointer_plan.status == "planned"
    assert pointer_plan.execute_allowed is False
    assert pointer_plan.current_pointer_publish_count == 0

# --- Merged from tests/data_lake/test_catalog_manifest_pointer.py ---

import hashlib
from pathlib import Path

import pandas as pd
import pytest

from market_data.catalog import (
    CATALOG_CURRENT_POINTER_NOT_PUBLISHED,
    CatalogEntry,
    CatalogError,
    CatalogStore,
    catalog_pointer_from_entry,
)
from market_data.contracts import (
    CR014_UNIVERSE_SCOPE_ALL_A_SHARE,
    DATASET_PRICES,
    QUALITY_STATUS_PASS,
    READINESS_STATUS_AVAILABLE,
    SCHEMA_VERSION,
)
from market_data.lake_layout import LakeLayout
from market_data.manifest import ManifestRecord
from market_data.publish import PublishIntent, publish_current_pointer
from market_data.readers import read_dataset
from market_data.validation import VALIDATE_DOES_NOT_PUBLISH, validate_p0_candidate


def test_published_current_pointer_selector_blocks_unpublished_candidate(tmp_path: Path) -> None:
    lake = _lake_with_prices(tmp_path)
    store = CatalogStore(LakeLayout(lake))
    store.upsert(_entry(published=False))

    with pytest.raises(CatalogError) as exc_info:
        store.get_published_current_pointer(DATASET_PRICES)

    assert CATALOG_CURRENT_POINTER_NOT_PUBLISHED in str(exc_info.value)


def test_published_current_pointer_selector_returns_only_published_entry(tmp_path: Path) -> None:
    lake = _lake_with_prices(tmp_path)
    store = CatalogStore(LakeLayout(lake))
    store.upsert(_entry(published=True))

    pointer = store.get_published_current_pointer(DATASET_PRICES)

    assert pointer.dataset == DATASET_PRICES
    assert pointer.latest_manifest_run_id == "run-cr139-s04"
    assert pointer.published_path == f"canonical/{DATASET_PRICES}/{SCHEMA_VERSION}/run_id=run-cr139-s04"


def test_validate_pass_does_not_publish_or_advance_current_pointer(tmp_path: Path) -> None:
    lake = _lake_with_prices(tmp_path)
    store = CatalogStore(LakeLayout(lake))
    store.upsert(_entry(published=False))
    before = _tree_hash(lake)

    validation = validate_p0_candidate(
        {
            "dataset": DATASET_PRICES,
            "status": "candidate_unpublished",
            "quality_status": QUALITY_STATUS_PASS,
            "readiness_status": READINESS_STATUS_AVAILABLE,
        },
        lifecycle={"dataset": DATASET_PRICES, "coverage_denominator": 1},
    )
    after = _tree_hash(lake)

    assert validation.passed is True
    assert validation.candidate_unpublished is True
    assert validation.publish_count == 0
    assert validation.current_pointer_changes == 0
    assert validation.details[0]["code"] == VALIDATE_DOES_NOT_PUBLISH
    assert before == after
    with pytest.raises(CatalogError):
        store.get_published_current_pointer(DATASET_PRICES)


def test_explicit_publish_gate_dry_run_does_not_write_catalog_current_pointer(tmp_path: Path) -> None:
    lake = _lake_with_prices(tmp_path)
    store = CatalogStore(LakeLayout(lake))
    store.upsert(_entry(published=False))
    pointer = catalog_pointer_from_entry(_entry(published=True))
    before = _tree_hash(lake)

    result = publish_current_pointer(
        store=store,
        candidate=pointer,
        intent=PublishIntent(
            publish=True,
            approval_token="fixture-approval-token",
            approved_by="user",
            reason="CR139-S04 fixture dry-run publish",
        ),
        dry_run=True,
        quality={
            "quality_status": QUALITY_STATUS_PASS,
            "readiness_status": READINESS_STATUS_AVAILABLE,
        },
        manifest=_manifest(),
        lifecycle={
            "coverage_denominator": pointer.coverage_denominator,
            "lifecycle_denominator_ref": "fixture-denominator",
        },
    )
    after = _tree_hash(lake)

    assert result.publish_allowed is True
    assert result.pointer_changes == 1
    assert result.catalog_writes == 0
    assert result.real_lake_writes == 0
    assert before == after
    with pytest.raises(CatalogError):
        store.get_published_current_pointer(DATASET_PRICES)


def test_reader_only_reads_published_catalog_entry(tmp_path: Path) -> None:
    lake = _lake_with_prices(tmp_path)
    store = CatalogStore(LakeLayout(lake))
    store.upsert(_entry(published=False))

    blocked = read_dataset(DATASET_PRICES, lake)

    assert blocked.status == "unavailable"
    assert blocked.issues[0]["code"] == "catalog_not_published"

    store.upsert(_entry(published=True))
    available = read_dataset(DATASET_PRICES, lake)

    assert available.status == "available"
    assert available.frame is not None
    assert len(available.frame) == 1
    assert available.frame.iloc[0]["symbol"] == "000001"


def _lake_with_prices(tmp_path: Path) -> Path:
    lake = tmp_path / "lake"
    layout = LakeLayout(lake)
    root = layout.canonical_dataset_root(DATASET_PRICES) / "run_id=run-cr139-s04"
    root.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(
        {
            "symbol": ["000001"],
            "trade_date": ["20260101"],
            "source_run_id": ["run-cr139-s04"],
            "close": [1.0],
        }
    ).to_parquet(root / "part.parquet", index=False)
    return lake


def _entry(*, published: bool) -> CatalogEntry:
    return CatalogEntry(
        dataset=DATASET_PRICES,
        schema_version=SCHEMA_VERSION,
        start_date="20260101",
        end_date="20260101",
        coverage={"rows": 1},
        quality_status=QUALITY_STATUS_PASS,
        dataset_status="available",
        latest_manifest_run_id="run-cr139-s04",
        source="fixture",
        source_interface="fixture.prices.daily",
        canonical_path=f"canonical/{DATASET_PRICES}/{SCHEMA_VERSION}/run_id=run-cr139-s04",
        published=published,
        published_at="2026-06-28T21:07:11+08:00" if published else None,
        readiness_status=READINESS_STATUS_AVAILABLE,
        coverage_denominator=1,
        coverage_ratio=1.0,
        coverage_start="20260101",
        coverage_end="20260101",
        lineage_checksum="lineage-fixture",
        universe_scope=CR014_UNIVERSE_SCOPE_ALL_A_SHARE,
        as_of_trade_date="20260101",
    )


def _manifest() -> ManifestRecord:
    return ManifestRecord(
        run_id="run-cr139-s04",
        dataset=DATASET_PRICES,
        source="fixture",
        source_interface="fixture.prices.daily",
        schema_hash="schema-fixture",
        row_count=1,
        quality_status=QUALITY_STATUS_PASS,
        readiness_status=READINESS_STATUS_AVAILABLE,
        lineage_checksum="lineage-fixture",
        lifecycle_denominator_ref="fixture-denominator",
        candidate_path="candidate://cr139-s04/prices",
    )


def _tree_hash(root: Path) -> str:
    rows = []
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        rows.append(f"{path.relative_to(root)}:{hashlib.sha256(path.read_bytes()).hexdigest()}")
    return hashlib.sha256("\n".join(rows).encode("utf-8")).hexdigest()

# --- Merged from tests/data_lake/test_catalog_manifest_pointer.py ---
from argparse import Namespace
import json

from market_data.cli import cmd_published_asof_replay
from market_data.replay import (
    PUBLISHED_ASOF_NOT_PUBLISHED,
    PUBLISHED_ASOF_READY,
    PUBLISHED_ASOF_SNAPSHOT_MISSING,
    PublishedAsOfReplayRequest,
    build_published_asof_replay,
)


def _pointer(**overrides) -> dict[str, object]:
    payload: dict[str, object] = {
        "dataset": "prices",
        "published": True,
        "status": "published",
        "as_of_trade_date": "2026-01-02",
        "published_path": "published://prices/20260102",
        "manifest_ref": "manifest://prices/20260102",
    }
    payload.update(overrides)
    return payload


def test_s35_published_asof_replay_selects_exact_published_snapshot() -> None:
    result = build_published_asof_replay(
        PublishedAsOfReplayRequest(dataset="prices", as_of_trade_date="2026-01-02"),
        [_pointer(), _pointer(dataset="events")],
    )

    assert result.status == PUBLISHED_ASOF_READY
    assert result.ready is True
    assert result.published_path == "published://prices/20260102"
    assert result.manifest_ref == "manifest://prices/20260102"
    assert result.provider_fetches == 0
    assert result.lake_writes == 0
    assert result.catalog_writes == 0
    assert result.manifest_writes == 0
    assert result.current_pointer_changes == 0


def test_s35_published_asof_replay_blocks_candidate_snapshot() -> None:
    result = build_published_asof_replay(
        {"dataset": "prices", "as_of_trade_date": "2026-01-02"},
        [_pointer(published=False, status="candidate_unpublished")],
    )

    assert result.ready is False
    assert result.error_codes == (PUBLISHED_ASOF_NOT_PUBLISHED,)
    assert result.provider_fetches == 0


def test_s35_published_asof_replay_blocks_missing_asof_without_provider_backfill() -> None:
    result = build_published_asof_replay(
        PublishedAsOfReplayRequest(dataset="prices", as_of_trade_date="2026-01-03"),
        [_pointer()],
    )

    assert result.ready is False
    assert result.error_codes == (PUBLISHED_ASOF_SNAPSHOT_MISSING,)
    assert result.details[0]["provider_backfill"] == "forbidden"
    assert result.provider_fetches == 0
    assert result.credential_reads == 0


def test_s35_cli_wrapper_uses_explicit_pointer_json_without_lake_scan() -> None:
    payload = cmd_published_asof_replay(
        Namespace(
            dataset="prices",
            as_of_trade_date="2026-01-02",
            run_id="replay-run",
            batch_id="replay-batch",
            pointer_json=json.dumps([_pointer()]),
        )
    )

    assert payload["ok"] is True
    assert payload["command"] == "published-asof-replay"
    assert payload["status"] == PUBLISHED_ASOF_READY
    assert payload["provider_fetches"] == 0
    assert payload["lake_writes"] == 0
