from __future__ import annotations

import importlib
import tomllib
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
LEGACY_ROOTS = ("engine", "market_data", "strategies", "trading")


def test_project_distribution_name_is_quant_lab() -> None:
    pyproject = tomllib.loads((PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8"))

    assert pyproject["project"]["name"] == "quant-lab"


def test_quant_lab_namespace_imports_without_runtime_side_effects() -> None:
    quant_lab = importlib.import_module("quant_lab")

    assert quant_lab.__version__ == "0.1.0"


def test_legacy_import_roots_stay_available() -> None:
    for module_name in LEGACY_ROOTS:
        assert importlib.import_module(module_name).__name__ == module_name


def test_quant_lab_alias_modules_match_legacy_roots() -> None:
    for module_name in LEGACY_ROOTS:
        legacy_module = importlib.import_module(module_name)
        alias_module = importlib.import_module(f"quant_lab.{module_name}")

        assert alias_module is legacy_module
