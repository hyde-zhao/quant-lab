#!/usr/bin/env python3
"""Stable entrypoint for QMT runtime smoke summary collection."""

from __future__ import annotations

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.legacy.cr.collect_cr089_qmt_runtime_smoke_summary import *
from scripts.legacy.cr.collect_cr089_qmt_runtime_smoke_summary import _ensure_summary_safe
from scripts.legacy.cr.collect_cr089_qmt_runtime_smoke_summary import main


if __name__ == "__main__":
    raise SystemExit(main())
