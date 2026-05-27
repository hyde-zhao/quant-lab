---
artifact: "CR-005 hs300 benchmark missing -> Tushare data-layer remediation review"
reviewer: "meta-dev"
lane: "lane-implementation"
round: 3
status: "completed"
governance_mode: "review-gated"
created_at: "2026-05-17"
change_id: "CR-005"
review_mode: true
---

# Review Findings

## 1. 审查范围

- 目标对象：CR-005 第三轮新增关注点：本地 `hs300_index` benchmark 缺失时，消费方仍返回 structured `unavailable` / `required_missing`，不得静默代理；数据补齐必须由数据层通过 Tushare 获取。
- 审查目标：CP5 LLD 可实现性、数据准确性和可用性、框架分层独立性、文件所有权与依赖合理性、LLD 强输入和测试缺口。
- 审查依据：`AGENTS.md` Review Gate / Story LLD 门控、`process/STATE.md`、CR-005 变更单、`process/HLD.md`、`process/STORY-BACKLOG.md`、`process/DEVELOPMENT-PLAN.yaml`、CR005-S01/S02/S03/S04/S06 Story、代码事实 `market_data/cli.py`、`market_data/source_registry.py`、`market_data/connectors/tushare.py`、`market_data/readers.py`、`engine/data_loader.py`。

## 2. Findings

<!-- findings-table -->

| ID | Severity | Rule Ref | Evidence | Impact | Suggestion | Anchor |
|----|----------|----------|----------|--------|------------|--------|
| F-MD-CR005-HS300-001 | BLOCKING | `CP5 implementability / explicit data-layer remediation entry` | HLD 只定义 generic `plan/fetch/normalize/validate` 流程和 benchmark 只读失败行为：`process/HLD.md:1060-1067`。CR005-S01 只写 `market_data/connectors/tushare.py`、`config.py`、`source_registry.py`、`runtime.py`、`storage.py`，没有拥有 `market_data/cli.py`：`process/stories/CR005-S01-tushare-connector-real-lake-writer.md:69-79`。CR005-S04 明确只读本地基准、缺失 unavailable / required_missing：`process/stories/CR005-S04-hs300-local-benchmark.md:72-86`。代码事实中 CLI 仍强制 `_require_prices`，真实 source 即使 `--enable-real-source` 也直接失败，且 Tushare registry 仅有 `prices.daily`：`market_data/cli.py:130-147`、`market_data/cli.py:177-193`、`market_data/source_registry.py:86-90`。 | 新关注点要求“消费方不补数，但数据层需要调用 Tushare 获取相关数据”。当前文档能阻止消费方静默代理，但没有给 CP5 LLD 一个明确的数据层补齐入口；S04 的 `available` 路径无法从缺失状态闭环到 Tushare 写湖。阻断 CR005-S01/S04 的 CP5 LLD 可实现性确认。 | 在 CP5 前由 meta-se/meta-po 修订正式设计或补充 Story：将 `market_data/cli.py` 或等价 job 纳入 S01/S02/S03 前置范围，定义 `plan/fetch/backfill/normalize/validate/catalog` 对 `hs300_index` 的显式命令、参数和结构化输出。最小契约应包含 `--dataset hs300_index`、`--source tushare`、`--interface hs300_index.daily` 或 exact Tushare 接口名、`--index-code 399300.SZ`、`--start-date`、`--end-date`、`--lake-root`、`--run-id`、`--resume-policy`、dry-run 输出、manifest 路径、quality/catalog 路径和错误枚举。消费方仍只能返回 `unavailable` / `required_missing`，不得在 resolver/Data Loader 内调用 connector。 | `process/HLD.md:1060`; `process/stories/CR005-S01-tushare-connector-real-lake-writer.md:73`; `market_data/cli.py:189` |
| F-MD-CR005-HS300-002 | BLOCKING | `Data Loader / benchmark resolver structured unavailable boundary` | HLD 在模块层声明 Readers / Benchmark Resolver 缺失时 structured unavailable：`process/HLD.md:973`，并声明缺 benchmark 返回 unavailable：`process/HLD.md:1055`、`process/HLD.md:1078`。但 CR005-S04 只定义 `resolve_hs300_benchmark(config)`，未定义 typed unavailable payload 字段和 Data Loader 交互：`process/stories/CR005-S04-hs300-local-benchmark.md:72-86`。代码事实中 `engine/data_loader.py` 仍以异常处理缺 parquet / quality 缺失，没有 structured `unavailable` 结果对象：`engine/data_loader.py:80-83`、`engine/data_loader.py:128-153`。 | 用户明确点名 Data Loader 与 benchmark resolver 缺数据时只返回 structured unavailable。当前文档没有说明 Data Loader 是否消费 benchmark resolver、是否不在 scope、或如何把 `ReaderBoundaryError` / missing parquet / quality fail 映射到 `benchmark_status=unavailable|required_missing`。阻断 S04 CP5 LLD；若直接实现，容易在 engine 层继续抛异常或诱导消费方补数。 | S04 LLD 前必须冻结 resolver 的 typed result，例如 `BenchmarkResult(status, dataset, source, index_code, start_date, end_date, coverage, quality_status, missing_reason, required, remediation_hint, catalog_entry, run_id)`；并明确 Data Loader 的边界二选一：A. Data Loader 不负责 benchmark，只由实验/benchmark resolver 返回结构化状态；B. Data Loader 需要暴露 benchmark metadata，则只能调用只读 resolver，不导入 connector，不联网。缺失状态必须包含 `required_missing` 分支和可审计的补齐建议，但补齐执行必须指向数据层 CLI/job。 | `process/stories/CR005-S04-hs300-local-benchmark.md:76`; `engine/data_loader.py:80` |
| F-MD-CR005-HS300-003 | REQUIRED | `Tushare exact field mapping / data accuracy` | HLD 将 `hs300_index` 映射为 `index_daily(ts_code='399300.SZ')`，最小字段只列 `trade_date`、`index_code`、`close`、`pct_chg`、`source`、`source_run_id`、`available_at`：`process/HLD.md:981`。S02 对 `hs300_index` 只要求 `trade_date + index_code`、`close`、lineage 和 `available_at`：`process/stories/CR005-S02-tushare-dataset-schema-normalization.md:73-81`。S02 又允许字段细节在 LLD 中用候选字段表达：`process/stories/CR005-S02-tushare-dataset-schema-normalization.md:132-134`。 | 对真实 benchmark 数据准确性而言，CP5 LLD 仍缺少 exact raw -> canonical 字段映射、日期格式、类型、单位、排序、去重、`ts_code` 到 `index_code` 的规范化、是否保留 `open/high/low/pre_close/change/vol/amount`、`pct_chg` 单位和缺失处理。该项不阻断 CP5 LLD 起草，但必须在 CP5 LLD 中冻结；未冻结则阻断实现。 | CR005-S02 LLD 必须加入 Tushare `index_daily` 字段映射表，至少覆盖 raw field、canonical field、type、nullable、unit、key、dedupe rule、sort rule、date parser、index code normalization、missing policy；同时给出正负例 fixture。若只需要 close 作为 benchmark，也应明确丢弃字段和理由，避免后续收益/指标误用未定义字段。 | `process/HLD.md:981`; `process/stories/CR005-S02-tushare-dataset-schema-normalization.md:77` |
| F-MD-CR005-HS300-004 | REQUIRED | `trade calendar / coverage denominator / availability` | HLD 定义 `trade_calendar` 用 `trade_cal`，最小字段为 `trade_date`、`exchange`、`is_open`、`pretrade_date`、`source_run_id`：`process/HLD.md:982`。S03 quality 要求 coverage 和 denominator，但未定义 `hs300_index` coverage 以哪个 exchange/open calendar 为分母，也未说明 `trade_calendar` 自身是否需要 `available_at`：`process/stories/CR005-S03-multidataset-quality-catalog-readers.md:74-89`。代码现状 Data Loader 只用本地 `trade_calendar` 过滤 open date：`engine/data_loader.py:160-168`。 | `hs300_index` 的可用性判断依赖交易日分母。若 `trade_cal` 的 exchange、开市日范围、补休日、停市日和 `index_daily` 覆盖不一致，quality 可能误报 pass 或 fail；若 calendar 缺 PIT/available 口径，也会影响回测日历可审计性。阻断实现，需在 S02/S03 LLD 中补齐。 | CR005-S03 LLD 必须定义 `hs300_index` coverage denominator：推荐使用 `trade_calendar(exchange=SSE/SZSE 或 CP5 冻结值, is_open=1)` 与请求区间交集；列出 no-open-day、partial calendar、index_daily 缺口、重复交易日、未来日期、非交易日记录的处理。若 `trade_calendar` 不参与信号 PIT，也应显式说明其 `available_at` 适用边界和可审计来源。 | `process/HLD.md:982`; `process/stories/CR005-S03-multidataset-quality-catalog-readers.md:76` |
| F-MD-CR005-HS300-005 | REQUIRED | `manifest / idempotency / resume / partial success contract` | HLD 与 S01 提到 plan/dry-run、raw/manifest 和 runtime 写湖：`process/HLD.md:1052`、`process/stories/CR005-S01-tushare-connector-real-lake-writer.md:77-79`。代码 runtime 已有 idempotency key、resume policy、partial_success、manifest 写入能力：`market_data/runtime.py:47-56`、`market_data/runtime.py:105-143`、`market_data/runtime.py:220-296`。但 CR005-S01/S02/S04 没有说明 `hs300_index` backfill 的 batch 切分、resume policy、partial_success 对 quality/catalog 的传播、重复 run 的覆盖策略。 | 对 2015-2025 回补，缺少 resume / idempotency 强契约会导致重复写 raw、manifest 与 canonical 不可追溯，或缺口修复后 catalog 仍指向旧失败 run。该项不阻断 LLD 起草，但阻断真实 Tushare 实现和可用性验收。 | CR005-S01/S02/S03 LLD 应把现有 runtime 能力落到 `hs300_index`：按日期窗口或接口限额切 batch，明确 `idempotency_key` 输入、`ResumePolicy(success=skip, failed=retry, partial_success=retry)` 或等价值、重复 manifest 处理、partial_success quality 状态、raw checksum 到 canonical/gold/catalog 的 lineage、补跑后 catalog latest 指针更新规则。 | `process/stories/CR005-S01-tushare-connector-real-lake-writer.md:78`; `market_data/runtime.py:47` |
| F-MD-CR005-HS300-006 | REQUIRED | `file ownership / wave dependency consistency` | Story Backlog 与 Development Plan 将 CR005-S04 置于 S03 后，并禁止 S04 修改 `market_data/connectors/**`：`process/STORY-BACKLOG.md:80-85`、`process/DEVELOPMENT-PLAN.yaml:781-835`。S03/S04 都将 `market_data/readers.py` 标为 shared 且 `file_conflict_free=false`：`process/DEVELOPMENT-PLAN.yaml:746-775`、`process/DEVELOPMENT-PLAN.yaml:808-835`。`market_data/cli.py` 的 CR-005 所有权却在 S05 comparison/文档 Wave，而 S05 位于 S04 后：`process/DEVELOPMENT-PLAN.yaml:836-890`。 | S01/S02/S03/S04/S06 的分层方向总体合理：connector 写湖、reader/benchmark 只读、Backtrader 后置。但“数据层调用 Tushare 补齐 hs300_index”的实现文件很可能是 CLI/job/source registry，当前 CLI 所有权晚于 S04，导致 S04 的 `available` 路径缺前置补齐能力。 | 将 `market_data/cli.py` 或等价 backfill job 的主所有权移到 S01/S02/S03，或新增 S01b/S03b Story 并使 S04 runtime/contract 依赖它。S03/S04 对 `market_data/readers.py` 的 shared 写入应串行：S03 冻结 reader status/error contract，S04 只消费或薄扩展 benchmark resolver，避免同一 CP5 批次并行写同一文件。 | `process/DEVELOPMENT-PLAN.yaml:861`; `process/DEVELOPMENT-PLAN.yaml:781` |
| F-MD-CR005-HS300-007 | RECOMMENDED | `benchmark口径 open item` | HLD 和 S04 均标记 `CR5-Q2` OPEN：沪深 300 采用价格指数、全收益指数或其他口径尚未确认：`process/HLD.md:1138-1139`、`process/stories/CR005-S04-hs300-local-benchmark.md:122-124`。 | 该项不阻断 `unavailable` / `required_missing` 结构实现，但会阻断真实 available 口径解释和对照报告准确性。 | 在 S04 LLD 中保留 `benchmark_variant` 或 `benchmark_policy` 字段，默认只支持 CP5 冻结的 `399300.SZ` 价格指数；若未来全收益指数接入，必须作为新 exact dataset/interface 或 policy，而不是复用同一 catalog entry。 | `process/stories/CR005-S04-hs300-local-benchmark.md:124` |
| F-MD-CR005-HS300-008 | RECOMMENDED | `structured error vocabulary` | 文档分散使用 `ConnectorError`、`ReaderBoundaryError`、`unavailable`、`required_missing`、`backend_unavailable`、`quality failed`，但未集中定义状态枚举和跨层映射。S04 只列举 status 名称：`process/stories/CR005-S04-hs300-local-benchmark.md:86`；S06 列举 `backend_unavailable`：`process/stories/CR005-S06-backtrader-optional-backend.md:88-103`。 | LLD 实现时不同模块可能各自拼字符串，影响消费方判断、测试断言和报告可读性。 | 在 CR005-S03 或 S04 LLD 中集中定义 `DataAvailabilityStatus` / `BenchmarkStatus` / `BackendStatus` 的枚举、错误字段、HTTP-like retryability 或 remediation 分类，并要求 CLI、reader、resolver、experiment metadata、Backtrader adapter 复用。 | `process/stories/CR005-S04-hs300-local-benchmark.md:86` |
| F-MD-CR005-HS300-009 | OBSERVATION | `framework layering` | HLD 明确拒绝 Tushare 直接接入 Data Loader / 实验 / Backtrader：`process/HLD.md:948-949`，S03 reader 禁止 connector/runtime/storage：`process/stories/CR005-S03-multidataset-quality-catalog-readers.md:81-89`，S06 Backtrader 禁止读取 token、导入 connector、联网、生成 PIT 或复权：`process/stories/CR005-S06-backtrader-optional-backend.md:92-103`。代码现状 `market_data/readers.py` 只导入 catalog/contracts/layout/pandas，未导入 connector/runtime；`engine/data_loader.py` 未导入 `market_data.connectors`：`market_data/readers.py:1-12`、`engine/data_loader.py:13-21`。 | 分层原则整体合理，能够保护消费方只读本地事实源和 Backtrader optional 后端的独立性。主要缺口不是方向错误，而是数据层补齐入口和结构化状态契约不够具体。 | 保持当前分层：resolver/Data Loader/Backtrader 永不调用 Tushare connector；Tushare 只由 `market_data` CLI/job/source registry 进入 raw/manifest/canonical/quality/catalog 链路。 | `process/HLD.md:948`; `market_data/readers.py:10` |

## 3. 汇总结论

- blocking_count: 2
- required_count: 4
- optional_count: 2
- recommended_next_action: `revise-cr005-design-before-cp5-lld`

### 门控结论

当前文档方向正确，但不足以直接进入 CR-005 CP5 LLD 批次确认。主要阻断点是：消费方 structured unavailable 已写清，但“缺失后由数据层调用 Tushare 补齐 hs300_index”的 CLI/job/source registry 契约没有落到可执行 Story 和文件所有权上；Data Loader 与 benchmark resolver 的 typed unavailable / required_missing 输出也未冻结。

在正式方案修订或补充 Story 后，可以进入 CP5 LLD 起草；在 exact Tushare 字段映射、trade calendar coverage、resume/idempotency、quality/catalog 状态传播和测试清单冻结前，不应进入实现。

### CP5 LLD 必补强输入

| 范围 | 必补输入 | 阻断对象 |
|---|---|---|
| S01/S02/S03 | `hs300_index` 数据层 backfill 命令/job、参数、dry-run 输出、真实 fetch 输出、错误枚举、resume policy、manifest lineage、quality/catalog 更新规则 | CP5 LLD |
| S04 | `BenchmarkResult` typed schema、`unavailable` / `required_missing` 映射、Data Loader 是否参与 benchmark 的边界决策 | CP5 LLD |
| S02 | Tushare `index_daily` raw -> canonical exact 字段映射、类型、单位、日期解析、dedupe、`index_code` normalization | 实现 |
| S03 | `trade_calendar` denominator、coverage 算法、quality fail/warn/pass 阈值、catalog latest 指针策略 | 实现 |
| S06 | Backtrader benchmark unavailable 行为只读化：只报告对照缺失，不触发补数、不联网 | 实现 |

### 最小测试要求

| 测试项 | 覆盖目标 |
|---|---|
| `resolve_hs300_benchmark` 缺本地 canonical/gold | 返回 `status=unavailable`，不导入 connector，不写 raw/manifest |
| `require_benchmark=true` 且缺本地基准 | 返回 `status=required_missing`，实验 metadata 可审计，不静默代理 |
| 缺基准后的补齐入口 | CLI/job dry-run 输出 `dataset=hs300_index`、`source=tushare`、接口、日期范围、batch_count、lake_root、manifest/quality/catalog 目标，不联网 |
| Tushare disabled / missing token / interface not allowlisted | 结构化错误，不写 raw，不泄露 token |
| Tushare `index_daily` fixture normalization | exact 字段映射、重复 key、缺 `close`、日期非法、`pct_chg` 单位校验 |
| trade calendar coverage | open-date 分母、缺口、非交易日记录、请求区间无 open day |
| resume/idempotency | success skip、failed retry、partial_success retry、重复 manifest 行处理、catalog latest 更新 |
| quality/catalog gate | `fetch_status` 与 `dataset_status` 分离；fetch failed + dataset pass 可读，dataset fail 阻断 |
| static import scan | `engine/data_loader.py`、`market_data/benchmarks.py`、实验入口、Backtrader adapter 对 `market_data.connectors` / `market_data.runtime` 导入次数为 0 |

## 4. 待确认项

- `hs300_index` 真实口径：是否冻结为 Tushare `index_daily(ts_code='399300.SZ')` 价格指数，还是需要全收益指数或另一个 exact dataset/interface。
- 数据层补齐入口归属：将 `market_data/cli.py` 移入 CR005-S01/S02/S03，还是新增独立 backfill Story 并作为 CR005-S04 前置依赖。
- Data Loader 是否要暴露 benchmark metadata：若要暴露，必须只调用只读 resolver；若不暴露，S04 需要明确 Data Loader 不在 benchmark resolver 调用链内。
- 真实 lake root 与 `.gitignore` 策略仍为 OPEN；该项会阻断真实数据写入实现，不阻断 structured unavailable 设计。
