---
handoff_id: "META-DEV-CR006-S02-LLD-REQUIRED-FIX-2026-05-18"
from_agent: "meta-po"
to_agent: "meta-dev"
status: "handoff-created"
created_at: "2026-05-18T23:24:55+08:00"
workflow_id: "local_backtest"
change_id: "CR-006"
story_id: "CR006-S02-canonical-gold-lightweight-engine-adapter"
batch_id: "CR006-BATCH-A"
recommended_resume_agent_id: "019e3b8b-14a3-78a2-942b-4c696480fd80"
recommended_agent_name: "dev-zhu"
dispatch:
  required: true
  mode: "handoff-only"
  platform: "codex"
  agent_role: "meta-dev"
  agent_path: ".codex/agents/meta-dev.toml"
  tool_name: ""
  agent_id: ""
  agent_name: ""
  thread_id: ""
  spawned_at: ""
  resumed_at: ""
  completed_at: ""
  evidence: "当前 meta-po 工具面无法直接 spawn_agent/resume_agent；主线程需真实 resume/spawn meta-dev 并回填 dispatch evidence。"
  fallback_reason: ""
  approved_by: ""
  approved_at: ""
---

# Handoff: CR006-S02 LLD Required Fix

## Dispatch Requirement

优先 `resume_agent` 复用 dev-zhu `019e3b8b-14a3-78a2-942b-4c696480fd80`；不可复用时由主线程真实 `spawn_agent` 新 meta-dev。

## 任务目标

处理 `CR006-REQ-005`：external `legacy_flat` 需要明确是 S02 必交付能力还是可选兼容入口，并同步测试与 Definition of Done。

## 允许写入范围

- `process/stories/CR006-S02-canonical-gold-lightweight-engine-adapter-LLD.md`
- `process/checks/CP5-CR006-S02-canonical-gold-lightweight-engine-adapter-LLD-IMPLEMENTABILITY.md`

## 禁止范围

- 不修改业务代码、实验、配置、README/docs/tests/market_data/delivery。
- 不修改 `process/STORY-BACKLOG.md`、`process/DEVELOPMENT-PLAN.yaml` 或 CR-006；这些由 meta-se 计划修订包负责。
- 不读取、列出、迁移、复制、比对或删除真实 `data/**`。
- 不读取或打印 `.env`、Tushare token、NAS 凭据或真实私有路径。
- 不把 LLD `confirmed` 改为 true，不把 CP5 标记为 approved。

## 完成标准

- S02 LLD 明确选择 A 必交付或 B 可选兼容入口。
- 接口、测试、实施步骤、风险、DoD 与该选择一致。
- S02 CP5 自动预检重跑/更新为 PASS 或明确仍有 REQUIRED。
