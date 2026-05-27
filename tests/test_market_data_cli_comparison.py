import csv
import hashlib
import json
from pathlib import Path

import pandas as pd
import pytest

from market_data.cli import build_parser, main
from market_data.comparison import COMPARISON_FIELDS, compare_sources, load_comparison_frame
from market_data.contracts import DATASET_HS300_INDEX, INTERFACE_HS300_INDEX_DAILY, SOURCE_TUSHARE
from market_data.lake_layout import LakeLayout
from market_data.storage import compute_idempotency_key, compute_params_hash


def run_cli(capsys, *args):
    code = main(list(args))
    captured = capsys.readouterr()
    stdout = json.loads(captured.out) if captured.out else {}
    stderr = json.loads(captured.err) if captured.err else {}
    return code, stdout, stderr


def write_hs300_raw_manifest(lake_root: Path) -> LakeLayout:
    layout = LakeLayout(lake_root)
    params = {"target_dataset": DATASET_HS300_INDEX, "index_code": "399300.SZ"}
    raw_path = layout.raw_batch_path(SOURCE_TUSHARE, INTERFACE_HS300_INDEX_DAILY, "2026-01-02", "b1")
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    rows = [
        {
            "ts_code": "399300.SZ",
            "trade_date": "20260102",
            "open": 3991.0,
            "high": 4010.0,
            "low": 3980.0,
            "close": 4000.0,
            "pre_close": 3990.0,
            "pct_chg": 0.25,
            "vol": 100.0,
            "amount": 200.0,
        },
        {
            "ts_code": "399300.SZ",
            "trade_date": "20260105",
            "open": 4001.0,
            "high": 4020.0,
            "low": 3990.0,
            "close": 4010.0,
            "pre_close": 4000.0,
            "pct_chg": 0.25,
            "vol": 120.0,
            "amount": 240.0,
        },
    ]
    payload = [
        {
            "_metadata": {
                "run_id": "run-hs300-cli",
                "batch_id": "b1",
                "source": SOURCE_TUSHARE,
                "interface": INTERFACE_HS300_INDEX_DAILY,
                "params": params,
                "row_count": len(rows),
            }
        },
        *rows,
    ]
    raw_path.write_text(
        "\n".join(json.dumps(item, ensure_ascii=False, sort_keys=True) for item in payload)
        + "\n",
        encoding="utf-8",
    )
    checksum = hashlib.sha256(raw_path.read_bytes()).hexdigest()
    params_hash = compute_params_hash(params)
    record = {
        "schema_version": "1.0",
        "run_id": "run-hs300-cli",
        "batch_id": "b1",
        "idempotency_key": compute_idempotency_key(
            "run-hs300-cli",
            "b1",
            SOURCE_TUSHARE,
            INTERFACE_HS300_INDEX_DAILY,
            params_hash,
        ),
        "source": SOURCE_TUSHARE,
        "interface": INTERFACE_HS300_INDEX_DAILY,
        "params": params,
        "params_hash": params_hash,
        "requested_at": "2026-05-18T00:00:00+00:00",
        "started_at": "2026-05-18T00:00:00+00:00",
        "finished_at": "2026-05-18T00:00:00+00:00",
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
    layout.manifest_path().parent.mkdir(parents=True, exist_ok=True)
    layout.manifest_path().write_text(
        json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return layout


def write_hs300_canonical(lake_root: Path, run_id: str, rows: list[dict]) -> Path:
    path = LakeLayout(lake_root).canonical_dataset_root(DATASET_HS300_INDEX) / f"run_id={run_id}" / "part.parquet"
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_parquet(path, index=False)
    return path


def hs300_canonical_rows(run_id: str, close: float = 4000.0) -> list[dict]:
    return [
        {
            "trade_date": "2026-01-02",
            "index_code": "399300.SZ",
            "close": close,
            "pre_close": close - 10,
            "pct_chg": 0.25,
            "open": close - 9,
            "high": close + 10,
            "low": close - 20,
            "volume": 100.0,
            "amount": 200.0,
            "benchmark_kind": "price_index",
            "source": SOURCE_TUSHARE,
            "source_interface": INTERFACE_HS300_INDEX_DAILY,
            "source_run_id": run_id,
            "schema_version": "1.0",
            "available_at": "2026-01-02T16:00:00+08:00",
            "available_at_rule": "daily_close_fact",
            "lineage_raw_checksum": f"checksum-{run_id}",
        }
    ]


def write_hs300_success_manifest_for_replay(lake_root: Path) -> None:
    layout = LakeLayout(lake_root)
    params = {
        "target_dataset": DATASET_HS300_INDEX,
        "index_code": "399300.SZ",
        "start_date": "2026-01-02",
        "end_date": "2026-01-02",
        "explicit_real_execution": True,
        "offline": False,
    }
    raw_path = layout.raw_batch_path(
        SOURCE_TUSHARE,
        INTERFACE_HS300_INDEX_DAILY,
        "2026-01-02",
        "b-replay",
    )
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    raw_rows = [
        {"_metadata": {"run_id": "run-replay", "batch_id": "b-replay"}},
        {"ts_code": "399300.SZ", "trade_date": "20260102", "close": 4000.0},
    ]
    raw_path.write_text(
        "\n".join(json.dumps(item, ensure_ascii=False, sort_keys=True) for item in raw_rows)
        + "\n",
        encoding="utf-8",
    )
    checksum = hashlib.sha256(raw_path.read_bytes()).hexdigest()
    params_hash = compute_params_hash(params)
    record = {
        "schema_version": "1.0",
        "run_id": "run-replay",
        "batch_id": "b-replay",
        "idempotency_key": compute_idempotency_key(
            "run-replay",
            "b-replay",
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
        "raw_path": str(raw_path.relative_to(lake_root)),
        "raw_checksum": checksum,
        "raw_row_count": 1,
        "canonical_path": None,
        "error_type": None,
        "error_message": None,
        "retryable": None,
    }
    layout.manifest_path().parent.mkdir(parents=True, exist_ok=True)
    layout.manifest_path().write_text(
        json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def common_args(tmp_path):
    return (
        "--lake-root",
        str(tmp_path),
        "--dataset",
        "prices",
        "--symbols",
        "000001.SZ,000002.SZ",
        "--start-date",
        "2026-01-02",
        "--end-date",
        "2026-01-03",
    )


def test_plan_does_not_write_or_fetch(tmp_path, capsys):
    before = list(tmp_path.rglob("*"))
    code, payload, stderr = run_cli(capsys, "plan", *common_args(tmp_path))

    assert code == 0
    assert stderr == {}
    assert payload["command"] == "plan"
    assert payload["offline"] is True
    assert payload["source"] == "fake"
    assert payload["batch_count"] == 1
    assert list(tmp_path.rglob("*")) == before


def test_cli_offline_smoke_and_quality_shape(tmp_path, capsys, monkeypatch):
    def deny_connect(*args, **kwargs):
        raise AssertionError("network must not be used")

    monkeypatch.setattr("socket.socket.connect", deny_connect)

    assert run_cli(
        capsys,
        "fetch",
        *common_args(tmp_path),
        "--run-id",
        "run-cli",
        "--batch-id",
        "b1",
    )[0] == 0

    code, norm, _ = run_cli(capsys, "normalize", "--lake-root", str(tmp_path), "--dataset", "prices")
    assert code == 0
    assert norm["row_count"] == 4
    canonical_path = Path(norm["canonical_paths"][0])
    assert canonical_path.exists()

    code, quality, _ = run_cli(
        capsys,
        "validate",
        "--lake-root",
        str(tmp_path),
        "--dataset",
        "prices",
        "--symbols",
        "000001.SZ,000002.SZ",
        "--start-date",
        "2026-01-02",
        "--end-date",
        "2026-01-03",
        "--open-trade-dates",
        "2026-01-02,2026-01-03",
    )
    assert code == 0
    assert quality["quality_status"] in {"pass", "warn"}
    assert quality["fetch_status"] == "success"
    assert quality["dataset_status"] in {"pass", "warn"}
    assert quality["denominator_mode"] == "open_trade_dates_in_requested_range_x_target_symbols"
    assert "thresholds_json" in quality["quality_csv_fields"]

    quality_csv = Path(quality["quality_csv_path"])
    quality_md = Path(quality["quality_markdown_path"])
    row = next(csv.DictReader(quality_csv.open("r", encoding="utf-8")))
    for field in (
        "run_id",
        "generated_at",
        "source_name",
        "source_interface",
        "target_dataset",
        "input_config_hash",
        "fetch_status",
        "dataset_status",
        "quality_status",
        "requested_start",
        "requested_end",
        "expected_rows",
        "actual_rows",
        "missing_rows",
        "missing_rate",
        "denominator_mode",
        "thresholds_json",
        "warnings_json",
        "is_pit_universe",
        "universe_mode",
        "pit_status",
        "survivorship_bias_note",
    ):
        assert field in row
    for name in row:
        if name.endswith("_json"):
            json.loads(row[name])
    assert "Markdown 仅供人工阅读" in quality_md.read_text(encoding="utf-8")

    code, natural_day_quality, _ = run_cli(
        capsys,
        "validate",
        "--lake-root",
        str(tmp_path),
        "--dataset",
        "prices",
        "--symbols",
        "000001.SZ,000002.SZ",
        "--start-date",
        "2026-01-02",
        "--end-date",
        "2026-01-03",
    )
    assert code == 0
    natural_day_row = next(
        csv.DictReader(Path(natural_day_quality["quality_csv_path"]).open("r", encoding="utf-8"))
    )
    natural_day_warnings = json.loads(natural_day_row["warnings_json"])
    assert "open_trade_dates 未显式传入，使用自然日范围计算 coverage" in natural_day_warnings
    code, published, stderr = run_cli(
        capsys,
        "publish",
        "--lake-root",
        str(tmp_path),
        "--dataset",
        "prices",
        "--allow-warn",
    )
    assert code == 0
    assert stderr == {}
    assert published["publish_status"] == "published"

    before = {path: path.stat().st_mtime_ns for path in tmp_path.rglob("*") if path.is_file()}
    code, read_payload, _ = run_cli(
        capsys,
        "read",
        "--lake-root",
        str(tmp_path),
        "--dataset",
        "prices",
        "--symbols",
        "000001.SZ",
        "--columns",
        "trade_date,symbol,close",
        "--allow-warn",
    )
    after = {path: path.stat().st_mtime_ns for path in tmp_path.rglob("*") if path.is_file()}
    assert code == 0
    assert read_payload["row_count"] == 2
    assert read_payload["columns"] == ["trade_date", "symbol", "close"]
    assert before == after

    code, comparison, _ = run_cli(
        capsys,
        "compare",
        "--lake-root",
        str(tmp_path),
        "--dataset",
        "prices",
        "--keys",
        "trade_date,symbol",
        "--fields",
        "close",
        "--tolerance",
        "0.0",
    )
    assert code == 0
    assert comparison["comparison_mode"] == "fake_reference"
    assert comparison["status_counts"] == {"match": 4}
    assert set(COMPARISON_FIELDS) <= set(comparison["comparison_rows"][0])

    assert not list((tmp_path.parent / "data").glob("market_data/**/*"))


def test_hs300_index_cli_normalize_validate_and_read(tmp_path, capsys):
    write_hs300_raw_manifest(tmp_path)

    code, norm, stderr = run_cli(
        capsys,
        "normalize",
        "--lake-root",
        str(tmp_path),
        "--dataset",
        DATASET_HS300_INDEX,
        "--run-id",
        "run-hs300-cli",
    )
    assert code == 0
    assert stderr == {}
    assert norm["dataset"] == DATASET_HS300_INDEX
    assert norm["row_count"] == 2

    code, quality, stderr = run_cli(
        capsys,
        "validate",
        "--lake-root",
        str(tmp_path),
        "--dataset",
        DATASET_HS300_INDEX,
        "--index-code",
        "399300.SZ",
        "--start-date",
        "2026-01-02",
        "--end-date",
        "2026-01-05",
        "--open-trade-dates",
        "2026-01-02,2026-01-05",
    )
    assert code == 0
    assert stderr == {}
    assert quality["quality_status"] == "pass"
    assert quality["dataset_status"] == "available"
    assert quality["denominator_mode"] == "trade_calendar_open_dates"
    code, published, stderr = run_cli(
        capsys,
        "publish",
        "--lake-root",
        str(tmp_path),
        "--dataset",
        DATASET_HS300_INDEX,
    )
    assert code == 0
    assert stderr == {}
    assert published["publish_status"] == "published"

    code, read_payload, stderr = run_cli(
        capsys,
        "read",
        "--lake-root",
        str(tmp_path),
        "--dataset",
        DATASET_HS300_INDEX,
        "--index-code",
        "399300.SZ",
        "--start-date",
        "2026-01-02",
        "--end-date",
        "2026-01-05",
        "--columns",
        "trade_date,index_code,close",
    )
    assert code == 0
    assert stderr == {}
    assert read_payload["row_count"] == 2
    assert read_payload["columns"] == ["trade_date", "index_code", "close"]


def test_hs300_validate_revalidate_run_id_scope_and_replay_idempotency(tmp_path, capsys, monkeypatch):
    def deny_connect(*args, **kwargs):
        raise AssertionError("network must not be used")

    monkeypatch.setattr("socket.socket.connect", deny_connect)

    write_hs300_canonical(tmp_path, "run-old", hs300_canonical_rows("run-old", close=3990.0))
    write_hs300_canonical(tmp_path, "run-target", hs300_canonical_rows("run-target", close=4000.0))

    validate_args = (
        "--lake-root",
        str(tmp_path),
        "--dataset",
        DATASET_HS300_INDEX,
        "--index-code",
        "399300.SZ",
        "--start-date",
        "2026-01-02",
        "--end-date",
        "2026-01-02",
        "--run-id",
        "run-target",
        "--open-trade-dates",
        "2026-01-02",
    )
    code, quality, stderr = run_cli(capsys, "validate", *validate_args)
    assert code == 0
    assert stderr == {}
    assert quality["quality_status"] == "pass"
    assert quality["dataset_status"] == "available"
    assert quality["coverage"]["actual_rows"] == 1

    code, revalidated, stderr = run_cli(capsys, "revalidate", *validate_args)
    assert code == 0
    assert stderr == {}
    assert revalidated["command"] == "revalidate"
    assert revalidated["quality_status"] == "pass"
    assert revalidated["network_calls"] == 0
    assert revalidated["canonical_writes"] == 0

    write_hs300_success_manifest_for_replay(tmp_path)
    before = sorted(path.relative_to(tmp_path) for path in tmp_path.rglob("*") if path.is_file())
    monkeypatch.setenv("MARKET_DATA_LAKE_ROOT", str(tmp_path / "ignored-env-lake"))
    code, replay, stderr = run_cli(
        capsys,
        "replay",
        "--lake-root",
        str(tmp_path),
        "--dataset",
        DATASET_HS300_INDEX,
        "--index-code",
        "399300.SZ",
        "--start-date",
        "2026-01-02",
        "--end-date",
        "2026-01-02",
        "--run-id",
        "run-replay",
        "--batch-id",
        "b-replay",
    )
    after = sorted(path.relative_to(tmp_path) for path in tmp_path.rglob("*") if path.is_file())
    assert code == 0
    assert stderr == {}
    assert replay["status"] == "skipped"
    assert replay["attempts"] == 0
    assert replay["network_calls"] == 0
    assert replay["writes"] == 0
    assert before == after


def test_replay_uses_market_data_lake_root_env_fallback(tmp_path, capsys, monkeypatch):
    def deny_connect(*args, **kwargs):
        raise AssertionError("network must not be used")

    monkeypatch.setattr("socket.socket.connect", deny_connect)
    monkeypatch.setenv("MARKET_DATA_LAKE_ROOT", str(tmp_path))
    write_hs300_success_manifest_for_replay(tmp_path)

    before = sorted(path.relative_to(tmp_path) for path in tmp_path.rglob("*") if path.is_file())
    code, replay, stderr = run_cli(
        capsys,
        "replay",
        "--dataset",
        DATASET_HS300_INDEX,
        "--index-code",
        "399300.SZ",
        "--start-date",
        "2026-01-02",
        "--end-date",
        "2026-01-02",
        "--run-id",
        "run-replay",
        "--batch-id",
        "b-replay",
    )
    after = sorted(path.relative_to(tmp_path) for path in tmp_path.rglob("*") if path.is_file())

    assert code == 0
    assert stderr == {}
    assert replay["status"] == "skipped"
    assert replay["attempts"] == 0
    assert replay["network_calls"] == 0
    assert replay["writes"] == 0
    assert before == after


def test_replay_missing_manifest_still_fails_with_env_lake_root(tmp_path, capsys, monkeypatch):
    def deny_connect(*args, **kwargs):
        raise AssertionError("network must not be used")

    monkeypatch.setattr("socket.socket.connect", deny_connect)
    monkeypatch.setenv("MARKET_DATA_LAKE_ROOT", str(tmp_path))

    before = sorted(path.relative_to(tmp_path) for path in tmp_path.rglob("*") if path.is_file())
    code, payload, stderr = run_cli(
        capsys,
        "replay",
        "--dataset",
        DATASET_HS300_INDEX,
        "--index-code",
        "399300.SZ",
        "--start-date",
        "2026-01-02",
        "--end-date",
        "2026-01-02",
        "--run-id",
        "run-replay-missing",
        "--batch-id",
        "b-replay-missing",
    )
    after = sorted(path.relative_to(tmp_path) for path in tmp_path.rglob("*") if path.is_file())

    assert code == 2
    assert payload == {}
    assert stderr["error_type"] == "replay_missing"
    assert before == after


def test_market_data_cli_help_includes_replay_and_revalidate():
    help_text = build_parser().format_help()
    assert "replay" in help_text
    assert "revalidate" in help_text


def test_real_sources_fail_fast_without_network_or_writes(tmp_path, capsys, monkeypatch):
    def deny_connect(*args, **kwargs):
        raise AssertionError("network must not be used")

    monkeypatch.setattr("socket.socket.connect", deny_connect)

    for source in ("akshare", "tushare", "tickflow"):
        code, payload, stderr = run_cli(capsys, "fetch", *common_args(tmp_path), "--source", source)
        assert code == 2
        assert payload == {}
        assert stderr["error_type"] == "source_disabled"
        assert source in stderr["error_message"]

    layout = LakeLayout(tmp_path)
    assert not layout.manifest_path().exists()
    assert not list(layout.raw_root.rglob("*")) if layout.raw_root.exists() else True


def test_compare_tolerance_missing_and_file_loading(tmp_path):
    left = pd.DataFrame(
        [
            {"trade_date": "2026-01-02", "symbol": "000001.SZ", "close": 10.00, "source": "fake"},
            {"trade_date": "2026-01-03", "symbol": "000001.SZ", "close": 12.00, "source": "fake"},
        ]
    )
    right = pd.DataFrame(
        [
            {
                "trade_date": "2026-01-02",
                "symbol": "000001.SZ",
                "close": 10.005,
                "source": "reference",
            },
            {
                "trade_date": "2026-01-04",
                "symbol": "000001.SZ",
                "close": 13.00,
                "source": "reference",
            },
        ]
    )

    rows = compare_sources(left, right, "prices", ["trade_date", "symbol"], ["close"], 0.01)
    by_key = {row.key: row for row in rows}
    assert by_key["trade_date=2026-01-02|symbol=000001.SZ"].status == "match"
    assert by_key["trade_date=2026-01-03|symbol=000001.SZ"].status == "missing_right"
    assert by_key["trade_date=2026-01-04|symbol=000001.SZ"].status == "missing_left"

    csv_path = tmp_path / "reference.csv"
    parquet_path = tmp_path / "reference.parquet"
    right.to_csv(csv_path, index=False)
    right.to_parquet(parquet_path, index=False)
    assert len(load_comparison_frame(csv_path)) == 2
    assert len(load_comparison_frame(parquet_path)) == 2


def test_compare_command_writes_only_explicit_tmp_output(tmp_path, capsys):
    left = pd.DataFrame(
        [{"trade_date": "2026-01-02", "symbol": "000001.SZ", "close": 10.00, "source": "fake"}]
    )
    right = pd.DataFrame(
        [
            {
                "trade_date": "2026-01-02",
                "symbol": "000001.SZ",
                "close": 10.02,
                "source": "reference",
            }
        ]
    )
    left_path = tmp_path / "left.parquet"
    right_path = tmp_path / "right.parquet"
    output_path = tmp_path / "comparison.csv"
    left.to_parquet(left_path, index=False)
    right.to_parquet(right_path, index=False)

    code, payload, stderr = run_cli(
        capsys,
        "compare",
        "--dataset",
        "prices",
        "--left-path",
        str(left_path),
        "--right-path",
        str(right_path),
        "--keys",
        "trade_date,symbol",
        "--fields",
        "close",
        "--tolerance",
        "0.01",
        "--output",
        str(output_path),
    )

    assert code == 0
    assert stderr == {}
    assert payload["status_counts"] == {"mismatch": 1}
    assert output_path.exists()
    row = next(csv.DictReader(output_path.open("r", encoding="utf-8")))
    assert set(COMPARISON_FIELDS) <= set(row)


def test_cli_error_does_not_leak_token_value(tmp_path, capsys):
    code, _, stderr = run_cli(
        capsys,
        "fetch",
        *common_args(tmp_path),
        "--source",
        "tushare",
        "--symbols",
        "000001.SZ",
    )

    assert code == 2
    assert "plain-token" not in json.dumps(stderr)
    assert "secret-value" not in json.dumps(stderr)
