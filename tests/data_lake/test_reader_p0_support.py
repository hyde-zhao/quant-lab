from __future__ import annotations

from pathlib import Path

import pandas as pd

from market_data.catalog import CatalogEntry, CatalogStore
from market_data.contracts import (
    DATASET_INDUSTRY_CLASSIFICATION,
    DATASET_LIQUIDITY_CAPACITY,
    DATASET_MARKET_CAP,
    DATASET_PRICES_LIMIT_CODE_CHANGE_FIXES,
    DATASET_PRICES_LIMIT_COVERAGE_EXCLUSIONS,
    DATASET_SCHEMA_REGISTRY,
    QUALITY_STATUS_PASS,
    READINESS_STATUS_AVAILABLE,
    SCHEMA_VERSION,
)
from market_data.lake_layout import LakeLayout
from market_data.readers import QualityPolicy, read_dataset


def test_w3_p0_reader_contract_registers_liquidity_and_market_cap() -> None:
    assert DATASET_LIQUIDITY_CAPACITY in DATASET_SCHEMA_REGISTRY
    assert DATASET_MARKET_CAP in DATASET_SCHEMA_REGISTRY
    assert DATASET_SCHEMA_REGISTRY[DATASET_LIQUIDITY_CAPACITY]["key_columns"] == (
        "trade_date",
        "symbol",
    )
    assert DATASET_SCHEMA_REGISTRY[DATASET_MARKET_CAP]["key_columns"] == (
        "trade_date",
        "symbol",
    )


def test_w3_p1_reader_contract_registers_supported_auxiliary_datasets() -> None:
    assert DATASET_SCHEMA_REGISTRY[DATASET_INDUSTRY_CLASSIFICATION]["key_columns"] == (
        "symbol",
        "classification_standard",
        "effective_date",
    )
    assert DATASET_SCHEMA_REGISTRY[DATASET_PRICES_LIMIT_CODE_CHANGE_FIXES]["key_columns"] == (
        "trade_date",
        "symbol",
        "source_symbol",
        "mapping_type",
    )
    assert DATASET_SCHEMA_REGISTRY[DATASET_PRICES_LIMIT_COVERAGE_EXCLUSIONS]["key_columns"] == (
        "trade_date",
        "symbol",
        "exclusion_reason",
    )


def test_w3_p0_read_dataset_supports_liquidity_capacity(tmp_path: Path) -> None:
    frame = pd.DataFrame(
        {
            "trade_date": ["20260102"],
            "symbol": ["000001.SZ"],
            "volume": [1000.0],
            "amount": [120000.0],
            "amount_unit": ["CNY"],
            "adv20_amount": [110000.0],
            "adv20_volume": [900.0],
            "turnover_rate": [1.2],
            "turnover_rate_f": [1.1],
            "source": ["fixture"],
            "source_interface": ["liquidity_capacity.daily"],
            "source_run_id": ["run-cr139-w3-fixture"],
            "available_at": ["2026-01-03T00:00:00+08:00"],
            "available_at_rule": ["next_day"],
            "schema_version": [SCHEMA_VERSION],
            "lineage_raw_checksum": ["checksum-liquidity"],
        }
    )
    _write_cataloged_parquet(
        tmp_path,
        dataset=DATASET_LIQUIDITY_CAPACITY,
        frame=frame,
        source_interface="liquidity_capacity.daily",
    )

    result = read_dataset(DATASET_LIQUIDITY_CAPACITY, tmp_path)

    assert result.status == "available"
    assert result.issues == []
    assert result.frame is not None
    assert len(result.frame) == 1
    assert result.frame.iloc[0]["symbol"] == "000001.SZ"


def test_w3_p0_read_dataset_supports_market_cap(tmp_path: Path) -> None:
    frame = pd.DataFrame(
        {
            "trade_date": ["20260102"],
            "symbol": ["000001.SZ"],
            "market_cap": [100000000.0],
            "float_market_cap": [80000000.0],
            "turnover_rate": [1.2],
            "turnover_rate_f": [1.1],
            "volume_ratio": [0.8],
            "pe": [10.0],
            "pe_ttm": [11.0],
            "pb": [1.5],
            "ps": [2.0],
            "ps_ttm": [2.1],
            "dv_ratio": [0.5],
            "dv_ttm": [0.6],
            "total_share": [1000000.0],
            "float_share": [800000.0],
            "free_share": [700000.0],
            "market_cap_unit": ["CNY"],
            "source": ["fixture"],
            "source_interface": ["market_cap.daily"],
            "source_run_id": ["run-cr139-w3-fixture"],
            "available_at": ["2026-01-03T00:00:00+08:00"],
            "available_at_rule": ["next_day"],
            "schema_version": [SCHEMA_VERSION],
            "lineage_raw_checksum": ["checksum-market-cap"],
        }
    )
    _write_cataloged_parquet(
        tmp_path,
        dataset=DATASET_MARKET_CAP,
        frame=frame,
        source_interface="market_cap.daily",
    )

    result = read_dataset(DATASET_MARKET_CAP, tmp_path)

    assert result.status == "available"
    assert result.issues == []
    assert result.frame is not None
    assert len(result.frame) == 1
    assert result.frame.iloc[0]["market_cap"] == 100000000.0


def test_w3_p1_read_dataset_supports_industry_classification(tmp_path: Path) -> None:
    frame = pd.DataFrame(
        {
            "symbol": ["000001.SZ"],
            "industry_code": ["801010"],
            "industry_name": ["fixture-industry"],
            "classification_standard": ["sw"],
            "effective_date": ["20260102"],
            "available_date": ["20260103"],
            "available_at": ["2026-01-03T00:00:00+08:00"],
            "available_at_rule": ["next_day"],
            "pit_status": ["pit_available"],
            "readiness_status": ["available"],
            "source": ["fixture"],
            "source_interface": ["industry_classification.snapshot"],
            "source_run_id": ["run-cr139-w3-fixture"],
            "schema_version": [SCHEMA_VERSION],
            "lineage_raw_checksum": ["checksum-industry"],
        }
    )
    _write_cataloged_parquet(
        tmp_path,
        dataset=DATASET_INDUSTRY_CLASSIFICATION,
        frame=frame,
        source_interface="industry_classification.snapshot",
    )

    result = read_dataset(DATASET_INDUSTRY_CLASSIFICATION, tmp_path)

    assert result.status == "available"
    assert result.frame is not None
    assert result.frame.iloc[0]["industry_code"] == "801010"


def test_w3_p1_industry_classification_non_pit_snapshot_is_conditional_reader_support(
    tmp_path: Path,
) -> None:
    frame = pd.DataFrame(
        {
            "symbol": ["000001.SZ"],
            "industry_code": ["801010"],
            "industry_name": ["fixture-industry"],
            "classification_standard": ["sw"],
            "effective_date": ["20260102"],
            "available_date": ["20260103"],
            "available_at": ["2026-01-03T00:00:00+08:00"],
            "available_at_rule": ["next_day"],
            "pit_status": ["non_pit_snapshot"],
            "readiness_status": ["non_pit_snapshot"],
            "source": ["fixture"],
            "source_interface": ["industry_classification.snapshot"],
            "source_run_id": ["run-cr139-w3-fixture"],
            "schema_version": [SCHEMA_VERSION],
            "lineage_raw_checksum": ["checksum-industry"],
        }
    )
    _write_cataloged_parquet(
        tmp_path,
        dataset=DATASET_INDUSTRY_CLASSIFICATION,
        frame=frame,
        source_interface="industry_classification.snapshot",
        known_limitations=[
            {"code": "non_pit_snapshot", "reason": "fixture industry snapshot"}
        ],
    )

    blocked = read_dataset(DATASET_INDUSTRY_CLASSIFICATION, tmp_path)
    allowed = read_dataset(
        DATASET_INDUSTRY_CLASSIFICATION,
        tmp_path,
        quality_policy=QualityPolicy(allow_warn=True),
    )

    assert blocked.status == "unavailable"
    assert {issue["code"] for issue in blocked.issues} >= {
        "readiness_not_available",
        "non_pit_snapshot",
    }
    assert allowed.status == "available"
    assert allowed.frame is not None
    assert len(allowed.frame) == 1
    assert {issue["code"] for issue in allowed.issues} >= {
        "readiness_not_available",
        "non_pit_snapshot",
    }


def test_w3_p1_read_dataset_supports_prices_limit_code_change_fixes(tmp_path: Path) -> None:
    frame = pd.DataFrame(
        {
            "trade_date": ["20260102"],
            "symbol": ["000001.SZ"],
            "source_symbol": ["000001"],
            "limit_up": [11.0],
            "limit_down": [9.0],
            "mapping_type": ["code_change"],
            "mapping_effective_date": ["20260101"],
            "reason": ["fixture"],
            "source": ["fixture"],
            "source_interface": ["cr018_price_limit_lifecycle_cleanup"],
            "source_run_id": ["run-cr139-w3-fixture"],
            "schema_version": [SCHEMA_VERSION],
            "lineage_raw_checksum": ["checksum-fixes"],
        }
    )
    _write_cataloged_parquet(
        tmp_path,
        dataset=DATASET_PRICES_LIMIT_CODE_CHANGE_FIXES,
        frame=frame,
        source_interface="cr018_price_limit_lifecycle_cleanup",
    )

    result = read_dataset(DATASET_PRICES_LIMIT_CODE_CHANGE_FIXES, tmp_path)

    assert result.status == "available"
    assert result.frame is not None
    assert result.frame.iloc[0]["mapping_type"] == "code_change"


def test_w3_p1_read_dataset_supports_prices_limit_coverage_exclusions(tmp_path: Path) -> None:
    frame = pd.DataFrame(
        {
            "trade_date": ["20260102"],
            "symbol": ["000001.SZ"],
            "exclusion_reason": ["fixture"],
            "reference_date": ["20260101"],
            "reference_symbol": ["000001"],
            "source": ["fixture"],
            "source_interface": ["cr018_price_limit_lifecycle_cleanup"],
            "source_run_id": ["run-cr139-w3-fixture"],
            "schema_version": [SCHEMA_VERSION],
            "lineage_raw_checksum": ["checksum-exclusions"],
        }
    )
    _write_cataloged_parquet(
        tmp_path,
        dataset=DATASET_PRICES_LIMIT_COVERAGE_EXCLUSIONS,
        frame=frame,
        source_interface="cr018_price_limit_lifecycle_cleanup",
    )

    result = read_dataset(DATASET_PRICES_LIMIT_COVERAGE_EXCLUSIONS, tmp_path)

    assert result.status == "available"
    assert result.frame is not None
    assert result.frame.iloc[0]["exclusion_reason"] == "fixture"


def _write_cataloged_parquet(
    lake: Path,
    *,
    dataset: str,
    frame: pd.DataFrame,
    source_interface: str,
    known_limitations: list[dict[str, str]] | None = None,
) -> Path:
    layout = LakeLayout(lake)
    run_id = "run-cr139-w3-fixture"
    root = layout.canonical_dataset_root(dataset) / f"run_id={run_id}"
    root.mkdir(parents=True, exist_ok=True)
    path = root / "part.parquet"
    frame.to_parquet(path, index=False)
    CatalogStore(layout).upsert(
        CatalogEntry(
            dataset=dataset,
            schema_version=SCHEMA_VERSION,
            start_date="20260102",
            end_date="20260102",
            coverage={"rows": len(frame)},
            quality_status=QUALITY_STATUS_PASS,
            dataset_status="available",
            latest_manifest_run_id=run_id,
            source="fixture",
            source_interface=source_interface,
            canonical_path=str(root.relative_to(lake)),
            published=True,
            published_at="2026-06-30T00:00:00+08:00",
            readiness_status=READINESS_STATUS_AVAILABLE,
            known_limitations=known_limitations or [],
            coverage_denominator=len(frame),
            coverage_ratio=1.0,
            coverage_start="20260102",
            coverage_end="20260102",
            lineage_checksum=f"lineage-{dataset}",
            universe_scope="fixture",
            as_of_trade_date="20260102",
        )
    )
    return path
