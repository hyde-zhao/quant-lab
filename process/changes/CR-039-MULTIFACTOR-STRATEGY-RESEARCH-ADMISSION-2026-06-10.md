---
cr_id: CR-039
title: 多因子策略研究闭环与候选策略准入
status: closed-current-delivery
created_at: 2026-06-10
created_by: codex
owner: meta-po
source: user
change_type: add
impact_level: high
workflow_mode_after_change: standard
activation_policy: "activated by user request on 2026-06-10 after CR-035/036/037 closure, CR-038 closure, and CR-020 no-overlap conflict precheck"
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

## CR-037 / CR-038 准入门禁

| 门禁 | 规则 | 失败行为 |
|---|---|---|
| CR-037 分级消费 | 默认只允许消费 CR-037 `baseline` / `candidate` 的因子、模型或异象。 | 非 `baseline` / `candidate` 不得进入默认候选策略。 |
| `watch` 项例外 | 使用 CR-037 `watch` 项必须有 CR-038 组合约束证据、权重上限、风险接受说明，并在准入包中标为 `watch` 或 `research_baseline`，不得直接标为 `simulation_candidate`。 | 缺少任一证据则 fail-closed。 |
| `reject` / 缺证项 | CR-037 `reject`、`needs-more-data`、`blocked_missing_evidence` 和 CR-038 未通过组合约束的对象不得进入策略分数、候选策略或 simulation 准入包。 | 发现后策略准入结论为 `blocked_missing_evidence` 或 `reject`。 |
| 成本 / 容量证据 | `simulation_candidate` 必须同时具备 CR-038 成本敏感性、换手、容量 / 流动性、风险暴露和归因证据。 | 缺成本 / 容量证据时，最高只能标为 `research_baseline` 或 `watch`。 |
| 第5章异象代理缺口 | 使用 CR-036 异象必须追溯 CR-036 gap register 和 CR-037 复验结论；CR-037 已判 `reject` 的异象默认不得进入策略。 | 缺失追溯或使用 reject 异象时 fail-closed。 |
| ML 边界 | CR-039 默认不训练或准入 ML 模型；若使用 ML alpha，必须另起 CR 或提供 CR-037 leakage guardrail、purge / embargo、解释性和调参边界。 | 缺少边界时不得纳入策略准入包。 |
| 交易授权 | `simulation_candidate` 只表示可发起后续 simulation 准入 CR 的研究输入，不授权 QMT、simulation、live、账户、订单或 broker runtime。 | 任一运行授权声明均视为门禁失败。 |

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
- [ ] 默认只消费 CR-037 `baseline` / `candidate`；使用 `watch` 必须有 CR-038 风险约束和显式风险接受；`reject` 不得进入策略候选。
- [ ] 缺少 CR-038 成本 / 容量证据时，不得输出 `simulation_candidate`。
- [ ] 准入包明确 `allowed_claims` 和 `blocked_claims`。
- [ ] 不声明 QMT-ready、simulation-ready、live-ready，除非后续交易 CR 单独完成。
- [ ] operation counts 中 QMT、simulation、live、broker lake、provider fetch、publish 均为 0。
- [ ] 峰值内存低于 16GB。

## 激活条件

本 CR 已于 2026-06-10 按用户要求启动为 `active-story-execution`。

- 前置状态：CR-035、CR-036、CR-037、CR-038 均已 `closed-user-approved`；CR-038 输出 `PORTFOLIO-ADMISSION-SUMMARY.json`，且 `simulation_candidate=false`。
- 冲突预检：CR-020 仍处于 `active-manual-validation-pending`，影响面限定在 Windows/QMT gateway、只读 `query_positions`、HMAC、allowlist、凭据输入和运行手册；CR-039 影响面限定在本地离线策略候选研究 engine / runner / reports / process research 产物。两者文件 owner、外部接口、权限边界、数据写入、账户 / 订单和运行授权无重叠。
- 并行边界：CR-039 不授权 QMT、simulation、live、账户 / 订单、provider fetch、lake write、catalog publish、dependency change、凭据读取或外部项目运行。
- 准入边界：由于 CR-038 当前组合摘要不输出 `simulation_candidate`，CR-039 最高只能形成 `research_baseline` / `watch` / `reject` / `blocked_missing_evidence` 等研究准入结论；若未来要进入 simulation，必须另起 CR-021 或后续 simulation 准入 CR 并重新取得运行授权。

## 实施与验证结果

| 项目 | 结果 | 证据 |
|---|---|---|
| 实现 | PASS | `engine/multifactor_strategy_candidates.py`, `scripts/run_multifactor_strategy_candidates.py`, `tests/test_multifactor_strategy_candidates.py` |
| CP6 | PASS | `process/checks/CP6-CR039-MULTIFACTOR-STRATEGY-CANDIDATES-CODING-DONE.md` |
| CP7 | PASS | `process/checks/CP7-CR039-MULTIFACTOR-STRATEGY-CANDIDATES-VERIFICATION-DONE.md` |
| QA 复核 | PASS | `process/handoffs/META-QA-CR039-CP7-2026-06-10.md` |
| 实际 runner | PASS | `run-cr039-multifactor-strategy-candidates-20260610` |
| 策略报告 | PASS | `process/research/multifactor_strategy_candidates/run-cr039-multifactor-strategy-candidates-20260610/STRATEGY-RESEARCH-REPORT.md` |
| 准入包 | PASS | `process/research/multifactor_strategy_candidates/run-cr039-multifactor-strategy-candidates-20260610/STRATEGY-ADMISSION-PACKAGE.json` |

最终候选为 `strategy_equal_weight_baseline`，准入等级为 `research_baseline`，`simulation_candidate=false`。`risk_adjusted_constrained` 因 CR-038 observation 样本容量状态非 PASS 被剔除，不进入最终候选、strategy_scores、risk_cost_summary 或准入包。

所有 forbidden operation counters 为 0；本 CR 不构成 QMT-ready、simulation-ready、live-ready、account/order-ready、provider-ready、lake-ready、publish-ready 或 production-valid。

## 关闭记录

用户于 2026-06-10 回复“接受cr039，然后启动cr041”。本 CR 按用户接受关闭为 `closed-current-delivery`。

关闭结论：

- 最终候选：`strategy_equal_weight_baseline`
- 准入等级：`research_baseline`
- `simulation_candidate=false`
- 可作为 CR041 API-less Paper Simulation Runner 的输入边界
- 不构成 simulation-ready、live-ready、broker-ready 或真实交易授权
- 覆盖标记：CR039 只覆盖 CR026/027/028 中“研究准入是否需要继续上外部 runner / minute / Level2”的判定输入；它没有覆盖 Qlib isolated runner、minute data Spike 或 Level2 microstructure Spike 的实现 / 数据 / 权限工作。

关闭不授权：

- 不连接 QMT / MiniQMT / XtQuant / 掘金量化 / broker
- 不读取账户、持仓、委托、成交或凭据
- 不下单、不撤单
- 不启动 simulation / live
- 不 provider fetch、不 lake write、不 catalog publish
