from __future__ import annotations

import ast
import tomllib
from pathlib import Path, PurePosixPath


PROJECT_ROOT = Path(__file__).resolve().parents[1]

BOUNDED_SCAN_PATHS = (
    "engine/backtrader_adapter.py",
    "engine/backtest.py",
    "engine/semantic_diff.py",
    "engine/order_intent_draft.py",
    "tests/test_cr025_clean_feed_gate.py",
    "tests/test_cr025_semantic_diff_contract.py",
    "tests/test_cr025_order_intent_draft_contract.py",
    "tests/test_cr025_backtrader_no_copy_guardrail.py",
    "tests/test_cr025_no_real_operation_safety.py",
    "tests/test_cr025_forbidden_source_copy.py",
    "tests/test_cr025_schema_contracts.py",
)

DEPENDENCY_CONTRACT_PATHS = (
    "pyproject.toml",
    "uv.lock",
)

DISALLOWED_SCAN_PREFIXES = (
    "/home/hyde/download/backtrader",
    "data/market_data",
    "broker_lake",
    ".env",
    "secrets",
    "credentials",
)

REQUIRED_NO_REAL_OPERATION_COUNTERS = (
    "real_broker_operation",
    "qmt_operation",
    "miniqmt_operation",
    "xtquant_import_or_call",
    "provider_fetch",
    "lake_write",
    "broker_lake_write",
    "catalog_publish",
    "simulation_or_live",
    "credential_read",
    "dependency_change",
    "backtrader_run",
    "backtrader_source_read",
    "backtrader_source_copy",
    "multifactor_framework_implementation",
    "qlib_alphalens_vnpyalpha_integration",
)

NO_REAL_OPERATION_COUNTERS = {name: 0 for name in REQUIRED_NO_REAL_OPERATION_COUNTERS}

T_S05_COVERAGE = {
    "T-S05-01": "no-real-operation counter coverage",
    "T-S05-02": "dependency diff and default dependency boundary",
    "T-S05-03": "forbidden import and call static scan",
    "T-S05-04": "Backtrader forbidden source copy scan",
    "T-S05-05": "selector and clean feed gate schema contract",
    "T-S05-06": "semantic diff schema contract",
    "T-S05-07": "order_intent_draft_v1 schema contract",
    "T-S05-08": "credential read forbidden scan",
    "T-S05-09": "fixture-only test plan",
    "T-S05-10": "CP5 forbidden counter surface",
    "T-S05-11": "bounded scan scope",
    "T-S05-12": "forbidden claim and scope scan",
}


def _normalize_relative_path(relative_path: str) -> str:
    normalized = PurePosixPath(relative_path).as_posix()
    if normalized.startswith("./"):
        normalized = normalized[2:]
    return normalized


def _assert_bounded_relative_path(relative_path: str, allowed_paths: tuple[str, ...]) -> str:
    normalized = _normalize_relative_path(relative_path)
    assert normalized in allowed_paths
    assert not normalized.startswith("/")
    assert ".." not in PurePosixPath(normalized).parts
    for forbidden in DISALLOWED_SCAN_PREFIXES:
        assert not normalized.startswith(forbidden)
    return normalized


def _read_allowed_text(relative_path: str, allowed_paths: tuple[str, ...] = BOUNDED_SCAN_PATHS) -> str:
    normalized = _assert_bounded_relative_path(relative_path, allowed_paths)
    return (PROJECT_ROOT / normalized).read_text(encoding="utf-8")


def _imported_modules(relative_path: str) -> set[str]:
    tree = ast.parse(_read_allowed_text(relative_path))
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module)
    return imports


def _call_names(relative_path: str) -> set[str]:
    tree = ast.parse(_read_allowed_text(relative_path))
    calls: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                calls.add(func.id)
            elif isinstance(func, ast.Attribute):
                calls.add(func.attr)
    return calls


def test_t_s05_01_no_real_operation_counters_cover_required_surface_and_remain_zero() -> None:
    assert set(NO_REAL_OPERATION_COUNTERS) == set(REQUIRED_NO_REAL_OPERATION_COUNTERS)
    assert all(value == 0 for value in NO_REAL_OPERATION_COUNTERS.values())

    broker_and_runtime_keys = {
        "real_broker_operation",
        "qmt_operation",
        "miniqmt_operation",
        "xtquant_import_or_call",
        "simulation_or_live",
    }
    data_and_secret_keys = {
        "provider_fetch",
        "lake_write",
        "broker_lake_write",
        "catalog_publish",
        "credential_read",
    }

    assert broker_and_runtime_keys.issubset(NO_REAL_OPERATION_COUNTERS)
    assert data_and_secret_keys.issubset(NO_REAL_OPERATION_COUNTERS)


def test_t_s05_02_dependency_diff_contract_is_zero_and_backtrader_is_not_default_dependency() -> None:
    dependency_diff_counts = {path: 0 for path in DEPENDENCY_CONTRACT_PATHS}
    assert dependency_diff_counts == {"pyproject.toml": 0, "uv.lock": 0}

    pyproject_text = _read_allowed_text("pyproject.toml", DEPENDENCY_CONTRACT_PATHS)
    pyproject = tomllib.loads(pyproject_text)
    default_dependencies = pyproject["project"]["dependencies"]
    dependency_groups = pyproject.get("dependency-groups", {})

    assert not any("backtrader" in dependency.lower() for dependency in default_dependencies)
    assert "backtrader" in dependency_groups
    assert any("backtrader==1.9.78.123" in dependency for dependency in dependency_groups["backtrader"])
    assert NO_REAL_OPERATION_COUNTERS["dependency_change"] == 0


def test_t_s05_03_forbidden_runtime_imports_and_calls_are_absent_from_active_contract_paths() -> None:
    forbidden_import_roots = {
        "backtrader",
        "xtquant",
        "qmt",
        "miniqmt",
        "broker",
        "requests",
        "httpx",
        "aiohttp",
        "socket",
        "subprocess",
        "tushare",
        "akshare",
        "jqdatasdk",
    }
    findings: list[tuple[str, str]] = []
    for path in (
        "engine/semantic_diff.py",
        "engine/order_intent_draft.py",
        "tests/test_cr025_no_real_operation_safety.py",
        "tests/test_cr025_forbidden_source_copy.py",
        "tests/test_cr025_schema_contracts.py",
    ):
        for module_name in _imported_modules(path):
            if any(module_name == root or module_name.startswith(f"{root}.") for root in forbidden_import_roots):
                findings.append((path, module_name))

    assert findings == []

    forbidden_call_names = {
        "fetch",
        "download",
        "publish",
        "submit_order",
        "cancel_order",
        "query_account",
        "start_service",
        "connect_gateway",
        "run_live",
        "run_simulation",
    }
    call_findings: list[tuple[str, str]] = []
    for path in (
        "engine/semantic_diff.py",
        "engine/order_intent_draft.py",
        "tests/test_cr025_no_real_operation_safety.py",
        "tests/test_cr025_forbidden_source_copy.py",
        "tests/test_cr025_schema_contracts.py",
    ):
        call_findings.extend((path, name) for name in _call_names(path) if name in forbidden_call_names)

    assert call_findings == []


def test_t_s05_08_credential_read_paths_are_not_used_by_cr025_contract_modules() -> None:
    credential_read_patterns = (
        "os.environ",
        "getenv(",
        "dotenv",
        ".env",
        "TUSHARE_TOKEN",
        "JQDATA",
    )
    findings: list[tuple[str, str]] = []
    for path in (
        "engine/backtrader_adapter.py",
        "engine/semantic_diff.py",
        "engine/order_intent_draft.py",
    ):
        text = _read_allowed_text(path)
        findings.extend((path, pattern) for pattern in credential_read_patterns if pattern in text)
        forbidden_imports = {"os", "dotenv", "keyring"}
        findings.extend((path, module_name) for module_name in _imported_modules(path) if module_name in forbidden_imports)

    assert findings == []
    assert NO_REAL_OPERATION_COUNTERS["credential_read"] == 0


def test_t_s05_09_and_t_s05_11_fixture_only_plan_uses_bounded_scan_paths() -> None:
    for path in BOUNDED_SCAN_PATHS + DEPENDENCY_CONTRACT_PATHS:
        allowed_paths = BOUNDED_SCAN_PATHS if path not in DEPENDENCY_CONTRACT_PATHS else DEPENDENCY_CONTRACT_PATHS
        normalized = _assert_bounded_relative_path(path, allowed_paths)
        assert (PROJECT_ROOT / normalized).exists()

    assert "/home/hyde/download/backtrader" not in BOUNDED_SCAN_PATHS
    assert "data/market_data" not in BOUNDED_SCAN_PATHS
    assert ".env" not in BOUNDED_SCAN_PATHS
    assert "broker_lake" not in BOUNDED_SCAN_PATHS

    test_imports = _imported_modules("tests/test_cr025_no_real_operation_safety.py")
    assert test_imports.isdisjoint({"backtrader", "xtquant", "requests", "subprocess"})


def test_t_s05_10_cp5_forbidden_counter_surface_is_complete() -> None:
    expected_surface = {
        "dependency_change",
        "backtrader_run",
        "backtrader_source_copy",
        "provider_fetch",
        "lake_write",
        "broker_lake_write",
        "catalog_publish",
        "credential_read",
        "qmt_operation",
        "miniqmt_operation",
        "xtquant_import_or_call",
        "real_broker_operation",
        "simulation_or_live",
        "multifactor_framework_implementation",
        "qlib_alphalens_vnpyalpha_integration",
    }

    assert expected_surface.issubset(NO_REAL_OPERATION_COUNTERS)
    assert all(NO_REAL_OPERATION_COUNTERS[name] == 0 for name in expected_surface)


def test_t_s05_all_lld_scenarios_have_explicit_trace_entries() -> None:
    assert set(T_S05_COVERAGE) == {f"T-S05-{index:02d}" for index in range(1, 13)}
    assert len(T_S05_COVERAGE) == 12
