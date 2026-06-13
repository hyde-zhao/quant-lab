---
cr_id: CR-041
title: API-less Paper Simulation Runner
status: closed-current-delivery
created_at: 2026-06-10
created_by: codex
owner: meta-po
source: user
change_type: add
impact_level: high
workflow_mode_after_change: standard
activation_policy: "activated by user request: accept CR039 and start CR041"
parent_cr: CR-040
predecessor_cr: CR-039
source_decision_id: USER-20260610-ACCEPT-CR039-START-CR041
related_changes:
  - CR-025
  - CR-030
  - CR-039
  - CR-040
---

# CR-041 API-less Paper Simulation Runner

## 背景与用户决策

用户已明确接受 CR039 输出，并要求启动 CR041。

CR039 的可消费输入边界为：

| 字段 | 值 |
|---|---|
| 最终候选策略 | `strategy_equal_weight_baseline` |
| 准入等级 | `research_baseline` |
| simulation_candidate | `false` |
| 证据路径 | `process/research/multifactor_strategy_candidates/run-cr039-multifactor-strategy-candidates-20260610/STRATEGY-ADMISSION-PACKAGE.json` |

CR041 的目标不是连接真实 broker，而是在完全无 broker / 无账户 / 无外部 SDK 的本地环境中，建立可审计、可复跑的 paper simulation runner，把研究候选策略推进到本地模拟成交、持仓账本、现金账本和净值曲线。

## 冲突预检

| 检查维度 | 结果 | 说明 |
|---|---|---|
| active_change | PASS | CR040 已关闭；CR039 已由用户接受并关闭；CR041 可成为新的 active formal CR。 |
| 受影响正式文档 | PASS | CR041 新增正式 CR，不直接改写 CR039 / CR040 历史结论。 |
| Story / LLD 批次 | PASS | CR041 需要新建 Story 设计批次；不得复用 CR020 QMT Story。 |
| 文件 owner | PASS | 预计新增 `engine/paper_simulation.py`、`scripts/run_paper_simulation.py`、`tests/test_cr041_paper_simulation.py`，不触碰 QMT gateway 文件。 |
| 外部接口 | PASS | 本 CR 不接 QMT / MiniQMT / XtQuant / 掘金 / Backtrader runtime。 |
| 权限 / 安全边界 | PASS | 不读取凭据、不查询账户、不下单、不撤单、不启动 simulation/live。 |
| 运行授权 | PASS | 仅允许本地离线 runner 与 fixture；真实 broker 运行仍为 not-authorized。 |
| 来源决策 | PASS | 用户明确“接受 CR039，然后启动 CR041”。 |

结论：冲突预检通过，允许将 CR041 从 planned 转为正式 active CR。

## 五维度影响分析

| 维度 | 影响 | 结论 |
|---|---|---|
| 需求层 | 新增本地 API-less paper simulation 能力，消费 CR039 research_baseline 策略输入。 | high impact，需要标准流程。 |
| 场景层 | 新增目标组合 -> 订单意图 -> 本地模拟成交 -> 持仓 / 现金 / 净值 / 对账场景。 | 需要 CP2 场景和测试矩阵。 |
| 计划层 | CR041 已拆分为 S01..S05；CR042 BrokerAdapter 合同必须等待 CR041 artifact 合同稳定。 | CP2 / CP3 approved，CP4 PASS，进入 active-cp4-pass-pending-lld。 |
| 安全层 | 本地模拟盘容易被误读为真实仿真或交易授权，必须 fail-closed。 | 明确不授权 broker、账户、凭据、下单、撤单。 |
| 交付层 | 新增 engine、runner、测试、报告 artifact 和过程证据。 | 后续需 CP3/CP4/CP5 后才能实现。 |

## 文档处理决策

| 文档 | 处理方式 | 旧基线保留 |
|---|---|---|
| `process/changes/CR-041-*.md` | 新增 | N/A |
| `process/changes/CR-019-FOLLOW-UP-TRACKING-2026-05-31.md` | 原文档更新 | 保留 CR040 / CR041 路线历史，更新 CR041 active 状态。 |
| `process/STATE.md` | 原文档更新 | 保留 CR039/CR040 关闭记录，写入 CR041 active。 |
| `process/changes/CR-INDEX.yaml` | 原文档更新 | 保留历史 CR 索引，新增 CR041 active。 |
| `scripts/check_cr_tracking_consistency.py` | 原文档更新 | 扩展状态守卫，允许 CR041 active / closed。 |

## 初始 Story 批次

| Story | 名称 | lld_policy | 目标 | 初步文件范围 |
|---|---|---|---|---|
| CR041-S01 | StrategyAdmissionPackage Reader | full-lld | 只读消费 CR039 package，校验 `research_baseline`、`simulation_candidate=false` 和 forbidden counters。 | `engine/paper_simulation.py` |
| CR041-S02 | Target Portfolio and Order Intent Builder | full-lld | 从目标权重 / 目标股数生成本地订单意图，不产生真实订单。 | `engine/paper_simulation.py`, `engine/order_intent_draft.py` |
| CR041-S03 | PaperBroker Fill Engine | full-lld | 本地撮合、partial fill、rejected fill、费用、滑点、涨跌停 / 停牌 / 成交量约束。 | `engine/paper_simulation.py` |
| CR041-S04 | Position / Cash / Equity Ledger | full-lld | 输出 fills、positions、cash ledger、equity curve、drawdown、turnover、cost。 | `engine/paper_simulation.py` |
| CR041-S05 | CLI and Report Artifacts | full-lld | 可复跑 runner，输出 reports 与 process/research artifact，并做 no-real-operation guardrail。 | `scripts/run_paper_simulation.py`, `tests/test_cr041_paper_simulation.py` |

全部 Story 在 CP5 批次统一确认前，不得进入实现。

## 已确认的真实度基线

用户于 2026-06-10 回复“同意”，确认 CR041 的目标为**日频 realistic paper simulation（L2-minus）**，不是盘口级真实撮合或真实仿真账户。

| 决策 | 已确认基线 |
|---|---|
| 真实度目标 | 日频 realistic paper simulation（L2-minus） |
| 信号与交易时间 | T 日收盘后生成信号，T+1 第一个开市日执行 |
| 执行价格 | raw open |
| 估值价格 | raw close |
| 复权边界 | qfq / hfq 不得作为成交执行价 |
| 成本 | commission、min commission、stamp duty、transfer fee |
| 滑点 | fixed bps 第一版基线 |
| 流动性 | max participation rate + partial fill |
| 交易约束 | trade_calendar、trade_status、prices_limit、raw OHLCV 必需；缺失 fail-closed |
| A 股账户规则 | 100 股 lot、现金不足、持仓不足、T+1 可卖 |
| 订单生命周期 | 第一版日内订单，不顺延；未成交记录 rejected / expired |
| 不纳入 | minute / tick / Level2 / order book / queue / 真实 broker 仿真账户 |

## Non-Goals

- 不连接 QMT、MiniQMT、XtQuant、掘金量化或任何 broker。
- 不安装、导入或运行 Backtrader 作为默认 runtime。
- 不读取 token、cookie、session、账户、持仓、委托、成交或任何凭据。
- 不下单、不撤单、不启动真实仿真 / 实盘。
- 不声明 CR039 策略为 simulation-ready、live-ready 或 broker-ready。
- 不写 broker lake、不 provider fetch、不 catalog publish、不扩大数据湖范围。

## 验收标准

- [x] CP2 需求 / 场景基线通过并经用户确认。
- [x] CP3 HLD 明确 API-less runner 架构和不授权边界。
- [x] CP4 Story DAG / 文件 owner / 并行安全检查 PASS。
- [x] 全部 CR041 Story 设计证据通过 CP5 批次人工确认。
- [x] 实现后本地 runner 输出 `order_intents`、`fills`、`positions`、`equity_curve`、`reconciliation`。
- [x] 所有 forbidden operation counters 为 0。
- [x] 测试覆盖 package 校验、订单意图、撮合、ledger、report 和不授权 guardrail。

## 当前阶段结论

`closed-current-delivery`。用户于 2026-06-11T00:20:00+08:00 回复“同意”，接受 CP8 `READY_WITH_RISK`、`DQ-CP8-CR041-01` 至 `DQ-CP8-CR041-04` 的推荐方案，以及两项 LOW residual risk（`CR041-RISK-CP7-01`、`CR041-RISK-CP7-02`）。CR041 当前 API-less 本地 paper simulation runner 交付范围已关闭。

CR041 已完成 CP2 / CP3 用户确认、CP4 Story DAG 自动预检、S01..S05 全部 full-lld / CP5 自动预检、CP5 批次人工确认、S01..S05 CP6 实现自检、CP7 独立验证、CP8 发布就绪自动预检和 CP8 人工终验：

- `process/checkpoints/CP2-CR041-REQUIREMENTS-BASELINE.md`
- `process/checkpoints/CP3-CR041-HLD-REVIEW.md`
- `process/checks/CP4-CR041-STORY-DAG-PARALLEL-SAFETY.md`
- `process/checkpoints/CP5-CR041-ALL-STORIES-LLD-BATCH.md`
- `process/context/CP6-CR041-CODING-CONTEXT.yaml`
- `process/checks/CP6-CR041-S01-strategy-admission-package-reader-CODING-DONE.md`
- `process/checks/CP6-CR041-S02-target-portfolio-order-intent-builder-CODING-DONE.md`
- `process/checks/CP6-CR041-S03-paper-broker-fill-engine-CODING-DONE.md`
- `process/checks/CP6-CR041-S04-position-cash-equity-ledger-CODING-DONE.md`
- `process/checks/CP6-CR041-S05-cli-report-artifacts-CODING-DONE.md`
- `process/checks/CP6-CR041-CP7-F01-validation-to-dict-CODING-DONE.md`
- `process/checks/CP7-CR041-PAPER-SIMULATION-VERIFICATION-DONE.md`
- `process/context/CP7-CR041-VERIFICATION-CONTEXT.yaml`
- `process/checks/CP8-CR041-DELIVERY-READINESS.md`
- `process/checkpoints/CP8-CR041-DELIVERY-READINESS.md`
- `process/release/RELEASE-CONTEXT.yaml`
- `docs/release/RELEASE-NOTES.md`

CP7 结论为 `PASS_WITH_RISK`，原 blocker `F-CR041-CP7-001` 已回修并关闭。CP8 自动预检 PASS，CP8 人工终验 approved；当前实现仍不授权 broker、Backtrader runtime、掘金、QMT、账户、凭据、下单、撤单、provider fetch、lake write、catalog publish 或 simulation/live。

CP8 approve 仅确认当前本地 runner 交付就绪并接受上述 LOW 风险，不授权真实发布、broker、Backtrader runtime、掘金、QMT、账户、凭据、下单、撤单、provider fetch、lake write、catalog publish、simulation/live 或任何交易运行。后续 CR042 / CR043 / CR044 必须独立启动、独立设计和独立授权。
