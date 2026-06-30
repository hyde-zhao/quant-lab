from __future__ import annotations

from pathlib import Path
import re


PROJECT_ROOT = Path(__file__).resolve().parents[2]
EXPERIMENTS_ROOT = PROJECT_ROOT / "experiments"
ENTRYPOINT_PATTERN = re.compile(r"run_[a-z0-9_]+(?:_exp\d{2}(?:_\d{2})?)?\.py$")
SPECIAL_ENTRYPOINTS = {"run_low_turnover_double_sort.py"}


def test_experiment_entrypoints_use_domain_first_names() -> None:
    entrypoints = sorted(path.name for path in EXPERIMENTS_ROOT.glob("*.py"))

    assert entrypoints
    assert not any(name.startswith("run_experiment_") for name in entrypoints)
    assert not any(name.startswith("run_exp") for name in entrypoints)

    for name in entrypoints:
        assert ENTRYPOINT_PATTERN.fullmatch(name), name
        if "_exp" not in name:
            assert name in SPECIAL_ENTRYPOINTS, name
