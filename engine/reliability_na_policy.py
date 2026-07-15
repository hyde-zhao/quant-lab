"""CR-170 canonical reliability N/A policy contract.

本模块只处理调用方显式传入的 fixture/static 元数据。它不读取文件、
凭据、授权系统、数据湖、运行时或外部服务，也不生成任何 Gate 状态。
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping


class NaEvidenceState(str, Enum):
    PRESENT = "PRESENT"
    MISSING = "MISSING"
    NA_WITH_COMPLETE_BOUNDARY = "NA_WITH_COMPLETE_BOUNDARY"
    NA_WITH_INCOMPLETE_BOUNDARY = "NA_WITH_INCOMPLETE_BOUNDARY"
    GENERIC_REASON_ESCAPE = "GENERIC_REASON_ESCAPE"


class HardeningDirection(str, Enum):
    STRICTER = "stricter"
    CONTROLLED_WIDENING = "controlled-widening"
    PRESERVE = "preserve"


class CompleteNaDisposition(str, Enum):
    REVIEWABLE = "reviewable"
    PROHIBITED = "prohibited"


@dataclass(frozen=True, slots=True)
class NaPolicySpec:
    policy_id: str
    gate_id: str
    evidence_keys: tuple[str, ...]
    reason_keys: tuple[str, ...]
    applicability_id: str
    owner: str
    baseline_path_type: str
    hardening_direction: HardeningDirection
    complete_na_disposition: CompleteNaDisposition


@dataclass(frozen=True, slots=True)
class NaBoundary:
    reason: str
    owner: str
    scope: str
    release_profile: str | None = None
    authorization_ref: str | None = None


@dataclass(frozen=True, slots=True)
class NaEvidenceDecision:
    policy_id: str
    state: NaEvidenceState
    applicable: bool
    reason_id: str
    boundary_complete: bool


_REASON_CATEGORIES = frozenset(
    {
        "missing",
        "generic_reason_escape",
        "boundary_incomplete",
        "complete_na_requires_review",
        "complete_na_not_permitted",
    }
)


def _policy(
    policy_id: str,
    gate_id: str,
    evidence_keys: tuple[str, ...],
    reason_keys: tuple[str, ...],
    applicability_id: str,
    baseline_path_type: str,
    direction: HardeningDirection,
    disposition: CompleteNaDisposition = CompleteNaDisposition.REVIEWABLE,
) -> NaPolicySpec:
    return NaPolicySpec(
        policy_id=policy_id,
        gate_id=gate_id,
        evidence_keys=evidence_keys,
        reason_keys=reason_keys,
        applicability_id=applicability_id,
        owner=gate_id,
        baseline_path_type=baseline_path_type,
        hardening_direction=direction,
        complete_na_disposition=disposition,
    )


NA_POLICY_SPECS: tuple[NaPolicySpec, ...] = (
    _policy(
        "G1-P01",
        "gate_1_statistical",
        ("multiple_testing_correction_refs",),
        ("multiple_testing_correction_na_reason",),
        "statistical-correction-required",
        "existing-reason-escape",
        HardeningDirection.STRICTER,
    ),
    _policy(
        "G1-P02",
        "gate_1_statistical",
        ("fdr_bh_refs",),
        ("fdr_bh_na_reason",),
        "fdr-correction-required",
        "existing-reason-escape",
        HardeningDirection.STRICTER,
    ),
    _policy(
        "G1-P03",
        "gate_1_statistical",
        ("white_reality_check_or_hansen_spa_refs",),
        ("white_reality_check_or_hansen_spa_na_reason", "wrc_spa_na_reason"),
        "data-snooping-correction-required",
        "missing-blocked-no-na",
        HardeningDirection.CONTROLLED_WIDENING,
    ),
    _policy(
        "G1-P04",
        "gate_1_statistical",
        ("pbo_or_cscv_refs",),
        ("pbo_or_cscv_na_reason",),
        "release-blocking-performance-robustness",
        "missing-blocked-no-na",
        HardeningDirection.CONTROLLED_WIDENING,
    ),
    _policy(
        "G1-P05",
        "gate_1_statistical",
        ("dsr_or_sharpe_ic_deflation_refs",),
        ("dsr_or_sharpe_ic_deflation_na_reason",),
        "sharpe-ic-reliability-claim",
        "missing-blocked-no-na",
        HardeningDirection.CONTROLLED_WIDENING,
    ),
    _policy(
        "G1-P06",
        "gate_1_statistical",
        ("trial_count_and_effective_trials",),
        ("trial_count_and_effective_trials_na_reason",),
        "trial-count-validation-required",
        "fixed-blocked-validation",
        HardeningDirection.PRESERVE,
        CompleteNaDisposition.PROHIBITED,
    ),
    _policy(
        "G2-P01",
        "gate_2_cv",
        ("split_policy_ref", "split_policy_refs"),
        ("split_policy_na_reason", "split_policy_n_a_reason"),
        "split-policy-required",
        "existing-reason-escape",
        HardeningDirection.STRICTER,
    ),
    _policy(
        "G2-P02",
        "gate_2_cv",
        ("walk_forward_ref", "walk_forward_refs"),
        ("walk_forward_na_reason", "walk_forward_n_a_reason"),
        "walk-forward-required",
        "existing-reason-escape",
        HardeningDirection.STRICTER,
    ),
    _policy(
        "G2-P03",
        "gate_2_cv",
        ("oos_ref", "oos_split_refs"),
        ("oos_na_reason", "oos_n_a_reason", "oos_split_na_reason"),
        "oos-required",
        "existing-reason-escape",
        HardeningDirection.STRICTER,
    ),
    _policy(
        "G2-P04",
        "gate_2_cv",
        ("purge_embargo_refs", "purge_window_ref", "purge_window_refs"),
        ("purge_embargo_na_reason", "purge_embargo_n_a_reason"),
        "overlap-requires-purge",
        "existing-reason-escape",
        HardeningDirection.STRICTER,
    ),
    _policy(
        "G2-P05",
        "gate_2_cv",
        ("embargo_gap_ref", "embargo_gap_refs"),
        ("embargo_gap_na_reason",),
        "overlapping-label-window",
        "missing-blocked-no-na",
        HardeningDirection.CONTROLLED_WIDENING,
    ),
    _policy(
        "G2-P06",
        "gate_2_cv",
        ("event_safe_gap_refs",),
        ("event_safe_gap_na_reason",),
        "overlapping-event-window",
        "missing-blocked-no-na",
        HardeningDirection.CONTROLLED_WIDENING,
    ),
    _policy(
        "G3-P01",
        "gate_3_pit_universe",
        ("pit_universe_refs", "cr153_universe_pit_audit_refs"),
        ("pit_universe_na_reason", "survivorship_free_universe_na_reason"),
        "pit-survivorship-contract-required",
        "existing-reason-escape",
        HardeningDirection.STRICTER,
    ),
    _policy(
        "G4-P01",
        "gate_4_capacity_impact",
        ("impact_model_family", "impact_model_ref"),
        ("impact_model_na_reason",),
        "impact-model-contract-required",
        "existing-structured-na-pass",
        HardeningDirection.STRICTER,
    ),
    _policy(
        "G4-P02",
        "gate_4_capacity_impact",
        ("adv_participation_ref",),
        ("adv_participation_ref_na_reason", "adv_participation_ref_n_a_reason"),
        "adv-participation-required",
        "existing-reason-escape",
        HardeningDirection.STRICTER,
    ),
    _policy(
        "G4-P03",
        "gate_4_capacity_impact",
        ("capacity_dollars_ref",),
        ("capacity_dollars_ref_na_reason", "capacity_dollars_ref_n_a_reason"),
        "capacity-dollars-required",
        "existing-reason-escape",
        HardeningDirection.STRICTER,
    ),
    _policy(
        "G4-P04",
        "gate_4_capacity_impact",
        ("liquidity_sizing_refs",),
        ("liquidity_sizing_refs_na_reason", "liquidity_sizing_refs_n_a_reason"),
        "liquidity-sizing-required",
        "existing-reason-escape",
        HardeningDirection.STRICTER,
    ),
    _policy(
        "G4-P05",
        "gate_4_capacity_impact",
        ("cost_underestimation_status",),
        ("cost_underestimation_na_reason",),
        "cost-underestimation-status-required",
        "existing-reason-escape",
        HardeningDirection.STRICTER,
    ),
    _policy(
        "G5-P01",
        "gate_5_regime_attribution_reconciliation",
        ("regime_slots",),
        ("regime_slots_na_reason", "regime_slots_n_a_reason"),
        "regime-slot-required",
        "structured-na-status-not-propagated",
        HardeningDirection.STRICTER,
    ),
    _policy(
        "G5-P02",
        "gate_5_regime_attribution_reconciliation",
        ("attribution_slots",),
        ("attribution_slots_na_reason", "attribution_slots_n_a_reason"),
        "attribution-slot-required",
        "structured-na-status-not-propagated",
        HardeningDirection.STRICTER,
    ),
    _policy(
        "G5-P03",
        "gate_5_regime_attribution_reconciliation",
        ("reconciliation_slots",),
        ("reconciliation_slots_na_reason", "reconciliation_slots_n_a_reason"),
        "reconciliation-slot-required",
        "structured-na-status-not-propagated",
        HardeningDirection.STRICTER,
    ),
)

NA_POLICY_BY_ID: Mapping[str, NaPolicySpec] = MappingProxyType(
    {policy.policy_id: policy for policy in NA_POLICY_SPECS}
)


def build_na_reason_id(policy: NaPolicySpec, category: str) -> str:
    """构造稳定的 policy reason ID。"""

    normalized_category = str(category or "").strip().lower()
    if normalized_category not in _REASON_CATEGORIES:
        raise ValueError(f"unsupported N/A reason category: {category!r}")
    gate_label = policy.gate_id.replace("gate_", "gate", 1).split("_", 1)[0]
    policy_label = policy.policy_id.lower().replace("-", "_")
    return f"{gate_label}_{policy_label}_{normalized_category}"


def classify_na_evidence(
    *,
    policy: NaPolicySpec,
    evidence_present: bool,
    applicable: bool,
    evidence: Mapping[str, Any],
    release_profile: str,
) -> NaEvidenceDecision:
    """按固定优先级分类一个 policy unit 的 N/A evidence 状态。"""

    if evidence_present:
        return NaEvidenceDecision(
            policy_id=policy.policy_id,
            state=NaEvidenceState.PRESENT,
            applicable=bool(applicable),
            reason_id="",
            boundary_complete=False,
        )

    boundaries = _as_mapping(evidence.get("n_a_boundaries"))
    raw_boundary = boundaries.get(policy.policy_id)
    if raw_boundary is not None:
        boundary = _boundary_from_value(raw_boundary)
        complete = _boundary_is_complete(
            boundary,
            policy=policy,
            release_profile=release_profile,
        )
        if complete:
            category = (
                "complete_na_not_permitted"
                if policy.complete_na_disposition is CompleteNaDisposition.PROHIBITED
                else "complete_na_requires_review"
            )
            state = NaEvidenceState.NA_WITH_COMPLETE_BOUNDARY
        else:
            category = "boundary_incomplete"
            state = NaEvidenceState.NA_WITH_INCOMPLETE_BOUNDARY
        return NaEvidenceDecision(
            policy_id=policy.policy_id,
            state=state,
            applicable=bool(applicable),
            reason_id=build_na_reason_id(policy, category),
            boundary_complete=complete,
        )

    if _has_generic_reason(evidence, policy):
        state = NaEvidenceState.GENERIC_REASON_ESCAPE
        category = "generic_reason_escape"
    else:
        state = NaEvidenceState.MISSING
        category = "missing"
    return NaEvidenceDecision(
        policy_id=policy.policy_id,
        state=state,
        applicable=bool(applicable),
        reason_id=build_na_reason_id(policy, category),
        boundary_complete=False,
    )


def _boundary_from_value(value: Any) -> NaBoundary:
    data = _as_mapping(value)
    return NaBoundary(
        reason=str(data.get("reason") or "").strip(),
        owner=str(data.get("owner") or "").strip(),
        scope=_normalize_scope(data.get("scope")),
        release_profile=str(data.get("release_profile") or "").strip() or None,
        authorization_ref=str(data.get("authorization_ref") or "").strip() or None,
    )


def _boundary_is_complete(
    boundary: NaBoundary,
    *,
    policy: NaPolicySpec,
    release_profile: str,
) -> bool:
    if not boundary.reason or boundary.owner != policy.owner:
        return False
    if policy.policy_id not in _scope_tokens(boundary.scope):
        return False
    return bool(
        boundary.authorization_ref
        or (
            boundary.release_profile
            and boundary.release_profile == str(release_profile or "").strip()
        )
    )


def _has_generic_reason(evidence: Mapping[str, Any], policy: NaPolicySpec) -> bool:
    candidates = (*policy.reason_keys, "n_a_reason", "na_reason")
    return any(bool(str(evidence.get(key) or "").strip()) for key in candidates)


def _normalize_scope(value: Any) -> str:
    if isinstance(value, (list, tuple, set, frozenset)):
        return " ".join(str(item).strip() for item in value if str(item).strip())
    return str(value or "").strip()


def _scope_tokens(value: str) -> frozenset[str]:
    normalized = value.replace(",", " ").replace(";", " ")
    return frozenset(item for item in normalized.split() if item)


def _as_mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}
