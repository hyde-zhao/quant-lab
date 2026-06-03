"""CR019-S05 的 QMT pairing / HMAC 鉴权离线合同。

本模块只做内存对象校验和 HMAC 计算，不读取配置文件、环境变量或凭据，
不启动服务、不打开网络连接、不调用 QMT / MiniQMT / XtQuant。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
import hashlib
import hmac
from typing import Mapping, MutableSet, Sequence


DEFAULT_AUTH_MODE = "pairing_hmac"
NO_AUTH_MODE = "no_auth"
FIXTURE_PAIRING_CODE = "fixture-only-pairing-code"

DEFAULT_PAIRING_REQUEST_TTL_SECONDS = 600
DEFAULT_PAIRING_CODE_TTL_SECONDS = 300
DEFAULT_HMAC_CLOCK_SKEW_SECONDS = 300
DEFAULT_NONCE_TTL_SECONDS = 600

QMT_HMAC_HEADER_CLIENT_ID = "x-qmt-client-id"
QMT_HMAC_HEADER_TIMESTAMP = "x-qmt-timestamp"
QMT_HMAC_HEADER_NONCE = "x-qmt-nonce"
QMT_HMAC_HEADER_SIGNATURE = "x-qmt-signature"

QMT_AUTH_FORBIDDEN_COUNTER_FIELDS: tuple[str, ...] = (
    "dependency_change",
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
    "service_start",
    "service_bind",
    "http_client_call",
    "gateway_socket_open",
)

TRADING_AUTHORIZATION_SCOPES = frozenset(
    {"simulation", "live", "account", "cancel", "simulation_submit", "live_submit"}
)


class QmtAuthBlockedReason(str, Enum):
    """S05 鉴权合同的稳定阻断原因。"""

    AUTH_HEADER_MISSING = "auth_header_missing"
    AUTH_PAIRING_PENDING = "auth_pairing_pending"
    AUTH_PAIRING_EXPIRED = "auth_pairing_expired"
    AUTH_CLIENT_NOT_APPROVED = "auth_client_not_approved"
    AUTH_TIMESTAMP_SKEW = "auth_timestamp_skew"
    AUTH_NONCE_REPLAY = "auth_nonce_replay"
    AUTH_SCOPE_DENIED = "auth_scope_denied"
    AUTH_SIGNATURE_MISMATCH = "auth_signature_mismatch"
    AUTH_NO_AUTH_NOT_ALLOWED = "auth_no_auth_not_allowed"
    AUTH_SECRET_UNAVAILABLE = "auth_secret_unavailable"


@dataclass(frozen=True, slots=True)
class PairingRequest:
    """pair request 阶段的公开字段；不包含 secret、token 或一次性 code。"""

    request_id: str
    client_name: str
    source_ip_hash: str
    machine_fingerprint_hash: str
    created_at: datetime
    expires_at: datetime
    status: str = "pending"

    @property
    def expired(self) -> bool:
        return self.expires_at <= self.created_at

    def is_active(self, now: datetime | None = None) -> bool:
        current = _coerce_now(now)
        return self.status == "pending" and current <= self.expires_at

    def to_public_dict(self) -> dict[str, object]:
        return {
            "request_id": self.request_id,
            "client_name": self.client_name,
            "source_ip_hash": self.source_ip_hash,
            "machine_fingerprint_hash": self.machine_fingerprint_hash,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "status": self.status,
        }


@dataclass(frozen=True, slots=True)
class PairingApproval:
    """pair approve / complete 阶段的运行态引用；不保存原始一次性 code。"""

    request_id: str
    client_id: str
    client_id_hash: str
    secret_ref: str
    scopes: tuple[str, ...]
    approved_at: datetime
    code_expires_at: datetime
    pairing_code_hash: str
    status: str = "approved"

    def __post_init__(self) -> None:
        object.__setattr__(self, "scopes", _as_tuple(self.scopes))

    def code_active(self, now: datetime | None = None) -> bool:
        return _coerce_now(now) <= self.code_expires_at

    def to_public_dict(self) -> dict[str, object]:
        return {
            "request_id": self.request_id,
            "client_id": self.client_id,
            "client_id_hash": self.client_id_hash,
            "secret_ref": "[REDACTED]",
            "scopes": list(self.scopes),
            "approved_at": self.approved_at.isoformat(),
            "code_expires_at": self.code_expires_at.isoformat(),
            "pairing_code_status": "redacted",
            "status": self.status,
        }


@dataclass(frozen=True, slots=True)
class QmtHmacHeaders:
    """Gateway 请求必须携带的四个 HMAC header。"""

    client_id: str
    timestamp: str
    nonce: str
    signature: str

    @classmethod
    def from_mapping(cls, headers: Mapping[str, object]) -> "QmtHmacHeaders | None":
        normalized = {str(key).lower(): str(value) for key, value in headers.items()}
        required = (
            QMT_HMAC_HEADER_CLIENT_ID,
            QMT_HMAC_HEADER_TIMESTAMP,
            QMT_HMAC_HEADER_NONCE,
            QMT_HMAC_HEADER_SIGNATURE,
        )
        if any(not normalized.get(key) for key in required):
            return None
        return cls(
            client_id=normalized[QMT_HMAC_HEADER_CLIENT_ID],
            timestamp=normalized[QMT_HMAC_HEADER_TIMESTAMP],
            nonce=normalized[QMT_HMAC_HEADER_NONCE],
            signature=normalized[QMT_HMAC_HEADER_SIGNATURE],
        )

    def to_dict(self) -> dict[str, str]:
        return {
            "client_id": self.client_id,
            "timestamp": self.timestamp,
            "nonce": self.nonce,
            "signature": self.signature,
        }


@dataclass(frozen=True, slots=True)
class QmtAuthConfig:
    """S05 鉴权配置合同；fixture secret 只能通过显式参数传入。"""

    auth_mode: str = DEFAULT_AUTH_MODE
    pairing_request_ttl_seconds: int = DEFAULT_PAIRING_REQUEST_TTL_SECONDS
    pairing_code_ttl_seconds: int = DEFAULT_PAIRING_CODE_TTL_SECONDS
    hmac_clock_skew_seconds: int = DEFAULT_HMAC_CLOCK_SKEW_SECONDS
    nonce_ttl_seconds: int = DEFAULT_NONCE_TTL_SECONDS
    approvals: Mapping[str, PairingApproval] = field(default_factory=dict)
    client_secrets: Mapping[str, str] = field(default_factory=dict)
    allow_no_auth_debug: bool = False
    allow_no_auth_fixture: bool = False
    allow_no_auth_temporary: bool = False

    def approval_for(self, client_id: str) -> PairingApproval | None:
        approval = self.approvals.get(client_id)
        if approval is not None:
            return approval
        client_hash = stable_qmt_auth_hash(client_id)
        for candidate in self.approvals.values():
            if candidate.client_id_hash == client_hash:
                return candidate
        return None


@dataclass(frozen=True, slots=True)
class QmtAuthResult:
    """鉴权结果只识别调用方和 scope，不授权交易或真实 QMT 调用。"""

    allowed: bool
    status: str
    blocked_reason: QmtAuthBlockedReason | None = None
    client_id_hash: str = ""
    scopes: tuple[str, ...] = ()
    required_scope: str = ""
    caller_identified: bool = False
    adapter_call_allowed: bool = False
    trade_authorized: bool = False
    simulation_authorized: bool = False
    live_authorized: bool = False
    account_authorized: bool = False
    cancel_authorized: bool = False
    counters: Mapping[str, int] = field(default_factory=lambda: collect_qmt_auth_safety_counters())

    @property
    def blocked(self) -> bool:
        return not self.allowed

    @property
    def reason_code(self) -> str:
        return self.blocked_reason.value if self.blocked_reason is not None else ""

    def to_dict(self) -> dict[str, object]:
        return {
            "allowed": self.allowed,
            "blocked": self.blocked,
            "status": self.status,
            "blocked_reason": self.reason_code,
            "client_id_hash": self.client_id_hash,
            "scopes": list(self.scopes),
            "required_scope": self.required_scope,
            "caller_identified": self.caller_identified,
            "adapter_call_allowed": self.adapter_call_allowed,
            "trade_authorized": self.trade_authorized,
            "simulation_authorized": self.simulation_authorized,
            "live_authorized": self.live_authorized,
            "account_authorized": self.account_authorized,
            "cancel_authorized": self.cancel_authorized,
            "counters": dict(self.counters),
        }


def create_pairing_request(
    *,
    client_name: str,
    source_context: Mapping[str, object],
    now: datetime | None = None,
    request_id: str | None = None,
    ttl_seconds: int = DEFAULT_PAIRING_REQUEST_TTL_SECONDS,
) -> PairingRequest:
    """创建 pairing request 合同对象，不生成或保存真实 secret。"""

    current = _coerce_now(now)
    source_ip_hash = str(source_context.get("source_ip_hash", ""))
    machine_hash = str(source_context.get("machine_fingerprint_hash", ""))
    resolved_request_id = request_id or stable_qmt_auth_hash(
        "|".join((client_name, source_ip_hash, machine_hash, current.isoformat()))
    )
    return PairingRequest(
        request_id=resolved_request_id,
        client_name=client_name,
        source_ip_hash=source_ip_hash,
        machine_fingerprint_hash=machine_hash,
        created_at=current,
        expires_at=_add_seconds(current, ttl_seconds),
    )


def list_pending_pairing_requests(
    registry: Sequence[PairingRequest] | Mapping[str, PairingRequest],
    *,
    now: datetime | None = None,
) -> tuple[dict[str, object], ...]:
    """列出 pending request 的公开摘要，不输出 code、token 或 secret。"""

    requests = registry.values() if isinstance(registry, Mapping) else registry
    return tuple(
        request.to_public_dict()
        for request in requests
        if request.is_active(now)
    )


def approve_pairing_request(
    request: PairingRequest,
    *,
    scopes: Sequence[str],
    now: datetime | None = None,
    client_id: str | None = None,
    secret_ref: str = "<runtime-secret-ref>",
    pairing_code: str = FIXTURE_PAIRING_CODE,
    code_ttl_seconds: int = DEFAULT_PAIRING_CODE_TTL_SECONDS,
) -> PairingApproval:
    """批准 pairing request，并只保存一次性 code 的摘要。"""

    current = _coerce_now(now)
    resolved_client_id = client_id or stable_qmt_auth_hash(
        f"{request.request_id}|{request.client_name}|client"
    )
    return PairingApproval(
        request_id=request.request_id,
        client_id=resolved_client_id,
        client_id_hash=stable_qmt_auth_hash(resolved_client_id),
        secret_ref=secret_ref,
        scopes=_as_tuple(scopes),
        approved_at=current,
        code_expires_at=_add_seconds(current, code_ttl_seconds),
        pairing_code_hash=stable_qmt_auth_hash(pairing_code),
    )


def complete_pairing(
    approval: PairingApproval,
    *,
    pairing_code: str,
    now: datetime | None = None,
) -> QmtAuthResult:
    """完成 pairing；成功也只返回 caller 识别结果，不返回真实 secret。"""

    if approval.status != "approved":
        return _blocked(
            QmtAuthBlockedReason.AUTH_CLIENT_NOT_APPROVED,
            client_id_hash=approval.client_id_hash,
        )
    if not approval.code_active(now):
        return _blocked(
            QmtAuthBlockedReason.AUTH_PAIRING_EXPIRED,
            client_id_hash=approval.client_id_hash,
        )
    if not hmac.compare_digest(
        approval.pairing_code_hash,
        stable_qmt_auth_hash(pairing_code),
    ):
        return _blocked(
            QmtAuthBlockedReason.AUTH_SIGNATURE_MISMATCH,
            client_id_hash=approval.client_id_hash,
        )
    return QmtAuthResult(
        allowed=True,
        status="paired",
        client_id_hash=approval.client_id_hash,
        scopes=approval.scopes,
        caller_identified=True,
    )


def validate_hmac_request(
    *,
    method: str,
    path: str,
    body: bytes | str,
    headers: Mapping[str, object],
    required_scope: str,
    config: QmtAuthConfig,
    now: datetime | None = None,
    used_nonce_store: MutableSet[str] | None = None,
) -> QmtAuthResult:
    """校验 HMAC header、timestamp、nonce、scope 和 signature。"""

    mode_result = validate_auth_mode(config, runtime_context="pairing_hmac")
    if mode_result.blocked:
        return mode_result

    parsed = QmtHmacHeaders.from_mapping(headers)
    if parsed is None:
        return _blocked(QmtAuthBlockedReason.AUTH_HEADER_MISSING, required_scope=required_scope)

    approval = config.approval_for(parsed.client_id)
    client_id_hash = stable_qmt_auth_hash(parsed.client_id)
    if approval is None or approval.status != "approved":
        return _blocked(
            QmtAuthBlockedReason.AUTH_CLIENT_NOT_APPROVED,
            client_id_hash=client_id_hash,
            required_scope=required_scope,
        )

    timestamp = _parse_epoch_seconds(parsed.timestamp)
    if timestamp is None:
        return _blocked(
            QmtAuthBlockedReason.AUTH_TIMESTAMP_SKEW,
            client_id_hash=approval.client_id_hash,
            required_scope=required_scope,
        )
    current = _coerce_now(now)
    if abs(int(current.timestamp()) - timestamp) > config.hmac_clock_skew_seconds:
        return _blocked(
            QmtAuthBlockedReason.AUTH_TIMESTAMP_SKEW,
            client_id_hash=approval.client_id_hash,
            required_scope=required_scope,
        )

    nonce_key = f"{approval.client_id_hash}:{parsed.nonce}"
    if used_nonce_store is not None:
        if nonce_key in used_nonce_store:
            return _blocked(
                QmtAuthBlockedReason.AUTH_NONCE_REPLAY,
                client_id_hash=approval.client_id_hash,
                required_scope=required_scope,
            )
        used_nonce_store.add(nonce_key)

    if required_scope not in approval.scopes:
        return _blocked(
            QmtAuthBlockedReason.AUTH_SCOPE_DENIED,
            client_id_hash=approval.client_id_hash,
            required_scope=required_scope,
        )

    secret = config.client_secrets.get(parsed.client_id)
    if not secret:
        return _blocked(
            QmtAuthBlockedReason.AUTH_SECRET_UNAVAILABLE,
            client_id_hash=approval.client_id_hash,
            required_scope=required_scope,
        )

    expected = build_qmt_hmac_signature(
        secret=secret,
        method=method,
        path=path,
        body=body,
        timestamp=str(timestamp),
        nonce=parsed.nonce,
    )
    if not hmac.compare_digest(parsed.signature, expected):
        return _blocked(
            QmtAuthBlockedReason.AUTH_SIGNATURE_MISMATCH,
            client_id_hash=approval.client_id_hash,
            required_scope=required_scope,
        )

    return QmtAuthResult(
        allowed=True,
        status="identified",
        client_id_hash=approval.client_id_hash,
        scopes=approval.scopes,
        required_scope=required_scope,
        caller_identified=True,
    )


def validate_auth_mode(
    config: QmtAuthConfig,
    *,
    runtime_context: str,
) -> QmtAuthResult:
    """校验 auth mode；no-auth 默认 fail closed。"""

    mode = config.auth_mode.strip().lower().replace("-", "_")
    if mode == DEFAULT_AUTH_MODE:
        return QmtAuthResult(allowed=True, status="auth_mode_allowed")
    if mode != NO_AUTH_MODE:
        return _blocked(QmtAuthBlockedReason.AUTH_NO_AUTH_NOT_ALLOWED)

    context = runtime_context.strip().lower()
    allowed = (
        (context == "local_debug" and config.allow_no_auth_debug)
        or (context == "fixture_test" and config.allow_no_auth_fixture)
        or (context == "explicit_temporary" and config.allow_no_auth_temporary)
    )
    if not allowed:
        return _blocked(QmtAuthBlockedReason.AUTH_NO_AUTH_NOT_ALLOWED)
    return QmtAuthResult(allowed=True, status="no_auth_temporary_allowed")


def build_qmt_hmac_signature(
    *,
    secret: str,
    method: str,
    path: str,
    body: bytes | str,
    timestamp: str,
    nonce: str,
) -> str:
    """构造 fixture HMAC 签名；调用方必须显式传入 fixture secret。"""

    body_hash = hashlib.sha256(_as_body_bytes(body)).hexdigest()
    payload = "\n".join((method.upper(), path, body_hash, timestamp, nonce))
    return hmac.new(secret.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256).hexdigest()


def collect_qmt_auth_safety_counters(
    counters: Mapping[str, int] | None = None,
) -> dict[str, int]:
    """归一化 S05 禁止操作计数；默认全部为 0。"""

    normalized = {key: 0 for key in QMT_AUTH_FORBIDDEN_COUNTER_FIELDS}
    if counters is None:
        return normalized
    for key, value in counters.items():
        normalized[str(key)] = int(value)
    return normalized


def stable_qmt_auth_hash(value: str) -> str:
    """生成审计用稳定摘要，不代表 secret。"""

    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _blocked(
    reason: QmtAuthBlockedReason,
    *,
    client_id_hash: str = "",
    required_scope: str = "",
) -> QmtAuthResult:
    return QmtAuthResult(
        allowed=False,
        status="blocked",
        blocked_reason=reason,
        client_id_hash=client_id_hash,
        required_scope=required_scope,
    )


def _parse_epoch_seconds(value: str) -> int | None:
    try:
        return int(value)
    except ValueError:
        return None


def _add_seconds(value: datetime, seconds: int) -> datetime:
    return datetime.fromtimestamp(int(value.timestamp()) + int(seconds), tz=timezone.utc)


def _coerce_now(value: datetime | None) -> datetime:
    current = value or datetime.now(timezone.utc)
    if current.tzinfo is None:
        return current.replace(tzinfo=timezone.utc)
    return current.astimezone(timezone.utc)


def _as_body_bytes(body: bytes | str) -> bytes:
    return body if isinstance(body, bytes) else body.encode("utf-8")


def _as_tuple(value: Sequence[str]) -> tuple[str, ...]:
    return tuple(str(item) for item in value)
