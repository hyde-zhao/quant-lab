from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

from scripts.check_design_runner_boundary import (
    REQUIRED_ARCHIVE_DOCS,
    REQUIRED_DOCS,
    check_design_runner_boundary,
)


def test_cr130_design_runner_boundary_current_docs_pass() -> None:
    result = check_design_runner_boundary(
        Path("process/docs/design"),
        Path("process/archive/design-cr-docs"),
    )

    assert result["passed"] is True
    assert result["errors"] == []


def test_cr130_design_runner_boundary_blocks_cr046_as_current_runner_hld(tmp_path: Path) -> None:
    design_root = tmp_path / "design"
    archive_root = tmp_path / "archive"
    design_root.mkdir()
    archive_root.mkdir()
    for relative_path in REQUIRED_DOCS.values():
        path = design_root / relative_path
        path.write_text(_valid_doc_text(relative_path), encoding="utf-8")
    for relative_path in REQUIRED_ARCHIVE_DOCS.values():
        path = archive_root / relative_path
        path.write_text(_valid_doc_text(relative_path), encoding="utf-8")
    hld_path = design_root / "HLD.md"
    hld_path.write_text(
        _valid_doc_text("HLD.md") + "\nCR046 当前 CP3 审查主 HLD\n",
        encoding="utf-8",
    )

    result = check_design_runner_boundary(design_root, archive_root)

    assert result["passed"] is False
    assert "hld_still_treats_cr046_as_current_runner_hld" in result["errors"]


def test_cr130_design_runner_boundary_cli_json() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "scripts/check_design_runner_boundary.py",
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
    assert payload["schema_version"] == "cr130-design-runner-boundary-check-v1"
    assert payload["passed"] is True


def _valid_doc_text(relative_path: str) -> str:
    if relative_path == "HLD.md":
        return """
---
version: "1.3"
change: "CR-131"
---
## Runner Architecture Authority
process/docs/features/strategy-runner-core/DESIGN.md
process/archive/design-cr-docs/RUNNER-CORE-MVP-DESIGN-CR126.md
archived legacy cross-target framework
"""
    if relative_path == "ARCHITECTURE-DECISION.md":
        return """
---
version: "1.4"
change: "CR-131"
---
Runner Core Authority
process/docs/features/strategy-runner-core/DESIGN.md
legacy cross-target ADR cluster
CR046 ADR 保留为 QMT / MiniQMT 双目标策略交付框架的历史决策簇
"""
    if relative_path == "HLD-CR046-QMT-MINIQMT-DUAL-TARGET-FRAMEWORK.md":
        return """
---
retained_as: "legacy_cross_target_framework"
offline_runner_implementation_authority: process/docs/features/strategy-runner-core/DESIGN.md
---
## 与 Strategy Runner Core 的边界
process/docs/features/strategy-runner-core/DESIGN.md
process/archive/design-cr-docs/RUNNER-CORE-MVP-DESIGN-CR126.md
"""
    if relative_path == "ARCHITECTURE-DECISION-CR046.md":
        return """
---
retained_as: "legacy_cross_target_adr_cluster"
offline_runner_implementation_authority: process/docs/features/strategy-runner-core/DESIGN.md
---
## 历史保留 / 权威转移
ADR-CR046-003 MiniQMT Runner 本轮只做安装设计（legacy）
不代表当前 offline runner core implementation authority
"""
    if relative_path == "RUNNER-CORE-MVP-DESIGN-CR126.md":
        return """
---
retained_as: "cr128_implementation_intake_source_design"
feature_authority: "process/docs/features/strategy-runner-core/DESIGN.md"
---
## 文档定位
不是长期 feature authority
不授权真实 runtime/NAS/QMT/provider/lake/catalog/trading
"""
    raise AssertionError(relative_path)
