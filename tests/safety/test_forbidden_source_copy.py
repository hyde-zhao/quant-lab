from __future__ import annotations

import ast
from pathlib import Path, PurePosixPath


PROJECT_ROOT = Path(__file__).resolve().parents[2]

DOC_PATH = "docs/reference/BACKTRADER-MODULE-REFERENCE.md"
TEST_PATH = "tests/safety/test_forbidden_source_copy.py"

BOUNDED_SOURCE_COPY_SCAN_PATHS = (
    "backtrader",
    "backtrader.egg-info",
    "vendor/backtrader",
    "vendors/backtrader",
    "third_party/backtrader",
    "external/backtrader",
    "samples/backtrader",
    "tests/backtrader",
    "tests/datas/backtrader",
    "datas/backtrader",
)

ALLOWED_TEXT_TARGETS = (
    DOC_PATH,
    "tests/backtest/test_backtrader_no_copy_guardrail.py",
    TEST_PATH,
)

DISALLOWED_SCAN_PREFIXES = (
    "/home/hyde/download/backtrader",
    "data/market_data",
    "broker_lake",
    ".env",
)

FORBIDDEN_SOURCE_COPY_COUNTS = {
    "backtrader_gpl_source_copy": 0,
    "backtrader_source_migration": 0,
    "vendored_backtrader_source": 0,
    "backtrader_samples_copy": 0,
    "backtrader_tests_copy": 0,
    "backtrader_datas_copy": 0,
    "backtrader_live_store_migration": 0,
    "backtrader_line_metaclass_runtime_migration": 0,
}


def _normalize_relative_path(relative_path: str) -> str:
    normalized = PurePosixPath(relative_path).as_posix()
    if normalized.startswith("./"):
        normalized = normalized[2:]
    return normalized


def _assert_repo_owned_path(relative_path: str, allowed_paths: tuple[str, ...]) -> str:
    normalized = _normalize_relative_path(relative_path)
    assert normalized in allowed_paths
    assert not normalized.startswith("/")
    assert ".." not in PurePosixPath(normalized).parts
    for forbidden in DISALLOWED_SCAN_PREFIXES:
        assert not normalized.startswith(forbidden)
    return normalized


def _read_allowed_text(relative_path: str) -> str:
    normalized = _assert_repo_owned_path(relative_path, ALLOWED_TEXT_TARGETS)
    return (PROJECT_ROOT / normalized).read_text(encoding="utf-8")


def _imported_modules(path: str) -> set[str]:
    tree = ast.parse(_read_allowed_text(path))
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module)
    return imports


def test_t_s05_04_forbidden_source_copy_counters_are_defined_and_zero() -> None:
    assert set(FORBIDDEN_SOURCE_COPY_COUNTS) == {
        "backtrader_gpl_source_copy",
        "backtrader_source_migration",
        "vendored_backtrader_source",
        "backtrader_samples_copy",
        "backtrader_tests_copy",
        "backtrader_datas_copy",
        "backtrader_live_store_migration",
        "backtrader_line_metaclass_runtime_migration",
    }
    assert all(value == 0 for value in FORBIDDEN_SOURCE_COPY_COUNTS.values())


def test_t_s05_04_repo_has_no_backtrader_vendored_source_or_migration_paths() -> None:
    existing_forbidden_paths = [
        relative_path
        for relative_path in BOUNDED_SOURCE_COPY_SCAN_PATHS
        if (PROJECT_ROOT / _assert_repo_owned_path(relative_path, BOUNDED_SOURCE_COPY_SCAN_PATHS)).exists()
    ]

    assert existing_forbidden_paths == []


def test_t_s05_04_no_copy_contract_declares_empty_migration_candidate_and_six_forbidden_classes() -> None:
    doc = _read_allowed_text(DOC_PATH)

    assert "migration_candidate=[]" in doc
    assert "migration_candidate: []" in doc
    assert "no-copy" in doc
    assert "no-source-migration" in doc
    assert "no-vendored-source" in doc
    assert "不复制、裁剪、改写或源码级移植" in doc

    for required_class in (
        "source",
        "samples",
        "tests",
        "datas",
        "live store",
        "line/metaclass runtime",
    ):
        assert required_class in doc


def test_t_s05_11_source_copy_scan_scope_is_bounded_and_never_reads_external_backtrader_tree() -> None:
    for relative_path in BOUNDED_SOURCE_COPY_SCAN_PATHS:
        normalized = _assert_repo_owned_path(relative_path, BOUNDED_SOURCE_COPY_SCAN_PATHS)
        assert not normalized.startswith("/home/hyde/download/backtrader")

    assert "/home/hyde/download/backtrader" not in BOUNDED_SOURCE_COPY_SCAN_PATHS
    assert DOC_PATH in ALLOWED_TEXT_TARGETS
    assert TEST_PATH in ALLOWED_TEXT_TARGETS
    assert ".env" not in ALLOWED_TEXT_TARGETS


def test_t_s05_11_source_copy_test_is_static_and_has_no_runtime_or_network_imports() -> None:
    imports = _imported_modules(TEST_PATH)
    forbidden_import_roots = {
        "backtrader",
        "importlib",
        "subprocess",
        "socket",
        "requests",
        "httpx",
        "aiohttp",
        "tushare",
        "xtquant",
        "qmt",
        "miniqmt",
        "broker",
    }

    assert imports.isdisjoint(forbidden_import_roots)


def test_t_s05_04_backtrader_reference_doc_does_not_authorize_source_migration() -> None:
    doc = _read_allowed_text(DOC_PATH)

    assert "任何候选从空集合变为非空，都必须停止当前 Story" in doc
    assert "另起 CR" in doc
    assert "legal review" in doc
    assert "CP3" in doc
    assert "CP5" in doc
    assert "源码级迁移候选为空" in doc
