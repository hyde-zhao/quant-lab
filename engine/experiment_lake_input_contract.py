"""CR139 experiment lake input contract helpers.

The helpers in this module adapt experiment scripts to the PIT lake reader
contract without authorizing real provider, catalog, lake write, or runtime
operations. Tests may inject fixture frames explicitly; production entrypoints
must provide an explicit lake root and as-of time.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Mapping

import pandas as pd

from engine.multifactor_contracts import FORBIDDEN_OPERATION_COUNTERS
from market_data.contracts import DATASET_INDEX_MEMBERS, DATASET_KEY_COLUMNS, DATASET_PRICES, DATASET_TRADE_CALENDAR
from market_data.readers import ReaderResult, read_panel_as_of


EXPERIMENT_REQUIRED_DATASETS = (DATASET_PRICES, DATASET_INDEX_MEMBERS, DATASET_TRADE_CALENDAR)
EXPERIMENT_FRAME_KEYS = {
    DATASET_PRICES: "prices",
    DATASET_INDEX_MEMBERS: "index_members",
    DATASET_TRADE_CALENDAR: "trade_calendar",
}
EXPERIMENT_PIT_KEYS = {
    DATASET_PRICES: DATASET_KEY_COLUMNS[DATASET_PRICES],
    DATASET_INDEX_MEMBERS: DATASET_KEY_COLUMNS[DATASET_INDEX_MEMBERS],
    DATASET_TRADE_CALENDAR: DATASET_KEY_COLUMNS[DATASET_TRADE_CALENDAR],
}


@dataclass(frozen=True, slots=True)
class ExperimentLakeInputRequest:
    lake_root: str | Path
    as_of: str
    start_date: str | None = None
    end_date: str | None = None
    symbols: tuple[str, ...] | None = None
    quality_policy: str = "require_pass"

    def to_dict(self) -> dict[str, Any]:
        return {
            "lake_root": str(self.lake_root),
            "as_of": self.as_of,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "symbols": list(self.symbols) if self.symbols is not None else None,
            "quality_policy": self.quality_policy,
        }


@dataclass(frozen=True, slots=True)
class ExperimentLakeInputResult:
    request: ExperimentLakeInputRequest
    frames: Mapping[str, pd.DataFrame]
    dataset_status: Mapping[str, str]
    source_lineage: Mapping[str, Any]
    permission_counters: Mapping[str, int] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "request": self.request.to_dict(),
            "dataset_status": dict(self.dataset_status),
            "source_lineage": dict(self.source_lineage),
            "permission_counters": dict(self.permission_counters),
            "frame_rows": {key: int(frame.shape[0]) for key, frame in self.frames.items()},
        }


ReaderFn = Callable[..., ReaderResult]


def add_experiment_lake_args(parser: Any, *, required: bool = True) -> None:
    parser.add_argument("--lake-root", required=required, help="显式传入只读 lake root；禁止默认仓库数据目录。")
    parser.add_argument("--as-of", required=required, help="PIT 决策时间，所有输入必须 available_at <= as_of。")
    parser.add_argument("--quality-policy", default="require_pass")


def load_experiment_lake_frames(
    args: Any,
    *,
    reader: ReaderFn = read_panel_as_of,
) -> ExperimentLakeInputResult:
    request = _request_from_args(args)
    fixture_frames = _fixture_frames(args)
    if fixture_frames is not None:
        return ExperimentLakeInputResult(
            request=request,
            frames=fixture_frames,
            dataset_status={dataset: "fixture" for dataset in EXPERIMENT_REQUIRED_DATASETS},
            source_lineage={
                "input_mode": "explicit_fixture_frames",
                "as_of": request.as_of,
                "datasets": list(EXPERIMENT_REQUIRED_DATASETS),
                "reader_contract": "read_panel_as_of",
            },
            permission_counters=_zero_permission_counters(),
        )

    frames: dict[str, pd.DataFrame] = {}
    statuses: dict[str, str] = {}
    issues: list[dict[str, Any]] = []
    filters = _reader_filters(request)
    for dataset in EXPERIMENT_REQUIRED_DATASETS:
        result = reader(
            dataset,
            request.lake_root,
            as_of=request.as_of,
            keys=EXPERIMENT_PIT_KEYS[dataset],
            filters=filters,
            quality_policy=request.quality_policy,
            required=True,
        )
        statuses[dataset] = result.status
        issues.extend(dict(item) for item in result.issues)
        if result.status != "available" or result.frame is None:
            issue_codes = ",".join(str(item.get("code") or "") for item in result.issues) or result.status
            raise ValueError(f"lake input unavailable: dataset={dataset} status={result.status} issues={issue_codes}")
        frames[EXPERIMENT_FRAME_KEYS[dataset]] = _normalise_experiment_frame(dataset, result.frame)

    return ExperimentLakeInputResult(
        request=request,
        frames=frames,
        dataset_status=statuses,
        source_lineage={
            "input_mode": "read_panel_as_of",
            "as_of": request.as_of,
            "datasets": list(EXPERIMENT_REQUIRED_DATASETS),
            "issues": issues,
        },
        permission_counters=_zero_permission_counters(),
    )


def _normalise_experiment_frame(dataset: str, frame: pd.DataFrame) -> pd.DataFrame:
    work = frame.copy()
    if dataset == DATASET_INDEX_MEMBERS and "symbol" not in work.columns and "con_code" in work.columns:
        work["symbol"] = work["con_code"]
    return work


def _request_from_args(args: Any) -> ExperimentLakeInputRequest:
    lake_root = getattr(args, "lake_root", None)
    as_of = getattr(args, "as_of", None)
    if lake_root is None or str(lake_root).strip() == "":
        raise ValueError("必须显式传入 --lake-root，禁止默认读取仓库旧数据目录。")
    if as_of is None or str(as_of).strip() == "":
        raise ValueError("必须显式传入 --as-of，禁止无 PIT 决策时间读取实验输入。")
    symbols = getattr(args, "symbols", None)
    return ExperimentLakeInputRequest(
        lake_root=lake_root,
        as_of=str(as_of),
        start_date=getattr(args, "start_date", None),
        end_date=getattr(args, "end_date", None),
        symbols=tuple(str(symbol) for symbol in symbols) if symbols else None,
        quality_policy=str(getattr(args, "quality_policy", None) or "require_pass"),
    )


def _fixture_frames(args: Any) -> dict[str, pd.DataFrame] | None:
    source = getattr(args, "fixture_frames", None)
    if source is None:
        return None
    if hasattr(source, "to_dict") and not isinstance(source, Mapping):
        source = source.to_dict()
    if not isinstance(source, Mapping):
        raise ValueError("fixture_frames 必须是 mapping。")
    frames: dict[str, pd.DataFrame] = {}
    for dataset, frame_key in EXPERIMENT_FRAME_KEYS.items():
        frame = source.get(frame_key)
        if frame is None:
            frame = source.get(dataset)
        if not isinstance(frame, pd.DataFrame):
            raise ValueError(f"fixture_frames 缺少 DataFrame: {frame_key}")
        frames[frame_key] = frame.copy()
    return frames


def _reader_filters(request: ExperimentLakeInputRequest) -> dict[str, Any]:
    filters: dict[str, Any] = {}
    if request.start_date:
        filters["start_date"] = request.start_date
    if request.end_date:
        filters["end_date"] = request.end_date
    if request.symbols:
        filters["symbols"] = list(request.symbols)
    return filters


def _zero_permission_counters() -> dict[str, int]:
    return {key: 0 for key in FORBIDDEN_OPERATION_COUNTERS}


__all__ = [
    "EXPERIMENT_FRAME_KEYS",
    "EXPERIMENT_PIT_KEYS",
    "EXPERIMENT_REQUIRED_DATASETS",
    "ExperimentLakeInputRequest",
    "ExperimentLakeInputResult",
    "add_experiment_lake_args",
    "load_experiment_lake_frames",
]
