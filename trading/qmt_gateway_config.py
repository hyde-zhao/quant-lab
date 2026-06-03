"""CR019-S04 的 Windows QMT gateway 配置离线合同。

本模块只构造和校验 gateway 配置对象，不读取配置文件、不读取凭据、
不启动服务、不绑定端口、不访问 QMT / MiniQMT / XtQuant。
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from enum import Enum
from ipaddress import ip_address, ip_network
from typing import Mapping, Sequence


GATEWAY_CONFIG_SCHEMA_VERSION = "cr019-s04-gateway-config-v1"
DEFAULT_GATEWAY_PORT = 18765
DEFAULT_CONFIG_PATH = "<config-path>"
DEFAULT_AUTH_MODE = "pairing_hmac"
NO_AUTH_MODE = "no_auth"
DEFAULT_PAIRING_REQUEST_TTL_SECONDS = 600
DEFAULT_PAIRING_CODE_TTL_SECONDS = 300
DEFAULT_HMAC_CLOCK_SKEW_SECONDS = 300
DEFAULT_NONCE_TTL_SECONDS = 600

GATEWAY_REQUIRED_REDACTION_FIELDS: tuple[str, ...] = (
    "secret",
    "token",
    "account",
    "session",
    "password",
    ".env",
)

GATEWAY_FORBIDDEN_COUNTER_FIELDS: tuple[str, ...] = (
    "dependency_change",
    "service_start",
    "service_start_count",
    "service_bind",
    "port_bind_count",
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
    "http_client_call",
    "gateway_socket_open",
    "public_exposure_allowed_count",
)


class GatewayBlockedReason(str, Enum):
    """S04 配置与生命周期合同的稳定阻断原因。"""

    PUBLIC_BIND_FORBIDDEN = "public_bind_forbidden"
    PUBLIC_EXPOSURE_NOT_AUTHORIZED = "public_exposure_not_authorized"
    FIREWALL_POLICY_MISSING = "firewall_policy_missing"
    ALLOWLIST_MISSING = "allowlist_missing"
    ALLOWLIST_PUBLIC_SOURCE_FORBIDDEN = "allowlist_public_source_forbidden"
    INVALID_ALLOWLIST_SOURCE = "invalid_allowlist_source"
    INVALID_BIND_HOST = "invalid_bind_host"
    INVALID_PORT = "invalid_port"
    CONFIG_PATH_MISSING = "config_path_missing"
    REDACTION_POLICY_INCOMPLETE = "redaction_policy_incomplete"
    HEARTBEAT_POLICY_INVALID = "heartbeat_policy_invalid"
    CREDENTIAL_READ_FORBIDDEN = "credential_read_forbidden"
    QMT_CALL_FORBIDDEN = "qmt_call_forbidden"
    AUTH_MODE_INVALID = "auth_mode_invalid"
    AUTH_NO_AUTH_NOT_ALLOWED = "auth_no_auth_not_allowed"
    AUTH_TTL_INVALID = "auth_ttl_invalid"


@dataclass(frozen=True, slots=True)
class GatewayBindConfig:
    """Windows gateway 的 host / port 合同；不执行真实绑定。"""

    bind_host: str = "127.0.0.1"
    port: int = DEFAULT_GATEWAY_PORT
    public_exposure_allowed: bool = False
    wsl_access_host: str = "<windows-host>"

    def to_dict(self) -> dict[str, object]:
        return {
            "bind_host": self.bind_host,
            "port": self.port,
            "public_exposure_allowed": self.public_exposure_allowed,
            "wsl_access_host": self.wsl_access_host,
        }


@dataclass(frozen=True, slots=True)
class GatewayFirewallPolicy:
    """Windows 防火墙合同；只校验字段，不创建系统规则。"""

    required: bool = True
    enabled: bool = True
    inbound_rule_present: bool = True
    rule_name: str = "qmt-gateway-local-only"
    profile: str = "private"

    def to_dict(self) -> dict[str, object]:
        return {
            "required": self.required,
            "enabled": self.enabled,
            "inbound_rule_present": self.inbound_rule_present,
            "rule_name": self.rule_name,
            "profile": self.profile,
        }


@dataclass(frozen=True, slots=True)
class GatewayAllowlist:
    """允许访问 gateway 的来源白名单。"""

    sources: tuple[str, ...] = ("127.0.0.1/32",)
    required: bool = True
    description: str = "local or explicitly approved WSL source"

    def __post_init__(self) -> None:
        object.__setattr__(self, "sources", _as_tuple(self.sources))

    def to_dict(self) -> dict[str, object]:
        return {
            "sources": list(self.sources),
            "required": self.required,
            "description": self.description,
        }


@dataclass(frozen=True, slots=True)
class HeartbeatPolicy:
    """gateway heartbeat 合同；不主动探测服务。"""

    interval_seconds: int = 10
    stale_after_seconds: int = 30
    unhealthy_after_missed: int = 3
    expected_schema_version: str = GATEWAY_CONFIG_SCHEMA_VERSION

    def to_dict(self) -> dict[str, object]:
        return {
            "interval_seconds": self.interval_seconds,
            "stale_after_seconds": self.stale_after_seconds,
            "unhealthy_after_missed": self.unhealthy_after_missed,
            "expected_schema_version": self.expected_schema_version,
        }


@dataclass(frozen=True, slots=True)
class RedactionPolicy:
    """日志脱敏字段合同；只保存字段名，不保存敏感值。"""

    redacted_fields: tuple[str, ...] = GATEWAY_REQUIRED_REDACTION_FIELDS
    required_fields: tuple[str, ...] = GATEWAY_REQUIRED_REDACTION_FIELDS
    redaction_status: str = "redacted"

    def __post_init__(self) -> None:
        object.__setattr__(self, "redacted_fields", _as_tuple(self.redacted_fields))
        object.__setattr__(self, "required_fields", _as_tuple(self.required_fields))

    @property
    def missing_fields(self) -> tuple[str, ...]:
        available = {field_name.lower() for field_name in self.redacted_fields}
        return tuple(
            field_name
            for field_name in self.required_fields
            if field_name.lower() not in available
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "redacted_fields": list(self.redacted_fields),
            "required_fields": list(self.required_fields),
            "redaction_status": self.redaction_status,
        }


@dataclass(frozen=True, slots=True)
class GatewayAuthConfig:
    """S05 pairing / HMAC 鉴权配置；不包含真实 secret。"""

    auth_mode: str = DEFAULT_AUTH_MODE
    pairing_request_ttl_seconds: int = DEFAULT_PAIRING_REQUEST_TTL_SECONDS
    pairing_code_ttl_seconds: int = DEFAULT_PAIRING_CODE_TTL_SECONDS
    hmac_clock_skew_seconds: int = DEFAULT_HMAC_CLOCK_SKEW_SECONDS
    nonce_ttl_seconds: int = DEFAULT_NONCE_TTL_SECONDS
    allow_no_auth_debug: bool = False
    allow_no_auth_fixture: bool = False
    allow_no_auth_temporary: bool = False

    @property
    def normalized_auth_mode(self) -> str:
        return self.auth_mode.strip().lower().replace("-", "_")

    @property
    def no_auth_explicitly_allowed(self) -> bool:
        return (
            self.allow_no_auth_debug
            or self.allow_no_auth_fixture
            or self.allow_no_auth_temporary
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "auth_mode": self.auth_mode,
            "pairing_request_ttl_seconds": self.pairing_request_ttl_seconds,
            "pairing_code_ttl_seconds": self.pairing_code_ttl_seconds,
            "hmac_clock_skew_seconds": self.hmac_clock_skew_seconds,
            "nonce_ttl_seconds": self.nonce_ttl_seconds,
            "allow_no_auth_debug": self.allow_no_auth_debug,
            "allow_no_auth_fixture": self.allow_no_auth_fixture,
            "allow_no_auth_temporary": self.allow_no_auth_temporary,
        }


@dataclass(frozen=True, slots=True)
class GatewaySafetyCounters:
    """S04 必须保持为 0 的真实操作计数。"""

    dependency_change: int = 0
    service_start: int = 0
    service_start_count: int = 0
    service_bind: int = 0
    port_bind_count: int = 0
    credential_read: int = 0
    qmt_operation: int = 0
    qmt_api_call: int = 0
    xtquant_import: int = 0
    real_order: int = 0
    real_cancel: int = 0
    account_query: int = 0
    account_write: int = 0
    provider_fetch: int = 0
    lake_write: int = 0
    broker_lake_write: int = 0
    publish: int = 0
    current_pointer_publish: int = 0
    simulation_or_live_run: int = 0
    http_client_call: int = 0
    gateway_socket_open: int = 0
    public_exposure_allowed_count: int = 0

    def to_dict(self) -> dict[str, int]:
        return {key: int(getattr(self, key)) for key in GATEWAY_FORBIDDEN_COUNTER_FIELDS}


@dataclass(frozen=True, slots=True)
class GatewayConfig:
    """gateway 配置的完整离线合同。"""

    config_path: str = DEFAULT_CONFIG_PATH
    bind: GatewayBindConfig = field(default_factory=GatewayBindConfig)
    firewall: GatewayFirewallPolicy = field(default_factory=GatewayFirewallPolicy)
    allowlist: GatewayAllowlist = field(default_factory=GatewayAllowlist)
    heartbeat: HeartbeatPolicy = field(default_factory=HeartbeatPolicy)
    redaction: RedactionPolicy = field(default_factory=RedactionPolicy)
    auth: GatewayAuthConfig = field(default_factory=GatewayAuthConfig)
    auth_mode: str = DEFAULT_AUTH_MODE
    gateway_name: str = "qmt-fastapi-gateway"
    schema_version: str = GATEWAY_CONFIG_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.auth.auth_mode == self.auth_mode:
            return
        if self.auth.auth_mode == DEFAULT_AUTH_MODE and self.auth_mode != DEFAULT_AUTH_MODE:
            object.__setattr__(self, "auth", replace(self.auth, auth_mode=self.auth_mode))
            return
        object.__setattr__(self, "auth_mode", self.auth.auth_mode)

    def to_dict(self) -> dict[str, object]:
        return {
            "config_path": self.config_path,
            "bind": self.bind.to_dict(),
            "firewall": self.firewall.to_dict(),
            "allowlist": self.allowlist.to_dict(),
            "heartbeat": self.heartbeat.to_dict(),
            "redaction": self.redaction.to_dict(),
            "auth": self.auth.to_dict(),
            "auth_mode": self.auth_mode,
            "gateway_name": self.gateway_name,
            "schema_version": self.schema_version,
        }


@dataclass(frozen=True, slots=True)
class GatewayConfigValidation:
    """配置安全校验结果；blocked reason 必须可测试。"""

    accepted: bool
    status: str
    reasons: tuple[str, ...] = ()
    counters: Mapping[str, int] = field(
        default_factory=lambda: collect_gateway_safety_counters()
    )
    public_exposure_allowed_count: int = 0
    missing_redaction_fields: tuple[str, ...] = ()

    @property
    def blocked(self) -> bool:
        return not self.accepted

    @property
    def primary_reason(self) -> str:
        return self.reasons[0] if self.reasons else ""

    def to_dict(self) -> dict[str, object]:
        return {
            "accepted": self.accepted,
            "blocked": self.blocked,
            "status": self.status,
            "primary_reason": self.primary_reason,
            "reasons": list(self.reasons),
            "public_exposure_allowed_count": self.public_exposure_allowed_count,
            "missing_redaction_fields": list(self.missing_redaction_fields),
            "counters": dict(self.counters),
        }


def build_gateway_config(
    source: Mapping[str, object] | GatewayConfig | None = None,
    **overrides: object,
) -> GatewayConfig:
    """从显式 dict / 参数构造配置；不读取磁盘或环境。"""

    if isinstance(source, GatewayConfig) and not overrides:
        return source
    raw: dict[str, object] = {}
    if isinstance(source, Mapping):
        raw.update(source)
    raw.update(overrides)

    auth = _build_auth_config(raw)
    return GatewayConfig(
        config_path=str(raw.get("config_path", DEFAULT_CONFIG_PATH)),
        bind=_build_bind_config(raw.get("bind", raw)),
        firewall=_build_firewall_policy(raw.get("firewall", raw)),
        allowlist=_build_allowlist(raw.get("allowlist", raw)),
        heartbeat=_build_heartbeat_policy(raw.get("heartbeat", raw)),
        redaction=_build_redaction_policy(raw.get("redaction", raw)),
        auth=auth,
        auth_mode=auth.auth_mode,
        gateway_name=str(raw.get("gateway_name", "qmt-fastapi-gateway")),
        schema_version=str(raw.get("schema_version", GATEWAY_CONFIG_SCHEMA_VERSION)),
    )


def validate_gateway_security(config: GatewayConfig) -> GatewayConfigValidation:
    """校验 gateway 配置是否满足 fail-closed 安全边界。"""

    reasons: list[str] = []

    if not config.config_path:
        reasons.append(GatewayBlockedReason.CONFIG_PATH_MISSING.value)
    if config.bind.port <= 0 or config.bind.port > 65535:
        reasons.append(GatewayBlockedReason.INVALID_PORT.value)
    bind_reason = _validate_bind_host(config.bind)
    if bind_reason is not None:
        reasons.append(bind_reason)
    if config.bind.public_exposure_allowed:
        reasons.append(GatewayBlockedReason.PUBLIC_EXPOSURE_NOT_AUTHORIZED.value)
    if (
        config.firewall.required is not True
        or config.firewall.enabled is not True
        or config.firewall.inbound_rule_present is not True
    ):
        reasons.append(GatewayBlockedReason.FIREWALL_POLICY_MISSING.value)
    allowlist_reasons = _validate_allowlist(config.allowlist)
    reasons.extend(allowlist_reasons)
    if _heartbeat_invalid(config.heartbeat):
        reasons.append(GatewayBlockedReason.HEARTBEAT_POLICY_INVALID.value)

    missing_redaction = config.redaction.missing_fields
    if missing_redaction:
        reasons.append(GatewayBlockedReason.REDACTION_POLICY_INCOMPLETE.value)
    auth_reason = _validate_auth_config(config.auth)
    if auth_reason is not None:
        reasons.append(auth_reason)

    unique_reasons = tuple(dict.fromkeys(reasons))
    accepted = not unique_reasons
    return GatewayConfigValidation(
        accepted=accepted,
        status="ready_to_start" if accepted else "blocked_config",
        reasons=unique_reasons,
        counters=collect_gateway_safety_counters(),
        public_exposure_allowed_count=0,
        missing_redaction_fields=missing_redaction,
    )


def collect_gateway_safety_counters(
    counters: Mapping[str, int] | GatewaySafetyCounters | None = None,
) -> dict[str, int]:
    """归一化 S04 禁止操作计数；默认全部为 0。"""

    normalized = GatewaySafetyCounters().to_dict()
    if counters is None:
        return normalized
    raw = counters.to_dict() if isinstance(counters, GatewaySafetyCounters) else dict(counters)
    for key, value in raw.items():
        normalized[str(key)] = int(value)
    return normalized


def _build_bind_config(raw: object) -> GatewayBindConfig:
    if isinstance(raw, GatewayBindConfig):
        return raw
    mapping = _as_mapping(raw)
    return GatewayBindConfig(
        bind_host=str(mapping.get("bind_host", mapping.get("host", "127.0.0.1"))),
        port=int(mapping.get("port", DEFAULT_GATEWAY_PORT)),
        public_exposure_allowed=_as_bool(mapping.get("public_exposure_allowed", False)),
        wsl_access_host=str(mapping.get("wsl_access_host", "<windows-host>")),
    )


def _build_firewall_policy(raw: object) -> GatewayFirewallPolicy:
    if isinstance(raw, GatewayFirewallPolicy):
        return raw
    mapping = _as_mapping(raw)
    return GatewayFirewallPolicy(
        required=_as_bool(mapping.get("firewall_required", mapping.get("required", True))),
        enabled=_as_bool(mapping.get("firewall_enabled", mapping.get("enabled", True))),
        inbound_rule_present=_as_bool(
            mapping.get("inbound_rule_present", mapping.get("rule_present", True))
        ),
        rule_name=str(mapping.get("rule_name", "qmt-gateway-local-only")),
        profile=str(mapping.get("profile", "private")),
    )


def _build_allowlist(raw: object) -> GatewayAllowlist:
    if isinstance(raw, GatewayAllowlist):
        return raw
    mapping = _as_mapping(raw)
    return GatewayAllowlist(
        sources=_as_tuple(mapping.get("allowlist_sources", mapping.get("sources", ("127.0.0.1/32",)))),
        required=_as_bool(mapping.get("allowlist_required", mapping.get("required", True))),
        description=str(
            mapping.get("allowlist_description", mapping.get("description", "local source"))
        ),
    )


def _build_heartbeat_policy(raw: object) -> HeartbeatPolicy:
    if isinstance(raw, HeartbeatPolicy):
        return raw
    mapping = _as_mapping(raw)
    return HeartbeatPolicy(
        interval_seconds=int(mapping.get("heartbeat_interval_seconds", mapping.get("interval_seconds", 10))),
        stale_after_seconds=int(mapping.get("heartbeat_stale_after_seconds", mapping.get("stale_after_seconds", 30))),
        unhealthy_after_missed=int(mapping.get("unhealthy_after_missed", 3)),
        expected_schema_version=str(
            mapping.get("expected_schema_version", GATEWAY_CONFIG_SCHEMA_VERSION)
        ),
    )


def _build_redaction_policy(raw: object) -> RedactionPolicy:
    if isinstance(raw, RedactionPolicy):
        return raw
    mapping = _as_mapping(raw)
    return RedactionPolicy(
        redacted_fields=_as_tuple(
            mapping.get("redacted_fields", GATEWAY_REQUIRED_REDACTION_FIELDS)
        ),
        required_fields=_as_tuple(
            mapping.get("required_fields", GATEWAY_REQUIRED_REDACTION_FIELDS)
        ),
        redaction_status=str(mapping.get("redaction_status", "redacted")),
    )


def _build_auth_config(raw: object) -> GatewayAuthConfig:
    if isinstance(raw, GatewayAuthConfig):
        return raw
    mapping = _as_mapping(raw)
    nested = _as_mapping(mapping.get("auth", mapping))
    return GatewayAuthConfig(
        auth_mode=str(nested.get("auth_mode", mapping.get("auth_mode", DEFAULT_AUTH_MODE))),
        pairing_request_ttl_seconds=int(
            nested.get(
                "pairing_request_ttl_seconds",
                mapping.get(
                    "pairing_request_ttl_seconds",
                    DEFAULT_PAIRING_REQUEST_TTL_SECONDS,
                ),
            )
        ),
        pairing_code_ttl_seconds=int(
            nested.get(
                "pairing_code_ttl_seconds",
                mapping.get("pairing_code_ttl_seconds", DEFAULT_PAIRING_CODE_TTL_SECONDS),
            )
        ),
        hmac_clock_skew_seconds=int(
            nested.get(
                "hmac_clock_skew_seconds",
                mapping.get("hmac_clock_skew_seconds", DEFAULT_HMAC_CLOCK_SKEW_SECONDS),
            )
        ),
        nonce_ttl_seconds=int(
            nested.get(
                "nonce_ttl_seconds",
                mapping.get("nonce_ttl_seconds", DEFAULT_NONCE_TTL_SECONDS),
            )
        ),
        allow_no_auth_debug=_as_bool(
            nested.get("allow_no_auth_debug", mapping.get("allow_no_auth_debug", False))
        ),
        allow_no_auth_fixture=_as_bool(
            nested.get("allow_no_auth_fixture", mapping.get("allow_no_auth_fixture", False))
        ),
        allow_no_auth_temporary=_as_bool(
            nested.get(
                "allow_no_auth_temporary",
                mapping.get("allow_no_auth_temporary", False),
            )
        ),
    )


def _validate_bind_host(bind: GatewayBindConfig) -> str | None:
    host = bind.bind_host.strip().lower()
    if not host:
        return GatewayBlockedReason.INVALID_BIND_HOST.value
    if host == "localhost":
        return None
    try:
        address = ip_address(host)
    except ValueError:
        return GatewayBlockedReason.INVALID_BIND_HOST.value
    if address.is_unspecified or address.is_global:
        return GatewayBlockedReason.PUBLIC_BIND_FORBIDDEN.value
    return None


def _validate_allowlist(allowlist: GatewayAllowlist) -> tuple[str, ...]:
    if allowlist.required and not allowlist.sources:
        return (GatewayBlockedReason.ALLOWLIST_MISSING.value,)

    reasons: list[str] = []
    for source in allowlist.sources:
        try:
            network = ip_network(str(source), strict=False)
        except ValueError:
            reasons.append(GatewayBlockedReason.INVALID_ALLOWLIST_SOURCE.value)
            continue
        if network.is_global:
            reasons.append(GatewayBlockedReason.ALLOWLIST_PUBLIC_SOURCE_FORBIDDEN.value)
    return tuple(dict.fromkeys(reasons))


def _heartbeat_invalid(heartbeat: HeartbeatPolicy) -> bool:
    return (
        heartbeat.interval_seconds <= 0
        or heartbeat.stale_after_seconds <= 0
        or heartbeat.stale_after_seconds < heartbeat.interval_seconds
        or heartbeat.unhealthy_after_missed <= 0
    )


def _validate_auth_config(auth: GatewayAuthConfig) -> str | None:
    if (
        auth.pairing_request_ttl_seconds <= 0
        or auth.pairing_code_ttl_seconds <= 0
        or auth.hmac_clock_skew_seconds <= 0
        or auth.nonce_ttl_seconds <= 0
    ):
        return GatewayBlockedReason.AUTH_TTL_INVALID.value
    mode = auth.normalized_auth_mode
    if mode == DEFAULT_AUTH_MODE:
        return None
    if mode != NO_AUTH_MODE:
        return GatewayBlockedReason.AUTH_MODE_INVALID.value
    if not auth.no_auth_explicitly_allowed:
        return GatewayBlockedReason.AUTH_NO_AUTH_NOT_ALLOWED.value
    return None


def _as_mapping(raw: object) -> Mapping[str, object]:
    return raw if isinstance(raw, Mapping) else {}


def _as_tuple(value: object) -> tuple[str, ...]:
    if isinstance(value, str):
        return (value,)
    if isinstance(value, Sequence):
        return tuple(str(item) for item in value)
    return tuple(str(item) for item in value) if value is not None else ()


def _as_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return bool(value)
