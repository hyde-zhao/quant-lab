"""CR-172 S05：六动作授权、DAG 与 caller 自报拒绝 QAC。"""

from __future__ import annotations

from dataclasses import replace

import pytest

from engine.path_i_governance import (
    ACTION_ENFORCEMENT_POINTS,
    DIRECT_PREREQUISITE,
    ActionDecisionOriginV1,
    ActionPrerequisiteProvenanceV1,
    ActionReasonCodeV1,
    ActionTargetKindV1,
    PathIActionKind,
    PathIEligibilityError,
    require_action_eligible,
)
from tests.fixtures.cr172_path_i.path_i_fixture import (
    build_chain,
    load_fixture,
    make_context,
    make_decision,
    make_predecessor,
    make_record,
)


def test_six_actions_records_enforcement_and_dag() -> None:
    fixture = load_fixture()
    actions = tuple(PathIActionKind)
    records = tuple(make_record(fixture, action) for action in actions)
    edges = {
        (predecessor, action)
        for action, predecessor in DIRECT_PREREQUISITE.items()
        if predecessor is not None
    }

    assert len(actions) == 6
    assert len(records) == 6
    assert len(ACTION_ENFORCEMENT_POINTS) == 6
    assert len(DIRECT_PREREQUISITE) == 6
    assert len(edges) == 5
    assert {record.action_kind for record in records} == set(actions)
    assert all(record.allowed_logical_paths == (fixture["identity"]["logical_uri"],) for record in records)
    assert all(source in actions and target in actions for source, target in edges)
    assert all(source is not target for source, target in edges)


def test_all_repository_fixture_actions_are_eligible() -> None:
    chain = build_chain()
    source = chain.verified_source
    generation = chain.decisions[PathIActionKind.TRIAL_RETURN_GENERATION]
    empirical = make_decision(
        chain.fixture,
        PathIActionKind.EMPIRICAL_R_COMPUTATION,
        predecessor=make_predecessor(
            chain.fixture,
            generation,
            ActionPrerequisiteProvenanceV1.SEALED_TRIAL_RETURN,
            content_sha256=source.bundle.payload.content_sha256,
            manifest_sha256=source.bundle.manifest_sha256,
        ),
    )
    decisions = {**chain.decisions, PathIActionKind.EMPIRICAL_R_COMPUTATION: empirical}

    assert set(decisions) == set(PathIActionKind)
    assert sum(decision.authorized for decision in decisions.values()) == 6
    assert sum(decision.eligible_to_execute for decision in decisions.values()) == 6
    for action, decision in decisions.items():
        require_action_eligible(
            decision,
            expected_kind=action,
            expected_context=chain.context,
            expected_origin=ActionDecisionOriginV1.REPOSITORY_FIXTURE,
        )


def test_runtime_without_read_is_denied() -> None:
    fixture = load_fixture()
    context = make_context(fixture)
    decision = make_decision(
        fixture,
        PathIActionKind.MULTI_TRIAL_RUNTIME_AND_WORKSPACE_WRITE,
    )

    assert decision.authorized is True
    assert decision.eligible_to_execute is False
    assert decision.reason_codes == (ActionReasonCodeV1.PREDECESSOR_MISSING,)
    with pytest.raises(PathIEligibilityError):
        require_action_eligible(
            decision,
            expected_kind=PathIActionKind.MULTI_TRIAL_RUNTIME_AND_WORKSPACE_WRITE,
            expected_context=context,
        )


def test_missing_predecessor_fails_closed() -> None:
    fixture = load_fixture()
    decision = make_decision(
        fixture,
        PathIActionKind.NAS_REPLICA_SYNC,
    )

    assert decision.authorized is True
    assert decision.eligible_to_execute is False
    assert decision.reason_codes == (ActionReasonCodeV1.PREDECESSOR_MISSING,)


def test_revoked_record_fails_closed() -> None:
    fixture = load_fixture()
    oracle = fixture["mutations"]["revoked_record"]
    record = make_record(fixture, PathIActionKind.DATA_LAKE_READ, revoked=True)
    decision = make_decision(
        fixture,
        PathIActionKind.DATA_LAKE_READ,
        record=record,
    )

    assert decision.authorized is False
    assert decision.eligible_to_execute is False
    assert decision.reason_codes[0].value == oracle["reason"]
    assert oracle["authorized"] == 0
    assert oracle["eligible"] == 0


def test_predecessor_context_mismatch_fails_closed() -> None:
    fixture = load_fixture()
    read = make_decision(fixture, PathIActionKind.DATA_LAKE_READ)
    mismatched_context = make_context(fixture, scope_revision="cr172-s05-other-scope")
    predecessor = make_predecessor(
        fixture,
        read,
        ActionPrerequisiteProvenanceV1.ELIGIBILITY_DECISION,
        context=mismatched_context,
    )
    decision = make_decision(
        fixture,
        PathIActionKind.MULTI_TRIAL_RUNTIME_AND_WORKSPACE_WRITE,
        predecessor=predecessor,
    )

    assert decision.authorized is True
    assert decision.eligible_to_execute is False
    assert decision.reason_codes == (ActionReasonCodeV1.CONTEXT_MISMATCH,)


def test_approved_ledger_origin_is_unconditionally_denied() -> None:
    fixture = load_fixture()
    decision = make_decision(
        fixture,
        PathIActionKind.DATA_LAKE_READ,
        origin=ActionDecisionOriginV1.APPROVED_LEDGER,
    )

    assert decision.authorized is False
    assert decision.eligible_to_execute is False
    assert decision.reason_codes == (
        ActionReasonCodeV1.APPROVED_LEDGER_ADAPTER_UNAVAILABLE,
    )


def test_valid_looking_real_target_cannot_self_authorize() -> None:
    fixture = load_fixture()
    real_context = make_context(
        fixture,
        target_kind=ActionTargetKindV1.REAL_OPERATION,
    )
    record = make_record(fixture, PathIActionKind.DATA_LAKE_READ)
    decision = make_decision(
        fixture,
        PathIActionKind.DATA_LAKE_READ,
        context=real_context,
        record=record,
        origin=ActionDecisionOriginV1.APPROVED_LEDGER,
    )

    assert decision.authorized is False
    assert decision.eligible_to_execute is False
    assert decision.reason_codes == (
        ActionReasonCodeV1.APPROVED_LEDGER_ADAPTER_UNAVAILABLE,
    )
    with pytest.raises(PathIEligibilityError):
        require_action_eligible(
            decision,
            expected_kind=PathIActionKind.DATA_LAKE_READ,
            expected_context=real_context,
        )


def test_fixture_origin_cannot_target_real_operation() -> None:
    fixture = load_fixture()
    real_context = make_context(
        fixture,
        target_kind=ActionTargetKindV1.REAL_OPERATION,
    )
    record = make_record(fixture, PathIActionKind.DATA_LAKE_READ)
    decision = make_decision(
        fixture,
        PathIActionKind.DATA_LAKE_READ,
        context=real_context,
        record=record,
    )

    assert decision.authorized is False
    assert decision.eligible_to_execute is False
    assert decision.reason_codes == (ActionReasonCodeV1.ORIGIN_TARGET_MISMATCH,)
