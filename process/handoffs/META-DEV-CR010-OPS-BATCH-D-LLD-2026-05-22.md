---
from_agent: "meta-po"
to_agent: "meta-dev"
handoff_id: "META-DEV-CR010-OPS-BATCH-D-LLD-2026-05-22"
created_at: "2026-05-22T19:33:44+08:00"
workflow_id: "local_backtest"
change_id: "CR-010"
wave_id: "CR010-OPS-BATCH-D"
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

# CR010-OPS-BATCH-D LLD 交接

## 目标

为 `CR010-S13` 至 `CR010-S16` 输出全量 LLD 与 Story 级 CP5 自动预检，完成后暂停等待 `checkpoints/CP5-CR010-OPS-BATCH-D-LLD-BATCH.md` 批次确认。

## 最小上下文

- `process/STATE.md`
- `process/changes/CR-010-REALISTIC-PRODUCTION-DATA-LAKE-2026-05-22.md`
- `process/STORY-BACKLOG.md`
- `process/DEVELOPMENT-PLAN.yaml`
- `checkpoints/CP4-CR010-REMAINING-BATCHES-STORY-PLAN-REVIEW.md`
- `process/checks/REAL-TUSHARE-DATA-LAKE-SMOKE-CR010-RESMOKE-2026-05-22.md`

## Story 范围

| Story | 目标 |
|---|---|
| `CR010-S13-backup-archive-restore-env-manifest-contract` | backup/archive/restore env 与 manifest/checksum/脱敏契约 |
| `CR010-S14-backup-cli-dry-run-execute-verify-report` | `backup-plan`、`backup-run`、`backup-verify`、`backup-report` |
| `CR010-S15-restore-cli-drill-read-revalidate-replay` | `restore-plan`、`restore-run`、`restore-drill` |
| `CR010-S16-retention-policy-archive-backup-cleanup` | retention policy 与 archive/backup cleanup |

## 关键约束

- 新增 CLI 默认 dry-run；只有显式 `--execute` 才允许复制、恢复或删除。
- `restore-root==lake-root` 必须 fail-fast。
- checksum skip/mismatch 必须 fail。
- 报告必须脱敏，不记录 token、`.env` 内容、NAS 凭据或真实私有路径。
- `restore-drill` 必须只读执行 `read/revalidate/replay`，`network_calls=0`。
- 旧 `data/**` 对比继续暂缓；不得读取、列出、迁移、复制、比对或删除。
