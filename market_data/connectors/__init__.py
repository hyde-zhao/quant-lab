"""Connector 轻量导出。"""

from .fake import FakeConnector
from .jqdata import JQDataAdapter
from .protocol import (
    AdapterConfig,
    ConnectorError,
    ConnectorProtocol,
    ConnectorRequest,
    ConnectorResult,
)

__all__ = [
    "AdapterConfig",
    "ConnectorError",
    "ConnectorProtocol",
    "ConnectorRequest",
    "ConnectorResult",
    "FakeConnector",
    "JQDataAdapter",
]
