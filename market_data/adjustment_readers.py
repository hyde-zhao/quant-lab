"""CR017-S04 显式复权口径 reader、single-policy gate 与 QMT handoff。"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence

import pandas as pd

from .contracts import (
    ADJUSTMENT_POLICY_RAW,
    ADJUSTMENT_POLICY_VALUES,
    CR017_FORBIDDEN_OPERATION_COUNTERS,
    CR017_VIEW_PRICES_RAW,
    QUALITY_STATUS_FAIL,
    QUALITY_STATUS_PASS,
)

GATE_STATUS_PASS = "pass"
GATE_STATUS_BLOCKED = "blocked"

RESEARCH_ADJUSTMENT_POLICY_MISSING = "research_adjustment_policy_missing"
RESEARCH_ADJUSTMENT_POLICY_MIXED = "research_adjustment_policy_mixed"
RESEARCH_ADJUSTMENT_POLICY_MISMATCH = "research_adjustment_policy_mismatch"
RESEARCH_ADJUSTMENT_POLICY_UNKNOWN = "research_adjustment_policy_unknown"
UNPUBLISHED_CANDIDATE_BLOCKED = "unpublished_candidate_blocked"
QUALITY_STATUS_BLOCKED = "quality_status_blocked"
RAW_PRICE_REF_REQUIRED = "raw_price_ref_required"

READER_REQUIRED_METADATA_FIELDS: tuple[str, ...] = (
    "policy",
    "view_id",
    "source_run_id",
    "quality_status",
    "single_policy_gate_status",
)


def zero_operation_counts() -> dict[str, int]:
    counts = dict(CR017_FORBIDDEN_OPERATION_COUNTERS)
    counts["qmt_api_call"] = 0
    counts["real_order"] = 0
    return counts


@dataclass(frozen=True, slots=True)
class SinglePolicyGateResult:
    """single-policy gate 的结构化结果。"""

    status: str
    policy: str
    requested_policy: str
    policies_seen: tuple[str, ...] = ()
    blocked_reason: str = ""
    missing_sample_count: int = 0
    source_fields: tuple[str, ...] = ()
    operation_counts: dict[str, int] = field(default_factory=zero_operation_counts)

    @property
    def passed(self) -> bool:
        return self.status == GATE_STATUS_PASS

    def to_metadata(self) -> dict[str, Any]:
        return {
            "single_policy_gate_status": self.status,
            "policy": self.policy,
            "requested_policy": self.requested_policy,
            "policies_seen": list(self.policies_seen),
            "blocked_reason": self.blocked_reason,
            "missing_sample_count": int(self.missing_sample_count),
            "source_fields": list(self.source_fields),
            "operation_counts": dict(self.operation_counts),
        }


@dataclass(frozen=True, slots=True)
class AdjustedViewMetadata:
    """reader 输出的复权视图 metadata。"""

    policy: str
    view_id: str
    source_run_id: str
    quality_status: str
    single_policy_gate_status: str
    research_adjustment_policy: str
    status: str = "available"
    blocked_reason: str = ""
    policies_seen: tuple[str, ...] = ()
    operation_counts: dict[str, int] = field(default_factory=zero_operation_counts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "policy": self.policy,
            "research_adjustment_policy": self.research_adjustment_policy,
            "view_id": self.view_id,
            "source_run_id": self.source_run_id,
            "quality_status": self.quality_status,
            "single_policy_gate_status": self.single_policy_gate_status,
            "status": self.status,
            "blocked_reason": self.blocked_reason,
            "policies_seen": list(self.policies_seen),
            "operation_counts": dict(self.operation_counts),
        }


@dataclass(frozen=True, slots=True)
class AdjustedViewResult:
    """显式 policy reader 结果；不执行抓取、写湖或 publish。"""

    status: str
    frame: pd.DataFrame | None
    metadata: AdjustedViewMetadata
    issues: tuple[dict[str, Any], ...] = ()
    operation_counts: dict[str, int] = field(default_factory=zero_operation_counts)

    @property
    def available(self) -> bool:
        return self.status == "available"

    def to_metadata(self) -> dict[str, Any]:
        return self.metadata.to_dict()


@dataclass(frozen=True, slots=True)
class QmtPolicyHandoff:
    """传给 QMT/OMS 侧的 metadata；执行价口径固定 raw。"""

    status: str
    research_adjustment_policy: str
    execution_price_policy: str = ADJUSTMENT_POLICY_RAW
    view_id: str = ""
    source_run_id: str = ""
    quality_status: str = QUALITY_STATUS_PASS
    raw_price_ref: str = ""
    blocked_reason: str = ""
    adjusted_execution_price_pass_count: int = 0
    operation_counts: dict[str, int] = field(default_factory=zero_operation_counts)

    @property
    def passed(self) -> bool:
        return self.status == GATE_STATUS_PASS

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "research_adjustment_policy": self.research_adjustment_policy,
            "execution_price_policy": self.execution_price_policy,
            "view_id": self.view_id,
            "source_run_id": self.source_run_id,
            "quality_status": self.quality_status,
            "raw_price_ref": self.raw_price_ref,
            "blocked_reason": self.blocked_reason,
            "adjusted_execution_price_pass_count": int(self.adjusted_execution_price_pass_count),
            "operation_counts": dict(self.operation_counts),
        }


def single_policy_gate(
    metadata_or_frame: Mapping[str, Any] | pd.DataFrame | None,
    requested_policy: str | None,
) -> SinglePolicyGateResult:
    """阻断缺失 policy、未知 policy、混用 policy 或 request/data 不一致。"""

    requested = _normalize_policy(requested_policy)
    if not requested:
        return _blocked_gate("", requested, RESEARCH_ADJUSTMENT_POLICY_MISSING)
    if requested not in ADJUSTMENT_POLICY_VALUES:
        return _blocked_gate(requested, requested, RESEARCH_ADJUSTMENT_POLICY_UNKNOWN)

    policies, missing_count, sources = _extract_policy_values(metadata_or_frame)
    if not policies:
        return _blocked_gate("", requested, RESEARCH_ADJUSTMENT_POLICY_MISSING, missing_count, sources)
    if len(policies) > 1:
        return _blocked_gate("", requested, RESEARCH_ADJUSTMENT_POLICY_MIXED, missing_count, sources, policies)
    policy = policies[0]
    if policy not in ADJUSTMENT_POLICY_VALUES:
        return _blocked_gate(policy, requested, RESEARCH_ADJUSTMENT_POLICY_UNKNOWN, missing_count, sources, policies)
    if policy != requested:
        return _blocked_gate(policy, requested, RESEARCH_ADJUSTMENT_POLICY_MISMATCH, missing_count, sources, policies)
    return SinglePolicyGateResult(
        status=GATE_STATUS_PASS,
        policy=policy,
        requested_policy=requested,
        policies_seen=(policy,),
        missing_sample_count=missing_count,
        source_fields=tuple(sources),
    )


def read_adjusted_view(
    view_id: str,
    research_adjustment_policy: str | None = None,
    *,
    policy: str | None = None,
    frame: pd.DataFrame | Sequence[Mapping[str, Any]] | None = None,
    metadata: Mapping[str, Any] | None = None,
    source_run_id: str | None = None,
    quality_status: str | None = None,
    candidate_published: bool = True,
    start_date: str | None = None,
    end_date: str | None = None,
    symbols: Sequence[str] | None = None,
) -> AdjustedViewResult:
    """读取调用方传入的 adjusted view fixture，并输出强制 policy metadata。

    本入口只处理已传入的 frame / metadata，不访问数据湖、不调用 provider、
    不发布 current pointer。
    """

    requested_policy = _normalize_policy(policy or research_adjustment_policy)
    work = _coerce_frame(frame)
    work = _filter_adjusted_frame(work, start_date=start_date, end_date=end_date, symbols=symbols)
    source_meta = dict(metadata or {})
    source_run = str(source_run_id or source_meta.get("source_run_id") or _first_frame_value(work, "source_run_id") or "")
    quality = str(quality_status or source_meta.get("quality_status") or _first_frame_value(work, "quality_status") or QUALITY_STATUS_PASS)
    if work is not None and source_meta:
        work.attrs.update(source_meta)

    if not candidate_published:
        return _adjusted_view_blocked(
            view_id=view_id,
            requested_policy=requested_policy,
            source_run_id=source_run,
            quality_status=quality,
            reason=UNPUBLISHED_CANDIDATE_BLOCKED,
            policies_seen=(),
        )
    if quality == QUALITY_STATUS_FAIL:
        return _adjusted_view_blocked(
            view_id=view_id,
            requested_policy=requested_policy,
            source_run_id=source_run,
            quality_status=quality,
            reason=QUALITY_STATUS_BLOCKED,
            policies_seen=(),
        )

    gate_payload: Mapping[str, Any] | pd.DataFrame | None
    if work is not None and not work.empty:
        gate_payload = work
    else:
        gate_payload = source_meta
    gate = single_policy_gate(gate_payload, requested_policy)
    if not gate.passed:
        return _adjusted_view_blocked(
            view_id=view_id,
            requested_policy=requested_policy,
            source_run_id=source_run,
            quality_status=quality,
            reason=gate.blocked_reason,
            policies_seen=gate.policies_seen,
            gate=gate,
        )

    output = work.copy() if work is not None else pd.DataFrame()
    reader_metadata = AdjustedViewMetadata(
        policy=gate.policy,
        research_adjustment_policy=gate.policy,
        view_id=view_id,
        source_run_id=source_run,
        quality_status=quality,
        single_policy_gate_status=GATE_STATUS_PASS,
        status="available",
        policies_seen=gate.policies_seen,
    )
    output.attrs.update(reader_metadata.to_dict())
    return AdjustedViewResult(
        status="available",
        frame=output.reset_index(drop=True),
        metadata=reader_metadata,
        issues=(),
        operation_counts=zero_operation_counts(),
    )


def assert_published_view_only(view_ref: Mapping[str, Any] | None) -> SinglePolicyGateResult:
    """默认阻断未发布 candidate，避免 reader 直接扫描 candidate truth。"""

    ref = dict(view_ref or {})
    if ref.get("published") is True or ref.get("status") == "published":
        policy = _normalize_policy(ref.get("research_adjustment_policy") or ref.get("policy"))
        return SinglePolicyGateResult(
            status=GATE_STATUS_PASS,
            policy=policy,
            requested_policy=policy,
            policies_seen=(policy,) if policy else (),
            source_fields=("view_ref",),
        )
    return _blocked_gate("", "", UNPUBLISHED_CANDIDATE_BLOCKED)


def build_qmt_policy_handoff(
    research_policy: str | None,
    raw_price_ref: str | Mapping[str, Any] | None,
    *,
    view_id: str = "",
    source_run_id: str = "",
    quality_status: str = QUALITY_STATUS_PASS,
    metadata: Mapping[str, Any] | None = None,
) -> QmtPolicyHandoff:
    """构建 QMT metadata handoff；执行价永远声明为 raw。"""

    policy = _normalize_policy(research_policy)
    raw_ref = _raw_price_ref_to_string(raw_price_ref)
    if not policy or policy not in ADJUSTMENT_POLICY_VALUES:
        return QmtPolicyHandoff(
            status=GATE_STATUS_BLOCKED,
            research_adjustment_policy=policy,
            view_id=view_id or str((metadata or {}).get("view_id") or ""),
            source_run_id=source_run_id or str((metadata or {}).get("source_run_id") or ""),
            quality_status=quality_status,
            raw_price_ref=raw_ref,
            blocked_reason=RESEARCH_ADJUSTMENT_POLICY_MISSING if not policy else RESEARCH_ADJUSTMENT_POLICY_UNKNOWN,
        )
    if not raw_ref:
        return QmtPolicyHandoff(
            status=GATE_STATUS_BLOCKED,
            research_adjustment_policy=policy,
            view_id=view_id or str((metadata or {}).get("view_id") or ""),
            source_run_id=source_run_id or str((metadata or {}).get("source_run_id") or ""),
            quality_status=quality_status,
            raw_price_ref="",
            blocked_reason=RAW_PRICE_REF_REQUIRED,
        )
    return QmtPolicyHandoff(
        status=GATE_STATUS_PASS,
        research_adjustment_policy=policy,
        view_id=view_id or str((metadata or {}).get("view_id") or ""),
        source_run_id=source_run_id or str((metadata or {}).get("source_run_id") or ""),
        quality_status=quality_status,
        raw_price_ref=raw_ref,
    )


def _adjusted_view_blocked(
    *,
    view_id: str,
    requested_policy: str,
    source_run_id: str,
    quality_status: str,
    reason: str,
    policies_seen: Sequence[str],
    gate: SinglePolicyGateResult | None = None,
) -> AdjustedViewResult:
    metadata = AdjustedViewMetadata(
        policy=requested_policy,
        research_adjustment_policy=requested_policy,
        view_id=view_id,
        source_run_id=source_run_id,
        quality_status=quality_status,
        single_policy_gate_status=GATE_STATUS_BLOCKED,
        status=GATE_STATUS_BLOCKED,
        blocked_reason=reason,
        policies_seen=tuple(policies_seen),
    )
    issue = {
        "code": reason,
        "view_id": view_id,
        "policy": requested_policy,
        "policies_seen": list(policies_seen),
    }
    if gate is not None:
        issue["gate"] = gate.to_metadata()
    return AdjustedViewResult(
        status=GATE_STATUS_BLOCKED,
        frame=None,
        metadata=metadata,
        issues=(issue,),
        operation_counts=zero_operation_counts(),
    )


def _blocked_gate(
    policy: str,
    requested_policy: str,
    reason: str,
    missing_count: int = 0,
    sources: Sequence[str] = (),
    policies_seen: Sequence[str] = (),
) -> SinglePolicyGateResult:
    return SinglePolicyGateResult(
        status=GATE_STATUS_BLOCKED,
        policy=policy,
        requested_policy=requested_policy,
        policies_seen=tuple(policies_seen),
        blocked_reason=reason,
        missing_sample_count=int(missing_count),
        source_fields=tuple(sources),
    )


def _extract_policy_values(
    metadata_or_frame: Mapping[str, Any] | pd.DataFrame | None,
) -> tuple[tuple[str, ...], int, tuple[str, ...]]:
    values: set[str] = set()
    missing_count = 0
    sources: list[str] = []
    if metadata_or_frame is None:
        return (), 0, ()
    if isinstance(metadata_or_frame, pd.DataFrame):
        frame_values, frame_missing, frame_sources = _policy_values_from_frame(metadata_or_frame)
        values.update(frame_values)
        missing_count += frame_missing
        sources.extend(frame_sources)
        attr_values = _policy_values_from_mapping(metadata_or_frame.attrs)
        if attr_values:
            values.update(attr_values)
            sources.append("frame.attrs")
        return tuple(sorted(values)), int(missing_count), tuple(sorted(set(sources)))
    mapping_values = _policy_values_from_mapping(metadata_or_frame)
    if mapping_values:
        values.update(mapping_values)
        sources.append("metadata")
    return tuple(sorted(values)), int(missing_count), tuple(sorted(set(sources)))


def _policy_values_from_frame(frame: pd.DataFrame) -> tuple[set[str], int, tuple[str, ...]]:
    values: set[str] = set()
    columns = [name for name in ("research_adjustment_policy", "adjustment_policy", "policy") if name in frame.columns]
    if not columns:
        return values, int(len(frame)), ()
    has_policy = pd.Series(False, index=frame.index)
    sources: list[str] = []
    for column in columns:
        series = frame[column]
        text = series.fillna("").astype(str).str.strip()
        values.update(item for item in text.tolist() if item)
        has_policy = has_policy | text.ne("")
        sources.append(f"frame.{column}")
    return values, int((~has_policy).sum()), tuple(sources)


def _policy_values_from_mapping(value: Mapping[str, Any]) -> set[str]:
    values: set[str] = set()
    for key in ("research_adjustment_policy", "policy", "adjustment_policy", "data_adjustment_policy"):
        policy = _normalize_policy(value.get(key))
        if policy:
            values.add(policy)
    raw_seen = value.get("policies_seen")
    if isinstance(raw_seen, Sequence) and not isinstance(raw_seen, (str, bytes)):
        values.update(policy for policy in (_normalize_policy(item) for item in raw_seen) if policy)
    nested = value.get("adjustment")
    if isinstance(nested, Mapping):
        values.update(_policy_values_from_mapping(nested))
    nested_metadata = value.get("metadata")
    if isinstance(nested_metadata, Mapping):
        values.update(_policy_values_from_mapping(nested_metadata))
    return values


def _coerce_frame(frame: pd.DataFrame | Sequence[Mapping[str, Any]] | None) -> pd.DataFrame | None:
    if frame is None:
        return None
    if isinstance(frame, pd.DataFrame):
        return frame.copy()
    return pd.DataFrame([dict(item) for item in frame])


def _filter_adjusted_frame(
    frame: pd.DataFrame | None,
    *,
    start_date: str | None,
    end_date: str | None,
    symbols: Sequence[str] | None,
) -> pd.DataFrame | None:
    if frame is None:
        return None
    output = frame.copy()
    if start_date is not None and "trade_date" in output.columns:
        output = output[output["trade_date"].astype(str) >= str(start_date)]
    if end_date is not None and "trade_date" in output.columns:
        output = output[output["trade_date"].astype(str) <= str(end_date)]
    if symbols is not None and "symbol" in output.columns:
        symbol_set = {str(item) for item in symbols}
        output = output[output["symbol"].astype(str).isin(symbol_set)]
    return output.reset_index(drop=True)


def _first_frame_value(frame: pd.DataFrame | None, column: str) -> Any:
    if frame is None or frame.empty or column not in frame.columns:
        return ""
    values = frame[column].dropna().astype(str).str.strip()
    if values.empty:
        return ""
    return values.iloc[0]


def _raw_price_ref_to_string(value: str | Mapping[str, Any] | None) -> str:
    if value is None:
        return ""
    if isinstance(value, Mapping):
        for key in ("raw_price_ref", "price_ref", "ref", "source_ref"):
            text = str(value.get(key) or "").strip()
            if text:
                return text
        if value.get("view_id") == CR017_VIEW_PRICES_RAW:
            trade_date = str(value.get("trade_date") or "")
            symbol = str(value.get("symbol") or "")
            if trade_date and symbol:
                return f"{CR017_VIEW_PRICES_RAW}:{trade_date}:{symbol}"
        return ""
    return str(value).strip()


def _normalize_policy(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


__all__ = [
    "GATE_STATUS_BLOCKED",
    "GATE_STATUS_PASS",
    "QUALITY_STATUS_BLOCKED",
    "RAW_PRICE_REF_REQUIRED",
    "READER_REQUIRED_METADATA_FIELDS",
    "RESEARCH_ADJUSTMENT_POLICY_MISSING",
    "RESEARCH_ADJUSTMENT_POLICY_MISMATCH",
    "RESEARCH_ADJUSTMENT_POLICY_MIXED",
    "RESEARCH_ADJUSTMENT_POLICY_UNKNOWN",
    "UNPUBLISHED_CANDIDATE_BLOCKED",
    "AdjustedViewMetadata",
    "AdjustedViewResult",
    "QmtPolicyHandoff",
    "SinglePolicyGateResult",
    "assert_published_view_only",
    "build_qmt_policy_handoff",
    "read_adjusted_view",
    "single_policy_gate",
    "zero_operation_counts",
]
