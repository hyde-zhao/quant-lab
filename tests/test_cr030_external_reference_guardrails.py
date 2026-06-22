from __future__ import annotations

import ast
import re
from pathlib import Path, PurePosixPath


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DOC_PATH = (
    PROJECT_ROOT
    / "process"
    / "docs"
    / "source-archive"
    / "docs"
    / "CR030-MULTIFACTOR-REFERENCE-MATRIX.md"
)
TEST_PATH = PROJECT_ROOT / "tests" / "test_cr030_external_reference_guardrails.py"

ALLOWED_TEXT_TARGETS = {
    "process/docs/source-archive/docs/CR030-MULTIFACTOR-REFERENCE-MATRIX.md",
    "tests/test_cr030_external_reference_guardrails.py",
}

REQUIRED_PROJECTS = (
    "Qlib",
    "Alphalens",
    "vectorbt",
    "PyBroker",
    "bt",
    "Zipline Reloaded",
    "QuantConnect LEAN",
    "RQAlpha",
    "vn.py / vnpy.alpha",
    "Backtrader",
)

REQUIRED_CLASSIFICATIONS = (
    "reference_only",
    "optional_spike",
    "exclude_by_default",
    "forbidden_migration",
)

REQUIRED_MATRIX_COLUMNS = (
    "项目",
    "分类",
    "License / 依赖风险",
    "可借鉴点",
    "不可做事项",
    "后续 Spike 条件",
    "与自有多因子研究闭环的关系",
)

REQUIRED_FORBIDDEN_COUNTERS = (
    "external_project_clone",
    "external_project_install",
    "external_project_run",
    "source_migration_or_vendor",
    "dependency_change",
    "provider_fetch",
    "lake_write",
    "catalog_publish",
    "reports_overwrite",
    "qmt_operation",
    "simulation_or_live",
    "account_or_order_operation",
    "credential_read",
)

FORBIDDEN_POSITIVE_PHRASES = (
    "授权运行外部项目",
    "允许运行外部项目",
    "授权安装外部依赖",
    "允许安装外部依赖",
    "授权源码迁移",
    "允许源码迁移",
    "授权 provider fetch",
    "允许 provider fetch",
    "授权 lake write",
    "允许 lake write",
    "授权 catalog publish",
    "允许 catalog publish",
    "授权 QMT",
    "允许 QMT",
    "授权 simulation",
    "允许 simulation",
    "授权 live",
    "允许 live",
    "授权凭据读取",
    "允许凭据读取",
    "可声明为 QMT-ready",
    "可声明为 simulation-ready",
    "可声明为 live-ready",
    "可声明为 production truth",
    "可声明为真实可交易证据",
    "允许声明为 QMT-ready",
    "允许声明为 simulation-ready",
    "允许声明为 live-ready",
    "允许声明为 production truth",
    "允许声明为真实可交易证据",
    "授权声明为 QMT-ready",
    "授权声明为 simulation-ready",
    "授权声明为 live-ready",
    "授权声明为 production truth",
    "授权声明为真实可交易证据",
)

FORBIDDEN_IMPORT_ROOTS = {
    "qlib",
    "alphalens",
    "vectorbt",
    "pybroker",
    "bt",
    "zipline",
    "lean",
    "rqalpha",
    "vnpy",
    "backtrader",
    "subprocess",
    "socket",
    "requests",
    "httpx",
    "aiohttp",
    "tushare",
    "xtquant",
    "qmt",
    "miniqmt",
    "dotenv",
    "os",
}


def _normalize_relative_path(relative_path: str) -> str:
    normalized = PurePosixPath(relative_path).as_posix()
    if normalized.startswith("./"):
        return normalized[2:]
    return normalized


def _read_allowed_text(relative_path: str) -> str:
    normalized = _normalize_relative_path(relative_path)
    assert normalized in ALLOWED_TEXT_TARGETS
    assert not normalized.startswith("/")
    assert ".." not in PurePosixPath(normalized).parts
    return (PROJECT_ROOT / normalized).read_text(encoding="utf-8")


def _markdown_table_rows(text: str, required_header: str) -> list[list[str]]:
    lines = text.splitlines()
    for index, line in enumerate(lines):
        if line.strip() == required_header:
            rows: list[list[str]] = []
            for row in lines[index + 2 :]:
                if not row.startswith("|"):
                    break
                cells = [cell.strip() for cell in row.strip().strip("|").split("|")]
                rows.append(cells)
            return rows
    raise AssertionError(f"未找到表头: {required_header}")


def _import_roots(path: Path) -> set[str]:
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
    calls: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                calls.add(func.id)
            elif isinstance(func, ast.Attribute):
                calls.add(func.attr)
    return calls


def test_reference_matrix_covers_required_external_projects() -> None:
    doc = _read_allowed_text("process/docs/source-archive/docs/CR030-MULTIFACTOR-REFERENCE-MATRIX.md")
    rows = _markdown_table_rows(doc, "| 项目 | 分类 | License / 依赖风险 | 可借鉴点 | 不可做事项 | 后续 Spike 条件 | 与自有多因子研究闭环的关系 |")

    projects = [row[0] for row in rows]
    assert projects == list(REQUIRED_PROJECTS)

    for row in rows:
        assert len(row) == len(REQUIRED_MATRIX_COLUMNS)
        assert all(cell for cell in row)


def test_reference_matrix_uses_allowed_classifications_and_covers_all_categories() -> None:
    doc = _read_allowed_text("process/docs/source-archive/docs/CR030-MULTIFACTOR-REFERENCE-MATRIX.md")
    rows = _markdown_table_rows(doc, "| 项目 | 分类 | License / 依赖风险 | 可借鉴点 | 不可做事项 | 后续 Spike 条件 | 与自有多因子研究闭环的关系 |")

    seen: set[str] = set()
    for row in rows:
        classes = set(re.findall(r"`([^`]+)`", row[1]))
        assert classes
        assert classes.issubset(REQUIRED_CLASSIFICATIONS)
        seen.update(classes)

    assert seen == set(REQUIRED_CLASSIFICATIONS)


def test_forbidden_operation_categories_are_covered_as_zero_count_contracts() -> None:
    doc = _read_allowed_text("process/docs/source-archive/docs/CR030-MULTIFACTOR-REFERENCE-MATRIX.md")
    rows = _markdown_table_rows(doc, "| 操作类别 | 本轮计数 | 状态 | 说明 |")
    counters = {row[0]: row[1:] for row in rows}

    assert set(REQUIRED_FORBIDDEN_COUNTERS).issubset(counters)
    for counter in REQUIRED_FORBIDDEN_COUNTERS:
        count, status, explanation = counters[counter]
        assert count == "0"
        assert status == "not-authorized"
        assert explanation


def test_cr026_remains_deferred_spike_only() -> None:
    doc = _read_allowed_text("process/docs/source-archive/docs/CR030-MULTIFACTOR-REFERENCE-MATRIX.md")

    assert "CR-026 保持后续 Spike candidate" in doc
    assert "不并入 CR-030 P0" in doc
    assert "不与 CR-030 当前 Story 并行启动" in doc
    assert "用户单独批准" in doc
    assert "provider 禁用" in doc
    assert "source-of-truth boundary" in doc


def test_positive_authorization_and_readiness_claims_are_absent() -> None:
    doc = _read_allowed_text("process/docs/source-archive/docs/CR030-MULTIFACTOR-REFERENCE-MATRIX.md")

    findings = [phrase for phrase in FORBIDDEN_POSITIVE_PHRASES if phrase in doc]
    assert findings == []

    readiness_terms = (
        "QMT-ready",
        "simulation-ready",
        "live-ready",
        "production truth",
        "真实可交易证据",
    )
    for term in readiness_terms:
        negative_context = re.findall(rf"(?:不构成|不得|不作为|不产生|不能作为)[^。\n|]*{re.escape(term)}", doc)
        all_occurrences = doc.count(term)
        assert all_occurrences == len(negative_context)


def test_guardrail_test_is_static_and_does_not_import_external_runtime_or_secret_paths() -> None:
    imports = _import_roots(TEST_PATH)
    assert imports.isdisjoint(FORBIDDEN_IMPORT_ROOTS)

    forbidden_call_names = (
        "connect",
        "download",
        "fetch",
        "getenv",
        "init",
        "install",
        "open",
        "publish",
        "qrun",
        "run",
        "submit_order",
    )
    calls = _call_names(TEST_PATH)
    assert calls.isdisjoint(forbidden_call_names)
    assert ALLOWED_TEXT_TARGETS == {
        "process/docs/source-archive/docs/CR030-MULTIFACTOR-REFERENCE-MATRIX.md",
        "tests/test_cr030_external_reference_guardrails.py",
    }
