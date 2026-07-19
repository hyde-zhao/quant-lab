"""Repository-local sealed-artifact replica verification contract。

本模块只接受显式传入的 repository fixture decision、sealed bundle 和
repository-owned storage port。它不读取环境、凭据或真实路径，不连接 NAS、
网络或运行时，也不创建新 seal、不修改 research canonical selection。
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib
import hmac
import json
import re
from typing import Final
import unicodedata
from urllib.parse import urlsplit

from engine.path_i_governance import (
    ActionDecisionOriginV1,
    ActionDecisionV1,
    ActionScopeContextV1,
    ActionTargetKindV1,
    PathIActionKind,
    PathIEligibilityError,
    require_action_eligible,
)
from engine.trial_return_artifact import (
    ResearchCanonicalSelectionV1,
    SealedTrialReturnBundleV1,
    VerifiedTrialReturnBundleV1,
    verify_sealed_trial_return_bundle,
)


__all__ = (
    "ReplicaSyncRequestV1",
    "ReplicaDeploymentMappingV1",
    "ReplicaStagingTokenV1",
    "ReplicaVerificationVectorV1",
    "ReplicaVerificationReceiptV1",
    "DistributionSelectionV1",
    "ReplicaPreflightV1",
    "VerifiedReplicaCandidateV1",
    "ReplicaPublishResultV1",
    "ReplicaPublishStatusV1",
    "ReplicaBlockReasonV1",
    "ReplicaStoragePortV1",
    "ReplicaStoragePortError",
    "canonical_replica_receipt_bytes",
    "validate_replica_preflight",
    "stage_and_verify_replica",
    "commit_verified_replica",
    "publish_repository_fixture_replica",
)


REPLICA_REQUEST_VERSION: Final = "replica-sync-request.v1"
REPLICA_MAPPING_VERSION: Final = "repository-fixture-replica-mapping.v1"
REPLICA_STAGING_VERSION: Final = "replica-staging-token.v1"
REPLICA_RECEIPT_VERSION: Final = "replica-verification-receipt.v1"
REPLICA_SELECTION_VERSION: Final = "distribution-selection.v1"
REPLICA_PORT_CAPABILITY_VERSION: Final = "repository-fixture-replica-port.v1"
REPLICA_RECEIPT_HASH_DOMAIN: Final = b"replica-receipt@v1\x00"
SOURCE_SELECTION_HASH_DOMAIN: Final = b"research-source-selection@v1\x00"
REPLICA_AUTHORITY: Final = "replica"
NON_DISTRIBUTABLE_STATE: Final = "non_distributable"

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


class ReplicaContractError(ValueError):
    """输入违反 replica v1 合同。"""


class ReplicaStoragePortError(ReplicaContractError):
    """Repository fixture storage port 拒绝操作。"""

    def __init__(self, reason: "ReplicaBlockReasonV1") -> None:
        self.reason = reason
        super().__init__(reason.value)


class ReplicaPublishStatusV1(str, Enum):
    VERIFIED = "VERIFIED"
    BLOCKED = "BLOCKED"


class ReplicaBlockReasonV1(str, Enum):
    NONE = "NONE"
    AUTHORIZATION_INVALID = "AUTHORIZATION_INVALID"
    DECISION_ORIGIN_INVALID = "DECISION_ORIGIN_INVALID"
    TARGET_KIND_INVALID = "TARGET_KIND_INVALID"
    CONTEXT_MISMATCH = "CONTEXT_MISMATCH"
    PORT_BINDING_INVALID = "PORT_BINDING_INVALID"
    SOURCE_TYPE_INVALID = "SOURCE_TYPE_INVALID"
    SOURCE_KIND_INVALID = "SOURCE_KIND_INVALID"
    SOURCE_UNVERSIONED = "SOURCE_UNVERSIONED"
    SOURCE_INTEGRITY_INVALID = "SOURCE_INTEGRITY_INVALID"
    RELEASE_MISMATCH = "RELEASE_MISMATCH"
    LOGICAL_URI_MISMATCH = "LOGICAL_URI_MISMATCH"
    CONTENT_MISMATCH = "CONTENT_MISMATCH"
    MANIFEST_MISMATCH = "MANIFEST_MISMATCH"
    SEAL_MISMATCH = "SEAL_MISMATCH"
    STALE_SOURCE_SELECTION = "STALE_SOURCE_SELECTION"
    STAGING_INTERRUPTED = "STAGING_INTERRUPTED"
    STAGING_INTEGRITY_INVALID = "STAGING_INTEGRITY_INVALID"
    VERIFICATION_INCOMPLETE = "VERIFICATION_INCOMPLETE"
    COMMIT_AUTHORIZATION_INVALID = "COMMIT_AUTHORIZATION_INVALID"
    COMMIT_DECISION_NOT_FRESH = "COMMIT_DECISION_NOT_FRESH"
    IMMUTABLE_PERSIST_FAILED = "IMMUTABLE_PERSIST_FAILED"
    POINTER_CONFLICT = "POINTER_CONFLICT"
    SELECTED_REPLICA_MISMATCH = "SELECTED_REPLICA_MISMATCH"


@dataclass(frozen=True, slots=True)
class ReplicaSyncRequestV1:
    schema_version: str
    request_id: str
    expected_release_id: str
    expected_logical_uri: str
    expected_content_sha256: str
    expected_manifest_sha256: str
    expected_source_selection_sha256: str

    def __post_init__(self) -> None:
        if self.schema_version != REPLICA_REQUEST_VERSION:
            raise ReplicaContractError("REQUEST_VERSION_UNSUPPORTED")
        _require_identifier("request_id", self.request_id)
        _require_identifier("expected_release_id", self.expected_release_id)
        _require_fixture_uri(self.expected_logical_uri)
        for name in (
            "expected_content_sha256",
            "expected_manifest_sha256",
            "expected_source_selection_sha256",
        ):
            _require_sha256(name, getattr(self, name))

    @classmethod
    def from_source_selection(
        cls,
        *,
        request_id: str,
        source_selection: ResearchCanonicalSelectionV1,
    ) -> "ReplicaSyncRequestV1":
        """从调用方已批准的 source selection 固化 deterministic expectation。"""

        if not isinstance(source_selection, ResearchCanonicalSelectionV1):
            raise ReplicaContractError("SOURCE_SELECTION_TYPE_INVALID")
        return cls(
            schema_version=REPLICA_REQUEST_VERSION,
            request_id=request_id,
            expected_release_id=source_selection.release_id,
            expected_logical_uri=source_selection.logical_uri,
            expected_content_sha256=source_selection.content_sha256,
            expected_manifest_sha256=source_selection.manifest_sha256,
            expected_source_selection_sha256=(
                _source_selection_sha256(source_selection)
            ),
        )


@dataclass(frozen=True, slots=True)
class ReplicaDeploymentMappingV1:
    mapping_version: str
    repository_owned: bool
    decision_origin: ActionDecisionOriginV1
    target_kind: ActionTargetKindV1
    logical_uri: str
    source_handle: str
    staging_handle: str
    version_handle: str
    pointer_handle: str

    def __post_init__(self) -> None:
        if self.mapping_version != REPLICA_MAPPING_VERSION:
            raise ReplicaContractError("MAPPING_VERSION_UNSUPPORTED")
        if self.repository_owned is not True:
            raise ReplicaContractError("MAPPING_NOT_REPOSITORY_OWNED")
        if self.decision_origin is not ActionDecisionOriginV1.REPOSITORY_FIXTURE:
            raise ReplicaContractError("MAPPING_ORIGIN_INVALID")
        if self.target_kind is not ActionTargetKindV1.REPOSITORY_FIXTURE:
            raise ReplicaContractError("MAPPING_TARGET_INVALID")
        _require_fixture_uri(self.logical_uri)
        for name in (
            "source_handle",
            "staging_handle",
            "version_handle",
            "pointer_handle",
        ):
            _require_relative_handle(name, getattr(self, name))


@dataclass(frozen=True, slots=True)
class ReplicaStagingTokenV1:
    staging_version: str
    request_id: str
    release_id: str
    logical_uri: str
    expected_content_sha256: str
    expected_manifest_sha256: str
    expected_source_selection_sha256: str
    state: str

    def __post_init__(self) -> None:
        if self.staging_version != REPLICA_STAGING_VERSION:
            raise ReplicaContractError("STAGING_VERSION_UNSUPPORTED")
        _require_identifier("request_id", self.request_id)
        _require_identifier("release_id", self.release_id)
        _require_fixture_uri(self.logical_uri)
        for name in (
            "expected_content_sha256",
            "expected_manifest_sha256",
            "expected_source_selection_sha256",
        ):
            _require_sha256(name, getattr(self, name))
        if self.state != NON_DISTRIBUTABLE_STATE:
            raise ReplicaContractError("STAGING_MUST_BE_NON_DISTRIBUTABLE")


@dataclass(frozen=True, slots=True)
class ReplicaVerificationVectorV1:
    seal: bool
    manifest: bool
    content: bool
    release: bool
    freshness: bool

    def __post_init__(self) -> None:
        if any(
            type(value) is not bool
            for value in (
                self.seal,
                self.manifest,
                self.content,
                self.release,
                self.freshness,
            )
        ):
            raise ReplicaContractError("VERIFICATION_VECTOR_BOOL_REQUIRED")

    @property
    def complete(self) -> bool:
        return all(
            (
                self.seal,
                self.manifest,
                self.content,
                self.release,
                self.freshness,
            )
        )


@dataclass(frozen=True, slots=True)
class ReplicaVerificationReceiptV1:
    schema_version: str
    authority: str
    release_id: str
    logical_uri: str
    content_sha256: str
    manifest_sha256: str
    source_selection_sha256: str
    original_seal_sha256: str
    decision_origin: ActionDecisionOriginV1
    target_kind: ActionTargetKindV1
    verification_vector: ReplicaVerificationVectorV1
    preflight_authorization_evidence_refs: tuple[str, str]
    commit_authorization_evidence_refs: tuple[str, str]
    replica_version_ref: str
    receipt_sha256: str

    def __post_init__(self) -> None:
        if self.schema_version != REPLICA_RECEIPT_VERSION:
            raise ReplicaContractError("RECEIPT_VERSION_UNSUPPORTED")
        if self.authority != REPLICA_AUTHORITY:
            raise ReplicaContractError("RECEIPT_AUTHORITY_INVALID")
        _require_identifier("release_id", self.release_id)
        _require_fixture_uri(self.logical_uri)
        for name in (
            "content_sha256",
            "manifest_sha256",
            "source_selection_sha256",
            "original_seal_sha256",
            "receipt_sha256",
        ):
            _require_sha256(name, getattr(self, name))
        if self.decision_origin is not ActionDecisionOriginV1.REPOSITORY_FIXTURE:
            raise ReplicaContractError("RECEIPT_ORIGIN_INVALID")
        if self.target_kind is not ActionTargetKindV1.REPOSITORY_FIXTURE:
            raise ReplicaContractError("RECEIPT_TARGET_INVALID")
        if not isinstance(self.verification_vector, ReplicaVerificationVectorV1):
            raise ReplicaContractError("VERIFICATION_VECTOR_TYPE_INVALID")
        if not self.verification_vector.complete:
            raise ReplicaContractError("VERIFICATION_INCOMPLETE")
        _require_evidence_pair(
            "preflight_authorization_evidence_refs",
            self.preflight_authorization_evidence_refs,
        )
        _require_evidence_pair(
            "commit_authorization_evidence_refs",
            self.commit_authorization_evidence_refs,
        )
        _require_identifier("replica_version_ref", self.replica_version_ref)
        expected = _sha256_prefixed(
            REPLICA_RECEIPT_HASH_DOMAIN + canonical_replica_receipt_bytes(self)
        )
        if not hmac.compare_digest(expected, self.receipt_sha256):
            raise ReplicaContractError("RECEIPT_DIGEST_MISMATCH")


@dataclass(frozen=True, slots=True)
class DistributionSelectionV1:
    selection_version: str
    release_id: str
    logical_uri: str
    content_sha256: str
    manifest_sha256: str
    original_seal_sha256: str
    source_selection_sha256: str
    receipt_sha256: str
    replica_version_ref: str
    selection_revision: int
    decision_origin: ActionDecisionOriginV1
    target_kind: ActionTargetKindV1

    def __post_init__(self) -> None:
        if self.selection_version != REPLICA_SELECTION_VERSION:
            raise ReplicaContractError("DISTRIBUTION_SELECTION_VERSION_UNSUPPORTED")
        _require_identifier("release_id", self.release_id)
        _require_fixture_uri(self.logical_uri)
        for name in (
            "content_sha256",
            "manifest_sha256",
            "original_seal_sha256",
            "source_selection_sha256",
            "receipt_sha256",
        ):
            _require_sha256(name, getattr(self, name))
        _require_identifier("replica_version_ref", self.replica_version_ref)
        if (
            isinstance(self.selection_revision, bool)
            or not isinstance(self.selection_revision, int)
            or self.selection_revision <= 0
        ):
            raise ReplicaContractError("SELECTION_REVISION_INVALID")
        if self.decision_origin is not ActionDecisionOriginV1.REPOSITORY_FIXTURE:
            raise ReplicaContractError("DISTRIBUTION_SELECTION_ORIGIN_INVALID")
        if self.target_kind is not ActionTargetKindV1.REPOSITORY_FIXTURE:
            raise ReplicaContractError("DISTRIBUTION_SELECTION_TARGET_INVALID")


@dataclass(frozen=True, slots=True)
class ReplicaPreflightV1:
    request: ReplicaSyncRequestV1
    action_context: ActionScopeContextV1
    preflight_decision: ActionDecisionV1
    verified_source: VerifiedTrialReturnBundleV1
    source_selection_sha256: str
    preflight_authorization_evidence_refs: tuple[str, str]


@dataclass(frozen=True, slots=True)
class VerifiedReplicaCandidateV1:
    preflight: ReplicaPreflightV1
    staging_token: ReplicaStagingTokenV1
    staged_verified: VerifiedTrialReturnBundleV1
    verification_vector: ReplicaVerificationVectorV1
    replica_version_ref: str


@dataclass(frozen=True, slots=True)
class ReplicaPublishResultV1:
    status: ReplicaPublishStatusV1
    reason: ReplicaBlockReasonV1
    receipt: ReplicaVerificationReceiptV1 | None
    selection: DistributionSelectionV1 | None
    previous_selection: DistributionSelectionV1 | None

    def __post_init__(self) -> None:
        if self.status is ReplicaPublishStatusV1.VERIFIED:
            if (
                self.reason is not ReplicaBlockReasonV1.NONE
                or self.receipt is None
                or self.selection is None
            ):
                raise ReplicaContractError("VERIFIED_RESULT_INVARIANT_INVALID")
        elif (
            self.reason is ReplicaBlockReasonV1.NONE
            or self.receipt is not None
            or self.selection is not None
        ):
            raise ReplicaContractError("BLOCKED_RESULT_INVARIANT_INVALID")


class ReplicaStoragePortV1:
    """Repository-owned nominal fixture port；不包含任何真实 NAS adapter。"""

    __slots__ = ("_mapping",)

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if "read_selected_replica" in cls.__dict__:
            raise TypeError("read_selected_replica contract 不得被 override")

    def __init__(self, mapping: ReplicaDeploymentMappingV1) -> None:
        if not isinstance(mapping, ReplicaDeploymentMappingV1):
            raise ReplicaStoragePortError(ReplicaBlockReasonV1.PORT_BINDING_INVALID)
        self._mapping = mapping

    @property
    def mapping(self) -> ReplicaDeploymentMappingV1:
        return self._mapping

    @property
    def current_selection(self) -> DistributionSelectionV1 | None:
        raise NotImplementedError

    def stage_bundle(
        self,
        preflight: ReplicaPreflightV1,
        staging_token: ReplicaStagingTokenV1,
    ) -> SealedTrialReturnBundleV1:
        raise NotImplementedError

    def persist_immutable_replica(
        self,
        candidate: VerifiedReplicaCandidateV1,
        receipt: ReplicaVerificationReceiptV1,
    ) -> None:
        raise NotImplementedError

    def compare_and_swap_selection(
        self,
        expected_previous: DistributionSelectionV1 | None,
        new_selection: DistributionSelectionV1,
    ) -> bool:
        raise NotImplementedError

    def _read_immutable_replica(
        self,
        replica_version_ref: str,
    ) -> tuple[
        SealedTrialReturnBundleV1,
        ResearchCanonicalSelectionV1,
        ReplicaVerificationReceiptV1,
    ]:
        raise NotImplementedError

    def read_selected_replica(
        self,
        distribution_selection: DistributionSelectionV1,
    ) -> tuple[
        SealedTrialReturnBundleV1,
        ResearchCanonicalSelectionV1,
        ReplicaVerificationReceiptV1,
    ]:
        """只按 current distribution selection 返回 exact immutable tuple。"""

        if not isinstance(distribution_selection, DistributionSelectionV1):
            raise ReplicaStoragePortError(
                ReplicaBlockReasonV1.SELECTED_REPLICA_MISMATCH
            )
        if self.current_selection != distribution_selection:
            raise ReplicaStoragePortError(
                ReplicaBlockReasonV1.SELECTED_REPLICA_MISMATCH
            )
        try:
            selected = self._read_immutable_replica(
                distribution_selection.replica_version_ref
            )
        except ReplicaStoragePortError:
            raise
        except Exception as exc:
            raise ReplicaStoragePortError(
                ReplicaBlockReasonV1.SELECTED_REPLICA_MISMATCH
            ) from exc
        _require_selected_tuple_matches(distribution_selection, selected)
        return selected


def canonical_replica_receipt_bytes(
    receipt: ReplicaVerificationReceiptV1,
) -> bytes:
    """返回排除 self-hash、展示时间与物理路径的 canonical receipt body。"""

    if not isinstance(receipt, ReplicaVerificationReceiptV1):
        raise ReplicaContractError("RECEIPT_TYPE_INVALID")
    return _canonical_json_bytes(
        {
            "authority": receipt.authority,
            "commit_authorization_evidence_refs": (
                receipt.commit_authorization_evidence_refs
            ),
            "content_sha256": receipt.content_sha256,
            "decision_origin": receipt.decision_origin,
            "logical_uri": receipt.logical_uri,
            "manifest_sha256": receipt.manifest_sha256,
            "original_seal_sha256": receipt.original_seal_sha256,
            "preflight_authorization_evidence_refs": (
                receipt.preflight_authorization_evidence_refs
            ),
            "release_id": receipt.release_id,
            "replica_version_ref": receipt.replica_version_ref,
            "schema_version": receipt.schema_version,
            "source_selection_sha256": receipt.source_selection_sha256,
            "target_kind": receipt.target_kind,
            "verification_vector": {
                "content": receipt.verification_vector.content,
                "freshness": receipt.verification_vector.freshness,
                "manifest": receipt.verification_vector.manifest,
                "release": receipt.verification_vector.release,
                "seal": receipt.verification_vector.seal,
            },
        }
    )


def validate_replica_preflight(
    request: ReplicaSyncRequestV1,
    source_bundle: SealedTrialReturnBundleV1,
    source_selection: ResearchCanonicalSelectionV1,
    decision: ActionDecisionV1,
    action_context: ActionScopeContextV1,
) -> ReplicaPreflightV1 | ReplicaPublishResultV1:
    """在 first storage write 前验证授权、S02 原 seal 与 deterministic freshness。"""

    if not isinstance(request, ReplicaSyncRequestV1):
        return _blocked(ReplicaBlockReasonV1.SOURCE_TYPE_INVALID)
    authorization_reason = _validate_sync_authorization(decision, action_context)
    if authorization_reason is not ReplicaBlockReasonV1.NONE:
        return _blocked(authorization_reason)
    if not isinstance(source_bundle, SealedTrialReturnBundleV1) or not isinstance(
        source_selection, ResearchCanonicalSelectionV1
    ):
        return _blocked(ReplicaBlockReasonV1.SOURCE_TYPE_INVALID)
    version_reason = _validate_source_versions(source_bundle, source_selection)
    if version_reason is not ReplicaBlockReasonV1.NONE:
        return _blocked(version_reason)
    try:
        verified = verify_sealed_trial_return_bundle(
            source_bundle,
            source_selection,
        )
    except Exception as exc:
        return _blocked(_map_source_integrity_reason(exc, staged=False))
    context_reason = _validate_source_context(verified, action_context)
    if context_reason is not ReplicaBlockReasonV1.NONE:
        return _blocked(context_reason)
    expectation_reason = _validate_source_expectation(request, verified)
    if expectation_reason is not ReplicaBlockReasonV1.NONE:
        return _blocked(expectation_reason)
    source_selection_sha256 = _source_selection_sha256(verified.selection)
    if not hmac.compare_digest(
        source_selection_sha256,
        request.expected_source_selection_sha256,
    ):
        return _blocked(ReplicaBlockReasonV1.STALE_SOURCE_SELECTION)
    return ReplicaPreflightV1(
        request=request,
        action_context=action_context,
        preflight_decision=decision,
        verified_source=verified,
        source_selection_sha256=source_selection_sha256,
        preflight_authorization_evidence_refs=(
            decision.approval_ref,
            decision.evidence_ref,
        ),
    )


def stage_and_verify_replica(
    preflight: ReplicaPreflightV1,
    mapping: ReplicaDeploymentMappingV1,
    storage_port: ReplicaStoragePortV1,
) -> VerifiedReplicaCandidateV1 | ReplicaPublishResultV1:
    """写入 non-distributable staging，并再次调用同一 S02 verifier。"""

    if not isinstance(preflight, ReplicaPreflightV1):
        return _blocked(ReplicaBlockReasonV1.SOURCE_TYPE_INVALID)
    port_reason = _validate_port_binding(preflight, mapping, storage_port)
    if port_reason is not ReplicaBlockReasonV1.NONE:
        return _blocked(port_reason, _safe_current_selection(storage_port))
    request = preflight.request
    token = ReplicaStagingTokenV1(
        staging_version=REPLICA_STAGING_VERSION,
        request_id=request.request_id,
        release_id=request.expected_release_id,
        logical_uri=request.expected_logical_uri,
        expected_content_sha256=request.expected_content_sha256,
        expected_manifest_sha256=request.expected_manifest_sha256,
        expected_source_selection_sha256=(
            request.expected_source_selection_sha256
        ),
        state=NON_DISTRIBUTABLE_STATE,
    )
    try:
        staged_bundle = storage_port.stage_bundle(preflight, token)
    except Exception:
        return _blocked(
            ReplicaBlockReasonV1.STAGING_INTERRUPTED,
            _safe_current_selection(storage_port),
        )
    if not isinstance(staged_bundle, SealedTrialReturnBundleV1):
        return _blocked(
            ReplicaBlockReasonV1.STAGING_INTEGRITY_INVALID,
            _safe_current_selection(storage_port),
        )
    if _validate_port_binding(preflight, mapping, storage_port) is not (
        ReplicaBlockReasonV1.NONE
    ):
        return _blocked(
            ReplicaBlockReasonV1.PORT_BINDING_INVALID,
            _safe_current_selection(storage_port),
        )
    try:
        staged_verified = verify_sealed_trial_return_bundle(
            staged_bundle,
            preflight.verified_source.selection,
        )
    except Exception as exc:
        return _blocked(
            _map_source_integrity_reason(exc, staged=True),
            _safe_current_selection(storage_port),
        )
    vector = _make_verification_vector(preflight, staged_verified)
    if not vector.complete:
        return _blocked(
            _vector_failure_reason(preflight, staged_verified, vector),
            _safe_current_selection(storage_port),
        )
    version_ref = _make_replica_version_ref(preflight, staged_verified)
    return VerifiedReplicaCandidateV1(
        preflight=preflight,
        staging_token=token,
        staged_verified=staged_verified,
        verification_vector=vector,
        replica_version_ref=version_ref,
    )


def commit_verified_replica(
    candidate: VerifiedReplicaCandidateV1,
    commit_decision: ActionDecisionV1,
    commit_context: ActionScopeContextV1,
    storage_port: ReplicaStoragePortV1,
) -> ReplicaPublishResultV1:
    """重验 fresh authorization，持久化 immutable tuple 并执行一次 CAS。"""

    previous = _safe_current_selection(storage_port)
    if not isinstance(candidate, VerifiedReplicaCandidateV1):
        return _blocked(ReplicaBlockReasonV1.STAGING_INTEGRITY_INVALID, previous)
    if not candidate.verification_vector.complete:
        return _blocked(ReplicaBlockReasonV1.VERIFICATION_INCOMPLETE, previous)
    authorization_reason = _validate_commit_recheck(
        candidate.preflight,
        commit_decision,
        commit_context,
    )
    if authorization_reason is not ReplicaBlockReasonV1.NONE:
        return _blocked(authorization_reason, previous)
    port_reason = _validate_port_binding(
        candidate.preflight,
        storage_port.mapping if isinstance(storage_port, ReplicaStoragePortV1) else None,
        storage_port,
    )
    if port_reason is not ReplicaBlockReasonV1.NONE:
        return _blocked(port_reason, previous)
    receipt = _make_receipt(candidate, commit_decision)
    new_selection = DistributionSelectionV1(
        selection_version=REPLICA_SELECTION_VERSION,
        release_id=receipt.release_id,
        logical_uri=receipt.logical_uri,
        content_sha256=receipt.content_sha256,
        manifest_sha256=receipt.manifest_sha256,
        original_seal_sha256=receipt.original_seal_sha256,
        source_selection_sha256=receipt.source_selection_sha256,
        receipt_sha256=receipt.receipt_sha256,
        replica_version_ref=receipt.replica_version_ref,
        selection_revision=(
            1 if previous is None else previous.selection_revision + 1
        ),
        decision_origin=receipt.decision_origin,
        target_kind=receipt.target_kind,
    )
    try:
        storage_port.persist_immutable_replica(candidate, receipt)
    except Exception:
        return _blocked(ReplicaBlockReasonV1.IMMUTABLE_PERSIST_FAILED, previous)
    if _validate_port_binding(
        candidate.preflight,
        storage_port.mapping,
        storage_port,
    ) is not ReplicaBlockReasonV1.NONE:
        return _blocked(ReplicaBlockReasonV1.PORT_BINDING_INVALID, previous)
    try:
        committed = storage_port.compare_and_swap_selection(
            previous,
            new_selection,
        )
    except Exception:
        committed = False
    if not committed or storage_port.current_selection != new_selection:
        return _blocked(
            ReplicaBlockReasonV1.POINTER_CONFLICT,
            _safe_current_selection(storage_port),
        )
    return ReplicaPublishResultV1(
        status=ReplicaPublishStatusV1.VERIFIED,
        reason=ReplicaBlockReasonV1.NONE,
        receipt=receipt,
        selection=new_selection,
        previous_selection=previous,
    )


def publish_repository_fixture_replica(
    request: ReplicaSyncRequestV1,
    source_bundle: SealedTrialReturnBundleV1,
    source_selection: ResearchCanonicalSelectionV1,
    preflight_decision: ActionDecisionV1,
    preflight_context: ActionScopeContextV1,
    commit_decision: ActionDecisionV1,
    commit_context: ActionScopeContextV1,
    mapping: ReplicaDeploymentMappingV1,
    storage_port: ReplicaStoragePortV1,
) -> ReplicaPublishResultV1:
    """执行 preflight→staging→reverify→receipt→CAS 的固定纯 fixture 流程。"""

    preflight = validate_replica_preflight(
        request,
        source_bundle,
        source_selection,
        preflight_decision,
        preflight_context,
    )
    if isinstance(preflight, ReplicaPublishResultV1):
        return preflight
    commit_reason = _validate_commit_recheck(
        preflight,
        commit_decision,
        commit_context,
    )
    if commit_reason is not ReplicaBlockReasonV1.NONE:
        return _blocked(commit_reason, _safe_current_selection(storage_port))
    candidate = stage_and_verify_replica(preflight, mapping, storage_port)
    if isinstance(candidate, ReplicaPublishResultV1):
        return candidate
    return commit_verified_replica(
        candidate,
        commit_decision,
        commit_context,
        storage_port,
    )


def _validate_sync_authorization(
    decision: object,
    context: object,
    *,
    commit: bool = False,
) -> ReplicaBlockReasonV1:
    invalid = (
        ReplicaBlockReasonV1.COMMIT_AUTHORIZATION_INVALID
        if commit
        else ReplicaBlockReasonV1.AUTHORIZATION_INVALID
    )
    if not isinstance(decision, ActionDecisionV1) or not isinstance(
        context, ActionScopeContextV1
    ):
        return invalid
    if decision.decision_origin is not ActionDecisionOriginV1.REPOSITORY_FIXTURE:
        return ReplicaBlockReasonV1.DECISION_ORIGIN_INVALID
    if (
        decision.target_kind is not ActionTargetKindV1.REPOSITORY_FIXTURE
        or context.target_kind is not ActionTargetKindV1.REPOSITORY_FIXTURE
    ):
        return ReplicaBlockReasonV1.TARGET_KIND_INVALID
    try:
        require_action_eligible(
            decision,
            expected_kind=PathIActionKind.NAS_REPLICA_SYNC,
            expected_context=context,
            expected_origin=ActionDecisionOriginV1.REPOSITORY_FIXTURE,
        )
    except (PathIEligibilityError, ValueError, TypeError):
        return invalid
    return ReplicaBlockReasonV1.NONE


def _validate_commit_recheck(
    preflight: ReplicaPreflightV1,
    commit_decision: object,
    commit_context: object,
) -> ReplicaBlockReasonV1:
    """要求 commit 是同一授权绑定上严格晚于 preflight 的重新判定。"""

    authorization_reason = _validate_sync_authorization(
        commit_decision,
        commit_context,
        commit=True,
    )
    if authorization_reason is not ReplicaBlockReasonV1.NONE:
        return authorization_reason
    if not isinstance(preflight, ReplicaPreflightV1):
        return ReplicaBlockReasonV1.COMMIT_AUTHORIZATION_INVALID
    if not isinstance(commit_decision, ActionDecisionV1) or not isinstance(
        commit_context, ActionScopeContextV1
    ):
        return ReplicaBlockReasonV1.COMMIT_AUTHORIZATION_INVALID
    if commit_context != preflight.action_context:
        return ReplicaBlockReasonV1.CONTEXT_MISMATCH
    first = preflight.preflight_decision
    if (
        commit_decision.action_kind is not first.action_kind
        or commit_decision.decision_origin is not first.decision_origin
        or commit_decision.target_kind is not first.target_kind
    ):
        return ReplicaBlockReasonV1.COMMIT_AUTHORIZATION_INVALID
    if commit_decision.evaluated_at <= first.evaluated_at:
        return ReplicaBlockReasonV1.COMMIT_DECISION_NOT_FRESH
    return ReplicaBlockReasonV1.NONE


def _validate_source_versions(
    bundle: SealedTrialReturnBundleV1,
    selection: ResearchCanonicalSelectionV1,
) -> ReplicaBlockReasonV1:
    if (
        bundle.payload.schema_version != "trial-return-payload.v1"
        or bundle.manifest.schema_version != "trial-return-manifest.v1"
        or bundle.seal.seal_version != "artifact-seal.v1"
        or selection.selection_version != "research-canonical-selection.v1"
    ):
        return ReplicaBlockReasonV1.SOURCE_UNVERSIONED
    if (
        bundle.manifest.object_kind != "trial_portfolio_return_series@v1"
        or bundle.manifest.seal_status != "sealed"
    ):
        return ReplicaBlockReasonV1.SOURCE_KIND_INVALID
    if (
        selection.decision_origin is not ActionDecisionOriginV1.REPOSITORY_FIXTURE
        or bundle.seal.logical_uri != selection.logical_uri
    ):
        return ReplicaBlockReasonV1.DECISION_ORIGIN_INVALID
    if selection.target_kind is not ActionTargetKindV1.REPOSITORY_FIXTURE:
        return ReplicaBlockReasonV1.TARGET_KIND_INVALID
    return ReplicaBlockReasonV1.NONE


def _validate_source_context(
    verified: VerifiedTrialReturnBundleV1,
    context: ActionScopeContextV1,
) -> ReplicaBlockReasonV1:
    manifest = verified.bundle.manifest
    if (
        manifest.release_id != context.release_id
        or manifest.run_id != context.run_id
        or manifest.family_id != context.family_id
    ):
        return ReplicaBlockReasonV1.CONTEXT_MISMATCH
    return ReplicaBlockReasonV1.NONE


def _validate_source_expectation(
    request: ReplicaSyncRequestV1,
    verified: VerifiedTrialReturnBundleV1,
) -> ReplicaBlockReasonV1:
    bundle = verified.bundle
    selection = verified.selection
    if (
        bundle.seal.release_id != request.expected_release_id
        or bundle.manifest.release_id != request.expected_release_id
        or selection.release_id != request.expected_release_id
    ):
        return ReplicaBlockReasonV1.RELEASE_MISMATCH
    if (
        bundle.seal.logical_uri != request.expected_logical_uri
        or bundle.manifest.logical_uri != request.expected_logical_uri
        or selection.logical_uri != request.expected_logical_uri
    ):
        return ReplicaBlockReasonV1.LOGICAL_URI_MISMATCH
    if not hmac.compare_digest(
        bundle.payload.content_sha256,
        request.expected_content_sha256,
    ):
        return ReplicaBlockReasonV1.CONTENT_MISMATCH
    if not hmac.compare_digest(
        bundle.manifest_sha256,
        request.expected_manifest_sha256,
    ):
        return ReplicaBlockReasonV1.MANIFEST_MISMATCH
    if not hmac.compare_digest(
        verified.original_seal_sha256,
        selection.original_seal_sha256,
    ):
        return ReplicaBlockReasonV1.SEAL_MISMATCH
    return ReplicaBlockReasonV1.NONE


def _validate_port_binding(
    preflight: ReplicaPreflightV1,
    mapping: object,
    storage_port: object,
) -> ReplicaBlockReasonV1:
    if not isinstance(mapping, ReplicaDeploymentMappingV1):
        return ReplicaBlockReasonV1.PORT_BINDING_INVALID
    if not isinstance(storage_port, ReplicaStoragePortV1):
        return ReplicaBlockReasonV1.PORT_BINDING_INVALID
    if storage_port.mapping != mapping:
        return ReplicaBlockReasonV1.PORT_BINDING_INVALID
    if (
        mapping.repository_owned is not True
        or mapping.decision_origin
        is not ActionDecisionOriginV1.REPOSITORY_FIXTURE
        or mapping.target_kind is not ActionTargetKindV1.REPOSITORY_FIXTURE
        or mapping.logical_uri != preflight.request.expected_logical_uri
    ):
        return ReplicaBlockReasonV1.PORT_BINDING_INVALID
    return ReplicaBlockReasonV1.NONE


def _make_verification_vector(
    preflight: ReplicaPreflightV1,
    staged: VerifiedTrialReturnBundleV1,
) -> ReplicaVerificationVectorV1:
    request = preflight.request
    source = preflight.verified_source
    return ReplicaVerificationVectorV1(
        seal=hmac.compare_digest(
            staged.original_seal_sha256,
            source.original_seal_sha256,
        )
        and hmac.compare_digest(
            staged.original_seal_sha256,
            staged.selection.original_seal_sha256,
        ),
        manifest=hmac.compare_digest(
            staged.bundle.manifest_sha256,
            request.expected_manifest_sha256,
        ),
        content=hmac.compare_digest(
            staged.bundle.payload.content_sha256,
            request.expected_content_sha256,
        ),
        release=(
            staged.bundle.seal.release_id == request.expected_release_id
            and staged.bundle.manifest.release_id == request.expected_release_id
            and staged.selection.release_id == request.expected_release_id
        ),
        freshness=hmac.compare_digest(
            preflight.source_selection_sha256,
            request.expected_source_selection_sha256,
        ),
    )


def _vector_failure_reason(
    preflight: ReplicaPreflightV1,
    staged: VerifiedTrialReturnBundleV1,
    vector: ReplicaVerificationVectorV1,
) -> ReplicaBlockReasonV1:
    del preflight, staged
    if not vector.seal:
        return ReplicaBlockReasonV1.SEAL_MISMATCH
    if not vector.manifest:
        return ReplicaBlockReasonV1.MANIFEST_MISMATCH
    if not vector.content:
        return ReplicaBlockReasonV1.CONTENT_MISMATCH
    if not vector.release:
        return ReplicaBlockReasonV1.RELEASE_MISMATCH
    if not vector.freshness:
        return ReplicaBlockReasonV1.STALE_SOURCE_SELECTION
    return ReplicaBlockReasonV1.VERIFICATION_INCOMPLETE


def _make_replica_version_ref(
    preflight: ReplicaPreflightV1,
    staged: VerifiedTrialReturnBundleV1,
) -> str:
    digest = staged.original_seal_sha256.removeprefix("sha256:")
    return (
        f"replica:{preflight.request.expected_release_id}:"
        f"{preflight.request.request_id}:{digest}"
    )


def _make_receipt(
    candidate: VerifiedReplicaCandidateV1,
    commit_decision: ActionDecisionV1,
) -> ReplicaVerificationReceiptV1:
    preflight = candidate.preflight
    staged = candidate.staged_verified
    values = {
        "schema_version": REPLICA_RECEIPT_VERSION,
        "authority": REPLICA_AUTHORITY,
        "release_id": preflight.request.expected_release_id,
        "logical_uri": preflight.request.expected_logical_uri,
        "content_sha256": preflight.request.expected_content_sha256,
        "manifest_sha256": preflight.request.expected_manifest_sha256,
        "source_selection_sha256": preflight.source_selection_sha256,
        "original_seal_sha256": staged.original_seal_sha256,
        "decision_origin": staged.selection.decision_origin,
        "target_kind": staged.selection.target_kind,
        "verification_vector": candidate.verification_vector,
        "preflight_authorization_evidence_refs": (
            preflight.preflight_authorization_evidence_refs
        ),
        "commit_authorization_evidence_refs": (
            commit_decision.approval_ref,
            commit_decision.evidence_ref,
        ),
        "replica_version_ref": candidate.replica_version_ref,
    }
    body = _canonical_json_bytes(
        {
            "authority": values["authority"],
            "commit_authorization_evidence_refs": values[
                "commit_authorization_evidence_refs"
            ],
            "content_sha256": values["content_sha256"],
            "decision_origin": values["decision_origin"],
            "logical_uri": values["logical_uri"],
            "manifest_sha256": values["manifest_sha256"],
            "original_seal_sha256": values["original_seal_sha256"],
            "preflight_authorization_evidence_refs": values[
                "preflight_authorization_evidence_refs"
            ],
            "release_id": values["release_id"],
            "replica_version_ref": values["replica_version_ref"],
            "schema_version": values["schema_version"],
            "source_selection_sha256": values["source_selection_sha256"],
            "target_kind": values["target_kind"],
            "verification_vector": {
                "content": candidate.verification_vector.content,
                "freshness": candidate.verification_vector.freshness,
                "manifest": candidate.verification_vector.manifest,
                "release": candidate.verification_vector.release,
                "seal": candidate.verification_vector.seal,
            },
        }
    )
    return ReplicaVerificationReceiptV1(
        **values,
        receipt_sha256=_sha256_prefixed(REPLICA_RECEIPT_HASH_DOMAIN + body),
    )


def _source_selection_sha256(
    selection: ResearchCanonicalSelectionV1,
) -> str:
    body = _canonical_json_bytes(
        {
            "content_sha256": selection.content_sha256,
            "decision_origin": selection.decision_origin,
            "logical_uri": selection.logical_uri,
            "manifest_sha256": selection.manifest_sha256,
            "original_seal_sha256": selection.original_seal_sha256,
            "release_id": selection.release_id,
            "selected_at": selection.selected_at,
            "selection_version": selection.selection_version,
            "target_kind": selection.target_kind,
        }
    )
    return _sha256_prefixed(SOURCE_SELECTION_HASH_DOMAIN + body)


def _require_selected_tuple_matches(
    distribution: DistributionSelectionV1,
    selected: object,
) -> None:
    if not isinstance(selected, tuple) or len(selected) != 3:
        raise ReplicaStoragePortError(
            ReplicaBlockReasonV1.SELECTED_REPLICA_MISMATCH
        )
    bundle, source_selection, receipt = selected
    if (
        not isinstance(bundle, SealedTrialReturnBundleV1)
        or not isinstance(source_selection, ResearchCanonicalSelectionV1)
        or not isinstance(receipt, ReplicaVerificationReceiptV1)
        or receipt.replica_version_ref != distribution.replica_version_ref
        or receipt.receipt_sha256 != distribution.receipt_sha256
        or receipt.source_selection_sha256
        != distribution.source_selection_sha256
        or receipt.release_id != distribution.release_id
        or receipt.logical_uri != distribution.logical_uri
        or receipt.content_sha256 != distribution.content_sha256
        or receipt.manifest_sha256 != distribution.manifest_sha256
        or receipt.original_seal_sha256 != distribution.original_seal_sha256
        or source_selection.release_id != distribution.release_id
        or source_selection.logical_uri != distribution.logical_uri
        or source_selection.content_sha256 != distribution.content_sha256
        or source_selection.manifest_sha256 != distribution.manifest_sha256
        or source_selection.original_seal_sha256
        != distribution.original_seal_sha256
        or source_selection.decision_origin is not distribution.decision_origin
        or source_selection.target_kind is not distribution.target_kind
        or bundle.payload.content_sha256 != distribution.content_sha256
        or bundle.manifest_sha256 != distribution.manifest_sha256
        or bundle.manifest.release_id != distribution.release_id
        or bundle.manifest.logical_uri != distribution.logical_uri
    ):
        raise ReplicaStoragePortError(
            ReplicaBlockReasonV1.SELECTED_REPLICA_MISMATCH
        )


def _map_source_integrity_reason(
    exc: Exception,
    *,
    staged: bool,
) -> ReplicaBlockReasonV1:
    reason = str(getattr(exc, "reason_code", exc))
    if "PAYLOAD" in reason or "CONTENT" in reason:
        return ReplicaBlockReasonV1.CONTENT_MISMATCH
    if "MANIFEST" in reason:
        return ReplicaBlockReasonV1.MANIFEST_MISMATCH
    if "SEAL" in reason:
        return ReplicaBlockReasonV1.SEAL_MISMATCH
    if "SELECTION" in reason:
        return ReplicaBlockReasonV1.STALE_SOURCE_SELECTION
    return (
        ReplicaBlockReasonV1.STAGING_INTEGRITY_INVALID
        if staged
        else ReplicaBlockReasonV1.SOURCE_INTEGRITY_INVALID
    )


def _blocked(
    reason: ReplicaBlockReasonV1,
    previous: DistributionSelectionV1 | None = None,
) -> ReplicaPublishResultV1:
    return ReplicaPublishResultV1(
        status=ReplicaPublishStatusV1.BLOCKED,
        reason=reason,
        receipt=None,
        selection=None,
        previous_selection=previous,
    )


def _safe_current_selection(
    storage_port: object,
) -> DistributionSelectionV1 | None:
    if not isinstance(storage_port, ReplicaStoragePortV1):
        return None
    try:
        current = storage_port.current_selection
    except Exception:
        return None
    return current if isinstance(current, DistributionSelectionV1) else None


def _canonical_json_bytes(value: object) -> bytes:
    normalized = _normalize_json_value(value)
    try:
        text = json.dumps(
            normalized,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        )
    except (TypeError, ValueError) as exc:
        raise ReplicaContractError("CANONICAL_JSON_INVALID") from exc
    return text.encode("utf-8")


def _normalize_json_value(value: object) -> object:
    from datetime import datetime, timezone

    if isinstance(value, datetime):
        if value.tzinfo is None or value.utcoffset() is None:
            raise ReplicaContractError("CANONICAL_DATETIME_INVALID")
        utc_value = value.astimezone(timezone.utc)
        return utc_value.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, str):
        return unicodedata.normalize("NFC", value)
    if isinstance(value, tuple):
        return [_normalize_json_value(item) for item in value]
    if isinstance(value, list):
        return [_normalize_json_value(item) for item in value]
    if isinstance(value, dict):
        if not all(isinstance(key, str) for key in value):
            raise ReplicaContractError("CANONICAL_JSON_KEY_INVALID")
        return {
            unicodedata.normalize("NFC", key): _normalize_json_value(item)
            for key, item in value.items()
        }
    if value is None or type(value) in {bool, int}:
        return value
    raise ReplicaContractError("CANONICAL_JSON_TYPE_INVALID")


def _sha256_prefixed(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def _require_identifier(name: str, value: object) -> None:
    if not isinstance(value, str) or not _IDENTIFIER_RE.fullmatch(value):
        raise ReplicaContractError(f"{name.upper()}_INVALID")
    if value.startswith("/") or ".." in value.split("/"):
        raise ReplicaContractError(f"{name.upper()}_INVALID")


def _require_relative_handle(name: str, value: object) -> None:
    if (
        not isinstance(value, str)
        or not value
        or value.startswith(("/", "\\"))
        or "\\" in value
        or any(part in {"", ".", ".."} for part in value.split("/"))
        or any(marker in value.lower() for marker in _FORBIDDEN_REF_MARKERS)
    ):
        raise ReplicaContractError(f"{name.upper()}_INVALID")


def _require_evidence_pair(name: str, value: object) -> None:
    if not isinstance(value, tuple) or len(value) != 2:
        raise ReplicaContractError(f"{name.upper()}_INVALID")
    for ref in value:
        if (
            not isinstance(ref, str)
            or not ref
            or ref.startswith(("/", "\\"))
            or "\\" in ref
            or ".." in ref.split("/")
            or any(marker in ref.lower() for marker in _FORBIDDEN_REF_MARKERS)
        ):
            raise ReplicaContractError(f"{name.upper()}_INVALID")


def _require_fixture_uri(value: object) -> str:
    if (
        not isinstance(value, str)
        or not value
        or not value.isascii()
        or "%" in value
        or "\\" in value
        or any(marker in value for marker in ("*", "?", "#"))
        or any(marker in value.lower() for marker in _FORBIDDEN_REF_MARKERS)
    ):
        raise ReplicaContractError("FIXTURE_URI_INVALID")
    try:
        parsed = urlsplit(value)
        port = parsed.port
    except ValueError as exc:
        raise ReplicaContractError("FIXTURE_URI_INVALID") from exc
    if (
        parsed.scheme != "fixture"
        or not value.startswith("fixture://")
        or parsed.hostname not in _FIXTURE_AUTHORITIES
        or parsed.netloc != parsed.netloc.lower()
        or port is not None
        or parsed.username is not None
        or parsed.password is not None
        or parsed.query
        or parsed.fragment
        or not parsed.path.startswith("/")
        or any(part in {"", ".", ".."} for part in parsed.path.split("/")[1:])
    ):
        raise ReplicaContractError("FIXTURE_URI_INVALID")
    return value


def _require_sha256(name: str, value: object) -> None:
    if not isinstance(value, str) or not _SHA256_RE.fullmatch(value):
        raise ReplicaContractError(f"{name.upper()}_INVALID")
