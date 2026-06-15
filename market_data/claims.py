"""CR014-S05 claim boundary 合同。"""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from typing import Any, Mapping, Sequence

from .contracts import CR014_CLAIM_FULL_A_SINCE_INCEPTION
from .readiness import (
    GAP_CANDIDATE_UNPUBLISHED,
    GAP_CATALOG_POINTER_MISSING,
    GAP_PERMISSION_COUNTER_VIOLATION,
    GapRegister,
    GapRegisterRow,
    PUBLISH_STATUS_PUBLISHED,
    _counter_violations,
    _normalise_permission_counters,
)
from .unsupported import (
    CR014_BASE_RELEASE_CONDITIONS,
    CR014_REAL_VWAP_CAPABILITIES,
    CR014_REAL_VWAP_RELEASE_CONDITIONS,
    CR014_UNSUPPORTED_CAPABILITY_SET,
    CR014_UNSUPPORTED_PRODUCTION_CLAIMS,
    UnsupportedDecisionMatrix,
    blocked_claim_rows,
    coerce_unsupported_decision_matrix,
    get_cr014_unsupported_decision_matrix,
    required_missing_rows,
    validate_release_conditions_complete,
)

CLAIM_FULL_A_SINCE_INCEPTION_PRODUCTION = "full_a_since_inception_production"
CLAIM_BOUNDARY_INVALID = "claim_boundary_invalid"
CLAIM_REQUIRED_FIELD_MISSING = "claim_required_field_missing"
CLAIM_ALLOWED_WHILE_BLOCKED = "claim_allowed_while_blocked"
CLAIM_CANDIDATE_UNPUBLISHED_ALLOWED = "candidate_unpublished_allowed"
CLAIM_PERMISSION_COUNTER_VIOLATION = GAP_PERMISSION_COUNTER_VIOLATION
CLAIM_UNSUPPORTED_ALLOWED = "unsupported_claim_allowed"
CLAIM_UNSUPPORTED_RELEASE_CONDITION_MISSING = "unsupported_release_condition_missing"

STRUCTURED_GAP_FIELDS: tuple[str, ...] = (
    "gap_code",
    "evidence_path",
    "remediation",
    "release_condition",
)


@dataclass(frozen=True, slots=True)
class ClaimBoundarySummary:
    allowed_claims: tuple[dict[str, Any], ...]
    blocked_claims: tuple[dict[str, Any], ...]
    required_missing: tuple[dict[str, Any], ...]
    permission_counters: dict[str, int]
    full_a_allowed_claim_count: int
    legacy_baseline_refs: tuple[str, ...] = ()
    status: str = "blocked"

    def to_dict(self) -> dict[str, Any]:
        return {
            "allowed_claims": [dict(item) for item in self.allowed_claims],
            "blocked_claims": [dict(item) for item in self.blocked_claims],
            "required_missing": [dict(item) for item in self.required_missing],
            "permission_counters": dict(self.permission_counters),
            "full_a_allowed_claim_count": self.full_a_allowed_claim_count,
            "legacy_baseline_refs": list(self.legacy_baseline_refs),
            "status": self.status,
        }


@dataclass(frozen=True, slots=True)
class ClaimBoundaryValidationResult:
    passed: bool
    error_codes: tuple[str, ...] = ()
    details: tuple[dict[str, Any], ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "error_codes": list(self.error_codes),
            "details": [dict(item) for item in self.details],
        }


@dataclass(frozen=True, slots=True)
class ReadinessSideEffectCheck:
    passed: bool
    counters: dict[str, int]
    error_codes: tuple[str, ...] = ()
    details: tuple[dict[str, Any], ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "counters": dict(self.counters),
            "error_codes": list(self.error_codes),
            "details": [dict(item) for item in self.details],
        }


def _payload(value: Any) -> dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, Mapping):
        return dict(value)
    to_dict = getattr(value, "to_dict", None)
    if callable(to_dict):
        return dict(to_dict())
    if is_dataclass(value):
        return asdict(value)
    if hasattr(value, "__dict__"):
        return dict(vars(value))
    return {}


def _allowed_claim_payloads(values: Sequence[Any]) -> tuple[dict[str, Any], ...]:
    output: list[dict[str, Any]] = []
    for value in values:
        if isinstance(value, Mapping):
            payload = dict(value)
        else:
            payload = {"claim": str(value)}
        if payload.get("claim"):
            output.append(payload)
    return tuple(output)


def _claim_name(value: Any) -> str:
    if isinstance(value, Mapping):
        return str(value.get("claim") or "")
    return str(value or "")


def _dedupe_mapping_rows(rows: Sequence[Mapping[str, Any]]) -> tuple[dict[str, Any], ...]:
    seen: set[tuple[str, str, str, str, str]] = set()
    output: list[dict[str, Any]] = []
    for row in rows:
        payload = dict(row)
        key = (
            str(payload.get("claim") or ""),
            str(payload.get("capability") or ""),
            str(payload.get("gap_code") or ""),
            str(payload.get("reason_code") or payload.get("blocked_reason") or ""),
            str(payload.get("evidence_path") or ""),
        )
        if key in seen:
            continue
        seen.add(key)
        output.append(payload)
    return tuple(output)


def _summary_payload(summary: ClaimBoundarySummary | Mapping[str, Any] | None) -> dict[str, Any]:
    if summary is None:
        return {}
    if isinstance(summary, ClaimBoundarySummary):
        return summary.to_dict()
    return dict(summary)


def _gap_rows(gap_register: GapRegister | Mapping[str, Any] | Sequence[Any]) -> tuple[dict[str, Any], ...]:
    if isinstance(gap_register, GapRegister):
        return tuple(row.to_dict() for row in gap_register.rows)
    if isinstance(gap_register, Mapping):
        rows = gap_register.get("rows", ())
        return tuple(_payload(row) for row in rows)
    return tuple(row.to_dict() if isinstance(row, GapRegisterRow) else _payload(row) for row in gap_register)


def _legacy_refs(gap_register: GapRegister | Mapping[str, Any] | Sequence[Any]) -> tuple[str, ...]:
    if isinstance(gap_register, GapRegister):
        return gap_register.legacy_baseline_refs
    if isinstance(gap_register, Mapping):
        return tuple(str(item) for item in gap_register.get("legacy_baseline_refs", ()))
    return ()


def _permission_counters(
    gap_register: GapRegister | Mapping[str, Any] | Sequence[Any],
    permission_counters: Mapping[str, Any] | None,
) -> dict[str, int]:
    base: Mapping[str, Any] | None = permission_counters
    if base is None and isinstance(gap_register, GapRegister):
        base = gap_register.permission_counters
    elif base is None and isinstance(gap_register, Mapping):
        base = gap_register.get("permission_counters")
    return _normalise_permission_counters(base)


def _publish_complete(publish_status: Mapping[str, Any] | Sequence[str] | str | None) -> bool:
    if publish_status is None:
        return False
    if isinstance(publish_status, str):
        return publish_status == PUBLISH_STATUS_PUBLISHED
    if isinstance(publish_status, Mapping):
        return bool(publish_status) and all(str(value) == PUBLISH_STATUS_PUBLISHED for value in publish_status.values())
    values = tuple(publish_status)
    return bool(values) and all(str(value) == PUBLISH_STATUS_PUBLISHED for value in values)


def _blocked_claim_from_gap(gap: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "claim": gap.get("claim") or CR014_CLAIM_FULL_A_SINCE_INCEPTION,
        "claim_scope": CLAIM_FULL_A_SINCE_INCEPTION_PRODUCTION,
        "dataset": gap.get("dataset"),
        "gap_code": gap.get("gap_code"),
        "evidence_path": gap.get("evidence_path"),
        "remediation": gap.get("remediation"),
        "release_condition": gap.get("release_condition"),
        "severity": gap.get("severity", "P0"),
    }


def _required_missing_from_gap(gap: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "dataset": gap.get("dataset"),
        "gap_code": gap.get("gap_code"),
        "evidence_path": gap.get("evidence_path"),
        "remediation": gap.get("remediation"),
        "release_condition": gap.get("release_condition"),
    }


def build_claim_boundary(
    gap_register: GapRegister | Mapping[str, Any] | Sequence[Any],
    publish_status: Mapping[str, Any] | Sequence[str] | str | None = None,
    unsupported_refs: Sequence[Mapping[str, Any] | str] = (),
    permission_counters: Mapping[str, Any] | None = None,
) -> ClaimBoundarySummary:
    """构建 allowed_claims / blocked_claims / required_missing 边界。"""

    gaps = _gap_rows(gap_register)
    counters = _permission_counters(gap_register, permission_counters)
    counter_violations = _counter_violations(counters)
    blocked = [_blocked_claim_from_gap(gap) for gap in gaps]
    required_missing = [_required_missing_from_gap(gap) for gap in gaps]

    for ref in unsupported_refs:
        payload = _payload(ref) if not isinstance(ref, str) else {"evidence_path": ref}
        item = {
            "dataset": payload.get("dataset", "unsupported"),
            "gap_code": payload.get("gap_code", "unsupported_claim_boundary"),
            "evidence_path": payload.get("evidence_path") or payload.get("ref") or "unsupported://missing",
            "remediation": payload.get("remediation", "route_unsupported_scope_to_future_story"),
            "release_condition": payload.get(
                "release_condition",
                "future Story, CP5 and user authorization approve this unsupported scope",
            ),
        }
        required_missing.append(item)
        blocked.append(
            {
                "claim": payload.get("claim", CR014_CLAIM_FULL_A_SINCE_INCEPTION),
                "claim_scope": CLAIM_FULL_A_SINCE_INCEPTION_PRODUCTION,
                **item,
                "severity": payload.get("severity", "P0"),
            }
        )

    if counter_violations:
        item = {
            "claim": CR014_CLAIM_FULL_A_SINCE_INCEPTION,
            "claim_scope": CLAIM_FULL_A_SINCE_INCEPTION_PRODUCTION,
            "dataset": "permission",
            "gap_code": GAP_PERMISSION_COUNTER_VIOLATION,
            "evidence_path": "permission_counters://cr014-s05",
            "remediation": "reset_forbidden_operation_counters_and_rerun_offline",
            "release_condition": "provider_fetch, lake_write, credential_read and old_report_overwrite counters are all 0",
            "severity": "P0",
        }
        blocked.append(item)
        required_missing.append({key: item[key] for key in STRUCTURED_GAP_FIELDS if key in item} | {"dataset": "permission"})

    publish_complete = _publish_complete(publish_status)
    if not publish_complete and not blocked:
        item = {
            "claim": CR014_CLAIM_FULL_A_SINCE_INCEPTION,
            "claim_scope": CLAIM_FULL_A_SINCE_INCEPTION_PRODUCTION,
            "dataset": "publish_status",
            "gap_code": GAP_CATALOG_POINTER_MISSING,
            "evidence_path": "publish_status://missing",
            "remediation": "provide_published_catalog_current_pointer_status",
            "release_condition": "all P0 datasets have explicit published current truth status",
            "severity": "P0",
        }
        blocked.append(item)
        required_missing.append({key: item[key] for key in STRUCTURED_GAP_FIELDS if key in item} | {"dataset": "publish_status"})
    full_a_allowed = not blocked and publish_complete
    allowed = (
        (
            {
                "claim": CR014_CLAIM_FULL_A_SINCE_INCEPTION,
                "claim_scope": CLAIM_FULL_A_SINCE_INCEPTION_PRODUCTION,
                "production": True,
                "release_condition": "all P0 gates passed and catalog current pointers are published",
            },
        )
        if full_a_allowed
        else ()
    )
    return ClaimBoundarySummary(
        allowed_claims=tuple(allowed),
        blocked_claims=tuple(dict(item) for item in blocked),
        required_missing=tuple(dict(item) for item in required_missing),
        permission_counters=counters,
        full_a_allowed_claim_count=1 if full_a_allowed else 0,
        legacy_baseline_refs=_legacy_refs(gap_register),
        status="allowed" if full_a_allowed else "blocked",
    )


def resolve_microstructure_claim_boundary(
    requested_claims: Sequence[str] = (),
    decision_matrix: UnsupportedDecisionMatrix | Mapping[str, Any] | Sequence[Any] | None = None,
    s05_claim_boundary: ClaimBoundarySummary | Mapping[str, Any] | None = None,
) -> ClaimBoundarySummary:
    """把 CR014-S08 unsupported matrix 合并进 S05 claim boundary。

    该函数只追加 W3 / microstructure / real VWAP 的 blocked / required
    rows，不删除 S05 既有 blocked claims，也不把 close proxy 或
    amount/volume 派生字段提升为 production real VWAP claim。
    """

    _ = requested_claims
    matrix = (
        get_cr014_unsupported_decision_matrix()
        if decision_matrix is None
        else coerce_unsupported_decision_matrix(decision_matrix)
    )
    base = _summary_payload(s05_claim_boundary)
    counters = _normalise_permission_counters(base.get("permission_counters"))
    allowed = list(_allowed_claim_payloads(base.get("allowed_claims") or ()))
    blocked = [dict(item) for item in base.get("blocked_claims") or () if isinstance(item, Mapping)]
    required = [dict(item) for item in base.get("required_missing") or () if isinstance(item, Mapping)]
    full_a_allowed_claim_count = int(base.get("full_a_allowed_claim_count") or 0)
    legacy_refs = tuple(str(item) for item in base.get("legacy_baseline_refs") or ())
    status = str(base.get("status") or "")

    if s05_claim_boundary is None:
        missing_s05 = {
            "claim": CR014_CLAIM_FULL_A_SINCE_INCEPTION,
            "claim_scope": CLAIM_FULL_A_SINCE_INCEPTION_PRODUCTION,
            "dataset": "s05_claim_boundary",
            "gap_code": "s05_claim_boundary_missing",
            "evidence_path": "claim_boundary://cr014-s05/missing",
            "remediation": "provide_verified_cr014_s05_claim_boundary_summary",
            "release_condition": "CR014-S05 CP6 and CP7 pass before S08 consumption",
            "severity": "P0",
        }
        blocked.append(missing_s05)
        required.append({key: missing_s05[key] for key in STRUCTURED_GAP_FIELDS if key in missing_s05} | {"dataset": "s05_claim_boundary"})
        full_a_allowed_claim_count = 0
        status = "blocked"

    validation = validate_release_conditions_complete(matrix)
    if not validation.passed:
        for detail in validation.details:
            capability = str(detail.get("capability") or "unknown")
            release_missing = {
                "claim": "unsupported_capability_release_condition",
                "claim_scope": "unsupported_capability_production",
                "capability": capability,
                "dataset": "unsupported",
                "gap_code": CLAIM_UNSUPPORTED_RELEASE_CONDITION_MISSING,
                "evidence_path": f"unsupported://cr014-s08/{capability}",
                "remediation": "complete_source_interface_story_cp5_user_authorization_release_condition",
                "release_condition": list(detail.get("missing_release_condition") or ()),
                "production_allowed_claim": False,
                "severity": "P0",
            }
            blocked.append(release_missing)
            required.append({key: release_missing[key] for key in STRUCTURED_GAP_FIELDS if key in release_missing} | {"dataset": "unsupported", "capability": capability})

    blocked = list(_dedupe_mapping_rows([*blocked, *blocked_claim_rows(matrix)]))
    required = list(_dedupe_mapping_rows([*required, *required_missing_rows(matrix)]))
    unsupported_claims = set(CR014_UNSUPPORTED_PRODUCTION_CLAIMS)
    allowed = [item for item in allowed if _claim_name(item) not in unsupported_claims]

    return ClaimBoundarySummary(
        allowed_claims=tuple(allowed),
        blocked_claims=tuple(blocked),
        required_missing=tuple(required),
        permission_counters=counters,
        full_a_allowed_claim_count=full_a_allowed_claim_count,
        legacy_baseline_refs=legacy_refs,
        status=status or ("blocked" if blocked else "allowed"),
    )


def validate_unsupported_claim_boundary(
    summary: ClaimBoundarySummary | Mapping[str, Any],
) -> ClaimBoundaryValidationResult:
    """校验 S08 unsupported claims 不进入 allowed production claims。"""

    payload = summary.to_dict() if isinstance(summary, ClaimBoundarySummary) else dict(summary)
    allowed = tuple(dict(item) for item in payload.get("allowed_claims", ()) if isinstance(item, Mapping))
    blocked = tuple(dict(item) for item in payload.get("blocked_claims", ()) if isinstance(item, Mapping))
    error_codes: list[str] = []
    details: list[dict[str, Any]] = []

    allowed_names = {_claim_name(item) for item in allowed}
    unsupported_allowed = sorted(allowed_names.intersection(CR014_UNSUPPORTED_PRODUCTION_CLAIMS))
    if unsupported_allowed:
        error_codes.append(CLAIM_UNSUPPORTED_ALLOWED)
        details.append({"allowed_claims": unsupported_allowed})

    for row in blocked:
        capability = str(row.get("capability") or "")
        if capability not in CR014_UNSUPPORTED_CAPABILITY_SET:
            continue
        if row.get("production_allowed_claim") is not False:
            error_codes.append(CLAIM_UNSUPPORTED_ALLOWED)
            details.append({"capability": capability, "row": row})
        release_condition = tuple(str(item) for item in row.get("release_condition") or ())
        required = set(CR014_BASE_RELEASE_CONDITIONS)
        if capability in CR014_REAL_VWAP_CAPABILITIES:
            required.update(CR014_REAL_VWAP_RELEASE_CONDITIONS)
        missing = sorted(required.difference(release_condition))
        if missing:
            error_codes.append(CLAIM_UNSUPPORTED_RELEASE_CONDITION_MISSING)
            details.append({"capability": capability, "missing_release_condition": missing})

    return ClaimBoundaryValidationResult(
        passed=not error_codes,
        error_codes=tuple(dict.fromkeys(error_codes)),
        details=tuple(details),
    )


def validate_claim_boundary(summary: ClaimBoundarySummary | Mapping[str, Any]) -> ClaimBoundaryValidationResult:
    """校验 claim boundary 的结构化字段和 fail-closed 规则。"""

    payload = summary.to_dict() if isinstance(summary, ClaimBoundarySummary) else dict(summary)
    blocked = tuple(dict(item) for item in payload.get("blocked_claims", ()))
    required_missing = tuple(dict(item) for item in payload.get("required_missing", ()))
    allowed = tuple(dict(item) for item in payload.get("allowed_claims", ()))
    counters = _normalise_permission_counters(payload.get("permission_counters"))
    error_codes: list[str] = []
    details: list[dict[str, Any]] = []

    for collection_name, rows in (("blocked_claims", blocked), ("required_missing", required_missing)):
        for row in rows:
            missing_fields = tuple(field for field in STRUCTURED_GAP_FIELDS if not row.get(field))
            if missing_fields:
                error_codes.append(CLAIM_REQUIRED_FIELD_MISSING)
                details.append(
                    {
                        "collection": collection_name,
                        "missing_fields": list(missing_fields),
                        "row": row,
                    }
                )

    full_a_blocking_rows = [
        item for item in blocked if not item.get("claim") or item.get("claim") == CR014_CLAIM_FULL_A_SINCE_INCEPTION
    ]
    if full_a_blocking_rows and any(item.get("claim") == CR014_CLAIM_FULL_A_SINCE_INCEPTION for item in allowed):
        error_codes.append(CLAIM_ALLOWED_WHILE_BLOCKED)
        details.append({"blocked_count": len(blocked), "allowed_claims": list(allowed)})
    if any(item.get("gap_code") == GAP_CANDIDATE_UNPUBLISHED for item in blocked) and allowed:
        error_codes.append(CLAIM_CANDIDATE_UNPUBLISHED_ALLOWED)
    violations = _counter_violations(counters)
    if violations or any(item.get("gap_code") == GAP_PERMISSION_COUNTER_VIOLATION for item in blocked):
        error_codes.append(CLAIM_PERMISSION_COUNTER_VIOLATION)
        details.append({"non_zero_counters": list(violations)})
    expected_allowed_count = 0 if full_a_blocking_rows or violations else len(
        [item for item in allowed if item.get("claim") == CR014_CLAIM_FULL_A_SINCE_INCEPTION]
    )
    if int(payload.get("full_a_allowed_claim_count") or 0) != expected_allowed_count:
        error_codes.append(CLAIM_BOUNDARY_INVALID)
        details.append(
            {
                "full_a_allowed_claim_count": payload.get("full_a_allowed_claim_count"),
                "expected": expected_allowed_count,
            }
        )

    unique_codes = tuple(dict.fromkeys(error_codes))
    return ClaimBoundaryValidationResult(
        passed=not unique_codes,
        error_codes=unique_codes,
        details=tuple(details),
    )


def assert_no_readiness_side_effects(
    summary_or_counters: ClaimBoundarySummary | Mapping[str, Any],
) -> ReadinessSideEffectCheck:
    """断言 S05 readiness / claim 合同未触发真实副作用。"""

    payload = (
        summary_or_counters.to_dict()
        if isinstance(summary_or_counters, ClaimBoundarySummary)
        else dict(summary_or_counters)
    )
    counters = _normalise_permission_counters(payload.get("permission_counters", payload))
    violations = _counter_violations(counters)
    if violations:
        return ReadinessSideEffectCheck(
            passed=False,
            counters=counters,
            error_codes=(CLAIM_PERMISSION_COUNTER_VIOLATION,),
            details=({"non_zero_counters": list(violations)},),
        )
    return ReadinessSideEffectCheck(passed=True, counters=counters)


__all__ = [
    "CLAIM_ALLOWED_WHILE_BLOCKED",
    "CLAIM_BOUNDARY_INVALID",
    "CLAIM_CANDIDATE_UNPUBLISHED_ALLOWED",
    "CLAIM_FULL_A_SINCE_INCEPTION_PRODUCTION",
    "CLAIM_PERMISSION_COUNTER_VIOLATION",
    "CLAIM_REQUIRED_FIELD_MISSING",
    "CLAIM_UNSUPPORTED_ALLOWED",
    "CLAIM_UNSUPPORTED_RELEASE_CONDITION_MISSING",
    "ClaimBoundarySummary",
    "ClaimBoundaryValidationResult",
    "ReadinessSideEffectCheck",
    "STRUCTURED_GAP_FIELDS",
    "assert_no_readiness_side_effects",
    "build_claim_boundary",
    "resolve_microstructure_claim_boundary",
    "validate_claim_boundary",
    "validate_unsupported_claim_boundary",
]
