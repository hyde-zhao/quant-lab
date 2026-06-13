"""CR020-S03 Linux C 端 Typer validation CLI 合同。

本模块只提供配对 / 诊断 / smoke / CP7 验收入口；业务运行时仍是
`QmtClient`。Typer 缺失时 fail-closed，不回退为其他 CLI runtime。
"""

from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
from dataclasses import asdict, dataclass, is_dataclass
from enum import Enum
import json
import sys
from typing import Callable, Mapping, Sequence, TextIO

from trading.qmt_client import (
    DEFAULT_REDACTION_LABEL,
    QmtClient,
    QmtClientConfig,
    QmtEndpointCategory,
    QmtRequest,
    QmtResponseStatus,
    collect_qmt_client_safety_counters,
)
from trading.qmt_transport import REST_GATEWAY_DEFAULT_TIMEOUT_SECONDS


ClientFactory = Callable[..., object]

EXIT_OK = 0
EXIT_VALIDATION = 2
EXIT_BLOCKED = 3
EXIT_AUTH = 4
EXIT_TRANSPORT = 5

TYPER_DEPENDENCY_MISSING = "typer_dependency_missing"


@dataclass(frozen=True, slots=True)
class QmtClientCliCommand:
    """C 端 CLI 命令矩阵；用于静态测试和 Typer adapter 生成。"""

    name: str
    client_method: str
    description: str
    validation_only: bool = True

    def to_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "client_method": self.client_method,
            "description": self.description,
            "validation_only": self.validation_only,
        }


@dataclass(frozen=True, slots=True)
class QmtClientCliOptions:
    """命令参数对象；不读取 `.env` 或任何凭据文件。"""

    base_url: str = ""
    run_id: str = "qmt-client-cli-fixture-run"
    stage: str = "shadow"
    mode: str = "dry_run"
    request_id: str = ""
    authorization_ref: str = ""
    redaction_label: str = DEFAULT_REDACTION_LABEL
    timeout_seconds: int = REST_GATEWAY_DEFAULT_TIMEOUT_SECONDS
    output: str = "json"


@dataclass(frozen=True, slots=True)
class QmtClientCliDependencyBlocked:
    """Typer 缺失时的结构化 fail-closed 结果。"""

    reason_code: str = TYPER_DEPENDENCY_MISSING
    message: str = "Typer 依赖未安装；CR020 client CLI 已阻断"

    def to_dict(self) -> dict[str, object]:
        return {
            "status": QmtResponseStatus.BLOCKED.value,
            "reason_code": self.reason_code,
            "message": self.message,
            "payload": {"operation_authorized": False, "real_operation": False},
            "counters": collect_qmt_client_safety_counters(),
        }


def build_qmt_client_cli_command_matrix() -> tuple[QmtClientCliCommand, ...]:
    """返回 C 端 validation CLI 的命令矩阵，不实例化 Typer。"""

    return (
        QmtClientCliCommand("health", "health", "gateway health smoke 验收"),
        QmtClientCliCommand("capabilities", "capabilities", "gateway capability smoke 验收"),
        QmtClientCliCommand("diagnostics", "diagnostics", "client diagnostics 摘要"),
        QmtClientCliCommand("pairing-status", "diagnostics", "pairing status 验收"),
        QmtClientCliCommand("validate-pairing", "diagnostics", "pairing 验收"),
        QmtClientCliCommand("query-positions", "query_positions", "positions 只读 smoke 验收"),
        QmtClientCliCommand(
            "validate-query-positions",
            "query_positions",
            "positions request 验收",
        ),
    )


def execute_qmt_client_cli_command(
    command: str,
    options: QmtClientCliOptions | None = None,
    *,
    client_factory: ClientFactory = QmtClient,
) -> object:
    """执行单个命令回调；所有业务语义均委托给 `QmtClient`。"""

    current = options or QmtClientCliOptions()
    client = _build_client(client_factory, current)
    if command == "health":
        return client.health(
            run_id=current.run_id,
            stage=current.stage,
            request_id=current.request_id,
            timeout_seconds=current.timeout_seconds,
        )
    if command == "capabilities":
        return client.capabilities(
            run_id=current.run_id,
            stage=current.stage,
            request_id=current.request_id,
            timeout_seconds=current.timeout_seconds,
        )
    if command in {"diagnostics", "pairing-status", "validate-pairing"}:
        return client.diagnostics(
            run_id=current.run_id,
            stage=current.stage,
            request_id=current.request_id,
            timeout_seconds=current.timeout_seconds,
        )
    if command in {"query-positions", "validate-query-positions"}:
        request = QmtRequest(
            run_id=current.run_id,
            endpoint=QmtEndpointCategory.POSITIONS,
            stage=current.stage,
            mode=current.mode or "live_readonly",
            authorization_ref=current.authorization_ref,
            redaction_label=current.redaction_label,
            request_id=current.request_id,
            payload={"validation_only": command == "validate-query-positions"},
            timeout_seconds=current.timeout_seconds,
        )
        return client.query_positions(request)
    return {
        "status": QmtResponseStatus.VALIDATION_ERROR.value,
        "reason_code": "unknown_command",
        "message": f"未知命令: {command}",
    }


def create_qmt_client_typer_app(
    *,
    client_factory: ClientFactory = QmtClient,
) -> object:
    """创建 Typer app；Typer 缺失时返回结构化 blocked 对象。"""

    try:
        import typer
    except ImportError:
        return QmtClientCliDependencyBlocked()

    app = typer.Typer(no_args_is_help=True)

    def emit(command: str, options: QmtClientCliOptions) -> None:
        response = execute_qmt_client_cli_command(
            command,
            options,
            client_factory=client_factory,
        )
        response_dict = _response_to_dict(response)
        typer.echo(_format_response(response_dict, options.output))
        raise typer.Exit(_exit_code(response_dict))

    @app.command("health")
    def health(
        base_url: str = "",
        run_id: str = "qmt-client-health",
        stage: str = "shadow",
        request_id: str = "",
        timeout_seconds: int = REST_GATEWAY_DEFAULT_TIMEOUT_SECONDS,
        output: str = "json",
    ) -> None:
        emit(
            "health",
            QmtClientCliOptions(
                base_url=base_url,
                run_id=run_id,
                stage=stage,
                request_id=request_id,
                timeout_seconds=timeout_seconds,
                output=output,
            ),
        )

    @app.command("capabilities")
    def capabilities(
        base_url: str = "",
        run_id: str = "qmt-client-capabilities",
        stage: str = "shadow",
        request_id: str = "",
        timeout_seconds: int = REST_GATEWAY_DEFAULT_TIMEOUT_SECONDS,
        output: str = "json",
    ) -> None:
        emit(
            "capabilities",
            QmtClientCliOptions(
                base_url=base_url,
                run_id=run_id,
                stage=stage,
                request_id=request_id,
                timeout_seconds=timeout_seconds,
                output=output,
            ),
        )

    @app.command("diagnostics")
    def diagnostics(
        base_url: str = "",
        run_id: str = "qmt-client-diagnostics",
        stage: str = "shadow",
        request_id: str = "",
        timeout_seconds: int = REST_GATEWAY_DEFAULT_TIMEOUT_SECONDS,
        output: str = "json",
    ) -> None:
        emit(
            "diagnostics",
            QmtClientCliOptions(
                base_url=base_url,
                run_id=run_id,
                stage=stage,
                request_id=request_id,
                timeout_seconds=timeout_seconds,
                output=output,
            ),
        )

    @app.command("pairing-status")
    def pairing_status(
        base_url: str = "",
        run_id: str = "qmt-client-pairing-status",
        stage: str = "shadow",
        request_id: str = "",
        timeout_seconds: int = REST_GATEWAY_DEFAULT_TIMEOUT_SECONDS,
        output: str = "json",
    ) -> None:
        emit(
            "pairing-status",
            QmtClientCliOptions(
                base_url=base_url,
                run_id=run_id,
                stage=stage,
                request_id=request_id,
                timeout_seconds=timeout_seconds,
                output=output,
            ),
        )

    @app.command("validate-pairing")
    def validate_pairing(
        base_url: str = "",
        run_id: str = "qmt-client-validate-pairing",
        stage: str = "shadow",
        request_id: str = "",
        timeout_seconds: int = REST_GATEWAY_DEFAULT_TIMEOUT_SECONDS,
        output: str = "json",
    ) -> None:
        emit(
            "validate-pairing",
            QmtClientCliOptions(
                base_url=base_url,
                run_id=run_id,
                stage=stage,
                request_id=request_id,
                timeout_seconds=timeout_seconds,
                output=output,
            ),
        )

    @app.command("query-positions")
    def query_positions(
        base_url: str = "",
        run_id: str = "qmt-client-query-positions",
        stage: str = "shadow",
        mode: str = "live_readonly",
        request_id: str = "",
        authorization_ref: str = "",
        redaction_label: str = DEFAULT_REDACTION_LABEL,
        timeout_seconds: int = REST_GATEWAY_DEFAULT_TIMEOUT_SECONDS,
        output: str = "json",
    ) -> None:
        emit(
            "query-positions",
            QmtClientCliOptions(
                base_url=base_url,
                run_id=run_id,
                stage=stage,
                mode=mode,
                request_id=request_id,
                authorization_ref=authorization_ref,
                redaction_label=redaction_label,
                timeout_seconds=timeout_seconds,
                output=output,
            ),
        )

    @app.command("validate-query-positions")
    def validate_query_positions(
        base_url: str = "",
        run_id: str = "qmt-client-validate-query-positions",
        stage: str = "shadow",
        mode: str = "live_readonly",
        request_id: str = "",
        authorization_ref: str = "",
        redaction_label: str = DEFAULT_REDACTION_LABEL,
        timeout_seconds: int = REST_GATEWAY_DEFAULT_TIMEOUT_SECONDS,
        output: str = "json",
    ) -> None:
        emit(
            "validate-query-positions",
            QmtClientCliOptions(
                base_url=base_url,
                run_id=run_id,
                stage=stage,
                mode=mode,
                request_id=request_id,
                authorization_ref=authorization_ref,
                redaction_label=redaction_label,
                timeout_seconds=timeout_seconds,
                output=output,
            ),
        )

    return app


def run_qmt_client_cli(
    argv: Sequence[str] | None = None,
    client_factory: ClientFactory = QmtClient,
    *,
    output_stream: TextIO | None = None,
    error_stream: TextIO | None = None,
) -> int:
    """运行 Typer CLI；Typer 不存在时输出 blocked JSON 并返回阻断码。"""

    out = output_stream or sys.stdout
    err = error_stream or sys.stderr
    app = create_qmt_client_typer_app(client_factory=client_factory)
    if isinstance(app, QmtClientCliDependencyBlocked):
        response = app.to_dict()
        _write_response(response, "json", out)
        return _exit_code(response)

    try:
        import typer

        with redirect_stdout(out), redirect_stderr(err):
            app(prog_name="qmt-client-cli", args=list(argv) if argv is not None else None)
        return EXIT_OK
    except typer.Exit as exc:
        return int(exc.exit_code or 0)
    except SystemExit as exc:
        return int(exc.code or 0)


def _build_client(client_factory: ClientFactory, options: QmtClientCliOptions) -> object:
    config = QmtClientConfig(
        base_url=options.base_url,
        default_timeout_seconds=options.timeout_seconds,
        default_stage=options.stage,
        default_mode=options.mode,
        redaction_label=options.redaction_label,
    )
    if client_factory is QmtClient:
        return QmtClient(config=config)
    try:
        return client_factory(config)
    except TypeError:
        return client_factory()


def _write_response(
    response: Mapping[str, object],
    output_format: str,
    output_stream: TextIO,
) -> None:
    output_stream.write(_format_response(response, output_format))
    output_stream.write("\n")


def _format_response(response: Mapping[str, object], output_format: str) -> str:
    if output_format == "text":
        return (
            f"{response.get('status')} "
            f"reason={response.get('reason_code', '')} "
            f"message={response.get('message', '')}"
        )
    return json.dumps(response, ensure_ascii=False, sort_keys=True)


def _response_to_dict(response: object) -> Mapping[str, object]:
    if hasattr(response, "to_dict"):
        return response.to_dict()  # type: ignore[no-any-return]
    if is_dataclass(response):
        return asdict(response)  # type: ignore[arg-type]
    if isinstance(response, Mapping):
        return response
    return {"status": str(response)}


def _exit_code(response: Mapping[str, object]) -> int:
    status = _value(response.get("status", ""))
    if status == QmtResponseStatus.OK.value:
        return EXIT_OK
    if status == QmtResponseStatus.VALIDATION_ERROR.value:
        return EXIT_VALIDATION
    if status == QmtResponseStatus.AUTH_ERROR.value:
        return EXIT_AUTH
    if status == QmtResponseStatus.TRANSPORT_ERROR.value:
        return EXIT_TRANSPORT
    if status == QmtResponseStatus.BLOCKED.value:
        return EXIT_BLOCKED
    return EXIT_VALIDATION


def _value(value: object) -> str:
    return value.value if isinstance(value, Enum) else str(value)


if __name__ == "__main__":
    raise SystemExit(run_qmt_client_cli())
