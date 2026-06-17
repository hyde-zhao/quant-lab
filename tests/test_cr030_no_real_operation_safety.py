from __future__ import annotations

import ast
import re
from pathlib import Path, PurePosixPath


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MAIN_DOC = PROJECT_ROOT / "docs" / "CR030-MULTIFACTOR-RESEARCH-LOOP.md"
REFERENCE_MATRIX = PROJECT_ROOT / "docs" / "CR030-MULTIFACTOR-REFERENCE-MATRIX.md"
TEST_PATH = PROJECT_ROOT / "tests" / "test_cr030_no_real_operation_safety.py"

ALLOWED_TEXT_TARGETS = {
    "docs/CR030-MULTIFACTOR-RESEARCH-LOOP.md",
    "docs/CR030-MULTIFACTOR-REFERENCE-MATRIX.md",
    "tests/test_cr030_no_real_operation_safety.py",
}

REQUIRED_CP3_DQ = tuple(f"DQ-CP3-CR030-0{index}" for index in range(1, 8))

REQUIRED_STORIES = (
    "CR030-S01-external-reference-matrix-and-loop-contract",
    "CR030-S02-factor-spec-run-spec-contract",
    "CR030-S03-factor-panel-label-window-fail-closed",
    "CR030-S04-factor-evaluation-report",
    "CR030-S05-multifactor-combiner-portfolio-plan",
    "CR030-S06-experiment-manifest-report-catalog",
    "CR030-S07-strategy-admission-package-handoff",
    "CR030-S08-safety-docs-and-follow-up-boundary",
)

REQUIRED_NO_REAL_OPERATION_CATEGORIES = (
    "runtime_implementation_enablement",
    "dependency_change",
    "external_project_clone",
    "external_project_install",
    "external_project_run",
    "source_copy_or_vendor",
    "provider_fetch",
    "lake_write",
    "catalog_publish",
    "reports_overwrite",
    "qmt_operation",
    "simulation_or_live",
    "account_or_order_operation",
    "credential_read",
)

FOLLOW_UP_ITEMS = (
    "CR-026",
    "optimizer",
    "ML workflow",
    "vectorbt",
    "PyBroker",
    "RQAlpha",
    "vn.py",
    "Backtrader",
)

READY_TERMS = (
    "QMT-ready",
    "simulation-ready",
    "live-ready",
    "production truth",
    "真实可交易授权",
    "真实可交易证据",
)

FORBIDDEN_POSITIVE_PHRASES = (
    "CR-030 verified 授权真实操作",
    "授权真实操作",
    "授权外部项目运行",
    "允许运行外部项目",
    "授权依赖变更",
    "允许依赖变更",
    "授权 provider fetch",
    "允许 provider fetch",
    "授权 lake write",
    "允许 lake write",
    "授权 catalog publish",
    "允许 catalog publish",
    "授权 QMT 操作",
    "允许 QMT 操作",
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
    "可声明为真实可交易授权",
    "可声明为真实可交易证据",
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


def _main_doc() -> str:
    return _read_allowed_text("docs/CR030-MULTIFACTOR-RESEARCH-LOOP.md")


def _all_target_texts() -> dict[str, str]:
    return {
        "docs/CR030-MULTIFACTOR-RESEARCH-LOOP.md": _read_allowed_text(
            "docs/CR030-MULTIFACTOR-RESEARCH-LOOP.md"
        ),
        "docs/CR030-MULTIFACTOR-REFERENCE-MATRIX.md": _read_allowed_text(
            "docs/CR030-MULTIFACTOR-REFERENCE-MATRIX.md"
        ),
    }


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


def _ready_term_negative_occurrences(text: str, term: str) -> list[str]:
    return re.findall(
        rf"(?:不构成|不得声明为|不把[^。\n|]*声明为|不是|不提供|不能作为|不授权|只在否定边界中出现)[^。\n|]*{re.escape(term)}",
        text,
    )


def test_cr030_main_doc_covers_all_cp3_decisions_and_story_boundaries() -> None:
    doc = _main_doc()

    for decision_id in REQUIRED_CP3_DQ:
        assert decision_id in doc

    for story_id in REQUIRED_STORIES:
        assert story_id in doc

    assert "ADR-079" not in doc or "ADR-086" not in doc
    assert "CP5" in doc
    assert "8 个" not in doc or "CR030-S08" in doc


def test_research_loop_exit_is_evidence_package_not_runtime_authorization() -> None:
    doc = _main_doc()

    required_terms = (
        "项目自有多因子研究",
        "本地回测",
        "模拟盘前策略准备包",
        "StrategyAdmissionPackage",
        "evidence_package_complete_for_follow_up_review",
        "CR-020",
        "CR-021",
        "CR-022",
        "CR-023",
        "CR-024",
    )
    for term in required_terms:
        assert term in doc

    assert "不授权真实模拟盘" in doc
    assert "不授权真实运行许可" in doc or "真实运行许可" in doc


def test_no_real_operation_table_covers_required_categories_with_zero_counts() -> None:
    doc = _main_doc()
    rows = _markdown_table_rows(doc, "| 类别 | 计数 | 状态 | 本轮边界 |")
    counters = {row[0]: row[1:] for row in rows}

    assert set(REQUIRED_NO_REAL_OPERATION_CATEGORIES).issubset(counters)
    for category in REQUIRED_NO_REAL_OPERATION_CATEGORIES:
        count, status, explanation = counters[category]
        assert count == "0"
        assert status == "not-authorized"
        assert explanation

    coverage_terms = (
        "实现",
        "依赖",
        "外部",
        "source copy",
        "provider",
        "lake",
        "publish",
        "QMT",
        "simulation",
        "live",
        "credential",
    )
    for term in coverage_terms:
        assert term in doc


def test_follow_up_spikes_are_deferred_and_not_part_of_cr030_p0() -> None:
    doc = _main_doc()

    for item in FOLLOW_UP_ITEMS:
        assert item in doc

    cr026_section = doc[doc.index("| CR-026 Qlib isolated runner |") :]
    for phrase in (
        "后续 Spike candidate",
        "不进入 CR-030 P0",
        "不并行启动",
        "用户单独批准",
        "provider 禁用",
        "source-of-truth boundary",
    ):
        assert phrase in cr026_section

    assert "optimizer Spike" in doc
    assert "后续 ML Spike" in doc
    assert "后续 performance / batch Spike" in doc


def test_positive_authorization_and_misleading_ready_claims_are_absent() -> None:
    for path, text in _all_target_texts().items():
        findings = [phrase for phrase in FORBIDDEN_POSITIVE_PHRASES if phrase in text]
        assert findings == [], f"{path} 包含正向越权声明: {findings}"

        for term in READY_TERMS:
            occurrences = text.count(term)
            negative_occurrences = _ready_term_negative_occurrences(text, term)
            assert occurrences == len(negative_occurrences), (
                path,
                term,
                occurrences,
                negative_occurrences,
            )


def test_docs_do_not_embed_external_runtime_or_dependency_commands() -> None:
    forbidden_command_lines = (
        r"^\s*(?:uv\s+add|pip\s+install|git\s+clone|qrun\b|python\s+-m\s+qlib\b)",
        r"^\s*(?:qlib\.init|provider_uri\s*=|xtquant\b|MiniQMT\b|XtQuant\b)",
        r"^\s*(?:gateway_start|order_submit|order_cancel|account_query|catalog_publish)\b",
    )

    for path, text in _all_target_texts().items():
        lines = text.splitlines()
        for pattern in forbidden_command_lines:
            matches = [line for line in lines if re.search(pattern, line)]
            assert matches == [], f"{path} 包含外部运行或依赖命令: {matches}"

    main_doc = _main_doc()
    assert "uv run --python 3.11 pytest" in main_doc
    assert "uv add" not in main_doc
    assert "pip install" not in main_doc
    assert "git clone" not in main_doc


def test_docs_do_not_contain_credential_examples_or_secret_assignments() -> None:
    secret_assignment = re.compile(
        r"\b(?:TOKEN|SECRET|PASSWORD|PASSWD|COOKIE|SESSION|PRIVATE_KEY|ACCOUNT)\b\s*=",
        re.IGNORECASE,
    )
    private_key_block = re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")

    for path, text in _all_target_texts().items():
        assert secret_assignment.search(text) is None, path
        assert private_key_block.search(text) is None, path


def test_safety_test_is_static_and_does_not_import_external_runtime_or_secret_paths() -> None:
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
        "docs/CR030-MULTIFACTOR-RESEARCH-LOOP.md",
        "docs/CR030-MULTIFACTOR-REFERENCE-MATRIX.md",
        "tests/test_cr030_no_real_operation_safety.py",
    }
