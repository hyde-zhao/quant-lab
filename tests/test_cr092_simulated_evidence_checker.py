from __future__ import annotations

import ast
from pathlib import Path

import yaml

from scripts.quality.check_simulated_evidence import check_evidence


CHECKER_PATH = Path("scripts/quality/check_simulated_evidence.py")

EVIDENCE_TEMPLATE = {
    "schema_version": "cr092-simulated-account-evidence-v1",
    "change_id": "CR-092",
    "not_authorization": True,
    "runtime_authorization_status": "not_authorized_by_template",
    "account_mode": "simulated",
    "run_id": "fixture-run",
    "evidence_source": "fixture",
    "scope": ["health", "capabilities", "query_positions_readonly"],
    "health_status": "N/A",
    "capabilities_status": "N/A",
    "query_positions_status": "N/A",
    "redaction_status": "PASS",
    "forbidden_counters": {
        "nas_access": 0,
        "credential_read": 0,
        "real_account_read": 0,
        "submit_cancel": 0,
        "simulation_live": 0,
        "provider_lake_publish": 0,
    },
    "simulated_account_summary": {"notes_redacted": "fixture only"},
}


def _write_evidence(tmp_path: Path, **overrides: object) -> Path:
    evidence = dict(EVIDENCE_TEMPLATE)
    evidence.update(overrides)
    path = tmp_path / "cr092-evidence.yaml"
    path.write_text(yaml.safe_dump(evidence, sort_keys=False), encoding="utf-8")
    return path


def test_cr092_evidence_template_passes(tmp_path: Path) -> None:
    path = _write_evidence(
        tmp_path,
        run_id="cr092-smoke-fixture",
        health_status="PASS",
        capabilities_status="PASS",
        query_positions_status="PASS",
    )

    result = check_evidence(path)

    assert result.passed is True
    assert result.errors == ()


def test_cr092_checker_rejects_real_account_marker(tmp_path: Path) -> None:
    path = _write_evidence(
        tmp_path,
        simulated_account_summary={"notes_redacted": "real_account=123456"},
    )

    result = check_evidence(path)

    assert result.passed is False
    assert any("real_account" in error for error in result.errors)


def test_cr092_checker_rejects_nonzero_forbidden_counter(tmp_path: Path) -> None:
    path = _write_evidence(
        tmp_path,
        forbidden_counters={
            "nas_access": 0,
            "credential_read": 1,
            "real_account_read": 0,
            "submit_cancel": 0,
            "simulation_live": 0,
            "provider_lake_publish": 0,
        },
    )

    result = check_evidence(path)

    assert result.passed is False
    assert "forbidden_counters.credential_read must be 0" in result.errors


def test_cr092_checker_rejects_forbidden_scope(tmp_path: Path) -> None:
    path = _write_evidence(tmp_path, scope=["health", "submit_order"])

    result = check_evidence(path)

    assert result.passed is False
    assert any("submit_order" in error for error in result.errors)


def test_cr092_checker_does_not_import_runtime_or_network_modules() -> None:
    tree = ast.parse(CHECKER_PATH.read_text(encoding="utf-8"), filename=str(CHECKER_PATH))
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module.split(".", 1)[0])

    assert not (
        imports
        & {
            "dotenv",
            "httpx",
            "requests",
            "socket",
            "subprocess",
            "trading",
            "urllib",
            "xtquant",
        }
    )
