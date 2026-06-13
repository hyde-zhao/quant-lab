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
from ipaddress import ip_address, ip_network
from typing import Callable, Mapping, MutableSet, Sequence


DEFAULT_AUTH_MODE = "pairing_hmac"
NO_AUTH_MODE = "no_auth"
FIXTURE_PAIRING_CODE = "fixture-only-pairing-code"

DEFAULT_PAIRING_REQUEST_TTL_SECONDS = 600
DEFAULT_PAIRING_CODE_TTL_SECONDS = 300
DEFAULT_HMAC_CLOCK_SKEW_SECONDS = 300
DEFAULT_NONCE_TTL_SECONDS = 600

CR020_QMT_AUTH_SCHEMA_VERSION = "cr020-s04-hmac-pairing-allowlist-scope-v1"
QMT_QUERY_POSITIONS_ENDPOINT_ID = "query_positions"
QMT_QUERY_POSITIONS_REQUIRED_SCOPE = "qmt:positions:read"

QMT_HMAC_HEADER_CLIENT_ID = "x-qmt-client-id"
QMT_HMAC_HEADER_TIMESTAMP = "x-qmt-timestamp"
QMT_HMAC_HEADER_NONCE = "x-qmt-nonce"
QMT_HMAC_HEADER_SIGNATURE = "x-qmt-signature"

QMT_AUTH_FORBIDDEN_COUNTER_FIELDS: tuple[str, ...] = (
    "adapter_call",
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
    "gateway_start",
    "service_start",
    "service_start_count",
    "service_bind",
    "port_bind_count",
    "transport_send",
    "network_call",
    "socket_open",
    "http_client_call",
    "gateway_socket_open",
    "raw_fallback",
    "redaction_fallback_to_raw",
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
    AUTH_SOURCE_MISSING = "auth_source_missing"
    AUTH_ALLOWLIST_MISSING = "auth_allowlist_missing"
    AUTH_ALLOWLIST_MISMATCH = "auth_allowlist_mismatch"
    AUTH_PUBLIC_SOURCE_FORBIDDEN = "auth_public_source_forbidden"
    AUTH_REQUIRED_SCOPE_UNAVAILABLE = "auth_required_scope_unavailable"
    AUTH_REDACTION_FAILED = "auth_redaction_failed"


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


@dataclass(frozen=True, slots=True)
class QmtRequestSourceContext:
    """Gateway 传入的请求来源上下文；公开输出只包含 hash/ref。"""

    source_ip: str = ""
    source_ref: str = ""
    source_ip_hash: str = ""
    machine_fingerprint_hash: str = ""
    provided_by: str = "gateway"
    is_public_source: bool = False
    counters: Mapping[str, int] = field(
        default_factory=lambda: collect_qmt_auth_safety_counters()
    )

    def __post_init__(self) -> None:
        resolved_hash = self.source_ip_hash
        if self.source_ip and not resolved_hash:
            resolved_hash = stable_qmt_auth_hash(self.source_ip)
        object.__setattr__(self, "source_ip_hash", resolved_hash)
        if not self.source_ref and resolved_hash:
            object.__setattr__(self, "source_ref", f"source:{resolved_hash[:12]}")
        if self.source_ip and not self.is_public_source:
            object.__setattr__(self, "is_public_source", _is_public_ip(self.source_ip))

    @property
    def present(self) -> bool:
        return bool(self.source_ip or self.source_ref or self.source_ip_hash)

    def to_dict(self) -> dict[str, object]:
        return {
            "source_ref": self.source_ref,
            "source_ip_hash": self.source_ip_hash,
            "machine_fingerprint_hash": self.machine_fingerprint_hash,
            "provided_by": self.provided_by,
            "is_public_source": self.is_public_source,
            "counters": dict(self.counters),
        }


@dataclass(frozen=True, slots=True)
class QmtAllowlistDecision:
    """来源白名单判定；未匹配时 fail-closed。"""

    allowed: bool
    status: str
    blocked_reason: QmtAuthBlockedReason | None = None
    source_ref: str = ""
    source_ip_hash: str = ""
    matched_source_ref: str = ""
    counters: Mapping[str, int] = field(
        default_factory=lambda: collect_qmt_auth_safety_counters()
    )

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
            "source_ref": self.source_ref,
            "source_ip_hash": self.source_ip_hash,
            "matched_source_ref": self.matched_source_ref,
            "counters": dict(self.counters),
        }


@dataclass(frozen=True, slots=True)
class QmtScopeDecision:
    """Endpoint required scope 与 pairing scopes 的 exact 判定。"""

    allowed: bool
    status: str
    required_scope: str
    granted_scopes: tuple[str, ...] = ()
    endpoint_id: str = ""
    blocked_reason: QmtAuthBlockedReason | None = None
    counters: Mapping[str, int] = field(
        default_factory=lambda: collect_qmt_auth_safety_counters()
    )

    def __post_init__(self) -> None:
        object.__setattr__(self, "granted_scopes", _as_tuple(self.granted_scopes))

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
            "endpoint_id": self.endpoint_id,
            "required_scope": self.required_scope,
            "granted_scopes": list(self.granted_scopes),
            "blocked_reason": self.reason_code,
            "counters": dict(self.counters),
        }


@dataclass(frozen=True, slots=True)
class QmtNonceDecision:
    """进程内 nonce 防重放判定；不保存或输出 raw nonce。"""

    allowed: bool
    status: str
    client_id_hash: str
    nonce_ref: str
    blocked_reason: QmtAuthBlockedReason | None = None
    expires_at: datetime | None = None
    counters: Mapping[str, int] = field(
        default_factory=lambda: collect_qmt_auth_safety_counters()
    )

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
            "client_id_hash": self.client_id_hash,
            "nonce_ref": self.nonce_ref,
            "blocked_reason": self.reason_code,
            "expires_at": self.expires_at.isoformat() if self.expires_at else "",
            "counters": dict(self.counters),
        }


@dataclass(frozen=True, slots=True)
class QmtHmacHeaderBuildResult:
    """S03 可消费的 HMAC headers；diagnostics 只输出 ref/hash。"""

    accepted: bool
    status: str
    headers: Mapping[str, str] = field(default_factory=dict)
    required_scope: str = ""
    client_id_hash: str = ""
    nonce_ref: str = ""
    signature_ref: str = ""
    blocked_reason: QmtAuthBlockedReason | None = None
    counters: Mapping[str, int] = field(
        default_factory=lambda: collect_qmt_auth_safety_counters()
    )

    @property
    def blocked(self) -> bool:
        return not self.accepted

    @property
    def reason_code(self) -> str:
        return self.blocked_reason.value if self.blocked_reason is not None else ""

    @property
    def redacted_headers(self) -> dict[str, str]:
        return {
            "X-QMT-Client-Id": self.client_id_hash,
            "X-QMT-Timestamp": "[REDACTED]",
            "X-QMT-Nonce": self.nonce_ref,
            "X-QMT-Signature": self.signature_ref,
        }

    def to_dict(self) -> dict[str, object]:
        return {
            "accepted": self.accepted,
            "blocked": self.blocked,
            "status": self.status,
            "blocked_reason": self.reason_code,
            "required_scope": self.required_scope,
            "client_id_hash": self.client_id_hash,
            "nonce_ref": self.nonce_ref,
            "signature_ref": self.signature_ref,
            "redacted_headers": self.redacted_headers,
            "counters": dict(self.counters),
        }


@dataclass(frozen=True, slots=True)
class QmtAuthAdmissionDecision:
    """Gateway dispatcher 前置的统一鉴权准入结果。"""

    accepted: bool
    status: str
    blocked_reason: QmtAuthBlockedReason | None = None
    allowlist_decision: QmtAllowlistDecision | None = None
    hmac_result: QmtAuthResult | None = None
    scope_decision: QmtScopeDecision | None = None
    redaction_status: str = "not_checked"
    client_id_hash: str = ""
    endpoint_id: str = ""
    required_scope: str = ""
    adapter_call_allowed: bool = False
    qmt_api_call_allowed: bool = False
    trade_authorized: bool = False
    account_write_authorized: bool = False
    simulation_authorized: bool = False
    live_authorized: bool = False
    counters: Mapping[str, int] = field(
        default_factory=lambda: collect_qmt_auth_safety_counters()
    )

    @property
    def blocked(self) -> bool:
        return not self.accepted

    @property
    def reason_code(self) -> str:
        return self.blocked_reason.value if self.blocked_reason is not None else ""

    def to_dict(self) -> dict[str, object]:
        return {
            "accepted": self.accepted,
            "blocked": self.blocked,
            "status": self.status,
            "blocked_reason": self.reason_code,
            "client_id_hash": self.client_id_hash,
            "endpoint_id": self.endpoint_id,
            "required_scope": self.required_scope,
            "redaction_status": self.redaction_status,
            "adapter_call_allowed": self.adapter_call_allowed,
            "qmt_api_call_allowed": self.qmt_api_call_allowed,
            "trade_authorized": self.trade_authorized,
            "account_write_authorized": self.account_write_authorized,
            "simulation_authorized": self.simulation_authorized,
            "live_authorized": self.live_authorized,
            "allowlist_decision": (
                self.allowlist_decision.to_dict()
                if self.allowlist_decision is not None
                else None
            ),
            "hmac_result": self.hmac_result.to_dict() if self.hmac_result else None,
            "scope_decision": (
                self.scope_decision.to_dict() if self.scope_decision is not None else None
            ),
            "counters": dict(self.counters),
        }


class QmtNonceReplayStore:
    """单进程 TTL nonce store；跨进程持久化由后续 CR 处理。"""

    def __init__(
        self,
        *,
        ttl_seconds: int = DEFAULT_NONCE_TTL_SECONDS,
        max_entries: int = 4096,
    ) -> None:
        self.ttl_seconds = int(ttl_seconds)
        self.max_entries = int(max_entries)
        self._expires_by_key: dict[str, datetime] = {}

    def check_and_remember(
        self,
        *,
        client_id_hash: str,
        nonce: str,
        now: datetime | None = None,
    ) -> QmtNonceDecision:
        current = _coerce_now(now)
        self._purge_expired(current)
        key = self._key(client_id_hash, nonce)
        nonce_ref = f"nonce:{stable_qmt_auth_hash(nonce)[:12]}"
        existing_expiry = self._expires_by_key.get(key)
        if existing_expiry is not None and existing_expiry > current:
            return QmtNonceDecision(
                allowed=False,
                status="blocked",
                client_id_hash=client_id_hash,
                nonce_ref=nonce_ref,
                blocked_reason=QmtAuthBlockedReason.AUTH_NONCE_REPLAY,
                expires_at=existing_expiry,
            )
        expires_at = _add_seconds(current, self.ttl_seconds)
        self._expires_by_key[key] = expires_at
        self._trim(current)
        return QmtNonceDecision(
            allowed=True,
            status="remembered",
            client_id_hash=client_id_hash,
            nonce_ref=nonce_ref,
            expires_at=expires_at,
        )

    @property
    def size(self) -> int:
        return len(self._expires_by_key)

    def _purge_expired(self, current: datetime) -> None:
        expired_keys = [
            key for key, expires_at in self._expires_by_key.items() if expires_at <= current
        ]
        for key in expired_keys:
            self._expires_by_key.pop(key, None)

    def _trim(self, current: datetime) -> None:
        self._purge_expired(current)
        overflow = len(self._expires_by_key) - max(self.max_entries, 1)
        if overflow <= 0:
            return
        for key, _expires_at in sorted(
            self._expires_by_key.items(),
            key=lambda item: item[1],
        )[:overflow]:
            self._expires_by_key.pop(key, None)

    @staticmethod
    def _key(client_id_hash: str, nonce: str) -> str:
        return f"{client_id_hash}:{stable_qmt_auth_hash(nonce)}"


class QmtHmacHeaderProvider:
    """S03 可注入 provider；只使用显式 fixture/runtime 参数。"""

    def __init__(
        self,
        *,
        client_id: str,
        secret: str,
        scopes: Sequence[str],
        clock: Callable[[], datetime] | None = None,
        nonce_provider: Callable[[], str] | None = None,
    ) -> None:
        self.client_id = client_id
        self._secret = secret
        self.scopes = _as_tuple(scopes)
        self._clock = clock
        self._nonce_provider = nonce_provider

    def build_headers(self, request: object) -> Mapping[str, str]:
        """返回传输层 headers；失败时返回空 mapping，调用方应 fail-closed。"""

        result = self.build_result(request)
        return dict(result.headers) if result.accepted else {}

    def build_result(self, request: object) -> QmtHmacHeaderBuildResult:
        required_scope = str(_request_value(request, "required_scope", ""))
        method = str(_request_value(request, "method", "POST"))
        path = str(_request_value(request, "path", ""))
        body = _request_value(request, "body", b"")
        if not self.client_id:
            return _blocked_header_result(
                QmtAuthBlockedReason.AUTH_CLIENT_NOT_APPROVED,
                required_scope=required_scope,
            )
        if not self._secret:
            return _blocked_header_result(
                QmtAuthBlockedReason.AUTH_SECRET_UNAVAILABLE,
                required_scope=required_scope,
                client_id_hash=stable_qmt_auth_hash(self.client_id),
            )
        if required_scope and required_scope not in self.scopes:
            return _blocked_header_result(
                QmtAuthBlockedReason.AUTH_SCOPE_DENIED,
                required_scope=required_scope,
                client_id_hash=stable_qmt_auth_hash(self.client_id),
            )
        current = _coerce_now(self._clock() if self._clock is not None else None)
        timestamp = str(int(current.timestamp()))
        nonce = (
            self._nonce_provider()
            if self._nonce_provider is not None
            else stable_qmt_auth_hash(f"{self.client_id}|{timestamp}")[:32]
        )
        return build_qmt_hmac_request_headers(
            client_id=self.client_id,
            secret=self._secret,
            method=method,
            path=path,
            body=body if isinstance(body, (bytes, str)) else repr(body),
            required_scope=required_scope,
            timestamp=timestamp,
            nonce=nonce,
            granted_scopes=self.scopes,
        )

    def diagnostics(self) -> dict[str, object]:
        return {
            "client_id_hash": stable_qmt_auth_hash(self.client_id) if self.client_id else "",
            "scopes": list(self.scopes),
            "secret_ref": "[REDACTED]",
            "schema_version": CR020_QMT_AUTH_SCHEMA_VERSION,
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


def build_qmt_request_source_context(
    metadata: Mapping[str, object] | None = None,
    *,
    source_ip: str | None = None,
    source_ref: str | None = None,
    machine_fingerprint_hash: str | None = None,
    provided_by: str = "gateway",
) -> QmtRequestSourceContext:
    """从 gateway 显式 metadata 构造来源上下文；不做网络探测。"""

    raw = dict(metadata or {})
    resolved_ip = str(
        source_ip
        or raw.get("source_ip")
        or raw.get("remote_addr")
        or raw.get("client_host")
        or ""
    )
    resolved_ref = str(source_ref or raw.get("source_ref") or raw.get("client_ref") or "")
    source_hash = str(raw.get("source_ip_hash") or "")
    machine_hash = str(
        machine_fingerprint_hash
        or raw.get("machine_fingerprint_hash")
        or raw.get("machine_hash")
        or ""
    )
    return QmtRequestSourceContext(
        source_ip=resolved_ip,
        source_ref=resolved_ref,
        source_ip_hash=source_hash,
        machine_fingerprint_hash=machine_hash,
        provided_by=provided_by,
    )


def validate_qmt_allowlist(
    source_context: QmtRequestSourceContext | Mapping[str, object] | None,
    allowlist: object,
) -> QmtAllowlistDecision:
    """按 S01 allowlist exact 合同校验来源，缺失或公网来源均阻断。"""

    context = _coerce_source_context(source_context)
    if not context.present:
        return _allowlist_blocked(
            QmtAuthBlockedReason.AUTH_SOURCE_MISSING,
            source_ref=context.source_ref,
            source_ip_hash=context.source_ip_hash,
        )
    if context.is_public_source:
        return _allowlist_blocked(
            QmtAuthBlockedReason.AUTH_PUBLIC_SOURCE_FORBIDDEN,
            source_ref=context.source_ref,
            source_ip_hash=context.source_ip_hash,
        )

    sources, required = _extract_allowlist(allowlist)
    if required and not sources:
        return _allowlist_blocked(
            QmtAuthBlockedReason.AUTH_ALLOWLIST_MISSING,
            source_ref=context.source_ref,
            source_ip_hash=context.source_ip_hash,
        )
    if not required:
        return _allowlist_blocked(
            QmtAuthBlockedReason.AUTH_ALLOWLIST_MISSING,
            source_ref=context.source_ref,
            source_ip_hash=context.source_ip_hash,
        )

    source_address = _parse_ip_address(context.source_ip)
    for source in sources:
        source_text = str(source)
        network = _parse_ip_network(source_text)
        if network is not None:
            if network.is_global:
                return _allowlist_blocked(
                    QmtAuthBlockedReason.AUTH_PUBLIC_SOURCE_FORBIDDEN,
                    source_ref=context.source_ref,
                    source_ip_hash=context.source_ip_hash,
                    matched_source_ref=source_text,
                )
            if source_address is not None and source_address in network:
                return QmtAllowlistDecision(
                    allowed=True,
                    status="allowlist_allowed",
                    source_ref=context.source_ref,
                    source_ip_hash=context.source_ip_hash,
                    matched_source_ref=source_text,
                )
            continue
        if context.source_ref and source_text == context.source_ref:
            return QmtAllowlistDecision(
                allowed=True,
                status="allowlist_allowed",
                source_ref=context.source_ref,
                source_ip_hash=context.source_ip_hash,
                matched_source_ref=source_text,
            )

    return _allowlist_blocked(
        QmtAuthBlockedReason.AUTH_ALLOWLIST_MISMATCH,
        source_ref=context.source_ref,
        source_ip_hash=context.source_ip_hash,
    )


def resolve_required_scope(
    *,
    endpoint_id: str = QMT_QUERY_POSITIONS_ENDPOINT_ID,
    method: str = "",
    path: str = "",
    endpoint_matrix: Sequence[object] | None = None,
) -> QmtScopeDecision:
    """按 endpoint id 或 method/path 解析 required_scope。"""

    spec = _resolve_endpoint_scope_spec(
        endpoint_id=endpoint_id,
        method=method,
        path=path,
        endpoint_matrix=endpoint_matrix,
    )
    if spec is None:
        return QmtScopeDecision(
            allowed=False,
            status="blocked",
            required_scope="",
            endpoint_id=endpoint_id,
            blocked_reason=QmtAuthBlockedReason.AUTH_REQUIRED_SCOPE_UNAVAILABLE,
        )
    return QmtScopeDecision(
        allowed=True,
        status="scope_resolved",
        required_scope=str(_spec_value(spec, "required_scope")),
        endpoint_id=str(_spec_value(spec, "endpoint_id")),
    )


def validate_qmt_scope(
    *,
    required_scope: str,
    granted_scopes: Sequence[str],
    endpoint_id: str = "",
) -> QmtScopeDecision:
    """校验 pairing approval 是否精确包含 endpoint required scope。"""

    granted = _as_tuple(granted_scopes)
    if not required_scope:
        return QmtScopeDecision(
            allowed=False,
            status="blocked",
            required_scope=required_scope,
            granted_scopes=granted,
            endpoint_id=endpoint_id,
            blocked_reason=QmtAuthBlockedReason.AUTH_REQUIRED_SCOPE_UNAVAILABLE,
        )
    if required_scope not in granted:
        return QmtScopeDecision(
            allowed=False,
            status="blocked",
            required_scope=required_scope,
            granted_scopes=granted,
            endpoint_id=endpoint_id,
            blocked_reason=QmtAuthBlockedReason.AUTH_SCOPE_DENIED,
        )
    return QmtScopeDecision(
        allowed=True,
        status="scope_allowed",
        required_scope=required_scope,
        granted_scopes=granted,
        endpoint_id=endpoint_id,
    )


def build_qmt_hmac_request_headers(
    *,
    client_id: str,
    secret: str,
    method: str,
    path: str,
    body: bytes | str,
    required_scope: str,
    timestamp: str,
    nonce: str,
    granted_scopes: Sequence[str] = (),
) -> QmtHmacHeaderBuildResult:
    """构造 transport headers，并把 diagnostics 限制为 hash/ref。"""

    client_id_hash = stable_qmt_auth_hash(client_id) if client_id else ""
    if not client_id:
        return _blocked_header_result(
            QmtAuthBlockedReason.AUTH_CLIENT_NOT_APPROVED,
            required_scope=required_scope,
        )
    if not secret:
        return _blocked_header_result(
            QmtAuthBlockedReason.AUTH_SECRET_UNAVAILABLE,
            required_scope=required_scope,
            client_id_hash=client_id_hash,
        )
    if required_scope and granted_scopes and required_scope not in granted_scopes:
        return _blocked_header_result(
            QmtAuthBlockedReason.AUTH_SCOPE_DENIED,
            required_scope=required_scope,
            client_id_hash=client_id_hash,
        )
    signature = build_qmt_hmac_signature(
        secret=secret,
        method=method,
        path=path,
        body=body,
        timestamp=timestamp,
        nonce=nonce,
    )
    headers = {
        "X-QMT-Client-Id": client_id,
        "X-QMT-Timestamp": str(timestamp),
        "X-QMT-Nonce": nonce,
        "X-QMT-Signature": signature,
    }
    return QmtHmacHeaderBuildResult(
        accepted=True,
        status="headers_built",
        headers=headers,
        required_scope=required_scope,
        client_id_hash=client_id_hash,
        nonce_ref=f"nonce:{stable_qmt_auth_hash(nonce)[:12]}",
        signature_ref=f"sigref:{stable_qmt_auth_hash(signature)[:12]}",
    )


def validate_no_auth_runtime_mode(
    config: QmtAuthConfig,
    *,
    runtime_context: str,
) -> QmtAuthResult:
    """CR020 no-auth 运行态门控；默认仍 fail-closed。"""

    return validate_auth_mode(config, runtime_context=runtime_context)


def evaluate_qmt_auth_admission(
    *,
    request_source: QmtRequestSourceContext | Mapping[str, object] | None,
    method: str,
    path: str,
    body: bytes | str,
    headers: Mapping[str, object],
    config: QmtAuthConfig,
    allowlist: object,
    endpoint_id: str = QMT_QUERY_POSITIONS_ENDPOINT_ID,
    required_scope: str = "",
    endpoint_matrix: Sequence[object] | None = None,
    now: datetime | None = None,
    nonce_store: MutableSet[str] | QmtNonceReplayStore | None = None,
    redaction_decision: object | None = None,
) -> QmtAuthAdmissionDecision:
    """统一执行 allowlist -> HMAC/scope/nonce -> redaction gate。"""

    source_context = _coerce_source_context(request_source)
    allowlist_decision = validate_qmt_allowlist(source_context, allowlist)
    if allowlist_decision.blocked:
        return _admission_blocked(
            allowlist_decision.blocked_reason
            or QmtAuthBlockedReason.AUTH_ALLOWLIST_MISMATCH,
            allowlist_decision=allowlist_decision,
            endpoint_id=endpoint_id,
            required_scope=required_scope,
        )

    scope_seed = (
        QmtScopeDecision(
            allowed=True,
            status="scope_resolved",
            required_scope=required_scope,
            endpoint_id=endpoint_id,
        )
        if required_scope
        else resolve_required_scope(
            endpoint_id=endpoint_id,
            method=method,
            path=path,
            endpoint_matrix=endpoint_matrix,
        )
    )
    if scope_seed.blocked:
        return _admission_blocked(
            scope_seed.blocked_reason
            or QmtAuthBlockedReason.AUTH_REQUIRED_SCOPE_UNAVAILABLE,
            allowlist_decision=allowlist_decision,
            scope_decision=scope_seed,
            endpoint_id=endpoint_id,
            required_scope=scope_seed.required_scope,
        )

    hmac_result = validate_hmac_request(
        method=method,
        path=path,
        body=body,
        headers=headers,
        required_scope=scope_seed.required_scope,
        config=config,
        now=now,
        used_nonce_store=nonce_store,
    )
    scope_decision = validate_qmt_scope(
        required_scope=scope_seed.required_scope,
        granted_scopes=hmac_result.scopes,
        endpoint_id=scope_seed.endpoint_id or endpoint_id,
    )
    if hmac_result.blocked:
        return _admission_blocked(
            hmac_result.blocked_reason or QmtAuthBlockedReason.AUTH_SIGNATURE_MISMATCH,
            allowlist_decision=allowlist_decision,
            hmac_result=hmac_result,
            scope_decision=scope_decision,
            endpoint_id=scope_seed.endpoint_id or endpoint_id,
            required_scope=scope_seed.required_scope,
            client_id_hash=hmac_result.client_id_hash,
        )
    if scope_decision.blocked:
        return _admission_blocked(
            scope_decision.blocked_reason or QmtAuthBlockedReason.AUTH_SCOPE_DENIED,
            allowlist_decision=allowlist_decision,
            hmac_result=hmac_result,
            scope_decision=scope_decision,
            endpoint_id=scope_seed.endpoint_id or endpoint_id,
            required_scope=scope_seed.required_scope,
            client_id_hash=hmac_result.client_id_hash,
        )

    redaction_status = _redaction_status(redaction_decision)
    if redaction_status == "failed":
        return _admission_blocked(
            QmtAuthBlockedReason.AUTH_REDACTION_FAILED,
            allowlist_decision=allowlist_decision,
            hmac_result=hmac_result,
            scope_decision=scope_decision,
            endpoint_id=scope_seed.endpoint_id or endpoint_id,
            required_scope=scope_seed.required_scope,
            client_id_hash=hmac_result.client_id_hash,
            redaction_status=redaction_status,
        )

    return QmtAuthAdmissionDecision(
        accepted=True,
        status="accepted_for_next_gate",
        allowlist_decision=allowlist_decision,
        hmac_result=hmac_result,
        scope_decision=scope_decision,
        redaction_status=redaction_status,
        client_id_hash=hmac_result.client_id_hash,
        endpoint_id=scope_seed.endpoint_id or endpoint_id,
        required_scope=scope_seed.required_scope,
        adapter_call_allowed=False,
        qmt_api_call_allowed=False,
        trade_authorized=False,
        account_write_authorized=False,
        simulation_authorized=False,
        live_authorized=False,
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
    used_nonce_store: MutableSet[str] | QmtNonceReplayStore | None = None,
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

    nonce_decision = _check_and_remember_nonce(
        used_nonce_store,
        client_id_hash=approval.client_id_hash,
        nonce=parsed.nonce,
        now=current,
    )
    if nonce_decision is not None and nonce_decision.blocked:
        return _blocked(
            QmtAuthBlockedReason.AUTH_NONCE_REPLAY,
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


def _coerce_source_context(
    source_context: QmtRequestSourceContext | Mapping[str, object] | None,
) -> QmtRequestSourceContext:
    if isinstance(source_context, QmtRequestSourceContext):
        return source_context
    if isinstance(source_context, Mapping):
        return build_qmt_request_source_context(source_context)
    return QmtRequestSourceContext()


def _request_value(request: object, key: str, default: object = "") -> object:
    if isinstance(request, Mapping):
        return request.get(key, default)
    return getattr(request, key, default)


def _extract_allowlist(allowlist: object) -> tuple[tuple[str, ...], bool]:
    if hasattr(allowlist, "sources"):
        sources = getattr(allowlist, "sources")
        required = bool(getattr(allowlist, "required", True))
        return _as_tuple(sources), required
    if isinstance(allowlist, Mapping):
        sources = allowlist.get("sources", allowlist.get("allowlist_sources", ()))
        required = bool(allowlist.get("required", allowlist.get("allowlist_required", True)))
        return _as_tuple(sources), required
    if isinstance(allowlist, Sequence) and not isinstance(allowlist, (bytes, bytearray, str)):
        return _as_tuple(allowlist), True
    return (), True


def _allowlist_blocked(
    reason: QmtAuthBlockedReason,
    *,
    source_ref: str = "",
    source_ip_hash: str = "",
    matched_source_ref: str = "",
) -> QmtAllowlistDecision:
    return QmtAllowlistDecision(
        allowed=False,
        status="blocked",
        blocked_reason=reason,
        source_ref=source_ref,
        source_ip_hash=source_ip_hash,
        matched_source_ref=matched_source_ref,
    )


def _admission_blocked(
    reason: QmtAuthBlockedReason,
    *,
    allowlist_decision: QmtAllowlistDecision | None = None,
    hmac_result: QmtAuthResult | None = None,
    scope_decision: QmtScopeDecision | None = None,
    endpoint_id: str = "",
    required_scope: str = "",
    client_id_hash: str = "",
    redaction_status: str = "not_checked",
) -> QmtAuthAdmissionDecision:
    return QmtAuthAdmissionDecision(
        accepted=False,
        status="blocked",
        blocked_reason=reason,
        allowlist_decision=allowlist_decision,
        hmac_result=hmac_result,
        scope_decision=scope_decision,
        redaction_status=redaction_status,
        client_id_hash=client_id_hash,
        endpoint_id=endpoint_id,
        required_scope=required_scope,
        adapter_call_allowed=False,
        qmt_api_call_allowed=False,
        trade_authorized=False,
        account_write_authorized=False,
        simulation_authorized=False,
        live_authorized=False,
    )


def _blocked_header_result(
    reason: QmtAuthBlockedReason,
    *,
    required_scope: str = "",
    client_id_hash: str = "",
) -> QmtHmacHeaderBuildResult:
    return QmtHmacHeaderBuildResult(
        accepted=False,
        status="blocked",
        required_scope=required_scope,
        client_id_hash=client_id_hash,
        blocked_reason=reason,
    )


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


def _check_and_remember_nonce(
    used_nonce_store: MutableSet[str] | QmtNonceReplayStore | None,
    *,
    client_id_hash: str,
    nonce: str,
    now: datetime,
) -> QmtNonceDecision | None:
    if used_nonce_store is None:
        return None
    if isinstance(used_nonce_store, QmtNonceReplayStore):
        return used_nonce_store.check_and_remember(
            client_id_hash=client_id_hash,
            nonce=nonce,
            now=now,
        )
    nonce_key = f"{client_id_hash}:{stable_qmt_auth_hash(nonce)}"
    nonce_ref = f"nonce:{stable_qmt_auth_hash(nonce)[:12]}"
    if nonce_key in used_nonce_store:
        return QmtNonceDecision(
            allowed=False,
            status="blocked",
            client_id_hash=client_id_hash,
            nonce_ref=nonce_ref,
            blocked_reason=QmtAuthBlockedReason.AUTH_NONCE_REPLAY,
        )
    used_nonce_store.add(nonce_key)
    return QmtNonceDecision(
        allowed=True,
        status="remembered",
        client_id_hash=client_id_hash,
        nonce_ref=nonce_ref,
    )


def _resolve_endpoint_scope_spec(
    *,
    endpoint_id: str,
    method: str,
    path: str,
    endpoint_matrix: Sequence[object] | None,
) -> object | None:
    specs = endpoint_matrix
    if specs is None:
        try:
            from trading.qmt_endpoint_matrix import iter_endpoint_specs
        except ImportError:
            specs = ()
        else:
            specs = iter_endpoint_specs()
    normalized_method = method.upper() if method else ""
    for spec in specs or ():
        spec_endpoint_id = str(_spec_value(spec, "endpoint_id"))
        if endpoint_id and spec_endpoint_id == endpoint_id:
            return spec
        if (
            normalized_method
            and path
            and str(_spec_value(spec, "method")).upper() == normalized_method
            and str(_spec_value(spec, "path")) == path
        ):
            return spec
    return None


def _spec_value(spec: object, field_name: str) -> object:
    if isinstance(spec, Mapping):
        return spec.get(field_name, "")
    return getattr(spec, field_name, "")


def _redaction_status(redaction_decision: object | None) -> str:
    if redaction_decision is None:
        return "not_checked"
    if bool(getattr(redaction_decision, "blocked", False)):
        return "failed"
    accepted = getattr(redaction_decision, "accepted", None)
    if accepted is False:
        return "failed"
    status = str(getattr(redaction_decision, "redaction_status", "") or "")
    if status.lower() in {"failed", "blocked", "redaction_failed"}:
        return "failed"
    if status:
        return status
    return "pass"


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


def _as_tuple(value: object) -> tuple[str, ...]:
    if isinstance(value, str):
        return (value,)
    if isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray, str)):
        return tuple(str(item) for item in value)
    if value is None:
        return ()
    return (str(value),)


def _parse_ip_address(value: str) -> object | None:
    if not value:
        return None
    try:
        return ip_address(value)
    except ValueError:
        return None


def _parse_ip_network(value: str) -> object | None:
    try:
        return ip_network(value, strict=False)
    except ValueError:
        return None


def _is_public_ip(value: str) -> bool:
    address = _parse_ip_address(value)
    return bool(address is not None and getattr(address, "is_global", False))
