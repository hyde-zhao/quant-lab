---
handoff_id: "META-SE-CR025-STORY-PLANNING-CP4-2026-06-01"
from_agent: "meta-po"
to_agent: "meta-se"
workflow_id: "local_backtest-cr025"
change_id: "CR-025"
phase: "story-planning"
created_at: "2026-06-01T22:37:12+08:00"
status: "completed-closed"
dispatch:
  required: true
  semantic: "stage-dispatch"
  mode: "subagent"
  platform: "codex"
  agent_role: "meta-se"
  agent_path: ".agents/agents/meta-se.md"
  tool_name: "multi_agent_v1.spawn_agent"
  agent_id: "019e839f-a973-7781-bed7-5261c695b887"
  agent_name: "se-shen"
  thread_id: "019e839f-a973-7781-bed7-5261c695b887"
  spawned_at: "2026-06-01T22:39:04+08:00"
  resumed_at: ""
  completed_at: "2026-06-01T22:42:19+08:00"
  evidence: "spawn_agent returned agent_id=019e839f-a973-7781-bed7-5261c695b887 nickname=se-shen for CR-025 Story Plan / CP4; wait_agent completed with CP4 PASS and close_agent called by meta-po."
  fallback_reason: ""
  approved_by: ""
  approved_at: ""
reuse_key:
  role: "meta-se"
  workflow_id: "local_backtest-cr025"
  change_id: "CR-025"
  story_id: "CR025-STORY-PLANNING-CP4"
  wave_id: "CR025-CP4"
---

# META-SE CR-025 Story Plan / CP4 交接

## 任务

请以 `meta-se` 身份执行 CR-025 的 Story Plan / CP4 阶段。CR-025 CP3 已由用户在 2026-06-01T22:37:12+08:00 回复“同意。继续”，`checkpoints/CP3-CR025-HLD-REVIEW.md` 已回填为 `approved`。

本轮只允许 Story 拆解、开发计划和 CP4 自动预检产物；不得生成 Story LLD，不得实现代码，不得修改依赖，不得运行 Backtrader，不得复制 / 裁剪 / 改写 / 源码级移植 Backtrader GPLv3 源码，不得触发真实 broker / QMT / MiniQMT / XtQuant / provider / lake / broker lake / publish / simulation / live，不得读取凭据。

## 必读输入

| 文件 / 路径 | 用途 |
|---|---|
| `AGENTS.md` | Story Plan、CP4、CP5、LLD 全量确认和子 agent 调度门控 |
| `process/STATE.md` | 当前 active_change、CP3 approved 状态、禁止真实操作边界 |
| `process/changes/CR-025-BACKTRADER-OPTIONAL-EXECUTION-BACKEND-HARDENING-2026-05-31.md` | CR-025 范围、影响面、验收和关闭边界 |
| `process/USE-CASES.md` | UC-19、SM-33 至 SM-41、TS-025-01 至 TS-025-11 |
| `process/REQUIREMENTS.md` | REQ-161 至 REQ-173、RA-057 至 RA-066 |
| `process/HLD.md` | §34 CR-025 HLD，含 Backtrader 模块矩阵、clean feed、semantic diff、order intent |
| `process/HLD-QMT-TRADING.md` | §18 `order_intent_draft_v1` 消费边界 |
| `process/ARCHITECTURE-DECISION.md` | ADR-074 至 ADR-077、AD-Q71 至 AD-Q76 |
| `process/discussions/CP3-CR025-HLD-DISCUSSION-LOG.md` | CP3 Architecture Gray Areas 和 advisor table |
| `process/checks/CP3-CR025-DISCUSSION-CHECKPOINT.json` | CP3 discussion 恢复点 |
| `process/checks/CP3-CR025-HLD-CONSISTENCY.md` | CP3 自动预检 PASS |
| `checkpoints/CP3-CR025-HLD-REVIEW.md` | CP3 人工审查 approved |
| `process/STORY-BACKLOG.md` | 现有 Story Backlog，需增量追加 CR-025 Story，不重写旧基线 |
| `process/DEVELOPMENT-PLAN.yaml` | 现有开发计划，需增量追加 CR-025 Wave / DAG / file owner / 完成准则 |
| `process/STORY-STATUS.md` | 状态汇总，需同步 CR-025 Story Plan / CP4 状态 |

## 必须覆盖的 Story 拆分维度

请基于 HLD §34 和 ADR-074..077 拆分 CR-025 Story。具体 Story 数量由你基于 DAG、文件所有权、CP5 全量 LLD 批次和可验证边界决定，但至少覆盖：

1. `clean feed gate`：PIT、`available_at`、复权口径、benchmark、tradability、quality、lineage、limitations。
2. `semantic diff schema / artifact`：lightweight baseline 与 Backtrader-style semantic reference 的成交、现金、成本、滑点、净值和差异原因。
3. `target portfolio / order_intent_draft_v1`：研究输出到 order intent draft 的字段、失败路径和 QMT 消费边界。
4. Backtrader module reference guardrail：HLD §34.5 的 `reference_only` / `adapt_interface` / `exclude` 分类、GPLv3 no-copy、`migration_candidate` 当前为空。
5. optional runtime boundary：若后续 CP5 选择 Backtrader optional dependency runtime，只能通过 optional dependency + lazy import；未安装必须 structured unavailable；本轮仍不得改 `pyproject.toml` / `uv.lock`。
6. no-real-operation safety：真实 broker、Backtrader live store、QMT、provider、lake、publish、simulation、live、credential 全部计数为 0。
7. 后续 QMT 路线衔接：CR-025 只提供 draft/evidence；CR-020..CR-024 保持独立授权。
8. 测试 / 验证策略：fixture、自有行为样例、forbidden import / forbidden source copy scan、schema contract、semantic diff contract。

## 目标输出

请最小化修改 / 新增以下产物：

1. 更新 `process/STORY-BACKLOG.md`，增量追加 CR-025 Story 清单、Story 数、Wave 数、状态和修订记录。
2. 更新 `process/DEVELOPMENT-PLAN.yaml`，增量追加 CR-025 Wave、DAG、依赖类型、并行策略、file ownership、merge owner、完成准则和 no-real-operation gates。
3. 更新 `process/STORY-STATUS.md`，同步 CR-025 Story Plan / CP4 状态。
4. 如项目惯例需要 Story 卡片，请新增 `process/stories/CR025-*.md`；不得新增 `*-LLD.md`。
5. 写入 CP4 自动预检：`process/checks/CP4-CR025-STORY-DAG-PARALLEL-SAFETY.md`。

## 验收要求

- CP4 自动预检必须包含 Entry Criteria、Checklist、Exit Criteria、Deliverables。
- Story Plan 必须明确 Story 数、Wave 数、DAG、依赖类型、并行性、文件所有权、merge order、完成准则和禁止真实操作边界。
- Story 数量、Wave 数量必须在 `STORY-BACKLOG.md`、`DEVELOPMENT-PLAN.yaml`、`STORY-STATUS.md` 和 CP4 中一致。
- CP4 只授权 Story Plan / DAG / 并行安全预检；不授权 LLD、实现、依赖变更、Backtrader 运行、源码移植或真实操作。
- 必须把 HLD §34.5 的 Backtrader 模块矩阵落到 Story/LLD 后续输入：默认 `migration_candidate` 为空；后续实现只能 clean-room 定义本项目接口。
- 必须显式说明 CP4 通过后，下一步仍需 meta-po 组织全量 LLD 队列与 CP5 人工确认，CP5 approved 前不得实现。

## 完成摘要

| 项目 | 结果 | 证据 |
|---|---|---|
| Story Plan | PASS | `process/STORY-BACKLOG.md`、`process/DEVELOPMENT-PLAN.yaml`、`process/STORY-STATUS.md` |
| Story 卡片 | PASS | `process/stories/CR025-S01..S06*.md` |
| CP4 自动预检 | PASS | `process/checks/CP4-CR025-STORY-DAG-PARALLEL-SAFETY.md` |
| Story / Wave / LLD 批次 | PASS | 6 Story / 4 Wave / 1 LLD batch：`CR025-RESEARCH-EXECUTION-SEMANTIC-ALIGNMENT-BATCH-A` |
| 子 agent 生命周期 | completed-closed | `multi_agent_v1.wait_agent` 返回 completed；`multi_agent_v1.close_agent` 已调用 |

本 handoff 完成不授权 LLD、实现、依赖变更、Backtrader 运行、源码移植、真实 broker / QMT / provider / lake / publish / simulation / live 或凭据读取。下一步由 meta-po 组织全量 LLD 队列和 CP5 批次人工确认。
