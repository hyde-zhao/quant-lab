#!/usr/bin/env python3
"""Stable entrypoint for one-off market-data lake repairs."""

from __future__ import annotations

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.legacy.cr.cr012_limited_window_lake_repair import *
from scripts.legacy.cr.cr012_limited_window_lake_repair import main


if __name__ == "__main__":
    raise SystemExit(main())
