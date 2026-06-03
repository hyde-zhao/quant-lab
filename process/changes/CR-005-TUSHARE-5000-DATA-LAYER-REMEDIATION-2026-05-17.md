---
cr_id: "CR-005"
status: "closed"
impact_level: "high"
rollback_to: "solution-design"
approval_result: "approved-story-execution-verified-closed"
created_at: "2026-05-17T16:25:00+08:00"
updated_at: "2026-05-30T14:25:41+08:00"
closure_state: "closed-by-g0-status-closure"
closure_decision_required_by: "user"
closed: true
closed_by: "meta-po"
closed_at: "2026-05-30T14:25:41+08:00"
closure_checkpoint: "checkpoints/CP8-G0-CR-STATUS-CLOSURE-2026-05-30.md"
close_approval_text: "@meta-po 好的按照你推荐的顺序，逐步完成。"
created_by: "codex"
approved_by: "user"
approved_at: "2026-05-17T19:13:17+08:00"
source: "user"
linked_change: "CR-004"
included_scope:
  - "Tushare 5000 real data source remediation"
  - "PIT as-of alignment and adjusted price data-layer contract"
  - "Backtrader optional backtest backend integration planning"
---

# CR-005：Tushare 5000 积分后的数据层整改与 Backtrader 可选后端接入

> 2026-05-30T14:25:41+08:00 状态更新：G0 第一批 CR 状态收口已通过 `checkpoints/CP8-G0-CR-STATUS-CLOSURE-2026-05-30.md` 人工审查，CR-005 关闭。关闭依据为 CR005-S01..S06 已 verified，后置文档收敛静态复核 PASS；关闭不授权真实 provider fetch、真实 lake 写入、凭据读取、旧 `data/**` 操作或 QMT 操作。

## 变更描述

用户准备购买 Tushare 5000 积分档，希望评估并推进数据层整改，使当前 `market_data/` 可迁移数据组件从“真实 Tushare fail-fast 边界”升级为“可控启用的 Tushare 真实采集源”，并补齐真实沪深 300 指数、指数权重、交易日历、股票复权价格等本地数据湖 dataset。

本变更不要求推倒当前架构。当前 CR-004 已建立的方向继续保留：

1. `market_data/` 作为独立可迁移包。
2. Parquet 数据湖作为本地事实源。
3. raw + manifest + canonical + quality + catalog 分层。
4. Data Loader、实验十、实验十二只读本地数据，不直接调用远端接口。
5. 默认测试路径 fake/offline，不依赖 Tushare token，不联网。

本变更的核心是：购买 Tushare 5000 后，将 Tushare 纳入本地数据湖和质量门体系，而不是把 Tushare API 直接接入回测或实验主路径。

本次用户同时提出“在回测框架中集成 Backtrader”。经 meta-po 按变更影响规则判定，Backtrader 不另建正式项目，也不新建 CR-006；它并入 CR-005，作为同一主项目内的“可选回测后端接入”新增 Story 候选。理由如下：

1. Tushare 与 Backtrader 的共同交界面都是本地 `canonical/gold` 数据契约：Tushare 负责写入本地数据湖，Backtrader 只消费本地事实源。
2. Backtrader 若独立成 CR-006，会在 CR-005 的 dataset schema、reader、quality gate 尚未确认前重复设计数据适配层，增加返工和口径漂移。
3. 当前项目仍以项目内轻量回测层为主路径；Backtrader 只是可选后端，不替代 `engine/backtest.py`，不改变默认离线测试路径。
4. Backtrader 接入不得读取 `TUSHARE_TOKEN`，不得联网，不得调用 Tushare adapter；其输入只能来自 `market_data.readers` 或经 CP5 确认的本地 adapter。
5. `pyproject.toml` 中的 `backtrader` 依赖只能在后续 CP5 批次人工确认通过后，通过 uv 规则加入；本变更阶段只做规划，不改依赖锁文件。

本次 CP3/CP4 人工确认前追加修改点已并入 CR-005，不新建 CR-006：PIT、复权和 Backtrader 的职责边界必须在 CR 文档、HLD、ADR、Story 计划和 CR005-S02/S03/S06 中统一落地。新增口径如下：

1. PIT 由 Pandas 数据层保证。所有非行情数据必须携带并消费 `available_date` / `effective_date` / `available_at`，在生成因子面板、score 或 Backtrader feed 前完成 as-of join；任一回测日只能看到当时已可得的数据。
2. 复权由行情层保证。行情 canonical/gold 必须保存 `adj_factor` 与统一 `adjustment_policy` 下的 adjusted price；价格收益、技术指标和 forward return 均使用同一复权价格口径计算。
3. Backtrader 只消费数据层产出的干净 `factor_panel` / `score` / OHLCV feed，只负责调仓、成交、成本、仓位、净值和风险分析。
4. Backtrader 不生成 PIT、不计算复权因子、不读取 Tushare、不联网、不绕过 quality gate；CR005-S06 的开发门控必须显式依赖 CR005-S02/CR005-S03 的 PIT、复权和 quality gate 契约稳定。

第三轮评审后追加两步补齐契约，替代原 CP3/CP4 旧稿中的隐含描述：

1. 消费层包括 Data Loader、实验入口、benchmark resolver、Backtrader adapter。消费层缺少本地 `hs300_index` 时只返回 typed `unavailable` / `required_missing` / `quality_failed`，可以携带 `next_action` 和 `remediation_job_spec`，但不得自动执行 fetch、backfill、normalize、validate 或 catalog 更新。
2. 数据层只在用户显式执行 `market_data` Tushare fetch/backfill job 时才允许联网并写湖。写入链路固定为 raw / manifest / canonical / quality / catalog / gold；resolver、实验和 Backtrader 不得导入 connector/runtime/storage，不得读取 `TUSHARE_TOKEN`。
3. `remediation_job_spec` 只是审计和人工执行建议，默认 `dry_run=true`，必须包含 dataset、source、exact interface、index code、date range、lake root、run id、resume policy、manifest / quality / catalog 目标路径和错误枚举。
4. 旧等权买入持有或同股票池代理如保留，只能命名为 `proxy_baseline`；不得填充 `hs300_index` benchmark 字段，不得声明为沪深 300 相对收益。

## 背景与事实基线

### 当前已存在能力

| 模块 | 当前状态 |
|---|---|
| `market_data/connectors/tushare.py` | 已存在，但目前只做 fail-fast，不真实调用 Tushare |
| `market_data/runtime.py` | 已有 retry / throttle / circuit breaker / resume / manifest 写入 |
| `market_data/storage.py` | 已有 raw JSONL、manifest、checksum、敏感参数脱敏 |
| `market_data/normalization.py` | 已能将 fake `prices` raw 标准化为 canonical parquet；当前只支持 `prices` |
| `market_data/validation.py` | 已能输出 quality CSV/Markdown，包含 `fetch_status`、`dataset_status`、coverage、thresholds、`denominator_mode` |
| `market_data/readers.py` | 已实现只读 canonical reader，不导入 connector/runtime/storage |
| `market_data/cli.py` | 当前仅支持 fake/offline 主路径；真实 source 即使传 `--enable-real-source` 仍被阻断 |

### 外部数据源假设

用户计划购买 Tushare 5000 积分档。基于本轮调研和用户决策，后续设计可以将 Tushare 视为优先真实源，但仍必须保留多源比对和本地质量门。

Tushare 5000 的工程含义：

1. 可作为稳定主数据源或校验源。
2. 支撑更高频次、更顺滑的 2015-2025 长区间回补。
3. 不替代本地 Parquet 数据湖。
4. 不替代 quality report、manifest、catalog、comparison report。

## 文档处理决策

| 受影响文档 | 处理方式 | 旧基线保留方式 | 修订记录位置 | 批准状态 |
|---|---|---|---|---|
| `process/USE-CASES.md` | 原文档更新 | 保留 v1.3 / UC-01..UC-06 已确认场景基线；按 CR-005 第三轮评审新增 UC-07，不删除旧场景 | `## 修订记录` v1.4 | updated-by-meta-pm-round3 |
| `process/REQUIREMENTS.md` | 原文档更新 | 保留 v1.3 / REQ-001..REQ-058 已确认需求基线；按 CR-005 第三轮评审新增 REQ-059..REQ-070，不重排旧编号 | `## 修订记录` v1.4 / `## 需求级变更记录` | updated-by-meta-pm-round3 |
| `process/HLD.md` | 原文档更新 | 保留 CR-004 fake/offline 默认与真实源默认关闭基线；追加 Tushare 5000 可控启用和第三轮两步补齐契约 | `## 0. 修订记录` / CR-005 §22 | pending-cp3-cp4-rerun |
| `process/ARCHITECTURE-DECISION.md` | 原文档更新 | 保留 ADR-009/012；修订 ADR-013/015/017，使 Tushare 数据层 backfill 与消费层 structured status 分离 | 修订记录 | pending-cp3-cp4-rerun |
| `process/STORY-BACKLOG.md` | 原文档更新 | 保留 STORY-014..018 状态；修订 CR-005 Story 组的 CLI/job 所有权与 dev_gate | 修订记录 | pending-cp4-rerun |
| `process/DEVELOPMENT-PLAN.yaml` | 原文档更新 | 保留 CR-004 批次 A-D；修订 CR-005 Wave / DAG、文件所有权和 required_contracts | 不适用 | pending-cp4-rerun |
| `process/stories/` | 新增后修订 | 不适用 | Story 卡片与 LLD frontmatter | pending-cp4-rerun |
| `market_data/**` | 后续修改 | 当前 fake/offline 与已验证 reader/quality 语义保留 | 代码与测试 | pending-CP5 |
| `engine/**` | 默认不变 | Data Loader 只读本地数据的边界保留；轻量回测主路径保留 | 如需桥接 Backtrader backend selector 必须另行 CP5 | protected |
| `experiments/**` | 默认后置 | 由 STORY-018 只读接入边界保护，不允许直接联网 | 如需真实基准接入必须走本地 `hs300_index` | protected |
| `pyproject.toml` / `uv.lock` | 后续可能更新 | 保留 uv 管理；新增 `tushare` 或 `backtrader` 依赖必须通过 uv，且不得改变默认离线测试 | 不适用 | pending-CP5 |

## 五维度影响分析

| 维度 | 评估问题 | 受影响对象 | 结论 | 处理动作 |
|---|---|---|---|---|
| 需求层 | 是否新增或重定义数据源能力 | Tushare connector、真实沪深 300、指数权重、PIT 可得性字段、复权价格 | true | 新增 Tushare 5000 可控真实源需求；明确 PIT as-of join 和 adjusted price 由数据层保证；不改变本地数据湖为事实源 |
| 场景层 | 是否改变测试和验收场景 | 2015-2025 回补、实验十/十二、牛熊慢牛震荡区间、Backtrader 对照回测、因子面板/score 输入 | true | 增加真实数据 dry-run、分批抓取、质量报告、多源比对、缺口回补、PIT 对齐、复权价格生成、Backtrader 本地输入适配和结果对照场景 |
| 计划层 | 是否改变 Story / Wave / 依赖 | CR-004 后续实现队列、STORY-004/018、CR005-S01/S02/S03/S04/S06、可选 Backtrader backend | true | 需要新 CR-005 Story 组；`market_data/cli.py` 或等价 backfill job 所有权前移到 CR005-S01，不晚于 CR005-S04；CR005-S04/S06 dev_gate 显式等待 hs300 backfill job、reader quality、BenchmarkResult schema 和 benchmark policy 冻结；不得直接跳进代码实现 |
| 安全层 | 是否引入凭据和联网风险 | `TUSHARE_TOKEN`、真实 API、raw 数据写入、Backtrader 可选依赖 | true | token 只读环境变量；默认测试不联网；真实抓取必须显式确认；Backtrader 不读取凭据、不联网 |
| 交付层 | 是否需要回归和文档更新 | README、USER-MANUAL、quality report、catalog、CLI、可选后端说明 | true | 验证通过后更新文档；禁止提交 token、真实私有数据、缓存；Backtrader 文档标注 optional |

## 回退决策

- 影响等级：high。
- 回退阶段：`solution-design`。
- 理由：本变更影响数据源真实启用、dataset schema、normalization、quality、catalog、CLI、依赖和实验真实基准路线，属于结构性数据层变更。
- 下一会话必须先由 `meta-po` 组织 `meta-se` / `meta-qa` 评审并更新 HLD/ADR/Story 计划，再进入 Story LLD 和 CP5。
- CP5 未通过前不得实现真实 Tushare adapter、不得增加真实抓取命令、不得写真实 `data/**` / `reports/**`。

## 推荐 Story 拆分

| Story | 目标 | 建议文件范围 | 说明 |
|---|---|---|---|
| CR005-S01 | Tushare 真实 connector 与显式写湖 job 可控启用 | `market_data/connectors/tushare.py`、`market_data/config.py`、`market_data/source_registry.py`、`market_data/runtime.py`、`market_data/storage.py`、`market_data/cli.py` 或等价 job、`pyproject.toml`、`uv.lock`、测试 | 实现真实 adapter、token env、allowlist、接口级限速、分页、错误映射、`hs300_index` backfill job spec 和 dry-run 默认；默认关闭 |
| CR005-S02 | Tushare 多 dataset schema、PIT 字段与复权 normalization | `market_data/contracts.py`、`market_data/normalization.py`、测试 | 支持 `prices`、`hs300_index`、`index_weights`、`trade_calendar`；非行情数据定义 `available_date` / `effective_date` / `available_at`；行情层保存 `adj_factor` 与 adjusted price；字段映射必须 exact |
| CR005-S03 | 多 dataset quality / catalog / readers / PIT as-of gate | `market_data/validation.py`、`market_data/catalog.py`、`market_data/readers.py`、测试 | 新增 dataset 的 coverage、schema 校验、quality CSV、catalog、只读 reader；reader 输出消费方可用前必须通过 PIT as-of join、复权口径一致和 quality gate |
| CR005-S04 | 真实沪深 300 基准本地接入 | `market_data/benchmarks.py`、`experiments/run_experiment_10.py`、`experiments/run_experiment_12.py`、专用测试 | 只读本地 `hs300_index`，返回 `BenchmarkResult` typed schema；缺失时 unavailable / required_missing，并携带只读 next_action / remediation_job_spec；不静默代理、不自动补数 |
| CR005-S05 | 多源 comparison 与回补作业文档 | `market_data/comparison.py`、README、docs/USER-MANUAL.md、测试 | Tushare vs AkShare/TickFlow/gold 差异报告；真实源启用和显式 backfill runbook；不拥有 backfill job 主入口 |
| CR005-S06 | Backtrader 可选回测后端接入 | `engine/backtest.py` 或后端 selector、`engine/backtrader_adapter.py`、`market_data/readers.py`、`pyproject.toml`、`uv.lock`、测试、README、docs/USER-MANUAL.md | 可选依赖；只消费本地 canonical/gold 派生的干净 factor panel / score / OHLCV feed；只负责调仓、成交、成本、仓位、净值和风险分析；不生成 PIT、不计算复权因子、不替代轻量回测主路径；不直接联网；不读取 Tushare token；默认 pytest 不依赖 Backtrader |

## 建议 dataset

| Dataset | Tushare 接口候选 | 用途 | 优先级 |
|---|---|---|---|
| `hs300_index` | `index_daily(ts_code='399300.SZ')` | 替换代理基准 | P0 |
| `prices` | `daily` 或 `pro_bar` + `adj_factor` | 股票回测价格、adjusted price、收益/技术指标/forward return 统一输入 | P0 |
| `trade_calendar` | `trade_cal` | 开市日、coverage 分母、回测日历 | P0 |
| `index_weights` | `index_weight(index_code='399300.SZ')` | 沪深 300 成分和权重 | P0/P1 |
| `adj_factor` 或复权价格 | `adj_factor` / `pro_bar` | 复权一致性；与 `prices` 共同生成 `adjusted_open/high/low/close` 或等价统一复权价格 | P0/P1 |
| `stock_basic` | `stock_basic` | 上市/退市、证券状态、股票池过滤 | P1 |
| `stk_limit` / 停复牌 | `stk_limit` / 停复牌相关接口 | 涨跌停与不可交易约束 | P2 |

## 设计约束

1. Tushare adapter 默认关闭；导入模块不得联网。
2. 真实调用必须同时满足：
   - `enabled=true`
   - source/interface exact allowlist 命中
   - `TUSHARE_TOKEN` 环境变量存在
   - 用户显式执行真实抓取命令
3. 不得把 token 写入 manifest、quality、catalog、日志、错误消息或测试 fixture。
4. 真实抓取前必须支持 `plan` / dry-run，输出批次数、预计接口、日期范围、目标 dataset。
5. 默认 pytest 不需要 token、不联网。
6. Data Loader、实验十、实验十二不得直接调用 Tushare；只能读取本地 canonical/gold + quality CSV。
7. raw 到 dataset 只允许显式 `target_dataset` 或 exact interface 映射。
8. 质量报告 CSV 仍为机器事实源，Markdown human-only。
9. `fetch_status` 与 `dataset_status` 必须分离；远端失败但本地 parquet 合规时不得一律 fail。
10. 真实抓取不得写入仓库内不可审计的大文件；如写真实数据，需明确 lake root、`.gitignore` 和人工确认。
11. Backtrader 仅作为 optional backend：未安装时轻量回测主路径必须照常运行，错误必须结构化为 `backend_unavailable` 或等价状态。
12. Backtrader adapter 的数据输入必须来自本地 canonical/gold 和 quality gate；不得在 adapter 内导入 `market_data.connectors`、读取 `TUSHARE_TOKEN` 或触发网络。
13. PIT 对齐必须在 Pandas 数据层完成：非行情数据按 `available_date` / `effective_date` / `available_at` 做 as-of join，任何回测日不得读取未来才可得字段。
14. 复权价格必须在行情层完成：保存 `adj_factor` 与统一 `adjustment_policy` 下的 adjusted price；价格收益、技术指标、forward return 不得混用未复权价或不同复权策略。
15. Backtrader 的输入只能是数据层已清洗的 factor panel、score 或 OHLCV feed；Backtrader 不承担 PIT 生成、复权因子计算、Tushare 读取、联网补数或 quality gate 判定职责。
16. 缺失 `hs300_index` 时，消费层只返回 typed status 和人工可执行的 `remediation_job_spec`，不得自动执行数据层 job。
17. `hs300_index` backfill job 默认 dry-run，只有用户显式执行并满足 enabled、allowlist、token env、lake root 前置条件时才允许联网和写湖。
18. `hs300_index` quality gate 必须以交易日历 open dates 为 coverage 分母，记录缺失交易日、gap reason、重复 key、source lineage、raw checksum 或等价 lineage、quality thresholds 和 available/unavailable 映射。

## 验收口径

| 编号 | 验收项 | 通过标准 |
|---|---|---|
| CR005-AC-001 | Tushare adapter 默认安全 | 无 token、未启用、未 allowlist 时 fail fast；import 不联网 |
| CR005-AC-002 | Tushare 真实启用显式 | 只有显式配置和显式命令才会调用真实 API |
| CR005-AC-003 | 沪深 300 指数日线 | `hs300_index` canonical/gold 可覆盖请求区间；`index_code+trade_date` 唯一；缺口进入 quality CSV/catalog，并映射到 `available` / `unavailable` / `required_missing` |
| CR005-AC-004 | 指数权重 | `index_weights` 可记录 `index_code`、`con_code`、`trade_date`、`weight` 或等价字段 |
| CR005-AC-005 | 交易日历 | `trade_calendar` 支撑 open trade dates 分母 |
| CR005-AC-006 | 股票价格 | `prices` 复权口径明确，不混用 |
| CR005-AC-007 | 质量报告 | 每个 dataset 输出 CSV canonical，含 coverage、thresholds、denominator、fetch/dataset 双状态、source/interface/run lineage、raw checksum 或等价 lineage；`hs300_index` 额外记录 missing trade dates、gap reason、duplicate key count |
| CR005-AC-008 | 本地事实源 | Data Loader / 实验只读本地数据，不直接联网 |
| CR005-AC-009 | 多源对比 | 至少支持 Tushare 与一个本地 reference/AkShare fixture 的差异报告 |
| CR005-AC-010 | 默认测试离线 | `uv run --python 3.11 pytest -q` 不需要 token、不联网 |
| CR005-AC-011 | Backtrader 可选后端安全 | 未安装 Backtrader 时默认轻量回测和测试通过；启用 Backtrader 时只读本地 canonical/gold，不联网、不读取 `TUSHARE_TOKEN`；输出与轻量回测对照报告 |
| CR005-AC-012 | PIT 数据层对齐 | 非行情 dataset 必含可审计的 `available_date` / `effective_date` / `available_at` 或等价字段；as-of join 后任一回测日使用的数据满足 `available_at <= decision_time` |
| CR005-AC-013 | 统一复权价格 | `prices` 或关联行情层保存 `adj_factor` 与 adjusted price；价格收益、技术指标和 forward return 使用同一 `adjustment_policy` 的复权价格 |
| CR005-AC-014 | Backtrader 职责边界 | Backtrader adapter 只消费数据层生成的干净 factor panel / score / OHLCV feed；PIT 生成、复权因子计算、Tushare 读取、联网和 quality gate 绕过次数均为 0 |
| CR005-AC-015 | 两步补齐契约 | 缺 `hs300_index` 时消费层只返回 typed status + `next_action` / `remediation_job_spec`，自动联网、自动 backfill、自动写湖次数均为 0 |
| CR005-AC-016 | 显式 hs300 backfill job | 数据层 job spec 至少包含 dataset、source、exact interface、index code、start/end、lake root、run id、resume policy、dry-run 默认、manifest/quality/catalog 路径和错误枚举；dry-run 网络调用次数为 0 |
| CR005-AC-017 | BenchmarkResult typed schema | resolver 输出字段至少覆盖 status、dataset、source、index_code、interface、date range、coverage、quality_status、missing_reason、required、remediation_job_spec、catalog_entry、run/lineage |
| CR005-AC-018 | `hs300_index` 数据准确性 | `hs300_index` available 路径必须输出 `benchmark_kind`、`index_code`、source interface、交易日历分母、coverage 起止、covered/missing trade dates、gap reason、quality threshold、`quality_status` 与 `benchmark_status` 映射；口径或质量未满足时不得声明 available |
| CR005-AC-019 | benchmark 可用性与补齐建议 | 本地 `hs300_index` 缺失、覆盖不足或 quality fail 时，消费层返回 structured `unavailable` / `required_missing`，并包含 `next_action` 与 `remediation_job_spec`；该 spec 指向显式 `market_data` Tushare 写湖 / backfill 作业，消费层网络调用次数为 0 |

## 正式需求映射（CR-005 第三轮）

| CR005-AC | 映射需求 | 映射场景 | 说明 |
|---|---|---|---|
| CR005-AC-001 | REQ-059, REQ-069 | UC-07 | Tushare adapter 默认安全、import 不联网、无 token / 未启用 / 未 allowlist 时 fail fast |
| CR005-AC-002 | REQ-059, REQ-060 | UC-07 | Tushare 真实启用必须来自显式配置和显式数据准备命令 |
| CR005-AC-003 | REQ-060, REQ-061, REQ-062, REQ-063, REQ-065 | UC-07 | `hs300_index` canonical/gold、typed missing status、口径/质量/缺口解释和不得静默代理 |
| CR005-AC-004 | REQ-066, REQ-067 | UC-06, UC-07 | `index_weights` schema、PIT 可用性字段和 quality/catalog |
| CR005-AC-005 | REQ-063, REQ-066, REQ-067 | UC-07 | `trade_calendar` open trade dates 分母与 benchmark coverage denominator |
| CR005-AC-006 | REQ-037, REQ-066 | UC-01, UC-06 | `prices` 复权口径与 adjusted price 一致性 |
| CR005-AC-007 | REQ-060, REQ-063, REQ-067 | UC-01, UC-07 | quality CSV、coverage、thresholds、denominator、fetch/dataset 双状态和复现字段 |
| CR005-AC-008 | REQ-064, REQ-065 | UC-07 | Data Loader / 实验只读本地数据，不直接联网，不以 proxy 填充 `hs300_index` |
| CR005-AC-009 | REQ-068 | UC-07 | Tushare 与 reference / AkShare fixture 差异报告 |
| CR005-AC-010 | REQ-059, REQ-064, REQ-069 | UC-07 | 默认测试离线、无 token、不联网 |
| CR005-AC-011 | REQ-064, REQ-070 | UC-07 | Backtrader optional backend 安全与未安装降级 |
| CR005-AC-012 | REQ-038, REQ-066 | UC-06, UC-07 | PIT 数据层对齐和 `available_at <= decision_time` |
| CR005-AC-013 | REQ-037, REQ-066 | UC-01, UC-06 | 统一复权价格、`adj_factor` 和 `adjustment_policy` |
| CR005-AC-014 | REQ-064, REQ-070 | UC-07 | Backtrader 职责边界：只消费干净 feed，不生成 PIT/复权、不联网、不绕过 quality gate |
| CR005-AC-015 | REQ-060, REQ-062, REQ-064 | UC-07 | 两步补齐契约：消费层只返回 typed status + next action，数据层显式执行补齐 |
| CR005-AC-016 | REQ-060, REQ-062 | UC-07 | 显式 `hs300_index` backfill job spec、dry-run、manifest/quality/catalog 路径和错误枚举 |
| CR005-AC-017 | REQ-062, REQ-063 | UC-07 | BenchmarkResult typed schema、coverage、quality、lineage 和 remediation 字段 |
| CR005-AC-018 | REQ-061, REQ-063, REQ-067 | UC-07 | 新增数据准确性 AC，冻结 benchmark 口径、coverage、quality 和 gap explanation |
| CR005-AC-019 | REQ-060, REQ-062, REQ-064 | UC-07 | 新增可用性 AC，保证缺失时有 structured next action 与补齐作业规格 |

## 非目标

1. 不在本 CR 中提交 Tushare token。
2. 不把 Tushare API 直接接入 `engine/data_loader.py`。
3. 不把实验十/十二改成运行时联网。
4. 不立刻引入 PostgreSQL / MySQL / ClickHouse 服务。
5. 不删除 CR-004 fake/offline 测试路径。
6. 不伪造真实沪深 300 数据；缺失时必须结构化 unavailable。
7. 不把 Backtrader 升级为默认主回测框架。
8. 不通过 Backtrader 适配层绕过现有 quality gate、复权口径、T+1 成交口径或离线边界。
9. 不在 Backtrader adapter 中实现 PIT as-of join、复权因子计算、Tushare 数据读取或联网补数。

## 当前状态与下一步

- 当前状态：CR-005 已进入 `ready-for-close`，但尚未最终关闭。关闭前仍需完成 20:01 后 README / USER-MANUAL 文档同步和最终静态复核，并由用户明确决定是否关闭。
- Story 执行：CR-005 已完成 CP3/CP4 人工确认与 CR005-S01 至 CR005-S06 的 CP5/CP6/CP7 Story 执行闭环；六个 Story 均已 verified。Backtrader 已作为同一变更内的可选后端落地，dependency group 固定为 `backtrader`，版本固定为 `backtrader==1.9.78.123`。
- 真实数据链路：截至 `2026-05-18T20:01:26+08:00`，CR-005 小窗口真实 Tushare 链路已 PASS。正式 dependency group `tushare==1.4.29` 已落地；正式入口为 `uv run --env-file .env --group tushare --python 3.11 ...`；`hs300_index` 的 `normalize` / `validate` / `read` CLI 已支持；未显式传 `--lake-root` 时优先使用 `.env` 中的 `MARKET_DATA_LAKE_ROOT`；复验后 `data/market_data` 未重新生成。
- 已完成：meta-po 完成 CR 归属判断和五维度影响分析更新；meta-se 完成 HLD/ADR/Story Plan/Development Plan 与 CR005-S01..S06 Story 卡片修订；meta-dev/meta-qa 已完成 S01..S06 的 LLD、实现与验证。两步补齐契约、`BenchmarkResult` typed schema、`hs300_index` backfill job spec、accuracy/quality AC、dev_gate、文件所有权、Backtrader optional backend、正式 Tushare 依赖入口和 CLI `hs300_index` 运维入口均已通过验证。
- 当前门控：Story 执行门控已通过；真实数据启用仍必须遵守显式 Tushare fetch/backfill、外置 lake root、no-network/no-token 默认边界，不得静默联网补数或把真实 lake 数据归档到 GitHub。更大窗口、2015-2025 长区间或全量回补必须用户另行显式授权。
- 尚未完成：README.md 与 docs/USER-MANUAL.md 仍需吸收 20:01 后真实数据验证和 CLI REQUIRED 关闭事实；完成后需由 meta-qa 做最终静态复核，确认 README/USER-MANUAL/CR/STATE 一致、无 token/NAS 凭据泄露、无自动授权全量回补。
- 下一步建议：主线程真实调度 `process/handoffs/META-DOC-CR005-POST-REAL-DATA-DOC-SYNC-2026-05-18.md`，随后调度 `process/handoffs/META-QA-CR005-FINAL-STATIC-RECHECK-2026-05-18.md`。两者 PASS 后，由用户决定是否最终关闭 CR-005；meta-po 不擅自关闭。
