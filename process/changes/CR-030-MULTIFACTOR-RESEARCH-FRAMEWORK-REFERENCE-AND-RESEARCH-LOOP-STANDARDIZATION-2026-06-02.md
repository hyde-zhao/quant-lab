---
cr_id: "CR-030"
title: "多因子研究框架借鉴与研究闭环标准化"
status: "closed-cp8-approved"
impact_level: "high"
workflow_mode_before: "standard"
workflow_mode_after_change: "standard"
fast_lane_upgrade_reason: "该变更涉及多因子研究对象模型、因子评估、组合构建、研究到回测 / 模拟 / 实盘交接边界、外部开源项目借鉴边界和后续 QMT 路线输入，必须按 standard 模式进入 CP2/CP3/CP4/CP5/CP6/CP7/CP8。"
rollback_to: "requirement-clarification"
approval_result: "cp8-approved-closed"
created_at: "2026-06-02T23:24:25+08:00"
created_by: "meta-po"
approved_by: "user"
approved_at: "2026-06-02T23:24:25+08:00"
approval_text: "完成CR-030的编写，编写的CR需要有足够的上下文，编写后后我要清除上下文了"
closed_by: "user"
closed_at: "2026-06-04T06:46:13+08:00"
close_approval_text: "我验证完了，你可以关闭CR-030了"
source: "cp8-follow-up"
source_tracking: "process/changes/CR-019-FOLLOW-UP-TRACKING-2026-05-31.md"
cr_index_path: "process/changes/CR-INDEX.yaml"
parent_cr: "CR-019"
source_checkpoint: "checkpoints/CP8-CR019-DELIVERY-READINESS.md"
source_decision_id: "D-CP8-CR019-05"
predecessor_cr: "CR-025"
predecessor_status: "closed-cp8-approved"
predecessor_checkpoint: "checkpoints/CP8-CR025-DELIVERY-READINESS.md"
related_candidates: ["CR-026", "CR-020", "CR-021", "CR-022", "CR-023", "CR-024"]
follow_up_type: "multifactor-research-framework-reference-and-research-loop-standardization"
risk_class: "research_framework_architecture_dependency_license_and_research_to_execution_governance"
owner: "meta-po"
runtime_authorization: "none"
external_repo_authorization: "static-research-only-after-cp2-cp3-revalidation; no clone/install/run/source-copy authorized by this CR creation"
acceptance_criteria: "CP2 确认多因子研究场景和范围；CP3 确认项目自有研究闭环架构、外部项目借鉴 / 不借鉴清单和依赖 / 许可证边界；CP4 生成 Story DAG 与并行安全预检；CP5 全量 LLD 确认；CP6/CP7 完成实现和验证；CP8 关闭时形成文档、后续 CR 分流和真实 QMT 路线输入。"
close_condition: "CR-030 范围内的多因子研究闭环正式文档、实现、验证和文档交付均完成，且 CP8 用户确认通过。"
analysis_artifacts:
  - "process/research/CR030-MULTIFACTOR-FRAMEWORK-REFERENCE-ANALYSIS-2026-06-03.md"
  - "process/discussions/CP2-CR030-SCENARIO-DISCUSSION-LOG.md"
  - "process/checks/CP2-CR030-DISCUSSION-CHECKPOINT.json"
  - "process/handoffs/META-PM-CR030-REQ-CLARIFICATION-2026-06-03.md"
  - "process/handoffs/META-PO-CR030-EXTERNAL-REFERENCE-RESEARCH-2026-06-03.md"
  - "process/discussions/CP3-CR030-HLD-DISCUSSION-LOG.md"
  - "process/checks/CP3-CR030-DISCUSSION-CHECKPOINT.json"
  - "process/checks/CP3-CR030-HLD-CONSISTENCY.md"
  - "checkpoints/CP3-CR030-HLD-REVIEW.md"
  - "process/checks/CP4-CR030-STORY-DAG-PARALLEL-SAFETY.md"
  - "checkpoints/CP5-CR030-MULTIFACTOR-RESEARCH-LOOP-BATCH-A-LLD-BATCH.md"
  - "process/handoffs/META-SE-CR030-HLD-2026-06-03.md"
  - "process/checks/CP8-CR030-DELIVERY-READINESS.md"
  - "checkpoints/CP8-CR030-DELIVERY-READINESS.md"
---

# CR-030 多因子研究框架借鉴与研究闭环标准化

## 0. 本 CR 的作用

本 CR 将 `process/changes/CR-019-FOLLOW-UP-TRACKING-2026-05-31.md` 中登记的后续候选项 `CR-030` 转为正式 CR。用户要求在清除对话上下文前完成 CR 编写，因此本文件必须承担恢复上下文的职责：后续继续推进时，应优先读取本文件、`process/STATE.md`、`process/changes/CR-INDEX.yaml` 和后续跟踪表，而不是依赖历史聊天记录。

本 CR 只授权完成正式 CR 编写和 CR 跟踪状态同步，不授权实现、不授权安装依赖、不授权运行外部项目、不授权克隆 / 迁移源码、不授权真实 provider / lake / publish / simulation / live / QMT / credential / broker 操作。

## 1. 变更摘要

当前系统定位不是开发通用大型量化框架，而是建设生产级的策略研究回测、模拟盘和实盘框架。用户已明确补充：本系统主要用于多因子策略的研究和回测，后续需要衔接模拟盘与真实 QMT 路线，但现阶段不能把“框架规模做大”误当成目标。

CR-025 已关闭，主要解决轻量执行引擎和 Backtrader 借鉴边界，包括：

- 保持项目自有轻量执行语义，不引入 Backtrader 运行依赖。
- 采用 Backtrader GPLv3 no-copy 方案：只做概念和测试语义借鉴，不复制源码，不迁移 GPL 代码。
- 建立 `order_intent_draft_v1` 作为研究 / 回测到 QMT 消费前的草稿边界。
- 明确 CR-025 不授权真实 broker、QMT、provider、lake、publish、simulation、live、credential 操作。

CR-025 对执行语义有价值，但没有补齐多因子研究闭环。本 CR 的目标是补齐项目自有的多因子研究对象模型、评估指标、组合构建、实验追溯和研究到执行交接边界，同时在 HLD 中记录可借鉴的 GitHub 成熟项目与不可引入 / 不可迁移的边界。

## 2. 背景与已知事实

### 2.1 用户目标

用户已经澄清：

- 目标不是开发“巨型通用框架”。
- 目标是生产级策略研究回测、模拟盘和实盘框架。
- 当前系统主要做多因子策略研究和回测。
- 后续真实 QMT 路线仍重要，但应在研究闭环和准入证据更清晰后推进。

因此 CR-030 的设计应以“多因子研究闭环可生产化”为中心，而不是围绕某一个外部框架做全面集成。

### 2.2 CR-025 的输入与边界

CR-025 已关闭，可作为 CR-030 的前置输入：

- `process/changes/CR-025-BACKTRADER-OPTIONAL-EXECUTION-BACKEND-HARDENING-2026-05-31.md`
- `process/HLD.md` 中 CR-025 相关章节
- `process/STORY-BACKLOG.md` 中 CR-025 Story
- `process/DEVELOPMENT-PLAN.yaml` 中 CR-025 计划
- `checkpoints/CP8-CR025-DELIVERY-READINESS.md`
- `README.md`、`docs/USER-MANUAL.md` 中 CR-025 交付说明

CR-025 可继承给 CR-030 的部分：

| CR-025 输出 | 对 CR-030 的意义 |
|---|---|
| `clean_feed` 输入边界 | 因子研究评估也必须基于受控、可追溯、已对齐的数据输入，而不是直接读取不明来源行情。 |
| semantic diff / regression evidence | 多因子组合和研究指标需要相同风格的语义回归证据，避免只比较原始收益曲线。 |
| `order_intent_draft_v1` | CR-030 的研究输出若进入执行链路，只能生成草稿级意图，不直接驱动 QMT。 |
| no-copy Backtrader 决策 | 外部项目借鉴统一遵守 no-copy / no-runtime / no-dependency-default 原则，除非后续 CP3/CP5 单独授权。 |
| runtime authorization none | 研究框架设计通过不等于真实运行授权。 |

CR-025 没有覆盖的部分，也是 CR-030 的主要缺口：

- `FactorSpec` / `FactorRunSpec` 的正式契约。
- 多因子 `FactorPanel`、标签窗口、点时一致性、缺失值 / 停牌 / 复权处理在研究层的归档方式。
- IC / RankIC / 分层收益 / 换手 / 覆盖率 / 稳定性 / 横截面暴露等因子评价。
- 单因子到多因子组合的标准化流程。
- 因子实验追溯、报告目录和可复现实验清单。
- 研究结论到回测 / 模拟 / 实盘准入的证据包。

### 2.3 CR-029 与真实数据准入背景

CR-029 已记录真实数据湖与 benchmark 准入验证，但 Stage6 当前没有可进入 QMT 的策略准入项：

- `process/changes/CR-029-STAGE6-DATA-LAKE-ADMISSION-BENCHMARK-REAL-RUN-2026-05-31.md`
- 关键结论：真实数据 / benchmark 验证可作为研究质量输入。
- 关键限制：`qmt_admission_allowed_count=0` 时不得启动真实 QMT 路线。

CR-030 应把真实数据和 benchmark 证据转化为多因子研究准入标准，而不是绕过准入直接进入 QMT。

### 2.4 CR-026 的关系

`CR-026` 是后续候选项，主题为 Qlib 隔离 runner / 多因子框架集成。它和 CR-030 有明显重叠：

- CR-026 更像“是否引入 Qlib 作为隔离研究 runner”的专项候选。
- CR-030 更像“项目自有多因子研究闭环标准化”的主线 CR。

本 CR 启动后，CP2/CP3 必须决策 CR-026 的去向：

- 合并到 CR-030，作为外部项目候选调研和可选 runner Spike。
- 保留为独立后续 CR，仅在 CR-030 定义好自有契约后再评估。
- 取消或降级为文档调研项。

在该决策未完成前，CR-030 不得默认安装、运行或接入 Qlib。

### 2.5 QMT 路线的关系

QMT 相关后续候选为 `CR-020` 到 `CR-024`，当前仍是候选 / 未授权状态。CR-030 只能为 QMT 路线准备研究层证据和交接契约，不得启动真实 QMT：

- 不连接真实 QMT。
- 不读取或写入 QMT 凭据。
- 不启动模拟盘、实盘、真实 broker。
- 不发布真实交易信号。
- 不把 `order_intent_draft_v1` 解释为可直接成交的委托。

### 2.6 2026-06-03 本轮新增分析事实

用户补充：Qlib 已下载到 `/home/hyde/download/qlib`，并授权本轮开启子 agent 做 web search。该授权只覆盖静态分析和公开资料调研，不授权安装、运行、clone、复制源码、修改依赖、provider / lake / publish、QMT / simulation / live 或凭据读取。

本轮已新增以下 CP2 输入产物：

| 产物 | 路径 | 用途 |
|---|---|---|
| 多因子框架借鉴与适配分析 | `process/research/CR030-MULTIFACTOR-FRAMEWORK-REFERENCE-ANALYSIS-2026-06-03.md` | 记录 Qlib 本地模块分析、外部项目借鉴矩阵、本项目能力映射、CR-026 分流和建议契约 |
| CP2 场景讨论日志 | `process/discussions/CP2-CR030-SCENARIO-DISCUSSION-LOG.md` | 记录 Scenario Gray Areas、Deferred Ideas、待人工决策草案和 CP2 正式化建议 |
| CP2 discussion checkpoint | `process/checks/CP2-CR030-DISCUSSION-CHECKPOINT.json` | 记录 discussion 输入已收敛，但正式 CP2 human gate 尚未发起 |
| meta-pm 交还摘要 | `process/handoffs/META-PM-CR030-REQ-CLARIFICATION-2026-06-03.md` | 记录 pm-chen 对 UC-20..UC-27、REQ-174..REQ-185 和 CR-026 分流的建议 |
| 外部调研交接摘要 | `process/handoffs/META-PO-CR030-EXTERNAL-REFERENCE-RESEARCH-2026-06-03.md` | 记录 Curie / Ampere 两个 explorer 子 agent 的公开资料调研摘要 |

本轮静态分析结论：

1. Qlib 最值得借鉴的是 qrun / task 配置化、DataHandler / Processor、Recorder / RecordTemp、SignalRecord / SigAnaRecord / PortAnaRecord、IC / RankIC / long-short / turnover 指标、TopkDropout 和 EnhancedIndexing 的组合语义。
2. Qlib 不应直接作为本项目默认 runtime：不采用 `.bin` 数据格式、`provider_uri`、`qlib.init`、官方数据下载、MLflow / pickle recorder、完整 qrun 入口或默认 optimizer 依赖。
3. Alphalens 适合借鉴因子评价和 tear sheet 口径；vectorbt / PyBroker 适合可选 Spike；bt 适合组合 DSL 参考；Zipline Reloaded 适合 Pipeline 因子管线参考；QuantConnect LEAN 适合 Alpha / Portfolio / Risk / Execution 分层参考；RQAlpha 许可证需谨慎，按限制性 / 需授权处理；vn.py / vnpy.alpha 可作为端到端流程 Spike。
4. 本项目已有 `engine/research_dataset.py`、`experiments/run_experiment_17_21_factor_suite.py`、`engine/stage6_admission.py`、`engine/semantic_diff.py` 和 CR-011 factor panel audit，应优先标准化和复用，不应从零重做平行多因子框架。
5. CR-026 推荐保留为 Qlib isolated runner 后续 Spike candidate，等待 CR-030 冻结 `FactorPanelContract`、`LabelWindowSpec`、`ResearchReportCatalog`、runner input/output、failure model、dependency isolation 和 source-of-truth boundary 后再启动。

### 2.7 2026-06-11 后续 CR 覆盖回写

用户要求检查 `CR-026`、`CR-027`、`CR-028` 是否已被 CR030-039 覆盖。本 CR 作为 CR026 重叠能力的主覆盖来源，结论如下：

| 候选项 | 覆盖状态 | 本 CR / CR030-039 已覆盖部分 | 未覆盖 / 保留部分 | 处理结论 |
|---|---|---|---|---|
| CR-026 `qlib_w7` | partial-covered / narrowed | CR030 已覆盖 Qlib 静态分析、外部项目参考矩阵、自有多因子研究合同、FactorPanelContract、LabelWindowSpec、ResearchReportCatalog、StrategyAdmissionPackage、no-runtime / no-provider / no-copy 边界；CR035-039 已覆盖模型、异象、稳健性、组合实践和策略准入的本地离线研究链路。 | Qlib isolated runner runtime、qrun / task 执行、`qlib.init`、`provider_uri`、`.bin` 数据格式、依赖隔离运行和 fixture-only runner 对照未覆盖。 | CR-026 不再作为宽泛 factor workflow CR；仅保留为可选 Qlib isolated runner Spike，需独立 CP2/CP3/CP5 和用户运行授权。 |
| CR-027 `minute_spike` | not-covered | CR030-039 只保持 minute 不授权边界，未证明 minute 需求成立。 | minute source / schema / storage / quality、minute cost model、bounded experiment、真实 minute 数据抓取均未覆盖。 | 继续保留后置 Spike 候选；不得因 CR030-039 关闭而标记 covered。 |
| CR-028 `level2_spike` | not-covered | CR030-039 只保持 Level2 不授权边界，未证明 Level2 需求成立。 | Level2 data rights、order-book schema、queue / impact-cost model、replay fixture、redaction 和 live quote 权限验证均未覆盖。 | 继续保留后置 Spike 候选；不得因 CR030-039 关闭而标记 covered。 |

## 3. 变更目标

CR-030 的目标是建立项目自有的多因子研究闭环，并在设计层明确哪些外部项目可以借鉴、哪些不引入、哪些只作为后续 Spike。

目标包括：

1. 定义多因子研究的核心对象和契约，包括 `FactorSpec`、`FactorRunSpec`、`FactorPanelContract`、`LabelWindowSpec`、`FactorEvaluationReport`、`ExperimentManifest`、`StrategyAdmissionPackage`。
2. 建立单因子和多因子评价标准，包括 IC、RankIC、分层收益、换手、覆盖率、稳定性、行业 / 风格暴露、缺失值和异常处理。
3. 建立多因子组合构建流程，包括标准化、中性化、正交化、权重合成、约束、组合构建与 turnover 控制。
4. 建立研究实验追溯和报告目录，使一次因子研究可复现、可审计、可进入后续准入。
5. 建立研究到执行的交接边界，明确何时只生成研究报告，何时允许生成 `order_intent_draft_v1`，何时必须等待 QMT 后续 CR。
6. 在 HLD 中记录外部 GitHub 项目的借鉴矩阵，包括可借鉴模块、不可引入模块、依赖 / 许可证 / 运行边界和迁移禁止项。

## 4. 非目标

本 CR 不做以下事项：

- 不实现真实 QMT、真实 broker、模拟盘或实盘。
- 不接入真实 provider，不拉取外部真实数据。
- 不写入 lake，不执行 publish。
- 不安装或运行外部 GitHub 项目。
- 不复制 Qlib、Backtrader、Alphalens、Zipline、Lean、RQAlpha、vn.py、vectorbt 等项目源码。
- 不把外部项目作为默认运行时依赖写入 `pyproject.toml` / `uv.lock`。
- 不把多因子研究框架扩展成大型通用量化平台。
- 不绕过 CP2/CP3/CP5 直接实现。

## 5. 外部项目借鉴候选清单

下表是 CR-030 当前候选调研面，不是已确认的引入清单。CP2/CP3 必须重新核验各项目截至当时的官方仓库状态、许可证、维护情况、依赖、API、数据假设和适用边界。CR 创建本身不授权 clone、install、run、source copy 或依赖变更。

| 候选项目 | 借鉴方向 | 可能适用点 | 默认边界 |
|---|---|---|---|
| Qlib | 多因子研究流程、数据层抽象、模型训练和回测研究闭环 | `FactorRunSpec`、实验配置、研究报告、可选隔离 runner Spike | 不默认安装；不默认作为 runtime dependency；是否合并 CR-026 需 CP2/CP3 决策。 |
| Alphalens | 因子评价指标和 tear sheet 思路 | IC / RankIC、分层收益、分位数组合、turnover、因子可视化报告 | 借鉴指标语义和报告结构；不复制源码；不默认引入 pyfolio / pandas 生态依赖。 |
| vectorbt | 向量化回测、参数扫描、组合计算 | 批量参数实验、向量化评估、快速研究反馈 | 只作为设计参考；是否引入依赖需 CP3/CP5 单独授权。 |
| Zipline Reloaded | Pipeline / research pipeline / event backtest 边界 | 因子管线、数据 bundle、资产域和交易日历处理 | 不默认迁移；注意许可证和数据假设；只做概念参考。 |
| QuantConnect LEAN | 生产级算法生命周期和研究到交易分层 | 研究 / 回测 / 模拟 / 实盘生命周期、准入分层、风险控制 | 不引入庞大运行时；只借鉴边界和准入思想。 |
| RQAlpha | 国内市场回测框架、事件循环、撮合和风控 | A 股上下文、交易日历、撮合与账户语义 | 与 CR-025 执行层关系需 CP3 明确；不默认替换 lightweight engine。 |
| vn.py / vnpy.alpha | 实盘交易生态和多因子扩展思路 | 因子研究到交易系统衔接、实盘边界和工程治理 | 不启动真实交易；不接入网关；只作为后续 QMT 路线边界参考。 |
| PyBroker | 策略研究、特征、ML 模型和回测 | 特征注册、模型训练与策略评估流程 | 仅候选参考；依赖和许可证需复核。 |
| bt | 组合构建和资产配置风格回测 | 权重构建、组合 rebalance、策略树组合 | 只借鉴组合构建 DSL / rebalance 思路。 |
| Backtrader | 执行语义、订单生命周期、测试语义 | 已由 CR-025 处理；CR-030 仅继承边界，不扩大引入范围 | GPLv3 no-copy；不运行、不复制、不迁移。 |

## 6. 建议形成的项目自有契约

以下契约是 CR-030 的候选设计输入，正式名称、字段和文件布局由 CP3 HLD 与 CP5 LLD 确认。

| 契约 / 产物 | 目的 | 必须回答的问题 |
|---|---|---|
| `FactorSpec` | 描述一个因子的稳定定义 | 因子名、版本、输入字段、计算窗口、适用股票池、点时规则、缺失值策略、依赖数据。 |
| `FactorRunSpec` | 描述一次因子计算 / 评价运行 | 数据快照、日期范围、股票池、benchmark、标签窗口、过滤条件、输出路径和运行 ID。 |
| `FactorPanelContract` | 描述因子面板数据契约 | index、columns、频率、点时一致性、缺失值、停牌、复权、行业 / 风格暴露字段。 |
| `LabelWindowSpec` | 描述收益标签和未来窗口 | horizon、收益口径、benchmark-adjusted、行业中性口径、未来数据防泄漏约束。 |
| `FactorEvaluationMetrics` | 定义单因子评价指标 | IC、RankIC、ICIR、分层收益、long-short、turnover、覆盖率、稳定性、分组暴露。 |
| `FactorEvaluationReport` | 输出可审计因子报告 | 指标表、图表索引、异常摘要、数据覆盖、通过 / 失败准入结论。 |
| `MultiFactorCombiner` | 定义多因子合成方式 | 标准化、中性化、正交化、加权、模型合成、约束和回测输入。 |
| `ExperimentManifest` | 保证研究可复现 | 运行参数、代码版本、数据版本、输入输出、指标摘要、异常和人工备注。 |
| `StrategyAdmissionPackage` | 将研究结论转成后续准入材料 | 因子证据、组合证据、风险摘要、回测摘要、是否允许进入 QMT 后续 CR。 |
| `ResearchToExecutionHandoff` | 连接研究和执行边界 | 何时只输出报告，何时输出 `order_intent_draft_v1`，何时必须等待 QMT 授权。 |
| `ResearchReportCatalog` | 管理研究报告目录 | 报告 ID、运行 ID、关联因子、数据快照、准入状态和文档路径。 |

## 7. 候选 Story / Wave 草案

以下只是 CR 创建阶段的初始候选，不代表已批准 Story。正式 Story 必须由 CP2/CP3 后的 `process/STORY-BACKLOG.md` 和 `process/DEVELOPMENT-PLAN.yaml` 确认。

| Story ID | 候选标题 | 预期输出 | 依赖 |
|---|---|---|---|
| CR030-S01 | 外部项目调研矩阵与许可证 / 依赖边界 | GitHub 项目借鉴矩阵、no-copy / no-runtime / dependency guardrail、CR-026 分流建议 | CP2 范围确认 |
| CR030-S02 | `FactorSpec` / `FactorRunSpec` 契约 | 研究对象 schema、字段说明、校验规则、最小示例 | CR030-S01 |
| CR030-S03 | `FactorPanelContract` 与 `LabelWindowSpec` | 因子面板、标签窗口、点时一致性、缺失值和数据泄漏防护 | CR030-S02 |
| CR030-S04 | 单因子评价指标与报告 | IC / RankIC / 分层收益 / turnover / 覆盖率 / 稳定性报告 | CR030-S03 |
| CR030-S05 | 多因子组合与组合构建 | 标准化、中性化、合成、组合权重和约束 | CR030-S04 |
| CR030-S06 | `ExperimentManifest` 与报告目录 | 可复现实验清单、报告索引、运行证据追溯 | CR030-S04 |
| CR030-S07 | `StrategyAdmissionPackage` 与研究到执行交接 | 准入证据包、`order_intent_draft_v1` 生成边界、QMT 后续 CR 输入 | CR030-S05, CR030-S06 |
| CR030-S08 | 文档与无真实运行护栏 | README / USER-MANUAL / guardrail / 不授权说明 | CR030-S01 到 CR030-S07 |
| CR030-S09 | Qlib / 外部 runner Spike 分流 | 是否合并 CR-026、是否后续单独启动 runner Spike | CR030-S01 |

## 8. 五维度影响分析

| 维度 | 是否影响 | 影响说明 | 初始结论 |
|---|---:|---|---|
| 需求 / 场景 | 是 | 需要把“多因子策略研究和回测”从泛化策略研究中提升为明确主场景，并补充研究报告、因子评价、准入证据和 QMT 交接边界。 | 进入 CP2 需求重整。 |
| 架构 / HLD | 是 | 需要新增或重构研究层对象模型、报告目录、实验追溯和研究到执行 handoff；需要记录外部项目借鉴矩阵。 | 进入 CP3 HLD。 |
| Story / LLD | 是 | 预计至少 8 个候选 Story，需要全量 LLD 后再进入实现。 | CP4/CP5 门控。 |
| 实现 / 测试 | 是 | 影响因子研究模块、实验模块、回测输入、报告和 guardrail；需要指标级、契约级、回归级测试。 | CP6/CP7 逐 Story 验证。 |
| 文档 / 运维 | 是 | README、USER-MANUAL、CR 跟踪、研究手册和不授权边界都需要更新。 | CP8 关闭时统一确认。 |

## 9. 文档处理决策

| 文档 | 处理方式 | 原因 | 当前状态 |
|---|---|---|---|
| `process/USE-CASES.md` | 更新原文档，保留旧基线和修订记录 | 多因子研究主场景需要正式进入场景文档。 | pending-CP2 |
| `process/REQUIREMENTS.md` | 更新原文档，保留旧基线和修订记录 | 需要新增多因子研究闭环、指标、报告和准入需求。 | pending-CP2 |
| `process/HLD.md` | 更新原文档，保留 CR-025 章节，新增 CR-030 HLD 章节 | 需要明确研究层架构、外部项目借鉴矩阵和 QMT 交接边界。 | pending-CP3 |
| `process/ARCHITECTURE-DECISION.md` | 更新原文档 | 需要记录自有契约优先、外部项目 no-copy/no-runtime、CR-026 分流等 ADR。 | pending-CP3 |
| `process/STORY-BACKLOG.md` | 更新原文档 | 需要新增 CR-030 Story，并标注与 CR-025 / QMT 候选的依赖。 | pending-CP4 |
| `process/DEVELOPMENT-PLAN.yaml` | 更新原文档 | 需要新增 CR-030 Wave、LLD 批次和门控计划。 | pending-CP4 |
| `process/TEST-STRATEGY.md` | 更新原文档 | 需要定义因子评价、组合构建、实验追溯和不授权护栏测试。 | pending-CP6/CP7 |
| `README.md` | 更新原文档 | 需要说明多因子研究闭环和外部项目借鉴边界。 | pending-CP8 |
| `docs/USER-MANUAL.md` | 更新原文档 | 需要说明用户如何运行研究、读取报告、理解准入和不授权项。 | pending-CP8 |
| `process/changes/CR-019-FOLLOW-UP-TRACKING-2026-05-31.md` | 更新原文档 | CR-030 已从 candidate 转为 active formal CR，并在 CP8 approved 后关闭。 | closed-cp8-approved |
| `process/changes/CR-INDEX.yaml` | 更新原文档 | 保持 active formal CR 与后续候选一致性。 | approved-by-this-intake |
| `process/STATE.md` | 更新原文档 | 恢复点必须指向 CR-030 closed-cp8-approved，并清空 active_change。 | closed-cp8-approved |

## 10. 冲突预检

| 检查项 | 结果 | 说明 |
|---|---|---|
| `STATE.md.active_change` | PASS | CR-025 关闭后 `active_change` 为空，可启动 CR-030。 |
| active formal CR | PASS | `CR-INDEX.yaml` 当前无 active formal CR。 |
| CR-025 状态 | PASS | CR-025 已关闭，可作为 CR-030 前置输入，不形成执行冲突。 |
| CR-030 candidate | PASS | CR-030 已在后续台账登记，允许按用户指令转正式 CR。 |
| CR-026 重叠 | ATTENTION | CR-026 与 CR-030 在 Qlib / 多因子框架方向重叠，但 CR-026 仍为 candidate，不阻断启动；CP2/CP3 必须分流。 |
| QMT 路线候选 | ATTENTION | CR-020 到 CR-024 仍未授权；CR-030 不得启动真实 QMT。 |
| 外部项目运行 | BLOCKED-BY-DESIGN | 本 CR 创建不授权 clone / install / run / dependency change / source copy。 |
| 文档影响 | EXPECTED | `USE-CASES.md`、`REQUIREMENTS.md`、`HLD.md`、`STORY-BACKLOG.md`、`DEVELOPMENT-PLAN.yaml` 后续需要变更。 |

## 11. 待人工决策项

以下决策项需要在 CP2 / CP3 前后进入 `process/STATE.md.human_gate_decisions.pending_human_decisions[]` 或对应 Decision Brief，不能只停留在本 CR。

| 决策 ID | 决策类型 | 待确认问题 | 推荐方案 | 备选方案 | 影响 / 风险 | 回退 / 切换条件 |
|---|---|---|---|---|---|---|
| DQ-CP2-CR030-01 | scope | CR-030 是否作为多因子研究闭环主线，并覆盖 CR-026 的 Qlib 候选分流？ | CR-030 作为主线；CR-026 暂作为 Qlib runner Spike 候选，不单独启动。 | 独立启动 CR-026；或取消 CR-026。 | 若并行启动会导致 HLD / Story 重叠；若取消过早可能遗漏 Qlib 优势。 | CP3 发现 Qlib runner 是必要主路径时，可把 CR-026 升级为子 CR。 |
| DQ-CP2-CR030-02 | scope | 外部项目调研面是否包含 Qlib、Alphalens、vectorbt、Zipline Reloaded、LEAN、RQAlpha、vn.py、PyBroker、bt、Backtrader？ | 全部作为调研候选，但只做静态设计借鉴和许可证 / 依赖复核。 | 收窄到 Qlib + Alphalens + vectorbt；或仅做 Qlib。 | 调研面太宽会增加设计成本；太窄会错过成熟实践。 | CP2 可按用户优先级收窄，CP3 再补充候选。 |
| DQ-CP2-CR030-03 | implementation | 多因子研究契约是否采用项目自有命名和 schema？ | 使用项目自有契约，外部项目只映射到自有契约。 | 直接采用某外部项目对象模型；或只写文档不建契约。 | 直接采用外部模型会带来依赖 / 许可证 / 迁移风险；只写文档会弱化可执行性。 | CP3 若证明外部对象模型更稳定，可改为适配层，但需单独依赖决策。 |
| DQ-CP2-CR030-04 | runtime_authorization | CP2 是否授权运行、安装、克隆外部项目或真实 provider / QMT 操作？ | 不授权。CP2 只确认需求、场景和调研范围。 | 授权静态官方资料查阅；授权隔离 clone / install Spike。 | 运行授权会扩大安全、依赖和许可证风险。 | 只有用户在后续 CP3/CP5 明确授权，才可变更。 |
| DQ-CP3-CR030-01 | architecture | 架构主选应是项目自有多因子契约，还是 Qlib runner-first，或完整外部框架集成？ | 项目自有多因子契约为主，外部项目作为参考和可选 Spike。 | Qlib runner-first；完整外部框架集成。 | runner-first 可能快速但受外部数据 / 依赖制约；完整集成超出当前目标。 | 如果自有契约无法覆盖核心研究能力，可切换到 runner-first。 |
| DQ-CP3-CR030-02 | implementation | Story 是否按契约、数据、评价、组合、追溯、准入、文档分组？ | 采用分层 Story，先契约再指标再组合再准入。 | 按外部项目模块拆分；或按实验脚本拆分。 | 分层 Story 更稳但初期文档多；脚本式拆分更快但难以生产化。 | CP4 DAG 发现依赖过重时可重排 Wave。 |

## 12. LLD 与实现门控

CR-030 必须遵守标准门控：

- CP2 未通过前，不得修改正式需求 / 场景基线之外的实现对象。
- CP3 HLD 未通过前，不得拆分最终 Story。
- CP4 自动预检未通过前，不得开始全量 LLD。
- CP5 全量 LLD 未通过前，不得进入实现。
- CP6/CP7 必须逐 Story 记录开发和验证证据。
- CP8 必须区分关闭范围、不授权范围、风险接受和后续 CR 候选。

建议的 LLD 批次：

```yaml
batch_id: "CR030-MULTIFACTOR-RESEARCH-LOOP-BATCH-A"
status: "pending-cp4-cp5"
scope:
  - "CR030-S01"
  - "CR030-S02"
  - "CR030-S03"
  - "CR030-S04"
  - "CR030-S05"
  - "CR030-S06"
  - "CR030-S07"
  - "CR030-S08"
  - "CR030-S09"
gate:
  cp2_required: true
  cp3_required: true
  cp4_required: true
  cp5_required: true
implementation_before_cp5_authorized: false
```

## 13. 验证方向

CR-030 后续测试策略至少应覆盖：

- 契约校验：`FactorSpec`、`FactorRunSpec`、`FactorPanelContract` 字段完整性、类型、缺失值和日期范围。
- 数据泄漏防护：标签窗口不能读取未来数据，研究报告必须暴露 point-in-time 假设。
- 因子指标：IC、RankIC、分层收益、turnover、覆盖率、稳定性等指标有确定性输入输出。
- 多因子组合：标准化、中性化、权重合成和约束在边界样例下稳定。
- 实验追溯：同一 manifest 能定位输入数据、代码版本、参数和报告。
- 准入证据包：`StrategyAdmissionPackage` 不满足阈值时不得进入 QMT 候选。
- 不授权护栏：无 CP3/CP5 运行授权时不得 clone/install/run 外部项目，不得改 `pyproject.toml` / `uv.lock`，不得触发 provider / lake / publish / QMT。

## 14. 不授权项闭环

如果后续用户回复 `approve` 通过 CP2/CP3/CP5/CP8，应明确说明该 approve 只接受当轮 Decision Brief 中的推荐方案，不表示授权以下操作：

- 不授权克隆、安装、运行 Qlib、Alphalens、vectorbt、Zipline、LEAN、RQAlpha、vn.py、PyBroker、bt 或 Backtrader。
- 不授权复制、迁移、改写外部项目源码。
- 不授权新增第三方依赖，不授权修改 `pyproject.toml` / `uv.lock`。
- 不授权启动 Backtrader 运行时。
- 不授权真实 provider 数据拉取。
- 不授权写 lake、publish 或生成生产数据。
- 不授权真实 broker、QMT、simulation、live、credential 操作。
- 不授权用 `order_intent_draft_v1` 直接下单。

任何上述操作都必须在后续 CP3/CP5 或单独 CR 中作为 `runtime_authorization` 或 `implementation` 决策项显式列出，并由用户明确授权。

## 15. 推荐推进顺序

1. `meta-po` 完成本 CR、`STATE.md`、`CR-INDEX.yaml`、后续台账同步。
2. `meta-po` 委托 `meta-pm` 进入 CP2 前需求 / 场景重整，重点确认多因子研究主场景、评价指标、研究报告、准入边界和 CR-026 分流。
3. CP2 Decision Brief 汇总 DQ-CP2-CR030-*，由用户确认。
4. `meta-po` 委托 `meta-se` 进入 CP3 HLD，要求分析外部 GitHub 项目但只做静态调研和设计借鉴；HLD 中必须写清楚引入 / 不引入 / 仅 Spike / 禁止迁移。
5. CP3 通过后进入 Story 拆解和 CP4 预检。
6. `meta-dev` 全量起草 LLD，CP5 统一确认后再实现。
7. 实现完成后由 `meta-qa` 验证，CP8 由 `meta-po` 关闭或分流后续 CR。

## 16. 初始结论

CR-030 已作为正式 CR 完成并关闭，当前阶段为 `closed-cp8-approved`。它已作为多因子研究闭环主线，完成研究对象模型、因子评价、组合构建、实验追溯和研究到执行准入边界；后续不得把本 CR 关闭误读为直接推进 QMT 或外部框架集成的运行授权。

本 CR 创建后，下一步建议进入 CP2：组织 `meta-pm` 重整 `USE-CASES.md` 和 `REQUIREMENTS.md`，并把本文件中的决策项转入人工决策队列。
