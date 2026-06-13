---
complexity: "standard"
confirmed: false
confirmed_by: ""
confirmed_at: ""
source_hld: "process/HLD.md"
source_hld_version: "3.0"
story_plan_status: "cr020-story-plan-cp4-pass-pending-lld"
created_at: "2026-05-14"
created_by: "meta-se"
active_change: "CR-020"
secondary_change: "CR-030"
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
cr015_revision_status: "draft-pending-cp3"
cr015_adr_range: "ADR-055..058"
cr015_confirmed: false
cr016_revision_status: "draft-pending-cp3"
cr016_adr_range: "ADR-059..061"
cr016_confirmed: false
cr017_revision_status: "draft-pending-cp3"
cr017_adr_range: "ADR-053..054"
cr017_confirmed: false
cr018_revision_status: "draft-pending-cp3"
cr018_adr_range: "ADR-062..066"
cr018_confirmed: false
cr019_revision_status: "draft-pending-cp3"
cr019_adr_range: "ADR-067..073"
cr019_confirmed: false
cr025_revision_status: "draft-pending-cp3"
cr025_adr_range: "ADR-074..078"
cr025_confirmed: false
cr030_revision_status: "story-plan-cp4-pass-pending-lld"
cr030_adr_range: "ADR-079..086"
cr030_confirmed: false
cr020_revision_status: "story-plan-cp4-pass-pending-lld"
cr020_adr_range: "ADR-087..093"
cr020_confirmed: false
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
| 1.7 | 2026-05-27 | meta-se | 按 CR-015 / CR-016 / CR-017 新增 ADR-053 至 ADR-061：冻结复权公式 / view schema、QMT adapter / OMS / broker lake / risk / stage gate / limit-protect / reconciliation / kill switch / cross-node deployment 决策；本增量待 CP3 确认，不授权 Story Plan、LLD、代码实现或真实交易操作 |
| 1.8 | 2026-05-29 | meta-se | 按 CR-018 新增 ADR-062 至 ADR-066：冻结 current truth scoped release、P0/P1 dataset priority、四类 benchmark group、release-level publish / rollback、published truth research rerun 与 QMT 后置；D1-D6 已由 CP2 approved，本增量待 CP3 确认 |
| 1.9 | 2026-05-30 | meta-se | 按 CR-019 新增 ADR-067 至 ADR-073：冻结阶段六 admission + 多基准 primary benchmark、QMT C/S bridge 主选、C 侧 Python client / 薄 CLI、完整 endpoint matrix 与运行门控分离、局域网无鉴权 / 可选 token-HMAC、fallback 和 Backtrader/Qlib/minute/Level2 后置；本增量待 CP3 确认，不授权代码实现、依赖变更、真实 QMT / provider / lake / broker 操作 |
| 1.9.1 | 2026-05-30 | meta-se | 按 CR-019 CP3 DQ-04 用户修订更新 ADR-071 与 AD-Q68：配对式 token/HMAC 默认启用，no-auth 仅限本机 debug / fixture / 显式临时模式；pairing 和 HMAC 只解决调用方识别，不替代 run mode、stage gate、risk gate、kill-switch 和 per-run authorization |
| 2.0 | 2026-06-01 | meta-se | 按 CR-025 新增 ADR-074 至 ADR-077：冻结 Backtrader optional semantic reference 默认定位、模块级 reference/adapt/exclude 分类、GPLv3 源码级移植治理和 order intent draft / QMT 边界；本增量待 CP3 确认，不授权实现、依赖变更、Backtrader 运行、源码复制 / 移植、真实 broker / QMT / provider / lake / publish / simulation / live 或凭据读取 |
| 2.0.1 | 2026-06-02 | meta-se | 按 CR-025 CP5 前定位澄清新增 ADR-078，并修订 ADR-074 / ADR-075：确认 Backtrader 只作为 execution semantic reference；多因子研究闭环（FactorSpec、FactorRunSpec、IC / RankIC、分层收益、多因子组合、实验追踪、策略准入包）另起后续 CR，参考 Qlib / Alphalens / vnpy.alpha，不并入 CR-025 |
| 2.1 | 2026-06-03 | meta-se | 按 CR-030 CP3 approved 口径新增 ADR-079 至 ADR-086：冻结项目自有多因子研究闭环、外部项目 reference / optional Spike / exclude / forbidden migration 矩阵、schema provenance、FactorPanel / LabelWindow fail-closed、P0 可解释组合、manifest/catalog、StrategyAdmissionPackage draft handoff 和 CR-026 后置；本增量用于 CP4 Story Plan，不授权实现、依赖变更、外部项目运行、provider/lake/publish、QMT/simulation/live 或凭据读取 |
| 2.2 | 2026-06-05 | meta-se | 按 CR-020 CP3 approved 口径新增 ADR-087 至 ADR-093：冻结 Windows gateway runtime 分层、gateway 唯一 QMT 服务端触达点、`.env` redacted credential_ref、QMT login/session ready gate、HMAC / allowlist / scope / nonce fail-closed、`query_positions` 单接口只读准入和 S 端依赖隔离；本增量用于 CP4 Story Plan，不授权 LLD、实现、依赖变更、gateway 启动、QMT 连接、真实 `.env` 读取、交易、账户写入、simulation/live、provider/lake/publish 或凭据输出 |

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
| CR-017 复权双视图 | `process/HLD-DATA-LAKE.md` §18 拥有 `prices_raw`、`adj_factor`、`prices_qfq`、`prices_hfq`、`returns_adjusted`、qfq as-of、旧 qfq 兼容和 QMT raw 执行价边界；主 HLD 只消费 view metadata | CP3 通过后再拆解，不在本轮生成 Story |
| CR-015 QMT foundation | `process/HLD-QMT-TRADING.md` 拥有 Windows QMT 节点、OMS、QMT adapter、pre-trade hard risk、broker lake 和 shadow / dry-run / mock foundation；策略层不得直连 QMT | CP3 通过后再拆解，不在本轮生成 Story |
| CR-016 QMT activation / ops | `process/HLD-QMT-TRADING.md` 拥有 stage gate、runbook、per-run 授权、T+1 限价 / 保护价、对账、kill switch 和资金放大 gate；真实操作仍需 per-run 授权 | CP3 通过后再拆解，不在本轮生成 Story |
| CR-018 production data lake closure | `process/HLD-DATA-LAKE.md` §19 拥有 release scope、P0/P1 dataset group、benchmark group、Explicit Publish Gate、rollback；主 HLD §32 只同步 research rerun 和 QMT admission | CP3 通过后 CR018-S01..S09 可进入 CP4 / CP5；真实 fetch / write / publish / QMT 仍需后续授权 |
| CR-019 stage6 admission / QMT C/S bridge | 主 HLD §33 同步阶段六 admission、C 侧调用边界、完整 endpoint matrix 与运行门控；`process/HLD-QMT-TRADING.md` §17 拥有 Windows FastAPI gateway、bind/firewall/auth/fallback 与 QMT adapter 衔接 | CP3 通过后才可进入 Story Plan；真实 service、QMT、provider、lake、broker 操作仍需 CP5 / per-run 授权 |

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

## ADR-053：CR-017 复权公式、provider 因子方向、as-of 与异常价格解释

**状态**：Draft for CR-015/016/017 CP3 review

**决策**：CR-017 采用 `prices_raw` + `adj_factor` 作为复权事实源，并在 HLD/ADR 阶段冻结公式方向、provider 因子解释、qfq `as_of_trade_date` 和异常价格质量门。推荐公式口径为：qfq 以 `as_of_trade_date` 为锚点，表达为 `raw_price * adj_factor(trade_date) / adj_factor(as_of_trade_date)`；hfq 以 provider/base date 为锚点，表达为 `raw_price * adj_factor(trade_date) / adj_factor(base_date)`。若 provider 因子方向相反，必须通过 `provider_factor_direction` 显式映射，禁止实现层隐式猜测。

**理由**：落实 Q-030、REQ-098 至 REQ-100、RA-034。复权公式方向错误会污染全部 qfq/hfq 派生视图；qfq 缺 as-of 会让历史价格漂移不可审计；异常价格未解释会让研究和 QMT raw price 边界失真。

**接受影响**：

- 后续 LLD 必须把 provider 字段解释、样例 parity、as-of metadata 和异常价格阈值作为强输入。
- qfq/hfq 派生在字段方向未确认时必须 fail-fast，不能先写入生产 view。
- QMT 交易层可依赖 raw / broker price，不依赖 qfq/hfq 执行价。

**不接受影响**：

- qfq/hfq 方向可能写反，且错误会批量污染研究结论。
- qfq 历史价格随未来因子变化而不可解释。
- CP3 无法批准后续复权派生 Story。

**备选方案**：

| 方案 | 优点 | 缺点 | 结论 |
|---|---|---|---|
| 只先支持 qfq，hfq 后置 | 范围小 | 不满足用户已确认的前复权 + 后复权双视图目标 | 不采用 |
| 只保存 provider 成品 qfq/hfq | 实现短 | raw 和因子链路弱，无法解释重算和异常 | 不采用 |

**回退点**：若 CP3 不接受本 ADR，回退到 CR-017 问题定义，重新确认 provider 因子方向和 qfq/hfq 是否同时进入本轮。

## ADR-054：CR-017 dataset / view schema、旧 qfq 兼容入口和迁移策略

**状态**：Draft for CR-015/016/017 CP3 review

**决策**：CR-017 采用独立 dataset / view：`prices_raw`、`adj_factor`、`prices_qfq`、`prices_hfq`、`returns_adjusted`。每个 view 必须有 `view_id`、`schema_version`、`derivation_version`、`source_run_id`、`lineage_checksum` 和 `quality_status`。旧 qfq 默认口径和旧报告作为历史基线只读保留；迁移只输出 `legacy_qfq_baseline_preserved=true`、旧基线引用、兼容入口、禁止覆盖声明和后续 CP5 条件。

**理由**：落实 Q-031、REQ-099、REQ-101、REQ-103。独立 view 可以维持现有单口径 gate，避免同一个 frame 混用 raw/qfq/hfq；旧 qfq 基线必须保留以支撑追溯。

**接受影响**：

- reader API 和报告 metadata 必须显式选择单一 `research_adjustment_policy`。
- 旧 qfq 数据不被覆盖；迁移需要额外 summary。
- QMT 只消费 raw / broker price，qfq/hfq 只作为 research metadata。

**不接受影响**：

- 单表混存会导致消费方误读和混用。
- 覆盖旧 qfq 会破坏旧报告追溯。
- 后续 Story 无法清晰划分数据湖 view 文件所有权。

**备选方案**：

| 方案 | 优点 | 缺点 | 结论 |
|---|---|---|---|
| 单 `prices` 表按 `adjustment_policy` 分区混存 | 路径少 | 混用风险高，破坏 single-policy gate | 不采用 |
| 直接覆盖旧 qfq 为新 qfq view | 迁移表面简单 | 旧报告不可追溯，审计风险高 | 不采用 |

**回退点**：若 CP3 不接受本 ADR，回退到 CR-017 schema 问题，重新定义 view id、兼容入口和 migration 范围。

## ADR-055：QMT 接入采用 Windows QMT 节点 + OMS + adapter，策略不得直连 QMT

**状态**：Draft for CR-015/016/017 CP3 review

**决策**：CR-015 QMT 接入采用 Linux 研究节点与 Windows QMT / MiniQMT 交易节点解耦的方式。策略层只输出 target portfolio / order intent metadata，不导入或调用 QMT / XtQuant 下单接口；所有 broker 触达必须经过 OMS、pre-trade risk 和 QMT adapter。Adapter 位于 Windows 节点，是唯一 QMT / XtQuant API 触达点。

**理由**：落实 Q-038、REQ-105、RA-035。直接让策略调用 QMT API 会绕过风控、状态机、审计和授权边界。

**接受影响**：

- 后续 Story 必须包含策略层 forbidden import / no direct call 验证。
- adapter contract、连接管理和跨节点通信成为 QMT foundation 必需设计。
- 模拟盘和实盘入口可以统一经过 stage gate 和 per-run authorization。

**不接受影响**：

- 策略可能绕过 OMS / risk 直接下单。
- 订单状态、broker event 和对账无法统一复盘。
- 凭据与账户信息泄露风险上升。

**备选方案**：

| 方案 | 优点 | 缺点 | 结论 |
|---|---|---|---|
| 策略直接调用 QMT API | 起步快 | 绕过风控和审计，误下单风险高 | 不采用 |
| 迁移到完整第三方交易平台 | 能力完整 | 打散现有研究 / 数据湖资产，成本过高 | 暂不采用 |

**回退点**：若 CP3 不接受本 ADR，回退到 CR-015 QMT 接入方式问题，重新确认是否仍推进 QMT foundation。

## ADR-056：broker lake 外置、schema、retention、redaction 与研究数据湖隔离

**状态**：Draft for CR-015/016/017 CP3 review

**决策**：CR-015 broker lake 必须外置，不写仓库 `data/**` / `reports/**`。推荐 root 为 `BROKER_LAKE_ROOT` 或等价受控配置；schema 覆盖 `order_intent`、`broker_order`、`fill`、`position`、`asset`、`error`、`reconciliation`、`incident`；默认 retention 为 3 年或用户配置；敏感字段通过 redaction gate 脱敏 / 禁入库，只允许保留 env var 名称、脱敏账户标签、run_id、strategy_id、root label 和 schema_version。

**理由**：落实 Q-032、REQ-108、REQ-111、RA-036。交易事实与研究数据湖生命周期、权限和敏感程度不同，必须隔离。

**接受影响**：

- 后续 LLD 必须定义 broker lake schema_version、partition、retention_policy 和 redaction_status。
- 未授权真实写入时只能生成 dry-run / mock 审计或写入计划。
- README / runbook 后续必须说明 broker lake 与 market data lake 的边界。

**不接受影响**：

- 只依赖 QMT 本地日志会导致策略级复盘和对账困难。
- 写入仓库会增加凭据、账户和真实交易事实泄露风险。
- broker lake 与研究数据湖混写会破坏权限和保留策略。

**备选方案**：

| 方案 | 优点 | 缺点 | 结论 |
|---|---|---|---|
| 只依赖 QMT 本地日志 | 实现少 | 不可控、不可复盘，难以测试 | 不采用 |
| 写入仓库 `data/**` / `reports/**` | 路径熟悉 | 敏感信息和真实交易事实入库风险高 | 禁止 |

**回退点**：若 CP3 不接受本 ADR，回退到 broker lake root / schema / retention / redaction 问题。

## ADR-057：OMS 状态机和 QMT / mock event 映射

**状态**：Draft for CR-015/016/017 CP3 review

**决策**：OMS 必须实现本地订单状态机，覆盖 `created`、`risk_passed`、`blocked`、`accepted`、`partially_filled`、`filled`、`cancel_pending`、`canceled`、`rejected`、`failed`、`timeout`、`unknown`、`manual_review`、`frozen`。QMT / mock adapter event 必须映射到状态迁移；unknown / timeout 不得静默当作成功或失败，必须进入 reconciliation 或 manual_review；撤单失败不重复无限撤单。

**理由**：落实 Q-033、REQ-107、REQ-116、RA-037。QMT 返回、网络异常和部分成交都可能产生不确定状态，没有本地状态机就无法防重复下单和复盘。

**接受影响**：

- mock broker fixtures 必须覆盖 partial fill、reject、cancel、unknown、timeout。
- 后续对账服务必须能读取 OMS local state 和 broker lake facts。
- 状态机 LLD 需要明确终态、非终态、人工介入和 retry 上限。

**不接受影响**：

- unknown 被误判为 filled 后可能重复下单或错误持仓。
- partial fill 处理不完整会导致目标仓位偏离。
- timeout 后无限重试会扩大风险。

**备选方案**：

| 方案 | 优点 | 缺点 | 结论 |
|---|---|---|---|
| 简化为 submitted / filled / failed 三态 | 实现简单 | 覆盖不了部分成交、撤单、unknown、timeout | 不采用 |
| 直接以 QMT 日志为状态真相 | 少写状态机 | 本地无法统一风控、对账和恢复 | 不采用 |

**回退点**：若 CP3 不接受本 ADR，回退到 OMS 状态机问题，重新定义交易状态边界。

## ADR-058：pre-trade hard risk gate 规则、阈值、配置位置和失败行为

**状态**：Draft for CR-015/016/017 CP3 review

**决策**：pre-trade risk 必须为 hard block，覆盖现金、100 股整手、T+1 可卖、可用持仓、价格口径、重复 intent、单票限额、组合限额和异常价格。风险配置写入交易配置 / run profile，后续 LLD 冻结 exact 路径；任一规则失败时 `adapter_calls=0`，blocked reason 和 rule_id 进入审计。

**理由**：落实 Q-034、REQ-109、REQ-110、RA-038。warn-only 风控在真实资金链路不可接受。

**接受影响**：

- 订单可能因配置过严而被阻断，但可解释、可复查。
- 后续 Story 必须提供 risk sample matrix 和 blocked reason enum。
- QMT adapter LLD 必须把 risk pass 作为唯一进入条件。

**不接受影响**：

- 风控失败仍可能触达 broker API。
- qfq/hfq 价格可能进入真实委托。
- 重复 intent 或现金不足会变成真实资金风险。

**备选方案**：

| 方案 | 优点 | 缺点 | 结论 |
|---|---|---|---|
| warn-only | 不影响成交 | 实盘风险不可接受 | 不采用 |
| 只依赖 QMT 返回校验 | 实现少 | 错误已触达 broker，无法满足 hard block | 不采用 |

**回退点**：若 CP3 不接受本 ADR，回退到 pre-trade risk 清单和阈值问题。

## ADR-059：QMT staged activation 准入、退出和回退阈值

**状态**：Draft for CR-015/016/017 CP3 review

**决策**：CR-016 阶段路径固定为 `shadow -> simulation -> live_readonly -> small_live -> scale_up`，不可跳过。每阶段必须输出准入条件、退出结果、观察窗口、失败阈值、回退条件和 blocked reason。CR-017 不阻断技术模拟盘，但在复权双视图实现验证前阻断生产策略复权治理完成声明和资金放大。

**理由**：落实 Q-035、REQ-112、REQ-119、RA-039。交易链路验证与真实资金风险必须分层推进。

**接受影响**：

- 实盘推进周期变长，但每步可审计。
- simulation 可以先验证技术链路；scale_up 需要研究成熟度和 CR-017 实现验证。
- 后续 runbook 必须按阶段维护。

**不接受影响**：

- 模拟盘通过后直接实盘会缺少只读核对和小资金隔离。
- 长期只停留 shadow / simulation 会无法验证真实账户和对账压力。
- CR-017 未完成却放大资金会造成研究口径和执行价格声明风险。

**备选方案**：

| 方案 | 优点 | 缺点 | 结论 |
|---|---|---|---|
| simulation 后直接 small_live | 快 | 缺 live_readonly、异常演练和小资金前置核对 | 不采用 |
| 长期只做 shadow / simulation | 风险低 | 无法验证真实账户、成交和运行压力 | 仅作为降级 |

**回退点**：若 CP3 不接受本 ADR，回退到 CR-016 stage gate 问题。

## ADR-060：T+1 限价 / 保护价、撤单重试、对账阈值和 kill switch

**状态**：Draft for CR-015/016/017 CP3 review

**决策**：CR-016 默认执行策略为 T 日收盘后信号、T+1 限价 / 保护价执行；保护带以 raw close 或 broker reference price 的可配置百分比表达。超时未成交默认撤可撤单，单 run 自动重试次数上限为 1，未成交归因为 cash / unfilled。盘前 / 盘中 / 盘后对账覆盖委托、成交、持仓、资产、现金和 broker lake 事实；差异阈值可配置，超阈值进入 manual_review 或 kill switch。Kill switch 必须停止新单、撤可撤单、冻结策略、记录 incident 和恢复条件。

**理由**：落实 Q-036、Q-037、REQ-115 至 REQ-117、RA-040。执行策略、对账和事故控制必须一起设计，否则真实运行风险不可控。

**接受影响**：

- 成交率可能下降，但追单和滑点风险可控。
- 后续 LLD 必须定义保护带默认值、撤单时点、retry 上限、对账阈值和 owner。
- 运行报告必须记录 limit_protect_policy、recon status、kill_switch_events 和 manual_takeover_status。

**不接受影响**：

- 当日盘中即时下单可能引入未来数据和价格风险。
- 只盘后对账会导致盘中异常发现过晚。
- kill switch 只靠人工停止程序不可审计。

**备选方案**：

| 方案 | 优点 | 缺点 | 结论 |
|---|---|---|---|
| T+1 市价 / 即时成交 | 成交率高 | 价格风险和滑点风险高，当前无微观结构支持 | 不采用 |
| 只盘后对账 | 实现简单 | 盘中风险无法及时控制 | 不采用 |
| 只人工停止程序 | 简单 | 事故时不稳定、不可审计 | 不采用 |

**回退点**：若 CP3 不接受本 ADR，回退到 Q-036 / Q-037，重新确认执行策略和运行治理阈值。

## ADR-061：Linux 研究节点与 Windows QMT 节点通信、鉴权、隔离和运维责任

**状态**：Draft for CR-015/016/017 CP3 review

**决策**：研究系统与交易节点解耦。保守默认采用 signed file drop + ack/error enum 作为 Linux 研究节点到 Windows QMT 节点的通信方式；后续可在 CP5 后评估本地 RPC。Adapter 只部署在 Windows QMT / MiniQMT 节点；Linux 节点不直接执行 QMT API。运维责任分为 research owner、trading node owner、approver，runbook 必须记录部署、启动、异常、恢复和手工接管责任。

**CR-019 增量说明**：ADR-061 的“节点解耦、adapter 只在 Windows、Linux 不直连 QMT API、运维责任分层”继续有效；通信默认值由 ADR-068 修订为 QMT C/S bridge，即 local_backtest C 侧 Python client / 薄 CLI 通过 REST 调用 Windows FastAPI gateway。signed file drop 不再是主路径，降级为 ADR-072 定义的 blocked-only / 人工 dry-run fallback。

**理由**：落实 Q-038、REQ-105、REQ-111、REQ-113。跨节点通信同时影响安全、可审计性和运行失败降级，必须在 CP3 冻结默认策略。

**接受影响**：

- file drop 延迟较高，但更易审计、权限更小。
- RPC 如需启用，必须后续补鉴权、重放防护、timeout 和审计。
- Windows 节点运维和 QMT session 状态进入 runbook。

**不接受影响**：

- Linux 直接远程调用 Windows QMT API 会扩大凭据和误操作风险。
- 全部迁到 Windows 会打散研究 / 数据湖资产。
- 运维责任不清会导致异常时无人接管。

**备选方案**：

| 方案 | 优点 | 缺点 | 结论 |
|---|---|---|---|
| Linux 直接远程调用 QMT API | 少一层投递 | 凭据和权限风险高，审计弱 | 不采用 |
| 全部迁移到 Windows 单机 | 通信简单 | 打散研究环境和数据湖边界 | 不采用 |
| 直接使用本地 RPC 为默认 | 交互性好 | 鉴权和运行时风险更高 | 后续评估 |

**回退点**：若 CP3 不接受本 ADR，回退到 Q-038，重新确认跨节点部署和通信策略。

## ADR-062：CR-018 current truth release scope 采用 scoped release

**状态**：Draft for CR-018 CP3 review

**决策**：CR-018 第一版 production current truth release scope 采用 `2015-01-05..latest_closed_trade_date` 的 scoped release。2015 年以前历史不纳入第一版 published current truth，必须在 release summary、readiness matrix、README / USER-MANUAL / research rerun report 中标记为 `blocked/future_backfill`，不得声明 since-inception 已关闭。

**理由**：CR-014 S14 已形成 2015-01-05 至 2026-05-28 的 `prices` / `adj_factor` candidate，可以作为生产闭环输入。若把 2015 年前也放入第一版，provider、生命周期和 benchmark 历史源风险显著上升，会推迟 current truth closure；若只发布 2026 YTD，研究重跑价值不足。

**接受影响**：

- `release_scope`、coverage denominator 和 blocked claims 必须全部体现 scoped release。
- 2015 年前研究或报告只能输出 future backfill / blocked，不得输出 production current truth allowed claim。
- CR018-S01 是所有下游 Story 的 contract 前置。

**不接受影响**：

- 若要求 since-inception 一次性关闭，需要新增历史源 Spike 和更长回补计划。
- 若只做 YTD，无法满足 publish 后研究重跑的样本深度。

**备选方案**：

| 方案 | 优点 | 缺点 | 结论 |
|---|---|---|---|
| since-inception 一次性关闭 | 声明最完整 | 周期长、provider 风险高、质量审计面大 | 后续 CR |
| 2026 YTD scoped release | 最快 | 研究重跑价值不足，不能支撑长期策略判断 | 不采用 |

**回写 HLD / Story**：`process/HLD-DATA-LAKE.md` §19.1、§19.2；CR018-S01。

**回退点**：若 CP3 不接受，回退到 AGA-CR018-01，重新界定 release scope。

## ADR-063：CR-018 P0/P1 dataset group 与声明边界

**状态**：Draft for CR-018 CP3 review

**决策**：CR-018 P0 dataset group 包含 `prices_raw`、`adj_factor`、`prices_qfq`、`prices_hfq`、`returns_adjusted`、`trade_calendar`、PIT universe / lifecycle / code-change、`trade_status`、`prices_limit` / ST / suspend，以及 ADR-064 定义的 benchmark group。行业、总市值、流通市值、beta、风格因子、ADV、turnover_rate、流动性、容量和冲击成本列为 P1；P1 缺失不阻断核心 current truth publish，但阻断行业中性、市值中性、纯 alpha、容量可交易、scale_up ready 和资金放大声明。

**理由**：P0 group 是 production current truth 的最小严肃研究分母，缺 PIT/W3/benchmark/复权派生会让研究和 QMT admission 继续携带关键偏差。P1 辅助数据对解释力和资金放大重要，但不是第一版 publish 的最小条件。

**接受影响**：

- P0 任一 required dataset 缺失时 release status 必须 blocked。
- P1 缺失必须进入 `blocked_claims`，不能在报告中被忽略。
- Story 拆分为 S01/S02/S03/S04/S05/S06，避免把所有数据域压进单个 Story。

**不接受影响**：

- core-only publish 会导致 PIT/W3/benchmark 仍缺失，无法严肃判断 QMT admission。
- data-rich 全量 P0 会显著拉长 publish 周期。

**备选方案**：

| 方案 | 优点 | 缺点 | 结论 |
|---|---|---|---|
| core only：prices_raw + adj_factor + trade_calendar | 快速 | 不能严肃研究，也不能支撑 QMT admission | 降级备选 |
| data-rich：P1 全部升 P0 | 声明能力强 | 交付慢，provider 风险高 | 条件备选 |

**回写 HLD / Story**：`process/HLD-DATA-LAKE.md` §19.3、§19.7、§19.8；CR018-S01、S02、S04、S05、S06。

**回退点**：若 CP3 不接受，回退到 AGA-CR018-02，重新划分 P0/P1。

## ADR-064：CR-018 benchmark group 覆盖四类宽基指数行情 / 成分 / 权重

**状态**：Draft for CR-018 CP3 review

**决策**：CR-018 benchmark group 默认将 HS300、ZZ500、ZZ1000 和中证全指的行情、历史成分、权重列为 P0。缺任一指数的行情、成分或权重时，release readiness 必须输出 `required_missing` 或 `blocked_claims`；报告不得声明真实超额收益、指数增强、真实 tracking error 或大小盘暴露完整。

**理由**：用户需要用 published truth 重跑研究并判断旧 proxy / fixed-snapshot 结论是否仍成立。只补 HS300 不足以解释低波或因子结论是否来自大小盘、宽基暴露或指数成分变化；只有行情没有历史成分 / 权重也不足以支持 PIT benchmark 和指数增强声明。

**接受影响**：

- CR018-S03 成为 release readiness 的 P0 Story。
- benchmark quality 必须同时检查行情、成分、权重和 trade_calendar denominator。
- QMT admission 前 research rerun 必须引用 benchmark readiness。

**不接受影响**：

- 只做 HS300 会保留 ZZ500 / ZZ1000 / 中证全指相关 blocked claims。
- 只做行情会让成分 / 权重暴露分析不可用。

**备选方案**：

| 方案 | 优点 | 缺点 | 结论 |
|---|---|---|---|
| 先只做 HS300 | 范围小 | 不能解释宽基和大小盘暴露 | 降级备选 |
| 只做指数行情，不做成分 / 权重 | 可先算指数收益 | 不能做 PIT 成分、权重和 tracking error | 不推荐 |

**回写 HLD / Story**：`process/HLD-DATA-LAKE.md` §19.8、§19.12；CR018-S03。

**回退点**：若 provider 不支持成分 / 权重，先保留行情为 candidate，成分 / 权重进入 required_missing。

## ADR-065：CR-018 Explicit Publish Gate 采用 release-level 总门与 release-level rollback

**状态**：Draft for CR-018 CP3 review

**决策**：CR-018 publish 采用 release-level 总门 + dataset-level 明细。只有 Explicit Publish Gate 可以更新 catalog current pointer；validate PASS、parity PASS、quality report PASS、DuckDB audit PASS 均不得自动 publish。rollback 以 release 为单位，必须只切换 current pointer 并记录 rollback event，不删除 raw、manifest、candidate、quality evidence 或历史 release summary。

**理由**：P0 group 是跨 dataset 的一致 release。如果每个 dataset 独立 publish / rollback，research rerun 很容易混用不同 as-of 的 PIT、benchmark 和价格视图，current truth 不再可复现。release-level 总门让 rollback、read smoke 和报告声明保持一致。

**接受影响**：

- release summary 必须记录 `release_id`、dataset list、scope、as_of_trade_date、source run ids、quality summary、blocked claims、rollback target、approver、approved_at 和 checksum。
- CR018-S06/S07 分别拥有 readiness/rollback gate 与 publish/current reader smoke。
- 后续如需 sub-release，也必须由总门协调。

**不接受影响**：

- dataset 独立 publish 灵活但会增加一致性和回滚复杂度。
- 只保留 candidate reader 无法进入 production current truth。

**备选方案**：

| 方案 | 优点 | 缺点 | 结论 |
|---|---|---|---|
| dataset 独立 publish / rollback | 灵活 | current truth 容易漂移，rollback 难审计 | 不采用 |
| 不 publish，只保留 candidate reader | 风险最低 | 不能解除 current truth blocked | 降级备选 |

**回写 HLD / Story**：`process/HLD-DATA-LAKE.md` §19.7、§19.9、§19.10；CR018-S06、S07。

**回退点**：若 CP3 不接受，回退到 AGA-CR018-03，重新设计 publish 粒度。

## ADR-066：CR-018 publish 后研究重跑是 QMT admission 前置

**状态**：Draft for CR-018 CP3 review

**决策**：CR-018 要求 QMT simulation、live_readonly、small_live、scale_up 全部后置到数据湖 publish + production research rerun PASS 之后。Published release 后必须重跑阶段三到阶段五核心研究，报告记录 release_id、benchmark、PIT universe、tradability、adjustment_policy、blocked claims、旧 proxy / fixed-snapshot 对比和 pass/fail。通过后只允许进入下一轮 QMT stage gate 审批，不自动授权真实下单、撤单、账户查询或资金放大。

**理由**：CR015/016/017 foundation 已证明离线 / mock / runbook 能力，但策略是否可进入 simulation 取决于 published truth 下的研究结论。若不重跑，旧 proxy 或 fixed-snapshot 结论可能被 PIT/W3/benchmark 推翻，交易链路会放大假 alpha 风险。

**接受影响**：

- CR018-S08 是 QMT admission 的 runtime 前置。
- CR018-S09 只能输出 admission gate 和 blocked reason，不直接授权 QMT operation。
- CR016-S05/S06 继续 later-gated，直到 S08 PASS 和独立 QMT stage gate。

**不接受影响**：

- QMT 技术 simulation 先行需要独立 no-strategy Spike，否则容易被误读为策略可运行。
- 只后置 live/small/scale 但不后置 simulation 会放大治理歧义。

**备选方案**：

| 方案 | 优点 | 缺点 | 结论 |
|---|---|---|---|
| 技术 simulation 先行，声明无策略意义 | 早测 adapter | 需额外授权和强声明，治理复杂 | 后续 Spike |
| 只后置 live/small/scale | 最快进入 simulation | 策略有效性风险高 | 不采用 |

**回写 HLD / Story**：`process/HLD-DATA-LAKE.md` §19.9、§19.16；`process/HLD.md` §32；CR018-S08、S09。

**回退点**：若 CP3 不接受，回退到 AGA-CR018-04，重新界定 QMT 后置策略。

## ADR-067：CR-019 阶段六 admission 采用新多因子 gate + 多基准 primary benchmark

**状态**：Draft for CR-019 CP3 review

**决策**：阶段六不得包装既有 production rerun fail 的旧多因子 / 低波策略进入模拟盘。CR-019 必须以实验 49-66 建立新的 A 股多因子 admission gate，覆盖数据、因子、组合、交易现实性、成本、benchmark、稳健性、消融、冻结、pre-sim 和连续 5 个真实交易日 dry-run。Admission benchmark 采用多基准看板 + primary benchmark：同时输出 HS300、ZZ500、ZZ1000 和中证全指，并按策略 universe / 风格选择 primary benchmark；admission pass/fail 以 primary benchmark、风险约束和 blocked claims 为主。

**理由**：落实 REQ-138、REQ-144、REQ-154、Q-040 和用户 CP2 批准。旧策略 production current truth 重跑失败，若包装为 simulation ready，会直接放大假 alpha 和数据偏差风险。多基准看板可减少风格错配，primary benchmark 让最终准入结论可判定。

**接受影响**：

- Admission package 必须记录旧失败证据、实验 49-66 gate、blocked reason、解除条件和 benchmark selection。
- 连续 5 个真实交易日 dry-run 通过后，也只进入 CR016 stage gate 和 per-run authorization，不自动授权 simulation。
- 多基准输出增加报告字段和验证矩阵。

**不接受影响**：

- 只用旧失败策略会误导模拟盘准入。
- 只用单一 HS300 或绝对收益口径会在中小盘 / 全市场多因子中形成风格解释缺口。

**备选方案**：

| 方案 | 优点 | 缺点 | 结论 |
|---|---|---|---|
| 只用 HS300 | 简单，字段少 | 偏大盘，不能解释中小盘或全 A 暴露 | 不采用为默认 |
| 只看绝对收益 / 回撤 / 波动 / 成本 | 适合绝对收益策略 | 不适合 long-only A 股多因子默认准入 | 条件备选 |

**回写 HLD / Story**：`process/HLD.md` §33.1、§33.4、§33.6；后续 CR019 admission Story。

**回退点**：若 CP3 不接受，回退到 Q-040 和 UC-15，重新定义 admission benchmark 与 freeze fields。

## ADR-068：CR-019 QMT C/S bridge 主选为 local_backtest C 侧 client + Windows FastAPI gateway

**状态**：Draft for CR-019 CP3 review

**决策**：CR-019 将 local_backtest / WSL 与 Windows QMT 节点通信主路径冻结为 QMT 独立 C/S 模块。C 侧位于 local_backtest，通过 Python client / 函数接口和薄 CLI 发起 REST 请求；S 侧部署在 Windows QMT 节点，是可运行 / 可安装的 FastAPI gateway，负责将 REST 请求转换为 QMT / XtQuant adapter 调用并访问 QMT 服务端。WSL / local_backtest 不直接导入或调用 xtquant。

**理由**：落实 REQ-145、REQ-149、REQ-159 和用户 D7 / QMT 模块纠偏。FastAPI gateway 相比 signed file drop 更适合完整 endpoint matrix、heartbeat、capabilities、typed blocked reason 和运行门控；同时保持 adapter 与 QMT 环境在 Windows。

**接受影响**：

- `process/HLD-QMT-TRADING.md` §17 成为 QMT gateway 运行合同增量。
- Windows gateway 必须有命令、配置路径、bind host / port、防火墙、heartbeat、日志脱敏和 incident 边界。
- signed file drop 从 ADR-061 旧默认主路径降级为 ADR-072 fallback。

**不接受影响**：

- 若继续 file drop 为主路径，将不满足用户完整 QMT 功能接口和服务化目标。
- 若 gateway 嵌入回测主进程，会破坏 C/S 模块边界并增加 WSL 直连风险。

**备选方案**：

| 方案 | 优点 | 缺点 | 结论 |
|---|---|---|---|
| signed file drop 主路径 | 简单、低权限 | 自动化弱、接口能力不可观测，不符合 D7 | fallback |
| 回测主进程内嵌 gateway | 文件少 | 与研究主进程耦合，测试和部署边界差 | 不采用 |

**回写 HLD / Story**：`process/HLD.md` §33.3、§33.8、§33.9；`process/HLD-QMT-TRADING.md` §17。

**回退点**：若 CP3 不接受，回退到 AGA-CR019-01，重新确认 bridge 主路径。

## ADR-069：CR-019 C 侧接口采用 Python client / 函数调用为主 + 薄 CLI

**状态**：Draft for CR-019 CP3 review

**决策**：C 侧对 local_backtest 的默认接口采用 Python client / 函数调用为主，CLI 作为薄包装复用同一 client，仅用于人工 smoke、运维检查和脚本集成。内部策略、OMS、admission dry-run 和测试不得以 shell 进程调用 / 文本解析作为默认主路径。

**理由**：落实 REQ-160 和 Q-044。Python client 更适合类型化请求、mock、错误处理、blocked result 和单元测试；薄 CLI 保留人工可操作性，但不复制业务逻辑。

**接受影响**：

- 后续 LLD 需要定义 typed request / response、错误枚举、timeout、redaction label 和 CLI exit code。
- CLI 只能包装 client，不拥有单独业务判断。

**不接受影响**：

- CLI-first 会让框架内部调用承担进程管理、文本解析和退出码契约，测试成本更高。
- Python-only 会减少运维检查入口。

**备选方案**：

| 方案 | 优点 | 缺点 | 结论 |
|---|---|---|---|
| CLI-first | 手工友好，便于 shell | 内部调用和 mock 成本高 | 不采用默认 |
| Python-only | 最薄，内部最简单 | 缺人工 smoke / 运维入口 | 条件备选 |

**回写 HLD / Story**：`process/HLD.md` §33.4、§33.9；`process/HLD-QMT-TRADING.md` §17.1。

**回退点**：若 CP3 不接受，回退到 Q-044，重新冻结 C 侧接口形态。

## ADR-070：CR-019 完整 QMT endpoint matrix 与运行门控分离

**状态**：Draft for CR-019 CP3 review

**决策**：Windows gateway 的 endpoint matrix 必须覆盖完整 QMT 功能类别：health/capabilities、validate/dry-run、行情、账户、持仓、委托、成交、simulation submit/cancel、live-readonly、live submit/cancel、reconciliation、kill-switch。接口类别完整支持不等于真实操作授权；任何真实转发必须通过 run mode、CR016 stage gate、pre-trade risk、kill switch、per-run authorization 和 raw execution policy。

**理由**：落实 REQ-146、REQ-147 和 Q-041，回应用户纠正“不做或少做鉴权不等于不做 QMT 功能”。接口完整性是能力目标，运行门控是安全目标，二者必须分离。

**接受影响**：

- API contract 和测试矩阵扩大，但每类 endpoint 都能给出 blocked / allowed 条件。
- `capabilities` 可显示 endpoint 类别，但不能视为真实 operation approval。
- 未满足 gate 时真实 QMT / order / cancel / account query 调用计数必须为 0。

**不接受影响**：

- dry-run-only 不满足用户完整 QMT 能力目标。
- 局域网无门控直转会绕过 CR016 stage gate 和 kill switch。

**备选方案**：

| 方案 | 优点 | 缺点 | 结论 |
|---|---|---|---|
| dry-run / readonly 子集 | 实现范围小 | 不满足完整 QMT 功能目标 | 可作为首批实现子集，不作为目标基线 |
| 局域网内无门控直转 | 集成最快 | 高风险，绕过运行治理 | 不采用 |

**回写 HLD / Story**：`process/HLD.md` §33.11；`process/HLD-QMT-TRADING.md` §17.2。

**回退点**：若 CP3 不接受，回退到 Q-041；不得在未重新决策前把接口目标退回 dry-run-only。

## ADR-071：CR-019 鉴权策略采用配对式 token/HMAC 默认启用

**状态**：Draft for CR-019 CP3 review

**决策**：第一版 FastAPI gateway 默认启用轻量配对式 token/HMAC。C 侧先执行 pairing request，S 侧 Windows gateway 记录 pending request，管理员通过 `qmt-gateway pair list` 和 `qmt-gateway pair approve <request_id>` 批准后生成 client id + secret，并通过一次性 pairing code 或短 TTL 领取窗口完成 C 侧 `pair complete`。后续请求必须携带 `X-QMT-Client-Id`、`X-QMT-Timestamp`、`X-QMT-Nonce`、`X-QMT-Signature`，签名建议为 `HMAC_SHA256(secret, method + path + body_hash + timestamp + nonce)`。S 侧必须校验 approved client、timestamp 偏移、nonce replay 和 scope。no-auth 仅允许本机 debug、fixture 测试或显式配置的临时模式。HMAC 通过后仍必须继续执行 run mode、stage gate、risk gate、kill-switch 和 per-run authorization；鉴权不触达或替代 QMT adapter。

**理由**：落实 REQ-148、REQ-151、Q-039 和 CP3 DQ-04 用户修订。用户已明确不再接受 no-auth 作为默认推荐，而是采用配对式 token/HMAC 默认启用。该方案比 no-auth 更能防止局域网误调用，同时比 mTLS / VPN / Windows ACL 轻量；鉴权只解决“谁能调用网关”，不削减 QMT endpoint 功能，也不替代真实交易运行门控。

**接受影响**：

- HLD / LLD 必须定义 pairing request / list / approve / complete、request_id、client name、来源 IP、机器指纹摘要、创建时间、过期时间、client id、secret、pairing code、timestamp 偏移、nonce replay 和 scope 的设计边界。
- 日志必须脱敏，禁止 secret、pairing code、token、账户号、session、cookie、交易密码、`.env` 和真实私有路径。
- no-auth 不再是默认推荐，只能作为本机 debug / fixture / 显式临时模式，且仍不能绕过 run gate。

**不接受影响**：

- no-auth 默认会使局域网误调用风险偏高，不再符合 DQ-04 修订。
- 若把 HMAC pass 当作 simulation / live / account / cancel 授权，会造成授权语义错误。
- 若记录 secret 或 pairing code，会造成凭据泄露风险。

**备选方案**：

| 方案 | 优点 | 缺点 | 结论 |
|---|---|---|---|
| no-auth 默认 | 最简单，fixture 方便 | 局域网误调用风险高，不符合用户修订 | 仅 debug / fixture / 显式临时 |
| 静态共享 token | 实现比 pairing 更简单 | 缺少客户端批准、过期和来源审计 | 不推荐 |
| mTLS / VPN / Windows ACL | 安全更强 | 对阶段六第一版过重 | 后续增强 |

**回写 HLD / Story**：`process/HLD.md` §33.4、§33.10、§33.13；`process/HLD-QMT-TRADING.md` §17.3。

**回退点**：若 CP3 不接受配对式 token/HMAC，回退到 Q-039 / DQ-04 重新选择鉴权默认值；若后续跨网段、多人访问或 live endpoint 默认启用，在 pairing/HMAC 基础上增加 scope、secret rotation 或更强鉴权方案。

## ADR-072：CR-019 FastAPI fallback 采用 blocked-only 或人工 dry-run / signed file drop

**状态**：Draft for CR-019 CP3 review

**决策**：FastAPI gateway 不可达、可选鉴权失败、heartbeat fail、部署边界不满足或 run gate fail 时，fallback 只能返回 blocked result，或生成供人工处理的 dry-run / signed file drop 文件。fallback 不得自动绕过 gateway 触发真实 QMT 发单、撤单、账户查询、reconciliation 或 broker lake 写入。

**理由**：落实 REQ-145、REQ-150 和 Q-042。fallback 的目标是 fail closed 和保留审计连续性，不是提高真实交易可用性。自动真实 fallback 会绕过 gateway、stage gate、risk gate 或 kill switch。

**接受影响**：

- gateway 故障时可用性降低，但安全性和审计边界清晰。
- signed file drop 仍保留为人工 dry-run fallback，不再承担完整 QMT 功能替代。

**不接受影响**：

- 自动真实 fallback 会造成未授权发单 / 撤单 / 查询风险。
- 完全删除 fallback 会降低故障诊断与人工演练便利性。

**备选方案**：

| 方案 | 优点 | 缺点 | 结论 |
|---|---|---|---|
| 仅 blocked-only | 最安全 | 人工排障信息少 | 可接受子方案 |
| 自动切换备用真实 QMT 路径 | 可用性高 | 风险极高，绕过 gate | 不采用 |

**回写 HLD / Story**：`process/HLD.md` §33.12；`process/HLD-QMT-TRADING.md` §17.4。

**回退点**：若 CP3 不接受，回退到 Q-042，重新定义 fallback 责任和 fail-close 策略。

## ADR-073：CR-019 Backtrader / Qlib / minute / Level2 均后置触发

**状态**：Draft for CR-019 CP3 review

**决策**：Backtrader 保持 W6 optional execution backend，只有 clean feed、候选策略稳定和执行对照需求明确后启动；Qlib 保持 W7 isolated runner，只有 factor panel、report catalog、PIT / available_at 和 isolated runner I/O 合同稳定后启动；分钟数据仅在交易现实性实验证明日频执行假设不足时进入 Spike；Level2 仅在订单簿深度、排队、冲击成本或微观结构成为主要风险且 L1 / minute 不足时另起授权和数据审计。

**理由**：落实 REQ-139 至 REQ-143、REQ-155 至 REQ-158 和 Q-043。阶段六 P0 是日频多因子 admission 与 QMT C/S bridge，不应被框架迁移、外部 ML workflow、高频数据或 Level2 权限工程挤占。

**接受影响**：

- Admission 主线保持聚焦；外部框架和高频数据以 Deferred Ideas 管理。
- 后续若触发，需要新 Story / CR / CP5，并明确依赖、权限和数据审计。

**不接受影响**：

- 提前 Qlib 或 Backtrader 会扩大依赖和事实源风险。
- 提前 minute / Level2 会引入存储、权限和微观结构验证成本。

**备选方案**：

| 方案 | 优点 | 缺点 | 结论 |
|---|---|---|---|
| 提前 Backtrader | 执行语义更完整 | 不解决 alpha 和数据缺口，可能抢占 admission | 后置 |
| 提前 Qlib | 快速比较 ML workflow | provider_uri / 依赖隔离复杂 | 后置 |
| 提前 minute / Level2 | 执行现实性更强 | 数据、权限和成本过高 | Spike 触发后再做 |

**回写 HLD / Story**：`process/HLD.md` §33.14；后续 roadmap / Story Plan。

**回退点**：若用户要求提前某项能力，回退到 UC-18 并新建 CR / Spike。

## ADR-074：CR-025 Backtrader 默认定位为 optional semantic reference

**状态**：Draft for CR-025 CP3 review

**决策**：CR-025 中 Backtrader 默认只作为 optional execution realism / semantic reference 和 design reference；lightweight engine 继续作为默认研究与回测主路径中的执行层 baseline。未显式选择 Backtrader 时，默认入口、默认测试、数据读取和 lightweight baseline 均不得导入、运行或依赖 Backtrader。Backtrader 输出只能标记为 research comparison，不得覆盖 lightweight baseline，不得作为 production truth、默认研究 truth、QMT simulation admission pass、真实交易授权或多因子研究主框架。

**理由**：落实 REQ-161、REQ-166、REQ-167 和 CP2 DQ-01，并响应 2026-06-02 CP5 前定位澄清。用户的目标是 production-grade research-to-execution 路线，且系统核心定位是多因子策略研究和回测，而不是框架级迁移。Backtrader 的当前价值是提供成熟事件驱动框架的执行语义参照，帮助解释成交、现金、成本、滑点、仓位和订单状态差异；默认迁移会扩大回归面，也不能直接解决 FactorSpec、IC / RankIC、多因子组合、OMS、risk、stage gate 和真实 QMT 治理。

**接受影响**：

- HLD / Story Plan 必须继续把 lightweight 写为 baseline。
- Backtrader adapter 若后续 CP5 批准实现，也只能通过 optional dependency + lazy import 进入。
- 未安装 Backtrader 是合法环境，必须返回 structured `backend_unavailable` 或 `not_selected`。
- 多因子研究闭环能力不由 Backtrader 或 CR-025 承接，必须另起后续 CR。

**不接受影响**：

- Backtrader 不能被写成主框架、默认依赖、阶段六 P0 或 QMT admission 前置。
- Backtrader 对照报告不能减少 research/data/QMT gate。
- Backtrader 不能被写成 FactorSpec、FactorRunSpec、IC / RankIC、分层收益、多因子组合、实验追踪或策略准入包的主框架。

**备选方案**：

| 方案 | 优点 | 缺点 | 结论 |
|---|---|---|---|
| Backtrader optional runtime | 可获得真实框架对照 | 需 CP5 依赖授权和回归矩阵 | 后续条件备选 |
| Backtrader 主路径迁移 | 框架统一 | 扩大回归、偏离当前目标 | 不采用 |
| 多因子研究后续 CR | 可围绕 Qlib / Alphalens / vnpy.alpha 设计研究闭环 | 需要独立 HLD / Story / CP5，不解决 CR-025 当前执行语义对齐 | 另起 CR |

**回写 HLD / Story**：`process/HLD.md` §34.1、§34.3、§34.4；后续 CR025 Story Plan。

**回退点**：若 CP3 不接受，回退到 AGA-CR025-01，重新确认 Backtrader 与 lightweight 的默认关系。

## ADR-075：CR-025 Backtrader 模块处理采用 reference/adapt/exclude 分类

**状态**：Draft for CR-025 CP3 review

**决策**：Backtrader 本地项目模块处理采用四类：`reference_only`、`adapt_interface`、`migration_candidate`、`exclude`。当前默认分类为：`cerebro.py`、broker/order/trade/position、analyzer/observer、strategy/signal、plot/writer、samples/tests 为 `reference_only`；clean feed、semantic diff、commission/sizer/fill assumption、target order 概念为 `adapt_interface`；`migration_candidate` 为空；live broker/store、外部 feeds、line/metaclass runtime、indicator library migration、samples/tests data copy 为 `exclude`。Backtrader 的 indicators / Strategy / analyzer 体系只用于识别执行语义和报告可解释性类别，不作为多因子研究主框架或因子评价框架。

**理由**：落实 REQ-173 和用户追加要求。Backtrader 本地包约 171 个 Python 文件，含完整事件驱动运行时、line/metaclass 体系、live stores、broker adapters 和大量指标。直接源码移植会把 CR-025 从 research-to-execution semantic alignment 扩大成框架工程；把 Backtrader 指标 / Strategy 体系作为多因子主框架则会进一步偏离 FactorSpec、IC / RankIC、分层收益和实验追踪等研究闭环问题。分类矩阵能保留可借鉴点，同时约束 GPLv3、维护、验证和范围膨胀风险。

**接受影响**：

- HLD 必须保留模块级矩阵，供后续 LLD 判断文件 owner 与 forbidden paths。
- 后续实现只能 clean-room 定义本项目接口；不得复制类、函数或样例数据。
- 如果用户要求某个模块成为源码级候选，必须重新进入 CP3 决策。
- 如果用户要求因子研究框架能力，必须路由到后续多因子研究 CR，而不是把 Backtrader indicators / Strategy 迁入 CR-025。

**不接受影响**：

- “参考 Backtrader”不能被简化为一句话，必须有模块职责、license 风险、维护成本和验证策略。
- `migration_candidate` 为空不代表永远不可迁移，而是当前 CR 不推荐。
- “Backtrader analyzer / indicator 可参考”不能被解释为 CR-025 要实现 IC、RankIC、分层收益或多因子组合。

**备选方案**：

| 方案 | 优点 | 缺点 | 结论 |
|---|---|---|---|
| 仅高层描述，不做模块矩阵 | 文档短 | 不满足 REQ-173 和用户要求 | 不采用 |
| 标记少数源码级候选 | 后续实现可能快 | GPLv3、维护和回归风险高 | 暂不推荐 |
| 将指标 / analyzer 迁入多因子研究闭环 | 短期看似复用现成概念 | 偏离 CR-025，且无法替代 Qlib / Alphalens 类研究评价能力 | 不采用，另起 CR |

**回写 HLD / Story**：`process/HLD.md` §34.5。

**回退点**：若 CP3 不接受，回退到 AGA-CR025-02，重新组织模块范围。

## ADR-076：CR-025 GPLv3 源码级移植默认 no-copy，例外需 CP3/CP5 双门控

**状态**：Draft for CR-025 CP3 review

**决策**：本项目默认不复制、裁剪、改写或源码级移植 `/home/hyde/download/backtrader` 中的 Backtrader GPLv3 / GPLv3+ 源码。所有后续实现必须采用 clean-room interface adaptation，或在 CP5 后通过 optional dependency 使用外部安装包而不把源码纳入本仓库。任何源码级移植例外都必须满足：1. CP3 决策项明确模块、替代方案、GPLv3/copyleft 影响、维护成本和回归范围；2. CP5 LLD/实现授权明确文件 owner、许可证标注、分发策略和回滚方案；3. 用户接受风险并完成必要法律 / 开源合规确认。

**理由**：落实 REQ-172、RA-066 和本地 `LICENSE` / `setup.py` 事实。GPLv3 是强 copyleft 许可证；源码复制、修改、分发或与本项目结合可能带来许可证继承、源码提供、修改标记和再分发义务。本项目当前是 production research tooling，不应在 CP3 默认承担该许可证和维护成本。

**接受影响**：

- CP3 可分析模块，但不能把源码级移植写成默认实现。
- LLD 必须把 Backtrader 源码复制、样例复制、测试数据复制列为 forbidden path。
- 后续可用 behavior fixture 重新构造测试，不使用 Backtrader 测试数据。

**不接受影响**：

- 不得把“开源可用”误写为“可直接复制”。
- 不得用重命名、裁剪或手工改写规避 license 风险。

**备选方案**：

| 方案 | 优点 | 缺点 | 结论 |
|---|---|---|---|
| optional dependency 使用外部包 | 可运行对照，不复制源码 | 仍需依赖隔离和分发策略 | CP5 后可选 |
| fork / vendor Backtrader 子集 | 可深度改造 | GPLv3 风险和维护成本最高 | 仅独立 CR / legal review 后考虑 |

**回写 HLD / Story**：`process/HLD.md` §34.5、§34.14。

**回退点**：若 CP3 不接受 no-copy 默认，回退到 AGA-CR025-03 并升级为 license / distribution 专题决策。

## ADR-077：CR-025 只冻结 order intent draft 与 QMT 消费边界

**状态**：Draft for CR-025 CP3 review

**决策**：CR-025 的 research-to-execution 输出只冻结 target portfolio / order intent draft，推荐 schema 为 `order_intent_draft_v1`，至少包含 `schema_version`、`strategy_id`、`run_id`、`signal_date`、`target_trade_date`、`symbol`、`side`、`target_weight` 或 `target_qty`、`research_adjustment_policy`、`execution_price_policy=raw`、`cost_config_ref`、`data_lineage_ref` 和 `limitations`。QMT companion HLD 只把该 draft 作为后续 OMS / risk / adapter 的输入候选；CR-025 不授权 CR-020 gateway 启动、QMT simulation、live-readonly、small-live、scale-up、账户查询、下单、撤单或 broker lake 写入。

**理由**：落实 REQ-169、REQ-171 和 CP2 DQ-04。用户目标包含生产执行路线，但真实 QMT route 已被拆为 CR-020..CR-024，并需要独立 runtime authorization。CR-025 的合理交界面是提供可审查的意图草案和 semantic diff evidence，而不是触达 broker。

**接受影响**：

- `process/HLD-QMT-TRADING.md` 只同步 order intent draft 消费边界。
- 后续 Story / LLD 必须把 `execution_price_policy=raw` 作为 hard gate。
- 缺 lineage、limitations 或 raw execution policy 时不得声明可进入 OMS。

**不接受影响**：

- CP3 approve 不等于服务启动或真实交易授权。
- Backtrader 对照结果不得写成 simulation-ready。

**备选方案**：

| 方案 | 优点 | 缺点 | 结论 |
|---|---|---|---|
| CR-025 直接调用 QMT validate / dry-run | 链路更快 | 越过 CR-020/CP 门控 | 不采用 |
| 仅输出 diff，不输出 intent draft | 范围更小 | 无法连接 production route | 备选但不推荐 |

**回写 HLD / Story**：`process/HLD.md` §34.7；`process/HLD-QMT-TRADING.md` §18。

**回退点**：若 CP3 不接受，回退到 AGA-CR025-04 / AGA-CR025-05，重新界定 CR-025 与 QMT route 的接口。

## ADR-078：CR-025 不承接多因子研究闭环主框架

**状态**：Draft for CR-025 CP5 refresh

**决策**：CR-025 不实现、不设计、不验收多因子研究闭环主框架。FactorSpec、FactorRunSpec、IC / RankIC、分层收益、多因子组合、实验追踪、策略准入包、Qlib isolated runner、Alphalens-style factor tear sheet 和 vnpy.alpha-style alpha research workflow 均属于后续 CR 范围。CR-025 只保留 Backtrader 作为 lightweight execution engine 的 execution semantic reference，覆盖 feed / broker / order / position / commission / slippage / analyzer 等执行层语义参考；Backtrader 不负责因子定义、因子评价、因子组合、实验注册或策略准入结论。

**理由**：2026-06-02 用户澄清系统核心定位是多因子策略研究和回测，并指出 Backtrader 不是多因子研究主参考。Backtrader 的优势在事件驱动执行语义、订单 / 仓位 / 成本 / 滑点 / broker 抽象和 analyzer 输出结构；多因子研究闭环需要独立的数据模型、因子运行规格、横截面统计、分层收益、组合构建、实验追踪和准入包，参考对象应优先评估 Qlib / Alphalens / vnpy.alpha。把这些能力塞入 CR-025 会扩大 CP5 范围、污染已完成的 6 Story / 4 Wave / 1 LLD batch，并让 meta-dev 的 LLD 输入失真。

**接受影响**：

- CR-025 的 6 Story / 4 Wave / 1 LLD batch 保持不变。
- S02 semantic diff 只比较执行语义差异，不新增 IC / RankIC / 分层收益字段。
- S04 no-copy guardrail 只管理 Backtrader 模块 reference / no-copy，不输出多因子研究框架评估报告。
- S06 docs / handoff 必须把多因子研究闭环登记为后续 CR 候选，并说明参考 Qlib / Alphalens / vnpy.alpha。
- meta-po 需要刷新 CP5 Decision Brief / launch message，提示 `approve` 不代表接受或授权多因子研究框架实现。

**不接受影响**：

- 不把 Backtrader indicators / Strategy / analyzer 体系改写为本项目 FactorSpec / FactorRunSpec。
- 不把 semantic diff artifact 扩展为 factor tear sheet、IC report 或 experiment tracker。
- 不把 CR-025 的 order intent draft 当作策略准入包。
- 不在 CR-025 中引入 Qlib / Alphalens / vnpy.alpha 依赖、provider fetch、lake write、publish、simulation/live 或凭据读取。

**备选方案**：

| 方案 | 优点 | 缺点 | 结论 |
|---|---|---|---|
| 后续多因子研究 CR 参考 Qlib / Alphalens / vnpy.alpha | 边界清晰，可单独设计 FactorSpec、IC / RankIC、分层收益和实验追踪 | 需要新 CP2/CP3/CP5，不能由 CR-025 立即交付 | 推荐 |
| 在 CR-025 内扩展多因子研究闭环 | 一次性合并讨论 | 扩大范围，破坏现有 LLD 批次，混淆 Backtrader 角色 | 不采用 |
| 暂不记录多因子研究路线 | 文档改动少 | 后续容易把执行语义和研究框架混在一起 | 不采用 |

**回写 HLD / Story**：`process/HLD.md` §34.1、§34.4、§34.6、§34.14、§34.15、§34.18；`process/STORY-BACKLOG.md` CR025-S02 / S04 / S06；`process/DEVELOPMENT-PLAN.yaml` CR025 metadata 与 S02 / S04 / S06。

**回退点**：若用户要求 CR-025 同时交付多因子研究闭环，回退到 CR-025 CP4/CP5 批次规划，或由 meta-po 启动新的多因子研究 CR 冲突预检；不得在当前 CP5 brief 中静默扩大实现范围。

## ADR-079：CR-030 采用项目自有多因子研究闭环主线

**状态**：Draft for CR-030 CP4 Story Plan

**决策**：CR-030 的主线采用项目自有多因子研究闭环，外部项目只进入 reference matrix、optional Spike、exclude 或 forbidden migration 分类。本项目的 data lake、`research_input_v1`、实验 17-21、CR-011 factor panel audit、label window gate、Stage6 admission gate 和 CR-025 `order_intent_draft_v1` 是多因子闭环的基线事实源；Qlib、Alphalens、vectorbt、PyBroker、bt、Zipline Reloaded、QuantConnect LEAN、RQAlpha、vn.py / vnpy.alpha、Backtrader 均不得成为默认 framework、truth、provider、runner、optimizer 或 report truth。

**理由**：落实 UC-20、REQ-174、REQ-183 和 CP3 DQ-CP3-CR030-01。当前系统已有生产数据湖、研究输入和 Stage6 gate 基线，直接引入外部 runner 会产生双 truth、依赖扩散、provider / runner 越权和许可证风险。

**接受影响**：

- Story Plan 必须先冻结自有合同，再处理评价、组合、manifest/catalog 和准入包。
- CR-026 Qlib isolated runner 只能在合同冻结后作为后续 Spike candidate。
- 后续 LLD 不得把外部对象替换为内部 truth。

**不接受影响**：

- 不安装、不运行、不 clone 外部项目。
- 不从外部项目复制源码、样例、测试或数据。
- 不把外部项目文档描述成本项目已具备能力。

**备选方案**：

| 方案 | 优点 | 缺点 | 结论 |
|---|---|---|---|
| Qlib runner-first / qrun 集成 | workflow / recorder 生态成熟 | provider_uri、`.bin` 数据格式、MLflow/pickle、依赖和双 truth 风险高 | 不作为 CR-030 默认；保留 CR-026 Spike |
| 文档 / Spike-only | 短期成本最低 | 无法支撑 CP4/CP5 和后续实现 | 仅作为 CP3 不通过回退 |

**回写 HLD / Story**：`process/HLD.md` §35.3、§35.5；`CR030-S01` 至 `CR030-S08`。

**回退点**：若后续证明自有 runner 表达力或性能不足，合同冻结后由 meta-po 单独启动 CR-026 或 bounded Spike。

## ADR-080：外部项目矩阵与迁移边界采用 reference-first 治理

**状态**：Draft for CR-030 CP4 Story Plan

**决策**：CR-030 必须输出并维护 10 类外部项目的借鉴矩阵。每个项目至少记录 license / dependency / provider / runtime boundary、可借鉴点、不可直接采用点、recommendation、切换条件和 not-authorized 边界。源码级迁移默认 forbidden，除非后续独立 CR / CP3 / CP5 / 用户风险接受明确批准。

**理由**：落实 UC-21、REQ-175、REQ-182、REQ-185 和 CP3 DQ-CP3-CR030-02 / 05。用户目标是借鉴成熟项目而不是把外部框架接管本项目；矩阵必须让引用边界可审计。

**接受影响**：

- `CR030-S01` 成为后续所有合同 Story 的外部 cross-check 前置。
- Qlib 为 reference_only + optional_spike；Alphalens / bt / Zipline / LEAN 为 reference_only；vectorbt / PyBroker / RQAlpha / vn.py 为 optional_spike 或 exclude by default；Backtrader 继承 CR-025 forbidden_migration。
- LLD 必须把外部运行、源码迁移、provider 和 dependency 变更列为 forbidden 或后续 Spike。

**不接受影响**：

- 不把 license 不确定项目写成可默认集成。
- 不把 GitHub 样例或测试数据迁入本仓库。

**备选方案**：

| 方案 | 优点 | 缺点 | 结论 |
|---|---|---|---|
| 只分析 Qlib | 范围小 | 容易把单一项目抽象误当通用事实 | 不采用 |
| 直接 adapter-first | 未来扩展快 | 内部合同未冻结前会形成空转适配层 | 后续增强 |

**回写 HLD / Story**：`process/HLD.md` §35.4；`CR030-S01`、`CR030-S08`。

**回退点**：若许可证 / 依赖风险无法静态判断，转 non-blocking Spike，不阻塞自有合同主线。

## ADR-081：Schema provenance 采用项目自有契约 + 既有基线 + external cross-check

**状态**：Draft for CR-030 CP4 Story Plan

**决策**：`FactorSpec`、`FactorRunSpec`、`FactorPanelContract`、`LabelWindowSpec`、`FactorEvaluationReport`、`MultiFactorCombiner`、`ExperimentManifest`、`ResearchReportCatalog` 和 `StrategyAdmissionPackage` 均采用项目自有契约。字段来源优先复用 `research_input_v1`、实验 17-21 `FactorDefinition`、CR-011 factor panel audit、label window gate 和 Stage6 admission gate，再用 Qlib / Alphalens / Zipline / LEAN 等概念 cross-check；不得直接采用外部对象作为内部 truth，也不得从零设计而不解释增量理由。

**理由**：落实 UC-22、UC-23、REQ-176、REQ-177、REQ-183、REQ-185 和 CP3 DQ-CP3-CR030-02。基线复用能减少双 truth，并让后续 LLD 可追溯到已有模块。

**接受影响**：

- `CR030-S02` 冻结 `FactorSpec` / `FactorRunSpec`。
- `CR030-S03` 冻结 `FactorPanelContract` / `LabelWindowSpec` 与错误码。
- 旧实验和 CR-011 不被覆盖；新对象必须说明兼容策略。

**不接受影响**：

- 不把 Qlib Alpha158、Alphalens factor_data、Zipline Pipeline 或 LEAN Alpha Model 作为内部对象。
- 不在字段缺失时进入评价、组合或准入。

**备选方案**：

| 方案 | 优点 | 缺点 | 结论 |
|---|---|---|---|
| 直接采用外部对象 | 初期字段现成 | 依赖和双 truth 风险高 | 不采用 |
| 从零设计 | 名称完全贴合本项目 | 容易遗漏成熟框架已解决的问题 | 不采用 |

**回写 HLD / Story**：`process/HLD.md` §35.6、§35.7；`CR030-S02`、`CR030-S03`。

**回退点**：若现有基线字段不足，只能通过 Story LLD 增量补字段，不得整体重写旧基线。

## ADR-082：FactorPanel / LabelWindow 防泄漏采用 fail-closed

**状态**：Draft for CR-030 CP4 Story Plan

**决策**：`FactorPanelContract` 与 `LabelWindowSpec` 对前视、标签重叠、lineage 缺失、复权口径混用、quality status 缺失、停牌 / 无成交 / 成本口径不明等场景采用 fail-closed。任一 P0 字段缺失或 `available_at > decision_time` / label overlap 风险存在时，评价、组合和准入必须输出 structured blocked reason，不得继续生成生产声明。

**理由**：落实 UC-23、REQ-177、REQ-182 和 HLD §35.7.3。多因子研究最主要的质量风险是假 alpha 和未来函数；warn-only 会让错误进入组合和准入。

**接受影响**：

- `CR030-S03` 是 `CR030-S04` / `CR030-S05` / `CR030-S07` 的 contract 前置。
- 后续测试必须至少覆盖 available_at、label overlap、lineage、复权混用、quality 缺失、provider/lake 未授权等错误码。
- blocked report 是合法输出，不是执行失败。

**不接受影响**：

- 不接受缺 `available_at` 的字段进入信号。
- 不用外部框架自动生成 PIT universe、复权因子或标签 truth。

**备选方案**：

| 方案 | 优点 | 缺点 | 结论 |
|---|---|---|---|
| warn-only | 更容易跑通 | 风险进入组合和准入 | 不采用 |
| 只在 admission 阶段阻断 | 前期报告多 | 污染中间指标和组合 | 不采用 |

**回写 HLD / Story**：`process/HLD.md` §35.7.3、§35.8；`CR030-S03`、`CR030-S04`、`CR030-S05`、`CR030-S07`。

**回退点**：若 CP5 发现某字段无法获得，应降级为 `research_limited` 或 blocked claims，而不是放宽 fail-closed。

## ADR-083：MultiFactorCombiner P0 采用可解释组合，optimizer 后置

**状态**：Draft for CR-030 CP4 Story Plan

**决策**：CR-030 P0 的 `MultiFactorCombiner` 采用可解释规则权重或轻量线性组合，显式记录标准化、winsorization、中性化、正交化、权重策略、缺失值处理、约束、benchmark、成本、容量、调仓频率、冻结策略和 blocked reason。Qlib EnhancedIndexing、cvxpy、外部 optimizer、ML workflow、风险模型或复杂组合优化仅作为后续 Spike 条件，不进入 CR-030 P0。

**理由**：落实 UC-25、REQ-179 和 CP3 DQ-CP3-CR030-04。P0 优先可解释性、验证性和权限最小；optimizer 过早引入会扩大依赖、风险模型和性能验证范围。

**接受影响**：

- `CR030-S05` 依赖 `CR030-S04` 的单因子评价报告。
- 多因子组合必须输出 `MultiFactorPortfolioPlan` 草稿，不生成 broker order。
- optimizer 需求进入 follow-up Spike 条件表。

**不接受影响**：

- 不新增 cvxpy / LightGBM / vectorbt optimizer 依赖。
- 不把组合权重优化结果写成真实可交易证据。

**备选方案**：

| 方案 | 优点 | 缺点 | 结论 |
|---|---|---|---|
| 默认 optimizer | 表达力强 | 依赖和风险模型要求高，验证复杂 | 后置 Spike |
| 不设计组合 | 范围小 | 无法形成策略准入闭环 | 不采用 |

**回写 HLD / Story**：`process/HLD.md` §35.6、§35.8、§35.13；`CR030-S05`。

**回退点**：若 P0 组合无法满足研究目标，再由 meta-po 启动 optimizer / ML weighting Spike。

## ADR-084：ExperimentManifest / ResearchReportCatalog 采用 JSON/CSV/Markdown artifact + config hash

**状态**：Draft for CR-030 CP4 Story Plan

**决策**：CR-030 使用项目自有 `ExperimentManifest` 与 `ResearchReportCatalog` 记录 run_id、strategy_id、config_hash、dataset/release、factor_versions、label_window、benchmark、cost_config、evaluation_window、seed、code_version、report_paths、allowed_claims、blocked_claims、limitations 和 evidence refs。报告形态采用 JSON / CSV / Markdown artifact 和路径索引；不采用 MLflow / pickle recorder 作为默认事实源。

**理由**：落实 UC-26、REQ-180、REQ-185。当前项目已有文件型报告和数据湖 catalog 习惯，JSON/CSV/Markdown 更易审计、diff 和离线验证；MLflow / pickle 会引入依赖与 artifact truth 迁移成本。

**接受影响**：

- `CR030-S06` 是 `CR030-S07` 的 admission 输入前置。
- 缺 manifest / catalog P0 字段时不得进入 `StrategyAdmissionPackage`。
- 旧报告不覆盖，新报告版本化输出。

**不接受影响**：

- 不写真实 lake，不 publish current pointer，不覆盖旧 reports。
- 不把未发布或未通过 readiness 的数据声明为 current truth。

**备选方案**：

| 方案 | 优点 | 缺点 | 结论 |
|---|---|---|---|
| MLflow recorder | 生态成熟 | 依赖、运行和 artifact truth 扩大 | 不采用默认 |
| pickle artifact | 快速保存对象 | 不易审计，兼容性差 | 不采用 |

**回写 HLD / Story**：`process/HLD.md` §35.6、§35.8；`CR030-S06`。

**回退点**：若后续需要外部 recorder，必须另起 adapter / Spike，并保持内部 catalog 为 truth。

## ADR-085：StrategyAdmissionPackage 只输出研究准入证据和 order_intent_draft_v1 草稿

**状态**：Draft for CR-030 CP4 Story Plan

**决策**：`StrategyAdmissionPackage` 只汇总数据、因子、组合、回测、成本、benchmark、稳健性、消融、冻结、pre-sim、5 日 dry-run 前置状态、blocked reasons、解除条件和 `order_intent_draft_v1` 草稿引用。该 package 不构成 QMT-ready、simulation-ready、live-ready、production truth 或真实可交易证据；没有 CR-020..CR-024 独立授权时，`qmt_api_call=0`、`real_order=0`、`account_query=0`。

**理由**：落实 UC-27、REQ-181、REQ-182 和 CP3 DQ-CP3-CR030-06。研究到执行需要有交接边界，但不能越过 Stage6 gate 和 QMT 后续 CR 授权。

**接受影响**：

- `CR030-S07` 依赖 `CR030-S05`、`CR030-S06` 和 CR-019 / CR-025 的只读合同。
- admission status 至少覆盖 pass / warn / fail / blocked。
- QMT handoff 必须写明 not-authorized 和后续 CR 路线。

**不接受影响**：

- 不生成真实 order。
- 不调用 QMT / MiniQMT / XtQuant，不启动 gateway，不查询账户，不写 broker lake。

**备选方案**：

| 方案 | 优点 | 缺点 | 结论 |
|---|---|---|---|
| 生成可执行 order | 链路短 | 安全和授权风险极高 | 不采用 |
| 完全不设计执行 handoff | 范围小 | 断开生产路线衔接 | 不推荐 |

**回写 HLD / Story**：`process/HLD.md` §35.6、§35.8、§35.12；`CR030-S07`、`CR030-S08`。

**回退点**：若用户要求真实 QMT 或 simulation，回退到 CR-020..CR-024 后续 CR，不在 CR-030 直接执行。

## ADR-086：CR-026 Qlib isolated runner 保持后续 Spike candidate

**状态**：Draft for CR-030 CP4 Story Plan

**决策**：CR-026 Qlib isolated runner / qrun / provider_uri / model workflow 不并入 CR-030 P0 实现，也不与 CR-030 CP4 并行启动。CR-026 的启动条件为：`FactorPanelContract`、`LabelWindowSpec`、`ResearchReportCatalog`、runner input/output、failure model、dependency isolation、provider 禁用和 source-of-truth boundary 已由 CR-030 LLD / 实现 / 验证冻结，并由用户单独批准运行和依赖边界。

**理由**：落实 UC-20、UC-21、REQ-184 和 CP3 DQ-CP3-CR030-03 / 07。Qlib 价值在 workflow / recorder / analyzer 生态，但在内部合同未稳定前接入会反向绑架 schema 和事实源。

**接受影响**：

- `CR030-S01` 记录 Qlib reference / optional_spike，不生成 runner。
- `CR030-S08` 记录 CR-026 重启条件和不授权项。
- CP4 不修改 CR tracking 或启动 CR-026。

**不接受影响**：

- 不运行 `/home/hyde/download/qlib`、不调用 qrun、不 import qlib、不使用 provider_uri、不下载数据。
- 不复制 Qlib 源码、示例、测试或数据。

**备选方案**：

| 方案 | 优点 | 缺点 | 结论 |
|---|---|---|---|
| 合并 CR-026 到 CR-030 P0 | 一次性评估 runtime | 扩大权限和依赖，污染 schema | 不采用 |
| 取消 CR-026 | 降低管理成本 | 丢失未来 runner 能力 | 不推荐 |

**回写 HLD / Story**：`process/HLD.md` §35.15、§35.17；`CR030-S01`、`CR030-S08`。

**回退点**：合同冻结且自有 runner 性能 / 表达力不足时，由 meta-po 启动 CR-026 冲突预检、CP2/CP3/CP5 和 per-run 授权。

## ADR-087：CR-020 runtime 分层采用 S 端 Typer CLI、C 端 Typer CLI 验收面和 Python REST client 业务面

**状态**：Approved by CR-020 CP3; active for CP4 Story Plan

**决策**：CR-020 采用分层 runtime：Windows S 端使用 `uv run` Typer Python CLI 管理 gateway lifecycle / login / diagnostics / rollback；Linux C 端使用 `uv run` Typer Python CLI 仅执行 pairing / diagnostics / smoke / CP7 validation；业务 runtime 由 `trading/qmt_client.py` 中的 Python REST client 直接调用 gateway REST API。C 端 CLI 不作为业务 runtime，也不得让策略代码经 shell CLI 调用 gateway。

**理由**：落实 HLD §36、DQ-CP3-CR020-01、DQ-CP3-CR020-02 和 CP2 DQ-CP2-CR020-04 的修订。该分层同时满足双端 CLI 框架一致、业务调用可类型化、超时 / 错误处理可控和 CP7 验收命令稳定。

**接受影响**：

- `CR020-S01` 拥有 S 端 lifecycle CLI 与 gateway runtime 准入边界。
- `CR020-S03` 拥有 C 端 Python REST client 和 C 端 Typer CLI 验收面。
- `CR020-S06` 必须在文档中区分 S 端命令、C 端验收命令和 Python REST runtime。

**不接受影响**：

- 不把 C 端 CLI 作为业务 runtime。
- 不通过 PowerShell / CMD 或 shell wrapper 定义正式业务接口。
- 不在 CP5 前实现、改依赖、启动 gateway 或连接 QMT。

**备选方案**：

| 方案 | 优点 | 缺点 | 结论 |
|---|---|---|---|
| CLI 作为业务 runtime | 命令入口统一 | 类型、超时、错误处理和安全边界弱；违背 CP3 | 不采用 |
| 取消 C 端 CLI | 依赖少 | pairing / diagnostics / CP7 缺少稳定命令面 | 不采用 |

**回写 HLD / Story**：`process/HLD.md` §36.1、§36.3、§36.5、§36.7；`CR020-S01`、`CR020-S03`、`CR020-S06`。

**回退点**：若 Python REST client 不可实现，回退 CP3 重新选择 runtime；若 Typer 与 Windows gateway 或 Linux CLI 不兼容，CP5 前切换 Click / argparse 并重发对应决策。

## ADR-088：Windows gateway 是唯一 QMT 服务端触达点

**状态**：Approved by CR-020 CP3; active for CP4 Story Plan

**决策**：CR-020 中所有 QMT / MiniQMT / XtQuant 触达必须位于 Windows gateway 进程边界内。Linux C 端和业务代码只能通过 Python REST client 调用 gateway REST API，不得导入、调用或直连 XtQuant / QMT SDK。gateway 负责统一承载 session ready、auth middleware、endpoint dispatcher 和 redaction layer。

**理由**：落实 HLD §36.5 至 §36.7、DQ-CP3-CR020-01 和 DQ-CP3-CR020-06。单一服务端触达点可以把 Windows-only / gateway-only 依赖、凭据读取、QMT session 和安全审计隔离在 S 端。

**接受影响**：

- `CR020-S01` 冻结 gateway process boundary、bind / firewall / allowlist / lifecycle。
- `CR020-S02` 在 gateway 内实现 login/session ready gate。
- `CR020-S05` 只在 gateway dispatcher 中解锁 `query_positions`。

**不接受影响**：

- 不允许 Linux C 端导入 XtQuant。
- 不允许策略层绕过 gateway 直连 QMT。
- 不允许 gateway 缺少 auth / redaction / session gate 时转发真实请求。

**备选方案**：

| 方案 | 优点 | 缺点 | 结论 |
|---|---|---|---|
| C 端直连 XtQuant | 链路短 | 污染 Linux runtime，破坏 C/S 边界 | 不采用 |
| 外部 Windows runtime | 依赖隔离最强 | 可审计性和 CP7 标准化较弱 | 作为 CR20-C 回退 |

**回写 HLD / Story**：`process/HLD.md` §36.4、§36.5、§36.6、§36.7；`CR020-S01`、`CR020-S02`、`CR020-S05`。

**回退点**：若 XtQuant 只能以外部运行环境承载，则切换 CR20-C，并保留 C 端 REST contract 与文档运行边界。

## ADR-089：`.env` 凭据策略采用本地未跟踪真实值和 redacted `credential_ref`

**状态**：Approved by CR-020 CP3; active for CP4 Story Plan

**决策**：真实 QMT 登录值只允许保存在本地未跟踪 `.env`；仓库只允许 `.env.example` 占位变量；日志、文档、检查点、Story、LLD、测试证据和对话只能记录 redacted `credential_ref`、hash/ref 或占位名，不得输出账号、密码、token、session、交易密码、私钥或真实私有路径。

**理由**：落实 DQ-CP3-CR020-03、CP2 DQ-CP2-CR020-03 和 HLD §36.1、§36.7、§36.18。用户要求 `.env` 存放账号密码，但项目必须把真实值排除在 Git、日志和检查点之外。

**接受影响**：

- `CR020-S02` 可规划 `.env.example` 占位和 credential_ref 脱敏合同。
- `CR020-S06` 必须写清 `.env` 本地未跟踪和凭据不入库边界。
- CP7 只检查脱敏证据和 forbidden leak 计数，不打印真实值。

**不接受影响**：

- 不读取、打印、解析或校验真实 `.env`。
- 不把 `.env`、`.env.*`、credential files 或真实 secret 作为交付物。
- 不把真实账户敏感信息写入 memory、checkpoint 或报告。

**备选方案**：

| 方案 | 优点 | 缺点 | 结论 |
|---|---|---|---|
| OS secret store | 安全性更高 | 实现和跨平台运维复杂 | 后续安全升级候选 |
| 每次交互输入 | 不落盘 | 不利于服务启动和 CP7 复验 | 仅在 `.env` 风险不可接受时切换 |

**回写 HLD / Story**：`process/HLD.md` §36.1、§36.7、§36.9、§36.13、§36.18；`CR020-S02`、`CR020-S06`。

**回退点**：发现任何真实凭据泄露时立即停止推进、轮转凭据、清理日志，并回退 security redesign。

## ADR-090：登录与 session ready gate 阻断所有只读查询前置

**状态**：Approved by CR-020 CP3; active for CP4 Story Plan

**决策**：gateway 启动后必须完成 QMT / MiniQMT / XtQuant login 和 session ready 判定。`session_ready=false`、login fail、session expired、QMT unavailable 或 `.env` 缺字段时，`query_positions` 必须返回 typed blocked / session_not_ready / transport_error，不得触达 QMT 查询。

**理由**：落实 HLD §36.7、§36.9、§36.11、§36.12 和 DQ-CP3-CR020-01。只读查询触达真实 QMT 前必须证明服务端会话可用且失败路径 fail-closed。

**接受影响**：

- `CR020-S02` 是 `CR020-S05` 的 runtime / session 前置。
- `CR020-S05` 的 endpoint dispatcher 必须消费 session ready gate。
- CP7 需要覆盖 session not ready、login fail 和 rollback 后查询失败。

**不接受影响**：

- 不采用 lazy login 绕过 gateway ready 状态。
- 不在 session not ready 时返回 positions payload。
- 不把 health 可达误写为 QMT session ready。

**备选方案**：

| 方案 | 优点 | 缺点 | 结论 |
|---|---|---|---|
| lazy login on first query | 启动更快 | 查询路径承担凭据和登录失败风险 | 不采用 |
| health-only | 风险最低 | 不满足 CR-020 最小只读闭环 | 回退治理备选 |

**回写 HLD / Story**：`process/HLD.md` §36.9、§36.10、§36.11、§36.12；`CR020-S02`、`CR020-S05`。

**回退点**：若 QMT login/session ready 不稳定且无法 fail-closed，回退 CR20-B health/login only 或转 Spike。

## ADR-091：HMAC / allowlist / scope / nonce / redaction 全部 fail-closed

**状态**：Approved by CR-020 CP3; active for CP4 Story Plan

**决策**：CR-020 真实只读 gateway 默认启用 pairing_hmac，allowlist 必填，scope 按 endpoint 校验，nonce / timestamp 防重放，redaction 同时覆盖响应、错误、日志和 diagnostics。缺 header、签名错误、timestamp 超窗、nonce replay、source 不在 allowlist、scope 不足或 redaction 失败时均 blocked，且不得触达 QMT。

**理由**：落实 DQ-CP3-CR020-04 和 HLD §36.3、§36.7、§36.9、§36.12。CR-020 触达真实只读 QMT API，必须同时具备身份、来源、权限和脱敏控制。

**接受影响**：

- `CR020-S04` 是 `CR020-S05` 的安全前置。
- `CR020-S03` 必须支持 HMAC header、timeout 和 typed blocked result。
- `CR020-S06` 必须把 wrong scope / replay / allowlist miss / redaction fail 写入 CP7 验收边界。

**不接受影响**：

- no-auth 只能用于 fixture / local_debug，不得连接真实 QMT readonly。
- HMAC pass 不等于交易、账户写入、simulation 或 live 授权。
- redaction 失败不得降级为原文输出。

**备选方案**：

| 方案 | 优点 | 缺点 | 结论 |
|---|---|---|---|
| no-auth local only | 简单 | 真实 readonly 风险不可接受 | 不采用 |
| HMAC only | 调用方身份强 | 缺少网络来源和 scope 边界 | 不采用 |

**回写 HLD / Story**：`process/HLD.md` §36.3、§36.7、§36.9、§36.12、§36.13；`CR020-S03`、`CR020-S04`、`CR020-S05`、`CR020-S06`。

**回退点**：任一安全门无法稳定验证时，CP7 FAIL 并停机回滚；仅 fixture/local_debug 可局部豁免且不得连接 QMT。

## ADR-092：`query_positions` 是 CR-020 唯一真实只读查询接口

**状态**：Approved by CR-020 CP3; active for CP4 Story Plan

**决策**：CR-020 只解锁 `POST /qmt/account/positions` / `query_positions`，scope 固定为 `qmt:positions:read`。除 health / capabilities / diagnostics 外，其他 QMT 查询、account、orders、trades、simulation、live、submit、cancel、account_write、broker_lake_write 均保持 blocked / later-gated，不进入本轮默认白名单。

**理由**：落实 DQ-CP3-CR020-05 和 HLD §36.1、§36.7、§36.10、§36.14。`query_positions` 足以证明真实 QMT 只读连接闭环，同时限制敏感数据面和脱敏范围。

**接受影响**：

- `CR020-S05` 是唯一 endpoint 解锁 Story。
- `CR020-S04` 的 scope registry 必须能表达 `qmt:positions:read`。
- `CR020-S06` 必须声明其他 endpoint 后置或另起 CR。

**不接受影响**：

- 不将 `query_account`、orders、trades 或 simulation endpoint 纳入本轮。
- 不把 account query 或 positions payload 写成交易准入证据。
- 不允许未脱敏 positions payload 进入日志、报告或检查点。

**备选方案**：

| 方案 | 优点 | 缺点 | 结论 |
|---|---|---|---|
| `query_account` | 可替代证明只读连接 | 需重发接口决策，敏感度仍高 | 回退候选 |
| health-only | 风险低 | 不满足至少一个查询接口目标 | 治理回退 |

**回写 HLD / Story**：`process/HLD.md` §36.1、§36.7、§36.10、§36.14、§36.17；`CR020-S05`、`CR020-S06`。

**回退点**：若 positions API 不稳定或无法脱敏，回退 CP3 改为 `query_account` 或收窄 health-only。

## ADR-093：S 端 gateway / XtQuant 依赖隔离，CP5 前不改依赖

**状态**：Approved by CR-020 CP3; active for CP4 Story Plan

**决策**：CR-020 在 CP4 只冻结依赖隔离策略：S 端 gateway / QMT / XtQuant / server 依赖必须与 Linux C 端主业务 runtime 隔离；C 端只消费 Python REST client 和验收 CLI。CP5 前 `implementation_allowed=false` 且 `dependency_change_allowed=false`；CP5 LLD 再决定 extras / group / external Windows runtime 的具体落地。

**理由**：落实 DQ-CP3-CR020-06、DQ-CP3-CR020-07 和 HLD §36.8、§36.12、§36.13。Windows-only / gateway-only 依赖污染 Linux 主环境会破坏研究主路径和 CI 兼容性。

**接受影响**：

- `CR020-S01`、`CR020-S02`、`CR020-S04` 只能在 CP5 LLD 中细化 S 端依赖隔离方案。
- `CR020-S03` 的 Linux C 端 runtime 不承载 XtQuant / gateway server 依赖。
- `CR020-S06` 必须记录分平台安装 / 运行边界和 CP5 前不改锁。

**不接受影响**：

- 本轮不修改 `pyproject.toml` 或 `uv.lock`。
- 不把 XtQuant / gateway server 依赖加入 Linux C 端主依赖。
- 不把 CP3 / CP4 通过解释为依赖安装授权或 gateway 启动授权。

**备选方案**：

| 方案 | 优点 | 缺点 | 结论 |
|---|---|---|---|
| 主依赖统一安装 | 简单 | 污染 Linux C 端，兼容风险高 | 不采用 |
| 完全外部 Windows runtime | 依赖最干净 | 审计和 CP7 标准化较弱 | 作为 CR20-C 回退 |

**回写 HLD / Story**：`process/HLD.md` §36.3、§36.8、§36.12、§36.13、§36.17；`CR020-S01`、`CR020-S02`、`CR020-S03`、`CR020-S06`。

**回退点**：隔离不可行时切换外部 Windows runtime；Typer 不兼容时切 Click / argparse；任何依赖变更必须等 CP5 LLD 批次人工确认。

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
| AD-Q50 | 是否接受 CR-017 复权公式、provider 因子方向、qfq as-of 和异常价格解释 | 已接受；方向不明时禁止实现，qfq 缺 as-of 时 quality fail | ADR-053、HLD-DATA-LAKE §18、Q-030、`checkpoints/CP3-CR015-CR016-CR017-HLD-REVIEW.md` | APPROVED_CP3 |
| AD-Q51 | 是否接受 CR-017 独立 dataset/view schema、旧 qfq 只读保留和 migration summary | 已接受；不在同一 `prices` frame 混存 raw/qfq/hfq，不覆盖旧 qfq | ADR-054、HLD-DATA-LAKE §18、Q-031、`checkpoints/CP3-CR015-CR016-CR017-HLD-REVIEW.md` | APPROVED_CP3 |
| AD-Q52 | 是否接受 QMT 接入采用 Windows QMT 节点 + OMS + adapter，策略不得直连 QMT | 已接受；adapter 是唯一 broker 触达点，策略层 QMT API 调用次数为 0 | ADR-055、HLD-QMT-TRADING、Q-038、`checkpoints/CP3-CR015-CR016-CR017-HLD-REVIEW.md` | APPROVED_CP3 |
| AD-Q53 | 是否接受 broker lake 外置、schema、retention、redaction 与研究数据湖隔离 | 已接受；未授权真实写入时 broker_lake_writes=0，后续只写外置 root | ADR-056、HLD-QMT-TRADING、Q-032、`checkpoints/CP3-CR015-CR016-CR017-HLD-REVIEW.md` | APPROVED_CP3 |
| AD-Q54 | 是否接受 OMS 状态机和 QMT / mock event 映射 | 已接受；unknown / timeout 不自动成功，partial fill、撤单失败进入状态机和 manual_review | ADR-057、HLD-QMT-TRADING、Q-033、`checkpoints/CP3-CR015-CR016-CR017-HLD-REVIEW.md` | APPROVED_CP3 |
| AD-Q55 | 是否接受 pre-trade hard risk gate 规则、阈值、配置位置和失败行为 | 已接受；任一规则失败 adapter_calls=0，warn-only 不可用 | ADR-058、HLD-QMT-TRADING、Q-034、`checkpoints/CP3-CR015-CR016-CR017-HLD-REVIEW.md` | APPROVED_CP3 |
| AD-Q56 | 是否接受 QMT staged activation 准入、退出和回退阈值 | 已接受；阶段不可跳过，CR-017 未验证前阻断生产策略复权治理声明和资金放大 | ADR-059、HLD-QMT-TRADING、Q-035、`checkpoints/CP3-CR015-CR016-CR017-HLD-REVIEW.md` | APPROVED_CP3 |
| AD-Q57 | 是否接受 T+1 限价 / 保护价、撤单重试、对账阈值和 kill switch | 已接受；保护带可配置，自动重试上限为 1，kill switch 停止新单、撤可撤单、冻结策略 | ADR-060、HLD-QMT-TRADING、Q-036/Q-037、`checkpoints/CP3-CR015-CR016-CR017-HLD-REVIEW.md` | APPROVED_CP3 |
| AD-Q58 | 是否接受 Linux 研究节点与 Windows QMT 节点通信、鉴权、隔离和运维责任方案 | 已接受 signed file drop + ack/error enum 为保守默认，本地 RPC 后续评估 | ADR-061、HLD-QMT-TRADING、Q-038、`checkpoints/CP3-CR015-CR016-CR017-HLD-REVIEW.md` | APPROVED_CP3 |
| AD-Q59 | 是否接受 CR-018 current truth release scope 采用 `2015-01-05..latest_closed_trade_date` 的 scoped release | 已由 CP2 D1 批准；CP3 只复核其在 HLD/ADR/Story Plan 中是否一致落地 | ADR-062、`process/HLD-DATA-LAKE.md` §19、`checkpoints/CP2-CR018-PRODUCTION-DATA-LAKE-CLOSURE-DECISION-BRIEF.md` D1 | APPROVED_CP2_PENDING_CP3_REVIEW |
| AD-Q60 | 是否接受 P0/P1 dataset group 与四类 benchmark group | 已由 CP2 D2/D3/D4 批准；P0 阻断 production current truth，P1 阻断中性化、纯 alpha、容量和 scale_up 声明 | ADR-063、ADR-064、REQ-126..REQ-129、REQ-135、REQ-136 | APPROVED_CP2_PENDING_CP3_REVIEW |
| AD-Q61 | 是否接受 Explicit Publish Gate 采用 release-level 总门、dataset-level 明细和 release-level rollback | 已由 CP2 D5 批准；publish 不得由 validate 自动触发，rollback 不做 dataset 局部漂移 | ADR-065、REQ-124、REQ-131、REQ-132 | APPROVED_CP2_PENDING_CP3_REVIEW |
| AD-Q62 | 是否接受 publish 后研究重跑 PASS 是 QMT simulation / live_readonly / small_live / scale_up 的前置 | 已由 CP2 D6 批准；CR015/016/017 的 QMT foundation 不等于策略可进入 QMT 阶段 | ADR-066、REQ-123、REQ-133、REQ-134、`process/HLD.md` §32 | APPROVED_CP2_PENDING_CP3_REVIEW |
| AD-Q63 | 是否接受 CR018-S01..S09 Story Plan 与 4 个 Wave 作为 CP3 通过后的 CP4/CP5 输入 | 默认接受；9 个 Story 覆盖 scope/dataset/readiness/publish/rollback/research rerun/QMT admission，LLD 批次为 `CR018-PRODUCTION-DATA-LAKE-CLOSURE-BATCH-A` | `process/STORY-BACKLOG.md` CR018 增量、`process/DEVELOPMENT-PLAN.yaml` CR018 waves、`process/checks/CP4-CR018-STORY-DAG-PARALLEL-SAFETY.md` | PENDING_CP3_REVIEW |
| AD-Q64 | 是否接受阶段六 admission 采用新多因子 gate + 多基准看板 + primary benchmark，且不得包装旧失败策略 | 默认接受；旧 production rerun fail 只能作为 blocked evidence，admission pass/fail 以 primary benchmark、风险约束和 blocked claims 为主 | ADR-067、REQ-138、REQ-144、REQ-154、Q-040 | PENDING_CP3_REVIEW |
| AD-Q65 | 是否接受 QMT C/S bridge 主选替代 ADR-061 的 signed file drop 默认通信 | 默认接受；C 侧位于 local_backtest，S 侧为 Windows FastAPI gateway；signed file drop 只作 fallback | ADR-068、ADR-061 增量说明、REQ-145、REQ-149、REQ-159 | PENDING_CP3_REVIEW |
| AD-Q66 | 是否接受 C 侧接口采用 Python client / 函数调用为主 + 薄 CLI | 默认接受；内部策略、OMS、admission dry-run 和测试使用 typed Python client，CLI 仅用于 smoke / ops / script wrapper | ADR-069、REQ-160、Q-044 | PENDING_CP3_REVIEW |
| AD-Q67 | 是否接受完整 QMT endpoint matrix 与运行门控分离 | 默认接受；health/capabilities、validate/dry-run、行情、账户、持仓、委托、成交、simulation、live、reconciliation、kill-switch 接口类别完整，但真实转发由 run mode / stage / risk / kill-switch / authorization 控制 | ADR-070、REQ-146、REQ-147、Q-041 | PENDING_CP3_REVIEW |
| AD-Q68 | 是否接受配对式 token/HMAC 默认启用，no-auth 仅 debug / fixture / 显式临时 | 默认接受；C 侧 pairing request，S 侧管理员 list / approve，C 侧 pair complete；后续请求使用 client id、timestamp、nonce、HMAC signature；HMAC 通过后仍继续运行门控 | ADR-071、REQ-148、REQ-151、Q-039、CP3-CR019-DQ-04 | PENDING_CP3_REVIEW |
| AD-Q69 | 是否接受 FastAPI fallback 只 blocked-only 或人工 dry-run / signed file drop，不自动真实 QMT | 默认接受；gateway 不可达、鉴权失败、heartbeat fail 或部署不满足时 fail closed | ADR-072、REQ-145、REQ-150、Q-042 | PENDING_CP3_REVIEW |
| AD-Q70 | 是否接受 Backtrader、Qlib、minute、Level2 均后置触发，不进入阶段六 P0 | 默认接受；Backtrader W6、Qlib W7、minute/Level2 Spike 后置，需触发条件和后续 CR / CP | ADR-073、REQ-139..143、REQ-155..158、Q-043 | PENDING_CP3_REVIEW |
| AD-Q71 | 是否接受 CR-025 Backtrader 默认定位为 optional semantic reference，不替代 lightweight 主路径 | 默认接受；Backtrader 只作为 design reference / research comparison，未选择或未安装时 lightweight 继续运行 | ADR-074、REQ-161、REQ-166、REQ-167、HLD §34 | PENDING_CP3_REVIEW |
| AD-Q72 | 是否接受 CR-025 Backtrader 模块处理矩阵和默认无源码级移植推荐 | 默认接受；`reference_only` / `adapt_interface` / `exclude` 为主，`migration_candidate` 当前为空 | ADR-075、REQ-173、HLD §34.5 | PENDING_CP3_REVIEW |
| AD-Q73 | 是否接受 GPLv3 源码级移植治理：默认 no-copy，例外需 CP3/CP5 双门控和合规确认 | 默认接受；CP5 前不得复制、裁剪、改写或移植 Backtrader 源码 | ADR-076、REQ-172、RA-066 | PENDING_CP3_REVIEW |
| AD-Q74 | 是否接受 CR-025 clean feed gate 与 semantic diff schema | 默认接受；gate 覆盖 PIT / available_at / 复权 / benchmark / tradability / cost / quality，diff 覆盖成交、现金、成本、净值和差异原因 | ADR-074..076、REQ-163、REQ-164、HLD §34.6 | PENDING_CP3_REVIEW |
| AD-Q75 | 是否接受 order intent draft 字段和 QMT route 边界 | 默认接受；CR-025 只输出 `order_intent_draft_v1`，不启动 gateway / simulation / live / broker lake | ADR-077、REQ-169、REQ-171、HLD-QMT-TRADING §18 | PENDING_CP3_REVIEW |
| AD-Q76 | 是否确认 CR-025 CP3 不授权实现、依赖变更、Backtrader 运行、源码迁移或真实操作 | 默认接受；所有真实 broker/QMT/provider/lake/publish/credential 计数目标为 0，且不授权多因子研究闭环实现 | ADR-074..078、REQ-165、REQ-168 | PENDING_CP3_REVIEW |
| AD-Q77 | 是否确认多因子研究闭环另起后续 CR，不并入 CR-025 CP5 | 默认接受；CR-025 只处理执行语义对齐、semantic diff、`order_intent_draft_v1` 与 no-copy / no-real-operation，FactorSpec、FactorRunSpec、IC / RankIC、分层收益、多因子组合、实验追踪和策略准入包后续参考 Qlib / Alphalens / vnpy.alpha 单独评审 | ADR-078、HLD §34、CR025-S02/S04/S06 | PENDING_CP5_REFRESH |
| AD-Q78 | 是否接受 CR-030 Story Plan 采用 8 个 Story、4 个 Wave 和 1 个全量 LLD 批次 | 默认接受：S01 外部矩阵 / 总合同，S02 因子定义 / 运行规格，S03 面板 / 标签，S04 单因子评价，S05 多因子组合，S06 manifest/catalog，S07 admission/handoff，S08 安全验证 / 文档；LLD 批次为 `CR030-MULTIFACTOR-RESEARCH-LOOP-BATCH-A` | ADR-079..086、HLD §35.17、UC-20..UC-27、REQ-174..185 | CP4_AUTO_PASS_PENDING_CP5 |
| AD-Q79 | 是否接受 CR-030 CP5 前 implementation_allowed=false 且真实操作执行计数为 0 | 默认接受；本轮只做 Story Plan / CP4，不做 LLD、不实现、不改依赖、不运行外部项目、不触发 provider/lake/publish/QMT/simulation/live、不读取凭据 | ADR-079..086、REQ-182、CP3 DQ-CP3-CR030-05 | CP4_AUTO_PASS_PENDING_CP5 |
| AD-Q80 | 是否接受 CR-026 Qlib runner 继续后置，且 optimizer / ML workflow / vectorbt / PyBroker / RQAlpha / vn.py 均不进入 CR-030 P0 | 默认接受；合同冻结后由 meta-po 单独启动 CR-026 或 bounded Spike，重新走冲突预检、CP2/CP3/CP5 和运行授权 | ADR-080、ADR-083、ADR-086、REQ-184 | CP4_AUTO_PASS_PENDING_CP5 |
| AD-Q81 | 是否接受 StrategyAdmissionPackage 只输出研究准入证据和 `order_intent_draft_v1` 草稿，不构成 QMT / simulation / live 授权 | 默认接受；CR-020..CR-024 仍需独立 CR 和 per-run authorization，`qmt_api_call`、`real_order`、`account_query` 均为 0 | ADR-085、REQ-181、REQ-182、CP3 DQ-CP3-CR030-06 | CP4_AUTO_PASS_PENDING_CP5 |
| AD-Q82 | 是否接受 CR-020 Story Plan 采用 6 个 Story、4 个 Wave 和 1 个全量 LLD 批次 | 默认接受：S01 Windows gateway runtime / admission，S02 Server QMT login / session，S03 Linux client REST transport，S04 HMAC pairing / allowlist / scope，S05 `query_positions` read-only，S06 docs / runbook / CP7 real-machine validation；LLD 批次为 `CR020-QMT-GATEWAY-READONLY-BATCH-A` | ADR-087..093、HLD §36.17、CP3 DQ-CP3-CR020-01..07 | CP4_AUTO_PASS_PENDING_CP5 |
| AD-Q83 | 是否接受 CR-020 CP5 前 `implementation_allowed=false` 且不授权 LLD、实现、依赖变更或运行 | 默认接受；本轮只做 Story Plan / CP4，不做 LLD、不实现、不改 `pyproject.toml` / `uv.lock`、不启动 gateway、不绑定端口、不连接 QMT / MiniQMT / XtQuant、不读取真实 `.env`、不输出凭据、不交易、不账户写入、不 simulation/live、不 provider/lake/publish/reports overwrite | ADR-087、ADR-089、ADR-093、CP3 DQ-CP3-CR020-01、DQ-CP3-CR020-07 | CP4_AUTO_PASS_PENDING_CP5 |
| AD-Q84 | 是否接受 `query_positions` 是 CR-020 唯一真实只读查询接口，scope 固定为 `qmt:positions:read` | 默认接受；health/session/capabilities 仅服务准入，其他 QMT endpoint、订单、撤单、改单、账户写入、simulation/live 和 broker lake 写入均保持 blocked / later-gated | ADR-090、ADR-091、ADR-092、HLD §36.4、§36.9、§36.11、CP3 DQ-CP3-CR020-05 | CP4_AUTO_PASS_PENDING_CP5 |
| AD-Q85 | 是否接受 `.env` 使用本地未跟踪真实值和 redacted `credential_ref` 策略 | 默认接受；Story、LLD、日志、报告、runbook、CP7 evidence 只允许 placeholder / `credential_ref`，不得读取、打印、解析、校验或泄露账号、密码、token、session、交易密码、私钥或真实私有路径 | ADR-089、ADR-090、ADR-091、HLD §36.9、CP3 DQ-CP3-CR020-03 | CP4_AUTO_PASS_PENDING_CP5 |
| AD-Q86 | 是否接受 HMAC / allowlist / scope / nonce / redaction 全部 fail-closed，并将 CP7 实机验收限定为只读持仓查询证据 | 默认接受；鉴权失败、allowlist 不匹配、scope 不足、nonce replay、session not ready、日志脱敏失败时 adapter call / query / real operation 均为 0；CP7 只验证 Windows S 端 + Linux C 端的只读持仓查询链路，不构成交易或账户写入授权 | ADR-091、ADR-092、HLD §36.10、§36.11、§36.14、CP3 DQ-CP3-CR020-04、DQ-CP3-CR020-06 | CP4_AUTO_PASS_PENDING_CP5 |

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
| 2026-05-27 | 按 CR-015 / CR-016 / CR-017 新增 ADR-053 至 ADR-061，并补齐设计确认点 AD-Q50..AD-Q58 | 用户已批准三张 CR 的 CP2 需求基线，要求在 CP3 前输出 HLD / ADR、冻结 Q-030..Q-038 决策输入 | 需要由 meta-po 发起 CR-015/016/017 CP3 人工审查；CP3 approve 前不得拆 Story、写 LLD 或实现；本轮不授权真实抓取、真实写湖、QMT API 调用、真实发单、撤单、账户写操作、账户查询、凭据读取或依赖修改 |
| 2026-05-28 | 回填 CR-015 / CR-016 / CR-017 CP3 审批结果，AD-Q50..AD-Q58 更新为 APPROVED_CP3 | 用户回复“通过审批，可以按照推荐方案组织子 agent 推进项目” | 允许进入 Story Plan / CP4；仍不授权 LLD、代码实现、真实抓取、真实写湖、QMT API 调用、真实发单、撤单、账户写操作、账户查询、凭据读取或依赖修改 |
| 2026-05-29 | 按 CR-018 新增 ADR-062 至 ADR-066，并补齐设计确认点 AD-Q59..AD-Q63 | 用户要求基于 CR018 已确认需求生成 solution-design 与 story-planning 产物，重点关闭 production current truth、P0/P1 dataset、publish/rollback、research rerun 和 QMT 后置 | 需要由 meta-po 发起 CR-018 CP3 人工审查；CP3 approve 前不得进入 LLD；本轮不授权 provider fetch、真实 lake 写入、publish current pointer、QMT 启动、代码/测试修改、凭据读取或依赖变更 |
| 2026-05-30 | 按 CR-019 新增 ADR-067 至 ADR-073，并补齐设计确认点 AD-Q64..AD-Q70 | 用户要求阶段六多因子 admission 和 QMT 独立 C/S 模块进入 CP3；重点冻结 C 侧 Python client / 薄 CLI、Windows FastAPI gateway、完整 endpoint matrix、运行门控、鉴权、fallback 和后置能力边界 | 需要由 meta-po 发起 CR-019 CP3 人工审查；CP3 approve 前不得进入 Story Plan、LLD 或实现；本轮不授权 FastAPI 实现、依赖变更、真实 QMT / provider / lake / broker 操作或 simulation/live run |
| 2026-05-30 | 按 CR-019 CP3 DQ-04 用户修订更新 ADR-071 / AD-Q68 | 用户选择配对式 token/HMAC 默认启用；no-auth 仅允许本机 debug、fixture 测试或显式配置的临时模式；HMAC 不替代运行门控 | 需要 meta-po 重新发起或刷新 CR-019 CP3 人工审查；CP3 仍 pending；本轮仍不授权实现、依赖、服务、凭据或真实 QMT 操作 |
| 2026-06-01 | 按 CR-025 新增 ADR-074 至 ADR-077，并补齐设计确认点 AD-Q71..AD-Q76 | 用户批准 CR-025 CP2 并要求 meta-se 分析本地 Backtrader GPLv3 项目的模块级借鉴 / 适配 / 移植候选 / 禁止移植边界 | 需要由 meta-po 发起 CR-025 CP3 人工审查；CP3 approve 前不得进入 Story Plan、LLD 或实现；本轮不授权 Backtrader 运行、源码复制 / 移植、依赖变更、真实 broker / QMT / provider / lake / publish / simulation / live 或凭据读取 |
| 2026-06-02 | 按 CR-025 CP5 前定位澄清新增 ADR-078，并修订 ADR-074 / ADR-075 | 用户确认系统核心定位是多因子策略研究和回测，Backtrader 只作为 lightweight execution engine 的执行语义参考 | 保持 CR025 6 Story / 4 Wave / 1 LLD batch 不变；meta-dev 需刷新受影响 LLD 文案，meta-po 需更新 CP5 Decision Brief / launch message，明确多因子研究闭环另起后续 CR |
| 2026-06-03 | 按 CR-030 CP3 approved 口径新增 ADR-079 至 ADR-086 与 AD-Q78..AD-Q81 | 用户已同意 CP3 DQ-CP3-CR030-01..07 的全部推荐方案，允许进入 story-planning / CP4 | 允许追加 CR030-S01..S08 Story Plan、DAG、文件所有权和 CP4 自动预检；CP5 全量 LLD 确认前仍不得实现、改依赖、运行外部项目、provider/lake/publish、QMT/simulation/live 或读取凭据 |
| 2026-06-05 | 按 CR-020 CP3 approved 口径新增 ADR-087 至 ADR-093 与 AD-Q82..AD-Q86 | 用户已同意 CP3 DQ-CP3-CR020-01..07 的全部推荐方案，允许进入 story-planning / CP4 | 允许追加 CR020-S01..S06 Story Plan、DAG、文件所有权和 CP4 自动预检；CP5 全量 LLD 确认前仍不得创建 LLD、实现、改依赖、启动 gateway、绑定端口、连接 QMT / MiniQMT / XtQuant、读取真实 `.env`、输出凭据、交易、账户写入、simulation/live、provider/lake/publish 或覆盖 reports |
