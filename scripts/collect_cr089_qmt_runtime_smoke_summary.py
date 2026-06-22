"""CR089 QMT runtime smoke 的交易机本地脱敏采集脚本。

用法示例：

    uv run --python 3.11 python scripts/collect_cr089_qmt_runtime_smoke_summary.py \
        --env-file .env \
        --base-url http://127.0.0.1:18765 \
        --runtime-authorization-ref cr089-runtime-smoke-20260617-query-positions

脚本只输出脱敏摘要。它不会启动 gateway，不会读取或输出原始持仓、账户、
secret、token、session、nonce、signature 或 QMT 日志。
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from typing import Mapping, Sequence
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from trading.qmt_client import QmtClient, QmtClientConfig, QmtResponse
from trading.qmt_gateway_contracts import CR020_QUERY_POSITIONS_SCOPE
from trading.qmt_runtime import (
    RUNTIME_SCHEMA_VERSION,
    StdlibQmtRestTransport,
    build_runtime_config,
    build_runtime_hmac_provider,
    load_runtime_env,
)


SUMMARY_SCHEMA_VERSION = "cr089-qmt-runtime-smoke-redacted-summary-v1"
DEFAULT_AUTH_REF = "cr089-runtime-smoke-20260617-query-positions"

DISALLOWED_OUTPUT_TOKENS = (
    "client_id_hash",
    "client_id_ref:",
    "nonce_ref:",
    "signature_ref:",
    "account_ref:",
    "QMT_CLIENT_SECRET",
    "QMT_ACCOUNT_REF",
    "QMT_LOGIN_ACCOUNT",
    "X-QMT-Client-Id",
    "X-QMT-Signature",
    '"items_redacted":',
)

FORBIDDEN_COUNTER_KEYS = (
    "real_order",
    "real_cancel",
    "account_write",
    "provider_fetch",
    "lake_write",
    "publish",
    "simulation_or_live_run",
    "credential_read",
    "raw_positions_emit",
    "redaction_fallback_to_raw",
)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    env = load_runtime_env(args.env_file)
    config = build_runtime_config(
        env,
        host=args.host,
        port=args.port,
        runtime_authorization_ref=args.runtime_authorization_ref,
    )
    base_url = (args.base_url or config.base_url).rstrip("/")
    run_id = args.run_id or _default_run_id()
    request_id = args.request_id or f"{run_id}-001"

    health = _fetch_health(base_url, args.timeout_seconds)
    query_response: QmtResponse | None = None
    if _health_is_ready(health):
        client = QmtClient(
            config=QmtClientConfig(
                base_url=base_url,
                default_stage="manual_cp7",
                default_mode="live_readonly",
                default_timeout_seconds=args.timeout_seconds,
            ),
            transport=StdlibQmtRestTransport(),
            auth_header_provider=build_runtime_hmac_provider(config),
        )
        query_response = client.query_positions(
            run_id=run_id,
            request_id=request_id,
            authorization_ref=config.runtime_authorization_ref,
            timeout_seconds=args.timeout_seconds,
        )

    summary = build_redacted_summary(
        env_file=args.env_file,
        base_url=base_url,
        host=config.host,
        port=config.port,
        config_flags={
            "client_id_configured": bool(config.client_id),
            "client_secret_configured": bool(config.client_secret),
            "account_ref_configured": bool(config.account_id),
            "miniqmt_path_configured": bool(config.miniqmt_path),
            "xtquant_site_packages_configured": bool(config.xtquant_site_packages),
            "allowed_source": config.allowed_source,
            "account_type": config.account_type,
        },
        runtime_authorization_ref=config.runtime_authorization_ref,
        run_id=run_id,
        request_id=request_id,
        health=health,
        query_response=query_response,
    )
    _ensure_summary_safe(summary)
    rendered = json.dumps(summary, ensure_ascii=False, sort_keys=True, indent=2)
    if args.output_json:
        Path(args.output_json).write_text(f"{rendered}\n", encoding="utf-8")
    print(rendered)
    return 0 if summary["status"] == "pass" else 2


def build_redacted_summary(
    *,
    env_file: str,
    base_url: str,
    host: str,
    port: int,
    config_flags: Mapping[str, object],
    runtime_authorization_ref: str,
    run_id: str,
    request_id: str,
    health: Mapping[str, object],
    query_response: QmtResponse | Mapping[str, object] | None,
) -> dict[str, object]:
    query_summary = _summarize_query_response(query_response)
    health_summary = _summarize_health(health)
    forbidden_counters = _forbidden_counters(query_summary)
    readonly_smoke = _readonly_smoke_summary(query_summary)
    status = _overall_status(health_summary, query_summary, readonly_smoke, forbidden_counters)

    return {
        "schema_version": SUMMARY_SCHEMA_VERSION,
        "status": status,
        "generated_at_utc": datetime.now(tz=timezone.utc).isoformat(),
        "change_id": "CR-089",
        "runtime_authorization_ref": runtime_authorization_ref,
        "run_id": run_id,
        "request_id": request_id,
        "execution_environment": {
            "host_role": "trading_pc",
            "base_url": base_url,
            "host": host,
            "port": port,
            "env_file_used_by_local_user_process": bool(env_file),
            "qmt_runtime": "user_local_only",
        },
        "local_config_summary": {
            "schema_version": RUNTIME_SCHEMA_VERSION,
            **dict(config_flags),
        },
        "server_health": health_summary,
        "readonly_smoke": readonly_smoke,
        "forbidden_operation_counters": forbidden_counters,
        "redaction_assurance": {
            "raw_payload_included": False,
            "raw_account_output_included": False,
            "client_or_account_refs_included": False,
            "nonce_or_signature_refs_included": False,
            "qmt_logs_included": False,
        },
        "operator_notes_redacted": (
            "Only paste this redacted summary. Do not paste raw QMT/MiniQMT/XtQuant logs, "
            "account details, positions, secrets, tokens, sessions, nonce or signatures."
        ),
    }


def _parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Collect CR089 QMT runtime smoke redacted summary on the trading PC."
    )
    parser.add_argument("--env-file", default=".env")
    parser.add_argument("--base-url", default="")
    parser.add_argument("--host", default="")
    parser.add_argument("--port", type=int, default=0)
    parser.add_argument("--runtime-authorization-ref", default=DEFAULT_AUTH_REF)
    parser.add_argument("--run-id", default="")
    parser.add_argument("--request-id", default="")
    parser.add_argument("--timeout-seconds", type=int, default=10)
    parser.add_argument("--output-json", default="")
    return parser.parse_args(argv)


def _default_run_id() -> str:
    return f"cr089-query-positions-{datetime.now().strftime('%Y%m%d-%H%M%S')}"


def _fetch_health(base_url: str, timeout_seconds: int) -> dict[str, object]:
    try:
        response = urlopen(f"{base_url.rstrip('/')}/qmt/health", timeout=timeout_seconds)
        body = response.read().decode("utf-8")
        payload = json.loads(body)
        if isinstance(payload, Mapping):
            return dict(payload)
        return {"status": "blocked", "blocked_reason": "health_response_not_mapping"}
    except HTTPError as exc:
        try:
            payload = json.loads(exc.read().decode("utf-8"))
        except Exception:
            payload = {}
        result = dict(payload) if isinstance(payload, Mapping) else {}
        result.setdefault("status", "blocked")
        result.setdefault("blocked_reason", f"health_http_error:{exc.code}")
        return result
    except (TimeoutError, URLError, OSError) as exc:
        return {
            "status": "blocked",
            "session_ready": False,
            "blocked_reason": f"health_unavailable:{type(exc).__name__}",
            "redaction_status": "redacted",
        }


def _health_is_ready(health: Mapping[str, object]) -> bool:
    return health.get("status") == "ok" and health.get("session_ready") is True


def _summarize_health(health: Mapping[str, object]) -> dict[str, object]:
    config = health.get("config")
    config_map = config if isinstance(config, Mapping) else {}
    return {
        "status": str(health.get("status", "blocked")),
        "session_ready": bool(health.get("session_ready", False)),
        "session_state": str(health.get("session_state", "")),
        "blocked_reason": str(health.get("blocked_reason", "")),
        "runtime_status": str(health.get("runtime_status", "")),
        "redaction_status": str(health.get("redaction_status", "redacted")),
        "config": {
            "host": str(config_map.get("host", "")),
            "port": int(config_map.get("port", 0) or 0),
            "allowed_source": str(config_map.get("allowed_source", "")),
            "miniqmt_path_configured": bool(
                config_map.get("miniqmt_path_configured", False)
            ),
            "xtquant_site_packages_configured": bool(
                config_map.get("xtquant_site_packages_configured", False)
            ),
            "client_id_configured": bool(config_map.get("client_id_hash", "")),
            "client_secret_configured": config_map.get("client_secret_ref") == "[REDACTED]",
            "account_ref_configured": bool(config_map.get("account_ref", "")),
        },
    }


def _summarize_query_response(
    query_response: QmtResponse | Mapping[str, object] | None,
) -> dict[str, object]:
    if query_response is None:
        return {
            "status": "skipped",
            "reason_code": "health_not_ready",
            "endpoint": "",
            "redaction_status": "not_run",
            "allowed": False,
            "blocked": True,
            "readonly_query_authorized": False,
            "operation_authorized": False,
            "real_operation": False,
            "transport_status": "",
            "status_code": "",
            "query_positions": {
                "position_count_bucket": "unknown",
                "positions_digest": "",
                "redaction_status": "not_run",
                "raw_payload_emitted": "unknown",
                "items_redacted_count": 0,
            },
            "counters": {},
            "gateway_counters": {},
        }

    response = query_response.to_dict() if hasattr(query_response, "to_dict") else dict(query_response)
    payload = _mapping(response.get("payload"))
    gateway_result = _mapping(payload.get("gateway_result"))
    allowed_payload = _mapping(gateway_result.get("allowed_payload"))
    gateway_data = _mapping(allowed_payload.get("data"))
    query_payload = _mapping(payload.get("query_positions")) or _mapping(
        gateway_data.get("query_positions")
    )
    transport_metadata = _mapping(response.get("transport_metadata"))
    gateway_counters = _mapping(gateway_result.get("counters"))

    return {
        "status": str(response.get("status", "")),
        "reason_code": str(response.get("reason_code", "")),
        "endpoint": str(response.get("endpoint", "")),
        "redaction_status": str(response.get("redaction_status", "")),
        "allowed": gateway_result.get("allowed") is True,
        "blocked": gateway_result.get("blocked") is True
        or response.get("blocked_result") is not None,
        "readonly_query_authorized": gateway_data.get("readonly_query_authorized") is True
        or payload.get("readonly_query_authorized") is True,
        "operation_authorized": payload.get("operation_authorized") is True
        or allowed_payload.get("operation_authorized") is True,
        "real_operation": payload.get("real_operation") is True
        or allowed_payload.get("real_operation") is True,
        "transport_status": str(transport_metadata.get("transport_status", "")),
        "status_code": str(transport_metadata.get("status_code", "")),
        "query_positions": {
            "position_count_bucket": _position_count_bucket(
                query_payload.get("position_count")
            ),
            "positions_digest": str(query_payload.get("positions_digest", "")),
            "redaction_status": str(query_payload.get("redaction_status", "")),
            "raw_payload_emitted": query_payload.get("raw_payload_emitted", "unknown"),
            "items_redacted_count": len(query_payload.get("items_redacted", []) or []),
        },
        "counters": _safe_int_counters(_mapping(response.get("counters"))),
        "gateway_counters": _safe_int_counters(gateway_counters),
    }


def _readonly_smoke_summary(query_summary: Mapping[str, object]) -> dict[str, object]:
    query_payload = _mapping(query_summary.get("query_positions"))
    status = "pass" if _query_passed(query_summary) else str(query_summary.get("status", "blocked"))
    return {
        "endpoint_id": "query_positions",
        "path": "/qmt/account/positions",
        "required_scope": CR020_QUERY_POSITIONS_SCOPE,
        "status": status,
        "blocked_reason": str(query_summary.get("reason_code", "")),
        "position_count_bucket": query_payload.get("position_count_bucket", "unknown"),
        "positions_digest": str(query_payload.get("positions_digest", "")),
        "redaction_status": str(query_payload.get("redaction_status", "")),
        "raw_payload_included": query_payload.get("raw_payload_emitted") is True,
        "raw_account_output_included": False,
        "trade_write_attempted": False,
        "readonly_query_authorized": query_summary.get("readonly_query_authorized") is True,
        "operation_authorized": query_summary.get("operation_authorized") is True,
        "real_operation": query_summary.get("real_operation") is True,
        "transport_status": str(query_summary.get("transport_status", "")),
        "status_code": str(query_summary.get("status_code", "")),
        "items_redacted_count": int(query_payload.get("items_redacted_count", 0) or 0),
    }


def _forbidden_counters(query_summary: Mapping[str, object]) -> dict[str, int]:
    counters = _mapping(query_summary.get("counters"))
    gateway_counters = _mapping(query_summary.get("gateway_counters"))
    merged = {**gateway_counters, **counters}
    result = {
        "nas_read": 0,
        "nas_write": 0,
        "nas_list": 0,
        "nas_copy": 0,
        "nas_publish": 0,
        "nas_pull": 0,
        "env_secret_emitted": 0,
        "qmt_start_by_collector": 0,
        "miniqmt_start_by_collector": 0,
        "gateway_start_by_collector": 0,
        "account_raw_query": 0,
        "submit_order": int(merged.get("real_order", 0) or 0),
        "cancel_order": int(merged.get("real_cancel", 0) or 0),
        "simulation": int(merged.get("simulation_or_live_run", 0) or 0),
        "live": int(merged.get("simulation_or_live_run", 0) or 0),
    }
    for key in FORBIDDEN_COUNTER_KEYS:
        result[key] = int(merged.get(key, 0) or 0)
    return result


def _overall_status(
    health_summary: Mapping[str, object],
    query_summary: Mapping[str, object],
    readonly_smoke: Mapping[str, object],
    forbidden_counters: Mapping[str, int],
) -> str:
    if health_summary.get("session_ready") is not True:
        return "blocked"
    if not _query_passed(query_summary):
        return "blocked"
    if readonly_smoke.get("raw_payload_included") is True:
        return "blocked"
    if readonly_smoke.get("raw_account_output_included") is True:
        return "blocked"
    if any(int(value) != 0 for value in forbidden_counters.values()):
        return "blocked"
    return "pass"


def _query_passed(query_summary: Mapping[str, object]) -> bool:
    query_payload = _mapping(query_summary.get("query_positions"))
    return (
        query_summary.get("status") == "ok"
        and query_summary.get("allowed") is True
        and query_summary.get("blocked") is False
        and query_summary.get("readonly_query_authorized") is True
        and query_summary.get("operation_authorized") is False
        and query_summary.get("real_operation") is False
        and query_payload.get("redaction_status") == "pass"
        and query_payload.get("raw_payload_emitted") is False
    )


def _position_count_bucket(value: object) -> str:
    try:
        count = int(value)
    except (TypeError, ValueError):
        return "unknown"
    if count <= 0:
        return "zero"
    if count == 1:
        return "one"
    if count <= 10:
        return "few"
    return "many"


def _mapping(value: object) -> dict[str, object]:
    return dict(value) if isinstance(value, Mapping) else {}


def _safe_int_counters(counters: Mapping[str, object]) -> dict[str, int]:
    safe: dict[str, int] = {}
    for key, value in counters.items():
        if isinstance(value, bool):
            safe[str(key)] = int(value)
            continue
        if isinstance(value, int):
            safe[str(key)] = value
    return safe


def _ensure_summary_safe(summary: Mapping[str, object]) -> None:
    rendered = json.dumps(summary, ensure_ascii=False, sort_keys=True)
    leaked = [token for token in DISALLOWED_OUTPUT_TOKENS if token in rendered]
    if leaked:
        raise RuntimeError(
            "redacted summary contains disallowed reference markers: "
            + ", ".join(sorted(leaked))
        )


if __name__ == "__main__":
    raise SystemExit(main())
