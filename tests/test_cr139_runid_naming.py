from market_data.lake_layout import (
    build_cr139_run_id,
    legacy_run_id_path_detected,
    validate_cr139_run_id,
)
from market_data.normalization import validate_partition_naming_contract


def test_cr139_run_id_is_deterministic_and_valid():
    run_id = build_cr139_run_id(
        dataset="prices",
        source="tushare",
        as_of_date="2026-06-29",
        purpose="canonical",
    )

    assert run_id == "cr139-w2-prices-tushare-20260629-canonical"
    assert validate_cr139_run_id(run_id)


def test_legacy_run_id_partition_path_is_blocked_by_static_contract():
    status = validate_partition_naming_contract(
        run_id="cr139-w2-prices-tushare-20260629-canonical",
        target_path="/lake/canonical/prices/1.0/run_id=legacy/part.parquet",
    )

    assert legacy_run_id_path_detected("/lake/canonical/prices/1.0/run_id=legacy")
    assert status["status"] == "blocked"
    assert status["physical_migration_executed"] is False
    assert status["lake_write_count"] == 0
