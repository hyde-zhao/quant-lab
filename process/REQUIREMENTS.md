---
status: confirmed
version: "1.7"
confirmed: true
confirmed_by: "user"
confirmed_at: "2026-05-26T22:51:23+08:00"
ready_for_design: true
source_use_cases: [UC-01, UC-02, UC-03, UC-04, UC-05, UC-06, UC-07, UC-08, UC-09]
review_round: 3
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
| DuckDB 只读查询 / 审计候选 | CR-014 HLD 待决策能力 | 仅用于评估 read-only Parquet / catalog 查询、coverage audit、PIT join、feature extraction 和 parity；需求阶段不得新增依赖或写 `.duckdb` 事实源 | P1（CR-014，待 HLD 决策） |

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

## 目标平台

- [x] 本地 Python 研究工具
- [ ] Claude Code
- [ ] Codex
- [ ] OpenClaw
