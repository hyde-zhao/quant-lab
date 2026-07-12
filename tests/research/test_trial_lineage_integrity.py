from __future__ import annotations

import ast
from dataclasses import replace
import json
from pathlib import Path

import pytest

from engine.experiment_family_lineage import (
    AppendCorrection,
    AttemptState,
    DeclareFamily,
    DeclareTrial,
    ExperimentFamilyManifest,
    ExperimentFamilySpec,
    ExperimentTrial,
    FamilyEvidenceProjection,
    FinalizeTrial,
    FinishAttempt,
    LineageAvailability,
    RecordSelection,
    RequestSeal,
    RequestSupersedingSeal,
    SelectionDecision,
    StartAttempt,
    TrialAttempt,
    TrialSelection,
    TrialState,
    ValidationStatus,
    derive_stable_trial_id,
    fold_family_lineage,
    project_family_evidence,
    unavailable_family_lineage,
    validate_family_lineage,
)
from engine.experiment_family_lineage_store import (
    LineageStoreError,
    LocalFamilyLineageRecorder,
    canonical_json_bytes,
    resolve_family_head,
)
from engine.mature_multifactor_research import PRODUCER_LINEAGE_MAPPING_INVENTORY
from engine.strategy_admission_package import attach_family_lineage_to_admission_package
from engine.strategy_admission_statistical_gate import consume_family_lineage_projection


REQUIREMENTS = frozenset(f"REQ-CR163-{index:03d}" for index in range(1, 9))
SCENARIO_TRACE = (
    {"scenario_id": "P01", "requirements": ("REQ-CR163-001", "REQ-CR163-005"), "feature_scope": ("FEAT-20", "FEAT-21"), "test_function": "tests/research/test_trial_lineage_integrity.py::test_p01_trace_and_producer_inventory_are_exact"},
    {"scenario_id": "P02", "requirements": ("REQ-CR163-002", "REQ-CR163-003"), "feature_scope": ("FEAT-20", "FEAT-21"), "test_function": "tests/research/test_trial_lineage_integrity.py::test_p02_two_seeds_retries_and_terminal_membership"},
    {"scenario_id": "P03", "requirements": ("REQ-CR163-004", "REQ-CR163-006"), "feature_scope": ("FEAT-20", "FEAT-22"), "test_function": "tests/research/test_trial_lineage_integrity.py::test_p03_ten_identical_seals_and_valid_claim_ceiling"},
    {"scenario_id": "N01", "requirements": ("REQ-CR163-001", "REQ-CR163-007"), "feature_scope": ("FEAT-20", "FEAT-21", "FEAT-22"), "test_function": "tests/research/test_trial_lineage_integrity.py::test_n01_absent_is_typed_unavailable_and_incomplete_is_blocked"},
    {"scenario_id": "N02", "requirements": ("REQ-CR163-002", "REQ-CR163-007"), "feature_scope": ("FEAT-20", "FEAT-21"), "test_function": "tests/research/test_trial_lineage_integrity.py::test_n02_orphan_attempt_is_blocked"},
    {"scenario_id": "B01", "requirements": ("REQ-CR163-003", "REQ-CR163-007"), "feature_scope": ("FEAT-20", "FEAT-21"), "test_function": "tests/research/test_trial_lineage_integrity.py::test_b01_declared_and_recomputed_count_mismatch_is_blocked"},
    {"scenario_id": "B02", "requirements": ("REQ-CR163-006",), "feature_scope": ("FEAT-20", "FEAT-22"), "test_function": "tests/research/test_trial_lineage_integrity.py::test_b02_absent_invalid_and_manual_mismatch_never_overclaim"},
    {"scenario_id": "F01", "requirements": ("REQ-CR163-002", "REQ-CR163-003"), "feature_scope": ("FEAT-20", "FEAT-21"), "test_function": "tests/research/test_trial_lineage_integrity.py::test_f01_terminal_classes_are_retained"},
    {"scenario_id": "R01", "requirements": ("REQ-CR163-004", "REQ-CR163-007"), "feature_scope": ("FEAT-20",), "test_function": "tests/research/test_trial_lineage_integrity.py::test_r01_supersession_recovery_and_invalid_chains"},
    {"scenario_id": "T01", "requirements": ("REQ-CR163-004", "REQ-CR163-006", "REQ-CR163-007"), "feature_scope": ("FEAT-20", "FEAT-22"), "test_function": "tests/research/test_trial_lineage_integrity.py::test_t01_five_negative_classes_are_target_bound_and_blocked"},
    {"scenario_id": "A01", "requirements": ("REQ-CR163-008",), "feature_scope": ("FEAT-20", "FEAT-21", "FEAT-22", "FEAT-23"), "test_function": "tests/research/test_trial_lineage_authorization.py::test_synthetic_s01_s05_public_path_runs_under_thirteen_zero_sentinels"},
    {"scenario_id": "G01", "requirements": ("REQ-CR163-006", "REQ-CR163-008"), "feature_scope": ("FEAT-22", "FEAT-23"), "test_function": "tests/research/test_trial_lineage_legacy_admission_regression.py::test_actual_and_synthetic_cr155_without_native_ledger_stay_blocked"},
)
CPI_IDS = frozenset(f"CPI-CR163-{index:03d}" for index in range(1, 5))
CHAIN_IDS = frozenset(("public_stage3", "legacy_cr039"))


def _spec(family_id: str = "family-cr163", *, reversed_metadata: bool = False) -> ExperimentFamilySpec:
    items = (("objective", "synthetic"), ("fixture", True))
    metadata = dict(reversed(items) if reversed_metadata else items)
    return ExperimentFamilySpec(
        1, family_id, "public_stage3", 0, "objective:synthetic", "space:synthetic", metadata=metadata
    )


def _trial(family_id: str, seed: int, suffix: str) -> ExperimentTrial:
    parameters = {"lookback": 20, "candidate": suffix}
    return ExperimentTrial(
        family_id,
        derive_stable_trial_id(family_id, parameters, seed),
        parameters,
        seed,
        1,
    )


def _terminal_commands(
    family_id: str = "family-cr163", *, reversed_metadata: bool = False
) -> tuple[ExperimentFamilySpec, ExperimentTrial, list[object]]:
    spec = _spec(family_id, reversed_metadata=reversed_metadata)
    trial = _trial(family_id, 7, "alpha")
    attempt = TrialAttempt(family_id, trial.trial_id, "attempt-1", 1)
    return spec, trial, [
        DeclareTrial("event-1", family_id, 1, trial=trial),
        StartAttempt("event-2", family_id, 2, attempt=attempt),
        FinishAttempt(
            "event-3", family_id, 3, attempt_id=attempt.attempt_id,
            state=AttemptState.FAILED, terminal_reason="synthetic retry stopped",
        ),
        FinalizeTrial(
            "event-4", family_id, 4, trial_id=trial.trial_id,
            state=TrialState.FAILED, terminal_reason="synthetic terminal",
        ),
        RequestSeal("event-5", family_id, 5, manifest_version=1),
    ]


def _sealed(root: Path, family_id: str = "family-cr163", *, reversed_metadata: bool = False):
    spec, trial, commands = _terminal_commands(family_id, reversed_metadata=reversed_metadata)
    recorder, declaration = LocalFamilyLineageRecorder.open(root, spec)
    assert declaration.accepted
    for command in commands:
        assert recorder.submit(command).accepted
    return recorder, trial, recorder.seal(1)


def _manifest(spec: ExperimentFamilySpec, commands: list[object], raw_count: int) -> ExperimentFamilyManifest:
    fold = fold_family_lineage(spec, commands)
    return ExperimentFamilyManifest(
        1, spec.family_id, 1, "fixture://spec", "fixture://events",
        len(commands), fold.last_sequence, raw_count, fold.trial_ids, seal_hash="sha256:fixture",
    )


def _blocked_projection(reason: str) -> FamilyEvidenceProjection:
    return FamilyEvidenceProjection(
        availability=LineageAvailability.BLOCKED,
        target_ref="fixture://blocked",
        target_hash="sha256:blocked",
        blocked_reasons=(reason,),
    )


def _validate_scenario_trace(trace: tuple[dict[str, object], ...]) -> None:
    required_fields = {"scenario_id", "requirements", "feature_scope", "test_function"}
    assert len(trace) == 12
    assert all(set(item) == required_fields for item in trace)
    scenario_ids = [str(item["scenario_id"]) for item in trace]
    test_functions = [str(item["test_function"]) for item in trace]
    assert len(set(scenario_ids)) == len(scenario_ids)
    assert len(set(test_functions)) == len(test_functions)
    assert set().union(*(set(item["requirements"]) for item in trace)) == REQUIREMENTS
    for item in trace:
        assert item["feature_scope"]
        path_text, function_name = str(item["test_function"]).split("::", 1)
        path = Path(path_text)
        assert path.is_file(), f"scenario_test_file_missing:{path_text}"
        functions = {
            node.name for node in ast.parse(path.read_text(encoding="utf-8")).body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        }
        assert function_name in functions, f"scenario_test_function_missing:{item['test_function']}"


def test_p01_trace_and_producer_inventory_are_exact() -> None:
    _validate_scenario_trace(SCENARIO_TRACE)
    assert len(SCENARIO_TRACE) == 12
    assert {item["scenario_id"] for item in SCENARIO_TRACE} == {
        "P01", "P02", "P03", "N01", "N02", "B01", "B02", "F01", "R01", "T01", "A01", "G01"
    }
    assert len(REQUIREMENTS) == 8
    assert set(PRODUCER_LINEAGE_MAPPING_INVENTORY) == CPI_IDS
    assert {mapping[0] for mapping in PRODUCER_LINEAGE_MAPPING_INVENTORY.values()} == CHAIN_IDS
    assert len(PRODUCER_LINEAGE_MAPPING_INVENTORY) == 4
    assert len(CHAIN_IDS) == 2


def test_trace_wrong_or_deleted_function_reference_fails_closed() -> None:
    malformed = tuple(
        {**item, "test_function": "tests/research/test_trial_lineage_integrity.py::deleted_test"}
        if item["scenario_id"] == "P01" else item
        for item in SCENARIO_TRACE
    )
    with pytest.raises(AssertionError, match="scenario_test_function_missing"):
        _validate_scenario_trace(malformed)


def test_p02_two_seeds_retries_and_terminal_membership() -> None:
    family_id = "family-counts"
    spec = _spec(family_id)
    commands: list[object] = [DeclareFamily("event-0", family_id, 0, spec=spec)]
    sequence = 1
    terminals = (TrialState.FAILED, TrialState.CANCELLED, TrialState.EXCLUDED, TrialState.NEVER_STARTED)
    trials = [_trial(family_id, index, terminal.value) for index, terminal in enumerate(terminals, 1)]
    for trial, terminal in zip(trials, terminals):
        commands.append(DeclareTrial(f"event-{sequence}", family_id, sequence, trial=trial)); sequence += 1
        if terminal in (TrialState.FAILED, TrialState.CANCELLED):
            for ordinal in range(1, 2):
                attempt = TrialAttempt(family_id, trial.trial_id, f"{trial.trial_id}-attempt-{ordinal}", ordinal)
                commands.append(StartAttempt(f"event-{sequence}", family_id, sequence, attempt=attempt)); sequence += 1
                commands.append(FinishAttempt(
                    f"event-{sequence}", family_id, sequence, attempt_id=attempt.attempt_id,
                    state=(AttemptState.CANCELLED if terminal is TrialState.CANCELLED else AttemptState.FAILED),
                    terminal_reason="synthetic retry",
                )); sequence += 1
        commands.append(FinalizeTrial(
            f"event-{sequence}", family_id, sequence, trial_id=trial.trial_id,
            state=terminal, terminal_reason="synthetic terminal",
        )); sequence += 1
    fold = fold_family_lineage(spec, commands)
    assert not fold.blocked_reasons
    assert fold.raw_trial_count == len(trials) == 4
    assert len(fold.trial_ids) == 4
    retry_trial = _trial(family_id, 99, "retry")
    retry_commands: list[object] = [
        DeclareFamily("retry-0", family_id, 0, spec=spec),
        DeclareTrial("retry-1", family_id, 1, trial=retry_trial),
    ]
    for ordinal in range(1, 4):
        attempt = TrialAttempt(family_id, retry_trial.trial_id, f"retry-attempt-{ordinal}", ordinal)
        retry_commands.extend((
            StartAttempt(f"retry-start-{ordinal}", family_id, ordinal * 2, attempt=attempt),
            FinishAttempt(
                f"retry-finish-{ordinal}", family_id, ordinal * 2 + 1,
                attempt_id=attempt.attempt_id, state=AttemptState.FAILED,
                terminal_reason="synthetic retry",
            ),
        ))
    assert fold_family_lineage(spec, retry_commands).raw_trial_count == 1
    assert derive_stable_trial_id(family_id, {"candidate": "same"}, 1) != derive_stable_trial_id(
        family_id, {"candidate": "same"}, 2
    )


def test_p03_ten_identical_seals_and_valid_claim_ceiling(
    tmp_path: Path,
) -> None:
    hashes: set[str] = set()
    projections = []
    for index in range(10):
        recorder, _, sealed = _sealed(tmp_path / str(index), reversed_metadata=bool(index % 2))
        hashes.add(sealed.manifest.seal_hash)
        projection = project_family_evidence(sealed.manifest, sealed.validation)
        projections.append(projection)
        assert sealed.validation.target_ref == sealed.manifest_ref
        assert sealed.validation.target_hash == sealed.manifest.seal_hash
        recorder.close()
    assert len(hashes) == 1
    assert all(item.effective_trial_count_availability is LineageAvailability.TYPED_UNAVAILABLE for item in projections)
    assert all(item.effective_trial_count is None for item in projections)
    assert all(item.effective_ref == item.effective_method == "" for item in projections)
    assert sum(item.raw_trial_count is not None for item in projections) == 10


def test_r01_supersession_recovery_and_invalid_chains(tmp_path: Path) -> None:
    recorder, _, v1 = _sealed(tmp_path / "valid")
    v1_path = tmp_path / "valid" / v1.manifest_ref
    v1_bytes = v1_path.read_bytes()
    correction = AppendCorrection(
        "event-6", recorder.spec.family_id, 6, corrects_event_id="event-4",
        reason="synthetic correction", correction={"note": "append only"},
    )
    request = RequestSupersedingSeal(
        "event-7", recorder.spec.family_id, 7, manifest_version=2,
        prior_head_ref=v1.manifest_ref, prior_head_hash=v1.manifest.seal_hash,
        reason="authorized synthetic correction",
    )
    assert recorder.submit(correction).accepted
    assert recorder.submit(request).accepted
    v2 = recorder.seal(2, (v1.manifest_ref, v1.manifest.seal_hash), request.reason)
    head = resolve_family_head(tmp_path / "valid", recorder.spec.family_id)
    assert head.ref == v2.manifest_ref
    assert head.chain_refs == (v1.manifest_ref, v2.manifest_ref)
    assert v2.manifest.supersedes_ref == v1.manifest_ref
    assert v2.manifest.supersedes_hash == v1.manifest.seal_hash
    assert v1_path.read_bytes() == v1_bytes
    recorder.close()

    _, _, broken = _sealed(tmp_path / "broken", "broken-family")
    (tmp_path / "broken" / broken.validation_ref).unlink()
    with pytest.raises(LineageStoreError):
        resolve_family_head(tmp_path / "broken", "broken-family")

    _, _, cyclic = _sealed(tmp_path / "cyclic", "cyclic-family")
    first_path = tmp_path / "cyclic" / cyclic.manifest_ref
    first = json.loads(first_path.read_text(encoding="utf-8"))
    second_ref = first_path.with_name("family-manifest-v0002.json").relative_to(tmp_path / "cyclic").as_posix()
    first.update(supersedes_ref=second_ref, supersedes_hash="untrusted-v2")
    first_path.write_bytes(canonical_json_bytes(first))
    second = dict(first, manifest_version=2, supersedes_ref=cyclic.manifest_ref, supersedes_hash="untrusted-v1", seal_hash="untrusted-v2")
    (tmp_path / "cyclic" / second_ref).write_bytes(canonical_json_bytes(second))
    with pytest.raises(LineageStoreError, match="supersession_cycle"):
        resolve_family_head(tmp_path / "cyclic", "cyclic-family")


def test_t01_five_negative_classes_are_target_bound_and_blocked(tmp_path: Path) -> None:
    spec, trial, valid_tail = _terminal_commands("negative-family")
    declaration = DeclareFamily("declare", spec.family_id, 0, spec=spec)

    incomplete_commands = [
        declaration,
        DeclareTrial("trial", spec.family_id, 1, trial=trial),
        RequestSeal("premature-seal", spec.family_id, 2, manifest_version=1),
    ]
    incomplete = validate_family_lineage(
        _manifest(spec, incomplete_commands, 1), spec, incomplete_commands,
        target_ref="fixture://incomplete", target_hash="sha256:fixture",
    )

    orphan_attempt = TrialAttempt(spec.family_id, trial.trial_id, "orphan", 1)
    orphan_commands = [declaration, StartAttempt("orphan", spec.family_id, 1, attempt=orphan_attempt)]
    orphan = validate_family_lineage(
        _manifest(spec, orphan_commands, 1), spec, orphan_commands,
        target_ref="fixture://orphan", target_hash="sha256:fixture",
    )

    valid_commands = [declaration, *valid_tail]
    count_mismatch = validate_family_lineage(
        _manifest(spec, valid_commands, 2), spec, valid_commands,
        target_ref="fixture://count", target_hash="sha256:fixture",
    )
    tampered = validate_family_lineage(
        _manifest(spec, valid_commands, 1), spec, valid_commands,
        target_ref="fixture://tamper", target_hash="sha256:not-the-seal",
    )

    _, _, broken = _sealed(tmp_path, "negative-broken")
    (tmp_path / broken.validation_ref).unlink()
    with pytest.raises(LineageStoreError) as caught:
        resolve_family_head(tmp_path, "negative-broken")

    negative = {
        "post_hoc_or_incomplete": incomplete.blocked_reasons,
        "identity_or_orphan_conflict": orphan.blocked_reasons,
        "count_mismatch": count_mismatch.blocked_reasons,
        "sealed_tamper": tampered.blocked_reasons,
        "broken_or_cyclic_supersession": caught.value.reasons,
    }
    assert len(negative) == 5
    assert all(reasons for reasons in negative.values())
    assert all(result.validation_status is ValidationStatus.BLOCKED for result in (incomplete, orphan, count_mismatch, tampered))
    assert incomplete.target_ref == "fixture://incomplete"
    assert orphan.target_ref == "fixture://orphan"
    assert count_mismatch.target_ref == "fixture://count"
    assert tampered.target_ref == "fixture://tamper"


def test_b02_absent_invalid_and_manual_mismatch_never_overclaim() -> None:
    absent = project_family_evidence(None, unavailable_family_lineage("not instrumented"))
    assert absent.availability is LineageAvailability.TYPED_UNAVAILABLE
    assert absent.raw_trial_count is None
    assert absent.effective_trial_count is None
    assert absent.effective_ref == absent.effective_method == ""
    assert consume_family_lineage_projection(_blocked_projection("manual_count_mismatch"))["availability"] == "blocked"

    package = {
        "admission_status": "blocked",
        "evidence_refs": (), "blocked_reasons": (), "limitations": (),
        "not_authorized_counters": {},
        "not_qmt_authorization": True, "not_simulation_authorization": True,
        "not_live_authorization": True, "not_broker_order": True,
    }
    attached = attach_family_lineage_to_admission_package(package, _blocked_projection("target_mismatch"))
    assert attached["admission_status"] == "blocked"
    assert attached["family_lineage_projection"]["raw_trial_count"] is None
    assert attached["family_lineage_projection"]["c1_input_status"] == "input_blocked"
    assert all(attached[field] is True for field in (
        "not_qmt_authorization", "not_simulation_authorization", "not_live_authorization", "not_broker_order"
    ))


def test_n01_absent_is_typed_unavailable_and_incomplete_is_blocked() -> None:
    absent = project_family_evidence(None, unavailable_family_lineage("not instrumented"))
    assert absent.availability is LineageAvailability.TYPED_UNAVAILABLE
    spec, trial, _ = _terminal_commands("n01-family")
    commands = [
        DeclareFamily("declare", spec.family_id, 0, spec=spec),
        DeclareTrial("trial", spec.family_id, 1, trial=trial),
        RequestSeal("premature", spec.family_id, 2, manifest_version=1),
    ]
    result = validate_family_lineage(
        _manifest(spec, commands, 1), spec, commands,
        target_ref="fixture://n01", target_hash="sha256:fixture",
    )
    assert result.validation_status is ValidationStatus.BLOCKED
    assert result.blocked_reasons


def test_n02_orphan_attempt_is_blocked() -> None:
    spec = _spec("n02-family")
    trial = _trial(spec.family_id, 7, "orphan")
    commands = [
        DeclareFamily("declare", spec.family_id, 0, spec=spec),
        StartAttempt(
            "orphan", spec.family_id, 1,
            attempt=TrialAttempt(spec.family_id, trial.trial_id, "attempt", 1),
        ),
    ]
    result = validate_family_lineage(
        _manifest(spec, commands, 1), spec, commands,
        target_ref="fixture://n02", target_hash="sha256:fixture",
    )
    assert result.validation_status is ValidationStatus.BLOCKED
    assert "orphan_attempt" in result.blocked_reasons


def test_b01_declared_and_recomputed_count_mismatch_is_blocked() -> None:
    spec, _, tail = _terminal_commands("b01-family")
    commands = [DeclareFamily("declare", spec.family_id, 0, spec=spec), *tail]
    result = validate_family_lineage(
        _manifest(spec, commands, 2), spec, commands,
        target_ref="fixture://b01", target_hash="sha256:fixture",
    )
    assert result.validation_status is ValidationStatus.BLOCKED
    assert "raw_trial_count_mismatch" in result.blocked_reasons


def test_f01_terminal_classes_are_retained() -> None:
    family_id = "f01-family"
    spec = _spec(family_id)
    commands: list[object] = [DeclareFamily("declare", family_id, 0, spec=spec)]
    for sequence, state in enumerate(
        (TrialState.FAILED, TrialState.CANCELLED, TrialState.EXCLUDED, TrialState.NEVER_STARTED), 1
    ):
        trial = _trial(family_id, sequence, state.value)
        commands.append(DeclareTrial(f"trial-{sequence}", family_id, sequence * 2 - 1, trial=trial))
        commands.append(FinalizeTrial(
            f"final-{sequence}", family_id, sequence * 2,
            trial_id=trial.trial_id, state=state, terminal_reason="synthetic terminal",
        ))
    fold = fold_family_lineage(spec, commands)
    assert fold.raw_trial_count == 4
    assert len(fold.trial_ids) == 4
