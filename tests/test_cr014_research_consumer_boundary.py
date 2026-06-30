import inspect

import pandas as pd

from engine.research_dataset import (
    DuckDbEvidenceRef,
    ResearchConsumerRequest,
    assert_research_consumer_forbidden_operations,
    attach_unsupported_claims_to_research_metadata,
    build_research_dataset_from_published_truth,
    consume_duckdb_audit_evidence_ref,
)
from engine.research_reporting import (
    attach_cr014_claim_boundary_metadata,
    emit_docs_runbook_refresh_contract,
)
from market_data.claims import (
    CLAIM_FULL_A_SINCE_INCEPTION_PRODUCTION,
    ClaimBoundarySummary,
    resolve_microstructure_claim_boundary,
)
from market_data.contracts import (
    CR014_CLAIM_FULL_A_SINCE_INCEPTION,
    CR014_FORBIDDEN_OPERATION_COUNTERS,
)


def _published_truth() -> dict[str, object]:
    return {
        "status": "published_current_truth",
        "catalog_pointer": {
            "dataset": "prices",
            "published": True,
            "published_path": "published://prices/current",
            "published_at": "2026-05-27T00:00:00+08:00",
            "as_of_trade_date": "2026-05-26",
            "universe_scope": "all_a_share",
        },
        "evidence_path": "catalog://prices/current",
    }


def _allowed_s05_summary() -> ClaimBoundarySummary:
    return ClaimBoundarySummary(
        allowed_claims=(
            {
                "claim": CR014_CLAIM_FULL_A_SINCE_INCEPTION,
                "claim_scope": CLAIM_FULL_A_SINCE_INCEPTION_PRODUCTION,
            },
            {"claim": "framework_validation", "claim_scope": "research"},
        ),
        blocked_claims=(),
        required_missing=(),
        permission_counters=dict(CR014_FORBIDDEN_OPERATION_COUNTERS),
        full_a_allowed_claim_count=1,
        status="allowed",
    )


def _blocked_s05_summary() -> ClaimBoundarySummary:
    row = {
        "claim": CR014_CLAIM_FULL_A_SINCE_INCEPTION,
        "claim_scope": CLAIM_FULL_A_SINCE_INCEPTION_PRODUCTION,
        "dataset": "prices",
        "gap_code": "candidate_unpublished",
        "evidence_path": "candidate://cr014-s05/prices",
        "remediation": "publish_current_truth_after_gate",
        "release_condition": "all P0 gates pass and explicit publish gate approves current pointer",
        "severity": "P0",
    }
    return ClaimBoundarySummary(
        allowed_claims=(
            {"claim": "framework_validation", "claim_scope": "research"},
            {"claim": "real_vwap_execution", "claim_scope": "invalid_upstream_attempt"},
        ),
        blocked_claims=(row,),
        required_missing=(
            {
                "dataset": "prices",
                "gap_code": "candidate_unpublished",
                "evidence_path": "candidate://cr014-s05/prices",
                "remediation": "publish_current_truth_after_gate",
                "release_condition": "all P0 gates pass and explicit publish gate approves current pointer",
            },
        ),
        permission_counters=dict(CR014_FORBIDDEN_OPERATION_COUNTERS),
        full_a_allowed_claim_count=0,
        status="blocked",
    )


def _consumer_request() -> ResearchConsumerRequest:
    return ResearchConsumerRequest(
        universe_scope="all_a_share",
        as_of_trade_date="2026-05-26",
        requested_claims=(CR014_CLAIM_FULL_A_SINCE_INCEPTION,),
    )


def test_consumer_gate_uses_published_truth_and_clean_reader_output_without_side_effects() -> None:
    frame = pd.DataFrame(
        {
            "trade_date": ["2026-05-26"],
            "symbol": ["000001.SZ"],
            "close": [10.0],
        }
    )

    dataset = build_research_dataset_from_published_truth(
        _consumer_request(),
        published_current_truth=_published_truth(),
        clean_reader_output={"frame": frame},
        claim_boundary_summary=_allowed_s05_summary(),
        duckdb_evidence_refs=[
            DuckDbEvidenceRef(
                run_id="duckdb-audit-1",
                evidence_path="evidence://duckdb/parity.json",
                parity_status="pass",
                audit_scope="published_current_truth",
            )
        ],
    )

    assert dataset.status == "available"
    assert dataset.gate_result.status == "pass"
    assert dataset.prices is not None
    assert dataset.prices.to_dict("records") == frame.to_dict("records")
    assert CR014_CLAIM_FULL_A_SINCE_INCEPTION in dataset.allowed_claims
    assert dataset.metadata["truth_source"] == "published_current_truth"
    assert dataset.metadata["published_current_truth_ref"]["catalog_pointer"]["published_path"] == "published://prices/current"
    assert dataset.metadata["duckdb_evidence_refs"] == [
        {
            "run_id": "duckdb-audit-1",
            "evidence_path": "evidence://duckdb/parity.json",
            "parity_status": "pass",
            "audit_scope": "published_current_truth",
        }
    ]
    for key, expected in CR014_FORBIDDEN_OPERATION_COUNTERS.items():
        assert dataset.metadata["permission_counters"][key] == expected
    assert dataset.metadata["candidate_lake_scans"] == 0
    assert dataset.metadata["duckdb_opens"] == 0
    assert dataset.metadata["docs_writes"] == 0


def test_missing_published_truth_returns_typed_required_missing_and_blocks_claims() -> None:
    dataset = build_research_dataset_from_published_truth(
        _consumer_request(),
        published_current_truth=None,
        claim_boundary_summary=_allowed_s05_summary(),
    )

    assert dataset.status == "required_missing"
    assert "published_current_truth_missing" in {issue.code for issue in dataset.issues}
    assert dataset.allowed_claims == []
    assert dataset.metadata["allowed_claims"] == []
    assert {
        item["gap_code"]
        for item in dataset.metadata["required_missing"]
    } >= {"published_current_truth_missing"}
    assert {
        item["gap_code"]
        for item in dataset.metadata["blocked_claims"]
    } >= {"published_current_truth_missing"}
    assert dataset.metadata["provider_fetches"] == 0
    assert dataset.metadata["lake_writes"] == 0
    assert dataset.metadata["credential_reads"] == 0
    assert dataset.metadata["candidate_lake_scans"] == 0


def test_candidate_unpublished_path_is_not_promoted_to_research_current_truth() -> None:
    dataset = build_research_dataset_from_published_truth(
        _consumer_request(),
        published_current_truth={
            "status": "candidate_unpublished",
            "candidate_path": "candidate://run-001/prices",
            "catalog_pointer": {"published": False, "published_path": "candidate://run-001/prices"},
        },
        claim_boundary_summary=_allowed_s05_summary(),
    )

    assert dataset.status == "required_missing"
    assert "candidate_lake_scan_attempt" in {issue.code for issue in dataset.issues}
    assert dataset.metadata["truth_source"] == "candidate_unpublished"
    assert dataset.metadata["published_current_truth_ref"] == {}
    assert dataset.metadata["allowed_claims"] == []
    assert dataset.metadata["candidate_lake_scans"] == 0


def test_duckdb_evidence_ref_is_reference_only_and_rejects_direct_access_fields() -> None:
    valid = consume_duckdb_audit_evidence_ref(
        {
            "run_id": "audit-001",
            "evidence_path": "evidence://duckdb/audit.json",
            "parity_status": "pass",
            "audit_scope": "published_current_truth",
        }
    )
    invalid = consume_duckdb_audit_evidence_ref(
        {
            "run_id": "audit-002",
            "evidence_path": "evidence://duckdb/audit.json",
            "parity_status": "pass",
            "audit_scope": "candidate_audit",
            "sql": "select * from prices",
        }
    )

    assert set(valid) == {"run_id", "evidence_path", "parity_status", "audit_scope"}
    assert invalid["error_code"] == "direct_duckdb_access_attempt"
    assert "sql" in invalid["blocked_fields"]


def test_reporting_adapter_attaches_s05_s08_claim_boundary_counters_and_docs_contract() -> None:
    boundary = resolve_microstructure_claim_boundary(s05_claim_boundary=_blocked_s05_summary())
    metadata = attach_cr014_claim_boundary_metadata(
        {"allowed_claims": ["framework_validation", "real_vwap_execution"], "blocked_claims": []},
        boundary,
        duckdb_evidence_refs=[
            {
                "run_id": "audit-003",
                "evidence_path": "evidence://duckdb/parity.json",
                "parity_status": "mismatch",
                "audit_scope": "published_current_truth",
            }
        ],
    )

    blocked_names = {item["claim"] for item in metadata["blocked_claims"]}
    required_capabilities = {item.get("capability") for item in metadata["required_missing"]}

    assert "framework_validation" in metadata["allowed_claims"]
    assert "real_vwap_execution" not in metadata["allowed_claims"]
    assert "real_vwap_execution" in blocked_names
    assert "vwap_fill_claim" in blocked_names
    assert "real_vwap_execution" in required_capabilities
    assert metadata["permission_counters"]["provider_fetch"] == 0
    assert metadata["duckdb_evidence_refs"] == [
        {
            "run_id": "audit-003",
            "evidence_path": "evidence://duckdb/parity.json",
            "parity_status": "mismatch",
            "audit_scope": "published_current_truth",
        }
    ]
    assert metadata["duckdb_evidence_policy"] == "reference_only"
    assert metadata["docs_runbook_refresh_policy"] == "metadata_only_no_docs_write"
    assert metadata["docs_runbook_refresh_contract"]["write_policy"] == "no_readme_or_docs_write_in_s07"
    assert metadata["docs_writes"] == 0


def test_docs_runbook_refresh_contract_is_structured_metadata_only() -> None:
    contract = emit_docs_runbook_refresh_contract(
        _blocked_s05_summary(),
        ops_boundary={"retention": "dry_run_default", "replay": "candidate_only"},
    )

    assert contract["contract_type"] == "cr014_docs_runbook_refresh_contract"
    assert contract["status"] == "metadata_only"
    assert contract["write_policy"] == "no_readme_or_docs_write_in_s07"
    assert "README.md" in contract["refresh_targets"]
    assert "docs/USER-MANUAL.md" in contract["refresh_targets"]
    assert contract["boundary_states"]["candidate_unpublished"] == 1
    assert contract["boundary_states"]["published_current_truth"] == "required_missing"
    assert contract["permission_counters"]["lake_write"] == 0


def test_s08_unsupported_boundary_guard_remains_compatible_with_s07_metadata() -> None:
    boundary = resolve_microstructure_claim_boundary(s05_claim_boundary=_blocked_s05_summary())
    metadata = attach_unsupported_claims_to_research_metadata(
        {
            "allowed_claims": ["framework_validation", "real_vwap_execution"],
            "blocked_claims": [],
            "required_missing": [],
            "known_limitations": [],
        },
        boundary,
    )

    blocked_names = {item["claim"] for item in metadata["blocked_claims"]}
    assert "framework_validation" in metadata["allowed_claims"]
    assert "real_vwap_execution" not in metadata["allowed_claims"]
    assert "real_vwap_execution" in blocked_names
    assert metadata["real_vwap_allowed_claim_count"] == 0
    assert metadata["vwap_fill_allowed_claim_count"] == 0
    assert metadata["microstructure_allowed_claim_count"] == 0


def test_research_consumer_forbidden_operation_guard_and_static_scan() -> None:
    guard = assert_research_consumer_forbidden_operations(
        touched_files=[
            "engine/research_dataset.py",
            "engine/research_reporting.py",
            "tests/test_cr014_research_consumer_boundary.py",
        ],
        duckdb_evidence_refs=[
            {
                "run_id": "audit-004",
                "evidence_path": "evidence://duckdb/parity.json",
                "parity_status": "pass",
                "audit_scope": "published_current_truth",
            }
        ],
    )
    forbidden_guard = assert_research_consumer_forbidden_operations(touched_files=["README.md"])
    source = "\n".join(
        inspect.getsource(func)
        for func in (
            build_research_dataset_from_published_truth,
            consume_duckdb_audit_evidence_ref,
            assert_research_consumer_forbidden_operations,
            attach_cr014_claim_boundary_metadata,
            emit_docs_runbook_refresh_contract,
        )
    )

    assert guard.passed is True
    assert forbidden_guard.passed is False
    assert "forbidden_file_touched" in forbidden_guard.error_codes
    for forbidden in (
        "read_research_inputs(",
        "read_dataset(",
        ".glob(",
        ".rglob(",
        "duckdb.connect",
        "to_parquet(",
        "to_csv(",
        "write_text(",
        "open(",
        "os.environ",
        "load_dotenv",
        "CatalogStore",
        "publish_current_pointer(",
    ):
        assert forbidden not in source
