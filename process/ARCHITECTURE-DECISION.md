---
complexity: "standard"
confirmed: true
confirmed_by: "user"
confirmed_at: "2026-05-14"
source_hld: "process/HLD.md"
source_hld_version: "2.4"
story_plan_status: "confirmed-with-cr014"
created_at: "2026-05-14"
created_by: "meta-se"
active_change: "CR-014"
secondary_change: "CR-010"
cr004_revision_status: "draft-pending-cp3-cp4"
cr004_confirmed: false
cr005_revision_status: "draft-pending-cp3-cp4-rerun"
cr005_confirmed: false
cr006_revision_status: "draft-pending-cp3-cp4"
cr006_confirmed: false
cr007_revision_status: "draft-pending-cp3-cp4"
cr007_confirmed: false
cr008_revision_status: "draft-pending-cp3-cp4"
cr008_confirmed: false
cr010_revision_status: "confirmed"
cr010_confirmed: true
cr010_confirmed_by: "user"
cr010_confirmed_at: "2026-05-22T15:09:54+08:00"
cr011_revision_status: "confirmed-pending-lld-cp5"
cr011_confirmed: true
cr011_confirmed_by: "user"
cr011_confirmed_at: "2026-05-24T08:25:22+08:00"
cr011_adr_range: "ADR-036..043"
cr013_revision_status: "draft-pending-cp3-cp4"
cr013_adr_range: "ADR-044..047"
cr014_revision_status: "confirmed"
cr014_adr_range: "ADR-048..052"
cr014_confirmed: true
cr014_confirmed_by: "user"
cr014_confirmed_at: "2026-05-26T23:58:12+08:00"
cr014_manual_checkpoint: "checkpoints/CP3-CR014-A-SHARE-SINCE-INCEPTION-DATA-LAKE-HLD-REVIEW-R2.md"
---

# 架构决策记录

> 本文件在 `story-planning` 阶段把已确认 HLD §15 的 ADR 候选收敛为正式规划决策。Story 计划已由用户确认通过，`confirmed=true`。后续可进入 Story LLD 起草，但未经单个 Story LLD 人工确认，不得进入实现。

## 修订记录

| 版本 | 日期 | 修订人 | 变更要点 |
|---|---|---|---|
| 0.1 | 2026-05-14 | meta-se | 基于已确认 HLD §15 收敛 ADR-001 至 ADR-007，并回写 Story/Wave 约束 |
| 0.2 | 2026-05-14 | meta-po | 记录 Story Plan 人工确认通过，作为 story-execution 阶段 LLD 起草输入 |
| 0.3 | 2026-05-17 | meta-se | 按 CR-004 增量新增 ADR-008 至 ADR-012，覆盖 `market_data/` 独立可迁移包、回测/实验主路径只读、真实联网 adapter 默认关闭、数据湖 canonical schema/manifest 契约和多源校验策略；本增量待 CP3/CP4 人工确认 |
| 0.4 | 2026-05-17 | meta-se | 按 CR-005 增量新增 ADR-013 至 ADR-016，覆盖 Tushare 只写本地数据湖、多 dataset schema/quality/readers、本地沪深 300 benchmark 和 Backtrader optional backend 后置接入；本增量待 CP3/CP4 人工确认 |
| 0.5 | 2026-05-17 | meta-se | 按 CR-005 追加修改点新增 ADR-017，并修订 ADR-014/016：PIT as-of join 与复权价格生成由 Pandas 数据层完成，Backtrader 只消费干净 factor panel / score / OHLCV feed |
| 0.6 | 2026-05-17 | meta-se | 按 CR-005 第三轮评审修订 ADR-013/015/017：冻结消费层 typed unavailable 与数据层显式 backfill job 的两步契约，补齐 `BenchmarkResult` schema、`hs300_index` job spec、quality/accuracy gate 和 CP3/CP4 重跑输入 |
| 0.7 | 2026-05-18 | meta-se | 按 CR-006 新增 ADR-018：冻结 structured `MARKET_DATA_LAKE_ROOT` 与 legacy flat `LOCAL_BACKTEST_DATA_DIR` 分离，路径优先级为显式参数/CLI > env/.env > config > fallback `data/`，并明确不自动迁移/复制/删除真实数据 |
| 0.8 | 2026-05-18 | meta-se | 按 CR-006 CP3 前修改意见重写 ADR-018：Tushare structured lake 成为新链路事实源；raw/manifest 仅用于采集审计、复现和质量追溯；轻量 engine 消费 canonical/gold 或外置派生 `legacy_flat`；Backtrader 消费 clean feed；旧 `data/` reference-only |
| 0.9 | 2026-05-20 | meta-se | 按 CR-007 新增 ADR-019 至 ADR-022：长周期 backfill 分批/resume/coverage gate、真实沪深300 benchmark policy、dataset readiness 与 PIT 边界、旧质量报告 legacy policy |
| 1.0 | 2026-05-20 | Codex | 按用户确认新增 ADR-023：当前骨架继续作为回测平台主干，Backtrader/VectorBT 作为可选后端或加速器，Qlib/LEAN 仅在目标变化时单独评估；同步落盘 `docs/ROADMAP.md` |
| 1.1 | 2026-05-21 | meta-se | 按 CR-008 新增 ADR-024 至 ADR-029：`research_input_v1` 唯一研究入口、proxy/real benchmark 字段隔离、research dataset builder 只读边界、PIT/fixed universe 声明、quality/adjustment/label window gate、因子辅助数据缺失降级语义 |
| 1.2 | 2026-05-22 | meta-se | 按 CR-010 新增 ADR-030 至 ADR-035：生产级数据湖独立 companion HLD、consumer 只读边界、日频价格可用时点、W3 fail-fast、catalog publish gate、真实回补分阶段授权与可恢复执行 |
| 1.3 | 2026-05-23 | meta-se | 按 CR-011 新增 ADR-036 至 ADR-043：benchmark policy consumption、PIT universe、tradability gates、execution price/VWAP degradation、adjustment audit、industry/market cap/style exposure、liquidity/capacity/cost sensitivity、factor panel audit/robust validation；本增量待 CP3/CP4 确认 |
| 1.4 | 2026-05-25 | meta-se | 按 CR-013 新增 ADR-044 至 ADR-047：full-history 不可外推、真实 VWAP / execution blocked、unsupported register 正式声明边界、证据保留与权限边界；本增量待 CP3/CP4 确认 |
| 1.5 | 2026-05-26 | meta-se | 按 CR-014 新增 ADR-048 至 ADR-051：Parquet lake + catalog/manifest 继续作为 source of truth、DuckDB 只读候选而非事实源、全 A since-inception 分区 / current pointer / lifecycle 决策、真实执行授权和 claim boundary 决策；本增量待 CP3 确认 |
| 1.6 | 2026-05-26 | meta-se | 按 CR-014 CP3 R2 修改意见新增 ADR-052：明确 DuckDB read-only 不等于没有写入；真实写入由 lake production pipeline 单写者负责，DuckDB 只读消费 published current truth 或受控 candidate audit evidence |

## Agent/Skill 组合方案

| 阶段 | Agent / Skill | 使用目的 | 输出 / 回写 |
|---|---|---|---|
| story-planning | `phase-designer` | 将 HLD §16 的 M0-M4 转为 5 个串行 Wave | `process/DEVELOPMENT-PLAN.yaml` 的 `waves` |
| story-planning | `dependency-mapper` | 建立 Story 级依赖 DAG，确保数据准备先于回测、回测先于扫描 | `depends_on`、依赖说明和输出文件边界 |
| story-planning | `wave-planner` | 判定 Wave 内是否可并行，避免同一输出文件冲突 | Wave `parallel` 与 Story 输出文件分配 |
| story-planning | `story-manager` | 生成 draft Story 卡片，保留 LLD 审核门控 | `process/stories/STORY-*.md` |
| story-planning | `dag-validator` | 对 `DEVELOPMENT-PLAN.yaml` 进行无环、无无效引用的规划级校验 | 本文件和 Backlog 的依赖校验结论 |

## 平台适配差异

| 适配面 | 决策 | Story 回写 |
|---|---|---|
| 目标平台 | 本地 Python 研究工具，运行时遵循仓库 uv 规则 | STORY-001 至 STORY-013 的 `dev_context.platform_target` |
| Python 依赖 | 后续实现必须以 `pyproject.toml` 为依赖声明源，以 `uv.lock` 为锁定结果 | STORY-001 |
| 联网边界 | 仅数据准备入口允许联网；回测、扫描、候选和差异分析主路径必须离线 | STORY-002、STORY-004、STORY-007、STORY-008 |
| 平台安装 | 本轮不生成安装规范或安装脚本；交接文件禁止写入 `delivery/**` | 全部 Story 均不得要求安装脚本作为输出 |
| 聚宽集成 | 第一版只输出人工回填候选，不自动调用、提交或轮询聚宽 | STORY-008 |
| CR-004 `market_data/` | 新增仓库内独立包，保持未来可迁移；首轮不发布安装包 | STORY-014 至 STORY-018 |
| CR-004 真实数据源 | TickFlow / AkShare / Tushare 真实 adapter 默认关闭，fake/offline 是默认测试路径 | STORY-015、STORY-017 |
| CR-004 实验接入 | 实验十 / 十二只读 canonical 或 gold parquet，不直接联网 | STORY-018 |
| CR-005 Tushare 真实源 | Tushare 从 fail-fast 边界升级为显式启用的真实写湖 source；只允许由用户显式执行的数据层 job 写 raw/manifest/canonical/quality/catalog/gold；消费层只返回 typed unavailable / remediation spec，不自动补数；非行情 PIT 与行情复权均在 Pandas 数据层收敛 | CR005-S01 至 CR005-S04 |
| CR-005 Backtrader 后端 | Backtrader 是 optional backend；只消费本地 canonical/gold + quality gate 派生的干净 factor panel / score / OHLCV feed，不读取 `TUSHARE_TOKEN`、不导入 `market_data.connectors` | CR005-S06 |
| CR-006 Tushare-first 数据方案 | Tushare structured lake 是新数据事实源；raw/manifest 仅用于采集审计、复现和质量追溯；轻量 engine 消费 canonical/gold 或派生 external `legacy_flat`；Backtrader 消费 clean feed；旧 `data/` reference-only | CR006-S01 至 CR006-S04 |
| CR-007 Canonical 数据覆盖与真实 benchmark | 长周期 backfill、同区间 `hs300_index` + `trade_calendar`、dataset readiness、实验十三真实 benchmark 和 legacy quality report 均延续 Tushare-first structured lake；不授权真实抓取或旧数据操作 | CR007-S01 至 CR007-S05 |
| CR-008 研究级数据层硬化 | `research_input_v1` 和 `research_dataset_builder` 作为研究消费入口；proxy/real benchmark 字段隔离；quality、复权、label window、PIT/fixed universe 和因子辅助数据缺失均必须结构化披露或阻断 | CR008-S01 至 CR008-S06 |
| CR-010 数据湖生产化 | 生产级数据湖设计拆入 `process/HLD-DATA-LAKE.md`；consumer 只读 published catalog/canonical/gold；真实回补需显式授权；W3 未确认 source/interface 前 fail-fast | CR010-S01 至 CR010-S12 |
| CR-011 因子研究数据补齐 | 旧实验 17-21 保留为 fixed/proxy/close baseline；新版研究只读 published catalog/readers，按 benchmark/PIT/tradability/execution/adjustment/exposure/capacity/factor audit gate 生成 allowed/blocked claims | CR011-S01 至 CR011-S08 |
| CR-013 unsupported data 与 claim boundary | CR-012 limited-window pass 只作为窗口级结论；2020-2024 full-history、真实 VWAP / 分钟执行价和 unsupported register 均进入 blocked / excluded 声明边界；本轮只读证据，不授权真实补数 | CR013-S01 至 CR013-S04 |
| CR-014 全 A since-inception 生产数据湖 | `process/HLD-DATA-LAKE.md` §17 拥有全 A current truth、生命周期、P0 分层、catalog current pointer、增量刷新 / replay 和 DuckDB 只读候选；主 HLD §30 只同步研究消费合同和声明边界 | CP3 通过后再拆解，不在本轮生成 Story |

## ADR-001：数据准备与回测主路径物理隔离

**状态**：Accepted for draft story plan

**决策**：创建独立数据准备/更新入口，该入口可以调用 AKShare 等远程数据源；回测、参数扫描、候选筛选和本地差异分析入口只读取本地 parquet、manifest 和质量报告，不得隐式触发联网补数。

**理由**：满足 REQ-016、REQ-034、REQ-047 至 REQ-057，并保持 HLD §3、§4、§8、§12 的离线主路径。

**约束**：

- 数据准备写入 `data/raw/**`、`data/*.parquet`、`data/manifests/data_prep_manifest.jsonl` 和 `reports/data_quality_report.*`。
- 回测主路径只能读取上述本地产物，发现缺口时返回明确错误或 warn/fail 质量状态，不调用数据准备。
- Story 输出边界必须避免数据准备模块与回测模块互相写同一实现文件。

**回写 Story / Wave**：STORY-002、STORY-003 位于 M0；STORY-004、STORY-007、STORY-008 显式继承离线只读约束。

## ADR-002：第一版采用项目内轻量日频回测层

**状态**：Accepted for draft story plan

**决策**：第一版不引入 RQAlpha、Backtrader、vectorbt、bt 等大型框架作为主回测框架，创建项目内轻量日频回测层。

**理由**：满足 REQ-013、REQ-036，降低学习型项目复杂度，并保留可调试性。

**约束**：

- 后续实现应按数据加载、信号、组合、指标、扫描和报告分层。
- 策略核心保持纯函数，不读写文件、不依赖回测全局状态。
- 若后续引入大型框架，必须另起 ADR 或 CR，不在本轮 Story 计划内实现。

**回写 Story / Wave**：STORY-001 固化目录与依赖基线；STORY-004 至 STORY-008 实现轻量分层主路径；STORY-013 仅扩展策略纯函数接口。

## ADR-003：默认复权口径为 `qfq`

**状态**：Accepted for draft story plan

**决策**：默认复权口径为前复权 `qfq`。同一次回测、扫描、候选筛选和聚宽对照不得混用复权口径，报告必须记录实际 `adjustment_policy`。

**理由**：落实 Q-004、REQ-037 和 HLD §7、§9。

**约束**：

- `data/prices.parquet` 可用行级 `adjustment_policy` 或 manifest 数据集 metadata 表达口径。
- 同一运行检测到混用复权口径时必须拒绝运行。
- CSV 报告必须输出 `adjustment_policy`。

**回写 Story / Wave**：STORY-003 负责标准化与 metadata；STORY-004 负责加载校验；STORY-006、STORY-007、STORY-008 负责报告字段继承。

## ADR-004：T 日收盘信号，T+1 收盘成交

**状态**：Accepted for draft story plan

**决策**：T 日收盘后生成信号，成交只能发生在 T+1 或之后；第一版默认使用 T+1 收盘价成交，成本在 T+1 调仓后从净值中扣除，新持仓从 T+1 收盘后承担后续收益。

**理由**：落实 Q-005、REQ-005 和 HLD §9。

**约束**：

- 信号层只使用 `available_at <= decision_time` 的价格。
- 组合层记录成交日、成本扣除、未成交原因和现金留存。
- 缺失成交价不得前填、后填、0 填充或使用替代收益。

**回写 Story / Wave**：STORY-005 实现信号与组合口径；STORY-006 输出指标和报告 metadata；STORY-010、STORY-011 在增强阶段扩展不可交易约束。

## ADR-005：JSONL manifest 作为 checkpoint 事实源

**状态**：Accepted for draft story plan

**决策**：`data/manifests/data_prep_manifest.jsonl` 是断点续传和批次审计的事实源，包含 `schema_version`、`run_id`、`batch_id`、请求、重试、raw 路径、标准化输出路径、覆盖范围和状态。

**理由**：落实 Q-014、Q-017、REQ-055 和 HLD §8。

**约束**：

- 批次状态枚举为 `pending`、`running`、`success`、`partial_success`、`failed`、`skipped`。
- 重试事件必须记录等待秒数、错误类型和错误信息。
- 质量报告通过 `manifest_run_id` 关联。

**回写 Story / Wave**：STORY-002 实现节流/重试/manifest；STORY-003 消费 manifest 生成质量报告；STORY-009 至 STORY-012 增强时必须同步扩展 manifest。

## ADR-006：质量阈值与运行降级

**状态**：Accepted for draft story plan

**决策**：质量状态采用 `pass`、`warn`、`fail`。`warn` 允许回测继续但必须披露；`fail` 阻塞请求区间回测或扫描。

**理由**：落实 Q-018、REQ-056、REQ-057 和 HLD §8、§12、§13。

**约束**：

- schema 缺失、覆盖缺口、未解决重复键、异常价格或请求区间缺失率 > 5% 为 `fail`。
- 0 < 缺失率 <= 5% 为 `warn`。
- 无质量报告时主路径失败，除非后续 LLD 明确提供探索模式且不作为验收路径。

**回写 Story / Wave**：STORY-003 输出质量报告；STORY-004、STORY-007、STORY-008 按 `pass/warn/fail` 处理启动与报告披露。

## ADR-007：第一版真实性限制以 metadata 和增强路线处理

**状态**：Accepted for draft story plan

**决策**：第一版不精确建模完整停牌、涨跌停、新股、退市、ST、财报披露日和历史成分变化；这些限制必须进入单次回测、扫描和候选报告 metadata，并作为 M3 增强 Story 处理。

**理由**：落实 REQ-015、REQ-041 至 REQ-046 和 HLD §1、§10、§17。

**约束**：

- 第一版报告不得把固定当前沪深 300 描述为 PIT universe。
- 单次、扫描、候选三类报告必须使用一致限制项字段。
- M3 增强必须同步 raw、manifest、质量报告和离线读取契约。

**回写 Story / Wave**：STORY-006、STORY-007、STORY-008 负责第一版披露；STORY-009 至 STORY-012 负责真实性增强。

## ADR-008：`market_data/` 作为独立可迁移市场数据包

**状态**：Draft for CR-004 CP3/CP4 review

**决策**：新增仓库根 `market_data/` 包，内部包含 connector/runtime/storage/normalization/validation/readers/cli 等职责。`market_data/` 不反向依赖 `engine/`、`experiments/`、`reports/`，与既有回测层通过 canonical parquet、quality、catalog 和 reader 契约衔接。

**理由**：CR-004 要求市场数据组件后续可迁移到其他项目；直接扩展 `engine/` 会把数据工程能力绑定到当前回测实现，增加迁移成本和回归风险。

**约束**：

- `market_data/` 可以复用 pandas/pyarrow/YAML 等通用依赖，但不得 import `engine.*`。
- 既有 `engine/` 行为在首轮不被删除或重写；迁移通过后续接入 Story 逐步发生。
- 首轮不生成安装脚本、不写入 `delivery/**`、不发布跨仓库包。

**回写 Story / Wave**：STORY-014 建立包骨架与契约；STORY-018 作为后续只读接入。

## ADR-009：回测与实验主路径只读 `market_data` 数据湖

**状态**：Draft for CR-004 CP3/CP4 review

**决策**：回测、参数扫描、Notebook、实验十和实验十二只能通过 reader 读取 canonical/gold parquet、quality 和 catalog，不得在主路径调用 connector/runtime，也不得因缺口自动联网补数。

**理由**：延续 ADR-001 的物理隔离原则，防止 CR-004 引入真实数据源后污染离线回测和实验复现性。

**约束**：

- `market_data.readers` 不导入 `market_data.connectors`，不写 raw/manifest/canonical。
- 实验十 / 十二接入时保留旧 `--data-dir` 或等价兼容路径；新增 reader 路径必须是显式参数或显式配置。
- 真实沪深 300 基准先作为只读 gold/canonical 数据集，不在实验入口下载。

**回写 Story / Wave**：STORY-016 提供 reader；STORY-018 接入实验十/十二和基准只读路径。

## ADR-010：真实联网 adapter 默认关闭，fake/offline 为默认测试路径

**状态**：Draft for CR-004 CP3/CP4 review

**决策**：fake connector 是默认启用源；TickFlow、AkShare、Tushare adapter 只实现协议边界、配置校验、错误映射和 fail-fast 行为。真实联网必须同时满足 `enabled=true`、source/interface allowlist、凭据引用存在且由用户显式执行。

**理由**：CR-004 引入多真实数据源，安全风险和稳定性风险高。默认关闭可以保证 CI、pytest、CLI smoke 和实验路径不依赖网络或凭据。

**约束**：

- 不提交 token、API key、cookie、session 或真实私有行情。
- 缺少凭据、接口未允许、source/interface 未解析均返回非重试结构化错误。
- 默认测试不得真实导入或调用 TickFlow/Tushare；AkShare 真实调用也只允许在显式真实 adapter 命令中发生。

**回写 Story / Wave**：STORY-015 负责 connector/runtime 边界；STORY-017 通过 CLI smoke 和多源 fake/reference 证明默认 offline。

## ADR-011：Parquet 数据湖 canonical schema 与 manifest 契约

**状态**：Draft for CR-004 CP3/CP4 review

**决策**：`market_data` 数据湖采用 raw / manifest / canonical / quality 必做分层，gold / catalog 预留最小结构。manifest 是批次和派生链路事实源；canonical parquet 是下游唯一标准读取面。

**理由**：该契约把真实源差异收敛到 canonical 层，支持从 raw 重建、质量审计、多源比对和后续实验只读接入。

**约束**：

- manifest 至少包含 `schema_version`、`run_id`、`batch_id`、`source`、`interface`、`params`、`requested_at`、`attempts`、`status`、`raw_path`、`canonical_path`、错误字段和时间字段。
- canonical prices 至少包含 `trade_date`、`symbol`、`close`、`source`、`source_run_id`；价格数据还需携带或可推导 `adjustment_policy` 与 `available_at`。
- quality 必须能定位字段缺失、重复、异常价格、覆盖缺口和 source manifest 不一致。
- catalog 首轮可为 JSON，至少记录 dataset、schema_version、coverage、quality_status 和 latest manifest run。

**回写 Story / Wave**：STORY-014 定义契约；STORY-015 写 raw/manifest；STORY-016 写 canonical/quality/catalog。

## ADR-012：多源校验先稳定接口，真实多源比对后置启用

**状态**：Draft for CR-004 CP3/CP4 review

**决策**：首轮多源校验只要求 fake/fake 或 fake/reference 的差异比对接口与结构化输出；真实 TickFlow/AkShare/Tushare 之间的行情差异比对在 source/interface、凭据、配额和字段口径确认后再启用。

**理由**：多源真实比对容易把联网、授权和口径问题混入最小闭环。先稳定接口可保证 validation、quality 和报告消费方不再反复变化。

**约束**：

- 比对输出至少包含 dataset、key、field、left_source、right_source、left_value、right_value、diff、tolerance、status。
- 默认测试只能使用 fake/reference 数据，不调用真实网络。
- 真实比对启用前必须更新 source registry、质量报告字段说明和 QA 回归命令。

**回写 Story / Wave**：STORY-017 负责多源比对接口和 fake/reference 验收；STORY-018 消费比对和基准状态但不启用真实联网。

## ADR-013：Tushare 只写入本地数据湖链路

**状态**：Draft for CR-005 CP3/CP4 review

**决策**：Tushare 只能通过用户显式执行的 `market_data` 数据层 fetch/backfill job 调用，并经 connector/runtime/storage 写入 raw / manifest，再由 normalization / validation / catalog 派生 canonical / quality / catalog / gold。Tushare API 不得直接接入 `engine/data_loader.py`、`engine/backtest.py`、实验十、实验十二、Backtrader adapter 或 Notebook 主路径；消费层返回的 `remediation_job_spec` 只描述人工可执行补齐动作，不自动执行。

**理由**：Tushare 5000 提供更稳定的真实数据能力，但直接进入回测主路径会破坏 ADR-001/009 的离线复现边界，并增加凭据、限频和测试不稳定风险。

**约束**：

- `market_data/connectors/tushare.py` import 阶段网络调用次数为 0；真实 provider 只能在 enabled + allowlist + explicit command 路径延迟导入。
- `TUSHARE_TOKEN` 只能作为环境变量名引用；token 值不得进入 manifest、quality、catalog、日志、错误消息或测试 fixture。
- 真实调用必须同时满足 `enabled=true`、exact interface allowlist、token env 存在和用户显式真实抓取命令。
- 真实抓取前必须支持 plan/dry-run，输出 dataset、接口、日期范围、批次数、目标 lake root、run id、resume policy、manifest/quality/catalog 目标路径和错误枚举，不调用网络。
- `hs300_index` backfill job spec 至少包含 `dataset=hs300_index`、`source=tushare`、exact interface、`index_code`、start/end、lake root、run id、resume policy 和 `dry_run=true` 默认。

**回写 Story / Wave**：CR005-S01 是写湖入口并拥有 `market_data/cli.py` 或等价 job 的主契约；CR005-S02/S03 消费 raw/manifest；CR005-S04/S06 只能读取下游本地产物并展示 remediation spec。

## ADR-014：CR-005 多 dataset schema 与 quality gate 先于消费方冻结

**状态**：Draft for CR-005 CP3/CP4 review

**决策**：CR-005 的 P0 dataset 至少包含 `prices`、`hs300_index`、`trade_calendar`、`index_weights`；P1 dataset 包含 `adj_factor` / 复权口径和 `stock_basic`。新增 dataset 必须先在 `market_data/contracts.py`、`source_registry.py`、normalization、validation、catalog 和 readers 中形成 exact 契约，再允许实验或 Backtrader 消费。非行情 dataset 必须定义 `available_date` / `effective_date` / `available_at` 或等价字段；行情 dataset 必须保存 `adj_factor` 与统一 `adjustment_policy` 下的 adjusted price。

**理由**：当前代码事实显示 `market_data/readers.py` 和 normalization/validation 主要支持 `prices`。如果 Backtrader 或实验先行，会重复设计数据适配层，并绕过 quality gate。

**约束**：

- raw 到 dataset 只允许显式 `target_dataset` 或 exact interface 映射，禁止 fuzzy/contains/相似度推断。
- 每个 dataset 的 quality CSV 至少含 `fetch_status`、`dataset_status`、coverage、thresholds、denominator、run_id/source/interface 复现字段。
- 价格收益、技术指标和 forward return 必须使用同一 `adjustment_policy` 的 adjusted price，不得混用未复权价或不同复权策略。
- 参与回测信号、股票池、权重或过滤的非行情数据必须通过 as-of join；消费方看到的数据必须满足 `available_at <= decision_time`。
- reader 不导入 connector/runtime，不写 raw/manifest/canonical。
- quality `fail` 阻断消费方；quality `warn` 只能由显式策略放行并在报告中披露。

**回写 Story / Wave**：CR005-S02 冻结 schema/normalization；CR005-S03 冻结 quality/catalog/readers；CR005-S04/S05/S06 均依赖 CR005-S03。

## ADR-015：沪深 300 基准优先使用本地 `hs300_index`

**状态**：Draft for CR-005 CP3/CP4 review

**决策**：真实沪深 300 基准以本地 `hs300_index` canonical/gold 为优先事实源。缺失或质量不合格时，返回 typed `BenchmarkResult(status=unavailable|required_missing|quality_failed)`；可携带 `next_action` / `remediation_job_spec`，但不得静默回退到等权代理、当前股票池代理、运行时联网下载或自动执行数据层 backfill。

**理由**：CR-004 已把真实基准定位为只读 gold/canonical。CR-005 引入 Tushare 后可以写入 `hs300_index`，但消费方仍必须保持本地只读与质量门。

**约束**：

- 实验十/十二、轻量回测报告和 Backtrader 对照报告只能通过 reader / benchmark resolver 获取基准。
- `BenchmarkResult` 必须至少披露 status、dataset、source、index_code、interface、date range、coverage、quality_status、missing_reason、required、remediation job spec、catalog entry、run / lineage。
- `hs300_index` quality gate 必须记录 `benchmark_kind`、trade calendar coverage denominator、missing trade dates、gap reason、duplicate key count、source lineage、raw checksum 或等价 lineage、quality thresholds 和 available/unavailable 映射。
- `hs300_index` 口径（价格指数/全收益指数/其他）在 CR5-Q2 未确认前保持 OPEN，Story 可先交付 unavailable 和只读契约；真实 available 路径只能在口径冻结后实现。
- 旧等权买入持有或同股票池代理如保留，只能命名为 `proxy_baseline`；不得填充 `hs300_index` benchmark 字段。

**回写 Story / Wave**：CR005-S04 负责本地基准、`BenchmarkResult` typed schema 和实验只读基准；CR005-S06 复用同一基准契约。CR005-S04/S06 开发必须等待 hs300 backfill job、reader quality、BenchmarkResult schema 和 benchmark policy 冻结。

## ADR-016：Backtrader 作为可选后端，不替代轻量主路径

**状态**：Draft for CR-005 CP3/CP4 review

**决策**：Backtrader 并入 CR-005 的 CR005-S06，作为 optional backend 和结果对照能力。默认主路径仍是 `engine/backtest.py`。Backtrader adapter 只读本地 canonical/gold + quality gate 派生的干净 factor panel / score / OHLCV feed，不联网、不读取 `TUSHARE_TOKEN`、不导入 `market_data.connectors`，且不得早于 CR005-S02/S03 的 PIT、复权和 quality gate 契约稳定进入开发。

**理由**：Backtrader 的真实价值依赖稳定 OHLCV、日历、benchmark 和质量门；提前独立开发会导致数据 feed 与 CR-005 dataset 口径漂移。把它设为 optional backend 可保留轻量主路径的透明性。

**约束**：

- 未安装 Backtrader 时必须返回 `backend_unavailable` 或等价结构化状态；默认轻量回测和默认 pytest 不受影响。
- Backtrader 依赖只能在 CP5 批次人工确认后通过 uv 加入 `pyproject.toml` / `uv.lock`。
- Backtrader adapter 禁止导入 `market_data.connectors`、`market_data.runtime`、`market_data.storage` 或读取环境变量 `TUSHARE_TOKEN`。
- Backtrader adapter 不生成 PIT、不计算复权因子、不读取 Tushare、不联网、不绕过 quality gate；其职责限定为调仓、成交、成本、仓位、净值和风险分析。
- Backtrader 输出只能作为对照报告；不得把 Backtrader 结果覆盖轻量回测结果。

**回写 Story / Wave**：CR005-S06 位于 CR5-W5，显式依赖 CR005-S02/S03/S04，文件所有权必须避免与 Tushare connector、normalization 和 reader 写入冲突。

## ADR-017：PIT 与复权由 Pandas 数据层保证，Backtrader 只消费干净输入

**状态**：Draft for CR-005 CP3/CP4 review

**决策**：PIT 对齐和复权价格生成属于 Pandas 数据层职责。所有非行情数据按 `available_date` / `effective_date` / `available_at` 做 as-of join；行情层保存 `adj_factor` 与统一 `adjustment_policy` 下的 adjusted price。Backtrader 只消费数据层产出的干净 factor panel、score 或 OHLCV feed。

**理由**：PIT 和复权是回测有效性的基础数据契约，不应散落到 Backtrader adapter 或各消费方中。先在 Pandas 数据层完成清洗，可让轻量回测、实验和 Backtrader 共享同一数据事实源，减少未来函数、复权口径漂移和联网绕过风险。

**约束**：

- 任一回测日的非行情字段必须满足 `available_at <= decision_time`；无法证明可得性时不得进入信号、过滤、权重或 score。
- `prices` 或关联行情层必须保存 `adj_factor` 与 adjusted price；收益、技术指标和 forward return 使用统一 `adjustment_policy` 的复权价格。
- Backtrader adapter 的输入只能是 reader/quality gate 后的 factor panel、score 或 OHLCV feed。
- Backtrader 只负责调仓、成交、成本、仓位、净值和风险分析；PIT 生成、复权因子计算、Tushare 读取、联网和 quality gate 判定均为禁止职责。
- consumer 缺 `hs300_index` 时的 `required_missing` 只能透传 typed `BenchmarkResult` 与 remediation spec；不得由 Data Loader、实验或 Backtrader 自动触发 fetch/backfill。

**回写 Story / Wave**：CR005-S02 负责 PIT/复权字段与 normalization；CR005-S03 负责 PIT as-of gate、复权一致 gate 和 reader 输出；CR005-S04 负责 BenchmarkResult 与 benchmark policy；CR005-S06 的 dev_gate 必须等待 CR005-S02/S03/S04 相关契约 confirmed/verified。

## ADR-018：Tushare-first structured lake 与运行时消费面分离

**状态**：Draft for CR-006 CP3/CP4 review

**决策**：CR-006 的新数据主线采用 Tushare-first structured lake。`MARKET_DATA_LAKE_ROOT` 继续表示 structured market data lake 根目录，承载 raw / manifest / canonical / quality / catalog / gold 分层，并作为新链路事实源。raw 与 manifest 仍然需要保留，但职责限定为数据获取审计、断点续传、复现、replay 和质量追溯；轻量回测框架与 Backtrader 不得把 raw/manifest 当作运行时输入。当前轻量回测框架应消费 canonical/gold reader，或从 canonical/gold 派生到仓库外 external `legacy_flat` 的兼容 flat parquet。Backtrader 只消费经过 quality gate、PIT as-of 和复权一致检查后的 clean OHLCV / factor / score feed。仓库旧 `data/` 保持现状，仅供以后人工参考/比对，不作为默认 fallback、不参与 Tushare 主路径、不用于证明新链路可用。

**理由**：旧 `data/` 的来源和质量证明无法在本轮设计中确认，Tushare 也不能被承诺完全覆盖旧 `data/`。若继续把旧 `data/` 作为 fallback，会把不可审计历史数据带入新链路。将 Tushare structured lake 设为事实源，并把 raw/manifest 与运行时消费面分离，可以同时满足可审计、可回放、可质量追溯和回测运行时稳定性。

**约束**：

- 不读取、列出、复制、迁移或删除真实 `data/**`；本 ADR 不授权任何旧数据操作。
- 不读取、打印或记录 `.env`、Tushare token、NAS 用户名、密码或真实私有路径。
- Tushare fetch/backfill 只能由用户显式执行的数据层 job 触发；轻量 engine、experiments、Backtrader 和 Notebook 不得自动触发 fetch/backfill。
- raw/manifest 必须记录 lineage 和状态，但不得被轻量回测或 Backtrader 直接消费。
- canonical/gold 必须经过 schema、PIT、复权和 quality gate 后才能进入运行时消费面。
- external `legacy_flat` 若存在，只能由 canonical/gold 派生，并带有 catalog/manifest lineage；它不等同于旧 repo `data/`。
- 旧 repo `data/` 只能作为 reference-only 样本；默认运行、测试和 smoke 不得依赖旧 `data/` 证明新链路可用。
- Backtrader adapter 禁止导入 `market_data.connectors`、`market_data.runtime`、`market_data.storage`，禁止读取 `TUSHARE_TOKEN`，禁止联网或自行生成 PIT/复权。

**回写 Story / Wave**：CR006-S01-tushare-first-data-acquisition-runbook 冻结 Tushare-first 采集、raw/manifest 审计和 canonical/gold 产出边界；CR006-S02-canonical-gold-lightweight-engine-adapter 设计轻量回测消费面；CR006-S03-backtrader-clean-feed-contract 设计 Backtrader clean feed；CR006-S04-old-data-reference-only-guardrail 固化旧 `data/` reference-only 护栏。四者统一进入 `CR006-BATCH-A` LLD，CP5 全量确认前不得实现。

## ADR-019：长周期 backfill 采用分批 planner、resume 与 coverage gate

**状态**：Draft for CR-007 CP3/CP4 review

**决策**：CR-007 的 `prices` 长周期补齐不采用无边界全市场一次性抓取。`market_data` 数据层必须先提供 dry-run planner，以显式 symbols / universe source、日期分片、股票池分批、`prices.daily` + `prices.adj_factor` 双接口计划、resume policy 和 coverage gate 为正式 backfill 前置合同。dry-run 默认网络调用为 0、写入为 0；真实 Tushare 调用和真实 lake 写入必须由用户另行授权。

**理由**：CR-006 已把 Tushare structured lake 设为事实源，但当前只有 2025 小窗口 `prices`，不能支撑 2015-2020 或 2015-2025 研究。长周期数据生产涉及配额、失败恢复、复权因子和覆盖证明，必须先规划、再授权执行。

**约束**：

- planner 必须输出 dataset、source/interface、start/end、symbols/universe source、batch_count、batch_size、run_id、batch_id pattern、target raw/manifest/canonical/quality/catalog/gold paths、resume policy、coverage gate 和 error enum。
- `prices.daily` 与 `prices.adj_factor` 必须按同一 `adjustment_policy` 进入 normalization；复权冲突阻断 canonical/gold 消费。
- 不指定 symbols/universe source 的全市场长周期抓取不得作为默认策略。
- 缺少 lake root、日期非法、股票池为空或 coverage 未满足时返回 structured error / `required_missing`，不得读取旧 `data/**` 补齐。

**回写 Story / Wave**：CR007-S01-prices-long-horizon-backfill-planner 是主 Story，文件所有权覆盖 `market_data/cli.py` 或等价 job、`market_data/runtime.py`、`market_data/connectors/tushare.py`、`market_data/normalization.py`、`market_data/validation.py` 与测试。

## ADR-020：真实沪深300 benchmark 必须与交易日历同区间覆盖

**状态**：Draft for CR-007 CP3/CP4 review

**决策**：真实沪深300 benchmark 只由本地 `hs300_index` canonical/gold 提供，且必须以同区间 `trade_calendar.is_open=true` 作为 coverage denominator。`hs300_index` 与 `prices` 无重叠、coverage gap、quality fail 或 benchmark policy 未确认时，消费层返回 typed `unavailable` / `required_missing` / `quality_failed`；代理 benchmark 只能命名为 `proxy_baseline`，不得填充 `hs300_index` 字段或声明沪深300超额收益。

**理由**：当前代码已有 `BenchmarkResult` 和 `resolve_hs300_benchmark`，实验十/十二已可消费只读基准；但实验十三仍固定同股票池等权代理，且当前 `hs300_index` 小样本与 2025 `prices` 无重叠。若不冻结真实 benchmark policy，实验报告会继续混淆代理与真实基准。

**约束**：

- S02 必须规划 `hs300_index` 与 `trade_calendar` 至少覆盖 2025 小窗口，并支持 2015-2020 / 2015-2025 长周期。
- quality gate 至少记录 missing trade dates、gap reason、coverage ratio、denominator mode、source lineage、duplicate key count 和 benchmark_kind。
- S04 修改实验十三时必须优先真实 `hs300_index`；缺失时只输出 `proxy_baseline` 对照和 structured missing reason。
- 实验十、实验十二、实验十三均不得在消费路径调用 connector/runtime/storage 或自动 backfill。

**回写 Story / Wave**：CR007-S02-benchmark-calendar-backfill 冻结数据与 coverage；CR007-S04-experiment-real-benchmark-consumption 冻结实验消费。

## ADR-021：dataset readiness 与 PIT / 非 PIT 边界显式化

**状态**：Draft for CR-007 CP3/CP4 review

**决策**：`index_members`、`index_weights`、`stock_basic` 必须具有 dataset readiness 状态，至少覆盖 exact source/interface、canonical schema、key columns、PIT fields、normalizer、validator、catalog、reader 和消费限制。PIT 字段或 historical availability 不完整时，reader/consumer 只能返回 structured warn/unavailable，不得标记为 PIT available。

**理由**：当前代码已定义 `index_members`、`index_weights`、`stock_basic` 常量和部分 PIT 字段，但 Tushare registry / adapter / normalizer 对 `index_members` 与 `stock_basic` 不完整。将这些对象直接用于股票池或过滤会引入未来函数和幸存者偏差。

**约束**：

- `index_members` 与 `stock_basic` 的 Tushare 接口、provider method、schema 和 quality gate 必须在 S03 中冻结；不可用时给出 remediation spec。
- `index_weights` 不等同于 `index_members`；权重数据不能自动推断成完整成分 PIT。
- `stock_basic` 可作为上市/退市/ST 等过滤参考前，必须定义 `effective_date`、`available_date`、`available_at` 或等价字段。
- 消费方必须记录 `is_pit_universe` / `pit_status` / `readiness_status`，不得只在文档中口头披露。

**回写 Story / Wave**：CR007-S03-index-members-stock-basic-datasets 是主 Story，并为后续实验和股票池消费提供 readiness contract。

## ADR-022：旧质量报告作为 legacy，当前质量真相源为 lake quality/catalog

**状态**：Draft for CR-007 CP3/CP4 review

**决策**：仓库旧 `reports/data_quality_report.csv` 只能作为 legacy old report 保留，不再作为 canonical lake 当前质量真相源，也不得作为 CR-007 coverage 证明。当前质量真相源必须来自 configured lake root 下的 `quality/catalog`，并通过 dataset、run_id、source/interface、coverage、quality_status 和 lineage 字段追溯。

**理由**：CR-007 明确旧报告覆盖 `2020-01-02` 至 `2024-04-24`，与当前 canonical/gold 小窗口和未来长周期 backfill 不是同一质量面。若继续引用旧报告，会掩盖真实 benchmark 和 long-horizon coverage 缺口。

**约束**：

- 不覆盖旧 `reports/data_quality_report.csv` 来制造当前质量通过证据。
- README / USER-MANUAL / guardrail 必须说明旧报告 legacy 边界，以及 lake `quality/catalog` 的当前质量真相源角色。
- 任何 coverage 声明必须携带 dataset、start/end、denominator、run_id/source/interface、quality_status 和 catalog/lineage。
- `reports/**` 作为真实输出或旧报告读取均需遵守当前 Story 文件所有权与授权边界；设计阶段不读取旧报告内容。

**回写 Story / Wave**：CR007-S05-data-quality-report-and-doc-guardrail 负责文档与 guardrail。

## ADR-023：当前骨架作为回测平台主干，开源框架作为可选后端

**状态**：Accepted

**决策**：后续继续在当前 `market_data/` + `engine/` + `strategies/` 骨架上完善回测平台，不整体迁移到 Backtrader、VectorBT、Zipline、Qlib 或 LEAN。`market_data/` 继续负责数据湖、catalog、quality、lineage、PIT 和复权契约；`engine/` 继续负责轻量日频回测、指标、报告、候选筛选和偏差审计；`strategies/` 继续保持可测策略纯函数接口。Backtrader 作为 optional backend，用于事件驱动、订单/成交语义、仓位和分钟级验证；VectorBT 作为可选扫描加速器，用于大规模参数扫描和向量化研究；Qlib 仅在机器学习因子平台成为主目标时单独评估；LEAN 仅在实盘、多资产或专业交易平台成为主目标时单独评估。

**理由**：当前项目的核心资产是本地数据可信层、quality gate、catalog、lineage、离线回测边界、复权/PIT 契约和聚宽人工对照能力。直接迁移到单一开源框架会打散这些边界，并把 A 股数据口径、凭据、联网、benchmark 和质量证明问题重新暴露给消费层。完全自研完整交易引擎又会在订单生命周期、分钟级事件循环、撮合、挂单、撤单和风控上付出过高成本。保留当前骨架为主干、按需集成开源后端，可以同时保持数据可信边界和工程扩展性。

**约束**：

- 默认回测主路径仍为轻量 engine，不依赖 Backtrader、VectorBT、Qlib 或 LEAN。
- 开源后端只能消费已通过 `market_data` quality gate、PIT as-of、复权一致性和 lineage 校验的本地数据。
- 开源后端不得读取 token、导入 connector/runtime/storage、联网、写 lake、触发 backfill 或绕过 catalog。
- Backtrader 输出只能作为对照或更真实事件驱动后端结果，不得覆盖轻量 engine 默认结果。
- VectorBT 只能作为参数扫描和向量化研究加速器；最终报告 schema、质量披露和 benchmark 语义必须与当前 engine 对齐。
- Qlib、LEAN、Zipline Reloaded 不进入短期主路径；引入前必须另起架构评估或变更记录。
- 完整路线、阶段目标、切换条件和不做事项以 `docs/ROADMAP.md` 为长期入口。

**回写 Story / Wave**：后续 Story 拆分应优先落在 Phase 1（日频研究可信度）、Phase 2（Backtrader optional backend 做实）、Phase 3（VectorBT 扫描加速）和 Phase 4（因子研究与归因）。具体执行计划需在 `process/STORY-BACKLOG.md` 或 `process/DEVELOPMENT-PLAN.yaml` 中另行拆分，不以本 ADR 直接授权真实抓取、依赖变更或后端迁移。

## ADR-024：`research_input_v1` 作为唯一新研究入口与报告 metadata 合同

**状态**：Draft for CR-008 CP3/CP4 review

**决策**：CR-008 之后的新研究报告和严肃因子研究入口必须声明并消费 `research_input_v1`。该合同至少包含 request、coverage、benchmark、universe、adjustment、label window、quality/readiness、known limitations 和 allowed claims 字段。历史报告可保留为 legacy，不回写旧报告字段；新报告不得绕过 `research_input_v1` 直接解释旧 `data/**` 或旧 `reports/data_quality_report.csv`。

**理由**：实验十四和实验十五已暴露“可跑实验”与“可支撑研究结论”之间的口径差距。若每个实验自行写 metadata，benchmark、PIT、复权、label window 和辅助数据缺失会继续漂移。

**约束**：

- 新报告强制写入 `manifest_run_id` 或 `source_run_id`、coverage start/end、benchmark status、universe mode、adjustment policy、label window、quality/readiness 和 known limitations。
- `research_input_v1` 是研究消费合同，不是数据生产授权；不得触发真实抓取、真实 lake 写入或凭据读取。
- 旧报告保留为 legacy，不作为 current quality truth、fixture、coverage proof 或默认 fallback。

**回写 Story / Wave**：CR008-S01 负责合同和报告 metadata；CR008-S03/S04/S05/S06 均引用该合同。

## ADR-025：proxy benchmark 与真实 benchmark 字段强隔离

**状态**：Draft for CR-008 CP3/CP4 review

**决策**：新报告必须把代理 benchmark 与真实 `hs300_index` 字段分离。代理只能写入 `proxy_*` 或 `proxy_baseline` 字段；真实沪深300只允许写入 `hs300_*` 或 `benchmark_kind=hs300` 的字段。真实 benchmark unavailable、coverage gap、quality fail、policy unconfirmed 或 price overlap missing 时，真实 `hs300_*` 输出次数必须为 0。

**理由**：CR007 已要求真实 benchmark 由 `hs300_index` + `trade_calendar` 同区间 coverage 支撑，但 CR008 指出历史 `benchmark_total_return` / `excess_return` 容易被误读为真实指数超额收益。字段隔离是防误读的最小强约束。

**约束**：

- 代理路径不得填充 `hs300_index`、`hs300_total_return`、`hs300_excess_return` 或等价真实字段。
- 缺真实 benchmark 时可以输出 proxy 探索报告，但必须写 `benchmark_status`、`benchmark_missing_reason` 和 proxy 限制。
- CR007-S04 如继续实现，必须消费本 ADR；不得只延续 CR007 的旧代理 fallback 文案。

**回写 Story / Wave**：CR008-S02 主责；CR007-S04 在 CR008 CP3/CP4 后按本 ADR 修订或确认继续。

## ADR-026：`research_dataset_builder` 只读消费 canonical/gold，不触发补数

**状态**：Draft for CR-008 CP3/CP4 review

**决策**：新增 `engine/research_dataset.py` 或等价 builder，作为研究数据集构建入口。builder 只允许消费 `market_data.readers`、`market_data.benchmarks` 和已经冻结的 canonical/gold 只读合同；不得导入 `market_data.connectors`、`market_data.runtime`、`market_data.storage`，不得执行 backfill、fetch、normalize、revalidate 或 replay。

**理由**：CR008 的核心是研究消费侧硬化。如果 builder 兼任数据生产，会突破 CR006/CR007 的离线边界并引入凭据、联网和真实 lake 写入风险。

**约束**：

- builder missing 结果只能返回 typed missing / remediation spec，`auto_execute=false`。
- builder 默认测试使用 tmp lake / fixture / monkeypatch，不需要 token、NAS 或真实 lake。
- builder 不读取旧 `data/**` 或旧 `reports/data_quality_report.csv`。

**回写 Story / Wave**：CR008-S03 主责；S04/S05/S06 在 builder 输出上定义 gate 和 allowed claims。

## ADR-027：PIT / fixed universe 必须显式声明

**状态**：Draft for CR-008 CP3/CP4 review

**决策**：研究入口必须输出 `universe_mode`、`is_pit_universe`、`pit_status` 和 `survivorship_bias_note`。严肃研究模式要求 PIT universe；PIT 不可用时必须结构化失败。探索模式可使用 `fixed_snapshot`，但必须披露幸存者偏差，且不得声明严肃 PIT 因子结论。

**理由**：当前 `index_members` 仍可能是固定快照，`stock_basic` 也可能只有当前状态。若不显式区分 PIT / fixed snapshot，因子结论会被幸存者偏差污染。

**约束**：

- `quality_status=pass` 不等于 PIT available；必须单独检查 `pit_status`。
- `index_weights` 不得替代完整 `index_members`。
- fixed snapshot 只能用于探索或框架验证，不能支撑严肃因子归因。

**回写 Story / Wave**：CR008-S05 主责，依赖 CR007-S03 / CR008-S03 合同。

## ADR-028：quality / adjustment / label window gate 是研究准入硬门

**状态**：Draft for CR-008 CP3/CP4 review

**决策**：研究入口必须把 quality、复权口径和未来收益标签窗口变成 gate。`quality_status=fail`、复权口径混用或缺失、`forward_return_horizon` 导致末端样本无法生成完整标签时，严肃研究必须 fail；探索模式允许结构化截断，但必须写 `label_available_end` 和截断样本数量。

**理由**：当前因子实验可运行不代表样本标签完整、复权口径一致或质量可审计。没有硬门会让错误样本进入收益、IC、分层或策略回测结论。

**约束**：

- 同一研究数据集只能有一个 `adjustment_policy`。
- label window 截断必须可量化：至少记录 `forward_return_horizon`、`label_available_end`、截断行数或截断日期。
- quality gate 不得用旧质量报告替代 lake quality/catalog 或 reader result。

**回写 Story / Wave**：CR008-S04 主责，依赖 CR008-S03 builder。

## ADR-029：因子辅助数据缺失时禁止对应严肃结论

**状态**：Draft for CR-008 CP3/CP4 review

**决策**：因子研究报告必须声明可交易性、OHLCV/VWAP、行业、市值 / 流通市值、流动性、复权审计和风格暴露的 availability。缺可交易性数据时不得声明真实可成交；缺行业 / 市值时不得声明行业中性或 size 中性；缺风格暴露时不得声明纯 alpha；缺复权审计链路时只能声明“使用已复权价格”，不得声明公司行动链路可审计。

**理由**：实验十五证明因子框架可运行，但没有这些辅助数据时不能支撑严肃因子归因、容量、可交易性或中性化结论。

**约束**：

- S06 不默认授权真实辅助数据抓取，只冻结消费合同和缺失降级语义。
- 辅助数据缺失应进入 `known_limitations` 与 `allowed_claims`，不是静默 warning。
- 后续新增真实行业、市值、可交易性或风格暴露数据生产时必须另走 CR / LLD / CP5。

**回写 Story / Wave**：CR008-S06 主责，依赖 CR008-S03/S04/S05。

## ADR-030：生产级数据湖独立 companion HLD

**状态**：Draft for CR-010 CP3/CP4 review

**决策**：CR-010 将生产级市场数据湖拆入 `process/HLD-DATA-LAKE.md`，主 HLD `process/HLD.md` 只保留 engine / experiments / reports / optional backend 的只读消费契约和双向引用。数据湖 HLD 拥有 connector、runtime、storage、backfill、normalization、validation、catalog publish、lineage 和 quality truth。

**理由**：CR-010 同时涉及生产数据治理和回测真实性消费，职责、风险、授权边界和验收方式均已超出主 HLD 单一研究工具增量。拆分能避免真实回补和研究消费边界混写。

**约束**：

- 主 HLD 不再新增真实源、runtime、storage、publish 细节，只同步消费契约影响。
- 数据湖 HLD 必须独立通过 CP3；Story/Wave 必须在 CP4 中引用 companion HLD。
- CR-004 至 CR-009 历史 PASS / FAIL 记录不回滚，CR-010 只在其上继续生产化。

**回写 Story / Wave**：CR010-S01 至 CR010-S12；`CR010-DL-BATCH-A`、`CR010-DL-BATCH-B`、`CR010-QF-BATCH-C`。

## ADR-031：consumer 只读 published catalog / canonical / gold

**状态**：Draft for CR-010 CP3/CP4 review

**决策**：engine、experiments、Backtrader、VectorBT 和 research dataset builder 只能读取已 publish 的 catalog current truth 及其 canonical/gold 派生数据。consumer 不得导入 `market_data.connectors`、`market_data.runtime`、`market_data.storage`、真实 provider SDK、网络库或 `.env` / token 读取逻辑。

**理由**：CR-004 至 CR-009 已反复确立“真实源写湖、消费层只读”的物理隔离原则。CR-010 需要把该原则提升为生产化准入门，避免缺数据时在回测路径隐式补数。

**约束**：

- missing / quality failed / required_missing 只能返回 remediation spec，且 `auto_execute=false`。
- consumer 路径网络调用次数目标值为 0。
- `validate` 不等于 publish；未 publish 的 run 不得作为 current truth 被 consumer 读取。

**回写 Story / Wave**：CR010-S01、CR010-S05、CR010-S10、CR010-S11、CR010-S12。

## ADR-032：日频价格与开盘前决策可用时点规则

**状态**：Draft for CR-010 CP3/CP4 review

**决策**：`trade_date=T` 的日频 `close/adjusted_close` 表示 T 日收盘后形成的价格事实。T 日开盘前决策只能使用 T-1 及更早已形成的数据；T 日收盘后可以使用 T 日 close 生成 T+1 交易信号。事件数据必须提供 explicit `available_at`，缺失时不得进入决策。

**理由**：用户已确认 D11。若继续以日期字段模糊推断开盘前可见性，会造成未来函数风险，尤其影响 open-decision 与事件信号。

**约束**：

- 价格和 benchmark canonical 必须写 `available_at_rule=daily_close_fact` 或等价值。
- open-decision consumer 必须使用 `previous_trade_day_for_open_decision` 规则。
- events 不适用日期推导；缺 explicit `available_at` 使用 `missing_required` 并 fail。

**回写 Story / Wave**：CR010-S02、CR010-S03、CR010-S09、CR010-S10。

## ADR-033：W3 source/interface 未确认前 fail-fast

**状态**：Draft for CR-010 CP3/CP4 review

**决策**：PIT、`trade_status`、`prices_limit`、`events` 等 W3 数据在 source/interface 未 exact 确认前，batch planning、normalizer、quality、reader 和 engine gate 均返回 `source_unresolved` / `required_missing` / `missing_required`，不得用空数据、`stock_basic` 当前快照、`index_weights` 或模糊 interface 替代 available。

**理由**：W3 数据直接影响 PIT、可交易性、涨跌停和事件时点。任何伪 available 都会让 production_strict 产生错误的真实性声明。

**约束**：

- source registry 必须 exact match；未知 interface fail-fast。
- `index_weights` 不得替代完整 `index_members`。
- `stock_basic` 只辅助，不证明 PIT universe。
- exploratory 可以继续实验但必须写 limitation；production_strict 必须 fail。

**回写 Story / Wave**：CR010-S06、CR010-S07、CR010-S08、CR010-S09、CR010-S10。

## ADR-034：catalog 显式 publish 后才能作为 current truth

**状态**：Draft for CR-010 CP3/CP4 review

**决策**：`validate` 只产出 candidate quality/readiness；只有显式 `publish` 且质量策略满足要求后，catalog 才更新 current truth。reader 默认只读 current truth。legacy `reports/data_quality_report.csv` 不作为 current quality truth。

**理由**：CR-009 真实复验暴露过质量失败和 replay 契约缺口。若 validate 自动更新 catalog，会让未确认或失败数据污染下游实验。

**约束**：

- `quality_status=pass` 才允许默认 publish。
- `quality_status=warn` 只允许 exploratory 或显式 allow warn publish。
- `quality_status=fail` 阻断 publish 和 production_strict。
- catalog 必须记录 coverage denominator、coverage ratio、source/interface、run_id、lineage checksum、quality/readiness/pit、available_at_rule、known_limitations、published_at。

**回写 Story / Wave**：CR010-S01、CR010-S05、CR010-S10、CR010-S11。

## ADR-035：真实回补采用分阶段授权和可恢复批次执行

**状态**：Draft for CR-010 CP3/CP4 review

**决策**：真实回补必须按“小窗口 3-5 个交易日 -> 1 年 -> 全历史 2015-01-01 至最近闭市交易日”逐级推进。每阶段先 dry-run，再由用户显式授权真实执行。批次执行必须记录 run_id、batch_id、idempotency_key、dataset、source/interface、date range、coverage、quality/readiness、失败批次和 retry 结果。

**理由**：数据湖真实写入和大规模抓取风险高，必须具备恢复和审计能力，且不能用一次授权覆盖所有历史范围。

**约束**：

- 成功批次默认 skip；失败批次可 retry。
- 参数、source/interface、dataset、date range、symbol universe 变化时返回 `resume_conflict`。
- provider error、network error、rate limited、schema mismatch、quality failed 使用结构化 enum。
- 日志不打印 token、真实私有路径或凭据。

**回写 Story / Wave**：CR010-S01、CR010-S02、CR010-S03、CR010-S05；真实 smoke 由 meta-qa 在用户授权后单独执行。

## ADR-036：CR-011 benchmark policy consumption 必须区分真实 benchmark 与 proxy baseline

**状态**：Draft for CR-011 CP3/CP4 review

**决策**：实验 17-21 v2 和后续因子研究报告必须通过 `BenchmarkPolicyResult` 消费真实 `hs300_index` 与 benchmark policy。真实 benchmark 字段只能写入 `hs300_*`；代理同股票池等权买入持有只能写入 `proxy_*` / `proxy_baseline`。缺真实 benchmark 时必须写 `benchmark_missing_reason`，不得静默替代。

**理由**：实验 17-21 旧报告明确当前 benchmark 是 proxy baseline。若新版报告仍把 proxy 当作沪深 300 超额收益，会直接污染因子有效性和策略 alpha 判断。

**约束**：

- `benchmark_policy_id`、`benchmark_kind`、`index_code`、coverage、quality/readiness 和 policy confirmed 状态必须进入 research metadata。
- proxy 结果写入真实 `hs300_*` 字段的次数必须为 0。
- production_strict 缺真实 benchmark 时 fail；exploratory 可输出 proxy，但必须写 limitation。

**回写 Story / Wave**：CR011-S01；`CR011-DATA-BATCH-A`。

## ADR-037：CR-011 PIT universe 与股票生命周期采用 as-of gate

**状态**：Draft for CR-011 CP3/CP4 review

**决策**：严肃因子研究必须使用 `universe_mode=pit`、`is_pit_universe=true` 和 `pit_status=pass` 的 as-of universe。`index_members` 是完整 membership 的主证据；`index_weights` 只提供权重信息，`stock_basic` / `stock_lifecycle` 只辅助上市、退市、状态判断，不得替代 PIT membership。

**理由**：固定快照股票池会引入幸存者偏差。PIT universe 是把实验 17-21 从探索结论升级为生产级研究输入的前置条件。

**约束**：

- universe join 必须满足 `available_at <= decision_time`，as-of 违规计数目标值为 0。
- fixed snapshot 只能进入 exploratory 并写 `survivorship_bias_note`。
- 缺 PIT membership 时 production_strict fail，不允许用当前快照或权重表伪装。

**回写 Story / Wave**：CR011-S02；`CR011-DATA-BATCH-A`。

## ADR-038：CR-011 tradability gates 必须覆盖真实可交易约束

**状态**：Draft for CR-011 CP3/CP4 review

**决策**：因子策略回测的 production_strict 模式必须同时通过停牌、涨跌停、ST、无成交、上市天数和事件状态 6 类 gate。任一 gate 缺 source/interface、缺 `available_at` 或 quality/readiness 不合规时，production_strict fail；exploratory 可运行但必须写 `blocked_claims`。

**理由**：实验 17-21 旧报告使用 close 代理且未纳入真实可交易约束，不能声明真实可成交或容量结论。可交易性 gate 必须在 portfolio 前形成机器可读矩阵。

**约束**：

- `trade_status`、`prices_limit`、`events` 均继承 CR-010 W3 fail-fast 策略。
- 默认全可交易、空表可用、日期推导事件可用时点均被禁止。
- 每个 blocked trade 必须有结构化 reason。

**回写 Story / Wave**：CR011-S03；`CR011-DATA-BATCH-A`。

## ADR-039：CR-011 execution price / VWAP 缺失必须显式降级

**状态**：Draft for CR-011 CP3/CP4 review

**决策**：执行价 policy 只允许 `open`、`close`、`vwap`、`close_proxy`。当真实 open/VWAP 不可用时，consumer 只能显式选择 `close_proxy` 降级，并写入 `execution_degradation_reason`；降级后不得声明 VWAP 成交、真实开盘成交或真实可成交。

**理由**：旧实验使用 close 执行价代理。若不把执行价降级写成合同，策略回测容易被误解为真实成交模拟。

**约束**：

- OHLCV / VWAP availability 必须进入 research metadata。
- VWAP 由 `amount / volume` 派生时，LLD 必须明确公式、异常量处理和可审计限制；未确认前默认 `vwap_status=required_missing`。
- execution price 缺失不得前填、后填或 0 填充。

**回写 Story / Wave**：CR011-S04；`CR011-DATA-BATCH-A`。

## ADR-040：CR-011 adjustment 与 corporate action audit 分层声明

**状态**：Draft for CR-011 CP3/CP4 review

**决策**：因子、收益、benchmark 和 portfolio 计算必须使用一致 `adjustment_policy`。`adj_factor` lineage 和 corporate action availability 必须分开表达：只有 `adj_factor_lineage` 不足以声明“完整公司行动链路可审计”；缺 corporate action 时只能声明“使用已复权价格”。

**理由**：复权口径混用会直接影响收益、因子和标签。公司行动审计是更强声明，不能由复权因子存在自动推出。

**约束**：

- 复权口径混用进入因子计算的次数必须为 0。
- `adjustment_audit_status` 必须输出 `pass / required_missing / quality_failed`。
- corporate action 缺 explicit `available_at` 时不得进入事件型决策。

**回写 Story / Wave**：CR011-S05；`CR011-DATA-BATCH-A`。

## ADR-041：CR-011 industry / market cap / style exposure 决定中性化声明边界

**状态**：Draft for CR-011 CP3/CP4 review

**决策**：行业中性、市值中性、风格中性和 pure alpha 声明必须依赖对应 exposure availability。行业分类、市值/流通市值、beta/style exposure 必须具备 effective/available_at 或明确 missing reason；当前快照不能作为 PIT exposure 支撑生产级中性化结论。

**理由**：没有 PIT exposure 时，因子表现可能由行业、市值或风格暴露驱动。报告必须阻断过强结论，而不是只输出全市场 z-score。

**约束**：

- 缺行业数据时行业中性和行业归因声明输出次数为 0。
- 缺市值/流通市值时 size neutral、容量结论和市值加权 IC 声明输出次数为 0。
- 缺 style exposure 时 pure alpha / 风格中性声明输出次数为 0。

**回写 Story / Wave**：CR011-S06；`CR011-DATA-BATCH-A`。

## ADR-042：CR-011 liquidity / capacity / cost sensitivity 使用固定网格和可审计输入

**状态**：Draft for CR-011 CP3/CP4 review

**决策**：容量和成本敏感性必须使用可追溯的 amount、volume、turnover、ADV 或等价流动性输入，并固定输出 `[0, 5, 10, 20]` bps 四档成本网格。缺流动性输入时不得声明容量可行，单一成本点不得支撑稳健性结论。

**理由**：实验 17-21 的高换手因子对成本敏感。容量和成本必须作为研究输出维度，而不是只在最终收益中体现一个默认成本参数。

**约束**：

- capacity report 必须包含成交额占比、换手、持仓数量、样本损失和成本侵蚀 5 类字段。
- cost grid 是报告合同，不允许只输出最佳成本假设。
- liquidity/capacity missing 必须进入 `blocked_claims`。

**回写 Story / Wave**：CR011-S07；`CR011-RESEARCH-BATCH-B`。

## ADR-043：CR-011 factor panel audit 与 robust validation 是结论升级前置

**状态**：Draft for CR-011 CP3/CP4 review

**决策**：新版因子研究必须落盘可审计 factor panel，覆盖 raw、directional、winsorized、zscore 四阶段，并输出 rolling、年度、市场状态、参数敏感性、成本敏感性五类 robust validation。报告结论只能从 `allowed_claims` 生成，旧 fixed/proxy/close baseline 不覆盖。

**理由**：实验 17-21 已有因子保留和策略化结果，但缺 panel 级审计和分层稳健性验证。没有审计面板和分层验证，结论无法复现和升级。

**约束**：

- 四阶段 panel 缺任一阶段时 robust validation fail。
- 新报告必须版本化输出，不覆盖 `reports/experiment_17_21/factor_strategy_report.md`。
- rolling/annual/market-state/parameter/cost 五类视图均需写入报告索引或 metadata。

**回写 Story / Wave**：CR011-S08；`CR011-VALIDATION-BATCH-C`。

## ADR-044：CR-013 limited-window pass 不得外推为 full-history production strict

**状态**：Draft for CR-013 CP3/CP4 review

**决策**：`2025-02-11..2026-02-18` limited-window 的 `production_strict_target_window_pass` 只允许作为窗口级结论。`2020-01-01..2024-12-31` 在 10 个正式 dataset 全部补齐 current truth 并通过新审计前，必须保持 `full_history_status=research_limited_only` / `blocked_window=2020-01-01..2024-12-31`，不得输出 full-history production strict allowed claim。

**理由**：CR-013 证据显示 `reports/data_lake_readiness_2020_2024/readiness_summary.md` 的 `overall_status=research_limited_only`，`readiness_matrix.csv` 中 10 个正式 dataset 均为 `limited_window_only` 且 `target_window_covered=False`。把 CR-012 limited-window pass 外推到 2020-2024 会直接污染生产级研究声明。

**约束**：

- 报告、README、USER-MANUAL 和研究 metadata 必须同时输出 `supported_window` 与 `blocked_window`。
- full-history allowed claim、全历史 PIT current truth、全历史可复现实盘级回测声明输出次数必须为 0。
- 解除 blocked 只能通过新 run_id / 新报告完成 10 个正式 dataset 的 2020-2024 full-history readiness audit。

**回写 Story / Wave**：CR013-S01；`CR013-BATCH-A`。

## ADR-045：CR-013 execution / VWAP / minute execution claims 必须保持 blocked

**状态**：Draft for CR-013 CP3/CP4 review

**决策**：当 `execution_price_audit.csv` 显示 `execution_price_status=required_missing`、`true_vwap_available_count=0` 或缺少 `vwap_status=available` 时，真实 VWAP、VWAP fill、分钟线、逐笔、盘口、委托、成交明细和真实撮合执行价必须保持 blocked / unsupported。close proxy 只能作为研究降级口径；不得由 close proxy、`amount/volume` 或其他日频派生方式形成真实 VWAP claim。

**理由**：CR-013 证据中 execution feed 仍缺少真实 VWAP 支撑，blocked claims 已包含 `real_vwap_execution;vwap_fill_claim`。若继续沿用 CR-011 的 close proxy 降级但不阻断 claim，报告会被误读为真实成交模拟。

**约束**：

- `blocked_claims` 必须包含 `real_vwap_execution` 和 `vwap_fill_claim`。
- `minute_tick_level2_order_match` 与真实撮合执行价必须进入 unsupported 声明。
- 真实 VWAP claim 解除条件固定为：存在 `vwap` 字段、`vwap_status=available`、execution audit 通过、相关 Story / CP5 获批。

**回写 Story / Wave**：CR013-S02；`CR013-BATCH-A`。

## ADR-046：CR-013 unsupported register 是正式声明边界输入

**状态**：Draft for CR-013 CP3/CP4 review

**决策**：`reports/data_lake_readiness_limited_2025_2026/unsupported_data_register.csv` 中的 9 个 `data_item` 必须作为正式声明边界输入。`research_contract_only` 只能声明为研究合同候选，`unsupported` 与 `contract_supported_but_unavailable` 必须进入 blocked / unsupported 摘要；所有 `pass_denominator=excluded` 项不得计入正式 dataset pass 分母或 allowed production claim。

**理由**：unsupported register 包含行业、市值、风格、capacity、完整公司行动、非 HS300 benchmark、分钟 / tick / Level2 / 撮合、microstructure impact cost 和真实 VWAP 等关键能力。如果这些项不进入交付声明，用户会把 research-only capability 当成已发布 production dataset。

**约束**：

- README、USER-MANUAL、readiness summary 和新版研究报告必须消费 `data_item`、`status`、`reason`、`pass_denominator`。
- excluded denominator 被计入 formal pass denominator 的次数必须为 0。
- register 缺行或字段缺失时，report/docs summary 必须 fail，不得用自由文本兜底。

**回写 Story / Wave**：CR013-S03；`CR013-BATCH-A`。

## ADR-047：CR-013 证据保留与权限边界

**状态**：Draft for CR-013 CP3/CP4 review

**决策**：`reports/data_lake_readiness_2020_2024/*` 和 `reports/data_lake_readiness_limited_2025_2026/unsupported_data_register.csv` 是 CR-013 的只读证据基线。后续 full-history 补数、真实 VWAP / 分钟数据接入或 unsupported register 刷新必须使用新 run_id、新目录或版本化文件，并写 `old_baseline_preserved=true`。本 CR 的默认设计、Story 计划和文档刷新不授权 provider fetch、真实 lake 写入、凭据读取、旧 `data/**` 读取或旧报告覆盖。

**理由**：CR-013 的价值依赖证据链可追溯。若后续补数覆盖触发证据，无法解释 limited-window pass 与 full-history blocked 的历史边界；若路线图被误解为执行授权，会违反用户给定安全边界。

**约束**：

- 默认计数必须为 `provider_fetches=0`、`lake_writes=0`、`credential_reads=0`、`legacy_data_reads=0`、`old_report_overwrites=0`。
- S04 只输出路线图，不包含真实 provider 命令、token、lake root 写入动作或旧 data 操作。
- 任何真实执行必须另起 Story / CP5，并由用户显式授权。

**回写 Story / Wave**：CR013-S04；`CR013-BATCH-A`。

## ADR-048：Parquet lake + catalog/manifest 继续作为 CR-014 source of truth

**状态**：Draft for CR-014 CP3 review

**决策**：CR-014 继续以外置 Parquet lake、manifest 和 catalog current pointer 作为生产数据事实源。raw / manifest / canonical / gold / quality / catalog 分层继续有效，`validate` 只产生 candidate quality/readiness，只有显式 `publish` 才能更新 catalog current pointer。DuckDB query result、quality report、临时 SQL view 或 pandas/pyarrow audit result 均不得自动成为 current truth。

**理由**：CR-010 已经把数据湖生产链路拆入 companion HLD，并确立 publish gate。CR-014 的全 A since-inception 目标扩大了 universe 和历史范围，但没有改变 source-of-truth 的核心问题：事实源必须可回放、可审计、可回滚，并能用 manifest / lineage 解释每次发布。继续使用 Parquet lake + catalog/manifest 能保持旧 current truth 可读，同时避免在 CP3 前进行高风险事实源迁移。

**约束**：

- P0 dataset 必须保留 raw / manifest / canonical / gold / quality / catalog 职责分离；缺任一必需层时 publish 次数为 0。
- catalog current pointer 必须记录 dataset、schema_version、coverage_start/end、coverage_denominator、latest_manifest_run_id、lineage checksum、published_at、known_limitations。
- `validate pass -> current pointer update` 的自动路径必须为 0。
- legacy `reports/data_quality_report.csv`、CR-012 limited-window report 和 CR-013 evidence report 只能作为 evidence / baseline，不作为 CR-014 current truth。

**回写 HLD / 后续规划**：`process/HLD-DATA-LAKE.md` §17.4、§17.5、§17.6；`process/HLD.md` §30.1、§30.2。CP3 通过后才能进入 Story 拆解。

## ADR-049：DuckDB 只作为 read-only query / audit / feature extraction 候选，不作为事实源

**状态**：Draft for CR-014 CP3 review

**决策**：DuckDB 在 CR-014 中定位为只读 query / audit / feature extraction 候选层。它只能读取 catalog current pointer 指向的 Parquet / gold / canonical 以及受控 SQL 模板，用于 coverage audit、PIT join、feature extraction 和 pandas/pyarrow parity。DuckDB 不替代 Parquet lake、manifest、catalog current pointer 或 publish gate；不得用 `.duckdb` native DB、DuckDB view 或 SQL result 作为 source of truth。

**理由**：DuckDB 官方能力支持直接读取多个 Parquet 文件、projection/filter pushdown、Hive partition filter pushdown，并支持 read-only mode 多进程读取，适合全历史审计查询。另一方面，native DB 多进程写入需要谨慎；当前项目使用外置 lake，事实源迁移到 `.duckdb` 会提高并发、恢复、NAS 文件锁和 lineage 风险。

**约束**：

- CP3/CP5 批准前 `dependency_changes=0`，不得修改 `pyproject.toml` / `uv.lock`。
- `.duckdb_source_of_truth_files=0`；任何持久 `.duckdb` cache 或 DuckLake 方案必须另起 ADR / CR。
- DuckDB 连接必须默认 read-only；失败时回退 pandas/pyarrow audit。
- DuckDB parity pass 只能作为 evidence，不得自动 publish 或生成 allowed claim。

**回写 HLD / 后续规划**：`process/HLD-DATA-LAKE.md` §17.3、§17.5、§17.6、§17.7；`process/HLD.md` §30.3。CP3 通过后由 Story 计划决定是否做 DuckDB spike。

## ADR-050：全 A since-inception 分区、catalog current pointer 与 lifecycle/code-change 是 CR-014 current truth 前置

**状态**：Draft for CR-014 CP3 review

**决策**：CR-014 的 production current truth 以全 A 股证券自存在 / 上市日起至最近已闭市交易日为范围，默认包含沪深北全部 A 股、科创板、创业板、北交所、退市 / 摘牌证券和历史代码变更。P0 dataset 默认沿用 `prices`、`adj_factor`、`hs300_index`、`trade_calendar`、`index_members`、`index_weights`、`stock_basic`，并把 lifecycle / code-change 作为全 A current truth 必需能力。分区策略必须服务 coverage denominator、增量刷新和 replay；catalog current pointer 必须表达当前发布版本，而不是候选质量结果。

**理由**：没有 lifecycle / code-change，coverage denominator 会出现幸存者偏差、重复计数或退市样本丢失；没有 current pointer，研究消费层无法判断哪些数据是发布事实、哪些只是候选。CR-014 的核心价值是全 A 可声明性，而不是单次回补窗口。

**约束**：

- readiness metadata 必须写入 `universe_scope=all_a_share`、`coverage_start_policy=security_inception_or_list_date`、`current_trade_date_policy=last_closed_open_trade_date`、`as_of_trade_date`。
- lifecycle 必需字段至少覆盖 `list_date`、`delist_date`、`list_status`、`code_change_mapping`、`exchange`、`board`、`effective_date`、`available_at`、`source_interface`、`run_id`。
- 缺 lifecycle/code-change、calendar 或 P0 dataset gate 时，输出 `required_missing` / `blocked_claims`，allowed full-A since-inception current truth 输出次数为 0。
- W3、minute、tick、Level2、order book、order match 和真实撮合执行价不因 CR-014 自动升级为 P0；解除 blocked 需单独 source/interface、Story、CP5 和用户授权。

**回写 HLD / 后续规划**：`process/HLD-DATA-LAKE.md` §17.1、§17.2、§17.5、§17.8；`process/HLD.md` §30.1、§30.4。CP3 通过后由 Story 计划拆出生命周期、P0 分层和 current pointer 工作。

## ADR-051：真实执行授权与 claim boundary 分离

**状态**：Draft for CR-014 CP3 review

**决策**：CR-014 HLD/ADR 批准只表示设计边界通过，不表示真实 provider fetch、真实 lake 写入、凭据读取、旧 `data/**` 操作、旧 reports 覆盖或 DuckDB 依赖修改获得授权。任何真实执行必须在后续 Story / CP5 / 用户显式授权下进行，并记录 authorization_id、scope、permission counters 和 claim boundary。报告、README、USER-MANUAL 和研究 metadata 必须消费 `allowed_claims`、`blocked_claims`、`required_missing`，不得以自由文本替代结构化声明边界。

**理由**：CR-014 同时扩大数据范围、引入 DuckDB 候选、涉及 provider 和凭据风险。把“设计通过”误读为“可以执行真实补数或读取旧数据”会违反 CP2 接受的安全边界，并可能覆盖旧 evidence。声明边界和执行授权分离可以让用户在每个风险点做明确决策。

**约束**：

- 未授权默认计数必须为 `provider_fetches=0`、`lake_writes=0`、`credential_reads=0`、`legacy_data_reads=0`、`legacy_data_lists=0`、`legacy_data_copies=0`、`legacy_data_deletes=0`、`old_report_overwrites=0`、`dependency_changes=0`。
- 后续真实执行必须先有 Story dev_gate、CP5 approved、用户显式授权和可审计 authorization_id。
- 旧 `reports/data_lake_readiness_2020_2024/*`、`reports/data_lake_readiness_limited_2025_2026/*` 和旧 `data/**` 不得被本 ADR 授权读取、覆盖或迁移。
- 任一 P0 gate、lifecycle gate、catalog pointer、permission gate 未通过时，allowed full-A since-inception production claim 输出次数为 0。

**回写 HLD / 后续规划**：`process/HLD-DATA-LAKE.md` §17.2、§17.8、§17.10、§17.13；`process/HLD.md` §30.2、§30.5。CP3 通过后由 Story Plan 明确 dev_gate 和文件所有权。

## ADR-052：DuckDB read-only 不等于没有写入，写入由 lake production pipeline 单写者负责

**状态**：Draft for CR-014 CP3 R2 review

**决策**：CR-014 采用“写入链路与查询链路分离”的架构。数据写入由 lake production pipeline 单写者链路负责：CP5 + 用户显式授权后，Provider Adapter / Run Gate 才能抓取 provider 并写入 `raw`、`manifest` 与 run metadata；Normalize / Replay 从 `raw` / `manifest` 生成 `canonical`、必要的 `gold` 和 `quality` candidate；Validate 只写 quality/readiness/parity candidate 或 audit evidence；只有 Explicit Publish Gate 满足质量策略并显式 publish 时才更新 catalog current pointer。DuckDB 保持 read-only，只读取 published current truth 或受控 candidate audit path，不写事实源、不触发 publish、不替代 catalog。

**理由**：用户在 CP3 审查中指出“DuckDB 作为只读，那么数据什么时候写入”。这个问题暴露了设计表达中的歧义：DuckDB 只读只是查询 / 审计层的约束，不代表数据湖没有写入链路。将写入责任集中到 lake production pipeline，可以保留可恢复、可审计、可授权的生产链路；将 DuckDB 保持只读，可以降低 native DB 写入并发、NAS 文件锁、事实源漂移和误发布风险。

**约束**：

- CP3 只批准 HLD/ADR，不授权真实写入；CP3 阶段 `provider_fetches=0`、`credential_reads=0`、`lake_writes=0`、`dependency_changes=0`。
- CP5 + 用户显式授权前，只允许 plan / dry-run / candidate 合同设计，不允许真实 provider fetch、credential read 或 lake write。
- `run` 是唯一允许写 `raw`、`manifest` 和 run metadata 的真实抓取阶段；`normalize` / `replay` 只写派生 candidate；`validate` 只写 candidate / evidence；`publish` 是唯一更新 catalog current pointer 的阶段。
- replay 必须满足 `provider_fetches=0`、`credential_reads=0`、`raw_writes=0`、`current_pointer_changes=0`。
- DuckDB 只能读取 catalog current pointer 指向的 Parquet，或在受控 candidate audit 中读取指定 candidate path；DuckDB query、view、parity report、feature result 不得反向成为 source of truth。

**可行性 / 易用性 / 扩展性结论**：

| 维度 | 结论 |
|---|---|
| 可行性 | 可行。写入继续由既有 lake pipeline 承担，DuckDB 只读消费 Parquet/catalog，不需要在 CP3 阶段迁移事实源或处理 native DB 写入并发 |
| 易用性 | 可解释。用户视角是 `plan -> run -> normalize/replay -> validate -> publish -> read/query`，其中只有 publish 后 reader/DuckDB 默认看到新 current truth |
| 扩展性 | 高。后续可扩展 DuckDB 只读审计、PIT join、feature extraction 和 parity；若要持久 `.duckdb` cache / DuckLake，必须另起 ADR / CR |

**回写 HLD / 后续规划**：`process/HLD-DATA-LAKE.md` §17.7.1、§17.7.2；`process/HLD.md` §30.3；后续 Story Plan 必须把 lake 写入者、DuckDB 只读消费者和 publish gate 拆成无文件冲突的职责边界。

## 设计确认点（需人工确认）

| ID | 确认点 | 默认规划 | 影响范围 | 状态 |
|---|---|---|---|---|
| AD-Q1 | 是否接受 Story 计划采用 13 个 Story、5 个 Wave | 接受，5 个 Wave 对齐 HLD M0-M4，13 个 Story 落在 HLD §18 的 10-15 个工作包范围 | Backlog、Development Plan、后续 LLD 顺序 | OPEN |
| AD-Q2 | 是否接受 M3 真实性增强和 M4 策略扩展纳入本计划但保持 draft、非第一版主路径阻塞项 | 接受，M0-M2 是第一版本地主路径，M3/M4 为后续增强 | Story 优先级、验收节奏 | OPEN |
| AD-Q3 | 是否接受本轮不生成 `PLATFORM-INSTALL-SPEC.md` | 接受，因本轮交接文件和用户指令的允许输出不包含该文件，且禁止生成安装脚本 / 写入 `delivery/**` | story-planning 输出范围 | OPEN |
| AD-Q4 | 是否接受 CR-004 将 `market_data/` 作为独立可迁移包而非直接重构 `engine/` | 默认接受；首轮新增包，旧 `engine/` 不被删除 | HLD §21、STORY-014..018、后续迁移顺序 | OPEN |
| AD-Q5 | 是否接受真实 TickFlow/AkShare/Tushare 默认关闭，fake/offline 为唯一默认测试路径 | 默认接受；真实 adapter 只做边界和 fail-fast | 安全边界、测试策略、CLI 默认行为 | OPEN |
| AD-Q6 | 是否接受真实沪深 300 基准先作为只读 gold/canonical 数据集接入 | 默认接受；实验入口不联网 | STORY-018、实验十/十二报告解释 | OPEN |
| AD-Q7 | 是否接受 CR-005 将 Tushare 真实调用限制为本地写湖链路 | 默认接受；Data Loader、实验、Backtrader 均不得直接调用 Tushare | HLD §22、CR005-S01..S06 | OPEN |
| AD-Q8 | 是否接受 Backtrader 并入 CR-005 且仅作为 optional backend | 默认接受；不新建 CR-006，不替代 `engine/backtest.py` | ADR-016、CR005-S06、pyproject 后续 CP5 | OPEN |
| AD-Q9 | 是否接受 CR005-S06 晚于 dataset schema 与 quality/readers 稳定进入开发 | 默认接受；CR005-S06 依赖 CR005-S02/S03/S04 | DEVELOPMENT-PLAN.yaml、Backlog、CP5 批次 | OPEN |
| AD-Q10 | 是否接受 PIT 与复权统一前置在 Pandas 数据层，Backtrader 不承担数据清洗职责 | 默认接受；Backtrader 只消费干净 feed 并只负责交易模拟与风险分析 | ADR-017、CR005-S02/S03/S06 | OPEN |
| AD-Q11 | 是否接受 `required_missing` 只生成 remediation spec，不由消费层自动联网或补数 | 默认接受；数据层 job 需用户显式执行 | ADR-013、ADR-015、CR005-S01/S04/S06 | OPEN |
| AD-Q12 | 是否接受旧代理基准只能命名为 `proxy_baseline`，不得填充 hs300 benchmark 字段 | 默认接受；缺真实 `hs300_index` 时不声明 hs300 相对收益 | ADR-015、CR005-S04/S06 | OPEN |
| AD-Q13 | 是否接受 CR-006 新链路以 Tushare structured lake 为事实源，不承诺覆盖旧 `data/` | 默认接受；旧 `data/` reference-only | ADR-018、CR006-S01、CR006-S04 | OPEN |
| AD-Q14 | 是否接受 raw/manifest 需要保留，但只用于采集审计、复现和质量追溯，不作为回测运行时输入 | 默认接受；运行时只读 canonical/gold/feed | ADR-018、CR006-S01、CR006-S02、CR006-S03 | OPEN |
| AD-Q15 | 是否接受轻量 engine 只消费 canonical/gold 或外置派生 `legacy_flat`，不默认 fallback 到 repo `data/` | 默认接受；旧 `data/` 不证明新链路可用 | ADR-018、CR006-S02、CR006-S04 | OPEN |
| AD-Q16 | 是否接受 Backtrader 只消费 quality gate 后 clean feed，且不读取 raw/manifest/token/connector | 默认接受；Backtrader 仍是 optional backend | ADR-018、ADR-016、ADR-017、CR006-S03 | OPEN |
| AD-Q17 | 是否接受 CR-007 长周期 backfill 先交付分批 planner、resume 和 coverage gate，真实抓取另行授权 | 默认接受；dry-run 网络调用和写入均为 0 | ADR-019、CR007-S01 | OPEN |
| AD-Q18 | 是否接受真实沪深300 benchmark 必须由 `hs300_index` 与 `trade_calendar` 同区间 coverage 支撑，代理只能为 `proxy_baseline` | 默认接受；缺口返回 required_missing | ADR-020、CR007-S02、CR007-S04 | OPEN |
| AD-Q19 | 是否接受 `index_members` / `index_weights` / `stock_basic` readiness 和 PIT 状态显式化，不完整时不得伪装 PIT available | 默认接受；structured warn/unavailable | ADR-021、CR007-S03 | OPEN |
| AD-Q20 | 是否接受旧 `reports/data_quality_report.csv` 仅作 legacy，当前质量真相源为 lake `quality/catalog` | 默认接受；不覆盖旧报告 | ADR-022、CR007-S05 | OPEN |
| AD-Q21 | 是否接受 `research_input_v1` 作为 CR008 后新研究报告的唯一研究输入 metadata 合同 | 默认接受；历史报告保留 legacy，新报告必须写 coverage、benchmark、universe、adjustment、label window、quality/readiness 和 limitations | ADR-024、CR008-S01 | OPEN |
| AD-Q22 | 是否接受 proxy benchmark 与真实 `hs300_index` 字段强隔离 | 默认接受；缺真实 benchmark 时真实 `hs300_*` 输出次数为 0，只允许 `proxy_*` / `proxy_baseline` | ADR-025、CR008-S02、CR007-S04 | OPEN |
| AD-Q23 | 是否接受 `research_dataset_builder` 只读 canonical/gold，不触发 fetch/backfill | 默认接受；builder 不导入 connector/runtime/storage，不读取旧 `data/**` 或旧质量报告 | ADR-026、CR008-S03 | OPEN |
| AD-Q24 | 是否接受严肃研究必须 PIT universe，fixed snapshot 只允许探索并披露幸存者偏差 | 默认接受；`universe_mode`、`pit_status`、`is_pit_universe` 必填 | ADR-027、CR008-S05、CR007-S03 | OPEN |
| AD-Q25 | 是否接受 quality / adjustment / label window gate 作为研究准入硬门 | 默认接受；quality fail、复权混用、label window 不足在严肃研究中 fail | ADR-028、CR008-S04 | OPEN |
| AD-Q26 | 是否接受因子辅助数据缺失时禁止对应严肃结论 | 默认接受；无行业/市值/可交易性/风格暴露时不得声明中性化、真实可成交或纯 alpha | ADR-029、CR008-S06 | OPEN |
| AD-Q27 | 是否接受 CR-010 拆出生产级数据湖 companion HLD | 默认接受；主 HLD 仅保留只读消费契约 | ADR-030、CR010-S01..S12 | OPEN |
| AD-Q28 | 是否接受 consumer 只读已 publish 的 catalog/canonical/gold | 默认接受；缺口只返回 remediation spec，consumer 网络调用为 0 | ADR-031、CR010-S10..S12 | OPEN |
| AD-Q29 | 是否接受日频价格 T 日 close 仅在 T 日收盘后可见，开盘前只能用 T-1 数据 | 用户已确认 D11；本轮要求写入 `available_at_rule` 并用于 gate | ADR-032、CR010-S02/S10 | RESOLVED：2026-05-22 用户确认 |
| AD-Q30 | 是否接受 W3 未确认 source/interface 前 fail-fast | 默认接受；PIT / trade_status / prices_limit / events 不伪造可用 | ADR-033、CR010-S06..S09 | OPEN |
| AD-Q31 | 是否接受 validate 不自动成为 current truth，必须显式 publish | 默认接受；`quality_status=fail` 阻断 publish 和 production_strict | ADR-034、CR010-S01/S05 | OPEN |
| AD-Q32 | 是否接受真实回补小窗口 -> 1 年 -> 全历史逐级授权 | 默认接受；当前任务不授权真实联网或真实 lake 写入 | ADR-035、CR010-S01..S05 | OPEN |
| AD-Q33 | 是否接受 CR-011 旧实验 17-21 报告只作为 fixed/proxy/close baseline，不被新版报告覆盖 | 默认接受；新版报告必须版本化输出，旧报告只作为追溯基线 | ADR-043、CR011-S08 | OPEN |
| AD-Q34 | 是否接受真实 benchmark policy 缺失时 production_strict fail，proxy 只能写 `proxy_*` | 默认接受；proxy 写入 `hs300_*` 次数必须为 0 | ADR-036、CR011-S01 | OPEN |
| AD-Q35 | 是否接受严肃因子研究必须 PIT universe，fixed snapshot 只能 exploratory | 默认接受；`index_weights` / `stock_basic` 不替代完整 membership | ADR-037、CR011-S02 | OPEN |
| AD-Q36 | 是否接受停牌、涨跌停、ST、无成交、上市天数、事件状态六类 tradability gate 作为真实可交易声明前置 | 默认接受；缺任一 P0 gate 时 production_strict fail | ADR-038、CR011-S03 | OPEN |
| AD-Q37 | 是否接受 open/VWAP 缺失时只能显式 `close_proxy` 降级，且阻断 VWAP / 真实成交声明 | 默认接受；`execution_degradation_reason` 必填 | ADR-039、CR011-S04 | OPEN |
| AD-Q38 | 是否接受 adj_factor lineage 与 corporate action audit 分层声明 | 默认接受；缺公司行动时只声明已使用复权价格，不声明完整公司行动审计 | ADR-040、CR011-S05 | OPEN |
| AD-Q39 | 是否接受行业、市值、风格 exposure 缺失时阻断中性化、pure alpha 和容量相关严肃结论 | 默认接受；当前快照不能支撑 PIT exposure | ADR-041、CR011-S06 | OPEN |
| AD-Q40 | 是否接受 CR-011 采用三个 CP5 批次并在每批次全量 LLD 确认前不得实现 | 默认接受：`CR011-DATA-BATCH-A`、`CR011-RESEARCH-BATCH-B`、`CR011-VALIDATION-BATCH-C` | ADR-036..043、CR011-S01..S08 | OPEN |
| AD-Q41 | 是否接受 CR-012 limited-window pass 不得外推到 `2020-01-01..2024-12-31` | 默认接受；full-history 保持 `research_limited_only` / blocked，直到 10 个正式 dataset 全部补齐并新审计通过 | ADR-044、CR013-S01 | OPEN |
| AD-Q42 | 是否接受真实 VWAP、VWAP fill、分钟 / 逐笔 / 盘口 / 撮合执行价在本轮继续 blocked | 默认接受；close proxy 只能作为研究降级，不得派生真实 VWAP claim | ADR-045、CR013-S02 | OPEN |
| AD-Q43 | 是否接受 unsupported register 9 行作为正式声明边界输入且 `pass_denominator=excluded` 不计入 pass 分母 | 默认接受；research-only / unsupported / contract-supported-but-unavailable 均进入 report/docs 声明 | ADR-046、CR013-S03 | OPEN |
| AD-Q44 | 是否接受 CR013-S04 只制定 full-history backfill roadmap，不授权 provider/lake/credential/old data 操作 | 默认接受；真实补数或 VWAP/分钟数据接入必须另起 Story / CP5 并由用户显式授权 | ADR-047、CR013-S04 | OPEN |
| AD-Q45 | 是否接受 CR-014 继续以 Parquet lake + catalog/manifest 作为 source of truth | 默认接受；DuckDB query、quality report 或 SQL view 不自动成为 current truth | ADR-048、HLD-DATA-LAKE §17 | OPEN |
| AD-Q46 | 是否接受 DuckDB 只作为 read-only query / audit / feature extraction 候选 | 默认接受；CP3/CP5 前不改依赖、不写 `.duckdb` 事实源，失败时回退 pandas/pyarrow audit | ADR-049、HLD-DATA-LAKE §17.6 | OPEN |
| AD-Q47 | 是否接受全 A since-inception current truth 必须以前 A universe、最近已闭市交易日、lifecycle/code-change 和 catalog current pointer 为前置 | 默认接受；缺字段进入 `required_missing` / `blocked_claims`，allowed full-A claim 为 0 | ADR-050、REQ-088..REQ-097 | OPEN |
| AD-Q48 | 是否接受 CR-014 HLD/ADR 通过不等于真实执行授权 | 默认接受；provider fetch、lake write、credential read、旧 data 操作、旧 reports 覆盖和依赖修改均需后续 Story / CP5 / 用户显式授权 | ADR-051、HLD-DATA-LAKE §17.13 | OPEN |
| AD-Q49 | 是否接受 DuckDB read-only 与 lake pipeline 写入并存 | 默认接受；CP5 + 用户显式授权后由 Provider Adapter / Run Gate 写 raw/manifest/run metadata，Normalize/Replay/Validate 只生成 candidate/evidence，Explicit Publish Gate 才更新 catalog current pointer，DuckDB 只读 published 或受控 candidate audit | ADR-052、HLD-DATA-LAKE §17.7.1 | OPEN |

## 变更记录

| 日期 | 变更 | 原因 | 影响 |
|---|---|---|---|
| 2026-05-14 | 从 HLD §15 收敛 ADR-001 至 ADR-007 | HLD 已人工确认，进入 story-planning | 为 Story 边界、Wave 依赖和 LLD 输入提供正式决策 |
| 2026-05-17 | 按 CR-004 增量追加 ADR-008 至 ADR-012 | 用户批准可迁移市场数据组件变更 | 需要重开 CP3/CP4；未经确认不得进入 CR-004 实现 |
| 2026-05-17 | 按 CR-005 增量追加 ADR-013 至 ADR-016 | 用户提出 Tushare 5000 数据层整改并要求 Backtrader 并入同一 CR | 需要重开 CP3/CP4；未经确认不得实现真实 Tushare 调用、Backtrader adapter 或依赖变更 |
| 2026-05-17 | 按 CR-005 追加修改点新增 ADR-017 并修订 ADR-014/016 | 用户要求明确 PIT、复权、Pandas 数据层和 Backtrader 职责边界 | meta-po 需要重跑 CP3/CP4 自动预检与人工审查稿；未经确认不得进入 CR005-S06 CP5/实现 |
| 2026-05-17 | 按 CR-005 第三轮评审修订 ADR-013/015/017 | 第三轮评审要求补齐 `hs300_index` 缺失到 Tushare backfill 的两步契约、typed schema、质量门与 dev_gate | 原 CP3/CP4 旧稿 superseded；meta-po 需重跑 CP3/CP4，CR005-S04/S06 不得在 required contracts 冻结前进入开发 |
| 2026-05-18 | 按 CR-006 新增 ADR-018 | 用户批准 legacy `data/` 外置化组织分析结论，要求进入 solution-design 修订链路 | 需要发起 CR-006 CP3/CP4；未经确认不得进入 CR006-BATCH-A LLD，不得修改 engine/experiments/config/README/docs/tests 或真实数据 |
| 2026-05-18 | 按 CR-006 CP3 前修改意见重写 ADR-018 | 用户明确旧 `data/` 不删除但放弃默认使用，要求以 Tushare 数据为主并评估 raw/manifest 与回测框架关系 | 需要重新生成 CR-006 CP3/CP4 自动预检；原 CP3 人工稿不得直接 approved，应由 meta-po 重发人工确认 |
| 2026-05-20 | 按 CR-007 新增 ADR-019 至 ADR-022 | 用户确认 canonical 数据湖长期覆盖、真实 benchmark、交易日历、成分/权重/stock_basic 和旧质量报告仍存在缺口 | 需要发起 CR-007 CP3/CP4；未经确认不得进入 CR007-BATCH-A LLD，不得真实 Tushare 抓取、真实 lake 写入、旧 `data/**` 操作或凭据读取 |
| 2026-05-20 | 新增回测平台演进路线与 ADR-023 | 用户确认将演进方向落盘 | `docs/ROADMAP.md` 成为长期路线入口；README 只保留摘要和链接；开源框架按 optional backend / accelerator 集成，不替代当前主干 |
| 2026-05-21 | 按 CR-008 新增 ADR-024 至 ADR-029 | 用户要求将研究级数据层口径硬化纳入开发计划，且 CR007/CR008 冲突时以 CR008 为主 | 需要发起 CR-008 CP3/CP4；未经确认不得进入 CR008-BATCH-A LLD，不得实现 CR008，不得真实抓取、真实 lake 写入、旧数据/旧报告操作或凭据读取 |
| 2026-05-22 | 按 CR-010 新增 ADR-030 至 ADR-035 | 用户要求数据湖生产化与回测真实性提升，且计划明确 companion HLD、publish gate、W3 fail-fast 与分阶段真实回补 | 需要发起 CR-010 CP3/CP4；未经确认不得进入 CR010 LLD 批次或真实复验；当前实现只允许离线 / fixture / tmp lake |
| 2026-05-23 | 按 CR-011 新增 ADR-036 至 ADR-043，并补齐 Story Plan 确认点 AD-Q33..AD-Q40 | 用户批准 CR-011 因子研究生产级数据补齐，要求补齐 Story Plan 层但不进入 LLD 或代码实现 | 需要由 meta-po 发起 CR-011 CP3/CP4；CP4 通过后才能进入 `CR011-DATA-BATCH-A` / `CR011-RESEARCH-BATCH-B` / `CR011-VALIDATION-BATCH-C` 全量 LLD；CP5 批次确认前不得实现 |
| 2026-05-25 | 按 CR-013 新增 ADR-044 至 ADR-047，并补齐 Story Plan 确认点 AD-Q41..AD-Q44 | 用户批准 CR-013 unsupported data 与 claim boundary 分析实现意图，要求先收敛 HLD / ADR / Story Plan 边界 | 需要由 meta-po 发起 CR-013 CP3 人工审查，并将 CP4 自动预检摘要汇入后续 CP5；CP5 全量 LLD 确认前不得实现，不授权 provider fetch、真实 lake 写入、凭据读取、旧 data 读取或旧报告覆盖 |
| 2026-05-26 | 按 CR-014 新增 ADR-048 至 ADR-051，并补齐设计确认点 AD-Q45..AD-Q48 | 用户已批准 CR-014 CP2 需求基线，要求在 CP3 前输出全 A since-inception 数据湖 HLD / ADR 增量和自动预检 | 需要由 meta-po 发起 CR-014 CP3 人工审查；CP3 approve 前不得拆 Story、写 LLD 或实现；本轮不授权 provider fetch、真实 lake 写入、凭据读取、旧 data 操作、旧 reports 覆盖或 DuckDB 依赖修改 |
| 2026-05-26 | 按 CR-014 CP3 R2 修改意见新增 ADR-052 和 AD-Q49 | 用户要求解释 DuckDB 只读时数据何时写入，并组织讨论方案可行性、易用性和扩展性 | 需要由 meta-po 重新发起 CP3 R2；CP3 R2 approve 前仍不得拆 Story、写 LLD 或实现；真实写入仍需 CP5 + 用户显式授权 |
