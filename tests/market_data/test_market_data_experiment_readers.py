import ast
import sys
from pathlib import Path

import pandas as pd

import experiments.run_out_of_sample_overfit_risk_exp10 as experiment_10
import experiments.run_market_regime_segments_exp12 as experiment_12
from market_data.benchmarks import BenchmarkPolicy, resolve_hs300_benchmark


TARGET_FILES = (
    Path("market_data/benchmarks.py"),
    Path("experiments/run_out_of_sample_overfit_risk_exp10.py"),
    Path("experiments/run_market_regime_segments_exp12.py"),
)


def test_help_includes_market_data_alias_and_benchmark_path(capsys, monkeypatch):
    for module_name, parser_func in (
        ("run_out_of_sample_overfit_risk_exp10.py", experiment_10.parse_args),
        ("run_market_regime_segments_exp12.py", experiment_12.parse_args),
    ):
        monkeypatch.setattr(sys, "argv", [module_name, "--help"])
        try:
            parser_func()
        except SystemExit as exc:
            assert exc.code == 0
        help_text = capsys.readouterr().out
        assert "--input-mode" in help_text
        assert "--data-dir" in help_text
        assert "--market-data-root" in help_text
        assert "--market-data-lake-root" in help_text
        assert "--benchmark-path" in help_text
        assert "--require-benchmark" in help_text


def test_market_data_root_alias_keeps_lake_root_destination(monkeypatch, tmp_path):
    benchmark_path = tmp_path / "hs300.parquet"
    _benchmark_frame().to_parquet(benchmark_path, index=False)

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_out_of_sample_overfit_risk_exp10.py",
            "--market-data-root",
            str(tmp_path / "lake"),
            "--benchmark-path",
            str(benchmark_path),
        ],
    )
    args10 = experiment_10.parse_args()
    assert args10.market_data_lake_root == str(tmp_path / "lake")
    assert args10.benchmark_path == str(benchmark_path)

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_market_regime_segments_exp12.py",
            "--market-data-root",
            str(tmp_path / "lake"),
            "--benchmark-path",
            str(benchmark_path),
        ],
    )
    args12 = experiment_12.parse_args()
    assert args12.market_data_lake_root == str(tmp_path / "lake")
    assert args12.benchmark_path == str(benchmark_path)


def test_explicit_benchmark_path_is_readonly_available(tmp_path):
    benchmark_path = tmp_path / "fixture" / "hs300.parquet"
    benchmark_path.parent.mkdir()
    _benchmark_frame().to_parquet(benchmark_path, index=False)
    before = _files_under(tmp_path)

    result = resolve_hs300_benchmark(
        lake_root=tmp_path / "lake",
        start_date="2026-01-02",
        end_date="2026-01-06",
        policy=BenchmarkPolicy.from_config({"benchmark_kind": "policy_unconfirmed"}),
        benchmark_path=benchmark_path,
    )
    after = _files_under(tmp_path)
    metadata = result.to_metadata()

    assert before == after
    assert result.status == "available"
    assert result.available
    assert result.frame is not None
    assert metadata["benchmark_status"] == "available"
    assert metadata["benchmark_source"] == "explicit_path"
    assert metadata["benchmark_dataset"] == "hs300_index"
    assert metadata["benchmark_path"] == str(benchmark_path)
    assert metadata["benchmark_unavailable_reason"] is None
    assert metadata["benchmark_is_proxy"] is False


def test_missing_benchmark_returns_structured_unavailable_and_required_missing(tmp_path, monkeypatch):
    monkeypatch.delenv("MARKET_DATA_LAKE_ROOT", raising=False)
    policy = BenchmarkPolicy.from_config({"benchmark_kind": "price_index", "confirmed": True})

    optional = resolve_hs300_benchmark(
        lake_root=tmp_path / "missing",
        start_date="2026-01-02",
        end_date="2026-01-06",
        policy=policy,
    )
    required = resolve_hs300_benchmark(
        lake_root=None,
        start_date="2026-01-02",
        end_date="2026-01-06",
        policy=BenchmarkPolicy.from_config(
            {"benchmark_kind": "price_index", "confirmed": True, "required": True},
            required=True,
        ),
    )

    assert optional.status == "unavailable"
    assert optional.to_metadata()["benchmark_dataset"] == "hs300_index"
    assert optional.to_metadata()["benchmark_source"] == "none"
    assert optional.to_metadata()["benchmark_unavailable_reason"] == "missing_dataset"
    assert required.status == "required_missing"
    assert required.to_metadata()["benchmark_unavailable_reason"] == "lake_root_missing"


def test_experiment_metadata_keeps_proxy_baseline_compatibility(tmp_path):
    missing = resolve_hs300_benchmark(
        lake_root=tmp_path / "missing",
        start_date="2026-01-02",
        end_date="2026-01-06",
        policy=BenchmarkPolicy.from_config({"benchmark_kind": "price_index", "confirmed": True}),
    )

    exp10 = experiment_10.apply_benchmark_metadata_experiment_10(missing, {})
    exp12 = experiment_12.apply_benchmark_metadata_experiment_12(
        missing,
        {"proxy_baseline": {"name": "legacy_proxy"}},
    )

    for payload in (exp10, exp12):
        assert payload["benchmark_status"] == "unavailable"
        assert payload["benchmark_source"] == "none"
        assert payload["benchmark_unavailable_reason"] == "missing_dataset"
        assert payload["hs300_benchmark_dataset"] == "hs300_index"
        assert payload["hs300_benchmark_is_proxy"] is False
        assert payload["benchmark_dataset"] == "proxy_baseline"
        assert payload["benchmark_kind"] == "proxy_baseline"
        assert "hs300_index" not in payload
    assert exp10["benchmark_relative_return_enabled"] is False
    assert exp12["hs300_relative_return_enabled"] is False
    assert exp12["proxy_baseline"] == {"name": "legacy_proxy"}


def test_no_forbidden_imports_or_data_layer_jobs():
    forbidden_exact = {
        "market_data.runtime",
        "market_data.storage",
        "requests",
        "urllib",
        "httpx",
        "aiohttp",
        "socket",
        "subprocess",
    }
    forbidden_calls = {"fetch", "backfill", "replay", "normalize", "revalidate", "run_data_layer", "run_backfill"}
    for source_path in TARGET_FILES:
        tree = ast.parse(source_path.read_text(encoding="utf-8"))
        imports = _imports_for(tree)
        assert not any(name.startswith("market_data.connectors") for name in imports), source_path
        assert not any(name in forbidden_exact for name in imports), source_path
        assert not any(_call_name(node.func) in forbidden_calls for node in ast.walk(tree) if isinstance(node, ast.Call)), source_path


def _benchmark_frame() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "trade_date": "2026-01-02",
                "index_code": "399300.SZ",
                "close": 4000.0,
                "benchmark_kind": "price_index",
                "source_run_id": "fixture-run",
                "lineage_raw_checksum": "fixture-checksum",
            },
            {
                "trade_date": "2026-01-05",
                "index_code": "399300.SZ",
                "close": 4010.0,
                "benchmark_kind": "price_index",
                "source_run_id": "fixture-run",
                "lineage_raw_checksum": "fixture-checksum",
            },
        ]
    )


def _files_under(root: Path) -> list[str]:
    return sorted(str(path.relative_to(root)) for path in root.rglob("*") if path.is_file())


def _imports_for(tree: ast.AST) -> list[str]:
    imports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.append(node.module)
    return imports


def _call_name(func: ast.AST) -> str:
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        return func.attr
    return ""
