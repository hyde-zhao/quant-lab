---
change_id: "CR-030"
story_id: "CR030-S08-safety-docs-and-follow-up-boundary"
title: "CR-030 多因子研究闭环、安全边界与后续 Spike 分流"
status: "implemented-cp6-ready"
created_at: "2026-06-03"
owner: "meta-dev"
source_lld: "process/stories/CR030-S08-safety-docs-and-follow-up-boundary-LLD.md"
cp5_review: "checkpoints/CP5-CR030-MULTIFACTOR-RESEARCH-LOOP-BATCH-A-LLD-BATCH.md"
---

# CR-030 多因子研究闭环、安全边界与后续 Spike 分流

## 1. 目标与非目标

CR-030 交付项目自有多因子研究闭环的 P0 合同、离线验证入口、研究证据链和模拟盘前策略准备包。用户在 CR-030 完成后，可以基于项目自有合同开展本地多因子研究和本地回测，并把 `StrategyAdmissionPackage` 作为后续模拟盘路线审查的输入。

本文中的“研究和生产”指完成多因子策略的研究与实验闭环，达到策略侧模拟盘入口：策略证据、组合计划、实验 manifest、catalog 引用和 handoff 草稿已具备后续审查输入价值。它不表示 QMT 接口、simulation 账号、gateway、订单通道、账户查询或真实运行授权已经 ready；这些运行侧入口必须等待 CR-020 / CR-021 等后续 CR 单独通过。QMT 接口 ready 且后续运行授权通过后，才可以把该策略侧入口输入到模拟盘流程。

CR-030 不交付外部 runner，不改变依赖，不读取凭据，不触发 provider，不写 lake，不 publish，不启动 QMT / MiniQMT / XtQuant / gateway，不进入 simulation 或 live，不生成真实 broker order，也不把任何研究报告、组合计划、catalog 或 `StrategyAdmissionPackage` 声明为 QMT-ready、simulation-ready、live-ready、production truth 或真实可交易授权。

## 2. CR-030 P0 研究闭环

CR-030 的主线采用项目自有闭环，不把 Qlib、Alphalens、vectorbt、PyBroker、bt、Zipline Reloaded、QuantConnect LEAN、RQAlpha、vn.py / vnpy.alpha 或 Backtrader 设为默认 framework、truth、provider、runner、optimizer 或 report truth。

```text
外部项目静态参考
  -> FactorSpec / FactorRunSpec
  -> FactorPanelContract / LabelWindowSpec
  -> FactorEvaluationReport
  -> MultiFactorPortfolioPlan
  -> ExperimentManifest / ResearchReportCatalog
  -> StrategyAdmissionPackage
  -> no-real-operation safety 与后续 Spike 分流
```

该闭环只使用本项目合同、fixture、静态文档和离线测试验证当前 P0 范围。任何真实数据、外部 runtime、QMT 路线或交易路线都必须另起 CR / Spike / per-run authorization。

## 3. 证据链与 Story 边界

| Story | 交付边界 | 可用证据 | 不授权边界 |
|---|---|---|---|
| CR030-S01-external-reference-matrix-and-loop-contract | 外部项目借鉴矩阵、分类语义、CR-026 后置条件和 no-copy / no-run 合同。 | `docs/CR030-MULTIFACTOR-REFERENCE-MATRIX.md`；`tests/test_cr030_external_reference_guardrails.py`。 | 不运行外部项目，不复制源码，不新增依赖，不把外部对象设为内部 truth。 |
| CR030-S02-factor-spec-run-spec-contract | `FactorSpec` / `FactorRunSpec` 字段、错误码、provenance 和 fail-closed 合同。 | `engine/multifactor_contracts.py`；`tests/test_cr030_factor_spec_run_spec_contract.py`。 | 不采用 Qlib / Alphalens / Zipline / LEAN 对象作为内部 schema truth。 |
| CR030-S03-factor-panel-label-window-fail-closed | `FactorPanelContract`、`LabelWindowSpec`、available_at、label overlap、lineage、复权口径和 quality gate。 | `engine/factor_panel_contracts.py`；`tests/test_cr030_factor_panel_label_window_gates.py`。 | 不允许前视、标签重叠、lineage 缺失或复权混用进入评价和准入。 |
| CR030-S04-factor-evaluation-report | 单因子评价报告、IC / RankIC、分层收益、turnover、capacity、blocked claims 和旧报告只读边界。 | `engine/factor_evaluation.py`；`tests/test_cr030_factor_evaluation_report.py`。 | 不运行 Alphalens，不把外部 tear sheet 或旧报告覆盖为当前 truth。 |
| CR030-S05-multifactor-combiner-portfolio-plan | 可解释规则权重 / 轻量线性组合、组合约束、成本、容量、benchmark 和 portfolio plan 草稿。 | `engine/multifactor_combiner.py`；`tests/test_cr030_multifactor_combiner.py`。 | 不启用 optimizer / ML workflow，不生成 broker order。 |
| CR030-S06-experiment-manifest-report-catalog | `ExperimentManifest`、`ResearchReportCatalog`、config hash、artifact refs、allowed / blocked claims 和旧报告只读边界。 | `engine/research_manifest.py`；`tests/test_cr030_experiment_manifest_catalog.py`。 | 不写真实 lake，不 publish current pointer，不覆盖旧 reports。 |
| CR030-S07-strategy-admission-package-handoff | `StrategyAdmissionPackage`、Stage6 gate summary、blocked reasons、unlock conditions、`order_intent_draft_v1` draft-only ref 和 not-authorized counters。 | `engine/strategy_admission_package.py`；`tests/test_cr030_strategy_admission_package.py`；S07 CP7 PASS。 | 可作为策略侧模拟盘入口审查输入；不构成 QMT-ready、simulation-ready、live-ready、production truth 或真实可交易授权。 |
| CR030-S08-safety-docs-and-follow-up-boundary | 本文档、no-real-operation 静态测试、CP3 / CP5 决策追溯和后续 Spike 分流。 | `docs/CR030-MULTIFACTOR-RESEARCH-LOOP.md`；`tests/test_cr030_no_real_operation_safety.py`。 | 不把文档、CP6、CP7、Story verified 或准入包解释为真实运行许可。 |

## 4. CP3 决策追溯

| 决策 ID | 已接受推荐方案 | S08 落地方式 | 后续重访条件 |
|---|---|---|---|
| DQ-CP3-CR030-01 | 接受 CR30-A 项目自有多因子研究闭环；外部项目只 reference / Spike / exclude / forbidden migration。 | 本文第 2 节固定 P0 主线，不把外部项目设为默认 truth。 | 用户要求 runner-first 时回退到 CR-026 或新 Spike。 |
| DQ-CP3-CR030-02 | 接受项目自有契约 + 现有基线复用 + external cross-check + fail-closed。 | 本文第 3 节串联 S02 / S03 / S04 / S06 合同证据。 | 字段字典或错误码变化时回到对应 Story / LLD。 |
| DQ-CP3-CR030-03 | CR-026 Qlib isolated runner 保持后续 Spike candidate，不并行启动。 | 本文第 8 节列出 CR-026 后置条件。 | 合同冻结、隔离和运行授权明确后启动 CR-026。 |
| DQ-CP3-CR030-04 | MultiFactorCombiner P0 使用可解释组合，EnhancedIndexing / cvxpy / ML optimizer 后置。 | 本文第 8 节把 optimizer、ML workflow 和复杂组合优化归入后续 Spike。 | P0 组合不足且用户接受依赖风险时另起 Spike。 |
| DQ-CP3-CR030-05 | CP3 通过不授权实现、依赖变更、外部项目运行或真实操作。 | 本文第 7 节记录 no-real-operation 表；当前实现只覆盖 LLD 指定文档和测试。 | 任何真实运行需求都必须另起 CR / Spike / per-run authorization。 |
| DQ-CP3-CR030-06 | `StrategyAdmissionPackage` 只输出 `order_intent_draft_v1` 草稿，不生成真实 order。 | 本文第 6 节固定 draft-only handoff 和 CR-020..CR-024 后续路线。 | QMT CR approved 后才允许消费 draft。 |
| DQ-CP3-CR030-07 | 接受静态调研作为 CP3 证据，runtime 细节转后续 Spike。 | 本文第 8 节把外部 runtime 细节作为 non-blocking 后续项管理。 | 实现发现 runtime 阻塞时转 bounded Spike。 |

## 5. 用户可用出口

新建因子研究从 [CR030 因子研究快速开始](CR030-FACTOR-RESEARCH-QUICKSTART.md) 进入；本文继续作为边界、证据链和后续分流说明。

| 出口 | 用户可以做什么 | 必须保留的限制 |
|---|---|---|
| 项目自有多因子研究 | 按 CR030-S02 至 S06 的合同准备因子、标签、评价报告、组合计划、manifest 和 catalog。 | 只能使用已通过 gate 的本项目输入；缺 P0 字段时 fail-closed。 |
| 本地回测 | 使用项目已有离线回测层和 CR030-S05 / S06 的研究 artifact 做本地研究验证。 | 本地回测不是 simulation，不接 broker，不写 QMT 运行证据。 |
| 模拟盘前策略准备包 | 使用 S07 `StrategyAdmissionPackage` 汇总研究证据、Stage6 gate、blocked reasons、unlock conditions 和 draft handoff ref。 | 该准备包表示 `evidence_package_complete_for_follow_up_review` 和策略侧模拟盘入口审查输入；QMT 接口 ready 且后续运行授权通过后才可投入模拟盘，不授权真实模拟盘、QMT、live、账户、订单或 broker lake。 |
| 后续路线审查输入 | 把 CR-030 输出交给 CR-020..CR-024 或 CR-026 / optimizer Spike 做输入。 | 后续路线必须重新经过 CR / CP / stage gate / per-run authorization。 |

## 6. StrategyAdmissionPackage 边界

`StrategyAdmissionPackage` 是研究准入证据包，不是交易许可。它可以包含：

| 对象 | 允许内容 | 禁止内容 |
|---|---|---|
| `allowed_claims` | `multifactor_research_and_local_backtest_evidence`、`pre_sim_strategy_preparation_package` 等研究证据声明。 | 不得声明为 QMT-ready、simulation-ready、live-ready、production truth 或真实可交易声明。 |
| `blocked_claims` | `qmt_ready`、`simulation_ready`、`live_ready`、`real_trading_authorized` 等 blocked claim。 | 把 blocked claim 转为 pass 或 allowed。 |
| `order_intent_draft_v1` | draft id、schema、ref、limitations 和 operation counters。 | symbol / side / target_qty 等可提交 broker order payload。 |
| `pre_sim_strategy_preparation` | `evidence_package_complete_for_follow_up_review`、策略侧模拟盘入口审查输入、not_authorization 和 CR-020..CR-024 后续路线。 | 真实 simulation run、QMT gateway run、account query、order submit 或 order cancel。 |

如果没有 CR-020、CR-021、CR-022、CR-023、CR-024 的独立批准，S07 / S08 必须保持 `MF_ADMISSION_QMT_CR_NOT_AUTHORIZED` 或等价 blocked reason。

## 7. No-Real-Operation 表

| 类别 | 计数 | 状态 | 本轮边界 |
|---|---:|---|---|
| runtime_implementation_enablement | 0 | not-authorized | 不把 CR-030 文档或证据包实现为真实运行开关。 |
| dependency_change | 0 | not-authorized | 不修改 `pyproject.toml` 或 `uv.lock`，不新增外部研究框架依赖。 |
| external_project_clone | 0 | not-authorized | 不 clone 外部项目或下载外部项目源码。 |
| external_project_install | 0 | not-authorized | 不安装 Qlib、Alphalens、vectorbt、PyBroker、bt、Zipline Reloaded、LEAN、RQAlpha、vn.py 或 Backtrader。 |
| external_project_run | 0 | not-authorized | 不运行 qrun、Notebook、外部 runner、外部样例或外部测试。 |
| source_copy_or_vendor | 0 | not-authorized | 不复制、裁剪、改写、vendor、fork 或迁移外部 source copy、样例、测试或数据。 |
| provider_fetch | 0 | not-authorized | 不触发 provider fetch、联网补数或外部 provider。 |
| lake_write | 0 | not-authorized | 不写 raw、manifest、canonical、gold、quality、catalog 或 broker lake。 |
| catalog_publish | 0 | not-authorized | 不 publish current pointer，不把研究结果提升为 catalog truth。 |
| reports_overwrite | 0 | not-authorized | 不覆盖历史报告或旧 `reports/**` artifact。 |
| qmt_operation | 0 | not-authorized | 不调用 QMT、MiniQMT、XtQuant，不启动 gateway，不绑定端口。 |
| simulation_or_live | 0 | not-authorized | 不进入 simulation、live_readonly、small_live、scale_up 或真实 live。 |
| account_or_order_operation | 0 | not-authorized | 不发单、不撤单、不查询账户、不生成真实 broker order。 |
| credential_read | 0 | not-authorized | 不读取、打印、记录或保存 `.env`、token、session、cookie、交易密码、私钥、账户配置或任何凭据。 |

上述计数是 S08 的文档与静态测试边界。它不覆盖未来独立 CR 的运行授权；未来授权必须在对应 CR / CP / stage gate 中重新记录。

## 8. 后续 Spike 与 CR 分流

| 后续项 | 当前状态 | 启动条件 | 当前禁止事项 |
|---|---|---|---|
| CR-026 Qlib isolated runner | 后续 Spike candidate，不进入 CR-030 P0，不并行启动。 | FactorPanelContract、LabelWindowSpec、ResearchReportCatalog、runner I/O、failure model、dependency isolation、provider 禁用、source-of-truth boundary 和用户单独批准均明确。 | 不运行 `/home/hyde/download/qlib`，不调用 qrun，不 import qlib，不使用 provider_uri，不下载数据。 |
| optimizer / EnhancedIndexing / cvxpy | 后续 optimizer Spike。 | P0 可解释组合不足，用户接受依赖和风险模型边界，CP3 / CP5 重新批准。 | 不新增 cvxpy，不默认启用复杂组合优化。 |
| ML workflow | 后续 ML Spike。 | 因子研究目标明确需要 walk-forward、bootstrap、模型训练和缓存合同。 | 不运行 PyBroker、Qlib MLflow、LightGBM 或外部 ML workflow。 |
| vectorbt | 后续 performance / batch Spike。 | 自有批量研究性能瓶颈有量化证据，并完成许可证 / 依赖 / runtime 风险接受。 | 不默认安装，不把 Portfolio stats 设为 report truth。 |
| PyBroker | 后续 ML / walk-forward Spike。 | 用户确认 ML 因子路线和非商业 / 依赖边界。 | 不接外部 data / broker，不运行 ML workflow。 |
| RQAlpha | 后续 A 股事件语义 Spike。 | 许可证、broker 语义和交易接口边界重新评审。 | 不默认依赖，不接 broker，不并入订单 API。 |
| vn.py / vnpy.alpha | 后续端到端流程对照 Spike。 | 用户需要外部流程对标，且 gateway / event engine / GUI / 实盘接口保持隔离。 | 不接 gateway、事件引擎、GUI 或实盘接口。 |
| Backtrader | 继承 CR-025 reference / forbidden migration 边界。 | 只可沿用 CR-025 no-copy / no-real-operation 门控。 | 不复制源码，不运行 Backtrader runtime，不把它当多因子研究主框架。 |

## 9. 常见越界与处理

| 触发语句 / 请求 | 处理方式 |
|---|---|
| “CR-030 已完成，直接启动 QMT / simulation / live。” | blocked；回到 CR-020..CR-024 和 per-run authorization。 |
| “把 Qlib runner 合并进当前 P0。” | blocked；按 CR-026 后置条件另起 Spike。 |
| “安装 vectorbt / PyBroker / RQAlpha / vn.py 试一下。” | blocked；依赖变更和外部 runtime 需要独立 CR / Spike。 |
| “把外部项目样例复制进仓库。” | blocked；source copy / vendor / migration 当前计数必须为 0。 |
| “把 StrategyAdmissionPackage 当作真实交易通过证明。” | blocked；它只能作为研究证据包和后续路线审查输入。 |
| “读取本机凭据来验证真实路径。” | blocked；credential_read 当前计数必须为 0。 |

## 10. 本地静态验证入口

S08 的验证入口只做本地静态 / 文本检查，不读取凭据、不访问 provider、不写 lake、不 publish、不启动 QMT，也不运行外部项目。

```bash
uv run --python 3.11 pytest -q tests/test_cr030_no_real_operation_safety.py
uv run --python 3.11 pytest -q tests/test_cr030_external_reference_guardrails.py tests/test_cr030_factor_spec_run_spec_contract.py tests/test_cr030_factor_panel_label_window_gates.py tests/test_cr030_factor_evaluation_report.py tests/test_cr030_multifactor_combiner.py tests/test_cr030_experiment_manifest_catalog.py tests/test_cr030_strategy_admission_package.py tests/test_cr030_no_real_operation_safety.py
uv run --python 3.11 python -m py_compile tests/test_cr030_no_real_operation_safety.py
```

若这些检查发现正向授权声明、ready 误导、凭据示例、外部运行指令、provider / lake / publish / QMT 操作说明或后续 Spike 被写成 P0，应修正文案或回退对应 Story，不得用人工解释绕过测试。
