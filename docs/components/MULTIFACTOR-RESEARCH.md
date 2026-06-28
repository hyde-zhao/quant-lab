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
| `StrategyCandidate` | 项目级策略候选合同。 | 统一历史候选输出、`SignalSet`、`ResearchEvidenceIndex` 与风控策略引用。 |
| `ResearchEvidenceIndex` | 研究证据索引。 | data release、manifest、metric refs、lineage refs、typed unavailable。 |
| `PortfolioRiskPolicy` | 成熟策略组合风控策略。 | top_n、max_weight、turnover、行业 / 风格 / 容量 / 费用 / 停止条件。 |
| mature admission support | Stage 2 no-lake 的成熟准入支撑包。 | 不代表 runtime / simulation / live 授权。 |
| mature research handoff | 研究机交接合同。 | 明确真实数据湖输入、evidence、验证计划和运行边界；Stage 3 只是当前项目阶段名。 |

## 2. 输出边界

多因子研究的出口是 `StrategyAdmissionPackage` 或等价策略准入包。Stage 3 的出口进一步收紧为评估通过的成熟多因子策略：`FactorModelValidationReport` 核心门禁无 blocked、mature admission 为 PASS、runner offline / preflight 证据通过。它可以交给 runner 做导入检查，但不能直接下单，也不能绕过 QMT gateway、stage gate、risk gate 或 reconciliation。

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
| 候选统一 | `build_project_strategy_candidate_from_cr039()` | 把历史候选 `StrategyCandidate` 归一为项目级 `strategy_candidate_v1`，并绑定 `SignalSet`、`ResearchEvidenceIndex`、`PortfolioRiskPolicy`。 |
| typed unavailable | `TypedUnavailable` / `build_stage2_research_evidence_index()` | Stage 2 缺真实数据时必须结构化标注成熟研究补齐条件，不伪造 lineage。 |
| 组合风控 | `build_stage2_portfolio_risk_policy()` | 支撑成熟策略生产需要的 top_n、单票上限、换手、行业 / 风格 / 容量和停止条件。 |
| 成熟准入支撑 | `build_stage2_mature_admission_support()` | 只说明框架已准备好承接成熟研究，不授权 simulation 或 live。 |
| 历史研究桥接 | `build_mature_admission_support_from_cr030_cr039_outputs()` | 将历史 `strategy_admission_package_v1` 边界、历史多因子候选和 MatureAdmissionSupport 打成 Stage 2 bundle。 |
| mature research handoff | `build_stage3_research_machine_handoff()` | 输出研究机输入清单、证据清单、数据湖要求、验证计划和不授权边界；函数名暂保留为兼容名。 |
| no-lake 防线 | `validate_stage2_no_lake()` | provider、lake、catalog、QMT、simulation、credential 等计数非 0 时 fail-closed。 |

Stage 2 允许 fixture、schema、静态样例、typed unavailable 和合成小样本；不连接数据湖，不触发 provider / lake / catalog / QMT / gateway / simulation / live。

## 5. Mature Research Handoff

Mature research 不是继续运行注入包样例，而是在研究机连接真实数据湖，生产“可解释、可审计、可扩展到真实股票池”的成熟多因子策略。Stage 2 输出的 `stage3_research_machine_handoff_v1` 是历史兼容 schema 名，至少要求后续补齐以下输入和证据。

| 类别 | 必要内容 |
|---|---|
| 数据输入 | `data_release_ref`、PIT universe、上市退市、ST、停牌、涨跌停、流动性、行业、市值、风格、benchmark、费用滑点模型。 |
| 研究证据 | run manifest、factor panel、label window、IC / RankIC、分层收益、换手、暴露、组合版本、风险版本、FactorModelValidationReport、成熟策略准入包、runner offline preflight。 |
| 追溯要求 | 每次调仓必须能追溯输入版本、信号版本、组合版本、风险版本和 evidence index。 |
| 运行边界 | Mature research handoff 不授权 gateway、QMT、simulation、live、账户查询、发单、撤单或凭据读取。 |
| 准入门禁 | 真实策略进入模拟盘前，必须重新生成 FactorModelValidationReport 和 mature strategy admission package；只有核心门禁无 blocked、admission PASS 的候选才能作为 Stage 3 输出，并且进入 Stage 4 前仍需单独取得 simulation runtime authorization。 |

## 6. Mature Research Package Contract

Mature research package 合同在 `engine/mature_multifactor_framework.py` 中定义 run manifest 和 mature research package。该合同只校验研究机产物引用，不读取数据湖、不导入 QMT、不触发 runner runtime。

| 能力 | 当前入口 | 边界 |
|---|---|---|
| run manifest | `build_stage3_research_run_manifest()` / `validate_stage3_research_run_manifest()` | 必须包含 run id、strategy id、config hash、冻结 `data_release_ref`、factor versions、code version、seed 和 date range。 |
| mature research package | `build_stage3_mature_research_package()` / `validate_stage3_mature_research_package()` | 必须补齐成熟研究 P0 输入 refs、全部 evidence refs、mature admission package ref、runner offline preflight ref 和 observation plan ref；函数名暂保留为兼容名。 |
| fail-closed | `validate_stage3_mature_research_package()` | 空引用、`typed_unavailable:*`、`required`、Stage 2 fixture placeholder 或缺 evidence 时均 blocked，不允许进入 Stage 4 审查候选。 |
| 授权边界 | mature research package flags (`Stage3MatureResearchPackage` 为兼容类名) | 固定 `not_runtime_authorization=true`、`not_simulation_authorization=true`、`not_live_authorization=true`、`not_gateway_or_qmt_operation=true`。 |

Mature research package 进入 observation / simulation 审查前只能作为研究准入输入；blocked package 只能作为诊断基线，不能进入 Stage 4。它不会自动授权 simulation runtime、gateway、`small_live` 或 `live`。

## 7. Mature Multifactor Research Runner

Mature multifactor research runner 的稳定入口为 `scripts/research/run_multifactor_strategy_research.py`，归档实现桥接路径为 `scripts/legacy/cr/run_stage3_mature_multifactor_research.py`，核心实现为 `engine/mature_multifactor_research.py`。旧 `engine/stage3_mature_multifactor_research.py` 已归档到 `docs/legacy/archive/engine/stage3_mature_multifactor_research.py`；文件名中的 `stage3` 是历史项目阶段命名。该 runner 只读 canonical data lake，写 research run 与 process evidence；禁止 provider fetch、lake write、catalog publish、QMT、gateway、simulation/live、账户/订单操作和凭据读取。

默认数据湖根目录为 `/home/hyde/data/quant-lab/lake`，研究输出根目录为 `/home/hyde/data/quant-lab/research/runs/stage3_mature_multifactor`。reader 优先读取完整 `canonical/<dataset>/1.0` 目录；catalog 中指向单个 parquet 分片的 `canonical_path` 只作为 lineage ref 使用，避免误读局部分片。

当前通过准入的研究候选运行：

| 项 | 值 |
|---|---|
| run_id | `stage3-mature-mf-20260627-csi-all-value-bottom-top200-step20-pass-candidate-v3` |
| date range | `2021-01-01` 到 `2026-06-26` |
| data release ref | `catalog://market-data/stage3-data-update/2026-06-26` |
| benchmark | 中证全指 `000985.SH` |
| factor score policy | `value_pb_inverse=-1` |
| top_n | `200` |
| rebalance step | `20` |
| min ADV20 | `1000000` 数据湖原生 `liquidity_capacity.adv20_amount` 单位 |
| factor panel rows | `6750809` |
| valid research rows | `267186` |
| rebalance count | `65` |
| portfolio rows | `9716` |
| mean composite RankIC | `-0.04572274972797082` |
| mean net forward return | `0.002406807133380886` |
| mean turnover | `0.3934171217245369` |
| research run status | `PASS` |
| mature admission status | `PASS` |
| factor model validation status | `pass_with_risk` |
| blocked gates | 无 |

该运行达到 Stage 3 出口标准，可进入 Stage 4 观察审查候选。`pass_with_risk` 门禁仍需在 Stage 4 前后持续跟踪，包括因子溢价显著性、时间切分、风格暴露、参数敏感性、IC 衰减、容量冲击和尾部风险。

关键产物：

| 产物 | 路径 |
|---|---|
| mature research package | `/home/hyde/data/quant-lab/research/runs/stage3_mature_multifactor/stage3-mature-mf-20260627-csi-all-value-bottom-top200-step20-pass-candidate-v3/STAGE3-MATURE-RESEARCH-PACKAGE.json` |
| mature admission package | `/home/hyde/data/quant-lab/research/runs/stage3_mature_multifactor/stage3-mature-mf-20260627-csi-all-value-bottom-top200-step20-pass-candidate-v3/MATURE-STRATEGY-ADMISSION-PACKAGE.json` |
| factor model validation report | `/home/hyde/data/quant-lab/research/runs/stage3_mature_multifactor/stage3-mature-mf-20260627-csi-all-value-bottom-top200-step20-pass-candidate-v3/FACTOR-MODEL-VALIDATION-REPORT.json` |
| runner offline preflight | `/home/hyde/data/quant-lab/research/runs/stage3_mature_multifactor/stage3-mature-mf-20260627-csi-all-value-bottom-top200-step20-pass-candidate-v3/RUNNER-OFFLINE-PREFLIGHT.json` |
| observation plan | `/home/hyde/data/quant-lab/research/runs/stage3_mature_multifactor/stage3-mature-mf-20260627-csi-all-value-bottom-top200-step20-pass-candidate-v3/STAGE4-OBSERVATION-PLAN.json` |
| process summary | `process/evidence/stage3-mature-multifactor/stage3-mature-mf-20260627-csi-all-value-bottom-top200-step20-pass-candidate-v3/stage3-research-summary.json` |

已知限制：当前策略已通过研究准入，但该结论只允许进入观察审查候选；`prices_limit` catalog lineage 仍记录历史 run ref，但 runner 实际读取完整 canonical root；流动性容量阈值使用数据湖原生字段单位；风格暴露使用市值、PB、波动和动量代理；mature research 仍不授权 simulation runtime、gateway、`small_live` 或 `live`。
