---
artifact: "CR006 Data Contract CP5 Context"
owner: "meta-se"
agent_name: "se-wei"
status: "complete"
created_at: "2026-05-19"
change_id: "CR-006"
batch_id: "CR006-BATCH-A"
checkpoint: "CP5"
classification: "minor_doc_fix_before_cp5"
source_handoff: "process/handoffs/META-SE-CR006-DATA-CONTRACT-CP5-CONTEXT-2026-05-19.md"
hld_refresh_required: false
story_replan_required: false
cp3_rerun_required: false
cp4_rerun_required: false
cp5_approved: false
implementation_allowed: false
---

# CR006 数据分层、存储格式与对外接口契约 - CP5 审查上下文

## 1. 结论

本文件是 CR006-BATCH-A 的 CP5 前审查上下文附录，只汇总既有 HLD、ADR、LLD、CP5 自动预检和 post-fix 评审中的事实，用于帮助 CP5 人工确认时集中审查“数据分层、存储格式与对外接口契约”。

本文件不是 HLD 刷新，不是 ADR 刷新，不新增架构决策，不改变 Story 边界、Story DAG、文件所有权、dev gate 或实现顺序，不触发 CP3/CP4 重跑，不修改 CP5 自动预检和 CP5 人工稿，不批准 CP5，不允许进入实现。

完成本附录后，CR006 可交回 meta-po 恢复 CP5 人工确认；是否批准 CP5 仍必须由用户在 CP5 人工确认中决定。

## 2. 数据分层总览

| 分层 | 事实来源 | 职责 | 主要产物 | Allowed Consumers | Forbidden Consumers |
|---|---|---|---|---|---|
| acquisition / raw-manifest audit | HLD §23、ADR-011、ADR-018、S01 LLD | Tushare-first 采集、dry-run、断点续传、审计、复现、质量追溯。raw/manifest 是审计与派生链路事实层，不是 runtime 价格输入面。 | raw artifact、manifest record、runbook summary | Tushare 采集 job、normalization/replay、quality/catalog、审计与排障流程 | 轻量回测 runtime、Backtrader runtime、experiments/notebook runtime、旧 data fallback、覆盖率证明 |
| normalization / quality / catalog / gold | HLD §23、HLD §22、ADR-011、ADR-014、ADR-018、S01/S02/S03 LLD | 将 raw/manifest 归一化为 canonical/gold，执行 schema、coverage、quality、PIT、复权一致性检查，并向 reader 暴露可消费状态。 | canonical parquet、quality records、catalog entries、gold dataset | quality gate、catalog、canonical/gold reader、轻量 engine adapter、Backtrader clean feed reader | 直接绕过 quality gate 的 runtime、以旧 data 补缺、connector/runtime 反向写入 |
| runtime adapter / feed | HLD §23、ADR-018、S02/S03 LLD | 面向轻量 engine 与 Backtrader 暴露只读运行时输入。轻量 P0 读 canonical/gold；external legacy_flat 仅为可选兼容派生；Backtrader 读 clean feed。 | `LightweightInputResult`、optional external `legacy_flat`、`BacktraderCleanFeedBundle` | 轻量回测、experiments、Backtrader backend selector/adapter、只读 validator | raw/manifest 直接读取、Tushare fetch/backfill、token/.env 读取、lake write、旧 repo data fallback |
| old data reference-only | HLD §23、ADR-018、S04 LLD | 将仓库内旧 `data/` 明确降级为 reference-only，仅可人工参考或另行授权比对。 | reference-only 文档合同、guardrail allowlist/denylist | `manual_reference`、`separately_authorized_comparison` | `fallback`、`migration_source`、`copy_source`、`coverage_proof`、`test_fixture`、`smoke_precondition` |

## 3. 存储格式与布局契约

下表只汇总既有合同。`<MARKET_DATA_LAKE_ROOT>`、`<external-data-root>`、`<repo>` 均为占位表达，不记录或推断真实私有路径。本附录不新增目录结构或分区策略。

| 对象 | format | layout / partition | primary key / uniqueness | required fields | lineage fields | allowed consumers | forbidden consumers |
|---|---|---|---|---|---|---|---|
| raw | Tushare 原始响应 artifact，S01 允许 JSON/JSONL 或等价 raw 存储形态 | `<MARKET_DATA_LAKE_ROOT>/raw/...`，由采集 job/storage 规划；属于 structured lake raw 层 | `run_id`、`batch_id`、`source_interface`、`raw_checksum` 组合用于审计唯一性；不作为业务主键 | `source`、`source_interface`、`params` 或 `params_hash`、`run_id`、`batch_id`、`raw_row_count`、`raw_checksum`、`status` | `source`、`source_interface`、`run_id`、`batch_id`、`raw_checksum`、request params | Tushare job、storage writer、normalization/replay、审计、排障 | 轻量回测、Backtrader、experiments runtime、old data coverage proof、test fixture |
| manifest | append-only manifest record，JSONL/manifest 记录或等价结构化记录 | `<MARKET_DATA_LAKE_ROOT>/manifest/...`；属于 structured lake manifest 层 | `manifest_run_id` 或 `run_id + batch_id + source_interface`；重复成功批次必须按 S01 resume policy fail fast | ADR-011 要求的 `schema_version`、`run_id`、`batch_id`、`source`、`interface`、`params`、`requested_at`、`attempts`、`status`、`raw_path`、`canonical_path`、错误字段、时间字段 | `manifest_run_id`、`run_id`、`source`、`source_interface`、`raw_path`、`canonical_path`、`raw_checksum`、`status` | resume、audit、normalization、quality、catalog、runbook summary | 轻量 engine runtime、Backtrader runtime、价格 reader、old data fallback |
| canonical | dataset-specific parquet / DataFrame contract | `<MARKET_DATA_LAKE_ROOT>/canonical/<dataset>/...` 或等价 canonical 层布局 | dataset-specific：`prices = trade_date + symbol`；`hs300_index = trade_date + index_code`；`trade_calendar = trade_date + exchange`；`index_weights = trade_date + index_code + con_code`；`adj_factor = trade_date + symbol`；`stock_basic = symbol + effective_date/available_date` | HLD §22.4 dataset 字段集：prices OHLC/adjusted OHLC/adj_factor/vol/amount/adjustment_policy；benchmark、calendar、index_weights、adj_factor、stock_basic 对应字段；所有 dataset 需满足 schema 与 quality gate 输入要求 | `source`、`source_interface`、`source_run_id`、`schema_version`、`manifest_run_id`、`lineage_raw_checksum` 或等价 lineage、`available_at` | quality/catalog、gold builder、S02 canonical/gold reader、S03 clean feed reader、experiments 只读 reader | connector/runtime 直接写入、绕过 quality gate 的 runtime、旧 data 补缺、raw/manifest 伪装 reader |
| quality | CSV/records 或等价质量记录 | `<MARKET_DATA_LAKE_ROOT>/quality/...`；按 dataset/run/gate 可定位 | `dataset + run_id + threshold profile + coverage window` 或等价质量 gate 标识 | ADR-014 要求的 `fetch_status`、`dataset_status`、coverage、thresholds、denominator、run/source/interface；需表达缺失字段、重复、异常价格、覆盖缺口、PIT/复权检查状态 | `run_id`、`source`、`source_interface`、`manifest_run_id`、`raw_checksum`、catalog reference | catalog、reader gate、S01 runbook、S02 adapter、S03 validator、QA 审查 | 忽略 quality gate 的 runtime、以旧 data 覆盖 quality 失败、silent fallback |
| catalog | JSON 首轮可接受，或等价 catalog entry | `<MARKET_DATA_LAKE_ROOT>/catalog/...`；按 dataset/schema/latest manifest 可定位 | `dataset + schema_version + latest_manifest_run_id` | ADR-011 要求的 `dataset`、`schema_version`、`coverage`、`quality_status`、`latest_manifest_run`；需可定位 quality 与 canonical/gold | latest manifest run、quality path/status、schema version、coverage、source/interface 摘要 | canonical/gold reader、轻量 adapter、Backtrader clean feed reader、runbook summary | runtime 修改 catalog、绕过 catalog 状态读取旧 data、将 catalog 当作数据源替代 parquet |
| gold | quality-gated parquet / DataFrame contract | `<MARKET_DATA_LAKE_ROOT>/gold/...`；由 canonical 归一化和质量门禁后生成 | dataset-specific，继承 canonical 主键或清洗后的 feed key | clean OHLCV、factor/score、calendar、benchmark status、adjustment policy、PIT evidence、quality status；字段按 S02/S03 请求面裁剪 | `source_run_id`、`source_interface`、`manifest_run_id`、`schema_version`、`lineage_raw_checksum`、quality/catalog reference | S02 lightweight canonical/gold reader、S03 Backtrader clean feed reader、experiments 只读 reader | raw/manifest 直接替代、connector/runtime 写入、旧 data fallback、未过 quality gate 的 Backtrader 输入 |
| external `legacy_flat` | optional flat parquet；HLD 示例含 `prices.parquet`、`index_members.parquet`、`trade_calendar.parquet` | 显式外置 `legacy_flat_dir`，位于仓库外；不得默认指向 `<repo>/data` | 继承 canonical/gold dataset 主键；派生批次需具备 lineage 唯一性 | flat 兼容字段、派生时间、source dataset、quality status、schema version | `LegacyFlatLineage`：source dataset、quality status、schema version、run/source/interface/catalog lineage | 仅在显式启用兼容模式时供轻量 engine 读取；S02 P0 不依赖它 | 默认/P0 输入、Backtrader 默认输入、source of truth、repo data fallback、从旧 data 复制 |
| Backtrader clean feed | in-memory typed bundle / DataFrame contract；不要求持久化 | 无持久化布局要求；由 `read_backtrader_clean_feed(...)` 或等价只读 reader 返回 | request identity + dataset/date/symbol/quality policy；OHLCV 内部按 `trade_date + symbol` 唯一 | `ohlcv` 中 `trade_date`、`symbol`、`open`、`high`、`low`、`close`、可选 `volume`；还包含 `factor_panel`、`score`、`calendar`、`benchmark_status`、`quality_summary`、`pit_evidence`、`adjustment_evidence`、`lineage`、status | dataset、source/interface、manifest run、raw checksum 摘要、quality/catalog reference、PIT/adjustment evidence | S03 Backtrader backend selector/adapter、in-memory validator | raw/manifest runtime read、旧 repo `data/**` read、Tushare connector、token/.env、lake write、normalize/revalidate/replay job |
| repo `data/` | legacy local files，格式不作为 CR006 新合同事实 | `<repo>/data/`，仅 reference-only；本附录不读取、不列出、不比较真实内容 | 不建立 CR006 runtime uniqueness 合同 | 不声明字段可用性；不得作为质量、覆盖或 fixture 证据 | unknown / untrusted；仅可在另行授权比对中注明来源 | 人工参考、另行授权比对 | fallback、migration source、copy source、coverage proof、test fixture、smoke precondition、runtime input |

## 4. 对外接口契约

| 接口 | 调用方 / 调用时机 | 输入契约 | 输出契约 | 失败与 typed errors | 禁止行为 |
|---|---|---|---|---|---|
| Tushare job -> raw/manifest | 用户显式运行 S01 runbook/CLI/job；默认 dry-run；真实采集需凭据、allowlist、source enabled 与显式确认 | `TushareFirstRunSpec`：dataset、source=`tushare`、source_interface、start/end、lake_root 占位、credential_env 名称、run_id、resume_policy、dry_run | raw artifact、manifest record、safe summary；dry-run 输出计划而不写真实 lake | `interface_not_allowed`、`unknown_dataset`、`invalid_date_range`、`missing_credential`、`source_disabled`、`resume_conflict`、remote/quota 类错误 | runtime 自动触发采集；打印 token；记录真实私有路径；把旧 data 作为输入或 fallback |
| raw/manifest -> canonical/gold | normalization、quality、catalog 数据层 job；由采集链路或明确数据任务触发 | raw path/checksum、manifest_run_id、schema_version、dataset mapping、date range、quality policy | canonical parquet、quality records、catalog entries、gold dataset；失败时提供可复现 lineage | `schema_mismatch`、`lineage_unavailable`、`quality_failed`、required dataset missing | 用旧 `data/` 补缺；绕过 manifest lineage；将 raw/manifest 暴露给轻量或 Backtrader runtime |
| canonical/gold -> lightweight engine | S02 reader/data loader/experiments 在 runtime 只读调用；P0 默认 canonical/gold | `LightweightInputRequest`：dataset、start/end、symbols、adjustment_policy、quality_policy、`input_mode=canonical_gold`；optional `legacy_flat` 需显式启用和外置目录 | `LightweightInputResult`：`ok|required_missing|quality_failed|lineage_missing|invalid_request`，含 bundle 与只读 remediation job spec | `required_missing`、`quality_failed`、`lineage_missing`、`invalid_request` | 自动 fetch/backfill；读取 raw/manifest；读取 repo `data/`；把 optional `legacy_flat` 当 P0 必需项 |
| canonical/gold -> Backtrader clean feed | S03 explicit backend selector/adapter；只读 clean feed reader 与 in-memory validator | clean feed request，包含 dataset/date/symbol、quality policy、PIT/as-of、adjustment policy、benchmark requirement | `BacktraderCleanFeedBundle` 或 structured unavailable status；包含 OHLCV、factor/score、calendar、benchmark、quality、PIT、adjustment、lineage | `backend_unavailable`、`dependency_missing`、`input_rejected/quality_failed`、`input_rejected/pit_failed`、`input_rejected/adjustment_policy_mismatch`、`benchmark_unavailable/benchmark_required_missing`、`failed/runtime_error` | raw/manifest runtime read；旧 repo data read；connector/runtime/storage 导入；Tushare fetch/backfill；真实 lake write；normalize/revalidate/replay job |
| old data guardrail | S04 文档合同与 guardrail scanner；CP5 后实现时用于防止旧 data 被重新定义为 runtime/fallback | 文档文本、allowlist/denylist、reference-only policy；不读取真实 `data/**` 内容 | reference-only notice、violation report、safe remediation wording | `old_data_fallback_wording`、`credential_or_private_path_exposure`、`silent_migration_or_comparison`、`missing_reference_only_notice`、`S04_DENYLIST_PATH_BLOCKED` | 扫描真实数据内容；迁移/复制/删除旧 data；把旧 data 当测试 fixture、smoke precondition 或 coverage proof |

## 5. Allowed / Forbidden Consumers

| consumer | allowed | forbidden |
|---|---|---|
| Tushare acquisition job | 在用户显式触发且满足凭据、allowlist、source enabled、dry-run/执行边界时写 raw/manifest，并驱动后续数据层任务 | 被轻量 engine 或 Backtrader runtime 自动调用；读取旧 `data/`；打印 token 或真实私有路径 |
| normalization / replay / quality / catalog | 读取 raw/manifest，生成 canonical、quality、catalog、gold，并保留 lineage | 向 runtime 暴露 raw/manifest 作为价格输入；用旧 data 补缺；绕过 manifest lineage |
| `market_data` readers / adapters | 只读 canonical/gold/quality/catalog；返回 typed result/status；不执行抓取 | 导入 connector/runtime/storage 写路径；自动 normalize/revalidate/replay；静默 fallback 到旧 data |
| lightweight engine / experiments | P0 通过 canonical/gold reader 读取质量门禁后的输入；可选启用 external `legacy_flat` 兼容模式 | 直接读 raw/manifest；默认读 external `legacy_flat`；读 `<repo>/data`；触发 Tushare fetch/backfill |
| Backtrader | 只读 clean feed bundle，并在内存中校验 quality、PIT、adjustment、benchmark 状态 | raw/manifest runtime read；旧 repo data read；lake write；connector/runtime/storage 导入；token/.env 读取 |
| old `data/` | 人工参考或另行授权比对 | fallback、migration source、copy source、coverage proof、test fixture、smoke precondition、runtime input |

## 6. Typed Errors

| typed error / status | 来源 | 含义 | 允许的后续动作 | 禁止的后续动作 |
|---|---|---|---|---|
| `interface_not_allowed` | S01 | 请求的 Tushare interface 不在 dataset allowlist | 修订 job spec 或 allowlist 设计后重新审查 | 改用旧 data 或任意 interface 绕过 |
| `unknown_dataset` | S01 | dataset 未纳入 CR006 dataset contract | 停止执行并补设计/Story 范围 | 静默创建未知 dataset |
| `invalid_date_range` | S01/S02/S03 | 日期区间无效或超出请求契约 | 修正请求参数 | 回退到旧 data |
| `missing_credential` | S01 | 真实采集缺少凭据环境变量 | 保持 dry-run 或由用户配置凭据后重试 | 打印、记录、硬编码 token |
| `source_disabled` | S01 | Tushare source 未启用 | 停止真实采集，输出 remediation | 自动切换其他来源或旧 data |
| `resume_conflict` | S01 | resume/idempotency 与既有成功或部分成功批次冲突 | 按 runbook 选择 skip/retry/fail fast | 覆盖 manifest 或静默重跑 |
| `schema_mismatch` | S01/ADR-011 | raw/canonical 字段不满足 schema | 停止派生，输出 schema 差异和 lineage | 将 raw 直接交给 runtime |
| `lineage_unavailable` / `lineage_missing` | S01/S02 | 无法证明 canonical/gold 或 legacy_flat 的来源链路 | 返回 typed failure，提示重建 lineage | 使用无 lineage 数据继续回测 |
| `quality_failed` | S01/S02/S03 | coverage、重复、异常、PIT 或复权门禁未通过 | 返回 failure/status，提示质量修复 | 绕过 quality gate 或用旧 data 补齐 |
| `required_missing` | S02/S03 | runtime 所需 dataset 或字段缺失 | 返回 remediation job spec 或 unavailable status | runtime 自动 fetch/backfill |
| `invalid_request` | S02/S03 | input_mode、目录、policy 或参数不合法 | 修正请求 | 默认指向 `<repo>/data` |
| `pit_failed` | S03 | Backtrader clean feed 不满足 PIT/as-of 约束 | 拒绝输入并保留证据 | 继续运行 Backtrader |
| `adjustment_policy_mismatch` | S03 | feed 复权策略与请求不一致 | 拒绝输入并提示策略差异 | 混用不同复权口径 |
| `backend_unavailable` / `dependency_missing` | S03 | Backtrader 后端或依赖不可用 | 返回 structured unavailable | 用旧 data smoke test 代替 |
| `benchmark_unavailable` / `benchmark_required_missing` | S03 | benchmark 为必需但不可用 | 返回 benchmark unavailable | 静默忽略 benchmark |
| `old_data_fallback_wording` | S04 | 文档或代码文本把旧 data 写成 fallback | 修改措辞为 reference-only | 保留 fallback 语义 |
| `credential_or_private_path_exposure` | S04 | 文档暴露 token、凭据或真实私有路径 | 删除敏感文本，改用占位 | 继续传播敏感内容 |
| `silent_migration_or_comparison` | S04 | 未授权迁移、复制或比对旧 data | 删除行为或补明确授权路径 | 默认执行迁移/复制/比对 |
| `missing_reference_only_notice` | S04 | 面向用户文档缺少旧 data reference-only 提示 | 补充 reference-only notice | 让用户误以为旧 data 仍是 runtime 输入 |
| `S04_DENYLIST_PATH_BLOCKED` | S04 | guardrail denylist 命中禁止路径或用法 | 阻断并输出 violation | 继续扫描或读取真实 `data/**` |

## 7. CP5 审查影响

本附录只补齐 CP5 人工审查上下文，不修改以下对象：

- 不修改 `process/HLD.md`、`process/ARCHITECTURE-DECISION.md`、`process/STORY-BACKLOG.md`、`process/DEVELOPMENT-PLAN.yaml`。
- 不修改四份 CR006-BATCH-A LLD。
- 不修改四份 CP5 自动预检、post-fix review 或 `checkpoints/CP5-CR006-BATCH-A-LLD-BATCH.md`。
- 不修改 `process/STATE.md`，不把 `implementation_allowed` 改为 `true`。
- 不修改代码、测试、README/docs、delivery 或真实数据目录。

本附录与 `process/checks/CR006-HLD-STORY-REFRESH-EVALUATION-2026-05-19.md` 的结论一致：

| 项目 | 结论 |
|---|---|
| HLD refresh required | false |
| Story replan required | false |
| CP3 rerun required | false |
| CP4 rerun required | false |
| CP5 auto precheck rerun required | false |
| CP5 approved by this file | false |
| implementation allowed | false |

完成本文件后，meta-se 可将上下文交回 meta-po，由 meta-po 恢复 CP5 人工确认流程。CP5 人工确认仍应以用户明确批准为准。

## 8. Source Traceability

| 来源文件 | 本附录使用的事实 |
|---|---|
| `process/HLD.md` §23 | CR-006 Tushare-first structured lake 方案、raw/manifest audit 层、canonical/gold runtime 面、Backtrader clean feed、旧 data reference-only |
| `process/HLD.md` §21/§22 | 数据湖 dataset、benchmark、字段与质量门禁事实 |
| `process/ARCHITECTURE-DECISION.md` ADR-011/014/016/017/018 | 数据湖分层、manifest/canonical/quality/catalog/gold 合同、Tushare 数据集、Backtrader 清洁输入、旧 data reference-only |
| `process/stories/CR006-S01-tushare-first-data-acquisition-runbook-LLD.md` | Tushare run spec、raw/manifest、normalization、quality/catalog、runbook typed errors |
| `process/stories/CR006-S02-canonical-gold-lightweight-engine-adapter-LLD.md` | canonical/gold reader P0、optional external legacy_flat、typed result/error |
| `process/stories/CR006-S03-backtrader-clean-feed-contract-LLD.md` | Backtrader clean feed bundle、reader/validator allowed boundary、forbidden runtime/data-job boundary |
| `process/stories/CR006-S04-old-data-reference-only-guardrail-LLD.md` | old data reference-only policy、allowlist/denylist、文档合同 typed errors |
| `process/checks/REVIEW-CR006-BATCH-A-LLD-POST-FIX-2026-05-18.md` | post-fix REQUIRED=0、BLOCKING=0、S02/S03/S04 合同修正完成 |
| `checkpoints/CP5-CR006-BATCH-A-LLD-BATCH.md` | CP5 当前仍待人工确认，context fix pending，不允许实现 |

## 9. Safety Confirmation

- 未读取、列出、迁移、复制、比对或删除真实 `data/**`。
- 未读取、打印或记录 `.env`、Tushare token、NAS 凭据或真实私有路径。
- 未执行 Tushare 抓取、真实 lake read/write、normalize、revalidate 或 replay job。
- 未修改 HLD、ADR、Story Backlog、Development Plan、LLD、CP5 自动预检、CP5 人工稿或 STATE。
- 未修改代码、测试、README/docs、delivery、`engine/`、`experiments/`、`config/`、`market_data/`。
- 未批准 CP5，未将 `implementation_allowed` 改为 `true`，未进入实现阶段。
