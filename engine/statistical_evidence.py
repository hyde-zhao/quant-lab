"""CR164 immutable statistical-evidence contracts and conservative aggregation.

The module is deliberately pure: it performs no file, environment, network,
credential, provider, broker, or runtime operations.  Callers must supply a
validated CR163 lineage projection and all method inputs explicitly.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, is_dataclass
from enum import Enum
import hashlib
import json
import math
from typing import Any, Mapping, Sequence


STATISTICAL_EVIDENCE_SCHEMA_VERSION = "statistical_evidence_v1"
SUMMARY_HASH_DOMAIN = "quant-lab.statistical-evidence-summary.v1"


class EvidenceStatus(str, Enum):
    PASS = "pass"
    FAIL = "fail"
    TYPED_UNAVAILABLE = "typed_unavailable"
    BLOCKED = "blocked"


class StatisticalMethod(str, Enum):
    BH = "bh"
    WRC = "wrc"
    SPA = "spa"
    PBO_CSCV = "pbo_cscv"
    DSR = "dsr"


_STATUS_SEVERITY = {
    EvidenceStatus.PASS: 0,
    EvidenceStatus.TYPED_UNAVAILABLE: 1,
    EvidenceStatus.FAIL: 2,
    EvidenceStatus.BLOCKED: 3,
}


@dataclass(frozen=True, slots=True)
class EvidenceIssue:
    code: str
    field: str
    message: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class StatisticalEvidenceInput:
    family_ref: str
    family_hash: str
    raw_trial_count: int
    candidate_ids: tuple[str, ...]
    candidate_membership_hash: str
    method_inputs: Mapping[str, Any] = field(default_factory=dict)
    schema_version: str = STATISTICAL_EVIDENCE_SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        return _json_value(asdict(self))


@dataclass(frozen=True, slots=True)
class EvidenceValidation:
    status: EvidenceStatus
    issues: tuple[EvidenceIssue, ...] = ()

    @property
    def passed(self) -> bool:
        return self.status is EvidenceStatus.PASS

    def to_dict(self) -> dict[str, Any]:
        return {"status": self.status.value, "issues": [item.to_dict() for item in self.issues]}


@dataclass(frozen=True, slots=True)
class MethodEvidence:
    method: StatisticalMethod
    status: EvidenceStatus
    family_ref: str
    family_hash: str
    raw_trial_count: int | None
    candidate_count: int
    input_hash: str
    config_hash: str
    result: Mapping[str, Any] = field(default_factory=dict)
    provenance: Mapping[str, Any] = field(default_factory=dict)
    reason_codes: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()
    evidence_ref: str = ""
    schema_version: str = STATISTICAL_EVIDENCE_SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        return _json_value(asdict(self))


@dataclass(frozen=True, slots=True)
class StatisticalEvidenceSummary:
    claim_id: str
    mandatory_methods: tuple[StatisticalMethod, ...]
    method_evidences: tuple[MethodEvidence, ...]
    status: EvidenceStatus
    reason_codes: tuple[str, ...]
    summary_hash: str
    limitations: tuple[str, ...] = ()
    schema_version: str = STATISTICAL_EVIDENCE_SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        return _json_value(asdict(self))


def canonical_json_bytes(value: Any) -> bytes:
    """Return deterministic JSON bytes, rejecting non-finite values."""

    normalized = _json_value(value)
    return json.dumps(
        normalized,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def canonical_hash(value: Any, *, domain: str = SUMMARY_HASH_DOMAIN) -> str:
    payload = {"domain": domain, "value": value}
    return f"sha256:{hashlib.sha256(canonical_json_bytes(payload)).hexdigest()}"


def candidate_membership_hash(candidate_ids: Sequence[str]) -> str:
    ids = _candidate_ids(candidate_ids)
    return canonical_hash(ids, domain="quant-lab.statistical-candidate-membership.v1")


def build_statistical_evidence_input(
    *,
    lineage_projection: Mapping[str, Any],
    candidate_ids: Sequence[str],
    method_inputs: Mapping[str, Any],
) -> StatisticalEvidenceInput:
    """Build an input without inferring or repairing lineage facts."""

    ids = _candidate_ids(candidate_ids)
    return StatisticalEvidenceInput(
        family_ref=str(lineage_projection.get("target_ref") or ""),
        family_hash=str(lineage_projection.get("target_hash") or ""),
        raw_trial_count=_strict_int(lineage_projection.get("raw_trial_count"), default=0),
        candidate_ids=ids,
        candidate_membership_hash=candidate_membership_hash(ids),
        method_inputs=_json_value(method_inputs),
    )


def validate_statistical_evidence_input(
    value: StatisticalEvidenceInput,
    *,
    method: StatisticalMethod | str | None = None,
) -> EvidenceValidation:
    issues: list[EvidenceIssue] = []
    unavailable: list[EvidenceIssue] = []
    if value.schema_version != STATISTICAL_EVIDENCE_SCHEMA_VERSION:
        issues.append(_issue("schema_version_unsupported", "schema_version", "Unsupported evidence schema."))
    if not value.family_ref:
        unavailable.append(_issue("family_ref_missing", "family_ref", "Sealed family ref is required."))
    if not value.family_hash:
        unavailable.append(_issue("family_hash_missing", "family_hash", "Sealed family hash is required."))
    if value.raw_trial_count < 1:
        unavailable.append(_issue("raw_trial_count_missing", "raw_trial_count", "Positive raw trial count is required."))
    try:
        ids = _candidate_ids(value.candidate_ids)
    except (TypeError, ValueError) as exc:
        ids = ()
        issues.append(_issue("candidate_identity_invalid", "candidate_ids", str(exc)))
    if ids and value.candidate_membership_hash != candidate_membership_hash(ids):
        issues.append(_issue("candidate_membership_hash_mismatch", "candidate_membership_hash", "Membership hash mismatch."))
    if ids and value.raw_trial_count != len(ids):
        issues.append(_issue("candidate_raw_trial_count_mismatch", "raw_trial_count", "Candidate count must equal sealed raw trial count."))
    try:
        canonical_json_bytes(value.method_inputs)
    except (TypeError, ValueError) as exc:
        issues.append(_issue("method_input_non_canonical", "method_inputs", str(exc)))
    selected = StatisticalMethod(method) if method is not None else None
    if selected is not None and selected.value not in value.method_inputs:
        unavailable.append(_issue("method_input_missing", selected.value, "Selected method input is missing."))
    if issues:
        return EvidenceValidation(EvidenceStatus.BLOCKED, tuple(issues + unavailable))
    if unavailable:
        return EvidenceValidation(EvidenceStatus.TYPED_UNAVAILABLE, tuple(unavailable))
    return EvidenceValidation(EvidenceStatus.PASS)


def make_method_evidence(
    *,
    method: StatisticalMethod | str,
    evidence_input: StatisticalEvidenceInput,
    status: EvidenceStatus | str,
    config: Mapping[str, Any],
    result: Mapping[str, Any] | None = None,
    provenance: Mapping[str, Any] | None = None,
    reason_codes: Sequence[str] = (),
    limitations: Sequence[str] = (),
    evidence_ref: str = "",
) -> MethodEvidence:
    selected = StatisticalMethod(method)
    normalized_status = EvidenceStatus(status)
    input_hash = canonical_hash(evidence_input.to_dict(), domain=f"quant-lab.{selected.value}.input.v1")
    config_hash = canonical_hash(config, domain=f"quant-lab.{selected.value}.config.v1")
    return MethodEvidence(
        method=selected,
        status=normalized_status,
        family_ref=evidence_input.family_ref,
        family_hash=evidence_input.family_hash,
        raw_trial_count=evidence_input.raw_trial_count,
        candidate_count=len(evidence_input.candidate_ids),
        input_hash=input_hash,
        config_hash=config_hash,
        result=_json_value(result or {}),
        provenance=_json_value(provenance or {}),
        reason_codes=tuple(sorted(set(reason_codes))),
        limitations=tuple(sorted(set(limitations))),
        evidence_ref=str(evidence_ref),
    )


def unavailable_method_evidence(
    method: StatisticalMethod | str,
    evidence_input: StatisticalEvidenceInput,
    *,
    reason_code: str,
    config: Mapping[str, Any] | None = None,
    limitations: Sequence[str] = (),
) -> MethodEvidence:
    return make_method_evidence(
        method=method,
        evidence_input=evidence_input,
        status=EvidenceStatus.TYPED_UNAVAILABLE,
        config=config or {},
        reason_codes=(reason_code,),
        limitations=limitations,
    )


def blocked_method_evidence(
    method: StatisticalMethod | str,
    evidence_input: StatisticalEvidenceInput,
    *,
    reason_codes: Sequence[str],
    config: Mapping[str, Any] | None = None,
) -> MethodEvidence:
    return make_method_evidence(
        method=method,
        evidence_input=evidence_input,
        status=EvidenceStatus.BLOCKED,
        config=config or {},
        reason_codes=reason_codes,
    )


def validate_method_evidence(
    evidence: MethodEvidence,
    *,
    expected_input: StatisticalEvidenceInput,
) -> EvidenceValidation:
    issues: list[EvidenceIssue] = []
    expected_input_hash = canonical_hash(
        expected_input.to_dict(), domain=f"quant-lab.{evidence.method.value}.input.v1"
    )
    if evidence.input_hash != expected_input_hash:
        issues.append(_issue("method_input_hash_mismatch", "input_hash", "Method evidence input hash mismatch."))
    if evidence.family_ref != expected_input.family_ref or evidence.family_hash != expected_input.family_hash:
        issues.append(_issue("method_family_identity_mismatch", "family_ref", "Method evidence family identity mismatch."))
    if evidence.raw_trial_count != expected_input.raw_trial_count:
        issues.append(_issue("method_raw_trial_count_mismatch", "raw_trial_count", "Method raw count mismatch."))
    if evidence.candidate_count != len(expected_input.candidate_ids):
        issues.append(_issue("method_candidate_count_mismatch", "candidate_count", "Method candidate count mismatch."))
    if evidence.status is not EvidenceStatus.PASS and not evidence.reason_codes:
        issues.append(_issue("method_reason_missing", "reason_codes", "Non-pass evidence requires a reason code."))
    try:
        canonical_json_bytes(evidence.to_dict())
    except (TypeError, ValueError) as exc:
        issues.append(_issue("method_evidence_non_canonical", "result", str(exc)))
    return EvidenceValidation(EvidenceStatus.BLOCKED if issues else EvidenceStatus.PASS, tuple(issues))


def aggregate_statistical_evidence(
    *,
    claim_id: str,
    mandatory_methods: Sequence[StatisticalMethod | str],
    evidences: Sequence[MethodEvidence],
) -> StatisticalEvidenceSummary:
    """Aggregate by BLOCKED > FAIL > TYPED_UNAVAILABLE > PASS.

    The mandatory denominator is explicit and cannot shrink to only methods
    that happened to produce evidence.
    """

    mandatory = tuple(StatisticalMethod(item) for item in mandatory_methods)
    if not claim_id.strip() or not mandatory or len(set(mandatory)) != len(mandatory):
        raise ValueError("claim_id and unique mandatory_methods are required")
    by_method: dict[StatisticalMethod, MethodEvidence] = {}
    duplicate = False
    for evidence in evidences:
        if evidence.method in by_method:
            duplicate = True
        by_method[evidence.method] = evidence
    selected: list[MethodEvidence] = []
    missing: list[StatisticalMethod] = []
    for method in mandatory:
        evidence = by_method.get(method)
        if evidence is None:
            missing.append(method)
        else:
            selected.append(evidence)
    reasons: set[str] = set()
    if duplicate:
        reasons.add("duplicate_method_evidence")
    if missing:
        reasons.add("method_evidence_ref_missing")
    if any(not item.evidence_ref for item in selected):
        reasons.add("method_evidence_ref_missing")
    if reasons:
        status = EvidenceStatus.BLOCKED
    else:
        status = max((item.status for item in selected), key=_STATUS_SEVERITY.__getitem__)
        if status is EvidenceStatus.BLOCKED:
            reasons.add("method_disagreement_conservative_block")
        elif status is EvidenceStatus.FAIL:
            reasons.add("method_policy_failed")
        elif status is EvidenceStatus.TYPED_UNAVAILABLE:
            reasons.add("mandatory_method_unavailable")
        else:
            reasons.add("all_mandatory_methods_passed")
    for item in selected:
        reasons.update(item.reason_codes)
    limitations = tuple(sorted({item for evidence in selected for item in evidence.limitations}))
    unsigned = {
        "schema_version": STATISTICAL_EVIDENCE_SCHEMA_VERSION,
        "claim_id": claim_id,
        "mandatory_methods": [item.value for item in mandatory],
        "method_evidences": [item.to_dict() for item in selected],
        "status": status.value,
        "reason_codes": sorted(reasons),
        "limitations": list(limitations),
    }
    return StatisticalEvidenceSummary(
        claim_id=claim_id,
        mandatory_methods=mandatory,
        method_evidences=tuple(selected),
        status=status,
        reason_codes=tuple(sorted(reasons)),
        summary_hash=canonical_hash(unsigned),
        limitations=limitations,
    )


def project_summary(summary: StatisticalEvidenceSummary, *, consumer_id: str) -> dict[str, Any]:
    if not consumer_id.strip():
        raise ValueError("consumer_id is required")
    return {
        "schema_version": STATISTICAL_EVIDENCE_SCHEMA_VERSION,
        "consumer_id": consumer_id,
        "claim_id": summary.claim_id,
        "status": summary.status.value,
        "summary_hash": summary.summary_hash,
        "mandatory_methods": [item.value for item in summary.mandatory_methods],
        "method_evidence_refs": [item.evidence_ref for item in summary.method_evidences],
        "reason_codes": list(summary.reason_codes),
        "limitations": list(summary.limitations),
        "effective_trial_count": None,
        "effective_trial_count_ref": "",
        "effective_trial_count_method": "",
        "effective_trial_count_availability": EvidenceStatus.TYPED_UNAVAILABLE.value,
    }


def _json_value(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value):
        return _json_value(asdict(value))
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("non-finite floats are not supported")
        return value
    if isinstance(value, Mapping):
        result: dict[str, Any] = {}
        for key, item in value.items():
            if not isinstance(key, str):
                raise TypeError("mapping keys must be strings")
            result[key] = _json_value(item)
        return dict(sorted(result.items()))
    if isinstance(value, (tuple, list)):
        return [_json_value(item) for item in value]
    raise TypeError(f"unsupported JSON value: {type(value).__name__}")


def _candidate_ids(values: Sequence[str]) -> tuple[str, ...]:
    result = tuple(values)
    if not result or any(not isinstance(item, str) or not item.strip() for item in result):
        raise ValueError("candidate_ids must contain non-empty strings")
    if len(set(result)) != len(result):
        raise ValueError("candidate_ids must be unique")
    return result


def _strict_int(value: Any, *, default: int) -> int:
    return value if isinstance(value, int) and not isinstance(value, bool) else default


def _issue(code: str, field: str, message: str) -> EvidenceIssue:
    return EvidenceIssue(code=code, field=field, message=message)


__all__ = [
    "EvidenceIssue",
    "EvidenceStatus",
    "EvidenceValidation",
    "MethodEvidence",
    "StatisticalEvidenceInput",
    "StatisticalEvidenceSummary",
    "StatisticalMethod",
    "aggregate_statistical_evidence",
    "blocked_method_evidence",
    "build_statistical_evidence_input",
    "candidate_membership_hash",
    "canonical_hash",
    "canonical_json_bytes",
    "make_method_evidence",
    "project_summary",
    "unavailable_method_evidence",
    "validate_method_evidence",
    "validate_statistical_evidence_input",
]
