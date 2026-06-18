"""CR091 immutable local cache 与 active pointer 只读解析。"""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

import yaml


class StrategyCacheError(ValueError):
    """本地 cache / active pointer fail-closed 错误。"""


@dataclass(frozen=True, slots=True)
class ActivePackagePointer:
    package_id: str
    package_path: Path
    pointer_path: Path
    not_authorization: bool = True


def resolve_active_package(cache_root: str | Path, active_pointer: str | Path) -> ActivePackagePointer:
    root = Path(cache_root).resolve()
    pointer = Path(active_pointer).resolve()
    if not pointer.is_file():
        raise StrategyCacheError("blocked_active_pointer_missing")
    if root not in pointer.parents:
        raise StrategyCacheError("blocked_active_pointer_outside_cache")
    data = _load_pointer(pointer)
    if data.get("not_authorization") is not True:
        raise StrategyCacheError("blocked_not_authorization_missing")
    package_id = str(data.get("package_id") or "")
    rel_path = str(data.get("package_path") or "")
    if not package_id or not rel_path:
        raise StrategyCacheError("blocked_active_pointer_incomplete")
    if rel_path.startswith("/") or ".." in Path(rel_path).parts:
        raise StrategyCacheError("blocked_cache_path_escape")
    package_path = (root / rel_path).resolve()
    if root not in package_path.parents and package_path != root:
        raise StrategyCacheError("blocked_cache_path_escape")
    if not package_path.is_dir():
        raise StrategyCacheError("blocked_active_package_missing")
    if not (package_path / ".immutable").is_file():
        raise StrategyCacheError("blocked_cache_package_not_immutable")
    return ActivePackagePointer(package_id=package_id, package_path=package_path, pointer_path=pointer)


def _load_pointer(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".json":
        value = json.loads(text)
    else:
        value = yaml.safe_load(text)
    if not isinstance(value, dict):
        raise StrategyCacheError("blocked_active_pointer_not_mapping")
    return value
