"""本地 CLI 最小诊断日志。"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import json
import logging
import sys
import time
from typing import Any
from uuid import uuid4


LOGGER_NAME = "local_backtest.cli_diag"


def _logger() -> logging.Logger:
    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(logging.Formatter("%(message)s"))
        logger.addHandler(handler)
    return logger


@dataclass(slots=True)
class DiagnosticContext:
    module: str
    story_id: str
    params_summary: dict[str, Any] = field(default_factory=dict)
    run_id: str = ""
    started_at: float = field(default_factory=time.monotonic)

    def __post_init__(self) -> None:
        if not self.run_id:
            self.run_id = f"{self.module}-{uuid4().hex[:12]}"

    def start(self) -> None:
        emit_diagnostic_event(
            self.module,
            self.story_id,
            "start",
            "started",
            run_id=self.run_id,
            params_summary=self.params_summary,
            elapsed_seconds=0.0,
            level=logging.INFO,
        )

    def end(self, status: str = "success", **extra: Any) -> None:
        emit_diagnostic_event(
            self.module,
            self.story_id,
            "end",
            status,
            run_id=self.run_id,
            params_summary={**self.params_summary, **extra},
            elapsed_seconds=time.monotonic() - self.started_at,
            level=logging.INFO,
        )

    def warning(self, status: str, **extra: Any) -> None:
        emit_diagnostic_event(
            self.module,
            self.story_id,
            status,
            status,
            run_id=self.run_id,
            params_summary={**self.params_summary, **extra},
            elapsed_seconds=time.monotonic() - self.started_at,
            level=logging.WARNING,
        )

    def error(self, exc: Exception, status: str = "structured_error", **extra: Any) -> None:
        emit_diagnostic_event(
            self.module,
            self.story_id,
            "structured_error",
            status,
            run_id=self.run_id,
            params_summary={**self.params_summary, **extra},
            elapsed_seconds=time.monotonic() - self.started_at,
            structured_error={
                "type": type(exc).__name__,
                "message": str(exc),
            },
            level=logging.ERROR,
        )


def start_diagnostic(
    module: str,
    story_id: str,
    params_summary: dict[str, Any] | None = None,
    *,
    run_id: str = "",
) -> DiagnosticContext:
    context = DiagnosticContext(
        module=module,
        story_id=story_id,
        params_summary=dict(params_summary or {}),
        run_id=run_id,
    )
    context.start()
    return context


def emit_diagnostic_event(
    module: str,
    story_id: str,
    event_name: str,
    status: str,
    *,
    run_id: str,
    params_summary: dict[str, Any] | None = None,
    elapsed_seconds: float,
    structured_error: dict[str, Any] | None = None,
    level: int = logging.INFO,
) -> None:
    payload: dict[str, Any] = {
        "event_name": event_name,
        "run_id": run_id,
        "module": module,
        "story_id": story_id,
        "status": status,
        "params_summary": _safe_value(params_summary or {}),
        "elapsed_seconds": round(max(float(elapsed_seconds), 0.0), 6),
    }
    if structured_error is not None:
        payload["structured_error"] = _safe_value(structured_error)
    _logger().log(level, json.dumps(payload, ensure_ascii=False, sort_keys=True))


def _safe_value(value: Any) -> Any:
    if isinstance(value, Path):
        return {"path_name": value.name}
    if isinstance(value, dict):
        return {str(key): _safe_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_safe_value(item) for item in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


__all__ = (
    "DiagnosticContext",
    "LOGGER_NAME",
    "emit_diagnostic_event",
    "start_diagnostic",
)
