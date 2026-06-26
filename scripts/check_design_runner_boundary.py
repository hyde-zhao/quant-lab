from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
from typing import Any


REQUIRED_DOCS = {
    "hld_index": "HLD.md",
    "adr_index": "ARCHITECTURE-DECISION.md",
}

REQUIRED_ARCHIVE_DOCS = {
    "cr046_hld": "HLD-CR046-QMT-MINIQMT-DUAL-TARGET-FRAMEWORK.md",
    "cr046_adr": "ARCHITECTURE-DECISION-CR046.md",
    "cr126_runner_design": "RUNNER-CORE-MVP-DESIGN-CR126.md",
}

STRATEGY_RUNNER_CORE_REF = "process/docs/features/strategy-runner-core/DESIGN.md"
CR126_RUNNER_DESIGN_REF = "process/archive/design-cr-docs/RUNNER-CORE-MVP-DESIGN-CR126.md"
ARCHIVE_ROOT_REF = "process/archive/design-cr-docs"
LEGACY_CROSS_TARGET_MARKER = "legacy_cross_target"
RUNNER_AUTHORITY_HEADING = "Runner Architecture Authority"
STRATEGY_RUNNER_BOUNDARY_HEADING = "与 Strategy Runner Core 的边界"


def check_design_runner_boundary(
    design_root: Path,
    archive_root: Path | None = None,
) -> dict[str, Any]:
    errors: list[str] = []
    texts: dict[str, str] = {}
    archive_root = archive_root or Path(ARCHIVE_ROOT_REF)

    if not design_root.exists():
        errors.append(f"design_root_missing:{design_root.as_posix()}")
        return _result(design_root, archive_root, errors)
    if not design_root.is_dir():
        errors.append(f"design_root_not_directory:{design_root.as_posix()}")
        return _result(design_root, archive_root, errors)
    if not archive_root.exists():
        errors.append(f"archive_root_missing:{archive_root.as_posix()}")
        return _result(design_root, archive_root, errors)
    if not archive_root.is_dir():
        errors.append(f"archive_root_not_directory:{archive_root.as_posix()}")
        return _result(design_root, archive_root, errors)

    for key, relative_path in REQUIRED_DOCS.items():
        path = design_root / relative_path
        if not path.is_file():
            errors.append(f"required_doc_missing:{relative_path}")
            continue
        texts[key] = path.read_text(encoding="utf-8")
    for key, relative_path in REQUIRED_ARCHIVE_DOCS.items():
        path = archive_root / relative_path
        if not path.is_file():
            errors.append(f"required_archive_doc_missing:{relative_path}")
            continue
        texts[key] = path.read_text(encoding="utf-8")

    hld_index = texts.get("hld_index", "")
    if hld_index:
        _require_any(hld_index, ('change: "CR-131"', "CR131"), "hld_index_change_not_cr131", errors)
        _require_version_at_least(hld_index, (1, 3), "hld_index_version_not_1_3", errors)
        _require(hld_index, RUNNER_AUTHORITY_HEADING, "hld_runner_authority_section_missing", errors)
        _require(hld_index, STRATEGY_RUNNER_CORE_REF, "hld_strategy_runner_core_ref_missing", errors)
        _require(hld_index, CR126_RUNNER_DESIGN_REF, "hld_cr126_runner_design_ref_missing", errors)
        _require(hld_index, "archived legacy cross-target framework", "hld_cr046_legacy_boundary_missing", errors)
        if "CR046 当前 CP3 审查主 HLD" in hld_index:
            errors.append("hld_still_treats_cr046_as_current_runner_hld")

    adr_index = texts.get("adr_index", "")
    if adr_index:
        _require_any(adr_index, ('change: "CR-131"', "CR131"), "adr_index_change_not_cr131", errors)
        _require_version_at_least(adr_index, (1, 4), "adr_index_version_not_1_4", errors)
        _require(adr_index, "Runner Core Authority", "adr_runner_core_authority_row_missing", errors)
        _require(adr_index, STRATEGY_RUNNER_CORE_REF, "adr_strategy_runner_core_ref_missing", errors)
        _require(adr_index, "legacy cross-target ADR cluster", "adr_cr046_legacy_cluster_missing", errors)
        _require(
            adr_index,
            "CR046 ADR 保留为 QMT / MiniQMT 双目标策略交付框架的历史决策簇",
            "adr_cr046_no_restore_statement_missing",
            errors,
        )

    cr046_hld = texts.get("cr046_hld", "")
    if cr046_hld:
        _require(cr046_hld, 'retained_as: "legacy_cross_target_framework"', "cr046_hld_legacy_marker_missing", errors)
        _require(cr046_hld, "offline_runner_implementation_authority", "cr046_hld_authority_pointer_missing", errors)
        _require(cr046_hld, STRATEGY_RUNNER_BOUNDARY_HEADING, "cr046_hld_boundary_section_missing", errors)
        _require(cr046_hld, STRATEGY_RUNNER_CORE_REF, "cr046_hld_strategy_runner_core_ref_missing", errors)
        _require(cr046_hld, CR126_RUNNER_DESIGN_REF, "cr046_hld_archived_cr126_ref_missing", errors)

    cr046_adr = texts.get("cr046_adr", "")
    if cr046_adr:
        _require(cr046_adr, 'retained_as: "legacy_cross_target_adr_cluster"', "cr046_adr_legacy_marker_missing", errors)
        _require(cr046_adr, "offline_runner_implementation_authority", "cr046_adr_authority_pointer_missing", errors)
        _require(cr046_adr, "## 历史保留 / 权威转移", "cr046_adr_transfer_section_missing", errors)
        _require(cr046_adr, "ADR-CR046-003 MiniQMT Runner 本轮只做安装设计（legacy）", "cr046_adr_003_legacy_marker_missing", errors)
        _require(
            cr046_adr,
            "不代表当前 offline runner core implementation authority",
            "cr046_adr_003_current_authority_warning_missing",
            errors,
        )

    cr126_design = texts.get("cr126_runner_design", "")
    if cr126_design:
        _require(
            cr126_design,
            'retained_as: "cr128_implementation_intake_source_design"',
            "cr126_source_design_marker_missing",
            errors,
        )
        _require(cr126_design, f'feature_authority: "{STRATEGY_RUNNER_CORE_REF}"', "cr126_feature_authority_ref_missing", errors)
        _require(cr126_design, "## 文档定位", "cr126_document_positioning_missing", errors)
        _require(cr126_design, "不是长期 feature authority", "cr126_not_long_term_authority_statement_missing", errors)
        _require(cr126_design, "不授权真实 runtime/NAS/QMT/provider/lake/catalog/trading", "cr126_not_runtime_ready_statement_missing", errors)

    return _result(design_root, archive_root, errors)


def _require(text: str, needle: str, error: str, errors: list[str]) -> None:
    if needle not in text:
        errors.append(error)


def _require_any(text: str, needles: tuple[str, ...], error: str, errors: list[str]) -> None:
    if not any(needle in text for needle in needles):
        errors.append(error)


def _require_version_at_least(
    text: str,
    minimum: tuple[int, int],
    error: str,
    errors: list[str],
) -> None:
    match = re.search(r'^version:\s*"(?P<major>\d+)\.(?P<minor>\d+)"', text, re.MULTILINE)
    if match is None:
        errors.append(error)
        return
    current = (int(match.group("major")), int(match.group("minor")))
    if current < minimum:
        errors.append(error)


def _result(design_root: Path, archive_root: Path, errors: list[str]) -> dict[str, Any]:
    return {
        "schema_version": "cr130-design-runner-boundary-check-v1",
        "design_root": design_root.as_posix(),
        "archive_root": archive_root.as_posix(),
        "passed": not errors,
        "errors": errors,
        "required_docs": REQUIRED_DOCS,
        "required_archive_docs": REQUIRED_ARCHIVE_DOCS,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check CR130 runner architecture authority boundaries in design docs."
    )
    parser.add_argument(
        "--design-root",
        default="process/docs/design",
        help="Design docs root to scan.",
    )
    parser.add_argument(
        "--archive-root",
        default=ARCHIVE_ROOT_REF,
        help="Archived CR-named design docs root to scan.",
    )
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON output.")
    args = parser.parse_args()

    result = check_design_runner_boundary(Path(args.design_root), Path(args.archive_root))
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    elif result["passed"]:
        print("Design runner boundary check: OK")
    else:
        print("Design runner boundary check: FAIL")
        for error in result["errors"]:
            print(f"- {error}")
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
