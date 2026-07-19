from __future__ import annotations

import ast
import copy
from dataclasses import dataclass, replace
from datetime import datetime, timedelta, timezone
import inspect

import pytest

import engine.research_artifact_materialization as materialization
import engine.research_artifact_replica as replica
import engine.trial_return_artifact as artifact
from engine.path_i_governance import (
    ActionAuthorizationRecordV1,
    ActionAuthorizationRequestV1,
    ActionDecisionOriginV1,
    ActionPrerequisiteEvidenceV1,
    ActionPrerequisiteProvenanceV1,
    ActionScopeContextV1,
    ActionTargetKindV1,
    GOVERNANCE_SCHEMA_VERSION,
    PathIActionKind,
    evaluate_action_decision,
)


NOW = datetime(2026, 7, 18, 6, 0, tzinfo=timezone.utc)
HASH_A = "sha256:" + "a" * 64
HASH_B = "sha256:" + "b" * 64
HASH_C = "sha256:" + "c" * 64
FIXTURE_ROOT = "fixture://repository/cr172"
FIXTURE_URI = f"{FIXTURE_ROOT}/family-fixture-001/run-fixture-001/trial-001"


class InMemoryReplicaStoragePort(replica.ReplicaStoragePortV1):
    """S03 current selection 的纯内存 fixture；无文件或网络操作。"""

    __slots__ = (
        "stage_calls",
        "persist_calls",
        "cas_calls",
        "read_calls",
        "_current",
        "_immutable",
    )

    def __init__(self, mapping: replica.ReplicaDeploymentMappingV1) -> None:
        super().__init__(mapping)
        self.stage_calls = 0
        self.persist_calls = 0
        self.cas_calls = 0
        self.read_calls = 0
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
        return copy.deepcopy(preflight.verified_source.bundle)

    def persist_immutable_replica(
        self,
        candidate: replica.VerifiedReplicaCandidateV1,
        receipt: replica.ReplicaVerificationReceiptV1,
    ) -> None:
        self.persist_calls += 1
        value = (
            candidate.staged_verified.bundle,
            candidate.staged_verified.selection,
            receipt,
        )
        existing = self._immutable.get(candidate.replica_version_ref)
        if existing is not None and existing != value:
            raise RuntimeError("immutable replica conflict")
        self._immutable[candidate.replica_version_ref] = value

    def compare_and_swap_selection(
        self,
        expected_previous: replica.DistributionSelectionV1 | None,
        new_selection: replica.DistributionSelectionV1,
    ) -> bool:
        self.cas_calls += 1
        if self._current != expected_previous:
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


class InMemoryMaterializationStoragePort(
    materialization.MaterializationStoragePortV1
):
    """只保存已验证 bytes/receipt 与 local selection 的纯内存 fixture。"""

    __slots__ = (
        "persist_calls",
        "receipt_read_calls",
        "cas_calls",
        "inject_pull_interruption",
        "inject_receipt_persist_failure",
        "inject_cas_failure",
        "_current",
        "_immutable",
        "_receipts",
    )

    def __init__(
        self,
        mapping: materialization.ExecutionDeploymentMappingV1,
        replica_port: replica.ReplicaStoragePortV1,
    ) -> None:
        super().__init__(mapping, replica_port)
        self.persist_calls = 0
        self.receipt_read_calls = 0
        self.cas_calls = 0
        self.inject_pull_interruption = False
        self.inject_receipt_persist_failure = False
        self.inject_cas_failure = False
        self._current: (
            materialization.ExecutionCacheSelectionV1 | None
        ) = None
        self._immutable: dict[
            str,
            tuple[bytes, materialization.MaterializationReceiptV1],
        ] = {}
        self._receipts: dict[
            str,
            materialization.MaterializationReceiptV1,
        ] = {}

    @property
    def current_selection(
        self,
    ) -> materialization.ExecutionCacheSelectionV1 | None:
        return self._current

    def _before_selected_read(self) -> None:
        if self.inject_pull_interruption:
            raise RuntimeError("controlled pull interruption")

    def persist_immutable_cache(
        self,
        candidate: materialization.VerifiedCacheCandidateV1,
        receipt: materialization.MaterializationReceiptV1,
    ) -> None:
        self.persist_calls += 1
        if self.inject_receipt_persist_failure:
            raise materialization.MaterializationStoragePortError(
                materialization.MaterializationBlockReasonV1.RECEIPT_PERSISTENCE_FAILED
            )
        payload_bytes = candidate.staged_verified.bundle.payload.payload_bytes
        existing = self._immutable.get(candidate.cache_version_ref)
        if existing is not None:
            if existing[0] != payload_bytes:
                raise materialization.MaterializationStoragePortError(
                    materialization.MaterializationBlockReasonV1.IMMUTABLE_CACHE_CONFLICT
                )
        else:
            self._immutable[candidate.cache_version_ref] = (
                payload_bytes,
                receipt,
            )
        existing_receipt = self._receipts.get(receipt.receipt_sha256)
        if existing_receipt is not None and existing_receipt != receipt:
            raise materialization.MaterializationStoragePortError(
                materialization.MaterializationBlockReasonV1.IMMUTABLE_CACHE_CONFLICT
            )
        self._receipts[receipt.receipt_sha256] = receipt

    def read_materialization_receipt(
        self,
        receipt_sha256: str,
    ) -> materialization.MaterializationReceiptV1 | None:
        self.receipt_read_calls += 1
        return self._receipts.get(receipt_sha256)

    def compare_and_swap_cache_selection(
        self,
        expected_previous: (
            materialization.ExecutionCacheSelectionV1 | None
        ),
        new_selection: materialization.ExecutionCacheSelectionV1,
    ) -> bool:
        self.cas_calls += 1
        if self.inject_cas_failure or self._current != expected_previous:
            return False
        self._current = new_selection
        return True


@dataclass(frozen=True, slots=True)
class MaterializationFixture:
    context: ActionScopeContextV1
    source: artifact.VerifiedTrialReturnBundleV1
    replica_receipt: replica.ReplicaVerificationReceiptV1
    distribution_selection: replica.DistributionSelectionV1
    replica_port: InMemoryReplicaStoragePort
    request: materialization.ExecutionMaterializationRequestV1
    preflight_decision: object
    commit_decision: object
    mapping: materialization.ExecutionDeploymentMappingV1
    storage_port: InMemoryMaterializationStoragePort


def make_context(
    *,
    target_kind: ActionTargetKindV1 = ActionTargetKindV1.REPOSITORY_FIXTURE,
    scope_sha256: str = HASH_A,
) -> ActionScopeContextV1:
    return ActionScopeContextV1(
        schema_version=GOVERNANCE_SCHEMA_VERSION,
        scope_revision="scope-v1",
        scope_sha256=scope_sha256,
        release_id="release-fixture-001",
        run_id="run-fixture-001",
        family_id="family-fixture-001",
        target_kind=target_kind,
    )


def make_generation_decision(context: ActionScopeContextV1):
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


def make_source_verified(
    context: ActionScopeContextV1,
) -> artifact.VerifiedTrialReturnBundleV1:
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
    fixture_port = artifact.RepositoryFixtureTrialReturnPortV1(
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
        fixture_port,
        created_at=NOW + timedelta(hours=1),
        sealed_at=NOW + timedelta(hours=2),
        source_lineage_refs=("fixture:explicit-period-observations",),
    )


def make_sync_decision(
    source: artifact.VerifiedTrialReturnBundleV1,
    context: ActionScopeContextV1,
    *,
    evaluated_at: datetime = NOW + timedelta(hours=3),
):
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


def make_replica_mapping() -> replica.ReplicaDeploymentMappingV1:
    return replica.ReplicaDeploymentMappingV1(
        mapping_version=replica.REPLICA_MAPPING_VERSION,
        repository_owned=True,
        decision_origin=ActionDecisionOriginV1.REPOSITORY_FIXTURE,
        target_kind=ActionTargetKindV1.REPOSITORY_FIXTURE,
        logical_uri=FIXTURE_URI,
        source_handle="source/fixture",
        staging_handle="staging/fixture",
        version_handle="versions/fixture",
        pointer_handle="pointers/fixture",
    )


def publish_replica(
    source: artifact.VerifiedTrialReturnBundleV1,
    context: ActionScopeContextV1,
    storage_port: InMemoryReplicaStoragePort,
) -> replica.ReplicaPublishResultV1:
    request = replica.ReplicaSyncRequestV1.from_source_selection(
        request_id="request-replica-001",
        source_selection=source.selection,
    )
    return replica.publish_repository_fixture_replica(
        request,
        source.bundle,
        source.selection,
        make_sync_decision(source, context),
        context,
        make_sync_decision(
            source,
            context,
            evaluated_at=NOW + timedelta(hours=4),
        ),
        context,
        storage_port.mapping,
        storage_port,
    )


def make_pull_decision(
    receipt: replica.ReplicaVerificationReceiptV1,
    context: ActionScopeContextV1,
    *,
    evaluated_at: datetime,
    revoked: bool = False,
    include_record: bool = True,
):
    record = None
    if include_record:
        record = ActionAuthorizationRecordV1(
            authorization_id="auth-execution-materialize",
            action_kind=PathIActionKind.EXECUTION_PULL_VERIFY_MATERIALIZE,
            owner="repository-fixture-owner",
            scope_revision=context.scope_revision,
            scope_sha256=context.scope_sha256,
            allowed_logical_paths=(FIXTURE_ROOT,),
            denied_logical_paths=(),
            valid_from=NOW - timedelta(hours=1),
            expires_at=NOW + timedelta(hours=12),
            revoked_at=(NOW + timedelta(hours=4) if revoked else None),
            approval_ref="approval:execution-materialize",
            evidence_ref="fixture:execution-materialize",
        )
    predecessor = ActionPrerequisiteEvidenceV1(
        predecessor_action_kind=PathIActionKind.NAS_REPLICA_SYNC,
        authorization_id="auth-nas-replica-sync",
        authorized=True,
        eligible_to_execute=True,
        context=context,
        provenance_kind=(
            ActionPrerequisiteProvenanceV1.VERIFIED_REPLICA_RECEIPT
        ),
        logical_uri=receipt.logical_uri,
        content_sha256=receipt.content_sha256,
        manifest_sha256=receipt.manifest_sha256,
        evidence_ref="fixture:verified-replica-receipt",
    )
    return evaluate_action_decision(
        ActionAuthorizationRequestV1(
            action_kind=(
                PathIActionKind.EXECUTION_PULL_VERIFY_MATERIALIZE
            ),
            logical_path=receipt.logical_uri,
            context=context,
        ),
        record,
        (predecessor,),
        decision_origin=ActionDecisionOriginV1.REPOSITORY_FIXTURE,
        evaluated_at=evaluated_at,
    )


def make_materialization_mapping(
    *, suffix: str = "one"
) -> materialization.ExecutionDeploymentMappingV1:
    return materialization.ExecutionDeploymentMappingV1(
        mapping_version=materialization.MATERIALIZATION_MAPPING_VERSION,
        repository_owned=True,
        decision_origin=ActionDecisionOriginV1.REPOSITORY_FIXTURE,
        target_kind=ActionTargetKindV1.REPOSITORY_FIXTURE,
        logical_uri=FIXTURE_URI,
        replica_handle=f"replica/{suffix}",
        staging_handle=f"staging/{suffix}",
        cache_handle=f"cache/{suffix}",
        pointer_handle=f"pointer/{suffix}",
    )


def make_fixture(
    *, mapping_suffix: str = "one"
) -> MaterializationFixture:
    context = make_context()
    source = make_source_verified(context)
    replica_port = InMemoryReplicaStoragePort(make_replica_mapping())
    replica_result = publish_replica(source, context, replica_port)
    assert replica_result.receipt is not None
    assert replica_result.selection is not None
    receipt = replica_result.receipt
    distribution = replica_result.selection
    request = materialization.ExecutionMaterializationRequestV1(
        schema_version=materialization.MATERIALIZATION_REQUEST_VERSION,
        request_id="request-materialization-001",
        expected_release_id=distribution.release_id,
        expected_logical_uri=distribution.logical_uri,
        expected_content_sha256=distribution.content_sha256,
        expected_manifest_sha256=distribution.manifest_sha256,
        expected_replica_receipt_sha256=distribution.receipt_sha256,
        action_context=context,
        source_authority=materialization.SOURCE_AUTHORITY,
        target_authority=materialization.TARGET_AUTHORITY,
    )
    mapping = make_materialization_mapping(suffix=mapping_suffix)
    storage_port = InMemoryMaterializationStoragePort(mapping, replica_port)
    return MaterializationFixture(
        context=context,
        source=source,
        replica_receipt=receipt,
        distribution_selection=distribution,
        replica_port=replica_port,
        request=request,
        preflight_decision=make_pull_decision(
            receipt,
            context,
            evaluated_at=NOW + timedelta(hours=5),
        ),
        commit_decision=make_pull_decision(
            receipt,
            context,
            evaluated_at=NOW + timedelta(hours=6),
        ),
        mapping=mapping,
        storage_port=storage_port,
    )


def materialize(
    fixture: MaterializationFixture,
    *,
    request: materialization.ExecutionMaterializationRequestV1 | None = None,
    commit_decision: object | None = None,
    current_replica_selection: replica.DistributionSelectionV1 | None = None,
) -> materialization.MaterializationResultV1:
    return materialization.materialize_repository_fixture_execution_cache(
        request or fixture.request,
        fixture.replica_receipt,
        fixture.distribution_selection,
        fixture.preflight_decision,
        fixture.context,
        commit_decision or fixture.commit_decision,
        fixture.context,
        current_replica_selection or fixture.distribution_selection,
        fixture.mapping,
        fixture.storage_port,
    )


def make_candidate(
    fixture: MaterializationFixture,
    *,
    request: materialization.ExecutionMaterializationRequestV1 | None = None,
) -> (
    materialization.VerifiedCacheCandidateV1
    | materialization.MaterializationResultV1
):
    preflight = materialization.validate_materialization_preflight(
        request or fixture.request,
        fixture.replica_receipt,
        fixture.distribution_selection,
        fixture.preflight_decision,
        fixture.context,
    )
    assert isinstance(preflight, materialization.MaterializationPreflightV1)
    return materialization.pull_and_verify_execution_staging(
        preflight,
        fixture.mapping,
        fixture.storage_port,
    )


def test_t_s04_p01_normal_materialization_exact_types_four_of_four() -> None:
    fixture = make_fixture()

    result = materialize(fixture)

    assert result.status is materialization.MaterializationStatusV1.MATERIALIZED
    assert result.receipt is not None
    assert result.selection is not None
    assert result.handle is not None
    assert result.receipt.verification_vector.complete is True
    assert result.selection.source_kind == materialization.EXECUTION_LOCAL_SOURCE_KIND
    assert result.handle.source_kind == materialization.EXECUTION_LOCAL_SOURCE_KIND
    assert fixture.storage_port.pull_calls == 1
    assert fixture.replica_port.read_calls == 1
    assert fixture.storage_port.persist_calls == 1
    assert fixture.storage_port.cas_calls == 1


def test_t_s04_p02_deterministic_receipt_and_idempotent_cache_reuse() -> None:
    fixture = make_fixture()
    results = []
    for suffix in ("one", "two", "three"):
        mapping = make_materialization_mapping(suffix=suffix)
        port = InMemoryMaterializationStoragePort(mapping, fixture.replica_port)
        local_fixture = replace(fixture, mapping=mapping, storage_port=port)
        results.append(materialize(local_fixture))

    receipts = [result.receipt for result in results]
    assert all(receipt is not None for receipt in receipts)
    assert len({receipt.receipt_sha256 for receipt in receipts if receipt}) == 1
    first = materialize(fixture)
    second = materialize(
        fixture,
        commit_decision=make_pull_decision(
            fixture.replica_receipt,
            fixture.context,
            evaluated_at=NOW + timedelta(hours=7),
        ),
    )
    assert first.status is second.status is materialization.MaterializationStatusV1.MATERIALIZED
    assert len(fixture.storage_port._immutable) == 1
    assert fixture.storage_port.persist_calls == fixture.storage_port.cas_calls == 2


def test_t_s04_n01_independent_authorization_is_required_before_read() -> None:
    fixture = make_fixture()
    missing_record = make_pull_decision(
        fixture.replica_receipt,
        fixture.context,
        evaluated_at=NOW + timedelta(hours=5),
        include_record=False,
    )
    sync_only = make_sync_decision(
        fixture.source,
        fixture.context,
        evaluated_at=NOW + timedelta(hours=5),
    )
    expired = make_pull_decision(
        fixture.replica_receipt,
        fixture.context,
        evaluated_at=NOW + timedelta(hours=13),
    )

    for decision in (None, missing_record, sync_only, expired):
        result = materialization.validate_materialization_preflight(
            fixture.request,
            fixture.replica_receipt,
            fixture.distribution_selection,
            decision,
            fixture.context,
        )
        assert isinstance(result, materialization.MaterializationResultV1)
        assert result.status is materialization.MaterializationStatusV1.BLOCKED
    assert fixture.storage_port.pull_calls == 0
    assert fixture.replica_port.read_calls == 0


def test_t_s04_n02_predecessor_and_context_mismatch_block_before_read() -> None:
    fixture = make_fixture()
    stale_distribution = replace(
        fixture.distribution_selection,
        receipt_sha256=HASH_B,
    )
    stale = materialization.validate_materialization_preflight(
        fixture.request,
        fixture.replica_receipt,
        stale_distribution,
        fixture.preflight_decision,
        fixture.context,
    )
    drift_context = make_context(scope_sha256=HASH_B)
    context_drift = materialization.validate_materialization_preflight(
        replace(fixture.request, action_context=drift_context),
        fixture.replica_receipt,
        fixture.distribution_selection,
        fixture.preflight_decision,
        fixture.context,
    )

    assert stale.reason is materialization.MaterializationBlockReasonV1.INELIGIBLE_REPLICA_PREDECESSOR
    assert context_drift.reason is materialization.MaterializationBlockReasonV1.CONTEXT_MISMATCH
    assert fixture.storage_port.pull_calls == fixture.replica_port.read_calls == 0


def test_t_s04_n03_fresh_commit_revoke_and_replica_drift_preserve_pointer() -> None:
    fixture = make_fixture()
    candidate = make_candidate(fixture)
    assert isinstance(candidate, materialization.VerifiedCacheCandidateV1)
    revoked = make_pull_decision(
        fixture.replica_receipt,
        fixture.context,
        evaluated_at=NOW + timedelta(hours=7),
        revoked=True,
    )
    revoked_result = materialization.commit_execution_cache(
        candidate,
        revoked,
        fixture.context,
        fixture.distribution_selection,
        fixture.storage_port,
    )
    drifted = replace(
        fixture.distribution_selection,
        selection_revision=fixture.distribution_selection.selection_revision + 1,
    )
    drift_result = materialization.commit_execution_cache(
        candidate,
        make_pull_decision(
            fixture.replica_receipt,
            fixture.context,
            evaluated_at=NOW + timedelta(hours=8),
        ),
        fixture.context,
        drifted,
        fixture.storage_port,
    )

    assert revoked_result.reason is materialization.MaterializationBlockReasonV1.COMMIT_AUTHORIZATION_INVALID
    assert drift_result.reason is materialization.MaterializationBlockReasonV1.REPLICA_SELECTION_DRIFT
    assert fixture.storage_port.current_selection is None
    assert fixture.storage_port.cas_calls == 0


def test_t_s04_n04_direct_nas_research_and_shared_runtime_sources_denied() -> None:
    fixture = make_fixture()
    for source in ("direct_nas_runtime", "direct_research", "shared_drive_runtime"):
        request = replace(fixture.request, source_authority=source)
        result = materialization.validate_materialization_preflight(
            request,
            fixture.replica_receipt,
            fixture.distribution_selection,
            fixture.preflight_decision,
            fixture.context,
        )
        assert result.reason is materialization.MaterializationBlockReasonV1.SOURCE_AUTHORITY_INVALID
    assert fixture.storage_port.pull_calls == fixture.replica_port.read_calls == 0


def test_t_s04_n05_release_manifest_and_content_mismatch_never_commit() -> None:
    fixture = make_fixture()
    mutations = (
        ("expected_release_id", "release-fixture-999", materialization.MaterializationBlockReasonV1.RELEASE_MISMATCH),
        ("expected_manifest_sha256", HASH_B, materialization.MaterializationBlockReasonV1.MANIFEST_MISMATCH),
        ("expected_content_sha256", HASH_C, materialization.MaterializationBlockReasonV1.CONTENT_MISMATCH),
    )
    for field_name, value, reason in mutations:
        request = replace(fixture.request, **{field_name: value})
        result = make_candidate(fixture, request=request)
        assert isinstance(result, materialization.MaterializationResultV1)
        assert result.reason is reason
    assert fixture.storage_port.pull_calls == fixture.replica_port.read_calls == 3
    assert fixture.storage_port.persist_calls == fixture.storage_port.cas_calls == 0


def test_t_s04_n06_unselected_or_stale_receipt_is_not_a_byte_source() -> None:
    fixture = make_fixture()
    stale_request = replace(
        fixture.request,
        expected_replica_receipt_sha256=HASH_B,
    )

    result = materialization.validate_materialization_preflight(
        stale_request,
        fixture.replica_receipt,
        fixture.distribution_selection,
        fixture.preflight_decision,
        fixture.context,
    )

    assert result.reason is materialization.MaterializationBlockReasonV1.INELIGIBLE_REPLICA_PREDECESSOR
    assert fixture.storage_port.pull_calls == fixture.replica_port.read_calls == 0


def test_t_s04_n07_fixture_origin_with_real_target_is_never_accepted() -> None:
    fixture = make_fixture()
    real_context = make_context(target_kind=ActionTargetKindV1.REAL_OPERATION)
    request = replace(fixture.request, action_context=real_context)
    decision = make_pull_decision(
        fixture.replica_receipt,
        real_context,
        evaluated_at=NOW + timedelta(hours=5),
    )

    result = materialization.validate_materialization_preflight(
        request,
        fixture.replica_receipt,
        fixture.distribution_selection,
        decision,
        real_context,
    )

    assert result.reason is materialization.MaterializationBlockReasonV1.TARGET_KIND_INVALID
    assert fixture.storage_port.pull_calls == fixture.replica_port.read_calls == 0


def test_t_s04_n08_non_fixture_port_and_path_escape_are_rejected() -> None:
    fixture = make_fixture()
    with pytest.raises(materialization.MaterializationContractError):
        replace(fixture.mapping, cache_handle="../escape")
    preflight = materialization.validate_materialization_preflight(
        fixture.request,
        fixture.replica_receipt,
        fixture.distribution_selection,
        fixture.preflight_decision,
        fixture.context,
    )
    assert isinstance(preflight, materialization.MaterializationPreflightV1)

    result = materialization.pull_and_verify_execution_staging(
        preflight,
        fixture.mapping,
        object(),
    )

    assert result.reason is materialization.MaterializationBlockReasonV1.PORT_BINDING_INVALID
    assert fixture.replica_port.read_calls == 0


def test_t_s04_f01_pull_interruption_leaves_only_non_runtime_staging() -> None:
    fixture = make_fixture()
    fixture.storage_port.inject_pull_interruption = True

    result = materialize(fixture)

    assert result.reason is materialization.MaterializationBlockReasonV1.STAGING_INTERRUPTED
    assert fixture.storage_port.pull_calls == 1
    assert fixture.replica_port.read_calls == 0
    assert fixture.storage_port.persist_calls == fixture.storage_port.cas_calls == 0
    assert fixture.storage_port.current_selection is None


def test_t_s04_f02_immutable_and_cas_conflicts_preserve_previous_cache() -> None:
    immutable_fixture = make_fixture()
    previous = materialize(immutable_fixture)
    assert previous.selection is not None
    candidate = make_candidate(immutable_fixture)
    assert isinstance(candidate, materialization.VerifiedCacheCandidateV1)
    stored_receipt = immutable_fixture.storage_port._immutable[
        candidate.cache_version_ref
    ][1]
    immutable_fixture.storage_port._immutable[candidate.cache_version_ref] = (
        b"corrupt-existing-bytes",
        stored_receipt,
    )
    conflict = materialization.commit_execution_cache(
        candidate,
        make_pull_decision(
            immutable_fixture.replica_receipt,
            immutable_fixture.context,
            evaluated_at=NOW + timedelta(hours=7),
        ),
        immutable_fixture.context,
        immutable_fixture.distribution_selection,
        immutable_fixture.storage_port,
    )
    assert conflict.reason is materialization.MaterializationBlockReasonV1.IMMUTABLE_CACHE_CONFLICT
    assert conflict.selection is conflict.handle is None
    assert immutable_fixture.storage_port.current_selection == previous.selection

    cas_fixture = make_fixture()
    cas_previous = materialize(cas_fixture)
    assert cas_previous.selection is not None
    cas_candidate = make_candidate(cas_fixture)
    assert isinstance(cas_candidate, materialization.VerifiedCacheCandidateV1)
    cas_fixture.storage_port.inject_cas_failure = True
    cas_calls_before = cas_fixture.storage_port.cas_calls
    cas_conflict = materialization.commit_execution_cache(
        cas_candidate,
        make_pull_decision(
            cas_fixture.replica_receipt,
            cas_fixture.context,
            evaluated_at=NOW + timedelta(hours=7),
        ),
        cas_fixture.context,
        cas_fixture.distribution_selection,
        cas_fixture.storage_port,
    )
    assert cas_conflict.reason is materialization.MaterializationBlockReasonV1.POINTER_CONFLICT
    assert cas_conflict.selection is cas_conflict.handle is None
    assert cas_fixture.storage_port.current_selection == cas_previous.selection
    assert cas_fixture.storage_port.cas_calls == cas_calls_before + 1


def test_t_s04_f03_tampered_seal_bytes_fail_in_the_single_s02_verifier(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = make_fixture()
    bundle, source_selection, receipt = fixture.replica_port._immutable[
        fixture.distribution_selection.replica_version_ref
    ]
    tampered_seal = replace(
        bundle.seal,
        sealed_at=bundle.seal.sealed_at + timedelta(seconds=1),
    )
    fixture.replica_port._immutable[
        fixture.distribution_selection.replica_version_ref
    ] = (replace(bundle, seal=tampered_seal), source_selection, receipt)
    verifier_calls = 0
    verifier = artifact.verify_sealed_trial_return_bundle

    def counted_verifier(*args: object, **kwargs: object):
        nonlocal verifier_calls
        verifier_calls += 1
        return verifier(*args, **kwargs)

    monkeypatch.setattr(
        materialization,
        "verify_sealed_trial_return_bundle",
        counted_verifier,
    )

    result = materialize(fixture)

    assert result.reason is materialization.MaterializationBlockReasonV1.SEAL_MISMATCH
    assert verifier_calls == 1
    assert fixture.storage_port.persist_calls == fixture.storage_port.cas_calls == 0
    assert fixture.storage_port.current_selection is None


def test_t_s04_b01_physical_mapping_is_excluded_from_receipt_identity() -> None:
    fixture = make_fixture()
    receipts = []
    mappings = tuple(
        make_materialization_mapping(suffix=suffix)
        for suffix in ("root-a", "root-b", "root-c")
    )
    for mapping in mappings:
        port = InMemoryMaterializationStoragePort(mapping, fixture.replica_port)
        result = materialize(replace(fixture, mapping=mapping, storage_port=port))
        assert result.receipt is not None
        receipts.append(result.receipt)

    bodies = tuple(
        materialization.canonical_materialization_receipt_bytes(receipt)
        for receipt in receipts
    )
    assert len({receipt.receipt_sha256 for receipt in receipts}) == 1
    assert len(set(bodies)) == 1
    assert all(
        handle.encode() not in bodies[0]
        for mapping in mappings
        for handle in (
            mapping.replica_handle,
            mapping.staging_handle,
            mapping.cache_handle,
            mapping.pointer_handle,
        )
    )


def test_t_s04_b02_only_selected_execution_local_handle_is_resolvable() -> None:
    fixture = make_fixture()
    result = materialize(fixture)
    assert result.selection is not None

    handle = materialization.resolve_execution_local_handle(
        result.selection,
        fixture.storage_port,
    )

    assert handle.source_kind == materialization.EXECUTION_LOCAL_SOURCE_KIND
    assert handle.local_handle.startswith(fixture.mapping.cache_handle + "/")
    assert all(
        forbidden not in materialization.__all__
        for forbidden in (
            "resolve_nas_handle",
            "resolve_research_handle",
            "resolve_staging_handle",
            "open_runtime_handle",
        )
    )


def test_cp6r1_f001_receipt_is_exact_readable_before_selection_cas() -> None:
    fixture = make_fixture()

    first = materialize(fixture)
    same_receipt = materialize(fixture)
    assert first.receipt is not None
    assert first.selection is not None
    assert same_receipt.receipt == first.receipt
    assert same_receipt.selection is not None
    assert fixture.storage_port.read_materialization_receipt(
        same_receipt.selection.materialization_receipt_sha256
    ) == same_receipt.receipt

    rotated_decision = replace(
        fixture.commit_decision,
        evidence_ref="fixture:execution-materialize-rotated",
    )
    rotated = materialize(fixture, commit_decision=rotated_decision)
    assert rotated.receipt is not None
    assert rotated.selection is not None
    assert rotated.receipt.receipt_sha256 != first.receipt.receipt_sha256
    assert fixture.storage_port.read_materialization_receipt(
        rotated.selection.materialization_receipt_sha256
    ) == rotated.receipt

    failure_fixture = make_fixture()
    previous = materialize(failure_fixture)
    assert previous.selection is not None
    failure_fixture.storage_port.inject_receipt_persist_failure = True
    failure = materialize(
        failure_fixture,
        commit_decision=replace(
            failure_fixture.commit_decision,
            evidence_ref="fixture:execution-materialize-rotated",
        ),
    )
    assert failure.reason is (
        materialization.MaterializationBlockReasonV1.RECEIPT_PERSISTENCE_FAILED
    )
    assert failure.receipt is failure.selection is failure.handle is None
    assert failure_fixture.storage_port.current_selection == previous.selection


def test_cp6r1_f002_resolver_requires_current_exact_selection_capability() -> None:
    fixture = make_fixture()
    old = materialize(fixture)
    current = materialize(
        fixture,
        commit_decision=replace(
            fixture.commit_decision,
            evidence_ref="fixture:execution-materialize-current",
        ),
    )
    assert old.selection is not None
    assert current.selection is not None
    forged = replace(
        current.selection,
        materialization_receipt_sha256=HASH_C,
        selection_revision=current.selection.selection_revision + 1,
    )
    uncommitted = replace(
        current.selection,
        selection_revision=current.selection.selection_revision + 1,
    )

    rejected = (old.selection, forged, uncommitted)
    for selection in rejected:
        with pytest.raises(materialization.MaterializationContractError):
            materialization.resolve_execution_local_handle(
                selection,
                fixture.storage_port,
            )

    handle = materialization.resolve_execution_local_handle(
        current.selection,
        fixture.storage_port,
    )
    assert handle.source_kind == materialization.EXECUTION_LOCAL_SOURCE_KIND
    with pytest.raises(materialization.MaterializationContractError):
        materialization.resolve_execution_local_handle(
            current.selection,
            fixture.mapping,
        )
    with pytest.raises(materialization.MaterializationContractError):
        materialization.resolve_execution_local_handle(
            current.selection,
            current.receipt,
        )


def test_cp6r1_f003_all_sensitive_evidence_markers_fail_before_persist() -> None:
    fixture = make_fixture()
    markers = ("password", "passwd", "secret", "token", "credential")
    ref_fields = ("approval_ref", "evidence_ref")

    for marker in markers:
        for ref_field in ref_fields:
            invalid_preflight = replace(
                fixture.preflight_decision,
                **{ref_field: f"fixture:{marker}-ref"},
            )
            result = materialization.validate_materialization_preflight(
                fixture.request,
                fixture.replica_receipt,
                fixture.distribution_selection,
                invalid_preflight,
                fixture.context,
            )
            assert isinstance(result, materialization.MaterializationResultV1)
            assert result.reason is (
                materialization.MaterializationBlockReasonV1.AUTHORIZATION_INVALID
            )
    assert fixture.storage_port.pull_calls == 0
    assert fixture.storage_port.persist_calls == fixture.storage_port.cas_calls == 0

    candidate = make_candidate(fixture)
    assert isinstance(candidate, materialization.VerifiedCacheCandidateV1)
    for marker in markers:
        for ref_field in ref_fields:
            invalid_commit = replace(
                fixture.commit_decision,
                **{ref_field: f"fixture:{marker}-ref"},
            )
            result = materialization.commit_execution_cache(
                candidate,
                invalid_commit,
                fixture.context,
                fixture.distribution_selection,
                fixture.storage_port,
            )
            assert result.reason is (
                materialization.MaterializationBlockReasonV1.COMMIT_AUTHORIZATION_INVALID
            )
    assert fixture.storage_port.persist_calls == fixture.storage_port.cas_calls == 0

    legal = materialization.commit_execution_cache(
        candidate,
        fixture.commit_decision,
        fixture.context,
        fixture.distribution_selection,
        fixture.storage_port,
    )
    assert legal.receipt is not None
    assert legal.selection is not None
    canonical_surfaces = (
        materialization.canonical_materialization_receipt_bytes(legal.receipt)
        + repr(legal.selection).encode("utf-8")
    ).lower()
    assert sum(canonical_surfaces.count(marker.encode()) for marker in markers) == 0


def test_t_s04_b03_recovery_dependency_and_zero_real_operation_guard() -> None:
    source = inspect.getsource(materialization)
    tree = ast.parse(source)
    calls = [
        node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    ]
    imports = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.Import, ast.ImportFrom))
        for alias in node.names
    }
    test_ids = {
        name.removeprefix("test_").upper().replace("_", "-")[:9]
        for name, value in globals().items()
        if name.startswith("test_t_s04_") and callable(value)
    }
    test_names = [
        name
        for name, value in globals().items()
        if name.startswith("test_t_s04_") and callable(value)
    ]

    assert calls.count("verify_sealed_trial_return_bundle") == 1
    assert source.count("read_selected_replica(") == 1
    assert "canonical_artifact_seal" not in source
    assert not ({"os", "pathlib", "socket", "subprocess", "requests"} & imports)
    assert "read_bytes(" not in source
    assert "open(" not in source
    assert len(test_names) == 16
    assert len(test_ids) == 16
    with pytest.raises(TypeError):
        type(
            "BypassPort",
            (materialization.MaterializationStoragePortV1,),
            {"pull_to_staging": lambda *_args: None},
        )
