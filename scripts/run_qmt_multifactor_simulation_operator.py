from __future__ import annotations

import argparse
from dataclasses import replace
import json
from pathlib import Path
import sys
from typing import Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from trading.qmt_runtime import build_runtime_config, load_runtime_env
from trading.strategy_runner.simulation_evidence import build_operator_evidence_index
from trading.strategy_runner.simulation_operator import (
    build_runtime_qmt_client,
    request_from_mapping,
    run_multifactor_simulation_fixture_operator,
    run_multifactor_simulation_operator,
    write_operator_evidence,
)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    spec = json.loads(Path(args.spec_json).read_text(encoding="utf-8"))
    if args.strategy_admission_json:
        spec["strategy_admission_package"] = json.loads(
            Path(args.strategy_admission_json).read_text(encoding="utf-8")
        )
    request = request_from_mapping(spec)
    if args.output_dir:
        output_path = Path(args.output_dir) / request.run_id / "operator-evidence.json"
        request = replace(
            request,
            persistence_policy=replace(
                request.persistence_policy,
                output_path=output_path.as_posix(),
            ),
        )
    if args.mode == "runtime":
        if not args.env_file:
            raise SystemExit("--env-file is required in runtime mode")
        env = load_runtime_env(args.env_file)
        config = build_runtime_config(
            env,
            runtime_authorization_ref=request.authorization_ref,
        )
        client = build_runtime_qmt_client(
            config=config,
            base_url=args.base_url or config.base_url,
            expected_runtime_profile=request.expected_runtime_profile,
            timeout_seconds=request.timeout_seconds,
        )
        result = run_multifactor_simulation_operator(request, qmt_client=client)
    else:
        result = run_multifactor_simulation_fixture_operator(request, mode=args.mode)
    output_path = write_operator_evidence(result, request.persistence_policy.output_path)
    index_path = output_path.with_name("operator-evidence.index.json")
    index_path.write_text(
        json.dumps(
            build_operator_evidence_index(
                result.to_dict(),
                evidence_ref=output_path.as_posix(),
                mode=args.mode,
            ),
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "status": result.status,
                "blocked_reason": result.blocked_reason,
                "mode": args.mode,
                "evidence_path": str(output_path),
                "evidence_index_path": str(index_path),
                "runtime_touched": args.mode == "runtime",
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0 if result.passed else 2


def _parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run QMT multifactor simulation operator.")
    parser.add_argument("--spec-json", required=True)
    parser.add_argument(
        "--mode",
        choices=("runtime", "fixture", "preflight-only", "plan-only", "reconcile-only"),
        default="runtime",
    )
    parser.add_argument("--env-file", default="")
    parser.add_argument("--base-url", default="")
    parser.add_argument("--output-dir", default="")
    parser.add_argument("--strategy-admission-json", default="")
    return parser.parse_args(argv)


if __name__ == "__main__":
    raise SystemExit(main())
