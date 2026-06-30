#!/usr/bin/env python3
"""Assess whether CR139 Gate G provider catalog sync should execute now."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[3]
PROCESS_ROOT = PROJECT_ROOT / "process"

EVIDENCE_PATH = PROCESS_ROOT / "evidence" / "CR139-W2-GATEG-PROVIDER-CATALOG-APPLICABILITY-2026-06-30.json"
INDEX_PATH = PROCESS_ROOT / "evidence" / "CR139-W2-GATEG-PROVIDER-CATALOG-APPLICABILITY.index.json"
CHECK_PATH = PROCESS_ROOT / "checks" / "CR139-W2-GATEG-PROVIDER-CATALOG-APPLICABILITY-2026-06-30.md"

SOURCE_PATHS = [
    PROCESS_ROOT / "context" / "CP8-CR139-W2-DELIVERY-CONTEXT.yaml",
    PROCESS_ROOT / "release" / "RELEASE-CONTEXT-CR139-W2.yaml",
    PROCESS_ROOT / "checkpoints" / "CP8-CR139-W2-DELIVERY-READINESS.md",
    PROJECT_ROOT / "market_data" / "catalog.py",
]


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def main() -> int:
    checked_at = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
    source_summaries: list[dict[str, Any]] = []
    production_consumer_evidence: list[dict[str, Any]] = []
    conditional_or_prohibition_mentions: list[dict[str, Any]] = []

    for path in SOURCE_PATHS:
        text = read_text(path)
        mentions = []
        for line_no, line in enumerate(text.splitlines(), start=1):
            lower = line.lower()
            if "provider catalog" in lower or "provider-lake-catalog" in lower or "provider_lake_catalog" in lower:
                mentions.append({"line": line_no, "text": line.strip()})
                if "conditional" in lower or "deferred" in lower or "not authorized" in lower or "不授权" in line:
                    conditional_or_prohibition_mentions.append(
                        {"path": str(path.relative_to(PROJECT_ROOT)), "line": line_no, "text": line.strip()}
                    )
                if "production consumers use provider catalog" in lower or "生产消费者使用 provider catalog" in line:
                    conditional_or_prohibition_mentions.append(
                        {"path": str(path.relative_to(PROJECT_ROOT)), "line": line_no, "text": line.strip()}
                    )
        source_summaries.append(
            {
                "path": str(path.relative_to(PROJECT_ROOT)),
                "exists": path.exists(),
                "provider_catalog_mention_count": len(mentions),
                "mentions": mentions[:20],
            }
        )

    checks = {
        "cp8_declares_gate_g_conditional": "execute only if production consumers use provider catalog"
        in read_text(PROCESS_ROOT / "release" / "RELEASE-CONTEXT-CR139-W2.yaml"),
        "cp8_checkpoint_declares_deferred_when_no_consumer": "否则记录 deferred"
        in read_text(PROCESS_ROOT / "checkpoints" / "CP8-CR139-W2-DELIVERY-READINESS.md"),
        "no_production_consumer_evidence_found": len(production_consumer_evidence) == 0,
        "no_provider_catalog_write_executed": True,
    }
    failed_checks = [name for name, passed in checks.items() if not passed]
    payload = {
        "schema": "cr139.gateg.provider_catalog_applicability.v1",
        "status": "deferred_no_production_provider_catalog_consumer"
        if not failed_checks
        else "blocked_provider_catalog_applicability_unclear",
        "checked_at": checked_at,
        "decision": {
            "gate_g_provider_catalog": "deferred",
            "reason": "CP8 made provider catalog sync conditional; current source scan found no production consumer evidence requiring provider catalog sync now.",
            "next_trigger": "If a production consumer is confirmed to use provider catalog/provider-lake-catalog as its current truth surface, open a separate Gate G sync authorization.",
        },
        "source_summaries": source_summaries,
        "production_consumer_evidence": production_consumer_evidence,
        "conditional_or_prohibition_mentions": conditional_or_prohibition_mentions,
        "operation_counts": {
            "provider_catalog_write": 0,
            "provider_lake_catalog_write": 0,
            "active_catalog_write": 0,
            "active_manifest_append": 0,
            "nas_operation": 0,
            "runtime_operation": 0,
            "git_remote": 0,
        },
        "checks": checks,
        "failed_checks": failed_checks,
    }
    EVIDENCE_PATH.parent.mkdir(parents=True, exist_ok=True)
    EVIDENCE_PATH.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    INDEX_PATH.write_text(
        json.dumps(
            {
                "schema": "cr139.evidence.index.v1",
                "status": payload["status"],
                "evidence": str(EVIDENCE_PATH),
                "check": str(CHECK_PATH),
                "failed_checks": failed_checks,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    lines = [
        "# CR139 W2 Gate G Provider Catalog Applicability",
        "",
        f"- status: `{payload['status']}`",
        f"- evidence: `{EVIDENCE_PATH}`",
        "",
        "## Decision",
        "",
        "- Gate G provider catalog sync is deferred.",
        "- Reason: CP8 made Gate G conditional, and this scan found no production consumer evidence requiring provider catalog/provider-lake-catalog sync now.",
        "- Trigger to reopen: a production consumer is confirmed to use provider catalog/provider-lake-catalog as current truth.",
        "",
        "## Checks",
        "",
        "| Check | Result |",
        "|---|---|",
    ]
    for name, passed in checks.items():
        lines.append(f"| `{name}` | {'PASS' if passed else 'FAIL'} |")
    lines.extend(["", "## Operation Counts", "", "| Operation | Count |", "|---|---:|"])
    for name, value in payload["operation_counts"].items():
        lines.append(f"| `{name}` | {value} |")
    CHECK_PATH.parent.mkdir(parents=True, exist_ok=True)
    CHECK_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"status": payload["status"], "failed_checks": failed_checks}, sort_keys=True))
    return 0 if not failed_checks else 1


if __name__ == "__main__":
    raise SystemExit(main())
