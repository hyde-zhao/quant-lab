"""实验报告 research_input_v1 metadata 写入工具。"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from engine.reporting import sanitize_tabular_text
from engine.research_dataset import (
    CR013_PERMISSION_COUNTERS,
    CR014_RESEARCH_CONSUMER_FORBIDDEN_COUNTERS,
    LEGACY_REPORT_POLICY,
    ResearchInputMetadata,
    assert_research_consumer_forbidden_operations,
    build_research_input_metadata,
    consume_duckdb_audit_evidence_ref,
    metadata_to_dict,
)


CR013_FORMAL_DATASETS = (
    "prices",
    "adj_factor",
    "hs300_index",
    "trade_calendar",
    "index_members",
    "index_weights",
    "stock_basic",
    "trade_status",
    "prices_limit",
    "events",
)

CR013_UNSUPPORTED_DATA_ITEMS = (
    "industry_classification",
    "market_cap",
    "style_exposure_beta_size_value_quality",
    "capacity_inputs_turnover_adv_constraints",
    "corporate_actions_full",
    "non_hs300_benchmark",
    "minute_tick_level2_order_match",
    "microstructure_impact_cost",
    "real_vwap_execution",
)


def _experiment_entrypoint(index: int) -> str:
    if index in {6, 7}:
        return "experiments/run_experiment_06_07.py"
    if index == 11:
        return "N/A"
    known = {
        8: "experiments/run_experiment_08.py",
        9: "experiments/run_experiment_09.py",
        10: "experiments/run_experiment_10.py",
        12: "experiments/run_experiment_12.py",
        13: "experiments/run_experiment_13.py",
        14: "experiments/run_experiment_14.py",
        15: "experiments/run_experiment_15_factor_framework.py",
        16: "experiments/run_experiment_16_momentum_factor.py",
    }
    return known.get(index, "legacy-script-regression")


EXPERIMENT_REALISM_REGISTRY: tuple[dict[str, str], ...] = tuple(
    {"experiment_id": f"{index:02d}", "entrypoint": _experiment_entrypoint(index)}
    for index in range(1, 17)
)


def legacy_report_limitation(path: str | Path, role: str) -> dict[str, str]:
    """只把历史报告路径写成 legacy 限制说明；不会读取或检查文件。"""

    return {
        "role": str(sanitize_tabular_text(role)),
        "source": str(sanitize_tabular_text(str(path))),
        "policy": LEGACY_REPORT_POLICY,
        "limitation": "legacy_only_not_current_truth; not_current_truth; not_coverage_proof",
    }


def read_unsupported_data_register(unsupported_register_path: str | Path) -> list[dict[str, str]]:
    """只读解析 CR-013 unsupported register，缺行或缺字段时 fail closed。"""

    required_fields = {"data_item", "status", "reason", "pass_denominator"}
    path = Path(unsupported_register_path)
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        missing = sorted(required_fields.difference(reader.fieldnames or ()))
        if missing:
            raise ValueError(f"unsupported_register_missing_field: {','.join(missing)}")
        rows = [dict(row) for row in reader]

    items = [str(row.get("data_item") or "") for row in rows]
    duplicate_items = sorted({item for item in items if items.count(item) > 1})
    if duplicate_items:
        raise ValueError(f"duplicate_data_item: {','.join(duplicate_items)}")
    expected = set(CR013_UNSUPPORTED_DATA_ITEMS)
    actual = set(items)
    if actual != expected:
        missing_items = ",".join(sorted(expected - actual))
        extra_items = ",".join(sorted(actual - expected))
        raise ValueError(f"unsupported_register_missing_row: missing={missing_items};extra={extra_items}")
    for row in rows:
        for field in required_fields:
            if not str(row.get(field) or "").strip():
                raise ValueError(f"unsupported_register_missing_field: {field}")
        if str(row.get("pass_denominator") or "") != "excluded":
            raise ValueError(f"excluded_denominator_violation: {row.get('data_item')}")
    return rows


def build_claim_boundary_summary(
    register_rows: Sequence[Mapping[str, Any]],
    s01_boundary: Mapping[str, Any],
    s02_boundary: Mapping[str, Any],
    *,
    evidence_paths: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """合并 S01/S02 合同和 unsupported register 为统一声明边界。"""

    rows = [dict(row) for row in register_rows]
    for row in rows:
        if str(row.get("pass_denominator") or "") != "excluded":
            raise ValueError(f"excluded_denominator_violation: {row.get('data_item')}")

    research_only = [row["data_item"] for row in rows if row.get("status") == "research_contract_only"]
    unsupported = [row["data_item"] for row in rows if row.get("status") == "unsupported"]
    blocked = [row["data_item"] for row in rows if row.get("status") == "contract_supported_but_unavailable"]
    execution_blocked = [str(item) for item in s02_boundary.get("blocked_claims") or []]

    return sanitize_metadata_text(
        {
            "supported_window": str(s01_boundary.get("supported_window") or "2025-02-11..2026-02-18"),
            "blocked_window": str(s01_boundary.get("blocked_window") or "2020-01-01..2024-12-31"),
            "full_history_status": str(s01_boundary.get("full_history_status") or "research_limited_only"),
            "formal_dataset_count": len(CR013_FORMAL_DATASETS),
            "formal_dataset_pass_denominator": len(CR013_FORMAL_DATASETS),
            "unsupported_data_items": rows,
            "research_only_items": research_only,
            "unsupported_items": unsupported,
            "blocked_claims": sorted(set([*blocked, *execution_blocked])),
            "execution_blocked_claims": execution_blocked,
            "pass_denominator_policy": {
                "unsupported_register_policy": "excluded",
                "excluded_item_count": len(rows),
                "excluded_from_pass_denominator": [row["data_item"] for row in rows],
                "excluded_in_formal_pass_denominator_count": 0,
            },
            "claim_categories": {
                "supported": ["limited_window_supported"],
                "research_only": research_only,
                "unsupported": unsupported,
                "blocked": sorted(set([*blocked, *execution_blocked])),
            },
            "evidence_paths": dict(evidence_paths or {}),
            "old_baseline_preserved": True,
            "permission_counters": dict(CR013_PERMISSION_COUNTERS),
        }
    )


def attach_report_claim_boundary(
    report_metadata: Mapping[str, Any],
    claim_boundary_summary: Mapping[str, Any],
) -> dict[str, Any]:
    """把 CR-013 claim boundary 注入新版报告 metadata，不覆盖旧报告。"""

    metadata = sanitize_metadata_text(dict(report_metadata))
    summary = sanitize_metadata_text(dict(claim_boundary_summary))
    metadata["claim_boundary_summary"] = summary
    metadata["unsupported_data_items"] = list(summary.get("unsupported_data_items") or [])
    metadata["blocked_claims"] = sorted(
        set([*list(metadata.get("blocked_claims") or []), *list(summary.get("blocked_claims") or [])])
    )
    metadata["allowed_claims"] = [
        claim
        for claim in list(metadata.get("allowed_claims") or [])
        if claim not in set(metadata["blocked_claims"])
    ]
    metadata["permission_counters"] = dict(CR013_PERMISSION_COUNTERS)
    metadata["old_baseline_preserved"] = True
    return sanitize_metadata_text(metadata)


def attach_cr014_claim_boundary_metadata(
    report_metadata: Mapping[str, Any],
    claim_boundary_summary: Mapping[str, Any] | Any,
    *,
    permission_counters: Mapping[str, Any] | None = None,
    duckdb_evidence_refs: Sequence[Mapping[str, Any] | Any] = (),
    docs_runbook_refresh_contract: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """把 CR014-S05/S08 claim boundary 注入报告 metadata。

    DuckDB evidence 在这里仍只保留 run_id/evidence_path/parity_status/audit_scope
    引用；docs/runbook 刷新也只作为结构化 metadata 输出。
    """

    metadata = sanitize_metadata_text(dict(report_metadata))
    summary = _claim_boundary_payload(claim_boundary_summary)
    counters = assert_research_consumer_forbidden_operations(
        permission_counters or summary.get("permission_counters") or CR014_RESEARCH_CONSUMER_FORBIDDEN_COUNTERS
    ).counters
    evidence_refs = [
        evidence
        for evidence in (consume_duckdb_audit_evidence_ref(ref) for ref in duckdb_evidence_refs)
        if set(evidence) == {"run_id", "evidence_path", "parity_status", "audit_scope"}
    ]
    blocked_claims = _dedupe_rows(
        [
            *[dict(item) for item in metadata.get("blocked_claims") or [] if isinstance(item, Mapping)],
            *[dict(item) for item in summary.get("blocked_claims") or [] if isinstance(item, Mapping)],
        ]
    )
    required_missing = _dedupe_rows(
        [
            *[dict(item) for item in metadata.get("required_missing") or [] if isinstance(item, Mapping)],
            *[dict(item) for item in summary.get("required_missing") or [] if isinstance(item, Mapping)],
        ]
    )
    blocked_names = _claim_names(blocked_claims)
    allowed_claims = [
        claim
        for claim in _ordered_names([*list(metadata.get("allowed_claims") or []), *list(summary.get("allowed_claims") or [])])
        if claim not in blocked_names
    ]
    contract = dict(docs_runbook_refresh_contract or emit_docs_runbook_refresh_contract(
        summary,
        permission_counters=counters,
        duckdb_evidence_refs=evidence_refs,
    ))
    metadata["cr014_claim_boundary"] = summary
    metadata["claim_boundary_summary"] = summary
    metadata["allowed_claims"] = allowed_claims
    metadata["blocked_claims"] = blocked_claims
    metadata["required_missing"] = required_missing
    metadata["permission_counters"] = counters
    metadata["duckdb_evidence_refs"] = evidence_refs
    metadata["duckdb_evidence_policy"] = "reference_only"
    metadata["docs_runbook_refresh_contract"] = contract
    metadata["docs_runbook_refresh_policy"] = "metadata_only_no_docs_write"
    metadata["provider_fetches"] = 0
    metadata["lake_writes"] = 0
    metadata["credential_reads"] = 0
    metadata["legacy_data_operations"] = 0
    metadata["old_report_reads"] = 0
    metadata["old_report_overwrites"] = 0
    metadata["candidate_lake_scans"] = 0
    metadata["duckdb_opens"] = 0
    metadata["duckdb_sql_views"] = 0
    metadata["docs_writes"] = 0
    return sanitize_metadata_text(metadata)


def emit_docs_runbook_refresh_contract(
    claim_boundary_summary: Mapping[str, Any] | Any,
    *,
    ops_boundary: Mapping[str, Any] | None = None,
    permission_counters: Mapping[str, Any] | None = None,
    duckdb_evidence_refs: Sequence[Mapping[str, Any] | Any] = (),
) -> dict[str, Any]:
    """输出 README / USER-MANUAL / runbook 后续刷新所需的结构化输入。"""

    summary = _claim_boundary_payload(claim_boundary_summary)
    counters = assert_research_consumer_forbidden_operations(
        permission_counters or summary.get("permission_counters") or CR014_RESEARCH_CONSUMER_FORBIDDEN_COUNTERS
    ).counters
    evidence_refs = [
        evidence
        for evidence in (consume_duckdb_audit_evidence_ref(ref) for ref in duckdb_evidence_refs)
        if set(evidence) == {"run_id", "evidence_path", "parity_status", "audit_scope"}
    ]
    required_missing = [dict(item) for item in summary.get("required_missing") or [] if isinstance(item, Mapping)]
    blocked_claims = [dict(item) for item in summary.get("blocked_claims") or [] if isinstance(item, Mapping)]
    allowed_claims = _ordered_names(summary.get("allowed_claims") or [])
    boundary_states = {
        "candidate_unpublished": sum(1 for item in required_missing if item.get("gap_code") == "candidate_unpublished"),
        "published_current_truth": "available" if allowed_claims and not required_missing else "required_missing",
        "duckdb_audit_only": len(evidence_refs),
        "authorization_needed": sum(
            1
            for item in [*required_missing, *blocked_claims]
            if "authorization" in str(item.get("release_condition") or "")
        ),
    }
    return sanitize_metadata_text(
        {
            "contract_type": "cr014_docs_runbook_refresh_contract",
            "status": "metadata_only",
            "write_policy": "no_readme_or_docs_write_in_s07",
            "refresh_targets": ["README.md", "docs/USER-MANUAL.md", "runbook"],
            "boundary_states": boundary_states,
            "allowed_claims": allowed_claims,
            "blocked_claims": blocked_claims,
            "required_missing": required_missing,
            "permission_counters": counters,
            "duckdb_evidence_refs": evidence_refs,
            "duckdb_evidence_policy": "reference_only",
            "ops_boundary": dict(ops_boundary or {}),
            "forbidden_actions": [
                "provider_fetch",
                "lake_write",
                "credential_read",
                "legacy_data_operation",
                "old_report_read",
                "old_report_overwrite",
                "candidate_lake_scan",
                "duckdb_open",
                "duckdb_sql_view",
                "catalog_current_pointer_publish",
                "docs_write",
                "s09_real_execution",
            ],
        }
    )


def render_cr013_claim_boundary_summary(claim_boundary_summary: Mapping[str, Any]) -> str:
    """渲染 README / USER-MANUAL / 报告共用的 CR-013 声明边界段落。"""

    summary = sanitize_metadata_text(dict(claim_boundary_summary))
    categories = summary.get("claim_categories") if isinstance(summary.get("claim_categories"), Mapping) else {}
    lines = [
        "## CR-013 Claim Boundary Summary",
        "",
        f"- supported_window: `{summary.get('supported_window')}`",
        f"- blocked_window: `{summary.get('blocked_window')}`",
        f"- full_history_status: `{summary.get('full_history_status')}`",
        f"- formal_dataset_pass_denominator: `{summary.get('formal_dataset_pass_denominator')}`",
        f"- excluded_in_formal_pass_denominator_count: `{summary.get('pass_denominator_policy', {}).get('excluded_in_formal_pass_denominator_count')}`",
        "",
        "| 类别 | 项 |",
        "|---|---|",
    ]
    for category in ("supported", "research_only", "unsupported", "blocked"):
        values = categories.get(category) if isinstance(categories, Mapping) else []
        lines.append(f"| `{category}` | `{';'.join(str(item) for item in values)}` |")
    lines.extend(
        [
            "",
            "```json",
            json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True),
            "```",
        ]
    )
    return "\n".join(lines)


def build_experiment_realism_matrix(
    metadata: ResearchInputMetadata | Mapping[str, Any],
    *,
    experiment_ids: tuple[int, ...] = tuple(range(1, 17)),
) -> dict[str, Any]:
    """生成 16 个实验的真实性限制矩阵，不触发 backfill 或联网。"""

    metadata_dict = metadata_to_dict(_coerce_metadata(metadata))
    realism_mode = str(metadata_dict.get("realism_mode") or "exploratory")
    allowed_claims = list(metadata_dict.get("allowed_claims") or [])
    blocked_claims = list(metadata_dict.get("blocked_claims") or [])
    known_limitations = list(metadata_dict.get("known_limitations") or [])
    readiness = metadata_dict.get("readiness") if isinstance(metadata_dict.get("readiness"), Mapping) else {}
    rows: list[dict[str, Any]] = []
    for experiment_id in experiment_ids:
        entrypoint = _experiment_entrypoint(experiment_id)
        status = "n/a" if entrypoint == "N/A" else ("blocked" if realism_mode == "production_strict" and blocked_claims else "smoke_ready")
        limitations = list(known_limitations)
        if entrypoint == "N/A":
            limitations.append(
                {
                    "code": "experiment_entrypoint_not_available",
                    "experiment_id": f"{experiment_id:02d}",
                }
            )
        rows.append(
            {
                "experiment_id": f"{experiment_id:02d}",
                "entrypoint": entrypoint,
                "status": status,
                "realism_mode": realism_mode,
                "release_lineage": {
                    "manifest_run_id": metadata_dict.get("manifest_run_id", ""),
                    "source_run_id": metadata_dict.get("source_run_id", ""),
                    "lineage": metadata_dict.get("lineage", {}),
                },
                "quality": metadata_dict.get("quality", {}),
                "readiness": readiness,
                "pit": readiness.get("pit", {}) if isinstance(readiness, Mapping) else {},
                "w3": readiness.get("w3", {}) if isinstance(readiness, Mapping) else {},
                "allowed_claims": allowed_claims,
                "blocked_claims": blocked_claims,
                "known_limitations": limitations,
                "network_calls": 0,
                "auto_backfill": False,
            }
        )
    return {
        "ok": True,
        "report_type": "experiment_realism_matrix",
        "realism_mode": realism_mode,
        "experiment_count": len(rows),
        "rows": sanitize_metadata_text(rows),
        "network_calls": 0,
        "auto_backfill": False,
        "legacy_report_policy": LEGACY_REPORT_POLICY,
    }


def render_research_input_metadata_section(metadata: ResearchInputMetadata | Mapping[str, Any]) -> str:
    """渲染新报告强制携带的 metadata section。"""

    metadata_dict = sanitize_metadata_text(metadata_to_dict(_coerce_metadata(metadata)))
    return "\n".join(
        [
            "## Research Input Metadata",
            "",
            f"- schema_name: `{metadata_dict['schema_name']}`",
            f"- report_kind: `{metadata_dict['report_kind']}`",
            f"- coverage: `{metadata_dict['coverage_start']}` to `{metadata_dict['coverage_end']}`",
            f"- benchmark_status: `{metadata_dict['benchmark_status']}`",
            f"- universe_mode: `{metadata_dict['universe_mode']}`",
            f"- adjustment_policy: `{metadata_dict['adjustment_policy']}`",
            f"- label_available_end: `{metadata_dict['label_available_end']}`",
            f"- quality/readiness: `{metadata_dict['quality_status']}` / `{metadata_dict['readiness_status']}`",
            f"- legacy_report_policy: `{metadata_dict['legacy_report_policy']}`",
            "",
            "```json",
            json.dumps(metadata_dict, ensure_ascii=False, indent=2, sort_keys=True),
            "```",
        ]
    )


def attach_research_input_metadata(
    report_lines: list[str],
    metadata: ResearchInputMetadata | Mapping[str, Any],
) -> list[str]:
    """返回附加 metadata section 的新列表，不修改调用方原列表。"""

    return [*report_lines, "", render_research_input_metadata_section(metadata), ""]


def sanitize_metadata_text(value: Any) -> Any:
    """递归净化进入 Markdown / CSV 的 metadata 文本字段。"""

    if isinstance(value, Mapping):
        return {str(key): sanitize_metadata_text(item) for key, item in value.items()}
    if isinstance(value, list):
        return [sanitize_metadata_text(item) for item in value]
    return sanitize_tabular_text(value)


def _claim_boundary_payload(claim_boundary_summary: Mapping[str, Any] | Any) -> dict[str, Any]:
    to_dict = getattr(claim_boundary_summary, "to_dict", None)
    if callable(to_dict):
        payload = dict(to_dict())
    elif isinstance(claim_boundary_summary, Mapping):
        payload = dict(claim_boundary_summary)
    else:
        payload = metadata_to_dict(claim_boundary_summary)
    payload["allowed_claims"] = [
        dict(item) if isinstance(item, Mapping) else {"claim": str(item)}
        for item in payload.get("allowed_claims") or []
    ]
    payload["blocked_claims"] = [
        dict(item)
        for item in payload.get("blocked_claims") or []
        if isinstance(item, Mapping)
    ]
    payload["required_missing"] = [
        dict(item)
        for item in payload.get("required_missing") or []
        if isinstance(item, Mapping)
    ]
    payload.setdefault("permission_counters", dict(CR014_RESEARCH_CONSUMER_FORBIDDEN_COUNTERS))
    return sanitize_metadata_text(payload)


def _claim_names(rows: Sequence[Any]) -> set[str]:
    names: set[str] = set()
    for row in rows:
        if isinstance(row, Mapping):
            claim = str(row.get("claim") or "")
        else:
            claim = str(row or "")
        if claim:
            names.add(claim)
    return names


def _ordered_names(rows: Sequence[Any]) -> list[str]:
    output: list[str] = []
    for row in rows:
        if isinstance(row, Mapping):
            claim = str(row.get("claim") or "")
        else:
            claim = str(row or "")
        if claim and claim not in output:
            output.append(claim)
    return output


def _dedupe_rows(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    seen: set[tuple[str, str, str, str]] = set()
    output: list[dict[str, Any]] = []
    for row in rows:
        payload = dict(row)
        key = (
            str(payload.get("claim") or ""),
            str(payload.get("gap_code") or ""),
            str(payload.get("capability") or ""),
            str(payload.get("evidence_path") or ""),
        )
        if key in seen:
            continue
        seen.add(key)
        output.append(payload)
    return output


def _coerce_metadata(metadata: ResearchInputMetadata | Mapping[str, Any]) -> ResearchInputMetadata:
    if isinstance(metadata, ResearchInputMetadata):
        return metadata
    return build_research_input_metadata(metadata)


__all__ = (
    "attach_research_input_metadata",
    "attach_cr014_claim_boundary_metadata",
    "attach_report_claim_boundary",
    "build_claim_boundary_summary",
    "build_experiment_realism_matrix",
    "CR013_FORMAL_DATASETS",
    "CR013_UNSUPPORTED_DATA_ITEMS",
    "EXPERIMENT_REALISM_REGISTRY",
    "legacy_report_limitation",
    "read_unsupported_data_register",
    "emit_docs_runbook_refresh_contract",
    "render_cr013_claim_boundary_summary",
    "render_research_input_metadata_section",
    "sanitize_metadata_text",
)
