"""Connector 协议与结构化结果。"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Protocol


@dataclass(frozen=True, slots=True)
class ConnectorRequest:
    source: str
    interface: str
    params: Mapping[str, Any]
    run_id: str
    batch_id: str
    params_hash: str = ""


@dataclass(frozen=True, slots=True)
class ConnectorError:
    error_type: str
    error_message: str
    retryable: bool
    source: str
    interface: str

    @property
    def safe_message(self) -> str:
        return self.error_message

    def to_dict(self) -> dict[str, Any]:
        return {
            "error_type": self.error_type,
            "error_message": self.error_message,
            "retryable": self.retryable,
            "source": self.source,
            "interface": self.interface,
        }


@dataclass(frozen=True, slots=True)
class ConnectorResult:
    source: str
    interface: str
    rows: list[dict[str, Any]]
    metadata: dict[str, Any] = field(default_factory=dict)
    partial_errors: list[ConnectorError] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class AdapterConfig:
    source: str
    enabled: bool = False
    allow_interfaces: tuple[str, ...] = ()
    credential_env_vars: tuple[str, ...] = ()


class ConnectorProtocol(Protocol):
    source: str

    def fetch(self, request: ConnectorRequest) -> ConnectorResult | ConnectorError:
        """获取一个批次的原始数据。"""


__all__ = [
    "AdapterConfig",
    "ConnectorError",
    "ConnectorProtocol",
    "ConnectorRequest",
    "ConnectorResult",
]
