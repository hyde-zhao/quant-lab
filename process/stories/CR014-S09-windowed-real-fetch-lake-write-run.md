---
story_id: "CR014-S09-windowed-real-fetch-lake-write-run"
title: "分时段真实抓取与 raw/manifest 写湖执行"
story_slug: "windowed-real-fetch-lake-write-run"
status: "full-history-2015-2026-ytd-prices-adj-factor-candidate-usable-non-pit-warn"
priority: "P0"
wave: "CR014-W5-REAL-RUN"
depends_on:
  - "CR014-S01-a-share-universe-lifecycle-contract"
  - "CR014-S02-parquet-layout-manifest-catalog-publish-gate"
  - "CR014-S03-p0-plan-run-normalize-validate-publish-contract"
  - "CR014-S04-duckdb-readonly-query-audit-parity-boundary"
  - "CR014-S05-full-history-readiness-gap-claim-boundary"
  - "CR014-S06-incremental-refresh-replay-retention-contract"
  - "CR014-S07-research-consumer-readonly-docs-runbook-boundary"
  - "CR014-S08-w3-minute-tick-level2-vwap-blocked-decision-boundary"
cp5_batch: "CR014-REAL-RUN-BATCH-B"
implementation_allowed: true
real_run_authorization_status: "authorized-and-executed-2015-2026-ytd"
cp5_auto_precheck: "process/checks/CP5-CR014-S09-windowed-real-fetch-lake-write-run-LLD-IMPLEMENTABILITY.md"
created_at: "2026-05-27"
updated_at: "2026-05-29T00:27:18+08:00"
cp6_auto_check: "process/checks/CP6-CR014-S09-windowed-real-fetch-lake-write-run-CODING-DONE.md"
cp6_status: "PASS"
cp7_auto_check: "process/checks/CP7-CR014-S09-windowed-real-fetch-lake-write-run-VERIFICATION-DONE.md"
cp7_status: "PASS"
contract_verified: true
real_run_smoke_check: "process/checks/REAL-TUSHARE-CR014-S09-YTD-CONFIG-LAKE-VERIFY-2026-05-28.md"
real_run_smoke_status: "PASS_PARTIAL_SCOPE"
real_run_full_history_check: "process/checks/REAL-TUSHARE-CR014-S14-FULL-HISTORY-PRICES-ADJ-FACTOR-PULL-2026-05-29.md"
real_run_full_history_status: "PASS_FULL_HISTORY_PRICES_ADJ_FACTOR_CANDIDATE_PULLED_PUBLISH_BLOCKED"
verified: false
change_id: "CR-014"
---

# CR014-S09：分时段真实抓取与 raw/manifest 写湖执行

## Story 摘要

在 CR014-S01..S08 的合同、事实源、run gate、publish gate、readiness/claim boundary、replay/retention 和研究消费边界全部完成后，单独执行真实 provider 抓取与 raw / manifest / run metadata 写湖。该 Story 不属于当前 `CR014-FULL-HISTORY-LAKE-BATCH-A` 的 CP5 审查范围，必须进入独立的 `CR014-REAL-RUN-BATCH-B` LLD、CP5 和用户显式运行授权。

## dev_context

**输入依据**：用户要求“把真实的抓取和写湖拆分一个任务或者 Story，在前面的 Story 都完成后，进行分时段的数据抓取和写湖”；`process/HLD-DATA-LAKE.md` §17；ADR-048、ADR-050、ADR-051、ADR-052；CR014-S01..S08 LLD。

**未来实现候选文件**：`market_data/cli.py`、`market_data/runtime.py`、`market_data/windowed_run.py`、`market_data/manifest.py`、`market_data/lake_layout.py`、`tests/test_cr014_windowed_real_run_contract.py`。

**开发合同**：

| 对象 | 合同 |
|---|---|
| 前置 Story | CR014-S01..S08 均必须 `verified`，且各自 CP6 / CP7 PASS |
| 独立门控 | 必须有 S09 LLD、S09 CP5 自动预检 PASS、S09 CP5 人工确认 approved |
| 运行授权 | 每次真实 run 必须有 `authorization_id`、dataset、date range、window policy、source/interface allowlist、lake root、resume policy、rollback policy |
| 分时段策略 | 按 dataset 的 `coverage_start..as_of_trade_date` 切成窗口；窗口粒度由 dataset policy 决定，默认支持 year / quarter / month / trading-day chunk |
| 写入范围 | 只允许写 raw、manifest、run metadata 和 run-scoped audit；不得自动 normalize、不得自动 publish current pointer |
| 失败恢复 | 每个窗口独立 run_id、manifest、checksum、resume token；失败窗口不得污染已成功窗口 |

## validation_context

**验证方式**：S09 LLD 前只做静态计划登记；S09 实现后先用 fixture / tmp_path / fake provider 验证窗口拆分、resume、manifest 和禁止 publish，再由用户单独授权真实 smoke。

**关键验证场景**：

| 场景 | 期望 |
|---|---|
| 无 authorization_id 执行真实 run | fail-closed，provider_fetch=0、lake_write=0、credential_read=0 |
| 分时段 plan | 输出窗口列表、dataset、date range、source/interface、expected partitions 和 resume token |
| 单窗口成功 | 写 raw、manifest、run metadata；current_pointer_changes=0 |
| 单窗口失败 | 记录 failed window，不覆盖成功窗口，不触发 publish |
| 全窗口完成 | 输出 run summary 和 candidate readiness input，不自动 publish |

## acceptance_criteria

| ID | 标准 | 验收方式 |
|---|---|---|
| AC-01 | S09 不得在 CR014-S01..S08 全部 verified 前进入实现 | dev_gate 检查 |
| AC-02 | S09 必须有独立 LLD、CP5 自动预检和 CP5 人工确认 | checkpoint 检查 |
| AC-03 | 每次真实 run 必须绑定 authorization_id、dataset、date range、window policy、source/interface allowlist 和 lake root | run gate 测试 |
| AC-04 | 分时段窗口 100% 可追溯到 manifest / run metadata | manifest contract test |
| AC-05 | raw/manifest 写湖完成后 current_pointer_changes=0，publish 仍需独立授权 | publish gate 测试 |
| AC-06 | 真实 provider / lake / credential 操作不得读取、覆盖或迁移旧 `data/**` 和旧 reports | forbidden operation scan |

## 依赖与文件影响范围

| 类型 | 内容 |
|---|---|
| 上游依赖 | CR014-S01、S02、S03、S04、S05、S06、S07、S08 全部 verified |
| 下游依赖 | 后续 normalize/validate/publish 运行批次；不在本 Story 自动触发 |
| 主所有权 | `market_data/windowed_run.py`、S03 已确认的 run gate 入口、run-scoped manifest 写入 |
| 共享文件 | `market_data/runtime.py`、`market_data/manifest.py`、`market_data/lake_layout.py`、`market_data/cli.py` |
| 禁止范围 | 未授权 provider fetch、未授权 lake write、未授权 credential read、旧 `data/**` 操作、旧 reports 覆盖、catalog current pointer 更新、retention execute |

## LLD 输入

- CR014-S01..S08 的已确认 LLD 和 CP7 结果。
- 用户对 S09 的独立 CP5 决策。
- 用户对每次真实 run 的 `authorization_id` 和 dataset/date/window/source/lake 范围授权。
- 当前 S09 CP5 自动预检只检查 LLD 设计可实现性，不批准 S09 实现或真实执行。

## S09 CP5 决策选项

用户最新提出的“2026 年第一天至今的数据测试”必须作为 S09 CP5 人工确认的运行窗口选项处理，不视为已经授权执行。当前日期为 2026-05-27，按“最近已闭市交易日”口径，本次默认窗口更新为 `2026-01-01..2026-05-26`。真实 provider fetch 与 raw / manifest / run metadata 写湖只有在 S09 CP5 approved，且每次 run 的授权字段完整后才允许执行。

| 选项 | 日期窗口 | 定位 | 说明 |
|---|---|---|---|
| 推荐 | `2026-01-01..2026-05-26` | 2026 年初至最近已闭市交易日 pilot | `2026-05-27` 在本次调度时不是已完成交易日，因此默认截至 `2026-05-26` |
| 备选 A | `2025-05-27..2026-05-26` | 最近完整一年 pilot | 覆盖更长的近一年窗口，但真实副作用和 provider 调用范围更大 |
| 备选 B | `2026-04-27..2026-05-26` | 一月 smoke | 用于先验证 provider/schema/lake 写入路径，副作用窗口最小 |

## Per-run 授权字段

以下字段必须在 S09 CP5 approved 后、每次真实 run 前由用户或授权记录明确给出；缺任一字段时真实执行 fail-closed，`provider_fetch=0`、`lake_write=0`、`credential_read=0`。

| 字段 | 要求 | 当前状态 |
|---|---|---|
| `authorization_id` | 每次真实 run 的唯一授权 ID | 待 S09 CP5 / per-run 授权 |
| `dataset` | dataset 清单，必须 exact | 待 S09 CP5 / per-run 授权 |
| `date range` | 起止日期，必须落在 S09 CP5 选项或用户显式修改范围内 | 待 S09 CP5 / per-run 授权 |
| `source/interface allowlist` | provider 与接口白名单，必须 exact | 待 S09 CP5 / per-run 授权 |
| `lake root` | 写湖根目录，必须显式给出且通过路径护栏 | 待 S09 CP5 / per-run 授权 |
| `window policy` | year / quarter / month / trading-day chunk 及窗口大小 | 待 S09 CP5 / per-run 授权 |
| `resume policy` | failed window 的 retry / skip / resume_conflict 策略 | 待 S09 CP5 / per-run 授权 |
| `rollback policy` | 已写 raw / manifest / metadata 的回滚或隔离策略 | 待 S09 CP5 / per-run 授权 |
| `credential source policy` | 凭据来源、读取时机、脱敏日志规则；禁止读取 `.env` 内容进入文档 | 待 S09 CP5 / per-run 授权 |

## AI 可执行任务清单

以下任务只在 S09 LLD confirmed、S09 CP5 approved、Story `implementation_allowed=true` 且 per-run 授权字段完整后可执行；当前只作为后续实现拆分输入。

| TASK-ID | 目标文件 | 动作 | 门控 |
|---|---|---|---|
| TASK-S09-01 | `market_data/windowed_run.py` | 创建窗口计划、授权对象、resume token 与失败窗口模型 | S09 CP5 approved 后才可实现 |
| TASK-S09-02 | `market_data/runtime.py` | 修改真实 run gate，加入 S09 per-run 授权校验与 fail-closed counters | S09 CP5 approved 后才可实现 |
| TASK-S09-03 | `market_data/manifest.py` | 修改 raw manifest / run metadata 写入合同，记录 window、checksum、attempt 和 resume 信息 | S09 CP5 approved 后才可实现 |
| TASK-S09-04 | `market_data/lake_layout.py` | 修改 raw / manifest / run metadata 路径解析，强制 lake root 显式化和禁区校验 | S09 CP5 approved 后才可实现 |
| TASK-S09-05 | `market_data/cli.py` | 修改 CLI plan/run 入口，真实执行前输出授权缺口和窗口计划 | S09 CP5 approved 后才可实现 |
| TASK-S09-06 | `tests/test_cr014_windowed_real_run_contract.py` | 创建 fake provider / tmp_path 合同测试，覆盖 unauthorized、partial failure、resume 和 no publish | S09 CP5 approved 后才可实现 |

## CP6 收尾记录

| 项 | 状态 | 说明 |
|---|---|---|
| CP6 | PASS | `process/checks/CP6-CR014-S09-windowed-real-fetch-lake-write-run-CODING-DONE.md` |
| CP7 | PASS | `process/checks/CP7-CR014-S09-windowed-real-fetch-lake-write-run-VERIFICATION-DONE.md` |
| 真实 smoke | PASS_PARTIAL_SCOPE | `process/checks/REAL-TUSHARE-CR014-S09-YTD-CONFIG-LAKE-VERIFY-2026-05-28.md` |
| S10 样本可用性 | PASS_SAMPLE_USABILITY_NOT_PUBLISHABLE_SAMPLE_ONLY | `process/checks/REAL-TUSHARE-CR014-S10-2026-USABILITY-VALIDATION-2026-05-28.md` |
| S11 full-A pull | RAW_MANIFEST_PULL_PASS_CANONICAL_PASS_QUALITY_GAP | `process/checks/REAL-TUSHARE-CR014-S11-FULL-A-2026-YTD-PULL-2026-05-28.md` |
| S12 adj_factor denominator 重验 | PASS_ADJ_FACTOR_OBSERVED_PRICE_DENOMINATOR_PUBLISH_BLOCKED | `process/checks/REAL-TUSHARE-CR014-S12-ADJ-FACTOR-PRICES-DENOMINATOR-REVALIDATION-2026-05-28.md` |
| S13 prices lifecycle/trade_status 重验 | PASS_PRICES_LIFECYCLE_TRADE_STATUS_DENOMINATOR_WARN_NON_PIT_PUBLISH_BLOCKED | `process/checks/REAL-TUSHARE-CR014-S13-PRICES-LIFECYCLE-TRADE-STATUS-DENOMINATOR-2026-05-28.md` |
| S14 full-history pull | PASS_FULL_HISTORY_PRICES_ADJ_FACTOR_CANDIDATE_PULLED_PUBLISH_BLOCKED | `process/checks/REAL-TUSHARE-CR014-S14-FULL-HISTORY-PRICES-ADJ-FACTOR-PULL-2026-05-29.md` |
| Story 状态 | full-history-2015-2026-ytd-prices-adj-factor-candidate-usable-non-pit-warn | 已完成 2015-01-05..2026-05-28 全 A `prices` / `adj_factor` raw、manifest、canonical candidate；合计 2768 个开市日、5536 条成功 manifest、`prices` 11311360 行、`adj_factor` 11823057 行；所有已观测 `prices` 交易对均有 `adj_factor` |
| real_run_authorized | 2015-2026-ytd configured lake run executed | 用户授权读取 `.env` token 后已执行真实抓取与写湖；token 未打印、未落盘；配置 lake root 只以 `<configured-env-lake-root>` 脱敏记录 |
| verified | false | `verified=false` 保持到 PIT universe / W3 质量缺口关闭并明确允许 publish；不得把 raw/canonical candidate 成功当作 production current truth |
