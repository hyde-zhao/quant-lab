"""Read-side audit record helpers for market data readers."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Mapping

import pandas as pd


@dataclass(frozen=True, slots=True)
class ReadAuditRecord:
    audit_id: str
    dataset: str
    reader_name: str
    status: str
    issue_codes: tuple[str, ...]
    catalog_run_id: str | None
    source_run_ids: tuple[str, ...]
    requested_as_of: str | None
    row_count: int
    strategy_run_id: str | None = None
    remediation_action: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "audit_id": self.audit_id,
            "dataset": self.dataset,
            "reader_name": self.reader_name,
            "status": self.status,
            "issue_codes": list(self.issue_codes),
            "catalog_run_id": self.catalog_run_id,
            "source_run_ids": list(self.source_run_ids),
            "requested_as_of": self.requested_as_of,
            "row_count": self.row_count,
            "strategy_run_id": self.strategy_run_id,
            "remediation_action": self.remediation_action,
        }


def build_read_audit_record(
    dataset: str,
    result: Any,
    *,
    reader_name: str,
    requested_as_of: str | pd.Timestamp | None = None,
    strategy_run_id: str | None = None,
) -> ReadAuditRecord:
    """Build a deterministic, JSON-safe read audit record from a ReaderResult-like object."""

    status = str(getattr(result, "status", "unknown") or "unknown")
    issues = tuple(_issue_codes(getattr(result, "issues", ())))
    frame = getattr(result, "frame", None)
    row_count = int(len(frame)) if isinstance(frame, pd.DataFrame) else 0
    source_run_ids = _source_run_ids(frame)
    catalog_entry = getattr(result, "catalog_entry", None)
    catalog_run_id = _text_or_none(getattr(catalog_entry, "latest_manifest_run_id", None))
    remediation = getattr(result, "remediation_spec", None)
    remediation_action = _remediation_action(remediation)
    as_of_text = _text_or_none(requested_as_of)
    audit_id = _audit_id(
        {
            "dataset": str(dataset),
            "reader_name": str(reader_name),
            "status": status,
            "issue_codes": list(issues),
            "catalog_run_id": catalog_run_id,
            "source_run_ids": list(source_run_ids),
            "requested_as_of": as_of_text,
            "row_count": row_count,
            "strategy_run_id": strategy_run_id,
            "remediation_action": remediation_action,
        }
    )
    return ReadAuditRecord(
        audit_id=audit_id,
        dataset=str(dataset),
        reader_name=str(reader_name),
        status=status,
        issue_codes=issues,
        catalog_run_id=catalog_run_id,
        source_run_ids=source_run_ids,
        requested_as_of=as_of_text,
        row_count=row_count,
        strategy_run_id=_text_or_none(strategy_run_id),
        remediation_action=remediation_action,
    )


def _issue_codes(issues: Any) -> list[str]:
    codes: list[str] = []
    for issue in issues or ():
        if isinstance(issue, Mapping):
            code = issue.get("code")
        else:
            code = getattr(issue, "code", None)
        if code is not None and str(code).strip():
            codes.append(str(code))
    return sorted(dict.fromkeys(codes))


def _source_run_ids(frame: Any) -> tuple[str, ...]:
    if not isinstance(frame, pd.DataFrame) or "source_run_id" not in frame.columns:
        return ()
    values = [str(item) for item in frame["source_run_id"].dropna().unique() if str(item).strip()]
    return tuple(sorted(dict.fromkeys(values)))


def _remediation_action(remediation: Any) -> str | None:
    if isinstance(remediation, Mapping):
        return _text_or_none(remediation.get("action"))
    return _text_or_none(getattr(remediation, "action", None))


def _text_or_none(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _audit_id(payload: Mapping[str, Any]) -> str:
    body = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return "read-audit-" + hashlib.sha256(body.encode("utf-8")).hexdigest()[:24]


__all__ = ["ReadAuditRecord", "build_read_audit_record"]
