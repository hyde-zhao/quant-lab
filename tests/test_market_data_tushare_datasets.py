import hashlib
import json
from pathlib import Path

import pandas as pd
import pytest

from market_data.contracts import (
    DATASET_ADJ_FACTOR,
    DATASET_HS300_INDEX,
    DATASET_INDEX_MEMBERS,
    DATASET_INDEX_WEIGHTS,
    DATASET_PRICES,
    DATASET_SCHEMA_REGISTRY,
    DATASET_STOCK_BASIC,
    DATASET_TRADE_CALENDAR,
    DATASETS,
    INTERFACE_HS300_INDEX_DAILY,
    INTERFACE_INDEX_MEMBERS_SNAPSHOT,
    INTERFACE_INDEX_WEIGHTS_SNAPSHOT,
    INTERFACE_PRICES_ADJ_FACTOR,
    INTERFACE_PRICES_DAILY,
    INTERFACE_STOCK_BASIC_SNAPSHOT,
    INTERFACE_TRADE_CALENDAR_DAILY,
    SOURCE_TUSHARE,
)
from market_data.lake_layout import LakeLayout
from market_data.normalization import (
    CanonicalSchemaError,
    DatasetMappingError,
    map_raw_to_dataset,
    normalize_run,
)
from market_data.source_registry import SourceRegistryError, resolve_interface
from market_data.storage import compute_idempotency_key, compute_params_hash


def write_raw_manifest(
    lake_root: Path,
    *,
    interface: str,
    dataset: str,
    rows: list[dict],
    params: dict | None = None,
    run_id: str = "run-tushare",
    batch_id: str = "b1",
    append_manifest: bool = False,
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
    params_hash = compute_params_hash(params)
    record = {
        "schema_version": "1.0",
        "run_id": run_id,
        "batch_id": batch_id,
        "idempotency_key": compute_idempotency_key(
            run_id,
            batch_id,
            SOURCE_TUSHARE,
            interface,
            params_hash,
        ),
        "source": SOURCE_TUSHARE,
        "interface": interface,
        "params": params,
        "params_hash": params_hash,
        "requested_at": "2026-05-17T00:00:00+00:00",
        "started_at": "2026-05-17T00:00:00+00:00",
        "finished_at": "2026-05-17T00:00:00+00:00",
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
    manifest_line = json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n"
    if append_manifest and manifest_path.exists():
        with manifest_path.open("a", encoding="utf-8") as fh:
            fh.write(manifest_line)
    else:
        manifest_path.write_text(manifest_line, encoding="utf-8")
    return layout


def test_dataset_contracts_and_tushare_exact_registry():
    for dataset in (DATASET_PRICES, DATASET_HS300_INDEX, DATASET_TRADE_CALENDAR, DATASET_INDEX_MEMBERS, DATASET_INDEX_WEIGHTS):
        assert dataset in DATASETS
        assert dataset in DATASET_SCHEMA_REGISTRY
        assert DATASET_SCHEMA_REGISTRY[dataset]["key_columns"]

    class Config:
        sources = {
            SOURCE_TUSHARE: {
                "enabled": True,
                "allow_interfaces": (
                    INTERFACE_PRICES_DAILY,
                    INTERFACE_PRICES_ADJ_FACTOR,
                    INTERFACE_HS300_INDEX_DAILY,
                    INTERFACE_TRADE_CALENDAR_DAILY,
                    INTERFACE_INDEX_MEMBERS_SNAPSHOT,
                    INTERFACE_INDEX_WEIGHTS_SNAPSHOT,
                ),
            }
        }

    assert resolve_interface(SOURCE_TUSHARE, INTERFACE_HS300_INDEX_DAILY, Config).target_dataset == "hs300_index"
    assert resolve_interface(SOURCE_TUSHARE, INTERFACE_PRICES_ADJ_FACTOR, Config).target_dataset == "adj_factor"
    members_spec = resolve_interface(SOURCE_TUSHARE, INTERFACE_INDEX_MEMBERS_SNAPSHOT, Config)
    assert members_spec.target_dataset == "index_members"
    assert members_spec.provider_method == "index_weight"
    with pytest.raises(SourceRegistryError):
        resolve_interface(SOURCE_TUSHARE, "index_daily", Config)


def test_raw_to_dataset_mapping_is_exact_and_conflict_checked():
    assert (
        map_raw_to_dataset(
            {"params": {"target_dataset": "hs300_index"}, "interface": "hs300_index.daily"}
        )
        == "hs300_index"
    )
    with pytest.raises(DatasetMappingError):
        map_raw_to_dataset({"params": {"target_dataset": "prices"}, "interface": "hs300_index.daily"})
    with pytest.raises(DatasetMappingError):
        map_raw_to_dataset({"params": {}, "interface": "HS300_INDEX.DAILY"})


def test_normalize_hs300_index_exact_mapping_and_lineage(tmp_path):
    layout = write_raw_manifest(
        tmp_path,
        interface=INTERFACE_HS300_INDEX_DAILY,
        dataset=DATASET_HS300_INDEX,
        params={"index_code": "399300.SZ"},
        rows=[
            {
                "ts_code": " 399300.sz ",
                "trade_date": "20260102",
                "close": "4000.1",
                "pre_close": "3990.0",
                "pct_chg": "0.25",
                "open": "3991",
                "high": "4010",
                "low": "3980",
                "vol": "100",
                "amount": "200",
            }
        ],
    )
    result = normalize_run(layout.manifest_path(), tmp_path, dataset=DATASET_HS300_INDEX)
    frame = pd.read_parquet(result.canonical_paths[0])
    assert list(frame["index_code"]) == ["399300.SZ"]
    assert list(frame["trade_date"]) == ["2026-01-02"]
    assert frame.iloc[0]["benchmark_kind"] == "price_index"
    assert frame.iloc[0]["source_interface"] == INTERFACE_HS300_INDEX_DAILY
    assert frame.iloc[0]["source_run_id"] == "run-tushare"
    assert frame.iloc[0]["schema_version"] == "1.0"
    assert frame.iloc[0]["lineage_raw_checksum"]


def test_hs300_invalid_date_missing_required_and_duplicate_fail_fast(tmp_path):
    for index, bad_date in enumerate(("2026/01/02", "20261340", "20260230", "2026-13-01", "not-date")):
        root = tmp_path / f"bad-date-{index}"
        layout = write_raw_manifest(
            root,
            interface=INTERFACE_HS300_INDEX_DAILY,
            dataset=DATASET_HS300_INDEX,
            params={"index_code": "399300.SZ"},
            rows=[{"ts_code": "399300.SZ", "trade_date": bad_date, "close": 1, "pre_close": 1}],
        )
        with pytest.raises(CanonicalSchemaError, match="invalid_date"):
            normalize_run(layout.manifest_path(), root, dataset=DATASET_HS300_INDEX)

    valid = write_raw_manifest(
        tmp_path / "valid-iso-date",
        interface=INTERFACE_HS300_INDEX_DAILY,
        dataset=DATASET_HS300_INDEX,
        params={"index_code": "399300.SZ"},
        rows=[{"ts_code": "399300.SZ", "trade_date": "2026-02-28", "close": 1, "pre_close": 1}],
    )
    result = normalize_run(valid.manifest_path(), tmp_path / "valid-iso-date", dataset=DATASET_HS300_INDEX)
    frame = pd.read_parquet(result.canonical_paths[0])
    assert frame.iloc[0]["trade_date"] == "2026-02-28"

    layout = write_raw_manifest(
        tmp_path / "missing",
        interface=INTERFACE_HS300_INDEX_DAILY,
        dataset=DATASET_HS300_INDEX,
        params={"index_code": "399300.SZ"},
        rows=[{"trade_date": "20260102", "close": 1, "pre_close": 1}],
    )
    with pytest.raises(CanonicalSchemaError, match="ts_code"):
        normalize_run(layout.manifest_path(), tmp_path / "missing", dataset=DATASET_HS300_INDEX)

    layout = write_raw_manifest(
        tmp_path / "duplicate",
        interface=INTERFACE_HS300_INDEX_DAILY,
        dataset=DATASET_HS300_INDEX,
        params={"index_code": "399300.SZ"},
        rows=[
            {"ts_code": "399300.SZ", "trade_date": "20260102", "close": 1, "pre_close": 1},
            {"ts_code": "399300.SZ", "trade_date": "20260102", "close": 2, "pre_close": 1},
        ],
    )
    with pytest.raises(CanonicalSchemaError, match="duplicate_key"):
        normalize_run(layout.manifest_path(), tmp_path / "duplicate", dataset=DATASET_HS300_INDEX)


def test_prices_adjusted_price_generation_and_policy_conflict(tmp_path):
    layout = write_raw_manifest(
        tmp_path,
        interface=INTERFACE_PRICES_DAILY,
        dataset=DATASET_PRICES,
        params={"adjustment_policy": "qfq"},
        rows=[
            {
                "ts_code": "000001.SZ",
                "trade_date": "20260102",
                "open": 10,
                "high": 11,
                "low": 9,
                "close": 10.5,
                "adj_factor": 2,
                "adjustment_policy": "qfq",
                "available_at": "2026-01-02T16:00:00+08:00",
            }
        ],
    )
    result = normalize_run(layout.manifest_path(), tmp_path, dataset=DATASET_PRICES)
    frame = pd.read_parquet(result.canonical_paths[0])
    assert frame.iloc[0]["symbol"] == "000001.SZ"
    assert frame.iloc[0]["adj_factor"] == 2
    assert frame.iloc[0]["adjusted_close"] == 21.0
    assert frame.iloc[0]["adjustment_policy"] == "qfq"

    layout = write_raw_manifest(
        tmp_path / "conflict",
        interface=INTERFACE_PRICES_DAILY,
        dataset=DATASET_PRICES,
        rows=[
            {
                "symbol": "000001.SZ",
                "trade_date": "20260102",
                "close": 10,
                "adj_factor": 1,
                "adjustment_policy": "qfq",
                "available_at": "2026-01-02T16:00:00+08:00",
            },
            {
                "symbol": "000002.SZ",
                "trade_date": "20260102",
                "close": 10,
                "adj_factor": 1,
                "adjustment_policy": "hfq",
                "available_at": "2026-01-02T16:00:00+08:00",
            },
        ],
    )
    with pytest.raises(CanonicalSchemaError, match="adjustment_policy_conflict"):
        normalize_run(layout.manifest_path(), tmp_path / "conflict", dataset=DATASET_PRICES)


def test_prices_daily_joins_separate_adj_factor_manifest(tmp_path):
    root = tmp_path / "separate-adj"
    layout = write_raw_manifest(
        root,
        interface=INTERFACE_PRICES_DAILY,
        dataset=DATASET_PRICES,
        params={"adjustment_policy": "qfq"},
        batch_id="daily",
        rows=[
            {
                "ts_code": "000001.SZ",
                "trade_date": "20260102",
                "open": 10,
                "high": 11,
                "low": 9,
                "close": 10.5,
            }
        ],
    )
    write_raw_manifest(
        root,
        interface=INTERFACE_PRICES_ADJ_FACTOR,
        dataset=DATASET_ADJ_FACTOR,
        params={"adjustment_policy": "qfq"},
        batch_id="adj",
        append_manifest=True,
        rows=[{"ts_code": "000001.SZ", "trade_date": "20260102", "adj_factor": 2}],
    )

    result = normalize_run(layout.manifest_path(), root, dataset=DATASET_PRICES)
    frame = pd.read_parquet(result.canonical_paths[0])
    assert frame.iloc[0]["adj_factor"] == 2
    assert frame.iloc[0]["adjusted_open"] == 20
    assert frame.iloc[0]["adjusted_high"] == 22
    assert frame.iloc[0]["adjusted_low"] == 18
    assert frame.iloc[0]["adjusted_close"] == 21
    assert frame.iloc[0]["adjustment_policy"] == "qfq"
    assert frame.iloc[0]["available_at"] == "2026-01-02T16:00:00+08:00"
    assert {record["interface"] for record in result.manifest_records} == {
        INTERFACE_PRICES_DAILY,
        INTERFACE_PRICES_ADJ_FACTOR,
    }


def test_tushare_adj_factor_derives_daily_available_at_not_run_finished(tmp_path):
    layout = write_raw_manifest(
        tmp_path,
        interface=INTERFACE_PRICES_ADJ_FACTOR,
        dataset=DATASET_ADJ_FACTOR,
        params={"adjustment_policy": "qfq"},
        rows=[{"ts_code": "000001.SZ", "trade_date": "20260102", "adj_factor": 2}],
    )

    result = normalize_run(layout.manifest_path(), tmp_path, dataset=DATASET_ADJ_FACTOR)
    frame = pd.read_parquet(result.canonical_paths[0])

    assert frame.iloc[0]["available_at"] == "2026-01-02T16:00:00+08:00"
    assert frame.iloc[0]["available_at_rule"] == "daily_close_fact"


def test_prices_daily_allows_extra_adj_factor_keys(tmp_path):
    root = tmp_path / "extra-adj"
    layout = write_raw_manifest(
        root,
        interface=INTERFACE_PRICES_DAILY,
        dataset=DATASET_PRICES,
        params={"adjustment_policy": "qfq"},
        batch_id="daily",
        rows=[
            {
                "ts_code": "000001.SZ",
                "trade_date": "20260102",
                "open": 10,
                "high": 11,
                "low": 9,
                "close": 10.5,
            }
        ],
    )
    write_raw_manifest(
        root,
        interface=INTERFACE_PRICES_ADJ_FACTOR,
        dataset=DATASET_ADJ_FACTOR,
        params={"adjustment_policy": "qfq"},
        batch_id="adj",
        append_manifest=True,
        rows=[
            {"ts_code": "000001.SZ", "trade_date": "20260102", "adj_factor": 2},
            {"ts_code": "000001.SZ", "trade_date": "20260103", "adj_factor": 2.1},
        ],
    )

    result = normalize_run(layout.manifest_path(), root, dataset=DATASET_PRICES)
    frame = pd.read_parquet(result.canonical_paths[0])

    assert len(frame) == 1
    assert frame.iloc[0]["adj_factor"] == 2


def test_prices_separate_adj_factor_missing_duplicate_and_policy_fail_fast(tmp_path):
    missing = tmp_path / "missing-adj"
    missing_layout = write_raw_manifest(
        missing,
        interface=INTERFACE_PRICES_DAILY,
        dataset=DATASET_PRICES,
        params={"adjustment_policy": "qfq"},
        batch_id="daily",
        rows=[
            {
                "symbol": "000001.SZ",
                "trade_date": "20260102",
                "close": 10,
                "available_at": "2026-01-02T16:00:00+08:00",
            }
        ],
    )
    write_raw_manifest(
        missing,
        interface=INTERFACE_PRICES_ADJ_FACTOR,
        dataset=DATASET_ADJ_FACTOR,
        params={"adjustment_policy": "qfq"},
        batch_id="adj",
        append_manifest=True,
        rows=[{"symbol": "000002.SZ", "trade_date": "20260102", "adj_factor": 2}],
    )
    with pytest.raises(CanonicalSchemaError, match="missing adj_factor"):
        normalize_run(missing_layout.manifest_path(), missing, dataset=DATASET_PRICES)

    duplicate = tmp_path / "duplicate-adj"
    duplicate_layout = write_raw_manifest(
        duplicate,
        interface=INTERFACE_PRICES_DAILY,
        dataset=DATASET_PRICES,
        params={"adjustment_policy": "qfq"},
        batch_id="daily",
        rows=[
            {
                "symbol": "000001.SZ",
                "trade_date": "20260102",
                "close": 10,
                "available_at": "2026-01-02T16:00:00+08:00",
            }
        ],
    )
    write_raw_manifest(
        duplicate,
        interface=INTERFACE_PRICES_ADJ_FACTOR,
        dataset=DATASET_ADJ_FACTOR,
        params={"adjustment_policy": "qfq"},
        batch_id="adj",
        append_manifest=True,
        rows=[
            {"symbol": "000001.SZ", "trade_date": "20260102", "adj_factor": 2},
            {"symbol": "000001.SZ", "trade_date": "20260102", "adj_factor": 2},
        ],
    )
    with pytest.raises(CanonicalSchemaError, match="duplicate_key"):
        normalize_run(duplicate_layout.manifest_path(), duplicate, dataset=DATASET_PRICES)

    conflict = tmp_path / "policy-conflict-adj"
    conflict_layout = write_raw_manifest(
        conflict,
        interface=INTERFACE_PRICES_DAILY,
        dataset=DATASET_PRICES,
        params={"adjustment_policy": "qfq"},
        batch_id="daily",
        rows=[
            {
                "symbol": "000001.SZ",
                "trade_date": "20260102",
                "close": 10,
                "available_at": "2026-01-02T16:00:00+08:00",
            }
        ],
    )
    write_raw_manifest(
        conflict,
        interface=INTERFACE_PRICES_ADJ_FACTOR,
        dataset=DATASET_ADJ_FACTOR,
        params={"adjustment_policy": "hfq"},
        batch_id="adj",
        append_manifest=True,
        rows=[{"symbol": "000001.SZ", "trade_date": "20260102", "adj_factor": 2}],
    )
    with pytest.raises(CanonicalSchemaError, match="adjustment_policy_conflict"):
        normalize_run(conflict_layout.manifest_path(), conflict, dataset=DATASET_PRICES)


def test_trade_calendar_and_index_weights_pit_fields(tmp_path):
    calendar = write_raw_manifest(
        tmp_path / "calendar",
        interface=INTERFACE_TRADE_CALENDAR_DAILY,
        dataset=DATASET_TRADE_CALENDAR,
        rows=[{"cal_date": "20260102", "exchange": "SSE", "is_open": 1, "pretrade_date": "20260101"}],
    )
    cal_result = normalize_run(calendar.manifest_path(), tmp_path / "calendar", dataset=DATASET_TRADE_CALENDAR)
    cal_frame = pd.read_parquet(cal_result.canonical_paths[0])
    assert bool(cal_frame.iloc[0]["is_open"]) is True
    assert cal_frame.iloc[0]["available_at"] == "2026-01-02T00:00:00+08:00"
    assert cal_frame.iloc[0]["available_at_rule"] == "calendar_known"

    weights = write_raw_manifest(
        tmp_path / "weights",
        interface=INTERFACE_INDEX_WEIGHTS_SNAPSHOT,
        dataset=DATASET_INDEX_WEIGHTS,
        rows=[
            {
                "trade_date": "20260102",
                "index_code": "399300.SZ",
                "con_code": "000001.SZ",
                "weight": 0.12,
                "effective_date": "20260102",
                "available_date": "20260103",
                "available_at": "2026-01-03T09:00:00+08:00",
            }
        ],
    )
    weight_result = normalize_run(weights.manifest_path(), tmp_path / "weights", dataset=DATASET_INDEX_WEIGHTS)
    weight_frame = pd.read_parquet(weight_result.canonical_paths[0])
    assert weight_frame.iloc[0]["available_at"] == "2026-01-03T09:00:00+08:00"
    assert weight_frame.iloc[0]["pit_status"] == "pit_available"

    missing_pit = write_raw_manifest(
        tmp_path / "missing-pit",
        interface=INTERFACE_INDEX_WEIGHTS_SNAPSHOT,
        dataset=DATASET_INDEX_WEIGHTS,
        rows=[
            {
                "trade_date": "20260102",
                "index_code": "399300.SZ",
                "con_code": "000001.SZ",
                "weight": 0.12,
            }
        ],
    )
    missing_result = normalize_run(missing_pit.manifest_path(), tmp_path / "missing-pit", dataset=DATASET_INDEX_WEIGHTS)
    missing_frame = pd.read_parquet(missing_result.canonical_paths[0])
    assert missing_frame.iloc[0]["available_at"] == "2026-01-02T16:00:00+08:00"
    assert missing_frame.iloc[0]["available_at_rule"] == "tushare_index_weight_effective_date_16:00"
    assert missing_frame.iloc[0]["pit_status"] == "pit_available"
    assert missing_frame.iloc[0]["readiness_status"] == "available"


def test_tushare_index_weight_raw_can_derive_pit_index_members(tmp_path):
    layout = write_raw_manifest(
        tmp_path,
        interface=INTERFACE_INDEX_WEIGHTS_SNAPSHOT,
        dataset=DATASET_INDEX_WEIGHTS,
        params={"index_code": "399300.SZ"},
        rows=[
            {
                "trade_date": "20260102",
                "index_code": "399300.SZ",
                "con_code": "000001.SZ",
                "weight": 0.12,
            },
            {
                "trade_date": "20260102",
                "index_code": "399300.SZ",
                "con_code": "000002.SZ",
                "weight": 0.34,
            },
        ],
    )

    weights = normalize_run(layout.manifest_path(), tmp_path, dataset=DATASET_INDEX_WEIGHTS)
    members = normalize_run(layout.manifest_path(), tmp_path, dataset=DATASET_INDEX_MEMBERS)
    weight_frame = pd.read_parquet(weights.canonical_paths[0])
    member_frame = pd.read_parquet(members.canonical_paths[0])

    assert len(weight_frame) == len(member_frame) == 2
    assert set(member_frame["con_code"]) == {"000001.SZ", "000002.SZ"}
    assert set(member_frame["is_member"]) == {True}
    assert set(member_frame["is_pit_universe"]) == {True}
    assert set(member_frame["pit_status"]) == {"pit_available"}
    assert set(member_frame["readiness_status"]) == {"available"}
    assert set(member_frame["derived_from"]) == {"index_weight"}


def test_tushare_stock_basic_prefers_ts_code_over_plain_symbol(tmp_path):
    layout = write_raw_manifest(
        tmp_path,
        interface=INTERFACE_STOCK_BASIC_SNAPSHOT,
        dataset=DATASET_STOCK_BASIC,
        params={"snapshot_date": "2026-01-02"},
        rows=[
            {
                "ts_code": "000001.SZ",
                "symbol": "000001",
                "name": "Ping An Bank",
                "market": "主板",
                "list_status": "L",
                "list_date": "19910403",
            }
        ],
    )

    result = normalize_run(layout.manifest_path(), tmp_path, dataset=DATASET_STOCK_BASIC)
    frame = pd.read_parquet(result.canonical_paths[0])

    assert frame.iloc[0]["symbol"] == "000001.SZ"
    assert frame.iloc[0]["pit_status"] == "pit_available"
    assert frame.iloc[0]["readiness_status"] == "available"


def test_normalization_boundary_does_not_import_provider_or_token(monkeypatch):
    monkeypatch.setenv("TUSHARE_TOKEN", "secret-value")
    import market_data.normalization as normalization

    source = Path(normalization.__file__).read_text(encoding="utf-8")
    assert "connectors.tushare" not in source
    assert "os.environ" not in source
    assert "TUSHARE_TOKEN" not in source
