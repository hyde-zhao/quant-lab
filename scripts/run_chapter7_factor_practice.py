"""CR-038 第七章因子投资实践 runner。

只读取本地第三章 factor panel / label parts 和 CR-037
ROBUSTNESS-ADMISSION-SUMMARY，写本地 reports/process 研究产物；不读取凭据、
不触发 provider fetch、不写 data lake、不 publish catalog、不触发 QMT /
simulation / live。
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

from engine.chapter7_factor_practice import (
    FORBIDDEN_OPERATION_COUNTS,
    Chapter7AnalysisResult,
    Chapter7Config,
    run_chapter7_analysis,
)
from scripts.run_chapter4_factor_models import assert_chapter3_report_pass, read_label_parts


CHAPTER7_RUN_SCHEMA = "chapter7_factor_practice_run_v1"

DEFAULT_INPUTS = (
    {
        "sample_id": "in_sample_2000_2019",
        "panel_path": "reports/chapter3_factor_panel/run-chapter3-empirical-2000-2019-financial-fallback-20260610/factor_panel.parquet",
        "label_root": "process/research/chapter3_empirical/run-chapter3-empirical-2000-2019-financial-fallback-20260610/label_parts",
        "chapter3_report_path": "process/research/chapter3_empirical/run-chapter3-empirical-2000-2019-financial-fallback-20260610/EMPIRICAL-RUN-REPORT.json",
        "robustness_admission_summary_path": "process/research/chapter6_factor_robustness/run-cr037-chapter6-robustness-20260610/ROBUSTNESS-ADMISSION-SUMMARY.json",
    },
    {
        "sample_id": "observation_2020_2026_ytd",
        "panel_path": "reports/chapter3_factor_panel/run-chapter3-empirical-2020-2026-ytd-financial-fallback-20260610/factor_panel.parquet",
        "label_root": "process/research/chapter3_empirical/run-chapter3-empirical-2020-2026-ytd-financial-fallback-20260610/label_parts",
        "chapter3_report_path": "process/research/chapter3_empirical/run-chapter3-empirical-2020-2026-ytd-financial-fallback-20260610/EMPIRICAL-RUN-REPORT.json",
        "robustness_admission_summary_path": "process/research/chapter6_factor_robustness/run-cr037-chapter6-robustness-20260610/ROBUSTNESS-ADMISSION-SUMMARY.json",
    },
)


@dataclass(frozen=True, slots=True)
class Chapter7Artifacts:
    run_id: str
    report_dir: Path
    process_dir: Path
    alpha_scores_path: Path
    optimized_portfolios_path: Path
    portfolio_metrics_path: Path
    risk_exposure_path: Path
    performance_attribution_path: Path
    turnover_cost_analysis_path: Path
    capacity_liquidity_analysis_path: Path
    manifest_path: Path
    report_json_path: Path
    report_md_path: Path
    portfolio_admission_summary_path: Path

    def to_dict(self) -> dict[str, str]:
        return {key: str(value) for key, value in asdict(self).items()}


@dataclass(frozen=True, slots=True)
class Chapter7RunResult:
    run_id: str
    status: str
    sample_results: tuple[Chapter7AnalysisResult, ...]
    artifacts: Chapter7Artifacts
    memory_budget: Mapping[str, Any]
    operation_counts: Mapping[str, int] = field(default_factory=lambda: dict(FORBIDDEN_OPERATION_COUNTS))
    schema_version: str = CHAPTER7_RUN_SCHEMA

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
    parser = argparse.ArgumentParser(description="运行 CR-038 第七章因子投资实践")
    parser.add_argument("--run-id", default="")
    parser.add_argument("--output-root", default="process/research/chapter7_factor_practice")
    parser.add_argument("--report-root", default="reports/chapter7_factor_practice")
    parser.add_argument("--input-config", default="", help="可选 JSON，字段为 samples 数组")
    parser.add_argument("--min-cross-section", type=int, default=30)
    parser.add_argument("--top-fraction", type=float, default=0.2)
    parser.add_argument("--max-weight", type=float, default=0.08)
    parser.add_argument("--cost-bps", default="0,5,10,25,50")
    parser.add_argument("--capacity-notional", default="10000000,50000000,100000000")
    parser.add_argument("--max-memory-gb", type=float, default=16.0)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    run_id = args.run_id or f"run-chapter7-factor-practice-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    result = run_chapter7_from_paths(
        load_input_samples(args.input_config),
        run_id=run_id,
        output_root=Path(args.output_root),
        report_root=Path(args.report_root),
        min_cross_section=args.min_cross_section,
        top_fraction=args.top_fraction,
        max_weight=args.max_weight,
        cost_bps_scenarios=parse_float_list(args.cost_bps, field_name="cost-bps"),
        capacity_notional_scenarios=parse_float_list(args.capacity_notional, field_name="capacity-notional"),
        max_memory_gb=args.max_memory_gb,
    )
    print(
        json.dumps(
            {"ok": True, "status": result.status, "run_id": result.run_id, "artifacts": result.artifacts.to_dict(), **FORBIDDEN_OPERATION_COUNTS},
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0 if result.status == "PASS" else 2


def run_chapter7_from_paths(
    samples: Sequence[Mapping[str, Any]],
    *,
    run_id: str,
    output_root: Path,
    report_root: Path,
    min_cross_section: int = 30,
    top_fraction: float = 0.2,
    max_weight: float = 0.08,
    cost_bps_scenarios: Sequence[float] = (0.0, 5.0, 10.0, 25.0, 50.0),
    capacity_notional_scenarios: Sequence[float] = (10_000_000.0, 50_000_000.0, 100_000_000.0),
    max_memory_gb: float = 16.0,
) -> Chapter7RunResult:
    artifacts = chapter7_artifacts(run_id, output_root=output_root, report_root=report_root)
    artifacts.report_dir.mkdir(parents=True, exist_ok=True)
    artifacts.process_dir.mkdir(parents=True, exist_ok=True)
    sample_results: list[Chapter7AnalysisResult] = []
    admission_summary = read_robustness_admission_summary(samples)
    assert_robustness_admission_summary_usable(admission_summary)
    for sample in samples:
        sample_id = str(sample["sample_id"])
        assert_chapter3_report_pass(Path(str(sample["chapter3_report_path"])), allow_limitations=True)
        panel = pd.read_parquet(Path(str(sample["panel_path"])))
        labels = read_label_parts(Path(str(sample["label_root"])))
        result = run_chapter7_analysis(
            panel,
            labels,
            admission_summary,
            run_id=run_id,
            sample_id=sample_id,
            config=Chapter7Config(
                top_n=max(1, int(150 * top_fraction)),
                min_cross_section=min_cross_section,
                max_weight=max_weight,
                cost_bps=tuple(float(value) for value in cost_bps_scenarios),
            ),
        )
        sample_results.append(result)
        enforce_memory_budget(max_memory_gb, f"sample_{sample_id}")
    write_outputs(sample_results, artifacts, max_memory_gb=max_memory_gb)
    status = "PASS" if sample_results and all(item.status == "PASS" for item in sample_results) else "WATCH"
    return Chapter7RunResult(
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


def read_robustness_admission_summary(samples: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    if not samples:
        raise ValueError("samples 不能为空")
    path = Path(str(samples[0]["robustness_admission_summary_path"]))
    if not path.exists():
        raise RuntimeError(f"缺少 CR-037 ROBUSTNESS-ADMISSION-SUMMARY: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def assert_robustness_admission_summary_usable(summary: Mapping[str, Any]) -> None:
    if summary.get("schema_version") != "chapter6_robustness_admission_summary_v1":
        raise RuntimeError(f"CR-037 summary schema 不匹配: {summary.get('schema_version')}")
    counts = summary.get("operation_counts") or {}
    nonzero = {key: value for key, value in counts.items() if int(value or 0) != 0}
    if nonzero:
        raise RuntimeError("CR-037 summary operation_counts 必须全为 0: " + ",".join(sorted(nonzero)))
    samples = summary.get("samples")
    if not isinstance(samples, list) or not samples:
        raise RuntimeError("CR-037 summary 缺少 samples")
    eligible = 0
    for sample in samples:
        for row in sample.get("robustness_admission_summary") or []:
            if row.get("asset_type") == "factor" and row.get("admission") in {"baseline", "candidate"}:
                eligible += 1
    if eligible <= 0:
        raise RuntimeError("CR-037 summary 没有 baseline/candidate 因子，CR-038 fail-closed")


def write_outputs(
    sample_results: Sequence[Chapter7AnalysisResult],
    artifacts: Chapter7Artifacts,
    *,
    max_memory_gb: float,
) -> None:
    alpha_scores = pd.concat([item.alpha_scores.assign(sample_id=item.sample_id) for item in sample_results], ignore_index=True)
    portfolios = pd.concat([item.optimized_portfolios.assign(sample_id=item.sample_id) for item in sample_results], ignore_index=True)
    metrics = pd.concat([item.portfolio_metrics.assign(sample_id=item.sample_id) for item in sample_results], ignore_index=True)
    risk = pd.concat([item.risk_exposure.assign(sample_id=item.sample_id) for item in sample_results], ignore_index=True)
    attribution = pd.concat([item.performance_attribution.assign(sample_id=item.sample_id) for item in sample_results], ignore_index=True)
    costs = pd.concat([item.turnover_cost_analysis.assign(sample_id=item.sample_id) for item in sample_results], ignore_index=True)
    capacity = pd.concat([item.capacity_liquidity_analysis.assign(sample_id=item.sample_id) for item in sample_results], ignore_index=True)
    admission = build_admission_payload(sample_results)
    alpha_scores.to_parquet(artifacts.alpha_scores_path, index=False)
    portfolios.to_parquet(artifacts.optimized_portfolios_path, index=False)
    metrics.to_csv(artifacts.portfolio_metrics_path, index=False)
    risk.to_csv(artifacts.risk_exposure_path, index=False)
    attribution.to_csv(artifacts.performance_attribution_path, index=False)
    costs.to_csv(artifacts.turnover_cost_analysis_path, index=False)
    capacity.to_csv(artifacts.capacity_liquidity_analysis_path, index=False)
    artifacts.portfolio_admission_summary_path.write_text(json.dumps(_json_safe(admission), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    manifest = {
        "schema_version": CHAPTER7_RUN_SCHEMA,
        "run_id": artifacts.run_id,
        "sample_results": [item.to_dict() for item in sample_results],
        "artifacts": artifacts.to_dict(),
        "memory_budget": memory_budget_summary(max_memory_gb),
        "operation_counts": dict(FORBIDDEN_OPERATION_COUNTS),
    }
    artifacts.manifest_path.write_text(json.dumps(_json_safe(manifest), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report = {
        "schema_version": CHAPTER7_RUN_SCHEMA,
        "run_id": artifacts.run_id,
        "status": "PASS" if sample_results and all(item.status == "PASS" for item in sample_results) else "WATCH",
        "sample_results": [item.to_dict() for item in sample_results],
        "artifacts": artifacts.to_dict(),
        "portfolio_admission_summary": admission,
        "operation_counts": dict(FORBIDDEN_OPERATION_COUNTS),
    }
    artifacts.report_json_path.write_text(json.dumps(_json_safe(report), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    artifacts.report_md_path.write_text(render_markdown(sample_results, artifacts), encoding="utf-8")


def chapter7_artifacts(run_id: str, *, output_root: Path, report_root: Path) -> Chapter7Artifacts:
    report_dir = report_root / run_id
    process_dir = output_root / run_id
    return Chapter7Artifacts(
        run_id=run_id,
        report_dir=report_dir,
        process_dir=process_dir,
        alpha_scores_path=report_dir / "alpha_scores.parquet",
        optimized_portfolios_path=report_dir / "optimized_portfolios.parquet",
        portfolio_metrics_path=report_dir / "portfolio_metrics.csv",
        risk_exposure_path=report_dir / "risk_exposure.csv",
        performance_attribution_path=report_dir / "performance_attribution.csv",
        turnover_cost_analysis_path=report_dir / "turnover_cost_analysis.csv",
        capacity_liquidity_analysis_path=report_dir / "capacity_liquidity_analysis.csv",
        manifest_path=report_dir / "chapter7_manifest.json",
        report_json_path=process_dir / "CHAPTER7-RUN-REPORT.json",
        report_md_path=process_dir / "CHAPTER7-RUN-REPORT.md",
        portfolio_admission_summary_path=process_dir / "PORTFOLIO-ADMISSION-SUMMARY.json",
    )


def build_admission_payload(sample_results: Sequence[Chapter7AnalysisResult]) -> dict[str, Any]:
    return {
        "schema_version": "chapter7_portfolio_admission_payload_v1",
        "not_authorization": True,
        "blocked_claims": list(sample_results[0].blocked_claims) if sample_results else [],
        "samples": [
            {
                "sample_id": item.sample_id,
                "status": item.status,
                "allowed_assets": [asset.to_dict() for asset in item.allowed_assets],
                "watch_assets_policy": [asset.to_dict() for asset in item.watch_assets],
                "rejected_assets_excluded": [asset.to_dict() for asset in item.rejected_assets],
                "portfolio_admission_summary": list(item.portfolio_admission_summary),
            }
            for item in sample_results
        ],
        "handoff": "CR-039 只能消费 research_candidate / observation 字段；本摘要不授权 QMT、simulation、live、provider、lake 或 publish。",
        "operation_counts": dict(FORBIDDEN_OPERATION_COUNTS),
    }


def render_markdown(sample_results: Sequence[Chapter7AnalysisResult], artifacts: Chapter7Artifacts) -> str:
    lines = [
        "# CR-038 第七章因子投资实践报告",
        "",
        f"- run_id: `{artifacts.run_id}`",
        f"- status: `{'PASS' if sample_results and all(item.status == 'PASS' for item in sample_results) else 'WATCH'}`",
        "- provider_fetch: `0`",
        "- lake_write: `0`",
        "- catalog_publish: `0`",
        "- qmt_operation: `0`",
        "- simulation_or_live: `0`",
        "- credential_read: `0`",
        "",
        "## 样本摘要",
        "",
        "| sample_id | status | allowed_assets | alpha_rows | weight_rows | metric_rows | risk_rows | attribution_rows | cost_rows | capacity_rows |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for item in sample_results:
        lines.append(
            f"| `{item.sample_id}` | `{item.status}` | {len(item.allowed_assets)} | {item.alpha_score_rows} | {item.portfolio_weight_rows} | {item.portfolio_metric_rows} | {item.risk_exposure_rows} | {item.attribution_rows} | {item.cost_rows} | {item.capacity_rows} |"
        )
    lines.extend(["", "## 组合准入摘要", "", "| sample_id | portfolio_id | admission | capacity_evidence | simulation_candidate | mean_net_25bps |", "|---|---|---|---|---|---:|"])
    for item in sample_results:
        for row in item.portfolio_admission_summary:
            lines.append(
                "| `{sample}` | `{portfolio}` | `{admission}` | `{capacity}` | `{simulation}` | {mean_net} |".format(
                    sample=item.sample_id,
                    portfolio=row.get("portfolio_id"),
                    admission=row.get("admission"),
                    capacity=row.get("capacity_evidence"),
                    simulation=str(row.get("simulation_candidate")).lower(),
                    mean_net=_fmt(row.get("net_mean_return_25bps")),
                )
            )
    lines.extend(
        [
            "",
            "## 产物",
            "",
            f"- alpha_scores: `{artifacts.alpha_scores_path}`",
            f"- optimized_portfolios: `{artifacts.optimized_portfolios_path}`",
            f"- portfolio_metrics: `{artifacts.portfolio_metrics_path}`",
            f"- risk_exposure: `{artifacts.risk_exposure_path}`",
            f"- performance_attribution: `{artifacts.performance_attribution_path}`",
            f"- turnover_cost_analysis: `{artifacts.turnover_cost_analysis_path}`",
            f"- capacity_liquidity_analysis: `{artifacts.capacity_liquidity_analysis_path}`",
            f"- portfolio_admission_summary: `{artifacts.portfolio_admission_summary_path}`",
            "",
            "## 边界",
            "",
            "本报告只允许作为项目内部组合研究证据和 CR-039 研究输入，不构成 production-valid、QMT-ready、simulation-ready、live-ready、provider-ready、lake-ready 或 publish-ready 声明。",
            "",
        ]
    )
    return "\n".join(lines)


def parse_float_list(value: str, *, field_name: str) -> tuple[float, ...]:
    try:
        parsed = tuple(float(item.strip()) for item in value.split(",") if item.strip())
    except ValueError as exc:
        raise ValueError(f"{field_name} 必须是逗号分隔数字") from exc
    if not parsed:
        raise ValueError(f"{field_name} 不能为空")
    return parsed


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
            f"第七章组合实践 runner 超过内存预算: context={context}, "
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
