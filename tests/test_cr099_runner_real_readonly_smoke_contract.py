from __future__ import annotations

import ast
from pathlib import Path

import yaml

from scripts.check_cr099_redacted_evidence import check_redacted_evidence, check_run_contract
from scripts.collect_cr099_runner_readonly_smoke import build_cr099_evidence


CHECKER_PATH = Path("scripts/check_cr099_redacted_evidence.py")


def _valid_contract() -> dict[str, object]:
    return {
        "schema_version": 1,
        "contract_id": "CR099-RUNNER-REAL-READONLY-SMOKE-RUN-CONTRACT",
        "cr_id": "CR-099",
        "run_id": "cr099-fixture-run",
        "authorization_ref": "user-approved-cr099-fixture",
        "authorized_by": "user",
        "authorized_at": "2026-06-19T16:13:23+08:00",
        "expires_at": "single-use",
        "gateway": {
            "host": "127.0.0.1",
            "port": 18765,
            "scheme": "http",
            "allowlist": ["health", "capabilities", "query_positions_readonly"],
        },
        "client_env": {
            "handling": "explicit-user-authorized-reference-only",
            "env_ref": "cr099-client-env:sha256:fixture",
            "secret_values_allowed_in_contract": False,
        },
        "evidence": {
            "output_dir": ".quant-lab/evidence/qmt/cr099/redacted/cr099-fixture-run/",
            "raw_payload_allowed": False,
        },
        "abort_conditions": [
            "missing_cp5_approval",
            "missing_runtime_authorization",
            "missing_or_ambiguous_env_ref",
            "endpoint_not_in_allowlist",
            "redaction_gate_unavailable",
            "forbidden_counter_non_zero",
            "raw_payload_detected",
        ],
    }


def _valid_evidence() -> dict[str, object]:
    return {
        "schema_version": 1,
        "cr_id": "CR-099",
        "run_id": "cr099-fixture-run",
        "authorization_ref": "user-approved-cr099-fixture",
        "generated_at": "2026-06-19T16:13:23+08:00",
        "execution_mode": "user-manual-windows-side",
        "endpoints": {
            "health": {
                "attempted": True,
                "status": "ok",
                "raw_payload_emitted": False,
            },
            "capabilities": {
                "attempted": True,
                "status": "ok",
                "readonly_supported": True,
                "raw_payload_emitted": False,
            },
            "query_positions_readonly": {
                "attempted": True,
                "status": "empty",
                "position_count_bucket": "zero",
                "positions_digest": "sha256:empty-fixture",
                "items_redacted_count": 0,
                "raw_payload_emitted": False,
            },
        },
        "forbidden_counters": {
            "account_id_values": 0,
            "security_code_values": 0,
            "raw_quantity_values": 0,
            "raw_cash_values": 0,
            "order_fields": 0,
            "fill_fields": 0,
            "submit_cancel_calls": 0,
            "buy_sell_calls": 0,
            "nas_operations": 0,
            "provider_lake_publish": 0,
        },
    }


def _write_yaml(tmp_path: Path, name: str, payload: dict[str, object]) -> Path:
    path = tmp_path / name
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    return path


def test_cr099_run_contract_accepts_minimal_authorized_reference(tmp_path: Path) -> None:
    path = _write_yaml(tmp_path, "contract.yaml", _valid_contract())

    result = check_run_contract(path)

    assert result.passed is True
    assert result.errors == ()


def test_cr099_run_contract_rejects_order_endpoint(tmp_path: Path) -> None:
    contract = _valid_contract()
    contract["gateway"] = {
        "host": "127.0.0.1",
        "port": 18765,
        "scheme": "http",
        "allowlist": ["health", "capabilities", "query_positions_readonly", "submit_order"],
    }
    path = _write_yaml(tmp_path, "contract.yaml", contract)

    result = check_run_contract(path)

    assert result.passed is False
    assert any("gateway.allowlist" in error for error in result.errors)


def test_cr099_run_contract_rejects_secret_like_env_ref(tmp_path: Path) -> None:
    contract = _valid_contract()
    contract["client_env"] = {
        "handling": "explicit-user-authorized-reference-only",
        "env_ref": "/tmp/client.env",
        "secret_values_allowed_in_contract": False,
    }
    path = _write_yaml(tmp_path, "contract.yaml", contract)

    result = check_run_contract(path)

    assert result.passed is False
    assert any(".env" in error for error in result.errors)


def test_cr099_redacted_evidence_accepts_zero_position_summary(tmp_path: Path) -> None:
    path = _write_yaml(tmp_path, "evidence.yaml", _valid_evidence())

    result = check_redacted_evidence(path)

    assert result.passed is True
    assert result.errors == ()


def test_cr099_redacted_evidence_rejects_nonzero_forbidden_counter(tmp_path: Path) -> None:
    evidence = _valid_evidence()
    evidence["forbidden_counters"] = {
        **evidence["forbidden_counters"],  # type: ignore[arg-type]
        "buy_sell_calls": 1,
    }
    path = _write_yaml(tmp_path, "evidence.yaml", evidence)

    result = check_redacted_evidence(path)

    assert result.passed is False
    assert "forbidden_counters.buy_sell_calls must be 0" in result.errors


def test_cr099_redacted_evidence_rejects_raw_payload_marker(tmp_path: Path) -> None:
    evidence = _valid_evidence()
    endpoints = evidence["endpoints"]  # type: ignore[assignment]
    endpoints["query_positions_readonly"] = {  # type: ignore[index]
        "attempted": True,
        "status": "ok",
        "position_count_bucket": "one_to_ten",
        "positions_digest": "sha256:redacted-fixture",
        "items_redacted_count": 1,
        "raw_payload_emitted": True,
    }
    path = _write_yaml(tmp_path, "evidence.yaml", evidence)

    result = check_redacted_evidence(path)

    assert result.passed is False
    assert any("raw_payload_emitted must be false" in error for error in result.errors)


def test_cr099_checker_does_not_import_runtime_or_network_modules() -> None:
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


def test_cr099_collector_builds_checker_accepted_redacted_evidence(tmp_path: Path) -> None:
    evidence = build_cr099_evidence(
        run_id="cr099-fixture-run",
        authorization_ref="user-approved-cr099-fixture",
        health={"status": "ok", "session_ready": True},
        capabilities={"status": "ok", "capabilities": ["health", "capabilities", "query_positions"]},
        query_response={
            "status": "ok",
            "payload": {
                "query_positions": {
                    "position_count": 0,
                    "positions_digest": "sha256:empty-fixture",
                    "items_redacted": [],
                    "redaction_status": "pass",
                    "raw_payload_emitted": False,
                },
                "readonly_query_authorized": True,
                "operation_authorized": False,
                "real_operation": False,
            },
            "counters": {},
        },
    )
    path = _write_yaml(tmp_path, "collector-evidence.yaml", evidence)

    result = check_redacted_evidence(path)

    assert evidence["overall_status"] == "pass"
    assert result.passed is True


def test_cr099_collector_blocks_nonzero_forbidden_counter(tmp_path: Path) -> None:
    evidence = build_cr099_evidence(
        run_id="cr099-fixture-run",
        authorization_ref="user-approved-cr099-fixture",
        health={"status": "ok", "session_ready": True},
        capabilities={"status": "ok", "capabilities": ["query_positions"]},
        query_response={
            "status": "ok",
            "payload": {
                "query_positions": {
                    "position_count": 0,
                    "positions_digest": "sha256:empty-fixture",
                    "items_redacted": [],
                    "redaction_status": "pass",
                    "raw_payload_emitted": False,
                },
                "readonly_query_authorized": True,
                "operation_authorized": False,
                "real_operation": False,
            },
            "counters": {"real_order": 1},
        },
    )
    path = _write_yaml(tmp_path, "collector-evidence.yaml", evidence)

    result = check_redacted_evidence(path)

    assert evidence["overall_status"] == "blocked"
    assert result.passed is False
    assert "forbidden_counters.submit_cancel_calls must be 0" in result.errors
