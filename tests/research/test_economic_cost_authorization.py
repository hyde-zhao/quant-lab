"""CR-168 S05：fixture/static-only 授权、registry N/A 与文档路径护栏。"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from engine.cross_strategy_reliability_gates import FORBIDDEN_OPERATION_FIELDS
from engine.economic_cost_evidence import EconomicCostEvidenceInput, build_economic_cost_evidence
from engine.economic_cost_gate4_projection import project_economic_cost_to_gate4
from engine.strategy_evidence import EvidenceAvailability


REPOSITORY_ROOT = Path(__file__).parents[2]
FIXTURE_ROOT = REPOSITORY_ROOT / "tests" / "fixtures" / "economic_cost"
TEXT_EXTENSIONS = {".py", ".md", ".yaml", ".yml", ".json", ".toml"}
CAPABILITY_REGISTRY_NA_EVIDENCE = {
    "availability": EvidenceAvailability.NOT_APPLICABLE_WITH_REASON.value,
    "reason": "project capability registry is absent; CR-168 uses existing Feature/module references for audit only",
    "feature_refs": (
        "docs/features/economic-cost-evidence/DESIGN.md",
        "docs/features/economic-cost-gate4-projection/DESIGN.md",
    ),
    "module_refs": (
        "engine/economic_cost_evidence.py",
        "engine/economic_cost_gate4_projection.py",
    ),
    "persistent_registry_write": 0,
    "parallel_registry_count": 0,
}


def _component():
    fixture = json.loads((FIXTURE_ROOT / "daily_multifactor_synthetic.json").read_text(encoding="utf-8"))
    result = build_economic_cost_evidence(EconomicCostEvidenceInput(**fixture["input"]))
    assert result.evidence is not None
    return result.evidence


def test_normal_fixture_has_zero_forbidden_operation_counts_and_never_executes_them() -> None:
    outcome = project_economic_cost_to_gate4(_component(), EvidenceAvailability.TYPED_UNAVAILABLE, {})
    assert outcome.canonical_summary is not None
    assert all(value == 0 for value in outcome.canonical_summary.operation_counts.values())
    assert set(FORBIDDEN_OPERATION_FIELDS).issubset(outcome.canonical_summary.operation_counts)


@pytest.mark.parametrize("operation", FORBIDDEN_OPERATION_FIELDS)
def test_each_forbidden_operation_counter_blocks_before_gate4(operation: str) -> None:
    outcome = project_economic_cost_to_gate4(
        _component(),
        EvidenceAvailability.TYPED_UNAVAILABLE,
        {operation: 1},
    )
    assert outcome.reason_code == "external_operation_forbidden"
    assert outcome.canonical_invoked is False


def test_capability_registry_missing_uses_auditable_na_with_existing_feature_and_module_refs() -> None:
    summary = json.loads((REPOSITORY_ROOT / "process" / "changes" / "summaries" / "CR-168.summary.json").read_text(encoding="utf-8"))
    resolution = summary["impact_capability_resolution"]
    assert resolution["summary"]["unresolved"] == 3
    assert {item["code"] for item in resolution["results"]} == {"E_REGISTRY_MISSING"}
    assert CAPABILITY_REGISTRY_NA_EVIDENCE["availability"] == EvidenceAvailability.NOT_APPLICABLE_WITH_REASON.value
    assert CAPABILITY_REGISTRY_NA_EVIDENCE["persistent_registry_write"] == 0
    assert CAPABILITY_REGISTRY_NA_EVIDENCE["parallel_registry_count"] == 0
    assert not (REPOSITORY_ROOT / "docs" / "design" / "CAPABILITY-REGISTRY.yaml").exists()
    for relative_path in (*CAPABILITY_REGISTRY_NA_EVIDENCE["feature_refs"], *CAPABILITY_REGISTRY_NA_EVIDENCE["module_refs"]):
        assert (REPOSITORY_ROOT / relative_path).is_file()


def test_no_parallel_registry_gate_envelope_or_wrong_quality_path_is_created() -> None:
    engine_paths = {path.name for path in (REPOSITORY_ROOT / "engine").glob("economic_cost*.py")}
    assert engine_paths == {"economic_cost_evidence.py", "economic_cost_calculator.py", "economic_cost_gate4_projection.py"}
    assert not list(REPOSITORY_ROOT.glob("**/*economic_cost*registry*"))
    wrong_quality_path = "process/" + "docs/quality/"
    for root in (REPOSITORY_ROOT / "engine", REPOSITORY_ROOT / "tests", REPOSITORY_ROOT / "docs"):
        for path in root.rglob("*"):
            if path.is_file() and path.suffix in TEXT_EXTENSIONS:
                assert wrong_quality_path not in path.read_text(encoding="utf-8", errors="ignore")


def test_c3_sources_are_in_memory_and_do_not_contain_external_operation_primitives() -> None:
    forbidden_fragments = ("open(", "os.environ", "requests.", "subprocess.", "socket.", "http://", "https://", "broker", "qmt_runtime")
    for relative_path in (
        "engine/economic_cost_evidence.py",
        "engine/economic_cost_calculator.py",
        "engine/economic_cost_gate4_projection.py",
    ):
        source = (REPOSITORY_ROOT / relative_path).read_text(encoding="utf-8")
        assert all(fragment not in source for fragment in forbidden_fragments)
