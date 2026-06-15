"""CR025 semantic diff 合同。

本模块只定义 lightweight baseline 与 Backtrader-style reference 的离线
research comparison artifact。它不导入、不运行 Backtrader，也不触发
provider、lake、broker、QMT 或凭据相关操作。
"""

from __future__ import annotations

from dataclasses import dataclass, field, fields as dataclass_fields, is_dataclass
from datetime import date, datetime, timezone
import json
from pathlib import Path, PurePosixPath
import re
from typing import Any, Mapping, Sequence


SCHEMA_VERSION = "semantic_diff_v1"
ARTIFACT_TYPE = "research_comparison"
PROJECT_ROOT = Path(__file__).resolve().parents[1]
SEMANTIC_DIFF_REPORT_ROOT = PROJECT_ROOT / "reports" / "semantic_diff"

REQUIRED_FIELD_GROUPS = (
    "metadata",
    "availability",
    "fills",
    "cash_cost",
    "portfolio",
    "performance",
    "timeline",
    "explanation",
    "qmt_relevance",
    "limitations",
)

REQUIRED_METADATA_FIELDS = (
    "schema_version",
    "baseline_backend",
    "reference_backend",
    "generated_at",
    "source_run_id",
    "lineage",
)

FORBIDDEN_OPERATION_COUNTERS = (
    "provider_fetch",
    "lake_write",
    "catalog_publish",
    "credential_read",
    "qmt_operation",
    "broker_operation",
    "simulation_or_live",
    "backtrader_run",
    "backtrader_source_read",
    "backtrader_source_copy",
    "dependency_change",
    "multifactor_framework_implementation",
    "qlib_alphalens_vnpyalpha_integration",
)

FORBIDDEN_CLAIM_PHRASES = (
    "production truth",
    "default research truth",
    "simulation-ready",
    "qmt admission pass",
    "qmt simulation admission pass",
    "factor tear sheet",
    "ic / rankic report",
    "strategy admission package",
    "completed multifactor research framework",
)

FORBIDDEN_SCOPE_TERMS = (
    "FactorSpec",
    "FactorRunSpec",
    "IC / RankIC",
    "分层收益",
    "多因子组合",
    "实验追踪",
    "策略准入包",
    "Qlib",
    "Alphalens",
    "vnpy.alpha",
)


class SemanticDiffError(Exception):
    """semantic diff 基础异常。"""


class SemanticDiffInputError(SemanticDiffError):
    """输入不满足 artifact 构建条件。"""


class SemanticDiffPathError(SemanticDiffError):
    """artifact 输出路径越界。"""


class SemanticDiffValidationError(SemanticDiffError):
    """artifact 未通过 schema / claim / counter 校验。"""


@dataclass(frozen=True, slots=True)
class SemanticDiffViolation:
    code: str
    message: str
    severity: str = "blocker"
    field: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "message": self.message,
            "severity": self.severity,
            "field": self.field,
        }


@dataclass(frozen=True, slots=True)
class SemanticDiffClaimScanResult:
    passed: bool
    forbidden_claim_counts: dict[str, int]
    scope_term_counts: dict[str, int]
    violations: tuple[SemanticDiffViolation, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "forbidden_claim_counts": dict(self.forbidden_claim_counts),
            "scope_term_counts": dict(self.scope_term_counts),
            "violations": [violation.to_dict() for violation in self.violations],
        }


@dataclass(frozen=True, slots=True)
class SemanticDiffValidationResult:
    passed: bool
    violations: tuple[SemanticDiffViolation, ...] = ()
    forbidden_claim_counts: dict[str, int] = field(default_factory=dict)
    forbidden_operation_counts: dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "violations": [violation.to_dict() for violation in self.violations],
            "forbidden_claim_counts": dict(self.forbidden_claim_counts),
            "forbidden_operation_counts": dict(self.forbidden_operation_counts),
        }


@dataclass(frozen=True, slots=True)
class SemanticDiffWriteResult:
    path: Path
    bytes_written: int
    validation: SemanticDiffValidationResult

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": str(self.path.relative_to(PROJECT_ROOT)),
            "bytes_written": self.bytes_written,
            "validation": self.validation.to_dict(),
        }


@dataclass(frozen=True, slots=True)
class SemanticDiffArtifact:
    schema_version: str
    artifact_type: str
    metadata: dict[str, Any]
    availability: dict[str, Any]
    fills: dict[str, Any]
    cash_cost: dict[str, Any]
    portfolio: dict[str, Any]
    performance: dict[str, Any]
    timeline: dict[str, Any]
    explanation: dict[str, Any]
    qmt_relevance: dict[str, Any]
    limitations: list[Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "artifact_type": self.artifact_type,
            "metadata": _json_safe(self.metadata),
            "availability": _json_safe(self.availability),
            "fills": _json_safe(self.fills),
            "cash_cost": _json_safe(self.cash_cost),
            "portfolio": _json_safe(self.portfolio),
            "performance": _json_safe(self.performance),
            "timeline": _json_safe(self.timeline),
            "explanation": _json_safe(self.explanation),
            "qmt_relevance": _json_safe(self.qmt_relevance),
            "limitations": _json_safe(self.limitations),
        }


def build_semantic_diff(
    baseline_result: Mapping[str, Any] | Any,
    reference_result: Mapping[str, Any] | Any | None = None,
    selection_result: Mapping[str, Any] | Any | None = None,
    config: Mapping[str, Any] | None = None,
) -> SemanticDiffArtifact:
    """构建 semantic diff artifact，不运行 reference backend。"""

    if baseline_result is None:
        raise SemanticDiffInputError("baseline_result is required and cannot be replaced by reference_result")

    cfg = dict(config or {})
    selection = _metadata_from(selection_result)
    baseline_summary = _summarize_result(baseline_result)
    reference_summary = _summarize_result(reference_result) if reference_result is not None else {}
    reference_available = _reference_available(reference_result, selection, cfg)
    blocked_reasons = _blocked_reasons(selection, cfg, reference_available)
    limitations = _artifact_limitations(selection, cfg, reference_available)
    operation_counts = _forbidden_operation_counts(selection, cfg)

    source_run_id = str(cfg.get("source_run_id") or _value_from(baseline_result, "run_id", default="semantic-diff-fixture"))
    lineage = _lineage_from_inputs(baseline_result, selection, cfg)
    reference_backend = str(cfg.get("reference_backend") or ("backtrader_optional_reference" if reference_available else "unavailable"))
    metadata = {
        "schema_version": SCHEMA_VERSION,
        "baseline_backend": str(cfg.get("baseline_backend") or "lightweight"),
        "reference_backend": reference_backend,
        "generated_at": str(cfg.get("generated_at") or _utc_now_text()),
        "source_run_id": source_run_id,
        "lineage": lineage,
        "artifact_type": ARTIFACT_TYPE,
        "forbidden_operation_counts": operation_counts,
    }

    availability = {
        "baseline_available": True,
        "reference_available": reference_available,
        "availability_status": "available" if reference_available else "reference_unavailable",
        "blocked_reasons": blocked_reasons,
        "limitations": limitations,
    }
    fills = _build_fills_group(baseline_summary, reference_summary, reference_available, cfg)
    cash_cost = _build_cash_cost_group(baseline_summary, reference_summary, reference_available)
    portfolio = _build_portfolio_group(baseline_summary, reference_summary, reference_available)
    performance = _build_performance_group(baseline_summary, reference_summary, reference_available)
    timeline = _build_timeline_group(baseline_summary, reference_summary, reference_available)
    diff_reason = _diff_reasons(
        fills,
        cash_cost,
        portfolio,
        performance,
        timeline,
        reference_available=reference_available,
    )
    explanation = {
        "diff_reason": diff_reason,
        "severity": "warn" if reference_available else "info",
        "requires_follow_up": bool(reference_available and any(reason != "no_material_delta" for reason in diff_reason)),
        "qmt_relevance": "draft_relevance_only",
    }
    qmt_relevance = {
        "status": "draft_relevance_only",
        "consumable_by": ["order_intent_draft"],
        "requires_follow_up": explanation["requires_follow_up"],
        "limitations": limitations,
        "not_authorized_operations": [
            "broker_operation",
            "qmt_operation",
            "simulation_or_live",
            "credential_read",
        ],
    }

    return SemanticDiffArtifact(
        schema_version=SCHEMA_VERSION,
        artifact_type=ARTIFACT_TYPE,
        metadata=metadata,
        availability=availability,
        fills=fills,
        cash_cost=cash_cost,
        portfolio=portfolio,
        performance=performance,
        timeline=timeline,
        explanation=explanation,
        qmt_relevance=qmt_relevance,
        limitations=limitations,
    )


def validate_semantic_diff_artifact(
    artifact: SemanticDiffArtifact | Mapping[str, Any],
) -> SemanticDiffValidationResult:
    """校验 artifact schema、双轨、claim guard 和禁止操作计数。"""

    data = artifact.to_dict() if isinstance(artifact, SemanticDiffArtifact) else _json_safe(dict(artifact))
    violations: list[SemanticDiffViolation] = []

    missing_groups = [group for group in REQUIRED_FIELD_GROUPS if group not in data]
    for group in missing_groups:
        violations.append(SemanticDiffViolation("missing_field_group", f"missing field group: {group}", field=group))

    if data.get("schema_version") != SCHEMA_VERSION:
        violations.append(SemanticDiffViolation("schema_version_mismatch", "schema_version must be semantic_diff_v1", field="schema_version"))
    if data.get("artifact_type") != ARTIFACT_TYPE:
        violations.append(SemanticDiffViolation("artifact_type_invalid", "artifact_type must be research_comparison", field="artifact_type"))

    metadata = _dict_value(data.get("metadata"))
    for field_name in REQUIRED_METADATA_FIELDS:
        if field_name not in metadata:
            violations.append(SemanticDiffViolation("metadata_missing", f"metadata.{field_name} is required", field=f"metadata.{field_name}"))
    if metadata.get("baseline_backend") != "lightweight":
        violations.append(SemanticDiffViolation("baseline_backend_invalid", "baseline_backend must remain lightweight", field="metadata.baseline_backend"))
    if metadata.get("reference_backend") == metadata.get("baseline_backend"):
        violations.append(SemanticDiffViolation("baseline_reference_collapsed", "reference backend must not collapse into baseline backend", field="metadata.reference_backend"))

    availability = _dict_value(data.get("availability"))
    if availability.get("baseline_available") is not True:
        violations.append(SemanticDiffViolation("baseline_unavailable", "baseline is required and cannot be replaced", field="availability.baseline_available"))
    if availability.get("reference_available") is False and not _non_empty_sequence(availability.get("blocked_reasons")):
        violations.append(SemanticDiffViolation("reference_unavailable_without_reason", "reference unavailable must keep blocked reasons", field="availability.blocked_reasons"))
    if not _non_empty_sequence(availability.get("limitations")):
        violations.append(SemanticDiffViolation("availability_limitations_missing", "availability.limitations must be non-empty", field="availability.limitations"))
    if not _non_empty_sequence(data.get("limitations")):
        violations.append(SemanticDiffViolation("limitations_missing", "top-level limitations must be non-empty", field="limitations"))

    for group_name in ("fills", "cash_cost", "portfolio", "performance", "timeline"):
        group = _dict_value(data.get(group_name))
        if "reason" not in group and group.get("unavailable") is not True:
            violations.append(SemanticDiffViolation("reason_missing", f"{group_name} must include reason or unavailable", field=group_name))

    explanation = _dict_value(data.get("explanation"))
    if not _non_empty_sequence(explanation.get("diff_reason")):
        violations.append(SemanticDiffViolation("diff_reason_missing", "explanation.diff_reason must be non-empty", field="explanation.diff_reason"))

    operation_counts = _forbidden_operation_counts_from_artifact(data)
    for name, count in operation_counts.items():
        if count != 0:
            violations.append(SemanticDiffViolation("forbidden_operation_nonzero", f"{name} count must be 0", field=f"metadata.forbidden_operation_counts.{name}"))

    claim_scan = scan_semantic_diff_claims(data)
    violations.extend(claim_scan.violations)

    return SemanticDiffValidationResult(
        passed=not violations,
        violations=tuple(violations),
        forbidden_claim_counts=claim_scan.forbidden_claim_counts,
        forbidden_operation_counts=operation_counts,
    )


def resolve_semantic_diff_path(
    source_run_id: str,
    schema_version: str = SCHEMA_VERSION,
    output_root: str | Path | None = None,
) -> Path:
    """解析本地 artifact 路径，并限制在 reports/semantic_diff/**。"""

    root = _resolve_report_root(output_root)
    safe_run_id = _safe_slug(source_run_id)
    safe_schema_version = _safe_slug(schema_version)
    path = root / safe_schema_version / f"{safe_run_id}.json"
    return _ensure_report_path(path)


def write_semantic_diff_artifact(
    artifact: SemanticDiffArtifact | Mapping[str, Any],
    path: str | Path | None = None,
) -> SemanticDiffWriteResult:
    """写入本地 reports/semantic_diff artifact。"""

    data = artifact.to_dict() if isinstance(artifact, SemanticDiffArtifact) else _json_safe(dict(artifact))
    validation = validate_semantic_diff_artifact(data)
    if not validation.passed:
        raise SemanticDiffValidationError(json.dumps(validation.to_dict(), ensure_ascii=False, sort_keys=True))

    target = _ensure_report_path(
        Path(path) if path is not None else resolve_semantic_diff_path(str(_dict_value(data.get("metadata")).get("source_run_id", "semantic-diff-fixture")))
    )
    if target.suffix != ".json":
        raise SemanticDiffPathError("semantic diff artifact path must use .json suffix")
    payload = json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(payload, encoding="utf-8")
    return SemanticDiffWriteResult(path=target, bytes_written=len(payload.encode("utf-8")), validation=validation)


def scan_semantic_diff_claims(text_or_artifact: str | Mapping[str, Any] | SemanticDiffArtifact) -> SemanticDiffClaimScanResult:
    """扫描误导性声明与越界研究框架术语。"""

    text = _text_for_scan(text_or_artifact)
    normalized = text.lower()
    forbidden_claim_counts = {phrase: normalized.count(phrase) for phrase in FORBIDDEN_CLAIM_PHRASES}
    scope_term_counts = {term: text.count(term) for term in FORBIDDEN_SCOPE_TERMS}
    violations: list[SemanticDiffViolation] = []

    for phrase, count in forbidden_claim_counts.items():
        if count:
            violations.append(SemanticDiffViolation("forbidden_claim", f"forbidden claim phrase found: {phrase}", field="claims"))
    for term, count in scope_term_counts.items():
        if count:
            violations.append(SemanticDiffViolation("forbidden_scope_term", f"forbidden scope term found: {term}", field="scope"))

    return SemanticDiffClaimScanResult(
        passed=not violations,
        forbidden_claim_counts=forbidden_claim_counts,
        scope_term_counts=scope_term_counts,
        violations=tuple(violations),
    )


def zero_forbidden_operation_counts() -> dict[str, int]:
    return {name: 0 for name in FORBIDDEN_OPERATION_COUNTERS}


def _build_fills_group(
    baseline: Mapping[str, Any],
    reference: Mapping[str, Any],
    reference_available: bool,
    config: Mapping[str, Any],
) -> dict[str, Any]:
    unavailable = not reference_available
    return {
        "fill_count": _pair(baseline.get("fill_count", 0), reference.get("fill_count"), unavailable, "fill_count_delta"),
        "fill_timing": _pair(baseline.get("fill_timing"), reference.get("fill_timing"), unavailable, "fill_timing_delta"),
        "partial_fill_flag": _pair(baseline.get("partial_fill_flag", False), reference.get("partial_fill_flag"), unavailable, "partial_fill_delta"),
        "price_source": _pair(
            config.get("baseline_price_source", baseline.get("price_source", "lightweight_execution_price")),
            config.get("reference_price_source", reference.get("price_source") if reference else None),
            unavailable,
            "price_source_delta",
        ),
        "rounding_policy": _pair(
            config.get("baseline_rounding_policy", baseline.get("rounding_policy", "lightweight_default")),
            config.get("reference_rounding_policy", reference.get("rounding_policy") if reference else None),
            unavailable,
            "rounding_policy_delta",
        ),
        "reason": "reference_unavailable" if unavailable else _reason_for_values(baseline.get("fill_count", 0), reference.get("fill_count"), "fill_count_delta"),
        "unavailable": unavailable,
    }


def _build_cash_cost_group(baseline: Mapping[str, Any], reference: Mapping[str, Any], reference_available: bool) -> dict[str, Any]:
    unavailable = not reference_available
    fields = ("starting_cash", "ending_cash", "commission", "tax", "slippage", "cash_reconciliation")
    group = {field_name: _pair(baseline.get(field_name), reference.get(field_name), unavailable, f"{field_name}_delta") for field_name in fields}
    group["reason"] = "reference_unavailable" if unavailable else _first_delta_reason(group, "cash_cost_no_delta")
    group["unavailable"] = unavailable
    return group


def _build_portfolio_group(baseline: Mapping[str, Any], reference: Mapping[str, Any], reference_available: bool) -> dict[str, Any]:
    unavailable = not reference_available
    fields = ("holdings_delta", "position_sizing_delta", "turnover_delta", "net_value_delta")
    group = {field_name: _pair(baseline.get(field_name), reference.get(field_name), unavailable, f"{field_name}_reason") for field_name in fields}
    group["reason"] = "reference_unavailable" if unavailable else _first_delta_reason(group, "portfolio_no_delta")
    group["unavailable"] = unavailable
    return group


def _build_performance_group(baseline: Mapping[str, Any], reference: Mapping[str, Any], reference_available: bool) -> dict[str, Any]:
    unavailable = not reference_available
    fields = ("nav", "returns", "drawdown")
    group = {field_name: _pair(baseline.get(field_name), reference.get(field_name), unavailable, f"{field_name}_delta") for field_name in fields}
    group["reason"] = "reference_unavailable" if unavailable else _first_delta_reason(group, "performance_no_delta")
    group["unavailable"] = unavailable
    return group


def _build_timeline_group(baseline: Mapping[str, Any], reference: Mapping[str, Any], reference_available: bool) -> dict[str, Any]:
    unavailable = not reference_available
    baseline_events = baseline.get("timeline", [])
    reference_events = reference.get("timeline", []) if reference else []
    return {
        "events": _json_safe(baseline_events if unavailable else {"baseline": baseline_events, "reference": reference_events}),
        "baseline_event_count": _safe_len(baseline_events),
        "reference_event_count": None if unavailable else _safe_len(reference_events),
        "reason": "reference_unavailable" if unavailable else _reason_for_values(_safe_len(baseline_events), _safe_len(reference_events), "timeline_event_delta"),
        "unavailable": unavailable,
    }


def _diff_reasons(*groups: Mapping[str, Any], reference_available: bool) -> list[str]:
    if not reference_available:
        return ["reference_unavailable"]
    reasons = [str(group.get("reason")) for group in groups if group.get("reason")]
    return sorted(dict.fromkeys(reasons)) or ["no_material_delta"]


def _pair(baseline_value: Any, reference_value: Any, unavailable: bool, delta_reason: str) -> dict[str, Any]:
    if unavailable:
        return {
            "baseline": _json_safe(baseline_value),
            "reference": None,
            "delta": None,
            "reason": "reference_unavailable",
            "unavailable": True,
        }
    return {
        "baseline": _json_safe(baseline_value),
        "reference": _json_safe(reference_value),
        "delta": _json_safe(_delta(baseline_value, reference_value)),
        "reason": _reason_for_values(baseline_value, reference_value, delta_reason),
        "unavailable": False,
    }


def _reason_for_values(baseline_value: Any, reference_value: Any, delta_reason: str) -> str:
    return "no_material_delta" if baseline_value == reference_value else delta_reason


def _first_delta_reason(group: Mapping[str, Any], fallback: str) -> str:
    for item in group.values():
        if isinstance(item, Mapping) and item.get("reason") not in {None, "no_material_delta"}:
            return str(item["reason"])
    return fallback


def _delta(baseline_value: Any, reference_value: Any) -> Any:
    if isinstance(baseline_value, (int, float)) and isinstance(reference_value, (int, float)):
        return reference_value - baseline_value
    return None if baseline_value == reference_value else {"changed": True}


def _summarize_result(result: Mapping[str, Any] | Any) -> dict[str, Any]:
    data = _metadata_from(result)
    metrics = _dict_value(_value_from(result, "metrics", default=data.get("metrics", {})))
    portfolio = _dict_value(_value_from(result, "portfolio", default=_value_from(result, "portfolio_result", default=data.get("portfolio", {}))))
    fills = _value_from(result, "fills", default=_value_from(result, "trades", default=_value_from(result, "orders", default=data.get("fills", []))))
    summary = {
        "fill_count": _value_from(result, "fill_count", default=data.get("fill_count", _safe_len(fills))),
        "fill_timing": _value_from(result, "fill_timing", default=data.get("fill_timing")),
        "partial_fill_flag": _partial_fill_flag(fills, data),
        "price_source": data.get("price_source"),
        "rounding_policy": data.get("rounding_policy"),
        "starting_cash": _first_present(data.get("starting_cash"), metrics.get("starting_cash"), portfolio.get("starting_cash")),
        "ending_cash": _first_present(data.get("ending_cash"), metrics.get("ending_cash"), metrics.get("final_cash"), portfolio.get("ending_cash")),
        "commission": _first_present(data.get("commission"), metrics.get("commission"), portfolio.get("commission"), 0),
        "tax": _first_present(data.get("tax"), metrics.get("tax"), portfolio.get("tax"), 0),
        "slippage": _first_present(data.get("slippage"), metrics.get("slippage"), portfolio.get("slippage"), 0),
        "cash_reconciliation": _first_present(data.get("cash_reconciliation"), metrics.get("cash_reconciliation"), "not_provided"),
        "holdings_delta": _first_present(data.get("holdings_delta"), portfolio.get("holdings"), data.get("holdings"), {}),
        "position_sizing_delta": _first_present(data.get("position_sizing_delta"), portfolio.get("position_sizing"), data.get("position_sizing"), {}),
        "turnover_delta": _first_present(data.get("turnover_delta"), metrics.get("turnover"), portfolio.get("turnover"), 0),
        "net_value_delta": _first_present(data.get("net_value_delta"), metrics.get("final_value"), metrics.get("ending_value"), portfolio.get("final_value")),
        "nav": _first_present(data.get("nav"), metrics.get("nav"), metrics.get("cumulative_return")),
        "returns": _first_present(data.get("returns"), metrics.get("total_return"), metrics.get("cumulative_return")),
        "drawdown": _first_present(data.get("drawdown"), metrics.get("max_drawdown")),
        "timeline": _json_safe(_value_from(result, "timeline", default=data.get("timeline", data.get("events", [])))),
    }
    return summary


def _reference_available(reference_result: Any | None, selection: Mapping[str, Any], config: Mapping[str, Any]) -> bool:
    if config.get("reference_available") is False:
        return False
    if reference_result is None:
        return False
    selected_backend = selection.get("selected_backend")
    availability_status = selection.get("availability_status")
    if selected_backend in {"none", "lightweight"}:
        return False
    if availability_status and availability_status != "available":
        return False
    return True


def _blocked_reasons(selection: Mapping[str, Any], config: Mapping[str, Any], reference_available: bool) -> list[str]:
    reasons = list(_as_sequence(config.get("blocked_reasons"))) + list(_as_sequence(selection.get("blocked_reasons")))
    unavailable = _dict_value(selection.get("unavailable"))
    reasons.extend(_as_sequence(unavailable.get("reasons")))
    if not reference_available and not reasons:
        reasons.append("reference_unavailable:not_selected_or_missing")
    return [str(reason) for reason in dict.fromkeys(reason for reason in reasons if str(reason).strip())]


def _artifact_limitations(selection: Mapping[str, Any], config: Mapping[str, Any], reference_available: bool) -> list[Any]:
    limitations = list(_as_sequence(config.get("limitations"))) + list(_as_sequence(selection.get("limitations")))
    if not reference_available:
        limitations.append({"code": "reference_unavailable", "severity": "info"})
    limitations.append({"code": "research_comparison_only", "severity": "info"})
    return _json_safe([item for item in limitations if item not in ("", None)])


def _lineage_from_inputs(baseline_result: Any, selection: Mapping[str, Any], config: Mapping[str, Any]) -> dict[str, Any]:
    lineage = _dict_value(config.get("lineage"))
    baseline_lineage = _dict_value(_value_from(baseline_result, "lineage", default=_metadata_from(baseline_result).get("lineage", {})))
    selection_lineage = _dict_value(selection.get("lineage"))
    return _json_safe(
        {
            "baseline": baseline_lineage,
            "reference_selector": selection_lineage,
            **lineage,
        }
    )


def _forbidden_operation_counts(selection: Mapping[str, Any], config: Mapping[str, Any]) -> dict[str, int]:
    counts = zero_forbidden_operation_counts()
    for source in (_dict_value(selection.get("forbidden_operation_counts")), _dict_value(config.get("forbidden_operation_counts"))):
        for name, value in source.items():
            if name in counts:
                counts[name] = int(value)
    return counts


def _forbidden_operation_counts_from_artifact(data: Mapping[str, Any]) -> dict[str, int]:
    metadata = _dict_value(data.get("metadata"))
    return {**zero_forbidden_operation_counts(), **{name: int(value) for name, value in _dict_value(metadata.get("forbidden_operation_counts")).items() if name in FORBIDDEN_OPERATION_COUNTERS}}


def _resolve_report_root(output_root: str | Path | None) -> Path:
    if output_root is None:
        return SEMANTIC_DIFF_REPORT_ROOT
    root = Path(output_root)
    if not root.is_absolute():
        root = PROJECT_ROOT / root
    return _ensure_report_path(root)


def _ensure_report_path(path: Path) -> Path:
    candidate = path if path.is_absolute() else PROJECT_ROOT / path
    resolved_candidate = candidate.resolve()
    resolved_root = SEMANTIC_DIFF_REPORT_ROOT.resolve()
    try:
        resolved_candidate.relative_to(resolved_root)
    except ValueError as exc:
        raise SemanticDiffPathError("semantic diff artifact output must stay under reports/semantic_diff") from exc
    return resolved_candidate


def _safe_slug(value: str) -> str:
    text = PurePosixPath(str(value).replace("\\", "/")).name
    text = re.sub(r"[^A-Za-z0-9._-]+", "-", text).strip(".-")
    return text or "semantic-diff-artifact"


def _text_for_scan(text_or_artifact: str | Mapping[str, Any] | SemanticDiffArtifact) -> str:
    if isinstance(text_or_artifact, str):
        return text_or_artifact
    if isinstance(text_or_artifact, SemanticDiffArtifact):
        value = text_or_artifact.to_dict()
    else:
        value = dict(text_or_artifact)
    return json.dumps(_json_safe(value), ensure_ascii=False, sort_keys=True)


def _metadata_from(value: Any) -> dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, Mapping):
        return dict(value)
    if hasattr(value, "to_metadata") and callable(value.to_metadata):
        return _dict_value(value.to_metadata())
    if hasattr(value, "to_dict") and callable(value.to_dict):
        return _dict_value(value.to_dict())
    if is_dataclass(value):
        return {field_info.name: getattr(value, field_info.name) for field_info in dataclass_fields(value)}
    if hasattr(value, "__dict__"):
        return dict(vars(value))
    return {"value": value}


def _value_from(value: Any, key: str, default: Any = None) -> Any:
    if value is None:
        return default
    if isinstance(value, Mapping):
        return value.get(key, default)
    if hasattr(value, key):
        return getattr(value, key)
    metadata = _metadata_from(value)
    return metadata.get(key, default)


def _dict_value(value: Any) -> dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, Mapping):
        return dict(value)
    return _metadata_from(value)


def _as_sequence(value: Any) -> tuple[Any, ...]:
    if value is None:
        return ()
    if isinstance(value, tuple):
        return value
    if isinstance(value, list):
        return tuple(value)
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return tuple(value)
    return (value,)


def _non_empty_sequence(value: Any) -> bool:
    return bool([item for item in _as_sequence(value) if item not in ("", None)])


def _partial_fill_flag(fills: Any, data: Mapping[str, Any]) -> bool:
    if "partial_fill_flag" in data:
        return bool(data["partial_fill_flag"])
    for fill in _as_sequence(fills):
        fill_data = _dict_value(fill)
        if fill_data.get("partial_fill") is True or str(fill_data.get("status", "")).lower() == "partial":
            return True
    return False


def _safe_len(value: Any) -> int:
    if value is None:
        return 0
    try:
        return len(value)
    except TypeError:
        return 1


def _first_present(*values: Any) -> Any:
    for value in values:
        if value is not None:
            return value
    return None


def _utc_now_text() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _json_safe(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, tuple):
        return [_json_safe(item) for item in value]
    if isinstance(value, set):
        return sorted(_json_safe(item) for item in value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if is_dataclass(value):
        return _json_safe(_metadata_from(value))
    if hasattr(value, "to_dict") and callable(value.to_dict):
        return _json_safe(value.to_dict())
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    try:
        json.dumps(value)
        return value
    except TypeError:
        return repr(value)


__all__ = (
    "ARTIFACT_TYPE",
    "FORBIDDEN_CLAIM_PHRASES",
    "FORBIDDEN_OPERATION_COUNTERS",
    "FORBIDDEN_SCOPE_TERMS",
    "REQUIRED_FIELD_GROUPS",
    "REQUIRED_METADATA_FIELDS",
    "SCHEMA_VERSION",
    "SEMANTIC_DIFF_REPORT_ROOT",
    "SemanticDiffArtifact",
    "SemanticDiffClaimScanResult",
    "SemanticDiffError",
    "SemanticDiffInputError",
    "SemanticDiffPathError",
    "SemanticDiffValidationError",
    "SemanticDiffValidationResult",
    "SemanticDiffViolation",
    "SemanticDiffWriteResult",
    "build_semantic_diff",
    "resolve_semantic_diff_path",
    "scan_semantic_diff_claims",
    "validate_semantic_diff_artifact",
    "write_semantic_diff_artifact",
    "zero_forbidden_operation_counts",
)
