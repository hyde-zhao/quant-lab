from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from trading.qmt_runtime import build_runtime_config, load_runtime_env
from trading.strategy_runner.simulation_operator import (
    build_runtime_qmt_client,
    request_from_mapping,
    run_multifactor_simulation_operator,
    write_operator_evidence,
)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    spec = json.loads(Path(args.spec_json).read_text(encoding="utf-8"))
    request = request_from_mapping(spec)
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
    output_path = write_operator_evidence(result, request.persistence_policy.output_path)
    print(json.dumps({"status": result.status, "blocked_reason": result.blocked_reason, "evidence_path": str(output_path)}, ensure_ascii=False, sort_keys=True))
    return 0 if result.passed else 2


def _parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run authorized QMT multifactor simulation operator.")
    parser.add_argument("--spec-json", required=True)
    parser.add_argument("--env-file", required=True)
    parser.add_argument("--base-url", default="")
    return parser.parse_args(argv)


if __name__ == "__main__":
    raise SystemExit(main())
