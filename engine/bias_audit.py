"""baseline/enhanced 回测偏差审计。"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import json
from typing import Any

import pandas as pd

from engine.contracts import AUDIT_REPORT_FIELDS
from engine.diagnostics import start_diagnostic
from engine.reporting import sanitize_tabular_text, write_rows_csv


@dataclass(slots=True)
class AuditComparableRun:
    run_id: str
    params: dict[str, Any]
    metrics: dict[str, Any]
    candidate_rank: int | None = None
    candidate_id: str = ""

    @property
    def param_key(self) -> str:
        return param_key(self.params)


@dataclass(slots=True)
class BiasAuditResult:
    rows: list[dict[str, Any]]
    warnings: list[str] = field(default_factory=list)


def param_key(params: dict[str, Any]) -> str:
    keys = ("strategy_name", "lookback", "rebalance_freq", "fraction")
    canonical = {key: params.get(key) for key in keys if key in params}
    if not canonical:
        canonical = dict(sorted(params.items()))
    return json.dumps(canonical, ensure_ascii=False, sort_keys=True)


def normalize_audit_input(value: list[AuditComparableRun] | list[dict[str, Any]] | pd.DataFrame) -> list[AuditComparableRun]:
    """对象优先；CSV/JSON sidecar 行兼容。"""

    if isinstance(value, pd.DataFrame):
        records = value.to_dict(orient="records")
    else:
        records = list(value)
    runs: list[AuditComparableRun] = []
    for item in records:
        if isinstance(item, AuditComparableRun):
            runs.append(item)
            continue
        metrics = {
            key: item.get(key)
            for key in ("total_return", "cumulative_return", "annual_return", "max_drawdown", "sharpe", "turnover")
            if key in item
        }
        params = {
            key: item.get(key)
            for key in ("strategy_name", "lookback", "rebalance_freq", "fraction")
            if key in item
        }
        runs.append(
            AuditComparableRun(
                run_id=str(item.get("run_id") or ""),
                params=params,
                metrics=metrics,
                candidate_rank=_optional_int(item.get("candidate_rank")),
                candidate_id=str(item.get("candidate_id") or ""),
            )
        )
    return runs


def load_audit_inputs(path: str | Path) -> list[AuditComparableRun]:
    target = Path(path)
    if target.suffix.lower() == ".json":
        data = json.loads(target.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            raise ValueError("审计 JSON 必须是 list")
        return normalize_audit_input(data)
    return normalize_audit_input(pd.read_csv(target))


def run_bias_audit(
    baseline: list[AuditComparableRun] | list[dict[str, Any]] | pd.DataFrame,
    enhanced: list[AuditComparableRun] | list[dict[str, Any]] | pd.DataFrame,
) -> BiasAuditResult:
    diag = start_diagnostic(
        "bias_audit",
        "STORY-012",
        {
            "baseline_rows": len(baseline),
            "enhanced_rows": len(enhanced),
        },
    )
    try:
        base_runs = {run.param_key: run for run in normalize_audit_input(baseline)}
        enhanced_runs = {run.param_key: run for run in normalize_audit_input(enhanced)}
        warnings: list[str] = []
        rows: list[dict[str, Any]] = []
        for key in sorted(set(base_runs) | set(enhanced_runs)):
            base = base_runs.get(key)
            enh = enhanced_runs.get(key)
            if base is None or enh is None:
                warnings.append(f"missing_pair:{key}")
                continue
            rank_status = "available"
            if base.candidate_rank is None or enh.candidate_rank is None:
                rank_status = "not_available"
                warnings.append(f"candidate_rank_missing:{key}")
            rows.append(_audit_row(key, base, enh, rank_status))
        if warnings:
            status = "missing_candidate_rank" if any(item.startswith("candidate_rank_missing") for item in warnings) else "degraded"
            diag.warning(status, warnings=warnings)
        diag.end("success" if rows else "empty", row_count=len(rows))
        return BiasAuditResult(rows=rows, warnings=warnings)
    except Exception as exc:
        diag.error(exc)
        raise


def write_bias_audit_report(result: BiasAuditResult, output_path: str | Path) -> str:
    return write_rows_csv(result.rows, output_path, list(AUDIT_REPORT_FIELDS))


def _audit_row(key: str, base: AuditComparableRun, enh: AuditComparableRun, rank_status: str) -> dict[str, Any]:
    base_return = _metric(base, "total_return", "cumulative_return")
    enh_return = _metric(enh, "total_return", "cumulative_return")
    base_drawdown = _metric(base, "max_drawdown")
    enh_drawdown = _metric(enh, "max_drawdown")
    base_sharpe = _metric(base, "sharpe")
    enh_sharpe = _metric(enh, "sharpe")
    return {
        "param_key": sanitize_tabular_text(key),
        "baseline_run_id": sanitize_tabular_text(base.run_id),
        "enhanced_run_id": sanitize_tabular_text(enh.run_id),
        "baseline_total_return": base_return,
        "enhanced_total_return": enh_return,
        "return_delta": _delta(enh_return, base_return),
        "baseline_max_drawdown": base_drawdown,
        "enhanced_max_drawdown": enh_drawdown,
        "max_drawdown_delta": _delta(enh_drawdown, base_drawdown),
        "baseline_sharpe": base_sharpe,
        "enhanced_sharpe": enh_sharpe,
        "sharpe_delta": _delta(enh_sharpe, base_sharpe),
        "candidate_rank_delta_status": rank_status,
        "warning": "" if rank_status == "available" else "candidate_rank_missing",
    }


def _metric(run: AuditComparableRun, primary: str, fallback: str | None = None) -> float | None:
    value = run.metrics.get(primary)
    if value is None and fallback:
        value = run.metrics.get(fallback)
    try:
        return None if value in (None, "") else float(value)
    except (TypeError, ValueError):
        return None


def _delta(left: float | None, right: float | None) -> float | None:
    if left is None or right is None:
        return None
    return left - right


def _optional_int(value: Any) -> int | None:
    try:
        return None if value in (None, "") or pd.isna(value) else int(value)
    except (TypeError, ValueError):
        return None


__all__ = (
    "AuditComparableRun",
    "BiasAuditResult",
    "load_audit_inputs",
    "normalize_audit_input",
    "param_key",
    "run_bias_audit",
    "sanitize_tabular_text",
    "write_bias_audit_report",
)
