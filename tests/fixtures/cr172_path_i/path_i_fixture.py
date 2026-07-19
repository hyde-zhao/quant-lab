"""CR-172 S05 的 repository-local、test-only fixture 组装器。"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
import json
from pathlib import Path
from typing import Any

from engine.path_i_governance import (
    ActionAuthorizationRecordV1,
    ActionAuthorizationRequestV1,
    ActionDecisionOriginV1,
    ActionDecisionV1,
    ActionPrerequisiteEvidenceV1,
    ActionPrerequisiteProvenanceV1,
    ActionScopeContextV1,
    ActionTargetKindV1,
    PathIActionKind,
    evaluate_action_decision,
)
from engine.research_artifact_materialization import (
    EXECUTION_LOCAL_SOURCE_KIND,
    MATERIALIZATION_MAPPING_VERSION,
    MATERIALIZATION_REQUEST_VERSION,
    SOURCE_AUTHORITY,
    TARGET_AUTHORITY,
    ExecutionCacheSelectionV1,
    ExecutionDeploymentMappingV1,
    ExecutionMaterializationRequestV1,
    MaterializationReceiptV1,
    MaterializationStoragePortV1,
    VerifiedCacheCandidateV1,
    materialize_repository_fixture_execution_cache,
)
from engine.research_artifact_replica import (
    REPLICA_MAPPING_VERSION,
    REPLICA_REQUEST_VERSION,
    DistributionSelectionV1,
    ReplicaDeploymentMappingV1,
    ReplicaStoragePortError,
    ReplicaStoragePortV1,
    ReplicaSyncRequestV1,
    ReplicaVerificationReceiptV1,
    VerifiedReplicaCandidateV1,
    publish_repository_fixture_replica,
)
from engine.trial_return_artifact import (
    ALIGNMENT_POLICY_V1,
    ENDPOINT_SEMANTICS_V1,
    RETURN_BASIS_V1,
    RETURN_DEFINITION_SCHEMA_VERSION,
    RepositoryFixtureTrialReturnPortV1,
    ReturnDefinitionV1,
    TrialReturnIdentityV1,
    TrialReturnObservationV1,
    TrialReturnSourceKindV1,
    VerifiedTrialReturnBundleV1,
    publish_repository_fixture_trial_return_artifact,
)


FIXTURE_PATHS = (
    Path(__file__).with_name("sealed_chain_v1.json"),
    Path(__file__).with_name("scenario_catalog.json"),
    Path(__file__).with_name("failure_mutations_v1.json"),
    Path(__file__).with_name("zero_operation_oracle_v1.json"),
)


def load_fixture() -> dict[str, Any]:
    """无规则地合并四份版本化 fixture；不访问仓库外路径。"""

    merged: dict[str, Any] = {}
    schemas: list[str] = []
    for path in FIXTURE_PATHS:
        document = json.loads(path.read_text(encoding="utf-8"))
        schemas.append(document.pop("schema_version"))
        overlap = set(merged).intersection(document)
        if overlap:
            raise ValueError(f"fixture 顶层字段重复: {sorted(overlap)}")
        merged.update(document)
    merged["fixture_schema_versions"] = tuple(schemas)
    return merged


def parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value)


def make_context(
    fixture: dict[str, Any],
    *,
    target_kind: ActionTargetKindV1 = ActionTargetKindV1.REPOSITORY_FIXTURE,
    scope_revision: str | None = None,
) -> ActionScopeContextV1:
    identity = fixture["identity"]
    scope = fixture["scope"]
    return ActionScopeContextV1(
        schema_version=scope["schema_version"],
        scope_revision=scope_revision or scope["scope_revision"],
        scope_sha256=scope["scope_sha256"],
        release_id=identity["release_id"],
        run_id=identity["run_id"],
        family_id=identity["family_id"],
        target_kind=target_kind,
    )


def make_record(
    fixture: dict[str, Any],
    action_kind: PathIActionKind,
    *,
    revoked: bool = False,
) -> ActionAuthorizationRecordV1:
    evaluated_at = parse_time(fixture["times"]["evaluated_at"])
    suffix = action_kind.value.replace("_", "-").lower()
    return ActionAuthorizationRecordV1(
        authorization_id=f"fixture-auth-{suffix}",
        action_kind=action_kind,
        owner="repository-fixture-owner",
        scope_revision=fixture["scope"]["scope_revision"],
        scope_sha256=fixture["scope"]["scope_sha256"],
        allowed_logical_paths=(fixture["identity"]["logical_uri"],),
        denied_logical_paths=(),
        valid_from=evaluated_at - timedelta(minutes=1),
        expires_at=evaluated_at + timedelta(days=1),
        revoked_at=evaluated_at if revoked else None,
        approval_ref=f"fixture://repository/cr172/approvals/{suffix}.json",
        evidence_ref=f"fixture://repository/cr172/evidence/{suffix}.json",
    )


def make_predecessor(
    fixture: dict[str, Any],
    decision: ActionDecisionV1,
    provenance_kind: ActionPrerequisiteProvenanceV1,
    *,
    content_sha256: str = "",
    manifest_sha256: str = "",
    context: ActionScopeContextV1 | None = None,
) -> ActionPrerequisiteEvidenceV1:
    return ActionPrerequisiteEvidenceV1(
        predecessor_action_kind=decision.action_kind,
        authorization_id=decision.authorization_id,
        authorized=decision.authorized,
        eligible_to_execute=decision.eligible_to_execute,
        context=context or make_context(fixture),
        provenance_kind=provenance_kind,
        logical_uri=fixture["identity"]["logical_uri"],
        content_sha256=content_sha256,
        manifest_sha256=manifest_sha256,
        evidence_ref=decision.evidence_ref,
    )


def make_decision(
    fixture: dict[str, Any],
    action_kind: PathIActionKind,
    *,
    predecessor: ActionPrerequisiteEvidenceV1 | None = None,
    context: ActionScopeContextV1 | None = None,
    record: ActionAuthorizationRecordV1 | None = None,
    origin: ActionDecisionOriginV1 = ActionDecisionOriginV1.REPOSITORY_FIXTURE,
    evaluated_at: datetime | None = None,
) -> ActionDecisionV1:
    actual_context = context or make_context(fixture)
    request = ActionAuthorizationRequestV1(
        action_kind=action_kind,
        logical_path=fixture["identity"]["logical_uri"],
        context=actual_context,
    )
    actual_record = record if record is not None else make_record(fixture, action_kind)
    return evaluate_action_decision(
        request,
        actual_record,
        () if predecessor is None else (predecessor,),
        decision_origin=origin,
        evaluated_at=evaluated_at or parse_time(fixture["times"]["evaluated_at"]),
    )


class MemoryReplicaStoragePort(ReplicaStoragePortV1):
    """只实现 S03 storage-port 协议的内存 fixture，不实现任何 NAS adapter。"""

    def __init__(self, mapping: ReplicaDeploymentMappingV1) -> None:
        super().__init__(mapping)
        self._current: DistributionSelectionV1 | None = None
        self._immutable: dict[
            str,
            tuple[
                object,
                object,
                ReplicaVerificationReceiptV1,
            ],
        ] = {}
        self.stage_calls = 0
        self.persist_calls = 0
        self.cas_calls = 0
        self.fail_stage = False

    @property
    def current_selection(self) -> DistributionSelectionV1 | None:
        return self._current

    def stage_bundle(self, preflight: object, staging_token: object) -> object:
        self.stage_calls += 1
        if self.fail_stage:
            raise RuntimeError("controlled repository fixture stage failure")
        return preflight.verified_source.bundle

    def persist_immutable_replica(
        self,
        candidate: VerifiedReplicaCandidateV1,
        receipt: ReplicaVerificationReceiptV1,
    ) -> None:
        self.persist_calls += 1
        value = (
            candidate.staged_verified.bundle,
            candidate.staged_verified.selection,
            receipt,
        )
        current = self._immutable.get(candidate.replica_version_ref)
        if current is not None and current != value:
            raise RuntimeError("immutable replica conflict")
        self._immutable[candidate.replica_version_ref] = value

    def compare_and_swap_selection(
        self,
        expected_previous: DistributionSelectionV1 | None,
        new_selection: DistributionSelectionV1,
    ) -> bool:
        self.cas_calls += 1
        if self._current != expected_previous:
            return False
        self._current = new_selection
        return True

    def _read_immutable_replica(self, replica_version_ref: str) -> tuple[object, object, object]:
        try:
            return self._immutable[replica_version_ref]
        except KeyError as exc:
            raise ReplicaStoragePortError from exc


class MemoryMaterializationStoragePort(MaterializationStoragePortV1):
    """只实现 S04 storage-port 协议的内存 fixture，不实现执行机 adapter。"""

    def __init__(
        self,
        mapping: ExecutionDeploymentMappingV1,
        replica_port: ReplicaStoragePortV1,
    ) -> None:
        super().__init__(mapping, replica_port)
        self._current: ExecutionCacheSelectionV1 | None = None
        self._receipts: dict[str, MaterializationReceiptV1] = {}
        self.persist_calls = 0
        self.cas_calls = 0
        self.fail_pull = False

    @property
    def current_selection(self) -> ExecutionCacheSelectionV1 | None:
        return self._current

    def _before_selected_read(self) -> None:
        if self.fail_pull:
            raise RuntimeError("controlled repository fixture pull failure")

    def persist_immutable_cache(
        self,
        candidate: VerifiedCacheCandidateV1,
        receipt: MaterializationReceiptV1,
    ) -> None:
        self.persist_calls += 1
        current = self._receipts.get(receipt.receipt_sha256)
        if current is not None and current != receipt:
            raise RuntimeError("immutable cache conflict")
        self._receipts[receipt.receipt_sha256] = receipt

    def read_materialization_receipt(
        self,
        receipt_sha256: str,
    ) -> MaterializationReceiptV1 | None:
        return self._receipts.get(receipt_sha256)

    def compare_and_swap_cache_selection(
        self,
        expected_previous: ExecutionCacheSelectionV1 | None,
        new_selection: ExecutionCacheSelectionV1,
    ) -> bool:
        self.cas_calls += 1
        if self._current != expected_previous:
            return False
        self._current = new_selection
        return True


@dataclass(slots=True)
class PathIChain:
    fixture: dict[str, Any]
    context: ActionScopeContextV1
    decisions: dict[PathIActionKind, ActionDecisionV1]
    commit_decisions: dict[PathIActionKind, ActionDecisionV1]
    verified_source: VerifiedTrialReturnBundleV1
    trial_port: RepositoryFixtureTrialReturnPortV1
    replica_port: MemoryReplicaStoragePort
    replica_result: object
    material_port: MemoryMaterializationStoragePort
    material_result: object


def build_source(fixture: dict[str, Any] | None = None) -> tuple[
    dict[str, Any],
    ActionScopeContextV1,
    dict[PathIActionKind, ActionDecisionV1],
    VerifiedTrialReturnBundleV1,
    RepositoryFixtureTrialReturnPortV1,
]:
    data = fixture or load_fixture()
    context = make_context(data)
    decisions: dict[PathIActionKind, ActionDecisionV1] = {}
    decisions[PathIActionKind.DATA_LAKE_READ] = make_decision(
        data, PathIActionKind.DATA_LAKE_READ
    )
    decisions[PathIActionKind.MULTI_TRIAL_RUNTIME_AND_WORKSPACE_WRITE] = make_decision(
        data,
        PathIActionKind.MULTI_TRIAL_RUNTIME_AND_WORKSPACE_WRITE,
        predecessor=make_predecessor(
            data,
            decisions[PathIActionKind.DATA_LAKE_READ],
            ActionPrerequisiteProvenanceV1.ELIGIBILITY_DECISION,
        ),
    )
    decisions[PathIActionKind.TRIAL_RETURN_GENERATION] = make_decision(
        data,
        PathIActionKind.TRIAL_RETURN_GENERATION,
        predecessor=make_predecessor(
            data,
            decisions[PathIActionKind.MULTI_TRIAL_RUNTIME_AND_WORKSPACE_WRITE],
            ActionPrerequisiteProvenanceV1.ELIGIBILITY_DECISION,
        ),
    )
    identity = TrialReturnIdentityV1(**data["identity"])
    observations = tuple(
        TrialReturnObservationV1(
            interval_start=parse_time(item["interval_start"]),
            timestamp=parse_time(item["timestamp"]),
            simple_return=item["simple_return"],
        )
        for item in data["observations"]
    )
    definition = ReturnDefinitionV1(
        object_kind=TrialReturnSourceKindV1.TRIAL_PORTFOLIO_RETURN_SERIES,
        schema_version=RETURN_DEFINITION_SCHEMA_VERSION,
        return_basis=RETURN_BASIS_V1,
        endpoint_semantics=ENDPOINT_SEMANTICS_V1,
        non_overlap_required=True,
        alignment_policy=ALIGNMENT_POLICY_V1,
    )
    trial_port = RepositoryFixtureTrialReturnPortV1(
        identity,
        decisions[PathIActionKind.TRIAL_RETURN_GENERATION],
        context,
    )
    verified = publish_repository_fixture_trial_return_artifact(
        identity,
        observations,
        definition,
        decisions[PathIActionKind.TRIAL_RETURN_GENERATION],
        context,
        trial_port,
        created_at=parse_time(data["times"]["created_at"]),
        sealed_at=parse_time(data["times"]["sealed_at"]),
        source_lineage_refs=tuple(data["source_lineage_refs"]),
    )
    return data, context, decisions, verified, trial_port


def build_chain(*, materialize: bool = True) -> PathIChain:
    data, context, decisions, verified, trial_port = build_source()
    sealed_predecessor = make_predecessor(
        data,
        decisions[PathIActionKind.TRIAL_RETURN_GENERATION],
        ActionPrerequisiteProvenanceV1.SEALED_TRIAL_RETURN,
        content_sha256=verified.bundle.payload.content_sha256,
        manifest_sha256=verified.bundle.manifest_sha256,
    )
    decisions[PathIActionKind.NAS_REPLICA_SYNC] = make_decision(
        data,
        PathIActionKind.NAS_REPLICA_SYNC,
        predecessor=sealed_predecessor,
    )
    commit_decisions = {
        PathIActionKind.NAS_REPLICA_SYNC: make_decision(
            data,
            PathIActionKind.NAS_REPLICA_SYNC,
            predecessor=sealed_predecessor,
            evaluated_at=(
                parse_time(data["times"]["evaluated_at"]) + timedelta(seconds=1)
            ),
        )
    }
    replica_request = ReplicaSyncRequestV1(
        schema_version=REPLICA_REQUEST_VERSION,
        request_id="replica-request-cr172-s05-001",
        expected_release_id=verified.selection.release_id,
        expected_logical_uri=verified.selection.logical_uri,
        expected_content_sha256=verified.selection.content_sha256,
        expected_manifest_sha256=verified.selection.manifest_sha256,
        expected_source_selection_sha256=data["expected_source_selection_sha256"],
    )
    replica_mapping = ReplicaDeploymentMappingV1(
        mapping_version=REPLICA_MAPPING_VERSION,
        repository_owned=True,
        decision_origin=ActionDecisionOriginV1.REPOSITORY_FIXTURE,
        target_kind=ActionTargetKindV1.REPOSITORY_FIXTURE,
        logical_uri=verified.selection.logical_uri,
        source_handle="fixture/research/source",
        staging_handle="fixture/replica/staging",
        version_handle="fixture/replica/versions",
        pointer_handle="fixture/replica/current",
    )
    replica_port = MemoryReplicaStoragePort(replica_mapping)
    replica_result = publish_repository_fixture_replica(
        replica_request,
        verified.bundle,
        verified.selection,
        decisions[PathIActionKind.NAS_REPLICA_SYNC],
        context,
        commit_decisions[PathIActionKind.NAS_REPLICA_SYNC],
        context,
        replica_mapping,
        replica_port,
    )
    if replica_result.receipt is None or replica_result.selection is None:
        raise AssertionError(f"repository fixture replica blocked: {replica_result.reason}")
    replica_predecessor = ActionPrerequisiteEvidenceV1(
        predecessor_action_kind=PathIActionKind.NAS_REPLICA_SYNC,
        authorization_id=decisions[PathIActionKind.NAS_REPLICA_SYNC].authorization_id,
        authorized=True,
        eligible_to_execute=True,
        context=context,
        provenance_kind=(
            ActionPrerequisiteProvenanceV1.VERIFIED_REPLICA_RECEIPT
        ),
        logical_uri=verified.selection.logical_uri,
        content_sha256=replica_result.receipt.content_sha256,
        manifest_sha256=replica_result.receipt.manifest_sha256,
        evidence_ref=replica_result.receipt.receipt_sha256,
    )
    decisions[PathIActionKind.EXECUTION_PULL_VERIFY_MATERIALIZE] = make_decision(
        data,
        PathIActionKind.EXECUTION_PULL_VERIFY_MATERIALIZE,
        predecessor=replica_predecessor,
    )
    commit_decisions[
        PathIActionKind.EXECUTION_PULL_VERIFY_MATERIALIZE
    ] = make_decision(
        data,
        PathIActionKind.EXECUTION_PULL_VERIFY_MATERIALIZE,
        predecessor=replica_predecessor,
        evaluated_at=(
            parse_time(data["times"]["evaluated_at"]) + timedelta(seconds=1)
        ),
    )
    material_mapping = ExecutionDeploymentMappingV1(
        mapping_version=MATERIALIZATION_MAPPING_VERSION,
        repository_owned=True,
        decision_origin=ActionDecisionOriginV1.REPOSITORY_FIXTURE,
        target_kind=ActionTargetKindV1.REPOSITORY_FIXTURE,
        logical_uri=verified.selection.logical_uri,
        replica_handle="fixture/replica/versions",
        staging_handle="fixture/execution/staging",
        cache_handle="fixture/execution/cache",
        pointer_handle="fixture/execution/current",
    )
    material_port = MemoryMaterializationStoragePort(material_mapping, replica_port)
    material_result: object = None
    if materialize:
        request = make_materialization_request(data, context, replica_result, "001")
        decision = decisions[PathIActionKind.EXECUTION_PULL_VERIFY_MATERIALIZE]
        commit_decision = commit_decisions[
            PathIActionKind.EXECUTION_PULL_VERIFY_MATERIALIZE
        ]
        material_result = materialize_repository_fixture_execution_cache(
            request,
            replica_result.receipt,
            replica_result.selection,
            decision,
            context,
            commit_decision,
            context,
            replica_result.selection,
            material_mapping,
            material_port,
        )
    return PathIChain(
        fixture=data,
        context=context,
        decisions=decisions,
        commit_decisions=commit_decisions,
        verified_source=verified,
        trial_port=trial_port,
        replica_port=replica_port,
        replica_result=replica_result,
        material_port=material_port,
        material_result=material_result,
    )


def make_materialization_request(
    data: dict[str, Any],
    context: ActionScopeContextV1,
    replica_result: object,
    suffix: str,
) -> ExecutionMaterializationRequestV1:
    return ExecutionMaterializationRequestV1(
        schema_version=MATERIALIZATION_REQUEST_VERSION,
        request_id=f"materialization-request-cr172-s05-{suffix}",
        expected_release_id=replica_result.selection.release_id,
        expected_logical_uri=replica_result.selection.logical_uri,
        expected_content_sha256=replica_result.selection.content_sha256,
        expected_manifest_sha256=replica_result.selection.manifest_sha256,
        expected_replica_receipt_sha256=replica_result.receipt.receipt_sha256,
        action_context=context,
        source_authority=SOURCE_AUTHORITY,
        target_authority=TARGET_AUTHORITY,
    )


def materialize_again(chain: PathIChain, suffix: str) -> object:
    decision = chain.decisions[PathIActionKind.EXECUTION_PULL_VERIFY_MATERIALIZE]
    commit_decision = chain.commit_decisions[
        PathIActionKind.EXECUTION_PULL_VERIFY_MATERIALIZE
    ]
    return materialize_repository_fixture_execution_cache(
        make_materialization_request(
            chain.fixture,
            chain.context,
            chain.replica_result,
            suffix,
        ),
        chain.replica_result.receipt,
        chain.replica_result.selection,
        decision,
        chain.context,
        commit_decision,
        chain.context,
        chain.replica_result.selection,
        chain.material_port.mapping,
        chain.material_port,
    )
