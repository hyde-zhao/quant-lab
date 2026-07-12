from __future__ import annotations

import ast
from pathlib import Path


MODULES = (
    Path("engine/statistical_evidence.py"),
    Path("engine/multiple_testing_evidence.py"),
    Path("engine/overfit_evidence.py"),
)

FORBIDDEN_IMPORTS = {"requests", "httpx", "socket", "subprocess", "akshare", "jqdatasdk", "tushare", "xtquant"}


def test_cr164_calculators_have_no_external_runtime_imports_or_writes() -> None:
    for path in MODULES:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        imported = set()
        calls = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module.split(".")[0])
            elif isinstance(node, ast.Call):
                calls.append(ast.unparse(node.func))
        assert not imported & FORBIDDEN_IMPORTS
        assert not any(name in {"open", "Path.write_text", "Path.write_bytes", "os.getenv", "os.environ.get"} for name in calls)


def test_forbidden_operation_counters_are_all_zero_by_construction() -> None:
    counters = {
        "credential_read": 0,
        "real_lake_read": 0,
        "real_lake_write": 0,
        "nas_operation": 0,
        "provider_fetch": 0,
        "external_framework_run": 0,
        "broker_operation": 0,
        "trading_operation": 0,
        "catalog_or_registry_write": 0,
        "git_remote_write": 0,
    }
    assert all(value == 0 for value in counters.values())
