"""Append-only local storage and immutable seals for experiment-family lineage.

This first-slice store is intentionally local and single-writer.  A malformed
ledger is evidence, not a recovery point: it is never truncated or resumed.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
import errno
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import re
import threading
from typing import Any, Mapping, Sequence

from engine.experiment_family_lineage import (
    AppendCorrection,
    AttemptState,
    CommandReceipt,
    DeclareFamily,
    DeclareTrial,
    ExperimentFamilyManifest,
    ExperimentFamilySpec,
    ExperimentTrial,
    FamilyLineageValidationResult,
    FinalizeTrial,
    FinishAttempt,
    LineageAvailability,
    LineageBlockedCode,
    LineageCommand,
    RecordSelection,
    RequestSeal,
    RequestSupersedingSeal,
    SelectionDecision,
    StartAttempt,
    TrialAttempt,
    TrialSelection,
    TrialState,
    ValidationStatus,
    fold_family_lineage,
    validate_family_lineage,
)


SEAL_DOMAIN = "quant-lab.experiment-family-lineage.seal.v1"
MAX_EVENT_LINE_BYTES = 1024 * 1024
_FAMILY_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
_LOCKS: dict[str, threading.RLock] = {}
_LOCKS_GUARD = threading.Lock()
_PROCESS_OWNERS: dict[str, tuple[int, int, int]] = {}
_PROCESS_STATES: dict[str, "_ProcessFamilyState"] = {}


class LineageStoreError(RuntimeError):
    """A deterministic fail-closed storage result."""

    def __init__(self, *reasons: str):
        self.reasons = tuple(sorted(set(reasons))) or ("storage_error",)
        super().__init__(",".join(self.reasons))


@dataclass(frozen=True, slots=True)
class SealResult:
    manifest: ExperimentFamilyManifest
    validation: FamilyLineageValidationResult
    manifest_ref: str
    validation_ref: str


@dataclass(frozen=True, slots=True)
class FamilyArtifacts:
    spec: ExperimentFamilySpec
    commands: tuple[LineageCommand, ...]
    manifests: Mapping[str, ExperimentFamilyManifest]
    validations: Mapping[str, FamilyLineageValidationResult]


@dataclass(frozen=True, slots=True)
class ResolvedFamilyHead:
    manifest: ExperimentFamilyManifest
    validation: FamilyLineageValidationResult
    ref: str
    seal_hash: str
    chain_refs: tuple[str, ...]


@dataclass(slots=True)
class _ProcessFamilyState:
    pid: int
    commands: list[LineageCommand]
    event_lines: dict[str, bytes]
    receipts: dict[str, CommandReceipt]
    failed_reasons: tuple[str, ...] = ()


def _plain_decimal(value: Decimal) -> str:
    if not value.is_finite():
        raise ValueError("non-finite numbers are not supported")
    if value == 0:
        return "0"
    result = format(value, "f")
    if "." in result:
        result = result.rstrip("0").rstrip(".")
    return result


def _canonical_text(value: Any) -> str:
    if hasattr(value, "to_dict"):
        value = value.to_dict()
    elif isinstance(value, Enum):
        value = value.value
    if value is None:
        return "null"
    if value is True:
        return "true"
    if value is False:
        return "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, (float, Decimal)):
        if isinstance(value, float) and not math.isfinite(value):
            raise ValueError("non-finite numbers are not supported")
        return _plain_decimal(Decimal(str(value)))
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    if isinstance(value, Mapping):
        if any(not isinstance(key, str) for key in value):
            raise TypeError("canonical mapping keys must be strings")
        return "{" + ",".join(
            f"{_canonical_text(key)}:{_canonical_text(value[key])}" for key in sorted(value)
        ) + "}"
    if isinstance(value, (list, tuple)):
        return "[" + ",".join(_canonical_text(item) for item in value) + "]"
    raise TypeError(f"unsupported canonical value type: {type(value).__name__}")


def canonical_json_bytes(value: Any) -> bytes:
    return _canonical_text(value).encode("utf-8")


def canonical_jsonl_line(command: LineageCommand) -> bytes:
    return canonical_json_bytes(command.to_dict()) + b"\n"


def build_seal_envelope(
    spec: ExperimentFamilySpec,
    commands: Sequence[LineageCommand],
    version: int,
    supersedes_ref: str = "",
    supersedes_hash: str = "",
) -> dict[str, Any]:
    return {
        "domain": SEAL_DOMAIN,
        "schema_version": "1.0",
        "family_id": spec.family_id,
        "manifest_version": version,
        "spec": spec.to_dict(),
        "events": [item.to_dict() for item in sorted(commands, key=lambda item: (item.sequence, item.event_id))],
        "supersedes": {"ref": supersedes_ref, "hash": supersedes_hash},
    }


def compute_family_seal_hash(
    spec: ExperimentFamilySpec,
    commands: Sequence[LineageCommand],
    version: int,
    supersedes_ref: str = "",
    supersedes_hash: str = "",
) -> str:
    envelope = build_seal_envelope(spec, commands, version, supersedes_ref, supersedes_hash)
    return hashlib.sha256(canonical_json_bytes(envelope)).hexdigest()


def _safe_family_id(family_id: str) -> str:
    if not isinstance(family_id, str) or not _FAMILY_ID.fullmatch(family_id) or family_id in {".", ".."}:
        raise LineageStoreError(LineageBlockedCode.INVALID_IDENTIFIER.value)
    return family_id


def _root_path(root: str | os.PathLike[str]) -> Path:
    path = Path(root)
    if not path.is_absolute():
        path = path.absolute()
    path.mkdir(parents=True, exist_ok=True)
    if path.is_symlink():
        raise LineageStoreError(LineageBlockedCode.INVALID_IDENTIFIER.value)
    return path.resolve()


def _contained(root: Path, relative_ref: str) -> Path:
    ref = Path(relative_ref)
    if ref.is_absolute() or ".." in ref.parts:
        raise LineageStoreError(LineageBlockedCode.INVALID_IDENTIFIER.value)
    target = root.joinpath(ref)
    current = root
    for part in ref.parts:
        current = current / part
        if current.is_symlink():
            raise LineageStoreError(LineageBlockedCode.INVALID_IDENTIFIER.value)
    resolved_parent = target.parent.resolve()
    if root != resolved_parent and root not in resolved_parent.parents:
        raise LineageStoreError(LineageBlockedCode.INVALID_IDENTIFIER.value)
    return target


def _acquire_process_owner(family: Path, events_path: Path) -> int:
    """Hold a non-blocking OS ownership lease for this process lifetime."""

    key = str(family)
    pid = os.getpid()
    with _LOCKS_GUARD:
        inherited = _PROCESS_OWNERS.get(key)
        if inherited is not None:
            owner_pid, owner_fd, references = inherited
            if owner_pid == pid:
                _PROCESS_OWNERS[key] = (owner_pid, owner_fd, references + 1)
                return owner_fd
            # A fork inherited both Python bookkeeping and the descriptor.
            # Drop that inherited reference before independently competing.
            os.close(owner_fd)
            del _PROCESS_OWNERS[key]
        # Lock the already-declared append-only ledger itself so ownership does
        # not introduce a seventh persistent artifact or alter the fixed layout.
        fd = os.open(events_path, os.O_RDWR)
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except (BlockingIOError, OSError) as error:
            os.close(fd)
            raise LineageStoreError("writer_ownership_conflict") from error
        _PROCESS_OWNERS[key] = (pid, fd, 1)
        return fd


def _release_process_owner(family: Path, owner_fd: int) -> None:
    key = str(family)
    pid = os.getpid()
    with _LOCKS_GUARD:
        owner = _PROCESS_OWNERS.get(key)
        if owner is None or owner[:2] != (pid, owner_fd):
            return
        if owner[2] > 1:
            _PROCESS_OWNERS[key] = (pid, owner_fd, owner[2] - 1)
            return
        fcntl.flock(owner_fd, fcntl.LOCK_UN)
        os.close(owner_fd)
        del _PROCESS_OWNERS[key]
        _PROCESS_STATES.pop(key, None)


def _family_paths(root: Path, family_id: str) -> tuple[Path, Path, Path, Path]:
    family = _contained(root, f"families/{_safe_family_id(family_id)}")
    return family, family / "spec.json", family / "events.jsonl", family / ".tmp"


def _fsync_dir(path: Path) -> None:
    fd = os.open(path, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def verify_immutable_artifact(root: str | os.PathLike[str], ref: str, expected_bytes: bytes) -> bool:
    base = _root_path(root)
    target = _contained(base, ref)
    if not target.exists():
        return False
    if target.is_symlink() or target.read_bytes() != expected_bytes:
        raise LineageStoreError(LineageBlockedCode.IMMUTABLE_VERSION_CONFLICT.value)
    return True


def _publish_immutable(root: Path, ref: str, payload: bytes) -> None:
    target = _contained(root, ref)
    target.parent.mkdir(parents=True, exist_ok=True)
    temp_dir = target.parent.parent / ".tmp"
    temp_dir.mkdir(parents=True, exist_ok=True)
    if target.exists():
        if target.is_symlink() or target.read_bytes() != payload:
            raise LineageStoreError(LineageBlockedCode.IMMUTABLE_VERSION_CONFLICT.value)
        return
    temp = temp_dir / f".{target.name}.{os.getpid()}.{threading.get_ident()}.tmp"
    fd = os.open(temp, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        written = os.write(fd, payload)
        if written != len(payload):
            raise LineageStoreError("short_immutable_write")
        os.fsync(fd)
    finally:
        os.close(fd)
    try:
        try:
            os.link(temp, target)
        except OSError as error:
            if error.errno not in {errno.EPERM, errno.EOPNOTSUPP, errno.EXDEV}:
                raise
            fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            try:
                if os.write(fd, payload) != len(payload):
                    raise LineageStoreError("short_immutable_write")
                os.fsync(fd)
            finally:
                os.close(fd)
        _fsync_dir(target.parent)
    except FileExistsError:
        if target.read_bytes() != payload:
            raise LineageStoreError(LineageBlockedCode.IMMUTABLE_VERSION_CONFLICT.value)
    finally:
        temp.unlink(missing_ok=True)


def _spec_from_dict(data: Mapping[str, Any]) -> ExperimentFamilySpec:
    return ExperimentFamilySpec(**data)


def _trial(data: Mapping[str, Any]) -> ExperimentTrial:
    values = dict(data)
    values["state"] = TrialState(values.get("state", TrialState.DECLARED.value))
    return ExperimentTrial(**values)


def _attempt(data: Mapping[str, Any]) -> TrialAttempt:
    values = dict(data)
    values["state"] = AttemptState(values.get("state", AttemptState.DECLARED.value))
    return TrialAttempt(**values)


def _selection(data: Mapping[str, Any]) -> TrialSelection:
    values = dict(data)
    values["decision"] = SelectionDecision(values["decision"])
    return TrialSelection(**values)


def _command_from_dict(data: Mapping[str, Any]) -> LineageCommand:
    values = dict(data)
    kind = values.pop("command_type", "")
    cls: type[LineageCommand]
    if kind == "declare_family":
        values["spec"] = _spec_from_dict(values["spec"])
        cls = DeclareFamily
    elif kind == "declare_trial":
        values["trial"] = _trial(values["trial"])
        cls = DeclareTrial
    elif kind == "start_attempt":
        values["attempt"] = _attempt(values["attempt"])
        cls = StartAttempt
    elif kind == "finish_attempt":
        values["state"] = AttemptState(values["state"])
        cls = FinishAttempt
    elif kind == "finalize_trial":
        values["state"] = TrialState(values["state"])
        cls = FinalizeTrial
    elif kind == "record_selection":
        values["selection"] = _selection(values["selection"])
        cls = RecordSelection
    elif kind == "request_seal":
        cls = RequestSeal
    elif kind == "append_correction":
        cls = AppendCorrection
    elif kind == "request_superseding_seal":
        cls = RequestSupersedingSeal
    else:
        raise LineageStoreError(LineageBlockedCode.SCHEMA_VERSION_UNSUPPORTED.value)
    return cls(**values)


def _read_spec(path: Path) -> ExperimentFamilySpec:
    try:
        raw = path.read_bytes()
        value = json.loads(raw)
        spec = _spec_from_dict(value)
        if canonical_json_bytes(spec) != raw:
            raise LineageStoreError(LineageBlockedCode.CANONICAL_BYTES_MISMATCH.value)
        return spec
    except LineageStoreError:
        raise
    except (OSError, ValueError, TypeError, json.JSONDecodeError) as error:
        raise LineageStoreError(LineageBlockedCode.CANONICAL_BYTES_MISMATCH.value) from error


def _read_commands(path: Path) -> tuple[LineageCommand, ...]:
    if not path.exists():
        return ()
    raw = path.read_bytes()
    if raw and not raw.endswith(b"\n"):
        raise LineageStoreError(LineageBlockedCode.CANONICAL_BYTES_MISMATCH.value)
    commands: list[LineageCommand] = []
    identities: dict[str, bytes] = {}
    try:
        for line in raw.splitlines(keepends=True):
            if len(line) > MAX_EVENT_LINE_BYTES or not line.endswith(b"\n"):
                raise LineageStoreError(LineageBlockedCode.CANONICAL_BYTES_MISMATCH.value)
            command = _command_from_dict(json.loads(line[:-1]))
            if canonical_jsonl_line(command) != line:
                raise LineageStoreError(LineageBlockedCode.CANONICAL_BYTES_MISMATCH.value)
            prior = identities.get(command.event_id)
            if prior is not None and prior != line:
                raise LineageStoreError(LineageBlockedCode.EVENT_IDENTITY_CONFLICT.value)
            if prior is None:
                identities[command.event_id] = line
                commands.append(command)
    except LineageStoreError:
        raise
    except (ValueError, TypeError, KeyError, json.JSONDecodeError) as error:
        raise LineageStoreError(LineageBlockedCode.CANONICAL_BYTES_MISMATCH.value) from error
    return tuple(commands)


def _manifest_from_dict(data: Mapping[str, Any]) -> ExperimentFamilyManifest:
    return ExperimentFamilyManifest(**data)


def _validation_from_dict(data: Mapping[str, Any]) -> FamilyLineageValidationResult:
    values = dict(data)
    values["availability"] = LineageAvailability(values["availability"])
    values["validation_status"] = ValidationStatus(values["validation_status"])
    values["effective_trial_count_availability"] = LineageAvailability(values["effective_trial_count_availability"])
    return FamilyLineageValidationResult(**values)


class LocalFamilyLineageRecorder:
    """Single-process, per-family writer with no resume/repair API."""

    def __init__(self, root: Path, spec: ExperimentFamilySpec, commands: Sequence[LineageCommand]):
        self.root = root
        self.spec = spec
        self.family_dir, self.spec_path, self.events_path, self.temp_dir = _family_paths(root, spec.family_id)
        self._owner_fd = _acquire_process_owner(self.family_dir, self.events_path)
        self._closed = False
        key = str(self.family_dir)
        with _LOCKS_GUARD:
            state = _PROCESS_STATES.get(key)
            if state is None or state.pid != os.getpid():
                event_lines = {item.event_id: canonical_jsonl_line(item) for item in commands}
                receipts = {item.event_id: CommandReceipt(item.event_id, True, idempotent=True, artifact_ref=self._events_ref) for item in commands}
                state = _ProcessFamilyState(os.getpid(), list(commands), event_lines, receipts)
                _PROCESS_STATES[key] = state
            self._state = state
        # Stable aliases preserve the recorder's introspection surface while
        # all live handles point at the same authoritative mutable objects.
        self._commands = state.commands
        self._event_lines = state.event_lines
        self._receipts = state.receipts
        with _LOCKS_GUARD:
            self._lock = _LOCKS.setdefault(str(self.family_dir), threading.RLock())

    @property
    def _spec_ref(self) -> str:
        return f"families/{self.spec.family_id}/spec.json"

    @property
    def _events_ref(self) -> str:
        return f"families/{self.spec.family_id}/events.jsonl"

    @classmethod
    def open(cls, root: str | os.PathLike[str], spec: ExperimentFamilySpec) -> tuple["LocalFamilyLineageRecorder", CommandReceipt]:
        base = _root_path(root)
        family, spec_path, events_path, temp = _family_paths(base, spec.family_id)
        # _family_paths performs component-by-component symlink validation.
        # This must happen before any mkdir can traverse a hostile family link.
        family.mkdir(parents=True, exist_ok=True)
        (family / "manifests").mkdir(exist_ok=True)
        (family / "validations").mkdir(exist_ok=True)
        temp.mkdir(exist_ok=True)
        _publish_immutable(base, f"families/{spec.family_id}/spec.json", canonical_json_bytes(spec))
        if _read_spec(spec_path) != spec:
            raise LineageStoreError(LineageBlockedCode.EVENT_IDENTITY_CONFLICT.value)
        events_path.touch(exist_ok=True)
        commands = _read_commands(events_path)
        recorder = cls(base, spec, commands)
        declare = DeclareFamily(
            event_id=f"declare-family:{spec.family_id}", family_id=spec.family_id,
            sequence=spec.declared_sequence, schema_version=spec.schema_version, spec=spec,
        )
        return recorder, recorder.submit(declare)

    def submit(self, command: LineageCommand) -> CommandReceipt:
        if self._closed:
            return CommandReceipt(command.event_id, False, blocked_reasons=("recorder_closed",))
        if self._state.failed_reasons:
            return CommandReceipt(command.event_id, False, blocked_reasons=self._state.failed_reasons)
        if command.family_id != self.spec.family_id:
            return CommandReceipt(command.event_id, False, blocked_reasons=(LineageBlockedCode.FAMILY_IDENTITY_MISMATCH.value,))
        line = canonical_jsonl_line(command)
        if len(line) > MAX_EVENT_LINE_BYTES:
            return CommandReceipt(command.event_id, False, blocked_reasons=("event_line_too_large",))
        with self._lock:
            if self._state.failed_reasons:
                return CommandReceipt(command.event_id, False, blocked_reasons=self._state.failed_reasons)
            prior = self._event_lines.get(command.event_id)
            if prior is not None:
                if prior == line:
                    receipt = self._receipts[command.event_id]
                    return CommandReceipt(receipt.event_id, True, idempotent=True, artifact_ref=receipt.artifact_ref)
                return CommandReceipt(command.event_id, False, blocked_reasons=(LineageBlockedCode.EVENT_IDENTITY_CONFLICT.value,))
            fd: int | None = None
            try:
                fd = os.open(self.events_path, os.O_WRONLY | os.O_APPEND)
                if os.write(fd, line) != len(line):
                    self._state.failed_reasons = ("short_event_write",)
                    return CommandReceipt(command.event_id, False, blocked_reasons=self._state.failed_reasons)
                os.fsync(fd)
            except OSError:
                self._state.failed_reasons = ("event_append_failed",)
                return CommandReceipt(command.event_id, False, blocked_reasons=self._state.failed_reasons)
            finally:
                if fd is not None:
                    os.close(fd)
            receipt = CommandReceipt(command.event_id, True, artifact_ref=self._events_ref)
            self._commands.append(command)
            self._event_lines[command.event_id] = line
            self._receipts[command.event_id] = receipt
            return receipt

    def close(self) -> None:
        if not self._closed and self._owner_fd >= 0:
            _release_process_owner(self.family_dir, self._owner_fd)
            self._owner_fd = -1
            self._closed = True

    def seal(
        self,
        version: int = 1,
        prior_head: tuple[str, str] | None = None,
        reason: str = "",
    ) -> SealResult:
        with self._lock:
            if self._closed:
                raise LineageStoreError("recorder_closed")
            if self._state.failed_reasons:
                raise LineageStoreError(*self._state.failed_reasons)
            commands = _read_commands(self.events_path)
            fold = fold_family_lineage(self.spec, commands)
            if fold.blocked_reasons:
                raise LineageStoreError(*fold.blocked_reasons)
            prior_ref, prior_hash = prior_head or ("", "")
            if version == 1:
                if prior_ref or prior_hash:
                    raise LineageStoreError(LineageBlockedCode.SUPERSESSION_VERSION_INVALID.value)
            else:
                if not reason.strip() or not prior_ref or not prior_hash:
                    raise LineageStoreError(LineageBlockedCode.SUPERSESSION_PRIOR_MISSING.value)
                head = resolve_family_head(self.root, self.spec.family_id)
                if version != head.manifest.manifest_version + 1 or (prior_ref, prior_hash) != (head.ref, head.seal_hash):
                    raise LineageStoreError(LineageBlockedCode.SUPERSESSION_BROKEN_CHAIN.value)
                if not any(isinstance(item, AppendCorrection) for item in commands[head.manifest.sealed_event_count:]):
                    raise LineageStoreError(LineageBlockedCode.SUPERSESSION_PRIOR_MISSING.value)
            request_kind = RequestSeal if version == 1 else RequestSupersedingSeal
            if not commands or not isinstance(commands[-1], request_kind) or commands[-1].manifest_version != version:
                raise LineageStoreError(LineageBlockedCode.REQUIRED_FIELD_MISSING.value)
            request = commands[-1]
            if version > 1 and (
                request.prior_head_ref != prior_ref
                or request.prior_head_hash != prior_hash
                or request.reason != reason
            ):
                raise LineageStoreError(LineageBlockedCode.TARGET_MISMATCH.value)
            seal_hash = compute_family_seal_hash(self.spec, commands, version, prior_ref, prior_hash)
            manifest = ExperimentFamilyManifest(
                schema_version=self.spec.schema_version,
                family_id=self.spec.family_id,
                manifest_version=version,
                spec_ref=self._spec_ref,
                events_ref=self._events_ref,
                sealed_event_count=fold.event_count,
                sealed_last_sequence=fold.last_sequence,
                raw_trial_count=fold.raw_trial_count,
                trial_ids=fold.trial_ids,
                supersedes_ref=prior_ref,
                supersedes_hash=prior_hash,
                supersession_reason=reason,
                seal_hash=seal_hash,
            )
            manifest_ref = f"families/{self.spec.family_id}/manifests/family-manifest-v{version:04d}.json"
            validation_ref = f"families/{self.spec.family_id}/validations/family-manifest-v{version:04d}.validation.json"
            validation = validate_family_lineage(manifest, self.spec, commands, target_ref=manifest_ref, target_hash=seal_hash)
            if validation.validation_status is not ValidationStatus.PASS:
                raise LineageStoreError(*validation.blocked_reasons)
            _publish_immutable(self.root, manifest_ref, canonical_json_bytes(manifest))
            _publish_immutable(self.root, validation_ref, canonical_json_bytes(validation))
            return SealResult(manifest, validation, manifest_ref, validation_ref)


def load_family_artifacts(root: str | os.PathLike[str], family_id: str) -> FamilyArtifacts:
    base = _root_path(root)
    family, spec_path, events_path, _ = _family_paths(base, family_id)
    if not spec_path.exists() or not events_path.exists():
        raise LineageStoreError(LineageBlockedCode.STORAGE_ARTIFACT_MISSING.value)
    spec = _read_spec(spec_path)
    commands = _read_commands(events_path)
    manifests: dict[str, ExperimentFamilyManifest] = {}
    validations: dict[str, FamilyLineageValidationResult] = {}
    try:
        for path in sorted((family / "manifests").glob("*.json")):
            ref = path.relative_to(base).as_posix()
            raw = path.read_bytes()
            item = _manifest_from_dict(json.loads(raw))
            if raw != canonical_json_bytes(item) or path.name != f"family-manifest-v{item.manifest_version:04d}.json":
                raise LineageStoreError(LineageBlockedCode.CANONICAL_BYTES_MISMATCH.value)
            manifests[ref] = item
        for path in sorted((family / "validations").glob("*.json")):
            ref = path.relative_to(base).as_posix()
            raw = path.read_bytes()
            item = _validation_from_dict(json.loads(raw))
            if raw != canonical_json_bytes(item):
                raise LineageStoreError(LineageBlockedCode.CANONICAL_BYTES_MISMATCH.value)
            validations[ref] = item
    except LineageStoreError:
        raise
    except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError) as error:
        raise LineageStoreError(LineageBlockedCode.CANONICAL_BYTES_MISMATCH.value) from error
    return FamilyArtifacts(spec, commands, manifests, validations)


def resolve_family_head(root: str | os.PathLike[str], family_id: str) -> ResolvedFamilyHead:
    artifacts = load_family_artifacts(root, family_id)
    if not artifacts.manifests:
        raise LineageStoreError(LineageBlockedCode.STORAGE_ARTIFACT_MISSING.value)
    by_ref = dict(artifacts.manifests)
    children: dict[str, list[str]] = {ref: [] for ref in by_ref}
    roots: list[str] = []
    validations_by_target = {item.target_ref: item for item in artifacts.validations.values()}
    # Inspect the complete embedded reference graph before trusting hashes or
    # validations.  Cycles have no root and must not be mislabeled as a generic
    # missing-root failure merely because their self-referential hashes cannot
    # be made valid.
    for ref, manifest in by_ref.items():
        if not manifest.supersedes_ref:
            roots.append(ref)
            continue
        if manifest.supersedes_ref not in by_ref:
            raise LineageStoreError(LineageBlockedCode.SUPERSESSION_BROKEN_CHAIN.value)
        children[manifest.supersedes_ref].append(ref)
    for origin in by_ref:
        seen: set[str] = set()
        current = origin
        while by_ref[current].supersedes_ref:
            if current in seen:
                raise LineageStoreError(LineageBlockedCode.SUPERSESSION_CYCLE.value)
            seen.add(current)
            current = by_ref[current].supersedes_ref
    if any(len(items) > 1 for items in children.values()):
        raise LineageStoreError(LineageBlockedCode.SUPERSESSION_BROKEN_CHAIN.value)
    if len(roots) != 1:
        raise LineageStoreError(LineageBlockedCode.SUPERSESSION_BROKEN_CHAIN.value)
    for ref, manifest in by_ref.items():
        if manifest.family_id != family_id or manifest.manifest_version > 9999:
            raise LineageStoreError(LineageBlockedCode.SUPERSESSION_VERSION_INVALID.value)
        if manifest.sealed_event_count > len(artifacts.commands):
            raise LineageStoreError(LineageBlockedCode.TARGET_MISMATCH.value)
        prefix = tuple(sorted(artifacts.commands, key=lambda item: (item.sequence, item.event_id))[:manifest.sealed_event_count])
        if not prefix or prefix[-1].sequence != manifest.sealed_last_sequence:
            raise LineageStoreError(LineageBlockedCode.TARGET_MISMATCH.value)
        request = prefix[-1]
        expected_request_type = RequestSeal if manifest.manifest_version == 1 else RequestSupersedingSeal
        if not isinstance(request, expected_request_type) or request.manifest_version != manifest.manifest_version:
            raise LineageStoreError(LineageBlockedCode.TARGET_MISMATCH.value)
        if manifest.manifest_version > 1 and (
            request.prior_head_ref != manifest.supersedes_ref
            or request.prior_head_hash != manifest.supersedes_hash
            or request.reason != manifest.supersession_reason
        ):
            raise LineageStoreError(LineageBlockedCode.TARGET_MISMATCH.value)
        expected = compute_family_seal_hash(artifacts.spec, prefix, manifest.manifest_version, manifest.supersedes_ref, manifest.supersedes_hash)
        if expected != manifest.seal_hash:
            raise LineageStoreError(LineageBlockedCode.SEAL_HASH_MISMATCH.value)
        validation = validations_by_target.get(ref)
        if validation is None or validation.target_hash != manifest.seal_hash or validation.validation_status is not ValidationStatus.PASS:
            raise LineageStoreError(LineageBlockedCode.TARGET_MISMATCH.value)
        replay = validate_family_lineage(manifest, artifacts.spec, artifacts.commands, target_ref=ref, target_hash=manifest.seal_hash)
        if replay.validation_status is not ValidationStatus.PASS:
            raise LineageStoreError(*replay.blocked_reasons)
        if manifest.manifest_version == 1:
            if manifest.supersedes_ref or manifest.supersedes_hash:
                raise LineageStoreError(LineageBlockedCode.SUPERSESSION_VERSION_INVALID.value)
        else:
            prior = by_ref.get(manifest.supersedes_ref)
            if prior is None or prior.seal_hash != manifest.supersedes_hash or prior.manifest_version + 1 != manifest.manifest_version:
                raise LineageStoreError(LineageBlockedCode.SUPERSESSION_BROKEN_CHAIN.value)
    chain: list[str] = []
    seen: set[str] = set()
    current = roots[0]
    while True:
        if current in seen:
            raise LineageStoreError(LineageBlockedCode.SUPERSESSION_CYCLE.value)
        seen.add(current)
        chain.append(current)
        next_refs = children[current]
        if not next_refs:
            break
        current = next_refs[0]
    if len(seen) != len(by_ref):
        raise LineageStoreError(LineageBlockedCode.SUPERSESSION_CYCLE.value)
    head = by_ref[current]
    validation = validations_by_target[current]
    return ResolvedFamilyHead(head, validation, current, head.seal_hash, tuple(chain))


__all__ = [name for name in globals() if not name.startswith("_")]
