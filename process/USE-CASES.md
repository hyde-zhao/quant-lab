---
status: confirmed
version: "1.15"
confirmed_by: "user"
confirmed_at: "2026-06-13T22:03:22+08:00"
engagement_mode: production
scenario_subject_type: target-artifact
scenario_subject_id: "local-backtest-production-data-lake-and-qmt-trading-layer"
target_artifact_type: tool
governance_mode: review-gated
review_policy: strict
total_use_cases: 32
---

# 使用场景

## 修订记录

| 版本 | 日期 | 修订人 | 变更要点 | 文档处理方式 |
|---|---|---|---|---|
| 1.0 | 2026-05-13 | meta-pm | 初始场景基线，覆盖本地日频回测、动量参数扫描、报告与聚宽候选验证 | 初始化基线 |
| 1.1 | 2026-05-13 | meta-pm | 根据 Review Round 1 补齐本地/聚宽边界、参数命名、数据偏差、扫描报告、UC-04 差异分析和 D1 覆盖 | 在既有 draft 上增量修订，保持 UC 编号与场景基线可追溯 |
| 1.2 | 2026-05-14 | meta-pm | 根据需求刷新分派补强复权口径、T 日信号/T+1 成交、`available_at`、历史窗口剔除、缺失价/无成交处理、非 PIT 股票池、报告 metadata 限制项和真实性增强优先级 | 需求确认前在既有 draft 上增量修订，不创建 CR，不改变确认状态 |
| 1.3 | 2026-05-14 | meta-pm | 根据数据源限速刷新分派补强独立数据准备、请求节流、重试退避、断点续传、raw 缓存、manifest、增量更新、最近 N 个交易日回补、质量报告、失败降级和回测主路径离线硬约束 | 需求确认前在既有 draft 上增量修订，不创建 CR，不改变确认状态 |
| 1.4 | 2026-05-17 | meta-pm | 按 CR-005 第三轮评审增量补齐本地 `hs300_index` benchmark 缺失后的只读消费、structured `required_missing`、Tushare 写湖补齐作业、benchmark 口径/质量/缺口解释和 Backtrader optional backend 边界 | CR-005 原文档增量更新；保留 UC-01 至 UC-06 旧基线，新增 UC-07 并回链 CR-005 文档处理决策 |
| 1.5 | 2026-05-23 | meta-pm | 按 CR-011 增量补齐生产级因子研究数据场景，覆盖真实 benchmark、PIT 股票池、可交易性、执行价、复权/公司行动、行业市值风格、流动性容量成本、因子审计面板、稳健性验证和真实数据授权边界 | CR-011 原文档增量更新；保留 UC-01 至 UC-07 旧基线，新增 UC-08 并回链 CR-011 文档处理决策 |
| 1.6 | 2026-05-26 | meta-pm | 按 CR-014 增量补齐 A 股自存在 / 上市日起至当前交易日的生产级全历史数据湖场景，覆盖全 A current truth、证券生命周期、P0 dataset 分层、catalog current pointer、增量刷新 / 重放、DuckDB 只读查询审计候选、权限边界、claim boundary 和验证场景 | CR-014 原文档增量更新；保留 UC-01 至 UC-08 旧基线，新增 UC-09 并回链 CR-014 文档处理决策 |
| 1.7 | 2026-05-27 | meta-pm | 按 CR-015 / CR-016 / CR-017 增量补齐 QMT 交易接入 foundation、模拟盘 / 实盘阶段激活和复权双视图场景，覆盖 OMS / adapter / broker lake / pre-trade hard block、shadow / dry-run / mock 默认边界、raw/qfq/hfq/returns_adjusted 分层、QMT raw 执行价格隔离、runbook、对账、kill switch 和 per-run 授权 | CR-015 / CR-016 / CR-017 原文档增量更新；保留 UC-01 至 UC-09 旧基线，新增 UC-10 至 UC-12 并回链三张 CR 的文档处理决策和 CP2 intake approved 结论 |
| 1.8 | 2026-05-29 | meta-pm / meta-po | 按 CR-018 增量补齐数据湖 production current truth 闭环和 QMT 后置场景，覆盖 CR014 S14 candidate 输入事实、PIT/W3/benchmark/复权派生、quality/readiness、Explicit Publish Gate、rollback、发布后研究重跑和 QMT stage gate 阻断 | CR-018 原文档增量更新；保留 UC-01 至 UC-12 旧基线，新增 UC-13 至 UC-14，并回链用户 D1-D6 批准结论 |
| 1.9 | 2026-05-30 | meta-pm | 按 CR-019 增量补齐阶段六 A 股多因子模拟盘准入与 Windows QMT FastAPI 本地服务桥接场景，覆盖 D1-D7、5 日 dry-run、simulation later-gated、signed file drop fallback、Backtrader/Qlib/minute/Level2 后置触发条件 | CR-019 原文档增量更新；保留 UC-01 至 UC-14 旧基线，新增 UC-15 至 UC-18，并保留 Q-038 signed file drop 为 fallback |
| 1.10 | 2026-05-30 | meta-po | 按用户补充修订 CR-019：Q40 采用多基准 + primary benchmark 推荐方案；QMT 模块定义为独立 C/S 模块，C 侧位于 local_backtest 并暴露统一 Python 接口，S 侧部署在 Windows 并通过 REST 转发 QMT 能力；C 侧接口形态进入 CP2 决策项 | CR-019 原文档增量更新；保留 UC-15 至 UC-18，不新增场景编号 |
| 1.11 | 2026-05-31 | meta-pm | 按 CR-025 增量补齐 Backtrader optional execution backend hardening 场景，覆盖可选后端默认关闭、依赖隔离、clean feed、执行语义差异报告、轻量主路径不替代、无真实 broker / QMT / provider / lake / publish 授权 | CR-025 原文档增量更新候选；保留 UC-01 至 UC-18 旧基线，新增 UC-19；本增量待 CP2 人工确认 |
| 1.12 | 2026-05-31 | meta-po | 按用户 CP2 修改意见将 CR-025 修订为 production-grade research-to-execution 路线中的研究执行语义对照与接口对齐，补充研究可信度、回测 / 模拟一致性、QMT 生产执行三条主线，明确 Backtrader 仅为 optional semantic reference | CR-025 原文档增量修订；保留 UC-01 至 UC-19 旧基线，不新增场景编号；本增量待 CP2 人工确认 |
| 1.13 | 2026-06-01 | meta-po | 用户批准 CR-025 CP2，并要求 CP3/HLD 中由 meta-se 充分分析本地 Backtrader 项目 `/home/hyde/download/backtrader`，记录可借鉴、可适配、可移植和禁止移植模块 | CR-025 场景基线确认；保留 UC-19 编号，新增 HLD 输入与验证场景，不授权实现或源码级移植 |
| 1.14 | 2026-06-03 | meta-po | 用户授权进入 CR-030 HLD，回填 CR-030 多因子研究框架借鉴与研究闭环标准化场景，覆盖外部项目静态借鉴、项目自有多因子契约、因子面板 / 标签窗口、单因子评价、多因子组合、实验追踪和策略准入包边界 | CR-030 原文档增量更新；保留 UC-01 至 UC-19 旧基线，新增 UC-20 至 UC-27；CP2 通过仅授权 HLD，不授权实现、依赖变更、外部项目运行、源码迁移、provider/lake/publish、QMT/simulation/live 或凭据读取 |
| 1.15 | 2026-06-13 | meta-po | 按 CR-046 增量补齐 QMT / MiniQMT 双目标策略交付框架场景，覆盖策略核心合同、QMT 终端策略包、MiniQMT runner 安装设计、验证框架、后续策略交付门禁和研究框架反向约束 | CR-046 原文档增量更新；保留 UC-01 至 UC-27 旧基线，新增 UC-28 至 UC-32；用户已于 2026-06-13T22:03:22+08:00 通过 CP2；不授权具体策略交付、QMT 运行验证、MiniQMT 连接、submit/cancel、simulation/live、provider/lake/publish 或凭据读取 |

## 用户画像（Personas）

| 画像 ID | 角色名称 | 典型背景 | 核心诉求 | 技术水平 |
|---|---|---|---|---|
| P-01 | 量化策略学习者 / 研究者 | 已跑通过聚宽“实践六”动量策略，希望在本地提高研究效率。这里的“实践六”指用户原始学习路径中的第六个策略实践案例，当前文档只承接其动量选股规则，不绑定任何平台课程实现。 | 用透明、可调试、速度更快的本地工具完成大部分策略研究和参数扫描。 | 中级 |
| P-02 | 策略验证者 | 需要把本地筛出的少量候选参数回填到聚宽做真实性校验。 | 减少平台任务数量，保留最终平台验证。 | 中级 |
| P-03 | 因子研究数据审计者 | 需要把实验 17-21 的固定快照 / proxy 结论升级为可审计的生产级研究输入，并识别哪些声明仍被数据缺口阻断。 | 让因子结论、报告声明、数据 lineage、可交易性和稳健性验证可以被复查、复跑和分层验收。 | 高级 |
| P-04 | 生产数据湖负责人 / 数据工程审计者 | 负责把研究数据湖从 limited-window 结果升级为面向全 A 股全生命周期的生产级 current truth，并对 provider、权限、catalog、回放和声明边界负责。 | 让 A 股证券自存在 / 上市日起至当前交易日的正式数据集可审计、可发布、可回滚、可增量刷新，并能支撑只读查询、审计和特征抽取。 | 高级 |
| P-05 | QMT 交易接入与运行负责人 | 负责把本地研究信号安全接入 Windows QMT / MiniQMT 节点，设计 OMS、adapter、broker lake、风控和运行手册。 | 在不绕过风控、不泄露凭据、不误用复权价下单的前提下，分阶段验证 shadow、模拟盘、实盘只读和小资金实盘链路。 | 高级 |
| P-06 | 研究口径与交易价格审计者 | 负责审查研究使用的前复权 / 后复权 / 收益率口径和交易执行使用的原始价格口径是否隔离。 | 让研究结果、报告声明、QMT order intent、成交和对账都能解释各自价格来源，避免把 qfq/hfq 复权价误当真实交易价格。 | 高级 |
| P-07 | 阶段六多因子模拟盘准入负责人 | 负责把 production current truth、因子库、组合构建、dry-run、QMT bridge 和 admission package 收敛为可审查准入链路。 | 在不误触真实 QMT、不绕过 per-run 授权的前提下，判断阶段六多因子策略是否可申请模拟盘。 | 高级 |
| P-08 | 研究执行后端评估者 / 回测-模拟一致性负责人 | 负责评估轻量回测主路径、Backtrader optional semantic reference 和后续 QMT simulation 之间的语义差异、接口边界和回归风险。 | 在保持轻量主路径稳定的前提下，将研究输出收敛为可审计 target portfolio / order intent，并把 Backtrader 作为显式选择的执行真实性对照，而不是默认框架或真实交易通道。 | 高级 |

## 成功指标（Success Metrics）

| 指标 ID | 指标名称 | 度量方式 | 目标值 |
|---|---|---|---|
| SM-01 | 历史区间可运行 | 对固定沪深 300 股票池和本地 parquet 执行动量回测 | 覆盖 2019-01-01 至 2025-12-31，输出完整净值序列 |
| SM-02 | 指标完整性 | 检查单次回测结果字段 | 至少包含累计收益、年化收益、最大回撤、Sharpe 和日净值曲线 |
| SM-03 | 参数扫描覆盖 | 执行默认网格 `lookbacks * rebalance_freqs * fractions = 5 * 4 * 3` | 60 组参数均生成一行结果 |
| SM-04 | 平台任务减少 | 对比本地扫描后需要提交到聚宽的候选数 | 聚宽候选验证不超过 4 组参数，且第一版不要求自动调用聚宽或自动联网 |
| SM-05 | 本地扫描效率与平台任务减少 | 记录本地 60 组参数扫描总耗时，并统计需要回填聚宽验证的候选数 | 在相同机器和同一数据快照下，`reports/momentum_param_sweep_local.csv` 生成耗时应被记录为 `scan_elapsed_seconds`；平台验证任务数从 60 组降至不超过 4 组。若无聚宽耗时基线，第一版只验收耗时记录和任务数减少，不把相对耗时百分比作为阻塞条件 |
| SM-06 | 策略逻辑方向一致性 | 检查本地与聚宽版本的核心选股口径 | “方向一致”指候选参数排序方向、收益/回撤量级、换手特征和差异解释一致可解释；不要求逐日净值完全一致 |
| SM-07 | 数据准备可追溯与离线可运行 | 检查数据准备 manifest、raw 缓存、标准化 parquet 和数据质量报告，并在断网环境执行回测/扫描 | 数据准备记录批次、限速、重试、失败项和覆盖范围；本地 parquet schema 与覆盖区间合规时，回测、扫描和候选筛选不联网仍可运行，并披露数据新鲜度 |
| SM-08 | 本地沪深 300 基准可用性 | 检查 `hs300_index` canonical/gold、quality CSV、catalog 和 benchmark resolver 输出 | `hs300_index` 可用时返回明确 benchmark 口径、覆盖区间、交易日历分母、缺失交易日和 quality status；缺失时返回 structured `unavailable` / `required_missing` 与可执行补齐建议，不静默代理 |
| SM-09 | Tushare 补齐链路分层隔离 | 在断网环境运行消费层，并在显式数据准备命令中验证 Tushare 写湖计划 | Data Loader、实验入口、benchmark resolver 和 Backtrader 网络调用次数为 0；只有用户显式执行 `market_data` 写湖 / 数据准备层 Tushare fetch/backfill job 时才允许联网写湖 |
| SM-10 | 生产级因子研究准入 | 检查 CR-011 新版因子研究输入的 data readiness / gate result | `hs300_index`、PIT universe、tradability、clean execution feed、adjustment、industry/market cap/style、liquidity/capacity/cost、factor audit panel、robust validation 和 credential boundary 均返回 `available/pass`，或返回机器可解析 `required_missing/blocked_claims`，不得静默降级 |
| SM-11 | 因子审计面板完整性 | 检查新版报告对应的 factor panel 落盘字段和覆盖统计 | 每个进入实验 17-21 的因子至少保留 `raw`、`directional`、`winsorized`、`zscore` 四层取值及 preprocessing metadata，覆盖股票/交易日数量与剔除原因可复核 |
| SM-12 | 稳健性验证覆盖 | 检查 rolling walk-forward、年度分层、市场状态分段、参数敏感性和成本敏感性输出 | 新版报告不得只给单一区间单一参数结论；至少输出年度、rolling、市场状态、参数网格和成本网格五类分层结果及 pass/warn/fail 状态 |
| SM-13 | 真实数据授权与凭据边界 | 检查默认测试、dry-run、真实执行报告和日志 | 未获显式授权时真实联网、真实 lake 写入、旧 `data/**` 操作和凭据读取均为 0；获授权执行时报告只记录环境变量名、source/interface、run_id、相对路径或脱敏 root label，不记录 token、用户名、密码、`.env` 内容或真实私有路径 |
| SM-14 | 全 A since-inception current truth 可声明性 | 检查 CR-014 readiness summary、dataset matrix、catalog current pointer 和 allowed_claims / blocked_claims | 每个发布为 current truth 的 P0 dataset 都必须给出全 A 证券自存在 / 上市日起至当前交易日的 coverage numerator / denominator、缺口清单、quality/readiness 状态和 source lineage；任一 P0 gate 未通过时不得声明全历史生产级可用 |
| SM-15 | 证券生命周期覆盖 | 检查 universe / lifecycle audit 输出 | 上市、暂停上市、退市 / 摘牌、代码变更、简称变更、交易所 / 板块迁移等生命周期事件均必须有可追溯字段或 `required_missing`，不得把固定快照或当前状态伪装为历史 PIT universe |
| SM-16 | P0 分层与 current pointer 可审计 | 检查 raw / manifest / canonical / gold / quality / catalog 产物和 publish gate | `validate` 结果自动成为 current truth 的次数为 0；只有显式 publish 后 catalog current pointer 才指向最新可读版本，且每个 pointer 可回溯 run_id、batch_id、lineage checksum 和 quality report |
| SM-17 | 增量刷新与重放稳定性 | 检查计划、增量运行和 replay 记录 | 未授权真实执行时 provider fetch、lake write、credential read、legacy data read、old report overwrite 计数均为 0；获授权后增量刷新默认只补缺口 / 最近 N 个交易日回补，replay 不触发 provider，重复 run 不污染 current pointer |
| SM-18 | DuckDB 候选边界可验证 | 检查 HLD 待决策项、默认依赖状态和只读审计方案 | DuckDB 在需求阶段只作为 read-only query / audit / feature extraction 候选能力；`pyproject.toml` / `uv.lock` 未经 CP3/CP5 批准不新增 DuckDB；若后续采用，默认只能只读 Parquet / catalog，不替代 source-of-truth lake |
| SM-19 | QMT foundation 安全边界 | 检查 OMS、QMT adapter、pre-trade risk、broker lake 和默认运行模式 | CR-015 默认仅允许 shadow / dry-run / mock；真实 `order_stock`、撤单和账户写操作次数为 0；策略层直接调用 QMT API 次数为 0 |
| SM-20 | OMS 状态机与 broker lake 可审计 | 使用 partial fill、cancel、reject、unknown、timeout 等样例验证状态迁移和审计输出 | 每个 order intent / broker order / fill / position / asset / error / reconciliation event 均可追溯 run_id、strategy_id、research_adjustment_policy、execution_price_policy、状态、时间戳和脱敏 broker 元数据 |
| SM-21 | 复权双视图与收益入口可验证 | 检查 `prices_raw`、`adj_factor`、`prices_qfq`、`prices_hfq`、`returns_adjusted` 和 quality / lineage metadata | raw 与 adj_factor 作为事实源；qfq/hfq/returns_adjusted 独立派生；qfq 记录 `as_of_trade_date`；同一研究 run 只能使用一个明确口径 |
| SM-22 | QMT raw 执行价格隔离 | 检查 order intent、委托、成交、对账和报告 metadata | 任一真实或模拟 QMT 委托价、成交价和 broker 对账价均使用 raw / broker price；qfq/hfq 只能作为研究口径记录，不得作为执行价 |
| SM-23 | QMT 阶段激活门控 | 检查 shadow、模拟盘、实盘只读、小资金实盘、资金放大五阶段 gate 记录 | 阶段顺序不可跳过；每一阶段必须输出准入、退出、回滚和阻断原因；CR-017 未完成前不得声明生产策略复权治理完成或进入资金放大 |
| SM-24 | 运行治理与人工授权 | 检查 runbook、对账、kill switch、暂停 / 恢复 / 手工接管和 per-run 授权记录 | 模拟盘前存在 runbook；盘前 / 盘中 / 盘后对账有结构化报告；kill switch 可阻断新单、撤可撤单、冻结策略并记录人工接管；任何真实 QMT 操作均需 per-run 授权 |
| SM-25 | 数据湖 production current truth 闭环 | 检查 published release、catalog current pointer、quality/readiness、rollback 和 release summary | 只有 Explicit Publish Gate 可以更新 current pointer；发布记录必须包含 `release_id`、dataset 清单、`release_scope`、`as_of_trade_date`、source run ids、quality 结果、blocked claims、rollback target、approver 和 approved_at |
| SM-26 | Published truth 研究重跑与 QMT 后置 | 检查 published release 后的阶段三到阶段五核心研究重跑报告和 QMT stage gate | 数据湖未 publish 或生产口径研究重跑未通过时，QMT simulation / live_readonly / small_live / scale_up 必须返回 blocked；通过后才允许另行申请 QMT 阶段解禁 |
| SM-27 | 阶段六多因子模拟盘准入闭环 | 检查实验 49-66、admission package、gate result 和 blocked claims | 数据、因子、策略、交易现实性、成本、benchmark、稳健性、消融、冻结、pre-sim、5 日 dry-run 和 admission package 均 PASS，或输出机器可解析 blocked reason；不得把旧失败策略包装为可申请模拟盘 |
| SM-28 | 5 日 dry-run 安全性 | 检查连续 5 个真实交易日 dry-run 输出、runbook 和安全计数 | 每个交易日输出 signal、target、order_plan、risk、log 和 no-real-op 证据；真实订单、撤单、账户查询、凭据读取、真实 provider fetch、真实 lake/report/delivery 写入计数均为 0 |
| SM-29 | QMT gateway 完整接口面与运行门控 | 检查 Windows QMT FastAPI gateway 的 endpoint matrix、run mode、stage gate、risk gate 和 no-real-op 计数 | Gateway 必须暴露完整 QMT 功能接口类别；未满足 run mode / stage gate / risk gate / kill-switch / 必要上下文时，simulation / live / account / cancel / query 等真实转发均返回 blocked，真实 QMT 调用计数为 0 |
| SM-30 | QMT C/S 模块部署边界 | 检查 C 侧 local_backtest client、S 侧 Windows gateway、绑定地址、防火墙、可选鉴权、heartbeat、部署责任和 fallback 设计 | C 侧不得导入 xtquant，只通过 REST 调用 S 侧；S 侧作为 Windows 可运行 / 可安装命令部署并转换为 QMT 接口调用；服务禁止默认暴露到公网或不受控局域网 |
| SM-31 | 后置能力边界可验证 | 检查 Backtrader、Qlib、分钟数据和 QMT Level2 的触发条件 | 四类能力均不得作为阶段六 P0 或模拟盘准入前置；只有达到 UC-18 的触发条件并经后续 CR / CP 门控后才允许纳入实现范围 |
| SM-32 | 日志脱敏与禁止真实操作默认值 | 检查 QMT C/S bridge、dry-run、fallback 和 admission 日志 | 日志不得包含 token、账户敏感信息、`.env` 内容或真实私有路径；未授权阶段 `qmt_api_call`、`real_order`、`account_query`、`credential_read`、`provider_fetch`、`lake_write`、`reports_write`、`delivery_write` 均为 0 |
| SM-33 | CR-025 轻量主路径保持默认 | 检查默认配置、未安装 Backtrader、显式选择 Backtrader 三类运行入口 | 默认运行仍走 lightweight engine；Backtrader 只有显式选择时进入 optional backend；未选择或未安装时轻量主路径可运行且结果不变 |
| SM-34 | CR-025 依赖隔离与 lazy import | 检查静态导入、依赖文件、未安装环境和测试入口 | CP5 前 `pyproject.toml` / `uv.lock` 不新增 Backtrader；未安装 Backtrader 时导入主包、轻量回测、数据读取和默认测试不失败；只有 optional backend 路径触发 lazy import |
| SM-35 | CR-025 clean feed 准入 | 检查 feed schema、PIT / `available_at`、复权口径、benchmark、tradability、cost 和 quality gate | 输入不满足 clean feed 契约时返回结构化 unavailable / blocked reason；不得由 Backtrader 生成 PIT、计算复权因子、联网补数或绕过 quality gate |
| SM-36 | CR-025 执行语义差异可解释 | 比较 lightweight engine 与 Backtrader optional backend 在同一 clean feed、同一候选策略、同一成本配置下的输出 | 对照报告至少列出调仓日、目标权重 / 下单量、成交价格、现金、手续费、滑点、税费、净值和差异原因；差异不得被静默当作 bug 或 truth 替代 |
| SM-37 | CR-025 无真实操作安全边界 | 检查 optional backend 执行期间的 broker、QMT、provider、lake、publish 和凭据计数 | `real_broker_calls=0`、`qmt_api_call=0`、`provider_fetch=0`、`lake_write=0`、`catalog_publish=0`、`credential_read=0`；Backtrader 不接入真实 broker、simulation、live 或 QMT |
| SM-38 | CR-025 三条主线映射清晰 | 检查 CP2 / tracking / HLD 输入是否同时覆盖研究可信度、回测 / 模拟一致性、QMT 生产执行 | CR-025 明确归属回测 / 模拟一致性主线，并列出与研究可信度和 QMT 生产执行主线的接口；不得只呈现 Backtrader 单点路线 |
| SM-39 | 研究输出到 order intent 衔接可审计 | 检查研究报告、lightweight baseline、Backtrader semantic diff 和 QMT OMS 输入字段 | target portfolio / order intent draft 至少包含 strategy_id、run_id、signal_date、target_trade_date、symbol、target_weight 或 target_qty、research_adjustment_policy、execution_price_policy、cost_config_ref、data_lineage_ref 和 limitations |
| SM-40 | CR-025 不扩大为框架工程或真实运行 | 检查 HLD/LLD/Story/文档范围 | 不复制 / 移植 Backtrader 源码，不自研完整事件驱动交易框架，不把 CR-025 approve 解释为 gateway 启动、simulation、live-readonly、small-live、scale-up 或任何真实账户操作授权 |
| SM-41 | Backtrader 本地项目分析完整 | 检查 CR-025 CP3/HLD 的 Backtrader 模块对比表 | HLD 必须读取 `/home/hyde/download/backtrader`，列出 license、模块职责、可借鉴 / 可适配 / 可移植候选 / 禁止移植分类；任何源码级移植候选必须带许可证、维护、回归和授权影响 |
| SM-42 | CR-030 外部多因子项目借鉴矩阵完整 | 检查 CP3/HLD 的外部项目矩阵 | Qlib、Alphalens、vectorbt、PyBroker、bt、Zipline Reloaded、QuantConnect LEAN、RQAlpha、vn.py / vnpy.alpha、Backtrader 至少 10 类候选均有 `reference_only` / `optional_spike` / `exclude` / `forbidden_migration` 分类、许可证 / 依赖 / 数据入口 / 运行授权边界和切换条件 |
| SM-43 | 项目自有多因子契约可冻结 | 检查 HLD/LLD 中的字段字典和 schema gate | `FactorSpec`、`FactorRunSpec`、`FactorPanelContract`、`LabelWindowSpec`、`FactorEvaluationReport`、`MultiFactorPortfolioPlan`、`ExperimentManifest`、`StrategyAdmissionPackage` 均给出必填字段、校验规则、错误码、失败策略和外部项目映射；不得直接采用外部框架对象作为内部 truth |
| SM-44 | schema 与校验不是从零设计 | 检查 CP3/HLD 的 schema provenance 和校验策略 | HLD 必须以 `research_input_v1`、实验 17-21 `FactorDefinition`、CR-011 factor panel audit、label window gate、Stage6 admission gate 为基线，并用 Qlib / Alphalens / Zipline / LEAN 做 cross-check；缺字段、前视风险或 lineage 不完整时 fail-closed |
| SM-45 | 因子面板和标签窗口防泄漏 | 检查 fixture、字段字典和 leakage audit 输出 | 每个因子值、标签、收益窗口和组合输入必须携带 `trade_date`、`symbol`、`available_at`、`decision_time`、`label_window_start/end`、`label_available_at` 和 data_lineage；任何 `available_at > decision_time` 或 label overlap 风险必须阻断 |
| SM-46 | 单因子评价可复查 | 检查 factor evaluation report | 每个候选因子至少输出覆盖率、IC、RankIC、ICIR、分层收益、多空收益、换手、成本敏感性、行业 / 市值 / 风格暴露、blocked claims 和年度 / rolling 分层状态 |
| SM-47 | 多因子组合构建边界清晰 | 检查 HLD 的 combiner / portfolio plan | 多因子组合必须说明标准化、winsorization、中性化、正交化、权重学习 / 规则权重、约束、benchmark、成本、容量、调仓频率和冻结策略；P0 不引入未批准外部 optimizer |
| SM-48 | 实验追踪和报告 catalog 可审计 | 检查 `ExperimentManifest` 与 report catalog 设计 | 每个研究 run 必须记录配置哈希、输入 dataset/release、因子版本、标签窗口、评估窗口、成本配置、随机种子、代码版本、报告路径和 allowed / blocked claims，支持复跑与差异解释 |
| SM-49 | 策略准入包不等于交易授权 | 检查 `StrategyAdmissionPackage`、Stage6 gate 和 QMT handoff | CR-030 只能输出可审计准入证据、blocked reasons 和 `order_intent_draft_v1` 草稿；`qmt_api_call`、`real_order`、`account_query`、`provider_fetch`、`lake_write`、`catalog_publish`、`credential_read` 均为 0，任何 QMT/simulation/live 仍由 CR-020..CR-024 单独授权 |

## 明确排除（Out of Scope）

- 第一版不模拟涨跌停、停牌、真实成交量约束和分钟级撮合。
- 第一版不精确建模完整停牌状态、涨跌停撮合、新股上市初期特殊规则、退市整理与摘牌、ST 历史状态、财报披露日和沪深 300 历史成分变化；报告 metadata 必须逐项警示这些限制。
- 第一版不处理沪深 300 历史成分股变化；使用固定当前沪深 300 成分股快照，并在报告中明确标记非 PIT、快照日期和幸存者偏差。
- 第一版不追求与聚宽逐日净值 100% 一致。
- 第一版不自动调用聚宽、不自动轮询聚宽回测结果、不要求联网运行回测主路径。
- 第一版回测、参数扫描、候选筛选和本地差异分析主路径不得联网；联网能力只能存在于独立数据准备/更新流程。
- 第一版不建设完整交易系统、订单簿、实盘接口或聚宽 API 兼容层。
- 第一版不默认引入 RQAlpha、Backtrader、vectorbt 或 bt 作为主框架。
- 第一版不把财报披露日、公告事件或其他事件数据作为策略信号输入；若后续引入事件字段，必须提供 `available_at` 并通过未来函数校验。
- CR-005 不允许把 Tushare API 直接接入 `engine/data_loader.py`、实验入口、benchmark resolver 或 Backtrader adapter；“数据层调用 Tushare”仅指 `market_data` 写湖 / 数据准备层在用户显式命令下调用 Tushare 并写入本地 raw / manifest / canonical / quality / catalog / gold 链路。
- CR-005 不允许用旧等权买入持有或同股票池代理填充 `hs300_index` benchmark 字段；如保留代理，只能命名为 `proxy_baseline`，不得声明为沪深 300 相对收益。
- CR-011 不覆盖或改写实验 17-21 既有报告；旧报告继续作为 fixed-snapshot / proxy-baseline / close-proxy 探索基线，新版生产级验证必须输出到版本化报告或新目录。
- CR-011 需求/场景增量阶段不授权真实联网、真实抓取、真实 lake 写入、旧 `data/**` 迁移/删除或凭据读取；真实执行只能在后续 Story 经 CP5 批次确认并获得用户显式授权后进行。
- CR-011 不默认声明 2005 年以来完整 PIT 历史、全市场长期覆盖、实盘可成交或生产 current truth；只能按 quality/readiness 通过的窗口和数据集声明 `production_strict_research`。
- CR-014 需求/场景增量阶段不执行 provider fetch、不读取凭据、不写真实 lake、不读取 / 列出 / 迁移 / 复制 / 比对 / 删除旧 `data/**`，也不覆盖旧 reports。
- CR-014 不在需求阶段承诺引入 DuckDB 依赖；DuckDB 仅作为后续 HLD/CP3/CP5 待决策的只读 query / audit / feature extraction 候选能力。
- CR-014 不用 DuckDB `.duckdb` 文件替代 Parquet lake、catalog/manifest 或 publish current pointer 的事实源地位。
- CR-014 不把 CR-010 / CR-012 limited-window pass、CR-013 roadmap 或任何未通过全历史审计的结果外推为 A 股 since-inception production current truth。
- CR-015 不授权真实 QMT 下单、撤单、账户写操作、账户凭据读取、实盘依赖引入或真实 broker lake 写入；默认仅做 shadow / dry-run / mock foundation 场景和需求。
- CR-015 初期不支持信用账户、多资产、期货、期权或完整第三方交易平台迁移；普通股票现金账户之外的订单规则、保证金和对账另行决策。
- CR-015 / CR-016 不允许策略层直接调用 QMT / XtQuant API；策略目标组合必须通过 OMS、pre-trade hard risk gate 和 QMT adapter。
- CR-016 不授权无 per-run 审批的模拟盘 / 实盘订单提交、撤单、账户查询、账户写操作或资金放大；不得跳过 shadow、模拟盘、实盘只读、小资金实盘的阶段门控。
- CR-016 不因 QMT 接入而解除真实 VWAP、minute、tick、level2、order-match、微观结构冲击成本或完整真实撮合执行价的 blocked claim。
- CR-017 不在本阶段修改代码、引入依赖、真实抓取、真实写湖、发布 `current` pointer、批量重算 / 覆盖旧 qfq 数据或声明完整公司行动链路可审计。
- CR-017 不允许把 qfq/hfq 复权价作为 QMT 委托价、成交价、成交核算或 broker 对账价；真实交易执行只能使用 raw / broker price。
- CR-018 不把 CR014 S14 `prices` / `adj_factor` candidate 直接发布为 production current truth；candidate 只能作为后续 PIT/W3/benchmark/quality/publish gate 的输入事实。
- CR-018 在 CP5 和单次真实运行授权前不执行新增 provider fetch、不读取或输出 `.env` / token / 凭据、不写真实 lake、不更新 catalog current pointer、不执行 DuckDB 持久事实源写入、不启动 QMT simulation / live 操作。
- CR-019 requirement-clarification / CP2 准备阶段不实现 FastAPI 服务、不新增依赖、不启动本地服务、不调用真实 QMT / MiniQMT / XtQuant、不读取凭据、不执行真实 provider fetch、不写真实 data / reports / delivery。
- CR-019 不把 FastAPI 服务存在、health pass 或 dry-run pass 等同于 QMT simulation 授权；simulation submit / cancel、账户 snapshot、reconciliation 和 kill-switch endpoint 必须 later-gated。
- CR-019 signed file drop 仅保留为 fallback；fallback 只能产生 dry-run 文件交换或 blocked result，不得自动改走真实 QMT 操作。
- CR-019 不把 Backtrader、Qlib、分钟数据或 QMT Level2 作为阶段六 P0；这些能力只在触发条件满足后通过后续 CR / CP 门控进入。
- CR-019 读取的 QMT 系统说明文档仅作为能力背景，不得推断当前项目已具备真实账户、模拟盘、Level2 或任一交易权限。
- CR-025 CP2 前只做场景 / 需求 / 检查 / 交接，不实现代码、不新增 Backtrader 依赖、不修改 `pyproject.toml` / `uv.lock`、不运行 Backtrader。
- CR-025 不把 Backtrader 设为默认主路径、默认依赖、生产 truth、阶段六 P0 或 QMT simulation 前置条件；轻量 engine 继续作为主路径。
- CR-025 不复制、裁剪或移植 Backtrader 源码，不自研完整事件驱动交易框架，不把当前任务扩大为完整交易平台迁移。
- CR-025 不接入 Backtrader live broker、store、真实 broker、QMT / MiniQMT / XtQuant、simulation、live、account query、cancel 或 order submit。
- CR-025 不直接启动 QMT gateway、绑定端口、接入 simulation / live-readonly / small-live / scale-up；这些必须由 CR-020..CR-024 单独启动和授权。
- CR-025 不触发 provider fetch、真实 lake write、broker lake write、catalog publish、报告覆盖、凭据读取或任何真实数据 / 真实账户操作。
- CR-025 不用 Backtrader 生成 PIT universe、复权因子、benchmark、可交易性事实或 quality status；这些只能来自已确认的本地数据 / 数据湖契约。
- CR-030 CP2 / CP3 阶段不实现代码、不新增依赖、不修改 `pyproject.toml` / `uv.lock`、不运行 Qlib / Alphalens / vectorbt / PyBroker / bt / Zipline Reloaded / QuantConnect LEAN / RQAlpha / vn.py / Backtrader 或其他外部项目。
- CR-030 不把 Qlib 或任何外部项目作为默认框架、事实源、provider、runner、optimizer、report truth 或策略准入 truth；外部项目只能作为静态架构参考或后续独立 Spike 候选。
- CR-030 不复制、裁剪、改写或源码级迁移外部项目代码、样例、测试、数据或 license-bound runtime；任何源码级移植候选必须另列 CP3 决策项并在 CP5 前取得实现授权。
- CR-030 不授权 provider fetch、真实联网补数、真实 lake write、catalog publish、broker lake write、报告覆盖、凭据读取、QMT / MiniQMT / XtQuant、simulation、live_readonly、small_live、scale_up、发单、撤单或账户查询。
- CR-030 不把因子评价、回测报告、组合方案或 `StrategyAdmissionPackage` 自动解释为可交易、QMT-ready、simulation-ready 或 production truth；真实执行交接必须由 Stage6 gate 和 CR-020..CR-024 单独控制。
- CR-030 不从零发明 schema；多因子 schema 和校验必须以本项目已有 `research_input_v1`、实验 17-21 `FactorDefinition`、CR-011 factor panel audit、label window gate 与 Stage6 admission gate 为基线，再用外部项目 cross-check。

## 边界说明

| 边界 | 第一版处理方式 | 不包含内容 |
|---|---|---|
| 本地回测主路径 | 只读当前仓库根下标准化 parquet、manifest 和必要 metadata，生成本地报告和候选清单；断网环境必须可运行 | 不在回测、扫描、候选筛选或差异分析过程中联网拉取数据 |
| 数据准备 | AKShare 等数据源拉取只能作为独立数据准备/更新流程；该流程负责请求节流、有限重试退避、断点续传、raw 缓存、标准化 parquet 派生、manifest 和质量报告 | 不把实时接口可用性作为回测器运行前提；不允许回测引擎直接调用 AKShare、聚宽或其他远程接口 |
| 数据更新周期 | 默认按缺口增量更新，并支持最近 N 个交易日可配置回补，用于处理数据迟到、复权修正或接口补发 | 不默认重复全量抓取；除显式强制刷新或回补窗口外，不重复请求已成功批次 |
| 聚宽验证 | 用户手动将不超过 4 组候选参数回填聚宽，并比较方向一致性 | 不自动提交、调度或抓取聚宽任务 |
| 平台任务减少 | 本地完成 60 组扫描，只把候选参数送平台验证 | 不在平台执行完整参数网格 |
| 复权口径 | 同一次回测、扫描、候选报告和聚宽差异分析必须使用一致复权口径；默认口径在 HLD 前确认，报告 metadata 必须记录实际口径 | 不允许在信号、成交、指标或报告中混用不同复权口径 |
| 数据可用时点 | 所有参与决策的数据必须满足 `available_at <= decision_time`；日线收盘价按 T 日收盘后可用生成信号，成交只能发生在 T+1 或之后 | 不允许使用决策时点尚不可得的数据，不允许隐式未来补值 |
| 缺失与无成交 | 历史窗口不足、缺失动量、缺失成交价或无成交必须剔除、留现金、记录失败或显式警示 | 不静默填充价格，不把不可交易目标当作已成交 |
| 股票池偏差 | 第一版使用固定当前沪深 300 成分股快照，并标记 `is_pit_universe=false` | 不做历史成分股点时还原，报告必须提示幸存者偏差 |
| 报告限制项 | 单次回测、扫描和候选报告必须输出 metadata 限制项，覆盖非 PIT 股票池、幸存者偏差、停牌、涨跌停、新股、退市、ST、财报披露日和历史成分变化限制 | 不允许只在 README 或口头说明中披露限制 |
| 失败降级 | 数据源不可用或数据准备部分失败时，若本地标准化 parquet 覆盖区间和 schema 合规，回测、扫描和候选筛选继续离线运行，并在报告或质量报告披露数据新鲜度、失败项和风险 | 不因远程接口临时不可用阻塞已缓存数据上的研究运行；不隐藏失败批次或陈旧数据风险 |
| 本地 benchmark 消费 | 实验十/十二、轻量回测、benchmark resolver 和 Backtrader optional backend 只能只读本地 `hs300_index` canonical/gold、quality 和 catalog；缺失或质量不通过时返回 typed `available` / `unavailable` / `required_missing` 结果 | 不在消费调用栈内联网、不导入 connector/runtime/storage、不读取 `TUSHARE_TOKEN`、不自动以代理基准替代 `hs300_index` |
| Tushare 写湖补齐 | 用户显式执行 `market_data` 数据准备 / 写湖作业时，才允许按 allowlist、token、批次、日期范围和 lake root 调用 Tushare，生成 raw、manifest、canonical/gold、quality 和 catalog | 不由 `engine/data_loader.py`、实验入口、benchmark resolver 或 Backtrader 自动触发；不提交 token 或真实私有数据 |
| Backtrader optional backend | 作为后置可选后端，只消费已通过 PIT、复权和 quality gate 的本地 feed；未安装或数据不合规时结构化不可用，轻量主路径继续可运行 | 不替代 `engine/backtest.py` 主路径；不生成 PIT、不计算复权因子、不绕过 quality gate、不联网 |
| CR-011 生产级因子研究数据补齐 | 在不覆盖实验 17-21 旧报告的前提下，使用 CR-010 数据湖 current truth 和 CR-008 `research_input_v1` 合同，补齐真实 benchmark、PIT universe、可交易性、执行价、复权/公司行动、行业市值风格、流动性容量成本、因子审计面板和稳健性验证 | 不在需求/场景阶段执行真实联网或写 lake；不把缺失数据静默降级为生产级结论；不打印、记录或保存任何凭据值 |
| CR-014 A 股全历史生产数据湖 | 目标是将数据湖目标扩展为全 A 股证券自存在 / 上市日起至当前交易日的 production current truth；必须保留 P0 dataset 分层、证券生命周期、catalog current pointer、增量刷新、replay、claim boundary 和只读查询审计候选边界 | 本阶段不执行真实 provider fetch、真实 lake 写入、凭据读取、旧 `data/**` 操作、旧报告覆盖或 DuckDB 依赖引入；不把 DuckDB 作为事实源替代 Parquet lake / catalog / manifest |
| CR-017 复权双视图 | `prices_raw` 与 `adj_factor` 作为事实源，独立派生 `prices_qfq`、`prices_hfq` 和 `returns_adjusted`；研究 run 必须显式选择单一 `research_adjustment_policy`，qfq 必须记录 `as_of_trade_date` | 不同复权口径不得在同一 frame / run 混用；不覆盖旧 qfq 基线；不在未授权情况下真实抓取、写湖、发布 current pointer 或迁移旧数据 |
| CR-015 QMT foundation | 通过 Windows QMT / MiniQMT 节点、XtQuant 外部 Python API、OMS 和 QMT adapter 承接目标组合到订单意图；pre-trade risk 失败必须 hard block；broker lake 外置且审计可追溯 | 策略层不直接调用 QMT API；默认仅 shadow / dry-run / mock；不得读取或输出凭据、账户号、session、cookie 或交易密码；不得把 broker lake 写入仓库 `data/**` / `reports/**` |
| CR-016 QMT 激活治理 | 按 `shadow -> QMT 模拟盘 -> 实盘只读 -> 小资金实盘 -> 放大资金` 分阶段推进；T 日收盘后信号、T+1 限价 / 保护价执行；必须有 runbook、对账、kill switch 和 per-run 授权 | 不得直接从模拟盘跳到放大资金；CR-017 不阻断技术模拟盘，但阻断生产策略复权治理声明和资金放大；无授权时真实 QMT API 操作计数必须为 0 |
| CR-018 数据湖 production closure | 以 CR014 S14 candidate 为输入，补齐 production current truth 所需的 PIT universe / lifecycle / code-change、ST / suspend / trade_status / prices_limit、真实 benchmark 行情 / 成分 / 权重、复权派生、quality/readiness、Explicit Publish Gate、rollback、发布后研究重跑和 QMT 后置门控 | 不把 candidate、validate PASS 或 parity PASS 自动视为 current truth；不在 publish + 研究重跑通过前解禁 QMT simulation / live_readonly / small_live / scale_up；行业 / 市值 / 流动性若列为 P1，则阻断中性化、容量和资金放大声明 |
| CR-019 阶段六多因子模拟盘准入 | 目标是重新制定可通过 production current truth、因子、策略、交易现实性、成本、benchmark、稳健性、消融、冻结、pre-sim 和 5 日 dry-run 的 A 股多因子准入链路 | 不把既有失败多因子 / 低波结果包装为模拟盘可申请；不在 admission package 和 stage gate 通过前申请 QMT simulation |
| CR-019 QMT C/S 模块 | QMT 模块拆成 C/S 两部分：C 侧位于 local_backtest，向框架暴露统一 Python client / 函数接口并可提供薄 CLI；S 侧部署在 Windows QMT 节点，作为可运行 / 可安装的 FastAPI gateway，通过 REST 接收 C 侧请求并转换为 QMT / XtQuant 接口调用 | Gateway 完整支持 QMT 功能接口类别不等于真实操作自动授权；C 侧不得直接依赖 xtquant；S 侧不默认暴露到公网或不受控局域网 |
| CR-019 dry-run / readonly / simulation-gated | `/health`、`/capabilities`、`/intents/validate`、`/dry-run/orders` 可作为第一版合同；真实 simulation submit / cancel、账户 snapshot、reconciliation、kill-switch 均需 CR016 stage gate、per-run authorization 和后续实现门控 | 不允许缺少 per-run 授权字段时触达真实 QMT；不允许 capability 发现结果自动升级为操作权限 |
| CR-019 fallback 与后置能力 | signed file drop 作为 FastAPI 不可达、鉴权失败或部署受限时的 fallback；Backtrader、Qlib、分钟数据、Level2 均按触发条件后置 | fallback 不能自动真实下单；Backtrader/Qlib 不接管事实源或默认依赖；分钟 / Level2 不用于阶段六 P0 准入 |
| CR-025 research execution semantic alignment | Backtrader 从 CR-019 deferred capability 转为正式研究路线 CR，但只作为显式选择的 optional execution realism / semantic reference；输入必须是本地 clean feed，输出必须是与 lightweight engine 的执行语义差异报告、结构化可用性状态和 target portfolio / order intent draft | 不替代 lightweight 主路径；不默认安装或导入；不复制 / 移植 Backtrader 源码；不自研完整事件驱动交易框架；不接真实 broker / QMT；不联网、不写湖、不 publish、不读取凭据；CP5 前不得实现或修改依赖 |

## 治理附录（Governance）

| 字段 | 当前值 | 说明 |
|---|---|---|
| `engagement_mode` | production | 面向目标产物的生产模式 |
| `scenario_subject_type` | target-artifact | 场景主体是本地日频回测工具，而不是元工作流自身 |
| `scenario_subject_id` | local-backtest-production-data-lake-and-qmt-trading-layer | 当前场景主体已从本地研究工具 / 生产级数据湖扩展到 QMT 交易接入 companion 层，但仍服务目标产物而非 meta-flow 自身 |
| `target_artifact_type` | tool | 目标交付是本地 Python 研究工具 / 回测层 |
| `governance_mode` | review-gated | 需求、HLD、Story 计划和 LLD 需要按项目检查点确认 |
| `review_policy` | strict | CR-014 / CR-015 / CR-016 / CR-017 命中生产数据湖、交易接口、凭据、外部节点、订单状态机、复权事实源、权限和多 Story 依赖，采用严格评审 |

## 使用场景列表

### UC-01：准备本地缓存行情并加载研究数据

| 字段 | 内容 |
|---|---|
| **使用角色** | P-01 量化策略学习者 / 研究者 |
| **触发条件** | 用户准备首次构造本地研究数据、更新已有缓存，或准备运行本地回测/参数扫描。 |
| **输入** | 数据准备流程输入：数据源配置、接口名、股票/日期范围、请求参数、`request_interval_seconds`、`batch_size`、`max_concurrency`、`max_retries`、`backoff_policy`、断点续传 manifest/checkpoint、增量更新范围、最近 N 个交易日回补配置和强制刷新开关。回测加载流程输入：当前仓库根下的 `data/prices.parquet`、`data/index_members.parquet`、`data/trade_calendar.parquet`、manifest 和质量报告；参与决策字段必须具备 `available_at` 或可审计的可用时点推导规则，价格数据必须具备一致复权口径元数据。 |
| **处理逻辑** | Given 用户执行独立数据准备/更新流程，When 需要访问 AKShare 等远程数据源，Then 系统按默认保守串行方式分批请求，保证相邻请求时间间隔不小于 `request_interval_seconds`，并按 `batch_size`、`max_concurrency` 控制压力；网络失败、限流或临时服务错误必须在 `max_retries` 上限内按 `backoff_policy` 退避，退避过程进入 manifest 或日志；成功批次写入 raw 缓存，标准化 parquet 从 raw 派生，manifest/checkpoint 记录批次状态，质量报告记录覆盖、缺失、失败、重复、异常价格、回补数量和数据新鲜度。Given 本地 parquet 文件存在，When 用户加载指定区间和股票池，Then 系统返回按交易日对齐的 `close_df`、固定股票池和交易日序列；若文件缺失、schema 不满足契约、复权口径混用、`available_at > decision_time`、缺失价格或无成交状态无法被显式处理，则给出明确错误或记录限制，而不是联网隐式拉取或静默填充。 |
| **输出/结果** | 数据准备流程输出 raw 缓存、标准化 parquet、manifest/checkpoint、数据质量报告和失败项清单；回测加载流程输出可供策略层使用的价格矩阵、股票池快照、交易日序列、复权口径、数据可用时点规则、覆盖区间、数据新鲜度和数据偏差标记。 |
| **前置条件** | 联网数据准备/更新流程与回测/扫描主路径物理隔离；第一版回测主路径离线只读标准化 parquet、manifest 和必要 metadata。 |
| **排除情况** | 第一版不在回测、扫描、候选筛选或差异分析过程中联网；不允许无限重试或高频压测数据源；不精确处理完整停牌状态、涨跌停撮合、历史成分股切换、新股上市初期特殊规则、退市整理与摘牌、ST 历史状态、财报披露日和复权因子自动校正；这些限制必须进入报告 metadata 或质量报告。 |

**处理流程（文字描述）：**
1. 若执行数据准备/更新流程，读取数据源、接口、股票/日期范围和限速配置，按 `request_interval_seconds`、`batch_size`、`max_concurrency` 进行保守分批请求。
2. 对网络失败、限流或临时服务错误执行有限次数重试与退避；超过 `max_retries` 后记录失败项，不进入无限循环。
3. 将成功获取的原始响应或原始表格写入 raw 缓存，并从 raw 缓存派生标准化 parquet。
4. 用 manifest/checkpoint 记录批次、数据源、接口、请求参数、股票/日期范围、请求时间、成功项、失败项、错误信息、重试次数、raw 路径、标准化输出路径、覆盖范围和最终状态。
5. 默认执行增量更新，只补缺失 symbol/date 或缺失日期；最近 N 个交易日回补基于交易日历而不是自然日，除显式强制刷新外不重复已成功批次。
6. 生成数据质量报告，记录覆盖区间、缺失统计、失败统计、失败 symbol/date、字段缺失、重复记录、异常价格、回补数量、最近成功更新时间和数据新鲜度。
7. 若执行回测加载流程，校验数据文件是否存在且字段满足最小 parquet schema；该流程不得联网。
8. 校验同一运行内复权口径一致，并确认参与决策字段的 `available_at` 不晚于对应 `decision_time`。
9. 读取 parquet 并按交易日、证券代码对齐，不对缺失价格或无成交记录做静默填充。
10. 返回策略计算所需的收盘价矩阵、固定股票池和交易日序列。
11. 在输出元数据中标记固定当前沪深 300 股票池、`is_pit_universe=false`、快照日期、幸存者偏差、数据新鲜度和第一版未建模限制。

---

### UC-02：运行实践六动量策略的本地日频回测

| 字段 | 内容 |
|---|---|
| **使用角色** | P-01 量化策略学习者 / 研究者 |
| **触发条件** | 用户希望在本地复现“实践六”动量策略的核心规则，不再为每次实验提交聚宽任务。 |
| **输入** | 回测起止日期、`lookback_days`、单次参数 `rebalance_freq`、`top_fraction`、`sell_buffer`、交易成本参数、初始资金和本地 parquet 数据。 |
| **处理逻辑** | Given 已加载价格和交易日历，When 到达每 N 个交易日的信号日 T，Then 系统在 T 日收盘后用截至 T 日收盘且 `available_at <= decision_time` 的历史价格计算动量排名，选前 `top_fraction`，保留仍在 `sell_buffer` 内的持仓，并生成等权目标组合；成交只能发生在 T+1 或之后。动量公式为 `close[T] / close[T-lookback_days] - 1`，历史窗口不足、任一端点价格缺失或不可用的股票必须剔除，不得参与排名。 |
| **输出/结果** | 日净值曲线、持仓变化、交易成本、核心绩效指标、复权口径、信号/成交时点、缺失数据处理记录和固定股票池偏差提示。 |
| **前置条件** | 已确认无前视偏差的信号日、成交日、收益归属规则和成本扣除规则；默认复权口径与成交假设仍需在 HLD 前确认。 |
| **排除情况** | 不要求与聚宽撮合结果逐日一致；第一版不精确处理完整停牌状态、涨跌停撮合、真实成交量限制、新股上市初期特殊规则、退市整理与摘牌、ST 历史状态和财报披露日。 |

**处理流程（文字描述）：**
1. 遍历交易日并识别信号日 T 与可成交日 T+1 或之后的交易日。
2. T 日收盘后使用满足 `available_at <= decision_time` 的历史窗口计算横截面动量。
3. 剔除历史窗口不足、端点价格缺失、复权口径不一致或不可审计可用时点的股票。
4. 根据排名、缓冲区和当前持仓生成目标权重。
5. 组合层按成交方向、成交基数和扣除时点扣除成本并更新净值；缺失成交价或无成交不得静默填充，未成交目标权重留作现金或记录为未成交。
6. 分析层计算指标，并记录指标假设、限制项和报告 metadata。

---

### UC-03：批量扫描动量策略参数并输出报告

| 字段 | 内容 |
|---|---|
| **使用角色** | P-01 量化策略学习者 / 研究者 |
| **触发条件** | 用户需要快速比较 60 组动量参数。 |
| **输入** | `lookbacks = [5, 10, 20, 30, 60]`、扫描候选列表 `rebalance_freqs = [5, 10, 20, 30]`、`fractions = [0.05, 0.10, 0.20]`，以及固定成本和回测区间。 |
| **处理逻辑** | Given 单次回测函数可重复调用且本地 parquet 覆盖区间和 schema 合规，When 用户执行参数扫描，Then 系统在断网环境下遍历 60 组参数并为每组记录累计收益、年化收益、最大回撤、Sharpe、换手、耗时、复权口径、非 PIT 股票池标记、样本内选择警示、数据新鲜度和第一版限制项；单次回测配置字段使用 `rebalance_freq`，扫描列表字段使用 `rebalance_freqs`。若最近一次数据准备失败但本地缓存仍满足本次扫描范围，扫描继续运行并披露失败项和新鲜度，不触发联网补数。 |
| **输出/结果** | `reports/momentum_param_sweep_local.csv` 及其 metadata，后续可派生热力图、收益排名、Sharpe 排名和最大回撤排名；CSV 是必需输出，热力图和 Notebook 是可选展示，不阻塞第一版验收。扫描报告应引用或携带数据质量报告摘要，包括覆盖区间、缺失统计、失败统计和最近成功更新时间。 |
| **前置条件** | 单次回测结果字段稳定，参数组合可序列化，失败参数组合有明确错误记录策略；数据准备与扫描主路径已隔离，扫描只能读取本地 parquet、manifest 和质量报告。 |
| **排除情况** | 第一版不要求并行扫描；性能优化可在基线跑通后处理；扫描过程不得因发现缺口而直接联网抓取数据。 |

**处理流程（文字描述）：**
1. 构造参数网格。
2. 校验本地 parquet、manifest 和质量报告是否覆盖扫描区间；该校验不得联网。
3. 循环调用本地回测器。
4. 汇总指标、数据新鲜度和限制项并输出 CSV。
5. 记录扫描耗时作为后续优化基线。
6. 生成候选清单 `reports/momentum_candidates_local.csv`，用于聚宽少量验证。

---

### UC-04：将本地候选参数回填到聚宽做最终验证

| 字段 | 内容 |
|---|---|
| **使用角色** | P-02 策略验证者 |
| **触发条件** | 本地参数扫描完成并产生候选参数。 |
| **输入** | 默认参数、本地 Sharpe 最优、本地收益最优、保守低换手参数，共不超过 4 组候选；候选清单来自 `reports/momentum_candidates_local.csv`。 |
| **处理逻辑** | Given 本地报告已按指标排序，When 用户选择候选参数，Then 系统提供可回填聚宽的参数列表、选择理由、策略核心逻辑对照说明和差异分析字段。差异分析至少覆盖候选排序方向、收益/回撤量级、换手特征、复权口径、固定股票池非 PIT 偏差、停牌/涨跌停/成交约束缺失影响、成本口径差异和财报披露日等事件时点限制。 |
| **输出/结果** | 少量候选参数清单，以及本地与聚宽方向一致性差异分析模板；候选报告 metadata 必须带出非 PIT、幸存者偏差和第一版未建模限制项。 |
| **前置条件** | 本地策略核心函数与聚宽策略逻辑保持同一口径：动量收益、前排买入、缓冲持有、等权目标、成本记录可对照。 |
| **排除情况** | 不在本地工具中自动调用聚宽任务或轮询聚宽回测结果；不要求第一版自动联网。 |

**处理流程（文字描述）：**
1. 从本地扫描报告中选择候选。
2. 固化候选参数和选择理由。
3. 输出聚宽回填口径和差异分析字段。
4. 用户手动或后续工具化提交聚宽验证。
5. 将聚宽结果与本地报告做方向一致性解释，不要求逐日净值一致。

---

### UC-05：扩展 RSI、MACD 等指标型策略

| 字段 | 内容 |
|---|---|
| **使用角色** | P-01 量化策略学习者 / 研究者 |
| **触发条件** | 动量策略本地版跑通后，用户希望复用同一研究底座验证 RSI、MACD。 |
| **输入** | 指标参数、价格序列、股票池和回测配置。 |
| **处理逻辑** | Given 回测引擎已将信号层、组合层、分析层分离，When 新增 RSI 或 MACD 策略，Then 只需增加策略核心函数并复用组合净值和指标计算。 |
| **输出/结果** | 可与动量策略横向对比的净值和指标报告。 |
| **前置条件** | 策略接口在 HLD 中明确。 |
| **排除情况** | 第一版初始化不要求实现 RSI/MACD，只预留目录和接口方向。 |

**处理流程（文字描述）：**
1. 复用数据加载和回测配置。
2. 编写新的策略核心函数。
3. 复用组合层与分析层生成报告。

---

### UC-06：逐步补齐更真实的数据和交易约束

| 字段 | 内容 |
|---|---|
| **使用角色** | P-01 量化策略学习者 / 研究者 |
| **触发条件** | 轻量回测器已能稳定跑通，用户需要提高结果真实性。 |
| **输入** | PIT universe provider、交易状态表、涨跌停价格、历史指数成分股、复权因子、成交量数据、事件 `available_at`、raw 缓存、manifest、质量报告和偏差审计配置。 |
| **处理逻辑** | Given 第一版轻量回测器已稳定，When 用户选择补齐某类约束，Then 系统按优先级以增量 Story 增加对应数据字段、交易规则、manifest 字段、质量报告检查和回归验证；后续增强优先级依次为 PIT universe provider、交易状态表、涨跌停约束、事件 `available_at`、偏差审计报告。所有真实性增强仍必须维持数据准备与回测主路径隔离，新增联网数据只能进入独立数据准备流程。 |
| **输出/结果** | 更接近平台回测的本地结果、差异解释、扩展后的 manifest、数据质量报告和偏差审计报告。 |
| **前置条件** | 第一版核心路径已通过验证，且数据源字段、限速策略、raw 到标准化派生链路和 manifest schema 已核验。 |
| **排除情况** | 不一次性重构成完整事件驱动交易系统。 |

**处理流程（文字描述）：**
1. 选择单个真实性约束。
2. 增加数据字段、`available_at` 约束、manifest 字段、质量报告检查和交易规则。
3. 通过独立数据准备流程获取或更新所需 raw 缓存，并从 raw 派生标准化 parquet。
4. 对动量策略回归验证差异。
5. 输出偏差审计报告，说明新增约束对收益、回撤、换手和候选排序的影响。

---

### UC-07：本地 hs300_index 基准缺失后的只读消费与 Tushare 数据准备补齐

| 字段 | 内容 |
|---|---|
| **使用角色** | P-01 量化策略学习者 / 研究者 |
| **触发条件** | 用户运行实验十/十二、轻量回测、benchmark resolver 或 Backtrader optional backend 时要求沪深 300 benchmark，但本地 `hs300_index` canonical/gold 缺失、覆盖不足、quality fail，或 benchmark 口径尚未满足验收。 |
| **输入** | 消费层输入：benchmark 名称 `hs300_index`、回测/实验起止日期、交易日历、quality policy、benchmark 口径要求和本地 lake root。数据准备层输入：用户显式 Tushare fetch/backfill 命令、`target_dataset=hs300_index`、`source=tushare`、exact interface 如 `index_daily(ts_code='399300.SZ')`、日期范围、batch 参数、allowlist、`TUSHARE_TOKEN` 环境变量引用、lake root、dry-run / plan 开关和 quality threshold。 |
| **处理逻辑** | Given 消费层只读本地数据，When `hs300_index` 存在且 quality/catalog 通过，Then 返回 typed `available` benchmark 结果，并携带 `benchmark_kind`、`index_code`、source interface、覆盖起止、交易日历分母、缺失交易日列表、gap explanation、`quality_status` 和 `source_run_id`。Given `hs300_index` 缺失、覆盖不足或 quality fail，When 消费层请求 benchmark，Then 返回 structured `unavailable` 或 `required_missing`，携带 `next_action` 与 `remediation_job_spec`，指向用户应显式执行的 `market_data` Tushare 写湖 / 数据准备作业；消费层不得导入 connector/runtime/storage、不得读取 `TUSHARE_TOKEN`、不得联网、不得静默代理。Given 用户显式执行数据准备补齐作业，When source enabled、allowlist 命中、token 存在且 dry-run/plan 通过，Then `market_data` 写湖层才允许调用 Tushare，写入 raw、manifest、canonical/gold、quality 和 catalog；失败或部分成功必须结构化记录并生成缺口解释。 |
| **输出/结果** | 消费层输出 typed benchmark result：`status=available/unavailable/required_missing`、`benchmark_status`、`quality_status`、`next_action`、`remediation_job_spec`、coverage、missing trade dates、gap reason、docs/runbook reference；数据准备层输出 Tushare raw、manifest/checkpoint、`hs300_index` canonical/gold、quality CSV、catalog entry、coverage/quality/gap explanation 和 source lineage。 |
| **前置条件** | CR-005 数据层契约通过 CP3/CP4；`market_data` 写湖入口与消费层物理隔离；真实 lake root、`.gitignore`、Tushare 接口配额和 `hs300_index` 口径在 CP5 前确认；默认测试和消费主路径断网可运行。 |
| **排除情况** | 不在 `engine/data_loader.py`、实验入口、benchmark resolver 或 Backtrader adapter 内自动 fetch/backfill；不读取或记录 token 值；不提交真实私有数据；不把 `proxy_baseline` 写成 `hs300_index`；不在 Backtrader 中生成 PIT、计算复权因子或绕过 quality gate。 |

**处理流程（文字描述）：**
1. 消费层接收 benchmark 请求，读取本地 catalog/quality 和 `hs300_index` canonical/gold；该流程不得联网。
2. 若本地 `hs300_index` 覆盖请求区间且 quality 通过，返回 `status=available`，并输出 benchmark 口径、指数代码、source interface、交易日历分母、覆盖起止和缺口解释。
3. 若本地 `hs300_index` 缺失、覆盖不足、quality fail 或口径未确认，返回 `status=unavailable` 或 `status=required_missing`，并生成 `next_action` 与 `remediation_job_spec`。
4. `remediation_job_spec` 指向 `market_data` 写湖 / 数据准备层的 Tushare fetch/backfill 作业，至少包含 `target_dataset=hs300_index`、source、interface、date_range、lake_root、quality_report_path、docs_ref 和是否需要先执行 dry-run/plan。
5. 用户显式执行数据准备作业后，写湖层校验 source enabled、allowlist、token env、batch 参数和 lake root；任一条件不满足时结构化失败，不联网。
6. 写湖层调用 Tushare 后写入 raw 和 manifest，再派生 `hs300_index` canonical/gold，生成 quality CSV、catalog 和 gap explanation。
7. 用户再次运行消费层时，resolver 只读更新后的本地数据；若仍有缺口，继续返回 structured status 和可操作补齐建议。

---

### UC-08：生产级因子研究数据补齐并重跑实验 17-21

| 字段 | 内容 |
|---|---|
| **使用角色** | P-03 因子研究数据审计者；P-01 量化策略学习者 / 研究者 |
| **触发条件** | 用户已获得实验 17-21 的探索结论，但报告仍限定为固定快照股票池、`proxy_baseline`、close 执行价代理和未建模交易约束；用户希望在进入新一轮设计和实现前，把生产级数据缺口转化为可验收的场景与需求。 |
| **输入** | CR-011 变更单、实验 17-21 报告、CR-008 `research_input_v1` 合同、CR-010 limited-window 数据湖 current truth、目标研究区间、`benchmark_policy=hs300_required`、`universe_mode=pit|required`、可交易性门控策略、`execution_price_policy`、`adjustment_policy`、行业/市值/风格中性化开关、流动性/容量/成本参数、因子列表、preprocessing 配置、rolling / 年度 / 市场状态 / 参数 / 成本网格，以及真实数据执行授权状态。 |
| **处理逻辑** | Given 用户要求把实验 17-21 升级为生产级因子研究，When 系统构建新版研究输入，Then 必须先读取本地 catalog/quality/readiness 并校验 `hs300_index`、PIT 股票池、历史权重、股票生命周期、停牌、涨跌停、ST、无成交、上市天数、事件状态、OHLCV/VWAP 或可审计日频执行价代理、`adj_factor`、公司行动、行业分类、市值/流通市值、Beta/风格暴露、成交额/换手/流动性和成本模型。Given 任一生产级必需数据缺失、quality fail、PIT 不完整、`available_at` 不满足或授权边界不满足，Then 系统必须返回结构化 gate result、`required_missing`、`blocked_claims` 和 remediation plan，不得把 fixed snapshot、proxy benchmark、close proxy 或未启用门控结果声明为生产级结论。Given 数据和授权均满足目标窗口，When 执行新版实验，Then 系统输出完整因子审计面板、真实 benchmark 对照、PIT 与可交易性过滤统计、行业/市值/风格中性 IC、容量成本敏感性、rolling walk-forward、年度分层、市场状态分段、参数敏感性和成本敏感性报告，并保留旧实验报告作为 baseline。 |
| **输出/结果** | 版本化新版因子研究报告；`production_strict_research` / `exploratory` gate result；真实 `hs300_index` benchmark 字段与 proxy 字段隔离；PIT universe 和可交易性过滤统计；执行价和复权审计；公司行动异常解释；行业/市值/风格中性分析；流动性、容量和成本敏感性表；完整 `factor_panel` 审计面板，至少包含 `raw`、`directional`、`winsorized`、`zscore` 四层；rolling / 年度 / 市场状态 / 参数 / 成本分层稳健性结果；allowed_claims / blocked_claims；脱敏后的 source/interface/run_id/lineage/quality metadata。 |
| **前置条件** | CR-011 已获批准并回退到 solution-design；CP3/CP4 通过前不得进入 LLD；CP5 批次确认通过前不得实现代码或执行真实抓取。真实联网、真实 lake 写入、旧 `data/**` 操作和凭据读取必须按后续 Story 显式授权执行；默认测试和 dry-run 不读取、不打印、不记录凭据值。 |
| **排除情况** | 不覆盖实验 17-21 旧报告，不把旧 `proxy_baseline` 追认为真实沪深 300；不在需求/场景阶段真实联网、真实抓取、写真实 lake 或读取凭据；不声明超出 quality/readiness 覆盖窗口的完整历史 PIT；不把缺失行业、市值、风格、容量或公司行动数据的结果称为中性化、容量可交易或复权链路可审计结论。 |

**处理流程（文字描述）：**
1. 读取 CR-011、实验 17-21 旧报告、CR-008 `research_input_v1` 合同和 CR-010 readiness/catalog/quality 事实，只做需求与场景增量，不触发真实联网或真实写 lake。
2. 对目标研究窗口执行生产级研究数据准入扫描，逐项检查真实 benchmark、PIT universe、股票生命周期、可交易性、执行价、复权/公司行动、行业/市值/风格、流动性/容量/成本和因子审计面板可用性。
3. 对每个数据域返回 `available/pass`、`warn/exploratory`、`required_missing` 或 `blocked`，并输出可追溯 source/interface/run_id、coverage、missing reason、quality status 和 remediation plan。
4. 若真实 benchmark 不可用，保留 `proxy_baseline` 但禁止输出 `hs300_*` 生产级超额收益；若 PIT 不可用，生产级因子结论 fail，探索模式必须标记 fixed snapshot 和幸存者偏差。
5. 若可交易性、执行价、复权、行业市值风格、流动性容量成本或公司行动数据缺失，阻断对应声明，并在 `blocked_claims` 中明确不得声明真实可成交、中性化、容量可交易、复权链路可审计或纯因子 alpha。
6. 若准入通过，生成新版研究输入和完整 factor audit panel，保留 raw / directional / winsorized / zscore 四层因子值、preprocessing metadata、过滤原因和 lineage。
7. 执行真实 benchmark 对照、PIT / fixed 对比、行业市值风格中性 IC、流动性容量成本敏感性、rolling walk-forward、年度分层、市场状态分段、参数敏感性和成本敏感性分析。
8. 输出版本化新版报告和审计产物，旧实验 17-21 报告继续作为 fixed-snapshot / proxy baseline 历史基线。

---

### UC-09：A 股自存在日起至当前交易日的生产级全历史数据湖

| 字段 | 内容 |
|---|---|
| **使用角色** | P-04 生产数据湖负责人 / 数据工程审计者；P-03 因子研究数据审计者 |
| **触发条件** | 用户已批准 CR-014 进入 standard 变更流程，并明确数据湖目标从 limited-window / 2020-2024 roadmap 升级为 A 股证券自存在 / 上市日起至当前交易日的 production current truth，同时要求评估 DuckDB 是否作为只读查询、审计和特征抽取候选能力。 |
| **输入** | CR-014 变更单；既有 CR-010 / CR-012 / CR-013 旧基线；A 股证券 universe、上市日 / 存在起始日、退市 / 摘牌日、list_status、代码变更和交易所 / 板块归属；P0 dataset 候选清单；source/interface allowlist；交易日历；lake root；raw / manifest / canonical / gold / quality / catalog 分层契约；catalog current pointer；增量刷新窗口；replay run_id / batch_id；DuckDB 候选评估输入；真实 provider / lake / credential / old data 权限状态。 |
| **处理逻辑** | Given CR-014 仍处于需求澄清增量阶段，When 用户或系统整理全历史数据湖需求，Then 只能写入场景、需求和澄清日志，不得执行真实 provider fetch、读取凭据、写真实 lake、读取或列出旧 `data/**`、覆盖旧 reports 或修改 DuckDB 依赖。Given 后续进入设计，When 定义 production current truth，Then 必须以全 A 股证券为 universe，按每只证券的存在 / 上市日至当前交易日计算 coverage denominator，并显式处理退市、摘牌、代码变更、简称变更、交易所 / 板块迁移、停牌和不可交易状态；固定快照或当前状态不得伪装为 PIT 历史。Given P0 dataset 需要发布，When 数据经过 plan / run / normalize / validate / publish 生命周期，Then raw、manifest、canonical、gold、quality、catalog 各层职责必须分离，validate pass 不得自动成为 current truth，只有显式 publish 后 catalog current pointer 才可供 reader / audit / feature extraction 消费。Given 需要持续保持当前交易日真值，When 执行增量刷新或 replay，Then 默认只补缺口和经批准的最近 N 个交易日回补，replay 只能从 manifest/raw 重放标准化和审计链路，不触发 provider，也不得污染已发布 current pointer。Given 评估 DuckDB，When HLD 尚未批准依赖与边界，Then DuckDB 只能记录为只读查询、coverage audit、PIT join、特征抽取和 pandas/pyarrow 对账候选，不替代 Parquet lake、catalog/manifest 或 source-of-truth current pointer。 |
| **输出/结果** | CR-014 场景基线；全 A since-inception production current truth 的范围定义；P0 dataset 分层和 publish current pointer 要求；证券生命周期 / 代码变更处理要求；增量刷新与 replay 要求；DuckDB 只读 query / audit / feature extraction 候选定位；allowed_claims / blocked_claims / required_missing 声明边界；权限计数边界；面向 CP2 的待确认问题和默认假设。 |
| **前置条件** | CR-014 已获用户批准进入 standard 变更流程；需求增量完成后仍需 CP2 用户确认，CP2 前不得进入 HLD；真实 provider fetch、真实 lake 写入、凭据读取、旧 `data/**` 操作、旧 reports 覆盖和 DuckDB 依赖引入必须等待后续 HLD/CP3/CP5 与用户显式授权。 |
| **排除情况** | 不在本阶段抓取 provider、不读取或打印 token / `.env` / 用户名 / 密码 / NAS 凭据、不写真实 lake、不读取 / 列出 / 迁移 / 复制 / 比对 / 删除旧 `data/**`、不覆盖旧报告、不修改代码或依赖、不将 DuckDB 设为已批准依赖、不把 limited-window pass 或 roadmap-only 结论声明为全 A 全历史 production current truth。 |

**处理流程（文字描述）：**
1. 读取 CR-014 的文档处理决策和旧基线映射，确认 `USE-CASES.md` 与 `REQUIREMENTS.md` 采用原文档增量更新，旧 UC / REQ 编号不重排。
2. 将目标 universe 从 limited-window / HS300 局部研究扩展为全 A 股证券，并把每只证券的存在 / 上市日至当前交易日作为 coverage denominator 的基本边界。
3. 定义证券生命周期处理要求，覆盖上市、退市 / 摘牌、暂停上市、代码变更、简称变更、交易所 / 板块归属变化和状态可用时点。
4. 将 P0 dataset 的生产链路固化为 raw、manifest、canonical、gold、quality、catalog 分层，要求每层输出具备 run_id、batch_id、source/interface、lineage 和质量状态。
5. 明确 publish gate：validate pass 只是候选质量结果，必须经显式 publish 才能更新 catalog current pointer；reader 和后续审计只能消费已发布 current truth 或结构化 missing 结果。
6. 定义增量刷新和 replay：默认只补缺口和经批准的最近 N 个交易日回补；replay 使用 manifest/raw 重放标准化和质量审计，不触发 provider。
7. 将 DuckDB 写入待 HLD 决策候选项：默认只读 Parquet / catalog，用于查询、coverage audit、PIT join、特征抽取和 pandas/pyarrow parity，不在需求阶段新增依赖。
8. 输出 allowed_claims / blocked_claims：只有全 A since-inception P0 gate、生命周期、quality/readiness、catalog current pointer 和权限边界均满足时，才允许声明对应 production current truth；否则必须输出 `required_missing` 或 `blocked_claims`。
9. 汇总 CP2 待确认问题，包括全 A 覆盖边界、P0 dataset 清单、当前交易日定义、DuckDB 角色和真实执行授权边界。

---

### UC-10：QMT 交易接入 foundation 的 shadow / dry-run / mock 验证

| 字段 | 内容 |
|---|---|
| **使用角色** | P-05 QMT 交易接入与运行负责人；P-06 研究口径与交易价格审计者 |
| **触发条件** | 用户已批准 CR-015 intake，准备在不真实发单、不读取凭据、不写真实 broker lake 的前提下，把本地研究目标组合接入 OMS、pre-trade risk、QMT adapter 和订单状态机设计。 |
| **输入** | CR-015；CP2 intake approved 结论；策略目标组合或目标权重；`strategy_id`、`run_id`、`signal_date`、`target_trade_date`；`research_adjustment_policy`；`execution_price_policy=raw`；现金、可用持仓、100 股整手、T+1 可卖、单票 / 组合上限、重复下单保护等 pre-trade risk 规则；mock broker fixture；外置 `BROKER_LAKE_ROOT` label 或 dry-run 路径标签；QMT adapter mode=`shadow|dry_run|mock`。 |
| **处理逻辑** | Given 策略层生成目标组合，When foundation 流程启动，Then 策略层只能提交目标组合 / order intent 请求，不得直接调用 QMT / XtQuant API。Given OMS 接收目标组合，When 生成 order intent，Then 必须记录研究口径 `research_adjustment_policy` 和交易执行口径 `execution_price_policy=raw`，并按现金、整手、可用持仓、T+1、限额和重复保护生成可审计意图。Given pre-trade risk 任一规则 fail，When order intent 准备发送 adapter，Then 系统必须 hard block，记录阻断原因，不触达 QMT adapter。Given adapter mode 为 shadow / dry-run / mock，When OMS 发送意图，Then 只生成模拟 adapter 响应、状态迁移和审计事件，不调用真实 `order_stock`、`order_stock_async`、`cancel_order_stock` 或任何真实账户写操作。Given broker lake 处于未授权真实写入状态，When 产生订单、成交、持仓、资产、错误和对账事件，Then 只能写入 mock / dry-run 审计产物或计划，不写仓库 `data/**` / `reports/**`，不输出凭据和账户敏感信息。 |
| **输出/结果** | QMT foundation 场景基线；order intent 合同；OMS 状态机事件；pre-trade hard block 决策；adapter mode 审计；mock / dry-run broker event 计划；脱敏后的 `run_id`、`strategy_id`、`research_adjustment_policy`、`execution_price_policy=raw`、risk result、state transition 和 blocked reason；允许 / 禁止声明边界。 |
| **前置条件** | CR-015 已 approved-for-intake；CR-017 的 raw / qfq / hfq 边界已被 CP2 intake 接受；CP3/CP4/CP5 前不得实现或调用真实 QMT；QMT 凭据、账户号、session、cookie、交易密码和 `.env` 内容不得读取、打印、记录或保存。 |
| **排除情况** | 不做真实发单、撤单、账户写操作、账户凭据读取、真实 broker lake 写入、QMT 依赖引入、信用账户、多资产、期货、期权、完整第三方交易平台迁移；不允许策略绕过 OMS / risk 直接调用 QMT；不允许把 qfq/hfq 复权价作为真实委托价或成交价。 |

**处理流程（文字描述）：**
1. 策略层输出目标组合和信号 metadata，仅提交给 OMS，不触达 QMT adapter。
2. OMS 将目标组合转换为 order intent，记录 `research_adjustment_policy`、`execution_price_policy=raw`、`signal_date`、`target_trade_date`、目标权重、现金和持仓快照引用。
3. pre-trade risk 执行 hard block 检查，覆盖现金、整手、T+1 可卖、可用持仓、组合 / 单票限额、重复下单和价格口径。
4. 风控通过时，adapter 在 shadow / dry-run / mock 模式下生成模拟 broker 响应；风控失败时不触达 adapter。
5. OMS 根据模拟响应推进状态机，覆盖 accepted、partially_filled、filled、cancel_pending、canceled、rejected、failed、unknown 和 timeout 等状态。
6. 系统输出脱敏审计事件和 broker lake 写入计划；未获授权时不写真实 broker lake、不写仓库数据目录、不输出任何账户敏感信息。

---

### UC-11：QMT 模拟盘 / 实盘阶段激活与运行治理

| 字段 | 内容 |
|---|---|
| **使用角色** | P-05 QMT 交易接入与运行负责人；P-01 量化策略学习者 / 研究者 |
| **触发条件** | CR-016 intake 已批准，且用户准备把 CR-015 foundation 验证后的链路按阶段推进到 QMT 模拟盘、实盘只读、小资金实盘和资金放大。 |
| **输入** | CR-016；CR-015 foundation 验证结果；阶段目标 `shadow|simulation|live_readonly|small_live|scale_up`；策略版本、参数、冻结时间、成功 / 失败标准；T 日收盘后信号；T+1 限价 / 保护价策略；账户模式和脱敏账户标签；单次运行授权记录；资金上限、单票上限、换手上限、现金安全垫；runbook；盘前 / 盘中 / 盘后对账规则；monitoring heartbeat；kill switch 与暂停 / 恢复 / 手工接管规则；CR-017 复权口径治理状态。 |
| **处理逻辑** | Given 当前阶段尚未满足前置 gate，When 用户请求进入后续阶段，Then 系统必须阻断并输出缺失 gate、所需 runbook、对账或授权项。Given 模拟盘前 runbook 未完成，When 请求启用 QMT 模拟盘，Then 阻断并要求补齐异常处理、审批点、回滚和恢复路径。Given 用户请求任何真实 QMT 操作，When per-run 授权缺少账户模式、策略、日期、金额上限、回滚策略或审批证据，Then 系统不得调用真实 API。Given 运行已获授权并进入对应阶段，When T 日信号在收盘后生成，Then T+1 才允许以限价 / 保护价生成订单，并执行盘前、盘中、盘后对账。Given heartbeat、风险、对账或人工触发异常，When kill switch 被触发，Then 必须停止新单、撤可撤单、冻结策略并记录人工接管。Given CR-017 仅完成设计但未完成实现验证，When 用户请求生产策略复权治理声明或资金放大，Then 阻断声明和资金放大，但不阻断技术链路模拟盘。 |
| **输出/结果** | 阶段准入 / 退出 / 阻断记录；runbook readiness；per-run 授权摘要；T 日信号与 T+1 委托计划；模拟盘 / 实盘只读 / 小资金实盘运行报告；盘前 / 盘中 / 盘后 reconciliation report；kill switch 事件；暂停 / 恢复 / 手工接管审计；资金放大 gate result；allowed_claims / blocked_claims。 |
| **前置条件** | CR-015 foundation 的 adapter / OMS / risk / broker lake 设计和验证已通过对应门控；CR-016 CP3/CP4/CP5/CP6/CP7/CP8 未通过前不得进入真实实现和验收关闭；真实发单、撤单、账户查询和账户写操作必须逐次获得用户 per-run 授权；凭据和账户敏感信息不得入库或输出日志。 |
| **排除情况** | 不允许从研究或模拟盘直接跳到放大资金；不允许无授权真实发单、撤单、账户写操作或账户凭据读取；不允许未完成 CR-017 口径治理就声明生产策略复权治理完成；不解除真实 VWAP、minute、tick、level2、order-match、微观结构冲击成本 blocked claim。 |

**处理流程（文字描述）：**
1. 系统读取当前目标阶段和上一阶段验证证据，生成 stage gate result。
2. 模拟盘前检查 runbook、mock / dry-run adapter 验证、pre-trade risk、状态机、broker lake 计划和对账规则。
3. 每次真实 QMT 操作前检查 per-run 授权，授权摘要必须覆盖账户模式、策略、日期、资金上限、操作范围和回滚策略。
4. T 日收盘后冻结信号和策略版本，T+1 按限价 / 保护价策略生成订单计划。
5. 运行中持续执行 heartbeat、风控和盘中对账；盘后生成完整 reconciliation report。
6. 发生异常或人工触发时执行 kill switch，停止新单、撤可撤单、冻结策略并记录接管人和处理结果。
7. 资金放大前检查 CR-017 复权治理、非沪深 300 benchmark、行业 / 市值 / 风格暴露、PIT、实验注册和运行稳定性；未通过时只允许保持小规模或模拟阶段。

---

### UC-12：复权双视图与 QMT 原始交易价隔离

| 字段 | 内容 |
|---|---|
| **使用角色** | P-06 研究口径与交易价格审计者；P-04 生产数据湖负责人 / 数据工程审计者；P-05 QMT 交易接入与运行负责人 |
| **触发条件** | 用户明确要求数据湖同时支持前复权 `qfq` 和后复权 `hfq`，并要求 CR-015 / CR-016 的 QMT 委托、成交和对账只使用 raw / broker price。 |
| **输入** | CR-017；`prices_raw` 候选事实源；`adj_factor` 候选事实源；provider 字段解释；复权公式与方向待 CP3 冻结项；`as_of_trade_date`；`source_run_id`、`batch_id`、lineage checksum、quality report；研究 run 的 `research_adjustment_policy=qfq|hfq|returns_adjusted|raw`；QMT 的 `execution_price_policy=raw`；旧 `qfq` 数据 / 报告兼容声明；真实抓取 / 写湖 / publish / 迁移授权状态。 |
| **处理逻辑** | Given 仍处于需求澄清或 HLD 前，When 整理复权双视图需求，Then 不执行真实抓取、真实写湖、发布 `current` pointer、依赖引入或旧 qfq 数据迁移。Given 数据湖设计 raw 和 adj_factor，When 生成复权视图，Then `prices_raw` 与 `adj_factor` 是事实源，`prices_qfq`、`prices_hfq` 和 `returns_adjusted` 是独立派生 dataset / view，不得在同一 `prices` frame 中混用。Given 生成 qfq，When 因复权因子变化导致历史价格漂移，Then 必须记录 `as_of_trade_date`、输入 snapshot 和 source lineage。Given 研究 run 选择复权口径，When reader / validation 启动，Then 同一 run 只能使用一个明确 `research_adjustment_policy`，混用时 fail fast。Given OMS 或 QMT adapter 构建订单、成交或对账，When 读取价格字段，Then 只能使用 raw / broker price，qfq/hfq 只能作为研究 metadata 和报告声明。 |
| **输出/结果** | 复权双视图场景基线；raw / adj_factor / qfq / hfq / returns_adjusted dataset 边界；qfq `as_of_trade_date` 要求；单 run 复权口径 gate；QMT raw 执行价格边界；旧 qfq 基线迁移 / 兼容声明；allowed_claims / blocked_claims；CR-017 与 CR-015 / CR-016 的交叉依赖。 |
| **前置条件** | CR-017 已 approved-for-intake；CR-014 数据湖分层和 publish gate 作为上游事实源边界；HLD/ADR 必须在实现前冻结公式、provider 字段解释、schema、reader API、quality gate、旧 qfq 兼容策略和 QMT raw 执行价格隔离。 |
| **排除情况** | 不在本阶段真实抓取、真实写湖、发布 `current` pointer、批量重算或覆盖旧 qfq 数据、修改代码或引入依赖；不把 `adj_factor` 声明为完整公司行动链路；不在同一 dataset / frame 混存 raw/qfq/hfq；不把 qfq/hfq 复权价用于 QMT 委托、成交、成交核算或 broker 对账。 |

**处理流程（文字描述）：**
1. 读取 CR-017 文档处理决策和旧基线映射，确认旧 `qfq` 默认口径保留为历史基线，双视图通过新增 dataset / view 增量实现。
2. 定义 `prices_raw` 与 `adj_factor` 作为事实源，记录 provider、interface、run_id、batch_id、可用时间和 lineage。
3. 派生 `prices_qfq`、`prices_hfq` 和 `returns_adjusted`，每个 view 内只允许单一口径。
4. qfq 物化时记录 `as_of_trade_date` 和输入 snapshot，避免未来复权因子变化导致历史价格漂移不可审计。
5. reader / validation 对研究 run 执行单口径 gate；发现 raw/qfq/hfq 混用时返回结构化错误。
6. OMS / QMT adapter 消费 order intent 时只读取 raw / broker price，并把研究复权口径作为 metadata 而不是执行价。
7. 输出迁移 / 兼容声明，说明旧 qfq 报告继续可追溯，新版严肃研究推荐使用 `returns_adjusted` 或显式 hfq / qfq 口径。

---

### UC-13：CR018 数据湖 production current truth closure 与 Explicit Publish Gate

| 字段 | 内容 |
|---|---|
| **使用角色** | P-04 生产数据湖负责人 / 数据工程审计者；P-03 因子研究数据审计者 |
| **触发条件** | CR014 S14 已形成 2015-01-05 至最近已闭市交易日的全 A `prices` / `adj_factor` candidate，但 catalog current pointer 尚未 publish；用户已批准 D1-D6，并把最高优先级切换为先完成数据湖 production current truth。 |
| **输入** | CR018；CR014 S14 candidate 检查记录；`prices_raw` / `adj_factor` candidate；trade calendar；PIT universe / lifecycle / code-change；ST、停牌、`trade_status`、`prices_limit`；HS300 / ZZ500 / ZZ1000 / 中证全指行情、历史成分和权重；qfq / hfq / returns_adjusted 派生；quality/readiness 规则；release approval；rollback target；真实 provider / lake / credential / publish 授权状态。 |
| **处理逻辑** | Given CR014 S14 candidate 已存在, When 系统评估 production current truth, Then 必须把 candidate、validate PASS、parity PASS 与 published current truth 区分开；candidate 只能作为输入事实，不得自动更新 current pointer。Given P0 dataset group 尚未满足, When 检查 release readiness, Then 必须逐项输出 raw / manifest / canonical / gold / quality / catalog lineage、coverage denominator、缺口、blocked claims 和解除条件。Given Explicit Publish Gate 被触发, When 用户批准发布, Then 只有该 gate 可以更新 catalog current pointer，且 release 必须记录 `release_id`、`release_scope`、`as_of_trade_date`、目标交易日口径、universe 口径、dataset 清单、source run ids、quality 结果、blocked claims、rollback target、approver 和 approved_at。Given publish 后发现质量异常, When 执行 rollback, Then current pointer 必须可回退到上一 release，并保留 candidate/raw/manifest，不做破坏性删除。 |
| **输出/结果** | production current truth release summary；dataset-group readiness matrix；allowed_claims / blocked_claims；catalog current pointer 更新记录；rollback plan；publish / rollback smoke result；脱敏 lineage metadata；不把 candidate 误称 current truth 的文档声明。 |
| **前置条件** | CR018 CP2 / CP3 / CP4 / CP5 必须通过；真实 provider fetch、真实 lake 写入、凭据读取和 catalog publish 必须分别获得后续明确授权；行业 / 市值 / 流动性若被列为 P1，则不得解除中性化、容量和资金放大相关 blocked claims。 |
| **排除情况** | 不在需求 / 设计阶段新增真实抓取或写湖；不打印或保存 token / `.env` / 用户名 / 密码 / NAS 私有路径；不把 DuckDB `.duckdb` 文件设为事实源；不因为 `prices` / `adj_factor` 已完整就跳过 PIT/W3/benchmark/quality；不把发布动作拆散为多个不可回滚的 current pointer 入口。 |

**处理流程（文字描述）：**
1. 读取 CR014 S14 candidate 检查记录，确认 `prices` / `adj_factor` 覆盖与 `catalog_not_published` 状态。
2. 固化 production current truth 的 release scope、`as_of_trade_date` 和 dataset group。
3. 对 PIT universe、lifecycle/code-change、ST、停牌、`trade_status`、`prices_limit`、benchmark 行情 / 成分 / 权重、复权派生和 quality/readiness 执行准入检查。
4. 生成 dataset-group readiness matrix，列出 available、required_missing、blocked_claims、quality fail 和解除条件。
5. 若 P0 gate 通过并获得 publish 授权，执行 Explicit Publish Gate，更新 catalog current pointer 并写 release summary。
6. 执行 read/query smoke、rollback smoke 和 current pointer 审计；失败时回滚到上一 release。
7. 将 allowed_claims / blocked_claims 写入用户文档和研究报告声明边界。

---

### UC-14：Published truth 研究重跑与 QMT 阶段后置门控

| 字段 | 内容 |
|---|---|
| **使用角色** | P-03 因子研究数据审计者；P-05 QMT 交易接入与运行负责人；P-01 量化策略学习者 / 研究者 |
| **触发条件** | 数据湖 current pointer 已发布，或用户请求在当前数据湖状态下重跑研究 / 启动 QMT simulation / live_readonly / small_live / scale_up。 |
| **输入** | published release；`release_id`；release summary；研究重跑配置；阶段三到阶段五核心研究脚本 / 报告规格；QMT stage request；stage gate rules；QMT foundation 验证证据；runbook；per-run 授权状态；allowed_claims / blocked_claims。 |
| **处理逻辑** | Given 数据湖未 publish, When 用户请求 QMT simulation 或更高阶段, Then stage gate 必须返回 blocked，并说明缺少 published release 和 production 研究重跑。Given published release 已存在, When 执行研究重跑, Then 阶段三到阶段五核心结论必须使用同一 `release_id`、明确 `research_adjustment_policy`、真实 benchmark、PIT universe、可交易状态和 blocked claim 边界，输出可追溯报告。Given 研究重跑未通过或结论被 PIT/W3/benchmark 推翻, When 用户请求 QMT 阶段推进, Then 继续 blocked，并保留 QMT foundation 仅为离线受控成果。Given publish + 研究重跑通过, When 用户另行申请 QMT simulation, Then 才允许进入 CR016 stage gate 的下一轮独立审批；该批准不自动授权真实下单、撤单、账户查询或资金放大。 |
| **输出/结果** | production release research rerun report；低波 / 因子主结论重评估；QMT stage gate result；blocked reason；可解禁范围；后续 CP5 / per-run 授权需求；文档中的 QMT 后置声明。 |
| **前置条件** | UC-13 的 publish gate 已通过或明确返回 blocked；研究重跑输入必须来自 published current truth；QMT foundation 仍必须满足 CR015/CR016/CR017 已验证边界。 |
| **排除情况** | 不把 QMT foundation 的离线 mock / dry-run 结果当作 simulation 授权；不在研究重跑失败时继续推进真实 QMT；不因技术链路可用而解除策略有效性、容量、行业 / 市值中性或实盘可交易 blocked claims。 |

**处理流程（文字描述）：**
1. 检查是否存在已发布 `release_id` 和可读 current pointer。
2. 若未发布，QMT simulation / live_readonly / small_live / scale_up gate 返回 blocked。
3. 若已发布，以该 `release_id` 重跑阶段三到阶段五核心研究，记录 benchmark、PIT universe、可交易性、复权口径和 blocked claims。
4. 对比旧 proxy / fixed-snapshot 结论与生产口径重跑结论，确认低波主线是否仍成立。
5. 研究重跑未通过时保持 QMT 后置；通过时只允许进入下一轮 QMT stage gate 审批，不自动发放真实操作权限。
6. 将 release research rerun result 和 QMT admission result 写入状态、文档和后续运行手册。

---

### UC-15：CR-019 阶段六 A 股多因子模拟盘准入基线

| 字段 | 内容 |
|---|---|
| **使用角色** | P-07 阶段六多因子模拟盘准入负责人；P-03 因子研究数据审计者；P-05 QMT 交易接入与运行负责人 |
| **触发条件** | production current truth 研究重跑显示既有多因子 / 低波策略未通过准入，且用户确认阶段六目标扩展为“制定 A 股多因子策略，并达到可申请模拟盘状态”。 |
| **输入** | CR-019；阶段六学习目标和计划；多因子 simulation admission plan；data gap / source acquisition plan；local_backtest improvement plan；published current truth / blocked claims；实验 49-66 计划；benchmark 组；PIT universe；行业 / 市值 / 财务 available_at；可交易性 / 成本 / 容量证据；QMT runbook；per-run authorization 状态。 |
| **处理逻辑** | Given 旧多因子或低波 production rerun fail, When 生成阶段六 admission 判断, Then 不得把旧失败结果包装为可申请模拟盘。Given 数据、因子、策略、交易现实性、成本、benchmark、稳健性、消融、冻结、pre-sim 或 dry-run 任一 gate 未过, When 用户请求 simulation admission, Then 输出 blocked_claims 和解除条件。Given 所有准入 gate 通过且连续 5 个真实交易日 dry-run 安全计数为 0, When 用户另行申请 QMT simulation, Then 才允许进入 CR016 stage gate 和 per-run authorization 评审。 |
| **输出/结果** | 阶段六多因子 admission package；gate result；blocked_claims / allowed_claims；实验 49-66 追溯；策略冻结摘要；5 日 dry-run summary；QMT simulation 申请前置条件。 |
| **前置条件** | CR-019 CP2 需求基线通过；后续 CP3 / CP4 / CP5 冻结设计、Story 和 LLD；真实 provider fetch、真实 lake 写入、真实 reports/delivery 写入、凭据读取、真实 QMT 操作和 simulation run 必须另行授权。 |
| **排除情况** | 不在需求阶段实现策略、补数、FastAPI、Backtrader 或 Qlib；不执行真实 QMT / MiniQMT / XtQuant；不把 QMT 文档能力说明当作当前账户授权；不跳过 publish + production rerun + admission + 5 日 dry-run。 |

**处理流程（文字描述）：**
1. 读取 CR-018 / CR-019 结论，确认既有策略 admission 当前为 blocked。
2. 冻结阶段六目标：重新制定 A 股多因子策略，而不是包装旧失败策略。
3. 将实验 49-66 映射到数据、因子、组合、交易现实性、成本、benchmark、稳健性、消融、冻结、pre-sim 和 dry-run gate。
4. 对每个 gate 输出 pass / fail / blocked、证据路径、解除条件和对应声明边界。
5. 连续 5 个真实交易日 dry-run 均通过且安全计数为 0 后，生成 admission package。
6. admission package 仅作为申请 QMT simulation 的输入，仍需 CR016 stage gate 和 per-run authorization。

---

### UC-16：QMT C/S 模块与 Windows FastAPI 服务桥接

| 字段 | 内容 |
|---|---|
| **使用角色** | P-05 QMT 交易接入与运行负责人；P-07 阶段六多因子模拟盘准入负责人 |
| **触发条件** | 用户在 CR-019 D7 中确认 WSL / local_backtest 与 Windows QMT 节点第一版桥接采用 FastAPI 本地服务，同时补充要求 QMT 模块必须从回测框架主进程摘离并形成独立 C/S 模块。 |
| **输入** | local_backtest 内 C 侧 QMT client 调用；统一 Python 接口候选；可选薄 CLI；Windows QMT 节点 S 侧 gateway；完整 QMT FastAPI 网关候选契约；Windows 可运行 / 可安装命令；绑定地址 / 防火墙 / 可选极简鉴权方案；heartbeat；QMT runbook；QMT 系统说明文档能力背景；signed file drop fallback 约束。 |
| **处理逻辑** | Given local_backtest 需要访问 QMT 能力, When 策略、OMS 或运行治理模块调用 QMT 能力, Then 必须先调用 C 侧统一 Python client / 函数接口，由 C 侧通过 REST 请求 Windows S 侧 gateway；local_backtest 不得直接依赖 xtquant。Given S 侧 gateway 设计接口面, When 定义能力范围, Then 必须覆盖 QMT 常用完整功能类别，包括 health / capabilities、intent validate、dry-run、行情 / 账户 / 持仓 / 委托 / 成交查询、simulation submit / cancel、live-readonly、live submit / cancel、reconciliation 和 kill-switch 等接口类别，并由 Windows QMT 客户端转换为 QMT / XtQuant 调用访问 QMT 服务端；不得把“不做或少做鉴权”误解为“不支持 QMT 功能”。Given 服务运行在受控局域网, When 选择鉴权策略, Then 第一版可不做应用层鉴权，或采用最简 token / HMAC；鉴权策略不改变 QMT 功能接口覆盖。 |
| **输出/结果** | C 侧统一 Python client / 函数接口候选设计；可选 CLI wrapper 边界；完整 QMT gateway API contract 草案；Windows 可安装 / 可运行 S 侧命令合同；WSL / Windows 部署边界；可选鉴权、heartbeat、日志脱敏和 fallback 设计输入；后续 HLD / ADR / Story Plan 输入。 |
| **前置条件** | 本轮只做需求与场景增量；FastAPI 实现、依赖变更、服务启动、端口开放和真实 QMT adapter 调用必须等 CP3/CP4/CP5/LLD 之后另行授权。 |
| **排除情况** | 不在需求阶段写 FastAPI 代码或新增依赖；不把服务绑定到公网或不受控局域网作为默认；不把 gateway 代码耦合进回测框架主进程；不读取 QMT 账户、token、session、cookie、交易密码或 `.env`；不在 CP5/CP6/CP7 前执行真实账户查询、发单、撤单或 broker lake 写入。 |

**处理流程（文字描述）：**
1. 将 D7 决策写入需求基线：FastAPI 本地服务是主选桥接方式，并将 QMT 模块拆成 local_backtest C 侧 client 与 Windows S 侧 gateway。
2. 将 Q-038 的 signed file drop 从旧主选降级为 fallback，并限定 fallback 只能 dry-run 或 blocked。
3. 定义完整 QMT endpoint 分类：基础健康 / 能力、校验 / dry-run、行情与账户只读、委托 / 成交 / 持仓查询、simulation submit / cancel、live-readonly、live submit / cancel、reconciliation、kill-switch。
4. 记录 C 侧接口形态备选：Python client / 函数调用、CLI-first、Python client 主接口 + 薄 CLI，并将推荐方案交给 CP2 / CP3 冻结。
5. 记录部署边界：Windows 节点运行独立 QMT gateway 命令并拥有 QMT adapter，WSL / local_backtest 侧通过 HTTP API 访问，不直接导入 xtquant。
6. 将 Windows 安装命令、启动 / 停止方式、绑定地址、防火墙、是否启用最简 token/HMAC、heartbeat、日志脱敏、fallback 切换条件作为 CP3 必须冻结项。

---

### UC-17：FastAPI 完整 QMT 接口与运行门控

| 字段 | 内容 |
|---|---|
| **使用角色** | P-05 QMT 交易接入与运行负责人；P-07 阶段六多因子模拟盘准入负责人；P-06 研究口径与交易价格审计者 |
| **触发条件** | QMT C/S bridge 合同进入 HLD，或用户要求回测框架通过 Windows API gateway 支持完整 QMT simulation / live / account / cancel / query 能力。 |
| **输入** | FastAPI capabilities；order intent；QMT 查询 / 交易请求；pre-trade risk result；CR016 stage gate；运行模式配置；可选 token/HMAC；runbook；reconciliation / kill switch readiness；日志脱敏策略；fallback policy。 |
| **处理逻辑** | Given FastAPI capabilities 返回完整 QMT endpoint 类别, When HLD/LLD 设计 gateway, Then 接口面必须支持 simulation、实盘只读、小资金实盘、撤单、账户 / 持仓 / 委托 / 成交查询、对账和 kill-switch 等完整功能类别。Given 请求进入真实 QMT 操作路径, When 当前 run mode、stage gate、risk gate、kill switch 或必要授权上下文不满足, Then 返回 blocked 并保持对应真实 QMT API 调用计数为 0。Given 服务只在受控局域网运行, When 选择鉴权策略, Then 可采用无应用层鉴权或最简 token/HMAC；鉴权只解决调用方识别，不削减 QMT 功能接口。 |
| **输出/结果** | 完整 QMT gateway endpoint matrix；运行门控状态机；blocked reason；required run-mode / stage context；redaction check result；真实操作计数；fallback 结果。 |
| **前置条件** | CR016 stage gate、runbook、运行模式、对账和 kill switch 规则仍有效；完整 endpoint 可以设计和实现，但真实操作只能在对应 stage / mode / risk gate 满足时转发。 |
| **排除情况** | 不允许 WSL 主进程直接调用 xtquant；不允许 gateway 与回测框架强耦合为同一进程；不允许日志输出敏感值；不允许 fallback 自动绕过 gateway 做真实 QMT；不允许把局域网运行表述为“无安全风险”。 |

**处理流程（文字描述）：**
1. C 侧请求进入 Windows FastAPI gateway 前先识别 endpoint 类别、run mode、stage gate、risk gate、kill switch 和可选鉴权状态。
2. 对 validate / dry-run endpoint 输出脱敏日志和 no-real-op 计数。
3. 对 simulation / live / account / cancel / query 等真实 QMT endpoint，若模式和门控满足则转发到 Windows QMT adapter；否则返回 blocked 并列出缺失前置项。
4. FastAPI 不可达、可选鉴权失败或部署边界不满足时，按 fallback policy 返回 blocked 或人工 dry-run 文件，不自动真实 QMT。
5. 默认未授权路径记录真实 QMT API 调用、凭据读取、provider fetch、lake/reports/delivery 写入计数为 0；已授权路径必须记录真实调用类别、run_id、stage、结果和脱敏审计信息。

---

### UC-18：Backtrader / Qlib / minute / Level2 后置边界

| 字段 | 内容 |
|---|---|
| **使用角色** | P-07 阶段六多因子模拟盘准入负责人；P-03 因子研究数据审计者；P-05 QMT 交易接入与运行负责人 |
| **触发条件** | 用户或设计方考虑引入 Backtrader、Qlib、分钟数据或 QMT Level2，以提升执行对照、因子 / ML 研究或微观结构分析能力。 |
| **输入** | CR-019 D1-D5 决策；ROADMAP；阶段六 admission plan；data gap plan；Backtrader optional backend 边界；Qlib isolated runner 边界；分钟 / Level2 数据缺口和触发条件；QMT 系统说明文档能力背景。 |
| **处理逻辑** | Given 用户请求 Backtrader, When production current truth、clean feed、candidate strategy 和轻量主路径未稳定, Then Backtrader 仅保持后置 optional execution backend。Given 用户请求 Qlib, When factor panel、report catalog、PIT / available_at 和隔离 runner 设计未冻结, Then Qlib 仅作为后置 isolated runner。Given 用户请求分钟数据或 Level2, When 实验 58-59 尚未证明执行成本 / 微观结构成为主要风险，Then 二者不作为阶段六 P0。Given QMT 文档说明 Level2 能力, When 当前项目未获对应权限和数据审计, Then 不得声明 Level2 可用。 |
| **输出/结果** | 后置能力触发条件表；Deferred Ideas；scope boundary；后续 CR / Spike 建议；不阻断阶段六日频多因子准入的说明。 |
| **前置条件** | 阶段六 P0 仍以日频 production current truth、多因子准入、5 日 dry-run 和 FastAPI 安全桥接为主；外部框架 / 高频数据不得绕过现有数据、权限和 stage gate。 |
| **排除情况** | 不把 Backtrader 升级为默认主框架；不把 Qlib 作为默认依赖或事实源；不把分钟或 Level2 数据作为 P0；不申请 QMT Level2；不基于 QMT 文档推断已有真实权限。 |

**处理流程（文字描述）：**
1. 对照 D1-D5 决策识别请求属于 P0 主线还是后置能力。
2. Backtrader 只有在 clean feed、候选策略、轻量主路径和执行对照需求明确后进入 W6 optional backend。
3. Qlib 只有在 factor panel、report catalog、PIT/available_at 和 isolated runner 设计稳定后进入 W7。
4. 分钟数据只有在交易现实性实验显示日频执行假设不足时作为 Spike 启动。
5. Level2 只有在订单簿深度、排队、冲击成本成为主要风险且 L1/minute 不足时另起授权和数据审计流程。
6. 未触发时写入 Deferred Ideas，不阻断 CP2 / CP3 主线。

---

### UC-19：CR-025 Backtrader 可选研究执行后端加固

| 字段 | 内容 |
|---|---|
| **使用角色** | P-08 研究执行后端评估者 / 回测引擎维护者；P-07 阶段六多因子模拟盘准入负责人；P-03 因子研究数据审计者 |
| **触发条件** | 用户按 CR-019 follow-up Track B 启动 `CR-025 backtrader_w6` 后进一步澄清：目标不是开发框架级 Backtrader/lightweight 回测框架，而是生产级策略研究回测、模拟盘和实盘框架；当前仍处于 CP2 intake，未批准实现、依赖变更或真实运行。 |
| **输入** | CR-025 正式 CR；CR-019 follow-up 台账 `D-CP8-CR019-05`；既有 `REQ-070`、`REQ-139`、`REQ-155`、QMT OMS / order intent 基线；lightweight engine 主路径；本地 clean feed 候选契约；benchmark / calendar / tradability / cost / quality gate 状态；可选后端选择参数；target portfolio / order intent 字段；Backtrader 本地项目 `/home/hyde/download/backtrader`；安全计数和依赖隔离检查结果。 |
| **处理逻辑** | Given 用户目标是 production-grade research-to-execution, When 定义 CR-025 scope, Then 系统必须把 CR-025 归入回测 / 模拟一致性主线，并显式连接研究可信度和 QMT 生产执行主线。Given meta-se 进入 CP3/HLD, When 分析 Backtrader, Then 必须读取 `/home/hyde/download/backtrader`，按模块输出可借鉴设计、可适配接口、源码级移植候选和禁止移植分类，并记录 license、维护、验证和授权影响。Given 用户未显式选择 Backtrader backend, When 运行研究或回测入口, Then 系统仍使用 lightweight engine 主路径。Given 用户显式选择 Backtrader 但依赖未安装, When optional backend 初始化, Then 返回结构化 `backend_unavailable`，轻量主路径不失败。Given 用户显式选择 Backtrader 且依赖可用, When clean feed 未通过 PIT、`available_at`、复权口径、tradability、benchmark、calendar 或 quality gate, Then optional backend 返回 blocked reason，不生成 PIT、不计算复权因子、不联网补数。Given clean feed、候选策略和成本配置均满足, When 运行 optional backend 对照, Then 输出与 lightweight engine 的执行语义差异报告，并将可进入后续 QMT 路线的结果收敛为 target portfolio / order intent draft 所需字段，不把 Backtrader 结果写成默认 truth 或 simulation-ready 证据。 |
| **输出/结果** | Backtrader module comparison matrix；optional backend availability result；clean feed validation result；lightweight vs Backtrader semantic diff report；research output -> target portfolio / order intent 衔接字段；dependency isolation evidence；safe counters；三条主线 scope boundary；CP3/HLD 和 CP5/LLD 输入。 |
| **前置条件** | CR-025 CP2 已由用户批准进入 CP3/HLD；CP3 只能冻结架构与决策项；CP5 批次确认前不得实现、不得新增依赖、不得修改 `pyproject.toml` / `uv.lock`、不得运行真实 Backtrader backend；源码级移植若被 HLD 推荐，仍需 CP3 明确决策和 CP5 实现授权。 |
| **排除情况** | 不替代 lightweight engine；不把 Backtrader 设为默认依赖或主框架；不在 CP3/CP5 前复制 / 移植 Backtrader 源码；不自研完整事件驱动交易框架；不接入 Backtrader live broker / store；不接 QMT / MiniQMT / XtQuant；不 provider fetch、不写 lake / broker lake、不 publish、不读取凭据、不覆盖旧报告；不把 Backtrader 对照结果作为 QMT simulation 申请或生产 truth；不把 CR-025 approve 解释为 gateway 启动、simulation、live-readonly、small-live 或 scale-up 授权。 |

**处理流程（文字描述）：**
1. 读取 CR-025、CR-019 follow-up 台账和旧需求映射，确认本轮为 production-grade research-to-execution 路线中的研究执行语义对照与接口对齐，而不是框架级主路径迁移或真实 broker 接入。
2. meta-se 在 CP3/HLD 读取 `/home/hyde/download/backtrader`，按 license、模块职责、设计可借鉴点、接口适配点、源码级移植候选、禁止移植项形成对比表。
3. 检查用户是否显式选择 Backtrader backend；未选择时维持 lightweight engine 主路径。
4. 在 HLD/LLD 前仅定义依赖隔离和 lazy import 契约；未安装 Backtrader 时 optional backend 返回结构化不可用，不影响轻量主路径。
5. 校验输入 feed 是否满足 PIT / `available_at` / 单一复权口径 / benchmark / calendar / tradability / cost / quality gate；任一不满足时返回 blocked reason。
6. 在后续 CP5 批准实现后，才允许对同一 clean feed、同一候选策略和同一成本配置运行 lightweight 与 Backtrader 对照。
7. 生成 semantic diff report，解释成交价格、调仓节奏、现金处理、成本扣除、滑点、税费、净值差异和不可比原因。
8. 将可被后续生产执行链路消费的研究输出收敛为 target portfolio / order intent draft 字段，并保留 limitations 与 lineage。
9. 检查安全计数：真实 broker、QMT、provider fetch、lake write、publish 和 credential read 均必须为 0。
10. 将 Backtrader 结果标记为 research comparison，不写成 production truth、默认研究 truth、simulation-ready 或 QMT admission pass。

---

### UC-20：CR-030 多因子研究闭环框架收敛

| 字段 | 内容 |
|---|---|
| **使用角色** | P-03 因子研究数据审计者；P-07 阶段六多因子模拟盘准入负责人；P-08 研究执行后端评估者 |
| **触发条件** | 用户要求借鉴 Qlib 及其他多因子项目，建设本项目自己的多因子策略研究、回测和准入分析框架，并保证准确性、合理性和易分析性。 |
| **输入** | CR-030 正式 CR；本地 Qlib `/home/hyde/download/qlib` 静态分析；外部项目调研；CR-011 因子研究基线；实验 17-21；CR-019 阶段六 admission gate；CR-025 `order_intent_draft_v1` 边界。 |
| **处理逻辑** | Given CR-030 进入 CP3/HLD, When 选择架构主线, Then 系统必须采用项目自有多因子研究闭环，不以 Qlib 或其他外部项目作为默认框架。Given 既有 `research_dataset.py`、实验 17-21 和 Stage6 admission gate 已存在, When 设计多因子框架, Then 必须复用并标准化这些基线，避免平行框架。Given 外部项目提供成熟设计, When HLD 借鉴, Then 只能进入 reference matrix、接口映射或后续 Spike，不得直接成为内部 truth。 |
| **输出/结果** | CR-030 HLD 主线选择；多因子研究闭环模块图；外部项目借鉴边界；现有能力复用清单；后续 Story 候选和不授权项。 |
| **前置条件** | CP2 已确认 UC-20..UC-27 和 REQ-174..REQ-185；CP3 只冻结 HLD 与决策项；CP5 前不得实现或改依赖。 |
| **排除情况** | 不引入默认 Qlib runner；不新增依赖；不运行外部项目；不改业务代码；不授权 provider/lake/publish/QMT/凭据。 |

**处理流程（文字描述）：**
1. 读取 CR-030、analysis artifact、CP2 discussion log 和正式需求基线。
2. 识别现有可复用基线：`research_input_v1`、实验 17-21 `FactorDefinition`、factor audit panel、label window gate、Stage6 admission gate。
3. 将外部项目能力拆成静态参考、可选 Spike、排除项和禁止迁移项。
4. 输出项目自有多因子闭环，不让外部框架接管事实源、runner、provider 或 report truth。
5. 将未解决的 runner / optimizer / ML workflow 需求登记为后续 CR 或 Spike。

---

### UC-21：外部多因子项目静态借鉴矩阵

| 字段 | 内容 |
|---|---|
| **使用角色** | P-03 因子研究数据审计者；P-07 阶段六多因子模拟盘准入负责人 |
| **触发条件** | HLD 需要解释 Qlib、Alphalens、vectorbt、PyBroker、bt、Zipline Reloaded、QuantConnect LEAN、RQAlpha、vn.py / vnpy.alpha、Backtrader 等项目哪些模块可借鉴、哪些不应进入本项目。 |
| **输入** | 本地 Qlib 静态分析；公开项目文档调研；许可证 / 依赖 / provider / runner / live trading 背景；现有数据湖和 QMT stage gate 边界。 |
| **处理逻辑** | Given 外部项目功能强但抽象和依赖不同, When HLD 输出参考矩阵, Then 每个项目必须按 `reference_only`、`optional_spike`、`exclude`、`forbidden_migration` 分类，并列出理由、影响面、切换条件和不授权边界。Given 项目含 provider、live broker、optimizer 或大框架运行时, When 当前未授权运行或依赖变更, Then 必须标记为禁止默认接入。 |
| **输出/结果** | 外部项目借鉴矩阵；license/dependency/provider/runtime boundary；CR-026 分流建议；HLD 决策项。 |
| **前置条件** | 静态调研完成；无需也不得运行外部项目。 |
| **排除情况** | 不 clone / install / run 外部项目；不复制源码；不把外部项目文档当成本项目已具备能力。 |

**处理流程（文字描述）：**
1. 按项目列出核心模块、许可证、依赖、数据入口、runner 形态和交易能力边界。
2. 对每个模块给出分类：静态借鉴、可选 Spike、排除、禁止迁移。
3. 将 Qlib isolated runner 保留为 CR-026 后续候选，不并行启动。
4. 对 vectorbt / PyBroker / RQAlpha 等存在许可证或适用性不确定的项目标注仅作参考。
5. 将矩阵结果写入 HLD 和 CP3 Decision Brief。

---

### UC-22：FactorSpec / FactorRunSpec 契约冻结

| 字段 | 内容 |
|---|---|
| **使用角色** | P-03 因子研究数据审计者；P-07 阶段六多因子模拟盘准入负责人 |
| **触发条件** | 需要把实验 17-21 的探索性因子定义升级为可复查、可复跑、可组合的因子定义和运行契约。 |
| **输入** | 实验 17-21 `FactorDefinition`；CR-011 factor audit panel；`research_input_v1`；数据湖 release / catalog；候选因子配置；调参和运行上下文。 |
| **处理逻辑** | Given 因子需要进入多因子研究闭环, When 生成或加载因子定义, Then 必须显式记录因子 ID、名称、版本、方向、输入字段、窗口、预处理、可用时点、依赖数据、参数、适用 universe 和 blocked claims。Given 同一因子多次运行, When 生成 `FactorRunSpec`, Then 必须记录运行窗口、数据 release、benchmark、成本、随机种子、代码版本、配置哈希和输出目录。 |
| **输出/结果** | `FactorSpec` 字段字典；`FactorRunSpec` 字段字典；校验规则；错误码；外部项目对象映射。 |
| **前置条件** | 需求基线已确认；HLD 只定义契约，不实现 schema 类。 |
| **排除情况** | 不直接采用 Qlib Alpha、Alphalens factor_data、Zipline Pipeline 或 LEAN Alpha Model 作为内部对象；不绕过既有数据 lake / readiness gate。 |

**处理流程（文字描述）：**
1. 从既有实验和 CR-011 中抽取可复用字段。
2. 补齐因子定义的方向、窗口、可用时点、预处理和 lineage。
3. 为运行层补齐数据 release、评估窗口、成本、benchmark、随机种子和配置哈希。
4. 设计 fail-closed 校验：字段缺失、可用时点不明、数据 lineage 不完整时阻断。
5. 在 HLD 中给出外部项目对象映射，而不是替换内部契约。

---

### UC-23：FactorPanelContract / LabelWindowSpec 与防泄漏校验

| 字段 | 内容 |
|---|---|
| **使用角色** | P-03 因子研究数据审计者 |
| **触发条件** | 因子面板和收益标签需要用于 IC、分层收益、组合构建和准入评估，必须证明不存在未来函数和标签泄漏。 |
| **输入** | 因子值面板；价格 / 收益数据；PIT universe；`available_at`；`decision_time`；label horizon；交易日历；data lineage。 |
| **处理逻辑** | Given 因子面板进入评价或组合, When 校验 `FactorPanelContract`, Then 每行必须包含 `trade_date`、`symbol`、factor value、factor version、`available_at`、source dataset、quality status 和 preprocessing metadata。Given 标签窗口用于收益评价, When 校验 `LabelWindowSpec`, Then 必须记录 `label_window_start`、`label_window_end`、`label_available_at`、收益口径、复权口径和成本口径；任一标签与决策时点重叠或不可证明时阻断。 |
| **输出/结果** | 因子面板契约；标签窗口契约；leakage audit；blocked reason；fixture 验证场景。 |
| **前置条件** | 复用 CR-011 factor panel audit 与 Stage6 label window gate；CP3 只冻结合同和失败策略。 |
| **排除情况** | 不用外部框架自动生成 PIT universe、复权因子或标签 truth；不接受缺少 `available_at` 的字段进入信号。 |

**处理流程（文字描述）：**
1. 对每个因子值建立 `available_at <= decision_time` 校验。
2. 对标签窗口建立 label end 和 label availability 校验。
3. 对 universe、停牌、缺价、无成交、复权口径和成本配置建立 blocked reason。
4. 对外部框架映射只作为参考，不绕过本项目校验。
5. 输出 HLD 级 fixture 列表，供 CP5 LLD 和测试使用。

---

### UC-24：单因子评价报告标准化

| 字段 | 内容 |
|---|---|
| **使用角色** | P-03 因子研究数据审计者；P-07 阶段六多因子模拟盘准入负责人 |
| **触发条件** | 研究者需要判断单个因子是否可靠，并能解释为什么进入或不进入多因子组合。 |
| **输入** | `FactorSpec`；`FactorPanelContract`；`LabelWindowSpec`；benchmark；成本配置；行业 / 市值 / 风格暴露；评估窗口和分层设置。 |
| **处理逻辑** | Given 单因子进入评价, When 输出 `FactorEvaluationReport`, Then 必须包含覆盖率、IC、RankIC、ICIR、分层收益、多空收益、换手、成本敏感性、暴露分析、年度 / rolling / 市场状态分层和 blocked claims。Given 任一必需输入不足, When 生成报告, Then 报告只能声明 `blocked` 或 `research_limited`，不得写成生产级有效因子。 |
| **输出/结果** | 单因子评价报告契约；metrics matrix；声明边界；报告 catalog 入口。 |
| **前置条件** | 因子面板与标签窗口通过校验；HLD 不要求实际计算新报告。 |
| **排除情况** | 不把单一全样本 IC 或收益曲线作为模拟盘准入证据；不覆盖旧实验报告。 |

**处理流程（文字描述）：**
1. 读取因子面板和标签窗口 gate 结果。
2. 设计 IC / RankIC / ICIR、分层收益、多空收益、换手和成本敏感性输出。
3. 设计年度、rolling、市场状态、行业 / 市值 / 风格暴露分层。
4. 对不足项输出 blocked claims 和解除条件。
5. 将报告登记到 experiment manifest / report catalog。

---

### UC-25：多因子组合构建与约束评审

| 字段 | 内容 |
|---|---|
| **使用角色** | P-07 阶段六多因子模拟盘准入负责人；P-03 因子研究数据审计者 |
| **触发条件** | 多个单因子候选需要组合为策略评分、目标权重或候选组合，并接受 benchmark、成本、容量和风险约束审查。 |
| **输入** | 多个通过评价的 `FactorEvaluationReport`；组合配置；benchmark；universe；成本 / 换手 / 容量约束；行业 / 市值 / 风格暴露；调仓频率。 |
| **处理逻辑** | Given 多因子组合进入 HLD, When 设计 `MultiFactorCombiner`, Then 必须说明标准化、winsorization、中性化、正交化、权重学习或规则权重、缺失值处理、约束、调仓、成本、容量和 benchmark 关系。Given 需要 optimizer, When 依赖、风险模型或 benchmark exposure 未冻结, Then optimizer 只能作为后续 Spike，不进入 P0。 |
| **输出/结果** | 多因子组合设计；`MultiFactorPortfolioPlan` 草稿；约束与风险表；optimizer 后置条件。 |
| **前置条件** | 单因子评价报告和输入契约可用；P0 以可解释组合为主。 |
| **排除情况** | 不默认引入 Qlib EnhancedIndexing、cvxpy、vectorbt optimizer 或外部组合优化器；不输出真实交易订单。 |

**处理流程（文字描述）：**
1. 选择 P0 多因子组合方式：可解释的规则权重或轻量线性组合优先。
2. 记录预处理顺序和缺失值策略。
3. 对行业、市值、风格、单票、行业、换手、成本、容量和 benchmark 偏离建立约束。
4. 输出 target portfolio / portfolio plan 草稿，而不是 broker order。
5. 将 optimizer / ML weighting 登记为后续 Spike 条件。

---

### UC-26：ExperimentManifest / ResearchReportCatalog 与 lineage 固化

| 字段 | 内容 |
|---|---|
| **使用角色** | P-03 因子研究数据审计者；P-07 阶段六多因子模拟盘准入负责人 |
| **触发条件** | 研究结果需要可追溯、可复跑、可比较，并能解释不同 run 之间的配置、数据和输出差异。 |
| **输入** | 因子定义；运行配置；数据 release / catalog；label window；评估窗口；成本配置；代码版本；报告路径；allowed / blocked claims。 |
| **处理逻辑** | Given 任一多因子研究 run 生成输出, When 落盘 manifest, Then 必须记录 run_id、strategy_id、配置哈希、输入 release、因子版本、标签窗口、benchmark、成本、随机种子、代码版本、报告路径和 claim boundary。Given 研究报告被后续准入或 QMT 路线引用, When 查询 catalog, Then 必须能找到来源 run、输入数据、blocked claims 和限制项。 |
| **输出/结果** | `ExperimentManifest` 契约；`ResearchReportCatalog` 契约；复跑 / 差异解释策略；报告声明边界。 |
| **前置条件** | 研究闭环采用项目自有契约；HLD 冻结 manifest 字段和 catalog 消费关系。 |
| **排除情况** | 不覆盖旧报告；不把未发布或未通过 readiness 的数据声明为 current truth；不写真实 lake / publish。 |

**处理流程（文字描述）：**
1. 定义 manifest 必填字段和配置哈希。
2. 将因子、标签、数据 release、benchmark、成本和代码版本关联到 run_id。
3. 把报告路径、allowed claims、blocked claims 和 limitations 写入 catalog。
4. 为复跑和差异解释定义最小字段。
5. 将 catalog 输出作为 StrategyAdmissionPackage 的输入之一。

---

### UC-27：StrategyAdmissionPackage 与 QMT handoff 边界

| 字段 | 内容 |
|---|---|
| **使用角色** | P-07 阶段六多因子模拟盘准入负责人；P-05 QMT 交易接入与运行负责人 |
| **触发条件** | 多因子研究结果需要判断是否可申请阶段六模拟盘或后续 QMT 路线，但当前 CR-030 不授权真实 QMT 操作。 |
| **输入** | 多因子组合报告；ExperimentManifest；ResearchReportCatalog；Stage6 admission gate；CR-025 `order_intent_draft_v1` 字段；CR-020..CR-024 route boundary。 |
| **处理逻辑** | Given 多因子研究闭环产出候选策略, When 生成 `StrategyAdmissionPackage`, Then 必须汇总数据、因子、组合、回测、成本、benchmark、稳健性、消融、冻结、pre-sim、5 日 dry-run 前置状态、blocked claims 和解除条件。Given 用户希望进入 QMT, When package 未通过 Stage6 gate 或缺少独立 QMT CR, Then 输出 blocked，不得提交真实 order、simulation、live 或 account query。 |
| **输出/结果** | `StrategyAdmissionPackage` 契约；admission status；blocked reason；`order_intent_draft_v1` handoff boundary；后续 CR 推荐。 |
| **前置条件** | CR-030 只提供研究准入证据；真实 QMT 路线必须由 CR-020..CR-024 单独启动。 |
| **排除情况** | 不生成真实订单；不调用 QMT；不读取账户；不启动 gateway；不把 CP3/HLD approve 解释为 simulation/live 授权。 |

**处理流程（文字描述）：**
1. 从 report catalog 汇总候选策略证据。
2. 对 Stage6 admission gate 建立 pass / warn / fail / blocked matrix。
3. 将可交接对象限定为报告、准入包和 `order_intent_draft_v1` 草稿。
4. 对 QMT simulation/live/account/cancel/query 输出 not-authorized。
5. 推荐后续是否启动 CR-020 或策略准入修复 CR。

### UC-28：QMT / MiniQMT 双目标策略交付框架

| 字段 | 内容 |
|---|---|
| **使用角色** | P-05 QMT 交易接入与运行负责人；P-07 阶段六多因子模拟盘准入负责人 |
| **触发条件** | 研究策略已经进入准入或候选阶段，需要先冻结可同时面向 QMT 终端策略和 MiniQMT / XtQuant 外部 runner 的交付框架，但当前不交付具体策略。 |
| **输入** | CR041 paper simulation 的 `order_intents` / fills / reconciliation 输出；CR042 broker-neutral adapter contract；CR046 正式变更单；用户事实：QMT 已在券商开通、当前无 MiniQMT 权限。 |
| **处理逻辑** | Given 用户要求后续研究策略同时支持 QMT 和 MiniQMT, When CR046 处于 framework-first, Then 系统必须定义统一策略核心合同、目标适配边界、策略包布局、验证证据模型和后续策略交付门禁；不得把框架设计解释为任一具体策略已可运行、可模拟盘或可交易。 |
| **输出/结果** | 双目标策略交付框架设计输入；策略核心合同；QMT terminal target 与 MiniQMT runner target 的边界；后续 CR047 策略交付入口。 |
| **前置条件** | CP2 确认 CR046 只做框架；CP3 冻结架构；CP5 冻结 Story 设计证据；真实运行仍需后续授权。 |
| **排除情况** | 不交付具体交易策略；不执行 QMT shadow / 模拟盘验证；不连接 MiniQMT；不读取账户、资金、持仓、委托或成交；不 submit/cancel；不 simulation/live。 |

**处理流程（文字描述）：**
1. 从研究输出抽象出策略元数据、信号、目标持仓、order intent、风险假设、成本假设和对账证据字段。
2. 将可复用策略核心与目标适配层分离，禁止策略核心直接调用 QMT / XtQuant / MiniQMT API。
3. 为 QMT 终端策略和 MiniQMT runner 定义共同输入输出、配置、日志、报告和失败状态。
4. 将具体策略实现和真实运行验证登记为后续 CR，当前只冻结合同和验证框架。

---

### UC-29：QMT 终端策略包交付形态

| 字段 | 内容 |
|---|---|
| **使用角色** | P-05 QMT 交易接入与运行负责人 |
| **触发条件** | 用户已具备 QMT 终端权限，需要在后续 CR 中能把研究策略导入 QMT 终端运行，但当前仅设计交付形态。 |
| **输入** | 双目标策略核心合同；QMT 终端手工导入约束；配置样例；shadow 报告格式；不授权边界。 |
| **处理逻辑** | Given QMT 终端可由用户在 Windows 上运行, When 交付 QMT terminal target, Then 策略包必须包含终端入口文件、配置样例、导入说明、输入数据格式、shadow 报告、日志规范和人工证据清单；任何 QMT API 调用点必须隔离在 adapter 边界并受后续运行授权控制。 |
| **输出/结果** | `targets/qmt_terminal/` 设计；QMT 终端导入 runbook；shadow 证据格式；运行授权前 fail-closed 规则。 |
| **前置条件** | CR046 框架通过 CP8 后，后续 CR047 选择具体策略并生成策略包；真实终端运行需要独立 runtime_authorization。 |
| **排除情况** | 不在 CR046 内执行终端导入、不运行策略、不读取 QMT 账户、不提交或撤销委托。 |

**处理流程（文字描述）：**
1. 定义终端策略入口如何加载配置和策略核心导出对象。
2. 定义 QMT terminal target 的输入、输出、日志、shadow report 和人工证据字段。
3. 明确终端内策略与策略核心之间的 adapter 边界，禁止业务策略绕过边界直接触达交易 API。
4. 把真实 shadow / 模拟盘步骤写为计划和门禁，不在 CR046 执行。

---

### UC-30：MiniQMT Runner 安装设计与运行边界

| 字段 | 内容 |
|---|---|
| **使用角色** | P-05 QMT 交易接入与运行负责人；P-08 研究执行后端评估者 |
| **触发条件** | 用户未来可能申请 MiniQMT 权限并自研 runner，需要提前冻结 runner 安装、目录、依赖隔离、配置和运行边界。 |
| **输入** | MiniQMT / XtQuant 未来权限前置；Windows runner 目录规范；uv 依赖管理约束；kill switch、日志和报告目录要求。 |
| **处理逻辑** | Given 用户当前没有 MiniQMT 权限, When CR046 设计 runner target, Then 只能定义安装设计和 dry-run 方案，包括 Windows 目录、uv 管理、Python 版本、依赖隔离、配置、启动停止、日志、kill switch、rollback 和 uninstall；不得真实安装 runner、连接 MiniQMT 或调用 xtquant。 |
| **输出/结果** | `targets/miniqmt_runner/` 安装设计；install dry-run 计划；配置和日志目录；权限前置检查；后续 CR049 实机验证入口。 |
| **前置条件** | MiniQMT 权限开通、用户逐 run 授权、runner install manifest、敏感信息不入仓规则。 |
| **排除情况** | 不安装真实 runner；不连接 MiniQMT；不订阅行情；不查询账户；不 submit/cancel；不常驻无人值守运行。 |

**处理流程（文字描述）：**
1. 设计 Windows runner 目录布局、配置文件、日志和报告输出位置。
2. 约定 Python 与依赖由 `uv` 管理，真实安装前必须有 dry-run manifest。
3. 定义 MiniQMT / xtquant 权限、userdata_mini、账户只读和 submit/cancel 的逐层门禁。
4. 设计启动、停止、健康检查、kill switch、rollback 和 uninstall，但不执行真实安装或连接。

---

### UC-31：双目标验证框架与证据模型

| 字段 | 内容 |
|---|---|
| **使用角色** | P-05 QMT 交易接入与运行负责人；P-07 阶段六多因子模拟盘准入负责人；P-03 因子研究数据审计者 |
| **触发条件** | 需要证明框架、策略包合同和安装设计可被静态验证，并为后续真实运行验证预留证据格式。 |
| **输入** | 策略包 schema；fixture 输入输出；QMT terminal shadow 计划；MiniQMT runner install dry-run 计划；不授权清单。 |
| **处理逻辑** | Given CR046 不执行真实终端或 runner, When 验证框架输出, Then 必须覆盖本地 fixture/schema 静态验证、策略包布局校验、QMT shadow 证据模板、MiniQMT install dry-run 证据模板、安全计数和后续 runtime gate；真实 API 调用计数必须为 0。 |
| **输出/结果** | 验证框架设计；证据模型；测试矩阵增量；静态 fixture 计划；后续只读 / submit / cancel 门禁。 |
| **前置条件** | CP3 HLD 冻结目标架构和包结构；CP5 冻结 Story 级验证设计。 |
| **排除情况** | 不运行 QMT；不连接 MiniQMT；不读取凭据或账户；不把 fixture pass 声明为 simulation-ready。 |

**处理流程（文字描述）：**
1. 定义策略包结构、schema 和 fixture 校验项。
2. 定义 QMT terminal shadow 手工验证证据模板，但本 CR 不执行。
3. 定义 MiniQMT runner install dry-run 证据模板，但本 CR 不执行真实安装。
4. 将只读连接、submit/cancel、tick runner 和无人值守运行拆成后续门禁。

---

### UC-32：交易交付框架反向约束研究框架

| 字段 | 内容 |
|---|---|
| **使用角色** | P-03 因子研究数据审计者；P-07 阶段六多因子模拟盘准入负责人；P-08 研究执行后端评估者 |
| **触发条件** | CR046 框架冻结后，需要让后续研究策略天然产出双目标交付所需的元数据、order intents、风险假设和证据。 |
| **输入** | CR030 多因子研究闭环；CR041 paper simulation；CR046 策略核心合同和验证框架；后续 CR051-candidate。 |
| **处理逻辑** | Given 交易交付框架先于具体策略交付冻结, When 研究框架继续完善, Then 后续研究输出必须对齐双目标策略包合同，至少产出策略元数据、数据 lineage、信号日期、目标交易日、目标持仓、order intents、成本 / 风险假设、blocked claims 和验证证据；本 CR 只登记反向约束，不实施研究框架改造。 |
| **输出/结果** | CR051-candidate；研究框架输出合同输入；后续研究准入与策略交付衔接清单。 |
| **前置条件** | CR046 CP8 通过；CR051 启动前完成冲突预检和 CP2。 |
| **排除情况** | 不在 CR046 内改造研究框架代码；不重跑研究；不生成具体策略；不申请模拟盘。 |

**处理流程（文字描述）：**
1. 从 CR046 策略核心合同提取研究输出必须提供的字段和证据。
2. 将缺口登记为 CR051-candidate，而不是混入当前框架 CR。
3. 后续研究框架改造必须继续保留数据湖、PIT、复权、成本、benchmark、admission gate 和不授权边界。
4. CR051 未启动前，不把当前 CR046 输出解释为研究框架已经完成。

---

## CR-046 Scenario Gray Areas

| 灰区 ID | 问题 | 为什么重要 | 用户选择 / 当前处理 | 状态 |
|---|---|---|---|---|
| SGA-046-01 | CR046 是框架 CR 还是具体策略交付 CR？ | 决定是否可以进入实现和运行验证。 | 采用 framework-first：只定双目标框架、验证框架、runner 安装设计和策略包契约。 | decision-item |
| SGA-046-02 | 是否同时保留 QMT 终端和 MiniQMT runner？ | 决定架构复杂度和后续策略包合同。 | 保留双目标；QMT 当前可用，MiniQMT 为未来路线。 | decision-item |
| SGA-046-03 | MiniQMT runner 安装是否进入本 CR？ | 会影响安装目录、uv、依赖隔离和配置合同。 | 进入安装设计和 dry-run 方案；不执行真实安装或连接。 | decision-item |
| SGA-046-04 | 当前是否授权任何真实运行或账户操作？ | 防止 CP2 被误读为运行授权。 | 不授权 QMT 运行验证、MiniQMT 连接、账户查询、submit/cancel、simulation/live。 | decision-item |
| SGA-046-05 | 首个具体策略何时交付？ | 防止框架和策略交付混杂。 | 作为 CR047-candidate，等待 CR046 CP8 后启动。 | decision-item |
| SGA-046-06 | 研究框架完善是否并入本 CR？ | 当前 CR 过大会阻塞交易框架定稿。 | 登记为 CR051-candidate，CR046 只定义反向约束。 | decision-item |

## CR-046 Deferred Ideas

| ID | 想法 / 风险 / 扩展场景 | 来源 | 延后原因 | 重启条件 |
|---|---|---|---|---|
| DEF-046-01 | 首个研究策略双目标交付 | SGA-046-05 | 需要先冻结框架、schema 和验证证据模型。 | CR046 CP8 通过后启动 CR047。 |
| DEF-046-02 | QMT 终端真实 shadow / 模拟盘 submit/cancel 验证 | SGA-046-04 | 需要具体策略包、用户逐 run 授权和运行证据模板。 | CR047 完成策略包后启动 CR048 或等价 runtime gate。 |
| DEF-046-03 | MiniQMT / XtQuant 只读连接与 runner install 实机验证 | SGA-046-03 | 用户当前没有 MiniQMT 权限。 | 权限开通后启动 CR049。 |
| DEF-046-04 | tick 级 MiniQMT runner / 资源控制 Spike | SGA-046-03 | tick 级复杂度和资源风险高，超出框架 first 范围。 | 日频双目标稳定后启动 CR050 Spike。 |
| DEF-046-05 | 研究框架完善 | SGA-046-06 | 需要先确定交易交付框架对研究输出的反向约束。 | CR046 CP8 后启动 CR051。 |

## CR-046 验证场景矩阵

| 测试场景 ID | 验证目标 | 输入 / 前置 | 期望结果 | 来源场景 |
|---|---|---|---|---|
| TS-046-01 | framework-first 范围不越界 | CR046、CP2 Decision Brief、工作区 diff | 只产生框架 / 需求 / 设计 / 验证计划；具体策略交付、真实运行、连接、submit/cancel 计数均为 0 | UC-28 |
| TS-046-02 | 策略核心合同双目标可消费 | 策略元数据、目标持仓、order intents、风险假设样例 | QMT terminal target 和 MiniQMT runner target 都能引用同一核心合同；策略核心不导入 QMT / xtquant | UC-28 |
| TS-046-03 | QMT terminal target 交付形态完整 | 策略包布局、配置样例、runbook、shadow 报告模板 | QMT 终端策略入口、配置、输入输出、日志和人工证据模板均可审查；真实终端运行仍 not-authorized | UC-29 |
| TS-046-04 | MiniQMT runner 安装设计可审查 | Windows 目录、uv、依赖隔离、配置、日志、kill switch、rollback | 安装设计覆盖 install dry-run / uninstall / upgrade / rollback；真实安装、连接和 xtquant 调用均为 0 | UC-30 |
| TS-046-05 | 验证框架不伪造真实证据 | fixture、schema、dry-run 计划、QMT shadow 模板、MiniQMT install 模板 | 本地静态验证和证据模板清晰区分于真实运行；fixture pass 不得声明 simulation-ready | UC-31 |
| TS-046-06 | 后续 CR 分流完整 | CR046 follow-up tracking、CR-INDEX、STATE | CR047..CR051 候选均有状态、阻塞前置、下一步和不授权边界；未提前创建正式 CR 文件 | UC-28, UC-32 |
| TS-046-07 | 研究框架反向约束可追溯 | CR030 合同、CR041 paper output、CR046 策略核心合同 | 后续 CR051 能消费策略元数据、order intent、风险 / 成本假设和验证证据字段；当前不实施研究框架改造 | UC-32 |

## CR-030 Scenario Gray Areas

| 灰区 ID | 问题 | 为什么重要 | 用户选择 / 当前处理 | 状态 |
|---|---|---|---|---|
| SGA-030-01 | CR-030 是自有多因子闭环主线，还是 Qlib-first runner 集成？ | 决定依赖、事实源、数据入口、Story 切分和后续 CR-026 定位。 | 采用项目自有闭环主线；Qlib 作为强参考和后续 isolated runner Spike 输入。 | resolved-by-user |
| SGA-030-02 | 外部项目借鉴面是否足够完整？ | 影响 HLD 准确性和后续方案可解释性。 | Qlib、Alphalens、vectorbt、PyBroker、bt、Zipline Reloaded、QuantConnect LEAN、RQAlpha、vn.py / vnpy.alpha、Backtrader 均进入矩阵。 | resolved-by-user |
| SGA-030-03 | schema 和校验是否需要从零设计？ | 从零设计会带来遗漏和不可验证风险，直接用外部对象又会冲突。 | 不从零设计；以本项目既有研究契约和 gate 为基线，用外部项目 cross-check，fail-closed。 | resolved-by-user |
| SGA-030-04 | 现有 `research_dataset.py` 和实验 17-21 是否复用？ | 重写会产生平行框架和验证债。 | 复用并标准化，HLD 需要指出缺口和兼容策略。 | resolved-by-user |
| SGA-030-05 | CP2/CP3 是否授权运行、安装、clone 外部项目？ | 会扩大许可证、依赖和安全面。 | 不授权；只允许静态分析和过程文档 / HLD。 | resolved-by-user |
| SGA-030-06 | 研究输出能否直接进入 QMT / simulation / live？ | 会绕过 CR-020..CR-024 和 per-run authorization。 | 不允许；只输出报告、准入包和 `order_intent_draft_v1` 草稿边界。 | resolved-by-user |
| SGA-030-07 | Qlib EnhancedIndexing / optimizer 是否纳入 P0？ | 依赖风险模型、optimizer 依赖和 benchmark exposure 数据。 | 不纳入 P0，作为后续组合优化 Spike。 | non-blocking-open |
| SGA-030-08 | vectorbt / PyBroker / RQAlpha 是否可作为实现依赖？ | 许可证、非商业口径和抽象假设需要独立评审。 | 仅静态参考或 optional Spike，不默认依赖。 | non-blocking-open |

## CR-030 Deferred Ideas

| ID | 想法 / 风险 / 扩展场景 | 来源 | 延后原因 | 重启条件 |
|---|---|---|---|---|
| DEF-030-01 | Qlib isolated runner / qrun 执行 | SGA-030-01 | Factor panel、label window、report catalog 和 runner I/O 合同尚未冻结。 | CR-030 合同冻结后，单独启动 CR-026 或 bounded Spike。 |
| DEF-030-02 | Qlib EnhancedIndexing / optimizer | SGA-030-07 | 需要风险模型、cvxpy / optimizer 依赖、benchmark exposure 和组合约束验证。 | 多因子组合 P0 通过后，用户要求组合优化且依赖 / 许可证通过。 |
| DEF-030-03 | vectorbt 性能对标 | SGA-030-08 | 当前尚无批量评价性能瓶颈证据，且许可证 / API 边界需复核。 | 自有实现出现可量化性能瓶颈或批量实验形状不足。 |
| DEF-030-04 | PyBroker ML walk-forward / bootstrap | SGA-030-08 | ML 策略、非商业口径和外部数据入口需要独立边界。 | ML 因子 / 模型策略进入后续 CR。 |
| DEF-030-05 | RQAlpha / vn.py 实盘生态接入 | SGA-030-08 | 与真实交易、gateway、broker 权限和运行治理相关。 | CR-020..CR-024 取得独立授权后再评估。 |
| DEF-030-06 | 真实 provider / lake / publish / QMT 操作 | SGA-030-05/06 | 当前 CP2/CP3 只授权需求和 HLD。 | 后续单独 CR、CP5 和 per-run authorization。 |

## CR-030 验证场景矩阵

| 测试场景 ID | 验证目标 | 输入 / 前置 | 期望结果 | 来源场景 |
|---|---|---|---|---|
| TS-030-01 | 自有闭环主线不被外部框架接管 | CR-030 HLD、外部项目矩阵 | HLD 推荐项目自有多因子闭环；Qlib / Alphalens / Zipline / LEAN 等只作 reference 或 Spike；不得成为默认 truth / runner / provider | UC-20, UC-21 |
| TS-030-02 | 外部项目矩阵完整 | 本地 Qlib 静态分析和公开项目调研 | 至少 10 类项目均有分类、理由、许可证 / 依赖 / 数据 / 运行边界和切换条件 | UC-21 |
| TS-030-03 | schema 与校验不从零设计 | `research_input_v1`、实验 17-21、CR-011、Stage6 gate、外部项目映射 | HLD 输出字段字典、校验规则、错误码、fail-closed 策略和 cross-check 表 | UC-22, UC-23 |
| TS-030-04 | 因子面板和标签窗口防泄漏 | 缺 `available_at`、label overlap、复权混用、lineage 缺失 fixture | 任一前视或 lineage 风险返回 blocked reason；不得进入评价或组合 | UC-23 |
| TS-030-05 | 单因子评价报告可复查 | 合格因子面板、标签窗口、benchmark、成本和暴露数据 | 报告包含 IC、RankIC、ICIR、分层收益、多空收益、换手、成本敏感性、暴露、blocked claims 和分层状态 | UC-24 |
| TS-030-06 | 多因子组合边界清晰 | 多个因子报告和组合配置 | HLD 明确预处理、权重、约束、benchmark、成本、容量、调仓和 optimizer 后置条件 | UC-25 |
| TS-030-07 | manifest / catalog 可追溯 | 研究 run 输出、报告路径和输入 release | 可追溯 run_id、配置哈希、数据 release、因子版本、标签窗口、成本、代码版本、报告路径和 claim boundary | UC-26 |
| TS-030-08 | 策略准入包不授权交易 | StrategyAdmissionPackage、Stage6 gate、QMT route boundary | 只输出 pass/warn/fail/blocked 与 `order_intent_draft_v1` 草稿；真实 QMT/simulation/live/account 操作计数为 0 | UC-27 |
| TS-030-09 | CR-026 分流正确 | CR-019 follow-up、CR-030 Decision Brief、HLD | Qlib isolated runner 保持后续 Spike candidate，不并行启动、不合入 CR-030 P0 实现 | UC-20, UC-21 |
| TS-030-10 | CP3 不越权 | CP3 HLD、Decision Brief、STATE | CP3 approve 只表示 HLD 通过；不授权实现、依赖变更、外部项目运行、provider/lake/publish、QMT/simulation/live 或凭据读取 | UC-20, UC-27 |

## CR-025 Scenario Gray Areas

> 本轮按用户要求优先基于已有上下文完成，不向用户追加提问；灰区采用 CR-025、CR-019 follow-up 台账和既有基线做 desk review，供 meta-po 后续 CP2 Decision Brief 汇总。未生成新的 CP2 人工确认结论。

| 灰区 ID | 问题 | 为什么重要 | 影响面 | 用户选择 / 当前处理 | 状态 |
|---|---|---|---|---|---|
| SGA-025-01 | Backtrader 是 optional research backend 还是替代 lightweight 主路径？ | 会改变默认入口、回归范围、依赖策略和用户对结果 truth 的理解。 | 范围 / 复杂度 / 验证 / 后续门控 | 采用 optional research backend；lightweight 主路径保留。 | resolved-from-CR |
| SGA-025-02 | Backtrader 依赖是否进入默认安装和默认测试路径？ | 会影响 `pyproject.toml` / `uv.lock`、CI 稳定性和未安装环境体验。 | 复杂度 / 验证 / 交付出口 / 后续门控 | 采用依赖隔离 + lazy import；CP5 前不改依赖。 | resolved-from-CR |
| SGA-025-03 | clean feed 与执行语义差异如何验收？ | 如果缺少 feed gate 和 diff report，Backtrader 可能绕过 PIT、复权、成本或质量边界。 | 范围 / 验证 / 设计 / 测试 | 新增 UC-19、SM-35、SM-36 和 TS-025-03/04。 | resolved-from-desk-review |
| SGA-025-04 | 是否允许真实 broker、QMT、provider、lake 或 publish？ | 会把研究后端误扩展为真实运行授权或数据写入授权。 | 安全 / 权限 / 交付 / 后续门控 | 明确全部不授权；真实计数必须为 0。 | resolved-from-CR |
| SGA-025-05 | CR-025 是开发框架级回测内核，还是服务生产级 research-to-execution 路线？ | 会决定 HLD 是围绕 Backtrader/lightweight 框架迁移，还是围绕研究可信度、回测 / 模拟一致性和 QMT 生产执行三条主线组织。 | 范围 / 架构 / CR tracking / 后续路线 | 采用 production-grade research-to-execution 路线；CR-025 负责研究执行语义对照与 target portfolio / order intent 衔接，QMT 真实执行由 CR-020..CR-024 承接。 | resolved-by-user |

## CR-025 Deferred Ideas

| ID | 想法 / 风险 / 扩展场景 | 来源 | 延后原因 | 重启条件 |
|---|---|---|---|---|
| DEF-025-01 | Backtrader live broker / store /真实 broker 接入 | SGA-025-04 | 当前 CR 只覆盖研究对照，不授权真实 broker 或账户操作。 | 另起独立 CR，明确 broker、账户、权限、风控、回滚和 per-run authorization。 |
| DEF-025-02 | 用 Backtrader 替换 lightweight engine 主路径 | SGA-025-01 | 会重写默认研究路径并扩大回归面，不符合 CR-025 optional backend 定位。 | 只有轻量主路径无法满足已确认核心场景，且 CP2/CP3 明确批准迁移时重启。 |
| DEF-025-03 | Backtrader 触发 provider fetch / lake write / publish | SGA-025-03/04 | 当前数据事实源、publish gate 和 provider 授权均由数据湖流程控制。 | 另起数据 / publish CR，经 CP5 和单次运行授权批准。 |
| DEF-025-04 | 将 Backtrader 对照结果作为 QMT simulation admission pass | SGA-025-01/04 | Backtrader 对照只能解释执行语义差异，不替代阶段六 admission package、5 日 dry-run 或 QMT stage gate。 | 阶段六 admission 另行通过全部 P0 gate，并由 QMT 路线 CR 独立确认。 |
| DEF-025-05 | Backtrader 源码级移植或自研完整事件驱动框架 | SGA-025-05 / CP2 用户补充 | 源码级移植可能引入 GPLv3、维护和回归风险；当前只授权 HLD 分析，不授权实现。 | 若 HLD 推荐任一移植候选，必须列为 CP3 决策项并在 CP5 前取得实现授权；若范围扩大为完整平台，另起 CR。 |
| DEF-025-06 | CR-025 内直接启动 QMT gateway / simulation / live | SGA-025-05 | 会把研究执行语义对照误扩展为真实运行授权，绕过 CR-020..CR-024 阶段门控。 | 用户明确启动 CR-020 或后续 QMT CR，并完成冲突预检、CP2 / CP3 / CP5 和 per-run authorization。 |

## CR-025 验证场景矩阵

| 测试场景 ID | 验证目标 | 输入 / 前置 | 期望结果 | 来源场景 |
|---|---|---|---|---|
| TS-025-01 | lightweight 主路径默认不变 | 未设置 optional backend、Backtrader 未安装、默认研究入口 | 运行仍走 lightweight engine；不导入 Backtrader；轻量主路径结果和既有回归不因 CR-025 改变 | UC-19 |
| TS-025-02 | 依赖隔离和 lazy import | 未安装 Backtrader 的环境、静态导入扫描、可选 backend 初始化 | 主包导入、数据读取、轻量回测和默认测试不失败；optional backend 返回 `backend_unavailable`；CP5 前依赖文件不变 | UC-19 |
| TS-025-03 | clean feed gate | 缺 PIT、缺 `available_at`、复权口径混用、benchmark 或 tradability 缺失的 feed | optional backend 返回结构化 blocked / unavailable；不生成 PIT、不计算复权因子、不联网补数、不绕过 quality gate | UC-19 |
| TS-025-04 | 执行语义差异报告 | 同一 clean feed、同一候选策略、同一成本配置下的 lightweight / Backtrader 对照 | 报告列出成交价、调仓、现金、成本、滑点、税费、净值和差异原因；Backtrader 不替代 production truth | UC-19 |
| TS-025-05 | 无真实 broker / QMT / provider / lake / publish | optional backend 请求、日志、安全计数 | `real_broker_calls=0`、`qmt_api_call=0`、`provider_fetch=0`、`lake_write=0`、`catalog_publish=0`、`credential_read=0` | UC-19 |
| TS-025-06 | 结果标签和声明边界 | Backtrader 对照报告、用户文档、admission package 输入 | Backtrader 输出标记为 research comparison；不得声明为默认研究 truth、QMT admission pass、simulation-ready 或生产级可交易证据 | UC-19 |
| TS-025-07 | CR-025 门控不越级 | CP2 intake、CP3/HLD、CP5/LLD 前置状态 | CP2 前只存在场景/需求/检查/交接；CP5 前不得实现、不得新增依赖、不得真实运行 | UC-19 |
| TS-025-08 | 三条主线 tracking 可见 | CR-019 follow-up tracking、CR-INDEX、STATE tracking、CP2 Decision Brief | 同时展示研究可信度、回测 / 模拟一致性、QMT 生产执行；CR-025、CR-020..CR-024、CR-026..CR-028 均能映射到对应主线 | UC-19 |
| TS-025-09 | target portfolio / order intent 衔接字段完整 | lightweight baseline、Backtrader semantic diff、研究报告输出 | 可交给后续 QMT OMS 评审的 draft 至少包含 strategy_id、run_id、signal_date、target_trade_date、symbol、target_weight/target_qty、research_adjustment_policy、execution_price_policy、cost_config_ref、data_lineage_ref、limitations | UC-19 |
| TS-025-10 | 禁止框架级扩张 | HLD、LLD、Story、实现建议 | 未出现复制 / 移植 Backtrader 源码、自研完整事件驱动框架或把 CR-025 approve 写成 QMT gateway / simulation / live 授权 | UC-19 |
| TS-025-11 | Backtrader 模块级分析可审计 | `/home/hyde/download/backtrader`、LICENSE、module tree、HLD | HLD 包含模块对比表，覆盖 Cerebro、broker/order/trade/position、feed、commission/sizer、analyzer/observer、indicator、store/live broker、plot/writer、samples/tests；每项都有 reference/adapt/migration/exclude 分类、理由、风险和验证策略 | UC-19 |

## CR-019 验证场景矩阵

| 测试场景 ID | 验证目标 | 输入 / 前置 | 期望结果 | 来源场景 |
|---|---|---|---|---|
| TS-019-01 | D1-D7 决策可追溯 | CR-019、clarification log、USE-CASES、REQUIREMENTS | D1-D7 均能追溯到场景、需求和 CP2 discussion；旧 signed file drop 基线保留为 fallback | UC-15, UC-16, UC-17, UC-18 |
| TS-019-02 | 旧失败策略不得包装为模拟盘准入 | production current truth rerun fail、阶段六 admission request | admission result 为 blocked，输出失败策略、缺口、解除条件和新多因子实验路径 | UC-15 |
| TS-019-03 | QMT gateway 完整接口面与默认阻断 | FastAPI capabilities、service config、dry-run order intent、simulation/account/cancel/query 请求 | 完整 QMT endpoint 类别可见；未满足 run mode / stage gate / risk gate / kill-switch / 必要上下文时，simulation/account/reconciliation/kill-switch 等真实转发返回 blocked；真实 QMT 调用计数 0 | UC-16, UC-17 |
| TS-019-04 | simulation endpoint later-gated | simulation submit / cancel 请求、缺失 per-run authorization | 请求被 hard block，列出缺失 stage gate / authorization 字段；不得因服务可用而授权真实 simulation | UC-17 |
| TS-019-05 | 鉴权与日志脱敏 | token / HMAC 候选、错误日志、请求日志样例 | 无 token、账户号、session、cookie、交易密码、`.env` 内容或真实私有路径泄露；鉴权失败不触发 QMT adapter | UC-16, UC-17 |
| TS-019-06 | QMT C/S 部署边界 | local_backtest C 侧 client、Windows QMT S 侧 gateway、绑定地址 / 防火墙方案 | C 侧不直接依赖 xtquant，只通过 REST 调用 S 侧；S 侧作为 Windows 可运行 / 可安装命令部署；公网 / 不受控局域网暴露被阻断 | UC-16 |
| TS-019-07 | signed file drop fallback 限定 | FastAPI 不可达、鉴权失败、部署不满足 | fallback 只产生 dry-run file drop 或 blocked result；不得自动真实 QMT 发单 / 撤单 / 查询 | UC-16, UC-17 |
| TS-019-08 | Backtrader / Qlib / minute / Level2 后置触发 | 用户请求外部框架或高频数据 | 未满足触发条件时写入 Deferred Ideas；不进入阶段六 P0，不新增依赖，不阻断日频多因子 admission 主线 | UC-18 |
| TS-019-09 | QMT 文档仅作能力背景 | 迅投 QMT 系统说明文档、当前项目授权状态 | 文档可作为能力背景引用；不得推断已可操作真实账户、模拟盘、Level2、发单、撤单或账户查询 | UC-16, UC-17, UC-18 |

## CR-014 验证场景矩阵

| 测试场景 ID | 验证目标 | 输入 / 前置 | 期望结果 | 来源场景 |
|---|---|---|---|---|
| TS-014-01 | 全 A since-inception coverage denominator | 全 A universe、每只证券上市 / 存在起始日、当前交易日、交易日历 | 每个 P0 dataset 输出证券数、交易日分母、coverage numerator / denominator、缺口列表和 `required_missing` / pass 状态；不得用自然日或固定快照替代交易日分母 | UC-09 |
| TS-014-02 | 退市与代码变更生命周期 | 含上市、退市 / 摘牌、代码变更、简称变更、交易所 / 板块迁移样例的生命周期记录 | PIT universe 能按 as-of date 返回正确证券身份和状态；缺失生命周期字段时阻断 production current truth 声明 | UC-09 |
| TS-014-03 | P0 dataset 分层和 current pointer | raw / manifest / canonical / gold / quality / catalog 候选产物、quality pass / fail 样例 | validate pass 不自动更新 current pointer；只有显式 publish 后 catalog current pointer 指向新版本，且可追溯 run_id、batch_id、lineage checksum 和 quality report | UC-09 |
| TS-014-04 | 增量刷新与 replay | 已成功批次、失败批次、缺口日期、最近 N 个交易日回补配置、manifest/raw | 默认跳过已成功批次，只补缺口；replay 不触发 provider，不读取凭据，不写 raw，只重放 canonical / quality 候选并保留原 current pointer | UC-09 |
| TS-014-05 | DuckDB 只读候选边界 | HLD 待决策状态、Parquet / catalog 样例、DuckDB 未批准依赖状态 | 需求阶段不修改 `pyproject.toml` / `uv.lock`；DuckDB 仅记录为 read-only query / audit / feature extraction 候选；不得写 `.duckdb` 作为事实源 | UC-09 |
| TS-014-06 | 权限和凭据边界 | 未授权真实执行状态、dry-run、默认测试 | provider fetch、lake write、credential read、legacy data read、old report overwrite 计数均为 0；日志只出现 env var 名称或脱敏 root label，不出现凭据值或真实私有路径 | UC-09 |
| TS-014-07 | claim boundary | limited-window pass、2020-2024 blocked 证据、全历史缺口矩阵 | allowed_claims 不包含未通过审计的全 A since-inception production current truth；blocked_claims 明确列出缺口、证据路径和解除条件 | UC-09 |

## CR-015 / CR-016 / CR-017 验证场景矩阵

| 测试场景 ID | 验证目标 | 输入 / 前置 | 期望结果 | 来源场景 |
|---|---|---|---|---|
| TS-015-01 | 策略不得直接调用 QMT API | 策略目标组合、QMT adapter mock、静态导入扫描或调用审计样例 | 策略层只输出目标组合 / order intent 请求；不得导入或调用 QMT / XtQuant 下单接口；所有 broker 触达必须经过 OMS、risk 和 adapter | UC-10 |
| TS-015-02 | pre-trade hard block | 现金不足、非整手、T+1 不可卖、持仓不可用、重复下单、单票 / 组合超限样例 | 任一规则失败时 order intent 被 hard block，blocked reason 可审计，QMT adapter 调用次数为 0 | UC-10 |
| TS-015-03 | OMS 状态机覆盖 | accepted、partial fill、filled、cancel pending、canceled、rejected、failed、unknown、timeout 的 mock broker event | OMS 产生合法状态迁移，记录 event_time、source、broker_order_ref、retry / manual_review 标记和最终状态；unknown 不被静默当作成功 | UC-10 |
| TS-015-04 | broker lake 与凭据边界 | 未授权真实写入、脱敏 root label、mock broker event、日志样例 | 不写仓库 `data/**` / `reports/**`；不输出 token、账户号、session、cookie、交易密码或 `.env` 内容；只生成 mock / dry-run 审计或写入计划 | UC-10 |
| TS-017-01 | raw / qfq / hfq / returns_adjusted 分层 | `prices_raw`、`adj_factor`、qfq/hfq 派生样例、quality metadata | raw 与 adj_factor 作为事实源；qfq/hfq/returns_adjusted 独立 dataset / view；lineage、source_run_id、batch_id 和 quality status 可追溯 | UC-12 |
| TS-017-02 | qfq as-of 可追溯 | 同一历史日期在不同 `as_of_trade_date` 下的 qfq 生成样例 | qfq 输出必须携带 `as_of_trade_date`、输入 snapshot 和 lineage；不得无声覆盖导致历史价格漂移不可解释 | UC-12 |
| TS-017-03 | 单 run 口径一致与 QMT raw 执行价 | 同一研究 run 混用 raw/qfq/hfq 的输入；order intent 中 qfq/hfq 价格样例 | reader / validation 对混用 fail fast；order intent、委托、成交和对账只接受 `execution_price_policy=raw`，复权价进入执行价时被阻断 | UC-10, UC-12 |
| TS-016-01 | 阶段激活顺序 | `shadow -> simulation -> live_readonly -> small_live -> scale_up` stage gate 样例 | 阶段不可跳过；缺少前置验证、runbook、授权、对账或 CR-017 口径治理时返回 blocked gate result | UC-11 |
| TS-016-02 | runbook 与 per-run 授权 | 模拟盘前 runbook 缺失样例；真实 QMT 操作缺少账户模式、策略、日期、资金上限、回滚策略或审批证据样例 | 模拟盘前无 runbook 时阻断；任何真实 QMT 操作无完整 per-run 授权时调用次数为 0，并输出缺失授权字段 | UC-11 |
| TS-016-03 | 对账与 kill switch | 持仓 / 委托 / 成交 / 资金差异样例、heartbeat fail、人工 kill switch 触发样例 | 盘前 / 盘中 / 盘后对账输出差异和处理责任；kill switch 停止新单、撤可撤单、冻结策略并记录人工接管和恢复条件 | UC-11 |

## CR-018 验证场景矩阵

| 测试场景 ID | 验证目标 | 输入 / 前置 | 期望结果 | 来源场景 |
|---|---|---|---|---|
| TS-018-01 | candidate 与 current truth 隔离 | CR014 S14 `prices` / `adj_factor` candidate、未发布 current pointer | candidate read/query smoke 可以通过，但 production current reader 仍因 `catalog_not_published` 或等价状态阻断；allowed_claims 不包含 production current truth | UC-13 |
| TS-018-02 | P0 dataset group readiness | PIT universe、lifecycle/code-change、ST、停牌、`trade_status`、`prices_limit`、benchmark 行情 / 成分 / 权重、复权派生和 quality/readiness 样例 | 任一 P0 缺口输出 `required_missing` / `blocked_claims`；全部通过时生成 dataset-group release readiness matrix | UC-13 |
| TS-018-03 | Explicit Publish Gate 与 rollback | release approval、quality PASS、previous release、rollback target | 只有 publish gate 更新 current pointer；release summary 字段完整；rollback 可恢复上一 release，不删除 raw/manifest/candidate | UC-13 |
| TS-018-04 | 发布后 read/query smoke | published release、reader 请求、catalog current pointer | reader 只消费已发布 current truth；读不到未发布 candidate；输出 release_id、scope、as_of_trade_date 和 lineage 摘要 | UC-13 |
| TS-018-05 | 生产口径研究重跑 | published release、阶段三到阶段五核心研究重跑配置 | 报告记录 release_id、benchmark、PIT、可交易性、复权口径、blocked claims 和旧 proxy/fixed-snapshot 对比；未通过时不得推荐进入 QMT | UC-14 |
| TS-018-06 | QMT 后置 stage gate | 未 publish / 未重跑 / 重跑失败 / 重跑通过四类状态 | 未 publish 或未重跑通过时 simulation/live_readonly/small_live/scale_up 全部 blocked；通过后仅允许进入下一轮 QMT stage gate 审批，不自动授权真实操作 | UC-14 |

<!-- coverage-checklist: begin -->
## 附录：覆盖自检表

| 维度 ID | 维度名称 | 状态 | 涉及场景 | 备注 |
|---|---|---|---|---|
| D1 | 用户维度 | 已补充 | UC-01 至 UC-32 | 覆盖策略研究者、聚宽候选验证者、因子研究数据审计者、生产数据湖负责人、QMT 交易接入 / 运行负责人、研究口径与交易价格审计者、阶段六多因子模拟盘准入负责人、研究执行后端评估者，以及 CR-046 双目标策略交付框架负责人 |
| D2 | 任务维度 | 已补充 | UC-01 至 UC-32 | 覆盖数据读取、回测、扫描、扩展策略、benchmark 消费、数据准备、生产级因子研究、全 A 数据湖、QMT foundation、阶段激活、复权双视图、publish/rollback、研究重跑、阶段六准入、QMT C/S bridge、Backtrader optional backend、多因子闭环、双目标策略交付框架、QMT terminal target、MiniQMT runner 安装设计、验证框架和研究反向约束 |
| D3 | 动机维度 | 已补充 | UC-02 至 UC-32 | 动机是提高本地研究效率、减少平台等待、升级探索性因子结论、建设可发布可回滚的 production truth，并在接入 QMT、申请模拟盘、引入可选执行后端、多因子闭环和双目标策略交付前降低假 alpha、口径混淆、凭据泄露、未授权 simulation、运行失控、schema 漏洞和框架不一致风险 |
| D4 | 时间维度 | 已补充 | UC-02 至 UC-32 | 明确 2019-2025 回测区间、60 组扫描、rolling/年度分段、since-inception、release `as_of_trade_date`、T 日信号 / T+1 执行、qfq `as_of_trade_date`、QMT 阶段推进、连续 5 个真实交易日 dry-run、后置能力触发时序，以及 CR-046 framework-first、CR047 策略交付和 CR049 MiniQMT 权限后置顺序 |
| D5 | 环境维度 | 已补充 | UC-01 至 UC-32 | 本地 parquet、raw、manifest、quality/catalog、断网消费、外置 lake、catalog current pointer、DuckDB 只读候选、Windows QMT / MiniQMT 节点、FastAPI 本地服务桥接、WSL / Windows 部署边界、外置 broker lake、mock adapter、凭据脱敏边界、Backtrader 未安装环境、本地 Qlib 静态分析路径、QMT terminal package 和 MiniQMT runner 安装边界均已记录 |
| D6 | 方式维度 | 已补充 | UC-02 至 UC-32 | 命令/脚本/Notebook/API 入口将在 HLD 中细化；CSV、typed result、写湖作业、gate result、factor audit panel、P0 分层、Explicit Publish Gate、research rerun、OMS order intent、shadow / dry-run / mock、Backtrader semantic diff、多因子 schema、策略包 schema、install dry-run 和双目标验证证据方式已记录 |
| D7 | 异常维度 | 已补充 | UC-01 至 UC-32 | 覆盖 schema 缺失、复权混用、`available_at` 越界、label overlap、lineage 缺失、缺失价格、无成交、数据源失败、quality fail、PIT 不完整、辅助数据缺失、catalog pointer 污染、publish/rollback 失败、DuckDB 越权写入、凭据未授权、QMT 直连绕过、pre-trade fail、unknown 状态、未授权 simulation、Backtrader 未安装、MiniQMT 权限缺失和 fixture pass 被误读为真实运行证据 |
| D8 | 集成维度 | 已补充 | UC-04 至 UC-32 | 与聚宽验证、策略扩展、`market_data` 写湖、只读 resolver、Backtrader optional backend、Qlib isolated runner、CR-008 `research_input_v1`、CR-010/012/013/014/018 数据湖基线、DuckDB 候选查询层、local_backtest C 侧 client、Windows QMT / XtQuant S 侧 gateway、OMS / adapter / broker lake、lightweight engine、Stage6 admission、QMT terminal target 和 MiniQMT runner target 的边界已记录 |
| D9 | 数据生命周期维度 | 已补充 | UC-09 至 UC-32 | CR-014/018 覆盖全 A 证券生命周期、代码变更、退市、current pointer、增量刷新、replay、publish release、rollback、权限计数和 claim boundary；CR-015/016/017/019/025/030/046 覆盖 broker event、order state、qfq as-of、admission package、dry-run 记录、bridge request、clean feed、semantic diff、factor panel、label window、StrategyAdmissionPackage、策略包合同和验证证据生命周期 |
<!-- coverage-checklist: end -->

## 附录：治理变更记录（可选）

| 版本 | 变更字段 | 旧值 | 新值 | 原因 |
|---|---|---|---|---|
| 1.0 | `target_artifact_type` | 空 | tool | 首次初始化，目标是本地 Python 研究工具 |
| 1.1 | `review_policy` | light | light | Review Round 1 要求修订但不改变治理强度，继续保持 draft |
| 1.5 | `governance_mode` | review-gated | review-gated | CR-011 涉及数据契约、真实源授权和多 Story 依赖，继续通过 CP3/CP4/CP5 门控推进 |
| 1.6 | `review_policy` / `scenario_subject_id` | light / local-daily-backtest-layer | strict / local-backtest-production-data-lake | CR-014 将目标扩展为生产级全历史数据湖，涉及权限、安全、存储布局、DuckDB 候选和多 Story 依赖 |
| 1.7 | `scenario_subject_id` / `review_policy` | local-backtest-production-data-lake / strict | local-backtest-production-data-lake-and-qmt-trading-layer / strict | CR-015 / CR-016 / CR-017 将目标扩展到 QMT 交易接入与复权双视图，涉及外部交易接口、凭据、安全、运行治理和价格口径隔离 |
| 1.8 | `total_use_cases` / `review_policy` | 12 / strict | 14 / strict | CR-018 将优先级切回数据湖 production current truth 闭环，并把 QMT simulation 后置到 publish + 研究重跑通过之后 |
| 1.9 | `total_use_cases` / `review_policy` | 14 / strict | 18 / strict | CR-019 将目标扩展到阶段六多因子模拟盘准入和 Windows QMT FastAPI bridge，仍保持 strict review-gated，并将 signed file drop 降级为 fallback |
| 1.10 | `UC-16` / `SM-29` / `SM-30` | FastAPI bridge / dry-run-only 安全指标 | QMT C/S bridge / 完整 endpoint matrix + 运行门控 | 用户确认 Q40 推荐方案，并补充 QMT 模块必须拆为 local_backtest C 侧 client 与 Windows S 侧 gateway |
| 1.11 | `status` / `total_use_cases` | confirmed / 18 | draft / 19 | CR-025 启动后追加 Backtrader optional backend hardening 场景；旧已确认基线保留，本增量等待 CP2 人工确认 |
