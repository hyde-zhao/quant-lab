---
cr_id: "CR-010"
status: "verified-limited-window-pass-pending-close-decision"
impact_level: "high"
rollback_to: "solution-design"
approval_result: "limited-window-pass-pending-close-decision"
created_at: "2026-05-22T09:11:39+08:00"
created_by: "meta-po"
approved_by: "user"
approved_at: "2026-05-22T15:09:54+08:00"
source: "user"
linked_issue: ""
updated_at: "2026-05-31T21:43:48+08:00"
---

# CR-010 数据湖生产化与回测真实性提升

## 变更描述

将当前 `market_data` 从“已验证的小窗口真实数据链路 + 研究消费防线”推进为两层能力：

- 短期：支撑 16 个 experiments 使用更真实的数据输入，优先提升 HS300 日频研究可信度。
- 长期：形成可恢复、可审计、可扩展的生产级外置数据湖。

本 CR 明确拆出 `process/HLD-DATA-LAKE.md` companion HLD。主 HLD `process/HLD.md` 保留为量化研究 / 回测框架 HLD，只描述只读消费契约；数据湖生产链路、真实源回补、quality truth、catalog publish、lineage 与恢复能力归属 companion HLD。

## 文档处理决策

| 受影响文档 | 处理方式 | 旧基线保留方式 | 修订记录位置 | 批准状态 |
|---|---|---|---|---|
| `process/USE-CASES.md` | 不变 | 既有场景基线保留；CR-010 不重写原场景 | 不适用 | approved |
| `process/REQUIREMENTS.md` | 不变 | 既有需求基线保留；CR-010 作为结构性设计/实现变更 | 不适用 | approved |
| `process/HLD.md` | 原文档更新 | CR-004..CR-009 章节保留为历史追溯；追加 CR-010 拆分判定与 §26 集成摘要 | `## 修订记录` v1.9 | approved |
| `process/HLD-DATA-LAKE.md` | 新增 | 新 companion HLD 引用主 HLD CR-010 拆分判定 | `## 修订记录` v0.1 | approved |
| `process/ARCHITECTURE-DECISION.md` | 原文档更新 | ADR-001..029 保留；追加 ADR-030..035 | `## 修订记录` v1.2 | approved |
| `process/STORY-BACKLOG.md` | 原文档更新 | 既有 Story 状态不回滚；追加 CR010-S01..S12 | `## 修订记录` v1.2 | approved |
| `process/DEVELOPMENT-PLAN.yaml` | 原文档更新 | 既有 Wave / CP 记录保留；追加 CR010 Wave 与 policy | frontmatter / waves | approved |
| `docs/USER-MANUAL.md` / `README.md` | 原文档更新 | 后续 Wave 4 更新，当前仅列为影响对象 | 后续修订记录 | pending |

## 旧基线映射

| 原基线对象 | 新增 / 修改对象 | 保留策略 | 映射说明 |
|---|---|---|---|
| CR-007 | CR-010 P0 data lake batch | 原文保留 | 长周期 coverage、benchmark/calendar、dataset readiness 是 CR-010 生产化基础，不回滚历史 PASS |
| CR-008 | CR-010 realism mode / research metadata | 原文保留 | `research_input_v1`、allowed/blocked claims 继续作为实验真实性报告基础 |
| CR-009 | CR-010 replay / real smoke baseline | 原文保留 | CR-009 关闭后的 PASS 是 CR-010 真实复验基线；历史 FAIL 只作审计上下文 |

## 五维度影响分析

| 维度 | 评估问题 | 受影响对象 | 结论 | 处理动作 |
|------|----------|-----------|------|---------|
| 需求层 | 是否新增或重定义正式需求 | `REQUIREMENTS.md`、HLD | true | 不重写需求基线；用 CR/HLD/ADR 承载生产化新增要求 |
| 场景层 | 是否改变测试矩阵覆盖范围 | experiments、真实 smoke、quality/readiness | true | 新增离线 pipeline、W3 fail-fast、16 experiments realism report、真实 smoke 分阶段验证 |
| 计划层 | 是否改变 Phase、Wave、任务依赖 | `STORY-BACKLOG.md`、`DEVELOPMENT-PLAN.yaml` | true | 新增 CR010-DL-BATCH-A/B 与 CR010-QF-BATCH-C，后续文档/终验为 Wave 4 |
| 安全层 | 是否引入高风险动作或权限要求 | 真实源、外置 lake、凭据、旧数据 | true | 默认不授权真实联网 / 真实 lake 写入 / 旧 `data/**` 操作；真实复验需用户逐级授权 |
| 交付层 | 是否需要刷新文档和回归集 | README、USER-MANUAL、tests、CP6/CP7 | true | Wave 4 文档收敛；所有实现 Story 需 CP6/CP7 |

## 回退决策

- 影响范围：全局数据层 + 研究消费层。
- 回退到阶段：`solution-design`。
- 需要重新确认的对象：`process/HLD-DATA-LAKE.md`、`process/HLD.md` v1.9、ADR-030..035、CR010 Story/Wave、CP3/CP4。

## LLD 设计批次门禁

- 是否需要 LLD 设计批次：true
- batch_id：
  - `CR010-DL-BATCH-A`
  - `CR010-DL-BATCH-B`
  - `CR010-QF-BATCH-C`
  - `CR010-OPS-BATCH-D`
- 批次范围来源：CR-010 影响分析与 companion HLD
- 批次内 Story：
  - `CR010-S01-multidataset-plan-run-publish-cli-contract`
  - `CR010-S02-prices-adj-factor-history-backfill-loop`
  - `CR010-S03-hs300-index-trade-calendar-backfill-loop`
  - `CR010-S04-index-members-weights-stock-basic-readiness`
  - `CR010-S05-catalog-coverage-production-readiness-report`
  - `CR010-S06-pit-source-interface-spike-readiness`
  - `CR010-S07-trade-status-contract-reader-fail-fast`
  - `CR010-S08-prices-limit-contract-gate-fail-fast`
  - `CR010-S09-events-available-at-contract-fail-fast`
  - `CR010-S10-realism-mode-research-metadata`
  - `CR010-S11-experiments-smoke-limitation-matrix`
  - `CR010-S12-backtrader-vectorbt-clean-feed-boundary`
  - `CR010-S13-backup-archive-restore-env-manifest-contract`
  - `CR010-S14-backup-cli-dry-run-execute-verify-report`
  - `CR010-S15-restore-cli-drill-read-revalidate-replay`
  - `CR010-S16-retention-policy-archive-backup-cleanup`
- 批次人工确认稿：
  - `checkpoints/CP5-CR010-DL-BATCH-A-LLD-BATCH.md`
  - `checkpoints/CP5-CR010-DL-BATCH-B-LLD-BATCH.md`
  - `checkpoints/CP5-CR010-QF-BATCH-C-LLD-BATCH.md`
  - `checkpoints/CP5-CR010-OPS-BATCH-D-LLD-BATCH.md`
- 开发启动条件：
  - [ ] 对应批次内全部 Story LLD 已输出
  - [ ] 对应批次内全部 Story CP5 自动预检已通过
  - [ ] 对应批次 CP5 人工确认结论为 `approved`
  - [ ] 批次内每个 Story 的 `dev_gate` 已满足

## 执行链路

| 顺序 | 责任角色 | 动作 | 输入 | 输出 | 门控 | 完成后下一步 |
|---|---|---|---|---|---|---|
| 1 | `meta-po` | 创建 CR 并分派 | 用户计划 | 本 CR、STATE 更新、调度证据 | CR 已登记 | 等待 HLD/ADR |
| 2 | `meta-se` | 输出 companion HLD、ADR、Story Plan | CR、既有 CR007/008/009 | HLD-DATA-LAKE、主 HLD 增量、ADR-030..035、Backlog/Plan | CP3/CP4 | 进入 LLD 批次 |
| 3 | `meta-dev` | 输出 LLD 并实现离线能力 | CP5 approved | 代码、测试、CP6 | CP6 | 交 QA |
| 4 | `meta-qa` | 离线验证和真实 smoke（需授权） | CP6、测试策略 | CP7、真实 smoke 记录 | CP7 / 授权 | 交 doc |
| 5 | `meta-doc` | 文档收敛 | 已验证实现 | README / USER-MANUAL | CP8 | 交用户终验 |

## 自动终验授权

- 是否启用：false
- 授权范围：不适用
- 适用检查点：CP8
- 授权原文：
- 授权时间：

## 处理结论

- 审批结论：`approved-for-cp3-cp4-and-dl-batch-a`
- [ ] 自动批准（低风险）
- [ ] 待人工确认（中风险）
- [x] 人工已审批（高风险）

审批记录：

- 审批人：user
- 审批时间：2026-05-22T15:09:54+08:00
- 原始审批文本：`你可以默认人工审批通过，继续推进项目。`
- 批准范围：CP3、CP4 与 CR010-DL-BATCH-A 的正式 LLD / CP5 / 离线实现推进。
- 保留限制：不授权真实联网、真实 Tushare 抓取、真实 lake 写入、旧 `data/**` 操作或凭据读取。

## 关联对象

| 类型 | 标识 | 说明 |
|---|---|---|
| HLD | `process/HLD-DATA-LAKE.md` | 新 companion HLD |
| HLD | `process/HLD.md` | 主 HLD v1.9 增量 |
| ADR | ADR-030..035 | CR-010 决策簇 |
| 检查点 | `process/checks/CP3-CR010-DATA-LAKE-HLD-CONSISTENCY.md` | HLD 自动预检 |
| 检查点 | `process/checks/CP4-CR010-STORY-PLAN-CONSISTENCY.md` | Story Plan 自动预检 |

## CR010-DL-BATCH-A 执行记录

| 项 | 结果 | 证据 |
|---|---|---|
| CP5 批次 | approved | `checkpoints/CP5-CR010-DL-BATCH-A-LLD-BATCH.md` |
| S01 | verified | `process/checks/CP6-CR010-S01-multidataset-plan-run-publish-cli-contract-CODING-DONE.md`；`process/checks/CP7-CR010-S01-multidataset-plan-run-publish-cli-contract-VERIFICATION-DONE.md` |
| S02 | verified | `process/checks/CP6-CR010-S02-prices-adj-factor-history-backfill-loop-CODING-DONE.md`；`process/checks/CP7-CR010-S02-prices-adj-factor-history-backfill-loop-VERIFICATION-DONE.md` |
| S03 | verified | `process/checks/CP6-CR010-S03-hs300-index-trade-calendar-backfill-loop-CODING-DONE.md`；`process/checks/CP7-CR010-S03-hs300-index-trade-calendar-backfill-loop-VERIFICATION-DONE.md` |
| S04 | verified | `process/checks/CP6-CR010-S04-index-members-weights-stock-basic-readiness-CODING-DONE.md`；`process/checks/CP7-CR010-S04-index-members-weights-stock-basic-readiness-VERIFICATION-DONE.md` |
| S05 | verified | `process/checks/CP6-CR010-S05-catalog-coverage-production-readiness-report-CODING-DONE.md`；`process/checks/CP7-CR010-S05-catalog-coverage-production-readiness-report-VERIFICATION-DONE.md` |

本批次新增 / 固化能力：

- P0 catalog coverage report builder。
- production readiness report builder，支持 `production_strict` / `exploratory`。
- `report-readiness` CLI。
- generic P0 replay manifest gate，返回 `network_calls=0`、`auto_execute=false`。

验证结果：

- `uv run --python 3.11 python -m py_compile market_data/contracts.py market_data/normalization.py market_data/catalog.py market_data/cli.py market_data/readers.py market_data/validation.py engine/research_dataset.py`：PASS
- `uv run --python 3.11 pytest -q tests/test_cr010_data_lake_publish_and_contracts.py`：6 passed
- `uv run --python 3.11 pytest -q tests/test_market_data_normalization_validation_readers.py tests/test_market_data_multidataset_quality_readers.py tests/test_market_data_cli_comparison.py tests/test_cr006_lightweight_engine_adapter.py tests/test_cr008_research_dataset_builder.py tests/test_cr010_data_lake_publish_and_contracts.py`：49 passed
- `uv run --python 3.11 pytest -q`：245 passed

安全确认：

- 未执行真实联网。
- 未执行真实 configured lake root 写入。
- 未读取、列出、迁移、复制、比对或删除旧 `data/**`。
- 未读取、打印或记录 token、`.env`、NAS 用户名、NAS 密码或真实私有路径。

## 真实执行授权更新

| 授权项 | 状态 | 授权人 | 授权时间 | 授权文本 / 说明 |
|---|---|---|---|---|
| 真实联网 | authorized | user | 2026-05-22T15:54:10+08:00 | 用户回复“包括真实联网” |
| 真实 Tushare 抓取 | authorized | user | 2026-05-22T15:54:10+08:00 | 用户回复“真实tushare抓取” |
| 真实写入数据湖 | authorized | user | 2026-05-22T15:54:10+08:00 | 用户回复“真实写入数据湖” |
| 读取 `.env` | authorized | user | 2026-05-22T15:54:10+08:00 | 用户回复“.env胚子好了，你可以读取” |
| 旧 `data/**` 对比 | deferred | user | 2026-05-22T15:54:10+08:00 | 用户回复“与旧的data/**对比可以暂缓” |

执行约束：

- 凭据值不得打印、写入报告或保存到 memory。
- 真实路径在用户回复中已授权可用于执行；对话与报告中默认使用 `<configured-lake-root>` 或相对路径。
- 旧 `data/**` 对比继续暂缓，不作为 coverage proof 或 current truth。

## 真实 Tushare 数据湖补跑记录

| 项 | 结果 | 证据 |
|---|---|---|
| 检查记录 | PARTIAL | `process/checks/REAL-TUSHARE-DATA-LAKE-SMOKE-CR010-RESMOKE-2026-05-22.md` |
| 真实联网 / Tushare / 写湖 | DONE | 小窗口 `2024-01-02` 至 `2024-01-04`；报告中仅记录 `<configured-lake-root>` 和相对路径。 |
| published P0 dataset | 6/7 | `trade_calendar`、`hs300_index`、`adj_factor` 为 pass；`prices`、`index_weights`、`stock_basic` 为 warn；`index_members` 失败候选。 |
| production readiness | FAIL | `production_strict` 阻断 `production_current_truth`、`quality_pass_research`、`pit_universe_research`。 |
| exploratory readiness | WARN | 允许 `exploratory_analysis` / `fixture_regression`，必须披露限制。 |
| 回归验证 | PASS | `uv run --python 3.11 pytest -q` => `249 passed in 7.62s`。 |

本次真实补跑后的实现修复：

- `tushare-first-acquire` 增加 `adj_factor/index_members/stock_basic` P0 真实入口。
- `validate/read` 按 `run_id` 或 catalog current canonical 隔离读取，避免历史 run 混读。
- `replay` 改为按 manifest `run_id/batch_id/dataset/interface` 匹配，兼容 `tushare-first-acquire`。
- raw 写入路径加入 `run_id=<run_id>`，避免不同 run 复用 `b1` 覆盖 raw。
- `revalidate` 保持同一 run 的 published current truth，不降级为候选。
- `index_weights` 缺真实 `available_at` 时标记为 `pit_incomplete`，不伪造 PIT available。

安全确认：

- 未打印或写入 token、`.env` 内容或真实私有路径。
- 未读取、列出、迁移、复制、比对或删除旧 `data/**`。
- 不声明 production current truth complete；`index_members` 仍需后续 source/interface 或日期窗口策略补齐。

## CR010 剩余能力全量实施编排登记

登记时间：2026-05-22T19:33:44+08:00

本节按用户给定计划登记 CR-010 后续批次。当前编排只更新计划、门控、交接和检查点记录；不修改 `market_data/**`、`engine/**`、`experiments/**`、`tests/**`、`README.md` 或 `docs/**`。

### 已知执行基线

| 事实 | 当前结论 | 证据 / 说明 |
|---|---|---|
| DL-BATCH-A | S01-S05 verified | 见本 CR “CR010-DL-BATCH-A 执行记录”与对应 CP6/CP7 |
| 真实 Tushare 小窗口 resmoke | PARTIAL | `process/checks/REAL-TUSHARE-DATA-LAKE-SMOKE-CR010-RESMOKE-2026-05-22.md` |
| published P0 dataset | 6/7 | `index_members` 阻断，`production_strict=fail` |
| NFS hot/archive/backup/restore root | PASS | STATE history `cr010-nfs-env-config-mounted-pass` |
| 旧 `data/**` 对比 | deferred | 用户明确暂缓；本轮不读取、不列出、不比对、不迁移 |

### CR010-OPS-BATCH-D 新增批次

| Story | 标题 | 范围 | 默认门控 |
|---|---|---|---|
| `CR010-S13-backup-archive-restore-env-manifest-contract` | backup/archive/restore env 与 manifest/checksum/脱敏契约 | 四类 lake root 环境变量、manifest/checksum、报告脱敏、路径冲突 fail-fast | 只登记契约；不得打印 `.env`、token、NAS 凭据或真实私有路径 |
| `CR010-S14-backup-cli-dry-run-execute-verify-report` | backup CLI | `backup-plan`、`backup-run`、`backup-verify`、`backup-report`；默认 dry-run，`--execute` 才复制 | 未通过 CP5/CP6/CP7 前不得执行真实备份 |
| `CR010-S15-restore-cli-drill-read-revalidate-replay` | restore CLI 与 drill | `restore-plan`、`restore-run`、`restore-drill`；`restore-root==lake-root` fail-fast | restore drill 必须 `read/revalidate/replay` 且 `network_calls=0` |
| `CR010-S16-retention-policy-archive-backup-cleanup` | retention policy | archive/backup retention policy、manifest/checksum 校验、报告脱敏与清理 dry-run | checksum skip/mismatch fail；未授权不得删除真实数据 |

新增 CLI 契约：

- backup：`backup-plan`、`backup-run`、`backup-verify`、`backup-report`。
- restore：`restore-plan`、`restore-run`、`restore-drill`。
- 全部新增 CLI 默认 dry-run；只有显式 `--execute` 才允许复制或恢复。
- `restore-root == lake-root` 必须 fail-fast。
- checksum 被 skip 或 mismatch 必须 fail。
- 报告必须脱敏，不记录 token、`.env` 内容、NAS 凭据或真实私有路径。
- `restore-drill` 只执行只读 `read/revalidate/replay` 路径，`network_calls=0`。

### DL-BATCH-B 执行意图与门控

| Story | 执行意图 | 门控结论 |
|---|---|---|
| `CR010-S06-pit-source-interface-spike-readiness` | 冻结 PIT exact source/interface Spike 记录；未确认前 fail-fast | 不把 `index_weights` 或 `stock_basic` 替代 `index_members` |
| `CR010-S07-trade-status-contract-reader-fail-fast` | `trade_status` 缺 source/interface 或 `available_at` 时 fail-fast | `production_strict=fail`，exploratory 必须写 limitation |
| `CR010-S08-prices-limit-contract-gate-fail-fast` | `prices_limit` 缺 source/interface 或 `available_at` 时 fail-fast | 不声明真实可成交 |
| `CR010-S09-events-available-at-contract-fail-fast` | events 缺 explicit `available_at` 时 fail-fast | 不用日期推导可用时点 |

### QF-BATCH-C 执行意图与门控

| Story | 执行意图 | 门控结论 |
|---|---|---|
| `CR010-S10-realism-mode-research-metadata` | 输出 realism metadata，区分 exploratory 与 production_strict | 不把 exploratory 结果写成 production_strict |
| `CR010-S11-experiments-smoke-limitation-matrix` | 覆盖 16 个 experiments smoke limitation matrix | 每个 experiment 必填 allowed_claims / blocked_claims / strict status |
| `CR010-S12-backtrader-vectorbt-clean-feed-boundary` | Backtrader / VectorBT clean feed 只读边界 | 消费路径网络调用为 0，不触发 backfill |

### 本轮调度与检查点结论

| 对象 | 状态 | 证据 |
|---|---|---|
| CP4 剩余批次 Story Plan addendum | approved | `checkpoints/CP4-CR010-REMAINING-BATCHES-STORY-PLAN-REVIEW.md`，`approval_source=user-preauthorized` |
| B/C/D LLD 交接 | handoff-created / dispatch-unavailable-in-this-thread | `process/handoffs/META-DEV-CR010-DL-BATCH-B-LLD-2026-05-22.md`、`process/handoffs/META-DEV-CR010-QF-BATCH-C-LLD-2026-05-22.md`、`process/handoffs/META-DEV-CR010-OPS-BATCH-D-LLD-2026-05-22.md` |
| B/C/D CP5 | BLOCKED | 未有真实子 agent LLD 输出与 Story 级 CP5 PASS；不得进入实现 |
| B/C/D CP6 | BLOCKED | 未有代码实现，不得标记编码完成 |
| B/C/D CP7 | BLOCKED | 未有 CP6 PASS 或 QA 子 agent 验证，不得标记 verified |

阻断说明：

- 当前工具面没有可调用的 `spawn_agent` / `resume_agent` / `send_input`；本轮只能创建 handoff 与 `BLOCKED` 检查点记录，不能声明 meta-dev / meta-qa 已执行。
- 没有用户明确批准 `inline-fallback` 代执行，因此 meta-po 不直接生成 LLD、不写代码、不跑业务测试、不回填 CP6/CP7 PASS。
- 后续主线程需要真实调度 meta-dev 完成 B/C/D 的 LLD 与实现，再真实调度 meta-qa 完成验证；每个 Story 的 CP6/CP7 必须补齐 Agent Dispatch Evidence。

## CR010 剩余能力实现与验证更新

更新时间：2026-05-22T19:58:44+08:00

主线程已在上述编排登记之后完成代码实现、测试和文档更新。由于两次 `meta-qa` 子 agent 均未返回完成结果并已 shutdown，本节只记录代码验证事实，不把正式 CP7 写成 meta-qa PASS。

| 批次 | 代码状态 | 验证状态 | 流程状态 |
|---|---|---|---|
| `CR010-OPS-BATCH-D` | implemented | PASS | OPS 核心模块由 `meta-dev/dev-xu` agent_id=`019e4f76-e461-7e20-87f4-cd6b79d713fc` 交付；CLI/retention 由主线程补齐；正式 CP7 缺 meta-qa 完成证据 |
| `CR010-DL-BATCH-B` | implemented | PASS | 主线程实现 W3 fail-fast 与 strict readiness；正式 CP6/CP7 仍缺独立 meta-dev/meta-qa 完成证据 |
| `CR010-QF-BATCH-C` | implemented | PASS | 主线程实现 strict realism metadata、16 experiments matrix 与 consumer boundary；正式 CP6/CP7 仍缺独立 meta-dev/meta-qa 完成证据 |

新增 / 修改代码与测试：

- `market_data/backup_restore.py`：backup/restore/retention 核心逻辑。
- `market_data/cli.py`：新增 `backup-plan`、`backup-run`、`backup-verify`、`backup-report`、`restore-plan`、`restore-run`、`restore-drill`。
- `market_data/catalog.py`、`market_data/readers.py`：W3 required dataset 与 fail-fast / production_strict gate。
- `engine/research_dataset.py`、`experiments/reporting.py`：`production_strict` blocked claims、readiness metadata 与 16 experiments realism matrix。
- `tests/test_cr010_backup_archive_restore.py`、`tests/test_cr010_w3_fail_fast_contracts.py`、`tests/test_cr010_experiments_realism_metadata.py`、`tests/test_cr010_consumer_boundary.py`。
- `README.md`、`docs/USER-MANUAL.md`：备份/恢复 uv 命令、脱敏边界、restore drill、retention policy 说明。

验证结果：

- `uv run --python 3.11 python -m py_compile market_data/*.py engine/*.py experiments/*.py`：PASS
- `uv run --python 3.11 pytest -q tests/test_cr010_backup_archive_restore.py tests/test_cr010_w3_fail_fast_contracts.py tests/test_cr010_experiments_realism_metadata.py tests/test_cr010_consumer_boundary.py`：17 passed
- `uv run --python 3.11 pytest -q tests/test_market_data_normalization_validation_readers.py tests/test_market_data_multidataset_quality_readers.py tests/test_market_data_cli_comparison.py tests/test_cr008_research_dataset_builder.py tests/test_cr010_data_lake_publish_and_contracts.py tests/test_cr010_backup_archive_restore.py tests/test_cr010_w3_fail_fast_contracts.py tests/test_cr010_experiments_realism_metadata.py tests/test_cr010_consumer_boundary.py`：63 passed
- `uv run --python 3.11 pytest -q`：266 passed in 11.44s
- 裸行 backup/restore CLI 示例静态检查：`rg -n "^python -m market_data\\.cli (backup|restore)" README.md docs/USER-MANUAL.md tests` 无输出。

安全确认：

- 未打印 `.env`、token、NAS 凭据或真实私有路径。
- 未读取、列出、迁移、复制、比对或删除旧 `data/**`。
- 未执行真实备份、真实恢复、真实删除或真实 Tushare 新抓取。
- CR-010 不关闭：真实小窗口 current truth 仍为 PARTIAL，`index_members` 仍阻断 production_strict。

流程证据缺口：

- `process/checks/CR010-REMAINING-BATCHES-MAIN-THREAD-VERIFICATION-2026-05-22.md` 已记录主线程验证事实与 agent 调度尝试。
- `meta-qa/qa-hua` agent_id=`019e4f82-43ab-7661-b6c1-410f654e5bd1` 与 `meta-qa/qa-jin` agent_id=`019e4f89-7aa5-75b3-9bd3-13776efa4463` 均已 shutdown，不能作为 CP7 PASS 证据。

## CR010 剩余能力 meta-qa 重验完成

更新时间：2026-05-22T20:18:16+08:00

用户重启进程后要求重新拉起 `meta-qa` 子进程验证。主线程已通过 `spawn_agent` 拉起 `meta-qa/qa-cao`，agent_id=`019e4f98-67f8-7151-92ab-dcc47378b19c`，本轮 agent 状态为 `completed`，不是 shutdown。

| 对象 | 结论 | 证据 |
|---|---|---|
| meta-qa dispatch | completed | `process/handoffs/META-QA-CR010-REMAINING-BATCHES-VERIFY-2026-05-22.md` |
| CR010 剩余批次 CP7 | PASS | `process/checks/CP7-CR010-REMAINING-BATCHES-META-QA-VERIFICATION-2026-05-22.md` |
| 测试策略增量 | updated | `process/TEST-STRATEGY.md` 的“CR-010 剩余批次 CP7 验证策略增量” |

本轮 meta-qa 执行并记录：

- `uv run --python 3.11 python -m py_compile market_data/*.py engine/*.py experiments/*.py`：PASS
- `uv run --python 3.11 pytest -q tests/test_cr010_backup_archive_restore.py tests/test_cr010_w3_fail_fast_contracts.py tests/test_cr010_experiments_realism_metadata.py tests/test_cr010_consumer_boundary.py`：17 passed
- 关联回归测试集：64 passed
- `uv run --python 3.11 pytest -q`：266 passed in 8.39s
- `git diff --check`：PASS
- backup/restore 裸 `python -m market_data.cli ...` 入口扫描：无命中

状态更新：

- 上一轮 `qa-hua` / `qa-jin` shutdown 仍不作为 QA PASS 或 CP7 PASS 证据。
- 本轮 `qa-cao` completed，CR010 剩余批次的正式 QA CP7 evidence gap 已补齐。
- `CR010-DL-BATCH-B`、`CR010-QF-BATCH-C`、`CR010-OPS-BATCH-D` 当前实现、测试、文档与安全边界通过独立 QA 验证。
- CR-010 不关闭：真实小窗口 current truth 仍为 PARTIAL，`index_members` 仍阻断 `production_strict`。

安全确认：

- 未执行真实备份、真实恢复、真实删除或真实 Tushare 新抓取。
- 未打印 `.env`、token、NAS 凭据或真实私有路径。
- 未读取、列出、迁移、复制、比对或删除旧 `data/**`。

## index_members 补探与真实运维 smoke 更新

更新时间：2026-05-22T21:11:43+08:00

本轮按剩余任务收敛计划继续处理 CR-010 关闭前提：真实 `index_members` current truth、`production_strict` 复检、backup/restore 运维 smoke 和流程状态债务。证据文件为 `process/checks/REAL-TUSHARE-DATA-LAKE-SMOKE-CR010-INDEX-MEMBERS-OPS-2026-05-22.md`。

### index_members current truth 结论

| 项 | 结论 | 说明 |
|---|---|---|
| Tushare `index_member` 探测 | 仍不可用 | `399300.SZ` / `000300.SH` 的无日期、2024-01 窗口、`is_new=Y/N` 和 2024 全年组合均返回 0 行。 |
| 扩大窗口真实 fetch | DONE | 2024-01-01..2024-01-31 真实 `tushare-first-acquire index_members` 成功，`network_calls=1`。 |
| normalize | DONE | `row_count=0`。 |
| validate | FAIL_EXPECTED | `quality_status=fail`、`dataset_status=required_missing`、`coverage_ratio=0.0`。 |
| publish | NOT_RUN | 不满足 quality/readiness；继续保持 `candidate_unpublished`。 |
| 替代源 | REJECTED | `index_weight` 同窗口有行数，但按 CR-010 约束不得替代 `index_members`；`stock_basic` 也不得替代 PIT membership。 |

结论：`index_members` 仍不能声明 current truth，`current_truth_complete=false`。

### production_strict 复检

| 模式 | 结论 | 说明 |
|---|---|---|
| `production_strict` | FAIL | 阻断包含 `index_members` 未发布 / quality fail / PIT incomplete，`index_weights` PIT incomplete，`prices` / `stock_basic` warn，以及 W3 `trade_status`、`prices_limit`、`events` missing。 |
| `exploratory` | WARN | 只允许 `exploratory_analysis` / `fixture_regression`，必须披露 limitations。 |
| W3 fail-fast | PASS | `trade_status`、`prices_limit`、`events` 继续保持 missing / required_missing；未伪造 available 或 `available_at`。 |

CR-010 关闭状态：`open`。在 `index_members` 与 `production_strict` 达标前，不触发 CP8 / close checklist。

### backup/restore 运维 smoke

本轮使用已发布 `prices` run 执行最小真实运维 smoke，release 为 `cr010-ops-smoke-20260522`，不覆盖 hot lake。

| 命令 | 结论 | 摘要 |
|---|---|---|
| `backup-plan` | PASS | file_count=4，bytes=78,772，报告仅含 root label 与相对路径。 |
| `backup-run --execute` | PASS | 首次 copied=4，二次同 checksum skip=4。 |
| `backup-verify` | PASS | checksum same=4。 |
| `backup-report` | PASS | checksum computed=4。 |
| `restore-plan` | PASS | would_restore=4。 |
| `restore-drill --execute` | PASS | read available，revalidate pass，replay `network_calls=0`、`auto_execute=false`。 |
| `restore-run --execute` | PASS | 恢复到 configured restore root，restored=4；未覆盖 hot lake。 |
| restore root `read` | PASS | `prices` row_count=3。 |
| restore root `revalidate` | PASS | `network_calls=0`，quality_status=warn。 |
| restore root `replay` | PASS | `network_calls=0`、`writes=0`。 |
| restore-root collision | PASS | `restore-root == lake-root` 返回 `restore_root_conflict`。 |

安全确认：

- 未打印 `.env`、token、NAS 凭据或真实私有路径。
- 未读取、列出、迁移、复制、比对或删除旧 `data/**`。
- 未执行真实删除。
- backup/restore 报告只记录 root label、相对路径、file count、bytes 和 checksum 状态。

### 流程状态债务清理

新增 `process/checks/CR010-BLOCKED-RECORDS-SUPERSEDED-2026-05-22.md`，声明 B/C/D 的 `CP5/CP6/CP7 *-BLOCKED` 文件是早期 handoff-only 阶段记录，旧文件保留为历史，不删除；当前门控事实以 `qa-cao` completed 的 `process/checks/CP7-CR010-REMAINING-BATCHES-META-QA-VERIFICATION-2026-05-22.md` 为准。

`process/STATE.md` 已清理过期 `formal_gate_note`：上一轮 `qa-hua` / `qa-jin` shutdown 仍不作为证据；`qa-cao` completed，CP7 evidence gap 已补齐。

## JQData index_members PIT source/interface 接入

更新时间：2026-05-22T22:09:07+08:00

本轮按用户补充计划为 `index_members` 增加 JQData 真实 PIT source/interface。该实现只覆盖 `index_members`，不替代 Tushare 全链路，不扩展 `prices`、`index_weights`、`stock_basic` 或 W3 数据集。证据文件为 `process/checks/REAL-JQDATA-DATA-LAKE-SMOKE-CR010-INDEX-MEMBERS-2026-05-22.md`。

### 实现范围

| 对象 | 结论 | 说明 |
|---|---|---|
| source registry | DONE | 新增 `source=jqdata`，默认 disabled，credential env vars 为 `JQDATA_USERNAME` / `JQDATA_PASSWORD`。 |
| interface | DONE | 仅允许 `index_members.snapshot`，`target_dataset=index_members`，provider method 为 `get_index_stocks`，`pit_required=true`。 |
| adapter | DONE | `JQDataAdapter` 读取环境变量认证，支持 `399300.SZ` / `000300.SH` / `000300.XSHG` 到 `000300.XSHG` 映射，并将 `000001.XSHE` / `600000.XSHG` 转为 `000001.SZ` / `600000.SH`。 |
| CLI | DONE | 新增 `jqdata-acquire`；dry-run 不联网不写湖，真实执行要求 `--enable-real-source`。 |
| replay | DONE | 复用 manifest/raw，`index_members` replay 不触发真实 source，保持 `network_calls=0`。 |
| 依赖 | DONE | 新增 `jqdata` dependency group，锁定 `jqdatasdk`。 |
| 真实 smoke | PASS | `jqdata-acquire --dry-run true --json` 通过；凭据补齐后真实执行 `network_calls=1`、`writes=1`，`normalize row_count=300`，`validate quality_status=pass`，`publish_status=published`、`readiness_status=available`、`pit_status=pit_available`。 |

### 22:09 时点数据真相口径（已被后续 limited window 收敛更新）

| 项 | 结论 | 说明 |
|---|---|---|
| JQData 账号窗口 | LIMITED | 当前账号已知验证窗口为 `2025-02-11..2026-02-18`，只记录为 `limited_pit_window`。 |
| 完整历史覆盖 | NOT_CLAIMED | 不声明 2005 起完整历史 PIT universe complete。 |
| CR-010 状态 | SUPERSEDED | 22:09 时点仅关闭 `index_members` blocker；23:34 后续章节已补齐 `index_weights`、`stock_basic` 与 W3，并将 limited window `production_strict` 收敛为 PASS。 |
| 替代约束 | ENFORCED | `index_weights` / `stock_basic` 不得替代 `index_members`；JQData 也不自动覆盖其他数据集。 |

### 真实 smoke 结果

| 环节 | 结果 | 摘要 |
|---|---|---|
| acquire | PASS | `network_calls=1`、`writes=1`，raw 相对路径为 `raw/jqdata/index_members.snapshot/20250211/run_id=run-jqdata-index-members-smoke-20260522/jqdata-hs300-20250211.jsonl`。 |
| normalize | PASS | `row_count=300`。 |
| validate | PASS | `quality_status=pass`、`dataset_status=available`、coverage 300/300。 |
| publish | PASS | `publish_status=published`、`readiness_status=available`、`pit_status=pit_available`。 |
| read | PASS | `row_count=300`，样例行显示 `source=jqdata`、`source_interface=index_members.snapshot`。 |
| revalidate | PASS | `network_calls=0`，quality 仍为 pass。 |
| replay | PASS | `network_calls=0`、`writes=0`、`auto_execute=false`。 |
| production_strict | SUPERSEDED | 22:09 时点为 `FAIL_REMAINING`；后续 limited window 收敛章节已更新为 PASS。 |
| exploratory | WARN | allowed claims 为 `exploratory_analysis` / `fixture_regression`。 |

安全确认：

- 未打印、写入或保存 `JQDATA_USERNAME` / `JQDATA_PASSWORD` 的真实值。
- raw、manifest、quality、catalog、README、USER-MANUAL 与测试只记录环境变量名、source/interface、相对路径和脱敏 root label。
- 未读取、列出、迁移、复制、比对或删除旧 `data/**`。

## limited window production_strict 收敛

更新时间：2026-05-22T23:34:00+08:00

本轮按用户确认的有限窗口方案继续收敛 CR-010：验收窗口固定为 `2025-02-11..2026-02-18`，不追求 2005 起完整历史覆盖。证据文件为 `process/checks/REAL-PROD-WINDOW-DATA-LAKE-SMOKE-CR010-2026-05-22.md`。

### 实现与数据源扩展

| 对象 | 结论 | 说明 |
|---|---|---|
| JQData source registry | DONE | `source=jqdata` 已扩展到 `index_members.snapshot`、`index_weights.snapshot`、`stock_basic.snapshot`、`trade_status.daily`、`prices_limit.daily`、`events.disclosure`。 |
| JQData adapter | DONE | 支持 `get_index_stocks`、`get_index_weights`、`get_all_securities`、`get_price`、`get_extras`；仍要求 enabled、allowlist、凭据、非 offline 和 `explicit_real_execution=true`。 |
| PIT available_at 规则 | DONE | `index_weights` 的 canonical `trade_date` 使用查询快照日，provider 权重日期进入 `effective_date`；`stock_basic` 不提前暴露未来上市 / 退市事实。 |
| W3 canonical 链路 | DONE | `trade_status`、`prices_limit`、`events` 完成 acquire、raw/manifest、normalize、validate、publish、read、revalidate、replay。 |
| P0 同窗 current truth | DONE | `prices`、`adj_factor`、`hs300_index`、`trade_calendar` 使用 `2025-02-11..2026-02-18` 窗口重建 / 重登记；`prices` 绑定 PIT universe，`prices` / `adj_factor` 使用 `trade_status` 可交易分母。 |

### 真实窗口 smoke 结果

| 数据集 | source | run_id | 结论 |
|---|---|---|---|
| `index_members` | `jqdata` | `run-jqdata-index-members-smoke-20260522` | `published/pass/available/pit_available` |
| `index_weights` | `jqdata` | `cr010-prod-window-20250211-20260218-index-weights-smoke-v2` | `published/pass/available/pit_available` |
| `stock_basic` | `jqdata` | `cr010-prod-window-20250211-20260218-stock-basic-smoke-v3` | `published/pass/available/pit_available` |
| `trade_status` | `jqdata` | `cr010-prod-window-20250211-20260218-trade-status-jqdata` | `published/pass/available`，row_count=75,300 |
| `prices_limit` | `jqdata` | `cr010-prod-window-20250211-20260218-prices-limit-jqdata` | `published/pass/available`，row_count=75,300 |
| `events` | `jqdata` | `cr010-prod-window-20250211-20260218-events-jqdata` | `published/pass/available`，row_count=0；空事件表仅在 source/interface 与 `available_at_rule` 冻结时允许 |
| `trade_calendar` | `tushare` | `cr010-prod-window-20250211-20260218-trade-calendar-tushare` | `published/pass/available`，row_count=373 |
| `hs300_index` | `tushare` | `cr010-prod-window-20250211-20260218-hs300-index-tushare` | `published/pass/available`，row_count=251 |
| `adj_factor` | `tushare` | `cr010-prod-window-20250211-20260218-prices-adj-tushare` | `published/pass/available`，row_count=74,957；按可交易分母 missing_rate=0.0 |
| `prices` | `tushare` | `cr010-prod-window-20250211-20260218-prices-adj-tushare` | `published/pass/available`，row_count=74,781；按可交易分母 missing_rate=0.0 |

### readiness 结论

| 模式 | 状态 | blockers | allowed_claims | blocked_claims |
|---|---|---|---|---|
| `production_strict` | PASS | [] | `production_strict_research` | `production_current_truth` |
| `exploratory` | PASS | [] | `exploratory_analysis`、`fixture_regression` | `production_current_truth` |

readiness coverage summary：dataset_count=10、published_count=10、missing_required_count=0、current_truth_complete=true。

声明边界：

- 本轮只允许声明 `2025-02-11..2026-02-18` limited window 内的 `production_strict_research`。
- 不声明 2005 起完整历史 PIT universe complete。
- 不声明全市场长期覆盖或持续 `production_current_truth`。
- `events` 当前仅为 ST 状态变更口径；后续扩展财报、公告或其他事件时必须重新确认真实披露 / 可用时点。

验证结果：

- `uv run --python 3.11 pytest -q tests/test_cr010_data_lake_publish_and_contracts.py tests/test_market_data_tushare_datasets.py tests/test_cr010_w3_fail_fast_contracts.py tests/test_cr010_jqdata_index_members_source.py`：33 passed
- 真实 P0 replay 复用 600 个既有 raw 请求，`status_counts={"skipped": 600}`；read/revalidate/replay 均未触发真实网络调用，replay `writes=0`。
- `report-readiness` 等价只读检查未触发补数、联网或写 lake。

安全确认：

- 未打印、写入或保存 Tushare token、JQData 用户名 / 密码、`.env` 内容或真实私有路径。
- 未读取、列出、迁移、复制、比对或删除旧 `data/**`。
- 文档与检查记录仅写 run_id、source/interface、row_count、质量状态和 `<configured-lake-root>` 语义。
