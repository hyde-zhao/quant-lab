"""Repository-local execution cache materialization v1 纯合同。

本模块只消费显式传入的 repository fixture 授权、S03 current distribution
selection 与 S02 verifier-library。它不读取环境、凭据、网络、真实 NAS 或执行机，
也不实现 runtime consumer、seal/digest facade 或任何上游 pointer 写入。
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib
import hmac
import json
import re
from typing import Final, Mapping
from urllib.parse import urlsplit

from engine.path_i_governance import (
    ActionDecisionOriginV1,
    ActionDecisionV1,
    ActionScopeContextV1,
    ActionTargetKindV1,
    PathIActionKind,
    require_action_eligible,
)
from engine.research_artifact_replica import (
    DistributionSelectionV1,
    ReplicaStoragePortV1,
    ReplicaVerificationReceiptV1,
)
from engine.trial_return_artifact import (
    ResearchCanonicalSelectionV1,
    SealedTrialReturnBundleV1,
    VerifiedTrialReturnBundleV1,
    verify_sealed_trial_return_bundle,
)


__all__ = (
    "ExecutionMaterializationRequestV1",
    "ExecutionDeploymentMappingV1",
    "ExecutionStagingTokenV1",
    "MaterializationVerificationVectorV1",
    "MaterializationReceiptV1",
    "ExecutionCacheSelectionV1",
    "ExecutionLocalCacheHandleV1",
    "MaterializationPreflightV1",
    "VerifiedCacheCandidateV1",
    "MaterializationResultV1",
    "MaterializationStatusV1",
    "MaterializationBlockReasonV1",
    "MaterializationStoragePortV1",
    "MaterializationStoragePortError",
    "canonical_materialization_receipt_bytes",
    "validate_materialization_preflight",
    "pull_and_verify_execution_staging",
    "commit_execution_cache",
    "resolve_execution_local_handle",
    "materialize_repository_fixture_execution_cache",
)


MATERIALIZATION_REQUEST_VERSION: Final = "execution-materialization-request.v1"
MATERIALIZATION_MAPPING_VERSION: Final = (
    "repository-fixture-execution-cache-mapping.v1"
)
MATERIALIZATION_STAGING_VERSION: Final = "execution-staging-token.v1"
MATERIALIZATION_RECEIPT_VERSION: Final = "materialization-receipt.v1"
EXECUTION_CACHE_SELECTION_VERSION: Final = "execution-cache-selection.v1"
MATERIALIZATION_PORT_CAPABILITY_VERSION: Final = (
    "repository-fixture-execution-cache-port.v1"
)
MATERIALIZATION_RECEIPT_HASH_DOMAIN: Final = b"materialization-receipt@v1\x00"
SOURCE_AUTHORITY: Final = "nas_verified_replica"
TARGET_AUTHORITY: Final = "execution_local_cache"
NON_RUNTIME_STAGING_STATE: Final = "non_runtime"
EXECUTION_LOCAL_SOURCE_KIND: Final = "execution_local_immutable_cache"

_SHA256_RE = re.compile(r"sha256:[0-9a-f]{64}\Z")
_IDENTIFIER_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:@/-]*\Z")
_FIXTURE_AUTHORITIES: Final = frozenset({"repository", "memory", "in-memory"})
_FORBIDDEN_REF_MARKERS: Final = (
    "password",
    "passwd",
    "secret",
    "token",
    "credential",
)


class MaterializationContractError(ValueError):
    """输入违反 execution cache materialization v1 合同。"""


class MaterializationStoragePortError(MaterializationContractError):
    """Repository fixture port 拒绝 materialization 操作。"""

    def __init__(self, reason: "MaterializationBlockReasonV1") -> None:
        self.reason = reason
        super().__init__(reason.value)


class MaterializationStatusV1(str, Enum):
    MATERIALIZED = "MATERIALIZED"
    BLOCKED = "BLOCKED"


class MaterializationBlockReasonV1(str, Enum):
    NONE = "NONE"
    AUTHORIZATION_INVALID = "AUTHORIZATION_INVALID"
    COMMIT_AUTHORIZATION_INVALID = "COMMIT_AUTHORIZATION_INVALID"
    COMMIT_DECISION_NOT_FRESH = "COMMIT_DECISION_NOT_FRESH"
    DECISION_ORIGIN_INVALID = "DECISION_ORIGIN_INVALID"
    TARGET_KIND_INVALID = "TARGET_KIND_INVALID"
    CONTEXT_MISMATCH = "CONTEXT_MISMATCH"
    SOURCE_AUTHORITY_INVALID = "SOURCE_AUTHORITY_INVALID"
    TARGET_AUTHORITY_INVALID = "TARGET_AUTHORITY_INVALID"
    PORT_BINDING_INVALID = "PORT_BINDING_INVALID"
    INELIGIBLE_REPLICA_PREDECESSOR = "INELIGIBLE_REPLICA_PREDECESSOR"
    SELECTED_REPLICA_MISMATCH = "SELECTED_REPLICA_MISMATCH"
    STAGING_INTERRUPTED = "STAGING_INTERRUPTED"
    STAGING_INTEGRITY_INVALID = "STAGING_INTEGRITY_INVALID"
    RELEASE_MISMATCH = "RELEASE_MISMATCH"
    MANIFEST_MISMATCH = "MANIFEST_MISMATCH"
    SEAL_MISMATCH = "SEAL_MISMATCH"
    CONTENT_MISMATCH = "CONTENT_MISMATCH"
    VERIFICATION_INCOMPLETE = "VERIFICATION_INCOMPLETE"
    REPLICA_SELECTION_DRIFT = "REPLICA_SELECTION_DRIFT"
    IMMUTABLE_CACHE_CONFLICT = "IMMUTABLE_CACHE_CONFLICT"
    RECEIPT_PERSISTENCE_FAILED = "RECEIPT_PERSISTENCE_FAILED"
    POINTER_CONFLICT = "POINTER_CONFLICT"
    LOCAL_HANDLE_INVALID = "LOCAL_HANDLE_INVALID"


@dataclass(frozen=True, slots=True)
class ExecutionMaterializationRequestV1:
    schema_version: str
    request_id: str
    expected_release_id: str
    expected_logical_uri: str
    expected_content_sha256: str
    expected_manifest_sha256: str
    expected_replica_receipt_sha256: str
    action_context: ActionScopeContextV1
    source_authority: str
    target_authority: str

    def __post_init__(self) -> None:
        if self.schema_version != MATERIALIZATION_REQUEST_VERSION:
            raise MaterializationContractError("REQUEST_VERSION_UNSUPPORTED")
        _require_identifier("request_id", self.request_id)
        _require_identifier("expected_release_id", self.expected_release_id)
        _require_fixture_uri(self.expected_logical_uri)
        for name in (
            "expected_content_sha256",
            "expected_manifest_sha256",
            "expected_replica_receipt_sha256",
        ):
            _require_sha256(name, getattr(self, name))
        if not isinstance(self.action_context, ActionScopeContextV1):
            raise MaterializationContractError("ACTION_CONTEXT_TYPE_INVALID")
        if not isinstance(self.source_authority, str) or not self.source_authority:
            raise MaterializationContractError("SOURCE_AUTHORITY_INVALID")
        if not isinstance(self.target_authority, str) or not self.target_authority:
            raise MaterializationContractError("TARGET_AUTHORITY_INVALID")


@dataclass(frozen=True, slots=True)
class ExecutionDeploymentMappingV1:
    mapping_version: str
    repository_owned: bool
    decision_origin: ActionDecisionOriginV1
    target_kind: ActionTargetKindV1
    logical_uri: str
    replica_handle: str
    staging_handle: str
    cache_handle: str
    pointer_handle: str

    def __post_init__(self) -> None:
        if self.mapping_version != MATERIALIZATION_MAPPING_VERSION:
            raise MaterializationContractError("MAPPING_VERSION_UNSUPPORTED")
        if self.repository_owned is not True:
            raise MaterializationContractError("MAPPING_NOT_REPOSITORY_OWNED")
        if self.decision_origin is not ActionDecisionOriginV1.REPOSITORY_FIXTURE:
            raise MaterializationContractError("MAPPING_ORIGIN_INVALID")
        if self.target_kind is not ActionTargetKindV1.REPOSITORY_FIXTURE:
            raise MaterializationContractError("MAPPING_TARGET_INVALID")
        _require_fixture_uri(self.logical_uri)
        for name in (
            "replica_handle",
            "staging_handle",
            "cache_handle",
            "pointer_handle",
        ):
            _require_relative_handle(name, getattr(self, name))


@dataclass(frozen=True, slots=True)
class ExecutionStagingTokenV1:
    staging_version: str
    request_id: str
    release_id: str
    logical_uri: str
    expected_content_sha256: str
    expected_manifest_sha256: str
    replica_receipt_sha256: str
    replica_selection_revision: int
    state: str

    def __post_init__(self) -> None:
        if self.staging_version != MATERIALIZATION_STAGING_VERSION:
            raise MaterializationContractError("STAGING_VERSION_UNSUPPORTED")
        _require_identifier("request_id", self.request_id)
        _require_identifier("release_id", self.release_id)
        _require_fixture_uri(self.logical_uri)
        for name in (
            "expected_content_sha256",
            "expected_manifest_sha256",
            "replica_receipt_sha256",
        ):
            _require_sha256(name, getattr(self, name))
        if (
            isinstance(self.replica_selection_revision, bool)
            or not isinstance(self.replica_selection_revision, int)
            or self.replica_selection_revision <= 0
        ):
            raise MaterializationContractError("REPLICA_SELECTION_REVISION_INVALID")
        if self.state != NON_RUNTIME_STAGING_STATE:
            raise MaterializationContractError("STAGING_MUST_BE_NON_RUNTIME")


@dataclass(frozen=True, slots=True)
class MaterializationVerificationVectorV1:
    release: bool
    manifest: bool
    seal: bool
    content: bool

    def __post_init__(self) -> None:
        if any(
            type(value) is not bool
            for value in (self.release, self.manifest, self.seal, self.content)
        ):
            raise MaterializationContractError("VERIFICATION_VECTOR_BOOL_REQUIRED")

    @property
    def complete(self) -> bool:
        return all((self.release, self.manifest, self.seal, self.content))


@dataclass(frozen=True, slots=True)
class MaterializationReceiptV1:
    schema_version: str
    authority: str
    release_id: str
    logical_uri: str
    content_sha256: str
    manifest_sha256: str
    original_seal_sha256: str
    replica_receipt_sha256: str
    replica_selection_revision: int
    decision_origin: ActionDecisionOriginV1
    target_kind: ActionTargetKindV1
    verification_vector: MaterializationVerificationVectorV1
    preflight_authorization_evidence_refs: tuple[str, str]
    commit_authorization_evidence_refs: tuple[str, str]
    cache_version_ref: str
    receipt_sha256: str

    def __post_init__(self) -> None:
        if self.schema_version != MATERIALIZATION_RECEIPT_VERSION:
            raise MaterializationContractError("RECEIPT_VERSION_UNSUPPORTED")
        if self.authority != TARGET_AUTHORITY:
            raise MaterializationContractError("RECEIPT_AUTHORITY_INVALID")
        _require_identifier("release_id", self.release_id)
        _require_fixture_uri(self.logical_uri)
        for name in (
            "content_sha256",
            "manifest_sha256",
            "original_seal_sha256",
            "replica_receipt_sha256",
            "receipt_sha256",
        ):
            _require_sha256(name, getattr(self, name))
        if (
            isinstance(self.replica_selection_revision, bool)
            or not isinstance(self.replica_selection_revision, int)
            or self.replica_selection_revision <= 0
        ):
            raise MaterializationContractError("REPLICA_SELECTION_REVISION_INVALID")
        if self.decision_origin is not ActionDecisionOriginV1.REPOSITORY_FIXTURE:
            raise MaterializationContractError("RECEIPT_ORIGIN_INVALID")
        if self.target_kind is not ActionTargetKindV1.REPOSITORY_FIXTURE:
            raise MaterializationContractError("RECEIPT_TARGET_INVALID")
        if not isinstance(
            self.verification_vector, MaterializationVerificationVectorV1
        ) or not self.verification_vector.complete:
            raise MaterializationContractError("VERIFICATION_INCOMPLETE")
        _require_evidence_pair(
            "preflight_authorization_evidence_refs",
            self.preflight_authorization_evidence_refs,
        )
        _require_evidence_pair(
            "commit_authorization_evidence_refs",
            self.commit_authorization_evidence_refs,
        )
        _require_identifier("cache_version_ref", self.cache_version_ref)
        expected = _sha256_prefixed(
            MATERIALIZATION_RECEIPT_HASH_DOMAIN
            + canonical_materialization_receipt_bytes(self)
        )
        if not hmac.compare_digest(expected, self.receipt_sha256):
            raise MaterializationContractError("RECEIPT_DIGEST_MISMATCH")


@dataclass(frozen=True, slots=True)
class ExecutionCacheSelectionV1:
    selection_version: str
    release_id: str
    logical_uri: str
    content_sha256: str
    manifest_sha256: str
    original_seal_sha256: str
    replica_receipt_sha256: str
    materialization_receipt_sha256: str
    cache_version_ref: str
    selection_revision: int
    decision_origin: ActionDecisionOriginV1
    target_kind: ActionTargetKindV1
    source_kind: str

    def __post_init__(self) -> None:
        if self.selection_version != EXECUTION_CACHE_SELECTION_VERSION:
            raise MaterializationContractError("CACHE_SELECTION_VERSION_UNSUPPORTED")
        _require_identifier("release_id", self.release_id)
        _require_fixture_uri(self.logical_uri)
        for name in (
            "content_sha256",
            "manifest_sha256",
            "original_seal_sha256",
            "replica_receipt_sha256",
            "materialization_receipt_sha256",
        ):
            _require_sha256(name, getattr(self, name))
        _require_identifier("cache_version_ref", self.cache_version_ref)
        if (
            isinstance(self.selection_revision, bool)
            or not isinstance(self.selection_revision, int)
            or self.selection_revision <= 0
        ):
            raise MaterializationContractError("CACHE_SELECTION_REVISION_INVALID")
        if self.decision_origin is not ActionDecisionOriginV1.REPOSITORY_FIXTURE:
            raise MaterializationContractError("CACHE_SELECTION_ORIGIN_INVALID")
        if self.target_kind is not ActionTargetKindV1.REPOSITORY_FIXTURE:
            raise MaterializationContractError("CACHE_SELECTION_TARGET_INVALID")
        if self.source_kind != EXECUTION_LOCAL_SOURCE_KIND:
            raise MaterializationContractError("CACHE_SOURCE_KIND_INVALID")


@dataclass(frozen=True, slots=True)
class ExecutionLocalCacheHandleV1:
    release_id: str
    logical_uri: str
    content_sha256: str
    materialization_receipt_sha256: str
    cache_version_ref: str
    source_kind: str
    local_handle: str

    def __post_init__(self) -> None:
        _require_identifier("release_id", self.release_id)
        _require_fixture_uri(self.logical_uri)
        _require_sha256("content_sha256", self.content_sha256)
        _require_sha256(
            "materialization_receipt_sha256",
            self.materialization_receipt_sha256,
        )
        _require_identifier("cache_version_ref", self.cache_version_ref)
        if self.source_kind != EXECUTION_LOCAL_SOURCE_KIND:
            raise MaterializationContractError("LOCAL_HANDLE_SOURCE_INVALID")
        _require_relative_handle("local_handle", self.local_handle)


@dataclass(frozen=True, slots=True)
class MaterializationPreflightV1:
    request: ExecutionMaterializationRequestV1
    replica_receipt: ReplicaVerificationReceiptV1
    distribution_selection: DistributionSelectionV1
    action_context: ActionScopeContextV1
    preflight_decision: ActionDecisionV1
    preflight_authorization_evidence_refs: tuple[str, str]


@dataclass(frozen=True, slots=True)
class VerifiedCacheCandidateV1:
    preflight: MaterializationPreflightV1
    staging_token: ExecutionStagingTokenV1
    staged_bundle: SealedTrialReturnBundleV1
    source_selection: ResearchCanonicalSelectionV1
    staged_verified: VerifiedTrialReturnBundleV1
    verification_vector: MaterializationVerificationVectorV1
    cache_version_ref: str


@dataclass(frozen=True, slots=True)
class MaterializationResultV1:
    status: MaterializationStatusV1
    reason: MaterializationBlockReasonV1
    receipt: MaterializationReceiptV1 | None
    selection: ExecutionCacheSelectionV1 | None
    handle: ExecutionLocalCacheHandleV1 | None
    previous_selection: ExecutionCacheSelectionV1 | None

    def __post_init__(self) -> None:
        if self.status is MaterializationStatusV1.MATERIALIZED:
            if (
                self.reason is not MaterializationBlockReasonV1.NONE
                or self.receipt is None
                or self.selection is None
                or self.handle is None
            ):
                raise MaterializationContractError("MATERIALIZED_RESULT_INVALID")
        elif (
            self.status is not MaterializationStatusV1.BLOCKED
            or self.reason is MaterializationBlockReasonV1.NONE
            or self.receipt is not None
            or self.selection is not None
            or self.handle is not None
        ):
            raise MaterializationContractError("BLOCKED_RESULT_INVALID")


class MaterializationStoragePortV1:
    """只绑定 repository fixture S03 port；不包含真实 NAS/执行机 adapter。"""

    __slots__ = ("_mapping", "_replica_port", "_pull_calls")

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if "pull_to_staging" in cls.__dict__:
            raise TypeError("pull_to_staging 必须唯一委托 S03 current selection")

    def __init__(
        self,
        mapping: ExecutionDeploymentMappingV1,
        replica_port: ReplicaStoragePortV1,
    ) -> None:
        if not isinstance(mapping, ExecutionDeploymentMappingV1):
            raise MaterializationStoragePortError(
                MaterializationBlockReasonV1.PORT_BINDING_INVALID
            )
        if not isinstance(replica_port, ReplicaStoragePortV1):
            raise MaterializationStoragePortError(
                MaterializationBlockReasonV1.PORT_BINDING_INVALID
            )
        self._mapping = mapping
        self._replica_port = replica_port
        self._pull_calls = 0

    @property
    def mapping(self) -> ExecutionDeploymentMappingV1:
        return self._mapping

    @property
    def replica_port(self) -> ReplicaStoragePortV1:
        return self._replica_port

    @property
    def pull_calls(self) -> int:
        return self._pull_calls

    @property
    def current_selection(self) -> ExecutionCacheSelectionV1 | None:
        raise NotImplementedError

    def pull_to_staging(
        self,
        distribution_selection: DistributionSelectionV1,
        replica_receipt: ReplicaVerificationReceiptV1,
        staging_token: ExecutionStagingTokenV1,
    ) -> tuple[
        ExecutionStagingTokenV1,
        SealedTrialReturnBundleV1,
        ResearchCanonicalSelectionV1,
    ]:
        """只通过 S03 final selected-read contract 取得 typed bytes candidate。"""

        self._pull_calls += 1
        try:
            self._before_selected_read()
        except Exception as exc:
            raise MaterializationStoragePortError(
                MaterializationBlockReasonV1.STAGING_INTERRUPTED
            ) from exc
        try:
            bundle, source_selection, selected_receipt = (
                self._replica_port.read_selected_replica(
                    distribution_selection
                )
            )
        except Exception as exc:
            raise MaterializationStoragePortError(
                MaterializationBlockReasonV1.SELECTED_REPLICA_MISMATCH
            ) from exc
        if selected_receipt != replica_receipt:
            raise MaterializationStoragePortError(
                MaterializationBlockReasonV1.SELECTED_REPLICA_MISMATCH
            )
        return staging_token, bundle, source_selection

    def _before_selected_read(self) -> None:
        """Repository fixture fault-injection seam；不得返回或替代数据。"""

    def persist_immutable_cache(
        self,
        candidate: VerifiedCacheCandidateV1,
        receipt: MaterializationReceiptV1,
    ) -> None:
        raise NotImplementedError

    def read_materialization_receipt(
        self,
        receipt_sha256: str,
    ) -> MaterializationReceiptV1 | None:
        """按 self-hash 精确读取已不可变持久化的 materialization receipt。"""

        raise NotImplementedError

    def compare_and_swap_cache_selection(
        self,
        expected_previous: ExecutionCacheSelectionV1 | None,
        new_selection: ExecutionCacheSelectionV1,
    ) -> bool:
        raise NotImplementedError


def canonical_materialization_receipt_bytes(
    receipt_body: MaterializationReceiptV1 | Mapping[str, object],
) -> bytes:
    """返回排除 self-hash、时间和所有 deployment handle 的 canonical body。"""

    if isinstance(receipt_body, MaterializationReceiptV1):
        values: Mapping[str, object] = {
            "authority": receipt_body.authority,
            "cache_version_ref": receipt_body.cache_version_ref,
            "commit_authorization_evidence_refs": (
                receipt_body.commit_authorization_evidence_refs
            ),
            "content_sha256": receipt_body.content_sha256,
            "decision_origin": receipt_body.decision_origin,
            "logical_uri": receipt_body.logical_uri,
            "manifest_sha256": receipt_body.manifest_sha256,
            "original_seal_sha256": receipt_body.original_seal_sha256,
            "preflight_authorization_evidence_refs": (
                receipt_body.preflight_authorization_evidence_refs
            ),
            "release_id": receipt_body.release_id,
            "replica_receipt_sha256": receipt_body.replica_receipt_sha256,
            "replica_selection_revision": (
                receipt_body.replica_selection_revision
            ),
            "schema_version": receipt_body.schema_version,
            "target_kind": receipt_body.target_kind,
            "verification_vector": {
                "content": receipt_body.verification_vector.content,
                "manifest": receipt_body.verification_vector.manifest,
                "release": receipt_body.verification_vector.release,
                "seal": receipt_body.verification_vector.seal,
            },
        }
    elif isinstance(receipt_body, Mapping):
        values = receipt_body
    else:
        raise MaterializationContractError("RECEIPT_BODY_TYPE_INVALID")
    expected_keys = {
        "authority",
        "cache_version_ref",
        "commit_authorization_evidence_refs",
        "content_sha256",
        "decision_origin",
        "logical_uri",
        "manifest_sha256",
        "original_seal_sha256",
        "preflight_authorization_evidence_refs",
        "release_id",
        "replica_receipt_sha256",
        "replica_selection_revision",
        "schema_version",
        "target_kind",
        "verification_vector",
    }
    if set(values) != expected_keys:
        raise MaterializationContractError("RECEIPT_BODY_FIELDS_INVALID")
    return _canonical_json_bytes(values)


def validate_materialization_preflight(
    request: ExecutionMaterializationRequestV1,
    replica_receipt: ReplicaVerificationReceiptV1,
    distribution_selection: DistributionSelectionV1,
    decision: ActionDecisionV1,
    action_context: ActionScopeContextV1,
) -> MaterializationPreflightV1 | MaterializationResultV1:
    """在任何 selected-replica read 或 staging 前完成 fail-closed guard。"""

    if not isinstance(request, ExecutionMaterializationRequestV1):
        return _blocked(MaterializationBlockReasonV1.CONTEXT_MISMATCH)
    if request.source_authority != SOURCE_AUTHORITY:
        return _blocked(MaterializationBlockReasonV1.SOURCE_AUTHORITY_INVALID)
    if request.target_authority != TARGET_AUTHORITY:
        return _blocked(MaterializationBlockReasonV1.TARGET_AUTHORITY_INVALID)
    if not isinstance(action_context, ActionScopeContextV1):
        return _blocked(MaterializationBlockReasonV1.CONTEXT_MISMATCH)
    if request.action_context != action_context:
        return _blocked(MaterializationBlockReasonV1.CONTEXT_MISMATCH)
    if action_context.target_kind is not ActionTargetKindV1.REPOSITORY_FIXTURE:
        return _blocked(MaterializationBlockReasonV1.TARGET_KIND_INVALID)
    if not isinstance(decision, ActionDecisionV1):
        return _blocked(MaterializationBlockReasonV1.AUTHORIZATION_INVALID)
    if decision.decision_origin is not ActionDecisionOriginV1.REPOSITORY_FIXTURE:
        return _blocked(MaterializationBlockReasonV1.DECISION_ORIGIN_INVALID)
    if decision.target_kind is not ActionTargetKindV1.REPOSITORY_FIXTURE:
        return _blocked(MaterializationBlockReasonV1.TARGET_KIND_INVALID)
    try:
        require_action_eligible(
            decision,
            expected_kind=(
                PathIActionKind.EXECUTION_PULL_VERIFY_MATERIALIZE
            ),
            expected_context=action_context,
            expected_origin=ActionDecisionOriginV1.REPOSITORY_FIXTURE,
        )
    except Exception:
        return _blocked(MaterializationBlockReasonV1.AUTHORIZATION_INVALID)
    try:
        _require_evidence_pair(
            "preflight_authorization_evidence_refs",
            (decision.approval_ref, decision.evidence_ref),
        )
    except MaterializationContractError:
        return _blocked(MaterializationBlockReasonV1.AUTHORIZATION_INVALID)
    if not isinstance(replica_receipt, ReplicaVerificationReceiptV1) or not isinstance(
        distribution_selection, DistributionSelectionV1
    ):
        return _blocked(
            MaterializationBlockReasonV1.INELIGIBLE_REPLICA_PREDECESSOR
        )
    if not _replica_predecessor_matches(
        request,
        replica_receipt,
        distribution_selection,
    ):
        return _blocked(
            MaterializationBlockReasonV1.INELIGIBLE_REPLICA_PREDECESSOR
        )
    return MaterializationPreflightV1(
        request=request,
        replica_receipt=replica_receipt,
        distribution_selection=distribution_selection,
        action_context=action_context,
        preflight_decision=decision,
        preflight_authorization_evidence_refs=(
            decision.approval_ref,
            decision.evidence_ref,
        ),
    )


def pull_and_verify_execution_staging(
    preflight: MaterializationPreflightV1,
    mapping: ExecutionDeploymentMappingV1,
    storage_port: MaterializationStoragePortV1,
) -> VerifiedCacheCandidateV1 | MaterializationResultV1:
    """从 S03 current selection 拉取 typed staging，并调用 S02 verifier 一次。"""

    if not isinstance(preflight, MaterializationPreflightV1):
        return _blocked(MaterializationBlockReasonV1.CONTEXT_MISMATCH)
    previous = _safe_current_selection(storage_port)
    if not _port_binding_valid(preflight, mapping, storage_port):
        return _blocked(MaterializationBlockReasonV1.PORT_BINDING_INVALID, previous)
    request = preflight.request
    distribution = preflight.distribution_selection
    token = ExecutionStagingTokenV1(
        staging_version=MATERIALIZATION_STAGING_VERSION,
        request_id=request.request_id,
        release_id=distribution.release_id,
        logical_uri=distribution.logical_uri,
        expected_content_sha256=request.expected_content_sha256,
        expected_manifest_sha256=request.expected_manifest_sha256,
        replica_receipt_sha256=distribution.receipt_sha256,
        replica_selection_revision=distribution.selection_revision,
        state=NON_RUNTIME_STAGING_STATE,
    )
    try:
        staged = storage_port.pull_to_staging(
            distribution,
            preflight.replica_receipt,
            token,
        )
    except MaterializationStoragePortError as exc:
        return _blocked(exc.reason, _safe_current_selection(storage_port))
    except Exception:
        return _blocked(
            MaterializationBlockReasonV1.STAGING_INTERRUPTED,
            _safe_current_selection(storage_port),
        )
    if (
        not isinstance(staged, tuple)
        or len(staged) != 3
        or not isinstance(staged[0], ExecutionStagingTokenV1)
        or staged[0] != token
        or staged[0].state != NON_RUNTIME_STAGING_STATE
        or not isinstance(staged[1], SealedTrialReturnBundleV1)
        or not isinstance(staged[2], ResearchCanonicalSelectionV1)
    ):
        return _blocked(
            MaterializationBlockReasonV1.STAGING_INTEGRITY_INVALID,
            _safe_current_selection(storage_port),
        )
    _, bundle, source_selection = staged
    try:
        verified = verify_sealed_trial_return_bundle(bundle, source_selection)
    except Exception as exc:
        return _blocked(
            _map_verifier_failure(exc),
            _safe_current_selection(storage_port),
        )
    vector = _make_verification_vector(preflight, verified)
    if not vector.complete:
        return _blocked(
            _vector_failure_reason(vector),
            _safe_current_selection(storage_port),
        )
    return VerifiedCacheCandidateV1(
        preflight=preflight,
        staging_token=token,
        staged_bundle=bundle,
        source_selection=source_selection,
        staged_verified=verified,
        verification_vector=vector,
        cache_version_ref=_make_cache_version_ref(preflight),
    )


def commit_execution_cache(
    candidate: VerifiedCacheCandidateV1,
    commit_decision: ActionDecisionV1,
    commit_context: ActionScopeContextV1,
    current_replica_selection: DistributionSelectionV1,
    storage_port: MaterializationStoragePortV1,
) -> MaterializationResultV1:
    """执行 fresh guard、immutable persist 和最多一次 local selection CAS。"""

    previous = _safe_current_selection(storage_port)
    if not isinstance(candidate, VerifiedCacheCandidateV1):
        return _blocked(MaterializationBlockReasonV1.STAGING_INTEGRITY_INVALID, previous)
    if not candidate.verification_vector.complete:
        return _blocked(MaterializationBlockReasonV1.VERIFICATION_INCOMPLETE, previous)
    authorization_reason = _commit_authorization_reason(
        candidate,
        commit_decision,
        commit_context,
    )
    if authorization_reason is not MaterializationBlockReasonV1.NONE:
        return _blocked(authorization_reason, previous)
    if (
        not isinstance(current_replica_selection, DistributionSelectionV1)
        or current_replica_selection != candidate.preflight.distribution_selection
        or not isinstance(storage_port, MaterializationStoragePortV1)
        or storage_port.replica_port.current_selection != current_replica_selection
    ):
        return _blocked(MaterializationBlockReasonV1.REPLICA_SELECTION_DRIFT, previous)
    if not _port_binding_valid(
        candidate.preflight,
        storage_port.mapping,
        storage_port,
    ):
        return _blocked(MaterializationBlockReasonV1.PORT_BINDING_INVALID, previous)
    receipt = _make_receipt(candidate, commit_decision)
    new_selection = ExecutionCacheSelectionV1(
        selection_version=EXECUTION_CACHE_SELECTION_VERSION,
        release_id=receipt.release_id,
        logical_uri=receipt.logical_uri,
        content_sha256=receipt.content_sha256,
        manifest_sha256=receipt.manifest_sha256,
        original_seal_sha256=receipt.original_seal_sha256,
        replica_receipt_sha256=receipt.replica_receipt_sha256,
        materialization_receipt_sha256=receipt.receipt_sha256,
        cache_version_ref=receipt.cache_version_ref,
        selection_revision=1 if previous is None else previous.selection_revision + 1,
        decision_origin=receipt.decision_origin,
        target_kind=receipt.target_kind,
        source_kind=EXECUTION_LOCAL_SOURCE_KIND,
    )
    try:
        storage_port.persist_immutable_cache(candidate, receipt)
    except MaterializationStoragePortError as exc:
        return _blocked(exc.reason, previous)
    except Exception:
        return _blocked(MaterializationBlockReasonV1.IMMUTABLE_CACHE_CONFLICT, previous)
    try:
        persisted_receipt = storage_port.read_materialization_receipt(
            receipt.receipt_sha256
        )
    except Exception:
        persisted_receipt = None
    if persisted_receipt != receipt:
        return _blocked(
            MaterializationBlockReasonV1.RECEIPT_PERSISTENCE_FAILED,
            previous,
        )
    try:
        handle = _make_execution_local_handle(
            new_selection,
            storage_port.mapping,
            persisted_receipt,
        )
    except Exception:
        return _blocked(MaterializationBlockReasonV1.LOCAL_HANDLE_INVALID, previous)
    try:
        committed = storage_port.compare_and_swap_cache_selection(
            previous,
            new_selection,
        )
    except Exception:
        committed = False
    if not committed or storage_port.current_selection != new_selection:
        return _blocked(
            MaterializationBlockReasonV1.POINTER_CONFLICT,
            _safe_current_selection(storage_port),
        )
    return MaterializationResultV1(
        status=MaterializationStatusV1.MATERIALIZED,
        reason=MaterializationBlockReasonV1.NONE,
        receipt=receipt,
        selection=new_selection,
        handle=handle,
        previous_selection=previous,
    )


def resolve_execution_local_handle(
    selection: ExecutionCacheSelectionV1,
    storage_port: MaterializationStoragePortV1,
) -> ExecutionLocalCacheHandleV1:
    """只把 port 当前 exact execution-local selection 映射为本地句柄。"""

    if not isinstance(selection, ExecutionCacheSelectionV1):
        raise MaterializationContractError("CACHE_SELECTION_TYPE_INVALID")
    if not isinstance(storage_port, MaterializationStoragePortV1):
        raise MaterializationContractError("STORAGE_PORT_TYPE_INVALID")
    if storage_port.current_selection != selection:
        raise MaterializationContractError("CACHE_SELECTION_NOT_CURRENT")
    try:
        receipt = storage_port.read_materialization_receipt(
            selection.materialization_receipt_sha256
        )
    except Exception as exc:
        raise MaterializationContractError("RECEIPT_NOT_READABLE") from exc
    return _make_execution_local_handle(selection, storage_port.mapping, receipt)


def _make_execution_local_handle(
    selection: ExecutionCacheSelectionV1,
    mapping: ExecutionDeploymentMappingV1,
    receipt: MaterializationReceiptV1 | None,
) -> ExecutionLocalCacheHandleV1:
    """校验 selection、receipt 与 mapping 的完整绑定后构造纯本地句柄。"""

    if not isinstance(mapping, ExecutionDeploymentMappingV1):
        raise MaterializationContractError("MAPPING_TYPE_INVALID")
    if not isinstance(receipt, MaterializationReceiptV1):
        raise MaterializationContractError("RECEIPT_TYPE_INVALID")
    if (
        selection.source_kind != EXECUTION_LOCAL_SOURCE_KIND
        or selection.logical_uri != mapping.logical_uri
        or selection.decision_origin is not mapping.decision_origin
        or selection.target_kind is not mapping.target_kind
        or receipt.receipt_sha256
        != selection.materialization_receipt_sha256
        or receipt.release_id != selection.release_id
        or receipt.logical_uri != selection.logical_uri
        or receipt.content_sha256 != selection.content_sha256
        or receipt.manifest_sha256 != selection.manifest_sha256
        or receipt.original_seal_sha256 != selection.original_seal_sha256
        or receipt.replica_receipt_sha256
        != selection.replica_receipt_sha256
        or receipt.cache_version_ref != selection.cache_version_ref
        or receipt.decision_origin is not selection.decision_origin
        or receipt.target_kind is not selection.target_kind
    ):
        raise MaterializationContractError("LOCAL_HANDLE_BINDING_INVALID")
    digest = selection.content_sha256.removeprefix("sha256:")
    local_handle = f"{mapping.cache_handle}/{selection.release_id}/{digest}"
    return ExecutionLocalCacheHandleV1(
        release_id=selection.release_id,
        logical_uri=selection.logical_uri,
        content_sha256=selection.content_sha256,
        materialization_receipt_sha256=(
            selection.materialization_receipt_sha256
        ),
        cache_version_ref=selection.cache_version_ref,
        source_kind=selection.source_kind,
        local_handle=local_handle,
    )


def materialize_repository_fixture_execution_cache(
    request: ExecutionMaterializationRequestV1,
    replica_receipt: ReplicaVerificationReceiptV1,
    distribution_selection: DistributionSelectionV1,
    preflight_decision: ActionDecisionV1,
    preflight_context: ActionScopeContextV1,
    commit_decision: ActionDecisionV1,
    commit_context: ActionScopeContextV1,
    current_replica_selection: DistributionSelectionV1,
    mapping: ExecutionDeploymentMappingV1,
    storage_port: MaterializationStoragePortV1,
) -> MaterializationResultV1:
    """执行固定的 preflight→S03 read→S02 verify→4/4→immutable→CAS。"""

    preflight = validate_materialization_preflight(
        request,
        replica_receipt,
        distribution_selection,
        preflight_decision,
        preflight_context,
    )
    if isinstance(preflight, MaterializationResultV1):
        return preflight
    candidate = pull_and_verify_execution_staging(
        preflight,
        mapping,
        storage_port,
    )
    if isinstance(candidate, MaterializationResultV1):
        return candidate
    return commit_execution_cache(
        candidate,
        commit_decision,
        commit_context,
        current_replica_selection,
        storage_port,
    )


def _replica_predecessor_matches(
    request: ExecutionMaterializationRequestV1,
    receipt: ReplicaVerificationReceiptV1,
    distribution: DistributionSelectionV1,
) -> bool:
    return (
        request.expected_logical_uri == distribution.logical_uri
        and request.expected_replica_receipt_sha256 == distribution.receipt_sha256
        and receipt.receipt_sha256 == distribution.receipt_sha256
        and receipt.replica_version_ref == distribution.replica_version_ref
        and receipt.source_selection_sha256 == distribution.source_selection_sha256
        and receipt.release_id == distribution.release_id
        and receipt.logical_uri == distribution.logical_uri
        and receipt.content_sha256 == distribution.content_sha256
        and receipt.manifest_sha256 == distribution.manifest_sha256
        and receipt.original_seal_sha256 == distribution.original_seal_sha256
        and receipt.decision_origin is distribution.decision_origin
        and receipt.target_kind is distribution.target_kind
        and receipt.verification_vector.complete
    )


def _port_binding_valid(
    preflight: MaterializationPreflightV1,
    mapping: object,
    storage_port: object,
) -> bool:
    return (
        isinstance(mapping, ExecutionDeploymentMappingV1)
        and isinstance(storage_port, MaterializationStoragePortV1)
        and storage_port.mapping == mapping
        and mapping.repository_owned is True
        and mapping.decision_origin
        is ActionDecisionOriginV1.REPOSITORY_FIXTURE
        and mapping.target_kind is ActionTargetKindV1.REPOSITORY_FIXTURE
        and mapping.logical_uri == preflight.request.expected_logical_uri
        and storage_port.replica_port.current_selection
        == preflight.distribution_selection
    )


def _make_verification_vector(
    preflight: MaterializationPreflightV1,
    verified: VerifiedTrialReturnBundleV1,
) -> MaterializationVerificationVectorV1:
    request = preflight.request
    receipt = preflight.replica_receipt
    distribution = preflight.distribution_selection
    bundle = verified.bundle
    selection = verified.selection
    return MaterializationVerificationVectorV1(
        release=(
            bundle.manifest.release_id
            == bundle.seal.release_id
            == selection.release_id
            == receipt.release_id
            == distribution.release_id
            == request.expected_release_id
        ),
        manifest=(
            bundle.manifest_sha256
            == selection.manifest_sha256
            == receipt.manifest_sha256
            == distribution.manifest_sha256
            == request.expected_manifest_sha256
        ),
        seal=(
            verified.original_seal_sha256
            == selection.original_seal_sha256
            == receipt.original_seal_sha256
            == distribution.original_seal_sha256
        ),
        content=(
            bundle.payload.content_sha256
            == selection.content_sha256
            == receipt.content_sha256
            == distribution.content_sha256
            == request.expected_content_sha256
        ),
    )


def _vector_failure_reason(
    vector: MaterializationVerificationVectorV1,
) -> MaterializationBlockReasonV1:
    if not vector.release:
        return MaterializationBlockReasonV1.RELEASE_MISMATCH
    if not vector.manifest:
        return MaterializationBlockReasonV1.MANIFEST_MISMATCH
    if not vector.seal:
        return MaterializationBlockReasonV1.SEAL_MISMATCH
    if not vector.content:
        return MaterializationBlockReasonV1.CONTENT_MISMATCH
    return MaterializationBlockReasonV1.VERIFICATION_INCOMPLETE


def _map_verifier_failure(exc: Exception) -> MaterializationBlockReasonV1:
    reason = str(getattr(exc, "reason_code", exc)).upper()
    if "MANIFEST" in reason:
        return MaterializationBlockReasonV1.MANIFEST_MISMATCH
    if "PAYLOAD" in reason or "CONTENT" in reason:
        return MaterializationBlockReasonV1.CONTENT_MISMATCH
    if "SEAL" in reason or "SELECTION" in reason:
        return MaterializationBlockReasonV1.SEAL_MISMATCH
    return MaterializationBlockReasonV1.STAGING_INTEGRITY_INVALID


def _commit_authorization_reason(
    candidate: VerifiedCacheCandidateV1,
    decision: object,
    context: object,
) -> MaterializationBlockReasonV1:
    if not isinstance(decision, ActionDecisionV1) or not isinstance(
        context, ActionScopeContextV1
    ):
        return MaterializationBlockReasonV1.COMMIT_AUTHORIZATION_INVALID
    if context != candidate.preflight.action_context:
        return MaterializationBlockReasonV1.CONTEXT_MISMATCH
    if (
        decision.decision_origin is not ActionDecisionOriginV1.REPOSITORY_FIXTURE
        or decision.target_kind is not ActionTargetKindV1.REPOSITORY_FIXTURE
    ):
        return MaterializationBlockReasonV1.COMMIT_AUTHORIZATION_INVALID
    try:
        require_action_eligible(
            decision,
            expected_kind=(
                PathIActionKind.EXECUTION_PULL_VERIFY_MATERIALIZE
            ),
            expected_context=context,
            expected_origin=ActionDecisionOriginV1.REPOSITORY_FIXTURE,
        )
    except Exception:
        return MaterializationBlockReasonV1.COMMIT_AUTHORIZATION_INVALID
    try:
        _require_evidence_pair(
            "commit_authorization_evidence_refs",
            (decision.approval_ref, decision.evidence_ref),
        )
    except MaterializationContractError:
        return MaterializationBlockReasonV1.COMMIT_AUTHORIZATION_INVALID
    if decision.evaluated_at <= candidate.preflight.preflight_decision.evaluated_at:
        return MaterializationBlockReasonV1.COMMIT_DECISION_NOT_FRESH
    return MaterializationBlockReasonV1.NONE


def _make_cache_version_ref(preflight: MaterializationPreflightV1) -> str:
    request = preflight.request
    ref = (
        f"execution-cache:{request.expected_release_id}:"
        f"{request.expected_logical_uri}:"
        f"{request.expected_content_sha256.removeprefix('sha256:')}"
    )
    _require_identifier("cache_version_ref", ref)
    return ref


def _make_receipt(
    candidate: VerifiedCacheCandidateV1,
    commit_decision: ActionDecisionV1,
) -> MaterializationReceiptV1:
    preflight = candidate.preflight
    request = preflight.request
    values: dict[str, object] = {
        "authority": TARGET_AUTHORITY,
        "cache_version_ref": candidate.cache_version_ref,
        "commit_authorization_evidence_refs": (
            commit_decision.approval_ref,
            commit_decision.evidence_ref,
        ),
        "content_sha256": request.expected_content_sha256,
        "decision_origin": commit_decision.decision_origin,
        "logical_uri": request.expected_logical_uri,
        "manifest_sha256": request.expected_manifest_sha256,
        "original_seal_sha256": (
            candidate.staged_verified.original_seal_sha256
        ),
        "preflight_authorization_evidence_refs": (
            preflight.preflight_authorization_evidence_refs
        ),
        "release_id": request.expected_release_id,
        "replica_receipt_sha256": (
            preflight.replica_receipt.receipt_sha256
        ),
        "replica_selection_revision": (
            preflight.distribution_selection.selection_revision
        ),
        "schema_version": MATERIALIZATION_RECEIPT_VERSION,
        "target_kind": commit_decision.target_kind,
        "verification_vector": {
            "content": candidate.verification_vector.content,
            "manifest": candidate.verification_vector.manifest,
            "release": candidate.verification_vector.release,
            "seal": candidate.verification_vector.seal,
        },
    }
    digest = _sha256_prefixed(
        MATERIALIZATION_RECEIPT_HASH_DOMAIN
        + canonical_materialization_receipt_bytes(values)
    )
    return MaterializationReceiptV1(
        schema_version=MATERIALIZATION_RECEIPT_VERSION,
        authority=TARGET_AUTHORITY,
        release_id=request.expected_release_id,
        logical_uri=request.expected_logical_uri,
        content_sha256=request.expected_content_sha256,
        manifest_sha256=request.expected_manifest_sha256,
        original_seal_sha256=(
            candidate.staged_verified.original_seal_sha256
        ),
        replica_receipt_sha256=preflight.replica_receipt.receipt_sha256,
        replica_selection_revision=(
            preflight.distribution_selection.selection_revision
        ),
        decision_origin=commit_decision.decision_origin,
        target_kind=commit_decision.target_kind,
        verification_vector=candidate.verification_vector,
        preflight_authorization_evidence_refs=(
            preflight.preflight_authorization_evidence_refs
        ),
        commit_authorization_evidence_refs=(
            commit_decision.approval_ref,
            commit_decision.evidence_ref,
        ),
        cache_version_ref=candidate.cache_version_ref,
        receipt_sha256=digest,
    )


def _blocked(
    reason: MaterializationBlockReasonV1,
    previous: ExecutionCacheSelectionV1 | None = None,
) -> MaterializationResultV1:
    return MaterializationResultV1(
        status=MaterializationStatusV1.BLOCKED,
        reason=reason,
        receipt=None,
        selection=None,
        handle=None,
        previous_selection=previous,
    )


def _safe_current_selection(
    storage_port: object,
) -> ExecutionCacheSelectionV1 | None:
    if not isinstance(storage_port, MaterializationStoragePortV1):
        return None
    try:
        current = storage_port.current_selection
    except Exception:
        return None
    return current if isinstance(current, ExecutionCacheSelectionV1) else None


def _canonical_json_bytes(values: Mapping[str, object]) -> bytes:
    def normalize(value: object) -> object:
        if isinstance(value, Enum):
            return value.value
        if isinstance(value, Mapping):
            return {str(key): normalize(item) for key, item in value.items()}
        if isinstance(value, tuple):
            return [normalize(item) for item in value]
        return value

    return json.dumps(
        normalize(values),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def _sha256_prefixed(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def _require_sha256(name: str, value: object) -> None:
    if not isinstance(value, str) or _SHA256_RE.fullmatch(value) is None:
        raise MaterializationContractError(f"{name.upper()}_INVALID")


def _require_identifier(name: str, value: object) -> None:
    if not isinstance(value, str) or _IDENTIFIER_RE.fullmatch(value) is None:
        raise MaterializationContractError(f"{name.upper()}_INVALID")


def _require_fixture_uri(value: object) -> None:
    if not isinstance(value, str):
        raise MaterializationContractError("FIXTURE_URI_REQUIRED")
    parsed = urlsplit(value)
    if (
        parsed.scheme != "fixture"
        or parsed.netloc not in _FIXTURE_AUTHORITIES
        or not parsed.path.startswith("/")
        or parsed.query
        or parsed.fragment
        or any(part in {"", ".", ".."} for part in parsed.path.split("/")[1:])
    ):
        raise MaterializationContractError("FIXTURE_URI_REQUIRED")


def _require_relative_handle(name: str, value: object) -> None:
    if not isinstance(value, str) or not value:
        raise MaterializationContractError(f"{name.upper()}_INVALID")
    if (
        value.startswith(("/", "\\"))
        or "\\" in value
        or urlsplit(value).scheme
        or any(part in {"", ".", ".."} for part in value.split("/"))
    ):
        raise MaterializationContractError(f"{name.upper()}_INVALID")


def _require_evidence_pair(name: str, value: object) -> None:
    if not isinstance(value, tuple) or len(value) != 2:
        raise MaterializationContractError(f"{name.upper()}_INVALID")
    for item in value:
        if not isinstance(item, str) or not item:
            raise MaterializationContractError(f"{name.upper()}_INVALID")
        lowered = item.lower()
        if any(marker in lowered for marker in _FORBIDDEN_REF_MARKERS):
            raise MaterializationContractError(f"{name.upper()}_INVALID")
