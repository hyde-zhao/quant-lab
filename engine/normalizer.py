"""raw JSONL 到标准化 parquet 的派生逻辑。

本模块只消费本地 raw cache 与 manifest，不导入数据源 adapter，不触发联网。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import json
import os
from typing import Any, Iterable

import pandas as pd

from engine.contracts import (
    DATASET_ALL_COLUMNS,
    DATASET_NAMES,
    DATASET_REQUIRED_COLUMNS,
    DEFAULT_ADJUSTMENT_POLICY,
    DEFAULT_AVAILABLE_AT_RULE,
    PARQUET_SCHEMA_VERSION,
    STANDARD_PARQUET_FILES,
)
from engine.manifest import ManifestError, ManifestFormatError, ManifestStore
from engine.source_registry import SourceRegistryError, validate_exact_source_interface


DATASET_BY_INTERFACE = {
    "prices": "prices",
    "stock_zh_a_hist": "prices",
    "index_members": "index_members",
    "index_stock_cons": "index_members",
    "trade_calendar": "trade_calendar",
    "tool_trade_date_hist_sina": "trade_calendar",
}

FIELD_ALIASES = {
    "prices": {
        "trade_date": ("trade_date", "date", "日期"),
        "symbol": ("symbol", "code", "股票代码"),
        "close": ("close", "收盘", "收盘价"),
        "available_at": ("available_at",),
        "adjustment_policy": ("adjustment_policy", "复权口径"),
        "volume": ("volume", "成交量"),
        "amount": ("amount", "成交额"),
        "is_suspended": ("is_suspended", "停牌"),
        "limit_up": ("limit_up", "涨停价"),
        "limit_down": ("limit_down", "跌停价"),
    },
    "index_members": {
        "symbol": ("symbol", "code", "品种代码", "成分券代码"),
        "snapshot_date": ("snapshot_date", "date", "纳入日期"),
        "effective_date": ("effective_date", "生效日期", "纳入日期"),
        "available_at": ("available_at",),
        "is_member": ("is_member",),
        "is_pit_universe": ("is_pit_universe",),
        "index_code": ("index_code", "指数代码"),
    },
    "trade_calendar": {
        "trade_date": ("trade_date", "date", "calendar_date", "交易日"),
        "is_open": ("is_open", "open", "是否交易"),
    },
}


class NormalizationError(Exception):
    """标准化基础异常。"""


class RawFormatError(NormalizationError):
    """raw JSONL 格式损坏。"""

    def __init__(
        self,
        raw_path: str | Path,
        message: str,
        *,
        batch_id: str = "",
        line_number: int | None = None,
    ) -> None:
        location = f"{raw_path}"
        if line_number is not None:
            location = f"{location}:{line_number}"
        detail = f"raw 解析失败: {location}: {message}"
        if batch_id:
            detail = f"{detail}; batch_id={batch_id}"
        super().__init__(detail)
        self.raw_path = str(raw_path)
        self.batch_id = batch_id
        self.line_number = line_number
        self.message = message


class NormalizationMappingError(NormalizationError):
    """raw interface 或字段无法映射。"""

    def __init__(
        self,
        interface: str,
        dataset: str,
        missing_fields: Iterable[str] = (),
    ) -> None:
        missing = tuple(missing_fields)
        suffix = f"; missing_fields={','.join(missing)}" if missing else ""
        super().__init__(
            f"标准化映射失败: interface={interface!r}, dataset={dataset!r}{suffix}"
        )
        self.interface = interface
        self.dataset = dataset
        self.missing_fields = missing


class ParquetWriteError(NormalizationError):
    """parquet 写入失败。"""


class SchemaValidationError(NormalizationError):
    """标准化 schema 校验失败。"""


class SourceInterfaceValidationError(NormalizationError):
    """source/interface 注册表校验失败。"""


@dataclass(slots=True)
class RawBatchInput:
    raw_path: str
    metadata: dict[str, Any]
    rows: list[dict[str, Any]]


@dataclass(slots=True)
class DatasetFrameResult:
    dataset: str
    frame: pd.DataFrame
    duplicate_record_count: int = 0
    duplicate_resolved_count: int = 0
    abnormal_price_count: int = 0
    missing_required_fields: list[str] = field(default_factory=list)
    available_at_rule: str = DEFAULT_AVAILABLE_AT_RULE
    adjustment_policy: str = DEFAULT_ADJUSTMENT_POLICY
    is_pit_universe: bool = False


@dataclass(slots=True)
class ParquetWriteResult:
    dataset: str
    path: str
    row_count: int
    schema_version: str


@dataclass(slots=True)
class StandardizationResult:
    manifest_path: str
    manifest_run_ids: list[str]
    parquet_paths: dict[str, str]
    dataset_rows: dict[str, int]
    failed_batches: list[dict[str, Any]]
    mapping_failures: list[dict[str, Any]]
    duplicate_record_count: int
    abnormal_price_count: int
    schema_version: str = PARQUET_SCHEMA_VERSION


def load_manifest_records(manifest_path: str | Path) -> list[dict[str, Any]]:
    """读取 manifest JSONL；损坏行会带路径和行号 fail fast。"""

    try:
        return list(ManifestStore(manifest_path).iter_records())
    except ManifestFormatError:
        raise
    except ManifestError as exc:
        raise NormalizationError(f"manifest 读取失败: {manifest_path}: {exc}") from exc


def read_raw_jsonl(raw_path: str | Path) -> RawBatchInput:
    """解析 STORY-002 raw JSONL，第一行必须是 batch_metadata。"""

    path = Path(raw_path)
    metadata: dict[str, Any] | None = None
    rows: list[dict[str, Any]] = []

    try:
        with path.open("r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                text = line.strip()
                if not text:
                    continue
                try:
                    record = json.loads(text)
                except json.JSONDecodeError as exc:
                    raise RawFormatError(
                        path,
                        exc.msg,
                        batch_id=(metadata or {}).get("batch_id", ""),
                        line_number=line_number,
                    ) from exc
                if not isinstance(record, dict):
                    raise RawFormatError(path, "JSONL 行必须是 object", line_number=line_number)

                record_type = record.get("_record_type")
                if line_number == 1:
                    if record_type != "batch_metadata":
                        raise RawFormatError(path, "第一行必须是 batch_metadata", line_number=1)
                    metadata = dict(record)
                    continue

                if record_type == "data":
                    rows.append({k: v for k, v in record.items() if k != "_record_type"})
                elif record_type == "payload":
                    rows.extend(_payload_to_rows(record.get("payload"), path, line_number))
                else:
                    raise RawFormatError(
                        path,
                        f"不支持的 _record_type: {record_type!r}",
                        batch_id=(metadata or {}).get("batch_id", ""),
                        line_number=line_number,
                    )
    except RawFormatError:
        raise
    except OSError as exc:
        raise RawFormatError(path, str(exc)) from exc

    if metadata is None:
        raise RawFormatError(path, "缺少 batch_metadata")
    return RawBatchInput(raw_path=str(path), metadata=metadata, rows=rows)


def map_raw_to_dataset(
    raw_rows: list[dict[str, Any]],
    metadata: dict[str, Any],
    mapping: dict[str, str] | None = None,
) -> tuple[str, pd.DataFrame]:
    """按显式 target_dataset 或 exact interface 映射到标准 dataset。"""

    request_params = metadata.get("request_params") or {}
    target_dataset = request_params.get("target_dataset") or metadata.get("target_dataset")
    effective_mapping = mapping or DATASET_BY_INTERFACE
    interface = str(metadata.get("interface") or "")
    if target_dataset:
        dataset = str(target_dataset)
        if dataset not in DATASET_NAMES:
            raise NormalizationMappingError(interface, dataset)
    else:
        dataset = effective_mapping.get(interface, "")
        if not dataset:
            raise NormalizationMappingError(interface, "")
    try:
        validate_exact_source_interface(
            str(metadata.get("source") or ""),
            interface,
            request_params,
        )
    except SourceRegistryError as exc:
        raise SourceInterfaceValidationError(str(exc)) from exc

    if not raw_rows:
        frame = pd.DataFrame()
    else:
        frame = pd.DataFrame(raw_rows)
    return dataset, frame


def normalize_prices(
    records: list[dict[str, Any]] | pd.DataFrame,
    schema_version: str = PARQUET_SCHEMA_VERSION,
    *,
    metadata: dict[str, Any] | None = None,
) -> DatasetFrameResult:
    """标准化价格数据，保留未解决重复键供质量报告判定 fail。"""

    _validate_schema_version(schema_version)
    source = _as_frame(records)
    mapped, missing = _map_columns(source, "prices")
    request_params = (metadata or {}).get("request_params") or {}
    if "symbol" in missing:
        injected = _infer_symbol(metadata or {})
        if injected:
            mapped["symbol"] = injected
            missing.remove("symbol")
    if missing:
        raise NormalizationMappingError(
            str((metadata or {}).get("interface") or ""),
            "prices",
            missing,
        )

    mapped["trade_date"] = _date_series(mapped["trade_date"], "prices.trade_date")
    mapped["symbol"] = mapped["symbol"].astype("string").str.strip()
    mapped["close"] = pd.to_numeric(mapped["close"], errors="coerce")
    mapped["available_at"] = _series_or_default(mapped, "available_at", "").fillna("").astype("string")
    mapped["adjustment_policy"] = (
        _series_or_default(
            mapped,
            "adjustment_policy",
            request_params.get("adjust", DEFAULT_ADJUSTMENT_POLICY),
        )
        .fillna(DEFAULT_ADJUSTMENT_POLICY)
        .astype("string")
    )
    for column in ("volume", "amount", "limit_up", "limit_down"):
        if column in mapped:
            mapped[column] = pd.to_numeric(mapped[column], errors="coerce")
    if "is_suspended" in mapped:
        mapped["is_suspended"] = _bool_series(mapped["is_suspended"], default=False)

    abnormal_price_count = int(mapped["close"].notna().mask(mapped["close"] > 0, False).sum())
    resolved, unresolved_count, resolved_count = _resolve_duplicates(
        mapped,
        ["trade_date", "symbol"],
    )
    ordered = _order_columns(resolved, "prices")
    policies = sorted(
        {
            str(value)
            for value in ordered["adjustment_policy"].dropna().unique().tolist()
            if str(value)
        }
    )
    if len(policies) > 1:
        unresolved_count += len(ordered)
    return DatasetFrameResult(
        dataset="prices",
        frame=ordered.sort_values(["trade_date", "symbol"], kind="stable").reset_index(drop=True),
        duplicate_record_count=unresolved_count,
        duplicate_resolved_count=resolved_count,
        abnormal_price_count=abnormal_price_count,
        adjustment_policy=policies[0] if len(policies) == 1 else ",".join(policies),
    )


def normalize_index_members(
    records: list[dict[str, Any]] | pd.DataFrame,
    schema_version: str = PARQUET_SCHEMA_VERSION,
    *,
    metadata: dict[str, Any] | None = None,
) -> DatasetFrameResult:
    """标准化指数成分股快照。"""

    _validate_schema_version(schema_version)
    source = _as_frame(records)
    mapped, missing = _map_columns(source, "index_members")
    request_params = (metadata or {}).get("request_params") or {}
    if missing:
        raise NormalizationMappingError(
            str((metadata or {}).get("interface") or ""),
            "index_members",
            missing,
        )
    mapped["symbol"] = mapped["symbol"].astype("string").str.strip()
    if "snapshot_date" in mapped:
        mapped["snapshot_date"] = _date_series(
            mapped["snapshot_date"],
            "index_members.snapshot_date",
            required=False,
        )
    elif request_params.get("snapshot_date"):
        mapped["snapshot_date"] = _format_date_value(request_params["snapshot_date"])
    else:
        mapped["snapshot_date"] = ""
    if "effective_date" in mapped:
        mapped["effective_date"] = _date_series(
            mapped["effective_date"],
            "index_members.effective_date",
            required=False,
        )
    elif request_params.get("effective_date"):
        mapped["effective_date"] = _format_date_value(request_params["effective_date"])
    else:
        mapped["effective_date"] = mapped["snapshot_date"]
    mapped["available_at"] = _series_or_default(mapped, "available_at", "").fillna("").astype("string")
    if "is_member" in mapped:
        mapped["is_member"] = _bool_series(mapped["is_member"], default=True)
    else:
        mapped["is_member"] = True
    if "is_pit_universe" in mapped:
        mapped["is_pit_universe"] = _bool_series(mapped["is_pit_universe"], default=False)
    else:
        mapped["is_pit_universe"] = bool(
            request_params.get("is_pit_universe") or request_params.get("pit_universe")
        )
    if "index_code" not in mapped and request_params.get("index_code"):
        mapped["index_code"] = str(request_params["index_code"])
    elif "index_code" not in mapped:
        mapped["index_code"] = ""
    if bool(mapped["is_pit_universe"].fillna(False).any()):
        try:
            validate_exact_source_interface(
                str((metadata or {}).get("source") or ""),
                str((metadata or {}).get("interface") or ""),
                {**request_params, "target_dataset": "index_members", "is_pit_universe": True},
            )
        except SourceRegistryError as exc:
            raise SourceInterfaceValidationError(str(exc)) from exc
        missing_pit = [
            field
            for field in ("index_code", "effective_date", "available_at", "is_member")
            if field not in mapped or mapped[field].fillna("").astype(str).eq("").any()
        ]
        if missing_pit:
            raise SchemaValidationError(
                "PIT index_members 缺少字段: " + ", ".join(missing_pit)
            )
    ordered = _order_columns(mapped, "index_members")
    dedupe_keys = ["symbol", "effective_date"] if bool(ordered["is_pit_universe"].fillna(False).any()) else ["symbol"]
    ordered = ordered.drop_duplicates(subset=dedupe_keys, keep="last")
    return DatasetFrameResult(
        dataset="index_members",
        frame=ordered.sort_values(["symbol"], kind="stable").reset_index(drop=True),
        is_pit_universe=bool(ordered["is_pit_universe"].fillna(False).all()),
    )


def normalize_trade_calendar(
    records: list[dict[str, Any]] | pd.DataFrame,
    schema_version: str = PARQUET_SCHEMA_VERSION,
    *,
    metadata: dict[str, Any] | None = None,
) -> DatasetFrameResult:
    """标准化交易日历。"""

    _validate_schema_version(schema_version)
    source = _as_frame(records)
    mapped, missing = _map_columns(source, "trade_calendar")
    if missing:
        raise NormalizationMappingError(
            str((metadata or {}).get("interface") or ""),
            "trade_calendar",
            missing,
        )
    mapped["trade_date"] = _date_series(mapped["trade_date"], "trade_calendar.trade_date")
    if "is_open" in mapped:
        mapped["is_open"] = _bool_series(mapped["is_open"], default=True)
    else:
        mapped["is_open"] = True
    resolved, unresolved_count, resolved_count = _resolve_duplicates(mapped, ["trade_date"])
    ordered = _order_columns(resolved, "trade_calendar")
    return DatasetFrameResult(
        dataset="trade_calendar",
        frame=ordered.sort_values(["trade_date"], kind="stable").reset_index(drop=True),
        duplicate_record_count=unresolved_count,
        duplicate_resolved_count=resolved_count,
    )


def write_standard_parquet(
    dataset: str,
    frame: pd.DataFrame,
    output_path: str | Path,
) -> ParquetWriteResult:
    """同目录临时文件写入并原子替换目标 parquet。"""

    if dataset not in DATASET_NAMES:
        raise ParquetWriteError(f"未知 dataset: {dataset}")
    path = Path(output_path)
    _ensure_parent_dir(path)
    _validate_frame_schema(dataset, frame)
    temp_path = path.with_name(f".{path.name}.tmp")
    try:
        frame.to_parquet(temp_path, index=False, engine="pyarrow")
        pd.read_parquet(temp_path, engine="pyarrow")
        os.replace(temp_path, path)
    except Exception as exc:
        try:
            if temp_path.exists():
                temp_path.unlink()
        finally:
            raise ParquetWriteError(f"parquet 写入失败: {path}: {exc}") from exc
    return ParquetWriteResult(
        dataset=dataset,
        path=str(path),
        row_count=len(frame),
        schema_version=PARQUET_SCHEMA_VERSION,
    )


def run_normalization(
    manifest_path: str | Path,
    raw_root: str | Path = "data/raw",
    output_dir: str | Path = "data",
    mapping: dict[str, str] | None = None,
) -> StandardizationResult:
    """从 manifest/raw 派生三类标准 parquet；不会调用远程数据源。"""

    records = _latest_manifest_records(load_manifest_records(manifest_path))
    frames_by_dataset: dict[str, list[pd.DataFrame]] = {dataset: [] for dataset in DATASET_NAMES}
    failed_batches: list[dict[str, Any]] = []
    mapping_failures: list[dict[str, Any]] = []
    duplicate_record_count = 0
    abnormal_price_count = 0
    manifest_run_ids: set[str] = set()

    for record in records:
        run_id = str(record.get("run_id") or "")
        if run_id:
            manifest_run_ids.add(run_id)
        status = str(record.get("status") or "")
        if status == "failed":
            failed_batches.append(_failed_batch_record(record))
            continue
        raw_path = str(record.get("raw_path") or "")
        if status not in {"success", "partial_success", "skipped"} or not raw_path:
            continue
        resolved_raw_path = _resolve_raw_path(raw_path, raw_root)
        if not resolved_raw_path.exists():
            failed_batches.append(
                {
                    **_failed_batch_record(record),
                    "error_type": "RawPathMissing",
                    "error_message": f"raw_path 不存在: {resolved_raw_path}",
                }
            )
            continue

        try:
            raw_batch = read_raw_jsonl(resolved_raw_path)
            _validate_manifest_raw_pair(record, raw_batch)
            dataset, raw_frame = map_raw_to_dataset(
                raw_batch.rows,
                raw_batch.metadata,
                mapping,
            )
            result = _normalize_dataset(dataset, raw_frame, raw_batch.metadata)
        except NormalizationMappingError as exc:
            mapping_failures.append(
                {
                    "batch_id": record.get("batch_id", ""),
                    "raw_path": str(resolved_raw_path),
                    "interface": exc.interface,
                    "dataset": exc.dataset,
                    "missing_fields": list(exc.missing_fields),
                    "error_message": str(exc),
                }
            )
            continue
        frames_by_dataset[result.dataset].append(result.frame)
        duplicate_record_count += result.duplicate_record_count
        abnormal_price_count += result.abnormal_price_count

    parquet_paths: dict[str, str] = {}
    dataset_rows: dict[str, int] = {}
    for dataset in DATASET_NAMES:
        frames = frames_by_dataset[dataset]
        if not frames:
            continue
        combined = pd.concat(frames, ignore_index=True)
        combined_result = _normalize_dataset(dataset, combined, {"interface": dataset})
        output_path = Path(output_dir) / STANDARD_PARQUET_FILES[dataset]
        write_result = write_standard_parquet(dataset, combined_result.frame, output_path)
        parquet_paths[dataset] = write_result.path
        dataset_rows[dataset] = write_result.row_count
        duplicate_record_count += combined_result.duplicate_record_count
        abnormal_price_count += combined_result.abnormal_price_count

    return StandardizationResult(
        manifest_path=str(manifest_path),
        manifest_run_ids=sorted(manifest_run_ids),
        parquet_paths=parquet_paths,
        dataset_rows=dataset_rows,
        failed_batches=failed_batches,
        mapping_failures=mapping_failures,
        duplicate_record_count=duplicate_record_count,
        abnormal_price_count=abnormal_price_count,
    )


def _payload_to_rows(payload: Any, raw_path: Path, line_number: int) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        rows = payload
    elif isinstance(payload, dict):
        for value in payload.values():
            if isinstance(value, list):
                rows = value
                break
        else:
            rows = [payload]
    else:
        raise RawFormatError(raw_path, "payload 必须可展开为 object/list", line_number=line_number)
    normalized: list[dict[str, Any]] = []
    for item in rows:
        if not isinstance(item, dict):
            raise RawFormatError(
                raw_path,
                "payload 列表元素必须是 object",
                line_number=line_number,
            )
        normalized.append(dict(item))
    return normalized


def _as_frame(records: list[dict[str, Any]] | pd.DataFrame) -> pd.DataFrame:
    if isinstance(records, pd.DataFrame):
        return records.copy()
    return pd.DataFrame(records)


def _map_columns(frame: pd.DataFrame, dataset: str) -> tuple[pd.DataFrame, list[str]]:
    mapped = pd.DataFrame(index=frame.index)
    aliases = FIELD_ALIASES[dataset]
    for target, names in aliases.items():
        source_name = next((name for name in names if name in frame.columns), None)
        if source_name is not None:
            mapped[target] = frame[source_name]
    missing = [
        column
        for column in DATASET_REQUIRED_COLUMNS[dataset]
        if column not in mapped
    ]
    return mapped, missing


def _normalize_dataset(
    dataset: str,
    frame: pd.DataFrame,
    metadata: dict[str, Any],
) -> DatasetFrameResult:
    if dataset == "prices":
        return normalize_prices(frame, metadata=metadata)
    if dataset == "index_members":
        return normalize_index_members(frame, metadata=metadata)
    if dataset == "trade_calendar":
        return normalize_trade_calendar(frame, metadata=metadata)
    raise NormalizationMappingError(str(metadata.get("interface") or ""), dataset)


def _date_series(series: pd.Series, field_name: str, *, required: bool = True) -> pd.Series:
    parsed = pd.to_datetime(series, errors="coerce")
    if required and parsed.isna().any():
        raise SchemaValidationError(f"日期字段不可解析: {field_name}")
    return parsed.dt.strftime("%Y-%m-%d").fillna("")


def _format_date_value(value: Any) -> str:
    parsed = pd.to_datetime(pd.Series([value]), errors="coerce")
    if parsed.isna().iloc[0]:
        return ""
    return str(parsed.dt.strftime("%Y-%m-%d").iloc[0])


def _bool_series(series: pd.Series, *, default: bool) -> pd.Series:
    def coerce(value: Any) -> bool:
        if pd.isna(value):
            return default
        if isinstance(value, bool):
            return value
        text = str(value).strip().lower()
        if text in {"true", "1", "yes", "y", "open", "交易", "是"}:
            return True
        if text in {"false", "0", "no", "n", "closed", "非交易", "否"}:
            return False
        return default

    return series.map(coerce).astype(bool)


def _series_or_default(frame: pd.DataFrame, column: str, default: Any) -> pd.Series:
    if column in frame:
        return frame[column]
    return pd.Series([default] * len(frame), index=frame.index)


def _resolve_duplicates(
    frame: pd.DataFrame,
    keys: list[str],
) -> tuple[pd.DataFrame, int, int]:
    if frame.empty:
        return frame, 0, 0
    exact_resolved = int(frame.duplicated(keep="first").sum())
    deduped = frame.drop_duplicates(keep="first")
    unresolved_mask = deduped.duplicated(subset=keys, keep=False)
    unresolved_count = int(unresolved_mask.sum())
    return deduped, unresolved_count, exact_resolved


def _order_columns(frame: pd.DataFrame, dataset: str) -> pd.DataFrame:
    columns = [column for column in DATASET_ALL_COLUMNS[dataset] if column in frame.columns]
    missing_optional = [
        column
        for column in DATASET_ALL_COLUMNS[dataset]
        if column not in columns and column not in DATASET_REQUIRED_COLUMNS[dataset]
    ]
    ordered = frame.loc[:, columns].copy()
    for column in missing_optional:
        ordered[column] = ""
    return ordered.loc[:, list(DATASET_ALL_COLUMNS[dataset])]


def _validate_frame_schema(dataset: str, frame: pd.DataFrame) -> None:
    missing = [
        column
        for column in DATASET_REQUIRED_COLUMNS[dataset]
        if column not in frame.columns
    ]
    if missing:
        raise SchemaValidationError(
            f"{dataset} 缺少必需字段: {', '.join(missing)}"
        )


def _validate_schema_version(schema_version: str) -> None:
    if schema_version != PARQUET_SCHEMA_VERSION:
        raise SchemaValidationError(
            f"不支持的 parquet schema version: {schema_version}"
        )


def _ensure_parent_dir(path: Path) -> None:
    parent = path.parent
    if not parent or str(parent) == ".":
        return
    current = Path(parent.anchor) if parent.is_absolute() else Path(".")
    parts = parent.parts[1:] if parent.is_absolute() else parent.parts
    for part in parts:
        current = current / part
        if current.exists() and not current.is_dir():
            raise ParquetWriteError(f"安装路径被非目录占用: {current}")
    parent.mkdir(parents=True, exist_ok=True)


def _infer_symbol(metadata: dict[str, Any]) -> str:
    request_params = metadata.get("request_params") or {}
    for key in ("symbol", "code"):
        value = request_params.get(key)
        if value:
            return str(value)
    symbols = request_params.get("symbols") or metadata.get("symbol_range") or []
    if isinstance(symbols, list) and len(symbols) == 1:
        return str(symbols[0])
    return ""


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


def _failed_batch_record(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "run_id": record.get("run_id", ""),
        "batch_id": record.get("batch_id", ""),
        "interface": record.get("interface", ""),
        "status": record.get("status", ""),
        "coverage_start": record.get("coverage_start", ""),
        "coverage_end": record.get("coverage_end", ""),
        "failed_items": record.get("failed_items", []),
        "error_type": record.get("error_type", ""),
        "error_message": record.get("error_message", ""),
        "raw_path": record.get("raw_path", ""),
    }


def _resolve_raw_path(raw_path: str, raw_root: str | Path) -> Path:
    path = Path(raw_path)
    if path.is_absolute() or path.exists():
        return path
    candidate = Path(raw_root) / path
    if candidate.exists():
        return candidate
    return path


def _validate_manifest_raw_pair(record: dict[str, Any], raw_batch: RawBatchInput) -> None:
    metadata = raw_batch.metadata
    for field in ("batch_id", "run_id"):
        manifest_value = str(record.get(field) or "")
        raw_value = str(metadata.get(field) or "")
        if manifest_value and raw_value and manifest_value != raw_value:
            raise RawFormatError(
                raw_batch.raw_path,
                f"manifest 与 raw {field} 不一致",
                batch_id=raw_value,
            )


__all__ = (
    "DATASET_BY_INTERFACE",
    "DatasetFrameResult",
    "NormalizationError",
    "NormalizationMappingError",
    "ParquetWriteError",
    "ParquetWriteResult",
    "RawBatchInput",
    "RawFormatError",
    "SchemaValidationError",
    "SourceInterfaceValidationError",
    "StandardizationResult",
    "load_manifest_records",
    "map_raw_to_dataset",
    "normalize_index_members",
    "normalize_prices",
    "normalize_trade_calendar",
    "read_raw_jsonl",
    "run_normalization",
    "write_standard_parquet",
)
