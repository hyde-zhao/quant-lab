"""阶段四真实回测前置数据湖 readiness audit。

该入口只读显式传入的 lake root，不读取 .env，不把仓库旧 data/**
作为生产覆盖证据，也不会抓取、补数或写入真实 lake。
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import sys
from typing import Any, Mapping, Sequence

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from market_data.catalog import (
    CatalogEntry,
    CatalogError,
    CatalogStore,
    P0_DATASETS,
    PRODUCTION_STRICT_DATASETS,
    W3_REQUIRED_DATASETS,
)
from market_data.contracts import (
    DATASETS,
    DATASET_ADJ_FACTOR,
    DATASET_EVENTS,
    DATASET_HS300_INDEX,
    DATASET_INDEX_MEMBERS,
    DATASET_INDEX_WEIGHTS,
    DATASET_KEY_COLUMNS,
    DATASET_PRICES,
    DATASET_PRICES_LIMIT,
    DATASET_SCHEMA_REGISTRY,
    DATASET_STOCK_BASIC,
    DATASET_TRADE_CALENDAR,
    DATASET_TRADE_STATUS,
    PIT_STATUS_AVAILABLE,
    QUALITY_STATUS_PASS,
)
from market_data.lake_layout import LakeLayout
from market_data.readers import (
    ExecutionFeedRequest,
    QualityPolicy,
    ReaderResult,
    read_dataset,
    read_execution_feed,
)
from market_data.source_registry import SOURCE_REGISTRY


DEFAULT_START_DATE = "2020-01-01"
DEFAULT_END_DATE = "2024-12-31"
DEFAULT_POLICY = "production_strict_research"
DEFAULT_OUTPUT_DIR = "reports/data_lake_readiness_2020_2024"
DEFAULT_MAX_WORKERS = 2
TARGET_INDEX_CODE = "399300.SZ"
INDEX_MEMBERS_AUDIT_MODE_SNAPSHOT_ASOF = "snapshot_asof"
INDEX_MEMBERS_AUDIT_MODE_DAILY_MATERIALIZED = "daily_materialized"
INDEX_MEMBERS_AUDIT_MODES = (
    INDEX_MEMBERS_AUDIT_MODE_SNAPSHOT_ASOF,
    INDEX_MEMBERS_AUDIT_MODE_DAILY_MATERIALIZED,
)

STATUS_AVAILABLE = "available_for_target_window"
STATUS_LIMITED = "limited_window_only"
STATUS_CONTRACT_UNAVAILABLE = "contract_supported_but_unavailable"
STATUS_RESEARCH_ONLY = "research_contract_only"
STATUS_UNSUPPORTED = "unsupported"
STATUS_BLOCKED = "blocked_required_missing"
STATUS_NA = "not_applicable"

MATRIX_COLUMNS = [
    "dataset",
    "priority",
    "final_status",
    "issue_code",
    "issue_category",
    "remediation",
    "evidence_path",
    "reader_status",
    "reader_issue_codes",
    "published",
    "current_truth",
    "quality_status",
    "readiness_status",
    "pit_status",
    "source",
    "source_interface",
    "source_run_id",
    "schema_version",
    "available_at_rule",
    "date_min",
    "date_max",
    "target_window_covered",
    "row_count",
    "symbol_count",
    "trading_day_count",
    "coverage_denominator",
    "coverage_numerator",
    "coverage_ratio",
    "membership_audit_mode",
    "missing_price_count",
    "untradable_or_suspended_count",
    "not_listed_or_delisted_count",
    "denominator_excluded_count",
    "missing_required_columns",
    "duplicate_key_count",
    "future_available_at_count",
    "available_at_semantics_gap_count",
    "invalid_date_count",
    "blocked_claims",
]

DATASET_REMEDIATION = {
    DATASET_PRICES: "补齐目标窗口 daily OHLCV、复权字段、lineage 与 published catalog；真实 VWAP 另见 execution_price_audit.csv。",
    DATASET_ADJ_FACTOR: "补齐目标窗口 adj_factor，并与 prices adjustment_policy、source_run_id 和 available_at 对齐。",
    DATASET_HS300_INDEX: "发布真实沪深 300 benchmark，覆盖目标交易日，不使用代理 benchmark。",
    DATASET_TRADE_CALENDAR: "先发布目标窗口交易日历；后续 coverage denominator 必须来自该 dataset。",
    DATASET_INDEX_MEMBERS: "补齐沪深 300 PIT membership，包含 in/out/effective/available_at/is_pit_universe/pit_status。",
    DATASET_INDEX_WEIGHTS: "补齐权重日期覆盖并与 index_members 对齐；不得用 weights 替代 membership。",
    DATASET_STOCK_BASIC: "补齐上市退市 lifecycle 字段，仅作为生命周期 gate，不替代 PIT membership。",
    DATASET_TRADE_STATUS: "确认 exact source/interface 后发布停牌、ST、可交易状态与 available_at。",
    DATASET_PRICES_LIMIT: "确认 exact source/interface 后发布涨跌停数据与 available_at。",
    DATASET_EVENTS: "按当前 ST 状态变更事件口径发布 event_type/event_date/available_at/payload。",
}

DAILY_MEMBERSHIP_DATASETS = {
    DATASET_PRICES,
    DATASET_ADJ_FACTOR,
    DATASET_TRADE_STATUS,
    DATASET_PRICES_LIMIT,
}
PIT_DATASETS = {DATASET_INDEX_MEMBERS, DATASET_INDEX_WEIGHTS, DATASET_STOCK_BASIC}
DAILY_DATE_DATASETS = {
    DATASET_PRICES,
    DATASET_ADJ_FACTOR,
    DATASET_HS300_INDEX,
    DATASET_INDEX_MEMBERS,
    DATASET_INDEX_WEIGHTS,
    DATASET_TRADE_CALENDAR,
    DATASET_TRADE_STATUS,
    DATASET_PRICES_LIMIT,
}
DATE_COLUMNS = (
    "trade_date",
    "event_date",
    "effective_date",
    "available_date",
    "in_date",
    "out_date",
    "list_date",
    "delist_date",
)
SPECIAL_AUDIT_FIELDS = {
    DATASET_INDEX_MEMBERS: (
        "in_date",
        "out_date",
        "effective_date",
        "available_at",
        "is_member",
        "is_pit_universe",
        "pit_status",
    ),
    DATASET_INDEX_WEIGHTS: (
        "trade_date",
        "index_code",
        "con_code",
        "weight",
        "effective_date",
        "available_at",
        "pit_status",
    ),
    DATASET_STOCK_BASIC: (
        "symbol",
        "list_status",
        "list_date",
        "delist_date",
        "effective_date",
        "available_at",
    ),
    DATASET_TRADE_STATUS: (
        "trade_date",
        "symbol",
        "is_tradable",
        "is_suspended",
        "is_st",
        "status_reason",
        "available_at",
        "source_interface",
    ),
    DATASET_PRICES_LIMIT: (
        "trade_date",
        "symbol",
        "limit_up",
        "limit_down",
        "available_at",
        "source_interface",
    ),
    DATASET_EVENTS: (
        "symbol",
        "event_type",
        "event_date",
        "available_at",
        "payload",
    ),
}

UNSUPPORTED_REGISTER = [
    {
        "data_item": "industry_classification",
        "status": STATUS_RESEARCH_ONLY,
        "reason": "reader capability 有研究层入口，但不是当前数据湖一等 DATASETS。",
        "pass_denominator": "excluded",
    },
    {
        "data_item": "market_cap",
        "status": STATUS_RESEARCH_ONLY,
        "reason": "市值 / 流通市值未注册为正式 lake dataset。",
        "pass_denominator": "excluded",
    },
    {
        "data_item": "style_exposure_beta_size_value_quality",
        "status": STATUS_RESEARCH_ONLY,
        "reason": "风格暴露属于研究层 capability，不是正式 current truth。",
        "pass_denominator": "excluded",
    },
    {
        "data_item": "capacity_inputs_turnover_adv_constraints",
        "status": STATUS_UNSUPPORTED,
        "reason": "完整 capacity 输入未注册为正式 lake dataset。",
        "pass_denominator": "excluded",
    },
    {
        "data_item": "corporate_actions_full",
        "status": STATUS_UNSUPPORTED,
        "reason": "完整分红、拆股、配股等公司行动库未注册为一等 dataset；events 当前只按 ST 事件口径审计。",
        "pass_denominator": "excluded",
    },
    {
        "data_item": "non_hs300_benchmark",
        "status": STATUS_UNSUPPORTED,
        "reason": "当前正式 benchmark 仅审计 hs300_index，不外推到中证全指、全 A 或任意 benchmark。",
        "pass_denominator": "excluded",
    },
    {
        "data_item": "minute_tick_level2_order_match",
        "status": STATUS_UNSUPPORTED,
        "reason": "分钟、逐笔、盘口、委托、成交明细、真实撮合数据未注册为正式 lake dataset。",
        "pass_denominator": "excluded",
    },
    {
        "data_item": "microstructure_impact_cost",
        "status": STATUS_UNSUPPORTED,
        "reason": "冲击成本所需盘口深度、买卖盘、逐笔冲击等微观结构数据不可用。",
        "pass_denominator": "excluded",
    },
    {
        "data_item": "real_vwap_execution",
        "status": STATUS_CONTRACT_UNAVAILABLE,
        "reason": "仅当 prices 存在 vwap 且 vwap_status=available 时才可声明真实 VWAP；否则只能登记 close proxy 或 required_missing。",
        "pass_denominator": "excluded",
    },
]


@dataclass(frozen=True, slots=True)
class AuditConfig:
    lake_root: Path
    start_date: str = DEFAULT_START_DATE
    end_date: str = DEFAULT_END_DATE
    policy: str = DEFAULT_POLICY
    max_workers: int = DEFAULT_MAX_WORKERS
    output_dir: Path = Path(DEFAULT_OUTPUT_DIR)
    no_env: bool = True
    no_legacy_data: bool = True
    index_code: str = TARGET_INDEX_CODE
    index_members_audit_mode: str = INDEX_MEMBERS_AUDIT_MODE_SNAPSHOT_ASOF


@dataclass(frozen=True, slots=True)
class DatasetProbe:
    dataset: str
    result: ReaderResult
    frame: pd.DataFrame | None
    catalog_entry: CatalogEntry | None
    evidence_path: str


@dataclass(frozen=True, slots=True)
class CoverageContext:
    open_dates: set[str] | None
    open_date_sequence: tuple[str, ...]
    membership_pairs: set[tuple[str, str]] | None
    membership_symbols: set[str] | None
    membership_audit_mode: str
    lifecycle_by_symbol: dict[str, dict[str, str]]
    untradable_pairs: set[tuple[str, str]]
    issues: dict[str, str]


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def _json_dump(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def _normalize_date_text(value: Any) -> str:
    text = str(value).strip()
    if len(text) == 8 and text.isdigit():
        return f"{text[:4]}-{text[4:6]}-{text[6:8]}"
    return text[:10] if len(text) >= 10 else text


def _date_series(series: pd.Series) -> pd.Series:
    text = series.astype(str).str.strip()
    text = text.where(
        ~text.str.match(r"^\d{8}$", na=False),
        text.str.slice(0, 4) + "-" + text.str.slice(4, 6) + "-" + text.str.slice(6, 8),
    )
    text = text.mask(text.isin({"", "None", "NaT", "nan", "NaN", "<NA>"}))
    return pd.to_datetime(text, errors="coerce")


def _datetime_series(series: pd.Series) -> pd.Series:
    text = series.astype(str).str.strip()
    text = text.mask(text.isin({"", "None", "NaT", "nan", "NaN", "<NA>"}))
    return pd.to_datetime(text, errors="coerce", utc=True)


def _date_values(frame: pd.DataFrame | None, column: str) -> set[str]:
    if frame is None or frame.empty or column not in frame.columns:
        return set()
    parsed = _date_series(frame[column]).dropna()
    return {item.strftime("%Y-%m-%d") for item in parsed}


def _date_text_or_none(value: Any) -> str | None:
    text = str(value).strip()
    if text in {"", "None", "NaT", "nan", "NaN", "<NA>"}:
        return None
    parsed = pd.to_datetime(_normalize_date_text(text), errors="coerce")
    if pd.isna(parsed):
        return None
    return parsed.strftime("%Y-%m-%d")


def _datetime_date_text_or_none(value: Any) -> str | None:
    text = str(value).strip()
    if text in {"", "None", "NaT", "nan", "NaN", "<NA>"}:
        return None
    parsed = pd.to_datetime(text, errors="coerce", utc=True)
    if pd.isna(parsed):
        return _date_text_or_none(value)
    return parsed.strftime("%Y-%m-%d")


def _first_date_from_row(row: Mapping[str, Any], columns: Sequence[str]) -> str | None:
    for column in columns:
        if column in row:
            value = _date_text_or_none(row[column])
            if value is not None:
                return value
    return None


def _falsey(series: pd.Series) -> pd.Series:
    if series.dtype == bool:
        return ~series.fillna(True)
    return series.astype(str).str.strip().str.lower().isin({"0", "false", "f", "no", "n", "closed"})


def _date_range_for_frame(
    frame: pd.DataFrame | None,
    entry: CatalogEntry | None,
    dataset: str,
) -> tuple[str | None, str | None]:
    date_column = _primary_date_column(frame, dataset)
    if frame is not None and date_column in frame.columns and not frame.empty:
        parsed = _date_series(frame[date_column]).dropna()
        if not parsed.empty:
            return parsed.min().strftime("%Y-%m-%d"), parsed.max().strftime("%Y-%m-%d")
    if entry is not None and (entry.start_date or entry.end_date):
        return entry.start_date, entry.end_date
    return None, None


def _primary_date_column(frame: pd.DataFrame | None, dataset: str) -> str:
    if dataset == DATASET_EVENTS:
        return "event_date"
    if frame is not None:
        if "trade_date" in frame.columns:
            return "trade_date"
        if "event_date" in frame.columns:
            return "event_date"
        if "effective_date" in frame.columns:
            return "effective_date"
    return "trade_date" if dataset in DAILY_DATE_DATASETS else ""


def _target_window_covered(
    dataset: str,
    date_min: str | None,
    date_max: str | None,
    entry: CatalogEntry | None,
    start_date: str,
    end_date: str,
) -> bool | None:
    if entry is not None and entry.start_date and entry.end_date:
        return entry.start_date <= start_date and entry.end_date >= end_date
    if dataset == DATASET_STOCK_BASIC:
        return None
    if date_min and date_max:
        return date_min <= start_date and date_max >= end_date
    return None


def _is_legacy_data_path(path: Path, cwd: Path | None = None) -> bool:
    cwd = (cwd or Path.cwd()).resolve()
    candidate = path.resolve() if path.exists() else (cwd / path).resolve() if not path.is_absolute() else path
    data_root = (cwd / "data").resolve()
    return candidate == data_root or data_root in candidate.parents


def _validate_audit_config(config: AuditConfig) -> None:
    if config.policy != DEFAULT_POLICY:
        raise ValueError(f"当前 readiness audit 仅支持 policy={DEFAULT_POLICY}: {config.policy}")
    if config.index_members_audit_mode not in INDEX_MEMBERS_AUDIT_MODES:
        raise ValueError(
            "--index-members-audit-mode 必须为 "
            f"{' 或 '.join(INDEX_MEMBERS_AUDIT_MODES)}: {config.index_members_audit_mode}"
        )
    if config.no_env and config.lake_root is None:
        raise ValueError("--lake-root 必须显式传入；no-env 模式禁止从 .env fallback")
    if config.no_legacy_data and _is_legacy_data_path(config.lake_root):
        raise ValueError(f"禁止把旧 data/** 作为生产覆盖证据: {config.lake_root}")
    if int(config.max_workers) < 1:
        raise ValueError("--max-workers 必须 >= 1")


def _priority(dataset: str) -> str:
    if dataset in P0_DATASETS:
        return "P0"
    if dataset in W3_REQUIRED_DATASETS:
        return "W3"
    return "registered"


def _read_catalog_entries(lake_root: Path) -> tuple[dict[str, CatalogEntry], str | None]:
    try:
        entries = {entry.dataset: entry for entry in CatalogStore(LakeLayout(lake_root)).list()}
    except (CatalogError, OSError) as exc:
        return {}, str(exc)
    return entries, None


def _path_exists(path: Path) -> bool:
    try:
        return path.exists()
    except OSError:
        return False


def _entry_evidence_path(lake_root: Path, entry: CatalogEntry | None, dataset: str) -> str:
    catalog_path = LakeLayout(lake_root).catalog_root / "catalog.json"
    parts: list[str] = []
    if _path_exists(catalog_path):
        parts.append(f"{catalog_path}#dataset={dataset}")
    if entry and entry.canonical_path:
        candidate = Path(entry.canonical_path)
        path = candidate if candidate.is_absolute() else lake_root / candidate
        parts.append(str(path))
    elif _path_exists(LakeLayout(lake_root).canonical_dataset_root(dataset)):
        parts.append(str(LakeLayout(lake_root).canonical_dataset_root(dataset)))
    return ";".join(parts) if parts else "catalog_missing"


def _filters_for_dataset(dataset: str, config: AuditConfig) -> dict[str, Any]:
    filters: dict[str, Any] = {
        "start_date": config.start_date,
        "end_date": config.end_date,
    }
    if dataset in {DATASET_HS300_INDEX, DATASET_INDEX_MEMBERS, DATASET_INDEX_WEIGHTS}:
        filters["index_code"] = config.index_code
    return filters


def _probe_dataset(
    dataset: str,
    config: AuditConfig,
    catalog_entries: Mapping[str, CatalogEntry],
) -> DatasetProbe:
    try:
        result = read_dataset(
            dataset,
            config.lake_root,
            filters=_filters_for_dataset(dataset, config),
            quality_policy=QualityPolicy(allow_warn=False, required=True),
            required=True,
        )
    except OSError as exc:
        result = ReaderResult(
            status="required_missing",
            issues=[
                {
                    "code": "lake_root_unavailable",
                    "dataset": dataset,
                    "reason": str(exc),
                }
            ],
            remediation_spec={
                "action": "restore_or_remount_explicit_lake_root",
                "dataset": dataset,
                "lake_root": str(config.lake_root),
                "dry_run_default": True,
                "auto_execute": False,
            },
        )
    entry = result.catalog_entry or catalog_entries.get(dataset)
    frame = result.frame if result.frame is not None else None
    return DatasetProbe(
        dataset=dataset,
        result=result,
        frame=frame,
        catalog_entry=entry,
        evidence_path=_entry_evidence_path(config.lake_root, entry, dataset),
    )


def _lake_root_unavailable_probe(dataset: str, config: AuditConfig, reason: str) -> DatasetProbe:
    return DatasetProbe(
        dataset=dataset,
        result=ReaderResult(
            status="required_missing",
            issues=[
                {
                    "code": "lake_root_unavailable",
                    "dataset": dataset,
                    "reason": reason,
                }
            ],
            remediation_spec={
                "action": "restore_or_remount_explicit_lake_root",
                "dataset": dataset,
                "lake_root": str(config.lake_root),
                "dry_run_default": True,
                "auto_execute": False,
            },
        ),
        frame=None,
        catalog_entry=None,
        evidence_path=str(config.lake_root),
    )


def _is_lake_root_unavailable_error(error: str | None) -> bool:
    if not error:
        return False
    text = error.lower()
    return "no such device" in text or "transport endpoint is not connected" in text


def _probe_all(
    config: AuditConfig,
    catalog_entries: Mapping[str, CatalogEntry],
) -> dict[str, DatasetProbe]:
    datasets = tuple(PRODUCTION_STRICT_DATASETS)
    if config.max_workers == 1:
        return {dataset: _probe_dataset(dataset, config, catalog_entries) for dataset in datasets}

    probes: dict[str, DatasetProbe] = {}
    with ThreadPoolExecutor(max_workers=min(config.max_workers, len(datasets))) as executor:
        futures = {
            executor.submit(_probe_dataset, dataset, config, catalog_entries): dataset
            for dataset in datasets
        }
        for future in as_completed(futures):
            dataset = futures[future]
            probes[dataset] = future.result()
    return {dataset: probes[dataset] for dataset in datasets}


def _truthy(series: pd.Series) -> pd.Series:
    if series.dtype == bool:
        return series.fillna(False)
    return series.astype(str).str.strip().str.lower().isin({"1", "true", "t", "yes", "y", "open"})


def _coverage_context(probes: Mapping[str, DatasetProbe], config: AuditConfig) -> CoverageContext:
    issues: dict[str, str] = {}
    calendar = probes.get(DATASET_TRADE_CALENDAR)
    open_dates: set[str] | None = None
    open_date_sequence: tuple[str, ...] = ()
    if calendar and calendar.result.available and calendar.frame is not None and "trade_date" in calendar.frame.columns:
        frame = calendar.frame
        if "is_open" in frame.columns:
            frame = frame[_truthy(frame["is_open"])]
        open_dates = _date_values(frame, "trade_date")
        open_date_sequence = tuple(sorted(open_dates))
        if not open_dates:
            issues[DATASET_TRADE_CALENDAR] = "coverage_denominator_empty"
    else:
        issues[DATASET_TRADE_CALENDAR] = "coverage_denominator_unavailable"

    members = probes.get(DATASET_INDEX_MEMBERS)
    membership_pairs: set[tuple[str, str]] | None = None
    membership_symbols: set[str] | None = None
    if members and members.result.available and members.frame is not None:
        frame = _membership_frame(members.frame)
        if config.index_members_audit_mode == INDEX_MEMBERS_AUDIT_MODE_SNAPSHOT_ASOF:
            membership_pairs = _snapshot_asof_membership_pairs(frame, open_date_sequence)
        else:
            membership_pairs = _daily_materialized_membership_pairs(frame, open_dates)
            if open_dates is not None and _looks_like_snapshot_membership(frame):
                member_dates = {date for date, _ in membership_pairs}
                if len(member_dates) < len(open_dates):
                    issues[DATASET_INDEX_MEMBERS] = "audit_mode_mismatch"
        membership_symbols = {symbol for _, symbol in membership_pairs}
        if not membership_pairs:
            issues[DATASET_INDEX_MEMBERS] = "coverage_denominator_empty"
    else:
        issues[DATASET_INDEX_MEMBERS] = "coverage_denominator_unavailable"

    stock_basic = probes.get(DATASET_STOCK_BASIC)
    lifecycle_by_symbol: dict[str, dict[str, str]] = {}
    if stock_basic and stock_basic.result.available and stock_basic.frame is not None:
        lifecycle_by_symbol = _stock_lifecycle_by_symbol(stock_basic.frame)

    trade_status = probes.get(DATASET_TRADE_STATUS)
    untradable_pairs: set[tuple[str, str]] = set()
    if trade_status and trade_status.result.available and trade_status.frame is not None:
        untradable_pairs = _untradable_pairs(trade_status.frame, open_dates)

    return CoverageContext(
        open_dates=open_dates,
        open_date_sequence=open_date_sequence,
        membership_pairs=membership_pairs,
        membership_symbols=membership_symbols,
        membership_audit_mode=config.index_members_audit_mode,
        lifecycle_by_symbol=lifecycle_by_symbol,
        untradable_pairs=untradable_pairs,
        issues=issues,
    )


def _membership_frame(frame: pd.DataFrame) -> pd.DataFrame:
    output = frame.copy()
    if "con_code" not in output.columns and "symbol" in output.columns:
        output["con_code"] = output["symbol"]
    return output


def _looks_like_snapshot_membership(frame: pd.DataFrame) -> bool:
    if frame.empty:
        return False
    date_columns = {"effective_date", "in_date", "out_date", "available_at"} & set(frame.columns)
    return bool(date_columns) and "trade_date" in frame.columns


def _active_member_frame(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return frame
    output = frame.copy()
    if "is_member" in output.columns:
        output = output[_truthy(output["is_member"])]
    if "is_pit_universe" in output.columns:
        output = output[_truthy(output["is_pit_universe"])]
    return output


def _daily_materialized_membership_pairs(
    frame: pd.DataFrame,
    open_dates: set[str] | None,
) -> set[tuple[str, str]]:
    if frame.empty or not {"trade_date", "con_code"} <= set(frame.columns):
        return set()
    work = _active_member_frame(frame)
    if open_dates is not None:
        work = work[work["trade_date"].map(_normalize_date_text).isin(open_dates)]
    return _pairs_from_frame(work, "trade_date", "con_code")


def _snapshot_asof_membership_pairs(
    frame: pd.DataFrame,
    open_dates: Sequence[str],
) -> set[tuple[str, str]]:
    if frame.empty or not open_dates or "con_code" not in frame.columns:
        return set()
    work = _active_member_frame(frame)
    if work.empty:
        return set()

    snapshot_dates = sorted(
        {
            _first_date_from_row(row, ("effective_date", "trade_date", "in_date")) or ""
            for row in work.to_dict(orient="records")
        }
        - {""}
    )
    next_snapshot_by_date = {
        snapshot_date: snapshot_dates[index + 1] if index + 1 < len(snapshot_dates) else None
        for index, snapshot_date in enumerate(snapshot_dates)
    }

    pairs: set[tuple[str, str]] = set()
    for row in work.to_dict(orient="records"):
        symbol = str(row.get("con_code") or "").strip()
        if not symbol:
            continue
        snapshot_date = _first_date_from_row(row, ("effective_date", "trade_date", "in_date"))
        start_date = _first_date_from_row(row, ("in_date", "effective_date", "trade_date"))
        if start_date is None:
            continue
        row_out_date = _date_text_or_none(row.get("out_date"))
        next_snapshot = next_snapshot_by_date.get(snapshot_date or "")
        end_exclusive = _min_date_text(row_out_date, next_snapshot)
        available_date = _datetime_date_text_or_none(row.get("available_at"))
        for trade_date in open_dates:
            if trade_date < start_date:
                continue
            if end_exclusive is not None and trade_date >= end_exclusive:
                continue
            if available_date is not None and trade_date < available_date:
                continue
            pairs.add((trade_date, symbol))
    return pairs


def _min_date_text(*values: str | None) -> str | None:
    candidates = [value for value in values if value]
    return min(candidates) if candidates else None


def _stock_lifecycle_by_symbol(frame: pd.DataFrame) -> dict[str, dict[str, str]]:
    if frame.empty:
        return {}
    work = frame.copy()
    if "symbol" not in work.columns and "ts_code" in work.columns:
        work["symbol"] = work["ts_code"]
    if "symbol" not in work.columns:
        return {}
    lifecycle: dict[str, dict[str, str]] = {}
    for row in work.to_dict(orient="records"):
        symbol = str(row.get("symbol") or "").strip()
        if not symbol:
            continue
        lifecycle[symbol] = {
            "list_date": _date_text_or_none(row.get("list_date")) or "",
            "delist_date": _date_text_or_none(row.get("delist_date")) or "",
            "list_status": str(row.get("list_status") or "").strip(),
            "available_at": _datetime_date_text_or_none(row.get("available_at")) or "",
        }
    return lifecycle


def _untradable_pairs(frame: pd.DataFrame, open_dates: set[str] | None) -> set[tuple[str, str]]:
    if frame.empty or not {"trade_date", "symbol"} <= set(frame.columns):
        return set()
    work = frame.copy()
    if open_dates is not None:
        work = work[work["trade_date"].map(_normalize_date_text).isin(open_dates)]
    mask = pd.Series(False, index=work.index)
    if "is_suspended" in work.columns:
        mask = mask | _truthy(work["is_suspended"])
    if "is_tradable" in work.columns:
        mask = mask | _falsey(work["is_tradable"])
    if "volume" in work.columns:
        mask = mask | (pd.to_numeric(work["volume"], errors="coerce").fillna(0) <= 0)
    return _pairs_from_frame(work[mask], "trade_date", "symbol")


def _missing_columns(dataset: str, frame: pd.DataFrame | None) -> list[str]:
    required = tuple(DATASET_SCHEMA_REGISTRY.get(dataset, {}).get("columns", ()))
    if not required:
        return []
    if frame is None:
        return list(required)
    return [column for column in required if column not in frame.columns]


def _duplicate_key_count(dataset: str, frame: pd.DataFrame | None) -> int:
    keys = DATASET_KEY_COLUMNS.get(dataset, ())
    if frame is None or frame.empty or not keys or not set(keys) <= set(frame.columns):
        return 0
    return int(frame.duplicated(list(keys)).sum())


def _invalid_date_count(frame: pd.DataFrame | None) -> int:
    if frame is None or frame.empty:
        return 0
    invalid = 0
    for column in DATE_COLUMNS:
        if column not in frame.columns:
            continue
        raw = frame[column].astype(str).str.strip()
        non_empty = ~raw.isin({"", "None", "NaT", "nan", "NaN", "<NA>"})
        invalid += int((_date_series(frame[column]).isna() & non_empty).sum())
    if "available_at" in frame.columns:
        raw = frame["available_at"].astype(str).str.strip()
        non_empty = ~raw.isin({"", "None", "NaT", "nan", "NaN", "<NA>"})
        invalid += int((_datetime_series(frame["available_at"]).isna() & non_empty).sum())
    return invalid


def _future_available_at_count(frame: pd.DataFrame | None, dataset: str) -> int:
    if frame is None or frame.empty or "available_at" not in frame.columns:
        return 0
    reference_column = _primary_date_column(frame, dataset)
    if reference_column not in frame.columns:
        return 0
    available = _datetime_series(frame["available_at"])
    reference = _date_series(frame[reference_column])
    valid = available.notna() & reference.notna()
    if dataset == DATASET_TRADE_CALENDAR and "available_at_rule" in frame.columns:
        rules = frame["available_at_rule"].astype(str).str.lower()
        valid = valid & ~rules.str.contains("next_open", na=False)
    if not valid.any():
        return 0
    available_dates = available.dt.date
    reference_dates = reference.dt.date
    return int(((available_dates > reference_dates) & valid).sum())


def _available_at_semantics_gap_count(frame: pd.DataFrame | None, dataset: str) -> int:
    if frame is None or frame.empty:
        return 0
    if dataset == DATASET_TRADE_CALENDAR and "available_at_rule" in frame.columns:
        rules = frame["available_at_rule"].astype(str).str.lower()
        return int(rules.str.contains("next_open", na=False).sum())
    return 0


def _symbol_count(dataset: str, frame: pd.DataFrame | None) -> int:
    if frame is None or frame.empty:
        return 0
    column = "symbol"
    if dataset in {DATASET_INDEX_MEMBERS, DATASET_INDEX_WEIGHTS}:
        column = "con_code"
    if column not in frame.columns:
        return 0
    return int(frame[column].astype(str).nunique())


def _trading_day_count(frame: pd.DataFrame | None) -> int:
    if frame is None or frame.empty or "trade_date" not in frame.columns:
        return 0
    return len(_date_values(frame, "trade_date"))


def _pairs_from_frame(
    frame: pd.DataFrame | None,
    date_column: str,
    symbol_column: str,
) -> set[tuple[str, str]]:
    if frame is None or frame.empty or not {date_column, symbol_column} <= set(frame.columns):
        return set()
    dates = frame[date_column].map(_normalize_date_text)
    symbols = frame[symbol_column].astype(str).str.strip()
    return {
        (date, symbol)
        for date, symbol in zip(dates, symbols, strict=False)
        if date and symbol
    }


def _coverage_metrics(
    dataset: str,
    frame: pd.DataFrame | None,
    context: CoverageContext,
) -> dict[str, Any]:
    empty_breakdown = _gap_breakdown()
    if dataset == DATASET_EVENTS:
        return {
            "coverage_denominator": None,
            "coverage_numerator": None,
            "coverage_ratio": None,
            "coverage_issue": "",
            **empty_breakdown,
        }
    if dataset == DATASET_TRADE_CALENDAR:
        if context.open_dates is None:
            return _coverage_unavailable("trade_calendar_denominator_unavailable")
        denominator = len(context.open_dates)
        return _coverage_ratio(denominator, denominator)
    if dataset == DATASET_HS300_INDEX:
        if context.open_dates is None:
            return _coverage_unavailable("trade_calendar_denominator_unavailable")
        dates = _date_values(frame, "trade_date")
        numerator = len(dates & context.open_dates)
        return _coverage_ratio(len(context.open_dates), numerator)
    if dataset == DATASET_INDEX_MEMBERS:
        if context.open_dates is None:
            return _coverage_unavailable("trade_calendar_denominator_unavailable")
        if context.membership_pairs is None:
            return _coverage_unavailable("pit_membership_denominator_unavailable")
        member_dates = {date for date, _ in context.membership_pairs}
        numerator = len(member_dates & context.open_dates)
        coverage = _coverage_ratio(len(context.open_dates), numerator)
        if context.issues.get(DATASET_INDEX_MEMBERS) == "audit_mode_mismatch":
            coverage["coverage_issue"] = "audit_mode_mismatch"
        return coverage
    if dataset == DATASET_STOCK_BASIC:
        if context.membership_symbols is None:
            return _coverage_unavailable("pit_membership_denominator_unavailable")
        if frame is None or "symbol" not in frame.columns:
            return _coverage_ratio(len(context.membership_symbols), 0)
        symbols = set(frame["symbol"].astype(str).str.strip())
        numerator = len(symbols & context.membership_symbols)
        return _coverage_ratio(len(context.membership_symbols), numerator)
    if dataset == DATASET_INDEX_WEIGHTS:
        if context.membership_pairs is None:
            return _coverage_unavailable("pit_membership_denominator_unavailable")
        pairs = _pairs_from_frame(frame, "trade_date", "con_code")
        if not pairs:
            return _coverage_ratio(0, 0)
        numerator = len(pairs & context.membership_pairs)
        coverage = _coverage_ratio(len(pairs), numerator)
        if numerator < len(pairs):
            coverage["coverage_issue"] = "index_weights_membership_mismatch"
        return coverage
    if dataset in DAILY_MEMBERSHIP_DATASETS:
        if context.membership_pairs is None:
            return _coverage_unavailable("pit_membership_denominator_unavailable")
        return _daily_membership_coverage(dataset, frame, context)
    return {
        "coverage_denominator": None,
        "coverage_numerator": None,
        "coverage_ratio": None,
        "coverage_issue": STATUS_NA,
        **empty_breakdown,
    }


def _coverage_ratio(denominator: int, numerator: int) -> dict[str, Any]:
    if denominator <= 0:
        return {
            "coverage_denominator": denominator,
            "coverage_numerator": numerator,
            "coverage_ratio": None,
            "coverage_issue": "coverage_denominator_empty",
            **_gap_breakdown(),
        }
    return {
        "coverage_denominator": denominator,
        "coverage_numerator": numerator,
        "coverage_ratio": numerator / denominator,
        "coverage_issue": "" if numerator >= denominator else "coverage_gap",
        **_gap_breakdown(),
    }


def _coverage_unavailable(code: str) -> dict[str, Any]:
    return {
        "coverage_denominator": None,
        "coverage_numerator": None,
        "coverage_ratio": None,
        "coverage_issue": code,
        **_gap_breakdown(),
    }


def _gap_breakdown(
    *,
    missing_price: int = 0,
    untradable_or_suspended: int = 0,
    not_listed_or_delisted: int = 0,
) -> dict[str, int]:
    denominator_excluded = untradable_or_suspended + not_listed_or_delisted
    return {
        "missing_price_count": int(missing_price),
        "untradable_or_suspended_count": int(untradable_or_suspended),
        "not_listed_or_delisted_count": int(not_listed_or_delisted),
        "denominator_excluded_count": int(denominator_excluded),
    }


def _daily_membership_coverage(
    dataset: str,
    frame: pd.DataFrame | None,
    context: CoverageContext,
) -> dict[str, Any]:
    assert context.membership_pairs is not None
    observed = _pairs_from_frame(frame, "trade_date", "symbol")
    observed_in_denominator = observed & context.membership_pairs
    missing = context.membership_pairs - observed_in_denominator
    missing_price = 0
    untradable_or_suspended = 0
    not_listed_or_delisted = 0
    for trade_date, symbol in missing:
        if _is_not_listed_or_delisted(symbol, trade_date, context.lifecycle_by_symbol):
            not_listed_or_delisted += 1
        elif dataset != DATASET_TRADE_STATUS and (trade_date, symbol) in context.untradable_pairs:
            untradable_or_suspended += 1
        else:
            missing_price += 1
    breakdown = _gap_breakdown(
        missing_price=missing_price,
        untradable_or_suspended=untradable_or_suspended,
        not_listed_or_delisted=not_listed_or_delisted,
    )
    denominator = len(context.membership_pairs)
    numerator = len(observed_in_denominator) + breakdown["denominator_excluded_count"]
    coverage = _coverage_ratio(denominator, numerator)
    coverage.update(breakdown)
    if missing_price:
        coverage["coverage_issue"] = "coverage_gap"
    else:
        coverage["coverage_issue"] = ""
    return coverage


def _is_not_listed_or_delisted(
    symbol: str,
    trade_date: str,
    lifecycle_by_symbol: Mapping[str, Mapping[str, str]],
) -> bool:
    lifecycle = lifecycle_by_symbol.get(symbol)
    if not lifecycle:
        return False
    list_date = lifecycle.get("list_date") or ""
    delist_date = lifecycle.get("delist_date") or ""
    available_at = lifecycle.get("available_at") or ""
    status = (lifecycle.get("list_status") or "").strip().upper()
    if list_date and trade_date < list_date:
        return True
    if delist_date and trade_date >= delist_date:
        return True
    if available_at and trade_date < available_at:
        return True
    return status in {"D", "DELISTED", "退市", "P", "PAUSED", "暂停上市"}


def _first_issue_code(issues: Sequence[str]) -> str:
    return issues[0] if issues else ""


def _reader_issue_codes(result: ReaderResult) -> list[str]:
    return [str(issue.get("code")) for issue in result.issues if issue.get("code")]


def _issue_categories(dataset: str, issues: Sequence[str], coverage: Mapping[str, Any]) -> list[str]:
    categories: list[str] = []
    issue_set = set(issues)
    data_gap_codes = {
        "catalog_missing",
        "canonical_missing",
        "target_window_not_covered",
        "coverage_gap",
        "coverage_denominator_empty",
        "coverage_denominator_unavailable",
        "trade_calendar_denominator_unavailable",
        "pit_membership_denominator_unavailable",
        "missing_required_columns",
        "duplicate_key",
        "invalid_date",
        "quality_not_pass",
        "pit_not_available",
        "index_weights_membership_mismatch",
    }
    metadata_codes = {
        "future_available_at",
        "calendar_available_at_rule_semantics_gap",
        "readiness_not_available",
        "pit_incomplete",
        "non_pit_snapshot",
        "non_pit_universe",
        "w3_required_fields_missing",
        "available_at_missing",
        "w3_source_unresolved",
    }
    if issue_set & data_gap_codes or int(coverage.get("missing_price_count") or 0):
        categories.append("data_gap")
    if issue_set & metadata_codes:
        categories.append("metadata_semantics_gap")
    if "audit_mode_mismatch" in issue_set:
        categories.append("audit_mode_mismatch")
    if dataset == DATASET_ADJ_FACTOR and (
        "future_available_at" in issue_set or "adj_factor_pit_available_at_blocked_claim" in issue_set
    ):
        categories.append("unsupported_claim")
    return _dedupe(categories)


def _blocked_claims(dataset: str, issues: Sequence[str]) -> list[str]:
    claims: list[str] = []
    if dataset == DATASET_ADJ_FACTOR and (
        "future_available_at" in issues or "adj_factor_pit_available_at_blocked_claim" in issues
    ):
        claims.append("pit_adjustment_no_leakage")
    if "coverage_gap" in issues and dataset in {DATASET_PRICES, DATASET_ADJ_FACTOR}:
        claims.append("production_strict_complete_market_data")
    if "calendar_available_at_rule_semantics_gap" in issues:
        claims.append("calendar_pit_available_at_semantics")
    return _dedupe(claims)


def _classify_status(
    dataset: str,
    probe: DatasetProbe,
    issues: list[str],
    target_window_covered: bool | None,
    coverage_ratio: float | None,
) -> str:
    if dataset not in DATASETS:
        return STATUS_UNSUPPORTED
    if target_window_covered is False and probe.catalog_entry is not None:
        return STATUS_LIMITED
    if not probe.result.available:
        if target_window_covered is False:
            return STATUS_LIMITED
        return STATUS_BLOCKED if dataset in PRODUCTION_STRICT_DATASETS else STATUS_CONTRACT_UNAVAILABLE
    blocking_codes = {
        "missing_required_columns",
        "duplicate_key",
        "invalid_date",
        "future_available_at",
        "calendar_available_at_rule_semantics_gap",
        "adj_factor_pit_available_at_blocked_claim",
        "audit_mode_mismatch",
        "index_weights_membership_mismatch",
        "quality_not_pass",
        "pit_not_available",
        "coverage_denominator_unavailable",
        "trade_calendar_denominator_unavailable",
        "pit_membership_denominator_unavailable",
        "coverage_denominator_empty",
    }
    if set(issues) & blocking_codes:
        return STATUS_BLOCKED
    if coverage_ratio is not None and coverage_ratio < 1.0:
        return STATUS_BLOCKED
    return STATUS_AVAILABLE


def _remediation(dataset: str, issues: Sequence[str], final_status: str, config: AuditConfig) -> str:
    if final_status == STATUS_AVAILABLE:
        return "保持 published current truth，并在真实回测前复跑该只读审计。"
    if final_status == STATUS_LIMITED:
        return f"补齐 {config.start_date}..{config.end_date} 目标窗口，不得把 limited window 外推为全历史可用。"
    if "lake_root_unavailable" in issues:
        return f"恢复或重新挂载显式 lake root: {config.lake_root}；当前路径不可读，不能验证真实数据覆盖。"
    if "catalog_missing" in issues:
        return f"在显式 lake 中发布 {dataset} catalog 与 canonical current truth；不要回退到 .env 或旧 data/**。"
    if "audit_mode_mismatch" in issues:
        return "当前 index_members 是 snapshot / rebalance 形态；使用 snapshot_asof 审计展开，或补齐 daily materialized PIT membership 后再用 daily_materialized 模式。"
    if "calendar_available_at_rule_semantics_gap" in issues:
        return "`trade_calendar.available_at` 必须表示交易日历已知时间；若需要 next_open，请迁移到独立字段并重发 metadata。"
    if "adj_factor_pit_available_at_blocked_claim" in issues:
        return "重发可证明 as-of 可见的 adj_factor available_at；若只能证明 ex-post 复权，报告必须保留 PIT 复权无泄漏 blocked claim。"
    if "trade_calendar_denominator_unavailable" in issues:
        return DATASET_REMEDIATION[DATASET_TRADE_CALENDAR]
    if "pit_membership_denominator_unavailable" in issues:
        return DATASET_REMEDIATION[DATASET_INDEX_MEMBERS]
    return DATASET_REMEDIATION.get(dataset, "补齐正式数据湖合同、catalog、quality 与 coverage 证据。")


def _dataset_matrix_row(
    dataset: str,
    probe: DatasetProbe,
    context: CoverageContext,
    config: AuditConfig,
) -> dict[str, Any]:
    frame = probe.frame
    entry = probe.catalog_entry
    date_min, date_max = _date_range_for_frame(frame, entry, dataset)
    target_window_covered = _target_window_covered(
        dataset,
        date_min,
        date_max,
        entry,
        config.start_date,
        config.end_date,
    )
    missing_columns = _missing_columns(dataset, frame) if probe.result.available else []
    duplicate_key_count = _duplicate_key_count(dataset, frame)
    invalid_date_count = _invalid_date_count(frame)
    future_available_count = _future_available_at_count(frame, dataset)
    available_at_semantics_gap_count = _available_at_semantics_gap_count(frame, dataset)
    coverage = _coverage_metrics(dataset, frame, context)

    issues = _reader_issue_codes(probe.result)
    if missing_columns:
        issues.append("missing_required_columns")
    if duplicate_key_count:
        issues.append("duplicate_key")
    if invalid_date_count:
        issues.append("invalid_date")
    if future_available_count:
        issues.append("future_available_at")
    if available_at_semantics_gap_count:
        issues.append("calendar_available_at_rule_semantics_gap")
    if dataset == DATASET_ADJ_FACTOR and future_available_count:
        issues.append("adj_factor_pit_available_at_blocked_claim")
    if entry and entry.quality_status and entry.quality_status != QUALITY_STATUS_PASS:
        issues.append("quality_not_pass")
    if dataset in PIT_DATASETS and entry and entry.pit_status and entry.pit_status != PIT_STATUS_AVAILABLE:
        issues.append("pit_not_available")
    if target_window_covered is False:
        issues.append("target_window_not_covered")
    coverage_issue = str(coverage.get("coverage_issue") or "")
    if coverage_issue and coverage_issue != STATUS_NA:
        issues.append(coverage_issue)
        if "denominator_unavailable" in coverage_issue:
            issues.append("coverage_denominator_unavailable")

    issues = _dedupe(issues)
    issue_categories = _issue_categories(dataset, issues, coverage)
    blocked_claims = _blocked_claims(dataset, issues)
    final_status = _classify_status(
        dataset,
        probe,
        issues,
        target_window_covered,
        coverage.get("coverage_ratio"),
    )
    return {
        "dataset": dataset,
        "priority": _priority(dataset),
        "final_status": final_status,
        "issue_code": ";".join(issues) if issues else "none",
        "issue_category": ";".join(issue_categories) if issue_categories else "none",
        "remediation": _remediation(dataset, issues, final_status, config),
        "evidence_path": probe.evidence_path,
        "reader_status": probe.result.status,
        "reader_issue_codes": ";".join(_reader_issue_codes(probe.result)),
        "published": bool(entry.published) if entry else False,
        "current_truth": bool(entry.published) if entry else False,
        "quality_status": entry.quality_status if entry else "missing",
        "readiness_status": entry.readiness_status if entry else "missing",
        "pit_status": entry.pit_status if entry else "missing",
        "source": entry.source if entry else "",
        "source_interface": entry.source_interface if entry else "",
        "source_run_id": entry.latest_manifest_run_id if entry else "",
        "schema_version": entry.schema_version if entry else "",
        "available_at_rule": entry.available_at_rule if entry else "",
        "date_min": date_min or "",
        "date_max": date_max or "",
        "target_window_covered": target_window_covered if target_window_covered is not None else STATUS_NA,
        "row_count": int(len(frame)) if frame is not None else 0,
        "symbol_count": _symbol_count(dataset, frame),
        "trading_day_count": _trading_day_count(frame),
        "coverage_denominator": coverage.get("coverage_denominator"),
        "coverage_numerator": coverage.get("coverage_numerator"),
        "coverage_ratio": coverage.get("coverage_ratio"),
        "membership_audit_mode": context.membership_audit_mode if dataset in {DATASET_INDEX_MEMBERS, DATASET_INDEX_WEIGHTS, *DAILY_MEMBERSHIP_DATASETS, DATASET_STOCK_BASIC} else "",
        "missing_price_count": coverage.get("missing_price_count", 0),
        "untradable_or_suspended_count": coverage.get("untradable_or_suspended_count", 0),
        "not_listed_or_delisted_count": coverage.get("not_listed_or_delisted_count", 0),
        "denominator_excluded_count": coverage.get("denominator_excluded_count", 0),
        "missing_required_columns": ";".join(missing_columns),
        "duplicate_key_count": duplicate_key_count,
        "future_available_at_count": future_available_count,
        "available_at_semantics_gap_count": available_at_semantics_gap_count,
        "invalid_date_count": invalid_date_count,
        "blocked_claims": ";".join(blocked_claims),
    }


def _dedupe(values: Sequence[str]) -> list[str]:
    output: list[str] = []
    seen: set[str] = set()
    for value in values:
        if value and value not in seen:
            output.append(value)
            seen.add(value)
    return output


def _source_interface_matrix_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for source, spec in sorted(SOURCE_REGISTRY.items()):
        if not spec.interfaces:
            rows.append(
                {
                    "source": source,
                    "source_status": spec.status,
                    "interface": "",
                    "target_dataset": "",
                    "dataset_scope": STATUS_UNSUPPORTED,
                    "provider_method": "",
                    "category": "",
                    "pit_required": False,
                    "adjustment_required": False,
                    "credential_env_vars": ";".join(spec.credential_env_vars),
                }
            )
            continue
        for interface in spec.interfaces:
            target = interface.target_dataset
            rows.append(
                {
                    "source": source,
                    "source_status": spec.status,
                    "interface": interface.name,
                    "target_dataset": target,
                    "dataset_scope": "formal_dataset" if target in DATASETS else STATUS_RESEARCH_ONLY,
                    "provider_method": interface.provider_method or "",
                    "category": interface.category,
                    "pit_required": interface.pit_required,
                    "adjustment_required": interface.adjustment_required,
                    "credential_env_vars": ";".join(spec.credential_env_vars),
                }
            )
    return rows


def _contract_snapshot(config: AuditConfig) -> dict[str, Any]:
    return {
        "generated_at": _now_utc(),
        "target_window": {"start_date": config.start_date, "end_date": config.end_date},
        "policy": config.policy,
        "index_members_audit_mode": config.index_members_audit_mode,
        "formal_datasets": list(PRODUCTION_STRICT_DATASETS),
        "p0_datasets": list(P0_DATASETS),
        "w3_required_datasets": list(W3_REQUIRED_DATASETS),
        "dataset_contracts": {
            dataset: {
                "priority": _priority(dataset),
                "columns": list(DATASET_SCHEMA_REGISTRY.get(dataset, {}).get("columns", ())),
                "key_columns": list(DATASET_SCHEMA_REGISTRY.get(dataset, {}).get("key_columns", ())),
                "pit_fields": list(DATASET_SCHEMA_REGISTRY.get(dataset, {}).get("pit_fields", ())),
                "w3_required": list(DATASET_SCHEMA_REGISTRY.get(dataset, {}).get("w3_required", ())),
            }
            for dataset in PRODUCTION_STRICT_DATASETS
        },
        "reader_contracts": {
            "no_env_fallback": config.no_env,
            "no_legacy_data": config.no_legacy_data,
            "w3_unresolved": "trade_status/prices_limit/events 缺 source_interface 或 UNKNOWN/UNRESOLVED 时 fail-fast",
            "vwap_policy": "prices 缺 vwap 或 vwap_status 时不从 amount/volume 派生真实 VWAP",
            "pit_membership_policy": "PIT 股票池只由 index_members 证明；snapshot_asof 模式按 effective/in/out/available_at 展开到 open trade dates，不由 prices/stock_basic/index_weights 替代",
            "trade_calendar_available_at_policy": "trade_calendar.available_at 表示交易日历已知时间；next_open 必须使用独立字段，不得写入 available_at",
            "adj_factor_claim_policy": "adj_factor.available_at 仍执行 strict PIT 检查；ex-post 复权只能保留 blocked claim",
        },
        "unsupported_policy": UNSUPPORTED_REGISTER,
    }


def _schema_quality_rows(matrix_rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "dataset": row["dataset"],
            "priority": row["priority"],
            "quality_status": row["quality_status"],
            "readiness_status": row["readiness_status"],
            "pit_status": row["pit_status"],
            "published": row["published"],
            "missing_required_columns": row["missing_required_columns"],
            "duplicate_key_count": row["duplicate_key_count"],
            "invalid_date_count": row["invalid_date_count"],
            "future_available_at_count": row["future_available_at_count"],
            "available_at_semantics_gap_count": row["available_at_semantics_gap_count"],
            "source": row["source"],
            "source_interface": row["source_interface"],
            "available_at_rule": row["available_at_rule"],
            "issue_category": row["issue_category"],
            "blocked_claims": row["blocked_claims"],
            "issue_code": row["issue_code"],
        }
        for row in matrix_rows
    ]


def _coverage_detail_rows(matrix_rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "dataset": row["dataset"],
            "issue_category": row["issue_category"],
            "date_min": row["date_min"],
            "date_max": row["date_max"],
            "target_window_covered": row["target_window_covered"],
            "row_count": row["row_count"],
            "symbol_count": row["symbol_count"],
            "trading_day_count": row["trading_day_count"],
            "coverage_denominator": row["coverage_denominator"],
            "coverage_numerator": row["coverage_numerator"],
            "coverage_ratio": row["coverage_ratio"],
            "coverage_basis": _coverage_basis(str(row["dataset"])),
            "membership_audit_mode": row["membership_audit_mode"],
            "missing_price_count": row["missing_price_count"],
            "untradable_or_suspended_count": row["untradable_or_suspended_count"],
            "not_listed_or_delisted_count": row["not_listed_or_delisted_count"],
            "denominator_excluded_count": row["denominator_excluded_count"],
            "issue_code": row["issue_code"],
        }
        for row in matrix_rows
    ]


def _coverage_basis(dataset: str) -> str:
    if dataset == DATASET_TRADE_CALENDAR:
        return "自身 open trade_date denominator"
    if dataset == DATASET_HS300_INDEX:
        return "trade_calendar open trade_date"
    if dataset == DATASET_INDEX_MEMBERS:
        return "trade_calendar open trade_date + index_members as-of PIT membership"
    if dataset == DATASET_STOCK_BASIC:
        return "index_members PIT symbol universe"
    if dataset == DATASET_INDEX_WEIGHTS:
        return "index_weights rows aligned to index_members as-of PIT membership"
    if dataset in DAILY_MEMBERSHIP_DATASETS:
        return "index_members as-of PIT date-symbol denominator with tradability/lifecycle gap attribution"
    if dataset == DATASET_EVENTS:
        return "sparse ST event capability; daily coverage ratio not applicable"
    return STATUS_NA


def _pit_w3_rows(
    probes: Mapping[str, DatasetProbe],
    matrix_rows: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    matrix_by_dataset = {str(row["dataset"]): row for row in matrix_rows}
    rows: list[dict[str, Any]] = []
    for dataset in (
        DATASET_INDEX_MEMBERS,
        DATASET_INDEX_WEIGHTS,
        DATASET_STOCK_BASIC,
        DATASET_TRADE_STATUS,
        DATASET_PRICES_LIMIT,
        DATASET_EVENTS,
    ):
        probe = probes[dataset]
        frame = probe.frame
        fields = SPECIAL_AUDIT_FIELDS[dataset]
        present = sorted(set(frame.columns) if frame is not None else set())
        missing = [field for field in fields if field not in present]
        event_types = ""
        if dataset == DATASET_EVENTS and frame is not None and "event_type" in frame.columns:
            event_types = ";".join(sorted(str(item) for item in frame["event_type"].dropna().unique()))
        rows.append(
            {
                "dataset": dataset,
                "audit_scope": "PIT" if dataset in PIT_DATASETS else "W3",
                "final_status": matrix_by_dataset[dataset]["final_status"],
                "required_fields": ";".join(fields),
                "missing_fields": ";".join(missing),
                "pit_status": matrix_by_dataset[dataset]["pit_status"],
                "readiness_status": matrix_by_dataset[dataset]["readiness_status"],
                "coverage_ratio": matrix_by_dataset[dataset]["coverage_ratio"],
                "future_available_at_count": matrix_by_dataset[dataset]["future_available_at_count"],
                "available_at_semantics_gap_count": matrix_by_dataset[dataset]["available_at_semantics_gap_count"],
                "source_interface": matrix_by_dataset[dataset]["source_interface"],
                "event_types": event_types,
                "issue_category": matrix_by_dataset[dataset]["issue_category"],
                "membership_audit_mode": matrix_by_dataset[dataset]["membership_audit_mode"],
                "issue_code": matrix_by_dataset[dataset]["issue_code"],
            }
        )
    return rows


def _execution_price_rows(config: AuditConfig, prices_probe: DatasetProbe) -> list[dict[str, Any]]:
    if "lake_root_unavailable" in _reader_issue_codes(prices_probe.result):
        return [
            {
                "logical_dataset": "execution_prices",
                "source_dataset": DATASET_PRICES,
                "reader_status": "required_missing",
                "execution_price_status": "required_missing",
                "row_count": 0,
                "missing_ohlcv_columns": "open;high;low;close;volume;amount",
                "true_vwap_available_count": 0,
                "vwap_required_missing_count": 0,
                "close_proxy_available_count": 0,
                "issue_code": "lake_root_unavailable",
                "blocked_claims": "real_vwap_execution;vwap_fill_claim",
                "remediation": f"恢复或重新挂载显式 lake root: {config.lake_root}；当前路径不可读，无法验证执行价。",
            }
        ]
    try:
        result = read_execution_feed(
            ExecutionFeedRequest(
                lake_root=config.lake_root,
                start_date=config.start_date,
                end_date=config.end_date,
                quality_policy=QualityPolicy(allow_warn=False, required=True),
            )
        )
    except OSError as exc:
        result = ReaderResult(
            status="required_missing",
            issues=[
                {
                    "code": "lake_root_unavailable",
                    "dataset": DATASET_PRICES,
                    "logical_dataset": "execution_prices",
                    "reason": str(exc),
                }
            ],
            remediation_spec={
                "action": "restore_or_remount_explicit_lake_root",
                "dataset": DATASET_PRICES,
                "logical_dataset": "execution_prices",
                "lake_root": str(config.lake_root),
                "dry_run_default": True,
                "auto_execute": False,
            },
        )
    frame = result.frame
    true_vwap_count = 0
    missing_vwap_count = 0
    close_proxy_count = 0
    if frame is not None and not frame.empty:
        if "vwap_status" in frame.columns:
            true_vwap_count = int((frame["vwap_status"].astype(str) == "available").sum())
            missing_vwap_count = int((frame["vwap_status"].astype(str) != "available").sum())
        if "close" in frame.columns:
            close_proxy_count = int(pd.to_numeric(frame["close"], errors="coerce").notna().sum())

    if result.status != "available":
        execution_status = result.status
    elif true_vwap_count and missing_vwap_count == 0:
        execution_status = "real_vwap_available"
    elif close_proxy_count:
        execution_status = "close_proxy_available"
    else:
        execution_status = "required_missing"

    price_frame = prices_probe.frame
    required_ohlcv = ("open", "high", "low", "close", "volume", "amount")
    missing_ohlcv = [
        column
        for column in required_ohlcv
        if price_frame is None or column not in price_frame.columns
    ]
    return [
        {
            "logical_dataset": "execution_prices",
            "source_dataset": DATASET_PRICES,
            "reader_status": result.status,
            "execution_price_status": execution_status,
            "row_count": int(len(frame)) if frame is not None else 0,
            "missing_ohlcv_columns": ";".join(missing_ohlcv),
            "true_vwap_available_count": true_vwap_count,
            "vwap_required_missing_count": missing_vwap_count,
            "close_proxy_available_count": close_proxy_count,
            "issue_code": ";".join(_reader_issue_codes(result)) or "none",
            "blocked_claims": "" if execution_status == "real_vwap_available" else "real_vwap_execution;vwap_fill_claim",
            "remediation": "如需真实 VWAP/分钟执行价，必须在 prices 中发布 vwap 且 vwap_status=available；不得由 amount/volume 派生。",
        }
    ]


def _unsupported_rows(execution_rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows = [dict(row) for row in UNSUPPORTED_REGISTER]
    execution_status = str(execution_rows[0]["execution_price_status"]) if execution_rows else ""
    for row in rows:
        if row["data_item"] == "real_vwap_execution" and execution_status == "real_vwap_available":
            row["status"] = STATUS_AVAILABLE
            row["reason"] = "prices 已提供 vwap 且 vwap_status=available。"
    return rows


def _overall_status(matrix_rows: Sequence[Mapping[str, Any]]) -> str:
    statuses = {str(row["final_status"]) for row in matrix_rows}
    if STATUS_BLOCKED in statuses or STATUS_CONTRACT_UNAVAILABLE in statuses:
        return "blocked"
    if STATUS_LIMITED in statuses:
        return "research_limited_only"
    if statuses == {STATUS_AVAILABLE}:
        return "production_strict_target_window_pass"
    return "exploratory_only"


def _blocking_rows(matrix_rows: Sequence[Mapping[str, Any]]) -> list[Mapping[str, Any]]:
    return [
        row
        for row in matrix_rows
        if row["final_status"] in {STATUS_BLOCKED, STATUS_LIMITED, STATUS_CONTRACT_UNAVAILABLE}
    ]


def _summary_markdown(
    config: AuditConfig,
    matrix_rows: Sequence[Mapping[str, Any]],
    execution_rows: Sequence[Mapping[str, Any]],
    catalog_error: str | None,
) -> str:
    overall = _overall_status(matrix_rows)
    counts = Counter(str(row["final_status"]) for row in matrix_rows)
    blocking = _blocking_rows(matrix_rows)
    execution_status = execution_rows[0]["execution_price_status"] if execution_rows else "unknown"
    lines = [
        "# 数据湖可用性 Readiness Summary",
        "",
        f"- 生成时间: {_now_utc()}",
        f"- lake_root: `{config.lake_root}`",
        f"- 目标窗口: `{config.start_date}..{config.end_date}`",
        f"- policy: `{config.policy}`",
        f"- index_members_audit_mode: `{config.index_members_audit_mode}`",
        f"- max_workers: `{config.max_workers}`",
        f"- 安全边界: no_env={config.no_env}, no_legacy_data={config.no_legacy_data}, lake_writes=0, provider_fetches=0",
        f"- 总体判定: `{overall}`",
    ]
    if catalog_error:
        lines.append(f"- catalog 读取问题: `{catalog_error}`")
    lines.extend(["", "## 状态计数", ""])
    lines.extend(["| status | count |", "|---|---:|"])
    for status, count in sorted(counts.items()):
        lines.append(f"| `{status}` | {count} |")
    lines.extend(["", "## 阻断与 limited window", ""])
    if not blocking:
        lines.append("- 未发现 P0/W3 阻断项。")
    else:
        for row in blocking:
            lines.append(
                f"- `{row['dataset']}`: `{row['final_status']}`; category=`{row['issue_category']}`; "
                f"issues=`{row['issue_code']}`; blocked_claims=`{row['blocked_claims'] or 'none'}`; remediation={row['remediation']}"
            )
    category_counts: Counter[str] = Counter()
    for row in matrix_rows:
        for category in str(row["issue_category"]).split(";"):
            category_counts[category or "none"] += 1
    lines.extend(["", "## CR-012 问题分类", ""])
    lines.extend(["| category | count | meaning |", "|---|---:|---|"])
    meanings = {
        "data_gap": "当前发布数据或覆盖不足，需要补数或重发 current truth。",
        "metadata_semantics_gap": "字段语义、available_at 或 readiness metadata 不满足 strict claim。",
        "audit_mode_mismatch": "审计模式与数据形态不匹配，例如 snapshot 被 daily materialized 口径审计。",
        "unsupported_claim": "当前数据不足以支撑生产级声明，只能保留 blocked claim。",
        "none": "未发现该 dataset 的阻断分类。",
    }
    for category, count in sorted(category_counts.items()):
        lines.append(f"| `{category}` | {count} | {meanings.get(category, '')} |")
    lines.extend(
        [
            "",
            "## 执行价 / VWAP",
            "",
            f"- execution_price_status: `{execution_status}`",
            "- 缺少真实 `vwap` 或 `vwap_status=available` 时，只能登记 close proxy 或 required_missing，不能声明真实 VWAP 执行价通过。",
            "",
            "## 口径声明",
            "",
            "- limited-window 结论只适用于本次审计目标窗口，不能外推为 `2020-01-01..2024-12-31` 或更长历史覆盖。",
            "- `index_members` 的默认审计口径为 `snapshot_asof`：用 `effective_date/in_date/out_date/available_at` 展开到 open trade dates 后计算 PIT coverage。",
            "- `index_weights` 只证明权重行与 as-of PIT membership 对齐，不替代 `index_members` 证明完整 PIT universe。",
            "- `prices` / `adj_factor` / `trade_status` / `prices_limit` 使用 as-of PIT membership denominator，并通过 lifecycle / tradability gate 将缺口归因为真实缺行情、不可交易、未上市/退市或 denominator excluded。",
            "- `trade_calendar.available_at` 表示交易日历已知时间；`next_open` 不得写入 `available_at`，必须使用独立字段。",
            "- `adj_factor.available_at` 保持 strict PIT 检查；若只能证明 ex-post 复权，禁止声明 PIT 无泄漏复权。",
            "- `hs300_index` 只代表真实沪深 300 benchmark，不代表其他指数或任意 benchmark。",
            "- `events` 当前只按 ST 状态变更事件能力审计，不扩展为完整公告 / 公司行动事件库。",
            "- unsupported / research_contract_only 数据不会进入 10 个正式 dataset 的 pass 分母。",
        ]
    )
    return "\n".join(lines) + "\n"


def _blocking_markdown(config: AuditConfig, matrix_rows: Sequence[Mapping[str, Any]]) -> str:
    blocking = _blocking_rows(matrix_rows)
    lines = [
        "# Blocking Gaps",
        "",
        f"- 目标窗口: `{config.start_date}..{config.end_date}`",
        f"- policy: `{config.policy}`",
        f"- index_members_audit_mode: `{config.index_members_audit_mode}`",
        "",
    ]
    if not blocking:
        lines.append("当前 10 个正式 dataset 未产生 production strict 阻断项。")
        return "\n".join(lines) + "\n"
    lines.extend(
        [
            "| priority | dataset | status | category | issue_code | blocked_claims | remediation |",
            "|---|---|---|---|---|---|---|",
        ]
    )
    for row in blocking:
        lines.append(
            f"| {row['priority']} | `{row['dataset']}` | `{row['final_status']}` | `{row['issue_category']}` | `{row['issue_code']}` | `{row['blocked_claims'] or 'none'}` | {row['remediation']} |"
        )
    lines.extend(
        [
            "",
            "## Remediation 分类",
            "",
            "- `data_gap`: 补齐或重发目标窗口 current truth，不得用旧 `data/**` 或 .env fallback 作为证据。",
            "- `metadata_semantics_gap`: 修正 `available_at` / `available_at_rule` / readiness metadata 语义后重新审计。",
            "- `audit_mode_mismatch`: 对 snapshot 成分使用 `snapshot_asof`，或物化每日 PIT membership 后使用 `daily_materialized`。",
            "- `unsupported_claim`: 保持 blocked claim，直到数据合同和 as-of 可见性可被正式证明。",
        ]
    )
    return "\n".join(lines) + "\n"


def _write_csv(path: Path, rows: Sequence[Mapping[str, Any]], columns: Sequence[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame = pd.DataFrame(list(rows))
    if columns:
        for column in columns:
            if column not in frame.columns:
                frame[column] = ""
        frame = frame[list(columns)]
    frame.to_csv(path, index=False)


def _write_outputs(
    config: AuditConfig,
    matrix_rows: Sequence[Mapping[str, Any]],
    probes: Mapping[str, DatasetProbe],
    execution_rows: Sequence[Mapping[str, Any]],
    catalog_error: str | None,
) -> dict[str, Path]:
    output_dir = config.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    unsupported_rows = _unsupported_rows(execution_rows)
    paths = {
        "readiness_matrix": output_dir / "readiness_matrix.csv",
        "readiness_summary": output_dir / "readiness_summary.md",
        "dataset_contract_snapshot": output_dir / "dataset_contract_snapshot.json",
        "dataset_coverage_detail": output_dir / "dataset_coverage_detail.csv",
        "source_interface_matrix": output_dir / "source_interface_matrix.csv",
        "schema_quality_audit": output_dir / "schema_quality_audit.csv",
        "pit_w3_audit": output_dir / "pit_w3_audit.csv",
        "execution_price_audit": output_dir / "execution_price_audit.csv",
        "unsupported_data_register": output_dir / "unsupported_data_register.csv",
        "blocking_gaps": output_dir / "blocking_gaps.md",
    }
    _write_csv(paths["readiness_matrix"], matrix_rows, MATRIX_COLUMNS)
    paths["readiness_summary"].write_text(
        _summary_markdown(config, matrix_rows, execution_rows, catalog_error),
        encoding="utf-8",
    )
    paths["dataset_contract_snapshot"].write_text(
        json.dumps(_contract_snapshot(config), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    _write_csv(paths["dataset_coverage_detail"], _coverage_detail_rows(matrix_rows))
    _write_csv(paths["source_interface_matrix"], _source_interface_matrix_rows())
    _write_csv(paths["schema_quality_audit"], _schema_quality_rows(matrix_rows))
    _write_csv(paths["pit_w3_audit"], _pit_w3_rows(probes, matrix_rows))
    _write_csv(paths["execution_price_audit"], execution_rows)
    _write_csv(paths["unsupported_data_register"], unsupported_rows)
    paths["blocking_gaps"].write_text(
        _blocking_markdown(config, matrix_rows),
        encoding="utf-8",
    )
    return paths


def run_audit(config: AuditConfig) -> dict[str, Any]:
    _validate_audit_config(config)
    catalog_entries, catalog_error = _read_catalog_entries(config.lake_root)
    if _is_lake_root_unavailable_error(catalog_error):
        probes = {
            dataset: _lake_root_unavailable_probe(dataset, config, str(catalog_error))
            for dataset in PRODUCTION_STRICT_DATASETS
        }
    else:
        probes = _probe_all(config, catalog_entries)
    context = _coverage_context(probes, config)
    matrix_rows = [
        _dataset_matrix_row(dataset, probes[dataset], context, config)
        for dataset in PRODUCTION_STRICT_DATASETS
    ]
    execution_rows = _execution_price_rows(config, probes[DATASET_PRICES])
    paths = _write_outputs(config, matrix_rows, probes, execution_rows, catalog_error)
    return {
        "ok": True,
        "overall_status": _overall_status(matrix_rows),
        "status_counts": dict(Counter(str(row["final_status"]) for row in matrix_rows)),
        "output_dir": str(config.output_dir),
        "paths": {key: str(value) for key, value in paths.items()},
        "blocking_count": len(_blocking_rows(matrix_rows)),
        "lake_writes": 0,
        "provider_fetches": 0,
        "legacy_data_reads": 0,
        "env_fallback_reads": 0,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="uv run python experiments/run_data_lake_readiness_audit.py",
        description="只读审计真实数据湖在目标窗口的生产级 readiness。",
    )
    parser.add_argument("--lake-root", required=True, type=Path)
    parser.add_argument("--start-date", default=DEFAULT_START_DATE)
    parser.add_argument("--end-date", default=DEFAULT_END_DATE)
    parser.add_argument("--policy", default=DEFAULT_POLICY)
    parser.add_argument("--max-workers", type=int, default=DEFAULT_MAX_WORKERS)
    parser.add_argument("--output-dir", type=Path, default=Path(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--no-env", dest="no_env", action="store_true", default=True)
    parser.add_argument("--allow-env", dest="no_env", action="store_false")
    parser.add_argument("--no-legacy-data", dest="no_legacy_data", action="store_true", default=True)
    parser.add_argument("--allow-legacy-data", dest="no_legacy_data", action="store_false")
    parser.add_argument("--index-code", default=TARGET_INDEX_CODE)
    parser.add_argument(
        "--index-members-audit-mode",
        choices=INDEX_MEMBERS_AUDIT_MODES,
        default=INDEX_MEMBERS_AUDIT_MODE_SNAPSHOT_ASOF,
        help="index_members 覆盖口径：snapshot_asof 展开 rebalance/snapshot；daily_materialized 要求每日物化行。",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    config = AuditConfig(
        lake_root=args.lake_root,
        start_date=args.start_date,
        end_date=args.end_date,
        policy=args.policy,
        max_workers=args.max_workers,
        output_dir=args.output_dir,
        no_env=args.no_env,
        no_legacy_data=args.no_legacy_data,
        index_code=args.index_code,
        index_members_audit_mode=args.index_members_audit_mode,
    )
    try:
        result = run_audit(config)
    except ValueError as exc:
        parser.exit(2, f"错误: {exc}\n")
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
