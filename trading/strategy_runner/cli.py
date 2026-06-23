"""Offline strategy runner CLI."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from trading.strategy_runner.result import RunResult
from trading.strategy_runner.runner import run_strategy_package_from_spec_file
from trading.strategy_runner.run_spec import RunSpecError


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run an offline strategy package from a RunSpec file.")
    parser.add_argument("--spec", required=True, type=Path, help="JSON/YAML RunSpec file")
    parser.add_argument("--json", action="store_true", help="emit JSON RunResult")
    args = parser.parse_args(argv)

    try:
        result = run_strategy_package_from_spec_file(args.spec)
    except (RunSpecError, ValueError, json.JSONDecodeError) as exc:
        result = RunResult.blocked(run_id="unknown", reason=str(exc))

    if args.json:
        print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"strategy runner status={result.status} run_id={result.run_id}")
        if result.blocked_reasons:
            print("blocked_reasons=" + ",".join(result.blocked_reasons), file=sys.stderr)
    return 0 if result.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
