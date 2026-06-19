"""CR091 脱敏 evidence summary。"""

from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path
import re
from typing import Any, Mapping

from trading.strategy_runner.adapters import AdapterResult, zero_cr091_operation_counters
from trading.strategy_runner.readonly_gateway import ReadonlyGatewayResult


EVIDENCE_SCHEMA_VERSION = "cr091-strategy-runner-evidence-v1"
SENSITIVE_PATTERNS = tuple(
    re.compile(pattern, re.IGNORECASE)
    for pattern in (
        "token",
        "secret",
        "password",
        "passwd",
        "account",
        "raw_positions",
        "raw_orders",
        "qmt_log",
        "credential",
    )
)
STRUCTURAL_REDACTION_KEYS = {"redaction_assurance", "forbidden_operation_counters"}
READONLY_COUNTER_ALIASES = {
    "service_start": "qmt_start",
    "qmt_operation": "qmt_start",
    "qmt_api_call": "qmt_start",
    "real_order": "submit_order",
    "real_cancel": "cancel_order",
    "account_query": "account_raw_query",
    "broker_lake_write": "lake_write",
    "publish": "catalog_publish",
    "current_pointer_publish": "catalog_publish",
    "simulation_or_live_run": "simulation",
    "service_bind": "gateway_start",
    "http_client_call": "gateway_socket_open",
}


class EvidenceRedactionError(ValueError):
    """evidence 脱敏检查失败。"""


@dataclass(frozen=True, slots=True)
class EvidenceSummary:
    status: str
    run_id: str
    package_id: str
    adapter_type: str
    strategy_id: str
    target_count: int
    order_intent_count: int
    readonly_reconciliation_status: str
    forbidden_operation_counters: Mapping[str, int] = field(default_factory=zero_cr091_operation_counters)
    redaction_assurance: Mapping[str, bool] = field(default_factory=dict)
    readonly_health_status: str = "not_run"
    readonly_capabilities_status: str = "not_run"
    readonly_position_count: int = 0
    readonly_positions_digest: str = ""
    readonly_items_redacted_count: int = 0
    readonly_transport_kind: str = ""
    runtime_authorization_ref: str = ""
    runtime_env_ref: str = ""
    schema_version: str = EVIDENCE_SCHEMA_VERSION
    not_authorization: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "status": self.status,
            "run_id": self.run_id,
            "package_id": self.package_id,
            "adapter_type": self.adapter_type,
            "strategy_id": self.strategy_id,
            "target_count": self.target_count,
            "order_intent_count": self.order_intent_count,
            "readonly_reconciliation_status": self.readonly_reconciliation_status,
            "forbidden_operation_counters": dict(self.forbidden_operation_counters),
            "redaction_assurance": dict(self.redaction_assurance),
            "readonly_health_status": self.readonly_health_status,
            "readonly_capabilities_status": self.readonly_capabilities_status,
            "readonly_position_count": self.readonly_position_count,
            "readonly_positions_digest": self.readonly_positions_digest,
            "readonly_items_redacted_count": self.readonly_items_redacted_count,
            "readonly_transport_kind": self.readonly_transport_kind,
            "runtime_authorization_ref": self.runtime_authorization_ref,
            "runtime_env_ref": self.runtime_env_ref,
            "not_authorization": self.not_authorization,
        }


def build_evidence_summary(
    *,
    run_id: str,
    package_id: str,
    adapter_type: str,
    adapter_result: AdapterResult,
    readonly_result: ReadonlyGatewayResult | None = None,
    readonly_health_result: ReadonlyGatewayResult | None = None,
    readonly_capabilities_result: ReadonlyGatewayResult | None = None,
) -> EvidenceSummary:
    target_count = 0 if adapter_result.target_portfolio is None else len(adapter_result.target_portfolio.target_symbols)
    forbidden = zero_cr091_operation_counters()
    forbidden.update({key: int(value or 0) for key, value in adapter_result.operation_counters.items() if key in forbidden})
    readonly_ok = True
    readonly_results = tuple(
        result
        for result in (readonly_health_result, readonly_capabilities_result, readonly_result)
        if result is not None
    )
    for current_readonly in readonly_results:
        assert_redacted(dict(current_readonly.payload))
        readonly_ok = readonly_ok and current_readonly.status == "ok"
        for key, value in current_readonly.operation_counters.items():
            mapped_key = READONLY_COUNTER_ALIASES.get(str(key), str(key))
            if mapped_key in forbidden:
                forbidden[mapped_key] = forbidden.get(mapped_key, 0) + int(value or 0)
        if current_readonly.payload.get("raw_payload_emitted") is True:
            forbidden["raw_positions_emit"] = forbidden.get("raw_positions_emit", 0) + 1
        redaction_status = str(current_readonly.payload.get("redaction_status", "pass")).lower()
        if redaction_status not in {"pass", "redacted"}:
            readonly_ok = False
    status = "pass" if adapter_result.passed and readonly_ok and all(value == 0 for value in forbidden.values()) else "blocked"
    summary = EvidenceSummary(
        status=status,
        run_id=run_id,
        package_id=package_id,
        adapter_type=adapter_type,
        strategy_id=adapter_result.strategy_id,
        target_count=target_count,
        order_intent_count=len(adapter_result.order_intents),
        readonly_reconciliation_status="not_run" if readonly_result is None else readonly_result.status,
        forbidden_operation_counters=forbidden,
        redaction_assurance={
            "token_emitted": False,
            "secret_emitted": False,
            "account_emitted": False,
            "raw_positions_emitted": False,
            "raw_orders_emitted": False,
            "qmt_logs_emitted": False,
        },
        readonly_health_status="not_run" if readonly_health_result is None else readonly_health_result.status,
        readonly_capabilities_status="not_run" if readonly_capabilities_result is None else readonly_capabilities_result.status,
        readonly_position_count=_int_payload(readonly_result, "position_count"),
        readonly_positions_digest=_str_payload(readonly_result, "positions_digest"),
        readonly_items_redacted_count=_int_payload(readonly_result, "items_redacted_count"),
        readonly_transport_kind="" if readonly_result is None else readonly_result.transport_kind,
        runtime_authorization_ref="" if readonly_result is None else readonly_result.authorization_ref,
        runtime_env_ref="" if readonly_result is None else readonly_result.runtime_env_ref,
    )
    assert_redacted(summary.to_dict())
    return summary


def write_evidence_summary(path: str | Path, summary: EvidenceSummary) -> None:
    payload = summary.to_dict()
    assert_redacted(payload)
    Path(path).write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def assert_redacted(payload: Mapping[str, Any]) -> None:
    _assert_redacted_value(payload, path="")


def _assert_redacted_value(value: Any, *, path: str) -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            key_text = str(key)
            child_path = f"{path}.{key_text}" if path else key_text
            if key_text in STRUCTURAL_REDACTION_KEYS:
                continue
            _raise_if_sensitive(key_text)
            _assert_redacted_value(item, path=child_path)
        return
    if isinstance(value, list | tuple):
        for index, item in enumerate(value):
            _assert_redacted_value(item, path=f"{path}[{index}]")
        return
    if isinstance(value, str):
        _raise_if_sensitive(value)


def _raise_if_sensitive(text: str) -> None:
    for pattern in SENSITIVE_PATTERNS:
        if pattern.search(text):
            raise EvidenceRedactionError("blocked_redaction_failed")


def _int_payload(readonly_result: ReadonlyGatewayResult | None, key: str) -> int:
    if readonly_result is None:
        return 0
    return int(readonly_result.payload.get(key, 0) or 0)


def _str_payload(readonly_result: ReadonlyGatewayResult | None, key: str) -> str:
    if readonly_result is None:
        return ""
    return str(readonly_result.payload.get(key, ""))
