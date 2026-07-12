from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
import inspect

import pytest

from engine.experiment_family_lineage import (
    AppendCorrection, AttemptState, C1InputStatus, CommandReceipt, DeclareFamily,
    DeclareTrial, ExperimentFamilyManifest, ExperimentFamilySpec, ExperimentTrial,
    FamilyLineageSession, FamilyState, FinalizeTrial, FinishAttempt,
    FamilyLineageValidationResult, LineageAvailability, LineageBlockedCode, LineageCommand, PERSISTENT_LINEAGE_OBJECTS,
    RecordSelection, RequestSeal, RequestSupersedingSeal, SelectionDecision,
    StartAttempt, TYPED_LINEAGE_COMMANDS, TrialAttempt, TrialSelection, TrialState,
    ValidationStatus, canonical_lineage_value_bytes, derive_stable_trial_id,
    fold_family_lineage, not_applicable_family_lineage, project_family_evidence,
    transition_attempt_state, transition_family_state, transition_trial_state,
    unavailable_family_lineage, validate_family_lineage,
)


def spec() -> ExperimentFamilySpec:
    return ExperimentFamilySpec(1, "family-1", "producer-1", 0, "objective:1", "space:1", metadata={"b": 2, "a": [1]})


def trial(seed: int = 7, *, suffix: str = "") -> ExperimentTrial:
    params = {"lookback": 20, "alpha": 0.1 + (0.01 if suffix else 0)}
    trial_id = derive_stable_trial_id("family-1", params, seed)
    return ExperimentTrial("family-1", trial_id, params, seed, 1)


def commands_for_terminal_trial(state: TrialState = TrialState.FAILED):
    item = trial()
    attempt = TrialAttempt("family-1", item.trial_id, "attempt-1", 1)
    reason = "fixture terminal" if state is not TrialState.SUCCEEDED else ""
    return item, [
        DeclareFamily("event-0", "family-1", 0, spec=spec()),
        DeclareTrial("event-1", "family-1", 1, trial=item),
        StartAttempt("event-2", "family-1", 2, attempt=attempt),
        FinishAttempt("event-3", "family-1", 3, attempt_id="attempt-1", state=AttemptState.FAILED, terminal_reason="retry stopped"),
        FinalizeTrial("event-4", "family-1", 4, trial_id=item.trial_id, state=state, terminal_reason=reason),
        RequestSeal("event-5", "family-1", 5, manifest_version=1),
    ]


def manifest_for(item: ExperimentTrial, *, event_count: int = 6, last_sequence: int = 5) -> ExperimentFamilyManifest:
    return ExperimentFamilyManifest(1, "family-1", 1, "spec.json", "events.jsonl", event_count, last_sequence, 1, (item.trial_id,), seal_hash="sha256:fixture")


def test_persistent_inventory_is_exactly_six_frozen_slotted_objects() -> None:
    assert [item.__name__ for item in PERSISTENT_LINEAGE_OBJECTS] == ["ExperimentFamilySpec", "ExperimentTrial", "TrialAttempt", "TrialSelection", "ExperimentFamilyManifest", "FamilyLineageValidationResult"]
    assert len(PERSISTENT_LINEAGE_OBJECTS) == 6
    assert FamilyLineageSession not in PERSISTENT_LINEAGE_OBJECTS
    for item in PERSISTENT_LINEAGE_OBJECTS:
        assert is_dataclass(item)
        assert "__slots__" in item.__dict__
    value = spec()
    with pytest.raises(FrozenInstanceError):
        value.family_id = "changed"  # type: ignore[misc]
    source = {"nested": [1]}
    frozen = ExperimentFamilySpec(1, "family-x", "producer", 0, "objective", "space", metadata=source)
    source["nested"].append(2)
    assert frozen.to_dict()["metadata"] == {"nested": [1]}


def test_canonical_value_and_stable_trial_id_are_strict_and_deterministic() -> None:
    left = derive_stable_trial_id("family-1", {"b": 2, "a": [1, {"z": True}]}, 7)
    right = derive_stable_trial_id("family-1", {"a": [1, {"z": True}], "b": 2}, 7)
    assert left == right
    assert left.startswith("trial-sha256:") and len(left) == 77
    assert left != derive_stable_trial_id("family-1", {"a": [1, {"z": True}], "b": 2}, 8)
    assert canonical_lineage_value_bytes({"b": 2, "a": 1}) == b'{"a":1,"b":2}'
    assert b'"family_id":"family-1"' in canonical_lineage_value_bytes(spec())
    with pytest.raises((TypeError, ValueError)):
        canonical_lineage_value_bytes({"bad": float("nan")})
    with pytest.raises(TypeError):
        canonical_lineage_value_bytes({1: "bad-key"})


@pytest.mark.parametrize("current,target", [(FamilyState.ABSENT, FamilyState.DECLARED), (FamilyState.DECLARED, FamilyState.RECORDING), (FamilyState.RECORDING, FamilyState.SEALED), (FamilyState.SEALED, FamilyState.SUPERSEDED)])
def test_legal_family_transitions(current, target) -> None:
    assert transition_family_state(current, target).accepted


@pytest.mark.parametrize("current,target", [(TrialState.DECLARED, TrialState.ACTIVE), (TrialState.DECLARED, TrialState.NEVER_STARTED), (TrialState.DECLARED, TrialState.EXCLUDED), *[(TrialState.ACTIVE, state) for state in (TrialState.SUCCEEDED, TrialState.FAILED, TrialState.CANCELLED, TrialState.EXCLUDED)]])
def test_legal_trial_transitions(current, target) -> None:
    assert transition_trial_state(current, target).accepted


@pytest.mark.parametrize("current,target", [(AttemptState.DECLARED, AttemptState.RUNNING), *[(AttemptState.RUNNING, state) for state in (AttemptState.SUCCEEDED, AttemptState.FAILED, AttemptState.CANCELLED)]])
def test_legal_attempt_transitions(current, target) -> None:
    assert transition_attempt_state(current, target).accepted


def test_every_nonlisted_and_unknown_transition_fails_closed() -> None:
    legal = {(FamilyState.ABSENT, FamilyState.DECLARED), (FamilyState.DECLARED, FamilyState.RECORDING), (FamilyState.RECORDING, FamilyState.SEALED), (FamilyState.SEALED, FamilyState.SUPERSEDED)}
    for current in FamilyState:
        for target in FamilyState:
            if (current, target) not in legal:
                result = transition_family_state(current, target)
                assert not result.accepted and result.blocked_reason == "illegal_family_transition"
    assert transition_trial_state("unknown", TrialState.ACTIVE).blocked_reason == "illegal_trial_transition"
    assert transition_attempt_state(AttemptState.RUNNING, "unknown").blocked_reason == "illegal_attempt_transition"


def test_nine_typed_commands_have_fixed_type_and_common_envelope() -> None:
    assert len(TYPED_LINEAGE_COMMANDS) == 9
    assert {item.command_type for item in TYPED_LINEAGE_COMMANDS} == {"declare_family", "declare_trial", "start_attempt", "finish_attempt", "finalize_trial", "record_selection", "request_seal", "append_correction", "request_superseding_seal"}
    for command in TYPED_LINEAGE_COMMANDS:
        assert {"event_id", "family_id", "sequence", "schema_version"} <= {item.name for item in fields(command)}
        assert "command_type" not in inspect.signature(command).parameters


class Recorder:
    def __init__(self) -> None:
        self.commands = []
        self.payloads = {}

    def submit(self, command):
        payload = canonical_lineage_value_bytes(command.to_dict())
        if command.event_id in self.payloads:
            same = self.payloads[command.event_id] == payload
            return CommandReceipt(command.event_id, same, idempotent=same, blocked_reasons=() if same else ("event_identity_conflict",))
        self.payloads[command.event_id] = payload
        self.commands.append(command)
        return CommandReceipt(command.event_id, True)


def test_session_submits_immediately_and_surfaces_idempotency_signal() -> None:
    recorder = Recorder()
    session = FamilyLineageSession.open(spec(), recorder, "opaque-local-root")
    item = trial()
    command = DeclareTrial("trial-event", "family-1", 1, trial=item)
    assert len(recorder.commands) == 1 and isinstance(recorder.commands[0], DeclareFamily)
    assert session.submit(command).accepted and len(recorder.commands) == 2
    assert session.submit(command).idempotent and len(recorder.commands) == 2
    conflict = DeclareTrial("trial-event", "family-1", 1, trial=trial(seed=8))
    assert session.submit(conflict).blocked_reasons == ("event_identity_conflict",)
    assert session.submit(DeclareTrial("foreign", "family-2", 2, trial=item)).blocked_reasons == ("family_identity_mismatch",)
    assert isinstance(session.seal(1).request_receipt, CommandReceipt)


def test_raw_count_is_distinct_declared_trial_identity_not_attempt_or_selection_count() -> None:
    first = trial()
    second = trial(seed=8)
    commands = [DeclareFamily("e0", "family-1", 0, spec=spec())]
    sequence = 1
    for item, terminal in ((first, TrialState.FAILED), (second, TrialState.EXCLUDED)):
        commands.append(DeclareTrial(f"e{sequence}", "family-1", sequence, trial=item)); sequence += 1
        if terminal is TrialState.FAILED:
            for ordinal in range(1, 4):
                attempt = TrialAttempt("family-1", item.trial_id, f"attempt-{ordinal}", ordinal)
                commands.extend([StartAttempt(f"e{sequence}", "family-1", sequence, attempt=attempt), FinishAttempt(f"e{sequence+1}", "family-1", sequence+1, attempt_id=attempt.attempt_id, state=AttemptState.FAILED, terminal_reason="retry")]); sequence += 2
        commands.append(FinalizeTrial(f"e{sequence}", "family-1", sequence, trial_id=item.trial_id, state=terminal, terminal_reason="terminal fixture")); sequence += 1
        selection = TrialSelection("family-1", item.trial_id, f"selection-{sequence}", sequence, SelectionDecision.EXCLUDED, "fixture")
        commands.append(RecordSelection(f"e{sequence}", "family-1", sequence, selection=selection)); sequence += 1
    result = fold_family_lineage(spec(), commands)
    assert result.raw_trial_count == 2
    assert result.trial_ids == tuple(sorted((first.trial_id, second.trial_id)))


def test_validator_pass_is_target_bound_and_effective_count_is_unavailable() -> None:
    item, commands = commands_for_terminal_trial()
    manifest = manifest_for(item)
    result = validate_family_lineage(manifest, spec(), commands, target_ref="manifest-v1.json", target_hash="sha256:fixture", forbidden_operation_counts={"runtime": 0, "external": 0})
    assert result.validation_status is ValidationStatus.PASS
    assert result.availability is LineageAvailability.PRESENT
    projection = project_family_evidence(manifest, result)
    assert projection.availability is LineageAvailability.PRESENT
    assert projection.raw_trial_count == 1
    assert projection.effective_trial_count_availability is LineageAvailability.TYPED_UNAVAILABLE
    assert projection.effective_trial_count is None and projection.effective_ref == projection.effective_method == ""
    assert projection.c1_input_status is C1InputStatus.RAW_INPUT_READY


@pytest.mark.parametrize("target_ref,target_hash,code", [("", "sha256:fixture", "target_ref_missing"), ("manifest-v1.json", "", "target_hash_missing"), ("manifest-v1.json", "sha256:wrong", "target_mismatch")])
def test_validator_blocks_missing_or_mismatched_target(target_ref, target_hash, code) -> None:
    item, commands = commands_for_terminal_trial()
    result = validate_family_lineage(manifest_for(item), spec(), commands, target_ref=target_ref, target_hash=target_hash)
    assert result.validation_status is ValidationStatus.BLOCKED
    assert code in result.blocked_reasons


def test_orphans_incomplete_identity_count_and_forbidden_operations_block_deterministically() -> None:
    item = trial()
    orphan_attempt = TrialAttempt("family-1", item.trial_id, "orphan", 1)
    orphan_selection = TrialSelection("family-1", item.trial_id, "selection", 2, SelectionDecision.REJECTED, "fixture")
    commands = [DeclareFamily("e0", "family-1", 0, spec=spec()), StartAttempt("e1", "family-1", 1, attempt=orphan_attempt), RecordSelection("e2", "family-1", 2, selection=orphan_selection), RequestSeal("e3", "family-1", 3)]
    result = validate_family_lineage(ExperimentFamilyManifest(1, "family-1", 1, "spec", "events", 4, 3, 1, (item.trial_id,), seal_hash="hash"), spec(), commands, target_ref="manifest", target_hash="hash", forbidden_operation_counts={"runtime": 1})
    assert result.blocked_reasons == tuple(sorted(result.blocked_reasons))
    assert {"orphan_attempt", "orphan_selection", "raw_trial_count_mismatch", "forbidden_operation_nonzero"} <= set(result.blocked_reasons)


def test_unavailable_not_applicable_and_blocked_projection_never_promote_status() -> None:
    unavailable = unavailable_family_lineage("producer not instrumented")
    projection = project_family_evidence(None, unavailable)
    assert projection.availability is LineageAvailability.TYPED_UNAVAILABLE and projection.raw_trial_count is None
    excluded = project_family_evidence(None, not_applicable_family_lineage("producer explicitly excluded"))
    assert excluded.availability is LineageAvailability.NOT_APPLICABLE_WITH_REASON
    item, commands = commands_for_terminal_trial()
    blocked = validate_family_lineage(manifest_for(item), spec(), commands, target_ref="manifest", target_hash="wrong")
    blocked_projection = project_family_evidence(manifest_for(item), blocked)
    assert blocked_projection.availability is LineageAvailability.BLOCKED
    assert blocked_projection.c1_input_status is C1InputStatus.INPUT_BLOCKED


def test_manifest_freezes_event_boundary_and_module_has_no_forbidden_imports() -> None:
    item = trial()
    manifest = manifest_for(item)
    assert manifest.to_dict()["sealed_event_count"] == 6
    assert manifest.to_dict()["sealed_last_sequence"] == 5
    source = inspect.getsource(inspect.getmodule(ExperimentFamilySpec))
    for forbidden in ("experiment_family_lineage_store", "mature_multifactor_research", "strategy_admission", "credential", "requests", "boto", "nas"):
        assert f"import {forbidden}" not in source and f"from {forbidden}" not in source
    assert set(item.value for item in LineageBlockedCode) >= {"storage_artifact_missing", "supersession_cycle", "effective_trial_claim_forbidden"}


def test_v1_validation_replays_exact_frozen_prefix_after_authorized_suffix_append() -> None:
    item, v1_commands = commands_for_terminal_trial()
    manifest = manifest_for(item)
    before = validate_family_lineage(manifest, spec(), v1_commands, target_ref="manifest-v1.json", target_hash="sha256:fixture")
    suffix = [
        AppendCorrection("event-6", "family-1", 6, corrects_event_id="event-4", reason="audit correction", correction={"note": "append-only"}),
        RequestSupersedingSeal("event-7", "family-1", 7, manifest_version=2, prior_head_ref="manifest-v1.json", prior_head_hash="sha256:fixture", reason="authorized correction"),
    ]
    after = validate_family_lineage(manifest, spec(), [*v1_commands, *suffix], target_ref="manifest-v1.json", target_hash="sha256:fixture")
    assert before.validation_status is ValidationStatus.PASS
    assert after.validation_status is ValidationStatus.PASS
    assert after.recomputed_raw_trial_count == before.recomputed_raw_trial_count == 1


@pytest.mark.parametrize(
    "event_count,last_sequence",
    [(5, 5), (7, 5), (6, 4), (6, 6)],
)
def test_malformed_or_ambiguous_frozen_boundary_blocks_deterministically(event_count, last_sequence) -> None:
    item, commands = commands_for_terminal_trial()
    malformed = manifest_for(item, event_count=event_count, last_sequence=last_sequence)
    first = validate_family_lineage(malformed, spec(), commands, target_ref="manifest-v1.json", target_hash="sha256:fixture")
    second = validate_family_lineage(malformed, spec(), list(reversed(commands)), target_ref="manifest-v1.json", target_hash="sha256:fixture")
    assert first.validation_status is ValidationStatus.BLOCKED
    assert LineageBlockedCode.TARGET_MISMATCH.value in first.blocked_reasons
    assert first.blocked_reasons == second.blocked_reasons


def test_internal_sequence_gap_in_frozen_boundary_blocks_even_when_count_matches() -> None:
    item, commands = commands_for_terminal_trial()
    commands_without_sequence_three = [command for command in commands if command.sequence != 3]
    malformed = manifest_for(item, event_count=5, last_sequence=5)
    result = validate_family_lineage(malformed, spec(), commands_without_sequence_three, target_ref="manifest-v1.json", target_hash="sha256:fixture")
    assert result.validation_status is ValidationStatus.BLOCKED
    assert LineageBlockedCode.TARGET_MISMATCH.value in result.blocked_reasons


def _sealed_commands():
    item, commands = commands_for_terminal_trial()
    return item, commands


@pytest.mark.parametrize("mutation_kind", ["declare_family", "declare", "start", "finish", "finalize", "selection", "request_seal"])
@pytest.mark.parametrize("superseded", [False, True])
def test_post_seal_and_post_supersession_mutations_preserve_state_and_membership(mutation_kind, superseded) -> None:
    item, commands = _sealed_commands()
    if superseded:
        commands.append(RequestSupersedingSeal("event-6", "family-1", 6, manifest_version=2, prior_head_ref="v1", prior_head_hash="hash-v1", reason="correction"))
    base = fold_family_lineage(spec(), commands)
    second = trial(seed=9)
    attempt = TrialAttempt("family-1", item.trial_id, "late-attempt", 2)
    sequence = 7 if superseded else 6
    mutations = {
        "declare_family": DeclareFamily("late", "family-1", sequence, spec=spec()),
        "declare": DeclareTrial("late", "family-1", sequence, trial=second),
        "start": StartAttempt("late", "family-1", sequence, attempt=attempt),
        "finish": FinishAttempt("late", "family-1", sequence, attempt_id="attempt-1", state=AttemptState.SUCCEEDED, terminal_reason="late"),
        "finalize": FinalizeTrial("late", "family-1", sequence, trial_id=item.trial_id, state=TrialState.SUCCEEDED, terminal_reason="late"),
        "selection": RecordSelection("late", "family-1", sequence, selection=TrialSelection("family-1", item.trial_id, "late-selection", sequence, SelectionDecision.SELECTED, "late")),
        "request_seal": RequestSeal("late", "family-1", sequence, manifest_version=1),
    }
    result = fold_family_lineage(spec(), [*commands, mutations[mutation_kind]])
    assert result.family_state is base.family_state
    assert result.raw_trial_count == base.raw_trial_count == 1
    assert result.trial_ids == base.trial_ids
    expected = "post_hoc_declaration" if mutation_kind == "declare" else "illegal_family_transition"
    assert expected in result.blocked_reasons


@pytest.mark.parametrize("availability", list(LineageAvailability))
@pytest.mark.parametrize("status", list(ValidationStatus))
@pytest.mark.parametrize("has_reasons", [False, True])
@pytest.mark.parametrize("has_target", [False, True])
@pytest.mark.parametrize("has_manifest", [False, True])
def test_projection_exhaustively_requires_coherent_target_bound_pass(availability, status, has_reasons, has_target, has_manifest) -> None:
    item = trial()
    manifest = manifest_for(item) if has_manifest else None
    target_ref = "manifest-v1.json" if has_target else ""
    target_hash = "sha256:fixture" if has_target else ""
    result = FamilyLineageValidationResult(
        schema_version=1,
        validation_id="validation:matrix",
        target_ref=target_ref,
        target_hash=target_hash,
        availability=availability,
        validation_status=status,
        blocked_reasons=("target_mismatch",) if has_reasons else (),
        unavailable_reason="explicit unavailable" if availability in (LineageAvailability.TYPED_UNAVAILABLE, LineageAvailability.NOT_APPLICABLE_WITH_REASON) else "",
        recomputed_raw_trial_count=1,
        declared_raw_trial_count=1,
    )
    projection = project_family_evidence(manifest, result)
    coherent = availability is LineageAvailability.PRESENT and status is ValidationStatus.PASS and not has_reasons and has_target and has_manifest
    assert (projection.availability is LineageAvailability.PRESENT) is coherent
    assert (projection.c1_input_status is C1InputStatus.RAW_INPUT_READY) is coherent


@pytest.mark.parametrize("unknown_type", [LineageCommand, type("UnknownLineageCommand", (LineageCommand,), {})])
def test_unknown_or_base_command_fails_closed_without_extending_fold_boundary(unknown_type) -> None:
    item, commands = commands_for_terminal_trial()
    base = fold_family_lineage(spec(), commands)
    unknown = unknown_type("unknown-event", "family-1", 6)
    result = fold_family_lineage(spec(), [*commands, unknown])
    assert result.family_state is base.family_state
    assert result.raw_trial_count == base.raw_trial_count
    assert result.event_count == base.event_count
    assert result.last_sequence == base.last_sequence
    assert LineageBlockedCode.SCHEMA_VERSION_UNSUPPORTED.value in result.blocked_reasons
    validation = validate_family_lineage(manifest_for(item), spec(), [*commands, unknown], target_ref="manifest-v1.json", target_hash="sha256:fixture")
    assert validation.validation_status is ValidationStatus.PASS
    # The unknown suffix is outside v1's immutable prefix; validating a head
    # that includes it must fail closed rather than count it silently.
    malformed_head = manifest_for(item, event_count=7, last_sequence=6)
    malformed_validation = validate_family_lineage(malformed_head, spec(), [*commands, unknown], target_ref="manifest-v1.json", target_hash="sha256:fixture")
    assert malformed_validation.validation_status is ValidationStatus.BLOCKED
    assert {"schema_version_unsupported", "target_mismatch"} <= set(malformed_validation.blocked_reasons)


@pytest.mark.parametrize(
    "changed",
    [
        {"schema_version": 2},
        {"producer_chain_id": "producer-drift"},
        {"objective_ref": "objective:drift"},
        {"parameter_space_ref": "space:drift"},
        {"run_refs": ("run:drift",)},
        {"experiment_refs": ("experiment:drift",)},
        {"metadata": {"drift": True}},
    ],
)
def test_declare_family_binds_complete_nested_spec_content_before_state_advances(changed) -> None:
    authoritative = spec()
    conflicting = replace(authoritative, **changed)
    command = DeclareFamily("event-0", "family-1", 0, spec=conflicting)
    fold = fold_family_lineage(authoritative, [command])
    assert fold.family_state is FamilyState.ABSENT
    assert fold.raw_trial_count == 0
    assert fold.blocked_reasons == (LineageBlockedCode.EVENT_IDENTITY_CONFLICT.value,)
    manifest = ExperimentFamilyManifest(1, "family-1", 1, "spec", "events", 1, 0, 0, (), seal_hash="hash")
    validation = validate_family_lineage(manifest, authoritative, [command], target_ref="manifest", target_hash="hash")
    assert validation.validation_status is ValidationStatus.BLOCKED
    assert LineageBlockedCode.EVENT_IDENTITY_CONFLICT.value in validation.blocked_reasons


@pytest.mark.parametrize(
    "selection_family,selection_trial,expected",
    [
        ("family-foreign", "local", LineageBlockedCode.FAMILY_IDENTITY_MISMATCH.value),
        ("family-1", "orphan", LineageBlockedCode.ORPHAN_SELECTION.value),
    ],
)
def test_record_selection_binds_nested_family_and_declared_local_parent(selection_family, selection_trial, expected) -> None:
    item, commands = commands_for_terminal_trial()
    selected_trial_id = item.trial_id if selection_trial == "local" else derive_stable_trial_id("family-1", {"orphan": True}, 99)
    selection = TrialSelection(selection_family, selected_trial_id, "selection-identity", 5, SelectionDecision.SELECTED, "identity probe")
    command_stream = [*commands[:-1], RecordSelection("event-selection", "family-1", 5, selection=selection), RequestSeal("event-6", "family-1", 6)]
    fold = fold_family_lineage(spec(), command_stream)
    assert fold.family_state is FamilyState.SEALED
    assert fold.raw_trial_count == 1
    assert fold.trial_ids == (item.trial_id,)
    assert expected in fold.blocked_reasons
    manifest = manifest_for(item, event_count=7, last_sequence=6)
    validation = validate_family_lineage(manifest, spec(), command_stream, target_ref="manifest", target_hash="sha256:fixture")
    assert validation.validation_status is ValidationStatus.BLOCKED
    assert expected in validation.blocked_reasons


def _all_command_identity_case(command_name: str):
    authoritative = spec()
    item = trial()
    declared = [DeclareFamily("event-0", "family-1", 0, spec=authoritative)]
    with_trial = [*declared, DeclareTrial("event-1", "family-1", 1, trial=item)]
    attempt = TrialAttempt("family-1", item.trial_id, "attempt-1", 1)
    active = [*with_trial, StartAttempt("event-2", "family-1", 2, attempt=attempt)]
    finished = [*active, FinishAttempt("event-3", "family-1", 3, attempt_id="attempt-1", state=AttemptState.FAILED, terminal_reason="fixture")]
    terminal = [*finished, FinalizeTrial("event-4", "family-1", 4, trial_id=item.trial_id, state=TrialState.FAILED, terminal_reason="fixture")]
    sealed = [*terminal, RequestSeal("event-5", "family-1", 5)]
    foreign_trial = replace(item, family_id="family-foreign")
    foreign_attempt = replace(attempt, family_id="family-foreign", attempt_id="attempt-foreign")
    foreign_selection = TrialSelection("family-foreign", item.trial_id, "selection-foreign", 5, SelectionDecision.SELECTED, "foreign")
    cases = {
        "DeclareFamily": ([DeclareFamily("identity", "family-1", 0, spec=replace(authoritative, objective_ref="objective:drift"))], LineageBlockedCode.EVENT_IDENTITY_CONFLICT.value, 0),
        "DeclareTrial": ([*declared, DeclareTrial("identity", "family-1", 1, trial=foreign_trial)], LineageBlockedCode.FAMILY_IDENTITY_MISMATCH.value, 0),
        "StartAttempt": ([*with_trial, StartAttempt("identity", "family-1", 2, attempt=foreign_attempt)], LineageBlockedCode.FAMILY_IDENTITY_MISMATCH.value, 1),
        "FinishAttempt": ([*active, FinishAttempt("identity", "family-1", 3, attempt_id="attempt-missing", state=AttemptState.FAILED, terminal_reason="missing")], LineageBlockedCode.ORPHAN_ATTEMPT.value, 1),
        "FinalizeTrial": ([*with_trial, FinalizeTrial("identity", "family-1", 2, trial_id="trial-missing", state=TrialState.FAILED, terminal_reason="missing")], LineageBlockedCode.ORPHAN_TRIAL.value, 1),
        "RecordSelection": ([*terminal, RecordSelection("identity", "family-1", 5, selection=foreign_selection)], LineageBlockedCode.FAMILY_IDENTITY_MISMATCH.value, 1),
        "RequestSeal": ([*terminal, RequestSeal("identity", "family-1", 5, prior_head_ref="unexpected-v0", prior_head_hash="unexpected-hash")], LineageBlockedCode.SUPERSESSION_VERSION_INVALID.value, 1),
        "AppendCorrection": ([*sealed, AppendCorrection("identity", "family-1", 6, corrects_event_id="event-missing", reason="missing", correction={"note": "invalid ref"})], LineageBlockedCode.EVENT_IDENTITY_CONFLICT.value, 1),
        "RequestSupersedingSeal": ([*terminal, RequestSupersedingSeal("identity", "family-1", 5, manifest_version=2, prior_head_ref="manifest-v1", prior_head_hash="hash-v1", reason="without sealed prior state")], LineageBlockedCode.ILLEGAL_FAMILY_TRANSITION.value, 1),
    }
    return authoritative, cases[command_name]


@pytest.mark.parametrize("command_name", [command.__name__ for command in TYPED_LINEAGE_COMMANDS])
def test_all_nine_commands_have_complete_nested_identity_fail_closed_matrix(command_name) -> None:
    authoritative, (commands, expected, raw_count) = _all_command_identity_case(command_name)
    result = fold_family_lineage(authoritative, commands)
    assert expected in result.blocked_reasons
    assert result.raw_trial_count == raw_count


def test_superseding_seal_nested_manifest_identity_requires_complete_prior_head() -> None:
    with pytest.raises(ValueError, match="prior_head_ref"):
        RequestSupersedingSeal("identity", "family-1", 6, manifest_version=2, prior_head_ref="", prior_head_hash="hash-v1", reason="missing ref")
    with pytest.raises(ValueError, match="prior_head_hash"):
        RequestSupersedingSeal("identity", "family-1", 6, manifest_version=2, prior_head_ref="manifest-v1", prior_head_hash="", reason="missing hash")
