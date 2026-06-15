"""TickFlow adapter unresolved 边界。"""

from __future__ import annotations

from .protocol import AdapterConfig, ConnectorError, ConnectorRequest


class TickFlowAdapter:
    source = "tickflow"

    def __init__(self, config: AdapterConfig | None = None) -> None:
        self.config = config or AdapterConfig(
            source=self.source,
            credential_env_vars=("TICKFLOW_TOKEN", "TICKFLOW_ENDPOINT"),
        )

    def fetch(self, request: ConnectorRequest) -> ConnectorError:
        return ConnectorError(
            "source_unresolved",
            "tickflow exact API, auth and rate limits are unresolved",
            False,
            request.source,
            request.interface,
        )


__all__ = ["TickFlowAdapter"]
