---
change_id: "CR-030"
title: "CR030 因子研究快速开始"
status: "draft-for-cp8-review"
created_at: "2026-06-03"
owner: "meta-po"
source_doc: "docs/CR030-MULTIFACTOR-RESEARCH-LOOP.md"
---

# CR030 因子研究快速开始

本文是 CR-030 的操作入口，目标是让你从“新增一个因子”开始，走完项目自有的多因子研究与实验闭环，形成策略侧模拟盘入口审查输入。

本文只覆盖本地离线研究与实验。不授权 QMT / MiniQMT / XtQuant、gateway、simulation、live、账户、订单、provider fetch、lake write、publish、凭据读取、外部项目运行或新增依赖。QMT 接口 ready 和真实模拟盘投入仍由 CR-020 / CR-021 等后续 CR 单独准入。

## 1. 当前手册在哪里

| 目的 | 文件 |
|---|---|
| 快速开始 | `docs/CR030-FACTOR-RESEARCH-QUICKSTART.md` |
| CR-030 边界与证据链 | `docs/CR030-MULTIFACTOR-RESEARCH-LOOP.md` |
| 外部框架借鉴矩阵 | `docs/CR030-MULTIFACTOR-REFERENCE-MATRIX.md` |
| CP8 人工终验 | `checkpoints/CP8-CR030-DELIVERY-READINESS.md` |

## 2. 先确认本地基线

在开始研究前，先跑 CR-030 的离线安全和合同测试：

```bash
uv run --python 3.11 pytest -q tests/test_cr030_external_reference_guardrails.py tests/test_cr030_factor_spec_run_spec_contract.py tests/test_cr030_factor_panel_label_window_gates.py tests/test_cr030_factor_evaluation_report.py tests/test_cr030_multifactor_combiner.py tests/test_cr030_experiment_manifest_catalog.py tests/test_cr030_strategy_admission_package.py tests/test_cr030_no_real_operation_safety.py
```

期望结果是 CR030 测试全通过。若失败，先修复 fail-closed 原因，不要绕过 gate。

## 3. 研究闭环的顺序

```text
FactorSpec / FactorRunSpec
  -> FactorPanelContract / LabelWindowSpec
  -> FactorEvaluationReport
  -> MultiFactorPortfolioPlan
  -> ExperimentManifest / ResearchReportCatalog
  -> StrategyAdmissionPackage
```

实际做研究时，你只需要把“你的因子定义”和“你的本地离线数据”填入这些合同。缺字段、前视、标签重叠、lineage 不完整、成本 / exposure 缺失、依赖 / QMT / provider 计数非零时，系统应 fail-closed 或 research_limited。

## 4. 新增一个因子

长期维护优先从通用因子库开始，而不是把因子写到某个书籍章节或实验脚本里：

```python
from engine.factor_library import (
    EquityFactorDefinition,
    build_equity_factor_library,
    to_factor_spec,
)

definition = EquityFactorDefinition(
    factor_id="quality_gross_profit_assets",
    name="毛利资产质量因子",
    category="quality",
    raw_variable="gross_profit_ttm / total_assets",
    direction="positive",
    input_fields=("financials.gross_profit_ttm", "financials.total_assets"),
    formula="gross_profit_ttm / total_assets",
    default_window=1,
    source_refs=("internal:research:quality_factor:v1",),
)

factor_library = build_equity_factor_library([definition])
factor_spec = to_factor_spec(factor_library["quality_gross_profit_assets"])
```

如果因子有自定义公式计算，把计算器注册到 `engine.factor_calculators.compute_equity_factor_matrices(...)` 的 `calculator_registry`，不要把新因子塞进第三章复刻模块：

```python
from engine.factor_calculators import FactorCalculationContext, compute_equity_factor_matrices

def quality_gross_profit_assets(context: FactorCalculationContext):
    return context.financial_daily["gross_profit_ttm"] / context.financial_daily["total_assets"]

result = compute_equity_factor_matrices(
    close=close,
    returns=returns,
    price_frame=prices,
    financial_daily=financial_daily,
    factor_ids=("quality_gross_profit_assets",),
    calculator_registry={"quality_gross_profit_assets": quality_gross_profit_assets},
)
```

已沉淀的第三章七个因子位于 `engine.factor_library.equity_core_factor_definitions()`；第三章来源只在 `source_refs` 中记录，因子 ID 不使用 `chapter3` 前缀。

若只是一次性探索，也可以直接从 `FactorSpec` 开始。下面是最小形态：

```python
from engine.multifactor_contracts import (
    BLOCKED_CLAIMS_DEFAULT,
    FactorDirection,
    FactorSpec,
    validate_factor_spec,
)

factor_spec = FactorSpec(
    factor_id="momentum_20d",
    name="Momentum 20D",
    version="v1",
    direction=FactorDirection.POSITIVE,
    input_fields=("close",),
    window=20,
    params={"lookback": 20},
    preprocessing={"winsorize": [0.01, 0.99], "zscore": True},
    universe={"mode": "research_input_v1", "pit_policy": "pit_required"},
    availability_policy={"available_at": "decision_time", "policy": "no_lookahead"},
    data_lineage={
        "source_dataset": "research_input_v1",
        "research_input_schema": "research_input_v1",
        "evidence_refs": ["your-local-factor-source"],
    },
    blocked_claims=BLOCKED_CLAIMS_DEFAULT,
    failure_policy="fail_closed",
)

result = validate_factor_spec(factor_spec)
assert result.passed, result.to_dict()
```

如果你从旧实验因子迁移，可以先看 `map_legacy_factor_definition()`，但输出仍必须是项目内部 `FactorSpec`，不能把 Qlib / Alphalens / Zipline / LEAN 对象当 truth。

## 5. 创建一次研究运行

`FactorRunSpec` 固定本次研究的日期、数据版本、标签窗口、成本、随机种子和输出根目录。`config_hash` 必须由配置生成，不能手写随意值。

```python
from engine.multifactor_contracts import (
    FactorRunSpec,
    PermissionCounters,
    build_factor_run_hash_payload,
    compute_config_hash,
    validate_factor_run_spec,
)

run_payload = {
    "run_id": "run-my-factor-001",
    "factor_id": factor_spec.factor_id,
    "factor_version": factor_spec.version,
    "date_range": {"start": "2021-01-01", "end": "2024-12-31"},
    "dataset_release": "research_input_v1_local_release",
    "benchmark": {"benchmark_id": "hs300", "policy": "hs300_required"},
    "label_window": {"horizon": 20, "return_kind": "forward_return", "adjustment_policy": "qfq"},
    "cost_config": {"cost_policy": "research_cost_v1", "commission_bps": 3, "slippage_bps": 5},
    "seed": 42,
    "code_version": "local-research-v1",
    "config_hash": "",
    "output_root": "reports/factor_research/run-my-factor-001",
    "permission_counters": PermissionCounters(),
    "failure_policy": "fail_closed",
    "strategy_id": "strategy-my-factor-001",
    "experiment_group": "cr030-local-factor-research",
    "combination_config": {"weighting_policy": "single_factor"},
}
run_payload["config_hash"] = compute_config_hash(
    build_factor_run_hash_payload(run_payload, factor_spec)
)
run_spec = FactorRunSpec(**run_payload)

result = validate_factor_run_spec(run_spec, factor_spec)
assert result.passed, result.to_dict()
```

## 6. 准备本地离线 panel 和 label

把你的本地因子结果转换成 `FactorPanelContract` 行，把未来收益标签转换成 `LabelWindowSpec` 行。关键要求：

| 要求 | 说明 |
|---|---|
| `available_at <= decision_time` | 因子值必须在决策时间前可用 |
| `label_window_start > decision_time` | 标签窗口不能和决策时间重叠 |
| `label_available_at` 晚于标签窗口结束 | 防止提前看到未来收益 |
| `data_lineage.evidence_refs` 不为空 | 每个 panel / label 都要能追溯来源 |
| `quality_status=pass` | 质量失败不得进入后续评价 |

最小示例：

```python
from engine.factor_panel_contracts import (
    FactorPanelContract,
    LabelWindowSpec,
    combine_panel_label_gate,
    validate_factor_panel,
    validate_label_window,
)

lineage = {
    "source_dataset": "research_input_v1_local_release",
    "research_input_schema": "research_input_v1",
    "evidence_refs": ["local-offline-factor-panel"],
}

panel_rows = [
    FactorPanelContract(
        trade_date="2024-01-02",
        symbol="000001.SZ",
        factor_id=factor_spec.factor_id,
        factor_version=factor_spec.version,
        raw_value=0.10,
        directional_value=0.10,
        winsorized_value=0.10,
        zscore_value=0.10,
        available_at="2024-01-02T08:30:00",
        decision_time="2024-01-02T09:30:00",
        source_dataset="research_input_v1_local_release",
        quality_status="pass",
        preprocessing_metadata={"adjustment_policy": "qfq", "winsorize": [0.01, 0.99], "zscore": True},
        data_lineage=lineage,
    )
]

label_rows = [
    {
        **LabelWindowSpec(
            label_id="forward_return_20d",
            trade_date="2024-01-02",
            symbol="000001.SZ",
            decision_time="2024-01-02T09:30:00",
            label_window_start="2024-01-03T09:30:00",
            label_window_end="2024-01-31T15:00:00",
            label_available_at="2024-01-31T16:00:00",
            return_kind="forward_return",
            adjustment_policy="qfq",
            cost_policy="research_cost_v1",
            benchmark_policy="hs300_required",
            data_lineage=lineage,
        ).to_dict(),
        "forward_return": 0.025,
    }
]

panel_result = validate_factor_panel(panel_rows[0], run_spec)
label_result = validate_label_window(label_rows[0], run_spec)
gate = combine_panel_label_gate(panel_result, label_result)
assert gate.passed, gate.to_dict()
```

## 7. 生成单因子评价报告

评价报告输出 IC、RankIC、ICIR、分层收益、long-short、turnover、成本敏感性和 exposure 摘要。缺成本或 exposure 时可以是 `research_limited`，但不得产生生产 / QMT / simulation ready 声明。

```python
from engine.factor_evaluation import build_factor_evaluation_report

report = build_factor_evaluation_report(
    panel_rows,
    label_rows,
    benchmark={"benchmark_id": "hs300", "policy": "hs300_required"},
    cost={"cost_policy": "research_cost_v1", "commission_bps": 3, "slippage_bps": 5},
    exposure=[
        {"symbol": "000001.SZ", "industry": "bank", "market_cap": 100.0, "style_beta": 0.8},
    ],
    evaluation_config={
        "run_id": run_spec.run_id,
        "factor_id": factor_spec.factor_id,
        "factor_version": factor_spec.version,
        "dataset_release": run_spec.dataset_release,
        "label_window": run_spec.label_window,
        "evaluation_window": run_spec.date_range,
        "rolling_window": 20,
        "quantiles": 5,
        "gate_result": gate,
        "permission_counters": PermissionCounters(),
        "evidence_refs": ["local-offline-factor-evaluation"],
    },
)

print(report.status)
print(report.IC)
print(report.RankIC)
```

## 8. 多因子组合

准备多个 `FactorEvaluationReport` 后，用 `rule_weight` 或 `linear_score` 合成组合。P0 默认不启用 optimizer / ML。

```python
from engine.multifactor_combiner import MultiFactorCombiner, build_multifactor_portfolio_plan

combiner = MultiFactorCombiner(
    combiner_id="combo-my-factor-001",
    factor_inputs=(),
    normalization={"method": "zscore", "scope": "cross_section"},
    winsorization={"method": "quantile", "limits": [0.01, 0.99]},
    neutralization={"method": "disabled", "reason": "P0 start"},
    orthogonalization={"method": "disabled", "reason": "P0 start"},
    weighting_policy={"policy": "rule_weight", "weights": {factor_spec.factor_id: 1.0}},
    missing_policy={"missing_report": "exclude_with_reason", "critical_constraint": "fail_closed"},
    constraints={
        "max_factor_weight": 1.0,
        "target_count": 20,
        "benchmark_deviation_cap": 0.1,
        "capacity": {"max_daily_participation": 0.05},
        "exposure": {"style_beta": "observed"},
        "rebalance_dates": ["2024-01-31"],
    },
    rebalance_frequency="monthly",
    turnover_cap=0.35,
    cost_config=run_spec.cost_config,
    benchmark=run_spec.benchmark,
    freeze_policy={"version": "freeze-my-factor-001", "change_policy": "cp_or_cr_required"},
    capacity={"max_daily_participation": 0.05},
    optimizer_policy={"enabled": False},
    permission_counters=PermissionCounters(),
)

portfolio_plan = build_multifactor_portfolio_plan([report], combiner)
print(portfolio_plan.status)
print(portfolio_plan.target_weights)
print(portfolio_plan.draft_handoff)
```

## 9. 形成 manifest / catalog

manifest 和 catalog 是策略侧模拟盘入口的审查证据。它们不是 publish current pointer，也不是 production truth。

```python
from engine.research_manifest import (
    assert_manifest_ready_for_admission,
    build_experiment_manifest,
    build_research_report_catalog_entry,
    validate_experiment_manifest,
)

report_ref = report.to_dict()
report_ref["artifact_paths"] = {
    "json": "reports/factor_evaluation/v1/run-my-factor-001/report.json",
    "csv": "reports/factor_evaluation/v1/run-my-factor-001/metrics.csv",
    "markdown": "reports/factor_evaluation/v1/run-my-factor-001/report.md",
}

manifest = build_experiment_manifest(
    run_spec,
    [report_ref],
    portfolio_plan,
    metadata={
        "report_id": report.report_id,
        "evidence_refs": ["local-offline-research-run"],
        "limitations": ["catalog 是研究报告索引，不是 current pointer。"],
        "permission_counters": PermissionCounters().to_dict(),
    },
)
catalog_entry = build_research_report_catalog_entry(manifest)

assert validate_experiment_manifest(manifest).passed
assert assert_manifest_ready_for_admission(manifest, catalog_entry).passed
```

## 10. 形成策略侧模拟盘入口包

最后生成 `StrategyAdmissionPackage`。在 QMT CR 未通过前，它应当因为 `MF_ADMISSION_QMT_CR_NOT_AUTHORIZED` 保持 blocked；这不是失败，而是当前安全边界。

```python
from engine.strategy_admission_package import (
    build_strategy_admission_package,
    zero_not_authorized_counters,
)

stage6_gate = {
    "admission_status": "pass",
    "stage_gate_ref": "local-stage6-review",
    "gate_matrix": [
        {"gate_id": "data_quality", "status": "pass", "evidence_ref": "local-data-quality"},
        {"gate_id": "factor_quality", "status": "pass", "evidence_ref": report.report_id},
    ],
    "blocked_claims": [],
    "missing_evidence": [],
    "evidence_refs": ["local-stage6-review"],
}

order_intent_draft_ref = {
    "schema_version": "order_intent_draft_v1",
    "draft_id": "draft-my-factor-001",
    "path_or_ref": "local-draft-only://draft-my-factor-001",
    "limitations": ["draft only", "not authorization", "later gated"],
    "operation_counters": zero_not_authorized_counters().to_dict(),
}

package = build_strategy_admission_package(
    portfolio_plan,
    manifest,
    catalog_entry,
    stage6_gate,
    order_intent_draft_ref,
)

print(package.admission_status)
print([reason.code for reason in package.blocked_reasons])
print(package.pre_sim_strategy_preparation)
```

期望看到：

- `pre_sim_strategy_preparation.status == evidence_package_complete_for_follow_up_review`
- `MF_ADMISSION_QMT_CR_NOT_AUTHORIZED` 出现在 blocked reasons
- `not_qmt_authorization == True`
- `not_simulation_authorization == True`
- `not_live_authorization == True`

这表示策略侧模拟盘入口证据包已形成，但真实模拟盘运行仍未授权。

## 11. 每次研究结束后的最小自检

```bash
uv run --python 3.11 pytest -q tests/test_cr030_factor_spec_run_spec_contract.py tests/test_cr030_factor_panel_label_window_gates.py tests/test_cr030_factor_evaluation_report.py tests/test_cr030_multifactor_combiner.py tests/test_cr030_experiment_manifest_catalog.py tests/test_cr030_strategy_admission_package.py tests/test_cr030_no_real_operation_safety.py
```

如果你写了新的研究脚本，建议同时检查：

- `PermissionCounters()` 全部保持 0。
- 报告和 catalog 只写新版本目录，不覆盖旧报告。
- `allowed_claims` 不包含 `qmt_ready`、`simulation_ready`、`live_ready`、`production_truth`。
- `StrategyAdmissionPackage` 可作为策略侧模拟盘入口审查输入，但不能作为真实交易通过证明。

## 12. 常见下一步

| 目标 | 下一步 |
|---|---|
| 新增一个普通技术因子 | 定义 `FactorSpec`，生成 panel / label，跑 S03 / S04 gate。 |
| 比较多个因子 | 生成多个 `FactorEvaluationReport`，再用 `build_multifactor_portfolio_plan()` 合成组合。 |
| 做复杂权重优化 | 另起 optimizer Spike；当前 P0 不启用 optimizer / cvxpy / ML。 |
| 接 Qlib runner | 另起 CR-026；当前只允许 reference，不运行 Qlib。 |
| 接 QMT 模拟盘 | 先完成 CR-020 gateway health，再完成 CR-021 simulation 准入。 |
