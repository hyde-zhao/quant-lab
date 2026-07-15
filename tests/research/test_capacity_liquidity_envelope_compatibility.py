"""CR-169 S03：C4 component 与 CR-166 neutral envelope 兼容性。"""

from dataclasses import replace

from engine.capacity_liquidity_evidence import (
    CapacityLiquidityEvidenceInput,
    build_capacity_liquidity_evidence,
)
from engine.strategy_evidence import (
    ComponentCatalogStatus,
    ComponentDescriptor,
    EvidenceAvailability,
    build_strategy_evidence_envelope,
    component_catalog_status,
    validate_strategy_evidence_envelope,
)


def _input(**changes: object) -> CapacityLiquidityEvidenceInput:
    values: dict[str, object] = {
        "manifest_ref": "fixture://manifest/daily",
        "run_ref": "fixture://run/daily",
        "strategy_ref": "fixture://strategy/daily",
        "package_ref": "fixture://package/daily",
        "price_basis": "adjusted_close",
        "notional_basis": "market_value",
        "currency": "CNY",
        "calendar": "CN-TRADING-DAY",
        "as_of": "2026-07-10",
        "horizon_start": "2026-01-01",
        "horizon_end": "2026-06-30",
        "lineage_context_ref": "fixture://context/lineage/shared",
        "authorization_context_ref": "fixture://context/authorization/static-only",
        "synthetic_adv": "1000000",
        "requested_notional": "50000",
        "turnover_notional": "250000",
        "participation_cap": "0.10",
        "currency_minor_unit": "0.01",
        "method": "static_adv_cap_v1",
        "model_version": "fixture-static-adv-cap-v1",
        "lineage_refs": ("fixture://lineage/c4",),
        "provenance_refs": ("fixture://provenance/c4",),
        "authorization_refs": ("fixture://authorization/static-only",),
        "limitations": ("fixture_static_only",),
    }
    values.update(changes)
    return CapacityLiquidityEvidenceInput(**values)


def _envelope(result, subject_ref: str, package_ref: str):
    assert result.evidence is not None
    component = result.evidence
    return build_strategy_evidence_envelope(
        evidence_kind="strategy-production-evidence",
        subject_ref=subject_ref,
        components=(
            ComponentDescriptor(
                component_type="capacity_liquidity",
                component_schema_version="v1",
                required=True,
                component_ref=component.component_ref,
                component_hash=component.component_hash,
                availability=EvidenceAvailability.PRESENT,
            ),
        ),
        logical_provenance={"package_ref": package_ref, "component_ref": component.component_ref},
        authorization_summary={"mode": "fixture-static", "authorization_ref": "fixture://authorization/static-only"},
        limitations=("fixture_static_only", "no_real_adv", "not_capacity_ready"),
    )


def test_c4_v1_is_the_single_active_capacity_liquidity_descriptor() -> None:
    assert component_catalog_status("capacity_liquidity", "v1") is ComponentCatalogStatus.ACTIVE
    assert component_catalog_status("capacity_liquidity", "reserved") is ComponentCatalogStatus.RESERVED
    assert component_catalog_status("capacity_liquidity", "v2") is ComponentCatalogStatus.UNKNOWN


def test_required_c4_v1_unavailable_never_false_passes() -> None:
    envelope = build_strategy_evidence_envelope(
        evidence_kind="strategy-production-evidence",
        subject_ref="strategy://daily",
        components=(
            ComponentDescriptor(
                component_type="capacity_liquidity",
                component_schema_version="v1",
                required=True,
                availability=EvidenceAvailability.TYPED_UNAVAILABLE,
                reason_codes=("c4_static_liquidity_basis_missing",),
            ),
        ),
        logical_provenance={"package_ref": "fixture://package/daily"},
        authorization_summary={"mode": "fixture-static"},
        limitations=("c4_unavailable",),
    )

    validation = validate_strategy_evidence_envelope(envelope)
    assert validation.availability is EvidenceAvailability.TYPED_UNAVAILABLE
    assert "mandatory_component_unavailable" in [issue.code for issue in validation.issues]


def test_daily_ml_share_component_hash_but_not_envelope_identity() -> None:
    daily = build_capacity_liquidity_evidence(_input())
    ml = build_capacity_liquidity_evidence(
        _input(
            manifest_ref="fixture://manifest/ml",
            run_ref="fixture://run/ml",
            strategy_ref="fixture://strategy/ml",
            package_ref="fixture://package/ml",
        )
    )
    assert daily.evidence is not None and ml.evidence is not None
    assert daily.evidence.component_hash == ml.evidence.component_hash
    daily_envelope = _envelope(daily, "strategy://daily", "fixture://package/daily")
    ml_envelope = _envelope(ml, "strategy://ml", "fixture://package/ml")
    assert daily_envelope.envelope_hash != ml_envelope.envelope_hash
    assert validate_strategy_evidence_envelope(daily_envelope).availability is EvidenceAvailability.PRESENT
    assert validate_strategy_evidence_envelope(ml_envelope).availability is EvidenceAvailability.PRESENT


def test_attachment_tamper_with_stale_envelope_hash_is_blocked() -> None:
    result = build_capacity_liquidity_evidence(_input())
    envelope = _envelope(result, "strategy://daily", "fixture://package/daily")
    tampered = replace(envelope, subject_ref="strategy://tampered")

    validation = validate_strategy_evidence_envelope(tampered)
    assert validation.availability is EvidenceAvailability.BLOCKED
    assert "envelope_hash_mismatch" in [issue.code for issue in validation.issues]


def test_no_parallel_envelope_or_registry_api_is_added() -> None:
    import engine.strategy_evidence as strategy_evidence

    public_names = set(strategy_evidence.__all__)
    assert "build_capacity_envelope" not in public_names
    assert "capacity_registry" not in public_names
    assert "discover_capacity_components" not in public_names
