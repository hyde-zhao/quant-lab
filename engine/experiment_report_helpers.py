"""Shared helpers for experiment Markdown reports."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Collection

import pandas as pd


def markdown_table(
    rows: list[dict[str, Any]],
    fields: list[str],
    *,
    percent_fields: Collection[str],
) -> str:
    header = "| " + " | ".join(format_header(field, percent_fields=percent_fields) for field in fields) + " |"
    sep = "| " + " | ".join("---" for _ in fields) + " |"
    body = [
        "| "
        + " | ".join(format_value(row.get(field, ""), field, percent_fields=percent_fields) for field in fields)
        + " |"
        for row in rows
    ]
    return "\n".join([header, sep, *body])


def format_header(field: str, *, percent_fields: Collection[str]) -> str:
    if field in percent_fields:
        return f"{field}(%)"
    return field


def format_value(value: Any, field: str, *, percent_fields: Collection[str]) -> str:
    if value in ("", None):
        return ""
    if field in percent_fields:
        try:
            return f"{float(value) * 100:.2f}%"
        except (TypeError, ValueError):
            return str(value)
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value)


def resolve_date_range(
    data_dir: Path,
    start_date: str | None = None,
    end_date: str | None = None,
) -> tuple[str, str]:
    calendar = pd.read_parquet(data_dir / "trade_calendar.parquet")
    dates = pd.to_datetime(calendar["trade_date"], errors="coerce").dropna().sort_values()
    start = start_date or dates.iloc[0].date().isoformat()
    end = end_date or dates.iloc[-1].date().isoformat()
    return start, end
