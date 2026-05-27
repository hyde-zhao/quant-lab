# Data Lake Full-History Backfill Roadmap

## Boundary

本路线图只描述后续授权门、阶段顺序和 release criteria。当前状态不授权真实 provider fetch、真实 lake 写入、凭据读取、旧 `data/**` 读取、旧报告覆盖、DuckDB 依赖引入、`.duckdb` 文件写入、catalog current pointer publish 或可直接执行的 backfill 命令。

CR014 Batch-A 已完成 `CR014-S01` 至 `CR014-S08` 的 CP7 验证，交付范围是离线合同与护栏实现。真实 provider 抓取、raw / manifest / run metadata 写湖已拆到 `CR014-S09-windowed-real-fetch-lake-write-run`，属于后续 Batch-B，不属于 Batch-A 授权范围。

| 字段 | 值 |
|---|---|
| current_status | `roadmap_and_batch_a_contracts_verified` |
| batch_a_status | `S01..S08 verified offline contracts and guardrails` |
| batch_b_status | `S09 planned / not_authorized` |
| supported_limited_window | `2025-02-11..2026-02-18` |
| prior_blocked_window | `2020-01-01..2024-12-31` |
| cr014_target_scope | `all_a_share_since_inception_or_list_date_to_last_closed_trade_date` |
| source_of_truth | `Parquet lake + manifest + catalog current pointer` |
| duckdb_role | `read-only query / audit / parity candidate only` |
| duckdb_dependency_change | `0` |
| duckdb_source_of_truth_files | `0` |
| full_history_status | `research_limited_only_until_real_S09_windows_and_publish_gates_complete` |
| future_run_id_rule | `new run_id and new report / evidence directory required` |

## Source of Truth and Publish Boundary

Parquet lake、manifest 和 catalog current pointer 是事实源。DuckDB query result、DuckDB view、parity report、quality/readiness report、pandas/pyarrow audit result 或临时 candidate evidence 都不能自动成为 current truth。

用户侧链路保持：

```text
plan -> run -> normalize/replay -> validate -> publish -> read/query
```

| 阶段 | 写入 / 输出 | 是否更新 current pointer | 边界 |
|---|---|---:|---|
| `plan` | plan spec、window plan、dry-run evidence | 0 | 不联网、不写湖、不读凭据。 |
| `run` | raw、manifest、run metadata、run-scoped audit | 0 | 只允许在后续 S09 Batch-B 且 per-run 授权齐全时真实写入。 |
| `normalize/replay` | canonical / gold / quality candidate、replay evidence | 0 | 只从 raw / manifest 派生；raw 缺失不补抓。 |
| `validate` / parity | readiness matrix、gap register、parity / audit evidence | 0 | PASS 只代表候选或证据通过，不自动 publish。 |
| `publish` | catalog current pointer、published metadata、known limitations | 1 | 只有 Explicit Publish Gate 可以更新 current pointer。 |
| `read/query` | reader output、DuckDB read-only query / audit result | 0 | 只读 published current truth 或受控 candidate audit path。 |

## CR014 Batch-A Verified Scope

| Story | 已验证范围 | 真实操作状态 |
|---|---|---|
| `CR014-S01` | 全 A universe / lifecycle / code-change 合同 | provider / lake / credential counters 全 0 |
| `CR014-S02` | Parquet layout、manifest、catalog current pointer、Explicit Publish Gate | validate / parity 不自动 publish；真实 current pointer publish 为 0 |
| `CR014-S03` | P0 `plan -> run -> normalize/replay -> validate -> publish -> read/query` 合同 | 真实抓取和 raw / manifest 写湖拆到 S09；S03 不执行 |
| `CR014-S04` | DuckDB read-only query / audit / parity boundary | 不引入 DuckDB 依赖、不写 `.duckdb`、不成为 source of truth |
| `CR014-S05` | full-history readiness matrix、gap register、claim boundary | 任一 P0 gate 未过时 full-A allowed claim 为 0 |
| `CR014-S06` | incremental refresh、replay、retention dry-run contract | replay 不 provider fetch、不读凭据、不写 raw、不改 current pointer；retention 默认 dry-run |
| `CR014-S07` | research consumer read-only contract 和 docs/runbook metadata | consumer 不扫 candidate、不 publish、不 fetch、不读凭据、不写 DuckDB |
| `CR014-S08` | W3 / minute / tick / Level2 / VWAP blocked decision boundary | production allowed claim count 为 0 |

Batch-A 不能被解释为真实全 A production current truth 已存在，也不能被解释为 S09 授权、publish 授权或 DuckDB 依赖授权。

## S09 Batch-B Authorization Gate

`CR014-S09-windowed-real-fetch-lake-write-run` 是后续 Batch-B，用于分时段真实 provider 抓取与 raw / manifest / run metadata 写湖。它必须在所有门禁满足后才能执行。

| 门禁 | 必须状态 |
|---|---|
| 上游 Story | `CR014-S01` 至 `CR014-S08` 已 verified。 |
| S09 LLD | `approved`。 |
| S09 CP5 | 自动预检 PASS 且人工确认 `approved`。 |
| per-run authorization | 每次真实 run 都有用户提供的 `authorization_id`。 |
| 授权字段 | 明确 dataset、date range、source/interface allowlist、lake root、window policy、resume policy、rollback policy。 |
| 写入范围 | 只允许写 raw、manifest、run metadata 和 run-scoped audit。 |
| 禁止连跳 | S09 不自动 normalize、validate、publish、retention execute 或更新 current pointer。 |

无 `authorization_id` 或授权字段不完整时，S09 必须 fail-closed：`provider_fetch=0`、`lake_write=0`、`credential_read=0`、`catalog_current_pointer_publish=0`。

## Roadmap Stages

| stage_id | scope | current_authorization_status | required_gate | release_criteria |
|---|---|---|---|---|
| `BA-01` | `offline_contracts_guardrails` | `verified` | 已完成 S01..S08 CP7 | 离线合同、护栏、counter 与 docs boundary 可追溯。 |
| `S09-01` | `windowed_real_fetch_raw_manifest_run_metadata` | `not_authorized` | S09 LLD approved + S09 CP5 approved + per-run `authorization_id` | 授权窗口内 raw、manifest、run metadata 可追溯；current pointer changes=0。 |
| `FH-01` | `normalize_replay_candidates` | `authorization_required_after_S09` | S09 输出可用 + 独立 run gate | canonical / gold / quality candidate 覆盖授权 dataset/window，不 publish。 |
| `FH-02` | `readiness_audit` | `authorization_required` | 候选完成后 QA / CP7 | readiness matrix 和 gap register 明确 P0 gate、lifecycle、claim boundary。 |
| `FH-03` | `explicit_publish` | `authorization_required` | Explicit Publish Gate | 质量策略、lineage checksum、known limitations 与 publish intent 均满足后才更新 current pointer。 |
| `FH-04` | `research_read_query` | `after_publish_only` | published current pointer 可读 | research consumer 只读 published current truth / clean reader output / structured claim metadata。 |
| `VWAP-01` | `execution_vwap_enablement` | `not_authorized` | 单独 source/interface + Story + CP5 + 用户显式授权 | 真实 `vwap` 字段、`vwap_status=available`、execution audit pass。 |
| `MICRO-01` | `minute_tick_level2_order_match` | `not_authorized` | 单独 source/interface + Story + CP5 + 用户显式授权 | minute / tick / Level2 / order book / order match 数据合同与审计通过。 |

## P0 Current Truth Release Criteria

CR014 的 P0 current truth 默认关注 7 类正式数据集，并要求 lifecycle / code-change 作为全 A denominator 前置能力。W3 和微观结构能力不因 Batch-A 自动进入 production allowed claim。

| dataset / capability | required_current_truth | release_gate |
|---|---|---|
| `prices` | 覆盖证券自存在 / 上市日起至最近已闭市交易日的日频价格 | S09 窗口完成 + readiness pass + Explicit Publish Gate |
| `adj_factor` | 覆盖目标窗口且 PIT available_at / adjustment policy 可审计 | S09 窗口完成 + readiness pass + Explicit Publish Gate |
| `hs300_index` | 覆盖目标窗口的真实 benchmark | S09 窗口完成 + readiness pass + Explicit Publish Gate |
| `trade_calendar` | 覆盖目标窗口且 calendar-known / next-open 语义明确 | S09 窗口完成 + readiness pass + Explicit Publish Gate |
| `index_members` | `snapshot_asof` PIT membership 覆盖目标窗口 | S09 窗口完成 + readiness pass + Explicit Publish Gate |
| `index_weights` | 权重行与 as-of membership 对齐，不替代 PIT membership | S09 窗口完成 + readiness pass + Explicit Publish Gate |
| `stock_basic` | lifecycle / listed / delisted / code-change gate 覆盖目标窗口 | S09 窗口完成 + readiness pass + Explicit Publish Gate |
| `trade_status` / `prices_limit` / `events` | W3 数据可作为后续约束能力，但 source/interface 与 available_at 必须单独确认 | 未确认前 production allowed claim 为 0 |

## Execution / VWAP / W3 Release Criteria

- W3 / minute / tick / Level2 / order book / order match / execution detail / real VWAP / VWAP fill / microstructure impact cost 的 `production_allowed_claim` 当前均为 `false`，计数为 0。
- close proxy 只能表达 `research_degradation`，不能声明真实 VWAP 或真实执行价。
- `amount/volume` 派生 VWAP 必须 fail-closed，不能解除真实 VWAP blocked claim。
- 解除真实 VWAP 必须同时具备 source/interface、独立 Story、CP5、用户显式授权、真实 `vwap` 字段、`vwap_status=available` 和 execution audit pass。
- 分钟、逐笔、Level2、盘口、委托、成交明细和真实撮合数据必须有单独数据合同、CP5 和用户显式授权。

## Research Consumer Boundary

研究消费层只能消费：

| 允许输入 | 说明 |
|---|---|
| published current truth | catalog current pointer 指向的 canonical / gold / quality truth。 |
| clean reader output | 已完成 schema、PIT、quality、复权和 claim boundary 校验的 reader / clean feed。 |
| structured claim metadata | `allowed_claims`、`blocked_claims`、`required_missing`、permission counters、DuckDB audit evidence refs。 |

研究消费层不得执行以下操作：扫描 candidate lake、publish、fetch provider data、读取凭据、读取旧 `data/**` 当 truth、覆盖旧 reports、打开或写入 DuckDB、创建 `.duckdb` source-of-truth 文件、把 DuckDB view / SQL result / parity PASS 当作 current truth。

## Authorization Matrix

| operation_kind | current_status | required_approval | forbidden_until_authorized |
|---|---|---|---|
| `provider_fetch` | `not_authorized` | S09 LLD + S09 CP5 + per-run `authorization_id` | provider fetch |
| `raw_manifest_run_metadata_write` | `not_authorized` | S09 LLD + S09 CP5 + per-run `authorization_id` | raw / manifest / run metadata lake write |
| `canonical_gold_quality_candidate_write` | `authorization_required_after_S09` | 独立 run gate / QA scope | candidate write outside authorized window |
| `catalog_current_pointer_publish` | `not_authorized` | Explicit Publish Gate | current pointer update |
| `credential_read` | `not_authorized` | per-run user authorization and environment-only credential policy | `.env` / token / password / cookie / session read |
| `duckdb_dependency_change` | `not_authorized` | 独立 ADR / Story / CP5 | `pyproject.toml` / `uv.lock` DuckDB change |
| `duckdb_write_or_dotduckdb` | `not_authorized` | 独立 ADR / Story / CP5 | DuckDB write, `.duckdb` source-of-truth file |
| `legacy_data_read` | `not_authorized` | 单独 Story / CP5 / 用户显式授权 | old `data/**` read / list / copy / migrate / compare / delete |
| `old_report_overwrite` | `not_authorized` | 单独 Story / CP5 / 用户显式授权 | old report overwrite |
| `retention_execute` | `not_authorized` | 独立 execute authorization + backup verification | delete / archive / migrate |

## Evidence Retention

- 后续补齐必须使用新 `run_id`、新 evidence directory 或版本化文件。
- 旧 `reports/data_lake_readiness_2020_2024/*`、`reports/data_lake_readiness_limited_2025_2026/*` 和 `reports/data_lake_readiness_2020_2024_cr013/*` 保持只读证据。
- `old_baseline_preserved=true` 是 release criteria 的一部分。
- S09 每个窗口必须保留 manifest、checksum、resume token、status、authorization_id 和 rollback policy 引用。
- publish 记录必须保留 `published_at`、`latest_manifest_run_id`、lineage checksum、coverage denominator、known limitations 和 explicit publish evidence。

## Forbidden Operation Counters

Batch-A 当前计数如下；后续 S09 或 publish 只有在对应授权门通过后才能改变相关计数，并且必须写入 run-scoped evidence。

| counter | value |
|---|---:|
| provider_fetches | 0 |
| lake_writes | 0 |
| credential_reads | 0 |
| legacy_data_reads | 0 |
| old_report_overwrites | 0 |
| duckdb_dependency_changes | 0 |
| duckdb_writes | 0 |
| duckdb_source_of_truth_files | 0 |
| catalog_current_pointer_publishes | 0 |
| s09_real_executions | 0 |

## Residual Risks

| 风险 | 当前处理 |
|---|---|
| Batch-A verified 被误读为全 A 数据已可用 | 文档明确 Batch-A 是离线合同与护栏，不是真实回补或 publish。 |
| validate / parity PASS 被误读为可读 current truth | 只有 Explicit Publish Gate 更新 current pointer；candidate 仍不可作为 truth。 |
| DuckDB 被误读为事实源 | DuckDB 只读，且当前无依赖、无 `.duckdb`、无 write path；事实源仍是 Parquet/catalog。 |
| S09 被提前执行 | S09 必须等 LLD、CP5 和 per-run authorization；Batch-A 不授权真实执行。 |
| W3 / VWAP / 微观结构声明被放宽 | production allowed claim 保持 0；解除需 future source/interface + Story + CP5 + explicit authorization。 |
