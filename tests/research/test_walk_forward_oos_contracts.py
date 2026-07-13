from __future__ import annotations

from dataclasses import replace

import pytest

from engine.strategy_evidence import (
    ComponentCatalogStatus,
    ComponentDescriptor,
    EvidenceAvailability,
    build_strategy_evidence_envelope,
    canonical_hash,
    canonical_json_bytes,
    component_catalog_status,
    validate_strategy_evidence_envelope,
)
from engine.walk_forward_oos_evidence import validate_walk_forward_oos_input
from tests.research.walk_forward_oos_test_support import evidence_input


def _descriptor(**changes) -> ComponentDescriptor:
    base = ComponentDescriptor(
        component_type="walk_forward_oos",
        component_schema_version="v1",
        required=True,
        component_ref="evidence://walk-forward/v1",
        component_hash="sha256:component",
        availability=EvidenceAvailability.PRESENT,
    )
    return replace(base, **changes)


def _envelope(*components: ComponentDescriptor):
    return build_strategy_evidence_envelope(
        evidence_kind="strategy-production-evidence",
        subject_ref="strategy://fixture",
        components=components,
        logical_provenance={"lineage_ref": "fixture://lineage"},
        authorization_summary={"validation_mode": "fixture-static"},
    )


def test_c2_input_exposes_all_seven_field_families() -> None:
    payload = evidence_input().to_dict()
    assert set(payload) >= {
        "manifest",
        "split_policy",
        "folds",
        "leakage_policy",
        "metric_policies",
        "fold_metrics",
        "lineage",
        "authorization",
    }
    assert validate_walk_forward_oos_input(evidence_input()).passed


def test_catalog_reserves_c3_c4_without_calculators() -> None:
    assert component_catalog_status("walk_forward_oos", "v1") is ComponentCatalogStatus.ACTIVE
    assert component_catalog_status("economic_cost", "reserved") is ComponentCatalogStatus.RESERVED
    assert component_catalog_status("capacity_liquidity", "reserved") is ComponentCatalogStatus.RESERVED
    assert component_catalog_status("future_unknown", "v9") is ComponentCatalogStatus.UNKNOWN


def test_unknown_mandatory_blocks_and_optional_is_preserve_only() -> None:
    mandatory = _envelope(
        _descriptor(component_type="future_unknown", component_schema_version="v9")
    )
    optional = _envelope(
        _descriptor(
            component_type="future_unknown",
            component_schema_version="v9",
            required=False,
            component_ref="",
            component_hash="",
            availability=EvidenceAvailability.TYPED_UNAVAILABLE,
        )
    )
    assert validate_strategy_evidence_envelope(mandatory).availability is EvidenceAvailability.BLOCKED
    assert validate_strategy_evidence_envelope(optional).availability is EvidenceAvailability.PRESENT


def test_envelope_order_hash_and_tamper_are_deterministic() -> None:
    first = _descriptor()
    second = _descriptor(component_type="economic_cost", component_schema_version="reserved", required=False, component_ref="", component_hash="", availability=EvidenceAvailability.TYPED_UNAVAILABLE)
    envelopes = [_envelope(*order) for order in ((first, second), (second, first)) for _ in range(5)]
    assert len({item.envelope_hash for item in envelopes}) == 1
    assert validate_strategy_evidence_envelope(envelopes[0]).passed
    assert validate_strategy_evidence_envelope(replace(envelopes[0], envelope_hash="sha256:tampered")).availability is EvidenceAvailability.BLOCKED


def test_neutral_canonical_rejects_unsupported_or_ambiguous_values() -> None:
    with pytest.raises(ValueError, match="non-finite"):
        canonical_json_bytes({"x": float("nan")})
    with pytest.raises(TypeError, match="unsupported"):
        canonical_json_bytes({"x": {1, 2}})
    with pytest.raises(TypeError, match="keys"):
        canonical_json_bytes({1: "x"})
    with pytest.raises(ValueError, match="domain"):
        canonical_hash({}, domain="")
