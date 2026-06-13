"""CR020 QMT login / session ready gate 离线合同。

本模块只处理显式传入的 fixture / mapping 和注入式 adapter protocol。
它不读取 `.env`，不导入 XtQuant / MiniQMT / QMT SDK，也不执行真实登录或查询。
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from enum import Enum
from typing import Mapping, Protocol, Sequence

from trading.qmt_redaction import (
    REDACTED_VALUE,
    redact_qmt_mapping,
    scan_for_qmt_sensitive_leaks,
)


QMT_SESSION_SCHEMA_VERSION = "cr020-s02-qmt-session-v1"
DEFAULT_QMT_SESSION_READY_TIMEOUT_SECONDS = 30
DEFAULT_QMT_SESSION_TTL_SECONDS = 3600
DEFAULT_QMT_CREDENTIAL_REQUIRED_KEYS: tuple[str, ...] = (
    "QMT_LOGIN_ACCOUNT",
    "QMT_LOGIN_PASSWORD",
    "QMT_ACCOUNT_REF",
)

QMT_SESSION_REQUIRED_ZERO_COUNTERS: tuple[str, ...] = (
    "credential_read",
    "qmt_login_call",
    "qmt_api_call",
    "xtquant_import",
    "query_positions_adapter_call",
    "credential_leak",
    "account_write",
    "account_query",
    "real_order",
    "real_cancel",
    "provider_fetch",
    "lake_write",
    "broker_lake_write",
    "publish",
    "current_pointer_publish",
    "simulation_or_live_run",
    "gateway_socket_open",
    "http_client_call",
)


class QmtSessionState(str, Enum):
    """QMT session 的稳定状态集合。"""

    NOT_CONFIGURED = "not_configured"
    LOGIN_PENDING = "login_pending"
    READY = "ready"
    EXPIRED = "expired"
    BLOCKED = "blocked"
    ERROR = "error"


class QmtSessionBlockedReason(str, Enum):
    """QMT session fail-closed 的稳定 reason code。"""

    CREDENTIAL_NOT_CONFIGURED = "credential_not_configured"
    CREDENTIAL_READ_FORBIDDEN = "credential_read_forbidden"
    LOGIN_NOT_ALLOWED = "login_not_allowed"
    LOGIN_FAILED = "login_failed"
    SESSION_NOT_READY = "session_not_ready"
    SESSION_EXPIRED = "session_expired"
    GATEWAY_RUNTIME_NOT_READY = "gateway_runtime_not_ready"
    QMT_RUNTIME_UNAVAILABLE = "qmt_runtime_unavailable"
    REDACTION_FAILED = "redaction_failed"


@dataclass(frozen=True, slots=True)
class QmtCredentialRef:
    """只保存脱敏凭据引用和变量名，不保存真实值。"""

    credential_ref: str = "<qmt-credential-ref-placeholder>"
    required_keys: tuple[str, ...] = DEFAULT_QMT_CREDENTIAL_REQUIRED_KEYS
    missing_keys: tuple[str, ...] = ()
    redaction_status: str = "pass"
    leak_count: int = 0
    schema_version: str = QMT_SESSION_SCHEMA_VERSION

    @property
    def configured(self) -> bool:
        return not self.missing_keys and self.redaction_status == "pass"

    def to_dict(self) -> dict[str, object]:
        return {
            "credential_ref": self.credential_ref,
            "required_keys": list(self.required_keys),
            "missing_keys": list(self.missing_keys),
            "redaction_status": self.redaction_status,
            "leak_count": self.leak_count,
            "configured": self.configured,
            "schema_version": self.schema_version,
        }


@dataclass(frozen=True, slots=True)
class QmtSessionConfig:
    """QMT session 构造配置；默认不允许真实登录。"""

    credential_ref: QmtCredentialRef = field(default_factory=QmtCredentialRef)
    ready_timeout_seconds: int = DEFAULT_QMT_SESSION_READY_TIMEOUT_SECONDS
    session_ttl_seconds: int = DEFAULT_QMT_SESSION_TTL_SECONDS
    qmt_login_allowed: bool = False
    redaction_required: bool = True
    gateway_runtime_ready: bool = False
    credential_ref_source: str = "<local-untracked-env-placeholder>"
    schema_version: str = QMT_SESSION_SCHEMA_VERSION

    def to_dict(self) -> dict[str, object]:
        return {
            "credential_ref": self.credential_ref.to_dict(),
            "ready_timeout_seconds": self.ready_timeout_seconds,
            "session_ttl_seconds": self.session_ttl_seconds,
            "qmt_login_allowed": self.qmt_login_allowed,
            "redaction_required": self.redaction_required,
            "gateway_runtime_ready": self.gateway_runtime_ready,
            "credential_ref_source": self.credential_ref_source,
            "schema_version": self.schema_version,
        }


@dataclass(frozen=True, slots=True)
class QmtSessionSnapshot:
    """session 状态快照；health / diagnostics / ready gate 共用。"""

    state: QmtSessionState
    ready: bool
    blocked_reason: QmtSessionBlockedReason | None = None
    credential_ref: str = "<qmt-credential-ref-placeholder>"
    started_at: str = ""
    ready_at: str = ""
    expires_at: str = ""
    runtime_status: str = "not_started"
    counters: Mapping[str, int] = field(default_factory=lambda: collect_qmt_session_safety_counters())
    redaction_status: str = "pass"
    leak_count: int = 0
    schema_version: str = QMT_SESSION_SCHEMA_VERSION

    @property
    def blocked(self) -> bool:
        return not self.ready

    def to_dict(self) -> dict[str, object]:
        return {
            "state": _state_value(self.state),
            "ready": self.ready,
            "blocked": self.blocked,
            "blocked_reason": _reason_value(self.blocked_reason),
            "credential_ref": self.credential_ref,
            "started_at": self.started_at,
            "ready_at": self.ready_at,
            "expires_at": self.expires_at,
            "runtime_status": self.runtime_status,
            "counters": dict(self.counters),
            "redaction_status": self.redaction_status,
            "leak_count": self.leak_count,
            "schema_version": self.schema_version,
        }


@dataclass(frozen=True, slots=True)
class QmtSessionGateResult:
    """query_positions 前置 ready gate 结果。"""

    allowed: bool
    state: QmtSessionState
    blocked_reason: QmtSessionBlockedReason | None
    endpoint_id: str = "query_positions"
    adapter_call_allowed: bool = False
    counters: Mapping[str, int] = field(default_factory=lambda: collect_qmt_session_safety_counters())
    redaction_status: str = "pass"
    schema_version: str = QMT_SESSION_SCHEMA_VERSION

    @property
    def blocked(self) -> bool:
        return not self.allowed

    def to_dict(self) -> dict[str, object]:
        return {
            "allowed": self.allowed,
            "blocked": self.blocked,
            "state": _state_value(self.state),
            "blocked_reason": _reason_value(self.blocked_reason),
            "endpoint_id": self.endpoint_id,
            "adapter_call_allowed": self.adapter_call_allowed,
            "counters": dict(self.counters),
            "redaction_status": self.redaction_status,
            "schema_version": self.schema_version,
        }


class QmtLoginAdapter(Protocol):
    """真实 Windows adapter 的最小注入协议；本模块不实现真实 SDK 调用。"""

    def login(self, config: QmtSessionConfig) -> QmtSessionSnapshot:
        """执行登录并返回快照；fixture adapter 可实现该方法。"""

    def check_ready(self) -> QmtSessionSnapshot:
        """检查 ready 状态；不得在本模块中触发真实 QMT import。"""

    def logout(self) -> QmtSessionSnapshot | None:
        """退出登录并返回快照；默认由运行面实现。"""


def build_qmt_credential_ref(
    source: Mapping[str, object] | None = None,
    *,
    required_keys: Sequence[str] = DEFAULT_QMT_CREDENTIAL_REQUIRED_KEYS,
) -> QmtCredentialRef:
    """从显式 mapping 生成脱敏 credential_ref；不读取真实 `.env`。"""

    raw = dict(source or {})
    normalized_required = tuple(str(key) for key in required_keys)
    missing = tuple(
        key for key in normalized_required if not str(raw.get(key, "")).strip()
    )
    raw_ref = raw.get(
        "credential_ref",
        raw.get("QMT_CREDENTIAL_REF", "<qmt-credential-ref-placeholder>"),
    )
    credential_ref = _safe_credential_ref(raw_ref)
    report = scan_for_qmt_sensitive_leaks({"credential_ref": credential_ref})
    status = "pass" if report.leak_count == 0 else "failed"
    return QmtCredentialRef(
        credential_ref=credential_ref,
        required_keys=normalized_required,
        missing_keys=missing,
        redaction_status=status,
        leak_count=report.leak_count,
    )


def build_qmt_session_config(
    source: Mapping[str, object] | None = None,
    *,
    qmt_login_allowed: bool = False,
    gateway_runtime_ready: bool = False,
    ready_timeout_seconds: int = DEFAULT_QMT_SESSION_READY_TIMEOUT_SECONDS,
    session_ttl_seconds: int = DEFAULT_QMT_SESSION_TTL_SECONDS,
    redaction_required: bool = True,
) -> QmtSessionConfig:
    """构造 session config；只消费显式 mapping 和 placeholder。"""

    raw = dict(source or {})
    credential_source = raw.get("credential_ref_source", raw)
    credential_ref = build_qmt_credential_ref(_as_mapping(credential_source))
    return QmtSessionConfig(
        credential_ref=credential_ref,
        ready_timeout_seconds=int(
            raw.get("ready_timeout_seconds", ready_timeout_seconds)
        ),
        session_ttl_seconds=int(raw.get("session_ttl_seconds", session_ttl_seconds)),
        qmt_login_allowed=_as_bool(raw.get("qmt_login_allowed", qmt_login_allowed)),
        redaction_required=_as_bool(raw.get("redaction_required", redaction_required)),
        gateway_runtime_ready=_as_bool(
            raw.get("gateway_runtime_ready", gateway_runtime_ready)
        ),
        credential_ref_source=str(
            raw.get("credential_ref_source_name", "<local-untracked-env-placeholder>")
        ),
    )


def plan_qmt_login_session(
    config: QmtSessionConfig | Mapping[str, object] | None = None,
    *,
    adapter: QmtLoginAdapter | None = None,
    now: datetime | None = None,
) -> QmtSessionSnapshot:
    """规划或执行注入式 fixture 登录；默认 fail-closed 且 adapter call 为 0。"""

    current_config = (
        config if isinstance(config, QmtSessionConfig) else build_qmt_session_config(config)
    )
    current_time = _format_time(now)
    credential = current_config.credential_ref

    if credential.missing_keys:
        return _blocked_snapshot(
            QmtSessionState.NOT_CONFIGURED,
            QmtSessionBlockedReason.CREDENTIAL_NOT_CONFIGURED,
            credential,
            runtime_status="credential_missing",
            started_at=current_time,
        )
    if current_config.redaction_required and (
        credential.redaction_status != "pass" or credential.leak_count > 0
    ):
        return _blocked_snapshot(
            QmtSessionState.BLOCKED,
            QmtSessionBlockedReason.REDACTION_FAILED,
            credential,
            runtime_status="redaction_failed",
            started_at=current_time,
        )
    if not current_config.qmt_login_allowed:
        return _blocked_snapshot(
            QmtSessionState.BLOCKED,
            QmtSessionBlockedReason.LOGIN_NOT_ALLOWED,
            credential,
            runtime_status="login_not_allowed",
            started_at=current_time,
        )
    if not current_config.gateway_runtime_ready:
        return _blocked_snapshot(
            QmtSessionState.BLOCKED,
            QmtSessionBlockedReason.GATEWAY_RUNTIME_NOT_READY,
            credential,
            runtime_status="gateway_runtime_not_ready",
            started_at=current_time,
        )
    if adapter is None:
        return _blocked_snapshot(
            QmtSessionState.ERROR,
            QmtSessionBlockedReason.QMT_RUNTIME_UNAVAILABLE,
            credential,
            runtime_status="adapter_missing",
            started_at=current_time,
        )

    snapshot = adapter.login(current_config)
    return evaluate_qmt_session_ready(snapshot, now=now)


def evaluate_qmt_session_ready(
    snapshot: QmtSessionSnapshot,
    *,
    now: datetime | None = None,
) -> QmtSessionSnapshot:
    """归一化 ready 状态；expired / blocked / error 都不可被解释为 ready。"""

    state = _normalize_state(snapshot.state)
    if state is not snapshot.state:
        snapshot = replace(snapshot, state=state)

    if snapshot.redaction_status != "pass" or snapshot.leak_count > 0:
        return replace(
            snapshot,
            state=QmtSessionState.BLOCKED,
            ready=False,
            blocked_reason=QmtSessionBlockedReason.REDACTION_FAILED,
        )

    expires_at = _parse_time(snapshot.expires_at)
    current_time = now or datetime.now(tz=timezone.utc)
    if expires_at is not None and current_time >= expires_at:
        return replace(
            snapshot,
            state=QmtSessionState.EXPIRED,
            ready=False,
            blocked_reason=QmtSessionBlockedReason.SESSION_EXPIRED,
        )

    if state is QmtSessionState.READY and snapshot.ready:
        return snapshot

    reason = snapshot.blocked_reason or QmtSessionBlockedReason.SESSION_NOT_READY
    return replace(snapshot, ready=False, blocked_reason=reason)


def require_qmt_session_ready(
    snapshot: QmtSessionSnapshot,
    *,
    endpoint_id: str = "query_positions",
    now: datetime | None = None,
) -> QmtSessionGateResult:
    """在 endpoint adapter 前执行 session ready gate。"""

    current = evaluate_qmt_session_ready(snapshot, now=now)
    if current.ready and current.state is QmtSessionState.READY:
        return QmtSessionGateResult(
            allowed=True,
            state=current.state,
            blocked_reason=None,
            endpoint_id=endpoint_id,
            adapter_call_allowed=True,
            counters=collect_qmt_session_safety_counters(current.counters),
            redaction_status=current.redaction_status,
        )
    return QmtSessionGateResult(
        allowed=False,
        state=current.state,
        blocked_reason=current.blocked_reason or QmtSessionBlockedReason.SESSION_NOT_READY,
        endpoint_id=endpoint_id,
        adapter_call_allowed=False,
        counters=collect_qmt_session_safety_counters(current.counters),
        redaction_status=current.redaction_status,
    )


def build_qmt_session_diagnostics(snapshot: QmtSessionSnapshot) -> dict[str, object]:
    """生成 redacted session diagnostics；不输出任何真实凭据。"""

    payload = snapshot.to_dict()
    redacted, report = redact_qmt_mapping(payload)
    leak_report = scan_for_qmt_sensitive_leaks(redacted)
    redaction_status = (
        "pass"
        if report.leak_count == 0 and leak_report.leak_count == 0
        else "failed"
    )
    redacted["redaction_status"] = redaction_status
    redacted["leak_count"] = report.leak_count + leak_report.leak_count
    redacted["redaction_report"] = report.to_dict()
    redacted["schema_version"] = QMT_SESSION_SCHEMA_VERSION
    return redacted


def collect_qmt_session_safety_counters(
    counters: Mapping[str, int] | None = None,
) -> dict[str, int]:
    """归一化 session 禁止操作计数；fixture 默认全部为 0。"""

    normalized = {key: 0 for key in QMT_SESSION_REQUIRED_ZERO_COUNTERS}
    if counters is None:
        return normalized
    for key, value in dict(counters).items():
        normalized[str(key)] = int(value)
    return normalized


def _blocked_snapshot(
    state: QmtSessionState,
    reason: QmtSessionBlockedReason,
    credential: QmtCredentialRef,
    *,
    runtime_status: str,
    started_at: str = "",
) -> QmtSessionSnapshot:
    return QmtSessionSnapshot(
        state=state,
        ready=False,
        blocked_reason=reason,
        credential_ref=credential.credential_ref,
        started_at=started_at,
        runtime_status=runtime_status,
        counters=collect_qmt_session_safety_counters(),
        redaction_status=credential.redaction_status,
        leak_count=credential.leak_count,
    )


def _safe_credential_ref(value: object) -> str:
    text = str(value or "").strip()
    if not text:
        return REDACTED_VALUE
    if text == REDACTED_VALUE:
        return text
    return REDACTED_VALUE


def _parse_time(value: object) -> datetime | None:
    if isinstance(value, datetime):
        return value if value.tzinfo is not None else value.replace(tzinfo=timezone.utc)
    if not isinstance(value, str) or not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo is not None else parsed.replace(tzinfo=timezone.utc)


def _format_time(value: datetime | None) -> str:
    if value is None:
        return ""
    current = value if value.tzinfo is not None else value.replace(tzinfo=timezone.utc)
    return current.isoformat()


def _reason_value(reason: QmtSessionBlockedReason | None) -> str:
    return reason.value if reason is not None else ""


def _normalize_state(state: object) -> QmtSessionState:
    if isinstance(state, QmtSessionState):
        return state
    try:
        return QmtSessionState(str(state))
    except ValueError:
        return QmtSessionState.ERROR


def _state_value(state: object) -> str:
    return _normalize_state(state).value


def _as_mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _as_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return bool(value)
