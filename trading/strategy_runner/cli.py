"""Offline strategy runner CLI."""

from __future__ import annotations

import argparse
from dataclasses import replace
import json
from pathlib import Path
import sys

from trading.strategy_runner.artifact_bundle import inspect_run_artifact_bundle, validate_run_artifact_bundle
from trading.strategy_runner.run_registry import (
    append_run_registry_from_bundle,
    inspect_run_registry_entry,
    read_run_registry,
)
from trading.strategy_runner.result import RunResult
from trading.strategy_runner.runner import run_strategy_package
from trading.strategy_runner.run_spec import RunSpec, RunSpecError


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run an offline strategy package from a RunSpec file.")
    parser.add_argument("--spec", type=Path, help="JSON/YAML RunSpec file")
    parser.add_argument(
        "--evidence-index-output",
        type=Path,
        help="write a lightweight evidence index JSON for pass runs",
    )
    parser.add_argument("--bundle-output", type=Path, help="write an offline run artifact bundle for pass runs")
    parser.add_argument("--inspect-bundle", type=Path, help="inspect an existing offline run artifact bundle")
    parser.add_argument("--validate-bundle", type=Path, help="validate an existing offline run artifact bundle")
    parser.add_argument("--registry-output", type=Path, help="append an offline runner run registry JSON")
    parser.add_argument("--append-registry-bundle", type=Path, help="append a validated bundle to a run registry")
    parser.add_argument("--list-registry", type=Path, help="list an offline runner run registry")
    parser.add_argument("--inspect-registry", type=Path, help="inspect one run entry in an offline runner registry")
    parser.add_argument("--run-id", help="run id for --inspect-registry")
    parser.add_argument("--json", action="store_true", help="emit JSON RunResult")
    args = parser.parse_args(argv)

    read_actions = [
        args.inspect_bundle is not None,
        args.validate_bundle is not None,
        args.append_registry_bundle is not None,
        args.list_registry is not None,
        args.inspect_registry is not None,
    ]
    if sum(read_actions) > 1:
        parser.error("bundle and registry read/append actions are mutually exclusive")

    if args.list_registry is not None or args.inspect_registry is not None or args.append_registry_bundle is not None:
        try:
            if args.list_registry is not None:
                payload = read_run_registry(args.list_registry)
            elif args.inspect_registry is not None:
                if not args.run_id:
                    parser.error("--run-id is required with --inspect-registry")
                payload = inspect_run_registry_entry(args.inspect_registry, args.run_id)
            else:
                if args.registry_output is None:
                    parser.error("--registry-output is required with --append-registry-bundle")
                payload = append_run_registry_from_bundle(args.registry_output, args.append_registry_bundle)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            result = RunResult.blocked(run_id=args.run_id or "unknown", reason=str(exc))
            if args.json:
                print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2, sort_keys=True))
            else:
                print(f"strategy runner registry action=blocked reason={exc}", file=sys.stderr)
            return 1
        if args.json:
            print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
        else:
            if args.inspect_registry is not None:
                print(f"strategy runner registry inspect=pass run_id={payload['run_id']}")
            else:
                print(f"strategy runner registry action=pass entries={payload.get('entry_count', 1)}")
        return 0

    if args.inspect_bundle is not None or args.validate_bundle is not None:
        action = "inspect" if args.inspect_bundle is not None else "validate"
        bundle_path = args.inspect_bundle if args.inspect_bundle is not None else args.validate_bundle
        try:
            payload = (
                inspect_run_artifact_bundle(bundle_path)
                if action == "inspect"
                else validate_run_artifact_bundle(bundle_path)
            )
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            result = RunResult.blocked(run_id="unknown", reason=str(exc))
            if args.json:
                print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2, sort_keys=True))
            else:
                print(f"strategy runner bundle {action}=blocked reason={exc}", file=sys.stderr)
            return 1
        if args.json:
            print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
        else:
            print(f"strategy runner bundle {action}=pass status={payload['status']} run_id={payload['run_id']}")
        return 0 if payload.get("passed") is True else 1

    if args.spec is None:
        parser.error("--spec is required unless --inspect-bundle is used")

    try:
        spec = RunSpec.from_file(args.spec)
        if (
            args.evidence_index_output is not None
            or args.bundle_output is not None
            or args.registry_output is not None
        ):
            spec = replace(
                spec,
                evidence_index_output_path=(
                    spec.evidence_index_output_path
                    if args.evidence_index_output is None
                    else args.evidence_index_output
                ),
                bundle_output_path=(
                    spec.bundle_output_path if args.bundle_output is None else args.bundle_output
                ),
                run_registry_output_path=(
                    spec.run_registry_output_path if args.registry_output is None else args.registry_output
                ),
            )
            spec.validate()
        result = run_strategy_package(spec)
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
