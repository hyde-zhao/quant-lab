"""AkShare adapter fail-fast 边界。"""

from __future__ import annotations

from .protocol import AdapterConfig, ConnectorError, ConnectorRequest


class AkShareAdapter:
    source = "akshare"

    def __init__(self, config: AdapterConfig | None = None) -> None:
        self.config = config or AdapterConfig(source=self.source)

    def fetch(self, request: ConnectorRequest) -> ConnectorError:
        if not self.config.enabled:
            return ConnectorError(
                "source_disabled",
                "akshare source is disabled by default",
                False,
                request.source,
                request.interface,
            )
        if request.interface not in self.config.allow_interfaces:
            return ConnectorError(
                "interface_not_allowed",
                "akshare interface is not allowlisted",
                False,
                request.source,
                request.interface,
            )
        return ConnectorError(
            "source_disabled",
            "akshare real network fetch is not enabled in default path",
            False,
            request.source,
            request.interface,
        )


__all__ = ["AkShareAdapter"]
