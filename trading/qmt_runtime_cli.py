"""CR020 手动实机验证 CLI。

Windows S 端使用 `serve` / `server-diagnostics`，Linux C 端使用
`query-positions` / `client-diagnostics`。Typer 缺失时 fail-closed。
"""

from __future__ import annotations

import json
import sys
from typing import Sequence, TextIO

from trading.qmt_client import QmtClient, QmtClientConfig
from trading.qmt_runtime import (
    RUNTIME_SCHEMA_VERSION,
    StdlibQmtRestTransport,
    build_runtime_config,
    build_runtime_hmac_provider,
    create_gateway_runtime,
    load_runtime_env,
    serve_gateway_runtime,
)


TYPER_MISSING_REASON = "typer_dependency_missing"


def run_qmt_runtime_cli(
    argv: Sequence[str] | None = None,
    *,
    output_stream: TextIO | None = None,
) -> int:
    """运行 Typer CLI；仅由 `python -m trading.qmt_runtime_cli` 调用。"""

    out = output_stream or sys.stdout
    try:
        import typer
    except ImportError:
        _emit(
            {
                "schema_version": RUNTIME_SCHEMA_VERSION,
                "status": "blocked",
                "reason_code": TYPER_MISSING_REASON,
                "message": "Typer 未安装；请用 `uv run --with typer` 手动运行",
            },
            out,
        )
        return 3

    app = typer.Typer(no_args_is_help=True)

    @app.command("server-diagnostics")
    def server_diagnostics(
        env_file: str = ".env",
        host: str = "",
        port: int = 0,
        runtime_authorization_ref: str = "",
    ) -> None:
        env = load_runtime_env(env_file)
        config = build_runtime_config(
            env,
            host=host,
            port=port or None,
            runtime_authorization_ref=runtime_authorization_ref,
        )
        _typer_emit(
            typer,
            {
                "schema_version": RUNTIME_SCHEMA_VERSION,
                "status": "ok",
                "config": config.to_public_dict(),
                "secrets_redacted": True,
            },
        )

    @app.command("serve")
    def serve(
        env_file: str = ".env",
        host: str = "",
        port: int = 0,
        runtime_authorization_ref: str = "",
    ) -> None:
        env = load_runtime_env(env_file)
        config = build_runtime_config(
            env,
            host=host,
            port=port or None,
            runtime_authorization_ref=runtime_authorization_ref,
        )
        runtime = create_gateway_runtime(config)
        typer.echo(
            json.dumps(
                {
                    "schema_version": RUNTIME_SCHEMA_VERSION,
                    "status": "starting",
                    "health": runtime.health_payload(),
                },
                ensure_ascii=False,
                sort_keys=True,
            )
        )
        serve_gateway_runtime(runtime)

    @app.command("client-diagnostics")
    def client_diagnostics(
        env_file: str = ".env",
        base_url: str = "",
        host: str = "",
        port: int = 0,
    ) -> None:
        env = load_runtime_env(env_file)
        config = build_runtime_config(env, host=host, port=port or None)
        resolved_base_url = base_url or config.base_url
        _typer_emit(
            typer,
            {
                "schema_version": RUNTIME_SCHEMA_VERSION,
                "status": "ok",
                "base_url": resolved_base_url,
                "client_id_hash": config.to_public_dict()["client_id_hash"],
                "client_secret_ref": "[REDACTED]" if config.client_secret else "",
            },
        )

    @app.command("query-positions")
    def query_positions(
        env_file: str = ".env",
        base_url: str = "",
        host: str = "",
        port: int = 0,
        run_id: str = "manual-cr020-query-positions",
        request_id: str = "manual-cr020-query-positions-001",
        timeout_seconds: int = 10,
    ) -> None:
        env = load_runtime_env(env_file)
        config = build_runtime_config(env, host=host, port=port or None)
        resolved_base_url = base_url or config.base_url
        client = QmtClient(
            config=QmtClientConfig(
                base_url=resolved_base_url,
                default_stage="manual_cp7",
                default_mode="live_readonly",
                default_timeout_seconds=timeout_seconds,
            ),
            transport=StdlibQmtRestTransport(),
            auth_header_provider=build_runtime_hmac_provider(config),
        )
        response = client.query_positions(
            run_id=run_id,
            request_id=request_id,
            authorization_ref=config.runtime_authorization_ref,
            timeout_seconds=timeout_seconds,
        )
        _typer_emit(typer, response.to_dict())

    try:
        app(prog_name="qmt-runtime-cli", args=list(argv) if argv is not None else None)
    except typer.Exit as exc:
        return int(exc.exit_code or 0)
    except SystemExit as exc:
        return int(exc.code or 0)
    return 0


def _typer_emit(typer_module: object, payload: object) -> None:
    getattr(typer_module, "echo")(
        json.dumps(_to_dict(payload), ensure_ascii=False, sort_keys=True)
    )


def _emit(payload: object, stream: TextIO) -> None:
    stream.write(json.dumps(_to_dict(payload), ensure_ascii=False, sort_keys=True))
    stream.write("\n")


def _to_dict(payload: object) -> object:
    if hasattr(payload, "to_dict"):
        return payload.to_dict()  # type: ignore[no-any-return]
    return payload


if __name__ == "__main__":
    raise SystemExit(run_qmt_runtime_cli())
