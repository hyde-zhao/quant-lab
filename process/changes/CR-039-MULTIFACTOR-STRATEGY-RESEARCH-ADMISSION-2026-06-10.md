---
cr_id: CR-039
title: 多因子策略研究闭环与候选策略准入
status: draft-not-active
created_at: 2026-06-10
created_by: codex
owner: meta-po
source: user
change_type: add
impact_level: high
workflow_mode_after_change: standard
activation_policy: "draft only; activate after CR-035/036/037/038 produce sufficient research evidence"
parent_cr: CR-034
source_decision_id: USER-20260610-BOOK-RESEARCH-PLAN
related_changes:
  - CR-030
  - CR-034
  - CR-035
  - CR-036
  - CR-037
  - CR-038
---

# CR-039 多因子策略研究闭环与候选策略准入

## 背景与上下文

CR-039 是第3章到第7章研究的收敛 CR，不对应单一书章。它的目标是把已经完成的因子、模型、异象、稳健性和组合实践结果，收敛成少数可继续观察或进入后续模拟盘准入链路的候选策略。

前置研究链路：

| 前置 CR | 作用 |
|---|---|
| CR-034 | 第三章七因子数据和复刻基线 |
| CR-035 | 第4章多因子模型和定价检验 |
| CR-036 | 第5章异象复刻和 alpha feature 候选 |
| CR-037 | 第6章稳健性、样本外和研究 guardrails |
| CR-038 | 第7章组合优化、风险暴露和归因 |

CR-039 仍是研究准入，不授权真实 QMT、simulation、live 或账户 / 订单能力。若候选策略需要进入模拟盘或真实交易，必须走 CR-020/021/022/023/024 交易准入链路，并重新取得运行授权。

## 目标

1. 从前置研究中选择 1-3 个多因子策略候选。
2. 定义统一策略研究 runner 输入输出合同。
3. 输出候选策略的样本内、验证期、2020-2026 YTD 样本外表现。
4. 输出成本、换手、容量、风险暴露、归因和失效风险摘要。
5. 形成 StrategyAdmissionPackage，用于后续是否启动 simulation 准入 CR 的人工决策。

## Non-Goals

- 不直接进入 QMT simulation。
- 不连接 broker、不查询真实账户、不发单、不撤单。
- 不把候选策略声明为 live-ready。
- 不覆盖前置研究报告。
- 不省略 CR-037 稳健性和 CR-038 风险 / 成本证据。

## 输入合同

| 输入 | 来源 | 必需性 |
|---|---|---|
| 因子模型准入摘要 | CR-035 | 必需 |
| 异象准入摘要 | CR-036 | 可选，若策略使用异象则必需 |
| 稳健性准入摘要 | CR-037 | 必需 |
| 组合准入摘要 | CR-038 | 必需 |
| 第三章因子面板 | CR-034 | 必需 |
| 策略配置 | 本 CR | 必需，必须包含因子权重、调仓频率、成本、约束和样本窗口 |

## 输出规划

| 输出 | 路径 | 说明 |
|---|---|---|
| 策略分数 | `reports/multifactor_strategy_candidates/<run_id>/strategy_scores.parquet` | 股票-日期-策略分数 |
| 回测结果 | `reports/multifactor_strategy_candidates/<run_id>/backtest_results.csv` | 净值、收益、回撤、换手 |
| 因子贡献 | `reports/multifactor_strategy_candidates/<run_id>/factor_contribution.csv` | 收益贡献和暴露贡献 |
| 风险成本摘要 | `reports/multifactor_strategy_candidates/<run_id>/risk_cost_summary.csv` | 成本、容量、风险 |
| 人读报告 | `process/research/multifactor_strategy_candidates/<run_id>/STRATEGY-RESEARCH-REPORT.md` | 候选策略报告 |
| 准入包 | `process/research/multifactor_strategy_candidates/<run_id>/STRATEGY-ADMISSION-PACKAGE.json` | 后续 simulation CR 决策输入 |

## 候选策略准入分级

| 分级 | 含义 | 后续动作 |
|---|---|---|
| research_baseline | 可作为长期研究基线 | 保持研究跟踪 |
| simulation_candidate | 具备启动模拟盘准入 CR 的证据 | 另起 CR-021 或后续 simulation 准入 CR |
| watch | 有局部有效性但证据不足 | 回到 CR-037/038 补稳健性或组合约束 |
| reject | 风险 / 成本 / 稳健性不足 | 保留报告，不进入后续 |
| blocked_missing_evidence | 前置报告缺失或字段不合规 | fail-closed |

## 验收标准

- [ ] 至少输出一个候选策略的完整研究报告。
- [ ] 每个候选策略都有样本内、验证期、2020-2026 YTD 样本外表现。
- [ ] 每个候选策略都有成本敏感性、换手、容量、风险暴露和归因。
- [ ] 每个候选策略都能追溯到 CR-035/036/037/038 输入。
- [ ] 准入包明确 `allowed_claims` 和 `blocked_claims`。
- [ ] 不声明 QMT-ready、simulation-ready、live-ready，除非后续交易 CR 单独完成。
- [ ] operation counts 中 QMT、simulation、live、broker lake、provider fetch、publish 均为 0。
- [ ] 峰值内存低于 16GB。

## 激活条件

本 CR 当前为 `draft-not-active`。必须等 CR-035/037/038 至少完成基础产物后才能启动；如果策略使用第5章异象，还必须等待 CR-036 完成。启动前必须做 CR 冲突预检，确认不会和 CR-020 当前 QMT gateway 验证或后续交易准入链路混淆。
