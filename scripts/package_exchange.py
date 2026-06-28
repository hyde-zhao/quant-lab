#!/usr/bin/env python3
"""Stable entrypoint for local fake package exchange readiness checks."""

from __future__ import annotations

from scripts.legacy.cr.cr100_package_exchange import *
from scripts.legacy.cr.cr100_package_exchange import main


if __name__ == "__main__":
    raise SystemExit(main())
