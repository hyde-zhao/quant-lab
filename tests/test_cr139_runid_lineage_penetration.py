from trading.strategy_runner.evidence_index import RunEvidenceIndex


def test_run_evidence_index_carries_data_lineage_without_authorizing_runtime():
    index = RunEvidenceIndex(
        run_id="strategy-run",
        status="pass",
        passed=True,
        package_id="pkg",
        data_run_id="data-run",
        source_run_id="source-run",
        publish_run_id="publish-run",
        manifest_ref="manifest/ref.jsonl",
        lineage_checksum="sha256:lineage",
        lineage_status="available",
    )

    payload = index.to_dict()

    assert payload["data_lineage"]["data_run_id"] == "data-run"
    assert payload["data_lineage"]["source_run_id"] == "source-run"
    assert payload["qmt_allowed"] is False
    assert payload["not_authorization"] is True
