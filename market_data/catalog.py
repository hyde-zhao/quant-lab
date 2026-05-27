"""market_data 最小 catalog JSON 存储。"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field, fields
from pathlib import Path
from typing import Any

from .contracts import (
    DATASET_ADJ_FACTOR,
    DATASET_EVENTS,
    DATASET_HS300_INDEX,
    DATASET_INDEX_MEMBERS,
    DATASET_INDEX_WEIGHTS,
    DATASET_PRICES_LIMIT,
    DATASET_PRICES,
    DATASET_STOCK_BASIC,
    DATASET_TRADE_CALENDAR,
    DATASET_TRADE_STATUS,
    PIT_STATUS_AVAILABLE,
    QUALITY_STATUS_FAIL,
    QUALITY_STATUS_MISSING,
    QUALITY_STATUS_PASS,
    QUALITY_STATUS_WARN,
    READINESS_STATUS_AVAILABLE,
    SCHEMA_VERSION,
)
from .lake_layout import LakeLayout, ensure_parent_dirs_for_write, is_duckdb_read_path_allowed


class CatalogError(RuntimeError):
    """catalog 读取或写入失败。"""


@dataclass(frozen=True, slots=True)
class CatalogEntry:
    dataset: str
    schema_version: str = SCHEMA_VERSION
    start_date: str | None = None
    end_date: str | None = None
    coverage: dict[str, Any] = field(default_factory=dict)
    quality_status: str = "unknown"
    dataset_status: str = "unknown"
    latest_manifest_run_id: str | None = None
    source: str | None = None
    source_interface: str | None = None
    lineage_raw_checksum: str | None = None
    canonical_path: str | None = None
    quality_csv_path: str | None = None
    quality_path: str | None = None
    generated_at: str | None = None
    updated_at: str | None = None
    published: bool = True
    published_at: str | None = None
    readiness_status: str | None = None
    pit_status: str | None = None
    available_at_rule: str | None = None
    known_limitations: list[Any] = field(default_factory=list)
    coverage_denominator: int | None = None
    coverage_ratio: float | None = None
    coverage_start: str | None = None
    coverage_end: str | None = None
    lineage_checksum: str | None = None
    universe_scope: str | None = None
    as_of_trade_date: str | None = None
    catalog_pointer_path: str | None = None

    @property
    def catalog_id(self) -> str:
        return f"{self.dataset}:{self.schema_version}:{self.start_date or ''}:{self.end_date or ''}"


CR014_CATALOG_POINTER_REQUIRED_FIELDS: tuple[str, ...] = (
    "dataset",
    "schema_version",
    "coverage_start",
    "coverage_end",
    "coverage_denominator",
    "latest_manifest_run_id",
    "lineage_checksum",
    "published_at",
    "known_limitations",
    "universe_scope",
    "as_of_trade_date",
)

CATALOG_POINTER_INCOMPLETE = "catalog_pointer_incomplete"
CATALOG_POINTER_DENOMINATOR_INVALID = "catalog_pointer_denominator_invalid"
DUCKDB_READ_PATH_NOT_WHITELISTED = "duckdb_read_path_not_whitelisted"
DUCKDB_GLOB_NOT_ALLOWED = "duckdb_glob_not_allowed"


@dataclass(frozen=True, slots=True)
class CatalogPointer:
    """CR014 catalog current pointer 合同。"""

    dataset: str
    schema_version: str
    coverage_start: str
    coverage_end: str
    coverage_denominator: int
    latest_manifest_run_id: str
    lineage_checksum: str
    published_at: str
    known_limitations: list[dict[str, Any]]
    universe_scope: str
    as_of_trade_date: str
    published_path: str | None = None
    quality_status: str = QUALITY_STATUS_PASS
    readiness_status: str = READINESS_STATUS_AVAILABLE

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class CatalogPointerValidationResult:
    passed: bool
    current_truth_visible: bool
    missing_fields: tuple[str, ...] = ()
    error_codes: tuple[str, ...] = ()
    details: tuple[dict[str, Any], ...] = ()
    required_fields: tuple[str, ...] = CR014_CATALOG_POINTER_REQUIRED_FIELDS

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class ReadOnlyPathValidationResult:
    allowed: bool
    path: str
    error_code: str | None = None
    reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _missing_pointer_value(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str) and not value.strip():
        return True
    return False


def _catalog_pointer_payload(pointer: CatalogPointer | CatalogEntry | dict[str, Any]) -> dict[str, Any]:
    if isinstance(pointer, CatalogPointer):
        return pointer.to_dict()
    if isinstance(pointer, CatalogEntry):
        payload = asdict(pointer)
        payload.setdefault("coverage_start", pointer.start_date)
        payload.setdefault("coverage_end", pointer.end_date)
        payload.setdefault("lineage_checksum", pointer.lineage_raw_checksum)
        if payload.get("coverage_start") is None:
            payload["coverage_start"] = pointer.start_date
        if payload.get("coverage_end") is None:
            payload["coverage_end"] = pointer.end_date
        if payload.get("lineage_checksum") is None:
            payload["lineage_checksum"] = pointer.lineage_raw_checksum
        return payload
    return dict(pointer)


def validate_catalog_pointer(
    pointer: CatalogPointer | CatalogEntry | dict[str, Any],
) -> CatalogPointerValidationResult:
    """校验 CR014 current pointer 必填字段；缺字段时 fail-closed。"""

    payload = _catalog_pointer_payload(pointer)
    missing = tuple(
        field
        for field in CR014_CATALOG_POINTER_REQUIRED_FIELDS
        if field not in payload or _missing_pointer_value(payload[field])
    )
    error_codes: list[str] = []
    details: list[dict[str, Any]] = []
    if missing:
        error_codes.append(CATALOG_POINTER_INCOMPLETE)
        details.append({"code": CATALOG_POINTER_INCOMPLETE, "missing_fields": list(missing)})

    denominator = payload.get("coverage_denominator")
    if denominator is not None and (
        isinstance(denominator, bool) or not isinstance(denominator, int) or denominator < 0
    ):
        error_codes.append(CATALOG_POINTER_DENOMINATOR_INVALID)
        details.append(
            {
                "code": CATALOG_POINTER_DENOMINATOR_INVALID,
                "coverage_denominator": denominator,
            }
        )

    known_limitations = payload.get("known_limitations")
    if known_limitations is not None and not isinstance(known_limitations, list):
        error_codes.append(CATALOG_POINTER_INCOMPLETE)
        details.append({"code": CATALOG_POINTER_INCOMPLETE, "field": "known_limitations"})

    passed = not error_codes
    return CatalogPointerValidationResult(
        passed=passed,
        current_truth_visible=passed,
        missing_fields=missing,
        error_codes=tuple(dict.fromkeys(error_codes)),
        details=tuple(details),
    )


def catalog_pointer_from_entry(entry: CatalogEntry) -> CatalogPointer:
    """将兼容 CatalogEntry 转为 CR014 CatalogPointer；字段不完整则抛错。"""

    payload = _catalog_pointer_payload(entry)
    validation = validate_catalog_pointer(payload)
    if not validation.passed:
        raise CatalogError(
            "catalog pointer 字段不完整: "
            + ",".join(validation.missing_fields or validation.error_codes)
        )
    return CatalogPointer(
        dataset=str(payload["dataset"]),
        schema_version=str(payload["schema_version"]),
        coverage_start=str(payload["coverage_start"]),
        coverage_end=str(payload["coverage_end"]),
        coverage_denominator=int(payload["coverage_denominator"]),
        latest_manifest_run_id=str(payload["latest_manifest_run_id"]),
        lineage_checksum=str(payload["lineage_checksum"]),
        published_at=str(payload["published_at"]),
        known_limitations=list(payload["known_limitations"]),
        universe_scope=str(payload["universe_scope"]),
        as_of_trade_date=str(payload["as_of_trade_date"]),
        published_path=payload.get("canonical_path") or payload.get("published_path"),
        quality_status=str(payload.get("quality_status") or QUALITY_STATUS_PASS),
        readiness_status=str(payload.get("readiness_status") or READINESS_STATUS_AVAILABLE),
    )


def validate_duckdb_read_path(
    path: str | Path,
    *,
    catalog_pointer_path: str | Path,
    candidate_audit_paths: tuple[str | Path, ...] = (),
) -> ReadOnlyPathValidationResult:
    """DuckDB read-only path 白名单校验，不导入或运行 DuckDB。"""

    path_text = str(path)
    if any(char in path_text for char in "*?["):
        return ReadOnlyPathValidationResult(
            allowed=False,
            path=path_text,
            error_code=DUCKDB_GLOB_NOT_ALLOWED,
            reason="DuckDB read-only path 禁止使用 glob",
        )
    allowed = is_duckdb_read_path_allowed(
        path,
        catalog_pointer_paths=(catalog_pointer_path,),
        candidate_audit_paths=candidate_audit_paths,
    )
    if allowed:
        return ReadOnlyPathValidationResult(allowed=True, path=path_text)
    return ReadOnlyPathValidationResult(
        allowed=False,
        path=path_text,
        error_code=DUCKDB_READ_PATH_NOT_WHITELISTED,
        reason="只允许 catalog pointer path 或受控 candidate audit path",
    )


class CatalogStore:
    """以 JSON 维护 dataset 最新质量与路径索引。"""

    def __init__(self, layout: LakeLayout | str | Path) -> None:
        self.layout = layout if isinstance(layout, LakeLayout) else LakeLayout(layout)

    @property
    def path(self) -> Path:
        return self.layout.catalog_root / "catalog.json"

    def _read_all(self) -> dict[str, Any]:
        if not self.path.exists():
            return {"schema_version": SCHEMA_VERSION, "datasets": {}}
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise CatalogError(f"catalog 不是合法 JSON: {self.path}") from exc
        if not isinstance(payload, dict) or not isinstance(payload.get("datasets"), dict):
            raise CatalogError(f"catalog 结构不合法: {self.path}")
        return payload

    def _entry_from_payload(self, item: dict[str, Any], dataset: str) -> CatalogEntry:
        entry_fields = {field.name for field in fields(CatalogEntry)}
        values = {key: value for key, value in item.items() if key in entry_fields}
        values.setdefault("dataset", dataset)
        return CatalogEntry(**values)

    def upsert(self, entry: CatalogEntry) -> Path:
        payload = self._read_all()
        payload["schema_version"] = SCHEMA_VERSION
        payload.setdefault("datasets", {})[entry.dataset] = asdict(entry)
        tmp_path = self.path.with_name(self.path.name + ".tmp")
        ensure_parent_dirs_for_write(tmp_path)
        tmp_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        tmp_path.replace(self.path)
        return self.path

    def get(self, dataset: str, quality_policy: object = None) -> CatalogEntry:
        payload = self._read_all()
        item = payload["datasets"].get(dataset)
        if item is None:
            raise CatalogError(f"catalog 中不存在 dataset: {dataset}")
        if not isinstance(item, dict):
            raise CatalogError(f"catalog dataset 结构不合法: {dataset}")
        entry = self._entry_from_payload(item, dataset)
        if quality_policy is None:
            return entry
        allow_warn = bool(getattr(quality_policy, "allow_warn", False))
        if isinstance(quality_policy, dict):
            allow_warn = bool(quality_policy.get("allow_warn", allow_warn))
        if entry.quality_status == "fail":
            raise CatalogError(f"catalog quality fail: {dataset}")
        if entry.quality_status == "warn" and not allow_warn:
            raise CatalogError(f"catalog quality warn blocked: {dataset}")
        return entry

    def get_current_pointer(self, dataset: str, quality_policy: object = None) -> CatalogPointer:
        entry = self.get(dataset, quality_policy=quality_policy)
        return catalog_pointer_from_entry(entry)

    def list(self, dataset: str | None = None) -> list[CatalogEntry]:
        payload = self._read_all()
        entries = [
            self._entry_from_payload(item, str(dataset))
            for dataset, item in payload["datasets"].items()
            if isinstance(item, dict)
        ]
        if dataset is not None:
            entries = [entry for entry in entries if entry.dataset == dataset]
        return entries


P0_DATASETS: tuple[str, ...] = (
    DATASET_PRICES,
    DATASET_ADJ_FACTOR,
    DATASET_HS300_INDEX,
    DATASET_TRADE_CALENDAR,
    DATASET_INDEX_MEMBERS,
    DATASET_INDEX_WEIGHTS,
    DATASET_STOCK_BASIC,
)

W3_REQUIRED_DATASETS: tuple[str, ...] = (
    DATASET_TRADE_STATUS,
    DATASET_PRICES_LIMIT,
    DATASET_EVENTS,
)

PRODUCTION_STRICT_DATASETS: tuple[str, ...] = (
    *P0_DATASETS,
    *W3_REQUIRED_DATASETS,
)

LEGACY_REPORT_POLICY = "legacy_only_not_current_truth"


def _coverage_row_missing(dataset: str) -> dict[str, Any]:
    return {
        "dataset": dataset,
        "publish_status": "missing_required",
        "current_truth": False,
        "quality_status": QUALITY_STATUS_MISSING,
        "readiness_status": "missing",
        "pit_status": "missing",
        "date_range": None,
        "source": None,
        "source_interface": None,
        "run_id": None,
        "canonical_path": None,
        "coverage_denominator": None,
        "coverage_ratio": None,
        "available_at_rule": None,
        "known_limitations": [{"code": "dataset_missing"}],
        "legacy_report_policy": LEGACY_REPORT_POLICY,
    }


def _coverage_row_from_entry(entry: CatalogEntry) -> dict[str, Any]:
    publish_status = "published" if entry.published else "candidate_unpublished"
    return {
        "dataset": entry.dataset,
        "publish_status": publish_status,
        "current_truth": bool(entry.published),
        "quality_status": entry.quality_status,
        "readiness_status": entry.readiness_status or "unknown",
        "pit_status": entry.pit_status or "unknown",
        "date_range": {
            "start_date": entry.start_date,
            "end_date": entry.end_date,
        },
        "source": entry.source,
        "source_interface": entry.source_interface,
        "run_id": entry.latest_manifest_run_id,
        "canonical_path": entry.canonical_path,
        "coverage_denominator": entry.coverage_denominator,
        "coverage_ratio": entry.coverage_ratio,
        "available_at_rule": entry.available_at_rule,
        "known_limitations": list(entry.known_limitations),
        "legacy_report_policy": LEGACY_REPORT_POLICY,
    }


def _source_policy_blockers(
    row: dict[str, Any],
    required_source: str | None,
) -> list[dict[str, Any]]:
    if required_source is None:
        return []
    dataset = str(row["dataset"])
    actual_source = str(row.get("source") or "")
    if actual_source == required_source:
        return []
    return [
        {
            "code": "source_policy_mismatch",
            "dataset": dataset,
            "expected_source": required_source,
            "actual_source": actual_source or "missing",
        }
    ]


def build_catalog_coverage_report(
    lake_root: str | Path | LakeLayout,
    *,
    datasets: tuple[str, ...] = P0_DATASETS,
) -> dict[str, Any]:
    """汇总 published catalog coverage，不读取旧 data 或 legacy report。"""

    store = CatalogStore(lake_root)
    entries = {entry.dataset: entry for entry in store.list()}
    rows = [
        _coverage_row_from_entry(entries[dataset])
        if dataset in entries
        else _coverage_row_missing(dataset)
        for dataset in datasets
    ]
    published = [row for row in rows if row["publish_status"] == "published"]
    candidates = [row for row in rows if row["publish_status"] == "candidate_unpublished"]
    missing = [row for row in rows if row["publish_status"] == "missing_required"]
    return {
        "ok": True,
        "report_type": "catalog_coverage",
        "datasets": list(datasets),
        "rows": rows,
        "summary": {
            "dataset_count": len(rows),
            "published_count": len(published),
            "candidate_unpublished_count": len(candidates),
            "missing_required_count": len(missing),
            "current_truth_complete": len(published) == len(rows),
        },
        "legacy_report_policy": LEGACY_REPORT_POLICY,
        "old_data_operations": {
            "read": 0,
            "list": 0,
            "migrate": 0,
            "copy": 0,
            "compare": 0,
            "delete": 0,
        },
        "legacy_quality_report_operations": {"read": 0, "open": 0, "overwrite": 0},
    }


def _row_blockers(row: dict[str, Any], realism_mode: str) -> list[dict[str, Any]]:
    blockers: list[dict[str, Any]] = []
    dataset = str(row["dataset"])
    if row["publish_status"] != "published":
        blockers.append({"code": "dataset_not_published", "dataset": dataset})
    quality_status = str(row.get("quality_status") or "missing")
    if quality_status == QUALITY_STATUS_FAIL:
        blockers.append({"code": "quality_failed", "dataset": dataset})
    elif quality_status in {QUALITY_STATUS_MISSING, "missing"}:
        blockers.append({"code": "quality_missing", "dataset": dataset})
    elif quality_status == QUALITY_STATUS_WARN and realism_mode == "production_strict":
        blockers.append({"code": "quality_warn_blocked", "dataset": dataset})
    readiness_status = str(row.get("readiness_status") or "missing")
    if readiness_status not in {READINESS_STATUS_AVAILABLE, QUALITY_STATUS_PASS, QUALITY_STATUS_WARN, "unknown"}:
        blockers.append(
            {
                "code": "readiness_not_available",
                "dataset": dataset,
                "readiness_status": readiness_status,
            }
        )
    if realism_mode == "production_strict" and dataset in {
        DATASET_INDEX_MEMBERS,
        DATASET_INDEX_WEIGHTS,
        DATASET_STOCK_BASIC,
    }:
        pit_status = str(row.get("pit_status") or "missing")
        if pit_status != PIT_STATUS_AVAILABLE:
            blockers.append(
                {
                    "code": "pit_not_available",
                    "dataset": dataset,
                    "pit_status": pit_status,
                }
            )
    if realism_mode == "production_strict" and dataset in W3_REQUIRED_DATASETS:
        readiness_status = str(row.get("readiness_status") or "missing")
        if row["publish_status"] != "published" or readiness_status != READINESS_STATUS_AVAILABLE:
            blockers.append(
                {
                    "code": "w3_required_missing",
                    "dataset": dataset,
                    "readiness_status": readiness_status,
                }
            )
        if dataset == DATASET_EVENTS and not row.get("available_at_rule"):
            blockers.append(
                {
                    "code": "events_available_at_missing",
                    "dataset": dataset,
                }
            )
    return blockers


def build_production_readiness_report(
    lake_root: str | Path | LakeLayout,
    *,
    datasets: tuple[str, ...] | None = None,
    realism_mode: str = "production_strict",
    required_source: str | None = None,
) -> dict[str, Any]:
    """构建 production readiness 报告；不会触发补数、联网或真实 lake 写入。"""

    if realism_mode not in {"production_strict", "exploratory"}:
        raise CatalogError(f"未知 realism_mode: {realism_mode}")
    effective_datasets = datasets or PRODUCTION_STRICT_DATASETS
    coverage = build_catalog_coverage_report(lake_root, datasets=effective_datasets)
    blockers: list[dict[str, Any]] = []
    limitations: list[dict[str, Any]] = []
    for row in coverage["rows"]:
        row_blockers = _row_blockers(row, realism_mode)
        row_blockers.extend(_source_policy_blockers(row, required_source))
        blockers.extend(row_blockers)
        limitations.extend(
            {
                "dataset": row["dataset"],
                **limitation,
            }
            for limitation in row.get("known_limitations", [])
            if isinstance(limitation, dict)
        )
    status = "pass" if not blockers else ("warn" if realism_mode == "exploratory" else "fail")
    blocked_claims = sorted(
        {
            "production_current_truth",
            *(
                ["pit_universe_research"]
                if any(item["code"].startswith("pit_") for item in blockers)
                else []
            ),
            *(
                ["real_benchmark_research"]
                if any(item.get("dataset") == DATASET_HS300_INDEX for item in blockers)
                else []
            ),
            *(
                ["adjustment_consistent_research"]
                if any(item.get("dataset") == DATASET_ADJ_FACTOR for item in blockers)
                else []
            ),
            *(
                ["real_tradable_execution"]
                if any(item.get("dataset") == DATASET_TRADE_STATUS for item in blockers)
                else []
            ),
            *(
                ["realistic_fillability"]
                if any(item.get("dataset") == DATASET_PRICES_LIMIT for item in blockers)
                else []
            ),
            *(
                ["event_timing_research"]
                if any(item.get("dataset") == DATASET_EVENTS for item in blockers)
                else []
            ),
            *(
                ["quality_pass_research"]
                if any("quality" in item["code"] for item in blockers)
                else []
            ),
            *(
                ["complete_p0_data_lake"]
                if coverage["summary"]["missing_required_count"]
                else []
            ),
        }
    )
    allowed_claims = (
        ["exploratory_analysis", "fixture_regression"]
        if realism_mode == "exploratory"
        else ([] if blockers else ["production_strict_research"])
    )
    return {
        "ok": True,
        "report_type": "production_readiness",
        "realism_mode": realism_mode,
        "status": status,
        "coverage_report": coverage,
        "blockers": blockers,
        "limitations": limitations,
        "allowed_claims": allowed_claims,
        "blocked_claims": blocked_claims,
        "remediation_spec": {
            "action": "publish_missing_or_fix_quality_before_production",
            "dry_run_default": True,
            "auto_execute": False,
            **({"required_source": required_source} if required_source else {}),
        },
        "legacy_report_policy": LEGACY_REPORT_POLICY,
    }


__all__ = [
    "CATALOG_POINTER_DENOMINATOR_INVALID",
    "CATALOG_POINTER_INCOMPLETE",
    "CR014_CATALOG_POINTER_REQUIRED_FIELDS",
    "CatalogEntry",
    "CatalogError",
    "CatalogPointer",
    "CatalogPointerValidationResult",
    "CatalogStore",
    "DUCKDB_GLOB_NOT_ALLOWED",
    "DUCKDB_READ_PATH_NOT_WHITELISTED",
    "LEGACY_REPORT_POLICY",
    "P0_DATASETS",
    "PRODUCTION_STRICT_DATASETS",
    "ReadOnlyPathValidationResult",
    "W3_REQUIRED_DATASETS",
    "build_catalog_coverage_report",
    "build_production_readiness_report",
    "catalog_pointer_from_entry",
    "validate_catalog_pointer",
    "validate_duckdb_read_path",
]
