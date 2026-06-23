from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ALLOWED_DESIGN_ROOT_FILES = frozenset(
    {
        "ARCHITECTURE-DECISION.md",
        "ARCHIVED-DESIGN-INDEX.md",
        "BLUEPRINT.md",
        "DEPENDENCY-MAP.md",
        "DOMAIN-MAP.md",
        "FEATURE-DESIGN-MATRIX.md",
        "HLD.md",
        "MODULE-BOUNDARIES.yaml",
        "PACKAGE-IDENTITY.yaml",
    }
)

ARCHIVE_INDEX = "ARCHIVE-INDEX.md"


def check_design_surface(design_root: Path, archive_root: Path) -> dict[str, Any]:
    errors: list[str] = []

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

    root_files = sorted(path.name for path in design_root.iterdir() if path.is_file())
    for file_name in root_files:
        if file_name not in ALLOWED_DESIGN_ROOT_FILES:
            errors.append(f"unexpected_design_root_file:{file_name}")
        if "CR" in file_name.upper():
            errors.append(f"cr_named_design_root_file:{file_name}")

    missing_allowed = sorted(ALLOWED_DESIGN_ROOT_FILES.difference(root_files))
    for file_name in missing_allowed:
        errors.append(f"required_design_root_file_missing:{file_name}")

    archive_files = sorted(path.name for path in archive_root.iterdir() if path.is_file())
    if ARCHIVE_INDEX not in archive_files:
        errors.append(f"archive_index_missing:{ARCHIVE_INDEX}")
    archived_cr_files = [file_name for file_name in archive_files if "CR" in file_name.upper()]
    if not archived_cr_files:
        errors.append("archived_cr_design_docs_missing")

    archived_index_text = (archive_root / ARCHIVE_INDEX).read_text(encoding="utf-8") if (archive_root / ARCHIVE_INDEX).is_file() else ""
    if "CR131" not in archived_index_text:
        errors.append("archive_index_cr131_marker_missing")

    return _result(design_root, archive_root, errors)


def _result(design_root: Path, archive_root: Path, errors: list[str]) -> dict[str, Any]:
    return {
        "schema_version": "cr131-design-surface-check-v1",
        "design_root": design_root.as_posix(),
        "archive_root": archive_root.as_posix(),
        "passed": not errors,
        "errors": errors,
        "allowed_design_root_files": sorted(ALLOWED_DESIGN_ROOT_FILES),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Check CR131 design surface archive boundary.")
    parser.add_argument("--design-root", default="process/docs/design")
    parser.add_argument("--archive-root", default="process/archive/design-cr-docs")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    result = check_design_surface(Path(args.design_root), Path(args.archive_root))
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    elif result["passed"]:
        print("Design surface check: OK")
    else:
        print("Design surface check: FAIL")
        for error in result["errors"]:
            print(f"- {error}")
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
