"""CR014-S06 增量刷新与最近 N 交易日回补计划合同。"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field, is_dataclass
from datetime import date
from typing import Any, Iterable, Mapping

from .contracts import CR014_FORBIDDEN_OPERATION_COUNTERS, SCHEMA_VERSION

INCREMENTAL_ACTION_SKIP = "skip"
INCREMENTAL_ACTION_RETRY = "retry"
INCREMENTAL_ACTION_PLAN_NEW = "plan_new"
INCREMENTAL_ACTION_BLOCKED = "blocked"


def cr014_s06_zero_permission_counters() -> dict[str, int]:
    """返回 S06 合同允许的零副作用计数。"""

    counters = dict(CR014_FORBIDDEN_OPERATION_COUNTERS)
    counters.update(
        {
            "provider_fetches": 0,
            "lake_writes": 0,
            "credential_reads": 0,
            "raw_writes": 0,
            "manifest_writes": 0,
            "current_pointer_changes": 0,
            "publish_count": 0,
            "delete_count": 0,
            "archive_count": 0,
            "migrate_count": 0,
        }
    )
    return counters


@dataclass(frozen=True, slots=True)
class AffectedPartition:
    dataset: str
    schema_version: str
    trade_date: str
    exchange: str | None = None
    board: str | None = None

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        return {key: value for key, value in payload.items() if value is not None}


@dataclass(frozen=True, slots=True)
class IncrementalBatchAction:
    batch_id: str
    action: str
    dataset: str
    trade_date: str
    reason: str
    partition_count: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class IncrementalRefreshPlan:
    dataset: str
    schema_version: str
    as_of_trade_date: str
    current_pointer_ref: str
    recent_n: int
    recent_trade_dates: tuple[str, ...]
    affected_partitions: tuple[AffectedPartition, ...]
    batch_actions: tuple[IncrementalBatchAction, ...]
    idempotency_key: str
    permission_counters: dict[str, int]
    status: str = "planned"
    provider_fetches: int = 0
    lake_writes: int = 0
    credential_reads: int = 0
    details: tuple[dict[str, Any], ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "dataset": self.dataset,
            "schema_version": self.schema_version,
            "as_of_trade_date": self.as_of_trade_date,
            "current_pointer_ref": self.current_pointer_ref,
            "recent_n": self.recent_n,
            "recent_trade_dates": list(self.recent_trade_dates),
            "affected_partitions": [item.to_dict() for item in self.affected_partitions],
            "batch_actions": [item.to_dict() for item in self.batch_actions],
            "idempotency_key": self.idempotency_key,
            "permission_counters": dict(self.permission_counters),
            "provider_fetches": self.provider_fetches,
            "lake_writes": self.lake_writes,
            "credential_reads": self.credential_reads,
            "details": [dict(item) for item in self.details],
        }


def _payload(value: Any) -> dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, Mapping):
        return dict(value)
    to_dict = getattr(value, "to_dict", None)
    if callable(to_dict):
        return dict(to_dict())
    if is_dataclass(value):
        return asdict(value)
    if hasattr(value, "__dict__"):
        return dict(vars(value))
    return {}


def _canonical_hash(value: Any) -> str:
    text = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _normalise_trade_date(value: Any) -> str:
    if isinstance(value, date):
        return value.isoformat()
    text = str(value).strip()
    if len(text) == 8 and text.isdigit():
        return f"{text[:4]}-{text[4:6]}-{text[6:]}"
    if len(text) >= 10 and text[4] == "-" and text[7] == "-":
        return text[:10]
    return text


def _calendar_open_dates(calendar: Iterable[Any]) -> tuple[str, ...]:
    dates: set[str] = set()
    for item in calendar:
        if isinstance(item, Mapping):
            raw_date = item.get("trade_date") or item.get("date")
            is_open = item.get("is_open", item.get("open", True))
            if raw_date is None or is_open in (False, 0, "0", "false", "False"):
                continue
            dates.add(_normalise_trade_date(raw_date))
        else:
            dates.add(_normalise_trade_date(item))
    return tuple(sorted(dates))


def _recent_trade_dates(
    calendar: Iterable[Any],
    *,
    as_of_trade_date: str,
    recent_n: int,
) -> tuple[str, ...]:
    if recent_n <= 0:
        return ()
    open_dates = [
        item for item in _calendar_open_dates(calendar) if not as_of_trade_date or item <= as_of_trade_date
    ]
    return tuple(open_dates[-recent_n:])


def _sequence_value(policy: Mapping[str, Any], plural_key: str, singular_key: str) -> tuple[str | None, ...]:
    value = policy.get(plural_key)
    if value is None:
        value = policy.get(singular_key)
    if value is None:
        return (None,)
    if isinstance(value, str):
        return (value,)
    values = tuple(str(item) for item in value)
    return values or (None,)


def _current_pointer_ref(current_pointer: Mapping[str, Any]) -> str:
    for key in (
        "catalog_pointer_path",
        "current_pointer_ref",
        "latest_manifest_run_id",
        "lineage_checksum",
        "published_path",
    ):
        value = current_pointer.get(key)
        if value is not None and str(value).strip():
            return str(value)
    dataset = current_pointer.get("dataset", "")
    schema_version = current_pointer.get("schema_version", SCHEMA_VERSION)
    coverage_end = current_pointer.get("coverage_end") or current_pointer.get("end_date") or ""
    return f"{dataset}:{schema_version}:{coverage_end}"


def _batch_ids(items: Iterable[Any]) -> set[str]:
    batch_ids: set[str] = set()
    for item in items:
        if isinstance(item, Mapping):
            batch_id = item.get("batch_id")
            if batch_id is None and item.get("dataset") and item.get("trade_date"):
                batch_id = f"{item['dataset']}:{_normalise_trade_date(item['trade_date'])}"
            if batch_id is not None:
                batch_ids.add(str(batch_id))
        else:
            batch_ids.add(str(item))
    return batch_ids


def plan_recent_backfill(
    affected_partitions: Iterable[AffectedPartition | Mapping[str, Any]],
    *,
    success_batches: Iterable[Any] = (),
    failed_batches: Iterable[Any] = (),
) -> tuple[IncrementalBatchAction, ...]:
    """按 affected partition 生成 skip / retry / plan_new 动作。"""

    success_ids = _batch_ids(success_batches)
    failed_ids = _batch_ids(failed_batches)
    grouped: dict[tuple[str, str], int] = {}
    for item in affected_partitions:
        payload = item.to_dict() if isinstance(item, AffectedPartition) else dict(item)
        dataset = str(payload.get("dataset") or "")
        trade_date = _normalise_trade_date(payload.get("trade_date") or "")
        grouped[(dataset, trade_date)] = grouped.get((dataset, trade_date), 0) + 1

    actions: list[IncrementalBatchAction] = []
    for dataset, trade_date in sorted(grouped):
        batch_id = f"{dataset}:{trade_date}"
        if batch_id in success_ids:
            action = INCREMENTAL_ACTION_SKIP
            reason = "already_successful"
        elif batch_id in failed_ids:
            action = INCREMENTAL_ACTION_RETRY
            reason = "previous_failed_batch"
        else:
            action = INCREMENTAL_ACTION_PLAN_NEW
            reason = "recent_trade_date_not_materialized"
        actions.append(
            IncrementalBatchAction(
                batch_id=batch_id,
                action=action,
                dataset=dataset,
                trade_date=trade_date,
                reason=reason,
                partition_count=grouped[(dataset, trade_date)],
            )
        )
    return tuple(actions)


def plan_incremental_refresh(
    current_pointer: Mapping[str, Any] | object,
    calendar: Iterable[Any],
    dataset_policy: Mapping[str, Any] | object,
    recent_n: int,
    *,
    success_batches: Iterable[Any] = (),
    failed_batches: Iterable[Any] = (),
) -> IncrementalRefreshPlan:
    """生成 CR014-S06 增量刷新 dry-run plan；不抓 provider，不写 lake。"""

    pointer = _payload(current_pointer)
    policy = _payload(dataset_policy)
    dataset = str(policy.get("dataset") or pointer.get("dataset") or "")
    schema_version = str(policy.get("schema_version") or pointer.get("schema_version") or SCHEMA_VERSION)
    calendar_dates = _calendar_open_dates(calendar)
    as_of_trade_date = _normalise_trade_date(
        policy.get("as_of_trade_date")
        or pointer.get("as_of_trade_date")
        or pointer.get("coverage_end")
        or pointer.get("end_date")
        or (calendar_dates[-1] if calendar_dates else "")
    )
    recent_trade_dates = _recent_trade_dates(
        calendar_dates,
        as_of_trade_date=as_of_trade_date,
        recent_n=recent_n,
    )
    exchanges = _sequence_value(policy, "exchanges", "exchange")
    boards = _sequence_value(policy, "boards", "board")
    affected: list[AffectedPartition] = []
    for trade_date in recent_trade_dates:
        for exchange in exchanges:
            for board in boards:
                affected.append(
                    AffectedPartition(
                        dataset=dataset,
                        schema_version=schema_version,
                        trade_date=trade_date,
                        exchange=exchange,
                        board=board,
                    )
                )
    batch_actions = plan_recent_backfill(
        affected,
        success_batches=success_batches,
        failed_batches=failed_batches,
    )
    pointer_ref = _current_pointer_ref(pointer)
    policy_hash = _canonical_hash(policy)
    idempotency_key = _canonical_hash(
        {
            "dataset": dataset,
            "schema_version": schema_version,
            "as_of_trade_date": as_of_trade_date,
            "current_pointer_ref": pointer_ref,
            "recent_n": recent_n,
            "dataset_policy_hash": policy_hash,
            "affected_partitions": [item.to_dict() for item in affected],
        }
    )
    details: list[dict[str, Any]] = []
    status = "planned"
    if not dataset or not recent_trade_dates:
        status = INCREMENTAL_ACTION_BLOCKED
        details.append(
            {
                "code": "incremental_plan_input_missing",
                "dataset_present": bool(dataset),
                "recent_trade_dates_present": bool(recent_trade_dates),
            }
        )
    return IncrementalRefreshPlan(
        dataset=dataset,
        schema_version=schema_version,
        as_of_trade_date=as_of_trade_date,
        current_pointer_ref=pointer_ref,
        recent_n=recent_n,
        recent_trade_dates=recent_trade_dates,
        affected_partitions=tuple(affected),
        batch_actions=batch_actions,
        idempotency_key=idempotency_key,
        permission_counters=cr014_s06_zero_permission_counters(),
        status=status,
        provider_fetches=0,
        lake_writes=0,
        credential_reads=0,
        details=tuple(details),
    )


__all__ = [
    "AffectedPartition",
    "INCREMENTAL_ACTION_BLOCKED",
    "INCREMENTAL_ACTION_PLAN_NEW",
    "INCREMENTAL_ACTION_RETRY",
    "INCREMENTAL_ACTION_SKIP",
    "IncrementalBatchAction",
    "IncrementalRefreshPlan",
    "cr014_s06_zero_permission_counters",
    "plan_incremental_refresh",
    "plan_recent_backfill",
]
