#!/usr/bin/env python
"""CLI for CR139 remediation inventory."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from market_data.remediation_inventory import build_inventory, format_summary
from market_data.lake_layout import MarketDataPathError, ensure_path_outside_root


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a read-only market data lake inventory report.")
    parser.add_argument("--lake-root", default=None, help="Market data lake root. Defaults to MARKET_DATA_LAKE_ROOT.")
    parser.add_argument("--out", default=None, help="Optional output path for the rendered report.")
    parser.add_argument("--format", choices=("json", "summary"), default="json")
    parser.add_argument("--dataset", default=None, help="Optional single dataset name to scan.")
    args = parser.parse_args()

    lake_root = args.lake_root or os.getenv("MARKET_DATA_LAKE_ROOT")
    if not lake_root:
        parser.error("--lake-root is required when MARKET_DATA_LAKE_ROOT is not set")

    lake_root_path = Path(lake_root)
    report = build_inventory(lake_root_path, dataset=args.dataset)
    rendered = report.to_json() if args.format == "json" else format_summary(report)
    if args.out:
        try:
            out_path = ensure_path_outside_root(args.out, lake_root_path)
        except MarketDataPathError as exc:
            parser.error(str(exc))
        out_path.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
