"""CR020 Windows QMT gateway 的显式运行时入口。

本模块只在用户手动执行 runtime CLI 时读取 `.env`、启动 HTTP server 或
懒加载 XtQuant。导入模块本身不读取凭据、不启动服务、不连接 QMT。
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import importlib
import json
from pathlib import Path
import sys
import time
from typing import Callable, Mapping
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from trading.qmt_auth import (
    PairingApproval,
    QmtAuthConfig,
    QmtHmacHeaderProvider,
    QmtNonceReplayStore,
    build_qmt_request_source_context,
    evaluate_qmt_auth_admission,
    stable_qmt_auth_hash,
)
from trading.qmt_client import QmtRestRequest, QmtTransportResult
from trading.qmt_endpoint_matrix import build_capabilities_payload
from trading.qmt_gateway_config import GatewayAllowlist
from trading.qmt_gateway_contracts import (
    CR020_QUERY_POSITIONS_ENDPOINT_ID,
    CR020_QUERY_POSITIONS_PATH,
    CR020_QUERY_POSITIONS_SCOPE,
    QmtBlockedReason,
    QmtQueryPositionsRequest,
    build_query_positions_blocked_result,
)
from trading.qmt_gateway_service import dispatch_qmt_gateway_endpoint
from trading.qmt_gateway_session import (
    QmtSessionBlockedReason,
    QmtSessionSnapshot,
    QmtSessionState,
)


RUNTIME_SCHEMA_VERSION = "cr020-runtime-manual-validation-v1"
DEFAULT_RUNTIME_AUTHORIZATION_REF = "manual-cr020-runtime-validation"


@dataclass(frozen=True, slots=True)
class QmtRuntimeConfig:
    """S/C runtime 共享配置；secret 字段不得出现在 public dict。"""

    host: str = "127.0.0.1"
    port: int = 18765
    allowed_source: str = "127.0.0.1/32"
    client_id: str = ""
    client_secret: str = ""
    xtquant_site_packages: str = ""
    miniqmt_path: str = ""
    account_id: str = ""
    account_type: str = "STOCK"
    runtime_authorization_ref: str = DEFAULT_RUNTIME_AUTHORIZATION_REF
    session_ttl_seconds: int = 3600
    schema_version: str = RUNTIME_SCHEMA_VERSION

    @property
    def base_url(self) -> str:
        return f"http://{self.host}:{self.port}"

    def to_public_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "host": self.host,
            "port": self.port,
            "base_url": self.base_url,
            "allowed_source": self.allowed_source,
            "client_id_hash": stable_qmt_auth_hash(self.client_id) if self.client_id else "",
            "client_secret_ref": "[REDACTED]" if self.client_secret else "",
            "xtquant_site_packages_configured": bool(self.xtquant_site_packages),
            "miniqmt_path_configured": bool(self.miniqmt_path),
            "account_ref": _redacted_ref(self.account_id, "account"),
            "account_type": self.account_type,
            "runtime_authorization_ref": self.runtime_authorization_ref,
            "session_ttl_seconds": self.session_ttl_seconds,
        }


class StdlibQmtRestTransport:
    """C 端真实 HTTP transport；只由 runtime CLI 显式启用。"""

    def __init__(self, *, opener: Callable[..., object] | None = None) -> None:
        self._opener = opener or urlopen

    def send(self, request: QmtRestRequest) -> QmtTransportResult:
        started = time.monotonic()
        url = f"{request.base_url.rstrip('/')}{request.path}"
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            **dict(request.headers),
        }
        http_request = Request(
            url,
            data=request.body,
            headers=headers,
            method=request.method,
        )
        try:
            response = self._opener(http_request, timeout=request.timeout_seconds)
            status_code = int(getattr(response, "status", 200))
            body_bytes = response.read()
            body = _json_body(body_bytes)
            status = str(body.get("status", "allowed" if status_code < 400 else "error"))
            return QmtTransportResult(
                status=status,
                status_code=status_code,
                body=body,
                elapsed_ms=_elapsed_ms(started),
                redaction_status=str(body.get("redaction_status", "redacted")),
            )
        except HTTPError as exc:
            body = _json_body(exc.read())
            return QmtTransportResult(
                status=str(body.get("status", "error")),
                status_code=int(exc.code),
                body=body,
                error_code=str(body.get("blocked_reason") or body.get("reason_code") or ""),
                message=str(body.get("message") or ""),
                elapsed_ms=_elapsed_ms(started),
            )
        except (TimeoutError, URLError) as exc:
            return QmtTransportResult(
                status="timeout" if isinstance(exc, TimeoutError) else "unavailable",
                status_code=0,
                body={},
                error_code="transport_timeout"
                if isinstance(exc, TimeoutError)
                else "gateway_unavailable",
                message=f"REST gateway unavailable: {type(exc).__name__}",
                elapsed_ms=_elapsed_ms(started),
            )


class XtQuantRuntimeAdapter:
    """Windows S 端 XtQuant adapter；所有 imports 都在手动运行时懒加载。"""

    def __init__(
        self,
        config: QmtRuntimeConfig,
        *,
        module_loader: Callable[[str], object] | None = None,
    ) -> None:
        self.config = config
        self._load_module = module_loader or importlib.import_module
        self._trader: object | None = None
        self._account: object | None = None
        self._session_snapshot: QmtSessionSnapshot | None = None

    @property
    def session_snapshot(self) -> QmtSessionSnapshot:
        return self._session_snapshot or _blocked_session(
            QmtSessionBlockedReason.SESSION_NOT_READY,
            "runtime-not-started",
            self.config,
        )

    def login(self) -> QmtSessionSnapshot:
        if not self.config.miniqmt_path or not self.config.account_id:
            self._session_snapshot = _blocked_session(
                QmtSessionBlockedReason.CREDENTIAL_NOT_CONFIGURED,
                "missing-miniqmt-path-or-account",
                self.config,
            )
            return self._session_snapshot
        try:
            _ensure_runtime_import_path(self.config)
            xttrader = self._load_module("xtquant.xttrader")
            xttype = self._load_module("xtquant.xttype")
            trader_cls = getattr(xttrader, "XtQuantTrader")
            account_cls = getattr(xttype, "StockAccount")
            session_id = int(time.time())
            trader = trader_cls(self.config.miniqmt_path, session_id)
            _call_if_exists(trader, "start")
            connect_result = _call_if_exists(trader, "connect")
            if not _looks_successful(connect_result):
                self._session_snapshot = _blocked_session(
                    QmtSessionBlockedReason.QMT_RUNTIME_UNAVAILABLE,
                    "xtquant-connect-failed",
                    self.config,
                )
                return self._session_snapshot
            account = account_cls(self.config.account_id, self.config.account_type)
            account_activation_result = _activate_xtquant_account(trader, account)
            if not _looks_successful(account_activation_result):
                self._session_snapshot = _blocked_session(
                    QmtSessionBlockedReason.LOGIN_FAILED,
                    "xtquant-account-activation-failed",
                    self.config,
                )
                return self._session_snapshot
            self._trader = trader
            self._account = account
            now = datetime.now(tz=timezone.utc)
            self._session_snapshot = QmtSessionSnapshot(
                state=QmtSessionState.READY,
                ready=True,
                credential_ref="[REDACTED]",
                started_at=now.isoformat(),
                ready_at=now.isoformat(),
                expires_at=(now + timedelta(seconds=self.config.session_ttl_seconds)).isoformat(),
                runtime_status="xtquant-ready",
            )
            return self._session_snapshot
        except Exception as exc:  # pragma: no cover - depends on Windows XtQuant
            self._session_snapshot = _blocked_session(
                QmtSessionBlockedReason.QMT_RUNTIME_UNAVAILABLE,
                f"xtquant-runtime-error:{type(exc).__name__}",
                self.config,
            )
            return self._session_snapshot

    def query_positions(
        self,
        request: QmtQueryPositionsRequest,
        session_snapshot: QmtSessionSnapshot,
    ) -> Mapping[str, object]:
        if self._trader is None or self._account is None or not session_snapshot.ready:
            raise RuntimeError("qmt session is not ready")
        positions = _call_if_exists(self._trader, "query_stock_positions", self._account)
        rows = [_position_to_mapping(position) for position in _as_list(positions)]
        if not rows and request.include_empty:
            rows = []
        return {
            "positions": rows[: request.max_positions],
            "request_id": request.request_id,
            "runtime_status": "xtquant-query-positions",
        }


class QmtGatewayRuntime:
    """S 端 HTTP gateway runtime；由 CLI 显式创建和启动。"""

    def __init__(
        self,
        config: QmtRuntimeConfig,
        adapter: XtQuantRuntimeAdapter,
    ) -> None:
        self.config = config
        self.adapter = adapter
        self.auth_config = build_runtime_auth_config(config)
        self.allowlist = GatewayAllowlist(sources=(config.allowed_source,), required=True)
        self.nonce_store = QmtNonceReplayStore()

    @property
    def session_snapshot(self) -> QmtSessionSnapshot:
        return self.adapter.session_snapshot

    def login(self) -> QmtSessionSnapshot:
        return self.adapter.login()

    def health_payload(self) -> dict[str, object]:
        snapshot = self.session_snapshot
        return {
            "schema_version": RUNTIME_SCHEMA_VERSION,
            "status": "ok" if snapshot.ready else "blocked",
            "session_ready": snapshot.ready,
            "session_state": snapshot.state.value,
            "blocked_reason": (
                snapshot.blocked_reason.value if snapshot.blocked_reason else ""
            ),
            "runtime_status": snapshot.runtime_status,
            "config": self.config.to_public_dict(),
            "redaction_status": "redacted",
        }

    def capabilities_payload(self) -> dict[str, object]:
        return build_capabilities_payload()

    def query_positions(
        self,
        *,
        body: bytes,
        headers: Mapping[str, object],
        source_ip: str,
    ) -> dict[str, object]:
        auth = evaluate_qmt_auth_admission(
            request_source=build_qmt_request_source_context({"source_ip": source_ip}),
            method="POST",
            path=CR020_QUERY_POSITIONS_PATH,
            body=body,
            headers=headers,
            config=self.auth_config,
            allowlist=self.allowlist,
            endpoint_id=CR020_QUERY_POSITIONS_ENDPOINT_ID,
            required_scope=CR020_QUERY_POSITIONS_SCOPE,
            nonce_store=self.nonce_store,
        )
        request_payload = _json_body(body)
        request = {
            "run_id": str(request_payload.get("run_id") or "qmt-runtime-query-positions"),
            "request_id": str(request_payload.get("request_id") or ""),
            "redaction_label": str(
                request_payload.get("redaction_label") or "qmt-positions-redacted"
            ),
            "payload": request_payload.get("payload")
            if isinstance(request_payload.get("payload"), Mapping)
            else {},
        }
        result = dispatch_qmt_gateway_endpoint(
            CR020_QUERY_POSITIONS_ENDPOINT_ID,
            request,
            session_snapshot=self.session_snapshot,
            auth_admission=auth,
            adapter=self.adapter,
        )
        return result.to_dict()


def load_runtime_env(env_file: str | Path = ".env") -> dict[str, str]:
    """显式读取 dotenv 文件；仅由 runtime CLI 调用。"""

    path = Path(env_file)
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def build_runtime_config(
    env: Mapping[str, str],
    *,
    host: str = "",
    port: int | None = None,
    runtime_authorization_ref: str = "",
) -> QmtRuntimeConfig:
    """从显式 env mapping 生成 runtime config。"""

    return QmtRuntimeConfig(
        host=host or env.get("QMT_GATEWAY_HOST", "127.0.0.1"),
        port=int(port or env.get("QMT_GATEWAY_PORT", 18765)),
        allowed_source=env.get("QMT_GATEWAY_ALLOWED_SOURCE", "127.0.0.1/32"),
        client_id=env.get("QMT_CLIENT_ID", ""),
        client_secret=env.get("QMT_CLIENT_SECRET", ""),
        xtquant_site_packages=env.get("QMT_XTQUANT_SITE_PACKAGES", ""),
        miniqmt_path=env.get("QMT_MINIQMT_PATH", ""),
        account_id=env.get("QMT_ACCOUNT_REF") or env.get("QMT_LOGIN_ACCOUNT", ""),
        account_type=env.get("QMT_ACCOUNT_TYPE", "STOCK"),
        runtime_authorization_ref=(
            runtime_authorization_ref
            or env.get("QMT_RUNTIME_REF")
            or DEFAULT_RUNTIME_AUTHORIZATION_REF
        ),
        session_ttl_seconds=int(env.get("QMT_SESSION_TTL_SECONDS", 3600)),
    )


def build_runtime_auth_config(config: QmtRuntimeConfig) -> QmtAuthConfig:
    """从 runtime config 构造 HMAC 校验配置；secret 只留在内存。"""

    now = datetime.now(tz=timezone.utc)
    approval = PairingApproval(
        request_id="runtime-env-pairing",
        client_id=config.client_id,
        client_id_hash=stable_qmt_auth_hash(config.client_id),
        secret_ref="[REDACTED]",
        scopes=(CR020_QUERY_POSITIONS_SCOPE,),
        approved_at=now,
        code_expires_at=now + timedelta(days=365),
        pairing_code_hash=stable_qmt_auth_hash("runtime-env-pairing"),
        status="approved",
    )
    approvals = {config.client_id: approval} if config.client_id else {}
    secrets = {config.client_id: config.client_secret} if config.client_secret else {}
    return QmtAuthConfig(approvals=approvals, client_secrets=secrets)


def build_runtime_hmac_provider(config: QmtRuntimeConfig) -> QmtHmacHeaderProvider:
    """C 端 runtime HMAC provider。"""

    return QmtHmacHeaderProvider(
        client_id=config.client_id,
        secret=config.client_secret,
        scopes=(CR020_QUERY_POSITIONS_SCOPE,),
        nonce_provider=lambda: stable_qmt_auth_hash(f"{time.time_ns()}|{config.client_id}")[:32],
    )


def create_gateway_runtime(config: QmtRuntimeConfig) -> QmtGatewayRuntime:
    adapter = XtQuantRuntimeAdapter(config)
    runtime = QmtGatewayRuntime(config, adapter)
    runtime.login()
    return runtime


def _ensure_runtime_import_path(config: QmtRuntimeConfig) -> None:
    """把 `.env` 中声明的 XtQuant site-packages 加入当前进程导入路径。"""

    if not config.xtquant_site_packages:
        return
    path = str(Path(config.xtquant_site_packages))
    if path not in sys.path:
        sys.path.insert(0, path)


def serve_gateway_runtime(runtime: QmtGatewayRuntime) -> None:
    """阻塞运行 HTTP server；只能由用户手动 CLI 调用。"""

    handler = _handler_factory(runtime)
    server = ThreadingHTTPServer((runtime.config.host, runtime.config.port), handler)
    server.serve_forever()


def _handler_factory(runtime: QmtGatewayRuntime) -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            if self.path == "/qmt/health":
                _write_json(self, 200, runtime.health_payload())
                return
            if self.path == "/qmt/capabilities":
                _write_json(self, 200, runtime.capabilities_payload())
                return
            _write_json(
                self,
                404,
                build_query_positions_blocked_result(
                    QmtBlockedReason.ENDPOINT_NOT_SUPPORTED,
                    endpoint_id=self.path,
                ).to_dict(),
            )

        def do_POST(self) -> None:  # noqa: N802
            body = self.rfile.read(int(self.headers.get("Content-Length", "0") or 0))
            if self.path != CR020_QUERY_POSITIONS_PATH:
                _write_json(
                    self,
                    404,
                    build_query_positions_blocked_result(
                        QmtBlockedReason.ENDPOINT_NOT_SUPPORTED,
                        endpoint_id=self.path,
                    ).to_dict(),
                )
                return
            payload = runtime.query_positions(
                body=body,
                headers={key: value for key, value in self.headers.items()},
                source_ip=str(self.client_address[0]),
            )
            status = 200 if payload.get("allowed") is True else 403
            _write_json(self, status, payload)

        def log_message(self, format: str, *args: object) -> None:
            return

    return Handler


def _write_json(
    handler: BaseHTTPRequestHandler,
    status_code: int,
    payload: Mapping[str, object],
) -> None:
    body = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
    handler.send_response(status_code)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def _json_body(body: bytes) -> dict[str, object]:
    if not body:
        return {}
    try:
        parsed = json.loads(body.decode("utf-8"))
    except json.JSONDecodeError:
        return {"raw_body_ref": _redacted_ref(body.decode("utf-8", errors="ignore"), "body")}
    return parsed if isinstance(parsed, dict) else {"value": parsed}


def _blocked_session(
    reason: QmtSessionBlockedReason,
    runtime_status: str,
    config: QmtRuntimeConfig,
) -> QmtSessionSnapshot:
    return QmtSessionSnapshot(
        state=QmtSessionState.BLOCKED,
        ready=False,
        blocked_reason=reason,
        credential_ref="[REDACTED]" if config.account_id else "",
        runtime_status=runtime_status,
    )


def _call_if_exists(target: object, name: str, *args: object) -> object:
    method = getattr(target, name, None)
    if method is None:
        return None
    return method(*args)


def _activate_xtquant_account(trader: object, account: object) -> object:
    """兼容不同 XtQuant 版本：旧版可能有 login，新版常见为 subscribe。"""

    login_method = getattr(trader, "login", None)
    if login_method is not None:
        return login_method(account)
    subscribe_method = getattr(trader, "subscribe", None)
    if subscribe_method is not None:
        return subscribe_method(account)
    return None


def _looks_successful(value: object) -> bool:
    if value in (None, True, 0):
        return True
    if isinstance(value, Mapping):
        code = value.get("error_id", value.get("code", value.get("status", 0)))
        return code in (0, "0", "success", "ok", True)
    return False


def _as_list(value: object) -> list[object]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return [value]


def _position_to_mapping(position: object) -> dict[str, object]:
    if isinstance(position, Mapping):
        return {str(key): value for key, value in position.items()}
    fields = (
        "account_id",
        "stock_code",
        "volume",
        "can_use_volume",
        "market_value",
        "direction",
        "open_price",
    )
    return {
        field: getattr(position, field)
        for field in fields
        if hasattr(position, field)
    }


def _elapsed_ms(started: float) -> int:
    return int((time.monotonic() - started) * 1000)


def _redacted_ref(value: object, label: str) -> str:
    text = str(value or "")
    if not text:
        return ""
    return f"{label}_ref:{stable_qmt_auth_hash(text)[:12]}"
