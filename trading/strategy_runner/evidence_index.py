"""Lightweight runner evidence index contract."""

from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path
from typing import Any, Mapping

from trading.strategy_runner.adapters import zero_cr091_operation_counters
from trading.strategy_runner.evidence import assert_redacted
from trading.strategy_runner.result import RunResult


RUN_EVIDENCE_INDEX_SCHEMA_VERSION = "cr134-runner-evidence-index-v1"


@dataclass(frozen=True, slots=True)
class RunEvidenceIndex:
    run_id: str
    status: str
    passed: bool
    package_id: str
    run_result_ref: str = ""
    evidence_summary_ref: str = "RunResult.evidence_summary"
    evidence_summary_excerpt: Mapping[str, Any] | None = None
    forbidden_operation_counters: Mapping[str, int] = field(default_factory=zero_cr091_operation_counters)
    qmt_allowed: bool = False
    not_authorization: bool = True
    schema_version: str = RUN_EVIDENCE_INDEX_SCHEMA_VERSION

    @classmethod
    def from_run_result(
        cls,
        result: RunResult,
        *,
        run_result_path: str | Path | None = None,
    ) -> "RunEvidenceIndex":
        return cls(
            run_id=result.run_id,
            status=result.status,
            passed=result.passed,
            package_id=result.package_id,
            run_result_ref="" if run_result_path is None else Path(run_result_path).as_posix(),
            evidence_summary_excerpt=_evidence_summary_excerpt(result.evidence_summary),
            forbidden_operation_counters=dict(result.forbidden_operation_counters),
            qmt_allowed=result.qmt_allowed,
            not_authorization=result.not_authorization,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "run_id": self.run_id,
            "status": self.status,
            "passed": self.passed,
            "package_id": self.package_id,
            "run_result_ref": self.run_result_ref,
            "evidence_summary_ref": self.evidence_summary_ref,
            "evidence_summary_excerpt": (
                None if self.evidence_summary_excerpt is None else dict(self.evidence_summary_excerpt)
            ),
            "forbidden_operation_counters": dict(self.forbidden_operation_counters),
            "qmt_allowed": self.qmt_allowed,
            "not_authorization": self.not_authorization,
        }


def write_run_evidence_index(
    path: str | Path,
    result: RunResult,
    *,
    run_result_path: str | Path | None = None,
) -> None:
    if not result.passed:
        raise ValueError("blocked_evidence_index_requires_pass_result")
    if result.not_authorization is not True or result.qmt_allowed is not False:
        raise ValueError("blocked_evidence_index_authorization_boundary")
    if any(value != 0 for value in result.forbidden_operation_counters.values()):
        raise ValueError("blocked_evidence_index_forbidden_operations")
    payload = RunEvidenceIndex.from_run_result(result, run_result_path=run_result_path).to_dict()
    assert_redacted(payload)
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _evidence_summary_excerpt(summary: Mapping[str, Any] | None) -> dict[str, Any] | None:
    if summary is None:
        return None
    excerpt_keys = (
        "schema_version",
        "status",
        "run_id",
        "package_id",
        "adapter_type",
        "delivery_target_id",
        "execution_adapter_id",
        "strategy_id",
        "target_count",
        "order_intent_count",
        "readonly_reconciliation_status",
        "forbidden_operation_counters",
        "redaction_assurance",
        "sensitive_field_hits",
        "not_authorization",
    )
    return {key: summary[key] for key in excerpt_keys if key in summary}
