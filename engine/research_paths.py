"""研究实验产物的默认 NAS 路径。"""

from __future__ import annotations

from pathlib import Path


RESEARCH_REPORT_ROOT = Path("/mnt/quant-lab-primary/research/reports")
RESEARCH_RUN_ROOT = Path("/mnt/quant-lab-primary/research/runs")


def research_report_path(*parts: str) -> Path:
    """返回 NAS 上的研究报告路径。"""

    return RESEARCH_REPORT_ROOT.joinpath(*parts)


def research_run_path(*parts: str) -> Path:
    """返回 NAS 上的研究运行产物路径。"""

    return RESEARCH_RUN_ROOT.joinpath(*parts)
