"""本地 fake/reference/Tushare comparison 输出契约。"""

from __future__ import annotations

import csv
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import pandas as pd


class ComparisonInputError(ValueError):
    """comparison 输入不满足 exact 契约。"""


@dataclass(frozen=True, slots=True)
class ComparisonRow:
    dataset: str
    key: str
    field: str
    left_source: str
    right_source: str
    left_value: Any
    right_value: Any
    diff: float | None
    tolerance: float
    status: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


COMPARISON_FIELDS: tuple[str, ...] = (
    "dataset",
    "key",
    "field",
    "left_source",
    "right_source",
    "left_value",
    "right_value",
    "diff",
    "tolerance",
    "status",
)

COMPARISON_STATUS_VALUES: tuple[str, ...] = (
    "match",
    "mismatch",
    "missing_left",
    "missing_right",
    "non_numeric_mismatch",
)

CR005_DATASET_COMPARISON_CONTRACT: dict[str, dict[str, tuple[str, ...]]] = {
    "prices": {
        "keys": ("trade_date", "symbol"),
        "fields": ("close", "adjusted_close"),
    },
    "hs300_index": {
        "keys": ("trade_date", "index_code"),
        "fields": ("close", "pct_chg"),
    },
    "trade_calendar": {
        "keys": ("trade_date", "exchange"),
        "fields": ("is_open", "pretrade_date"),
    },
    "index_weights": {
        "keys": ("trade_date", "index_code", "con_code"),
        "fields": ("weight",),
    },
}


def _frame(value: pd.DataFrame | Iterable[Mapping[str, Any]]) -> pd.DataFrame:
    if isinstance(value, pd.DataFrame):
        return value.copy()
    return pd.DataFrame(list(value))


def _validate_columns(frame: pd.DataFrame, columns: Sequence[str], side: str) -> None:
    missing = [column for column in columns if column not in frame.columns]
    if missing:
        raise ComparisonInputError(f"{side} 缺少字段: {','.join(missing)}")


def _key_value(row: Mapping[str, Any], keys: Sequence[str]) -> str:
    return "|".join(f"{key}={row[key]}" for key in keys)


def _indexed(frame: pd.DataFrame, keys: Sequence[str], side: str) -> dict[str, dict[str, Any]]:
    records = frame.to_dict("records")
    output: dict[str, dict[str, Any]] = {}
    for row in records:
        key = _key_value(row, keys)
        if key in output:
            raise ComparisonInputError(f"{side} 存在重复 key: {key}")
        output[key] = row
    return output


def _source(row: Mapping[str, Any] | None, default: str) -> str:
    if not row:
        return default
    value = row.get("source")
    return str(value) if value is not None else default


def _compare_value(left: Any, right: Any, tolerance: float) -> tuple[float | None, str]:
    if pd.isna(left) and pd.isna(right):
        return 0.0, "match"
    try:
        left_num = float(left)
        right_num = float(right)
    except (TypeError, ValueError):
        return None, "match" if left == right else "non_numeric_mismatch"
    diff = abs(left_num - right_num)
    return diff, "match" if diff <= tolerance else "mismatch"


def compare_sources(
    left: pd.DataFrame | Iterable[Mapping[str, Any]],
    right: pd.DataFrame | Iterable[Mapping[str, Any]],
    dataset: str,
    keys: Sequence[str],
    fields: Sequence[str],
    tolerance: float,
    left_source: str = "fake",
    right_source: str = "reference",
) -> list[ComparisonRow]:
    if not keys:
        raise ComparisonInputError("keys 不能为空")
    if not fields:
        raise ComparisonInputError("fields 不能为空")
    left_frame = _frame(left)
    right_frame = _frame(right)
    _validate_columns(left_frame, [*keys, *fields], "left")
    _validate_columns(right_frame, [*keys, *fields], "right")
    left_index = _indexed(left_frame, keys, "left")
    right_index = _indexed(right_frame, keys, "right")
    rows: list[ComparisonRow] = []
    for key in sorted(set(left_index) | set(right_index)):
        left_row = left_index.get(key)
        right_row = right_index.get(key)
        for field in fields:
            if left_row is None:
                rows.append(
                    ComparisonRow(
                        dataset,
                        key,
                        field,
                        left_source,
                        _source(right_row, right_source),
                        None,
                        right_row.get(field) if right_row else None,
                        None,
                        tolerance,
                        "missing_left",
                    )
                )
                continue
            if right_row is None:
                rows.append(
                    ComparisonRow(
                        dataset,
                        key,
                        field,
                        _source(left_row, left_source),
                        right_source,
                        left_row.get(field),
                        None,
                        None,
                        tolerance,
                        "missing_right",
                    )
                )
                continue
            diff, status = _compare_value(left_row.get(field), right_row.get(field), tolerance)
            rows.append(
                ComparisonRow(
                    dataset,
                    key,
                    field,
                    _source(left_row, left_source),
                    _source(right_row, right_source),
                    left_row.get(field),
                    right_row.get(field),
                    diff,
                    tolerance,
                    status,
                )
            )
    return rows


def compare_local_dataset(
    left: pd.DataFrame | Iterable[Mapping[str, Any]],
    right: pd.DataFrame | Iterable[Mapping[str, Any]],
    dataset: str,
    tolerance: float = 0.0,
    keys: Sequence[str] | None = None,
    fields: Sequence[str] | None = None,
    left_source: str = "tushare",
    right_source: str = "reference",
) -> list[ComparisonRow]:
    """按 CR-005 本地数据集契约比较两个已落地的本地数据源。"""

    contract = CR005_DATASET_COMPARISON_CONTRACT.get(dataset)
    if contract is None:
        supported = ",".join(sorted(CR005_DATASET_COMPARISON_CONTRACT))
        raise ComparisonInputError(f"不支持的 CR005 comparison dataset: {dataset}; supported={supported}")
    return compare_sources(
        left,
        right,
        dataset,
        keys or contract["keys"],
        fields or contract["fields"],
        tolerance,
        left_source=left_source,
        right_source=right_source,
    )


def comparison_summary(
    rows: Sequence[ComparisonRow],
    left_source: str | None = None,
    right_source: str | None = None,
) -> dict[str, Any]:
    """输出可机器断言的本地 comparison status summary。"""

    counts = {status: 0 for status in COMPARISON_STATUS_VALUES}
    counts.update(status_counts(rows))
    datasets = sorted({row.dataset for row in rows})
    inferred_left = left_source or (rows[0].left_source if rows else "")
    inferred_right = right_source or (rows[0].right_source if rows else "")
    return {
        "row_count": len(rows),
        "status_counts": counts,
        "datasets": datasets,
        "left_source": inferred_left,
        "right_source": inferred_right,
        "network_calls": 0,
    }


def load_comparison_frame(path: str | Path) -> pd.DataFrame:
    path_text = str(path)
    if path_text.startswith(("http://", "https://")):
        raise ComparisonInputError("comparison 只接受本地文件路径，不支持远程 URL")
    source = Path(path)
    if not source.exists():
        raise ComparisonInputError(f"comparison 输入不存在: {source}")
    if source.suffix.lower() == ".csv":
        return pd.read_csv(source)
    if source.suffix.lower() == ".parquet":
        return pd.read_parquet(source)
    raise ComparisonInputError(f"不支持的 comparison 文件类型: {source.suffix}")


def write_comparison_csv(rows: Sequence[ComparisonRow], path: str | Path) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(COMPARISON_FIELDS))
        writer.writeheader()
        for row in rows:
            writer.writerow(row.to_dict())
    return output


def status_counts(rows: Sequence[ComparisonRow]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        counts[row.status] = counts.get(row.status, 0) + 1
    return counts


__all__ = [
    "COMPARISON_STATUS_VALUES",
    "COMPARISON_FIELDS",
    "CR005_DATASET_COMPARISON_CONTRACT",
    "ComparisonInputError",
    "ComparisonRow",
    "compare_local_dataset",
    "compare_sources",
    "comparison_summary",
    "load_comparison_frame",
    "status_counts",
    "write_comparison_csv",
]
