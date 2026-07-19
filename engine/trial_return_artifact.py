"""Repository-local trial-return artifact v1 纯合同。

本模块只处理显式提供的 repository fixture observations，并在内存中完成
payload、manifest、seal、verification 与 fixture commit。它不读取 runner、
lineage、环境变量、文件系统、数据湖或 NAS，也不提供真实 canonical adapter。
"""

from __future__ import annotations

from dataclasses import dataclass, fields
from datetime import datetime, timezone
from enum import Enum
import hashlib
import json
import math
import re
from typing import Final, Sequence
import unicodedata
from urllib.parse import urlsplit

import pyarrow as pa
import pyarrow.parquet as pq

from engine.path_i_governance import (
    ActionDecisionOriginV1,
    ActionDecisionV1,
    ActionScopeContextV1,
    ActionTargetKindV1,
    PathIActionKind,
    PathIEligibilityError,
    require_action_eligible,
)


__all__ = (
    "SealedTrialReturnBundleV1",
    "ResearchCanonicalSelectionV1",
    "VerifiedTrialReturnBundleV1",
    "canonical_artifact_seal_bytes",
    "canonical_artifact_seal_sha256",
    "verify_sealed_trial_return_bundle",
)


TRIAL_RETURN_OBJECT_KIND: Final = "trial_portfolio_return_series@v1"
FORWARD_LABEL_PROXY_OBJECT_KIND: Final = "forward_label_proxy@v1"
RETURN_DEFINITION_SCHEMA_VERSION: Final = "trial-return-definition.v1"
PAYLOAD_SCHEMA_VERSION: Final = "trial-return-payload.v1"
MANIFEST_SCHEMA_VERSION: Final = "trial-return-manifest.v1"
SEAL_VERSION: Final = "artifact-seal.v1"
SELECTION_VERSION: Final = "research-canonical-selection.v1"
RETURN_BASIS_V1: Final = "portfolio_period_simple_return"
ENDPOINT_SEMANTICS_V1: Final = "timestamp_is_interval_end"
ALIGNMENT_POLICY_V1: Final = "strict_non_overlapping_utc_intervals"
PARQUET_WRITER_PROFILE: Final = "trial-return-parquet-v1"
PRODUCER_CONTRACT_VERSION: Final = (
    "trial-return-artifact.v1+trial-return-parquet-v1+pyarrow-16.1.0"
)
REPOSITORY_FIXTURE_PORT_CAPABILITY_VERSION: Final = (
    "repository-fixture-trial-return-port.v1"
)

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

_PAYLOAD_ARROW_SCHEMA: Final = pa.schema(
    [
        pa.field("timestamp", pa.timestamp("us", tz="UTC"), nullable=False),
        pa.field("simple_return", pa.float64(), nullable=False),
    ]
)


class TrialReturnContractError(ValueError):
    """稳定 reason code 表示输入不满足 trial-return v1 合同。"""

    def __init__(self, reason_code: str, opaque_id: str = "") -> None:
        self.reason_code = reason_code
        self.opaque_id = opaque_id
        message = reason_code if not opaque_id else f"{reason_code}:{opaque_id}"
        super().__init__(message)


class TrialReturnAuthorizationError(TrialReturnContractError):
    """generation decision/context/fixture target 不满足绑定。"""


class TrialReturnIntegrityError(TrialReturnContractError):
    """payload、manifest、seal 或 selection 完整性校验失败。"""


class TrialReturnFixturePortError(TrialReturnContractError):
    """verified bundle 提交到 repository fixture port 失败。"""


class TrialReturnSourceKindV1(str, Enum):
    TRIAL_PORTFOLIO_RETURN_SERIES = TRIAL_RETURN_OBJECT_KIND
    FORWARD_LABEL_PROXY = FORWARD_LABEL_PROXY_OBJECT_KIND


@dataclass(frozen=True, slots=True)
class TrialReturnObservationV1:
    interval_start: datetime
    timestamp: datetime
    simple_return: float

    def __post_init__(self) -> None:
        start = _require_utc_datetime("interval_start", self.interval_start)
        end = _require_utc_datetime("timestamp", self.timestamp)
        if start >= end:
            raise TrialReturnContractError("INTERVAL_NOT_POSITIVE")
        if isinstance(self.simple_return, bool) or not isinstance(
            self.simple_return, (int, float)
        ):
            raise TrialReturnContractError("SIMPLE_RETURN_NOT_NUMERIC")
        simple_return = float(self.simple_return)
        if not math.isfinite(simple_return) or simple_return < -1.0:
            raise TrialReturnContractError("SIMPLE_RETURN_OUT_OF_DOMAIN")
        object.__setattr__(self, "interval_start", start)
        object.__setattr__(self, "timestamp", end)
        object.__setattr__(self, "simple_return", simple_return)


@dataclass(frozen=True, slots=True)
class ReturnDefinitionV1:
    object_kind: TrialReturnSourceKindV1
    schema_version: str
    return_basis: str
    endpoint_semantics: str
    non_overlap_required: bool
    alignment_policy: str

    def __post_init__(self) -> None:
        try:
            kind = TrialReturnSourceKindV1(self.object_kind)
        except (TypeError, ValueError) as exc:
            raise TrialReturnContractError("OBJECT_KIND_UNSUPPORTED") from exc
        object.__setattr__(self, "object_kind", kind)
        if self.schema_version != RETURN_DEFINITION_SCHEMA_VERSION:
            raise TrialReturnContractError("DEFINITION_SCHEMA_UNSUPPORTED")
        if self.return_basis != RETURN_BASIS_V1:
            raise TrialReturnContractError("RETURN_BASIS_UNSUPPORTED")
        if self.endpoint_semantics != ENDPOINT_SEMANTICS_V1:
            raise TrialReturnContractError("ENDPOINT_SEMANTICS_REQUIRED")
        if self.non_overlap_required is not True:
            raise TrialReturnContractError("NON_OVERLAP_REQUIRED")
        if self.alignment_policy != ALIGNMENT_POLICY_V1:
            raise TrialReturnContractError("ALIGNMENT_POLICY_UNSUPPORTED")


@dataclass(frozen=True, slots=True)
class TrialReturnIdentityV1:
    family_id: str
    run_id: str
    trial_id: str
    release_id: str
    logical_uri: str

    def __post_init__(self) -> None:
        for name in ("family_id", "run_id", "trial_id", "release_id"):
            _require_identifier(name, getattr(self, name))
        _require_fixture_uri(self.logical_uri)


@dataclass(frozen=True, slots=True)
class TrialReturnPayloadV1:
    schema_version: str
    payload_bytes: bytes
    row_count: int
    observation_window: tuple[datetime, datetime]
    content_sha256: str

    def __post_init__(self) -> None:
        if self.schema_version != PAYLOAD_SCHEMA_VERSION:
            raise TrialReturnContractError("PAYLOAD_SCHEMA_UNSUPPORTED")
        if not isinstance(self.payload_bytes, bytes) or not self.payload_bytes:
            raise TrialReturnContractError("PAYLOAD_BYTES_REQUIRED")
        if isinstance(self.row_count, bool) or not isinstance(self.row_count, int):
            raise TrialReturnContractError("ROW_COUNT_INVALID")
        if self.row_count <= 0:
            raise TrialReturnContractError("ROW_COUNT_INVALID")
        window = _require_observation_window(self.observation_window)
        object.__setattr__(self, "observation_window", window)
        _require_sha256("content_sha256", self.content_sha256)


@dataclass(frozen=True, slots=True)
class TrialReturnManifestV1:
    object_kind: str
    schema_version: str
    family_id: str
    run_id: str
    trial_id: str
    logical_uri: str
    return_basis: str
    source_lineage_refs: tuple[str, ...]
    row_count: int
    observation_window: tuple[datetime, datetime]
    content_sha256: str
    producer_contract_version: str
    release_id: str
    created_at: datetime
    seal_status: str

    def __post_init__(self) -> None:
        if len(fields(type(self))) != 15:
            raise RuntimeError("manifest semantics 必须为 15/15")
        if self.object_kind != TRIAL_RETURN_OBJECT_KIND:
            raise TrialReturnContractError("MANIFEST_OBJECT_KIND_INVALID")
        if self.schema_version != MANIFEST_SCHEMA_VERSION:
            raise TrialReturnContractError("MANIFEST_SCHEMA_UNSUPPORTED")
        for name in ("family_id", "run_id", "trial_id", "release_id"):
            _require_identifier(name, getattr(self, name))
        _require_fixture_uri(self.logical_uri)
        if self.return_basis != RETURN_BASIS_V1:
            raise TrialReturnContractError("RETURN_BASIS_UNSUPPORTED")
        refs = _require_opaque_refs("source_lineage_refs", self.source_lineage_refs)
        object.__setattr__(self, "source_lineage_refs", refs)
        if isinstance(self.row_count, bool) or not isinstance(self.row_count, int):
            raise TrialReturnContractError("ROW_COUNT_INVALID")
        if self.row_count <= 0:
            raise TrialReturnContractError("ROW_COUNT_INVALID")
        window = _require_observation_window(self.observation_window)
        object.__setattr__(self, "observation_window", window)
        _require_sha256("content_sha256", self.content_sha256)
        if self.producer_contract_version != PRODUCER_CONTRACT_VERSION:
            raise TrialReturnContractError("PRODUCER_CONTRACT_UNSUPPORTED")
        object.__setattr__(
            self,
            "created_at",
            _require_utc_datetime("created_at", self.created_at),
        )
        if self.seal_status != "sealed":
            raise TrialReturnContractError("SEAL_STATUS_INVALID")


@dataclass(frozen=True, slots=True)
class ArtifactSealV1:
    seal_version: str
    logical_uri: str
    content_sha256: str
    manifest_sha256: str
    release_id: str
    sealed_at: datetime
    producer_contract_version: str
    authorization_evidence_refs: tuple[str, ...]

    def __post_init__(self) -> None:
        if len(fields(type(self))) != 8:
            raise RuntimeError("seal semantics 必须为 8/8")
        if self.seal_version != SEAL_VERSION:
            raise TrialReturnContractError("SEAL_VERSION_UNSUPPORTED")
        _require_fixture_uri(self.logical_uri)
        _require_sha256("content_sha256", self.content_sha256)
        _require_sha256("manifest_sha256", self.manifest_sha256)
        _require_identifier("release_id", self.release_id)
        object.__setattr__(
            self,
            "sealed_at",
            _require_utc_datetime("sealed_at", self.sealed_at),
        )
        if self.producer_contract_version != PRODUCER_CONTRACT_VERSION:
            raise TrialReturnContractError("PRODUCER_CONTRACT_UNSUPPORTED")
        refs = _require_opaque_refs(
            "authorization_evidence_refs",
            self.authorization_evidence_refs,
        )
        object.__setattr__(self, "authorization_evidence_refs", refs)


@dataclass(frozen=True, slots=True)
class SealedTrialReturnBundleV1:
    payload: TrialReturnPayloadV1
    manifest: TrialReturnManifestV1
    manifest_sha256: str
    seal: ArtifactSealV1

    def __post_init__(self) -> None:
        if not isinstance(self.payload, TrialReturnPayloadV1):
            raise TrialReturnIntegrityError("PAYLOAD_TYPE_INVALID")
        if not isinstance(self.manifest, TrialReturnManifestV1):
            raise TrialReturnIntegrityError("MANIFEST_TYPE_INVALID")
        _require_sha256("manifest_sha256", self.manifest_sha256)
        if not isinstance(self.seal, ArtifactSealV1):
            raise TrialReturnIntegrityError("SEAL_TYPE_INVALID")


@dataclass(frozen=True, slots=True)
class ResearchCanonicalSelectionV1:
    selection_version: str
    release_id: str
    logical_uri: str
    content_sha256: str
    manifest_sha256: str
    original_seal_sha256: str
    decision_origin: ActionDecisionOriginV1
    target_kind: ActionTargetKindV1
    selected_at: datetime

    def __post_init__(self) -> None:
        if self.selection_version != SELECTION_VERSION:
            raise TrialReturnIntegrityError("SELECTION_VERSION_UNSUPPORTED")
        _require_identifier("release_id", self.release_id)
        _require_fixture_uri(self.logical_uri)
        for name in (
            "content_sha256",
            "manifest_sha256",
            "original_seal_sha256",
        ):
            _require_sha256(name, getattr(self, name))
        if self.decision_origin is not ActionDecisionOriginV1.REPOSITORY_FIXTURE:
            raise TrialReturnAuthorizationError("SELECTION_ORIGIN_NOT_FIXTURE")
        if self.target_kind is not ActionTargetKindV1.REPOSITORY_FIXTURE:
            raise TrialReturnAuthorizationError("SELECTION_TARGET_NOT_FIXTURE")
        object.__setattr__(
            self,
            "selected_at",
            _require_utc_datetime("selected_at", self.selected_at),
        )


@dataclass(frozen=True, slots=True, init=False)
class VerifiedTrialReturnBundleV1:
    bundle: SealedTrialReturnBundleV1
    selection: ResearchCanonicalSelectionV1
    original_seal_sha256: str

    def __init__(self, *_args: object, **_kwargs: object) -> None:
        raise TrialReturnIntegrityError("VERIFIER_CONSTRUCTION_REQUIRED")


@dataclass(frozen=True, slots=True)
class AppendOnlyLineageAuditV1:
    state: str
    observed_event_refs: tuple[str, ...]
    erase_events: bool
    fake_rollback: bool
    canonical_selection_advance: bool

    def __post_init__(self) -> None:
        refs = _require_opaque_refs("observed_event_refs", self.observed_event_refs)
        object.__setattr__(self, "observed_event_refs", refs)
        if self.state != "partial_lineage_blocked_audit":
            raise TrialReturnContractError("LINEAGE_AUDIT_STATE_INVALID")
        if (
            self.erase_events is not False
            or self.fake_rollback is not False
            or self.canonical_selection_advance is not False
        ):
            raise TrialReturnContractError("LINEAGE_AUDIT_MUST_NOT_ROLL_BACK")


@dataclass(frozen=True, slots=True)
class _RepositoryFixturePortBindingV1:
    capability_version: str
    repository_owned: bool
    decision_origin: ActionDecisionOriginV1
    target_kind: ActionTargetKindV1
    scope_revision: str
    scope_sha256: str
    release_id: str
    run_id: str
    family_id: str
    logical_uri: str
    authorization_id: str
    approval_ref: str
    evidence_ref: str

    def __post_init__(self) -> None:
        if self.capability_version != REPOSITORY_FIXTURE_PORT_CAPABILITY_VERSION:
            raise TrialReturnFixturePortError("FIXTURE_PORT_CAPABILITY_INVALID")
        if self.repository_owned is not True:
            raise TrialReturnFixturePortError("FIXTURE_PORT_NOT_REPOSITORY_OWNED")
        if self.decision_origin is not ActionDecisionOriginV1.REPOSITORY_FIXTURE:
            raise TrialReturnFixturePortError("FIXTURE_PORT_ORIGIN_INVALID")
        if self.target_kind is not ActionTargetKindV1.REPOSITORY_FIXTURE:
            raise TrialReturnFixturePortError("FIXTURE_PORT_TARGET_INVALID")
        for name in (
            "scope_revision",
            "release_id",
            "run_id",
            "family_id",
            "authorization_id",
        ):
            _require_identifier(name, getattr(self, name))
        _require_sha256("scope_sha256", self.scope_sha256)
        _require_fixture_uri(self.logical_uri)
        _require_opaque_refs(
            "fixture_port_authorization_refs",
            (self.approval_ref, self.evidence_ref),
        )


class RepositoryFixtureTrialReturnPortV1:
    """Repository-owned nominal in-memory fixture port。

    该类是 S02 唯一可接受的 port capability。Publisher 使用 exact type 与
    immutable binding 做 pre-side-effect 校验；任意 subclass、结构兼容冒充
    或绑定漂移对象均不会被调用。
    """

    __slots__ = (
        "_binding",
        "_selected",
        "_call_count",
        "_commit_count",
        "_inject_atomic_failure",
    )

    def __init__(
        self,
        identity: TrialReturnIdentityV1,
        generation_decision: ActionDecisionV1,
        generation_context: ActionScopeContextV1,
        *,
        inject_atomic_failure: bool = False,
    ) -> None:
        _require_fixture_generation_authorization(
            identity,
            generation_decision,
            generation_context,
        )
        if type(inject_atomic_failure) is not bool:
            raise TrialReturnFixturePortError("FIXTURE_PORT_FAILURE_MODE_INVALID")
        self._binding = _make_repository_fixture_port_binding(
            identity,
            generation_decision,
            generation_context,
        )
        self._selected: VerifiedTrialReturnBundleV1 | None = None
        self._call_count = 0
        self._commit_count = 0
        self._inject_atomic_failure = inject_atomic_failure

    @property
    def binding(self) -> _RepositoryFixturePortBindingV1:
        return self._binding

    @property
    def selected(self) -> VerifiedTrialReturnBundleV1 | None:
        return self._selected

    @property
    def call_count(self) -> int:
        return self._call_count

    @property
    def commit_count(self) -> int:
        return self._commit_count

    def commit_verified(self, verified: VerifiedTrialReturnBundleV1) -> None:
        """原子提交 verified selection；受控失败发生在 selection 写入之前。"""

        _require_verified_matches_port_binding(verified, self._binding)
        self._call_count += 1
        if self._inject_atomic_failure:
            raise TrialReturnFixturePortError("FIXTURE_PORT_CONTROLLED_FAILURE")
        self._selected = verified
        self._commit_count += 1


def prepare_repository_fixture_candidate(
    identity: TrialReturnIdentityV1,
    observations: Sequence[TrialReturnObservationV1],
    definition: ReturnDefinitionV1,
    *,
    created_at: datetime,
    source_lineage_refs: tuple[str, ...],
) -> tuple[TrialReturnPayloadV1, TrialReturnManifestV1]:
    """从显式 period-return fixture 生成 payload 和 15-field manifest。"""

    if not isinstance(identity, TrialReturnIdentityV1):
        raise TrialReturnContractError("IDENTITY_TYPE_INVALID")
    if not isinstance(definition, ReturnDefinitionV1):
        raise TrialReturnContractError("DEFINITION_TYPE_INVALID")
    if definition.object_kind is not TrialReturnSourceKindV1.TRIAL_PORTFOLIO_RETURN_SERIES:
        raise TrialReturnContractError("FORWARD_LABEL_PROXY_FORBIDDEN")
    ordered = _validate_and_order_observations(observations)
    created_at_utc = _require_utc_datetime("created_at", created_at)
    refs = _require_opaque_refs("source_lineage_refs", source_lineage_refs)
    payload_bytes = _serialize_payload(ordered)
    observation_window = (ordered[0].interval_start, ordered[-1].timestamp)
    payload = TrialReturnPayloadV1(
        schema_version=PAYLOAD_SCHEMA_VERSION,
        payload_bytes=payload_bytes,
        row_count=len(ordered),
        observation_window=observation_window,
        content_sha256=_sha256_prefixed(payload_bytes),
    )
    manifest = TrialReturnManifestV1(
        object_kind=TRIAL_RETURN_OBJECT_KIND,
        schema_version=MANIFEST_SCHEMA_VERSION,
        family_id=identity.family_id,
        run_id=identity.run_id,
        trial_id=identity.trial_id,
        logical_uri=identity.logical_uri,
        return_basis=definition.return_basis,
        source_lineage_refs=refs,
        row_count=payload.row_count,
        observation_window=payload.observation_window,
        content_sha256=payload.content_sha256,
        producer_contract_version=PRODUCER_CONTRACT_VERSION,
        release_id=identity.release_id,
        created_at=created_at_utc,
        seal_status="sealed",
    )
    return payload, manifest


def canonical_artifact_seal_bytes(seal: ArtifactSealV1) -> bytes:
    """返回 ArtifactSealV1 唯一 versioned canonical JSON bytes。"""

    if not isinstance(seal, ArtifactSealV1):
        raise TrialReturnIntegrityError("SEAL_TYPE_INVALID")
    return _canonical_json_bytes(
        {
            "authorization_evidence_refs": seal.authorization_evidence_refs,
            "content_sha256": seal.content_sha256,
            "logical_uri": seal.logical_uri,
            "manifest_sha256": seal.manifest_sha256,
            "producer_contract_version": seal.producer_contract_version,
            "release_id": seal.release_id,
            "seal_version": seal.seal_version,
            "sealed_at": seal.sealed_at,
        }
    )


def canonical_artifact_seal_sha256(seal: ArtifactSealV1) -> str:
    """只对 canonical_artifact_seal_bytes 的结果计算 lowercase SHA-256。"""

    return _sha256_prefixed(canonical_artifact_seal_bytes(seal))


def verify_sealed_trial_return_bundle(
    bundle: SealedTrialReturnBundleV1,
    selection: ResearchCanonicalSelectionV1,
) -> VerifiedTrialReturnBundleV1:
    """复算 payload/manifest/seal，并只返回 verifier 构造的 verified value。"""

    if not isinstance(bundle, SealedTrialReturnBundleV1):
        raise TrialReturnIntegrityError("BUNDLE_TYPE_INVALID")
    if not isinstance(selection, ResearchCanonicalSelectionV1):
        raise TrialReturnIntegrityError("SELECTION_TYPE_INVALID")
    _verify_payload(bundle.payload)
    manifest_sha256 = _sha256_prefixed(_canonical_manifest_bytes(bundle.manifest))
    if manifest_sha256 != bundle.manifest_sha256:
        raise TrialReturnIntegrityError("MANIFEST_DIGEST_MISMATCH")
    if (
        bundle.manifest.content_sha256 != bundle.payload.content_sha256
        or bundle.manifest.row_count != bundle.payload.row_count
        or bundle.manifest.observation_window != bundle.payload.observation_window
    ):
        raise TrialReturnIntegrityError("PAYLOAD_MANIFEST_MISMATCH")
    seal = bundle.seal
    if (
        seal.logical_uri != bundle.manifest.logical_uri
        or seal.content_sha256 != bundle.payload.content_sha256
        or seal.manifest_sha256 != manifest_sha256
        or seal.release_id != bundle.manifest.release_id
        or seal.producer_contract_version != bundle.manifest.producer_contract_version
    ):
        raise TrialReturnIntegrityError("SEAL_BINDING_MISMATCH")
    original_seal_sha256 = canonical_artifact_seal_sha256(seal)
    if (
        selection.release_id != seal.release_id
        or selection.logical_uri != seal.logical_uri
        or selection.content_sha256 != seal.content_sha256
        or selection.manifest_sha256 != seal.manifest_sha256
        or selection.original_seal_sha256 != original_seal_sha256
    ):
        raise TrialReturnIntegrityError("SELECTION_BINDING_MISMATCH")
    return _verified_from_verifier(bundle, selection, original_seal_sha256)


def publish_repository_fixture_trial_return_artifact(
    identity: TrialReturnIdentityV1,
    observations: Sequence[TrialReturnObservationV1],
    definition: ReturnDefinitionV1,
    generation_decision: ActionDecisionV1,
    generation_context: ActionScopeContextV1,
    fixture_port: RepositoryFixtureTrialReturnPortV1,
    *,
    created_at: datetime,
    sealed_at: datetime,
    source_lineage_refs: tuple[str, ...],
) -> VerifiedTrialReturnBundleV1:
    """执行 guard→candidate→seal→verify→commit 的固定 fixture-only 顺序。"""

    _require_fixture_generation_authorization(
        identity,
        generation_decision,
        generation_context,
    )
    _require_repository_fixture_port_binding(
        fixture_port,
        identity,
        generation_decision,
        generation_context,
    )
    payload, manifest = prepare_repository_fixture_candidate(
        identity,
        observations,
        definition,
        created_at=created_at,
        source_lineage_refs=source_lineage_refs,
    )
    manifest_sha256 = _sha256_prefixed(_canonical_manifest_bytes(manifest))
    seal = ArtifactSealV1(
        seal_version=SEAL_VERSION,
        logical_uri=identity.logical_uri,
        content_sha256=payload.content_sha256,
        manifest_sha256=manifest_sha256,
        release_id=identity.release_id,
        sealed_at=sealed_at,
        producer_contract_version=PRODUCER_CONTRACT_VERSION,
        authorization_evidence_refs=(
            generation_decision.approval_ref,
            generation_decision.evidence_ref,
        ),
    )
    bundle = SealedTrialReturnBundleV1(
        payload=payload,
        manifest=manifest,
        manifest_sha256=manifest_sha256,
        seal=seal,
    )
    seal_sha256 = canonical_artifact_seal_sha256(seal)
    selection = ResearchCanonicalSelectionV1(
        selection_version=SELECTION_VERSION,
        release_id=identity.release_id,
        logical_uri=identity.logical_uri,
        content_sha256=payload.content_sha256,
        manifest_sha256=manifest_sha256,
        original_seal_sha256=seal_sha256,
        decision_origin=generation_decision.decision_origin,
        target_kind=generation_context.target_kind,
        selected_at=sealed_at,
    )
    verified = verify_sealed_trial_return_bundle(bundle, selection)
    _require_repository_fixture_port_binding(
        fixture_port,
        identity,
        generation_decision,
        generation_context,
    )
    try:
        fixture_port.commit_verified(verified)
    except Exception as exc:
        raise TrialReturnFixturePortError("FIXTURE_PORT_COMMIT_FAILED") from exc
    return verified


def classify_append_only_lineage_partial_success(
    observed_event_refs: tuple[str, ...],
) -> AppendOnlyLineageAuditV1:
    """只保留 append-only partial success 审计事实，不执行伪回滚。"""

    return AppendOnlyLineageAuditV1(
        state="partial_lineage_blocked_audit",
        observed_event_refs=observed_event_refs,
        erase_events=False,
        fake_rollback=False,
        canonical_selection_advance=False,
    )


def _require_fixture_generation_authorization(
    identity: TrialReturnIdentityV1,
    decision: ActionDecisionV1,
    context: ActionScopeContextV1,
) -> None:
    if not isinstance(identity, TrialReturnIdentityV1):
        raise TrialReturnAuthorizationError("IDENTITY_TYPE_INVALID")
    if not isinstance(context, ActionScopeContextV1):
        raise TrialReturnAuthorizationError("CONTEXT_TYPE_INVALID")
    if context.target_kind is not ActionTargetKindV1.REPOSITORY_FIXTURE:
        raise TrialReturnAuthorizationError("FIXTURE_TARGET_REQUIRED")
    if (
        identity.family_id != context.family_id
        or identity.run_id != context.run_id
        or identity.release_id != context.release_id
    ):
        raise TrialReturnAuthorizationError("IDENTITY_CONTEXT_MISMATCH")
    try:
        require_action_eligible(
            decision,
            expected_kind=PathIActionKind.TRIAL_RETURN_GENERATION,
            expected_context=context,
            expected_origin=ActionDecisionOriginV1.REPOSITORY_FIXTURE,
        )
    except PathIEligibilityError as exc:
        raise TrialReturnAuthorizationError("ACTION_NOT_ELIGIBLE") from exc


def _make_repository_fixture_port_binding(
    identity: TrialReturnIdentityV1,
    decision: ActionDecisionV1,
    context: ActionScopeContextV1,
) -> _RepositoryFixturePortBindingV1:
    return _RepositoryFixturePortBindingV1(
        capability_version=REPOSITORY_FIXTURE_PORT_CAPABILITY_VERSION,
        repository_owned=True,
        decision_origin=decision.decision_origin,
        target_kind=context.target_kind,
        scope_revision=context.scope_revision,
        scope_sha256=context.scope_sha256,
        release_id=context.release_id,
        run_id=context.run_id,
        family_id=context.family_id,
        logical_uri=identity.logical_uri,
        authorization_id=decision.authorization_id,
        approval_ref=decision.approval_ref,
        evidence_ref=decision.evidence_ref,
    )


def _require_repository_fixture_port_binding(
    fixture_port: object,
    identity: TrialReturnIdentityV1,
    decision: ActionDecisionV1,
    context: ActionScopeContextV1,
) -> None:
    if type(fixture_port) is not RepositoryFixtureTrialReturnPortV1:
        raise TrialReturnFixturePortError("FIXTURE_PORT_NOMINAL_TYPE_REQUIRED")
    expected = _make_repository_fixture_port_binding(identity, decision, context)
    if fixture_port.binding != expected:
        raise TrialReturnFixturePortError("FIXTURE_PORT_BINDING_MISMATCH")


def _require_verified_matches_port_binding(
    verified: VerifiedTrialReturnBundleV1,
    binding: _RepositoryFixturePortBindingV1,
) -> None:
    if not isinstance(verified, VerifiedTrialReturnBundleV1):
        raise TrialReturnFixturePortError("FIXTURE_PORT_VERIFIED_TYPE_REQUIRED")
    manifest = verified.bundle.manifest
    authorization_evidence_refs = verified.bundle.seal.authorization_evidence_refs
    selection = verified.selection
    if (
        authorization_evidence_refs
        != (binding.approval_ref, binding.evidence_ref)
        or selection.decision_origin is not binding.decision_origin
        or selection.target_kind is not binding.target_kind
        or selection.release_id != binding.release_id
        or selection.logical_uri != binding.logical_uri
        or manifest.release_id != binding.release_id
        or manifest.run_id != binding.run_id
        or manifest.family_id != binding.family_id
        or manifest.logical_uri != binding.logical_uri
    ):
        raise TrialReturnFixturePortError(
            "FIXTURE_PORT_VERIFIED_BINDING_MISMATCH"
        )


def _validate_and_order_observations(
    observations: Sequence[TrialReturnObservationV1],
) -> tuple[TrialReturnObservationV1, ...]:
    if isinstance(observations, (str, bytes)) or not isinstance(
        observations, Sequence
    ):
        raise TrialReturnContractError("OBSERVATIONS_TYPE_INVALID")
    if not observations:
        raise TrialReturnContractError("OBSERVATIONS_REQUIRED")
    if not all(isinstance(item, TrialReturnObservationV1) for item in observations):
        raise TrialReturnContractError("OBSERVATION_TYPE_INVALID")
    ordered = tuple(sorted(observations, key=lambda item: item.timestamp))
    for previous, current in zip(ordered, ordered[1:]):
        if current.timestamp <= previous.timestamp:
            raise TrialReturnContractError("TIMESTAMP_NOT_STRICTLY_INCREASING")
        if current.interval_start < previous.timestamp:
            raise TrialReturnContractError("OBSERVATION_INTERVAL_OVERLAP")
    return ordered


def _serialize_payload(
    observations: tuple[TrialReturnObservationV1, ...],
) -> bytes:
    table = pa.Table.from_arrays(
        [
            pa.array(
                [item.timestamp for item in observations],
                type=pa.timestamp("us", tz="UTC"),
                from_pandas=False,
                safe=True,
            ),
            pa.array(
                [item.simple_return for item in observations],
                type=pa.float64(),
                from_pandas=False,
                safe=True,
            ),
        ],
        schema=_PAYLOAD_ARROW_SCHEMA,
    )
    sink = pa.BufferOutputStream()
    pq.write_table(
        table,
        sink,
        row_group_size=len(observations),
        version="2.6",
        use_dictionary=False,
        compression="NONE",
        write_statistics=False,
        use_deprecated_int96_timestamps=False,
        coerce_timestamps="us",
        allow_truncated_timestamps=False,
        data_page_version="1.0",
        store_schema=True,
        write_page_index=False,
    )
    return sink.getvalue().to_pybytes()


def _verify_payload(payload: TrialReturnPayloadV1) -> None:
    if _sha256_prefixed(payload.payload_bytes) != payload.content_sha256:
        raise TrialReturnIntegrityError("PAYLOAD_DIGEST_MISMATCH")
    try:
        table = pq.read_table(pa.BufferReader(payload.payload_bytes))
    except (pa.ArrowException, OSError, ValueError) as exc:
        raise TrialReturnIntegrityError("PAYLOAD_PARQUET_INVALID") from exc
    if not table.schema.equals(_PAYLOAD_ARROW_SCHEMA, check_metadata=True):
        raise TrialReturnIntegrityError("PAYLOAD_SCHEMA_NOT_EXACT")
    if table.num_columns != 2 or table.column_names != [
        "timestamp",
        "simple_return",
    ]:
        raise TrialReturnIntegrityError("PAYLOAD_COLUMNS_NOT_EXACT")
    if table.num_rows != payload.row_count:
        raise TrialReturnIntegrityError("PAYLOAD_ROW_COUNT_MISMATCH")
    if any(column.null_count for column in table.columns):
        raise TrialReturnIntegrityError("PAYLOAD_NULL_FORBIDDEN")
    timestamps = tuple(table.column("timestamp").to_pylist())
    returns = tuple(table.column("simple_return").to_pylist())
    if not timestamps or timestamps[-1] != payload.observation_window[1]:
        raise TrialReturnIntegrityError("PAYLOAD_WINDOW_MISMATCH")
    if any(left >= right for left, right in zip(timestamps, timestamps[1:])):
        raise TrialReturnIntegrityError("PAYLOAD_TIMESTAMP_ORDER_INVALID")
    if any(
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(float(value))
        or float(value) < -1.0
        for value in returns
    ):
        raise TrialReturnIntegrityError("PAYLOAD_RETURN_DOMAIN_INVALID")


def _canonical_manifest_bytes(manifest: TrialReturnManifestV1) -> bytes:
    if not isinstance(manifest, TrialReturnManifestV1):
        raise TrialReturnIntegrityError("MANIFEST_TYPE_INVALID")
    return _canonical_json_bytes(
        {
            "content_sha256": manifest.content_sha256,
            "created_at": manifest.created_at,
            "family_id": manifest.family_id,
            "logical_uri": manifest.logical_uri,
            "object_kind": manifest.object_kind,
            "observation_window": manifest.observation_window,
            "producer_contract_version": manifest.producer_contract_version,
            "release_id": manifest.release_id,
            "return_basis": manifest.return_basis,
            "row_count": manifest.row_count,
            "run_id": manifest.run_id,
            "schema_version": manifest.schema_version,
            "seal_status": manifest.seal_status,
            "source_lineage_refs": manifest.source_lineage_refs,
            "trial_id": manifest.trial_id,
        }
    )


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
        raise TrialReturnIntegrityError("CANONICAL_JSON_INVALID") from exc
    return text.encode("utf-8")


def _normalize_json_value(value: object) -> object:
    if isinstance(value, datetime):
        return _format_utc(value)
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
            raise TrialReturnIntegrityError("CANONICAL_JSON_KEY_INVALID")
        return {
            unicodedata.normalize("NFC", key): _normalize_json_value(item)
            for key, item in value.items()
        }
    if value is None or type(value) in {bool, int}:
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise TrialReturnIntegrityError("CANONICAL_JSON_NUMBER_INVALID")
        return value
    raise TrialReturnIntegrityError("CANONICAL_JSON_TYPE_INVALID")


def _verified_from_verifier(
    bundle: SealedTrialReturnBundleV1,
    selection: ResearchCanonicalSelectionV1,
    original_seal_sha256: str,
) -> VerifiedTrialReturnBundleV1:
    _require_sha256("original_seal_sha256", original_seal_sha256)
    verified = object.__new__(VerifiedTrialReturnBundleV1)
    object.__setattr__(verified, "bundle", bundle)
    object.__setattr__(verified, "selection", selection)
    object.__setattr__(verified, "original_seal_sha256", original_seal_sha256)
    return verified


def _require_observation_window(
    value: object,
) -> tuple[datetime, datetime]:
    if not isinstance(value, tuple) or len(value) != 2:
        raise TrialReturnContractError("OBSERVATION_WINDOW_INVALID")
    start = _require_utc_datetime("observation_window_start", value[0])
    end = _require_utc_datetime("observation_window_end", value[1])
    if start >= end:
        raise TrialReturnContractError("OBSERVATION_WINDOW_INVALID")
    return start, end


def _require_opaque_refs(name: str, value: object) -> tuple[str, ...]:
    if not isinstance(value, tuple) or not value:
        raise TrialReturnContractError(f"{name.upper()}_REQUIRED")
    refs = tuple(value)
    if len(set(refs)) != len(refs):
        raise TrialReturnContractError(f"{name.upper()}_DUPLICATE")
    for ref in refs:
        if (
            not isinstance(ref, str)
            or not ref
            or ref.startswith("/")
            or "\\" in ref
            or ".." in ref.split("/")
            or any(marker in ref.lower() for marker in _FORBIDDEN_REF_MARKERS)
        ):
            raise TrialReturnContractError(f"{name.upper()}_INVALID")
    return refs


def _require_identifier(name: str, value: object) -> None:
    if not isinstance(value, str) or not _IDENTIFIER_RE.fullmatch(value):
        raise TrialReturnContractError(f"{name.upper()}_INVALID")
    if value.startswith("/") or ".." in value.split("/"):
        raise TrialReturnContractError(f"{name.upper()}_INVALID")


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
        raise TrialReturnContractError("FIXTURE_URI_INVALID")
    try:
        parsed = urlsplit(value)
        port = parsed.port
    except ValueError as exc:
        raise TrialReturnContractError("FIXTURE_URI_INVALID") from exc
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
        raise TrialReturnContractError("FIXTURE_URI_INVALID")
    return value


def _require_sha256(name: str, value: object) -> None:
    if not isinstance(value, str) or not _SHA256_RE.fullmatch(value):
        raise TrialReturnIntegrityError(f"{name.upper()}_INVALID")


def _require_utc_datetime(name: str, value: object) -> datetime:
    if (
        not isinstance(value, datetime)
        or value.tzinfo is None
        or value.utcoffset() is None
        or value.utcoffset().total_seconds() != 0
    ):
        raise TrialReturnContractError(f"{name.upper()}_MUST_BE_UTC")
    return value.astimezone(timezone.utc)


def _format_utc(value: datetime) -> str:
    utc_value = _require_utc_datetime("canonical_datetime", value)
    return utc_value.strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def _sha256_prefixed(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()
