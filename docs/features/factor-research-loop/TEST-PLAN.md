---
status: "draft-current-index"
version: "1.0"
feature_id: "FEAT-03"
---

# Feature Test Plan: factor-research-loop

## 测试矩阵

| 测试域 | 关键场景 | 验证入口 |
|---|---|---|
| 外部参考边界 | 外部项目仅静态参考，不运行、不迁移源码 | `tests/test_cr030_external_reference_guardrails.py` |
| FactorSpec / RunSpec | schema、错误码、failure policy 完整 | `tests/test_cr030_factor_spec_run_spec_contract.py` |
| FactorPanel / LabelWindow | 四层值、coverage、label window fail-closed | `tests/test_cr030_factor_panel_label_window_gates.py` |
| 因子评价报告 | IC、RankIC、分层收益、成本敏感性、blocked claims | `tests/test_cr030_factor_evaluation_report.py` |
| 多因子组合 | 权重、约束、benchmark、成本、冻结策略 | `tests/test_cr030_multifactor_combiner.py` |
| Manifest / Catalog | config hash、dataset release、report path、复跑证据 | `tests/test_cr030_experiment_manifest_catalog.py` |
| StrategyAdmissionPackage | 不等同交易授权，no-real-op 计数保持 0 | `tests/test_cr030_strategy_admission_package.py`、`tests/test_cr030_no_real_operation_safety.py` |

## 手工验证

| 场景 | 预期 |
|---|---|
| 研究报告用于 QMT 后续评审 | 只能提供 evidence / blocked reason / order_intent_draft_ref，不触发 QMT |
| 外部项目分析更新 | 必须记录 reference / optional Spike / exclude / forbidden migration 分类 |

