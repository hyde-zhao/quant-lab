"""本地回测报告行与 CSV/Markdown 安全输出。"""

from __future__ import annotations

from pathlib import Path
import csv
from typing import Any, Iterable


FORMULA_PREFIXES = ("=", "+", "-", "@")


def sanitize_tabular_text(value: Any) -> Any:
    """防止 CSV/Markdown 文本字段公式注入；数值等类型保持原样。"""

    if not isinstance(value, str):
        return value
    if value and value[0] in FORMULA_PREFIXES:
        return "'" + value
    return value.replace("\n", " ").replace("\r", " ")


def build_backtest_report_row(metrics: dict[str, Any], metadata: dict[str, Any]) -> dict[str, Any]:
    """合并指标与 metadata 为单次回测报告行。"""

    row = {**metadata, **metrics}
    for key in ("strategy_name", "quality_status", "survivorship_bias_note", "trade_limitations_note"):
        if key in row:
            row[key] = sanitize_tabular_text(row[key])
    return row


def write_rows_csv(rows: Iterable[dict[str, Any]], output_path: str | Path, fieldnames: list[str]) -> str:
    """按固定字段写 CSV。调用方负责传入临时或显式路径。"""

    target = Path(output_path)
    _ensure_parent_dir(target)
    with target.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: sanitize_tabular_text(row.get(field, "")) for field in fieldnames})
    return str(target)


def _ensure_parent_dir(path: Path) -> None:
    parent = path.parent
    if parent and str(parent) != ".":
        parent.mkdir(parents=True, exist_ok=True)


__all__ = (
    "FORMULA_PREFIXES",
    "build_backtest_report_row",
    "sanitize_tabular_text",
    "write_rows_csv",
)
