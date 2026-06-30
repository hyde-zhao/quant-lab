"""CR139 golden baseline snapshot and comparison utilities.

The module is intentionally read-only for the market data lake. It consumes the
S01 remediation inventory, scans canonical parquet files, and writes only the
caller-provided output directory.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import pyarrow.parquet as pq

from .contracts import SCHEMA_VERSION
from .lake_layout import LakeLayout, ensure_path_outside_root
from .remediation_inventory import InventoryEntry, InventoryReport, build_inventory

GOLDEN_BASELINE_SCHEMA_VERSION = "golden_baseline_v1"
GOLDEN_DIFF_SCHEMA_VERSION = "golden_diff_v1"
GOLDEN_BASELINE_TOOL_VERSION = "cr139-s02-v0.1"
BASELINE_FILENAME = "golden-baseline-snapshot.json"
DIFF_FILENAME = "golden-diff-report.json"
DETERMINISTIC_FROZEN_AT = "1970-01-01T00:00:00+00:00"

ATTRIBUTION_STRUCTURAL_FIX = "structural_fix"
ATTRIBUTION_HISTORICAL_DATA_CHANGE = "historical_data_change"
ATTRIBUTION_AMBIGUOUS = "ambiguous"
ALLOWED_ATTRIBUTIONS = (
    ATTRIBUTION_STRUCTURAL_FIX,
    ATTRIBUTION_HISTORICAL_DATA_CHANGE,
    ATTRIBUTION_AMBIGUOUS,
)

FORBIDDEN_OPERATION_COUNTS: dict[str, int] = {
    "provider_fetch": 0,
    "lake_write": 0,
    "catalog_write": 0,
    "current_pointer_publish": 0,
    "credential_read": 0,
}


@dataclass(frozen=True, slots=True)
class MetricSpec:
    metric_id: str
    dimension: str
    datasets: tuple[str, ...]
    structural_relevance: str
    structural_story: str | None
    description: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


MINIMUM_METRIC_SPECS: tuple[MetricSpec, ...] = (
    MetricSpec("row_count", "data_scale", ("*",), "low", None, "Canonical parquet total row count."),
    MetricSpec(
        "unique_key_dup_count",
        "uniqueness",
        ("prices", "financial_pit", "market_cap"),
        "high",
        "CR139-S07",
        "Duplicate count for the (symbol, trade_date) key.",
    ),
    MetricSpec(
        "partition_digest",
        "partition_structure",
        ("*",),
        "high",
        "CR139-S08",
        "Deterministic digest of run_id partitions and parquet content.",
    ),
    MetricSpec(
        "pit_reader_summary",
        "pit_semantics",
        ("financial_pit", "market_cap", "events"),
        "high",
        "CR139-S05",
        "Available-at summary over deterministic as-of samples.",
    ),
    MetricSpec(
        "published_unavailable_count",
        "published_gate",
        ("*",),
        "high",
        "CR139-S04",
        "Count of datasets unavailable through the published gate.",
    ),
    MetricSpec(
        "benchmark_window_symbol_set",
        "benchmark_sample",
        ("prices", "hs300_index"),
        "medium",
        None,
        "Hash of the deterministic benchmark window symbol set.",
    ),
    MetricSpec(
        "panel_join_row_count",
        "panel_join",
        ("feature_panel",),
        "high",
        "CR139-S06",
        "Inner join row count for prices x financial_pit x market_cap.",
    ),
)
MINIMUM_METRIC_IDS = tuple(spec.metric_id for spec in MINIMUM_METRIC_SPECS)


@dataclass(frozen=True, slots=True)
class GoldenMetric:
    metric_id: str
    value: Any
    structural_relevance: str
    evidence: dict[str, Any] = field(default_factory=dict)
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class GoldenDatasetSnapshot:
    dataset: str
    row_count: int
    coverage: dict[str, Any]
    metrics: list[GoldenMetric] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["metrics"] = [metric.to_dict() for metric in self.metrics]
        return payload


@dataclass(frozen=True, slots=True)
class GoldenBaselineSnapshot:
    schema_version: str
    snapshot_id: str
    frozen_at: str
    lake_root: str
    tool_version: str
    source_inventory_id: str
    metric_spec_ids: list[str]
    datasets: list[GoldenDatasetSnapshot]
    operation_counts: dict[str, int] = field(default_factory=lambda: dict(FORBIDDEN_OPERATION_COUNTS))

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["datasets"] = [dataset.to_dict() for dataset in self.datasets]
        return payload

    def to_json(self) -> str:
        return _json_dumps(self.to_dict())


@dataclass(frozen=True, slots=True)
class StructuralChangeRef:
    story_id: str
    metric_ids: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class GoldenDiff:
    dataset: str
    metric_id: str
    baseline_value: Any
    current_value: Any
    delta: Any
    attribution: str
    evidence: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class GoldenDiffReport:
    schema_version: str
    baseline_snapshot_id: str
    current_snapshot_id: str
    compared_at: str
    diffs: list[GoldenDiff]
    ambiguous_rate: float
    status: str
    operation_counts: dict[str, int] = field(default_factory=lambda: dict(FORBIDDEN_OPERATION_COUNTS))

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["diffs"] = [diff.to_dict() for diff in self.diffs]
        return payload

    def to_json(self) -> str:
        return _json_dumps(self.to_dict())


def freeze_golden_baseline(
    lake_root: str | Path,
    inventory: InventoryReport | None = None,
    metric_specs: Sequence[MetricSpec] | None = None,
    out_dir: str | Path | None = None,
    *,
    frozen_at: str = DETERMINISTIC_FROZEN_AT,
) -> GoldenBaselineSnapshot:
    """Build a deterministic GoldenBaselineSnapshot from canonical parquet."""

    layout = LakeLayout(lake_root)
    source_inventory = inventory or build_inventory(layout.lake_root, scanned_at=frozen_at)
    specs = tuple(metric_specs or MINIMUM_METRIC_SPECS)
    dataset_snapshots: list[GoldenDatasetSnapshot] = []
    for entry in sorted(source_inventory.entries, key=lambda item: item.dataset):
        dataset_snapshots.append(_freeze_dataset(layout, entry, specs))
    snapshot = GoldenBaselineSnapshot(
        schema_version=GOLDEN_BASELINE_SCHEMA_VERSION,
        snapshot_id=_snapshot_id(source_inventory, dataset_snapshots, frozen_at),
        frozen_at=frozen_at,
        lake_root=source_inventory.lake_root_label,
        tool_version=GOLDEN_BASELINE_TOOL_VERSION,
        source_inventory_id=_inventory_id(source_inventory),
        metric_spec_ids=sorted(spec.metric_id for spec in specs),
        datasets=dataset_snapshots,
    )
    if out_dir is not None:
        write_baseline_snapshot(snapshot, out_dir)
    return snapshot


def compare_golden_baselines(
    baseline: GoldenBaselineSnapshot | Mapping[str, Any] | str | Path,
    current: GoldenBaselineSnapshot | Mapping[str, Any] | str | Path,
    structural_changes: Sequence[StructuralChangeRef | Mapping[str, Any] | str] | None = None,
    *,
    compared_at: str = DETERMINISTIC_FROZEN_AT,
) -> GoldenDiffReport:
    base = load_baseline_snapshot(baseline)
    curr = load_baseline_snapshot(current)
    if base.schema_version != curr.schema_version:
        raise ValueError(f"snapshot schema mismatch: {base.schema_version} != {curr.schema_version}")

    changes = _normalise_structural_changes(structural_changes or ())
    diffs: list[GoldenDiff] = []
    for key in sorted(set(_metric_map(base)) | set(_metric_map(curr))):
        base_metric = _metric_map(base).get(key)
        curr_metric = _metric_map(curr).get(key)
        base_value = base_metric.value if base_metric is not None else None
        curr_value = curr_metric.value if curr_metric is not None else None
        if base_value == curr_value:
            continue
        dataset, metric_id = key
        attribution, evidence = _attribute_diff(metric_id, base_metric, curr_metric, changes)
        diffs.append(
            GoldenDiff(
                dataset=dataset,
                metric_id=metric_id,
                baseline_value=base_value,
                current_value=curr_value,
                delta=_delta(base_value, curr_value),
                attribution=attribution,
                evidence=evidence,
            )
        )

    ambiguous_count = sum(1 for diff in diffs if diff.attribution == ATTRIBUTION_AMBIGUOUS)
    ambiguous_rate = round(ambiguous_count / len(diffs), 6) if diffs else 0.0
    return GoldenDiffReport(
        schema_version=GOLDEN_DIFF_SCHEMA_VERSION,
        baseline_snapshot_id=base.snapshot_id,
        current_snapshot_id=curr.snapshot_id,
        compared_at=compared_at,
        diffs=diffs,
        ambiguous_rate=ambiguous_rate,
        status="WARN" if ambiguous_rate > 0.05 else "PASS",
    )


def write_baseline_snapshot(
    snapshot: GoldenBaselineSnapshot,
    out_dir: str | Path,
    *,
    forbidden_root: str | Path | None = None,
) -> Path:
    target = Path(out_dir)
    if forbidden_root is not None:
        target = ensure_path_outside_root(target, forbidden_root)
    target.mkdir(parents=True, exist_ok=True)
    path = target / BASELINE_FILENAME
    path.write_text(snapshot.to_json(), encoding="utf-8")
    return path


def write_diff_report(
    report: GoldenDiffReport,
    out_path: str | Path,
    *,
    forbidden_root: str | Path | None = None,
) -> Path:
    path = Path(out_path)
    if forbidden_root is not None:
        path = ensure_path_outside_root(path, forbidden_root)
    if path.suffix:
        path.parent.mkdir(parents=True, exist_ok=True)
        target = path
    else:
        path.mkdir(parents=True, exist_ok=True)
        target = path / DIFF_FILENAME
    target.write_text(report.to_json(), encoding="utf-8")
    return target


def load_baseline_snapshot(value: GoldenBaselineSnapshot | Mapping[str, Any] | str | Path) -> GoldenBaselineSnapshot:
    if isinstance(value, GoldenBaselineSnapshot):
        return value
    if isinstance(value, Mapping):
        return _snapshot_from_dict(value)
    path = Path(value)
    if path.is_dir():
        path = path / BASELINE_FILENAME
    return _snapshot_from_dict(json.loads(path.read_text(encoding="utf-8")))


def format_snapshot_summary(snapshot: GoldenBaselineSnapshot) -> str:
    rows = ["dataset\tmetrics\trow_count\tcoverage"]
    for dataset in snapshot.datasets:
        metric_ids = ",".join(metric.metric_id for metric in dataset.metrics)
        coverage = f"{dataset.coverage.get('start') or '-'}..{dataset.coverage.get('end') or '-'}"
        rows.append(f"{dataset.dataset}\t{metric_ids}\t{dataset.row_count}\t{coverage}")
    return "\n".join(rows) + "\n"


def format_diff_summary(report: GoldenDiffReport) -> str:
    rows = ["dataset\tmetric\tattribution\tbaseline\tcurrent"]
    for diff in report.diffs:
        rows.append(
            "\t".join(
                [
                    diff.dataset,
                    diff.metric_id,
                    diff.attribution,
                    json.dumps(diff.baseline_value, sort_keys=True),
                    json.dumps(diff.current_value, sort_keys=True),
                ]
            )
        )
    rows.append(f"ambiguous_rate\t{report.ambiguous_rate}")
    rows.append(f"status\t{report.status}")
    return "\n".join(rows) + "\n"


def _freeze_dataset(
    layout: LakeLayout,
    entry: InventoryEntry,
    specs: Sequence[MetricSpec],
) -> GoldenDatasetSnapshot:
    paths = _canonical_paths(layout.canonical_dataset_root(entry.dataset, entry.schema_version))
    columns = _columns_present(paths)
    metrics: list[GoldenMetric] = []
    for spec in specs:
        if not _spec_applies(spec, entry.dataset):
            continue
        try:
            value, evidence = _compute_metric(spec, layout, entry, paths, columns)
            metrics.append(
                GoldenMetric(
                    metric_id=spec.metric_id,
                    value=value,
                    structural_relevance=spec.structural_relevance,
                    evidence=evidence,
                )
            )
        except Exception as exc:  # pragma: no cover - exercised by defensive runtime paths
            metrics.append(
                GoldenMetric(
                    metric_id=spec.metric_id,
                    value=None,
                    structural_relevance=spec.structural_relevance,
                    evidence={"dataset": entry.dataset},
                    error=f"{type(exc).__name__}: {exc}",
                )
            )
    return GoldenDatasetSnapshot(
        dataset=entry.dataset,
        row_count=entry.row_count,
        coverage={"start": entry.coverage_start, "end": entry.coverage_end},
        metrics=sorted(metrics, key=lambda item: item.metric_id),
    )


def _compute_metric(
    spec: MetricSpec,
    layout: LakeLayout,
    entry: InventoryEntry,
    paths: Sequence[Path],
    columns: Sequence[str],
) -> tuple[Any, dict[str, Any]]:
    if spec.metric_id == "row_count":
        return entry.row_count, {"source": "S01 InventoryEntry.row_count"}
    if spec.metric_id == "unique_key_dup_count":
        return entry.duplicate_key_count, {"key_schema": entry.key_schema, "applicable": entry.key_check_applicable}
    if spec.metric_id == "partition_digest":
        return _partition_digest(paths, layout.lake_root), {"partition_count": entry.partition_count}
    if spec.metric_id == "pit_reader_summary":
        return _pit_reader_summary(paths, columns, entry), {"sample_policy": "coverage start/mid/end"}
    if spec.metric_id == "published_unavailable_count":
        value = 0 if entry.published else 1
        return value, {"published": entry.published, "reader_reject_count": value}
    if spec.metric_id == "benchmark_window_symbol_set":
        return _benchmark_window_symbol_set(paths, columns, entry), {"sample_policy": "coverage window symbol set"}
    if spec.metric_id == "panel_join_row_count":
        return _panel_join_row_count(layout), {"source_datasets": ["prices", "financial_pit", "market_cap"]}
    raise ValueError(f"unsupported metric spec: {spec.metric_id}")


def _canonical_paths(root: Path) -> list[Path]:
    if not root.exists():
        return []
    return sorted(path for path in root.rglob("*.parquet") if ".tmp" not in path.name)


def _columns_present(paths: Sequence[Path]) -> list[str]:
    columns: set[str] = set()
    for path in paths:
        columns.update(pq.ParquetFile(path).schema_arrow.names)
    return sorted(columns)


def _table_to_pandas(paths: Sequence[Path], columns: Sequence[str] | None = None):
    import pandas as pd

    frames = []
    for path in paths:
        table = pq.read_table(path, columns=list(columns) if columns is not None else None)
        frames.append(table.to_pandas())
    if not frames:
        return pd.DataFrame(columns=list(columns or ()))
    return pd.concat(frames, ignore_index=True)


def _partition_digest(paths: Sequence[Path], lake_root: Path) -> dict[str, Any]:
    rows: list[str] = []
    source_run_ids: set[str] = set()
    for path in paths:
        relative = _relative_to_lake(path, lake_root)
        file_hash = hashlib.sha256(path.read_bytes()).hexdigest()
        rows.append(f"{relative}:{file_hash}")
        for part in path.parts:
            if part.startswith("run_id="):
                source_run_ids.add(part.split("=", 1)[1])
    digest = hashlib.sha256("\n".join(sorted(rows)).encode("utf-8")).hexdigest()
    return {
        "file_count": len(paths),
        "source_run_ids": sorted(source_run_ids),
        "digest": digest,
    }


def _pit_reader_summary(paths: Sequence[Path], columns: Sequence[str], entry: InventoryEntry) -> dict[str, Any]:
    if not paths:
        return {"as_of_samples": [], "available_count": 0, "future_filtered_count": 0, "available_at_present": False}
    if "available_at" not in set(columns):
        return {
            "as_of_samples": _as_of_samples(entry),
            "available_count": entry.row_count,
            "future_filtered_count": 0,
            "available_at_present": False,
        }
    frame = _table_to_pandas(paths, ["available_at"])
    samples = _as_of_samples(entry)
    if not samples:
        samples = sorted(str(value)[:10].replace("-", "") for value in frame["available_at"].dropna().tolist())[:1]
    as_of = samples[-1] if samples else ""
    normalized = frame["available_at"].astype(str).str.slice(0, 10).str.replace("-", "", regex=False)
    available_count = int((normalized <= as_of).sum()) if as_of else int(len(frame))
    future_filtered_count = int((normalized > as_of).sum()) if as_of else 0
    return {
        "as_of_samples": samples,
        "available_count": available_count,
        "future_filtered_count": future_filtered_count,
        "available_at_present": True,
    }


def _benchmark_window_symbol_set(paths: Sequence[Path], columns: Sequence[str], entry: InventoryEntry) -> dict[str, Any]:
    if "symbol" not in set(columns) or not paths:
        symbols = [entry.dataset] if entry.row_count else []
    else:
        frame = _table_to_pandas(paths, ["symbol"])
        symbols = sorted(str(value) for value in frame["symbol"].dropna().unique().tolist())
    digest = hashlib.sha256("\n".join(symbols).encode("utf-8")).hexdigest()
    return {
        "coverage": {"start": entry.coverage_start, "end": entry.coverage_end},
        "symbol_count": len(symbols),
        "symbol_hash": digest,
    }


def _panel_join_row_count(layout: LakeLayout) -> int:
    import pandas as pd

    frames = {}
    for dataset in ("prices", "financial_pit", "market_cap"):
        paths = _canonical_paths(layout.canonical_dataset_root(dataset, SCHEMA_VERSION))
        columns = _columns_present(paths)
        required = {"symbol", "trade_date"}
        if not paths or not required.issubset(columns):
            return 0
        frames[dataset] = _table_to_pandas(paths, ["symbol", "trade_date"]).drop_duplicates()
    joined = pd.merge(frames["prices"], frames["financial_pit"], on=["symbol", "trade_date"], how="inner")
    joined = pd.merge(joined, frames["market_cap"], on=["symbol", "trade_date"], how="inner")
    return int(len(joined))


def _as_of_samples(entry: InventoryEntry) -> list[str]:
    start = entry.coverage_start
    end = entry.coverage_end
    if not start and not end:
        return []
    if start == end or not end:
        return [start] if start else [end]  # type: ignore[list-item]
    mid = start
    return [value for value in (start, mid, end) if value]


def _spec_applies(spec: MetricSpec, dataset: str) -> bool:
    return "*" in spec.datasets or dataset in spec.datasets


def _metric_map(snapshot: GoldenBaselineSnapshot) -> dict[tuple[str, str], GoldenMetric]:
    return {
        (dataset.dataset, metric.metric_id): metric
        for dataset in snapshot.datasets
        for metric in dataset.metrics
    }


def _attribute_diff(
    metric_id: str,
    baseline: GoldenMetric | None,
    current: GoldenMetric | None,
    changes: Sequence[StructuralChangeRef],
) -> tuple[str, dict[str, Any]]:
    structural_story = _structural_story_for_metric(metric_id)
    story_ids = {change.story_id for change in changes}
    change_metric_ids = {metric_id for change in changes for metric_id in change.metric_ids}
    if structural_story and (structural_story in story_ids or metric_id in change_metric_ids):
        return ATTRIBUTION_STRUCTURAL_FIX, {"structural_change_story": structural_story}
    if metric_id in {"row_count", "benchmark_window_symbol_set"}:
        if changes and metric_id == "row_count":
            return ATTRIBUTION_STRUCTURAL_FIX, {"structural_change_story": sorted(story_ids)}
        return ATTRIBUTION_HISTORICAL_DATA_CHANGE, {"historical_window_change": True}
    if changes and baseline and current and (
        baseline.structural_relevance == "high" or current.structural_relevance == "high"
    ):
        return ATTRIBUTION_STRUCTURAL_FIX, {"structural_change_story": sorted(story_ids)}
    if baseline and current and _coverage_changed(baseline.evidence, current.evidence):
        return ATTRIBUTION_HISTORICAL_DATA_CHANGE, {"historical_window_change": True}
    return ATTRIBUTION_AMBIGUOUS, {"structural_change_story": structural_story, "historical_window_change": False}


def _coverage_changed(base_evidence: Mapping[str, Any], curr_evidence: Mapping[str, Any]) -> bool:
    return base_evidence.get("coverage") != curr_evidence.get("coverage")


def _structural_story_for_metric(metric_id: str) -> str | None:
    for spec in MINIMUM_METRIC_SPECS:
        if spec.metric_id == metric_id:
            return spec.structural_story
    return None


def _normalise_structural_changes(
    values: Sequence[StructuralChangeRef | Mapping[str, Any] | str],
) -> list[StructuralChangeRef]:
    changes: list[StructuralChangeRef] = []
    for value in values:
        if isinstance(value, StructuralChangeRef):
            changes.append(value)
        elif isinstance(value, str):
            changes.append(StructuralChangeRef(story_id=value))
        else:
            metric_ids = tuple(str(item) for item in value.get("metric_ids", ()))
            story_id = str(value.get("story_id") or value.get("id") or "")
            if story_id:
                changes.append(StructuralChangeRef(story_id=story_id, metric_ids=metric_ids))
    return changes


def _delta(base_value: Any, curr_value: Any) -> Any:
    if isinstance(base_value, (int, float)) and isinstance(curr_value, (int, float)):
        return curr_value - base_value
    return {"changed": base_value != curr_value}


def _snapshot_id(
    inventory: InventoryReport,
    datasets: Sequence[GoldenDatasetSnapshot],
    frozen_at: str,
) -> str:
    payload = {
        "frozen_at": frozen_at,
        "inventory_id": _inventory_id(inventory),
        "datasets": [dataset.to_dict() for dataset in datasets],
        "tool_version": GOLDEN_BASELINE_TOOL_VERSION,
    }
    return hashlib.sha256(_json_dumps(payload).encode("utf-8")).hexdigest()


def _inventory_id(inventory: InventoryReport) -> str:
    payload = inventory.to_dict()
    payload.pop("scanned_at", None)
    return hashlib.sha256(_json_dumps(payload).encode("utf-8")).hexdigest()


def _snapshot_from_dict(payload: Mapping[str, Any]) -> GoldenBaselineSnapshot:
    datasets = [
        GoldenDatasetSnapshot(
            dataset=str(item["dataset"]),
            row_count=int(item.get("row_count", 0)),
            coverage=dict(item.get("coverage", {})),
            metrics=[
                GoldenMetric(
                    metric_id=str(metric["metric_id"]),
                    value=metric.get("value"),
                    structural_relevance=str(metric.get("structural_relevance", "")),
                    evidence=dict(metric.get("evidence", {})),
                    error=metric.get("error"),
                )
                for metric in item.get("metrics", [])
            ],
        )
        for item in payload.get("datasets", [])
    ]
    return GoldenBaselineSnapshot(
        schema_version=str(payload["schema_version"]),
        snapshot_id=str(payload["snapshot_id"]),
        frozen_at=str(payload["frozen_at"]),
        lake_root=str(payload["lake_root"]),
        tool_version=str(payload["tool_version"]),
        source_inventory_id=str(payload["source_inventory_id"]),
        metric_spec_ids=list(payload.get("metric_spec_ids", [])),
        datasets=datasets,
        operation_counts=dict(payload.get("operation_counts", FORBIDDEN_OPERATION_COUNTS)),
    )


def _relative_to_lake(path: Path, lake_root: Path) -> str:
    try:
        return str(path.relative_to(lake_root))
    except ValueError:
        return str(path)


def _json_dumps(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


__all__ = [
    "ALLOWED_ATTRIBUTIONS",
    "BASELINE_FILENAME",
    "DIFF_FILENAME",
    "GOLDEN_BASELINE_SCHEMA_VERSION",
    "GOLDEN_BASELINE_TOOL_VERSION",
    "GOLDEN_DIFF_SCHEMA_VERSION",
    "MINIMUM_METRIC_IDS",
    "MINIMUM_METRIC_SPECS",
    "GoldenBaselineSnapshot",
    "GoldenDatasetSnapshot",
    "GoldenDiff",
    "GoldenDiffReport",
    "GoldenMetric",
    "MetricSpec",
    "StructuralChangeRef",
    "compare_golden_baselines",
    "format_diff_summary",
    "format_snapshot_summary",
    "freeze_golden_baseline",
    "load_baseline_snapshot",
    "write_baseline_snapshot",
    "write_diff_report",
]
