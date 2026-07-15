"""Method-neutral strategy evidence envelope primitives for CR-166.

The module is intentionally value-only.  It does not discover plugins, read
paths, inspect the environment, dereference evidence refs, or mutate a store.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, is_dataclass
from enum import Enum
import hashlib
import json
import math
from typing import Any, Mapping, Sequence


STRATEGY_EVIDENCE_ENVELOPE_SCHEMA_VERSION = "strategy_evidence_envelope_v1"
STRATEGY_EVIDENCE_ENVELOPE_HASH_DOMAIN = "quant-lab.strategy-evidence-envelope.v1"
STRATEGY_EVIDENCE_INVENTORY_HASH_DOMAIN = "quant-lab.strategy-evidence-inventory.v1"


class EvidenceAvailability(str, Enum):
    PRESENT = "present"
    TYPED_UNAVAILABLE = "typed_unavailable"
    NOT_APPLICABLE_WITH_REASON = "not_applicable_with_reason"
    BLOCKED = "blocked"


class ComponentCatalogStatus(str, Enum):
    ACTIVE = "active"
    RESERVED = "reserved"
    UNKNOWN = "unknown"


COMPONENT_CATALOG: Mapping[tuple[str, str], ComponentCatalogStatus] = {
    ("walk_forward_oos", "v1"): ComponentCatalogStatus.ACTIVE,
    ("economic_cost", "v1"): ComponentCatalogStatus.ACTIVE,
    ("capacity_liquidity", "v1"): ComponentCatalogStatus.ACTIVE,
    ("capacity_liquidity", "reserved"): ComponentCatalogStatus.RESERVED,
}


@dataclass(frozen=True, slots=True)
class StrategyEvidenceIssue:
    code: str
    field: str
    message: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class StrategyEvidenceValidation:
    availability: EvidenceAvailability
    issues: tuple[StrategyEvidenceIssue, ...] = ()

    @property
    def passed(self) -> bool:
        return self.availability is EvidenceAvailability.PRESENT

    def to_dict(self) -> dict[str, Any]:
        return {
            "availability": self.availability.value,
            "issues": [item.to_dict() for item in self.issues],
        }


@dataclass(frozen=True, slots=True)
class ComponentDescriptor:
    component_type: str
    component_schema_version: str
    required: bool
    component_ref: str = ""
    component_hash: str = ""
    availability: EvidenceAvailability | str = EvidenceAvailability.TYPED_UNAVAILABLE
    reason_codes: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["availability"] = EvidenceAvailability(self.availability).value
        data["reason_codes"] = list(self.reason_codes)
        return canonical_json_value(data)


@dataclass(frozen=True, slots=True)
class StrategyEvidenceEnvelope:
    evidence_kind: str
    subject_ref: str
    components: tuple[ComponentDescriptor, ...]
    logical_provenance: Mapping[str, Any]
    authorization_summary: Mapping[str, Any]
    limitations: tuple[str, ...]
    reason_codes: tuple[str, ...]
    inventory_hash: str
    envelope_hash: str
    schema_version: str = STRATEGY_EVIDENCE_ENVELOPE_SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        return canonical_json_value(asdict(self))

    def unsigned_dict(self) -> dict[str, Any]:
        data = self.to_dict()
        data.pop("envelope_hash", None)
        return data


def canonical_json_value(value: Any) -> Any:
    """Normalize the supported finite JSON subset without touching external state."""

    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value):
        return canonical_json_value(asdict(value))
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
            result[key] = canonical_json_value(item)
        return dict(sorted(result.items()))
    if isinstance(value, (tuple, list)):
        return [canonical_json_value(item) for item in value]
    raise TypeError(f"unsupported JSON value: {type(value).__name__}")


def canonical_json_bytes(value: Any) -> bytes:
    """Return deterministic UTF-8 JSON bytes for the supported value subset."""

    return json.dumps(
        canonical_json_value(value),
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def canonical_hash(value: Any, *, domain: str) -> str:
    """Hash a value in an explicit domain; neutral callers get no default domain."""

    if not isinstance(domain, str) or not domain.strip():
        raise ValueError("domain is required")
    payload = {"domain": domain, "value": value}
    return f"sha256:{hashlib.sha256(canonical_json_bytes(payload)).hexdigest()}"


def component_catalog_status(component_type: str, schema_version: str) -> ComponentCatalogStatus:
    return COMPONENT_CATALOG.get((component_type, schema_version), ComponentCatalogStatus.UNKNOWN)


def build_strategy_evidence_envelope(
    *,
    evidence_kind: str,
    subject_ref: str,
    components: Sequence[ComponentDescriptor],
    logical_provenance: Mapping[str, Any],
    authorization_summary: Mapping[str, Any],
    limitations: Sequence[str] = (),
    reason_codes: Sequence[str] = (),
) -> StrategyEvidenceEnvelope:
    ordered = tuple(
        sorted(
            components,
            key=lambda item: (item.component_type, item.component_schema_version, item.component_ref),
        )
    )
    inventory = [item.to_dict() for item in ordered]
    inventory_hash = canonical_hash(inventory, domain=STRATEGY_EVIDENCE_INVENTORY_HASH_DOMAIN)
    unsigned = {
        "schema_version": STRATEGY_EVIDENCE_ENVELOPE_SCHEMA_VERSION,
        "evidence_kind": str(evidence_kind),
        "subject_ref": str(subject_ref),
        "components": inventory,
        "logical_provenance": canonical_json_value(logical_provenance),
        "authorization_summary": canonical_json_value(authorization_summary),
        "limitations": sorted({str(item) for item in limitations if str(item)}),
        "reason_codes": sorted({str(item) for item in reason_codes if str(item)}),
        "inventory_hash": inventory_hash,
    }
    return StrategyEvidenceEnvelope(
        evidence_kind=str(evidence_kind),
        subject_ref=str(subject_ref),
        components=ordered,
        logical_provenance=canonical_json_value(logical_provenance),
        authorization_summary=canonical_json_value(authorization_summary),
        limitations=tuple(unsigned["limitations"]),
        reason_codes=tuple(unsigned["reason_codes"]),
        inventory_hash=inventory_hash,
        envelope_hash=canonical_hash(unsigned, domain=STRATEGY_EVIDENCE_ENVELOPE_HASH_DOMAIN),
    )


def validate_strategy_evidence_envelope(envelope: StrategyEvidenceEnvelope) -> StrategyEvidenceValidation:
    blocked: list[StrategyEvidenceIssue] = []
    unavailable: list[StrategyEvidenceIssue] = []
    if envelope.schema_version != STRATEGY_EVIDENCE_ENVELOPE_SCHEMA_VERSION:
        blocked.append(_issue("envelope_schema_unsupported", "schema_version", "Unsupported envelope schema."))
    if not envelope.evidence_kind.strip():
        unavailable.append(_issue("evidence_kind_missing", "evidence_kind", "Evidence kind is required."))
    if not envelope.subject_ref.strip():
        unavailable.append(_issue("subject_ref_missing", "subject_ref", "Subject ref is required."))
    identities: set[tuple[str, str, str]] = set()
    for descriptor in envelope.components:
        availability = EvidenceAvailability(descriptor.availability)
        identity = (descriptor.component_type, descriptor.component_schema_version, descriptor.component_ref)
        if identity in identities:
            blocked.append(_issue("component_identity_duplicate", "components", "Component identity must be unique."))
        identities.add(identity)
        catalog_status = component_catalog_status(descriptor.component_type, descriptor.component_schema_version)
        if catalog_status is ComponentCatalogStatus.UNKNOWN and descriptor.required:
            blocked.append(_issue("mandatory_component_unknown", "components", "Unknown mandatory component is blocked."))
        elif catalog_status is ComponentCatalogStatus.RESERVED and descriptor.required:
            unavailable.append(_issue("mandatory_component_reserved", "components", "Reserved component is unavailable."))
        if availability is EvidenceAvailability.PRESENT and (not descriptor.component_ref or not descriptor.component_hash):
            blocked.append(_issue("present_component_identity_missing", "components", "Present component requires ref and hash."))
        if availability is EvidenceAvailability.BLOCKED:
            blocked.append(_issue("component_blocked", "components", "A mandatory evidence component is blocked."))
        elif descriptor.required and availability is not EvidenceAvailability.PRESENT:
            unavailable.append(_issue("mandatory_component_unavailable", "components", "Mandatory component is unavailable."))
    try:
        expected_inventory = canonical_hash(
            [item.to_dict() for item in envelope.components],
            domain=STRATEGY_EVIDENCE_INVENTORY_HASH_DOMAIN,
        )
        if expected_inventory != envelope.inventory_hash:
            blocked.append(_issue("inventory_hash_mismatch", "inventory_hash", "Component inventory hash mismatch."))
        if canonical_hash(envelope.unsigned_dict(), domain=STRATEGY_EVIDENCE_ENVELOPE_HASH_DOMAIN) != envelope.envelope_hash:
            blocked.append(_issue("envelope_hash_mismatch", "envelope_hash", "Envelope hash mismatch."))
    except (TypeError, ValueError) as exc:
        blocked.append(_issue("envelope_non_canonical", "envelope", str(exc)))
    if blocked:
        return StrategyEvidenceValidation(EvidenceAvailability.BLOCKED, tuple(blocked + unavailable))
    if unavailable:
        return StrategyEvidenceValidation(EvidenceAvailability.TYPED_UNAVAILABLE, tuple(unavailable))
    return StrategyEvidenceValidation(EvidenceAvailability.PRESENT)


def _issue(code: str, field: str, message: str) -> StrategyEvidenceIssue:
    return StrategyEvidenceIssue(code=code, field=field, message=message)


__all__ = [
    "COMPONENT_CATALOG",
    "ComponentCatalogStatus",
    "ComponentDescriptor",
    "EvidenceAvailability",
    "StrategyEvidenceEnvelope",
    "StrategyEvidenceIssue",
    "StrategyEvidenceValidation",
    "build_strategy_evidence_envelope",
    "canonical_hash",
    "canonical_json_bytes",
    "canonical_json_value",
    "component_catalog_status",
    "validate_strategy_evidence_envelope",
]
