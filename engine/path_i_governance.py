"""PATH-I repository-local 授权、执行资格与声明治理合同。

本模块只提供不可变值对象和确定性判定函数。它不连接授权后端，不读取环境、
凭据或真实路径，也不执行任何数据湖、运行时、NAS、信号或交易操作。
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
import re
from types import MappingProxyType
from typing import Final, Mapping
from urllib.parse import urlsplit


GOVERNANCE_SCHEMA_VERSION: Final = "path-i-governance.v1"
RUN_PATH_DELIVERY_STATUS: Final = "contract_ready/runtime_enforcement_deferred"
NEW_RUN_LOGICAL_ROOT_TEMPLATE: Final = (
    "research://multifactor-strategy-research/{run_id}/"
)
LEGACY_RUN_LOGICAL_ROOT_TEMPLATE: Final = (
    "legacy://stage3_mature_multifactor/{run_id}/"
)

_SHA256_RE = re.compile(r"sha256:[0-9a-f]{64}\Z")
_IDENTIFIER_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:@/-]*\Z")
_FIXTURE_AUTHORITIES: Final = frozenset({"repository", "memory", "in-memory"})
_SECRET_MARKERS: Final = ("password", "passwd", "secret", "token", "credential")


class PathIGovernanceError(ValueError):
    """输入违反 PATH-I v1 治理合同。"""


class PathIEligibilityError(PathIGovernanceError):
    """consumer 在 first side effect 前发现执行资格不成立。"""


class PathIActionKind(str, Enum):
    DATA_LAKE_READ = "data_lake_read"
    MULTI_TRIAL_RUNTIME_AND_WORKSPACE_WRITE = (
        "multi_trial_runtime_and_workspace_write"
    )
    TRIAL_RETURN_GENERATION = "trial_return_generation"
    EMPIRICAL_R_COMPUTATION = "empirical_R_computation"
    NAS_REPLICA_SYNC = "nas_replica_sync"
    EXECUTION_PULL_VERIFY_MATERIALIZE = "execution_pull_verify_materialize"


class ActionDecisionOriginV1(str, Enum):
    REPOSITORY_FIXTURE = "repository_fixture"
    APPROVED_LEDGER = "approved_ledger"


class ActionTargetKindV1(str, Enum):
    REPOSITORY_FIXTURE = "repository_fixture"
    REAL_OPERATION = "real_operation"


class ActionPrerequisiteProvenanceV1(str, Enum):
    ELIGIBILITY_DECISION = "eligibility_decision"
    SEALED_TRIAL_RETURN = "sealed_trial_return"
    VERIFIED_REPLICA_RECEIPT = "verified_replica_receipt"


class ActionReasonCodeV1(str, Enum):
    ALLOW = "ALLOW"
    APPROVED_LEDGER_ADAPTER_UNAVAILABLE = "APPROVED_LEDGER_ADAPTER_UNAVAILABLE"
    RECORD_MISSING = "RECORD_MISSING"
    RECORD_INVALID = "RECORD_INVALID"
    ACTION_MISMATCH = "ACTION_MISMATCH"
    NOT_YET_VALID = "NOT_YET_VALID"
    EXPIRED = "EXPIRED"
    REVOKED = "REVOKED"
    SCOPE_MISMATCH = "SCOPE_MISMATCH"
    PATH_INVALID = "PATH_INVALID"
    PATH_DENIED = "PATH_DENIED"
    PATH_NOT_ALLOWED = "PATH_NOT_ALLOWED"
    DECISION_ORIGIN_INVALID = "DECISION_ORIGIN_INVALID"
    TARGET_KIND_INVALID = "TARGET_KIND_INVALID"
    ORIGIN_TARGET_MISMATCH = "ORIGIN_TARGET_MISMATCH"
    FIXTURE_URI_REQUIRED = "FIXTURE_URI_REQUIRED"
    PREDECESSOR_MISSING = "PREDECESSOR_MISSING"
    PREDECESSOR_DENIED = "PREDECESSOR_DENIED"
    PREDECESSOR_INELIGIBLE = "PREDECESSOR_INELIGIBLE"
    CONTEXT_MISMATCH = "CONTEXT_MISMATCH"
    PROVENANCE_MISSING = "PROVENANCE_MISSING"
    PROVENANCE_INVALID = "PROVENANCE_INVALID"


class EmpiricalRStateV1(str, Enum):
    DECLARED_EXACT = "declared_exact"
    EMPIRICAL = "empirical"
    TYPED_UNAVAILABLE = "typed_unavailable"
    BLOCKED = "BLOCKED"


class RunPathModeV1(str, Enum):
    NEW_SEMANTIC_ROOT = "new_semantic_root"
    LEGACY_READ_ONLY = "legacy_read_only"


DIRECT_PREREQUISITE: Final[Mapping[PathIActionKind, PathIActionKind | None]] = (
    MappingProxyType(
        {
            PathIActionKind.DATA_LAKE_READ: None,
            PathIActionKind.MULTI_TRIAL_RUNTIME_AND_WORKSPACE_WRITE: (
                PathIActionKind.DATA_LAKE_READ
            ),
            PathIActionKind.TRIAL_RETURN_GENERATION: (
                PathIActionKind.MULTI_TRIAL_RUNTIME_AND_WORKSPACE_WRITE
            ),
            PathIActionKind.EMPIRICAL_R_COMPUTATION: (
                PathIActionKind.TRIAL_RETURN_GENERATION
            ),
            PathIActionKind.NAS_REPLICA_SYNC: (
                PathIActionKind.TRIAL_RETURN_GENERATION
            ),
            PathIActionKind.EXECUTION_PULL_VERIFY_MATERIALIZE: (
                PathIActionKind.NAS_REPLICA_SYNC
            ),
        }
    )
)

ACTION_ENFORCEMENT_POINTS: Final[Mapping[PathIActionKind, str]] = MappingProxyType(
    {
        PathIActionKind.DATA_LAKE_READ: "before_data_release_dereference",
        PathIActionKind.MULTI_TRIAL_RUNTIME_AND_WORKSPACE_WRITE: (
            "before_runner_launch_or_workspace_write"
        ),
        PathIActionKind.TRIAL_RETURN_GENERATION: "before_first_candidate_byte",
        PathIActionKind.EMPIRICAL_R_COMPUTATION: "before_estimator_entry",
        PathIActionKind.NAS_REPLICA_SYNC: "before_nas_staging_or_pointer",
        PathIActionKind.EXECUTION_PULL_VERIFY_MATERIALIZE: (
            "before_nas_read_execution_staging_or_pointer"
        ),
    }
)

_EXPECTED_PROVENANCE: Final[
    Mapping[PathIActionKind, ActionPrerequisiteProvenanceV1]
] = MappingProxyType(
    {
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
    }
)


@dataclass(frozen=True, slots=True)
class ActionScopeContextV1:
    schema_version: str
    scope_revision: str
    scope_sha256: str
    release_id: str
    run_id: str
    family_id: str
    target_kind: ActionTargetKindV1

    def __post_init__(self) -> None:
        if self.schema_version != GOVERNANCE_SCHEMA_VERSION:
            raise PathIGovernanceError("schema_version 非 path-i-governance.v1")
        for name in ("scope_revision", "release_id", "run_id", "family_id"):
            _require_identifier(name, getattr(self, name))
        _require_sha256("scope_sha256", self.scope_sha256)
        object.__setattr__(
            self,
            "target_kind",
            _require_enum(ActionTargetKindV1, self.target_kind, "TARGET_KIND_INVALID"),
        )


@dataclass(frozen=True, slots=True)
class ActionAuthorizationRequestV1:
    action_kind: PathIActionKind
    logical_path: str
    context: ActionScopeContextV1

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "action_kind",
            _require_enum(PathIActionKind, self.action_kind, "ACTION_MISMATCH"),
        )
        if not isinstance(self.context, ActionScopeContextV1):
            raise PathIGovernanceError("request context 类型无效")


@dataclass(frozen=True, slots=True)
class ActionAuthorizationRecordV1:
    authorization_id: str
    action_kind: PathIActionKind
    owner: str
    scope_revision: str
    scope_sha256: str
    allowed_logical_paths: tuple[str, ...]
    denied_logical_paths: tuple[str, ...]
    valid_from: datetime
    expires_at: datetime
    revoked_at: datetime | None
    approval_ref: str
    evidence_ref: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "action_kind",
            _require_enum(PathIActionKind, self.action_kind, "ACTION_MISMATCH"),
        )
        object.__setattr__(
            self,
            "allowed_logical_paths",
            tuple(sorted(set(self.allowed_logical_paths))),
        )
        object.__setattr__(
            self,
            "denied_logical_paths",
            tuple(sorted(set(self.denied_logical_paths))),
        )


@dataclass(frozen=True, slots=True)
class ActionPrerequisiteEvidenceV1:
    predecessor_action_kind: PathIActionKind
    authorization_id: str
    authorized: bool
    eligible_to_execute: bool
    context: ActionScopeContextV1
    provenance_kind: ActionPrerequisiteProvenanceV1
    logical_uri: str
    content_sha256: str
    manifest_sha256: str
    evidence_ref: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "predecessor_action_kind",
            _require_enum(
                PathIActionKind,
                self.predecessor_action_kind,
                "PROVENANCE_INVALID",
            ),
        )
        object.__setattr__(
            self,
            "provenance_kind",
            _require_enum(
                ActionPrerequisiteProvenanceV1,
                self.provenance_kind,
                "PROVENANCE_INVALID",
            ),
        )


@dataclass(frozen=True, slots=True)
class ActionDecisionV1:
    schema_version: str
    action_kind: PathIActionKind
    authorization_id: str
    decision_origin: ActionDecisionOriginV1
    authorized: bool
    eligible_to_execute: bool
    reason_codes: tuple[ActionReasonCodeV1, ...]
    scope_revision: str
    scope_sha256: str
    release_id: str
    run_id: str
    family_id: str
    target_kind: ActionTargetKindV1
    approval_ref: str
    evidence_ref: str
    evaluated_at: datetime

    def __post_init__(self) -> None:
        _validate_action_decision_invariants(self)


@dataclass(frozen=True, slots=True)
class EmpiricalRInputsV1:
    declared_fixture_matrix: bool
    source_available: bool
    sealed_provenance_complete: bool
    alignment_complete: bool
    method_version_ref: str
    method_hash_valid: bool
    compute_decision: ActionDecisionV1 | None
    integrity_conflict: bool
    unapproved_repair: bool
    independently_verified: bool


@dataclass(frozen=True, slots=True)
class EmpiricalRDispositionV1:
    state: EmpiricalRStateV1
    reason_codes: tuple[str, ...]
    method_version_ref: str
    computation_authorization_ref: str
    positive_effective_count: bool
    c1_computable: bool


@dataclass(frozen=True, slots=True)
class RunPathIntentV1:
    mode: RunPathModeV1
    logical_root: str
    requested_operation: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "mode",
            _require_enum(RunPathModeV1, self.mode, "RUN_PATH_MODE_INVALID"),
        )


@dataclass(frozen=True, slots=True)
class RunPathDecisionV1:
    mode: RunPathModeV1
    logical_root: str
    writable: bool
    reason_codes: tuple[str, ...]
    delivery_status: str


@dataclass(frozen=True, slots=True)
class SignatureKeySlotV1:
    signature: str
    key_id: str


@dataclass(frozen=True, slots=True)
class ValidityWindowSlotV1:
    valid_from: datetime
    valid_until: datetime


@dataclass(frozen=True, slots=True)
class SignalBatchBoundaryV1:
    schema_version: str
    batch_id: str
    strategy_id: str
    strategy_package_hash: str
    content_sha256: str
    signature_key: SignatureKeySlotV1
    validity_window: ValidityWindowSlotV1
    sequence_no: int


@dataclass(frozen=True, slots=True)
class PathIClaimCeilingV1:
    path_i_design_ready: bool
    stage3_entry_ready: bool = False
    c1_computable: bool = False
    real_data_authorized: bool = False
    multi_trial_runtime_authorized: bool = False
    signal_transport_authorized: bool = False

    def __post_init__(self) -> None:
        _validate_claim_ceiling(self)


def evaluate_action_decision(
    request: ActionAuthorizationRequestV1,
    record: ActionAuthorizationRecordV1 | None,
    predecessor_evidence: tuple[ActionPrerequisiteEvidenceV1, ...] = (),
    *,
    decision_origin: ActionDecisionOriginV1,
    evaluated_at: datetime,
) -> ActionDecisionV1:
    """按 own record、直接前置与上下文顺序执行单动作 fail-closed 判定。"""

    if not isinstance(request, ActionAuthorizationRequestV1):
        raise PathIGovernanceError("request 类型无效")
    origin = _require_enum(
        ActionDecisionOriginV1,
        decision_origin,
        ActionReasonCodeV1.DECISION_ORIGIN_INVALID.value,
    )
    evaluated_at_utc = _require_aware_datetime("evaluated_at", evaluated_at)

    if origin is ActionDecisionOriginV1.APPROVED_LEDGER:
        return _make_decision(
            request,
            record,
            origin,
            evaluated_at_utc,
            authorized=False,
            eligible=False,
            reason=ActionReasonCodeV1.APPROVED_LEDGER_ADAPTER_UNAVAILABLE,
        )

    if request.context.target_kind is not ActionTargetKindV1.REPOSITORY_FIXTURE:
        return _make_decision(
            request,
            record,
            origin,
            evaluated_at_utc,
            authorized=False,
            eligible=False,
            reason=ActionReasonCodeV1.ORIGIN_TARGET_MISMATCH,
        )
    if not _is_repository_fixture_uri(request.logical_path):
        return _make_decision(
            request,
            record,
            origin,
            evaluated_at_utc,
            authorized=False,
            eligible=False,
            reason=ActionReasonCodeV1.FIXTURE_URI_REQUIRED,
        )

    own_reason = _evaluate_own_record(request, record, evaluated_at_utc)
    if own_reason is not None:
        return _make_decision(
            request,
            record,
            origin,
            evaluated_at_utc,
            authorized=False,
            eligible=False,
            reason=own_reason,
        )

    expected_predecessor = DIRECT_PREREQUISITE[request.action_kind]
    if expected_predecessor is None:
        return _make_decision(
            request,
            record,
            origin,
            evaluated_at_utc,
            authorized=True,
            eligible=True,
            reason=ActionReasonCodeV1.ALLOW,
        )

    predecessor_reason = _evaluate_predecessor(
        request,
        predecessor_evidence,
        expected_predecessor,
    )
    return _make_decision(
        request,
        record,
        origin,
        evaluated_at_utc,
        authorized=True,
        eligible=predecessor_reason is None,
        reason=predecessor_reason or ActionReasonCodeV1.ALLOW,
    )


def require_action_eligible(
    decision: ActionDecisionV1,
    *,
    expected_kind: PathIActionKind,
    expected_context: ActionScopeContextV1,
    expected_origin: ActionDecisionOriginV1 | None = None,
) -> None:
    """consumer 必须在 first side effect 前调用的无副作用 guard。"""

    if not isinstance(decision, ActionDecisionV1):
        raise PathIEligibilityError("decision 类型无效")
    _validate_action_decision_invariants(
        decision,
        error_type=PathIEligibilityError,
    )
    kind = _require_enum(PathIActionKind, expected_kind, "ACTION_MISMATCH")
    if expected_origin is not None:
        origin = _require_enum(
            ActionDecisionOriginV1,
            expected_origin,
            "DECISION_ORIGIN_INVALID",
        )
        if decision.decision_origin is not origin:
            raise PathIEligibilityError("decision origin 不匹配")
    if decision.action_kind is not kind:
        raise PathIEligibilityError("action kind 不匹配")
    if not _decision_context_matches(decision, expected_context):
        raise PathIEligibilityError("decision context 不匹配")
    if not decision.authorized or not decision.eligible_to_execute:
        raise PathIEligibilityError("action 未取得执行资格")


def classify_empirical_r(inputs: EmpiricalRInputsV1) -> EmpiricalRDispositionV1:
    """只分类 empirical-R disposition；不计算 R 或有效计数。"""

    if not isinstance(inputs, EmpiricalRInputsV1):
        raise PathIGovernanceError("empirical inputs 类型无效")
    if inputs.integrity_conflict or inputs.unapproved_repair:
        return EmpiricalRDispositionV1(
            state=EmpiricalRStateV1.BLOCKED,
            reason_codes=("INTEGRITY_CONFLICT",),
            method_version_ref=inputs.method_version_ref,
            computation_authorization_ref="",
            positive_effective_count=False,
            c1_computable=False,
        )
    if inputs.declared_fixture_matrix:
        return EmpiricalRDispositionV1(
            state=EmpiricalRStateV1.DECLARED_EXACT,
            reason_codes=("DECLARED_FIXTURE_ONLY",),
            method_version_ref=inputs.method_version_ref,
            computation_authorization_ref="",
            positive_effective_count=False,
            c1_computable=False,
        )
    compute_eligible = (
        inputs.compute_decision is not None
        and inputs.compute_decision.action_kind
        is PathIActionKind.EMPIRICAL_R_COMPUTATION
        and inputs.compute_decision.authorized
        and inputs.compute_decision.eligible_to_execute
    )
    empirical_ready = all(
        (
            inputs.source_available,
            inputs.sealed_provenance_complete,
            inputs.alignment_complete,
            bool(inputs.method_version_ref),
            inputs.method_hash_valid,
            compute_eligible,
            inputs.independently_verified,
        )
    )
    if empirical_ready:
        return EmpiricalRDispositionV1(
            state=EmpiricalRStateV1.EMPIRICAL,
            reason_codes=("EMPIRICAL_PREREQUISITES_COMPLETE",),
            method_version_ref=inputs.method_version_ref,
            computation_authorization_ref=(
                inputs.compute_decision.authorization_id
                if inputs.compute_decision is not None
                else ""
            ),
            positive_effective_count=False,
            c1_computable=False,
        )
    return EmpiricalRDispositionV1(
        state=EmpiricalRStateV1.TYPED_UNAVAILABLE,
        reason_codes=("EMPIRICAL_PREREQUISITE_UNAVAILABLE",),
        method_version_ref=inputs.method_version_ref,
        computation_authorization_ref="",
        positive_effective_count=False,
        c1_computable=False,
    )


def decide_run_path(intent: RunPathIntentV1) -> RunPathDecisionV1:
    """返回 contract-only 路径决定，不读取或创建真实目录。"""

    if not isinstance(intent, RunPathIntentV1):
        raise PathIGovernanceError("run path intent 类型无效")
    if intent.mode is RunPathModeV1.NEW_SEMANTIC_ROOT:
        if (
            intent.logical_root != NEW_RUN_LOGICAL_ROOT_TEMPLATE
            or intent.requested_operation != "contract"
        ):
            raise PathIGovernanceError("新路径仅允许 exact contract intent")
        return RunPathDecisionV1(
            mode=intent.mode,
            logical_root=intent.logical_root,
            writable=False,
            reason_codes=("NEW_PATH_CONTRACT_READY",),
            delivery_status=RUN_PATH_DELIVERY_STATUS,
        )
    if (
        intent.logical_root != LEGACY_RUN_LOGICAL_ROOT_TEMPLATE
        or intent.requested_operation != "read"
    ):
        raise PathIGovernanceError("legacy 路径只允许 exact read-only audit")
    return RunPathDecisionV1(
        mode=intent.mode,
        logical_root=intent.logical_root,
        writable=False,
        reason_codes=("LEGACY_READ_ONLY",),
        delivery_status=RUN_PATH_DELIVERY_STATUS,
    )


def validate_signal_batch_boundary(
    boundary: SignalBatchBoundaryV1,
) -> SignalBatchBoundaryV1:
    """校验八个语义槽；不产生 wire、mailbox 或 transport 对象。"""

    if not isinstance(boundary, SignalBatchBoundaryV1):
        raise PathIGovernanceError("signal boundary 类型无效")
    if boundary.schema_version != "signal-batch-boundary.v1":
        raise PathIGovernanceError("signal schema_version 无效")
    for name in ("batch_id", "strategy_id"):
        _require_identifier(name, getattr(boundary, name))
    _require_sha256("strategy_package_hash", boundary.strategy_package_hash)
    _require_sha256("content_sha256", boundary.content_sha256)
    if not isinstance(boundary.signature_key, SignatureKeySlotV1):
        raise PathIGovernanceError("signature/key_id 复合槽无效")
    if not boundary.signature_key.signature or not boundary.signature_key.key_id:
        raise PathIGovernanceError("signature/key_id 不能为空")
    if _contains_secret_marker(boundary.signature_key.key_id):
        raise PathIGovernanceError("key_id 不得携带 credential 语义")
    if not isinstance(boundary.validity_window, ValidityWindowSlotV1):
        raise PathIGovernanceError("validity window 复合槽无效")
    valid_from = _require_aware_datetime(
        "valid_from", boundary.validity_window.valid_from
    )
    valid_until = _require_aware_datetime(
        "valid_until", boundary.validity_window.valid_until
    )
    if valid_from >= valid_until:
        raise PathIGovernanceError("valid_from 必须早于 valid_until")
    if (
        isinstance(boundary.sequence_no, bool)
        or not isinstance(boundary.sequence_no, int)
        or boundary.sequence_no < 0
    ):
        raise PathIGovernanceError("sequence_no 必须为非负整数")
    return boundary


def enforce_path_i_claim_ceiling(
    claim: PathIClaimCeilingV1,
) -> PathIClaimCeilingV1:
    """确保五项高阶声明始终为 false。"""

    if not isinstance(claim, PathIClaimCeilingV1):
        raise PathIGovernanceError("claim 类型无效")
    _validate_claim_ceiling(claim)
    return claim


def _evaluate_own_record(
    request: ActionAuthorizationRequestV1,
    record: ActionAuthorizationRecordV1 | None,
    evaluated_at: datetime,
) -> ActionReasonCodeV1 | None:
    if record is None:
        return ActionReasonCodeV1.RECORD_MISSING
    if not isinstance(record, ActionAuthorizationRecordV1):
        return ActionReasonCodeV1.RECORD_INVALID
    if not _record_is_structurally_valid(record):
        return ActionReasonCodeV1.RECORD_INVALID
    if record.action_kind is not request.action_kind:
        return ActionReasonCodeV1.ACTION_MISMATCH
    valid_from = record.valid_from.astimezone(timezone.utc)
    expires_at = record.expires_at.astimezone(timezone.utc)
    if evaluated_at < valid_from:
        return ActionReasonCodeV1.NOT_YET_VALID
    if evaluated_at >= expires_at:
        return ActionReasonCodeV1.EXPIRED
    if record.revoked_at is not None:
        revoked_at = record.revoked_at.astimezone(timezone.utc)
        if revoked_at <= evaluated_at:
            return ActionReasonCodeV1.REVOKED
    if (
        record.scope_revision != request.context.scope_revision
        or record.scope_sha256 != request.context.scope_sha256
    ):
        return ActionReasonCodeV1.SCOPE_MISMATCH
    if not _is_canonical_logical_uri(request.logical_path):
        return ActionReasonCodeV1.PATH_INVALID
    if any(
        _path_matches_prefix(request.logical_path, denied)
        for denied in record.denied_logical_paths
    ):
        return ActionReasonCodeV1.PATH_DENIED
    if not any(
        _path_matches_prefix(request.logical_path, allowed)
        for allowed in record.allowed_logical_paths
    ):
        return ActionReasonCodeV1.PATH_NOT_ALLOWED
    return None


def _record_is_structurally_valid(record: ActionAuthorizationRecordV1) -> bool:
    try:
        for name in ("authorization_id", "owner"):
            _require_identifier(name, getattr(record, name))
        _require_identifier("scope_revision", record.scope_revision)
        _require_sha256("scope_sha256", record.scope_sha256)
        if not record.approval_ref or not record.evidence_ref:
            return False
        valid_from = _require_aware_datetime("valid_from", record.valid_from)
        expires_at = _require_aware_datetime("expires_at", record.expires_at)
        if valid_from >= expires_at:
            return False
        if record.revoked_at is not None:
            _require_aware_datetime("revoked_at", record.revoked_at)
        if not record.allowed_logical_paths:
            return False
        if not all(
            _is_canonical_logical_uri(path)
            for path in record.allowed_logical_paths + record.denied_logical_paths
        ):
            return False
    except (PathIGovernanceError, TypeError):
        return False
    return True


def _evaluate_predecessor(
    request: ActionAuthorizationRequestV1,
    predecessor_evidence: tuple[ActionPrerequisiteEvidenceV1, ...],
    expected_predecessor: PathIActionKind,
) -> ActionReasonCodeV1 | None:
    if not predecessor_evidence:
        return ActionReasonCodeV1.PREDECESSOR_MISSING
    if len(predecessor_evidence) != 1:
        return ActionReasonCodeV1.PROVENANCE_INVALID
    evidence = predecessor_evidence[0]
    if not isinstance(evidence, ActionPrerequisiteEvidenceV1):
        return ActionReasonCodeV1.PROVENANCE_INVALID
    if evidence.predecessor_action_kind is not expected_predecessor:
        return ActionReasonCodeV1.PROVENANCE_INVALID
    if not evidence.authorized:
        return ActionReasonCodeV1.PREDECESSOR_DENIED
    if not evidence.eligible_to_execute:
        return ActionReasonCodeV1.PREDECESSOR_INELIGIBLE
    if not _contexts_equal(evidence.context, request.context):
        return ActionReasonCodeV1.CONTEXT_MISMATCH
    expected_provenance = _EXPECTED_PROVENANCE[request.action_kind]
    if evidence.provenance_kind is not expected_provenance:
        return ActionReasonCodeV1.PROVENANCE_INVALID
    if not evidence.authorization_id or not evidence.evidence_ref:
        return ActionReasonCodeV1.PROVENANCE_MISSING
    if not _is_repository_fixture_uri(evidence.logical_uri):
        return ActionReasonCodeV1.PROVENANCE_INVALID
    artifact_provenance = expected_provenance in {
        ActionPrerequisiteProvenanceV1.SEALED_TRIAL_RETURN,
        ActionPrerequisiteProvenanceV1.VERIFIED_REPLICA_RECEIPT,
    }
    if artifact_provenance:
        if not (
            _is_sha256(evidence.content_sha256)
            and _is_sha256(evidence.manifest_sha256)
        ):
            return ActionReasonCodeV1.PROVENANCE_MISSING
    elif evidence.content_sha256 or evidence.manifest_sha256:
        return ActionReasonCodeV1.PROVENANCE_INVALID
    return None


def _make_decision(
    request: ActionAuthorizationRequestV1,
    record: ActionAuthorizationRecordV1 | None,
    origin: ActionDecisionOriginV1,
    evaluated_at: datetime,
    *,
    authorized: bool,
    eligible: bool,
    reason: ActionReasonCodeV1,
) -> ActionDecisionV1:
    valid_record = record if isinstance(record, ActionAuthorizationRecordV1) else None
    return ActionDecisionV1(
        schema_version=GOVERNANCE_SCHEMA_VERSION,
        action_kind=request.action_kind,
        authorization_id=valid_record.authorization_id if valid_record else "",
        decision_origin=origin,
        authorized=authorized,
        eligible_to_execute=eligible,
        reason_codes=(reason,),
        scope_revision=request.context.scope_revision,
        scope_sha256=request.context.scope_sha256,
        release_id=request.context.release_id,
        run_id=request.context.run_id,
        family_id=request.context.family_id,
        target_kind=request.context.target_kind,
        approval_ref=valid_record.approval_ref if valid_record else "",
        evidence_ref=valid_record.evidence_ref if valid_record else "",
        evaluated_at=evaluated_at,
    )


def _contexts_equal(
    left: ActionScopeContextV1, right: ActionScopeContextV1
) -> bool:
    return (
        left.schema_version,
        left.scope_revision,
        left.scope_sha256,
        left.release_id,
        left.run_id,
        left.family_id,
        left.target_kind,
    ) == (
        right.schema_version,
        right.scope_revision,
        right.scope_sha256,
        right.release_id,
        right.run_id,
        right.family_id,
        right.target_kind,
    )


def _decision_context_matches(
    decision: ActionDecisionV1, context: ActionScopeContextV1
) -> bool:
    return (
        decision.schema_version,
        decision.scope_revision,
        decision.scope_sha256,
        decision.release_id,
        decision.run_id,
        decision.family_id,
        decision.target_kind,
    ) == (
        context.schema_version,
        context.scope_revision,
        context.scope_sha256,
        context.release_id,
        context.run_id,
        context.family_id,
        context.target_kind,
    )


def _validate_action_decision_invariants(
    decision: ActionDecisionV1,
    *,
    error_type: type[PathIGovernanceError] = PathIGovernanceError,
) -> None:
    """校验所有 ActionDecisionV1 构造方与 consumer 共用的唯一不变量。"""

    def fail(message: str) -> None:
        raise error_type(message)

    if not isinstance(decision, ActionDecisionV1):
        fail("decision 类型无效")
    if decision.schema_version != GOVERNANCE_SCHEMA_VERSION:
        fail("decision schema_version 无效")
    if not isinstance(decision.action_kind, PathIActionKind):
        fail("decision action kind 无效")
    if not isinstance(decision.decision_origin, ActionDecisionOriginV1):
        fail("decision origin 无效")
    if not isinstance(decision.target_kind, ActionTargetKindV1):
        fail("decision target kind 无效")
    if (
        type(decision.authorized) is not bool
        or type(decision.eligible_to_execute) is not bool
    ):
        fail("decision authorization flags 必须为 bool")
    if decision.eligible_to_execute and not decision.authorized:
        fail("eligible_to_execute 必须蕴含 authorized")
    if (
        not isinstance(decision.reason_codes, tuple)
        or len(decision.reason_codes) != 1
        or not isinstance(decision.reason_codes[0], ActionReasonCodeV1)
    ):
        fail("decision reason_codes 必须包含唯一稳定 reason")
    reason = decision.reason_codes[0]
    try:
        for name in ("scope_revision", "release_id", "run_id", "family_id"):
            _require_identifier(name, getattr(decision, name))
        _require_sha256("scope_sha256", decision.scope_sha256)
        _require_aware_datetime("evaluated_at", decision.evaluated_at)
    except PathIGovernanceError as exc:
        raise error_type(str(exc)) from exc

    if decision.decision_origin is ActionDecisionOriginV1.APPROVED_LEDGER:
        if (
            decision.authorized
            or decision.eligible_to_execute
            or reason
            is not ActionReasonCodeV1.APPROVED_LEDGER_ADAPTER_UNAVAILABLE
        ):
            fail("approved_ledger current-v1 必须为唯一 unavailable hard deny")
        return

    if decision.target_kind is ActionTargetKindV1.REAL_OPERATION:
        if (
            decision.authorized
            or decision.eligible_to_execute
            or reason is not ActionReasonCodeV1.ORIGIN_TARGET_MISMATCH
        ):
            fail("repository_fixture 与 real_operation 只能形成 typed deny")
        return

    executable_refs = (
        decision.authorization_id,
        decision.approval_ref,
        decision.evidence_ref,
    )
    if decision.authorized and not all(executable_refs):
        fail("authorized decision 必须保留非空 authorization/approval/evidence refs")

    predecessor_denials = {
        ActionReasonCodeV1.PREDECESSOR_MISSING,
        ActionReasonCodeV1.PREDECESSOR_DENIED,
        ActionReasonCodeV1.PREDECESSOR_INELIGIBLE,
        ActionReasonCodeV1.CONTEXT_MISMATCH,
        ActionReasonCodeV1.PROVENANCE_MISSING,
        ActionReasonCodeV1.PROVENANCE_INVALID,
    }
    own_denials = {
        ActionReasonCodeV1.RECORD_MISSING,
        ActionReasonCodeV1.RECORD_INVALID,
        ActionReasonCodeV1.ACTION_MISMATCH,
        ActionReasonCodeV1.NOT_YET_VALID,
        ActionReasonCodeV1.EXPIRED,
        ActionReasonCodeV1.REVOKED,
        ActionReasonCodeV1.SCOPE_MISMATCH,
        ActionReasonCodeV1.PATH_INVALID,
        ActionReasonCodeV1.PATH_DENIED,
        ActionReasonCodeV1.PATH_NOT_ALLOWED,
        ActionReasonCodeV1.FIXTURE_URI_REQUIRED,
    }
    if reason is ActionReasonCodeV1.ORIGIN_TARGET_MISMATCH:
        fail("repository_fixture target 不得使用 origin-target mismatch reason")
    if decision.eligible_to_execute:
        if reason is not ActionReasonCodeV1.ALLOW:
            fail("eligible decision 必须且只能使用 ALLOW reason")
    elif decision.authorized:
        if reason not in predecessor_denials:
            fail("authorized but ineligible decision 必须使用直接前置 deny reason")
    elif reason not in own_denials:
        fail("unauthorized decision 必须使用 own-record/origin/path deny reason")
    if reason is ActionReasonCodeV1.RECORD_MISSING and any(executable_refs):
        fail("RECORD_MISSING decision 不得携带 record refs")


def _require_enum(enum_type: type[Enum], value: object, code: str) -> Enum:
    if isinstance(value, enum_type):
        return value
    try:
        return enum_type(value)
    except (TypeError, ValueError) as exc:
        raise PathIGovernanceError(code) from exc


def _require_identifier(name: str, value: object) -> None:
    if not isinstance(value, str) or not _IDENTIFIER_RE.fullmatch(value):
        raise PathIGovernanceError(f"{name} 不是受限 identifier")
    if value.startswith("/") or ".." in value.split("/"):
        raise PathIGovernanceError(f"{name} 不得包含绝对路径或上级段")


def _require_sha256(name: str, value: object) -> None:
    if not isinstance(value, str) or not _SHA256_RE.fullmatch(value):
        raise PathIGovernanceError(f"{name} 不是 lowercase sha256")


def _is_sha256(value: str) -> bool:
    return bool(_SHA256_RE.fullmatch(value))


def _require_aware_datetime(name: str, value: object) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None:
        raise PathIGovernanceError(f"{name} 必须是 tz-aware datetime")
    if value.utcoffset() is None:
        raise PathIGovernanceError(f"{name} 必须包含有效 UTC offset")
    return value.astimezone(timezone.utc)


def _canonical_logical_uri(value: object) -> str | None:
    """返回 v1 唯一 URI 表示；任何 percent-encoding 均 fail closed。"""

    if not isinstance(value, str) or not value or not value.isascii():
        return None
    if "%" in value or "\\" in value:
        return None
    if any(marker in value for marker in ("*", "?", "#")):
        return None
    try:
        parsed = urlsplit(value)
        _ = parsed.port
    except ValueError:
        return None
    if not parsed.scheme or not parsed.netloc:
        return None
    if not value.startswith(f"{parsed.scheme}://"):
        return None
    if parsed.scheme != parsed.scheme.lower() or parsed.netloc != parsed.netloc.lower():
        return None
    if parsed.username is not None or parsed.password is not None:
        return None
    if parsed.query or parsed.fragment:
        return None
    if not parsed.path.startswith("/"):
        return None
    if any(part in {"", ".", ".."} for part in parsed.path.split("/")[1:]):
        return None
    if _contains_secret_marker(value):
        return None
    return value


def _is_canonical_logical_uri(value: object) -> bool:
    return _canonical_logical_uri(value) is not None


def _is_repository_fixture_uri(value: object) -> bool:
    canonical = _canonical_logical_uri(value)
    if canonical is None:
        return False
    parsed = urlsplit(canonical)
    return (
        parsed.scheme == "fixture"
        and parsed.hostname in _FIXTURE_AUTHORITIES
        and parsed.port is None
    )


def _path_matches_prefix(logical_path: str, prefix: str) -> bool:
    canonical_path = _canonical_logical_uri(logical_path)
    canonical_prefix = _canonical_logical_uri(prefix)
    if canonical_path is None or canonical_prefix is None:
        return False
    normalized_prefix = canonical_prefix.rstrip("/")
    return canonical_path == normalized_prefix or canonical_path.startswith(
        normalized_prefix + "/"
    )


def _contains_secret_marker(value: str) -> bool:
    lowered = value.lower()
    return any(marker in lowered for marker in _SECRET_MARKERS)


def _validate_claim_ceiling(claim: PathIClaimCeilingV1) -> None:
    high_order_values = (
        claim.stage3_entry_ready,
        claim.c1_computable,
        claim.real_data_authorized,
        claim.multi_trial_runtime_authorized,
        claim.signal_transport_authorized,
    )
    if any(value is not False for value in high_order_values):
        raise PathIGovernanceError("PATH-I 五项高阶 claim 必须全部为 false")


def _validate_dag() -> None:
    if set(DIRECT_PREREQUISITE) != set(PathIActionKind):
        raise RuntimeError("PATH-I DAG nodes 必须为 6/6")
    if set(ACTION_ENFORCEMENT_POINTS) != set(PathIActionKind):
        raise RuntimeError("PATH-I enforcement points 必须为 6/6")
    edges = tuple(value for value in DIRECT_PREREQUISITE.values() if value is not None)
    if len(edges) != 5 or any(value not in PathIActionKind for value in edges):
        raise RuntimeError("PATH-I DAG edges 必须为 5/5")
    for node in PathIActionKind:
        seen: set[PathIActionKind] = set()
        cursor: PathIActionKind | None = node
        while cursor is not None:
            if cursor in seen:
                raise RuntimeError("PATH-I DAG 不得包含环")
            seen.add(cursor)
            cursor = DIRECT_PREREQUISITE[cursor]


_validate_dag()
