from __future__ import annotations

from dataclasses import fields, replace
from datetime import datetime, timedelta, timezone

import pytest

import engine.path_i_governance as governance
from engine.path_i_governance import (
    ActionAuthorizationRecordV1,
    ActionAuthorizationRequestV1,
    ActionDecisionV1,
    ActionDecisionOriginV1,
    ActionPrerequisiteEvidenceV1,
    ActionPrerequisiteProvenanceV1,
    ActionReasonCodeV1,
    ActionScopeContextV1,
    ActionTargetKindV1,
    EmpiricalRInputsV1,
    EmpiricalRStateV1,
    LEGACY_RUN_LOGICAL_ROOT_TEMPLATE,
    NEW_RUN_LOGICAL_ROOT_TEMPLATE,
    PathIActionKind,
    PathIClaimCeilingV1,
    PathIEligibilityError,
    PathIGovernanceError,
    RunPathIntentV1,
    RunPathModeV1,
    SignalBatchBoundaryV1,
    SignatureKeySlotV1,
    ValidityWindowSlotV1,
    classify_empirical_r,
    decide_run_path,
    enforce_path_i_claim_ceiling,
    evaluate_action_decision,
    require_action_eligible,
    validate_signal_batch_boundary,
)


NOW = datetime(2026, 7, 18, 6, 0, tzinfo=timezone.utc)
HASH_A = "sha256:" + "a" * 64
HASH_B = "sha256:" + "b" * 64
FIXTURE_ROOT = "fixture://repository/cr172"
FIXTURE_TARGET = f"{FIXTURE_ROOT}/target"


def make_context(
    *,
    target_kind: ActionTargetKindV1 = ActionTargetKindV1.REPOSITORY_FIXTURE,
    run_id: str = "run-fixture-001",
) -> ActionScopeContextV1:
    return ActionScopeContextV1(
        schema_version=governance.GOVERNANCE_SCHEMA_VERSION,
        scope_revision="scope-v1",
        scope_sha256=HASH_A,
        release_id="release-fixture-001",
        run_id=run_id,
        family_id="family-fixture-001",
        target_kind=target_kind,
    )


def make_request(
    action_kind: PathIActionKind,
    *,
    context: ActionScopeContextV1 | None = None,
    logical_path: str = FIXTURE_TARGET,
) -> ActionAuthorizationRequestV1:
    return ActionAuthorizationRequestV1(
        action_kind=action_kind,
        logical_path=logical_path,
        context=context or make_context(),
    )


def make_record(
    action_kind: PathIActionKind,
    *,
    allowed: tuple[str, ...] = (FIXTURE_ROOT,),
    denied: tuple[str, ...] = (),
    valid_from: datetime = NOW - timedelta(hours=1),
    expires_at: datetime = NOW + timedelta(hours=1),
    revoked_at: datetime | None = None,
) -> ActionAuthorizationRecordV1:
    return ActionAuthorizationRecordV1(
        authorization_id=f"auth-{action_kind.value}",
        action_kind=action_kind,
        owner="repository-fixture-owner",
        scope_revision="scope-v1",
        scope_sha256=HASH_A,
        allowed_logical_paths=allowed,
        denied_logical_paths=denied,
        valid_from=valid_from,
        expires_at=expires_at,
        revoked_at=revoked_at,
        approval_ref=f"approval:{action_kind.value}",
        evidence_ref=f"fixture:{action_kind.value}",
    )


def make_predecessor(
    action_kind: PathIActionKind,
    *,
    context: ActionScopeContextV1 | None = None,
    authorized: bool = True,
    eligible: bool = True,
) -> ActionPrerequisiteEvidenceV1:
    predecessor = governance.DIRECT_PREREQUISITE[action_kind]
    assert predecessor is not None
    provenance = {
        PathIActionKind.MULTI_TRIAL_RUNTIME_AND_WORKSPACE_WRITE: (
            ActionPrerequisiteProvenanceV1.ELIGIBILITY_DECISION
        ),
        PathIActionKind.TRIAL_RETURN_GENERATION: (
            ActionPrerequisiteProvenanceV1.ELIGIBILITY_DECISION
        ),
        PathIActionKind.EMPIRICAL_R_COMPUTATION: (
            ActionPrerequisiteProvenanceV1.SEALED_TRIAL_RETURN
        ),
        PathIActionKind.NAS_REPLICA_SYNC: (
            ActionPrerequisiteProvenanceV1.SEALED_TRIAL_RETURN
        ),
        PathIActionKind.EXECUTION_PULL_VERIFY_MATERIALIZE: (
            ActionPrerequisiteProvenanceV1.VERIFIED_REPLICA_RECEIPT
        ),
    }[action_kind]
    has_artifact = provenance is not ActionPrerequisiteProvenanceV1.ELIGIBILITY_DECISION
    return ActionPrerequisiteEvidenceV1(
        predecessor_action_kind=predecessor,
        authorization_id=f"auth-{predecessor.value}",
        authorized=authorized,
        eligible_to_execute=eligible,
        context=context or make_context(),
        provenance_kind=provenance,
        logical_uri=f"{FIXTURE_ROOT}/predecessor",
        content_sha256=HASH_A if has_artifact else "",
        manifest_sha256=HASH_B if has_artifact else "",
        evidence_ref=f"fixture:{predecessor.value}",
    )


def evaluate_fixture(action_kind: PathIActionKind):
    evidence = ()
    if governance.DIRECT_PREREQUISITE[action_kind] is not None:
        evidence = (make_predecessor(action_kind),)
    return evaluate_action_decision(
        make_request(action_kind),
        make_record(action_kind),
        evidence,
        decision_origin=ActionDecisionOriginV1.REPOSITORY_FIXTURE,
        evaluated_at=NOW,
    )


def test_action_kind_and_dag_are_exact() -> None:
    assert {item.value for item in PathIActionKind} == {
        "data_lake_read",
        "multi_trial_runtime_and_workspace_write",
        "trial_return_generation",
        "empirical_R_computation",
        "nas_replica_sync",
        "execution_pull_verify_materialize",
    }
    assert set(governance.DIRECT_PREREQUISITE) == set(PathIActionKind)
    assert set(governance.ACTION_ENFORCEMENT_POINTS) == set(PathIActionKind)
    assert len(set(governance.ACTION_ENFORCEMENT_POINTS.values())) == 6
    assert sum(value is not None for value in governance.DIRECT_PREREQUISITE.values()) == 5
    assert sum(value is None for value in governance.DIRECT_PREREQUISITE.values()) == 1


def test_approval_record_remains_exactly_twelve_fields() -> None:
    actual = {field.name for field in fields(ActionAuthorizationRecordV1)}
    assert actual == {
        "authorization_id",
        "action_kind",
        "owner",
        "scope_revision",
        "scope_sha256",
        "allowed_logical_paths",
        "denied_logical_paths",
        "valid_from",
        "expires_at",
        "revoked_at",
        "approval_ref",
        "evidence_ref",
    }
    assert len(actual) == 12


def test_origin_and_target_enums_are_exact_and_retained() -> None:
    assert {item.value for item in ActionDecisionOriginV1} == {
        "repository_fixture",
        "approved_ledger",
    }
    assert {item.value for item in ActionTargetKindV1} == {
        "repository_fixture",
        "real_operation",
    }
    decision = evaluate_fixture(PathIActionKind.DATA_LAKE_READ)
    assert decision.decision_origin is ActionDecisionOriginV1.REPOSITORY_FIXTURE
    assert decision.target_kind is ActionTargetKindV1.REPOSITORY_FIXTURE
    with pytest.raises(PathIGovernanceError):
        ActionScopeContextV1(
            schema_version=governance.GOVERNANCE_SCHEMA_VERSION,
            scope_revision="scope-v1",
            scope_sha256=HASH_A,
            release_id="release-1",
            run_id="run-1",
            family_id="family-1",
            target_kind="unknown",
        )


def test_each_action_uses_only_its_own_record() -> None:
    decisions = [evaluate_fixture(action_kind) for action_kind in PathIActionKind]
    assert len(decisions) == 6
    assert all(decision.authorized for decision in decisions)
    assert all(decision.eligible_to_execute for decision in decisions)
    wrong_record = make_record(PathIActionKind.DATA_LAKE_READ)
    request = make_request(PathIActionKind.TRIAL_RETURN_GENERATION)
    decision = evaluate_action_decision(
        request,
        wrong_record,
        (make_predecessor(PathIActionKind.TRIAL_RETURN_GENERATION),),
        decision_origin=ActionDecisionOriginV1.REPOSITORY_FIXTURE,
        evaluated_at=NOW,
    )
    assert not decision.authorized
    assert not decision.eligible_to_execute
    assert decision.reason_codes == (ActionReasonCodeV1.ACTION_MISMATCH,)


def test_approved_ledger_is_unconditionally_unavailable_for_all_actions() -> None:
    real_context = make_context(target_kind=ActionTargetKindV1.REAL_OPERATION)
    for action_kind in PathIActionKind:
        request = make_request(
            action_kind,
            context=real_context,
            logical_path=f"research://approved/release/{action_kind.value}",
        )
        real_record = replace(
            make_record(action_kind),
            allowed_logical_paths=("research://approved/release",),
        )
        decision = evaluate_action_decision(
            request,
            real_record,
            (),
            decision_origin=ActionDecisionOriginV1.APPROVED_LEDGER,
            evaluated_at=NOW,
        )
        assert not decision.authorized
        assert not decision.eligible_to_execute
        assert decision.reason_codes == (
            ActionReasonCodeV1.APPROVED_LEDGER_ADAPTER_UNAVAILABLE,
        )
        with pytest.raises(PathIEligibilityError):
            require_action_eligible(
                decision,
                expected_kind=action_kind,
                expected_context=real_context,
                expected_origin=ActionDecisionOriginV1.APPROVED_LEDGER,
            )


def test_fixture_decision_rejects_real_target_before_first_side_effect() -> None:
    real_context = make_context(target_kind=ActionTargetKindV1.REAL_OPERATION)
    decision = evaluate_action_decision(
        make_request(PathIActionKind.DATA_LAKE_READ, context=real_context),
        make_record(PathIActionKind.DATA_LAKE_READ),
        decision_origin=ActionDecisionOriginV1.REPOSITORY_FIXTURE,
        evaluated_at=NOW,
    )
    side_effects: list[str] = []
    with pytest.raises(PathIEligibilityError):
        require_action_eligible(
            decision,
            expected_kind=PathIActionKind.DATA_LAKE_READ,
            expected_context=real_context,
            expected_origin=ActionDecisionOriginV1.REPOSITORY_FIXTURE,
        )
        side_effects.append("forbidden")
    assert not decision.authorized
    assert not decision.eligible_to_execute
    assert decision.reason_codes == (ActionReasonCodeV1.ORIGIN_TARGET_MISMATCH,)
    assert side_effects == []


def test_repository_fixture_requires_fixture_uri_and_owned_authority() -> None:
    for logical_path in (
        "research://repository/cr172/target",
        "fixture://external/cr172/target",
        "fixture://repository:9000/cr172/target",
        "fixture://repository/cr172/%2A",
        "fixture://repository/cr172/%2E%2E/target",
    ):
        decision = evaluate_action_decision(
            make_request(PathIActionKind.DATA_LAKE_READ, logical_path=logical_path),
            make_record(PathIActionKind.DATA_LAKE_READ),
            decision_origin=ActionDecisionOriginV1.REPOSITORY_FIXTURE,
            evaluated_at=NOW,
        )
        assert not decision.authorized
        assert not decision.eligible_to_execute
        assert decision.reason_codes == (ActionReasonCodeV1.FIXTURE_URI_REQUIRED,)


@pytest.mark.parametrize(
    ("authorized", "eligible", "expected_reason"),
    [
        (False, False, ActionReasonCodeV1.PREDECESSOR_DENIED),
        (True, False, ActionReasonCodeV1.PREDECESSOR_INELIGIBLE),
    ],
)
def test_runtime_record_without_eligible_read_is_ineligible(
    authorized: bool,
    eligible: bool,
    expected_reason: ActionReasonCodeV1,
) -> None:
    action_kind = PathIActionKind.MULTI_TRIAL_RUNTIME_AND_WORKSPACE_WRITE
    predecessor = make_predecessor(
        action_kind,
        authorized=authorized,
        eligible=eligible,
    )
    decision = evaluate_action_decision(
        make_request(action_kind),
        make_record(action_kind),
        (predecessor,),
        decision_origin=ActionDecisionOriginV1.REPOSITORY_FIXTURE,
        evaluated_at=NOW,
    )
    launched: list[str] = []
    with pytest.raises(PathIEligibilityError):
        require_action_eligible(
            decision,
            expected_kind=action_kind,
            expected_context=make_context(),
            expected_origin=ActionDecisionOriginV1.REPOSITORY_FIXTURE,
        )
        launched.extend(("runner", "workspace", "pointer"))
    assert decision.authorized
    assert not decision.eligible_to_execute
    assert decision.reason_codes == (expected_reason,)
    assert launched == []


def test_runtime_record_without_read_evidence_is_ineligible() -> None:
    action_kind = PathIActionKind.MULTI_TRIAL_RUNTIME_AND_WORKSPACE_WRITE
    decision = evaluate_action_decision(
        make_request(action_kind),
        make_record(action_kind),
        (),
        decision_origin=ActionDecisionOriginV1.REPOSITORY_FIXTURE,
        evaluated_at=NOW,
    )
    assert decision.authorized
    assert not decision.eligible_to_execute
    assert decision.reason_codes == (ActionReasonCodeV1.PREDECESSOR_MISSING,)


@pytest.mark.parametrize(
    "action_kind",
    [
        PathIActionKind.MULTI_TRIAL_RUNTIME_AND_WORKSPACE_WRITE,
        PathIActionKind.TRIAL_RETURN_GENERATION,
        PathIActionKind.EMPIRICAL_R_COMPUTATION,
        PathIActionKind.NAS_REPLICA_SYNC,
        PathIActionKind.EXECUTION_PULL_VERIFY_MATERIALIZE,
    ],
)
def test_all_five_prerequisite_edges_fail_closed(
    action_kind: PathIActionKind,
) -> None:
    missing = evaluate_action_decision(
        make_request(action_kind),
        make_record(action_kind),
        (),
        decision_origin=ActionDecisionOriginV1.REPOSITORY_FIXTURE,
        evaluated_at=NOW,
    )
    mismatch = evaluate_action_decision(
        make_request(action_kind),
        make_record(action_kind),
        (make_predecessor(action_kind, context=make_context(run_id="other-run")),),
        decision_origin=ActionDecisionOriginV1.REPOSITORY_FIXTURE,
        evaluated_at=NOW,
    )
    assert missing.authorized and not missing.eligible_to_execute
    assert mismatch.authorized and not mismatch.eligible_to_execute
    assert mismatch.reason_codes == (ActionReasonCodeV1.CONTEXT_MISMATCH,)


def test_record_time_scope_and_path_failures_have_stable_priority() -> None:
    action_kind = PathIActionKind.DATA_LAKE_READ
    request = make_request(action_kind)
    cases = (
        (None, ActionReasonCodeV1.RECORD_MISSING),
        (
            make_record(action_kind, valid_from=NOW + timedelta(seconds=1)),
            ActionReasonCodeV1.NOT_YET_VALID,
        ),
        (
            make_record(action_kind, expires_at=NOW),
            ActionReasonCodeV1.EXPIRED,
        ),
        (
            make_record(action_kind, revoked_at=NOW),
            ActionReasonCodeV1.REVOKED,
        ),
        (
            replace(make_record(action_kind), scope_revision="other-scope"),
            ActionReasonCodeV1.SCOPE_MISMATCH,
        ),
        (
            make_record(action_kind, denied=(FIXTURE_ROOT,)),
            ActionReasonCodeV1.PATH_DENIED,
        ),
        (
            make_record(action_kind, allowed=("fixture://repository/elsewhere",)),
            ActionReasonCodeV1.PATH_NOT_ALLOWED,
        ),
    )
    for record, reason in cases:
        decision = evaluate_action_decision(
            request,
            record,
            decision_origin=ActionDecisionOriginV1.REPOSITORY_FIXTURE,
            evaluated_at=NOW,
        )
        assert not decision.authorized
        assert not decision.eligible_to_execute
        assert decision.reason_codes == (reason,)


def test_mid_operation_revocation_blocks_next_commit() -> None:
    action_kind = PathIActionKind.DATA_LAKE_READ
    before = evaluate_fixture(action_kind)
    after = evaluate_action_decision(
        make_request(action_kind),
        make_record(action_kind, revoked_at=NOW),
        decision_origin=ActionDecisionOriginV1.REPOSITORY_FIXTURE,
        evaluated_at=NOW,
    )
    pointer_commits: list[str] = []
    require_action_eligible(
        before,
        expected_kind=action_kind,
        expected_context=make_context(),
        expected_origin=ActionDecisionOriginV1.REPOSITORY_FIXTURE,
    )
    with pytest.raises(PathIEligibilityError):
        require_action_eligible(
            after,
            expected_kind=action_kind,
            expected_context=make_context(),
            expected_origin=ActionDecisionOriginV1.REPOSITORY_FIXTURE,
        )
        pointer_commits.append("commit")
    assert pointer_commits == []


def test_consumer_guard_rejects_wrong_kind_context_and_origin() -> None:
    decision = evaluate_fixture(PathIActionKind.DATA_LAKE_READ)
    with pytest.raises(PathIEligibilityError):
        require_action_eligible(
            decision,
            expected_kind=PathIActionKind.NAS_REPLICA_SYNC,
            expected_context=make_context(),
        )
    with pytest.raises(PathIEligibilityError):
        require_action_eligible(
            decision,
            expected_kind=PathIActionKind.DATA_LAKE_READ,
            expected_context=make_context(run_id="other-run"),
        )
    with pytest.raises(PathIEligibilityError):
        require_action_eligible(
            decision,
            expected_kind=PathIActionKind.DATA_LAKE_READ,
            expected_context=make_context(),
            expected_origin=ActionDecisionOriginV1.APPROVED_LEDGER,
        )


def test_decisions_are_deterministic_and_immutable() -> None:
    decisions = [evaluate_fixture(PathIActionKind.NAS_REPLICA_SYNC) for _ in range(3)]
    assert decisions[0] == decisions[1] == decisions[2]
    with pytest.raises((AttributeError, TypeError)):
        decisions[0].authorized = False


def test_direct_decision_construction_rejects_invalid_invariants() -> None:
    valid = evaluate_fixture(PathIActionKind.DATA_LAKE_READ)
    values = {field.name: getattr(valid, field.name) for field in fields(valid)}
    invalid_variants = (
        {"authorized": False, "eligible_to_execute": True},
        {
            "decision_origin": ActionDecisionOriginV1.APPROVED_LEDGER,
            "authorized": True,
            "eligible_to_execute": True,
        },
        {"target_kind": ActionTargetKindV1.REAL_OPERATION},
        {"reason_codes": (ActionReasonCodeV1.EXPIRED,)},
    )
    for changes in invalid_variants:
        with pytest.raises(PathIGovernanceError):
            ActionDecisionV1(**(values | changes))


@pytest.mark.parametrize(
    "ref_name",
    ["authorization_id", "approval_ref", "evidence_ref"],
)
def test_executable_decision_requires_all_non_empty_refs(ref_name: str) -> None:
    decision = evaluate_fixture(PathIActionKind.DATA_LAKE_READ)
    with pytest.raises(PathIGovernanceError):
        replace(decision, **{ref_name: ""})


def test_dataclasses_replace_cannot_turn_hard_deny_into_executable() -> None:
    real_context = make_context(target_kind=ActionTargetKindV1.REAL_OPERATION)
    denied = evaluate_action_decision(
        make_request(
            PathIActionKind.DATA_LAKE_READ,
            context=real_context,
            logical_path="research://approved/release/data_lake_read",
        ),
        replace(
            make_record(PathIActionKind.DATA_LAKE_READ),
            allowed_logical_paths=("research://approved/release",),
        ),
        decision_origin=ActionDecisionOriginV1.APPROVED_LEDGER,
        evaluated_at=NOW,
    )
    with pytest.raises(PathIGovernanceError):
        replace(
            denied,
            authorized=True,
            eligible_to_execute=True,
            reason_codes=(ActionReasonCodeV1.ALLOW,),
        )


def test_consumer_guard_defensively_revalidates_decision_invariants() -> None:
    forged = evaluate_fixture(PathIActionKind.DATA_LAKE_READ)
    object.__setattr__(
        forged,
        "decision_origin",
        ActionDecisionOriginV1.APPROVED_LEDGER,
    )
    with pytest.raises(PathIEligibilityError):
        require_action_eligible(
            forged,
            expected_kind=PathIActionKind.DATA_LAKE_READ,
            expected_context=make_context(),
        )


def test_constructor_and_consumer_call_the_same_invariant_validator(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = governance._validate_action_decision_invariants
    calls: list[type[PathIGovernanceError]] = []

    def tracking_validator(
        decision: ActionDecisionV1,
        *,
        error_type: type[PathIGovernanceError] = PathIGovernanceError,
    ) -> None:
        calls.append(error_type)
        original(decision, error_type=error_type)

    monkeypatch.setattr(
        governance,
        "_validate_action_decision_invariants",
        tracking_validator,
    )
    decision = evaluate_fixture(PathIActionKind.DATA_LAKE_READ)
    require_action_eligible(
        decision,
        expected_kind=PathIActionKind.DATA_LAKE_READ,
        expected_context=make_context(),
        expected_origin=ActionDecisionOriginV1.REPOSITORY_FIXTURE,
    )
    assert calls == [PathIGovernanceError, PathIEligibilityError]


@pytest.mark.parametrize(
    "logical_path",
    [
        "fixture://repository/cr172/%74arget",
        "fixture://repository/cr172%2Ftarget",
        "fixture://repository/cr172/%2E/target",
        "fixture://repository/cr172/%2E%2E/target",
        "fixture://repository/cr172/%2A",
        "fixture://repository/cr172/%25",
        "fixture://%72epository/cr172/target",
        "fixture://Repository/cr172/target",
    ],
)
def test_v1_rejects_noncanonical_percent_encoding_and_authority(
    logical_path: str,
) -> None:
    decision = evaluate_action_decision(
        make_request(PathIActionKind.DATA_LAKE_READ, logical_path=logical_path),
        make_record(PathIActionKind.DATA_LAKE_READ),
        decision_origin=ActionDecisionOriginV1.REPOSITORY_FIXTURE,
        evaluated_at=NOW,
    )
    assert not decision.authorized
    assert not decision.eligible_to_execute
    assert decision.reason_codes == (ActionReasonCodeV1.FIXTURE_URI_REQUIRED,)


@pytest.mark.parametrize(
    ("allowed", "denied"),
    [
        (("fixture://repository/cr172/%74arget",), ()),
        ((FIXTURE_ROOT,), ("fixture://repository/cr172/%64enied",)),
    ],
)
def test_record_allow_and_deny_paths_use_the_same_canonical_form(
    allowed: tuple[str, ...],
    denied: tuple[str, ...],
) -> None:
    decision = evaluate_action_decision(
        make_request(PathIActionKind.DATA_LAKE_READ),
        make_record(
            PathIActionKind.DATA_LAKE_READ,
            allowed=allowed,
            denied=denied,
        ),
        decision_origin=ActionDecisionOriginV1.REPOSITORY_FIXTURE,
        evaluated_at=NOW,
    )
    assert not decision.authorized
    assert not decision.eligible_to_execute
    assert decision.reason_codes == (ActionReasonCodeV1.RECORD_INVALID,)


def test_plain_canonical_allowed_and_denied_subtree_controls_are_stable() -> None:
    allowed = evaluate_action_decision(
        make_request(PathIActionKind.DATA_LAKE_READ),
        make_record(PathIActionKind.DATA_LAKE_READ),
        decision_origin=ActionDecisionOriginV1.REPOSITORY_FIXTURE,
        evaluated_at=NOW,
    )
    denied_root = f"{FIXTURE_ROOT}/denied"
    denied = evaluate_action_decision(
        make_request(
            PathIActionKind.DATA_LAKE_READ,
            logical_path=f"{denied_root}/child",
        ),
        make_record(
            PathIActionKind.DATA_LAKE_READ,
            denied=(denied_root,),
        ),
        decision_origin=ActionDecisionOriginV1.REPOSITORY_FIXTURE,
        evaluated_at=NOW,
    )
    assert allowed.authorized and allowed.eligible_to_execute
    assert allowed.reason_codes == (ActionReasonCodeV1.ALLOW,)
    assert not denied.authorized and not denied.eligible_to_execute
    assert denied.reason_codes == (ActionReasonCodeV1.PATH_DENIED,)


def test_empirical_disposition_has_exactly_four_states_and_pre_v2_ceiling() -> None:
    compute_decision = evaluate_fixture(PathIActionKind.EMPIRICAL_R_COMPUTATION)
    base = EmpiricalRInputsV1(
        declared_fixture_matrix=False,
        source_available=True,
        sealed_provenance_complete=True,
        alignment_complete=True,
        method_version_ref="method-v2-fixture",
        method_hash_valid=True,
        compute_decision=compute_decision,
        integrity_conflict=False,
        unapproved_repair=False,
        independently_verified=True,
    )
    dispositions = (
        classify_empirical_r(replace(base, declared_fixture_matrix=True)),
        classify_empirical_r(base),
        classify_empirical_r(replace(base, method_version_ref="")),
        classify_empirical_r(replace(base, integrity_conflict=True)),
    )
    assert {item.state for item in dispositions} == set(EmpiricalRStateV1)
    assert all(not item.positive_effective_count for item in dispositions)
    assert all(not item.c1_computable for item in dispositions)


def test_run_path_is_contract_only_and_runtime_deferred() -> None:
    new_decision = decide_run_path(
        RunPathIntentV1(
            mode=RunPathModeV1.NEW_SEMANTIC_ROOT,
            logical_root=NEW_RUN_LOGICAL_ROOT_TEMPLATE,
            requested_operation="contract",
        )
    )
    legacy_decision = decide_run_path(
        RunPathIntentV1(
            mode=RunPathModeV1.LEGACY_READ_ONLY,
            logical_root=LEGACY_RUN_LOGICAL_ROOT_TEMPLATE,
            requested_operation="read",
        )
    )
    assert not new_decision.writable
    assert not legacy_decision.writable
    assert new_decision.delivery_status == governance.RUN_PATH_DELIVERY_STATUS
    assert legacy_decision.delivery_status == governance.RUN_PATH_DELIVERY_STATUS
    for operation in ("write", "move", "rename", "rewrite", "migration"):
        with pytest.raises(PathIGovernanceError):
            decide_run_path(
                RunPathIntentV1(
                    mode=RunPathModeV1.LEGACY_READ_ONLY,
                    logical_root=LEGACY_RUN_LOGICAL_ROOT_TEMPLATE,
                    requested_operation=operation,
                )
            )


def make_signal_boundary() -> SignalBatchBoundaryV1:
    return SignalBatchBoundaryV1(
        schema_version="signal-batch-boundary.v1",
        batch_id="batch-fixture-001",
        strategy_id="strategy-fixture-001",
        strategy_package_hash=HASH_A,
        content_sha256=HASH_B,
        signature_key=SignatureKeySlotV1(
            signature="fixture-signature",
            key_id="fixture-key-001",
        ),
        validity_window=ValidityWindowSlotV1(
            valid_from=NOW,
            valid_until=NOW + timedelta(minutes=5),
        ),
        sequence_no=1,
    )


def test_signal_boundary_has_exactly_eight_semantic_slots() -> None:
    assert len(fields(SignalBatchBoundaryV1)) == 8
    boundary = make_signal_boundary()
    assert validate_signal_batch_boundary(boundary) is boundary
    with pytest.raises(PathIGovernanceError):
        validate_signal_batch_boundary(
            replace(
                boundary,
                signature_key=SignatureKeySlotV1(
                    signature="fixture-signature",
                    key_id="credential-token",
                ),
            )
        )
    with pytest.raises(TypeError):
        SignalBatchBoundaryV1(
            **{
                field.name: getattr(boundary, field.name)
                for field in fields(SignalBatchBoundaryV1)
                if field.name != "sequence_no"
            }
        )


@pytest.mark.parametrize(
    "field_name",
    [
        "stage3_entry_ready",
        "c1_computable",
        "real_data_authorized",
        "multi_trial_runtime_authorized",
        "signal_transport_authorized",
    ],
)
def test_claim_ceiling_rejects_each_high_order_true(field_name: str) -> None:
    claim = PathIClaimCeilingV1(path_i_design_ready=True)
    assert enforce_path_i_claim_ceiling(claim) is claim
    values = {field.name: getattr(claim, field.name) for field in fields(claim)}
    values[field_name] = True
    with pytest.raises(PathIGovernanceError):
        PathIClaimCeilingV1(**values)


def test_governance_module_has_zero_operation_surface() -> None:
    forbidden_import_roots = {
        "boto3",
        "os",
        "pandas",
        "pathlib",
        "pyarrow",
        "requests",
        "shutil",
        "socket",
        "subprocess",
    }
    imported_roots = {
        value.__name__.split(".", 1)[0]
        for value in vars(governance).values()
        if getattr(value, "__class__", None).__name__ == "module"
        and hasattr(value, "__name__")
    }
    assert imported_roots.isdisjoint(forbidden_import_roots)
    assert not hasattr(governance, "authorization_backend")
    assert not hasattr(governance, "signal_exchange")
    assert not hasattr(governance, "runtime_adapter")
