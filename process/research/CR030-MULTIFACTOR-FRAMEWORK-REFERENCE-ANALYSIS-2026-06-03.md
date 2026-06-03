---
change_id: "CR-030"
title: "多因子研究框架借鉴与本项目适配分析"
status: "draft-cp2-input"
created_at: "2026-06-03T00:06:23+08:00"
created_by: "meta-po"
analysis_scope: "static local Qlib analysis + public web static research + current project mapping"
local_qlib_path: "/home/hyde/download/qlib"
runtime_authorization: "none"
dependency_change_authorized: false
external_repo_clone_install_run_authorized: false
source_copy_authorized: false
provider_fetch_authorized: false
lake_write_authorized: false
publish_authorized: false
qmt_simulation_live_authorized: false
credential_access_authorized: false
---

# CR-030 多因子研究框架借鉴与本项目适配分析

## 1. 结论摘要

CR-030 应采用“项目自有多因子研究闭环”为主线，而不是以 Qlib 或任一外部项目作为默认框架。外部项目的正确用法是提供设计参照、指标口径、报告结构、批量实验形状、研究到执行分层和许可证 / 依赖边界输入。

推荐落地路线：

| 层级 | 推荐做法 | 主要借鉴来源 | 本项目落点 |
|---|---|---|---|
| 研究任务配置 | 定义项目自有 `FactorRunSpec` / `ExperimentManifest`，用 run_id、数据快照、股票池、benchmark、标签窗口和输出目录冻结一次研究运行 | Qlib qrun / task / Recorder | 作为 `experiments/run_experiment_17_21_factor_suite.py` 的脚本级产物上移为正式契约 |
| 因子定义 | 定义项目自有 `FactorSpec`，描述输入字段、窗口、方向、PIT / `available_at`、依赖辅助数据和 failure path | Qlib Alpha158 / Zipline Pipeline / vnpy.alpha | 复用现有默认因子集，补齐元数据和校验规则 |
| 数据面板 | 定义 `FactorPanelContract` 和 `LabelWindowSpec`，保留 raw / directional / winsorized / zscore 四阶段、label horizon、泄漏防护和 lineage | Qlib DataHandler / Processor、Alphalens clean factor data | 复用 `engine/research_dataset.py` 与 CR-011 factor panel audit |
| 单因子评价 | 输出 IC、RankIC、ICIR、分层收益、long-short、turnover、coverage、稳定性和暴露报告 | Alphalens、Qlib SigAnaRecord / analysis_model | 标准化现有 IC / group return / monotonicity 能力 |
| 多因子组合 | 先支持加权 zscore、标准化、中性化、约束和 turnover 控制；优化器仅作为后续 Spike | Qlib TopkDropout / EnhancedIndexing、bt AlgoStack、LEAN Portfolio Construction | 连接 lightweight research backtest 和 `order_intent_draft_v1` |
| 准入证据 | 将研究报告汇总为 `StrategyAdmissionPackage`，映射 Stage6 gate，失败时 blocked | LEAN 分层、Qlib PortAnaRecord、现有 `engine/stage6_admission.py` | 不绕过 CR-020..CR-024 的 QMT 后续门控 |

不推荐的路线：

- 不把 Qlib 的 `.bin` 数据格式、`provider_uri`、`qlib.init`、MLflow / pickle recorder 或完整 runtime 引入本项目主路径。
- 不把 Alphalens、vectorbt、PyBroker、bt、Zipline Reloaded、LEAN、RQAlpha 或 vn.py 设为默认依赖。
- 不复制、裁剪、改写任何外部项目源码。
- 不在 CP2 / CP3 / CP5 前运行、安装或 clone 外部项目。
- 不把研究报告、factor tear sheet、Backtrader semantic diff 或 `order_intent_draft_v1` 声明为 QMT simulation / live 授权。

## 2. 调研口径和证据来源

| 来源 | 核验方式 | 本轮是否运行 / 安装 | 说明 |
|---|---|---:|---|
| 本地 Qlib | 静态读取 `/home/hyde/download/qlib` 的 README、LICENSE、docs、examples、qlib 源文件路径和配置样例 | 否 | 用户已下载，本轮只读分析，不执行 qrun、不 import、不安装依赖 |
| Alphalens / vectorbt / PyBroker / bt | 子 agent Curie 公开资料 web search、官方仓库 / PyPI / GitHub API 摘要 | 否 | 只作为公开状态和设计借鉴输入 |
| Zipline Reloaded / QuantConnect LEAN / RQAlpha / vn.py | 子 agent Ampere 公开资料 web search、官方仓库 / PyPI / GitHub API 摘要 | 否 | 只作为公开状态和设计借鉴输入 |
| 本项目现状 | 静态读取 `engine/research_dataset.py`、`experiments/run_experiment_17_21_factor_suite.py`、`engine/stage6_admission.py`、CR / STATE / docs | 否 | 用于判断现有能力应复用还是重做 |

外部项目官方入口：

| 项目 | 官方入口 | 许可证 / 状态口径 |
|---|---|---|
| Qlib | https://github.com/microsoft/qlib | 本地 LICENSE 为 MIT；正式引入前仍需 CP3 复核依赖、运行边界和数据假设 |
| Alphalens | https://github.com/quantopian/alphalens | Apache-2.0；原项目偏静态，`alphalens-reloaded` 更现代但仍建议只借鉴指标 |
| vectorbt | https://github.com/polakowo/vectorbt / https://vectorbt.dev | Apache 2.0 with Commons Clause；不适合作为默认依赖 |
| PyBroker | https://github.com/edtechre/pybroker / https://www.pybroker.com | Apache 2.0 with Commons Clause / 非商业免费口径；不适合作为默认依赖 |
| bt | https://github.com/pmorissette/bt | MIT；适合借鉴组合 DSL，不是因子诊断核心 |
| Zipline Reloaded | https://github.com/stefan-jansen/zipline-reloaded / https://zipline.ml4trading.io | Apache-2.0；适合借鉴 Pipeline，不适合作为本项目运行核心 |
| QuantConnect LEAN | https://github.com/QuantConnect/Lean / https://www.quantconnect.com/docs/v2 | Apache-2.0；大型 C# 引擎，只借鉴分层契约 |
| RQAlpha | https://github.com/ricequant/rqalpha / https://rqalpha.readthedocs.io/zh_CN/latest/ | 公开信息存在非商业限制口径，按限制性 / 需授权处理 |
| vn.py | https://github.com/vnpy/vnpy / https://www.vnpy.com | MIT；`vnpy.alpha` 适合做流程对标，主框架过重 |

## 3. Qlib 本地静态分析

本地 Qlib 位于 `/home/hyde/download/qlib`。本轮只做静态分析，未安装、未 import、未执行 qrun、未读取外部 provider、未写任何数据。

### 3.1 Qlib 关键模块

| Qlib 模块 / 文件 | 静态观察 | 对 CR-030 的借鉴价值 | 本项目边界 |
|---|---|---|---|
| `docs/component/workflow.rst` | 工作流包含数据加载 / 处理 / 切片、模型训练 / 推理 / 保存、信号分析和回测评估 | 借鉴为 `FactorRunSpec -> model / factor evaluation -> portfolio analysis -> report catalog` 的阶段划分 | 不引入 qrun 作为本项目主入口 |
| `docs/component/data.rst` | 数据工作流包含数据转换、表达式引擎、DataHandler、processor、Dataset 和健康检查 | 借鉴 DataHandler / Processor 分层，以及 fit_start / fit_end 防泄漏思想 | 不采用 Qlib `.bin`、`provider_uri` 或官方数据下载 |
| `docs/component/recorder.rst` | Experiment / Recorder / RecordTemp 分层，记录 SignalRecord、SigAnaRecord、PortAnaRecord artifact | 借鉴 recorder 模板和 artifact catalog | 不采用 MLflow / pickle 作为项目事实源 |
| `docs/component/report.rst` | 报告覆盖 IC / RankIC、累计收益、风险分析、分层 label 等图表 | 借鉴报告目录和指标类别 | 报告输出必须使用本项目 JSON / CSV / Markdown 契约 |
| `qlib/contrib/data/handler.py` | Alpha158 / Alpha360 使用 feature / label config、learn / infer processors | 借鉴因子定义、标签窗口和 processor pipeline | 不直接采用 Alpha158 字段为项目 schema |
| `qlib/data/dataset/processor.py` | DropnaLabel、ProcessInf、Fillna、ZScoreNorm、CSZScoreNorm 等 processor | 借鉴缺失 / inf / 标准化 / 横截面标准化处理顺序 | 本项目仍需保留 raw / directional / winsorized / zscore 审计层 |
| `qlib/workflow/record_temp.py` | SignalRecord 存预测 / label，SigAnaRecord 存 IC / RankIC，PortAnaRecord 存 backtest / risk analysis | 借鉴“同一 run 下的结构化 record templates” | 不使用 pickle artifact 作为跨版本稳定接口 |
| `qlib/contrib/eva/alpha.py` | 包含 IC、long-short、precision、autocorr 等评价函数 | 借鉴指标集合和计算顺序 | 实现时使用本项目数据合同和测试样例 |
| `qlib/contrib/report/analysis_model/analysis_model_performance.py` | 包含分组收益、long-short、monthly IC、prediction autocorr、turnover 等分析 | 借鉴单因子 / 模型得分报告结构 | 不引入 notebook / plotly 作为阻塞性交付 |
| `qlib/contrib/strategy/signal_strategy.py` | TopkDropoutStrategy 从 score 到 top-k / drop 调仓 | 借鉴 score 到 target portfolio 的桥接语义 | 不直接复用交易策略或订单实现 |
| `qlib/contrib/strategy/optimizer/enhanced_indexing.py` | 增强指数优化使用风险模型、benchmark deviation、factor deviation 等约束 | 作为组合优化 Spike 参考 | 不默认引入 cvxpy / 风险模型依赖 |
| `examples/benchmarks/LightGBM/workflow_config_lightgbm_Alpha158.yaml` | 示例配置覆盖 qlib init、market、benchmark、dataset、model、record | 借鉴配置文件 shape | 不复制配置或运行 qrun |
| `examples/portfolio/config_enhanced_indexing.yaml` | 示例展示组合优化 workflow | 借鉴 portfolio / risk / benchmark 约束表达 | 只作为后续可选 Spike 输入 |

### 3.2 Qlib 最值得借鉴的能力

| 借鉴项 | 为什么重要 | 建议映射到本项目 |
|---|---|---|
| 配置化 task / qrun 思想 | 一次研究运行需要可复现输入、模型 / 因子配置、报告和 artifact | `FactorRunSpec` + `ExperimentManifest` |
| Handler / Processor / Dataset 分层 | 因子研究必须分离数据加载、预处理、标签构造和模型输入 | `FactorPanelContract` + `LabelWindowSpec` |
| RecordTemp / Recorder | 研究输出不能只靠临时 CSV，需要结构化 artifact catalog | `ResearchReportCatalog` |
| SignalRecord / SigAnaRecord / PortAnaRecord | 信号、因子评价和组合分析应该分层记录 | `FactorEvaluationReport` + `StrategyAdmissionPackage` |
| IC / RankIC / long-short / turnover / autocorr | 多因子框架的可分析性依赖标准指标集合 | `FactorEvaluationMetrics` |
| TopkDropout / EnhancedIndexing | 从 score 到组合的路径需要显式调仓和约束语义 | `MultiFactorCombiner`，优化器后置 |

### 3.3 Qlib 不适合直接引入的能力

| 不建议引入项 | 原因 | CR-030 处理方式 |
|---|---|---|
| Qlib `.bin` 数据格式 / provider_uri | 与本项目 market data lake / catalog / current truth 边界冲突 | 只借鉴 DataHandler 概念，不替换数据事实源 |
| `qlib.init` / qrun runtime | 会把运行入口和全局配置绑到 Qlib | 本项目继续使用自有 CLI / experiment runner |
| MLflow / pickle artifact | pickle 跨版本稳定性和审计性弱，MLflow 增加依赖和运行复杂度 | 使用 JSON / YAML / CSV / Markdown 可审计产物 |
| 官方数据下载 / provider | 当前不授权 provider fetch，也不允许外部数据源自动进入研究主路径 | 后续若需要，另起 provider / runner CR |
| EnhancedIndexing 默认 optimizer | 需要 cvxpy、风险模型和 benchmark / factor exposure 完整数据 | 仅作为后续组合优化 Spike |
| online serving / RL order execution | 超出当前多因子日频研究闭环 | 保留为 deferred idea，不进入 CR-030 P0 |

## 4. 其他外部项目借鉴矩阵

| 项目 | 建议分类 | 最值得借鉴 | 不适合引入点 | 对 CR-030 的建议 |
|---|---|---|---|---|
| Alphalens | 借鉴 | `factor_data` 清洗、forward returns、分位数组合收益、IC / RankIC、turnover、grouped analysis、tear sheet | 原 Quantopian 包正式 release 旧；Notebook / pyfolio 生态偏老 | 用它定义单因子评价口径，不作为依赖 |
| vectorbt | 可选 Spike | 向量化批量实验、参数网格、broadcasting、Portfolio stats、交易记录矩阵化 | Commons Clause 合规风险；完整 backtesting engine 抽象过大 | 只对标批量实验 shape 和性能，不默认依赖 |
| PyBroker | 可选 Spike | ML walk-forward、bootstrap metrics、模型 / 指标缓存、ranking 和 position sizing | Commons Clause / 非商业口径；内置外部数据和 broker 入口 | 只借鉴 walk-forward / bootstrap 验证 |
| bt | 借鉴 | AlgoStack、组合权重、rebalance、策略树和结果比较 | 不是因子诊断库，IC / 暴露 / factor decay 需自定义 | 借鉴组合层 DSL 边界，不替换引擎 |
| Zipline Reloaded | 借鉴 | Pipeline API、Factor / Filter / Classifier、CustomFactor、rank / top / mask / groupby、盘前 pipeline output | 数据 bundle、资产元数据、交易日历和美股语境适配成本 | 借鉴因子计算 DAG 和横截面筛选语义 |
| QuantConnect LEAN | 借鉴 | Universe Selection、Alpha Model、Portfolio Construction、Risk Management、Execution | 大型 C# 引擎，CLI / Docker / 云端数据复杂 | 借鉴 Alpha -> Portfolio -> Risk -> Execution 契约 |
| RQAlpha | 可选 Spike | A 股事件驱动、scheduler、订单 API、撮合 / 模拟 broker、Mod 扩展 | 许可证需按限制性 / 需授权处理；与 Ricequant 生态绑定 | 仅做 A 股交易约束 / Mod 设计 Spike |
| vn.py / vnpy.alpha | 可选 Spike | dataset、Alpha158 / Alpha101、表达式函数、预处理、模型训练、信号、策略回测、实盘衔接 | 主框架 gateway / 事件引擎 / GUI / 实盘接口过重 | 做端到端流程对标，不集成 gateway |
| Backtrader | 已由 CR-025 收敛 | 执行语义、订单生命周期、差异报告、no-copy guardrail | GPLv3 no-copy、不可默认依赖、不可真实 broker | CR-030 只继承 CR-025 边界，不扩大范围 |

## 5. 本项目已有能力映射

| 本项目现有对象 | 已具备能力 | CR-030 应如何复用 |
|---|---|---|
| `engine/research_dataset.py` | `research_input_v1`、quality / adjustment / label / PIT / universe / tradability / exposure / capacity gate，robust validation claims，label window gate，neutralization claims | 作为 `FactorPanelContract`、`LabelWindowSpec`、辅助数据 gate 和 safety counter 的核心事实来源 |
| `experiments/run_experiment_17_21_factor_suite.py` | `FactorDefinition`、默认因子集、raw factor matrices、preprocess、forward returns、IC、group returns、monotonicity、factor correlations、multifactor score、factor panel audit、robust validation views | 上移为正式 `FactorSpec`、`FactorEvaluationReport` 和 `ExperimentManifest`，避免脚本级散落 |
| `engine/stage6_admission.py` | Stage6 gate、P0 准入、blocked claims、forbidden counters、QMT admission 阻断 | 作为 `StrategyAdmissionPackage` 的准入后端，不在 CR-030 重写 |
| `engine/semantic_diff.py` | artifact schema、forbidden claim scan、production truth / QMT admission 声明边界 | 复用为因子报告和 admission package 的声明护栏模式 |
| `docs/CR019-DEFERRED-CAPABILITIES.md` | Qlib W7 / Backtrader W6 / minute / Level2 后置触发条件 | CR-026 保持 runner Spike candidate，等待 CR-030 契约冻结 |
| `process/stories/CR011-S08-factor-panel-audit-and-robust-validation.md` | 四阶段 factor panel audit 与稳健性五视图已 verified | CR-030 不重做，从“实验 17-21 增量验证”提升为通用多因子研究契约 |

## 6. 推荐的 CR-030 自有契约

| 契约 | 最小字段 / 能力 | 借鉴来源 | 验收关注点 |
|---|---|---|---|
| `FactorSpec` | `factor_id`、`name`、`version`、`direction`、`input_fields`、`window`、`available_at_policy`、`pit_policy`、`auxiliary_requirements`、`failure_policy` | Qlib Alpha158、Zipline Pipeline | 同一因子版本可复现；不可用辅助数据必须 blocked |
| `FactorRunSpec` | `run_id`、`date_range`、`universe`、`benchmark`、`label_window`、`data_snapshot`、`factor_specs`、`output_root`、`permission_counters` | Qlib qrun / task | 运行输入可追溯；未授权计数必须为 0 |
| `FactorPanelContract` | index、columns、frequency、raw / directional / winsorized / zscore、lineage、coverage、missing / halt / limit flags | Qlib DataHandler、CR-011 S08 | 四阶段 exact 覆盖；缺失原因可审计 |
| `LabelWindowSpec` | horizon、return_kind、benchmark_adjusted、industry_neutral_optional、`label_available_end`、leakage_check | Alphalens forward returns、Qlib label config | 未来数据防泄漏；标签窗口和交易时点一致 |
| `FactorEvaluationReport` | IC、RankIC、ICIR、group returns、long-short、turnover、coverage、autocorr、exposure、blocked claims | Alphalens、Qlib SigAnaRecord | 指标可重算；失败项可机器读取 |
| `MultiFactorCombiner` | factor weights、normalization、neutralization、orthogonalization、constraints、rebalance、turnover cap | Qlib TopkDropout / EnhancedIndexing、bt | 默认简单可解释，优化器后置 |
| `ExperimentManifest` | run_id、code version、data version、params、artifact list、metrics summary、exceptions、limitations | Qlib Recorder | 不使用 pickle 作为稳定事实源 |
| `ResearchReportCatalog` | report_id、run_id、factor_ids、artifact paths、admission_status、source_lineage、created_at | Qlib Recorder / report | 报告可找回、可审计、可分流 |
| `StrategyAdmissionPackage` | factor evidence、portfolio evidence、robustness、ablation、freeze、pre-sim / dry-run readiness、blocked claims | LEAN 分层、Stage6 admission | 失败即 blocked，不直接 QMT-ready |
| `ResearchToExecutionHandoff` | target portfolio、`order_intent_draft_v1` 字段、limitations、execution_price_policy、lineage | CR-025 semantic diff / order intent | 只生成草稿，不授权发单 |

## 7. CR-026 分流建议

推荐 CP2 采用以下决策：

| 项 | 推荐结论 |
|---|---|
| CR-030 | 当前 active 主线，负责定义本项目自有多因子研究闭环、外部项目借鉴矩阵、研究报告和准入包 |
| CR-026 | 保留为 `Qlib isolated runner / factor workflow boundary` 后续 Spike candidate，不并行启动、不并入实现范围 |
| CR-026 重启条件 | CR-030 冻结 `FactorPanelContract`、`LabelWindowSpec`、`ResearchReportCatalog`、runner input/output、failure model、dependency isolation 和 source-of-truth boundary |
| 当前禁止项 | 不安装 Qlib、不运行 qrun、不接入 Qlib provider、不复制源码、不修改依赖 |

理由：

1. Qlib 的 workflow / DataHandler / Recorder 对 CR-030 有强借鉴价值，但其 runtime 和数据格式会改变本项目事实源边界。
2. 当前项目已有 research dataset、factor panel audit、robust validation 和 Stage6 gate，CR-030 应优先标准化现有能力。
3. CR-026 的阻塞条件本来就是 factor panel、label window、report catalog 和 runner I/O 合同尚未冻结；这些正是 CR-030 应先完成的内容。

## 8. CP2 建议新增 Use Cases 与 Requirements

### 8.1 建议新增 Use Cases

| 建议 UC | 场景名称 | 核心问题 |
|---|---|---|
| UC-20 | 多因子研究闭环主线确认 | CR-030 是否作为自有多因子研究闭环标准化主线，而不是 Qlib-first 或大型框架集成 |
| UC-21 | 外部项目静态借鉴矩阵 | 确认 Qlib、Alphalens、vectorbt、Zipline Reloaded、LEAN、RQAlpha、vn.py、PyBroker、bt、Backtrader 的静态借鉴范围和不引入边界 |
| UC-22 | 研究对象契约冻结 | 确认 `FactorSpec`、`FactorRunSpec`、`FactorPanelContract`、`LabelWindowSpec` 最小字段 |
| UC-23 | 单因子评价与报告 | 确认 IC、RankIC、ICIR、分层收益、long-short、turnover、coverage、稳定性和暴露报告 |
| UC-24 | 多因子组合构建 | 确认标准化、中性化、正交化、加权合成、组合约束、容量 / 成本和 benchmark 边界 |
| UC-25 | 实验追溯与报告目录 | 确认 `ExperimentManifest`、`ResearchReportCatalog` 和可复现审计口径 |
| UC-26 | 策略准入包与研究到执行交接 | 确认 `StrategyAdmissionPackage`、Stage6 gate、`order_intent_draft_v1` 草稿边界 |
| UC-27 | CR-026 / Qlib runner 分流 | 确认 CR-026 保留为后续 Spike candidate，不并行启动、不授权实现 |

### 8.2 建议新增 Requirements

| 建议 ID | 类型 | 需求建议 | 优先级 |
|---|---|---|---|
| REQ-174 | 范围 | CR-030 必须以项目自有多因子研究闭环为主线，外部项目只作为设计参考 / Spike 候选 | P0 |
| REQ-175 | 外部借鉴 | CP3 HLD 必须输出外部项目借鉴矩阵，并标注 `reference_only / optional_spike / exclude / forbidden_migration` | P0 |
| REQ-176 | 契约 | 必须定义 `FactorSpec` 与 `FactorRunSpec` | P0 |
| REQ-177 | 数据面板 | 必须定义 `FactorPanelContract` 与 `LabelWindowSpec`，覆盖 PIT、`available_at`、复权、停牌、label horizon 和泄漏防护 | P0 |
| REQ-178 | 单因子评价 | 必须输出 IC / RankIC / ICIR、分层收益、long-short、turnover、coverage、稳定性和暴露 | P0 |
| REQ-179 | 多因子组合 | 必须设计标准化、去极值、中性化、正交化、权重合成、约束、rebalance、容量 / 成本和 benchmark 对照 | P0 |
| REQ-180 | 追溯 | 必须生成 `ExperimentManifest` 和报告目录 | P0 |
| REQ-181 | 准入 | 必须定义 `StrategyAdmissionPackage`，映射 Stage6 gate，任一 P0 gate 缺失或失败时 blocked | P0 |
| REQ-182 | 安全边界 | CR-030 CP2/CP3/CP5 前必须保持 provider / lake / publish / QMT / credential / dependency change 计数为 0 | P0 |
| REQ-183 | 复用现状 | CP3/LLD 应优先复用 `engine/research_dataset.py` 和实验 17-21 能力 | P0 |
| REQ-184 | CR-026 分流 | CP2 必须形成 CR-026 去向决策；未决前不得安装、运行或接入 Qlib | P0 |
| REQ-185 | 文档 | README / USER-MANUAL / TEST-STRATEGY 后续必须说明多因子闭环、外部项目边界、准入包和不授权项 | P1 |

## 9. 风险和护栏

| 风险 | 等级 | 触发条件 | 护栏 |
|---|---|---|---|
| 外部框架误引入 | 高 | 把 Qlib / vectorbt / vn.py 等作为默认依赖 | CP3 只允许 reference / optional Spike；CP5 前禁止依赖变更 |
| 许可证误判 | 高 | 复制源码、引入 Commons Clause / 限制性项目、误判 RQAlpha license | 每个项目在 HLD 中保留 license / dependency / migration 复核列 |
| 数据事实源冲突 | 高 | 用 Qlib provider / bundle 替换本项目 data lake / catalog | `FactorRunSpec` 必须引用本项目数据快照和 source-of-truth boundary |
| 指标不可复现 | 中 | 报告只输出图或 notebook，没有机器可读 metrics | 所有报告必须输出 JSON / CSV / Markdown artifact |
| 研究结果误当交易授权 | 高 | factor report / order intent draft 被声明为 QMT-ready | `StrategyAdmissionPackage` 和 Stage6 gate 未通过时 blocked |
| 重做既有能力 | 中 | 绕开 `research_dataset.py` 与实验 17-21 写新框架 | CP3/LLD 必须列出复用路径和迁移理由 |

## 10. 当前状态

- 本分析可作为 CR-030 CP2 discussion 和后续 CP3 HLD 的输入。
- 尚未更新 `process/USE-CASES.md` / `process/REQUIREMENTS.md` 的正式 CR-030 增量。
- 尚未发起 CP2 人工门禁。
- 当前仍不授权实现、依赖变更、外部项目 clone / install / run、源码复制 / 迁移、provider fetch、lake write、publish、QMT / simulation / live 或凭据读取。
