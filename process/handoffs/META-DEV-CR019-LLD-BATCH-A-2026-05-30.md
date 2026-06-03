---
handoff_id: "META-DEV-CR019-LLD-BATCH-A-2026-05-30"
from_agent: "meta-po"
to_agent: "meta-dev"
workflow_id: "local_backtest-cr019"
change_id: "CR-019"
phase: "story-planning"
created_at: "2026-05-30T18:26:00+08:00"
status: "agent_completed"
dispatch:
  required: true
  semantic: "stage-dispatch"
  mode: "subagent"
  platform: "codex"
  agent_role: "meta-dev"
  agent_path: ".agents/agents/meta-dev.md"
  tool_name: "multi_agent_v1.spawn_agent"
  agent_id: "019e786c-c6c5-71d1-83d9-0af5a4457eb3"
  agent_name: "dev-he"
  thread_id: "019e786c-c6c5-71d1-83d9-0af5a4457eb3"
  spawned_at: "2026-05-30T18:27:49+08:00"
  resumed_at: ""
  completed_at: "2026-05-30T18:42:39+08:00"
  evidence: "spawn_agent returned agent_id=019e786c-c6c5-71d1-83d9-0af5a4457eb3 nickname=dev-he; close_agent previous_status returned completed LLD Batch A with CR019-S01..S04 CP5 PASS"
  fallback_reason: ""
  approved_by: ""
  approved_at: ""
reuse_key:
  role: "meta-dev"
  workflow_id: "local_backtest-cr019"
  change_id: "CR-019"
  story_id: "CR019-LLD-BATCH-A"
  wave_id: "CR019-STAGE6-QMT-BRIDGE-BATCH-A"
---

# META-DEV CR-019 LLD Batch A

## 任务

请以 `meta-dev` 身份为以下 Story 编写 LLD 与对应 CP5 自动预检。只允许写入本批 Story 卡片、Story LLD 和 CP5 自动预检；不得实现代码、修改依赖、启动服务、读取凭据或执行真实 QMT / provider / lake / broker / publish / simulation / live 操作。

## 分配 Story

| Story | 文件 |
|---|---|
| CR019-S01-stage6-admission-gate-package | `process/stories/CR019-S01-stage6-admission-gate-package.md` |
| CR019-S02-primary-benchmark-dashboard | `process/stories/CR019-S02-primary-benchmark-dashboard.md` |
| CR019-S03-qmt-cside-client-cli-contract | `process/stories/CR019-S03-qmt-cside-client-cli-contract.md` |
| CR019-S04-windows-gateway-lifecycle-deployment | `process/stories/CR019-S04-windows-gateway-lifecycle-deployment.md` |

## 必读输入

| 文件 | 用途 |
|---|---|
| `AGENTS.md` | LLD、CP5、并行 LLD clarification queue 和禁止实现门控 |
| `process/STATE.md` | 当前 CR-019、CP4 PASS、并行 LLD 边界 |
| `process/STORY-BACKLOG.md` | CR019-S01..S10、Wave、DAG、阻塞项 |
| `process/DEVELOPMENT-PLAN.yaml` | `cr019_plan`、文件所有权、依赖、CP5 前门控 |
| `process/checks/CP4-CR019-STORY-DAG-PARALLEL-SAFETY.md` | CP4 PASS 证据 |
| `process/HLD.md` | §33 CR-019 HLD |
| `process/HLD-QMT-TRADING.md` | §17 QMT companion HLD |
| `process/ARCHITECTURE-DECISION.md` | ADR-067..ADR-073、AD-Q64..AD-Q70 |
| `checkpoints/CP3-CR019-HLD-REVIEW.md` | CP3 approved 决策 |

## 目标输出

1. 为每个 Story 新增 `process/stories/<story_id>-LLD.md`。
2. 每份 LLD 必须包含 14 个可见章节，frontmatter `confirmed=false`、`status=ready-for-review`、`cp5_batch=CR019-STAGE6-QMT-BRIDGE-BATCH-A`。
3. 为每个 Story 新增 CP5 自动预检：`process/checks/CP5-<story_id>-LLD-IMPLEMENTABILITY.md`。
4. 可更新本批 4 张 Story 卡片状态为 `lld-ready-for-review` 或等价待审查状态；不要修改 `process/STATE.md`、`process/STORY-STATUS.md`、`process/STORY-BACKLOG.md` 或 `process/DEVELOPMENT-PLAN.yaml`。

## 约束

- 不得创建实现文件：`engine/**`、`trading/**`、`docs/**`、`tests/**` 只能在 LLD/CP5 中描述，不得实际创建或修改。
- 不得生成 CR019-S05..S10 的 LLD 或 CP5 预检。
- 如发现阻断性实现灰区，写入 LLD 的 OPEN/Spike，并在最终回复中按 `lld_clarification_queue` 字段格式列出；不要直接询问用户。
- CP5 自动预检必须包含 Entry Criteria、Checklist、Exit Criteria、Deliverables 和 Agent Dispatch Evidence。
