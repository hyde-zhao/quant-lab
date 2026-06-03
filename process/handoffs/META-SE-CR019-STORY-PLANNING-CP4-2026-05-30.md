---
handoff_id: "META-SE-CR019-STORY-PLANNING-CP4-2026-05-30"
from_agent: "meta-po"
to_agent: "meta-se"
workflow_id: "local_backtest-cr019"
change_id: "CR-019"
phase: "story-planning"
created_at: "2026-05-30T18:04:03+08:00"
status: "agent_completed"
dispatch:
  required: true
  semantic: "stage-dispatch"
  mode: "subagent"
  platform: "codex"
  agent_role: "meta-se"
  agent_path: ".agents/agents/meta-se.md"
  tool_name: "multi_agent_v1.resume_agent / multi_agent_v1.send_input"
  agent_id: "019e782a-2097-7112-a0da-9f0a692a06fd"
  agent_name: "se-wei"
  thread_id: "019e782a-2097-7112-a0da-9f0a692a06fd"
  spawned_at: "2026-05-30T17:14:51+08:00"
  resumed_at: "2026-05-30T18:05:47+08:00"
  completed_at: "2026-05-30T18:25:09+08:00"
  evidence: "resume_agent returned status=pending_init; send_input submission_id=019e7858-c8a3-7e40-966a-2b880f64eb7e for CR-019 Story Plan / CP4; close_agent previous_status returned completed Story Plan with 10 Stories, 5 Waves, CP4 PASS"
  fallback_reason: ""
  approved_by: ""
  approved_at: ""
reuse_key:
  role: "meta-se"
  workflow_id: "local_backtest-cr019"
  change_id: "CR-019"
  story_id: "CR019-STORY-PLANNING-CP4"
  wave_id: "CR019-G2-CP4"
---

# META-SE CR-019 Story Plan / CP4 交接

## 任务

请以 `meta-se` 身份执行 CR-019 的 Story Plan / CP4 阶段。CP3 已由用户 `approve`，DQ-01 至 DQ-07 全部接受，其中 DQ-04 已修订为配对式 token/HMAC 默认启用。

本轮只允许 Story 拆解、开发计划和 CP4 自动预检产物，不允许 Story LLD、代码实现、依赖变更、服务启动、凭据读取、真实 QMT / MiniQMT / XtQuant 调用、真实 provider fetch、真实 lake / broker lake 写入、publish 或 simulation / live run。

## 必读输入

| 文件 | 用途 |
|---|---|
| `AGENTS.md` | Story Plan、CP4、CP5 和子 agent 调度门控规则 |
| `process/STATE.md` | 当前 active_change、CP3 approved 状态和禁止真实操作边界 |
| `process/changes/CR-019-STAGE6-MULTIFACTOR-SIMULATION-ARCHITECTURE-2026-05-30.md` | CR-019 范围与影响分析 |
| `process/USE-CASES.md` | UC-15 至 UC-18 |
| `process/REQUIREMENTS.md` | REQ-138 至 REQ-160 |
| `process/CLARIFICATION-LOG.md` | Q-039 至 Q-044 |
| `process/HLD.md` | §33 CR-019 HLD，包含 C/S bridge、完整 endpoint matrix、pairing/HMAC、运行门控和后置能力 |
| `process/HLD-QMT-TRADING.md` | §17 QMT companion HLD |
| `process/ARCHITECTURE-DECISION.md` | ADR-067 至 ADR-073、AD-Q64 至 AD-Q70 |
| `process/discussions/CP3-CR019-HLD-DISCUSSION-LOG.md` | CP3 architecture gray areas 和 DQ-04 修订记录 |
| `process/checks/CP3-CR019-DISCUSSION-CHECKPOINT.json` | CP3 discussion 恢复点 |
| `process/checks/CP3-CR019-HLD-CONSISTENCY.md` | CP3 自动预检 PASS |
| `checkpoints/CP3-CR019-HLD-REVIEW.md` | CP3 人工审查 approved |
| `process/STORY-BACKLOG.md` | 现有 Story Backlog，需增量追加 CR-019 Story，不重写旧基线 |
| `process/DEVELOPMENT-PLAN.yaml` | 现有开发计划，需增量追加 CR-019 Wave / DAG / file ownership，不重写旧基线 |
| `process/STORY-STATUS.md` | 状态汇总，需同步 CR-019 Story Plan / CP4 状态 |

## 必须覆盖的 Story 拆分维度

至少覆盖以下能力面，具体 Story 数量由你基于 DAG、文件归属和 CP5 批次设计决定：

1. 阶段六多因子 admission gate、多基准看板和 primary benchmark。
2. QMT C 侧 Python client / 函数接口与薄 CLI。
3. Windows FastAPI gateway 可运行 / 可安装命令与服务生命周期。
4. 配对式 token/HMAC：pair request / list / approve / complete、请求签名、timestamp、nonce、scope、日志脱敏。
5. 完整 QMT endpoint matrix：health/capabilities、validate/dry-run、行情、账户、持仓、委托、成交、simulation submit/cancel、live-readonly、live submit/cancel、reconciliation、kill-switch。
6. 运行门控：run mode、stage gate、risk gate、kill-switch、per-run authorization 与 blocked reason。
7. Fallback / incident：blocked-only、人工 dry-run / signed file drop、fail closed。
8. 后置能力边界：Backtrader、Qlib、minute、Level2 的触发条件和不进入 P0 的门控。
9. 文档 / runbook / 用户手册更新边界。

## 目标输出

请最小化修改 / 新增以下产物：

1. 更新 `process/STORY-BACKLOG.md`，增量追加 CR-019 Story 清单。
2. 更新 `process/DEVELOPMENT-PLAN.yaml`，增量追加 CR-019 Wave、DAG、依赖、并行性、file owner 和完成准则。
3. 如本项目惯例需要 Story 卡片，请新增 `process/stories/CR019-*.md`；不得新增 LLD。
4. 写入 CP4 自动预检：`process/checks/CP4-CR019-STORY-DAG-PARALLEL-SAFETY.md`。
5. 更新 `process/STORY-STATUS.md` 的 CR-019 Story Plan / CP4 状态。

## 验收要求

- CP4 自动预检必须包含 Entry Criteria、Checklist、Exit Criteria、Deliverables。
- Story Plan 必须明确 Wave、DAG、依赖类型、并行性、文件所有权、完成准则和不得真实操作边界。
- Story 数量、Wave 数量必须在 `STORY-BACKLOG.md`、`DEVELOPMENT-PLAN.yaml` 和 CP4 中一致。
- 必须显式说明 CP4 通过不授权 LLD 或实现；后续必须进入全量 LLD 批次和 CP5 人工确认。
- 不得把完整 endpoint 可见写成真实 QMT 已授权。
- 不得把 pairing/HMAC 鉴权写成交易授权或替代运行门控。
- 不得读取 `.env`、token、账户、session 或任何真实凭据。
