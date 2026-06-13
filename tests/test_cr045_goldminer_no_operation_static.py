from __future__ import annotations

import ast
from pathlib import Path

from engine.goldminer_bridge_contract import (
    SENSITIVE_FIELD_CATEGORIES,
    build_bridge_capabilities,
    build_bridge_health,
    forbidden_operation_counter_names,
    zero_forbidden_operation_counts,
)
from engine.goldminer_bridge_probe import build_readonly_probe_request, evaluate_readonly_probe_request


PROJECT_ROOT = Path(".")

CR045_ARTIFACT_PATHS = (
    Path("engine/goldminer_bridge_contract.py"),
    Path("engine/goldminer_bridge_client.py"),
    Path("engine/goldminer_bridge_probe.py"),
    Path("tests/test_cr045_goldminer_bridge_contract.py"),
    Path("tests/test_cr045_goldminer_bridge_client.py"),
    Path("tests/test_cr045_goldminer_readonly_probe.py"),
    Path("tests/test_cr045_goldminer_no_operation_static.py"),
    Path("docs/goldminer/CR045-BRIDGE-RUNBOOK.md"),
)

FORBIDDEN_SCAN_PREFIXES = (
    ".env",
    "reports/live",
    "reports/simulation_runtime",
    "data/market_data",
    "catalog",
)


def collect_cr045_artifact_paths(project_root: Path = PROJECT_ROOT) -> list[Path]:
    paths: list[Path] = []
    for relative_path in CR045_ARTIFACT_PATHS:
        normalized = relative_path.as_posix()
        if any(normalized == prefix or normalized.startswith(prefix + "/") for prefix in FORBIDDEN_SCAN_PREFIXES):
            continue
        path = project_root / relative_path
        if path.exists():
            paths.append(path)
    return paths


def _imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module.split(".")[0])
    return imports


def _call_names(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            names.add(node.func.id)
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            names.add(node.func.attr)
    return names


def test_artifact_scan_scope_excludes_credentials_and_runtime_outputs() -> None:
    paths = collect_cr045_artifact_paths()
    normalized = {path.relative_to(PROJECT_ROOT).as_posix() for path in paths}

    assert ".env" not in normalized
    assert not any(path.startswith(".env.") for path in normalized)
    assert not any(path.startswith("reports/live") for path in normalized)
    assert not any(path.startswith("reports/simulation_runtime") for path in normalized)
    assert not any(path.startswith("data/market_data") for path in normalized)
    assert "engine/goldminer_bridge_contract.py" in normalized


def test_sensitive_field_categories_are_complete_and_redacted_only() -> None:
    assert {
        "token",
        "secret",
        "password",
        "passwd",
        "cookie",
        "session",
        "private_key",
        "account_id",
        "broker_account",
        "real_account",
        "trade_password",
        "credential",
    } <= set(SENSITIVE_FIELD_CATEGORIES)


def test_forbidden_operation_counters_are_all_zero_in_fixture_evidence() -> None:
    health = build_bridge_health().operation_counts
    capabilities = build_bridge_capabilities().operation_counts
    readonly = evaluate_readonly_probe_request(build_readonly_probe_request("cash_skeleton")).operation_counts

    for counters in (health, capabilities, readonly, zero_forbidden_operation_counts()):
        assert set(counters) == set(forbidden_operation_counter_names())
        assert all(count == 0 for count in counters.values())


def test_cr045_modules_do_not_import_or_call_real_runtime_boundaries() -> None:
    code_paths = [
        Path("engine/goldminer_bridge_contract.py"),
        Path("engine/goldminer_bridge_client.py"),
        Path("engine/goldminer_bridge_probe.py"),
    ]
    forbidden_imports = {"gm", "gmtrade", "socket", "requests", "urllib", "subprocess", "http"}
    forbidden_calls = {
        "login",
        "connect",
        "query",
        "submit",
        "cancel",
        "set_token",
        "set_endpoint",
        "open",
        "read_text",
        "write_text",
        "request",
        "urlopen",
        "run",
        "Popen",
    }

    for path in code_paths:
        assert _imported_modules(path).isdisjoint(forbidden_imports), path
        assert _call_names(path).isdisjoint(forbidden_calls), path


def test_runbook_does_not_contain_positive_runtime_authorization_claims() -> None:
    runbook = Path("docs/goldminer/CR045-BRIDGE-RUNBOOK.md").read_text(encoding="utf-8")
    forbidden_positive_claims = (
        "simulation_ready=true",
        "live_ready=true",
        "real-readonly-verified",
        "Goldminer login/connect authorized",
        "runtime start authorized",
    )

    for claim in forbidden_positive_claims:
        assert claim not in runbook


def test_no_operation_static_summary_can_be_reproduced_without_env_read() -> None:
    paths = collect_cr045_artifact_paths()

    assert paths
    assert all(path.name not in {".env"} and not path.name.startswith(".env.") for path in paths)
    assert all(path.exists() for path in paths)
