from pathlib import Path

from engine.research_dataset import (
    CR017_CONSUMER_FORBIDDEN_COUNTERS,
    CR017_UNSUPPORTED_EXECUTION_FEATURES,
    build_adjustment_blocked_claims,
    build_consumer_guidance_matrix,
    render_migration_guide_sections,
    research_dataset_policy_metadata,
)


ROOT = Path(__file__).resolve().parents[2]


def _read_text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def _section(text: str, heading: str, next_heading_prefix: str) -> str:
    start = text.index(heading)
    end = text.find(f"\n{next_heading_prefix}", start + len(heading))
    return text[start:] if end == -1 else text[start:end]


def test_consumer_guidance_covers_required_consumers() -> None:
    matrix = build_consumer_guidance_matrix()

    assert set(matrix) >= {"chart", "long_horizon_research", "factor_research", "qmt_order_intent"}
    assert matrix["chart"]["recommended_policy"] == "qfq"
    assert "hfq" in matrix["long_horizon_research"]["allowed_policies"]
    assert "returns_adjusted" in matrix["long_horizon_research"]["allowed_policies"]
    assert matrix["factor_research"]["recommended_policy"] == "returns_adjusted"
    assert "returns_adjusted" in matrix["factor_research"]["allowed_policies"]


def test_qmt_order_intent_is_raw_only() -> None:
    matrix = build_consumer_guidance_matrix()
    qmt = matrix["qmt_order_intent"]

    assert qmt["execution_price_policy"] == "raw"
    assert qmt["allowed_policies"] == ["raw"]
    assert qmt["non_raw_execution_allowed_count"] == 0
    assert qmt["adjusted_execution_price_pass_count"] == 0
    assert set(qmt["blocked_policies"]) == {"qfq", "hfq", "returns_adjusted"}

    metadata = research_dataset_policy_metadata(cr017_status="dev-ready", stage="scale_up")
    assert metadata["execution_price_policy"] == "raw"
    assert metadata["qmt_execution_raw_only"] is True
    assert metadata["qmt_non_raw_execution_allowed_count"] == 0
    assert metadata["adjusted_execution_price_pass_count"] == 0


def test_cr017_unverified_blocks_production_governance_and_scale_up() -> None:
    blocked = build_adjustment_blocked_claims(cr017_status="ready-for-verification", stage="scale_up")
    blocked_claims = {item["claim"] for item in blocked["blocked_claims"]}

    assert blocked["cr017_verified"] is False
    assert blocked["production_adjustment_governance_claim_allowed_count"] == 0
    assert blocked["scale_up_allowed_count"] == 0
    assert {"production_adjustment_governance", "scale_up"} <= blocked_claims

    metadata = research_dataset_policy_metadata(cr017_status="ready-for-verification", stage="scale_up")
    assert metadata["production_adjustment_governance_claim_allowed_count"] == 0
    assert metadata["scale_up_allowed_count"] == 0
    assert "production_adjustment_governance" not in metadata["allowed_claims"]
    assert "scale_up" not in metadata["allowed_claims"]


def test_migration_contract_preserves_legacy_qfq_and_old_reports() -> None:
    metadata = research_dataset_policy_metadata(cr017_status="not_verified", stage="research")
    migration_contract = metadata["migration_contract"]

    assert migration_contract["legacy_qfq_baseline_preserved"] is True
    assert migration_contract["old_report_overwrite_allowed"] is False
    assert migration_contract["new_prices_qfq_replaces_legacy_qfq"] is False

    migration_doc = _read_text("process/docs/source-archive/docs/ADJUSTMENT-POLICY-MIGRATION.md")
    assert "legacy qfq baseline remains read-only" in migration_doc
    assert "old report overwrite" in migration_doc
    assert "legacy qfq overwrite" in migration_doc


def test_docs_expose_consumer_boundary_without_unsupported_execution_claims() -> None:
    migration_doc = _read_text("process/docs/source-archive/docs/ADJUSTMENT-POLICY-MIGRATION.md")
    readme_section = _section(
        _read_text("README.md"),
        "### CR-017 复权双视图与 QMT 消费边界",
        "### ",
    )
    manual_section = _section(
        _read_text("docs/USER-MANUAL.md"),
        "#### CR-017 复权双视图与 QMT 消费边界",
        "#### ",
    )

    for text in (migration_doc, readme_section, manual_section):
        lower_text = text.lower()
        assert "chart" in text
        assert "long_horizon_research" in text or "long-horizon research" in text or "long-horizon" in text
        assert "factor_research" in text or "Factor research" in text or "因子研究" in text
        assert "QMT" in text
        assert "raw-only" in text
        assert "non-raw execution allowed count" in lower_text
        assert "scale_up allowed count" in text

    for feature in CR017_UNSUPPORTED_EXECUTION_FEATURES:
        assert f"`{feature}` | unsupported / blocked" in migration_doc

    prohibited_phrases = (
        "真实 VWAP 已支持",
        "minute 已支持",
        "tick 已支持",
        "Level2 已支持",
        "order-match 已支持",
        "microstructure impact cost 已支持",
        "real VWAP supported",
        "minute execution supported",
        "tick execution supported",
        "level2 execution supported",
        "order-match execution supported",
        "microstructure impact cost supported",
    )
    combined = "\n".join((migration_doc, readme_section, manual_section))
    for phrase in prohibited_phrases:
        assert phrase not in combined


def test_rendered_sections_and_safety_counters_are_zero() -> None:
    sections = render_migration_guide_sections()
    metadata = research_dataset_policy_metadata(cr017_status="not_verified", stage="scale_up")

    assert "Consumer Guidance Matrix" in sections["consumer_guidance"]
    assert "Non-raw execution allowed count: `0`" in sections["governance"]
    assert "Old reports overwrite allowed: `false`" in sections["legacy_qfq"]

    counters = metadata["operation_counts"]
    for counter in CR017_CONSUMER_FORBIDDEN_COUNTERS:
        assert counters[counter] == 0
    assert metadata["unsupported_execution_feature_allowed_count"] == 0
