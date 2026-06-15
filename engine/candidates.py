"""从参数扫描结果选择候选配置。"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from engine.contracts import CANDIDATE_REPORT_FIELDS
from engine.diagnostics import start_diagnostic
from engine.reporting import sanitize_tabular_text, write_rows_csv


@dataclass(slots=True)
class CandidateSelection:
    rows: list[dict[str, Any]]
    warnings: list[str]


def load_sweep_csv(path: str | Path) -> pd.DataFrame:
    return pd.read_csv(path)


def select_candidates(
    sweep_rows: pd.DataFrame | list[dict[str, Any]],
    max_candidates: int = 4,
) -> CandidateSelection:
    """选择 best_sharpe、best_return、conservative_low_turnover 等候选。"""

    diag = start_diagnostic(
        "candidates",
        "STORY-008",
        {
            "input_rows": len(sweep_rows),
            "max_candidates": max_candidates,
        },
    )
    frame = pd.DataFrame(sweep_rows).copy()
    try:
        if frame.empty:
            diag.warning("no_candidate", reason="sweep_empty")
            diag.end("empty")
            return CandidateSelection([], ["sweep_empty"])
        success = frame[frame.get("status", "") == "success"].copy()
        if success.empty:
            diag.warning("no_candidate", reason="no_success_rows")
            diag.end("empty")
            return CandidateSelection([], ["no_success_rows"])
        for column in ("sharpe", "cumulative_return", "max_drawdown", "turnover"):
            if column in success:
                success[column] = pd.to_numeric(success[column], errors="coerce")
        selected: list[tuple[str, pd.Series]] = []
        if "sharpe" in success:
            selected.append(("best_sharpe", success.sort_values(["sharpe", "run_id"], ascending=[False, True]).iloc[0]))
        if "cumulative_return" in success:
            selected.append(("best_return", success.sort_values(["cumulative_return", "run_id"], ascending=[False, True]).iloc[0]))
        selected.append(("conservative_low_turnover", _select_conservative(success)))

        rows: list[dict[str, Any]] = []
        seen: set[tuple[Any, Any, Any, str]] = set()
        deduped = 0
        for reason, row in selected:
            key = (row.get("lookback"), row.get("rebalance_freq"), row.get("fraction"), row.get("strategy_name", "momentum"))
            if key in seen:
                deduped += 1
                continue
            seen.add(key)
            rows.append(_candidate_row(len(rows) + 1, reason, row))
            if len(rows) >= max_candidates:
                break
        if deduped:
            diag.warning("dedupe", deduped=deduped)
        if not rows:
            diag.warning("no_candidate", reason="no_candidate_selected")
        diag.end("success" if rows else "empty", candidate_count=len(rows))
        return CandidateSelection(rows=rows, warnings=[] if rows else ["no_candidate_selected"])
    except Exception as exc:
        diag.error(exc)
        raise


def write_candidate_csv(selection: CandidateSelection, output_path: str | Path) -> str:
    return write_rows_csv(selection.rows, output_path, list(CANDIDATE_REPORT_FIELDS))


def _select_conservative(success: pd.DataFrame) -> pd.Series:
    work = success.copy()
    if {"max_drawdown", "cumulative_return", "sharpe", "turnover"}.issubset(work.columns):
        median_drawdown = work["max_drawdown"].median()
        median_sharpe = work["sharpe"].median()
        filtered = work[
            (work["max_drawdown"] >= median_drawdown * 1.25)
            & ((work["cumulative_return"] >= 0) | (work["sharpe"] >= median_sharpe * 0.8))
        ]
        if not filtered.empty:
            work = filtered
    return work.sort_values(["turnover", "run_id"], ascending=[True, True]).iloc[0]


def _candidate_row(candidate_number: int, reason: str, row: pd.Series) -> dict[str, Any]:
    return {
        "candidate_id": f"CAND-{candidate_number:02d}",
        "candidate_type": reason,
        "selection_reason": sanitize_tabular_text(reason),
        "lookback": row.get("lookback", ""),
        "rebalance_freq": row.get("rebalance_freq", ""),
        "fraction": row.get("fraction", ""),
        "local_cumulative_return": row.get("cumulative_return", ""),
        "local_annual_return": row.get("annual_return", ""),
        "local_max_drawdown": row.get("max_drawdown", ""),
        "local_sharpe": row.get("sharpe", ""),
        "local_turnover": row.get("turnover", ""),
        "joinquant_result_status": "pending_manual_validation",
        "joinquant_cumulative_return": "",
        "joinquant_max_drawdown": "",
        "joinquant_sharpe": "",
        "difference_note": "",
        "quality_status": row.get("quality_status", ""),
        "limitations_metadata": sanitize_tabular_text(row.get("limitations_metadata", "")),
    }


__all__ = (
    "CandidateSelection",
    "load_sweep_csv",
    "sanitize_tabular_text",
    "select_candidates",
    "write_candidate_csv",
)
