from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

import yaml

from trading.strategy_runner import RunSpec, run_strategy_package, run_strategy_package_from_path


FIXTURE_ROOT = Path(__file__).resolve().parents[1] / "fixtures" / "cr091_strategy_runner"
PACKAGE_ROOT = FIXTURE_ROOT / "cr091_strategy_package"


def test_cr134_run_spec_accepts_evidence_index_output_path(tmp_path: Path) -> None:
    spec = RunSpec.from_mapping(
        {
            "schema_version": "cr128-run-spec-v1",
            "package_root": PACKAGE_ROOT.resolve().as_posix(),
            "run_id": "cr134-spec",
            "output_path": "out/result.json",
            "evidence_index_output_path": "out/evidence-index.json",
            "mode": "offline",
            "not_authorization": True,
        },
        base_dir=tmp_path,
    )

    assert spec.output_path == tmp_path / "out" / "result.json"
    assert spec.evidence_index_output_path == tmp_path / "out" / "evidence-index.json"
    payload = spec.to_dict()
    assert payload["evidence_index_output_path"].endswith("out/evidence-index.json")


def test_cr134_runner_writes_lightweight_evidence_index_for_pass_run(tmp_path: Path) -> None:
    result_output = tmp_path / "runner-result.json"
    index_output = tmp_path / "evidence" / "runner-evidence.index.json"

    result = run_strategy_package_from_path(
        PACKAGE_ROOT,
        run_id="cr134-pass-index",
        output_path=result_output,
        evidence_index_output_path=index_output,
    )

    assert result.passed
    payload = json.loads(index_output.read_text(encoding="utf-8"))
    assert payload["schema_version"] == "cr134-runner-evidence-index-v1"
    assert payload["run_id"] == "cr134-pass-index"
    assert payload["passed"] is True
    assert payload["run_result_ref"] == result_output.as_posix()
    assert payload["evidence_summary_ref"] == "RunResult.evidence_summary"
    assert payload["evidence_summary_excerpt"]["status"] == "pass"
    assert payload["not_authorization"] is True
    assert payload["qmt_allowed"] is False
    assert all(value == 0 for value in payload["forbidden_operation_counters"].values())
    assert "target_portfolio" not in payload
    assert "order_intents" not in json.dumps(payload, ensure_ascii=False)


def test_cr134_runner_does_not_write_evidence_index_for_blocked_run(tmp_path: Path) -> None:
    result_output = tmp_path / "runner-result.json"
    index_output = tmp_path / "runner-evidence.index.json"
    spec = RunSpec(
        package_root=PACKAGE_ROOT,
        run_id="cr134-blocked-index",
        output_path=result_output,
        evidence_index_output_path=index_output,
        runtime_authorized=True,
    )

    result = run_strategy_package(spec)

    assert result.status == "blocked"
    assert not result_output.exists()
    assert not index_output.exists()


def test_cr134_cli_writes_evidence_index_output(tmp_path: Path) -> None:
    spec_path = tmp_path / "run-spec.yaml"
    result_output = tmp_path / "result.json"
    index_output = tmp_path / "cli-evidence.index.json"
    spec_path.write_text(
        yaml.safe_dump(
            {
                "schema_version": "cr128-run-spec-v1",
                "package_root": PACKAGE_ROOT.resolve().as_posix(),
                "run_id": "cr134-cli-index",
                "output_path": result_output.as_posix(),
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
            "--evidence-index-output",
            str(index_output),
            "--json",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    cli_payload = json.loads(completed.stdout)
    index_payload = json.loads(index_output.read_text(encoding="utf-8"))
    assert cli_payload["passed"] is True
    assert index_payload["run_id"] == "cr134-cli-index"
    assert index_payload["run_result_ref"] == result_output.as_posix()
    assert index_payload["not_authorization"] is True
    assert index_payload["qmt_allowed"] is False


def test_cr134_cli_does_not_write_index_for_blocked_spec(tmp_path: Path) -> None:
    spec_path = tmp_path / "run-spec.yaml"
    index_output = tmp_path / "blocked-evidence.index.json"
    spec_path.write_text(
        yaml.safe_dump(
            {
                "schema_version": "cr128-run-spec-v1",
                "package_root": PACKAGE_ROOT.resolve().as_posix(),
                "run_id": "cr134-cli-blocked-index",
                "runtime_authorized": True,
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
            "--evidence-index-output",
            str(index_output),
            "--json",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    payload = json.loads(completed.stdout)
    assert completed.returncode == 1
    assert payload["status"] == "blocked"
    assert not index_output.exists()
