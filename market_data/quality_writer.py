"""Partitioned quality report writer for CR139 quality path reorganization."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, Mapping

from .lake_layout import LakeLayout, ensure_parent_dirs_for_write

QUALITY_WRITE_MODE_OFFICIAL = "official"
QUALITY_WRITE_MODE_SMOKE = "smoke"
QUALITY_WRITE_MODE_PROBE = "probe"
QUALITY_WRITE_MODES = frozenset({QUALITY_WRITE_MODE_OFFICIAL, QUALITY_WRITE_MODE_SMOKE, QUALITY_WRITE_MODE_PROBE})


@dataclass(frozen=True, slots=True)
class QualityWriteRequest:
    dataset: str
    run_id: str
    as_of_date: str
    payload: Mapping[str, Any]
    mode: str = QUALITY_WRITE_MODE_OFFICIAL
    filename: str = "quality.json"


@dataclass(frozen=True, slots=True)
class QualityWriteResult:
    dataset: str
    run_id: str
    as_of_date: str
    mode: str
    path: Path
    scratch: bool
    operation_counters: dict[str, int]

    def to_dict(self) -> dict[str, Any]:
        return {
            "dataset": self.dataset,
            "run_id": self.run_id,
            "as_of_date": self.as_of_date,
            "mode": self.mode,
            "path": self.path.as_posix(),
            "scratch": self.scratch,
            "operation_counters": dict(self.operation_counters),
        }


def quality_partition_path(layout: LakeLayout | str | Path, request: QualityWriteRequest) -> Path:
    """Return the CR139 quality partition path without writing."""

    layout = layout if isinstance(layout, LakeLayout) else LakeLayout(layout)
    dataset = _safe_segment(request.dataset, "dataset")
    run_id = _safe_segment(request.run_id, "run_id")
    as_of_date = _normalise_date(request.as_of_date)
    filename = _safe_filename(request.filename)
    mode = str(request.mode)
    if mode not in QUALITY_WRITE_MODES:
        raise ValueError(f"unsupported_quality_write_mode: {mode}")
    if mode == QUALITY_WRITE_MODE_OFFICIAL:
        return layout.quality_root / dataset / as_of_date / f"{run_id}-{filename}"
    return layout.quality_root / "_scratch" / run_id / f"{dataset}-{as_of_date}-{filename}"


def write_partitioned_quality_report(
    layout: LakeLayout | str | Path,
    request: QualityWriteRequest,
) -> QualityWriteResult:
    """Write a JSON quality report to the partitioned quality path."""

    path = quality_partition_path(layout, request)
    body = {
        "dataset": str(request.dataset),
        "run_id": str(request.run_id),
        "as_of_date": _normalise_date(request.as_of_date),
        "mode": str(request.mode),
        "payload": dict(request.payload),
    }
    text = json.dumps(body, ensure_ascii=True, sort_keys=True, indent=2) + "\n"
    tmp_path = path.with_name(path.name + ".tmp")
    ensure_parent_dirs_for_write(tmp_path)
    with tmp_path.open("w", encoding="utf-8") as fh:
        fh.write(text)
        fh.flush()
        os.fsync(fh.fileno())
    tmp_path.replace(path)
    mode = str(request.mode)
    return QualityWriteResult(
        dataset=str(request.dataset),
        run_id=str(request.run_id),
        as_of_date=_normalise_date(request.as_of_date),
        mode=mode,
        path=path,
        scratch=mode != QUALITY_WRITE_MODE_OFFICIAL,
        operation_counters={
            "quality_file_write": 1,
            "catalog_write": 0,
            "manifest_write": 0,
            "pointer_advance": 0,
            "provider_fetch": 0,
            "runtime_operation": 0,
        },
    )


def _normalise_date(value: str) -> str:
    text = str(value).strip()
    if not text:
        raise ValueError("quality_write_required_field_missing: as_of_date")
    if len(text) == 8 and text.isdigit():
        return date(int(text[:4]), int(text[4:6]), int(text[6:8])).isoformat()
    if len(text) >= 10 and text[4] == "-" and text[7] == "-":
        return date.fromisoformat(text[:10]).isoformat()
    raise ValueError(f"invalid_quality_as_of_date: {text}")


def _safe_segment(value: str, field: str) -> str:
    text = str(value).strip()
    if not text:
        raise ValueError(f"quality_write_required_field_missing: {field}")
    if text in {".", ".."} or "/" in text or "\\" in text:
        raise ValueError(f"unsafe_quality_path_segment: {field}")
    return text


def _safe_filename(value: str) -> str:
    text = _safe_segment(value, "filename")
    if text.endswith(".tmp"):
        raise ValueError("unsafe_quality_path_segment: filename")
    return text


__all__ = [
    "QUALITY_WRITE_MODE_OFFICIAL",
    "QUALITY_WRITE_MODE_PROBE",
    "QUALITY_WRITE_MODE_SMOKE",
    "QUALITY_WRITE_MODES",
    "QualityWriteRequest",
    "QualityWriteResult",
    "quality_partition_path",
    "write_partitioned_quality_report",
]
