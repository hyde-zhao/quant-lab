"""raw/manifest 到 canonical parquet 的标准化。"""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Any, Mapping

import pandas as pd

from .contracts import (
    CANONICAL_ADJ_FACTOR_COLUMNS,
    CANONICAL_HS300_INDEX_COLUMNS,
    CANONICAL_INDEX_MEMBERS_COLUMNS,
    CANONICAL_INDEX_WEIGHTS_COLUMNS,
    CANONICAL_EVENTS_COLUMNS,
    CANONICAL_PRICES_LIMIT_COLUMNS,
    CANONICAL_STOCK_BASIC_COLUMNS,
    CANONICAL_TRADE_STATUS_COLUMNS,
    CANONICAL_TRADE_CALENDAR_COLUMNS,
    CR005_CANONICAL_PRICES_COLUMNS,
    DATASET_ADJ_FACTOR,
    DATASET_EVENTS,
    DATASET_HS300_INDEX,
    DATASET_INDEX_MEMBERS,
    DATASET_INDEX_WEIGHTS,
    DATASET_PRICES_LIMIT,
    DATASET_PRICES,
    DATASET_SCHEMA_REGISTRY,
    DATASET_STOCK_BASIC,
    DATASET_TRADE_CALENDAR,
    DATASET_TRADE_STATUS,
    DATASETS,
    INTERFACE_EVENTS_DISCLOSURE,
    INTERFACE_HS300_INDEX_DAILY,
    INTERFACE_INDEX_MEMBERS_SNAPSHOT,
    INTERFACE_INDEX_WEIGHTS_SNAPSHOT,
    INTERFACE_PRICES_LIMIT_DAILY,
    INTERFACE_PRICES_ADJ_FACTOR,
    INTERFACE_PRICES_DAILY,
    INTERFACE_STOCK_BASIC_SNAPSHOT,
    INTERFACE_TRADE_STATUS_DAILY,
    INTERFACE_TRADE_CALENDAR_DAILY,
    PIT_STATUS_AVAILABLE,
    PIT_STATUS_INCOMPLETE,
    PIT_STATUS_NON_PIT_SNAPSHOT,
    READINESS_STATUS_AVAILABLE,
    READINESS_STATUS_NON_PIT_SNAPSHOT,
    READINESS_STATUS_PIT_INCOMPLETE,
    SCHEMA_VERSION,
    SOURCE_TUSHARE,
)
from .lake_layout import LakeLayout, ensure_parent_dirs_for_write


class DatasetMappingError(ValueError):
    """raw 到 dataset 映射不满足 exact 契约。"""


class CanonicalSchemaError(ValueError):
    """canonical schema 或 raw 字段不满足契约。"""


class ManifestLineageError(RuntimeError):
    """manifest/raw/canonical 血缘校验失败。"""


ADJUSTMENT_POLICY_CONFLICT = "adjustment_policy_conflict"
AVAILABLE_AT_RULE_DAILY_CLOSE_FACT = "daily_close_fact"
AVAILABLE_AT_RULE_CALENDAR_KNOWN = "calendar_known"
AVAILABLE_AT_RULE_DATE_ONLY_NEXT_OPEN = "date_only_next_open"
AVAILABLE_AT_RULE_EXPLICIT_TIMESTAMP = "explicit_timestamp"
AVAILABLE_AT_RULE_MISSING_REQUIRED = "missing_required"
AVAILABLE_AT_RULE_TUSHARE_INDEX_WEIGHT_EFFECTIVE_CLOSE = "tushare_index_weight_effective_date_16:00"
AVAILABLE_AT_RULE_TUSHARE_STOCK_BASIC_LIST_DATE = "tushare_stock_basic_list_date"
AVAILABLE_AT_RULE_TUSHARE_STOCK_ST_0920 = "tushare_stock_st_09:20"
AVAILABLE_AT_RULE_TUSHARE_STK_LIMIT_0840 = "tushare_stk_limit_08:40"
AVAILABLE_AT_RULE_TUSHARE_SUSPEND_D_0930 = "tushare_suspend_d_09:30_stock_st_09:20_daily"

W3_UNRESOLVED_DATASETS = frozenset(
    {
        DATASET_TRADE_STATUS,
        DATASET_PRICES_LIMIT,
        DATASET_EVENTS,
    }
)


DEFAULT_INTERFACE_DATASET_MAP: dict[str, str] = {
    INTERFACE_PRICES_DAILY: DATASET_PRICES,
    INTERFACE_PRICES_ADJ_FACTOR: DATASET_ADJ_FACTOR,
    INTERFACE_HS300_INDEX_DAILY: DATASET_HS300_INDEX,
    INTERFACE_TRADE_CALENDAR_DAILY: DATASET_TRADE_CALENDAR,
    INTERFACE_INDEX_MEMBERS_SNAPSHOT: DATASET_INDEX_MEMBERS,
    INTERFACE_INDEX_WEIGHTS_SNAPSHOT: DATASET_INDEX_WEIGHTS,
    INTERFACE_STOCK_BASIC_SNAPSHOT: DATASET_STOCK_BASIC,
    INTERFACE_TRADE_STATUS_DAILY: DATASET_TRADE_STATUS,
    INTERFACE_PRICES_LIMIT_DAILY: DATASET_PRICES_LIMIT,
    INTERFACE_EVENTS_DISCLOSURE: DATASET_EVENTS,
}


@dataclass(frozen=True, slots=True)
class NormalizationResult:
    dataset: str
    run_id: str | None
    canonical_paths: tuple[Path, ...]
    row_count: int
    manifest_records: tuple[dict[str, Any], ...] = field(default_factory=tuple)
    skipped_status_counts: dict[str, int] = field(default_factory=dict)
    lineage_filled_from_manifest: bool = False


CANDIDATE_UNPUBLISHED = "candidate_unpublished"
REPLAY_SOURCE_MISSING = "replay_source_missing"
NORMALIZE_MANIFEST_INCOMPLETE = "normalize_manifest_incomplete"


@dataclass(frozen=True, slots=True)
class NormalizeCandidate:
    dataset: str
    run_id: str
    candidate_path: str
    candidate_layer: str = "canonical"
    status: str = CANDIDATE_UNPUBLISHED
    current_pointer_changes: int = 0
    provider_fetches: int = 0
    credential_reads: int = 0
    raw_writes: int = 0
    publish_count: int = 0
    manifest_complete: bool = True
    error_codes: tuple[str, ...] = ()
    details: tuple[dict[str, Any], ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "dataset": self.dataset,
            "run_id": self.run_id,
            "candidate_path": self.candidate_path,
            "candidate_layer": self.candidate_layer,
            "status": self.status,
            "current_pointer_changes": self.current_pointer_changes,
            "provider_fetches": self.provider_fetches,
            "credential_reads": self.credential_reads,
            "raw_writes": self.raw_writes,
            "publish_count": self.publish_count,
            "manifest_complete": self.manifest_complete,
            "error_codes": list(self.error_codes),
            "details": [dict(item) for item in self.details],
        }


@dataclass(frozen=True, slots=True)
class ReplayRequest:
    run_id: str
    batch_id: str
    dataset: str | None = None


@dataclass(frozen=True, slots=True)
class ReplayResult:
    run_id: str
    batch_id: str
    status: str
    candidate: NormalizeCandidate | None = None
    provider_fetches: int = 0
    credential_reads: int = 0
    raw_writes: int = 0
    current_pointer_changes: int = 0
    publish_count: int = 0
    error_codes: tuple[str, ...] = ()
    details: tuple[dict[str, Any], ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "batch_id": self.batch_id,
            "status": self.status,
            "candidate": self.candidate.to_dict() if self.candidate else None,
            "provider_fetches": self.provider_fetches,
            "credential_reads": self.credential_reads,
            "raw_writes": self.raw_writes,
            "current_pointer_changes": self.current_pointer_changes,
            "publish_count": self.publish_count,
            "error_codes": list(self.error_codes),
            "details": [dict(item) for item in self.details],
        }


def _record_payload(record: Mapping[str, Any] | object) -> dict[str, Any]:
    if isinstance(record, Mapping):
        return dict(record)
    to_dict = getattr(record, "to_dict", None)
    if callable(to_dict):
        return dict(to_dict())
    raise TypeError(f"不支持的 P0 manifest 输入类型: {type(record)!r}")


def normalize_p0_candidate(
    manifest_record: Mapping[str, Any] | object,
    raw_ref: str | None = None,
    dataset_contract: Mapping[str, Any] | None = None,
) -> NormalizeCandidate:
    """从 S02 manifest 合同生成未发布 candidate；不更新 current pointer。"""

    from .manifest import validate_manifest_record

    payload = _record_payload(manifest_record)
    dataset = str(payload.get("dataset") or (dataset_contract or {}).get("dataset") or "")
    run_id = str(payload.get("run_id") or "")
    candidate_path = str(payload.get("candidate_path") or "")
    manifest_check = validate_manifest_record(payload)
    details: list[dict[str, Any]] = []
    error_codes: list[str] = []
    if not manifest_check.passed:
        error_codes.append(NORMALIZE_MANIFEST_INCOMPLETE)
        error_codes.extend(manifest_check.error_codes)
        details.extend(manifest_check.details)
    if raw_ref is None and not payload.get("raw_path"):
        details.append(
            {
                "code": "raw_ref_not_materialized_by_s03",
                "unblock_condition": "authorized_run_must_materialize_raw_before_normalize",
            }
        )

    return NormalizeCandidate(
        dataset=dataset,
        run_id=run_id,
        candidate_path=candidate_path,
        status=CANDIDATE_UNPUBLISHED if not error_codes else "blocked",
        current_pointer_changes=0,
        provider_fetches=0,
        credential_reads=0,
        raw_writes=0,
        publish_count=0,
        manifest_complete=manifest_check.passed,
        error_codes=tuple(dict.fromkeys(error_codes)),
        details=tuple(details),
    )


def _find_replay_record(
    request: ReplayRequest,
    manifest_store: Mapping[str, Any] | list[Mapping[str, Any]] | tuple[Mapping[str, Any], ...] | None,
) -> dict[str, Any] | None:
    if manifest_store is None:
        return None
    records: list[Mapping[str, Any]]
    if isinstance(manifest_store, Mapping):
        values = manifest_store.get("records")
        if isinstance(values, list):
            records = values
        else:
            records = [manifest_store]
    else:
        records = list(manifest_store)
    for record in records:
        if str(record.get("run_id") or "") != request.run_id:
            continue
        if str(record.get("batch_id") or "") != request.batch_id:
            continue
        if request.dataset and str(record.get("dataset") or "") != request.dataset:
            continue
        return dict(record)
    return None


def replay_p0_candidate(
    run_id: str,
    batch_id: str,
    manifest_store: Mapping[str, Any] | list[Mapping[str, Any]] | tuple[Mapping[str, Any], ...] | None = None,
    *,
    dataset: str | None = None,
) -> ReplayResult:
    """P0 replay 只消费已有 manifest/raw 引用；缺源时不补抓 provider。"""

    request = ReplayRequest(run_id=run_id, batch_id=batch_id, dataset=dataset)
    record = _find_replay_record(request, manifest_store)
    if record is None:
        return ReplayResult(
            run_id=run_id,
            batch_id=batch_id,
            status="blocked",
            error_codes=(REPLAY_SOURCE_MISSING,),
            details=(
                {
                    "code": REPLAY_SOURCE_MISSING,
                    "unblock_condition": "provide_existing_manifest_raw_reference_or_authorize_separate_run",
                },
            ),
        )
    candidate = normalize_p0_candidate(record, raw_ref=str(record.get("raw_path") or "manifest_raw"))
    return ReplayResult(
        run_id=run_id,
        batch_id=batch_id,
        status="candidate_unpublished" if not candidate.error_codes else "blocked",
        candidate=candidate,
        provider_fetches=0,
        credential_reads=0,
        raw_writes=0,
        current_pointer_changes=0,
        publish_count=0,
        error_codes=candidate.error_codes,
        details=candidate.details,
    )


def _load_manifest_records(manifest_path: Path) -> list[dict[str, Any]]:
    if not manifest_path.exists():
        raise ManifestLineageError(f"manifest 不存在: {manifest_path}")
    records: list[dict[str, Any]] = []
    with manifest_path.open("r", encoding="utf-8") as fh:
        for lineno, line in enumerate(fh, start=1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ManifestLineageError(f"manifest 第 {lineno} 行不是合法 JSON") from exc
            if not isinstance(record, dict):
                raise ManifestLineageError(f"manifest 第 {lineno} 行不是对象")
            records.append(record)
    return records


def map_raw_to_dataset(
    manifest_record: Mapping[str, Any],
    target_dataset: str | None = None,
    interface_map: Mapping[str, str] | None = None,
) -> str:
    params = manifest_record.get("params")
    params = params if isinstance(params, Mapping) else {}
    explicit = target_dataset if target_dataset is not None else params.get("target_dataset")
    if explicit is not None:
        if explicit in DATASETS:
            interface = manifest_record.get("interface")
            if explicit in W3_UNRESOLVED_DATASETS and str(interface or "").strip().upper() in {
                "",
                "UNKNOWN",
                "UNRESOLVED",
            }:
                raise DatasetMappingError(f"source_unresolved: dataset={explicit}")
            mapping = dict(interface_map or DEFAULT_INTERFACE_DATASET_MAP)
            mapped = mapping.get(str(interface))
            if (
                explicit == DATASET_INDEX_MEMBERS
                and str(manifest_record.get("source")) == SOURCE_TUSHARE
                and str(interface) == INTERFACE_INDEX_WEIGHTS_SNAPSHOT
            ):
                return DATASET_INDEX_MEMBERS
            if mapped is not None and mapped != explicit:
                raise DatasetMappingError(
                    f"target_dataset 与 exact interface 冲突: {explicit} != {mapped}"
                )
            return str(explicit)
        raise DatasetMappingError(f"不支持的 target_dataset: {explicit}")

    mapping = dict(interface_map or DEFAULT_INTERFACE_DATASET_MAP)
    interface = manifest_record.get("interface")
    if interface in mapping:
        return mapping[str(interface)]
    raise DatasetMappingError(f"无法通过 exact interface 映射 dataset: {interface}")


def load_manifest_success_records(
    manifest_path: str | Path,
    dataset: str,
    *,
    run_id: str | None = None,
) -> list[dict[str, Any]]:
    if dataset not in DATASETS:
        raise DatasetMappingError(f"不支持的 dataset: {dataset}")
    selected: list[dict[str, Any]] = []
    for record in _load_manifest_records(Path(manifest_path)):
        if run_id is not None and record.get("run_id") != run_id:
            continue
        status = record.get("status")
        if status != "success":
            continue
        if _record_feeds_dataset(record, dataset):
            selected.append(record)
    return selected


def _resolve_raw_path(raw_path_value: object, layout: LakeLayout) -> Path:
    if not raw_path_value:
        raise ManifestLineageError("manifest 缺少 raw_path")
    raw_path = Path(str(raw_path_value))
    if not raw_path.is_absolute():
        raw_path = layout.lake_root / raw_path
    if not raw_path.exists():
        raise ManifestLineageError(f"manifest 指向的 raw 不存在: {raw_path}")
    try:
        raw_path.resolve().relative_to(layout.lake_root.resolve())
    except ValueError as exc:
        raise ManifestLineageError(f"raw_path 不在 lake_root 下: {raw_path}") from exc
    return raw_path


def _raw_checksum(raw_path: Path) -> str:
    return hashlib.sha256(raw_path.read_bytes()).hexdigest()


def _read_raw_jsonl(raw_path: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    metadata: dict[str, Any] = {}
    rows: list[dict[str, Any]] = []
    with raw_path.open("r", encoding="utf-8") as fh:
        for lineno, line in enumerate(fh, start=1):
            if not line.strip():
                continue
            try:
                item = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ManifestLineageError(f"raw 第 {lineno} 行不是合法 JSON") from exc
            if not isinstance(item, dict):
                raise ManifestLineageError(f"raw 第 {lineno} 行不是对象")
            if "_metadata" in item:
                value = item["_metadata"]
                metadata = dict(value) if isinstance(value, Mapping) else {}
            else:
                rows.append(item)
    return metadata, rows


def _verify_raw(record: Mapping[str, Any], raw_path: Path, rows: list[dict[str, Any]]) -> None:
    expected_checksum = record.get("raw_checksum")
    if expected_checksum and expected_checksum != _raw_checksum(raw_path):
        raise ManifestLineageError("raw checksum 与 manifest 不一致")
    expected_count = record.get("raw_row_count")
    if expected_count is not None and int(expected_count) != len(rows):
        raise ManifestLineageError("raw row_count 与 manifest 不一致")


def _parse_date(value: object) -> str:
    text = str(value).strip()
    try:
        if len(text) == 8 and text.isdigit():
            return datetime.strptime(text, "%Y%m%d").date().isoformat()
        if len(text) >= 10 and text[4] == "-" and text[7] == "-":
            return date.fromisoformat(text[:10]).isoformat()
    except ValueError as exc:
        raise CanonicalSchemaError("invalid_date") from exc
    raise CanonicalSchemaError("invalid_date")


def _next_available_at(trade_date: str) -> str:
    return f"{trade_date}T16:00:00+08:00"


def _timestamp_at(day: object, time_text: str) -> str:
    return f"{_parse_date(day)}T{time_text}+08:00"


def _available_at_value(row: Mapping[str, Any], source: str, source_interface: str, trade_date: str) -> str:
    if row.get("available_at") not in (None, ""):
        return str(row["available_at"])
    if source == SOURCE_TUSHARE and source_interface == INTERFACE_PRICES_DAILY:
        return _next_available_at(trade_date)
    return _string_value(row, "available_at")


def _daily_available_at_value(row: Mapping[str, Any], record: Mapping[str, Any], trade_date: str) -> str:
    if row.get("available_at") not in (None, ""):
        return str(row["available_at"])
    source = _lineage(record, "source")
    source_interface = _lineage(record, "interface")
    if source == SOURCE_TUSHARE and source_interface == INTERFACE_PRICES_ADJ_FACTOR:
        return _next_available_at(trade_date)
    return str(record.get("finished_at") or _next_available_at(trade_date))


def _available_at_rule_value(row: Mapping[str, Any], default: str) -> str:
    value = row.get("available_at_rule")
    if value in {
        AVAILABLE_AT_RULE_DAILY_CLOSE_FACT,
        AVAILABLE_AT_RULE_CALENDAR_KNOWN,
        AVAILABLE_AT_RULE_DATE_ONLY_NEXT_OPEN,
        AVAILABLE_AT_RULE_EXPLICIT_TIMESTAMP,
        AVAILABLE_AT_RULE_MISSING_REQUIRED,
        AVAILABLE_AT_RULE_TUSHARE_INDEX_WEIGHT_EFFECTIVE_CLOSE,
        AVAILABLE_AT_RULE_TUSHARE_STOCK_BASIC_LIST_DATE,
        AVAILABLE_AT_RULE_TUSHARE_STOCK_ST_0920,
        AVAILABLE_AT_RULE_TUSHARE_STK_LIMIT_0840,
        AVAILABLE_AT_RULE_TUSHARE_SUSPEND_D_0930,
        "not_applicable",
    }:
        return str(value)
    return default


def _float_value(row: Mapping[str, Any], field: str, *, nullable: bool = False) -> float | None:
    value = row.get(field)
    if value is None or value == "":
        if nullable:
            return None
        raise CanonicalSchemaError(f"schema_mismatch: missing {field}")
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise CanonicalSchemaError(f"schema_mismatch: {field} is not numeric") from exc


def _string_value(row: Mapping[str, Any], field: str) -> str:
    value = row.get(field)
    if value is None or value == "":
        raise CanonicalSchemaError(f"schema_mismatch: missing {field}")
    return str(value)


def _optional_string(row: Mapping[str, Any], field: str) -> str:
    value = row.get(field)
    return "" if value is None else str(value)


def _optional_date(value: object) -> str:
    if value is None or value == "":
        return ""
    return _parse_date(value)


def _first_date(*values: object) -> str:
    for value in values:
        parsed = _optional_date(value)
        if parsed:
            return parsed
    raise CanonicalSchemaError("invalid_date")


def _bool_value(value: object, *, default: bool = False) -> bool:
    if value is None or value == "":
        return default
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if text in {"1", "true", "yes", "y"}:
        return True
    if text in {"0", "false", "no", "n"}:
        return False
    return default


def _lineage(record: Mapping[str, Any], field: str, default: object = None) -> str:
    value = record.get(field, default)
    if value is None or value == "":
        raise ManifestLineageError(f"manifest 缺少血缘字段: {field}")
    return str(value)


def _assert_no_duplicate(frame: pd.DataFrame, keys: tuple[str, ...]) -> None:
    if not frame.empty and frame.duplicated(list(keys)).any():
        raise CanonicalSchemaError("duplicate_key")


def _record_params(record: Mapping[str, Any]) -> Mapping[str, Any]:
    params = record.get("params")
    return params if isinstance(params, Mapping) else {}


def _is_tushare_index_weight_record(record: Mapping[str, Any]) -> bool:
    return str(record.get("source")) == SOURCE_TUSHARE and str(record.get("interface")) in {
        INTERFACE_INDEX_MEMBERS_SNAPSHOT,
        INTERFACE_INDEX_WEIGHTS_SNAPSHOT,
    }


def _record_feeds_dataset(record: Mapping[str, Any], dataset: str) -> bool:
    mapped = map_raw_to_dataset(record)
    if mapped == dataset:
        return True
    return dataset == DATASET_INDEX_MEMBERS and _is_tushare_index_weight_record(record)


def _adjustment_policy(
    record: Mapping[str, Any],
    metadata: Mapping[str, Any],
    row: Mapping[str, Any],
    *,
    default: str,
) -> str:
    params = _record_params(record)
    value = row.get(
        "adjustment_policy",
        metadata.get("adjustment_policy", params.get("adjustment_policy", default)),
    )
    if value is None or value == "":
        raise CanonicalSchemaError("schema_mismatch: missing adjustment_policy")
    return str(value)


def _symbol_value(row: Mapping[str, Any]) -> str:
    if row.get("ts_code") not in (None, ""):
        return _string_value(row, "ts_code").strip().upper()
    return _string_value(row, "symbol").strip().upper()


def _canonical_rows(
    record: Mapping[str, Any],
    metadata: Mapping[str, Any],
    raw_rows: list[dict[str, Any]],
    adj_factor_lookup: Mapping[tuple[str, str], tuple[float, str]] | None = None,
) -> tuple[list[dict[str, Any]], bool]:
    canonical_rows: list[dict[str, Any]] = []
    lineage_filled = False
    run_id = str(record.get("run_id") or "")
    source = str(record.get("source") or "")
    source_interface = str(record.get("interface") or "")
    raw_checksum = str(record.get("raw_checksum") or "")
    policies: set[str] = set()
    for index, row in enumerate(raw_rows):
        missing = [field for field in ("trade_date", "close") if field not in row]
        if "symbol" not in row and "ts_code" not in row:
            missing.append("symbol")
        if missing:
            raise CanonicalSchemaError(f"raw 第 {index + 1} 行缺少字段: {','.join(missing)}")
        if row.get("source") is not None and str(row["source"]) != source:
            raise ManifestLineageError("raw source 与 manifest source 不一致")
        source_run_id = row.get("source_run_id")
        if source_run_id is None:
            source_run_id = metadata.get("run_id") or run_id
            lineage_filled = True
        if str(source_run_id) != run_id:
            raise ManifestLineageError("raw source_run_id 与 manifest run_id 不一致")
        trade_date = _parse_date(row["trade_date"])
        symbol = _symbol_value(row)
        close = _float_value(row, "close")
        assert close is not None
        open_price = _float_value(row, "open", nullable=True)
        high = _float_value(row, "high", nullable=True)
        low = _float_value(row, "low", nullable=True)
        open_price = close if open_price is None else open_price
        high = close if high is None else high
        low = close if low is None else low
        adjustment_policy = _adjustment_policy(record, metadata, row, default="none")
        policies.add(adjustment_policy)
        joined = adj_factor_lookup.get((trade_date, symbol)) if adj_factor_lookup is not None else None
        adj_factor = row.get("adj_factor")
        if adj_factor is None and joined is not None:
            adj_factor_value, factor_policy = joined
            if factor_policy != adjustment_policy:
                raise CanonicalSchemaError(ADJUSTMENT_POLICY_CONFLICT)
        elif adj_factor is None and adjustment_policy == "none":
            adj_factor_value = 1.0
        elif adj_factor is None:
            raise CanonicalSchemaError("schema_mismatch: missing adj_factor")
        else:
            adj_factor_value = float(adj_factor)
            if joined is not None:
                joined_factor, factor_policy = joined
                if joined_factor != adj_factor_value or factor_policy != adjustment_policy:
                    raise CanonicalSchemaError(ADJUSTMENT_POLICY_CONFLICT)
        adjusted_open = float(row.get("adjusted_open", open_price * adj_factor_value))
        adjusted_high = float(row.get("adjusted_high", high * adj_factor_value))
        adjusted_low = float(row.get("adjusted_low", low * adj_factor_value))
        adjusted_close = float(row.get("adjusted_close", close * adj_factor_value))
        canonical_rows.append(
            {
                "trade_date": trade_date,
                "symbol": symbol,
                "open": open_price,
                "high": high,
                "low": low,
                "close": close,
                "adj_factor": adj_factor_value,
                "adjusted_open": adjusted_open,
                "adjusted_high": adjusted_high,
                "adjusted_low": adjusted_low,
                "adjusted_close": adjusted_close,
                "adjustment_policy": adjustment_policy,
                "source": source,
                "source_interface": source_interface,
                "source_run_id": run_id,
                "schema_version": SCHEMA_VERSION,
                "available_at": _available_at_value(row, source, source_interface, trade_date),
                "available_at_rule": _available_at_rule_value(
                    row,
                    AVAILABLE_AT_RULE_DAILY_CLOSE_FACT,
                ),
                "lineage_raw_checksum": raw_checksum,
            }
        )
    if len(policies) > 1:
        raise CanonicalSchemaError(ADJUSTMENT_POLICY_CONFLICT)
    return canonical_rows, lineage_filled


def _normalize_adj_factor_rows(
    record: Mapping[str, Any],
    metadata: Mapping[str, Any],
    raw_rows: list[dict[str, Any]],
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    policies: set[str] = set()
    source = _lineage(record, "source")
    source_interface = _lineage(record, "interface")
    run_id = _lineage(record, "run_id")
    raw_checksum = _lineage(record, "raw_checksum")
    for row in raw_rows:
        trade_date = _parse_date(row.get("trade_date"))
        policy = _adjustment_policy(record, metadata, row, default="qfq")
        policies.add(policy)
        rows.append(
            {
                "trade_date": trade_date,
                "symbol": _symbol_value(row),
                "adj_factor": _float_value(row, "adj_factor"),
                "adjustment_policy": policy,
                "source": source,
                "source_interface": source_interface,
                "source_run_id": run_id,
                "available_at": _daily_available_at_value(row, record, trade_date),
                "available_at_rule": _available_at_rule_value(
                    row,
                    AVAILABLE_AT_RULE_DAILY_CLOSE_FACT,
                ),
                "schema_version": SCHEMA_VERSION,
                "lineage_raw_checksum": raw_checksum,
            }
        )
    if len(policies) > 1:
        raise CanonicalSchemaError(ADJUSTMENT_POLICY_CONFLICT)
    frame = pd.DataFrame(rows, columns=CANONICAL_ADJ_FACTOR_COLUMNS)
    _assert_no_duplicate(frame, ("trade_date", "symbol"))
    return frame.sort_values(["trade_date", "symbol"]).reset_index(drop=True)


def _adj_factor_frame(
    record: Mapping[str, Any],
    metadata: Mapping[str, Any],
    raw_rows: list[dict[str, Any]],
) -> pd.DataFrame:
    frame = _normalize_adj_factor_rows(record, metadata, raw_rows)
    return frame[["trade_date", "symbol", "adj_factor", "adjustment_policy"]]


def _load_adj_factor_lookup(
    layout: LakeLayout,
    records: list[dict[str, Any]],
) -> dict[tuple[str, str], tuple[float, str]]:
    frames: list[pd.DataFrame] = []
    for record in records:
        raw_path = _resolve_raw_path(record.get("raw_path"), layout)
        metadata, raw_rows = _read_raw_jsonl(raw_path)
        _verify_raw(record, raw_path, raw_rows)
        frames.append(_adj_factor_frame(record, metadata, raw_rows))
    if not frames:
        return {}
    frame = pd.concat(frames, ignore_index=True)
    _assert_no_duplicate(frame, ("trade_date", "symbol"))
    policies = set(str(item) for item in frame["adjustment_policy"].unique())
    if len(policies) > 1:
        raise CanonicalSchemaError(ADJUSTMENT_POLICY_CONFLICT)
    return {
        (str(row.trade_date), str(row.symbol)): (float(row.adj_factor), str(row.adjustment_policy))
        for row in frame.itertuples(index=False)
    }


def _canonical_path(layout: LakeLayout, dataset: str, run_id: str, batch_id: str) -> Path:
    return (
        layout.canonical_dataset_root(dataset, SCHEMA_VERSION)
        / f"run_id={run_id}"
        / f"part-{batch_id}.parquet"
    )


def _write_parquet_atomic(frame: pd.DataFrame, path: Path) -> None:
    tmp_path = path.with_name(path.name + ".tmp")
    ensure_parent_dirs_for_write(tmp_path)
    frame.to_parquet(tmp_path, index=False)
    with tmp_path.open("rb") as fh:
        os.fsync(fh.fileno())
    tmp_path.replace(path)


def _normalize_hs300_rows(
    record: Mapping[str, Any],
    raw_rows: list[dict[str, Any]],
) -> pd.DataFrame:
    params = record.get("params")
    params = params if isinstance(params, Mapping) else {}
    expected_code = str(params.get("index_code", "399300.SZ")).strip().upper()
    rows: list[dict[str, Any]] = []
    for row in raw_rows:
        index_code = _string_value(row, "ts_code").strip().upper()
        if index_code != expected_code:
            raise CanonicalSchemaError("schema_mismatch: index_code")
        trade_date = _parse_date(row.get("trade_date"))
        pre_close = _float_value(row, "pre_close", nullable=True)
        pct_chg = _float_value(row, "pct_chg", nullable=True)
        if pre_close is None and pct_chg is None:
            raise CanonicalSchemaError("schema_mismatch: require pre_close or pct_chg")
        rows.append(
            {
                "trade_date": trade_date,
                "index_code": index_code,
                "close": _float_value(row, "close"),
                "pre_close": pre_close,
                "pct_chg": pct_chg,
                "open": _float_value(row, "open", nullable=True),
                "high": _float_value(row, "high", nullable=True),
                "low": _float_value(row, "low", nullable=True),
                "volume": _float_value(row, "vol", nullable=True),
                "amount": _float_value(row, "amount", nullable=True),
                "benchmark_kind": str(params.get("benchmark_kind", "price_index")),
                "source": _lineage(record, "source"),
                "source_interface": _lineage(record, "interface"),
                "source_run_id": _lineage(record, "run_id"),
                "schema_version": SCHEMA_VERSION,
                "available_at": str(row.get("available_at") or _next_available_at(trade_date)),
                "available_at_rule": _available_at_rule_value(
                    row,
                    AVAILABLE_AT_RULE_DAILY_CLOSE_FACT,
                ),
                "lineage_raw_checksum": _lineage(record, "raw_checksum"),
            }
        )
    frame = pd.DataFrame(rows, columns=CANONICAL_HS300_INDEX_COLUMNS)
    _assert_no_duplicate(frame, ("trade_date", "index_code"))
    return frame.sort_values(["trade_date", "index_code"]).reset_index(drop=True)


def _normalize_trade_calendar_rows(
    record: Mapping[str, Any],
    raw_rows: list[dict[str, Any]],
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for row in raw_rows:
        trade_date = _parse_date(row.get("cal_date", row.get("trade_date")))
        explicit_available_at = row.get("available_at") not in (None, "")
        if explicit_available_at:
            available_at = str(row["available_at"])
            default_available_at_rule = AVAILABLE_AT_RULE_EXPLICIT_TIMESTAMP
        elif _lineage(record, "source") == SOURCE_TUSHARE and _lineage(record, "interface") == INTERFACE_TRADE_CALENDAR_DAILY:
            available_at = _timestamp_at(trade_date, "00:00:00")
            default_available_at_rule = AVAILABLE_AT_RULE_CALENDAR_KNOWN
        else:
            available_at = str(record.get("finished_at") or "")
            default_available_at_rule = AVAILABLE_AT_RULE_DATE_ONLY_NEXT_OPEN
        rows.append(
            {
                "trade_date": trade_date,
                "exchange": str(row.get("exchange", "SSE")).upper(),
                "is_open": bool(int(row.get("is_open", 0))),
                "pretrade_date": _parse_date(row["pretrade_date"]) if row.get("pretrade_date") else None,
                "source": _lineage(record, "source"),
                "source_interface": _lineage(record, "interface"),
                "source_run_id": _lineage(record, "run_id"),
                "available_at": available_at,
                "available_at_rule": _available_at_rule_value(row, default_available_at_rule),
                "schema_version": SCHEMA_VERSION,
                "lineage_raw_checksum": _lineage(record, "raw_checksum"),
            }
        )
    frame = pd.DataFrame(rows, columns=CANONICAL_TRADE_CALENDAR_COLUMNS)
    _assert_no_duplicate(frame, ("trade_date", "exchange"))
    return frame.sort_values(["trade_date", "exchange"]).reset_index(drop=True)


def _normalize_index_weights_rows(
    record: Mapping[str, Any],
    raw_rows: list[dict[str, Any]],
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    source = _lineage(record, "source")
    source_interface = _lineage(record, "interface")
    is_tushare_index_weight = _is_tushare_index_weight_record(record)
    for row in raw_rows:
        trade_date = _parse_date(row.get("trade_date"))
        available_date = _parse_date(row.get("available_date", trade_date))
        effective_date = _parse_date(row.get("effective_date", trade_date))
        available_at = row.get("available_at")
        explicit_available_at = available_at not in (None, "")
        derived_available_at = False
        if not available_at and is_tushare_index_weight:
            available_at = _timestamp_at(effective_date, "16:00:00")
            derived_available_at = True
        elif not available_at:
            available_at = record.get("finished_at")
        if not available_at:
            raise CanonicalSchemaError("schema_mismatch: missing available_at")
        pit_status = str(
            row.get(
                "pit_status",
                PIT_STATUS_AVAILABLE
                if explicit_available_at or derived_available_at
                else PIT_STATUS_INCOMPLETE,
            )
        )
        readiness_status = str(
            row.get(
                "readiness_status",
                READINESS_STATUS_AVAILABLE
                if pit_status == PIT_STATUS_AVAILABLE
                else READINESS_STATUS_PIT_INCOMPLETE,
            )
        )
        rows.append(
            {
                "trade_date": trade_date,
                "index_code": _string_value(row, "index_code").strip().upper(),
                "con_code": _string_value(row, "con_code").strip().upper(),
                "weight": _float_value(row, "weight"),
                "effective_date": effective_date,
                "available_date": available_date,
                "available_at": str(available_at),
                "available_at_rule": _available_at_rule_value(
                    row,
                    AVAILABLE_AT_RULE_EXPLICIT_TIMESTAMP
                    if explicit_available_at
                    else AVAILABLE_AT_RULE_TUSHARE_INDEX_WEIGHT_EFFECTIVE_CLOSE
                    if derived_available_at
                    else AVAILABLE_AT_RULE_DATE_ONLY_NEXT_OPEN,
                ),
                "pit_status": pit_status,
                "readiness_status": readiness_status,
                "source": source,
                "source_interface": source_interface,
                "source_run_id": _lineage(record, "run_id"),
                "schema_version": SCHEMA_VERSION,
                "lineage_raw_checksum": _lineage(record, "raw_checksum"),
            }
        )
    frame = pd.DataFrame(rows, columns=CANONICAL_INDEX_WEIGHTS_COLUMNS)
    _assert_no_duplicate(frame, ("trade_date", "index_code", "con_code"))
    return frame.sort_values(["trade_date", "index_code", "con_code"]).reset_index(drop=True)


def _normalize_index_members_rows(
    record: Mapping[str, Any],
    raw_rows: list[dict[str, Any]],
) -> pd.DataFrame:
    params = _record_params(record)
    expected_index_code = str(params.get("index_code", "399300.SZ")).strip().upper()
    rows: list[dict[str, Any]] = []
    source = _lineage(record, "source")
    source_interface = _lineage(record, "interface")
    derived_from_index_weight = _is_tushare_index_weight_record(record)
    for row in raw_rows:
        index_code = str(row.get("index_code", expected_index_code)).strip().upper()
        con_code = _string_value(row, "con_code").strip().upper()
        in_date = _optional_date(row.get("in_date"))
        out_date = _optional_date(row.get("out_date"))
        effective_date = _first_date(
            row.get("effective_date"),
            row.get("in_date"),
            row.get("trade_date"),
            params.get("start_date"),
        )
        trade_date = _optional_date(row.get("trade_date")) or effective_date
        available_date = _optional_date(row.get("available_date")) or trade_date
        explicit_available_at = row.get("available_at") not in (None, "")
        derived_available_at = False
        if row.get("available_at") not in (None, ""):
            available_at = str(row.get("available_at"))
        elif derived_from_index_weight:
            available_at = _timestamp_at(effective_date, "16:00:00")
            derived_available_at = True
        else:
            available_at = str(record.get("finished_at") or "")
        if not available_at:
            raise CanonicalSchemaError("schema_mismatch: missing available_at")
        is_pit_universe = _bool_value(
            row.get("is_pit_universe"),
            default=derived_from_index_weight,
        )
        pit_status = str(
            row.get(
                "pit_status",
                PIT_STATUS_AVAILABLE
                if (explicit_available_at or derived_available_at) and is_pit_universe
                else PIT_STATUS_INCOMPLETE,
            )
        )
        if not is_pit_universe and pit_status == PIT_STATUS_AVAILABLE:
            pit_status = PIT_STATUS_INCOMPLETE
        readiness_status = str(
            row.get(
                "readiness_status",
                READINESS_STATUS_AVAILABLE
                if pit_status == PIT_STATUS_AVAILABLE
                else READINESS_STATUS_PIT_INCOMPLETE,
            )
        )
        rows.append(
            {
                "trade_date": trade_date,
                "index_code": index_code,
                "con_code": con_code,
                "in_date": in_date,
                "out_date": out_date,
                "is_member": _bool_value(row.get("is_member"), default=True),
                "effective_date": effective_date,
                "available_date": available_date,
                "available_at": available_at,
                "available_at_rule": _available_at_rule_value(
                    row,
                    AVAILABLE_AT_RULE_EXPLICIT_TIMESTAMP
                    if explicit_available_at
                    else AVAILABLE_AT_RULE_TUSHARE_INDEX_WEIGHT_EFFECTIVE_CLOSE
                    if derived_available_at
                    else AVAILABLE_AT_RULE_DATE_ONLY_NEXT_OPEN,
                ),
                "is_pit_universe": is_pit_universe,
                "pit_status": pit_status,
                "readiness_status": readiness_status,
                "source": source,
                "source_interface": source_interface,
                "source_run_id": _lineage(record, "run_id"),
                "schema_version": SCHEMA_VERSION,
                "lineage_raw_checksum": _lineage(record, "raw_checksum"),
                "derived_from": str(row.get("derived_from") or ("index_weight" if derived_from_index_weight else "")),
            }
        )
    frame = pd.DataFrame(rows, columns=CANONICAL_INDEX_MEMBERS_COLUMNS)
    _assert_no_duplicate(frame, ("trade_date", "index_code", "con_code"))
    return frame.sort_values(["trade_date", "index_code", "con_code"]).reset_index(drop=True)


def _normalize_stock_basic_rows(
    record: Mapping[str, Any],
    raw_rows: list[dict[str, Any]],
) -> pd.DataFrame:
    params = _record_params(record)
    rows: list[dict[str, Any]] = []
    source = _lineage(record, "source")
    source_interface = _lineage(record, "interface")
    is_tushare_stock_basic = source == SOURCE_TUSHARE and source_interface == INTERFACE_STOCK_BASIC_SNAPSHOT
    for row in raw_rows:
        symbol = _symbol_value(row)
        list_date = _optional_date(row.get("list_date"))
        snapshot_date = _optional_date(params.get("snapshot_date")) or _optional_date(params.get("trade_date"))
        if list_date and snapshot_date and list_date > snapshot_date:
            continue
        raw_delist_date = _optional_date(row.get("delist_date"))
        delist_date = raw_delist_date if raw_delist_date and snapshot_date and raw_delist_date <= snapshot_date else ""
        available_date = _optional_date(row.get("available_date")) or snapshot_date or _optional_date(record.get("finished_at"))
        effective_date = _optional_date(row.get("effective_date")) or list_date or available_date
        if not effective_date:
            raise CanonicalSchemaError("invalid_date")
        if not available_date:
            raise CanonicalSchemaError("invalid_date")
        derived_available_at = False
        if row.get("available_at") not in (None, ""):
            available_at = str(row.get("available_at"))
        elif is_tushare_stock_basic:
            available_at = _timestamp_at(effective_date, "00:00:00")
            derived_available_at = True
        else:
            available_at = str(record.get("finished_at") or "")
        if not available_at:
            raise CanonicalSchemaError("schema_mismatch: missing available_at")
        pit_status = str(
            row.get(
                "pit_status",
                PIT_STATUS_AVAILABLE if is_tushare_stock_basic else PIT_STATUS_NON_PIT_SNAPSHOT,
            )
        )
        readiness_status = str(
            row.get(
                "readiness_status",
                READINESS_STATUS_AVAILABLE
                if pit_status == PIT_STATUS_AVAILABLE
                else READINESS_STATUS_NON_PIT_SNAPSHOT,
            )
        )
        rows.append(
            {
                "symbol": symbol,
                "name": _string_value(row, "name"),
                "market": _optional_string(row, "market"),
                "list_status": str(row.get("list_status", row.get("status", ""))),
                "list_date": list_date,
                "delist_date": delist_date,
                "effective_date": effective_date,
                "available_date": available_date,
                "available_at": available_at,
                "available_at_rule": _available_at_rule_value(
                    row,
                    AVAILABLE_AT_RULE_EXPLICIT_TIMESTAMP
                    if row.get("available_at") not in (None, "")
                    else AVAILABLE_AT_RULE_TUSHARE_STOCK_BASIC_LIST_DATE
                    if derived_available_at
                    else AVAILABLE_AT_RULE_DATE_ONLY_NEXT_OPEN,
                ),
                "pit_status": pit_status,
                "readiness_status": readiness_status,
                "source": source,
                "source_interface": source_interface,
                "source_run_id": _lineage(record, "run_id"),
                "schema_version": SCHEMA_VERSION,
                "lineage_raw_checksum": _lineage(record, "raw_checksum"),
            }
        )
    frame = pd.DataFrame(rows, columns=CANONICAL_STOCK_BASIC_COLUMNS)
    _assert_no_duplicate(frame, ("symbol",))
    return frame.sort_values(["symbol"]).reset_index(drop=True)


def _normalize_trade_status_rows(
    record: Mapping[str, Any],
    raw_rows: list[dict[str, Any]],
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    source = _lineage(record, "source")
    source_interface = _lineage(record, "interface")
    for row in raw_rows:
        trade_date = _parse_date(row.get("trade_date"))
        available_at = row.get("available_at")
        derived_available_at = False
        if not available_at and source == SOURCE_TUSHARE and source_interface == INTERFACE_TRADE_STATUS_DAILY:
            available_at = _timestamp_at(trade_date, "09:30:00")
            derived_available_at = True
        rows.append(
            {
                "trade_date": trade_date,
                "symbol": _symbol_value(row),
                "is_tradable": _bool_value(row.get("is_tradable"), default=True),
                "is_suspended": _bool_value(row.get("is_suspended"), default=False),
                "is_st": _bool_value(row.get("is_st"), default=False),
                "status_reason": _optional_string(row, "status_reason"),
                "source": source,
                "source_interface": source_interface,
                "source_run_id": _lineage(record, "run_id"),
                "available_at": str(available_at) if available_at not in (None, "") else _string_value(row, "available_at"),
                "available_at_rule": _available_at_rule_value(
                    row,
                    AVAILABLE_AT_RULE_TUSHARE_SUSPEND_D_0930 if derived_available_at else AVAILABLE_AT_RULE_EXPLICIT_TIMESTAMP,
                ),
                "schema_version": SCHEMA_VERSION,
                "lineage_raw_checksum": _lineage(record, "raw_checksum"),
            }
        )
    frame = pd.DataFrame(rows, columns=CANONICAL_TRADE_STATUS_COLUMNS)
    _assert_no_duplicate(frame, ("trade_date", "symbol"))
    return frame.sort_values(["trade_date", "symbol"]).reset_index(drop=True)


def _normalize_prices_limit_rows(
    record: Mapping[str, Any],
    raw_rows: list[dict[str, Any]],
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    source = _lineage(record, "source")
    source_interface = _lineage(record, "interface")
    for row in raw_rows:
        trade_date = _parse_date(row.get("trade_date"))
        available_at = row.get("available_at")
        derived_available_at = False
        if not available_at and source == SOURCE_TUSHARE and source_interface == INTERFACE_PRICES_LIMIT_DAILY:
            available_at = _timestamp_at(trade_date, "08:40:00")
            derived_available_at = True
        rows.append(
            {
                "trade_date": trade_date,
                "symbol": _symbol_value(row),
                "limit_up": _float_value(row, "limit_up"),
                "limit_down": _float_value(row, "limit_down"),
                "source": source,
                "source_interface": source_interface,
                "source_run_id": _lineage(record, "run_id"),
                "available_at": str(available_at) if available_at not in (None, "") else _string_value(row, "available_at"),
                "available_at_rule": _available_at_rule_value(
                    row,
                    AVAILABLE_AT_RULE_TUSHARE_STK_LIMIT_0840 if derived_available_at else AVAILABLE_AT_RULE_EXPLICIT_TIMESTAMP,
                ),
                "schema_version": SCHEMA_VERSION,
                "lineage_raw_checksum": _lineage(record, "raw_checksum"),
            }
        )
    frame = pd.DataFrame(rows, columns=CANONICAL_PRICES_LIMIT_COLUMNS)
    _assert_no_duplicate(frame, ("trade_date", "symbol"))
    return frame.sort_values(["trade_date", "symbol"]).reset_index(drop=True)


def _normalize_events_rows(
    record: Mapping[str, Any],
    raw_rows: list[dict[str, Any]],
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    source = _lineage(record, "source")
    source_interface = _lineage(record, "interface")
    for row in raw_rows:
        event_date = _parse_date(row.get("event_date"))
        payload = row.get("payload", "")
        if isinstance(payload, (dict, list)):
            payload = json.dumps(payload, ensure_ascii=False, sort_keys=True)
        available_at = row.get("available_at")
        derived_available_at = False
        if not available_at and source == SOURCE_TUSHARE and source_interface == INTERFACE_EVENTS_DISCLOSURE:
            available_at = _timestamp_at(event_date, "09:20:00")
            derived_available_at = True
        rows.append(
            {
                "symbol": _symbol_value(row),
                "event_type": _string_value(row, "event_type"),
                "event_date": event_date,
                "available_at": str(available_at) if available_at not in (None, "") else _string_value(row, "available_at"),
                "available_at_rule": _available_at_rule_value(
                    row,
                    AVAILABLE_AT_RULE_TUSHARE_STOCK_ST_0920 if derived_available_at else AVAILABLE_AT_RULE_EXPLICIT_TIMESTAMP,
                ),
                "payload": str(payload),
                "source": source,
                "source_interface": source_interface,
                "source_run_id": _lineage(record, "run_id"),
                "schema_version": SCHEMA_VERSION,
                "lineage_raw_checksum": _lineage(record, "raw_checksum"),
            }
        )
    frame = pd.DataFrame(rows, columns=CANONICAL_EVENTS_COLUMNS)
    _assert_no_duplicate(frame, ("symbol", "event_type", "event_date", "available_at"))
    return frame.sort_values(["symbol", "event_date", "event_type"]).reset_index(drop=True)


def _frame_for_dataset(
    dataset: str,
    record: Mapping[str, Any],
    metadata: Mapping[str, Any],
    raw_rows: list[dict[str, Any]],
    adj_factor_lookup: Mapping[tuple[str, str], tuple[float, str]] | None = None,
) -> tuple[pd.DataFrame, bool]:
    if dataset == DATASET_PRICES:
        rows, filled = _canonical_rows(record, metadata, raw_rows, adj_factor_lookup)
        frame = pd.DataFrame(rows, columns=CR005_CANONICAL_PRICES_COLUMNS)
        _assert_no_duplicate(frame, ("trade_date", "symbol"))
        return frame.sort_values(["trade_date", "symbol"]).reset_index(drop=True), filled
    if dataset == DATASET_ADJ_FACTOR:
        return _normalize_adj_factor_rows(record, metadata, raw_rows), False
    if dataset == DATASET_HS300_INDEX:
        return _normalize_hs300_rows(record, raw_rows), False
    if dataset == DATASET_TRADE_CALENDAR:
        return _normalize_trade_calendar_rows(record, raw_rows), False
    if dataset == DATASET_INDEX_MEMBERS:
        return _normalize_index_members_rows(record, raw_rows), False
    if dataset == DATASET_INDEX_WEIGHTS:
        return _normalize_index_weights_rows(record, raw_rows), False
    if dataset == DATASET_STOCK_BASIC:
        return _normalize_stock_basic_rows(record, raw_rows), False
    if dataset == DATASET_TRADE_STATUS:
        return _normalize_trade_status_rows(record, raw_rows), False
    if dataset == DATASET_PRICES_LIMIT:
        return _normalize_prices_limit_rows(record, raw_rows), False
    if dataset == DATASET_EVENTS:
        return _normalize_events_rows(record, raw_rows), False
    raise DatasetMappingError(f"不支持的 dataset: {dataset}")


def normalize_run(
    manifest_path: str | Path,
    lake_root: str | Path,
    dataset: str = DATASET_PRICES,
    run_id: str | None = None,
    thresholds: object = None,
) -> NormalizationResult:
    del thresholds
    if dataset not in DATASET_SCHEMA_REGISTRY:
        raise DatasetMappingError(f"不支持的 dataset: {dataset}")
    layout = LakeLayout(lake_root)
    records = _load_manifest_records(Path(manifest_path))
    skipped: dict[str, int] = {}
    success_records: list[dict[str, Any]] = []
    adj_factor_records: list[dict[str, Any]] = []
    for record in records:
        if run_id is not None and record.get("run_id") != run_id:
            continue
        status = str(record.get("status"))
        if status != "success":
            skipped[status] = skipped.get(status, 0) + 1
            continue
        mapped = map_raw_to_dataset(record)
        if mapped == dataset or _record_feeds_dataset(record, dataset):
            success_records.append(record)
        elif dataset == DATASET_PRICES and mapped == DATASET_ADJ_FACTOR:
            adj_factor_records.append(record)
    if not success_records:
        raise ManifestLineageError("manifest 中没有可标准化的 success 记录")

    canonical_paths: list[Path] = []
    total_rows = 0
    filled = False
    adj_factor_lookup = (
        _load_adj_factor_lookup(layout, adj_factor_records)
        if dataset == DATASET_PRICES and adj_factor_records
        else None
    )
    pending_writes: list[tuple[dict[str, Any], pd.DataFrame]] = []
    price_keys: set[tuple[str, str]] = set()
    for record in success_records:
        raw_path = _resolve_raw_path(record.get("raw_path"), layout)
        metadata, raw_rows = _read_raw_jsonl(raw_path)
        _verify_raw(record, raw_path, raw_rows)
        frame, row_filled = _frame_for_dataset(dataset, record, metadata, raw_rows, adj_factor_lookup)
        filled = filled or row_filled
        if dataset == DATASET_PRICES and adj_factor_lookup is not None:
            price_keys.update((str(row.trade_date), str(row.symbol)) for row in frame.itertuples(index=False))
        pending_writes.append((dict(record), frame))

    for record, frame in pending_writes:
        target = _canonical_path(
            layout,
            dataset,
            str(record["run_id"]),
            str(record["batch_id"]),
        )
        _write_parquet_atomic(frame, target)
        canonical_paths.append(target)
        total_rows += len(frame)

    result_run_id = str(success_records[0].get("run_id")) if success_records else run_id
    return NormalizationResult(
        dataset=dataset,
        run_id=result_run_id,
        canonical_paths=tuple(canonical_paths),
        row_count=total_rows,
        manifest_records=tuple(dict(item) for item in [*success_records, *adj_factor_records]),
        skipped_status_counts=skipped,
        lineage_filled_from_manifest=filled,
    )


__all__ = [
    "ADJUSTMENT_POLICY_CONFLICT",
    "CanonicalSchemaError",
    "DatasetMappingError",
    "ManifestLineageError",
    "NormalizationResult",
    "load_manifest_success_records",
    "map_raw_to_dataset",
    "CANDIDATE_UNPUBLISHED",
    "NORMALIZE_MANIFEST_INCOMPLETE",
    "NormalizeCandidate",
    "normalize_run",
    "normalize_p0_candidate",
    "REPLAY_SOURCE_MISSING",
    "ReplayRequest",
    "ReplayResult",
    "replay_p0_candidate",
]
