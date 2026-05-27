---
checkpoint_id: "CP4"
checkpoint_name: "CR-006 Story DAG 与并行安全预检"
type: "auto_precheck"
status: "PASS"
owner: "meta-se"
created_at: "2026-05-18T21:30:00+08:00"
checked_at: "2026-05-18T22:10:00+08:00"
target:
  phase: "story-planning"
  story_id: ""
  artifacts:
    - "process/STORY-BACKLOG.md"
    - "process/DEVELOPMENT-PLAN.yaml"
    - "process/stories/CR006-S01-tushare-first-data-acquisition-runbook.md"
    - "process/stories/CR006-S02-canonical-gold-lightweight-engine-adapter.md"
    - "process/stories/CR006-S03-backtrader-clean-feed-contract.md"
    - "process/stories/CR006-S04-old-data-reference-only-guardrail.md"
manual_checkpoint: "checkpoints/CP4-CR006-STORY-PLAN-REVIEW.md"
---

# CP4 CR-006 Story DAG 与并行安全预检

## Entry Criteria

| 条目 | 状态 | 证据 | 说明 |
|---|---|---|---|
| CR-006 HLD / ADR 草案已重写 | PASS | `process/HLD.md` §23；ADR-018 | CP3 自动预检已更新为 Tushare-first，仍待人工确认。 |
| Story Backlog 已替换 CR-006 Story | PASS | `process/STORY-BACKLOG.md` v0.8 | 已替换为 CR006-S01..S04 和 `CR006-BATCH-A` Wave。 |
| Development Plan 已更新 CR-006 | PASS | `process/DEVELOPMENT-PLAN.yaml` v0.6 | 已更新四张 Story、依赖、文件所有权、lld_gate、dev_gate。 |
| Story 卡片齐全 | PASS | `process/stories/CR006-S01...S04*.md` | 四张卡片均包含 dev_context、validation_context、acceptance_criteria。 |

## Checklist

| # | 检查项 | 状态 | 证据 | 处理意见 |
|---|---|---|---|---|
| 1 | Story 覆盖 CR-006 新目标 | PASS | Story Backlog CR006-S01..S04 | S01 覆盖 Tushare acquisition/raw-manifest 审计；S02 覆盖轻量 engine；S03 覆盖 Backtrader feed；S04 覆盖旧 data reference-only。 |
| 2 | Story 粒度合理 | PASS | 四张 Story 卡片 | 每张 Story 有独立目标、文件所有权、验证入口和量化 AC；总数 4，与 HLD §23.12 一致。 |
| 3 | acceptance_criteria 可验证 | PASS | Story 卡片 `acceptance_criteria` | 量化覆盖 raw/manifest 非运行时、quality gate、0 次旧 data 默认 fallback、0 次凭据泄露。 |
| 4 | 依赖关系完整 | PASS | `DEVELOPMENT-PLAN.yaml` dependency_graph | CR005-S01/S02/S03 -> S01；S01/CR005-S03 -> S02；S01/S02/CR005-S06 -> S03；S01/S02/S03 -> S04。 |
| 5 | 依赖类型明确 | PASS | `dependency_type` 字段 | S01 上游为 contract；S02 依赖 contract；S03 依赖 Backtrader contract；S04 依赖 contract/runtime。 |
| 6 | DAG 无环 | PASS | 静态拓扑检查 | 新增边均从 CR005 基线或上游 CR006 Story 指向下游，无回边。 |
| 7 | 文件所有权明确 | PASS | `file_ownership` 字段 | S01 primary acquisition test；S02 primary lightweight adapter test；S03 primary Backtrader feed test；S04 primary old data guardrail test。 |
| 8 | 并行计划合理 | PASS | `parallel_policy.cr006_policy`；`CR006-BATCH-A` | LLD 可按 max_parallel_lld=3 分轮起草并全量确认；开发默认按依赖顺序，避免 shared 文件冲突。 |
| 9 | dev_gate 阻止未确认实现 | PASS | 四张 Story `dev_gate` | `lld_confirmed=false`、`cp5_required=true`、`implementation_allowed=false`。 |
| 10 | 禁止真实数据操作已进入 Story | PASS | Story forbidden / AC | 四张 Story 均禁止真实 `data/**` 操作、`.env`/凭据读取和真实路径记录。 |
| 11 | raw/manifest 职责边界进入 Story | PASS | CR006-S01/S02/S03 | S01 保留 raw/manifest 审计；S02/S03 明确不作为 runtime input。 |
| 12 | 旧 data reference-only 护栏进入 Story | PASS | CR006-S04 | S04 明确旧 `data/` 不作为 fallback、迁移源或覆盖证明。 |
| 13 | CP4 后续调度可计算 | PASS | `CR006-BATCH-A` scope | CP5 批次范围覆盖全部 4 张目标 Story，符合全量 LLD 统一确认路径。 |
| 14 | 未越过实现边界 | PASS | 本轮修改文件清单 | 未修改 engine/experiments/config/README/docs/tests/market_data/delivery 或真实数据；只写过程文档、Story 卡片和检查结果。 |

## Exit Criteria

| 条目 | 状态 | 证据 | 说明 |
|---|---|---|---|
| DAG 校验通过 | PASS | `DEVELOPMENT-PLAN.yaml` `dag_validation_result` | 无循环、无无效引用、无孤立新增节点。 |
| 文件冲突可控 | PASS | Story file_ownership | shared 文件均有 merge_owner；开发默认按依赖顺序调度。 |
| 首批 LLD 队列可计算 | PASS | `CR006-BATCH-A` | 四张 Story 全部进入同一 LLD 批次；max_parallel_lld=3 时可分轮起草，CP5 全量确认。 |
| 人工审查稿需重新发起 | PASS | `checkpoints/CP4-CR006-STORY-PLAN-REVIEW.md` | 本轮仅写自动预检结果；meta-po 负责发起人工确认。 |

## Deliverables

| 交付物 | 路径 | 状态 | 说明 |
|---|---|---|---|
| Story Backlog | `process/STORY-BACKLOG.md` | PASS | 已替换 CR006-S01..S04 与 Wave。 |
| Development Plan | `process/DEVELOPMENT-PLAN.yaml` | PASS | 已更新 DAG、Wave、文件所有权、gate。 |
| Story 卡片 | `process/stories/CR006-S01-tushare-first-data-acquisition-runbook.md` | PASS | Tushare acquisition Story。 |
| Story 卡片 | `process/stories/CR006-S02-canonical-gold-lightweight-engine-adapter.md` | PASS | 轻量 engine adapter Story。 |
| Story 卡片 | `process/stories/CR006-S03-backtrader-clean-feed-contract.md` | PASS | Backtrader clean feed Story。 |
| Story 卡片 | `process/stories/CR006-S04-old-data-reference-only-guardrail.md` | PASS | old data reference-only Story。 |
| CP4 自动预检 | `process/checks/CP4-CR006-STORY-PLAN-PRECHECK.md` | PASS | 本文件。 |

## 结论

- 结论：`PASS`
- 阻断项：无。
- REQUIRED：CP4 人工确认通过前不得启动 CR006-BATCH-A LLD；CP5 全量确认通过前不得实现；旧 `data/**` 读取、比对、迁移、复制或删除仍需用户另行授权。
- 下一步：CP3 通过后，CP4 可由 meta-po 重新发起人工确认；确认对象应为本次四 Story Tushare-first 计划。
