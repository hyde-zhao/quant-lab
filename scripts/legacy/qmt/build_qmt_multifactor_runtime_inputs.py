from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from trading.strategy_runner.runtime_inputs import (  # noqa: E402
    build_runtime_inputs,
    write_runtime_inputs,
)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    base_spec = _read_json(args.base_spec_json)
    admission = _read_json(args.strategy_admission_json)
    overlay = _read_json(args.runtime_overlay_json)
    inputs = build_runtime_inputs(
        base_spec=base_spec,
        admission_package=admission,
        overlay=overlay,
        readonly_evidence_ref=args.readonly_evidence_ref,
        run_id=args.run_id,
        authorization_ref=args.runtime_authorization_ref,
        expected_runtime_profile=args.expected_runtime_profile,
    )
    spec_path, admission_path = write_runtime_inputs(
        inputs,
        output_dir=args.output_dir,
        run_id=args.run_id,
    )
    print(
        json.dumps(
            {
                "status": "pass",
                "spec_path": spec_path.as_posix(),
                "admission_package_path": admission_path.as_posix(),
                **inputs.to_summary(),
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


def _parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build private QMT multifactor runtime spec/admission inputs."
    )
    parser.add_argument("--base-spec-json", required=True)
    parser.add_argument("--strategy-admission-json", required=True)
    parser.add_argument("--runtime-overlay-json", required=True)
    parser.add_argument("--readonly-evidence-ref", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--runtime-authorization-ref", required=True)
    parser.add_argument("--expected-runtime-profile", default="cr138-simulation")
    parser.add_argument("--output-dir", required=True)
    return parser.parse_args(argv)


def _read_json(path: str) -> dict[str, object]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


if __name__ == "__main__":
    raise SystemExit(main())
