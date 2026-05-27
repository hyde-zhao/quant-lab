---
checkpoint_id: "CP4"
checkpoint_name: "CR-006 Story 拆解与并行安全门"
type: "auto_then_manual"
status: "approved"
owner: "meta-po"
created_at: "2026-05-18T22:33:23+08:00"
reviewed_by: "user"
reviewed_at: "2026-05-18T22:33:23+08:00"
auto_check_result: "process/checks/CP4-CR006-STORY-PLAN-PRECHECK.md"
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
    - "process/checks/CP4-CR006-STORY-PLAN-PRECHECK.md"
---

# CP4 CR-006 Story 拆解与并行安全门人工审查

本检查点确认对象是 CR-006 Tushare-first 方案下的四 Story 计划与 DAG：

1. `CR006-S01-tushare-first-data-acquisition-runbook`
2. `CR006-S02-canonical-gold-lightweight-engine-adapter`
3. `CR006-S03-backtrader-clean-feed-contract`
4. `CR006-S04-old-data-reference-only-guardrail`

本 CP4 只批准 Story 边界、依赖 DAG、文件所有权、并行 LLD 策略和门控；不授权实现、不授权真实 Tushare 抓取、不授权读取/列出/迁移/复制/比对/删除旧 `data/**`，也不授权读取或打印 `.env`、token、NAS 凭据。

## 自动预检摘要

| 预检文件 | 结论 | 阻断项 | 说明 |
|---|---|---|---|
| `process/checks/CP4-CR006-STORY-PLAN-PRECHECK.md` | PASS | 0 | CR006-BATCH-A 四张 Story、DAG、文件所有权、dev_gate、no-old-data 操作边界和 CP5 全量确认路径均已静态预检通过。 |

## 审查回填说明

用户最新回复“全部接受，拉起meta-po继续推进，能够并行时，拉起子agent并行。”按本轮用户指令，视为对后续 CP4 Story Plan 的明确批准，前提是 CP4 自动预检 PASS 且人工稿内容与当前四 Story Tushare-first 计划一致。当前 `process/checks/CP4-CR006-STORY-PLAN-PRECHECK.md` 结论为 PASS，本文件确认对象也限定为上述四 Story 计划，因此回填为 `approved`。

## Entry Criteria

| 条目 | 状态 | 证据 | 审查意见 |
|---|---|---|---|
| CP3 HLD / ADR 已批准 | approved | `checkpoints/CP3-CR006-HLD-REVIEW.md` | 用户已接受 Tushare-first HLD / ADR 架构增量。 |
| CP4 自动预检已通过 | approved | `process/checks/CP4-CR006-STORY-PLAN-PRECHECK.md` | 无 BLOCKING / FAIL。 |
| Story Backlog 已包含四 Story | approved | `process/STORY-BACKLOG.md` | CR006-S01..S04 与 CR006-BATCH-A 一致。 |
| Development Plan 已包含 DAG 和文件所有权 | approved | `process/DEVELOPMENT-PLAN.yaml` | DAG 无环，LLD 可并行分轮，开发仍受 CP5 门控。 |
| 四张 Story 卡片齐全 | approved | `process/stories/CR006-S01...S04*.md` | 均包含 dev_context、validation_context、acceptance_criteria、file_ownership、dev_gate。 |

## Checklist

| # | 检查项 | 审查结果 | 证据 | 审查意见 |
|---|---|---|---|---|
| 1 | 是否接受 CR006-BATCH-A 四 Story 拆解粒度 | approved | Story Backlog CR006-S01..S04 | 用户“全部接受”；四 Story 与 HLD §23.12 一致。 |
| 2 | 是否接受 S01 冻结 Tushare-first acquisition / raw-manifest 审计 / canonical-gold 产出契约 | approved | CR006-S01 Story | S01 不触碰 engine/experiments/docs/data/.env。 |
| 3 | 是否接受 S02 冻结 canonical/gold 到轻量 engine 适配契约 | approved | CR006-S02 Story | S02 不读取 raw/manifest，不默认 fallback repo `data/`。 |
| 4 | 是否接受 S03 冻结 Backtrader clean feed contract | approved | CR006-S03 Story | S03 不读取 raw/manifest/token，不导入 connector/runtime/storage。 |
| 5 | 是否接受 S04 固化旧 `data/` reference-only 护栏 | approved | CR006-S04 Story | S04 不读取、列出、迁移、复制、比对或删除旧 `data/**`。 |
| 6 | 是否接受 DAG 与开发依赖 | approved | `process/DEVELOPMENT-PLAN.yaml` | S01 -> S02 -> S03 -> S04；LLD 可提前并行起草，开发不得越过依赖和 CP5。 |
| 7 | 是否接受文件所有权和并行安全策略 | approved | Story 卡片 `file_ownership` | LLD 阶段只写各自 LLD/CP5；实现阶段按文件冲突和 dev_gate 控制。 |
| 8 | 是否接受 CP5 全量确认门控 | approved | Development Plan `lld_batch` | 四个 Story LLD 必须全量输出、全量 CP5 自动预检 PASS、统一人工确认后才可实现。 |
| 9 | 是否确认 CP4 不授权实现或真实数据操作 | approved | 本文件风险接受项 | 实现、旧数据操作、真实抓取、凭据读取均未授权。 |

## Exit Criteria

| 条目 | 审查结果 | 证据 | 审查意见 |
|---|---|---|---|
| Story 边界可作为 LLD 输入 | approved | Story Backlog / Story 卡片 | CR006-S01..S04 进入 `lld-ready`。 |
| DAG 与并行策略可用于 LLD 调度 | approved | Development Plan `CR006-BATCH-A` | `max_parallel_lld=3`，建议先并行 S01/S02/S03，S04 第二轮。 |
| 文件所有权冲突可控 | approved | Story 卡片 `file_ownership` | LLD 阶段不写业务文件；实现仍需 CP5 后重新判定。 |
| 实现仍被 CP5 阻断 | approved | Story `dev_gate` | CP5 全量人工确认前不得进入实现。 |

## Deliverables

| 交付物 | 路径 | 审查结果 | 审查意见 |
|---|---|---|---|
| Story Backlog | `process/STORY-BACKLOG.md` | approved | CR006-BATCH-A 四 Story 计划通过。 |
| Development Plan | `process/DEVELOPMENT-PLAN.yaml` | approved | DAG、Wave、LLD 批次和文件所有权通过。 |
| CR006-S01 Story | `process/stories/CR006-S01-tushare-first-data-acquisition-runbook.md` | approved | 可进入 LLD。 |
| CR006-S02 Story | `process/stories/CR006-S02-canonical-gold-lightweight-engine-adapter.md` | approved | 可进入 LLD。 |
| CR006-S03 Story | `process/stories/CR006-S03-backtrader-clean-feed-contract.md` | approved | 可进入 LLD。 |
| CR006-S04 Story | `process/stories/CR006-S04-old-data-reference-only-guardrail.md` | approved | 可进入 LLD；建议第二轮起草。 |
| CP4 自动预检 | `process/checks/CP4-CR006-STORY-PLAN-PRECHECK.md` | approved | PASS。 |

## 人工审查结果

- 结论：`approved`
- 审查人：user
- 审查时间：2026-05-18T22:33:23+08:00
- 修改意见：无。用户“全部接受”当前四 Story Tushare-first 计划，并要求能够并行时拉起子 agent 并行。
- 风险接受项：
  - CP4 只批准 CR006-BATCH-A 四 Story 计划、依赖 DAG、文件所有权、LLD 并行策略和后续 CP5 门控。
  - CP4 不授权实现；不得修改 `engine/**`、`experiments/**`、`config/**`、README、docs、tests、`market_data/**`、`delivery/**` 或真实数据。
  - CP4 不授权 Tushare 真实抓取、真实回补、normalize、validate、read 或写入真实数据湖。
  - CP4 不授权读取、列出、迁移、复制、比对或删除旧 `data/**`。
  - CP4 不授权读取、打印或记录 `.env`、Tushare token、NAS 用户名、密码或真实私有路径。
  - CR006-BATCH-A 的四个 Story LLD 必须全量输出、全量 CP5 自动预检 PASS、统一人工确认后才可实现。
