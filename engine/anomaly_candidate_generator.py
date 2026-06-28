"""Controlled anomaly candidate generation.

The generator creates a bounded, auditable search space. It does not infer new
formulas from outcomes and does not read the data lake.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence

import numpy as np
import pandas as pd

from engine.anomaly_research import AnomalyDefinition, cross_sectional_winsorize, cross_sectional_zscore


ANOMALY_TEMPLATE_SCHEMA = "controlled_anomaly_template_v1"


@dataclass(frozen=True, slots=True)
class ControlledAnomalyTemplate:
    candidate_id: str
    name: str
    source_type: str
    category: str
    input_fields: tuple[str, ...]
    transform: str
    direction: str
    formula: str
    hypothesis: str
    economic_rationale: str
    prior_logic_ref: str
    a_share_adjustments: tuple[str, ...] = (
        "exclude_smallest_30pct_market_cap",
        "long_only_feasibility",
        "transaction_cost_0_3pct_one_way",
        "policy_cycle_coverage",
    )
    schema_version: str = ANOMALY_TEMPLATE_SCHEMA

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_anomaly_definition(self) -> AnomalyDefinition:
        return AnomalyDefinition(
            anomaly_id=self.candidate_id,
            name=self.name,
            chapter_ref="5.auto",
            source_ref=self.prior_logic_ref,
            required_factor_ids=self.input_fields,
            direction=self.direction,
            formula=self.formula,
            source_type=self.source_type,
            hypothesis=self.hypothesis,
            economic_rationale=self.economic_rationale,
            prior_logic_ref=self.prior_logic_ref,
            a_share_adjustments=self.a_share_adjustments,
        )


DEFAULT_CONTROLLED_ANOMALY_TEMPLATES: tuple[ControlledAnomalyTemplate, ...] = (
    ControlledAnomalyTemplate(
        candidate_id="auto_value_pb_inverse",
        name="Auto PB Inverse Value",
        source_type="financial_extension",
        category="value",
        input_fields=("pb",),
        transform="inverse",
        direction="positive",
        formula="-pb",
        hypothesis="Low price-to-book stocks may embed value compensation or investor neglect.",
        economic_rationale="The candidate extends valuation anomaly research with a simple, auditable PB proxy.",
        prior_logic_ref="controlled-template:valuation:pb_inverse",
    ),
    ControlledAnomalyTemplate(
        candidate_id="auto_value_pe_inverse",
        name="Auto PE Inverse Value",
        source_type="financial_extension",
        category="value",
        input_fields=("pe_ttm",),
        transform="inverse",
        direction="positive",
        formula="-pe_ttm",
        hypothesis="Low PE stocks may earn higher future returns after controlling for known factors.",
        economic_rationale="The candidate tests a classic valuation proxy without data-mined formula selection.",
        prior_logic_ref="controlled-template:valuation:pe_inverse",
    ),
    ControlledAnomalyTemplate(
        candidate_id="auto_momentum_20d",
        name="Auto Momentum 20D",
        source_type="behavioral_theory",
        category="momentum",
        input_fields=("ret_20d",),
        transform="identity",
        direction="positive",
        formula="ret_20d",
        hypothesis="Recent winners may continue to outperform because information diffuses slowly.",
        economic_rationale="Short horizon momentum is a predeclared behavioral candidate, not a fitted threshold.",
        prior_logic_ref="controlled-template:momentum:ret_20d",
    ),
    ControlledAnomalyTemplate(
        candidate_id="auto_momentum_252_21d",
        name="Auto Momentum 252-21D",
        source_type="behavioral_theory",
        category="momentum",
        input_fields=("ret_252_21d",),
        transform="identity",
        direction="positive",
        formula="ret_252_21d",
        hypothesis="Intermediate-term winners may continue to outperform after skipping the most recent month.",
        economic_rationale="The skip-month momentum design is fixed before testing to reduce reversal contamination.",
        prior_logic_ref="controlled-template:momentum:ret_252_21d",
    ),
    ControlledAnomalyTemplate(
        candidate_id="auto_reversal_5d",
        name="Auto Reversal 5D",
        source_type="market_microstructure",
        category="reversal",
        input_fields=("ret_5d",),
        transform="inverse",
        direction="positive",
        formula="-ret_5d",
        hypothesis="Very short-term losers may rebound because of overreaction and liquidity pressure.",
        economic_rationale="The candidate reflects a microstructure and behavior prior with a fixed 5-day horizon.",
        prior_logic_ref="controlled-template:reversal:ret_5d",
    ),
    ControlledAnomalyTemplate(
        candidate_id="auto_low_turnover_20d",
        name="Auto Low Turnover 20D",
        source_type="market_microstructure",
        category="liquidity",
        input_fields=("turnover_20d",),
        transform="inverse",
        direction="positive",
        formula="-turnover_20d",
        hypothesis="Low-turnover stocks may capture attention or liquidity-related return differences.",
        economic_rationale="The turnover direction is predeclared from liquidity and attention theories.",
        prior_logic_ref="controlled-template:liquidity:low_turnover_20d",
    ),
    ControlledAnomalyTemplate(
        candidate_id="auto_adv20_liquidity",
        name="Auto ADV20 Liquidity",
        source_type="market_microstructure",
        category="liquidity",
        input_fields=("adv20",),
        transform="log1p",
        direction="positive",
        formula="log1p(adv20)",
        hypothesis="Higher tradable capacity may improve implementation quality for long-only portfolios.",
        economic_rationale="This candidate tests liquidity capacity as an implementation-aware anomaly proxy.",
        prior_logic_ref="controlled-template:liquidity:adv20_log",
    ),
    ControlledAnomalyTemplate(
        candidate_id="auto_low_volatility_20d",
        name="Auto Low Volatility 20D",
        source_type="risk_theory",
        category="volatility",
        input_fields=("vol_20d",),
        transform="inverse",
        direction="positive",
        formula="-vol_20d",
        hypothesis="Low volatility stocks may earn more stable risk-adjusted returns under leverage constraints.",
        economic_rationale="The candidate encodes the low-volatility risk and constraint story with fixed inputs.",
        prior_logic_ref="controlled-template:risk:low_volatility_20d",
    ),
    ControlledAnomalyTemplate(
        candidate_id="auto_roe_quality",
        name="Auto ROE Quality",
        source_type="financial_extension",
        category="quality",
        input_fields=("roe_ttm",),
        transform="identity",
        direction="positive",
        formula="roe_ttm",
        hypothesis="More profitable firms may earn persistent quality premia.",
        economic_rationale="ROE is a fixed profitability proxy with a direct economic interpretation.",
        prior_logic_ref="controlled-template:quality:roe_ttm",
    ),
    ControlledAnomalyTemplate(
        candidate_id="auto_low_asset_growth",
        name="Auto Low Asset Growth",
        source_type="financial_extension",
        category="investment",
        input_fields=("asset_growth",),
        transform="inverse",
        direction="positive",
        formula="-asset_growth",
        hypothesis="Low investment firms may outperform firms with aggressive asset expansion.",
        economic_rationale="The candidate follows the investment anomaly prior using a fixed growth field.",
        prior_logic_ref="controlled-template:investment:low_asset_growth",
    ),
)


def generate_controlled_anomaly_definitions(
    *,
    available_fields: Sequence[str] | None = None,
    templates: Sequence[ControlledAnomalyTemplate] = DEFAULT_CONTROLLED_ANOMALY_TEMPLATES,
) -> tuple[AnomalyDefinition, ...]:
    field_set = set(available_fields) if available_fields is not None else None
    definitions: list[AnomalyDefinition] = []
    for template in templates:
        if field_set is not None and not set(template.input_fields) <= field_set:
            continue
        definitions.append(template.to_anomaly_definition())
    return tuple(definitions)


def build_candidate_matrices_from_panel(
    feature_panel: pd.DataFrame,
    *,
    templates: Sequence[ControlledAnomalyTemplate] = DEFAULT_CONTROLLED_ANOMALY_TEMPLATES,
) -> dict[str, pd.DataFrame]:
    required = {"trade_date", "symbol"}
    missing = required - set(feature_panel.columns)
    if missing:
        raise ValueError("feature_panel 缺少字段: " + ", ".join(sorted(missing)))

    matrices: dict[str, pd.DataFrame] = {}
    available = set(feature_panel.columns)
    for template in templates:
        if not set(template.input_fields) <= available:
            continue
        raw = _template_raw_series(feature_panel, template)
        work = feature_panel[["trade_date", "symbol"]].copy()
        work["candidate_value"] = raw
        matrix = work.pivot_table(
            index="trade_date",
            columns="symbol",
            values="candidate_value",
            aggfunc="last",
        ).sort_index()
        matrices[template.candidate_id] = cross_sectional_zscore(cross_sectional_winsorize(matrix))
    return matrices


def _template_raw_series(feature_panel: pd.DataFrame, template: ControlledAnomalyTemplate) -> pd.Series:
    if len(template.input_fields) != 1:
        raise ValueError(f"controlled template only supports one input field for now: {template.candidate_id}")
    field = template.input_fields[0]
    values = pd.to_numeric(feature_panel[field], errors="coerce")
    if template.transform == "identity":
        return values
    if template.transform == "inverse":
        return -values
    if template.transform == "log1p":
        return np.log1p(values.clip(lower=0))
    raise ValueError(f"unknown controlled anomaly transform: {template.transform}")


def template_map(
    templates: Sequence[ControlledAnomalyTemplate] = DEFAULT_CONTROLLED_ANOMALY_TEMPLATES,
) -> Mapping[str, ControlledAnomalyTemplate]:
    return {template.candidate_id: template for template in templates}
