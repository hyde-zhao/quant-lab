from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

import pytest

from trading.strategy_runner import (
    RunSpec,
    RunSpecError,
    run_strategy_package,
    run_strategy_package_from_path,
)
from trading.strategy_runner.readonly_gateway import ReadonlyGatewayClient


FIXTURE_ROOT = Path(__file__).parent / "fixtures" / "cr091_strategy_runner"
PACKAGE_ROOT = FIXTURE_ROOT / "cr091_strategy_package"


def test_cr128_runner_core_runs_fixture_package_end_to_end() -> None:
    result = run_strategy_package_from_path(PACKAGE_ROOT, run_id="cr128-fixture")

    assert result.passed
    assert result.package_id == "strategy-package-cr091-fixture-0.1.0"
    assert result.adapter_status == "pass"
    assert result.evidence_status == "pass"
    assert result.target_count == 2
    assert result.order_intent_count == 2
    assert result.qmt_allowed is False
    assert result.not_authorization is True
    assert all(value == 0 for value in result.forbidden_operation_counters.values())
    payload = result.to_dict()
    assert payload["target_portfolio"]["not_authorization"] is True
    assert payload["evidence_summary"]["readonly_reconciliation_status"] == "ok"


def test_cr128_runner_core_writes_result_json(tmp_path: Path) -> None:
    output = tmp_path / "result.json"
    spec = RunSpec.from_package_root(PACKAGE_ROOT, run_id="cr128-output", output_path=output)

    result = run_strategy_package(spec)

    assert result.passed
    written = json.loads(output.read_text(encoding="utf-8"))
    assert written["schema_version"] == "cr128-run-result-v1"
    assert written["run_id"] == "cr128-output"
    assert written["passed"] is True
    assert written["not_authorization"] is True


def test_cr128_run_spec_rejects_external_authorization_flags() -> None:
    spec = RunSpec(
        package_root=PACKAGE_ROOT,
        run_id="cr128-bad-auth",
        runtime_authorized=True,
    )

    with pytest.raises(RunSpecError, match="blocked_authorization_flag_true:runtime_authorized"):
        spec.validate()


def test_cr128_run_spec_rejects_non_offline_mode() -> None:
    spec = RunSpec(package_root=PACKAGE_ROOT, run_id="cr128-live", mode="live")

    with pytest.raises(RunSpecError, match="blocked_non_offline_mode"):
        spec.validate()


def test_cr128_runner_does_not_write_output_when_spec_is_invalid(tmp_path: Path) -> None:
    output = tmp_path / "result.json"
    spec = RunSpec(
        package_root=PACKAGE_ROOT,
        run_id="cr128-invalid-output",
        output_path=output,
        runtime_authorized=True,
    )

    result = run_strategy_package(spec)

    assert result.status == "blocked"
    assert "blocked_authorization_flag_true:runtime_authorized" in result.blocked_reasons
    assert not output.exists()


def test_cr128_runner_fail_closed_for_bad_package_path() -> None:
    result = run_strategy_package_from_path(PACKAGE_ROOT / "missing", run_id="cr128-missing")

    assert result.status == "blocked"
    assert "blocked_manifest_missing" in result.blocked_reasons
    assert result.not_authorization is True
    assert result.qmt_allowed is False


def test_cr128_runner_does_not_call_runtime_transport(monkeypatch: pytest.MonkeyPatch) -> None:
    def forbidden_from_transport(*args: object, **kwargs: object) -> ReadonlyGatewayClient:
        raise AssertionError("runtime transport must not be constructed")

    monkeypatch.setattr(ReadonlyGatewayClient, "from_transport", forbidden_from_transport)

    result = run_strategy_package_from_path(PACKAGE_ROOT, run_id="cr128-no-runtime")

    assert result.passed


def test_cr128_runner_source_does_not_import_external_permission_domains() -> None:
    source = Path("trading/strategy_runner/runner.py").read_text(encoding="utf-8")
    forbidden = (
        "os.environ",
        "dotenv",
        "xtquant",
        "provider",
        "catalog_publish",
        "lake_write",
        "PackageExchange",
        "from_transport",
    )

    assert not [token for token in forbidden if token in source]


def test_cr128_checker_script_uses_runner_core_api() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "scripts/quality/check_strategy_runner_package.py",
            "--package-root",
            str(PACKAGE_ROOT),
            "--json",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    payload = json.loads(completed.stdout)
    assert payload["passed"] is True
    assert payload["adapter_status"] == "pass"
    assert payload["evidence_status"] == "pass"
    assert payload["target_count"] == 2
    assert payload["order_intent_count"] == 2
    assert payload["not_authorization"] is True
