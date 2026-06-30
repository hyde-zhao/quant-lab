import json

import pytest

from market_data.cli import (
    PricesLongHorizonPlanSpec,
    build_prices_long_horizon_plan,
    main,
)
from market_data.contracts import (
    DATASET_ADJ_FACTOR,
    DATASET_PRICES,
    INTERFACE_PRICES_ADJ_FACTOR,
    INTERFACE_PRICES_DAILY,
    SOURCE_TUSHARE,
)
from market_data.normalization import ADJUSTMENT_POLICY_CONFLICT
from market_data.runtime import ResumePolicy, resume_policy_to_dict
from market_data.validation import (
    DENOMINATOR_MODE_PRICES,
    DENOMINATOR_MODE_TRADE_CALENDAR_REQUIRED,
    build_prices_coverage_gate,
)


def run_cli(capsys, *args):
    code = main(list(args))
    captured = capsys.readouterr()
    stdout = json.loads(captured.out) if captured.out else {}
    stderr = json.loads(captured.err) if captured.err else {}
    return code, stdout, stderr


def base_spec(tmp_path, **overrides):
    values = {
        "lake_root": str(tmp_path),
        "start_date": "2026-01-01",
        "end_date": "2026-01-05",
        "symbols": ("000001.SZ", "000002.SZ"),
        "symbol_batch_size": 1,
        "slice_days": 3,
        "run_id": "run-cr007-s01",
    }
    values.update(overrides)
    return PricesLongHorizonPlanSpec(**values)


def test_plan_outputs_required_fields_and_no_side_effects(tmp_path):
    plan = build_prices_long_horizon_plan(base_spec(tmp_path))

    for field in (
        "dataset",
        "source",
        "interfaces",
        "start_date",
        "end_date",
        "symbols_or_universe",
        "batch_count",
        "date_slices",
        "run_id",
        "resume_policy",
        "target_paths",
        "coverage_gate",
    ):
        assert field in plan
    assert plan["dataset"] == DATASET_PRICES
    assert plan["source"] == SOURCE_TUSHARE
    assert {item["interface"] for item in plan["interfaces"]} == {
        INTERFACE_PRICES_DAILY,
        INTERFACE_PRICES_ADJ_FACTOR,
    }
    assert plan["network_calls"] == 0
    assert plan["writes"] == 0
    assert plan["dry_run"] is True
    assert plan["target_paths"]["lake_root"] == "<configured-lake-root>"
    assert plan["old_data_operations"] == {
        "read": 0,
        "list": 0,
        "migrate": 0,
        "copy": 0,
        "compare": 0,
        "delete": 0,
    }
    assert not list(tmp_path.rglob("*"))


def test_missing_universe_fails_fast(capsys, tmp_path):
    code, payload, stderr = run_cli(
        capsys,
        "prices-long-horizon-plan",
        "--lake-root",
        str(tmp_path),
        "--start-date",
        "2026-01-01",
        "--end-date",
        "2026-01-05",
    )

    assert code == 2
    assert payload == {}
    assert stderr["error_type"] == "universe_missing"
    assert not list(tmp_path.rglob("*"))


def test_symbol_and_date_batches_are_paired(tmp_path):
    plan = build_prices_long_horizon_plan(
        base_spec(
            tmp_path,
            symbols=("000001.SZ", "000002.SZ", "000003.SZ"),
            symbol_batch_size=2,
            slice_days=3,
        )
    )

    assert len(plan["date_slices"]) == 2
    assert plan["symbols_or_universe"]["symbol_batch_count"] == 2
    assert plan["batch_count"] == 8
    grouped = {}
    for request in plan["planned_connector_requests"]:
        key = (request["date_slice"]["slice_id"], tuple(request["symbols"]))
        grouped.setdefault(key, set()).add(request["interface"])
    assert grouped
    assert all(
        interfaces == {INTERFACE_PRICES_DAILY, INTERFACE_PRICES_ADJ_FACTOR}
        for interfaces in grouped.values()
    )
    assert {request["target_dataset"] for request in plan["planned_connector_requests"]} == {
        DATASET_PRICES,
        DATASET_ADJ_FACTOR,
    }


def test_universe_source_is_recorded_without_default_full_market(tmp_path):
    plan = build_prices_long_horizon_plan(
        base_spec(tmp_path, symbols=(), universe_source="cr007-s03-readiness")
    )

    assert plan["symbols_or_universe"]["symbols"] == []
    assert plan["symbols_or_universe"]["universe_source"] == "cr007-s03-readiness"
    assert plan["symbols_or_universe"]["symbols_resolved"] is False
    assert plan["batch_count"] == len(plan["date_slices"]) * 2
    for request in plan["planned_connector_requests"]:
        assert request["universe_source"] == "cr007-s03-readiness"
        assert request["symbols_resolved"] is False
        assert "ts_code" not in request["params"]
        assert "symbol" not in request["params"]


def test_resume_policy_matches_runtime_default(tmp_path):
    plan = build_prices_long_horizon_plan(base_spec(tmp_path))
    assert plan["resume_policy"] == resume_policy_to_dict(ResumePolicy())
    assert plan["resume_policy"] == {
        "success": "skip",
        "failed": "retry",
        "partial_success": "retry",
        "duplicate_manifest": "fail",
    }


def test_coverage_gate_requires_trade_calendar_denominator(tmp_path):
    plan = build_prices_long_horizon_plan(base_spec(tmp_path))
    gate = plan["coverage_gate"]

    assert gate["denominator_mode"] == DENOMINATOR_MODE_TRADE_CALENDAR_REQUIRED
    assert gate["coverage_denominator_status"] == "trade_calendar_required"
    assert gate["requires_trade_calendar"] is True
    assert gate["coverage_pass_claimed"] is False


def test_coverage_gate_uses_open_trade_dates_when_provided():
    gate = build_prices_coverage_gate(
        start_date="2026-01-01",
        end_date="2026-01-05",
        symbols_count=2,
        date_slices=[{"start_date": "2026-01-01", "end_date": "2026-01-05"}],
        open_trade_dates=["2026-01-02", "2026-01-05"],
    )

    assert gate["denominator_mode"] == DENOMINATOR_MODE_PRICES
    assert gate["coverage_denominator_status"] == "ready"
    assert gate["open_trade_dates_count"] == 2
    assert gate["expected_rows"] == 4
    assert gate["requires_trade_calendar"] is False


def test_adjustment_policy_conflict_is_exported_for_fail_fast_contract():
    assert ADJUSTMENT_POLICY_CONFLICT == "adjustment_policy_conflict"


def test_no_credentials_or_old_data_are_read_or_printed(tmp_path, monkeypatch):
    monkeypatch.setenv("TUSHARE_TOKEN", "secret-token-value")
    plan = build_prices_long_horizon_plan(base_spec(tmp_path))
    serialized = json.dumps(plan, ensure_ascii=False, sort_keys=True)

    assert "secret-token-value" not in serialized
    assert str(tmp_path) not in serialized
    assert "reports/data_quality_report.csv" not in serialized
    assert plan["old_quality_report_operations"] == {"read": 0, "open": 0, "overwrite": 0}
    assert plan["old_data_operations"]["read"] == 0


def test_tushare_adapter_not_invoked_by_dry_run(tmp_path, monkeypatch):
    def fail_fetch(*args, **kwargs):
        raise AssertionError("dry-run planner must not call TushareAdapter.fetch")

    monkeypatch.setattr("market_data.connectors.tushare.TushareAdapter.fetch", fail_fetch)

    plan = build_prices_long_horizon_plan(base_spec(tmp_path))

    assert plan["network_calls"] == 0
    assert plan["writes"] == 0


def test_real_execution_gate_remains_closed(capsys, tmp_path):
    code, payload, stderr = run_cli(
        capsys,
        "prices-long-horizon-plan",
        "--lake-root",
        str(tmp_path),
        "--start-date",
        "2026-01-01",
        "--end-date",
        "2026-01-05",
        "--symbols",
        "000001.SZ",
        "--dry-run",
        "false",
    )

    assert code == 2
    assert payload == {}
    assert stderr["error_type"] == "source_disabled"
    assert not list(tmp_path.rglob("*"))
