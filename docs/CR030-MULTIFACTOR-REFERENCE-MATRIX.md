---
change_id: "CR-030"
story_id: "CR030-S01-external-reference-matrix-and-loop-contract"
title: "CR-030 外部项目借鉴矩阵与多因子研究闭环总合同"
status: "implemented-cp6-ready"
created_at: "2026-06-03"
owner: "meta-dev"
source_lld: "process/stories/CR030-S01-external-reference-matrix-and-loop-contract-LLD.md"
cp5_review: "checkpoints/CP5-CR030-MULTIFACTOR-RESEARCH-LOOP-BATCH-A-LLD-BATCH.md"
---

# CR-030 外部项目借鉴矩阵与多因子研究闭环总合同

## 1. 目标与边界

本文冻结 CR-030 的外部项目借鉴边界。CR-030 的主线是项目自有多因子研究闭环：以本项目 data lake、`research_input_v1`、实验 17-21、CR-011 factor panel audit、label window gate、Stage6 admission gate 和 CR-025 `order_intent_draft_v1` 为基线事实源，再用外部项目做静态 cross-check。

本文只构成设计参考和后续 Story 的合同输入，不构成任何外部项目运行授权、依赖安装授权、源码迁移授权、provider / lake / publish 授权、QMT / simulation / live 授权或凭据读取授权。

CR-030 或后续 `StrategyAdmissionPackage` 不构成 QMT-ready、simulation-ready、live-ready、production truth 或真实可交易证据；这些词只能在否定边界中出现。

## 2. 分类语义

| 分类 | 含义 | 默认动作 | 切换条件 |
|---|---|---|---|
| `reference_only` | 仅借鉴概念、指标、合同形状或报告结构。 | 不新增依赖、不运行、不复制源码、不把外部对象设为内部 truth。 | 内部合同稳定后，如需要互操作映射，另起 adapter / Spike。 |
| `optional_spike` | 保留为后续有边界的预研候选。 | 当前不进入 CR-030 P0；只记录触发条件和风险。 | 用户单独批准 CR / Spike、依赖隔离、运行权限、数据事实源和回归范围。 |
| `exclude_by_default` | 默认排除为运行时、依赖、provider、runner、optimizer 或 report truth。 | 不作为默认集成路线。 | 只有许可证、依赖、权限、事实源和验收边界重新评审后才可重访。 |
| `forbidden_migration` | 源码、样例、测试、数据或运行时语义的迁移默认禁止。 | 不复制、不裁剪、不改写、不 vendor、不从外部树迁移代码。 | 仅在独立 CR、CP3/CP5、合规确认和用户风险接受全部完成后重访。 |

允许的分类值只能是以上枚举或由以上枚举组合而成。`exclude_by_default` 是默认排除语义，等价于 HLD 中 “exclude by default” 的机器可扫描写法。

## 3. 外部项目矩阵

| 项目 | 分类 | License / 依赖风险 | 可借鉴点 | 不可做事项 | 后续 Spike 条件 | 与自有多因子研究闭环的关系 |
|---|---|---|---|---|---|---|
| Qlib | `reference_only` + `optional_spike` | 本轮静态口径为 MIT；依赖可能包含 MLflow、LightGBM、cvxpy、Redis、Mongo、Jupyter、Cython / C++ 扩展，正式使用前必须重新复核。 | qrun / task shape、DataHandler / Processor / Dataset 分层、Recorder、SignalRecord、SigAnaRecord、PortAnaRecord、IC / RankIC、long-short、turnover、TopkDropout、EnhancedIndexing 约束表达。 | 不运行 qrun，不调用 `qlib.init`，不使用 `provider_uri`，不采用 `.bin` 数据格式，不下载官方数据，不复制源码 / 示例 / 测试 / 数据，不把 MLflow 或 pickle artifact 设为事实源。 | CR-030 冻结 FactorPanelContract、LabelWindowSpec、ResearchReportCatalog、runner I/O、failure model、dependency isolation、provider 禁用和 source-of-truth boundary 后，由 meta-po 单独启动 CR-026。 | 只作为 workflow / recorder / analyzer cross-check；项目内部 truth 仍由自有合同和本项目数据湖承担。 |
| Alphalens | `reference_only` | 静态口径为 Apache-2.0；原 Quantopian 包偏静态，reloaded 生态需单独复核。 | clean factor data、forward returns、IC / RankIC、分位数组合收益、long-short、turnover、grouped analysis、tear sheet。 | 不默认安装，不把 `factor_data` 作为内部 truth，不用 Notebook / pyfolio 旧生态替代本项目报告，不用外部对象字段替换 FactorPanelContract。 | 若 CR030-S04 的单因子评价指标出现口径争议，可另起 bounded metrics Spike 对照公式和字段映射。 | 作为单因子评价口径参考；内部报告输出仍使用 CR030-S04 的 JSON / CSV / Markdown 合同。 |
| vectorbt | `optional_spike` + `exclude_by_default` | 静态口径为 Apache 2.0 with Commons Clause；商业限制和依赖风险需复核。 | 向量化批量实验、broadcasting、参数网格、Portfolio stats、交易记录矩阵化思路。 | 不作为默认 backtesting engine，不作为 optimizer，不运行样例，不新增依赖，不让外部 Portfolio stats 替代本项目 report truth。 | 只有当自有批量研究性能瓶颈有量化证据，且用户批准 dependency / runtime Spike 后才评估。 | 可作为性能和批量实验 shape 的后续参考；CR-030 P0 仍优先可解释、可审计的自有闭环。 |
| PyBroker | `optional_spike` + `exclude_by_default` | 静态口径为 Apache 2.0 with Commons Clause / 非商业免费口径；许可证、数据入口和 broker 入口必须复核。 | ML walk-forward、bootstrap metrics、ranking、position sizing、模型 / 指标缓存。 | 不接外部 data / broker，不运行 ML workflow，不新增依赖，不把 ML 训练流程提前并入 P0。 | 仅当后续 ML 因子 CR 明确需要 walk-forward / bootstrap 且权限边界批准后评估。 | 只为后续 ML 因子验证路线提供参考；当前自有闭环先冻结传统因子和可解释组合。 |
| bt | `reference_only` | 静态口径为 MIT；依赖风险低于大型 runner，但不是因子诊断核心。 | AlgoStack、组合权重、rebalance、策略树、结果比较、组合层 DSL。 | 不作为因子诊断库，不替代 lightweight engine，不把其结果对象作为本项目 truth。 | 若 CR030-S05 的组合 DSL 表达不足，可在不改依赖前提下先做文档级语义 Spike。 | 为 MultiFactorCombiner 的组合约束和 rebalance 语义提供参考。 |
| Zipline Reloaded | `reference_only` | 静态口径为 Apache-2.0；bundle、calendar、asset metadata 和交易日历运行时适配成本高。 | Pipeline API、Factor / Filter / Classifier、CustomFactor、rank / top / mask / groupby、横截面筛选。 | 不引入 bundle / calendar / asset metadata runtime，不作为 runner，不让 Zipline 对象替代 FactorSpec。 | 若 FactorSpec / FactorPanelContract 需要更复杂 DAG 语义，可另起 pipeline mapping Spike。 | 用于因子 DAG 和横截面筛选 cross-check；内部仍采用自有字段字典。 |
| QuantConnect LEAN | `reference_only` + `exclude_by_default` | 静态口径为 Apache-2.0；大型 C# 引擎、CLI / Docker / cloud data / runtime 栈成本高。 | Universe Selection、Alpha Model、Portfolio Construction、Risk Management、Execution 分层。 | 不引入 C# runtime、CLI、Docker 或 cloud data，不作为执行引擎，不绕开 QMT route gate。 | 若 StrategyAdmissionPackage 需要更细的分层状态，可做文档级分层对照 Spike。 | 用于 admission package 分层 cross-check；不产生执行授权。 |
| RQAlpha | `optional_spike` + `exclude_by_default` | 公开信息存在非商业限制口径，按限制性 / 需授权处理；交易接口和 broker 语义风险高。 | A 股事件驱动、scheduler、订单 API 语义、撮合 / 模拟 broker、Mod 扩展。 | 不默认依赖，不接 broker，不运行 A 股事件回测，不把订单 API 或 broker 语义并入 CR-030。 | 只有 A 股交易约束设计需要对照且许可证 / 授权边界明确时，另起 Spike。 | 可为后续 A 股约束和事件语义提供参考；不改变 CR-030 研究闭环边界。 |
| vn.py / vnpy.alpha | `optional_spike` + `exclude_by_default` | vn.py 静态口径为 MIT；`vnpy.alpha` 可做流程参考，但 gateway / event engine / GUI / 实盘接口过重。 | dataset、Alpha158 / Alpha101、表达式函数、预处理、模型训练、信号、策略回测、实盘衔接流程。 | 不接 gateway、事件引擎、GUI 或实盘接口，不替代 QMT C/S route，不默认引入主框架。 | 当端到端研究流程需要外部流程对标时，做文档级或 fixture-only Spike。 | `vnpy.alpha` 只作为流程参考；项目内部合同仍由 FactorSpec、FactorRunSpec、ExperimentManifest 和 ResearchReportCatalog 承担。 |
| Backtrader | `reference_only` + `forbidden_migration` | CR-025 已确认本地项目 GPLv3；仅作为 lightweight execution engine 的 execution semantic reference。 | 执行语义、订单生命周期、semantic diff、no-copy guardrail、target portfolio / order intent draft 衔接。 | 不默认依赖、不运行、不复制源码、不接 live broker / store、不扩大 CR-025 授权、不作为多因子研究主框架。 | 若后续需要对 order intent draft 和执行语义做更深对照，必须沿用 CR-025 no-copy / no-real-operation 门控。 | 只继承 CR-025 执行语义边界；不承担 FactorSpec、IC / RankIC、manifest 或 admission package 的主框架职责。 |

## 4. CR-026 Qlib isolated runner 后置条件

CR-026 保持后续 Spike candidate，不并入 CR-030 P0，也不与 CR-030 当前 Story 并行启动。2026-06-11 覆盖复核后，CR-026 已收窄为 **Qlib isolated runner optional Spike**：多因子研究主框架、自有合同、factor panel / label window、report catalog、组合实践和策略准入已经由 CR030-039 覆盖；Qlib runtime / qrun / provider_uri / 依赖隔离运行仍未覆盖。

CR-026 重启条件：

| 条件 | 必须满足的证据 |
|---|---|
| 内部合同冻结 | CR030-S02 至 S07 的 FactorPanelContract、LabelWindowSpec、ResearchReportCatalog、runner input/output、failure model 和 StrategyAdmissionPackage 均已完成 CP6 / CP7 或由 meta-po 明确判定合同冻结。 |
| 依赖隔离设计 | 明确不污染默认依赖，不修改主路径依赖锁，隔离环境和回滚策略经 CP5 批准。 |
| provider 禁用 | 明确不使用外部 provider 或官方数据下载，不让 `provider_uri` 接管本项目数据事实源。 |
| 运行授权 | 用户单独批准 CR-026 或 bounded Spike 的运行范围、命令、输入、输出和回归边界。 |
| source-of-truth boundary | Qlib runtime 只能消费内部已冻结合同，不得反向改写内部 truth。 |

| 覆盖状态 | 2026-06-11 结论 |
|---|---|
| 已覆盖 | CR030-039 已覆盖自有多因子研究闭环、合同、组合实践、策略准入和 no-real-operation 边界。 |
| 未覆盖 | Qlib isolated runner runtime、qrun / task 执行、`qlib.init`、`provider_uri`、`.bin` 数据格式、依赖隔离运行和 fixture-only runner 对照。 |
| 当前动作 | 保留 CR-026 为 narrowed optional Spike；启动前必须重新做冲突预检、依赖隔离设计和用户运行授权。 |

## 5. No-Real-Operation 计数合同

| 操作类别 | 本轮计数 | 状态 | 说明 |
|---|---:|---|---|
| external_project_clone | 0 | not-authorized | 不 clone 外部项目。 |
| external_project_install | 0 | not-authorized | 不安装 Qlib、Alphalens、vectorbt、PyBroker、bt、Zipline Reloaded、LEAN、RQAlpha、vn.py 或 Backtrader。 |
| external_project_run | 0 | not-authorized | 不运行 qrun、Notebook、外部 runner、外部样例或外部测试。 |
| source_migration_or_vendor | 0 | not-authorized | 不复制、裁剪、改写、vendor、fork 或迁移外部源码、样例、测试、数据。 |
| dependency_change | 0 | not-authorized | 不修改 `pyproject.toml` 或 `uv.lock`。 |
| provider_fetch | 0 | not-authorized | 不触发真实 provider、联网补数或外部 provider。 |
| lake_write | 0 | not-authorized | 不写 raw / manifest / canonical / gold / quality / catalog。 |
| catalog_publish | 0 | not-authorized | 不 publish current pointer，不把验证结果提升为 catalog truth。 |
| reports_overwrite | 0 | not-authorized | 不覆盖历史报告或 `data/reports` 产物。 |
| qmt_operation | 0 | not-authorized | 不调用 QMT / MiniQMT / XtQuant，不启动 gateway。 |
| simulation_or_live | 0 | not-authorized | 不进入 simulation、live_readonly、small_live、scale_up 或真实 live。 |
| account_or_order_operation | 0 | not-authorized | 不发单、不撤单、不查询账户、不生成真实 broker order。 |
| credential_read | 0 | not-authorized | 不读取、打印、记录或保存 `.env`、token、session、cookie、交易密码、私钥、账户配置或任何凭据。 |

## 6. 后续 Story 消费规则

| 下游 Story | 消费方式 | 禁止误读 |
|---|---|---|
| CR030-S02 | 用本矩阵作为 FactorSpec / FactorRunSpec 的 external cross-check 词汇表。 | 不得直接采用外部对象作为内部 schema truth。 |
| CR030-S03 | 用 Qlib / Alphalens / Zipline 的数据面板和标签概念做边界对照。 | 不得引入外部 provider、bundle、calendar 或 `.bin`。 |
| CR030-S04 | 用 Alphalens / Qlib 指标口径对照 IC / RankIC / 分层收益。 | 不得运行 Alphalens 或 Qlib 报告。 |
| CR030-S05 | 用 Qlib / bt / LEAN 的组合概念对照可解释组合。 | 不得启用外部 optimizer 或生成 broker order。 |
| CR030-S06 | 用 Qlib Recorder 概念对照 manifest / catalog。 | 不得采用 MLflow / pickle 作为默认事实源，不 publish。 |
| CR030-S07 | 用 LEAN 分层和 CR-025 order intent draft 对照 admission package。 | 不得声明为 QMT-ready、simulation-ready、live-ready、production truth 或真实可交易证据。 |
| CR030-S08 | 汇总安全文档和 follow-up Spike 边界。 | 不得把 CP5 approve 解释为真实运行或交易授权。 |

## 7. 回滚与重访

若后续发现许可证、依赖或运行边界与本文冲突，默认处理为 `optional_spike` 或 `exclude_by_default`，不阻塞项目自有多因子研究闭环主线。任何扩大到依赖变更、外部运行、源码迁移、provider / lake / publish、QMT / simulation / live 或凭据读取的请求，必须停止当前 Story 路线并交由 meta-po 发起独立 CR / Spike / per-run 授权。
