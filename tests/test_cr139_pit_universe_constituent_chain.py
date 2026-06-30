from __future__ import annotations

from engine.contracts import (
    PIT_UNIVERSE_AVAILABLE_AFTER_DECISION_TIME,
    PIT_UNIVERSE_FIXED_SNAPSHOT_FORBIDDEN,
    PitUniverseConstituent,
    PitUniverseConstituentChain,
    SURVIVORSHIP_BIAS_NOTE,
    validate_pit_universe_constituent_chain,
)


def test_s26_pit_universe_constituent_chain_passes_for_pit_members() -> None:
    chain = PitUniverseConstituentChain(
        universe_id="hs300",
        as_of_date="2026-01-05",
        policy_version="stage2-v1",
        universe_policy_ref="config_facts/universe_policy/all_a_share/config-facts-cr139-v1",
        constituents=(
            PitUniverseConstituent(
                symbol="000001",
                effective_from="2025-12-01",
                effective_to="9999-12-31",
                available_at="2026-01-04T18:00:00+08:00",
                source_run_id="run-index-members-001",
                lineage_checksum="lineage-001",
            ),
        ),
    )

    result = validate_pit_universe_constituent_chain(chain, decision_time="2026-01-05T09:00:00+08:00")

    assert result.passed is True
    assert result.issues == ()


def test_s26_pit_universe_constituent_chain_blocks_fixed_snapshot() -> None:
    chain = PitUniverseConstituentChain(
        universe_id="hs300",
        as_of_date="2026-01-05",
        policy_version="stage2-v1",
        universe_policy_ref="config_facts/universe_policy/all_a_share/config-facts-cr139-v1",
        constituents=(),
        is_pit_universe=False,
        survivorship_bias_note=SURVIVORSHIP_BIAS_NOTE,
    )

    result = validate_pit_universe_constituent_chain(chain)

    assert result.passed is False
    assert any(issue["code"] == PIT_UNIVERSE_FIXED_SNAPSHOT_FORBIDDEN for issue in result.issues)


def test_s26_pit_universe_constituent_chain_blocks_future_available_at() -> None:
    chain = {
        "universe_id": "hs300",
        "as_of_date": "2026-01-05",
        "policy_version": "stage2-v1",
        "universe_policy_ref": "config_facts/universe_policy/all_a_share/config-facts-cr139-v1",
        "is_pit_universe": True,
        "constituents": [
            {
                "symbol": "000001",
                "effective_from": "2025-12-01",
                "effective_to": "9999-12-31",
                "available_at": "2026-01-05T10:00:00+08:00",
                "source_run_id": "run-index-members-001",
                "lineage_checksum": "lineage-001",
            }
        ],
    }

    result = validate_pit_universe_constituent_chain(chain, decision_time="2026-01-05T09:00:00+08:00")

    assert result.passed is False
    assert any(issue["code"] == PIT_UNIVERSE_AVAILABLE_AFTER_DECISION_TIME for issue in result.issues)
