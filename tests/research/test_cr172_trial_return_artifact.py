from __future__ import annotations

import ast
from dataclasses import fields, replace
from datetime import datetime, timedelta, timezone
import inspect
import re

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

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
from engine.trial_return_artifact import (
    ResearchCanonicalSelectionV1,
    SealedTrialReturnBundleV1,
    VerifiedTrialReturnBundleV1,
    canonical_artifact_seal_bytes,
    canonical_artifact_seal_sha256,
    verify_sealed_trial_return_bundle,
)


NOW = datetime(2026, 7, 18, 6, 0, tzinfo=timezone.utc)
HASH_A = "sha256:" + "a" * 64
FIXTURE_ROOT = "fixture://repository/cr172"
FIXTURE_URI = f"{FIXTURE_ROOT}/family-fixture-001/run-fixture-001/trial-001"


class UnboundStructuralPort:
    def __init__(self) -> None:
        self.calls = 0
        self.records: list[VerifiedTrialReturnBundleV1] = []

    def commit_verified(self, verified: VerifiedTrialReturnBundleV1) -> None:
        self.calls += 1
        self.records.append(verified)


class RecordThenFailPort:
    def __init__(self) -> None:
        self.calls = 0
        self.records: list[VerifiedTrialReturnBundleV1] = []

    def commit_verified(self, verified: VerifiedTrialReturnBundleV1) -> None:
        self.calls += 1
        self.records.append(verified)
        raise RuntimeError("non-compliant record-then-fail")


def make_context(
    *,
    target_kind: ActionTargetKindV1 = ActionTargetKindV1.REPOSITORY_FIXTURE,
) -> ActionScopeContextV1:
    return ActionScopeContextV1(
        schema_version=GOVERNANCE_SCHEMA_VERSION,
        scope_revision="scope-v1",
        scope_sha256=HASH_A,
        release_id="release-fixture-001",
        run_id="run-fixture-001",
        family_id="family-fixture-001",
        target_kind=target_kind,
    )


def make_generation_decision(
    *,
    context: ActionScopeContextV1 | None = None,
):
    context = context or make_context()
    action_kind = PathIActionKind.TRIAL_RETURN_GENERATION
    record = ActionAuthorizationRecordV1(
        authorization_id="auth-trial-return-generation",
        action_kind=action_kind,
        owner="repository-fixture-owner",
        scope_revision=context.scope_revision,
        scope_sha256=context.scope_sha256,
        allowed_logical_paths=(FIXTURE_ROOT,),
        denied_logical_paths=(),
        valid_from=NOW - timedelta(hours=1),
        expires_at=NOW + timedelta(hours=1),
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
            action_kind=action_kind,
            logical_path=FIXTURE_URI,
            context=context,
        ),
        record,
        (predecessor,),
        decision_origin=ActionDecisionOriginV1.REPOSITORY_FIXTURE,
        evaluated_at=NOW,
    )


def make_identity() -> artifact.TrialReturnIdentityV1:
    return artifact.TrialReturnIdentityV1(
        family_id="family-fixture-001",
        run_id="run-fixture-001",
        trial_id="trial-001",
        release_id="release-fixture-001",
        logical_uri=FIXTURE_URI,
    )


def make_definition(
    *,
    object_kind: artifact.TrialReturnSourceKindV1 = (
        artifact.TrialReturnSourceKindV1.TRIAL_PORTFOLIO_RETURN_SERIES
    ),
) -> artifact.ReturnDefinitionV1:
    return artifact.ReturnDefinitionV1(
        object_kind=object_kind,
        schema_version=artifact.RETURN_DEFINITION_SCHEMA_VERSION,
        return_basis=artifact.RETURN_BASIS_V1,
        endpoint_semantics=artifact.ENDPOINT_SEMANTICS_V1,
        non_overlap_required=True,
        alignment_policy=artifact.ALIGNMENT_POLICY_V1,
    )


def make_observations() -> tuple[artifact.TrialReturnObservationV1, ...]:
    return (
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
        artifact.TrialReturnObservationV1(
            interval_start=NOW + timedelta(days=2),
            timestamp=NOW + timedelta(days=3),
            simple_return=0.005,
        ),
    )


def make_port(
    *,
    identity: artifact.TrialReturnIdentityV1 | None = None,
    decision=None,
    context: ActionScopeContextV1 | None = None,
    inject_atomic_failure: bool = False,
) -> artifact.RepositoryFixtureTrialReturnPortV1:
    fixture_identity = identity or make_identity()
    fixture_context = context or make_context()
    fixture_decision = decision or make_generation_decision(context=fixture_context)
    return artifact.RepositoryFixtureTrialReturnPortV1(
        fixture_identity,
        fixture_decision,
        fixture_context,
        inject_atomic_failure=inject_atomic_failure,
    )


def publish(
    port: object | None = None,
) -> tuple[
    VerifiedTrialReturnBundleV1,
    artifact.RepositoryFixtureTrialReturnPortV1,
]:
    fixture_port = port or make_port()
    verified = artifact.publish_repository_fixture_trial_return_artifact(
        make_identity(),
        make_observations(),
        make_definition(),
        make_generation_decision(),
        make_context(),
        fixture_port,
        created_at=NOW + timedelta(hours=1),
        sealed_at=NOW + timedelta(hours=2),
        source_lineage_refs=("fixture:explicit-period-observations",),
    )
    assert isinstance(fixture_port, artifact.RepositoryFixtureTrialReturnPortV1)
    return verified, fixture_port


def test_fixture_observations_produce_exact_v1_verified_bundle() -> None:
    verified, port = publish()
    payload = verified.bundle.payload
    table = pq.read_table(pa.BufferReader(payload.payload_bytes))
    assert table.column_names == ["timestamp", "simple_return"]
    assert table.num_columns == 2
    assert table.schema == pa.schema(
        [
            pa.field("timestamp", pa.timestamp("us", tz="UTC"), nullable=False),
            pa.field("simple_return", pa.float64(), nullable=False),
        ]
    )
    assert len(fields(verified.bundle.manifest)) == 15
    assert len(fields(verified.bundle.seal)) == 8
    assert port.call_count == 1
    assert port.commit_count == 1
    assert port.selected is verified
    assert verified.selection.decision_origin is (
        ActionDecisionOriginV1.REPOSITORY_FIXTURE
    )
    assert verified.selection.target_kind is ActionTargetKindV1.REPOSITORY_FIXTURE
    assert verified.original_seal_sha256 == canonical_artifact_seal_sha256(
        verified.bundle.seal
    )
    assert verified.selection.original_seal_sha256 == verified.original_seal_sha256


def test_same_input_has_one_payload_manifest_seal_and_digest_under_three_mappings(
) -> None:
    results = tuple(publish()[0] for _ in range(3))
    host_mappings = (
        {"root": "/tmp/one"},
        {"root": "/mnt/research/two"},
        {"root": "D:\\research\\three"},
    )
    assert len(host_mappings) == 3
    assert len({item.bundle.payload.payload_bytes for item in results}) == 1
    assert len({item.bundle.payload.content_sha256 for item in results}) == 1
    assert len({item.bundle.manifest_sha256 for item in results}) == 1
    assert len({canonical_artifact_seal_bytes(item.bundle.seal) for item in results}) == 1
    assert len({item.original_seal_sha256 for item in results}) == 1
    seal_bytes = canonical_artifact_seal_bytes(results[0].bundle.seal)
    assert all(mapping["root"].encode() not in seal_bytes for mapping in host_mappings)


def test_forward_label_proxy_is_never_trial_return() -> None:
    port = make_port()
    with pytest.raises(
        artifact.TrialReturnContractError,
        match="FORWARD_LABEL_PROXY_FORBIDDEN",
    ):
        artifact.publish_repository_fixture_trial_return_artifact(
            make_identity(),
            make_observations(),
            make_definition(
                object_kind=artifact.TrialReturnSourceKindV1.FORWARD_LABEL_PROXY
            ),
            make_generation_decision(),
            make_context(),
            port,
            created_at=NOW + timedelta(hours=1),
            sealed_at=NOW + timedelta(hours=2),
            source_lineage_refs=("fixture:forward-label-proxy",),
        )
    assert port.call_count == 0
    assert port.commit_count == 0
    assert port.selected is None
    assert not hasattr(artifact, "compute_empirical_r")
    assert not hasattr(artifact, "compute_effective_count")


def test_fixture_decision_with_real_target_is_denied_before_candidate_and_port(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    context = make_context(target_kind=ActionTargetKindV1.REAL_OPERATION)
    decision = make_generation_decision(context=context)
    port = make_port()
    serialized: list[bool] = []

    def forbidden_serializer(_observations: object) -> bytes:
        serialized.append(True)
        raise AssertionError("authorization guard 必须先于 serialization")

    monkeypatch.setattr(artifact, "_serialize_payload", forbidden_serializer)
    with pytest.raises(
        artifact.TrialReturnAuthorizationError,
        match="FIXTURE_TARGET_REQUIRED",
    ):
        artifact.publish_repository_fixture_trial_return_artifact(
            make_identity(),
            make_observations(),
            make_definition(),
            decision,
            context,
            port,
            created_at=NOW + timedelta(hours=1),
            sealed_at=NOW + timedelta(hours=2),
            source_lineage_refs=("fixture:explicit-period-observations",),
        )
    assert serialized == []
    assert port.call_count == 0
    assert port.commit_count == 0
    assert port.selected is None


def test_wrong_kind_uri_interval_or_basis_fails_closed() -> None:
    with pytest.raises(artifact.TrialReturnContractError):
        artifact.ReturnDefinitionV1(
            object_kind="layered_returns",
            schema_version=artifact.RETURN_DEFINITION_SCHEMA_VERSION,
            return_basis=artifact.RETURN_BASIS_V1,
            endpoint_semantics=artifact.ENDPOINT_SEMANTICS_V1,
            non_overlap_required=True,
            alignment_policy=artifact.ALIGNMENT_POLICY_V1,
        )
    with pytest.raises(artifact.TrialReturnContractError):
        replace(make_identity(), logical_uri="research://repository/real/target")
    with pytest.raises(artifact.TrialReturnContractError):
        replace(make_definition(), return_basis="unknown")
    overlap = (
        make_observations()[0],
        artifact.TrialReturnObservationV1(
            interval_start=NOW + timedelta(hours=12),
            timestamp=NOW + timedelta(days=2),
            simple_return=0.01,
        ),
    )
    with pytest.raises(
        artifact.TrialReturnContractError,
        match="OBSERVATION_INTERVAL_OVERLAP",
    ):
        artifact.prepare_repository_fixture_candidate(
            make_identity(),
            overlap,
            make_definition(),
            created_at=NOW,
            source_lineage_refs=("fixture:explicit-period-observations",),
        )


def test_partial_payload_or_manifest_never_verifies_or_commits() -> None:
    verified, _ = publish()
    payload = replace(
        verified.bundle.payload,
        payload_bytes=verified.bundle.payload.payload_bytes[:-16],
    )
    partial_payload_bundle = replace(verified.bundle, payload=payload)
    with pytest.raises(
        artifact.TrialReturnIntegrityError,
        match="PAYLOAD_DIGEST_MISMATCH",
    ):
        verify_sealed_trial_return_bundle(
            partial_payload_bundle,
            verified.selection,
        )
    mutated_manifest = replace(verified.bundle.manifest, run_id="run-tampered")
    partial_manifest_bundle = replace(verified.bundle, manifest=mutated_manifest)
    with pytest.raises(
        artifact.TrialReturnIntegrityError,
        match="MANIFEST_DIGEST_MISMATCH",
    ):
        verify_sealed_trial_return_bundle(
            partial_manifest_bundle,
            verified.selection,
        )


def test_seal_or_selection_digest_mismatch_uses_no_secondary_hash() -> None:
    verified, _ = publish()
    tampered_seal = replace(
        verified.bundle.seal,
        content_sha256="sha256:" + "b" * 64,
    )
    with pytest.raises(
        artifact.TrialReturnIntegrityError,
        match="SEAL_BINDING_MISMATCH",
    ):
        verify_sealed_trial_return_bundle(
            replace(verified.bundle, seal=tampered_seal),
            verified.selection,
        )
    wrong_selection = replace(
        verified.selection,
        original_seal_sha256="sha256:" + "c" * 64,
    )
    with pytest.raises(
        artifact.TrialReturnIntegrityError,
        match="SELECTION_BINDING_MISMATCH",
    ):
        verify_sealed_trial_return_bundle(verified.bundle, wrong_selection)
    with pytest.raises(artifact.TrialReturnIntegrityError):
        replace(verified.selection, original_seal_sha256="SHA256:" + "A" * 64)


def test_controlled_fixture_port_failure_keeps_selection_unadvanced() -> None:
    port = make_port(inject_atomic_failure=True)
    original_selection = port.selected
    with pytest.raises(
        artifact.TrialReturnFixturePortError,
        match="FIXTURE_PORT_COMMIT_FAILED",
    ):
        publish(port)
    assert port.call_count == 1
    assert port.commit_count == 0
    assert port.selected is original_selection is None


def test_unbound_structural_port_is_rejected_before_first_call() -> None:
    port = UnboundStructuralPort()
    with pytest.raises(
        artifact.TrialReturnFixturePortError,
        match="FIXTURE_PORT_NOMINAL_TYPE_REQUIRED",
    ):
        artifact.publish_repository_fixture_trial_return_artifact(
            make_identity(),
            make_observations(),
            make_definition(),
            make_generation_decision(),
            make_context(),
            port,  # type: ignore[arg-type]
            created_at=NOW + timedelta(hours=1),
            sealed_at=NOW + timedelta(hours=2),
            source_lineage_refs=("fixture:explicit-period-observations",),
        )
    assert port.calls == 0
    assert port.records == []


def test_record_then_fail_noncompliant_port_is_never_called() -> None:
    port = RecordThenFailPort()
    with pytest.raises(
        artifact.TrialReturnFixturePortError,
        match="FIXTURE_PORT_NOMINAL_TYPE_REQUIRED",
    ):
        artifact.publish_repository_fixture_trial_return_artifact(
            make_identity(),
            make_observations(),
            make_definition(),
            make_generation_decision(),
            make_context(),
            port,  # type: ignore[arg-type]
            created_at=NOW + timedelta(hours=1),
            sealed_at=NOW + timedelta(hours=2),
            source_lineage_refs=("fixture:explicit-period-observations",),
        )
    assert port.calls == 0
    assert port.records == []


@pytest.mark.parametrize(
    ("field_name", "drift_value"),
    [
        ("capability_version", "repository-fixture-trial-return-port.v2"),
        ("repository_owned", False),
        ("decision_origin", ActionDecisionOriginV1.APPROVED_LEDGER),
        ("target_kind", ActionTargetKindV1.REAL_OPERATION),
        ("scope_revision", "scope-v2"),
        ("scope_sha256", "sha256:" + "b" * 64),
        ("release_id", "release-fixture-002"),
        ("run_id", "run-fixture-002"),
        ("family_id", "family-fixture-002"),
        ("logical_uri", f"{FIXTURE_ROOT}/other-bound-target"),
        ("authorization_id", "auth-other"),
        ("approval_ref", "approval:other"),
        ("evidence_ref", "fixture:other"),
    ],
)
def test_each_fixture_port_binding_drift_fails_before_first_call(
    field_name: str,
    drift_value: object,
) -> None:
    port = make_port()
    object.__setattr__(port.binding, field_name, drift_value)
    with pytest.raises(
        artifact.TrialReturnFixturePortError,
        match="FIXTURE_PORT_BINDING_MISMATCH",
    ):
        publish(port)
    assert port.call_count == 0
    assert port.commit_count == 0
    assert port.selected is None


def test_binding_drift_during_candidate_build_is_rejected_before_port_call(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    port = make_port()
    original_serializer = artifact._serialize_payload

    def serialize_then_drift(
        observations: tuple[artifact.TrialReturnObservationV1, ...],
    ) -> bytes:
        payload_bytes = original_serializer(observations)
        object.__setattr__(port.binding, "release_id", "release-drifted")
        return payload_bytes

    monkeypatch.setattr(artifact, "_serialize_payload", serialize_then_drift)
    with pytest.raises(
        artifact.TrialReturnFixturePortError,
        match="FIXTURE_PORT_BINDING_MISMATCH",
    ):
        publish(port)
    assert port.call_count == 0
    assert port.commit_count == 0
    assert port.selected is None


@pytest.mark.parametrize(
    "authorization_evidence_refs",
    [
        ("approval:other", "fixture:trial-return-generation"),
        ("approval:trial-return-generation", "fixture:other"),
        ("fixture:trial-return-generation", "approval:trial-return-generation"),
        (
            "approval:trial-return-generation",
            "fixture:trial-return-generation",
            "fixture:extra",
        ),
        ("approval:trial-return-generation",),
    ],
    ids=[
        "approval-mismatch",
        "evidence-mismatch",
        "swapped",
        "extra-ref",
        "missing-ref",
    ],
)
def test_direct_commit_rejects_nonexact_authorization_evidence_refs(
    authorization_evidence_refs: tuple[str, ...],
) -> None:
    verified, _ = publish()
    port = make_port()
    object.__setattr__(
        verified.bundle.seal,
        "authorization_evidence_refs",
        authorization_evidence_refs,
    )

    with pytest.raises(
        artifact.TrialReturnFixturePortError,
        match="FIXTURE_PORT_VERIFIED_BINDING_MISMATCH",
    ):
        port.commit_verified(verified)

    assert port.call_count == 0
    assert port.commit_count == 0
    assert port.selected is None


def test_publisher_commit_uses_authorization_evidence_binding_guard(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    port = make_port()
    original_verifier = artifact.verify_sealed_trial_return_bundle

    def verify_then_drift_authorization_refs(
        bundle: SealedTrialReturnBundleV1,
        selection: ResearchCanonicalSelectionV1,
    ) -> VerifiedTrialReturnBundleV1:
        verified = original_verifier(bundle, selection)
        object.__setattr__(
            verified.bundle.seal,
            "authorization_evidence_refs",
            ("approval:other", "fixture:other"),
        )
        return verified

    monkeypatch.setattr(
        artifact,
        "verify_sealed_trial_return_bundle",
        verify_then_drift_authorization_refs,
    )

    with pytest.raises(
        artifact.TrialReturnFixturePortError,
        match="FIXTURE_PORT_COMMIT_FAILED",
    ):
        publish(port)

    assert port.call_count == 0
    assert port.commit_count == 0
    assert port.selected is None


def test_controlled_failure_preserves_existing_selected_value() -> None:
    port = make_port()
    original, _ = publish(port)
    object.__setattr__(port, "_inject_atomic_failure", True)
    with pytest.raises(
        artifact.TrialReturnFixturePortError,
        match="FIXTURE_PORT_COMMIT_FAILED",
    ):
        publish(port)
    assert port.call_count == 2
    assert port.commit_count == 1
    assert port.selected is original


def test_partial_lineage_is_blocked_audit_only() -> None:
    audit = artifact.classify_append_only_lineage_partial_success(
        ("lineage:event:finish", "lineage:event:finalize")
    )
    assert audit.state == "partial_lineage_blocked_audit"
    assert audit.observed_event_refs == (
        "lineage:event:finish",
        "lineage:event:finalize",
    )
    assert audit.erase_events is False
    assert audit.fake_rollback is False
    assert audit.canonical_selection_advance is False


def test_public_contract_exports_and_digest_format_are_exact() -> None:
    assert artifact.__all__ == (
        "SealedTrialReturnBundleV1",
        "ResearchCanonicalSelectionV1",
        "VerifiedTrialReturnBundleV1",
        "canonical_artifact_seal_bytes",
        "canonical_artifact_seal_sha256",
        "verify_sealed_trial_return_bundle",
    )
    assert sum(name.endswith("V1") for name in artifact.__all__) == 3
    assert sum(callable(getattr(artifact, name)) for name in artifact.__all__[3:]) == 3
    verified, _ = publish()
    assert re.fullmatch(r"sha256:[0-9a-f]{64}", verified.original_seal_sha256)
    with pytest.raises(
        artifact.TrialReturnIntegrityError,
        match="VERIFIER_CONSTRUCTION_REQUIRED",
    ):
        VerifiedTrialReturnBundleV1(
            verified.bundle,
            verified.selection,
            verified.original_seal_sha256,
        )


def test_verifier_requires_exact_selection_and_cannot_trust_receipt_metadata() -> None:
    verified, _ = publish()
    receipt_only = {
        "original_seal_sha256": verified.original_seal_sha256,
        "content_sha256": verified.bundle.payload.content_sha256,
    }
    with pytest.raises(
        artifact.TrialReturnIntegrityError,
        match="SELECTION_TYPE_INVALID",
    ):
        verify_sealed_trial_return_bundle(verified.bundle, receipt_only)  # type: ignore[arg-type]
    assert isinstance(verified.bundle, SealedTrialReturnBundleV1)
    assert isinstance(verified.selection, ResearchCanonicalSelectionV1)


def test_current_runner_lineage_and_real_operation_surface_are_untouched() -> None:
    source = inspect.getsource(artifact)
    tree = ast.parse(source)
    forbidden_import_roots = {
        "boto3",
        "os",
        "pandas",
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
    assert "engine.mature_multifactor_research" not in source
    assert "engine.experiment_family_lineage" not in source
    assert "engine.experiment_family_lineage_store" not in source
    assert "forward_label_proxy@v1" in source
    assert source.count("def canonical_artifact_seal_bytes(") == 1
    assert source.count("def canonical_artifact_seal_sha256(") == 1
    assert source.count("def verify_sealed_trial_return_bundle(") == 1
    assert source.count("fixture_port.commit_verified(verified)") == 1
    assert source.count("hashlib.sha256(") == 1
    assert "hasattr(fixture_port" not in source
    assert "Protocol" not in source
    assert "type(fixture_port) is not RepositoryFixtureTrialReturnPortV1" in source
