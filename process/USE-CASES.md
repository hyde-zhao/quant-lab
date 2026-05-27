---
status: confirmed
version: "1.6"
confirmed_by: "user"
confirmed_at: "2026-05-26T22:51:23+08:00"
engagement_mode: production
scenario_subject_type: target-artifact
scenario_subject_id: "local-backtest-production-data-lake"
target_artifact_type: tool
governance_mode: review-gated
review_policy: strict
total_use_cases: 9
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

## 用户画像（Personas）

| 画像 ID | 角色名称 | 典型背景 | 核心诉求 | 技术水平 |
|---|---|---|---|---|
| P-01 | 量化策略学习者 / 研究者 | 已跑通过聚宽“实践六”动量策略，希望在本地提高研究效率。这里的“实践六”指用户原始学习路径中的第六个策略实践案例，当前文档只承接其动量选股规则，不绑定任何平台课程实现。 | 用透明、可调试、速度更快的本地工具完成大部分策略研究和参数扫描。 | 中级 |
| P-02 | 策略验证者 | 需要把本地筛出的少量候选参数回填到聚宽做真实性校验。 | 减少平台任务数量，保留最终平台验证。 | 中级 |
| P-03 | 因子研究数据审计者 | 需要把实验 17-21 的固定快照 / proxy 结论升级为可审计的生产级研究输入，并识别哪些声明仍被数据缺口阻断。 | 让因子结论、报告声明、数据 lineage、可交易性和稳健性验证可以被复查、复跑和分层验收。 | 高级 |
| P-04 | 生产数据湖负责人 / 数据工程审计者 | 负责把研究数据湖从 limited-window 结果升级为面向全 A 股全生命周期的生产级 current truth，并对 provider、权限、catalog、回放和声明边界负责。 | 让 A 股证券自存在 / 上市日起至当前交易日的正式数据集可审计、可发布、可回滚、可增量刷新，并能支撑只读查询、审计和特征抽取。 | 高级 |

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

## 治理附录（Governance）

| 字段 | 当前值 | 说明 |
|---|---|---|
| `engagement_mode` | production | 面向目标产物的生产模式 |
| `scenario_subject_type` | target-artifact | 场景主体是本地日频回测工具，而不是元工作流自身 |
| `scenario_subject_id` | local-backtest-production-data-lake | 当前 CR-014 场景真正服务的目标产物已扩展为本地研究工具内的生产级数据湖 |
| `target_artifact_type` | tool | 目标交付是本地 Python 研究工具 / 回测层 |
| `governance_mode` | review-gated | 需求、HLD、Story 计划和 LLD 需要按项目检查点确认 |
| `review_policy` | strict | CR-014 命中生产数据湖、外部数据源、权限、存储布局、DuckDB 技术选型和多 Story 依赖，采用严格评审 |

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

<!-- coverage-checklist: begin -->
## 附录：覆盖自检表

| 维度 ID | 维度名称 | 状态 | 涉及场景 | 备注 |
|---|---|---|---|---|
| D1 | 用户维度 | 已补充 | UC-01, UC-02, UC-03, UC-04, UC-05, UC-06, UC-07, UC-08, UC-09 | 覆盖策略研究者、聚宽候选验证者、因子研究数据审计者，并新增生产数据湖负责人 / 数据工程审计者 |
| D2 | 任务维度 | 已补充 | UC-01, UC-02, UC-03, UC-05, UC-07, UC-08, UC-09 | 覆盖数据读取、回测、扫描、扩展策略、本地 benchmark 消费、Tushare 数据准备补齐、CR-011 生产级因子研究数据准入，以及 CR-014 全 A 全历史数据湖 current truth |
| D3 | 动机维度 | 已补充 | UC-02, UC-03, UC-04, UC-07, UC-08, UC-09 | 动机是提高本地研究效率、减少平台等待、升级探索性因子结论，并把 limited-window 数据湖目标升级为可持续审计的全 A 生产 current truth |
| D4 | 时间维度 | 已补充 | UC-02, UC-03, UC-07, UC-08, UC-09 | 明确 2019-2025 回测区间、60 组扫描、benchmark 覆盖起止、CR-011 rolling/年度分段，并新增自存在 / 上市日起至当前交易日和持续增量刷新 |
| D5 | 环境维度 | 已补充 | UC-01, UC-03, UC-04, UC-07, UC-08, UC-09 | 本地 parquet、raw、manifest、quality/catalog、断网消费、显式写湖、外置 lake、catalog current pointer、DuckDB 只读候选和凭据脱敏边界已记录 |
| D6 | 方式维度 | 已补充 | UC-02, UC-03, UC-04, UC-07, UC-08, UC-09 | 命令/脚本/Notebook 入口将在 HLD 中细化；CSV、typed result、写湖作业、gate result、factor audit panel、P0 分层、publish current pointer 和 replay 方式已记录 |
| D7 | 异常维度 | 已补充 | UC-01, UC-02, UC-03, UC-06, UC-07, UC-08, UC-09 | 覆盖 schema 缺失、复权混用、`available_at` 越界、缺失价格、无成交、数据源失败、quality fail、PIT 不完整、执行价代理、辅助数据缺失、证券生命周期缺口、catalog pointer 污染、DuckDB 越权写入、凭据未授权和 blocked claims |
| D8 | 集成维度 | 已补充 | UC-04, UC-05, UC-07, UC-08, UC-09 | 与聚宽验证、策略扩展、`market_data` 写湖、只读 resolver、Backtrader optional backend、CR-008 `research_input_v1`、CR-010/012/013 数据湖基线和 DuckDB 候选查询层的边界已记录 |
| D9 | 数据生命周期维度 | 已补充 | UC-09 | CR-014 新增全 A 证券生命周期、代码变更、退市、current pointer、增量刷新、replay、权限计数和 claim boundary 覆盖 |
<!-- coverage-checklist: end -->

## 附录：治理变更记录（可选）

| 版本 | 变更字段 | 旧值 | 新值 | 原因 |
|---|---|---|---|---|
| 1.0 | `target_artifact_type` | 空 | tool | 首次初始化，目标是本地 Python 研究工具 |
| 1.1 | `review_policy` | light | light | Review Round 1 要求修订但不改变治理强度，继续保持 draft |
| 1.5 | `governance_mode` | review-gated | review-gated | CR-011 涉及数据契约、真实源授权和多 Story 依赖，继续通过 CP3/CP4/CP5 门控推进 |
| 1.6 | `review_policy` / `scenario_subject_id` | light / local-daily-backtest-layer | strict / local-backtest-production-data-lake | CR-014 将目标扩展为生产级全历史数据湖，涉及权限、安全、存储布局、DuckDB 候选和多 Story 依赖 |
