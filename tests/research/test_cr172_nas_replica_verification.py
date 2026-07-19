from __future__ import annotations

import ast
import copy
from dataclasses import FrozenInstanceError, replace
from datetime import datetime, timedelta, timezone
import inspect

import pytest

import engine.research_artifact_replica as replica
import engine.trial_return_artifact as artifact
from engine.path_i_governance import (
    ActionAuthorizationRecordV1,
    ActionAuthorizationRequestV1,
    ActionDecisionOriginV1,
    ActionPrerequisiteEvidenceV1,
    ActionPrerequisiteProvenanceV1,
    ActionReasonCodeV1,
    ActionScopeContextV1,
    ActionTargetKindV1,
    GOVERNANCE_SCHEMA_VERSION,
    PathIActionKind,
    evaluate_action_decision,
)


NOW = datetime(2026, 7, 18, 6, 0, tzinfo=timezone.utc)
HASH_A = "sha256:" + "a" * 64
HASH_B = "sha256:" + "b" * 64
FIXTURE_ROOT = "fixture://repository/cr172"
FIXTURE_URI = f"{FIXTURE_ROOT}/family-fixture-001/run-fixture-001/trial-001"


class InMemoryReplicaStoragePort(replica.ReplicaStoragePortV1):
    """只保存显式 fixture value；不访问文件系统或网络。"""

    __slots__ = (
        "stage_calls",
        "persist_calls",
        "cas_calls",
        "read_calls",
        "staging_states",
        "inject_stage_failure",
        "inject_persist_failure",
        "inject_cas_failure",
        "concurrent_selection_on_cas",
        "stage_transform",
        "_current",
        "_immutable",
    )

    def __init__(
        self,
        mapping: replica.ReplicaDeploymentMappingV1,
        *,
        inject_stage_failure: bool = False,
        inject_persist_failure: bool = False,
        inject_cas_failure: bool = False,
        stage_transform=None,
    ) -> None:
        super().__init__(mapping)
        self.stage_calls = 0
        self.persist_calls = 0
        self.cas_calls = 0
        self.read_calls = 0
        self.staging_states: list[str] = []
        self.inject_stage_failure = inject_stage_failure
        self.inject_persist_failure = inject_persist_failure
        self.inject_cas_failure = inject_cas_failure
        self.concurrent_selection_on_cas: (
            replica.DistributionSelectionV1 | None
        ) = None
        self.stage_transform = stage_transform
        self._current: replica.DistributionSelectionV1 | None = None
        self._immutable: dict[
            str,
            tuple[
                artifact.SealedTrialReturnBundleV1,
                artifact.ResearchCanonicalSelectionV1,
                replica.ReplicaVerificationReceiptV1,
            ],
        ] = {}

    @property
    def current_selection(self) -> replica.DistributionSelectionV1 | None:
        return self._current

    def stage_bundle(
        self,
        preflight: replica.ReplicaPreflightV1,
        staging_token: replica.ReplicaStagingTokenV1,
    ) -> artifact.SealedTrialReturnBundleV1:
        self.stage_calls += 1
        self.staging_states.append(staging_token.state)
        if self.inject_stage_failure:
            raise RuntimeError("controlled staging interruption")
        staged = copy.deepcopy(preflight.verified_source.bundle)
        if self.stage_transform is not None:
            staged = self.stage_transform(staged)
        return staged

    def persist_immutable_replica(
        self,
        candidate: replica.VerifiedReplicaCandidateV1,
        receipt: replica.ReplicaVerificationReceiptV1,
    ) -> None:
        self.persist_calls += 1
        if self.inject_persist_failure:
            raise RuntimeError("controlled receipt persistence failure")
        value = (
            candidate.staged_verified.bundle,
            candidate.staged_verified.selection,
            receipt,
        )
        existing = self._immutable.get(candidate.replica_version_ref)
        if existing is not None and existing != value:
            raise RuntimeError("immutable version conflict")
        self._immutable[candidate.replica_version_ref] = value

    def compare_and_swap_selection(
        self,
        expected_previous: replica.DistributionSelectionV1 | None,
        new_selection: replica.DistributionSelectionV1,
    ) -> bool:
        self.cas_calls += 1
        if self.concurrent_selection_on_cas is not None:
            self._current = self.concurrent_selection_on_cas
            self.concurrent_selection_on_cas = None
        if self.inject_cas_failure or self._current != expected_previous:
            return False
        self._current = new_selection
        return True

    def _read_immutable_replica(
        self,
        replica_version_ref: str,
    ) -> tuple[
        artifact.SealedTrialReturnBundleV1,
        artifact.ResearchCanonicalSelectionV1,
        replica.ReplicaVerificationReceiptV1,
    ]:
        self.read_calls += 1
        return self._immutable[replica_version_ref]


class StructuralPort:
    def __init__(self) -> None:
        self.stage_calls = 0

    def stage_bundle(self, *_args: object) -> object:
        self.stage_calls += 1
        raise AssertionError("structural port 不得被调用")


def make_context(
    *,
    target_kind: ActionTargetKindV1 = ActionTargetKindV1.REPOSITORY_FIXTURE,
    release_id: str = "release-fixture-001",
) -> ActionScopeContextV1:
    return ActionScopeContextV1(
        schema_version=GOVERNANCE_SCHEMA_VERSION,
        scope_revision="scope-v1",
        scope_sha256=HASH_A,
        release_id=release_id,
        run_id="run-fixture-001",
        family_id="family-fixture-001",
        target_kind=target_kind,
    )


def make_generation_decision(
    context: ActionScopeContextV1 | None = None,
):
    context = context or make_context()
    record = ActionAuthorizationRecordV1(
        authorization_id="auth-trial-return-generation",
        action_kind=PathIActionKind.TRIAL_RETURN_GENERATION,
        owner="repository-fixture-owner",
        scope_revision=context.scope_revision,
        scope_sha256=context.scope_sha256,
        allowed_logical_paths=(FIXTURE_ROOT,),
        denied_logical_paths=(),
        valid_from=NOW - timedelta(hours=1),
        expires_at=NOW + timedelta(hours=12),
        revoked_at=None,
        approval_ref="approval:trial-return-generation",
        evidence_ref="fixture:trial-return-generation",
    )
    predecessor = ActionPrerequisiteEvidenceV1(
        predecessor_action_kind=(
            PathIActionKind.MULTI_TRIAL_RUNTIME_AND_WORKSPACE_WRITE
        ),
        authorization_id="auth-runtime-fixture",
        authorized=True,
        eligible_to_execute=True,
        context=context,
        provenance_kind=ActionPrerequisiteProvenanceV1.ELIGIBILITY_DECISION,
        logical_uri=f"{FIXTURE_ROOT}/runtime-predecessor",
        content_sha256="",
        manifest_sha256="",
        evidence_ref="fixture:runtime-predecessor",
    )
    return evaluate_action_decision(
        ActionAuthorizationRequestV1(
            action_kind=PathIActionKind.TRIAL_RETURN_GENERATION,
            logical_path=FIXTURE_URI,
            context=context,
        ),
        record,
        (predecessor,),
        decision_origin=ActionDecisionOriginV1.REPOSITORY_FIXTURE,
        evaluated_at=NOW,
    )


def make_source_verified() -> artifact.VerifiedTrialReturnBundleV1:
    context = make_context()
    decision = make_generation_decision(context)
    identity = artifact.TrialReturnIdentityV1(
        family_id=context.family_id,
        run_id=context.run_id,
        trial_id="trial-001",
        release_id=context.release_id,
        logical_uri=FIXTURE_URI,
    )
    definition = artifact.ReturnDefinitionV1(
        object_kind=(
            artifact.TrialReturnSourceKindV1.TRIAL_PORTFOLIO_RETURN_SERIES
        ),
        schema_version=artifact.RETURN_DEFINITION_SCHEMA_VERSION,
        return_basis=artifact.RETURN_BASIS_V1,
        endpoint_semantics=artifact.ENDPOINT_SEMANTICS_V1,
        non_overlap_required=True,
        alignment_policy=artifact.ALIGNMENT_POLICY_V1,
    )
    observations = (
        artifact.TrialReturnObservationV1(
            interval_start=NOW,
            timestamp=NOW + timedelta(days=1),
            simple_return=0.02,
        ),
        artifact.TrialReturnObservationV1(
            interval_start=NOW + timedelta(days=1),
            timestamp=NOW + timedelta(days=2),
            simple_return=-0.01,
        ),
    )
    port = artifact.RepositoryFixtureTrialReturnPortV1(
        identity,
        decision,
        context,
    )
    return artifact.publish_repository_fixture_trial_return_artifact(
        identity,
        observations,
        definition,
        decision,
        context,
        port,
        created_at=NOW + timedelta(hours=1),
        sealed_at=NOW + timedelta(hours=2),
        source_lineage_refs=("fixture:explicit-period-observations",),
    )


def make_sync_decision(
    source: artifact.VerifiedTrialReturnBundleV1,
    *,
    context: ActionScopeContextV1 | None = None,
    evaluated_at: datetime = NOW + timedelta(hours=3),
):
    context = context or make_context()
    record = ActionAuthorizationRecordV1(
        authorization_id="auth-nas-replica-sync",
        action_kind=PathIActionKind.NAS_REPLICA_SYNC,
        owner="repository-fixture-owner",
        scope_revision=context.scope_revision,
        scope_sha256=context.scope_sha256,
        allowed_logical_paths=(FIXTURE_ROOT,),
        denied_logical_paths=(),
        valid_from=NOW - timedelta(hours=1),
        expires_at=NOW + timedelta(hours=12),
        revoked_at=None,
        approval_ref="approval:nas-replica-sync",
        evidence_ref="fixture:nas-replica-sync",
    )
    predecessor = ActionPrerequisiteEvidenceV1(
        predecessor_action_kind=PathIActionKind.TRIAL_RETURN_GENERATION,
        authorization_id="auth-trial-return-generation",
        authorized=True,
        eligible_to_execute=True,
        context=context,
        provenance_kind=ActionPrerequisiteProvenanceV1.SEALED_TRIAL_RETURN,
        logical_uri=source.selection.logical_uri,
        content_sha256=source.bundle.payload.content_sha256,
        manifest_sha256=source.bundle.manifest_sha256,
        evidence_ref="fixture:sealed-trial-return",
    )
    return evaluate_action_decision(
        ActionAuthorizationRequestV1(
            action_kind=PathIActionKind.NAS_REPLICA_SYNC,
            logical_path=source.selection.logical_uri,
            context=context,
        ),
        record,
        (predecessor,),
        decision_origin=ActionDecisionOriginV1.REPOSITORY_FIXTURE,
        evaluated_at=evaluated_at,
    )


def make_mapping(*, suffix: str = "a") -> replica.ReplicaDeploymentMappingV1:
    return replica.ReplicaDeploymentMappingV1(
        mapping_version=replica.REPLICA_MAPPING_VERSION,
        repository_owned=True,
        decision_origin=ActionDecisionOriginV1.REPOSITORY_FIXTURE,
        target_kind=ActionTargetKindV1.REPOSITORY_FIXTURE,
        logical_uri=FIXTURE_URI,
        source_handle=f"source/{suffix}",
        staging_handle=f"staging/{suffix}",
        version_handle=f"versions/{suffix}",
        pointer_handle=f"pointers/{suffix}",
    )


def make_request(
    source: artifact.VerifiedTrialReturnBundleV1,
    *,
    request_id: str = "request-replica-001",
) -> replica.ReplicaSyncRequestV1:
    return replica.ReplicaSyncRequestV1.from_source_selection(
        request_id=request_id,
        source_selection=source.selection,
    )


def publish(
    source: artifact.VerifiedTrialReturnBundleV1,
    port: InMemoryReplicaStoragePort,
    *,
    request: replica.ReplicaSyncRequestV1 | None = None,
    preflight_decision=None,
    commit_decision=None,
    preflight_context: ActionScopeContextV1 | None = None,
    commit_context: ActionScopeContextV1 | None = None,
) -> replica.ReplicaPublishResultV1:
    context = preflight_context or make_context()
    return replica.publish_repository_fixture_replica(
        request or make_request(source),
        source.bundle,
        source.selection,
        preflight_decision or make_sync_decision(source, context=context),
        context,
        commit_decision or make_sync_decision(
            source,
            context=commit_context or context,
            evaluated_at=NOW + timedelta(hours=4),
        ),
        commit_context or context,
        port.mapping,
        port,
    )


def make_previous_selection(
    source: artifact.VerifiedTrialReturnBundleV1,
    port: InMemoryReplicaStoragePort,
) -> replica.DistributionSelectionV1:
    result = publish(
        source,
        port,
        request=make_request(source, request_id="request-previous"),
    )
    assert result.status is replica.ReplicaPublishStatusV1.VERIFIED
    assert result.selection is not None
    return result.selection


def test_t_s03_p01_original_seal_five_of_five_cas_and_selected_read() -> None:
    source = make_source_verified()
    original_research_selection = copy.deepcopy(source.selection)
    port = InMemoryReplicaStoragePort(make_mapping())

    result = publish(source, port)

    assert result.status is replica.ReplicaPublishStatusV1.VERIFIED
    assert result.reason is replica.ReplicaBlockReasonV1.NONE
    assert result.receipt is not None
    assert result.selection is not None
    assert result.receipt.verification_vector.complete is True
    assert result.receipt.original_seal_sha256 == source.original_seal_sha256
    assert result.receipt.original_seal_sha256 == source.selection.original_seal_sha256
    assert port.stage_calls == port.persist_calls == port.cas_calls == 1
    assert port.staging_states == [replica.NON_DISTRIBUTABLE_STATE]
    selected = port.read_selected_replica(result.selection)
    assert selected == (source.bundle, source.selection, result.receipt)
    assert source.selection == original_research_selection


def test_t_s03_p02_receipt_is_deterministic_and_mapping_is_outside_hash() -> None:
    source = make_source_verified()
    results = []
    mappings = tuple(make_mapping(suffix=suffix) for suffix in ("one", "two", "three"))
    for mapping in mappings:
        result = publish(source, InMemoryReplicaStoragePort(mapping))
        assert result.receipt is not None
        results.append(result)

    assert len({item.receipt.receipt_sha256 for item in results if item.receipt}) == 1
    bodies = tuple(
        replica.canonical_replica_receipt_bytes(item.receipt)
        for item in results
        if item.receipt is not None
    )
    assert len(set(bodies)) == 1
    assert all(
        handle.encode() not in bodies[0]
        for mapping in mappings
        for handle in (
            mapping.source_handle,
            mapping.staging_handle,
            mapping.version_handle,
            mapping.pointer_handle,
        )
    )


@pytest.mark.parametrize(
    "decision_mutator",
    [
        lambda decision: replace(
            decision,
            authorized=False,
            eligible_to_execute=False,
            reason_codes=(ActionReasonCodeV1.REVOKED,),
        ),
        lambda decision: replace(
            decision,
            decision_origin=ActionDecisionOriginV1.APPROVED_LEDGER,
            authorized=False,
            eligible_to_execute=False,
            reason_codes=(
                ActionReasonCodeV1.APPROVED_LEDGER_ADAPTER_UNAVAILABLE,
            ),
        ),
        lambda decision: replace(
            decision,
            target_kind=ActionTargetKindV1.REAL_OPERATION,
            authorized=False,
            eligible_to_execute=False,
            reason_codes=(ActionReasonCodeV1.ORIGIN_TARGET_MISMATCH,),
        ),
        lambda decision: replace(
            decision,
            action_kind=PathIActionKind.EXECUTION_PULL_VERIFY_MATERIALIZE,
        ),
    ],
    ids=["revoked", "wrong-origin", "real-target", "wrong-kind"],
)
def test_t_s03_a01_wrong_decision_is_rejected_before_any_port_write(
    decision_mutator,
) -> None:
    source = make_source_verified()
    port = InMemoryReplicaStoragePort(make_mapping())
    decision = decision_mutator(make_sync_decision(source))

    result = publish(source, port, preflight_decision=decision)

    assert result.status is replica.ReplicaPublishStatusV1.BLOCKED
    assert port.stage_calls == port.persist_calls == port.cas_calls == 0
    assert port.current_selection is None


@pytest.mark.parametrize(
    ("request_mutator", "reason"),
    [
        (
            lambda value: replace(value, expected_release_id="release-other"),
            replica.ReplicaBlockReasonV1.RELEASE_MISMATCH,
        ),
        (
            lambda value: replace(
                value,
                expected_logical_uri=f"{FIXTURE_ROOT}/other/source",
            ),
            replica.ReplicaBlockReasonV1.LOGICAL_URI_MISMATCH,
        ),
        (
            lambda value: replace(value, expected_content_sha256=HASH_B),
            replica.ReplicaBlockReasonV1.CONTENT_MISMATCH,
        ),
        (
            lambda value: replace(value, expected_manifest_sha256=HASH_B),
            replica.ReplicaBlockReasonV1.MANIFEST_MISMATCH,
        ),
        (
            lambda value: replace(
                value,
                expected_source_selection_sha256=HASH_B,
            ),
            replica.ReplicaBlockReasonV1.STALE_SOURCE_SELECTION,
        ),
    ],
    ids=["release", "logical-uri", "content", "manifest", "freshness"],
)
def test_t_s03_n02_expectation_mismatch_never_stages_or_advances(
    request_mutator,
    reason: replica.ReplicaBlockReasonV1,
) -> None:
    source = make_source_verified()
    port = InMemoryReplicaStoragePort(make_mapping())
    request = request_mutator(make_request(source))

    result = publish(source, port, request=request)

    assert result.reason is reason
    assert port.stage_calls == port.persist_calls == port.cas_calls == 0
    assert port.current_selection is None


def test_t_s03_n01_unversioned_source_is_blocked_before_staging() -> None:
    source = make_source_verified()
    object.__setattr__(source.bundle.seal, "seal_version", "artifact-seal")
    port = InMemoryReplicaStoragePort(make_mapping())

    result = publish(source, port)

    assert result.reason is replica.ReplicaBlockReasonV1.SOURCE_UNVERSIONED
    assert port.stage_calls == port.persist_calls == port.cas_calls == 0


def test_t_s03_f01_copy_interruption_is_non_distributable_and_preserves_previous(
) -> None:
    source = make_source_verified()
    port = InMemoryReplicaStoragePort(make_mapping())
    previous = make_previous_selection(source, port)
    port.inject_stage_failure = True

    result = publish(
        source,
        port,
        request=make_request(source, request_id="request-interrupted"),
    )

    assert result.reason is replica.ReplicaBlockReasonV1.STAGING_INTERRUPTED
    assert port.current_selection == previous
    assert port.persist_calls == port.cas_calls == 1


def test_t_s03_f02_staged_content_tamper_never_creates_receipt_or_pointer() -> None:
    source = make_source_verified()

    def tamper(bundle: artifact.SealedTrialReturnBundleV1):
        tampered_payload = replace(
            bundle.payload,
            payload_bytes=bundle.payload.payload_bytes[:-16],
        )
        return replace(bundle, payload=tampered_payload)

    port = InMemoryReplicaStoragePort(make_mapping(), stage_transform=tamper)

    result = publish(source, port)

    assert result.reason is replica.ReplicaBlockReasonV1.CONTENT_MISMATCH
    assert result.receipt is result.selection is None
    assert port.stage_calls == 1
    assert port.persist_calls == port.cas_calls == 0


def test_t_s03_a02_commit_revoke_preserves_previous_selection() -> None:
    source = make_source_verified()
    port = InMemoryReplicaStoragePort(make_mapping())
    previous = make_previous_selection(source, port)
    revoked = replace(
        make_sync_decision(source),
        authorized=False,
        eligible_to_execute=False,
        reason_codes=(ActionReasonCodeV1.REVOKED,),
    )

    result = publish(
        source,
        port,
        request=make_request(source, request_id="request-revoked"),
        commit_decision=revoked,
    )

    assert result.reason is replica.ReplicaBlockReasonV1.COMMIT_AUTHORIZATION_INVALID
    assert port.current_selection == previous
    assert port.persist_calls == port.cas_calls == 1


@pytest.mark.parametrize(
    ("case", "expected_reason"),
    [
        ("reused", replica.ReplicaBlockReasonV1.COMMIT_DECISION_NOT_FRESH),
        ("equal-time", replica.ReplicaBlockReasonV1.COMMIT_DECISION_NOT_FRESH),
        ("older", replica.ReplicaBlockReasonV1.COMMIT_DECISION_NOT_FRESH),
        ("expired", replica.ReplicaBlockReasonV1.COMMIT_AUTHORIZATION_INVALID),
        ("revoked", replica.ReplicaBlockReasonV1.COMMIT_AUTHORIZATION_INVALID),
    ],
)
def test_t_s03_a03_commit_requires_strictly_newer_re_evaluation_before_staging(
    case: str,
    expected_reason: replica.ReplicaBlockReasonV1,
) -> None:
    source = make_source_verified()
    port = InMemoryReplicaStoragePort(make_mapping())
    preflight = make_sync_decision(
        source,
        evaluated_at=NOW + timedelta(hours=3),
    )
    if case == "reused":
        commit = preflight
    elif case == "equal-time":
        commit = replace(preflight)
    elif case == "older":
        commit = replace(
            preflight,
            evaluated_at=NOW + timedelta(hours=2),
        )
    else:
        reason = (
            ActionReasonCodeV1.EXPIRED
            if case == "expired"
            else ActionReasonCodeV1.REVOKED
        )
        commit = replace(
            preflight,
            authorized=False,
            eligible_to_execute=False,
            reason_codes=(reason,),
            evaluated_at=NOW + timedelta(hours=4),
        )

    result = publish(
        source,
        port,
        preflight_decision=preflight,
        commit_decision=commit,
    )

    assert result.reason is expected_reason
    assert result.receipt is result.selection is None
    assert port.stage_calls == port.persist_calls == port.cas_calls == 0
    assert port.current_selection is None


@pytest.mark.parametrize(
    ("failure", "reason"),
    [
        ("persist", replica.ReplicaBlockReasonV1.IMMUTABLE_PERSIST_FAILED),
        ("cas", replica.ReplicaBlockReasonV1.POINTER_CONFLICT),
    ],
)
def test_t_s03_f03_persist_or_cas_failure_never_overwrites_previous(
    failure: str,
    reason: replica.ReplicaBlockReasonV1,
) -> None:
    source = make_source_verified()
    port = InMemoryReplicaStoragePort(make_mapping())
    previous = make_previous_selection(source, port)
    setattr(port, f"inject_{failure}_failure", True)

    result = publish(
        source,
        port,
        request=make_request(source, request_id=f"request-{failure}-failure"),
    )

    assert result.reason is reason
    assert port.current_selection == previous
    assert result.receipt is result.selection is None


def test_t_s03_f04_concurrent_current_cas_conflict_preserves_other_writer() -> None:
    source = make_source_verified()
    port = InMemoryReplicaStoragePort(make_mapping())
    previous = make_previous_selection(source, port)
    concurrent = replace(
        previous,
        selection_revision=previous.selection_revision + 1,
    )
    port.concurrent_selection_on_cas = concurrent
    port.cas_calls = 0
    port.persist_calls = 0

    result = publish(
        source,
        port,
        request=make_request(source, request_id="request-concurrent-current"),
    )

    assert result.reason is replica.ReplicaBlockReasonV1.POINTER_CONFLICT
    assert result.receipt is result.selection is None
    assert result.previous_selection == concurrent
    assert port.current_selection == concurrent
    assert port.persist_calls == port.cas_calls == 1


def test_t_s03_n03_selected_read_rejects_old_fake_and_receipt_drift() -> None:
    source = make_source_verified()
    port = InMemoryReplicaStoragePort(make_mapping())
    first = publish(
        source,
        port,
        request=make_request(source, request_id="request-first"),
    )
    second = publish(
        source,
        port,
        request=make_request(source, request_id="request-second"),
    )
    assert first.selection is not None and second.selection is not None

    with pytest.raises(
        replica.ReplicaStoragePortError,
        match="SELECTED_REPLICA_MISMATCH",
    ):
        port.read_selected_replica(first.selection)
    fake = replace(second.selection, selection_revision=99)
    with pytest.raises(replica.ReplicaStoragePortError):
        port.read_selected_replica(fake)

    selected_tuple = port._immutable[second.selection.replica_version_ref]
    object.__setattr__(selected_tuple[2], "logical_uri", f"{FIXTURE_ROOT}/drift")
    with pytest.raises(replica.ReplicaStoragePortError):
        port.read_selected_replica(second.selection)


def test_t_s03_b02_path_traversal_absolute_override_and_structural_port_denied(
    tmp_path,
) -> None:
    with pytest.raises(replica.ReplicaContractError):
        replace(make_mapping(), staging_handle="../escape")
    with pytest.raises(replica.ReplicaContractError):
        replace(make_mapping(), version_handle=str(tmp_path / "outside"))
    with pytest.raises(replica.ReplicaContractError):
        replace(
            make_mapping(),
            target_kind=ActionTargetKindV1.REAL_OPERATION,
        )

    source = make_source_verified()
    structural = StructuralPort()
    preflight = replica.validate_replica_preflight(
        make_request(source),
        source.bundle,
        source.selection,
        make_sync_decision(source),
        make_context(),
    )
    assert isinstance(preflight, replica.ReplicaPreflightV1)
    result = replica.stage_and_verify_replica(
        preflight,
        make_mapping(),
        structural,  # type: ignore[arg-type]
    )
    assert isinstance(result, replica.ReplicaPublishResultV1)
    assert result.reason is replica.ReplicaBlockReasonV1.PORT_BINDING_INVALID
    assert structural.stage_calls == 0


def test_t_s03_b01_receipt_is_frozen_original_seal_correlation_only() -> None:
    source = make_source_verified()
    result = publish(source, InMemoryReplicaStoragePort(make_mapping()))
    assert result.receipt is not None
    receipt = result.receipt
    assert receipt.authority == replica.REPLICA_AUTHORITY
    assert receipt.original_seal_sha256 == source.original_seal_sha256
    assert receipt.decision_origin is source.selection.decision_origin
    assert receipt.target_kind is source.selection.target_kind
    with pytest.raises(FrozenInstanceError):
        receipt.release_id = "release-other"  # type: ignore[misc]


def test_t_s03_z01_static_zero_operation_and_single_verifier_truth() -> None:
    source = inspect.getsource(replica)
    tree = ast.parse(source)
    forbidden_import_roots = {
        "boto3",
        "os",
        "paramiko",
        "pathlib",
        "requests",
        "shutil",
        "socket",
        "subprocess",
    }
    imported_roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".", 1)[0])

    assert imported_roots.isdisjoint(forbidden_import_roots)
    assert "canonical_artifact_seal_bytes" not in source
    assert "canonical_artifact_seal_sha256" not in source
    assert source.count("verify_sealed_trial_return_bundle(") == 2
    assert "ArtifactSealV1" not in source
    assert "research_artifact_materialization" not in source
    assert "mature_multifactor_research" not in source
    assert "experiment_family_lineage" not in source
    assert "read_bytes(" not in source
    assert "getenv(" not in source
    assert "environ" not in source
    assert "rsync" not in source.lower()
    assert not any("verifier" in name for name in replica.__all__)
    assert not any("latest" in name for name in replica.__all__)
