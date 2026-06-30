from __future__ import annotations

import ast
from pathlib import Path


CONSUMER_FILES = (
    Path("engine/research_dataset.py"),
    Path("engine/backtest.py"),
    Path("engine/backtrader_adapter.py"),
    Path("market_data/readers.py"),
    Path("engine/research_reporting.py"),
)


def test_research_and_optional_backend_consumers_do_not_import_production_fetch_layers() -> None:
    forbidden_imports = {
        "market_data.connectors",
        "market_data.runtime",
        "market_data.storage",
        "requests",
        "httpx",
        "aiohttp",
        "socket",
        "tushare",
    }
    for path in CONSUMER_FILES:
        imports = _imported_modules(path)
        assert not [
            module
            for module in imports
            if any(module == forbidden or module.startswith(f"{forbidden}.") for forbidden in forbidden_imports)
        ]


def test_consumer_sources_do_not_reference_token_or_trigger_backfill() -> None:
    forbidden_tokens = {
        "TUSHARE_TOKEN",
        "enable_real_source",
        "tushare-first-acquire",
        "prices-long-horizon-plan",
        "backup-run",
        "restore-run",
    }
    for path in CONSUMER_FILES:
        source = path.read_text(encoding="utf-8")
        assert not [token for token in forbidden_tokens if token in source]


def _imported_modules(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    imports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.append(node.module)
    return imports
