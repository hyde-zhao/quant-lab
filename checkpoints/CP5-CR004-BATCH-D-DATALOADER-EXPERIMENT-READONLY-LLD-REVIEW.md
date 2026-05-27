---
checkpoint_id: "CP5"
checkpoint_name: "CR-004 Batch D Data Loader 与实验只读接入 LLD 确认门"
type: "rolling_auto_then_manual"
status: "approved"
owner: "meta-po"
created_at: "2026-05-17T15:44:22+08:00"
reviewed_by: "user"
reviewed_at: "2026-05-17T15:53:20+08:00"
auto_check_result: "process/checks/CP5-CR004-BATCH-D-DATALOADER-EXPERIMENT-READONLY-LLD-PRECHECK.md"
target:
  phase: "story-execution"
  batch_id: "CR004-BATCH-D"
  artifacts:
    - "process/stories/STORY-003-parquet-quality-report-LLD.md"
    - "process/stories/STORY-004-offline-data-loader-contract-validator-LLD.md"
    - "process/stories/STORY-018-cr004-experiment-readonly-benchmark-LLD.md"
---

# CP5 CR-004 Batch D Data Loader 与实验只读接入 LLD 人工审查

## 自动预检摘要

| 预检文件 | 结论 | 阻断项 | 说明 |
|---|---|---|---|
| `process/checks/CP5-CR004-BATCH-D-DATALOADER-EXPERIMENT-READONLY-LLD-PRECHECK.md` | PASS | 0 | Batch D 三份 LLD 自动预检时均保持 `confirmed=false`、`implementation_allowed=false`；用户回复“通过”后已回填确认状态。 |

## Entry Criteria

| 条目 | 状态 | 证据 | 审查意见 |
|---|---|---|---|
| STORY-016 verified | 通过 | `process/checks/CP7-STORY-016-cr004-canonical-validation-readers-VERIFICATION-DONE.md` | 用户回复“通过”。 |
| STORY-017 verified | 通过 | `process/checks/CP7-STORY-017-cr004-cli-offline-comparison-VERIFICATION-DONE.md` | 用户回复“通过”。 |
| Data Loader 边界已由用户澄清 | 通过 | 本轮对话；`process/constraints/CR004-QUALITY-DATALOADER-CONFIRMATION-CONSTRAINTS-2026-05-17.md` | 用户回复“通过”。 |
| STORY-003 LLD 修订完成 | 通过 | `process/stories/STORY-003-parquet-quality-report-LLD.md` | 用户回复“通过”。 |
| STORY-004 LLD 修订完成 | 通过 | `process/stories/STORY-004-offline-data-loader-contract-validator-LLD.md` | 用户回复“通过”。 |
| STORY-018 LLD 新建完成 | 通过 | `process/stories/STORY-018-cr004-experiment-readonly-benchmark-LLD.md` | 用户回复“通过”。 |
| 实现尚未开始 | 通过 | 三份 LLD frontmatter；自动预检 | CP5 通过后才允许后续按限定范围实现。 |

## Checklist

| # | 检查项 | 审查结果 | 证据 | 审查意见 |
|---|---|---|---|---|
| 1 | 是否接受本批只包含 STORY-003/004/018，不重开 STORY-016/017 | 通过 | 自动预检；meta-se 结论 | 用户回复“通过”。 |
| 2 | 是否接受 STORY-003 legacy quality 只有字段完整对齐 CR-004 时才可作为新验收事实源 | 通过 | STORY-003 LLD §1、§2、§8、§10、§13 | 用户回复“通过”。 |
| 3 | 是否接受 Data Loader 不是抓取组件，只做加载/校验/拒绝或放行 | 通过 | STORY-004 LLD §1、§2、§7、§8 | 用户回复“通过”。 |
| 4 | 是否接受 Data Loader 不联网、不调用 connector/runtime/data_prep、不自动补数或生成质量报告 | 通过 | STORY-004 LLD §2、§4、§8、§9、§10 | 用户回复“通过”。 |
| 5 | 是否接受质量报告机器入口仅 CSV 或显式内存 summary fallback，Markdown human-only | 通过 | STORY-003/004 LLD；约束文件 | 用户回复“通过”。 |
| 6 | 是否接受 `dataset_status=fail` / `quality_status=fail` 永不放行，`allow_warn` 只放宽 warn | 通过 | STORY-004 LLD §6、§7、§8、§10 | 用户回复“通过”。 |
| 7 | 是否接受 quality CSV 缺 coverage、thresholds、denominator、双状态或可复现字段时主路径 fail fast | 通过 | STORY-004 LLD §8；CR004 约束 G-01..G-04 | 用户回复“通过”。 |
| 8 | 是否接受 PIT 不完整拒绝、non-PIT 可 warn 但必须披露幸存者偏差 | 通过 | STORY-004 LLD §5、§7、§8、§10 | 用户回复“通过”。 |
| 9 | 是否接受 STORY-018 只做实验十/十二显式只读接入和 benchmark resolver，不抓取真实沪深 300 | 通过 | STORY-018 LLD §1、§2、§4、§7 | 用户回复“通过”。 |
| 10 | 是否接受缺真实沪深 300 基准时结构化 `unavailable` / `required_missing`，不静默代理 | 通过 | STORY-018 LLD §5、§7、§8、§10 | 用户回复“通过”。 |
| 11 | 是否接受旧 `--data-dir` 默认行为保留，新 `--market-data-root` 显式 opt-in | 通过 | STORY-018 LLD §2、§6、§8、§10 | 用户回复“通过”。 |
| 12 | 是否接受 STORY-018 文件范围包含 `market_data/benchmarks.py`、两个实验脚本和专用测试，不修改 `engine/**` | 通过 | STORY-018 LLD §4、§11、§13 | 用户回复“通过”。 |
| 13 | 是否接受 CP5 通过前不得实现、不得真实抓取数据、不得写真实 `data/**` / `reports/**` / `delivery/**` | 通过 | 三份 LLD frontmatter 和 §14 | 用户回复“通过”。 |

## Exit Criteria

| 条目 | 审查结果 | 证据 | 审查意见 |
|---|---|---|---|
| Batch D LLD 可作为后续实现输入 | 通过 | 三份 LLD | 用户回复“通过”。 |
| 实现边界清晰且互不冲突 | 通过 | STORY-003/004/018 LLD §4、§11 | 用户回复“通过”。 |
| 质量门、只读边界、真实数据后置边界均明确 | 通过 | 自动预检 Checklist | 用户回复“通过”。 |

## Deliverables

| 交付物 | 路径 | 审查结果 | 审查意见 |
|---|---|---|---|
| STORY-003 LLD 修订 | `process/stories/STORY-003-parquet-quality-report-LLD.md` | 通过 | 用户回复“通过”。 |
| STORY-004 LLD 修订 | `process/stories/STORY-004-offline-data-loader-contract-validator-LLD.md` | 通过 | 用户回复“通过”。 |
| STORY-018 LLD 新建 | `process/stories/STORY-018-cr004-experiment-readonly-benchmark-LLD.md` | 通过 | 用户回复“通过”。 |
| CP5 自动预检 | `process/checks/CP5-CR004-BATCH-D-DATALOADER-EXPERIMENT-READONLY-LLD-PRECHECK.md` | 通过 | 用户回复“通过”。 |

## 人工审查结果

- 结论：`approved`
- 审查人：user
- 审查时间：2026-05-17T15:53:20+08:00
- 修改意见：无。
- 风险接受项：本批确认的是 Data Loader / 实验只读 / 基准 unavailable 的 LLD 边界；允许后续按三份 LLD 的限定范围分 Story 进入实现；不代表真实沪深 300 数据已抓取，不代表实验十/十二已接入真实数据，不授权真实联网或写真实 `data/**`、`reports/**`、`delivery/**`。

## 可直接回复

请回复以下任一格式：

- `1` / `approve` / `通过`：批准 CP5 Batch D，允许后续按 LLD 分 Story 进入实现。
- `2 修改: <具体修改点>`：要求修改后重新提交 CP5。
- `3` / `reject` / `不通过`：拒绝本次 Batch D LLD。
