import ast
import hashlib
import json
from pathlib import Path

import pandas as pd
import pytest

from market_data.catalog import CatalogEntry, CatalogStore
from market_data.connectors.protocol import AdapterConfig, ConnectorRequest
from market_data.connectors.tushare import TushareAdapter
from market_data.contracts import (
    DATASET_INDEX_MEMBERS,
    DATASET_INDEX_WEIGHTS,
    DATASET_SCHEMA_REGISTRY,
    DATASET_STOCK_BASIC,
    INTERFACE_INDEX_MEMBERS_SNAPSHOT,
    INTERFACE_INDEX_WEIGHTS_SNAPSHOT,
    INTERFACE_STOCK_BASIC_SNAPSHOT,
    PIT_STATUS_AVAILABLE,
    PIT_STATUS_FAILED,
    PIT_STATUS_INCOMPLETE,
    PIT_STATUS_NON_PIT_SNAPSHOT,
    READINESS_STATUS_NON_PIT_SNAPSHOT,
    READINESS_STATUS_PIT_INCOMPLETE,
    SOURCE_FAKE,
    SOURCE_TUSHARE,
)
from market_data.lake_layout import LakeLayout
from market_data.normalization import DatasetMappingError, map_raw_to_dataset, normalize_run
from market_data.readers import QualityPolicy, read_dataset, read_index_universe
from market_data.source_registry import SourceRegistryError, resolve_interface
from market_data.validation import QUALITY_STATUS_WARN, validate_dataset


def _write_raw_manifest(
    lake_root: Path,
    *,
    interface: str,
    dataset: str,
    rows: list[dict],
    params: dict | None = None,
    run_id: str,
    batch_id: str,
    append_manifest: bool = False,
    finished_at: str = "2026-01-03T09:30:00+08:00",
) -> LakeLayout:
    layout = LakeLayout(lake_root)
    params = {"target_dataset": dataset, **(params or {})}
    raw_path = layout.raw_batch_path(SOURCE_TUSHARE, interface, "2026-01-02", batch_id)
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    metadata = {
        "_metadata": {
            "run_id": run_id,
            "batch_id": batch_id,
            "source": SOURCE_TUSHARE,
            "interface": interface,
            "params": params,
            "row_count": len(rows),
        }
    }
    raw_path.write_text(
        "\n".join(json.dumps(item, ensure_ascii=False, sort_keys=True) for item in [metadata, *rows])
        + "\n",
        encoding="utf-8",
    )
    checksum = hashlib.sha256(raw_path.read_bytes()).hexdigest()
    record = {
        "schema_version": "1.0",
        "run_id": run_id,
        "batch_id": batch_id,
        "idempotency_key": f"{run_id}:{batch_id}",
        "source": SOURCE_TUSHARE,
        "interface": interface,
        "params": params,
        "params_hash": hashlib.sha256(
            json.dumps(params, ensure_ascii=False, sort_keys=True).encode("utf-8")
        ).hexdigest(),
        "requested_at": "2026-01-03T09:00:00+08:00",
        "started_at": "2026-01-03T09:00:00+08:00",
        "finished_at": finished_at,
        "attempts": 1,
        "status": "success",
        "raw_path": str(raw_path.relative_to(lake_root)),
        "raw_checksum": checksum,
        "raw_row_count": len(rows),
        "canonical_path": None,
        "error_type": None,
        "error_message": None,
        "retryable": None,
    }
    manifest_path = layout.manifest_path()
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n"
    if append_manifest and manifest_path.exists():
        with manifest_path.open("a", encoding="utf-8") as fh:
            fh.write(line)
    else:
        manifest_path.write_text(line, encoding="utf-8")
    return layout


def _prepare_s03_lake(lake_root: Path) -> dict[str, object]:
    layout = _write_raw_manifest(
        lake_root,
        interface=INTERFACE_INDEX_MEMBERS_SNAPSHOT,
        dataset=DATASET_INDEX_MEMBERS,
        run_id="run-members",
        batch_id="members",
        params={"index_code": "399300.SZ", "start_date": "20260102", "end_date": "20260102"},
        rows=[
            {
                "trade_date": "20260102",
                "index_code": "399300.sz",
                "con_code": "000001.sz",
                "in_date": "20250101",
                "is_member": True,
                "available_at": "2026-01-03T09:30:00+08:00",
            }
        ],
    )
    members = normalize_run(layout.manifest_path(), lake_root, dataset=DATASET_INDEX_MEMBERS)

    _write_raw_manifest(
        lake_root,
        interface=INTERFACE_STOCK_BASIC_SNAPSHOT,
        dataset=DATASET_STOCK_BASIC,
        run_id="run-stock-basic",
        batch_id="stock-basic",
        append_manifest=True,
        params={"snapshot_date": "20260102"},
        rows=[
            {
                "ts_code": "000001.sz",
                "name": "Ping An Bank",
                "market": "主板",
                "list_status": "L",
                "list_date": "19910403",
                "available_at": "2026-01-03T09:30:00+08:00",
            }
        ],
    )
    stock_basic = normalize_run(layout.manifest_path(), lake_root, dataset=DATASET_STOCK_BASIC)

    _write_raw_manifest(
        lake_root,
        interface=INTERFACE_INDEX_WEIGHTS_SNAPSHOT,
        dataset=DATASET_INDEX_WEIGHTS,
        run_id="run-weights",
        batch_id="weights",
        append_manifest=True,
        params={"index_code": "399300.SZ"},
        rows=[
            {
                "trade_date": "20260102",
                "index_code": "399300.SZ",
                "con_code": "000001.SZ",
                "weight": 0.12,
                "effective_date": "20260102",
                "available_date": "20260103",
                "available_at": "2026-01-03T09:30:00+08:00",
            }
        ],
    )
    weights = normalize_run(layout.manifest_path(), lake_root, dataset=DATASET_INDEX_WEIGHTS)
    return {
        "members": members,
        "stock_basic": stock_basic,
        "weights": weights,
    }


def test_contract_registry_and_exact_tushare_interfaces_are_structured() -> None:
    for dataset in (DATASET_INDEX_MEMBERS, DATASET_INDEX_WEIGHTS, DATASET_STOCK_BASIC):
        registry = DATASET_SCHEMA_REGISTRY[dataset]
        assert registry["columns"]
        assert registry["key_columns"]
        assert registry["pit_fields"] == ("effective_date", "available_date", "available_at")
        assert PIT_STATUS_AVAILABLE in registry["pit_status_values"]
        assert READINESS_STATUS_PIT_INCOMPLETE in registry["readiness_status_values"]

    assert "pit_status" in DATASET_SCHEMA_REGISTRY[DATASET_INDEX_MEMBERS]["columns"]
    assert "readiness_status" in DATASET_SCHEMA_REGISTRY[DATASET_STOCK_BASIC]["columns"]
    assert resolve_interface(SOURCE_FAKE, INTERFACE_INDEX_WEIGHTS_SNAPSHOT).target_dataset == DATASET_INDEX_WEIGHTS

    class Config:
        sources = {
            SOURCE_TUSHARE: {
                "enabled": True,
                "allow_interfaces": (
                    INTERFACE_INDEX_MEMBERS_SNAPSHOT,
                    INTERFACE_INDEX_WEIGHTS_SNAPSHOT,
                    INTERFACE_STOCK_BASIC_SNAPSHOT,
                ),
            }
        }

    members = resolve_interface(SOURCE_TUSHARE, INTERFACE_INDEX_MEMBERS_SNAPSHOT, Config)
    weights = resolve_interface(SOURCE_TUSHARE, INTERFACE_INDEX_WEIGHTS_SNAPSHOT, Config)
    stock_basic = resolve_interface(SOURCE_TUSHARE, INTERFACE_STOCK_BASIC_SNAPSHOT, Config)
    assert (members.target_dataset, members.provider_method, members.pit_required) == (
        DATASET_INDEX_MEMBERS,
        "index_weight",
        True,
    )
    assert (weights.target_dataset, weights.provider_method, weights.pit_required) == (
        DATASET_INDEX_WEIGHTS,
        "index_weight",
        True,
    )
    assert (stock_basic.target_dataset, stock_basic.provider_method, stock_basic.pit_required) == (
        DATASET_STOCK_BASIC,
        "stock_basic",
        True,
    )
    with pytest.raises(SourceRegistryError):
        resolve_interface(SOURCE_TUSHARE, INTERFACE_STOCK_BASIC_SNAPSHOT.upper(), Config)


def test_tushare_adapter_maps_new_interfaces_with_fake_provider_only(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[str, dict]] = []

    class FakeProvider:
        def index_weight(self, **kwargs):
            calls.append(("index_weight", kwargs))
            return [{"index_code": kwargs["index_code"], "con_code": "000001.SZ"}]

        def stock_basic(self, **kwargs):
            calls.append(("stock_basic", kwargs))
            return [{"ts_code": "000001.SZ", "name": "Ping An Bank"}]

    def provider_factory(env_name: str) -> FakeProvider:
        assert env_name == "TUSHARE_TOKEN"
        return FakeProvider()

    monkeypatch.setenv("TUSHARE_TOKEN", "fixture-secret")
    adapter = TushareAdapter(
        AdapterConfig(
            source=SOURCE_TUSHARE,
            enabled=True,
            allow_interfaces=(INTERFACE_INDEX_MEMBERS_SNAPSHOT, INTERFACE_STOCK_BASIC_SNAPSHOT),
            credential_env_vars=("TUSHARE_TOKEN",),
        ),
        provider_factory=provider_factory,
    )
    gated = adapter.fetch(
        ConnectorRequest(
            source=SOURCE_TUSHARE,
            interface=INTERFACE_INDEX_MEMBERS_SNAPSHOT,
            params={"index_code": "399300.SZ", "start_date": "2026-01-02", "end_date": "2026-01-03"},
            run_id="run-members",
            batch_id="members",
        )
    )
    assert gated.error_type == "source_disabled"
    assert calls == []

    members = adapter.fetch(
        ConnectorRequest(
            source=SOURCE_TUSHARE,
            interface=INTERFACE_INDEX_MEMBERS_SNAPSHOT,
            params={
                "target_dataset": DATASET_INDEX_MEMBERS,
                "index_code": "399300.sz",
                "start_date": "2026-01-02",
                "end_date": "2026-01-03",
                "explicit_real_execution": True,
                "offline": False,
            },
            run_id="run-members",
            batch_id="members",
        )
    )
    stock_basic = adapter.fetch(
        ConnectorRequest(
            source=SOURCE_TUSHARE,
            interface=INTERFACE_STOCK_BASIC_SNAPSHOT,
            params={
                "target_dataset": DATASET_STOCK_BASIC,
                "exchange": "",
                "list_status": "L",
                "fields": "ts_code,name,market,list_status,list_date,delist_date",
                "explicit_real_execution": True,
                "offline": False,
            },
            run_id="run-stock-basic",
            batch_id="stock-basic",
        )
    )
    assert members.metadata["provider_interface"] == "index_weight"
    assert stock_basic.metadata["provider_interface"] == "stock_basic"
    assert calls == [
        (
            "index_weight",
            {"index_code": "399300.SZ", "start_date": "20260102", "end_date": "20260103"},
        ),
        (
            "stock_basic",
            {
                "exchange": "",
                "list_status": "L",
                "fields": "ts_code,name,market,list_status,list_date,delist_date",
            },
        ),
    ]
    assert "fixture-secret" not in json.dumps([members.metadata, stock_basic.metadata], ensure_ascii=False)


def test_normalization_defaults_do_not_claim_incomplete_pit_available(tmp_path: Path) -> None:
    results = _prepare_s03_lake(tmp_path)
    members_frame = pd.read_parquet(results["members"].canonical_paths[0])
    stock_basic_frame = pd.read_parquet(results["stock_basic"].canonical_paths[0])

    assert members_frame.iloc[0]["index_code"] == "399300.SZ"
    assert members_frame.iloc[0]["con_code"] == "000001.SZ"
    assert bool(members_frame.iloc[0]["is_pit_universe"]) is True
    assert members_frame.iloc[0]["pit_status"] == PIT_STATUS_AVAILABLE
    assert members_frame.iloc[0]["readiness_status"] == "available"
    assert members_frame.iloc[0]["derived_from"] == "index_weight"
    assert stock_basic_frame.iloc[0]["symbol"] == "000001.SZ"
    assert stock_basic_frame.iloc[0]["pit_status"] == PIT_STATUS_AVAILABLE
    assert stock_basic_frame.iloc[0]["readiness_status"] == "available"

    assert map_raw_to_dataset({"interface": INTERFACE_STOCK_BASIC_SNAPSHOT, "params": {}}) == DATASET_STOCK_BASIC
    with pytest.raises(DatasetMappingError):
        map_raw_to_dataset(
            {
                "interface": INTERFACE_STOCK_BASIC_SNAPSHOT,
                "params": {"target_dataset": DATASET_INDEX_MEMBERS},
            }
        )


def test_validation_outputs_readiness_and_pit_status_without_false_pit_available(tmp_path: Path) -> None:
    results = _prepare_s03_lake(tmp_path)
    members = validate_dataset(
        DATASET_INDEX_MEMBERS,
        tmp_path,
        ("2026-01-02", "2026-01-02"),
        expected_symbols=["000001.SZ"],
        validation_context={
            "canonical_paths": results["members"].canonical_paths,
            "decision_time": "2026-01-03T12:00:00+08:00",
        },
        required=True,
    )
    stock_basic = validate_dataset(
        DATASET_STOCK_BASIC,
        tmp_path,
        ("2026-01-02", "2026-01-02"),
        expected_symbols=["000001.SZ"],
        validation_context={
            "canonical_paths": results["stock_basic"].canonical_paths,
            "decision_time": "2026-01-03T12:00:00+08:00",
        },
        required=True,
    )
    weights = validate_dataset(
        DATASET_INDEX_WEIGHTS,
        tmp_path,
        ("2026-01-02", "2026-01-02"),
        expected_symbols=["000001.SZ"],
        validation_context={
            "canonical_paths": results["weights"].canonical_paths,
            "decision_time": "2026-01-03T12:00:00+08:00",
        },
        required=True,
    )
    future_weights = validate_dataset(
        DATASET_INDEX_WEIGHTS,
        tmp_path,
        ("2026-01-02", "2026-01-02"),
        expected_symbols=["000001.SZ"],
        validation_context={
            "canonical_paths": results["weights"].canonical_paths,
            "decision_time": "2026-01-02T12:00:00+08:00",
        },
        required=True,
    )

    assert members.quality_status == "pass"
    assert members.pit_status == PIT_STATUS_AVAILABLE
    assert members.readiness_status == "available"
    assert "pit_incomplete" not in members.issue_codes
    assert stock_basic.quality_status == "pass"
    assert stock_basic.pit_status == PIT_STATUS_AVAILABLE
    assert stock_basic.readiness_status == "available"
    assert weights.pit_status == PIT_STATUS_AVAILABLE
    assert weights.readiness_status == "available"
    assert future_weights.pit_status == PIT_STATUS_FAILED
    assert "future_availability" in future_weights.issue_codes
    assert [members.pit_status, stock_basic.pit_status].count(PIT_STATUS_AVAILABLE) == 2


def test_reader_blocks_pit_incomplete_and_never_substitutes_weights(tmp_path: Path) -> None:
    results = _prepare_s03_lake(tmp_path)
    store = CatalogStore(tmp_path)
    members_path = results["members"].canonical_paths[0]
    store.upsert(
        CatalogEntry(
            dataset=DATASET_INDEX_MEMBERS,
            quality_status="pass",
            dataset_status="available",
            start_date="2026-01-02",
            end_date="2026-01-02",
            canonical_path=str(members_path.relative_to(tmp_path)),
            latest_manifest_run_id="run-members",
            source=SOURCE_TUSHARE,
            source_interface=INTERFACE_INDEX_MEMBERS_SNAPSHOT,
        )
    )
    available = read_dataset(DATASET_INDEX_MEMBERS, tmp_path, required=True)
    assert available.status == "available"
    assert available.frame is not None
    assert set(available.frame["pit_status"]) == {PIT_STATUS_AVAILABLE}

    allowed_warn = read_dataset(
        DATASET_INDEX_MEMBERS,
        tmp_path,
        quality_policy=QualityPolicy(allow_warn=True, required=True),
        required=True,
    )
    assert allowed_warn.status == "available"
    assert allowed_warn.frame is not None
    assert set(allowed_warn.frame["pit_status"]) == {PIT_STATUS_AVAILABLE}

    weights_only = tmp_path / "weights-only"
    weight_results = _prepare_s03_lake(weights_only)
    weight_path = weight_results["weights"].canonical_paths[0]
    weight_store = CatalogStore(weights_only)
    weight_store.upsert(
        CatalogEntry(
            dataset=DATASET_INDEX_WEIGHTS,
            quality_status="pass",
            dataset_status="available",
            canonical_path=str(weight_path.relative_to(weights_only)),
        )
    )
    before = sorted(path.relative_to(weights_only) for path in weights_only.rglob("*") if path.is_file())
    universe = read_index_universe(weights_only, pit_required=True, required=True)
    after = sorted(path.relative_to(weights_only) for path in weights_only.rglob("*") if path.is_file())

    assert universe.status == "required_missing"
    assert universe.frame is None
    assert any(issue["code"] == "index_members_not_available" for issue in universe.issues)
    assert universe.remediation_spec["not_substituted_by"] == DATASET_INDEX_WEIGHTS
    assert universe.remediation_spec["auto_execute"] is False
    assert before == after


def test_reader_validation_boundaries_and_missing_lake_root_are_offline(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("MARKET_DATA_LAKE_ROOT", raising=False)
    missing = read_dataset(DATASET_INDEX_MEMBERS, None, required=True)
    assert missing.status == "required_missing"
    assert missing.remediation_spec["auto_execute"] is False
    assert missing.remediation_spec["dry_run_default"] is True

    forbidden_modules = {
        "market_data.connectors",
        "market_data.runtime",
        "market_data.storage",
    }
    for path in (Path("market_data/readers.py"), Path("market_data/validation.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        imported: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module if node.level == 0 else f"market_data.{node.module}")
        assert not any(
            module == forbidden or module.startswith(f"{forbidden}.")
            for module in imported
            for forbidden in forbidden_modules
        )
        assert "reports/data_quality_report.csv" not in path.read_text(encoding="utf-8")
