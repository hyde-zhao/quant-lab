---
handoff_id: "META-SE-CR006-LEGACY-DATA-DIRECTORY-DESIGN-2026-05-18"
from_agent: "meta-po"
to_agent: "meta-se"
status: "completed"
created_at: "2026-05-18T21:12:35+08:00"
workflow_id: "local_backtest"
change_id: "CR-006"
story_id: ""
wave_id: "CR006-solution-design"
context_scope:
  - "process/STATE.md"
  - "process/changes/CR-006-LEGACY-DATA-DIRECTORY-EXTERNALIZATION-2026-05-18.md"
  - "process/changes/CR-005-TUSHARE-5000-DATA-LAYER-REMEDIATION-2026-05-17.md"
  - "process/HLD.md"
  - "process/ARCHITECTURE-DECISION.md"
  - "process/STORY-BACKLOG.md"
  - "process/DEVELOPMENT-PLAN.yaml"
dispatch:
  required: true
  mode: "spawn_agent"
  platform: "codex"
  agent_role: "meta-se"
  agent_path: ""
  tool_name: "spawn_agent"
  agent_id: "019e3b45-76a7-7e00-a354-f4fd9e76fba4"
  agent_name: "se-jiang"
  thread_id: "019e3b45-76a7-7e00-a354-f4fd9e76fba4"
  spawned_at: "2026-05-18T21:27:21+08:00"
  resumed_at: ""
  completed_at: "2026-05-18T21:40:53+08:00"
  evidence: "用户在父线程回复“通过”（按规则等同 approve）后，主线程通过 Codex spawn_agent 真实调度 meta-se/se-jiang 执行 CR-006 HLD/ADR/Story Plan/Development Plan 修订。"
  fallback_reason: ""
  approved_by: "user"
  approved_at: "2026-05-18T21:27:21+08:00"
---

# META-SE Handoff：CR-006 Legacy Data Directory Externalization

## 目标

在用户批准 CR-006 后，由 `meta-se` 修订设计层与 Story 计划，使 legacy 扁平数据目录外置化成为可评审、可拆解、可进入 CR006-BATCH-A LLD 的正式输入。

## 必读最小上下文

| 路径 | 用途 |
|---|---|
| `process/STATE.md` | 当前阶段、active_change、CR-006 等待用户确认状态。 |
| `process/changes/CR-006-LEGACY-DATA-DIRECTORY-EXTERNALIZATION-2026-05-18.md` | 本 CR 的五维影响分析、设计约束、验收口径和建议 Story。 |
| `process/changes/CR-005-TUSHARE-5000-DATA-LAYER-REMEDIATION-2026-05-17.md` | structured `MARKET_DATA_LAKE_ROOT` 边界；CR-006 不得破坏 CR-005。 |
| `process/HLD.md` | 需要增量追加 CR-006 HLD 设计与修订记录。 |
| `process/ARCHITECTURE-DECISION.md` | 需要新增或修订 legacy flat data dir 与 structured lake 分离 ADR。 |
| `process/STORY-BACKLOG.md` | 需要新增 CR006-S01..S03 Story 计划。 |
| `process/DEVELOPMENT-PLAN.yaml` | 需要新增 CR006 Wave、DAG、文件所有权和 dev_gate。 |

## 不得加载 / 不得触碰

- 不读取、列出、迁移、复制或删除真实 `data/**` 数据。
- 不读取、打印或记录 `.env`、Tushare token、NAS 用户名、NAS 密码或真实私有路径。
- 不修改 `engine/**`、`experiments/**`、`market_data/**`、`README.md`、`docs/USER-MANUAL.md`、`config/**` 或测试代码。
- 不生成或改写 Story LLD；CR006-BATCH-A LLD 是 CP3/CP4 通过后的 meta-dev 职责。

## 需要产出

1. 修订 `process/HLD.md`：
   - 追加 CR-006 修订记录。
   - 增加 legacy flat data dir 外置化设计，明确 `LOCAL_BACKTEST_DATA_DIR` 或等价变量与 `MARKET_DATA_LAKE_ROOT` 分离。
   - 保留 `data/` 兼容 fallback，但不推荐真实数据继续放在仓库工作区。
   - 明确不自动迁移 / 复制 / 删除真实数据。

2. 修订 `process/ARCHITECTURE-DECISION.md`：
   - 新增或修订 ADR，冻结 structured lake root 与 legacy flat dir 的职责边界。
   - 明确优先级：显式参数或 CLI 参数 > env / `.env` > config > fallback `data/`。
   - 明确安全边界：不记录凭据、不暴露真实路径、不静默迁移。

3. 修订 `process/STORY-BACKLOG.md` 和 `process/DEVELOPMENT-PLAN.yaml`：
   - 新增 `CR006-S01-legacy-data-dir-config-resolver`。
   - 新增 `CR006-S02-engine-experiments-path-migration`。
   - 新增 `CR006-S03-docs-runbook-and-cleanup-guardrails`。
   - 建立 `CR006-BATCH-A` 作为全量 LLD 设计批次。
   - 明确文件所有权、依赖、dev_gate 和禁止真实数据操作的验证条件。

4. 为 meta-po 触发 CP3 / CP4 准备证据：
   - HLD / ADR 修订后需要 CP3 自动预检和人工确认。
   - Story Plan 修订后需要 CP4 自动预检和人工确认。
   - CP3/CP4 未 approved 前，不得进入 meta-dev LLD。

## Dispatch Evidence

本文件已由主线程在用户回复“通过”后真实调度 `meta-se`：

- `dispatch.mode=spawn_agent`
- `dispatch.tool_name=spawn_agent`
- `dispatch.agent_id=019e3b45-76a7-7e00-a354-f4fd9e76fba4`
- `dispatch.thread_id=019e3b45-76a7-7e00-a354-f4fd9e76fba4`
- `dispatch.agent_name=se-jiang`
- `dispatch.spawned_at=2026-05-18T21:27:21+08:00`
- `dispatch.completed_at=2026-05-18T21:40:53+08:00`

meta-se 已完成并新增 summary：`process/handoffs/META-SE-CR006-LEGACY-DATA-DIRECTORY-DESIGN-SUMMARY-2026-05-18.md`。
