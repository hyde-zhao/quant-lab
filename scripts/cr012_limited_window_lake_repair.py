"""CR-012 limited-window current truth 修复工具。

该脚本只服务于 `2025-02-11..2026-02-18` readiness 复验：

- 先从现有 current truth 计算缺口；
- 可选联网抓取 Tushare 缺失日频数据和退市 stock_basic；
- 生成新的 merged canonical run；
- 更新 catalog current truth 指针。
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from experiments.run_data_lake_readiness_audit import (
    AuditConfig,
    DATASET_ADJ_FACTOR,
    DATASET_INDEX_MEMBERS,
    DATASET_PRICES,
    DATASET_PRICES_LIMIT,
    DATASET_STOCK_BASIC,
    DATASET_TRADE_CALENDAR,
    DATASET_TRADE_STATUS,
    _coverage_context,
    _pairs_from_frame,
    _probe_all,
    _read_catalog_entries,
)
from engine.research_paths import research_report_path
from market_data.catalog import CatalogEntry, CatalogStore
from market_data.connectors.protocol import AdapterConfig, ConnectorRequest
from market_data.connectors.tushare import TushareAdapter
from market_data.contracts import (
    DATASET_SCHEMA_REGISTRY,
    INTERFACE_PRICES_ADJ_FACTOR,
    INTERFACE_PRICES_DAILY,
    INTERFACE_PRICES_LIMIT_DAILY,
    INTERFACE_STOCK_BASIC_SNAPSHOT,
    INTERFACE_TRADE_STATUS_DAILY,
    SCHEMA_VERSION,
    SOURCE_TUSHARE,
)
from market_data.lake_layout import LakeLayout, ensure_parent_dirs_for_write
from market_data.normalization import normalize_run
from market_data.runtime import RuntimeContext, RuntimePolicy, execute_batches


DEFAULT_LAKE_ROOT = Path("/mnt/ugreen-data-lake")
DEFAULT_START_DATE = "2025-02-11"
DEFAULT_END_DATE = "2026-02-18"
DEFAULT_REPORT_DIR = research_report_path("data_lake_readiness_limited_2025_2026")
JQDATA_WEIGHTS_V2 = (
    "canonical/index_weights/1.0/"
    "run_id=cr010-prod-window-20250211-20260218-index-weights-smoke-v2/"
    "part-jqdata-index-weights-20250211.parquet"
)


def _now_text() -> str:
    return datetime.now(timezone.utc).isoformat()


def _run_token() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _clean_symbol(symbol: str) -> str:
    return symbol.replace(".", "")


def _read_parquet_path(path: Path) -> pd.DataFrame:
    if path.is_dir():
        files = sorted(path.rglob("*.parquet"))
        if not files:
            return pd.DataFrame()
        return pd.concat([pd.read_parquet(item) for item in files], ignore_index=True)
    if path.exists():
        return pd.read_parquet(path)
    return pd.DataFrame()


def _entry_path(lake_root: Path, entry: CatalogEntry) -> Path:
    if not entry.canonical_path:
        return Path("")
    path = Path(entry.canonical_path)
    return path if path.is_absolute() else lake_root / path


def _current_frame(lake_root: Path, entries: Mapping[str, CatalogEntry], dataset: str) -> pd.DataFrame:
    return _read_parquet_path(_entry_path(lake_root, entries[dataset]))


def _run_frame(layout: LakeLayout, dataset: str, run_id: str) -> pd.DataFrame:
    root = layout.canonical_dataset_root(dataset) / f"run_id={run_id}"
    return _read_parquet_path(root)


def _date_text(value: object) -> str:
    text = str(value).strip()
    if len(text) >= 10 and text[4] == "-" and text[7] == "-":
        return text[:10]
    if len(text) == 8 and text.isdigit():
        return f"{text[:4]}-{text[4:6]}-{text[6:8]}"
    return text


def _align_columns(dataset: str, frame: pd.DataFrame) -> pd.DataFrame:
    columns = list(DATASET_SCHEMA_REGISTRY[dataset]["columns"])
    output = frame.copy()
    for column in columns:
        if column not in output.columns:
            output[column] = None
    return output[columns]


def _dedupe(frame: pd.DataFrame, keys: Sequence[str]) -> pd.DataFrame:
    if frame.empty:
        return frame
    output = frame.copy()
    for key in keys:
        if key in output.columns:
            output[key] = output[key].map(_date_text) if key.endswith("date") else output[key].astype(str)
    return output.drop_duplicates(list(keys), keep="last").reset_index(drop=True)


def _sort_frame(dataset: str, frame: pd.DataFrame) -> pd.DataFrame:
    sort_keys = list(DATASET_SCHEMA_REGISTRY[dataset]["key_columns"])
    existing = [key for key in sort_keys if key in frame.columns]
    if existing:
        return frame.sort_values(existing).reset_index(drop=True)
    return frame.reset_index(drop=True)


def _write_merged_dataset(
    lake_root: Path,
    dataset: str,
    run_id: str,
    frame: pd.DataFrame,
) -> Path:
    layout = LakeLayout(lake_root)
    output = _align_columns(dataset, _sort_frame(dataset, frame))
    target = layout.canonical_dataset_root(dataset) / f"run_id={run_id}" / f"part-cr012-{dataset}.parquet"
    ensure_parent_dirs_for_write(target)
    output.to_parquet(target, index=False)
    return target


def _publish_entry(
    *,
    lake_root: Path,
    store: CatalogStore,
    current: CatalogEntry,
    dataset: str,
    run_id: str,
    canonical_path: Path,
    source: str,
    source_interface: str,
    available_at_rule: str,
) -> None:
    now = _now_text()
    store.upsert(
        replace(
            current,
            dataset=dataset,
            schema_version=SCHEMA_VERSION,
            start_date=DEFAULT_START_DATE,
            end_date=DEFAULT_END_DATE,
            latest_manifest_run_id=run_id,
            source=source,
            source_interface=source_interface,
            lineage_raw_checksum=f"cr012_repair:{run_id}:{dataset}",
            canonical_path=str(canonical_path.relative_to(lake_root)),
            generated_at=now,
            updated_at=now,
            published=True,
            published_at=now,
            quality_status="pass",
            dataset_status="available",
            readiness_status=current.readiness_status or "available",
            available_at_rule=available_at_rule,
        )
    )


def _gap_symbols(
    probes: Mapping[str, Any],
    membership_pairs: set[tuple[str, str]],
    dataset: str,
) -> dict[str, list[str]]:
    frame = probes[dataset].frame
    observed = _pairs_from_frame(frame, "trade_date", "symbol")
    missing = membership_pairs - observed
    output: dict[str, list[str]] = {}
    for trade_date, symbol in sorted(missing):
        output.setdefault(symbol, []).append(trade_date)
    return output


def build_plan(lake_root: Path, start_date: str, end_date: str) -> dict[str, Any]:
    config = AuditConfig(
        lake_root=lake_root,
        start_date=start_date,
        end_date=end_date,
        max_workers=1,
    )
    entries, catalog_error = _read_catalog_entries(lake_root)
    if catalog_error:
        raise RuntimeError(catalog_error)
    probes = _probe_all(config, entries)
    context = _coverage_context(probes, config)
    if context.membership_pairs is None or context.open_dates is None:
        raise RuntimeError("PIT membership 或 trade_calendar denominator 不可用")

    member_dates = {date for date, _ in context.membership_pairs}
    stock_frame = probes[DATASET_STOCK_BASIC].frame
    stock_symbols = set(stock_frame["symbol"].astype(str)) if stock_frame is not None and "symbol" in stock_frame else set()
    stock_missing_symbols = sorted((context.membership_symbols or set()) - stock_symbols)

    adj_missing = _gap_symbols(probes, context.membership_pairs, DATASET_ADJ_FACTOR)
    price_missing = _gap_symbols(probes, context.membership_pairs, DATASET_PRICES)
    trade_status_missing = _gap_symbols(probes, context.membership_pairs, DATASET_TRADE_STATUS)
    prices_limit_missing = _gap_symbols(probes, context.membership_pairs, DATASET_PRICES_LIMIT)
    market_backfill_symbols = sorted(set(adj_missing) - set(stock_missing_symbols))
    w3_backfill_symbols = sorted(set(trade_status_missing) | set(prices_limit_missing) | set(price_missing))

    return {
        "lake_root": str(lake_root),
        "start_date": start_date,
        "end_date": end_date,
        "open_trade_dates": len(context.open_dates),
        "membership_pairs": len(context.membership_pairs),
        "missing_membership_dates": sorted(context.open_dates - member_dates),
        "stock_basic_missing_symbols": stock_missing_symbols,
        "price_missing_symbols": {symbol: [dates[0], dates[-1], len(dates)] for symbol, dates in sorted(price_missing.items())},
        "adj_factor_missing_symbols": {symbol: [dates[0], dates[-1], len(dates)] for symbol, dates in sorted(adj_missing.items())},
        "trade_status_missing_symbols": {
            symbol: [dates[0], dates[-1], len(dates)] for symbol, dates in sorted(trade_status_missing.items())
        },
        "prices_limit_missing_symbols": {
            symbol: [dates[0], dates[-1], len(dates)] for symbol, dates in sorted(prices_limit_missing.items())
        },
        "market_backfill_symbols": market_backfill_symbols,
        "market_backfill_symbol_count": len(market_backfill_symbols),
        "w3_backfill_symbols": w3_backfill_symbols,
        "w3_backfill_symbol_count": len(w3_backfill_symbols),
        "jqdata_index_weights_patch_path": JQDATA_WEIGHTS_V2,
        "repair_actions": [
            "derive index_members 2025-02-11 as-of snapshot from existing JQData index_weights v2",
            "rewrite trade_calendar available_at to calendar_known date 00:00",
            "rewrite existing Tushare adj_factor derived available_at to trade_date 16:00",
            "fetch Tushare prices.daily and prices.adj_factor for market_backfill_symbols",
            "fetch Tushare trade_status.daily and prices_limit.daily for W3 missing symbols",
            "fetch Tushare stock_basic list_status=D with lifecycle fields and merge rows",
            "publish merged canonical runs and update catalog current truth",
        ],
    }


def write_plan(plan: Mapping[str, Any], report_dir: Path) -> None:
    report_dir.mkdir(parents=True, exist_ok=True)
    (report_dir / "cr012_repair_plan.json").write_text(
        json.dumps(plan, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    lines = [
        "# CR-012 Limited Window Lake Repair Plan",
        "",
        f"- window: `{plan['start_date']}..{plan['end_date']}`",
        f"- open_trade_dates: `{plan['open_trade_dates']}`",
        f"- membership_pairs_before_repair: `{plan['membership_pairs']}`",
        f"- missing_membership_dates: `{len(plan['missing_membership_dates'])}`",
        f"- stock_basic_missing_symbols: `{','.join(plan['stock_basic_missing_symbols']) or 'none'}`",
        f"- market_backfill_symbol_count: `{plan['market_backfill_symbol_count']}`",
        f"- market_backfill_symbols: `{','.join(plan['market_backfill_symbols']) or 'none'}`",
        f"- w3_backfill_symbol_count: `{plan['w3_backfill_symbol_count']}`",
        f"- w3_backfill_symbols: `{','.join(plan['w3_backfill_symbols']) or 'none'}`",
        "",
        "## Actions",
        "",
    ]
    lines.extend(f"- {item}" for item in plan["repair_actions"])
    lines.append("")
    (report_dir / "cr012_repair_plan.md").write_text("\n".join(lines), encoding="utf-8")


def _tushare_requests(
    run_id: str,
    market_symbols: Sequence[str],
    w3_symbols: Sequence[str],
) -> list[ConnectorRequest]:
    requests: list[ConnectorRequest] = []
    for symbol in market_symbols:
        clean = _clean_symbol(symbol)
        common = {
            "symbol": symbol,
            "start_date": DEFAULT_START_DATE,
            "end_date": DEFAULT_END_DATE,
            "adjustment_policy": "qfq",
            "explicit_real_execution": True,
            "offline": False,
        }
        requests.append(
            ConnectorRequest(
                SOURCE_TUSHARE,
                INTERFACE_PRICES_DAILY,
                {**common, "target_dataset": DATASET_PRICES},
                run_id,
                f"daily-{clean}",
            )
        )
        requests.append(
            ConnectorRequest(
                SOURCE_TUSHARE,
                INTERFACE_PRICES_ADJ_FACTOR,
                {**common, "target_dataset": DATASET_ADJ_FACTOR},
                run_id,
                f"adj-{clean}",
            )
        )
    if w3_symbols:
        w3_common = {
            "symbols": list(w3_symbols),
            "start_date": DEFAULT_START_DATE,
            "end_date": DEFAULT_END_DATE,
            "explicit_real_execution": True,
            "offline": False,
        }
        requests.append(
            ConnectorRequest(
                SOURCE_TUSHARE,
                INTERFACE_TRADE_STATUS_DAILY,
                {**w3_common, "target_dataset": DATASET_TRADE_STATUS},
                run_id,
                "trade-status-w3-missing",
            )
        )
        requests.append(
            ConnectorRequest(
                SOURCE_TUSHARE,
                INTERFACE_PRICES_LIMIT_DAILY,
                {**w3_common, "target_dataset": DATASET_PRICES_LIMIT},
                run_id,
                "prices-limit-w3-missing",
            )
        )
    requests.append(
        ConnectorRequest(
            SOURCE_TUSHARE,
            INTERFACE_STOCK_BASIC_SNAPSHOT,
            {
                "target_dataset": DATASET_STOCK_BASIC,
                "start_date": DEFAULT_START_DATE,
                "end_date": DEFAULT_END_DATE,
                "snapshot_date": DEFAULT_END_DATE,
                "exchange": "",
                "list_status": "D",
                "fields": "ts_code,symbol,name,area,industry,market,list_date,delist_date,list_status",
                "explicit_real_execution": True,
                "offline": False,
            },
            run_id,
            "stock-basic-delisted",
        )
    )
    return requests


def fetch_tushare_repair_data(
    lake_root: Path,
    run_id: str,
    market_symbols: Sequence[str],
    w3_symbols: Sequence[str],
    *,
    throttle_seconds: float,
) -> dict[str, Any]:
    if not os.environ.get("TUSHARE_TOKEN"):
        raise RuntimeError("missing credential env var: TUSHARE_TOKEN")
    requests = _tushare_requests(run_id, market_symbols, w3_symbols)
    adapter = TushareAdapter(
        AdapterConfig(
            source=SOURCE_TUSHARE,
            enabled=True,
            allow_interfaces=(
                INTERFACE_PRICES_DAILY,
                INTERFACE_PRICES_ADJ_FACTOR,
                INTERFACE_STOCK_BASIC_SNAPSHOT,
                INTERFACE_TRADE_STATUS_DAILY,
                INTERFACE_PRICES_LIMIT_DAILY,
            ),
            credential_env_vars=("TUSHARE_TOKEN",),
        )
    )
    results = execute_batches(
        requests,
        adapter,
        LakeLayout(lake_root),
        RuntimePolicy(max_retries=1, throttle_seconds=throttle_seconds),
        context=RuntimeContext(run_id),
    )
    failures = [item for item in results if item.status not in {"success", "skipped"}]
    if failures:
        payload = [
            {"batch_id": item.batch_id, "status": item.status, "error_type": item.error_type}
            for item in failures
        ]
        raise RuntimeError(f"Tushare repair fetch failed: {payload}")
    return {
        "network_calls": len([item for item in results if item.status == "success"]),
        "skipped": len([item for item in results if item.status == "skipped"]),
        "batches": len(results),
    }


def normalize_repair_run(lake_root: Path, fetch_run_id: str) -> dict[str, Any]:
    layout = LakeLayout(lake_root)
    output: dict[str, Any] = {}
    for dataset in (
        DATASET_ADJ_FACTOR,
        DATASET_PRICES,
        DATASET_STOCK_BASIC,
        DATASET_TRADE_STATUS,
        DATASET_PRICES_LIMIT,
    ):
        result = normalize_run(layout.manifest_path(), lake_root, dataset=dataset, run_id=fetch_run_id)
        output[dataset] = {
            "row_count": result.row_count,
            "canonical_paths": [str(path.relative_to(lake_root)) for path in result.canonical_paths],
        }
    return output


def _fix_adj_factor_available_at(frame: pd.DataFrame) -> pd.DataFrame:
    output = frame.copy()
    if output.empty:
        return output
    mask = (
        output.get("source", pd.Series("", index=output.index)).astype(str).eq(SOURCE_TUSHARE)
        & output.get("source_interface", pd.Series("", index=output.index)).astype(str).eq(INTERFACE_PRICES_ADJ_FACTOR)
        & output.get("available_at_rule", pd.Series("", index=output.index)).astype(str).eq("daily_close_fact")
    )
    output.loc[mask, "trade_date"] = output.loc[mask, "trade_date"].map(_date_text)
    output.loc[mask, "available_at"] = output.loc[mask, "trade_date"].map(lambda day: f"{day}T16:00:00+08:00")
    return output


def _fix_trade_calendar_available_at(frame: pd.DataFrame) -> pd.DataFrame:
    output = frame.copy()
    if output.empty:
        return output
    output["trade_date"] = output["trade_date"].map(_date_text)
    output["available_at"] = output["trade_date"].map(lambda day: f"{day}T00:00:00+08:00")
    output["available_at_rule"] = "calendar_known"
    return output


def _members_from_jqdata_weights(lake_root: Path) -> pd.DataFrame:
    path = lake_root / JQDATA_WEIGHTS_V2
    if not path.exists():
        raise RuntimeError(f"missing JQData weights patch file: {path}")
    weights = pd.read_parquet(path)
    rows = pd.DataFrame(
        {
            "trade_date": "2025-02-11",
            "index_code": weights["index_code"].astype(str).str.upper(),
            "con_code": weights["con_code"].astype(str).str.upper(),
            "in_date": weights["effective_date"].map(_date_text),
            "out_date": None,
            "is_member": True,
            "effective_date": weights["effective_date"].map(_date_text),
            "available_date": weights["available_date"].map(_date_text),
            "available_at": weights["available_at"].astype(str),
            "available_at_rule": weights["available_at_rule"].astype(str),
            "is_pit_universe": True,
            "pit_status": "pit_available",
            "readiness_status": "available",
            "source": "jqdata",
            "source_interface": "index_members.snapshot",
            "source_run_id": weights["source_run_id"].astype(str),
            "schema_version": SCHEMA_VERSION,
            "lineage_raw_checksum": weights["lineage_raw_checksum"].astype(str),
            "derived_from": "index_weight",
        }
    )
    return rows


def apply_repair(
    lake_root: Path,
    plan: Mapping[str, Any],
    *,
    fetch_run_id: str,
    merged_run_id: str,
    fetch_tushare: bool,
    throttle_seconds: float,
) -> dict[str, Any]:
    entries, catalog_error = _read_catalog_entries(lake_root)
    if catalog_error:
        raise RuntimeError(catalog_error)
    layout = LakeLayout(lake_root)
    fetch_summary: dict[str, Any] = {"network_calls": 0, "skipped": 0, "batches": 0}
    normalize_summary: dict[str, Any] = {}
    if fetch_tushare:
        fetch_summary = fetch_tushare_repair_data(
            lake_root,
            fetch_run_id,
            plan["market_backfill_symbols"],
            plan["w3_backfill_symbols"],
            throttle_seconds=throttle_seconds,
        )
        normalize_summary = normalize_repair_run(lake_root, fetch_run_id)

    price_patch = _run_frame(layout, DATASET_PRICES, fetch_run_id)
    adj_patch = _run_frame(layout, DATASET_ADJ_FACTOR, fetch_run_id)
    stock_patch = _run_frame(layout, DATASET_STOCK_BASIC, fetch_run_id)
    trade_status_patch = _run_frame(layout, DATASET_TRADE_STATUS, fetch_run_id)
    prices_limit_patch = _run_frame(layout, DATASET_PRICES_LIMIT, fetch_run_id)

    prices = _dedupe(
        pd.concat([_current_frame(lake_root, entries, DATASET_PRICES), price_patch], ignore_index=True),
        ("trade_date", "symbol"),
    )
    adj_factor = _dedupe(
        pd.concat([_current_frame(lake_root, entries, DATASET_ADJ_FACTOR), adj_patch], ignore_index=True),
        ("trade_date", "symbol"),
    )
    adj_factor = _fix_adj_factor_available_at(adj_factor)
    trade_calendar = _fix_trade_calendar_available_at(_current_frame(lake_root, entries, DATASET_TRADE_CALENDAR))
    index_members = _dedupe(
        pd.concat(
            [
                _current_frame(lake_root, entries, DATASET_INDEX_MEMBERS),
                _members_from_jqdata_weights(lake_root),
            ],
            ignore_index=True,
        ),
        ("trade_date", "index_code", "con_code"),
    )
    stock_basic = _dedupe(
        pd.concat([_current_frame(lake_root, entries, DATASET_STOCK_BASIC), stock_patch], ignore_index=True),
        ("symbol",),
    )
    trade_status = _dedupe(
        pd.concat([_current_frame(lake_root, entries, DATASET_TRADE_STATUS), trade_status_patch], ignore_index=True),
        ("trade_date", "symbol"),
    )
    prices_limit = _dedupe(
        pd.concat([_current_frame(lake_root, entries, DATASET_PRICES_LIMIT), prices_limit_patch], ignore_index=True),
        ("trade_date", "symbol"),
    )

    outputs: dict[str, Path] = {}
    for dataset, frame in (
        (DATASET_PRICES, prices),
        (DATASET_ADJ_FACTOR, adj_factor),
        (DATASET_TRADE_CALENDAR, trade_calendar),
        (DATASET_INDEX_MEMBERS, index_members),
        (DATASET_STOCK_BASIC, stock_basic),
        (DATASET_TRADE_STATUS, trade_status),
        (DATASET_PRICES_LIMIT, prices_limit),
    ):
        outputs[dataset] = _write_merged_dataset(lake_root, dataset, merged_run_id, frame)

    store = CatalogStore(layout)
    _publish_entry(
        lake_root=lake_root,
        store=store,
        current=entries[DATASET_PRICES],
        dataset=DATASET_PRICES,
        run_id=merged_run_id,
        canonical_path=outputs[DATASET_PRICES],
        source=SOURCE_TUSHARE,
        source_interface="prices.daily",
        available_at_rule="daily_close_fact",
    )
    _publish_entry(
        lake_root=lake_root,
        store=store,
        current=entries[DATASET_ADJ_FACTOR],
        dataset=DATASET_ADJ_FACTOR,
        run_id=merged_run_id,
        canonical_path=outputs[DATASET_ADJ_FACTOR],
        source=SOURCE_TUSHARE,
        source_interface="prices.adj_factor",
        available_at_rule="daily_close_fact",
    )
    _publish_entry(
        lake_root=lake_root,
        store=store,
        current=entries[DATASET_TRADE_CALENDAR],
        dataset=DATASET_TRADE_CALENDAR,
        run_id=merged_run_id,
        canonical_path=outputs[DATASET_TRADE_CALENDAR],
        source=SOURCE_TUSHARE,
        source_interface="trade_calendar.daily",
        available_at_rule="calendar_known",
    )
    _publish_entry(
        lake_root=lake_root,
        store=store,
        current=entries[DATASET_INDEX_MEMBERS],
        dataset=DATASET_INDEX_MEMBERS,
        run_id=merged_run_id,
        canonical_path=outputs[DATASET_INDEX_MEMBERS],
        source="mixed",
        source_interface="index_members.snapshot",
        available_at_rule="tushare_index_weight_effective_date_16:00;jqdata_daily_close_fact",
    )
    _publish_entry(
        lake_root=lake_root,
        store=store,
        current=entries[DATASET_STOCK_BASIC],
        dataset=DATASET_STOCK_BASIC,
        run_id=merged_run_id,
        canonical_path=outputs[DATASET_STOCK_BASIC],
        source=SOURCE_TUSHARE,
        source_interface="stock_basic.snapshot",
        available_at_rule="tushare_stock_basic_list_date",
    )
    _publish_entry(
        lake_root=lake_root,
        store=store,
        current=entries[DATASET_TRADE_STATUS],
        dataset=DATASET_TRADE_STATUS,
        run_id=merged_run_id,
        canonical_path=outputs[DATASET_TRADE_STATUS],
        source=SOURCE_TUSHARE,
        source_interface="trade_status.daily",
        available_at_rule="tushare_suspend_d_09:30_stock_st_09:20_daily",
    )
    _publish_entry(
        lake_root=lake_root,
        store=store,
        current=entries[DATASET_PRICES_LIMIT],
        dataset=DATASET_PRICES_LIMIT,
        run_id=merged_run_id,
        canonical_path=outputs[DATASET_PRICES_LIMIT],
        source=SOURCE_TUSHARE,
        source_interface="prices_limit.daily",
        available_at_rule="tushare_stk_limit_08:40",
    )

    return {
        "fetch_run_id": fetch_run_id,
        "merged_run_id": merged_run_id,
        "fetch_summary": fetch_summary,
        "normalize_summary": normalize_summary,
        "canonical_outputs": {dataset: str(path.relative_to(lake_root)) for dataset, path in outputs.items()},
        "catalog_updates": sorted(outputs),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lake-root", type=Path, default=DEFAULT_LAKE_ROOT)
    parser.add_argument("--start-date", default=DEFAULT_START_DATE)
    parser.add_argument("--end-date", default=DEFAULT_END_DATE)
    parser.add_argument("--report-dir", type=Path, default=DEFAULT_REPORT_DIR)
    parser.add_argument("--fetch-run-id")
    parser.add_argument("--merged-run-id")
    parser.add_argument("--fetch-tushare", action="store_true")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--throttle-seconds", type=float, default=0.12)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    lake_root = args.lake_root
    token = _run_token()
    fetch_run_id = args.fetch_run_id or f"cr012-limited-window-fetch-{token}"
    merged_run_id = args.merged_run_id or f"cr012-limited-window-merged-{token}"

    plan = build_plan(lake_root, args.start_date, args.end_date)
    write_plan(plan, args.report_dir)
    result: dict[str, Any] = {
        "ok": True,
        "mode": "plan" if not args.apply else "apply",
        "plan_path": str(args.report_dir / "cr012_repair_plan.md"),
        "plan": plan,
    }
    if args.apply:
        result["repair"] = apply_repair(
            lake_root,
            plan,
            fetch_run_id=fetch_run_id,
            merged_run_id=merged_run_id,
            fetch_tushare=args.fetch_tushare,
            throttle_seconds=args.throttle_seconds,
        )
        (args.report_dir / "cr012_repair_result.json").write_text(
            json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
