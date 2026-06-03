"""CR019-S03 的 QMT thin CLI。

CLI 只解析参数、调用同一 QMT client、格式化输出并返回退出码；不复制
client 的 gate、auth、transport 或业务判定。
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, is_dataclass
from enum import Enum
from typing import Callable, Mapping, Sequence, TextIO

from trading.qmt_client import (
    DEFAULT_REDACTION_LABEL,
    QmtClient,
    QmtEndpointCategory,
    QmtRequest,
    QmtResponseStatus,
)


ClientFactory = Callable[[], object]

EXIT_OK = 0
EXIT_VALIDATION = 2
EXIT_BLOCKED = 3
EXIT_AUTH = 4
EXIT_TRANSPORT = 5


def run_qmt_cli(
    argv: Sequence[str] | None = None,
    client_factory: ClientFactory = QmtClient,
    *,
    output_stream: TextIO | None = None,
    error_stream: TextIO | None = None,
) -> int:
    """运行 QMT thin CLI 并返回进程退出码。"""

    out = output_stream or sys.stdout
    err = error_stream or sys.stderr
    parser = _build_parser()
    try:
        args = parser.parse_args(list(argv) if argv is not None else None)
    except _CliArgumentError as exc:
        print(str(exc), file=err)
        return EXIT_VALIDATION

    client = client_factory()
    try:
        response = _call_client(client, args)
    except AttributeError as exc:
        print(f"client contract missing method: {exc}", file=err)
        return EXIT_VALIDATION

    response_dict = _response_to_dict(response)
    _write_response(response_dict, args.output, out)
    return _exit_code(response_dict)


def _build_parser() -> argparse.ArgumentParser:
    parser = _ArgumentParser(prog="qmt-cli")
    parser.add_argument(
        "--output",
        choices=("json", "text"),
        default="json",
        help="output format",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    for command in (
        "health",
        "capabilities",
        "validate-intent",
        "query-market",
        "query-account",
        "submit-order-intent",
        "reconcile",
        "kill-switch",
    ):
        _add_common_args(subparsers.add_parser(command))

    submit = subparsers.choices["submit-order-intent"]
    submit.add_argument(
        "--endpoint",
        choices=(
            QmtEndpointCategory.SIMULATION_SUBMIT.value,
            QmtEndpointCategory.SIMULATION_CANCEL.value,
            QmtEndpointCategory.LIVE_SUBMIT.value,
            QmtEndpointCategory.LIVE_CANCEL.value,
        ),
        default=QmtEndpointCategory.SIMULATION_SUBMIT.value,
    )
    return parser


def _add_common_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--run-id", default="qmt-cli-fixture-run")
    parser.add_argument("--stage", default="shadow")
    parser.add_argument("--mode", default="dry_run")
    parser.add_argument("--intent-id", default="")
    parser.add_argument("--authorization-ref", default="")
    parser.add_argument("--redaction-label", default=DEFAULT_REDACTION_LABEL)
    parser.add_argument("--request-id", default="")
    parser.add_argument("--strategy-id", default="")
    parser.add_argument("--operator-ref", default="")
    parser.add_argument("--timeout-seconds", type=int, default=3)


def _call_client(client: object, args: argparse.Namespace) -> object:
    command = args.command
    if command == "health":
        return client.health(
            run_id=args.run_id,
            stage=args.stage,
            timeout_seconds=args.timeout_seconds,
        )
    if command == "capabilities":
        return client.capabilities(run_id=args.run_id, stage=args.stage)

    request = _request_from_args(args, _endpoint_for_command(command, args))
    if command == "validate-intent":
        return client.validate_intent(request)
    if command == "query-market":
        return client.query_market(request)
    if command == "query-account":
        return client.query_account_like(QmtEndpointCategory.ACCOUNT_QUERY, request)
    if command == "submit-order-intent":
        return client.submit_order_intent(request, endpoint=request.endpoint)
    if command == "reconcile":
        return client.reconcile(request)
    if command == "kill-switch":
        return client.kill_switch(request)
    raise AttributeError(command)


def _endpoint_for_command(
    command: str,
    args: argparse.Namespace,
) -> QmtEndpointCategory:
    if command == "validate-intent":
        return QmtEndpointCategory.VALIDATE_INTENT
    if command == "query-market":
        return QmtEndpointCategory.MARKET_QUERY
    if command == "query-account":
        return QmtEndpointCategory.ACCOUNT_QUERY
    if command == "submit-order-intent":
        return QmtEndpointCategory(args.endpoint)
    if command == "reconcile":
        return QmtEndpointCategory.RECONCILIATION
    if command == "kill-switch":
        return QmtEndpointCategory.KILL_SWITCH
    return QmtEndpointCategory.HEALTH


def _request_from_args(
    args: argparse.Namespace,
    endpoint: QmtEndpointCategory,
) -> QmtRequest:
    return QmtRequest(
        run_id=args.run_id,
        endpoint=endpoint,
        stage=args.stage,
        mode=args.mode,
        intent_id=args.intent_id,
        authorization_ref=args.authorization_ref,
        redaction_label=args.redaction_label,
        request_id=args.request_id,
        strategy_id=args.strategy_id,
        operator_ref=args.operator_ref,
        timeout_seconds=args.timeout_seconds,
    )


def _write_response(
    response: Mapping[str, object],
    output_format: str,
    output_stream: TextIO,
) -> None:
    if output_format == "text":
        reason = str(response.get("reason_code", ""))
        message = str(response.get("message", ""))
        endpoint = str(response.get("endpoint", ""))
        print(
            f"{response.get('status')} endpoint={endpoint} reason={reason} message={message}",
            file=output_stream,
        )
        return
    json.dump(response, output_stream, ensure_ascii=False, sort_keys=True)
    output_stream.write("\n")


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


def _response_to_dict(response: object) -> Mapping[str, object]:
    if hasattr(response, "to_dict"):
        return response.to_dict()  # type: ignore[no-any-return]
    if is_dataclass(response):
        return asdict(response)  # type: ignore[arg-type]
    if isinstance(response, Mapping):
        return response
    return {"status": str(response)}


def _value(value: object) -> str:
    return value.value if isinstance(value, Enum) else str(value)


class _CliArgumentError(Exception):
    pass


class _ArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise _CliArgumentError(message)


if __name__ == "__main__":
    raise SystemExit(run_qmt_cli())
