"""Offline strategy runner result contract."""

from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path
from typing import Any, Mapping

from trading.strategy_runner.adapters import AdapterResult, zero_cr091_operation_counters
from trading.strategy_runner.evidence import EvidenceSummary


RUN_RESULT_SCHEMA_VERSION = "cr128-run-result-v1"


@dataclass(frozen=True, slots=True)
class RunResult:
    run_id: str
    status: str
    package_id: str = ""
    adapter_status: str = ""
    evidence_status: str = ""
    target_count: int = 0
    order_intent_count: int = 0
    blocked_reasons: tuple[str, ...] = ()
    target_portfolio: Mapping[str, Any] | None = None
    evidence_summary: Mapping[str, Any] | None = None
    forbidden_operation_counters: Mapping[str, int] = field(default_factory=zero_cr091_operation_counters)
    qmt_allowed: bool = False
    not_authorization: bool = True
    schema_version: str = RUN_RESULT_SCHEMA_VERSION

    @property
    def passed(self) -> bool:
        return self.status == "pass"

    @classmethod
    def from_adapter_and_evidence(
        cls,
        *,
        run_id: str,
        package_id: str,
        adapter_result: AdapterResult,
        evidence: EvidenceSummary,
    ) -> "RunResult":
        target_count = 0 if adapter_result.target_portfolio is None else len(adapter_result.target_portfolio.target_symbols)
        status = "pass" if adapter_result.passed and evidence.status == "pass" else "blocked"
        blocked_reasons = tuple(sorted(set(adapter_result.blocked_reasons + _evidence_blocks(evidence))))
        return cls(
            run_id=run_id,
            status=status,
            package_id=package_id,
            adapter_status=adapter_result.status,
            evidence_status=evidence.status,
            target_count=target_count,
            order_intent_count=len(adapter_result.order_intents),
            blocked_reasons=blocked_reasons,
            target_portfolio=None if adapter_result.target_portfolio is None else adapter_result.target_portfolio.to_dict(),
            evidence_summary=evidence.to_dict(),
            forbidden_operation_counters=evidence.forbidden_operation_counters,
        )

    @classmethod
    def blocked(cls, *, run_id: str, reason: str, package_id: str = "") -> "RunResult":
        return cls(
            run_id=run_id,
            status="blocked",
            package_id=package_id,
            adapter_status="blocked",
            evidence_status="not_built",
            blocked_reasons=(reason,),
        )

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "RunResult":
        if payload.get("schema_version") != RUN_RESULT_SCHEMA_VERSION:
            raise ValueError("blocked_run_result_schema_mismatch")
        return cls(
            run_id=str(payload.get("run_id") or ""),
            status=str(payload.get("status") or ""),
            package_id=str(payload.get("package_id") or ""),
            adapter_status=str(payload.get("adapter_status") or ""),
            evidence_status=str(payload.get("evidence_status") or ""),
            target_count=int(payload.get("target_count") or 0),
            order_intent_count=int(payload.get("order_intent_count") or 0),
            blocked_reasons=tuple(str(item) for item in payload.get("blocked_reasons") or ()),
            target_portfolio=payload.get("target_portfolio"),
            evidence_summary=payload.get("evidence_summary"),
            forbidden_operation_counters={
                str(key): int(value or 0)
                for key, value in dict(payload.get("forbidden_operation_counters") or {}).items()
            },
            qmt_allowed=bool(payload.get("qmt_allowed", False)),
            not_authorization=bool(payload.get("not_authorization", True)),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "run_id": self.run_id,
            "status": self.status,
            "passed": self.passed,
            "package_id": self.package_id,
            "adapter_status": self.adapter_status,
            "evidence_status": self.evidence_status,
            "target_count": self.target_count,
            "order_intent_count": self.order_intent_count,
            "blocked_reasons": list(self.blocked_reasons),
            "target_portfolio": None if self.target_portfolio is None else dict(self.target_portfolio),
            "evidence_summary": None if self.evidence_summary is None else dict(self.evidence_summary),
            "forbidden_operation_counters": dict(self.forbidden_operation_counters),
            "qmt_allowed": self.qmt_allowed,
            "not_authorization": self.not_authorization,
        }


def write_run_result(path: str | Path, result: RunResult) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result.to_dict(), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def read_run_result(path: str | Path) -> RunResult:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("blocked_run_result_not_mapping")
    return RunResult.from_dict(payload)


def _evidence_blocks(evidence: EvidenceSummary) -> tuple[str, ...]:
    if evidence.status == "pass":
        return ()
    return ("blocked_evidence_status",)
