---
cr_id: CR-036
title: 第5章异象复刻与异象研究数据集
status: draft-not-active
created_at: 2026-06-10
created_by: codex
owner: meta-po
source: user
change_type: add
impact_level: high
workflow_mode_after_change: standard
activation_policy: "draft only; activate after CR-035 model baseline is available or user explicitly waives that dependency"
parent_cr: CR-034
source_decision_id: USER-20260610-BOOK-RESEARCH-PLAN
related_changes:
  - CR-030
  - CR-034
  - CR-035
---

# CR-036 第5章异象复刻与异象研究数据集

## 背景与上下文

第5章在第3章因子和第4章多因子模型基础上研究 A 股异象。书中第5章包括：

| 章节 | 主题 | 项目内定位 |
|---|---|---|
| 5.1 | 估值高低中的异象 | 异象变量，不等同于第三章 `value_bm` 因子 |
| 5.2 | 基本面锚定反转 | 复合变量 / 反转异象，需要额外基本面锚定字段 |
| 5.3 | 特质性波动率 | 异象变量，需要模型残差或特质波动率估计 |

CR-034 已关闭并提供第三章七因子面板。CR-035 将提供第4章模型解释输入。CR-036 不应把第5章异象混入第三章七因子基线，而应形成独立的 anomaly panel、排序检验、α 检验和准入结论。

## 目标

1. 精读第5章，冻结三类异象的变量定义、数据需求、排序口径和检验口径。
2. 建立第5章异象数据集，不污染第三章七因子 canonical factor set。
3. 复刻估值高低异象、基本面锚定反转、特质性波动率异象。
4. 使用第4章模型结果解释异象收益，输出 α 检验和模型解释能力。
5. 判断异象是否可作为后续 alpha feature、观察项或拒绝项。
6. 形成第6章稳健性复验和第7章组合实践的候选输入。

## Non-Goals

- 不把第5章异象改名为第三章因子。
- 不改写 CR-034 第三章七因子面板。
- 不做组合优化、Smart Beta 或实盘交易。
- 不触发 provider fetch、lake write、catalog publish、QMT、simulation 或 live。
- 不把异象显著性直接等同于可交易策略有效。

## 影响范围

| 维度 | 影响 | 处理 |
|---|---|---|
| 需求层 | 新增三类异象复刻和模型 α 检验需求 | 独立于第三章因子复刻 |
| 场景层 | 新增异象排序、长短组合、模型解释和样本外稳定性场景 | CR-037 继续做稳健性 |
| 计划层 | 依赖 CR-035 模型定义和因子收益 | 默认 CR-035 完成后启动 |
| 安全层 | 只读本地研究输入 | 禁止真实 provider / lake write / publish / 交易 |
| 交付层 | 新增 anomaly panel、anomaly return、alpha test 和报告 | 大型 parquet 不默认提交 |

## 输入合同

| 输入 | 来源 | 说明 |
|---|---|---|
| 第三章七因子面板 | CR-034 | 用于控制变量、模型解释和对照 |
| 第4章模型结果 | CR-035 | 用于 α 检验和模型解释 |
| 财务 PIT 字段 | local lake / CR-034 readiness | book equity、ROE、ROA、total assets 等 |
| 日收益 / 市场收益 | CR-034 后复权收益 | 特质波动率需要回归残差或模型残差 |
| 第5章变量定义 | 书籍 Markdown | 必须在报告中追溯到 5.1/5.2/5.3 |

## 输出规划

| 输出 | 路径 | 说明 |
|---|---|---|
| 异象面板 | `reports/chapter5_anomalies/<run_id>/anomaly_panel.parquet` | anomaly_id、raw/directional/winsorized/zscore |
| 异象收益 | `reports/chapter5_anomalies/<run_id>/anomaly_returns.csv` | 分组收益、多空收益 |
| α 检验 | `reports/chapter5_anomalies/<run_id>/alpha_tests.csv` | 相对第4章模型的 alpha / t 值 |
| 异象 manifest | `reports/chapter5_anomalies/<run_id>/anomaly_manifest.json` | 输入、口径、窗口、限制 |
| 人读报告 | `process/research/chapter5_anomalies/<run_id>/CHAPTER5-RUN-REPORT.md` | 第5章复刻报告 |
| 准入摘要 | `process/research/chapter5_anomalies/<run_id>/ANOMALY-ADMISSION-SUMMARY.json` | alpha feature / watch / reject |

## 数据缺口处理规则

- 缺少第5章变量必需字段时，先输出 gap register，不允许静默用近似字段替代。
- 需要新增真实 provider fetch 或 lake write 时，必须另起数据补齐 CR 或在本 CR 内重新发起运行授权，不得默认继承 CR-034 授权。
- 特质性波动率必须明确使用的定价模型、收益窗口和最小有效样本数。

## 验收标准

- [ ] 三类异象均有变量定义、数据字段、排序方向和书中章节来源。
- [ ] 每类异象都有单变量排序、多空收益和 Newey-West 或等价 t 值。
- [ ] 每类异象都有相对第4章模型的 α 检验。
- [ ] 报告明确区分“异象变量”和“可纳入策略的 alpha feature”。
- [ ] operation counts 中 provider fetch、lake write、publish、QMT、simulation、live 均为 0，除非用户另行授权并记录。
- [ ] 峰值内存低于 16GB。

## 激活条件

本 CR 当前为 `draft-not-active`。推荐在 CR-035 完成后启动；若用户要求并行，必须先做冲突预检并确认 CR-036 不依赖 CR-035 产物或接受临时模型解释缺口。
