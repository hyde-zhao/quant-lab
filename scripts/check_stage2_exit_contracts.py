#!/usr/bin/env python3
"""生成并校验 Stage 2 的精确七项合同退出结果。

该工具只消费调用方显式传入的仓库内 manifest 与 evidence refs，不扫描外部数据源、
不读取凭据，也不修补历史合同。前六项失败由 CR-157 owner 或新治理 CR 处理；
第七项 evidence index/C4 失败回到 CR-169。
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Mapping, Sequence


STAGE2_CONTRACT_IDS = (
    "factor_spec",
    "factor_run_spec",
    "factor_panel",
    "label_window",
    "evaluation",
    "portfolio_risk",
    "admission_package_evidence_index",
)
HISTORICAL_REMEDIATION_ROUTE = "CR-157-owner-or-new-governance-CR"
C4_REMEDIATION_ROUTE = "CR-169-NEEDS_REWORK"
VALID_STATUSES = {"PASS", "FAIL", "BLOCKED"}


def build_stage2_exit_verification(
    entries: Sequence[Mapping[str, Any]],
    *,
    project_root: Path | None = None,
    checked_at: str | None = None,
) -> dict[str, Any]:
    """构造机器可审计的七项退出结果；不得从缺失证据推断 PASS。"""

    by_id = {str(entry.get("contract_id", "")): entry for entry in entries}
    unknown = sorted(set(by_id).difference(STAGE2_CONTRACT_IDS))
    if unknown:
        raise ValueError(f"unknown Stage2 contract ids: {unknown}")

    items: list[dict[str, Any]] = []
    for index, contract_id in enumerate(STAGE2_CONTRACT_IDS):
        entry = by_id.get(contract_id, {})
        declared = str(entry.get("status", "BLOCKED")).upper()
        evidence_refs = tuple(str(ref).strip() for ref in entry.get("evidence_refs", ()) if str(ref).strip())
        route = HISTORICAL_REMEDIATION_ROUTE if index < 6 else C4_REMEDIATION_ROUTE
        status = declared if declared in VALID_STATUSES else "BLOCKED"
        notes = str(entry.get("notes", "")).strip()

        invalid_refs: list[str] = []
        if project_root is not None:
            invalid_refs = [ref for ref in evidence_refs if not _valid_repo_evidence_ref(ref, project_root)]
        if not evidence_refs or invalid_refs:
            status = "BLOCKED"
            reason = "evidence_refs_missing" if not evidence_refs else "evidence_refs_invalid_or_outside_route"
            notes = "; ".join(part for part in (notes, reason) if part)

        items.append(
            {
                "contract_id": contract_id,
                "status": status,
                "evidence_refs": list(evidence_refs),
                "notes": notes,
                "route_on_fail": route,
            }
        )

    statuses = [item["status"] for item in items]
    decision = "PASS" if statuses == ["PASS"] * 7 else ("FAIL" if "FAIL" in statuses else "BLOCKED")
    blockers = [
        {"contract_id": item["contract_id"], "status": item["status"], "route": item["route_on_fail"]}
        for item in items
        if item["status"] != "PASS"
    ]
    routes = list(dict.fromkeys(item["route"] for item in blockers))
    return {
        "schema_version": 1,
        "check_id": "STAGE2-EXIT-VERIFICATION",
        "cr_id": "CR-169",
        "checked_at": checked_at or datetime.now(timezone.utc).isoformat(),
        "items": items,
        "counts": {"required": 7, "pass": statuses.count("PASS"), "fail": statuses.count("FAIL"), "blocked": statuses.count("BLOCKED")},
        "decision": decision,
        "stage2_complete": decision == "PASS",
        "stage3_entry_ready": False,
        "blockers": blockers,
        "follow_up_routes": routes,
        "operation_counts": {
            "real_data_read": 0,
            "provider_fetch": 0,
            "runtime_operation": 0,
            "trading_operation": 0,
            "remote_write": 0,
        },
    }


def _valid_repo_evidence_ref(ref: str, project_root: Path) -> bool:
    root = project_root.resolve()
    path = Path(ref)
    candidate = path.resolve() if path.is_absolute() else (root / path).resolve()
    allowed_roots = (root, (root / "process").resolve())
    within_route = any(candidate == allowed or allowed in candidate.parents for allowed in allowed_roots)
    return within_route and candidate.is_file()


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, type=Path, help="显式七项 evidence manifest")
    parser.add_argument("--output", required=True, type=Path, help="result JSON 输出路径")
    parser.add_argument("--project-root", default=Path.cwd(), type=Path)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    root = args.project_root.resolve()
    if not _valid_repo_evidence_ref(str(args.manifest), root):
        raise SystemExit("manifest 必须是 repository/process route 内的已有文件")
    output = args.output.resolve() if args.output.is_absolute() else (root / args.output).resolve()
    allowed_outputs = ((root / "process").resolve(),)
    if not any(output == allowed or allowed in output.parents for allowed in allowed_outputs):
        raise SystemExit("output 必须位于 process route")

    payload = json.loads(args.manifest.read_text(encoding="utf-8"))
    result = build_stage2_exit_verification(payload.get("items", ()), project_root=root)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"decision": result["decision"], "pass": result["counts"]["pass"], "output": str(output)}, ensure_ascii=False))
    return 0 if result["decision"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
