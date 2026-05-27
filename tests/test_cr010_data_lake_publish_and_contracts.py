import argparse
import hashlib
import json
from pathlib import Path

import pandas as pd
import pytest

from engine.research_dataset import ResearchDatasetRequest, build_research_dataset
from market_data.catalog import CatalogEntry, CatalogStore
from market_data.catalog import build_catalog_coverage_report, build_production_readiness_report
from market_data.cli import cmd_publish, cmd_report_readiness, cmd_replay, cmd_revalidate, cmd_validate
from market_data.cli import TushareFirstRunSpec, build_tushare_first_plan
from market_data.contracts import (
    DATASET_ADJ_FACTOR,
    DATASET_EVENTS,
    DATASET_HS300_INDEX,
    DATASET_INDEX_MEMBERS,
    DATASET_INDEX_WEIGHTS,
    DATASET_PRICES,
    DATASET_PRICES_LIMIT,
    DATASET_STOCK_BASIC,
    DATASET_TRADE_CALENDAR,
    DATASET_TRADE_STATUS,
    INTERFACE_EVENTS_DISCLOSURE,
    INTERFACE_HS300_INDEX_DAILY,
    INTERFACE_INDEX_MEMBERS_SNAPSHOT,
    INTERFACE_INDEX_WEIGHTS_SNAPSHOT,
    INTERFACE_PRICES_LIMIT_DAILY,
    INTERFACE_PRICES_ADJ_FACTOR,
    INTERFACE_STOCK_BASIC_SNAPSHOT,
    INTERFACE_TRADE_STATUS_DAILY,
    SOURCE_TUSHARE,
)
from market_data.lake_layout import LakeLayout
from market_data.normalization import DatasetMappingError, normalize_run
from market_data.readers import QualityPolicy, ReaderResult, read_dataset
from market_data.storage import compute_idempotency_key, compute_params_hash


def _prices_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "trade_date": ["2026-01-02", "2026-01-03"],
            "symbol": ["000001.SZ", "000001.SZ"],
            "open": [10.0, 10.5],
            "high": [10.8, 11.0],
            "low": [9.8, 10.1],
            "close": [10.2, 10.7],
            "adj_factor": [1.0, 1.0],
            "adjusted_open": [10.0, 10.5],
            "adjusted_high": [10.8, 11.0],
            "adjusted_low": [9.8, 10.1],
            "adjusted_close": [10.2, 10.7],
            "adjustment_policy": ["qfq", "qfq"],
            "source": ["fixture", "fixture"],
            "source_interface": ["prices.daily", "prices.daily"],
            "source_run_id": ["run-cr010", "run-cr010"],
            "schema_version": ["1.0", "1.0"],
            "available_at": ["2026-01-02T16:00:00+08:00", "2026-01-03T16:00:00+08:00"],
            "available_at_rule": ["daily_close_fact", "daily_close_fact"],
            "lineage_raw_checksum": ["checksum-prices", "checksum-prices"],
        }
    )


def _write_prices_canonical(lake_root: Path) -> Path:
    layout = LakeLayout(lake_root)
    path = layout.canonical_dataset_root(DATASET_PRICES) / "run_id=run-cr010" / "part-b1.parquet"
    path.parent.mkdir(parents=True, exist_ok=True)
    _prices_frame().to_parquet(path, index=False)
    return path


def test_validate_writes_unpublished_candidate_and_publish_unlocks_reader(tmp_path: Path) -> None:
    _write_prices_canonical(tmp_path)
    args = argparse.Namespace(
        lake_root=tmp_path,
        dataset=DATASET_PRICES,
        symbols="000001.SZ",
        index_code=None,
        exchange="SSE",
        start_date="2026-01-02",
        end_date="2026-01-03",
        run_id="run-cr010",
        open_trade_dates="2026-01-02,2026-01-03",
        prices_missing_rate_pass=0.0,
        prices_missing_rate_warn=0.05,
        prices_missing_rate_fail=0.2,
    )

    validated = cmd_validate(args)
    assert validated["catalog_status"] == "candidate_unpublished"
    candidate = CatalogStore(tmp_path).get(DATASET_PRICES)
    assert candidate.published is False
    assert candidate.available_at_rule == "daily_close_fact"

    blocked = read_dataset(
        DATASET_PRICES,
        tmp_path,
        quality_policy=QualityPolicy(allow_warn=True, required=True),
        required=True,
    )
    assert blocked.status == "required_missing"
    assert blocked.issues[0]["code"] == "catalog_not_published"

    with pytest.raises(Exception, match="quality_status=warn"):
        cmd_publish(argparse.Namespace(lake_root=tmp_path, dataset=DATASET_PRICES, allow_warn=False))

    published = cmd_publish(argparse.Namespace(lake_root=tmp_path, dataset=DATASET_PRICES, allow_warn=True))
    assert published["publish_status"] == "published"
    revalidated = cmd_revalidate(args)
    assert revalidated["command"] == "revalidate"
    assert CatalogStore(tmp_path).get(DATASET_PRICES).published is True
    result = read_dataset(
        DATASET_PRICES,
        tmp_path,
        quality_policy=QualityPolicy(allow_warn=True, required=True),
        required=True,
    )
    assert result.status == "available"
    assert result.catalog_entry is not None
    assert result.catalog_entry.published is True


def test_validate_prices_can_bind_explicit_pit_universe(tmp_path: Path) -> None:
    _write_prices_canonical(tmp_path)
    args = argparse.Namespace(
        lake_root=tmp_path,
        dataset=DATASET_PRICES,
        symbols="000001.SZ",
        index_code=None,
        exchange="SSE",
        start_date="2026-01-02",
        end_date="2026-01-03",
        run_id="run-cr010",
        open_trade_dates="2026-01-02,2026-01-03",
        decision_time=None,
        is_pit_universe=True,
        prices_missing_rate_pass=0.0,
        prices_missing_rate_warn=0.05,
        prices_missing_rate_fail=0.2,
    )

    validated = cmd_validate(args)
    entry = CatalogStore(tmp_path).get(DATASET_PRICES)

    assert validated["quality_status"] == "pass"
    assert entry.quality_status == "pass"
    assert entry.known_limitations == []


def test_validate_prices_can_use_trade_status_tradable_denominator(tmp_path: Path) -> None:
    layout = LakeLayout(tmp_path)
    price_path = layout.canonical_dataset_root(DATASET_PRICES) / "run_id=run-cr010" / "part-b1.parquet"
    price_path.parent.mkdir(parents=True, exist_ok=True)
    _prices_frame().iloc[[0]].to_parquet(price_path, index=False)

    trade_status_path = layout.canonical_dataset_root(DATASET_TRADE_STATUS) / "run_id=run-trade-status" / "part-b1.parquet"
    trade_status_path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(
        [
            {
                "trade_date": "2026-01-02",
                "symbol": "000001.SZ",
                "is_tradable": True,
                "is_suspended": False,
                "is_st": False,
                "status_reason": "normal",
                "source": "fixture",
                "source_interface": "trade_status.daily",
                "source_run_id": "run-trade-status",
                "available_at": "2026-01-02T16:00:00+08:00",
                "available_at_rule": "daily_close_fact",
                "schema_version": "1.0",
                "lineage_raw_checksum": "checksum-trade-status",
            },
            {
                "trade_date": "2026-01-03",
                "symbol": "000001.SZ",
                "is_tradable": False,
                "is_suspended": True,
                "is_st": False,
                "status_reason": "suspended",
                "source": "fixture",
                "source_interface": "trade_status.daily",
                "source_run_id": "run-trade-status",
                "available_at": "2026-01-03T16:00:00+08:00",
                "available_at_rule": "daily_close_fact",
                "schema_version": "1.0",
                "lineage_raw_checksum": "checksum-trade-status",
            },
        ]
    ).to_parquet(trade_status_path, index=False)
    CatalogStore(tmp_path).upsert(
        CatalogEntry(
            dataset=DATASET_TRADE_STATUS,
            quality_status="pass",
            dataset_status="available",
            published=True,
            source="fixture",
            source_interface="trade_status.daily",
            latest_manifest_run_id="run-trade-status",
            canonical_path=str(trade_status_path.relative_to(tmp_path)),
            readiness_status="available",
            available_at_rule="daily_close_fact",
        )
    )
    args = argparse.Namespace(
        lake_root=tmp_path,
        dataset=DATASET_PRICES,
        symbols="000001.SZ",
        index_code=None,
        exchange="SSE",
        start_date="2026-01-02",
        end_date="2026-01-03",
        run_id="run-cr010",
        open_trade_dates="2026-01-02,2026-01-03",
        decision_time=None,
        is_pit_universe=True,
        use_trade_status_denominator=True,
        prices_missing_rate_pass=0.0,
        prices_missing_rate_warn=0.05,
        prices_missing_rate_fail=0.2,
    )

    validated = cmd_validate(args)

    assert validated["quality_status"] == "pass"
    assert validated["coverage"]["expected_rows"] == 1
    assert validated["coverage"]["missing_rows"] == 0


def test_w3_unresolved_datasets_fail_fast_without_fake_availability(tmp_path: Path) -> None:
    missing = read_dataset(DATASET_EVENTS, tmp_path, required=True)
    assert missing.status == "required_missing"
    assert missing.issues[0]["code"] == "catalog_missing"
    assert missing.remediation_spec["auto_execute"] is False

    CatalogStore(tmp_path).upsert(
        CatalogEntry(
            dataset=DATASET_EVENTS,
            quality_status="pass",
            dataset_status="available",
            published=True,
            source_interface="UNRESOLVED",
        )
    )
    unresolved = read_dataset(DATASET_EVENTS, tmp_path, required=True)
    assert unresolved.status == "required_missing"
    assert unresolved.issues[0]["code"] == "w3_source_unresolved"


def test_adj_factor_normalization_writes_available_at_rule(tmp_path: Path) -> None:
    layout = LakeLayout(tmp_path)
    params = {"target_dataset": DATASET_ADJ_FACTOR, "adjustment_policy": "qfq"}
    raw_path = layout.raw_batch_path(SOURCE_TUSHARE, INTERFACE_PRICES_ADJ_FACTOR, "2026-01-02", "b1")
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    raw_rows = [
        {"_metadata": {"run_id": "run-adj", "batch_id": "b1", "source": SOURCE_TUSHARE}},
        {"ts_code": "000001.SZ", "trade_date": "20260102", "adj_factor": 1.25},
    ]
    raw_path.write_text(
        "\n".join(json.dumps(item, ensure_ascii=False, sort_keys=True) for item in raw_rows) + "\n",
        encoding="utf-8",
    )
    checksum = hashlib.sha256(raw_path.read_bytes()).hexdigest()
    params_hash = compute_params_hash(params)
    manifest = {
        "schema_version": "1.0",
        "run_id": "run-adj",
        "batch_id": "b1",
        "idempotency_key": compute_idempotency_key("run-adj", "b1", SOURCE_TUSHARE, INTERFACE_PRICES_ADJ_FACTOR, params_hash),
        "source": SOURCE_TUSHARE,
        "interface": INTERFACE_PRICES_ADJ_FACTOR,
        "params": params,
        "params_hash": params_hash,
        "requested_at": "2026-05-22T00:00:00+00:00",
        "started_at": "2026-05-22T00:00:00+00:00",
        "finished_at": "2026-05-22T00:00:00+00:00",
        "attempts": 1,
        "status": "success",
        "raw_path": str(raw_path.relative_to(tmp_path)),
        "raw_checksum": checksum,
        "raw_row_count": 1,
        "canonical_path": None,
        "error_type": None,
        "error_message": None,
        "retryable": None,
    }
    layout.manifest_path().parent.mkdir(parents=True, exist_ok=True)
    layout.manifest_path().write_text(json.dumps(manifest, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")

    result = normalize_run(layout.manifest_path(), tmp_path, dataset=DATASET_ADJ_FACTOR)
    frame = pd.read_parquet(result.canonical_paths[0])
    assert frame.iloc[0]["available_at_rule"] == "daily_close_fact"
    assert frame.iloc[0]["adj_factor"] == 1.25

    w3_root = tmp_path / "w3"
    w3_layout = LakeLayout(w3_root)
    w3_params = {"target_dataset": DATASET_EVENTS}
    w3_raw_path = w3_layout.raw_batch_path(SOURCE_TUSHARE, "UNRESOLVED", "2026-01-02", "b1")
    w3_raw_path.parent.mkdir(parents=True, exist_ok=True)
    w3_raw_path.write_text(
        json.dumps({"symbol": "000001.SZ", "event_type": "fixture", "event_date": "2026-01-02"}, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    w3_checksum = hashlib.sha256(w3_raw_path.read_bytes()).hexdigest()
    w3_params_hash = compute_params_hash(w3_params)
    w3_manifest = {
        **manifest,
        "params": w3_params,
        "params_hash": w3_params_hash,
        "interface": "UNRESOLVED",
        "raw_path": str(w3_raw_path.relative_to(w3_root)),
        "raw_checksum": w3_checksum,
        "idempotency_key": compute_idempotency_key("run-adj", "b1", SOURCE_TUSHARE, "UNRESOLVED", w3_params_hash),
    }
    w3_layout.manifest_path().parent.mkdir(parents=True, exist_ok=True)
    w3_layout.manifest_path().write_text(json.dumps(w3_manifest, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    with pytest.raises(DatasetMappingError, match="source_unresolved"):
        normalize_run(w3_layout.manifest_path(), w3_root, dataset=DATASET_EVENTS)


def test_empty_tushare_events_catalog_keeps_stock_st_available_at_rule(tmp_path: Path) -> None:
    layout = LakeLayout(tmp_path)
    params = {
        "target_dataset": DATASET_EVENTS,
        "start_date": "2026-01-02",
        "end_date": "2026-01-03",
    }
    raw_path = layout.raw_batch_path(SOURCE_TUSHARE, INTERFACE_EVENTS_DISCLOSURE, "2026-01-02", "b1")
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    raw_path.write_text(
        json.dumps(
            {"_metadata": {"run_id": "run-events", "batch_id": "b1", "source": SOURCE_TUSHARE}},
            ensure_ascii=False,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    checksum = hashlib.sha256(raw_path.read_bytes()).hexdigest()
    params_hash = compute_params_hash(params)
    manifest = {
        "schema_version": "1.0",
        "run_id": "run-events",
        "batch_id": "b1",
        "idempotency_key": compute_idempotency_key("run-events", "b1", SOURCE_TUSHARE, INTERFACE_EVENTS_DISCLOSURE, params_hash),
        "source": SOURCE_TUSHARE,
        "interface": INTERFACE_EVENTS_DISCLOSURE,
        "params": params,
        "params_hash": params_hash,
        "requested_at": "2026-05-22T00:00:00+00:00",
        "started_at": "2026-05-22T00:00:00+00:00",
        "finished_at": "2026-05-22T00:00:00+00:00",
        "attempts": 1,
        "status": "success",
        "raw_path": str(raw_path.relative_to(tmp_path)),
        "raw_checksum": checksum,
        "raw_row_count": 0,
        "canonical_path": None,
        "error_type": None,
        "error_message": None,
        "retryable": None,
    }
    layout.manifest_path().parent.mkdir(parents=True, exist_ok=True)
    layout.manifest_path().write_text(json.dumps(manifest, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    normalize_run(layout.manifest_path(), tmp_path, dataset=DATASET_EVENTS)

    payload = cmd_validate(
        argparse.Namespace(
            lake_root=tmp_path,
            dataset=DATASET_EVENTS,
            symbols=None,
            index_code="399300.SZ",
            exchange="SSE",
            start_date="2026-01-02",
            end_date="2026-01-03",
            run_id="run-events",
            open_trade_dates=None,
            decision_time=None,
            is_pit_universe=False,
            use_trade_status_denominator=False,
            prices_missing_rate_pass=0.0,
            prices_missing_rate_warn=0.02,
            prices_missing_rate_fail=0.05,
        )
    )

    assert payload["quality_status"] == "pass"
    assert CatalogStore(layout).get(DATASET_EVENTS).available_at_rule == "tushare_stock_st_09:20"


def test_research_dataset_realism_mode_is_reported_in_metadata(tmp_path: Path) -> None:
    prices = _prices_frame()
    calendar = pd.DataFrame({"trade_date": ["2026-01-02", "2026-01-03"], "is_open": [True, True]})

    def fake_reader(dataset, *_args, **_kwargs):
        if dataset == DATASET_PRICES:
            return ReaderResult(
                status="available",
                frame=prices,
                catalog_entry=CatalogEntry(dataset=dataset, quality_status="pass", published=True),
            )
        if dataset == "trade_calendar":
            return ReaderResult(
                status="available",
                frame=calendar,
                catalog_entry=CatalogEntry(dataset=dataset, quality_status="pass", published=True),
            )
        return ReaderResult(status="unavailable", issues=[{"code": "not_required_for_explicit_symbols"}])

    def fake_benchmark_resolver(**_kwargs):
        return {"status": "available", "benchmark_status": "available", "benchmark_kind": "price_index"}

    dataset = build_research_dataset(
        ResearchDatasetRequest(
            lake_root=tmp_path,
            start_date="2026-01-02",
            end_date="2026-01-03",
            symbols=("000001.SZ",),
            realism_mode="exploratory",
        ),
        reader=fake_reader,
        benchmark_resolver=fake_benchmark_resolver,
    )

    assert dataset.metadata["realism_mode"] == "exploratory"
    assert dataset.metadata["analysis_mode"] == "exploratory"
    assert ResearchDatasetRequest(realism_mode="production_strict").analysis_mode == "research"


def test_catalog_coverage_and_production_readiness_reports_disclose_missing_p0(tmp_path: Path) -> None:
    store = CatalogStore(tmp_path)
    store.upsert(
        CatalogEntry(
            dataset=DATASET_PRICES,
            quality_status="pass",
            dataset_status="available",
            published=True,
            start_date="2026-01-02",
            end_date="2026-01-03",
            source="fixture",
            source_interface="prices.daily",
            latest_manifest_run_id="run-prices",
            canonical_path="canonical/prices/1.0/run_id=run-prices/part.parquet",
            readiness_status="available",
            pit_status="not_applicable",
            available_at_rule="daily_close_fact",
            coverage_denominator=2,
            coverage_ratio=1.0,
        )
    )
    store.upsert(
        CatalogEntry(
            dataset=DATASET_HS300_INDEX,
            quality_status="pass",
            dataset_status="available",
            published=True,
            start_date="2026-01-02",
            end_date="2026-01-03",
            source="fixture",
            source_interface="hs300_index.daily",
            latest_manifest_run_id="run-hs300",
            readiness_status="available",
            pit_status="not_applicable",
            available_at_rule="daily_close_fact",
            coverage_denominator=2,
            coverage_ratio=1.0,
        )
    )

    coverage = build_catalog_coverage_report(tmp_path)
    assert coverage["summary"]["dataset_count"] == 7
    assert coverage["summary"]["published_count"] == 2
    assert coverage["summary"]["missing_required_count"] == 5
    assert coverage["summary"]["current_truth_complete"] is False
    assert coverage["old_data_operations"]["read"] == 0
    assert coverage["legacy_quality_report_operations"]["read"] == 0
    missing_datasets = {
        row["dataset"]
        for row in coverage["rows"]
        if row["publish_status"] == "missing_required"
    }
    assert {
        DATASET_ADJ_FACTOR,
        DATASET_TRADE_CALENDAR,
        DATASET_INDEX_MEMBERS,
        DATASET_INDEX_WEIGHTS,
        DATASET_STOCK_BASIC,
    } <= missing_datasets

    strict = build_production_readiness_report(tmp_path, realism_mode="production_strict")
    assert strict["status"] == "fail"
    assert "complete_p0_data_lake" in strict["blocked_claims"]
    assert strict["remediation_spec"]["auto_execute"] is False

    exploratory = build_production_readiness_report(tmp_path, realism_mode="exploratory")
    assert exploratory["status"] == "warn"
    assert "exploratory_analysis" in exploratory["allowed_claims"]

    cli_payload = cmd_report_readiness(
        argparse.Namespace(
            lake_root=tmp_path,
            report="coverage",
            realism_mode="production_strict",
            datasets=None,
            required_source=None,
        )
    )
    assert cli_payload["report_type"] == "catalog_coverage"


def test_production_readiness_can_require_tushare_only_source(tmp_path: Path) -> None:
    store = CatalogStore(tmp_path)
    for dataset in (
        DATASET_PRICES,
        DATASET_ADJ_FACTOR,
        DATASET_HS300_INDEX,
        DATASET_TRADE_CALENDAR,
        DATASET_INDEX_MEMBERS,
        DATASET_INDEX_WEIGHTS,
        DATASET_STOCK_BASIC,
        DATASET_TRADE_STATUS,
        DATASET_PRICES_LIMIT,
        DATASET_EVENTS,
    ):
        source = SOURCE_TUSHARE
        if dataset == DATASET_INDEX_WEIGHTS:
            source = "jqdata"
        store.upsert(
            CatalogEntry(
                dataset=dataset,
                quality_status="pass",
                dataset_status="available",
                published=True,
                start_date="2026-01-02",
                end_date="2026-01-03",
                source=source,
                source_interface=f"{dataset}.daily",
                latest_manifest_run_id=f"run-{dataset}",
                readiness_status="available",
                pit_status="pit_available"
                if dataset in {DATASET_INDEX_MEMBERS, DATASET_INDEX_WEIGHTS, DATASET_STOCK_BASIC}
                else "not_applicable",
                available_at_rule="daily_close_fact",
                coverage_denominator=1,
                coverage_ratio=1.0,
            )
        )

    strict = build_production_readiness_report(
        tmp_path,
        realism_mode="production_strict",
        required_source=SOURCE_TUSHARE,
    )

    assert strict["status"] == "fail"
    assert {
        "code": "source_policy_mismatch",
        "dataset": DATASET_INDEX_WEIGHTS,
        "expected_source": SOURCE_TUSHARE,
        "actual_source": "jqdata",
    } in strict["blockers"]
    assert strict["allowed_claims"] == []
    assert strict["remediation_spec"]["required_source"] == SOURCE_TUSHARE


def test_replay_supports_generic_p0_manifest_without_network(tmp_path: Path) -> None:
    layout = LakeLayout(tmp_path)
    params = {"target_dataset": DATASET_ADJ_FACTOR, "adjustment_policy": "qfq"}
    raw_path = layout.raw_batch_path(SOURCE_TUSHARE, INTERFACE_PRICES_ADJ_FACTOR, "2026-01-02", "b1")
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    raw_path.write_text(
        "\n".join(
            [
                json.dumps({"_metadata": {"run_id": "run-replay", "batch_id": "b1"}}, ensure_ascii=False),
                json.dumps({"ts_code": "000001.SZ", "trade_date": "20260102", "adj_factor": 1.0}, ensure_ascii=False),
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    checksum = hashlib.sha256(raw_path.read_bytes()).hexdigest()
    params_hash = compute_params_hash(params)
    manifest = {
        "schema_version": "1.0",
        "run_id": "run-replay",
        "batch_id": "b1",
        "idempotency_key": compute_idempotency_key(
            "run-replay",
            "b1",
            SOURCE_TUSHARE,
            INTERFACE_PRICES_ADJ_FACTOR,
            params_hash,
        ),
        "source": SOURCE_TUSHARE,
        "interface": INTERFACE_PRICES_ADJ_FACTOR,
        "params": params,
        "params_hash": params_hash,
        "requested_at": "2026-05-22T00:00:00+00:00",
        "started_at": "2026-05-22T00:00:00+00:00",
        "finished_at": "2026-05-22T00:00:00+00:00",
        "attempts": 1,
        "status": "success",
        "raw_path": str(raw_path.relative_to(tmp_path)),
        "raw_checksum": checksum,
        "raw_row_count": 1,
        "canonical_path": None,
        "error_type": None,
        "error_message": None,
        "retryable": None,
    }
    layout.manifest_path().parent.mkdir(parents=True, exist_ok=True)
    layout.manifest_path().write_text(json.dumps(manifest, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")

    payload = cmd_replay(
        argparse.Namespace(
            lake_root=tmp_path,
            dataset=DATASET_ADJ_FACTOR,
            start_date="2026-01-02",
            end_date="2026-01-02",
            index_code="399300.SZ",
            run_id="run-replay",
            batch_id="b1",
        )
    )

    assert payload["status"] == "ready_for_offline_replay"
    assert payload["network_calls"] == 0
    assert payload["writes"] == 0
    assert payload["auto_execute"] is False
    assert payload["raw_path"] == str(raw_path.relative_to(tmp_path))


def test_replay_matches_tushare_first_hs300_manifest_without_exact_params_hash(tmp_path: Path) -> None:
    layout = LakeLayout(tmp_path)
    params = {
        "target_dataset": DATASET_HS300_INDEX,
        "index_code": "399300.SZ",
        "benchmark_kind": "price_index",
        "start_date": "2026-01-02",
        "end_date": "2026-01-05",
        "explicit_real_execution": True,
        "offline": False,
    }
    raw_path = layout.raw_batch_path(SOURCE_TUSHARE, INTERFACE_HS300_INDEX_DAILY, "2026-01-02", "b1")
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    raw_path.write_text(
        "\n".join(
            [
                json.dumps({"_metadata": {"run_id": "run-hs300", "batch_id": "b1"}}, ensure_ascii=False),
                json.dumps({"ts_code": "399300.SZ", "trade_date": "20260102", "close": 4000.0, "pre_close": 3990.0}, ensure_ascii=False),
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    checksum = hashlib.sha256(raw_path.read_bytes()).hexdigest()
    params_hash = compute_params_hash(params)
    manifest = {
        "schema_version": "1.0",
        "run_id": "run-hs300",
        "batch_id": "b1",
        "idempotency_key": compute_idempotency_key(
            "run-hs300",
            "b1",
            SOURCE_TUSHARE,
            INTERFACE_HS300_INDEX_DAILY,
            params_hash,
        ),
        "source": SOURCE_TUSHARE,
        "interface": INTERFACE_HS300_INDEX_DAILY,
        "params": params,
        "params_hash": params_hash,
        "requested_at": "2026-05-22T00:00:00+00:00",
        "started_at": "2026-05-22T00:00:00+00:00",
        "finished_at": "2026-05-22T00:00:00+00:00",
        "attempts": 1,
        "status": "success",
        "raw_path": str(raw_path.relative_to(tmp_path)),
        "raw_checksum": checksum,
        "raw_row_count": 1,
        "canonical_path": None,
        "error_type": None,
        "error_message": None,
        "retryable": None,
    }
    layout.manifest_path().parent.mkdir(parents=True, exist_ok=True)
    layout.manifest_path().write_text(json.dumps(manifest, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")

    payload = cmd_replay(
        argparse.Namespace(
            lake_root=tmp_path,
            dataset=DATASET_HS300_INDEX,
            start_date="2026-01-02",
            end_date="2026-01-05",
            index_code="399300.SZ",
            run_id="run-hs300",
            batch_id="b1",
        )
    )

    assert payload["status"] == "skipped"
    assert payload["network_calls"] == 0
    assert payload["raw_path"] == str(raw_path.relative_to(tmp_path))


def test_tushare_first_p0_dataset_allowlist_covers_auxiliary_datasets(tmp_path: Path) -> None:
    cases = [
        (DATASET_ADJ_FACTOR, INTERFACE_PRICES_ADJ_FACTOR),
        (DATASET_INDEX_MEMBERS, INTERFACE_INDEX_MEMBERS_SNAPSHOT),
        (DATASET_INDEX_WEIGHTS, INTERFACE_INDEX_WEIGHTS_SNAPSHOT),
        (DATASET_STOCK_BASIC, INTERFACE_STOCK_BASIC_SNAPSHOT),
        (DATASET_TRADE_STATUS, INTERFACE_TRADE_STATUS_DAILY),
        (DATASET_PRICES_LIMIT, INTERFACE_PRICES_LIMIT_DAILY),
        (DATASET_EVENTS, INTERFACE_EVENTS_DISCLOSURE),
    ]
    for dataset, interface in cases:
        plan = build_tushare_first_plan(
            TushareFirstRunSpec(
                dataset=dataset,
                source_interface=interface,
                start_date="2026-01-02",
                end_date="2026-01-05",
                lake_root=str(tmp_path),
                symbol="000001.SZ",
                run_id=f"run-{dataset}",
            )
        )
        assert plan["dataset"] == dataset
        assert plan["interface"] == interface
        assert plan["params"]["target_dataset"] == dataset

    stock_basic = build_tushare_first_plan(
        TushareFirstRunSpec(
            dataset=DATASET_STOCK_BASIC,
            source_interface=INTERFACE_STOCK_BASIC_SNAPSHOT,
            start_date="2026-01-02",
            end_date="2026-01-05",
            lake_root=str(tmp_path),
            list_status="L",
            fields="ts_code,name,list_status,list_date,delist_date",
        )
    )
    assert stock_basic["params"]["snapshot_date"] == "2026-01-05"
    assert stock_basic["params"]["list_status"] == "L"
    assert stock_basic["params"]["fields"] == "ts_code,name,list_status,list_date,delist_date"


def test_reader_uses_catalog_current_run_directory_not_all_historical_canonical(tmp_path: Path) -> None:
    layout = LakeLayout(tmp_path)
    old_path = layout.canonical_dataset_root(DATASET_HS300_INDEX) / "run_id=run-old" / "part-b1.parquet"
    current_path = layout.canonical_dataset_root(DATASET_HS300_INDEX) / "run_id=run-current" / "part-b1.parquet"
    old_path.parent.mkdir(parents=True, exist_ok=True)
    current_path.parent.mkdir(parents=True, exist_ok=True)
    old = pd.DataFrame(
        {
            "trade_date": ["2026-01-02"],
            "index_code": ["399300.SZ"],
            "close": [3000.0],
            "source_run_id": ["run-old"],
        }
    )
    current = pd.DataFrame(
        {
            "trade_date": ["2026-01-02"],
            "index_code": ["399300.SZ"],
            "close": [4000.0],
            "source_run_id": ["run-current"],
        }
    )
    old.to_parquet(old_path, index=False)
    current.to_parquet(current_path, index=False)
    CatalogStore(layout).upsert(
        CatalogEntry(
            dataset=DATASET_HS300_INDEX,
            quality_status="pass",
            dataset_status="available",
            published=True,
            latest_manifest_run_id="run-current",
            canonical_path=str(current_path.parent.relative_to(tmp_path)),
            source_interface="hs300_index.daily",
        )
    )

    result = read_dataset(
        DATASET_HS300_INDEX,
        tmp_path,
        filters={
            "start": "2026-01-02",
            "end": "2026-01-02",
            "index_code": "399300.SZ",
        },
        required=True,
    )

    assert result.status == "available"
    assert result.frame is not None
    assert result.frame["close"].tolist() == [4000.0]
    assert result.frame["source_run_id"].tolist() == ["run-current"]
