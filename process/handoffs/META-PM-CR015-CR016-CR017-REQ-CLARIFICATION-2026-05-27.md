---
handoff_id: "META-PM-CR015-CR016-CR017-REQ-CLARIFICATION-2026-05-27"
from_agent: "meta-po"
to_agent: "meta-pm"
created_at: "2026-05-27T22:50:13+08:00"
status: "completed"
workflow_id: "local_backtest-cr015-cr016-cr017"
change_ids:
  - "CR-015"
  - "CR-016"
  - "CR-017"
dispatch:
  mode: "spawned"
  agent_id: "019e69ec-0002-7860-969e-a4cce1cb4ae9"
  thread_id: "019e69ec-0002-7860-969e-a4cce1cb4ae9"
  tool_name: "multi_agent_v1.spawn_agent"
  spawned_at: "2026-05-27T22:50:13+08:00"
  resumed_at: ""
  completed_at: "2026-05-27T23:10:03+08:00"

## 完成摘要

- 修改 `process/USE-CASES.md`：新增 `UC-10`、`UC-11`、`UC-12`，更新到 `version: "1.7"`、`total_use_cases: 12`。
- 修改 `process/REQUIREMENTS.md`：新增 `REQ-098` 至 `REQ-122`，更新到 `version: "1.8"`，`source_use_cases` 扩展到 UC-01..UC-12。
- 修改 `process/CLARIFICATION-LOG.md`：Q-025 至 Q-029 更新为 `RESOLVED_USER_APPROVED`，新增 Q-030 至 Q-038 为 `REQUIRED_FOR_CP3`。
- 未执行代码修改、真实抓取、写湖、QMT 调用、发单、撤单或凭据读取。
---

# Meta-PM Handoff: CR-015 / CR-016 / CR-017 Requirement Clarification

## 目标

基于已批准的 CP2 intake 决策，增量刷新 CR-015、CR-016、CR-017 的场景与需求基线。

## 输入

| 输入 | 路径 |
|---|---|
| CP2 intake 决策稿 | `checkpoints/CP2-CR015-CR016-CR017-INTAKE-DECISION-BRIEF.md` |
| CR-015 | `process/changes/CR-015-QMT-TRADING-FOUNDATION-2026-05-27.md` |
| CR-016 | `process/changes/CR-016-QMT-SIMULATION-LIVE-ACTIVATION-2026-05-27.md` |
| CR-017 | `process/changes/CR-017-ADJUSTMENT-POLICY-DUAL-VIEW-SUPPORT-2026-05-27.md` |
| 缺口检查 | `process/checks/CR015-CR016-CR017-GAP-REVIEW-2026-05-27.md` |
| 现有场景 | `process/USE-CASES.md` |
| 现有需求 | `process/REQUIREMENTS.md` |
| 澄清日志 | `process/CLARIFICATION-LOG.md` |

## 已批准决策

| ID | 结论 |
|---|---|
| D-ALL-01 | 混合推进：先冻结 CR-017 复权与 raw 交易价边界；CR-015 foundation 可并行做无真实发单设计；CR-016 真实激活后置。 |
| D-CR15-01 | Windows QMT / MiniQMT 节点 + XtQuant 外部 Python API + OMS + QMT adapter；策略不得直接调用 QMT API。 |
| D-CR15-02 | 建立本地订单状态机、外置 broker lake、pre-trade hard block；默认仅 shadow / dry-run / mock，不授权真实发单。 |
| D-CR17-01 | `prices_raw` + `adj_factor` 为事实源；独立派生 `prices_qfq`、`prices_hfq`、`returns_adjusted`；qfq 必须记录 `as_of_trade_date`；QMT 使用 raw/broker price。 |
| D-CR16-01 | `shadow -> QMT 模拟盘 -> 实盘只读 -> 小资金实盘 -> 放大资金`；T 日收盘后信号，T+1 限价 / 保护价；必须有 runbook、对账、kill switch、per-run 授权。 |

## 任务

1. 增量更新 `process/USE-CASES.md`：
   - 追加 CR-015 QMT foundation 使用场景。
   - 追加 CR-016 QMT simulation/live activation 使用场景。
   - 追加 CR-017 adjustment dual-view 使用场景。
   - 保留 UC-01 至 UC-09 旧基线，更新修订记录、persona、success metrics、Out of Scope、边界说明、验证场景矩阵。
2. 增量更新 `process/REQUIREMENTS.md`：
   - 追加 CR-015 / CR-016 / CR-017 对应 REQ 编号，不覆盖 REQ-001 至 REQ-097。
   - 明确无真实发单、无真实抓取/写湖、无复权价下单、凭据脱敏和 per-run 授权边界。
   - 将 `research_adjustment_policy` 与 `execution_price_policy=raw` 写入需求。
   - 将 raw/qfq/hfq/returns_adjusted、qfq `as_of_trade_date` 和 migration 需求写入需求。
3. 增量更新 `process/CLARIFICATION-LOG.md`：
   - 记录本轮用户 approve。
   - 若仍有 HLD 前必须决策的问题，列为 `REQUIRED_FOR_CP3`，不要阻塞已批准的 CP2 intake。
4. 输出简短完成摘要，列出新增 UC / REQ 编号、仍待 CP3 处理的问题、没有执行的高风险动作。

## 输出约束

- 只允许修改：
  - `process/USE-CASES.md`
  - `process/REQUIREMENTS.md`
  - `process/CLARIFICATION-LOG.md`
- 不修改代码。
- 不读取或输出 `.env` / token / 账户信息。
- 不执行 QMT、Tushare、真实写湖或真实发单。
- 不覆盖历史报告或旧数据。
