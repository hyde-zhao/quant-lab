"""CR020 Windows QMT gateway CLI 离线合同。

本模块只定义 S 端命令矩阵、结构化输出和可选 Typer adapter。
Typer 缺失时返回 `typer_dependency_missing`；模块导入本身不得失败。
"""

from __future__ import annotations

from dataclasses import dataclass, field
import json
from typing import Callable, Mapping

from trading.qmt_gateway_config import (
    CR020_GATEWAY_RUNTIME_SCHEMA_VERSION,
    GatewayRuntimeFlags,
    build_gateway_config,
    build_gateway_runtime_flags,
    collect_gateway_runtime_counters,
)
from trading.qmt_gateway_service import (
    build_gateway_runtime_diagnostics,
    build_gateway_runtime_health_summary,
    plan_gateway_runtime_action,
)


GATEWAY_CLI_SCHEMA_VERSION = "cr020-s01-gateway-cli-v1"
TYPER_DEPENDENCY_MISSING_REASON = "typer_dependency_missing"


@dataclass(frozen=True, slots=True)
class GatewayCliCommandSpec:
    """S 端 Typer CLI 命令合同；不执行真实 runtime。"""

    command: str
    options: tuple[str, ...]
    requires_runtime_authorization: bool
    dry_run_only: bool
    forbidden_side_effects: tuple[str, ...]
    description: str
    schema_version: str = GATEWAY_CLI_SCHEMA_VERSION

    def to_dict(self) -> dict[str, object]:
        return {
            "command": self.command,
            "options": list(self.options),
            "requires_runtime_authorization": self.requires_runtime_authorization,
            "dry_run_only": self.dry_run_only,
            "forbidden_side_effects": list(self.forbidden_side_effects),
            "description": self.description,
            "schema_version": self.schema_version,
        }


@dataclass(frozen=True, slots=True)
class GatewayTyperAdapterResult:
    """Typer adapter 构造结果；缺依赖时以 blocked 结构返回。"""

    available: bool
    app: object | None = None
    error_code: str = ""
    commands: tuple[GatewayCliCommandSpec, ...] = ()
    counters: Mapping[str, int] = field(default_factory=collect_gateway_runtime_counters)
    schema_version: str = GATEWAY_CLI_SCHEMA_VERSION

    @property
    def blocked(self) -> bool:
        return not self.available

    def to_dict(self) -> dict[str, object]:
        return {
            "available": self.available,
            "blocked": self.blocked,
            "error_code": self.error_code,
            "commands": [command.to_dict() for command in self.commands],
            "command_count": len(self.commands),
            "counters": dict(self.counters),
            "schema_version": self.schema_version,
        }


def build_gateway_cli_command_matrix(
    flags: GatewayRuntimeFlags | Mapping[str, object] | None = None,
) -> tuple[GatewayCliCommandSpec, ...]:
    """构造 S 端命令矩阵；不依赖 Typer 安装。"""

    current_flags = build_gateway_runtime_flags(flags)
    common_options = (
        "--config",
        "--host",
        "--port",
        "--runtime-authorization-ref",
        "--dry-run",
    )
    forbidden = (
        "service_start",
        "port_bind",
        "credential_read",
        "qmt_api_call",
        "real_order",
        "account_write",
        "provider_fetch",
        "lake_write",
        "publish",
    )
    return (
        GatewayCliCommandSpec(
            command="admission",
            options=common_options,
            requires_runtime_authorization=False,
            dry_run_only=True,
            forbidden_side_effects=forbidden,
            description="输出 gateway runtime admission 状态。",
        ),
        GatewayCliCommandSpec(
            command="plan",
            options=common_options,
            requires_runtime_authorization=False,
            dry_run_only=True,
            forbidden_side_effects=forbidden,
            description="输出 gateway lifecycle / runtime 计划。",
        ),
        GatewayCliCommandSpec(
            command="serve",
            options=common_options,
            requires_runtime_authorization=True,
            dry_run_only=current_flags.dry_run_only,
            forbidden_side_effects=forbidden,
            description="在运行授权缺失时返回 blocked，不启动服务。",
        ),
        GatewayCliCommandSpec(
            command="stop",
            options=("--runtime-authorization-ref", "--dry-run"),
            requires_runtime_authorization=True,
            dry_run_only=True,
            forbidden_side_effects=("process_signal", "service_stop_without_auth"),
            description="输出 stop 计划；默认不发送进程信号。",
        ),
        GatewayCliCommandSpec(
            command="health",
            options=("--config", "--runtime-authorization-ref", "--dry-run"),
            requires_runtime_authorization=False,
            dry_run_only=True,
            forbidden_side_effects=("socket_probe", "http_client_call", "qmt_api_call"),
            description="输出 fixture observation health 摘要，不探测网络。",
        ),
        GatewayCliCommandSpec(
            command="diagnostics",
            options=common_options,
            requires_runtime_authorization=False,
            dry_run_only=True,
            forbidden_side_effects=forbidden,
            description="输出脱敏 diagnostics、admission 与 zero counters。",
        ),
    )


def build_gateway_cli_result(
    command: str,
    config: Mapping[str, object] | None = None,
    *,
    flags: GatewayRuntimeFlags | Mapping[str, object] | None = None,
) -> dict[str, object]:
    """按命令名构造 JSON-friendly 结果；不执行真实 runtime。"""

    command_name = command.strip().lower() or "admission"
    current_config = build_gateway_config(config)
    current_flags = build_gateway_runtime_flags(flags)

    if command_name == "health":
        result = build_gateway_runtime_health_summary(
            config=current_config,
            flags=current_flags,
        )
    elif command_name == "diagnostics":
        result = build_gateway_runtime_diagnostics(
            current_config,
            flags=current_flags,
            requested_action="diagnostics",
        )
    else:
        result = plan_gateway_runtime_action(
            command_name,
            current_config,
            flags=current_flags,
        ).to_dict()

    return {
        "schema_version": CR020_GATEWAY_RUNTIME_SCHEMA_VERSION,
        "command": command_name,
        "result": result,
        "counters": collect_gateway_runtime_counters(),
    }


def create_gateway_typer_app(
    command_matrix: tuple[GatewayCliCommandSpec, ...] | None = None,
    *,
    importer: Callable[[str], object] | None = None,
) -> object | GatewayTyperAdapterResult:
    """创建 Typer app；Typer 缺失时 fail-closed。"""

    commands = command_matrix or build_gateway_cli_command_matrix()
    load_module = importer or __import__
    try:
        typer_module = load_module("typer")
    except Exception:
        return GatewayTyperAdapterResult(
            available=False,
            error_code=TYPER_DEPENDENCY_MISSING_REASON,
            commands=commands,
            counters=collect_gateway_runtime_counters(),
        )

    typer_factory = getattr(typer_module, "Typer", None)
    if typer_factory is None:
        return GatewayTyperAdapterResult(
            available=False,
            error_code=TYPER_DEPENDENCY_MISSING_REASON,
            commands=commands,
            counters=collect_gateway_runtime_counters(),
        )

    app = typer_factory(no_args_is_help=True)
    for spec in commands:
        _register_typer_command(app, typer_module, spec)
    return app


def probe_gateway_typer_adapter(
    *,
    importer: Callable[[str], object] | None = None,
) -> GatewayTyperAdapterResult:
    """返回 Typer adapter 可用性摘要；不让 import-time 依赖影响测试。"""

    commands = build_gateway_cli_command_matrix()
    app_or_result = create_gateway_typer_app(commands, importer=importer)
    if isinstance(app_or_result, GatewayTyperAdapterResult):
        return app_or_result
    return GatewayTyperAdapterResult(
        available=True,
        app=app_or_result,
        commands=commands,
        counters=collect_gateway_runtime_counters(),
    )


def _register_typer_command(
    app: object,
    typer_module: object,
    spec: GatewayCliCommandSpec,
) -> None:
    option = getattr(typer_module, "Option")
    echo = getattr(typer_module, "echo")

    def command_callback(
        config_path: str = option("<config-path>", "--config"),
        host: str = option("127.0.0.1", "--host"),
        port: int = option(18765, "--port"),
        runtime_authorization_ref: str = option("", "--runtime-authorization-ref"),
        dry_run: bool = option(True, "--dry-run"),
    ) -> None:
        payload = build_gateway_cli_result(
            spec.command,
            {
                "config_path": config_path,
                "bind_host": host,
                "port": port,
            },
            flags={
                "runtime_authorization_ref": runtime_authorization_ref,
                "dry_run_only": dry_run,
            },
        )
        echo(json.dumps(payload, ensure_ascii=False, sort_keys=True))

    getattr(app, "command")(spec.command)(command_callback)
