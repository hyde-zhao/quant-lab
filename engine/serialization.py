"""Shared serialization and light validation helpers for research contracts."""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
from datetime import date, datetime
from enum import Enum
from pathlib import Path
import math
from typing import Any, Mapping, Sequence


def json_safe(value: Any) -> Any:
    """Return a JSON-compatible representation for common contract objects."""

    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value):
        return json_safe(asdict(value))
    if isinstance(value, Mapping):
        return {str(key): json_safe(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return tuple(json_safe(item) for item in value)
    if isinstance(value, list):
        return [json_safe(item) for item in value]
    if isinstance(value, set):
        return sorted(json_safe(item) for item in value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Path):
        return str(value)
    return value


def as_mapping(value: Any, *, none_as_empty: bool = False) -> dict[str, Any] | None:
    """Coerce dataclasses, mapping-like contracts and ``to_dict`` objects."""

    if value is None:
        return {} if none_as_empty else None
    if isinstance(value, Mapping):
        return json_safe(dict(value))
    to_dict = getattr(value, "to_dict", None)
    if callable(to_dict):
        return as_mapping(to_dict(), none_as_empty=none_as_empty)
    if is_dataclass(value):
        return json_safe(asdict(value))
    if hasattr(value, "__dict__"):
        return json_safe(vars(value))
    slots = getattr(type(value), "__slots__", ())
    if slots:
        return json_safe({slot: getattr(value, slot) for slot in slots if hasattr(value, slot)})
    return {} if none_as_empty else None


def is_blank(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return value.strip() == ""
    if isinstance(value, Mapping):
        return len(value) == 0
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return len(value) == 0
    return False


def safe_float(value: Any) -> float | None:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    if result != result or math.isinf(result):
        return None
    return result


def normalise_permission_counters(
    value: Any,
    allowed_fields: Sequence[str],
) -> dict[str, int]:
    data = as_mapping(value, none_as_empty=True) or {}
    counters: dict[str, int] = {}
    for key in allowed_fields:
        raw_value = data.get(key, 0)
        try:
            counters[key] = int(raw_value)
        except (TypeError, ValueError):
            counters[key] = 1
    return counters
