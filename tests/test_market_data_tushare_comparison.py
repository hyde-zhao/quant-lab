import ast
import csv
from pathlib import Path

import pandas as pd
import pytest

from market_data.comparison import (
    COMPARISON_FIELDS,
    COMPARISON_STATUS_VALUES,
    ComparisonInputError,
    compare_local_dataset,
    comparison_summary,
    load_comparison_frame,
    write_comparison_csv,
)


def test_cr005_local_comparison_rows_and_summary_are_offline(monkeypatch):
    network_calls = {"count": 0}

    def deny_connect(*args, **kwargs):
        network_calls["count"] += 1
        raise AssertionError("comparison 不得联网")

    monkeypatch.setattr("socket.socket.connect", deny_connect)
    monkeypatch.setenv("TUSHARE_TOKEN", "plain-token-secret-value")

    left = pd.DataFrame(
        [
            {
                "trade_date": "2026-01-02",
                "index_code": "399300.SZ",
                "close": 4000.0,
                "benchmark_kind": "price_index",
                "source": "tushare",
            },
            {
                "trade_date": "2026-01-03",
                "index_code": "399300.SZ",
                "close": 4000.0,
                "benchmark_kind": "price_index",
                "source": "tushare",
            },
            {
                "trade_date": "2026-01-04",
                "index_code": "399300.SZ",
                "close": 4010.0,
                "benchmark_kind": "price_index",
                "source": "tushare",
            },
        ]
    )
    right = pd.DataFrame(
        [
            {
                "trade_date": "2026-01-02",
                "index_code": "399300.SZ",
                "close": 4000.005,
                "benchmark_kind": "price_index",
                "source": "reference",
            },
            {
                "trade_date": "2026-01-03",
                "index_code": "399300.SZ",
                "close": 4000.5,
                "benchmark_kind": "proxy_baseline",
                "source": "reference",
            },
            {
                "trade_date": "2026-01-05",
                "index_code": "399300.SZ",
                "close": 3999.0,
                "benchmark_kind": "price_index",
                "source": "reference",
            },
        ]
    )

    rows = compare_local_dataset(
        left,
        right,
        "hs300_index",
        tolerance=0.01,
        fields=("close", "benchmark_kind"),
    )
    summary = comparison_summary(rows)

    assert network_calls["count"] == 0
    assert len(COMPARISON_FIELDS) == 10
    assert all(tuple(row.to_dict()) == COMPARISON_FIELDS for row in rows)
    assert summary["row_count"] == len(rows)
    assert summary["datasets"] == ["hs300_index"]
    assert summary["network_calls"] == 0
    assert set(summary["status_counts"]) == set(COMPARISON_STATUS_VALUES)
    assert summary["status_counts"]["match"] == 2
    assert summary["status_counts"]["mismatch"] == 1
    assert summary["status_counts"]["non_numeric_mismatch"] == 1
    assert summary["status_counts"]["missing_left"] == 2
    assert summary["status_counts"]["missing_right"] == 2
    assert "plain-token-secret-value" not in str([row.to_dict() for row in rows])


def test_cr005_dataset_defaults_cover_p0_local_contracts():
    fixtures = {
        "prices": (
            pd.DataFrame(
                [
                    {
                        "trade_date": "2026-01-02",
                        "symbol": "000001.SZ",
                        "close": 10.0,
                        "adjusted_close": 20.0,
                    }
                ]
            ),
            pd.DataFrame(
                [
                    {
                        "trade_date": "2026-01-02",
                        "symbol": "000001.SZ",
                        "close": 10.0,
                        "adjusted_close": 20.0,
                    }
                ]
            ),
        ),
        "trade_calendar": (
            pd.DataFrame(
                [{"trade_date": "2026-01-02", "exchange": "SSE", "is_open": True, "pretrade_date": "2025-12-31"}]
            ),
            pd.DataFrame(
                [{"trade_date": "2026-01-02", "exchange": "SSE", "is_open": True, "pretrade_date": "2025-12-31"}]
            ),
        ),
        "index_weights": (
            pd.DataFrame(
                [{"trade_date": "2026-01-02", "index_code": "399300.SZ", "con_code": "000001.SZ", "weight": 0.12}]
            ),
            pd.DataFrame(
                [{"trade_date": "2026-01-02", "index_code": "399300.SZ", "con_code": "000001.SZ", "weight": 0.12}]
            ),
        ),
        "hs300_index": (
            pd.DataFrame(
                [{"trade_date": "2026-01-02", "index_code": "399300.SZ", "close": 4000.0, "pct_chg": 0.25}]
            ),
            pd.DataFrame(
                [{"trade_date": "2026-01-02", "index_code": "399300.SZ", "close": 4000.0, "pct_chg": 0.25}]
            ),
        ),
    }

    for dataset, (left, right) in fixtures.items():
        rows = compare_local_dataset(left, right, dataset)
        assert rows
        assert {row.dataset for row in rows} == {dataset}
        assert comparison_summary(rows)["status_counts"]["match"] == len(rows)


def test_comparison_file_io_is_local_and_explicit(tmp_path):
    left = pd.DataFrame(
        [{"trade_date": "2026-01-02", "index_code": "399300.SZ", "close": 4000.0, "pct_chg": 0.25}]
    )
    right = left.copy()
    left_path = tmp_path / "left.csv"
    right_path = tmp_path / "right.parquet"
    output_path = tmp_path / "explicit" / "comparison.csv"
    left.to_csv(left_path, index=False)
    right.to_parquet(right_path, index=False)

    rows = compare_local_dataset(
        load_comparison_frame(left_path),
        load_comparison_frame(right_path),
        "hs300_index",
    )
    before = {path.relative_to(tmp_path) for path in tmp_path.rglob("*") if path.is_file()}
    written = write_comparison_csv(rows, output_path)
    after = {path.relative_to(tmp_path) for path in tmp_path.rglob("*") if path.is_file()}

    assert written == output_path
    assert after - before == {Path("explicit/comparison.csv")}
    row = next(csv.DictReader(output_path.open("r", encoding="utf-8")))
    assert tuple(row) == COMPARISON_FIELDS
    assert not any(part in after for part in (Path("raw"), Path("manifest"), Path("canonical"), Path("quality"), Path("catalog"), Path("gold")))
    with pytest.raises(ComparisonInputError, match="本地文件路径"):
        load_comparison_frame("https://example.invalid/right.csv")


def test_comparison_source_has_no_connector_runtime_storage_imports():
    source = Path("market_data/comparison.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module)

    forbidden = {
        "market_data.connectors",
        "market_data.runtime",
        "market_data.storage",
        "requests",
        "urllib",
        "socket",
    }
    assert not any(name == item or name.startswith(f"{item}.") for name in imports for item in forbidden)


def test_docs_record_tushare_backfill_required_missing_proxy_and_backtrader_boundaries():
    readme = Path("README.md").read_text(encoding="utf-8")
    manual = Path("docs/USER-MANUAL.md").read_text(encoding="utf-8")
    combined = f"{readme}\n{manual}"

    for token in ("enabled=true", "allowlist", "TUSHARE_TOKEN", "explicit command"):
        assert token in combined
    for token in ("required_missing", "不自动联网", "不自动 backfill", "不自动写湖", "remediation_job_spec", "next_action"):
        assert token in combined
    for token in ("dataset", "source", "interface", "index_code", "date range", "lake root", "run_id", "resume_policy", "dry_run", "path", "error enum"):
        assert token in manual
    for token in ("proxy_baseline", "不能填充 `hs300_index`", "不得声明沪深 300 相对收益"):
        assert token in combined
    for token in ("Backtrader", "optional backend", "不默认替代轻量主路径", "不联网", "不读 token/connector", "不绕过 quality gate"):
        assert token in combined

    forbidden_patterns = (
        "proxy_baseline 填充 hs300_index",
        "required_missing 自动 backfill",
        "Backtrader 默认替代轻量主路径",
    )
    assert not any(pattern in combined for pattern in forbidden_patterns)
