"""第三章真实数据 readiness 审计工具。"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from market_data.contracts import SCHEMA_VERSION


CHAPTER3_START_DATE = "2000-01-01"
CHAPTER3_END_DATE = "2019-12-31"

REQUIRED_CANONICAL_DATASETS: tuple[str, ...] = (
    "prices",
    "adj_factor",
    "trade_calendar",
    "stock_basic",
    "trade_status",
    "prices_limit",
    "events",
    "market_cap",
    "liquidity_capacity",
)

TRADING_DAY_DATASETS: tuple[str, ...] = (
    "prices",
    "adj_factor",
    "prices_hfq",
    "trade_status",
    "prices_limit",
    "market_cap",
    "liquidity_capacity",
)

FINANCIAL_PIT_DATASET_CANDIDATES: tuple[str, ...] = (
    "income",
    "income_statement",
    "balancesheet",
    "balance_sheet",
    "cashflow",
    "cash_flow",
    "fina_indicator",
    "financials",
    "financial_pit",
)

HFQ_DATASET_CANDIDATES: tuple[str, ...] = (
    "prices_hfq",
    "hfq_prices",
)

PASS = "PASS"
PASS_WITH_LIMITATIONS = "PASS_WITH_LIMITATIONS"
BLOCKED = "BLOCKED"
MISSING = "MISSING"


@dataclass(frozen=True, slots=True)
class DatasetRunCoverage:
    """单个 canonical run 的轻量覆盖摘要。"""

    dataset: str
    run_id: str
    path: str
    row_count: int = 0
    columns: tuple[str, ...] = ()
    start_date: str = ""
    end_date: str = ""
    issues: tuple[str, ...] = ()

    @property
    def has_rows(self) -> bool:
        return self.row_count > 0


@dataclass(frozen=True, slots=True)
class DatasetReadiness:
    """单个数据集对第三章目标窗口的 readiness 结果。"""

    dataset: str
    status: str
    target_start: str
    target_end: str
    aggregate_start: str = ""
    aggregate_end: str = ""
    row_count: int = 0
    run_ids: tuple[str, ...] = ()
    missing_reason: str = ""
    limitations: tuple[str, ...] = ()
    required_columns_missing: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "dataset": self.dataset,
            "status": self.status,
            "target_start": self.target_start,
            "target_end": self.target_end,
            "aggregate_start": self.aggregate_start,
            "aggregate_end": self.aggregate_end,
            "row_count": self.row_count,
            "run_ids": list(self.run_ids),
            "missing_reason": self.missing_reason,
            "limitations": list(self.limitations),
            "required_columns_missing": list(self.required_columns_missing),
        }


@dataclass(frozen=True, slots=True)
class Chapter3ReadinessReport:
    """第三章真实数据 readiness 报告。"""

    lake_root: str
    target_start: str
    target_end: str
    status: str
    datasets: tuple[DatasetReadiness, ...]
    hfq_status: str
    hfq_reason: str
    financial_pit_status: str
    financial_pit_reason: str
    source_limitations: tuple[str, ...] = ()
    operation_counts: Mapping[str, int] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_name": "chapter3.real_data_readiness.v1",
            "lake_root": self.lake_root,
            "target_start": self.target_start,
            "target_end": self.target_end,
            "status": self.status,
            "datasets": [item.to_dict() for item in self.datasets],
            "hfq_status": self.hfq_status,
            "hfq_reason": self.hfq_reason,
            "financial_pit_status": self.financial_pit_status,
            "financial_pit_reason": self.financial_pit_reason,
            "source_limitations": list(self.source_limitations),
            "operation_counts": dict(self.operation_counts),
        }


def build_chapter3_readiness_report(
    lake_root: str | Path,
    *,
    target_start: str = CHAPTER3_START_DATE,
    target_end: str = CHAPTER3_END_DATE,
    datasets: Sequence[str] = REQUIRED_CANONICAL_DATASETS,
) -> Chapter3ReadinessReport:
    """扫描 canonical lake，生成第三章真实数据 readiness 报告。"""

    root = Path(lake_root)
    first_open_date = discover_first_open_date(root, target_start=target_start, target_end=target_end)
    dataset_results = tuple(
        evaluate_dataset_readiness(
            collect_dataset_runs(root, dataset),
            dataset=dataset,
            target_start=first_open_date if dataset in TRADING_DAY_DATASETS and first_open_date else target_start,
            target_end=target_end,
        )
        for dataset in datasets
    )
    discovered = set(discover_canonical_datasets(root))
    hfq_status, hfq_reason = evaluate_hfq_readiness(
        discovered,
        dataset_results,
        target_start=target_start,
        target_end=target_end,
    )
    financial_status, financial_reason = evaluate_financial_pit_readiness(discovered)
    statuses = [item.status for item in dataset_results] + [hfq_status, financial_status]
    if any(status == BLOCKED or status == MISSING for status in statuses):
        status = BLOCKED
    elif any(status == PASS_WITH_LIMITATIONS for status in statuses):
        status = PASS_WITH_LIMITATIONS
    else:
        status = PASS
    return Chapter3ReadinessReport(
        lake_root=str(root),
        target_start=target_start,
        target_end=target_end,
        status=status,
        datasets=dataset_results,
        hfq_status=hfq_status,
        hfq_reason=hfq_reason,
        financial_pit_status=financial_status,
        financial_pit_reason=financial_reason,
        source_limitations=(
            "Tushare 财务接口通常提供公告日/报告期字段；若源端不提供完整 revision/as-of 链，需要在实证报告中降级为公告日 PIT 并显式披露。",
        ),
        operation_counts={
            "credential_read": 0,
            "provider_fetch": 0,
            "lake_write": 0,
            "catalog_current_pointer_publish": 0,
            "qmt_operation": 0,
            "simulation_or_live_run": 0,
        },
    )


def discover_canonical_datasets(lake_root: str | Path) -> tuple[str, ...]:
    root = Path(lake_root) / "canonical"
    if not root.exists():
        return ()
    return tuple(sorted(item.name for item in root.iterdir() if item.is_dir()))


def discover_first_open_date(
    lake_root: str | Path,
    *,
    target_start: str,
    target_end: str,
) -> str:
    runs = collect_dataset_runs(lake_root, "trade_calendar")
    first_open = ""
    for run in runs:
        for path in sorted(Path(run.path).rglob("*.parquet")):
            try:
                import pandas as pd

                frame = pd.read_parquet(path, columns=["trade_date", "is_open"])
            except Exception:
                continue
            frame["trade_date"] = frame["trade_date"].astype(str)
            open_frame = frame[
                (frame["trade_date"] >= target_start)
                & (frame["trade_date"] <= target_end)
                & frame["is_open"].astype(bool)
            ]
            if open_frame.empty:
                continue
            value = str(open_frame["trade_date"].min())
            first_open = value if not first_open else min(first_open, value)
    return first_open


def collect_dataset_runs(lake_root: str | Path, dataset: str) -> tuple[DatasetRunCoverage, ...]:
    dataset_root = Path(lake_root) / "canonical" / dataset / SCHEMA_VERSION
    if not dataset_root.exists():
        return ()
    results: list[DatasetRunCoverage] = []
    for run_dir in sorted(dataset_root.glob("run_id=*")):
        if not run_dir.is_dir():
            continue
        parquet_paths = tuple(sorted(run_dir.rglob("*.parquet")))
        if not parquet_paths:
            results.append(
                DatasetRunCoverage(
                    dataset=dataset,
                    run_id=run_dir.name.removeprefix("run_id="),
                    path=str(run_dir),
                    issues=("no_parquet_files",),
                )
            )
            continue
        results.append(_summarize_parquet_run(dataset, run_dir, parquet_paths))
    return tuple(results)


def evaluate_dataset_readiness(
    runs: Sequence[DatasetRunCoverage],
    *,
    dataset: str,
    target_start: str,
    target_end: str,
) -> DatasetReadiness:
    if not runs:
        return DatasetReadiness(
            dataset=dataset,
            status=MISSING,
            target_start=target_start,
            target_end=target_end,
            missing_reason="canonical_dataset_missing",
        )
    usable = [run for run in runs if run.has_rows]
    if not usable:
        return DatasetReadiness(
            dataset=dataset,
            status=MISSING,
            target_start=target_start,
            target_end=target_end,
            run_ids=tuple(run.run_id for run in runs),
            missing_reason="canonical_dataset_has_no_rows",
        )
    start_values = [run.start_date for run in usable if run.start_date]
    end_values = [run.end_date for run in usable if run.end_date]
    aggregate_start = min(start_values) if start_values else ""
    aggregate_end = max(end_values) if end_values else ""
    row_count = sum(run.row_count for run in usable)
    run_ids = tuple(run.run_id for run in usable)
    if aggregate_start and aggregate_end and aggregate_start <= target_start and aggregate_end >= target_end:
        status = PASS
        reason = ""
    else:
        status = BLOCKED
        reason = "target_window_not_covered"
    return DatasetReadiness(
        dataset=dataset,
        status=status,
        target_start=target_start,
        target_end=target_end,
        aggregate_start=aggregate_start,
        aggregate_end=aggregate_end,
        row_count=row_count,
        run_ids=run_ids,
        missing_reason=reason,
        limitations=tuple(sorted({issue for run in usable for issue in run.issues})),
    )


def evaluate_hfq_readiness(
    discovered_datasets: Iterable[str],
    dataset_results: Sequence[DatasetReadiness],
    *,
    target_start: str,
    target_end: str,
) -> tuple[str, str]:
    discovered = set(discovered_datasets)
    if discovered.intersection(HFQ_DATASET_CANDIDATES):
        return PASS, "已有后复权 canonical dataset。"
    by_dataset = {item.dataset: item for item in dataset_results}
    prices = by_dataset.get("prices")
    adj_factor = by_dataset.get("adj_factor")
    if prices and adj_factor and prices.status == PASS and adj_factor.status == PASS:
        return PASS_WITH_LIMITATIONS, (
            "未发现独立 prices_hfq canonical dataset，但 raw prices + adj_factor 覆盖目标窗口，"
            "可在 CR-034 内派生第三章专用 hfq candidate。"
        )
    return BLOCKED, (
        f"未发现 prices_hfq；且 raw prices/adj_factor 尚未共同覆盖 {target_start}..{target_end}，"
        "不能派生完整第三章后复权视图。"
    )


def evaluate_financial_pit_readiness(discovered_datasets: Iterable[str]) -> tuple[str, str]:
    discovered = set(discovered_datasets)
    matched = sorted(discovered.intersection(FINANCIAL_PIT_DATASET_CANDIDATES))
    if not matched:
        return BLOCKED, (
            "未发现 income/balance/cashflow/fina_indicator/financial_pit 等 canonical 财务 PIT 数据集。"
        )
    return PASS_WITH_LIMITATIONS, (
        "发现财务候选数据集 "
        + ", ".join(matched)
        + "；仍需逐字段审计 ann_date/report_period/update_flag/revision/as_of。"
    )


def render_readiness_markdown(report: Chapter3ReadinessReport) -> str:
    lines = [
        "# CR-034 第三章真实数据 Readiness Report",
        "",
        f"- status: `{report.status}`",
        f"- target_window: `{report.target_start}`..`{report.target_end}`",
        f"- lake_root: `{report.lake_root}`",
        "- catalog_current_pointer_publish: `0`",
        "- qmt_operation: `0`",
        "- simulation_or_live_run: `0`",
        "",
        "## Dataset Coverage",
        "",
        "| dataset | status | aggregate_start | aggregate_end | rows | missing_reason | run_count |",
        "|---|---|---|---|---:|---|---:|",
    ]
    for item in report.datasets:
        lines.append(
            "| `{dataset}` | `{status}` | `{start}` | `{end}` | {rows} | `{reason}` | {runs} |".format(
                dataset=item.dataset,
                status=item.status,
                start=item.aggregate_start or "",
                end=item.aggregate_end or "",
                rows=item.row_count,
                reason=item.missing_reason or "",
                runs=len(item.run_ids),
            )
        )
    lines.extend(
        [
            "",
            "## Blocking Gates",
            "",
            f"- hfq_status: `{report.hfq_status}`",
            f"- hfq_reason: {report.hfq_reason}",
            f"- financial_pit_status: `{report.financial_pit_status}`",
            f"- financial_pit_reason: {report.financial_pit_reason}",
            "",
            "## Source Limitations",
            "",
        ]
    )
    for limitation in report.source_limitations:
        lines.append(f"- {limitation}")
    lines.extend(
        [
            "",
            "## Operation Counts",
            "",
            "| operation | count |",
            "|---|---:|",
        ]
    )
    for key, value in sorted(report.operation_counts.items()):
        lines.append(f"| `{key}` | {value} |")
    lines.append("")
    return "\n".join(lines)


def write_readiness_report(report: Chapter3ReadinessReport, output_dir: str | Path) -> tuple[Path, Path]:
    root = Path(output_dir)
    root.mkdir(parents=True, exist_ok=True)
    json_path = root / "READINESS-REPORT.json"
    md_path = root / "READINESS-REPORT.md"
    json_path.write_text(json.dumps(report.to_dict(), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md_path.write_text(render_readiness_markdown(report), encoding="utf-8")
    return json_path, md_path


def _summarize_parquet_run(
    dataset: str,
    run_dir: Path,
    parquet_paths: Sequence[Path],
) -> DatasetRunCoverage:
    columns: set[str] = set()
    row_count = 0
    min_date = ""
    max_date = ""
    issues: list[str] = []
    for path in parquet_paths:
        summary = _parquet_file_summary(path)
        row_count += int(summary.get("row_count") or 0)
        columns.update(str(item) for item in summary.get("columns") or ())
        file_min = str(summary.get("min_date") or "")
        file_max = str(summary.get("max_date") or "")
        if file_min:
            min_date = file_min if not min_date else min(min_date, file_min)
        if file_max:
            max_date = file_max if not max_date else max(max_date, file_max)
        issues.extend(str(item) for item in summary.get("issues") or ())
    return DatasetRunCoverage(
        dataset=dataset,
        run_id=run_dir.name.removeprefix("run_id="),
        path=str(run_dir),
        row_count=row_count,
        columns=tuple(sorted(columns)),
        start_date=min_date,
        end_date=max_date,
        issues=tuple(sorted(set(issues))),
    )


def _parquet_file_summary(path: Path) -> dict[str, Any]:
    try:
        import pyarrow.parquet as pq
    except Exception:
        return _parquet_file_summary_pandas(path)
    try:
        parquet_file = pq.ParquetFile(path)
        row_count = parquet_file.metadata.num_rows
        columns = tuple(parquet_file.schema_arrow.names)
        date_column = _date_column(columns)
        if not date_column:
            return {"row_count": row_count, "columns": columns, "issues": ("date_column_missing",)}
        min_date = ""
        max_date = ""
        column_index = columns.index(date_column)
        for group_index in range(parquet_file.metadata.num_row_groups):
            column = parquet_file.metadata.row_group(group_index).column(column_index)
            stats = column.statistics
            if stats is None or stats.min is None or stats.max is None:
                return _parquet_file_summary_pandas(path)
            group_min = _normalize_date_value(stats.min)
            group_max = _normalize_date_value(stats.max)
            if group_min:
                min_date = group_min if not min_date else min(min_date, group_min)
            if group_max:
                max_date = group_max if not max_date else max(max_date, group_max)
        return {"row_count": row_count, "columns": columns, "min_date": min_date, "max_date": max_date, "issues": ()}
    except Exception as exc:
        return {"row_count": 0, "columns": (), "issues": (f"parquet_summary_failed:{exc.__class__.__name__}",)}


def _parquet_file_summary_pandas(path: Path) -> dict[str, Any]:
    try:
        import pandas as pd

        frame = pd.read_parquet(path)
    except Exception as exc:
        return {"row_count": 0, "columns": (), "issues": (f"parquet_read_failed:{exc.__class__.__name__}",)}
    columns = tuple(str(item) for item in frame.columns)
    date_column = _date_column(columns)
    if not date_column or frame.empty:
        return {"row_count": len(frame), "columns": columns, "issues": ("date_column_missing",)}
    values = frame[date_column].dropna().map(_normalize_date_value)
    values = values[values != ""]
    return {
        "row_count": len(frame),
        "columns": columns,
        "min_date": values.min() if len(values) else "",
        "max_date": values.max() if len(values) else "",
        "issues": (),
    }


def _date_column(columns: Sequence[str]) -> str:
    for name in ("trade_date", "event_date", "available_at", "ann_date", "end_date", "report_period", "cal_date"):
        if name in columns:
            return name
    return ""


def _normalize_date_value(value: Any) -> str:
    text = str(value).strip()
    if not text:
        return ""
    if len(text) >= 10 and text[4] == "-" and text[7] == "-":
        return text[:10]
    if len(text) == 8 and text.isdigit():
        return f"{text[:4]}-{text[4:6]}-{text[6:8]}"
    return text[:10]


__all__ = [
    "BLOCKED",
    "CHAPTER3_END_DATE",
    "CHAPTER3_START_DATE",
    "MISSING",
    "PASS",
    "PASS_WITH_LIMITATIONS",
    "Chapter3ReadinessReport",
    "DatasetReadiness",
    "DatasetRunCoverage",
    "build_chapter3_readiness_report",
    "collect_dataset_runs",
    "discover_canonical_datasets",
    "discover_first_open_date",
    "evaluate_dataset_readiness",
    "evaluate_financial_pit_readiness",
    "evaluate_hfq_readiness",
    "render_readiness_markdown",
    "write_readiness_report",
]
