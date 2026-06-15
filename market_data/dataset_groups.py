"""CR018-S01 P0/P1 dataset group 与 claim matrix 合同。"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, is_dataclass
from typing import Any, Mapping, Sequence

from .contracts import (
    CR017_VIEW_ADJ_FACTOR,
    CR017_VIEW_PRICES_HFQ,
    CR017_VIEW_PRICES_QFQ,
    CR017_VIEW_PRICES_RAW,
    CR017_VIEW_RETURNS_ADJUSTED,
    DATASET_TRADE_CALENDAR,
    READINESS_STATUS_AVAILABLE,
    READINESS_STATUS_REQUIRED_MISSING,
)
from .release_scope import (
    CLAIM_PRODUCTION_CURRENT_TRUTH,
    FORBIDDEN_OPERATION_COUNTER_KEYS,
    ReleaseScopeResult,
    default_permission_counters,
    normalise_permission_counters,
)

PRIORITY_P0 = "P0"
PRIORITY_P1 = "P1"

DATASET_PIT_UNIVERSE = "pit_universe"
DATASET_LIFECYCLE_CODE_CHANGE = "lifecycle_code_change"
DATASET_TRADE_STATUS = "trade_status"
DATASET_PRICES_LIMIT_ST_SUSPEND = "prices_limit_st_suspend"
DATASET_BENCHMARK_GROUP = "benchmark_group"

DATASET_INDUSTRY_CLASSIFICATION = "industry_classification"
DATASET_MARKET_CAP_TOTAL = "market_cap_total"
DATASET_MARKET_CAP_FLOAT = "market_cap_float"
DATASET_BETA_STYLE_FACTORS = "beta_style_factors"
DATASET_ADV = "adv"
DATASET_TURNOVER_RATE = "turnover_rate"
DATASET_LIQUIDITY_CAPACITY = "liquidity_capacity"
DATASET_MARKET_IMPACT_COST = "market_impact_cost"

REASON_P0_REQUIRED_MISSING = "p0_required_missing"
REASON_P1_AUXILIARY_MISSING = "p1_auxiliary_missing"
REASON_UNREGISTERED_DATASET = "unregistered_dataset"
REASON_PERMISSION_COUNTER_VIOLATION = "permission_counter_violation"

CLAIM_INDUSTRY_NEUTRALIZED = "industry_neutralized"
CLAIM_MARKET_CAP_NEUTRALIZED = "market_cap_neutralized"
CLAIM_PURE_ALPHA = "pure_alpha"
CLAIM_CAPACITY_TRADABLE = "capacity_tradable"
CLAIM_SCALE_UP_READY = "scale_up_ready"
CLAIM_CAPITAL_AMPLIFICATION = "capital_amplification"
CLAIM_PUBLISH_READINESS = "publish_readiness"

P1_BLOCKED_CLAIMS: tuple[str, ...] = (
    CLAIM_INDUSTRY_NEUTRALIZED,
    CLAIM_MARKET_CAP_NEUTRALIZED,
    CLAIM_PURE_ALPHA,
    CLAIM_CAPACITY_TRADABLE,
    CLAIM_SCALE_UP_READY,
    CLAIM_CAPITAL_AMPLIFICATION,
)

AVAILABLE_STATUSES = {
    READINESS_STATUS_AVAILABLE,
    "pass",
    "published",
    "ready",
    "ok",
}


class DatasetGroupError(RuntimeError):
    """dataset group 合同错误。"""


@dataclass(frozen=True, slots=True)
class DatasetGroupEntry:
    dataset_id: str
    priority: str
    required_for_publish: bool
    required_layers: tuple[str, ...]
    blocks_core_release: bool
    blocked_claims_when_missing: tuple[str, ...] = ()
    description: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            **asdict(self),
            "required_layers": list(self.required_layers),
            "blocked_claims_when_missing": list(self.blocked_claims_when_missing),
        }


@dataclass(frozen=True, slots=True)
class ClaimMatrixResult:
    release_blocked: bool
    allowed_claims: tuple[dict[str, Any], ...]
    blocked_claims: tuple[dict[str, Any], ...]
    required_missing: tuple[dict[str, Any], ...]
    dataset_matrix: tuple[dict[str, Any], ...]
    unknown_datasets: tuple[str, ...] = ()
    permission_counters: dict[str, int] = field(default_factory=dict)
    error_codes: tuple[str, ...] = ()
    unknown_dataset_readiness_pass_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "release_blocked": self.release_blocked,
            "allowed_claims": [dict(item) for item in self.allowed_claims],
            "blocked_claims": [dict(item) for item in self.blocked_claims],
            "required_missing": [dict(item) for item in self.required_missing],
            "dataset_matrix": [dict(item) for item in self.dataset_matrix],
            "unknown_datasets": list(self.unknown_datasets),
            "permission_counters": dict(self.permission_counters),
            "error_codes": list(self.error_codes),
            "unknown_dataset_readiness_pass_count": self.unknown_dataset_readiness_pass_count,
        }


def _entry(
    dataset_id: str,
    priority: str,
    *,
    layers: tuple[str, ...],
    blocked_claims: tuple[str, ...] = (),
    description: str = "",
) -> DatasetGroupEntry:
    required_for_publish = priority == PRIORITY_P0
    return DatasetGroupEntry(
        dataset_id=dataset_id,
        priority=priority,
        required_for_publish=required_for_publish,
        required_layers=layers,
        blocks_core_release=required_for_publish,
        blocked_claims_when_missing=blocked_claims,
        description=description,
    )


P0_DATASET_GROUPS: tuple[DatasetGroupEntry, ...] = (
    _entry(CR017_VIEW_PRICES_RAW, PRIORITY_P0, layers=("raw", "manifest", "canonical", "quality", "catalog")),
    _entry(CR017_VIEW_ADJ_FACTOR, PRIORITY_P0, layers=("raw", "manifest", "canonical", "quality", "catalog")),
    _entry(CR017_VIEW_PRICES_QFQ, PRIORITY_P0, layers=("canonical", "gold_or_view", "quality", "catalog")),
    _entry(CR017_VIEW_PRICES_HFQ, PRIORITY_P0, layers=("canonical", "gold_or_view", "quality", "catalog")),
    _entry(CR017_VIEW_RETURNS_ADJUSTED, PRIORITY_P0, layers=("canonical", "gold_or_view", "quality", "catalog")),
    _entry(DATASET_TRADE_CALENDAR, PRIORITY_P0, layers=("raw", "manifest", "canonical", "quality", "catalog")),
    _entry(DATASET_PIT_UNIVERSE, PRIORITY_P0, layers=("raw", "manifest", "canonical", "quality", "catalog")),
    _entry(DATASET_LIFECYCLE_CODE_CHANGE, PRIORITY_P0, layers=("raw", "manifest", "canonical", "quality", "catalog")),
    _entry(DATASET_TRADE_STATUS, PRIORITY_P0, layers=("raw", "manifest", "canonical", "quality", "catalog")),
    _entry(DATASET_PRICES_LIMIT_ST_SUSPEND, PRIORITY_P0, layers=("raw", "manifest", "canonical", "quality", "catalog")),
    _entry(DATASET_BENCHMARK_GROUP, PRIORITY_P0, layers=("raw", "manifest", "canonical", "gold_or_view", "quality", "catalog")),
)

P1_DATASET_GROUPS: tuple[DatasetGroupEntry, ...] = (
    _entry(DATASET_INDUSTRY_CLASSIFICATION, PRIORITY_P1, layers=("raw", "manifest", "canonical", "quality", "catalog"), blocked_claims=(CLAIM_INDUSTRY_NEUTRALIZED, CLAIM_PURE_ALPHA)),
    _entry(DATASET_MARKET_CAP_TOTAL, PRIORITY_P1, layers=("raw", "manifest", "canonical", "quality", "catalog"), blocked_claims=(CLAIM_MARKET_CAP_NEUTRALIZED, CLAIM_PURE_ALPHA)),
    _entry(DATASET_MARKET_CAP_FLOAT, PRIORITY_P1, layers=("raw", "manifest", "canonical", "quality", "catalog"), blocked_claims=(CLAIM_MARKET_CAP_NEUTRALIZED, CLAIM_CAPACITY_TRADABLE)),
    _entry(DATASET_BETA_STYLE_FACTORS, PRIORITY_P1, layers=("raw", "manifest", "canonical", "quality", "catalog"), blocked_claims=(CLAIM_PURE_ALPHA,)),
    _entry(DATASET_ADV, PRIORITY_P1, layers=("raw", "manifest", "canonical", "quality", "catalog"), blocked_claims=(CLAIM_CAPACITY_TRADABLE, CLAIM_SCALE_UP_READY)),
    _entry(DATASET_TURNOVER_RATE, PRIORITY_P1, layers=("raw", "manifest", "canonical", "quality", "catalog"), blocked_claims=(CLAIM_CAPACITY_TRADABLE, CLAIM_SCALE_UP_READY)),
    _entry(DATASET_LIQUIDITY_CAPACITY, PRIORITY_P1, layers=("raw", "manifest", "canonical", "quality", "catalog"), blocked_claims=(CLAIM_CAPACITY_TRADABLE, CLAIM_SCALE_UP_READY, CLAIM_CAPITAL_AMPLIFICATION)),
    _entry(DATASET_MARKET_IMPACT_COST, PRIORITY_P1, layers=("raw", "manifest", "canonical", "quality", "catalog"), blocked_claims=(CLAIM_CAPACITY_TRADABLE, CLAIM_SCALE_UP_READY, CLAIM_CAPITAL_AMPLIFICATION)),
)

DATASET_GROUP_REGISTRY: dict[str, DatasetGroupEntry] = {
    entry.dataset_id: entry for entry in (*P0_DATASET_GROUPS, *P1_DATASET_GROUPS)
}


def list_dataset_groups(priority: str | None = None) -> tuple[DatasetGroupEntry, ...]:
    if priority is None:
        return tuple(DATASET_GROUP_REGISTRY.values())
    if priority not in {PRIORITY_P0, PRIORITY_P1}:
        return ()
    return tuple(entry for entry in DATASET_GROUP_REGISTRY.values() if entry.priority == priority)


def get_dataset_group_entry(dataset_id: str) -> DatasetGroupEntry:
    try:
        return DATASET_GROUP_REGISTRY[dataset_id]
    except KeyError as exc:
        raise DatasetGroupError(f"{REASON_UNREGISTERED_DATASET}: {dataset_id}") from exc


def required_for_publish_dataset_ids() -> tuple[str, ...]:
    return tuple(entry.dataset_id for entry in P0_DATASET_GROUPS)


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
    return {"readiness_status": str(value)}


def _readiness_status(value: Any) -> str:
    payload = _payload(value)
    return str(
        payload.get("readiness_status")
        or payload.get("status")
        or payload.get("publish_status")
        or READINESS_STATUS_REQUIRED_MISSING
    )


def _is_available(status: str) -> bool:
    return status in AVAILABLE_STATUSES


def _dedupe_rows(rows: Sequence[Mapping[str, Any]]) -> tuple[dict[str, Any], ...]:
    seen: set[tuple[str, str, str, str]] = set()
    output: list[dict[str, Any]] = []
    for row in rows:
        payload = dict(row)
        key = (
            str(payload.get("claim") or ""),
            str(payload.get("dataset_id") or ""),
            str(payload.get("reason_code") or ""),
            str(payload.get("priority") or ""),
        )
        if key in seen:
            continue
        seen.add(key)
        output.append(payload)
    return tuple(output)


def _dataset_matrix_row(entry: DatasetGroupEntry, status: str) -> dict[str, Any]:
    return {
        "dataset_id": entry.dataset_id,
        "priority": entry.priority,
        "readiness_status": status,
        "required_for_publish": entry.required_for_publish,
        "required_layers": list(entry.required_layers),
        "blocks_core_release": entry.blocks_core_release,
        "blocked_claims_when_missing": list(entry.blocked_claims_when_missing),
    }


def build_release_claim_matrix(
    dataset_readiness: Mapping[str, Any] | None = None,
    *,
    p1_available: bool | None = None,
    permission_counters: Mapping[str, Any] | None = None,
) -> ClaimMatrixResult:
    """构建 CR018 release allowed/blocked claim matrix；不触发 publish。"""

    readiness = {str(key): _readiness_status(value) for key, value in dict(dataset_readiness or {}).items()}
    if p1_available is not None:
        default_p1_status = READINESS_STATUS_AVAILABLE if p1_available else READINESS_STATUS_REQUIRED_MISSING
        for entry in P1_DATASET_GROUPS:
            readiness.setdefault(entry.dataset_id, default_p1_status)

    counters = normalise_permission_counters(permission_counters)
    counter_violation = any(counters.get(key, 0) != 0 for key in FORBIDDEN_OPERATION_COUNTER_KEYS)
    unknown_datasets = tuple(sorted(dataset for dataset in readiness if dataset not in DATASET_GROUP_REGISTRY))

    rows: list[dict[str, Any]] = []
    required_missing: list[dict[str, Any]] = []
    blocked: list[dict[str, Any]] = []
    error_codes: list[str] = []

    for entry in list_dataset_groups():
        status = readiness.get(entry.dataset_id, READINESS_STATUS_REQUIRED_MISSING)
        rows.append(_dataset_matrix_row(entry, status))
        if _is_available(status):
            continue
        if entry.priority == PRIORITY_P0:
            error_codes.append(REASON_P0_REQUIRED_MISSING)
            required_missing.append(
                {
                    "dataset_id": entry.dataset_id,
                    "priority": entry.priority,
                    "reason_code": REASON_P0_REQUIRED_MISSING,
                    "required_for_publish": True,
                    "readiness_status": status,
                }
            )
            blocked.append(
                {
                    "claim": CLAIM_PRODUCTION_CURRENT_TRUTH,
                    "dataset_id": entry.dataset_id,
                    "priority": entry.priority,
                    "reason_code": REASON_P0_REQUIRED_MISSING,
                }
            )
        else:
            for claim in entry.blocked_claims_when_missing:
                blocked.append(
                    {
                        "claim": claim,
                        "dataset_id": entry.dataset_id,
                        "priority": entry.priority,
                        "reason_code": REASON_P1_AUXILIARY_MISSING,
                        "readiness_status": status,
                    }
                )

    for dataset_id in unknown_datasets:
        error_codes.append(REASON_UNREGISTERED_DATASET)
        required_missing.append(
            {
                "dataset_id": dataset_id,
                "priority": "unknown",
                "reason_code": REASON_UNREGISTERED_DATASET,
                "required_for_publish": False,
                "readiness_status": readiness[dataset_id],
            }
        )
        blocked.append(
            {
                "claim": CLAIM_PUBLISH_READINESS,
                "dataset_id": dataset_id,
                "priority": "unknown",
                "reason_code": REASON_UNREGISTERED_DATASET,
            }
        )

    if counter_violation:
        error_codes.append(REASON_PERMISSION_COUNTER_VIOLATION)
        blocked.append(
            {
                "claim": CLAIM_PUBLISH_READINESS,
                "dataset_id": "permission_counters",
                "priority": "P0",
                "reason_code": REASON_PERMISSION_COUNTER_VIOLATION,
                "permission_counters": dict(counters),
            }
        )

    release_blocked = any(
        item["reason_code"] in {REASON_P0_REQUIRED_MISSING, REASON_UNREGISTERED_DATASET, REASON_PERMISSION_COUNTER_VIOLATION}
        for item in blocked
    )
    allowed = (
        (
            {
                "claim": CLAIM_PRODUCTION_CURRENT_TRUTH,
                "scope": "2015-01-05..latest_closed_trade_date",
                "required_for_publish_datasets": list(required_for_publish_dataset_ids()),
            },
        )
        if not release_blocked
        else ()
    )
    return ClaimMatrixResult(
        release_blocked=release_blocked,
        allowed_claims=allowed,
        blocked_claims=_dedupe_rows(blocked),
        required_missing=_dedupe_rows(required_missing),
        dataset_matrix=tuple(rows),
        unknown_datasets=unknown_datasets,
        permission_counters=counters,
        error_codes=tuple(dict.fromkeys(error_codes)),
        unknown_dataset_readiness_pass_count=0,
    )


def _release_scope_payload(release_scope_result: ReleaseScopeResult | Mapping[str, Any]) -> dict[str, Any]:
    if isinstance(release_scope_result, ReleaseScopeResult):
        return release_scope_result.to_dict()
    return dict(release_scope_result)


def serialize_release_readiness_summary(
    release_scope_result: ReleaseScopeResult | Mapping[str, Any],
    dataset_readiness: Mapping[str, Any] | None = None,
    *,
    p1_available: bool | None = None,
    permission_counters: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """序列化 CR018 S01 readiness summary，输出仅为 JSON-ready dict。"""

    scope_payload = _release_scope_payload(release_scope_result)
    scope = scope_payload.get("release_scope") or {}
    counters = normalise_permission_counters(permission_counters or scope_payload.get("permission_counters"))
    claim_matrix = build_release_claim_matrix(
        dataset_readiness,
        p1_available=p1_available,
        permission_counters=counters,
    )
    release_blocked_claims = tuple(dict(item) for item in scope_payload.get("blocked_claims", ()))
    blocked_claims = _dedupe_rows((*claim_matrix.blocked_claims, *release_blocked_claims))
    allowed_claims = tuple(dict(item) for item in claim_matrix.allowed_claims)
    if not scope_payload.get("passed", False):
        allowed_claims = ()

    return {
        "schema_version": "cr018.release_readiness.v1",
        "release_id": scope.get("release_id"),
        "release_scope": dict(scope),
        "as_of_trade_date": scope.get("as_of_trade_date"),
        "calendar_source": scope.get("calendar_source"),
        "dataset_group_matrix": [dict(item) for item in claim_matrix.dataset_matrix],
        "required_for_publish": list(required_for_publish_dataset_ids()),
        "allowed_claims": [dict(item) for item in allowed_claims],
        "blocked_claims": [dict(item) for item in blocked_claims],
        "required_missing": [dict(item) for item in claim_matrix.required_missing],
        "permission_counters": counters,
        "operation_counts": dict(counters),
        "publish_readiness_pass": bool(scope_payload.get("passed", False)) and not claim_matrix.release_blocked,
        "unknown_dataset_readiness_pass_count": claim_matrix.unknown_dataset_readiness_pass_count,
        "json_ready": True,
    }


__all__ = [
    "CLAIM_CAPACITY_TRADABLE",
    "CLAIM_CAPITAL_AMPLIFICATION",
    "CLAIM_INDUSTRY_NEUTRALIZED",
    "CLAIM_MARKET_CAP_NEUTRALIZED",
    "CLAIM_PUBLISH_READINESS",
    "CLAIM_PURE_ALPHA",
    "CLAIM_SCALE_UP_READY",
    "DATASET_GROUP_REGISTRY",
    "DATASET_BENCHMARK_GROUP",
    "DATASET_PIT_UNIVERSE",
    "DatasetGroupEntry",
    "DatasetGroupError",
    "P0_DATASET_GROUPS",
    "P1_BLOCKED_CLAIMS",
    "P1_DATASET_GROUPS",
    "PRIORITY_P0",
    "PRIORITY_P1",
    "REASON_P0_REQUIRED_MISSING",
    "REASON_P1_AUXILIARY_MISSING",
    "REASON_UNREGISTERED_DATASET",
    "ClaimMatrixResult",
    "build_release_claim_matrix",
    "get_dataset_group_entry",
    "list_dataset_groups",
    "required_for_publish_dataset_ids",
    "serialize_release_readiness_summary",
]
