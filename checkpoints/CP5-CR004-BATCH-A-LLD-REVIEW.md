---
checkpoint_id: "CP5"
checkpoint_name: "CR-004 批次 A Story LLD 确认门"
type: "rolling_auto_then_manual"
status: "approved"
owner: "meta-po"
created_at: "2026-05-17T13:00:54+08:00"
reviewed_by: "user"
reviewed_at: "2026-05-17T13:04:25+08:00"
auto_check_result: "process/checks/CP5-CR004-BATCH-A-LLD-PRECHECK.md"
target:
  phase: "story-execution"
  story_id: "STORY-014,STORY-015"
  artifacts:
    - "process/stories/STORY-014-cr004-market-data-package-lake-contracts-LLD.md"
    - "process/stories/STORY-015-cr004-connector-runtime-raw-manifest-LLD.md"
---

# CP5 CR-004 批次 A Story LLD 确认门 人工审查

## 自动预检摘要

| 预检文件 | 结论 | 阻断项 | 说明 |
|---|---|---|---|
| `process/checks/CP5-CR004-BATCH-A-LLD-PRECHECK.md` | PASS | 0 | STORY-014 与 STORY-015 LLD 已更新到 `lld_version=1.1`，meta-se/meta-qa 复核 findings 已修订回 LLD。 |

## Entry Criteria

| 条目 | 状态 | 证据 | 审查意见 |
|---|---|---|---|
| CP3 已确认 | 待审查 | `checkpoints/CP3-CR004-HLD-REVIEW.md` |  |
| CP4 已确认 | 待审查 | `checkpoints/CP4-CR004-STORY-PLAN-REVIEW.md` |  |
| 批次 A LLD 已完成 | 待审查 | `process/stories/STORY-014...-LLD.md`; `process/stories/STORY-015...-LLD.md` |  |
| 实现尚未开始 | 待审查 | `process/STATE.md`; meta-dev 汇报 |  |
| meta-se / meta-qa 复核已完成 | 待审查 | `process/reviews/CR004-BATCH-A-SE-FINDINGS-2026-05-17.md`; `process/reviews/CR004-BATCH-A-QA-FINDINGS-2026-05-17.md` |  |
| revise findings 已处理 | 待审查 | 两个 LLD 修订记录 1.1；`process/checks/CP5-CR004-BATCH-A-LLD-PRECHECK.md` |  |

## Checklist

| # | 检查项 | 审查结果 | 证据 | 审查意见 |
|---|---|---|---|---|
| 1 | 是否接受 STORY-014 的 `market_data` 包骨架、schema/source registry/lake layout 作为下游冻结契约 | 待审查 | `process/stories/STORY-014-cr004-market-data-package-lake-contracts-LLD.md` §3-§8 |  |
| 2 | 是否接受 STORY-014 不新增依赖、不修改 `pyproject.toml` / `uv.lock` 的实施口径 | 待审查 | STORY-014 LLD §2、§4、§11 |  |
| 3 | 是否接受 STORY-014 的 fake 默认启用、真实源 disabled/unresolved 的 source registry 设计 | 待审查 | STORY-014 LLD §5、§6 |  |
| 4 | 是否接受 STORY-015 依赖 STORY-014 契约，且共享契约变更必须回到 LLD/CP5 修改 | 待审查 | STORY-015 LLD frontmatter、§3、§4 |  |
| 5 | 是否接受 STORY-015 的 connector protocol、fake connector、真实 adapter fail-fast 设计 | 待审查 | STORY-015 LLD §3、§5、§6 |  |
| 6 | 是否接受 STORY-015 的 runtime throttle/retry/circuit breaker、clock/sleeper/jitter 注入设计 | 待审查 | STORY-015 LLD §5、§7、§8 |  |
| 7 | 是否接受 STORY-015 的 raw JSONL + manifest JSONL 持久化设计足以支撑 STORY-016 | 待审查 | STORY-015 LLD §5、§7 |  |
| 8 | 是否接受默认无真实网络、无凭据落盘、真实 adapter 不进入默认测试路径 | 待审查 | 两个 LLD §9；`process/TEST-STRATEGY.md` CR-004 增量 |  |
| 9 | 是否接受开放问题不阻塞 fake/offline 最小闭环，但阻塞真实 source 默认启用 | 待审查 | 两个 LLD §12 |  |
| 10 | 是否授权 CP5 通过后由 `meta-dev` 先实现 STORY-014，再实现 STORY-015 | 待审查 | `process/DEVELOPMENT-PLAN.yaml` CR4-W0/W1；本审查稿 |  |
| 11 | 是否接受 STORY-015 的 resume / 断点续跑协议作为稳定拉取的基础设计 | 待审查 | STORY-015 LLD §5.2、§8、§10 |  |
| 12 | 是否接受 `run_id/source_run_id` 在 request、raw、manifest、canonical 之间的血缘闭环 | 待审查 | STORY-014 LLD §5；STORY-015 LLD §5、§8、§10 |  |
| 13 | 是否接受 `source_unresolved` 作为 TickFlow exact API 未确认时的可诊断错误类型 | 待审查 | STORY-014 LLD §5、§8；STORY-015 LLD §8 |  |
| 14 | 是否接受 fake `available_at` / `adjustment_policy` 的 deterministic 来源规则 | 待审查 | STORY-015 LLD §5、§7、§10 |  |
| 15 | 是否接受 raw `.tmp` 原子 rename、checksum/row_count、manifest append 失败时 `orphan_raw` 补偿策略 | 待审查 | STORY-014 LLD §5；STORY-015 LLD §5、§8、§10 |  |
| 16 | 是否接受 Batch A 只冻结 `prices` + raw/manifest 基础契约，`index_members`、`trade_calendar`、quality gate、多源比对延期到 STORY-016/017 | 待审查 | 两个 LLD §2、§5、§14 |  |
| 17 | 是否接受 CP6 前必须执行缓存禁入库扫描，保证组件可移植交付面干净 | 待审查 | 两个 LLD §9、§10、§14 |  |

## Exit Criteria

| 条目 | 审查结果 | 证据 | 审查意见 |
|---|---|---|---|
| STORY-014 LLD 可作为实现输入 | 待审查 | STORY-014 LLD |  |
| STORY-015 LLD 可作为实现输入 | 待审查 | STORY-015 LLD |  |
| CP5 通过后实现范围清晰 | 待审查 | 两个 LLD §4、§11、§13 |  |
| 评审关注项已进入实现约束 | 待审查 | CP5 自动预检 Checklist #11-#18 |  |

## Deliverables

| 交付物 | 路径 | 审查结果 | 审查意见 |
|---|---|---|---|
| STORY-014 LLD | `process/stories/STORY-014-cr004-market-data-package-lake-contracts-LLD.md` | 待审查 | 当前版本 `1.1`。 |
| STORY-015 LLD | `process/stories/STORY-015-cr004-connector-runtime-raw-manifest-LLD.md` | 待审查 | 当前版本 `1.1`。 |
| CP5 自动预检 | `process/checks/CP5-CR004-BATCH-A-LLD-PRECHECK.md` | 待审查 |  |
| meta-se 复核 findings | `process/reviews/CR004-BATCH-A-SE-FINDINGS-2026-05-17.md` | 待审查 | required findings 已修订回 LLD。 |
| meta-qa 复核 findings | `process/reviews/CR004-BATCH-A-QA-FINDINGS-2026-05-17.md` | 待审查 | required findings 已修订回 LLD。 |
| 补充确认约束 | `process/constraints/CR004-QUALITY-DATALOADER-CONFIRMATION-CONSTRAINTS-2026-05-17.md` | 待审查 | 用户带约束通过的质量报告、Data Loader、文件边界和质量门禁协议。 |

## 人工审查结果

- 结论：`approved-with-constraints`
- 审查人：user
- 审查时间：2026-05-17T13:04:25+08:00
- 修改意见：接受 CP5 批次 A，但后续执行必须遵守 `process/constraints/CR004-QUALITY-DATALOADER-CONFIRMATION-CONSTRAINTS-2026-05-17.md`。质量报告第一版以 CSV 为 canonical source，Markdown 仅为人类渲染；raw 到 dataset 只允许显式 `target_dataset` 或 exact interface 映射；质量报告必须披露 denominator、fetch/dataset 双状态、non-PIT 风险、coverage、显式阈值和可复现字段；Data Loader 不得自动修复数据，不得放行 fail，返回对象必须携带质量决策原因；`engine/contracts.py` 只追加纯常量；确认后实现范围不得越过各 Story LLD 文件边界。
- 风险接受项：第一版接受 non-PIT 股票池策略，但必须设置并披露 `is_pit_universe=false`、`universe_mode`、`pit_status` 和 survivorship bias 风险。

## 可直接回复

请回复以下任一格式：

- `1` / `approve` / `通过`：批准 CP5 批次 A，允许 `meta-dev` 实现 STORY-014 和 STORY-015。
- `2 修改: <具体修改点>`：要求修改后重新提交 CP5。
- `3` / `reject` / `不通过`：拒绝本次批次 A LLD。
