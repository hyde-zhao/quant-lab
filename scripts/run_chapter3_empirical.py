"""CR-034 第三章真实因子面板与单因子实证 runner。

该脚本只读取本地 lake canonical parquet，并写本地研究报告。不读取凭据、
不触发 provider fetch、不 publish catalog current pointer、不触发 QMT /
simulation / live。
"""

from __future__ import annotations

import argparse
import fnmatch
import gc
import json
import os
import resource
import sys
from dataclasses import asdict, dataclass, field
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Mapping, Sequence

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("NUMEXPR_NUM_THREADS", "1")

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from engine.chapter3_factor_replication import (
    DEFAULT_FACTOR_IDS,
    Chapter3FactorReplicationResult,
    Chapter3ResearchPolicy,
    factor_matrices_to_panel,
    prepare_chapter3_research_data,
    replicate_chapter3_factors,
)
from engine.factor_evaluation import build_factor_evaluation_report
from engine.multifactor_combiner import MultiFactorCombiner, build_multifactor_portfolio_plan
from engine.factor_statistics import long_short_summary, single_sort_returns
from market_data.contracts import SCHEMA_VERSION


EMPIRICAL_SCHEMA = "chapter3_empirical_run_v1"
FACTOR_VERSION = "chapter3-real-v1"
TARGET_START = "2000-01-01"
TARGET_END = "2019-12-31"
FORBIDDEN_OPERATION_COUNTS = {
    "credential_read": 0,
    "provider_fetch": 0,
    "lake_write": 0,
    "catalog_current_pointer_publish": 0,
    "qmt_operation": 0,
    "simulation_or_live_run": 0,
}


@dataclass(frozen=True, slots=True)
class Chapter3EmpiricalArtifacts:
    run_id: str
    output_dir: Path
    factor_panel_path: Path
    manifest_path: Path
    preprocessing_summary_path: Path
    metrics_csv_path: Path
    report_json_path: Path
    report_md_path: Path
    portfolio_plan_path: Path

    def to_dict(self) -> dict[str, str]:
        return {key: str(value) for key, value in asdict(self).items()}


@dataclass(frozen=True, slots=True)
class Chapter3EmpiricalResult:
    run_id: str
    status: str
    factor_ids: tuple[str, ...]
    monthly_panel_rows: int
    label_rows: int
    rebalance_count: int
    factor_summaries: tuple[dict[str, Any], ...]
    factor_correlation: dict[str, dict[str, float | None]]
    portfolio_plan: Mapping[str, Any]
    artifacts: Chapter3EmpiricalArtifacts
    limitations: tuple[str, ...] = ()
    operation_counts: Mapping[str, int] = field(default_factory=lambda: dict(FORBIDDEN_OPERATION_COUNTS))
    memory_budget: Mapping[str, Any] = field(default_factory=dict)
    schema_version: str = EMPIRICAL_SCHEMA

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "run_id": self.run_id,
            "status": self.status,
            "factor_ids": list(self.factor_ids),
            "monthly_panel_rows": self.monthly_panel_rows,
            "label_rows": self.label_rows,
            "rebalance_count": self.rebalance_count,
            "factor_summaries": list(self.factor_summaries),
            "factor_correlation": self.factor_correlation,
            "portfolio_plan": _json_safe(dict(self.portfolio_plan)),
            "artifacts": self.artifacts.to_dict(),
            "limitations": list(self.limitations),
            "operation_counts": dict(self.operation_counts),
            "memory_budget": dict(self.memory_budget),
        }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="运行第三章真实因子面板和单因子实证")
    parser.add_argument("--lake-root", default=os.environ.get("MARKET_DATA_LAKE_ROOT", "/mnt/ugreen-data-lake"))
    parser.add_argument("--start", default=TARGET_START)
    parser.add_argument("--end", default=TARGET_END)
    parser.add_argument("--run-id", default="")
    parser.add_argument("--output-root", default="process/research/chapter3_empirical")
    parser.add_argument("--panel-root", default="reports/chapter3_factor_panel")
    parser.add_argument("--min-cross-section", type=int, default=30)
    parser.add_argument("--min-period-ratio", type=float, default=2.0 / 3.0)
    parser.add_argument("--execution-mode", choices=("chunked", "full"), default="chunked")
    parser.add_argument("--chunk-lookback-days", type=int, default=540)
    parser.add_argument("--max-memory-gb", type=float, default=16.0)
    parser.add_argument("--resume", action="store_true", help="chunked 模式下复用已完成的年度 part 文件")
    parser.add_argument("--allow-large-full-run", action="store_true", help="允许超过两年的 full 模式，仅用于受控调试")
    parser.add_argument("--allow-readiness-non-pass", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    run_id = args.run_id or f"run-chapter3-empirical-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    lake_root = Path(args.lake_root)
    if not args.allow_readiness_non_pass:
        assert_readiness_pass(Path("process/research/chapter3_real_data_readiness/READINESS-REPORT.json"))
    if args.execution_mode == "full":
        assert_full_mode_window_allowed(args.start, args.end, allow_large=bool(args.allow_large_full_run))
        frames = load_chapter3_lake_frames(lake_root, start=args.start, end=args.end)
        enforce_memory_budget(args.max_memory_gb, "full_lake_load")
        result = run_empirical_from_frames(
            frames,
            run_id=run_id,
            start=args.start,
            end=args.end,
            output_root=Path(args.output_root),
            panel_root=Path(args.panel_root),
            min_cross_section=args.min_cross_section,
            min_period_ratio=args.min_period_ratio,
            max_memory_gb=args.max_memory_gb,
        )
    else:
        result = run_empirical_from_lake_chunked(
            lake_root,
            run_id=run_id,
            start=args.start,
            end=args.end,
            output_root=Path(args.output_root),
            panel_root=Path(args.panel_root),
            min_cross_section=args.min_cross_section,
            min_period_ratio=args.min_period_ratio,
            lookback_days=args.chunk_lookback_days,
            resume=bool(args.resume),
            max_memory_gb=args.max_memory_gb,
        )
    print(json.dumps({"ok": True, "status": result.status, "run_id": result.run_id, "artifacts": result.artifacts.to_dict(), **FORBIDDEN_OPERATION_COUNTS}, ensure_ascii=False, sort_keys=True))
    return 0


def assert_readiness_pass(path: Path) -> None:
    if not path.exists():
        raise RuntimeError(f"缺少 readiness 报告: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if str(data.get("status")) != "PASS":
        raise RuntimeError(f"第三章 readiness 未通过: {data.get('status')}")


def assert_full_mode_window_allowed(start: str, end: str, *, allow_large: bool) -> None:
    if allow_large:
        return
    days = (_parse_date(end) - _parse_date(start)).days + 1
    if days > 731:
        raise RuntimeError(
            "full 模式只允许两年以内调试窗口；长窗口必须使用默认 chunked 模式。"
        )


def load_chapter3_lake_frames(lake_root: Path, *, start: str, end: str) -> dict[str, pd.DataFrame]:
    start_year = _parse_date(start).year
    end_year = _parse_date(end).year
    price_run_ids = chapter3_price_run_ids(start_year, end_year)
    market_run_ids = chapter3_market_cap_run_ids(start_year, end_year)
    financial_run_ids = chapter3_financial_run_ids(start_year, end_year)
    trade_status_run_ids = chapter3_trade_status_run_ids(start_year, end_year)
    prices_limit_run_ids = chapter3_prices_limit_run_ids(start_year, end_year)
    prices = read_dataset_runs(
        lake_root,
        "prices",
        selected_run_ids=price_run_ids,
        columns=("trade_date", "symbol", "open", "high", "low", "close", "volume", "amount"),
        start=start,
        end=end,
    )
    adj_factor = read_dataset_runs(
        lake_root,
        "adj_factor",
        selected_run_ids=price_run_ids,
        columns=("trade_date", "symbol", "adj_factor"),
        start=start,
        end=end,
    )
    prices = build_back_adjusted_prices(prices, adj_factor)
    market_cap = read_dataset_runs(
        lake_root,
        "market_cap",
        selected_run_ids=market_run_ids,
        columns=("trade_date", "symbol", "market_cap", "float_market_cap", "turnover_rate", "turnover_rate_f"),
        start=start,
        end=end,
    )
    liquidity = read_dataset_runs(
        lake_root,
        "liquidity_capacity",
        selected_run_ids=market_run_ids,
        columns=("trade_date", "symbol", "turnover_rate", "turnover_rate_f", "adv20_amount", "adv20_volume"),
        start=start,
        end=end,
    )
    market_cap = merge_market_cap_liquidity(market_cap, liquidity)
    return {
        "prices": prices,
        "market_cap": market_cap,
        "financials": read_dataset_runs(
            lake_root,
            "financial_pit",
            selected_run_ids=financial_run_ids,
            columns=None,
            start=start,
            end=end,
            date_column="available_at",
        ),
        "stock_basic": normalise_stock_basic_for_historical_research(
            read_dataset_runs(lake_root, "stock_basic", columns=None)
        ),
        "trade_status": read_dataset_runs(
            lake_root,
            "trade_status",
            selected_run_ids=trade_status_run_ids,
            columns=("trade_date", "symbol", "is_tradable", "is_suspended", "is_st", "status_reason"),
            start=start,
            end=end,
        ),
        "prices_limit": read_dataset_runs(
            lake_root,
            "prices_limit",
            selected_run_ids=prices_limit_run_ids,
            columns=("trade_date", "symbol", "limit_up", "limit_down"),
            start=start,
            end=end,
        ),
        "trade_calendar": read_dataset_runs(
            lake_root,
            "trade_calendar",
            columns=("trade_date", "is_open"),
            start=start,
            end=end,
        ).drop_duplicates(["trade_date"], keep="last"),
    }


def chapter3_price_run_ids(start_year: int, end_year: int) -> tuple[str, ...]:
    run_ids: list[str] = []
    run_ids.extend(yearly_run_ids("run-cr034-chapter3-backfill", max(2000, start_year), min(2014, end_year)))
    run_ids.extend(yearly_run_ids("run-cr014-s14-prices-adj-factor", max(2015, start_year), min(2025, end_year), fuzzy=True))
    if start_year <= 2026 <= end_year:
        run_ids.append("run-cr014-s11-full-a-2026-ytd-date-batch-143508")
    return tuple(run_ids)


def chapter3_market_cap_run_ids(start_year: int, end_year: int) -> tuple[str, ...]:
    run_ids: list[str] = []
    run_ids.extend(yearly_run_ids("run-cr034-chapter3-backfill", max(2000, start_year), min(2014, end_year)))
    if end_year >= 2015:
        run_ids.append("run-cr018-missing-data-backfill-20150101-20260528-p0p1-20260529")
    return tuple(run_ids)


def chapter3_financial_run_ids(start_year: int, end_year: int) -> tuple[str, ...]:
    run_ids: list[str] = []
    if start_year <= 2019:
        run_ids.extend(("run-cr034-chapter3-constraints-2000-2019", "run-cr034-financial-pit-2000-2019"))
    if end_year >= 2020:
        run_ids.append("run-cr034-financial-pit-2020-2026*ytd*audited")
    return tuple(run_ids)


def chapter3_trade_status_run_ids(start_year: int, end_year: int) -> tuple[str, ...]:
    run_ids: list[str] = []
    if start_year <= 2019:
        run_ids.append("run-cr034-chapter3-constraints-2000-2019")
    if end_year >= 2020:
        run_ids.extend(
            (
                "run-cr018-missing-data-backfill-20150101-20260528-p0p1-20260529",
                "run-cr014-s13-trade-status-missing-2026-ytd-231252",
            )
        )
    return tuple(run_ids)


def chapter3_prices_limit_run_ids(start_year: int, end_year: int) -> tuple[str, ...]:
    run_ids: list[str] = []
    if start_year <= 2019:
        run_ids.append("run-cr034-chapter3-constraints-2000-2019")
    if end_year >= 2020:
        run_ids.extend(
            (
                "run-cr018-missing-data-backfill-20150101-20260528-p0p1-20260529",
                "run-cr018-price-limit-lifecycle-cleanup-20150101-20260528-20260529",
            )
        )
    return tuple(run_ids)


def run_empirical_from_frames(
    frames: Mapping[str, pd.DataFrame],
    *,
    run_id: str,
    start: str,
    end: str,
    output_root: Path,
    panel_root: Path,
    min_cross_section: int = 30,
    min_period_ratio: float = 2.0 / 3.0,
    max_memory_gb: float = 16.0,
) -> Chapter3EmpiricalResult:
    artifacts = empirical_artifacts(run_id, output_root=output_root, panel_root=panel_root)
    artifacts.output_dir.mkdir(parents=True, exist_ok=True)
    artifacts.factor_panel_path.parent.mkdir(parents=True, exist_ok=True)
    result = replicate_chapter3_factors(
        frames["prices"],
        market_cap=frames.get("market_cap"),
        financials=frames.get("financials"),
        stock_basic=frames.get("stock_basic"),
        trade_status=frames.get("trade_status"),
        prices_limit=frames.get("prices_limit"),
        trade_calendar=frames.get("trade_calendar"),
        min_cross_section=min_cross_section,
        min_period_ratio=min_period_ratio,
    )
    prepared = prepare_chapter3_research_data(
        frames["prices"],
        stock_basic=frames.get("stock_basic"),
        financials=frames.get("financials"),
        trade_status=frames.get("trade_status"),
        prices_limit=frames.get("prices_limit"),
        trade_calendar=frames.get("trade_calendar"),
    )
    rebalance_dates = tuple(day for day in prepared.rebalance_dates if start <= day.isoformat() <= end)
    labels = build_next_rebalance_labels(prepared.close, rebalance_dates)
    monthly_panel = build_monthly_factor_panel(result, rebalance_dates, run_id=run_id)
    monthly_panel = monthly_panel[monthly_panel["trade_date"].isin(labels["trade_date"].unique())].reset_index(drop=True)
    enforce_memory_budget(max_memory_gb, "full_factor_panel")
    return finalize_empirical_outputs(
        monthly_panel,
        labels,
        result.preprocessing_summary,
        tuple(result.limitations) + tuple(prepared.limitations),
        run_id=run_id,
        start=start,
        end=end,
        artifacts=artifacts,
        max_memory_gb=max_memory_gb,
    )


def run_empirical_from_lake_chunked(
    lake_root: Path,
    *,
    run_id: str,
    start: str,
    end: str,
    output_root: Path,
    panel_root: Path,
    min_cross_section: int = 30,
    min_period_ratio: float = 2.0 / 3.0,
    lookback_days: int = 540,
    resume: bool = False,
    max_memory_gb: float = 16.0,
) -> Chapter3EmpiricalResult:
    artifacts = empirical_artifacts(run_id, output_root=output_root, panel_root=panel_root)
    artifacts.output_dir.mkdir(parents=True, exist_ok=True)
    artifacts.factor_panel_path.parent.mkdir(parents=True, exist_ok=True)
    panel_part_paths: list[Path] = []
    label_part_paths: list[Path] = []
    preprocessing_part_paths: list[Path] = []
    part_root = artifacts.factor_panel_path.parent / "parts"
    label_part_root = artifacts.output_dir / "label_parts"
    part_root.mkdir(parents=True, exist_ok=True)
    label_part_root.mkdir(parents=True, exist_ok=True)
    limitations: list[str] = []
    start_day = _parse_date(start)
    end_day = _parse_date(end)
    for year in range(start_day.year, end_day.year + 1):
        panel_part_path = part_root / f"factor_panel_{year}.parquet"
        label_part_path = label_part_root / f"labels_{year}.parquet"
        preprocessing_part_path = part_root / f"preprocessing_summary_{year}.csv"
        if resume and panel_part_path.exists() and label_part_path.exists() and preprocessing_part_path.exists():
            print(f"[chapter3_empirical] year={year} resume existing parts", flush=True)
            panel_part_paths.append(panel_part_path)
            label_part_paths.append(label_part_path)
            preprocessing_part_paths.append(preprocessing_part_path)
            enforce_memory_budget(max_memory_gb, f"resume_year_{year}")
            continue
        year_start = max(date(year, 1, 1), start_day)
        year_end = min(date(year, 12, 31), end_day)
        chunk_start = max(start_day, year_start - timedelta(days=lookback_days))
        label_end = min(end_day, year_end + timedelta(days=45))
        print(
            f"[chapter3_empirical] year={year} chunk={chunk_start.isoformat()}..{label_end.isoformat()} target={year_start.isoformat()}..{year_end.isoformat()}",
            flush=True,
        )
        frames = load_chapter3_lake_frames(lake_root, start=chunk_start.isoformat(), end=label_end.isoformat())
        chunk_result = replicate_chapter3_factors(
            frames["prices"],
            market_cap=frames.get("market_cap"),
            financials=frames.get("financials"),
            stock_basic=frames.get("stock_basic"),
            trade_status=frames.get("trade_status"),
            prices_limit=frames.get("prices_limit"),
            trade_calendar=frames.get("trade_calendar"),
            min_cross_section=min_cross_section,
            min_period_ratio=min_period_ratio,
        )
        prepared = prepare_chapter3_research_data(
            frames["prices"],
            stock_basic=frames.get("stock_basic"),
            financials=frames.get("financials"),
            trade_status=frames.get("trade_status"),
            prices_limit=frames.get("prices_limit"),
            trade_calendar=frames.get("trade_calendar"),
        )
        target_rebalances = tuple(
            day for day in prepared.rebalance_dates if year_start.isoformat() <= day.isoformat() <= year_end.isoformat()
        )
        all_rebalances = list(prepared.rebalance_dates)
        label_rebalances = list(target_rebalances)
        if target_rebalances:
            last_target = target_rebalances[-1]
            next_dates = [day for day in all_rebalances if day > last_target]
            if next_dates:
                label_rebalances.append(next_dates[0])
        labels = build_next_rebalance_labels(prepared.close, label_rebalances)
        monthly_panel = build_monthly_factor_panel(chunk_result, target_rebalances, run_id=run_id)
        if not labels.empty and not monthly_panel.empty:
            monthly_panel = monthly_panel[monthly_panel["trade_date"].isin(labels["trade_date"].unique())].reset_index(drop=True)
        monthly_panel.to_parquet(panel_part_path, index=False)
        labels.to_parquet(label_part_path, index=False)
        summary = chunk_result.preprocessing_summary.copy()
        summary["chunk_year"] = year
        summary.to_csv(preprocessing_part_path, index=False)
        panel_part_paths.append(panel_part_path)
        label_part_paths.append(label_part_path)
        preprocessing_part_paths.append(preprocessing_part_path)
        limitations.extend(chunk_result.limitations)
        limitations.extend(prepared.limitations)
        print(
            f"[chapter3_empirical] year={year} panel_rows={len(monthly_panel)} label_rows={len(labels)}",
            flush=True,
        )
        del frames, chunk_result, prepared, labels, monthly_panel, summary
        gc.collect()
        enforce_memory_budget(max_memory_gb, f"chunk_year_{year}")
    monthly_panel = pd.concat((pd.read_parquet(path) for path in panel_part_paths), ignore_index=True) if panel_part_paths else pd.DataFrame()
    labels = pd.concat((pd.read_parquet(path) for path in label_part_paths), ignore_index=True) if label_part_paths else pd.DataFrame()
    enforce_memory_budget(max_memory_gb, "final_parts_concat")
    if not monthly_panel.empty:
        monthly_panel = monthly_panel.drop_duplicates(["trade_date", "symbol", "factor_id"], keep="last").reset_index(drop=True)
    if not labels.empty:
        labels = labels.drop_duplicates(["trade_date", "symbol"], keep="last").reset_index(drop=True)
    preprocessing = pd.concat((pd.read_csv(path) for path in preprocessing_part_paths), ignore_index=True) if preprocessing_part_paths else pd.DataFrame()
    enforce_memory_budget(max_memory_gb, "final_deduplicate")
    return finalize_empirical_outputs(
        monthly_panel,
        labels,
        preprocessing,
        tuple(dict.fromkeys(limitations)),
        run_id=run_id,
        start=start,
        end=end,
        artifacts=artifacts,
        max_memory_gb=max_memory_gb,
    )


def finalize_empirical_outputs(
    monthly_panel: pd.DataFrame,
    labels: pd.DataFrame,
    preprocessing_summary: pd.DataFrame,
    limitations: Sequence[str],
    *,
    run_id: str,
    start: str,
    end: str,
    artifacts: Chapter3EmpiricalArtifacts,
    max_memory_gb: float = 16.0,
) -> Chapter3EmpiricalResult:
    monthly_panel.to_parquet(artifacts.factor_panel_path, index=False)
    preprocessing_summary.to_csv(artifacts.preprocessing_summary_path, index=False)
    manifest = build_panel_manifest(run_id, monthly_panel, labels, limitations)
    manifest["evaluation_window"] = {"start": start, "end": end}
    manifest["memory_budget"] = memory_budget_summary(max_memory_gb)
    artifacts.manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    enforce_memory_budget(max_memory_gb, "panel_write")
    factor_summaries, reports = evaluate_factors(monthly_panel, labels, run_id=run_id, start=start, end=end)
    enforce_memory_budget(max_memory_gb, "factor_evaluation")
    factor_correlation = factor_correlation_matrix(monthly_panel)
    portfolio_plan = build_research_portfolio_plan(run_id, reports)
    enforce_memory_budget(max_memory_gb, "portfolio_plan")
    write_metrics_csv(artifacts.metrics_csv_path, factor_summaries)
    empirical = Chapter3EmpiricalResult(
        run_id=run_id,
        status="PASS",
        factor_ids=tuple(DEFAULT_FACTOR_IDS),
        monthly_panel_rows=int(len(monthly_panel)),
        label_rows=int(len(labels)),
        rebalance_count=int(labels["trade_date"].nunique()) if not labels.empty else 0,
        factor_summaries=tuple(factor_summaries),
        factor_correlation=factor_correlation,
        portfolio_plan=portfolio_plan,
        artifacts=artifacts,
        limitations=tuple(limitations),
        memory_budget=memory_budget_summary(max_memory_gb),
    )
    artifacts.report_json_path.write_text(json.dumps(empirical.to_dict(), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    artifacts.report_md_path.write_text(render_empirical_markdown(empirical, start=start, end=end), encoding="utf-8")
    artifacts.portfolio_plan_path.write_text(json.dumps(_json_safe(dict(portfolio_plan)), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return empirical


def empirical_artifacts(run_id: str, *, output_root: Path, panel_root: Path) -> Chapter3EmpiricalArtifacts:
    output_dir = output_root / run_id
    panel_dir = panel_root / run_id
    return Chapter3EmpiricalArtifacts(
        run_id=run_id,
        output_dir=output_dir,
        factor_panel_path=panel_dir / "factor_panel.parquet",
        manifest_path=panel_dir / "factor_panel_manifest.json",
        preprocessing_summary_path=panel_dir / "preprocessing_summary.csv",
        metrics_csv_path=output_dir / "factor_metrics.csv",
        report_json_path=output_dir / "EMPIRICAL-RUN-REPORT.json",
        report_md_path=output_dir / "EMPIRICAL-RUN-REPORT.md",
        portfolio_plan_path=output_dir / "MULTIFACTOR-ADMISSION-SUMMARY.json",
    )


def build_monthly_factor_panel(
    result: Chapter3FactorReplicationResult,
    rebalance_dates: Sequence[Any],
    *,
    run_id: str,
) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    for factor_id in DEFAULT_FACTOR_IDS:
        if factor_id not in result.raw_matrices:
            continue
        part = factor_matrices_to_panel(
            Chapter3FactorReplicationResult(
                factor_definitions=result.factor_definitions,
                raw_matrices={factor_id: result.raw_matrices[factor_id].reindex(rebalance_dates)},
                directional_matrices={factor_id: result.directional_matrices[factor_id].reindex(rebalance_dates)},
                winsorized_matrices={factor_id: result.winsorized_matrices[factor_id].reindex(rebalance_dates)},
                zscore_matrices={factor_id: result.zscore_matrices[factor_id].reindex(rebalance_dates)},
                market_factor_return=result.market_factor_return,
                preprocessing_summary=result.preprocessing_summary,
                limitations=result.limitations,
            ),
            source_dataset="chapter3_real_lake_candidate",
            factor_version=FACTOR_VERSION,
            quality_status="pass",
        )
        frames.append(part)
    if not frames:
        return pd.DataFrame()
    panel = pd.concat(frames, ignore_index=True)
    panel = panel.dropna(subset=["zscore_value"]).reset_index(drop=True)
    panel["trade_date"] = panel["trade_date"].astype(str)
    panel["available_at"] = panel["trade_date"].map(lambda day: f"{day}T16:30:00+08:00")
    panel["decision_time"] = panel["available_at"]
    panel["run_id"] = run_id
    panel["data_lineage"] = "cr034_readiness_pass_candidate"
    return panel


def build_next_rebalance_labels(close: pd.DataFrame, rebalance_dates: Sequence[Any]) -> pd.DataFrame:
    dates = list(rebalance_dates)
    rows: list[pd.DataFrame] = []
    for current, nxt in zip(dates, dates[1:]):
        if current not in close.index or nxt not in close.index:
            continue
        returns = close.loc[nxt] / close.loc[current] - 1.0
        part = returns.rename("forward_return").reset_index()
        part.columns = ["symbol", "forward_return"]
        part["trade_date"] = pd.Timestamp(current).date().isoformat()
        part["label_window_start"] = pd.Timestamp(current).date().isoformat()
        part["label_window_end"] = pd.Timestamp(nxt).date().isoformat()
        part["label_available_at"] = f"{pd.Timestamp(nxt).date().isoformat()}T16:30:00+08:00"
        rows.append(part.dropna(subset=["forward_return"]))
    if not rows:
        return pd.DataFrame(columns=["trade_date", "symbol", "forward_return"])
    labels = pd.concat(rows, ignore_index=True)
    labels["label_id"] = "next_rebalance_return"
    labels["return_kind"] = "next_month_hfq_return"
    labels["adjustment_policy"] = "hfq"
    return labels


def evaluate_factors(
    panel: pd.DataFrame,
    labels: pd.DataFrame,
    *,
    run_id: str,
    start: str,
    end: str,
) -> tuple[list[dict[str, Any]], list[Any]]:
    summaries: list[dict[str, Any]] = []
    reports: list[Any] = []
    for factor_id in DEFAULT_FACTOR_IDS:
        factor_panel = panel[panel["factor_id"] == factor_id]
        book_metrics = chapter3_book_style_metrics(factor_panel, labels)
        report = build_factor_evaluation_report(
            factor_panel.to_dict("records"),
            labels.to_dict("records"),
            benchmark={"benchmark_id": "A_share_cross_section_equal_weight"},
            cost={"commission_bps": 3.0, "slippage_bps": 5.0},
            exposure={"status": "not_neutralized", "note": "第三章基础复刻阶段不做行业/市值中性化。"},
            evaluation_config={
                "run_id": run_id,
                "factor_id": factor_id,
                "factor_version": FACTOR_VERSION,
                "dataset_release": "cr034_readiness_pass_candidate",
                "label_window": {"kind": "next_rebalance_return"},
                "evaluation_window": {"start": start, "end": end},
                "quantiles": 10,
                "permission_counters": dict(FORBIDDEN_OPERATION_COUNTS),
                "evidence_refs": ["process/research/chapter3_real_data_readiness/READINESS-REPORT.md"],
            },
        )
        reports.append(report)
        data = report.to_dict()
        summaries.append(
            {
                "factor_id": factor_id,
                "status": data["status"],
                "observations": data["coverage"].get("observations"),
                "rank_ic_mean": data["RankIC"].get("mean"),
                "ic_mean": data["IC"].get("mean"),
                "icir": data["ICIR"].get("value"),
                "long_short_return": book_metrics.get("long_short_return"),
                "long_short_t_stat": book_metrics.get("long_short_t_stat"),
                "long_short_t_stat_method": book_metrics.get("long_short_t_stat_method"),
                "long_short_observations": book_metrics.get("long_short_observations"),
                "turnover": data["turnover"].get("value"),
                "admission": factor_admission(data),
            }
        )
    return summaries, reports


def chapter3_book_style_metrics(factor_panel: pd.DataFrame, labels: pd.DataFrame) -> dict[str, Any]:
    """按第三章展示习惯计算收益和 t 值。

    CR030 的 `build_factor_evaluation_report` 负责通用研究准入指标；
    第三章复刻报告额外保留书中更直观的多空收益和 Newey-West t 值。
    """

    missing = {
        "long_short_return": None,
        "long_short_t_stat": None,
        "long_short_t_stat_method": "newey_west",
        "long_short_observations": 0,
    }
    if factor_panel.empty or labels.empty:
        return missing
    required_panel = {"trade_date", "symbol", "zscore_value"}
    required_labels = {"trade_date", "symbol", "forward_return"}
    if not required_panel <= set(factor_panel.columns) or not required_labels <= set(labels.columns):
        return missing

    factor_matrix = factor_panel.pivot_table(index="trade_date", columns="symbol", values="zscore_value", aggfunc="last")
    label_matrix = labels.pivot_table(index="trade_date", columns="symbol", values="forward_return", aggfunc="last")
    group_returns = single_sort_returns(
        factor_matrix,
        label_matrix,
        quantiles=10,
        min_cross_section=30,
    )
    summary = long_short_summary(group_returns, high_minus_low=True, t_stat_method="newey_west")
    return {
        "long_short_return": summary.get("mean"),
        "long_short_t_stat": summary.get("t_stat"),
        "long_short_t_stat_method": summary.get("t_stat_method", "newey_west"),
        "long_short_observations": summary.get("observation_count", 0),
    }


def factor_admission(report: Mapping[str, Any]) -> str:
    rank_ic = _as_float((report.get("RankIC") or {}).get("mean"))
    long_short = _as_float((report.get("long_short_returns") or {}).get("value"))
    observations = int((report.get("coverage") or {}).get("observations") or 0)
    if observations <= 0:
        return "blocked_no_observations"
    if rank_ic is None or long_short is None:
        return "watch_missing_metric"
    if rank_ic > 0 and long_short > 0:
        return "research_candidate"
    return "watch_or_reweight"


def build_research_portfolio_plan(run_id: str, reports: Sequence[Any]) -> Mapping[str, Any]:
    weights = {factor_id: 1.0 / len(DEFAULT_FACTOR_IDS) for factor_id in DEFAULT_FACTOR_IDS}
    combiner = MultiFactorCombiner(
        combiner_id=f"combo-{run_id}",
        factor_inputs=tuple(DEFAULT_FACTOR_IDS),
        normalization={"policy": "zscore"},
        winsorization={"limits": [0.01, 0.99]},
        neutralization={"enabled": False, "reason": "第三章基础复刻不做中性化"},
        orthogonalization={"enabled": False},
        weighting_policy={"policy": "rule_weight", "weights": weights},
        missing_policy={"policy": "drop_missing_factor_date_symbol"},
        constraints={"max_factor_weight": 1.0, "min_factor_weight": 0.0},
        rebalance_frequency="monthly",
        turnover_cap={"enabled": False},
        cost_config={"commission_bps": 3.0, "slippage_bps": 5.0},
        benchmark={"benchmark_id": "A_share_cross_section_equal_weight"},
        freeze_policy={"version": FACTOR_VERSION, "change_policy": "cp_or_cr_required"},
        capacity={"status": "not_evaluated"},
        permission_counters=dict(FORBIDDEN_OPERATION_COUNTS),
    )
    return build_multifactor_portfolio_plan(reports, combiner).to_dict()


def factor_correlation_matrix(panel: pd.DataFrame) -> dict[str, dict[str, float | None]]:
    if panel.empty:
        return {}
    matrix = panel.pivot_table(index=["trade_date", "symbol"], columns="factor_id", values="zscore_value", aggfunc="last")
    corr = matrix.corr(min_periods=30)
    return {
        str(row): {str(column): (None if pd.isna(value) else float(value)) for column, value in values.items()}
        for row, values in corr.to_dict(orient="index").items()
    }


def build_panel_manifest(
    run_id: str,
    panel: pd.DataFrame,
    labels: pd.DataFrame,
    limitations: Sequence[str],
) -> dict[str, Any]:
    return {
        "schema_version": "chapter3_factor_panel_manifest_v1",
        "run_id": run_id,
        "factor_version": FACTOR_VERSION,
        "factor_ids": list(DEFAULT_FACTOR_IDS),
        "panel_rows": int(len(panel)),
        "label_rows": int(len(labels)),
        "date_count": int(panel["trade_date"].nunique()) if not panel.empty else 0,
        "symbol_count": int(panel["symbol"].nunique()) if not panel.empty else 0,
        "source_dataset": "cr034_readiness_pass_candidate",
        "limitations": list(limitations),
        "operation_counts": dict(FORBIDDEN_OPERATION_COUNTS),
    }


def render_empirical_markdown(result: Chapter3EmpiricalResult, *, start: str, end: str) -> str:
    lines = [
        f"# CR-034 第三章 {start}..{end} 全样本实证报告",
        "",
        f"- status: `{result.status}`",
        f"- run_id: `{result.run_id}`",
        f"- evaluation_window: `{start}`..`{end}`",
        f"- factor_panel_rows: `{result.monthly_panel_rows}`",
        f"- label_rows: `{result.label_rows}`",
            f"- rebalance_count: `{result.rebalance_count}`",
            f"- max_memory_gb: `{result.memory_budget.get('max_memory_gb', '')}`",
            f"- max_rss_gb_observed: `{_fmt(result.memory_budget.get('max_rss_gb_observed'))}`",
            f"- memory_status: `{result.memory_budget.get('status', '')}`",
            "- catalog_current_pointer_publish: `0`",
        "- qmt_operation: `0`",
        "- simulation_or_live_run: `0`",
        "",
        "## 单因子摘要",
        "",
        "| factor_id | status | observations | long_short_return | long_short_t_stat | t_stat_method | RankIC | IC | ICIR | turnover | admission |",
        "|---|---|---:|---:|---:|---|---:|---:|---:|---:|---|",
    ]
    for item in result.factor_summaries:
        lines.append(
            "| `{factor_id}` | `{status}` | {obs} | {ls} | {ls_t} | `{t_method}` | {rank_ic} | {ic} | {icir} | {turnover} | `{admission}` |".format(
                factor_id=item["factor_id"],
                status=item["status"],
                obs=item.get("observations") or 0,
                ls=_fmt(item.get("long_short_return")),
                ls_t=_fmt(item.get("long_short_t_stat")),
                t_method=item.get("long_short_t_stat_method") or "",
                rank_ic=_fmt(item.get("rank_ic_mean")),
                ic=_fmt(item.get("ic_mean")),
                icir=_fmt(item.get("icir")),
                turnover=_fmt(item.get("turnover")),
                admission=item.get("admission") or "",
            )
        )
    lines.extend(
        [
            "",
            "## 产物",
            "",
            f"- factor_panel: `{result.artifacts.factor_panel_path}`",
            f"- manifest: `{result.artifacts.manifest_path}`",
            f"- preprocessing_summary: `{result.artifacts.preprocessing_summary_path}`",
            f"- metrics_csv: `{result.artifacts.metrics_csv_path}`",
            f"- portfolio_plan: `{result.artifacts.portfolio_plan_path}`",
            "",
            "## 多因子研究准入结论",
            "",
            "本报告允许作为项目内部多因子研究输入，不构成 production-valid、QMT-ready、simulation-ready 或 live-ready 声明。",
        ]
    )
    if result.limitations:
        lines.extend(["", "## 限制", ""])
        lines.extend(f"- {item}" for item in result.limitations)
    lines.append("")
    return "\n".join(lines)


def write_metrics_csv(path: Path, summaries: Sequence[Mapping[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(list(summaries)).to_csv(path, index=False)


def read_dataset_runs(
    lake_root: Path,
    dataset: str,
    *,
    selected_run_ids: Sequence[str] = (),
    columns: Sequence[str] | None = None,
    start: str = "",
    end: str = "",
    date_column: str = "trade_date",
) -> pd.DataFrame:
    root = lake_root / "canonical" / dataset / SCHEMA_VERSION
    frames: list[pd.DataFrame] = []
    if not root.exists():
        return pd.DataFrame(columns=list(columns or ()))
    selected = tuple(selected_run_ids)
    for run_dir in sorted(root.glob("run_id=*")):
        run_id = run_dir.name.removeprefix("run_id=")
        if selected and not any(run_id == item or fnmatch.fnmatch(run_id, item) for item in selected):
            continue
        for path in sorted(run_dir.glob("*.parquet")):
            read_kwargs: dict[str, Any] = {}
            if columns:
                read_kwargs["columns"] = list(columns)
            if date_column and (start or end):
                filters: list[tuple[str, str, str]] = []
                if start:
                    filters.append((date_column, ">=", start))
                if end:
                    filters.append((date_column, "<=", end))
                read_kwargs["filters"] = filters
            try:
                frame = pd.read_parquet(path, **read_kwargs)
            except Exception:
                frame = pd.read_parquet(path, columns=list(columns) if columns else None)
                if columns:
                    for column in columns:
                        if column not in frame.columns:
                            frame[column] = pd.NA
                    frame = frame[list(columns)]
            if frame.empty:
                continue
            if date_column in frame.columns and (start or end):
                dates = frame[date_column].map(_iso_day)
                mask = pd.Series(True, index=frame.index)
                if start:
                    mask &= dates >= start
                if end:
                    mask &= dates <= end
                frame = frame.loc[mask]
            if not frame.empty:
                frames.append(frame)
    if not frames:
        return pd.DataFrame(columns=list(columns or ()))
    result = pd.concat(frames, ignore_index=True)
    if {"trade_date", "symbol"} <= set(result.columns):
        result["trade_date"] = result["trade_date"].map(_iso_day)
        result["symbol"] = result["symbol"].astype(str).str.upper()
        result = result.drop_duplicates(["trade_date", "symbol"], keep="last")
    return result.reset_index(drop=True)


def yearly_run_ids(prefix: str, start_year: int, end_year: int, *, fuzzy: bool = False) -> tuple[str, ...]:
    suffix = "*" if fuzzy else ""
    return tuple(f"{prefix}-{year}{suffix}" for year in range(start_year, end_year + 1))


def build_back_adjusted_prices(prices: pd.DataFrame, adj_factor: pd.DataFrame) -> pd.DataFrame:
    merged = prices.merge(adj_factor, on=["trade_date", "symbol"], how="inner")
    for column in ("open", "high", "low", "close"):
        merged[column] = pd.to_numeric(merged[column], errors="coerce")
    merged["adj_factor"] = pd.to_numeric(merged["adj_factor"], errors="coerce")
    merged["back_adjusted_open"] = merged["open"] * merged["adj_factor"]
    merged["back_adjusted_high"] = merged["high"] * merged["adj_factor"]
    merged["back_adjusted_low"] = merged["low"] * merged["adj_factor"]
    merged["back_adjusted_close"] = merged["close"] * merged["adj_factor"]
    return merged.dropna(subset=["back_adjusted_close"]).reset_index(drop=True)


def merge_market_cap_liquidity(market_cap: pd.DataFrame, liquidity: pd.DataFrame) -> pd.DataFrame:
    if liquidity.empty:
        return market_cap
    keep = [column for column in ("trade_date", "symbol", "turnover_rate", "turnover_rate_f", "adv20_amount", "adv20_volume") if column in liquidity.columns]
    merged = market_cap.merge(liquidity[keep], on=["trade_date", "symbol"], how="left", suffixes=("", "_liq"))
    for column in ("turnover_rate", "turnover_rate_f"):
        alt = f"{column}_liq"
        if alt in merged.columns:
            merged[column] = merged[column].combine_first(merged[alt])
            merged = merged.drop(columns=[alt])
    return merged


def normalise_stock_basic_for_historical_research(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty or "symbol" not in frame.columns:
        return frame
    work = frame.copy()
    work["symbol"] = work["symbol"].astype(str).str.upper()
    if "list_date" in work.columns:
        work["list_date"] = work["list_date"].map(_iso_day)
    if "delist_date" in work.columns:
        work["delist_date"] = work["delist_date"].map(lambda value: _iso_day(value) if str(value).strip() else "")
    work["_list_date_sort"] = work.get("list_date", "").replace("", "9999-12-31")
    work = work.sort_values(["symbol", "_list_date_sort"]).drop_duplicates(["symbol"], keep="first")
    # 历史研究中 D 表示当前已退市，不应抹掉退市日前的样本；日期边界由 list/delist_date 控制。
    work["list_status"] = "L"
    return work.drop(columns=[column for column in ("_list_date_sort",) if column in work.columns])


def _iso_day(value: Any) -> str:
    text = str(value).strip()
    if not text or text.lower() in {"nan", "nat", "none"}:
        return ""
    if len(text) >= 10 and text[4] == "-" and text[7] == "-":
        return text[:10]
    if len(text) >= 8 and text[:8].isdigit():
        return f"{text[:4]}-{text[4:6]}-{text[6:8]}"
    return text[:10]


def _parse_date(value: Any) -> date:
    return datetime.strptime(_iso_day(value), "%Y-%m-%d").date()


def _as_float(value: Any) -> float | None:
    if value is None or pd.isna(value):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _fmt(value: Any) -> str:
    number = _as_float(value)
    return "" if number is None else f"{number:.6f}"


def max_rss_bytes() -> int:
    rss = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    if sys.platform == "darwin":
        return rss
    return rss * 1024


def memory_budget_summary(max_memory_gb: float) -> dict[str, Any]:
    observed = max_rss_bytes()
    budget_bytes = int(max_memory_gb * 1024 * 1024 * 1024) if max_memory_gb > 0 else 0
    return {
        "max_memory_gb": float(max_memory_gb),
        "max_rss_bytes_observed": observed,
        "max_rss_gb_observed": observed / 1024 / 1024 / 1024,
        "budget_bytes": budget_bytes,
        "status": "not_enforced" if budget_bytes <= 0 else ("pass" if observed <= budget_bytes else "fail"),
    }


def enforce_memory_budget(max_memory_gb: float, context: str) -> None:
    if max_memory_gb <= 0:
        return
    budget_bytes = int(max_memory_gb * 1024 * 1024 * 1024)
    observed = max_rss_bytes()
    if observed > budget_bytes:
        raise MemoryError(
            f"第三章实证 runner 超过内存预算: context={context}, "
            f"observed_gb={observed / 1024 / 1024 / 1024:.3f}, budget_gb={max_memory_gb:.3f}"
        )


def _json_safe(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if hasattr(value, "item"):
        try:
            return value.item()
        except Exception:
            return str(value)
    if isinstance(value, Path):
        return str(value)
    if pd.isna(value) if not isinstance(value, (list, tuple, dict, str, bytes)) else False:
        return None
    return value


if __name__ == "__main__":
    raise SystemExit(main())
