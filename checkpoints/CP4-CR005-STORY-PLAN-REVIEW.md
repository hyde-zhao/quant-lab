---
checkpoint_id: "CP4"
checkpoint_name: "CR-005 Story 拆解与并行安全门"
type: "auto_then_manual"
status: "approved"
owner: "meta-po"
created_at: "2026-05-17T19:02:35+08:00"
updated_at: "2026-05-17T19:13:17+08:00"
reviewed_by: "user"
reviewed_at: "2026-05-17T19:13:17+08:00"
auto_check_result: "process/checks/CP4-CR005-STORY-PLAN-PRECHECK.md"
supersedes:
  - "previous CP4 draft status=superseded-awaiting-revision after round3 hs300/Tushare review"
target:
  phase: "story-planning"
  story_id: ""
  artifacts:
    - "process/STORY-BACKLOG.md"
    - "process/DEVELOPMENT-PLAN.yaml"
    - "process/stories/CR005-S01-tushare-connector-real-lake-writer.md"
    - "process/stories/CR005-S02-tushare-dataset-schema-normalization.md"
    - "process/stories/CR005-S03-multidataset-quality-catalog-readers.md"
    - "process/stories/CR005-S04-hs300-local-benchmark.md"
    - "process/stories/CR005-S05-comparison-backfill-docs.md"
    - "process/stories/CR005-S06-backtrader-optional-backend.md"
---

# CP4 CR-005 Story 拆解与并行安全门

> 这是第三轮 hs300_index / Tushare 修订后的新 CP4 审查稿。旧 CP4 稿已被第三轮评审 superseded，本文件才是当前待确认对象。

## 自动预检摘要

| 预检文件 | 结论 | 阻断项 | 说明 |
|---|---|---|---|
| `process/checks/CP4-CR005-STORY-PLAN-PRECHECK.md` | PASS | 0 | CR005-S01..S06、CR5-W0..W5、DAG、文件所有权、S04/S06 dev_gate、proxy_baseline 边界和 QA post-revision 残留修正均已覆盖。 |

## Entry Criteria

| 条目 | 状态 | 证据 | 审查意见 |
|---|---|---|---|
| CP3 自动预检通过 | 待审查 | `process/checks/CP3-CR005-HLD-PRECHECK.md` | CP3 人工确认仍需用户同步确认。 |
| 第三轮 meta-se Story Plan 修订已完成并关闭 | 待审查 | `process/handoffs/META-SE-CR005-HS300-TUSHARE-DESIGN-REVISION-2026-05-17.md` |  |
| QA post-revision blocking 已修正 | 待审查 | `process/DEVELOPMENT-PLAN.yaml`；QA post-revision findings |  |
| 旧 CP4 稿已 superseded，新稿已生成 | 待审查 | 本文件；`process/checks/CP4-CR005-STORY-PLAN-PRECHECK.md` |  |

## Checklist

| # | 检查项 | 审查结果 | 证据 | 审查意见 |
|---|---|---|---|---|
| 1 | 是否接受 CR005-S01..S06 第三轮 Story 拆解和边界 | 待审查 | `process/STORY-BACKLOG.md` Story 列表 |  |
| 2 | 是否接受 CR-005 CP5 批次策略：A=CR005-S01/S02，B1=CR005-S03，B2=CR005-S04，C=CR005-S05，D=CR005-S06 | 待审查 | `process/DEVELOPMENT-PLAN.yaml` cr005_policy；HLD §22.13 |  |
| 3 | 是否接受 CR005-S01 拥有 `hs300_index` backfill job / `market_data/cli.py` 或等价 job 契约 | 待审查 | CR005-S01；Development Plan |  |
| 4 | 是否接受 CR005-S02 作为 hs300 schema、PIT 和复权契约前置 | 待审查 | CR005-S02 |  |
| 5 | 是否接受 CR005-S03 作为 hs300 quality/catalog/readers gate 前置 | 待审查 | CR005-S03 |  |
| 6 | 是否接受 CR005-S04 负责 `BenchmarkResult` typed schema、只读 resolver、remediation spec 和 proxy_baseline 边界 | 待审查 | CR005-S04 |  |
| 7 | 是否接受 CR005-S05 只负责 comparison / runbook / docs，不拥有 backfill job 主入口 | 待审查 | CR005-S05 |  |
| 8 | 是否接受 CR005-S06 Backtrader dev_gate：等待 S01/S02/S03/S04 契约稳定，benchmark missing 只报告对照缺失，不触发补数 | 待审查 | CR005-S06 |  |
| 9 | 是否接受 Development Plan 中 S04/S06 开发门控：hs300 backfill job、reader quality、BenchmarkResult schema、benchmark policy frozen 后才可开发 | 待审查 | `process/DEVELOPMENT-PLAN.yaml` CR005 policy / W3 / W5 |  |
| 10 | 是否接受 QA post-revision 的 CP5 REQUIRED 输入进入后续 LLD：fake backfill 后 resolver available、`next_action` 字段表一致性、Data Loader benchmark status 口径 | 待审查 | `process/checks/REVIEW-CR005-HS300-TUSHARE-META-QA-POST-REVISION.md` |  |
| 11 | 是否接受 `proxy_baseline` 残留修正：真实基准缺失只能 structured unavailable/required_missing，旧代理不能作为 hs300 fallback | 待审查 | `process/DEVELOPMENT-PLAN.yaml` CR4-W4；CR005-S04 |  |
| 12 | 是否接受 CP4 通过不授权实现，仍需每批 CP5 LLD 人工确认后才能开发 | 待审查 | 本文件；Story `dev_gate.cp5_required=true`；`process/STATE.md` |  |

## Exit Criteria

| 条目 | 审查结果 | 证据 | 审查意见 |
|---|---|---|---|
| Story Plan 可作为 CR-005 CP5 LLD 批次输入 | 待审查 | `process/STORY-BACKLOG.md`、`process/DEVELOPMENT-PLAN.yaml` |  |
| Story DAG 与文件所有权可接受 | 待审查 | `process/DEVELOPMENT-PLAN.yaml` |  |
| CR005-S01/S03/S04/S06 dev_gate 可接受 | 待审查 | CR005 Story 卡片 |  |
| CP5 前置约束明确 | 待审查 | CR005 Story 卡片、QA post-revision |  |

## Deliverables

| 交付物 | 路径 | 审查结果 | 审查意见 |
|---|---|---|---|
| Story Backlog | `process/STORY-BACKLOG.md` | 待审查 |  |
| Development Plan | `process/DEVELOPMENT-PLAN.yaml` | 待审查 |  |
| CR005 Story 卡片 | `process/stories/CR005-S01...S06*.md` | 待审查 |  |
| QA post-revision | `process/checks/REVIEW-CR005-HS300-TUSHARE-META-QA-POST-REVISION.md` | 待审查 |  |

## 人工审查结果

- 结论：`approved`
- 审查人：user
- 审查时间：2026-05-17T19:13:17+08:00
- 修改意见：
- 风险接受项：
  - 接受 CR-005 CP5 批次策略：A=CR005-S01/S02，B1=CR005-S03，B2=CR005-S04，C=CR005-S05，D=CR005-S06。
  - 接受 CR005-S04/S06 的开发门控：hs300 backfill job、reader quality、`BenchmarkResult` schema 和 benchmark policy frozen 后才可开发。
  - 接受 CP4 通过只代表 Story Plan 可进入 CP5 LLD 批次设计，不授权任何 Story 实现、依赖变更、真实数据写入或 token 使用。

## 允许回复格式

- `1` / `approve` / `通过`：确认通过，Story Plan 可进入 CR-005 CP5 LLD 批次设计，但仍不得实现代码。
- `2` / `修改: <具体修改点>`：需要修改，meta-po 将路由给对应子 agent 修订后重跑 CP3/CP4。
- `3` / `reject` / `不通过`：确认不通过，回退到 `story-planning` 或按影响范围回退到 `solution-design`。
