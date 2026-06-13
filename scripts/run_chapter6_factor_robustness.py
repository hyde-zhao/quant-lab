"""CR-037 第六章因子稳健性 runner。

只读取本地第三章 factor panel / label parts 和 CR-036 异象面板，写本地
reports/process/docs 研究产物；不读取凭据、不触发 provider fetch、不写 data
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

from engine.chapter6_factor_robustness import (
    FORBIDDEN_OPERATION_COUNTS,
    Chapter6RobustnessResult,
    run_chapter6_analysis,
)
from scripts.run_chapter4_factor_models import assert_chapter3_report_pass, read_label_parts
from scripts.run_chapter5_anomalies import assert_chapter4_report_pass


CHAPTER6_RUN_SCHEMA = "chapter6_factor_robustness_run_v1"

DEFAULT_INPUTS = (
    {
        "sample_id": "in_sample_2000_2019",
        "panel_path": "reports/chapter3_factor_panel/run-chapter3-empirical-2000-2019-financial-fallback-20260610/factor_panel.parquet",
        "label_root": "process/research/chapter3_empirical/run-chapter3-empirical-2000-2019-financial-fallback-20260610/label_parts",
        "chapter3_report_path": "process/research/chapter3_empirical/run-chapter3-empirical-2000-2019-financial-fallback-20260610/EMPIRICAL-RUN-REPORT.json",
        "chapter4_report_path": "process/research/chapter4_factor_models/run-cr035-chapter4-factor-models-20260610/CHAPTER4-RUN-REPORT.json",
        "chapter5_report_path": "process/research/chapter5_anomalies/run-cr036-chapter5-anomalies-20260610/CHAPTER5-RUN-REPORT.json",
        "chapter5_anomaly_panel_path": "reports/chapter5_anomalies/run-cr036-chapter5-anomalies-20260610/anomaly_panel.parquet",
    },
    {
        "sample_id": "observation_2020_2026_ytd",
        "panel_path": "reports/chapter3_factor_panel/run-chapter3-empirical-2020-2026-ytd-financial-fallback-20260610/factor_panel.parquet",
        "label_root": "process/research/chapter3_empirical/run-chapter3-empirical-2020-2026-ytd-financial-fallback-20260610/label_parts",
        "chapter3_report_path": "process/research/chapter3_empirical/run-chapter3-empirical-2020-2026-ytd-financial-fallback-20260610/EMPIRICAL-RUN-REPORT.json",
        "chapter4_report_path": "process/research/chapter4_factor_models/run-cr035-chapter4-factor-models-20260610/CHAPTER4-RUN-REPORT.json",
        "chapter5_report_path": "process/research/chapter5_anomalies/run-cr036-chapter5-anomalies-20260610/CHAPTER5-RUN-REPORT.json",
        "chapter5_anomaly_panel_path": "reports/chapter5_anomalies/run-cr036-chapter5-anomalies-20260610/anomaly_panel.parquet",
    },
)


@dataclass(frozen=True, slots=True)
class Chapter6Artifacts:
    run_id: str
    report_dir: Path
    process_dir: Path
    guardrails_path: Path
    robustness_returns_path: Path
    rolling_ic_path: Path
    annual_factor_metrics_path: Path
    market_state_results_path: Path
    decay_report_path: Path
    ml_leakage_audit_path: Path
    manifest_path: Path
    report_json_path: Path
    report_md_path: Path
    robustness_admission_summary_path: Path

    def to_dict(self) -> dict[str, str]:
        return {key: str(value) for key, value in asdict(self).items()}


@dataclass(frozen=True, slots=True)
class Chapter6RunResult:
    run_id: str
    status: str
    sample_results: tuple[Chapter6RobustnessResult, ...]
    artifacts: Chapter6Artifacts
    memory_budget: Mapping[str, Any]
    operation_counts: Mapping[str, int] = field(default_factory=lambda: dict(FORBIDDEN_OPERATION_COUNTS))
    schema_version: str = CHAPTER6_RUN_SCHEMA

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
    parser = argparse.ArgumentParser(description="运行 CR-037 第六章因子稳健性")
    parser.add_argument("--run-id", default="")
    parser.add_argument("--output-root", default="process/research/chapter6_factor_robustness")
    parser.add_argument("--report-root", default="reports/chapter6_factor_robustness")
    parser.add_argument("--guardrails-path", default="docs/quality/FACTOR-RESEARCH-GUARDRAILS.md")
    parser.add_argument("--input-config", default="", help="可选 JSON，字段为 samples 数组")
    parser.add_argument("--min-cross-section", type=int, default=30)
    parser.add_argument("--quantiles", type=int, default=5)
    parser.add_argument("--rolling-window", type=int, default=36)
    parser.add_argument("--rolling-min-periods", type=int, default=12)
    parser.add_argument("--max-memory-gb", type=float, default=16.0)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    run_id = args.run_id or f"run-chapter6-factor-robustness-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    result = run_chapter6_from_paths(
        load_input_samples(args.input_config),
        run_id=run_id,
        output_root=Path(args.output_root),
        report_root=Path(args.report_root),
        guardrails_path=Path(args.guardrails_path),
        min_cross_section=args.min_cross_section,
        quantiles=args.quantiles,
        rolling_window=args.rolling_window,
        rolling_min_periods=args.rolling_min_periods,
        max_memory_gb=args.max_memory_gb,
    )
    print(json.dumps({"ok": True, "status": result.status, "run_id": result.run_id, "artifacts": result.artifacts.to_dict(), **FORBIDDEN_OPERATION_COUNTS}, ensure_ascii=False, sort_keys=True))
    return 0 if result.status == "PASS" else 2


def run_chapter6_from_paths(
    samples: Sequence[Mapping[str, Any]],
    *,
    run_id: str,
    output_root: Path,
    report_root: Path,
    guardrails_path: Path,
    min_cross_section: int = 30,
    quantiles: int = 5,
    rolling_window: int = 36,
    rolling_min_periods: int = 12,
    max_memory_gb: float = 16.0,
) -> Chapter6RunResult:
    artifacts = chapter6_artifacts(run_id, output_root=output_root, report_root=report_root, guardrails_path=guardrails_path)
    artifacts.report_dir.mkdir(parents=True, exist_ok=True)
    artifacts.process_dir.mkdir(parents=True, exist_ok=True)
    artifacts.guardrails_path.parent.mkdir(parents=True, exist_ok=True)
    sample_results: list[Chapter6RobustnessResult] = []
    all_anomaly_panel = read_anomaly_panel(samples)
    for sample in samples:
        sample_id = str(sample["sample_id"])
        assert_chapter3_report_pass(Path(str(sample["chapter3_report_path"])))
        assert_chapter4_report_pass(Path(str(sample["chapter4_report_path"])))
        assert_chapter5_report_pass(Path(str(sample["chapter5_report_path"])))
        panel = pd.read_parquet(Path(str(sample["panel_path"])))
        labels = read_label_parts(Path(str(sample["label_root"])))
        anomaly_panel = all_anomaly_panel[all_anomaly_panel["sample_id"] == sample_id].copy() if "sample_id" in all_anomaly_panel.columns else all_anomaly_panel.copy()
        result = run_chapter6_analysis(
            panel,
            labels,
            anomaly_panel,
            run_id=run_id,
            sample_id=sample_id,
            min_cross_section=min_cross_section,
            quantiles=quantiles,
            rolling_window=rolling_window,
            rolling_min_periods=rolling_min_periods,
        )
        sample_results.append(result)
        enforce_memory_budget(max_memory_gb, f"sample_{sample_id}")
    write_outputs(sample_results, artifacts, max_memory_gb=max_memory_gb)
    status = "PASS" if sample_results and all(item.status == "PASS" for item in sample_results) else "BLOCKED"
    return Chapter6RunResult(
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


def read_anomaly_panel(samples: Sequence[Mapping[str, Any]]) -> pd.DataFrame:
    if not samples:
        return pd.DataFrame()
    path = Path(str(samples[0]["chapter5_anomaly_panel_path"]))
    if not path.exists():
        raise RuntimeError(f"缺少 CR-036 anomaly panel: {path}")
    return pd.read_parquet(path)


def assert_chapter5_report_pass(path: Path) -> None:
    if not path.exists():
        raise RuntimeError(f"缺少第五章报告: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("status") != "PASS":
        raise RuntimeError(f"第五章报告状态不是 PASS: {path} status={data.get('status')}")


def write_outputs(
    sample_results: Sequence[Chapter6RobustnessResult],
    artifacts: Chapter6Artifacts,
    *,
    max_memory_gb: float,
) -> None:
    robustness_returns = pd.concat([item.robustness_returns.assign(sample_id=item.sample_id) for item in sample_results], ignore_index=True)
    rolling_ic = pd.concat([item.rolling_ic.assign(sample_id=item.sample_id) for item in sample_results], ignore_index=True)
    annual_metrics = pd.concat([item.annual_factor_metrics.assign(sample_id=item.sample_id) for item in sample_results], ignore_index=True)
    market_states = pd.concat([item.market_state_results.assign(sample_id=item.sample_id) for item in sample_results], ignore_index=True)
    decay = pd.concat([item.decay_report.assign(sample_id=item.sample_id) for item in sample_results], ignore_index=True)
    leakage_audit = build_leakage_payload(sample_results)
    admission = build_admission_payload(sample_results)
    robustness_returns.to_csv(artifacts.robustness_returns_path, index=False)
    rolling_ic.to_csv(artifacts.rolling_ic_path, index=False)
    annual_metrics.to_csv(artifacts.annual_factor_metrics_path, index=False)
    market_states.to_csv(artifacts.market_state_results_path, index=False)
    decay.to_csv(artifacts.decay_report_path, index=False)
    artifacts.ml_leakage_audit_path.write_text(render_ml_leakage_audit(leakage_audit), encoding="utf-8")
    artifacts.robustness_admission_summary_path.write_text(json.dumps(_json_safe(admission), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    artifacts.guardrails_path.write_text(render_guardrails(sample_results, artifacts), encoding="utf-8")
    manifest = {
        "schema_version": CHAPTER6_RUN_SCHEMA,
        "run_id": artifacts.run_id,
        "sample_results": [item.to_dict() for item in sample_results],
        "artifacts": artifacts.to_dict(),
        "memory_budget": memory_budget_summary(max_memory_gb),
        "operation_counts": dict(FORBIDDEN_OPERATION_COUNTS),
    }
    artifacts.manifest_path.write_text(json.dumps(_json_safe(manifest), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report = {
        "schema_version": CHAPTER6_RUN_SCHEMA,
        "run_id": artifacts.run_id,
        "status": "PASS" if sample_results and all(item.status == "PASS" for item in sample_results) else "BLOCKED",
        "sample_results": [item.to_dict() for item in sample_results],
        "artifacts": artifacts.to_dict(),
        "robustness_admission_summary": admission,
        "ml_leakage_audit": leakage_audit,
        "operation_counts": dict(FORBIDDEN_OPERATION_COUNTS),
    }
    artifacts.report_json_path.write_text(json.dumps(_json_safe(report), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    artifacts.report_md_path.write_text(render_markdown(sample_results, artifacts), encoding="utf-8")


def chapter6_artifacts(run_id: str, *, output_root: Path, report_root: Path, guardrails_path: Path) -> Chapter6Artifacts:
    report_dir = report_root / run_id
    process_dir = output_root / run_id
    return Chapter6Artifacts(
        run_id=run_id,
        report_dir=report_dir,
        process_dir=process_dir,
        guardrails_path=guardrails_path,
        robustness_returns_path=report_dir / "robustness_returns.csv",
        rolling_ic_path=report_dir / "rolling_ic.csv",
        annual_factor_metrics_path=report_dir / "annual_factor_metrics.csv",
        market_state_results_path=report_dir / "market_state_results.csv",
        decay_report_path=report_dir / "decay_report.csv",
        ml_leakage_audit_path=report_dir / "ml_leakage_audit.md",
        manifest_path=report_dir / "robustness_manifest.json",
        report_json_path=process_dir / "CHAPTER6-RUN-REPORT.json",
        report_md_path=process_dir / "CHAPTER6-RUN-REPORT.md",
        robustness_admission_summary_path=process_dir / "ROBUSTNESS-ADMISSION-SUMMARY.json",
    )


def build_leakage_payload(sample_results: Sequence[Chapter6RobustnessResult]) -> dict[str, Any]:
    return {
        "schema_version": "chapter6_ml_leakage_audit_payload_v1",
        "not_authorization": True,
        "samples": [{"sample_id": item.sample_id, **dict(item.ml_leakage_audit)} for item in sample_results],
        "operation_counts": dict(FORBIDDEN_OPERATION_COUNTS),
    }


def build_admission_payload(sample_results: Sequence[Chapter6RobustnessResult]) -> dict[str, Any]:
    return {
        "schema_version": "chapter6_robustness_admission_summary_v1",
        "not_authorization": True,
        "blocked_claims": list(sample_results[0].blocked_claims) if sample_results else [],
        "samples": [
            {
                "sample_id": item.sample_id,
                "status": item.status,
                "robustness_admission_summary": list(item.robustness_admission_summary),
                "guardrail_summary": list(item.guardrail_summary),
                "ml_leakage_audit": dict(item.ml_leakage_audit),
            }
            for item in sample_results
        ],
        "handoff": "CR-038/CR-039 只能消费 baseline/candidate；watch/reject/needs-more-data 必须保留风险说明或剔除。",
        "operation_counts": dict(FORBIDDEN_OPERATION_COUNTS),
    }


def render_markdown(sample_results: Sequence[Chapter6RobustnessResult], artifacts: Chapter6Artifacts) -> str:
    lines = [
        "# CR-037 第六章因子稳健性报告",
        "",
        f"- run_id: `{artifacts.run_id}`",
        f"- status: `{'PASS' if sample_results and all(item.status == 'PASS' for item in sample_results) else 'BLOCKED'}`",
        "- provider_fetch: `0`",
        "- lake_write: `0`",
        "- catalog_publish: `0`",
        "- qmt_operation: `0`",
        "- simulation_or_live: `0`",
        "- ml_training_authorized: `false`",
        "",
        "## 样本摘要",
        "",
        "| sample_id | status | asset_count | return_rows | rolling_ic_rows | annual_rows | market_state_rows | decay_rows | leakage_status |",
        "|---|---|---:|---:|---:|---:|---:|---:|---|",
    ]
    for item in sample_results:
        lines.append(
            f"| `{item.sample_id}` | `{item.status}` | {len(item.asset_ids)} | {item.robustness_return_rows} | {item.rolling_ic_rows} | {item.annual_metric_rows} | {item.market_state_rows} | {item.decay_rows} | `{item.ml_leakage_audit.get('status')}` |"
        )
    lines.extend(["", "## 准入摘要", "", "| sample_id | asset_type | asset_id | admission | mean_ls | t_stat | mean_rank_ic | positive_year_ratio |", "|---|---|---|---|---:|---:|---:|---:|"])
    for item in sample_results:
        for row in item.robustness_admission_summary:
            lines.append(
                "| `{sample}` | `{asset_type}` | `{asset_id}` | `{admission}` | {mean} | {t} | {ic} | {year_ratio} |".format(
                    sample=item.sample_id,
                    asset_type=row["asset_type"],
                    asset_id=row["asset_id"],
                    admission=row["admission"],
                    mean=_fmt(row.get("mean_long_short_return")),
                    t=_fmt(row.get("t_stat")),
                    ic=_fmt(row.get("mean_rank_ic")),
                    year_ratio=_fmt(row.get("positive_year_ratio")),
                )
            )
    lines.extend(["", "## 护栏摘要", "", "| sample_id | guardrail_id | status | rule |", "|---|---|---|---|"])
    for item in sample_results:
        for row in item.guardrail_summary:
            lines.append(f"| `{item.sample_id}` | `{row['guardrail_id']}` | `{row['status']}` | {row['rule']} |")
    lines.extend(
        [
            "",
            "## 产物",
            "",
            f"- guardrails: `{artifacts.guardrails_path}`",
            f"- robustness_returns: `{artifacts.robustness_returns_path}`",
            f"- rolling_ic: `{artifacts.rolling_ic_path}`",
            f"- annual_factor_metrics: `{artifacts.annual_factor_metrics_path}`",
            f"- market_state_results: `{artifacts.market_state_results_path}`",
            f"- decay_report: `{artifacts.decay_report_path}`",
            f"- ml_leakage_audit: `{artifacts.ml_leakage_audit_path}`",
            f"- robustness_admission_summary: `{artifacts.robustness_admission_summary_path}`",
            "",
            "## 边界",
            "",
            "本报告只允许作为项目内部因子 / 异象稳健性证据和 CR-038/CR-039 输入，不构成 production-valid、QMT-ready、simulation-ready、live-ready 或 ML-model-ready 声明。",
            "",
        ]
    )
    return "\n".join(lines)


def render_guardrails(sample_results: Sequence[Chapter6RobustnessResult], artifacts: Chapter6Artifacts) -> str:
    lines = [
        "# 因子研究护栏",
        "",
        f"- source_cr: `CR-037`",
        f"- run_id: `{artifacts.run_id}`",
        "- status: `active`",
        "- runtime_authorization: `not-authorized`",
        "",
        "## 核心规则",
        "",
        "| guardrail_id | rule |",
        "|---|---|",
    ]
    rules: dict[str, str] = {}
    for item in sample_results:
        for row in item.guardrail_summary:
            rules[str(row["guardrail_id"])] = str(row["rule"])
    for guardrail_id, rule in sorted(rules.items()):
        lines.append(f"| `{guardrail_id}` | {rule} |")
    lines.extend(
        [
            "",
            "## 准入边界",
            "",
            "- `baseline` 和 `candidate` 只能作为 CR-038 / CR-039 的研究输入，不自动授权组合优化、模拟盘或实盘。",
            "- `watch`、`reject`、`needs-more-data` 必须保留风险说明；策略层默认不得直接消费。",
            "- ML 研究必须先声明时间切分、purge / embargo、label overlap 防护和解释性边界。",
            "- 任一新增 provider fetch、lake write、catalog publish、QMT、simulation、live、账户 / 订单或凭据读取都必须另起 CR。",
            "",
            "## 证据入口",
            "",
            f"- report: `{artifacts.report_md_path}`",
            f"- admission: `{artifacts.robustness_admission_summary_path}`",
            f"- leakage_audit: `{artifacts.ml_leakage_audit_path}`",
            "",
        ]
    )
    return "\n".join(lines)


def render_ml_leakage_audit(payload: Mapping[str, Any]) -> str:
    lines = ["# CR-037 ML Leakage Audit", "", "| sample_id | status | factor_leakage_count | anomaly_leakage_count | policy |", "|---|---|---:|---:|---|"]
    for item in payload.get("samples", []):
        lines.append(
            f"| `{item.get('sample_id')}` | `{item.get('status')}` | {item.get('factor_leakage_count')} | {item.get('anomaly_leakage_count')} | `{item.get('recommended_split_policy')}` |"
        )
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "CR-037 only audits leakage boundaries. It does not train, tune, select, deploy, or authorize any ML model.",
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
            f"第六章稳健性 runner 超过内存预算: context={context}, "
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
