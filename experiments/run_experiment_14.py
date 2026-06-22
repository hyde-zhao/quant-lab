"""实验十四：数据与 benchmark 口径审计报告。"""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
from pathlib import Path
import sys
from typing import Any

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from engine.research_dataset import ResearchInputMetadata, build_research_input_metadata
from engine.research_paths import research_report_path
from experiments.reporting import attach_research_input_metadata, legacy_report_limitation
from market_data.benchmarks import BenchmarkPolicy, resolve_hs300_benchmark


REQUIRED_PARQUETS = {
    "prices": "prices.parquet",
    "index_members": "index_members.parquet",
    "trade_calendar": "trade_calendar.parquet",
}

SIMPLIFIED_POOL = ["000001.SZ", "600519.SH", "000858.SZ", "000002.SZ", "300750.SZ"]


@dataclass(frozen=True, slots=True)
class AuditIssue:
    severity: str
    check: str
    message: str


@dataclass(frozen=True, slots=True)
class DatasetSummary:
    dataset: str
    status: str
    rows: int = 0
    start_date: str = ""
    end_date: str = ""
    symbol_count: int = 0
    trade_day_count: int = 0
    missing_rate: float | None = None
    notes: str = ""


def main() -> None:
    args = parse_args()
    report_path = run_audit(args)
    print(f"报告已生成: {report_path}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="运行实验十四数据与 benchmark 口径审计。")
    parser.add_argument("--data-dir", required=True, default=None, help="必须显式传入的本地标准 parquet 目录。")
    parser.add_argument("--quality-report", default=str(research_report_path("data_quality_report.csv")))
    parser.add_argument("--phase-two-report", default=str(research_report_path("experiment_13", "backtest_report.md")))
    parser.add_argument("--output-dir", default=str(research_report_path("experiment_14")))
    parser.add_argument("--forward-return-horizon", type=int, default=20)
    parser.add_argument("--market-data-lake-root", default=None)
    parser.add_argument("--benchmark-kind", default="price_index")
    parser.add_argument("--benchmark-confirmed", action="store_true", help="声明真实 benchmark policy 已确认。")
    parser.add_argument("--benchmark-unconfirmed", action="store_true", help="显式声明 benchmark policy 未确认。")
    return parser.parse_args()


def run_audit(args: argparse.Namespace) -> Path:
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    data_dir = require_explicit_data_dir(args)
    frames, load_issues = load_local_frames(data_dir)
    quality_rows = load_quality_report(Path(args.quality_report))
    summaries, summary_issues = summarize_datasets(frames, quality_rows)
    coverage_start, coverage_end = price_coverage(summaries)
    label_window, label_issues = calculate_forward_label_window(
        frames.get("trade_calendar"),
        coverage_start,
        coverage_end,
        int(args.forward_return_horizon),
    )
    universe_summary, universe_issues = summarize_universe(frames.get("index_members"))
    benchmark_summary, benchmark_issues = summarize_benchmark(
        args,
        coverage_start=coverage_start,
        coverage_end=coverage_end,
    )
    report_checks, report_issues = inspect_phase_report(
        Path(args.phase_two_report),
        coverage_end,
    )

    issues = [
        *load_issues,
        *summary_issues,
        *label_issues,
        *universe_issues,
        *benchmark_issues,
        *report_issues,
    ]
    status = overall_status(issues)
    research_input_metadata = build_experiment_14_research_input_metadata(
        status=status,
        summaries=summaries,
        label_window=label_window,
        universe_summary=universe_summary,
        benchmark_summary=benchmark_summary,
        args=args,
    )
    report = render_report(
        status=status,
        summaries=summaries,
        quality_rows=quality_rows,
        label_window=label_window,
        universe_summary=universe_summary,
        benchmark_summary=benchmark_summary,
        report_checks=report_checks,
        issues=issues,
        args=args,
        research_input_metadata=research_input_metadata,
    )
    report_path = output_dir / "data_and_benchmark_report.md"
    report_path.write_text(report, encoding="utf-8")
    return report_path


def require_explicit_data_dir(args: argparse.Namespace) -> Path:
    data_dir = getattr(args, "data_dir", None)
    if data_dir is None or str(data_dir).strip() == "":
        raise ValueError("必须显式传入 --data-dir，禁止默认读取仓库旧数据目录。")
    return Path(data_dir)


def load_local_frames(data_dir: Path) -> tuple[dict[str, pd.DataFrame], list[AuditIssue]]:
    frames: dict[str, pd.DataFrame] = {}
    issues: list[AuditIssue] = []
    for dataset, filename in REQUIRED_PARQUETS.items():
        path = data_dir / filename
        if not path.exists():
            frames[dataset] = pd.DataFrame()
            issues.append(AuditIssue("FAIL", "数据文件", f"缺少标准 parquet: {path}"))
            continue
        try:
            frames[dataset] = pd.read_parquet(path)
        except Exception as exc:
            frames[dataset] = pd.DataFrame()
            issues.append(AuditIssue("FAIL", "数据文件", f"parquet 读取失败: {path}: {type(exc).__name__}: {exc}"))
    return frames, issues


def load_quality_report(path: Path) -> list[dict[str, str]]:
    return []


def summarize_datasets(
    frames: dict[str, pd.DataFrame],
    quality_rows: list[dict[str, str]],
) -> tuple[list[DatasetSummary], list[AuditIssue]]:
    issues: list[AuditIssue] = []
    quality_by_dataset = {row.get("dataset", ""): row for row in quality_rows}
    prices = frames.get("prices", pd.DataFrame())
    calendar = frames.get("trade_calendar", pd.DataFrame())
    summaries = [
        summarize_prices(prices, calendar, quality_by_dataset.get("prices")),
        summarize_index_members(frames.get("index_members", pd.DataFrame()), quality_by_dataset.get("index_members")),
        summarize_calendar(calendar, quality_by_dataset.get("trade_calendar")),
    ]
    if not quality_rows:
        issues.append(AuditIssue("WARN", "质量报告", "未找到质量报告 CSV，缺失率只能从 parquet 粗略估算。"))
    else:
        overall = quality_by_dataset.get("overall") or quality_rows[-1]
        if overall.get("quality_status") == "fail":
            issues.append(AuditIssue("FAIL", "质量报告", "overall quality_status=fail。"))
        elif overall.get("quality_status") == "warn":
            issues.append(AuditIssue("WARN", "质量报告", "overall quality_status=warn。"))
    for summary in summaries:
        if summary.status == "missing":
            issues.append(AuditIssue("FAIL", "数据覆盖", f"{summary.dataset} 不可用。"))
    return summaries, issues


def summarize_prices(
    frame: pd.DataFrame,
    calendar: pd.DataFrame,
    quality_row: dict[str, str] | None,
) -> DatasetSummary:
    if frame.empty:
        return DatasetSummary(dataset="prices", status="missing")
    work = frame.copy()
    work["trade_date"] = work["trade_date"].astype(str)
    start = str(work["trade_date"].min())
    end = str(work["trade_date"].max())
    symbol_count = int(work["symbol"].astype(str).nunique()) if "symbol" in work.columns else 0
    trade_day_count = int(work["trade_date"].nunique())
    missing_rate = _quality_missing_rate(quality_row)
    if missing_rate is None:
        missing_rate = estimate_price_missing_rate(work, calendar, start, end, symbol_count)
    policies = sorted({str(value) for value in work.get("adjustment_policy", pd.Series(dtype="object")).dropna().unique()})
    notes = f"adjustment_policy={', '.join(policies) if policies else '未声明'}"
    return DatasetSummary("prices", "available", len(work), start, end, symbol_count, trade_day_count, missing_rate, notes)


def summarize_index_members(frame: pd.DataFrame, quality_row: dict[str, str] | None) -> DatasetSummary:
    if frame.empty:
        return DatasetSummary(dataset="index_members", status="missing")
    work = frame.copy()
    date_columns = [column for column in ("snapshot_date", "effective_date", "trade_date") if column in work.columns]
    dates = pd.Series(dtype="object")
    for column in date_columns:
        dates = pd.concat([dates, work[column].dropna().astype(str)], ignore_index=True)
    start = str(dates.min()) if not dates.empty else ""
    end = str(dates.max()) if not dates.empty else ""
    symbol_count = int(work["symbol"].astype(str).nunique()) if "symbol" in work.columns else 0
    missing_rate = _quality_missing_rate(quality_row)
    pit_values = sorted({str(value) for value in work.get("is_pit_universe", pd.Series(dtype="object")).dropna().unique()})
    notes = f"is_pit_universe={', '.join(pit_values) if pit_values else '未声明'}"
    return DatasetSummary("index_members", "available", len(work), start, end, symbol_count, 0, missing_rate, notes)


def summarize_calendar(frame: pd.DataFrame, quality_row: dict[str, str] | None) -> DatasetSummary:
    if frame.empty:
        return DatasetSummary(dataset="trade_calendar", status="missing")
    work = frame.copy()
    work["trade_date"] = work["trade_date"].astype(str)
    open_frame = open_calendar(work)
    start = str(open_frame["trade_date"].min()) if not open_frame.empty else str(work["trade_date"].min())
    end = str(open_frame["trade_date"].max()) if not open_frame.empty else str(work["trade_date"].max())
    missing_rate = _quality_missing_rate(quality_row)
    return DatasetSummary("trade_calendar", "available", len(work), start, end, 0, int(open_frame["trade_date"].nunique()), missing_rate)


def estimate_price_missing_rate(
    prices: pd.DataFrame,
    calendar: pd.DataFrame,
    start: str,
    end: str,
    symbol_count: int,
) -> float | None:
    if calendar.empty or symbol_count <= 0:
        return None
    open_dates = open_calendar(calendar)
    if open_dates.empty:
        return None
    open_dates = open_dates[(open_dates["trade_date"].astype(str) >= start) & (open_dates["trade_date"].astype(str) <= end)]
    denominator = int(open_dates["trade_date"].nunique()) * symbol_count
    if denominator <= 0:
        return None
    actual = int(prices[["trade_date", "symbol"]].drop_duplicates().shape[0])
    return max(denominator - actual, 0) / denominator


def open_calendar(frame: pd.DataFrame) -> pd.DataFrame:
    work = frame.copy()
    work["trade_date"] = work["trade_date"].astype(str)
    if "is_open" in work.columns:
        work = work[work["is_open"].astype(bool)]
    return work.sort_values("trade_date").reset_index(drop=True)


def _quality_missing_rate(row: dict[str, str] | None) -> float | None:
    if not row:
        return None
    value = row.get("missing_rate")
    if value in (None, ""):
        return None
    try:
        return float(value)
    except ValueError:
        return None


def price_coverage(summaries: list[DatasetSummary]) -> tuple[str, str]:
    prices = next((summary for summary in summaries if summary.dataset == "prices"), None)
    if prices is None:
        return "", ""
    return prices.start_date, prices.end_date


def calculate_forward_label_window(
    calendar: pd.DataFrame | None,
    coverage_start: str,
    coverage_end: str,
    horizon: int,
) -> tuple[dict[str, Any], list[AuditIssue]]:
    issues: list[AuditIssue] = []
    result = {
        "horizon": horizon,
        "coverage_start": coverage_start,
        "coverage_end": coverage_end,
        "label_usable_start": coverage_start,
        "label_usable_end": "",
        "status": "unavailable",
    }
    if not coverage_start or not coverage_end:
        issues.append(AuditIssue("FAIL", "未来收益窗口", "prices 覆盖区间不可用，无法计算未来收益标签。"))
        return result, issues
    if calendar is None or calendar.empty:
        issues.append(AuditIssue("FAIL", "未来收益窗口", "交易日历不可用，无法计算未来收益标签窗口。"))
        return result, issues
    open_dates = open_calendar(calendar)
    open_dates = open_dates[(open_dates["trade_date"] >= coverage_start) & (open_dates["trade_date"] <= coverage_end)]
    dates = open_dates["trade_date"].drop_duplicates().sort_values().tolist()
    if horizon <= 0:
        result.update({"label_usable_end": coverage_end, "status": "available"})
        return result, issues
    if len(dates) <= horizon:
        issues.append(AuditIssue("FAIL", "未来收益窗口", f"交易日数量 {len(dates)} 不足以支持 {horizon} 日未来收益计算。"))
        return result, issues
    result.update({"label_usable_end": dates[-horizon - 1], "status": "available"})
    return result, issues


def summarize_universe(frame: pd.DataFrame | None) -> tuple[dict[str, Any], list[AuditIssue]]:
    issues: list[AuditIssue] = []
    if frame is None or frame.empty:
        issues.append(AuditIssue("FAIL", "股票池", "index_members 不可用，无法确认股票池口径。"))
        return {"status": "missing"}, issues
    symbol_count = int(frame["symbol"].astype(str).nunique()) if "symbol" in frame.columns else 0
    pit_values = {bool(value) for value in frame.get("is_pit_universe", pd.Series([False])).fillna(False).tolist()}
    is_pit = pit_values == {True}
    if is_pit:
        pool_type = "PIT 池"
    else:
        pool_type = "固定快照池"
        issues.append(AuditIssue("WARN", "股票池", "当前 index_members 为固定快照池，不是 PIT 池，存在幸存者偏差。"))
    return {
        "status": "available",
        "symbol_count": symbol_count,
        "pool_type": pool_type,
        "is_pit_universe": is_pit,
        "simplified_pool": ", ".join(SIMPLIFIED_POOL),
        "fixed_snapshot_pool": f"{symbol_count} 只，来自当前 index_members parquet",
        "pit_pool": "当前可用" if is_pit else "当前不可用",
    }, issues


def summarize_benchmark(args: argparse.Namespace, *, coverage_start: str, coverage_end: str) -> tuple[dict[str, Any], list[AuditIssue]]:
    issues: list[AuditIssue] = []
    confirmed = bool(args.benchmark_confirmed and not args.benchmark_unconfirmed)
    summary: dict[str, Any] = {
        "status": "proxy_or_unconfirmed",
        "classification": "代理基准",
        "benchmark_kind": args.benchmark_kind,
        "message": "benchmark policy 未确认，报告只能声明代理基准，不能声明真实沪深300超额收益。",
    }
    if not coverage_start or not coverage_end:
        issues.append(AuditIssue("FAIL", "benchmark", "缺少价格覆盖区间，无法评估 benchmark 覆盖。"))
        return summary, issues
    if not confirmed:
        issues.append(AuditIssue("WARN", "benchmark", "benchmark policy 未确认；当前只能使用代理基准。"))
        return summary, issues
    policy = BenchmarkPolicy.from_config(
        {
            "benchmark_kind": args.benchmark_kind,
            "confirmed": True,
            "required": False,
            "allow_warn": True,
        }
    )
    result = resolve_hs300_benchmark(
        args.market_data_lake_root,
        coverage_start,
        coverage_end,
        policy,
        required=False,
    )
    metadata = result.to_metadata()
    if result.available:
        summary.update(
            {
                "status": "available",
                "classification": "真实指数",
                "message": "真实 hs300_index benchmark 可用。",
                "metadata": metadata,
            }
        )
        return summary, issues
    summary.update(
        {
            "status": result.status,
            "classification": "代理基准",
            "message": f"真实 hs300_index benchmark 不可用: {result.missing_reason or result.status}",
            "metadata": metadata,
        }
    )
    issues.append(AuditIssue("WARN", "benchmark", summary["message"]))
    return summary, issues


def inspect_phase_report(path: Path, coverage_end: str) -> tuple[dict[str, Any], list[AuditIssue]]:
    issues: list[AuditIssue] = []
    checks: dict[str, Any] = {
        "path": str(path),
        "status": "legacy_only_not_current_truth",
        "legacy_report_policy": "legacy_only_not_current_truth",
        "dates": [],
        "mentions_proxy_benchmark": False,
        "mentions_real_benchmark": False,
        "mentions_universe": False,
        "mentions_bias": False,
        "max_report_date": "",
    }
    issues.append(AuditIssue("WARN", "阶段二报告", f"阶段二报告仅作为 legacy 限制记录，不读取内容: {path}"))
    return checks, issues


def build_experiment_14_research_input_metadata(
    *,
    status: str,
    summaries: list[DatasetSummary],
    label_window: dict[str, Any],
    universe_summary: dict[str, Any],
    benchmark_summary: dict[str, Any],
    args: argparse.Namespace,
) -> ResearchInputMetadata:
    coverage_start, coverage_end = price_coverage(summaries)
    metadata_coverage_start, metadata_coverage_end = metadata_coverage_window(coverage_start, coverage_end, label_window)
    label_available_end = str(label_window.get("label_usable_end") or metadata_coverage_end)
    benchmark_metadata = dict(benchmark_summary.get("metadata") or {})
    benchmark_metadata.setdefault("benchmark_status", benchmark_summary.get("status", "proxy_or_unconfirmed"))
    benchmark_metadata.setdefault("benchmark_kind", benchmark_summary.get("benchmark_kind", args.benchmark_kind))
    benchmark_metadata.setdefault("missing_reason", benchmark_summary.get("message", ""))
    universe_mode = "pit" if universe_summary.get("is_pit_universe") else "fixed_snapshot"
    if universe_summary.get("status") == "missing":
        universe_mode = "missing"
    known_limitations: list[Any] = [
        legacy_report_limitation(args.quality_report, "legacy_quality_report"),
        legacy_report_limitation(args.phase_two_report, "legacy_phase_two_report"),
        "旧质量报告和旧阶段报告仅作为 legacy limitation，不作为 current truth 或 coverage proof。",
    ]
    if not coverage_start or not coverage_end:
        known_limitations.append("prices 覆盖区间不可用；失败报告仅使用 metadata 占位日期以保留错误报告可读性。")
    if not label_window.get("label_usable_end"):
        known_limitations.append("label_available_end 不可用；失败报告使用 coverage_end 作为 metadata 占位，不作为可交易标签证明。")
    if universe_mode != "pit":
        known_limitations.append("当前股票池不是严格 PIT 股票池，存在幸存者偏差。")
    if benchmark_metadata.get("benchmark_status") != "available":
        known_limitations.append("benchmark 未确认为真实可用时，只能声明代理基准或未确认 benchmark。")
    return build_research_input_metadata(
        {
            "report_kind": "experiment_14_data_benchmark",
            "source_run_id": "experiment_14_offline_run",
            "coverage_start": metadata_coverage_start,
            "coverage_end": metadata_coverage_end,
            "benchmark": benchmark_metadata,
            "universe": {
                "universe_mode": universe_mode,
                "is_pit_universe": bool(universe_summary.get("is_pit_universe", False)),
                "pit_status": "available" if universe_mode == "pit" else "unavailable",
                "survivorship_bias_note": "fixed snapshot universe; not PIT" if universe_mode != "pit" else "",
            },
            "adjustment_policy": infer_adjustment_policy(summaries),
            "label_window": {
                "forward_return_horizon": int(label_window.get("horizon", args.forward_return_horizon)),
                "label_available_end": label_available_end,
                "label_status": label_window.get("status", ""),
            },
            "quality": {
                "quality_status": status,
                "readiness_status": "audit_ready" if status != "FAIL" else "audit_blocked",
            },
            "known_limitations": known_limitations,
            "allowed_claims": ["data_coverage_audit", "benchmark_policy_audit", "legacy_boundary_disclosure"],
        }
    )


def metadata_coverage_window(coverage_start: str, coverage_end: str, label_window: dict[str, Any]) -> tuple[str, str]:
    start = str(coverage_start or label_window.get("coverage_start") or "")
    end = str(coverage_end or label_window.get("coverage_end") or "")
    if start and end:
        return start, end
    fallback = start or end or "1970-01-01"
    return fallback, fallback


def infer_adjustment_policy(summaries: list[DatasetSummary]) -> str:
    prices = next((summary for summary in summaries if summary.dataset == "prices"), None)
    if prices and "adjustment_policy=" in prices.notes:
        value = prices.notes.split("adjustment_policy=", 1)[1].strip()
        return value or "source_declared_unknown"
    return "source_declared_unknown"


def overall_status(issues: list[AuditIssue]) -> str:
    severities = {issue.severity for issue in issues}
    if "FAIL" in severities:
        return "FAIL"
    if "WARN" in severities:
        return "WARN"
    return "PASS"


def render_report(
    *,
    status: str,
    summaries: list[DatasetSummary],
    quality_rows: list[dict[str, str]],
    label_window: dict[str, Any],
    universe_summary: dict[str, Any],
    benchmark_summary: dict[str, Any],
    report_checks: dict[str, Any],
    issues: list[AuditIssue],
    args: argparse.Namespace,
    research_input_metadata: ResearchInputMetadata,
) -> str:
    lines = [
        "# 实验十四：数据与 benchmark 口径修复报告",
        "",
        "## 执行结论",
        "",
        f"- 审计状态：**{status}**",
        f"- 数据目录：`{args.data_dir}`",
        f"- 质量报告：`{args.quality_report}`",
        f"- 阶段二报告：`{args.phase_two_report}`",
        "",
        "### 关键问题",
        "",
        render_issue_list(issues),
        "",
        *attach_research_input_metadata([], research_input_metadata),
        "",
        "## 数据覆盖",
        "",
        markdown_table(
            [asdict(summary) for summary in summaries],
            ["dataset", "status", "rows", "start_date", "end_date", "symbol_count", "trade_day_count", "missing_rate", "notes"],
        ),
        "",
        "## 质量报告摘要",
        "",
        render_quality_table(quality_rows),
        "",
        "## 未来收益可用窗口",
        "",
        markdown_table([label_window], ["horizon", "coverage_start", "coverage_end", "label_usable_start", "label_usable_end", "status"]),
        "",
        "## 股票池口径",
        "",
        markdown_table(
            [
                {"口径": "5 股池", "说明": universe_summary.get("simplified_pool", ", ".join(SIMPLIFIED_POOL)), "PIT": "否", "用途": "简化策略 smoke test / 对照实验"},
                {"口径": "固定快照池", "说明": universe_summary.get("fixed_snapshot_pool", ""), "PIT": "否", "用途": "当前本地 parquet 的实际股票池"},
                {"口径": "PIT 池", "说明": universe_summary.get("pit_pool", "当前不可用"), "PIT": "是", "用途": "未来严格历史成分研究"},
            ],
            ["口径", "说明", "PIT", "用途"],
        ),
        "",
        "## Benchmark 口径",
        "",
        markdown_table(
            [
                {
                    "classification": benchmark_summary.get("classification", ""),
                    "status": benchmark_summary.get("status", ""),
                    "benchmark_kind": benchmark_summary.get("benchmark_kind", ""),
                    "message": benchmark_summary.get("message", ""),
                }
            ],
            ["classification", "status", "benchmark_kind", "message"],
        ),
        "",
        "## 阶段二报告一致性检查",
        "",
        markdown_table(
            [
                {
                    "path": report_checks.get("path", ""),
                    "status": report_checks.get("status", ""),
                    "max_report_date": report_checks.get("max_report_date", ""),
                    "mentions_proxy_benchmark": report_checks.get("mentions_proxy_benchmark", False),
                    "mentions_real_benchmark": report_checks.get("mentions_real_benchmark", False),
                    "mentions_universe": report_checks.get("mentions_universe", False),
                    "mentions_bias": report_checks.get("mentions_bias", False),
                }
            ],
            [
                "path",
                "status",
                "max_report_date",
                "mentions_proxy_benchmark",
                "mentions_real_benchmark",
                "mentions_universe",
                "mentions_bias",
            ],
        ),
        "",
        "## 偏差披露",
        "",
        "- 当前固定快照池不是 PIT 股票池，存在幸存者偏差。",
        "- 当前 benchmark 若未返回真实 `hs300_index` available，只能称为代理基准，不能声明真实沪深300超额收益。",
        "- 当前样本必须扣除未来收益 horizon 后再进入因子研究；超出 `label_usable_end` 的日期不能生成完整未来收益标签。",
        "- 历史报告若使用晚于当前 parquet 覆盖终点的日期，应视为来自不同数据版本，不能直接作为当前数据口径下的研究依据。",
        "",
        "## 后续修复建议",
        "",
        "- 在真实 `hs300_index` 可用前，实验报告字段使用 `vs proxy_baseline`，不要写成 `vs hs300_index`。",
        "- 因子研究默认使用 `label_usable_start` 至 `label_usable_end`，并在报告里展示未来收益 horizon。",
        "- 接入 PIT 成分前，所有结论必须保留固定快照池和幸存者偏差说明。",
        "",
    ]
    metadata = benchmark_summary.get("metadata")
    if metadata:
        lines.extend(["## Benchmark Metadata", "", "```json", _json_like(metadata), "```", ""])
    return "\n".join(lines)


def render_issue_list(issues: list[AuditIssue]) -> str:
    if not issues:
        return "- 未发现阻断项或警告项。"
    return "\n".join(f"- **{issue.severity}** `{issue.check}`：{issue.message}" for issue in issues)


def render_quality_table(rows: list[dict[str, str]]) -> str:
    if not rows:
        return "未读取到质量报告 CSV。"
    fields = [
        "dataset",
        "coverage_start",
        "coverage_end",
        "missing_rate",
        "duplicate_record_count",
        "abnormal_price_count",
        "quality_status",
        "adjustment_policy",
        "is_pit_universe",
    ]
    return markdown_table(rows, fields)


def markdown_table(rows: list[dict[str, Any]], fields: list[str]) -> str:
    header = "| " + " | ".join(fields) + " |"
    sep = "| " + " | ".join("---" for _ in fields) + " |"
    body = ["| " + " | ".join(format_value(row.get(field, "")) for field in fields) + " |" for row in rows]
    return "\n".join([header, sep, *body])


def format_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float):
        return f"{value:.6f}"
    if isinstance(value, list):
        return ", ".join(str(item) for item in value)
    return str(value).replace("\n", " ")


def _json_like(value: Any, indent: int = 0) -> str:
    prefix = " " * indent
    if isinstance(value, dict):
        if not value:
            return "{}"
        lines = ["{"]
        items = list(value.items())
        for index, (key, item) in enumerate(items):
            comma = "," if index < len(items) - 1 else ""
            lines.append(f'{prefix}  "{key}": {_json_like(item, indent + 2)}{comma}')
        lines.append(prefix + "}")
        return "\n".join(lines)
    if isinstance(value, list):
        return "[" + ", ".join(_json_like(item, indent) for item in value) + "]"
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    return '"' + str(value).replace('"', '\\"') + '"'


if __name__ == "__main__":
    main()
