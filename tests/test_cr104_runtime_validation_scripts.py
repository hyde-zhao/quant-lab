from __future__ import annotations

import ast
import json
from pathlib import Path

from scripts.qmt.build_runtime_preflight_evidence import build_preflight_evidence
from scripts.quality.check_redacted_evidence import check_redacted_evidence


def test_cr104_preflight_evidence_passes_redacted_checker(tmp_path: Path) -> None:
    evidence_path = tmp_path / "cr104-preflight-evidence.json"
    evidence = build_preflight_evidence(
        run_id="cr104-test-preflight",
        authorization_ref="cr104-test-preflight-ref",
        generated_at="2026-06-21T00:00:00+00:00",
        reason_code="missing_runtime_authorization",
    )
    evidence_path.write_text(json.dumps(evidence), encoding="utf-8")

    result = check_redacted_evidence(evidence_path)

    assert result.passed is True
    assert result.errors == ()
    assert any("blocked-preflight" in warning for warning in result.warnings)


def test_cr104_preflight_builder_does_not_import_runtime_or_network_modules() -> None:
    tree = ast.parse(Path("scripts/qmt/build_runtime_preflight_evidence.py").read_text(encoding="utf-8"))
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module.split(".", 1)[0])

    assert not (
        imports
        & {
            "dotenv",
            "httpx",
            "requests",
            "socket",
            "subprocess",
            "trading",
            "urllib",
            "xtquant",
        }
    )


def test_cr104_powershell_defaults_to_dry_run_and_blocks_runtime_without_cp2() -> None:
    script = Path("scripts/qmt/run_miniqmt_runtime_validation.ps1").read_text(encoding="utf-8")

    assert '[string]$Mode = "DryRunPreflight"' in script
    assert "missing_explicit_runtime_authorization" in script
    assert "IApproveRuntimeReadonlyAuthorization" in script
    assert "collect_readonly_smoke_evidence.py" in script
    assert script.index('if ($Mode -eq "DryRunPreflight")') < script.index("collect_readonly_smoke_evidence.py")
