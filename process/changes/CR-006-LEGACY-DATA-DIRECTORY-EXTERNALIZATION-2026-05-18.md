---
cr_id: "CR-006"
status: "closed"
impact_level: "medium"
rollback_to: "story-execution"
approval_result: "cp7-pass-batch-a-verified-closed"
batch_a_verified: true
closed: true
close_gate: "closed-by-g0-status-closure"
created_at: "2026-05-18T20:57:04+08:00"
updated_at: "2026-05-30T14:25:41+08:00"
closed_by: "meta-po"
closed_at: "2026-05-30T14:25:41+08:00"
closure_checkpoint: "checkpoints/CP8-G0-CR-STATUS-CLOSURE-2026-05-30.md"
close_approval_text: "@meta-po 好的按照你推荐的顺序，逐步完成。"
created_by: "codex"
approved_by: "user"
approved_at: "2026-05-19T21:45:00+08:00"
source: "user"
linked_issue: ""
linked_change: "CR-005"
---

# CR-006：Tushare-first 数据方案与旧 data reference-only 护栏

> 2026-05-30T14:25:41+08:00 状态更新：G0 第一批 CR 状态收口已通过 `checkpoints/CP8-G0-CR-STATUS-CLOSURE-2026-05-30.md` 人工审查，CR-006 关闭。关闭依据为 CR006-BATCH-A 四张 Story CP7 与 batch summary 均 PASS；关闭不授权真实 Tushare 抓取、真实 lake read/write、旧 `data/**` 操作、凭据读取或 QMT 操作。

> 2026-05-19T22:32:37+08:00 状态更新：meta-qa/qa-wei 已完成 CR006-BATCH-A CP7 验证，四份 Story CP7 与 batch summary 均为 PASS。验证结果：S01 4 passed、S02 4 passed、S03 7 passed、S04 5 passed、CR006 聚合 20 passed、全量回归 127 passed。meta-po 已回填 QA handoff、STATE 与本 CR：CR006-BATCH-A 标记为 `verified`；由于本 CR 自动终验授权=false，未直接 `closed`，当前状态为 `verified-pending-user-close-decision`。仍不授权真实 Tushare 抓取、真实 lake read/write、旧 `data/**` 读取/列出/迁移/复制/比对/删除或 `.env` / token / NAS 凭据读取打印。

## 变更描述

CR-006 的当前权威口径已从“旧 `data/` 外置化并保留 fallback”收敛为 **Tushare-first 数据方案**。旧 `data/` 保持现状，仅供以后人工参考/比对；它不作为默认 fallback、不作为迁移源、不参与 Tushare 主路径，也不用于证明新链路可用。

本变更的核心结论如下：

1. `MARKET_DATA_LAKE_ROOT` 继续表示 `market_data/` structured lake 根目录，承载 raw / manifest / canonical / quality / catalog / gold 分层，并作为新链路事实源。
2. raw / manifest 必须保留，但职责限定为采集审计、断点续传、复现、replay 和质量追溯；轻量 engine 与 Backtrader 不得把 raw / manifest 当作运行时输入。
3. 轻量 engine 只能消费 canonical/gold reader，或消费由 canonical/gold 派生且带 lineage 的仓库外 external `legacy_flat`；external `legacy_flat` 不等同于旧 repo `data/`。
4. Backtrader 只能消费经过 quality gate、PIT as-of 和复权一致检查后的 clean OHLCV / factor / score feed。
5. 旧 repo `data/` 是 reference-only 历史样本；任何读取、列出、迁移、复制、比对或删除旧 `data/**` 的动作均不在本 CR 默认授权内，必须另行获得用户明确授权。

本 CR 不授权立即移动、删除或改写任何真实数据；不授权读取、展示或记录用户 `.env` 中的 token、NAS 用户名、密码或真实挂载凭据。

## 当前事实基线

> 本节仅保留 CR 创建时的历史事实基线，用于解释为什么需要将旧 `data/` 降级为 reference-only。它不是当前实现任务清单，也不授权读取、列出、迁移、复制、比对或删除真实 `data/**`。

### 历史记录：CR 创建时仓库内 `data/` 内容

截至 CR 创建时，仓库工作区内存在以下 legacy 数据资产：

| 路径 | 类型 | 说明 |
|---|---|---|
| `data/prices.parquet` | 扁平 parquet | 旧回测价格输入，约 59MB |
| `data/index_members.parquet` | 扁平 parquet | 旧回测股票池输入 |
| `data/trade_calendar.parquet` | 扁平 parquet | 旧回测交易日历输入 |
| `data/raw/**` | raw cache | 旧数据准备 raw 缓存 |
| `data/manifests/data_prep_manifest.jsonl` | manifest | 旧数据准备批次事实源 |
| `data/.gitkeep` | 占位文件 | 可继续保留 |

`.gitignore` 已忽略 `data/`、`*.parquet`、`*.jsonl` 等真实数据形态，说明真实数据不应归档到 GitHub。

### 历史记录：CR 创建时主要代码引用

| 位置 | 当前行为 | CR-006 影响 |
|---|---|---|
| `engine/data_loader.py` | 默认 `data_dir="data"`，默认 manifest 为 `data/manifests/data_prep_manifest.jsonl` | 当前 CR006-BATCH-A 不再以旧 fallback 为目标；后续轻量 engine 应消费 canonical/gold 或 external `legacy_flat` |
| `engine/data_prep.py` | 默认写 `data/raw` 和 `data/manifests/data_prep_manifest.jsonl` | 当前 CR006-BATCH-A 不迁移旧 raw/manifest；Tushare-first raw/manifest 由 structured lake 数据层拥有 |
| `engine/normalizer.py` | 默认从 `data/raw` 解析 raw 路径 | 当前 CR006-BATCH-A 不再要求解析旧 repo `data/raw` |
| `engine/contracts.py` | 定义 `prices.parquet`、`index_members.parquet`、`trade_calendar.parquet` 文件名 | 文件名契约保留，目录根可配置 |
| `experiments/run_experiment_06_07.py`、`08.py`、`09.py`、`10.py`、`12.py`、`13.py` | 通过 `data_dir / "trade_calendar.parquet"` 等读取扁平输入 | 需要统一使用 resolved data dir 或显式 CLI 参数 |
| `config/data_prep.yaml` | `raw_cache_path_pattern: "data/raw/{source}/{interface}/{yyyymmdd}/{batch_id}.{ext}"` | 需要迁移为可配置模板或外置默认 |
| `README.md`、`docs/USER-MANUAL.md` | 仍大量展示 `data/*.parquet` 和 `data/raw/**` legacy 示例 | 需要更新为外置 legacy data dir 说明 |

### 与 CR-005 的边界

CR-005 已建立 `MARKET_DATA_LAKE_ROOT` 作为结构化 market data lake。CR-006 不改变该决策，也不把旧 repo `data/` 或旧 flat parquet 直接塞入 `MARKET_DATA_LAKE_ROOT` 根目录。

推荐后续目录语义如下：

```text
<external-data-root>/
  market_data_lake/
    raw/
    manifest/
    canonical/
    quality/
    catalog/
    gold/
  legacy_flat/
    prices.parquet
    index_members.parquet
    trade_calendar.parquet
    raw/
    manifests/
```

`MARKET_DATA_LAKE_ROOT` 指向结构化 `market_data_lake/`。`legacy_flat/` 若存在，只能作为 canonical/gold 派生的外部兼容面，不是旧 repo `data/` 的迁移目标，也不是默认 fallback。

## 文档处理决策

| 受影响文档 | 处理方式 | 旧基线保留方式 | 修订记录位置 | 批准状态 |
|---|---|---|---|---|
| `process/USE-CASES.md` | 原文档更新 | 保留既有数据准备、离线回测和真实数据湖场景；CR-006 当前不再以 legacy 外置化为主线 | `## 修订记录` | superseded-by-tushare-first |
| `process/REQUIREMENTS.md` | 原文档更新 | 保留既有数据准备、离线边界、Tushare 数据湖、Backtrader 可选后端需求；旧 fallback 口径不再作为 CR-006 验收依据 | `## 修订记录` | superseded-by-tushare-first |
| `process/HLD.md` | 原文档更新 | §23 已重写为 Tushare-first structured lake、raw/manifest audit-only、runtime clean consumption、旧 `data/` reference-only | `## 0. 修订记录` | approved |
| `process/ARCHITECTURE-DECISION.md` | 原文档更新 | ADR-018 已重写为 Tushare-first structured lake 与运行时消费面分离 | 修订记录 | approved |
| `process/STORY-BACKLOG.md` | 原文档更新 | 保留 STORY-001..018 和 CR005-S01..S06 历史状态；新增 CR-006 Story，不重写已完成 Story | 修订记录 | pending |
| `process/DEVELOPMENT-PLAN.yaml` | 原文档更新 | 保留已完成 Wave / CR-005 Story 执行记录；新增 CR-006 Wave / DAG / 文件所有权 | 不适用 | pending |
| `process/stories/` | 新增 | 不适用 | Story 卡片与 LLD frontmatter | pending |
| `engine/**` | 后续修改 | 轻量 engine 消费 canonical/gold 或 external `legacy_flat`，不得默认 fallback 到旧 repo `data/` | 代码与测试 | pending-CP5 |
| `experiments/**` | 后续修改 | 实验入口继承轻量 engine 的 clean consumption 边界，不自动触发 fetch/backfill | 代码与测试 | pending-CP5 |
| `config/data_prep.yaml` | 不作为本批次主目标 | 不新增旧 legacy fallback 口径；Tushare-first 数据层配置仍由 CR005/CR006-S01 契约约束 | 不适用 | superseded-by-tushare-first |
| `README.md` / `docs/USER-MANUAL.md` | 原文档更新 | 说明旧 `data/` reference-only，不能作为 fallback、迁移源或覆盖证明 | 文档修订记录或相关章节 | pending-after-validation |
| `.env` / `.gitignore` | 原文档更新 | `.env` 不提交和真实数据不入 Git 的基线保留；新增 `LOCAL_BACKTEST_DATA_DIR` 占位说明，不记录真实值 | 不适用 | pending-CP5 |

## 旧基线映射

| 原基线对象 | 新增 / 修改对象 | 保留策略 | 映射说明 |
|---|---|---|---|
| 旧 repo `data/` | reference-only 历史样本 | 保持现状，不读取、不列出、不迁移、不删除 | 不作为 fallback、迁移源或新链路可用性证明 |
| 旧 flat 文件名契约 | external `legacy_flat` 可选派生面 | 仅保留文件名兼容语义 | 若 S02 需要 flat 形态，必须从 canonical/gold 派生到仓库外并带 lineage |
| 旧 `data/raw/**`、`data/manifests/**` | Tushare-first structured lake 的 raw / manifest | 只保留“审计/复现/质量追溯”职责 | 新 raw/manifest 属于 structured lake，不作为轻量 engine 或 Backtrader runtime 输入 |
| `MARKET_DATA_LAKE_ROOT` | structured market data lake 根目录 | 原文保留 | CR-006 不复用该变量承载旧 repo `data/` 或旧 flat parquet |
| README / USER-MANUAL 中 `data/` 示例 | reference-only 警示与 guardrail | 历史说明可保留但必须标注非默认输入 | 不得把旧 `data/` 写成 fallback、迁移源或覆盖证明 |

## 五维度影响分析

| 维度 | 评估问题 | 受影响对象 | 结论（true/false） | 处理动作 |
|------|----------|-----------|--------------------|---------|
| 需求层 | 是否新增、删除或重定义 REQ-* | `process/REQUIREMENTS.md`、Tushare 数据层、轻量 engine、Backtrader、旧 `data/` 护栏 | true | 以 Tushare-first、raw/manifest audit-only、runtime clean consumption、旧 `data/` reference-only 覆盖旧 externalization/fallback 口径 |
| 场景层 | 是否改变测试矩阵覆盖范围 | `process/USE-CASES.md`、数据获取、回测运行、Backtrader、文档护栏 | true | 覆盖 Tushare structured lake、canonical/gold、external `legacy_flat`、Backtrader clean feed 和 no-old-data guardrail |
| 计划层 | 是否改变 Phase、Wave、任务依赖 | HLD、ADR、Story 计划、LLD、engine / experiments / docs 修改 | true | 回退到 `solution-design`，由 meta-se 设计 resolver 和迁移边界，再按 CP4 / CP5 / CP6 / CP7 执行 |
| 安全层 | 是否引入新的高风险动作或权限要求 | NAS / 外置路径、`.env`、真实数据、删除本地 `data/**` | true | 不记录凭据，不输出真实 token，不自动删除数据；任何迁移、复制、删除必须用户显式授权；真实数据仍不入 Git |
| 交付层 | 是否需要重新生成交付物或回归子集 | README、USER-MANUAL、测试、guardrail | true | 更新文档和最小回归测试；验证旧 `data/` 不作为 fallback、迁移源或覆盖证明 |

## 回退决策

- 影响范围：中等结构性变更，主要影响 Tushare-first 数据事实源、轻量 engine / Backtrader 消费面和旧 `data/` reference-only 护栏，不改变 CR-005 结构化数据湖主线。
- 回退到阶段：`solution-design`
- 需要重新确认的对象：
  - HLD：Tushare-first structured lake、raw/manifest audit-only、runtime clean consumption、旧 `data/` reference-only。
  - ADR：ADR-018 的事实源、运行时消费面和旧 `data/` 护栏。
  - Story 计划：S01 acquisition/runbook、S02 lightweight adapter、S03 Backtrader clean feed、S04 old data guardrail。
  - 安全边界：不自动复制 / 删除真实数据，不记录凭据，不把真实数据提交到 Git。
  - 验证策略：默认离线 fixture、no-token/no-network、no old data read/list/migrate/delete、raw/manifest 非 runtime 输入。

## LLD 设计批次门禁

- 是否需要 LLD 设计批次：true
- batch_id：`CR006-BATCH-A`
- 批次范围来源：CR 影响分析
- 批次内 Story：
  - `CR006-S01-tushare-first-data-acquisition-runbook`
  - `CR006-S02-canonical-gold-lightweight-engine-adapter`
  - `CR006-S03-backtrader-clean-feed-contract`
  - `CR006-S04-old-data-reference-only-guardrail`
- 批次人工确认稿：`checkpoints/CP5-CR006-BATCH-A-LLD-BATCH.md`
- 开发启动条件：
  - [x] 批次内全部 Story LLD 已输出
  - [x] 批次内全部 Story CP5 自动预检已通过
  - [x] 批次 CP5 人工确认结论为 `approved`
  - [x] 批次内每个 Story 的 `dev_gate` 已满足
  - [ ] 若涉及真实数据读取、列出、迁移、复制、比对或删除，必须获得用户显式授权并记录执行范围
  - [ ] 不得读取或打印 `.env`、Tushare token、NAS 用户名、密码或真实私有路径

## Dev Wave 调度计划

CP5 已批准，代码实现已由主线程真实调度 meta-dev 执行并完成 CP6；CP7 已由 meta-qa/qa-wei 完成并 PASS，BATCH-A 已 verified。由于自动终验授权=false，本变更单仍不表示 CR-006 已 closed。

| Wave | Story | handoff | 并行结论 | 文件所有权 / 依赖 |
|---|---|---|---|---|
| `CR006-DEV-W1` | `CR006-S01-tushare-first-data-acquisition-runbook` | `process/handoffs/META-DEV-CR006-BATCH-A-DEV-W1-S01-2026-05-19.md` | 单独启动 | 写 `market_data/cli.py`、`market_data/connectors/tushare.py`、`market_data/storage.py`、`market_data/normalization.py`、`market_data/validation.py`、`market_data/catalog.py` 和 S01 测试；不写 engine/docs。 |
| `CR006-DEV-W2` | `CR006-S02-canonical-gold-lightweight-engine-adapter` | `process/handoffs/META-DEV-CR006-BATCH-A-DEV-W2-S02-2026-05-19.md` | 等 W1 CP6 PASS 后单独启动 | 写 `engine/data_loader.py`、`engine/backtest.py`、experiments、`market_data/readers.py` 和 S02 测试。S02 与 S03 共享 `market_data/readers.py`、`engine/backtest.py`，必须串行。 |
| `CR006-DEV-W3` | `CR006-S03-backtrader-clean-feed-contract` | `process/handoffs/META-DEV-CR006-BATCH-A-DEV-W3-S03-2026-05-19.md` | W2 CP6 PASS 后可与 S04 并行 | 写 `engine/backtrader_adapter.py`、`engine/backtest.py`、`market_data/readers.py` 和 S03 测试；不写 docs。 |
| `CR006-DEV-W3` | `CR006-S04-old-data-reference-only-guardrail` | `process/handoffs/META-DEV-CR006-BATCH-A-DEV-W3-S04-2026-05-19.md` | W2 CP6 PASS 后可与 S03 并行 | 写 `README.md`、`docs/USER-MANUAL.md`、`.gitignore` 和 S04 测试；不写 engine/market_data。若 guardrail 最终测试需扫描 S03 新代码，应在 S03 完成后再确认 S04 CP6 测试结果。 |

## CP6 开发完成汇总

| Story | Agent | CP6 | 修改范围摘要 | 测试证据 |
|---|---|---|---|---|
| `CR006-S01` | `dev-kong` / `019e3b8b-1448-74f0-adff-c217808e4374` | `process/checks/CP6-CR006-S01-tushare-first-data-acquisition-runbook-CODING-DONE.md` PASS | `market_data/cli.py`、`market_data/connectors/tushare.py`、S01 测试 | S01 4 passed；扩展 27 passed |
| `CR006-S02` | `dev-zhu` / `019e3b8b-14a3-78a2-942b-4c696480fd80` | `process/checks/CP6-CR006-S02-canonical-gold-lightweight-engine-adapter-CODING-DONE.md` PASS | `market_data/readers.py`、`engine/data_loader.py`、`engine/backtest.py`、experiments、S02 测试 | S02 4 passed；相关 57 passed；S01 扩展 27 passed；全量 115 passed |
| `CR006-S03` | `dev-he` / `019e3b8b-953b-70e0-be88-c412fc25ed2d` | `process/checks/CP6-CR006-S03-backtrader-clean-feed-contract-CODING-DONE.md` PASS | `market_data/readers.py`、`engine/backtrader_adapter.py`、`engine/backtest.py`、S03 测试 | S03 7 passed；相关 36 passed；import-boundary 8 passed；全量 127 passed |
| `CR006-S04` | `dev-yang` / `019e3b90-7cf6-7b32-9a77-45017825307e` | `process/checks/CP6-CR006-S04-old-data-reference-only-guardrail-CODING-DONE.md` PASS | `README.md`、`docs/USER-MANUAL.md`、`.gitignore`、S04 测试 | S04 5 passed；post-S03 聚合验证 20 passed；全量 127 passed |

CP6 安全边界：四个 dev 均声明未读取、列出、迁移、复制、比对或删除真实 `data/**`，未读取/打印 `.env`、真实 token 或 NAS 凭据，未执行真实 Tushare/lake/normalize/revalidate/replay job。

## CP7 验证完成汇总

- handoff：`process/handoffs/META-QA-CR006-BATCH-A-CP7-VERIFY-2026-05-19.md`
- 执行 agent：`meta-qa/qa-wei`
- dispatch evidence：主线程回报 qa-wei 已完成；CP7 文件未暴露 spawn/resume metadata，本 CR 不伪造 agent_id/thread_id。
- 输出：
  - `process/checks/CP7-CR006-S01-tushare-first-data-acquisition-runbook-VERIFICATION-DONE.md`：PASS，4 passed
  - `process/checks/CP7-CR006-S02-canonical-gold-lightweight-engine-adapter-VERIFICATION-DONE.md`：PASS，4 passed
  - `process/checks/CP7-CR006-S03-backtrader-clean-feed-contract-VERIFICATION-DONE.md`：PASS，7 passed
  - `process/checks/CP7-CR006-S04-old-data-reference-only-guardrail-VERIFICATION-DONE.md`：PASS，5 passed
  - `process/checks/CP7-CR006-BATCH-A-VERIFICATION-SUMMARY-2026-05-19.md`：PASS
- 聚合验证：四个 CR006 测试文件 20 passed
- 全量回归：`uv run --python 3.11 pytest -q` -> 127 passed
- CP7 安全边界：QA 声明未读取/列出/迁移/复制/比对/删除真实 `data/**`，未读取/打印 `.env`、token、NAS 凭据，未执行真实 Tushare/lake/normalize/validate/read/replay/backfill job。

## 推荐 Story 拆分

| Story | 目标 | 建议文件范围 | 说明 |
|---|---|---|---|
| CR006-S01 | Tushare-first 数据获取与 runbook | `market_data/cli.py` 或等价 job、`market_data/connectors/tushare.py`、`market_data/storage.py`、`market_data/normalization.py`、`market_data/validation.py`、runbook/测试 | 冻结 Tushare-first acquisition、raw/manifest 审计职责、canonical/gold 产出和 no-old-data 采集边界 |
| CR006-S02 | canonical/gold 到轻量 engine 适配 | `engine/data_loader.py`、`engine/backtest.py`、`experiments/run_experiment_*.py`、`market_data/readers.py`、adapter 测试 | 轻量 engine 消费 canonical/gold 或由 canonical/gold 派生的 external `legacy_flat`；不默认读取旧 repo `data/` |
| CR006-S03 | Backtrader clean feed contract | `engine/backtrader_adapter.py`、`engine/backtest.py` 或 selector、`market_data/readers.py`、feed contract 测试 | Backtrader 只消费 quality gate 后 clean OHLCV/factor/score feed；不读 token/raw/manifest，不触发补数 |
| CR006-S04 | 旧 data reference-only 护栏 | `README.md`、`docs/USER-MANUAL.md`、`.gitignore`、guardrail 测试或静态检查 | 固化旧 `data/` reference-only；不作为 fallback、迁移源或覆盖证明；不执行清理 |

## 设计约束

1. Tushare structured lake 是 CR-006 新数据事实源；旧 repo `data/` 不参与事实源证明。
2. raw/manifest 必须存在，但仅用于采集审计、断点续传、复现、replay 和质量追溯，不作为轻量 engine 或 Backtrader runtime 输入。
3. 轻量 engine 只能消费 canonical/gold reader，或消费由 canonical/gold 派生且带 lineage 的仓库外 external `legacy_flat`。
4. external `legacy_flat` 不等同于旧 repo `data/`，不得从旧 repo `data/` 静默复制或迁移生成。
5. Backtrader 只能消费 quality gate 后 clean feed；不得读取 raw/manifest/token，不得导入 connector/runtime/storage，不得联网或补数。
6. 旧 repo `data/` 只能 reference-only；默认运行、测试和 smoke 对旧 repo `data/` 的读取次数必须为 0。
7. 旧数据覆盖性比对、迁移、复制、删除或目录列举必须另行获得用户明确授权。
8. 不在 CR、README、USER-MANUAL、manifest、quality、catalog、测试 fixture 或日志中记录 token、NAS 用户名、密码或真实凭据。
9. 默认测试不得依赖用户真实 NAS、token、联网或真实 Tushare fetch；必须使用 fake/offline fixture、`tmp_path` 或受控本地夹具。
10. 文档示例只能使用占位路径，如 `<external-data-root>/market_data_lake` 或 `<external-data-root>/legacy_flat`，不得记录真实私有路径。
11. Notebook 的 `data/ohlcv.csv` 示例属于用户自备研究数据，不应被自动迁移或纳入 structured lake。
12. CP5 required fixes 已清零并由用户人工 approved；后续只能按 dev handoff 调度 meta-dev，实现过程中仍不得抓取真实 Tushare、不写真实 lake、不触碰旧 `data/**`、不读取或打印凭据，并必须继续经过 CP6/CP7。

## 验收口径

| 编号 | 验收项 | 通过标准 |
|---|---|---|
| CR006-AC-001 | Tushare-first 事实源 | HLD §23 与 ADR-018 中明确 Tushare structured lake 是新链路事实源，旧 repo `data/` 不用于证明新链路可用 |
| CR006-AC-002 | raw/manifest 审计层 | raw/manifest 仅用于采集审计、断点续传、复现、replay 和质量追溯；轻量 engine 与 Backtrader runtime 读取 raw/manifest 的次数为 0 |
| CR006-AC-003 | no old data acquisition dependency | S01 采集/runbook 不读取、列出、迁移、复制、比对或删除旧 `data/**`；旧数据覆盖性分析必须另行授权 |
| CR006-AC-004 | 轻量 engine canonical/gold 消费 | 轻量 engine 运行输入来自 canonical/gold reader 或由 canonical/gold 派生且带 lineage 的 external `legacy_flat` |
| CR006-AC-005 | quality gate 阻断 | canonical/gold 或派生输入的 quality fail / required_missing 必须结构化阻断运行，不自动 fallback 到旧 repo `data/` |
| CR006-AC-006 | no repo data fallback | 默认运行、默认测试和 smoke 对旧 repo `data/` 的消费次数为 0；旧 repo `data/` 不作为 fallback |
| CR006-AC-007 | Backtrader clean feed | Backtrader 只消费 quality gate、PIT as-of 和复权一致检查后的 clean OHLCV / factor / score feed |
| CR006-AC-008 | Backtrader 禁止边界 | Backtrader 不读取 token/raw/manifest，不导入 connector/runtime/storage，不联网，不触发 fetch/backfill/normalize job |
| CR006-AC-009 | 安全与默认离线 | 默认测试使用 fake/offline fixture、`tmp_path` 或受控本地夹具；不输出、不提交、不记录 token、NAS 用户名、密码、真实凭据或真实私有路径 |
| CR006-AC-010 | external `legacy_flat` lineage | external `legacy_flat` 若交付，只能由 canonical/gold 派生并携带 catalog/manifest lineage；不得从旧 repo `data/` 静默复制或迁移 |
| CR006-AC-011 | 消费层不自动补数 | 轻量 engine、experiments、Backtrader 和 Notebook 不触发 Tushare fetch/backfill；缺数据只返回 typed error / remediation spec |
| CR006-AC-012 | old data reference-only | README、USER-MANUAL、`.gitignore` 或 guardrail 明确旧 repo `data/` 仅供以后人工参考/比对 |
| CR006-AC-013 | no fallback / migration source / proof | 文档与 guardrail 明确旧 repo `data/` 不作为 fallback、迁移源、覆盖证明或 Tushare-first 可用性证明 |
| CR006-AC-014 | 旧数据授权门禁 | 任何旧 `data/**` 读取、列出、迁移、复制、比对或删除动作都需要用户另行明确授权并记录范围；默认 dev/qa 范围内次数为 0 |

## 执行链路

| 顺序 | 责任角色 | 动作 | 输入 | 输出 | 门控 | 完成后下一步 |
|---|---|---|---|---|---|---|
| 1 | `meta-po` | 创建 CR 并登记 active_change | 用户请求、`STATE.md`、当前代码引用清单 | 本 CR、状态更新 | CR 已登记 | 等待 CR-006 方案确认 |
| 2 | `meta-se` | 修订 HLD / ADR / Story 计划 | 本 CR、CR-004/CR-005 数据边界、当前代码引用 | HLD/ADR/Story Plan 修订、Story 卡片、DAG | CP3 / CP4 | 交给 meta-dev 做 LLD |
| 3 | `meta-dev` | 完成 CR006 批次 LLD 与实现 | 已确认 Story、CP5、CR | 配置解析、路径迁移、测试、CP6 证据 | CP5 / CP6 | 交给 meta-qa |
| 4 | `meta-qa` | 验证路径、回归和安全边界 | CR、实现结果、LLD、测试命令 | CP7 验证、回归结果、安全检查 | CP7 | 交回 meta-po |
| 5 | `meta-doc` | 更新 README / USER-MANUAL / runbook | CR、实现结果、验证结论 | 文档更新 | 文档自检 | 交回 meta-po |
| 6 | `meta-po` | 收敛终验与关闭决策 | 下游结果、CR、检查点 | CP8 或 CR 收敛检查 | 用户确认 | 关闭 CR 或路由返工 |

## 自动终验授权

- 是否启用：false
- 授权范围：不适用
- 适用检查点：CP8 / CR-006 收敛检查
- 自动通过条件：
  - [ ] 自动预检结论为 `PASS`
  - [ ] 无 `BLOCKING`
  - [ ] 无 `REQUIRED`
  - [ ] 授权动作明确包含关闭 CR 和 / 或推进下一阶段
- 授权原文：
- 授权时间：
- 回填要求：若生效，人工审查稿必须标注 `approval_source=user-preauthorized`

## 处理结论

- 审批结论：`cp7-pass-batch-a-verified-pending-close`
- [ ] 自动批准（低风险）
- [x] 已人工确认进入 solution-design 修订链路（中风险）
- [x] CP3 HLD / ADR 人工确认已通过
- [x] CP4 Story Plan 人工确认已通过
- [x] CP5 Batch A 人工确认已通过
- [x] CP6 Batch A 编码完成检查已通过
- [x] CP7 Batch A 验证已通过
- [x] BATCH-A 已 verified
- [ ] CR-006 待用户关闭确认

CR-006 属于中风险结构性变更。当前 `CR006-BATCH-A` 四张 Story 的 LLD 与四份 CP5 自动预检均已完成且 PASS；双 lane review 的 5 个 REQUIRED findings 已在 post-fix 聚合中核验关闭，剩余 `CR006-ADV-002` 为非阻断建议。数据分层、存储格式与对外接口契约的 CP5 审查上下文已由 meta-se/se-wei 完成，结论 `PASS_FOR_CONTEXT_APPENDIX`，并已纳入 CP5 人工稿审查上下文。用户已批准 `checkpoints/CP5-CR006-BATCH-A-LLD-BATCH.md`；四个 Story 已完成 CP6 PASS；CP7 已由 meta-qa/qa-wei 验证 PASS，BATCH-A 已 verified。由于自动终验授权=false，CR-006 未直接 closed；当前等待用户回复 `approve` / `修改: <具体修改点>` / `reject`。当前仍不授权真实 Tushare 抓取、不授权读取/列出/迁移/复制/比对/删除旧 `data/**`，也不授权读取或打印 `.env` / token / NAS 凭据。

## meta-po 组织分析记录

| 时间 | 组织分析结论 | 证据 | 后续门控 |
|---|---|---|---|
| 2026-05-18T21:12:35+08:00 | CR-006 影响分析已收敛；保持 `status=open`、`approval_result=pending`、`rollback_to=solution-design`。需要 meta-se 修订 HLD / ADR / Story Plan / Development Plan；需要 CP3、CP4；需要 `CR006-BATCH-A` 全量 LLD 与 CP5 统一确认。 | `process/checks/CR006-IMPACT-CONVERGENCE-2026-05-18.md`、`process/handoffs/META-SE-CR006-LEGACY-DATA-DIRECTORY-DESIGN-2026-05-18.md` | 用户批准前不得调度正式设计修订；CP3/CP4/CP5 通过前不得实施 `engine/**`、`experiments/**`、`config/**`、README 或 USER-MANUAL 修改。 |
| 2026-05-18T21:27:21+08:00 | 用户回复“通过”，按规则等同 `approve`；CR-006 组织分析获批进入 `solution-design` 修订链路。主线程已通过 Codex `spawn_agent` 真实调度 meta-se/se-jiang，agent_id/thread_id=`019e3b45-76a7-7e00-a354-f4fd9e76fba4`。 | `process/handoffs/META-SE-CR006-LEGACY-DATA-DIRECTORY-DESIGN-2026-05-18.md`、`process/STATE.md` | 等待 meta-se 输出 HLD / ADR / Story Plan / Development Plan 修订和 CP3/CP4 预检；CP3/CP4/CP5 通过前仍不得实施 `engine/**`、`experiments/**`、`config/**`、README 或 USER-MANUAL 修改。 |
| 2026-05-18T21:40:53+08:00 | meta-se/se-jiang 已完成 HLD / ADR / Story Plan / Development Plan 修订，CP3 / CP4 自动预检均为 `PASS`。meta-po 已生成 CP3 人工审查稿。 | `process/HLD.md`、`process/ARCHITECTURE-DECISION.md`、`process/STORY-BACKLOG.md`、`process/DEVELOPMENT-PLAN.yaml`、`process/checks/CP3-CR006-HLD-PRECHECK.md`、`process/checks/CP4-CR006-STORY-PLAN-PRECHECK.md`、`checkpoints/CP3-CR006-HLD-REVIEW.md` | 等待用户确认 CP3；CP3 approved 后再发起 CP4 人工确认。CP4/CP5 前不得实现。 |
| 2026-05-18T22:13:32+08:00 | 用户在 CP3 前提出修改意见后，meta-se/se-shen 已将 CR-006 修订为 Tushare-first 数据方案：旧 `data/` 保持现状仅供以后参考；Tushare structured lake 为新事实源；raw/manifest 保留为审计和复现层，不作为轻量回测或 Backtrader runtime 输入；CP3/CP4 自动预检重跑均 `PASS`。 | `process/HLD.md`、`process/ARCHITECTURE-DECISION.md`、`process/STORY-BACKLOG.md`、`process/DEVELOPMENT-PLAN.yaml`、`process/checks/CP3-CR006-HLD-PRECHECK.md`、`process/checks/CP4-CR006-STORY-PLAN-PRECHECK.md`、`checkpoints/CP3-CR006-HLD-REVIEW.md` | 等待用户确认新的 CP3；CP3 approved 后再发起 CP4。CP4/CP5 前不得实现，不得读取/比对/迁移/删除旧 `data/**`。 |
| 2026-05-18T22:33:23+08:00 | 用户回复“全部接受”，按本轮指令视为对 Tushare-first CP3 审查稿和四 Story CP4 Story Plan 的批准。meta-po 已回填 `checkpoints/CP3-CR006-HLD-REVIEW.md` 与 `checkpoints/CP4-CR006-STORY-PLAN-REVIEW.md` 为 approved，并将 CR006-BATCH-A 推进到 LLD-ready。 | `checkpoints/CP3-CR006-HLD-REVIEW.md`、`checkpoints/CP4-CR006-STORY-PLAN-REVIEW.md`、`process/handoffs/META-DEV-CR006-S01-LLD-2026-05-18.md`、`process/handoffs/META-DEV-CR006-S02-LLD-2026-05-18.md`、`process/handoffs/META-DEV-CR006-S03-LLD-2026-05-18.md`、`process/handoffs/META-DEV-CR006-S04-LLD-2026-05-18.md` | 等待主线程按 max_parallel_lld=3 真实并行调度 meta-dev 起草 S01/S02/S03 LLD；S04 建议第二轮。CP5 全量确认前不得实现，仍不得读取/列出/迁移/复制/比对/删除旧 `data/**` 或读取 `.env` / 凭据。 |
| 2026-05-18T23:01:45+08:00 | 主线程真实并行调度的四个 meta-dev LLD 子 agent 均已完成；四份 LLD 与四份 CP5 自动预检均已核验 PASS，四份 handoff 均含 `spawn_agent` 调度证据。meta-po 已生成 `checkpoints/CP5-CR006-BATCH-A-LLD-BATCH.md`，CR-006 进入 CP5 batch review pending。 | `checkpoints/CP5-CR006-BATCH-A-LLD-BATCH.md`、四份 `process/stories/CR006-S0*-*-LLD.md`、四份 `process/checks/CP5-CR006-S0*-*-LLD-IMPLEMENTABILITY.md`、四份 `process/handoffs/META-DEV-CR006-S0*-LLD-2026-05-18.md`、`process/STATE.md` | 等待用户回复 `approve` / `修改: <具体修改点>` / `reject`。CP5 approved 前不得实现，仍不得真实抓取、不得读取/列出/迁移/复制/比对/删除旧 `data/**` 或读取 `.env` / 凭据。 |
| 2026-05-18T23:24:55+08:00 | 主线程真实并行调度 meta-se/se-wei 与 meta-qa/qa-wei 对 CR006-BATCH-A 四份 LLD 做双 lane review；两条 lane 均为 `PASS_WITH_REQUIRED`。meta-po 聚合为 blocking=0、REQUIRED=5、ADVISORY=2，CP5 不可 approve，进入 required fixes pending。 | `process/checks/REVIEW-CR006-BATCH-A-LLD-META-SE-2026-05-18.md`、`process/checks/REVIEW-CR006-BATCH-A-LLD-META-QA-2026-05-18.md`、`process/checks/REVIEW-CR006-BATCH-A-LLD-SUMMARY-2026-05-18.md`、`checkpoints/CP5-CR006-BATCH-A-LLD-BATCH.md`、`process/STATE.md` | 主线程需真实调度 required fixes：meta-se 修订 CR-006/Story Backlog/Development Plan；meta-dev 分别修订 S02/S03/S04 LLD 与 CP5 自动预检。REQUIRED 清零前不得 approve CP5 或进入实现。 |
| 2026-05-19T00:01:52+08:00 | meta-po/po-sun 完成 post-fix 聚合，spawn_agent agent_id/thread_id=`019e3bd0-969f-7ab1-87a9-2ecfb3b0d0f3`：计划侧检查 PASS；S02/S03/S04 CP5 均 PASS；`CR006-REQ-001..005` 已有关闭证据。聚合结论 blocking=0、REQUIRED=0、ADVISORY=1，CP5 可重新提交用户人工确认，但未批准 CP5，implementation_allowed=false。 | `process/checks/REVIEW-CR006-BATCH-A-LLD-POST-FIX-2026-05-18.md`、`process/checks/REVIEW-CR006-BATCH-A-LLD-PLAN-FIX-2026-05-18.md`、四份 CR006 CP5 自动预检、`checkpoints/CP5-CR006-BATCH-A-LLD-BATCH.md`、`process/STATE.md` | 等待用户回复 `approve` / `修改: <具体修改点>` / `reject`。CP5 approved 前不得实现，仍不得真实抓取、不得读取/列出/迁移/复制/比对/删除旧 `data/**` 或读取 `.env` / 凭据。 |
| 2026-05-19T21:18:31+08:00 | meta-po/po-sun 将用户最新要求路由为 `minor_doc_fix_before_cp5`：只补充 CP5 审查上下文或轻量设计附录，不刷新 HLD/ADR、不重跑 CP3、不重制 Story、不重跑 CP4、不批准 CP5、不进入实现。已创建 meta-se handoff，建议主线程真实调度 meta-se 起草 `CR006 数据分层、存储格式与对外接口契约` 附录。 | `process/checks/CR006-HLD-STORY-REFRESH-EVALUATION-2026-05-19.md`、`process/checks/CR006-CP5-CONTEXT-FIX-ROUTING-2026-05-19.md`、`process/handoffs/META-SE-CR006-DATA-CONTRACT-CP5-CONTEXT-2026-05-19.md`、`checkpoints/CP5-CR006-BATCH-A-LLD-BATCH.md`、`process/STATE.md` | 主线程需真实 resume/spawn meta-se 并回填 dispatch evidence；附录完成后恢复 CP5 人工确认。CP5 approved 前不得实现，仍不得真实抓取、不得读取/列出/迁移/复制/比对/删除旧 `data/**` 或读取 `.env` / 凭据。 |
| 2026-05-19T21:31:58+08:00 | meta-se/se-wei 已按 handoff 完成 CP5 前轻量附录，dispatch mode=`resume_agent`，agent_id/thread_id=`019e3bab-199f-7f21-a772-c6ffaae65f95`，结果 `PASS_FOR_CONTEXT_APPENDIX`。meta-po 已恢复 CP5 人工确认入口为 `ready_for_user_review` / `pending_user_review`。 | `process/checks/CR006-DATA-CONTRACT-CP5-CONTEXT-2026-05-19.md`、`process/handoffs/META-SE-CR006-DATA-CONTRACT-CP5-CONTEXT-2026-05-19.md`、`process/checks/CR006-CP5-CONTEXT-FIX-ROUTING-2026-05-19.md`、`checkpoints/CP5-CR006-BATCH-A-LLD-BATCH.md`、`process/STATE.md` | 等待用户回复 `approve` / `修改: <具体修改点>` / `reject`。CP5 approved 前不得实现，仍不得真实抓取、不得读取/列出/迁移/复制/比对/删除旧 `data/**` 或读取 `.env` / 凭据。 |
| 2026-05-19T21:45:00+08:00 | 用户回复“通过，唤醒meta-po，并行拉起子agent完成story的开发。”，按 CP5 `approve` 处理。meta-po 已回填 CP5 人工稿为 `approved`，四份 LLD 已标记 confirmed/implementation_allowed，并创建 dev handoff。调度计划为 W1/S01 -> W2/S02 -> W3/S03+S04；S02/S03 因共享 `market_data/readers.py`、`engine/backtest.py` 必须串行，S03/S04 可并行。 | `checkpoints/CP5-CR006-BATCH-A-LLD-BATCH.md`、四份 CR006 LLD、`process/handoffs/META-DEV-CR006-BATCH-A-DEV-W1-S01-2026-05-19.md`、`process/handoffs/META-DEV-CR006-BATCH-A-DEV-W2-S02-2026-05-19.md`、`process/handoffs/META-DEV-CR006-BATCH-A-DEV-W3-S03-2026-05-19.md`、`process/handoffs/META-DEV-CR006-BATCH-A-DEV-W3-S04-2026-05-19.md`、`process/STATE.md` | 主线程应先真实调度 W1/S01 meta-dev；W1 CP6 PASS 后调度 W2/S02；W2 CP6 PASS 后并行调度 W3/S03 与 W3/S04。仍不得真实抓取、不得读取/列出/迁移/复制/比对/删除旧 `data/**` 或读取 `.env` / 凭据；不得跳过 CP6/CP7。 |
| 2026-05-19T22:25:00+08:00 | 四个 dev Story 已完成 CP6 PASS：S01/dev-kong、S02/dev-zhu、S03/dev-he、S04/dev-yang。meta-po 已回填 dev handoff 调度证据并创建 CP7 meta-qa 验证 handoff。 | 四份 CP6 文件、四份 dev handoff、`process/handoffs/META-QA-CR006-BATCH-A-CP7-VERIFY-2026-05-19.md`、`process/STATE.md` | 主线程应真实调度 meta-qa/qa-wei 执行 CP7。CP7 全部 PASS 前不得标记 CR-006 verified/closed；仍不得真实抓取、不得读取/列出/迁移/复制/比对/删除旧 `data/**` 或读取 `.env` / 凭据。 |
| 2026-05-19T22:32:37+08:00 | meta-qa/qa-wei 已完成 CP7 验证，四份 Story CP7 与 batch summary 均 PASS；S01 4 passed、S02 4 passed、S03 7 passed、S04 5 passed、CR006 聚合 20 passed、全量回归 127 passed。meta-po 已回填 QA handoff、STATE 与本 CR，CR006-BATCH-A 标记为 verified。 | 四份 CP7 Story 文件、`process/checks/CP7-CR006-BATCH-A-VERIFICATION-SUMMARY-2026-05-19.md`、`process/handoffs/META-QA-CR006-BATCH-A-CP7-VERIFY-2026-05-19.md`、`process/STATE.md`、本 CR | 因自动终验授权=false，CR-006 未直接 closed；等待用户回复 `approve` / `修改: <具体修改点>` / `reject`。关闭前仍不得真实抓取、不得读取/列出/迁移/复制/比对/删除旧 `data/**` 或读取 `.env` / 凭据。 |

## 关联对象

| 类型 | 标识 | 说明 |
|---|---|---|
| 变更 | CR-005 | 已确认 structured market data lake 与 `MARKET_DATA_LAKE_ROOT`，CR-006 不改变该边界 |
| 模块 | `engine/data_loader.py` | legacy parquet 加载入口 |
| 模块 | `engine/data_prep.py` | legacy raw / manifest 写入入口 |
| 模块 | `engine/normalizer.py` | legacy raw 到 flat parquet 标准化入口 |
| 模块 | `experiments/run_experiment_06_07.py`、`08.py`、`09.py`、`10.py`、`12.py`、`13.py` | legacy `data_dir` 消费方 |
| 配置 | `config/data_prep.yaml` | raw cache path pattern |
| 文档 | `README.md`、`docs/USER-MANUAL.md` | 需要更新路径说明、`.env` 配置和迁移 runbook |
| 数据 | `data/*.parquet`、`data/raw/**`、`data/manifests/**` | 后续用户授权后迁移 / 清理对象 |
