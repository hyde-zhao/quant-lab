"""CR-035 第四章多因子模型定价检验 runner。

只读取第三章 factor panel 和 label parts，写 NAS reports/runs
研究产物；不读取凭据、不触发 provider fetch、不写 data lake、不 publish
catalog、不触发 QMT / simulation / live。
"""

from __future__ import annotations

import argparse
import json
import os
import resource
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping, Sequence

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("NUMEXPR_NUM_THREADS", "1")

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from engine.chapter4_factor_models import (
    DEFAULT_CHAPTER4_MODELS,
    FORBIDDEN_OPERATION_COUNTS,
    Chapter4AnalysisResult,
    run_chapter4_analysis,
)
from engine.research_paths import research_report_path, research_run_path


CHAPTER4_RUN_SCHEMA = "chapter4_factor_models_run_v1"

DEFAULT_INPUTS = (
    {
        "sample_id": "in_sample_2000_2019",
        "panel_path": str(research_report_path("chapter3_factor_panel", "run-chapter3-empirical-2000-2019-financial-fallback-20260610", "factor_panel.parquet")),
        "label_root": str(research_run_path("chapter3_empirical", "run-chapter3-empirical-2000-2019-financial-fallback-20260610", "label_parts")),
        "report_path": str(research_run_path("chapter3_empirical", "run-chapter3-empirical-2000-2019-financial-fallback-20260610", "EMPIRICAL-RUN-REPORT.json")),
    },
    {
        "sample_id": "observation_2020_2026_ytd",
        "panel_path": str(research_report_path("chapter3_factor_panel", "run-chapter3-empirical-2020-2026-ytd-financial-fallback-20260610", "factor_panel.parquet")),
        "label_root": str(research_run_path("chapter3_empirical", "run-chapter3-empirical-2020-2026-ytd-financial-fallback-20260610", "label_parts")),
        "report_path": str(research_run_path("chapter3_empirical", "run-chapter3-empirical-2020-2026-ytd-financial-fallback-20260610", "EMPIRICAL-RUN-REPORT.json")),
    },
)


@dataclass(frozen=True, slots=True)
class Chapter4Artifacts:
    run_id: str
    report_dir: Path
    process_dir: Path
    fama_macbeth_results_path: Path
    factor_model_returns_path: Path
    model_comparison_path: Path
    factor_correlation_path: Path
    model_correlation_path: Path
    manifest_path: Path
    report_json_path: Path
    report_md_path: Path
    model_admission_summary_path: Path

    def to_dict(self) -> dict[str, str]:
        return {key: str(value) for key, value in asdict(self).items()}


@dataclass(frozen=True, slots=True)
class Chapter4RunResult:
    run_id: str
    status: str
    sample_results: tuple[Chapter4AnalysisResult, ...]
    artifacts: Chapter4Artifacts
    memory_budget: Mapping[str, Any]
    operation_counts: Mapping[str, int] = field(default_factory=lambda: dict(FORBIDDEN_OPERATION_COUNTS))
    schema_version: str = CHAPTER4_RUN_SCHEMA

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "run_id": self.run_id,
            "status": self.status,
            "sample_results": [item.to_dict() for item in self.sample_results],
            "artifacts": self.artifacts.to_dict(),
            "memory_budget": dict(self.memory_budget),
            "operation_counts": dict(self.operation_counts),
        }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="运行 CR-035 第四章多因子模型定价检验")
    parser.add_argument("--run-id", default="")
    parser.add_argument("--output-root", default=str(research_run_path("chapter4_factor_models")))
    parser.add_argument("--report-root", default=str(research_report_path("chapter4_factor_models")))
    parser.add_argument("--input-config", default="", help="可选 JSON，字段为 samples 数组")
    parser.add_argument("--min-cross-section", type=int, default=30)
    parser.add_argument("--quantiles", type=int, default=5)
    parser.add_argument("--max-memory-gb", type=float, default=16.0)
    parser.add_argument("--allow-report-limitations", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    run_id = args.run_id or f"run-chapter4-factor-models-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    samples = load_input_samples(args.input_config)
    result = run_chapter4_from_paths(
        samples,
        run_id=run_id,
        output_root=Path(args.output_root),
        report_root=Path(args.report_root),
        min_cross_section=args.min_cross_section,
        quantiles=args.quantiles,
        max_memory_gb=args.max_memory_gb,
        allow_report_limitations=bool(args.allow_report_limitations),
    )
    print(json.dumps({"ok": True, "status": result.status, "run_id": result.run_id, "artifacts": result.artifacts.to_dict(), **FORBIDDEN_OPERATION_COUNTS}, ensure_ascii=False, sort_keys=True))
    return 0 if result.status == "PASS" else 2


def run_chapter4_from_paths(
    samples: Sequence[Mapping[str, Any]],
    *,
    run_id: str,
    output_root: Path,
    report_root: Path,
    min_cross_section: int = 30,
    quantiles: int = 5,
    max_memory_gb: float = 16.0,
    allow_report_limitations: bool = False,
) -> Chapter4RunResult:
    artifacts = chapter4_artifacts(run_id, output_root=output_root, report_root=report_root)
    artifacts.report_dir.mkdir(parents=True, exist_ok=True)
    artifacts.process_dir.mkdir(parents=True, exist_ok=True)
    sample_results: list[Chapter4AnalysisResult] = []
    for sample in samples:
        sample_id = str(sample["sample_id"])
        assert_chapter3_report_pass(Path(str(sample["report_path"])), allow_limitations=allow_report_limitations)
        panel = pd.read_parquet(Path(str(sample["panel_path"])))
        labels = read_label_parts(Path(str(sample["label_root"])))
        result = run_chapter4_analysis(
            panel,
            labels,
            run_id=run_id,
            sample_id=sample_id,
            models=DEFAULT_CHAPTER4_MODELS,
            min_cross_section=min_cross_section,
            quantiles=quantiles,
        )
        sample_results.append(result)
        enforce_memory_budget(max_memory_gb, f"sample_{sample_id}")
    write_outputs(sample_results, artifacts, max_memory_gb=max_memory_gb)
    status = "PASS" if sample_results and all(item.status == "PASS" for item in sample_results) else "BLOCKED"
    return Chapter4RunResult(
        run_id=run_id,
        status=status,
        sample_results=tuple(sample_results),
        artifacts=artifacts,
        memory_budget=memory_budget_summary(max_memory_gb),
        operation_counts=dict(FORBIDDEN_OPERATION_COUNTS),
    )


def load_input_samples(input_config: str) -> tuple[Mapping[str, Any], ...]:
    if not input_config:
        return tuple(DEFAULT_INPUTS)
    data = json.loads(Path(input_config).read_text(encoding="utf-8"))
    samples = data.get("samples")
    if not isinstance(samples, list) or not samples:
        raise ValueError("input-config 必须包含非空 samples 数组")
    return tuple(samples)


def assert_chapter3_report_pass(path: Path, *, allow_limitations: bool = False) -> None:
    if not path.exists():
        raise RuntimeError(f"缺少第三章报告: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("status") != "PASS":
        raise RuntimeError(f"第三章报告状态不是 PASS: {path} status={data.get('status')}")
    limitations = data.get("limitations") or []
    if limitations and not allow_limitations:
        raise RuntimeError(f"第三章报告存在 limitations，按 CR-035 输入合同阻断: {path}")


def read_label_parts(label_root: Path) -> pd.DataFrame:
    if not label_root.exists():
        raise RuntimeError(f"缺少 label_parts 目录: {label_root}")
    paths = sorted(label_root.glob("*.parquet"))
    if not paths:
        raise RuntimeError(f"label_parts 目录为空: {label_root}")
    return pd.concat((pd.read_parquet(path) for path in paths), ignore_index=True)


def write_outputs(
    sample_results: Sequence[Chapter4AnalysisResult],
    artifacts: Chapter4Artifacts,
    *,
    max_memory_gb: float,
) -> None:
    fmb = _with_sample(pd.concat([item.fama_macbeth_results.assign(sample_id=item.sample_id) for item in sample_results], ignore_index=True))
    returns = _with_sample(pd.concat([item.factor_model_returns.assign(sample_id=item.sample_id) for item in sample_results], ignore_index=True))
    comparison = _with_sample(pd.concat([item.model_comparison.assign(sample_id=item.sample_id) for item in sample_results], ignore_index=True))
    factor_corr = stack_correlation(sample_results, "factor")
    model_corr = stack_correlation(sample_results, "model")
    admission = build_admission_payload(sample_results)
    fmb.to_csv(artifacts.fama_macbeth_results_path, index=False)
    returns.to_parquet(artifacts.factor_model_returns_path, index=False)
    comparison.to_csv(artifacts.model_comparison_path, index=False)
    factor_corr.to_csv(artifacts.factor_correlation_path, index=False)
    model_corr.to_csv(artifacts.model_correlation_path, index=False)
    artifacts.model_admission_summary_path.write_text(json.dumps(admission, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    manifest = {
        "schema_version": CHAPTER4_RUN_SCHEMA,
        "run_id": artifacts.run_id,
        "model_definitions": [model.to_dict() for model in DEFAULT_CHAPTER4_MODELS],
        "sample_results": [item.to_dict() for item in sample_results],
        "artifacts": artifacts.to_dict(),
        "memory_budget": memory_budget_summary(max_memory_gb),
        "operation_counts": dict(FORBIDDEN_OPERATION_COUNTS),
    }
    artifacts.manifest_path.write_text(json.dumps(_json_safe(manifest), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    run_result = {
        "schema_version": CHAPTER4_RUN_SCHEMA,
        "run_id": artifacts.run_id,
        "status": "PASS" if sample_results and all(item.status == "PASS" for item in sample_results) else "BLOCKED",
        "sample_results": [item.to_dict() for item in sample_results],
        "artifacts": artifacts.to_dict(),
        "model_admission_summary": admission,
        "operation_counts": dict(FORBIDDEN_OPERATION_COUNTS),
    }
    artifacts.report_json_path.write_text(json.dumps(_json_safe(run_result), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    artifacts.report_md_path.write_text(render_markdown(sample_results, artifacts), encoding="utf-8")


def chapter4_artifacts(run_id: str, *, output_root: Path, report_root: Path) -> Chapter4Artifacts:
    report_dir = report_root / run_id
    process_dir = output_root / run_id
    return Chapter4Artifacts(
        run_id=run_id,
        report_dir=report_dir,
        process_dir=process_dir,
        fama_macbeth_results_path=report_dir / "fama_macbeth_results.csv",
        factor_model_returns_path=report_dir / "factor_model_returns.parquet",
        model_comparison_path=report_dir / "model_comparison.csv",
        factor_correlation_path=report_dir / "factor_correlation.csv",
        model_correlation_path=report_dir / "model_correlation.csv",
        manifest_path=report_dir / "factor_model_manifest.json",
        report_json_path=process_dir / "CHAPTER4-RUN-REPORT.json",
        report_md_path=process_dir / "CHAPTER4-RUN-REPORT.md",
        model_admission_summary_path=process_dir / "MODEL-ADMISSION-SUMMARY.json",
    )


def stack_correlation(sample_results: Sequence[Chapter4AnalysisResult], kind: str) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for item in sample_results:
        matrix = item.factor_correlation if kind == "factor" else item.model_correlation
        for row_id, values in matrix.to_dict(orient="index").items():
            for column_id, value in values.items():
                rows.append({"sample_id": item.sample_id, "row_id": row_id, "column_id": column_id, "correlation": value})
    return pd.DataFrame(rows)


def build_admission_payload(sample_results: Sequence[Chapter4AnalysisResult]) -> dict[str, Any]:
    return {
        "schema_version": "chapter4_model_admission_summary_v1",
        "not_authorization": True,
        "blocked_claims": list(sample_results[0].blocked_claims) if sample_results else [],
        "samples": [
            {
                "sample_id": item.sample_id,
                "status": item.status,
                "model_admission_summary": list(item.model_admission_summary),
            }
            for item in sample_results
        ],
        "handoff": "CR-038/CR-039 只能消费本摘要作为研究输入；QMT、simulation、live 仍需独立 CR 和运行授权。",
        "operation_counts": dict(FORBIDDEN_OPERATION_COUNTS),
    }


def render_markdown(sample_results: Sequence[Chapter4AnalysisResult], artifacts: Chapter4Artifacts) -> str:
    lines = [
        "# CR-035 第四章多因子模型定价检验报告",
        "",
        f"- run_id: `{artifacts.run_id}`",
        f"- status: `{'PASS' if sample_results and all(item.status == 'PASS' for item in sample_results) else 'BLOCKED'}`",
        "- provider_fetch: `0`",
        "- lake_write: `0`",
        "- catalog_publish: `0`",
        "- qmt_operation: `0`",
        "- simulation_or_live: `0`",
        "",
        "## 样本摘要",
        "",
        "| sample_id | status | panel_rows | label_rows | matched_rows | rebalance_count |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for item in sample_results:
        lines.append(
            f"| `{item.sample_id}` | `{item.status}` | {item.panel_rows} | {item.label_rows} | {item.matched_rows} | {item.rebalance_count} |"
        )
    lines.extend(
        [
            "",
            "## 模型准入摘要",
            "",
            "| sample_id | model_id | admission | reason |",
            "|---|---|---|---|",
        ]
    )
    for item in sample_results:
        for summary in item.model_admission_summary:
            lines.append(
                f"| `{item.sample_id}` | `{summary['model_id']}` | `{summary['admission']}` | {summary['reason']} |"
            )
    lines.extend(
        [
            "",
            "## 产物",
            "",
            f"- fama_macbeth_results: `{artifacts.fama_macbeth_results_path}`",
            f"- factor_model_returns: `{artifacts.factor_model_returns_path}`",
            f"- model_comparison: `{artifacts.model_comparison_path}`",
            f"- factor_correlation: `{artifacts.factor_correlation_path}`",
            f"- model_correlation: `{artifacts.model_correlation_path}`",
            f"- model_admission_summary: `{artifacts.model_admission_summary_path}`",
            "",
            "## 边界",
            "",
            "本报告只允许作为项目内部第4章研究证据和 CR-037/CR-038/CR-039 输入，不构成 production-valid、QMT-ready、simulation-ready 或 live-ready 声明。",
            "",
        ]
    )
    return "\n".join(lines)


def _with_sample(frame: pd.DataFrame) -> pd.DataFrame:
    return frame


def max_rss_bytes() -> int:
    rss = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    if sys.platform == "darwin":
        return rss
    return rss * 1024


def memory_budget_summary(max_memory_gb: float) -> dict[str, Any]:
    observed = max_rss_bytes()
    budget_bytes = int(max_memory_gb * 1024 * 1024 * 1024) if max_memory_gb > 0 else 0
    return {
        "max_memory_gb": float(max_memory_gb),
        "max_rss_bytes_observed": observed,
        "max_rss_gb_observed": observed / 1024 / 1024 / 1024,
        "budget_bytes": budget_bytes,
        "status": "not_enforced" if budget_bytes <= 0 else ("pass" if observed <= budget_bytes else "fail"),
    }


def enforce_memory_budget(max_memory_gb: float, context: str) -> None:
    if max_memory_gb <= 0:
        return
    budget_bytes = int(max_memory_gb * 1024 * 1024 * 1024)
    observed = max_rss_bytes()
    if observed > budget_bytes:
        raise MemoryError(
            f"第四章模型 runner 超过内存预算: context={context}, "
            f"observed_gb={observed / 1024 / 1024 / 1024:.3f}, budget_gb={max_memory_gb:.3f}"
        )


def _json_safe(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if hasattr(value, "item"):
        try:
            return value.item()
        except Exception:
            return str(value)
    if isinstance(value, Path):
        return str(value)
    if pd.isna(value) if not isinstance(value, (list, tuple, dict, str, bytes)) else False:
        return None
    return value


if __name__ == "__main__":
    raise SystemExit(main())
