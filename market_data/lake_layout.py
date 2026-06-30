"""market_data 数据湖路径契约。"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Union

from .contracts import SCHEMA_VERSION

PathLike = Union[str, Path]
_GLOB_CHARS = frozenset("*?[")
CR139_RUN_ID_PATTERN = re.compile(
    r"^cr139-w2-[a-z0-9][a-z0-9_]*-[a-z0-9][a-z0-9_]*-\d{8}-[a-z0-9][a-z0-9_]*$"
)
LEGACY_RUN_ID_PATH_SEGMENT_PATTERN = re.compile(r"(^|/)run_id=[^/]+(/|$)")


class MarketDataPathError(ValueError):
    """数据湖路径不可安全写入。"""


def _compact_date(value: object) -> str:
    text = str(value)
    if len(text) == 8 and text.isdigit():
        return text
    if len(text) >= 10 and text[4] == "-" and text[7] == "-":
        return text[:10].replace("-", "")
    raise MarketDataPathError(f"无法解析日期路径片段: {text}")


def _clean_partition_value(name: str, value: object) -> str:
    text = str(value).strip()
    if not text:
        raise MarketDataPathError(f"{name} 路径片段不能为空")
    if "/" in text or "\\" in text:
        raise MarketDataPathError(f"{name} 路径片段不能包含目录分隔符: {text}")
    if any(char in text for char in _GLOB_CHARS):
        raise MarketDataPathError(f"{name} 路径片段不能包含 glob 字符: {text}")
    return text


def build_cr139_run_id(
    *,
    dataset: str,
    source: str,
    as_of_date: object,
    purpose: str,
) -> str:
    """Build deterministic W2 run_id; no directory creation or storage touch."""

    dataset_part = _clean_run_id_token("dataset", dataset)
    source_part = _clean_run_id_token("source", source)
    purpose_part = _clean_run_id_token("purpose", purpose)
    return f"cr139-w2-{dataset_part}-{source_part}-{_compact_date(as_of_date)}-{purpose_part}"


def validate_cr139_run_id(run_id: str) -> bool:
    """Return whether a run_id follows the W2 naming contract."""

    return bool(CR139_RUN_ID_PATTERN.fullmatch(str(run_id).strip()))


def legacy_run_id_path_detected(path: PathLike) -> bool:
    """Detect legacy run_id path segments for audit/planning only."""

    return bool(LEGACY_RUN_ID_PATH_SEGMENT_PATTERN.search(Path(path).as_posix()))


def ensure_path_outside_root(path: PathLike, root: PathLike, *, label: str = "输出路径") -> Path:
    """Resolve path and fail when it would write inside the protected lake root."""

    resolved_path = _normalise_for_allowlist(path)
    resolved_root = _normalise_for_allowlist(root)
    try:
        resolved_path.relative_to(resolved_root)
    except ValueError:
        return resolved_path
    raise MarketDataPathError(f"{label}不能位于 lake_root 内: {resolved_path}")


def _clean_run_id_token(name: str, value: object) -> str:
    text = _clean_partition_value(name, value).lower().replace("-", "_")
    if not re.fullmatch(r"[a-z0-9][a-z0-9_]*", text):
        raise MarketDataPathError(f"{name} run_id token 不合法: {text}")
    return text


def _normalise_for_allowlist(path: PathLike) -> Path:
    return Path(path).expanduser().resolve(strict=False)


def _contains_glob(path: PathLike) -> bool:
    return any(char in str(path) for char in _GLOB_CHARS)


@dataclass(frozen=True, slots=True)
class LakeLayout:
    """只负责解析路径，不隐式创建目录或写入数据。"""

    lake_root: PathLike

    def __post_init__(self) -> None:
        object.__setattr__(self, "lake_root", Path(self.lake_root))

    @property
    def raw_root(self) -> Path:
        return self.lake_root / "raw"

    @property
    def manifest_root(self) -> Path:
        return self.lake_root / "manifest"

    @property
    def canonical_root(self) -> Path:
        return self.lake_root / "canonical"

    @property
    def gold_root(self) -> Path:
        return self.lake_root / "gold"

    @property
    def quality_root(self) -> Path:
        return self.lake_root / "quality"

    @property
    def catalog_root(self) -> Path:
        return self.lake_root / "catalog"

    @property
    def candidate_root(self) -> Path:
        return self.lake_root / "candidate"

    @property
    def published_root(self) -> Path:
        return self.lake_root / "published"

    @property
    def features_root(self) -> Path:
        return self.lake_root / "features"

    @property
    def orphan_raw_root(self) -> Path:
        return self.raw_root / "_orphan"

    def raw_batch_path(
        self,
        source: str,
        interface: str,
        trade_date: object,
        batch_id: str,
        suffix: str = "jsonl",
    ) -> Path:
        clean_suffix = suffix[1:] if suffix.startswith(".") else suffix
        return (
            self.raw_root
            / source
            / interface
            / _compact_date(trade_date)
            / f"{batch_id}.{clean_suffix}"
        )

    def raw_run_batch_path(
        self,
        source: str,
        interface: str,
        trade_date: object,
        run_id: str,
        batch_id: str,
        suffix: str = "jsonl",
    ) -> Path:
        clean_suffix = suffix[1:] if suffix.startswith(".") else suffix
        return (
            self.raw_root
            / source
            / interface
            / _compact_date(trade_date)
            / f"run_id={run_id}"
            / f"{batch_id}.{clean_suffix}"
        )

    def manifest_path(self) -> Path:
        return self.manifest_root / "market_data_manifest.jsonl"

    def canonical_dataset_root(
        self,
        dataset: str,
        schema_version: str = SCHEMA_VERSION,
    ) -> Path:
        return self.canonical_root / dataset / schema_version

    def canonical_current_root(
        self,
        dataset: str,
        schema_version: str = SCHEMA_VERSION,
    ) -> Path:
        """返回 canonical current 根路径，不隐式创建目录。"""

        return (
            self.canonical_root
            / _clean_partition_value("dataset", dataset)
            / _clean_partition_value("schema_version", schema_version)
            / "current"
        )

    def canonical_archive_root(
        self,
        dataset: str,
        schema_version: str = SCHEMA_VERSION,
    ) -> Path:
        """返回 canonical archive 根路径，不隐式创建目录。"""

        return (
            self.canonical_root
            / _clean_partition_value("dataset", dataset)
            / _clean_partition_value("schema_version", schema_version)
            / "archive"
        )

    def canonical_current_partition_path(
        self,
        dataset: str,
        schema_version: str = SCHEMA_VERSION,
        *,
        partition_date: object | None = None,
        trade_date: object | None = None,
        exchange: str | None = None,
        board: str | None = None,
    ) -> Path:
        """返回 canonical current Hive-style 分区路径，不包含 run_id 段。"""

        return self._canonical_versioned_partition_path(
            self.canonical_current_root(dataset, schema_version),
            partition_date=partition_date,
            trade_date=trade_date,
            exchange=exchange,
            board=board,
        )

    def canonical_archive_partition_path(
        self,
        dataset: str,
        schema_version: str = SCHEMA_VERSION,
        *,
        partition_date: object | None = None,
        trade_date: object | None = None,
        exchange: str | None = None,
        board: str | None = None,
    ) -> Path:
        """返回 canonical archive Hive-style 分区路径，不包含 run_id 段。"""

        return self._canonical_versioned_partition_path(
            self.canonical_archive_root(dataset, schema_version),
            partition_date=partition_date,
            trade_date=trade_date,
            exchange=exchange,
            board=board,
        )

    def _canonical_versioned_partition_path(
        self,
        root: Path,
        *,
        partition_date: object | None = None,
        trade_date: object | None = None,
        exchange: str | None = None,
        board: str | None = None,
    ) -> Path:
        path = root
        effective_date = trade_date if trade_date is not None else partition_date
        if effective_date is not None:
            path = path / f"trade_date={_compact_date(effective_date)}"
        if exchange is not None:
            path = path / f"exchange={_clean_partition_value('exchange', exchange)}"
        if board is not None:
            path = path / f"board={_clean_partition_value('board', board)}"
        return path

    def candidate_dataset_root(
        self,
        dataset: str,
        schema_version: str,
        run_id: str,
    ) -> Path:
        """返回 CR014 未发布候选 Parquet 根路径，不创建目录。"""

        return (
            self.candidate_root
            / "parquet"
            / f"dataset={_clean_partition_value('dataset', dataset)}"
            / f"schema_version={_clean_partition_value('schema_version', schema_version)}"
            / f"run_id={_clean_partition_value('run_id', run_id)}"
        )

    def published_dataset_root(
        self,
        dataset: str,
        schema_version: str = SCHEMA_VERSION,
    ) -> Path:
        """返回 CR014 已发布 current truth Parquet 根路径，不创建目录。"""

        return (
            self.published_root
            / "parquet"
            / f"dataset={_clean_partition_value('dataset', dataset)}"
            / f"schema_version={_clean_partition_value('schema_version', schema_version)}"
        )

    def feature_artifact_path(
        self,
        feature_set_id: str,
        schema_version: str,
        artifact_version: str,
        *,
        as_of_trade_date: object,
        run_id: str,
    ) -> Path:
        """Return the CR139 versioned features artifact path without creating it."""

        return (
            self.features_root
            / f"feature_set={_clean_partition_value('feature_set_id', feature_set_id)}"
            / f"schema_version={_clean_partition_value('schema_version', schema_version)}"
            / f"artifact_version={_clean_partition_value('artifact_version', artifact_version)}"
            / f"as_of_trade_date={_compact_date(as_of_trade_date)}"
            / f"run_id={_clean_partition_value('run_id', run_id)}"
        )

    def candidate_partition_path(
        self,
        dataset: str,
        schema_version: str,
        run_id: str,
        *,
        partition_date: object | None = None,
        trade_date: object | None = None,
        exchange: str | None = None,
        board: str | None = None,
    ) -> Path:
        """返回 CR014 candidate Hive-style 分区路径，不隐式写入。"""

        path = self.candidate_dataset_root(dataset, schema_version, run_id)
        effective_date = trade_date if trade_date is not None else partition_date
        if effective_date is not None:
            path = path / f"trade_date={_compact_date(effective_date)}"
        if exchange is not None:
            path = path / f"exchange={_clean_partition_value('exchange', exchange)}"
        if board is not None:
            path = path / f"board={_clean_partition_value('board', board)}"
        return path

    def published_partition_path(
        self,
        dataset: str,
        schema_version: str = SCHEMA_VERSION,
        *,
        partition_date: object | None = None,
        trade_date: object | None = None,
        exchange: str | None = None,
        board: str | None = None,
    ) -> Path:
        """返回 CR014 published Hive-style 分区路径，不隐式写入。"""

        path = self.published_dataset_root(dataset, schema_version)
        effective_date = trade_date if trade_date is not None else partition_date
        if effective_date is not None:
            path = path / f"trade_date={_compact_date(effective_date)}"
        if exchange is not None:
            path = path / f"exchange={_clean_partition_value('exchange', exchange)}"
        if board is not None:
            path = path / f"board={_clean_partition_value('board', board)}"
        return path

    def catalog_current_pointer_path(
        self,
        dataset: str,
        schema_version: str = SCHEMA_VERSION,
    ) -> Path:
        """返回 CR014 catalog current pointer 文件路径，不读取或写入文件。"""

        return (
            self.catalog_root
            / "current"
            / f"dataset={_clean_partition_value('dataset', dataset)}"
            / f"schema_version={_clean_partition_value('schema_version', schema_version)}"
            / "pointer.json"
        )

    def candidate_audit_path(self, dataset: str, run_id: str, audit_id: str) -> Path:
        """返回 DuckDB / parity 可审计的受控 candidate audit path。"""

        return (
            self.candidate_root
            / "audit"
            / f"dataset={_clean_partition_value('dataset', dataset)}"
            / f"run_id={_clean_partition_value('run_id', run_id)}"
            / f"audit_id={_clean_partition_value('audit_id', audit_id)}"
        )

    def s09_window_raw_path(
        self,
        *,
        dataset: str,
        source: str,
        interface: str,
        run_id: str,
        window_id: str,
        suffix: str = "json",
    ) -> Path:
        """返回 S09 run-scoped raw window 路径，不隐式写入。"""

        clean_suffix = suffix[1:] if suffix.startswith(".") else suffix
        return (
            self.raw_root
            / "windowed"
            / f"dataset={_clean_partition_value('dataset', dataset)}"
            / f"source={_clean_partition_value('source', source)}"
            / f"interface={_clean_partition_value('interface', interface)}"
            / f"run_id={_clean_partition_value('run_id', run_id)}"
            / f"window_id={_clean_partition_value('window_id', window_id)}"
            / f"payload.{clean_suffix}"
        )

    def s09_window_manifest_path(
        self,
        *,
        dataset: str,
        run_id: str,
        window_id: str,
        suffix: str = "json",
    ) -> Path:
        """返回 S09 window manifest 路径，不更新 catalog current pointer。"""

        clean_suffix = suffix[1:] if suffix.startswith(".") else suffix
        return (
            self.manifest_root
            / "windowed"
            / f"dataset={_clean_partition_value('dataset', dataset)}"
            / f"run_id={_clean_partition_value('run_id', run_id)}"
            / f"window_id={_clean_partition_value('window_id', window_id)}"
            / f"manifest.{clean_suffix}"
        )

    def s09_window_metadata_path(
        self,
        *,
        dataset: str,
        run_id: str,
        window_id: str,
        suffix: str = "json",
    ) -> Path:
        """返回 S09 run metadata 路径，不触发 normalize / publish。"""

        clean_suffix = suffix[1:] if suffix.startswith(".") else suffix
        return (
            self.manifest_root
            / "windowed"
            / f"dataset={_clean_partition_value('dataset', dataset)}"
            / f"run_id={_clean_partition_value('run_id', run_id)}"
            / f"window_id={_clean_partition_value('window_id', window_id)}"
            / f"run_metadata.{clean_suffix}"
        )


def is_duckdb_read_path_allowed(
    path: PathLike,
    *,
    catalog_pointer_paths: Iterable[PathLike] = (),
    candidate_audit_paths: Iterable[PathLike] = (),
) -> bool:
    """精确白名单：只允许 catalog pointer path 或受控 candidate audit path。"""

    if _contains_glob(path):
        return False
    target = _normalise_for_allowlist(path)
    allowed = {
        _normalise_for_allowlist(item)
        for item in (*tuple(catalog_pointer_paths), *tuple(candidate_audit_paths))
    }
    return target in allowed


def ensure_parent_dirs_for_write(path: PathLike) -> None:
    """逐级检查父路径，普通文件占用时 fail fast。"""

    target = Path(path)
    parents = list(target.parents)
    for parent in reversed(parents):
        if parent.exists() and not parent.is_dir():
            raise MarketDataPathError(f"安装路径被非目录占用: {parent}")
    target.parent.mkdir(parents=True, exist_ok=True)


def ensure_s09_lake_root_allowed(lake_root: PathLike) -> Path:
    """校验 S09 lake root；禁止默认旧 data/reports、凭据和 DuckDB 路径。"""

    if str(lake_root).strip() == "":
        raise MarketDataPathError("S09 lake root 必须显式提供")
    path = Path(lake_root)
    parts = path.parts
    if not path.is_absolute() and parts and parts[0] in {"data", "reports"}:
        raise MarketDataPathError(
            "S09 lake root 不得默认指向旧 repo data/** 或 reports/**"
        )
    if path.is_absolute():
        cwd = Path.cwd()
        for forbidden_root in (cwd / "data", cwd / "reports"):
            try:
                path.relative_to(forbidden_root)
            except ValueError:
                continue
            raise MarketDataPathError(
                "S09 lake root 不得默认指向旧 repo data/** 或 reports/**"
            )
    lowered_parts = tuple(part.lower() for part in parts)
    if ".env" in lowered_parts or any(part.endswith(".duckdb") for part in lowered_parts):
        raise MarketDataPathError("S09 lake root 不得指向凭据文件或 DuckDB 文件")
    if path.exists() and not path.is_dir():
        raise MarketDataPathError(f"安装路径被非目录占用: {path}")
    for parent in reversed(path.parents):
        if parent.exists() and not parent.is_dir():
            raise MarketDataPathError(f"安装路径被非目录占用: {parent}")
    return path


__all__ = [
    "CR139_RUN_ID_PATTERN",
    "LEGACY_RUN_ID_PATH_SEGMENT_PATTERN",
    "LakeLayout",
    "MarketDataPathError",
    "build_cr139_run_id",
    "ensure_parent_dirs_for_write",
    "ensure_s09_lake_root_allowed",
    "is_duckdb_read_path_allowed",
    "legacy_run_id_path_detected",
    "validate_cr139_run_id",
]
