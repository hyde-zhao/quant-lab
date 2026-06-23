"""Offline strategy runner CLI."""

from __future__ import annotations

import argparse
from dataclasses import replace
import json
from pathlib import Path
import sys

from trading.strategy_runner.artifact_bundle import inspect_run_artifact_bundle, validate_run_artifact_bundle
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
    parser.add_argument("--json", action="store_true", help="emit JSON RunResult")
    args = parser.parse_args(argv)

    if args.inspect_bundle is not None and args.validate_bundle is not None:
        parser.error("--inspect-bundle and --validate-bundle are mutually exclusive")

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
        if args.evidence_index_output is not None or args.bundle_output is not None:
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
