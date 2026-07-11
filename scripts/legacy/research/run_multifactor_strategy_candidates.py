"""CR-039 多因子策略候选研究 runner。

只读取 CR-038 组合研究 artifact，写 NAS reports/runs 研究产物；
不读取凭据、不访问网络、不写 data lake、不 publish catalog、不触发 QMT /
simulation / live。
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("NUMEXPR_NUM_THREADS", "1")

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from engine.multifactor_strategy_candidates import (
    FORBIDDEN_OPERATION_COUNTS,
    StrategyResearchResult,
    run_strategy_research,
)
from engine.mature_multifactor_research import ProducerLineageConfig
from engine.research_cli import enforce_memory_budget, json_safe as _json_safe, memory_budget_summary
from engine.research_paths import research_report_path, research_run_path
from scripts.research.run_multifactor_strategy_research import parse_producer_lineage_cli_pair


CR039_RUN_SCHEMA = "multifactor_strategy_candidates_run_v1"
DEFAULT_CR038_RUN_ID = "run-cr038-chapter7-factor-practice-20260610"


@dataclass(frozen=True, slots=True)
class StrategyCandidateArtifacts:
    run_id: str
    report_dir: Path
    process_dir: Path
    strategy_scores_path: Path
    backtest_results_path: Path
    factor_contribution_path: Path
    risk_cost_summary_path: Path
    manifest_path: Path
    report_json_path: Path
    report_md_path: Path
    admission_package_path: Path

    def to_dict(self) -> dict[str, str]:
        return {key: str(value) for key, value in asdict(self).items()}


@dataclass(frozen=True, slots=True)
class StrategyCandidateRunResult:
    run_id: str
    status: str
    research_result: StrategyResearchResult
    artifacts: StrategyCandidateArtifacts
    memory_budget: Mapping[str, Any]
    operation_counts: Mapping[str, int] = field(default_factory=lambda: dict(FORBIDDEN_OPERATION_COUNTS))
    schema_version: str = CR039_RUN_SCHEMA

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "run_id": self.run_id,
            "status": self.status,
            "research_result": self.research_result.to_dict(),
            "artifacts": self.artifacts.to_dict(),
            "memory_budget": dict(self.memory_budget),
            "operation_counts": dict(self.operation_counts),
        }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="运行多因子策略候选研究")
    parser.add_argument("--run-id", default="")
    parser.add_argument("--output-root", default=str(research_run_path("multifactor_strategy_candidates")))
    parser.add_argument("--report-root", default=str(research_report_path("multifactor_strategy_candidates")))
    parser.add_argument("--cr038-run-id", default=DEFAULT_CR038_RUN_ID)
    parser.add_argument("--portfolio-admission-summary", default="")
    parser.add_argument("--cr035-model-admission-summary", default=str(research_run_path("chapter4_factor_models", "run-cr035-chapter4-factor-models-20260610", "MODEL-ADMISSION-SUMMARY.json")))
    parser.add_argument("--cr036-anomaly-admission-summary", default=str(research_run_path("chapter5_anomalies", "run-cr036-chapter5-anomalies-20260610", "ANOMALY-ADMISSION-SUMMARY.json")))
    parser.add_argument("--cr037-robustness-admission-summary", default=str(research_run_path("chapter6_factor_robustness", "run-cr037-chapter6-robustness-20260610", "ROBUSTNESS-ADMISSION-SUMMARY.json")))
    parser.add_argument("--chapter7-report-root", default=str(research_report_path("chapter7_factor_practice")))
    parser.add_argument("--chapter7-process-root", default=str(research_run_path("chapter7_factor_practice")))
    parser.add_argument("--max-memory-gb", type=float, default=16.0)
    parser.add_argument("--lineage-spec", default=None)
    parser.add_argument("--lineage-root", default=None)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    lineage_config = parse_producer_lineage_cli_pair(
        lineage_spec=args.lineage_spec,
        lineage_root=args.lineage_root,
        producer_chain_id="legacy_cr039",
    )
    run_id = args.run_id or f"run-multifactor-strategy-candidates-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    result = run_strategy_candidates_from_paths(
        run_id=run_id,
        output_root=Path(args.output_root),
        report_root=Path(args.report_root),
        cr038_run_id=args.cr038_run_id,
        portfolio_admission_summary=Path(args.portfolio_admission_summary) if args.portfolio_admission_summary else None,
        cr035_model_admission_summary=Path(args.cr035_model_admission_summary),
        cr036_anomaly_admission_summary=Path(args.cr036_anomaly_admission_summary),
        cr037_robustness_admission_summary=Path(args.cr037_robustness_admission_summary),
        chapter7_report_root=Path(args.chapter7_report_root),
        chapter7_process_root=Path(args.chapter7_process_root),
        max_memory_gb=args.max_memory_gb,
        lineage_config=lineage_config,
    )
    print(
        json.dumps(
            {"ok": True, "status": result.status, "run_id": result.run_id, "artifacts": result.artifacts.to_dict(), **FORBIDDEN_OPERATION_COUNTS},
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0 if result.status == "PASS" else 2


def run_strategy_candidates_from_paths(
    *,
    run_id: str,
    output_root: Path,
    report_root: Path,
    cr038_run_id: str = DEFAULT_CR038_RUN_ID,
    portfolio_admission_summary: Path | None = None,
    cr035_model_admission_summary: Path = research_run_path("chapter4_factor_models", "run-cr035-chapter4-factor-models-20260610", "MODEL-ADMISSION-SUMMARY.json"),
    cr036_anomaly_admission_summary: Path = research_run_path("chapter5_anomalies", "run-cr036-chapter5-anomalies-20260610", "ANOMALY-ADMISSION-SUMMARY.json"),
    cr037_robustness_admission_summary: Path = research_run_path("chapter6_factor_robustness", "run-cr037-chapter6-robustness-20260610", "ROBUSTNESS-ADMISSION-SUMMARY.json"),
    chapter7_report_root: Path = research_report_path("chapter7_factor_practice"),
    chapter7_process_root: Path = research_run_path("chapter7_factor_practice"),
    max_memory_gb: float = 16.0,
    lineage_config: ProducerLineageConfig | None = None,
) -> StrategyCandidateRunResult:
    artifacts = strategy_candidate_artifacts(run_id, output_root=output_root, report_root=report_root)
    artifacts.report_dir.mkdir(parents=True, exist_ok=True)
    artifacts.process_dir.mkdir(parents=True, exist_ok=True)

    cr038_report_dir = chapter7_report_root / cr038_run_id
    cr038_process_dir = chapter7_process_root / cr038_run_id
    admission_path = portfolio_admission_summary or cr038_process_dir / "PORTFOLIO-ADMISSION-SUMMARY.json"
    input_refs = {
        "cr038_portfolio_admission_summary": str(admission_path),
        "cr035_model_admission_summary": str(cr035_model_admission_summary),
        "cr036_anomaly_admission_summary": str(cr036_anomaly_admission_summary),
        "cr037_robustness_admission_summary": str(cr037_robustness_admission_summary),
        "cr038_alpha_scores": str(cr038_report_dir / "alpha_scores.parquet"),
        "cr038_portfolio_metrics": str(cr038_report_dir / "portfolio_metrics.csv"),
        "cr038_turnover_cost_analysis": str(cr038_report_dir / "turnover_cost_analysis.csv"),
        "cr038_capacity_liquidity_analysis": str(cr038_report_dir / "capacity_liquidity_analysis.csv"),
        "cr038_risk_exposure": str(cr038_report_dir / "risk_exposure.csv"),
        "cr038_performance_attribution": str(cr038_report_dir / "performance_attribution.csv"),
    }
    payload = json.loads(admission_path.read_text(encoding="utf-8"))
    upstream_summaries = {
        "cr035_model_admission": json.loads(cr035_model_admission_summary.read_text(encoding="utf-8")),
        "cr036_anomaly_admission": json.loads(cr036_anomaly_admission_summary.read_text(encoding="utf-8")),
        "cr037_robustness_admission": json.loads(cr037_robustness_admission_summary.read_text(encoding="utf-8")),
    }
    result = run_strategy_research(
        run_id=run_id,
        upstream_research_summaries=upstream_summaries,
        portfolio_admission_payload=payload,
        alpha_scores=pd.read_parquet(cr038_report_dir / "alpha_scores.parquet"),
        portfolio_metrics=pd.read_csv(cr038_report_dir / "portfolio_metrics.csv"),
        turnover_cost_analysis=pd.read_csv(cr038_report_dir / "turnover_cost_analysis.csv"),
        capacity_liquidity_analysis=pd.read_csv(cr038_report_dir / "capacity_liquidity_analysis.csv"),
        risk_exposure=pd.read_csv(cr038_report_dir / "risk_exposure.csv"),
        performance_attribution=pd.read_csv(cr038_report_dir / "performance_attribution.csv"),
        input_refs=input_refs,
        lineage_config=lineage_config,
    )
    write_outputs(result, artifacts, max_memory_gb=max_memory_gb)
    enforce_memory_budget(max_memory_gb, "cr039_strategy_candidates")
    return StrategyCandidateRunResult(
        run_id=run_id,
        status=result.status,
        research_result=result,
        artifacts=artifacts,
        memory_budget=memory_budget_summary(max_memory_gb),
        operation_counts=dict(FORBIDDEN_OPERATION_COUNTS),
    )


def write_outputs(result: StrategyResearchResult, artifacts: StrategyCandidateArtifacts, *, max_memory_gb: float) -> None:
    if not result.strategy_scores.empty:
        result.strategy_scores.to_parquet(artifacts.strategy_scores_path, index=False)
    else:
        pd.DataFrame().to_parquet(artifacts.strategy_scores_path, index=False)
    result.backtest_results.to_csv(artifacts.backtest_results_path, index=False)
    result.factor_contribution.to_csv(artifacts.factor_contribution_path, index=False)
    result.risk_cost_summary.to_csv(artifacts.risk_cost_summary_path, index=False)
    artifacts.admission_package_path.write_text(
        json.dumps(_json_safe(result.admission_package), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    manifest = {
        "schema_version": CR039_RUN_SCHEMA,
        "run_id": artifacts.run_id,
        "status": result.status,
        "artifacts": artifacts.to_dict(),
        "memory_budget": memory_budget_summary(max_memory_gb),
        "operation_counts": dict(FORBIDDEN_OPERATION_COUNTS),
    }
    artifacts.manifest_path.write_text(json.dumps(_json_safe(manifest), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report = {
        "schema_version": CR039_RUN_SCHEMA,
        "run_id": artifacts.run_id,
        "status": result.status,
        "research_result": result.to_dict(),
        "artifacts": artifacts.to_dict(),
        "operation_counts": dict(FORBIDDEN_OPERATION_COUNTS),
    }
    artifacts.report_json_path.write_text(json.dumps(_json_safe(report), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    artifacts.report_md_path.write_text(render_markdown(result, artifacts), encoding="utf-8")


def strategy_candidate_artifacts(run_id: str, *, output_root: Path, report_root: Path) -> StrategyCandidateArtifacts:
    report_dir = report_root / run_id
    process_dir = output_root / run_id
    return StrategyCandidateArtifacts(
        run_id=run_id,
        report_dir=report_dir,
        process_dir=process_dir,
        strategy_scores_path=report_dir / "strategy_scores.parquet",
        backtest_results_path=report_dir / "backtest_results.csv",
        factor_contribution_path=report_dir / "factor_contribution.csv",
        risk_cost_summary_path=report_dir / "risk_cost_summary.csv",
        manifest_path=report_dir / "strategy_candidates_manifest.json",
        report_json_path=process_dir / "STRATEGY-RESEARCH-REPORT.json",
        report_md_path=process_dir / "STRATEGY-RESEARCH-REPORT.md",
        admission_package_path=process_dir / "STRATEGY-ADMISSION-PACKAGE.json",
    )


def render_markdown(result: StrategyResearchResult, artifacts: StrategyCandidateArtifacts) -> str:
    lines = [
        "# CR-039 多因子策略候选研究报告",
        "",
        f"- run_id: `{artifacts.run_id}`",
        f"- status: `{result.status}`",
        "- provider_fetch: `0`",
        "- lake_write: `0`",
        "- catalog_publish: `0`",
        "- qmt_operation: `0`",
        "- simulation_or_live: `0`",
        "- credential_read: `0`",
        "",
        "## 策略候选",
        "",
        "| strategy_id | source_portfolio_id | admission | simulation_candidate | mean_net_25bps | mean_turnover | capacity_evidence |",
        "|---|---|---|---|---:|---:|---|",
    ]
    for item in result.strategy_candidates:
        lines.append(
            f"| `{item.strategy_id}` | `{item.source_portfolio_id}` | `{item.admission}` | `{str(item.simulation_candidate).lower()}` | {item.mean_net_return_25bps:.6f} | {item.mean_turnover:.6f} | `{item.capacity_evidence}` |"
        )
    lines.extend(["", "## 窗口覆盖", "", "| evaluation_window | strategy_count | rows | mean_net_25bps |", "|---|---:|---:|---:|"])
    if not result.risk_cost_summary.empty:
        for window, group in result.risk_cost_summary.groupby("evaluation_window", sort=True):
            mean_net = pd.to_numeric(group["mean_net_return_25bps"], errors="coerce").mean()
            lines.append(f"| `{window}` | {group['strategy_id'].nunique()} | {len(group)} | {mean_net:.6f} |")
    lines.extend(
        [
            "",
            "## 产物",
            "",
            f"- strategy_scores: `{artifacts.strategy_scores_path}`",
            f"- backtest_results: `{artifacts.backtest_results_path}`",
            f"- factor_contribution: `{artifacts.factor_contribution_path}`",
            f"- risk_cost_summary: `{artifacts.risk_cost_summary_path}`",
            f"- strategy_admission_package: `{artifacts.admission_package_path}`",
            "",
            "## 边界",
            "",
            "本报告只允许作为本地离线研究候选和后续人工决策输入，不构成 QMT-ready、simulation-ready、live-ready、production-valid、account/order-ready、provider-ready、lake-ready 或 publish-ready 声明。",
            "",
        ]
    )
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
