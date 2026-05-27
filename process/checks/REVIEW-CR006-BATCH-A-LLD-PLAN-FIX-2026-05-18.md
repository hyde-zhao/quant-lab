---
check_id: "REVIEW-CR006-BATCH-A-LLD-PLAN-FIX"
type: "plan_fix_auto_record"
status: "PASS"
owner: "meta-se"
created_at: "2026-05-18T23:34:18+08:00"
checked_at: "2026-05-18T23:34:18+08:00"
target:
  change_id: "CR-006"
  batch_id: "CR006-BATCH-A"
  artifacts:
    - "process/changes/CR-006-LEGACY-DATA-DIRECTORY-EXTERNALIZATION-2026-05-18.md"
    - "process/STORY-BACKLOG.md"
    - "process/DEVELOPMENT-PLAN.yaml"
source_review:
  - "process/checks/REVIEW-CR006-BATCH-A-LLD-SUMMARY-2026-05-18.md"
  - "process/checks/REVIEW-CR006-BATCH-A-LLD-META-SE-2026-05-18.md"
  - "process/checks/REVIEW-CR006-BATCH-A-LLD-META-QA-2026-05-18.md"
manual_checkpoint: "checkpoints/CP5-CR006-BATCH-A-LLD-BATCH.md"
---

# CR006-BATCH-A LLD 计划侧 REQUIRED 修订检查结果

## Entry Criteria

| 条目 | 状态 | 证据 | 说明 |
|---|---|---|---|
| 双 lane review 聚合已完成 | PASS | `process/checks/REVIEW-CR006-BATCH-A-LLD-SUMMARY-2026-05-18.md` | 聚合结论为 `revise`，REQUIRED=5，其中计划侧由 meta-se 处理 `CR006-REQ-002/003/004`。 |
| 允许写入范围明确 | PASS | 用户指令与 handoff | 本轮仅写入 CR-006、Story Backlog、Development Plan 和本检查记录。 |
| CP5 仍未批准 | PASS | `checkpoints/CP5-CR006-BATCH-A-LLD-BATCH.md` | 本轮不把 CP5 标记为 approved，不进入实现。 |
| 并行 meta-dev 修订范围隔离 | PASS | 用户指令 | 本轮未修改 S02/S03/S04 LLD、CP5 自动预检、代码、测试或文档交付物。 |

## Checklist

| # | 检查项 | 状态 | 证据 | 处理意见 |
|---|---|---|---|---|
| 1 | `CR006-REQ-003`：CR-006 旧 externalization / fallback AC 已收敛为 Tushare-first AC | PASS | `process/changes/CR-006-LEGACY-DATA-DIRECTORY-EXTERNALIZATION-2026-05-18.md` `## 验收口径` | 权威 AC 改为 `CR006-AC-001..014`：Tushare-first、raw/manifest audit-only、lightweight canonical/gold、Backtrader clean feed、old data reference-only。 |
| 2 | `CR006-REQ-003`：Story Backlog CR006-S01..S04 AC 映射覆盖新口径 | PASS | `process/STORY-BACKLOG.md` `## Story 列表` | S01 映射 AC-001/002/003/009；S02 映射 AC-004/005/006/010；S03 映射 AC-007/008/011；S04 映射 AC-012/013/014。 |
| 3 | `CR006-REQ-004`：Story Backlog 顶层 CR005 状态与 verified / CP7 PASS 闭环 | PASS | `process/STORY-BACKLOG.md` frontmatter 与 `## 阻塞项` | `cr005_status=verified-cp7-pass`、`cr005_confirmed=true`；`CR5-BLK-001..005` 已标注 RESOLVED 或 SUPERSEDED。 |
| 4 | `CR006-REQ-004`：Development Plan 顶层 CR005 状态与 verified / CP7 PASS 闭环 | PASS | `process/DEVELOPMENT-PLAN.yaml` frontmatter 与 `state_closure.cr005` | `cr005_status=verified-cp7-pass`、`cr005_confirmed=true`；补充 CR005-S01..S06 Story 与 CP7 证据清单。 |
| 5 | `CR006-REQ-002`：S04 计划侧 dependency_type 统一为 `contract` | PASS | `process/DEVELOPMENT-PLAN.yaml` CR006-S04 `dependency_type` | S04 对 S01/S02/S03 均为 `contract`；required_contracts 补充 S02/S03 合同冻结条件。 |
| 6 | S04 调度说明与 Backlog / LLD 修订方向一致 | PASS | `process/STORY-BACKLOG.md` `CR006-BATCH-A` Wave 行；`process/DEVELOPMENT-PLAN.yaml` `parallel_policy.cr006_policy` | 明确 S04 可在 S02/S03 LLD 合同与边界术语冻结后收敛，不要求等待 S02/S03 CP6 runtime。 |
| 7 | CP5 门控状态保持 changes requested | PASS | CR-006 frontmatter 与处理结论 | CR-006 仍为 `cp5-review-required-changes-pending`，未授权实现。 |
| 8 | 安全边界未放宽 | PASS | CR-006 设计约束、Backlog S04 非范围、Development Plan forbidden 列表 | 继续禁止真实 Tushare 抓取、真实 lake 写入、旧 `data/**` 读取/列出/迁移/复制/比对/删除、`.env` / token / NAS 凭据读取或打印。 |

## Exit Criteria

| 条目 | 状态 | 证据 | 说明 |
|---|---|---|---|
| 计划侧 REQUIRED 已关闭 | PASS | Checklist #1-#6 | 关闭范围仅限 meta-se 计划侧：`CR006-REQ-002/003/004`。 |
| 下游 LLD REQUIRED 未被本轮代改 | PASS | 未修改 `process/stories/*-LLD.md` | `CR006-REQ-001/005` 和 S04 LLD/guardrail advisory 仍由并行 meta-dev 修订与复核。 |
| 不推进开发 | PASS | `implementation_allowed=false` 保持不变 | CP5 required fixes 全部清零并人工 approved 前仍不得实现。 |

## Deliverables

| 交付物 | 路径 | 状态 | 说明 |
|---|---|---|---|
| CR-006 计划侧修订 | `process/changes/CR-006-LEGACY-DATA-DIRECTORY-EXTERNALIZATION-2026-05-18.md` | PASS | 旧 AC 已被 Tushare-first AC 替换。 |
| Story Backlog 修订 | `process/STORY-BACKLOG.md` | PASS | AC 映射、CR005 状态、S04 调度说明已更新。 |
| Development Plan 修订 | `process/DEVELOPMENT-PLAN.yaml` | PASS | CR005 state closure、S04 dependency_type、CR006 policy 已更新。 |
| 计划侧修订检查记录 | `process/checks/REVIEW-CR006-BATCH-A-LLD-PLAN-FIX-2026-05-18.md` | PASS | 本文件。 |

## 结论

- 结论：`PASS`
- 计划侧关闭项：`CR006-REQ-002`、`CR006-REQ-003`、`CR006-REQ-004`
- 非本轮关闭项：`CR006-REQ-001`、`CR006-REQ-005` 以及 S04 LLD/guardrail advisory，由并行 meta-dev 修订后再聚合复核。
- 下一步：交回 meta-po 聚合所有 required fixes；CP5 不得在全部 REQUIRED 清零前 approve。
