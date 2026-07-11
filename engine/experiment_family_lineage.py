"""Immutable experiment-family lineage contracts and pure validation helpers.

This module deliberately performs no storage, runtime, data, credential, or
external operations.  Persistent recording and sealing are implemented by a
downstream recorder through :class:`LineageRecorder`.
"""

from __future__ import annotations

from dataclasses import dataclass, field, fields as dataclass_fields, is_dataclass
from enum import Enum
import hashlib
import json
import math
from types import MappingProxyType
from typing import Any, ClassVar, Mapping, Protocol, Sequence, runtime_checkable


LINEAGE_SCHEMA_VERSION = 1
TRIAL_ID_DOMAIN = "quant-lab.experiment-family-lineage.trial-id.v1"


class _StringEnum(str, Enum):
    def __str__(self) -> str:
        return self.value


class LineageAvailability(_StringEnum):
    PRESENT = "present"
    TYPED_UNAVAILABLE = "typed_unavailable"
    NOT_APPLICABLE_WITH_REASON = "not_applicable_with_reason"
    BLOCKED = "blocked"


class ValidationStatus(_StringEnum):
    PASS = "pass"
    UNAVAILABLE = "unavailable"
    BLOCKED = "blocked"


class FamilyState(_StringEnum):
    ABSENT = "absent"
    DECLARED = "declared"
    RECORDING = "recording"
    SEALED = "sealed"
    SUPERSEDED = "superseded"


class TrialState(_StringEnum):
    DECLARED = "declared"
    ACTIVE = "active"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"
    EXCLUDED = "excluded"
    NEVER_STARTED = "never_started"


class AttemptState(_StringEnum):
    DECLARED = "declared"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


class SelectionDecision(_StringEnum):
    SELECTED = "selected"
    REJECTED = "rejected"
    EXCLUDED = "excluded"


class C1InputStatus(_StringEnum):
    RAW_INPUT_READY = "raw_input_ready"
    INPUT_BLOCKED = "input_blocked"


class LineageBlockedCode(_StringEnum):
    SCHEMA_VERSION_UNSUPPORTED = "schema_version_unsupported"
    REQUIRED_FIELD_MISSING = "required_field_missing"
    INVALID_IDENTIFIER = "invalid_identifier"
    FAMILY_IDENTITY_MISMATCH = "family_identity_mismatch"
    EVENT_IDENTITY_CONFLICT = "event_identity_conflict"
    SEQUENCE_NOT_MONOTONIC = "sequence_not_monotonic"
    POST_HOC_DECLARATION = "post_hoc_declaration"
    ORPHAN_TRIAL = "orphan_trial"
    ORPHAN_ATTEMPT = "orphan_attempt"
    ORPHAN_SELECTION = "orphan_selection"
    ILLEGAL_FAMILY_TRANSITION = "illegal_family_transition"
    ILLEGAL_TRIAL_TRANSITION = "illegal_trial_transition"
    ILLEGAL_ATTEMPT_TRANSITION = "illegal_attempt_transition"
    DUPLICATE_ATTEMPT_ORDINAL = "duplicate_attempt_ordinal"
    STABLE_TRIAL_ID_MISMATCH = "stable_trial_id_mismatch"
    TERMINAL_REASON_MISSING = "terminal_reason_missing"
    ACTIVE_ENTITY_AT_SEAL = "active_entity_at_seal"
    RAW_TRIAL_COUNT_MISMATCH = "raw_trial_count_mismatch"
    TARGET_REF_MISSING = "target_ref_missing"
    TARGET_HASH_MISSING = "target_hash_missing"
    TARGET_MISMATCH = "target_mismatch"
    EFFECTIVE_TRIAL_CLAIM_FORBIDDEN = "effective_trial_claim_forbidden"
    FORBIDDEN_OPERATION_NONZERO = "forbidden_operation_nonzero"
    STORAGE_ARTIFACT_MISSING = "storage_artifact_missing"
    CANONICAL_BYTES_MISMATCH = "canonical_bytes_mismatch"
    SEAL_HASH_MISMATCH = "seal_hash_mismatch"
    IMMUTABLE_VERSION_CONFLICT = "immutable_version_conflict"
    SUPERSESSION_PRIOR_MISSING = "supersession_prior_missing"
    SUPERSESSION_VERSION_INVALID = "supersession_version_invalid"
    SUPERSESSION_BROKEN_CHAIN = "supersession_broken_chain"
    SUPERSESSION_CYCLE = "supersession_cycle"


def _require_text(value: str, name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")


def _freeze_json(value: Any) -> Any:
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("non-finite floats are not supported")
        return value
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value):
        return _freeze_json({item.name: getattr(value, item.name) for item in dataclass_fields(value)})
    if isinstance(value, Mapping):
        frozen: dict[str, Any] = {}
        for key, item in value.items():
            if not isinstance(key, str):
                raise TypeError("lineage mapping keys must be strings")
            frozen[key] = _freeze_json(item)
        return MappingProxyType(dict(sorted(frozen.items())))
    if isinstance(value, (tuple, list)):
        return tuple(_freeze_json(item) for item in value)
    raise TypeError(f"unsupported lineage value type: {type(value).__name__}")


def _thaw_json(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value):
        return {item.name: _thaw_json(getattr(value, item.name)) for item in dataclass_fields(value)}
    if isinstance(value, Mapping):
        return {key: _thaw_json(item) for key, item in sorted(value.items())}
    if isinstance(value, tuple):
        return [_thaw_json(item) for item in value]
    return value


def canonical_lineage_value_bytes(value: Any) -> bytes:
    """Return strict deterministic JSON bytes for a supported lineage value."""

    canonical = _thaw_json(_freeze_json(value))
    return json.dumps(
        canonical,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def derive_stable_trial_id(family_id: str, normalized_parameters: Mapping[str, Any], seed: Any) -> str:
    _require_text(family_id, "family_id")
    payload = {
        "domain": TRIAL_ID_DOMAIN,
        "family_id": family_id,
        "normalized_parameters": normalized_parameters,
        "seed": seed,
    }
    digest = hashlib.sha256(canonical_lineage_value_bytes(payload)).hexdigest()
    return f"trial-sha256:{digest}"


class _Serializable:
    def to_dict(self) -> dict[str, Any]:
        return _thaw_json(self)


def _tuple_text(values: Sequence[str], name: str) -> tuple[str, ...]:
    result = tuple(values)
    if any(not isinstance(value, str) or not value.strip() for value in result):
        raise ValueError(f"{name} must contain non-empty strings")
    return result


@dataclass(frozen=True, slots=True)
class ExperimentFamilySpec(_Serializable):
    schema_version: int
    family_id: str
    producer_chain_id: str
    declared_sequence: int
    objective_ref: str
    parameter_space_ref: str
    run_refs: tuple[str, ...] = ()
    experiment_refs: tuple[str, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _require_text(self.family_id, "family_id")
        _require_text(self.producer_chain_id, "producer_chain_id")
        _require_text(self.objective_ref, "objective_ref")
        _require_text(self.parameter_space_ref, "parameter_space_ref")
        if self.declared_sequence < 0:
            raise ValueError("declared_sequence must be non-negative")
        object.__setattr__(self, "run_refs", _tuple_text(self.run_refs, "run_refs"))
        object.__setattr__(self, "experiment_refs", _tuple_text(self.experiment_refs, "experiment_refs"))
        object.__setattr__(self, "metadata", _freeze_json(self.metadata))


_TRIAL_REASON_STATES = frozenset({TrialState.SUCCEEDED, TrialState.FAILED, TrialState.CANCELLED, TrialState.EXCLUDED, TrialState.NEVER_STARTED})


@dataclass(frozen=True, slots=True)
class ExperimentTrial(_Serializable):
    family_id: str
    trial_id: str
    normalized_parameters: Mapping[str, Any]
    seed: Any
    declared_sequence: int
    state: TrialState = TrialState.DECLARED
    terminal_reason: str = ""
    run_refs: tuple[str, ...] = ()
    experiment_refs: tuple[str, ...] = ()
    artifact_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _require_text(self.family_id, "family_id")
        _require_text(self.trial_id, "trial_id")
        if self.declared_sequence < 0:
            raise ValueError("declared_sequence must be non-negative")
        object.__setattr__(self, "normalized_parameters", _freeze_json(self.normalized_parameters))
        object.__setattr__(self, "seed", _freeze_json(self.seed))
        object.__setattr__(self, "run_refs", _tuple_text(self.run_refs, "run_refs"))
        object.__setattr__(self, "experiment_refs", _tuple_text(self.experiment_refs, "experiment_refs"))
        object.__setattr__(self, "artifact_refs", _tuple_text(self.artifact_refs, "artifact_refs"))


@dataclass(frozen=True, slots=True)
class TrialAttempt(_Serializable):
    family_id: str
    trial_id: str
    attempt_id: str
    ordinal: int
    state: AttemptState = AttemptState.DECLARED
    terminal_reason: str = ""
    run_ref: str = ""
    experiment_ref: str = ""
    artifact_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _require_text(self.family_id, "family_id")
        _require_text(self.trial_id, "trial_id")
        _require_text(self.attempt_id, "attempt_id")
        if self.ordinal < 1:
            raise ValueError("ordinal must be at least 1")
        object.__setattr__(self, "artifact_refs", _tuple_text(self.artifact_refs, "artifact_refs"))


@dataclass(frozen=True, slots=True)
class TrialSelection(_Serializable):
    family_id: str
    trial_id: str
    selection_id: str
    sequence: int
    decision: SelectionDecision
    reason: str
    artifact_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _require_text(self.family_id, "family_id")
        _require_text(self.trial_id, "trial_id")
        _require_text(self.selection_id, "selection_id")
        _require_text(self.reason, "reason")
        if self.sequence < 0:
            raise ValueError("sequence must be non-negative")
        object.__setattr__(self, "artifact_refs", _tuple_text(self.artifact_refs, "artifact_refs"))


@dataclass(frozen=True, slots=True)
class ExperimentFamilyManifest(_Serializable):
    schema_version: int
    family_id: str
    manifest_version: int
    spec_ref: str
    events_ref: str
    sealed_event_count: int
    sealed_last_sequence: int
    raw_trial_count: int
    trial_ids: tuple[str, ...]
    supersedes_ref: str = ""
    supersedes_hash: str = ""
    supersession_reason: str = ""
    seal_hash: str = ""
    sealed_at: str = ""

    def __post_init__(self) -> None:
        _require_text(self.family_id, "family_id")
        _require_text(self.spec_ref, "spec_ref")
        _require_text(self.events_ref, "events_ref")
        if self.manifest_version < 1 or self.sealed_event_count < 0 or self.sealed_last_sequence < 0 or self.raw_trial_count < 0:
            raise ValueError("manifest version and count fields are out of range")
        trial_ids = tuple(sorted(set(_tuple_text(self.trial_ids, "trial_ids"))))
        if len(trial_ids) != len(self.trial_ids):
            raise ValueError("trial_ids must be unique")
        object.__setattr__(self, "trial_ids", trial_ids)


@dataclass(frozen=True, slots=True)
class FamilyLineageValidationResult(_Serializable):
    schema_version: int
    validation_id: str
    target_ref: str
    target_hash: str
    availability: LineageAvailability
    validation_status: ValidationStatus
    blocked_reasons: tuple[str, ...] = ()
    unavailable_reason: str = ""
    recomputed_raw_trial_count: int | None = None
    declared_raw_trial_count: int | None = None
    effective_trial_count_availability: LineageAvailability = LineageAvailability.TYPED_UNAVAILABLE
    effective_trial_count: int | None = None
    effective_ref: str = ""
    effective_method: str = ""
    forbidden_operation_counts: Mapping[str, int] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "blocked_reasons", tuple(sorted(set(str(reason) for reason in self.blocked_reasons))))
        counts = {str(key): int(value) for key, value in self.forbidden_operation_counts.items()}
        object.__setattr__(self, "forbidden_operation_counts", _freeze_json(counts))
        if self.effective_trial_count_availability is not LineageAvailability.TYPED_UNAVAILABLE:
            raise ValueError("effective trial count must remain typed_unavailable")
        if self.effective_trial_count is not None or self.effective_ref or self.effective_method:
            raise ValueError("effective trial count claims are forbidden")


PERSISTENT_LINEAGE_OBJECTS = (
    ExperimentFamilySpec,
    ExperimentTrial,
    TrialAttempt,
    TrialSelection,
    ExperimentFamilyManifest,
    FamilyLineageValidationResult,
)


@dataclass(frozen=True, slots=True)
class TransitionResult(_Serializable):
    accepted: bool
    state: str
    blocked_reason: str = ""


_FAMILY_EDGES = {(FamilyState.ABSENT, FamilyState.DECLARED), (FamilyState.DECLARED, FamilyState.RECORDING), (FamilyState.RECORDING, FamilyState.SEALED), (FamilyState.SEALED, FamilyState.SUPERSEDED)}
_TRIAL_EDGES = {(TrialState.DECLARED, TrialState.ACTIVE), (TrialState.DECLARED, TrialState.NEVER_STARTED), (TrialState.DECLARED, TrialState.EXCLUDED), *((TrialState.ACTIVE, state) for state in (TrialState.SUCCEEDED, TrialState.FAILED, TrialState.CANCELLED, TrialState.EXCLUDED))}
_ATTEMPT_EDGES = {(AttemptState.DECLARED, AttemptState.RUNNING), *((AttemptState.RUNNING, state) for state in (AttemptState.SUCCEEDED, AttemptState.FAILED, AttemptState.CANCELLED))}


def _transition(current: Any, requested: Any, enum_type: type[Enum], edges: set[tuple[Any, Any]], code: LineageBlockedCode) -> TransitionResult:
    try:
        current_state = enum_type(current)
        requested_state = enum_type(requested)
    except (TypeError, ValueError):
        return TransitionResult(False, str(current), code.value)
    if (current_state, requested_state) not in edges:
        return TransitionResult(False, current_state.value, code.value)
    return TransitionResult(True, requested_state.value)


def transition_family_state(current: FamilyState | str, requested: FamilyState | str) -> TransitionResult:
    return _transition(current, requested, FamilyState, _FAMILY_EDGES, LineageBlockedCode.ILLEGAL_FAMILY_TRANSITION)


def transition_trial_state(current: TrialState | str, requested: TrialState | str) -> TransitionResult:
    return _transition(current, requested, TrialState, _TRIAL_EDGES, LineageBlockedCode.ILLEGAL_TRIAL_TRANSITION)


def transition_attempt_state(current: AttemptState | str, requested: AttemptState | str) -> TransitionResult:
    return _transition(current, requested, AttemptState, _ATTEMPT_EDGES, LineageBlockedCode.ILLEGAL_ATTEMPT_TRANSITION)


@dataclass(frozen=True, slots=True)
class LineageCommand(_Serializable):
    event_id: str
    family_id: str
    sequence: int
    schema_version: int = LINEAGE_SCHEMA_VERSION
    command_type: ClassVar[str] = "lineage_command"

    def __post_init__(self) -> None:
        _require_text(self.event_id, "event_id")
        _require_text(self.family_id, "family_id")
        if self.sequence < 0:
            raise ValueError("sequence must be non-negative")

    def to_dict(self) -> dict[str, Any]:
        result = _thaw_json(self)
        result["command_type"] = self.command_type
        return result


@dataclass(frozen=True, slots=True)
class DeclareFamily(LineageCommand):
    spec: ExperimentFamilySpec = field(default=None)  # type: ignore[assignment]
    command_type: ClassVar[str] = "declare_family"


@dataclass(frozen=True, slots=True)
class DeclareTrial(LineageCommand):
    trial: ExperimentTrial = field(default=None)  # type: ignore[assignment]
    command_type: ClassVar[str] = "declare_trial"


@dataclass(frozen=True, slots=True)
class StartAttempt(LineageCommand):
    attempt: TrialAttempt = field(default=None)  # type: ignore[assignment]
    command_type: ClassVar[str] = "start_attempt"


@dataclass(frozen=True, slots=True)
class FinishAttempt(LineageCommand):
    attempt_id: str = ""
    state: AttemptState = AttemptState.FAILED
    terminal_reason: str = ""
    command_type: ClassVar[str] = "finish_attempt"

    def __post_init__(self) -> None:
        LineageCommand.__post_init__(self)
        _require_text(self.attempt_id, "attempt_id")


@dataclass(frozen=True, slots=True)
class FinalizeTrial(LineageCommand):
    trial_id: str = ""
    state: TrialState = TrialState.FAILED
    terminal_reason: str = ""
    command_type: ClassVar[str] = "finalize_trial"

    def __post_init__(self) -> None:
        LineageCommand.__post_init__(self)
        _require_text(self.trial_id, "trial_id")


@dataclass(frozen=True, slots=True)
class RecordSelection(LineageCommand):
    selection: TrialSelection = field(default=None)  # type: ignore[assignment]
    command_type: ClassVar[str] = "record_selection"


@dataclass(frozen=True, slots=True)
class RequestSeal(LineageCommand):
    manifest_version: int = 1
    prior_head_ref: str = ""
    prior_head_hash: str = ""
    reason: str = ""
    command_type: ClassVar[str] = "request_seal"

    def __post_init__(self) -> None:
        LineageCommand.__post_init__(self)
        if self.manifest_version != 1:
            raise ValueError("initial seal manifest_version must be 1")


@dataclass(frozen=True, slots=True)
class AppendCorrection(LineageCommand):
    corrects_event_id: str = ""
    reason: str = ""
    correction: Mapping[str, Any] = field(default_factory=dict)
    command_type: ClassVar[str] = "append_correction"

    def __post_init__(self) -> None:
        LineageCommand.__post_init__(self)
        _require_text(self.corrects_event_id, "corrects_event_id")
        _require_text(self.reason, "reason")
        object.__setattr__(self, "correction", _freeze_json(self.correction))


@dataclass(frozen=True, slots=True)
class RequestSupersedingSeal(LineageCommand):
    manifest_version: int = 2
    prior_head_ref: str = ""
    prior_head_hash: str = ""
    reason: str = ""
    command_type: ClassVar[str] = "request_superseding_seal"

    def __post_init__(self) -> None:
        LineageCommand.__post_init__(self)
        if self.manifest_version < 2:
            raise ValueError("superseding seal manifest_version must be at least 2")
        _require_text(self.prior_head_ref, "prior_head_ref")
        _require_text(self.prior_head_hash, "prior_head_hash")
        _require_text(self.reason, "reason")


TYPED_LINEAGE_COMMANDS = (DeclareFamily, DeclareTrial, StartAttempt, FinishAttempt, FinalizeTrial, RecordSelection, RequestSeal, AppendCorrection, RequestSupersedingSeal)


@dataclass(frozen=True, slots=True)
class CommandReceipt(_Serializable):
    event_id: str
    accepted: bool
    idempotent: bool = False
    blocked_reasons: tuple[str, ...] = ()
    artifact_ref: str = ""


@runtime_checkable
class LineageRecorder(Protocol):
    def submit(self, command: LineageCommand) -> CommandReceipt: ...


@dataclass(frozen=True, slots=True)
class SealRequestResult(_Serializable):
    request_receipt: CommandReceipt
    manifest: ExperimentFamilyManifest | None = None
    validation: FamilyLineageValidationResult | None = None


class FamilyLineageSession:
    """Non-persistent immediate-submit application façade."""

    __slots__ = ("spec", "recorder", "lineage_root", "declare_receipt", "_next_sequence")

    def __init__(self, spec: ExperimentFamilySpec, recorder: LineageRecorder, lineage_root: str, declare_receipt: CommandReceipt) -> None:
        self.spec = spec
        self.recorder = recorder
        self.lineage_root = lineage_root
        self.declare_receipt = declare_receipt
        self._next_sequence = spec.declared_sequence + 1

    @classmethod
    def open(cls, spec: ExperimentFamilySpec, recorder: LineageRecorder, lineage_root: str) -> "FamilyLineageSession":
        _require_text(lineage_root, "lineage_root")
        command = DeclareFamily(event_id=f"declare-family:{spec.family_id}", family_id=spec.family_id, sequence=spec.declared_sequence, schema_version=spec.schema_version, spec=spec)
        receipt = recorder.submit(command)
        return cls(spec, recorder, lineage_root, receipt)

    def submit(self, command: LineageCommand) -> CommandReceipt:
        if command.family_id != self.spec.family_id:
            return CommandReceipt(command.event_id, False, blocked_reasons=(LineageBlockedCode.FAMILY_IDENTITY_MISMATCH.value,))
        receipt = self.recorder.submit(command)
        self._next_sequence = max(self._next_sequence, command.sequence + 1)
        return receipt

    def seal(self, version: int, prior_head: tuple[str, str] | None = None, reason: str = "") -> SealRequestResult:
        prior_ref, prior_hash = prior_head or ("", "")
        command_type = RequestSeal if version == 1 else RequestSupersedingSeal
        command = command_type(event_id=f"request-seal:{self.spec.family_id}:{version}", family_id=self.spec.family_id, sequence=self._next_sequence, manifest_version=version, prior_head_ref=prior_ref, prior_head_hash=prior_hash, reason=reason)
        return SealRequestResult(self.submit(command))


@dataclass(frozen=True, slots=True)
class LineageFoldResult(_Serializable):
    family_state: FamilyState
    trial_states: Mapping[str, TrialState]
    attempt_states: Mapping[str, AttemptState]
    trial_ids: tuple[str, ...]
    raw_trial_count: int
    blocked_reasons: tuple[str, ...]
    event_count: int
    last_sequence: int


def fold_family_lineage(spec: ExperimentFamilySpec, commands: Sequence[LineageCommand]) -> LineageFoldResult:
    reasons: set[str] = set()
    family_state = FamilyState.ABSENT
    trials: dict[str, TrialState] = {}
    attempts: dict[str, AttemptState] = {}
    attempt_parents: dict[str, str] = {}
    ordinals: set[tuple[str, int]] = set()
    selection_ids: set[str] = set()
    event_payloads: dict[str, bytes] = {}
    last_sequence = -1
    ordered = sorted(commands, key=lambda item: (item.sequence, item.event_id))
    for command in ordered:
        # The public base class is an envelope, not an executable command.  An
        # unknown subclass is equally unsupported: neither may enter the
        # semantic event boundary or mutate fold state.
        if type(command) not in TYPED_LINEAGE_COMMANDS:
            reasons.add(LineageBlockedCode.SCHEMA_VERSION_UNSUPPORTED.value)
            continue
        if command.schema_version != LINEAGE_SCHEMA_VERSION:
            reasons.add(LineageBlockedCode.SCHEMA_VERSION_UNSUPPORTED.value)
        if command.family_id != spec.family_id:
            reasons.add(LineageBlockedCode.FAMILY_IDENTITY_MISMATCH.value)
        payload = canonical_lineage_value_bytes(command.to_dict())
        prior = event_payloads.get(command.event_id)
        if prior is not None:
            if prior != payload:
                reasons.add(LineageBlockedCode.EVENT_IDENTITY_CONFLICT.value)
            continue
        event_payloads[command.event_id] = payload
        if command.sequence < last_sequence:
            reasons.add(LineageBlockedCode.SEQUENCE_NOT_MONOTONIC.value)
        last_sequence = max(last_sequence, command.sequence)

        if family_state in (FamilyState.SEALED, FamilyState.SUPERSEDED) and isinstance(
            command,
            (DeclareTrial, StartAttempt, FinishAttempt, FinalizeTrial, RecordSelection),
        ):
            reasons.add(
                LineageBlockedCode.POST_HOC_DECLARATION.value
                if isinstance(command, DeclareTrial)
                else LineageBlockedCode.ILLEGAL_FAMILY_TRANSITION.value
            )
            continue

        if isinstance(command, DeclareFamily):
            if command.spec is None:
                reasons.add(LineageBlockedCode.REQUIRED_FIELD_MISSING.value)
            elif command.spec.family_id != command.family_id or command.spec.family_id != spec.family_id:
                reasons.add(LineageBlockedCode.FAMILY_IDENTITY_MISMATCH.value)
            elif canonical_lineage_value_bytes(command.spec) != canonical_lineage_value_bytes(spec):
                reasons.add(LineageBlockedCode.EVENT_IDENTITY_CONFLICT.value)
            else:
                transition = transition_family_state(family_state, FamilyState.DECLARED)
                if not transition.accepted:
                    reasons.add(transition.blocked_reason)
                else:
                    family_state = FamilyState.DECLARED
        elif isinstance(command, DeclareTrial):
            if family_state is FamilyState.ABSENT:
                reasons.add(LineageBlockedCode.ORPHAN_TRIAL.value)
                reasons.add(LineageBlockedCode.POST_HOC_DECLARATION.value)
                continue
            trial = command.trial
            if trial is None:
                reasons.add(LineageBlockedCode.REQUIRED_FIELD_MISSING.value)
                continue
            if trial.family_id != command.family_id or trial.family_id != spec.family_id:
                reasons.add(LineageBlockedCode.FAMILY_IDENTITY_MISMATCH.value)
                continue
            if trial.trial_id != derive_stable_trial_id(trial.family_id, trial.normalized_parameters, trial.seed):
                reasons.add(LineageBlockedCode.STABLE_TRIAL_ID_MISMATCH.value)
            if trial.trial_id in trials:
                reasons.add(LineageBlockedCode.EVENT_IDENTITY_CONFLICT.value)
            else:
                trials[trial.trial_id] = TrialState.DECLARED
                family_state = FamilyState.RECORDING
        elif isinstance(command, StartAttempt):
            attempt = command.attempt
            if attempt is None:
                reasons.add(LineageBlockedCode.REQUIRED_FIELD_MISSING.value)
                continue
            if attempt.family_id != command.family_id or attempt.family_id != spec.family_id:
                reasons.add(LineageBlockedCode.FAMILY_IDENTITY_MISMATCH.value)
                continue
            if attempt.trial_id not in trials:
                reasons.add(LineageBlockedCode.ORPHAN_ATTEMPT.value)
                continue
            if attempt.attempt_id in attempts:
                reasons.add(LineageBlockedCode.EVENT_IDENTITY_CONFLICT.value)
                continue
            if (attempt.trial_id, attempt.ordinal) in ordinals:
                reasons.add(LineageBlockedCode.DUPLICATE_ATTEMPT_ORDINAL.value)
            else:
                ordinals.add((attempt.trial_id, attempt.ordinal))
            attempts[attempt.attempt_id] = AttemptState.RUNNING
            attempt_parents[attempt.attempt_id] = attempt.trial_id
            transition = transition_trial_state(trials[attempt.trial_id], TrialState.ACTIVE)
            if transition.accepted:
                trials[attempt.trial_id] = TrialState.ACTIVE
            else:
                reasons.add(transition.blocked_reason)
        elif isinstance(command, FinishAttempt):
            if command.attempt_id not in attempts:
                reasons.add(LineageBlockedCode.ORPHAN_ATTEMPT.value)
                continue
            transition = transition_attempt_state(attempts[command.attempt_id], command.state)
            if transition.accepted:
                attempts[command.attempt_id] = command.state
            else:
                reasons.add(transition.blocked_reason)
            if command.state in (AttemptState.FAILED, AttemptState.CANCELLED) and not command.terminal_reason.strip():
                reasons.add(LineageBlockedCode.TERMINAL_REASON_MISSING.value)
        elif isinstance(command, FinalizeTrial):
            if command.trial_id not in trials:
                reasons.add(LineageBlockedCode.ORPHAN_TRIAL.value)
                continue
            transition = transition_trial_state(trials[command.trial_id], command.state)
            if transition.accepted:
                trials[command.trial_id] = command.state
            else:
                reasons.add(transition.blocked_reason)
            if command.state in _TRIAL_REASON_STATES and not command.terminal_reason.strip():
                reasons.add(LineageBlockedCode.TERMINAL_REASON_MISSING.value)
        elif isinstance(command, RecordSelection):
            selection = command.selection
            if selection is None:
                reasons.add(LineageBlockedCode.REQUIRED_FIELD_MISSING.value)
            elif selection.family_id != command.family_id or selection.family_id != spec.family_id:
                reasons.add(LineageBlockedCode.FAMILY_IDENTITY_MISMATCH.value)
            elif selection.trial_id not in trials:
                reasons.add(LineageBlockedCode.ORPHAN_SELECTION.value)
            elif selection.selection_id in selection_ids:
                reasons.add(LineageBlockedCode.EVENT_IDENTITY_CONFLICT.value)
            else:
                selection_ids.add(selection.selection_id)
        elif isinstance(command, RequestSeal):
            if command.prior_head_ref or command.prior_head_hash:
                reasons.add(LineageBlockedCode.SUPERSESSION_VERSION_INVALID.value)
                continue
            if any(state in (TrialState.DECLARED, TrialState.ACTIVE) for state in trials.values()) or any(state is AttemptState.RUNNING for state in attempts.values()):
                reasons.add(LineageBlockedCode.ACTIVE_ENTITY_AT_SEAL.value)
            transition = transition_family_state(family_state, FamilyState.SEALED)
            if transition.accepted:
                family_state = FamilyState.SEALED
            else:
                reasons.add(transition.blocked_reason)
        elif isinstance(command, AppendCorrection):
            if command.corrects_event_id == command.event_id or command.corrects_event_id not in event_payloads:
                reasons.add(LineageBlockedCode.EVENT_IDENTITY_CONFLICT.value)
        elif isinstance(command, RequestSupersedingSeal):
            if any(state in (TrialState.DECLARED, TrialState.ACTIVE) for state in trials.values()) or any(state is AttemptState.RUNNING for state in attempts.values()):
                reasons.add(LineageBlockedCode.ACTIVE_ENTITY_AT_SEAL.value)
            transition = transition_family_state(family_state, FamilyState.SUPERSEDED)
            if transition.accepted:
                family_state = FamilyState.SUPERSEDED
            else:
                reasons.add(transition.blocked_reason)

    trial_ids = tuple(sorted(trials))
    return LineageFoldResult(family_state, MappingProxyType(dict(sorted(trials.items()))), MappingProxyType(dict(sorted(attempts.items()))), trial_ids, len(trial_ids), tuple(sorted(reasons)), len(event_payloads), max(last_sequence, 0))


def _validation_id(payload: Mapping[str, Any]) -> str:
    return "validation-sha256:" + hashlib.sha256(canonical_lineage_value_bytes(payload)).hexdigest()


def validate_family_lineage(manifest: ExperimentFamilyManifest, spec: ExperimentFamilySpec, commands: Sequence[LineageCommand], *, target_ref: str, target_hash: str, storage_reasons: Sequence[str] = (), forbidden_operation_counts: Mapping[str, int] | None = None) -> FamilyLineageValidationResult:
    # A manifest validates its immutable prefix, not every event appended to a
    # later version.  Both frozen fields participate: the sequence boundary
    # selects the prefix and the event count proves that the cut is exact.
    ordered_commands = sorted(commands, key=lambda item: (item.sequence, item.event_id))
    frozen_commands = tuple(
        command for command in ordered_commands if command.sequence <= manifest.sealed_last_sequence
    )
    boundary_reasons: set[str] = set()
    if len(frozen_commands) != manifest.sealed_event_count:
        boundary_reasons.add(LineageBlockedCode.TARGET_MISMATCH.value)
    frozen_sequences = {command.sequence for command in frozen_commands}
    expected_sequences = set(range(spec.declared_sequence, manifest.sealed_last_sequence + 1))
    if not expected_sequences.issubset(frozen_sequences):
        boundary_reasons.add(LineageBlockedCode.TARGET_MISMATCH.value)
    fold = fold_family_lineage(spec, frozen_commands)
    reasons = set(fold.blocked_reasons) | boundary_reasons | {str(reason) for reason in storage_reasons}
    counts = {str(key): int(value) for key, value in (forbidden_operation_counts or {}).items()}
    if spec.schema_version != LINEAGE_SCHEMA_VERSION or manifest.schema_version != LINEAGE_SCHEMA_VERSION:
        reasons.add(LineageBlockedCode.SCHEMA_VERSION_UNSUPPORTED.value)
    if not target_ref:
        reasons.add(LineageBlockedCode.TARGET_REF_MISSING.value)
    if not target_hash:
        reasons.add(LineageBlockedCode.TARGET_HASH_MISSING.value)
    if manifest.family_id != spec.family_id:
        reasons.add(LineageBlockedCode.FAMILY_IDENTITY_MISMATCH.value)
    if target_hash and target_hash != manifest.seal_hash:
        reasons.add(LineageBlockedCode.TARGET_MISMATCH.value)
    if manifest.raw_trial_count != fold.raw_trial_count or tuple(manifest.trial_ids) != fold.trial_ids:
        reasons.add(LineageBlockedCode.RAW_TRIAL_COUNT_MISMATCH.value)
    if manifest.sealed_event_count != fold.event_count or manifest.sealed_last_sequence != fold.last_sequence:
        reasons.add(LineageBlockedCode.TARGET_MISMATCH.value)
    if any(value != 0 for value in counts.values()):
        reasons.add(LineageBlockedCode.FORBIDDEN_OPERATION_NONZERO.value)
    ordered_reasons = tuple(sorted(reasons))
    payload = {"family_id": spec.family_id, "target_ref": target_ref, "target_hash": target_hash, "reasons": ordered_reasons, "raw_trial_count": fold.raw_trial_count, "forbidden_operation_counts": counts}
    return FamilyLineageValidationResult(
        schema_version=LINEAGE_SCHEMA_VERSION,
        validation_id=_validation_id(payload),
        target_ref=target_ref,
        target_hash=target_hash,
        availability=LineageAvailability.BLOCKED if ordered_reasons else LineageAvailability.PRESENT,
        validation_status=ValidationStatus.BLOCKED if ordered_reasons else ValidationStatus.PASS,
        blocked_reasons=ordered_reasons,
        recomputed_raw_trial_count=fold.raw_trial_count,
        declared_raw_trial_count=manifest.raw_trial_count,
        forbidden_operation_counts=counts,
    )


def unavailable_family_lineage(reason: str) -> FamilyLineageValidationResult:
    _require_text(reason, "reason")
    payload = {"availability": LineageAvailability.TYPED_UNAVAILABLE.value, "reason": reason}
    return FamilyLineageValidationResult(LINEAGE_SCHEMA_VERSION, _validation_id(payload), "", "", LineageAvailability.TYPED_UNAVAILABLE, ValidationStatus.UNAVAILABLE, unavailable_reason=reason)


def not_applicable_family_lineage(reason: str) -> FamilyLineageValidationResult:
    _require_text(reason, "reason")
    payload = {"availability": LineageAvailability.NOT_APPLICABLE_WITH_REASON.value, "reason": reason}
    return FamilyLineageValidationResult(LINEAGE_SCHEMA_VERSION, _validation_id(payload), "", "", LineageAvailability.NOT_APPLICABLE_WITH_REASON, ValidationStatus.UNAVAILABLE, unavailable_reason=reason)


@dataclass(frozen=True, slots=True)
class FamilyEvidenceProjection(_Serializable):
    availability: LineageAvailability
    target_ref: str = ""
    target_hash: str = ""
    raw_trial_count: int | None = None
    blocked_reasons: tuple[str, ...] = ()
    unavailable_reason: str = ""
    effective_trial_count_availability: LineageAvailability = LineageAvailability.TYPED_UNAVAILABLE
    effective_trial_count: int | None = None
    effective_ref: str = ""
    effective_method: str = ""
    c1_input_status: C1InputStatus = C1InputStatus.INPUT_BLOCKED


def project_family_evidence(manifest: ExperimentFamilyManifest | None, validation: FamilyLineageValidationResult) -> FamilyEvidenceProjection:
    if validation.availability is LineageAvailability.TYPED_UNAVAILABLE:
        return FamilyEvidenceProjection(LineageAvailability.TYPED_UNAVAILABLE, unavailable_reason=validation.unavailable_reason)
    if validation.availability is LineageAvailability.NOT_APPLICABLE_WITH_REASON:
        return FamilyEvidenceProjection(LineageAvailability.NOT_APPLICABLE_WITH_REASON, unavailable_reason=validation.unavailable_reason)
    reasons = set(validation.blocked_reasons)
    coherent_pass = (
        validation.availability is LineageAvailability.PRESENT
        and validation.validation_status is ValidationStatus.PASS
        and not validation.blocked_reasons
        and not validation.unavailable_reason
        and manifest is not None
        and bool(validation.target_ref)
        and bool(validation.target_hash)
        and validation.target_hash == manifest.seal_hash
        and validation.recomputed_raw_trial_count is not None
        and validation.recomputed_raw_trial_count == manifest.raw_trial_count
        and validation.declared_raw_trial_count == manifest.raw_trial_count
    )
    if not coherent_pass:
        if (
            manifest is None
            or not validation.target_ref
            or not validation.target_hash
            or (manifest is not None and validation.target_hash != manifest.seal_hash)
        ):
            reasons.add(LineageBlockedCode.TARGET_MISMATCH.value)
        if not reasons:
            reasons.add(LineageBlockedCode.REQUIRED_FIELD_MISSING.value)
        return FamilyEvidenceProjection(LineageAvailability.BLOCKED, target_ref=validation.target_ref, target_hash=validation.target_hash, blocked_reasons=tuple(sorted(reasons)))
    return FamilyEvidenceProjection(LineageAvailability.PRESENT, target_ref=validation.target_ref, target_hash=validation.target_hash, raw_trial_count=validation.recomputed_raw_trial_count, c1_input_status=C1InputStatus.RAW_INPUT_READY)


__all__ = [name for name in globals() if not name.startswith("_")]
