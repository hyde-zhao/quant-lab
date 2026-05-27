"""CR014 Explicit Publish Gate 合同。"""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from typing import Any, Mapping

from .catalog import CatalogPointer, validate_catalog_pointer
from .contracts import (
    QUALITY_STATUS_PASS,
    READINESS_STATUS_AVAILABLE,
)
from .manifest import (
    ManifestCompletenessResult,
    ManifestRecord,
    validate_manifest_record,
)

PUBLISH_NOT_AUTHORIZED = "publish_not_authorized"
QUALITY_NOT_PUBLISHABLE = "quality_not_publishable"
READINESS_NOT_PUBLISHABLE = "readiness_not_publishable"
LIFECYCLE_DENOMINATOR_MISSING = "lifecycle_denominator_missing"
CATALOG_POINTER_INCOMPLETE_FOR_PUBLISH = "catalog_pointer_incomplete"
REAL_PUBLISH_NOT_AUTHORIZED = "real_publish_not_authorized"


@dataclass(frozen=True, slots=True)
class PublishIntent:
    """显式发布意图；approval_token 只校验存在，不在结果中回显。"""

    publish: bool = False
    approval_token: str | None = None
    approved_by: str | None = None
    reason: str | None = None

    @property
    def is_explicit(self) -> bool:
        return self.publish and bool(str(self.approval_token or "").strip())


@dataclass(frozen=True, slots=True)
class PublishGateResult:
    publish_allowed: bool
    pointer_changes: int
    manifest_complete: bool
    catalog_pointer_complete: bool
    quality_status: str
    readiness_status: str
    error_codes: tuple[str, ...] = ()
    details: tuple[dict[str, Any], ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class PointerUpdateResult:
    publish_allowed: bool
    dry_run: bool
    pointer_changes: int
    catalog_writes: int
    real_lake_writes: int
    error_codes: tuple[str, ...] = ()
    details: tuple[dict[str, Any], ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _as_mapping(value: Any) -> dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, Mapping):
        return dict(value)
    if isinstance(value, CatalogPointer):
        return value.to_dict()
    if isinstance(value, ManifestRecord):
        return value.to_dict()
    if is_dataclass(value):
        return asdict(value)
    raise TypeError(f"不支持的 publish gate 输入类型: {type(value)!r}")


def _manifest_result(
    manifest: ManifestRecord | Mapping[str, Any] | ManifestCompletenessResult | None,
) -> ManifestCompletenessResult:
    if isinstance(manifest, ManifestCompletenessResult):
        return manifest
    if manifest is None:
        return ManifestCompletenessResult(
            passed=False,
            publish_allowed=False,
            missing_fields=("manifest",),
            error_codes=("manifest_incomplete",),
            details=({"code": "manifest_incomplete", "missing_fields": ["manifest"]},),
        )
    return validate_manifest_record(manifest)


def _value_from_inputs(field: str, *payloads: Mapping[str, Any]) -> Any:
    for payload in payloads:
        value = payload.get(field)
        if value is not None:
            return value
    return None


def _has_lifecycle_denominator(
    lifecycle: Mapping[str, Any],
    candidate: Mapping[str, Any],
    manifest: Mapping[str, Any],
) -> bool:
    denominator = _value_from_inputs("coverage_denominator", lifecycle, candidate)
    denominator_ref = _value_from_inputs("lifecycle_denominator_ref", lifecycle, manifest)
    if denominator is not None and not isinstance(denominator, bool):
        if isinstance(denominator, int) and denominator >= 0:
            return True
    return bool(str(denominator_ref or "").strip())


def validate_publish_candidate(
    candidate: CatalogPointer | Mapping[str, Any],
    quality: Mapping[str, Any] | None = None,
    manifest: ManifestRecord | Mapping[str, Any] | ManifestCompletenessResult | None = None,
    lifecycle: Mapping[str, Any] | None = None,
    intent: PublishIntent | None = None,
) -> PublishGateResult:
    """校验发布候选；Validate / parity PASS 不会隐式更新 pointer。"""

    candidate_payload = _as_mapping(candidate)
    quality_payload = dict(quality or {})
    lifecycle_payload = dict(lifecycle or {})
    manifest_check = _manifest_result(manifest)
    manifest_payload = _as_mapping(manifest) if manifest is not None and not isinstance(manifest, ManifestCompletenessResult) else {}
    pointer_check = validate_catalog_pointer(candidate_payload)

    quality_status = str(
        _value_from_inputs("quality_status", quality_payload, candidate_payload, manifest_payload)
        or ""
    )
    readiness_status = str(
        _value_from_inputs("readiness_status", quality_payload, candidate_payload, manifest_payload)
        or ""
    )
    error_codes: list[str] = []
    details: list[dict[str, Any]] = []

    if not pointer_check.passed:
        error_codes.append(CATALOG_POINTER_INCOMPLETE_FOR_PUBLISH)
        details.extend(pointer_check.details)
    if not manifest_check.passed:
        error_codes.extend(manifest_check.error_codes)
        details.extend(manifest_check.details)
    if quality_status != QUALITY_STATUS_PASS:
        error_codes.append(QUALITY_NOT_PUBLISHABLE)
        details.append({"code": QUALITY_NOT_PUBLISHABLE, "quality_status": quality_status or "missing"})
    if readiness_status != READINESS_STATUS_AVAILABLE:
        error_codes.append(READINESS_NOT_PUBLISHABLE)
        details.append(
            {
                "code": READINESS_NOT_PUBLISHABLE,
                "readiness_status": readiness_status or "missing",
            }
        )
    if not _has_lifecycle_denominator(lifecycle_payload, candidate_payload, manifest_payload):
        error_codes.append(LIFECYCLE_DENOMINATOR_MISSING)
        details.append({"code": LIFECYCLE_DENOMINATOR_MISSING})
    if intent is None or not intent.is_explicit:
        error_codes.append(PUBLISH_NOT_AUTHORIZED)
        details.append({"code": PUBLISH_NOT_AUTHORIZED})

    unique_codes = tuple(dict.fromkeys(error_codes))
    publish_allowed = not unique_codes
    return PublishGateResult(
        publish_allowed=publish_allowed,
        pointer_changes=1 if publish_allowed else 0,
        manifest_complete=manifest_check.passed,
        catalog_pointer_complete=pointer_check.passed,
        quality_status=quality_status,
        readiness_status=readiness_status,
        error_codes=unique_codes,
        details=tuple(details),
    )


def publish_current_pointer(
    store: object,
    candidate: CatalogPointer | Mapping[str, Any],
    intent: PublishIntent,
    *,
    dry_run: bool = True,
    quality: Mapping[str, Any] | None = None,
    manifest: ManifestRecord | Mapping[str, Any] | ManifestCompletenessResult | None = None,
    lifecycle: Mapping[str, Any] | None = None,
) -> PointerUpdateResult:
    """返回 current pointer 更新合同结果；默认 dry-run 且不写 catalog。"""

    del store
    gate = validate_publish_candidate(
        candidate,
        quality=quality,
        manifest=manifest,
        lifecycle=lifecycle,
        intent=intent,
    )
    if not gate.publish_allowed:
        return PointerUpdateResult(
            publish_allowed=False,
            dry_run=dry_run,
            pointer_changes=0,
            catalog_writes=0,
            real_lake_writes=0,
            error_codes=gate.error_codes,
            details=gate.details,
        )
    if dry_run:
        return PointerUpdateResult(
            publish_allowed=True,
            dry_run=True,
            pointer_changes=1,
            catalog_writes=0,
            real_lake_writes=0,
            details=({"code": "dry_run_only", "catalog_current_pointer_publish": 0},),
        )
    return PointerUpdateResult(
        publish_allowed=False,
        dry_run=False,
        pointer_changes=0,
        catalog_writes=0,
        real_lake_writes=0,
        error_codes=(REAL_PUBLISH_NOT_AUTHORIZED,),
        details=(
            {
                "code": REAL_PUBLISH_NOT_AUTHORIZED,
                "reason": "当前 Story 只授权 explicit publish gate dry-run 合同，不执行真实 current pointer 写入",
            },
        ),
    )


__all__ = [
    "CATALOG_POINTER_INCOMPLETE_FOR_PUBLISH",
    "LIFECYCLE_DENOMINATOR_MISSING",
    "PUBLISH_NOT_AUTHORIZED",
    "QUALITY_NOT_PUBLISHABLE",
    "READINESS_NOT_PUBLISHABLE",
    "REAL_PUBLISH_NOT_AUTHORIZED",
    "PointerUpdateResult",
    "PublishGateResult",
    "PublishIntent",
    "publish_current_pointer",
    "validate_publish_candidate",
]
