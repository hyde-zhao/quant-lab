"""Batch anomaly discovery runner for controlled candidates."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Mapping, Sequence

import pandas as pd

from engine.anomaly_admission import AnomalyAdmissionDecision, build_anomaly_admission_decisions
from engine.anomaly_candidate_generator import (
    DEFAULT_CONTROLLED_ANOMALY_TEMPLATES,
    ControlledAnomalyTemplate,
    build_candidate_matrices_from_panel,
    generate_controlled_anomaly_definitions,
)
from engine.anomaly_multiple_testing import apply_multiple_testing_control
from engine.anomaly_research import (
    AnomalyDefinition,
    build_alpha_tests,
    build_anomaly_candidates,
    build_anomaly_research_reports,
    build_anomaly_returns,
)
from engine.multifactor_contracts import FORBIDDEN_OPERATION_COUNTERS


ANOMALY_DISCOVERY_RUN_SCHEMA = "anomaly_discovery_run_v1"
FORBIDDEN_OPERATION_COUNTS = {key: 0 for key in FORBIDDEN_OPERATION_COUNTERS}


@dataclass(frozen=True, slots=True)
class AnomalyDiscoveryRunResult:
    run_id: str
    status: str
    sample_id: str
    candidate_count: int
    tested_candidate_count: int
    admitted_stage3_candidate_count: int
    anomaly_returns: pd.DataFrame
    alpha_tests: pd.DataFrame
    anomaly_candidates: tuple[dict[str, Any], ...]
    anomaly_research_reports: tuple[dict[str, Any], ...]
    anomaly_admission_decisions: tuple[dict[str, Any], ...]
    blocked_claims: tuple[dict[str, str], ...]
    operation_counts: Mapping[str, int] = field(default_factory=lambda: dict(FORBIDDEN_OPERATION_COUNTS))
    schema_version: str = ANOMALY_DISCOVERY_RUN_SCHEMA

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "run_id": self.run_id,
            "status": self.status,
            "sample_id": self.sample_id,
            "candidate_count": self.candidate_count,
            "tested_candidate_count": self.tested_candidate_count,
            "admitted_stage3_candidate_count": self.admitted_stage3_candidate_count,
            "anomaly_candidates": list(self.anomaly_candidates),
            "anomaly_research_reports": list(self.anomaly_research_reports),
            "anomaly_admission_decisions": list(self.anomaly_admission_decisions),
            "blocked_claims": list(self.blocked_claims),
            "operation_counts": dict(self.operation_counts),
        }


def run_anomaly_discovery(
    feature_panel: pd.DataFrame,
    model_returns: pd.DataFrame,
    *,
    run_id: str,
    sample_id: str,
    templates: Sequence[ControlledAnomalyTemplate] = DEFAULT_CONTROLLED_ANOMALY_TEMPLATES,
    min_cross_section: int = 30,
    quantiles: int = 5,
    alpha_model_ids: Sequence[str] = ("seven_factor_full", "ashare_pricing_candidate", "ff3_equity_core"),
    multiple_testing_alpha: float = 0.05,
) -> AnomalyDiscoveryRunResult:
    validate_anomaly_discovery_inputs(feature_panel, model_returns)
    available_fields = tuple(column for column in feature_panel.columns if column not in {"trade_date", "symbol", "forward_return"})
    definitions = generate_controlled_anomaly_definitions(available_fields=available_fields, templates=templates)
    matrices = build_candidate_matrices_from_panel(feature_panel, templates=templates)
    matrices = {definition.anomaly_id: matrices[definition.anomaly_id] for definition in definitions if definition.anomaly_id in matrices}
    definitions = tuple(definition for definition in definitions if definition.anomaly_id in matrices)
    forward_returns = feature_panel.pivot_table(
        index="trade_date",
        columns="symbol",
        values="forward_return",
        aggfunc="last",
    ).sort_index()

    anomaly_returns = build_anomaly_returns(
        matrices,
        forward_returns,
        anomalies=definitions,
        min_cross_section=min_cross_section,
        quantiles=quantiles,
    )
    alpha_tests = build_alpha_tests(anomaly_returns, model_returns, model_ids=alpha_model_ids)
    candidates = build_anomaly_candidates(definitions)
    reports = build_anomaly_research_reports(anomaly_returns, alpha_tests, candidates)
    reports = apply_multiple_testing_control(reports, alpha=multiple_testing_alpha)
    decisions = build_anomaly_admission_decisions(
        reports,
        evidence_refs=(f"artifact://anomaly-discovery/{run_id}/anomaly_research_report.json",),
    )
    stage3_count = sum(1 for decision in decisions if decision.admission_status == "stage3_candidate")
    status = "PASS" if definitions and not anomaly_returns.empty else "BLOCKED"
    return AnomalyDiscoveryRunResult(
        run_id=run_id,
        status=status,
        sample_id=sample_id,
        candidate_count=len(definitions),
        tested_candidate_count=len(reports),
        admitted_stage3_candidate_count=stage3_count,
        anomaly_returns=anomaly_returns,
        alpha_tests=alpha_tests,
        anomaly_candidates=tuple(candidate.to_dict() for candidate in candidates),
        anomaly_research_reports=tuple(dict(report) for report in reports),
        anomaly_admission_decisions=tuple(decision.to_dict() for decision in decisions),
        blocked_claims=default_anomaly_discovery_blocked_claims(),
        operation_counts=dict(FORBIDDEN_OPERATION_COUNTS),
    )


def validate_anomaly_discovery_inputs(feature_panel: pd.DataFrame, model_returns: pd.DataFrame) -> None:
    required_panel = {"trade_date", "symbol", "forward_return"}
    required_model = {"trade_date", "model_id", "model_return"}
    missing_panel = required_panel - set(feature_panel.columns)
    missing_model = required_model - set(model_returns.columns)
    if missing_panel:
        raise ValueError("feature_panel 缺少字段: " + ", ".join(sorted(missing_panel)))
    if missing_model:
        raise ValueError("model_returns 缺少字段: " + ", ".join(sorted(missing_model)))
    if feature_panel.empty:
        raise ValueError("feature_panel 不能为空")
    if model_returns.empty:
        raise ValueError("model_returns 不能为空")
    if {"available_at", "label_available_at"} <= set(feature_panel.columns):
        available_at = pd.to_datetime(feature_panel["available_at"], errors="coerce", utc=True)
        label_available_at = pd.to_datetime(feature_panel["label_available_at"], errors="coerce", utc=True)
        if bool((available_at.notna() & label_available_at.notna() & (label_available_at <= available_at)).any()):
            raise ValueError("label_available_at 必须晚于 available_at，检测到潜在前视")


def write_anomaly_discovery_outputs(result: AnomalyDiscoveryRunResult, output_dir: str | Path) -> dict[str, str]:
    root = Path(output_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "run_report": root / "ANOMALY-DISCOVERY-RUN-REPORT.json",
        "anomaly_candidates": root / "anomaly_candidates.json",
        "anomaly_research_report": root / "anomaly_research_report.json",
        "anomaly_admission_decisions": root / "anomaly_admission_decisions.json",
        "anomaly_returns": root / "anomaly_returns.parquet",
        "alpha_tests": root / "alpha_tests.parquet",
        "report_md": root / "ANOMALY-DISCOVERY-REPORT.md",
    }
    _write_json(paths["run_report"], result.to_dict())
    _write_json(paths["anomaly_candidates"], list(result.anomaly_candidates))
    _write_json(paths["anomaly_research_report"], list(result.anomaly_research_reports))
    _write_json(paths["anomaly_admission_decisions"], list(result.anomaly_admission_decisions))
    result.anomaly_returns.to_parquet(paths["anomaly_returns"], index=False)
    result.alpha_tests.to_parquet(paths["alpha_tests"], index=False)
    paths["report_md"].write_text(render_anomaly_discovery_report(result), encoding="utf-8")
    return {key: str(value) for key, value in paths.items()}


def render_anomaly_discovery_report(result: AnomalyDiscoveryRunResult) -> str:
    admitted = [
        item
        for item in result.anomaly_admission_decisions
        if item.get("admission_status") in {"factor_catalog_candidate", "stage3_candidate"}
    ]
    lines = [
        f"# Anomaly Discovery Report: {result.run_id}",
        "",
        f"- status: `{result.status}`",
        f"- sample_id: `{result.sample_id}`",
        f"- candidates: `{result.candidate_count}`",
        f"- tested candidates: `{result.tested_candidate_count}`",
        f"- stage3 candidates: `{result.admitted_stage3_candidate_count}`",
        f"- admitted catalog candidates: `{len(admitted)}`",
        "- provider_fetch: `0`",
        "- lake_write: `0`",
        "- catalog_publish: `0`",
        "- qmt_operation: `0`",
        "",
        "## Candidate Decisions",
        "",
        "| factor_id | status | multiple_testing | source_decision |",
        "|---|---|---|---|",
    ]
    for item in result.anomaly_admission_decisions:
        lines.append(
            "| {factor_id} | {admission_status} | {multiple_testing_pass} | {source_decision} |".format(
                **item
            )
        )
    return "\n".join(lines) + "\n"


def anomaly_definitions_from_candidates(candidates: Sequence[Mapping[str, Any]]) -> tuple[AnomalyDefinition, ...]:
    definitions: list[AnomalyDefinition] = []
    for candidate in candidates:
        definitions.append(
            AnomalyDefinition(
                anomaly_id=str(candidate["anomaly_id"]),
                name=str(candidate.get("name") or candidate["anomaly_id"]),
                chapter_ref="5.auto",
                source_ref=str(candidate.get("prior_logic_ref") or "anomaly_discovery"),
                required_factor_ids=tuple(candidate.get("required_factor_ids") or candidate.get("input_fields") or ()),
                direction=str(candidate.get("expected_direction") or "positive"),
                formula=str(candidate.get("formula") or ""),
                source_type=str(candidate.get("source_type") or "unspecified"),
                hypothesis=str(candidate.get("hypothesis") or ""),
                economic_rationale=str(candidate.get("economic_rationale") or ""),
                prior_logic_ref=str(candidate.get("prior_logic_ref") or ""),
                a_share_adjustments=tuple(candidate.get("a_share_adjustments") or ()),
            )
        )
    return tuple(definitions)


def default_anomaly_discovery_blocked_claims() -> tuple[dict[str, str], ...]:
    return (
        {"claim": "qmt_ready", "status": "blocked", "reason": "自动异象发现不授权 QMT。"},
        {"claim": "simulation_ready", "status": "blocked", "reason": "自动异象发现不授权 simulation。"},
        {"claim": "live_ready", "status": "blocked", "reason": "自动异象发现不授权 live。"},
        {"claim": "catalog_publish", "status": "blocked", "reason": "发现结果只能生成候选，不自动 publish catalog。"},
    )


def _write_json(path: Path, payload: Any) -> None:
    import json

    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
