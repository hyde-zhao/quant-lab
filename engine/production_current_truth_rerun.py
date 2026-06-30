"""CR018-S08 production current truth research rerun dry-run contract.

本模块只组装 release-bound fixture / dry-run payload，不执行阶段三到阶段五
真实长任务，不读取凭据，不触发 provider fetch、lake write、catalog publish 或 QMT。
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any, Mapping, Sequence

from engine.research_dataset import (
    CR018_S08_OPERATION_COUNTERS,
    CR018_S08_REASON_CANDIDATE_INPUT_FORBIDDEN,
    CR018_S08_REASON_CATALOG_NOT_PUBLISHED,
    CR018_S08_REASON_PROXY_INPUT_FORBIDDEN,
    CR018_S08_REASON_REQUIRED_MISSING,
    CR018_S08_STATUS_BLOCKED,
    CR018_S08_STATUS_PASS,
    load_production_current_truth_dataset,
)


PRODUCTION_RERUN_REPORT_SCHEMA = "cr018.production_current_truth_rerun_report.v1"
QMT_ADMISSION_EVIDENCE_SCHEMA = "cr018.qmt_admission_evidence_from_s08.v1"
OLD_BASELINE_DIFF_SCHEMA = "cr018.old_proxy_fixed_baseline_diff.v1"
REQUIRED_RESEARCH_PHASES = ("phase_3", "phase_4", "phase_5")
RERUN_STATUS_FAIL = "fail"
RERUN_REASON_RESEARCH_PHASE_MISSING = "research_phase_missing"
RERUN_REASON_REQUEST_FIELD_MISSING = "request_field_missing"
RERUN_REASON_RERUN_FAILED = "rerun_failed"
RERUN_REASON_QMT_ADMISSION_BLOCKED = "qmt_admission_blocked_by_rerun"
RERUN_REASON_OLD_REPORT_OVERWRITE_FORBIDDEN = "old_report_overwrite_forbidden"
RERUN_REAL_OPERATION_COUNTER_KEYS = tuple(CR018_S08_OPERATION_COUNTERS)


@dataclass(frozen=True, slots=True)
class ProductionRerunRequest:
    """S08 release-bound research rerun 请求合同。"""

    release_id: str
    strategy_set: tuple[str, ...]
    research_phases: tuple[str, ...]
    research_adjustment_policy: str
    benchmark_policy: str
    as_of_trade_date: str = ""
    report_target: str = ""
    run_id: str = ""
    release_scope: Mapping[str, Any] | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "release_id", str(self.release_id or "").strip())
        object.__setattr__(
            self,
            "strategy_set",
            tuple(str(item).strip() for item in self.strategy_set if str(item).strip()),
        )
        object.__setattr__(
            self,
            "research_phases",
            tuple(str(item).strip() for item in self.research_phases if str(item).strip()),
        )
        object.__setattr__(
            self,
            "research_adjustment_policy",
            str(self.research_adjustment_policy or "").strip(),
        )
        object.__setattr__(self, "benchmark_policy", str(self.benchmark_policy or "").strip())
        object.__setattr__(self, "as_of_trade_date", str(self.as_of_trade_date or "").strip())
        object.__setattr__(self, "report_target", str(self.report_target or "").strip())
        object.__setattr__(self, "run_id", str(self.run_id or "").strip())


def production_current_truth_rerun_entry(
    request: ProductionRerunRequest | Mapping[str, Any],
    *,
    release_metadata: Mapping[str, Any] | None = None,
    current_truth_metadata: Mapping[str, Any] | None = None,
    current_reader_result: Mapping[str, Any] | Any | None = None,
    current_reader_metadata: Mapping[str, Any] | Any | None = None,
    p0_dataset_ids: Sequence[str] | None = None,
    current_pointers: Mapping[str, Any] | Sequence[Mapping[str, Any]] | None = None,
    candidate_path: str | Path | None = None,
    candidate_pointers: Mapping[str, Any] | Sequence[Mapping[str, Any]] | None = None,
    proxy_input: Mapping[str, Any] | Sequence[Any] | str | None = None,
    provider_raw_fallback: bool = False,
    required_missing: Sequence[Mapping[str, Any] | str] | None = None,
    research_results_fixture: Mapping[str, Any] | None = None,
    old_baseline_fixture: Mapping[str, Any] | None = None,
    existing_report_targets: Sequence[str | Path] = (),
    permission_counters: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """构建 S08 production rerun dry-run report payload。

    调用方必须显式提供已发布 release/current reader metadata 和研究结果
    fixture。本函数不会读取 report_target、旧报告、provider、lake、.env 或 QMT。
    """

    req = coerce_production_rerun_request(request)
    request_reasons = validate_rerun_request(req)
    dataset_bundle = load_production_current_truth_dataset(
        req.release_id,
        release_metadata=release_metadata,
        current_truth_metadata=current_truth_metadata,
        current_reader_result=current_reader_result,
        current_reader_metadata=current_reader_metadata,
        p0_dataset_ids=p0_dataset_ids,
        current_pointers=current_pointers,
        candidate_path=candidate_path,
        candidate_pointers=candidate_pointers,
        proxy_input=proxy_input,
        provider_raw_fallback=provider_raw_fallback,
        required_missing=required_missing,
        permission_counters=permission_counters,
    )
    overwrite_guard = old_report_overwrite_guard(
        req.report_target,
        existing_report_targets=existing_report_targets,
        release_id=req.release_id,
        run_id=req.run_id,
    )
    report_payload = build_rerun_report_payload(
        req,
        dataset_bundle=dataset_bundle,
        research_results_fixture=research_results_fixture,
        old_baseline_fixture=old_baseline_fixture,
        request_blocked_reasons=[*request_reasons, *overwrite_guard.get("blocked_reasons", [])],
        overwrite_guard=overwrite_guard,
    )
    report_payload["qmt_admission_evidence"] = build_qmt_admission_evidence(report_payload)
    return report_payload


def build_rerun_report_payload(
    request: ProductionRerunRequest | Mapping[str, Any],
    *,
    dataset_bundle: Mapping[str, Any],
    research_results_fixture: Mapping[str, Any] | None = None,
    old_baseline_fixture: Mapping[str, Any] | None = None,
    request_blocked_reasons: Sequence[Mapping[str, Any]] = (),
    overwrite_guard: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """组装 S08 rerun report payload，不执行真实研究。"""

    req = coerce_production_rerun_request(request)
    fixture = _plain_payload(research_results_fixture)
    baseline_diff = build_old_proxy_fixed_baseline_diff(
        old_baseline_fixture=old_baseline_fixture,
        research_results_fixture=fixture,
    )
    operation_counts = _merge_operation_counts(
        dataset_bundle.get("operation_counts") if isinstance(dataset_bundle, Mapping) else None,
        (overwrite_guard or {}).get("operation_counts") if isinstance(overwrite_guard, Mapping) else None,
    )
    blocked_reasons = _dedupe_payloads(
        [
            *list(dataset_bundle.get("blocked_reasons") or []),
            *list(request_blocked_reasons or []),
        ]
    )
    blocked_claims = _dedupe_payloads(
        [
            *list(dataset_bundle.get("blocked_claims") or []),
            *[
                item
                for item in blocked_reasons
                if isinstance(item, Mapping)
            ],
        ]
    )
    fixture_status = str(fixture.get("status") or RERUN_STATUS_FAIL).strip().lower()
    if blocked_reasons or dataset_bundle.get("status") == CR018_S08_STATUS_BLOCKED:
        status = CR018_S08_STATUS_BLOCKED
        passed = False
    elif fixture_status == CR018_S08_STATUS_PASS:
        status = CR018_S08_STATUS_PASS
        passed = True
    else:
        status = RERUN_STATUS_FAIL
        passed = False
        blocked_claims = _dedupe_payloads(
            [
                *blocked_claims,
                _blocked_reason(
                    RERUN_REASON_RERUN_FAILED,
                    "research_results_fixture",
                    "阶段三到阶段五 dry-run fixture 未 PASS，QMT admission 必须 blocked。",
                ),
            ]
        )

    return _json_safe(
        {
            "schema_name": PRODUCTION_RERUN_REPORT_SCHEMA,
            "mode": "fixture_dry_run",
            "fixture_only": True,
            "real_stage_3_to_5_execution": False,
            "release_id": req.release_id,
            "release_scope": _first_mapping(req.release_scope, dataset_bundle.get("release_scope")),
            "as_of_trade_date": req.as_of_trade_date or str(dataset_bundle.get("as_of_trade_date") or ""),
            "strategy_set": list(req.strategy_set),
            "research_phases": list(req.research_phases),
            "benchmark": _first_mapping(
                dataset_bundle.get("benchmark"),
                {"benchmark_policy": req.benchmark_policy},
            ),
            "benchmark_policy": req.benchmark_policy,
            "pit_universe": _first_mapping(dataset_bundle.get("pit_universe")),
            "tradability": _first_mapping(dataset_bundle.get("tradability")),
            "adjustment_policy": req.research_adjustment_policy
            or str(dataset_bundle.get("adjustment_policy") or ""),
            "dataset_bundle": dict(dataset_bundle),
            "research_results_fixture": fixture,
            "old_proxy_fixed_baseline_diff": baseline_diff,
            "blocked_claims": blocked_claims,
            "blocked_reasons": blocked_reasons,
            "report_target": {
                "requested": req.report_target,
                "guard": dict(overwrite_guard or {}),
                "old_report_overwrite_allowed": False,
            },
            "status": status,
            "pass": passed,
            "fail": status == RERUN_STATUS_FAIL,
            "production_rerun_allowed_count": 1 if passed else 0,
            "operation_counts": operation_counts,
            **operation_counts,
        }
    )


def build_qmt_admission_evidence(report_payload: Mapping[str, Any]) -> dict[str, Any]:
    """S09 只在 S08 PASS 后才能消费的 QMT admission evidence。"""

    status = str(report_payload.get("status") or "").strip().lower()
    passed = bool(report_payload.get("pass")) and status == CR018_S08_STATUS_PASS
    return _json_safe(
        {
            "schema_name": QMT_ADMISSION_EVIDENCE_SCHEMA,
            "release_id": str(report_payload.get("release_id") or ""),
            "rerun_status": status,
            "s08_pass": passed,
            "allowed": passed,
            "qmt_admission_allowed_count": 1 if passed else 0,
            "qmt_operation": 0,
            "blocked_reason": "" if passed else RERUN_REASON_QMT_ADMISSION_BLOCKED,
            "blocked_claims": [] if passed else list(report_payload.get("blocked_claims") or []),
            "evidence_paths": {
                "rerun_report": str(report_payload.get("report_target", {}).get("requested") or ""),
            },
        }
    )


def old_report_overwrite_guard(
    target_report_path: str | Path | None,
    *,
    existing_report_targets: Sequence[str | Path] = (),
    release_id: str = "",
    run_id: str = "",
) -> dict[str, Any]:
    """阻止覆盖旧报告；冲突时只给出 unique target 建议，不写文件。"""

    target = _normalize_target_path(target_report_path)
    existing = {_normalize_target_path(item) for item in existing_report_targets}
    operation_counts = dict(CR018_S08_OPERATION_COUNTERS)
    if not target:
        return {
            "status": "not_requested",
            "target_unique": False,
            "overwrite_allowed": False,
            "old_report_overwrite": 0,
            "operation_counts": operation_counts,
            "blocked_reasons": [],
        }
    if target in existing:
        return {
            "status": CR018_S08_STATUS_BLOCKED,
            "reason_code": RERUN_REASON_OLD_REPORT_OVERWRITE_FORBIDDEN,
            "target_unique": False,
            "requested_target": target,
            "unique_target": unique_report_target(target, release_id=release_id, run_id=run_id),
            "overwrite_allowed": False,
            "old_report_overwrite": 0,
            "operation_counts": operation_counts,
            "blocked_reasons": [
                _blocked_reason(
                    RERUN_REASON_OLD_REPORT_OVERWRITE_FORBIDDEN,
                    "report_target",
                    "S08 不允许覆盖旧 experiment 或旧 production report。",
                    {"requested_target": target},
                )
            ],
        }
    return {
        "status": "unique_target",
        "target_unique": True,
        "requested_target": target,
        "unique_target": target,
        "overwrite_allowed": False,
        "old_report_overwrite": 0,
        "operation_counts": operation_counts,
        "blocked_reasons": [],
    }


def unique_report_target(target_report_path: str | Path, *, release_id: str = "", run_id: str = "") -> str:
    target = _normalize_target_path(target_report_path)
    suffix_parts = [part for part in (release_id, run_id or "dry-run") if part]
    suffix = "-".join(_safe_slug(part) for part in suffix_parts) or "dry-run"
    path = Path(target)
    if path.suffix:
        return str(path.with_name(f"{path.stem}.{suffix}{path.suffix}"))
    return f"{target}.{suffix}"


def build_old_proxy_fixed_baseline_diff(
    *,
    old_baseline_fixture: Mapping[str, Any] | None = None,
    research_results_fixture: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """只对显式 fixture 做旧 proxy / fixed baseline 差异摘要。"""

    old = _plain_payload(old_baseline_fixture)
    new = _plain_payload(research_results_fixture)
    old_metrics = _plain_payload(old.get("metrics"))
    new_metrics = _plain_payload(new.get("metrics"))
    compared_keys = sorted(set(old_metrics) & set(new_metrics))
    metric_delta = {
        key: _numeric_delta(new_metrics.get(key), old_metrics.get(key))
        for key in compared_keys
        if _numeric_delta(new_metrics.get(key), old_metrics.get(key)) is not None
    }
    return _json_safe(
        {
            "schema_name": OLD_BASELINE_DIFF_SCHEMA,
            "old_proxy_baseline_present": bool(old.get("proxy_baseline")),
            "old_fixed_baseline_present": bool(old.get("fixed_baseline")),
            "old_baseline_policy": "comparison_only_not_production_input",
            "old_proxy_or_fixed_input_allowed": False,
            "proxy_input_allowed_count": 0,
            "compared_metrics": compared_keys,
            "metric_delta": metric_delta,
            "known_limitations": [
                "旧 proxy/fixed baseline 只用于差异摘要，不得作为 production current truth 输入。"
            ],
        }
    )


def validate_rerun_request(request: ProductionRerunRequest | Mapping[str, Any]) -> list[dict[str, Any]]:
    req = coerce_production_rerun_request(request)
    reasons: list[dict[str, Any]] = []
    if not req.release_id:
        reasons.append(
            _blocked_reason(
                RERUN_REASON_REQUEST_FIELD_MISSING,
                "release_id",
                "production rerun 必须提供 published release_id。",
            )
        )
    if not req.strategy_set:
        reasons.append(
            _blocked_reason(
                RERUN_REASON_REQUEST_FIELD_MISSING,
                "strategy_set",
                "production rerun 必须提供非空 strategy set。",
            )
        )
    missing_phases = [phase for phase in REQUIRED_RESEARCH_PHASES if phase not in req.research_phases]
    if missing_phases:
        reasons.append(
            _blocked_reason(
                RERUN_REASON_RESEARCH_PHASE_MISSING,
                "research_phases",
                "production rerun 必须覆盖 phase_3 / phase_4 / phase_5。",
                {"missing_phases": missing_phases},
            )
        )
    if not req.research_adjustment_policy:
        reasons.append(
            _blocked_reason(
                RERUN_REASON_REQUEST_FIELD_MISSING,
                "research_adjustment_policy",
                "production rerun 必须固定 research adjustment policy。",
            )
        )
    if not req.benchmark_policy:
        reasons.append(
            _blocked_reason(
                RERUN_REASON_REQUEST_FIELD_MISSING,
                "benchmark_policy",
                "production rerun 必须固定 benchmark policy。",
            )
        )
    return reasons


def coerce_production_rerun_request(
    request: ProductionRerunRequest | Mapping[str, Any],
) -> ProductionRerunRequest:
    if isinstance(request, ProductionRerunRequest):
        return request
    values = dict(request)
    return ProductionRerunRequest(
        release_id=str(values.get("release_id") or ""),
        strategy_set=tuple(values.get("strategy_set") or values.get("strategies") or ()),
        research_phases=tuple(values.get("research_phases") or values.get("phases") or ()),
        research_adjustment_policy=str(
            values.get("research_adjustment_policy") or values.get("adjustment_policy") or ""
        ),
        benchmark_policy=str(values.get("benchmark_policy") or ""),
        as_of_trade_date=str(values.get("as_of_trade_date") or ""),
        report_target=str(values.get("report_target") or ""),
        run_id=str(values.get("run_id") or ""),
        release_scope=values.get("release_scope") if isinstance(values.get("release_scope"), Mapping) else None,
    )


def assert_s08_real_operation_counts_zero(payload: Mapping[str, Any]) -> None:
    counts = dict(payload.get("operation_counts") or payload)
    observed = {key: int(counts.get(key, 0) or 0) for key in RERUN_REAL_OPERATION_COUNTER_KEYS}
    expected = {key: 0 for key in RERUN_REAL_OPERATION_COUNTER_KEYS}
    if observed != expected:
        raise AssertionError(f"S08 real operation counts must be zero: {observed!r}")


def _merge_operation_counts(*sources: Mapping[str, Any] | None) -> dict[str, int]:
    counters = dict(CR018_S08_OPERATION_COUNTERS)
    for source in sources:
        for key, value in dict(source or {}).items():
            if key in counters:
                counters[str(key)] = int(value or 0)
    return counters


def _blocked_reason(
    reason_code: str,
    field_name: str,
    message: str,
    details: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "reason_code": str(reason_code),
        "field": str(field_name),
        "status": CR018_S08_STATUS_BLOCKED,
        "message": str(message),
        "severity": "BLOCKING",
        "source_story": "CR018-S08",
        "details": _json_safe(dict(details or {})),
    }


def _normalize_target_path(value: str | Path | None) -> str:
    return str(value or "").strip()


def _safe_slug(value: str) -> str:
    return "".join(ch.lower() if ch.isalnum() else "-" for ch in str(value)).strip("-") or "dry-run"


def _first_mapping(*values: Any) -> dict[str, Any]:
    for value in values:
        if isinstance(value, Mapping):
            return _json_safe(dict(value))
    return {}


def _numeric_delta(new_value: Any, old_value: Any) -> float | None:
    try:
        return float(new_value) - float(old_value)
    except (TypeError, ValueError):
        return None


def _dedupe_payloads(items: Sequence[Any]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()
    for item in items:
        if not isinstance(item, Mapping):
            continue
        payload = _json_safe(dict(item))
        key = (
            str(payload.get("reason_code") or payload.get("claim") or ""),
            str(payload.get("field") or ""),
            str(payload.get("message") or ""),
        )
        if key in seen:
            continue
        seen.add(key)
        output.append(payload)
    return output


def _plain_payload(value: Any) -> dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, Mapping):
        return dict(value)
    if is_dataclass(value):
        return asdict(value)
    if hasattr(value, "to_dict"):
        return dict(value.to_dict())
    return {}


def _json_safe(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in value.items() if item is not None}
    if isinstance(value, tuple):
        return [_json_safe(item) for item in value]
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, set):
        return [_json_safe(item) for item in sorted(value)]
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    return value


__all__ = (
    "OLD_BASELINE_DIFF_SCHEMA",
    "PRODUCTION_RERUN_REPORT_SCHEMA",
    "QMT_ADMISSION_EVIDENCE_SCHEMA",
    "REQUIRED_RESEARCH_PHASES",
    "RERUN_REAL_OPERATION_COUNTER_KEYS",
    "RERUN_REASON_OLD_REPORT_OVERWRITE_FORBIDDEN",
    "RERUN_REASON_QMT_ADMISSION_BLOCKED",
    "RERUN_REASON_RESEARCH_PHASE_MISSING",
    "RERUN_REASON_RERUN_FAILED",
    "RERUN_STATUS_FAIL",
    "ProductionRerunRequest",
    "assert_s08_real_operation_counts_zero",
    "build_old_proxy_fixed_baseline_diff",
    "build_qmt_admission_evidence",
    "build_rerun_report_payload",
    "coerce_production_rerun_request",
    "old_report_overwrite_guard",
    "production_current_truth_rerun_entry",
    "unique_report_target",
    "validate_rerun_request",
)
