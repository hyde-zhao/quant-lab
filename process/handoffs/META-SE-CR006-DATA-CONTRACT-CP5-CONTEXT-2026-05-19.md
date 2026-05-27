---
handoff_id: "META-SE-CR006-DATA-CONTRACT-CP5-CONTEXT-2026-05-19"
from_agent: "meta-po"
from_agent_name: "po-sun"
to_agent: "meta-se"
status: "completed"
created_at: "2026-05-19T21:18:31+08:00"
workflow_id: "local_backtest"
change_id: "CR-006"
batch_id: "CR006-BATCH-A"
task_type: "minor_doc_fix_before_cp5"
recommended_output: "process/checks/CR006-DATA-CONTRACT-CP5-CONTEXT-2026-05-19.md"
recommended_resume_agent_id: "019e3bab-199f-7f21-a772-c6ffaae65f95"
recommended_agent_name: "se-wei"
dispatch:
  required: true
  mode: "resume_agent"
  platform: "codex"
  agent_role: "meta-se"
  agent_path: ".codex/agents/meta-se.toml"
  tool_name: "resume_agent/send_input"
  agent_id: "019e3bab-199f-7f21-a772-c6ffaae65f95"
  agent_name: "se-wei"
  thread_id: "019e3bab-199f-7f21-a772-c6ffaae65f95"
  spawned_at: ""
  resumed_at: "2026-05-19T21:18:31+08:00"
  completed_at: "2026-05-19T21:31:58+08:00"
  evidence: "主线程通过 Codex 子 agent 能力复用 meta-se/se-wei，完成 CR006 数据分层、存储格式与对外接口契约 CP5 审查上下文；仅写入 process/checks/CR006-DATA-CONTRACT-CP5-CONTEXT-2026-05-19.md。"
  fallback_reason: ""
  approved_by: ""
  approved_at: ""
---

# Handoff: CR006 Data Contract CP5 Context

## Dispatch Requirement

优先复用 `meta-se/se-wei` 线程 `019e3bab-199f-7f21-a772-c6ffaae65f95`；不可复用时由主线程真实 `spawn_agent` 新 meta-se。handoff 文件只表示交接，不表示目标 agent 已执行。

复用键：

- role: `meta-se`
- workflow_id: `local_backtest`
- change_id: `CR-006`
- batch_id: `CR006-BATCH-A`
- wave_id: `CR006-BATCH-A-cp5-context-fix`

## Task Goal

起草 CP5 审查上下文文件：

- `process/checks/CR006-DATA-CONTRACT-CP5-CONTEXT-2026-05-19.md`

主题为“CR006 数据分层、存储格式与对外接口契约”。该文件只汇总既有 HLD / ADR / LLD 事实，帮助用户在 CP5 人工确认前集中审查数据分层、存储格式、对外接口、allowed consumers / forbidden consumers 和 typed errors。

## Classification

本任务已由 meta-po 路由为 `minor_doc_fix_before_cp5`：

- 不刷新 HLD / ADR。
- 不重跑 CP3。
- 不重制 Story，不改 Story 边界、DAG、文件所有权或 Wave。
- 不重跑 CP4。
- 不修改 LLD 或 Story 级 CP5 自动预检。
- 不批准 CP5，不进入实现。

## Minimum Context

请只读取以下上下文：

- `process/checks/CR006-HLD-STORY-REFRESH-EVALUATION-2026-05-19.md`
- `process/HLD.md` §23
- `process/ARCHITECTURE-DECISION.md` 中 ADR-018，必要时只参考 ADR-011 / ADR-014 / ADR-016 / ADR-017
- `process/stories/CR006-S01-tushare-first-data-acquisition-runbook-LLD.md` 中数据分层、存储格式、接口相关章节
- `process/stories/CR006-S02-canonical-gold-lightweight-engine-adapter-LLD.md` 中 canonical/gold reader、external `legacy_flat`、typed error 相关章节
- `process/stories/CR006-S03-backtrader-clean-feed-contract-LLD.md` 中 clean feed、reader、validator、forbidden boundary 相关章节
- `process/stories/CR006-S04-old-data-reference-only-guardrail-LLD.md` 中 old data reference-only、guardrail allowlist/denylist、文档合同相关章节
- `process/checks/REVIEW-CR006-BATCH-A-LLD-POST-FIX-2026-05-18.md`
- `checkpoints/CP5-CR006-BATCH-A-LLD-BATCH.md`
- `process/STATE.md` 中 CR006 CP5 状态摘要

## Output Requirements

输出 `process/checks/CR006-DATA-CONTRACT-CP5-CONTEXT-2026-05-19.md`，建议结构：

1. `## 结论`：说明这是 CP5 审查上下文，不是新架构决策。
2. `## 数据分层总览`：用表格集中列出 acquisition/raw-manifest audit、normalization-quality-catalog-gold、runtime adapter/feed、old data reference-only。
3. `## 存储格式与布局契约`：列出 raw、manifest、canonical、quality、catalog、gold、external `legacy_flat`、Backtrader clean feed、repo `data/`。
4. `## 对外接口契约`：列出 Tushare job -> raw/manifest、raw/manifest -> canonical/gold、canonical/gold -> lightweight engine、canonical/gold -> Backtrader clean feed、old data guardrail。
5. `## Allowed / Forbidden Consumers`：明确轻量 engine、Backtrader、实验、normalization/replay、old data reference-only 的允许和禁止消费面。
6. `## Typed Errors`：只引用已有错误，例如 `required_missing`、`quality_failed`、`lineage_missing`、`pit_failed`、`adjustment_policy_mismatch`、`backend_unavailable`、`interface_not_allowed`。
7. `## CP5 审查影响`：说明该附录不改变 HLD/ADR/Story/LLD/CP5 自动预检；完成后可回到 CP5 人工确认。
8. `## Safety Confirmation`：确认未读取真实 `data/**`，未读取 `.env` / 凭据，未执行 Tushare / lake 操作。

## Allowed Writes

- `process/checks/CR006-DATA-CONTRACT-CP5-CONTEXT-2026-05-19.md`

## Forbidden Writes

- `process/HLD.md`
- `process/ARCHITECTURE-DECISION.md`
- `process/STORY-BACKLOG.md`
- `process/DEVELOPMENT-PLAN.yaml`
- `process/stories/CR006-S01-tushare-first-data-acquisition-runbook-LLD.md`
- `process/stories/CR006-S02-canonical-gold-lightweight-engine-adapter-LLD.md`
- `process/stories/CR006-S03-backtrader-clean-feed-contract-LLD.md`
- `process/stories/CR006-S04-old-data-reference-only-guardrail-LLD.md`
- any business code, tests, docs, delivery files, real data files, `.env` or credentials

## Safety Boundaries

- 不读取、列出、迁移、复制、比对或删除真实 `data/**`。
- 不读取、打印或记录 `.env`、Tushare token、NAS 用户名、NAS 密码或真实私有路径。
- 不执行 Tushare 抓取、真实 lake read/write、normalize/revalidate/replay job。
- 不把 CP5 写为 approved，不把 `implementation_allowed` 改为 true。

## Completion Criteria

- 输出文件存在且只汇总已有事实。
- 明确说明不新增架构决策、不改变 Story 边界、不触发 CP3/CP4 重跑。
- 明确 CP5 仍未批准，完成后交回 meta-po 恢复 CP5 人工确认。
- 回填本 handoff 的 `dispatch` 字段或由主线程在 STATE/CR 中补充真实调度证据。

## Completion Evidence

- completed_at: `2026-05-19T21:31:58+08:00`
- agent: `meta-se/se-wei`
- agent_id: `019e3bab-199f-7f21-a772-c6ffaae65f95`
- output: `process/checks/CR006-DATA-CONTRACT-CP5-CONTEXT-2026-05-19.md`
- result: `PASS_FOR_CONTEXT_APPENDIX`
- scope confirmation:
  - HLD / ADR / Story / Story DAG / 文件所有权：未改变
  - CP3 / CP4：不触发重跑
  - CP5 自动预检 / CP5 人工稿：未修改
  - CP5 approval：未批准
  - implementation_allowed：保持 `false`
