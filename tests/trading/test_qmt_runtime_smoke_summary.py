from __future__ import annotations

import importlib.util
from pathlib import Path


SCRIPT_PATH = Path("scripts/qmt/collect_qmt_runtime_smoke_summary.py")


def _load_script_module():
    spec = importlib.util.spec_from_file_location(
        "collect_cr089_qmt_runtime_smoke_summary",
        SCRIPT_PATH,
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_cr089_runtime_summary_keeps_only_redacted_query_positions_fields() -> None:
    module = _load_script_module()
    response = {
        "blocked_result": None,
        "counters": {
            "credential_read": 0,
            "real_order": 0,
            "real_cancel": 0,
            "account_write": 0,
            "provider_fetch": 0,
            "lake_write": 0,
            "publish": 0,
            "simulation_or_live_run": 0,
        },
        "endpoint": "positions",
        "message": "",
        "payload": {
            "gateway_result": {
                "allowed": True,
                "blocked": False,
                "allowed_payload": {
                    "data": {
                        "endpoint_id": "query_positions",
                        "operation_authorized": False,
                        "query_positions": {
                            "items_redacted": [
                                {
                                    "position_ref": "position_ref:forbidden",
                                    "instrument_ref": "instrument_ref:forbidden",
                                }
                            ],
                            "position_count": 1,
                            "positions_digest": "positions:fixture",
                            "raw_payload_emitted": False,
                            "redaction_status": "pass",
                        },
                        "readonly_query_authorized": True,
                        "real_operation": False,
                        "scope": "qmt:positions:read",
                    },
                    "operation_authorized": False,
                    "real_operation": False,
                },
                "counters": {
                    "query_positions_read_attempt": 1,
                    "readonly_positions_adapter_call": 1,
                    "raw_positions_emit": 0,
                    "redaction_fallback_to_raw": 0,
                    "real_order": 0,
                    "real_cancel": 0,
                },
                "status": "allowed",
            },
            "operation_authorized": False,
            "query_positions": {
                "items_redacted": [
                    {
                        "position_ref": "position_ref:forbidden",
                        "instrument_ref": "instrument_ref:forbidden",
                    }
                ],
                "position_count": 1,
                "positions_digest": "positions:fixture",
                "raw_payload_emitted": False,
                "redaction_status": "pass",
            },
            "readonly_query_authorized": True,
            "real_operation": False,
            "scope": "qmt:positions:read",
        },
        "reason_code": "",
        "redaction_status": "redacted",
        "run_id": "cr089-query-positions-fixture",
        "schema_version": "cr019-s03-qmt-client-v1",
        "status": "ok",
        "transport_metadata": {
            "client_id_ref": "client_id_ref:should-not-emit",
            "nonce_ref": "nonce_ref:should-not-emit",
            "signature_ref": "signature_ref:should-not-emit",
            "status_code": "200",
            "transport_status": "allowed",
        },
    }

    summary = module.build_redacted_summary(
        env_file=".env",
        base_url="http://127.0.0.1:18765",
        host="127.0.0.1",
        port=18765,
        config_flags={
            "client_id_configured": True,
            "client_secret_configured": True,
            "account_ref_configured": True,
            "miniqmt_path_configured": True,
            "xtquant_site_packages_configured": True,
            "allowed_source": "127.0.0.1/32",
            "account_type": "STOCK",
        },
        runtime_authorization_ref="cr089-runtime-smoke-20260617-query-positions",
        run_id="cr089-query-positions-fixture",
        request_id="cr089-query-positions-fixture-001",
        health={
            "status": "ok",
            "session_ready": True,
            "session_state": "ready",
            "blocked_reason": "",
            "runtime_status": "xtquant-ready",
            "redaction_status": "redacted",
            "config": {
                "host": "127.0.0.1",
                "port": 18765,
                "allowed_source": "127.0.0.1/32",
                "client_id_hash": "should-not-emit",
                "client_secret_ref": "[REDACTED]",
                "account_ref": "account_ref:should-not-emit",
                "miniqmt_path_configured": True,
                "xtquant_site_packages_configured": True,
            },
        },
        query_response=response,
    )

    module._ensure_summary_safe(summary)
    assert summary["status"] == "pass"
    readonly = summary["readonly_smoke"]
    assert readonly["status"] == "pass"
    assert readonly["position_count_bucket"] == "one"
    assert readonly["positions_digest"] == "positions:fixture"
    assert readonly["items_redacted_count"] == 1
    assert "position_ref:forbidden" not in str(summary)
    assert "instrument_ref:forbidden" not in str(summary)
    assert "client_id_ref:" not in str(summary)
    assert "nonce_ref:" not in str(summary)
    assert "signature_ref:" not in str(summary)
    assert "account_ref:" not in str(summary)


def test_cr089_runtime_summary_blocks_when_health_is_not_ready() -> None:
    module = _load_script_module()

    summary = module.build_redacted_summary(
        env_file=".env",
        base_url="http://127.0.0.1:18765",
        host="127.0.0.1",
        port=18765,
        config_flags={},
        runtime_authorization_ref="cr089-runtime-smoke-20260617-query-positions",
        run_id="run-fixture",
        request_id="request-fixture",
        health={
            "status": "blocked",
            "session_ready": False,
            "blocked_reason": "xtquant-connect-failed",
            "redaction_status": "redacted",
        },
        query_response=None,
    )

    module._ensure_summary_safe(summary)
    assert summary["status"] == "blocked"
    assert summary["readonly_smoke"]["status"] == "skipped"
    assert summary["readonly_smoke"]["blocked_reason"] == "health_not_ready"
