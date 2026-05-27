---
checkpoint_id: "CP5"
checkpoint_name: "CR-005 Batch B2/C / CR005-S04+S05 LLD 批次可实现性门"
type: "batch_auto_then_manual"
status: "approved"
owner: "codex-main-orchestrator"
created_at: "2026-05-17T23:03:42+08:00"
updated_at: "2026-05-17T23:10:12+08:00"
reviewed_by: "user"
reviewed_at: "2026-05-17T23:10:12+08:00"
auto_check_result:
  - "process/checks/CP5-CR005-S04-hs300-local-benchmark-LLD-IMPLEMENTABILITY.md"
  - "process/checks/CP5-CR005-S05-comparison-backfill-docs-LLD-IMPLEMENTABILITY.md"
target:
  phase: "story-execution"
  batch_id: "CR005-BATCH-B2C-S04-S05-LLD"
  story_id:
    - "CR005-S04"
    - "CR005-S05"
  artifacts:
    - "process/handoffs/META-DEV-CR005-S04-LLD-2026-05-17.md"
    - "process/handoffs/META-DEV-CR005-S05-LLD-2026-05-17.md"
    - "process/stories/CR005-S04-hs300-local-benchmark.md"
    - "process/stories/CR005-S05-comparison-backfill-docs.md"
    - "process/stories/CR005-S04-hs300-local-benchmark-LLD.md"
    - "process/stories/CR005-S05-comparison-backfill-docs-LLD.md"
    - "process/checks/CP5-CR005-S04-hs300-local-benchmark-LLD-IMPLEMENTABILITY.md"
    - "process/checks/CP5-CR005-S05-comparison-backfill-docs-LLD-IMPLEMENTABILITY.md"
---

# CP5 CR-005 Batch B2/C / CR005-S04+S05 LLD 批次可实现性人工审查

本文件是 `CR005-S04` 与 `CR005-S05` 并行 LLD 的人工审查稿。通过本检查点只代表两份 LLD 可作为后续实现输入；确认前不得实现 S04/S05，确认后也不得跳过 CP6/CP7，不授权进入 `CR005-S06`、Backtrader、真实联网或真实写 lake。

## 自动预检摘要

| Story | 预检文件 | 结论 | FAIL | OPEN | 说明 |
|---|---|---:|---:|---:|---|
| CR005-S04 | `process/checks/CP5-CR005-S04-hs300-local-benchmark-LLD-IMPLEMENTABILITY.md` | PASS | 0 | 3 | 覆盖 14 个可见章节、BenchmarkResult schema、BenchmarkPolicy、NextAction、RemediationJobSpec、resolver 流程、实验只读接入、no-network/no-write/no-proxy-hs300 边界。 |
| CR005-S05 | `process/checks/CP5-CR005-S05-comparison-backfill-docs-LLD-IMPLEMENTABILITY.md` | PASS | 0 | 4 | 覆盖 14 个可见章节、comparison 10 字段、显式 backfill runbook、required_missing 不自动补数、proxy_baseline、Backtrader optional 文档边界和默认离线验证。 |

## Entry Criteria

| 条目 | 状态 | 证据 | 审查意见 |
|---|---|---|---|
| CP3 HLD 架构评审已人工确认 | 待审查 | `checkpoints/CP3-CR005-HLD-REVIEW.md` status=`approved` |  |
| CP4 Story Plan 已人工确认 | 待审查 | `checkpoints/CP4-CR005-STORY-PLAN-REVIEW.md` status=`approved` |  |
| 上游 `CR005-S01/S03` 已 verified | 待审查 | `process/checks/CP7-CR005-S01-tushare-connector-real-lake-writer-VERIFICATION-DONE.md`；`process/checks/CP7-CR005-S03-multidataset-quality-catalog-readers-VERIFICATION-DONE.md` | S01/S03 均已 CP7 PASS。 |
| S04 LLD 已生成且未确认实现 | 待审查 | `process/stories/CR005-S04-hs300-local-benchmark-LLD.md` | frontmatter `confirmed=false`、`implementation_allowed=false`。 |
| S05 LLD 已生成且未确认实现 | 待审查 | `process/stories/CR005-S05-comparison-backfill-docs-LLD.md` | frontmatter `confirmed=false`、`implementation_allowed=false`。 |
| S04/S05 Story 级 CP5 自动预检 PASS | 待审查 | 两个 CP5 自动预检文件 | S04 `PASS` / S05 `PASS`，均无 FAIL。 |
| 真实子 agent 调度证据存在 | 待审查 | S04/S05 handoff | S04=`dev-zhang the 2nd`，agent_id=`019e3670-7311-7f02-ba42-83d0f5c93586`；S05=`dev-he the 2nd`，agent_id=`019e3670-7370-7690-a15d-5debb33342ad`。 |
| 未实现代码 | 待审查 | 两个子 agent 结果摘要 | 本轮只写 Story/LLD/CP5/handoff，未修改实现、测试、文档正文、依赖锁文件或真实数据路径。 |

## Checklist

| # | 检查项 | 审查结果 | 证据 | 审查意见 |
|---|---|---|---|---|
| 1 | 是否接受本批范围为 `CR005-S04` 与 `CR005-S05` 的 LLD/CP5，并行设计、不并行实现 | 待审查 | S04/S05 handoff；两个 CP5 自动预检 |  |
| 2 | 是否确认 S04 LLD 保持 14 个可见章节，且包含 `tier`、`shared_fragments`、`open_items` | 待审查 | S04 LLD §1-§14；frontmatter |  |
| 3 | 是否确认 S05 LLD 保持 14 个可见章节，且包含 `tier`、`shared_fragments`、`open_items` | 待审查 | S05 LLD §1-§14；frontmatter |  |
| 4 | 是否接受 S04 冻结 `BenchmarkResult` / `BenchmarkPolicy` / `NextAction` / `RemediationJobSpec` typed schema | 待审查 | S04 LLD §5、§6、§10 |  |
| 5 | 是否接受 S04 缺 `hs300_index` 时只返回 typed unavailable / required_missing，不自动联网、不自动 backfill、不静默代理 | 待审查 | S04 LLD §2、§7、§8、§10、§12 |  |
| 6 | 是否接受 S04 实验十/十二只读接入边界，旧 `--data-dir` 仅保留本地价格路径，代理只能命名为 `proxy_baseline` | 待审查 | S04 LLD §3、§7、§10、§13 |  |
| 7 | 是否接受 S05 comparison 只比较本地数据，不在 compare 阶段调用 Tushare / connector / runtime / 网络 | 待审查 | S05 LLD §2、§6、§7、§10 |  |
| 8 | 是否接受 S05 文档 runbook 只描述用户显式 backfill，`required_missing` 不自动联网、不自动写湖 | 待审查 | S05 LLD §2、§7、§8、§10 |  |
| 9 | 是否接受 S05 文档中 Backtrader 只作为 optional backend，不默认替代轻量主路径、不读 token/connector | 待审查 | S05 LLD §2、§9、§10、§14 |  |
| 10 | 是否接受 S04 的 3 个 OPEN 项作为后续门控风险，不阻断 LLD 审查 | 待审查 | 本文件 OPEN 项表 |  |
| 11 | 是否接受 S05 的 4 个 OPEN 项作为后续门控风险，不阻断 LLD 审查 | 待审查 | 本文件 OPEN 项表 |  |
| 12 | 是否确认本 CP5 通过后只允许分别计算 S04/S05 dev_gate，不授权 S06、Backtrader、真实联网或真实写 lake | 待审查 | 本文件；S04/S05 LLD frontmatter |  |

## OPEN 项与风险接受

| ID | Story | 风险 / 未决点 | CP5 人工确认时的接受口径 |
|---|---|---|---|
| O-S04-01 | S04 | CR5-Q2 benchmark 口径未确认。 | 接受 S04 冻结 `policy_unconfirmed` 行为；不阻断 schema / unavailable / required_missing 设计，但阻断 production `available` 口径声明。 |
| O-S04-02 | S04 | 是否需要修改 `market_data/readers.py` 取决于实现阶段现有 reader API 是否足够。 | 接受实现阶段优先在 `benchmarks.py` 适配；只有必要时才小范围修改 readers。 |
| O-S04-03 | S04 | S06 复用 `BenchmarkResult`。 | 接受 S06 必须等待 S04 CP5 批次确认和 schema 冻结后，才可计算 S06 dev_gate。 |
| O-S05-01 | S05 | S04 `BenchmarkResult` schema 与 benchmark available policy 仍在并行 LLD 中冻结；S05 不拥有 resolver 字段表。 | 接受 S05 文档实现前按 S04 CP5 确认后的字段表引用；若 S04 未确认，只写边界不写最终字段承诺。 |
| O-S05-02 | S05 | `README.md` / `docs/USER-MANUAL.md` 是 shared 文件，后续实现可能与其他文档补丁冲突。 | 接受 S05 实现前复核工作树，并按 meta-po 串行合并文档修改。 |
| O-S05-03 | S05 | Backtrader adapter 的具体命令、依赖安装和输出形态由 CR005-S06 拥有。 | 接受 S05 只描述 optional 边界，不写成 Backtrader 详细实现手册。 |
| O-S05-04 | S05 | 真实 Tushare 配额、字段和限频仍需用户在真实启用前确认。 | 接受 S05 只做离线文档/runbook，不默认执行联网验证。 |

## Exit Criteria

| 条目 | 审查结果 | 证据 | 审查意见 |
|---|---|---|---|
| Batch 内全部 LLD 已输出 | 待审查 | S04/S05 LLD |  |
| Batch 内 Story 级 CP5 自动预检均 PASS | 待审查 | S04/S05 CP5 自动预检 |  |
| OPEN 项已由用户接受或提出修改要求 | 待审查 | 本文件 OPEN 项表 |  |
| 实现边界清楚：确认前不得实现；确认后仍不得越权联网、写真实 lake 或推进 S06/Backtrader | 待审查 | 本文件；S04/S05 LLD |  |
| 若人工确认通过，可分别创建限定 S04/S05 的实现 handoff | 待审查 | `process/DEVELOPMENT-PLAN.yaml` parallel policy |  |

## Deliverables

| 交付物 | 路径 | 审查结果 | 审查意见 |
|---|---|---|---|
| S04 handoff 与调度证据 | `process/handoffs/META-DEV-CR005-S04-LLD-2026-05-17.md` | 待审查 |  |
| S05 handoff 与调度证据 | `process/handoffs/META-DEV-CR005-S05-LLD-2026-05-17.md` | 待审查 |  |
| S04 Story 卡片 | `process/stories/CR005-S04-hs300-local-benchmark.md` | 待审查 |  |
| S05 Story 卡片 | `process/stories/CR005-S05-comparison-backfill-docs.md` | 待审查 |  |
| S04 LLD | `process/stories/CR005-S04-hs300-local-benchmark-LLD.md` | 待审查 |  |
| S05 LLD | `process/stories/CR005-S05-comparison-backfill-docs-LLD.md` | 待审查 |  |
| S04 CP5 自动预检 | `process/checks/CP5-CR005-S04-hs300-local-benchmark-LLD-IMPLEMENTABILITY.md` | 待审查 |  |
| S05 CP5 自动预检 | `process/checks/CP5-CR005-S05-comparison-backfill-docs-LLD-IMPLEMENTABILITY.md` | 待审查 |  |

## 人工审查结果

- 结论：`approved`
- 审查人：user
- 审查时间：2026-05-17T23:10:12+08:00
- 修改意见：无
- 风险接受项：
  - O-S04-01：benchmark 口径未确认，S04 冻结 `policy_unconfirmed`，阻断 production available 口径声明。
  - O-S04-02：实现阶段优先在 `benchmarks.py` 适配，必要时才小范围改 readers。
  - O-S04-03：S06 等待 S04 schema 冻结后再计算 dev_gate。
  - O-S05-01：S05 文档引用 S04 CP5 确认后的字段表。
  - O-S05-02：S05 实现前复核 shared 文档文件并串行合并。
  - O-S05-03：S05 只描述 Backtrader optional 边界。
  - O-S05-04：真实联网启用前另行确认 Tushare 配额、字段和限频。

## 允许回复格式

请审查本文件后，在“人工审查结果”中填写结论，也可以直接回复以下任一整行：

- `1` / `approve` / `通过`：确认通过；后续可分别创建 S04/S05 实现 handoff。仍不得跳过 CP6/CP7。
- `2` / `修改: <具体修改点>`：需要修改；将路由给对应 meta-dev 修订 LLD / CP5 预检后重新发起本批审查。
- `3` / `reject` / `不通过`：确认不通过；回退到 S04/S05 LLD 设计，保持不得实现。
