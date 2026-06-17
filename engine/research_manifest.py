"""CR030-S06 实验 manifest 与研究报告 catalog 合同。

本模块只定义项目自有、离线、可审计的 ExperimentManifest /
ResearchReportCatalog。JSON / CSV / Markdown 路径引用是默认事实源；
不采用 MLflow、pickle recorder、lake current pointer 或 publish 结果作为 truth，
不读取凭据，不触发 provider / lake / QMT / simulation / live。
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, is_dataclass
from datetime import date, datetime, timezone
from enum import Enum
import csv
import json
from pathlib import Path
import re
from typing import Any, Mapping, Sequence

from engine.multifactor_contracts import (
    FORBIDDEN_OPERATION_COUNTERS,
    PermissionCounters,
    compute_config_hash,
)
from engine.research_paths import research_report_path


MANIFEST_SCHEMA_VERSION = "experiment_manifest_v1"
CATALOG_SCHEMA_VERSION = "research_report_catalog_v1"
ARTIFACT_SCHEMA_VERSION = "v1"
INTERNAL_TRUTH_SOURCE = "project_json_csv_markdown_artifacts"

MF_SCHEMA_REQUIRED_FIELD_MISSING = "MF_SCHEMA_REQUIRED_FIELD_MISSING"
MF_CONFIG_HASH_MISSING = "MF_CONFIG_HASH_MISSING"
MF_LINEAGE_MISSING = "MF_LINEAGE_MISSING"
MF_FORBIDDEN_TRUTH_SOURCE = "MF_FORBIDDEN_TRUTH_SOURCE"
MF_REPORT_ARTIFACT_PATH_FORBIDDEN = "MF_REPORT_ARTIFACT_PATH_FORBIDDEN"
MF_REPORT_ARTIFACT_EXISTS = "MF_REPORT_ARTIFACT_EXISTS"
MF_PROVIDER_OR_LAKE_NOT_AUTHORIZED = "MF_PROVIDER_OR_LAKE_NOT_AUTHORIZED"
MF_ADMISSION_NOT_READY = "MF_ADMISSION_NOT_READY"

MANIFEST_P0_FIELDS = (
    "run_id",
    "strategy_id",
    "config_hash",
    "dataset_release",
    "factor_versions",
    "label_window",
    "benchmark",
    "cost_config",
    "evaluation_window",
    "seed",
    "code_version",
    "report_paths",
    "allowed_claims",
    "blocked_claims",
    "limitations",
    "evidence_refs",
)

CATALOG_P0_FIELDS = (
    "catalog_entry_id",
    "report_id",
    "run_id",
    "factor_ids",
    "artifact_paths",
    "created_at",
    "source_lineage",
    "status",
    "admission_candidate",
    "allowed_claims",
    "blocked_claims",
)

ALLOWED_ARTIFACT_SUFFIXES = (".json", ".csv", ".md", ".markdown")
FORBIDDEN_TRUTH_MARKERS = (
    "mlflow",
    "pickle",
    ".pkl",
    ".pickle",
    "recorder://",
    "mlflow://",
)
PRODUCTION_READY_MARKERS = (
    "production truth",
    "production_truth",
    "qmt-ready",
    "qmt_ready",
    "simulation-ready",
    "simulation_ready",
    "live-ready",
    "live_ready",
    "tradable_evidence",
)


class CatalogStatus(str, Enum):
    PASS = "pass"
    BLOCKED = "blocked"
    RESEARCH_LIMITED = "research_limited"


@dataclass(frozen=True, slots=True)
class ManifestBlockedReason:
    code: str
    message: str
    field: str = ""
    severity: str = "blocker"
    evidence_ref: str = ""
    remediation: str = ""

    def to_dict(self) -> dict[str, Any]:
        return _json_safe(asdict(self))


@dataclass(frozen=True, slots=True)
class ResearchClaim:
    claim: str
    status: str
    reason: str
    evidence_ref: str = ""
    code: str = ""
    limitation: str = ""

    def to_dict(self) -> dict[str, Any]:
        return _json_safe(asdict(self))


@dataclass(frozen=True, slots=True)
class ManifestValidationResult:
    status: str
    blocked_reasons: tuple[ManifestBlockedReason, ...] = ()
    object_type: str = ""
    object_id: str = ""
    permission_counters: dict[str, int] = field(default_factory=dict)

    @property
    def passed(self) -> bool:
        return self.status == CatalogStatus.PASS.value

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "blocked_reasons": [reason.to_dict() for reason in self.blocked_reasons],
            "object_type": self.object_type,
            "object_id": self.object_id,
            "permission_counters": dict(self.permission_counters),
        }


@dataclass(frozen=True, slots=True)
class ExperimentManifest:
    run_id: str
    strategy_id: str
    config_hash: str
    dataset_release: str | Mapping[str, Any]
    factor_versions: tuple[Mapping[str, Any], ...]
    label_window: Mapping[str, Any]
    benchmark: Mapping[str, Any] | str
    cost_config: Mapping[str, Any]
    evaluation_window: Mapping[str, Any]
    seed: int | str
    code_version: str
    report_paths: tuple[str, ...]
    allowed_claims: tuple[ResearchClaim, ...]
    blocked_claims: tuple[ResearchClaim, ...]
    limitations: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    schema_version: str = MANIFEST_SCHEMA_VERSION
    source_of_truth: str = INTERNAL_TRUTH_SOURCE
    permission_counters: Mapping[str, int] = field(default_factory=dict)
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["allowed_claims"] = [claim.to_dict() for claim in self.allowed_claims]
        data["blocked_claims"] = [claim.to_dict() for claim in self.blocked_claims]
        return _json_safe(data)


@dataclass(frozen=True, slots=True)
class ResearchReportCatalog:
    catalog_entry_id: str
    report_id: str
    run_id: str
    strategy_id: str
    factor_ids: tuple[str, ...]
    artifact_paths: tuple[str, ...]
    created_at: str
    source_lineage: Mapping[str, Any]
    status: str
    admission_candidate: bool
    allowed_claims: tuple[ResearchClaim, ...]
    blocked_claims: tuple[ResearchClaim, ...]
    limitations: tuple[str, ...] = ()
    evidence_refs: tuple[str, ...] = ()
    schema_version: str = CATALOG_SCHEMA_VERSION
    source_of_truth: str = INTERNAL_TRUTH_SOURCE

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["allowed_claims"] = [claim.to_dict() for claim in self.allowed_claims]
        data["blocked_claims"] = [claim.to_dict() for claim in self.blocked_claims]
        return _json_safe(data)


@dataclass(frozen=True, slots=True)
class ResearchCatalogArtifactPaths:
    json_path: Path
    csv_path: Path
    markdown_path: Path

    def to_dict(self) -> dict[str, str]:
        return {
            "json": self.json_path.as_posix(),
            "csv": self.csv_path.as_posix(),
            "markdown": self.markdown_path.as_posix(),
        }


@dataclass(frozen=True, slots=True)
class ResearchCatalogWriteResult:
    status: str
    artifact_refs: tuple[str, ...]
    blocked_reasons: tuple[ManifestBlockedReason, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "artifact_refs": list(self.artifact_refs),
            "blocked_reasons": [reason.to_dict() for reason in self.blocked_reasons],
        }


def compute_experiment_config_hash(payload: Mapping[str, Any] | Any) -> str:
    """复用项目稳定 JSON hash，确保字段顺序不影响 manifest config_hash。"""

    return compute_config_hash(payload)


def build_experiment_manifest(
    run_spec: Mapping[str, Any] | Any,
    reports: Sequence[Mapping[str, Any] | Any],
    portfolio_plan: Mapping[str, Any] | Any | None = None,
    metadata: Mapping[str, Any] | None = None,
) -> ExperimentManifest:
    run_data = _as_mapping(run_spec) or {}
    plan_data = _as_mapping(portfolio_plan) or {}
    meta = dict(metadata or {})
    report_data = [_as_mapping(report) or {} for report in reports]

    allowed_claims = _collect_claims(report_data, "allowed_claims")
    blocked_claims = _collect_claims(report_data, "blocked_claims")
    report_paths = _collect_report_paths(report_data, meta)
    evidence_refs = _collect_evidence_refs(report_data, meta)
    limitations = _collect_limitations(report_data, meta)
    factor_versions = _factor_versions(run_data, report_data, plan_data, meta)

    return ExperimentManifest(
        run_id=str(run_data.get("run_id") or meta.get("run_id") or ""),
        strategy_id=str(run_data.get("strategy_id") or plan_data.get("strategy_id") or meta.get("strategy_id") or ""),
        config_hash=str(run_data.get("config_hash") or meta.get("config_hash") or ""),
        dataset_release=run_data.get("dataset_release") or meta.get("dataset_release") or "",
        factor_versions=factor_versions,
        label_window=_mapping_or_empty(run_data.get("label_window") or meta.get("label_window")),
        benchmark=run_data.get("benchmark") or meta.get("benchmark") or {},
        cost_config=_mapping_or_empty(run_data.get("cost_config") or meta.get("cost_config")),
        evaluation_window=_mapping_or_empty(run_data.get("evaluation_window") or run_data.get("date_range") or meta.get("evaluation_window")),
        seed=run_data.get("seed") if run_data.get("seed") is not None else meta.get("seed", ""),
        code_version=str(run_data.get("code_version") or meta.get("code_version") or ""),
        report_paths=report_paths,
        allowed_claims=allowed_claims,
        blocked_claims=blocked_claims,
        limitations=limitations,
        evidence_refs=evidence_refs,
        permission_counters=_normalise_permission_counters(run_data.get("permission_counters") or meta.get("permission_counters")),
        metadata=_json_safe({**meta, "portfolio_plan_ref": plan_data.get("plan_id") or plan_data.get("portfolio_plan_id") or ""}),
    )


def validate_experiment_manifest(manifest: ExperimentManifest | Mapping[str, Any] | Any) -> ManifestValidationResult:
    data = _as_mapping(manifest)
    if data is None:
        return _validation_result(
            "ExperimentManifest",
            "",
            (
                _reason(
                    MF_SCHEMA_REQUIRED_FIELD_MISSING,
                    "ExperimentManifest 必须是 dataclass 或 mapping",
                    field="manifest",
                ),
            ),
        )

    reasons: list[ManifestBlockedReason] = []
    reasons.extend(_required_field_reasons(data, MANIFEST_P0_FIELDS))
    if _is_blank(data.get("config_hash")):
        reasons.append(_reason(MF_CONFIG_HASH_MISSING, "ExperimentManifest.config_hash 缺失", field="config_hash"))
    reasons.extend(_artifact_path_reasons(data.get("report_paths"), field="report_paths"))
    reasons.extend(_claim_reasons(data))
    reasons.extend(_lineage_reasons(data))
    reasons.extend(_forbidden_truth_reasons(data))
    counters = _normalise_permission_counters(data.get("permission_counters"))
    reasons.extend(_permission_counter_reasons(counters))
    return _validation_result("ExperimentManifest", str(data.get("run_id") or ""), tuple(reasons), counters)


def build_research_report_catalog_entry(
    manifest: ExperimentManifest | Mapping[str, Any] | Any,
    report_refs: Sequence[str] | Mapping[str, Any] | None = None,
    *,
    created_at: str | None = None,
) -> ResearchReportCatalog:
    manifest_data = _as_mapping(manifest) or {}
    validation = validate_experiment_manifest(manifest_data)
    refs = _normalise_report_refs(report_refs)
    artifact_paths = tuple(dict.fromkeys(refs or tuple(manifest_data.get("report_paths") or ())))
    report_id = _first_report_id(manifest_data, artifact_paths)
    catalog_entry_id = _safe_slug(f"{manifest_data.get('run_id') or 'run-unknown'}-{report_id}")
    blocked_claims = _claims_from_data(manifest_data.get("blocked_claims"))
    if not validation.passed:
        blocked_claims = tuple(blocked_claims) + tuple(
            ResearchClaim(
                claim="strategy_admission_candidate",
                status="blocked",
                code=reason.code,
                reason=reason.message,
                evidence_ref=reason.evidence_ref,
                limitation="缺 P0 manifest/catalog 字段时不得进入 StrategyAdmissionPackage。",
            )
            for reason in validation.blocked_reasons
        )

    factor_ids = _factor_ids_from_manifest(manifest_data)
    return ResearchReportCatalog(
        catalog_entry_id=catalog_entry_id,
        report_id=report_id,
        run_id=str(manifest_data.get("run_id") or ""),
        strategy_id=str(manifest_data.get("strategy_id") or ""),
        factor_ids=factor_ids,
        artifact_paths=artifact_paths,
        created_at=created_at or _utc_timestamp(),
        source_lineage={
            "manifest_schema_version": manifest_data.get("schema_version") or MANIFEST_SCHEMA_VERSION,
            "config_hash": manifest_data.get("config_hash") or "",
            "dataset_release": manifest_data.get("dataset_release") or "",
            "evidence_refs": list(manifest_data.get("evidence_refs") or ()),
            "source_of_truth": INTERNAL_TRUTH_SOURCE,
            "no_real_operation_boundary": {
                "catalog_publish": 0,
                "lake_write": 0,
                "credential_read": 0,
                "qmt_operation": 0,
                "simulation_or_live": 0,
            },
        },
        status=CatalogStatus.PASS.value if validation.passed else CatalogStatus.BLOCKED.value,
        admission_candidate=validation.passed,
        allowed_claims=_claims_from_data(manifest_data.get("allowed_claims")),
        blocked_claims=tuple(_dedupe_claims(blocked_claims)),
        limitations=tuple(str(item) for item in manifest_data.get("limitations") or ()),
        evidence_refs=tuple(str(item) for item in manifest_data.get("evidence_refs") or ()),
    )


def validate_research_report_catalog_entry(
    entry: ResearchReportCatalog | Mapping[str, Any] | Any,
) -> ManifestValidationResult:
    data = _as_mapping(entry)
    if data is None:
        return _validation_result(
            "ResearchReportCatalog",
            "",
            (
                _reason(
                    MF_SCHEMA_REQUIRED_FIELD_MISSING,
                    "ResearchReportCatalog 必须是 dataclass 或 mapping",
                    field="catalog_entry",
                ),
            ),
        )
    reasons: list[ManifestBlockedReason] = []
    reasons.extend(_required_field_reasons(data, CATALOG_P0_FIELDS))
    reasons.extend(_artifact_path_reasons(data.get("artifact_paths"), field="artifact_paths"))
    reasons.extend(_claim_reasons(data))
    reasons.extend(_forbidden_truth_reasons(data))
    if data.get("admission_candidate") is True and str(data.get("status")) != CatalogStatus.PASS.value:
        reasons.append(
            _reason(
                MF_ADMISSION_NOT_READY,
                "admission_candidate=true 只能用于 status=pass 的 catalog entry",
                field="admission_candidate",
            )
        )
    return _validation_result("ResearchReportCatalog", str(data.get("catalog_entry_id") or ""), tuple(reasons))


def assert_manifest_ready_for_admission(
    manifest: ExperimentManifest | Mapping[str, Any] | Any,
    catalog_entry: ResearchReportCatalog | Mapping[str, Any] | Any,
) -> ManifestValidationResult:
    manifest_result = validate_experiment_manifest(manifest)
    catalog_result = validate_research_report_catalog_entry(catalog_entry)
    manifest_data = _as_mapping(manifest) or {}
    catalog_data = _as_mapping(catalog_entry) or {}
    reasons = list(manifest_result.blocked_reasons) + list(catalog_result.blocked_reasons)

    if catalog_data.get("admission_candidate") is not True:
        reasons.append(
            _reason(
                MF_ADMISSION_NOT_READY,
                "catalog entry 未标记为 admission_candidate，阻断 StrategyAdmissionPackage",
                field="admission_candidate",
            )
        )
    if manifest_data.get("run_id") and catalog_data.get("run_id") and manifest_data["run_id"] != catalog_data["run_id"]:
        reasons.append(
            _reason(
                MF_LINEAGE_MISSING,
                "manifest.run_id 与 catalog.run_id 不一致",
                field="run_id",
            )
        )
    return _validation_result("StrategyAdmissionPackageReadiness", str(manifest_data.get("run_id") or ""), tuple(reasons))


def query_research_report_catalog(
    catalog: ResearchReportCatalog | Mapping[str, Any] | Sequence[ResearchReportCatalog | Mapping[str, Any] | Any],
    filters: Mapping[str, Any] | None = None,
) -> tuple[ResearchReportCatalog, ...]:
    filter_data = dict(filters or {})
    entries = _catalog_entries(catalog)
    result: list[ResearchReportCatalog] = []
    for entry in entries:
        data = entry.to_dict()
        if filter_data.get("run_id") and data.get("run_id") != filter_data["run_id"]:
            continue
        if filter_data.get("report_id") and data.get("report_id") != filter_data["report_id"]:
            continue
        if filter_data.get("strategy_id") and data.get("strategy_id") != filter_data["strategy_id"]:
            continue
        if filter_data.get("factor_id") and str(filter_data["factor_id"]) not in set(data.get("factor_ids") or ()):
            continue
        result.append(entry)
    return tuple(result)


def resolve_research_catalog_paths(
    catalog_entry_id: str,
    output_root: str | Path = research_report_path("research_catalog"),
) -> ResearchCatalogArtifactPaths:
    root = Path(output_root)
    if "experiment_" in root.as_posix() or "factor_evaluation" in root.as_posix():
        raise ValueError(f"{MF_REPORT_ARTIFACT_PATH_FORBIDDEN}: {root.as_posix()}")
    if len(root.parts) < 2 or root.parts[-2:] != ("reports", "research_catalog"):
        root = root / "reports" / "research_catalog"
    safe_id = _safe_slug(catalog_entry_id)
    base = root / ARTIFACT_SCHEMA_VERSION / safe_id
    paths = ResearchCatalogArtifactPaths(
        json_path=base / "catalog_entry.json",
        csv_path=base / "catalog_entry.csv",
        markdown_path=base / "catalog_entry.md",
    )
    for path in paths.to_dict().values():
        normalised = Path(path).as_posix()
        if "/reports/research_catalog/" not in f"/{normalised}":
            raise ValueError(f"{MF_REPORT_ARTIFACT_PATH_FORBIDDEN}: {normalised}")
    return paths


def write_research_catalog_artifacts(
    entries: ResearchReportCatalog | Sequence[ResearchReportCatalog],
    paths: ResearchCatalogArtifactPaths,
) -> ResearchCatalogWriteResult:
    entry_tuple = (entries,) if isinstance(entries, ResearchReportCatalog) else tuple(entries)
    blocked: list[ManifestBlockedReason] = []
    for path in (paths.json_path, paths.csv_path, paths.markdown_path):
        if path.exists():
            blocked.append(
                _reason(
                    MF_REPORT_ARTIFACT_EXISTS,
                    f"目标 catalog artifact 已存在，禁止覆盖: {path.as_posix()}",
                    field="artifact_path",
                    evidence_ref=path.as_posix(),
                )
            )
    if blocked:
        return ResearchCatalogWriteResult(status=CatalogStatus.BLOCKED.value, artifact_refs=(), blocked_reasons=tuple(blocked))

    paths.json_path.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "schema_version": CATALOG_SCHEMA_VERSION,
        "entries": [entry.to_dict() for entry in entry_tuple],
    }
    paths.json_path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")

    with paths.csv_path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["catalog_entry_id", "report_id", "run_id", "strategy_id", "status", "admission_candidate", "artifact_paths"])
        for entry in entry_tuple:
            writer.writerow(
                [
                    entry.catalog_entry_id,
                    entry.report_id,
                    entry.run_id,
                    entry.strategy_id,
                    entry.status,
                    str(entry.admission_candidate).lower(),
                    "|".join(entry.artifact_paths),
                ]
            )

    paths.markdown_path.write_text(_render_catalog_markdown(entry_tuple), encoding="utf-8")
    return ResearchCatalogWriteResult(status=CatalogStatus.PASS.value, artifact_refs=tuple(paths.to_dict().values()))


def _catalog_entries(
    catalog: ResearchReportCatalog | Mapping[str, Any] | Sequence[ResearchReportCatalog | Mapping[str, Any] | Any],
) -> tuple[ResearchReportCatalog, ...]:
    if isinstance(catalog, ResearchReportCatalog):
        return (catalog,)
    if isinstance(catalog, Mapping):
        if isinstance(catalog.get("entries"), Sequence) and not isinstance(catalog.get("entries"), (str, bytes)):
            return tuple(_entry_from_mapping(item) for item in catalog["entries"])
        return (_entry_from_mapping(catalog),)
    if isinstance(catalog, Sequence) and not isinstance(catalog, (str, bytes, bytearray)):
        return tuple(_entry_from_mapping(item) for item in catalog)
    return ()


def _entry_from_mapping(value: ResearchReportCatalog | Mapping[str, Any] | Any) -> ResearchReportCatalog:
    if isinstance(value, ResearchReportCatalog):
        return value
    data = _as_mapping(value) or {}
    return ResearchReportCatalog(
        catalog_entry_id=str(data.get("catalog_entry_id") or ""),
        report_id=str(data.get("report_id") or ""),
        run_id=str(data.get("run_id") or ""),
        strategy_id=str(data.get("strategy_id") or ""),
        factor_ids=tuple(str(item) for item in data.get("factor_ids") or ()),
        artifact_paths=tuple(str(item) for item in data.get("artifact_paths") or ()),
        created_at=str(data.get("created_at") or ""),
        source_lineage=_mapping_or_empty(data.get("source_lineage")),
        status=str(data.get("status") or ""),
        admission_candidate=bool(data.get("admission_candidate")),
        allowed_claims=_claims_from_data(data.get("allowed_claims")),
        blocked_claims=_claims_from_data(data.get("blocked_claims")),
        limitations=tuple(str(item) for item in data.get("limitations") or ()),
        evidence_refs=tuple(str(item) for item in data.get("evidence_refs") or ()),
        schema_version=str(data.get("schema_version") or CATALOG_SCHEMA_VERSION),
        source_of_truth=str(data.get("source_of_truth") or INTERNAL_TRUTH_SOURCE),
    )


def _validation_result(
    object_type: str,
    object_id: str,
    reasons: Sequence[ManifestBlockedReason],
    counters: Mapping[str, int] | None = None,
) -> ManifestValidationResult:
    return ManifestValidationResult(
        status=CatalogStatus.BLOCKED.value if reasons else CatalogStatus.PASS.value,
        blocked_reasons=tuple(reasons),
        object_type=object_type,
        object_id=object_id,
        permission_counters=dict(counters or _zero_permission_counters()),
    )


def _required_field_reasons(data: Mapping[str, Any], required_fields: Sequence[str]) -> list[ManifestBlockedReason]:
    reasons: list[ManifestBlockedReason] = []
    for field_name in required_fields:
        if field_name not in data or _is_blank(data.get(field_name)):
            reasons.append(
                _reason(
                    MF_SCHEMA_REQUIRED_FIELD_MISSING,
                    f"必填字段缺失: {field_name}",
                    field=field_name,
                    remediation="补齐 P0 manifest/catalog 字段后再进入下游。",
                )
            )
    return reasons


def _artifact_path_reasons(paths: Any, field: str) -> list[ManifestBlockedReason]:
    if _is_blank(paths):
        return []
    if isinstance(paths, (str, bytes)):
        values = [str(paths)]
    elif isinstance(paths, Sequence):
        values = [str(item) for item in paths]
    else:
        return [_reason(MF_REPORT_ARTIFACT_PATH_FORBIDDEN, "artifact paths 必须是字符串列表", field=field)]
    reasons: list[ManifestBlockedReason] = []
    for value in values:
        lower = value.lower()
        if any(marker in lower for marker in FORBIDDEN_TRUTH_MARKERS):
            reasons.append(
                _reason(
                    MF_FORBIDDEN_TRUTH_SOURCE,
                    "MLflow / pickle recorder 不得作为默认 truth",
                    field=field,
                    evidence_ref=value,
                    remediation="改用 JSON / CSV / Markdown artifact 路径引用。",
                )
            )
        if "://" not in value and Path(value).suffix.lower() not in ALLOWED_ARTIFACT_SUFFIXES:
            reasons.append(
                _reason(
                    MF_REPORT_ARTIFACT_PATH_FORBIDDEN,
                    "catalog 只登记 JSON / CSV / Markdown artifact",
                    field=field,
                    evidence_ref=value,
                )
            )
    return reasons


def _claim_reasons(data: Mapping[str, Any]) -> list[ManifestBlockedReason]:
    reasons: list[ManifestBlockedReason] = []
    allowed = _claims_from_data(data.get("allowed_claims"))
    blocked = _claims_from_data(data.get("blocked_claims"))
    limitations = data.get("limitations") or ()
    if not allowed:
        reasons.append(_reason(MF_SCHEMA_REQUIRED_FIELD_MISSING, "allowed_claims 缺失", field="allowed_claims"))
    if not blocked:
        reasons.append(_reason(MF_SCHEMA_REQUIRED_FIELD_MISSING, "blocked_claims 缺失", field="blocked_claims"))
    if _is_blank(limitations):
        reasons.append(_reason(MF_SCHEMA_REQUIRED_FIELD_MISSING, "limitations 缺失", field="limitations"))
    for claim in allowed:
        if _contains_any(str(claim.claim), PRODUCTION_READY_MARKERS):
            reasons.append(
                _reason(
                    MF_ADMISSION_NOT_READY,
                    "manifest/catalog 不得声明 production truth、QMT-ready、simulation-ready 或 live-ready",
                    field="allowed_claims",
                    evidence_ref=claim.evidence_ref,
                )
            )
    return reasons


def _lineage_reasons(data: Mapping[str, Any]) -> list[ManifestBlockedReason]:
    reasons: list[ManifestBlockedReason] = []
    if _is_blank(data.get("evidence_refs")):
        reasons.append(_reason(MF_LINEAGE_MISSING, "evidence_refs 缺失", field="evidence_refs"))
    if _is_blank(data.get("dataset_release")):
        reasons.append(_reason(MF_LINEAGE_MISSING, "dataset_release 缺失", field="dataset_release"))
    return reasons


def _forbidden_truth_reasons(data: Mapping[str, Any], prefix: str = "") -> list[ManifestBlockedReason]:
    reasons: list[ManifestBlockedReason] = []
    for key, value in data.items():
        full_key = f"{prefix}.{key}" if prefix else str(key)
        if str(key) in {"source_of_truth", "truth_source", "recorder", "runtime", "provider", "provider_uri"}:
            if _contains_any(value, FORBIDDEN_TRUTH_MARKERS):
                reasons.append(
                    _reason(
                        MF_FORBIDDEN_TRUTH_SOURCE,
                        f"字段不得指向 MLflow / pickle recorder truth: {full_key}",
                        field=full_key,
                    )
                )
        if isinstance(value, Mapping):
            reasons.extend(_forbidden_truth_reasons(value, full_key))
        elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
            for index, item in enumerate(value):
                if isinstance(item, Mapping):
                    reasons.extend(_forbidden_truth_reasons(item, f"{full_key}[{index}]"))
                elif _contains_any(item, FORBIDDEN_TRUTH_MARKERS):
                    reasons.append(
                        _reason(
                            MF_FORBIDDEN_TRUTH_SOURCE,
                            f"字段不得包含 MLflow / pickle recorder truth: {full_key}[{index}]",
                            field=full_key,
                            evidence_ref=str(item),
                        )
                    )
        elif _contains_any(value, FORBIDDEN_TRUTH_MARKERS):
            reasons.append(
                _reason(
                    MF_FORBIDDEN_TRUTH_SOURCE,
                    f"字段不得包含 MLflow / pickle recorder truth: {full_key}",
                    field=full_key,
                    evidence_ref=str(value),
                )
            )
    return reasons


def _permission_counter_reasons(counters: Mapping[str, int]) -> list[ManifestBlockedReason]:
    reasons = []
    for key, value in counters.items():
        if int(value) != 0:
            reasons.append(
                _reason(
                    MF_PROVIDER_OR_LAKE_NOT_AUTHORIZED,
                    f"未授权操作计数必须为 0: {key}={value}",
                    field=f"permission_counters.{key}",
                    remediation="停止当前 admission/catalog 流程，回退独立授权或 CR。",
                )
            )
    return reasons


def _collect_claims(reports: Sequence[Mapping[str, Any]], field_name: str) -> tuple[ResearchClaim, ...]:
    claims: list[ResearchClaim] = []
    for report in reports:
        claims.extend(_claims_from_data(report.get(field_name)))
    return tuple(_dedupe_claims(claims))


def _collect_report_paths(reports: Sequence[Mapping[str, Any]], metadata: Mapping[str, Any]) -> tuple[str, ...]:
    paths: list[str] = [str(path) for path in metadata.get("report_paths") or []]
    for report in reports:
        artifact_paths = report.get("artifact_paths")
        if isinstance(artifact_paths, Mapping):
            paths.extend(str(path) for path in artifact_paths.values() if path)
        elif isinstance(artifact_paths, Sequence) and not isinstance(artifact_paths, (str, bytes)):
            paths.extend(str(path) for path in artifact_paths if path)
        elif artifact_paths:
            paths.append(str(artifact_paths))
        for field_name in ("json_path", "metrics_csv_path", "markdown_path", "report_path"):
            if report.get(field_name):
                paths.append(str(report[field_name]))
    return tuple(dict.fromkeys(paths))


def _collect_evidence_refs(reports: Sequence[Mapping[str, Any]], metadata: Mapping[str, Any]) -> tuple[str, ...]:
    refs: list[str] = [str(ref) for ref in metadata.get("evidence_refs") or []]
    for report in reports:
        refs.extend(str(ref) for ref in report.get("evidence_refs") or [])
    return tuple(dict.fromkeys(refs))


def _collect_limitations(reports: Sequence[Mapping[str, Any]], metadata: Mapping[str, Any]) -> tuple[str, ...]:
    limitations: list[str] = [str(item) for item in metadata.get("limitations") or []]
    for report in reports:
        limitations.extend(str(item) for item in report.get("limitations") or [])
        for claim in _claims_from_data(report.get("blocked_claims")):
            if claim.limitation:
                limitations.append(claim.limitation)
    return tuple(dict.fromkeys(limitations))


def _factor_versions(
    run_data: Mapping[str, Any],
    reports: Sequence[Mapping[str, Any]],
    plan_data: Mapping[str, Any],
    metadata: Mapping[str, Any],
) -> tuple[Mapping[str, Any], ...]:
    configured = metadata.get("factor_versions") or plan_data.get("factor_versions")
    if configured:
        if isinstance(configured, Mapping):
            return (_json_safe(configured),)
        return tuple(_json_safe(item) for item in configured)
    values: list[Mapping[str, Any]] = []
    if run_data.get("factor_id") or run_data.get("factor_version"):
        values.append({"factor_id": run_data.get("factor_id") or "", "version": run_data.get("factor_version") or ""})
    for report in reports:
        if report.get("factor_id") or report.get("factor_version"):
            values.append({"factor_id": report.get("factor_id") or "", "version": report.get("factor_version") or ""})
    deduped: dict[str, Mapping[str, Any]] = {}
    for value in values:
        deduped[f"{value.get('factor_id')}::{value.get('version')}"] = value
    return tuple(deduped.values())


def _factor_ids_from_manifest(data: Mapping[str, Any]) -> tuple[str, ...]:
    factor_ids = []
    for item in data.get("factor_versions") or ():
        if isinstance(item, Mapping) and item.get("factor_id"):
            factor_ids.append(str(item["factor_id"]))
    return tuple(dict.fromkeys(factor_ids))


def _normalise_report_refs(report_refs: Sequence[str] | Mapping[str, Any] | None) -> tuple[str, ...]:
    if report_refs is None:
        return ()
    if isinstance(report_refs, Mapping):
        if isinstance(report_refs.get("artifact_paths"), Mapping):
            return tuple(str(path) for path in report_refs["artifact_paths"].values() if path)
        return tuple(str(path) for path in report_refs.values() if path)
    return tuple(str(path) for path in report_refs)


def _first_report_id(manifest_data: Mapping[str, Any], artifact_paths: Sequence[str]) -> str:
    metadata = manifest_data.get("metadata") if isinstance(manifest_data.get("metadata"), Mapping) else {}
    if metadata.get("report_id"):
        return _safe_slug(str(metadata["report_id"]))
    if artifact_paths:
        parts = Path(artifact_paths[0]).parts
        if len(parts) >= 3 and parts[-1]:
            return _safe_slug(parts[-2] if parts[-2] != ARTIFACT_SCHEMA_VERSION else Path(artifact_paths[0]).stem)
    return _safe_slug(f"report-{manifest_data.get('run_id') or 'unknown'}")


def _claims_from_data(claims: Any) -> tuple[ResearchClaim, ...]:
    if not isinstance(claims, Sequence) or isinstance(claims, (str, bytes)):
        return ()
    result: list[ResearchClaim] = []
    for claim in claims:
        if isinstance(claim, ResearchClaim):
            result.append(claim)
        elif isinstance(claim, Mapping):
            result.append(
                ResearchClaim(
                    claim=str(claim.get("claim") or ""),
                    status=str(claim.get("status") or ""),
                    reason=str(claim.get("reason") or claim.get("message") or ""),
                    evidence_ref=str(claim.get("evidence_ref") or ""),
                    code=str(claim.get("code") or ""),
                    limitation=str(claim.get("limitation") or ""),
                )
            )
    return tuple(_dedupe_claims(result))


def _dedupe_claims(claims: Sequence[ResearchClaim]) -> list[ResearchClaim]:
    seen: set[tuple[str, str, str]] = set()
    result: list[ResearchClaim] = []
    for claim in claims:
        key = (claim.claim, claim.code, claim.evidence_ref)
        if key in seen:
            continue
        seen.add(key)
        result.append(claim)
    return result


def _normalise_permission_counters(counters: PermissionCounters | Mapping[str, Any] | Any | None = None) -> dict[str, int]:
    if isinstance(counters, PermissionCounters):
        source = counters.to_dict()
    elif isinstance(counters, Mapping):
        source = counters
    elif counters is not None and hasattr(counters, "to_dict"):
        source = counters.to_dict()
    else:
        source = {}
    return {key: int(source.get(key, 0) or 0) for key in FORBIDDEN_OPERATION_COUNTERS}


def _zero_permission_counters() -> dict[str, int]:
    return {key: 0 for key in FORBIDDEN_OPERATION_COUNTERS}


def _render_catalog_markdown(entries: Sequence[ResearchReportCatalog]) -> str:
    lines = [
        "# Research Report Catalog Entry",
        "",
        "本文件是 CR030-S06 离线研究报告索引，不是 lake current pointer，不触发 catalog publish。",
        "",
        "| catalog_entry_id | report_id | run_id | strategy_id | status | admission_candidate |",
        "|---|---|---|---|---|---|",
    ]
    for entry in entries:
        lines.append(
            f"| {entry.catalog_entry_id} | {entry.report_id} | {entry.run_id} | {entry.strategy_id} | "
            f"{entry.status} | {str(entry.admission_candidate).lower()} |"
        )
    lines.extend(
        [
            "",
            "## No-Real-Operation Boundary",
            "",
            "- catalog_publish = 0",
            "- lake_write = 0",
            "- credential_read = 0",
            "- qmt_operation = 0",
            "- simulation_or_live = 0",
        ]
    )
    return "\n".join(lines) + "\n"


def _reason(
    code: str,
    message: str,
    *,
    field: str = "",
    evidence_ref: str = "",
    remediation: str = "",
    severity: str = "blocker",
) -> ManifestBlockedReason:
    return ManifestBlockedReason(
        code=code,
        message=message,
        field=field,
        evidence_ref=evidence_ref,
        remediation=remediation,
        severity=severity,
    )


def _mapping_or_empty(value: Any) -> Mapping[str, Any]:
    if isinstance(value, Mapping):
        return _json_safe(value)
    return {}


def _as_mapping(value: Any) -> dict[str, Any] | None:
    if value is None:
        return None
    if is_dataclass(value):
        return _json_safe(asdict(value))
    if isinstance(value, Mapping):
        return _json_safe(dict(value))
    if hasattr(value, "to_dict"):
        converted = value.to_dict()
        if isinstance(converted, Mapping):
            return _json_safe(converted)
    if hasattr(value, "__dict__"):
        return _json_safe(vars(value))
    slots = getattr(type(value), "__slots__", ())
    if slots:
        return _json_safe({slot: getattr(value, slot) for slot in slots if hasattr(value, slot)})
    return None


def _json_safe(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value):
        return _json_safe(asdict(value))
    if isinstance(value, Mapping):
        return {str(key): _json_safe(value[key]) for key in sorted(value, key=lambda item: str(item))}
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Path):
        return value.as_posix()
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [_json_safe(item) for item in value]
    return str(value)


def _is_blank(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return value.strip() == ""
    if isinstance(value, Mapping):
        return len(value) == 0
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return len(value) == 0
    return False


def _contains_any(value: Any, markers: Sequence[str]) -> bool:
    text = json.dumps(_json_safe(value), ensure_ascii=False, sort_keys=True).lower()
    return any(marker.lower() in text for marker in markers)


def _safe_slug(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9_.-]+", "-", value.strip()).strip("-").lower()
    return slug or "unknown"


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
