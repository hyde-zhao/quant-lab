#!/usr/bin/env python3
"""Stable entrypoint for factor robustness validation."""

from __future__ import annotations

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.legacy.cr.run_chapter6_factor_robustness import *
from scripts.legacy.cr.run_chapter6_factor_robustness import main


if __name__ == "__main__":
    raise SystemExit(main())
