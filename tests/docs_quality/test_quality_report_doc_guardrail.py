from __future__ import annotations

import ast
from pathlib import Path, PurePosixPath


PROJECT_ROOT = Path(__file__).resolve().parents[2]

DOC_SCAN_TARGETS = (
    "README.md",
    "docs/USER-MANUAL.md",
    ".gitignore",
    "tests/docs_quality/test_quality_report_doc_guardrail.py",
)

DENYLIST_PREFIXES = (
    "data/",
    "reports/",
    "raw/",
    "canonical/",
    "gold/",
    "quality/",
    "catalog/",
    "manifest/",
    "manifests/",
    "market_data_lake/",
    "legacy_flat/",
    "credentials/",
    ".git/",
    ".venv/",
    ".pytest_cache/",
    ".mypy_cache/",
    ".ruff_cache/",
    "__pycache__/",
)

DENYLIST_NAMES = {
    ".env",
    ".env.local",
    ".env.production",
}

DENYLIST_SUFFIXES = (
    ".csv",
    ".parquet",
    ".feather",
    ".arrow",
    ".jsonl",
    ".zip",
    ".gz",
    ".sqlite",
    ".db",
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".ipynb",
    ".pkl",
    ".joblib",
    ".pyc",
    ".pem",
    ".key",
    ".secret",
)

QUALITY_TRUTH_REQUIRED_PHRASES = (
    "legacy quality report",
    "legacy old report",
    "lake quality/catalog current truth",
    "current quality truth",
    "coverage proof forbidden",
)

COVERAGE_PROOF_FIELDS = (
    "dataset",
    "start/end",
    "denominator",
    "run_id/source/interface",
    "quality_status",
    "catalog/lineage",
)

FORBIDDEN_LEGACY_REPORT_CLAIMS = (
    "`reports/data_quality_report.csv` 是 current quality truth",
    "reports/data_quality_report.csv is current quality truth",
    "旧 `reports/data_quality_report.csv` 可作为 coverage proof",
    "legacy quality report 可作为 coverage proof",
    "legacy old report 可作为 current quality truth",
    "旧 `data/**` 可作为 fallback",
    "旧 `data/**` 可作为 fixture",
    "data/prices.parquet 可作为 fallback",
)

CREDENTIAL_SENTINELS = (
    "REAL_TUSHARE_TOKEN_SENTINEL",
    "NAS_USERNAME_SENTINEL",
    "NAS_PASSWORD_SENTINEL",
    "PRIVATE_LAKE_PATH_SENTINEL",
)

UNSAFE_CONTENT_READ_FUNCS = {
    "open",
    "read_text",
    "read_bytes",
    "read_csv",
    "read_parquet",
    "read_json",
}

UNSAFE_PATH_LITERALS = (
    "reports/data_quality_report.csv",
    "data/prices.parquet",
    ".env",
)


def _normalize_relative_path(relative_path: str) -> str:
    normalized = PurePosixPath(relative_path).as_posix()
    if normalized.startswith("./"):
        return normalized[2:]
    return normalized


def _denylist_reason(relative_path: str) -> str | None:
    # 只做字符串级路径判定；不得为了判断边界读取或列出真实数据/报告目录。
    normalized = _normalize_relative_path(relative_path)
    name = PurePosixPath(normalized).name
    if normalized in DENYLIST_NAMES or name in DENYLIST_NAMES:
        return "env_or_credential_file"
    if any(normalized == prefix.rstrip("/") or normalized.startswith(prefix) for prefix in DENYLIST_PREFIXES):
        return "blocked_path_prefix"
    if normalized.endswith(DENYLIST_SUFFIXES):
        return "blocked_binary_or_data_file"
    return None


def _read_allowlisted_text(relative_path: str) -> str:
    normalized = _normalize_relative_path(relative_path)
    assert normalized in set(DOC_SCAN_TARGETS)
    assert _denylist_reason(normalized) is None
    return (PROJECT_ROOT / normalized).read_text(encoding="utf-8")


def _combined_docs_text() -> str:
    readme = _read_allowlisted_text("README.md")
    manual = _read_allowlisted_text("docs/USER-MANUAL.md")
    return f"{readme}\n{manual}"


def _call_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return ""


def _node_contains_literal(node: ast.AST, expected: str) -> bool:
    return any(
        isinstance(child, ast.Constant) and isinstance(child.value, str) and expected in child.value
        for child in ast.walk(node)
    )


def test_allowlist_is_limited_to_s05_text_files() -> None:
    allowed = set(DOC_SCAN_TARGETS)
    assert allowed == {
        "README.md",
        "docs/USER-MANUAL.md",
        ".gitignore",
        "tests/docs_quality/test_quality_report_doc_guardrail.py",
    }
    assert sum(target.startswith("data/") for target in allowed) == 0
    assert sum(target.startswith("reports/") for target in allowed) == 0
    assert sum(target.startswith(".env") for target in allowed) == 0
    assert sum(target.startswith("credentials/") for target in allowed) == 0
    assert not any(target.startswith("delivery/") for target in allowed)


def test_denylist_blocks_unsafe_paths_with_string_rules_only() -> None:
    blocked = (
        "reports/data_quality_report.csv",
        "reports/quality.md",
        "data/prices.parquet",
        "data/raw/tushare/file.jsonl",
        ".env",
        ".env.production",
        "credentials/nas.txt",
        "quality/catalog/current.jsonl",
        "market_data_lake/raw/file.jsonl",
    )
    for relative_path in blocked:
        assert _denylist_reason(relative_path) is not None

    for relative_path in DOC_SCAN_TARGETS:
        assert _denylist_reason(relative_path) is None


def test_docs_declare_legacy_report_and_lake_quality_truth() -> None:
    combined = _combined_docs_text()
    combined_lower = combined.lower()

    for phrase in QUALITY_TRUTH_REQUIRED_PHRASES:
        assert phrase in combined_lower
    for field in COVERAGE_PROOF_FIELDS:
        assert field in combined
    assert "reports/data_quality_report.csv" in combined
    assert "quality/catalog" in combined


def test_docs_reject_legacy_report_and_old_data_as_proof_or_fixture() -> None:
    combined = _combined_docs_text()

    for forbidden in FORBIDDEN_LEGACY_REPORT_CLAIMS:
        assert forbidden not in combined
    assert "不得作为 `current quality truth`、coverage proof、fixture、fallback" in combined
    assert "不得用 legacy old report 或旧 `data/**` 补证" in combined


def test_gitignore_keeps_lake_report_credentials_and_fixture_rules() -> None:
    gitignore = _read_allowlisted_text(".gitignore")
    required_rules = (
        "data/",
        "reports/",
        "raw/",
        "canonical/",
        "gold/",
        "quality/",
        "catalog/",
        "manifest/",
        "manifests/",
        "market_data_lake/",
        "legacy_flat/",
        "*.parquet",
        "*.feather",
        "*.arrow",
        "*.jsonl",
        "*.sqlite",
        "*.db",
        ".env",
        ".env.*",
        "credentials/",
        "*.pem",
        "*.key",
        "*.secret",
        "!tests/fixtures/**",
    )
    for rule in required_rules:
        assert rule in gitignore


def test_docs_do_not_expose_credential_sentinels() -> None:
    combined = _combined_docs_text()
    for sentinel in CREDENTIAL_SENTINELS:
        assert sentinel not in combined


def test_test_source_does_not_read_old_report_old_data_or_env() -> None:
    source = _read_allowlisted_text("tests/docs_quality/test_quality_report_doc_guardrail.py")
    tree = ast.parse(source)

    violations = []
    for call in (node for node in ast.walk(tree) if isinstance(node, ast.Call)):
        if _call_name(call.func) not in UNSAFE_CONTENT_READ_FUNCS:
            continue
        for literal in UNSAFE_PATH_LITERALS:
            if _node_contains_literal(call, literal):
                violations.append(f"{_call_name(call.func)}({literal})")

    assert _denylist_reason("reports/data_quality_report.csv") is not None
    assert _denylist_reason("data/prices.parquet") is not None
    assert _denylist_reason(".env") is not None
    assert violations == []
