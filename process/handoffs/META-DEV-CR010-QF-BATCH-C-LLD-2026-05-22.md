---
from_agent: "meta-po"
to_agent: "meta-dev"
handoff_id: "META-DEV-CR010-QF-BATCH-C-LLD-2026-05-22"
created_at: "2026-05-22T19:33:44+08:00"
workflow_id: "local_backtest"
change_id: "CR-010"
wave_id: "CR010-QF-BATCH-C"
story_id: ""
status: "handoff-created"
dispatch:
  required: true
  mode: "handoff-only"
  platform: "codex"
  agent_role: "meta-dev"
  agent_path: ".agents/agents/meta-dev.md"
  tool_name: ""
  agent_id: ""
  agent_name: ""
  thread_id: ""
  spawned_at: ""
  resumed_at: ""
  completed_at: ""
  evidence: "当前 meta-po 工具面未提供 spawn_agent/resume_agent/send_input；本文件只表示交接输入，不代表 meta-dev 已执行。"
  fallback_reason: ""
  approved_by: ""
  approved_at: ""
reusable: true
---

# CR010-QF-BATCH-C LLD 交接

## 目标

为 `CR010-S10` 至 `CR010-S12` 输出全量 LLD 与 Story 级 CP5 自动预检，完成后暂停等待 `checkpoints/CP5-CR010-QF-BATCH-C-LLD-BATCH.md` 批次确认。

## 最小上下文

- `process/STATE.md`
- `process/changes/CR-010-REALISTIC-PRODUCTION-DATA-LAKE-2026-05-22.md`
- `process/STORY-BACKLOG.md`
- `process/DEVELOPMENT-PLAN.yaml`
- `checkpoints/CP4-CR010-STORY-PLAN-REVIEW.md`
- `process/checks/REAL-TUSHARE-DATA-LAKE-SMOKE-CR010-RESMOKE-2026-05-22.md`

## Story 范围

| Story | 目标 |
|---|---|
| `CR010-S10-realism-mode-research-metadata` | 统一 `realism_mode` 与 research metadata |
| `CR010-S11-experiments-smoke-limitation-matrix` | 16 experiments smoke limitation matrix |
| `CR010-S12-backtrader-vectorbt-clean-feed-boundary` | Backtrader / VectorBT clean feed 只读边界 |

## 关键约束

- `exploratory` 结果不得写成 `production_strict`。
- 16 个 experiments 必须输出 coverage、benchmark、universe、adjustment、quality/readiness、W3 限制、allowed_claims、blocked_claims 与 strict status。
- Backtrader / VectorBT 消费路径网络调用为 0，不触发补数或真实源。
- 不读取旧 `data/**`，不读取旧质量报告内容，不打印凭据或真实私有路径。
- CP5 批次确认前不得实现。
