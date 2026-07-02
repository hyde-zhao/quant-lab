from __future__ import annotations

from engine.research_production_contracts import (
    EVENT_GATE_STATUS_BLOCKED,
    EVENT_GATE_STATUS_NEEDS_REVIEW,
    EVENT_GATE_STATUS_PASS,
    EventResearchSpec,
    EventTimeSemantics,
    ResearchDatasetSpec,
    build_event_revision_pit_gate,
    event_research_spec_from_mapping,
    validate_event_research_spec,
    validate_event_time_semantics,
)
from engine.event_strategy_contracts import (
    EVENT_AUDIT_SLOT_STATUS_DEFERRED_CR154,
    EVENT_AUDIT_SLOT_STATUS_NOT_APPLICABLE,
    EVENT_AUDIT_SLOT_STATUS_PRESENT,
    EVENT_STUDY_STATUS_BLOCKED,
    EVENT_STUDY_STATUS_FAIL,
    EVENT_STUDY_STATUS_NEEDS_REVIEW,
    EVENT_STUDY_STATUS_PASS,
    EventBiasAuditSlot,
    EventBiasRiskAuditSummary,
    EventCVSplitAuditRefs,
    EventEvidenceRef,
    EventReliabilityDeferredRef,
    EventStudyMethodSlot,
    EventStudyMethodSpec,
    EventStudyMultipleTestingSlot,
    EventStudyTestFamilySlot,
    EventStudyTestReport,
    EventStudyWindowSpec,
    NormalReturnModelSpec,
    UniversePITAuditSlot,
    validate_event_bias_audit_slot,
    validate_event_bias_risk_audit_summary,
    validate_event_cv_split_audit_refs,
    validate_event_multiple_testing_slot,
    validate_event_reliability_deferred_refs,
    validate_event_study_method_spec,
    validate_event_study_test_report,
    validate_universe_pit_audit,
)
from engine.event_strategy_admission_gate import (
    EVENT_GATE_LIMITATIONS,
    EventAdmissionGateStatus,
    evaluate_event_strategy_admission_gate,
    event_gate_summary,
    validate_event_gate_operation_counters,
)
from engine.strategy_admission_package import (
    MF_ADMISSION_EVENT_GATE_BLOCKED,
    AdmissionStatus,
    NotAuthorizedCounters,
    StrategyAdmissionPackage,
    attach_event_gate_to_admission_package,
    map_event_gate_status_to_admission_status,
    zero_not_authorized_counters,
)


def _dataset_spec() -> ResearchDatasetSpec:
    return ResearchDatasetSpec(
        spec_id="research-dataset-event-20260702",
        universe="csi300",
        start_date="2020-01-01",
        end_date="2026-07-01",
        as_of="2026-07-02",
        features=("event_surprise",),
        labels=("forward_return_5d",),
        output_snapshot_id="snapshot-event-20260702-v1",
        feature_artifact_refs=("event_feature_matrix_v1",),
        label_artifact_refs=("forward_return_5d",),
    )


def _time_semantics(**overrides: str) -> EventTimeSemantics:
    payload = {
        "event_occurred_at": "2026-06-30T15:00:00+08:00",
        "event_announced_at": "2026-07-01T08:00:00+08:00",
        "event_available_at": "2026-07-01T09:15:00+08:00",
        "decision_time": "2026-07-01T09:30:00+08:00",
        "timezone": "Asia/Shanghai",
        "calendar_ref": "calendar://fixture/cn-trading-v1",
    }
    payload.update(overrides)
    return EventTimeSemantics(**payload)


def _event_spec(**overrides: object) -> EventResearchSpec:
    payload: dict[str, object] = {
        "spec_id": "event-research-spec-20260702",
        "research_dataset_spec_id": "research-dataset-event-20260702",
        "event_id": "event-fixture-earnings-0001",
        "event_type": "earnings",
        "entity_id": "000001.SZ",
        "entity_id_field": "symbol",
        "source_snapshot_refs": ("snapshot://fixture/events/20260701-v1",),
        "revision_policy_ref": "policy://fixture/event-revision-policy-v1",
        "revision_source_refs": ("snapshot://fixture/events/revisions/20260701-v1",),
        "time_semantics": _time_semantics(),
    }
    payload.update(overrides)
    return EventResearchSpec(**payload)


def _issue_codes(issues: tuple[dict[str, object], ...]) -> set[str]:
    return {str(issue["code"]) for issue in issues}


def test_cr153_s01_event_time_semantics_serializes_all_independent_time_fields() -> None:
    payload = _time_semantics().to_dict()

    assert payload["event_occurred_at"] == "2026-06-30T15:00:00+08:00"
    assert payload["event_announced_at"] == "2026-07-01T08:00:00+08:00"
    assert payload["event_available_at"] == "2026-07-01T09:15:00+08:00"
    assert payload["decision_time"] == "2026-07-01T09:30:00+08:00"


def test_cr153_s01_event_research_spec_serializes_json_safe_refs_and_times() -> None:
    payload = _event_spec().to_dict()

    assert payload["source_snapshot_refs"] == ["snapshot://fixture/events/20260701-v1"]
    assert payload["revision_source_refs"] == ["snapshot://fixture/events/revisions/20260701-v1"]
    assert payload["time_semantics"]["event_available_at"] == "2026-07-01T09:15:00+08:00"
    assert all(value == 0 for value in payload["operation_counts"].values())


def test_cr153_s01_event_revision_pit_gate_passes_ordered_static_fixture() -> None:
    gate = build_event_revision_pit_gate(_event_spec(), research_dataset_spec=_dataset_spec())

    assert gate.status == EVENT_GATE_STATUS_PASS
    assert gate.passed is True
    assert gate.issues == ()
    assert all(value == 0 for value in gate.operation_counts.values())


def test_cr153_s01_event_available_after_decision_time_is_blocked() -> None:
    spec = _event_spec(time_semantics=_time_semantics(event_available_at="2026-07-01T10:00:00+08:00"))

    gate = build_event_revision_pit_gate(spec, research_dataset_spec=_dataset_spec())

    assert gate.status == EVENT_GATE_STATUS_BLOCKED
    assert "event_available_after_decision_time" in _issue_codes(gate.issues)


def test_cr153_s01_missing_event_available_at_is_blocked_and_never_inferred() -> None:
    time_semantics = _time_semantics(event_available_at="")

    issues = validate_event_time_semantics(time_semantics)
    gate = build_event_revision_pit_gate(_event_spec(time_semantics=time_semantics), research_dataset_spec=_dataset_spec())

    assert gate.status == EVENT_GATE_STATUS_BLOCKED
    assert _issue_codes(issues) >= {
        "event_available_at_missing",
        "event_available_at_inference_forbidden",
    }
    assert "event_available_after_decision_time" not in _issue_codes(issues)


def test_cr153_s01_announced_before_decision_cannot_substitute_missing_availability() -> None:
    time_semantics = _time_semantics(
        event_announced_at="2026-07-01T08:00:00+08:00",
        event_available_at="",
        decision_time="2026-07-01T09:30:00+08:00",
    )

    gate = build_event_revision_pit_gate(_event_spec(time_semantics=time_semantics), research_dataset_spec=_dataset_spec())

    assert gate.status == EVENT_GATE_STATUS_BLOCKED
    assert "event_available_at_inference_forbidden" in _issue_codes(gate.issues)


def test_cr153_s01_missing_revision_policy_defaults_to_blocked() -> None:
    gate = build_event_revision_pit_gate(
        _event_spec(revision_policy_ref="", revision_policy_na_reason=""),
        research_dataset_spec=_dataset_spec(),
    )

    assert gate.status == EVENT_GATE_STATUS_BLOCKED
    assert "event_revision_policy_missing" in _issue_codes(gate.issues)


def test_cr153_s01_explicit_revision_policy_na_reason_is_needs_review_not_pass() -> None:
    gate = build_event_revision_pit_gate(
        _event_spec(
            revision_policy_ref="",
            revision_policy_na_reason="Fixture source is immutable by construction for this static event family.",
        ),
        research_dataset_spec=_dataset_spec(),
    )

    assert gate.status == EVENT_GATE_STATUS_NEEDS_REVIEW
    assert gate.passed is False
    assert "event_revision_policy_needs_review" in _issue_codes(gate.issues)


def test_cr153_s01_mutable_latest_current_source_refs_are_blocked() -> None:
    spec = _event_spec(source_snapshot_refs=("catalog://current/events",))

    gate = build_event_revision_pit_gate(spec, research_dataset_spec=_dataset_spec())

    assert gate.status == EVENT_GATE_STATUS_BLOCKED
    assert "event_mutable_source_ref_forbidden" in _issue_codes(gate.issues)


def test_cr153_s01_forbidden_operation_counter_nonzero_is_blocked() -> None:
    spec = _event_spec(operation_counts={"real_event_feed_read": 1})

    gate = build_event_revision_pit_gate(spec, research_dataset_spec=_dataset_spec())

    assert gate.status == EVENT_GATE_STATUS_BLOCKED
    assert "event_forbidden_operation_counter_nonzero" in _issue_codes(gate.issues)


def test_cr153_s01_anchor_mismatch_is_blocked() -> None:
    spec = _event_spec(research_dataset_spec_id="research-dataset-other")

    issues = validate_event_research_spec(spec, research_dataset_spec=_dataset_spec())

    assert "event_research_dataset_spec_id_mismatch" in _issue_codes(issues)


def test_cr153_s01_event_research_spec_from_mapping_preserves_explicit_availability() -> None:
    spec = event_research_spec_from_mapping(_event_spec().to_dict())

    assert spec.time_semantics.event_available_at == "2026-07-01T09:15:00+08:00"
    assert build_event_revision_pit_gate(spec, research_dataset_spec=_dataset_spec()).status == EVENT_GATE_STATUS_PASS


# CR153-S02 event study method, test family and EV-GAP-7 slots.


def _s02_method_slot(method_name: str, *, status: str = EVENT_STUDY_STATUS_PASS) -> EventStudyMethodSlot:
    return EventStudyMethodSlot(
        method_name=method_name,
        status=status,
        support_level="slot_only",
        report_ref=f"report://fixture/cr153/s02/{method_name}",
        limitations=("metadata-only",),
    )


def _s02_method_spec(**overrides: object) -> EventStudyMethodSpec:
    payload: dict[str, object] = {
        "method_id": "event-study-method-20260702",
        "event_research_spec_id": "event-research-spec-20260702",
        "estimation_window": EventStudyWindowSpec(
            window_id="estimation-minus-120-minus-20",
            relative_start=-120,
            relative_end=-20,
            trading_calendar_ref="calendar://fixture/cn-trading-v1",
        ),
        "event_window": EventStudyWindowSpec(
            window_id="event-minus-1-plus-1",
            relative_start=-1,
            relative_end=1,
            trading_calendar_ref="calendar://fixture/cn-trading-v1",
        ),
        "normal_return_model": NormalReturnModelSpec(
            model_id="market-model-fixture",
            model_type="market_model",
            market_benchmark_ref="benchmark://fixture/csi300",
            estimation_method="ols_ref_only",
        ),
        "return_horizon": "[-1,+1]",
        "car_method_slot": _s02_method_slot("car"),
        "bhar_method_slot": _s02_method_slot("bhar", status=EVENT_STUDY_STATUS_NEEDS_REVIEW),
        "calendar_time_method_slot": _s02_method_slot("calendar_time", status=EVENT_STUDY_STATUS_NEEDS_REVIEW),
        "method_ref": "method://fixture/event-study/spec-v1",
    }
    payload.update(overrides)
    return EventStudyMethodSpec(**payload)


def _s02_family_slot(family_id: str, *, status: str = EVENT_STUDY_STATUS_PASS) -> EventStudyTestFamilySlot:
    return EventStudyTestFamilySlot(
        family_id=family_id,
        status=status,
        sample_count=42,
        raw_p_value=0.04 if status in {EVENT_STUDY_STATUS_PASS, EVENT_STUDY_STATUS_FAIL} else None,
        adjusted_p_value=0.048 if status in {EVENT_STUDY_STATUS_PASS, EVENT_STUDY_STATUS_FAIL} else None,
        report_ref=f"report://fixture/cr153/s02/{family_id}",
        n_a_reason="" if status in {EVENT_STUDY_STATUS_PASS, EVENT_STUDY_STATUS_FAIL} else "slot-only deferred fixture",
    )


def _s02_multiple_slot(**overrides: object) -> EventStudyMultipleTestingSlot:
    payload: dict[str, object] = {
        "family_id": "event_window_family",
        "tested_window_count": 5,
        "correction_method": "holm",
        "adjusted_p_value": 0.048,
        "status": EVENT_STUDY_STATUS_PASS,
        "report_ref": "report://fixture/cr153/s02/multiple-testing",
    }
    payload.update(overrides)
    return EventStudyMultipleTestingSlot(**payload)


def _s02_test_report(**overrides: object) -> EventStudyTestReport:
    payload: dict[str, object] = {
        "report_id": "event-study-test-report-20260702",
        "method_id": "event-study-method-20260702",
        "test_family_slots": (
            _s02_family_slot("patell"),
            _s02_family_slot("bmp"),
            _s02_family_slot("generalized_sign"),
            _s02_family_slot("rank"),
            _s02_family_slot("bootstrap", status=EVENT_STUDY_STATUS_NEEDS_REVIEW),
        ),
        "multiple_testing_or_data_snooping_slot": _s02_multiple_slot(),
        "sample_count": 42,
    }
    payload.update(overrides)
    return EventStudyTestReport(**payload)


def _s02_issue_codes(issues: tuple[object, ...]) -> set[str]:
    return {str(issue.to_dict()["code"]) for issue in issues}


def test_cr153_s02_event_study_method_spec_serializes_required_method_slots() -> None:
    payload = _s02_method_spec().to_dict()

    assert validate_event_study_method_spec(payload) == ()
    assert payload["estimation_window"]["window_id"] == "estimation-minus-120-minus-20"
    assert payload["event_window"]["window_id"] == "event-minus-1-plus-1"
    assert payload["normal_return_model"]["model_type"] == "market_model"
    assert payload["return_horizon"] == "[-1,+1]"
    assert payload["car_method_slot"]["method_name"] == "car"
    assert payload["bhar_method_slot"]["method_name"] == "bhar"
    assert payload["calendar_time_method_slot"]["method_name"] == "calendar_time"


def test_cr153_s02_missing_method_evidence_is_blocked() -> None:
    issues = validate_event_study_method_spec(
        {
            "method_id": "ordinary-forward-return-only",
            "event_research_spec_id": "event-research-spec-20260702",
            "forward_return_days": 5,
        }
    )

    assert _s02_issue_codes(issues) >= {
        "event_study_estimation_window_missing",
        "event_study_event_window_missing",
        "event_study_normal_return_model_missing",
        "event_study_return_horizon_missing",
        "event_study_method_slot_missing",
        "event_study_method_ref_or_na_missing",
    }
    assert all(issue.status == EVENT_STUDY_STATUS_BLOCKED for issue in issues)


def test_cr153_s02_event_study_test_report_serializes_required_family_and_multiple_testing_slots() -> None:
    payload = _s02_test_report().to_dict()

    assert validate_event_study_test_report(payload) == ()
    family_ids = {slot["family_id"] for slot in payload["test_family_slots"]}
    assert family_ids == {"patell", "bmp", "generalized_sign", "rank", "bootstrap"}
    assert payload["multiple_testing_or_data_snooping_slot"]["family_id"] == "event_window_family"
    assert payload["multiple_testing_or_data_snooping_slot"]["tested_window_count"] == 5
    assert payload["multiple_testing_or_data_snooping_slot"]["correction_method"] == "holm"
    assert payload["multiple_testing_or_data_snooping_slot"]["adjusted_p_value"] == 0.048


def test_cr153_s02_missing_test_family_or_multiple_testing_slot_is_blocked() -> None:
    issues = validate_event_study_test_report(
        _s02_test_report(
            test_family_slots=(),
            multiple_testing_or_data_snooping_slot=None,
        )
    )

    assert _s02_issue_codes(issues) >= {
        "event_study_test_family_slots_missing",
        "event_study_test_family_slot_missing",
        "event_study_multiple_testing_slot_missing",
    }
    assert all(issue.status == EVENT_STUDY_STATUS_BLOCKED for issue in issues)


def test_cr153_s02_multiple_testing_slot_requires_ref_or_na_reason_and_valid_p_value() -> None:
    issues = validate_event_multiple_testing_slot(
        _s02_multiple_slot(
            adjusted_p_value=1.2,
            report_ref="",
            n_a_reason="",
        )
    )

    assert _s02_issue_codes(issues) >= {
        "event_study_adjusted_p_value_invalid",
        "event_study_multiple_testing_report_ref_or_na_missing",
    }
    assert all(issue.status == EVENT_STUDY_STATUS_BLOCKED for issue in issues)


def test_cr153_s02_deferred_algorithms_are_slot_only_and_active_claim_is_blocked() -> None:
    issues = validate_event_multiple_testing_slot(
        _s02_multiple_slot(
            correction_method="white_reality_check",
            implementation_state="implemented",
            status=EVENT_STUDY_STATUS_PASS,
        )
    )

    assert "event_study_unsupported_algorithm_active" in _s02_issue_codes(issues)
    assert all(issue.status == EVENT_STUDY_STATUS_BLOCKED for issue in issues)


def test_cr153_s02_forbidden_operation_counter_nonzero_is_blocked() -> None:
    issues = validate_event_study_test_report(
        _s02_test_report(operation_counts={"provider_fetch": 1, "real_data_validation": 1})
    )

    assert "event_study_forbidden_operation_nonzero" in _s02_issue_codes(issues)
    assert all(issue.status == EVENT_STUDY_STATUS_BLOCKED for issue in issues)


def test_cr153_s02_field_partition_does_not_define_s03_bias_audit_slots() -> None:
    payload = _s02_test_report().to_dict()
    forbidden_s03_fields = {
        "overlap_report_slot",
        "cluster_report_slot",
        "endogeneity_treatment_slot",
        "event_cv_split_audit_refs",
        "universe_pit_audit",
        "capacity_ref",
        "impact_ref",
        "regime_ref",
        "reconciliation_ref",
    }

    assert forbidden_s03_fields.isdisjoint(payload)
    assert forbidden_s03_fields.isdisjoint(_s02_method_spec().to_dict())


# CR153-S03 bias, event CV, universe PIT and CR154 deferred reliability slots.


def _s03_ref(ref_id: str, *, kind: str = "static_fixture") -> EventEvidenceRef:
    return EventEvidenceRef(
        ref_id=ref_id,
        kind=kind,
        path_or_id=f"fixture://cr153/s03/{ref_id}",
        description=f"CR153 S03 static fixture ref {ref_id}",
    )


def _s03_overlap_slot(**overrides: object) -> EventBiasAuditSlot:
    payload: dict[str, object] = {
        "slot_name": "overlap_report_slot",
        "status": EVENT_AUDIT_SLOT_STATUS_PRESENT,
        "evidence_refs": (_s03_ref("overlap-report-v1"),),
        "limitations": ("overlap visibility only; no covariance correction",),
    }
    payload.update(overrides)
    return EventBiasAuditSlot(**payload)


def _s03_cluster_slot(**overrides: object) -> EventBiasAuditSlot:
    payload: dict[str, object] = {
        "slot_name": "cluster_report_slot",
        "status": EVENT_AUDIT_SLOT_STATUS_NOT_APPLICABLE,
        "evidence_refs": (),
        "n_a_reason": "Static single-issuer fixture does not exercise cross-entity clustering.",
        "cluster_dimensions": ("entity", "date", "event_type"),
        "limitations": ("No cluster robust variance or two-way clustering is implemented in CR153.",),
    }
    payload.update(overrides)
    return EventBiasAuditSlot(**payload)


def _s03_endogeneity_slot(**overrides: object) -> EventBiasAuditSlot:
    payload: dict[str, object] = {
        "slot_name": "endogeneity_treatment_slot",
        "status": EVENT_AUDIT_SLOT_STATUS_DEFERRED_CR154,
        "evidence_refs": (),
        "deferred_to": "CR154",
        "deferred_reason": "PSM/IV/matching/Heckman causal treatment governance is deferred to CR154.",
        "limitations": ("Self-selection treatment visibility only.",),
        "treatment_family": "deferred_matching",
    }
    payload.update(overrides)
    return EventBiasAuditSlot(**payload)


def _s03_cv_refs(**overrides: object) -> EventCVSplitAuditRefs:
    payload: dict[str, object] = {
        "status": EVENT_AUDIT_SLOT_STATUS_PRESENT,
        "split_audit_refs": (_s03_ref("cv-split-audit-v1"),),
        "limitations": ("Static split audit refs only; no fold generation, PBO or DSR.",),
    }
    payload.update(overrides)
    return EventCVSplitAuditRefs(**payload)


def _s03_universe_audit(**overrides: object) -> UniversePITAuditSlot:
    payload: dict[str, object] = {
        "status": EVENT_AUDIT_SLOT_STATUS_DEFERRED_CR154,
        "universe_snapshot_refs": (_s03_ref("universe-snapshot-v1"),),
        "pit_policy_ref": _s03_ref("universe-pit-policy-v1", kind="policy"),
        "deferred_to": "CR154",
        "deferred_reason": "Full survivorship-free universe gate is deferred to CR154.",
        "limitations": ("Universe PIT audit visibility only.",),
    }
    payload.update(overrides)
    return UniversePITAuditSlot(**payload)


def _s03_deferred_refs() -> tuple[EventReliabilityDeferredRef, ...]:
    return tuple(
        EventReliabilityDeferredRef(
            risk_area=risk_area,
            follow_up_ref=f"CR154-{risk_area}-governance",
            n_a_reason=f"{risk_area} reliability governance is explicitly deferred to CR154.",
            deferred_reason=f"CR153 first wave records {risk_area} handoff risk only.",
            limitations=(f"No {risk_area} governance implementation in CR153.",),
        )
        for risk_area in ("capacity", "impact", "regime", "reconciliation")
    )


def _s03_summary(**overrides: object) -> EventBiasRiskAuditSummary:
    payload: dict[str, object] = {
        "summary_id": "event-bias-risk-audit-summary-20260702",
        "event_study_report_ref": "report://fixture/cr153/s02/event-study-test-report-20260702",
        "overlap_report_slot": _s03_overlap_slot(),
        "cluster_report_slot": _s03_cluster_slot(),
        "endogeneity_treatment_slot": _s03_endogeneity_slot(),
        "event_cv_split_audit_refs": _s03_cv_refs(),
        "universe_pit_audit": _s03_universe_audit(),
        "reliability_deferred_refs": _s03_deferred_refs(),
    }
    payload.update(overrides)
    return EventBiasRiskAuditSummary(**payload)


def _s03_issue_codes(issues: tuple[object, ...]) -> set[str]:
    return {str(issue.to_dict()["code"]) for issue in issues}


def test_cr153_s03_complete_bias_risk_audit_summary_serializes_static_slots() -> None:
    payload = _s03_summary().to_dict()

    assert validate_event_bias_risk_audit_summary(payload) == ()
    assert payload["overlap_report_slot"]["status"] == EVENT_AUDIT_SLOT_STATUS_PRESENT
    assert payload["cluster_report_slot"]["status"] == EVENT_AUDIT_SLOT_STATUS_NOT_APPLICABLE
    assert payload["endogeneity_treatment_slot"]["deferred_to"] == "CR154"
    assert payload["event_cv_split_audit_refs"]["split_audit_refs"][0]["ref_id"] == "cv-split-audit-v1"
    assert payload["universe_pit_audit"]["pit_policy_ref"]["ref_id"] == "universe-pit-policy-v1"
    assert {ref["risk_area"] for ref in payload["reliability_deferred_refs"]} == {
        "capacity",
        "impact",
        "regime",
        "reconciliation",
    }


def test_cr153_s03_present_overlap_slot_without_refs_is_blocked() -> None:
    issues = validate_event_bias_audit_slot(_s03_overlap_slot(evidence_refs=()))

    assert "event_audit_present_refs_missing" in _s03_issue_codes(issues)
    assert all(issue.status == EVENT_STUDY_STATUS_BLOCKED for issue in issues)


def test_cr153_s03_cluster_not_applicable_requires_reason() -> None:
    issues = validate_event_bias_audit_slot(_s03_cluster_slot(n_a_reason=""))

    assert "event_audit_not_applicable_reason_missing" in _s03_issue_codes(issues)
    assert all(issue.status == EVENT_STUDY_STATUS_BLOCKED for issue in issues)


def test_cr153_s03_endogeneity_deferred_requires_cr154_and_reason() -> None:
    issues = validate_event_bias_audit_slot(
        _s03_endogeneity_slot(deferred_to="", deferred_reason="", n_a_reason="", limitations=())
    )

    assert _s03_issue_codes(issues) >= {
        "event_audit_deferred_to_cr154_missing",
        "event_audit_deferred_reason_missing",
    }
    assert all(issue.status == EVENT_STUDY_STATUS_BLOCKED for issue in issues)


def test_cr153_s03_event_cv_split_refs_are_static_refs_only() -> None:
    payload = _s03_cv_refs().to_dict()

    assert validate_event_cv_split_audit_refs(payload) == ()
    assert payload["split_audit_refs"][0]["path_or_id"].startswith("fixture://")
    assert "fold" not in payload
    assert "pbo" not in payload
    assert "dsr" not in payload


def test_cr153_s03_event_cv_missing_refs_requires_na_or_deferred_reason() -> None:
    issues = validate_event_cv_split_audit_refs(
        _s03_cv_refs(split_audit_refs=(), n_a_reason="", deferred_reason="", limitations=())
    )

    assert "event_audit_present_refs_missing" in _s03_issue_codes(issues)
    assert all(issue.status == EVENT_STUDY_STATUS_BLOCKED for issue in issues)


def test_cr153_s03_universe_pit_audit_is_visible_without_survivorship_gate_claim() -> None:
    payload = _s03_universe_audit().to_dict()

    assert validate_universe_pit_audit(payload) == ()
    assert payload["status"] == EVENT_AUDIT_SLOT_STATUS_DEFERRED_CR154
    assert payload["deferred_to"] == "CR154"
    assert "survivorship-free universe gate is deferred" in payload["deferred_reason"]


def test_cr153_s03_deferred_reliability_refs_cannot_be_omitted() -> None:
    refs = [ref for ref in _s03_deferred_refs() if ref.risk_area != "capacity"]
    issues = validate_event_reliability_deferred_refs(refs)

    assert "event_reliability_deferred_ref_missing" in _s03_issue_codes(issues)
    assert all(issue.status == EVENT_STUDY_STATUS_BLOCKED for issue in issues)


def test_cr153_s03_deferred_reliability_refs_must_point_to_cr154() -> None:
    refs = list(_s03_deferred_refs())
    refs[0] = EventReliabilityDeferredRef(
        risk_area="capacity",
        status=EVENT_AUDIT_SLOT_STATUS_PRESENT,
        deferred_to="",
        follow_up_ref="CR154-capacity-governance",
        n_a_reason="capacity reliability governance is explicitly deferred to CR154.",
    )

    issues = validate_event_reliability_deferred_refs(refs)

    assert "event_reliability_deferred_ref_status_invalid" in _s03_issue_codes(issues)
    assert all(issue.status == EVENT_STUDY_STATUS_BLOCKED for issue in issues)


def test_cr153_s03_forbidden_operation_counter_nonzero_blocks_summary() -> None:
    issues = validate_event_bias_risk_audit_summary(
        _s03_summary(operation_counts={"real_event_feed_read": 1, "event_store_write": 1})
    )

    assert "event_study_forbidden_operation_nonzero" in _s03_issue_codes(issues)
    assert all(issue.status == EVENT_STUDY_STATUS_BLOCKED for issue in issues)


def test_cr153_s03_validators_keep_s02_method_and_test_fields_read_only() -> None:
    method_payload = _s02_method_spec().to_dict()
    report_payload = _s02_test_report().to_dict()
    summary_payload = _s03_summary(event_study_report_ref=report_payload["report_id"]).to_dict()

    assert validate_event_study_method_spec(method_payload) == ()
    assert validate_event_study_test_report(report_payload) == ()
    assert validate_event_bias_risk_audit_summary(summary_payload) == ()
    assert {
        "overlap_report_slot",
        "cluster_report_slot",
        "endogeneity_treatment_slot",
        "event_cv_split_audit_refs",
        "universe_pit_audit",
    }.issubset(summary_payload)
    assert "multiple_testing_or_data_snooping_slot" not in summary_payload


# CR153-S04 event admission gate and package adapter.


def _s04_trace_evidence(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "status": "PASS",
        "trace_ref": "trace://fixture/cr153/s04/event-to-signal-v1",
        "event_to_signal_ref": "trace://fixture/cr153/s04/event-to-signal-v1",
        "signal_to_order_intent_ref": "trace://fixture/cr153/s04/signal-to-order-intent-v1",
        "evidence_refs": (
            "trace://fixture/cr153/s04/event-to-signal-v1",
            "trace://fixture/cr153/s04/signal-to-order-intent-v1",
        ),
        "limitations": ("trace metadata only; no order flow",),
    }
    payload.update(overrides)
    return payload


def _s04_gate(**overrides: object):
    payload: dict[str, object] = {
        "pit_gate": build_event_revision_pit_gate(_event_spec(), research_dataset_spec=_dataset_spec()),
        "method_spec": _s02_method_spec(
            bhar_method_slot=_s02_method_slot("bhar"),
            calendar_time_method_slot=_s02_method_slot("calendar_time"),
        ),
        "test_report": _s02_test_report(
            test_family_slots=(
                _s02_family_slot("patell"),
                _s02_family_slot("bmp"),
                _s02_family_slot("generalized_sign"),
                _s02_family_slot("rank"),
                _s02_family_slot("bootstrap"),
            )
        ),
        "multiple_testing_slot": _s02_multiple_slot(),
        "bias_risk_audit": _s03_summary(),
        "trace_evidence": _s04_trace_evidence(),
        "operation_counts": {},
        "gate_ref": "gate://fixture/cr153/s04/event-admission-v1",
    }
    payload.update(overrides)
    return evaluate_event_strategy_admission_gate(**payload)


def _s04_issue_codes(gate) -> set[str]:
    return {str(issue["code"]) for issue in gate.to_dict()["blocked_reasons"] + gate.to_dict()["needs_review_reasons"]}


def _s04_package() -> StrategyAdmissionPackage:
    return StrategyAdmissionPackage(
        package_id="strategy-admission:event-fixture",
        strategy_id="strategy-event-fixture",
        run_id="run-event-fixture",
        admission_status=AdmissionStatus.PASS,
        evidence_refs=("fixture://existing/package-evidence",),
        blocked_reasons=(),
        unlock_conditions=(),
        stage6_gate_summary={"status": "pass", "passed": True},
        portfolio_plan_ref={"plan_id": "event-plan-fixture"},
        manifest_ref={"run_id": "run-event-fixture"},
        catalog_ref={"catalog_entry_id": "event-catalog-fixture"},
        order_intent_draft_ref={
            "schema_version": "order_intent_draft_v1",
            "draft_id": "draft-event-fixture",
            "path_or_ref": "fixture://draft/event",
            "limitations": ("draft only",),
        },
        not_authorized_counters=zero_not_authorized_counters(),
        allowed_claims=(),
        blocked_claims=(),
        limitations=(
            "not_qmt_authorization",
            "not_simulation_authorization",
            "not_live_authorization",
            "not_broker_order",
        ),
        pre_sim_strategy_preparation={"status": "fixture"},
    )


def test_cr153_s04_event_gate_pass_static_fixture_keeps_limitations() -> None:
    gate = _s04_gate()
    payload = gate.to_dict()

    assert gate.status is EventAdmissionGateStatus.PASS
    assert payload["gate_present"] is True
    assert payload["gate_required"] is True
    assert payload["gate_status"] == "PASS"
    assert payload["gate_ref"] == "gate://fixture/cr153/s04/event-admission-v1"
    assert payload["blocked_reasons"] == []
    assert all(value == 0 for value in payload["operation_counts"].values())
    assert set(EVENT_GATE_LIMITATIONS).issubset(set(payload["limitations"]))
    assert "trace://fixture/cr153/s04/event-to-signal-v1" in payload["evidence_refs"]


def test_cr153_s04_missing_mandatory_evidence_blocks_by_field() -> None:
    cases = (
        (
            {"pit_gate": None},
            "event_gate_pit_evidence_missing",
        ),
        (
            {"method_spec": None},
            "event_gate_method_evidence_missing",
        ),
        (
            {"test_report": None},
            "event_gate_test_family_evidence_missing",
        ),
        (
            {"test_report": _s02_test_report(multiple_testing_or_data_snooping_slot=None), "multiple_testing_slot": None},
            "event_gate_multiple_testing_evidence_missing",
        ),
        (
            {"trace_evidence": None},
            "event_gate_trace_evidence_missing",
        ),
    )

    for overrides, expected_code in cases:
        gate = _s04_gate(**overrides)
        assert gate.status is EventAdmissionGateStatus.BLOCKED
        assert expected_code in _s04_issue_codes(gate)


def test_cr153_s04_forbidden_counter_nonzero_or_noninteger_blocks() -> None:
    gate = _s04_gate(operation_counts={"provider_fetch": 1, "event_store_write": "bad"})
    issues = validate_event_gate_operation_counters({"real_order": 1, "credential_read": "bad"})

    assert gate.status is EventAdmissionGateStatus.BLOCKED
    assert {"provider_fetch", "event_store_write"} <= {
        str(reason["field"]) for reason in gate.to_dict()["blocked_reasons"]
    }
    assert {issue.field for issue in issues} == {"real_order", "credential_read"}


def test_cr153_s04_status_priority_blocked_fail_review_pass() -> None:
    blocked = _s04_gate(operation_counts={"real_order": 1}, trace_evidence=_s04_trace_evidence(status="FAIL"))
    failed = _s04_gate(trace_evidence=_s04_trace_evidence(status="FAIL"))
    needs_review = _s04_gate(trace_evidence=_s04_trace_evidence(status="NEEDS_REVIEW"))
    passed = _s04_gate()

    assert blocked.status is EventAdmissionGateStatus.BLOCKED
    assert failed.status is EventAdmissionGateStatus.FAIL
    assert needs_review.status is EventAdmissionGateStatus.NEEDS_REVIEW
    assert passed.status is EventAdmissionGateStatus.PASS


def test_cr153_s04_unknown_status_fails_closed_to_blocked() -> None:
    gate = _s04_gate(trace_evidence=_s04_trace_evidence(status="MAYBE_READY"))
    summary = event_gate_summary({"gate_status": "SOMETHING_ELSE"})

    assert gate.status is EventAdmissionGateStatus.BLOCKED
    assert "event_gate_unknown_input_status" in _s04_issue_codes(gate)
    assert summary["gate_status"] == "BLOCKED"
    assert any(reason["code"] == "event_gate_unknown_status" for reason in summary["blocked_reasons"])


def test_cr153_s04_event_gate_summary_shape_is_stable() -> None:
    summary = event_gate_summary(_s04_gate())

    assert {
        "schema_version",
        "gate_present",
        "gate_required",
        "gate_status",
        "status",
        "gate_ref",
        "blocked_reasons",
        "needs_review_reasons",
        "evidence_refs",
        "operation_counts",
        "limitations",
    }.issubset(summary)


def test_cr153_s04_event_status_adapter_maps_four_states_and_unknown() -> None:
    assert map_event_gate_status_to_admission_status("PASS") is AdmissionStatus.PASS
    assert map_event_gate_status_to_admission_status("FAIL") is AdmissionStatus.FAIL
    assert map_event_gate_status_to_admission_status("NEEDS_REVIEW") is AdmissionStatus.WARN
    assert map_event_gate_status_to_admission_status("BLOCKED") is AdmissionStatus.BLOCKED
    assert map_event_gate_status_to_admission_status("unknown") is AdmissionStatus.BLOCKED


def test_cr153_s04_package_linkage_pass_does_not_authorize_runtime_or_clear_claims() -> None:
    payload = attach_event_gate_to_admission_package(_s04_package(), event_gate_summary(_s04_gate()))

    assert payload["event_gate_status"] == "PASS"
    assert payload["event_gate_present"] is True
    assert payload["event_gate_required"] is True
    assert payload["event_gate_ref"] == "gate://fixture/cr153/s04/event-admission-v1"
    assert payload["not_qmt_authorization"] is True
    assert payload["not_simulation_authorization"] is True
    assert payload["not_live_authorization"] is True
    assert payload["not_broker_order"] is True
    assert "event_gate_pass_not_runtime_ready" in payload["limitations"]
    assert any(claim["claim"] == "event_gate_pass_not_runtime_ready" for claim in payload["blocked_claims"])
    assert "trace://fixture/cr153/s04/event-to-signal-v1" in payload["evidence_refs"]


def test_cr153_s04_package_linkage_non_pass_degrades_status_and_appends_reason() -> None:
    failed_payload = attach_event_gate_to_admission_package(
        _s04_package(),
        event_gate_summary(_s04_gate(trace_evidence=_s04_trace_evidence(status="FAIL"))),
    )
    review_payload = attach_event_gate_to_admission_package(
        _s04_package(),
        event_gate_summary(_s04_gate(trace_evidence=_s04_trace_evidence(status="NEEDS_REVIEW"))),
    )
    blocked_payload = attach_event_gate_to_admission_package(
        _s04_package(),
        event_gate_summary(_s04_gate(operation_counts={"broker_access": 1})),
    )

    assert failed_payload["admission_status"] == AdmissionStatus.FAIL.value
    assert review_payload["admission_status"] == AdmissionStatus.WARN.value
    assert blocked_payload["admission_status"] == AdmissionStatus.BLOCKED.value
    assert any(reason["code"] == MF_ADMISSION_EVENT_GATE_BLOCKED for reason in blocked_payload["blocked_reasons"])
    assert "provide_passing_CR153_event_gate_or_route_review" in blocked_payload["unlock_conditions"]


def test_cr153_s04_package_linkage_preserves_ml_and_statistical_gate_fields() -> None:
    package = _s04_package().to_dict()
    package.update(
        {
            "statistical_gate_summary": {"status": "PASS", "gate_ref": "stat://fixture"},
            "ml_gate_summary": {"gate_status": "PASS", "gate_ref": "ml://fixture"},
            "gate_status": "PASS",
            "gate_ref": "ml://fixture",
        }
    )

    payload = attach_event_gate_to_admission_package(package, event_gate_summary(_s04_gate()))

    assert payload["statistical_gate_summary"]["gate_ref"] == "stat://fixture"
    assert payload["ml_gate_summary"]["gate_ref"] == "ml://fixture"
    assert payload["gate_status"] == "PASS"
    assert payload["gate_ref"] == "ml://fixture"
    assert payload["event_gate_status"] == "PASS"
