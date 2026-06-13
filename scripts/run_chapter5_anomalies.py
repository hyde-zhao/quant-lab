"""CR-036 第五章异象复刻 runner。

只读取本地第三章 factor panel / label parts 和 CR-035 模型收益，写本地
reports/process 研究产物；不读取凭据、不触发 provider fetch、不写 data
lake、不 publish catalog、不触发 QMT / simulation / live。
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

from engine.chapter5_anomalies import (
    DEFAULT_CHAPTER5_ANOMALIES,
    FORBIDDEN_OPERATION_COUNTS,
    Chapter5AnalysisResult,
    run_chapter5_analysis,
)
from scripts.run_chapter4_factor_models import assert_chapter3_report_pass, read_label_parts


CHAPTER5_RUN_SCHEMA = "chapter5_anomalies_run_v1"

DEFAULT_INPUTS = (
    {
        "sample_id": "in_sample_2000_2019",
        "panel_path": "reports/chapter3_factor_panel/run-chapter3-empirical-2000-2019-financial-fallback-20260610/factor_panel.parquet",
        "label_root": "process/research/chapter3_empirical/run-chapter3-empirical-2000-2019-financial-fallback-20260610/label_parts",
        "chapter3_report_path": "process/research/chapter3_empirical/run-chapter3-empirical-2000-2019-financial-fallback-20260610/EMPIRICAL-RUN-REPORT.json",
        "chapter4_report_path": "process/research/chapter4_factor_models/run-cr035-chapter4-factor-models-20260610/CHAPTER4-RUN-REPORT.json",
        "chapter4_model_returns_path": "reports/chapter4_factor_models/run-cr035-chapter4-factor-models-20260610/factor_model_returns.parquet",
    },
    {
        "sample_id": "observation_2020_2026_ytd",
        "panel_path": "reports/chapter3_factor_panel/run-chapter3-empirical-2020-2026-ytd-financial-fallback-20260610/factor_panel.parquet",
        "label_root": "process/research/chapter3_empirical/run-chapter3-empirical-2020-2026-ytd-financial-fallback-20260610/label_parts",
        "chapter3_report_path": "process/research/chapter3_empirical/run-chapter3-empirical-2020-2026-ytd-financial-fallback-20260610/EMPIRICAL-RUN-REPORT.json",
        "chapter4_report_path": "process/research/chapter4_factor_models/run-cr035-chapter4-factor-models-20260610/CHAPTER4-RUN-REPORT.json",
        "chapter4_model_returns_path": "reports/chapter4_factor_models/run-cr035-chapter4-factor-models-20260610/factor_model_returns.parquet",
    },
)


@dataclass(frozen=True, slots=True)
class Chapter5Artifacts:
    run_id: str
    report_dir: Path
    process_dir: Path
    anomaly_panel_path: Path
    anomaly_returns_path: Path
    alpha_tests_path: Path
    anomaly_correlation_path: Path
    gap_register_path: Path
    manifest_path: Path
    report_json_path: Path
    report_md_path: Path
    anomaly_admission_summary_path: Path

    def to_dict(self) -> dict[str, str]:
        return {key: str(value) for key, value in asdict(self).items()}


@dataclass(frozen=True, slots=True)
class Chapter5RunResult:
    run_id: str
    status: str
    sample_results: tuple[Chapter5AnalysisResult, ...]
    artifacts: Chapter5Artifacts
    memory_budget: Mapping[str, Any]
    operation_counts: Mapping[str, int] = field(default_factory=lambda: dict(FORBIDDEN_OPERATION_COUNTS))
    schema_version: str = CHAPTER5_RUN_SCHEMA

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
    parser = argparse.ArgumentParser(description="运行 CR-036 第五章异象复刻")
    parser.add_argument("--run-id", default="")
    parser.add_argument("--output-root", default="process/research/chapter5_anomalies")
    parser.add_argument("--report-root", default="reports/chapter5_anomalies")
    parser.add_argument("--input-config", default="", help="可选 JSON，字段为 samples 数组")
    parser.add_argument("--min-cross-section", type=int, default=30)
    parser.add_argument("--quantiles", type=int, default=5)
    parser.add_argument("--residual-window", type=int, default=12)
    parser.add_argument("--residual-min-periods", type=int, default=6)
    parser.add_argument("--max-memory-gb", type=float, default=16.0)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    run_id = args.run_id or f"run-chapter5-anomalies-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    result = run_chapter5_from_paths(
        load_input_samples(args.input_config),
        run_id=run_id,
        output_root=Path(args.output_root),
        report_root=Path(args.report_root),
        min_cross_section=args.min_cross_section,
        quantiles=args.quantiles,
        residual_window=args.residual_window,
        residual_min_periods=args.residual_min_periods,
        max_memory_gb=args.max_memory_gb,
    )
    print(json.dumps({"ok": True, "status": result.status, "run_id": result.run_id, "artifacts": result.artifacts.to_dict(), **FORBIDDEN_OPERATION_COUNTS}, ensure_ascii=False, sort_keys=True))
    return 0 if result.status == "PASS" else 2


def run_chapter5_from_paths(
    samples: Sequence[Mapping[str, Any]],
    *,
    run_id: str,
    output_root: Path,
    report_root: Path,
    min_cross_section: int = 30,
    quantiles: int = 5,
    residual_window: int = 12,
    residual_min_periods: int = 6,
    max_memory_gb: float = 16.0,
) -> Chapter5RunResult:
    artifacts = chapter5_artifacts(run_id, output_root=output_root, report_root=report_root)
    artifacts.report_dir.mkdir(parents=True, exist_ok=True)
    artifacts.process_dir.mkdir(parents=True, exist_ok=True)
    sample_results: list[Chapter5AnalysisResult] = []
    all_model_returns = pd.read_parquet(Path(str(samples[0]["chapter4_model_returns_path"]))) if samples else pd.DataFrame()
    for sample in samples:
        sample_id = str(sample["sample_id"])
        assert_chapter3_report_pass(Path(str(sample["chapter3_report_path"])))
        assert_chapter4_report_pass(Path(str(sample["chapter4_report_path"])))
        panel = pd.read_parquet(Path(str(sample["panel_path"])))
        labels = read_label_parts(Path(str(sample["label_root"])))
        model_returns = all_model_returns[all_model_returns["sample_id"] == sample_id].copy()
        result = run_chapter5_analysis(
            panel,
            labels,
            model_returns,
            run_id=run_id,
            sample_id=sample_id,
            anomalies=DEFAULT_CHAPTER5_ANOMALIES,
            min_cross_section=min_cross_section,
            quantiles=quantiles,
            residual_window=residual_window,
            residual_min_periods=residual_min_periods,
        )
        sample_results.append(result)
        enforce_memory_budget(max_memory_gb, f"sample_{sample_id}")
    write_outputs(sample_results, artifacts, max_memory_gb=max_memory_gb)
    status = "PASS" if sample_results and all(item.status == "PASS" for item in sample_results) else "BLOCKED"
    return Chapter5RunResult(
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


def assert_chapter4_report_pass(path: Path) -> None:
    if not path.exists():
        raise RuntimeError(f"缺少第四章报告: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("status") != "PASS":
        raise RuntimeError(f"第四章报告状态不是 PASS: {path} status={data.get('status')}")


def write_outputs(
    sample_results: Sequence[Chapter5AnalysisResult],
    artifacts: Chapter5Artifacts,
    *,
    max_memory_gb: float,
) -> None:
    anomaly_panel = pd.concat([item.anomaly_panel.assign(sample_id=item.sample_id) for item in sample_results], ignore_index=True)
    anomaly_returns = pd.concat([item.anomaly_returns.assign(sample_id=item.sample_id) for item in sample_results], ignore_index=True)
    alpha_tests = pd.concat([item.alpha_tests.assign(sample_id=item.sample_id) for item in sample_results], ignore_index=True)
    anomaly_correlation = stack_correlation(sample_results)
    gap_register = [dict(row, sample_id=item.sample_id) for item in sample_results for row in item.gap_register]
    admission = build_admission_payload(sample_results)
    anomaly_panel.to_parquet(artifacts.anomaly_panel_path, index=False)
    anomaly_returns.to_csv(artifacts.anomaly_returns_path, index=False)
    alpha_tests.to_csv(artifacts.alpha_tests_path, index=False)
    anomaly_correlation.to_csv(artifacts.anomaly_correlation_path, index=False)
    pd.DataFrame(gap_register).to_csv(artifacts.gap_register_path, index=False)
    artifacts.anomaly_admission_summary_path.write_text(json.dumps(admission, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    manifest = {
        "schema_version": CHAPTER5_RUN_SCHEMA,
        "run_id": artifacts.run_id,
        "anomaly_definitions": [item.to_dict() for item in DEFAULT_CHAPTER5_ANOMALIES],
        "sample_results": [item.to_dict() for item in sample_results],
        "artifacts": artifacts.to_dict(),
        "memory_budget": memory_budget_summary(max_memory_gb),
        "operation_counts": dict(FORBIDDEN_OPERATION_COUNTS),
    }
    artifacts.manifest_path.write_text(json.dumps(_json_safe(manifest), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report = {
        "schema_version": CHAPTER5_RUN_SCHEMA,
        "run_id": artifacts.run_id,
        "status": "PASS" if sample_results and all(item.status == "PASS" for item in sample_results) else "BLOCKED",
        "sample_results": [item.to_dict() for item in sample_results],
        "artifacts": artifacts.to_dict(),
        "anomaly_admission_summary": admission,
        "operation_counts": dict(FORBIDDEN_OPERATION_COUNTS),
    }
    artifacts.report_json_path.write_text(json.dumps(_json_safe(report), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    artifacts.report_md_path.write_text(render_markdown(sample_results, artifacts), encoding="utf-8")


def chapter5_artifacts(run_id: str, *, output_root: Path, report_root: Path) -> Chapter5Artifacts:
    report_dir = report_root / run_id
    process_dir = output_root / run_id
    return Chapter5Artifacts(
        run_id=run_id,
        report_dir=report_dir,
        process_dir=process_dir,
        anomaly_panel_path=report_dir / "anomaly_panel.parquet",
        anomaly_returns_path=report_dir / "anomaly_returns.csv",
        alpha_tests_path=report_dir / "alpha_tests.csv",
        anomaly_correlation_path=report_dir / "anomaly_correlation.csv",
        gap_register_path=report_dir / "gap_register.csv",
        manifest_path=report_dir / "anomaly_manifest.json",
        report_json_path=process_dir / "CHAPTER5-RUN-REPORT.json",
        report_md_path=process_dir / "CHAPTER5-RUN-REPORT.md",
        anomaly_admission_summary_path=process_dir / "ANOMALY-ADMISSION-SUMMARY.json",
    )


def stack_correlation(sample_results: Sequence[Chapter5AnalysisResult]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for item in sample_results:
        for row_id, values in item.anomaly_correlation.to_dict(orient="index").items():
            for column_id, value in values.items():
                rows.append({"sample_id": item.sample_id, "row_id": row_id, "column_id": column_id, "correlation": value})
    return pd.DataFrame(rows)


def build_admission_payload(sample_results: Sequence[Chapter5AnalysisResult]) -> dict[str, Any]:
    return {
        "schema_version": "chapter5_anomaly_admission_summary_v1",
        "not_authorization": True,
        "blocked_claims": list(sample_results[0].blocked_claims) if sample_results else [],
        "samples": [
            {
                "sample_id": item.sample_id,
                "status": item.status,
                "anomaly_admission_summary": list(item.anomaly_admission_summary),
                "gap_register": list(item.gap_register),
            }
            for item in sample_results
        ],
        "handoff": "CR-037 必须先复验稳健性和 strict gaps；CR-038/CR-039 只能在复验后消费 alpha feature candidate。",
        "operation_counts": dict(FORBIDDEN_OPERATION_COUNTS),
    }


def render_markdown(sample_results: Sequence[Chapter5AnalysisResult], artifacts: Chapter5Artifacts) -> str:
    lines = [
        "# CR-036 第五章异象复刻报告",
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
        "| sample_id | status | panel_rows | label_rows | anomaly_panel_rows | anomaly_return_rows | alpha_test_rows |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for item in sample_results:
        lines.append(
            f"| `{item.sample_id}` | `{item.status}` | {item.panel_rows} | {item.label_rows} | {item.anomaly_panel_rows} | {item.anomaly_return_rows} | {item.alpha_test_rows} |"
        )
    lines.extend(["", "## 异象准入摘要", "", "| sample_id | anomaly_id | admission | mean_long_short | t_stat | max_abs_alpha_t |", "|---|---|---|---:|---:|---:|"])
    for item in sample_results:
        for row in item.anomaly_admission_summary:
            lines.append(
                "| `{sample}` | `{anomaly}` | `{admission}` | {mean} | {t} | {alpha_t} |".format(
                    sample=item.sample_id,
                    anomaly=row["anomaly_id"],
                    admission=row["admission"],
                    mean=_fmt(row.get("mean_long_short_return")),
                    t=_fmt(row.get("t_stat")),
                    alpha_t=_fmt(row.get("max_abs_alpha_t_stat")),
                )
            )
    lines.extend(["", "## 缺口登记", "", "| sample_id | gap_id | status | severity | impact |", "|---|---|---|---|---|"])
    for item in sample_results:
        for gap in item.gap_register:
            lines.append(f"| `{item.sample_id}` | `{gap['gap_id']}` | `{gap['status']}` | `{gap['severity']}` | {gap['impact']} |")
    lines.extend(
        [
            "",
            "## 产物",
            "",
            f"- anomaly_panel: `{artifacts.anomaly_panel_path}`",
            f"- anomaly_returns: `{artifacts.anomaly_returns_path}`",
            f"- alpha_tests: `{artifacts.alpha_tests_path}`",
            f"- anomaly_correlation: `{artifacts.anomaly_correlation_path}`",
            f"- gap_register: `{artifacts.gap_register_path}`",
            f"- anomaly_admission_summary: `{artifacts.anomaly_admission_summary_path}`",
            "",
            "## 边界",
            "",
            "本报告只允许作为项目内部第5章异象研究证据和 CR-037/CR-038/CR-039 输入，不构成 production-valid、QMT-ready、simulation-ready 或 live-ready 声明。",
            "",
        ]
    )
    return "\n".join(lines)


def _fmt(value: Any) -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return ""
    return "" if pd.isna(number) else f"{number:.6f}"


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
    observed = max_rss_bytes()
    budget_bytes = int(max_memory_gb * 1024 * 1024 * 1024)
    if observed > budget_bytes:
        raise MemoryError(
            f"第五章异象 runner 超过内存预算: context={context}, "
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
