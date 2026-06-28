from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from trading.strategy_runner import (
    RunSpec,
    resolve_active_package,
    run_strategy_package,
)


def check_package(package_root: Path) -> dict[str, Any]:
    run_id = "cr091-offline-check"
    result = run_strategy_package(RunSpec.from_package_root(package_root, run_id=run_id))
    cache_root = package_root / "cache"
    active_package_id = ""
    active_error = ""
    try:
        active = resolve_active_package(cache_root, cache_root / "active.json")
        active_package_id = active.package_id
    except Exception as exc:
        active_error = str(exc)
    counters = dict(result.forbidden_operation_counters)
    passed = (
        result.passed
        and result.package_id == active_package_id
        and all(value == 0 for value in counters.values())
    )
    return {
        "schema_version": "cr091-strategy-runner-package-check-v1",
        "passed": passed,
        "package_id": result.package_id,
        "active_package_id": active_package_id,
        "active_pointer_error": active_error,
        "adapter_status": result.adapter_status,
        "evidence_status": result.evidence_status,
        "target_count": result.target_count,
        "order_intent_count": result.order_intent_count,
        "blocked_reasons": list(result.blocked_reasons),
        "forbidden_operation_counters": counters,
        "not_authorization": True,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Strategy runner offline package checker")
    parser.add_argument("--package-root", required=True, type=Path)
    parser.add_argument("--json", action="store_true", help="emit JSON summary")
    args = parser.parse_args(argv)
    try:
        result = check_package(args.package_root)
    except Exception as exc:
        result = {
            "schema_version": "cr091-strategy-runner-package-check-v1",
            "passed": False,
            "error": str(exc),
            "not_authorization": True,
        }
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"CR091 package check passed={result.get('passed')}")
        if not result.get("passed"):
            print(result.get("error", "adapter or evidence check failed"), file=sys.stderr)
    return 0 if result.get("passed") is True else 1


if __name__ == "__main__":
    raise SystemExit(main())
