"""CR018 prices_limit 生命周期 / 代码变更清理脚本。

该脚本只处理已经确认的价格涨跌停覆盖率缺口：
- BJ: 北交所 2021-11-15 前，或个股北交所有效起始日前，不计入涨跌停分母。
- SZ: 代码变更导致 provider 查询代码和研究侧 symbol 不一致时，补写映射后的涨跌停价。
- SH: 科创板首日无涨跌幅限制，不计入涨跌停分母。

脚本会写入新的 candidate run，不发布 current pointer，不触发 QMT。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

import pandas as pd
import tushare as ts

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from market_data.catalog import CatalogEntry, CatalogStore
from market_data.contracts import (
    CANONICAL_PRICES_LIMIT_COLUMNS,
    DATASET_PRICES_LIMIT,
    QUALITY_STATUS_PASS,
    READINESS_STATUS_AVAILABLE,
    SCHEMA_VERSION,
    SOURCE_TUSHARE,
)
from market_data.lake_layout import LakeLayout, ensure_parent_dirs_for_write
from market_data.storage import compute_idempotency_key, compute_params_hash, sanitize_params


DATASET_BSE_CODE_MAPPING = "bse_code_mapping"
DATASET_LIFECYCLE_CODE_CHANGE = "lifecycle_code_change"
DATASET_PRICES_LIMIT_COVERAGE_EXCLUSIONS = "prices_limit_coverage_exclusions"
DATASET_PRICES_LIMIT_CODE_CHANGE_FIXES = "prices_limit_code_change_fixes"

BSE_FIRST_TRADING_DAY = "2021-11-15"
OLD_PRICES_LIMIT_RUN_ID = "run-cr018-missing-data-backfill-20150101-20260528-p0p1-20260529"

BSE_CODE_MAPPING_COLUMNS = (
    "name",
    "old_code",
    "new_code",
    "list_date",
    "effective_bse_start",
    "source",
    "source_interface",
    "source_run_id",
    "schema_version",
    "lineage_raw_checksum",
)

LIFECYCLE_CODE_CHANGE_COLUMNS = (
    "canonical_symbol",
    "source_symbol",
    "mapping_type",
    "effective_date",
    "valid_start",
    "valid_end",
    "name",
    "reason",
    "source",
    "source_interface",
    "source_run_id",
    "schema_version",
    "lineage_raw_checksum",
)

CODE_CHANGE_FIX_COLUMNS = (
    "trade_date",
    "symbol",
    "source_symbol",
    "limit_up",
    "limit_down",
    "mapping_type",
    "mapping_effective_date",
    "reason",
    "source",
    "source_interface",
    "source_run_id",
    "schema_version",
    "lineage_raw_checksum",
)

COVERAGE_EXCLUSION_COLUMNS = (
    "trade_date",
    "symbol",
    "exclusion_reason",
    "reference_date",
    "reference_symbol",
    "source",
    "source_interface",
    "source_run_id",
    "schema_version",
    "lineage_raw_checksum",
)

SZ_CODE_CHANGE_FIXES = (
    {
        "canonical_symbol": "001914.SZ",
        "source_symbol": "000043.SZ",
        "mapping_type": "sz_code_change",
        "effective_date": "2019-12-16",
        "valid_start": "2015-01-01",
        "valid_end": "2019-12-13",
        "name": "招商积余",
        "reason": "000043.SZ 中航善达在 2019-12-16 变更为 001914.SZ 招商积余；代码启用日前 stk_limit 需用旧代码查询。",
    },
    {
        "canonical_symbol": "000022.SZ",
        "source_symbol": "001872.SZ",
        "mapping_type": "provider_pre_effective_code_switch",
        "effective_date": "2018-12-26",
        "valid_start": "2018-12-19",
        "valid_end": "2018-12-20",
        "name": "深赤湾A/招商港口",
        "reason": "000022.SZ 变更为 001872.SZ 前的 provider 涨跌停价已按新代码返回。",
    },
)


@dataclass(slots=True)
class CleanupContext:
    layout: LakeLayout
    run_id: str
    start: str
    end: str
    old_prices_limit_run_id: str
    sleep_seconds: float
    dry_run: bool
    network_calls: int = 0
    output_paths: dict[str, list[str]] = field(default_factory=dict)


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _iso_day(value: Any) -> str:
    text = str(value)
    if len(text) >= 10 and text[4] == "-" and text[7] == "-":
        return text[:10]
    return datetime.strptime(text[:8], "%Y%m%d").date().isoformat()


def _compact_day(value: Any) -> str:
    return _iso_day(value).replace("-", "")


def _timestamp(day: Any, time_text: str) -> str:
    return f"{_iso_day(day)}T{time_text}+08:00"


def _hash_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _frame_checksum(frame: pd.DataFrame, dataset: str) -> str:
    payload = f"{dataset}:{len(frame)}:{','.join(frame.columns)}"
    if not frame.empty:
        payload += f":{frame.iloc[0].to_json(default_handler=str)}:{frame.iloc[-1].to_json(default_handler=str)}"
    return _hash_text(payload)


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


def _fetch(pro: Any, method_name: str, ctx: CleanupContext, **params: Any) -> pd.DataFrame:
    method = getattr(pro, method_name)
    frame = method(**params)
    ctx.network_calls += 1
    if ctx.sleep_seconds:
        time.sleep(ctx.sleep_seconds)
    return frame if isinstance(frame, pd.DataFrame) else pd.DataFrame()


def _write_jsonl_raw(
    ctx: CleanupContext,
    *,
    interface: str,
    batch_id: str,
    trade_date: str,
    params: Mapping[str, Any],
    rows: Sequence[Mapping[str, Any]],
) -> str:
    if ctx.dry_run:
        return _hash_text(f"dry-run:{interface}:{batch_id}:{len(rows)}")
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


def _write_parquet(ctx: CleanupContext, dataset: str, frame: pd.DataFrame, name: str) -> Path:
    path = ctx.layout.canonical_dataset_root(dataset, SCHEMA_VERSION) / f"run_id={ctx.run_id}" / name
    ctx.output_paths.setdefault(dataset, []).append(str(path.relative_to(ctx.layout.lake_root)))
    if ctx.dry_run:
        return path
    tmp_path = path.with_name(path.name + ".tmp")
    ensure_parent_dirs_for_write(tmp_path)
    frame.to_parquet(tmp_path, index=False)
    with tmp_path.open("rb") as fh:
        os.fsync(fh.fileno())
    tmp_path.replace(path)
    return path


def _price_run_for_year(ctx: CleanupContext, year: int) -> Path:
    root = ctx.layout.canonical_dataset_root("prices", SCHEMA_VERSION)
    if year == 2026:
        exact = root / "run_id=run-cr014-s11-full-a-2026-ytd-date-batch-143508"
        if exact.exists():
            return exact
    matches = sorted(root.glob(f"run_id=run-cr014-s14-prices-adj-factor-{year}-*"))
    if not matches:
        raise RuntimeError(f"缺少 {year} 年 prices run")
    return matches[-1]


def _price_pairs_for_year(ctx: CleanupContext, year: int) -> pd.DataFrame:
    run_root = _price_run_for_year(ctx, year)
    frames: list[pd.DataFrame] = []
    for path in sorted(run_root.glob("*.parquet")):
        frame = pd.read_parquet(path, columns=["trade_date", "symbol"])
        frame["trade_date"] = frame["trade_date"].astype(str)
        frame["symbol"] = frame["symbol"].astype(str)
        frame = frame[(frame["trade_date"] >= ctx.start) & (frame["trade_date"] <= ctx.end)]
        if not frame.empty:
            frames.append(frame)
    if not frames:
        return pd.DataFrame(columns=["trade_date", "symbol"])
    return pd.concat(frames, ignore_index=True).drop_duplicates(["trade_date", "symbol"])


def _old_prices_limit_for_year(ctx: CleanupContext, year: int) -> pd.DataFrame:
    path = (
        ctx.layout.canonical_dataset_root(DATASET_PRICES_LIMIT, SCHEMA_VERSION)
        / f"run_id={ctx.old_prices_limit_run_id}"
        / f"part-prices-limit-{year}.parquet"
    )
    if not path.exists():
        return pd.DataFrame(columns=CANONICAL_PRICES_LIMIT_COLUMNS)
    frame = pd.read_parquet(path)
    for column in CANONICAL_PRICES_LIMIT_COLUMNS:
        if column not in frame.columns:
            frame[column] = None
    frame["trade_date"] = frame["trade_date"].astype(str)
    frame["symbol"] = frame["symbol"].astype(str)
    return frame[list(CANONICAL_PRICES_LIMIT_COLUMNS)]


def fetch_bse_mapping(pro: Any, ctx: CleanupContext) -> tuple[pd.DataFrame, dict[str, str]]:
    frame = _fetch(pro, "bse_mapping", ctx)
    rows = _clean_records(frame)
    checksum = _write_jsonl_raw(
        ctx,
        interface="bse_mapping.snapshot",
        batch_id="bse-mapping",
        trade_date=ctx.end,
        params={"target_dataset": DATASET_BSE_CODE_MAPPING, "snapshot_date": ctx.end},
        rows=rows,
    )
    normalised: list[dict[str, Any]] = []
    effective_by_symbol: dict[str, str] = {}
    for row in rows:
        old_code = str(row.get("o_code") or "").strip().upper()
        new_code = str(row.get("n_code") or "").strip().upper()
        list_date = _iso_day(row.get("list_date")) if row.get("list_date") else ""
        effective = max(BSE_FIRST_TRADING_DAY, list_date) if list_date else BSE_FIRST_TRADING_DAY
        if old_code:
            effective_by_symbol[old_code] = effective
        if new_code:
            effective_by_symbol[new_code] = effective
        normalised.append(
            {
                "name": str(row.get("name") or ""),
                "old_code": old_code,
                "new_code": new_code,
                "list_date": list_date,
                "effective_bse_start": effective,
                "source": SOURCE_TUSHARE,
                "source_interface": "bse_mapping.snapshot",
                "source_run_id": ctx.run_id,
                "schema_version": SCHEMA_VERSION,
                "lineage_raw_checksum": checksum,
            }
        )
    output = pd.DataFrame(normalised, columns=BSE_CODE_MAPPING_COLUMNS).drop_duplicates(["old_code", "new_code"])
    _write_parquet(ctx, DATASET_BSE_CODE_MAPPING, output, "part-bse-code-mapping.parquet")
    return output, effective_by_symbol


def build_lifecycle_code_change(ctx: CleanupContext, bse_mapping: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    checksum = _frame_checksum(bse_mapping, DATASET_BSE_CODE_MAPPING)
    for item in _clean_records(bse_mapping):
        rows.append(
            {
                "canonical_symbol": item["new_code"],
                "source_symbol": item["old_code"],
                "mapping_type": "bse_old_new_code",
                "effective_date": item["effective_bse_start"],
                "valid_start": "",
                "valid_end": item["effective_bse_start"],
                "name": item["name"],
                "reason": "北交所新旧代码映射；effective_date 用 max(2021-11-15, bse_mapping.list_date)。",
                "source": SOURCE_TUSHARE,
                "source_interface": "bse_mapping.snapshot",
                "source_run_id": ctx.run_id,
                "schema_version": SCHEMA_VERSION,
                "lineage_raw_checksum": checksum,
            }
        )
    for fix in SZ_CODE_CHANGE_FIXES:
        rows.append(
            {
                **fix,
                "source": "curated+tushare",
                "source_interface": "code_change_mapping.curated",
                "source_run_id": ctx.run_id,
                "schema_version": SCHEMA_VERSION,
                "lineage_raw_checksum": _hash_text(json.dumps(fix, ensure_ascii=False, sort_keys=True)),
            }
        )
    frame = pd.DataFrame(rows, columns=LIFECYCLE_CODE_CHANGE_COLUMNS).drop_duplicates(
        ["canonical_symbol", "source_symbol", "mapping_type", "effective_date"]
    )
    _write_parquet(ctx, DATASET_LIFECYCLE_CODE_CHANGE, frame, "part-lifecycle-code-change.parquet")
    return frame


def _missing_pairs(prices: pd.DataFrame, limits: pd.DataFrame) -> pd.DataFrame:
    existing = limits[["trade_date", "symbol"]].drop_duplicates()
    merged = prices.merge(existing.assign(_has_limit=True), on=["trade_date", "symbol"], how="left")
    return merged[merged["_has_limit"].isna()][["trade_date", "symbol"]].drop_duplicates()


def fetch_code_change_limit_fixes(
    pro: Any,
    ctx: CleanupContext,
    old_limits_by_year: Mapping[int, pd.DataFrame],
    price_pairs_by_year: Mapping[int, pd.DataFrame],
) -> pd.DataFrame:
    fix_rows: list[dict[str, Any]] = []
    raw_rows: list[dict[str, Any]] = []
    for fix in SZ_CODE_CHANGE_FIXES:
        canonical_symbol = str(fix["canonical_symbol"])
        source_symbol = str(fix["source_symbol"])
        start_date = str(fix["valid_start"])
        end_date = str(fix["valid_end"])
        frame = _fetch(
            pro,
            "stk_limit",
            ctx,
            ts_code=source_symbol,
            start_date=_compact_day(start_date),
            end_date=_compact_day(end_date),
        )
        provider_rows = _clean_records(frame)
        raw_rows.extend(
            {
                **row,
                "_canonical_symbol": canonical_symbol,
                "_source_symbol": source_symbol,
                "_mapping_type": fix["mapping_type"],
                "_mapping_effective_date": fix["effective_date"],
            }
            for row in provider_rows
        )
        provider = pd.DataFrame(provider_rows)
        if provider.empty:
            continue
        provider["trade_date"] = provider["trade_date"].map(_iso_day)
        provider["source_symbol"] = provider["ts_code"].astype(str).str.upper()
        provider["symbol"] = canonical_symbol
        years = range(int(start_date[:4]), int(end_date[:4]) + 1)
        missing_keys = []
        for year in years:
            prices = price_pairs_by_year.get(year, pd.DataFrame(columns=["trade_date", "symbol"]))
            old_limits = old_limits_by_year.get(year, pd.DataFrame(columns=CANONICAL_PRICES_LIMIT_COLUMNS))
            missing_keys.append(_missing_pairs(prices, old_limits))
        missing = pd.concat(missing_keys, ignore_index=True).drop_duplicates(["trade_date", "symbol"]) if missing_keys else pd.DataFrame(columns=["trade_date", "symbol"])
        missing = missing[missing["symbol"].eq(canonical_symbol)]
        mapped = provider.merge(missing, on=["trade_date", "symbol"], how="inner")
        for row in _clean_records(mapped):
            fix_rows.append(
                {
                    "trade_date": _iso_day(row["trade_date"]),
                    "symbol": canonical_symbol,
                    "source_symbol": source_symbol,
                    "limit_up": row.get("up_limit"),
                    "limit_down": row.get("down_limit"),
                    "mapping_type": fix["mapping_type"],
                    "mapping_effective_date": fix["effective_date"],
                    "reason": fix["reason"],
                    "source": SOURCE_TUSHARE,
                    "source_interface": "prices_limit.code_change_lookup",
                    "source_run_id": ctx.run_id,
                    "schema_version": SCHEMA_VERSION,
                    "lineage_raw_checksum": "",
                }
            )
    checksum = _write_jsonl_raw(
        ctx,
        interface="prices_limit.code_change_lookup",
        batch_id="sz-code-change-prices-limit",
        trade_date=ctx.start,
        params={"target_dataset": DATASET_PRICES_LIMIT, "fix_count": len(SZ_CODE_CHANGE_FIXES)},
        rows=raw_rows,
    )
    for row in fix_rows:
        row["lineage_raw_checksum"] = checksum
    frame = pd.DataFrame(fix_rows, columns=CODE_CHANGE_FIX_COLUMNS).drop_duplicates(["trade_date", "symbol"])
    _write_parquet(ctx, DATASET_PRICES_LIMIT_CODE_CHANGE_FIXES, frame, "part-prices-limit-code-change-fixes.parquet")
    return frame


def write_cleaned_prices_limit(
    ctx: CleanupContext,
    old_limits_by_year: Mapping[int, pd.DataFrame],
    code_change_fixes: pd.DataFrame,
) -> dict[int, pd.DataFrame]:
    cleaned_by_year: dict[int, pd.DataFrame] = {}
    canonical_fix_rows: list[dict[str, Any]] = []
    for row in _clean_records(code_change_fixes):
        canonical_fix_rows.append(
            {
                "trade_date": row["trade_date"],
                "symbol": row["symbol"],
                "limit_up": row["limit_up"],
                "limit_down": row["limit_down"],
                "source": row["source"],
                "source_interface": row["source_interface"],
                "source_run_id": row["source_run_id"],
                "available_at": _timestamp(row["trade_date"], "08:40:00"),
                "available_at_rule": "tushare_stk_limit_08:40_code_change_mapped",
                "schema_version": SCHEMA_VERSION,
                "lineage_raw_checksum": row["lineage_raw_checksum"],
            }
        )
    fixes = pd.DataFrame(canonical_fix_rows, columns=CANONICAL_PRICES_LIMIT_COLUMNS)
    for year in range(int(ctx.start[:4]), int(ctx.end[:4]) + 1):
        old = old_limits_by_year.get(year, pd.DataFrame(columns=CANONICAL_PRICES_LIMIT_COLUMNS))
        parts = [old]
        if not fixes.empty:
            parts.append(fixes[fixes["trade_date"].astype(str).str[:4].eq(str(year))])
        frame = pd.concat(parts, ignore_index=True)
        frame = frame.drop_duplicates(["trade_date", "symbol"], keep="last")
        frame = frame.sort_values(["trade_date", "symbol"]).reset_index(drop=True)
        for column in CANONICAL_PRICES_LIMIT_COLUMNS:
            if column not in frame.columns:
                frame[column] = None
        frame = frame[list(CANONICAL_PRICES_LIMIT_COLUMNS)]
        _write_parquet(ctx, DATASET_PRICES_LIMIT, frame, f"part-prices-limit-{year}.parquet")
        cleaned_by_year[year] = frame
    return cleaned_by_year


def _stock_list_dates(ctx: CleanupContext) -> dict[str, str]:
    root = ctx.layout.canonical_dataset_root("stock_basic", SCHEMA_VERSION)
    frames: list[pd.DataFrame] = []
    for path in sorted(root.glob("run_id=*/*.parquet")):
        try:
            frame = pd.read_parquet(path, columns=["symbol", "list_date"])
        except Exception:
            continue
        frames.append(frame)
    if not frames:
        return {}
    stock = pd.concat(frames, ignore_index=True).dropna(subset=["symbol"]).drop_duplicates(["symbol"], keep="last")
    result: dict[str, str] = {}
    for row in _clean_records(stock):
        symbol = str(row.get("symbol") or "").upper()
        list_date = str(row.get("list_date") or "")
        if symbol and list_date:
            result[symbol] = _iso_day(list_date)
    return result


def build_coverage_exclusions_and_validation(
    ctx: CleanupContext,
    price_pairs_by_year: Mapping[int, pd.DataFrame],
    cleaned_limits_by_year: Mapping[int, pd.DataFrame],
    bse_effective_by_symbol: Mapping[str, str],
) -> tuple[pd.DataFrame, dict[str, Any]]:
    stock_list_dates = _stock_list_dates(ctx)
    exclusion_rows: list[dict[str, Any]] = []
    unresolved_rows: list[dict[str, str]] = []
    raw_missing_total = 0
    price_pair_total = 0
    cleaned_limit_pairs_total = 0

    for year, prices in sorted(price_pairs_by_year.items()):
        limits = cleaned_limits_by_year.get(year, pd.DataFrame(columns=CANONICAL_PRICES_LIMIT_COLUMNS))
        price_pair_total += int(len(prices))
        cleaned_limit_pairs_total += int(len(limits[["trade_date", "symbol"]].drop_duplicates())) if not limits.empty else 0
        missing = _missing_pairs(prices, limits)
        raw_missing_total += int(len(missing))
        for row in _clean_records(missing):
            trade_date = str(row["trade_date"])
            symbol = str(row["symbol"]).upper()
            reason = ""
            reference_date = ""
            reference_symbol = ""
            if symbol.endswith(".BJ"):
                effective = bse_effective_by_symbol.get(symbol, BSE_FIRST_TRADING_DAY)
                if trade_date < effective:
                    reason = "before_bse_effective_start"
                    reference_date = effective
                    reference_symbol = symbol
            elif symbol.startswith("688") and symbol.endswith(".SH"):
                list_date = stock_list_dates.get(symbol)
                if list_date and trade_date == list_date:
                    reason = "star_market_first_trading_day_no_price_limit"
                    reference_date = list_date
                    reference_symbol = symbol
            if reason:
                exclusion_rows.append(
                    {
                        "trade_date": trade_date,
                        "symbol": symbol,
                        "exclusion_reason": reason,
                        "reference_date": reference_date,
                        "reference_symbol": reference_symbol,
                        "source": "derived",
                        "source_interface": "prices_limit.lifecycle_denominator_cleanup",
                        "source_run_id": ctx.run_id,
                        "schema_version": SCHEMA_VERSION,
                        "lineage_raw_checksum": "",
                    }
                )
            else:
                unresolved_rows.append({"trade_date": trade_date, "symbol": symbol})

    exclusions = pd.DataFrame(exclusion_rows, columns=COVERAGE_EXCLUSION_COLUMNS).drop_duplicates(["trade_date", "symbol"])
    checksum = _frame_checksum(exclusions, DATASET_PRICES_LIMIT_COVERAGE_EXCLUSIONS)
    if not exclusions.empty:
        exclusions["lineage_raw_checksum"] = checksum
    _write_parquet(ctx, DATASET_PRICES_LIMIT_COVERAGE_EXCLUSIONS, exclusions, "part-prices-limit-coverage-exclusions.parquet")
    reason_counts = exclusions.groupby("exclusion_reason").size().to_dict() if not exclusions.empty else {}
    adjusted_denominator = int(price_pair_total - len(exclusions))
    validation = {
        "schema_name": "cr018.price_limit_lifecycle_cleanup_validation.v1",
        "run_id": ctx.run_id,
        "start": ctx.start,
        "end": ctx.end,
        "price_pair_total": int(price_pair_total),
        "cleaned_limit_pairs_total": int(cleaned_limit_pairs_total),
        "raw_missing_after_code_change_fixes": int(raw_missing_total),
        "excluded_missing_pairs": int(len(exclusions)),
        "adjusted_denominator": adjusted_denominator,
        "unresolved_missing_pairs": int(len(unresolved_rows)),
        "coverage_ratio_after_cleanup": 1.0 if adjusted_denominator else 0.0,
        "exclusion_reason_counts": {str(key): int(value) for key, value in reason_counts.items()},
        "unresolved_missing_sample": unresolved_rows[:50],
        "status": "pass" if not unresolved_rows else "fail",
        "qmt_operation_count": 0,
        "current_pointer_publish_count": 0,
    }
    return exclusions, validation


def _catalog_upsert(
    ctx: CleanupContext,
    dataset: str,
    *,
    rows: int,
    status: str = QUALITY_STATUS_PASS,
    canonical_path: str | None = None,
    coverage_denominator: int | None = None,
    coverage_ratio: float | None = None,
    notes: Sequence[Mapping[str, Any] | str] = (),
) -> None:
    if ctx.dry_run:
        return
    paths = ctx.output_paths.get(dataset, [])
    if canonical_path is None:
        if paths:
            common_root = ctx.layout.canonical_dataset_root(dataset, SCHEMA_VERSION) / f"run_id={ctx.run_id}"
            canonical_path = str(common_root.relative_to(ctx.layout.lake_root))
        else:
            canonical_path = ""
    entry = CatalogEntry(
        dataset=dataset,
        schema_version=SCHEMA_VERSION,
        start_date=ctx.start,
        end_date=ctx.end,
        coverage={
            "run_id": ctx.run_id,
            "dataset": dataset,
            "actual_rows": rows,
            "status": status,
            "notes": list(notes),
        },
        quality_status=status,
        dataset_status="available" if status == QUALITY_STATUS_PASS else "fail",
        latest_manifest_run_id=ctx.run_id,
        source=SOURCE_TUSHARE if dataset != DATASET_PRICES_LIMIT_COVERAGE_EXCLUSIONS else "derived",
        source_interface="cr018_price_limit_lifecycle_cleanup",
        lineage_raw_checksum=_hash_text(json.dumps(paths, ensure_ascii=False, sort_keys=True)),
        canonical_path=canonical_path,
        generated_at=_iso_now(),
        updated_at=_iso_now(),
        published=False,
        readiness_status=READINESS_STATUS_AVAILABLE if status == QUALITY_STATUS_PASS else "quality_failed",
        coverage_denominator=coverage_denominator if coverage_denominator is not None else rows,
        coverage_ratio=coverage_ratio if coverage_ratio is not None else (1.0 if rows else 0.0),
        coverage_start=ctx.start,
        coverage_end=ctx.end,
        known_limitations=list(notes),
    )
    CatalogStore(ctx.layout).upsert(entry)


def write_quality_summary(
    ctx: CleanupContext,
    *,
    validation: Mapping[str, Any],
    row_counts: Mapping[str, int],
    code_change_fixes: pd.DataFrame,
    exclusions: pd.DataFrame,
) -> Path:
    payload = {
        "run_id": ctx.run_id,
        "start": ctx.start,
        "end": ctx.end,
        "generated_at": _iso_now(),
        "network_calls": ctx.network_calls,
        "dry_run": ctx.dry_run,
        "qmt_operation_count": 0,
        "current_pointer_publish_count": 0,
        "row_counts": {str(key): int(value) for key, value in row_counts.items()},
        "code_change_fix_rows": int(len(code_change_fixes)),
        "coverage_exclusion_rows": int(len(exclusions)),
        "validation": dict(validation),
        "output_paths": ctx.output_paths,
    }
    summary_path = ctx.layout.quality_root / ctx.run_id / "cr018_price_limit_lifecycle_cleanup_summary.json"
    validation_path = ctx.layout.quality_root / ctx.run_id / "cr018_price_limit_lifecycle_cleanup_validation.json"
    md_path = ctx.layout.quality_root / ctx.run_id / "cr018_price_limit_lifecycle_cleanup_summary.md"
    if not ctx.dry_run:
        ensure_parent_dirs_for_write(summary_path)
        summary_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        validation_path.write_text(json.dumps(validation, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        lines = [
            "# CR018 Price Limit Lifecycle Cleanup Summary",
            "",
            f"- run_id: `{ctx.run_id}`",
            f"- range: `{ctx.start}`..`{ctx.end}`",
            f"- network_calls: `{ctx.network_calls}`",
            "- qmt_operation_count: `0`",
            "- current_pointer_publish_count: `0`",
            f"- status: `{validation.get('status')}`",
            f"- unresolved_missing_pairs: `{validation.get('unresolved_missing_pairs')}`",
            "",
            "| item | count |",
            "|---|---:|",
        ]
        for key, value in row_counts.items():
            lines.append(f"| `{key}` | {int(value)} |")
        lines.extend(
            [
                f"| `code_change_fix_rows` | {len(code_change_fixes)} |",
                f"| `coverage_exclusion_rows` | {len(exclusions)} |",
                "",
                "## Exclusion Reasons",
                "",
                "| reason | count |",
                "|---|---:|",
            ]
        )
        for reason, count in sorted(dict(validation.get("exclusion_reason_counts") or {}).items()):
            lines.append(f"| `{reason}` | {int(count)} |")
        md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return summary_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Clean price-limit lifecycle and symbol-change data")
    parser.add_argument("--lake-root", default=os.environ.get("MARKET_DATA_LAKE_ROOT", ""))
    parser.add_argument("--start", default="2015-01-01")
    parser.add_argument("--end", default="2026-05-28")
    parser.add_argument("--run-id", default="")
    parser.add_argument("--old-prices-limit-run-id", default=OLD_PRICES_LIMIT_RUN_ID)
    parser.add_argument("--sleep-seconds", type=float, default=0.05)
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.lake_root:
        raise RuntimeError("缺少 --lake-root 或 MARKET_DATA_LAKE_ROOT")
    token = os.environ.get("TUSHARE_TOKEN")
    if not token:
        raise RuntimeError("缺少 TUSHARE_TOKEN")
    run_id = args.run_id or (
        f"run-cr018-price-limit-lifecycle-cleanup-"
        f"{_compact_day(args.start)}-{_compact_day(args.end)}-{datetime.now().strftime('%Y%m%d')}"
    )
    ctx = CleanupContext(
        layout=LakeLayout(Path(args.lake_root)),
        run_id=run_id,
        start=_iso_day(args.start),
        end=_iso_day(args.end),
        old_prices_limit_run_id=str(args.old_prices_limit_run_id),
        sleep_seconds=float(args.sleep_seconds),
        dry_run=bool(args.dry_run),
    )
    print(f"[start] run_id={ctx.run_id} range={ctx.start}..{ctx.end}", flush=True)
    pro = ts.pro_api(token)
    bse_mapping, bse_effective = fetch_bse_mapping(pro, ctx)
    lifecycle = build_lifecycle_code_change(ctx, bse_mapping)

    price_pairs_by_year: dict[int, pd.DataFrame] = {}
    old_limits_by_year: dict[int, pd.DataFrame] = {}
    for year in range(int(ctx.start[:4]), int(ctx.end[:4]) + 1):
        print(f"[load] {year}", flush=True)
        price_pairs_by_year[year] = _price_pairs_for_year(ctx, year)
        old_limits_by_year[year] = _old_prices_limit_for_year(ctx, year)

    code_change_fixes = fetch_code_change_limit_fixes(pro, ctx, old_limits_by_year, price_pairs_by_year)
    cleaned_limits_by_year = write_cleaned_prices_limit(ctx, old_limits_by_year, code_change_fixes)
    exclusions, validation = build_coverage_exclusions_and_validation(
        ctx,
        price_pairs_by_year,
        cleaned_limits_by_year,
        bse_effective,
    )
    row_counts = {
        DATASET_BSE_CODE_MAPPING: len(bse_mapping),
        DATASET_LIFECYCLE_CODE_CHANGE: len(lifecycle),
        DATASET_PRICES_LIMIT_CODE_CHANGE_FIXES: len(code_change_fixes),
        DATASET_PRICES_LIMIT_COVERAGE_EXCLUSIONS: len(exclusions),
        DATASET_PRICES_LIMIT: sum(len(frame) for frame in cleaned_limits_by_year.values()),
    }
    status = QUALITY_STATUS_PASS if validation.get("status") == "pass" else "fail"
    _catalog_upsert(ctx, DATASET_BSE_CODE_MAPPING, rows=len(bse_mapping))
    _catalog_upsert(ctx, DATASET_LIFECYCLE_CODE_CHANGE, rows=len(lifecycle))
    _catalog_upsert(ctx, DATASET_PRICES_LIMIT_CODE_CHANGE_FIXES, rows=len(code_change_fixes))
    _catalog_upsert(ctx, DATASET_PRICES_LIMIT_COVERAGE_EXCLUSIONS, rows=len(exclusions))
    _catalog_upsert(
        ctx,
        DATASET_PRICES_LIMIT,
        rows=row_counts[DATASET_PRICES_LIMIT],
        status=status,
        coverage_denominator=int(validation["adjusted_denominator"]),
        coverage_ratio=float(validation["coverage_ratio_after_cleanup"]) if status == QUALITY_STATUS_PASS else 0.0,
        notes=[
            {"code": "before_bse_effective_start_excluded_from_denominator"},
            {"code": "star_market_first_trading_day_no_price_limit_excluded"},
            {"code": "sz_code_change_prices_limit_mapped"},
            {"code": "candidate_unpublished"},
        ],
    )
    summary_path = write_quality_summary(
        ctx,
        validation=validation,
        row_counts=row_counts,
        code_change_fixes=code_change_fixes,
        exclusions=exclusions,
    )
    print(json.dumps({"ok": validation.get("status") == "pass", "summary": str(summary_path), **validation}, ensure_ascii=False, sort_keys=True), flush=True)
    return 0 if validation.get("status") == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
