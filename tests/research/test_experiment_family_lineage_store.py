from __future__ import annotations

from dataclasses import replace
from decimal import Decimal
import hashlib
import inspect
import json
import math
import multiprocessing
import os
import platform
from pathlib import Path
import threading
import time
import tracemalloc

import pytest

from engine.experiment_family_lineage import (
    AppendCorrection,
    AttemptState,
    DeclareTrial,
    ExperimentFamilySpec,
    ExperimentTrial,
    FinalizeTrial,
    FinishAttempt,
    RequestSeal,
    RequestSupersedingSeal,
    StartAttempt,
    TrialAttempt,
    TrialState,
    ValidationStatus,
    derive_stable_trial_id,
)
from engine.experiment_family_lineage_store import (
    LineageStoreError,
    LocalFamilyLineageRecorder,
    build_seal_envelope,
    canonical_json_bytes,
    canonical_jsonl_line,
    compute_family_seal_hash,
    load_family_artifacts,
    resolve_family_head,
    verify_immutable_artifact,
)


def spec(family_id: str = "family-1", **metadata) -> ExperimentFamilySpec:
    return ExperimentFamilySpec(1, family_id, "producer-1", 0, "objective:1", "space:1", metadata=metadata)


def terminal_commands(family_id: str = "family-1"):
    family_spec = spec(family_id, a=1, b=[2])
    trial_id = derive_stable_trial_id(family_id, {"alpha": 0.1}, 7)
    trial = ExperimentTrial(family_id, trial_id, {"alpha": 0.1}, 7, 1)
    attempt = TrialAttempt(family_id, trial_id, "attempt-1", 1)
    return family_spec, trial, [
        DeclareTrial("event-1", family_id, 1, trial=trial),
        StartAttempt("event-2", family_id, 2, attempt=attempt),
        FinishAttempt("event-3", family_id, 3, attempt_id="attempt-1", state=AttemptState.FAILED, terminal_reason="fixture"),
        FinalizeTrial("event-4", family_id, 4, trial_id=trial_id, state=TrialState.FAILED, terminal_reason="fixture"),
        RequestSeal("event-5", family_id, 5, manifest_version=1),
    ]


def sealed_family(root: Path, family_id: str = "family-1"):
    family_spec, trial, commands = terminal_commands(family_id)
    recorder, declaration = LocalFamilyLineageRecorder.open(root, family_spec)
    assert declaration.accepted
    for command in commands:
        assert recorder.submit(command).accepted
    return recorder, trial, recorder.seal(1)


def _cross_process_writer(root: str, family_id: str, writer_index: int, barrier, results) -> None:
    import time as worker_time

    barrier.wait()
    try:
        family_spec = spec(family_id)
        command = AppendCorrection(f"writer-{writer_index}", family_id, 1, corrects_event_id=f"declare-family:{family_id}", reason="writer", correction={"writer": writer_index})
        recorder, _ = LocalFamilyLineageRecorder.open(root, family_spec)
        receipt = recorder.submit(command)
        results.put(("accepted" if receipt.accepted else "blocked", receipt.blocked_reasons))
        worker_time.sleep(0.4)
        recorder.close()
    except LineageStoreError as error:
        results.put(("blocked", error.reasons))


def test_restricted_canonical_json_golden_and_rejections() -> None:
    assert canonical_json_bytes({"z": -0.0, "é": [Decimal("1.2300"), 2.0], "a": True}) == '{"a":true,"z":0,"é":[1.23,2]}'.encode()
    with pytest.raises(ValueError):
        canonical_json_bytes(float("nan"))
    with pytest.raises(ValueError):
        canonical_json_bytes(Decimal("Infinity"))
    with pytest.raises(TypeError):
        canonical_json_bytes({1: "bad"})
    with pytest.raises(TypeError):
        canonical_json_bytes({1, 2})


def test_create_only_spec_append_idempotency_and_conflict(tmp_path: Path) -> None:
    recorder, receipt = LocalFamilyLineageRecorder.open(tmp_path, spec())
    assert receipt.accepted
    line_count = recorder.events_path.read_bytes().count(b"\n")
    again = recorder.submit(recorder._commands[0])
    assert again.accepted and again.idempotent
    assert recorder.events_path.read_bytes().count(b"\n") == line_count
    conflict = replace(recorder._commands[0], spec=spec(changed=True))
    blocked = recorder.submit(conflict)
    assert not blocked.accepted and blocked.blocked_reasons == ("event_identity_conflict",)
    original = recorder.spec_path.read_bytes()
    with pytest.raises(LineageStoreError):
        LocalFamilyLineageRecorder.open(tmp_path, spec(changed=True))
    assert recorder.spec_path.read_bytes() == original


def test_append_is_canonical_one_line_and_rebuilds_receipts(tmp_path: Path) -> None:
    family_spec, _, commands = terminal_commands()
    recorder, _ = LocalFamilyLineageRecorder.open(tmp_path, family_spec)
    assert recorder.submit(commands[0]).accepted
    assert recorder.events_path.read_bytes().splitlines(keepends=True)[-1] == canonical_jsonl_line(commands[0])
    reopened, _ = LocalFamilyLineageRecorder.open(tmp_path, family_spec)
    before = reopened.events_path.stat().st_size
    assert reopened.submit(commands[0]).idempotent
    assert reopened.events_path.stat().st_size == before


def test_deterministic_seal_ten_roots_and_hash_domain_exclusions(tmp_path: Path) -> None:
    hashes = set()
    for index in range(10):
        recorder, _, result = sealed_family(tmp_path / str(index))
        os.utime(recorder.spec_path, (index + 1, index + 1))
        hashes.add(result.manifest.seal_hash)
        assert "sealed_at" not in build_seal_envelope(recorder.spec, recorder._commands, 1)
    assert len(hashes) == 1
    family_spec, _, commands = terminal_commands()
    recorder, _ = LocalFamilyLineageRecorder.open(tmp_path / "domain", family_spec)
    all_commands = [*recorder._commands, *commands]
    baseline = compute_family_seal_hash(family_spec, all_commands, 1)
    assert baseline == compute_family_seal_hash(family_spec, all_commands, 1)
    assert baseline != compute_family_seal_hash(family_spec, all_commands, 2)
    assert baseline != compute_family_seal_hash(spec("family-1", changed=True), all_commands, 1)


def test_initial_seal_is_target_bound_create_exclusive_and_resolves(tmp_path: Path) -> None:
    _, _, result = sealed_family(tmp_path)
    assert result.validation.validation_status is ValidationStatus.PASS
    assert result.validation.target_ref == result.manifest_ref
    assert result.validation.target_hash == result.manifest.seal_hash
    before = (tmp_path / result.manifest_ref).read_bytes()
    head = resolve_family_head(tmp_path, "family-1")
    assert head.ref == result.manifest_ref and head.chain_refs == (result.manifest_ref,)
    assert verify_immutable_artifact(tmp_path, result.manifest_ref, before)
    with pytest.raises(LineageStoreError, match="immutable_version_conflict"):
        verify_immutable_artifact(tmp_path, result.manifest_ref, b"different")
    assert (tmp_path / result.manifest_ref).read_bytes() == before


def test_valid_supersession_preserves_and_replays_v1_prefix(tmp_path: Path) -> None:
    recorder, _, v1 = sealed_family(tmp_path)
    v1_bytes = (tmp_path / v1.manifest_ref).read_bytes()
    correction = AppendCorrection("event-6", "family-1", 6, corrects_event_id="event-4", reason="audit", correction={"note": "append only"})
    request = RequestSupersedingSeal("event-7", "family-1", 7, manifest_version=2, prior_head_ref=v1.manifest_ref, prior_head_hash=v1.manifest.seal_hash, reason="authorized correction")
    assert recorder.submit(correction).accepted and recorder.submit(request).accepted
    v2 = recorder.seal(2, (v1.manifest_ref, v1.manifest.seal_hash), "authorized correction")
    head = resolve_family_head(tmp_path, "family-1")
    assert head.ref == v2.manifest_ref and head.chain_refs == (v1.manifest_ref, v2.manifest_ref)
    assert v2.manifest.supersedes_ref == v1.manifest_ref
    assert v2.manifest.supersedes_hash == v1.manifest.seal_hash
    assert v2.manifest.supersession_reason == "authorized correction"
    assert (tmp_path / v1.manifest_ref).read_bytes() == v1_bytes
    artifacts = load_family_artifacts(tmp_path, "family-1")
    v1_prefix = artifacts.commands[:v1.manifest.sealed_event_count]
    assert compute_family_seal_hash(artifacts.spec, v1_prefix, 1) == v1.manifest.seal_hash


def test_supersession_rejects_wrong_prior_and_requires_correction(tmp_path: Path) -> None:
    recorder, _, v1 = sealed_family(tmp_path)
    request = RequestSupersedingSeal("event-6", "family-1", 6, manifest_version=2, prior_head_ref=v1.manifest_ref, prior_head_hash=v1.manifest.seal_hash, reason="reason")
    assert recorder.submit(request).accepted
    with pytest.raises(LineageStoreError, match="supersession_prior_missing"):
        recorder.seal(2, (v1.manifest_ref, v1.manifest.seal_hash), "reason")


@pytest.mark.parametrize("target", ["spec", "events", "manifest"])
def test_tamper_is_blocked_without_mutating_sealed_artifacts(tmp_path: Path, target: str) -> None:
    recorder, _, result = sealed_family(tmp_path)
    path = {"spec": recorder.spec_path, "events": recorder.events_path, "manifest": tmp_path / result.manifest_ref}[target]
    original = path.read_bytes()
    path.write_bytes(original + (b" " if target != "events" else b"{}\n"))
    with pytest.raises(LineageStoreError):
        resolve_family_head(tmp_path, "family-1")


def test_malformed_tail_is_retained_and_no_resume_or_repair_surface_exists(tmp_path: Path) -> None:
    family_spec = spec("old-family")
    recorder, _ = LocalFamilyLineageRecorder.open(tmp_path, family_spec)
    # Declaration plus 9,998 complete corrections = 9,999 valid commands;
    # the following bytes are the interrupted 10,000th command.
    for sequence in range(1, 9_999):
        assert recorder.submit(AppendCorrection(f"e-{sequence}", "old-family", sequence, corrects_event_id="declare-family:old-family", reason="synthetic", correction={"n": sequence})).accepted
    partial = b'{"command_type":"append_correction"'
    fd = os.open(recorder.events_path, os.O_WRONLY | os.O_APPEND)
    try:
        os.write(fd, partial)
        os.fsync(fd)
    finally:
        os.close(fd)
    size = recorder.events_path.stat().st_size
    with pytest.raises(LineageStoreError, match="canonical_bytes_mismatch"):
        LocalFamilyLineageRecorder.open(tmp_path, family_spec)
    assert recorder.events_path.stat().st_size == size
    assert "resume" not in inspect.signature(LocalFamilyLineageRecorder.open).parameters
    assert not any(hasattr(LocalFamilyLineageRecorder, name) for name in ("truncate", "repair", "resume"))
    new, receipt = LocalFamilyLineageRecorder.open(tmp_path, spec("new-family"))
    assert receipt.accepted and new.spec.family_id != recorder.spec.family_id
    assert len(new._commands) == 1


def test_manifest_raw_trial_count_mismatch_is_blocked(tmp_path: Path) -> None:
    _, _, result = sealed_family(tmp_path)
    path = tmp_path / result.manifest_ref
    manifest = json.loads(path.read_text())
    manifest["raw_trial_count"] += 1
    path.write_bytes(canonical_json_bytes(manifest))
    with pytest.raises(LineageStoreError, match="raw_trial_count_mismatch"):
        resolve_family_head(tmp_path, "family-1")


def test_broken_chain_fork_and_missing_validation_fail_closed(tmp_path: Path) -> None:
    recorder, _, v1 = sealed_family(tmp_path / "broken")
    validation_path = tmp_path / "broken" / v1.validation_ref
    validation_path.unlink()
    with pytest.raises(LineageStoreError, match="target_mismatch"):
        resolve_family_head(tmp_path / "broken", "family-1")

    recorder, _, v1 = sealed_family(tmp_path / "fork")
    correction = AppendCorrection("event-6", "family-1", 6, corrects_event_id="event-4", reason="audit", correction={"x": 1})
    request = RequestSupersedingSeal("event-7", "family-1", 7, manifest_version=2, prior_head_ref=v1.manifest_ref, prior_head_hash=v1.manifest.seal_hash, reason="r")
    recorder.submit(correction); recorder.submit(request)
    v2 = recorder.seal(2, (v1.manifest_ref, v1.manifest.seal_hash), "r")
    manifest_path = tmp_path / "fork" / v2.manifest_ref
    validation_path = tmp_path / "fork" / v2.validation_ref
    fork_manifest = json.loads(manifest_path.read_text())
    fork_manifest["manifest_version"] = 3
    fork_manifest["seal_hash"] = compute_family_seal_hash(recorder.spec, recorder._commands, 3, v1.manifest_ref, v1.manifest.seal_hash)
    fork_path = manifest_path.with_name("family-manifest-v0003.json")
    fork_path.write_bytes(canonical_json_bytes(fork_manifest))
    fork_validation = json.loads(validation_path.read_text())
    fork_ref = fork_path.relative_to(tmp_path / "fork").as_posix()
    fork_validation["target_ref"] = fork_ref
    fork_validation["target_hash"] = fork_manifest["seal_hash"]
    fork_validation_path = validation_path.with_name("family-manifest-v0003.validation.json")
    fork_validation_path.write_bytes(canonical_json_bytes(fork_validation))
    with pytest.raises(LineageStoreError):
        resolve_family_head(tmp_path / "fork", "family-1")


def test_full_graph_cycle_is_classified_before_untrusted_hashes(tmp_path: Path) -> None:
    _, _, v1 = sealed_family(tmp_path)
    first_path = tmp_path / v1.manifest_ref
    first = json.loads(first_path.read_text())
    second_ref = first_path.with_name("family-manifest-v0002.json").relative_to(tmp_path).as_posix()
    first["supersedes_ref"] = second_ref
    first["supersedes_hash"] = "untrusted-v2"
    first_path.write_bytes(canonical_json_bytes(first))
    second = dict(first)
    second["manifest_version"] = 2
    second["supersedes_ref"] = v1.manifest_ref
    second["supersedes_hash"] = "untrusted-v1"
    second["seal_hash"] = "untrusted-v2"
    (tmp_path / second_ref).write_bytes(canonical_json_bytes(second))
    with pytest.raises(LineageStoreError, match="supersession_cycle"):
        resolve_family_head(tmp_path, "family-1")


def test_path_traversal_absolute_separator_and_symlink_escape_blocked(tmp_path: Path) -> None:
    for family_id in ("../escape", "/absolute", "bad/name", ".."):
        with pytest.raises(LineageStoreError, match="invalid_identifier"):
            LocalFamilyLineageRecorder.open(tmp_path, spec(family_id))
    outside = tmp_path.parent / f"{tmp_path.name}-outside"
    outside.mkdir()
    (tmp_path / "linked").symlink_to(outside, target_is_directory=True)
    with pytest.raises(LineageStoreError):
        verify_immutable_artifact(tmp_path, "linked/escape.json", b"x")
    assert list(outside.iterdir()) == []


def test_qa_s02_001_family_symlink_is_rejected_before_any_child_mutation(tmp_path: Path) -> None:
    outside = tmp_path.parent / f"{tmp_path.name}-hostile-family-target"
    outside.mkdir()
    families = tmp_path / "families"
    families.mkdir()
    (families / "family-1").symlink_to(outside, target_is_directory=True)
    before = tuple(outside.iterdir())
    with pytest.raises(LineageStoreError, match="invalid_identifier"):
        LocalFamilyLineageRecorder.open(tmp_path, spec())
    assert tuple(outside.iterdir()) == before == ()


@pytest.mark.parametrize(
    "field,ledger_value,seal_value",
    [
        ("prior_head_ref", "WRONG-REF", None),
        ("prior_head_hash", "WRONG-HASH", None),
        ("reason", "ledger reason", "manifest reason"),
    ],
)
def test_qa_s02_002_superseding_request_is_bound_to_seal_arguments(tmp_path: Path, field: str, ledger_value: str, seal_value: str | None) -> None:
    recorder, _, v1 = sealed_family(tmp_path)
    recorder.submit(AppendCorrection("event-6", "family-1", 6, corrects_event_id="event-4", reason="audit", correction={"x": 1}))
    values = {
        "event_id": "event-7", "family_id": "family-1", "sequence": 7,
        "manifest_version": 2, "prior_head_ref": v1.manifest_ref,
        "prior_head_hash": v1.manifest.seal_hash, "reason": "manifest reason",
    }
    values[field] = ledger_value
    recorder.submit(RequestSupersedingSeal(**values))
    reason = seal_value or "manifest reason"
    with pytest.raises(LineageStoreError, match="target_mismatch"):
        recorder.seal(2, (v1.manifest_ref, v1.manifest.seal_hash), reason)
    assert not (tmp_path / f"families/family-1/manifests/family-manifest-v0002.json").exists()


def test_qa_s02_002_resolver_replays_request_reason_binding(tmp_path: Path) -> None:
    recorder, _, v1 = sealed_family(tmp_path)
    recorder.submit(AppendCorrection("event-6", "family-1", 6, corrects_event_id="event-4", reason="audit", correction={"x": 1}))
    recorder.submit(RequestSupersedingSeal("event-7", "family-1", 7, manifest_version=2, prior_head_ref=v1.manifest_ref, prior_head_hash=v1.manifest.seal_hash, reason="bound reason"))
    v2 = recorder.seal(2, (v1.manifest_ref, v1.manifest.seal_hash), "bound reason")
    path = tmp_path / v2.manifest_ref
    manifest = json.loads(path.read_text())
    manifest["supersession_reason"] = "contradictory reason"
    path.write_bytes(canonical_json_bytes(manifest))
    with pytest.raises(LineageStoreError, match="target_mismatch"):
        resolve_family_head(tmp_path, "family-1")


@pytest.mark.parametrize("round_number", range(3))
def test_qa_s02_003_cross_process_ownership_allows_exactly_one_writer(tmp_path: Path, round_number: int) -> None:
    family_id = f"family-{round_number}"
    family_spec = spec(family_id)
    setup, _ = LocalFamilyLineageRecorder.open(tmp_path, family_spec)
    setup.close()
    context = multiprocessing.get_context("spawn")
    barrier = context.Barrier(2)
    results = context.Queue()
    processes = [context.Process(target=_cross_process_writer, args=(str(tmp_path), family_id, index, barrier, results)) for index in range(2)]
    for process in processes:
        process.start()
    observed = [results.get(timeout=10) for _ in processes]
    for process in processes:
        process.join(timeout=10)
        assert process.exitcode == 0
    assert [status for status, _ in observed].count("accepted") == 1
    assert [status for status, _ in observed].count("blocked") == 1
    assert any("writer_ownership_conflict" in reasons for status, reasons in observed if status == "blocked")
    reopened, _ = LocalFamilyLineageRecorder.open(tmp_path, family_spec)
    assert len(reopened._commands) == 2
    assert reopened._commands[1].sequence == 1
    reopened.close()


def test_qa_s02_004_short_write_latches_terminal_failure_and_retains_partial(tmp_path: Path, monkeypatch) -> None:
    recorder, _ = LocalFamilyLineageRecorder.open(tmp_path, spec())
    original_write = os.write

    def short_write(fd, payload):
        original_write(fd, payload[:7])
        return 7

    monkeypatch.setattr(os, "write", short_write)
    first = recorder.submit(AppendCorrection("short", "family-1", 1, corrects_event_id="declare-family:family-1", reason="short", correction={}))
    assert first.blocked_reasons == ("short_event_write",)
    size = recorder.events_path.stat().st_size
    second = recorder.submit(AppendCorrection("later", "family-1", 2, corrects_event_id="declare-family:family-1", reason="later", correction={}))
    assert second.blocked_reasons == first.blocked_reasons
    assert recorder.events_path.stat().st_size == size
    with pytest.raises(LineageStoreError, match="short_event_write"):
        recorder.seal(1)
    recorder.close()
    monkeypatch.setattr(os, "write", original_write)
    with pytest.raises(LineageStoreError, match="canonical_bytes_mismatch"):
        LocalFamilyLineageRecorder.open(tmp_path, spec())
    fresh, receipt = LocalFamilyLineageRecorder.open(tmp_path, spec("fresh-family"))
    assert receipt.accepted
    fresh.close()


def test_qa_s02_004_oserror_latches_terminal_failure(tmp_path: Path, monkeypatch) -> None:
    recorder, _ = LocalFamilyLineageRecorder.open(tmp_path, spec())

    def failed_write(fd, payload):
        raise OSError("synthetic append failure")

    monkeypatch.setattr(os, "write", failed_write)
    first = recorder.submit(AppendCorrection("failed", "family-1", 1, corrects_event_id="declare-family:family-1", reason="failed", correction={}))
    assert first.blocked_reasons == ("event_append_failed",)
    second = recorder.submit(AppendCorrection("later", "family-1", 2, corrects_event_id="declare-family:family-1", reason="later", correction={}))
    assert second.blocked_reasons == first.blocked_reasons
    with pytest.raises(LineageStoreError, match="event_append_failed"):
        recorder.seal(1)


def test_qa_s02_005_two_handles_replay_same_event_idempotently(tmp_path: Path) -> None:
    first, _ = LocalFamilyLineageRecorder.open(tmp_path, spec())
    second, declaration = LocalFamilyLineageRecorder.open(tmp_path, spec())
    assert declaration.idempotent
    command = AppendCorrection("shared-event", "family-1", 1, corrects_event_id="declare-family:family-1", reason="shared", correction={"value": 1})
    accepted = first.submit(command)
    replayed = second.submit(command)
    assert accepted.accepted and not accepted.idempotent
    assert replayed.accepted and replayed.idempotent
    assert first._commands is second._commands
    assert first.events_path.read_bytes().count(b"\n") == 2
    first.close(); second.close()


def test_qa_s02_005_two_handles_block_conflicting_event_with_one_ledger_fact(tmp_path: Path) -> None:
    first, _ = LocalFamilyLineageRecorder.open(tmp_path, spec())
    second, _ = LocalFamilyLineageRecorder.open(tmp_path, spec())
    original = AppendCorrection("shared-event", "family-1", 1, corrects_event_id="declare-family:family-1", reason="original", correction={"value": 1})
    conflict = AppendCorrection("shared-event", "family-1", 1, corrects_event_id="declare-family:family-1", reason="conflict", correction={"value": 2})
    assert first.submit(original).accepted
    blocked = second.submit(conflict)
    assert not blocked.accepted and blocked.blocked_reasons == ("event_identity_conflict",)
    lines = first.events_path.read_bytes().splitlines()
    assert len(lines) == 2
    assert json.loads(lines[-1])["reason"] == "original"
    first.close(); second.close()


def test_qa_s02_005_two_handles_serialize_distinct_events_without_deadlock(tmp_path: Path) -> None:
    first, _ = LocalFamilyLineageRecorder.open(tmp_path, spec())
    second, _ = LocalFamilyLineageRecorder.open(tmp_path, spec())
    first_done = threading.Event()
    receipts = []

    def submit_first():
        receipts.append(first.submit(AppendCorrection("event-a", "family-1", 1, corrects_event_id="declare-family:family-1", reason="a", correction={})))
        first_done.set()

    def submit_second():
        assert first_done.wait(timeout=2)
        receipts.append(second.submit(AppendCorrection("event-b", "family-1", 2, corrects_event_id="event-a", reason="b", correction={})))

    threads = [threading.Thread(target=submit_first), threading.Thread(target=submit_second)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=3)
        assert not thread.is_alive()
    assert len(receipts) == 2 and all(receipt.accepted for receipt in receipts)
    commands = load_family_artifacts(tmp_path, "family-1").commands
    assert [command.event_id for command in commands] == ["declare-family:family-1", "event-a", "event-b"]
    first.close(); second.close()


def test_qa_s02_005_close_reopen_rebuild_has_no_ownership_or_index_leak(tmp_path: Path) -> None:
    first, _ = LocalFamilyLineageRecorder.open(tmp_path, spec())
    second, _ = LocalFamilyLineageRecorder.open(tmp_path, spec())
    assert first.submit(AppendCorrection("event-a", "family-1", 1, corrects_event_id="declare-family:family-1", reason="a", correction={})).accepted
    first.close()
    assert first.submit(AppendCorrection("closed", "family-1", 2, corrects_event_id="event-a", reason="closed", correction={})).blocked_reasons == ("recorder_closed",)
    assert second.submit(AppendCorrection("event-b", "family-1", 2, corrects_event_id="event-a", reason="b", correction={})).accepted
    second.close()
    rebuilt, declaration = LocalFamilyLineageRecorder.open(tmp_path, spec())
    assert declaration.idempotent
    assert [command.event_id for command in rebuilt._commands] == ["declare-family:family-1", "event-a", "event-b"]
    rebuilt.close()
    reopened, _ = LocalFamilyLineageRecorder.open(tmp_path, spec())
    assert len(reopened._commands) == 3
    reopened.close()


def test_10k_characterization_records_four_metrics_without_threshold(tmp_path: Path, record_property) -> None:
    family_spec = spec("characterization", fixture="deterministic-v1")
    recorder, _ = LocalFamilyLineageRecorder.open(tmp_path, family_spec)
    trial_id = derive_stable_trial_id("characterization", {"alpha": 1}, 1)
    trial = ExperimentTrial("characterization", trial_id, {"alpha": 1}, 1, 1)
    attempt = TrialAttempt("characterization", trial_id, "attempt-1", 1)
    prefix = [
        DeclareTrial("event-00001", "characterization", 1, trial=trial),
        StartAttempt("event-00002", "characterization", 2, attempt=attempt),
        FinishAttempt("event-00003", "characterization", 3, attempt_id="attempt-1", state=AttemptState.FAILED, terminal_reason="synthetic"),
        FinalizeTrial("event-00004", "characterization", 4, trial_id=trial_id, state=TrialState.FAILED, terminal_reason="synthetic"),
    ]
    for command in prefix:
        assert recorder.submit(command).accepted
    for sequence in range(5, 9_999):
        receipt = recorder.submit(AppendCorrection(f"event-{sequence:05d}", "characterization", sequence, corrects_event_id="event-00004", reason="synthetic", correction={"ordinal": sequence, "bucket": sequence % 17}))
        assert receipt.accepted
    recorder.submit(RequestSeal("event-09999", "characterization", 9_999, manifest_version=1))
    assert len(recorder._commands) == 10_000
    fixture_hash = hashlib.sha256(recorder.events_path.read_bytes()).hexdigest()
    tracemalloc.start()
    opened = time.perf_counter()
    rebuilt, _ = LocalFamilyLineageRecorder.open(tmp_path, family_spec)
    open_rebuild_elapsed_seconds = time.perf_counter() - opened
    sealing = time.perf_counter()
    result = rebuilt.seal(1)
    seal_elapsed_seconds = time.perf_counter() - sealing
    _, peak_tracemalloc_bytes = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    manifest_bytes = (tmp_path / result.manifest_ref).stat().st_size
    metrics = {
        "open_rebuild_elapsed_seconds": open_rebuild_elapsed_seconds,
        "seal_elapsed_seconds": seal_elapsed_seconds,
        "peak_tracemalloc_bytes": peak_tracemalloc_bytes,
        "manifest_bytes": manifest_bytes,
    }
    assert len(metrics) == 4
    assert all(isinstance(value, (int, float)) and math.isfinite(value) and value >= 0 for value in metrics.values())
    record_property("characterization_metrics", json.dumps(metrics, sort_keys=True))
    record_property("environment", json.dumps({"python": platform.python_version(), "os": platform.platform(), "cpu": platform.processor(), "fixture_hash": fixture_hash}, sort_keys=True))
    # Observations only: deliberately no capacity, latency, memory, or size threshold.


def test_module_has_no_external_runtime_or_data_imports() -> None:
    source = inspect.getsource(inspect.getmodule(LocalFamilyLineageRecorder))
    for forbidden in ("requests", "boto", "credential", "data_lake", "nas", "mature_multifactor_research", "strategy_admission"):
        assert f"import {forbidden}" not in source and f"from {forbidden}" not in source
