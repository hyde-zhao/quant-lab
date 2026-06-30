from pathlib import Path

from scripts.quality.check_script_entrypoints import check_script_entrypoints


def test_script_entrypoint_naming_guardrail_passes_current_repo() -> None:
    result = check_script_entrypoints(Path(".").resolve())
    assert result["status"] == "PASS"
    assert result["unstable_new_root_entrypoints"] == []
    assert result["unstable_root_entrypoints"] == []
    assert result["unstable_engine_modules"] == []
    assert result["missing_stable_entrypoints"] == []
    assert result["missing_archived_legacy_entrypoints"] == []
    assert result["missing_archived_engine_modules"] == []
