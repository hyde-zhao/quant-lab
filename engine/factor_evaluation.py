"""CR030-S04 单因子评价报告合同。

本模块只实现项目自有的离线评价 schema、指标计算、声明边界和本地
artifact writer 合同。不导入或运行 Alphalens / Qlib / 外部 runtime，
不读取凭据，不触发 provider / lake / publish / QMT / simulation / live。
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, is_dataclass
from enum import Enum
import csv
import json
import math
from pathlib import Path
import re
from statistics import mean, pstdev
from typing import Any, Mapping, Sequence

from engine.factor_panel_contracts import PanelGateResult, to_blocked_claims
from engine.multifactor_contracts import FORBIDDEN_OPERATION_COUNTERS


FACTOR_EVALUATION_SCHEMA = "factor_evaluation_report_v1"
ARTIFACT_SCHEMA_VERSION = "v1"

MF_REPORT_INPUT_BLOCKED = "MF_REPORT_INPUT_BLOCKED"
MF_REPORT_NO_OBSERVATIONS = "MF_REPORT_NO_OBSERVATIONS"
MF_REPORT_COST_MISSING = "MF_REPORT_COST_MISSING"
MF_REPORT_EXPOSURE_MISSING = "MF_REPORT_EXPOSURE_MISSING"
MF_REPORT_CLAIM_UNSUPPORTED = "MF_REPORT_CLAIM_UNSUPPORTED"
MF_REPORT_ARTIFACT_PATH_FORBIDDEN = "MF_REPORT_ARTIFACT_PATH_FORBIDDEN"
MF_REPORT_ARTIFACT_EXISTS = "MF_REPORT_ARTIFACT_EXISTS"

PRODUCTION_CLAIM_MARKERS = (
    "production-valid",
    "production_valid",
    "production truth",
    "production_truth",
    "qmt-ready",
    "qmt_ready",
    "simulation-ready",
    "simulation_ready",
    "live-ready",
    "live_ready",
    "tradable_evidence",
    "real tradable",
)


class FactorEvaluationStatus(str, Enum):
    PASS = "pass"
    WARN = "warn"
    FAIL = "fail"
    BLOCKED = "blocked"
    RESEARCH_LIMITED = "research_limited"


@dataclass(frozen=True, slots=True)
class ReportClaim:
    claim: str
    status: str
    reason: str
    evidence_ref: str = ""
    code: str = ""
    limitation: str = ""

    def to_dict(self) -> dict[str, Any]:
        return _json_safe(asdict(self))


@dataclass(frozen=True, slots=True)
class ArtifactPaths:
    json_path: Path
    metrics_csv_path: Path
    markdown_path: Path

    def to_dict(self) -> dict[str, str]:
        return {
            "json": self.json_path.as_posix(),
            "metrics_csv": self.metrics_csv_path.as_posix(),
            "markdown": self.markdown_path.as_posix(),
        }


@dataclass(frozen=True, slots=True)
class ArtifactWriteResult:
    status: str
    artifact_refs: tuple[str, ...]
    blocked_reasons: tuple[ReportClaim, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "artifact_refs": list(self.artifact_refs),
            "blocked_reasons": [reason.to_dict() for reason in self.blocked_reasons],
        }


@dataclass(frozen=True, slots=True)
class FactorEvaluationReport:
    report_id: str
    run_id: str
    factor_id: str
    factor_version: str
    dataset_release: str
    label_window: Mapping[str, Any]
    evaluation_window: Mapping[str, Any]
    coverage: Mapping[str, Any]
    IC: Mapping[str, Any]
    RankIC: Mapping[str, Any]
    ICIR: Mapping[str, Any]
    quantile_returns: Mapping[str, Any]
    long_short_returns: Mapping[str, Any]
    turnover: Mapping[str, Any]
    cost_sensitivity: Mapping[str, Any]
    exposure_summary: Mapping[str, Any]
    annual_breakdown: Mapping[str, Any]
    rolling_breakdown: Mapping[str, Any]
    status: str
    allowed_claims: tuple[ReportClaim, ...]
    blocked_claims: tuple[ReportClaim, ...]
    evidence_refs: tuple[str, ...]
    benchmark: Mapping[str, Any] | str = field(default_factory=dict)
    regime_breakdown: Mapping[str, Any] = field(default_factory=dict)
    autocorr: Mapping[str, Any] = field(default_factory=dict)
    capacity_summary: Mapping[str, Any] = field(default_factory=dict)
    schema_version: str = FACTOR_EVALUATION_SCHEMA
    permission_counters: Mapping[str, int] = field(default_factory=dict)
    artifact_paths: Mapping[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["allowed_claims"] = [claim.to_dict() for claim in self.allowed_claims]
        data["blocked_claims"] = [claim.to_dict() for claim in self.blocked_claims]
        data["evidence_refs"] = list(self.evidence_refs)
        return _json_safe(data)

    @property
    def production_valid_claim_count(self) -> int:
        return sum(1 for claim in self.allowed_claims if _is_production_claim(claim.claim))


def validate_factor_evaluation_inputs(
    panel: Any,
    label: Any,
    evaluation_config: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    config = dict(evaluation_config or {})
    reasons: list[ReportClaim] = []

    for gate_name in ("gate_result", "panel_gate_result", "label_gate_result"):
        gate = config.get(gate_name)
        if isinstance(gate, PanelGateResult) and not gate.passed:
            reasons.extend(_claims_from_panel_gate(gate))
        elif isinstance(gate, Mapping) and str(gate.get("status") or "") in {
            FactorEvaluationStatus.BLOCKED.value,
            FactorEvaluationStatus.RESEARCH_LIMITED.value,
        }:
            reasons.append(
                ReportClaim(
                    claim="factor_evaluation_blocked",
                    status="blocked",
                    code=MF_REPORT_INPUT_BLOCKED,
                    reason=f"S03 gate 未通过: {gate_name}",
                    evidence_ref=str(gate.get("object_id") or gate.get("evidence_ref") or gate_name),
                    limitation="不得继续生成生产有效、QMT-ready、simulation-ready 或 live-ready 声明。",
                )
            )

    panel_rows = _normalise_rows(panel)
    label_rows = _normalise_rows(label)
    if not panel_rows and not reasons:
        reasons.append(_blocked_claim("factor_evaluation_blocked", MF_REPORT_NO_OBSERVATIONS, "panel 无可评价行", "panel"))
    if not label_rows and not reasons:
        reasons.append(_blocked_claim("factor_evaluation_blocked", MF_REPORT_NO_OBSERVATIONS, "label 无可评价行", "label"))

    status = FactorEvaluationStatus.BLOCKED.value if reasons else FactorEvaluationStatus.PASS.value
    return {
        "status": status,
        "blocked_reasons": tuple(reasons),
        "panel_rows": panel_rows,
        "label_rows": label_rows,
    }


def build_factor_evaluation_report(
    panel: Any,
    label: Any,
    benchmark: Mapping[str, Any] | str | None = None,
    cost: Mapping[str, Any] | None = None,
    exposure: Mapping[str, Any] | Sequence[Mapping[str, Any]] | None = None,
    evaluation_config: Mapping[str, Any] | None = None,
) -> FactorEvaluationReport:
    config = dict(evaluation_config or {})
    permission_counters = _normalise_permission_counters(config.get("permission_counters"))
    validation = validate_factor_evaluation_inputs(panel, label, config)

    metadata = _report_metadata(validation["panel_rows"], validation["label_rows"], config)
    report_id = _build_report_id(metadata, config)
    evidence_refs = _evidence_refs(config, validation["panel_rows"], validation["label_rows"])

    if validation["status"] == FactorEvaluationStatus.BLOCKED.value:
        blocked_claims = tuple(validation["blocked_reasons"]) + _default_not_authorized_claims(evidence_refs)
        return FactorEvaluationReport(
            report_id=report_id,
            run_id=metadata["run_id"],
            factor_id=metadata["factor_id"],
            factor_version=metadata["factor_version"],
            dataset_release=metadata["dataset_release"],
            label_window=metadata["label_window"],
            evaluation_window=metadata["evaluation_window"],
            coverage=_empty_metric("blocked"),
            IC=_empty_metric("blocked"),
            RankIC=_empty_metric("blocked"),
            ICIR=_empty_metric("blocked"),
            quantile_returns=_empty_metric("blocked"),
            long_short_returns=_empty_metric("blocked"),
            turnover=_empty_metric("blocked"),
            cost_sensitivity=_empty_metric("blocked"),
            exposure_summary=_empty_metric("blocked"),
            annual_breakdown={},
            rolling_breakdown={},
            status=FactorEvaluationStatus.BLOCKED.value,
            allowed_claims=(),
            blocked_claims=blocked_claims,
            evidence_refs=evidence_refs,
            benchmark=benchmark or {},
            permission_counters=permission_counters,
        )

    joined = _join_panel_label(validation["panel_rows"], validation["label_rows"], config)
    coverage = _coverage(joined, validation["panel_rows"], validation["label_rows"])
    grouped_returns = _returns_by_date(joined)
    ic_series = [_correlation(values["factor"], values["return"]) for values in grouped_returns.values()]
    rank_ic_series = [_correlation(_ranks(values["factor"]), _ranks(values["return"])) for values in grouped_returns.values()]
    ic_series = [value for value in ic_series if value is not None]
    rank_ic_series = [value for value in rank_ic_series if value is not None]

    quantile_returns = _quantile_returns(joined, int(config.get("quantiles") or 5))
    long_short_returns = _long_short_returns(quantile_returns)
    turnover = _turnover(joined, int(config.get("quantiles") or 5))
    cost_sensitivity = _cost_sensitivity(long_short_returns, cost)
    exposure_summary = _exposure_summary(exposure)
    annual_breakdown = _annual_breakdown(joined)
    rolling_breakdown = _rolling_breakdown(joined, int(config.get("rolling_window") or 3))

    status = _classify_status(joined, cost, exposure)
    blocked_claims: list[ReportClaim] = []
    if not joined:
        blocked_claims.append(
            _blocked_claim("factor_evaluation_blocked", MF_REPORT_NO_OBSERVATIONS, "panel 与 label 无交集", "matched_rows")
        )
        status = FactorEvaluationStatus.FAIL.value
    if not cost:
        blocked_claims.append(
            _blocked_claim(
                "cost_adjusted_or_capacity_claim",
                MF_REPORT_COST_MISSING,
                "缺 cost_config / cost evidence，不能声明成本后有效、容量或生产有效。",
                "cost_config",
            )
        )
    if not exposure:
        blocked_claims.append(
            _blocked_claim(
                "neutralized_or_pure_alpha_claim",
                MF_REPORT_EXPOSURE_MISSING,
                "缺 exposure evidence，不能声明中性化、pure alpha、容量或生产有效。",
                "exposure",
            )
        )

    report_without_claims = FactorEvaluationReport(
        report_id=report_id,
        run_id=metadata["run_id"],
        factor_id=metadata["factor_id"],
        factor_version=metadata["factor_version"],
        dataset_release=metadata["dataset_release"],
        label_window=metadata["label_window"],
        evaluation_window=metadata["evaluation_window"],
        coverage=coverage,
        IC=_series_metric("IC", ic_series),
        RankIC=_series_metric("RankIC", rank_ic_series),
        ICIR=_icir_metric(ic_series),
        quantile_returns=quantile_returns,
        long_short_returns=long_short_returns,
        turnover=turnover,
        cost_sensitivity=cost_sensitivity,
        exposure_summary=exposure_summary,
        annual_breakdown=annual_breakdown,
        rolling_breakdown=rolling_breakdown,
        status=status,
        allowed_claims=(),
        blocked_claims=tuple(blocked_claims),
        evidence_refs=evidence_refs,
        benchmark=benchmark or {},
        permission_counters=permission_counters,
    )
    allowed, guard_blocked = classify_factor_report_claims(report_without_claims)
    return _replace_claims(report_without_claims, allowed, tuple(blocked_claims) + guard_blocked)


def classify_factor_report_claims(report: FactorEvaluationReport | Mapping[str, Any]) -> tuple[tuple[ReportClaim, ...], tuple[ReportClaim, ...]]:
    data = report.to_dict() if isinstance(report, FactorEvaluationReport) else dict(report)
    status = str(data.get("status") or "")
    blocked: list[ReportClaim] = list(_claims_from_data(data.get("blocked_claims")))
    allowed: list[ReportClaim] = []
    evidence_ref = _first_evidence_ref(data)

    requested_claims = list(data.get("requested_claims") or data.get("allowed_claims") or [])
    for claim in requested_claims:
        claim_name = claim.get("claim") if isinstance(claim, Mapping) else str(claim)
        if _is_production_claim(str(claim_name)):
            blocked.append(
                ReportClaim(
                    claim=str(claim_name),
                    status="blocked",
                    code=MF_REPORT_CLAIM_UNSUPPORTED,
                    reason="CR030-S04 不允许从单因子评价直接产生 production-valid / QMT-ready / simulation-ready / live-ready 声明。",
                    evidence_ref=evidence_ref,
                    limitation="真实 QMT / simulation / live 需后续独立 CR 与 per-run authorization。",
                )
            )

    if status in {FactorEvaluationStatus.PASS.value, FactorEvaluationStatus.WARN.value}:
        allowed.append(
            ReportClaim(
                claim="single_factor_research_evidence",
                status="allowed",
                code="MF_REPORT_RESEARCH_EVIDENCE_ALLOWED",
                reason="仅允许作为项目自有多因子研究输入证据，不构成生产、QMT、模拟盘或实盘声明。",
                evidence_ref=evidence_ref,
                limitation="需与成本、暴露、年度/rolling、组合和 Stage6 gate 证据共同使用。",
            )
        )

    if _single_full_sample_only(data):
        blocked.append(
            ReportClaim(
                claim="production_valid_from_single_full_sample_metric",
                status="blocked",
                code=MF_REPORT_CLAIM_UNSUPPORTED,
                reason="单一全样本 IC 或单一收益曲线不能形成 production-valid、QMT-ready、simulation-ready 或 live-ready 声明。",
                evidence_ref=evidence_ref,
                limitation="必须补充年度、rolling、成本、暴露、组合和准入证据。",
            )
        )

    if _metric_status(data.get("cost_sensitivity")) in {"missing", "blocked"}:
        blocked.append(
            _blocked_claim("cost_adjusted_or_capacity_claim", MF_REPORT_COST_MISSING, "缺成本敏感性证据，阻断生产有效和容量声明。", "cost_sensitivity")
        )
    if _metric_status(data.get("exposure_summary")) in {"missing", "blocked"}:
        blocked.append(
            _blocked_claim("neutralized_or_pure_alpha_claim", MF_REPORT_EXPOSURE_MISSING, "缺暴露证据，阻断中性化和 pure alpha 声明。", "exposure_summary")
        )

    blocked.extend(_default_not_authorized_claims(tuple(data.get("evidence_refs") or ())))
    return tuple(_dedupe_claims(allowed)), tuple(_dedupe_claims(blocked))


def resolve_factor_evaluation_report_paths(
    report_id: str,
    output_root: str | Path = "reports/factor_evaluation",
) -> ArtifactPaths:
    root = Path(output_root)
    root_parts = root.parts
    if len(root_parts) < 2 or root_parts[-2:] != ("reports", "factor_evaluation"):
        root = root / "reports" / "factor_evaluation"
    if "experiment_" in root.as_posix() or "research_catalog" in root.as_posix():
        raise ValueError(f"{MF_REPORT_ARTIFACT_PATH_FORBIDDEN}: {root.as_posix()}")
    safe_id = _safe_slug(report_id)
    base = root / ARTIFACT_SCHEMA_VERSION / safe_id
    paths = ArtifactPaths(
        json_path=base / "report.json",
        metrics_csv_path=base / "metrics.csv",
        markdown_path=base / "report.md",
    )
    for path in paths.to_dict().values():
        normalised = Path(path).as_posix()
        if "/reports/factor_evaluation/" not in f"/{normalised}":
            raise ValueError(f"{MF_REPORT_ARTIFACT_PATH_FORBIDDEN}: {normalised}")
    return paths


def write_factor_evaluation_artifacts(report: FactorEvaluationReport, paths: ArtifactPaths) -> ArtifactWriteResult:
    blocked: list[ReportClaim] = []
    for path in (paths.json_path, paths.metrics_csv_path, paths.markdown_path):
        if path.exists():
            blocked.append(
                ReportClaim(
                    claim="artifact_write",
                    status="blocked",
                    code=MF_REPORT_ARTIFACT_EXISTS,
                    reason=f"目标 artifact 已存在，禁止覆盖: {path.as_posix()}",
                    evidence_ref=path.as_posix(),
                )
            )
    if blocked:
        return ArtifactWriteResult(status="blocked", artifact_refs=(), blocked_reasons=tuple(blocked))

    paths.json_path.parent.mkdir(parents=True, exist_ok=True)
    report_data = report.to_dict()
    paths.json_path.write_text(json.dumps(report_data, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")

    with paths.metrics_csv_path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["metric", "value", "status"])
        for metric_name in ("coverage", "IC", "RankIC", "ICIR", "long_short_returns", "turnover"):
            metric = report_data.get(metric_name) or {}
            writer.writerow([metric_name, metric.get("value", metric.get("mean", "")), metric.get("status", "")])

    paths.markdown_path.write_text(_render_markdown_report(report), encoding="utf-8")
    return ArtifactWriteResult(status="pass", artifact_refs=tuple(paths.to_dict().values()))


def _replace_claims(
    report: FactorEvaluationReport,
    allowed_claims: tuple[ReportClaim, ...],
    blocked_claims: tuple[ReportClaim, ...],
) -> FactorEvaluationReport:
    return FactorEvaluationReport(
        **{
            **report.to_dict(),
            "allowed_claims": allowed_claims,
            "blocked_claims": blocked_claims,
            "evidence_refs": tuple(report.evidence_refs),
            "permission_counters": dict(report.permission_counters),
        }
    )


def _join_panel_label(
    panel_rows: Sequence[Mapping[str, Any]],
    label_rows: Sequence[Mapping[str, Any]],
    config: Mapping[str, Any],
) -> list[dict[str, Any]]:
    label_by_key = {(_row_date(row), str(row.get("symbol") or "")): row for row in label_rows}
    joined: list[dict[str, Any]] = []
    for row in panel_rows:
        key = (_row_date(row), str(row.get("symbol") or ""))
        label = label_by_key.get(key)
        if not label:
            continue
        factor_value = _first_number(row, ("zscore_value", "factor_value", "directional_value", "winsorized_value", "raw_value", "value"))
        return_value = _first_number(label, ("forward_return", "return", "label_return", "excess_return", "value"))
        if factor_value is None or return_value is None:
            continue
        joined.append(
            {
                "date": _row_date(row),
                "year": _row_date(row)[:4],
                "symbol": str(row.get("symbol") or ""),
                "factor": factor_value,
                "return": return_value,
                "weight": float(config.get("default_weight") or 1.0),
            }
        )
    return joined


def _coverage(joined: Sequence[Mapping[str, Any]], panel_rows: Sequence[Mapping[str, Any]], label_rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    panel_keys = {(_row_date(row), str(row.get("symbol") or "")) for row in panel_rows}
    label_keys = {(_row_date(row), str(row.get("symbol") or "")) for row in label_rows}
    matched_keys = {(_row_date(row), str(row.get("symbol") or "")) for row in joined}
    dates = {date for date, _ in matched_keys}
    symbols = {symbol for _, symbol in matched_keys}
    denominator = max(len(panel_keys | label_keys), 1)
    return {
        "status": "pass" if joined else "missing",
        "observations": len(joined),
        "panel_observations": len(panel_rows),
        "label_observations": len(label_rows),
        "matched_observations": len(matched_keys),
        "matched_ratio": len(matched_keys) / denominator,
        "date_count": len(dates),
        "symbol_count": len(symbols),
        "date_coverage": sorted(dates),
        "symbol_coverage": sorted(symbols),
    }


def _returns_by_date(joined: Sequence[Mapping[str, Any]]) -> dict[str, dict[str, list[float]]]:
    grouped: dict[str, dict[str, list[float]]] = {}
    for row in joined:
        group = grouped.setdefault(str(row["date"]), {"factor": [], "return": []})
        group["factor"].append(float(row["factor"]))
        group["return"].append(float(row["return"]))
    return grouped


def _series_metric(name: str, values: Sequence[float]) -> dict[str, Any]:
    if not values:
        return {"metric": name, "value": None, "mean": None, "observations": 0, "status": "missing"}
    return {
        "metric": name,
        "value": mean(values),
        "mean": mean(values),
        "observations": len(values),
        "series": list(values),
        "status": "pass",
    }


def _icir_metric(values: Sequence[float]) -> dict[str, Any]:
    if len(values) < 2:
        return {"metric": "ICIR", "value": None, "observations": len(values), "status": "missing"}
    std = pstdev(values)
    return {
        "metric": "ICIR",
        "value": None if std == 0 else mean(values) / std,
        "observations": len(values),
        "status": "pass" if std else "warn",
    }


def _quantile_returns(joined: Sequence[Mapping[str, Any]], quantiles: int) -> dict[str, Any]:
    if not joined:
        return _empty_metric("missing")
    sorted_rows = sorted(joined, key=lambda row: (str(row["date"]), float(row["factor"])))
    grouped_by_date: dict[str, list[Mapping[str, Any]]] = {}
    for row in sorted_rows:
        grouped_by_date.setdefault(str(row["date"]), []).append(row)
    buckets: dict[str, list[float]] = {f"q{idx}": [] for idx in range(1, quantiles + 1)}
    for rows in grouped_by_date.values():
        for idx, row in enumerate(rows):
            bucket = min(int(idx * quantiles / max(len(rows), 1)) + 1, quantiles)
            buckets[f"q{bucket}"].append(float(row["return"]))
    return {
        "status": "pass",
        "quantiles": quantiles,
        "returns": {bucket: (mean(values) if values else None) for bucket, values in buckets.items()},
        "observations": {bucket: len(values) for bucket, values in buckets.items()},
    }


def _long_short_returns(quantile_returns: Mapping[str, Any]) -> dict[str, Any]:
    returns = quantile_returns.get("returns") if isinstance(quantile_returns.get("returns"), Mapping) else {}
    if not returns:
        return _empty_metric("missing")
    sorted_keys = sorted(returns)
    low = returns.get(sorted_keys[0])
    high = returns.get(sorted_keys[-1])
    value = None if low is None or high is None else high - low
    return {
        "status": "pass" if value is not None else "missing",
        "long_quantile": sorted_keys[-1],
        "short_quantile": sorted_keys[0],
        "value": value,
    }


def _turnover(joined: Sequence[Mapping[str, Any]], quantiles: int) -> dict[str, Any]:
    if not joined:
        return _empty_metric("missing")
    by_date: dict[str, list[Mapping[str, Any]]] = {}
    for row in joined:
        by_date.setdefault(str(row["date"]), []).append(row)
    previous: set[str] | None = None
    turnovers: list[float] = []
    for date_key in sorted(by_date):
        rows = sorted(by_date[date_key], key=lambda row: float(row["factor"]))
        top_start = max(int(len(rows) * (quantiles - 1) / quantiles), 0)
        current = {str(row["symbol"]) for row in rows[top_start:]}
        if previous is not None:
            denominator = max(len(previous | current), 1)
            turnovers.append(len(previous ^ current) / denominator)
        previous = current
    return {
        "status": "pass" if turnovers else "warn",
        "value": mean(turnovers) if turnovers else 0.0,
        "observations": len(turnovers),
    }


def _cost_sensitivity(long_short_returns: Mapping[str, Any], cost: Mapping[str, Any] | None) -> dict[str, Any]:
    if not cost:
        return {"status": "missing", "value": None, "reason": "cost_config missing"}
    gross = long_short_returns.get("value")
    commission_bps = _number(cost.get("commission_bps")) or 0.0
    slippage_bps = _number(cost.get("slippage_bps")) or 0.0
    total_cost = (commission_bps + slippage_bps) / 10000
    return {
        "status": "pass" if gross is not None else "missing",
        "gross_long_short_return": gross,
        "cost_bps": commission_bps + slippage_bps,
        "net_long_short_return": None if gross is None else float(gross) - total_cost,
    }


def _exposure_summary(exposure: Mapping[str, Any] | Sequence[Mapping[str, Any]] | None) -> dict[str, Any]:
    if not exposure:
        return {"status": "missing", "reason": "exposure missing"}
    rows = _normalise_rows(exposure)
    if not rows and isinstance(exposure, Mapping):
        rows = [exposure]
    numeric: dict[str, list[float]] = {}
    categorical: dict[str, set[str]] = {}
    for row in rows:
        for key, value in row.items():
            number = _number(value)
            if number is not None:
                numeric.setdefault(str(key), []).append(number)
            elif value not in (None, ""):
                categorical.setdefault(str(key), set()).add(str(value))
    return {
        "status": "pass",
        "numeric_means": {key: mean(values) for key, values in numeric.items()},
        "categories": {key: sorted(values) for key, values in categorical.items()},
        "observations": len(rows),
    }


def _annual_breakdown(joined: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    grouped: dict[str, list[float]] = {}
    for row in joined:
        grouped.setdefault(str(row["year"]), []).append(float(row["return"]))
    return {year: {"mean_return": mean(values), "observations": len(values)} for year, values in sorted(grouped.items())}


def _rolling_breakdown(joined: Sequence[Mapping[str, Any]], window: int) -> dict[str, Any]:
    by_date = sorted((str(row["date"]), float(row["return"])) for row in joined)
    if len(by_date) < window:
        return {"status": "missing", "window": window, "series": []}
    series = []
    for idx in range(window, len(by_date) + 1):
        chunk = by_date[idx - window : idx]
        series.append({"end_date": chunk[-1][0], "mean_return": mean(value for _, value in chunk), "observations": window})
    return {"status": "pass", "window": window, "series": series}


def _classify_status(joined: Sequence[Mapping[str, Any]], cost: Mapping[str, Any] | None, exposure: Any) -> str:
    if not joined:
        return FactorEvaluationStatus.FAIL.value
    if not cost or not exposure:
        return FactorEvaluationStatus.RESEARCH_LIMITED.value
    return FactorEvaluationStatus.PASS.value


def _single_full_sample_only(data: Mapping[str, Any]) -> bool:
    annual = data.get("annual_breakdown") or {}
    rolling = data.get("rolling_breakdown") or {}
    rolling_series = rolling.get("series") if isinstance(rolling, Mapping) else []
    ic = data.get("IC") if isinstance(data.get("IC"), Mapping) else {}
    long_short = data.get("long_short_returns") if isinstance(data.get("long_short_returns"), Mapping) else {}
    has_full_sample_metric = ic.get("value") is not None or long_short.get("value") is not None
    return bool(has_full_sample_metric and not annual and not rolling_series)


def _claims_from_panel_gate(gate: PanelGateResult) -> list[ReportClaim]:
    claims = []
    for claim in to_blocked_claims(gate):
        claims.append(
            ReportClaim(
                claim=str(claim.get("claim") or "factor_evaluation_blocked"),
                status="blocked",
                code=str(claim.get("code") or MF_REPORT_INPUT_BLOCKED),
                reason=str(claim.get("message") or "S03 gate blocked"),
                evidence_ref=str(claim.get("evidence_ref") or claim.get("object_id") or ""),
                limitation="S03 gate fail 时 S04 只能输出 blocked / research_limited，生产有效声明次数必须为 0。",
            )
        )
    return claims


def _claims_from_data(claims: Any) -> list[ReportClaim]:
    result = []
    if not isinstance(claims, Sequence) or isinstance(claims, (str, bytes)):
        return result
    for claim in claims:
        if isinstance(claim, ReportClaim):
            result.append(claim)
        elif isinstance(claim, Mapping):
            result.append(
                ReportClaim(
                    claim=str(claim.get("claim") or ""),
                    status=str(claim.get("status") or "blocked"),
                    reason=str(claim.get("reason") or claim.get("message") or ""),
                    evidence_ref=str(claim.get("evidence_ref") or ""),
                    code=str(claim.get("code") or ""),
                    limitation=str(claim.get("limitation") or ""),
                )
            )
    return result


def _default_not_authorized_claims(evidence_refs: Sequence[str]) -> tuple[ReportClaim, ...]:
    evidence_ref = evidence_refs[0] if evidence_refs else ""
    return tuple(
        ReportClaim(
            claim=claim,
            status="blocked",
            code=MF_REPORT_CLAIM_UNSUPPORTED,
            reason="CR030-S04 单因子评价报告不授权生产、QMT、模拟盘或实盘就绪声明。",
            evidence_ref=evidence_ref,
            limitation="需后续组合、manifest/catalog、Stage6 admission 和独立运行授权。",
        )
        for claim in ("production_valid", "qmt_ready", "simulation_ready", "live_ready")
    )


def _blocked_claim(claim: str, code: str, reason: str, evidence_ref: str) -> ReportClaim:
    return ReportClaim(claim=claim, status="blocked", code=code, reason=reason, evidence_ref=evidence_ref)


def _dedupe_claims(claims: Sequence[ReportClaim]) -> list[ReportClaim]:
    seen: set[tuple[str, str, str]] = set()
    result: list[ReportClaim] = []
    for claim in claims:
        key = (claim.claim, claim.code, claim.evidence_ref)
        if key in seen:
            continue
        seen.add(key)
        result.append(claim)
    return result


def _report_metadata(panel_rows: Sequence[Mapping[str, Any]], label_rows: Sequence[Mapping[str, Any]], config: Mapping[str, Any]) -> dict[str, Any]:
    first_panel = panel_rows[0] if panel_rows else {}
    first_label = label_rows[0] if label_rows else {}
    return {
        "run_id": str(config.get("run_id") or "run-unknown"),
        "factor_id": str(config.get("factor_id") or first_panel.get("factor_id") or "factor-unknown"),
        "factor_version": str(config.get("factor_version") or first_panel.get("factor_version") or "version-unknown"),
        "dataset_release": str(config.get("dataset_release") or first_panel.get("source_dataset") or "dataset-unknown"),
        "label_window": dict(config.get("label_window") or {"label_id": first_label.get("label_id", "")}),
        "evaluation_window": dict(config.get("evaluation_window") or _date_window(panel_rows, label_rows)),
    }


def _build_report_id(metadata: Mapping[str, Any], config: Mapping[str, Any]) -> str:
    if config.get("report_id"):
        return _safe_slug(str(config["report_id"]))
    window = metadata.get("evaluation_window") if isinstance(metadata.get("evaluation_window"), Mapping) else {}
    raw = f"{metadata['run_id']}-{metadata['factor_id']}-{window.get('start', 'na')}-{window.get('end', 'na')}-{FACTOR_EVALUATION_SCHEMA}"
    return _safe_slug(raw)


def _evidence_refs(config: Mapping[str, Any], panel_rows: Sequence[Mapping[str, Any]], label_rows: Sequence[Mapping[str, Any]]) -> tuple[str, ...]:
    refs = list(config.get("evidence_refs") or [])
    for row in list(panel_rows[:1]) + list(label_rows[:1]):
        lineage = row.get("data_lineage")
        if isinstance(lineage, Mapping):
            value = lineage.get("evidence_refs")
            if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
                refs.extend(str(item) for item in value)
            elif value:
                refs.append(str(value))
    return tuple(dict.fromkeys(refs or ["fixture://cr030-s04-factor-evaluation"]))


def _date_window(panel_rows: Sequence[Mapping[str, Any]], label_rows: Sequence[Mapping[str, Any]]) -> dict[str, str]:
    dates = sorted({_row_date(row) for row in list(panel_rows) + list(label_rows) if _row_date(row)})
    return {"start": dates[0] if dates else "", "end": dates[-1] if dates else ""}


def _normalise_rows(value: Any) -> list[Mapping[str, Any]]:
    if value is None:
        return []
    if is_dataclass(value):
        return [_json_safe(asdict(value))]
    if isinstance(value, Mapping):
        if isinstance(value.get("rows"), Sequence) and not isinstance(value.get("rows"), (str, bytes)):
            return [_as_mapping(row) for row in value["rows"]]
        return [_json_safe(dict(value))]
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return [_as_mapping(row) for row in value]
    return []


def _as_mapping(row: Any) -> Mapping[str, Any]:
    if is_dataclass(row):
        return _json_safe(asdict(row))
    if isinstance(row, Mapping):
        return _json_safe(dict(row))
    return {}


def _normalise_permission_counters(value: Any) -> dict[str, int]:
    if is_dataclass(value):
        raw = asdict(value)
    elif isinstance(value, Mapping):
        raw = dict(value)
    else:
        raw = {}
    return {key: int(raw.get(key) or 0) for key in FORBIDDEN_OPERATION_COUNTERS}


def _render_markdown_report(report: FactorEvaluationReport) -> str:
    return "\n".join(
        [
            f"# Factor Evaluation Report: {report.report_id}",
            "",
            f"- status: `{report.status}`",
            f"- run_id: `{report.run_id}`",
            f"- factor_id: `{report.factor_id}`",
            f"- production_valid_claim_count: `{report.production_valid_claim_count}`",
            "",
            "## Metrics",
            "",
            f"- coverage observations: `{report.coverage.get('observations')}`",
            f"- IC: `{report.IC.get('value')}`",
            f"- RankIC: `{report.RankIC.get('value')}`",
            f"- ICIR: `{report.ICIR.get('value')}`",
            "",
            "## Claims",
            "",
            f"- allowed: `{len(report.allowed_claims)}`",
            f"- blocked: `{len(report.blocked_claims)}`",
            "",
        ]
    )


def _json_safe(value: Any) -> Any:
    if isinstance(value, Path):
        return value.as_posix()
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value):
        return _json_safe(asdict(value))
    if isinstance(value, Mapping):
        return {str(key): _json_safe(val) for key, val in value.items()}
    if isinstance(value, tuple):
        return tuple(_json_safe(item) for item in value)
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    return value


def _row_date(row: Mapping[str, Any]) -> str:
    return str(row.get("trade_date") or row.get("date") or "")[:10]


def _first_number(row: Mapping[str, Any], fields: Sequence[str]) -> float | None:
    for field_name in fields:
        value = _number(row.get(field_name))
        if value is not None:
            return value
    return None


def _number(value: Any) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(number) or math.isinf(number):
        return None
    return number


def _correlation(xs: Sequence[float], ys: Sequence[float]) -> float | None:
    if len(xs) != len(ys) or len(xs) < 2:
        return None
    x_mean = mean(xs)
    y_mean = mean(ys)
    numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(xs, ys))
    x_denominator = math.sqrt(sum((x - x_mean) ** 2 for x in xs))
    y_denominator = math.sqrt(sum((y - y_mean) ** 2 for y in ys))
    denominator = x_denominator * y_denominator
    if denominator == 0:
        return None
    return numerator / denominator


def _ranks(values: Sequence[float]) -> list[float]:
    sorted_pairs = sorted((value, idx) for idx, value in enumerate(values))
    ranks = [0.0] * len(values)
    for rank, (_, idx) in enumerate(sorted_pairs, start=1):
        ranks[idx] = float(rank)
    return ranks


def _metric_status(metric: Any) -> str:
    if isinstance(metric, Mapping):
        return str(metric.get("status") or "")
    return ""


def _empty_metric(status: str) -> dict[str, Any]:
    return {"status": status, "value": None, "observations": 0}


def _first_evidence_ref(data: Mapping[str, Any]) -> str:
    refs = data.get("evidence_refs")
    if isinstance(refs, Sequence) and not isinstance(refs, (str, bytes)) and refs:
        return str(refs[0])
    return ""


def _is_production_claim(value: str) -> bool:
    normalised = value.lower().replace(" ", "_")
    return any(marker.replace(" ", "_") in normalised for marker in PRODUCTION_CLAIM_MARKERS)


def _safe_slug(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9_.-]+", "-", value.strip()).strip("-._")
    return slug[:180] or "factor-evaluation-report"
