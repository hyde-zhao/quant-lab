from __future__ import annotations

from pathlib import Path
import re

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[2]
TESTS_ROOT = PROJECT_ROOT / "tests"
PROVENANCE_PATH = TESTS_ROOT / "PROVENANCE.yaml"
ALLOWED_DOMAINS = {
    "backtest",
    "data_lake",
    "docs_quality",
    "experiments",
    "market_data",
    "meta_flow",
    "research",
    "runner",
    "safety",
    "scripts",
    "trading",
}
FORBIDDEN_FILE_PATTERNS = (
    re.compile(r"test_cr\d{3}_"),
    re.compile(r"test_story_"),
    re.compile(r"test_stage\d+_"),
    re.compile(r"test_experiment_\d+"),
)


def test_tests_are_grouped_by_domain_and_not_flat_cr_files() -> None:
    flat_tests = sorted(path.name for path in TESTS_ROOT.glob("test_*.py"))
    assert flat_tests == []

    domains = {path.name for path in TESTS_ROOT.iterdir() if path.is_dir() and path.name not in {"fixtures", "__pycache__"}}
    assert domains <= ALLOWED_DOMAINS
    assert "chapters" not in domains
    assert not any(re.fullmatch(r"cr\d{3}", domain) for domain in domains)

    for path in TESTS_ROOT.rglob("test_*.py"):
        relative = path.relative_to(TESTS_ROOT).as_posix()
        assert len(path.relative_to(TESTS_ROOT).parts) == 2, relative
        assert path.parent.name in ALLOWED_DOMAINS, relative
        assert not any(pattern.match(path.name) for pattern in FORBIDDEN_FILE_PATTERNS), relative


def test_test_provenance_registry_covers_every_test_file() -> None:
    payload = yaml.safe_load(PROVENANCE_PATH.read_text(encoding="utf-8"))
    items = payload["items"]
    actual = sorted(path.relative_to(PROJECT_ROOT).as_posix() for path in TESTS_ROOT.rglob("test_*.py"))

    assert sorted(items) == actual

    old_paths: list[str] = []
    for path, metadata in items.items():
        domain = Path(path).parts[1]
        assert domain in metadata["domains"], path
        assert metadata.get("old_paths") or metadata.get("introduced_by"), path
        assert metadata["provenance"], path
        old_paths.extend(metadata["old_paths"])

    assert len(old_paths) == len(set(old_paths))
