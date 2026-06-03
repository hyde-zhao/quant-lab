"""CR015-S01 的 signed file-drop transport 合同。

本模块只校验 metadata 并生成结构化 ack；不得写文件、打开 socket、读取凭据
或调用 broker SDK。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Mapping

from trading.qmt_environment import (
    AdapterMode,
    CR015_ALLOWED_ADAPTER_MODES,
    ForbiddenOperationCounters,
    NodeRole,
)


class TransportStatus(str, Enum):
    """signed file-drop 合同的投递状态。"""

    ACCEPTED = "accepted"
    REJECTED = "rejected"
    TIMEOUT = "timeout"
    UNKNOWN = "unknown"


class TransportKind(str, Enum):
    """QMT transport 合同类型；S03 仅新增 REST gateway 的离线合同。"""

    SIGNED_FILE_DROP = "signed_file_drop"
    REST_GATEWAY = "rest_gateway"


class TransportErrorCode(str, Enum):
    """暴露给后续 adapter Story 的结构化 transport 错误码。"""

    INVALID_SIGNATURE = "invalid_signature"
    EXPIRED_PAYLOAD = "expired_payload"
    MODE_NOT_AUTHORIZED = "mode_not_authorized"
    CREDENTIAL_ACCESS_BLOCKED = "credential_access_blocked"
    REAL_QMT_BLOCKED = "real_qmt_blocked"
    MISSING_REQUIRED_FIELD = "missing_required_field"
    UNKNOWN_FIELD = "unknown_field"
    MALFORMED_PAYLOAD = "malformed_payload"
    REST_GATEWAY_UNAVAILABLE = "rest_gateway_unavailable"
    REST_GATEWAY_TIMEOUT = "rest_gateway_timeout"
    AUTH_REQUIRED = "auth_required"
    AUTH_FAILED = "auth_failed"


REQUIRED_PAYLOAD_FIELDS = frozenset(
    {
        "run_id",
        "strategy_id",
        "payload_id",
        "payload_checksum",
        "signature_ref",
        "created_at",
        "expires_at",
        "node_role",
        "adapter_mode",
    }
)

ADAPTER_PAYLOAD_OPTIONAL_FIELDS = frozenset(
    {
        "intent_id",
        "adapter_request_id",
        "risk_status",
        "execution_price_policy",
        "broker_event_type",
    }
)

ADAPTER_PAYLOAD_METADATA_FIELDS = (
    REQUIRED_PAYLOAD_FIELDS | ADAPTER_PAYLOAD_OPTIONAL_FIELDS
)

ADAPTER_FACING_TRANSPORT_ERROR_CODES = frozenset(
    {
        TransportErrorCode.INVALID_SIGNATURE,
        TransportErrorCode.EXPIRED_PAYLOAD,
        TransportErrorCode.MODE_NOT_AUTHORIZED,
        TransportErrorCode.CREDENTIAL_ACCESS_BLOCKED,
        TransportErrorCode.MISSING_REQUIRED_FIELD,
        TransportErrorCode.UNKNOWN_FIELD,
        TransportErrorCode.MALFORMED_PAYLOAD,
    }
)

REST_GATEWAY_TRANSPORT_KIND = TransportKind.REST_GATEWAY

REST_GATEWAY_REQUIRED_METADATA_FIELDS = frozenset(
    {
        "endpoint",
        "run_id",
        "stage",
        "mode",
        "redaction_label",
    }
)

REST_GATEWAY_OPTIONAL_METADATA_FIELDS = frozenset(
    {
        "transport_kind",
        "request_id",
        "intent_id",
        "authorization_ref",
        "client_id_ref",
        "timestamp_utc",
        "nonce_ref",
        "signature_ref",
        "body_checksum",
        "schema_version",
        "timeout_seconds",
    }
)

REST_GATEWAY_PAYLOAD_METADATA_FIELDS = (
    REST_GATEWAY_REQUIRED_METADATA_FIELDS | REST_GATEWAY_OPTIONAL_METADATA_FIELDS
)

REST_GATEWAY_AUTH_HEADER_SLOTS = frozenset(
    {
        "client_id_ref",
        "timestamp_utc",
        "nonce_ref",
        "signature_ref",
    }
)

REST_GATEWAY_TRANSPORT_ERROR_CODES = frozenset(
    {
        TransportErrorCode.REST_GATEWAY_UNAVAILABLE,
        TransportErrorCode.REST_GATEWAY_TIMEOUT,
        TransportErrorCode.AUTH_REQUIRED,
        TransportErrorCode.AUTH_FAILED,
        TransportErrorCode.CREDENTIAL_ACCESS_BLOCKED,
        TransportErrorCode.MISSING_REQUIRED_FIELD,
        TransportErrorCode.UNKNOWN_FIELD,
        TransportErrorCode.MALFORMED_PAYLOAD,
        TransportErrorCode.REAL_QMT_BLOCKED,
    }
)

REST_GATEWAY_DEFAULT_TIMEOUT_SECONDS = 3
REST_GATEWAY_MAX_TIMEOUT_SECONDS = 30

SENSITIVE_FIELD_FRAGMENTS = frozenset(
    {
        "account",
        "token",
        "session",
        "cookie",
        "password",
        "secret",
        "private_key",
        "credential",
        ".env",
    }
)

SENSITIVE_VALUE_MARKERS = frozenset(
    {
        "token=",
        "session=",
        "cookie=",
        "password=",
        "secret=",
        "private_key=",
        ".env",
    }
)


@dataclass(frozen=True)
class TransportPayload:
    """signed file-drop payload 的白名单 metadata。"""

    run_id: str
    strategy_id: str
    payload_id: str
    payload_checksum: str
    signature_ref: str
    created_at: datetime
    expires_at: datetime
    node_role: NodeRole
    adapter_mode: AdapterMode


@dataclass(frozen=True)
class TransportAck:
    """payload 校验器和 mock transport 返回的结构化 ack。"""

    status: TransportStatus
    payload_id: str | None = None
    error_code: TransportErrorCode | None = None
    message: str = ""
    observed_at: datetime | None = None
    counters: Mapping[str, int] = field(
        default_factory=lambda: ForbiddenOperationCounters().to_dict()
    )


@dataclass(frozen=True)
class PayloadBuildResult:
    """从不可信 metadata 构造 payload 的结果。"""

    accepted: bool
    payload: TransportPayload | None
    ack: TransportAck
    sanitized_metadata: Mapping[str, str]


@dataclass(frozen=True)
class RestGatewayPayloadMetadata:
    """REST gateway payload 的脱敏 metadata 合同；不表示真实网络调用。"""

    endpoint: str
    run_id: str
    stage: str
    mode: str
    redaction_label: str
    transport_kind: TransportKind = REST_GATEWAY_TRANSPORT_KIND
    request_id: str = ""
    intent_id: str = ""
    authorization_ref: str = ""
    client_id_ref: str = ""
    timestamp_utc: str = ""
    nonce_ref: str = ""
    signature_ref: str = ""
    body_checksum: str = ""
    schema_version: str = "cr019-s03-rest-gateway-v1"
    timeout_seconds: int = REST_GATEWAY_DEFAULT_TIMEOUT_SECONDS

    def to_dict(self) -> dict[str, str]:
        return {
            "transport_kind": self.transport_kind.value,
            "endpoint": self.endpoint,
            "run_id": self.run_id,
            "stage": self.stage,
            "mode": self.mode,
            "redaction_label": self.redaction_label,
            "request_id": self.request_id,
            "intent_id": self.intent_id,
            "authorization_ref": self.authorization_ref,
            "client_id_ref": self.client_id_ref,
            "timestamp_utc": self.timestamp_utc,
            "nonce_ref": self.nonce_ref,
            "signature_ref": self.signature_ref,
            "body_checksum": self.body_checksum,
            "schema_version": self.schema_version,
            "timeout_seconds": str(self.timeout_seconds),
        }


@dataclass(frozen=True)
class RestGatewayPayloadBuildResult:
    """从不可信 metadata 构造 REST gateway payload metadata 的结果。"""

    accepted: bool
    metadata: RestGatewayPayloadMetadata | None
    ack: TransportAck
    sanitized_metadata: Mapping[str, str]


def build_transport_payload(
    metadata: Mapping[str, object],
    *,
    now: datetime | None = None,
) -> PayloadBuildResult:
    """基于严格 metadata 白名单构造 transport payload。"""

    safe_metadata: dict[str, str] = {}
    payload_id = str(metadata.get("payload_id", "")) or None

    sensitive_key = _first_sensitive_key(metadata)
    if sensitive_key is not None:
        return _rejected_build_result(
            payload_id,
            TransportErrorCode.CREDENTIAL_ACCESS_BLOCKED,
            f"sensitive metadata field blocked: {sensitive_key}",
        )

    unknown_fields = set(metadata) - REQUIRED_PAYLOAD_FIELDS
    if unknown_fields:
        field_name = sorted(unknown_fields)[0]
        return _rejected_build_result(
            payload_id,
            TransportErrorCode.UNKNOWN_FIELD,
            f"unknown metadata field blocked: {field_name}",
        )

    missing_fields = [field for field in sorted(REQUIRED_PAYLOAD_FIELDS) if not metadata.get(field)]
    if missing_fields:
        return _rejected_build_result(
            payload_id,
            TransportErrorCode.MISSING_REQUIRED_FIELD,
            f"missing required metadata field: {missing_fields[0]}",
        )

    if _contains_sensitive_value(metadata):
        return _rejected_build_result(
            payload_id,
            TransportErrorCode.CREDENTIAL_ACCESS_BLOCKED,
            "sensitive metadata value blocked",
        )

    try:
        node_role = NodeRole(str(metadata["node_role"]))
        adapter_mode = AdapterMode(str(metadata["adapter_mode"]))
        created_at = _parse_datetime(metadata["created_at"])
        expires_at = _parse_datetime(metadata["expires_at"])
    except (KeyError, TypeError, ValueError):
        return _rejected_build_result(
            payload_id,
            TransportErrorCode.MALFORMED_PAYLOAD,
            "payload metadata is malformed",
        )

    if adapter_mode not in CR015_ALLOWED_ADAPTER_MODES:
        return _rejected_build_result(
            payload_id,
            TransportErrorCode.MODE_NOT_AUTHORIZED,
            "adapter_mode is not authorized by CR015-S01",
        )

    payload = TransportPayload(
        run_id=str(metadata["run_id"]),
        strategy_id=str(metadata["strategy_id"]),
        payload_id=str(metadata["payload_id"]),
        payload_checksum=str(metadata["payload_checksum"]),
        signature_ref=str(metadata["signature_ref"]),
        created_at=created_at,
        expires_at=expires_at,
        node_role=node_role,
        adapter_mode=adapter_mode,
    )
    ack = validate_payload_metadata(payload, now=now)
    if ack.status is not TransportStatus.ACCEPTED:
        return PayloadBuildResult(
            accepted=False,
            payload=None,
            ack=ack,
            sanitized_metadata=sanitize_payload_for_audit(payload),
        )

    safe_metadata.update(sanitize_payload_for_audit(payload))
    return PayloadBuildResult(
        accepted=True,
        payload=payload,
        ack=ack,
        sanitized_metadata=safe_metadata,
    )


def validate_payload_metadata(
    payload: TransportPayload,
    *,
    now: datetime | None = None,
) -> TransportAck:
    """校验签名引用、过期时间、checksum 和模式。"""

    observed_at = _utc_now() if now is None else _ensure_aware_utc(now)
    if payload.adapter_mode not in CR015_ALLOWED_ADAPTER_MODES:
        return rejected_ack(
            payload.payload_id,
            TransportErrorCode.MODE_NOT_AUTHORIZED,
            "adapter_mode is not authorized by CR015-S01",
            observed_at=observed_at,
        )
    if not payload.signature_ref:
        return rejected_ack(
            payload.payload_id,
            TransportErrorCode.INVALID_SIGNATURE,
            "signature_ref is required",
            observed_at=observed_at,
        )
    if not payload.payload_checksum:
        return rejected_ack(
            payload.payload_id,
            TransportErrorCode.MISSING_REQUIRED_FIELD,
            "payload_checksum is required",
            observed_at=observed_at,
        )
    if _contains_sensitive_value({"signature_ref": payload.signature_ref}):
        return rejected_ack(
            payload.payload_id,
            TransportErrorCode.CREDENTIAL_ACCESS_BLOCKED,
            "signature_ref must be a reference or digest only",
            observed_at=observed_at,
        )
    if payload.expires_at <= observed_at:
        return rejected_ack(
            payload.payload_id,
            TransportErrorCode.EXPIRED_PAYLOAD,
            "payload has expired",
            observed_at=observed_at,
        )

    return TransportAck(
        status=TransportStatus.ACCEPTED,
        payload_id=payload.payload_id,
        observed_at=observed_at,
        counters=ForbiddenOperationCounters().to_dict(),
    )


def sanitize_payload_for_audit(payload: TransportPayload) -> dict[str, str]:
    """返回白名单且不含凭据的审计表示。"""

    return {
        "run_id": payload.run_id,
        "strategy_id": payload.strategy_id,
        "payload_id": payload.payload_id,
        "payload_checksum": payload.payload_checksum,
        "signature_ref": payload.signature_ref,
        "created_at": payload.created_at.isoformat(),
        "expires_at": payload.expires_at.isoformat(),
        "node_role": payload.node_role.value,
        "adapter_mode": payload.adapter_mode.value,
    }


def build_rest_gateway_payload_metadata(
    metadata: Mapping[str, object],
) -> RestGatewayPayloadBuildResult:
    """构造 REST gateway metadata；只做离线合同校验，不执行网络请求。"""

    payload_id = str(
        metadata.get("request_id") or metadata.get("intent_id") or metadata.get("run_id", "")
    ) or None

    sensitive_key = _first_sensitive_key(metadata)
    if sensitive_key is not None:
        return _rejected_rest_gateway_build_result(
            payload_id,
            TransportErrorCode.CREDENTIAL_ACCESS_BLOCKED,
            f"sensitive metadata field blocked: {sensitive_key}",
        )

    unknown_fields = set(metadata) - REST_GATEWAY_PAYLOAD_METADATA_FIELDS
    if unknown_fields:
        field_name = sorted(unknown_fields)[0]
        return _rejected_rest_gateway_build_result(
            payload_id,
            TransportErrorCode.UNKNOWN_FIELD,
            f"unknown REST gateway metadata field blocked: {field_name}",
        )

    missing_fields = [
        field for field in sorted(REST_GATEWAY_REQUIRED_METADATA_FIELDS) if not metadata.get(field)
    ]
    if missing_fields:
        return _rejected_rest_gateway_build_result(
            payload_id,
            TransportErrorCode.MISSING_REQUIRED_FIELD,
            f"missing required REST gateway metadata field: {missing_fields[0]}",
        )

    if _contains_sensitive_value(metadata):
        return _rejected_rest_gateway_build_result(
            payload_id,
            TransportErrorCode.CREDENTIAL_ACCESS_BLOCKED,
            "sensitive REST gateway metadata value blocked",
        )

    transport_kind = str(metadata.get("transport_kind", REST_GATEWAY_TRANSPORT_KIND.value))
    if transport_kind != REST_GATEWAY_TRANSPORT_KIND.value:
        return _rejected_rest_gateway_build_result(
            payload_id,
            TransportErrorCode.MALFORMED_PAYLOAD,
            "transport_kind must be rest_gateway",
        )

    try:
        timeout_seconds = int(
            metadata.get("timeout_seconds", REST_GATEWAY_DEFAULT_TIMEOUT_SECONDS)
        )
    except (TypeError, ValueError):
        return _rejected_rest_gateway_build_result(
            payload_id,
            TransportErrorCode.MALFORMED_PAYLOAD,
            "timeout_seconds must be an integer",
        )

    if timeout_seconds <= 0 or timeout_seconds > REST_GATEWAY_MAX_TIMEOUT_SECONDS:
        return _rejected_rest_gateway_build_result(
            payload_id,
            TransportErrorCode.MALFORMED_PAYLOAD,
            "timeout_seconds is outside the REST gateway contract range",
        )

    payload = RestGatewayPayloadMetadata(
        endpoint=str(metadata["endpoint"]),
        run_id=str(metadata["run_id"]),
        stage=str(metadata["stage"]),
        mode=str(metadata["mode"]),
        redaction_label=str(metadata["redaction_label"]),
        request_id=str(metadata.get("request_id", "")),
        intent_id=str(metadata.get("intent_id", "")),
        authorization_ref=str(metadata.get("authorization_ref", "")),
        client_id_ref=str(metadata.get("client_id_ref", "")),
        timestamp_utc=str(metadata.get("timestamp_utc", "")),
        nonce_ref=str(metadata.get("nonce_ref", "")),
        signature_ref=str(metadata.get("signature_ref", "")),
        body_checksum=str(metadata.get("body_checksum", "")),
        schema_version=str(metadata.get("schema_version", "cr019-s03-rest-gateway-v1")),
        timeout_seconds=timeout_seconds,
    )
    sanitized = payload.to_dict()
    return RestGatewayPayloadBuildResult(
        accepted=True,
        metadata=payload,
        ack=accepted_ack(payload.request_id or payload.intent_id or payload.run_id),
        sanitized_metadata=sanitized,
    )


def accepted_ack(payload_id: str, *, observed_at: datetime | None = None) -> TransportAck:
    return TransportAck(
        status=TransportStatus.ACCEPTED,
        payload_id=payload_id,
        observed_at=_utc_now() if observed_at is None else _ensure_aware_utc(observed_at),
        counters=ForbiddenOperationCounters().to_dict(),
    )


def rejected_ack(
    payload_id: str | None,
    error_code: TransportErrorCode,
    message: str,
    *,
    observed_at: datetime | None = None,
) -> TransportAck:
    return TransportAck(
        status=TransportStatus.REJECTED,
        payload_id=payload_id,
        error_code=error_code,
        message=message,
        observed_at=_utc_now() if observed_at is None else _ensure_aware_utc(observed_at),
        counters=ForbiddenOperationCounters().to_dict(),
    )


def timeout_ack(payload_id: str | None, *, observed_at: datetime | None = None) -> TransportAck:
    return TransportAck(
        status=TransportStatus.TIMEOUT,
        payload_id=payload_id,
        message="transport acknowledgement timed out",
        observed_at=_utc_now() if observed_at is None else _ensure_aware_utc(observed_at),
        counters=ForbiddenOperationCounters().to_dict(),
    )


def rest_gateway_timeout_ack(
    payload_id: str | None,
    *,
    observed_at: datetime | None = None,
) -> TransportAck:
    """REST gateway timeout 的结构化合同；不代表真实请求已发出。"""

    return TransportAck(
        status=TransportStatus.TIMEOUT,
        payload_id=payload_id,
        error_code=TransportErrorCode.REST_GATEWAY_TIMEOUT,
        message="REST gateway transport acknowledgement timed out",
        observed_at=_utc_now() if observed_at is None else _ensure_aware_utc(observed_at),
        counters=ForbiddenOperationCounters().to_dict(),
    )


def unknown_ack(payload_id: str | None, *, observed_at: datetime | None = None) -> TransportAck:
    return TransportAck(
        status=TransportStatus.UNKNOWN,
        payload_id=payload_id,
        message="transport acknowledgement status is unknown",
        observed_at=_utc_now() if observed_at is None else _ensure_aware_utc(observed_at),
        counters=ForbiddenOperationCounters().to_dict(),
    )


def _rejected_build_result(
    payload_id: str | None,
    error_code: TransportErrorCode,
    message: str,
) -> PayloadBuildResult:
    ack = rejected_ack(payload_id, error_code, message)
    return PayloadBuildResult(
        accepted=False,
        payload=None,
        ack=ack,
        sanitized_metadata={},
    )


def _rejected_rest_gateway_build_result(
    payload_id: str | None,
    error_code: TransportErrorCode,
    message: str,
) -> RestGatewayPayloadBuildResult:
    ack = rejected_ack(payload_id, error_code, message)
    return RestGatewayPayloadBuildResult(
        accepted=False,
        metadata=None,
        ack=ack,
        sanitized_metadata={},
    )


def _first_sensitive_key(metadata: Mapping[str, object]) -> str | None:
    for key in metadata:
        normalized = str(key).lower()
        if any(fragment in normalized for fragment in SENSITIVE_FIELD_FRAGMENTS):
            return str(key)
    return None


def _contains_sensitive_value(metadata: Mapping[str, object]) -> bool:
    for value in metadata.values():
        normalized = str(value).lower()
        if any(marker in normalized for marker in SENSITIVE_VALUE_MARKERS):
            return True
    return False


def _parse_datetime(value: object) -> datetime:
    if isinstance(value, datetime):
        return _ensure_aware_utc(value)
    parsed = datetime.fromisoformat(str(value))
    return _ensure_aware_utc(parsed)


def _ensure_aware_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _utc_now() -> datetime:
    return datetime.now(tz=UTC)
