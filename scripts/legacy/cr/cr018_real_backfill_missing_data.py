"""CR018 生产级数据湖缺口补数脚本。

该脚本执行真实 Tushare 读取和真实 lake candidate 写入，但不发布 current
pointer。QMT、下单、账户和交易接口不在本脚本范围内。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import pandas as pd
import tushare as ts

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from market_data.catalog import CatalogEntry, CatalogStore
from market_data.contracts import (
    CANONICAL_EVENTS_COLUMNS,
    CANONICAL_HS300_INDEX_COLUMNS,
    CANONICAL_INDEX_MEMBERS_COLUMNS,
    CANONICAL_INDEX_WEIGHTS_COLUMNS,
    CANONICAL_PRICES_LIMIT_COLUMNS,
    CANONICAL_STOCK_BASIC_COLUMNS,
    CANONICAL_TRADE_STATUS_COLUMNS,
    DATASET_EVENTS,
    DATASET_HS300_INDEX,
    DATASET_INDEX_MEMBERS,
    DATASET_INDEX_WEIGHTS,
    DATASET_PRICES_LIMIT,
    DATASET_STOCK_BASIC,
    DATASET_TRADE_STATUS,
    INTERFACE_EVENTS_DISCLOSURE,
    INTERFACE_HS300_INDEX_DAILY,
    INTERFACE_INDEX_WEIGHTS_SNAPSHOT,
    INTERFACE_PRICES_LIMIT_DAILY,
    INTERFACE_STOCK_BASIC_SNAPSHOT,
    INTERFACE_TRADE_STATUS_DAILY,
    PIT_STATUS_AVAILABLE,
    PIT_STATUS_NON_PIT_SNAPSHOT,
    QUALITY_STATUS_PASS,
    READINESS_STATUS_AVAILABLE,
    READINESS_STATUS_NON_PIT_SNAPSHOT,
    SCHEMA_VERSION,
    SOURCE_TUSHARE,
)
from market_data.lake_layout import LakeLayout, ensure_parent_dirs_for_write
from market_data.normalization import normalize_run
from market_data.storage import compute_idempotency_key, compute_params_hash, sanitize_params


DATASET_INDUSTRY_CLASSIFICATION = "industry_classification"
DATASET_MARKET_CAP = "market_cap"
DATASET_LIQUIDITY_CAPACITY = "liquidity_capacity"

CANONICAL_INDUSTRY_CLASSIFICATION_COLUMNS = (
    "symbol",
    "industry_code",
    "industry_name",
    "classification_standard",
    "effective_date",
    "available_date",
    "available_at",
    "available_at_rule",
    "pit_status",
    "readiness_status",
    "source",
    "source_interface",
    "source_run_id",
    "schema_version",
    "lineage_raw_checksum",
)

CANONICAL_MARKET_CAP_COLUMNS = (
    "trade_date",
    "symbol",
    "market_cap",
    "float_market_cap",
    "turnover_rate",
    "turnover_rate_f",
    "volume_ratio",
    "pe",
    "pe_ttm",
    "pb",
    "ps",
    "ps_ttm",
    "dv_ratio",
    "dv_ttm",
    "total_share",
    "float_share",
    "free_share",
    "market_cap_unit",
    "source",
    "source_interface",
    "source_run_id",
    "available_at",
    "available_at_rule",
    "schema_version",
    "lineage_raw_checksum",
)

CANONICAL_LIQUIDITY_CAPACITY_COLUMNS = (
    "trade_date",
    "symbol",
    "volume",
    "amount",
    "amount_unit",
    "adv20_amount",
    "adv20_volume",
    "turnover_rate",
    "turnover_rate_f",
    "source",
    "source_interface",
    "source_run_id",
    "available_at",
    "available_at_rule",
    "schema_version",
    "lineage_raw_checksum",
)

BENCHMARKS = {
    "HS300": "399300.SZ",
    "ZZ500": "000905.SH",
    "ZZ1000": "000852.SH",
    "CSI_ALL_SHARE": "000985.SH",
}

PRICE_FULL_RUN_PREFIXES = (
    "run-cr014-s14-prices-adj-factor-",
    "run-cr014-s11-full-a-2026-ytd-date-batch-143508",
    "run-stage3-data-update-",
)


@dataclass(slots=True)
class DatasetSummary:
    dataset: str
    rows: int = 0
    paths: list[str] = field(default_factory=list)
    status: str = QUALITY_STATUS_PASS
    notes: list[str] = field(default_factory=list)
    duplicate_keys: int = 0


@dataclass(slots=True)
class BackfillContext:
    layout: LakeLayout
    run_id: str
    start: str
    end: str
    sleep_seconds: float
    dry_run: bool
    summaries: dict[str, DatasetSummary] = field(default_factory=dict)
    network_calls: int = 0


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _parse_day(value: str) -> date:
    text = value.replace("-", "")
    return datetime.strptime(text, "%Y%m%d").date()


def _iso_day(value: Any) -> str:
    text = str(value)
    if len(text) >= 10 and text[4] == "-" and text[7] == "-":
        return text[:10]
    return datetime.strptime(text[:8], "%Y%m%d").date().isoformat()


def _compact_day(value: Any) -> str:
    return _iso_day(value).replace("-", "")


def _timestamp(day: Any, time_text: str) -> str:
    return f"{_iso_day(day)}T{time_text}+08:00"


def _date_ranges_by_year(start: str, end: str) -> list[tuple[int, str, str]]:
    current = _parse_day(start)
    stop = _parse_day(end)
    ranges: list[tuple[int, str, str]] = []
    while current <= stop:
        year_end = min(date(current.year, 12, 31), stop)
        ranges.append((current.year, current.isoformat(), year_end.isoformat()))
        current = year_end + timedelta(days=1)
    return ranges


def _month_ranges(start: str, end: str) -> list[tuple[str, str]]:
    current = date(_parse_day(start).year, _parse_day(start).month, 1)
    stop = _parse_day(end)
    ranges: list[tuple[str, str]] = []
    while current <= stop:
        next_month = date(current.year + (1 if current.month == 12 else 0), 1 if current.month == 12 else current.month + 1, 1)
        month_end = min(next_month - timedelta(days=1), stop)
        month_start = max(current, _parse_day(start))
        ranges.append((month_start.isoformat(), month_end.isoformat()))
        current = next_month
    return ranges


def _clean_records(frame: pd.DataFrame) -> list[dict[str, Any]]:
    if frame is None or frame.empty:
        return []
    clean = frame.where(pd.notna(frame), None)
    records: list[dict[str, Any]] = []
    for row in clean.to_dict("records"):
        converted: dict[str, Any] = {}
        for key, value in row.items():
            if hasattr(value, "item"):
                value = value.item()
            converted[str(key)] = value
        records.append(converted)
    return records


def _hash_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _frame_checksum(frame: pd.DataFrame, dataset: str) -> str:
    payload = f"{dataset}:{len(frame)}:{','.join(frame.columns)}"
    if not frame.empty:
        payload += f":{frame.iloc[0].to_json(default_handler=str)}:{frame.iloc[-1].to_json(default_handler=str)}"
    return _hash_text(payload)


def _write_jsonl_raw(
    ctx: BackfillContext,
    *,
    interface: str,
    batch_id: str,
    trade_date: str,
    params: Mapping[str, Any],
    rows: Sequence[Mapping[str, Any]],
) -> str:
    if ctx.dry_run:
        return ""
    params_hash = compute_params_hash(params)
    raw_path = ctx.layout.raw_run_batch_path(
        SOURCE_TUSHARE,
        interface,
        trade_date,
        ctx.run_id,
        batch_id,
    )
    tmp_path = raw_path.with_suffix(raw_path.suffix + ".tmp")
    ensure_parent_dirs_for_write(tmp_path)
    metadata = {
        "_metadata": {
            "schema_version": SCHEMA_VERSION,
            "run_id": ctx.run_id,
            "batch_id": batch_id,
            "source": SOURCE_TUSHARE,
            "interface": interface,
            "params": sanitize_params(params),
            "params_hash": params_hash,
            "row_count": len(rows),
        }
    }
    with tmp_path.open("w", encoding="utf-8") as fh:
        fh.write(json.dumps(metadata, ensure_ascii=False, sort_keys=True) + "\n")
        for row in rows:
            fh.write(json.dumps(dict(row), ensure_ascii=False, sort_keys=True) + "\n")
        fh.flush()
        os.fsync(fh.fileno())
    raw_bytes = tmp_path.read_bytes()
    checksum = hashlib.sha256(raw_bytes).hexdigest()
    tmp_path.replace(raw_path)
    record = {
        "schema_version": SCHEMA_VERSION,
        "run_id": ctx.run_id,
        "batch_id": batch_id,
        "idempotency_key": compute_idempotency_key(
            ctx.run_id,
            batch_id,
            SOURCE_TUSHARE,
            interface,
            params_hash,
        ),
        "source": SOURCE_TUSHARE,
        "interface": interface,
        "params": sanitize_params(params),
        "params_hash": params_hash,
        "requested_at": _iso_now(),
        "started_at": _iso_now(),
        "finished_at": _iso_now(),
        "attempts": 1,
        "status": "success",
        "raw_path": str(raw_path.relative_to(ctx.layout.lake_root)),
        "raw_checksum": checksum,
        "raw_row_count": len(rows),
        "canonical_path": "",
        "error_type": "",
        "error_message": "",
        "retryable": False,
    }
    manifest_path = ctx.layout.manifest_path()
    ensure_parent_dirs_for_write(manifest_path)
    with manifest_path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
        fh.flush()
        os.fsync(fh.fileno())
    return checksum


def _write_parquet(ctx: BackfillContext, dataset: str, frame: pd.DataFrame, name: str) -> Path:
    path = (
        ctx.layout.canonical_dataset_root(dataset, SCHEMA_VERSION)
        / f"run_id={ctx.run_id}"
        / name
    )
    if ctx.dry_run:
        return path
    tmp_path = path.with_name(path.name + ".tmp")
    ensure_parent_dirs_for_write(tmp_path)
    frame.to_parquet(tmp_path, index=False)
    with tmp_path.open("rb") as fh:
        os.fsync(fh.fileno())
    tmp_path.replace(path)
    return path


def _summary(ctx: BackfillContext, dataset: str) -> DatasetSummary:
    if dataset not in ctx.summaries:
        ctx.summaries[dataset] = DatasetSummary(dataset=dataset)
    return ctx.summaries[dataset]


def _append_summary(ctx: BackfillContext, dataset: str, frame: pd.DataFrame, path: Path, keys: Sequence[str]) -> None:
    summary = _summary(ctx, dataset)
    summary.rows += int(len(frame))
    summary.paths.append(str(path.relative_to(ctx.layout.lake_root)))
    if keys and not frame.empty:
        duplicate_count = int(frame.duplicated(list(keys)).sum())
        summary.duplicate_keys += duplicate_count
        if duplicate_count:
            summary.status = "fail"
            summary.notes.append(f"duplicate_keys={duplicate_count}")


def _fetch(pro: Any, method_name: str, ctx: BackfillContext, *, retries: int = 3, **params: Any) -> pd.DataFrame:
    method = getattr(pro, method_name)
    last_error: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            frame = method(**params)
            ctx.network_calls += 1
            if ctx.sleep_seconds:
                time.sleep(ctx.sleep_seconds)
            return frame if isinstance(frame, pd.DataFrame) else pd.DataFrame()
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            if ctx.sleep_seconds:
                time.sleep(max(ctx.sleep_seconds, 0.5) * attempt)
    raise RuntimeError(f"Tushare {method_name} 调用失败: {last_error}") from last_error


def _open_trade_dates(ctx: BackfillContext) -> list[str]:
    paths = sorted((ctx.layout.canonical_dataset_root("trade_calendar", SCHEMA_VERSION)).glob("run_id=*/*.parquet"))
    frames: list[pd.DataFrame] = []
    for path in paths:
        try:
            frame = pd.read_parquet(path, columns=["trade_date", "is_open"])
        except Exception:
            continue
        frame["trade_date"] = frame["trade_date"].astype(str)
        frames.append(frame)
    if not frames:
        raise RuntimeError("缺少 trade_calendar canonical，无法确定开市日期分母")
    calendar = pd.concat(frames, ignore_index=True).drop_duplicates(["trade_date"])
    calendar = calendar[
        (calendar["trade_date"] >= ctx.start)
        & (calendar["trade_date"] <= ctx.end)
        & (calendar["is_open"].astype(bool))
    ]
    return sorted(calendar["trade_date"].tolist())


def _price_paths(ctx: BackfillContext) -> list[Path]:
    root = ctx.layout.canonical_dataset_root("prices", SCHEMA_VERSION)
    paths: list[Path] = []
    for run_dir in sorted(root.glob("run_id=*")):
        run_id = run_dir.name.removeprefix("run_id=")
        if run_id.startswith(PRICE_FULL_RUN_PREFIXES):
            paths.extend(sorted(run_dir.glob("*.parquet")))
    if not paths:
        raise RuntimeError("缺少 2015 至今 prices candidate，无法构造 trade_status / liquidity 分母")
    return paths


def refresh_prices_volume_amount(ctx: BackfillContext) -> None:
    manifest_path = ctx.layout.manifest_path()
    run_ids = sorted(
        {
            path.parent.name.removeprefix("run_id=")
            for path in _price_paths(ctx)
        }
    )
    for run_id in run_ids:
        print(f"[prices] refresh canonical volume/amount from raw: {run_id}", flush=True)
        if not ctx.dry_run:
            normalize_run(manifest_path, ctx.layout.lake_root, dataset="prices", run_id=run_id)
    summary = _summary(ctx, "prices")
    summary.notes.append("refreshed volume/amount from existing raw prices.daily")


def backfill_stock_basic_and_industry(pro: Any, ctx: BackfillContext) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    fields = "ts_code,symbol,name,area,industry,market,list_date,delist_date,is_hs"
    for status in ("L", "D", "P"):
        frame = _fetch(pro, "stock_basic", ctx, exchange="", list_status=status, fields=fields)
        part = _clean_records(frame)
        for row in part:
            row["list_status"] = status
        rows.extend(part)
    raw_checksum = _write_jsonl_raw(
        ctx,
        interface=INTERFACE_STOCK_BASIC_SNAPSHOT,
        batch_id="stock-basic-l-d-p",
        trade_date=ctx.end,
        params={"target_dataset": DATASET_STOCK_BASIC, "snapshot_date": ctx.end, "list_status": "L,D,P"},
        rows=rows,
    )
    canonical_rows: list[dict[str, Any]] = []
    industry_rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    status_priority = {"L": 0, "D": 1, "P": 2}
    for row in sorted(rows, key=lambda item: (str(item.get("ts_code") or item.get("symbol")), status_priority.get(str(item.get("list_status")), 9))):
        symbol = str(row.get("ts_code") or "").strip().upper()
        if not symbol or symbol in seen:
            continue
        seen.add(symbol)
        list_date = _iso_day(row["list_date"]) if row.get("list_date") else ""
        delist_date = _iso_day(row["delist_date"]) if row.get("delist_date") else ""
        effective_date = list_date or ctx.end
        canonical_rows.append(
            {
                "symbol": symbol,
                "name": str(row.get("name") or ""),
                "market": str(row.get("market") or ""),
                "list_status": str(row.get("list_status") or ""),
                "list_date": list_date,
                "delist_date": delist_date,
                "effective_date": effective_date,
                "available_date": ctx.end,
                "available_at": _timestamp(ctx.end, "00:00:00"),
                "available_at_rule": "tushare_stock_basic_snapshot",
                "pit_status": PIT_STATUS_AVAILABLE,
                "readiness_status": READINESS_STATUS_AVAILABLE,
                "source": SOURCE_TUSHARE,
                "source_interface": INTERFACE_STOCK_BASIC_SNAPSHOT,
                "source_run_id": ctx.run_id,
                "schema_version": SCHEMA_VERSION,
                "lineage_raw_checksum": raw_checksum,
            }
        )
        industry = str(row.get("industry") or "").strip()
        if industry:
            industry_rows.append(
                {
                    "symbol": symbol,
                    "industry_code": "",
                    "industry_name": industry,
                    "classification_standard": "tushare_stock_basic_industry",
                    "effective_date": effective_date,
                    "available_date": ctx.end,
                    "available_at": _timestamp(ctx.end, "00:00:00"),
                    "available_at_rule": "tushare_stock_basic_snapshot",
                    "pit_status": PIT_STATUS_NON_PIT_SNAPSHOT,
                    "readiness_status": READINESS_STATUS_NON_PIT_SNAPSHOT,
                    "source": SOURCE_TUSHARE,
                    "source_interface": "industry_classification.snapshot",
                    "source_run_id": ctx.run_id,
                    "schema_version": SCHEMA_VERSION,
                    "lineage_raw_checksum": raw_checksum,
                }
            )
    stock_frame = pd.DataFrame(canonical_rows, columns=CANONICAL_STOCK_BASIC_COLUMNS)
    stock_path = _write_parquet(ctx, DATASET_STOCK_BASIC, stock_frame, "part-stock-basic-lifecycle.parquet")
    _append_summary(ctx, DATASET_STOCK_BASIC, stock_frame, stock_path, ("symbol",))
    industry_frame = pd.DataFrame(industry_rows, columns=CANONICAL_INDUSTRY_CLASSIFICATION_COLUMNS)
    industry_path = _write_parquet(ctx, DATASET_INDUSTRY_CLASSIFICATION, industry_frame, "part-industry-classification.parquet")
    _append_summary(ctx, DATASET_INDUSTRY_CLASSIFICATION, industry_frame, industry_path, ("symbol",))
    _summary(ctx, DATASET_INDUSTRY_CLASSIFICATION).notes.append("Tushare stock_basic industry is a snapshot, not historical SW PIT industry")
    return stock_frame


def backfill_benchmarks(pro: Any, ctx: BackfillContext) -> None:
    index_daily_frames: list[pd.DataFrame] = []
    weight_frames: list[pd.DataFrame] = []
    for benchmark_id, index_code in BENCHMARKS.items():
        print(f"[benchmark] {benchmark_id} {index_code}", flush=True)
        daily = _fetch(
            pro,
            "index_daily",
            ctx,
            ts_code=index_code,
            start_date=_compact_day(ctx.start),
            end_date=_compact_day(ctx.end),
        )
        daily_rows = _clean_records(daily)
        checksum = _write_jsonl_raw(
            ctx,
            interface=INTERFACE_HS300_INDEX_DAILY,
            batch_id=f"benchmark-{benchmark_id.lower()}-daily",
            trade_date=ctx.start,
            params={
                "target_dataset": DATASET_HS300_INDEX,
                "index_code": index_code,
                "benchmark_id": benchmark_id,
                "benchmark_kind": "price_index",
                "start_date": ctx.start,
                "end_date": ctx.end,
            },
            rows=daily_rows,
        )
        normalised_daily: list[dict[str, Any]] = []
        for row in daily_rows:
            trade_date = _iso_day(row["trade_date"])
            normalised_daily.append(
                {
                    "trade_date": trade_date,
                    "index_code": str(row.get("ts_code") or index_code).upper(),
                    "close": row.get("close"),
                    "pre_close": row.get("pre_close"),
                    "pct_chg": row.get("pct_chg"),
                    "open": row.get("open"),
                    "high": row.get("high"),
                    "low": row.get("low"),
                    "volume": row.get("vol"),
                    "amount": row.get("amount"),
                    "benchmark_kind": "price_index",
                    "source": SOURCE_TUSHARE,
                    "source_interface": INTERFACE_HS300_INDEX_DAILY,
                    "source_run_id": ctx.run_id,
                    "schema_version": SCHEMA_VERSION,
                    "available_at": _timestamp(trade_date, "16:00:00"),
                    "available_at_rule": "daily_close_fact",
                    "lineage_raw_checksum": checksum,
                }
            )
        index_daily_frames.append(pd.DataFrame(normalised_daily, columns=CANONICAL_HS300_INDEX_COLUMNS))

        for year, range_start, range_end in _date_ranges_by_year(ctx.start, ctx.end):
            weights = _fetch(
                pro,
                "index_weight",
                ctx,
                index_code=index_code,
                start_date=_compact_day(range_start),
                end_date=_compact_day(range_end),
            )
            rows = _clean_records(weights)
            checksum = _write_jsonl_raw(
                ctx,
                interface=INTERFACE_INDEX_WEIGHTS_SNAPSHOT,
                batch_id=f"benchmark-{benchmark_id.lower()}-weights-{year}",
                trade_date=range_start,
                params={
                    "target_dataset": DATASET_INDEX_WEIGHTS,
                    "index_code": index_code,
                    "benchmark_id": benchmark_id,
                    "start_date": range_start,
                    "end_date": range_end,
                },
                rows=rows,
            )
            normalised_weights: list[dict[str, Any]] = []
            for row in rows:
                trade_date = _iso_day(row["trade_date"])
                normalised_weights.append(
                    {
                        "trade_date": trade_date,
                        "index_code": str(row.get("index_code") or index_code).upper(),
                        "con_code": str(row.get("con_code") or "").upper(),
                        "weight": row.get("weight"),
                        "effective_date": trade_date,
                        "available_date": trade_date,
                        "available_at": _timestamp(trade_date, "16:00:00"),
                        "available_at_rule": "tushare_index_weight_effective_date_16:00",
                        "pit_status": PIT_STATUS_AVAILABLE,
                        "readiness_status": READINESS_STATUS_AVAILABLE,
                        "source": SOURCE_TUSHARE,
                        "source_interface": INTERFACE_INDEX_WEIGHTS_SNAPSHOT,
                        "source_run_id": ctx.run_id,
                        "schema_version": SCHEMA_VERSION,
                        "lineage_raw_checksum": checksum,
                    }
                )
            if normalised_weights:
                weight_frames.append(pd.DataFrame(normalised_weights, columns=CANONICAL_INDEX_WEIGHTS_COLUMNS))
    index_frame = pd.concat(index_daily_frames, ignore_index=True).drop_duplicates(["trade_date", "index_code"])
    index_path = _write_parquet(ctx, DATASET_HS300_INDEX, index_frame, "part-benchmark-index-daily.parquet")
    _append_summary(ctx, DATASET_HS300_INDEX, index_frame, index_path, ("trade_date", "index_code"))

    weights_frame = pd.concat(weight_frames, ignore_index=True).drop_duplicates(["trade_date", "index_code", "con_code"])
    weights_path = _write_parquet(ctx, DATASET_INDEX_WEIGHTS, weights_frame, "part-benchmark-index-weights.parquet")
    _append_summary(ctx, DATASET_INDEX_WEIGHTS, weights_frame, weights_path, ("trade_date", "index_code", "con_code"))

    members = weights_frame.assign(
        in_date="",
        out_date="",
        is_member=True,
        is_pit_universe=True,
        derived_from="index_weight",
    )
    members = members.rename(columns={"weight": "_weight"})
    members_frame = pd.DataFrame(
        {
            "trade_date": members["trade_date"],
            "index_code": members["index_code"],
            "con_code": members["con_code"],
            "in_date": members["in_date"],
            "out_date": members["out_date"],
            "is_member": members["is_member"],
            "effective_date": members["effective_date"],
            "available_date": members["available_date"],
            "available_at": members["available_at"],
            "available_at_rule": members["available_at_rule"],
            "is_pit_universe": members["is_pit_universe"],
            "pit_status": members["pit_status"],
            "readiness_status": members["readiness_status"],
            "source": members["source"],
            "source_interface": members["source_interface"],
            "source_run_id": members["source_run_id"],
            "schema_version": members["schema_version"],
            "lineage_raw_checksum": members["lineage_raw_checksum"],
            "derived_from": members["derived_from"],
        },
        columns=CANONICAL_INDEX_MEMBERS_COLUMNS,
    ).drop_duplicates(["trade_date", "index_code", "con_code"])
    members_path = _write_parquet(ctx, DATASET_INDEX_MEMBERS, members_frame, "part-benchmark-index-members.parquet")
    _append_summary(ctx, DATASET_INDEX_MEMBERS, members_frame, members_path, ("trade_date", "index_code", "con_code"))


def backfill_prices_limit(pro: Any, ctx: BackfillContext, open_dates: Sequence[str]) -> None:
    dates_by_year: dict[int, list[str]] = defaultdict(list)
    for item in open_dates:
        dates_by_year[_parse_day(item).year].append(item)
    for year, dates in sorted(dates_by_year.items()):
        print(f"[prices_limit] {year} dates={len(dates)}", flush=True)
        rows: list[dict[str, Any]] = []
        for trade_date in dates:
            frame = _fetch(pro, "stk_limit", ctx, trade_date=_compact_day(trade_date))
            for row in _clean_records(frame):
                if not row.get("ts_code"):
                    continue
                rows.append(
                    {
                        "trade_date": _iso_day(row.get("trade_date") or trade_date),
                        "symbol": str(row.get("ts_code")).upper(),
                        "limit_up": row.get("up_limit"),
                        "limit_down": row.get("down_limit"),
                        "source": SOURCE_TUSHARE,
                        "source_interface": INTERFACE_PRICES_LIMIT_DAILY,
                        "source_run_id": ctx.run_id,
                        "available_at": _timestamp(trade_date, "08:40:00"),
                        "available_at_rule": "tushare_stk_limit_08:40",
                        "schema_version": SCHEMA_VERSION,
                        "lineage_raw_checksum": "",
                    }
                )
        raw_checksum = _write_jsonl_raw(
            ctx,
            interface=INTERFACE_PRICES_LIMIT_DAILY,
            batch_id=f"prices-limit-{year}",
            trade_date=f"{year}-01-01",
            params={"target_dataset": DATASET_PRICES_LIMIT, "year": year, "start_date": dates[0], "end_date": dates[-1]},
            rows=rows,
        )
        for row in rows:
            row["lineage_raw_checksum"] = raw_checksum
        frame = pd.DataFrame(rows, columns=CANONICAL_PRICES_LIMIT_COLUMNS).drop_duplicates(["trade_date", "symbol"])
        path = _write_parquet(ctx, DATASET_PRICES_LIMIT, frame, f"part-prices-limit-{year}.parquet")
        _append_summary(ctx, DATASET_PRICES_LIMIT, frame, path, ("trade_date", "symbol"))


def _fetch_stock_st_recursive(pro: Any, ctx: BackfillContext, start: str, end: str) -> pd.DataFrame:
    frame = _fetch(pro, "stock_st", ctx, start_date=_compact_day(start), end_date=_compact_day(end))
    if len(frame) < 1000 or start == end:
        return frame
    start_day = _parse_day(start)
    end_day = _parse_day(end)
    mid_day = start_day + timedelta(days=(end_day - start_day).days // 2)
    left = _fetch_stock_st_recursive(pro, ctx, start, mid_day.isoformat())
    right_start = (mid_day + timedelta(days=1)).isoformat()
    right = _fetch_stock_st_recursive(pro, ctx, right_start, end)
    return pd.concat([left, right], ignore_index=True)


def fetch_suspend_and_st(pro: Any, ctx: BackfillContext, open_dates: Sequence[str]) -> tuple[pd.DataFrame, pd.DataFrame]:
    suspend_rows: list[dict[str, Any]] = []
    for idx, trade_date in enumerate(open_dates, start=1):
        if idx == 1 or idx % 100 == 0:
            print(f"[suspend_d] {idx}/{len(open_dates)} {trade_date}", flush=True)
        frame = _fetch(pro, "suspend_d", ctx, trade_date=_compact_day(trade_date))
        for row in _clean_records(frame):
            if row.get("ts_code"):
                suspend_rows.append(
                    {
                        "trade_date": _iso_day(row.get("trade_date") or trade_date),
                        "symbol": str(row.get("ts_code")).upper(),
                        "suspend_timing": row.get("suspend_timing") or "",
                        "suspend_type": row.get("suspend_type") or "",
                    }
                )
    suspend_frame = pd.DataFrame(suspend_rows, columns=["trade_date", "symbol", "suspend_timing", "suspend_type"]).drop_duplicates(["trade_date", "symbol"])
    _write_jsonl_raw(
        ctx,
        interface=INTERFACE_TRADE_STATUS_DAILY,
        batch_id="suspend-d-full-range",
        trade_date=ctx.start,
        params={"target_dataset": DATASET_TRADE_STATUS, "source_fact": "suspend_d", "start_date": ctx.start, "end_date": ctx.end},
        rows=suspend_rows,
    )
    st_frames: list[pd.DataFrame] = []
    for start, end in _month_ranges(ctx.start, ctx.end):
        print(f"[stock_st] {start}..{end}", flush=True)
        st_frames.append(_fetch_stock_st_recursive(pro, ctx, start, end))
    st_frame = pd.concat(st_frames, ignore_index=True) if st_frames else pd.DataFrame()
    st_rows = _clean_records(st_frame)
    _write_jsonl_raw(
        ctx,
        interface=INTERFACE_EVENTS_DISCLOSURE,
        batch_id="stock-st-full-range",
        trade_date=ctx.start,
        params={"target_dataset": DATASET_EVENTS, "source_fact": "stock_st", "start_date": ctx.start, "end_date": ctx.end},
        rows=st_rows,
    )
    if st_frame.empty:
        st_frame = pd.DataFrame(columns=["ts_code", "trade_date", "type", "type_name", "name"])
    st_frame = st_frame.rename(columns={"ts_code": "symbol"})
    if "trade_date" in st_frame:
        st_frame["trade_date"] = st_frame["trade_date"].map(_iso_day)
    if "symbol" in st_frame:
        st_frame["symbol"] = st_frame["symbol"].astype(str).str.upper()
    st_frame = st_frame.drop_duplicates(["trade_date", "symbol"])
    return suspend_frame, st_frame


def backfill_trade_status_and_events(ctx: BackfillContext, suspend_frame: pd.DataFrame, st_frame: pd.DataFrame) -> None:
    st_keys = st_frame[["trade_date", "symbol"]].copy() if {"trade_date", "symbol"} <= set(st_frame.columns) else pd.DataFrame(columns=["trade_date", "symbol"])
    st_keys["_is_st"] = True
    suspend_keys = suspend_frame[["trade_date", "symbol"]].copy() if not suspend_frame.empty else pd.DataFrame(columns=["trade_date", "symbol"])
    suspend_keys["_is_suspended"] = True
    price_paths = _price_paths(ctx)
    frames_by_year: dict[int, list[pd.DataFrame]] = defaultdict(list)
    for path in price_paths:
        frame = pd.read_parquet(path, columns=["trade_date", "symbol"])
        frame["trade_date"] = frame["trade_date"].astype(str)
        frame = frame[(frame["trade_date"] >= ctx.start) & (frame["trade_date"] <= ctx.end)]
        if frame.empty:
            continue
        for year, part in frame.groupby(frame["trade_date"].str[:4]):
            frames_by_year[int(year)].append(part[["trade_date", "symbol"]])

    for year, parts in sorted(frames_by_year.items()):
        print(f"[trade_status] {year}", flush=True)
        pairs = pd.concat(parts, ignore_index=True).drop_duplicates(["trade_date", "symbol"])
        pairs = pairs.merge(suspend_keys, on=["trade_date", "symbol"], how="left")
        pairs = pairs.merge(st_keys, on=["trade_date", "symbol"], how="left")
        pairs["is_suspended"] = pairs["_is_suspended"].eq(True)
        pairs["is_st"] = pairs["_is_st"].eq(True)
        pairs["is_tradable"] = ~pairs["is_suspended"]
        pairs["status_reason"] = ""
        pairs.loc[pairs["is_suspended"], "status_reason"] = "suspended"
        pairs.loc[pairs["is_st"] & ~pairs["is_suspended"], "status_reason"] = "st"
        checksum = _hash_text(f"{ctx.run_id}:trade_status:{year}:{len(pairs)}")
        pairs["source"] = SOURCE_TUSHARE
        pairs["source_interface"] = INTERFACE_TRADE_STATUS_DAILY
        pairs["source_run_id"] = ctx.run_id
        pairs["available_at"] = pairs["trade_date"].map(lambda value: _timestamp(value, "09:30:00"))
        pairs["available_at_rule"] = "tushare_suspend_d_09:30_stock_st_09:20_daily"
        pairs["schema_version"] = SCHEMA_VERSION
        pairs["lineage_raw_checksum"] = checksum
        frame = pairs[list(CANONICAL_TRADE_STATUS_COLUMNS)].sort_values(["trade_date", "symbol"]).reset_index(drop=True)
        path = _write_parquet(ctx, DATASET_TRADE_STATUS, frame, f"part-trade-status-{year}.parquet")
        _append_summary(ctx, DATASET_TRADE_STATUS, frame, path, ("trade_date", "symbol"))

    event_rows: list[dict[str, Any]] = []
    for row in _clean_records(st_frame):
        symbol = str(row.get("symbol") or "").upper()
        trade_date = row.get("trade_date")
        if not symbol or not trade_date:
            continue
        event_rows.append(
            {
                "symbol": symbol,
                "event_type": "st_status",
                "event_date": _iso_day(trade_date),
                "available_at": _timestamp(trade_date, "09:20:00"),
                "available_at_rule": "tushare_stock_st_09:20",
                "payload": json.dumps(row, ensure_ascii=False, sort_keys=True),
                "source": SOURCE_TUSHARE,
                "source_interface": INTERFACE_EVENTS_DISCLOSURE,
                "source_run_id": ctx.run_id,
                "schema_version": SCHEMA_VERSION,
                "lineage_raw_checksum": _hash_text(f"{ctx.run_id}:stock_st:{len(st_frame)}"),
            }
        )
    events = pd.DataFrame(event_rows, columns=CANONICAL_EVENTS_COLUMNS).drop_duplicates(["symbol", "event_type", "event_date", "available_at"])
    path = _write_parquet(ctx, DATASET_EVENTS, events, "part-events-stock-st.parquet")
    _append_summary(ctx, DATASET_EVENTS, events, path, ("symbol", "event_type", "event_date", "available_at"))


def backfill_daily_basic_market_cap(pro: Any, ctx: BackfillContext, open_dates: Sequence[str]) -> None:
    dates_by_year: dict[int, list[str]] = defaultdict(list)
    for item in open_dates:
        dates_by_year[_parse_day(item).year].append(item)
    fields = ",".join(
        [
            "ts_code",
            "trade_date",
            "turnover_rate",
            "turnover_rate_f",
            "volume_ratio",
            "pe",
            "pe_ttm",
            "pb",
            "ps",
            "ps_ttm",
            "dv_ratio",
            "dv_ttm",
            "total_share",
            "float_share",
            "free_share",
            "total_mv",
            "circ_mv",
        ]
    )
    for year, dates in sorted(dates_by_year.items()):
        print(f"[daily_basic/market_cap] {year} dates={len(dates)}", flush=True)
        rows: list[dict[str, Any]] = []
        for trade_date in dates:
            frame = _fetch(pro, "daily_basic", ctx, trade_date=_compact_day(trade_date), fields=fields)
            checksum_seed = f"{ctx.run_id}:daily_basic:{trade_date}:{len(frame)}"
            checksum = _hash_text(checksum_seed)
            for row in _clean_records(frame):
                if not row.get("ts_code"):
                    continue
                rows.append(
                    {
                        "trade_date": _iso_day(row.get("trade_date") or trade_date),
                        "symbol": str(row.get("ts_code")).upper(),
                        "market_cap": row.get("total_mv"),
                        "float_market_cap": row.get("circ_mv"),
                        "turnover_rate": row.get("turnover_rate"),
                        "turnover_rate_f": row.get("turnover_rate_f"),
                        "volume_ratio": row.get("volume_ratio"),
                        "pe": row.get("pe"),
                        "pe_ttm": row.get("pe_ttm"),
                        "pb": row.get("pb"),
                        "ps": row.get("ps"),
                        "ps_ttm": row.get("ps_ttm"),
                        "dv_ratio": row.get("dv_ratio"),
                        "dv_ttm": row.get("dv_ttm"),
                        "total_share": row.get("total_share"),
                        "float_share": row.get("float_share"),
                        "free_share": row.get("free_share"),
                        "market_cap_unit": "ten_thousand_cny",
                        "source": SOURCE_TUSHARE,
                        "source_interface": "daily_basic.daily",
                        "source_run_id": ctx.run_id,
                        "available_at": _timestamp(trade_date, "16:00:00"),
                        "available_at_rule": "tushare_daily_basic_16:00",
                        "schema_version": SCHEMA_VERSION,
                        "lineage_raw_checksum": checksum,
                    }
                )
        _write_jsonl_raw(
            ctx,
            interface="daily_basic.daily",
            batch_id=f"daily-basic-{year}",
            trade_date=f"{year}-01-01",
            params={"target_dataset": DATASET_MARKET_CAP, "year": year, "start_date": dates[0], "end_date": dates[-1]},
            rows=rows,
        )
        frame = pd.DataFrame(rows, columns=CANONICAL_MARKET_CAP_COLUMNS).drop_duplicates(["trade_date", "symbol"])
        path = _write_parquet(ctx, DATASET_MARKET_CAP, frame, f"part-market-cap-{year}.parquet")
        _append_summary(ctx, DATASET_MARKET_CAP, frame, path, ("trade_date", "symbol"))


def backfill_liquidity_capacity(ctx: BackfillContext) -> None:
    print("[liquidity_capacity] derive volume/amount/ADV20 from prices + turnover from market_cap", flush=True)
    price_frames: list[pd.DataFrame] = []
    for path in _price_paths(ctx):
        try:
            frame = pd.read_parquet(path, columns=["trade_date", "symbol", "volume", "amount"])
        except Exception:
            continue
        frame["trade_date"] = frame["trade_date"].astype(str)
        frame = frame[(frame["trade_date"] >= ctx.start) & (frame["trade_date"] <= ctx.end)]
        if not frame.empty:
            price_frames.append(frame)
    if not price_frames:
        _summary(ctx, DATASET_LIQUIDITY_CAPACITY).status = "fail"
        _summary(ctx, DATASET_LIQUIDITY_CAPACITY).notes.append("prices volume/amount unavailable")
        return
    prices = pd.concat(price_frames, ignore_index=True).drop_duplicates(["trade_date", "symbol"])
    cap_paths = sorted((ctx.layout.canonical_dataset_root(DATASET_MARKET_CAP, SCHEMA_VERSION) / f"run_id={ctx.run_id}").glob("*.parquet"))
    cap_frames = [pd.read_parquet(path, columns=["trade_date", "symbol", "turnover_rate", "turnover_rate_f"]) for path in cap_paths]
    caps = pd.concat(cap_frames, ignore_index=True).drop_duplicates(["trade_date", "symbol"]) if cap_frames else pd.DataFrame(columns=["trade_date", "symbol", "turnover_rate", "turnover_rate_f"])
    frame = prices.merge(caps, on=["trade_date", "symbol"], how="left")
    frame = frame.sort_values(["symbol", "trade_date"]).reset_index(drop=True)
    frame["adv20_amount"] = frame.groupby("symbol")["amount"].transform(lambda series: series.rolling(20, min_periods=5).mean())
    frame["adv20_volume"] = frame.groupby("symbol")["volume"].transform(lambda series: series.rolling(20, min_periods=5).mean())
    frame["amount_unit"] = "thousand_cny"
    frame["source"] = SOURCE_TUSHARE
    frame["source_interface"] = "prices.daily+daily_basic.daily"
    frame["source_run_id"] = ctx.run_id
    frame["available_at"] = frame["trade_date"].map(lambda value: _timestamp(value, "16:00:00"))
    frame["available_at_rule"] = "daily_close_fact"
    frame["schema_version"] = SCHEMA_VERSION
    frame["lineage_raw_checksum"] = _frame_checksum(frame, DATASET_LIQUIDITY_CAPACITY)
    frame = frame[list(CANONICAL_LIQUIDITY_CAPACITY_COLUMNS)].sort_values(["trade_date", "symbol"]).reset_index(drop=True)
    for year, part in frame.groupby(frame["trade_date"].str[:4]):
        path = _write_parquet(ctx, DATASET_LIQUIDITY_CAPACITY, part, f"part-liquidity-capacity-{year}.parquet")
        _append_summary(ctx, DATASET_LIQUIDITY_CAPACITY, part, path, ("trade_date", "symbol"))


def _catalog_upsert(ctx: BackfillContext, dataset: str, summary: DatasetSummary) -> None:
    if ctx.dry_run or not summary.paths:
        return
    store = CatalogStore(ctx.layout)
    entry = CatalogEntry(
        dataset=dataset,
        schema_version=SCHEMA_VERSION,
        start_date=ctx.start,
        end_date=ctx.end,
        coverage={
            "run_id": ctx.run_id,
            "dataset": dataset,
            "actual_rows": summary.rows,
            "duplicate_key_count": summary.duplicate_keys,
            "status": summary.status,
            "notes": summary.notes,
        },
        quality_status=summary.status,
        dataset_status="available" if summary.status == QUALITY_STATUS_PASS else "fail",
        latest_manifest_run_id=ctx.run_id,
        source=SOURCE_TUSHARE,
        source_interface="cr018_real_backfill_missing_data",
        lineage_raw_checksum=_hash_text(json.dumps(summary.paths, sort_keys=True)),
        canonical_path=summary.paths[0],
        generated_at=_iso_now(),
        updated_at=_iso_now(),
        published=False,
        readiness_status=READINESS_STATUS_AVAILABLE if summary.status == QUALITY_STATUS_PASS else "quality_failed",
        pit_status=PIT_STATUS_AVAILABLE if dataset in {DATASET_INDEX_MEMBERS, DATASET_INDEX_WEIGHTS, DATASET_STOCK_BASIC} else None,
        coverage_denominator=summary.rows,
        coverage_ratio=1.0 if summary.rows else 0.0,
        coverage_start=ctx.start,
        coverage_end=ctx.end,
        known_limitations=[{"code": note} for note in summary.notes],
    )
    store.upsert(entry)


def write_summary(ctx: BackfillContext) -> Path:
    payload = {
        "run_id": ctx.run_id,
        "start": ctx.start,
        "end": ctx.end,
        "generated_at": _iso_now(),
        "network_calls": ctx.network_calls,
        "dry_run": ctx.dry_run,
        "qmt_operation_count": 0,
        "current_pointer_publish_count": 0,
        "datasets": {
            key: {
                "rows": value.rows,
                "paths": value.paths,
                "status": value.status,
                "notes": value.notes,
                "duplicate_keys": value.duplicate_keys,
            }
            for key, value in sorted(ctx.summaries.items())
        },
    }
    if not ctx.dry_run:
        for dataset, summary in ctx.summaries.items():
            _catalog_upsert(ctx, dataset, summary)
    summary_path = ctx.layout.quality_root / ctx.run_id / "cr018_missing_data_backfill_summary.json"
    md_path = ctx.layout.quality_root / ctx.run_id / "cr018_missing_data_backfill_summary.md"
    if not ctx.dry_run:
        ensure_parent_dirs_for_write(summary_path)
        summary_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        lines = [
            "# CR018 Missing Data Backfill Summary",
            "",
            f"- run_id: `{ctx.run_id}`",
            f"- range: `{ctx.start}`..`{ctx.end}`",
            f"- network_calls: `{ctx.network_calls}`",
            "- qmt_operation_count: `0`",
            "- current_pointer_publish_count: `0`",
            "",
            "| dataset | rows | status | duplicate_keys |",
            "|---|---:|---|---:|",
        ]
        for dataset, summary in sorted(ctx.summaries.items()):
            lines.append(f"| `{dataset}` | {summary.rows} | `{summary.status}` | {summary.duplicate_keys} |")
        md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return summary_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="补齐生产级市场数据湖缺口")
    parser.add_argument("--lake-root", default=os.environ.get("MARKET_DATA_LAKE_ROOT", ""))
    parser.add_argument("--start", default="2015-01-01")
    parser.add_argument("--end", default="2026-05-28")
    parser.add_argument("--run-id", default="")
    parser.add_argument("--sleep-seconds", type=float, default=0.05)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--skip-refresh-prices", action="store_true")
    parser.add_argument(
        "--datasets",
        default="prices_refresh,stock_basic,benchmarks,prices_limit,trade_status,events,market_cap,liquidity",
        help="逗号分隔：prices_refresh,stock_basic,benchmarks,prices_limit,trade_status,events,market_cap,liquidity",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.lake_root:
        raise RuntimeError("缺少 --lake-root 或 MARKET_DATA_LAKE_ROOT")
    token = os.environ.get("TUSHARE_TOKEN")
    if not token:
        raise RuntimeError("缺少 TUSHARE_TOKEN")
    run_id = args.run_id or f"run-cr018-missing-data-backfill-{_compact_day(args.start)}-{_compact_day(args.end)}-{datetime.now().strftime('%H%M%S')}"
    ctx = BackfillContext(
        layout=LakeLayout(Path(args.lake_root)),
        run_id=run_id,
        start=_iso_day(args.start),
        end=_iso_day(args.end),
        sleep_seconds=args.sleep_seconds,
        dry_run=bool(args.dry_run),
    )
    selected = {item.strip() for item in str(args.datasets).split(",") if item.strip()}
    pro = ts.pro_api(token)
    open_dates = _open_trade_dates(ctx)
    print(f"[start] run_id={ctx.run_id} range={ctx.start}..{ctx.end} open_dates={len(open_dates)}", flush=True)
    if "prices_refresh" in selected and not args.skip_refresh_prices:
        refresh_prices_volume_amount(ctx)
    stock_frame = pd.DataFrame()
    if "stock_basic" in selected:
        stock_frame = backfill_stock_basic_and_industry(pro, ctx)
        print(f"[stock_basic] rows={len(stock_frame)}", flush=True)
    if "benchmarks" in selected:
        backfill_benchmarks(pro, ctx)
    if "prices_limit" in selected:
        backfill_prices_limit(pro, ctx, open_dates)
    suspend_frame = pd.DataFrame()
    st_frame = pd.DataFrame()
    if {"trade_status", "events"} & selected:
        suspend_frame, st_frame = fetch_suspend_and_st(pro, ctx, open_dates)
    if "trade_status" in selected:
        backfill_trade_status_and_events(ctx, suspend_frame, st_frame)
    elif "events" in selected:
        empty_suspend = pd.DataFrame(columns=["trade_date", "symbol"])
        backfill_trade_status_and_events(ctx, empty_suspend, st_frame)
    if "market_cap" in selected:
        backfill_daily_basic_market_cap(pro, ctx, open_dates)
    if "liquidity" in selected:
        backfill_liquidity_capacity(ctx)
    summary_path = write_summary(ctx)
    print(f"[done] summary={summary_path}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
