---
cr_id: CR-035
title: 第4章多因子模型复刻与 A 股定价检验
status: draft-not-active
created_at: 2026-06-10
created_by: codex
owner: meta-po
source: user
change_type: add
impact_level: high
workflow_mode_after_change: standard
activation_policy: "draft only; must pass CR conflict precheck before becoming active because CR-020 is currently active-manual-validation-pending"
parent_cr: CR-034
source_decision_id: USER-20260610-BOOK-RESEARCH-PLAN
related_changes:
  - CR-030
  - CR-034
---

# CR-035 第4章多因子模型复刻与 A 股定价检验

## 背景与上下文

《因子投资：方法与实践》第4章在第3章七个主流因子基础上，研究主流多因子模型和 A 股中哪些因子被定价。第3章已经由 CR-034 关闭，形成可用于后续研究的七因子面板：

| 输入 | 状态 | 路径 |
|---|---|---|
| 2000-2019 第三章七因子面板 | PASS；2,550,289 行；239 期调仓；峰值 RSS 3.49GB | `reports/chapter3_factor_panel/run-chapter3-empirical-2000-2019-financial-fallback-20260610/factor_panel.parquet` |
| 2020-2026 YTD 第三章七因子面板 | PASS；1,957,024 行；76 期调仓；峰值 RSS 5.67GB | `reports/chapter3_factor_panel/run-chapter3-empirical-2020-2026-ytd-financial-fallback-20260610/factor_panel.parquet` |
| 第三章因子口径 | 七因子已复刻：市场、规模、价值、动量、盈利、投资、异常换手率 | `process/research/chapter3_factor_replication/README.md` |
| 多因子研究合同 | FactorSpec、FactorRunSpec、FactorPanelContract、LabelWindowSpec、FactorEvaluationReport、StrategyAdmissionPackage 已由 CR-030 建立 | `docs/CR030-MULTIFACTOR-RESEARCH-LOOP.md` |

本 CR 是第三章研究的直接下游，目标是把“单因子复刻和基础评价”推进到“多因子模型定价检验与模型比较”。它不进入组合优化和交易准入，后者由 CR-038 / CR-039 或后续 QMT CR 单独处理。

## 目标

1. 复刻第4章“主流多因子模型综述”的项目内模型定义和因子组合输入。
2. 基于第三章七因子面板，执行第4章 `4.2 A股中被定价的因子` 的 Fama-MacBeth 回归检验。
3. 输出每个因子的横截面风险溢价、t 值、样本数、窗口、稳定性和方向解释。
4. 复刻第4章 `4.3 多因子模型比较` 的项目内可执行版本，包括模型收益、相关性、α 检验、GRS 或等价比较。
5. 落地第4章 `4.4 多因子模型的简约性`，给出进入后续策略研究的基线模型建议。
6. 形成第7章组合实践前的“模型准入摘要”：哪些因子进入 baseline、哪些只观察、哪些需要在第6章稳健性中重点复验。

## Non-Goals

- 不新增第5章异象变量。
- 不做第7章组合优化、Smart Beta、因子择时或风险归因。
- 不接入 QMT、simulation、live、账户、订单或 broker lake。
- 不触发 provider fetch、lake write、catalog current pointer publish。
- 不把任何模型声明为 production-valid、QMT-ready、simulation-ready 或 live-ready。
- 不把外部论文模型未验证地作为项目 current truth。

## 影响范围

| 维度 | 影响 | 处理 |
|---|---|---|
| 需求层 | 新增第4章模型复刻、Fama-MacBeth、模型比较和简约性结论 | 建立 CR-035 研究需求，不修改 CR-034 历史基线 |
| 场景层 | 增加多因子模型检验、样本内 / 样本外切分、模型冗余分析 | 新增 chapter4 研究场景和报告 |
| 计划层 | 依赖 CR-034 因子面板；为 CR-036/037/038 提供模型解释输入 | CR-035 完成前不启动依赖第4章模型结果的异象解释和组合优化 |
| 安全层 | 只读本地 parquet / manifest / 报告 | 禁止 provider、lake write、publish、QMT、simulation、live |
| 交付层 | 新增 reports/chapter4_factor_models 和 process/research/chapter4_factor_models | 小型报告可提交，大型 parquet 默认不提交 |

## 输入合同

| 输入 | 必需字段 | 失败行为 |
|---|---|---|
| 第三章 factor panel | `trade_date`、`symbol`、`factor_id`、`zscore_value`、`available_at`、`run_id`、`data_lineage` | 缺 P0 字段 fail-closed |
| 标签 / forward returns | `trade_date`、`symbol`、`forward_return`、`label_available_at` | 标签窗口与因子 available_at 重叠或前视时 fail-closed |
| 因子定义 | `engine.factor_library` canonical factor definitions | 因子 ID 未注册或方向不明时 fail-closed |
| 第三章报告 | 两段 empirical report | report status 非 PASS 或 limitations 非空时阻断模型准入 |

## 输出规划

| 输出 | 路径 | 说明 |
|---|---|---|
| 因子收益 / Fama-MacBeth 结果 | `reports/chapter4_factor_models/<run_id>/fama_macbeth_results.csv` | 因子溢价、t 值、样本数、窗口 |
| 模型收益 | `reports/chapter4_factor_models/<run_id>/factor_model_returns.parquet` | 各模型月度收益和因子组合 |
| 模型比较 | `reports/chapter4_factor_models/<run_id>/model_comparison.csv` | α、GRS 或等价统计、相关性和冗余性 |
| 因子相关性 | `reports/chapter4_factor_models/<run_id>/factor_correlation.csv` | 七因子相关结构 |
| manifest | `reports/chapter4_factor_models/<run_id>/factor_model_manifest.json` | 输入 run、参数、窗口、资源和限制 |
| 运行报告 | `process/research/chapter4_factor_models/<run_id>/CHAPTER4-RUN-REPORT.md` | 人读报告 |
| 机器报告 | `process/research/chapter4_factor_models/<run_id>/CHAPTER4-RUN-REPORT.json` | 机器可读 |
| 模型准入摘要 | `process/research/chapter4_factor_models/<run_id>/MODEL-ADMISSION-SUMMARY.json` | 给 CR-038/039 消费 |

## 资源与运行边界

- 默认串行运行，不并发跑重型任务。
- 默认 `OMP_NUM_THREADS=1`、`OPENBLAS_NUM_THREADS=1`、`MKL_NUM_THREADS=1`、`NUMEXPR_NUM_THREADS=1`。
- 默认使用 chunked / 按窗口处理，单次运行 `--max-memory-gb 16`。
- 大型 parquet 只作为本地研究 artifact，不默认提交 Git。

## 验收标准

- [ ] Fama-MacBeth 回归覆盖七个第三章因子，并输出 t 值和样本数。
- [ ] 模型比较至少覆盖书中第4章涉及的主流模型和 A 股示例模型的项目内可执行版本。
- [ ] 报告区分样本内、验证期和 2020-2026 YTD 观察期。
- [ ] 输出模型准入结论：baseline / watch / reject / needs-robustness-review。
- [ ] operation counts 中 provider fetch、lake write、publish、QMT、simulation、live 均为 0。
- [ ] 峰值内存低于 16GB。
- [ ] 报告不声明 production-valid、QMT-ready、simulation-ready 或 live-ready。

## 激活条件

本 CR 当前为 `draft-not-active`。正式启动前必须完成：

1. CR 冲突预检，确认不会影响 CR-020 QMT gateway 当前活跃验证。
2. 用户确认启动 CR-035。
3. 若需要修改正式文档或新增 runner，进入 standard 流程并生成 Story / LLD / CP5 证据。
