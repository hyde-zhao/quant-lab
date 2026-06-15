"""CR019-S02 阶段六多基准看板与 primary benchmark policy 离线合同。

本模块只归一化调用方传入的 readiness / fixture / dry-run evidence，不读取
凭据、不触发 provider fetch、不写 lake / broker lake、不 publish，也不调用
QMT / MiniQMT / XtQuant。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping, Sequence

from market_data.contracts import (
    CR018_BENCHMARK_CSI_ALL_SHARE,
    CR018_BENCHMARK_DATASET_COMPONENTS,
    CR018_BENCHMARK_DATASET_PRICES,
    CR018_BENCHMARK_DATASET_TYPES,
    CR018_BENCHMARK_DATASET_WEIGHTS,
    CR018_BENCHMARK_HS300,
    CR018_BENCHMARK_INDEX_CODES,
    CR018_BENCHMARK_ZZ1000,
    CR018_BENCHMARK_ZZ500,
)


class BenchmarkId(str, Enum):
    """阶段六 admission 固定消费的四类宽基 benchmark。"""

    HS300 = CR018_BENCHMARK_HS300
    ZZ500 = CR018_BENCHMARK_ZZ500
    ZZ1000 = CR018_BENCHMARK_ZZ1000
    CSI_ALL_SHARE = CR018_BENCHMARK_CSI_ALL_SHARE


class BenchmarkReadinessStatus(str, Enum):
    """单个 benchmark 在 S02 dashboard 中的归一化状态。"""

    READY = "ready"
    UNAVAILABLE = "unavailable"
    BLOCKED = "blocked"


BENCHMARK_DASHBOARD_SCHEMA_VERSION = "cr019-s02-benchmark-dashboard-v1"
UNRESOLVED_PRIMARY_BENCHMARK = "unresolved"

FORBIDDEN_OPERATION_COUNTERS: tuple[str, ...] = (
    "provider_fetch",
    "lake_write",
    "broker_lake_write",
    "publish",
    "current_pointer_publish",
    "credential_read",
    "qmt_api_call",
    "xtquant_import",
    "service_start",
    "dependency_change",
    "real_order_call",
    "real_cancel_call",
    "account_query_call",
    "simulation_or_live_run",
)

_BENCHMARK_DISPLAY_NAMES: dict[BenchmarkId, str] = {
    BenchmarkId.HS300: "HS300",
    BenchmarkId.ZZ500: "ZZ500",
    BenchmarkId.ZZ1000: "ZZ1000",
    BenchmarkId.CSI_ALL_SHARE: "CSI_ALL_SHARE",
}

_DATASET_READY_FIELDS: dict[str, str] = {
    CR018_BENCHMARK_DATASET_PRICES: "prices_ready",
    CR018_BENCHMARK_DATASET_COMPONENTS: "components_ready",
    CR018_BENCHMARK_DATASET_WEIGHTS: "weights_ready",
}

_READY_VALUES = {"available", "pass", "passed", "ready", "true"}
_BLOCKED_VALUES = {"blocked", "required_missing"}

_BENCHMARK_ALIASES: dict[str, BenchmarkId] = {
    "HS300": BenchmarkId.HS300,
    "hs300": BenchmarkId.HS300,
    "csi300": BenchmarkId.HS300,
    "399300.SZ": BenchmarkId.HS300,
    "ZZ500": BenchmarkId.ZZ500,
    "zz500": BenchmarkId.ZZ500,
    "csi500": BenchmarkId.ZZ500,
    "000905.SH": BenchmarkId.ZZ500,
    "ZZ1000": BenchmarkId.ZZ1000,
    "zz1000": BenchmarkId.ZZ1000,
    "csi1000": BenchmarkId.ZZ1000,
    "000852.SH": BenchmarkId.ZZ1000,
    "CSI_ALL_SHARE": BenchmarkId.CSI_ALL_SHARE,
    "CSI_ALL": BenchmarkId.CSI_ALL_SHARE,
    "csi_all_share": BenchmarkId.CSI_ALL_SHARE,
    "csi_all": BenchmarkId.CSI_ALL_SHARE,
    "000985.SH": BenchmarkId.CSI_ALL_SHARE,
    "中证全指": BenchmarkId.CSI_ALL_SHARE,
}

_PROFILE_BENCHMARK_ALIASES: dict[str, BenchmarkId] = {
    "large_cap": BenchmarkId.HS300,
    "large-cap": BenchmarkId.HS300,
    "large": BenchmarkId.HS300,
    "blue_chip": BenchmarkId.HS300,
    "blue-chip": BenchmarkId.HS300,
    "hs300": BenchmarkId.HS300,
    "csi300": BenchmarkId.HS300,
    "mid_cap": BenchmarkId.ZZ500,
    "mid-cap": BenchmarkId.ZZ500,
    "mid": BenchmarkId.ZZ500,
    "zz500": BenchmarkId.ZZ500,
    "csi500": BenchmarkId.ZZ500,
    "small_cap": BenchmarkId.ZZ1000,
    "small-cap": BenchmarkId.ZZ1000,
    "small": BenchmarkId.ZZ1000,
    "zz1000": BenchmarkId.ZZ1000,
    "csi1000": BenchmarkId.ZZ1000,
    "all_market": BenchmarkId.CSI_ALL_SHARE,
    "all-market": BenchmarkId.CSI_ALL_SHARE,
    "all_a_share": BenchmarkId.CSI_ALL_SHARE,
    "all-a-share": BenchmarkId.CSI_ALL_SHARE,
    "broad_market": BenchmarkId.CSI_ALL_SHARE,
    "broad-market": BenchmarkId.CSI_ALL_SHARE,
    "mixed": BenchmarkId.CSI_ALL_SHARE,
    "csi_all": BenchmarkId.CSI_ALL_SHARE,
    "csi_all_share": BenchmarkId.CSI_ALL_SHARE,
}

_UNIVERSE_KEYS = (
    "universe",
    "universe_profile",
    "universe_scope",
    "market_cap",
    "market_cap_bucket",
    "benchmark_hint",
)

_STYLE_KEYS = (
    "style",
    "style_profile",
    "style_bucket",
    "market_cap_tilt",
    "size_tilt",
    "benchmark_hint",
)

_REAL_BENCHMARK_FIELDS = frozenset(
    {
        "real_benchmark_id",
        "real_benchmark_kind",
        "real_benchmark_ref",
        "real_benchmark_return",
        "real_tracking_error",
        "primary_benchmark",
        "benchmark_id",
        "benchmark_ref",
        "production_excess_return",
        "index_enhancement",
        "tracking_error",
        "hs300_return",
        "hs300_excess_return",
    }
)


@dataclass(frozen=True, slots=True)
class BenchmarkReadiness:
    """四基准 readiness 的 JSON-ready 行，不代表任何真实补数动作。"""

    benchmark_id: BenchmarkId | str
    prices_ready: bool
    components_ready: bool
    weights_ready: bool
    source_ref: str
    as_of_trade_date: str = ""
    status: BenchmarkReadinessStatus | str = BenchmarkReadinessStatus.READY
    reason_code: str = ""
    blocked_reason: str = ""
    missing_fields: tuple[str, ...] = ()
    index_code: str = ""
    dataset_statuses: Mapping[str, str] = field(default_factory=dict)

    @property
    def ready(self) -> bool:
        return (
            _enum_value(self.status) == BenchmarkReadinessStatus.READY.value
            and self.prices_ready
            and self.components_ready
            and self.weights_ready
            and bool(self.source_ref)
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "benchmark_id": _enum_value(self.benchmark_id),
            "display_name": _display_name(self.benchmark_id),
            "index_code": self.index_code,
            "prices_ready": self.prices_ready,
            "components_ready": self.components_ready,
            "weights_ready": self.weights_ready,
            "source_ref": self.source_ref,
            "as_of_trade_date": self.as_of_trade_date,
            "status": _enum_value(self.status),
            "reason_code": self.reason_code,
            "blocked_reason": self.blocked_reason,
            "missing_fields": list(self.missing_fields),
            "dataset_statuses": dict(self.dataset_statuses),
        }


@dataclass(frozen=True, slots=True)
class PrimaryBenchmarkDecision:
    """Primary benchmark 选择结果；无法安全判定时 fail closed。"""

    primary_benchmark: BenchmarkId | str
    status: str
    selection_basis: tuple[str, ...]
    reason_code: str = ""
    blocked: bool = False
    candidate_benchmark: BenchmarkId | str = ""
    blocked_reasons: tuple[str, ...] = ()
    universe_profile: Mapping[str, object] = field(default_factory=dict)
    style_profile: Mapping[str, object] = field(default_factory=dict)

    def to_dict(self) -> dict[str, object]:
        return {
            "primary_benchmark": _enum_value(self.primary_benchmark),
            "status": self.status,
            "selection_basis": list(self.selection_basis),
            "reason_code": self.reason_code,
            "blocked": self.blocked,
            "candidate_benchmark": _enum_value(self.candidate_benchmark),
            "blocked_reasons": list(self.blocked_reasons),
            "universe_profile": dict(self.universe_profile),
            "style_profile": dict(self.style_profile),
        }


@dataclass(frozen=True, slots=True)
class BenchmarkDashboard:
    """阶段六 admission benchmark dashboard 的内存合同。"""

    readiness_rows: tuple[BenchmarkReadiness, ...]
    primary_decision: PrimaryBenchmarkDecision
    status: str
    blocked_reasons: tuple[str, ...]
    permission_counters: Mapping[str, int] = field(
        default_factory=lambda: collect_benchmark_policy_safety_counters()
    )
    schema_version: str = BENCHMARK_DASHBOARD_SCHEMA_VERSION
    source_story: str = "CR019-S02-primary-benchmark-dashboard"

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "source_story": self.source_story,
            "status": self.status,
            "benchmark_count": len(
                {
                    _enum_value(row.benchmark_id)
                    for row in self.readiness_rows
                    if _coerce_benchmark_id(row.benchmark_id) is not None
                }
            ),
            "required_benchmarks": [
                benchmark.value for benchmark in required_stage6_benchmarks()
            ],
            "readiness_rows": [row.to_dict() for row in self.readiness_rows],
            "primary_decision": self.primary_decision.to_dict(),
            "blocked_reasons": list(self.blocked_reasons),
            "permission_counters": dict(self.permission_counters),
        }


def required_stage6_benchmarks() -> tuple[BenchmarkId, ...]:
    """返回阶段六 admission 必须展示的四类宽基 benchmark。"""

    return (
        BenchmarkId.HS300,
        BenchmarkId.ZZ500,
        BenchmarkId.ZZ1000,
        BenchmarkId.CSI_ALL_SHARE,
    )


def collect_benchmark_policy_safety_counters(
    counters: Mapping[str, object] | None = None,
) -> dict[str, int]:
    """归一化 S02 禁止操作计数；未传入时全部为 0。"""

    normalized = {key: 0 for key in FORBIDDEN_OPERATION_COUNTERS}
    if counters:
        for key, value in counters.items():
            normalized[str(key)] = int(value)
    return normalized


def build_benchmark_readiness(
    readiness: Mapping[str | BenchmarkId, object] | Sequence[object] | None,
    *,
    as_of_trade_date: str = "",
) -> tuple[BenchmarkReadiness, ...]:
    """从 readiness dict 或 CR018-S03 行式 evidence 构造四基准 readiness。"""

    indexed, unknown_rows = _index_readiness(readiness, as_of_trade_date)
    rows = [
        _build_required_readiness_row(
            benchmark_id,
            indexed.get(benchmark_id),
            as_of_trade_date,
        )
        for benchmark_id in required_stage6_benchmarks()
    ]
    rows.extend(unknown_rows)
    return tuple(rows)


def select_primary_benchmark(
    universe_profile: Mapping[str, object] | str | None,
    style_profile: Mapping[str, object] | str | None,
    readiness_rows: Sequence[BenchmarkReadiness | Mapping[str, object]],
) -> PrimaryBenchmarkDecision:
    """按 universe 优先、style 补充的 exact 规则选择 primary benchmark。"""

    universe = _profile_to_mapping(universe_profile, "universe")
    style = _profile_to_mapping(style_profile, "style")
    universe_candidate, universe_basis = _candidate_from_profile(
        universe, _UNIVERSE_KEYS, "universe"
    )
    style_candidate, style_basis = _candidate_from_profile(style, _STYLE_KEYS, "style")
    selection_basis = tuple(item for item in (*universe_basis, *style_basis) if item)

    if universe_candidate and style_candidate and universe_candidate != style_candidate:
        return _unresolved_primary_decision(
            "primary_benchmark_unresolved",
            (*selection_basis, "conflict:universe_style"),
            ("universe_style_conflict",),
            universe_candidate,
            universe,
            style,
        )

    candidate = universe_candidate or style_candidate
    if candidate is None:
        return _unresolved_primary_decision(
            "primary_benchmark_unresolved",
            (*selection_basis, "missing:universe_or_style_profile"),
            ("unknown_universe_profile",),
            "",
            universe,
            style,
        )

    readiness = _readiness_map(readiness_rows).get(candidate)
    if readiness is None:
        return _unresolved_primary_decision(
            "primary_benchmark_unresolved",
            (*selection_basis, f"candidate:{candidate.value}"),
            ("missing_benchmark_readiness",),
            candidate,
            universe,
            style,
        )
    if not readiness.ready:
        return _unresolved_primary_decision(
            "primary_benchmark_unresolved",
            (*selection_basis, f"candidate:{candidate.value}"),
            (readiness.reason_code or "benchmark_unavailable",),
            candidate,
            universe,
            style,
        )

    return PrimaryBenchmarkDecision(
        primary_benchmark=candidate,
        status="selected",
        selection_basis=(*selection_basis, f"readiness:{candidate.value}:ready"),
        candidate_benchmark=candidate,
        universe_profile=universe,
        style_profile=style,
    )


def build_benchmark_dashboard(
    readiness_rows: Sequence[BenchmarkReadiness | Mapping[str, object]],
    primary_decision: PrimaryBenchmarkDecision | Mapping[str, object],
    permission_counters: Mapping[str, object] | None = None,
    *,
    benchmark_payload: Mapping[str, object] | None = None,
) -> BenchmarkDashboard:
    """构造 dashboard 内存 payload，不写真实报告、不 publish。"""

    rows = tuple(_coerce_readiness_row(row) for row in readiness_rows)
    decision = _coerce_primary_decision(primary_decision)
    counters = collect_benchmark_policy_safety_counters(permission_counters)
    blocked_reasons: list[str] = []

    required_ids = set(required_stage6_benchmarks())
    present_ids = {
        benchmark_id
        for benchmark_id in (_coerce_benchmark_id(row.benchmark_id) for row in rows)
        if benchmark_id is not None
    }
    if present_ids != required_ids:
        blocked_reasons.append("missing_benchmark_readiness")

    for row in rows:
        if _coerce_benchmark_id(row.benchmark_id) is None:
            blocked_reasons.append("unknown_benchmark_id")
        elif not row.ready:
            blocked_reasons.append(row.reason_code or "benchmark_unavailable")

    if decision.blocked:
        blocked_reasons.append(decision.reason_code or "primary_benchmark_unresolved")
        blocked_reasons.extend(decision.blocked_reasons)

    if any(value != 0 for value in counters.values()):
        blocked_reasons.append("real_operation_forbidden")

    proxy_error = reject_proxy_as_real_benchmark(benchmark_payload or {})
    if proxy_error:
        blocked_reasons.append(str(proxy_error["reason_code"]))

    deduped_reasons = tuple(dict.fromkeys(blocked_reasons))
    return BenchmarkDashboard(
        readiness_rows=rows,
        primary_decision=decision,
        status="blocked" if deduped_reasons else "ready",
        blocked_reasons=deduped_reasons,
        permission_counters=counters,
    )


def reject_proxy_as_real_benchmark(
    benchmark_payload: Mapping[str, object] | None,
) -> dict[str, object] | None:
    """禁止 proxy benchmark 写入真实 benchmark 字段。"""

    payload = dict(benchmark_payload or {})
    if not _payload_declares_proxy(payload):
        return None

    forbidden_fields = tuple(
        field
        for field in sorted(_REAL_BENCHMARK_FIELDS)
        if _has_value(payload.get(field))
    )
    if not forbidden_fields:
        return None

    return {
        "blocked": True,
        "reason_code": "proxy_benchmark_forbidden",
        "forbidden_fields": list(forbidden_fields),
        "proxy_as_real_count": len(forbidden_fields),
        "unlock_condition": "move_proxy_benchmark_to_comparison_only_fields",
    }


def serialize_benchmark_dashboard(
    dashboard: BenchmarkDashboard | Mapping[str, object],
) -> dict[str, object]:
    """返回 JSON-ready dashboard dict，供后续 S01/S10 只读引用。"""

    if isinstance(dashboard, BenchmarkDashboard):
        return dashboard.to_dict()
    return dict(dashboard)


def _index_readiness(
    readiness: Mapping[str | BenchmarkId, object] | Sequence[object] | None,
    as_of_trade_date: str,
) -> tuple[dict[BenchmarkId, object], list[BenchmarkReadiness]]:
    if readiness is None:
        return {}, []
    if isinstance(readiness, Mapping):
        return _index_readiness_mapping(readiness), []
    return _index_readiness_sequence(readiness, as_of_trade_date)


def _index_readiness_mapping(
    readiness: Mapping[str | BenchmarkId, object],
) -> dict[BenchmarkId, object]:
    indexed: dict[BenchmarkId, object] = {}
    for key, value in readiness.items():
        benchmark_id = _coerce_benchmark_id(key)
        if benchmark_id is not None:
            indexed[benchmark_id] = value
    return indexed


def _index_readiness_sequence(
    readiness: Sequence[object],
    as_of_trade_date: str,
) -> tuple[dict[BenchmarkId, object], list[BenchmarkReadiness]]:
    indexed: dict[BenchmarkId, object] = {}
    dataset_rows: dict[BenchmarkId, list[Mapping[str, object]]] = {}
    unknown_rows: list[BenchmarkReadiness] = []

    for item in readiness:
        if isinstance(item, BenchmarkReadiness):
            benchmark_id = _coerce_benchmark_id(item.benchmark_id)
            if benchmark_id is None:
                unknown_rows.append(item)
            else:
                indexed[benchmark_id] = item
            continue
        if not isinstance(item, Mapping):
            continue
        benchmark_id = _coerce_benchmark_id(
            item.get("benchmark_id") or item.get("id") or item.get("index_code")
        )
        if benchmark_id is None:
            unknown_rows.append(
                _unknown_readiness_row(
                    str(item.get("benchmark_id") or item.get("id") or ""),
                    as_of_trade_date,
                )
            )
            continue
        if any(field in item for field in _DATASET_READY_FIELDS.values()):
            indexed[benchmark_id] = item
            continue
        dataset_rows.setdefault(benchmark_id, []).append(item)

    for benchmark_id, rows in dataset_rows.items():
        if benchmark_id not in indexed:
            indexed[benchmark_id] = _aggregate_dataset_rows(
                benchmark_id, rows, as_of_trade_date
            )
    return indexed, unknown_rows


def _aggregate_dataset_rows(
    benchmark_id: BenchmarkId,
    rows: Sequence[Mapping[str, object]],
    as_of_trade_date: str,
) -> dict[str, object]:
    dataset_statuses: dict[str, str] = {}
    payload: dict[str, object] = {
        "benchmark_id": benchmark_id,
        "source_ref": "",
        "as_of_trade_date": as_of_trade_date,
        "dataset_statuses": dataset_statuses,
    }
    source_refs: list[str] = []
    for row in rows:
        dataset_type = str(row.get("dataset_type") or "")
        if dataset_type not in CR018_BENCHMARK_DATASET_TYPES:
            continue
        status = str(row.get("readiness_status") or row.get("status") or "")
        dataset_statuses[dataset_type] = status
        payload[_DATASET_READY_FIELDS[dataset_type]] = _status_is_ready(status)
        source_refs.append(
            str(
                row.get("source_ref")
                or row.get("evidence_ref")
                or f"cr018-s03:{benchmark_id.value}:{dataset_type}"
            )
        )
        if row.get("as_of_trade_date"):
            payload["as_of_trade_date"] = str(row["as_of_trade_date"])
    payload["source_ref"] = "|".join(dict.fromkeys(source_refs))
    return payload


def _build_required_readiness_row(
    benchmark_id: BenchmarkId,
    raw: object,
    as_of_trade_date: str,
) -> BenchmarkReadiness:
    if raw is None:
        return BenchmarkReadiness(
            benchmark_id=benchmark_id,
            prices_ready=False,
            components_ready=False,
            weights_ready=False,
            source_ref="",
            as_of_trade_date=as_of_trade_date,
            status=BenchmarkReadinessStatus.BLOCKED,
            reason_code="missing_benchmark_readiness",
            blocked_reason="missing_benchmark_readiness",
            missing_fields=(
                "prices_ready",
                "components_ready",
                "weights_ready",
                "source_ref",
            ),
            index_code=_index_code(benchmark_id),
        )
    if isinstance(raw, BenchmarkReadiness):
        return raw
    if not isinstance(raw, Mapping):
        raw = {"source_ref": str(raw)}

    prices_ready = _as_bool(raw.get("prices_ready"))
    components_ready = _as_bool(raw.get("components_ready"))
    weights_ready = _as_bool(raw.get("weights_ready"))
    source_ref = str(raw.get("source_ref") or raw.get("evidence_ref") or "")
    row_as_of = str(raw.get("as_of_trade_date") or as_of_trade_date or "")
    explicit_status = str(raw.get("status") or raw.get("readiness_status") or "")
    missing_fields = tuple(
        field
        for field, ready in (
            ("prices_ready", prices_ready),
            ("components_ready", components_ready),
            ("weights_ready", weights_ready),
        )
        if not ready
    ) + (() if source_ref else ("source_ref",))

    status = BenchmarkReadinessStatus.READY
    reason_code = str(raw.get("reason_code") or "")
    if missing_fields or (explicit_status and not _status_is_ready(explicit_status)):
        status = (
            BenchmarkReadinessStatus.BLOCKED
            if explicit_status in _BLOCKED_VALUES
            else BenchmarkReadinessStatus.UNAVAILABLE
        )
        reason_code = reason_code or "benchmark_unavailable"

    return BenchmarkReadiness(
        benchmark_id=benchmark_id,
        prices_ready=prices_ready,
        components_ready=components_ready,
        weights_ready=weights_ready,
        source_ref=source_ref,
        as_of_trade_date=row_as_of,
        status=status,
        reason_code=reason_code,
        blocked_reason=reason_code,
        missing_fields=missing_fields,
        index_code=_index_code(benchmark_id),
        dataset_statuses=dict(raw.get("dataset_statuses") or {}),
    )


def _coerce_readiness_row(
    row: BenchmarkReadiness | Mapping[str, object],
) -> BenchmarkReadiness:
    if isinstance(row, BenchmarkReadiness):
        return row
    benchmark_id = _coerce_benchmark_id(row.get("benchmark_id"))
    if benchmark_id is None:
        return _unknown_readiness_row(str(row.get("benchmark_id") or ""), "")
    return _build_required_readiness_row(benchmark_id, row, "")


def _unknown_readiness_row(
    benchmark_id: str,
    as_of_trade_date: str,
) -> BenchmarkReadiness:
    return BenchmarkReadiness(
        benchmark_id=benchmark_id or "unknown",
        prices_ready=False,
        components_ready=False,
        weights_ready=False,
        source_ref="",
        as_of_trade_date=as_of_trade_date,
        status=BenchmarkReadinessStatus.BLOCKED,
        reason_code="unknown_benchmark_id",
        blocked_reason="unknown_benchmark_id",
        missing_fields=("benchmark_id",),
    )


def _coerce_primary_decision(
    decision: PrimaryBenchmarkDecision | Mapping[str, object],
) -> PrimaryBenchmarkDecision:
    if isinstance(decision, PrimaryBenchmarkDecision):
        return decision
    primary = _coerce_benchmark_id(decision.get("primary_benchmark")) or str(
        decision.get("primary_benchmark") or UNRESOLVED_PRIMARY_BENCHMARK
    )
    candidate = _coerce_benchmark_id(decision.get("candidate_benchmark")) or str(
        decision.get("candidate_benchmark") or ""
    )
    return PrimaryBenchmarkDecision(
        primary_benchmark=primary,
        status=str(decision.get("status") or ""),
        selection_basis=tuple(decision.get("selection_basis") or ()),
        reason_code=str(decision.get("reason_code") or ""),
        blocked=bool(decision.get("blocked", False)),
        candidate_benchmark=candidate,
        blocked_reasons=tuple(decision.get("blocked_reasons") or ()),
    )


def _profile_to_mapping(
    profile: Mapping[str, object] | str | None,
    default_key: str,
) -> dict[str, object]:
    if profile is None:
        return {}
    if isinstance(profile, Mapping):
        return dict(profile)
    return {default_key: str(profile)}


def _candidate_from_profile(
    profile: Mapping[str, object],
    keys: Sequence[str],
    source: str,
) -> tuple[BenchmarkId | None, tuple[str, ...]]:
    for key in keys:
        if key not in profile:
            continue
        value = str(profile[key])
        candidate = _PROFILE_BENCHMARK_ALIASES.get(value)
        if candidate is not None:
            return candidate, (f"{source}:{key}={value}->{candidate.value}",)
    return None, tuple(f"{source}:{key}={profile[key]}" for key in keys if key in profile)


def _unresolved_primary_decision(
    reason_code: str,
    selection_basis: Sequence[str],
    blocked_reasons: Sequence[str],
    candidate_benchmark: BenchmarkId | str,
    universe_profile: Mapping[str, object],
    style_profile: Mapping[str, object],
) -> PrimaryBenchmarkDecision:
    return PrimaryBenchmarkDecision(
        primary_benchmark=UNRESOLVED_PRIMARY_BENCHMARK,
        status="blocked",
        selection_basis=tuple(selection_basis),
        reason_code=reason_code,
        blocked=True,
        candidate_benchmark=candidate_benchmark,
        blocked_reasons=tuple(dict.fromkeys(blocked_reasons)),
        universe_profile=universe_profile,
        style_profile=style_profile,
    )


def _readiness_map(
    readiness_rows: Sequence[BenchmarkReadiness | Mapping[str, object]],
) -> dict[BenchmarkId, BenchmarkReadiness]:
    mapped: dict[BenchmarkId, BenchmarkReadiness] = {}
    for row in readiness_rows:
        coerced = _coerce_readiness_row(row)
        benchmark_id = _coerce_benchmark_id(coerced.benchmark_id)
        if benchmark_id is not None:
            mapped[benchmark_id] = coerced
    return mapped


def _payload_declares_proxy(payload: Mapping[str, object]) -> bool:
    if bool(payload.get("is_proxy")):
        return True
    marker_fields = (
        "benchmark_kind",
        "benchmark_source_kind",
        "benchmark_type",
        "source_kind",
    )
    if any("proxy" in str(payload.get(field, "")).lower() for field in marker_fields):
        return True
    return any(
        key.startswith("proxy_") and _has_value(value)
        for key, value in payload.items()
    )


def _has_value(value: object) -> bool:
    return value not in (None, "", (), [], {})


def _coerce_benchmark_id(value: object) -> BenchmarkId | None:
    if isinstance(value, BenchmarkId):
        return value
    if isinstance(value, Enum):
        value = value.value
    return _BENCHMARK_ALIASES.get(str(value))


def _status_is_ready(value: object) -> bool:
    if isinstance(value, Enum):
        value = value.value
    text = str(value).lower()
    return text in _READY_VALUES


def _as_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, Enum):
        value = value.value
    if isinstance(value, str):
        return value.lower() in _READY_VALUES
    return bool(value)


def _index_code(benchmark_id: BenchmarkId) -> str:
    return CR018_BENCHMARK_INDEX_CODES[benchmark_id.value]


def _display_name(benchmark_id: BenchmarkId | str) -> str:
    coerced = _coerce_benchmark_id(benchmark_id)
    if coerced is None:
        return str(benchmark_id)
    return _BENCHMARK_DISPLAY_NAMES[coerced]


def _enum_value(value: object) -> object:
    if isinstance(value, Enum):
        return value.value
    return value


__all__ = [
    "BENCHMARK_DASHBOARD_SCHEMA_VERSION",
    "FORBIDDEN_OPERATION_COUNTERS",
    "UNRESOLVED_PRIMARY_BENCHMARK",
    "BenchmarkDashboard",
    "BenchmarkId",
    "BenchmarkReadiness",
    "BenchmarkReadinessStatus",
    "PrimaryBenchmarkDecision",
    "build_benchmark_dashboard",
    "build_benchmark_readiness",
    "collect_benchmark_policy_safety_counters",
    "reject_proxy_as_real_benchmark",
    "required_stage6_benchmarks",
    "select_primary_benchmark",
    "serialize_benchmark_dashboard",
]
