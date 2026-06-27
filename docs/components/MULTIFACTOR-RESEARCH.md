# 组件说明：多因子研究

多因子研究组件覆盖 FactorSpec、FactorRunSpec、factor panel、label window、单因子评价、多因子组合和 StrategyAdmissionPackage。它输出“策略准入输入”，不输出真实交易许可。

## 1. 核心对象

| 对象 | 说明 | 检查 |
|---|---|---|
| `FactorSpec` | 因子定义、方向、依赖和 lineage。 | 字段完整、方向明确、无外部 truth 混入。 |
| `FactorRunSpec` | 一次因子运行的窗口、数据源和权限计数。 | run_id、date range、permission counters。 |
| factor panel | 因子值矩阵。 | no-lookahead、缺失、winsorize、zscore。 |
| label window | 未来收益或目标标签窗口。 | label 不重叠、available_at 合法。 |
| evaluation report | IC / RankIC / 分层收益 / turnover / cost / exposure。 | 指标齐全，blocked claims 优先。 |
| portfolio plan | 多因子组合权重和候选持仓。 | max weight、turnover、capacity、risk。 |
| admission package | 模拟盘入口审查输入。 | 证据 refs、限制、授权状态、handoff。 |
| `StrategyTypeAdapter` | Stage 2 起新增的策略类型适配合同。 | 多因子输出必须归一到 `SignalSet` / `StrategyCandidate` / `ResearchEvidenceIndex`。 |
| `SignalSet` | 策略信号集合。 | signal、available_at、universe_ref、lineage_ref、not_order。 |
| `StrategyCandidate` | 项目级策略候选合同。 | 统一 CR039 候选、`SignalSet`、`ResearchEvidenceIndex` 与风控策略引用。 |
| `ResearchEvidenceIndex` | 研究证据索引。 | data release、manifest、metric refs、lineage refs、typed unavailable。 |
| `PortfolioRiskPolicy` | 成熟策略组合风控策略。 | top_n、max_weight、turnover、行业 / 风格 / 容量 / 费用 / 停止条件。 |
| mature admission support | Stage 2 no-lake 的成熟准入支撑包。 | 不代表 runtime / simulation / live 授权。 |
| Stage 3 research machine handoff | 研究机交接合同。 | 明确真实数据湖输入、evidence、验证计划和运行边界。 |

## 2. 输出边界

多因子研究的出口是 `StrategyAdmissionPackage` 或等价策略准入包。它可以交给 runner 做导入检查，但不能直接下单，也不能绕过 QMT gateway、stage gate、risk gate 或 reconciliation。

## 3. 必要检查

| 检查 | 必须满足 |
|---|---|
| 数据 | 使用 current truth 或 clean feed，PIT / quality pass。 |
| 因子 | 因子方向、可用时点、异常值处理和 lineage 可追踪。 |
| 标签 | label window 与 decision time 不泄漏。 |
| 单因子 | IC / RankIC / 分层收益 / turnover / cost / exposure 有结果或 unavailable。 |
| 多因子 | 组合规则、权重约束、换手约束和风险摘要明确。 |
| 准入 | 不声明 QMT-ready / simulation-ready，除非后续 runner gate 通过。 |

## 4. Stage 2 No-Lake 支撑

Stage 2 的目标是升级框架合同，而不是生产真实策略。当前 no-lake 支撑入口是 `engine/mature_multifactor_framework.py`：

| 能力 | 当前入口 | 边界 |
|---|---|---|
| 策略类型适配 | `build_multifactor_strategy_type_adapter()` | 当前只实现 multifactor adapter；事件型、机器学习和规则型策略后续通过同一 adapter 合同扩展。 |
| 信号归一化 | `build_stage2_signal_set()` | 输出 `SignalSet`，不是订单、不是 target portfolio、不是 runtime authorization。 |
| 候选统一 | `build_project_strategy_candidate_from_cr039()` | 把 CR039 `StrategyCandidate` 归一为项目级 `strategy_candidate_v1`，并绑定 `SignalSet`、`ResearchEvidenceIndex`、`PortfolioRiskPolicy`。 |
| typed unavailable | `TypedUnavailable` / `build_stage2_research_evidence_index()` | Stage 2 缺真实数据时必须结构化标注 Stage 3 补齐条件，不伪造 lineage。 |
| 组合风控 | `build_stage2_portfolio_risk_policy()` | 支撑 Stage 3 策略生产需要的 top_n、单票上限、换手、行业 / 风格 / 容量和停止条件。 |
| 成熟准入支撑 | `build_stage2_mature_admission_support()` | 只说明框架已准备好承接 Stage 3，不授权 simulation 或 live。 |
| CR030 / CR039 桥接 | `build_mature_admission_support_from_cr030_cr039_outputs()` | 将 CR030 `strategy_admission_package_v1` 边界、CR039 `multifactor_strategy_admission_package_v1` 候选和 MatureAdmissionSupport 打成 Stage 2 bundle。 |
| Stage 3 交接 | `build_stage3_research_machine_handoff()` | 输出研究机输入清单、证据清单、数据湖要求、验证计划和不授权边界。 |
| no-lake 防线 | `validate_stage2_no_lake()` | provider、lake、catalog、QMT、simulation、credential 等计数非 0 时 fail-closed。 |

Stage 2 允许 fixture、schema、静态样例、typed unavailable 和合成小样本；不连接数据湖，不触发 provider / lake / catalog / QMT / gateway / simulation / live。

## 5. Stage 3 研究机交接合同

Stage 3 不是继续运行注入包样例，而是在研究机连接真实数据湖，生产“可解释、可审计、可扩展到真实股票池”的成熟多因子策略。Stage 2 输出的 `stage3_research_machine_handoff_v1` 至少要求后续补齐以下输入和证据。

| 类别 | 必要内容 |
|---|---|
| 数据输入 | `data_release_ref`、PIT universe、上市退市、ST、停牌、涨跌停、流动性、行业、市值、风格、benchmark、费用滑点模型。 |
| 研究证据 | run manifest、factor panel、label window、IC / RankIC、分层收益、换手、暴露、组合版本、风险版本、成熟策略准入包、runner offline preflight。 |
| 追溯要求 | 每次调仓必须能追溯输入版本、信号版本、组合版本、风险版本和 evidence index。 |
| 运行边界 | Stage 3 交接合同不授权 gateway、QMT、simulation、live、账户查询、发单、撤单或凭据读取。 |
| 准入门禁 | 真实策略进入模拟盘前，必须重新生成 mature strategy admission package，并单独取得 simulation runtime authorization。 |
