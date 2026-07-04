"""CR155 daily multifactor baseline strategy artifact contracts.

The module evaluates passed-in refs and metadata only. It does not read data
lakes, credentials, NAS paths, providers, runtime adapters, brokers, catalogs,
registries, or external frameworks.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, is_dataclass
from enum import Enum
from typing import Any, Mapping, Sequence

from engine.serialization import as_mapping, is_blank, json_safe, normalise_permission_counters, safe_float


DAILY_MULTIFACTOR_BASELINE_SCHEMA_VERSION = "daily_multifactor_baseline_artifact_v1"

FORBIDDEN_PROVENANCE_OPERATION_FIELDS = (
    "credential_read",
    "env_read",
    "real_lake_write",
    "catalog_pointer_mutation",
    "nas_operation",
    "nas_read",
    "nas_write",
    "nas_sync",
    "provider_fetch",
    "runtime_operation",
    "qmt_runtime",
    "miniqmt_runtime",
    "xtquant_runtime",
    "simulation_or_live_run",
    "trading_operation",
    "broker_operation",
    "external_framework_run",
    "store_write",
    "registry_write",
    "catalog_or_registry_write",
    "publish_operation",
    "production_deployment",
)

REQUIRED_RERUN_METRICS = (
    "total_return",
    "max_drawdown",
    "turnover",
    "cost",
    "capacity_liquidity_summary",
)

NON_AUTHORIZATION_WORDING = (
    "research artifact only",
    "does not authorize paper trading",
    "does not authorize live trading",
    "does not authorize runtime execution",
    "does not authorize broker operation",
    "does not authorize production deployment",
    "does not authorize publish or registry promotion",
)

OVERCLAIM_TERMS = (
    "paper-ready",
    "paper ready",
    "paper readiness",
    "live-ready",
    "live ready",
    "live readiness",
    "trading-ready",
    "trading ready",
    "trading readiness",
    "runtime-ready",
    "runtime ready",
    "runtime readiness",
    "production-ready",
    "production ready",
    "production readiness",
    "broker-ready",
    "broker ready",
    "qmt-ready",
    "deploy-ready",
    "deployable to production",
)


class ArtifactStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    NEEDS_REVIEW = "NEEDS_REVIEW"
    BLOCKED = "BLOCKED"


@dataclass(frozen=True, slots=True)
class ValidationIssue:
    code: str
    severity: str
    message: str
    field: str = ""
    evidence_ref: str = ""

    def to_dict(self) -> dict[str, Any]:
        return dict(_sorted_json_safe(asdict(self)))


@dataclass(frozen=True, slots=True)
class ContractValidationResult:
    status: ArtifactStatus | str
    issues: tuple[ValidationIssue, ...] = ()
    evidence_refs: tuple[str, ...] = ()
    schema_version: str = DAILY_MULTIFACTOR_BASELINE_SCHEMA_VERSION

    @property
    def passed(self) -> bool:
        return _status_value(self.status) == ArtifactStatus.PASS.value

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["status"] = _status_value(self.status)
        data["issues"] = [issue.to_dict() for issue in self.issues]
        data["passed"] = self.passed
        return dict(_sorted_json_safe(data))


@dataclass(frozen=True, slots=True)
class DailyMultifactorBaselineArtifact:
    strategy_id: str
    universe_ref: str
    factor_specs: tuple[Mapping[str, Any], ...]
    signal_spec: Mapping[str, Any]
    portfolio_policy: Mapping[str, Any]
    validation_refs: Mapping[str, Any]
    admission_refs: Mapping[str, Any]
    claim_boundary: tuple[str, ...]
    schema_version: str = DAILY_MULTIFACTOR_BASELINE_SCHEMA_VERSION
    rerun_refs: Mapping[str, Any] = field(default_factory=dict)
    evidence_refs: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return artifact_to_json_dict(self)


@dataclass(frozen=True, slots=True)
class ReadonlyDataProvenance:
    input_refs: tuple[str, ...]
    read_scope: Mapping[str, Any]
    operation_counts: Mapping[str, int] = field(default_factory=dict)
    fallback_mode: str = ""
    notes: tuple[str, ...] = ()
    evidence_refs: tuple[str, ...] = ()
    schema_version: str = DAILY_MULTIFACTOR_BASELINE_SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        return dict(_sorted_json_safe(asdict(self)))


@dataclass(frozen=True, slots=True)
class HistoricalBacktestRef:
    run_ref: str
    report_ref: str
    cost_ref: str
    risk_ref: str
    evidence_refs: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return dict(_sorted_json_safe(asdict(self)))


@dataclass(frozen=True, slots=True)
class WalkForwardSplitManifest:
    folds: tuple[Mapping[str, Any], ...]
    purge_policy_ref: str
    embargo_days: int | None
    manifest_ref: str = ""
    evidence_refs: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return dict(_sorted_json_safe(asdict(self)))


@dataclass(frozen=True, slots=True)
class ValidationMetrics:
    total_return: float
    max_drawdown: float
    turnover: float
    cost: float
    capacity_liquidity_summary: str
    evidence_refs: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return dict(_sorted_json_safe(asdict(self)))


@dataclass(frozen=True, slots=True)
class BaselineValidationSummary:
    status: ArtifactStatus | str
    artifact_status: ArtifactStatus | str
    provenance_status: ArtifactStatus | str
    split_manifest_status: ArtifactStatus | str
    historical_backtest_ref: HistoricalBacktestRef | Mapping[str, Any]
    split_manifest: WalkForwardSplitManifest | Mapping[str, Any]
    metrics: ValidationMetrics | Mapping[str, Any]
    real_data_claim_allowed: bool
    reasons: tuple[ValidationIssue, ...] = ()
    evidence_refs: tuple[str, ...] = ()
    schema_version: str = DAILY_MULTIFACTOR_BASELINE_SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        for key in ("status", "artifact_status", "provenance_status", "split_manifest_status"):
            data[key] = _status_value(data[key])
        data["historical_backtest_ref"] = _mapping_or_dataclass_dict(self.historical_backtest_ref)
        data["split_manifest"] = _mapping_or_dataclass_dict(self.split_manifest)
        data["metrics"] = _mapping_or_dataclass_dict(self.metrics)
        data["reasons"] = [reason.to_dict() for reason in self.reasons]
        return dict(_sorted_json_safe(data))


@dataclass(frozen=True, slots=True)
class GateDecision:
    status: ArtifactStatus | str
    reasons: tuple[str, ...] = ()
    evidence_refs: tuple[str, ...] = ()
    gate_ref: str = ""

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["status"] = _status_value(self.status)
        return dict(_sorted_json_safe(data))


@dataclass(frozen=True, slots=True)
class DailyMultifactorAdmissionPackage:
    strategy_id: str
    package_status: ArtifactStatus | str
    paper_candidate: bool
    validation_status: ArtifactStatus | str
    statistical_gate: GateDecision | Mapping[str, Any]
    reliability_gate: GateDecision | Mapping[str, Any]
    blockers: tuple[str, ...]
    risks: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    non_authorization: tuple[str, ...] = NON_AUTHORIZATION_WORDING
    schema_version: str = DAILY_MULTIFACTOR_BASELINE_SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        for key in ("package_status", "validation_status"):
            data[key] = _status_value(data[key])
        data["statistical_gate"] = _mapping_or_dataclass_dict(self.statistical_gate)
        data["reliability_gate"] = _mapping_or_dataclass_dict(self.reliability_gate)
        return dict(_sorted_json_safe(data))


@dataclass(frozen=True, slots=True)
class MetricTolerance:
    numeric_tolerance: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return dict(_sorted_json_safe(asdict(self)))


@dataclass(frozen=True, slots=True)
class RerunMetricSnapshot:
    run_ref: str
    metrics: Mapping[str, Any]
    admission_status: ArtifactStatus | str
    evidence_refs: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["admission_status"] = _status_value(self.admission_status)
        return dict(_sorted_json_safe(data))


@dataclass(frozen=True, slots=True)
class RerunConsistencyReport:
    status: ArtifactStatus | str
    drift_reasons: tuple[str, ...]
    compared_metrics: Mapping[str, Any]
    tolerance: MetricTolerance | Mapping[str, Any]
    snapshot_refs: tuple[str, str]
    admission_status_match: bool
    schema_version: str = DAILY_MULTIFACTOR_BASELINE_SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["status"] = _status_value(self.status)
        data["tolerance"] = _mapping_or_dataclass_dict(self.tolerance)
        return dict(_sorted_json_safe(data))


def build_claim_boundary(strategy_id: str, extra: Sequence[str] = ()) -> tuple[str, ...]:
    strategy = str(strategy_id or "").strip() or "daily_multifactor_baseline"
    return (
        f"{strategy} is a research baseline artifact only.",
        "It is a simple non-optimal daily multifactor factor combination.",
        "It does not authorize paper, live, trading, runtime, broker, publish or production use.",
        *tuple(str(item) for item in extra if str(item).strip()),
    )


def artifact_to_json_dict(artifact: DailyMultifactorBaselineArtifact | Mapping[str, Any]) -> dict[str, Any]:
    return dict(_sorted_json_safe(_mapping_or_dataclass_dict(artifact)))


def validate_baseline_artifact(
    artifact: DailyMultifactorBaselineArtifact | Mapping[str, Any] | None,
    *,
    require_rerun_refs: bool = False,
) -> ContractValidationResult:
    data = _as_mapping(artifact)
    issues: list[ValidationIssue] = []
    for field_name in ("strategy_id", "schema_version", "universe_ref"):
        if is_blank(data.get(field_name)):
            issues.append(_issue("artifact_required_field_missing", field_name, f"{field_name} is required.", "BLOCKER"))
    for field_name in ("signal_spec", "portfolio_policy", "validation_refs", "admission_refs"):
        if is_blank(data.get(field_name)):
            issues.append(_issue("artifact_required_ref_group_missing", field_name, f"{field_name} is required.", "BLOCKER"))
    if is_blank(data.get("factor_specs")):
        issues.append(_issue("artifact_factor_specs_missing", "factor_specs", "factor_specs must be non-empty.", "BLOCKER"))
    if require_rerun_refs and is_blank(data.get("rerun_refs")):
        issues.append(_issue("artifact_rerun_refs_missing", "rerun_refs", "rerun_refs are required for final package.", "BLOCKER"))

    claim_boundary = _text_items(data.get("claim_boundary"))
    if not claim_boundary:
        issues.append(_issue("artifact_claim_boundary_missing", "claim_boundary", "claim_boundary is required.", "BLOCKER"))
    else:
        issues.extend(_overclaim_issues(claim_boundary, field="claim_boundary"))

    return _result_from_issues(issues, evidence_refs=_sequence_of_str(data.get("evidence_refs")))


def validate_readonly_provenance(provenance: ReadonlyDataProvenance | Mapping[str, Any] | None) -> ContractValidationResult:
    data = _as_mapping(provenance)
    issues: list[ValidationIssue] = []
    counters = normalise_permission_counters(data.get("operation_counts"), FORBIDDEN_PROVENANCE_OPERATION_FIELDS)
    nonzero = [key for key, value in counters.items() if value != 0]
    if nonzero:
        issues.append(
            _issue(
                "readonly_provenance_forbidden_operation",
                "operation_counts",
                f"Forbidden operation counters must remain zero: {', '.join(nonzero)}.",
                "BLOCKER",
            )
        )
    if is_blank(data.get("input_refs")):
        issues.append(_issue("readonly_provenance_input_refs_missing", "input_refs", "input_refs are required.", "BLOCKER"))
    if is_blank(data.get("read_scope")):
        issues.append(_issue("readonly_provenance_read_scope_missing", "read_scope", "read_scope is required.", "BLOCKER"))

    fallback_mode = str(data.get("fallback_mode") or "").strip()
    if fallback_mode == "fixture_static" and not nonzero:
        issues.append(
            _issue(
                "readonly_provenance_fixture_static_fallback",
                "fallback_mode",
                "fixture_static fallback blocks real-data baseline wording.",
                "MEDIUM",
            )
        )
    return _result_from_issues(issues, evidence_refs=_sequence_of_str(data.get("evidence_refs")))


def build_provenance_summary(provenance: ReadonlyDataProvenance | Mapping[str, Any]) -> dict[str, Any]:
    data = _as_mapping(provenance)
    result = validate_readonly_provenance(data)
    fallback_mode = str(data.get("fallback_mode") or "").strip()
    return dict(
        _sorted_json_safe(
            {
                "status": _status_value(result.status),
                "claim_allowed": result.passed and fallback_mode != "fixture_static",
                "input_refs": _sequence_of_str(data.get("input_refs")),
                "read_scope": data.get("read_scope") or {},
                "fallback_mode": fallback_mode,
                "operation_counts": normalise_permission_counters(data.get("operation_counts"), FORBIDDEN_PROVENANCE_OPERATION_FIELDS),
                "issues": [issue.to_dict() for issue in result.issues],
                "evidence_refs": _sequence_of_str(data.get("evidence_refs")),
            }
        )
    )


def downgrade_to_fixture_static(reason: str, *, evidence_refs: Sequence[str] = ()) -> ReadonlyDataProvenance:
    return ReadonlyDataProvenance(
        input_refs=("fixture://daily-multifactor-baseline/static",),
        read_scope={"purpose": "CR155 fixture/static fallback", "real_data_claim_allowed": False},
        operation_counts={key: 0 for key in FORBIDDEN_PROVENANCE_OPERATION_FIELDS},
        fallback_mode="fixture_static",
        notes=(str(reason),),
        evidence_refs=tuple(str(ref) for ref in evidence_refs),
    )


def validate_split_manifest(manifest: WalkForwardSplitManifest | Mapping[str, Any] | None) -> ContractValidationResult:
    data = _as_mapping(manifest)
    issues: list[ValidationIssue] = []
    folds = _sequence(data.get("folds"))
    if not folds:
        issues.append(_issue("walk_forward_folds_missing", "folds", "folds are required.", "BLOCKER"))
    for index, fold in enumerate(folds):
        fold_data = _as_mapping(fold)
        for field_name in ("fold_id", "train_start", "train_end", "test_start", "test_end", "metrics_ref"):
            if is_blank(fold_data.get(field_name)):
                issues.append(
                    _issue(
                        "walk_forward_fold_field_missing",
                        f"folds[{index}].{field_name}",
                        f"{field_name} is required for each walk-forward fold.",
                        "BLOCKER",
                    )
                )
    if is_blank(data.get("purge_policy_ref")):
        issues.append(_issue("walk_forward_purge_policy_missing", "purge_policy_ref", "purge_policy_ref is required.", "BLOCKER"))
    embargo_days = data.get("embargo_days")
    if embargo_days is None or _as_int(embargo_days, default=-1) < 0:
        issues.append(_issue("walk_forward_embargo_days_invalid", "embargo_days", "embargo_days must be non-negative.", "BLOCKER"))
    return _result_from_issues(issues, evidence_refs=_sequence_of_str(data.get("evidence_refs")))


def build_validation_summary(
    artifact: DailyMultifactorBaselineArtifact | Mapping[str, Any],
    provenance: ReadonlyDataProvenance | Mapping[str, Any],
    historical_backtest_ref: HistoricalBacktestRef | Mapping[str, Any],
    split_manifest: WalkForwardSplitManifest | Mapping[str, Any],
    metrics: ValidationMetrics | Mapping[str, Any],
) -> BaselineValidationSummary:
    artifact_result = validate_baseline_artifact(artifact)
    provenance_result = validate_readonly_provenance(provenance)
    split_result = validate_split_manifest(split_manifest)
    backtest_issues = _validate_historical_backtest_ref(historical_backtest_ref)
    metric_issues = _validate_metrics(metrics)
    reasons = [*artifact_result.issues, *provenance_result.issues, *split_result.issues, *backtest_issues, *metric_issues]
    status = _status_from_child_statuses(
        (
            artifact_result.status,
            provenance_result.status,
            split_result.status,
            _status_from_issues(backtest_issues),
            _status_from_issues(metric_issues),
        )
    )
    provenance_data = _as_mapping(provenance)
    real_data_claim_allowed = (
        _status_value(provenance_result.status) == ArtifactStatus.PASS.value
        and str(provenance_data.get("fallback_mode") or "").strip() != "fixture_static"
    )
    evidence_refs = (
        *_sequence_of_str(_as_mapping(historical_backtest_ref).get("evidence_refs")),
        *_sequence_of_str(_as_mapping(split_manifest).get("evidence_refs")),
        *_sequence_of_str(_as_mapping(metrics).get("evidence_refs")),
    )
    return BaselineValidationSummary(
        status=status,
        artifact_status=artifact_result.status,
        provenance_status=provenance_result.status,
        split_manifest_status=split_result.status,
        historical_backtest_ref=historical_backtest_ref,
        split_manifest=split_manifest,
        metrics=metrics,
        real_data_claim_allowed=real_data_claim_allowed,
        reasons=tuple(reasons),
        evidence_refs=tuple(evidence_refs),
    )


def validation_allows_admission(summary: BaselineValidationSummary | Mapping[str, Any] | None) -> tuple[bool, tuple[str, ...]]:
    data = _as_mapping(summary)
    status = _status_value(data.get("status"))
    if status == ArtifactStatus.PASS.value:
        return True, ()
    return False, (f"validation_status_{status.lower()}_blocks_admission",)


def compose_admission_package(
    artifact: DailyMultifactorBaselineArtifact | Mapping[str, Any],
    validation_summary: BaselineValidationSummary | Mapping[str, Any],
    statistical_gate: GateDecision | Mapping[str, Any] | None,
    reliability_gate: GateDecision | Mapping[str, Any] | None,
) -> DailyMultifactorAdmissionPackage:
    artifact_result = validate_baseline_artifact(artifact)
    validation_data = _as_mapping(validation_summary)
    validation_status = _status_value(validation_data.get("status"))
    stat_gate, stat_missing = _normalize_gate_decision(statistical_gate, "statistical_gate")
    reliability, reliability_missing = _normalize_gate_decision(reliability_gate, "reliability_gate")
    blockers: list[str] = []
    risks: list[str] = []

    if not artifact_result.passed:
        blockers.extend(issue.code for issue in artifact_result.issues)
    if validation_status != ArtifactStatus.PASS.value:
        blockers.append(f"validation_status_{validation_status.lower()}")
    if stat_missing:
        blockers.append("statistical_gate_missing")
    if reliability_missing:
        blockers.append("reliability_gate_missing")

    child_statuses = [validation_status, stat_gate.status, reliability.status]
    for label, gate in (("statistical_gate", stat_gate), ("reliability_gate", reliability)):
        status = _status_value(gate.status)
        if status in {ArtifactStatus.FAIL.value, ArtifactStatus.BLOCKED.value}:
            blockers.append(f"{label}_{status.lower()}")
            blockers.extend(gate.reasons)
        elif status == ArtifactStatus.NEEDS_REVIEW.value:
            risks.append(f"{label}_needs_review")
            risks.extend(gate.reasons)

    if blockers:
        package_status = ArtifactStatus.BLOCKED if any("missing" in item or "blocked" in item for item in blockers) else ArtifactStatus.FAIL
    else:
        package_status = _status_from_child_statuses(child_statuses)
    paper_candidate = _status_value(package_status) == ArtifactStatus.PASS.value
    artifact_data = _as_mapping(artifact)
    evidence_refs = (
        *_sequence_of_str(artifact_data.get("evidence_refs")),
        *_sequence_of_str(validation_data.get("evidence_refs")),
        *stat_gate.evidence_refs,
        *reliability.evidence_refs,
    )
    return DailyMultifactorAdmissionPackage(
        strategy_id=str(artifact_data.get("strategy_id") or ""),
        package_status=package_status,
        paper_candidate=paper_candidate,
        validation_status=validation_status,
        statistical_gate=stat_gate,
        reliability_gate=reliability,
        blockers=tuple(dict.fromkeys(blockers)),
        risks=tuple(dict.fromkeys(risks)),
        evidence_refs=tuple(dict.fromkeys(evidence_refs)),
    )


def derive_paper_candidate(package: DailyMultifactorAdmissionPackage | Mapping[str, Any]) -> tuple[bool, tuple[str, ...]]:
    data = _as_mapping(package)
    status = _status_value(data.get("package_status"))
    if status == ArtifactStatus.PASS.value and bool(data.get("paper_candidate")):
        return True, ("all_mandatory_gates_passed",)
    reasons = tuple(str(item) for item in _sequence(data.get("blockers")) or _sequence(data.get("risks")) or (f"package_status_{status.lower()}",))
    return False, reasons


def validate_admission_package(package: DailyMultifactorAdmissionPackage | Mapping[str, Any] | None) -> ContractValidationResult:
    data = _as_mapping(package)
    issues: list[ValidationIssue] = []
    for field_name in ("strategy_id", "package_status", "validation_status", "statistical_gate", "reliability_gate"):
        if is_blank(data.get(field_name)):
            issues.append(_issue("admission_package_required_field_missing", field_name, f"{field_name} is required.", "BLOCKER"))
    if is_blank(data.get("non_authorization")):
        issues.append(_issue("admission_package_non_authorization_missing", "non_authorization", "non_authorization wording is required.", "BLOCKER"))
    else:
        issues.extend(_overclaim_issues(_text_items(data.get("non_authorization")), field="non_authorization"))
    return _result_from_issues(issues, evidence_refs=_sequence_of_str(data.get("evidence_refs")))


def compare_rerun_metrics(
    first: RerunMetricSnapshot | Mapping[str, Any],
    second: RerunMetricSnapshot | Mapping[str, Any],
    tolerance: MetricTolerance | Mapping[str, Any] | None = None,
) -> RerunConsistencyReport:
    first_data = _as_mapping(first)
    second_data = _as_mapping(second)
    tolerance_data = _as_mapping(tolerance or MetricTolerance())
    numeric_tolerance = safe_float(tolerance_data.get("numeric_tolerance"))
    if numeric_tolerance is None or numeric_tolerance < 0:
        numeric_tolerance = 0.0
    drift_reasons: list[str] = []
    compared: dict[str, Any] = {}

    first_status = _status_value(first_data.get("admission_status"))
    second_status = _status_value(second_data.get("admission_status"))
    admission_status_match = first_status == second_status
    if not admission_status_match:
        drift_reasons.append(f"admission_status_drift:{first_status}->{second_status}")

    if is_blank(first_data.get("run_ref")) or is_blank(second_data.get("run_ref")):
        drift_reasons.append("rerun_run_ref_missing")

    first_metrics = _as_mapping(first_data.get("metrics"))
    second_metrics = _as_mapping(second_data.get("metrics"))
    for key in REQUIRED_RERUN_METRICS:
        if key not in first_metrics or key not in second_metrics:
            drift_reasons.append(f"rerun_metric_missing:{key}")
            compared[key] = {"status": ArtifactStatus.BLOCKED.value}
            continue
        lhs = first_metrics[key]
        rhs = second_metrics[key]
        lhs_float = safe_float(lhs)
        rhs_float = safe_float(rhs)
        if lhs_float is not None and rhs_float is not None:
            diff = abs(lhs_float - rhs_float)
            passed = diff <= numeric_tolerance
            compared[key] = {"first": lhs_float, "second": rhs_float, "diff": diff, "status": "PASS" if passed else "DRIFT"}
            if not passed:
                drift_reasons.append(f"rerun_numeric_drift:{key}:{diff}")
        else:
            passed = _sorted_json_safe(lhs) == _sorted_json_safe(rhs)
            compared[key] = {"first": lhs, "second": rhs, "status": "PASS" if passed else "DRIFT"}
            if not passed:
                drift_reasons.append(f"rerun_value_drift:{key}")

    if any(reason.startswith("rerun_metric_missing") or reason == "rerun_run_ref_missing" for reason in drift_reasons):
        status = ArtifactStatus.BLOCKED
    elif not admission_status_match:
        status = ArtifactStatus.FAIL
    elif drift_reasons:
        status = ArtifactStatus.NEEDS_REVIEW
    else:
        status = ArtifactStatus.PASS
    return RerunConsistencyReport(
        status=status,
        drift_reasons=tuple(drift_reasons),
        compared_metrics=compared,
        tolerance=MetricTolerance(numeric_tolerance=numeric_tolerance),
        snapshot_refs=(str(first_data.get("run_ref") or ""), str(second_data.get("run_ref") or "")),
        admission_status_match=admission_status_match,
    )


def rerun_allows_candidate(report: RerunConsistencyReport | Mapping[str, Any]) -> tuple[bool, tuple[str, ...]]:
    data = _as_mapping(report)
    status = _status_value(data.get("status"))
    if status == ArtifactStatus.PASS.value:
        return True, ()
    reasons = tuple(str(item) for item in _sequence(data.get("drift_reasons")) or (f"rerun_status_{status.lower()}",))
    return False, reasons


def build_release_wording(
    artifact: DailyMultifactorBaselineArtifact | Mapping[str, Any],
    package: DailyMultifactorAdmissionPackage | Mapping[str, Any],
    rerun_report: RerunConsistencyReport | Mapping[str, Any],
) -> tuple[str, ...]:
    artifact_data = _as_mapping(artifact)
    package_data = _as_mapping(package)
    rerun_data = _as_mapping(rerun_report)
    return (
        f"{artifact_data.get('strategy_id') or 'daily_multifactor_baseline'} is a research baseline artifact.",
        f"Admission package status is {_status_value(package_data.get('package_status'))}; paper_candidate={bool(package_data.get('paper_candidate'))}.",
        f"Rerun consistency status is {_status_value(rerun_data.get('status'))}.",
        "This evidence does not authorize paper, live, trading, runtime, broker, publish, registry promotion or production use.",
    )


def validate_release_wording(wording: Sequence[str] | str) -> ContractValidationResult:
    items = _text_items(wording)
    issues: list[ValidationIssue] = []
    if not items:
        issues.append(_issue("release_wording_missing", "release_wording", "release wording is required.", "BLOCKER"))
    issues.extend(_overclaim_issues(items, field="release_wording"))
    return _result_from_issues(issues)


def _validate_historical_backtest_ref(ref: HistoricalBacktestRef | Mapping[str, Any]) -> tuple[ValidationIssue, ...]:
    data = _as_mapping(ref)
    issues = []
    for field_name in ("run_ref", "report_ref", "cost_ref", "risk_ref"):
        if is_blank(data.get(field_name)):
            issues.append(_issue("historical_backtest_ref_missing", field_name, f"{field_name} is required.", "BLOCKER"))
    return tuple(issues)


def _validate_metrics(metrics: ValidationMetrics | Mapping[str, Any]) -> tuple[ValidationIssue, ...]:
    data = _as_mapping(metrics)
    issues: list[ValidationIssue] = []
    for field_name in ("total_return", "max_drawdown", "turnover", "cost"):
        if safe_float(data.get(field_name)) is None:
            issues.append(_issue("validation_metric_invalid", field_name, f"{field_name} must be numeric.", "BLOCKER"))
    if is_blank(data.get("capacity_liquidity_summary")):
        issues.append(
            _issue(
                "validation_metric_capacity_liquidity_missing",
                "capacity_liquidity_summary",
                "capacity_liquidity_summary is required.",
                "BLOCKER",
            )
        )
    return tuple(issues)


def _normalize_gate_decision(gate: GateDecision | Mapping[str, Any] | None, field_name: str) -> tuple[GateDecision, bool]:
    if gate is None:
        return GateDecision(ArtifactStatus.BLOCKED, reasons=(f"{field_name}_missing",)), True
    data = _as_mapping(gate)
    evidence_refs = _sequence_of_str(data.get("evidence_refs"))
    gate_ref = str(data.get("gate_ref") or "")
    missing = not evidence_refs and not gate_ref
    status = _status_value(data.get("status"))
    if missing:
        status = ArtifactStatus.BLOCKED.value
    return (
        GateDecision(
            status=status,
            reasons=tuple(str(item) for item in _sequence(data.get("reasons"))),
            evidence_refs=evidence_refs,
            gate_ref=gate_ref,
        ),
        missing,
    )


def _result_from_issues(issues: Sequence[ValidationIssue], *, evidence_refs: Sequence[str] = ()) -> ContractValidationResult:
    return ContractValidationResult(status=_status_from_issues(issues), issues=tuple(issues), evidence_refs=tuple(evidence_refs))


def _status_from_issues(issues: Sequence[ValidationIssue]) -> ArtifactStatus:
    if not issues:
        return ArtifactStatus.PASS
    severities = {issue.severity.upper() for issue in issues}
    if "BLOCKER" in severities:
        return ArtifactStatus.BLOCKED
    if "HIGH" in severities:
        return ArtifactStatus.FAIL
    return ArtifactStatus.NEEDS_REVIEW


def _status_from_child_statuses(statuses: Sequence[Any]) -> ArtifactStatus:
    normalized = [_status_value(status) for status in statuses]
    if ArtifactStatus.BLOCKED.value in normalized:
        return ArtifactStatus.BLOCKED
    if ArtifactStatus.FAIL.value in normalized:
        return ArtifactStatus.FAIL
    if ArtifactStatus.NEEDS_REVIEW.value in normalized:
        return ArtifactStatus.NEEDS_REVIEW
    return ArtifactStatus.PASS


def _issue(code: str, field: str, message: str, severity: str, evidence_ref: str = "") -> ValidationIssue:
    return ValidationIssue(code=code, severity=severity, message=message, field=field, evidence_ref=evidence_ref)


def _overclaim_issues(items: Sequence[str], *, field: str) -> list[ValidationIssue]:
    text = "\n".join(str(item).lower() for item in items)
    issues: list[ValidationIssue] = []
    for term in OVERCLAIM_TERMS:
        if term in text:
            issues.append(
                _issue(
                    "overclaim_wording_detected",
                    field,
                    f"Overclaim wording is not allowed for CR155 research artifact: {term}.",
                    "BLOCKER",
                )
            )
    return issues


def _as_mapping(value: Any) -> dict[str, Any]:
    if is_dataclass(value):
        return dict(_sorted_json_safe(asdict(value)))
    return as_mapping(value, none_as_empty=True) or {}


def _mapping_or_dataclass_dict(value: Any) -> dict[str, Any]:
    return _as_mapping(value)


def _sequence(value: Any) -> tuple[Any, ...]:
    if value is None:
        return ()
    if isinstance(value, (str, bytes, bytearray)):
        return (value,)
    if isinstance(value, Sequence):
        return tuple(value)
    return (value,)


def _sequence_of_str(value: Any) -> tuple[str, ...]:
    return tuple(str(item) for item in _sequence(value) if str(item))


def _text_items(value: Any) -> tuple[str, ...]:
    if isinstance(value, str):
        items = (value,)
    else:
        items = _sequence(value)
    return tuple(str(item) for item in items if str(item).strip())


def _as_int(value: Any, *, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _status_value(value: Any) -> str:
    if isinstance(value, Enum):
        return str(value.value).upper()
    text = str(value or "").strip().upper()
    if text in {status.value for status in ArtifactStatus}:
        return text
    if text in {"PASS", "PASSED"}:
        return ArtifactStatus.PASS.value
    if text in {"WARN", "WARNING", "REVIEW", "NEEDS REVIEW"}:
        return ArtifactStatus.NEEDS_REVIEW.value
    if text in {"FAIL", "FAILED"}:
        return ArtifactStatus.FAIL.value
    if text in {"BLOCK", "BLOCKED", "NOT_EVALUATED", ""}:
        return ArtifactStatus.BLOCKED.value
    return text


def _sorted_json_safe(value: Any) -> Any:
    safe = json_safe(value)
    if isinstance(safe, Mapping):
        return {str(key): _sorted_json_safe(safe[key]) for key in sorted(safe)}
    if isinstance(safe, tuple):
        return tuple(_sorted_json_safe(item) for item in safe)
    if isinstance(safe, list):
        return [_sorted_json_safe(item) for item in safe]
    return safe


__all__ = [
    "ArtifactStatus",
    "BaselineValidationSummary",
    "ContractValidationResult",
    "DAILY_MULTIFACTOR_BASELINE_SCHEMA_VERSION",
    "DailyMultifactorAdmissionPackage",
    "DailyMultifactorBaselineArtifact",
    "FORBIDDEN_PROVENANCE_OPERATION_FIELDS",
    "GateDecision",
    "HistoricalBacktestRef",
    "MetricTolerance",
    "NON_AUTHORIZATION_WORDING",
    "REQUIRED_RERUN_METRICS",
    "ReadonlyDataProvenance",
    "RerunConsistencyReport",
    "RerunMetricSnapshot",
    "ValidationIssue",
    "ValidationMetrics",
    "WalkForwardSplitManifest",
    "artifact_to_json_dict",
    "build_claim_boundary",
    "build_provenance_summary",
    "build_release_wording",
    "build_validation_summary",
    "compare_rerun_metrics",
    "compose_admission_package",
    "derive_paper_candidate",
    "downgrade_to_fixture_static",
    "rerun_allows_candidate",
    "validate_admission_package",
    "validate_baseline_artifact",
    "validate_readonly_provenance",
    "validate_release_wording",
    "validate_split_manifest",
    "validation_allows_admission",
]
