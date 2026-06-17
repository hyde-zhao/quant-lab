"""标准化 parquet 与 manifest 的数据质量计算和报告渲染。"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
import csv
import json
from typing import Any

import pandas as pd

from engine.contracts import (
    DATASET_NAMES,
    DATASET_REQUIRED_COLUMNS,
    DEFAULT_ADJUSTMENT_POLICY,
    DEFAULT_AVAILABLE_AT_RULE,
    QUALITY_REPORT_FIELDS,
    QUALITY_REPORT_FORMATS,
    QUALITY_REPORT_SCHEMA_VERSION,
    QUALITY_STATUS_VALUES,
    STANDARD_PARQUET_FILES,
    SURVIVORSHIP_BIAS_NOTE,
)
from engine.manifest import ManifestError, ManifestFormatError, ManifestStore
from engine.research_paths import research_report_path
from engine.source_registry import require_resolved_registry_key, SourceRegistryError


class QualityError(Exception):
    """质量报告基础异常。"""


class QualityManifestError(QualityError):
    """manifest 读取或解析失败。"""


class ParquetReadError(QualityError):
    """parquet 读取失败。"""


class QualityReportWriteError(QualityError):
    """质量报告写入失败。"""


class QualitySourceRegistryError(QualityError):
    """增强数据质量路径的 source/interface 未解析。"""


@dataclass(slots=True)
class QualitySummary:
    records: list[dict[str, Any]]
    quality_status: str
    manifest_run_id: str
    source_manifest_path: str


@dataclass(slots=True)
class QualityReportResult:
    csv_path: str
    markdown_path: str
    quality_status: str
    manifest_run_id: str


def normalize_quality_status(value: Any) -> str:
    """归一化 reader/catalog/metadata 传入的质量状态。"""

    if value is None:
        return "missing"
    text = str(value).strip().lower()
    if not text or text in {"unknown", "none", "null", "na", "n/a", "not_evaluated"}:
        return "missing"
    if text in {"pass", "passed", "ok", "available", "success"}:
        return "pass"
    if text in {"warn", "warning", "quality_warn", "available_with_warnings"}:
        return "warn"
    if text in {"fail", "failed", "quality_failed", "error"}:
        return "fail"
    if text in {"missing", "required_missing", "unavailable", "lineage_missing", "invalid_request"}:
        return "missing"
    return "missing"


def quality_status_from_reader_result(result: Any, metadata: dict[str, Any] | None = None) -> tuple[str, str]:
    """从 reader/catalog/metadata 提取质量状态与来源，不读取任何报告文件。"""

    if result is not None:
        raw_reader_status = str(getattr(result, "status", "") or "").strip().lower()
        reader_status = normalize_quality_status(raw_reader_status)
        if reader_status == "fail":
            return "fail", "reader_result"
        if raw_reader_status in {"required_missing", "unavailable", "lineage_missing", "invalid_request"}:
            return "missing", "reader_result"
        issues = getattr(result, "issues", None) or []
        if _issues_contain_quality_warn(issues):
            return "warn", "reader_result"
        catalog_entry = getattr(result, "catalog_entry", None)
        if catalog_entry is not None:
            catalog_status = normalize_quality_status(getattr(catalog_entry, "quality_status", None))
            if catalog_status != "missing":
                return catalog_status, "catalog_entry"

    raw_metadata = metadata or {}
    if isinstance(raw_metadata, dict):
        quality = raw_metadata.get("quality")
        if isinstance(quality, dict):
            quality_status = normalize_quality_status(quality.get("quality_status") or quality.get("status"))
            if quality_status != "missing":
                return quality_status, "metadata"
        quality_status = normalize_quality_status(raw_metadata.get("quality_status"))
        if quality_status != "missing":
            return quality_status, "metadata"
    return "missing", "missing"


def load_manifest_records(manifest_path: str | Path) -> list[dict[str, Any]]:
    """读取 manifest JSONL；损坏行结构化暴露路径与行号。"""

    try:
        return list(ManifestStore(manifest_path).iter_records())
    except ManifestFormatError as exc:
        raise QualityManifestError(str(exc)) from exc
    except ManifestError as exc:
        raise QualityManifestError(f"manifest 读取失败: {manifest_path}: {exc}") from exc


def calculate_quality(
    parquet_paths: dict[str, str | Path],
    manifest_path: str | Path,
    requested_range: dict[str, str] | tuple[str, str],
    as_of_date: str | date | datetime,
) -> QualitySummary:
    """计算三类 parquet 的质量指标与整体 `pass/warn/fail`。"""

    requested_start, requested_end = _coerce_requested_range(requested_range)
    as_of = _to_date(as_of_date)
    manifest_records = load_manifest_records(manifest_path)
    latest_records = _latest_manifest_records(manifest_records)
    manifest_run_ids = sorted(
        {
            str(record.get("run_id"))
            for record in latest_records
            if record.get("run_id")
        }
    )
    manifest_run_id = ",".join(manifest_run_ids)
    failed_batches = [
        record for record in latest_records if str(record.get("status") or "") == "failed"
    ]
    failed_symbol_dates = _failed_symbol_dates(failed_batches)
    last_successful_update_at = _last_successful_update_at(latest_records)
    standardized_output_paths = {
        dataset: str(parquet_paths.get(dataset, ""))
        for dataset in DATASET_NAMES
    }

    frames: dict[str, pd.DataFrame] = {}
    schema_errors: dict[str, list[str]] = {}
    for dataset in DATASET_NAMES:
        path = parquet_paths.get(dataset)
        if not path:
            frames[dataset] = pd.DataFrame()
            schema_errors[dataset] = list(DATASET_REQUIRED_COLUMNS[dataset])
            continue
        try:
            frame = pd.read_parquet(path, engine="pyarrow")
        except Exception as exc:
            raise ParquetReadError(f"parquet 读取失败: {path}: {exc}") from exc
        frames[dataset] = frame
        schema_errors[dataset] = _missing_required_columns(dataset, frame)

    prices = _prepare_prices(frames["prices"]) if not frames["prices"].empty else pd.DataFrame()
    index_members = (
        _prepare_index_members(frames["index_members"])
        if not frames["index_members"].empty
        else pd.DataFrame()
    )
    trade_calendar = (
        _prepare_trade_calendar(frames["trade_calendar"])
        if not frames["trade_calendar"].empty
        else pd.DataFrame()
    )

    open_dates = _open_dates(trade_calendar, requested_start, requested_end)
    symbols = sorted(
        {
            str(symbol)
            for symbol in index_members.get("symbol", pd.Series(dtype="string")).dropna().tolist()
            if str(symbol)
        }
    )
    prices_metrics = _price_metrics(
        prices,
        open_dates,
        symbols,
        requested_start,
        requested_end,
        schema_errors["prices"],
    )
    last_success_date = _timestamp_date(last_successful_update_at)
    coverage_end = _parse_optional_date(prices_metrics["coverage_end"])
    freshness_trade_days = _freshness_trade_days(open_dates, coverage_end, requested_end)
    freshness_calendar_days = (
        max((as_of - last_success_date).days, 0) if last_success_date is not None else 0
    )

    common = {
        "report_schema_version": QUALITY_REPORT_SCHEMA_VERSION,
        "manifest_run_id": manifest_run_id,
        "requested_start": requested_start.isoformat(),
        "requested_end": requested_end.isoformat(),
        "failed_batch_count": len(failed_batches),
        "failed_symbol_dates": failed_symbol_dates,
        "last_successful_update_at": last_successful_update_at,
        "data_freshness_calendar_days": freshness_calendar_days,
        "source_manifest_path": str(manifest_path),
        "standardized_output_paths": standardized_output_paths,
    }

    dataset_records = [
        _dataset_record(
            dataset="prices",
            coverage_start=prices_metrics["coverage_start"],
            coverage_end=prices_metrics["coverage_end"],
            missing_rate=prices_metrics["missing_rate"],
            missing_required_fields=schema_errors["prices"],
            duplicate_record_count=prices_metrics["duplicate_record_count"],
            abnormal_price_count=prices_metrics["abnormal_price_count"],
            backfill_trade_days=prices_metrics["backfill_trade_days"],
            backfill_record_count=prices_metrics["backfill_record_count"],
            data_freshness_trade_days=freshness_trade_days,
            available_at_rule=_available_at_rule(prices),
            adjustment_policy=_adjustment_policy(prices),
            is_pit_universe=False,
            survivorship_bias_note=SURVIVORSHIP_BIAS_NOTE,
            common=common,
        ),
        _dataset_record(
            dataset="index_members",
            coverage_start=_coverage_from_optional_column(index_members, "snapshot_date")[0],
            coverage_end=_coverage_from_optional_column(index_members, "snapshot_date")[1],
            missing_rate=0.0,
            missing_required_fields=schema_errors["index_members"],
            duplicate_record_count=_duplicate_count(index_members, ["symbol"]),
            abnormal_price_count=0,
            backfill_trade_days=0,
            backfill_record_count=0,
            data_freshness_trade_days=0,
            available_at_rule="explicit" if _has_non_empty(index_members, "available_at") else "",
            adjustment_policy="",
            is_pit_universe=bool(
                index_members.get("is_pit_universe", pd.Series([False])).fillna(False).all()
            )
            if not index_members.empty
            else False,
            survivorship_bias_note=SURVIVORSHIP_BIAS_NOTE,
            common=common,
        ),
        _dataset_record(
            dataset="trade_calendar",
            coverage_start=_coverage_from_required_column(trade_calendar, "trade_date")[0],
            coverage_end=_coverage_from_required_column(trade_calendar, "trade_date")[1],
            missing_rate=0.0,
            missing_required_fields=schema_errors["trade_calendar"],
            duplicate_record_count=_duplicate_count(trade_calendar, ["trade_date"]),
            abnormal_price_count=0,
            backfill_trade_days=0,
            backfill_record_count=0,
            data_freshness_trade_days=0,
            available_at_rule="",
            adjustment_policy="",
            is_pit_universe=False,
            survivorship_bias_note=SURVIVORSHIP_BIAS_NOTE,
            common=common,
        ),
    ]

    for record in dataset_records:
        record["quality_status"] = _status_for_record(record, failed_batches)

    overall = dict(dataset_records[0])
    overall["dataset"] = "overall"
    overall["missing_required_fields"] = sorted(
        {
            field
            for record in dataset_records
            for field in record["missing_required_fields"]
        }
    )
    overall["duplicate_record_count"] = sum(
        int(record["duplicate_record_count"]) for record in dataset_records
    )
    overall["abnormal_price_count"] = sum(
        int(record["abnormal_price_count"]) for record in dataset_records
    )
    overall["quality_status"] = _overall_status(dataset_records, failed_batches)
    records = dataset_records + [overall]
    return QualitySummary(
        records=records,
        quality_status=overall["quality_status"],
        manifest_run_id=manifest_run_id,
        source_manifest_path=str(manifest_path),
    )


def render_quality_reports(
    summary: QualitySummary,
    csv_path: str | Path,
    markdown_path: str | Path,
) -> QualityReportResult:
    """按固定字段顺序输出 CSV 与 Markdown 报告。"""

    if "csv" not in QUALITY_REPORT_FORMATS or "markdown" not in QUALITY_REPORT_FORMATS:
        raise QualityReportWriteError("质量报告格式常量缺少 csv/markdown")
    csv_target = Path(csv_path)
    md_target = Path(markdown_path)
    _ensure_parent_dir(csv_target)
    _ensure_parent_dir(md_target)
    try:
        with csv_target.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(QUALITY_REPORT_FIELDS))
            writer.writeheader()
            for record in summary.records:
                writer.writerow(_stringify_record(record))
        lines = _markdown_table(summary.records)
        md_target.write_text("\n".join(lines) + "\n", encoding="utf-8")
    except OSError as exc:
        raise QualityReportWriteError(f"质量报告写入失败: {exc}") from exc
    return QualityReportResult(
        csv_path=str(csv_target),
        markdown_path=str(md_target),
        quality_status=summary.quality_status,
        manifest_run_id=summary.manifest_run_id,
    )


def run_quality_report(
    parquet_paths: dict[str, str | Path] | None,
    manifest_path: str | Path,
    report_dir: str | Path = research_report_path(),
    requested_range: dict[str, str] | tuple[str, str] | None = None,
    as_of_date: str | date | datetime | None = None,
) -> QualityReportResult:
    """计算并渲染默认 `data_quality_report.csv/.md`。"""

    effective_paths = parquet_paths or {
        dataset: Path("data") / filename
        for dataset, filename in STANDARD_PARQUET_FILES.items()
    }
    effective_range = requested_range or _requested_range_from_manifest(manifest_path)
    effective_as_of = as_of_date or date.today()
    summary = calculate_quality(
        effective_paths,
        manifest_path,
        effective_range,
        effective_as_of,
    )
    target_dir = Path(report_dir)
    return render_quality_reports(
        summary,
        target_dir / "data_quality_report.csv",
        target_dir / "data_quality_report.md",
    )


def validate_quality_enhancement_registry(*, pit_universe: bool = False, trade_status: bool = False, limits: bool = False, events: bool = False) -> None:
    """质量增强路径启用前校验 source/interface 注册表。"""

    keys: list[str] = []
    if pit_universe:
        keys.append("index_members_pit")
    if trade_status:
        keys.append("trade_status")
    if limits:
        keys.append("prices_limit")
    if events:
        keys.append("events")
    try:
        for key in keys:
            require_resolved_registry_key(key)
    except SourceRegistryError as exc:
        raise QualitySourceRegistryError(str(exc)) from exc


def _dataset_record(
    *,
    dataset: str,
    coverage_start: str,
    coverage_end: str,
    missing_rate: float,
    missing_required_fields: list[str],
    duplicate_record_count: int,
    abnormal_price_count: int,
    backfill_trade_days: int,
    backfill_record_count: int,
    data_freshness_trade_days: int,
    available_at_rule: str,
    adjustment_policy: str,
    is_pit_universe: bool,
    survivorship_bias_note: str,
    common: dict[str, Any],
) -> dict[str, Any]:
    record = {
        **common,
        "dataset": dataset,
        "coverage_start": coverage_start,
        "coverage_end": coverage_end,
        "missing_rate": round(float(missing_rate), 6),
        "missing_required_fields": missing_required_fields,
        "duplicate_record_count": int(duplicate_record_count),
        "abnormal_price_count": int(abnormal_price_count),
        "backfill_trade_days": int(backfill_trade_days),
        "backfill_record_count": int(backfill_record_count),
        "data_freshness_trade_days": int(data_freshness_trade_days),
        "quality_status": "pass",
        "available_at_rule": available_at_rule,
        "adjustment_policy": adjustment_policy,
        "is_pit_universe": bool(is_pit_universe),
        "survivorship_bias_note": survivorship_bias_note,
    }
    return {field: record.get(field, "") for field in QUALITY_REPORT_FIELDS}


def _status_for_record(record: dict[str, Any], failed_batches: list[dict[str, Any]]) -> str:
    if (
        record["missing_required_fields"]
        or int(record["duplicate_record_count"]) > 0
        or int(record["abnormal_price_count"]) > 0
        or float(record["missing_rate"]) > 0.05
        or _coverage_gap(record)
    ):
        return "fail"
    if 0 < float(record["missing_rate"]) <= 0.05:
        return "warn"
    if failed_batches:
        return "warn"
    return "pass"


def _overall_status(records: list[dict[str, Any]], failed_batches: list[dict[str, Any]]) -> str:
    statuses = [record["quality_status"] for record in records]
    if "fail" in statuses:
        return "fail"
    if "warn" in statuses or failed_batches:
        return "warn"
    return "pass"


def _issues_contain_quality_warn(issues: list[Any]) -> bool:
    for issue in issues:
        if isinstance(issue, dict):
            code = str(issue.get("code") or "").lower()
        else:
            code = str(getattr(issue, "code", "") or "").lower()
        if code in {"quality_warn", "quality_warning", "input_quality_warn", "quality_warn_blocked"}:
            return True
    return False


def _coverage_gap(record: dict[str, Any]) -> bool:
    if record["dataset"] not in {"prices", "trade_calendar"}:
        return False
    start = _parse_optional_date(record["coverage_start"])
    end = _parse_optional_date(record["coverage_end"])
    requested_start = _to_date(record["requested_start"])
    requested_end = _to_date(record["requested_end"])
    if start is None or end is None:
        return True
    return start > requested_start or end < requested_end


def _prepare_prices(frame: pd.DataFrame) -> pd.DataFrame:
    prepared = frame.copy()
    if "trade_date" in prepared:
        prepared["trade_date"] = pd.to_datetime(prepared["trade_date"], errors="coerce").dt.date
    if "close" in prepared:
        prepared["close"] = pd.to_numeric(prepared["close"], errors="coerce")
    if "symbol" in prepared:
        prepared["symbol"] = prepared["symbol"].astype("string").str.strip()
    return prepared


def _prepare_index_members(frame: pd.DataFrame) -> pd.DataFrame:
    prepared = frame.copy()
    if "symbol" in prepared:
        prepared["symbol"] = prepared["symbol"].astype("string").str.strip()
    if "snapshot_date" in prepared:
        prepared["snapshot_date"] = pd.to_datetime(
            prepared["snapshot_date"],
            errors="coerce",
        ).dt.date
    if "is_pit_universe" not in prepared:
        prepared["is_pit_universe"] = False
    return prepared


def _prepare_trade_calendar(frame: pd.DataFrame) -> pd.DataFrame:
    prepared = frame.copy()
    if "trade_date" in prepared:
        prepared["trade_date"] = pd.to_datetime(prepared["trade_date"], errors="coerce").dt.date
    if "is_open" not in prepared:
        prepared["is_open"] = True
    else:
        prepared["is_open"] = prepared["is_open"].fillna(True).astype(bool)
    return prepared


def _price_metrics(
    prices: pd.DataFrame,
    open_dates: list[date],
    symbols: list[str],
    requested_start: date,
    requested_end: date,
    schema_errors: list[str],
) -> dict[str, Any]:
    if prices.empty or schema_errors:
        denominator = max(len(open_dates) * len(symbols), 1)
        trade_dates = (
            _safe_date_series(prices, "trade_date")
            if "trade_date" in prices
            else pd.Series(dtype=object)
        )
        coverage = _coverage_from_series(trade_dates)
        duplicate_keys = [
            key for key in ("trade_date", "symbol") if key in prices.columns
        ]
        duplicate_count = (
            _duplicate_count(prices, duplicate_keys)
            if len(duplicate_keys) == 2
            else 0
        )
        return {
            "coverage_start": coverage[0],
            "coverage_end": coverage[1],
            "missing_rate": 1.0,
            "duplicate_record_count": duplicate_count,
            "abnormal_price_count": 0,
            "backfill_trade_days": 0,
            "backfill_record_count": 0,
            "missing_points": denominator,
        }
    in_range = prices[
        (prices["trade_date"] >= requested_start) & (prices["trade_date"] <= requested_end)
    ].copy()
    coverage = _coverage_from_required_column(prices, "trade_date")
    duplicate_count = _duplicate_count(prices, ["trade_date", "symbol"])
    abnormal_price_count = int((prices["close"].notna() & (prices["close"] <= 0)).sum())
    denominator = len(open_dates) * len(symbols)
    if denominator <= 0:
        missing_points = 1
        missing_rate = 1.0
    else:
        present = set(
            zip(
                in_range["trade_date"],
                in_range["symbol"].astype(str),
                strict=False,
            )
        )
        missing_pairs = {
            (trade_date, symbol)
            for trade_date in open_dates
            for symbol in symbols
            if (trade_date, symbol) not in present
        }
        close_missing = int(
            in_range[["trade_date", "symbol", "close"]]
            .drop_duplicates(subset=["trade_date", "symbol"])
            ["close"]
            .isna()
            .sum()
        )
        missing_points = len(missing_pairs) + close_missing
        missing_rate = missing_points / denominator
    recent_dates = open_dates[-5:]
    backfill_records = int(in_range[in_range["trade_date"].isin(recent_dates)].shape[0])
    return {
        "coverage_start": coverage[0],
        "coverage_end": coverage[1],
        "missing_rate": missing_rate,
        "duplicate_record_count": duplicate_count,
        "abnormal_price_count": abnormal_price_count,
        "backfill_trade_days": len(recent_dates),
        "backfill_record_count": backfill_records,
        "missing_points": missing_points,
    }


def _open_dates(calendar: pd.DataFrame, requested_start: date, requested_end: date) -> list[date]:
    if calendar.empty or "trade_date" not in calendar:
        return []
    mask = (
        (calendar["trade_date"] >= requested_start)
        & (calendar["trade_date"] <= requested_end)
        & calendar.get("is_open", pd.Series(True, index=calendar.index)).fillna(True).astype(bool)
    )
    return sorted(calendar.loc[mask, "trade_date"].dropna().unique().tolist())


def _freshness_trade_days(
    open_dates: list[date],
    coverage_end: date | None,
    requested_end: date,
) -> int:
    if coverage_end is None:
        return len(open_dates)
    return sum(1 for item in open_dates if coverage_end < item <= requested_end)


def _missing_required_columns(dataset: str, frame: pd.DataFrame) -> list[str]:
    return [
        f"{dataset}.{column}"
        for column in DATASET_REQUIRED_COLUMNS[dataset]
        if column not in frame.columns
    ]


def _coverage_from_required_column(frame: pd.DataFrame, column: str) -> tuple[str, str]:
    if frame.empty or column not in frame:
        return "", ""
    values = pd.Series(frame[column]).dropna()
    return _coverage_from_series(values)


def _coverage_from_series(values: pd.Series) -> tuple[str, str]:
    values = values.dropna()
    if values.empty:
        return "", ""
    return min(values).isoformat(), max(values).isoformat()


def _safe_date_series(frame: pd.DataFrame, column: str) -> pd.Series:
    values = pd.to_datetime(frame[column], errors="coerce").dt.date
    return pd.Series(values)


def _coverage_from_optional_column(frame: pd.DataFrame, column: str) -> tuple[str, str]:
    if frame.empty or column not in frame:
        return "", ""
    values = pd.Series(frame[column]).dropna()
    if values.empty:
        return "", ""
    return min(values).isoformat(), max(values).isoformat()


def _duplicate_count(frame: pd.DataFrame, keys: list[str]) -> int:
    if frame.empty or any(key not in frame.columns for key in keys):
        return 0
    return int(frame.duplicated(subset=keys, keep=False).sum())


def _has_non_empty(frame: pd.DataFrame, column: str) -> bool:
    return (
        not frame.empty
        and column in frame.columns
        and frame[column].fillna("").astype(str).str.len().gt(0).any()
    )


def _available_at_rule(prices: pd.DataFrame) -> str:
    if _has_non_empty(prices, "available_at"):
        return "explicit"
    return DEFAULT_AVAILABLE_AT_RULE


def _adjustment_policy(prices: pd.DataFrame) -> str:
    if prices.empty or "adjustment_policy" not in prices:
        return DEFAULT_ADJUSTMENT_POLICY
    policies = sorted(
        {
            str(value)
            for value in prices["adjustment_policy"].fillna(DEFAULT_ADJUSTMENT_POLICY).unique()
            if str(value)
        }
    )
    return policies[0] if len(policies) == 1 else ",".join(policies)


def _failed_symbol_dates(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for record in records:
        failed_items = record.get("failed_items") or []
        if not isinstance(failed_items, list):
            failed_items = [failed_items]
        for item in failed_items:
            if isinstance(item, dict):
                output.append(item)
            else:
                output.append(
                    {
                        "item": item,
                        "coverage_start": record.get("coverage_start", ""),
                        "coverage_end": record.get("coverage_end", ""),
                    }
                )
    return output


def _last_successful_update_at(records: list[dict[str, Any]]) -> str:
    candidates = [
        str(record.get("completed_at") or record.get("request_finished_at") or "")
        for record in records
        if str(record.get("status") or "") in {"success", "partial_success", "skipped"}
    ]
    return max([value for value in candidates if value], default="")


def _timestamp_date(value: str) -> date | None:
    if not value:
        return None
    text = value.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(text).date()
    except ValueError:
        return _parse_optional_date(value)


def _coerce_requested_range(
    requested_range: dict[str, str] | tuple[str, str],
) -> tuple[date, date]:
    if isinstance(requested_range, dict):
        start = requested_range.get("start") or requested_range.get("requested_start")
        end = requested_range.get("end") or requested_range.get("requested_end")
    else:
        start, end = requested_range
    if not start or not end:
        raise QualityError("requested_range 必须包含 start/end")
    return _to_date(start), _to_date(end)


def _requested_range_from_manifest(manifest_path: str | Path) -> dict[str, str]:
    records = load_manifest_records(manifest_path)
    starts: list[str] = []
    ends: list[str] = []
    for record in records:
        if record.get("coverage_start"):
            starts.append(str(record["coverage_start"]))
        if record.get("coverage_end"):
            ends.append(str(record["coverage_end"]))
    if not starts or not ends:
        raise QualityError("无法从 manifest 推导 requested_range")
    return {"start": min(starts), "end": max(ends)}


def _to_date(value: str | date | datetime) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    parsed = pd.to_datetime(pd.Series([value]), errors="coerce")
    if parsed.isna().iloc[0]:
        raise QualityError(f"日期不可解析: {value!r}")
    return parsed.dt.date.iloc[0]


def _parse_optional_date(value: Any) -> date | None:
    if value in ("", None):
        return None
    try:
        return _to_date(value)
    except QualityError:
        return None


def _latest_manifest_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    latest: dict[str, dict[str, Any]] = {}
    anonymous: list[dict[str, Any]] = []
    for record in records:
        batch_id = str(record.get("batch_id") or "")
        if batch_id:
            latest[batch_id] = record
        else:
            anonymous.append(record)
    return anonymous + list(latest.values())


def _ensure_parent_dir(path: Path) -> None:
    parent = path.parent
    if not parent or str(parent) == ".":
        return
    current = Path(parent.anchor) if parent.is_absolute() else Path(".")
    parts = parent.parts[1:] if parent.is_absolute() else parent.parts
    for part in parts:
        current = current / part
        if current.exists() and not current.is_dir():
            raise QualityReportWriteError(f"安装路径被非目录占用: {current}")
    parent.mkdir(parents=True, exist_ok=True)


def _stringify_record(record: dict[str, Any]) -> dict[str, Any]:
    output: dict[str, Any] = {}
    for field in QUALITY_REPORT_FIELDS:
        value = record.get(field, "")
        if isinstance(value, (list, dict, tuple)):
            output[field] = json.dumps(value, ensure_ascii=False, sort_keys=True)
        else:
            output[field] = value
    return output


def _markdown_table(records: list[dict[str, Any]]) -> list[str]:
    lines = [
        "# 数据质量报告",
        "",
        "| " + " | ".join(QUALITY_REPORT_FIELDS) + " |",
        "| " + " | ".join("---" for _ in QUALITY_REPORT_FIELDS) + " |",
    ]
    for record in records:
        stringified = _stringify_record(record)
        values = [_escape_markdown(stringified.get(field, "")) for field in QUALITY_REPORT_FIELDS]
        lines.append("| " + " | ".join(values) + " |")
    return lines


def _escape_markdown(value: Any) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


__all__ = (
    "ParquetReadError",
    "QualityError",
    "QualityManifestError",
    "QualityReportResult",
    "QualityReportWriteError",
    "QualitySourceRegistryError",
    "QualitySummary",
    "calculate_quality",
    "load_manifest_records",
    "normalize_quality_status",
    "quality_status_from_reader_result",
    "render_quality_reports",
    "run_quality_report",
    "validate_quality_enhancement_registry",
)
