---
status: confirmed
version: "1.16"
confirmed: true
confirmed_by: "user"
confirmed_at: "2026-06-13T22:03:22+08:00"
ready_for_design: true
source_use_cases: [UC-01, UC-02, UC-03, UC-04, UC-05, UC-06, UC-07, UC-08, UC-09, UC-10, UC-11, UC-12, UC-13, UC-14, UC-15, UC-16, UC-17, UC-18, UC-19, UC-20, UC-21, UC-22, UC-23, UC-24, UC-25, UC-26, UC-27, UC-28, UC-29, UC-30, UC-31, UC-32]
review_round: 11
---

# 结构化需求

## 修订记录

| 版本 | 日期 | 修订人 | 变更要点 | 文档处理方式 |
|----|------|--------|----------|--------------|
| 1.0 | 2026-05-13 | meta-pm | 从用户 `/init` 输入和 `USE-CASES.md` 提取初始需求基线 | 初始化基线 |
| 1.1 | 2026-05-13 | meta-pm | 根据 Review Round 1 补齐工程根、路径归属、parquet schema、无前视偏差、成本模型、扫描报告、候选清单、聚宽边界和偏差披露需求 | 在既有 draft 上增量修订，保留 REQ-001 至 REQ-020 编号并新增 REQ-021 起的补充需求 |
| 1.2 | 2026-05-14 | meta-pm | 根据需求刷新分派补齐复权口径一致、T 日收盘后信号/T+1 成交、`available_at <= decision_time`、历史窗口不足剔除、缺失价格/无成交处理、非 PIT 股票池、报告 metadata 限制项和后续真实性增强需求 | 需求确认前增量修订，保留既有编号并新增 REQ-037 起的补充需求，不改变 draft / ready 状态 |
| 1.3 | 2026-05-14 | meta-pm | 根据数据源限速刷新分派补齐独立数据准备、请求节流、有限重试退避、断点续传、raw 缓存、增量更新、最近 N 个交易日回补、manifest、质量报告、失败降级和回测主路径离线硬约束 | 需求确认前增量修订，保留既有编号并新增 REQ-047 起的补充需求，不改变 draft / ready 状态 |
| 1.4 | 2026-05-17 | meta-pm | 按 CR-005 第三轮评审补齐 `hs300_index` 本地 benchmark、Tushare 写湖补齐作业、structured `unavailable/required_missing`、`next_action` / `remediation_job_spec`、benchmark 口径、coverage / quality / gap explanation、consumer no-network/no-connector 和 Backtrader optional backend 边界 | CR-005 原文档增量更新；保留 REQ-001 至 REQ-058 旧基线，新增 REQ-059 至 REQ-070 并建立 CR005-AC 追溯 |
| 1.5 | 2026-05-23 | meta-pm | 按 CR-011 增量补齐生产级因子研究数据需求，覆盖真实 benchmark、PIT 股票池、可交易性、执行价、复权/公司行动、行业市值风格、流动性容量成本、因子审计面板、稳健性验证、报告声明门控和真实数据授权/凭据边界 | CR-011 原文档增量更新；保留 REQ-001 至 REQ-070 旧基线，新增 REQ-071 至 REQ-082 并回链 UC-08 与 CR-011 旧基线映射 |
| 1.6 | 2026-05-25 | meta-pm | 按 CR-013 增量补齐 unsupported data 与 claim boundary，覆盖 2020-2024 full-history 不得外推、真实 VWAP / 分钟执行价 blocked、unsupported register 进入用户文档和报告声明边界、provider/lake/credential/old data 权限未授权 | CR-013 原文档增量更新；保留 REQ-001 至 REQ-082 旧基线，新增 REQ-083 至 REQ-087 并回链 UC-08 与 CR-013 旧基线映射 |
| 1.7 | 2026-05-26 | meta-pm | 按 CR-014 增量补齐 A 股 since-inception-to-current-trading-day 生产级全历史数据湖需求，覆盖全 A current truth、证券生命周期、P0 dataset 分层、catalog current pointer、增量刷新 / replay、DuckDB 只读查询审计候选、权限 / 凭据 / 真实写湖边界、claim boundary 和可量化验收 | CR-014 原文档增量更新；保留 REQ-001 至 REQ-087 旧基线，新增 REQ-088 至 REQ-097 并回链 UC-09 与 CR-014 旧基线映射；本增量待 CP2 用户确认 |
| 1.8 | 2026-05-27 | meta-pm | 按 CR-015 / CR-016 / CR-017 增量补齐 QMT 交易接入 foundation、模拟盘 / 实盘阶段激活和复权双视图需求，覆盖 raw/qfq/hfq/returns_adjusted、qfq as-of、QMT raw 执行价格、OMS / adapter / broker lake / pre-trade risk、runbook、对账、kill switch、per-run 授权和凭据脱敏 | CR-015 / CR-016 / CR-017 原文档增量更新；保留 REQ-001 至 REQ-097 旧基线，新增 REQ-098 至 REQ-122 并回链 UC-10 至 UC-12 与 CP2 intake approved 决策 |
| 1.9 | 2026-05-29 | meta-pm / meta-po | 按 CR-018 增量补齐数据湖 production current truth 闭环需求，覆盖 CR014 S14 candidate 输入事实、PIT/W3/benchmark/复权派生、quality/readiness、Explicit Publish Gate、rollback、发布后研究重跑和 QMT 后置门控 | CR-018 原文档增量更新；保留 REQ-001 至 REQ-122 旧基线，新增 REQ-123 至 REQ-137，并回链 UC-13 至 UC-14 与用户 D1-D6 批准结论 |
| 1.10 | 2026-05-30 | meta-pm | 按 CR-019 增量补齐阶段六多因子模拟盘准入、Windows QMT FastAPI bridge、D1-D7、stage gate、per-run authorization、fallback、日志脱敏、安全默认值和后置触发条件 | CR-019 原文档增量更新；保留 REQ-001 至 REQ-137 旧基线，新增 REQ-138 至 REQ-158，并回链 UC-15 至 UC-18 与用户 D1-D7 批准结论 |
| 1.11 | 2026-05-30 | meta-po | 按用户补充修订 CR-019：Q40 采用多基准 + primary benchmark 推荐方案；QMT 模块必须为独立 C/S 模块，C 侧位于 local_backtest 并暴露统一 Python 接口，S 侧部署在 Windows 并通过 REST 转换为 QMT 接口调用；C 侧接口形态进入 CP2 / CP3 决策 | CR-019 原文档增量更新；保留 REQ-001 至 REQ-158，新增 REQ-159 至 REQ-160，并回链 UC-16 至 UC-17 |
| 1.12 | 2026-05-31 | meta-pm | 按 CR-025 增量补齐 Backtrader optional execution backend hardening 需求，覆盖可选后端范围、依赖隔离、clean feed、执行语义差异报告、轻量主路径回归、安全计数、无真实 broker/QMT/provider/lake/publish 授权和 CP5 前不得实现 | CR-025 原文档增量更新候选；保留 REQ-001 至 REQ-160 旧基线，新增 REQ-161 至 REQ-168，并回链 UC-19；本增量待 CP2 人工确认 |
| 1.13 | 2026-05-31 | meta-po | 按用户 CP2 修改意见将 CR-025 目标从框架级 Backtrader/lightweight 讨论修订为 production-grade research-to-execution 路线：研究可信度、回测 / 模拟一致性、QMT 生产执行三条主线；Backtrader 仅作为 optional execution realism / semantic reference，新增 research output 到 target portfolio / order intent 的衔接要求 | CR-025 原文档增量修订；保留 REQ-001 至 REQ-168 旧基线，修订 REQ-161 说明并新增 REQ-169 至 REQ-172；本增量待 CP2 人工确认 |
| 1.14 | 2026-06-01 | meta-po | 用户批准 CR-025 CP2，并追加 CP3/HLD 约束：meta-se 必须分析本地 Backtrader 项目 `/home/hyde/download/backtrader`，形成模块级借鉴 / 适配 / 移植候选 / 禁止移植对比；任何源码级移植只能作为 HLD 决策项，不构成 CP2 或 CP3 默认实现授权 | CR-025 需求基线确认；保留 REQ-001 至 REQ-172，修订 REQ-172 并新增 REQ-173；进入 CP3/HLD |
| 1.15 | 2026-06-03 | meta-po | 用户授权进入 CR-030 HLD，回填多因子研究框架借鉴与研究闭环标准化需求，覆盖外部项目借鉴矩阵、项目自有 schema、FactorSpec / FactorRunSpec、FactorPanel / LabelWindow、评价报告、多因子组合、ExperimentManifest / ReportCatalog、StrategyAdmissionPackage、CR-026 分流和不授权边界 | CR-030 需求基线确认；保留 REQ-001 至 REQ-173，新增 REQ-174 至 REQ-185；进入 CP3/HLD，不授权实现、依赖变更、外部项目运行、源码迁移、provider/lake/publish、QMT/simulation/live 或凭据读取 |
| 1.16 | 2026-06-13 | meta-po | 按 CR-046 增量补齐 QMT / MiniQMT 双目标策略交付框架需求，覆盖 framework-first 范围、策略核心合同、QMT terminal target、MiniQMT runner 安装设计、验证框架、后续 CR 分流和研究框架反向约束 | CR-046 原文档增量更新；保留 REQ-001 至 REQ-185，新增 REQ-186 至 REQ-200；用户已于 2026-06-13T22:03:22+08:00 通过 CP2；不授权具体策略交付、QMT 运行验证、MiniQMT 连接、submit/cancel、simulation/live、provider/lake/publish 或凭据读取 |

## 需求上下文

| 字段 | 当前口径 |
|---|---|
| 工程根 | 当前仓库根 `/home/hyde/workspace/local_backtest` |
| 第一版运行边界 | 本地离线执行，回测、参数扫描、候选筛选和本地差异分析主路径只读当前仓库根下标准化 parquet、manifest 和必要 metadata |
| 数据准备边界 | AKShare 等远程数据源拉取只能存在于独立数据准备/更新流程；该流程不属于回测主路径，并必须负责限速、节流、有限重试退避、断点续传、raw 缓存、标准化派生、manifest 和质量报告 |
| 联网边界 | 联网能力只能存在于独立数据准备/更新流程；回测、扫描、候选筛选和差异分析不得请求 AKShare、聚宽或其他远程接口 |
| CR-005 Tushare 边界 | “数据层调用 Tushare”仅指 `market_data` 写湖 / 数据准备层在用户显式命令下调用 Tushare 并写入本地数据湖；不指 `engine/data_loader.py`、实验入口、benchmark resolver 或 Backtrader 自动联网 |
| CR-005 benchmark 边界 | `hs300_index` 是本地 canonical/gold benchmark 数据集；缺失或质量不通过时消费层必须返回 typed `unavailable` / `required_missing`，不得静默代理为同股票池等权、买入持有或其他 proxy |
| CR-005 Backtrader 边界 | Backtrader 仅为 optional backend，后置消费本地已 PIT/复权清洗且通过 quality gate 的 feed；未安装或输入不可用时不得影响轻量主路径 |
| CR-011 生产级因子研究边界 | 实验 17-21 旧结论继续限定为 fixed snapshot、proxy baseline、close execution proxy 的探索结论；CR-011 只新增生产级数据补齐和新版报告要求，不覆盖旧报告 |
| CR-011 数据准入边界 | 新版因子研究必须通过真实 benchmark、PIT universe、tradability、execution feed、adjustment/corporate action、industry/market cap/style、liquidity/capacity/cost、factor audit panel 和 robust validation gate；任一必需 gate 未通过时只能输出 `required_missing` / `blocked_claims`，不得声明生产级结论 |
| CR-011 授权边界 | 本需求增量不授权真实联网、真实抓取、真实 lake 写入、旧 `data/**` 操作或凭据读取；后续真实执行必须由 Story/CP5 门控和用户显式授权控制，报告不得记录 token、用户名、密码、`.env` 内容或真实私有路径 |
| CR-013 full-history 声明边界 | CR-012 limited-window 通过结论只适用于 `2025-02-11..2026-02-18`；`2020-01-01..2024-12-31` 当前仍为 `research_limited_only`，10 个正式 dataset 均为 `limited_window_only`，不得外推为全历史生产级 current truth |
| CR-013 执行价声明边界 | `execution_price_audit.csv` 当前为 `required_missing`，`true_vwap_available_count=0`；真实 VWAP、VWAP fill、分钟线、逐笔、盘口、委托、成交明细和真实撮合执行价必须保持 blocked，不得由 close proxy 或 `amount/volume` 派生为真实 VWAP |
| CR-013 unsupported register 边界 | `unsupported_data_register.csv` 中 `research_contract_only`、`unsupported`、`contract_supported_but_unavailable` 项必须进入用户文档和报告声明边界；这些项排除在 pass denominator 之外，不得被当作已发布生产 dataset |
| CR-013 权限边界 | 本轮只允许需求增量刷新；不授权 provider fetch、真实 lake 写入、凭据读取、旧 `data/**` 读取或旧报告覆盖；后续任何 2020-2024 补数、真实 VWAP / 分钟数据接入或 unsupported register 刷新必须另行显式授权 |
| CR-014 全 A 全历史目标边界 | 数据湖目标升级为 A 股证券自存在 / 上市日起至当前交易日的 production current truth；CR-010/012 limited-window pass 与 CR-013 roadmap/blocked 旧基线继续保留，不得外推为全历史可用 |
| CR-014 证券生命周期边界 | 全 A current truth 必须处理上市 / 存在起始日、退市 / 摘牌日、暂停上市、代码变更、简称变更、交易所 / 板块归属和 list_status；缺失时返回 `required_missing` / `blocked_claims`，不得用当前快照伪装 PIT |
| CR-014 DuckDB 边界 | DuckDB 在需求阶段只作为 HLD 待决策的 read-only query / audit / feature extraction 候选能力；未经 CP3/CP5 批准不得修改 `pyproject.toml` / `uv.lock`，不得用 `.duckdb` 文件替代 Parquet lake、catalog 或 manifest |
| CR-014 权限边界 | 本轮只允许需求增量刷新；不授权 provider fetch、真实 lake 写入、凭据读取、旧 `data/**` 读取 / 列出 / 迁移 / 复制 / 比对 / 删除、旧 reports 覆盖或 DuckDB 依赖引入 |
| CR-015 QMT foundation 边界 | QMT 接入采用 Windows QMT / MiniQMT 节点、XtQuant 外部 Python API、OMS 和 QMT adapter；策略不得直接调用 QMT API；默认仅 shadow / dry-run / mock，不授权真实发单、撤单、账户写操作或凭据读取 |
| CR-015 broker lake / 风控边界 | broker lake 必须外置、可审计、日志脱敏；pre-trade risk 必须 hard block；订单意图必须同时记录 `research_adjustment_policy` 与 `execution_price_policy=raw`，禁止 qfq/hfq 进入真实执行价 |
| CR-016 QMT 激活边界 | 激活路径采用 `shadow -> QMT 模拟盘 -> 实盘只读 -> 小资金实盘 -> 放大资金`；T 日收盘后信号，T+1 限价 / 保护价执行；runbook、对账、kill switch 和 per-run 授权是进入真实链路的前置条件 |
| CR-016 声明与资金放大边界 | CR-017 不阻断技术模拟盘，但阻断生产策略复权治理声明和资金放大；真实 VWAP、minute、tick、level2、order-match 和微观结构执行价 blocked claim 继续保留 |
| CR-017 复权双视图边界 | `prices_raw` + `adj_factor` 是事实源；`prices_qfq`、`prices_hfq`、`returns_adjusted` 是独立派生 dataset / view；qfq 必须记录 `as_of_trade_date`；同一研究 run 只能使用一个明确复权口径 |
| CR-017 权限与迁移边界 | 本轮不授权真实抓取、真实写湖、发布 current pointer、批量重算 / 覆盖旧 qfq 数据、修改代码或引入依赖；旧 qfq 默认口径作为历史基线保留，迁移和兼容策略待 HLD/CP5 决策 |
| CR-018 数据湖优先级边界 | 用户已批准 D1-D6，后续最高优先级切换为先完成数据湖 production current truth，再进入 QMT simulation / live_readonly / small_live / scale_up |
| CR-018 current truth 闭环边界 | CR014 S14 `prices` / `adj_factor` candidate 是生产闭环输入，不等于 published current truth；必须补齐或显式阻断 PIT/W3/benchmark/quality，并经 Explicit Publish Gate 才能更新 catalog current pointer |
| CR-018 QMT 后置边界 | 数据湖未 publish 或 publish 后研究重跑未通过时，QMT simulation / live_readonly / small_live / scale_up 全部保持 blocked；通过后仍需独立 QMT stage gate 和 per-run 授权 |
| CR-019 阶段六目标边界 | 用户已确认阶段六目标是制定 A 股多因子策略并达到可申请模拟盘状态；既有 production rerun 失败策略不得包装为 admission pass，必须通过新的数据、因子、策略、交易现实性、成本、benchmark、稳健性、消融、冻结、pre-sim、5 日 dry-run 和 admission package |
| CR-019 D1-D7 决策边界 | D1 Backtrader 后置 optional execution backend；D2 Qlib 后置 isolated runner；D3 分钟数据不作为 P0，仅后置 Spike；D4 QMT xtdata 不进入 WSL 主路径，最终 simulation 采用 Windows QMT bridge；D5 暂不申请 QMT Level2；D6 shadow + 连续 5 个真实交易日 dry-run 后再申请 QMT simulation；D7 第一版桥接采用 FastAPI 本地服务 |
| CR-019 QMT C/S 模块边界 | QMT 模块必须拆分为 C/S 两部分：C 侧位于 local_backtest 内，向框架暴露统一 Python client / 函数接口并可提供薄 CLI；S 侧部署在 Windows QMT 节点，作为可运行 / 可安装的 FastAPI gateway，通过 REST 接收请求并转换为 QMT / XtQuant 接口调用 |
| CR-019 simulation later-gated 边界 | QMT gateway 必须支持完整 QMT 功能接口类别，但 FastAPI 服务存在、health pass、capabilities pass 或 endpoint 可见都不等于真实 simulation / live 授权；真实转发必须受 CR016 stage gate、per-run authorization、run mode、risk gate、对账和 kill switch 约束 |
| CR-019 fallback 边界 | Q-038 signed file drop 保留为 fallback，而非主选；fallback 只能产生 dry-run 文件交换或 blocked result，不得自动真实发单、撤单、账户查询或 broker lake 写入 |
| CR-019 QMT 文档边界 | 迅投 QMT 系统说明文档只能作为平台能力背景；不得据此推断当前项目已拥有真实账户、模拟盘、Level2、交易、撤单、账户查询或行情权限 |
| CR-025 research execution semantic alignment 边界 | Backtrader 只作为显式选择的 optional execution realism / semantic reference；默认仍使用 lightweight engine；CR-025 负责研究执行语义对照与 target portfolio / order intent 衔接，不替代 production truth、阶段六 P0 或 QMT admission gate。 |
| CR-025 依赖隔离边界 | CP5 前不得修改 `pyproject.toml` / `uv.lock` 或新增 Backtrader 依赖；后续若实现，必须采用 optional extra 或等价隔离方式与 lazy import，未安装时返回结构化 `backend_unavailable`。 |
| CR-025 clean feed / 执行语义边界 | Backtrader optional backend 只能消费已通过 PIT、`available_at`、单一复权口径、benchmark、calendar、tradability、cost 和 quality gate 的本地 feed；执行语义差异必须输出对照报告，不静默归因。 |
| CR-025 安全与运行授权边界 | 本 CR 不授权真实 broker、Backtrader live store、QMT / MiniQMT / XtQuant、provider fetch、真实 lake write、broker lake write、catalog publish、凭据读取、真实数据或真实账户操作；对应计数必须保持 0。 |
| CR-025 production-grade research-to-execution 目标边界 | 用户已澄清目标是生产级策略研究回测、模拟盘和实盘框架；CR-025 不开发框架级回测内核、不默认移植 Backtrader 源码、不迁移主路径，而是把研究执行语义对照和 target portfolio / order intent 衔接纳入生产路线。 |
| CR-025 三条主线边界 | 研究可信度由数据湖 / ResearchDataset / admission gate 承接；回测 / 模拟一致性由 lightweight baseline、Backtrader optional semantic reference 和 semantic diff 承接；QMT 生产执行由 CR-020..CR-024 的 gateway / simulation / live-readonly / small-live / scale-up 路线承接。 |
| CR-025 Backtrader 项目分析边界 | CP3/HLD 必须读取 `/home/hyde/download/backtrader`，识别 license、模块结构、Cerebro/broker/order/feed/analyzer/indicator/sizer/observer/store 等模块职责，并输出“可借鉴设计 / 可适配接口 / 源码级移植候选 / 禁止移植”对比表；源码级移植若被推荐，必须成为 CP3 决策项并说明 GPLv3、维护、回归和 CP5 授权影响。 |
| CR-030 多因子闭环主线边界 | CR-030 采用项目自有多因子研究闭环，不以 Qlib、Alphalens、vectorbt、Zipline、LEAN、RQAlpha、vn.py 或 Backtrader 作为默认框架、事实源、provider、runner、optimizer 或 report truth；外部项目只作为静态参考、接口映射或后续 Spike 候选。 |
| CR-030 schema 基线边界 | CR-030 的 schema 和校验不从零设计，而是以 `research_input_v1`、实验 17-21 `FactorDefinition`、CR-011 factor panel audit、label window gate 和 Stage6 admission gate 为基线，用 Qlib / Alphalens / Zipline / LEAN 等项目做 cross-check；HLD 必须输出字段字典、校验规则、错误码和 failure policy。 |
| CR-030 外部项目运行边界 | 本轮不授权 clone、install、run、qrun、回测样例、Notebook、外部 provider、外部数据下载或源码迁移；已存在的本地 Qlib `/home/hyde/download/qlib` 仅允许静态读取和架构分析。 |
| CR-030 研究到执行边界 | CR-030 只能产出研究报告、准入包、blocked claims 和 `order_intent_draft_v1` 草稿边界；不得生成真实 order、不得调用 QMT / MiniQMT / XtQuant、不得启动 gateway、不得进入 simulation/live/account/cancel/query。 |
| CR-030 CR-026 分流边界 | Qlib isolated runner / qrun / provider_uri / model workflow 不并入 CR-030 P0 实现；CR-026 保留为合同冻结后的后续 Spike candidate，启动前需重新冲突预检、CP2/CP3/CP5 和运行授权。 |
| 数据更新边界 | 已有本地缓存时默认只补缺口，并支持基于交易日历的最近 N 个交易日可配置回补；除显式强制刷新或回补窗口外，不重复已成功批次 |
| 失败降级边界 | 数据源不可用或数据准备部分失败时，若本地 parquet 覆盖区间和 schema 合规，回测/扫描继续离线运行，并在报告或质量报告披露数据新鲜度和失败项 |
| 聚宽边界 | 第一版只输出不超过 4 组候选参数供用户手动回填聚宽验证，不自动调用聚宽、不自动联网、不轮询平台任务 |
| 规范输出文件 | 参数扫描 CSV 为 `reports/momentum_param_sweep_local.csv`；候选清单 CSV 为 `reports/momentum_candidates_local.csv` |
| 参数命名 | 扫描候选列表使用 `rebalance_freqs`；单次回测参数使用 `rebalance_freq` |
| 复权口径硬约束 | 同一次回测、扫描、候选筛选和差异分析必须使用一致复权口径；默认采用前复权、后复权还是不复权仍需 HLD 前确认 |
| 信号与成交时点硬约束 | T 日收盘后生成信号，成交只能发生在 T+1 或之后；不得把 T 日收盘前不可得数据用于 T 日盘中决策 |
| 数据可用时点硬约束 | 任一参与决策的数据字段必须满足 `available_at <= decision_time`；无法证明可用时点的字段不得进入信号、过滤或成交判断 |
| 缺失与无成交硬约束 | 历史窗口不足必须剔除；缺失价格、缺失成交价或无成交不得静默填充，也不得被当作真实成交 |
| 股票池偏差硬约束 | 固定当前沪深 300 股票池必须标记为非 PIT，并披露幸存者偏差 |
| 报告 metadata 硬约束 | 单次回测、扫描和候选报告必须强制输出复权口径、信号/成交时点、股票池 PIT 标记、幸存者偏差和第一版限制项 |
| 数据准备可追溯硬约束 | 数据准备必须输出 manifest/checkpoint 和质量报告；manifest 至少记录批次、数据源、接口、请求参数、范围、请求时间、成功项、失败项、错误信息、重试次数、raw 路径、标准化输出路径、覆盖范围和最终状态 |

## 路径归属表

| 路径 | 归属层 | 第一版职责 | 必需性 |
|---|---|---|---|
| `data/prices.parquet` | 数据输入 | 多股票日收盘价输入 | P0 |
| `data/index_members.parquet` | 数据输入 | 固定沪深 300 成分股快照输入 | P0 |
| `data/trade_calendar.parquet` | 数据输入 | 交易日序输入 | P0 |
| `data/hs300_index.parquet` 或等价 lake path | 数据输入 / benchmark | 本地沪深 300 benchmark canonical/gold 输入；由 `market_data` 写湖 / 数据准备层生成 | P0（CR-005） |
| `data/raw/` | 数据准备输出 | 原始响应或原始表格缓存；标准化 parquet 必须可从 raw 派生 | P0 |
| `data/manifests/` | 数据准备输出 | manifest/checkpoint，记录批次状态、限速、重试、失败项、raw 路径、标准化输出路径和覆盖范围 | P0 |
| `market_data/**` | 数据准备 / 写湖层 | Tushare connector、runtime、storage、schema、normalization、quality、catalog、reader 和 benchmark resolver 的边界载体 | P0（CR-005） |
| `engine/data_loader.py` | 数据层 | 读取 parquet、校验 schema、输出 `close_df` 和交易日序 | P0 |
| `engine/backtest.py` | 回测编排层 | 串联信号、组合、分析和报告输出 | P0 |
| `engine/portfolio.py` | 组合层 | 等权目标、现金规则、成本扣除、净值更新 | P0 |
| `engine/metrics.py` | 分析层 | 绩效指标和净值完整性检查 | P0 |
| `strategies/momentum.py` | 信号层 | 动量纯函数、目标持仓选择 | P0 |
| `strategies/rsi.py`、`strategies/macd.py` | 后续策略层 | 第一版仅预留方向，不要求实现 | P2 |
| `notebooks/` | 展示层 | 可选研究展示和图表派生 | P2 |
| `reports/momentum_param_sweep_local.csv` | 报告输出 | 参数扫描必需 CSV | P0 |
| `reports/momentum_candidates_local.csv` | 报告输出 | 聚宽回填候选参数必需 CSV | P0 |
| `reports/data_quality_report.*` | 数据准备输出 / 报告输入 | 覆盖区间、缺失统计、失败统计、字段缺失、重复记录、异常价格、回补数量、最近成功更新时间和数据新鲜度 | P0 |
| `reports/experiment_17_21/*` | 历史报告基线 | CR-011 触发背景和 fixed snapshot / proxy baseline 旧基线；不得覆盖 | P0（CR-011 追溯） |
| `reports/experiment_cr011_*` 或等价版本化目录 | 新版研究报告输出 | 生产级因子研究报告、factor audit panel、稳健性验证、gate result 和脱敏 lineage metadata | P0（CR-011） |
| `reports/data_lake_readiness_2020_2024/*` | CR-013 证据基线 | 证明 2020-2024 full-history 仍为 `research_limited_only` / `limited_window_only`，作为声明边界证据保留；不得覆盖 | P0（CR-013 追溯） |
| `reports/data_lake_readiness_limited_2025_2026/unsupported_data_register.csv` | CR-013 unsupported 证据基线 | 登记 research-only、unsupported、contract-supported-but-unavailable 数据项，后续用户文档和报告声明必须消费其状态与 reason；不得把 excluded 项计入 pass 分母 | P0（CR-013 追溯） |
| `MARKET_DATA_LAKE_ROOT` / `--lake-root` 指向的外置 lake | CR-014 生产数据湖根 | 承载全 A since-inception raw / manifest / canonical / gold / quality / catalog；真实写入必须等待 CP5 与用户显式授权 | P0（CR-014，待授权） |
| `raw/manifest/canonical/gold/quality/catalog` | CR-014 P0 dataset 分层 | 每个发布候选 dataset 必须能从 raw/manifest 追溯到 canonical/gold/quality，并经显式 publish 更新 catalog current pointer | P0（CR-014） |
| `catalog/current` 或等价 current pointer | CR-014 current truth 指针 | 只指向已发布、quality/readiness 通过或按策略允许的版本；validate pass 不得自动成为 current truth | P0（CR-014） |
| `catalog/releases/<release_id>` 或等价 release summary | CR-018 production release 证据 | 记录 dataset 清单、release scope、as_of_trade_date、source run ids、quality 结果、blocked claims、rollback target、approver 和 approved_at | P0（CR-018） |
| production research rerun report | CR-018 发布后研究重跑证据 | 使用 published release 重跑阶段三到阶段五核心研究，并输出 release_id、benchmark、PIT、可交易性、复权口径、blocked claims 和旧 proxy/fixed-snapshot 对比 | P0（CR-018） |
| DuckDB 只读查询 / 审计候选 | CR-014 HLD 待决策能力 | 仅用于评估 read-only Parquet / catalog 查询、coverage audit、PIT join、feature extraction 和 parity；需求阶段不得新增依赖或写 `.duckdb` 事实源 | P1（CR-014，待 HLD 决策） |
| stage6 simulation admission package | CR-019 阶段六准入证据 | 汇总实验 49-66、数据 / 因子 / 策略 / 交易现实性 / 成本 / benchmark / 稳健性 / 消融 / 冻结 / pre-sim / 5 日 dry-run gate、blocked_claims 和申请 QMT simulation 的前置证据 | P0（CR-019，需求阶段不写真实 reports） |
| QMT C/S module：local_backtest client + Windows gateway | CR-019 WSL / Windows 桥接候选能力 | C 侧位于 local_backtest，提供统一 Python client / 函数接口并可派生薄 CLI；S 侧为 Windows QMT FastAPI gateway，可运行 / 可安装，承接完整 QMT endpoint matrix 并将 REST 请求转换为 QMT / XtQuant 接口调用；HLD/LLD 后才允许实现；需求阶段不新增依赖、不启动服务、不调用真实 QMT | P0（CR-019，待 CP3/CP5 决策） |
| signed file drop fallback | CR-019 FastAPI fallback | FastAPI 不可达、鉴权失败或部署边界不满足时，仅作为 dry-run 文件交换或 blocked result fallback；不作为主选通信路径，不自动真实 QMT | P1（CR-019 fallback） |
| Backtrader optional backend / Qlib isolated runner / minute / Level2 | CR-019 后置能力 | Backtrader、Qlib、分钟数据和 Level2 只按触发条件进入后续 CR / Spike，不作为阶段六 P0 或当前依赖 | P1/P2（CR-019 后置） |
| CR025 research execution semantic alignment contract | CR-025 研究执行语义对齐 | optional semantic reference 选择、依赖隔离、clean feed gate、semantic diff report、target portfolio / order intent draft、安全计数、fallback 到 lightweight 主路径和 structured unavailable / blocked result | P1（CR-025，CP5 前不得实现或新增依赖） |
| CR025 semantic diff report | CR-025 对照报告 | lightweight 与 Backtrader 在同一 clean feed、同一策略、同一成本配置下的调仓、成交价格、现金、成本、滑点、税费、净值和差异原因 | P1（CR-025，研究比较，不是 production truth） |

## 数据与接口契约

### 数据准备产物契约

| 产物 | 必需内容 | 约束 |
|---|---|---|
| raw 缓存 | 原始响应、原始表格或可复现原始数据切片；至少能追溯到数据源、接口、请求参数、股票/日期范围和请求时间 | 标准化 parquet 必须可从 raw 缓存派生；不得只保留无法追溯的最终宽表 |
| 标准化 parquet | `data/prices.parquet`、`data/index_members.parquet`、`data/trade_calendar.parquet` 等回测只读输入 | 只由数据准备/更新流程写入；回测、扫描、候选筛选只读，不在主路径内触发联网补数 |
| manifest/checkpoint | 批次 ID、数据源、接口、请求参数、股票/日期范围、请求时间、成功项、失败项、错误信息、重试次数、退避记录、raw 路径、标准化输出路径、覆盖范围和最终状态 | 断点续传必须基于 manifest/checkpoint 判断已成功批次；除显式强制刷新或最近 N 个交易日回补外，不重复已成功批次 |
| 数据质量报告 | 覆盖区间、缺失统计、失败统计、失败 symbol/date、字段缺失、重复记录、异常价格、回补数量、最近成功更新时间和数据新鲜度 | 回测和扫描报告必须可引用或携带质量摘要；数据源不可用时必须披露本地缓存新鲜度和失败项 |

### 数据准备配置契约

| 配置项 | 要求 |
|---|---|
| `request_interval_seconds` | 请求节流间隔；相邻请求时间间隔不得小于配置值。 |
| `batch_size` | 单批请求规模；用于限制每次请求的股票数、日期数或接口支持的等价批量单位。 |
| `max_concurrency` | 最大并发；默认保守串行抓取，默认值建议为 1，具体默认值需 HLD 前确认。 |
| `max_retries` | 最大重试次数；必须有上限，不允许无限循环。 |
| `backoff_policy` | 退避策略；可为固定退避或指数退避，但必须可记录到 manifest 或日志。 |
| `recent_trade_days_backfill` | 最近 N 个交易日回补窗口；必须基于交易日历而不是自然日，默认值需 HLD 前确认。 |
| `force_refresh` | 显式强制刷新开关；仅开启时允许重复抓取已成功批次。 |

### CR-005 benchmark 与补齐作业契约

| 对象 | 必需内容 | 约束 |
|---|---|---|
| `hs300_index` canonical/gold | `trade_date`、`index_code`、`close`、`pct_chg`、`benchmark_kind`、`source`、`source_interface`、`source_run_id`、`available_at`、coverage 起止、quality status | `index_code` 默认为 `399300.SZ`；`benchmark_kind` 取值需在 CP5 前确认，未确认前不得把真实路径标为 fully available |
| benchmark typed result | `status=available/unavailable/required_missing`、`benchmark_status`、`quality_status`、`coverage_start`、`coverage_end`、`trade_calendar_denominator`、`missing_trade_dates`、`gap_reason`、`next_action`、`remediation_job_spec` | `unavailable/required_missing` 必须可机器解析；不得只输出自由文本错误；消费层不得自动执行补齐 |
| `remediation_job_spec` | `target_dataset=hs300_index`、`source=tushare`、exact interface、date range、lake root、quality report path、docs/runbook reference、dry-run/plan 要求 | 只描述用户下一步应执行的数据准备作业；不得携带 token 值；不得由消费层执行 |
| Tushare 写湖 / backfill job | plan、fetch/backfill、normalize、validate/catalog 的作业规格、批次、allowlist、manifest、raw/canonical/gold/quality/catalog 输出 | 只有用户显式执行 `market_data` 写湖 / 数据准备命令时才允许联网；`engine/data_loader.py`、实验入口、benchmark resolver 和 Backtrader 不得触发 |

### CR-011 生产级因子研究数据契约

| 数据域 | 必需内容 | 缺失或质量失败时处理 |
|---|---|---|
| 真实 benchmark | `hs300_index` canonical/gold、`benchmark_kind`、`index_code`、coverage、trade calendar denominator、missing dates、quality status、source lineage | 不输出 `hs300_*` 生产级超额收益；只允许 `proxy_baseline` 字段并写入 `blocked_claims` |
| PIT 股票池与生命周期 | `index_members`、`index_weights`、`stock_basic`、上市/退市日期、list status、`effective_date`、`available_at`、`pit_status` | `production_strict_research` fail；探索模式必须标记 fixed snapshot / limited PIT window / survivorship bias |
| 可交易性 | 停牌、涨跌停、ST、无成交、上市天数、退市/摘牌、事件状态、可买可卖枚举和原因码 | 不得声明真实可成交；成交和样本过滤必须输出 blocked reason 与 symbol/date 统计 |
| 执行价 | clean OHLCV、VWAP 或经批准的日频执行价代理、`execution_price_policy`、缺失/无成交处理 | 缺 VWAP 或 open/high/low 时不得静默用 close 冒充真实执行价；只能声明 `close_proxy` 或阻断真实执行声明 |
| 复权与公司行动 | `adj_factor`、adjusted OHLC、`adjustment_policy`、分红/送转/拆合/配股等公司行动来源和异常价格解释 | 只能声明“使用已复权价格”，不得声明公司行动链路可审计 |
| 行业 / 市值 / 风格 | PIT 行业分类、市值、流通市值、Beta、size/value/liquidity 等风格暴露矩阵和 coverage | 不得声明行业中性、市值中性、风格中性或纯因子 alpha |
| 流动性 / 容量 / 成本 | amount、volume、turnover、ADV、成交参与率、冲击成本模型、成本网格、容量上限 | 不得声明容量可交易；成本后收益只能作为探索结果 |
| 因子审计面板 | 每个因子的 `raw`、`directional`、`winsorized`、`zscore` 四层值、预处理参数、过滤原因、lineage 和 coverage | 不得把预处理后结果解释为可复现因子结论；缺层级必须 fail |
| 稳健性验证 | rolling walk-forward、年度分层、市场状态分段、参数敏感性、成本敏感性、样本内外对照 | 不得只基于单一区间单一参数声明稳定性 |
| 授权与凭据 | source enabled、exact allowlist、credential env var 名称、explicit real execution、脱敏 root label、network/write counters | 未授权时真实联网/写湖/凭据读取必须为 0；报告不得记录凭据值、`.env` 内容或真实私有路径 |

### CR-013 unsupported 与声明边界契约

| 对象 | 必需内容 | 声明约束 |
|---|---|---|
| limited-window 与 full-history 边界 | `readiness_scope`、`target_window`、`overall_status`、10 个正式 dataset 的 `final_status` / `issue_code` / `remediation`、证据路径 | `2025-02-11..2026-02-18` pass 不得外推到 `2020-01-01..2024-12-31`；2020-2024 全历史在新补数和新审计通过前必须保持 blocked |
| execution / VWAP claim | `execution_price_status`、`missing_ohlcv_columns`、`true_vwap_available_count`、`vwap_status`、`blocked_claims`、remediation | 缺少 `vwap` 且 `vwap_status=available` 时不得声明真实 VWAP / VWAP fill；不得由 close proxy 或 `amount/volume` 派生为真实 VWAP；分钟 / 逐笔 / 盘口 / 撮合执行价保持 unsupported |
| unsupported data register | `data_item`、`status`、`reason`、`pass_denominator`、对应 allowed / blocked claim | `research_contract_only` 只能声明为研究合同候选；`unsupported` 与 `contract_supported_but_unavailable` 必须进入 blocked / unsupported 声明；`pass_denominator=excluded` 不得计入生产级可用分母 |
| 用户文档和报告声明 | supported / research-only / unsupported / blocked 四类声明、证据路径、窗口范围、解除条件 | README、USER-MANUAL 和报告摘要不得只展示 limited-window pass；必须同时显示 2020-2024 full-history blocked、真实 VWAP / 分钟执行价 blocked 和 unsupported register 摘要 |
| 证据保留与权限 | 原报告路径、run_id、生成时间、安全计数、provider/lake/credential/old data 权限状态 | 现有 2020-2024 报告与 unsupported register 是 CR-013 证据基线；后续补数或刷新必须产生新 run / 新报告，不覆盖旧证据；默认 provider_fetches=0、lake_writes=0、credential_reads=0、legacy_data_reads=0 |

### CR-014 全 A 全历史数据湖契约

| 对象 | 必需内容 | 声明约束 |
|---|---|---|
| 全 A universe current truth | 全 A 证券代码、交易所、板块、上市 / 存在起始日、退市 / 摘牌日、list_status、代码变更、简称变更、effective_date、available_at、source/interface、run_id | 缺生命周期或代码映射时不得声明 since-inception PIT current truth；固定快照只能作为探索性输入 |
| P0 dataset 分层 | `prices`、`adj_factor`、`hs300_index`、`trade_calendar`、`index_members`、`index_weights`、`stock_basic` 及 CP2/CP3 确认的新增 P0 dataset 均需 raw / manifest / canonical / gold / quality / catalog 分层 | 分层缺失或 lineage 不可追溯时不得 publish 为 production current truth；P0 清单最终以 CP2/CP3 决策为准 |
| catalog current pointer | dataset、schema_version、coverage_start / end、coverage numerator / denominator、quality/readiness、published_at、source/interface、latest_manifest_run_id、lineage checksum、known_limitations | validate pass 不得自动更新 current pointer；reader / query / audit 默认只能消费已发布 current truth 或 structured missing |
| 增量刷新与 replay | 缺口补齐计划、最近 N 个交易日回补、force_refresh、idempotency_key、skip/retry/resume_conflict、run_id、batch_id、manifest/raw replay 输入 | replay 不得触发 provider 或读取凭据；重复运行不得污染已发布 current pointer；真实执行前必须有 CP5 与用户显式授权 |
| DuckDB 候选能力 | read-only Parquet / catalog query、coverage audit、PIT join、feature extraction、pandas/pyarrow parity、SQL view registry 候选 | DuckDB 为 HLD 待决策能力；未经批准不得写入依赖、不得持久化 `.duckdb` 作为事实源、不得执行 lake 写入或替代 catalog/manifest |
| claim boundary | allowed_claims、blocked_claims、readiness_scope、supported_window、blocked_window、evidence_paths、解除条件、permission counters | limited-window pass、2020-2024 roadmap 或旧报告不得外推为全 A since-inception production current truth；任一 P0 gate 未过必须产生 blocked claim |

### CR-017 复权双视图与 QMT 交易价格隔离契约

| 对象 | 必需内容 | 声明约束 |
|---|---|---|
| `prices_raw` | 未复权原始交易价、OHLCV、source/interface、run_id、batch_id、available_at、lineage checksum、quality status | QMT 委托、成交、成交核算和 broker 对账只能使用 raw / broker price；raw 不得被 qfq/hfq 覆盖 |
| `adj_factor` | 复权因子、provider 字段解释、因子方向、可用时间、source_run_id、input snapshot、quality status | 只能声明“使用复权因子”；在公司行动事件链未补齐前不得声明完整公司行动链路可审计 |
| `prices_qfq` | 前复权派生价格、`as_of_trade_date`、输入 snapshot、source_run_id、derivation_version、quality status | qfq 历史价格随 as-of 变化必须可追溯；不得无声覆盖旧 qfq 基线 |
| `prices_hfq` | 后复权派生价格、source_run_id、derivation_version、quality status | 主要服务长期收益、波动率、动量和因子研究；不得作为真实交易执行价 |
| `returns_adjusted` | 调整后收益率、收益计算口径、source_run_id、quality status | 严肃收益 / 因子研究推荐入口之一；仍需记录研究口径，不替代 raw 交易事实 |
| 研究 run 口径 gate | `research_adjustment_policy`、dataset/view id、reader policy、validation result、报告 metadata | 同一 run 不得混用 raw/qfq/hfq/returns_adjusted；混用必须 fail fast 并输出 blocked reason |
| QMT 执行价边界 | `execution_price_policy=raw`、broker price source、order intent price reference、成交 / 对账 price source | qfq/hfq 不得进入委托价、成交价或 broker reconciliation；只能作为研究 metadata |

### CR-015 QMT Foundation 契约

| 对象 | 必需内容 | 声明约束 |
|---|---|---|
| QMT adapter 边界 | Windows QMT / MiniQMT 节点、XtQuant 外部 Python API、adapter mode、connection lifecycle、mock fixture | 策略层不得直接调用 QMT API；真实 `order_stock` / `cancel_order_stock` 调用必须等 CR-016 per-run 授权 |
| OMS order intent | strategy_id、run_id、signal_date、target_trade_date、symbol、side、target_qty / target_weight、cash snapshot、holdings snapshot、`research_adjustment_policy`、`execution_price_policy=raw` | order intent 是策略目标到 broker order 的唯一入口；缺少价格口径字段时不得进入 adapter |
| OMS 状态机 | order_intent、broker_order_ref、state、event_time、fill_qty、filled_amount、cancel_reason、reject_reason、unknown / timeout 标记 | partial fill、cancel、reject、unknown、timeout 不得被静默当作成功；状态迁移必须可重放 |
| pre-trade hard risk gate | 现金、整手、T+1 可卖、可用持仓、价格口径、重复下单、单票 / 组合上限、异常价格、交易日历 | 任一规则 fail 时不得触达 adapter；warn-only 不满足 CR-015 |
| broker lake | 外置 root label、orders、trades、positions、assets、errors、reconciliation、retention、redaction、lineage | 不写仓库 `data/**` / `reports/**`；不保存 token、账户号、session、cookie、交易密码或 `.env` 内容 |
| 默认运行模式 | shadow、dry-run、mock adapter、safe counters、blocked real API list | CR-015 不授权真实发单、撤单、账户写操作或凭据读取 |

### CR-016 QMT 激活与运行治理契约

| 对象 | 必需内容 | 声明约束 |
|---|---|---|
| stage gate | `shadow`、`simulation`、`live_readonly`、`small_live`、`scale_up`、前置证据、准入 / 退出 / 回滚条件 | 阶段不可跳过；缺前置证据时返回 blocked gate result |
| runbook | 启动前检查、审批点、异常处理、对账、kill switch、暂停 / 恢复、手工接管、回滚策略 | 模拟盘前必须存在；缺失时不得进入 QMT 模拟盘 |
| per-run 授权 | 账户模式、策略、日期、运行窗口、资金上限、操作范围、审批人、回滚策略、授权时间 | 任一真实 QMT 操作缺授权字段时调用次数必须为 0；授权记录不得包含敏感凭据值 |
| T 日信号 / T+1 执行 | signal_date、decision_time、target_trade_date、limit / protect price policy、timeout / cancel policy | 不允许 T 日盘中即时信号即时下单；成交策略细节在 CP3 冻结 |
| 对账 | 盘前 / 盘中 / 盘后委托、成交、持仓、资产、现金、差异阈值、处理责任 | 差异必须结构化输出；超阈值时进入 blocked 或 manual_review |
| kill switch | 停止新单、撤可撤单、冻结策略、人工接管、恢复条件、审计事件 | kill switch 触发后不得继续提交新单；恢复必须有明确条件和记录 |
| 资金放大 gate | 模拟盘稳定性、小资金实盘表现、CR-017 口径治理、PIT / benchmark / exposure / capacity / execution claim 状态 | CR-017 未实现验证前不得声明生产策略复权治理完成或进入资金放大 |

### CR-019 QMT C/S 模块与 Windows FastAPI Gateway 候选契约

| 对象 | 第一版要求 | 约束 |
|---|---|---|
| C/S 模块边界 | C 侧位于 local_backtest 内，向策略、OMS、运行治理和测试暴露统一 Python client / 函数接口；S 侧部署在 Windows QMT / MiniQMT 节点，作为可运行 / 可安装的 FastAPI gateway | C 侧不得导入 xtquant 或直接触达 QMT；S 侧是唯一 QMT / XtQuant 转换层；需求阶段不实现服务、不新增依赖、不打开端口 |
| C 侧接口形态 | 推荐 Python client / 函数调用作为主接口，薄 CLI 仅用于人工 smoke、运维检查和脚本包装 | CLI-first 会增加内部调用和测试复杂度；Python-only 缺少手工排障入口；最终由 CP2/CP3 冻结 |
| S 侧职责 | 接收 C 侧 REST 请求，校验 schema、run mode、stage、risk、kill-switch 和可选鉴权，再转换为 QMT / XtQuant 接口调用并由 Windows QMT 客户端访问 QMT 服务端，或返回 blocked | S 侧不得把局域网请求直接视为真实操作授权；日志必须脱敏 |
| `/health` | 返回服务存活、版本、mode、heartbeat 时间、gateway 运行状态和 QMT client 摘要状态 | health pass 只表示服务可达，不表示 QMT simulation 或真实账户授权 |
| `/capabilities` | 返回 endpoint 列表、allowed / later-gated / blocked 状态、支持能力、当前运行模式和禁止项 | capability 可见不等于可执行授权；simulation、account、reconciliation、kill-switch 等真实转发必须再过运行门控 |
| `/intents/validate` | 校验 order intent schema、价格口径、stage、risk、authorization 字段完整性 | validation 通过不触发真实 QMT；缺字段必须返回 blocked reason |
| `/dry-run/orders` | 生成 dry-run order plan、risk result、no-real-op 安全计数和脱敏日志 | `real_order_calls`、`real_cancel_calls`、`account_query_calls`、`credential_reads` 必须为 0 |
| market / account / position / order / trade query | 必须纳入完整 endpoint matrix；按 run mode 和 live-readonly / simulation / live gate 判断是否真实转发 | 未满足门控时返回 blocked；账户、资金、持仓和订单日志必须脱敏 |
| simulation submit / cancel | 必须纳入完整 endpoint matrix；满足 simulation run mode、CR016 stage gate、risk gate、kill-switch 和必要上下文时才可真实转发 | 不因 FastAPI 服务存在而授权；缺任一门控时真实 QMT 调用计数为 0 |
| live-readonly / live submit / live cancel | 必须纳入完整 endpoint matrix；真实转发只在后续 live_readonly / small_live / scale_up gate 通过后可用 | 默认不得启用无门控直转；小资金和资金放大另需 per-run 授权 |
| `/reconciliation/{run_id}` 与 `/kill-switch` | 支持对账查询、停止新单、撤可撤单、冻结策略和人工接管状态 | kill-switch 的真实撤单动作必须受运行模式、阶段门控和人工策略约束 |
| 鉴权 | 第一版可在受控局域网内不做应用层鉴权；若 CP3 判定需要鉴权，采用最简 token / HMAC，并定义失败行为和日志脱敏 | 鉴权策略不得削减 QMT 功能接口覆盖；禁止日志打印密钥或 `.env` 内容 |
| 绑定与防火墙 | 默认本机或受控边界；需定义 bind host、port、Windows 防火墙和访问来源 allowlist | 禁止公网或不受控局域网默认暴露；部署细节为 CP3 必须冻结项 |
| fallback | FastAPI 不可达、鉴权失败、heartbeat fail 或部署边界不满足时，可转 signed file drop dry-run 或 blocked | fallback 不得自动真实发单、撤单、账户查询或 broker lake 写入 |

### CR-025 Research Execution Semantic Alignment 契约

| 对象 | 第一版要求 | 约束 |
|---|---|---|
| optional semantic reference 选择 | 默认使用 lightweight engine；只有用户显式选择 `backtrader` 或等价 optional reference 配置时才进入 Backtrader 语义对照路径 | 不得把 Backtrader 设为默认主路径、默认依赖、阶段六 P0 或生产执行 truth |
| 依赖隔离 | Backtrader 依赖必须被 optional extra 或等价机制隔离；主包导入、轻量回测、数据读取和默认测试不得强依赖 Backtrader | CP5 前不得修改 `pyproject.toml` / `uv.lock`；未安装时返回 `backend_unavailable` |
| clean feed gate | 输入必须通过 PIT / `available_at`、单一复权口径、benchmark、calendar、tradability、cost、quality gate 和 schema 检查 | Backtrader 不生成 PIT、不计算复权因子、不联网补数、不读取 provider token、不绕过 quality gate |
| execution semantics adapter | 对齐调仓日、目标权重 / 数量、成交价格、现金、手续费、滑点、税费、未成交 / 缺失处理和净值归属字段 | 执行语义差异必须显式输出，不得把差异静默归因或覆盖 lightweight 结果 |
| semantic diff report | 比较 lightweight 与 Backtrader 在同一 clean feed、同一候选策略、同一成本配置下的结果 | 报告用于 research comparison，不是 production truth、默认研究 truth 或 QMT simulation admission pass |
| target portfolio / order intent draft | 将研究输出衔接到后续 QMT OMS 可评审的 draft 字段，至少包含 strategy_id、run_id、signal_date、target_trade_date、symbol、target_weight / target_qty、research_adjustment_policy、execution_price_policy、cost_config_ref、data_lineage_ref、limitations | 仅定义接口草案和声明边界；不得在 CR-025 内触发 QMT gateway、simulation、live、下单、撤单、账户查询或 broker lake 写入 |
| safety counters | `real_broker_calls`、`qmt_api_call`、`provider_fetch`、`lake_write`、`broker_lake_write`、`catalog_publish`、`credential_read`、`dependency_changes` | CP2/CP3/CP5 前全部应为 0；任何真实 broker / QMT / provider / lake / publish 行为必须另起 CR 并单独授权 |

### 最小 parquet schema

| 文件 | 必需字段 | 可选字段 | 约束 |
|---|---|---|---|
| `data/prices.parquet` | `trade_date`, `symbol`, `close` | `available_at`, `adjustment_policy`, `volume`, `amount` | `trade_date` 可排序且可转换为日期；`symbol` 为证券代码；`close` 为正数或缺失值；参与决策时必须具备 `available_at` 或可审计的收盘后可用时点推导规则；同一运行内 `adjustment_policy` 不得混用 |
| `data/index_members.parquet` | `symbol` | `snapshot_date`, `available_at`, `is_pit_universe` | 第一版按固定当前沪深 300 成分股快照使用；报告必须记录快照日期、`is_pit_universe=false` 和幸存者偏差 |
| `data/trade_calendar.parquet` | `trade_date` | `is_open` | 交易日序按升序去重；如存在 `is_open`，仅 `true` 计入回测交易日 |
| `data/hs300_index.parquet` 或等价 lake path | `trade_date`, `index_code`, `close`, `pct_chg`, `benchmark_kind`, `source`, `source_interface`, `source_run_id`, `available_at` | `coverage_start`, `coverage_end`, `quality_status`, `missing_trade_dates`, `gap_reason` | 仅由 `market_data` 写湖 / 数据准备层生成；消费层只读；缺失或 quality fail 时返回 structured `unavailable` / `required_missing` |

### 数据可用时点契约

| 字段 | 要求 |
|---|---|
| `decision_time` | 生成信号或做交易判断的时间点；第一版动量信号默认为 T 日收盘后决策。 |
| `available_at` | 任一参与决策字段的实际可用时间；必须小于等于对应 `decision_time`。 |
| 缺失 `available_at` 的日线价格 | 只有在 HLD 明确批准“收盘价在 T 日收盘后可用”的推导规则后，才能用于 T 日收盘后信号；否则不得作为决策字段。 |
| 事件类字段 | 财报、公告、ST 状态等事件字段第一版默认 Out of Scope；后续引入时必须提供字段级 `available_at`。 |

### `close_df` 契约

| 字段 | 要求 |
|---|---|
| 结构 | pandas DataFrame |
| index | 按升序排列的交易日序，来自 `data/trade_calendar.parquet` |
| columns | 股票代码，来自固定股票池与价格数据交集 |
| values | 收盘价，允许缺失；策略层必须在排名前过滤缺失动量 |
| 复权口径 | 同一 `close_df` 内必须采用单一复权口径，并在结果 metadata 中记录 |
| 时间边界 | 回测区间内不得自动向未来补值；T 日收盘后信号只能使用 T 日收盘时已经可得的数据，成交只能发生在 T+1 或之后 |

### 层接口边界

| 层 | 输入 | 输出 | 边界 |
|---|---|---|---|
| 信号层 | `close_df` 历史窗口、当前持仓、策略参数 | 目标股票列表或目标权重前置集合 | 纯函数，不读写文件，不依赖回测全局状态 |
| 组合层 | 当前净值、当前权重、目标权重、成本参数、日收益 | 日净值、成交明细、成本明细、持仓权重 | 不计算选股信号，不读报告文件 |
| 分析层 | 净值序列、日收益、成交/持仓摘要 | 累计收益、年化收益、最大回撤、Sharpe、换手等指标 | 不改变回测结果 |
| 扫描层 | 参数网格、单次回测入口、失败策略 | 扫描 CSV、候选清单 CSV | 不改变策略逻辑，只调度多组参数 |
| CR-005 写湖层 | Tushare source config、allowlist、token env 引用、interface、batch/date range、lake root | raw、manifest、canonical/gold、quality、catalog | 只在用户显式执行 `market_data` 数据准备命令时联网；不得被消费层自动调用 |
| CR-005 benchmark resolver | 本地 `hs300_index` canonical/gold、quality、catalog、date range、quality policy | typed benchmark result | 只读本地文件；不得导入 connector/runtime/storage，不得读取 `TUSHARE_TOKEN`，不得用 proxy 填充 `hs300_index` |
| CR-005 Backtrader optional backend | 已通过 PIT/复权/quality gate 的本地 factor panel / score / OHLCV feed、calendar、benchmark result | optional backend result 或 `backend_unavailable` / data unavailable 状态 | 不替代轻量主路径；不生成 PIT、不计算复权因子、不联网、不绕过 quality gate |
| CR-011 因子研究准入层 | CR-008 `research_input_v1`、CR-010 catalog/quality/readiness、实验 17-21 因子列表、生产级 gate 配置 | `production_strict_research` / `exploratory` gate result、allowed_claims、blocked_claims、factor audit panel、稳健性报告 | 只消费本地 reader 和已授权数据湖事实；不得在实验入口自动联网、读取凭据或写 lake |
| CR-014 全历史数据湖生产层 | 全 A universe、P0 dataset 计划、source/interface allowlist、lake root、run_id、batch_id、quality/readiness policy | raw、manifest、canonical、gold、quality、catalog candidate、publish current pointer | 需求阶段不执行；真实 provider fetch、lake write、credential read 必须等待 CP5 与用户显式授权 |
| CR-014 只读查询 / 审计候选层 | 已发布 Parquet lake、catalog current pointer、quality/readiness metadata、可选 DuckDB HLD 决策 | query result、coverage audit、PIT join audit、feature extraction candidate、parity report | 默认只读；DuckDB 未获批准前不得新增依赖、不得持久化 `.duckdb` 作为事实源、不得写 lake 或改 catalog |
| CR-017 复权派生层 | `prices_raw`、`adj_factor`、provider 字段解释、as-of、derivation config | `prices_qfq`、`prices_hfq`、`returns_adjusted`、quality / lineage metadata | 不真实抓取、不真实写湖、不发布 current pointer；同一 view 内单一复权口径，不混存 raw/qfq/hfq |
| CR-017 reader / validation 层 | dataset/view id、`research_adjustment_policy`、requested fields、run metadata | 单口径 reader result 或 structured blocked reason | 同一研究 run 不得混用复权口径；QMT 执行路径只能拿 raw / broker price |
| CR-015 OMS / order intent 层 | 策略目标组合、现金 / 持仓 snapshot、risk config、研究口径和执行价口径 | order intent、risk result、state transition、adapter request plan | 策略不直接调用 QMT；risk fail 时 hard block；缺 `execution_price_policy=raw` 时不得进入 adapter |
| CR-015 QMT adapter 层 | OMS adapter request、adapter mode、mock fixture、Windows QMT node config 引用 | shadow / dry-run / mock response、脱敏 broker event | CR-015 默认不调用真实 QMT 下单 / 撤单 / 账户写接口；真实链路必须走 CR-016 per-run 授权 |
| CR-015 / CR-016 broker lake 层 | orders、trades、positions、assets、errors、reconciliation event、external root label | broker lake candidate / dry-run audit / reconciliation report | 外置存储；不得写仓库 `data/**` / `reports/**`；不得保存或输出凭据、账户号、session、cookie、交易密码 |
| CR-016 activation / ops 层 | stage gate、runbook、per-run 授权、信号、订单计划、monitoring、reconciliation、kill switch | stage gate result、run report、reconciliation report、incident / takeover audit | 阶段不可跳过；无授权真实 API 调用次数为 0；kill switch 触发后停止新单并按规则撤可撤单 |
| CR-025 research execution semantic alignment 层 | optional semantic reference 选择、clean feed、候选策略、成本配置、benchmark/calendar、lightweight baseline result、research output | optional reference availability、blocked reason、semantic diff report、target portfolio / order intent draft、安全计数 | 只作为显式选择的研究对照和接口衔接；不默认导入、不联网、不写湖、不接真实 broker / QMT、不替代 lightweight 主路径 |

### 报告 schema

| 文件 | 必需字段 |
|---|---|
| `reports/momentum_param_sweep_local.csv` | `lookback_days`, `rebalance_freq`, `top_fraction`, `sell_buffer`, `commission_rate`, `slippage_rate`, `sell_tax_rate`, `start_date`, `end_date`, `total_return`, `annual_return`, `max_drawdown`, `sharpe`, `turnover`, `final_nav`, `scan_elapsed_seconds`, `status`, `error_message`, `adjustment_policy`, `signal_timing`, `execution_timing`, `is_pit_universe`, `survivorship_bias_warning`, `data_limitations`, `data_coverage_start`, `data_coverage_end`, `last_successful_update_at`, `data_freshness_days`, `data_quality_status` |
| `reports/momentum_candidates_local.csv` | `candidate_type`, `lookback_days`, `rebalance_freq`, `top_fraction`, `sell_buffer`, `selection_reason`, `rank_metric`, `total_return`, `annual_return`, `max_drawdown`, `sharpe`, `turnover`, `bias_warning`, `jq_validation_scope`, `adjustment_policy`, `signal_timing`, `execution_timing`, `is_pit_universe`, `survivorship_bias_warning`, `data_limitations`, `data_coverage_start`, `data_coverage_end`, `last_successful_update_at`, `data_freshness_days`, `data_quality_status` |
| `reports/data_quality_report.*` | `coverage_start`, `coverage_end`, `symbols_total`, `trade_dates_total`, `missing_count`, `missing_rate`, `failed_count`, `failed_symbol`, `failed_date`, `missing_field`, `duplicate_count`, `abnormal_price_count`, `backfilled_trade_days`, `backfilled_records`, `last_successful_update_at`, `data_freshness_days`, `quality_status` |
| `reports/benchmark_quality_report.*` 或 `reports/data_quality_report.*` 中的 `hs300_index` 行 | `dataset`, `benchmark_kind`, `index_code`, `source`, `source_interface`, `source_run_id`, `coverage_start`, `coverage_end`, `trade_calendar_denominator`, `covered_trade_dates`, `missing_trade_dates`, `missing_rate`, `quality_threshold`, `quality_status`, `gap_reason`, `next_action` |
| CR-011 新版因子研究报告 | `report_version`, `baseline_report_path`, `research_mode`, `gate_status`, `allowed_claims`, `blocked_claims`, `benchmark_kind`, `universe_mode`, `pit_status`, `tradability_gate_status`, `execution_price_policy`, `adjustment_policy`, `industry_neutralization_status`, `market_cap_neutralization_status`, `style_exposure_status`, `capacity_cost_status`, `robust_validation_status`, `source_run_ids`, `quality_report_paths`, `credential_redaction_status` |
| CR-011 factor audit panel | `trade_date`, `symbol`, `factor_name`, `raw_value`, `directional_value`, `winsorized_value`, `zscore_value`, `direction_multiplier`, `winsor_lower`, `winsor_upper`, `imputation_flag`, `valid_mask`, `filter_reason`, `preprocessing_version`, `source_run_id`, `universe_mode`, `benchmark_kind` |
| CR-011 稳健性验证表 | `validation_slice`, `slice_type`, `start_date`, `end_date`, `factor_name`, `strategy_name`, `top_fraction`, `parameter_set_id`, `cost_scenario_id`, `annual_return`, `max_drawdown`, `sharpe`, `turnover`, `ic_mean`, `icir`, `sample_count`, `status`, `warning_reason` |
| CR-013 声明边界报告 / 用户文档摘要 | `readiness_scope`, `supported_window`, `blocked_window`, `overall_status`, `limited_window_status`, `full_history_status`, `dataset_status_counts`, `blocked_claims`, `unsupported_data_items`, `pass_denominator_policy`, `evidence_paths`, `remediation_required`, `permission_counters`, `old_report_preserved` |
| CR-014 全 A 全历史 readiness / current truth 摘要 | `readiness_scope`, `universe_scope`, `current_trade_date_policy`, `dataset`, `priority`, `coverage_start`, `coverage_end`, `coverage_numerator`, `coverage_denominator`, `missing_symbol_dates`, `lifecycle_status`, `code_change_status`, `quality_status`, `readiness_status`, `catalog_pointer_status`, `source_interface`, `run_id`, `lineage_checksum`, `allowed_claims`, `blocked_claims`, `permission_counters`, `duckdb_candidate_status` |
| CR-014 DuckDB parity / audit 候选报告 | `duckdb_enabled`, `decision_status`, `query_scope`, `read_only_mode`, `parquet_paths`, `catalog_snapshot`, `sql_view_registry_status`, `pandas_pyarrow_parity_status`, `row_count_diff`, `value_diff_summary`, `write_attempts`, `dependency_change_status`, `blocked_reason` |
| CR-017 adjustment readiness / migration 摘要 | `dataset`, `view_id`, `research_adjustment_policy`, `execution_price_policy`, `source_run_id`, `batch_id`, `as_of_trade_date`, `derivation_version`, `lineage_checksum`, `quality_status`, `single_policy_gate_status`, `legacy_qfq_baseline_preserved`, `allowed_claims`, `blocked_claims`, `permission_counters` |
| CR-015 QMT foundation dry-run / mock 报告 | `run_id`, `strategy_id`, `adapter_mode`, `order_intent_count`, `blocked_intent_count`, `risk_rule`, `blocked_reason`, `state_transition_count`, `unknown_count`, `mock_broker_event_count`, `research_adjustment_policy`, `execution_price_policy`, `real_qmt_api_calls`, `credential_reads`, `broker_lake_writes`, `redaction_status` |
| CR-016 activation / ops 报告 | `run_id`, `stage`, `gate_status`, `runbook_status`, `authorization_status`, `signal_date`, `target_trade_date`, `limit_protect_policy`, `pre_market_recon_status`, `intraday_recon_status`, `post_market_recon_status`, `kill_switch_events`, `manual_takeover_status`, `allowed_claims`, `blocked_claims`, `real_order_calls`, `real_cancel_calls`, `account_write_calls` |

### 报告 metadata 限制项

| 限制项 | 第一版输出要求 |
|---|---|
| 复权口径 | 必须输出实际使用口径；不得混用。 |
| 信号与成交时点 | 必须输出 T 日收盘后信号、T+1 或之后成交的口径。 |
| 股票池 | 必须输出固定当前沪深 300、`is_pit_universe=false`、快照日期和幸存者偏差警示。 |
| 数据可用时点 | 必须说明参与决策字段的 `available_at` 校验或推导规则。 |
| 第一版未精确建模项 | 必须警示完整停牌状态、涨跌停撮合、新股上市初期特殊规则、退市整理/摘牌、ST 历史状态、财报披露日和沪深 300 历史成分变化。 |
| CR-011 生产级声明 | 必须输出 allowed_claims / blocked_claims；数据 gate 未通过时不得声明真实 benchmark、PIT、真实可成交、中性化、容量可交易、复权链路可审计或稳定生产级 alpha。 |
| CR-011 凭据与路径脱敏 | 必须只输出环境变量名、source/interface、run_id、相对路径或脱敏 root label；不得输出 token、用户名、密码、`.env` 内容或真实私有路径。 |
| CR-013 unsupported 声明 | 必须输出 limited-window / full-history 窗口边界、2020-2024 blocked 状态、真实 VWAP / 分钟执行价 blocked 状态、unsupported register 摘要和证据路径；不得把 excluded 项计入生产级 pass 分母。 |
| CR-014 全历史声明 | 必须输出全 A since-inception-to-current-trading-day 的可声明范围、P0 dataset gate、证券生命周期、catalog current pointer、增量刷新 / replay 状态、DuckDB 候选状态和权限计数；任一缺口必须进入 blocked_claims。 |
| CR-017 复权声明 | 必须输出 `research_adjustment_policy`、`execution_price_policy`、view id、qfq `as_of_trade_date`、single-policy gate、legacy qfq baseline preserved 状态；不得把复权因子声明为完整公司行动链路审计。 |
| CR-015 QMT foundation 声明 | 必须输出 adapter mode、pre-trade risk result、OMS state summary、broker lake write mode、真实 QMT API 调用计数和凭据读取计数；CR-015 默认声明为 shadow / dry-run / mock foundation，不得声明真实发单可用。 |
| CR-016 QMT 激活声明 | 必须输出 stage gate、runbook、per-run 授权、对账、kill switch、资金放大 gate 和 CR-017 口径治理状态；不得在缺少门控证据时声明生产策略、实盘收益或可放大资金。 |

## 需求条目

| ID | 类型 | 需求描述 | 优先级 | 验收条件 | 来源 |
|----|------|---------|--------|---------|------|
| REQ-001 | 结构 | 项目必须以当前仓库根为工程根，并在仓库根下建立或使用 `data/`、`engine/`、`strategies/`、`notebooks/`、`reports/` 分层目录。 | P0 | Given 当前工作目录为仓库根, When 检查工程结构, Then 五个目录均位于仓库根下且职责与路径归属表一致。 | 用户原始输入修订, UC-01 |
| REQ-002 | 功能 | 数据层必须能从本地 `data/prices.parquet` 读取多股票日线收盘价，并返回按交易日对齐的价格矩阵。 | P0 | Given `data/prices.parquet` 存在且包含 `trade_date`, `symbol`, `close`, When 调用数据加载函数读取指定区间, Then 返回以交易日为索引、股票代码为列的 `close_df`。 | UC-01 |
| REQ-003 | 功能 | 数据层必须能读取沪深 300 成分股池；第一版允许使用固定当前沪深 300 成分股快照，并必须记录快照口径、`is_pit_universe=false` 和幸存者偏差。 | P0 | Given `data/index_members.parquet` 存在, When 回测启动, Then 系统可获得用于横截面排序的股票池列表，并在报告 metadata 中输出固定当前股票池、快照日期、非 PIT 标记和幸存者偏差提示。 | UC-01, UC-06 |
| REQ-004 | 功能 | 回测器必须基于交易日历支持每 N 个交易日调仓，单次参数名为 `rebalance_freq`。 | P0 | Given `rebalance_freq=20`, When 回测遍历交易日, Then 系统只在每 20 个交易日触发目标持仓更新。 | UC-02 |
| REQ-005 | 功能 | 动量策略必须按 T 日收盘后可得价格计算过去 `lookback_days` 的收益率，成交只能在 T+1 或之后发生。 | P0 | Given `lookback_days=20` 且信号日为 `T`, When T 日收盘后计算动量, Then 使用 `close[T] / close[T-20] - 1` 计算排名，且任一成交记录的成交日不早于 T+1。 | UC-02 |
| REQ-006 | 功能 | 动量策略必须支持按 `top_fraction` 选择排名靠前股票，且排名前必须剔除历史窗口不足、端点价格缺失或可用时点不合规的股票。 | P0 | Given 股票池有 300 只股票且 `top_fraction=0.10`, When 生成买入集合, Then 初始买入数量按过滤后的可排名股票数计算，历史窗口不足或缺失端点价格的股票不参与排名。 | UC-02 |
| REQ-007 | 功能 | 动量策略必须支持 `sell_buffer` 持仓缓冲，已持仓股票跌出缓冲范围后才卖出。 | P0 | Given 当前持仓股票仍位于前 `sell_buffer` 排名范围内, When 调仓, Then 该股票可继续保留在目标持仓中。 | UC-02 |
| REQ-008 | 功能 | 组合层必须将目标持仓转换为等权目标权重；默认全仓等权，因缺失成交价、无成交或不可交易无法持有的股票权重留作现金或记录为未成交。 | P0 | Given 目标持仓数量为 20, When 生成目标权重, Then 可交易目标每只股票目标权重相等，股票权重合计不超过 100%，缺失成交价或无成交的目标不被静默填充，剩余部分记为现金或未成交明细。 | UC-02 |
| REQ-009 | 功能 | 组合层必须支持 `commission_rate`、`slippage_rate`、`sell_tax_rate` 三类成本参数，并按交易方向、成交金额基数和调仓扣除时点记录成本。 | P0 | Given 买入成交金额和卖出成交金额均大于 0, When 发生调仓交易, Then 买入扣除佣金和滑点，卖出扣除佣金、滑点和卖出税费，成本从调仓日组合净值中扣除并写入成本明细。 | UC-02 |
| REQ-010 | 功能 | 分析层必须输出日净值曲线、累计收益、年化收益、最大回撤和 Sharpe，并记录指标假设。 | P0 | Given 单次回测完成, When 读取结果对象, Then 结果至少包含上述 5 类输出，并记录年化交易日数、无风险利率和收益频率。 | UC-02 |
| REQ-011 | 功能 | 系统必须支持动量策略 60 组参数扫描，扫描候选列表字段为 `lookbacks`、`rebalance_freqs`、`fractions`。 | P0 | Given `lookbacks=[5,10,20,30,60]`、`rebalance_freqs=[5,10,20,30]`、`fractions=[0.05,0.10,0.20]`, When 运行扫描, Then 输出 60 行参数结果，单行中参数字段为 `rebalance_freq`。 | UC-03 |
| REQ-012 | 功能 | 参数扫描必须输出 `reports/momentum_param_sweep_local.csv`。 | P0 | Given 参数扫描完成, When 检查报告目录, Then 存在 CSV 且字段满足报告 schema。 | UC-03 |
| REQ-013 | 架构 | 策略逻辑必须拆分为信号层、组合层、分析层和扫描层，避免把本地回测器写成完整聚宽复制品。 | P0 | Given 查看 `engine/` 和 `strategies/`, When 评审模块职责, Then 策略选股、组合净值、绩效指标、参数扫描分别位于清晰边界内。 | UC-02, UC-03, UC-05 |
| REQ-014 | 架构 | 动量策略核心必须抽取为纯函数，便于本地回测器和聚宽策略复用或复制同一逻辑。 | P0 | Given 查看 `strategies/momentum.py`, When 定位动量收益和目标持仓函数, Then 函数不读写文件、不依赖回测引擎全局状态且可被单元测试调用。 | UC-02, UC-04 |
| REQ-015 | 约束 | 第一版可不精确建模完整停牌状态、涨跌停撮合、历史成分股变化、分红送转、分钟级撮合、真实成交量约束、新股上市初期特殊规则、退市整理与摘牌、ST 历史状态和财报披露日，但必须在报告 metadata 中警示。 | P0 | Given 第一版 Story 范围评审, When 检查任务列表和报告 schema, Then 这些能力仅作为后续扩展或明确排除项出现，且报告 metadata 包含对应限制项。 | UC-06 |
| REQ-016 | 数据 | 数据链路必须采用“独立数据准备/更新流程与回测主路径物理隔离；回测只读本地 parquet、manifest 和必要 metadata”的缓存策略。 | P0 | Given 数据已缓存, When 多次运行回测、扫描、候选筛选或本地差异分析, Then 主路径不发生网络请求、不自动拉取 AKShare/聚宽/其他远程数据，只读取本地标准化 parquet、manifest 和质量报告摘要。 | UC-01, UC-03 |
| REQ-017 | 验收 | 第一版必须能跑完整 2019-2025 区间。 | P0 | Given 本地数据覆盖 2019-01-01 至 2025-12-31, When 执行动量默认参数回测, Then 生成完整区间净值和指标。 | UC-02 |
| REQ-018 | 验收 | 本地扫描后只应将少量候选参数回填聚宽验证。 | P0 | Given 本地扫描完成, When 生成候选清单, Then 候选组数不超过 4 组，包含默认参数、Sharpe 最优、收益最优、保守低换手参数。 | UC-04 |
| REQ-019 | 扩展 | RSI 和 MACD 策略应复用同一数据层、组合层和分析层。 | P2 | Given 动量第一版完成, When 新增 RSI 或 MACD 策略, Then 不需要复制组合净值和指标计算代码。 | UC-05 |
| REQ-020 | 工程 | Python 依赖和脚本执行必须遵循项目 uv 规则。 | P0 | Given 项目需要 Python 代码或测试, When 添加依赖或运行脚本, Then 使用 `pyproject.toml`/`uv.lock` 和 `uv run`，不提交 `.venv/`。 | AGENTS.md |
| REQ-021 | 数据 | 数据加载层必须校验最小 parquet schema，并在字段缺失、类型不可转换或交易日序为空时 fail fast。 | P0 | Given 任一必需 parquet 文件缺少必需字段, When 启动回测, Then 系统停止执行并输出包含文件名和缺失字段的错误。 | UC-01 |
| REQ-022 | 数据 | 数据层必须输出稳定的 `close_df` 契约，并保证交易日序升序、去重且来自交易日历。 | P0 | Given 输入价格数据包含多个股票和交易日, When 加载指定区间, Then `close_df.index` 与交易日历交集一致且升序无重复，`close_df.columns` 为股票代码。 | UC-01 |
| REQ-023 | 策略 | 回测必须明确日序、成交价和收益归属：T 日收盘后生成信号，目标交易只能在 T+1 或之后生效，收益归属按 HLD 确认的日收益口径执行。 | P0 | Given 某日为信号日 `T`, When 生成目标持仓, Then 日志或结果元数据能说明信号日期、`decision_time`、成交日期、成交价口径和收益归属日期，且成交日期不早于 T+1。 | UC-02 |
| REQ-024 | 组合 | 净值序列必须保持完整性，不得出现负净值、非有限值、重复交易日或缺失起止日期。 | P0 | Given 回测完成, When 执行净值完整性检查, Then `nav` 序列日期唯一升序，首尾覆盖回测区间，所有净值为有限正数。 | UC-02 |
| REQ-025 | 分析 | 指标计算默认使用 252 个交易日年化，无风险利率默认 0 或显式参数化，并在报告中记录实际值。 | P0 | Given 单次回测完成, When 输出绩效指标, Then 报告包含 `annualization_days=252` 和 `risk_free_rate` 字段或元数据。 | UC-02 |
| REQ-026 | 扫描 | 参数扫描 CSV 必须按报告 schema 输出每组参数、绩效、换手、耗时、状态和错误信息。 | P0 | Given 60 组扫描中某组失败, When 扫描结束, Then CSV 仍包含该组参数，`status=failed` 且 `error_message` 非空；其他成功组继续输出指标。 | UC-03 |
| REQ-027 | 扫描 | 扫描失败策略必须支持“记录失败并继续”，不得因单组参数失败丢失整批扫描结果。 | P0 | Given 单个参数组合因数据不足失败, When 执行全量扫描, Then 扫描进程继续处理后续组合并在 CSV 中记录失败原因。 | UC-03 |
| REQ-028 | 候选 | 系统必须输出 `reports/momentum_candidates_local.csv`，用于聚宽少量验证。 | P0 | Given 参数扫描 CSV 已生成, When 生成候选清单, Then 候选清单字段满足报告 schema 且候选数不超过 4。 | UC-04 |
| REQ-029 | 候选 | 保守低换手候选必须在非失败扫描结果中选择，并优先满足换手较低、最大回撤可接受、收益或 Sharpe 不明显劣于中位水平的规则。 | P1 | Given 扫描结果包含 `turnover`, `max_drawdown`, `annual_return`, `sharpe`, When 选择保守低换手候选, Then `selection_reason` 说明换手排序、风险过滤和收益/Sharpe 对比依据。 | UC-04 |
| REQ-030 | 验收 | 聚宽方向一致口径必须比较候选排序方向、收益/回撤量级、换手特征和差异解释，不要求逐日净值一致。 | P0 | Given 用户手动获得聚宽候选验证结果, When 编写差异分析, Then 至少覆盖排序、收益、回撤、换手和差异原因五类字段。 | UC-04 |
| REQ-031 | 报告 | 固定股票池偏差报告必须输出快照日期、股票池数量、`is_pit_universe=false`、是否使用历史成分股、幸存者偏差警示和适用解释边界。 | P0 | Given 第一版使用固定当前沪深 300 成分股快照, When 生成单次回测或扫描报告, Then 报告 metadata 包含上述偏差字段，且不得把固定当前股票池表述为 PIT 股票池。 | UC-01, UC-06 |
| REQ-032 | 风险 | 参数扫描报告必须包含样本内过拟合警示；第一版不实现样本外拆分时，必须把样本外拆分列为 P1/P2 后续需求。 | P0 | Given 扫描报告生成, When 用户查看报告, Then 报告包含“扫描结果为样本内选择，不代表样本外稳定性”的警示，并在里程碑中保留样本外拆分后续项。 | UC-03 |
| REQ-033 | 可视化 | 第一版报告以 CSV 为必需交付；热力图、Notebook 和图形化展示为可选增强，不阻塞验收。 | P1 | Given 参数扫描完成, When 只生成 CSV 且无图表, Then 第一版验收仍可通过；若生成图表，图表必须可由 CSV 派生。 | UC-03 |
| REQ-034 | 离线 | 第一版回测、扫描、候选筛选和本地差异分析命令必须可在无网络环境下运行，前提是本地 parquet 覆盖区间、schema、manifest 和质量报告摘要满足要求。 | P0 | Given 断开网络且本地 parquet 覆盖区间和 schema 合规, When 执行默认回测、60 组参数扫描和候选筛选, Then 不发生网络请求且产出报告；报告披露数据覆盖区间、最近成功更新时间、数据新鲜度和已知失败项。 | UC-01, UC-03, UC-04 |
| REQ-035 | 成本 | 成本模型必须在报告中记录实际使用的 `commission_rate`、`slippage_rate`、`sell_tax_rate`，默认费率可在 HLD/LLD 中显式确认。 | P0 | Given 用户未传入费率且系统使用默认配置, When 输出回测结果, Then 报告记录三个成本参数的实际值和扣除口径。 | UC-02 |
| REQ-036 | 工程 | HLD/LLD 不得把第一版实现绑定到大型量化框架；如后续引入 RQAlpha、Backtrader、vectorbt 或 bt，必须作为后续迁移或优化决策单独评审。 | P1 | Given 进入方案设计, When 评审技术选型, Then 主方案仍为项目内轻量日频回测层，外部框架仅作为后续候选。 | UC-05, UC-06 |
| REQ-037 | 数据 | 回测、扫描、候选筛选和差异分析必须使用一致复权口径，并在报告 metadata 中记录实际口径。 | P0 | Given 同一次回测输入存在不同复权口径的价格字段或文件, When 启动回测或扫描, Then 系统拒绝运行或要求显式选择单一口径；Given 回测完成, When 查看报告 metadata, Then 可看到实际 `adjustment_policy`。 | UC-01, UC-02, UC-03 |
| REQ-038 | 数据 | 系统必须对所有参与决策的数据字段执行 `available_at <= decision_time` 校验或可审计推导。 | P0 | Given 某字段 `available_at` 晚于信号 `decision_time`, When 该字段被用于信号、过滤、股票池或成交判断, Then 系统阻止使用并记录错误；Given 字段缺少 `available_at`, Then 只有 HLD 批准的推导规则可作为替代。 | UC-01, UC-02 |
| REQ-039 | 策略 | 动量排名必须剔除历史窗口不足的股票。 | P0 | Given 某股票在信号日 T 之前不足 `lookback_days` 个有效历史窗口, When 计算动量排名, Then 该股票不参与排名、不进入买入集合，并在过滤统计中记录原因。 | UC-02 |
| REQ-040 | 数据 | 缺失价格、缺失成交价或无成交不得静默填充。 | P0 | Given 某股票信号端点价格缺失、成交日价格缺失或被标记无成交, When 运行回测, Then 系统剔除该股票、保留现金、记录未成交或失败原因，不得用前值、后值、0、指数收益或任意默认价格填充为真实价格。 | UC-01, UC-02 |
| REQ-041 | 报告 | 报告 metadata 必须强制输出第一版限制项，且单次回测、扫描和候选清单三类输出保持一致。 | P0 | Given 任一报告文件生成, When 检查 metadata 或 CSV 限制字段, Then 至少包含复权口径、信号/成交时点、`available_at` 规则、非 PIT 股票池、幸存者偏差、完整停牌、涨跌停、新股、退市、ST、财报披露日和历史成分变化限制。 | UC-03, UC-04, UC-06 |
| REQ-042 | 增强 | 后续应优先实现 PIT universe provider，以点时还原沪深 300 历史成分。 | P1 | Given 第一版报告显示固定当前股票池偏差, When 规划真实性增强, Then PIT universe provider 位于增强优先级首位，并能按日期返回当时可用股票池及其 `available_at`。 | UC-06 |
| REQ-043 | 增强 | 后续应实现交易状态表，用于表达停牌、无成交、特殊处理和可交易性。 | P1 | Given 后续数据包含交易状态表, When 回测生成成交, Then 组合层根据交易状态决定可交易、不可交易、留现金或延后处理，并输出原因。 | UC-06 |
| REQ-044 | 增强 | 后续应实现涨跌停约束，避免在不可成交价格上假设成交。 | P1 | Given 后续数据包含涨跌停价格或涨跌停状态, When 调仓目标触及涨停买入或跌停卖出限制, Then 系统按约束拒绝或延后成交，并在成交明细中记录原因。 | UC-06 |
| REQ-045 | 增强 | 后续引入财报、公告、ST 等事件字段时，必须实现事件级 `available_at`。 | P1 | Given 某事件字段被用于信号或过滤, When 计算决策, Then 系统使用事件披露或可用时间校验 `available_at <= decision_time`，不得用报告期日期替代披露日。 | UC-06 |
| REQ-046 | 增强 | 后续应输出偏差审计报告，汇总非 PIT、幸存者偏差、停牌、涨跌停、事件时点和成交假设对结果的影响。 | P1 | Given 增强回测完成, When 输出偏差审计报告, Then 报告列出启用/未启用的真实性约束、受影响样本数、收益/回撤/换手/候选排序变化和剩余限制。 | UC-04, UC-06 |
| REQ-047 | 数据准备 | 数据准备/更新流程必须显式处理数据源限速、字段变更、临时不可用和失败风险，不得把高频请求或无限重试压到数据源。 | P0 | Given 数据源返回限流、临时错误或字段缺失, When 执行数据准备, Then 系统按配置节流和有限重试处理，重试耗尽后记录失败项和错误信息，不进入无限循环，也不让回测主路径直接补抓。 | UC-01 |
| REQ-048 | 数据准备 | 数据准备/更新流程必须支持可配置请求节流参数 `request_interval_seconds`、`batch_size`、`max_concurrency`，默认采用保守串行抓取。 | P0 | Given `request_interval_seconds=2`, `batch_size=50`, `max_concurrency=1`, When 数据准备连续发起多个请求, Then 相邻请求时间间隔不小于 2 秒，单批规模不超过 50，且同一时刻并发请求数不超过 1。 | UC-01 |
| REQ-049 | 数据准备 | 请求节流必须可验证，数据准备运行记录必须能证明相邻请求时间间隔不小于配置值。 | P0 | Given 数据准备运行完成, When 检查 manifest 或日志中的请求时间, Then 任意相邻请求的时间差均大于等于 `request_interval_seconds`，不满足时任务标记为失败或质量报告标记异常。 | UC-01 |
| REQ-050 | 数据准备 | 数据准备/更新流程必须支持有上限的 `max_retries` 和可记录的 `backoff_policy`，不允许无限循环。 | P0 | Given `max_retries=3` 且数据源连续失败, When 执行数据准备, Then 同一批次最多尝试 1 次初始请求加 3 次重试，退避策略和每次重试时间写入 manifest 或日志，最终状态为 failed 或 partial_success。 | UC-01 |
| REQ-051 | 数据准备 | 数据准备/更新流程必须支持基于 manifest/checkpoint 的断点续传，不重复已成功批次，除非显式强制刷新或最近 N 个交易日回补。 | P0 | Given manifest 中批次 A 已成功、批次 B 失败, When 重新执行同一数据准备任务且未开启 `force_refresh`, Then 系统跳过批次 A，从批次 B 或后续缺口继续；若开启最近 N 个交易日回补，仅回补交易日历定义的窗口内批次。 | UC-01 |
| REQ-052 | 数据准备 | raw 缓存必须存在，标准化 parquet 必须可从 raw 缓存派生。 | P0 | Given 某批次数据准备成功, When 检查输出产物, Then 存在对应 raw 缓存路径和标准化 parquet 输出路径；Given 删除标准化 parquet 但保留 raw 缓存, When 执行标准化派生流程, Then 可重新生成等价 schema 的 parquet。 | UC-01 |
| REQ-053 | 数据准备 | 增量更新默认只补缺失日期或缺失 symbol/date，不重复全量抓取。 | P0 | Given 本地 parquet 已覆盖 2019-2025 中大部分 symbol/date, When 执行默认更新, Then 系统根据 manifest、parquet 覆盖范围和交易日历识别缺口，只请求缺失范围，不重新请求完整历史区间。 | UC-01 |
| REQ-054 | 数据准备 | 更新流程必须支持最近 N 个交易日可配置回补，且 N 基于交易日历而不是自然日。 | P0 | Given `recent_trade_days_backfill=5` 且交易日历中最近 5 个开市日跨越周末或节假日, When 执行数据更新, Then 只回补最近 5 个交易日对应的 symbol/date，而不是最近 5 个自然日。 | UC-01 |
| REQ-055 | 可追溯 | 数据准备必须输出 manifest/checkpoint，至少记录批次、数据源、接口、请求参数、股票/日期范围、请求时间、成功项、失败项、错误信息、重试次数、退避记录、raw 路径、标准化输出路径、覆盖范围和最终状态。 | P0 | Given 数据准备完成或部分失败, When 检查 manifest, Then 每个批次均包含上述字段，且最终状态只能是 success、partial_success、failed 或 skipped 等 HLD 明确定义的枚举值。 | UC-01 |
| REQ-056 | 可验证 | 数据质量报告必须记录覆盖区间、缺失统计、失败统计、失败 symbol/date、字段缺失、重复记录、异常价格、回补数量、最近成功更新时间和数据新鲜度。 | P0 | Given 数据准备或更新流程结束, When 读取 `reports/data_quality_report.*`, Then 可看到上述质量字段；若存在失败项或异常价格，报告中包含可定位的 symbol/date 和原因。 | UC-01, UC-03 |
| REQ-057 | 降级 | 数据源不可用时，若本地 parquet 覆盖区间和 schema 合规，回测、扫描和候选筛选必须继续离线运行，并披露数据新鲜度和失败项。 | P0 | Given 数据源接口不可用但本地 parquet 满足 2019-2025 回测区间和 schema, When 执行默认回测、参数扫描或候选筛选, Then 系统不联网、不阻塞运行，报告或质量报告披露最近成功更新时间、数据新鲜度、失败批次和可能影响。 | UC-01, UC-03, UC-04 |
| REQ-058 | 增强 | 后续真实性增强引入新数据字段时，必须同步扩展 raw 缓存、manifest、质量报告和离线回测读取契约。 | P1 | Given 后续新增 PIT universe、交易状态、涨跌停或事件字段, When 规划增强 Story, Then 该 Story 同时定义 raw 到标准化派生规则、manifest 字段、质量报告检查和回测离线读取方式。 | UC-06 |
| REQ-059 | 数据源 | Tushare 真实源必须默认关闭，并且只有 source enabled、exact allowlist 命中、`TUSHARE_TOKEN` 环境变量存在、用户显式执行数据准备命令时才允许真实 API 调用。 | P0 | Given 未配置 token、source 未启用或接口未 allowlist, When 导入 Tushare connector 或执行 plan/dry-run, Then 网络调用次数为 0 且返回结构化 fail-fast；Given 条件满足且用户显式执行 fetch/backfill, Then 仅 `market_data` 写湖层允许调用 Tushare。 | UC-07, CR005-AC-001, CR005-AC-002 |
| REQ-060 | 数据准备 | 系统必须提供 `hs300_index` 的 Tushare 写湖 / backfill 作业规格，支持 plan、fetch/backfill、normalize、validate/catalog，并将 raw、manifest、canonical/gold、quality 和 catalog 作为正式输出。 | P0 | Given 用户执行 `target_dataset=hs300_index` 的 plan, When 检查计划输出, Then 包含 source、exact interface、date range、batch 参数、lake root、预计输出和 quality report path 且不联网；Given 用户显式执行 fetch/backfill, Then 成功或部分成功均写入 manifest 并生成可追溯质量结果。 | UC-07, CR005-AC-003, CR005-AC-007 |
| REQ-061 | 数据 | 本地 `hs300_index` benchmark 必须来自 canonical/gold 数据集，最小字段包含 `trade_date`、`index_code`、`close`、`pct_chg`、`benchmark_kind`、`source`、`source_interface`、`source_run_id` 和 `available_at`。 | P0 | Given `hs300_index` canonical/gold 存在, When benchmark resolver 读取请求区间, Then 输出字段满足最小 schema，并且 `index_code`、`benchmark_kind`、source interface 与 source run 可追溯；字段缺失时不得返回 available。 | UC-07, CR005-AC-003 |
| REQ-062 | 可用性 | benchmark resolver 必须返回 typed `BenchmarkResult` 或等价结构，状态至少包含 `available`、`unavailable`、`required_missing`，并在缺失时携带 `next_action` 与 `remediation_job_spec`。 | P0 | Given 本地 `hs300_index` 缺失、覆盖不足或 quality fail, When 消费层请求 benchmark, Then 返回机器可解析的 `status=unavailable` 或 `status=required_missing`、`target_dataset=hs300_index`、`next_action` 和 `remediation_job_spec`；消费层不得自动执行补齐。 | UC-07, CR005-AC-003, CR005-AC-008 |
| REQ-063 | 数据准确性 | `hs300_index` 可用路径必须冻结 benchmark 口径并输出质量解释，至少包含 `benchmark_kind`、`index_code`、Tushare source interface、交易日历分母、coverage 起止、covered/missing trade dates、gap reason、quality threshold、`quality_status` 与 `benchmark_status` 映射。 | P0 | Given benchmark resolver 返回 `available`, When 检查结果和 quality report, Then 上述字段均存在且 `quality_status` 通过；Given `benchmark_kind` 仍为 OPEN 或质量阈值未满足, Then 只能返回 `required_missing` / `unavailable`，不得声明为可比较基准。 | UC-07, CR005-AC-003, CR005-AC-005, CR005-AC-007 |
| REQ-064 | 分层约束 | Data Loader、实验入口、benchmark resolver、Backtrader adapter 均属于只读 consumer，不得导入 Tushare connector/runtime/storage、不得读取 `TUSHARE_TOKEN`、不得发起网络请求或自动补数。 | P0 | Given 断网环境和本地数据可用, When 执行 Data Loader、实验十/十二、benchmark resolver 或 Backtrader optional backend, Then 网络调用次数为 0；When 做静态导入扫描, Then consumer 不导入 `market_data.connectors`、runtime 或 storage。 | UC-07, CR005-AC-008, CR005-AC-010, CR005-AC-011, CR005-AC-014 |
| REQ-065 | 约束 | 缺失 `hs300_index` 时不得用旧等权买入持有、同股票池收益或其他代理填充 benchmark 字段；如保留代理，只能命名为 `proxy_baseline` 并与 `hs300_index` 指标隔离。 | P0 | Given 本地 `hs300_index` 缺失, When 生成回测或实验报告, Then `hs300_index` 相对收益字段为空或标记 unavailable；若存在代理基准，字段名必须为 `proxy_baseline` 且报告说明不能解释为沪深 300 相对收益。 | UC-07, CR005-AC-003, CR005-AC-008 |
| REQ-066 | 数据 | `trade_calendar`、`index_weights`、`prices` / `adj_factor` 等 CR-005 P0/P1 数据集必须提供 exact source/interface 映射、PIT 可用性字段或复权字段，并进入 quality/catalog。 | P0 | Given CR-005 P0 dataset 完成 normalization, When 检查 contracts、quality 和 catalog, Then `trade_calendar` 支撑 open trade dates 分母，`index_weights` 记录 `index_code`、`con_code`、`trade_date`、`weight` 和可用性字段，`prices` 保存统一 `adjustment_policy` 与 adjusted price。 | UC-06, UC-07, CR005-AC-004, CR005-AC-005, CR005-AC-006, CR005-AC-012, CR005-AC-013 |
| REQ-067 | 质量 | 每个 CR-005 dataset 的质量报告必须分离 `fetch_status` 与 `dataset_status`，并输出 coverage、thresholds、denominator、source/interface、run lineage、缺口原因和可复现字段。 | P0 | Given 任一 CR-005 dataset 完成或部分失败, When 读取 quality CSV, Then 可看到 fetch/dataset 双状态、coverage 分母、阈值、source/interface、source_run_id、缺口列表和 gap explanation；远端失败但本地合规 parquet 可读时不得一律阻断 reader。 | UC-01, UC-07, CR005-AC-007 |
| REQ-068 | 对比 | 系统必须支持 Tushare 与至少一个本地 reference / AkShare fixture 的差异报告，用于解释 `hs300_index` 和相关 dataset 的数据差异。 | P1 | Given Tushare 与 reference fixture 均可读, When 执行 comparison, Then 输出差异报告，至少包含 dataset、date range、key count、missing keys、value diff summary、source_run_id、quality_status、gap explanation 和处理建议。 | UC-07, CR005-AC-009 |
| REQ-069 | 可验证 | 默认测试与默认消费路径必须离线、无 token 可运行；真实 Tushare 测试必须显式标记且不属于默认 pytest 阻塞路径。 | P0 | Given 未设置 `TUSHARE_TOKEN` 且网络不可用, When 执行默认测试或消费路径, Then 不需要 token、不联网且不失败于 Tushare 真实源；Given 真实源测试被显式选择, Then 需先通过 source enabled、allowlist、token 和 lake root 校验。 | UC-07, CR005-AC-010 |
| REQ-070 | 可选后端 | Backtrader 只能作为 optional backend 读取本地 canonical/gold 和 quality gate 后的干净 factor panel / score / OHLCV feed；未安装或输入不可用时返回结构化 `backend_unavailable` 或 data unavailable，轻量主路径继续可运行。 | P1 | Given Backtrader 未安装, When 用户未选择或选择 optional backend, Then 默认轻量主路径照常运行，optional backend 返回 `backend_unavailable`；Given Backtrader 已启用, When 检查 adapter, Then 不读取 token、不联网、不生成 PIT、不计算复权因子、不绕过 quality gate，并输出与轻量回测的对照结果。 | UC-07, CR005-AC-011, CR005-AC-014 |
| REQ-071 | 数据 | CR-011 新版实验 17-21 必须使用真实 `hs300_index` benchmark 作为生产级对照，并与 `proxy_baseline` 字段隔离。 | P0 | Given `benchmark_policy=hs300_required` 且目标研究区间已确定, When 构建新版因子研究输入, Then `hs300_index` 的 `benchmark_kind`、`index_code`、coverage 起止、交易日历分母、covered/missing trade dates、quality_status、source_interface 和 source_run_id 均存在且 quality pass；Given 任一字段缺失或 quality fail, Then 只输出 `required_missing` / `blocked_claims`，不得生成 `hs300_*` 生产级超额收益。 | UC-08, CR-011 |
| REQ-072 | 数据 | CR-011 新版因子研究必须使用 PIT 股票池、历史权重和股票生命周期数据，禁止把固定快照伪装为 PIT。 | P0 | Given `universe_mode=pit|required`, When 研究入口按任一交易日 as-of 构建股票池, Then 每个成员均可追溯 `index_members` / `index_weights` / `stock_basic` 的 `effective_date`、`available_at`、上市日期、退市日期、list_status 和 `pit_status`；Given PIT 不完整或只能使用固定快照, Then `production_strict_research` gate fail，并输出 fixed snapshot / limited PIT window / survivorship bias blocked claim。 | UC-08, CR-011 |
| REQ-073 | 数据 | CR-011 新版因子研究必须把停牌、涨跌停、ST、无成交、上市天数、退市/摘牌和事件状态纳入可交易性门控。 | P0 | Given 目标组合在调仓日产生买卖指令, When tradability gate 运行, Then 每个 symbol/date 输出可买、可卖、不可交易或需延后成交的枚举状态，并至少记录 suspended、limit_up、limit_down、st_status、no_trade、min_listing_days、delist_or_paused、event_blocked 等原因码；Given 相关数据缺失, Then 报告不得声明真实可成交，并输出受影响 symbol/date 数量。 | UC-08, CR-011 |
| REQ-074 | 数据 | CR-011 新版因子研究必须提供 clean execution feed，支持 open/high/low/close/VWAP 或可审计的日频执行价代理，并记录 `execution_price_policy`。 | P0 | Given 用户选择 `execution_price_policy`, When 构建回测成交价格, Then feed 至少输出 trade_date、symbol、open、high、low、close、volume、amount、vwap_or_proxy、execution_price、policy、available_at、source_run_id 和 unfilled_reason；Given VWAP 或 OHLC 缺失且降级为 close proxy, Then 报告必须标记 `execution_price_policy=close_proxy`，并在 `blocked_claims` 中禁止真实执行价声明。 | UC-08, CR-011 |
| REQ-075 | 数据 | CR-011 新版因子研究必须补齐复权因子与公司行动审计，解释异常价格和复权链路来源。 | P1 | Given `adjustment_policy` 被用于因子或收益计算, When 生成新版报告, Then 每个参与价格字段均可追溯 `adj_factor`、adjusted OHLC、source_run_id、lineage_raw_checksum 和公司行动来源；若发生分红、送转、拆合、配股或异常收益解释事件, Then 报告输出 symbol/date、事件类型、raw price、adjusted price、adj_factor_change 和 explanation；Given 公司行动不可用, Then 不得声明复权链路可审计。 | UC-08, CR-011 |
| REQ-076 | 数据 | CR-011 新版因子研究必须支持行业、市值、流通市值和风格暴露数据，用于行业/市值/风格中性 IC 与归因。 | P1 | Given 报告声明行业中性、市值中性、风格中性或纯因子 alpha, When 运行分析, Then 输入必须包含 PIT `industry_classification`、`market_cap`、`float_market_cap`、beta/style exposure、effective_date、available_at 和 coverage；输出至少包含 raw IC、industry_neutral_ic、market_cap_neutral_ic、style_neutral_ic、样本数、缺失率和 neutralization_status；Given 任一必需辅助数据缺失, Then 对应声明进入 `blocked_claims`。 | UC-08, CR-011 |
| REQ-077 | 数据 | CR-011 新版因子研究必须把流动性、容量和交易成本敏感性纳入策略验收。 | P1 | Given 因子策略组合已生成目标权重, When 运行容量成本分析, Then 系统至少输出 amount、volume、turnover、ADV、participation_rate、impact_cost、commission/slippage/tax、capacity_limit、cost_scenario_id 和 cost_after_return；成本敏感性至少覆盖当前默认成本、低成本、高手续费/滑点压力和容量压力四类场景；Given 流动性或容量数据缺失, Then 不得声明容量可交易。 | UC-08, CR-011 |
| REQ-078 | 可追溯 | CR-011 新版因子研究必须落盘完整 factor audit panel，保留 raw、directional、winsorized、zscore 四层因子值。 | P0 | Given 因子进入实验 17-21 新版候选集, When 生成 factor panel, Then 每个 factor_name / trade_date / symbol 至少包含 raw_value、directional_value、winsorized_value、zscore_value、direction_multiplier、winsor_lower、winsor_upper、imputation_flag、valid_mask、filter_reason、preprocessing_version、source_run_id、universe_mode 和 benchmark_kind；Given 任一层级缺失, Then 因子状态为 `factor_audit_incomplete` 且不得进入生产级结论。 | UC-08, CR-011 |
| REQ-079 | 可验证 | CR-011 新版因子研究必须执行稳健性验证，覆盖 rolling walk-forward、年度分层、市场状态分段、参数敏感性和成本敏感性。 | P0 | Given 新版实验完成基础回测, When 生成稳健性报告, Then 至少输出五类验证表：rolling walk-forward、annual、market_state、parameter_grid、cost_grid；每个切片均包含 start_date、end_date、sample_count、annual_return、max_drawdown、sharpe、turnover、ic_mean、icir、status 和 warning_reason；Given 只存在单一区间单一参数结果, Then `robust_validation_status=fail`。 | UC-08, CR-011 |
| REQ-080 | 报告 | CR-011 新版报告必须输出 allowed_claims / blocked_claims，并把旧实验 17-21 结论限定为探索基线。 | P0 | Given 新版报告生成, When 读取 report metadata, Then 至少包含 report_version、baseline_report_path、research_mode、gate_status、allowed_claims、blocked_claims、benchmark_kind、universe_mode、pit_status、tradability_gate_status、execution_price_policy、neutralization_status、capacity_cost_status 和 robust_validation_status；Given 任一生产级 gate 未通过, Then 相关声明必须出现在 `blocked_claims`，不得只用自由文本提示。 | UC-08, CR-011 |
| REQ-081 | 安全 | CR-011 默认路径不得真实联网、不得真实写 lake、不得操作旧 `data/**`、不得读取或打印凭据；真实执行必须由显式授权、allowlist 和 source enabled 同时控制。 | P0 | Given 未进入获授权真实执行 Story, When 运行 dry-run、默认测试、需求阶段检查或实验消费路径, Then network_calls=0、lake_writes=0、credential_reads=0、legacy_data_operations=0；Given 后续获授权真实执行, Then 报告只能记录 credential env var 名称、source/interface、run_id、相对路径或脱敏 root label，不得记录 token、用户名、密码、`.env` 内容或真实私有路径。 | UC-08, CR-011 |
| REQ-082 | 交付 | CR-011 新版研究产物必须与实验 17-21 旧报告隔离，旧报告作为 baseline 保留，不得覆盖或重写。 | P0 | Given `reports/experiment_17_21/factor_strategy_report.md` 已存在, When 生成 CR-011 新版报告、factor audit panel 或稳健性验证表, Then 输出到版本化新目录或带 CR-011 run_id 的新文件，并在 metadata 中记录 baseline_report_path；旧报告文件内容、旧 `proxy_baseline` 结论和旧产物清单保持可追溯。 | UC-08, CR-011 |
| REQ-083 | 报告 | CR-013 必须阻止 limited-window pass 被外推为 2020-2024 full-history 或更长历史的生产级可用声明。 | P0 | Given `reports/data_lake_readiness_2020_2024/readiness_summary.md` 显示 `overall_status=research_limited_only` 且 `readiness_matrix.csv` 中 10 个正式 dataset 均为 `limited_window_only`, When 生成报告 metadata、用户文档或 allowed_claims, Then `2020-01-01..2024-12-31` 必须标记为 blocked / research_limited_only，allowed_claims 不得包含 full-history `production_strict_research`、全历史 PIT current truth 或全历史可复现实盘级回测声明，并记录补齐 10 个正式 dataset 后重新审计的 remediation。 | UC-08, CR-013 |
| REQ-084 | 报告 | CR-013 必须将真实 VWAP、VWAP fill、分钟 / 逐笔 / 盘口 / 撮合执行价声明保持 blocked，直到真实执行价数据和审计同时通过。 | P0 | Given `execution_price_audit.csv` 中 `execution_price_status=required_missing`、`true_vwap_available_count=0` 或缺少 `vwap_status=available`, When 构建 execution feed、报告声明或文档说明, Then `blocked_claims` 必须包含 `real_vwap_execution` 和 `vwap_fill_claim`，分钟 / tick / Level2 order book / order match / 真实撮合执行价必须声明为 unsupported；close proxy 只能作为研究降级口径，不得写成真实 VWAP 或 production strict 真实执行价。 | UC-08, CR-013 |
| REQ-085 | 交付 | CR-013 必须把 unsupported data register 纳入用户文档和报告声明边界，逐项披露 research-only、unsupported 和 contract-supported-but-unavailable 内容。 | P0 | Given `unsupported_data_register.csv` 包含 `industry_classification`、`market_cap`、`style_exposure_beta_size_value_quality`、`capacity_inputs_turnover_adv_constraints`、`corporate_actions_full`、`non_hs300_benchmark`、`minute_tick_level2_order_match`、`microstructure_impact_cost`、`real_vwap_execution` 等行, When 生成 README、USER-MANUAL、readiness summary 或新版研究报告, Then 每一行必须进入 supported / research-only / unsupported / blocked claim 摘要，保留 `status`、`reason`、`pass_denominator=excluded`，且不得被计入正式 dataset pass 分母或 allowed production claim。 | UC-08, CR-013 |
| REQ-086 | 安全 | CR-013 需求、设计、文档刷新和默认验证不授权 provider fetch、真实 lake 写入、凭据读取、旧 `data/**` 读取或旧报告覆盖。 | P0 | Given 执行 CR-013 需求增量、声明边界检查、dry-run 或默认验证, When 检查运行计数与文件变更, Then `provider_fetches=0`、`lake_writes=0`、`credential_reads=0`、`legacy_data_reads=0`、`old_report_overwrites=0`；Given 后续需要补齐 2020-2024、接入分钟 / VWAP 数据或刷新正式 register, Then 必须由单独 Story / CP5 门控和用户显式授权后才能执行真实 provider / lake / credential / old data 操作。 | UC-08, CR-013 |
| REQ-087 | 可追溯 | CR-013 必须把 2020-2024 readiness 报告、execution price audit 和 unsupported register 作为旧证据基线保留，后续整改不得覆盖这些触发证据。 | P0 | Given `reports/data_lake_readiness_2020_2024/*` 和 `reports/data_lake_readiness_limited_2025_2026/unsupported_data_register.csv` 已作为 CR-013 证据, When 后续生成 full-history gap register、补数路线图、新 readiness run 或刷新后的 unsupported register, Then 输出必须使用新 run_id、新目录或版本化文件，并在 metadata 中记录 CR-013 evidence_paths 与 old_baseline_preserved=true；不得修改或覆盖本轮证据文件。 | UC-08, CR-013 |
| REQ-088 | 数据 | CR-014 必须将目标定义为 A 股证券自存在 / 上市日起至当前交易日的 production current truth，而不是固定历史窗口或 limited-window pass。 | P0 | Given CR-014 readiness summary 生成, When 检查 `readiness_scope`、`universe_scope` 和 `current_trade_date_policy`, Then 范围必须标明全 A 股、每只证券自存在 / 上市日起、截至当前交易日；每个发布为 current truth 的 P0 dataset 必须输出 coverage numerator / denominator、缺口清单和 evidence_paths；任一 P0 gate 未通过时 allowed_claims 不得包含全 A since-inception production current truth。 | UC-09, CR-014 |
| REQ-089 | 数据 | CR-014 必须显式建模证券生命周期、退市 / 摘牌和代码变更，禁止用当前股票快照伪装 PIT 历史。 | P0 | Given 全 A universe 构建或 as-of 查询运行, When 检查任一 symbol/date, Then 可追溯上市 / 存在起始日、退市 / 摘牌日、list_status、代码变更、简称变更、交易所 / 板块归属、effective_date、available_at、source_interface 和 run_id；Given 任一必需生命周期字段缺失, Then 返回 `required_missing` / `blocked_claims`，不得 publish 为 production current truth。 | UC-09, CR-014 |
| REQ-090 | 数据架构 | CR-014 P0 dataset 必须保留 raw / manifest / canonical / gold / quality / catalog 分层，每层职责、输入、输出和 lineage 必须可审计。 | P0 | Given 任一 P0 dataset 完成一次候选生产, When 检查 lake 分层, Then raw 可追溯 provider 原始响应或原始切片，manifest 记录 run/batch/idempotency/request/status，canonical/gold 保存标准化 Parquet，quality 输出 coverage/readiness，catalog 仅保存已发布 current pointer；缺任一必需层或 lineage checksum 时不得 publish。 | UC-09, CR-014 |
| REQ-091 | 数据发布 | CR-014 catalog current pointer 必须由显式 publish 更新，validate pass、quality report 或 DuckDB 查询结果不得自动成为 current truth。 | P0 | Given validate 结果为 pass, When 尚未执行显式 publish, Then catalog current pointer 不变且 reader 返回旧 current truth 或 candidate_unpublished；Given publish 执行并通过 quality/readiness policy, Then current pointer 记录 dataset、schema_version、coverage_start/end、coverage_denominator、latest_manifest_run_id、lineage checksum、published_at 和 known_limitations。 | UC-09, CR-014 |
| REQ-092 | 数据运维 | CR-014 必须支持增量刷新、最近 N 个交易日回补和 replay，并保证 replay 不触发 provider、不读取凭据、不污染 current pointer。 | P0 | Given 已存在成功批次、失败批次和缺口日期, When 生成增量计划, Then 默认 skip 已成功批次、retry 失败批次、只补缺口和经批准的最近 N 个交易日；Given 执行 replay, Then provider_fetches=0、credential_reads=0、raw_writes=0，输出 canonical / quality candidate 或审计结果，current pointer 仅在后续显式 publish 后变化。 | UC-09, CR-014 |
| REQ-093 | 架构候选 | CR-014 必须把 DuckDB 明确为 HLD 待决策的 read-only query / audit / feature extraction 候选能力，不得在需求阶段直接承诺依赖引入。 | P1 | Given 仍处于 requirement-clarification 或 CP2 前, When 检查依赖和设计声明, Then `pyproject.toml` / `uv.lock` 不新增 DuckDB，需求只记录 DuckDB 候选用途、只读边界和待决策项；Given 后续 HLD 评估 DuckDB, Then 默认只能读取 Parquet / catalog 用于 coverage audit、PIT join、feature extraction 和 pandas/pyarrow parity，不得替代 Parquet lake / catalog / manifest 事实源。 | UC-09, CR-014 |
| REQ-094 | 安全 | CR-014 需求澄清、默认验证和 HLD 前工作不授权 provider fetch、真实 lake 写入、凭据读取、旧 `data/**` 操作、旧 reports 覆盖或 DuckDB 依赖修改。 | P0 | Given 执行 CR-014 需求增量、dry-run、默认测试或文档整理, When 检查权限计数和文件变更, Then `provider_fetches=0`、`lake_writes=0`、`credential_reads=0`、`legacy_data_reads=0`、`legacy_data_lists=0`、`legacy_data_copies=0`、`legacy_data_deletes=0`、`old_report_overwrites=0`、`dependency_changes=0`；任何真实执行必须等待 CP5 与用户显式授权。 | UC-09, CR-014 |
| REQ-095 | 报告 | CR-014 必须输出 allowed_claims / blocked_claims / required_missing，阻止 limited-window、2020-2024 roadmap 或旧报告被外推为全 A 全历史 production current truth。 | P0 | Given 生成 readiness summary、用户文档或研究报告, When 任一 P0 dataset、证券生命周期、catalog pointer、quality/readiness 或权限 gate 未通过, Then blocked_claims 必须列出缺口、证据路径、解除条件和影响声明；allowed_claims 只能包含已通过当前 truth 和审计的范围，不得包含未验证的全 A since-inception claim。 | UC-09, CR-014 |
| REQ-096 | 验证 | CR-014 必须建立可量化验证场景，覆盖全 A coverage denominator、生命周期、P0 分层、current pointer、增量刷新 / replay、DuckDB 只读边界、权限计数和 claim boundary。 | P0 | Given 进入 CP2 或后续测试策略, When 检查验证矩阵, Then 至少包含 TS-014-01 至 TS-014-07，且每个场景都有输入 / 前置、可检查输出和对应 REQ / UC 来源；缺少任一 P0 验证维度时 ready_for_design 不得置为 true。 | UC-09, CR-014 |
| REQ-097 | 时间边界 | CR-014 的“当前交易日”必须在 CP2/HLD 中明确为最近已闭市交易日或用户显式批准的其他口径，并进入 current truth / refresh / claim metadata。 | P0 | Given 未确认 current trading day policy, When 生成全历史 readiness 或 current truth 声明, Then 只能标记 `[待确认]` 或 `required_missing`，不得声明 up-to-date production current truth；Given policy 已确认, Then report metadata 必须记录 policy、as_of_trade_date、calendar_source、refresh_lag 和是否包含最近 N 交易日回补。 | UC-09, CR-014 |
| REQ-098 | 数据 | CR-017 必须将 `prices_raw` 与 `adj_factor` 作为复权事实源，原始交易价格不得被 qfq/hfq 覆盖。 | P0 | Given 构建复权双视图候选数据, When 检查事实源层, Then `prices_raw` 保留未复权 OHLCV、source/interface、run_id、batch_id、available_at、lineage checksum 和 quality status；`adj_factor` 保留复权因子、provider 字段解释、因子方向、可用时间和 source_run_id；不得只有 qfq/hfq 成品表而无 raw + adj_factor 事实源。 | UC-12, CR-017 |
| REQ-099 | 数据 | CR-017 必须独立派生 `prices_qfq`、`prices_hfq` 和 `returns_adjusted`，不得在同一个 `prices` frame 中混存 raw/qfq/hfq。 | P0 | Given raw 与 adj_factor 可用, When 生成派生视图, Then qfq、hfq、returns_adjusted 具有独立 dataset/view id、schema_version、derivation_version、source_run_id、lineage 和 quality_status；Given 单个 frame 同时包含多个 adjustment policy 且无显式 view 隔离, Then validation fail。 | UC-12, CR-017 |
| REQ-100 | 数据 | CR-017 的 qfq 物化结果必须记录 `as_of_trade_date` 和输入 snapshot，以解释前复权历史价格漂移。 | P0 | Given 同一历史交易日在不同 as-of 下重算 qfq, When 比较 qfq 输出, Then 每条 qfq 或其 dataset metadata 可追溯 `as_of_trade_date`、input_snapshot_id、source_run_id 和 derivation_version；不得无声覆盖旧 qfq 基线或让历史价格变化不可审计。 | UC-12, CR-017 |
| REQ-101 | 数据 | CR-017 reader / validation 必须强制同一研究 run 使用一个明确 `research_adjustment_policy`。 | P0 | Given 用户请求研究 run, When 输入同时包含 raw、qfq、hfq 或 returns_adjusted 且未指定单一 policy, Then 系统返回 structured blocked reason；Given 已指定 policy, Then 报告 metadata 记录 policy、view_id、source_run_id 和 single_policy_gate_status。 | UC-12, CR-017 |
| REQ-102 | 安全 | CR-015 / CR-016 的 QMT order intent、委托、成交和 broker 对账必须使用 `execution_price_policy=raw`，qfq/hfq 只允许作为研究 metadata。 | P0 | Given OMS 生成 order intent 或 QMT adapter 处理委托 / 成交 / 对账, When 检查价格字段, Then `execution_price_policy=raw` 且 price_source 为 raw / broker price；Given qfq/hfq 价格被用于委托价、成交价或对账价, Then pre-trade / validation 必须 hard block 并输出 blocked reason。 | UC-10, UC-11, UC-12, CR-015, CR-016, CR-017 |
| REQ-103 | 迁移 | CR-017 必须保留旧 qfq 默认口径和旧报告作为历史基线，并为双视图升级提供迁移 / 兼容声明。 | P0 | Given 旧报告或旧 qfq 数据已存在, When 生成 CR-017 readiness / migration 摘要, Then 输出 `legacy_qfq_baseline_preserved=true`、旧基线路径或引用、迁移影响、兼容入口、禁止覆盖声明和后续 CP5 前置条件；不得批量重算或覆盖旧 qfq 数据。 | UC-12, CR-017 |
| REQ-104 | 安全 | CR-017 需求、设计和默认验证不授权真实抓取、真实写湖、发布 current pointer、批量迁移旧数据、修改代码或引入依赖。 | P0 | Given 执行 CR-017 需求增量、HLD 前整理、dry-run 或默认验证, When 检查权限计数和文件变更, Then provider_fetches=0、lake_writes=0、credential_reads=0、current_pointer_publishes=0、legacy_qfq_overwrites=0、dependency_changes=0；任何真实操作必须等待 Story / CP5 和用户显式授权。 | UC-12, CR-017 |
| REQ-105 | 架构 | CR-015 QMT 接入必须采用 Windows QMT / MiniQMT 节点、XtQuant 外部 Python API、OMS 和 QMT adapter 边界，策略层不得直接调用 QMT API。 | P0 | Given 策略产生目标组合, When 进入交易接入链路, Then 策略层只提交目标组合或 order intent 请求；静态导入扫描或调用审计不得发现策略层直接导入 / 调用 QMT / XtQuant 下单接口；所有 broker 触达必须经 OMS、risk 和 adapter。 | UC-10, CR-015 |
| REQ-106 | 交易合同 | CR-015 OMS 必须把目标组合转换为 order intent，并显式记录 `research_adjustment_policy` 与 `execution_price_policy=raw`。 | P0 | Given 目标组合包含 symbol、target weight、当前持仓和现金 snapshot, When OMS 生成 order intent, Then 每条 intent 至少包含 strategy_id、run_id、signal_date、target_trade_date、symbol、side、target_qty 或 target_weight、cash / holdings snapshot 引用、research_adjustment_policy、execution_price_policy、risk_profile 和 idempotency_key；缺少口径字段时不得进入 adapter。 | UC-10, CR-015, CR-017 |
| REQ-107 | 交易状态 | CR-015 必须建立本地 OMS 订单状态机，覆盖 accepted、partially_filled、filled、cancel_pending、canceled、rejected、failed、unknown、timeout 等状态。 | P0 | Given mock broker 返回部分成交、拒单、撤单、unknown 或 timeout 事件, When OMS 处理事件, Then 状态迁移符合状态机定义，记录 event_time、broker_order_ref、fill_qty、filled_amount、reason、retry / manual_review 标记；unknown 不得静默当作成功或失败。 | UC-10, CR-015 |
| REQ-108 | 数据 | CR-015 必须设计外置 broker lake，用于订单、成交、持仓、资产、错误和对账事件审计，并与仓库 `data/**` / `reports/**` 隔离。 | P0 | Given 生成 broker event 或 reconciliation event, When broker lake 处于未授权真实写入状态, Then 只输出 mock / dry-run 审计或写入计划；Given 后续获授权写入, Then root 必须为外置 `BROKER_LAKE_ROOT` 或等价配置，并记录 run_id、schema_version、redaction_status、retention_policy 和 lineage；不得写入仓库 `data/**` / `reports/**`。 | UC-10, CR-015 |
| REQ-109 | 风控 | CR-015 pre-trade risk gate 必须为 hard block，覆盖现金、整手、T+1 可卖、可用持仓、价格口径、重复下单和限额规则。 | P0 | Given 任一 order intent 触发现金不足、非 100 股整手、T+1 不可卖、可用持仓不足、qfq/hfq 执行价、重复 intent、单票 / 组合超限或异常价格, When pre-trade risk 运行, Then intent 被 hard block，adapter 调用次数为 0，blocked reason 和 rule_id 可审计。 | UC-10, CR-015 |
| REQ-110 | 安全 | CR-015 默认运行模式必须限定为 shadow / dry-run / mock adapter，真实 QMT 下单、撤单、账户写操作和凭据读取保持 0。 | P0 | Given 未进入 CR-016 获授权阶段, When 执行 CR-015 foundation 测试、dry-run 或 mock adapter, Then `real_order_calls=0`、`real_cancel_calls=0`、`account_write_calls=0`、`credential_reads=0`；任何真实 API 调用必须被 blocked 并指向 CR-016 per-run 授权流程。 | UC-10, CR-015 |
| REQ-111 | 安全 | CR-015 / CR-016 必须对 QMT 凭据、账户、session、cookie、交易密码、`.env` 内容和真实私有路径做脱敏和禁入库控制。 | P0 | Given 生成日志、报告、broker lake event 或错误信息, When 内容包含凭据值、账户号、session、cookie、交易密码、`.env` 内容或真实私有路径, Then redaction gate 必须阻断或脱敏；报告只允许保留环境变量名、脱敏账户标签、source/interface、run_id 和脱敏 root label。 | UC-10, UC-11, CR-015, CR-016 |
| REQ-112 | 运行治理 | CR-016 必须按 `shadow -> QMT 模拟盘 -> 实盘只读 -> 小资金实盘 -> 放大资金` 顺序推进，阶段不可跳过。 | P0 | Given 用户请求进入某一阶段, When 上一阶段验证、runbook、对账、授权或风险 gate 缺失, Then 系统返回 blocked stage gate result；Given 阶段完成, Then 输出准入证据、退出结果、回滚条件和下一阶段前置项。 | UC-11, CR-016 |
| REQ-113 | 运行治理 | CR-016 进入 QMT 模拟盘前必须完成 runbook，覆盖启动、审批、异常处理、对账、kill switch、暂停 / 恢复和回滚。 | P0 | Given 用户请求启用 QMT 模拟盘, When runbook 不存在或缺少异常处理 / 审批 / kill switch / recovery 内容, Then stage gate fail；Given runbook 完整, Then runbook_status=pass 并记录版本、适用阶段和审批状态。 | UC-11, CR-016 |
| REQ-114 | 安全 | CR-016 任一真实 QMT 操作必须具备 per-run 授权，授权字段至少覆盖账户模式、策略、日期、资金上限、操作范围、审批人和回滚策略。 | P0 | Given 请求真实发单、撤单、账户查询、账户写操作或进入实盘只读 / 小资金实盘阶段, When per-run 授权缺少任一必需字段, Then 真实 API 调用次数为 0 并输出 missing_authorization_fields；Given 授权存在, Then 报告只记录脱敏授权摘要，不记录凭据值。 | UC-11, CR-016 |
| REQ-115 | 交易策略 | CR-016 默认执行策略必须为 T 日收盘后信号，T+1 使用限价 / 保护价执行，盘中即时信号即时下单不得作为默认路径。 | P0 | Given signal_date=T, When 生成 QMT 订单计划, Then decision_time 不早于 T 日收盘后，target_trade_date 不早于 T+1，订单计划包含 limit / protect price policy、timeout / cancel policy 待 CP3 冻结项；Given 请求 T 日盘中即时下单, Then 默认 blocked。 | UC-11, CR-016 |
| REQ-116 | 对账 | CR-016 必须提供盘前、盘中、盘后对账，覆盖委托、成交、持仓、资产、现金和 broker lake 事实差异。 | P0 | Given QMT 模拟盘或实盘只读阶段运行, When 对账执行, Then 输出 pre_market、intraday、post_market reconciliation report，包含 broker snapshot、local state、diff、threshold、owner、action 和 status；差异超阈值时进入 blocked 或 manual_review。 | UC-11, CR-016 |
| REQ-117 | 运行治理 | CR-016 必须具备 kill switch，支持停止新单、撤可撤单、冻结策略、暂停 / 恢复和人工接管。 | P0 | Given heartbeat fail、风控异常、对账差异超阈值或人工触发 kill switch, When kill switch 执行, Then 停止新单、按规则撤可撤单、冻结策略状态并生成 incident event；恢复前必须满足恢复条件并记录接管人、时间和处理结果。 | UC-11, CR-016 |
| REQ-118 | 研究治理 | CR-016 模拟盘前必须冻结实验注册，记录策略版本、参数、数据口径、成功 / 失败标准和报告声明边界。 | P0 | Given 用户准备进入 QMT 模拟盘, When 检查实验注册, Then strategy_version、parameter_set_id、research_adjustment_policy、execution_price_policy、success_criteria、failure_criteria、start_date、end_date 和 allowed / blocked claims 均存在；缺失时不得把模拟盘结果解释为可比较实验。 | UC-11, CR-016, CR-017 |
| REQ-119 | 资金放大 | CR-016 资金放大必须受研究成熟度和运行稳定性 gate 约束，CR-017 复权治理未完成时不得进入资金放大或生产策略声明。 | P0 | Given 用户请求从小资金实盘进入放大资金, When 检查 gate, Then 必须包含模拟盘 / 小资金稳定性、对账通过、kill switch 演练、PIT / benchmark / exposure / capacity / cost / execution claim 状态和 CR-017 实现验证；任一 P0 gate 未过时返回 blocked_claims。 | UC-11, CR-016, CR-017 |
| REQ-120 | 约束 | CR-015 / CR-016 不得解除真实 VWAP、minute、tick、level2、order-match、微观结构冲击成本或真实撮合执行价的 blocked claim。 | P0 | Given QMT foundation 或 activation 文档、报告或 allowed_claims 生成, When 检查执行价声明, Then 不得包含真实 VWAP / VWAP fill / minute / tick / level2 / order-match / microstructure impact cost 已支持声明；除非后续新 CR、CP5 和真实数据审计单独通过。 | UC-10, UC-11, CR-015, CR-016 |
| REQ-121 | 验证 | CR-015 / CR-016 / CR-017 必须建立可量化验证场景，覆盖 QMT API 绕过、pre-trade hard block、OMS 状态机、broker lake 脱敏、复权双视图、单 run 口径、raw 执行价、阶段激活、runbook / 授权、对账和 kill switch。 | P0 | Given 进入 CP2 或后续测试策略, When 检查验证矩阵, Then 至少包含 TS-015-01 至 TS-016-03 和 TS-017-01 至 TS-017-03，且每个场景都有输入 / 前置、可检查输出和对应 UC / REQ 来源。 | UC-10, UC-11, UC-12, CR-015, CR-016, CR-017 |
| REQ-122 | CP3 输入 | CR-015 / CR-016 / CR-017 的 CP3 HLD 必须冻结仍开放的实现级决策，包括 qfq/hfq 公式、provider 字段解释、broker lake schema、OMS 状态机映射、pre-trade risk 清单、阶段准入阈值、限价 / 保护价策略、对账阈值和 kill switch 行为。 | P0 | Given 进入 CP3 HLD 评审, When 检查 Decision Brief 或 HLD 待决策项, Then REQUIRED_FOR_CP3 开放问题均有推荐方案、备选方案、影响分析和明确决策；缺少任一关键决策时不得批准进入对应 Story Plan / LLD。 | UC-10, UC-11, UC-12, CR-015, CR-016, CR-017 |
| REQ-123 | 优先级 | CR-018 必须把数据湖 production current truth 闭环列为 QMT simulation 之前的最高优先级。 | P0 | Given 用户请求推进 QMT simulation / live_readonly / small_live / scale_up, When 数据湖未 publish 或生产口径研究重跑未通过, Then stage gate 必须返回 `blocked_by_data_lake_production_truth` 或等价结构化阻断原因，不得进入真实或模拟 QMT 操作。 | UC-13, UC-14, CR-018 |
| REQ-124 | 数据 | CR-018 必须定义 production current truth 完成条件，覆盖 release scope、as_of_trade_date、dataset group、quality/readiness、allowed_claims / blocked_claims 和 rollback。 | P0 | Given 生成 release readiness 或发布摘要, When 检查 production current truth 字段, Then 必须包含 `release_id`、`release_scope`、`as_of_trade_date`、universe 口径、dataset 清单、coverage、quality 结果、blocked claims、rollback target 和 evidence_paths；任一必需字段缺失不得 publish。 | UC-13, CR-018 |
| REQ-125 | 数据 | CR014 S14 的 `prices` / `adj_factor` candidate 只能作为 CR-018 输入事实，不得自动 publish 为 current truth。 | P0 | Given `prices` / `adj_factor` candidate read/query smoke 通过, When 未经过 Explicit Publish Gate, Then production current reader 必须保持 `catalog_not_published` 或等价阻断；文档和报告不得把 candidate、validate PASS 或 parity PASS 写成 published current truth。 | UC-13, CR-018 |
| REQ-126 | 数据 | CR-018 必须补齐或结构化阻断 PIT universe、证券 lifecycle、上市 / 退市、代码变更和交易所 / 板块迁移。 | P0 | Given 构建 production release denominator 或研究重跑 universe, When 检查任一 symbol/date, Then 必须能追溯 list_date、delist_date、list_status、code-change mapping、exchange/board、effective_date、available_at、source_interface 和 run_id；缺失时输出 `required_missing` 并阻断 PIT/current truth 声明。 | UC-13, UC-14, CR-018 |
| REQ-127 | 数据 | CR-018 必须补齐或结构化阻断 ST、停牌、`trade_status`、`prices_limit`、涨跌停和可买 / 可卖状态。 | P0 | Given 执行 release readiness、研究重跑或 QMT admission 检查, When 对任一交易日计算可交易性, Then 必须输出停牌、ST、涨停、跌停、可买、可卖和缺口原因；缺失时不得声明真实可交易、容量可用或 QMT 可执行。 | UC-13, UC-14, CR-018 |
| REQ-128 | 数据 | CR-018 必须将 HS300、ZZ500、ZZ1000 和中证全指行情、历史成分和权重纳入真实 benchmark release scope，或明确 blocked claim。 | P0 | Given 生成 production release 或研究重跑报告, When benchmark coverage 检查运行, Then 四类 benchmark 的行情、成分和权重必须返回 available / pass，或输出 `required_missing` / `blocked_claims`；缺失时不得声明真实超额收益、指数增强或真实 tracking error。 | UC-13, UC-14, CR-018 |
| REQ-129 | 数据 | CR-018 必须保持 `prices_raw` 与 `adj_factor` 为事实源，并把 qfq、hfq、returns_adjusted 作为独立派生数据集 / 视图纳入 publish readiness。 | P0 | Given 生成复权派生 readiness, When 检查 lineage, Then qfq / hfq / returns_adjusted 必须记录 source_run_id、batch_id、input snapshot、as_of_trade_date、quality status 和派生策略；同一研究 run 混用多口径必须 fail fast。 | UC-12, UC-13, CR-018 |
| REQ-130 | 质量 | CR-018 必须建立 production quality gate，覆盖覆盖率、重复键、字段缺失、价格异常、收益尖峰、复权异常、停牌填充、future leakage、manifest lineage 和 current pointer 一致性。 | P0 | Given release readiness 检查运行, When 任一质量维度 fail, Then release status 必须为 blocked 或 failed，blocked_claims 包含字段级缺口、影响声明和解除条件；不得以人工说明替代机器可解析结果。 | UC-13, CR-018 |
| REQ-131 | 发布 | CR-018 必须通过 Explicit Publish Gate 更新 catalog current pointer，发布记录字段必须完整且可审计。 | P0 | Given 用户批准 publish, When gate 执行, Then 只有 publish gate 能写 current pointer；发布记录必须包含 `release_id`、dataset list、scope、source run ids、quality summary、blocked claims、rollback target、approver、approved_at 和 checksum；其他流程写 current pointer 必须失败。 | UC-13, CR-018 |
| REQ-132 | 回滚 | CR-018 必须支持 release 级 rollback，且 rollback 不得删除 candidate、raw、manifest 或历史 release 证据。 | P0 | Given 发布后质量异常或用户触发 rollback, When rollback 执行, Then current pointer 回到上一 release，rollback event 记录 reason、operator、time、from_release、to_release 和 smoke result；raw/manifest/candidate/history release 均保留。 | UC-13, CR-018 |
| REQ-133 | 研究 | CR-018 必须在 publish 后使用 published release 重跑阶段三到阶段五核心研究，再判断是否进入 QMT simulation。 | P0 | Given current pointer 已发布, When 生成 QMT admission 或策略 readiness, Then 必须先存在 release-bound research rerun report，记录 release_id、benchmark、PIT、tradability、adjustment_policy、blocked claims、旧 proxy/fixed-snapshot 对比和 pass/fail；缺失或 fail 时 QMT admission blocked。 | UC-14, CR-018 |
| REQ-134 | QMT 门控 | CR-018 必须把 QMT simulation、live_readonly、small_live 和 scale_up 全部后置到数据湖 publish + production research rerun PASS 之后。 | P0 | Given 用户请求任一 QMT 阶段, When 数据湖 publish 或 research rerun 未通过, Then stage gate 必须阻断且真实 QMT 操作计数为 0；通过后也只进入下一轮 QMT stage gate 审批，不自动授权真实发单、撤单或账户查询。 | UC-14, CR-018 |
| REQ-135 | 数据 | CR-018 可将行业、总市值、流通市值、beta 和风格因子列为 P1，但在其未通过前必须阻断行业中性、市值中性、纯 alpha 和风格归因声明。 | P1 | Given 行业 / 市值 / 风格数据缺失或 quality fail, When 研究报告或 QMT admission 生成, Then allowed_claims 不得包含行业中性、大小盘中性、风格归因完整或纯 alpha；如用户要求这些声明，则必须把对应数据升为 P0。 | UC-13, UC-14, CR-018 |
| REQ-136 | 数据 | CR-018 可将 ADV、turnover_rate、流动性、容量和冲击成本列为 P1，但在其未通过前必须阻断容量、资金放大和 scale_up 声明。 | P1 | Given 流动性 / 容量数据缺失或质量不通过, When 生成研究报告、QMT admission 或 scale_up gate, Then 只能输出探索性容量近似，不得声明可容量化交易、资金放大或 scale_up ready。 | UC-14, CR-018 |
| REQ-137 | 文档 | CR-018 必须刷新用户文档和 readiness summary，明确 candidate、published current truth、blocked claims、rollback、research rerun 和 QMT 后置边界。 | P0 | Given README、USER-MANUAL、TEST-STRATEGY 或 release summary 更新, When 搜索 `candidate=production`、`simulation ready`、`current truth complete` 等含混表达, Then 文档必须区分 candidate / validate PASS / published current truth，并列出 QMT 后置条件；含混表述必须修正或标记 blocked。 | UC-13, UC-14, CR-018 |
| REQ-138 | 优先级 | CR-019 必须将阶段六目标定义为重新制定 A 股多因子策略并达到可申请模拟盘状态，不得包装既有 production rerun fail 策略。 | P0 | Given 既有多因子或低波 production rerun 结论为 fail, When 生成阶段六 admission 或用户文档, Then 必须输出 blocked status、失败证据、解除条件和新多因子实验路径，不得标记为 simulation ready。 | UC-15, CR-019 |
| REQ-139 | 后置能力 | D1 决策必须把 Backtrader 保持为后置 optional execution backend，而非阶段六 P0 或默认主框架。 | P1 | Given HLD、Story Plan 或需求范围引用 Backtrader, When 检查 CR-019 scope, Then Backtrader 只能在 clean feed、候选策略和执行对照需求明确后进入后置 Story；不得替代轻量主路径或阻断日频多因子 admission。 | UC-18, CR-019 D1 |
| REQ-140 | 后置能力 | D2 决策必须把 Qlib 保持为后置 isolated runner，不得作为默认依赖、事实源或阶段六 P0。 | P1 | Given 设计文档或 Story 引入 Qlib, When 检查触发条件, Then 必须存在 isolated runner、输入导出合同、factor panel/report catalog 稳定证据和 no-default-provider 约束；否则只能记录为 Deferred Idea。 | UC-18, CR-019 D2 |
| REQ-141 | 后置能力 | D3 决策必须把分钟数据列为后置 Spike，不作为阶段六多因子模拟盘准入 P0。 | P2 | Given 用户请求分钟数据或分钟执行价, When 实验 58-59 尚未证明日频执行假设不足, Then 需求和 Story 不得把分钟数据列为 P0；只能输出触发条件、Spike 目标和 blocked claim。 | UC-18, CR-019 D3 |
| REQ-142 | 架构 | D4 决策必须禁止 QMT xtdata 进入 WSL 主路径，并把 Windows QMT bridge 作为最终 simulation 前的推荐架构。 | P0 | Given WSL 研究节点需要与 QMT 交互, When 设计数据或交易接入路径, Then WSL 不得直接导入 / 调用 xtquant；QMT adapter 和后续真实接口边界必须位于 Windows QMT 节点。 | UC-16, CR-019 D4 |
| REQ-143 | 后置能力 | D5 决策必须将 QMT Level2 保持为后置触发项，首轮不申请、不作为准入前置。 | P2 | Given 设计或文档提到 Level2、盘口、逐笔或委托队列, When 当前没有独立授权、数据审计和微观结构需求证据, Then 必须标记为 later-gated / deferred，不得声明 Level2 可用或 simulation 必需。 | UC-18, CR-019 D5 |
| REQ-144 | 运行治理 | D6 决策必须要求 shadow + 连续 5 个真实交易日 dry-run 后，才允许申请 QMT simulation。 | P0 | Given 用户请求 QMT simulation, When 缺少 shadow 证据或连续 5 个真实交易日 dry-run 安全记录, Then stage gate 必须返回 blocked，真实 QMT 操作计数为 0；Given 5 日 dry-run 通过, Then 仍只进入 per-run authorization 评审。 | UC-15, UC-17, CR-019 D6 |
| REQ-145 | 架构 | D7 决策必须把第一版 WSL / Windows 桥接主选设为 FastAPI 本地服务，并将 signed file drop 降为 fallback。 | P0 | Given HLD/ADR 选择桥接方案, When 检查 CR-019 决策, Then 主方案必须为 Windows QMT 节点 FastAPI local bridge；signed file drop 仅用于 FastAPI 不可达、鉴权失败或部署受限时的 dry-run / blocked fallback。 | UC-16, UC-17, CR-019 D7 |
| REQ-146 | API | FastAPI bridge 必须覆盖完整 QMT 功能接口类别，不得把“不做或少做鉴权”误解为“不支持 QMT 功能”。 | P0 | Given CP3 HLD 或 LLD 定义 gateway API, When 检查 endpoint matrix, Then 必须覆盖 health/capabilities、intent validate、dry-run、行情查询、账户 / 持仓 / 委托 / 成交查询、simulation submit/cancel、live-readonly、live submit/cancel、reconciliation、kill-switch 等完整 QMT 功能类别；未满足运行门控的真实操作返回 blocked，但接口类别不得缺失。 | UC-16, UC-17, CR-019 |
| REQ-147 | 运行门控 | FastAPI 服务存在、health pass、capabilities pass 或接口存在不得等同于真实 QMT 操作授权。 | P0 | Given FastAPI 服务可达且完整 QMT endpoint 可见, When 用户请求 simulation、live、cancel、account snapshot 或 reconciliation, Then 系统必须检查当前 run mode、CR016 stage gate、risk gate、kill switch 和必要授权上下文；缺任一项时返回 blocked，且对应真实 QMT 调用次数为 0。 | UC-17, CR-019 |
| REQ-148 | 鉴权 | FastAPI bridge 第一版可在受控局域网内不做应用层鉴权；若 CP3 判定需要鉴权，则采用最简 token / HMAC，不得因鉴权策略削减 QMT 功能接口。 | P0 | Given HLD 选择“无应用层鉴权”, When 评审安全边界, Then 必须同时冻结局域网 / 绑定 / 防火墙 / 日志脱敏 / run mode / stage gate；Given HLD 选择 token / HMAC, When 鉴权失败、过期或签名不匹配, Then 请求被拒绝且不触达 QMT adapter。 | UC-16, UC-17, CR-019 |
| REQ-149 | 部署 | FastAPI bridge 必须从回测框架主进程中摘离，交付为 Windows 系统可运行和可安装的 QMT gateway 命令。 | P0 | Given CP3 HLD 或后续 LLD 评审 FastAPI bridge, When 检查部署合同, Then 必须包含 Windows gateway 命令名称、安装方式、启动 / 停止方式、配置路径、bind host/port、Windows 防火墙、访问来源、heartbeat interval、owner、failure mode 和 fallback；local_backtest / WSL 侧只能通过 C 侧 client 的 HTTP API 调用链访问 S 侧 gateway，不得直接导入 xtquant。 | UC-16, CR-019 |
| REQ-150 | fallback | FastAPI fallback 不得自动绕过 gateway 改走真实 QMT；fallback 可选择 blocked-only 或 signed file drop dry-run / 人工处理。 | P0 | Given FastAPI 不可达、可选鉴权失败、heartbeat fail 或部署边界不满足, When 系统执行 fallback, Then 只能返回 blocked、生成 dry-run 文件 / ack / error 或进入人工处理；不得自动真实发单、撤单、账户查询或写 broker lake。 | UC-16, UC-17, CR-019 |
| REQ-151 | 安全 | FastAPI bridge、dry-run、fallback 和 admission 日志必须脱敏，禁止输出凭据、账户敏感信息和真实私有路径。 | P0 | Given 生成请求日志、错误日志、dry-run summary 或 admission package, When 内容包含 token、签名密钥、账户号、session、cookie、交易密码、`.env` 内容或真实私有路径, Then redaction gate 必须阻断或脱敏；报告只保留 env var 名称、脱敏账户标签、run_id 和 root label。 | UC-16, UC-17, CR-019 |
| REQ-152 | 安全 | CR-019 在 CP2 / CP3 / CP4 / CP5 前禁止真实操作；后续实现若进入 simulation / live 路径，必须只通过 Windows QMT gateway 转发并记录脱敏审计。 | P0 | Given 执行 CR-019 requirement-clarification、CP2 自动检查或设计阶段, When 检查安全声明和变更范围, Then `qmt_api_call=0`、`real_order=0`、`account_query=0`、`credential_read=0`、`provider_fetch=0`、`lake_write=0`、`reports_write=0`、`delivery_write=0`、`dependency_changes=0`；Given 后续 CP5/CP6/CP7 批准真实 QMT 功能实现, Then 所有真实调用必须经 gateway、run_id、stage、mode、结果和脱敏日志记录。 | UC-15, UC-16, UC-17, CR-019 |
| REQ-153 | 约束 | QMT 系统说明文档只能作为能力背景，不得推断当前项目已有真实账户、模拟盘、Level2 或交易权限。 | P0 | Given 文档引用 QMT 模拟运行、模型交易、文件交互或 Level2 能力, When 生成 HLD、需求、检查点或用户文档, Then 必须标记为 capability background；不得写成 current entitlement、可操作账户或已授权 endpoint。 | UC-16, UC-17, UC-18, CR-019 |
| REQ-154 | 准入 | 阶段六 admission package 必须覆盖实验 49-66 的数据、因子、策略、交易现实性、成本、benchmark、稳健性、消融、冻结、pre-sim 和 5 日 dry-run gate。 | P0 | Given 生成 simulation admission package, When 检查 gate matrix, Then 每个 gate 必须有 status、evidence、blocked reason、解除条件和关联实验；任一 P0 gate 未通过时 admission_status=blocked。 | UC-15, CR-019 |
| REQ-155 | 后置触发 | Backtrader 只有在 clean feed、候选策略稳定和执行对照需求明确后才可作为 W6 optional backend 启动。 | P1 | Given 用户请求 Backtrader 实现, When clean execution feed、candidate strategy、cost/tradability gate 或轻量主路径稳定性缺失, Then Story Plan 必须 blocked 或 deferred；不得新增默认依赖。 | UC-18, CR-019 |
| REQ-156 | 后置触发 | Qlib 只有在 factor panel、report catalog、PIT/available_at 和 isolated runner 输入输出契约稳定后才可作为 W7 启动。 | P1 | Given 用户请求 Qlib benchmark 或 ML workflow, When 缺少隔离 runner、export/import schema、factor lineage 或 no-provider-uri 约束, Then Qlib 只能作为 deferred idea；不得接管数据湖事实源或默认 provider。 | UC-18, CR-019 |
| REQ-157 | 后置触发 | 分钟数据只有在交易现实性实验显示日频执行假设不足时才进入 Spike，不阻断阶段六日频多因子准入。 | P2 | Given 实验 58-59 输出执行质量 / 成本 / 未成交问题, When 该问题成为 admission 主要风险且日频代理无法解释, Then 可创建分钟数据 Spike；否则保持 blocked / deferred，不影响 CP2/CP3 主线。 | UC-18, CR-019 |
| REQ-158 | 后置触发 | Level2 只有在订单簿深度、排队、冲击成本或微观结构成为主要风险且 L1 / 分钟 Spike 不足时，才可另起授权和数据审计。 | P2 | Given 用户请求 Level2 或 QMT 文档显示 Level2 能力, When 当前无独立权限、无微观结构风险证据或 L1/minute 尚未验证不足, Then Level2 保持 deferred；若触发，必须新建 CR、权限审批、数据审计和安全门控。 | UC-18, CR-019 |
| REQ-159 | 架构 | QMT 模块必须是独立 C/S 模块：C 侧位于 local_backtest，S 侧部署在 Windows QMT 节点。 | P0 | Given CP3 HLD 或 LLD 拆分 QMT 模块, When 检查模块边界, Then C 侧必须作为 local_backtest 内部模块向策略、OMS、运行治理和测试暴露统一调用接口，并通过 REST 调用 Windows S 侧；S 侧必须作为 Windows 可运行 / 可安装 gateway 接收 REST 请求，转换为 QMT / XtQuant 接口调用，并由 Windows QMT 客户端访问 QMT 服务端；C 侧不得直接导入或调用 xtquant。 | UC-16, UC-17, CR-019 |
| REQ-160 | 接口 | C 侧对 local_backtest 的默认推荐接口为 Python client / 函数调用，CLI 只作为薄包装用于人工 smoke、运维检查和脚本集成；若选择 CLI-first 必须由 CP3 另行说明理由。 | P0 | Given 策略、OMS、admission dry-run 或测试需要访问 QMT 能力, When 调用 C 侧接口, Then 应能通过类型化 Python 对象 / dataclass / dict 契约完成 health、capabilities、query、order intent、simulation/live 请求和 blocked result 处理；Given 用户需要人工检查或运维, Then CLI 可复用同一 client 并只负责参数解析、输出格式和退出码，不复制业务逻辑。 | UC-16, UC-17, CR-019 |
| REQ-161 | 范围 | CR-025 必须将目标归一为 production-grade research-to-execution 路线中的研究执行语义对照与接口对齐；Backtrader 仅作为显式选择的 optional execution realism / semantic reference，默认主路径仍为 lightweight engine。 | P0 | Given 用户未显式选择 Backtrader backend, When 运行研究、回测或默认测试入口, Then 系统必须使用 lightweight engine；Given 文档、HLD 或 Story 描述 Backtrader, Then 必须标记为 optional semantic reference，不得写成默认框架、生产 truth、阶段六 P0、QMT admission 前置或主路径迁移；Given 讨论生产级目标, Then 必须引用 research-to-execution 三条主线而不是框架级迁移。 | UC-19, CR-025 |
| REQ-162 | 依赖隔离 | CR-025 在 CP5 批准前不得新增 Backtrader 依赖；后续若实现，必须通过 optional extra 或等价隔离机制与 lazy import 保持默认环境可用。 | P0 | Given CP2/CP3/CP4/CP5 前的工作区, When 检查 `pyproject.toml`、`uv.lock` 和默认 import/test 路径, Then Backtrader 不得出现在默认依赖中；Given 用户显式选择 Backtrader 但未安装, Then 返回结构化 `backend_unavailable`，轻量主路径不失败。 | UC-19, CR-025 |
| REQ-163 | 数据契约 | Backtrader optional backend 只能消费本地 clean feed，且 clean feed 必须通过 PIT / `available_at`、单一复权口径、benchmark、calendar、tradability、cost、quality gate 和 schema 检查。 | P0 | Given Backtrader optional backend 接收到缺 PIT、缺 `available_at`、复权混用、benchmark 缺失、tradability 缺失或 quality fail 的输入, When backend 初始化或运行前校验, Then 必须返回 structured blocked / unavailable reason；不得生成 PIT、计算复权因子、联网补数或绕过 quality gate。 | UC-19, CR-025 |
| REQ-164 | 执行语义 | CR-025 必须定义 lightweight engine 与 Backtrader optional backend 的执行语义对照输出。 | P1 | Given 同一 clean feed、同一候选策略和同一成本配置, When 后续 CP5 批准实现并运行对照, Then semantic diff report 必须至少包含调仓日、目标权重 / 数量、成交价格、现金、手续费、滑点、税费、未成交 / 缺失处理、净值和差异原因；不得静默覆盖 lightweight 结果。 | UC-19, CR-025 |
| REQ-165 | 安全 | CR-025 不授权真实 broker、Backtrader live store、QMT / MiniQMT / XtQuant、provider fetch、lake write、broker lake write、catalog publish 或凭据读取。 | P0 | Given CR-025 CP2 intake、HLD、Story Plan、LLD 或后续验证, When 检查运行安全计数, Then `real_broker_calls=0`、`qmt_api_call=0`、`provider_fetch=0`、`lake_write=0`、`broker_lake_write=0`、`catalog_publish=0`、`credential_read=0`；任何非 0 都必须阻断并转独立 CR / 授权。 | UC-19, CR-025 |
| REQ-166 | 声明边界 | Backtrader optional backend 的输出只能标记为 research comparison，不得作为 production truth、默认研究 truth、simulation-ready 证据或 QMT admission pass。 | P0 | Given 生成 Backtrader 对照报告、用户文档、admission package 或研究摘要, When 检查声明文本和 metadata, Then 必须包含 optional backend、research comparison、lightweight baseline 和限制项；不得写成替代 lightweight 主路径、真实可交易证明或 QMT 准入通过。 | UC-19, CR-025 |
| REQ-167 | 回归 | CR-025 必须证明 lightweight 主路径、既有 benchmark resolver、数据读取和默认测试不受 Backtrader optional backend 影响。 | P0 | Given Backtrader 未安装或 optional backend disabled, When 运行默认 lightweight 回测、benchmark resolver、数据读取和相关最小回归, Then 不得出现 Backtrader import error、依赖缺失错误或默认结果漂移；若 optional backend 出错，必须 fallback 为 structured unavailable / blocked，不影响主路径。 | UC-19, CR-025 |
| REQ-168 | 门控 | CR-025 的实现、依赖变更、Story / LLD 批次和任何真实运行均必须等待后续 CP3 / CP4 / CP5 对应门控批准。 | P0 | Given 当前处于 CP2 前需求 / 场景输入阶段, When 检查变更范围, Then 只能修改过程文档、检查和交接；不得实现代码、改依赖、运行 Backtrader、触发 provider/lake/publish/QMT；Given CP5 未批准, Then Story 不得进入实现。 | UC-19, CR-025 |
| REQ-169 | 接口 | CR-025 的 CP3/HLD 必须定义研究输出到生产执行链路的接口边界：策略研究结果只能形成 target portfolio / order intent draft 或等价可审计对象，后续真实 broker 触达必须交给 QMT OMS / risk / adapter / stage gate。 | P0 | Given 后续 HLD/Story 设计 CR-025, When 研究报告、lightweight baseline 或 Backtrader semantic diff 输出可进入生产路线, Then 必须至少携带 strategy_id、run_id、signal_date、target_trade_date、symbol、target_weight 或 target_qty、research_adjustment_policy、execution_price_policy、cost_config_ref、data_lineage_ref 和 limitations；Given 缺少这些字段, Then 不得声明可进入 QMT OMS 或 simulation 申请。 | UC-19, CR-025 |
| REQ-170 | 路线治理 | CR tracking 必须显式展示三条主线：研究可信度、回测 / 模拟一致性、QMT 生产执行，并把 CR-025、CR-020..CR-024、CR-026..CR-028 映射到对应主线。 | P0 | Given 用户查询当前 CR 或推进建议, When 输出 CR tracking, Then 必须同时说明 CR-025 属于回测 / 模拟一致性主线并连接研究可信度和 QMT 生产执行；CR-020..CR-024 属于 QMT 生产执行主线；CR-026、CR-027、CR-028 属于后置研究 / 数据增强能力；不得只输出 Backtrader 单线。 | UC-19, CR-025 |
| REQ-171 | 优先级 | CR-025 CP2/CP3 应优先冻结 research-to-execution 范围、order intent 衔接和 semantic diff；真实 QMT gateway、simulation、live-readonly、small-live、scale-up 仍必须通过 CR-020..CR-024 独立启动和授权。 | P0 | Given 用户要求推进生产级框架, When 选择下一步 CR, Then 可在 CR-025 CP2/CP3 范围确认后启动 CR-020 gateway health 准入，但不得把 CR-025 approve 解释为服务启动、端口绑定、QMT 调用、simulation、live 或账户权限授权。 | UC-19, CR-025 |
| REQ-172 | 非目标 | CR-025 不得在 CP2/CP3 阶段复制、裁剪或直接移植 Backtrader 源码，也不得默认自研完整事件驱动交易框架；若 HLD 认为存在源码级移植候选，必须单列架构决策、许可证影响、维护成本、回归范围和 CP5 前置授权。 | P0 | Given HLD、LLD 或实现建议出现 Backtrader 源码移植、完整 Cerebro 类运行时、自研 live broker 或完整交易平台迁移, When 检查范围, Then 在没有 CP3 明确决策与 CP5 实现授权前必须标记为 out-of-scope；Given HLD 推荐任一源码级移植候选, Then 必须列出 GPLv3/copyleft 影响、替代方案、切换条件和是否需要另起 CR。 | UC-19, CR-025 |
| REQ-173 | HLD 输入 | CR-025 的 CP3/HLD 必须充分分析本地 Backtrader 项目 `/home/hyde/download/backtrader`，并记录哪些模块可借鉴、哪些可适配、哪些理论上可移植、哪些禁止进入本项目。 | P0 | Given meta-se 进入 CR-025 CP3/HLD, When 分析 Backtrader, Then HLD 必须至少覆盖 license、module inventory、Cerebro orchestration、broker/order/trade/position、feed/data line、commission/sizer、analyzer/observer、indicator、store/live broker、plot/writer 和 samples/tests；每类模块必须给出 recommendation=`reference_only|adapt_interface|migration_candidate|exclude`、理由、影响面、验证策略和是否需要 CP3/CP5 决策；不得只写“参考 Backtrader”而无模块级证据。 | UC-19, CR-025 |
| REQ-174 | 范围 | CR-030 必须采用项目自有多因子研究闭环主线，外部项目只作为静态参考或后续 Spike 候选。 | P0 | Given meta-se 进入 CR-030 CP3/HLD, When 选择推荐架构, Then 推荐方案必须以本项目既有数据湖、`research_input_v1`、实验 17-21、CR-011 factor audit、Stage6 admission gate 和 CR-025 order intent 边界为基线；Qlib、Alphalens、vectorbt、Zipline、LEAN、RQAlpha、vn.py、Backtrader 等不得成为默认 framework / truth / provider / runner。 | UC-20, CR-030 |
| REQ-175 | 架构 | CR-030 HLD 必须输出外部多因子项目借鉴矩阵，逐项说明可借鉴、可选 Spike、排除和禁止迁移。 | P0 | Given HLD 分析外部项目, When 输出 reference matrix, Then 至少覆盖 Qlib、Alphalens、vectorbt、PyBroker、bt、Zipline Reloaded、QuantConnect LEAN、RQAlpha、vn.py / vnpy.alpha、Backtrader 10 类候选；每项必须包含 license、依赖、数据入口、runner/provider/live 能力、recommendation、理由、影响面、验证策略、切换条件和 not-authorized 边界。 | UC-21, CR-030 |
| REQ-176 | 数据契约 | CR-030 必须定义 `FactorSpec` 和 `FactorRunSpec`，并映射到现有实验与外部项目对象，但不得直接采用外部对象作为内部 truth。 | P0 | Given 因子进入研究闭环, When 校验 `FactorSpec`, Then 必须包含 factor_id、name、version、direction、input_fields、window、params、preprocessing、universe、availability_policy、data_lineage、blocked_claims；Given 生成 `FactorRunSpec`, Then 必须包含 run_id、factor_id/version、date_range、dataset_release、benchmark、cost_config、seed、code_version、config_hash、output_root 和 failure_policy。 | UC-22, CR-030 |
| REQ-177 | 防泄漏 | CR-030 必须定义 `FactorPanelContract` 与 `LabelWindowSpec`，并用 fail-closed 校验阻断前视和标签泄漏。 | P0 | Given 因子面板或标签窗口缺少 `available_at`、`decision_time`、`label_window_start/end`、`label_available_at`、lineage、复权口径或 quality status, When 进入评价、组合或准入, Then 必须返回 structured blocked reason；Given `available_at > decision_time` 或 label overlap 风险存在, Then 评价和组合必须 fail-closed。 | UC-23, CR-030 |
| REQ-178 | 评价 | CR-030 必须定义 `FactorEvaluationReport`，覆盖单因子可靠性、分层、成本、暴露和声明边界。 | P0 | Given 单因子评价运行结果, When 输出报告, Then 至少包含 coverage、IC、RankIC、ICIR、quantile/layered returns、long-short returns、turnover、cost sensitivity、industry/market-cap/style exposure、annual/rolling/market-regime breakdown、pass/warn/fail/blocked status、allowed_claims、blocked_claims 和 evidence refs；不得用单一全样本指标声明生产有效。 | UC-24, CR-030 |
| REQ-179 | 组合 | CR-030 必须定义 `MultiFactorCombiner` 和 `MultiFactorPortfolioPlan` 的 HLD 合同，P0 采用可解释组合，optimizer 后置。 | P0 | Given 多因子进入组合, When HLD 输出 combiner 方案, Then 必须说明标准化、winsorization、中性化、正交化、权重策略、缺失值处理、约束、benchmark、成本、容量、调仓频率、冻结策略和 blocked reason；Given 需要 Qlib EnhancedIndexing、cvxpy 或外部 optimizer, Then 必须标记为后续 Spike，不进入 CR-030 P0 实现。 | UC-25, CR-030 |
| REQ-180 | 追踪 | CR-030 必须定义 `ExperimentManifest` 与 `ResearchReportCatalog`，确保研究 run 可复跑、可比较、可审计。 | P0 | Given 任一研究 run 生成报告或准入输入, When 写入 manifest/catalog, Then 必须记录 run_id、strategy_id、config_hash、dataset/release、factor_versions、label_window、benchmark、cost_config、evaluation_window、seed、code_version、report_paths、allowed_claims、blocked_claims、limitations 和 evidence refs；缺任一 P0 字段时不得进入 StrategyAdmissionPackage。 | UC-26, CR-030 |
| REQ-181 | 准入 | CR-030 必须定义 `StrategyAdmissionPackage`，把多因子研究结果映射到 Stage6 gate，但不构成 QMT 或 simulation/live 授权。 | P0 | Given 多因子候选策略请求准入, When 生成 package, Then 必须覆盖数据、因子、组合、回测、成本、benchmark、稳健性、消融、冻结、pre-sim、5 日 dry-run 前置状态、blocked reasons、解除条件和 `order_intent_draft_v1` 草稿字段；Given 任一 Stage6 P0 gate 未通过或无独立 QMT CR, Then admission_status=blocked，`qmt_api_call=0`、`real_order=0`、`account_query=0`。 | UC-27, CR-030 |
| REQ-182 | 安全 | CR-030 的 CP2/CP3/CP4/CP5 前不得实现、改依赖、运行外部项目、源码迁移、provider fetch、lake write、publish、QMT/simulation/live 或凭据读取。 | P0 | Given 当前处于 CR-030 requirement / HLD / Story Plan / LLD 门控前, When 检查工作区、命令记录或产物, Then `implementation_changes=0`、`dependency_changes=0`、`external_project_run=0`、`source_migration=0`、`provider_fetch=0`、`lake_write=0`、`catalog_publish=0`、`qmt_api_call=0`、`credential_read=0`；任何非 0 必须阻断并要求独立授权。 | UC-20, UC-21, UC-27, CR-030 |
| REQ-183 | 复用 | CR-030 必须复用并标准化现有 `research_dataset.py`、实验 17-21、CR-011 factor panel audit、label window gate 和 Stage6 admission gate，不得重建平行框架。 | P0 | Given HLD/Story 设计多因子闭环, When 识别文件和模块影响面, Then 必须列出现有基线的复用方式、缺口、兼容策略和迁移风险；若推荐新对象或新目录, Then 必须说明为什么现有对象不足、如何避免双 truth，以及回滚 / 兼容策略。 | UC-20, UC-22, UC-23, CR-030 |
| REQ-184 | 分流 | CR-026 Qlib isolated runner 必须保持后续 Spike candidate，直到 CR-030 合同冻结后再单独启动。 | P1 | Given 用户或 HLD 提到 Qlib qrun、provider_uri、model workflow、recorder 或 enhanced indexing, When 当前 CR-030 还未冻结 FactorSpec/Panel/Label/Report/Manifest 合同, Then CR-026 不得并行启动或并入 P0；HLD 必须给出重启条件、输入输出合同、依赖隔离和运行授权前置。 | UC-20, UC-21, CR-030 |
| REQ-185 | 文档与验证 | CR-030 的 HLD、后续 LLD 和测试策略必须解释 schema 来源、校验策略、外部项目边界、准入声明边界和不授权项。 | P0 | Given 生成 HLD/LLD/TEST-STRATEGY/README/USER-MANUAL, When 描述 CR-030, Then 必须包含 schema provenance、external project matrix、field dictionary、validation rules、failure policy、blocked claims、QMT not-authorized boundary、CR-026 disposition 和 fixture/test matrix；不得只写“参考 Qlib / Alphalens”而无可验证合同。 | UC-20 至 UC-27, CR-030 |
| REQ-186 | 范围 | CR-046 必须采用 framework-first 范围，只交付 QMT / MiniQMT 双目标策略交付框架、验证框架设计、MiniQMT runner 安装设计和策略包契约。 | P0 | Given CR-046 处于 CP2/CP3/CP5/CP6/CP7/CP8 任一阶段, When 检查正式产物和工作区 diff, Then 不得出现具体策略交付、真实 QMT 运行验证、MiniQMT 连接、submit/cancel、simulation/live 或凭据读取；若出现必须阻断并要求新 CR / runtime authorization。 | UC-28, CR-046 |
| REQ-187 | 策略核心合同 | 双目标框架必须定义可被 QMT terminal target 与 MiniQMT runner target 共同消费的策略核心合同。 | P0 | Given HLD/LLD 定义策略核心, When 审查字段, Then 至少包含 strategy_id、run_id、signal_date、target_trade_date、symbol、target_weight/target_qty、order_intent、risk_assumption、cost_assumption、data_lineage_ref、blocked_claims 和 evidence_ref；策略核心不得导入或直接调用 QMT / XtQuant / MiniQMT API。 | UC-28, UC-32, CR-046 |
| REQ-188 | QMT target | CR-046 必须定义 QMT 终端策略包形态，包括入口、配置、输入输出、日志、shadow 报告和人工导入说明。 | P0 | Given 后续 CR047 选择具体策略, When 生成 QMT terminal target, Then 必须能按 CR046 合同生成可审查的 `targets/qmt_terminal/` 结构、配置样例、导入步骤、shadow evidence 模板和 not-authorized 边界；当前 CR 不执行终端导入或运行。 | UC-29, CR-046 |
| REQ-189 | MiniQMT target | CR-046 必须定义 MiniQMT runner target 的安装设计和运行边界，但不得实现或执行真实 runner runtime。 | P0 | Given 用户当前没有 MiniQMT 权限, When 设计 MiniQMT target, Then 必须包含 Windows 目录规范、uv 管理、Python 版本、依赖隔离、配置、日志、启动/停止、kill switch、install dry-run、uninstall、upgrade 和 rollback；真实安装、连接、订阅行情、账户查询和 submit/cancel 均为 0。 | UC-30, CR-046 |
| REQ-190 | 验证框架 | CR-046 必须定义双目标验证框架，区分静态 fixture / schema 校验、QMT shadow 计划和 MiniQMT install dry-run 计划。 | P0 | Given 生成验证框架, When 审查测试矩阵, Then 必须包含策略包布局校验、核心合同 schema 校验、fixture 输入输出、QMT terminal shadow 证据模板、MiniQMT install dry-run 证据模板、安全计数和后续 runtime gate；不得把 fixture pass 声明为 simulation-ready。 | UC-31, CR-046 |
| REQ-191 | 后续分流 | CR-046 必须把首个具体策略交付、QMT 真实模拟盘验证、MiniQMT 实机验证、tick runner Spike 和研究框架完善拆为后续候选项。 | P0 | Given CP2/CP8 决策或 CR tracking 查询, When 列出 CR046 后续事项, Then CR047-candidate、CR048-candidate、CR049-candidate、CR050-candidate 和 CR051-candidate 必须有状态、阻塞前置、下一步和不授权边界，且不得提前创建正式 CR 文件。 | UC-28, UC-32, CR-046 |
| REQ-192 | 安全不授权 | CR-046 的任何 approval 都不得授权真实账户、凭据、连接、查询、下单、撤单、simulation/live、provider fetch、lake write 或 catalog publish。 | P0 | Given 用户回复 `approve` 或后续进入 CP3/CP5/CP8, When 解读授权范围, Then 只能解释为框架和验证设计通过；`credential_read`、`account_id_read`、`account_query`、`qmt_api_call`、`miniqmt_connection`、`order_submit`、`order_cancel`、`simulation_live`、`provider_fetch`、`lake_write`、`catalog_publish` 均必须保持 0。 | UC-28 至 UC-31, CR-046 |
| REQ-193 | QMT 权限事实 | HLD 必须区分当前 QMT 终端已可用与 MiniQMT 权限缺失两个事实，不得将二者混同。 | P0 | Given 架构设计或验证计划描述运行环境, When 提到 QMT / MiniQMT, Then 必须写明 QMT 终端可作为未来人工运行目标，MiniQMT 当前为未授权/未开通未来路线；任何 MiniQMT 实机验证必须等待 CR049 或等价授权。 | UC-29, UC-30, CR-046 |
| REQ-194 | 研究反向约束 | CR-046 必须输出研究框架后续需要满足的交付字段和证据要求，并登记为 CR051-candidate。 | P1 | Given CR046 框架冻结, When 准备后续研究框架完善, Then 必须能从 CR046 合同追溯到策略元数据、target portfolio、order intents、风险/成本假设、数据 lineage、blocked claims 和验证证据字段；当前 CR 不改造研究代码。 | UC-32, CR-046 |
| REQ-195 | 包结构 | CR-046 HLD/LLD 必须定义策略交付包顶层结构和目标目录职责。 | P0 | Given 设计策略包, When 检查结构, Then 必须至少包含 `strategy_core/`、`targets/qmt_terminal/`、`targets/miniqmt_runner/`、`validation/` 和 `docs/` 的职责、输入输出和 owner；任何目录不得含真实凭据或账户敏感信息。 | UC-28 至 UC-31, CR-046 |
| REQ-196 | 安装治理 | MiniQMT runner 安装设计必须遵循本项目 Python 依赖管理约束，优先使用 `uv` 并隔离 Windows runner 环境。 | P0 | Given 设计 install / upgrade / rollback, When 描述 Python 和依赖, Then 必须使用 `uv` 命令作为默认管理方式，禁止手工维护 `.venv` 或裸 `pip install` 作为默认路径；真实安装前必须先产出 dry-run manifest。 | UC-30, CR-046 |
| REQ-197 | 失败路径 | 双目标框架必须定义 QMT target、MiniQMT target 和验证框架的 fail-closed 行为。 | P0 | Given 缺配置、缺 schema 字段、MiniQMT 权限缺失、QMT 运行未授权或安全计数非 0, When 运行验证或审查, Then 必须输出 blocked / unavailable / not-authorized 状态和解除条件，不得降级为 silent pass。 | UC-28 至 UC-31, CR-046 |
| REQ-198 | 文档路径 | CR-046 本轮产品基线沿用当前仓库 `process/USE-CASES.md` / `process/REQUIREMENTS.md`；新增框架文档路径在 CP3/HLD 冻结。 | P1 | Given CR046 正文引用 `docs/product/*`, When CP2 产物生成, Then 必须说明当前仓库现有产品基线为 legacy `process/*`，不在 CP2 静默另建 `docs/product/` 双真相源；后续若迁移目录必须单独决策。 | UC-28, CR-046 |
| REQ-199 | 不替代 broker adapter | CR-046 双目标框架不得绕过 CR042 broker-neutral adapter 与 CR041 paper simulation 的既有合同。 | P0 | Given HLD/LLD 设计 adapter, When 处理 order intents、fills、positions、reconciliation, Then 必须说明如何复用或兼容 CR041/CR042 语义；不得让策略包直接成为真实 broker order 入口。 | UC-28, UC-31, CR-046 |
| REQ-200 | 门禁解释 | CR-046 CP2 approve 只表示需求 / 场景基线和六项推荐决策通过，不表示 CP3/CP5/CP6/CP7/CP8 自动通过。 | P0 | Given 用户在 CP2 回复 approve, When 更新状态或继续推进, Then 只能进入 CP3 HLD 准备；不得跳过架构、Story、LLD、实现、验证或终验门禁。 | UC-28 至 UC-32, CR-046 |

## 需求级变更记录

| 版本 | 操作 | 涉及需求 | 原因 / 来源 | 处理说明 |
|----|------|---------|-----------|---------|
| 1.0 | 初始化 | REQ-001 - REQ-020 | 用户 `/init` 原始输入 | 首次创建需求文档，状态为 draft，等待用户确认 |
| 1.1 | 修订 | REQ-001, REQ-003, REQ-005, REQ-008, REQ-009, REQ-011, REQ-012, REQ-016, REQ-018, REQ-020 | Review Round 1 blocking/required | 修正工程根、参数名、离线边界、成本口径、聚宽边界和报告输出 |
| 1.1 | 新增 | REQ-021 - REQ-036 | Review Round 1 blocking/required | 补齐数据契约、接口边界、净值完整性、扫描失败策略、候选清单、偏差披露、过拟合警示和可视化边界 |
| 1.2 | 修订 | REQ-003, REQ-005, REQ-006, REQ-008, REQ-015, REQ-023, REQ-031 | 2026-05-14 需求刷新分派 | 强化非 PIT 股票池、T 日收盘后信号/T+1 成交、历史窗口剔除、缺失价/无成交处理和报告限制项 |
| 1.2 | 新增 | REQ-037 - REQ-046 | 2026-05-14 需求刷新分派 | 新增复权一致、`available_at` 校验、metadata 限制项和真实性增强优先级 |
| 1.3 | 修订 | REQ-016, REQ-034 | 2026-05-14 数据源限速刷新分派 | 强化数据准备与回测主路径物理隔离、断网可运行、manifest/质量报告读取和数据新鲜度披露 |
| 1.3 | 新增 | REQ-047 - REQ-058 | 2026-05-14 数据源限速刷新分派 | 新增数据源限速、请求节流、节流可验证、有限重试退避、断点续传、raw 缓存、增量更新、最近 N 个交易日回补、manifest、质量报告、失败降级和真实性增强数据链路契约 |
| 1.4 | 新增 | REQ-059 - REQ-070 | CR-005 第三轮 hs300 / Tushare 评审阻断项 | 新增 Tushare 显式写湖、`hs300_index` 本地 benchmark、typed unavailable/required_missing、next action、数据准确性/可用性、consumer no-network/no-connector 和 Backtrader optional backend 正式需求；旧 REQ 编号不重排 |
| 1.5 | 新增 | REQ-071 - REQ-082 | CR-011 因子研究生产级数据补齐 | 新增真实 benchmark、PIT 股票池、可交易性、执行价、复权/公司行动、行业市值风格、流动性容量成本、因子审计面板、稳健性验证、报告声明门控、凭据边界和旧报告隔离需求；旧 REQ 编号不重排 |
| 1.6 | 新增 | REQ-083 - REQ-087 | CR-013 unsupported data 与 claim boundary | 新增 2020-2024 full-history 不得外推、真实 VWAP / 分钟执行价 blocked、unsupported register 用户文档和报告声明边界、provider/lake/credential/old data 权限未授权、旧证据报告保留需求；旧 REQ 编号不重排 |
| 1.7 | 新增 | REQ-088 - REQ-097 | CR-014 A 股 since-inception production data lake | 新增全 A 自存在 / 上市日起至当前交易日 current truth、证券生命周期 / 退市 / 代码变更、P0 dataset 分层、catalog current pointer、增量刷新 / replay、DuckDB 只读查询审计候选、权限与凭据边界、claim boundary、验证矩阵和当前交易日口径需求；旧 REQ 编号不重排，待 CP2 用户确认 |
| 1.8 | 新增 | REQ-098 - REQ-122 | CR-015 / CR-016 / CR-017 QMT foundation、QMT activation 与 adjustment dual-view | 新增 raw/qfq/hfq/returns_adjusted、qfq as-of、研究口径与 raw 执行价隔离、QMT adapter / OMS / broker lake / pre-trade hard block、shadow / dry-run / mock 默认、runbook、对账、kill switch、per-run 授权、资金放大 gate 和验证矩阵需求；旧 REQ 编号不重排，CP2 intake 已 approved |
| 1.9 | 新增 | REQ-123 - REQ-137 | CR-018 production data lake closure | 新增 production current truth 完成定义、CR014 S14 candidate 与 current truth 隔离、PIT/W3/benchmark/复权派生、quality/readiness、Explicit Publish Gate、rollback、发布后研究重跑、QMT 后置门控、P1 行业市值流动性声明边界和文档刷新需求；旧 REQ 编号不重排，D1-D6 已获用户批准 |
| 1.10 | 新增 | REQ-138 - REQ-158 | CR-019 stage6 multifactor simulation architecture | 新增阶段六多因子模拟盘准入、D1-D7、FastAPI 本地服务桥接、安全鉴权、WSL/Windows 部署、stage gate、per-run authorization、fallback、日志脱敏、禁止真实操作默认值和 Backtrader/Qlib/minute/Level2 后置触发条件；旧 REQ 编号不重排，D1-D7 已获用户批准 |
| 1.11 | 新增 | REQ-159 - REQ-160 | CR-019 user correction：QMT C/S module and C-side interface | 新增 QMT 独立 C/S 模块边界、C 侧 local_backtest 统一 Python client / 函数接口推荐、薄 CLI wrapper 备选；Q40 已按用户确认采用多基准 + primary benchmark 方案 |
| 1.12 | 新增 | REQ-161 - REQ-168 | CR-025 Backtrader optional execution backend hardening | 新增 optional backend 范围、默认 lightweight 主路径、依赖隔离、clean feed、semantic diff report、无真实 broker/QMT/provider/lake/publish、结果声明边界、轻量主路径回归和 CP5 前不得实现；旧 REQ 编号不重排，待 CP2 人工确认 |
| 1.13 | 修订 / 新增 | REQ-161, REQ-169 - REQ-172 | CR-025 CP2 用户修改意见：生产级 research-to-execution platform route | 修订 CR-025 范围为研究执行语义对照与接口对齐；新增 target portfolio / order intent 衔接、三条主线 tracking、推进优先级和禁止框架级源码移植 / 完整交易框架自研；旧 REQ 编号不重排，待 CP2 人工确认 |
| 1.14 | 修订 / 新增 | REQ-172, REQ-173 | CR-025 CP2 用户批准与 Backtrader 本地项目分析要求 | CP2 approved；新增 CP3/HLD 必须分析 `/home/hyde/download/backtrader` 的模块级借鉴 / 适配 / 移植候选 / 禁止移植对比；源码级移植仍需 CP3 决策与 CP5 授权 |
| 1.15 | 新增 | REQ-174 - REQ-185 | CR-030 CP2 用户授权进入 HLD：多因子研究框架借鉴与研究闭环标准化 | 新增项目自有多因子闭环、外部项目借鉴矩阵、FactorSpec / FactorRunSpec、FactorPanelContract / LabelWindowSpec、FactorEvaluationReport、MultiFactorCombiner、ExperimentManifest / ResearchReportCatalog、StrategyAdmissionPackage、CR-026 分流、安全不授权、现有能力复用和文档 / 验证要求；旧 REQ 编号不重排，进入 CP3/HLD |
| 1.16 | 新增 | REQ-186 - REQ-200 | CR-046 QMT / MiniQMT 双目标策略交付框架 | 新增 framework-first 范围、策略核心合同、QMT terminal target、MiniQMT runner 安装设计、验证框架、后续分流、安全不授权、研究反向约束、包结构、安装治理、失败路径和门禁解释；旧 REQ 编号不重排，待 CP2 人工确认 |

## 风险与假设

| ID | 类型 | 内容 | 关联需求 | 缓解措施 / 验证方式 |
|----|------|------|---------|-------------------|
| RA-001 | 风险 | AKShare 免费接口可能变更、限频或字段不稳定。 | REQ-016, REQ-034, REQ-047 - REQ-057 | 数据拉取与本地回测解耦；回测只依赖 parquet 契约；数据准备流程必须节流、有限重试、断点续传、raw 缓存、manifest 记录和质量报告披露。 |
| RA-002 | 假设 | 第一版使用固定当前沪深 300 成分股快照，接受幸存者偏差。 | REQ-003, REQ-031 | 在报告中显式标注快照日期、股票池数量和幸存者偏差，不把结果解释为严肃实盘级证据。 |
| RA-003 | 风险 | 不处理停牌、涨跌停和成交量约束会导致本地结果与聚宽存在差异。 | REQ-015, REQ-030 | 聚宽只用于少量候选的真实性校验；差异分析必须解释约束缺失影响。 |
| RA-004 | 假设 | 回测资金默认全仓等权，因缺失价格无法持有的目标权重留作现金。 | REQ-008, REQ-024 | 在 HLD/LLD 中明确现金处理、日收益归属和成本扣除顺序。 |
| RA-005 | 风险 | 参数扫描可能产生样本内过拟合。 | REQ-011, REQ-032 | 第一版报告必须提示样本内选择风险；样本外拆分列入后续里程碑。 |
| RA-006 | 假设 | 第一版不要求本地和聚宽逐日净值一致。 | REQ-030 | 使用方向一致口径验收：排序方向、收益/回撤量级、换手特征和差异解释。 |
| RA-007 | 风险 | 默认复权口径尚未确认，若本地与聚宽或不同数据文件复权口径不一致，会导致动量排名和收益指标不可比。 | REQ-037 | HLD 前必须确认默认复权口径；实现层必须拒绝混用并在报告 metadata 中记录实际口径。 |
| RA-008 | 风险 | 若缺少字段级 `available_at` 或可审计推导规则，未来函数可能进入信号、股票池或事件过滤。 | REQ-038, REQ-045 | HLD 前确认未来函数校验层级；第一版只允许明确可用时点的数据进入决策。 |
| RA-009 | 风险 | 第一版不精确建模完整停牌、涨跌停、新股、退市、ST、财报披露日和历史成分变化，可能高估可交易性和收益稳定性。 | REQ-015, REQ-041 - REQ-046 | 报告 metadata 强制警示；后续按 PIT universe provider、交易状态表、涨跌停约束、事件 `available_at`、偏差审计报告顺序增强。 |
| RA-010 | 风险 | AKShare 等免费数据源可能限速、字段变更、临时不可用或返回迟到修正数据，影响本地缓存新鲜度与完整性。 | REQ-047 - REQ-057 | 独立数据准备流程必须节流、有限重试、断点续传、raw 缓存、manifest 记录和质量报告披露；本地 parquet 合规时回测主路径降级为离线运行。 |
| RA-011 | 假设 | 第一版默认允许数据准备联网，但回测、扫描、候选筛选和差异分析主路径必须离线。 | REQ-016, REQ-034, REQ-057 | HLD 必须把数据准备入口与回测入口物理隔离，并用测试或日志证明回测主路径无网络请求。 |
| RA-012 | 风险 | 若 raw 缓存保留策略、manifest schema 或质量阈值不明确，后续难以复现 parquet 派生和解释数据失败。 | REQ-052, REQ-055, REQ-056 | HLD 前确认 raw 缓存保留策略、manifest schema、质量报告阈值和数据新鲜度披露规则。 |
| RA-013 | 风险 | `hs300_index` 的价格指数 / 全收益指数 / 其他口径尚未确认，可能导致 benchmark 相对收益不可比较。 | REQ-061, REQ-063 | CP5 前由 meta-se / 用户确认 `benchmark_kind`；未确认前 resolver 只能返回 `required_missing` / `unavailable`，不得声明 fully available。 |
| RA-014 | 风险 | 消费层若自动调用 Tushare 或读取 token，会破坏离线主路径与凭据边界。 | REQ-059, REQ-064, REQ-069 | 静态导入扫描、网络调用计数、凭据扫描和断网测试必须覆盖 Data Loader、实验入口、benchmark resolver 与 Backtrader。 |
| RA-015 | 风险 | `required_missing` 只有错误文本而无补齐作业规格，会让用户无法完成数据准备闭环。 | REQ-060, REQ-062, REQ-063 | typed result 必须包含 `next_action` 与 `remediation_job_spec`，并指向 `market_data` 写湖 / 数据准备层而非消费调用栈。 |
| RA-016 | 风险 | CR-011 若只补真实 benchmark 而未补 PIT、可交易性和执行价，可能把旧探索结论误升级为生产级结论。 | REQ-071 - REQ-074, REQ-080 | `production_strict_research` gate 必须同时检查 benchmark、PIT、tradability 和 execution feed；任一缺失必须进入 `blocked_claims`。 |
| RA-017 | 风险 | 行业、市值、风格和容量数据缺失时，中性化 IC、容量可交易和纯 alpha 声明会被高估或误读。 | REQ-076, REQ-077, REQ-080 | 只有辅助数据 coverage 与 `available_at` 通过时才允许输出对应声明；缺失时仅保留原始因子表现或探索性结果。 |
| RA-018 | 风险 | 因子面板只保存 zscore 而不保存 raw / directional / winsorized，会导致后续无法审计方向统一、去极值和标准化过程。 | REQ-078 | factor audit panel 必须保留四层取值、预处理参数、过滤原因和 lineage；缺层级时标记 `factor_audit_incomplete`。 |
| RA-019 | 风险 | 单一区间单一参数回测可能掩盖市场状态、年度和成本变化下的不稳定性。 | REQ-079 | 新版报告必须输出 rolling、annual、market_state、parameter_grid、cost_grid 五类验证表，并为每个切片记录 status 与 warning_reason。 |
| RA-020 | 风险 | CR-010 limited window 数据湖事实可能不足以覆盖实验 17-21 旧样本区间，导致生产级验证窗口小于旧报告窗口。 | REQ-071, REQ-072, REQ-080, REQ-082 | 报告必须记录实际 coverage_start / coverage_end、missing reason 和 baseline_report_path；不得把 limited window 结论外推到旧报告全区间。 |
| RA-021 | 风险 | 真实数据授权和凭据边界若在实现阶段被放宽，可能泄露 token、`.env`、真实私有路径或误写真实 lake。 | REQ-081 | 默认 network/write/credential counters 为 0；真实执行必须显式授权、source enabled、allowlist 命中，并在报告中只保留脱敏 metadata。 |
| RA-022 | 风险 | CR-012 limited-window pass 被误读为 2020-2024 或全历史生产级可用，导致用户基于未覆盖窗口做实盘级结论。 | REQ-083, REQ-087 | 报告和用户文档必须显式输出 supported_window / blocked_window、10 个 dataset 的 `limited_window_only` 状态和 evidence_paths；解除 blocked 只能通过新补数与新审计。 |
| RA-023 | 风险 | close proxy、`amount/volume` 或日频成交额被误包装为真实 VWAP、分钟执行价或真实撮合执行。 | REQ-084 | execution audit 必须将 `real_vwap_execution` / `vwap_fill_claim` 写入 blocked_claims；真实 VWAP 只有在 `vwap` 与 `vwap_status=available` 且审计通过后才能解除。 |
| RA-024 | 风险 | unsupported register 未进入用户文档和报告，导致 research-only / unsupported 数据被当作 production dataset 使用。 | REQ-085 | 文档和报告 schema 强制消费 `unsupported_data_register.csv` 的 status、reason 和 pass_denominator；`excluded` 项不得进入 pass 分母。 |
| RA-025 | 风险 | CR-013 后续补数诉求可能被误解为当前已授权 provider fetch、真实 lake 写入、凭据读取或旧数据读取。 | REQ-086, REQ-087 | 默认计数必须为 0，任何真实 provider/lake/credential/old data 操作必须通过单独 Story / CP5 与用户显式授权；旧证据报告只读保留。 |
| RA-026 | 风险 | “全 A since-inception”若未冻结 universe、交易所 / 板块边界和当前交易日口径，HLD 可能对 coverage denominator 使用不同解释。 | REQ-088, REQ-097 | CP2 必须确认覆盖边界和 current trading day policy；未确认时只能标记 `required_missing`，不得声明 up-to-date production current truth。 |
| RA-027 | 风险 | 证券生命周期、退市和代码变更缺失会导致历史样本幸存者偏差或重复计数。 | REQ-089 | lifecycle dataset 必须输出 effective_date、available_at、list_status、delist/code-change mapping 和 blocked reason；缺失时阻断 PIT current truth。 |
| RA-028 | 风险 | validate pass 被误当成 current truth，可能使未发布候选数据污染 reader、审计或特征抽取。 | REQ-090, REQ-091 | 保留显式 publish gate；current pointer 必须记录 published_at、latest_manifest_run_id、lineage checksum 和 quality/readiness。 |
| RA-029 | 风险 | 增量刷新或 replay 若重复写入、触发 provider 或改写 current pointer，会破坏可恢复性和审计链。 | REQ-092 | manifest idempotency、skip/retry/resume_conflict、replay no-provider/no-credential/no-current-pointer-change 必须进入测试场景。 |
| RA-030 | 风险 | DuckDB 候选能力可能被误解为已批准依赖或事实源替代方案。 | REQ-093 | 需求阶段只记录 read-only query/audit/feature extraction 候选；依赖修改和 `.duckdb` 持久化必须由 HLD/CP3/CP5 单独批准。 |
| RA-031 | 风险 | 真实执行授权边界若不清，可能触发 provider fetch、读取凭据、写真实 lake、读取旧 `data/**` 或覆盖旧 reports。 | REQ-094, REQ-095 | 权限计数必须覆盖 provider/lake/credential/legacy data/old report/dependency；任何真实操作必须单独 Story、CP5 和用户显式授权。 |
| RA-032 | 风险 | qfq/hfq 复权价若误入 QMT 委托、成交或对账，会造成真实价格错误和资金风险。 | REQ-102, REQ-109, REQ-120 | order intent 必须记录 `execution_price_policy=raw`；pre-trade 和 validation 对 qfq/hfq 执行价 hard block；TS-017-03 覆盖该风险。 |
| RA-033 | 风险 | qfq 未记录 `as_of_trade_date` 时，未来复权因子变化会导致历史价格漂移不可解释。 | REQ-100, REQ-103 | qfq 物化必须保存 as-of、input snapshot 和 lineage；旧 qfq 基线保留，迁移不得覆盖。 |
| RA-034 | 风险 | qfq/hfq 公式、provider 字段方向和 `adj_factor` 语义若在 CP3 未冻结，后续实现可能把复权方向写反或污染数据湖。 | REQ-098, REQ-099, REQ-122 | CP3 HLD / ADR 必须冻结公式、字段解释、schema 和 quality gate；CP5 前不得实现真实写湖或迁移。 |
| RA-035 | 风险 | 策略层直接调用 QMT API 会绕过 OMS、pre-trade risk、状态机和审计。 | REQ-105, REQ-106, REQ-109 | 静态导入扫描和调用审计必须验证策略层无 QMT API 直连；adapter 是唯一 broker 触达点。 |
| RA-036 | 风险 | broker lake、QMT 账户信息或凭据若写入仓库、日志或报告，会造成敏感信息泄露。 | REQ-108, REQ-111, REQ-114 | broker lake 必须外置；日志和报告只保留脱敏标签、环境变量名和 run_id；默认 credential_reads=0。 |
| RA-037 | 风险 | OMS 状态机若不处理 partial fill、unknown 或 timeout，可能把未确认订单误判为成功并引发重复下单。 | REQ-107, REQ-116 | 状态机必须覆盖异常状态并进入 manual_review / retry；对账报告校验本地状态与 broker 事实差异。 |
| RA-038 | 风险 | pre-trade risk 如果只是 warn 而非 hard block，风控失败仍可能触达真实 broker API。 | REQ-109, REQ-110 | 风控失败时 adapter 调用次数必须为 0；warn-only 不满足验收。 |
| RA-039 | 风险 | CR-016 阶段推进过快或跳过实盘只读 / 小资金隔离，会把未验证链路直接暴露给真实资金。 | REQ-112, REQ-113, REQ-114, REQ-119 | 阶段 gate 不可跳过；runbook、per-run 授权、对账和稳定性证据是下一阶段前置条件。 |
| RA-040 | 风险 | 缺少 kill switch、对账或手工接管路径时，运行异常可能持续提交新单或无法恢复。 | REQ-116, REQ-117 | kill switch 必须停止新单、撤可撤单、冻结策略并记录接管；对账差异超阈值进入 blocked / manual_review。 |
| RA-041 | 假设 | CR-017 不阻断 CR-016 技术链路模拟盘，但在复权治理实现验证前阻断生产策略复权治理声明和资金放大。 | REQ-118, REQ-119, REQ-120 | 阶段 gate 将技术链路验证与生产策略声明分离；资金放大必须检查 CR-017 实现验证和研究成熟度 gate。 |
| RA-042 | 风险 | `prices` / `adj_factor` candidate 覆盖完整后被误读为 production current truth，可能绕过 PIT/W3/benchmark/quality/publish gate。 | REQ-123, REQ-125, REQ-131, REQ-137 | readiness summary、reader smoke 和文档必须区分 candidate / validate PASS / published current truth；current pointer 未发布时生产 reader blocked。 |
| RA-043 | 风险 | PIT universe、lifecycle、ST、停牌、涨跌停或 trade_status 缺失会使低波和可交易性结论继续带幸存者偏差或假成交。 | REQ-126, REQ-127, REQ-133 | P0 gate 不通过时阻断 production current truth、真实可交易、QMT admission 和严肃超额收益声明。 |
| RA-044 | 风险 | benchmark 行情、历史成分或权重缺失会导致“跑赢沪深300”“指数增强”“真实 tracking error”声明失真。 | REQ-128, REQ-133 | HS300 / ZZ500 / ZZ1000 / 中证全指作为默认 P0 benchmark group；缺失时 blocked_claims 必须禁止真实超额和指数增强声明。 |
| RA-045 | 风险 | publish 粒度过细或多入口更新 current pointer 会增加一致性、回滚和审计复杂度。 | REQ-131, REQ-132 | 采用 release-level 总门 + dataset-level 明细；只有 Explicit Publish Gate 可以更新 current pointer，rollback 以 release 为单位。 |
| RA-046 | 风险 | 行业、市值、风格、流动性和容量若作为 P1 延后，研究可能暂时无法证明纯 alpha、中性化和资金放大可行。 | REQ-135, REQ-136 | P1 不阻断 production current truth 核心发布，但阻断行业 / 市值中性、容量、scale_up 和纯 alpha 声明；用户要求声明时升为 P0。 |
| RA-047 | 假设 | 用户已批准 D1-D6 推荐方案：数据湖优先、CR018 承接、candidate 不直发、真实抓取窗口化、QMT 后置、publish 后研究重跑。 | REQ-123 - REQ-137 | CP2 人工结果记录用户批准文本；后续 HLD/Story/LLD 以该决策为输入，真实执行和 publish 仍需 CP5 / per-run 授权。 |
| RA-048 | 风险 | FastAPI 服务存在、health pass 或 dry-run pass 被误读为 QMT simulation 授权。 | REQ-146, REQ-147, REQ-148, REQ-152 | simulation endpoint 必须 later-gated；capability 与 authorization 分离；缺 stage gate 或 per-run authorization 时真实 QMT 调用计数为 0。 |
| RA-049 | 风险 | FastAPI 鉴权或日志脱敏设计不足会泄露 token、账户信息、签名密钥、`.env` 内容或真实私有路径；若选择无应用层鉴权，绑定和防火墙边界不清也会造成误暴露。 | REQ-148, REQ-151 | CP3 必须冻结“无应用层鉴权”或“最简 token/HMAC”的适用条件、失败行为和 redaction gate；默认日志只保留脱敏标签。 |
| RA-050 | 风险 | WSL / Windows bridge 绑定地址、防火墙或访问来源不清，可能把服务暴露到公网或不受控局域网。 | REQ-149 | HLD/LLD 必须定义 bind host/port、防火墙、allowlist 和 heartbeat；公网默认暴露 fail。 |
| RA-051 | 风险 | signed file drop fallback 若边界不清，可能在 FastAPI 失败时自动绕到真实 QMT。 | REQ-145, REQ-150, REQ-152 | fallback 只能 dry-run 文件交换或 blocked；真实发单、撤单、账户查询计数必须为 0。 |
| RA-052 | 风险 | QMT 系统说明文档被过度解释为当前项目已有真实账户、模拟盘、Level2 或交易权限。 | REQ-153 | 所有引用均标记为能力背景；真实权限、endpoint 和账户操作必须通过独立授权与 stage gate。 |
| RA-053 | 风险 | 阶段六目标若只包装旧失败策略，会误导用户认为已满足多因子模拟盘准入。 | REQ-138, REQ-154 | admission package 必须记录旧失败证据、实验 49-66 gate、blocked_claims 和解除条件。 |
| RA-054 | 风险 | Backtrader、Qlib、分钟数据或 Level2 范围膨胀，会把阶段六 P0 从日频多因子准入转向框架迁移或高频数据工程。 | REQ-139 - REQ-143, REQ-155 - REQ-158 | 四类能力均以后置触发条件和 Deferred Ideas 管理；未触发前不得新增依赖或阻断 P0。 |
| RA-055 | 风险 | D6 的 shadow + 5 日 dry-run 被跳过，会使未验证策略直接申请 simulation。 | REQ-144, REQ-147, REQ-154 | stage gate 必须检查连续 5 个真实交易日 dry-run 安全证据；通过后仍只进入 per-run authorization。 |
| RA-056 | 风险 | C 侧接口若采用 CLI-first，local_backtest 内部策略、OMS 和测试会被迫通过进程调用和文本解析访问 QMT，增加序列化、错误处理和 mock 成本。 | REQ-159, REQ-160 | 推荐 Python client / 函数调用作为主接口，CLI 仅作为薄包装复用同一 client；若 CP3 选择 CLI-first，必须补充进程调用、退出码、结构化输出和测试隔离设计。 |
| RA-057 | 风险 | Backtrader 被误写为默认主路径或主框架，会扩大回归面并削弱 lightweight engine 的透明可调试优势，也会偏离用户的 production-grade research-to-execution 目标。 | REQ-161, REQ-166, REQ-167 | 默认入口和文档声明必须保留 lightweight engine；Backtrader 只作为显式选择的 optional execution realism / semantic reference。 |
| RA-058 | 风险 | Backtrader 依赖泄漏到默认安装或默认测试路径，会导致未安装环境失败并违反 CP5 前不得改依赖的门控。 | REQ-162, REQ-167, REQ-168 | CP5 前依赖文件不变；后续实现采用 optional extra / lazy import；未安装时返回 `backend_unavailable`。 |
| RA-059 | 风险 | clean feed gate 不完整时，Backtrader 可能绕过 PIT、`available_at`、复权、benchmark、tradability 或 quality 边界。 | REQ-163, REQ-164 | optional backend 运行前必须校验 clean feed；不合规时 structured blocked，不生成或补齐事实数据。 |
| RA-060 | 风险 | lightweight 与 Backtrader 的成交、现金、成本、滑点和净值语义差异若不显式报告，用户可能把差异误读为策略收益改善或引擎错误。 | REQ-164, REQ-166 | semantic diff report 必须解释差异原因，Backtrader 输出只能作为 research comparison。 |
| RA-061 | 风险 | Backtrader live broker / store 或真实 broker 接入被误纳入 CR-025，会把研究后端扩展为真实运行授权。 | REQ-165, REQ-168 | 明确真实 broker、QMT、provider、lake、publish、credential 计数为 0；真实 broker 需独立 CR 和授权。 |
| RA-062 | 风险 | Backtrader 对照结果被写入 QMT admission、production truth 或用户文档时，可能绕过阶段六 admission package、5 日 dry-run 和 QMT stage gate。 | REQ-166, REQ-168 | 报告 metadata 和文档必须标注 optional research comparison；不得作为 simulation-ready 或 production-truth 证据。 |
| RA-063 | 风险 | 若 CR tracking 仍只按 Backtrader / Qlib 后置能力展示，会掩盖用户真正目标中的研究可信度、回测 / 模拟一致性和 QMT 生产执行三条主线。 | REQ-170, REQ-171 | follow-up tracking、CR-INDEX 和 STATE tracking 必须补充三条主线视图；推进建议必须区分研究语义对照、gateway health 和真实交易授权。 |
| RA-064 | 风险 | 研究输出缺少 target portfolio / order intent 衔接字段时，即使回测或 Backtrader 对照可运行，也无法安全进入 QMT OMS、simulation 或 stage gate。 | REQ-169, REQ-171 | CP3 必须冻结 research output -> order intent draft 合同；缺字段时不得声明 simulation-ready 或 QMT admission pass。 |
| RA-065 | 风险 | 复制 / 移植 Backtrader 源码或自研完整事件驱动框架会把 CR-025 从生产链路收敛误扩展为框架工程，带来许可证、维护和回归风险。 | REQ-172 | CP3/HLD 可评估模块级候选，但 CP5 前不得实施源码级移植；任何移植推荐必须进入架构决策和授权门控。 |
| RA-066 | 风险 | Backtrader 本地项目采用 GPLv3 许可证；若 HLD 推荐源码级移植但未显式处理 copyleft、分发、修改标记和源码开放义务，可能造成许可证合规风险。 | REQ-172, REQ-173 | HLD 必须把 license 作为模块对比表的硬列；默认优先借鉴设计和接口适配，源码级移植需单独风险接受或另起 CR。 |

## 里程碑建议

| 里程碑 | 包含需求 | 交付物 | 前置里程碑 |
|--------|---------|--------|-----------|
| M0 - 数据准备与缓存可追溯 | REQ-016, REQ-021, REQ-022, REQ-034, REQ-047 - REQ-057 | 独立数据准备/更新入口、请求节流、有限重试退避、断点续传、raw 缓存、标准化 parquet 派生、manifest/checkpoint、质量报告、失败降级和离线读取契约 | - |
| M1 - 本地动量最小回测器 | REQ-001 - REQ-010, REQ-013 - REQ-017, REQ-020 - REQ-025, REQ-031, REQ-034 - REQ-041, REQ-057 | 仓库根目录结构、parquet 数据加载、复权一致校验、`available_at` 防护、T 日收盘后信号/T+1 成交、动量信号、组合净值、成本扣除、指标输出、报告 metadata、离线默认回测和数据新鲜度披露 | M0 |
| M2 - 参数扫描与报告 | REQ-011, REQ-012, REQ-018, REQ-026 - REQ-030, REQ-032, REQ-033, REQ-041 | `reports/momentum_param_sweep_local.csv`、`reports/momentum_candidates_local.csv`、过拟合警示、聚宽方向一致性差异分析模板、统一 metadata 限制项 | M1 |
| M3 - 真实性增强 | REQ-042 - REQ-046, REQ-058 | PIT universe provider、交易状态表、涨跌停约束、事件 `available_at`、扩展 raw/manifest/质量报告契约、偏差审计报告 | M2 |
| M4 - 策略扩展 | REQ-019 | RSI/MACD 接口复用和新增策略报告 | M2 |
| M5 - CR-005 Tushare 写湖与本地 benchmark | REQ-059 - REQ-069 | Tushare 显式写湖 / backfill 作业、`hs300_index` canonical/gold、benchmark typed result、quality/catalog、comparison、断网消费验证 | M0 |
| M6 - CR-005 Backtrader optional backend | REQ-070 | 可选 Backtrader 后端、backend unavailable 降级、轻量主路径不受影响、对照报告 | M5 |
| M7 - CR-011 生产级数据准入 | REQ-071 - REQ-077, REQ-081 | 真实 benchmark、PIT universe、可交易性、clean execution feed、复权/公司行动、行业市值风格、流动性容量成本和授权边界 gate | M5 |
| M8 - CR-011 因子审计与稳健性报告 | REQ-078 - REQ-080, REQ-082 | 完整 factor audit panel、rolling/年度/市场状态/参数/成本稳健性验证、新版报告声明门控和旧报告隔离 | M7 |
| M9 - CR-013 声明边界与 unsupported register | REQ-083 - REQ-087 | full-history blocked 声明、真实 VWAP / 分钟执行价 blocked 声明、unsupported register 文档与报告摘要、权限计数和证据保留 | M8 |
| M10 - CR-014 全 A 全历史生产数据湖基线 | REQ-088 - REQ-097 | 全 A since-inception current truth 范围、证券生命周期、P0 分层、catalog current pointer、增量刷新 / replay、DuckDB 只读候选评估、权限边界、claim boundary 和 TS-014 验证矩阵 | CP2 确认后进入 HLD；M9 旧声明边界保留为输入 |
| M11 - CR-017 复权双视图与 raw 执行价格隔离 | REQ-098 - REQ-104 | `prices_raw`、`adj_factor`、`prices_qfq`、`prices_hfq`、`returns_adjusted`、qfq `as_of_trade_date`、single-policy reader gate、旧 qfq 迁移声明和 QMT raw 执行价格边界 | M10；CP3 必须冻结复权公式、provider 字段解释、schema 和迁移策略 |
| M12 - CR-015 QMT foundation | REQ-105 - REQ-111 | Windows QMT / MiniQMT 节点边界、XtQuant adapter 合同、OMS order intent、订单状态机、pre-trade hard block、外置 broker lake、shadow / dry-run / mock 默认模式和凭据脱敏 | M11 可并行设计；真实发单后置到 CR-016 per-run 授权 |
| M13 - CR-016 QMT activation / ops | REQ-112 - REQ-122 | shadow / 模拟盘 / 实盘只读 / 小资金 / 资金放大 stage gate、runbook、per-run 授权、T+1 限价 / 保护价、对账、kill switch、实验注册、资金放大 gate 和 TS-015/016/017 验证矩阵 | M12 foundation 通过 CP7；CR-017 口径治理至少完成设计，资金放大前完成实现验证 |
| M14 - CR-018 production current truth closure | REQ-123 - REQ-132, REQ-135 - REQ-137 | CR014 S14 candidate 输入事实收敛、PIT/W3/benchmark/复权派生、quality/readiness、release summary、Explicit Publish Gate、current pointer smoke、rollback 和文档声明边界 | M10/M11；用户已批准 D1-D6；真实抓取 / 写湖 / publish 仍需 CP5 与单次授权 |
| M15 - CR-018 publish 后研究重跑与 QMT admission | REQ-133 - REQ-137 | 使用 published release 重跑阶段三到阶段五核心研究，输出生产口径低波 / 因子结论、blocked claims 和 QMT stage gate admission result | M14 publish + rollback smoke 通过；QMT simulation 仍需 CR016 stage gate 和 per-run 授权 |
| M16 - CR-019 阶段六多因子 admission baseline | REQ-138, REQ-144, REQ-154 | 阶段六多因子实验 49-66 gate、旧失败策略 blocked、5 日 dry-run 前置和 admission package 合同 | M14/M15；当前 CP2 只冻结需求，不执行真实数据、报告或 QMT |
| M17 - CR-019 QMT C/S bridge 设计与安全合同 | REQ-142, REQ-145 - REQ-153, REQ-159 - REQ-160 | local_backtest C 侧 Python client / 薄 CLI、Windows QMT S 侧 FastAPI gateway HLD/ADR、完整 endpoint matrix、运行门控、鉴权、绑定、防火墙、heartbeat、fallback、日志脱敏和禁止真实操作默认值 | M16 可并行设计；实现和依赖变更必须等 CP3/CP4/CP5/LLD |
| M18 - CR-019 后置执行 / ML / 高频能力 | REQ-139 - REQ-143, REQ-155 - REQ-158 | Backtrader optional backend、Qlib isolated runner、minute Spike、Level2 Spike 的触发条件和后续 CR 建议 | M16/M17 后按证据触发；未触发前不阻断 CP3 主线 |
| M19 - CR-025 research execution semantic alignment | REQ-161 - REQ-173 | production-grade research-to-execution 三条主线映射、optional reference 范围冻结、依赖隔离、clean feed gate、semantic diff report、target portfolio / order intent 衔接、Backtrader 本地项目模块级分析、安全计数、lightweight 主路径回归和 CP5 前不得实现边界 | CR-025 CP2 approved 后进入 CP3；CP5 批准前不实现、不新增依赖、不运行真实 Backtrader backend；源码级移植若被 HLD 推荐需单独决策；真实 QMT 由 CR-020..CR-024 独立授权 |

## 默认假设（REQUIRED 级别澄清采用的默认值）

| ID | 假设内容 | 影响范围 | 关联需求 |
|----|---------|---------|---------|
| A-001 | 第一版回测、扫描、候选筛选和本地差异分析主路径只读取本地 parquet、manifest 和质量报告摘要，不在主路径中自动联网。 | 数据层边界、测试稳定性 | REQ-016, REQ-034, REQ-057 |
| A-002 | 第一版股票池使用固定沪深 300 成分股快照。 | 回测偏差、报告解释 | REQ-003, REQ-031 |
| A-003 | 第一版信号在 T 日收盘后生成，使用 T 日收盘时已经可得的数据；成交只能发生在 T+1 或之后，避免前视偏差。 | 策略计算、成交时点和验收 | REQ-005, REQ-023 |
| A-004 | 手续费、滑点、印花税均作为参数配置，默认值在 HLD/LLD 确认，但报告必须记录实际使用值。 | 组合净值、报告可复现性 | REQ-009, REQ-035 |
| A-005 | CSV 是第一版报告必需输出，Notebook 和热力图为可选展示。 | 工程落地顺序、验收范围 | REQ-033 |
| A-006 | 本地与聚宽比较采用方向一致性，不要求逐日净值一致。 | 聚宽验证、验收标准 | REQ-030 |
| A-007 | 默认复权口径尚未确认；在确认前只固化“同一运行口径一致且报告记录实际口径”。 | 数据契约、聚宽对照、指标可解释性 | REQ-037 |
| A-008 | 第一版日线收盘价可在 T 日收盘后生成信号，但成交只能发生在 T+1 或之后；具体成交价和收益归属仍需 HLD 前确认。 | 信号时点、组合成交、净值归属 | REQ-005, REQ-023 |
| A-009 | 财报披露日和事件字段第一版默认不进入策略信号；如用户确认纳入，则必须提供事件级 `available_at` 并调整需求范围。 | 事件数据、未来函数防护 | REQ-038, REQ-045 |
| A-010 | 数据准备/更新流程可以联网，但必须独立于回测、扫描、候选筛选和差异分析主路径。 | 数据链路边界、离线验收 | REQ-016, REQ-034, REQ-047 |
| A-011 | 请求节流、重试退避、断点续传、raw 缓存、manifest 和质量报告属于第一版数据准备能力，不等同于回测主路径联网能力。 | HLD 分层、测试边界 | REQ-047 - REQ-057 |
| A-012 | 最近 N 个交易日回补的默认 N 尚未确认；需求阶段只固化“可配置且基于交易日历”。 | 数据更新周期、质量报告 | REQ-054, REQ-056 |
| A-013 | `hs300_index` 真实口径尚未确认；需求阶段默认要求显式记录 `benchmark_kind`，并将口径未确认视为 `required_missing`。 | benchmark 可比性、quality gate、对照报告 | REQ-061, REQ-063 |
| A-014 | Tushare 5000 档可作为 CR-005 优先真实源，但不会改变本地数据湖为事实源和消费层只读边界。 | Tushare 写湖、Data Loader、实验入口、Backtrader | REQ-059, REQ-060, REQ-064 |
| A-015 | 实验 17-21 旧报告结论保持 fixed snapshot / proxy baseline / close proxy 探索基线，CR-011 不修改旧报告内容。 | 报告追溯、结论边界 | REQ-080, REQ-082 |
| A-016 | CR-011 生产级验证窗口以实际 catalog/quality/readiness 覆盖为准；若只能覆盖 limited window，报告不得外推到完整旧样本区间。 | 真实数据覆盖、声明边界 | REQ-071, REQ-072, REQ-080 |
| A-017 | 因子预处理顺序沿用实验 17-21 的方向统一、去极值、标准化思路，但新版必须保留 raw / directional / winsorized / zscore 审计层。 | 因子面板、审计追溯 | REQ-078 |
| A-018 | 真实执行价、容量成本模型、行业/风格分类细节由 meta-se 在 HLD 中冻结；需求阶段只固化必需数据域、降级语义和验收字段。 | HLD 决策、后续 Story 拆解 | REQ-074, REQ-076, REQ-077 |
| A-019 | 本轮 meta-pm 只做需求/场景增量，不执行真实联网、真实 lake 写入、凭据读取或旧 `data/**` 操作。 | 安全边界、阶段门控 | REQ-081 |
| A-020 | CR-013 本轮只刷新 `REQUIREMENTS.md` 与必要澄清日志；`USE-CASES.md` 按 CR 文档处理决策保持不变，HLD / Story / README / docs / 代码 / 测试 / 报告 CSV 均不在本轮修改范围。 | 增量追溯、权限边界 | REQ-083 - REQ-087 |
| A-021 | CR-014 默认把“当前交易日”解释为最近已闭市且交易日历标记为 open 的交易日；最终口径待 CP2/HLD 确认。 | current truth、增量刷新、报告声明 | REQ-088, REQ-097 |
| A-022 | CR-014 默认 P0 dataset 沿用 CR-010 的 `prices`、`adj_factor`、`hs300_index`、`trade_calendar`、`index_members`、`index_weights`、`stock_basic`，并把生命周期 / 代码变更作为全 A current truth 必需能力；最终 P0 清单待 CP2/HLD 决策。 | P0 分层、coverage denominator、Story 拆解 | REQ-089, REQ-090 |
| A-023 | DuckDB 默认仅作为 HLD 待决策的只读 query / audit / feature extraction 候选，不进入需求阶段依赖、不替代 Parquet lake / catalog / manifest。 | 技术选型、依赖边界 | REQ-093 |
| A-024 | CR-014 本轮只修改 `USE-CASES.md`、`REQUIREMENTS.md` 和 `CLARIFICATION-LOG.md`，不修改 HLD、ADR、Story、LLD、README、docs、代码、测试、reports、`pyproject.toml` 或 `uv.lock`。 | 文件边界、变更追溯 | REQ-094 |
| A-025 | 未获得后续单独授权前，CR-014 provider fetch、真实 lake 写入、凭据读取、旧 `data/**` 操作、旧 reports 覆盖和 DuckDB 依赖修改均保持 0。 | 权限边界、安全验证 | REQ-094, REQ-095 |
| A-026 | 用户已在 CP2 intake 批准 CR-015 / CR-016 / CR-017 的推荐方案，D-ALL-01 至 D-CR16-01 作为需求基线输入。 | CP2 状态、HLD 输入 | REQ-098 - REQ-122 |
| A-027 | CR-017 默认采用 `prices_raw` + `adj_factor` 事实源、独立 qfq/hfq/returns_adjusted 派生视图、qfq `as_of_trade_date` 和 QMT raw 执行价格隔离。 | 数据湖口径、QMT 价格边界 | REQ-098 - REQ-104 |
| A-028 | 研究默认消费策略按场景分层：图表和人工核对可用 qfq，长期收益 / 因子研究推荐 hfq 或 returns_adjusted，交易执行只用 raw / broker price；最终默认值由 CP3 冻结。 | 研究口径、报告 metadata | REQ-099, REQ-101, REQ-102, REQ-122 |
| A-029 | CR-015 默认只做 shadow / dry-run / mock foundation，不授权真实发单、撤单、账户写操作、凭据读取或真实 broker lake 写入。 | 安全边界、测试策略 | REQ-105 - REQ-111 |
| A-030 | CR-015 初期账户范围仅为普通股票现金账户；信用、多资产、期货、期权和完整第三方交易平台迁移为 Out of Scope。 | 订单规则、风控范围 | REQ-106, REQ-109 |
| A-031 | broker lake 默认为外置 root 或等价受控存储；需求阶段只定义契约和 dry-run / mock 审计，不写仓库 `data/**` / `reports/**`。 | 存储边界、脱敏 | REQ-108, REQ-111 |
| A-032 | CR-016 阶段路径固定为 `shadow -> QMT 模拟盘 -> 实盘只读 -> 小资金实盘 -> 放大资金`，不可跳过。 | 运行治理、资金风险 | REQ-112, REQ-119 |
| A-033 | 每次真实 QMT 操作必须有 per-run 授权；授权只记录脱敏摘要，不记录凭据值、账户敏感信息或 `.env` 内容。 | 安全授权、审计 | REQ-114, REQ-111 |
| A-034 | CR-017 不阻断 CR-016 技术模拟盘，但阻断生产策略复权治理完成声明和资金放大，直到复权双视图实现和验证通过。 | 阶段准入、声明边界 | REQ-118, REQ-119, REQ-120 |
| A-035 | 本轮 meta-pm 只修改 `USE-CASES.md`、`REQUIREMENTS.md` 和 `CLARIFICATION-LOG.md`；不修改代码、不读取 `.env` 或账户信息、不真实抓取、不写湖、不发单。 | 文件边界、权限边界 | REQ-104, REQ-110, REQ-114 |
| A-036 | CR-018 第一版 production current truth 时间范围采用 `2015-01-05..latest_closed_trade_date` 的 scoped release；2015 前回补作为 blocked/future backfill 记录，除非后续用户要求 since-inception 一次性关闭。 | release scope、coverage denominator、Story 拆解 | REQ-124, REQ-126 |
| A-037 | CR-018 默认 P0 dataset group 包含 prices_raw、adj_factor、qfq/hfq/returns_adjusted、trade_calendar、PIT universe/lifecycle/code-change、trade_status、prices_limit/ST/suspend、HS300/ZZ500/ZZ1000/中证全指行情/成分/权重。 | 数据湖生产闭环、publish gate | REQ-126 - REQ-131 |
| A-038 | 行业、市值、风格、流动性、ADV、turnover_rate 和容量成本默认列为 P1，但阻断中性化、纯 alpha、容量和 scale_up 声明；若用户要求解除这些声明，则升为 P0。 | 研究声明、QMT admission、资金放大 | REQ-135, REQ-136 |
| A-039 | publish 粒度默认采用 release-level 总门 + dataset-level 明细，rollback 以 release 为单位；不采用多个独立 current pointer 写入口。 | publish / rollback / 审计 | REQ-131, REQ-132 |
| A-040 | QMT simulation、live_readonly、small_live 和 scale_up 默认全部等数据湖 publish + production research rerun PASS 后再申请解禁；不采用先行技术 simulation 的备选路径。 | QMT stage gate、运行授权 | REQ-123, REQ-134 |
| A-041 | 用户已批准 CR-019 D1-D7 推荐方案，作为本轮需求和场景基线输入。 | CR-019 CP2 / CP3 输入 | REQ-138 - REQ-158 |
| A-042 | 用户已纠正：FastAPI gateway 必须支持完整 QMT 功能接口类别，不能把“不做应用层鉴权”误解为“不做 simulation / account / cancel 等 QMT 功能”。 | API 合同、能力边界 | REQ-146, REQ-147 |
| A-043 | WSL 研究节点不直接依赖 xtquant；Windows QMT 节点拥有 QMT adapter 与独立 FastAPI gateway 命令，gateway 必须从回测框架主进程摘离。 | 部署架构 | REQ-142, REQ-149 |
| A-044 | signed file drop 从 Q-038 旧主选降级为 fallback；fallback 不得自动绕过 gateway 触发真实 QMT，可采用 blocked-only 或 dry-run / 人工处理。 | fallback 安全 | REQ-145, REQ-150 |
| A-045 | simulation submit / cancel、账户 snapshot、reconciliation、kill-switch、live submit / cancel 等 endpoint 类别必须可设计和支持；真实转发由 run mode、stage gate、risk gate 和 kill switch 控制。 | stage gate、运行门控 | REQ-146, REQ-147, REQ-148 |
| A-046 | 本轮 CR-019 只做需求 / 场景 / CP1 / CP2 准备，不实现代码、不新增依赖、不读取凭据、不调用真实 QMT、不真实 provider fetch、不写真实 data/reports/delivery。 | 权限边界 | REQ-152 |
| A-047 | QMT 系统说明文档只作为能力背景，不代表当前项目已拥有真实账户、模拟盘、Level2 或交易权限。 | 文档引用边界 | REQ-153 |
| A-048 | Backtrader、Qlib、分钟数据和 Level2 均为后置能力，不作为阶段六 P0。 | 范围控制 | REQ-139 - REQ-143, REQ-155 - REQ-158 |
| A-049 | 申请 QMT simulation 前必须先完成 shadow + 连续 5 个真实交易日 dry-run；通过后仍需 per-run authorization。 | 运行治理 | REQ-144, REQ-154 |
| A-050 | FastAPI bind host/port、防火墙、token/HMAC 细节、endpoint schema 和 fallback 切换条件为 CP3/HLD 必须冻结项，不阻断 CP2 自动预检。 | CP3 输入 | REQ-148, REQ-149, REQ-150 |
| A-051 | 用户已确认 Q40 采用“多基准看板 + primary benchmark 规则”，即同时输出 HS300、ZZ500、ZZ1000 和中证全指，并按策略 universe / 风格选择 primary benchmark。 | benchmark / tracking / freeze fields | REQ-138, REQ-154 |
| A-052 | 用户已补充 QMT 模块必须为独立 C/S 模块：C 侧位于 local_backtest，S 侧部署在 Windows QMT 节点并将 REST 请求转换为 QMT 接口调用。 | 模块边界、部署、API 合同 | REQ-149, REQ-159, REQ-160 |
| A-053 | C 侧接口当前推荐 Python client / 函数调用作为主接口，CLI 作为薄包装；该推荐需在 CP2 approve 或 CP3 HLD 中冻结。 | C 侧接口设计 | REQ-160 |
| A-054 | CR-025 已由 CR-019 follow-up Track B 转为正式 active CR，但当前仅处于 CP2 intake；用户未授权实现、依赖变更或真实运行。 | 变更门控、文件边界 | REQ-161 - REQ-168 |
| A-055 | Backtrader 在 CR-025 中只作为 optional execution realism / semantic reference，不替代 lightweight engine、不作为阶段六 P0、不作为 QMT admission 通过证据。 | 范围控制 | REQ-161, REQ-166 |
| A-056 | Backtrader optional backend 后续实现必须使用本地 clean feed；feed 事实由既有数据湖 / reader / quality gate 提供，Backtrader 不负责生成或补齐事实数据。 | 数据契约、质量门控 | REQ-163 |
| A-057 | 未安装 Backtrader 是合法环境；optional backend 不可用不得影响默认研究、轻量回测和数据读取。 | 依赖隔离、回归 | REQ-162, REQ-167 |
| A-058 | 本轮 meta-pm 只修改 `USE-CASES.md`、`REQUIREMENTS.md`、`CLARIFICATION-LOG.md`、CP1 检查和交接文件；不修改业务代码、测试、依赖、数据、HLD、Story、README 或 docs。 | 文件边界、安全边界 | REQ-168 |
| A-059 | 用户已澄清目标为生产级策略研究回测、模拟盘和实盘框架；CR-025 需要服务 production-grade research-to-execution 路线，而不是开发框架级 Backtrader/lightweight 回测框架。 | 范围控制、CP2 决策 | REQ-161, REQ-169, REQ-170 |
| A-060 | 三条主线默认映射为：研究可信度由数据湖 / ResearchDataset / admission gate 承接；回测 / 模拟一致性由 CR-025 承接；QMT 生产执行由 CR-020..CR-024 承接。 | CR tracking、推进顺序 | REQ-170, REQ-171 |
| A-061 | CR-025 可以为后续 QMT production route 提供 target portfolio / order intent 衔接和 semantic diff 证据，但不能授权 gateway 启动、simulation、live-readonly、small-live 或 scale-up。 | 运行授权、安全边界 | REQ-165, REQ-169, REQ-171 |
| A-062 | 用户要求 meta-se 在 CR-025 CP3/HLD 充分分析 `/home/hyde/download/backtrader`，对比可借鉴、可适配、可移植和禁止移植模块，并把移植候选及其许可证 / 维护 / 回归影响写入 HLD。 | HLD 输入、架构决策 | REQ-172, REQ-173 |
| A-063 | CR-030 的 schema 和校验采用“项目自有契约 + 现有基线复用 + 外部项目 cross-check + fail-closed”策略，不从零设计，也不直接采用 Qlib / Alphalens / Zipline / LEAN 对象作为内部 truth。 | schema provenance、校验策略 | REQ-176, REQ-177, REQ-183, REQ-185 |
| A-064 | 本地 Qlib `/home/hyde/download/qlib` 仅作为静态分析输入；当前未授权安装、运行、qrun、provider_uri、数据下载或源码迁移。 | 外部项目边界、安全边界 | REQ-175, REQ-182, REQ-184 |
| A-065 | CR-030 HLD 必须同时比较 Qlib、Alphalens、vectorbt、PyBroker、bt、Zipline Reloaded、QuantConnect LEAN、RQAlpha、vn.py / vnpy.alpha 和 Backtrader，防止只借鉴单一项目造成架构偏差。 | HLD 输入、外部项目矩阵 | REQ-175, REQ-185 |
| A-066 | 现有 `research_dataset.py`、实验 17-21、CR-011 factor audit panel、label window gate 和 Stage6 admission gate 不是可忽略旧实现，而是 CR-030 schema / 校验 / 准入的基线事实。 | 复用、兼容、避免双 truth | REQ-174, REQ-176, REQ-177, REQ-183 |
| A-067 | CR-026 Qlib isolated runner 保持后续 Spike candidate；只有 CR-030 合同冻结后，才能单独评估 runner I/O、依赖隔离、provider 禁用、report import/export 和运行授权。 | follow-up tracking、分流 | REQ-184 |
| A-068 | CR-030 研究结果最多进入 `StrategyAdmissionPackage` 和 `order_intent_draft_v1` 草稿边界；任何 QMT gateway、simulation、live、account query、order submit 或 cancel 仍需 CR-020..CR-024 独立授权。 | 运行授权、QMT 边界 | REQ-181, REQ-182 |
| A-069 | 外部项目矩阵中的源码级迁移候选默认视为禁止，除非 CP3 单独列为决策项并在 CP5 前取得实现授权、许可证影响评估和回归范围确认。 | 许可证、源码迁移 | REQ-175, REQ-182, REQ-185 |
| A-070 | CP3 HLD 通过只表示架构方向和决策项通过，不表示允许实现、多因子框架落地、依赖变更、真实数据写入、catalog publish、外部项目运行或交易相关操作。 | CP3 人工门禁、授权边界 | REQ-182, REQ-185 |
| A-071 | CR-046 已由用户收窄为 framework-first：先冻结 QMT / MiniQMT 双目标策略交付框架、验证框架、MiniQMT runner 安装设计和策略包契约。 | 范围控制、CP2 决策 | REQ-186, REQ-200 |
| A-072 | 用户当前已有 QMT 终端权限，可在 QMT 终端内运行策略；当前没有 MiniQMT 权限，MiniQMT runner 属未来路线。 | 平台事实、环境边界 | REQ-188, REQ-189, REQ-193 |
| A-073 | CR-046 不交付具体策略，不执行 QMT 终端运行验证，不连接 MiniQMT，不读取账户、资金、持仓、委托或成交，不 submit/cancel，不 simulation/live。 | 安全不授权、运行门禁 | REQ-186, REQ-192, REQ-200 |
| A-074 | 首个具体策略双目标交付应作为 CR047-candidate，研究框架完善应作为 CR051-candidate；CR046 只输出后续入口和阻塞前置。 | follow-up tracking、分流 | REQ-191, REQ-194 |
| A-075 | 当前产品基线仍在 legacy `process/USE-CASES.md` / `process/REQUIREMENTS.md`，CP2 不静默迁移到 `docs/product/` 双真相源。 | 文档路由、交付隔离 | REQ-198 |

## 明确排除项（Out of Scope）

- 第一版不精确建模完整停牌状态。
- 第一版不做涨跌停撮合或涨跌停买卖限制。
- 第一版不做历史成分股点时还原。
- 第一版不做分红送转和复权因子自动处理。
- 第一版不处理新股上市初期特殊规则。
- 第一版不处理退市整理与摘牌规则。
- 第一版不处理 ST 历史状态。
- 第一版不把财报披露日或财报事件字段作为策略信号输入。
- 第一版不做分钟级撮合。
- 第一版不做真实成交量约束。
- 第一版不做实盘接口、订单簿或完整聚宽 API 兼容层。
- 第一版不自动调用聚宽、不自动联网、不轮询平台任务。
- 第一版不允许回测、扫描、候选筛选或本地差异分析在主路径中联网补数。
- 第一版不做高频抓取、实时行情订阅或对免费数据源的压力测试。
- 第一版不以热力图、Notebook 或交互式看板作为阻塞性交付。
- 第一版不引入 RQAlpha、Backtrader、vectorbt 或 bt 作为核心框架。
- CR-005 不把 Tushare API 直接接入 `engine/data_loader.py`、实验入口、benchmark resolver 或 Backtrader adapter。
- CR-005 不允许消费层在缺失 `hs300_index` 时自动联网 fetch/backfill。
- CR-005 不允许把代理基准写入 `hs300_index` 字段或声明为沪深 300 相对收益。
- CR-005 不把 Backtrader 升级为默认主框架，不在 Backtrader adapter 内生成 PIT、计算复权因子、读取 Tushare 或绕过 quality gate。
- CR-011 不覆盖、删除或重写 `reports/experiment_17_21/*` 旧报告；旧报告仅作为 fixed snapshot / proxy baseline 历史基线。
- CR-011 需求/场景阶段不执行真实联网、真实 Tushare/JQData 抓取、真实 lake 写入、旧 `data/**` 操作或凭据读取。
- CR-011 不声明超出 quality/readiness 覆盖窗口的完整历史 PIT、全市场长期覆盖或生产 current truth。
- CR-011 在行业、市值、风格、容量、公司行动或执行价数据缺失时，不允许声明对应中性化、容量可交易、复权链路可审计或真实执行价结论。
- CR-011 不把新版生产级因子研究实现提前到 CP3/CP4/CP5 门控之前；CP5 批次确认通过前不得实现代码。
- CR-013 不补齐 `2020-01-01..2024-12-31` full-history 数据，不声明 full-history production strict readiness，不把 CR-012 limited-window pass 外推为全历史可用。
- CR-013 不接入或构造真实 VWAP、分钟线、逐笔、盘口、委托、成交明细或真实撮合执行价；不得由 close proxy 或 `amount/volume` 派生真实 VWAP claim。
- CR-013 不修改或覆盖 `reports/data_lake_readiness_2020_2024/*`、`reports/data_lake_readiness_limited_2025_2026/unsupported_data_register.csv` 或其他旧报告证据。
- CR-013 不授权 provider fetch、真实 lake 写入、凭据读取、旧 `data/**` 读取；后续如需执行真实补数或真实数据接入，必须另起 Story / CP5 并获得用户显式授权。
- CR-014 需求澄清阶段不执行 provider fetch、不读取凭据、不写真实 lake、不读取 / 列出 / 迁移 / 复制 / 比对 / 删除旧 `data/**`，不覆盖旧 reports。
- CR-014 需求澄清阶段不修改 HLD、ADR、Story Backlog、Development Plan、Story、LLD、README、docs、代码、测试、`pyproject.toml`、`uv.lock` 或任何 reports。
- CR-014 不在需求阶段把 DuckDB 作为已批准依赖或默认事实源；DuckDB 只作为 HLD 待决策的 read-only query / audit / feature extraction 候选。
- CR-014 不允许 DuckDB `.duckdb` 文件替代 Parquet lake、catalog current pointer、manifest 或 publish gate。
- CR-014 不在全 A since-inception coverage、证券生命周期、P0 dataset、quality/readiness 和 current pointer 未通过前声明 production current truth。
- CR-015 不授权真实 `order_stock`、`order_stock_async`、`cancel_order_stock`、账户写操作、账户凭据读取或真实 broker lake 写入；默认仅 shadow / dry-run / mock。
- CR-015 不支持信用账户、多资产、期货、期权、保证金、融券、完整第三方交易平台迁移或策略层直接调用 QMT API。
- CR-015 / CR-016 不允许把 qfq/hfq 复权价作为 QMT 委托价、成交价、成交核算价或 broker 对账价。
- CR-016 不允许跳过 shadow、模拟盘、实盘只读、小资金实盘、资金放大阶段门控；不允许无 per-run 授权的真实 QMT 操作。
- CR-016 不解除真实 VWAP、minute、tick、level2、order-match、微观结构冲击成本或真实撮合执行价 blocked claim。
- CR-017 不在本阶段真实抓取、真实写湖、发布 current pointer、批量重算 / 覆盖旧 qfq 数据、修改代码或引入依赖。
- CR-017 不把 `adj_factor` 需求等同于完整公司行动事件链路；在公司行动数据补齐前只能声明使用复权因子，不声明完整公司行动审计。
- CR-015 / CR-016 / CR-017 不在 CP3/CP4/CP5/CP6/CP7/CP8 门控前进入实现、真实运行或关闭 CR。
- CR-018 不把 CR014 S14 `prices` / `adj_factor` candidate 直接 publish；candidate、validate PASS、parity PASS 均不等于 published current truth。
- CR-018 不在 CP5 与单次授权前新增 provider fetch、读取凭据、写真实 lake、更新 current pointer、启动 QMT simulation / live 操作或写持久 `.duckdb` 事实源。
- CR-018 不在行业 / 市值 / 风格 / 流动性 / 容量数据缺失时声明纯 alpha、行业中性、市值中性、容量可交易或 scale_up ready。
- CR-019 requirement-clarification / CP2 准备阶段不实现 FastAPI、不新增依赖、不启动本地服务、不调用真实 QMT / MiniQMT / XtQuant、不读取凭据、不执行真实 provider fetch、不写真实 data / reports / delivery。
- CR-019 不把 FastAPI 服务存在、health pass、capabilities pass 或 dry-run pass 等同于真实 QMT simulation 授权；simulation endpoint 必须 later-gated。
- CR-019 不允许 fallback 自动真实发单、撤单、账户查询、账户写操作或 broker lake 写入；signed file drop 仅为 dry-run / blocked fallback。
- CR-019 不把 Backtrader、Qlib、分钟数据或 QMT Level2 作为阶段六 P0；四类能力需满足后置触发条件并通过后续 CR / CP 门控。
- CR-019 不基于 QMT 系统说明文档推断当前项目已拥有真实账户、模拟盘、Level2、交易、撤单、账户查询或行情权限。
- CR-025 CP2 前不实现 Backtrader backend、不新增依赖、不修改 `pyproject.toml` / `uv.lock`、不运行 Backtrader、不调整业务代码或测试。
- CR-025 不把 Backtrader 设为默认主路径、默认依赖、生产 truth、阶段六 P0、QMT simulation admission pass 或 lightweight engine 替代方案。
- CR-025 不复制、裁剪或移植 Backtrader 源码，不自研完整事件驱动交易框架，不把当前任务扩大为完整交易平台迁移。
- CR-025 不直接实现模拟盘、实盘只读、小资金实盘、资金放大、服务启动、端口绑定或 QMT gateway 实机运行；这些必须由 CR-020..CR-024 独立启动和授权。
- CR-025 不接入 Backtrader live broker / store、真实 broker、QMT / MiniQMT / XtQuant、simulation、live、account query、cancel 或 order submit。
- CR-025 不触发 provider fetch、真实 lake write、broker lake write、catalog publish、报告覆盖、凭据读取、真实数据或真实账户操作。
- CR-025 不用 Backtrader 生成 PIT universe、复权因子、benchmark、tradability、quality status 或任何数据湖事实；这些必须来自既有本地数据 / 数据湖契约。
- CR-030 CP2 / CP3 阶段不实现多因子框架、不新增依赖、不修改 `pyproject.toml` / `uv.lock`、不修改业务代码或测试、不运行外部项目、不 clone / install / qrun / notebook 执行任何参考项目。
- CR-030 不把 Qlib、Alphalens、vectorbt、PyBroker、bt、Zipline Reloaded、QuantConnect LEAN、RQAlpha、vn.py / vnpy.alpha 或 Backtrader 设为默认框架、默认 runner、默认 provider、默认 optimizer、事实源或 report truth。
- CR-030 不复制、裁剪、改写或源码级迁移外部项目源码、样例、测试、数据、runner runtime、provider runtime、broker/live trading runtime；源码级迁移必须单列 CP3/CP5 授权。
- CR-030 不授权 provider fetch、真实联网补数、真实 lake write、catalog publish、broker lake write、报告覆盖、凭据读取、QMT / MiniQMT / XtQuant、gateway 启动、simulation、live_readonly、small_live、scale_up、发单、撤单或账户查询。
- CR-030 不把因子评价、多因子组合、回测报告、`StrategyAdmissionPackage` 或 `order_intent_draft_v1` 草稿声明为 QMT-ready、simulation-ready、live-ready、production truth 或真实可交易证据。
- CR-030 不从零发明 schema；若 HLD 需要新增字段或对象，必须说明其相对 `research_input_v1`、实验 17-21、CR-011 factor panel audit、label window gate 和 Stage6 admission gate 的增量理由、兼容策略和 fail-closed 校验。
- CR-046 不交付具体交易策略、不生成可交易策略包、不执行 QMT 终端 shadow / 模拟盘运行验证、不启动 QMT 运行环境、不连接 MiniQMT / XtQuant、不订阅行情、不读取账户 / 资金 / 持仓 / 委托 / 成交、不 submit/cancel、不 simulation/live。
- CR-046 不真实安装 MiniQMT runner、不创建 Windows bridge runtime、不读取或输出 `.env`、token、account_id、账号、密码、session、cookie、private key 或真实私有路径。
- CR-046 不触发 provider fetch、真实 lake write、broker lake write、catalog publish、报告覆盖、真实数据写入或依赖变更；MiniQMT runner 安装只定义设计和 dry-run 计划。
- CR-046 不把 fixture/schema/static validation pass 声明为 QMT-ready、MiniQMT-ready、simulation-ready、live-ready 或真实可交易证据。
- CR-046 不在当前 CR 内改造研究框架代码；研究框架完善只登记为 CR051-candidate，启动时重新做冲突预检和 CP2。

## 目标平台

- [x] 本地 Python 研究工具
- [ ] Claude Code
- [ ] Codex
- [ ] OpenClaw
