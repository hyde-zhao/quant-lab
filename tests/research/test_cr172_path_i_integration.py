"""CR-172 S05：S01-S04 artifact 链与失败恢复集成 QAC。"""

from __future__ import annotations

from dataclasses import fields, replace
from datetime import datetime

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

import engine.research_artifact_materialization as materialization_module
from engine.path_i_governance import (
    ActionDecisionOriginV1,
    ActionTargetKindV1,
    EmpiricalRInputsV1,
    EmpiricalRStateV1,
    PathIActionKind,
    classify_empirical_r,
)
from engine.research_artifact_materialization import (
    MaterializationBlockReasonV1,
    MaterializationReceiptV1,
    MaterializationStatusV1,
)
from engine.research_artifact_replica import (
    REPLICA_REQUEST_VERSION,
    ReplicaBlockReasonV1,
    ReplicaPublishStatusV1,
    ReplicaSyncRequestV1,
    ReplicaVerificationReceiptV1,
    publish_repository_fixture_replica,
    validate_replica_preflight,
)
from engine.trial_return_artifact import (
    ALIGNMENT_POLICY_V1,
    ENDPOINT_SEMANTICS_V1,
    RETURN_BASIS_V1,
    RETURN_DEFINITION_SCHEMA_VERSION,
    ReturnDefinitionV1,
    TrialReturnContractError,
    TrialReturnIdentityV1,
    TrialReturnObservationV1,
    TrialReturnSourceKindV1,
    canonical_artifact_seal_bytes,
    canonical_artifact_seal_sha256,
    classify_append_only_lineage_partial_success,
    prepare_repository_fixture_candidate,
    verify_sealed_trial_return_bundle,
)
from tests.fixtures.cr172_path_i.path_i_fixture import (
    build_chain,
    build_source,
    load_fixture,
    materialize_again,
    parse_time,
)


def test_canonical_payload_and_seal_contract() -> None:
    chain = build_chain()
    payload = chain.verified_source.bundle.payload
    table = pq.read_table(pa.BufferReader(payload.payload_bytes))

    assert table.column_names == ["timestamp", "simple_return"]
    assert table.num_columns == 2
    assert table.num_rows == 3
    assert canonical_artifact_seal_bytes(chain.verified_source.bundle.seal)
    assert canonical_artifact_seal_sha256(chain.verified_source.bundle.seal) == (
        chain.verified_source.original_seal_sha256
    )
    assert verify_sealed_trial_return_bundle(
        chain.verified_source.bundle,
        chain.verified_source.selection,
    ) == chain.verified_source


def test_three_stage_artifact_chain_is_exact() -> None:
    chain = build_chain()
    source = chain.verified_source
    replica = chain.replica_result
    material = chain.material_result

    assert replica.status is ReplicaPublishStatusV1.VERIFIED
    assert material.status is MaterializationStatusV1.MATERIALIZED
    assert replica.receipt.original_seal_sha256 == source.original_seal_sha256
    assert replica.selection.receipt_sha256 == replica.receipt.receipt_sha256
    assert material.receipt.replica_receipt_sha256 == replica.receipt.receipt_sha256
    assert material.selection.materialization_receipt_sha256 == (
        material.receipt.receipt_sha256
    )
    assert material.handle.content_sha256 == source.bundle.payload.content_sha256
    assert chain.trial_port.call_count == 1
    assert chain.replica_port.stage_calls == 1
    assert chain.material_port.pull_calls == 1


def test_materialization_calls_s02_verifier_once(monkeypatch: pytest.MonkeyPatch) -> None:
    chain = build_chain(materialize=False)
    verifier = materialization_module.verify_sealed_trial_return_bundle
    calls = 0

    def counted_verifier(bundle: object, selection: object) -> object:
        nonlocal calls
        calls += 1
        return verifier(bundle, selection)

    monkeypatch.setattr(
        materialization_module,
        "verify_sealed_trial_return_bundle",
        counted_verifier,
    )
    result = materialize_again(chain, "verifier-once")

    assert result.status is MaterializationStatusV1.MATERIALIZED
    assert calls == 1
    assert chain.material_port.pull_calls == 1


def test_forward_label_proxy_is_rejected() -> None:
    fixture = load_fixture()
    oracle = fixture["mutations"]["forward_label_proxy"]
    identity = TrialReturnIdentityV1(**fixture["identity"])
    observations = tuple(
        TrialReturnObservationV1(
            interval_start=parse_time(item["interval_start"]),
            timestamp=parse_time(item["timestamp"]),
            simple_return=item["simple_return"],
        )
        for item in fixture["observations"]
    )
    definition = ReturnDefinitionV1(
        object_kind=TrialReturnSourceKindV1.FORWARD_LABEL_PROXY,
        schema_version=RETURN_DEFINITION_SCHEMA_VERSION,
        return_basis=RETURN_BASIS_V1,
        endpoint_semantics=ENDPOINT_SEMANTICS_V1,
        non_overlap_required=True,
        alignment_policy=ALIGNMENT_POLICY_V1,
    )

    with pytest.raises(TrialReturnContractError, match="FORWARD_LABEL_PROXY_FORBIDDEN"):
        prepare_repository_fixture_candidate(
            identity,
            observations,
            definition,
            created_at=parse_time(fixture["times"]["created_at"]),
            source_lineage_refs=tuple(fixture["source_lineage_refs"]),
        )
    empirical = classify_empirical_r(
        EmpiricalRInputsV1(
            declared_fixture_matrix=False,
            source_available=False,
            sealed_provenance_complete=False,
            alignment_complete=False,
            method_version_ref="FU-CR173-001-deferred",
            method_hash_valid=False,
            compute_decision=None,
            integrity_conflict=False,
            unapproved_repair=False,
            independently_verified=False,
        )
    )
    assert empirical.state is EmpiricalRStateV1.TYPED_UNAVAILABLE
    assert empirical.c1_computable is False
    assert empirical.positive_effective_count is False
    assert oracle == {
        "trial_return_accepted": 0,
        "empirical_r_accepted": 0,
        "effective_count_accepted": 0,
    }


def test_tampered_source_fails_closed_before_replica_write() -> None:
    chain = build_chain()
    oracle = chain.fixture["mutations"]["payload_byte_tamper"]
    source = chain.verified_source
    tampered_payload = replace(
        source.bundle.payload,
        payload_bytes=source.bundle.payload.payload_bytes + b"tamper",
    )
    tampered_bundle = replace(source.bundle, payload=tampered_payload)
    request = ReplicaSyncRequestV1(
        schema_version=REPLICA_REQUEST_VERSION,
        request_id="replica-request-cr172-s05-tamper",
        expected_release_id=source.selection.release_id,
        expected_logical_uri=source.selection.logical_uri,
        expected_content_sha256=source.selection.content_sha256,
        expected_manifest_sha256=source.selection.manifest_sha256,
        expected_source_selection_sha256=(
            chain.fixture["expected_source_selection_sha256"]
        ),
    )
    before = (
        chain.replica_port.stage_calls,
        chain.replica_port.persist_calls,
        chain.replica_port.cas_calls,
        chain.replica_port.current_selection,
    )

    result = validate_replica_preflight(
        request,
        tampered_bundle,
        source.selection,
        chain.decisions[PathIActionKind.NAS_REPLICA_SYNC],
        chain.context,
    )

    assert result.status is ReplicaPublishStatusV1.BLOCKED
    assert result.reason.value == oracle["reason"]
    assert oracle["accepted"] == 0
    assert oracle["replica_write"] == 0
    assert before == (
        chain.replica_port.stage_calls,
        chain.replica_port.persist_calls,
        chain.replica_port.cas_calls,
        chain.replica_port.current_selection,
    )


def test_partial_lineage_never_advances_selection() -> None:
    oracle = load_fixture()["mutations"]["partial_lineage"]
    audit = classify_append_only_lineage_partial_success(
        ("fixture://repository/cr172/events/producer-started",)
    )

    assert audit.state == "partial_lineage_blocked_audit"
    assert audit.erase_events is False
    assert audit.fake_rollback is False
    assert audit.canonical_selection_advance is False
    assert oracle == {
        "canonical_selection_advance": 0,
        "erase_events": 0,
        "fake_rollback": 0,
    }


def test_replica_failure_preserves_previous_selection() -> None:
    chain = build_chain()
    oracle = chain.fixture["mutations"]["replica_staging_failure"]
    previous = chain.replica_port.current_selection
    before_persist = chain.replica_port.persist_calls
    before_cas = chain.replica_port.cas_calls
    chain.replica_port.fail_stage = True
    source = chain.verified_source
    request = ReplicaSyncRequestV1(
        schema_version=REPLICA_REQUEST_VERSION,
        request_id="replica-request-cr172-s05-controlled-failure",
        expected_release_id=source.selection.release_id,
        expected_logical_uri=source.selection.logical_uri,
        expected_content_sha256=source.selection.content_sha256,
        expected_manifest_sha256=source.selection.manifest_sha256,
        expected_source_selection_sha256=(
            chain.fixture["expected_source_selection_sha256"]
        ),
    )
    decision = chain.decisions[PathIActionKind.NAS_REPLICA_SYNC]
    commit_decision = chain.commit_decisions[PathIActionKind.NAS_REPLICA_SYNC]

    result = publish_repository_fixture_replica(
        request,
        source.bundle,
        source.selection,
        decision,
        chain.context,
        commit_decision,
        chain.context,
        chain.replica_port.mapping,
        chain.replica_port,
    )

    assert result.status is ReplicaPublishStatusV1.BLOCKED
    assert result.reason.value == oracle["reason"]
    assert oracle["accepted"] == 0
    assert oracle["previous_selection_preserved"] == 1
    assert result.previous_selection == previous
    assert chain.replica_port.current_selection == previous
    assert chain.replica_port.persist_calls == before_persist
    assert chain.replica_port.cas_calls == before_cas


def test_materialization_failure_preserves_previous_selection() -> None:
    chain = build_chain()
    oracle = chain.fixture["mutations"]["materialization_pull_failure"]
    previous = chain.material_port.current_selection
    before_persist = chain.material_port.persist_calls
    before_cas = chain.material_port.cas_calls
    chain.material_port.fail_pull = True

    result = materialize_again(chain, "controlled-failure")

    assert result.status is MaterializationStatusV1.BLOCKED
    assert result.reason.value == oracle["reason"]
    assert oracle["accepted"] == 0
    assert oracle["previous_selection_preserved"] == 1
    assert result.previous_selection == previous
    assert chain.material_port.current_selection == previous
    assert chain.material_port.persist_calls == before_persist
    assert chain.material_port.cas_calls == before_cas


def test_s03_s04_keep_only_original_seal_digest() -> None:
    chain = build_chain()
    replica_fields = {item.name for item in fields(ReplicaVerificationReceiptV1)}
    material_fields = {item.name for item in fields(MaterializationReceiptV1)}

    assert "original_seal_sha256" in replica_fields
    assert "original_seal_sha256" in material_fields
    assert not {name for name in replica_fields | material_fields if "secondary" in name}
    assert chain.replica_result.receipt.original_seal_sha256 == (
        chain.material_result.receipt.original_seal_sha256
    )


def test_fixture_provenance_surface_is_minimal() -> None:
    chain = build_chain()
    source = chain.verified_source
    fixture_uri = chain.fixture["identity"]["logical_uri"]

    assert source.selection.decision_origin is ActionDecisionOriginV1.REPOSITORY_FIXTURE
    assert source.selection.target_kind is ActionTargetKindV1.REPOSITORY_FIXTURE
    assert source.selection.logical_uri == fixture_uri
    assert chain.replica_port.mapping.logical_uri == fixture_uri
    assert chain.material_port.mapping.logical_uri == fixture_uri
    all_fields = {
        item.name
        for model in (
            type(source.selection),
            type(chain.replica_result.receipt),
            type(chain.material_result.receipt),
        )
        for item in fields(model)
    }
    assert "evidence_kind" not in all_fields
