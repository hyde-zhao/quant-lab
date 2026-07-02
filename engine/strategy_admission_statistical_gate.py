"""CR151 metadata-only statistical admission gate contracts.

The module defines local fixture/static contracts for multifactor strategy
admission evidence. It only evaluates passed-in metadata objects and operation
counters; it does not read files, credentials, data lakes, NAS paths, providers,
runtime adapters, brokers, Git remotes, or external frameworks.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Mapping, Sequence

from engine.serialization import as_mapping, json_safe, safe_float


STATISTICAL_GATE_SCHEMA_VERSION = "strategy_admission_statistical_gate_v1"

STATISTICAL_GATE_FORBIDDEN_OPERATION_FIELDS = (
    "credential_read",
    "real_lake_read",
    "real_lake_write",
    "nas_access",
    "nas_read",
    "nas_write",
    "nas_sync_or_write",
    "provider_fetch",
    "qmt_runtime",
    "simulation_or_live_run",
    "runtime_operation",
    "broker_access",
    "trading_operation",
    "external_framework_run",
    "git_remote_write",
    "catalog_pointer_mutation",
)


class StatisticalGateStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    NEEDS_REVIEW = "NEEDS_REVIEW"
    BLOCKED = "BLOCKED"


@dataclass(frozen=True, slots=True)
class StatisticalValidationIssue:
    code: str
    severity: str
    message: str
    field: str = ""
    evidence_ref: str = ""

    def to_dict(self) -> dict[str, Any]:
        return dict(json_safe(asdict(self)))


@dataclass(frozen=True, slots=True)
class MultipleTestingReport:
    family_id: str
    candidate_count: int
    raw_p_values: tuple[float, ...]
    adjusted_p_values: tuple[float, ...]
    alpha: float
    method: str
    rejected_count: int
    report_ref: str = ""

    def to_dict(self) -> dict[str, Any]:
        return dict(json_safe(asdict(self)))


@dataclass(frozen=True, slots=True)
class RobustFactorStatisticsReport:
    metric_id: str
    sample_count: int
    ic_mean: float
    rank_ic_mean: float
    robust_t_stat: float
    p_value: float
    autocorrelation_lags: tuple[int, ...]
    report_ref: str = ""

    def to_dict(self) -> dict[str, Any]:
        return dict(json_safe(asdict(self)))


@dataclass(frozen=True, slots=True)
class WalkForwardValidationPlan:
    folds: int
    train_window: str
    validation_window: str
    oos_window: str
    embargo_days: int
    fold_metrics: tuple[Mapping[str, Any], ...]
    report_ref: str = ""

    def to_dict(self) -> dict[str, Any]:
        return dict(json_safe(asdict(self)))


@dataclass(frozen=True, slots=True)
class BacktestOverfitRiskReport:
    trial_count: int
    pbo: float
    dsr: float
    observed_sharpe: float
    skew: float
    kurtosis: float
    sample_length: int
    report_ref: str = ""

    def to_dict(self) -> dict[str, Any]:
        return dict(json_safe(asdict(self)))


@dataclass(frozen=True, slots=True)
class StatisticalGateThresholds:
    fdr_alpha: float = 0.05
    min_robust_t: float = 2.0
    max_p_value: float = 0.05
    min_oos_pass_rate: float = 0.67
    max_pbo: float = 0.2
    min_dsr: float = 0.0
    min_sample_count: int = 30

    def to_dict(self) -> dict[str, Any]:
        return dict(json_safe(asdict(self)))


@dataclass(frozen=True, slots=True)
class StrategyAdmissionStatisticalGate:
    status: StatisticalGateStatus | str
    report_refs: tuple[str, ...]
    blocked_reasons: tuple[StatisticalValidationIssue, ...] = ()
    needs_review_reasons: tuple[StatisticalValidationIssue, ...] = ()
    operation_counts: Mapping[str, int] = field(default_factory=dict)
    statistical_gate_ref: str = ""
    thresholds: StatisticalGateThresholds | Mapping[str, Any] = field(default_factory=StatisticalGateThresholds)
    schema_version: str = STATISTICAL_GATE_SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["status"] = _status_value(self.status)
        data["blocked_reasons"] = [issue.to_dict() for issue in self.blocked_reasons]
        data["needs_review_reasons"] = [issue.to_dict() for issue in self.needs_review_reasons]
        if isinstance(self.thresholds, StatisticalGateThresholds):
            data["thresholds"] = self.thresholds.to_dict()
        return dict(json_safe(data))


def default_statistical_gate_thresholds() -> StatisticalGateThresholds:
    """Return explicit fixture/static defaults for CR151 Wave A tests."""

    return StatisticalGateThresholds()


def validate_multiple_testing_report(report: MultipleTestingReport | Mapping[str, Any] | None) -> tuple[StatisticalValidationIssue, ...]:
    data = _as_mapping(report)
    issues: list[StatisticalValidationIssue] = []
    if not str(data.get("family_id") or "").strip():
        issues.append(_issue("statistical_multiple_testing_family_missing", "family_id", "Multiple-testing family id is required."))
    candidate_count = _as_int(data.get("candidate_count"))
    if candidate_count <= 0:
        issues.append(_issue("statistical_multiple_testing_candidate_count_invalid", "candidate_count", "candidate_count must be positive."))
    raw_p_values = _numeric_tuple(data.get("raw_p_values"))
    adjusted_p_values = _numeric_tuple(data.get("adjusted_p_values"))
    if not raw_p_values:
        issues.append(_issue("statistical_multiple_testing_raw_p_values_missing", "raw_p_values", "raw p-values are required."))
    if not adjusted_p_values:
        issues.append(_issue("statistical_multiple_testing_adjusted_p_values_missing", "adjusted_p_values", "adjusted p-values are required."))
    if candidate_count > 0 and raw_p_values and len(raw_p_values) != candidate_count:
        issues.append(
            _issue(
                "statistical_multiple_testing_raw_p_value_count_mismatch",
                "raw_p_values",
                "raw_p_values length must match candidate_count.",
            )
        )
    if candidate_count > 0 and adjusted_p_values and len(adjusted_p_values) != candidate_count:
        issues.append(
            _issue(
                "statistical_multiple_testing_adjusted_p_value_count_mismatch",
                "adjusted_p_values",
                "adjusted_p_values length must match candidate_count.",
            )
        )
    if raw_p_values and adjusted_p_values and len(raw_p_values) != len(adjusted_p_values):
        issues.append(
            _issue(
                "statistical_multiple_testing_p_value_pair_count_mismatch",
                "adjusted_p_values",
                "raw_p_values and adjusted_p_values lengths must match.",
            )
        )
    alpha = safe_float(data.get("alpha"))
    if alpha is None or not 0 < alpha <= 1:
        issues.append(_issue("statistical_multiple_testing_alpha_invalid", "alpha", "alpha must be in (0, 1]."))
    if not str(data.get("method") or "").strip():
        issues.append(_issue("statistical_multiple_testing_method_missing", "method", "multiple-testing method is required."))
    rejected_count = _as_int(data.get("rejected_count"), default=-1)
    if rejected_count < 0:
        issues.append(_issue("statistical_multiple_testing_rejected_count_invalid", "rejected_count", "rejected_count must be non-negative."))
    if candidate_count > 0 and rejected_count > candidate_count:
        issues.append(
            _issue(
                "statistical_multiple_testing_rejected_count_exceeds_candidates",
                "rejected_count",
                "rejected_count must not exceed candidate_count.",
            )
        )
    return tuple(issues)


def validate_robust_statistics_report(report: RobustFactorStatisticsReport | Mapping[str, Any] | None) -> tuple[StatisticalValidationIssue, ...]:
    data = _as_mapping(report)
    issues: list[StatisticalValidationIssue] = []
    if not str(data.get("metric_id") or "").strip():
        issues.append(_issue("statistical_robust_metric_id_missing", "metric_id", "robust statistics metric id is required."))
    if _as_int(data.get("sample_count")) <= 0:
        issues.append(_issue("statistical_robust_sample_count_invalid", "sample_count", "sample_count must be positive."))
    for field_name in ("ic_mean", "rank_ic_mean", "robust_t_stat", "p_value"):
        if safe_float(data.get(field_name)) is None:
            issues.append(_issue(f"statistical_robust_{field_name}_invalid", field_name, f"{field_name} must be numeric."))
    if not _sequence(data.get("autocorrelation_lags")):
        issues.append(_issue("statistical_robust_autocorrelation_lags_missing", "autocorrelation_lags", "autocorrelation_lags are required."))
    return tuple(issues)


def validate_walk_forward_plan(plan: WalkForwardValidationPlan | Mapping[str, Any] | None) -> tuple[StatisticalValidationIssue, ...]:
    data = _as_mapping(plan)
    issues: list[StatisticalValidationIssue] = []
    folds = _as_int(data.get("folds"))
    if folds <= 0:
        issues.append(_issue("statistical_walk_forward_folds_invalid", "folds", "folds must be positive."))
    for field_name in ("train_window", "validation_window", "oos_window"):
        if not str(data.get(field_name) or "").strip():
            issues.append(_issue(f"statistical_walk_forward_{field_name}_missing", field_name, f"{field_name} is required."))
    if _as_int(data.get("embargo_days"), default=-1) < 0:
        issues.append(_issue("statistical_walk_forward_embargo_invalid", "embargo_days", "embargo_days must be non-negative."))
    fold_metrics = _sequence(data.get("fold_metrics"))
    if not fold_metrics:
        issues.append(_issue("statistical_walk_forward_fold_metrics_missing", "fold_metrics", "fold_metrics are required."))
    return tuple(issues)


def validate_overfit_risk_report(report: BacktestOverfitRiskReport | Mapping[str, Any] | None) -> tuple[StatisticalValidationIssue, ...]:
    data = _as_mapping(report)
    issues: list[StatisticalValidationIssue] = []
    if _as_int(data.get("trial_count")) <= 0:
        issues.append(_issue("statistical_overfit_trial_count_invalid", "trial_count", "trial_count must be positive."))
    if _as_int(data.get("sample_length")) <= 0:
        issues.append(_issue("statistical_overfit_sample_length_invalid", "sample_length", "sample_length must be positive."))
    for field_name in ("pbo", "dsr", "observed_sharpe", "skew", "kurtosis"):
        if safe_float(data.get(field_name)) is None:
            issues.append(_issue(f"statistical_overfit_{field_name}_invalid", field_name, f"{field_name} must be numeric."))
    return tuple(issues)


def forbidden_operation_counts_zero(operation_counts: Mapping[str, Any] | None) -> tuple[StatisticalValidationIssue, ...]:
    normalized = _normalise_operation_counts(operation_counts)
    return tuple(
        StatisticalValidationIssue(
            code="statistical_gate_forbidden_operation_nonzero",
            severity="blocker",
            message=f"{key} counter must remain 0 for CR151 local/static validation.",
            field=key,
        )
        for key, value in normalized.items()
        if int(value) != 0
    )


def evaluate_strategy_admission_statistical_gate(
    *,
    multiple_testing_report: MultipleTestingReport | Mapping[str, Any] | None = None,
    robust_statistics_report: RobustFactorStatisticsReport | Mapping[str, Any] | None = None,
    walk_forward_plan: WalkForwardValidationPlan | Mapping[str, Any] | None = None,
    overfit_risk_report: BacktestOverfitRiskReport | Mapping[str, Any] | None = None,
    thresholds: StatisticalGateThresholds | Mapping[str, Any] | None = None,
    operation_counts: Mapping[str, Any] | None = None,
    report_refs: Sequence[str] | None = None,
    statistical_gate_ref: str = "",
) -> StrategyAdmissionStatisticalGate:
    """Evaluate CR151 Wave A reports with fail-closed status precedence."""

    threshold = _thresholds(thresholds)
    normalized_counts = _normalise_operation_counts(operation_counts)
    blocked: list[StatisticalValidationIssue] = list(forbidden_operation_counts_zero(normalized_counts))

    mandatory_reports = (
        ("multiple_testing_report", multiple_testing_report, validate_multiple_testing_report),
        ("robust_statistics_report", robust_statistics_report, validate_robust_statistics_report),
        ("walk_forward_plan", walk_forward_plan, validate_walk_forward_plan),
        ("overfit_risk_report", overfit_risk_report, validate_overfit_risk_report),
    )
    for field_name, report, validator in mandatory_reports:
        if report is None or not _as_mapping(report):
            blocked.append(_issue(f"statistical_gate_{field_name}_missing", field_name, f"{field_name} is mandatory."))
            continue
        blocked.extend(validator(report))

    hard_fail: list[StatisticalValidationIssue] = []
    needs_review: list[StatisticalValidationIssue] = []
    if not blocked:
        hard_fail.extend(_hard_threshold_issues(multiple_testing_report, robust_statistics_report, walk_forward_plan, overfit_risk_report, threshold))
        needs_review.extend(_needs_review_issues(robust_statistics_report, threshold))

    if blocked:
        status = StatisticalGateStatus.BLOCKED
    elif hard_fail:
        status = StatisticalGateStatus.FAIL
        blocked.extend(hard_fail)
    elif needs_review:
        status = StatisticalGateStatus.NEEDS_REVIEW
    else:
        status = StatisticalGateStatus.PASS

    return StrategyAdmissionStatisticalGate(
        status=status,
        report_refs=_collect_report_refs(
            (multiple_testing_report, robust_statistics_report, walk_forward_plan, overfit_risk_report),
            report_refs,
        ),
        blocked_reasons=tuple(blocked),
        needs_review_reasons=tuple(needs_review),
        operation_counts=normalized_counts,
        statistical_gate_ref=str(statistical_gate_ref or ""),
        thresholds=threshold,
    )


def _hard_threshold_issues(
    multiple_testing_report: MultipleTestingReport | Mapping[str, Any] | None,
    robust_statistics_report: RobustFactorStatisticsReport | Mapping[str, Any] | None,
    walk_forward_plan: WalkForwardValidationPlan | Mapping[str, Any] | None,
    overfit_risk_report: BacktestOverfitRiskReport | Mapping[str, Any] | None,
    thresholds: StatisticalGateThresholds,
) -> tuple[StatisticalValidationIssue, ...]:
    issues: list[StatisticalValidationIssue] = []
    multiple = _as_mapping(multiple_testing_report)
    adjusted = _numeric_tuple(multiple.get("adjusted_p_values"))
    rejected_count = _as_int(multiple.get("rejected_count"))
    alpha = safe_float(multiple.get("alpha")) or thresholds.fdr_alpha
    effective_alpha = min(float(alpha), thresholds.fdr_alpha)
    if rejected_count <= 0 and not any(value <= effective_alpha for value in adjusted):
        issues.append(_fail_issue("statistical_gate_fdr_no_rejections", "adjusted_p_values", "No adjusted p-value passes the FDR alpha threshold."))

    robust = _as_mapping(robust_statistics_report)
    robust_t = abs(safe_float(robust.get("robust_t_stat")) or 0.0)
    p_value = safe_float(robust.get("p_value"))
    if robust_t < thresholds.min_robust_t:
        issues.append(_fail_issue("statistical_gate_robust_t_below_threshold", "robust_t_stat", "robust t-statistic is below threshold."))
    if p_value is None or p_value > thresholds.max_p_value:
        issues.append(_fail_issue("statistical_gate_p_value_above_threshold", "p_value", "robust p-value exceeds threshold."))

    pass_rate = _walk_forward_pass_rate(walk_forward_plan)
    if pass_rate < thresholds.min_oos_pass_rate:
        issues.append(_fail_issue("statistical_gate_oos_pass_rate_below_threshold", "fold_metrics", "walk-forward OOS pass rate is below threshold."))

    overfit = _as_mapping(overfit_risk_report)
    pbo = safe_float(overfit.get("pbo"))
    dsr = safe_float(overfit.get("dsr"))
    if pbo is None or pbo > thresholds.max_pbo:
        issues.append(_fail_issue("statistical_gate_pbo_above_threshold", "pbo", "PBO exceeds threshold."))
    if dsr is None or dsr < thresholds.min_dsr:
        issues.append(_fail_issue("statistical_gate_dsr_below_threshold", "dsr", "DSR is below threshold."))
    return tuple(issues)


def _needs_review_issues(
    robust_statistics_report: RobustFactorStatisticsReport | Mapping[str, Any] | None,
    thresholds: StatisticalGateThresholds,
) -> tuple[StatisticalValidationIssue, ...]:
    robust = _as_mapping(robust_statistics_report)
    if _as_int(robust.get("sample_count")) < thresholds.min_sample_count:
        return (
            StatisticalValidationIssue(
                code="statistical_gate_sample_count_below_review_threshold",
                severity="warning",
                message="sample_count is present but below the CR151 fixture review threshold.",
                field="sample_count",
            ),
        )
    return ()


def _walk_forward_pass_rate(plan: WalkForwardValidationPlan | Mapping[str, Any] | None) -> float:
    fold_metrics = _sequence(_as_mapping(plan).get("fold_metrics"))
    if not fold_metrics:
        return 0.0
    passed = 0
    for metric in fold_metrics:
        item = _as_mapping(metric)
        if bool(item.get("passed")):
            passed += 1
            continue
        status = str(item.get("status") or "").strip().lower()
        if status == "pass":
            passed += 1
    return passed / len(fold_metrics)


def _collect_report_refs(reports: Sequence[Any], explicit_refs: Sequence[str] | None) -> tuple[str, ...]:
    refs: list[str] = [str(item) for item in explicit_refs or () if str(item)]
    for report in reports:
        ref = str(_as_mapping(report).get("report_ref") or "")
        if ref:
            refs.append(ref)
    return tuple(dict.fromkeys(refs))


def _thresholds(value: StatisticalGateThresholds | Mapping[str, Any] | None) -> StatisticalGateThresholds:
    if value is None:
        return default_statistical_gate_thresholds()
    if isinstance(value, StatisticalGateThresholds):
        return value
    data = as_mapping(value, none_as_empty=True) or {}
    default = default_statistical_gate_thresholds()
    return StatisticalGateThresholds(
        fdr_alpha=float(data.get("fdr_alpha", default.fdr_alpha)),
        min_robust_t=float(data.get("min_robust_t", default.min_robust_t)),
        max_p_value=float(data.get("max_p_value", default.max_p_value)),
        min_oos_pass_rate=float(data.get("min_oos_pass_rate", default.min_oos_pass_rate)),
        max_pbo=float(data.get("max_pbo", default.max_pbo)),
        min_dsr=float(data.get("min_dsr", default.min_dsr)),
        min_sample_count=int(data.get("min_sample_count", default.min_sample_count)),
    )


def _normalise_operation_counts(operation_counts: Mapping[str, Any] | None) -> dict[str, int]:
    source = dict(operation_counts or {})
    keys = tuple(dict.fromkeys((*STATISTICAL_GATE_FORBIDDEN_OPERATION_FIELDS, *tuple(str(key) for key in source))))
    normalized: dict[str, int] = {}
    for key in keys:
        try:
            normalized[key] = int(source.get(key, 0) or 0)
        except (TypeError, ValueError):
            normalized[key] = 1
    return normalized


def _as_mapping(value: Any) -> dict[str, Any]:
    return as_mapping(value, none_as_empty=True) or {}


def _sequence(value: Any) -> tuple[Any, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        return (value,) if value else ()
    if isinstance(value, Mapping):
        return (value,)
    if isinstance(value, Sequence):
        return tuple(value)
    return (value,)


def _numeric_tuple(value: Any) -> tuple[float, ...]:
    result: list[float] = []
    for item in _sequence(value):
        numeric = safe_float(item)
        if numeric is not None:
            result.append(numeric)
    return tuple(result)


def _as_int(value: Any, *, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _status_value(value: Any) -> str:
    return str(value.value if hasattr(value, "value") else value)


def _issue(code: str, field: str, message: str) -> StatisticalValidationIssue:
    return StatisticalValidationIssue(code=code, severity="blocker", message=message, field=field)


def _fail_issue(code: str, field: str, message: str) -> StatisticalValidationIssue:
    return StatisticalValidationIssue(code=code, severity="fail", message=message, field=field)
