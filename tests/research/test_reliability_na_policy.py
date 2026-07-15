from __future__ import annotations

from dataclasses import asdict
import json

import pytest

from engine.reliability_na_policy import (
    NA_POLICY_BY_ID,
    NA_POLICY_SPECS,
    CompleteNaDisposition,
    HardeningDirection,
    NaEvidenceState,
    build_na_reason_id,
    classify_na_evidence,
)


def _boundary(policy_id: str, *, profile: str = "candidate-release") -> dict[str, object]:
    policy = NA_POLICY_BY_ID[policy_id]
    return {
        "reason": "fixture policy is explicitly unavailable",
        "owner": policy.owner,
        "scope": policy.policy_id,
        "release_profile": profile,
        "authorization_ref": "",
    }


def _decision(
    policy_id: str = "G2-P01",
    *,
    present: bool = False,
    applicable: bool = True,
    evidence: dict[str, object] | None = None,
    profile: str = "candidate-release",
):
    return classify_na_evidence(
        policy=NA_POLICY_BY_ID[policy_id],
        evidence_present=present,
        applicable=applicable,
        evidence=evidence or {},
        release_profile=profile,
    )


def test_inventory_exact_counts_and_unique_ids() -> None:
    assert len(NA_POLICY_SPECS) == 21
    assert len(NA_POLICY_BY_ID) == 21
    assert len({policy.policy_id for policy in NA_POLICY_SPECS}) == 21
    assert [
        sum(policy.gate_id.startswith(f"gate_{gate_number}_") for policy in NA_POLICY_SPECS)
        for gate_number in range(1, 6)
    ] == [6, 6, 1, 5, 3]
    assert all(
        policy.evidence_keys
        and policy.reason_keys
        and policy.applicability_id
        and policy.owner == policy.gate_id
        and policy.baseline_path_type
        for policy in NA_POLICY_SPECS
    )


def test_inventory_direction_and_disposition_counts() -> None:
    assert sum(
        policy.hardening_direction is HardeningDirection.STRICTER
        for policy in NA_POLICY_SPECS
    ) == 15
    assert sum(
        policy.hardening_direction is HardeningDirection.CONTROLLED_WIDENING
        for policy in NA_POLICY_SPECS
    ) == 5
    assert sum(
        policy.hardening_direction is HardeningDirection.PRESERVE
        for policy in NA_POLICY_SPECS
    ) == 1
    assert sum(
        policy.complete_na_disposition is CompleteNaDisposition.REVIEWABLE
        for policy in NA_POLICY_SPECS
    ) == 20
    assert NA_POLICY_BY_ID["G1-P06"].complete_na_disposition is CompleteNaDisposition.PROHIBITED


def test_five_states_and_precedence() -> None:
    assert _decision(present=True, evidence={"na_reason": "ignored"}).state is NaEvidenceState.PRESENT
    assert _decision().state is NaEvidenceState.MISSING
    assert _decision(evidence={"na_reason": "generic"}).state is NaEvidenceState.GENERIC_REASON_ESCAPE
    assert _decision(evidence={"n_a_boundaries": {"G2-P01": {"reason": "only"}}}).state is NaEvidenceState.NA_WITH_INCOMPLETE_BOUNDARY
    complete = _decision(evidence={"n_a_boundaries": {"G2-P01": _boundary("G2-P01")}})
    assert complete.state is NaEvidenceState.NA_WITH_COMPLETE_BOUNDARY
    assert complete.boundary_complete is True


@pytest.mark.parametrize("missing_field", ["reason", "owner", "scope", "release_profile"])
def test_boundary_requires_four_fields_or_opaque_authorization(missing_field: str) -> None:
    boundary = _boundary("G2-P01")
    boundary[missing_field] = ""
    result = _decision(evidence={"n_a_boundaries": {"G2-P01": boundary}})
    assert result.state is NaEvidenceState.NA_WITH_INCOMPLETE_BOUNDARY
    assert result.boundary_complete is False


def test_boundary_owner_scope_and_profile_must_match() -> None:
    for field, value in (
        ("owner", "gate_3_pit_universe"),
        ("scope", "G2-P02"),
        ("release_profile", "exploratory"),
    ):
        boundary = _boundary("G2-P01")
        boundary[field] = value
        result = _decision(evidence={"n_a_boundaries": {"G2-P01": boundary}})
        assert result.state is NaEvidenceState.NA_WITH_INCOMPLETE_BOUNDARY


def test_opaque_authorization_ref_can_replace_profile_match_without_being_parsed() -> None:
    boundary = _boundary("G2-P01", profile="exploratory")
    boundary["authorization_ref"] = "decision://CP2/opaque-only"
    result = _decision(evidence={"n_a_boundaries": {"G2-P01": boundary}})
    assert result.state is NaEvidenceState.NA_WITH_COMPLETE_BOUNDARY
    assert boundary["authorization_ref"] == "decision://CP2/opaque-only"


def test_policy_specific_boundary_precedes_generic_reason() -> None:
    result = _decision(
        evidence={
            "na_reason": "generic escape",
            "n_a_boundaries": {"G2-P01": _boundary("G2-P01")},
        }
    )
    assert result.state is NaEvidenceState.NA_WITH_COMPLETE_BOUNDARY


def test_policy_reason_key_is_generic_escape_without_structured_boundary() -> None:
    result = _decision(evidence={"split_policy_na_reason": "legacy text"})
    assert result.state is NaEvidenceState.GENERIC_REASON_ESCAPE
    assert result.reason_id == "gate2_g2_p01_generic_reason_escape"


def test_prohibited_complete_na_has_stable_not_permitted_reason() -> None:
    result = _decision(
        "G1-P06",
        evidence={"n_a_boundaries": {"G1-P06": _boundary("G1-P06")}},
    )
    assert result.state is NaEvidenceState.NA_WITH_COMPLETE_BOUNDARY
    assert result.reason_id == "gate1_g1_p06_complete_na_not_permitted"


def test_conditional_applicability_is_preserved_in_decision() -> None:
    result = _decision(
        "G2-P05",
        applicable=False,
        evidence={"n_a_boundaries": {"G2-P05": _boundary("G2-P05")}},
    )
    assert result.state is NaEvidenceState.NA_WITH_COMPLETE_BOUNDARY
    assert result.applicable is False


def test_reason_category_is_closed() -> None:
    with pytest.raises(ValueError, match="unsupported N/A reason category"):
        build_na_reason_id(NA_POLICY_BY_ID["G1-P01"], "invented")


def test_decision_is_deterministic_for_mapping_order_variants() -> None:
    policy = NA_POLICY_BY_ID["G4-P02"]
    boundary_items = list(_boundary("G4-P02").items())
    serialized: set[str] = set()
    for index in range(10):
        ordered_items = boundary_items[index % len(boundary_items) :] + boundary_items[: index % len(boundary_items)]
        evidence = {"n_a_boundaries": {"G4-P02": dict(ordered_items)}}
        result = classify_na_evidence(
            policy=policy,
            evidence_present=False,
            applicable=True,
            evidence=evidence,
            release_profile="candidate-release",
        )
        serialized.add(json.dumps(asdict(result), sort_keys=True, default=str))
    assert len(serialized) == 1


def test_private_module_is_not_reexported_from_engine_package() -> None:
    import engine

    assert not hasattr(engine, "NA_POLICY_SPECS")
