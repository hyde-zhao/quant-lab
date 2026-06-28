#!/usr/bin/env python3
"""List factor catalog entries without touching data lake or runtime systems."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Sequence

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.factor_registry import (
    FactorAvailabilityStatus,
    anomaly_candidate_catalog_entries,
    filter_factor_catalog_entries,
)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="List registered quant-lab factors.")
    parser.add_argument("--format", choices=("table", "json"), default="table")
    parser.add_argument("--status", choices=tuple(item.value for item in FactorAvailabilityStatus))
    parser.add_argument("--used-by", dest="used_by", choices=("stage3", "stage3_candidate", "chapter3", "chapter5", "anomaly_discovery"))
    parser.add_argument("--factor-id", dest="factor_id")
    parser.add_argument("--anomaly-candidates", help="Optional anomaly_candidates.json from scripts/run_anomaly_discovery.py.")
    parser.add_argument("--anomaly-decisions", help="Optional anomaly_admission_decisions.json from scripts/run_anomaly_discovery.py.")
    args = parser.parse_args(argv)

    extra_entries = ()
    if args.anomaly_candidates or args.anomaly_decisions:
        if not args.anomaly_candidates or not args.anomaly_decisions:
            print("--anomaly-candidates and --anomaly-decisions must be provided together", file=sys.stderr)
            return 2
        candidates = json.loads(Path(args.anomaly_candidates).read_text(encoding="utf-8"))
        decisions = json.loads(Path(args.anomaly_decisions).read_text(encoding="utf-8"))
        extra_entries = anomaly_candidate_catalog_entries(candidates=candidates, decisions=decisions)

    try:
        entries = filter_factor_catalog_entries(
            status=args.status,
            used_by=args.used_by,
            factor_id=args.factor_id,
            extra_entries=extra_entries,
        )
    except KeyError:
        print(f"unknown factor_id: {args.factor_id}", file=sys.stderr)
        return 2

    if args.format == "json":
        payload: Any
        if args.factor_id:
            payload = entries[0].to_dict()
        else:
            payload = [entry.to_dict() for entry in entries]
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
        return 0

    print(_format_table(entries))
    return 0


def _format_table(entries: Sequence[Any]) -> str:
    columns = ("factor_id", "status", "used_by", "category", "calculator_status")
    rows = [
        (
            entry.factor_id,
            entry.status,
            ",".join(entry.used_by),
            entry.category,
            entry.calculator_status,
        )
        for entry in entries
    ]
    widths = [
        max(len(columns[index]), *(len(row[index]) for row in rows)) if rows else len(columns[index])
        for index in range(len(columns))
    ]
    lines = [
        "  ".join(columns[index].ljust(widths[index]) for index in range(len(columns))),
        "  ".join("-" * width for width in widths),
    ]
    lines.extend("  ".join(row[index].ljust(widths[index]) for index in range(len(columns))) for row in rows)
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
