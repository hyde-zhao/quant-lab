from pathlib import Path, PurePosixPath


PROJECT_ROOT = Path(__file__).resolve().parents[2]

DOC_SCAN_TARGETS = (
    "README.md",
    "docs/USER-MANUAL.md",
    ".gitignore",
)

ACTIVE_STATIC_SCAN_TARGETS = DOC_SCAN_TARGETS + (
    "market_data/cli.py",
    "market_data/connectors/tushare.py",
    "market_data/storage.py",
    "market_data/normalization.py",
    "market_data/validation.py",
    "market_data/catalog.py",
    "market_data/readers.py",
    "engine/data_loader.py",
    "engine/backtest.py",
    "experiments/comparison.py",
    "experiments/compare_backtest.py",
    "tests/market_data/test_tushare_first_acquisition.py",
    "tests/backtest/test_lightweight_engine_adapter.py",
    "tests/backtest/test_old_data_reference_guardrail.py",
)

POST_S03_STATIC_SCAN_TARGETS = (
    "engine/backtrader_adapter.py",
    "engine/backtest.py",
    "market_data/readers.py",
    "tests/backtest/test_backtrader_clean_feed.py",
)

DENYLIST_PREFIXES = (
    "data/",
    ".git/",
    ".venv/",
    ".pytest_cache/",
    ".mypy_cache/",
    ".ruff_cache/",
    "__pycache__/",
    "credentials/",
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
)

DENYLIST_NAMES = {
    ".env",
    ".env.local",
    ".env.production",
}

DENYLIST_SUFFIXES = (
    ".parquet",
    ".feather",
    ".arrow",
    ".csv",
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

REQUIRED_REFERENCE_ONLY_PHRASES = (
    "旧 repo `data/`",
    "reference-only",
    "不能作为 fallback",
    "不得用旧 repo `data/` 当 fallback",
    "不得用旧 repo `data/` 证明覆盖率",
    "不得读取、列出、复制、迁移、比对或删除旧 repo `data/**`",
    "MARKET_DATA_LAKE_ROOT",
    "dry-run",
    "required_missing",
)

FORBIDDEN_OLD_DATA_CLAIMS = (
    "旧 repo `data/` 作为默认 fallback",
    "旧 repo `data/` 是默认 fallback",
    "旧 repo `data/` 可作为 fallback",
    "旧 repo `data/` 可自动迁移",
    "旧 repo `data/` 用于覆盖证明",
    "旧 `data/` 作为迁移源",
    "旧 `data/` 作为测试 fixture",
    "缺口时读取旧 repo `data/`",
    "缺口时列出旧 repo `data/`",
)

CREDENTIAL_SENTINELS = (
    "REAL_TUSHARE_TOKEN_SENTINEL",
    "NAS_USERNAME_SENTINEL",
    "NAS_PASSWORD_SENTINEL",
    "PRIVATE_LAKE_PATH_SENTINEL",
)


def _normalize_relative_path(relative_path: str) -> str:
    normalized = PurePosixPath(relative_path).as_posix()
    if normalized.startswith("./"):
        return normalized[2:]
    return normalized


def _denylist_reason(relative_path: str) -> str | None:
    # 只做字符串级路径判定；禁止为了判断边界去读取或列出真实数据目录。
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
    assert normalized in set(ACTIVE_STATIC_SCAN_TARGETS) | set(POST_S03_STATIC_SCAN_TARGETS)
    assert _denylist_reason(normalized) is None
    return (PROJECT_ROOT / normalized).read_text(encoding="utf-8")


def test_guardrail_allowlist_and_post_s03_targets_are_explicit() -> None:
    allowed = set(ACTIVE_STATIC_SCAN_TARGETS) | set(POST_S03_STATIC_SCAN_TARGETS)
    assert "README.md" in allowed
    assert "docs/USER-MANUAL.md" in allowed
    assert "tests/backtest/test_old_data_reference_guardrail.py" in allowed
    assert "engine/backtrader_adapter.py" in POST_S03_STATIC_SCAN_TARGETS
    assert "tests/backtest/test_backtrader_clean_feed.py" in POST_S03_STATIC_SCAN_TARGETS
    assert not any(target.startswith("data/") for target in allowed)
    assert not any(target.startswith(".env") for target in allowed)


def test_denylist_blocks_sensitive_or_large_paths_with_string_rules_only() -> None:
    blocked = (
        "data/prices.parquet",
        "data/raw/tushare/hs300.jsonl",
        ".env",
        ".env.production",
        "credentials/nas.txt",
        "market_data_lake/raw/file.jsonl",
        "reports/data_quality_report.csv",
        ".pytest_cache/v/cache/nodeids",
    )
    for relative_path in blocked:
        assert _denylist_reason(relative_path) is not None

    allowed = (
        "README.md",
        "docs/USER-MANUAL.md",
        "market_data/cli.py",
        "engine/backtest.py",
        "tests/backtest/test_old_data_reference_guardrail.py",
    )
    for relative_path in allowed:
        assert _denylist_reason(relative_path) is None


def test_documentation_declares_old_data_reference_only_contract() -> None:
    readme = _read_allowlisted_text("README.md")
    manual = _read_allowlisted_text("docs/USER-MANUAL.md")
    combined = f"{readme}\n{manual}"

    for phrase in REQUIRED_REFERENCE_ONLY_PHRASES:
        assert phrase in combined

    for forbidden in FORBIDDEN_OLD_DATA_CLAIMS:
        assert forbidden not in combined


def test_gitignore_excludes_lake_data_credentials_and_large_outputs() -> None:
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
    )
    for rule in required_rules:
        assert rule in gitignore


def test_static_scan_reports_no_high_risk_old_data_or_secret_claims() -> None:
    scanned = []
    violations = []
    for relative_path in ACTIVE_STATIC_SCAN_TARGETS:
        candidate = PROJECT_ROOT / relative_path
        if not candidate.exists():
            continue
        text = _read_allowlisted_text(relative_path)
        scanned.append(relative_path)
        if relative_path == "tests/backtest/test_old_data_reference_guardrail.py":
            continue
        blocked_phrases = CREDENTIAL_SENTINELS
        blocked_phrases = FORBIDDEN_OLD_DATA_CLAIMS + CREDENTIAL_SENTINELS
        for forbidden in blocked_phrases:
            if forbidden in text:
                violations.append(f"{relative_path}: blocked phrase {forbidden!r}")

    assert "README.md" in scanned
    assert "docs/USER-MANUAL.md" in scanned
    assert "tests/backtest/test_old_data_reference_guardrail.py" in scanned
    assert violations == []
