---
handoff_id: "META-SE-CR006-BATCH-A-REQUIRED-FIXES-PLAN-2026-05-18"
from_agent: "meta-po"
to_agent: "meta-se"
status: "handoff-created"
created_at: "2026-05-18T23:24:55+08:00"
workflow_id: "local_backtest"
change_id: "CR-006"
batch_id: "CR006-BATCH-A"
dispatch:
  required: true
  mode: "handoff-only"
  platform: "codex"
  agent_role: "meta-se"
  agent_path: ".codex/agents/meta-se.toml"
  tool_name: ""
  agent_id: ""
  agent_name: ""
  thread_id: ""
  spawned_at: ""
  resumed_at: ""
  completed_at: ""
  evidence: "当前 meta-po 工具面无法直接 spawn_agent；主线程需真实 spawn/resume meta-se 并回填 dispatch evidence。"
  fallback_reason: ""
  approved_by: ""
  approved_at: ""
---

# Handoff: CR006-BATCH-A Required Fixes - Planning / AC / State Closure

## Dispatch Requirement

主线程需要通过 Codex `spawn_agent` 或复用合适 meta-se 线程执行本任务，并回填 `dispatch.agent_id`、`thread_id`、`tool_name`、`spawned_at`、`completed_at`。

## 任务目标

处理聚合评审中的计划与验收口径 REQUIRED：

- `CR006-REQ-002` 的计划侧：将 S04 对 S02/S03 的依赖类型统一为 `contract`，或明确 S04 必须晚于 S02/S03 CP6。当前 meta-po 判定倾向统一为 `contract`。
- `CR006-REQ-003`：修订 CR-006 与 Story Backlog 的 Tushare-first AC 映射，清理旧 externalization / fallback AC 冲突。
- `CR006-REQ-004`：闭环 Story Backlog / Development Plan 顶层 CR005 状态和 CR5-BLK 阻塞项，使其与 CR005 Story verified / CP7 PASS 事实一致。
- `CR006-ADV-002`：可顺手处理 HLD §23 锚点可追溯性；不得为此扩大范围。

## 允许写入范围

- `process/changes/CR-006-LEGACY-DATA-DIRECTORY-EXTERNALIZATION-2026-05-18.md`
- `process/STORY-BACKLOG.md`
- `process/DEVELOPMENT-PLAN.yaml`
- 可新增一个计划侧修订检查记录：`process/checks/REVIEW-CR006-BATCH-A-LLD-PLAN-FIX-2026-05-18.md`

## 禁止范围

- 不修改业务代码、实验、配置、README/docs/tests/market_data/delivery。
- 不读取、列出、迁移、复制、比对或删除真实 `data/**`。
- 不读取或打印 `.env`、Tushare token、NAS 用户名、密码或真实私有路径。
- 不把 CP5 标记为 approved。

## 输入文件

- `process/checks/REVIEW-CR006-BATCH-A-LLD-SUMMARY-2026-05-18.md`
- `process/checks/REVIEW-CR006-BATCH-A-LLD-META-SE-2026-05-18.md`
- `process/checks/REVIEW-CR006-BATCH-A-LLD-META-QA-2026-05-18.md`
- `process/changes/CR-006-LEGACY-DATA-DIRECTORY-EXTERNALIZATION-2026-05-18.md`
- `process/STORY-BACKLOG.md`
- `process/DEVELOPMENT-PLAN.yaml`
- `checkpoints/CP5-CR006-BATCH-A-LLD-BATCH.md`

## 完成标准

- REQUIRED `CR006-REQ-002/003/004` 的计划侧状态均已修订或明确状态化。
- 输出文件不与 S02/S03/S04 meta-dev LLD 修订写入范围冲突。
- 明确 CP5 仍为 `changes_requested`，等待所有 required fixes 完成后由 meta-po 聚合。
