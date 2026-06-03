from __future__ import annotations

import ast
import re
from pathlib import Path, PurePosixPath


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DOC_PATH = PROJECT_ROOT / "docs" / "CR025-BACKTRADER-MODULE-REFERENCE.md"
TEST_PATH = PROJECT_ROOT / "tests" / "test_cr025_backtrader_no_copy_guardrail.py"

ALLOWED_TEXT_TARGETS = {
    "docs/CR025-BACKTRADER-MODULE-REFERENCE.md",
    "tests/test_cr025_backtrader_no_copy_guardrail.py",
}

REQUIRED_CLASSIFICATIONS = (
    "reference_only",
    "adapt_interface",
    "migration_candidate",
    "exclude",
)

REQUIRED_FORBIDDEN_CLASSES = (
    "source",
    "samples",
    "tests",
    "datas",
    "live store",
    "line/metaclass runtime",
)

MULTIFACTOR_BOUNDARY_TERMS = (
    "FactorSpec",
    "FactorRunSpec",
    "IC / RankIC",
    "分层收益",
    "多因子组合",
    "实验追踪",
    "策略准入包",
    "Qlib",
    "Alphalens",
    "vnpy.alpha",
    "CR-030",
)

FORBIDDEN_REPO_PATHS = (
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

FORBIDDEN_OPERATION_COUNTS = {
    "backtrader_run": 0,
    "backtrader_source_copy": 0,
    "provider_fetch": 0,
    "lake_write": 0,
    "catalog_publish": 0,
    "credential_read": 0,
    "qmt_operation": 0,
    "broker_simulation_live": 0,
    "multifactor_framework_implementation": 0,
    "qlib_alphalens_vnpyalpha_integration": 0,
}


def _normalize_relative_path(relative_path: str) -> str:
    normalized = PurePosixPath(relative_path).as_posix()
    if normalized.startswith("./"):
        return normalized[2:]
    return normalized


def _read_repo_text(relative_path: str) -> str:
    normalized = _normalize_relative_path(relative_path)
    assert normalized in ALLOWED_TEXT_TARGETS
    return (PROJECT_ROOT / normalized).read_text(encoding="utf-8")


def _import_roots(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module)
    return imports


def test_module_reference_doc_declares_four_categories_and_empty_migration_candidates() -> None:
    doc = _read_repo_text("docs/CR025-BACKTRADER-MODULE-REFERENCE.md")

    for classification in REQUIRED_CLASSIFICATIONS:
        assert f"`{classification}`" in doc

    assert "migration_candidate=[]" in doc
    assert re.search(r"migration_candidate:\s*\[\]", doc)
    assert "当前无默认源码级候选" in doc
    assert "另起 CR" in doc
    assert "legal review" in doc
    assert "CP3" in doc
    assert "CP5" in doc


def test_no_copy_guardrail_covers_source_samples_tests_datas_live_and_line_runtime() -> None:
    doc = _read_repo_text("docs/CR025-BACKTRADER-MODULE-REFERENCE.md")

    for token in ("no-copy", "no-source-migration", "no-vendored-source", "GPLv3"):
        assert token in doc

    assert "不复制、裁剪、改写或源码级移植" in doc

    for forbidden_class in REQUIRED_FORBIDDEN_CLASSES:
        assert forbidden_class in doc

    for path_fragment in (
        "backtrader/**",
        "vendor/backtrader/**",
        "vendors/backtrader/**",
        "third_party/backtrader/**",
        "external/backtrader/**",
    ):
        assert path_fragment in doc


def test_backtrader_is_execution_semantic_reference_not_multifactor_framework() -> None:
    doc = _read_repo_text("docs/CR025-BACKTRADER-MODULE-REFERENCE.md")

    assert "execution semantic reference" in doc
    assert "lightweight execution engine" in doc
    assert "不作为多因子研究主框架" in doc
    assert "不作为 production truth" in doc
    assert "不作为 simulation-ready" in doc
    assert "不作为 QMT admission pass" in doc

    for term in MULTIFACTOR_BOUNDARY_TERMS:
        assert term in doc

    assert "不得从 CR-025 自动继承依赖变更" in doc
    assert "provider fetch" in doc
    assert "lake write" in doc
    assert "catalog publish" in doc
    assert "凭据读取" in doc


def test_repo_has_no_vendored_backtrader_source_or_copied_samples_tests_datas() -> None:
    existing_forbidden_paths = [
        relative_path
        for relative_path in FORBIDDEN_REPO_PATHS
        if (PROJECT_ROOT / relative_path).exists()
    ]

    assert existing_forbidden_paths == []


def test_forbidden_operation_counts_are_static_zero_contracts() -> None:
    doc = _read_repo_text("docs/CR025-BACKTRADER-MODULE-REFERENCE.md")

    assert set(FORBIDDEN_OPERATION_COUNTS) == {
        "backtrader_run",
        "backtrader_source_copy",
        "provider_fetch",
        "lake_write",
        "catalog_publish",
        "credential_read",
        "qmt_operation",
        "broker_simulation_live",
        "multifactor_framework_implementation",
        "qlib_alphalens_vnpyalpha_integration",
    }
    assert all(value == 0 for value in FORBIDDEN_OPERATION_COUNTS.values())

    for operation in (
        "Backtrader run",
        "Backtrader source copy / source migration",
        "provider fetch",
        "lake write",
        "catalog publish",
        "credential read",
        "QMT / MiniQMT / XtQuant operation",
        "broker / simulation / live",
        "multifactor framework implementation",
        "Qlib / Alphalens / vnpy.alpha integration",
    ):
        assert operation in doc


def test_guardrail_test_is_static_and_does_not_import_backtrader_runtime() -> None:
    imports = _import_roots(TEST_PATH)
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
    }

    assert imports.isdisjoint(forbidden_import_roots)
    assert ALLOWED_TEXT_TARGETS == {
        "docs/CR025-BACKTRADER-MODULE-REFERENCE.md",
        "tests/test_cr025_backtrader_no_copy_guardrail.py",
    }
