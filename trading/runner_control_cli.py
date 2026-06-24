"""CR138 Runner control plane 本地 CLI 渲染辅助。"""

from __future__ import annotations

import json

from trading.runner_control_contracts import BatchOpsSummary, OpsSummary, PreflightResult


def render_preflight(result: PreflightResult, *, as_json: bool = False) -> str:
    if as_json:
        return json.dumps(result.to_dict(), ensure_ascii=False, sort_keys=True)
    reasons = ",".join(result.blocked_reasons) or "-"
    return f"run_id={result.run_id} status={result.status} blocked_reasons={reasons} adapter_calls={result.adapter_calls}"


def render_ops_summary(summary: OpsSummary, *, as_json: bool = False) -> str:
    if as_json:
        return json.dumps(summary.to_dict(), ensure_ascii=False, sort_keys=True)
    reasons = ",".join(summary.blocked_reasons) or "-"
    return (
        f"run_id={summary.run_id} state={summary.state} "
        f"gateway_status={summary.gateway_status or '-'} "
        f"latest_report_state={summary.latest_report_state or '-'} "
        f"blocked_reasons={reasons} next_manual_action={summary.next_manual_action}"
    )


def render_batch_ops_summary(summary: BatchOpsSummary, *, as_json: bool = False) -> str:
    if as_json:
        return json.dumps(summary.to_dict(), ensure_ascii=False, sort_keys=True)
    return (
        f"batch_id={summary.batch_id} run_count={summary.run_count} "
        f"status_counts={dict(summary.status_counts)} "
        f"blocked_run_refs={','.join(summary.blocked_run_refs) or '-'}"
    )
