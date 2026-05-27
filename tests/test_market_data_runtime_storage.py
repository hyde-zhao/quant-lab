from datetime import datetime, timezone

import pytest

from market_data.connectors.akshare import AkShareAdapter
from market_data.connectors.fake import FakeConnector
from market_data.connectors.protocol import AdapterConfig, ConnectorRequest
from market_data.connectors.tickflow import TickFlowAdapter
from market_data.connectors.tushare import TushareAdapter
from market_data.lake_layout import LakeLayout
from market_data.runtime import RuntimeContext, RuntimePolicy, execute_batches
from market_data.storage import (
    ManifestCorruptionError,
    ManifestWriter,
    StorageWriteError,
    compute_idempotency_key,
    compute_params_hash,
    load_manifest_index,
    read_manifest_records,
)


def fixed_clock():
    return datetime(2026, 5, 17, 5, 0, tzinfo=timezone.utc)


def batch(batch_id="b1", run_id="run-1", params=None):
    params = params or {
        "symbols": ["000001.SZ", "000002.SZ"],
        "start_date": "2026-01-02",
        "end_date": "2026-01-03",
        "seed": 7,
    }
    return ConnectorRequest(
        source="fake",
        interface="prices.daily",
        params=params,
        run_id=run_id,
        batch_id=batch_id,
    )


def test_fake_connector_is_deterministic_and_carries_pit_fields():
    request = batch()
    first = FakeConnector(seed=7).fetch(request)
    second = FakeConnector(seed=7).fetch(request)
    assert not hasattr(first, "error_type")
    assert first.rows == second.rows
    assert first.rows[0]["source_run_id"] == "run-1"
    assert first.rows[0]["adjustment_policy"] == "none"
    assert first.rows[0]["available_at"].endswith("16:00:00+08:00")


def test_real_adapters_fail_fast_without_network(monkeypatch):
    def deny_connect(*args, **kwargs):
        raise AssertionError("network must not be used")

    monkeypatch.setattr("socket.socket.connect", deny_connect)
    request = ConnectorRequest(
        source="akshare",
        interface="prices.daily",
        params={},
        run_id="run-1",
        batch_id="b1",
    )
    assert AkShareAdapter().fetch(request).error_type == "source_disabled"

    tushare_request = ConnectorRequest(
        source="tushare",
        interface="prices.daily",
        params={},
        run_id="run-1",
        batch_id="b1",
    )
    tushare = TushareAdapter(
        AdapterConfig(
            source="tushare",
            enabled=True,
            allow_interfaces=("prices.daily",),
            credential_env_vars=("TUSHARE_TOKEN",),
        )
    )
    assert tushare.fetch(tushare_request).error_type == "missing_credential"

    tickflow_request = ConnectorRequest(
        source="tickflow",
        interface="prices.daily",
        params={},
        run_id="run-1",
        batch_id="b1",
    )
    assert TickFlowAdapter().fetch(tickflow_request).error_type == "source_unresolved"


def test_execute_success_writes_raw_and_manifest(tmp_path):
    layout = LakeLayout(tmp_path)
    result = execute_batches(
        [batch()],
        FakeConnector(seed=7),
        layout,
        RuntimePolicy(),
        context=RuntimeContext("run-1"),
        clock=fixed_clock,
    )
    assert result[0].status == "success"
    raw_path = tmp_path / result[0].raw_path
    assert raw_path.exists()
    manifest = read_manifest_records(layout)
    assert len(manifest) == 1
    record = manifest[0]
    assert record["run_id"] == "run-1"
    assert record["raw_checksum"]
    assert record["raw_row_count"] == 4
    assert record["canonical_path"] is None
    assert record["idempotency_key"] == result[0].idempotency_key


def test_retry_success_and_backoff_are_bounded(tmp_path):
    sleeps = []
    result = execute_batches(
        [batch()],
        FakeConnector(seed=7, failure_plan={"b1": ["retryable_error", None]}),
        LakeLayout(tmp_path),
        RuntimePolicy(max_retries=2, backoff_base_seconds=10, backoff_max_seconds=5),
        context=RuntimeContext("run-1"),
        clock=fixed_clock,
        sleeper=sleeps.append,
        jitter=lambda: 0,
    )
    assert result[0].status == "success"
    assert result[0].attempts == 2
    assert sleeps == [5]


def test_max_retries_zero_calls_once(tmp_path):
    result = execute_batches(
        [batch()],
        FakeConnector(seed=7, failure_plan={"b1": "retryable_error"}),
        LakeLayout(tmp_path),
        RuntimePolicy(max_retries=0, backoff_base_seconds=1),
        context=RuntimeContext("run-1"),
        clock=fixed_clock,
    )
    assert result[0].status == "failed"
    assert result[0].attempts == 1


def test_non_retryable_does_not_retry(tmp_path):
    result = execute_batches(
        [batch()],
        FakeConnector(seed=7, failure_plan={"b1": "non_retryable_error"}),
        LakeLayout(tmp_path),
        RuntimePolicy(max_retries=3),
        context=RuntimeContext("run-1"),
        clock=fixed_clock,
    )
    assert result[0].status == "failed"
    assert result[0].attempts == 1


def test_throttle_zero_does_not_sleep(tmp_path):
    sleeps = []
    execute_batches(
        [batch("b1"), batch("b2")],
        FakeConnector(seed=7),
        LakeLayout(tmp_path),
        RuntimePolicy(throttle_seconds=0),
        context=RuntimeContext("run-1"),
        clock=fixed_clock,
        sleeper=sleeps.append,
    )
    assert sleeps == []


def test_circuit_threshold_and_success_reset(tmp_path):
    result = execute_batches(
        [batch("b1"), batch("b2"), batch("b3")],
        FakeConnector(seed=7, failure_plan={"b1": "non_retryable_error", "b3": "non_retryable_error"}),
        LakeLayout(tmp_path),
        RuntimePolicy(max_retries=0, circuit_breaker_failure_threshold=2),
        context=RuntimeContext("run-1"),
        clock=fixed_clock,
    )
    assert [item.status for item in result] == ["failed", "success", "failed"]


def test_circuit_open_skips_remaining_batches(tmp_path):
    result = execute_batches(
        [batch("b1"), batch("b2")],
        FakeConnector(seed=7, failure_plan={"b1": "non_retryable_error"}),
        LakeLayout(tmp_path),
        RuntimePolicy(max_retries=0, circuit_breaker_failure_threshold=1),
        context=RuntimeContext("run-1"),
        clock=fixed_clock,
    )
    assert result[0].status == "failed"
    assert result[1].status == "circuit_open"
    assert result[1].attempts == 0


def test_resume_success_skips_connector(tmp_path):
    layout = LakeLayout(tmp_path)
    execute_batches(
        [batch()],
        FakeConnector(seed=7),
        layout,
        RuntimePolicy(),
        context=RuntimeContext("run-1"),
        clock=fixed_clock,
    )

    class ExplodingConnector:
        source = "fake"

        def fetch(self, request):
            raise AssertionError("connector should not be called")

    resumed = execute_batches(
        [batch()],
        ExplodingConnector(),
        layout,
        RuntimePolicy(),
        context=RuntimeContext("run-1"),
        clock=fixed_clock,
    )
    assert resumed[0].status == "skipped"
    assert resumed[0].attempts == 0


def test_same_batch_id_different_runs_do_not_overwrite_raw(tmp_path):
    layout = LakeLayout(tmp_path)
    first = execute_batches(
        [batch(run_id="run-1")],
        FakeConnector(seed=7),
        layout,
        RuntimePolicy(),
        context=RuntimeContext("run-1"),
        clock=fixed_clock,
    )[0]
    second = execute_batches(
        [batch(run_id="run-2")],
        FakeConnector(seed=8),
        layout,
        RuntimePolicy(),
        context=RuntimeContext("run-2"),
        clock=fixed_clock,
    )[0]

    assert first.status == "success"
    assert second.status == "success"
    assert first.raw_path != second.raw_path
    assert "run_id=run-1" in str(first.raw_path)
    assert "run_id=run-2" in str(second.raw_path)
    assert (tmp_path / first.raw_path).exists()
    assert (tmp_path / second.raw_path).exists()
    assert len(load_manifest_index(layout)) == 2


def test_failed_manifest_retries_on_resume(tmp_path):
    layout = LakeLayout(tmp_path)
    execute_batches(
        [batch()],
        FakeConnector(seed=7, failure_plan={"b1": "non_retryable_error"}),
        layout,
        RuntimePolicy(max_retries=0),
        context=RuntimeContext("run-1"),
        clock=fixed_clock,
    )
    retried = execute_batches(
        [batch()],
        FakeConnector(seed=7),
        layout,
        RuntimePolicy(max_retries=0),
        context=RuntimeContext("run-1"),
        clock=fixed_clock,
    )
    assert retried[0].status == "success"
    assert len(read_manifest_records(layout)) == 2


def test_duplicate_success_manifest_fails(tmp_path):
    layout = LakeLayout(tmp_path)
    execute_batches(
        [batch()],
        FakeConnector(seed=7),
        layout,
        RuntimePolicy(),
        context=RuntimeContext("run-1"),
        clock=fixed_clock,
    )
    record = read_manifest_records(layout)[0]
    ManifestWriter().append(record, layout)
    with pytest.raises(ManifestCorruptionError):
        load_manifest_index(layout)


class FailOnceManifestWriter(ManifestWriter):
    def __init__(self):
        self.calls = 0

    def append(self, record, layout):
        self.calls += 1
        if self.calls == 1:
            raise StorageWriteError("forced manifest failure")
        return super().append(record, layout)


def test_manifest_append_failure_quarantines_orphan_raw(tmp_path):
    layout = LakeLayout(tmp_path)
    with pytest.raises(StorageWriteError):
        execute_batches(
            [batch()],
            FakeConnector(seed=7),
            layout,
            RuntimePolicy(),
            context=RuntimeContext("run-1"),
            clock=fixed_clock,
            manifest_writer=FailOnceManifestWriter(),
        )
    orphan = layout.orphan_raw_root / "run-1" / "b1.jsonl"
    assert orphan.exists()
    manifest = read_manifest_records(layout)
    assert manifest[0]["status"] == "orphan_raw"


def test_lineage_and_idempotency_key_match_manifest(tmp_path):
    layout = LakeLayout(tmp_path)
    result = execute_batches(
        [batch()],
        FakeConnector(seed=7),
        layout,
        RuntimePolicy(),
        context=RuntimeContext("run-1"),
        clock=fixed_clock,
    )[0]
    record = read_manifest_records(layout)[0]
    expected_hash = compute_params_hash(batch().params)
    assert record["params_hash"] == expected_hash
    assert result.idempotency_key == compute_idempotency_key(
        "run-1",
        "b1",
        "fake",
        "prices.daily",
        expected_hash,
    )
    raw_text = (tmp_path / record["raw_path"]).read_text(encoding="utf-8")
    assert '"source_run_id": "run-1"' in raw_text


def test_sensitive_params_are_redacted_in_manifest(tmp_path):
    params = {
        "symbols": ["000001.SZ"],
        "start_date": "2026-01-02",
        "end_date": "2026-01-02",
        "token": "plain-token",
        "cookie": "secret-value",
    }
    layout = LakeLayout(tmp_path)
    execute_batches(
        [batch(params=params)],
        FakeConnector(seed=7),
        layout,
        RuntimePolicy(),
        context=RuntimeContext("run-1"),
        clock=fixed_clock,
    )
    manifest_text = layout.manifest_path().read_text(encoding="utf-8")
    assert "plain-token" not in manifest_text
    assert "secret-value" not in manifest_text
    assert "<redacted>" in manifest_text
