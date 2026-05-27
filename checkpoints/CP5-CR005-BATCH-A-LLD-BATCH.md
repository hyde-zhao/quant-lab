---
checkpoint_id: "CP5"
checkpoint_name: "CR-005 Batch A LLD 批次可实现性门"
type: "batch_auto_then_manual"
status: "approved"
owner: "meta-po"
created_at: "2026-05-17T19:35:20+08:00"
updated_at: "2026-05-17T19:50:57+08:00"
reviewed_by: "user"
reviewed_at: "2026-05-17T19:50:57+08:00"
auto_check_result:
  - "process/checks/CP5-CR005-S01-tushare-connector-real-lake-writer-LLD-IMPLEMENTABILITY.md"
  - "process/checks/CP5-CR005-S02-tushare-dataset-schema-normalization-LLD-IMPLEMENTABILITY.md"
target:
  phase: "story-execution"
  batch_id: "CR005-BATCH-A"
  story_id:
    - "CR005-S01"
    - "CR005-S02"
  artifacts:
    - "process/handoffs/META-DEV-CR005-BATCH-A-LLD-2026-05-17.md"
    - "process/stories/CR005-S01-tushare-connector-real-lake-writer.md"
    - "process/stories/CR005-S01-tushare-connector-real-lake-writer-LLD.md"
    - "process/stories/CR005-S02-tushare-dataset-schema-normalization.md"
    - "process/stories/CR005-S02-tushare-dataset-schema-normalization-LLD.md"
    - "process/checks/CP5-CR005-S01-tushare-connector-real-lake-writer-LLD-IMPLEMENTABILITY.md"
    - "process/checks/CP5-CR005-S02-tushare-dataset-schema-normalization-LLD-IMPLEMENTABILITY.md"
---

# CP5 CR-005 Batch A LLD 批次可实现性人工审查

本文件是 CR-005 第一批 LLD 的统一人工审查稿。通过本检查点只代表 `CR005-S01` / `CR005-S02` 的 LLD 设计可作为实现输入；仍不得跳过后续 CP6 / CP7，也不得把本批批准扩展到 CR005-S03/S04/S05/S06 或 Backtrader 实现。

## 自动预检摘要

| 预检文件 | 结论 | 阻断项 | 说明 |
|---|---|---|---|
| `process/checks/CP5-CR005-S01-tushare-connector-real-lake-writer-LLD-IMPLEMENTABILITY.md` | PASS | 0 | S01 LLD 覆盖 Tushare 默认 disabled、import no-network、missing token / not allowlisted fail fast、`hs300_index` backfill job spec、dry-run 默认、manifest/idempotency/resume/partial success 和 token 不外泄。 |
| `process/checks/CP5-CR005-S02-tushare-dataset-schema-normalization-LLD-IMPLEMENTABILITY.md` | PASS | 0 | S02 LLD 覆盖多 dataset schema、`hs300_index` raw->canonical exact mapping、PIT 字段、`prices` + `adj_factor` 复权 normalization、typed status 和 S03/S04 交接要求。 |

## Entry Criteria

| 条目 | 状态 | 证据 | 审查意见 |
|---|---|---|---|
| CP3 HLD 架构评审已人工确认 | 待审查 | `checkpoints/CP3-CR005-HLD-REVIEW.md` status=`approved` |  |
| CP4 Story Plan 已人工确认 | 待审查 | `checkpoints/CP4-CR005-STORY-PLAN-REVIEW.md` status=`approved` |  |
| Batch A 范围符合已批准计划 | 待审查 | `process/DEVELOPMENT-PLAN.yaml`；`process/STATE.md` `parallel_execution.lld_design_batch` | 范围为 `CR005-S01` + `CR005-S02`。 |
| meta-dev 调度证据真实存在 | 待审查 | `process/handoffs/META-DEV-CR005-BATCH-A-LLD-2026-05-17.md` | 主线程回报 `spawn_agent`：agent_id=`019e35ab-7bca-7cf2-8f2f-2f763f501565`，nickname=`dev-yang`，completed then closed。 |
| 两个 LLD 均已生成且未确认 | 待审查 | `process/stories/CR005-S01-tushare-connector-real-lake-writer-LLD.md`；`process/stories/CR005-S02-tushare-dataset-schema-normalization-LLD.md` | frontmatter 均为 `confirmed=false`，`implementation_allowed=false`。 |
| 两个 Story 级 CP5 自动预检均 PASS | 待审查 | 两个 `process/checks/CP5-CR005-S0*-...-IMPLEMENTABILITY.md` | 无阻断 CP5 人工审查的 FAIL。 |

## Checklist

| # | 检查项 | 审查结果 | 证据 | 审查意见 |
|---|---|---|---|---|
| 1 | 是否接受 Batch A 范围：S01 冻结 Tushare 写湖 / hs300 backfill job；S02 冻结多 dataset schema / PIT / 复权 normalization | 待审查 | `process/stories/CR005-S01...LLD.md`；`process/stories/CR005-S02...LLD.md` |  |
| 2 | 是否接受 S01 的 Tushare 调用边界：仅 `market_data` 写湖 / 数据准备层可显式联网，consumer 不得调用 connector/runtime/storage | 待审查 | S01 LLD §2、§3、§4、§7、§9 |  |
| 3 | 是否接受 S01 的 `hs300_index` backfill job spec：dataset/source/interface/index_code/date range/lake root/run_id/resume/dry-run/raw/manifest/canonical/quality/catalog/gold/error enum | 待审查 | S01 LLD §5、§6、§10、§14 |  |
| 4 | 是否接受 S01 的凭据安全边界：token 只以 `TUSHARE_TOKEN` 环境变量名出现，不进入 manifest、日志、stdout/stderr、测试 fixture 或文档示例值 | 待审查 | S01 LLD §2、§5、§9、§10 |  |
| 5 | 是否接受 S02 的 `hs300_index` raw->canonical exact mapping、key、dedupe、sort、date parser、lineage 与 typed status | 待审查 | S02 LLD §5.1、§5.2、§5.3、§10 |  |
| 6 | 是否接受 S02 的 PIT as-of 契约：非行情数据以 `available_date` / `effective_date` / `available_at` 支撑后续 reader gate | 待审查 | S02 LLD §2、§5.5、§8、§10 |  |
| 7 | 是否接受 S02 的复权契约：数据层保存 `adj_factor`、`adjustment_policy` 和 adjusted OHLC，下游不重新选择复权口径 | 待审查 | S02 LLD §2、§5.4、§8、§10 |  |
| 8 | 是否接受 S03/S04 交接要求：`next_action` 字段表一致性和 fake backfill -> quality/catalog -> resolver available 集成测试作为后续 LLD 必检项 | 待审查 | S02 LLD §10、§12、§14；S02 CP5 预检 |  |
| 9 | 是否接受文件所有权和并行边界：S01/S02 可按批次确认，但开发时必须计算 `market_data/source_registry.py` 等 shared 文件合并顺序 | 待审查 | S01/S02 Story 卡片 `file_ownership`；两个 LLD §4、§11 |  |
| 10 | 是否确认两个 Story 级 CP5 自动预检均 PASS，且当前无阻断项 | 待审查 | 两个 CP5 自动预检结论 |  |
| 11 | 是否接受 7 个 OPEN 项作为风险接受 / 后续前置决策，而非阻断本批 LLD 审查 | 待审查 | 本文件“OPEN 项与风险接受” |  |
| 12 | 是否确认本 CP5 通过后也只允许进入 Batch A 的开发门控计算，不授权 S03/S04/S05/S06、Backtrader、真实网络测试或真实数据写入 | 待审查 | 本文件；`process/STATE.md` protected boundaries |  |

## OPEN 项与风险接受

| ID | 来源 | 风险 / 未决点 | CP5 人工确认时的接受口径 |
|---|---|---|---|
| O-S01-01 | S01 | Tushare 5000 档 exact 限频、积分消耗和可用字段未确认。 | 接受 S01 先冻结默认离线、dry-run、显式真实执行与保守串行边界；真实 provider 成功路径不得作为默认验收。 |
| O-S01-02 | S01 | 真实数据 lake root 与 `.gitignore` 策略未确认；用户已确认真实数据不归档到 GitHub，lake root 外置可配置，可使用 NAS 但不得硬编码 NAS。 | **已确认决策**：真实行情数据、Tushare 拉取结果、raw/canonical/gold/quality/catalog 等 lake 数据不得归档到 GitHub，也不得默认写入仓库内真实 `data/**`；真实 lake root 必须外置且可配置，优先通过显式 `--lake-root` 或环境变量 `MARKET_DATA_LAKE_ROOT` 指定；NAS 是推荐共享部署形态，例如 `/mnt/nas/quant_lake/local_backtest`，但实现不得硬编码 NAS；当前只依赖 POSIX path，本机外置目录也可用，S3/MinIO 仅保留未来扩展点；仓库只保留 schema、contract、文档、job spec 示例和小型脱敏 fixture；`.gitignore` 必须阻止仓库内误放 raw/canonical/gold/quality/lake artifacts、本地 env 文件入库，同时允许 `tests/fixtures/` 小型样本；未配置 lake root 时必须 fail fast / structured missing，不得静默写 `./data`。 |
| O-S01-03 | S01 | 是否把 `quota_or_rate_limited`、`remote_error`、`schema_mismatch`、`lake_root_invalid`、`resume_conflict` 升格进 `contracts.CONNECTOR_ERROR_TYPES`。 | 接受本批先在 job spec 层冻结枚举；实现前由 S01/S02 merge owner 决定是否升格全局常量。 |
| O-S02-01 | S02 | 真实 Tushare 字段、积分消耗、限频未确认。 | 接受 candidate exact mapping；真实字段差异必须通过 LLD 修改或 CR 处理，不得运行时猜测字段。 |
| O-S02-02 | S02 | `hs300_index` benchmark 采用价格指数、全收益指数或其他口径未确认。 | 接受 S02 保存 `benchmark_kind` / `policy_unconfirmed`；S04 available 路径必须等待 benchmark policy 冻结。 |
| O-S02-03 | S02 | `prices` adjusted price 主选 `daily + adj_factor` 还是 provider adjusted output 仍需确认。 | 接受 CP5 审查需明确默认主选；未确认时实现不得混用复权口径。 |
| O-S02-04 | S02 | `next_action` 机器字段表由 CR005-S04 拥有，S02 仅记录交接要求。 | 接受 S04 LLD 必须冻结 `next_action` 字段表，并把 fake backfill 后 resolver available 作为必检集成测试。 |

## Exit Criteria

| 条目 | 审查结果 | 证据 | 审查意见 |
|---|---|---|---|
| Batch A 内全部 LLD 已输出 | 待审查 | S01/S02 LLD 路径 |  |
| Batch A 内全部 Story 级 CP5 自动预检均 PASS | 待审查 | 两个 CP5 自动预检 |  |
| OPEN 项已由用户接受或提出修改要求 | 待审查 | 本文件 OPEN 项表 |  |
| 实现边界清楚：CP5 通过后仍不得越权写真实数据、联网默认测试或改非本批 Story | 待审查 | 本文件；S01/S02 LLD §4、§13、§14 |  |
| 若人工确认通过，meta-po 可将 S01/S02 LLD 标记为 approved/dev-ready 候选，并计算开发文件冲突与依赖门控 | 待审查 | `process/STATE.md` |  |

## 已确认设计输入

### O-S01-02：真实数据 lake root 与 Git 归档边界

用户已确认方向：

- 真实行情数据、Tushare 拉取结果、raw/canonical/gold/quality/catalog 等 lake 数据不得归档到 GitHub，也不得默认写入仓库内真实 `data/**`。
- 真实 lake root 必须外置且可配置，优先通过显式 `--lake-root` 或环境变量 `MARKET_DATA_LAKE_ROOT` 指定。
- NAS 是推荐共享部署形态，例如 `/mnt/nas/quant_lake/local_backtest`，但实现不得硬编码 NAS；当前只依赖 POSIX path，本机外置目录也可用，S3/MinIO 仅保留未来扩展点。
- 仓库只保留 schema、contract、文档、job spec 示例和小型脱敏 fixture。
- `.gitignore` 必须阻止仓库内误放 raw/canonical/gold/quality/lake artifacts、本地 env 文件入库，同时允许 `tests/fixtures/` 小型样本。
- 未配置 lake root 时必须 fail fast / structured missing，不得静默写 `./data`。

该决策已作为 O-S01-02 的 CP5 风险接受 / 设计输入。CP5 Batch A 可进入开发门控计算，但仍不得执行真实联网测试、写真实数据或提交 token；真实联网 / 真实数据写入只允许用户显式运行并提供 lake root。

## Deliverables

| 交付物 | 路径 | 审查结果 | 审查意见 |
|---|---|---|---|
| Batch A handoff 与调度证据 | `process/handoffs/META-DEV-CR005-BATCH-A-LLD-2026-05-17.md` | 待审查 |  |
| CR005-S01 LLD | `process/stories/CR005-S01-tushare-connector-real-lake-writer-LLD.md` | 待审查 |  |
| CR005-S02 LLD | `process/stories/CR005-S02-tushare-dataset-schema-normalization-LLD.md` | 待审查 |  |
| CR005-S01 CP5 自动预检 | `process/checks/CP5-CR005-S01-tushare-connector-real-lake-writer-LLD-IMPLEMENTABILITY.md` | 待审查 |  |
| CR005-S02 CP5 自动预检 | `process/checks/CP5-CR005-S02-tushare-dataset-schema-normalization-LLD-IMPLEMENTABILITY.md` | 待审查 |  |
| DEV-LOG 摘要 | `DEV-LOG.md` | 待审查 |  |
| STATE 门控记录 | `process/STATE.md` | 待审查 |  |

## 人工审查结果

- 结论：`approved`
- 审查人：user
- 审查时间：2026-05-17T19:50:57+08:00
- 修改意见：
  - 用户确认 O-S01-02：真实 lake root 外置可配置；真实数据不得归档 GitHub；优先 `--lake-root` 或 `MARKET_DATA_LAKE_ROOT`；NAS 可作为推荐共享部署但不得硬编码；当前只依赖 POSIX path，S3/MinIO 仅未来扩展；`.gitignore` 阻止 repo 内误放 lake artifacts / 本地 env 文件，同时允许 `tests/fixtures/` 小型样本；未配置 lake root 必须 fail fast / structured missing，不得静默写 `./data`。
- 风险接受项：
  - 接受 O-S01-01：Tushare 5000 档限频、积分消耗和可用字段未确认；Batch A 实现必须默认离线、dry-run、显式真实执行，真实 provider 成功路径不得作为默认验收。
  - 接受 O-S01-02 已确认 lake root / `.gitignore` 决策，作为 Batch A 实现硬约束。
  - 接受 O-S01-03：error enum 可先在 job spec 层冻结；是否升格 `contracts.CONNECTOR_ERROR_TYPES` 由 Batch A 实现按共享文件合并顺序处理。
  - 接受 O-S02-01：真实 Tushare 字段、积分消耗、限频未确认；真实字段差异不得运行时猜测，必须通过 LLD 修改或 CR 处理。
  - 接受 O-S02-02：`hs300_index` benchmark 口径未最终确认；S04 available 路径必须等待 benchmark policy 冻结。
  - 接受 O-S02-03：Batch A 实现主选 `daily + adj_factor` 生成 adjusted price；若改用 provider adjusted output，必须补一致性校验并回到设计确认。
  - 接受 O-S02-04：`next_action` 机器字段表由 CR005-S04 冻结，S02 只交接 target_dataset/source/interface/date range。

## 允许回复格式

请审查本文件后，在“人工审查结果”中填写结论，也可以直接回复以下任一整行：

- `1` / `approve` / `通过`：确认通过；meta-po 将回填 CP5 Batch A 为 approved，并计算 `CR005-S01` / `CR005-S02` 是否进入 `dev-ready` 候选。仍不得跳过 CP6/CP7。
- `2` / `修改: <具体修改点>`：需要修改；meta-po 将路由给 meta-dev 修订 LLD / CP5 预检后重新发起本批审查。
- `3` / `reject` / `不通过`：确认不通过；回退到 Batch A LLD 设计，保持不得实现。
