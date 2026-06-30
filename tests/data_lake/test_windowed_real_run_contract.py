from __future__ import annotations

import json
from pathlib import Path

from market_data.cli import cmd_s09_run_gate
from market_data.contracts import DATASET_PRICES, INTERFACE_PRICES_DAILY, SOURCE_TUSHARE
from market_data.lake_layout import MarketDataPathError, ensure_s09_lake_root_allowed
from market_data.manifest import validate_s09_window_manifest_record
from market_data.runtime import DevGate, evaluate_s09_windowed_run_gate
from market_data.windowed_run import (
    S09_DEFAULT_PILOT_END,
    S09_DEFAULT_PILOT_START,
    FakeWindowProvider,
    TmpPathWindowWriter,
    build_s09_authorization,
    evaluate_s09_run_gate,
    execute_windowed_run,
    plan_windowed_run,
    resume_windowed_run,
    rollback_windowed_run,
)


def _auth_payload(tmp_path: Path, **overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "authorization_id": "CR014-S09-PILOT-20260527-001",
        "datasets": [DATASET_PRICES],
        "date_range": {
            "start_date": S09_DEFAULT_PILOT_START,
            "end_date": S09_DEFAULT_PILOT_END,
        },
        "source_interface_allowlist": [
            {"source": SOURCE_TUSHARE, "interface": INTERFACE_PRICES_DAILY}
        ],
        "lake_root": str(tmp_path),
        "window_policy": {"policy_type": "month", "stop_on_error": False},
        "resume_policy": {
            "skip_success": True,
            "retry_failed": True,
            "conflict_strategy": "fail_closed",
        },
        "rollback_policy": {"mode": "preview_only", "execute_authorized": False},
        "credential_source_policy": {
            "policy_type": "env",
            "env_var_names": ["TUSHARE_TOKEN"],
            "redact_values": True,
        },
        "approved_by": "unit-test",
    }
    payload.update(overrides)
    return payload


def _auth(tmp_path: Path, **overrides: object):
    result = build_s09_authorization(_auth_payload(tmp_path, **overrides))
    assert result.ok, result.to_dict()
    assert result.authorization is not None
    return result.authorization


def _fake_gate(authorization) -> object:
    gate = evaluate_s09_run_gate(
        dev_gate=DevGate(
            cp5_approved=True,
            lld_confirmed=True,
            dependencies_satisfied=True,
            file_conflict_free=True,
        ),
        authorization=authorization,
        cp5_state={
            "implementation_allowed": True,
            "real_run_authorized": False,
        },
        execution_mode="fake",
        allow_fake_provider=True,
    )
    assert gate.run_allowed, gate.to_dict()
    return gate


def _assert_forbidden_zero(counters: dict[str, int]) -> None:
    for key in (
        "provider_fetch",
        "lake_write",
        "credential_read",
        "current_pointer_changes",
        "publish_count",
        "retention_execute_count",
        "duckdb_open",
        "duckdb_write",
        "duckdb_dependency_change",
        "duckdb_files_created",
    ):
        assert counters[key] == 0


def test_unauthorized_s09_run_fails_closed_without_provider_or_lake_calls() -> None:
    provider = FakeWindowProvider()
    gate = evaluate_s09_windowed_run_gate(
        authorization={},
        dev_gate=DevGate(),
        cp5_state={"implementation_allowed": False, "real_run_authorized": False},
    )

    assert gate.run_allowed is False
    assert gate.status == "blocked"
    assert provider.call_count == 0
    assert {
        error.code for error in gate.errors
    } >= {"s09_cp5_not_approved", "authorization_required", "real_run_not_authorized"}
    _assert_forbidden_zero(gate.permission_counters)


def test_default_2026_ytd_month_window_split_is_closed_interval(tmp_path: Path) -> None:
    authorization = _auth(tmp_path)
    plan = plan_windowed_run(authorization)

    assert plan.status == "planned"
    assert [(window.start_date, window.end_date) for window in plan.windows] == [
        ("2026-01-01", "2026-01-31"),
        ("2026-02-01", "2026-02-28"),
        ("2026-03-01", "2026-03-31"),
        ("2026-04-01", "2026-04-30"),
        ("2026-05-01", "2026-05-26"),
    ]
    assert all(window.resume_token for window in plan.windows)
    _assert_forbidden_zero(plan.permission_counters)


def test_fake_provider_success_writes_raw_manifest_and_metadata_under_tmp_path(
    tmp_path: Path,
) -> None:
    authorization = _auth(
        tmp_path,
        date_range={"start_date": "2026-01-01", "end_date": "2026-01-31"},
    )
    plan = plan_windowed_run(authorization)
    provider = FakeWindowProvider()
    writer = TmpPathWindowWriter(tmp_path)
    summary = execute_windowed_run(
        plan,
        authorization,
        provider=provider,
        writer=writer,
        gate_result=_fake_gate(authorization),
    )

    assert summary.status == "succeeded"
    assert summary.succeeded_count == 1
    assert summary.failed_count == 0
    assert summary.fake_provider_calls == 1
    assert summary.raw_write_count == 1
    assert summary.manifest_write_count == 1
    assert summary.run_metadata_write_count == 1
    assert summary.current_pointer_changes == 0
    assert summary.publish_count == 0
    assert summary.retention_execute_count == 0
    assert summary.duckdb_open_count == 0
    assert summary.duckdb_write_count == 0
    _assert_forbidden_zero(summary.permission_counters)

    record = summary.records[0]
    assert record.raw_refs and Path(record.raw_refs[0]).exists()
    assert record.manifest_ref and Path(record.manifest_ref).exists()
    assert record.run_metadata_ref and Path(record.run_metadata_ref).exists()
    manifest_payload = json.loads(Path(record.manifest_ref).read_text(encoding="utf-8"))
    manifest_result = validate_s09_window_manifest_record(manifest_payload)
    assert manifest_result.passed is True
    assert manifest_result.publish_allowed is False


def test_execute_windowed_run_without_gate_fails_closed(tmp_path: Path) -> None:
    authorization = _auth(
        tmp_path,
        date_range={"start_date": "2026-01-01", "end_date": "2026-01-31"},
    )
    plan = plan_windowed_run(authorization)
    provider = FakeWindowProvider()
    writer = TmpPathWindowWriter(tmp_path)

    summary = execute_windowed_run(
        plan,
        authorization,
        provider=provider,
        writer=writer,
    )

    assert summary.status == "blocked"
    assert provider.call_count == 0
    assert writer.tmp_path_write_count == 0
    assert summary.errors[0].code == "real_run_not_authorized"
    _assert_forbidden_zero(summary.permission_counters)


def test_partial_failure_records_failed_window_without_overwriting_success(
    tmp_path: Path,
) -> None:
    authorization = _auth(
        tmp_path,
        date_range={"start_date": "2026-01-01", "end_date": "2026-02-28"},
    )
    plan = plan_windowed_run(authorization)
    failing_window = plan.windows[1].window_id
    provider = FakeWindowProvider(failures={failing_window: "schema mismatch"})
    writer = TmpPathWindowWriter(tmp_path)
    summary = execute_windowed_run(
        plan,
        authorization,
        provider=provider,
        writer=writer,
        gate_result=_fake_gate(authorization),
    )

    assert summary.status == "partial_failed"
    assert summary.succeeded_count == 1
    assert summary.failed_count == 1
    success = [record for record in summary.records if record.status == "succeeded"][0]
    failed = [record for record in summary.records if record.status == "failed"][0]
    assert Path(success.raw_refs[0]).exists()
    assert failed.window_id == failing_window
    assert failed.error_code == "provider_error"
    assert failed.raw_refs == ()
    assert failed.resume_token
    assert summary.publish_count == 0
    assert summary.retention_execute_count == 0
    _assert_forbidden_zero(summary.permission_counters)


def test_resume_conflict_fails_closed_when_request_fingerprint_changes(
    tmp_path: Path,
) -> None:
    authorization = _auth(
        tmp_path,
        date_range={"start_date": "2026-01-01", "end_date": "2026-01-31"},
    )
    plan = plan_windowed_run(authorization)
    summary = execute_windowed_run(
        plan,
        authorization,
        provider=FakeWindowProvider(),
        writer=TmpPathWindowWriter(tmp_path),
        gate_result=_fake_gate(authorization),
    )
    changed_authorization = _auth(
        tmp_path,
        date_range={"start_date": "2026-01-01", "end_date": "2026-01-31"},
        source_interface_allowlist=[
            {"source": SOURCE_TUSHARE, "interface": "tushare.daily.changed"}
        ],
    )

    resume = resume_windowed_run(summary, changed_authorization)

    assert resume.status == "resume_conflict"
    assert resume.run_allowed is False
    assert resume.windows_to_run == ()
    assert resume.conflicts
    assert resume.errors[0].code == "resume_conflict"
    _assert_forbidden_zero(resume.permission_counters)


def test_rollback_preview_never_executes_delete_archive_or_publish(tmp_path: Path) -> None:
    authorization = _auth(
        tmp_path,
        date_range={"start_date": "2026-01-01", "end_date": "2026-01-31"},
    )
    plan = plan_windowed_run(authorization)
    summary = execute_windowed_run(
        plan,
        authorization,
        provider=FakeWindowProvider(),
        writer=TmpPathWindowWriter(tmp_path),
        gate_result=_fake_gate(authorization),
    )
    raw_path = Path(summary.records[0].raw_refs[0])

    preview = rollback_windowed_run(summary)

    assert preview.status == "preview"
    assert preview.actions
    assert all(action["execute"] is False for action in preview.actions)
    assert raw_path.exists()
    _assert_forbidden_zero(preview.permission_counters)


def test_s09_lake_root_rejects_current_repo_old_data_and_reports_paths() -> None:
    for forbidden_path in (Path.cwd() / "data" / "market_data", Path.cwd() / "reports"):
        try:
            ensure_s09_lake_root_allowed(forbidden_path)
        except MarketDataPathError as exc:
            assert "旧 repo data/** 或 reports/**" in str(exc)
        else:  # pragma: no cover - 失败路径为了保持断言信息直接
            raise AssertionError(f"expected S09 lake root rejection: {forbidden_path}")


def test_cli_s09_run_gate_is_offline_safe_and_does_not_authorize_real_run(
    tmp_path: Path,
) -> None:
    class Args:
        authorization_id = "CR014-S09-PILOT-20260527-001"
        approved_by = "unit-test"
        datasets = DATASET_PRICES
        dataset = DATASET_PRICES
        start_date = "2026-01-01"
        end_date = "2026-05-26"
        source = SOURCE_TUSHARE
        interface = INTERFACE_PRICES_DAILY
        lake_root = str(tmp_path)
        window_policy = "month"
        trading_day_chunk_size = 20
        credential_envs = "TUSHARE_TOKEN"
        cp5_approved = True
        lld_confirmed = True
        dependencies_satisfied = True
        file_conflict_free = True
        implementation_allowed = True
        stop_on_error = False

    payload = cmd_s09_run_gate(Args())

    assert payload["command"] == "s09-run-gate"
    assert payload["real_run_authorized"] is False
    assert payload["run_gate"]["run_allowed"] is False
    assert {
        error["code"] for error in payload["run_gate"]["errors"]
    } == {"real_run_not_authorized"}
    _assert_forbidden_zero(payload["run_gate"]["permission_counters"])


def test_no_publish_retention_or_duckdb_side_effect_files_are_created(tmp_path: Path) -> None:
    authorization = _auth(
        tmp_path,
        date_range={"start_date": "2026-01-01", "end_date": "2026-01-31"},
    )
    summary = execute_windowed_run(
        plan_windowed_run(authorization),
        authorization,
        provider=FakeWindowProvider(),
        writer=TmpPathWindowWriter(tmp_path),
        gate_result=_fake_gate(authorization),
    )

    assert summary.current_pointer_changes == 0
    assert summary.publish_count == 0
    assert summary.retention_execute_count == 0
    assert summary.duckdb_open_count == 0
    assert summary.duckdb_write_count == 0
    assert list(tmp_path.rglob("*.duckdb")) == []
    assert list((tmp_path / "catalog" / "current").glob("**/*")) == []
