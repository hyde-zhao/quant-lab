---
from_agent: "meta-po"
to_agent: "meta-dev"
handoff_id: "META-DEV-CR010-DL-BATCH-B-LLD-2026-05-22"
created_at: "2026-05-22T19:33:44+08:00"
workflow_id: "local_backtest"
change_id: "CR-010"
wave_id: "CR010-DL-BATCH-B"
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

# CR010-DL-BATCH-B LLD 交接

## 目标

为 `CR010-S06` 至 `CR010-S09` 输出全量 LLD 与 Story 级 CP5 自动预检，完成后暂停等待 `checkpoints/CP5-CR010-DL-BATCH-B-LLD-BATCH.md` 批次确认。

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
| `CR010-S06-pit-source-interface-spike-readiness` | PIT exact source/interface 未确认前 fail-fast，禁止模糊匹配 |
| `CR010-S07-trade-status-contract-reader-fail-fast` | `trade_status` source/interface 或 `available_at` 缺失时 fail-fast |
| `CR010-S08-prices-limit-contract-gate-fail-fast` | `prices_limit` source/interface 或 `available_at` 缺失时 fail-fast |
| `CR010-S09-events-available-at-contract-fail-fast` | events 缺 explicit `available_at` 时 fail-fast |

## 关键约束

- 不把 `index_weights` 或 `stock_basic` 替代 `index_members`。
- `production_strict` 对 PIT/W3 缺口必须 fail；exploratory 必须写 limitation。
- 不真实接 provider，不触发真实 Tushare 抓取，不读取旧 `data/**`。
- 不打印 `.env`、token、NAS 凭据或真实私有路径。
- 交付 LLD 后由 meta-po 生成或回收 CP5 批次人工审查；CP5 通过前不得实现。
