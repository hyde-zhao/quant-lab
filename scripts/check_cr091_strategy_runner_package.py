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
    ReadonlyGatewayClient,
    adapt_strategy_payload,
    build_evidence_summary,
    load_strategy_package,
    resolve_active_package,
)


def check_package(package_root: Path) -> dict[str, Any]:
    package = load_strategy_package(package_root)
    cache_root = package_root / "cache"
    active = resolve_active_package(cache_root, cache_root / "active.json")
    adapter_result = adapt_strategy_payload(package.to_adapter_payload(), run_id="cr091-offline-check")
    readonly = ReadonlyGatewayClient().query_positions(run_id="cr091-offline-check")
    evidence = build_evidence_summary(
        run_id="cr091-offline-check",
        package_id=package.package_id,
        adapter_type=str(package.manifest.get("adapter_type")),
        adapter_result=adapter_result,
        readonly_result=readonly,
    )
    passed = (
        package.package_id == active.package_id
        and adapter_result.passed
        and readonly.passed
        and evidence.status == "pass"
        and all(value == 0 for value in evidence.forbidden_operation_counters.values())
    )
    return {
        "schema_version": "cr091-strategy-runner-package-check-v1",
        "passed": passed,
        "package_id": package.package_id,
        "active_package_id": active.package_id,
        "adapter_status": adapter_result.status,
        "target_count": 0 if adapter_result.target_portfolio is None else len(adapter_result.target_portfolio.target_symbols),
        "order_intent_count": len(adapter_result.order_intents),
        "readonly_reconciliation_status": readonly.status,
        "forbidden_operation_counters": dict(evidence.forbidden_operation_counters),
        "not_authorization": True,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="CR091 strategy runner offline package checker")
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
