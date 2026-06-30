from __future__ import annotations

import ast
import inspect

from trading import qmt_gateway_gates
from trading.kill_switch import read_kill_switch_result
from trading.pretrade_risk import read_pretrade_risk_result
from trading.qmt_auth import QmtAuthBlockedReason, QmtAuthResult
from trading.qmt_endpoint_matrix import QmtEndpointCategory, get_endpoint_spec
from trading.qmt_gateway_contracts import QmtBlockedReason, QmtGatewayResultStatus
from trading.qmt_gateway_gates import (
    QmtGateContext,
    collect_qmt_gateway_gate_safety_counters,
    evaluate_qmt_gateway_gates,
    to_qmt_gateway_result,
)
from trading.stage_gate import (
    GateStatus,
    Stage,
    StageGateResult,
    read_admission_gate_result,
    read_stage_gate_result,
)


REQUIRED_ZERO_COUNTERS = {
    "adapter_call",
    "qmt_api_call",
    "real_order",
    "real_cancel",
    "cancel_order",
    "account_query",
    "broker_lake_write",
    "simulation_or_live_run",
    "credential_read",
    "service_start",
    "service_bind",
    "http_client_call",
    "gateway_socket_open",
}


def _assert_zero_counters(counters: object) -> None:
    current = dict(counters)  # type: ignore[arg-type]
    assert {key: current.get(key, 0) for key in REQUIRED_ZERO_COUNTERS} == {
        key: 0 for key in REQUIRED_ZERO_COUNTERS
    }


def _auth_for(category: QmtEndpointCategory, **overrides: object) -> QmtAuthResult:
    spec = get_endpoint_spec(category)
    values: dict[str, object] = {
        "allowed": True,
        "status": "identified",
        "client_id_hash": "fixture-client-hash",
        "scopes": (spec.required_scope,),
        "required_scope": spec.required_scope,
        "caller_identified": True,
    }
    values.update(overrides)
    return QmtAuthResult(**values)  # type: ignore[arg-type]


def _admission_pass() -> dict[str, object]:
    return {
        "admission_status": "pass",
        "admission_package_ref": "fixture:admission:package",
        "stage_gate_ref": "fixture:cr016-stage-gate",
        "blocked_claims": (),
        "missing_evidence": (),
        "permission_counters": {},
    }


def _stage_pass() -> StageGateResult:
    return StageGateResult(
        gate_status=GateStatus.PASS,
        current_stage=Stage.SHADOW,
        target_stage=Stage.SIMULATION,
        evidence_refs={"runbook_ref": "fixture:runbook"},
        authorization_id="auth-fixture",
    )


def _risk_pass() -> dict[str, object]:
    return {
        "passed": True,
        "status": "pass",
        "risk_profile_id": "risk-profile-fixture",
        "blocked_rules": (),
        "adapter_calls": 0,
        "safety_counters": {},
    }


def _risk_blocked() -> dict[str, object]:
    return {
        "passed": False,
        "status": "blocked",
        "blocked_rules": ("cash_insufficient",),
        "adapter_calls": 0,
        "safety_counters": {},
    }


def _kill_pass() -> dict[str, object]:
    return {
        "status": "pass",
        "kill_switch_active": False,
        "required_evidence": (),
        "safety_counters": {},
    }


def _kill_active() -> dict[str, object]:
    return {
        "status": "active",
        "kill_switch_active": True,
        "blocked_reason": "manual_trigger",
        "required_evidence": ("kill_switch_recovery_gate",),
        "safety_counters": {},
    }


def _run_gate_context(
    *,
    category: QmtEndpointCategory = QmtEndpointCategory.SIMULATION_SUBMIT,
    auth_result: QmtAuthResult | None = None,
    admission_result: object | None = None,
    stage_gate_result: object | None = None,
    risk_result: object | None = None,
    kill_switch_result: object | None = None,
    authorization_ref: str = "auth-fixture",
    authorization_status: str = "valid",
    execution_price_policy: str = "raw",
) -> QmtGateContext:
    return QmtGateContext(
        endpoint_spec=get_endpoint_spec(category),
        auth_result=auth_result or _auth_for(category),
        admission_result=admission_result if admission_result is not None else _admission_pass(),
        stage_gate_result=stage_gate_result if stage_gate_result is not None else _stage_pass(),
        risk_result=risk_result if risk_result is not None else _risk_pass(),
        kill_switch_result=(
            kill_switch_result if kill_switch_result is not None else _kill_pass()
        ),
        authorization_ref=authorization_ref,
        authorization_status=authorization_status,
        execution_price_policy=execution_price_policy,
    )


def test_auth_failed_has_highest_priority_and_forbidden_counters_zero() -> None:
    auth = QmtAuthResult(
        allowed=False,
        status="blocked",
        blocked_reason=QmtAuthBlockedReason.AUTH_SIGNATURE_MISMATCH,
    )

    decision = evaluate_qmt_gateway_gates(
        _run_gate_context(
            auth_result=auth,
            admission_result=None,
            stage_gate_result=None,
            risk_result=_risk_blocked(),
            kill_switch_result=_kill_active(),
            authorization_ref="",
        )
    )

    assert decision.blocked is True
    assert decision.blocked_reason is QmtBlockedReason.AUTH_BLOCKED
    assert decision.blocked_by == "hmac_auth"
    assert decision.suppressed_reasons == ()
    _assert_zero_counters(decision.counters)

    result = to_qmt_gateway_result(get_endpoint_spec(QmtEndpointCategory.SIMULATION_SUBMIT), decision)
    assert result.status is QmtGatewayResultStatus.BLOCKED
    assert result.blocked_reason is QmtBlockedReason.AUTH_BLOCKED
    _assert_zero_counters(result.counters)


def test_scope_denied_is_auth_priority_before_run_gates() -> None:
    decision = evaluate_qmt_gateway_gates(
        _run_gate_context(
            auth_result=_auth_for(
                QmtEndpointCategory.LIVE_SUBMIT,
                scopes=("qmt:health",),
            ),
            category=QmtEndpointCategory.LIVE_SUBMIT,
            admission_result=None,
            stage_gate_result=None,
        )
    )

    assert decision.blocked_reason is QmtBlockedReason.SCOPE_DENIED
    assert decision.blocked_by == "hmac_scope"
    assert decision.required_evidence == ("scope:qmt:live:submit",)
    _assert_zero_counters(decision.counters)


def test_unknown_endpoint_blocks_with_s06_unknown_endpoint_reason() -> None:
    decision = evaluate_qmt_gateway_gates(
        QmtGateContext(
            endpoint_spec="not-a-qmt-endpoint",
            auth_result=_auth_for(QmtEndpointCategory.HEALTH),
        )
    )

    assert decision.blocked_reason is QmtBlockedReason.UNKNOWN_ENDPOINT
    assert decision.blocked_by == "endpoint_matrix"
    _assert_zero_counters(decision.counters)


def test_admission_and_stage_missing_fail_closed_before_authorization() -> None:
    decision = evaluate_qmt_gateway_gates(
        QmtGateContext(
            endpoint_spec=get_endpoint_spec(QmtEndpointCategory.SIMULATION_SUBMIT),
            auth_result=_auth_for(QmtEndpointCategory.SIMULATION_SUBMIT),
            admission_result=None,
            stage_gate_result=None,
            risk_result=None,
            kill_switch_result=None,
            authorization_ref="",
        )
    )

    assert decision.blocked_reason is QmtBlockedReason.STAGE_GATE_BLOCKED
    assert decision.blocked_by == "admission_gate"
    assert "admission_package_ref" in decision.required_evidence
    assert {
        failure.blocked_by for failure in decision.suppressed_reasons
    } >= {"stage_gate", "per_run_authorization", "pretrade_risk", "kill_switch"}
    _assert_zero_counters(decision.counters)


def test_authorization_missing_blocks_after_admission_and_stage_pass() -> None:
    decision = evaluate_qmt_gateway_gates(
        _run_gate_context(authorization_ref="", authorization_status="")
    )

    assert decision.blocked_reason is QmtBlockedReason.AUTHORIZATION_MISSING
    assert decision.blocked_by == "per_run_authorization"
    assert decision.required_evidence == ("authorization_ref",)
    assert decision.hmac_trade_authorization_claim_count == 0
    _assert_zero_counters(decision.counters)


def test_risk_failure_has_priority_before_kill_switch() -> None:
    decision = evaluate_qmt_gateway_gates(
        _run_gate_context(risk_result=_risk_blocked(), kill_switch_result=_kill_active())
    )

    assert decision.blocked_reason is QmtBlockedReason.RISK_GATE_BLOCKED
    assert decision.blocked_by == "pretrade_risk"
    assert decision.suppressed_reasons[0].blocked_by == "kill_switch"
    _assert_zero_counters(decision.counters)


def test_kill_switch_active_blocks_after_risk_pass() -> None:
    decision = evaluate_qmt_gateway_gates(
        _run_gate_context(kill_switch_result=_kill_active())
    )

    assert decision.blocked_reason is QmtBlockedReason.KILL_SWITCH_ACTIVE
    assert decision.blocked_by == "kill_switch"
    assert decision.required_evidence == ("kill_switch_recovery_gate",)
    _assert_zero_counters(decision.counters)


def test_raw_policy_blocks_qfq_execution_policy() -> None:
    decision = evaluate_qmt_gateway_gates(
        _run_gate_context(execution_price_policy="qfq")
    )

    assert decision.blocked_reason is QmtBlockedReason.RAW_POLICY_BLOCKED
    assert decision.blocked_by == "raw_execution_policy"
    assert decision.required_evidence == ("execution_price_policy=raw",)
    _assert_zero_counters(decision.counters)


def test_hmac_pass_never_authorizes_trading_without_per_run_gate() -> None:
    auth = _auth_for(
        QmtEndpointCategory.LIVE_SUBMIT,
        trade_authorized=True,
        simulation_authorized=True,
        live_authorized=True,
        account_authorized=True,
        cancel_authorized=True,
    )

    decision = evaluate_qmt_gateway_gates(
        _run_gate_context(
            category=QmtEndpointCategory.LIVE_SUBMIT,
            auth_result=auth,
        )
    )

    assert decision.blocked_reason is QmtBlockedReason.QMT_OPERATION_NOT_AUTHORIZED
    assert decision.blocked_by == "auth_result"
    assert decision.hmac_trade_authorization_claim_count == 5
    assert decision.auth_caller_identified is True
    _assert_zero_counters(decision.counters)


def test_all_gates_pass_returns_fixture_allowed_result_without_real_authorization() -> None:
    spec = get_endpoint_spec(QmtEndpointCategory.SIMULATION_SUBMIT)
    decision = evaluate_qmt_gateway_gates(_run_gate_context())
    result = to_qmt_gateway_result(spec, decision)

    assert decision.allowed is True
    assert decision.blocked_reason is None
    assert result.status is QmtGatewayResultStatus.ALLOWED
    assert result.allowed_payload is not None
    assert result.allowed_payload.fixture_only is True
    assert result.allowed_payload.operation_authorized is False
    assert result.allowed_payload.real_operation is False
    _assert_zero_counters(result.counters)


def test_blocked_result_detail_preserves_suppressed_reasons() -> None:
    spec = get_endpoint_spec(QmtEndpointCategory.SIMULATION_SUBMIT)
    decision = evaluate_qmt_gateway_gates(
        QmtGateContext(
            endpoint_spec=spec,
            auth_result=_auth_for(QmtEndpointCategory.SIMULATION_SUBMIT),
            admission_result=None,
            stage_gate_result=None,
            risk_result=_risk_blocked(),
            kill_switch_result=_kill_active(),
            authorization_ref="",
        )
    )
    result = to_qmt_gateway_result(spec, decision)

    assert result.error is not None
    detail = result.error.detail
    assert detail["blocked_by"] == "admission_gate"
    assert detail["gate_schema_version"] == "cr019-s07-qmt-gateway-gates-v1"
    suppressed = detail["suppressed_reasons"]
    assert isinstance(suppressed, list)
    assert {item["blocked_by"] for item in suppressed} >= {
        "stage_gate",
        "per_run_authorization",
        "pretrade_risk",
        "kill_switch",
    }
    _assert_zero_counters(result.counters)


def test_read_only_adapters_do_not_mutate_shared_gate_objects() -> None:
    stage_result = _stage_pass()
    original_evidence = dict(stage_result.evidence_refs)
    stage_view = read_stage_gate_result(stage_result)
    admission_view = read_admission_gate_result(
        {
            "admission_status": "blocked",
            "blocked_claims": [{"reason_code": "p0_gate_failed"}],
            "missing_evidence": ("cost_model",),
            "permission_counters": {},
        }
    )
    risk_context = _risk_blocked()
    risk_view = read_pretrade_risk_result(risk_context)
    kill_view = read_kill_switch_result(_kill_active())

    assert stage_result.evidence_refs == original_evidence
    assert stage_view["passed"] is True
    assert admission_view["passed"] is False
    assert admission_view["blocked_reason"] == "p0_gate_failed"
    assert risk_context["blocked_rules"] == ("cash_insufficient",)
    assert risk_view["blocked_reason"] == "cash_insufficient"
    assert kill_view["blocked_reason"] == "manual_trigger"


def test_forbidden_operation_counters_are_all_zero() -> None:
    counters = collect_qmt_gateway_gate_safety_counters()

    _assert_zero_counters(counters)
    assert counters["adapter_call"] == 0
    assert counters["qmt_api_call"] == 0
    assert counters["real_order"] == 0
    assert counters["real_cancel"] == 0
    assert counters["account_query"] == 0
    assert counters["broker_lake_write"] == 0
    assert counters["simulation_or_live_run"] == 0


def test_sources_do_not_import_service_network_or_qmt_runtime_modules() -> None:
    forbidden_import_roots = {
        "fastapi",
        "uvicorn",
        "requests",
        "httpx",
        "socket",
        "urllib",
        "subprocess",
        "xtquant",
        "xttrader",
        "xtdata",
    }

    imports: list[str] = []
    tree = ast.parse(
        inspect.getsource(qmt_gateway_gates),
        filename=qmt_gateway_gates.__name__,
    )
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.append(node.module.split(".", 1)[0])

    assert not (set(imports) & forbidden_import_roots)
