from __future__ import annotations

import ast
import inspect

from trading import qmt_client, qmt_endpoint_matrix, qmt_gateway_contracts
from trading.qmt_auth import QmtAuthResult
from trading.qmt_client import (
    QmtBlockedReason,
    QmtClient,
    QmtEndpointCategory,
    QmtRequest,
    QmtResponseStatus,
    collect_qmt_client_safety_counters,
)
from trading.qmt_endpoint_matrix import (
    HLD_ENDPOINT_CATEGORIES,
    ACCOUNT_LIKE_ENDPOINTS,
    LATER_GATED_ENDPOINTS,
    QMT_ENDPOINT_MATRIX_SCHEMA_VERSION,
    QmtEndpointVisibility,
    QmtRealOperationKind,
    build_capabilities_payload,
    endpoint_specs_by_hld_category,
    get_endpoint_spec,
    iter_endpoint_specs,
)
from trading.qmt_gateway_contracts import (
    QmtGatewayResultStatus,
    build_allowed_result,
    build_blocked_result,
    collect_qmt_gateway_contract_counters,
)


REQUIRED_ZERO_COUNTERS = {
    "dependency_change",
    "service_start",
    "credential_read",
    "qmt_operation",
    "qmt_api_call",
    "xtquant_import",
    "real_order",
    "real_cancel",
    "account_query",
    "account_write",
    "provider_fetch",
    "lake_write",
    "broker_lake_write",
    "publish",
    "current_pointer_publish",
    "simulation_or_live_run",
    "service_bind",
    "http_client_call",
    "gateway_socket_open",
}


def _request(
    endpoint: QmtEndpointCategory,
    *,
    mode: str = "dry_run",
    authorization_ref: str = "",
    payload: dict[str, object] | None = None,
) -> QmtRequest:
    return QmtRequest(
        run_id="run-cr019-s06-fixture",
        endpoint=endpoint,
        stage="shadow",
        mode=mode,
        intent_id="intent-cr019-s06-fixture",
        authorization_ref=authorization_ref,
        redaction_label="fixture-redacted",
        payload=payload or {},
    )


def _assert_zero_counters(counters: object) -> None:
    current = dict(counters)  # type: ignore[arg-type]
    assert {key: current.get(key) for key in REQUIRED_ZERO_COUNTERS} == {
        key: 0 for key in REQUIRED_ZERO_COUNTERS
    }


def _call_contract_method(client: QmtClient, category: QmtEndpointCategory):
    spec = get_endpoint_spec(category)
    method = getattr(client, spec.client_method)
    if category in {QmtEndpointCategory.HEALTH, QmtEndpointCategory.CAPABILITIES}:
        return method(run_id="run-cr019-s06-fixture", stage="shadow")
    return method(_request(category))


def test_endpoint_matrix_covers_all_hld_categories_and_freezes_required_fields() -> None:
    specs = iter_endpoint_specs()
    grouped = endpoint_specs_by_hld_category()

    assert QMT_ENDPOINT_MATRIX_SCHEMA_VERSION == "cr019-s06-qmt-endpoint-matrix-v1"
    assert tuple(grouped) == HLD_ENDPOINT_CATEGORIES
    assert len(HLD_ENDPOINT_CATEGORIES) == 14
    assert all(grouped[category] for category in HLD_ENDPOINT_CATEGORIES)

    endpoint_ids = [spec.endpoint_id for spec in specs]
    assert len(endpoint_ids) == len(set(endpoint_ids))
    for spec in specs:
        assert spec.method in {"GET", "POST"}
        assert spec.path.startswith("/qmt/")
        assert spec.client_method
        assert spec.required_scope.startswith("qmt:")
        assert spec.gate_inputs
        assert spec.real_operation_kind in set(QmtRealOperationKind)
        assert spec.default_visibility in set(QmtEndpointVisibility)
        assert spec.blocked_reason in set(QmtBlockedReason)
        assert spec.blocked_cases


def test_each_hld_category_has_typed_blocked_result_case() -> None:
    for category, specs in endpoint_specs_by_hld_category().items():
        assert specs, category
        for spec in specs:
            case = spec.blocked_cases[0]
            result = build_blocked_result(spec.endpoint_id, case.reason, case.message)
            assert result.status is QmtGatewayResultStatus.BLOCKED
            assert result.blocked is True
            assert result.endpoint_id == spec.endpoint_id
            assert result.blocked_reason is case.reason
            assert result.error is not None
            assert result.error.redaction_status == "redacted"
            _assert_zero_counters(result.counters)


def test_allowed_result_is_fixture_only_and_does_not_authorize_real_operation() -> None:
    result = build_allowed_result(
        "dry_run",
        {"fixture_ack": True, "real_operation": False},
    )

    assert result.status is QmtGatewayResultStatus.ALLOWED
    assert result.allowed is True
    assert result.allowed_payload is not None
    assert result.allowed_payload.fixture_only is True
    assert result.allowed_payload.operation_authorized is False
    assert result.allowed_payload.real_operation is False
    _assert_zero_counters(result.counters)


def test_capabilities_visibility_does_not_grant_account_order_cancel_or_live_auth() -> None:
    payload = build_capabilities_payload()
    response = QmtClient().capabilities(run_id="run-capability-fixture", stage="shadow")

    assert payload["operation_authorized"] is False
    assert payload["account_authorized"] is False
    assert payload["order_authorized"] is False
    assert payload["cancel_authorized"] is False
    assert payload["simulation_authorized"] is False
    assert payload["live_authorized"] is False
    assert set(payload["endpoint_categories"]) == set(HLD_ENDPOINT_CATEGORIES)

    assert response.blocked is True
    assert response.reason_code == QmtBlockedReason.TRANSPORT_UNAVAILABLE.value
    capability_payload = response.payload["capabilities"]
    assert isinstance(capability_payload, dict)
    assert capability_payload["operation_authorized"] is False
    _assert_zero_counters(response.counters)


def test_client_methods_consume_matrix_and_default_later_gated_endpoints_blocked() -> None:
    client = QmtClient()

    validate_response = client.validate_intent(_request(QmtEndpointCategory.VALIDATE_INTENT))
    dry_run_response = client.dry_run(_request(QmtEndpointCategory.DRY_RUN))
    assert validate_response.status is QmtResponseStatus.OK
    assert dry_run_response.status is QmtResponseStatus.OK
    assert validate_response.payload["operation_authorized"] is False
    assert dry_run_response.payload["real_operation"] is False
    _assert_zero_counters(validate_response.counters)
    _assert_zero_counters(dry_run_response.counters)

    for category in LATER_GATED_ENDPOINTS:
        response = _call_contract_method(client, category)
        assert response.blocked is True
        if category is QmtEndpointCategory.POSITIONS:
            assert response.reason_code == QmtBlockedReason.TRANSPORT_UNAVAILABLE.value
            assert response.status is QmtResponseStatus.TRANSPORT_ERROR
        else:
            assert response.reason_code == QmtBlockedReason.PER_RUN_AUTHORIZATION_MISSING.value
        assert response.payload["operation_authorized"] is False
        _assert_zero_counters(response.counters)
        if category in ACCOUNT_LIKE_ENDPOINTS:
            assert response.counters["account_query"] == 0
        if category in {
            QmtEndpointCategory.SIMULATION_SUBMIT,
            QmtEndpointCategory.LIVE_SUBMIT,
        }:
            assert response.counters["real_order"] == 0
        if category in {
            QmtEndpointCategory.SIMULATION_CANCEL,
            QmtEndpointCategory.LIVE_CANCEL,
        }:
            assert response.counters["real_cancel"] == 0


def test_hmac_pass_identifies_caller_but_never_authorizes_endpoint_operation() -> None:
    auth_result = QmtAuthResult(
        allowed=True,
        status="allowed",
        scopes=("qmt:live:submit",),
        required_scope="qmt:live:submit",
        caller_identified=True,
    )
    response = QmtClient().submit_live(
        _request(
            QmtEndpointCategory.LIVE_SUBMIT,
            mode="small_live",
            authorization_ref="hmac-pass-only",
            payload={"auth_result": auth_result.to_dict()},
        )
    )

    assert auth_result.caller_identified is True
    assert auth_result.trade_authorized is False
    assert auth_result.simulation_authorized is False
    assert auth_result.live_authorized is False
    assert auth_result.account_authorized is False
    assert auth_result.cancel_authorized is False
    assert response.blocked is True
    assert response.reason_code == QmtBlockedReason.PER_RUN_AUTHORIZATION_MISSING.value
    assert response.counters["real_order"] == 0
    _assert_zero_counters(response.counters)


def test_client_only_reexports_matrix_and_contracts_without_copying_enums() -> None:
    source = inspect.getsource(qmt_client)

    assert "class QmtEndpointCategory" not in source
    assert "class QmtBlockedReason" not in source
    assert "from trading.qmt_endpoint_matrix import" in source
    assert "from trading.qmt_gateway_contracts import" in source
    assert qmt_client.QmtEndpointCategory is qmt_endpoint_matrix.QmtEndpointCategory
    assert qmt_client.QmtBlockedReason is qmt_gateway_contracts.QmtBlockedReason


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
    for module in (qmt_endpoint_matrix, qmt_gateway_contracts, qmt_client):
        tree = ast.parse(inspect.getsource(module), filename=module.__name__)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend(alias.name.split(".", 1)[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.append(node.module.split(".", 1)[0])

    assert not (set(imports) & forbidden_import_roots)


def test_forbidden_operation_counters_are_all_zero() -> None:
    client_counters = collect_qmt_client_safety_counters()
    contract_counters = collect_qmt_gateway_contract_counters()

    _assert_zero_counters(client_counters)
    _assert_zero_counters(contract_counters)
    assert client_counters["qmt_api_call"] == 0
    assert client_counters["real_order"] == 0
    assert client_counters["real_cancel"] == 0
    assert client_counters["account_query"] == 0
    assert contract_counters["broker_lake_write"] == 0
