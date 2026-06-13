---
cr_id: CR-038
title: 第7章因子投资实践、风险模型与组合优化
status: closed-user-approved
created_at: 2026-06-10
created_by: codex
owner: meta-po
source: user
change_type: add
impact_level: high
workflow_mode_after_change: standard
activation_policy: "activated by user request on 2026-06-10 after CR-035/036/037 closure and CR-020 no-overlap conflict precheck"
parent_cr: CR-034
source_decision_id: USER-20260610-BOOK-RESEARCH-PLAN
related_changes:
  - CR-030
  - CR-034
  - CR-035
  - CR-036
  - CR-037
---

# CR-038 第7章因子投资实践、风险模型与组合优化

## 背景与上下文

第7章把因子研究推进到投资实践，覆盖收益率模型、风险模型、投资组合优化、Smart Beta、因子择时、风格分析、风险归因和展望。它依赖前置研究：

- CR-034：第三章七因子数据与复刻已关闭。
- CR-035：第4章模型定价检验和模型 baseline。
- CR-036：第5章异象复刻和 alpha feature 候选；其代理定义缺口由 CR-037 复验结果约束消费。
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
| 容量分析 | `reports/chapter7_factor_practice/<run_id>/capacity_liquidity_analysis.csv` | 流动性 / 小盘暴露 / 单票成交额 proxy / 容量敏感性 |
| 人读报告 | `process/research/chapter7_factor_practice/<run_id>/CHAPTER7-RUN-REPORT.md` | 第7章实践报告 |
| 组合准入摘要 | `process/research/chapter7_factor_practice/<run_id>/PORTFOLIO-ADMISSION-SUMMARY.json` | 给 CR-039 消费 |

## CR-037 交接门禁

| 门禁 | 规则 | 失败行为 |
|---|---|---|
| 稳健性准入消费 | 默认只允许消费 CR-037 `ROBUSTNESS-ADMISSION-SUMMARY.json` 中 `baseline` / `candidate` 的因子或异象。 | 未命中则不得进入 alpha score 或 optimizer 输入。 |
| `watch` 项处理 | `watch` 只能进入观察组合、降权组合或场景化组合；必须在报告中写明风险、约束、权重上限和不进入 CR-039 `simulation_candidate` 的默认边界。 | 未写风险接受和组合约束时 fail-closed。 |
| `reject` 项处理 | CR-037 `reject`、`needs-more-data`、`blocked_missing_evidence` 默认不得进入 alpha score、组合优化器输入、组合准入摘要或 CR-039 候选策略。 | 如需例外，必须另起 CR 或在本 CR 中形成显式人工风险接受决策。 |
| CR-036 异象代理缺口 | 使用第5章异象时必须同时读取 CR-036 gap register 和 CR-037 对应异象准入；CR-037 已判为 `reject` 的异象不得直接消费。 | 缺少 gap / robustness 追溯时 fail-closed。 |
| 成本敏感性 | 必须报告 gross return、net return、单期换手、年化换手、成本后收益衰减，并至少测试多档成本假设。 | 只有零成本结果时不得输出可给 CR-039 消费的 portfolio admission。 |
| 容量 / 流动性敏感性 | 必须报告低流动性 / 小盘暴露或等价容量 proxy，包括单票权重、组合持仓数、目标成交额 proxy、低流动性暴露和容量衰减情景。 | 缺少容量证据时，组合最多为研究观察项，不得进入 CR-039 `simulation_candidate`。 |
| ML 边界 | CR-038 默认不训练 ML；若使用 ML alpha，必须另起 CR 或继承 CR-037 leakage guardrail，明确 purge / embargo、解释性和调参边界。 | 未满足时不得把 ML 结果纳入组合。 |

## 组合研究边界

| 事项 | 规则 |
|---|---|
| 决策时间 | 遵循项目 D11：开盘前决策只能使用前一交易日已形成数据 |
| 调仓频率 | 默认月度，与第三章 / 第4章研究对齐；其他频率需参数化并单独报告 |
| 成本 | 必须报告成本敏感性；默认不把零成本结果作为最终准入 |
| 容量 | 必须报告容量 / 流动性敏感性；没有容量证据时不得输出可进入 simulation 准入链路的组合结论 |
| 风险约束 | 至少报告因子暴露；是否做行业 / 市值中性化需在报告中明确 |
| 大文件 | 大型 parquet 作为本地 artifact，不默认提交 |

## 验收标准

- [ ] alpha score 可追溯到 CR-035/037 已准入因子，默认只消费 CR-037 `baseline` / `candidate`。
- [ ] 至少实现一个 baseline 组合和一个约束优化组合。
- [ ] 组合报告包含收益、回撤、换手、成本、容量 / 流动性、风险暴露和归因。
- [ ] `watch` 项若被使用，必须有显式风险接受、降权 / 权重上限和不进入默认 `simulation_candidate` 的说明；`reject` 项不得进入组合输入。
- [ ] 报告区分研究组合、候选策略和真实交易准入。
- [ ] operation counts 中 QMT、simulation、live、broker lake、provider fetch、publish 均为 0。
- [ ] 峰值内存低于 16GB。
- [ ] 输出 CR-039 可消费的 portfolio admission summary。

## 激活条件

本 CR 已于 2026-06-10 按用户要求启动为 `active-story-execution`，并在同日完成实现与验证，当前状态为 `verified-pending-user-close`。

- 冲突预检：CR-020 仍处于 `active-manual-validation-pending`，但其影响面限定在 Windows/QMT 只读网关、凭据输入、REST client、HMAC、allowlist、query_positions 和 QMT runbook；CR-038 影响面限定在本地离线第7章组合研究 engine / runner / reports / process research 产物。两者文件 owner、运行授权、外部接口、权限边界和数据写入边界无重叠。
- 并行边界：CR-038 不授权 QMT、simulation、live、账户 / 订单、provider fetch、lake write、catalog publish、dependency change、凭据读取或外部项目运行。
- 前置证据：CR-035、CR-036、CR-037 均已 `closed-user-approved`；CR-038 默认只消费 CR-037 `baseline` / `candidate`，`watch` 必须降权并写风险接受边界，`reject` / `needs-more-data` / `blocked_missing_evidence` fail-closed。

## 实施与验证结果

| 项目 | 结果 | 证据 |
|---|---|---|
| 实现 | PASS | `engine/chapter7_factor_practice.py`, `scripts/run_chapter7_factor_practice.py`, `tests/test_chapter7_factor_practice.py` |
| CP6 | PASS | `process/checks/CP6-CR038-CHAPTER7-FACTOR-PRACTICE-CODING-DONE.md` |
| CP7 | PASS | `process/checks/CP7-CR038-CHAPTER7-FACTOR-PRACTICE-VERIFICATION-DONE.md` |
| QA 复核 | PASS | `process/handoffs/META-QA-CR038-CP7-2026-06-10.md` |
| 实际 runner | PASS | `run-cr038-chapter7-factor-practice-20260610` |
| 组合报告 | PASS | `process/research/chapter7_factor_practice/run-cr038-chapter7-factor-practice-20260610/CHAPTER7-RUN-REPORT.md` |
| CR039 输入 | PASS | `process/research/chapter7_factor_practice/run-cr038-chapter7-factor-practice-20260610/PORTFOLIO-ADMISSION-SUMMARY.json` |

所有 forbidden operation counters 为 0；`simulation_candidate=false`；本 CR 不构成 QMT-ready、simulation-ready、live-ready 或 production-valid。

## 关闭记录

| 项目 | 结论 |
|---|---|
| 关闭时间 | 2026-06-10 |
| 关闭方式 | 用户在对话中明确要求“关闭CR038” |
| 最终状态 | `closed-user-approved` |
| 关闭依据 | CP6 PASS、CP7 PASS、实际 runner PASS、QA 复核 PASS |
| 主要证据 | `process/checks/CP6-CR038-CHAPTER7-FACTOR-PRACTICE-CODING-DONE.md`; `process/checks/CP7-CR038-CHAPTER7-FACTOR-PRACTICE-VERIFICATION-DONE.md`; `process/research/chapter7_factor_practice/run-cr038-chapter7-factor-practice-20260610/PORTFOLIO-ADMISSION-SUMMARY.json` |
| 后续消费 | CR-039 只能只读消费组合准入摘要和本地研究 artifact |
| 不授权边界 | 不授权 QMT、simulation、live、provider fetch、lake write、catalog publish、账户、订单、凭据读取或依赖变更 |
