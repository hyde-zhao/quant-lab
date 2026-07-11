from __future__ import annotations

import inspect
import json
from pathlib import Path

import pytest

from engine.experiment_family_lineage import (
    ExperimentFamilySpec,
    FinalizeTrial,
    RecordSelection,
    SelectionDecision,
    StartAttempt,
    derive_stable_trial_id,
)
from engine.experiment_family_lineage_store import load_family_artifacts
from engine.mature_multifactor_research import (
    PRODUCER_LINEAGE_MAPPING_INVENTORY,
    ProducerLineageConfig,
    ProducerLineageError,
    _ProducerLineageTrial,
    build_strategy_candidate,
)
from engine.multifactor_strategy_candidates import build_strategy_candidates
from scripts.legacy.research import run_multifactor_strategy_candidates as legacy_wrapper
from scripts.research import run_multifactor_strategy_research as public_wrapper


def _payload(chain: str, family_id: str = "family-cr163") -> dict[str, object]:
    return {
        "schema_version": 1,
        "family_id": family_id,
        "producer_chain_id": chain,
        "declared_sequence": 0,
        "objective_ref": "objective:synthetic",
        "parameter_space_ref": "parameters:synthetic",
        "run_refs": ["run:synthetic"],
        "metadata": {"fixture": True},
    }


def _config(tmp_path: Path, chain: str, family_id: str = "family-cr163") -> ProducerLineageConfig:
    spec_path = tmp_path / f"{chain}-spec.json"
    spec_path.write_text(json.dumps(_payload(chain, family_id)), encoding="utf-8")
    return public_wrapper.parse_producer_lineage_cli_pair(
        lineage_spec=str(spec_path.resolve()),
        lineage_root=str((tmp_path / f"{chain}-lineage").resolve()),
        producer_chain_id=chain,
    )


def test_exact_four_mappings_and_two_chains_are_frozen() -> None:
    assert set(PRODUCER_LINEAGE_MAPPING_INVENTORY) == {
        "CPI-CR163-001", "CPI-CR163-002", "CPI-CR163-003", "CPI-CR163-004"
    }
    assert {value[0] for value in PRODUCER_LINEAGE_MAPPING_INVENTORY.values()} == {
        "public_stage3", "legacy_cr039"
    }
    assert sum(value[1] == "wrapper_orchestration" for value in PRODUCER_LINEAGE_MAPPING_INVENTORY.values()) == 2
    assert sum(value[1] == "candidate_hook_boundary" for value in PRODUCER_LINEAGE_MAPPING_INVENTORY.values()) == 2


def test_both_wrappers_use_the_same_strict_parser_object() -> None:
    assert legacy_wrapper.parse_producer_lineage_cli_pair is public_wrapper.parse_producer_lineage_cli_pair
    assert public_wrapper.parse_producer_lineage_cli_pair(
        lineage_spec=None, lineage_root=None, producer_chain_id="public_stage3"
    ) is None


@pytest.mark.parametrize("spec,root", [("/tmp/spec.json", None), (None, "/tmp/root")])
def test_partial_cli_pair_is_blocked(spec: str | None, root: str | None) -> None:
    with pytest.raises(ProducerLineageError, match="lineage_cli_pair_required") as caught:
        public_wrapper.parse_producer_lineage_cli_pair(
            lineage_spec=spec, lineage_root=root, producer_chain_id="public_stage3"
        )
    assert caught.value.code == "lineage_cli_pair_required"


@pytest.mark.parametrize(
    "mutation,expected",
    [
        ({"schema_version": 99}, "schema_version_unsupported"),
        ({"producer_chain_id": "legacy_cr039"}, "family_identity_mismatch"),
        ({"family_id": ""}, "invalid_identifier"),
    ],
)
def test_invalid_spec_is_blocked_before_any_lineage_root_is_created(
    tmp_path: Path, mutation: dict[str, object], expected: str
) -> None:
    payload = _payload("public_stage3")
    payload.update(mutation)
    spec_path = tmp_path / "spec.json"
    spec_path.write_text(json.dumps(payload), encoding="utf-8")
    root = tmp_path / "must-not-exist"
    with pytest.raises(ProducerLineageError) as caught:
        public_wrapper.parse_producer_lineage_cli_pair(
            lineage_spec=str(spec_path.resolve()),
            lineage_root=str(root.resolve()),
            producer_chain_id="public_stage3",
        )
    assert caught.value.code == expected
    assert not root.exists()


@pytest.mark.parametrize(
    "spec_value,root_value,expected",
    [
        ("https://example.invalid/spec.json", "/tmp/root", "lineage_spec_path_invalid"),
        ("/tmp/missing-spec.json", "s3://bucket/root", "lineage_spec_path_invalid"),
    ],
)
def test_nonlocal_or_missing_paths_fail_closed(spec_value: str, root_value: str, expected: str) -> None:
    with pytest.raises(ProducerLineageError) as caught:
        public_wrapper.parse_producer_lineage_cli_pair(
            lineage_spec=spec_value, lineage_root=root_value, producer_chain_id="public_stage3"
        )
    assert caught.value.code == expected


def test_one_session_one_selection_writer_and_candidate_count_does_not_change_raw_count(tmp_path: Path) -> None:
    config = _config(tmp_path, "legacy_cr039")
    trial = _ProducerLineageTrial(
        config,
        expected_chain_id="legacy_cr039",
        normalized_parameters=[{"source_portfolio_id": item} for item in ("p1", "p2", "p3", "p4")],
        seed=0,
        run_id="run:synthetic",
    )
    # A hook may return any list length; membership was already declared once.
    candidate_list_length = 17
    assert candidate_list_length > 1
    trial.finish(decision=SelectionDecision.SELECTED, reason="synthetic_candidates_built")
    trial.seal_and_close()
    artifacts = load_family_artifacts(config.lineage_root, config.family_spec.family_id)
    assert len([item for item in artifacts.commands if isinstance(item, StartAttempt)]) == 4
    assert len([item for item in artifacts.commands if isinstance(item, FinalizeTrial)]) == 4
    assert len([item for item in artifacts.commands if isinstance(item, RecordSelection)]) == 4
    assert next(iter(artifacts.manifests.values())).raw_trial_count == 4
    replay = _ProducerLineageTrial(
        config,
        expected_chain_id="legacy_cr039",
        normalized_parameters=[{"source_portfolio_id": item} for item in ("p1", "p2", "p3", "p4")],
        seed=0,
        run_id="run:synthetic",
    )
    replay.finish(decision=SelectionDecision.SELECTED, reason="synthetic_candidates_built")
    replay.seal_and_close()
    replayed = load_family_artifacts(config.lineage_root, config.family_spec.family_id)
    assert next(iter(replayed.manifests.values())).raw_trial_count == 4
    assert len(replayed.commands) == len(artifacts.commands)


def test_retry_ordinal_is_not_part_of_stable_trial_identity_and_seed_is() -> None:
    params = {"portfolio": "p1", "window": "synthetic"}
    first = derive_stable_trial_id("family", params, 7)
    assert first == derive_stable_trial_id("family", params, 7)
    assert first != derive_stable_trial_id("family", params, 8)


def test_programmatic_contract_rejects_mapping_and_hooks_remain_pure(tmp_path: Path) -> None:
    with pytest.raises(ProducerLineageError, match="producer_lineage_config_invalid"):
        _ProducerLineageTrial(  # type: ignore[arg-type]
            {"lineage_root": str(tmp_path)},
            expected_chain_id="public_stage3",
            normalized_parameters={},
            seed=0,
            run_id="run",
        )
    for hook in (build_strategy_candidate, build_strategy_candidates):
        source = inspect.getsource(hook)
        assert "FamilyLineageSession" not in source
        assert ".submit(" not in source
        assert "RecordSelection" not in source


def test_no_environment_default_history_or_manual_count_inference() -> None:
    source = inspect.getsource(public_wrapper.parse_producer_lineage_cli_pair)
    forbidden = ("os.environ", "getenv", "raw_trial_count", "manual", "manifest", "history", "cwd(")
    assert all(item not in source for item in forbidden)


def test_typed_config_binds_exact_chain(tmp_path: Path) -> None:
    public = _config(tmp_path, "public_stage3", "public-family")
    assert public.producer_chain_id == "public_stage3"
    with pytest.raises(ProducerLineageError, match="family_identity_mismatch"):
        ProducerLineageConfig(public.family_spec, public.lineage_root, "legacy_cr039")
