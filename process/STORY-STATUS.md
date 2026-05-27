---
last_updated: "2026-05-27T21:33:34+08:00"
current_wave: "CR014-W5-REAL-RUN"
current_story: "CR014-S09-windowed-real-fetch-lake-write-run"
current_gate: "s09-full-a-prices-batching-decision"
---

## Story 状态汇总

| Story ID | 标题 | Wave | 状态 | 负责人 | 阻塞 |
|----------|------|------|------|--------|------|
| STORY-001 | 工程基线与数据契约骨架 | W0 | verified | meta-qa | 无；正式 8 维度验收 PASS，无 BLOCKING/REQUIRED 失败项 |
| STORY-002 | 数据准备节流重试与 manifest | W0 | verified | meta-qa | 无；正式验证 PASS，无 BLOCKING/REQUIRED 失败项 |
| STORY-003 | 标准化 parquet 与数据质量报告 | W0 | verified | meta-qa | 无；`BUG-STORY-003-001` 已 CLOSED / REGRESSION_PASS，正式回归 PASS |
| STORY-004 | 离线 Data Loader 与合同校验 | W1 | verified | meta-qa | 实现完成；pytest 覆盖离线 parquet、质量门禁、缺质量报告 fail fast；F-004 日志回归 PASS |
| STORY-005 | 动量信号与组合成交引擎 | W1 | verified | meta-qa | 实现完成；pytest 覆盖 T+1 买入与会计恒等式；F-004 日志回归 PASS |
| STORY-006 | 指标、单次回测报告与 metadata | W1 | verified | meta-qa | 实现完成；pytest 覆盖 2019-2025 schedule 边界、回测指标与日志回归 |
| STORY-007 | 60 组参数扫描报告 | W2 | verified | meta-qa | 实现完成；pytest 覆盖默认 60 组扫描、失败行 schema、文本字段防护与日志回归 |
| STORY-008 | 候选报告与聚宽人工验证模板 | W2 | verified | meta-qa | 实现完成；pytest 覆盖候选选择、selection_reason 与日志回归 |
| STORY-009 | PIT 股票池 Provider 增强契约 | W3 | verified | meta-qa | 实现完成；pytest 覆盖 `UNRESOLVED` registry fail fast 与日志回归；未伪造数据源 |
| STORY-010 | 交易状态与不可交易约束 | W3 | verified | meta-qa | 实现完成；pytest 覆盖 `UNRESOLVED` trade_status fail fast、portfolio 交易状态 gate 与日志回归 |
| STORY-011 | 涨跌停与事件 available_at 增强 | W3 | verified | meta-qa | 实现完成；pytest 覆盖 limit/events `UNRESOLVED` fail fast 与日志回归；保留 `STORY-010 -> STORY-011` 串行依赖 |
| STORY-012 | 偏差审计报告 | W3 | verified | meta-qa | 实现完成；pytest 覆盖对象优先审计输入、delta、缺候选 rank warning 降级与日志回归 |
| STORY-013 | 策略扩展接口与 RSI/MACD 示例 | W4 | verified | meta-qa | 实现完成；pytest 覆盖 RSI/MACD 默认参数、warm-up 后目标、非法参数失败与日志回归 |

## CR-005 Batch A 状态

| Story ID | 标题 | Wave | 状态 | 负责人 | 阻塞 |
|---|---|---|---|---|---|
| CR005-S01 | Tushare connector 真实写湖边界 | CR5-W0 | verified | meta-qa | 无；CP7 PASS，lake root / `.gitignore`、默认离线、no-network、token、dry-run job spec 和禁区复核通过 |
| CR005-S02 | Tushare 多 dataset schema、PIT 字段与复权 normalization | CR5-W1 | verified | meta-qa | 无；CP7 重验 PASS，非法日期 fail fast 与 `prices.daily + prices.adj_factor` 分离 manifest join 均通过 |

## CR-005 Batch B1 / S03 LLD 状态

| Story ID | 标题 | Wave | 状态 | 负责人 | 阻塞 |
|---|---|---|---|---|---|
| CR005-S03 | 多 dataset quality/catalog/readers 与 PIT/复权 gate | CR5-W2 | verified / CP7 PASS | meta-po | CP7 PASS，agent_id/thread_id=`019e363c-9916-7971-980a-699bcf023852`；meta-po 已收敛为 verified。下一步等待用户是否启动 S04，不得自动进入 S04/S05/S06 或 Backtrader |

## CR-005 Batch B2/C：S04/S05 Implementation / CP7 Queue

| Story ID | 标题 | Wave | 状态 | 负责人 | 阻塞 |
|---|---|---|---|---|---|
| CR005-S04 | 沪深 300 本地基准与实验只读接入 | CR5-W3 | verified / CP7 PASS | meta-po | 无；S04 CP7 PASS，目标测试 6 passed，S04+S03 最小回归 15 passed，全量离线回归 90 passed；未联网、未真实写 lake、未进入 S06/Backtrader |
| CR005-S05 | 多源 comparison 与回补文档 | CR5-W4 | verified / CP7 PASS | meta-po | 无；S05 CP7 PASS，目标测试 5 passed，S05+S03 最小回归 14 passed，comparison CLI 回归 6 passed，全量离线回归 90 passed；未联网、未真实写 lake、未进入 S06/Backtrader |

## CR-005 Batch D：S06 LLD / Implementation Queue

| Story ID | 标题 | Wave | 状态 | 负责人 | 阻塞 |
|---|---|---|---|---|---|
| CR005-S06 | Backtrader optional backend | CR5-W5 | verified / CP7 PASS | meta-po | 无阻塞；CP7=`process/checks/CP7-CR005-S06-backtrader-optional-backend-VERIFICATION-DONE.md`，meta-qa/qa-cao the 2nd agent_id/thread_id=`019e36bb-f4d5-7153-8b8d-738352fbc0b0`。专项 16 passed、全量 106 passed、真实 Backtrader Cerebro smoke 输出 `Cerebro`，forbidden import/token/network scan 无输出。 |

## CR-007 Batch A：Canonical 数据覆盖与 benchmark

| Story ID | 标题 | Wave | 状态 | 负责人 | 阻塞 |
|---|---|---|---|---|---|
| CR007-S01 | 长周期 prices 回补 planner | CR007-DEV-W1 | verified | meta-qa | CP7 PASS；未授权真实 fetch/lake 写入 |
| CR007-S02 | benchmark / calendar 回补 | CR007-DEV-W2 | verified | meta-qa/qa-yan | CP7 PASS；`hs300_index` / `trade_calendar` 合同冻结 |
| CR007-S03 | 成分、权重与股票基础信息 readiness | CR007-VERIFY-W3-CR008-UNLOCK | verified | meta-qa/qa-shi the 2nd | CP7 PASS；专项 `6 passed`、相关 market_data 回归 `32 passed`；已作为 CR008-S05 解锁输入 |
| CR007-S04 | 实验真实 benchmark 消费 | CR007-VERIFY-W4 | verified | meta-qa/qa-jin the 2nd | CP7 PASS；CP7=`process/checks/CP7-CR007-S04-experiment-real-benchmark-consumption-VERIFICATION-DONE.md`，S04 定向 `7 passed`、S02/CR008 回归 `13 passed`、py_compile 通过 |
| CR007-S05 | 质量报告与文档 guardrail | CR007-VERIFY-W5 | verified | meta-qa/qa-he the 2nd | CP7 PASS；CP7=`process/checks/CP7-CR007-S05-data-quality-report-and-doc-guardrail-VERIFICATION-DONE.md`，S05 专项 `7 passed`、CR006/CR008 回归 `31 passed`、CR008 auxiliary/proxy 回归 `18 passed`、py_compile 通过 |

## CR-008 Batch A：研究级数据层口径硬化

| Story ID | 标题 | Wave | 状态 | 负责人 | 阻塞 |
|---|---|---|---|---|---|
| CR008-S01 | research input 合同与报告 metadata | CR008-REVERIFY-W1 | verified | meta-po | CP7 重验 PASS；CP7=`process/checks/CP7-CR008-S01-research-input-contract-and-report-metadata-VERIFICATION-DONE.md`，测试 `22 passed`，CP7-F01/F02 已关闭 |
| CR008-S02 | proxy / real benchmark 字段隔离 | CR008-VERIFY-W2 | verified | meta-qa/qa-lv | CP7 PASS；CP7=`process/checks/CP7-CR008-S02-proxy-real-benchmark-field-separation-VERIFICATION-DONE.md`，测试 `16 passed`，无阻断项 |
| CR008-S03 | 统一 research dataset builder | CR008-VERIFY-W3 | verified | meta-qa/qa-he | CP7 PASS；CP7=`process/checks/CP7-CR008-S03-research-dataset-builder-VERIFICATION-DONE.md`，S03 定向 `9 passed`、回归 `31 passed`，无阻断项 |
| CR008-S04 | 质量、复权与 label window gate | CR008-VERIFY-W4A | verified | meta-qa/qa-kong the 2nd | CP7 PASS；CP7=`process/checks/CP7-CR008-S04-quality-adjustment-label-window-gates-VERIFICATION-DONE.md`，S04 定向 `11 passed`、S03 builder 回归 `9 passed`、py_compile 通过 |
| CR008-S05 | PIT / fixed universe 消费合同 | CR008-VERIFY-W5 | verified | meta-qa/qa-wei the 2nd | CP7 PASS；CP7=`process/checks/CP7-CR008-S05-pit-universe-consumption-contract-VERIFICATION-DONE.md`，S05 定向 `9 passed`、S03/S04 回归 `20 passed`、py_compile 通过 |
| CR008-S06 | 因子研究辅助数据合同 | CR008-VERIFY-W6 | verified | meta-qa/qa-zhang the 2nd | CP7 PASS；CP7=`process/checks/CP7-CR008-S06-factor-research-auxiliary-data-contract-VERIFICATION-DONE.md`，S06 定向 `11 passed`、S03/S04/S05 回归 `29 passed`、实验十五回归 `3 passed`、py_compile 通过 |

## CR-010：真实生产数据湖与研究真实性

### CR010-DL-BATCH-A：数据湖基础生产化

| Story ID | 标题 | Wave | 状态 | 负责人 | 阻塞 |
|---|---|---|---|---|---|
| CR010-S01 | multi-dataset plan/run/publish CLI 合同 | CR010-DL-BATCH-A | verified | meta-po / direct-main-thread record | CP6/CP7 已记录 PASS；真实 Tushare resmoke 后 current truth 仍为 PARTIAL |
| CR010-S02 | prices + adj_factor 历史回补闭环 | CR010-DL-BATCH-A | verified | meta-po / direct-main-thread record | CP6/CP7 已记录 PASS；真实小窗口 `prices` readiness 为 warn_non_pit_universe |
| CR010-S03 | hs300_index + trade_calendar 回补闭环 | CR010-DL-BATCH-A | verified | meta-po / direct-main-thread record | CP6/CP7 已记录 PASS；`trade_calendar`、`hs300_index` readiness available |
| CR010-S04 | index_members / index_weights / stock_basic readiness 强化 | CR010-DL-BATCH-A | verified | meta-po / direct-main-thread record | CP6/CP7 已记录 PASS；2026-05-22 补探中 Tushare `index_member` 对 HS300 相关组合仍为 0 行，`index_members` 继续阻断；`index_weights` / `stock_basic` 不得替代 |
| CR010-S05 | catalog coverage 与 production readiness report | CR010-DL-BATCH-A | verified | meta-po / direct-main-thread record | CP6/CP7 已记录 PASS；补探后仍为 `current_truth_complete=false`、`production_strict=fail`，`exploratory=warn` |

### CR010-DL-BATCH-B：W3 数据契约与 fail-fast

| Story ID | 标题 | Wave | 状态 | 负责人 | 阻塞 |
|---|---|---|---|---|---|
| CR010-S06 | PIT source/interface Spike 与 readiness 加固 | CR010-DL-BATCH-B | implemented / meta-qa CP7 PASS | main-thread + meta-qa/qa-cao | `index_members` 不由 `index_weights` / `stock_basic` 替代；验证见 `process/checks/CP7-CR010-REMAINING-BATCHES-META-QA-VERIFICATION-2026-05-22.md` |
| CR010-S07 | trade_status 合同 / reader / fail-fast | CR010-DL-BATCH-B | implemented / meta-qa CP7 PASS | main-thread + meta-qa/qa-cao | `trade_status` source/interface 或 `available_at` 缺失 fail-fast；production_strict 阻断 |
| CR010-S08 | prices_limit 合同 / gate / fail-fast | CR010-DL-BATCH-B | implemented / meta-qa CP7 PASS | main-thread + meta-qa/qa-cao | `prices_limit` source/interface 或 `available_at` 缺失 fail-fast；不声明真实可成交 |
| CR010-S09 | events 合同 / available_at gate / fail-fast | CR010-DL-BATCH-B | implemented / meta-qa CP7 PASS | main-thread + meta-qa/qa-cao | events 缺 explicit `available_at` fail-fast |

### CR010-QF-BATCH-C：实验消费与真实性报告

| Story ID | 标题 | Wave | 状态 | 负责人 | 阻塞 |
|---|---|---|---|---|---|
| CR010-S10 | 统一 realism_mode 与 research metadata | CR010-QF-BATCH-C | implemented / meta-qa CP7 PASS | main-thread + meta-qa/qa-cao | `production_strict` 输出 blocked claims、readiness/PIT/W3 状态；缺口 fail |
| CR010-S11 | 16 experiments smoke 与 limitation matrix | CR010-QF-BATCH-C | implemented / meta-qa CP7 PASS | main-thread + meta-qa/qa-cao | 16 行 experiment realism matrix；experiment 11 标记 N/A |
| CR010-S12 | Backtrader / VectorBT clean feed 边界回归 | CR010-QF-BATCH-C | implemented / meta-qa CP7 PASS | main-thread + meta-qa/qa-cao | consumer boundary 静态验证无 connector/runtime/storage/provider/network/token/backfill |

### CR010-OPS-BATCH-D：备份、归档、恢复与保留策略

| Story ID | 标题 | Wave | 状态 | 负责人 | 阻塞 |
|---|---|---|---|---|---|
| CR010-S13 | backup/archive/restore env 与 manifest/checksum/脱敏契约 | CR010-OPS-BATCH-D | implemented / meta-qa CP7 PASS | meta-dev/dev-xu + main-thread + meta-qa/qa-cao | dev agent `019e4f76-e461-7e20-87f4-cd6b79d713fc` 交付核心模块；报告脱敏验证 PASS |
| CR010-S14 | backup CLI dry-run / execute / verify / report | CR010-OPS-BATCH-D | implemented / meta-qa CP7 PASS / real smoke PASS | meta-dev/dev-xu + main-thread + meta-qa/qa-cao | `backup-plan/run/verify/report` 已接入 CLI；真实 release smoke：copied=4、skip=4、verify same=4、report computed=4 |
| CR010-S15 | restore CLI 与 restore drill | CR010-OPS-BATCH-D | implemented / meta-qa CP7 PASS / real smoke PASS | meta-dev/dev-xu + main-thread + meta-qa/qa-cao | `restore-root==lake-root` fail-fast；restore-drill 与 restore root read/revalidate/replay 通过，replay `network_calls=0` |
| CR010-S16 | retention policy 与 archive/backup cleanup | CR010-OPS-BATCH-D | implemented / meta-qa CP7 PASS | main-thread + meta-qa/qa-cao | retention 只读预检：published run 保护，failed/candidate run 保留；本版本不自动删除 |

### CR010 批次门控摘要

| 批次 | CP5 | CP6 | CP7 | 下一步 |
|---|---|---|---|---|
| CR010-DL-BATCH-A | approved | PASS | PASS | 已 verified；真实小窗口 resmoke PARTIAL，CR-010 不关闭 |
| CR010-DL-BATCH-B | old CP5/CP6/CP7 blocked records superseded | main-thread PASS | PASS: meta-qa/qa-cao | 代码与测试已通过；旧 handoff-only BLOCKED 记录见 `process/checks/CR010-BLOCKED-RECORDS-SUPERSEDED-2026-05-22.md` |
| CR010-QF-BATCH-C | old CP5/CP6/CP7 blocked records superseded | main-thread PASS | PASS: meta-qa/qa-cao | 代码与测试已通过；正式 QA 证据见 `process/checks/CP7-CR010-REMAINING-BATCHES-META-QA-VERIFICATION-2026-05-22.md` |
| CR010-OPS-BATCH-D | old CP5/CP6/CP7 blocked records superseded | dev-xu/main-thread PASS | PASS: meta-qa/qa-cao + real ops smoke | dev agent 交付 OPS 核心；真实 backup/restore smoke 见 `process/checks/REAL-TUSHARE-DATA-LAKE-SMOKE-CR010-INDEX-MEMBERS-OPS-2026-05-22.md` |

## CR-011：因子研究生产级数据补齐

### CR011-DATA-BATCH-A：数据与研究消费合同

| Story ID | 标题 | Wave | 状态 | 负责人 | 阻塞 |
|---|---|---|---|---|---|
| CR011-S01 | 真实 benchmark 与 policy 消费 | CR011-DATA-BATCH-A | verified / CP7 PASS | meta-qa/qa-hua | CP6=`process/checks/CP6-CR011-S01-real-benchmark-and-policy-consumption-CODING-DONE.md`，CP7=`process/checks/CP7-CR011-S01-real-benchmark-and-policy-consumption-VERIFICATION-DONE.md`；S01 定向 6 passed，相关回归 74 passed |
| CR011-S02 | PIT 股票池与股票生命周期 | CR011-DATA-BATCH-A | verified / CP7 PASS | meta-qa/qa-shi | CP6 replacement 接管复核 PASS；CP7=`process/checks/CP7-CR011-S02-pit-universe-and-stock-lifecycle-completion-VERIFICATION-DONE.md`，S02 定向 `7 passed`、相关回归 `35 passed` |
| CR011-S03 | 可交易性与涨跌停门控 | CR011-DATA-BATCH-A | verified / CP7 PASS | meta-qa/qa-wei | CP7=`process/checks/CP7-CR011-S03-tradability-status-and-price-limit-gates-VERIFICATION-DONE.md`；S03 定向 `8 passed`、相关回归 `33 passed`、安全扫描 PASS |
| CR011-S04 | OHLCV / VWAP 干净执行 feed | CR011-DATA-BATCH-A | verified / CP7 reverify PASS | meta-qa/qa-hua the 2nd | 首次 CP7 FAIL 的 `CR011-S04-CP7-F01` 已由 blocker-fix CP6=`process/checks/CP6-CR011-S04-CP7-BLOCKER-FIX-CODING-DONE.md` 修复并由 CP7 复验=`process/checks/CP7-CR011-S04-ohlcv-vwap-clean-execution-feed-REVERIFY-DONE.md` PASS；agent_id/thread_id=`019e585a-12bf-7721-affc-a0927f18c5c6` |
| CR011-S05 | 复权与公司行动审计 | CR011-DATA-BATCH-A | verified / CP7 PASS | meta-qa/qa-he the 2nd | CP7=`process/checks/CP7-CR011-S05-adjustment-and-corporate-action-audit-VERIFICATION-DONE.md`；S05 定向 `7 passed`、S04/S01/CR008 回归 `57 passed`、available_at probe PASS、安全扫描 PASS |
| CR011-S06 | 行业 / 市值 / 风格暴露 | CR011-DATA-BATCH-A | verified / CP7 reverify PASS | meta-qa/qa-jin the 2nd | CP7 首验=`process/checks/CP7-CR011-S06-industry-market-cap-style-exposure-data-VERIFICATION-DONE.md` FAIL，阻断项 `CR011-S06-CP7-F01` 已由 CP6 blocker-fix=`process/checks/CP6-CR011-S06-CP7-BLOCKER-FIX-CODING-DONE.md` 修复，并由 CP7 复验=`process/checks/CP7-CR011-S06-industry-market-cap-style-exposure-data-REVERIFY-DONE.md` PASS；agent_id/thread_id=`019e58c2-6271-7131-adf0-5e026d7680af` |
| CR011-S07 | 流动性 / 容量 / 成本敏感性 | CR011-RESEARCH-BATCH-B | verified / CP7 PASS | meta-qa/qa-yan the 2nd | CP7=`process/checks/CP7-CR011-S07-liquidity-capacity-and-cost-sensitivity-VERIFICATION-DONE.md` PASS；S07 定向 `7 passed`、S03/S04/S06 回归 `40 passed`、benchmark/实验回归 `8 passed`，安全扫描 PASS；agent_id/thread_id=`019e58f5-c3ae-7930-8113-30f28ad4388e` |
| CR011-S08 | 因子审计面板与稳健性验证 | CR011-VALIDATION-BATCH-C | verified / CP7 PASS | meta-qa/qa-lv the 2nd | CP7=`process/checks/CP7-CR011-S08-factor-panel-audit-and-robust-validation-VERIFICATION-DONE.md` PASS；S08 定向 `3 passed`、S01/S02/S05/S07/实验回归 `29 passed`、fail-closed probe PASS；agent_id/thread_id=`019e5931-551d-7a41-bdf9-cbf98b0829fb` |

### CR011 批次门控摘要

| 批次 | CP5 自动预检 | CP5 人工确认 | 实现授权 | 下一步 |
|---|---|---|---|---|
| CR011-DATA-BATCH-A | PASS：S01..S06 六份 Story 级预检全通过 | approved：`checkpoints/CP5-CR011-DATA-BATCH-A-LLD-BATCH.md` | true for S01..S06，仍受 Story DAG / file ownership 串行调度 | S01/S02/S03/S04/S05/S06 verified；DATA-BATCH-A 已完成 |
| CR011-RESEARCH-BATCH-B | PASS：S07 Story 级预检通过 | approved：`checkpoints/CP5-CR011-RESEARCH-BATCH-B-LLD-BATCH.md` | true for S07 offline implementation | S07 CP6 PASS、CP7 PASS，RESEARCH-BATCH-B 已 verified |
| CR011-VALIDATION-BATCH-C | PASS：S08 Story 级预检通过 | approved：`checkpoints/CP5-CR011-VALIDATION-BATCH-C-LLD-BATCH.md` | true for S08 offline implementation | S08 CP6 PASS、CP7 PASS；VALIDATION-BATCH-C 已 verified；CR-011 文档刷新已完成；CP8 自动预检 PASS；用户已 approve CP8，CR-011 已关闭 |

## CR-014：全 A since-inception 生产数据湖 Story Plan

### CR014-FULL-HISTORY-LAKE-BATCH-A：执行态

| Story ID | 标题 | Wave | 状态 | 负责人 | 阻塞 |
|---|---|---|---|---|---|
| CR014-S01-a-share-universe-lifecycle-contract | 全 A universe / lifecycle / code-change 合同 | CR014-W1-CONTRACTS | verified | meta-qa/qa-he | CP6 PASS；CP7 PASS；agent_id=`019e66a7-b1a5-7d21-8463-8a8c73422a06`；真实操作计数均为 0 |
| CR014-S02-parquet-layout-manifest-catalog-publish-gate | Parquet layout / manifest / catalog current pointer / publish gate | CR014-W1-CONTRACTS | verified | meta-qa/qa-lv | CP6 PASS；CP7 PASS；dev_agent_id=`019e66a7-f383-7b01-89e0-ca2951dd659c`；qa_agent_id=`019e66b4-4415-7b60-9dbd-ee706cd16828`；真实操作计数均为 0 |
| CR014-S03-p0-plan-run-normalize-validate-publish-contract | P0 dataset plan/run/normalize/validate/publish 合同 | CR014-W2-PIPELINE | verified | meta-qa/qa-hua | CP6 PASS；CP7 PASS；dev_agent_id=`019e66ba-bf09-7c31-98e9-86a4fdab70ec`；qa_agent_id=`019e66cb-6bd3-7bc3-96b8-88fd50ce59eb`；真实抓取与 raw/manifest 写湖仍拆到 S09；真实操作计数均为 0 |
| CR014-S04-duckdb-readonly-query-audit-parity-boundary | DuckDB read-only query/audit/parity 边界 | CR014-W2-PIPELINE | verified | meta-qa/qa-jin | CP6 PASS；CP7 PASS；dev_agent_id=`019e66cb-e892-7d11-8f59-753d62b13f4f`；qa_agent_id=`019e66d8-59ef-7a53-bf8e-caf959456b1f`；本批不引入 DuckDB 依赖、不写 `.duckdb`；真实操作计数均为 0 |
| CR014-S05-full-history-readiness-gap-claim-boundary | full-history readiness audit / gap register / claim boundary | CR014-W3-AUDIT-OPS | verified | meta-qa/qa-shi | CP6 PASS；CP7 PASS；dev_agent_id=`019e66e0-4083-7f61-92bd-20868a50cfb4`；qa_agent_id=`019e66f1-c806-79f1-8710-1df27ca34c50`；任一 P0 gate 未过时 full-A allowed claim=0；不读/覆盖旧 reports；真实操作计数均为 0 |
| CR014-S06-incremental-refresh-replay-retention-contract | incremental refresh / replay / retention 合同 | CR014-W3-AUDIT-OPS | verified | meta-qa/qa-zhang | CP6 PASS；CP7 PASS；dev_agent_id=`019e66d8-99d0-7823-9a85-5d850d07e8e7`；qa_agent_id=`019e66e7-ad3b-7882-92f8-bb2aaa4fc054`；replay 不触发 provider、不读凭据、不写 raw、不改 current pointer；retention 仅 dry-run |
| CR014-S07-research-consumer-readonly-docs-runbook-boundary | research consumer read-only contract 与 docs/runbook 后续边界 | CR014-W4-CONSUMER-BOUNDARY | verified | meta-qa/qa-cao | CP6 PASS；CP7 PASS；dev_agent_id=`019e671e-01d5-7472-97f0-9457e2c6bc2b`；qa_agent_id=`019e672d-81dd-7683-a31e-4aed391942b3`；研究消费层不得直接 DuckDB 写入/发布/扫未发布 lake；真实操作计数均为 0 |
| CR014-S08-w3-minute-tick-level2-vwap-blocked-decision-boundary | W3 / minute / tick / Level2 / VWAP blocked 决策边界 | CR014-W4-CONSUMER-BOUNDARY | verified | meta-qa/qa-wei | CP6 PASS；CP7 PASS；dev_agent_id=`019e66fc-3fbd-7c61-9b5e-9fedcf5fbbd0`；qa_agent_id=`019e6710-77a0-7441-b5d0-e9a05356be38`；W3/minute/tick/Level2/VWAP production allowed claim=0；真实操作计数均为 0 |
| CR014-S09-windowed-real-fetch-lake-write-run | 分时段真实抓取与 raw/manifest 写湖执行 | CR014-W5-REAL-RUN | partial-real-smoke-pass-full-a-prices-pending | meta-po | 真实 Tushare smoke PASS，写入 `/tmp/local-backtest-cr014-s09-ytd-lake`；已完成 stock_basic 全交易所、trade_calendar、hs300_index、prices/adj_factor 的 `000001.SZ` 样本；全 A prices/adj_factor 待批处理 runner |

### CR014 门控摘要

| 项 | 状态 | 说明 |
|---|---|---|
| CP3 R2 | APPROVED | 用户已批准 D1-D12 推荐决策，采用 CR14-A |
| CP4 自动预检 | PASS | `process/checks/CP4-CR014-STORY-DAG-PARALLEL-SAFETY.md` 已生成，结论 PASS |
| LLD | APPROVED | 8 张 LLD 与 8 个 CP5 自动预检均已完成；用户已按推荐全部允许 |
| 实现授权 | true-for-batch-a-controlled-code | S01..S08 可按 Story DAG、文件所有权、CP6/CP7 进入受控离线实现 |
| 真实操作计数 | 0 | provider_fetch=0、lake_write=0、credential_read=0、duckdb_dependency_change=0 |
| Publish Gate | NOT_AUTHORIZED | Validate/parity PASS 不自动 publish；只有 Explicit Publish Gate 可更新 catalog current pointer |
| 真实抓取/写湖 | SPLIT_TO_BATCH_B | 已拆分为 `CR014-S09-windowed-real-fetch-lake-write-run`；需 S01..S08 verified 后独立 LLD / CP5 / authorization_id 才能分时段执行 |
| CP8 自动预检 | PASS | `process/checks/CP8-CR014-DELIVERY-READINESS.md` 已生成，结论 PASS |
| CP8 人工终验 | APPROVED | 用户已回复同意；`checkpoints/CP8-CR014-DELIVERY-READINESS.md` 已回填 approved；不包含 S09 真实执行授权 |

## Wave 进度

| Wave | 总数 | package-draft | ready-for-lld-review | package-ready-for-review | package-approved | in-development | ready-for-verification | verified | blocked |
|------|------|---------------|----------------------|--------------------------|------------------|----------------|------------------------|----------|---------|
| W0 | 3 | 0 | 0 | 0 | 0 | 0 | 0 | 3 | 0 |
| W1 | 3 | 0 | 0 | 0 | 0 | 0 | 0 | 3 | 0 |
| W2 | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 2 | 0 |
| W3 | 4 | 0 | 0 | 0 | 0 | 0 | 0 | 4 | 0 |
| W4 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 |
| CR014-W1-CONTRACTS | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 2 | 0 |
| CR014-W2-PIPELINE | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 2 | 0 |
| CR014-W3-AUDIT-OPS | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 2 | 0 |
| CR014-W4-CONSUMER-BOUNDARY | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 2 | 0 |
| CR014-W5-REAL-RUN | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 |

## 当前门控

## CR-004 Batch D 当前状态

| 对象 | 状态 | 证据 | 下一步 |
|---|---|---|---|
| STORY-003 legacy quality addendum | CP5 approved | `process/stories/STORY-003-parquet-quality-report-LLD.md`; `checkpoints/CP5-CR004-BATCH-D-DATALOADER-EXPERIMENT-READONLY-LLD-REVIEW.md` | 仅在需要字段对齐时按限定范围处理；不重开真实抓取或真实报告生成。 |
| STORY-004 Data Loader first / no real fetch | CP5 approved / dev-ready | `process/stories/STORY-004-offline-data-loader-contract-validator-LLD.md`; `checkpoints/CP5-CR004-BATCH-D-DATALOADER-EXPERIMENT-READONLY-LLD-REVIEW.md` | 可按 LLD 进入实现；只允许 `engine/data_loader.py` 和 `engine/contracts.py` 纯常量范围。 |
| STORY-018 实验十/十二只读接入 | CP5 approved / dev-ready | `process/stories/STORY-018-cr004-experiment-readonly-benchmark-LLD.md`; `checkpoints/CP5-CR004-BATCH-D-DATALOADER-EXPERIMENT-READONLY-LLD-REVIEW.md` | 可按 LLD 进入实现；不得联网抓取真实沪深 300，不得静默代理基准。 |

本批 CP5 通过只代表 LLD 可作为实现输入；当前尚未生成 CP6/CP7，尚未实现代码，尚未抓取真实行情，尚未写真实 `data/**`、`reports/**` 或 `delivery/**`。

`STORY-001` 已完成实现范围收敛并通过 meta-qa 正式 8 维度验收，`process/VERIFICATION-REPORT.md` 结论为 PASS，无 BLOCKING 或 REQUIRED 失败项。meta-po 已将 `STORY-001` 收敛为 `verified`。

meta-po 静态复核的 STORY-001 实现源文件范围为：`pyproject.toml`、`uv.lock`、`config/data_prep.yaml`、`engine/__init__.py`、`engine/contracts.py`、`strategies/__init__.py`、`data/.gitkeep`、`reports/.gitkeep`。验证报告确认未发现 `STORY-002+` 源文件、data fetcher、manifest writer、quality report 逻辑、回测引擎逻辑、策略逻辑或 `delivery/**` 产物。导入验证产生的缓存和虚拟环境残留已清理，不作为 STORY-001 源实现范围。

`STORY-002` 依赖的 `STORY-001` 已满足。meta-dev 已创建 `process/stories/STORY-002-data-prep-throttle-manifest-LLD.md`，用户已明确回复 `确认通过`，meta-po 已将 LLD 确认为通过。meta-dev 报告 STORY-002 实现完成，且声明只修改 `engine/manifest.py`、`engine/akshare_adapter.py`、`engine/data_prep.py`、`engine/contracts.py`；未实现 STORY-003；未创建 normalizer/parquet/quality report；未写真实 `data/raw/**` 或 `data/manifests/**`；未调用真实 AKShare；未写 delivery；验证使用 fake adapter 和临时目录。meta-qa 正式验证结论 PASS，无 BLOCKING 或 REQUIRED 失败项；meta-po 已将 STORY-002 收敛为 `verified`。

`STORY-003` 依赖 `STORY-001` 与 `STORY-002`，当前均已 verified。W0 为串行 Wave，meta-dev 已完成 STORY-003 LLD、实现与限定范围 bugfix。meta-qa 已完成 `BUG-STORY-003-001` 回归验证，`process/VERIFICATION-REPORT.md` 中回归结论为 PASS，Bug 状态建议为 `CLOSED / REGRESSION_PASS`。meta-po 已关闭该 Bug，并将 STORY-003 从 `ready-for-verification` 收敛为 `verified`。

W0 包含 `STORY-001`、`STORY-002`、`STORY-003`，三者均已 verified，因此 W0 完成。用户已于 2026-05-15 明确确认通过 `STORY-004` 至 `STORY-013` 批量 LLD / Story Package，meta-po 已回写检查点与 LLD frontmatter，并进入 `story-execution`。本轮实现按主链 `STORY-004 -> STORY-005 -> STORY-006 -> STORY-007 -> STORY-008 -> STORY-009 -> STORY-010 -> STORY-011 -> STORY-012` 维持依赖串行；`STORY-013` 在 `STORY-008` 后文件所有权无冲突，随 W3 起点并行排队条件满足后实现。当前 `STORY-004` 至 `STORY-013` 均已完成实现并通过针对性 pytest。W3 硬门禁保持：`STORY-009/010/011` 的 `source/interface=UNRESOLVED` 未替换 exact 值前，相关 data_prep、normalizer、quality、loader 启用路径必须 fail fast；本轮只落地 fail-fast 防线，未伪造数据源。

## 非阻断观察项

| ID | 状态 | 归属 | 说明 | 后续处理 |
|---|---|---|---|---|
| OBS-STORY-003-GUARDRAIL-SCRIPT-MISSING | PROCESS_DEBT_OPEN | 仓库级流程债 | `scripts/check_delivery_guardrails.py` 与 `scripts/` 目录不存在，无法执行项目规则中的提交前 guardrail 命令。 | 不阻断 STORY-003 或 W0；不得在本轮越界创建脚本。后续可由独立流程治理 Story 或 QA 流程债处理。 |
| OBS-STORY-003-VALIDATION-ENV-STORY-ID | QA_OBSERVATION_OPEN | 后续 QA 观察项 | `process/VALIDATION-ENV.yaml` 的 `story_id` 仍为 `STORY-001`，但 `approval.confirmed=true`，且当前状态与 handoff 已指向 STORY-003/W1。 | 不阻断 STORY-003 或 W0；后续进入 STORY-004 验证前由 meta-po/meta-qa 决定是否刷新验证环境元数据，避免审计歧义。 |

## 阻塞项清单

- 当前 CR-005 Batch A Story 执行 BLOCKING 阻塞项已关闭：`CR005-S02` CP7 重验 PASS，非法日历日期校验与 `prices.daily + prices.adj_factor` 分离输入 join 均已验证；`STORY-001` 至 `STORY-013` 历史基线仍均为 verified。不得据此自动进入 `CR005-S03/S04/S05/S06` 或 Backtrader。
- CR005-S03、CR005-S04、CR005-S05、CR005-S06 均已 CP7 PASS 并由 meta-po 收敛为 verified。S06 专项测试 `16 passed`，全量离线回归 `106 passed`，真实 Backtrader Cerebro smoke 输出 `Cerebro`；未联网、未真实写 lake、未读取 token、未导入 connector/runtime/storage。
- Documentation 阶段交付出口 BLOCKING 门控已关闭：用户已确认正式用户文档输出路径为仓库根 `README.md` + `docs/USER-MANUAL.md`。文档已输出并通过后置 QA；仍不得写 `delivery/**`、安装脚本、代码、测试或真实数据。
- 目录结构收敛门控已完成：meta-dev 执行前 `find work -type f -print` 与 `find delivery -type f -print` 均无输出，仅发现空目录；已用 `rmdir` 删除 `work/studies/quant-trading/local_backtest/`、清理后变空的 `work/` 父目录链、`delivery/` 下空子目录及 `delivery/` 本身；清理后 `work/` 与 `delivery/` 均不存在。meta-doc 已刷新 README / USER-MANUAL 的目录边界说明；meta-po 已复核文件系统与文档覆盖，无 BLOCKING；用户已于 2026-05-16 通过 CP8 人工终验。
- 人工确认门控：`checkpoints/STORY-004-LLD-CHECKPOINT.md` 已被批量 LLD 包门控取代；当前活动检查点为 `checkpoints/STORY-PACKAGE-LLD-CHECKPOINT.md`。
- LLD 输出门控：`process/handoffs/META-DEV-LLD-BATCH-REMAINING-2026-05-15.md` 已完成 9 个剩余 LLD 草案输出；meta-po 已完成批量 LLD / Story Package 聚合。
- 实现推进已完成：`STORY-004` 至 `STORY-013` 均已 verified。2026-05-16 Galileo 独立 meta-qa 对 `QA-IND-REQ-001 / F-004` 执行最小回归，`uv run --python 3.11 pytest -q tests/test_story_004_013.py::test_t_logging_minimal_01_cli_diagnostics` 结果 `1 passed`，`uv run --python 3.11 pytest -q` 结果 `10 passed`，`compileall` 通过；日志 REQUIRED 缺口已关闭。
- 文档阶段已收敛：`README.md` 与 `docs/USER-MANUAL.md` 已由 meta-doc 输出，meta-qa 后置文档复核 PASS，无 BLOCKING/REQUIRED 失败项；`process/TEST-STRATEGY.md`、`process/VERIFICATION-REPORT.md`、`process/DEVELOPMENT-PLAN.yaml` 与本文件已对齐 PASS / `CLOSED / REGRESSION_PASS` / delivered，历史 FAIL 记录仅作为可审计上下文保留。
- 全局限制执行结果：未写 `delivery/**`，未生成真实生产数据，未生成安装脚本；测试使用临时目录、fixture 或 fake runner。
- 下一状态：已交付 delivered；W3 真实数据源 `UNRESOLVED` 仍作为后续真实数据启用前风险处理。

## Documentation Readiness 路由

| 项 | 状态 | 说明 |
|---|---|---|
| QA documentation readiness | PASS | `process/handoffs/META-QA-DOCUMENTATION-READINESS-2026-05-16.md` 已支持进入 documentation；当前已收敛到 CP8 |
| 批量 LLD / Story Package 前置门控 | PASS | `checkpoints/STORY-PACKAGE-LLD-CHECKPOINT.md` 已确认通过，不阻塞 documentation |
| README / USER-MANUAL | PASS | 已由 meta-doc 输出到 `README.md` 与 `docs/USER-MANUAL.md`；本轮不修改正文 |
| 交付出口 | PASS | 用户已确认选项 2：仓库根 `README.md` + `docs/USER-MANUAL.md`，作为当前本地回测项目正式用户文档 |
| 后置 QA 文档复核 | PASS | `process/VERIFICATION-REPORT.md` 最新“文档后置 QA 复核报告：README / USER-MANUAL”结论 PASS，无 BLOCKING/REQUIRED；建议进入最终交付 / CP8 |
| CP8 交付就绪 | APPROVED / DELIVERED | meta-po 已刷新 CP8 自动预检与人工终验稿；用户已于 2026-05-16 回复 `通过`；CP8 已记录 `git status --short` 与允许范围，并继续跟踪 W3 真实数据源启用、`VALIDATION-ENV.yaml` 历史元数据滞后等非阻断项 |
| CR-001 目录结构收敛 | CLOSED / ACCEPTED / COMPLETED | meta-dev 已完成空目录核验与 `rmdir` 清理；meta-doc 已刷新 README / USER-MANUAL；meta-po 已复核 `work/` 与 `delivery/` 不存在、文档覆盖目录边界；无非空目录保留、无 BLOCKING；用户 CP8 终验已通过 |
