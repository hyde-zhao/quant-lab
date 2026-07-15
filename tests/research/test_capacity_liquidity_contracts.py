"""CR-169 S01：C4 typed contract、13 字段关联头与 fail-closed 校验。"""

from dataclasses import replace

import pytest

from engine.capacity_liquidity_evidence import (
    C4_REASON_CODES,
    CORRELATION_HEADER_FIELDS,
    CapacityLiquidityEvidenceInput,
    capacity_liquidity_semantic_hash,
    normalize_capacity_liquidity_input,
    prepare_capacity_liquidity_validation,
    validate_c3_c4_correlation_headers,
    validate_capacity_liquidity_semantic_hash,
)
from engine.strategy_evidence import EvidenceAvailability


def _valid_input(**changes: object) -> CapacityLiquidityEvidenceInput:
    base = CapacityLiquidityEvidenceInput(
        manifest_ref="fixture://manifest/daily",
        run_ref="fixture://run/daily",
        strategy_ref="fixture://strategy/daily",
        package_ref="fixture://package/daily",
        price_basis="adjusted_close",
        notional_basis="market_value",
        currency="CNY",
        calendar="CN-TRADING-DAY",
        as_of="2026-07-10",
        horizon_start="2026-01-01",
        horizon_end="2026-06-30",
        lineage_context_ref="fixture://context/lineage/daily",
        authorization_context_ref="fixture://context/authorization/static-only",
        synthetic_adv="1000000",
        requested_notional="100000",
        turnover_notional="250000",
        participation_cap="0.20",
        currency_minor_unit="0.01",
        method="static_adv_cap_v1",
        model_version="fixture-static-adv-cap-v1",
        lineage_refs=("fixture://lineage/c4",),
        provenance_refs=("fixture://provenance/c4",),
        authorization_refs=("fixture://authorization/static-only",),
        limitations=("fixture_static_only", "no_real_adv"),
        no_real_adv_claim=True,
        no_real_liquidity_claim=True,
        no_capacity_ready_claim=True,
    )
    return replace(base, **changes)


def _codes(value: CapacityLiquidityEvidenceInput) -> list[str]:
    return [issue.code for issue in prepare_capacity_liquidity_validation(value).issues]


def test_valid_contract_has_exact_header_and_no_issues() -> None:
    result = prepare_capacity_liquidity_validation(_valid_input())

    assert result.availability is EvidenceAvailability.PRESENT
    assert result.issues == ()
    assert tuple(result.header.to_dict()) == CORRELATION_HEADER_FIELDS
    assert len(result.header.to_dict()) == 13
    assert len(C4_REASON_CODES) == 12


@pytest.mark.parametrize(
    ("changes", "expected_code", "expected_availability"),
    [
        ({"strategy_ref": ""}, "c4_identity_binding_missing", EvidenceAvailability.TYPED_UNAVAILABLE),
        ({"synthetic_adv": None}, "c4_static_liquidity_basis_missing", EvidenceAvailability.TYPED_UNAVAILABLE),
        ({"model_version": ""}, "c4_proxy_model_version_missing", EvidenceAvailability.TYPED_UNAVAILABLE),
        ({"requested_notional": float("nan")}, "c4_nonfinite_numeric_invalid", EvidenceAvailability.BLOCKED),
        ({"participation_cap": "1.1"}, "c4_negative_or_participation_cap_invalid", EvidenceAvailability.BLOCKED),
        ({"liquidity_currency": "USD"}, "c4_unit_currency_basis_mismatch", EvidenceAvailability.BLOCKED),
        ({"horizon_end": "2026-07-11"}, "c4_calendar_temporal_mismatch", EvidenceAvailability.BLOCKED),
        ({"authorization_refs": ()}, "c4_lineage_provenance_authorization_missing_or_mismatch", EvidenceAvailability.TYPED_UNAVAILABLE),
        ({"claimed_semantic_hash": "sha256:tampered"}, "c4_component_or_envelope_hash_tampered", EvidenceAvailability.BLOCKED),
        ({"no_real_adv_claim": False}, "c4_lineage_provenance_authorization_missing_or_mismatch", EvidenceAvailability.BLOCKED),
    ],
)
def test_input_fail_closed_matrix(
    changes: dict[str, object], expected_code: str, expected_availability: EvidenceAvailability
) -> None:
    result = prepare_capacity_liquidity_validation(_valid_input(**changes))

    assert expected_code in [issue.code for issue in result.issues]
    assert result.availability is expected_availability


@pytest.mark.parametrize("field_name", CORRELATION_HEADER_FIELDS)
def test_each_header_field_mismatch_is_blocked(field_name: str) -> None:
    left = prepare_capacity_liquidity_validation(_valid_input()).header
    right = replace(left, **{field_name: f"fixture://mismatch/{field_name}"})

    validation = validate_c3_c4_correlation_headers(left, right)

    assert validation.availability is EvidenceAvailability.BLOCKED
    assert "c4_c3_c4_correlation_header_mismatch" in [issue.code for issue in validation.issues]


def test_semantic_hash_excludes_attachment_identity_and_is_deterministic() -> None:
    daily, _, _ = normalize_capacity_liquidity_input(_valid_input())
    ml, _, _ = normalize_capacity_liquidity_input(
        _valid_input(
            manifest_ref="fixture://manifest/ml",
            run_ref="fixture://run/ml",
            strategy_ref="fixture://strategy/ml",
            package_ref="fixture://package/ml",
        )
    )

    hashes = {capacity_liquidity_semantic_hash(daily) for _ in range(10)}
    assert hashes == {capacity_liquidity_semantic_hash(ml)}
    assert len(hashes) == 1
    for identity_field in ("manifest_ref", "run_ref", "strategy_ref", "package_ref"):
        assert identity_field not in daily.semantic_projection()


def test_explicit_semantic_hash_tamper_is_blocked() -> None:
    normalized, _, _ = normalize_capacity_liquidity_input(_valid_input())
    valid_hash = capacity_liquidity_semantic_hash(normalized)

    assert validate_capacity_liquidity_semantic_hash(normalized, valid_hash).passed
    tampered = validate_capacity_liquidity_semantic_hash(normalized, "sha256:tampered")
    assert tampered.availability is EvidenceAvailability.BLOCKED
    assert [issue.code for issue in tampered.issues] == ["c4_component_or_envelope_hash_tampered"]


def test_refs_remain_opaque_and_alpha_decay_is_absent() -> None:
    result = prepare_capacity_liquidity_validation(
        _valid_input(
            lineage_refs=("https://example.invalid/lineage",),
            provenance_refs=("file:///unreadable/provenance",),
            authorization_refs=("opaque://authorization/static",),
        )
    )

    assert result.availability is EvidenceAvailability.PRESENT
    assert _codes(_valid_input()) == []
    assert all("alpha" not in field_name for field_name in result.normalized_input.__dataclass_fields__)
