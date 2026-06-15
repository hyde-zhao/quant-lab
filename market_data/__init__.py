"""可迁移市场数据组件。"""

from .contracts import (
    CANONICAL_PRICES_REQUIRED_COLUMNS,
    CONNECTOR_ERROR_TYPES,
    MANIFEST_REQUIRED_FIELDS,
    SCHEMA_VERSION,
)
from .lake_layout import LakeLayout
from .source_registry import resolve_interface, resolve_source

__version__ = "0.1.0"

__all__ = [
    "__version__",
    "SCHEMA_VERSION",
    "CANONICAL_PRICES_REQUIRED_COLUMNS",
    "MANIFEST_REQUIRED_FIELDS",
    "CONNECTOR_ERROR_TYPES",
    "LakeLayout",
    "resolve_source",
    "resolve_interface",
]
