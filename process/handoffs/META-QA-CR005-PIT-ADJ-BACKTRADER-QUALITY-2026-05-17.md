---
handoff_id: "META-QA-CR005-PIT-ADJ-BACKTRADER-QUALITY-2026-05-17"
from_agent: "meta-po"
to_agent: "meta-qa"
status: "completed"
created_at: "2026-05-17T17:55:47+08:00"
workflow_id: "local_backtest"
change_id: "CR-005"
story_id: "CR005-QUALITY-REVIEW-REVISION-2"
wave_id: "CR005-SOLUTION-DESIGN-REVISION-2"
dispatch:
  required: true
  mode: "subagent"
  platform: "codex"
  agent_role: "meta-qa"
  agent_path: ".codex/agents/meta-qa.toml"
  tool_name: "spawn_agent"
  agent_id: "019e354c-746a-7540-bad1-6c06588d7f72"
  agent_name: "qa-kong"
  thread_id: "019e354c-746a-7540-bad1-6c06588d7f72"
  spawned_at: "2026-05-17T17:55:47+08:00"
  resumed_at: ""
  completed_at: "2026-05-17T17:55:47+08:00"
  evidence: "用户回报主线程已通过 spawn_agent 真实并行调度第二轮 meta-qa；agent_id=019e354c-746a-7540-bad1-6c06588d7f72，nickname=qa-kong，状态 completed。meta-qa 已更新 process/TEST-STRATEGY.md 与 process/checks/QA-CR005-QUALITY-REVIEW.md，新增 PIT as-of、复权一致性、Backtrader 干净输入边界三类 CP5 前 BLOCKING 质量门，并更新 CP5 前最小测试清单。"
  fallback_reason: ""
  approved_by: ""
  approved_at: ""
---

# Handoff：CR-005 PIT / 复权 / Backtrader 第二轮质量评审

## 触发背景

用户在 CP3/CP4 人工确认前追加 PIT、复权、Pandas 数据层和 Backtrader 职责边界修改点，要求第二轮 meta-qa 并行评审质量门和回归范围。

## 第二轮 meta-qa 完成范围

用户回报第二轮 `meta-qa/qa-kong` 已完成以下正式产物修改：

- `process/TEST-STRATEGY.md`
- `process/checks/QA-CR005-QUALITY-REVIEW.md`

关键落点：

- 新增 PIT as-of join CP5 前 BLOCKING 质量门：非行情数据必须按 `available_date` / `effective_date` / `available_at` 对齐，future leak 负例必须阻断。
- 新增复权一致性 CP5 前 BLOCKING 质量门：数据层保存 `adj_factor`、adjusted price 和 `adjustment_policy`，收益、技术指标、forward return 使用统一复权价格。
- 新增 Backtrader 干净输入边界 CP5 前 BLOCKING 质量门：Backtrader 只消费已通过 PIT、复权和 quality gate 的干净 factor panel / score / feed。
- 更新 CP5 前最小测试清单，覆盖默认离线、凭据安全、PIT 负例、复权缺失/混用、quality gate、Backtrader 未安装降级和 adapter 边界扫描。

## 当前门控

- 本 handoff 只记录真实第二轮子 agent 调度和质量评审结果。
- CP3/CP4 仍等待人工确认。
- CP5 未满足前不得实现真实 Tushare 调用、Backtrader adapter、依赖变更或真实数据写入。
