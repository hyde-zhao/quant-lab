---
cr_id: CR-038
title: 第7章因子投资实践、风险模型与组合优化
status: draft-not-active
created_at: 2026-06-10
created_by: codex
owner: meta-po
source: user
change_type: add
impact_level: high
workflow_mode_after_change: standard
activation_policy: "draft only; activate after CR-035/037 provide model and robustness admission inputs"
parent_cr: CR-034
source_decision_id: USER-20260610-BOOK-RESEARCH-PLAN
related_changes:
  - CR-030
  - CR-034
  - CR-035
  - CR-037
---

# CR-038 第7章因子投资实践、风险模型与组合优化

## 背景与上下文

第7章把因子研究推进到投资实践，覆盖收益率模型、风险模型、投资组合优化、Smart Beta、因子择时、风格分析、风险归因和展望。它依赖前置研究：

- CR-034：第三章七因子数据与复刻已关闭。
- CR-035：第4章模型定价检验和模型 baseline。
- CR-037：第6章稳健性和研究 guardrails。

CR-038 的目标是研究级组合实践，不等于 QMT、simulation 或 live 准入。任何真实交易、账户查询、broker lake 写入或 QMT 运行都必须走 CR-020/021/022/023/024 等交易准入链路。

## 目标

1. 基于已准入因子构建收益率模型 / alpha score。
2. 建立研究级风险暴露视图：市场、规模、价值、动量、盈利、投资、换手率，以及必要的行业 / 市值暴露。
3. 实现组合优化研究：等权多因子、IC 加权、风险调整、约束优化、换手控制和成本敏感性。
4. 复刻第7章 Smart Beta、因子择时、风格分析和风险归因的项目内可执行研究版本。
5. 输出组合研究报告和进入 CR-039 策略候选准入的候选组合。

## Non-Goals

- 不发单、不撤单、不连接 QMT。
- 不声明 simulation-ready、live-ready 或 production-valid。
- 不写 broker lake。
- 不做真实账户读取。
- 不把第7章组合研究结果直接作为实盘策略。
- 不绕过 CR-037 稳健性 guardrails。

## 影响范围

| 维度 | 影响 | 处理 |
|---|---|---|
| 需求层 | 新增收益模型、风险模型、组合优化和归因研究 | 作为研究级 CR，不进入交易准入 |
| 场景层 | 增加 portfolio construction、constraint、turnover、cost、attribution 场景 | 所有结果仅限研究 |
| 计划层 | 依赖 CR-035/037 | 前置未完成时只能做设计或 smoke |
| 安全层 | 不触发 QMT / simulation / live | operation counts 必须为 0 |
| 交付层 | 新增组合 artifact、报告、准入摘要 | 大型 parquet 不默认提交 |

## 输出规划

| 输出 | 路径 | 说明 |
|---|---|---|
| alpha score | `reports/chapter7_factor_practice/<run_id>/alpha_scores.parquet` | 股票-日期-分数 |
| 组合权重 | `reports/chapter7_factor_practice/<run_id>/optimized_portfolios.parquet` | 研究级目标权重 |
| 组合指标 | `reports/chapter7_factor_practice/<run_id>/portfolio_metrics.csv` | 收益、回撤、夏普、换手、成本 |
| 风险暴露 | `reports/chapter7_factor_practice/<run_id>/risk_exposure.csv` | 因子和行业 / 市值暴露 |
| 归因结果 | `reports/chapter7_factor_practice/<run_id>/performance_attribution.csv` | 因子贡献、选股、风格 |
| 成本分析 | `reports/chapter7_factor_practice/<run_id>/turnover_cost_analysis.csv` | 成本敏感性 |
| 人读报告 | `process/research/chapter7_factor_practice/<run_id>/CHAPTER7-RUN-REPORT.md` | 第7章实践报告 |
| 组合准入摘要 | `process/research/chapter7_factor_practice/<run_id>/PORTFOLIO-ADMISSION-SUMMARY.json` | 给 CR-039 消费 |

## 组合研究边界

| 事项 | 规则 |
|---|---|
| 决策时间 | 遵循项目 D11：开盘前决策只能使用前一交易日已形成数据 |
| 调仓频率 | 默认月度，与第三章 / 第4章研究对齐；其他频率需参数化并单独报告 |
| 成本 | 必须报告成本敏感性；默认不把零成本结果作为最终准入 |
| 风险约束 | 至少报告因子暴露；是否做行业 / 市值中性化需在报告中明确 |
| 大文件 | 大型 parquet 作为本地 artifact，不默认提交 |

## 验收标准

- [ ] alpha score 可追溯到 CR-035/037 已准入因子。
- [ ] 至少实现一个 baseline 组合和一个约束优化组合。
- [ ] 组合报告包含收益、回撤、换手、成本、风险暴露和归因。
- [ ] 报告区分研究组合、候选策略和真实交易准入。
- [ ] operation counts 中 QMT、simulation、live、broker lake、provider fetch、publish 均为 0。
- [ ] 峰值内存低于 16GB。
- [ ] 输出 CR-039 可消费的 portfolio admission summary。

## 激活条件

本 CR 当前为 `draft-not-active`。推荐在 CR-035 和 CR-037 完成后启动；如果用户只想先做第7章设计，可先创建设计 Story，不执行全量组合优化。
