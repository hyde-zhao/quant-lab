from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
from typing import Any, Mapping, Sequence
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.legacy.cr.check_cr099_redacted_evidence import check_redacted_evidence
from trading.qmt_client import QmtClient, QmtClientConfig, QmtResponse
from trading.qmt_runtime import (
    StdlibQmtRestTransport,
    build_runtime_config,
    build_runtime_hmac_provider,
    load_runtime_env,
)


FORBIDDEN_COUNTERS = {
    "account_id_values": 0,
    "security_code_values": 0,
    "raw_quantity_values": 0,
    "raw_cash_values": 0,
    "order_fields": 0,
    "fill_fields": 0,
    "submit_cancel_calls": 0,
    "buy_sell_calls": 0,
    "nas_operations": 0,
    "provider_lake_publish": 0,
}


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    env = load_runtime_env(args.env_file)
    config = build_runtime_config(
        env,
        host=args.host,
        port=args.port or None,
        runtime_authorization_ref=args.authorization_ref,
    )
    base_url = (args.base_url or config.base_url).rstrip("/")

    health = _fetch_json(f"{base_url}/qmt/health", args.timeout_seconds)
    capabilities = _fetch_json(f"{base_url}/qmt/capabilities", args.timeout_seconds)
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
        run_id=args.run_id,
        request_id=args.request_id or f"{args.run_id}-query-positions",
        authorization_ref=args.authorization_ref,
        timeout_seconds=args.timeout_seconds,
    )

    evidence = build_cr099_evidence(
        run_id=args.run_id,
        authorization_ref=args.authorization_ref,
        health=health,
        capabilities=capabilities,
        query_response=query_response,
    )
    output_path = Path(args.output_json)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    rendered = json.dumps(evidence, ensure_ascii=False, indent=2, sort_keys=True)
    output_path.write_text(f"{rendered}\n", encoding="utf-8")

    check = check_redacted_evidence(output_path)
    print(json.dumps(check.to_dict(), ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if check.passed and evidence["overall_status"] == "pass" else 2


def build_cr099_evidence(
    *,
    run_id: str,
    authorization_ref: str,
    health: Mapping[str, object],
    capabilities: Mapping[str, object],
    query_response: QmtResponse | Mapping[str, object],
) -> dict[str, object]:
    query = _query_summary(query_response)
    health_summary = _health_summary(health)
    capability_summary = _capability_summary(capabilities)
    counters = _forbidden_counters(query)
    overall_status = "pass" if _passed(health_summary, capability_summary, query, counters) else "blocked"
    return {
        "schema_version": 1,
        "cr_id": "CR-099",
        "run_id": run_id,
        "authorization_ref": authorization_ref,
        "generated_at": datetime.now(tz=timezone.utc).isoformat(),
        "execution_mode": "codex-runner-authorized",
        "overall_status": overall_status,
        "endpoints": {
            "health": health_summary,
            "capabilities": capability_summary,
            "query_positions_readonly": {
                "attempted": True,
                "status": query["status"],
                "reason_code": query["reason_code"],
                "position_count_bucket": query["position_count_bucket"],
                "positions_digest": query["positions_digest"],
                "items_redacted_count": query["items_redacted_count"],
                "raw_payload_emitted": False,
            },
        },
        "forbidden_counters": counters,
    }


def _parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Collect runner readonly redacted evidence.")
    parser.add_argument("--env-file", required=True)
    parser.add_argument("--base-url", default="")
    parser.add_argument("--host", default="")
    parser.add_argument("--port", type=int, default=0)
    parser.add_argument("--authorization-ref", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--request-id", default="")
    parser.add_argument("--timeout-seconds", type=int, default=10)
    parser.add_argument("--output-json", required=True)
    return parser.parse_args(argv)


def _fetch_json(url: str, timeout_seconds: int) -> dict[str, object]:
    try:
        response = urlopen(url, timeout=timeout_seconds)
        payload = json.loads(response.read().decode("utf-8"))
        return dict(payload) if isinstance(payload, Mapping) else {"status": "blocked"}
    except HTTPError as exc:
        try:
            payload = json.loads(exc.read().decode("utf-8"))
        except Exception:
            payload = {}
        result = dict(payload) if isinstance(payload, Mapping) else {}
        result.setdefault("status", "blocked")
        return result
    except (TimeoutError, URLError, OSError) as exc:
        return {"status": "blocked", "blocked_reason": type(exc).__name__}


def _health_summary(payload: Mapping[str, object]) -> dict[str, object]:
    return {
        "attempted": True,
        "status": _status(payload),
        "session_ready": payload.get("session_ready") is True,
        "raw_payload_emitted": False,
    }


def _capability_summary(payload: Mapping[str, object]) -> dict[str, object]:
    capabilities = payload.get("capabilities")
    if isinstance(capabilities, Mapping):
        capabilities = capabilities.get("capabilities")
    endpoint_ids = payload.get("endpoint_ids")
    values = [str(item) for item in capabilities] if isinstance(capabilities, list) else []
    if isinstance(endpoint_ids, list):
        values.extend(str(item) for item in endpoint_ids)
    return {
        "attempted": True,
        "status": "ok" if values else _status(payload),
        "readonly_supported": "query_positions" in values or "query_positions_readonly" in values,
        "raw_payload_emitted": False,
    }


def _query_summary(response: QmtResponse | Mapping[str, object]) -> dict[str, object]:
    current = response.to_dict() if hasattr(response, "to_dict") else dict(response)
    payload = _mapping(current.get("payload"))
    gateway_result = _mapping(payload.get("gateway_result"))
    allowed_payload = _mapping(gateway_result.get("allowed_payload"))
    data = _mapping(allowed_payload.get("data"))
    query_positions = _mapping(payload.get("query_positions")) or _mapping(data.get("query_positions"))
    count = _int(query_positions.get("position_count"))
    digest = str(query_positions.get("positions_digest", ""))
    if not digest.startswith("sha256:"):
        digest = "sha256:" + hashlib.sha256(f"{count}|{current.get('status', '')}".encode("utf-8")).hexdigest()
    items = query_positions.get("items_redacted")
    items_count = len(items) if isinstance(items, list) else _int_zero(query_positions.get("items_redacted_count"))
    return {
        "status": _status(current),
        "reason_code": str(current.get("reason_code", "")),
        "position_count_bucket": _position_count_bucket(count),
        "positions_digest": digest,
        "items_redacted_count": items_count,
        "raw_payload_emitted": query_positions.get("raw_payload_emitted") is True,
        "redaction_status": str(query_positions.get("redaction_status", "")),
        "readonly_query_authorized": data.get("readonly_query_authorized") is True
        or payload.get("readonly_query_authorized") is True,
        "operation_authorized": payload.get("operation_authorized") is True
        or allowed_payload.get("operation_authorized") is True,
        "real_operation": payload.get("real_operation") is True
        or allowed_payload.get("real_operation") is True,
        "counters": _mapping(current.get("counters")),
    }


def _forbidden_counters(query: Mapping[str, object]) -> dict[str, int]:
    counters = _mapping(query.get("counters"))
    result = dict(FORBIDDEN_COUNTERS)
    result["submit_cancel_calls"] = max(
        _int_zero(counters.get("real_order")),
        _int_zero(counters.get("real_cancel")),
        _int_zero(counters.get("submit_order")),
        _int_zero(counters.get("cancel_order")),
    )
    result["buy_sell_calls"] = max(_int_zero(counters.get("real_order")), _int_zero(counters.get("real_cancel")))
    result["provider_lake_publish"] = max(
        _int_zero(counters.get("provider_fetch")),
        _int_zero(counters.get("lake_write")),
        _int_zero(counters.get("publish")),
    )
    return result


def _passed(
    health: Mapping[str, object],
    capabilities: Mapping[str, object],
    query: Mapping[str, object],
    counters: Mapping[str, int],
) -> bool:
    return (
        health.get("status") == "ok"
        and health.get("session_ready") is True
        and capabilities.get("status") == "ok"
        and capabilities.get("readonly_supported") is True
        and query.get("status") == "ok"
        and query.get("redaction_status") == "pass"
        and query.get("raw_payload_emitted") is False
        and query.get("readonly_query_authorized") is True
        and query.get("operation_authorized") is False
        and query.get("real_operation") is False
        and all(value == 0 for value in counters.values())
    )


def _position_count_bucket(count: int | None) -> str:
    if count is None:
        return "unknown"
    if count <= 0:
        return "zero"
    if count <= 10:
        return "one_to_ten"
    return "gt_ten"


def _mapping(value: object) -> dict[str, object]:
    return dict(value) if isinstance(value, Mapping) else {}


def _status(payload: Mapping[str, object]) -> str:
    value = str(payload.get("status", "blocked"))
    return "ok" if value in {"ok", "allowed"} else value


def _int(value: object) -> int | None:
    try:
        return int(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _int_zero(value: object) -> int:
    current = _int(value)
    return 0 if current is None else current


if __name__ == "__main__":
    raise SystemExit(main())
