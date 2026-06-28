"""Unified factor catalog for research consumers.

The catalog is a governance/readability layer over concrete calculators. It
does not read the data lake, publish catalog pointers, or execute research
runs.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any, Mapping, Sequence

from engine.factor_library import equity_core_factor_definitions
from engine.multifactor_contracts import FactorDirection


FACTOR_REGISTRY_SCHEMA = "factor_registry_v1"
ANOMALY_DISCOVERY_FACTOR_FAMILY = "anomaly_discovery_candidate"

STAGE3_MATURE_MULTIFACTOR_FACTOR_IDS = (
    "momentum_20d",
    "reversal_5d",
    "volatility_20d",
    "liquidity_adv20",
    "value_pb_inverse",
)

CHAPTER5_ANOMALY_PROXY_FACTOR_IDS = (
    "valuation_extreme_spread",
    "fundamental_anchor_reversal",
    "idiosyncratic_volatility_proxy",
)


class FactorAvailabilityStatus(str, Enum):
    DEFINED = "defined"
    CALCULABLE = "calculable"
    STAGE3_ACTIVE = "stage3_active"
    PROXY_ONLY = "proxy_only"
    DEPRECATED = "deprecated"
    BLOCKED = "blocked"


@dataclass(frozen=True, slots=True)
class FactorUsageRef:
    consumer: str
    purpose: str
    ref: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class FactorCatalogEntry:
    factor_id: str
    name: str
    category: str
    family: str
    direction: str
    input_fields: tuple[str, ...]
    formula: str
    source_refs: tuple[str, ...]
    status: str
    calculator_status: str
    used_by: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    notes: str = ""
    window: int | Mapping[str, Any] = 1
    required_factor_ids: tuple[str, ...] = ()
    source_dataset: str = ""
    schema_version: str = FACTOR_REGISTRY_SCHEMA

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["status"] = str(self.status)
        return data


def factor_catalog_entries(extra_entries: Sequence[FactorCatalogEntry] = ()) -> tuple[FactorCatalogEntry, ...]:
    return (
        *_core_catalog_entries(),
        *_stage3_catalog_entries(),
        *_chapter5_proxy_entries(),
        *tuple(extra_entries),
    )


def factor_catalog_entry_map(extra_entries: Sequence[FactorCatalogEntry] = ()) -> dict[str, FactorCatalogEntry]:
    return {entry.factor_id: entry for entry in factor_catalog_entries(extra_entries)}


def get_factor_catalog_entry(factor_id: str) -> FactorCatalogEntry:
    entries = factor_catalog_entry_map()
    if factor_id not in entries:
        raise KeyError(f"unknown factor_id: {factor_id}")
    return entries[factor_id]


def filter_factor_catalog_entries(
    *,
    status: str | FactorAvailabilityStatus | None = None,
    used_by: str | None = None,
    factor_id: str | None = None,
    extra_entries: Sequence[FactorCatalogEntry] = (),
) -> tuple[FactorCatalogEntry, ...]:
    entries = factor_catalog_entries(extra_entries)
    if factor_id:
        entry_map = factor_catalog_entry_map(extra_entries)
        if factor_id not in entry_map:
            raise KeyError(f"unknown factor_id: {factor_id}")
        return (entry_map[factor_id],)
    if status:
        status_value = status.value if isinstance(status, FactorAvailabilityStatus) else str(status)
        entries = tuple(entry for entry in entries if entry.status == status_value)
    if used_by:
        entries = tuple(entry for entry in entries if used_by in entry.used_by)
    return entries


def stage3_factor_catalog_entries(extra_entries: Sequence[FactorCatalogEntry] = ()) -> tuple[FactorCatalogEntry, ...]:
    entries = factor_catalog_entry_map(extra_entries)
    missing = [factor_id for factor_id in STAGE3_MATURE_MULTIFACTOR_FACTOR_IDS if factor_id not in entries]
    if missing:
        raise KeyError("stage3 factors missing from registry: " + ", ".join(missing))
    return tuple(entries[factor_id] for factor_id in STAGE3_MATURE_MULTIFACTOR_FACTOR_IDS)


def stage3_candidate_factor_catalog_entries(
    extra_entries: Sequence[FactorCatalogEntry] = (),
) -> tuple[FactorCatalogEntry, ...]:
    return tuple(entry for entry in extra_entries if "stage3_candidate" in entry.used_by)


def anomaly_candidate_catalog_entries(
    *,
    candidates: Sequence[Mapping[str, Any]],
    decisions: Sequence[Mapping[str, Any]],
) -> tuple[FactorCatalogEntry, ...]:
    """Convert admitted anomaly discovery candidates into catalog entries.

    This is an explicit dynamic bridge from a discovery artifact to the factor
    catalog. It does not mutate the default code registry or publish any data
    catalog pointer.
    """

    candidates_by_id = {str(item.get("anomaly_id")): item for item in candidates}
    entries: list[FactorCatalogEntry] = []
    for decision in decisions:
        status = str(decision.get("admission_status") or "")
        if status not in {"factor_catalog_candidate", "stage3_candidate"}:
            continue
        anomaly_id = str(decision.get("anomaly_id") or decision.get("factor_id"))
        candidate = candidates_by_id.get(anomaly_id)
        if not candidate:
            continue
        used_by = ["anomaly_discovery", "chapter5"]
        if status == "stage3_candidate":
            used_by.append("stage3_candidate")
        entries.append(
            FactorCatalogEntry(
                factor_id=str(decision.get("factor_id") or anomaly_id),
                name=str(candidate.get("name") or anomaly_id),
                category=str(candidate.get("source_type") or "anomaly"),
                family=ANOMALY_DISCOVERY_FACTOR_FAMILY,
                direction=str(candidate.get("expected_direction") or FactorDirection.POSITIVE.value),
                input_fields=tuple(candidate.get("input_fields") or candidate.get("required_factor_ids") or ()),
                formula=str(candidate.get("formula") or ""),
                source_refs=(str(candidate.get("prior_logic_ref") or "anomaly_discovery"),),
                status=FactorAvailabilityStatus.CALCULABLE.value,
                calculator_status="runner_local:engine.anomaly_candidate_generator.build_candidate_matrices_from_panel",
                used_by=tuple(used_by),
                evidence_refs=tuple(decision.get("evidence_refs") or ("engine.anomaly_discovery",)),
                notes="Dynamically admitted from controlled anomaly discovery; not persisted in the static registry.",
                required_factor_ids=tuple(candidate.get("required_factor_ids") or candidate.get("input_fields") or ()),
                source_dataset="anomaly_discovery_feature_panel",
            )
        )
    return tuple(entries)


def validate_factor_catalog(entries: Sequence[FactorCatalogEntry] | None = None) -> dict[str, tuple[str, ...]]:
    items = tuple(entries or factor_catalog_entries())
    allowed_status = {item.value for item in FactorAvailabilityStatus}
    allowed_direction = {item.value for item in FactorDirection}
    seen: set[str] = set()
    issues_by_factor: dict[str, tuple[str, ...]] = {}

    for entry in items:
        issues: list[str] = []
        if not entry.factor_id:
            issues.append("factor_id required")
        if entry.factor_id in seen:
            issues.append("factor_id duplicate")
        seen.add(entry.factor_id)
        if entry.status not in allowed_status:
            issues.append("status invalid")
        if entry.direction not in allowed_direction:
            issues.append("direction invalid")
        if not entry.name:
            issues.append("name required")
        if not entry.category:
            issues.append("category required")
        if not entry.family:
            issues.append("family required")
        if not entry.input_fields:
            issues.append("input_fields required")
        if not entry.formula:
            issues.append("formula required")
        if not entry.source_refs:
            issues.append("source_refs required")
        if not entry.calculator_status:
            issues.append("calculator_status required")
        if not entry.used_by:
            issues.append("used_by required")
        if entry.status == FactorAvailabilityStatus.PROXY_ONLY.value and not (
            entry.required_factor_ids or entry.notes
        ):
            issues.append("proxy_only requires required_factor_ids or notes")
        if issues:
            issues_by_factor[entry.factor_id or "<missing>"] = tuple(issues)
    return issues_by_factor


def _core_catalog_entries() -> tuple[FactorCatalogEntry, ...]:
    entries: list[FactorCatalogEntry] = []
    for definition in equity_core_factor_definitions():
        entries.append(
            FactorCatalogEntry(
                factor_id=definition.factor_id,
                name=definition.name,
                category=definition.category,
                family="equity_core",
                direction=definition.direction,
                input_fields=definition.input_fields,
                formula=definition.formula,
                source_refs=definition.source_refs,
                status=FactorAvailabilityStatus.CALCULABLE.value,
                calculator_status="engine.factor_calculators.core_equity_factor_calculators",
                used_by=("chapter3", "chapter6", "chapter7"),
                evidence_refs=("engine.factor_library", "engine.factor_calculators"),
                notes=definition.implementation_note,
                window=definition.default_window,
                source_dataset="research_input_v1",
            )
        )
    return tuple(entries)


def _stage3_catalog_entries() -> tuple[FactorCatalogEntry, ...]:
    return (
        FactorCatalogEntry(
            factor_id="momentum_20d",
            name="Momentum 20D",
            category="momentum",
            family="stage3_mature_multifactor",
            direction=FactorDirection.POSITIVE.value,
            input_fields=("adjusted_close",),
            formula="adjusted_close / lag(adjusted_close, 20) - 1",
            source_refs=("internal:stage3_mature_multifactor:factor_panel",),
            status=FactorAvailabilityStatus.STAGE3_ACTIVE.value,
            calculator_status="runner_local:engine.mature_multifactor_research.build_research_frame",
            used_by=("stage3", "stage3_mature_multifactor"),
            evidence_refs=("engine.mature_multifactor_research",),
            notes="Runner-local factor calculated from canonical prices inside Stage3 research.",
            window=20,
            source_dataset="prices",
        ),
        FactorCatalogEntry(
            factor_id="reversal_5d",
            name="Reversal 5D",
            category="reversal",
            family="stage3_mature_multifactor",
            direction=FactorDirection.POSITIVE.value,
            input_fields=("adjusted_close",),
            formula="-(adjusted_close / lag(adjusted_close, 5) - 1)",
            source_refs=("internal:stage3_mature_multifactor:factor_panel",),
            status=FactorAvailabilityStatus.STAGE3_ACTIVE.value,
            calculator_status="runner_local:engine.mature_multifactor_research.build_research_frame",
            used_by=("stage3", "stage3_mature_multifactor"),
            evidence_refs=("engine.mature_multifactor_research",),
            notes="Runner-local short-term reversal score.",
            window=5,
            source_dataset="prices",
        ),
        FactorCatalogEntry(
            factor_id="volatility_20d",
            name="Low Volatility 20D",
            category="volatility",
            family="stage3_mature_multifactor",
            direction=FactorDirection.POSITIVE.value,
            input_fields=("adjusted_close", "daily_return"),
            formula="-std(daily_return, 20)",
            source_refs=("internal:stage3_mature_multifactor:factor_panel",),
            status=FactorAvailabilityStatus.STAGE3_ACTIVE.value,
            calculator_status="runner_local:engine.mature_multifactor_research.build_research_frame",
            used_by=("stage3", "stage3_mature_multifactor"),
            evidence_refs=("engine.mature_multifactor_research",),
            notes="Positive direction means lower realized volatility scores higher after sign inversion.",
            window=20,
            source_dataset="prices",
        ),
        FactorCatalogEntry(
            factor_id="liquidity_adv20",
            name="Liquidity ADV20",
            category="liquidity",
            family="stage3_mature_multifactor",
            direction=FactorDirection.POSITIVE.value,
            input_fields=("adv20_amount",),
            formula="log1p(max(adv20_amount, 0))",
            source_refs=("internal:stage3_mature_multifactor:factor_panel",),
            status=FactorAvailabilityStatus.STAGE3_ACTIVE.value,
            calculator_status="runner_local:engine.mature_multifactor_research.build_research_frame",
            used_by=("stage3", "stage3_mature_multifactor"),
            evidence_refs=("engine.mature_multifactor_research",),
            notes="Runner consumes the published liquidity capacity field and does not compute a new lake dataset.",
            window=20,
            source_dataset="liquidity_capacity",
        ),
        FactorCatalogEntry(
            factor_id="value_pb_inverse",
            name="Value PB Inverse",
            category="value",
            family="stage3_mature_multifactor",
            direction=FactorDirection.POSITIVE.value,
            input_fields=("pb",),
            formula="-pb",
            source_refs=("internal:stage3_mature_multifactor:factor_panel",),
            status=FactorAvailabilityStatus.STAGE3_ACTIVE.value,
            calculator_status="runner_local:engine.mature_multifactor_research.build_research_frame",
            used_by=("stage3", "stage3_mature_multifactor"),
            evidence_refs=("engine.mature_multifactor_research",),
            notes="Proxy for cheaper valuation within the Stage3 mature multifactor runner.",
            window=1,
            source_dataset="market_cap",
        ),
    )


def _chapter5_proxy_entries() -> tuple[FactorCatalogEntry, ...]:
    return (
        FactorCatalogEntry(
            factor_id="valuation_extreme_spread",
            name="Valuation Extreme Spread",
            category="anomaly",
            family="chapter5_anomaly_proxy",
            direction=FactorDirection.CUSTOM.value,
            input_fields=("value_bm", "value_pb_inverse"),
            formula="cross_sectional_spread(high_valuation_proxy, low_valuation_proxy)",
            source_refs=("book:factor_investing:chapter5:anomaly_proxy",),
            status=FactorAvailabilityStatus.PROXY_ONLY.value,
            calculator_status="proxy_only:no_project_calculator",
            used_by=("chapter5",),
            evidence_refs=("engine.chapter5_anomalies",),
            notes="Conceptual anomaly proxy; requires a concrete valuation factor selection before calculation.",
            required_factor_ids=("value_bm", "value_pb_inverse"),
            source_dataset="factor_panel",
        ),
        FactorCatalogEntry(
            factor_id="fundamental_anchor_reversal",
            name="Fundamental Anchor Reversal",
            category="anomaly",
            family="chapter5_anomaly_proxy",
            direction=FactorDirection.CUSTOM.value,
            input_fields=("profitability_roe_ttm", "momentum_12_1", "reversal_5d"),
            formula="fundamental_quality_anchor - recent_price_extension",
            source_refs=("book:factor_investing:chapter5:anomaly_proxy",),
            status=FactorAvailabilityStatus.PROXY_ONLY.value,
            calculator_status="proxy_only:no_project_calculator",
            used_by=("chapter5",),
            evidence_refs=("engine.chapter5_anomalies",),
            notes="Proxy combines fundamental anchor and reversal concepts; not a registered calculator.",
            required_factor_ids=("profitability_roe_ttm", "momentum_12_1", "reversal_5d"),
            source_dataset="factor_panel",
        ),
        FactorCatalogEntry(
            factor_id="idiosyncratic_volatility_proxy",
            name="Idiosyncratic Volatility Proxy",
            category="anomaly",
            family="chapter5_anomaly_proxy",
            direction=FactorDirection.NEGATIVE.value,
            input_fields=("market_beta_252", "volatility_20d"),
            formula="residual_volatility_proxy_after_market_beta_control",
            source_refs=("book:factor_investing:chapter5:anomaly_proxy",),
            status=FactorAvailabilityStatus.PROXY_ONLY.value,
            calculator_status="proxy_only:no_project_calculator",
            used_by=("chapter5",),
            evidence_refs=("engine.chapter5_anomalies",),
            notes="Proxy only until residual volatility is calculated from a regression residual panel.",
            required_factor_ids=("market_beta_252", "volatility_20d"),
            source_dataset="factor_panel",
        ),
    )
