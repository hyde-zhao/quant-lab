---
handoff_id: "META-DEV-CR025-LLD-BATCH-A-2026-06-01"
from_agent: "meta-po"
to_agent: "meta-dev"
workflow_id: "local_backtest-cr025"
change_id: "CR-025"
phase: "story-planning"
batch_id: "CR025-RESEARCH-EXECUTION-SEMANTIC-ALIGNMENT-BATCH-A"
lld_wave_id: "CR025-LLD-W1-FEED-SEMANTIC"
story_scope:
  - "CR025-S01-clean-feed-gate-backend-selector"
  - "CR025-S02-semantic-diff-schema-artifact"
  - "CR025-S04-backtrader-module-reference-no-copy-guardrail"
created_at: "2026-06-01T22:58:54+08:00"
status: "completed-closed"
dispatch:
  required: true
  semantic: "lld-batch-dispatch"
  mode: "subagent"
  platform: "codex"
  agent_role: "meta-dev"
  agent_path: ".agents/agents/meta-dev.md"
  tool_name: "multi_agent_v1.spawn_agent"
  agent_id: "019e83b3-a392-7892-a311-49e6a7e571c9"
  agent_name: "dev-zhang"
  thread_id: "019e83b3-a392-7892-a311-49e6a7e571c9"
  spawned_at: "2026-06-01T23:00:59+08:00"
  completed_at: "2026-06-01T23:11:56+08:00"
  evidence: "spawn_agent returned agent_id=019e83b3-a392-7892-a311-49e6a7e571c9 nickname=dev-zhang for CR-025 LLD Batch A; wait_agent completed with 3 LLD and 3 CP5 PASS; close_agent called."
  fallback_reason: ""
  approved_by: ""
  approved_at: ""
reuse_key:
  role: "meta-dev"
  workflow_id: "local_backtest-cr025"
  change_id: "CR-025"
  batch_id: "CR025-RESEARCH-EXECUTION-SEMANTIC-ALIGNMENT-BATCH-A"
  lld_wave_id: "CR025-LLD-W1-FEED-SEMANTIC"
---

# META-DEV CR-025 LLD Batch A 交接

## 任务

请以 `meta-dev` 身份只为 CR-025 的 LLD Batch A 起草 Story 级 LLD 与 CP5 自动预检。CR-025 CP4 已 PASS，允许进入 LLD 设计；本轮仍不授权实现、依赖变更、Backtrader 运行、源码迁移或任何真实外部操作。

## 必读输入

| 文件 | 用途 |
|---|---|
| `AGENTS.md` | CP5、LLD、子 agent 调度、真实操作禁止边界 |
| `process/STATE.md` | 当前 active_change、LLD 批次、禁止操作边界 |
| `process/changes/CR-025-BACKTRADER-OPTIONAL-EXECUTION-BACKEND-HARDENING-2026-05-31.md` | CR 范围、验收、关闭边界 |
| `process/HLD.md` §34 | CR-025 HLD、Backtrader 模块矩阵、clean feed、semantic diff |
| `process/HLD-QMT-TRADING.md` §18 | `order_intent_draft_v1` 下游边界 |
| `process/ARCHITECTURE-DECISION.md` ADR-074..ADR-077 | 架构决策和 no-copy / optional runtime 决策 |
| `process/STORY-BACKLOG.md` | Story / Wave / DAG / open questions |
| `process/DEVELOPMENT-PLAN.yaml` | 文件所有权、依赖、完成准则 |
| `process/STORY-STATUS.md` | 当前 Story 状态，只读 |
| `process/checks/CP4-CR025-STORY-DAG-PARALLEL-SAFETY.md` | CP4 PASS 与 CP5 前禁止边界 |
| `process/stories/CR025-S01-clean-feed-gate-backend-selector.md` | S01 Story 卡片 |
| `process/stories/CR025-S02-semantic-diff-schema-artifact.md` | S02 Story 卡片 |
| `process/stories/CR025-S04-backtrader-module-reference-no-copy-guardrail.md` | S04 Story 卡片 |

## 允许写入

| Story | LLD 输出 | CP5 自动预检输出 |
|---|---|---|
| `CR025-S01-clean-feed-gate-backend-selector` | `process/stories/CR025-S01-clean-feed-gate-backend-selector-LLD.md` | `process/checks/CP5-CR025-S01-clean-feed-gate-backend-selector-LLD-IMPLEMENTABILITY.md` |
| `CR025-S02-semantic-diff-schema-artifact` | `process/stories/CR025-S02-semantic-diff-schema-artifact-LLD.md` | `process/checks/CP5-CR025-S02-semantic-diff-schema-artifact-LLD-IMPLEMENTABILITY.md` |
| `CR025-S04-backtrader-module-reference-no-copy-guardrail` | `process/stories/CR025-S04-backtrader-module-reference-no-copy-guardrail-LLD.md` | `process/checks/CP5-CR025-S04-backtrader-module-reference-no-copy-guardrail-LLD-IMPLEMENTABILITY.md` |

## 禁止写入

- 不修改 `process/STORY-BACKLOG.md`、`process/DEVELOPMENT-PLAN.yaml`、`process/STORY-STATUS.md`、`process/STATE.md`、`README.md`、`docs/USER-MANUAL.md`。
- 不修改代码、测试、依赖或配置：`engine/**`、`trading/**`、`tests/**`、`pyproject.toml`、`uv.lock`、`.env`。
- 不复制、裁剪、改写或源码级移植 `/home/hyde/download/backtrader/**`、Backtrader samples、tests、datas、live store 或 line/metaclass runtime。
- 不运行 Backtrader、不安装依赖、不触发真实 broker / QMT / MiniQMT / XtQuant / provider / lake / broker lake / publish / simulation / live，不读取凭据。

## LLD 内容要求

- 每份 `STORY-*-LLD.md` 必须保持 14 个可见章节，覆盖文件影响范围、数据模型、接口、核心流程、异常处理、测试设计、实施步骤、风险、回滚策略、OPEN/Spike 状态。
- S01 必须冻结 clean feed gate、backend selector、lazy import / structured unavailable、默认 Backtrader import count = 0。
- S02 必须冻结 semantic diff schema / artifact，不允许 reference 覆盖 lightweight baseline，不允许声明 production truth / simulation-ready。
- S04 必须冻结 Backtrader module reference / no-copy guardrail，`migration_candidate=[]`，并说明任何源码级移植例外必须另起 CR 或回退 CP3/CP5。
- 每份 CP5 自动预检必须包含 Entry Criteria、Checklist、Exit Criteria、Deliverables、结论，结论只能基于 LLD 可实现性，不得批准实现。

## 完成回报

完成后返回：

- 创建的 3 份 LLD 路径。
- 创建的 3 份 CP5 自动预检路径与结论。
- 未回答阻断问题数量；如有 LLD clarification item，列出 `id/story_id/question/blocks_lld`。
- 确认未执行的禁止操作计数均为 0。

## 完成摘要

| 交付物 | 路径 | 结果 |
|---|---|---|
| LLD | `process/stories/CR025-S01-clean-feed-gate-backend-selector-LLD.md` | ready-for-review |
| LLD | `process/stories/CR025-S02-semantic-diff-schema-artifact-LLD.md` | ready-for-review |
| LLD | `process/stories/CR025-S04-backtrader-module-reference-no-copy-guardrail-LLD.md` | ready-for-review |
| CP5 自动预检 | `process/checks/CP5-CR025-S01-clean-feed-gate-backend-selector-LLD-IMPLEMENTABILITY.md` | PASS |
| CP5 自动预检 | `process/checks/CP5-CR025-S02-semantic-diff-schema-artifact-LLD-IMPLEMENTABILITY.md` | PASS |
| CP5 自动预检 | `process/checks/CP5-CR025-S04-backtrader-module-reference-no-copy-guardrail-LLD-IMPLEMENTABILITY.md` | PASS |

未回答阻断问题数量：0。禁止操作执行计数：0。本 handoff 完成不表示 CP5 人工确认已通过，也不授权实现。
