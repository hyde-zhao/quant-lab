from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


FORBIDDEN_DEFAULT_PREFIXES = (
    "cr102-",
    "cr103-",
    "cr104-",
)

REQUIRED_BOUNDARY_DOCS = (
    "qmt-miniqmt-dual-target-framework/DESIGN.md",
    "execution-semantics-reference/DESIGN.md",
    "factor-research-loop/DESIGN.md",
    "qmt-gateway-readonly/DESIGN.md",
    "qmt-trading-governance/DESIGN.md",
    "runtime-authorization-safety/DESIGN.md",
)

BOUNDARY_HEADING = "## 与 Strategy Runner Core 的边界"


def check_feature_runner_boundary(features_root: Path) -> dict[str, Any]:
    errors: list[str] = []
    forbidden_entries: list[str] = []

    if not features_root.exists():
        errors.append(f"features_root_missing:{features_root.as_posix()}")
        return _result(features_root, errors, forbidden_entries)
    if not features_root.is_dir():
        errors.append(f"features_root_not_directory:{features_root.as_posix()}")
        return _result(features_root, errors, forbidden_entries)

    for entry in sorted(features_root.iterdir(), key=lambda path: path.name):
        lower_name = entry.name.lower()
        if any(lower_name.startswith(prefix) for prefix in FORBIDDEN_DEFAULT_PREFIXES):
            forbidden_entries.append(entry.as_posix())
            errors.append(f"forbidden_runner_runtime_feature_entry:{entry.as_posix()}")

    strategy_runner_core = features_root / "strategy-runner-core" / "DESIGN.md"
    if not strategy_runner_core.is_file():
        errors.append("strategy_runner_core_design_missing")

    for relative_path in REQUIRED_BOUNDARY_DOCS:
        path = features_root / relative_path
        if not path.is_file():
            errors.append(f"boundary_doc_missing:{relative_path}")
            continue
        text = path.read_text(encoding="utf-8")
        if BOUNDARY_HEADING not in text:
            errors.append(f"strategy_runner_core_boundary_missing:{relative_path}")

    legacy_framework = features_root / "qmt-miniqmt-dual-target-framework" / "DESIGN.md"
    if legacy_framework.is_file():
        text = legacy_framework.read_text(encoding="utf-8")
        if 'retained_as: "legacy_cross_target_framework"' not in text:
            errors.append("legacy_cross_target_marker_missing:qmt-miniqmt-dual-target-framework/DESIGN.md")
        if "offline_runner_implementation_authority" not in text:
            errors.append("offline_runner_authority_pointer_missing:qmt-miniqmt-dual-target-framework/DESIGN.md")

    return _result(features_root, errors, forbidden_entries)


def _result(features_root: Path, errors: list[str], forbidden_entries: list[str]) -> dict[str, Any]:
    return {
        "schema_version": "cr129-feature-runner-boundary-check-v1",
        "features_root": features_root.as_posix(),
        "passed": not errors,
        "errors": errors,
        "forbidden_entries": forbidden_entries,
        "required_boundary_docs": list(REQUIRED_BOUNDARY_DOCS),
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check CR129 strategy-runner-core feature boundary guardrails."
    )
    parser.add_argument(
        "--features-root",
        default="process/docs/features",
        help="Feature docs root to scan.",
    )
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON output.")
    args = parser.parse_args()

    result = check_feature_runner_boundary(Path(args.features_root))
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    elif result["passed"]:
        print("Feature runner boundary check: OK")
    else:
        print("Feature runner boundary check: FAIL")
        for error in result["errors"]:
            print(f"- {error}")
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
