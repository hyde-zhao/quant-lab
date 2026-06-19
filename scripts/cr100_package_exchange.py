from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from trading.strategy_runner.package_exchange import (
    ExchangeOperationResult,
    PackageExchangeError,
    check_exchange,
    create_fake_exchange_root,
    fake_publish_package,
    fake_pull_package,
    validate_package,
)


def _print_result(result: ExchangeOperationResult) -> int:
    print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result.passed else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="CR100 local fake package exchange readiness CLI. No real NAS access."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init-fake-root")
    init_parser.add_argument("--exchange-root", required=True, type=Path)

    check_package_parser = subparsers.add_parser("check-package")
    check_package_parser.add_argument("--package-root", required=True, type=Path)

    publish_parser = subparsers.add_parser("fake-publish")
    publish_parser.add_argument("--package-root", required=True, type=Path)
    publish_parser.add_argument("--exchange-root", required=True, type=Path)

    pull_parser = subparsers.add_parser("fake-pull")
    pull_parser.add_argument("--exchange-root", required=True, type=Path)
    pull_parser.add_argument("--cache-root", required=True, type=Path)
    pull_parser.add_argument("--package-id", required=True)
    pull_parser.add_argument("--package-version", required=True)

    check_exchange_parser = subparsers.add_parser("check-exchange")
    check_exchange_parser.add_argument("--exchange-root", required=True, type=Path)

    args = parser.parse_args(argv)

    if args.command == "init-fake-root":
        root = create_fake_exchange_root(args.exchange_root)
        result = ExchangeOperationResult(
            operation="init_fake_root",
            passed=True,
            exchange_root=str(root.resolve()),
            forbidden_operation_counters={
                "nas_access": 0,
                "nas_read": 0,
                "nas_write": 0,
                "nas_publish": 0,
                "nas_pull": 0,
                "credential_read": 0,
                "runtime_start": 0,
                "trade_write": 0,
                "provider_lake_publish": 0,
            },
        )
        return _print_result(result)

    if args.command == "check-package":
        try:
            validation = validate_package(args.package_root)
            result = ExchangeOperationResult(
                operation="check_package",
                passed=True,
                package_id=validation.identity.package_id,
                package_version=validation.identity.package_version,
                checked_files=validation.checked_files,
                forbidden_operation_counters={
                    "nas_access": 0,
                    "nas_read": 0,
                    "nas_write": 0,
                    "nas_publish": 0,
                    "nas_pull": 0,
                    "credential_read": 0,
                    "runtime_start": 0,
                    "trade_write": 0,
                    "provider_lake_publish": 0,
                },
            )
        except PackageExchangeError as exc:
            result = ExchangeOperationResult(
                operation="check_package",
                passed=False,
                errors=(str(exc),),
                forbidden_operation_counters={
                    "nas_access": 0,
                    "nas_read": 0,
                    "nas_write": 0,
                    "nas_publish": 0,
                    "nas_pull": 0,
                    "credential_read": 0,
                    "runtime_start": 0,
                    "trade_write": 0,
                    "provider_lake_publish": 0,
                },
            )
        return _print_result(result)

    if args.command == "fake-publish":
        return _print_result(fake_publish_package(args.package_root, args.exchange_root))

    if args.command == "fake-pull":
        return _print_result(
            fake_pull_package(
                args.exchange_root,
                args.cache_root,
                args.package_id,
                args.package_version,
            )
        )

    if args.command == "check-exchange":
        return _print_result(check_exchange(args.exchange_root))

    parser.error(f"unsupported command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
