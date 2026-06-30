#!/usr/bin/env python
"""CLI for CR139 golden baseline snapshots."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from market_data.remediation_baseline import (
    compare_golden_baselines,
    format_diff_summary,
    format_snapshot_summary,
    freeze_golden_baseline,
    write_baseline_snapshot,
    write_diff_report,
)
from market_data.lake_layout import MarketDataPathError, ensure_path_outside_root


def main() -> int:
    parser = argparse.ArgumentParser(description="Build or compare CR139 read-only golden baselines.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    freeze_parser = subparsers.add_parser("freeze", help="Freeze a GoldenBaselineSnapshot.")
    freeze_parser.add_argument("--lake-root", default=None, help="Market data lake root. Defaults to MARKET_DATA_LAKE_ROOT.")
    freeze_parser.add_argument("--out", required=True, help="Output directory for golden-baseline-snapshot.json.")
    freeze_parser.add_argument("--format", choices=("json", "summary"), default="json")
    freeze_parser.add_argument(
        "--frozen-at",
        default="1970-01-01T00:00:00+00:00",
        help="Deterministic frozen_at value. Defaults to a stable audit sentinel.",
    )

    compare_parser = subparsers.add_parser("compare", help="Compare two GoldenBaselineSnapshot outputs.")
    compare_parser.add_argument("--baseline", required=True, help="Baseline snapshot file or directory.")
    compare_parser.add_argument("--current", required=True, help="Current snapshot file or directory.")
    compare_parser.add_argument("--structural-changes", default=None, help="JSON file or JSON string of structural Story refs.")
    compare_parser.add_argument("--out", default=None, help="Optional file or directory for golden-diff-report.json.")
    compare_parser.add_argument("--lake-root", default=None, help="Protected market data lake root; required for guarded --out writes when MARKET_DATA_LAKE_ROOT is not set.")
    compare_parser.add_argument("--format", choices=("json", "summary"), default="json")
    compare_parser.add_argument(
        "--compared-at",
        default="1970-01-01T00:00:00+00:00",
        help="Deterministic compared_at value. Defaults to a stable audit sentinel.",
    )

    args = parser.parse_args()
    if args.command == "freeze":
        lake_root = args.lake_root or os.getenv("MARKET_DATA_LAKE_ROOT")
        if not lake_root:
            freeze_parser.error("--lake-root is required when MARKET_DATA_LAKE_ROOT is not set")
        lake_root_path = Path(lake_root)
        snapshot = freeze_golden_baseline(lake_root_path, frozen_at=args.frozen_at)
        try:
            write_baseline_snapshot(snapshot, args.out, forbidden_root=lake_root_path)
        except MarketDataPathError as exc:
            freeze_parser.error(str(exc))
        rendered = snapshot.to_json() if args.format == "json" else format_snapshot_summary(snapshot)
        print(rendered, end="")
        return 0

    structural_changes = _load_structural_changes(args.structural_changes)
    report = compare_golden_baselines(
        args.baseline,
        args.current,
        structural_changes=structural_changes,
        compared_at=args.compared_at,
    )
    if args.out:
        lake_root = args.lake_root or os.getenv("MARKET_DATA_LAKE_ROOT")
        if not lake_root:
            compare_parser.error("--lake-root is required when --out is used and MARKET_DATA_LAKE_ROOT is not set")
        try:
            ensure_path_outside_root(args.out, lake_root)
            write_diff_report(report, args.out)
        except MarketDataPathError as exc:
            compare_parser.error(str(exc))
    rendered = report.to_json() if args.format == "json" else format_diff_summary(report)
    print(rendered, end="")
    return 0


def _load_structural_changes(value: str | None):
    if not value:
        return []
    path = Path(value)
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return json.loads(value)


if __name__ == "__main__":
    raise SystemExit(main())
