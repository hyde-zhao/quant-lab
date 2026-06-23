from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

import pytest
import yaml

from trading.strategy_runner import RunSpec, RunSpecError, run_strategy_package_from_spec_file


FIXTURE_ROOT = Path(__file__).parent / "fixtures" / "cr091_strategy_runner"
PACKAGE_ROOT = FIXTURE_ROOT / "cr091_strategy_package"


def test_cr133_run_spec_loads_yaml_file_and_runs_package(tmp_path: Path) -> None:
    spec_path = tmp_path / "run-spec.yaml"
    output_path = tmp_path / "out" / "runner-result.json"
    spec_path.write_text(
        yaml.safe_dump(
            {
                "schema_version": "cr128-run-spec-v1",
                "package_root": PACKAGE_ROOT.resolve().as_posix(),
                "run_id": "cr133-yaml",
                "output_path": "out/runner-result.json",
                "mode": "offline",
                "include_fake_readonly": True,
                "not_authorization": True,
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    result = run_strategy_package_from_spec_file(spec_path)

    assert result.passed
    assert result.run_id == "cr133-yaml"
    written = json.loads(output_path.read_text(encoding="utf-8"))
    assert written["run_id"] == "cr133-yaml"
    assert written["passed"] is True
    assert written["qmt_allowed"] is False


def test_cr133_run_spec_loads_json_file() -> None:
    spec = RunSpec.from_mapping(
        {
            "schema_version": "cr128-run-spec-v1",
            "package_root": PACKAGE_ROOT.as_posix(),
            "run_id": "cr133-json",
            "mode": "offline",
            "not_authorization": True,
        }
    )

    assert spec.run_id == "cr133-json"
    assert spec.package_root == PACKAGE_ROOT
    assert spec.qmt_allowed is False


def test_cr133_run_spec_rejects_unknown_fields() -> None:
    with pytest.raises(RunSpecError, match="blocked_run_spec_unknown_fields:provider_token"):
        RunSpec.from_mapping(
            {
                "schema_version": "cr128-run-spec-v1",
                "package_root": PACKAGE_ROOT.as_posix(),
                "run_id": "cr133-bad",
                "provider_token": "forbidden",
            }
        )


def test_cr133_run_spec_rejects_authorization_true() -> None:
    with pytest.raises(RunSpecError, match="blocked_authorization_flag_true:trade_write_authorized"):
        RunSpec.from_mapping(
            {
                "schema_version": "cr128-run-spec-v1",
                "package_root": PACKAGE_ROOT.as_posix(),
                "run_id": "cr133-bad-auth",
                "trade_write_authorized": True,
            }
        )


def test_cr133_cli_runs_yaml_spec_json(tmp_path: Path) -> None:
    spec_path = tmp_path / "run-spec.yaml"
    spec_path.write_text(
        yaml.safe_dump(
            {
                "schema_version": "cr128-run-spec-v1",
                "package_root": PACKAGE_ROOT.resolve().as_posix(),
                "run_id": "cr133-cli",
                "mode": "offline",
                "not_authorization": True,
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "trading.strategy_runner.cli",
            "--spec",
            str(spec_path),
            "--json",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    payload = json.loads(completed.stdout)
    assert payload["schema_version"] == "cr128-run-result-v1"
    assert payload["run_id"] == "cr133-cli"
    assert payload["passed"] is True
    assert payload["not_authorization"] is True


def test_cr133_cli_blocks_invalid_spec(tmp_path: Path) -> None:
    spec_path = tmp_path / "run-spec.json"
    spec_path.write_text(
        json.dumps(
            {
                "schema_version": "cr128-run-spec-v1",
                "package_root": PACKAGE_ROOT.resolve().as_posix(),
                "run_id": "cr133-cli-blocked",
                "runtime_authorized": True,
            }
        ),
        encoding="utf-8",
    )

    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "trading.strategy_runner.cli",
            "--spec",
            str(spec_path),
            "--json",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    payload = json.loads(completed.stdout)
    assert completed.returncode == 1
    assert payload["status"] == "blocked"
    assert "blocked_authorization_flag_true:runtime_authorized" in payload["blocked_reasons"]
    assert payload["qmt_allowed"] is False
