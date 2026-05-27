---
status: active
created_at: "2026-05-13"
created_by: "meta-pm"
---

# 澄清与调研日志

## 修订记录

| 日期 | 记录人 | 事项 | 结果 |
|---|---|---|---|
| 2026-05-13 | meta-pm | 初始化阶段零快速调研 | 基于用户输入和官方页面核验，形成初始范围判断 |
| 2026-05-13 | meta-pm | Review Round 1 需求阶段整改 | 补齐阶段零结构、状态化 Q-001/Q-002/Q-003，并将 blocking/required 项关联到 USE-CASES/REQUIREMENTS |
| 2026-05-14 | meta-pm | 需求确认前草稿刷新 | 根据 meta-po 交接文件追加 HLD 前必须确认问题 Q-004 至 Q-011，并将复权、时点、缺失数据、非 PIT 股票池和报告 metadata 限制项回写需求草稿 |
| 2026-05-14 | meta-pm | 数据源限速需求刷新 | 根据数据源限速交接文件追加 HLD 前确认问题 Q-012 至 Q-019，并将节流、退避、断点续传、raw 缓存、manifest、质量报告、最近 N 个交易日回补和失败降级回写需求草稿 |
| 2026-05-23 | meta-pm | CR-011 因子研究生产级数据补齐 | 增量新增 UC-08 与 REQ-071 至 REQ-082，保留实验 17-21 旧基线并固化生产级数据准入、因子审计和稳健性验证边界 |
| 2026-05-25 | meta-pm | CR-013 unsupported data 与 claim boundary | USE-CASES 按 CR 决策保持不变；REQUIREMENTS 增量升级到 v1.6，新增 REQ-083 至 REQ-087，固化 2020-2024 full-history 不得外推、真实 VWAP / 分钟执行价 blocked、unsupported register 文档和报告声明边界、无 provider/lake/credential/old data 权限 |
| 2026-05-26 | meta-pm | CR-014 A 股 since-inception 生产级全历史数据湖需求澄清 | 增量新增 UC-09 与 REQ-088 至 REQ-097，保留 CR-010/012/013 旧基线，固化全 A current truth、证券生命周期、P0 分层、catalog current pointer、增量刷新 / replay、DuckDB 只读候选、权限边界和 claim boundary；本增量待 CP2 用户确认 |

## 调研发现（2026-05-26）

### 现有可复用资源

- `process/changes/CR-014-A-SHARE-SINCE-INCEPTION-PRODUCTION-DATA-LAKE-2026-05-26.md` 已批准进入 standard 变更流程，并明确文档处理方式为原文档增量更新：`USE-CASES.md` 保留旧场景基线并新增 A 股 since-inception production data lake 场景，`REQUIREMENTS.md` 保留 REQ-001 至 REQ-087 并追加新需求。
- 现有 `process/HLD-DATA-LAKE.md` 已定义数据湖分层、publish gate、P0 dataset、catalog current truth、consumer 只读边界、CR-013 full-history blocked / unsupported register 边界，可作为后续 HLD 增量输入；本轮不修改 HLD。
- 当前代码事实中已存在 `market_data/lake_layout.py` 的 `raw` / `manifest` / `canonical` / `gold` / `quality` / `catalog` 路径契约，以及 `market_data/catalog.py` 的 JSON catalog current truth 结构；本轮只把这些事实转为需求，不修改代码。
- `.agents/skills/use-case-discovery/SKILL.md`、`requirement-extraction/SKILL.md`、`requirement-clarifier/SKILL.md` 可复用为本轮场景增量、需求提取和澄清问题记录的执行规范。

### 平台能力约束

- 当前目标仍为本地 Python 研究工具 / 生产数据湖，不是 meta-flow 自我开发；`engagement_mode=production`，场景主体为目标产物而非当前工作流。
- CR-014 不授权 provider fetch、真实 lake 写入、凭据读取、旧 `data/**` 读取 / 列出 / 迁移 / 复制 / 比对 / 删除、旧 reports 覆盖或 DuckDB 依赖引入。
- DuckDB 在本阶段只能作为 HLD 待决策的 read-only query / audit / feature extraction 候选能力；不得在需求阶段承诺依赖或用 `.duckdb` 替代 Parquet lake / catalog / manifest。
- meta-pm 本轮写入范围限定为 `process/USE-CASES.md`、`process/REQUIREMENTS.md`、`process/CLARIFICATION-LOG.md`；CP1 / CP2 自动检查文件和人工 checkpoint 由 meta-po 后续发起。

### 对需求的初步影响

- CR-014 将目标从 limited-window / 2020-2024 roadmap 升级为 A 股证券自存在 / 上市日起至当前交易日的 production current truth，必须新增 `UC-09` 和 `REQ-088` 起的需求，而不是覆盖 UC-08 或 REQ-083 至 REQ-087。
- 新需求必须显式处理全 A universe、证券生命周期 / 退市 / 代码变更、P0 dataset 分层、catalog current pointer、增量刷新 / replay、DuckDB 只读候选、权限计数、claim boundary 和可量化验证场景。
- `USE-CASES.md` 与 `REQUIREMENTS.md` 的 CR-014 增量应回到 draft / ready_for_design=false，等待 CP2 用户确认后再进入 HLD。

## 调研发现（2026-05-13）

### 现有可复用资源

- `process/REQUEST.md` 已登记本地日频组合回测层的原始目标、推荐目录、第一版能力、数据路线、框架路线和动量策略核心函数示意。
- `process/INPUT-INDEX.md` 已索引 AKShare 与 RQAlpha 官方依据，可作为数据源风险和后续框架取舍背景。
- 当前需求阶段不复用大型量化框架作为第一版主路径；RQAlpha、Backtrader、vectorbt、bt 仅作为后续迁移或优化候选。
- 当前仓库内已存在 `process/USE-CASES.md` 与 `process/REQUIREMENTS.md` draft，本轮采用增量修订，不替换为新文档。

### 平台能力约束

- 目标平台是本地 Python 研究工具，不是 Claude Code、Codex Skill、OpenClaw 或聚宽自动化集成。
- Python 工程必须遵循项目 uv 规则：依赖声明以 `pyproject.toml` 为准，锁定以 `uv.lock` 为准，执行入口使用 `uv run`，不得提交 `.venv/`。
- 第一版回测与参数扫描主路径必须支持离线执行；前提是当前仓库根下三类 parquet 文件已存在。
- 聚宽在第一版中只作为人工少量候选验证平台；不自动调用、不自动联网、不轮询任务。

### 对需求的初步影响

- 工程根统一为当前仓库根 `/home/hyde/workspace/local_backtest`，原始请求中的示意路径只保留为背景，不作为实施根。
- 数据链路拆为“独立数据准备”和“离线只读回测主路径”；AKShare 拉取可后置为独立脚本或后续 Story。
- 第一版必须显式披露固定成分股快照和幸存者偏差，避免把学习型结果误解为实盘级结论。
- 本地与聚宽的校验目标是方向一致性和差异可解释，不是逐日净值一致。
- 参数扫描规范输出统一为 `reports/momentum_param_sweep_local.csv`，聚宽回填候选清单统一为 `reports/momentum_candidates_local.csv`。

## 阶段零快速调研

### 已核验事实

| 主题 | 结论 | 来源 |
|---|---|---|
| AKShare 定位 | AKShare 是 Python 财经数据接口库，适合学习和研究阶段的数据获取；其声明数据用于学术研究、仅供参考，接口可能受不可控因素影响。 | https://pypi.org/project/akshare/ |
| RQAlpha 定位 | RQAlpha 官方文档将其定位为覆盖数据获取、算法交易、回测引擎、模拟交易、实盘交易到数据分析的程序化交易方案，并强调配置方式和扩展性。 | https://rqalpha.readthedocs.io/zh-cn/develop/ |

### 初始判断

- 当前阶段优先建设项目内轻量日频组合回测层，不引入完整事件驱动框架。
- 第一版数据链路采用“独立数据准备 + parquet 本地缓存 + 回测只读本地缓存”。
- 第一版以动量策略为验收主线，RSI、MACD 作为后续扩展策略。
- 后续 HLD 阶段需要重新核对具体 AKShare 接口字段、复权字段、沪深 300 成分股接口和交易日历接口；这些不在需求阶段提前锁死实现细节。

## 澄清问题状态

| ID | 状态 | 问题 | 默认处理 | 是否阻塞 HLD | 关联需求 |
|---|---|---|---|---|---|
| Q-001 | RESOLVED_DEFAULT | 第一版是否需要自动联网拉取 AKShare 数据，还是先假设 parquet 已存在？ | 第一版回测/扫描主路径只读本地 parquet、manifest 和质量报告摘要；联网能力只能存在于独立数据准备/更新流程，且该流程必须节流、有限重试、断点续传和输出 raw/manifest/质量报告。 | 否；HLD 需要同时设计离线回测主路径和独立数据准备入口，但不得把联网能力放入回测/扫描/候选筛选主路径。 | REQ-016, REQ-021, REQ-034, REQ-047 - REQ-057 |
| Q-002 | RESOLVED_FOR_HLD | 手续费、滑点、印花税的默认费率是否固定为某组值？ | 成本接口和扣除规则已定：使用 `commission_rate`、`slippage_rate`、`sell_tax_rate`；默认费率可在 HLD/LLD 作为显式配置确认，报告必须记录实际值。 | 否；费率默认值待 HLD/LLD 显式配置确认，但不阻塞 HLD。 | REQ-009, REQ-035 |
| Q-003 | RESOLVED_DEFAULT | 本地回测结果与聚宽校验的“方向一致”如何量化？ | 不要求逐日净值一致；比较候选排序方向、收益/回撤量级、换手特征和差异解释。 | 否；已形成验收口径。 | REQ-030, RA-006 |
| Q-004 | REQUIRED_FOR_HLD | 默认复权口径采用前复权、后复权还是不复权？本地回测与聚宽候选验证是否必须使用同一口径？ | 暂不指定默认值；需求只固化“同一运行口径一致、不得混用、报告 metadata 记录实际口径”。 | 是；HLD 必须给出默认复权口径、配置项和报告字段。 | REQ-037, RA-007 |
| Q-005 | REQUIRED_FOR_HLD | 第一版成交假设如何定义：T+1 开盘、T+1 收盘、VWAP 近似，还是仅按收盘到收盘收益归属？ | 暂定硬约束为 T 日收盘后生成信号、T+1 或之后成交；成交价口径和收益归属待 HLD 确认。 | 是；HLD 必须定义成交价、成交日期、成本扣除和收益归属。 | REQ-005, REQ-008, REQ-023 |
| Q-006 | REQUIRED_FOR_HLD | 股票池表达采用固定当前沪深 300 快照文件，还是需要在第一版引入日期维度或 PIT 接口占位？ | 第一版按固定当前沪深 300 快照处理，并标记 `is_pit_universe=false` 与幸存者偏差；PIT universe provider 列为后续 P1 增强。 | 是；HLD 必须确定 `index_members.parquet` schema、快照日期字段和未来 PIT 扩展点。 | REQ-003, REQ-031, REQ-042 |
| Q-007 | REQUIRED_FOR_HLD | 缺失价、停牌和无成交如何处理：剔除、留现金、延后成交、失败，还是按不同场景分层处理？ | 当前需求禁止静默填充；历史窗口不足和信号端点缺失剔除，成交价缺失或无成交留现金/记录未成交/失败的细分规则待 HLD 确认。 | 是；HLD 必须给出数据加载、信号排名和组合成交三层处理表。 | REQ-006, REQ-008, REQ-039, REQ-040 |
| Q-008 | REQUIRED_FOR_HLD | 第一版 parquet 数据字段最低要求是否强制包含 `available_at`、`adjustment_policy`、成交状态或成交量？ | 当前需求允许日线价格在 HLD 批准后用“收盘后可用”规则推导 `available_at`；事件字段第一版默认不纳入。最低字段集仍需 HLD 确认。 | 是；HLD 必须明确最小 schema、可选字段和缺字段失败行为。 | REQ-021, REQ-037, REQ-038 |
| Q-009 | REQUIRED_FOR_HLD | 涨跌停字段是否第一版强制输入？若不强制，报告限制项和候选聚宽验证如何表达该偏差？ | 当前需求将涨跌停撮合列为第一版可延后但必须警示；涨跌停约束作为后续 P1 增强。 | 是；HLD 必须决定涨跌停字段是否进入第一版 schema 或仅进入 metadata 限制项。 | REQ-015, REQ-041, REQ-044 |
| Q-010 | REQUIRED_FOR_HLD | 未来函数校验做到哪个层级：数据加载层、信号层、股票池层、事件层、报告审计层，还是全部覆盖？ | 当前需求要求所有参与决策字段满足 `available_at <= decision_time`；具体校验层级和错误策略待 HLD 确认。 | 是；HLD 必须定义校验边界、失败策略和测试样例。 | REQ-038, REQ-045, RA-008 |
| Q-011 | REQUIRED_FOR_HLD | 财报披露日和财报/公告事件是否明确列为第一版 Out of Scope？ | 当前需求默认财报披露日和事件字段第一版 Out of Scope；若纳入则必须提供事件级 `available_at` 并调整需求范围。 | 是；HLD 前需确认是否保持 Out of Scope，以免设计阶段误引入事件数据。 | REQ-015, REQ-041, REQ-045, A-009 |
| Q-012 | REQUIRED_FOR_HLD | 数据准备默认节流参数如何取值：`request_interval_seconds`、`batch_size`、`max_concurrency` 的默认值分别是多少？ | 当前需求只固化三项均可配置，且默认保守串行抓取；`max_concurrency` 建议默认 1，但默认值仍待 HLD 前确认。 | 是；HLD 必须给出默认节流参数、配置位置和覆盖测试方式。 | REQ-047, REQ-048, REQ-049 |
| Q-013 | REQUIRED_FOR_HLD | `max_retries` 默认上限和 `backoff_policy` 采用固定退避还是指数退避？退避细节记录到 manifest 还是日志？ | 当前需求只固化重试必须有限、不可无限循环，且退避过程必须可记录到 manifest 或日志。 | 是；HLD 必须定义默认重试次数、退避算法、最大等待边界和记录字段。 | REQ-050, REQ-055 |
| Q-014 | REQUIRED_FOR_HLD | 断点续传状态由 manifest、独立 checkpoint 文件还是二者共同承载？批次状态枚举如何定义？ | 当前需求只固化断点续传必须基于 manifest/checkpoint，跳过已成功批次，除 `force_refresh` 或最近 N 交易日回补外不重复抓取。 | 是；HLD 必须定义 checkpoint 载体、批次 ID、状态枚举和恢复算法。 | REQ-051, REQ-055 |
| Q-015 | REQUIRED_FOR_HLD | 最近 N 个交易日回补的默认 N 取值是多少，是否对价格、复权因子、成分股和交易日历采用同一窗口？ | 当前需求只固化 N 可配置，且必须基于交易日历而不是自然日。 | 是；HLD 必须给出默认 N、适用数据类型和与增量缺口补齐的优先级关系。 | REQ-053, REQ-054, A-012 |
| Q-016 | REQUIRED_FOR_HLD | raw 缓存保留策略是什么：长期保留、按批次滚动保留、按大小清理，还是由用户手动清理？ | 当前需求只固化 raw 缓存必须存在，标准化 parquet 必须可从 raw 派生；保留周期和清理策略待确认。 | 是；HLD 必须定义 raw 路径组织、命名、保留/清理策略和复现边界。 | REQ-052, RA-012 |
| Q-017 | REQUIRED_FOR_HLD | manifest schema 的文件格式、字段类型、路径、状态枚举和版本字段如何定义？ | 当前需求已列出 manifest 至少记录字段，但未锁定 JSON、JSONL、YAML 或 parquet 等具体格式。 | 是；HLD 必须定义 manifest schema、兼容升级规则和与质量报告的关联方式。 | REQ-051, REQ-055 |
| Q-018 | REQUIRED_FOR_HLD | 数据质量报告阈值如何定义：缺失率、失败率、重复记录、异常价格达到什么条件时阻塞数据准备或仅警告？ | 当前需求只固化质量报告必须记录统计和异常定位；阻塞阈值与质量状态枚举待确认。 | 是；HLD 必须定义质量阈值、`quality_status` 枚举、失败/警告策略和报告字段。 | REQ-056, RA-012 |
| Q-019 | REQUIRED_FOR_HLD | 数据源不可用时，本地缓存新鲜度如何披露：按自然日、交易日、最近成功批次还是覆盖区间缺口计算？ | 当前需求只固化本地 parquet 合规时回测/扫描继续离线运行，并披露最近成功更新时间、数据新鲜度、失败批次和可能影响。 | 是；HLD 必须定义新鲜度计算方式、报告展示字段和不可用数据源的降级提示。 | REQ-034, REQ-057 |
| Q-020 | REQUIRED_FOR_CP2 | CR-014 的全 A universe 覆盖边界是否包含沪深北全部 A 股、科创板、创业板、北交所、退市 / 摘牌证券和历史代码变更？ | 默认按“全 A 证券自存在 / 上市日起至当前交易日”处理，并要求生命周期缺口进入 `required_missing` / `blocked_claims`。 | 是；CP2 未确认前不得进入 HLD。 | REQ-088, REQ-089, RA-026, RA-027 |
| Q-021 | REQUIRED_FOR_CP2 | CR-014 P0 dataset 清单是否沿用 `prices`、`adj_factor`、`hs300_index`、`trade_calendar`、`index_members`、`index_weights`、`stock_basic`，并新增 lifecycle / code-change 能力为 P0？ | 默认沿用 CR-010 P0 dataset，并把生命周期 / 代码变更作为全 A current truth 的必需能力；W3 / minute / tick / Level2 仍需单独决策。 | 是；CP2 未确认前不得进入 HLD。 | REQ-090, REQ-096 |
| Q-022 | REQUIRED_FOR_CP2 | “当前交易日”是否定义为最近已闭市交易日，还是允许盘中 / 当日未闭市数据进入 current truth？ | 默认采用最近已闭市且交易日历 `is_open=true` 的交易日；盘中或未闭市数据不进入 production current truth。 | 是；CP2 未确认前不得进入 HLD。 | REQ-088, REQ-097 |
| Q-023 | REQUIRED_FOR_CP2 | DuckDB 是否只作为 read-only query / audit / feature extraction 候选，且依赖引入必须等 HLD/CP3/CP5 决策？ | 默认只读候选，不新增依赖，不写 `.duckdb` 事实源，不替代 Parquet lake / catalog / manifest。 | 是；CP2 未确认前不得进入 HLD。 | REQ-093, RA-030 |
| Q-024 | REQUIRED_FOR_CP2 | CR-014 后续真实 provider fetch、真实 lake 写入、凭据读取、旧 `data/**` 操作和旧 reports 覆盖是否均需单独授权？ | 默认全部保持 0；任何真实执行必须由后续 Story / CP5 和用户显式授权控制。 | 是；CP2 未确认前不得进入 HLD 或实现。 | REQ-094, REQ-095, RA-031 |

## 2026-05-14 需求刷新摘要

| 类别 | 纳入内容 | 落点 |
|---|---|---|
| 第一版硬约束 | 复权口径一致；T 日收盘后生成信号、T+1 或之后成交；`available_at <= decision_time`；历史窗口不足剔除；缺失价格或无成交不得静默填充；固定当前沪深 300 股票池标记非 PIT 和幸存者偏差；报告 metadata 强制输出限制项。 | `process/USE-CASES.md` v1.2；`process/REQUIREMENTS.md` v1.2 |
| 第一版警示项 | 完整停牌状态、涨跌停撮合、新股上市初期特殊规则、退市整理/摘牌、ST 历史状态、财报披露日、沪深 300 历史成分变化。 | `USE-CASES.md` Out of Scope、边界说明、UC-01/UC-02/UC-06；`REQUIREMENTS.md` REQ-015、REQ-041、风险与假设 |
| 后续增强优先级 | PIT universe provider、交易状态表、涨跌停约束、事件 `available_at`、偏差审计报告。 | `USE-CASES.md` UC-06；`REQUIREMENTS.md` REQ-042 至 REQ-046、M3 |
| HLD 前确认项 | 默认复权口径、成交假设、股票池表达、缺失价/停牌处理、数据字段最低要求、涨跌停字段是否强制、未来函数校验层级、财报是否第一版 Out of Scope。 | Q-004 至 Q-011，状态均为 `REQUIRED_FOR_HLD` |

## 2026-05-14 数据源限速刷新摘要

| 类别 | 纳入内容 | 落点 |
|---|---|---|
| 数据链路边界 | 数据准备/更新流程可联网；回测、扫描、候选筛选和本地差异分析主路径必须物理隔离并离线只读本地 parquet、manifest 和质量报告摘要。 | `process/USE-CASES.md` v1.3 边界说明、UC-01、UC-03；`process/REQUIREMENTS.md` v1.3 REQ-016、REQ-034、REQ-057 |
| 数据源限速与节流 | 数据准备默认保守串行抓取，支持 `request_interval_seconds`、`batch_size`、`max_concurrency`，且相邻请求间隔必须可验证。 | `USE-CASES.md` UC-01；`REQUIREMENTS.md` REQ-047 至 REQ-049 |
| 重试退避与断点续传 | `max_retries` 必须有上限，`backoff_policy` 必须可记录；断点续传基于 manifest/checkpoint，不重复已成功批次，除非强制刷新或最近 N 个交易日回补。 | `USE-CASES.md` UC-01；`REQUIREMENTS.md` REQ-050、REQ-051 |
| raw 缓存与增量更新 | raw 缓存必须存在，标准化 parquet 必须可从 raw 派生；默认只补缺口，并支持基于交易日历的最近 N 个交易日回补。 | `USE-CASES.md` UC-01；`REQUIREMENTS.md` REQ-052 至 REQ-054 |
| manifest 与质量报告 | manifest 记录批次、数据源、接口、请求参数、范围、请求时间、成功项、失败项、错误信息、重试次数、raw 路径、标准化输出路径、覆盖范围和最终状态；质量报告记录覆盖、缺失、失败、字段缺失、重复、异常价格、回补数量、最近成功更新时间和数据新鲜度。 | `USE-CASES.md` UC-01、UC-03、UC-06；`REQUIREMENTS.md` 数据准备产物契约、报告 schema、REQ-055、REQ-056 |
| 失败降级 | 数据源不可用时，若本地 parquet 覆盖区间和 schema 合规，回测/扫描/候选筛选仍可离线运行，并披露失败项与新鲜度。 | `USE-CASES.md` 边界说明、UC-03；`REQUIREMENTS.md` REQ-034、REQ-057、RA-010、RA-011 |
| HLD 前确认项 | 默认节流参数、重试次数/退避策略、断点续传状态承载、最近 N 日回补默认值、raw 缓存保留策略、manifest schema、质量报告阈值、数据源不可用时的新鲜度披露。 | Q-012 至 Q-019，状态均为 `REQUIRED_FOR_HLD` |

## Review Round 1 整改摘要

| 类别 | 处理结果 | 落点 |
|---|---|---|
| 场景补强 | 补齐 UC-04 差异分析输出、本地/聚宽/平台边界、固定成分股快照和幸存者偏差、第一版离线只读 parquet 主路径。 | `process/USE-CASES.md` v1.1 |
| 成功指标 | 修订 SM-05 为可验收的扫描耗时记录和平台任务减少指标；解释“实践六”和“方向一致”。 | `process/USE-CASES.md` v1.1 |
| 覆盖自检 | D1 补齐 UC-05/UC-06。 | `process/USE-CASES.md` v1.1 |
| 需求补强 | 补齐工程根、路径归属、数据 schema、`close_df`、交易日序、无前视偏差、成本模型、指标假设、扫描 CSV、候选清单、过拟合警示和报告边界。 | `process/REQUIREMENTS.md` v1.1 |
| 澄清项 | Q-001/Q-002/Q-003 均已状态化，不存在未处理的开放澄清项。 | 本文件 |

## 2026-05-23 CR-011 场景与需求增量摘要

| 类别 | 纳入内容 | 落点 |
|---|---|---|
| 用户真实意图 | 用户希望把实验 17-21 的探索性结论从 fixed snapshot / proxy benchmark / close proxy 升级为可审计、可复现、可分层验证的生产级因子研究输入；旧结论不删除，只保留为历史 baseline。 | `process/USE-CASES.md` v1.5 UC-08；`process/REQUIREMENTS.md` v1.5 REQ-071 至 REQ-082 |
| 候选理解与取舍 | 候选 A：只补真实 `hs300_index`，成本低但仍无法支撑生产级因子结论；候选 B：同时补 benchmark、PIT、可交易性、执行价、复权/公司行动、行业市值风格、容量成本、因子审计和稳健性验证，范围更大但与 CR-011 目标一致。本轮采用候选 B。 | `process/USE-CASES.md` UC-08；`process/REQUIREMENTS.md` CR-011 生产级因子研究数据契约 |
| 推荐范围 | Scope 为生产级因子研究数据准入、声明门控、新版报告产物和安全授权边界；Out of Scope 为覆盖旧报告、需求阶段真实联网/写湖/凭据读取、超出 readiness 覆盖窗口的完整历史 PIT 或生产 current truth 声明。 | `process/USE-CASES.md` Out of Scope / UC-08；`process/REQUIREMENTS.md` 明确排除项 |
| 成功指标 | 新增 SM-10 至 SM-13，覆盖生产级准入、因子审计面板完整性、稳健性验证覆盖和真实数据授权/凭据边界。 | `process/USE-CASES.md` 成功指标；`process/REQUIREMENTS.md` REQ-071 至 REQ-082 |
| 风险与影响 | 主要风险为只补局部数据导致旧结论被误升级、limited window 被外推、辅助数据缺失却声明中性化/容量可交易、因子预处理不可审计、真实执行泄露凭据或误写 lake。 | `process/REQUIREMENTS.md` RA-016 至 RA-021 |
| 待 meta-se 消费 | HLD 需要冻结 CR-011 数据域 gate、执行价策略、行业/风格/容量模型、factor audit panel schema、稳健性验证矩阵、报告产物路径和真实执行授权边界；CP3/CP4 通过前不得进入 LLD，CP5 批次确认前不得实现代码。 | 后续 `process/HLD.md` / `process/HLD-DATA-LAKE.md` / ADR / Story Plan |

## 2026-05-25 CR-013 需求增量摘要

| 类别 | 纳入内容 | 落点 |
|---|---|---|
| 用户真实意图 | 用户已批准将 CR-013 的 unsupported data 与 claim boundary 纳入需求基线，防止 CR-012 limited-window pass 被误外推为 2020-2024 或全历史生产级可用。 | `process/REQUIREMENTS.md` v1.6 REQ-083 |
| 声明边界 | 2020-2024 readiness 仍为 `research_limited_only`，10 个正式 dataset 均为 `limited_window_only`；真实 VWAP / VWAP fill / 分钟执行价仍为 blocked。 | `process/REQUIREMENTS.md` v1.6 REQ-083, REQ-084 |
| unsupported register | `unsupported_data_register.csv` 中 research-only、unsupported、contract-supported-but-unavailable 项必须进入用户文档和报告声明边界，且 `pass_denominator=excluded` 不得计入生产级 pass。 | `process/REQUIREMENTS.md` v1.6 REQ-085 |
| 权限边界 | 本轮不授权 provider fetch、真实 lake 写入、凭据读取、旧 `data/**` 读取或旧报告覆盖；后续真实补数或数据接入必须另行显式授权。 | `process/REQUIREMENTS.md` v1.6 REQ-086, REQ-087 |

## 2026-05-26 CR-014 场景与需求增量摘要

| 类别 | 纳入内容 | 落点 |
|---|---|---|
| 用户真实意图 | 用户要把数据湖目标从 limited-window / roadmap-only 升级为生产级 A 股全历史数据湖，覆盖 A 股证券自存在 / 上市日起至当前交易日的可审计 current truth，而不是继续停留在 2020-2024 blocked 或 2025-2026 limited-window 通过声明。 | `process/USE-CASES.md` v1.6 UC-09；`process/REQUIREMENTS.md` v1.7 REQ-088 |
| 候选理解与取舍 | 候选 A：只扩展 2020-2024 roadmap，改动小但仍不能支撑用户要求的全 A since-inception current truth；候选 B：定义全 A universe、证券生命周期、P0 分层、catalog current pointer、增量刷新 / replay 和 claim boundary，范围更大但与 CR-014 目标一致。本轮采用候选 B。DuckDB 作为候选查询 / 审计能力纳入 HLD 待决策，不在需求阶段承诺依赖。 | `process/USE-CASES.md` UC-09；`process/REQUIREMENTS.md` REQ-088 至 REQ-097 |
| 推荐范围 | Scope 为全 A since-inception current truth 范围、证券生命周期 / 退市 / 代码变更、P0 dataset 分层、catalog current pointer、增量刷新 / replay、DuckDB 只读候选、权限计数、claim boundary 和 TS-014 验证矩阵；Out of Scope 为本阶段真实抓取、写湖、凭据读取、旧 `data/**` 操作、旧报告覆盖、DuckDB 依赖修改和 `.duckdb` 事实源替代。 | `process/USE-CASES.md` Out of Scope / UC-09；`process/REQUIREMENTS.md` 明确排除项 |
| 成功指标 | 新增 SM-14 至 SM-18，覆盖全 A since-inception current truth 可声明性、证券生命周期覆盖、P0 分层与 current pointer 可审计、增量刷新 / replay 稳定性和 DuckDB 候选边界。 | `process/USE-CASES.md` 成功指标；`process/REQUIREMENTS.md` REQ-088 至 REQ-097 |
| 测试场景 | 新增 TS-014-01 至 TS-014-07，覆盖全 A coverage denominator、退市 / 代码变更、P0 分层 / current pointer、增量刷新 / replay、DuckDB 只读边界、权限计数和 claim boundary。 | `process/USE-CASES.md` CR-014 验证场景矩阵；`process/REQUIREMENTS.md` REQ-096 |
| 风险与影响 | 主要风险为 universe 边界未冻结、生命周期缺口导致幸存者偏差、validate pass 污染 current pointer、replay 误触发 provider、DuckDB 被误解为已批准依赖或事实源、权限边界被误读为真实执行授权。 | `process/REQUIREMENTS.md` RA-026 至 RA-031 |
| 待 CP2 用户确认 | 需要确认全 A 覆盖边界、P0 dataset 清单、当前交易日口径、DuckDB 只读候选定位、以及真实 provider / lake / credential / old data / reports 操作均需单独授权。 | Q-020 至 Q-024 |

### CP2 Decision Brief 输入（CR-014）

| 字段 | 内容 |
|---|---|
| 用户真实意图 | 建设生产级 A 股全历史数据湖，使全 A 证券从存在 / 上市日起至当前交易日的 P0 数据、生命周期、catalog current pointer、增量刷新和声明边界可审计、可重放、可持续维护。 |
| 候选理解与取舍 | 候选 A 是继续补 2020-2024 / limited-window 缺口，优点是范围小，缺点是不能满足全 A since-inception current truth；候选 B 是升级为全 A production data lake，优点是匹配用户目标，缺点是需要 HLD/Story/权限/测试全链路重做。本轮推荐候选 B。DuckDB 只作为 HLD 待决策候选，不作为本阶段依赖承诺。 |
| 推荐范围 | 纳入全 A universe、证券生命周期、P0 分层、catalog current pointer、增量刷新 / replay、DuckDB 只读候选、权限边界和 claim boundary；排除真实抓取、写湖、凭据读取、旧数据操作、旧报告覆盖、DuckDB 依赖修改和实现级代码变更。 |
| 成功指标 | SM-14 至 SM-18；验收口径为 P0 coverage numerator / denominator、生命周期缺口、current pointer publish、replay no-provider/no-credential、权限计数 0、DuckDB dependency_changes=0、blocked_claims 完整。 |
| 风险与影响 | 若 CP2 不确认覆盖边界和 P0 清单，HLD 无法冻结 dataset / Story；若 DuckDB 角色不清，可能引入不必要依赖或事实源冲突；若权限边界不清，可能误触发真实 provider / lake / credential / old data 操作。 |
| 待用户决策 | Q-020 全 A 覆盖边界；Q-021 P0 dataset 清单；Q-022 当前交易日口径；Q-023 DuckDB 只读候选定位；Q-024 真实执行授权边界。 |

### CR-014 默认假设

| ID | 默认假设 | 关联需求 |
|---|---|---|
| A-021 | “当前交易日”默认指最近已闭市且交易日历 `is_open=true` 的交易日，最终口径待 CP2/HLD 确认。 | REQ-088, REQ-097 |
| A-022 | P0 dataset 默认沿用 CR-010 的 7 个 P0 dataset，并把生命周期 / 代码变更作为全 A current truth 必需能力，最终清单待 CP2/HLD 决策。 | REQ-089, REQ-090 |
| A-023 | DuckDB 默认只作为 HLD 待决策的 read-only query / audit / feature extraction 候选，不进入需求阶段依赖。 | REQ-093 |
| A-024 | 本轮只修改 `process/USE-CASES.md`、`process/REQUIREMENTS.md`、`process/CLARIFICATION-LOG.md`。 | REQ-094 |
| A-025 | 未经后续单独授权，provider fetch、真实 lake 写入、凭据读取、旧 `data/**` 操作、旧 reports 覆盖和 DuckDB 依赖修改均保持 0。 | REQ-094, REQ-095 |
