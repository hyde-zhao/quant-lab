from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

from scripts.check_design_surface import ALLOWED_DESIGN_ROOT_FILES, check_design_surface


def test_cr131_design_surface_current_docs_pass() -> None:
    result = check_design_surface(
        Path("process/docs/design"),
        Path("process/archive/design-cr-docs"),
    )

    assert result["passed"] is True
    assert result["errors"] == []


def test_cr131_design_surface_blocks_cr_named_default_root_file(tmp_path: Path) -> None:
    design_root = tmp_path / "design"
    archive_root = tmp_path / "archive"
    design_root.mkdir()
    archive_root.mkdir()
    for file_name in ALLOWED_DESIGN_ROOT_FILES:
        (design_root / file_name).write_text("current\n", encoding="utf-8")
    (design_root / "HLD-CR999-EXAMPLE.md").write_text("bad\n", encoding="utf-8")
    (archive_root / "ARCHIVE-INDEX.md").write_text("CR131\n", encoding="utf-8")
    (archive_root / "HLD-CR999-EXAMPLE.md").write_text("archived\n", encoding="utf-8")

    result = check_design_surface(design_root, archive_root)

    assert result["passed"] is False
    assert "cr_named_design_root_file:HLD-CR999-EXAMPLE.md" in result["errors"]
    assert "unexpected_design_root_file:HLD-CR999-EXAMPLE.md" in result["errors"]


def test_cr131_design_surface_cli_json() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "scripts/check_design_surface.py",
            "--design-root",
            "process/docs/design",
            "--archive-root",
            "process/archive/design-cr-docs",
            "--json",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    payload = json.loads(completed.stdout)
    assert payload["schema_version"] == "cr131-design-surface-check-v1"
    assert payload["passed"] is True
