from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

from scripts.check_feature_runner_boundary import check_feature_runner_boundary


def test_cr129_feature_runner_boundary_current_docs_pass() -> None:
    result = check_feature_runner_boundary(Path("process/docs/features"))

    assert result["passed"] is True
    assert result["errors"] == []
    assert result["forbidden_entries"] == []


def test_cr129_feature_runner_boundary_blocks_cr102_runtime_fragments(tmp_path: Path) -> None:
    features_root = tmp_path / "features"
    features_root.mkdir()
    (features_root / "strategy-runner-core").mkdir()
    (features_root / "strategy-runner-core" / "DESIGN.md").write_text("# Strategy Runner Core\n", encoding="utf-8")
    for relative_path in (
        "qmt-miniqmt-dual-target-framework/DESIGN.md",
        "execution-semantics-reference/DESIGN.md",
        "factor-research-loop/DESIGN.md",
        "qmt-gateway-readonly/DESIGN.md",
        "qmt-trading-governance/DESIGN.md",
        "runtime-authorization-safety/DESIGN.md",
    ):
        path = features_root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        extra = ""
        if relative_path == "qmt-miniqmt-dual-target-framework/DESIGN.md":
            extra = (
                'retained_as: "legacy_cross_target_framework"\n'
                "offline_runner_implementation_authority: process/docs/features/strategy-runner-core/DESIGN.md\n"
            )
        path.write_text(f"{extra}## 与 Strategy Runner Core 的边界\n", encoding="utf-8")
    (features_root / "cr102-nas-real-package-exchange-authorization").mkdir()

    result = check_feature_runner_boundary(features_root)

    assert result["passed"] is False
    assert result["forbidden_entries"] == [
        (features_root / "cr102-nas-real-package-exchange-authorization").as_posix()
    ]
    assert any(error.startswith("forbidden_runner_runtime_feature_entry:") for error in result["errors"])


def test_cr129_feature_runner_boundary_cli_json() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "scripts/check_feature_runner_boundary.py",
            "--features-root",
            "process/docs/features",
            "--json",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    payload = json.loads(completed.stdout)
    assert payload["schema_version"] == "cr129-feature-runner-boundary-check-v1"
    assert payload["passed"] is True
