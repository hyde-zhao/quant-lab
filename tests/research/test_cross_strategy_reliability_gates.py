from __future__ import annotations

from pathlib import Path

from engine.experiment_family_lineage import (
    ExperimentFamilyManifest,
    FamilyLineageValidationResult,
    LineageAvailability,
    ValidationStatus,
)
from engine.cross_strategy_reliability_gates import (
    IMPACT_MODEL_FAMILIES,
    STATISTICAL_ARTIFACT_SLOTS,
    ArtifactRef,
    ReliabilityGateStatus,
    build_shared_gate_summary,
    evaluate_gate1_statistical_reliability,
    fixture_cases_shared_contract,
    normalize_forbidden_operation_counts,
    resolve_admission_policy,
    validate_gate2_cv_governance,
    validate_gate3_pit_universe,
    validate_gate4_capacity_impact,
    validate_gate5_slots,
)
from engine.strategy_admission_statistical_gate import ValidationBoundFamilyEvidence


def _gate1_artifacts(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "multiple_testing_correction_refs": ["fixture://cr154/gate1/multiple-testing"],
        "fdr_bh_refs": ["fixture://cr154/gate1/fdr-bh"],
        "white_reality_check_or_hansen_spa_refs": ["fixture://cr154/gate1/wrc-spa"],
        "pbo_or_cscv_refs": ["fixture://cr154/gate1/pbo"],
        "dsr_or_sharpe_ic_deflation_refs": ["fixture://cr154/gate1/dsr"],
        "trial_count_and_effective_trials": {
            "raw_trial_count": 25,
            "effective_trial_count": 8.0,
            "provenance_ref": "fixture://cr154/gate1/trials",
        },
        "oos_split_refs": ["fixture://cr154/gate1/oos"],
        "purge_embargo_refs": ["fixture://cr154/gate1/purge-embargo"],
        "survivorship_audit_refs": ["fixture://cr154/gate1/survivorship"],
        "impact_capacity_refs": ["fixture://cr154/gate1/impact-capacity"],
        "blocked_claims": [],
        "release_blocking_reason": None,
    }
    base.update(overrides)
    return base


def _trusted_family_lineage() -> ValidationBoundFamilyEvidence:
    manifest = ExperimentFamilyManifest(
        schema_version=1,
        family_id="cr154-reliability-family",
        manifest_version=1,
        spec_ref="fixture://cr154/lineage/spec",
        events_ref="fixture://cr154/lineage/events",
        sealed_event_count=25,
        sealed_last_sequence=25,
        raw_trial_count=25,
        trial_ids=tuple(f"trial-{index:02d}" for index in range(25)),
        seal_hash="sha256:cr154-trusted-lineage",
        sealed_at="2026-07-11T00:00:00Z",
    )
    validation = FamilyLineageValidationResult(
        schema_version=1,
        validation_id="validation-cr154-trusted-lineage",
        target_ref="fixture://cr154/lineage/manifest-v1",
        target_hash=manifest.seal_hash,
        availability=LineageAvailability.PRESENT,
        validation_status=ValidationStatus.PASS,
        recomputed_raw_trial_count=manifest.raw_trial_count,
        declared_raw_trial_count=manifest.raw_trial_count,
    )
    return ValidationBoundFamilyEvidence(manifest, validation)


def test_cr154_s01_shared_contract_fixture_cases_are_stable_and_forbidden_counters_block() -> None:
    cases = fixture_cases_shared_contract()
    by_id = {case["case_id"]: case for case in cases}

    assert by_id["shared_minimal_pass"]["summary"]["status"] == "PASS"
    assert by_id["shared_minimal_pass"]["summary"]["schema_version"] == "cross_strategy_reliability_gates_v1"
    assert by_id["shared_forbidden_operation_blocked"]["summary"]["status"] == "BLOCKED"
    assert by_id["shared_forbidden_operation_blocked"]["summary"]["release_blocking_reason"]["reason_id"] == "forbidden_operation_detected"

    counts = normalize_forbidden_operation_counts({"credential_read": "bad", "custom_real_runtime_counter": 2})
    assert counts["credential_read"] == 1
    assert counts["custom_real_runtime_counter"] == 2


def test_cr154_s02_gate1_requires_explicit_statistical_artifacts_and_propagates_gate3_gate4() -> None:
    assert len(STATISTICAL_ARTIFACT_SLOTS) == 12

    gate = evaluate_gate1_statistical_reliability(
        _gate1_artifacts(),
        release_profile="candidate-release",
        claim_types=("statistical_significance", "sharpe"),
        family_lineage_projection=_trusted_family_lineage(),
    )
    assert gate.status is ReliabilityGateStatus.BLOCKED
    assert gate.family_lineage_projection["availability"] == "present"
    assert {claim.claim_id for claim in gate.blocked_claims} == {
        "trial_count_policy",
        "effective_trial_count_unavailable",
    }

    missing_lineage = evaluate_gate1_statistical_reliability(
        _gate1_artifacts(),
        release_profile="candidate-release",
        claim_types=("statistical_significance", "sharpe"),
    )
    assert missing_lineage.status is ReliabilityGateStatus.BLOCKED
    assert missing_lineage.family_lineage_projection["availability"] == "typed_unavailable"

    blocked = evaluate_gate1_statistical_reliability(
        _gate1_artifacts(white_reality_check_or_hansen_spa_refs=[], trial_count_and_effective_trials={"raw_trial_count": 0}),
        release_profile="candidate-release",
        claim_types=("statistical_significance",),
    )
    payload = blocked.to_dict()
    assert payload["status"] == "BLOCKED"
    assert payload["release_blocking_reason"]["reason_id"] == "effective_trial_count_unavailable"
    assert {"statistical_significance", "trial_count_policy"} <= {claim["claim_id"] for claim in payload["blocked_claims"]}

    missing_multiple_and_fdr = evaluate_gate1_statistical_reliability(
        _gate1_artifacts(
            multiple_testing_correction_refs=[],
            fdr_bh_refs=[],
            trial_count_and_effective_trials={
                "raw_trial_count": 3,
                "effective_trial_count": 9.0,
                "provenance_ref": "fixture://cr154/gate1/trials",
            },
        ),
        release_profile="candidate-release",
        claim_types=("statistical_significance",),
    )
    missing_payload = missing_multiple_and_fdr.to_dict()
    assert missing_payload["status"] == "BLOCKED"
    assert {"multiple_testing_correction", "fdr_bh_correction", "trial_count_policy"} <= {
        claim["claim_id"] for claim in missing_payload["blocked_claims"]
    }

    approximated_trials = evaluate_gate1_statistical_reliability(
        _gate1_artifacts(
            trial_count_and_effective_trials={
                "raw_trial_count": 3,
                "effective_trial_count": 9.0,
                "provenance_ref": "fixture://cr154/gate1/trials",
                "approximation_reason": "fixture approximation groups correlated trials conservatively",
            },
        ),
        release_profile="candidate-release",
        claim_types=("statistical_significance",),
    )
    approximated_payload = approximated_trials.to_dict()
    assert approximated_payload["status"] == "BLOCKED"
    assert "trial_count_approximation_review" in {
        claim["claim_id"] for claim in approximated_payload["blocked_claims"]
    }

    gate3 = build_shared_gate_summary(
        gate_id="gate_3_pit_universe",
        artifact_refs=(ArtifactRef("pit_universe_refs", "fixture://blocked", owner_gate="gate_3_pit_universe", status="BLOCKED"),),
    )
    propagated = evaluate_gate1_statistical_reliability(_gate1_artifacts(), gate3_summary=gate3, release_profile="release-readiness")
    assert propagated.to_dict()["status"] == "BLOCKED"
    assert "survivorship_free" in {claim["claim_id"] for claim in propagated.to_dict()["blocked_claims"]}


def test_cr154_s03_s04_s05_s06_gate_contracts_are_fixture_only_and_fail_closed() -> None:
    cv_missing_oos = validate_gate2_cv_governance(
        {"purge_embargo_refs": ["fixture://cv/purge"]},
        strategy_class="ml",
        release_profile="candidate-release",
    )
    assert cv_missing_oos.to_dict()["status"] == "BLOCKED"
    assert {"split_policy_missing", "walk_forward_missing", "oos_split_missing", "overlap_applicability_unknown"} <= {
        claim["claim_id"] for claim in cv_missing_oos.to_dict()["blocked_claims"]
    }

    cv = validate_gate2_cv_governance(
        {
            "split_policy_ref": "fixture://cv/split-policy",
            "walk_forward_refs": ["fixture://cv/wf"],
            "oos_split_refs": ["fixture://cv/oos"],
            "overlap_applicability": "overlapping-label-window",
            "overlapping_labels_or_windows": True,
        },
        strategy_class="ml",
        release_profile="candidate-release",
    )
    assert cv.to_dict()["status"] == "BLOCKED"
    assert "leakage_safe_cv" in {claim["claim_id"] for claim in cv.to_dict()["blocked_claims"]}

    pit = validate_gate3_pit_universe({"pit_universe_refs": ["fixture://pit"], "cr153_slot_lifecycle": "delegated_to_cr154"})
    assert pit.to_dict()["status"] == "PASS"

    assert set(IMPACT_MODEL_FAMILIES) == {"square_root", "almgren_chriss", "gatheral", "custom", "n/a-with-reason"}
    impact = validate_gate4_capacity_impact(
        {
            "impact_model_family": "almgren_chriss",
            "impact_model_ref": "fixture://impact/almgren",
            "adv_participation_ref": "fixture://impact/adv",
            "capacity_dollars_ref": "fixture://impact/capacity",
            "liquidity_sizing_refs": ["fixture://impact/liquidity"],
            "cost_underestimation_status": "PASS",
            "no_real_tca_claim": True,
        }
    )
    assert impact.to_dict()["status"] == "PASS"

    missing_impact = validate_gate4_capacity_impact(
        {"impact_model_family": "almgren_chriss", "no_real_tca_claim": True},
        release_profile="candidate-release",
    )
    missing_impact_payload = missing_impact.to_dict()
    assert missing_impact_payload["status"] == "BLOCKED"
    assert {"impact_model_ref_missing", "adv_participation_missing", "capacity_dollars_missing", "liquidity_sizing_missing", "cost_underestimation_status_missing"} <= {
        claim["claim_id"] for claim in missing_impact_payload["blocked_claims"]
    }

    overclaim = validate_gate4_capacity_impact(
        {"impact_model_family": "free_text", "no_real_tca_claim": False, "real_tca_claim": True},
        release_profile="release-readiness",
    )
    assert overclaim.to_dict()["status"] == "BLOCKED"
    assert {"impact_model_family_invalid", "no_real_tca_claim_missing", "real_tca_not_authorized"} <= {
        claim["claim_id"] for claim in overclaim.to_dict()["blocked_claims"]
    }

    gate5 = validate_gate5_slots(
        {
            "regime_slots": [
                {
                    "slot_id": "regime-static-policy",
                    "slot_type": "regime",
                    "status": "PASS",
                    "refs": ["fixture://gate5/regime"],
                    "limitations": ["local_static_only"],
                    "owner": "CR-154",
                    "claim_limit": "not production regime detection",
                    "last_review_ref": "fixture://gate5/review",
                }
            ],
            "attribution_slots": [
                {
                    "slot_id": "attribution-static-policy",
                    "slot_type": "attribution",
                    "status": "PASS",
                    "refs": ["fixture://gate5/attrib"],
                    "limitations": ["local_static_only"],
                    "owner": "CR-154",
                    "claim_limit": "not broker PnL attribution",
                    "last_review_ref": "fixture://gate5/review",
                }
            ],
            "reconciliation_slots": [
                {
                    "slot_id": "reconciliation-static-policy",
                    "slot_type": "reconciliation",
                    "status": "PASS",
                    "refs": ["fixture://gate5/recon"],
                    "limitations": ["local_static_only"],
                    "owner": "CR-154",
                    "claim_limit": "not runtime reconciliation",
                    "last_review_ref": "fixture://gate5/review",
                }
            ],
            "no_runtime_reconciliation_claim": True,
        }
    )
    assert gate5.to_dict()["status"] == "PASS"

    gate5_strings = validate_gate5_slots(
        {
            "regime_slots": ["fixture://gate5/regime"],
            "attribution_slots": ["fixture://gate5/attrib"],
            "reconciliation_slots": ["fixture://gate5/recon"],
            "no_runtime_reconciliation_claim": True,
        }
    )
    assert gate5_strings.to_dict()["status"] == "BLOCKED"
    assert {"regime_slot_shape_invalid", "attribution_slot_shape_invalid", "reconciliation_slot_shape_invalid"} <= {
        claim["claim_id"] for claim in gate5_strings.to_dict()["blocked_claims"]
    }

    real_recon = validate_gate5_slots({"real_reconciliation_claim": True}, release_profile="release-readiness")
    assert real_recon.to_dict()["status"] == "BLOCKED"
    assert {"real_reconciliation_not_authorized", "no_runtime_reconciliation_claim_missing"} <= {
        claim["claim_id"] for claim in real_recon.to_dict()["blocked_claims"]
    }


def test_cr154_s07_admission_policy_tiers_fail_closed_and_never_authorize_runtime() -> None:
    gate_ids = (
        "gate_1_statistical",
        "gate_2_cv",
        "gate_3_pit_universe",
        "gate_4_capacity_impact",
        "gate_5_regime_attribution_reconciliation",
    )
    gates = [
        build_shared_gate_summary(
            gate_id=gate_id,
            artifact_refs=(ArtifactRef("contract_ref", f"fixture://{gate_id}", owner_gate=gate_id),),
        )
        for gate_id in gate_ids
    ]

    result = resolve_admission_policy(strategy_class="ml", release_profile="release-readiness", gate_summaries=gates)
    payload = result.to_dict()
    assert payload["tier"] == "T2"
    assert payload["gate_mode"] == "release-blocking"
    assert payload["status"] == "PASS"
    assert "not paper/live/trading/broker/runtime readiness" in payload["release_wording"]

    unknown = resolve_admission_policy(strategy_class="ml", release_profile="mystery", gate_summaries=gates)
    assert unknown.to_dict()["status"] == "BLOCKED"
    assert unknown.to_dict()["release_blocking_reason"]["reason_id"] == "unknown_release_profile_fail_closed"

    duplicate_gates = [
        build_shared_gate_summary(
            gate_id="gate_1_statistical",
            artifact_refs=(ArtifactRef("contract_ref", f"fixture://duplicate/{idx}", owner_gate="gate_1_statistical"),),
        )
        for idx in range(5)
    ]
    t2_duplicate = resolve_admission_policy(strategy_class="ml", release_profile="release-readiness", gate_summaries=duplicate_gates)
    assert t2_duplicate.to_dict()["status"] == "BLOCKED"
    assert t2_duplicate.to_dict()["release_blocking_reason"]["reason_id"] == "mandatory_gate_evidence_missing"

    t1_missing = resolve_admission_policy(strategy_class="ml", release_profile="candidate-release", gate_summaries=[])
    assert t1_missing.to_dict()["status"] == "BLOCKED"
    assert t1_missing.to_dict()["release_blocking_reason"]["reason_id"] == "default_required_gate_evidence_missing"

    failed_gate = build_shared_gate_summary(
        gate_id="gate_2_cv",
        artifact_refs=(ArtifactRef("contract_ref", "fixture://failed", owner_gate="gate_2_cv", status="FAIL"),),
    )
    t1_failed = resolve_admission_policy(
        strategy_class="ml",
        release_profile="candidate-release",
        gate_summaries=(gates[0], failed_gate, gates[2], gates[3], gates[4]),
    )
    assert t1_failed.to_dict()["status"] == "BLOCKED"
    assert t1_failed.to_dict()["release_blocking_reason"]["reason_id"] == "default_required_gate_blocked"

    t3 = resolve_admission_policy(strategy_class="event-driven", release_profile="live", gate_summaries=gates)
    assert t3.to_dict()["gate_mode"] == "not-authorized"
    assert t3.to_dict()["release_blocking_reason"]["reason_id"] == "runtime_profile_not_authorized"

    runtime_alias = resolve_admission_policy(
        strategy_class="ml",
        release_profile="exploratory",
        gate_summaries=gates,
        requested_claims=("broker-readiness",),
    )
    assert runtime_alias.to_dict()["status"] == "BLOCKED"
    assert runtime_alias.to_dict()["release_blocking_reason"]["reason_id"] == "runtime_readiness_claim_not_authorized"


def test_cr154_module_has_no_runtime_or_broker_imports_or_enablement_strings() -> None:
    source = Path("engine/cross_strategy_reliability_gates.py").read_text(encoding="utf-8")
    lowered = source.lower()

    assert "import xtquant" not in lowered
    assert "from xtquant" not in lowered
    assert "subprocess" not in lowered
    assert "os.system" not in lowered
    assert "popen" not in lowered
    assert "requests." not in lowered
    assert "urllib" not in lowered
    assert "git clone" not in lowered
    assert "pip install" not in lowered
    assert "paper-ready" not in lowered
    assert "simulation-ready" not in lowered
    assert "live-ready" not in lowered
    assert "trading-ready" not in lowered
    assert "broker-ready" not in lowered
    assert "runtime-ready" not in lowered
