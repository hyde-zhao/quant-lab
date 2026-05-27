---
plan_id: "LLD-BATCH-REMAINING-2026-05-15"
created_at: "2026-05-15"
created_by: "meta-po"
status: "confirmed"
scope: "remaining-story-lld-package"
source_story_backlog: "process/STORY-BACKLOG.md"
source_development_plan: "process/DEVELOPMENT-PLAN.yaml"
handoff: "process/handoffs/META-DEV-LLD-BATCH-REMAINING-2026-05-15.md"
checkpoint: "checkpoints/STORY-PACKAGE-LLD-CHECKPOINT.md"
delivery_write_allowed: false
implementation_allowed: true
---

# 剩余 Story LLD 批量输出计划

## 1. 工作流纠偏结论

用户已明确纠偏当前工作流理解：不能继续按“每个 Story 临到开发前才逐个输出 LLD”的旧流程推进。当前流程应理解为：

1. `meta-se` 完成 Story 分解和开发计划后，进入 Story Package 准备。
2. `meta-dev` 根据已确认的 Story Backlog、Development Plan、HLD 和 ADR 输出 Story 级 LLD。
3. `meta-po` 聚合 LLD 包并发起人工确认。
4. LLD 包确认通过后，才允许进入对应 Story 的实现。

本次纠偏不回滚已完成的 W0 实现与验证事实；从当前时点起，暂停 STORY-004 单张 LLD 确认后的实现路径。剩余 Story 的 LLD 包已补齐，并已由用户在 `checkpoints/STORY-PACKAGE-LLD-CHECKPOINT.md` 中确认通过。

## 2. 当前 LLD 盘点

| Story ID | Wave | Story 状态 | LLD 状态 | 检查点状态 | 结论 |
|---|---|---|---|---|---|
| STORY-001 | W0 | verified | confirmed | confirmed | 已完成，不重做 |
| STORY-002 | W0 | verified | confirmed | confirmed | 已完成，不重做 |
| STORY-003 | W0 | verified | confirmed | confirmed | 已完成，不重做 |
| STORY-004 | W1 | package-ready-for-review | ready-for-review, confirmed=false, open_items=4 | pending-human-confirmation | 已有 LLD，纳入批量 LLD 包统一确认 |
| STORY-005 | W1 | package-ready-for-review | ready-for-review, confirmed=false, open_items=3 | pending-human-confirmation | 已完成 LLD 草案，纳入批量确认 |
| STORY-006 | W1 | package-ready-for-review | ready-for-review, confirmed=false, open_items=2 | pending-human-confirmation | 已完成 LLD 草案，纳入批量确认 |
| STORY-007 | W2 | package-ready-for-review | ready-for-review, confirmed=false, open_items=1 | pending-human-confirmation | 已完成 LLD 草案，纳入批量确认 |
| STORY-008 | W2 | package-ready-for-review | ready-for-review, confirmed=false, open_items=1 | pending-human-confirmation | 已完成 LLD 草案，纳入批量确认 |
| STORY-009 | W3 | package-ready-for-review | ready-for-review, confirmed=false, open_items=4 | pending-human-confirmation | 已完成 LLD 草案，纳入批量确认 |
| STORY-010 | W3 | package-ready-for-review | ready-for-review, confirmed=false, open_items=3 | pending-human-confirmation | 已完成 LLD 草案，纳入批量确认 |
| STORY-011 | W3 | package-ready-for-review | ready-for-review, confirmed=false, open_items=3 | pending-human-confirmation | 已完成 LLD 草案，纳入批量确认 |
| STORY-012 | W3 | package-ready-for-review | ready-for-review, confirmed=false, open_items=2 | pending-human-confirmation | 已完成 LLD 草案，纳入批量确认 |
| STORY-013 | W4 | package-ready-for-review | ready-for-review, confirmed=false, open_items=2 | pending-human-confirmation | 已完成 LLD 草案，纳入批量确认 |

## 3. 批量输出范围

本轮要求 `meta-dev` 输出以下 9 个缺失 LLD；当前 9 个草案均已输出，等待 meta-po 聚合批量检查点：

| Story ID | 目标 LLD 路径 |
|---|---|
| STORY-005 | `process/stories/STORY-005-momentum-portfolio-engine-LLD.md` |
| STORY-006 | `process/stories/STORY-006-backtest-metrics-report-metadata-LLD.md` |
| STORY-007 | `process/stories/STORY-007-parameter-sweep-report-LLD.md` |
| STORY-008 | `process/stories/STORY-008-candidate-report-jq-template-LLD.md` |
| STORY-009 | `process/stories/STORY-009-pit-universe-provider-contract-LLD.md` |
| STORY-010 | `process/stories/STORY-010-trade-status-constraints-LLD.md` |
| STORY-011 | `process/stories/STORY-011-limit-event-available-at-LLD.md` |
| STORY-012 | `process/stories/STORY-012-bias-audit-report-LLD.md` |
| STORY-013 | `process/stories/STORY-013-strategy-extension-rsi-macd-LLD.md` |

`STORY-004` LLD 已存在，本轮只允许在批量包一致性需要时修订 `process/stories/STORY-004-offline-data-loader-contract-validator-LLD.md`，不得把它确认为可实现。

## 4. 并行策略

LLD 起草属于设计产物输出，不是代码实现。允许 `meta-dev` 在同一个 handoff 下按 Wave/依赖分组并行或分批输出：

| 分组 | Story | 并行说明 |
|---|---|---|
| G1 | STORY-005, STORY-006 | 可同批起草，但 STORY-006 必须显式引用 STORY-005 的结果接口；若接口不确定，写入 `open_items` |
| G2 | STORY-007, STORY-008 | 可同批起草，但 STORY-008 必须显式引用 STORY-007 扫描报告 schema |
| G3 | STORY-009, STORY-010, STORY-011, STORY-012 | 可同批起草；STORY-010 依赖 STORY-009，STORY-011 依赖 STORY-009 与 STORY-010，STORY-012 依赖 STORY-010/011，依赖不确定处必须状态化 |
| G4 | STORY-013 | 可与 G3 同批起草；依赖 STORY-008 的候选/扫描接口，不得要求 W3 已实现 |

并行只适用于 LLD 文档起草；实现仍按用户确认后的 Story/Wave 门控执行。

## 5. 统一 LLD 契约

每个 `STORY-*-LLD.md` 必须保持 14 个可见章节，不得因 Tier 简化而合并章节。frontmatter 必须包含：

- `story_id`
- `title`
- `story_slug`
- `tier`
- `status: "ready-for-review"`
- `confirmed: false`
- `source_story`
- `source_hld`
- `source_adr`
- `shared_fragments`
- `open_items`
- `depends_on`

每个 LLD 至少覆盖文件影响范围、接口设计、核心流程、异常处理、测试设计、实施步骤、风险、回滚策略和 Definition of Done。

## 6. 禁止范围

本轮只允许输出 LLD 过程文档和必要的 Story 状态回写。禁止：

- 实现代码。
- 生成真实数据。
- 写入 `data/**`、`reports/**` 的真实产物。
- 写入 `delivery/**`。
- 生成安装脚本。
- 创建或修改仓库级 guardrail 脚本。
- 把任一 Story 推进到 `in-development`。
- 把任一未确认 LLD 标记为 `confirmed=true`。

## 7. 当前检查点

`meta-po` 已创建新的批量 LLD / Story Package 检查点：`checkpoints/STORY-PACKAGE-LLD-CHECKPOINT.md`。检查点已覆盖：

1. STORY-004 至 STORY-013 的 LLD 是否齐全。
2. 每个 LLD 是否满足 14 章节和强输入字段要求。
3. `open_items` 是否完整状态化。
4. 与 HLD、ADR、Story Backlog、Development Plan 是否一致。
5. 是否存在代码、数据、`delivery/**` 或安装脚本越界输出。

批量检查点已确认通过，已允许进入后续 Story 实现调度；截至 2026-05-16，`STORY-004` 至 `STORY-013` 均已 verified。`delivery_write_allowed=false` 继续生效，文档交付出口确认前不得写入 `delivery/**`。
