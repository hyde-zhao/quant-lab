"""数据准备 manifest 的 append-only JSONL 存储。

本模块只处理 manifest 文件读写、记录构造和断点续传查询，不调用 AKShare，
不做 raw 标准化，也不生成质量报告。
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
import json
from pathlib import Path
from typing import Any, Iterable

from engine.contracts import MANIFEST_REQUIRED_FIELDS, MANIFEST_STATUS_VALUES


class ManifestError(Exception):
    """manifest 基础异常。"""


class ManifestFormatError(ManifestError):
    """manifest JSONL 解析失败。"""

    def __init__(self, path: str | Path, line_number: int, message: str) -> None:
        super().__init__(f"manifest 解析失败: {path}:{line_number}: {message}")
        self.path = str(path)
        self.line_number = line_number
        self.message = message


class ManifestWriteError(ManifestError):
    """manifest 写入失败。"""


def utc_now_ms() -> str:
    """返回 UTC ISO 8601 毫秒时间戳，使用 Z 后缀。"""

    return (
        datetime.now(UTC)
        .isoformat(timespec="milliseconds")
        .replace("+00:00", "Z")
    )


def ensure_parent_dir(path: str | Path) -> None:
    """逐级确认父路径是目录，并创建缺失目录。"""

    target = Path(path)
    parent = target.parent
    if not parent or str(parent) == ".":
        return

    current = Path(parent.anchor) if parent.is_absolute() else Path(".")
    for part in parent.parts if not parent.is_absolute() else parent.parts[1:]:
        current = current / part
        if current.exists() and not current.is_dir():
            raise ManifestWriteError(f"安装路径被非目录占用: {current}")
    parent.mkdir(parents=True, exist_ok=True)


def _json_default(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, tuple):
        return list(value)
    raise TypeError(f"对象不可 JSON 序列化: {type(value).__name__}")


def normalize_manifest_record(record: dict[str, Any]) -> dict[str, Any]:
    """补齐 manifest 条件字段的默认值并校验状态枚举。"""

    normalized = dict(record)
    status = normalized.get("status")
    if status not in MANIFEST_STATUS_VALUES:
        raise ManifestWriteError(f"非法 manifest 状态: {status!r}")

    normalized.setdefault("schema_version", "1.0")
    normalized.setdefault("request_params", {})
    normalized.setdefault("symbol_range", [])
    normalized.setdefault("date_range", {})
    normalized.setdefault("requested_at", "")
    normalized.setdefault("request_started_at", normalized.get("requested_at", ""))
    normalized.setdefault("request_finished_at", "")
    normalized.setdefault("completed_at", "")
    normalized.setdefault("manifest_written_at", utc_now_ms())
    normalized.setdefault("attempts", 0)
    normalized.setdefault("retry_events", [])
    normalized.setdefault("raw_path", "")
    normalized.setdefault("standardized_output_path", None)
    normalized.setdefault("coverage_start", "")
    normalized.setdefault("coverage_end", "")
    normalized.setdefault("success_items", [])
    normalized.setdefault("failed_items", [])
    normalized.setdefault("error_type", "")
    normalized.setdefault("error_message", "")

    missing = [field for field in MANIFEST_REQUIRED_FIELDS if field not in normalized]
    if missing:
        raise ManifestWriteError(f"manifest 记录缺少字段: {', '.join(missing)}")
    return normalized


@dataclass(slots=True)
class ManifestAppendResult:
    path: str
    line_number: int


class ManifestStore:
    """append-only JSONL manifest 存储。"""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def append(self, record: dict[str, Any]) -> ManifestAppendResult:
        """追加一条 manifest 记录，返回写入行号。"""

        normalized = normalize_manifest_record(record)
        normalized["manifest_written_at"] = utc_now_ms()
        try:
            ensure_parent_dir(self.path)
            line_number = self._line_count() + 1
            with self.path.open("a", encoding="utf-8") as handle:
                handle.write(
                    json.dumps(
                        normalized,
                        ensure_ascii=False,
                        sort_keys=True,
                        default=_json_default,
                    )
                )
                handle.write("\n")
        except ManifestError:
            raise
        except OSError as exc:
            raise ManifestWriteError(f"manifest 写入失败: {self.path}: {exc}") from exc
        except TypeError as exc:
            raise ManifestWriteError(str(exc)) from exc
        return ManifestAppendResult(path=str(self.path), line_number=line_number)

    def iter_records(self) -> Iterable[dict[str, Any]]:
        """按文件顺序读取 manifest 记录；损坏行会结构化报错。"""

        if not self.path.exists():
            return []
        records: list[dict[str, Any]] = []
        try:
            with self.path.open("r", encoding="utf-8") as handle:
                for line_number, line in enumerate(handle, start=1):
                    text = line.strip()
                    if not text:
                        continue
                    try:
                        parsed = json.loads(text)
                    except json.JSONDecodeError as exc:
                        raise ManifestFormatError(
                            self.path,
                            line_number,
                            exc.msg,
                        ) from exc
                    if not isinstance(parsed, dict):
                        raise ManifestFormatError(
                            self.path,
                            line_number,
                            "JSONL 行必须是 object",
                        )
                    records.append(parsed)
        except ManifestFormatError:
            raise
        except OSError as exc:
            raise ManifestError(f"manifest 读取失败: {self.path}: {exc}") from exc
        return records

    def latest_by_batch_id(self) -> dict[str, dict[str, Any]]:
        """按 batch_id 返回最后一条有效记录。"""

        latest: dict[str, dict[str, Any]] = {}
        for record in self.iter_records():
            batch_id = record.get("batch_id")
            if isinstance(batch_id, str) and batch_id:
                latest[batch_id] = record
        return latest

    def successful_batch_ids(self) -> set[str]:
        """返回最新状态为 success 的 batch_id 集合。"""

        return {
            batch_id
            for batch_id, record in self.latest_by_batch_id().items()
            if record.get("status") == "success"
        }

    def should_skip_batch(self, batch_id: str, force_refresh: bool = False) -> bool:
        """判断批次是否可按最新 success 记录跳过。"""

        if force_refresh:
            return False
        latest = self.latest_by_batch_id().get(batch_id)
        return bool(latest and latest.get("status") == "success")

    def _line_count(self) -> int:
        if not self.path.exists():
            return 0
        with self.path.open("r", encoding="utf-8") as handle:
            return sum(1 for _ in handle)


__all__ = (
    "ManifestAppendResult",
    "ManifestError",
    "ManifestFormatError",
    "ManifestStore",
    "ManifestWriteError",
    "ensure_parent_dir",
    "normalize_manifest_record",
    "utc_now_ms",
)
