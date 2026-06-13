---
cr_id: CR-036
title: 第5章异象复刻与异象研究数据集
status: closed-user-approved
created_at: 2026-06-10
created_by: codex
owner: meta-po
source: user
change_type: add
impact_level: high
workflow_mode_after_change: standard
activation_policy: "activated by user request on 2026-06-10 after CR-035 was closed; local offline implementation passed; closed by user request on 2026-06-10"
parent_cr: CR-034
source_decision_id: USER-20260610-BOOK-RESEARCH-PLAN
related_changes:
  - CR-030
  - CR-034
  - CR-035
---

# CR-036 第5章异象复刻与异象研究数据集

## 背景与上下文

第5章在第3章因子和第4章多因子模型基础上研究 A 股异象。书中第5章包括：

| 章节 | 主题 | 项目内定位 |
|---|---|---|
| 5.1 | 估值高低中的异象 | 异象变量，不等同于第三章 `value_bm` 因子 |
| 5.2 | 基本面锚定反转 | 复合变量 / 反转异象，需要额外基本面锚定字段 |
| 5.3 | 特质性波动率 | 异象变量，需要模型残差或特质波动率估计 |

CR-034 已关闭并提供第三章七因子面板。CR-035 将提供第4章模型解释输入。CR-036 不应把第5章异象混入第三章七因子基线，而应形成独立的 anomaly panel、排序检验、α 检验和准入结论。

## 目标

1. 精读第5章，冻结三类异象的变量定义、数据需求、排序口径和检验口径。
2. 建立第5章异象数据集，不污染第三章七因子 canonical factor set。
3. 复刻估值高低异象、基本面锚定反转、特质性波动率异象。
4. 使用第4章模型结果解释异象收益，输出 α 检验和模型解释能力。
5. 判断异象是否可作为后续 alpha feature、观察项或拒绝项。
6. 形成第6章稳健性复验和第7章组合实践的候选输入。

## Non-Goals

- 不把第5章异象改名为第三章因子。
- 不改写 CR-034 第三章七因子面板。
- 不做组合优化、Smart Beta 或实盘交易。
- 不触发 provider fetch、lake write、catalog publish、QMT、simulation 或 live。
- 不把异象显著性直接等同于可交易策略有效。

## 影响范围

| 维度 | 影响 | 处理 |
|---|---|---|
| 需求层 | 新增三类异象复刻和模型 α 检验需求 | 独立于第三章因子复刻 |
| 场景层 | 新增异象排序、长短组合、模型解释和样本外稳定性场景 | CR-037 继续做稳健性 |
| 计划层 | 依赖 CR-035 模型定义和因子收益 | 默认 CR-035 完成后启动 |
| 安全层 | 只读本地研究输入 | 禁止真实 provider / lake write / publish / 交易 |
| 交付层 | 新增 anomaly panel、anomaly return、alpha test 和报告 | 大型 parquet 不默认提交 |

## 输入合同

| 输入 | 来源 | 说明 |
|---|---|---|
| 第三章七因子面板 | CR-034 | 用于控制变量、模型解释和对照 |
| 第4章模型结果 | CR-035 | 用于 α 检验和模型解释 |
| 财务 PIT 字段 | local lake / CR-034 readiness | book equity、ROE、ROA、total assets 等 |
| 日收益 / 市场收益 | CR-034 后复权收益 | 特质波动率需要回归残差或模型残差 |
| 第5章变量定义 | 书籍 Markdown | 必须在报告中追溯到 5.1/5.2/5.3 |

## 输出规划

| 输出 | 路径 | 说明 |
|---|---|---|
| 异象面板 | `reports/chapter5_anomalies/<run_id>/anomaly_panel.parquet` | anomaly_id、raw/directional/winsorized/zscore |
| 异象收益 | `reports/chapter5_anomalies/<run_id>/anomaly_returns.csv` | 分组收益、多空收益 |
| α 检验 | `reports/chapter5_anomalies/<run_id>/alpha_tests.csv` | 相对第4章模型的 alpha / t 值 |
| 异象 manifest | `reports/chapter5_anomalies/<run_id>/anomaly_manifest.json` | 输入、口径、窗口、限制 |
| 人读报告 | `process/research/chapter5_anomalies/<run_id>/CHAPTER5-RUN-REPORT.md` | 第5章复刻报告 |
| 准入摘要 | `process/research/chapter5_anomalies/<run_id>/ANOMALY-ADMISSION-SUMMARY.json` | alpha feature / watch / reject |

## 数据缺口处理规则

- 缺少第5章变量必需字段时，先输出 gap register，不允许静默用近似字段替代。
- 需要新增真实 provider fetch 或 lake write 时，必须另起数据补齐 CR 或在本 CR 内重新发起运行授权，不得默认继承 CR-034 授权。
- 特质性波动率必须明确使用的定价模型、收益窗口和最小有效样本数。

## 验收标准

- [x] 三类异象均有变量定义、数据字段、排序方向和 5.1 / 5.2 / 5.3 章节主题追溯；仓库未找到第5章书籍 Markdown 原文，已登记 strict gap，不声明逐字严格复刻。
- [x] 每类异象都有单变量排序、多空收益和等价 t 值。
- [x] 每类异象都有相对第4章模型的 α 检验。
- [x] 报告明确区分“异象变量”和“可纳入策略的 alpha feature”。
- [x] operation counts 中 provider fetch、lake write、publish、QMT、simulation、live 均为 0。
- [x] 峰值内存低于 16GB。

## 激活条件

本 CR 已于 2026-06-10 在用户关闭 CR-035 后启动。CR-035 模型 baseline 已作为本 CR α 检验输入；CR-020 仍处于 MiniQMT 权限等待状态，本 CR 未触碰 QMT / simulation / live / provider / lake / publish 路径。

## 冲突预检（2026-06-10）

| 维度 | 结论 |
|---|---|
| 与 CR-020 | 无执行面冲突。CR-020 影响 Windows/QMT gateway、只读 `query_positions`、凭据与 runtime；CR-036 只读消费本地 CR-034 / CR-035 研究产物并写 `reports/chapter5_anomalies/` 与 `process/research/chapter5_anomalies/`。 |
| 与 CR-035 | 依赖满足。CR-035 已关闭并产出 `reports/chapter4_factor_models/run-cr035-chapter4-factor-models-20260610/factor_model_returns.parquet` 与模型准入摘要。 |
| 禁止操作 | 未触发 provider fetch、lake write、catalog publish、QMT、simulation、live、账户 / 订单操作、凭据读取或依赖变更。 |
| 书籍原文 | 仓库未找到第5章书籍 Markdown 原文；本 CR 按已冻结的 5.1 / 5.2 / 5.3 主题实现项目内可执行定义，严格复刻声明保持 blocked。 |

## 实现结果（2026-06-10）

| 类别 | 路径 / 结果 |
|---|---|
| 引擎 | `engine/chapter5_anomalies.py` |
| Runner | `scripts/run_chapter5_anomalies.py` |
| 测试 | `tests/test_chapter5_anomalies.py` |
| run_id | `run-cr036-chapter5-anomalies-20260610` |
| 运行状态 | `PASS` |
| 人读报告 | `process/research/chapter5_anomalies/run-cr036-chapter5-anomalies-20260610/CHAPTER5-RUN-REPORT.md` |
| JSON 报告 | `process/research/chapter5_anomalies/run-cr036-chapter5-anomalies-20260610/CHAPTER5-RUN-REPORT.json` |
| 准入摘要 | `process/research/chapter5_anomalies/run-cr036-chapter5-anomalies-20260610/ANOMALY-ADMISSION-SUMMARY.json` |
| 异象面板 | `reports/chapter5_anomalies/run-cr036-chapter5-anomalies-20260610/anomaly_panel.parquet` |
| 异象收益 | `reports/chapter5_anomalies/run-cr036-chapter5-anomalies-20260610/anomaly_returns.csv` |
| α 检验 | `reports/chapter5_anomalies/run-cr036-chapter5-anomalies-20260610/alpha_tests.csv` |
| 缺口登记 | `reports/chapter5_anomalies/run-cr036-chapter5-anomalies-20260610/gap_register.csv` |

## 样本与准入摘要

| sample_id | 异象 | admission | mean_long_short | t_stat | max_abs_alpha_t |
|---|---|---|---:|---:|---:|
| `in_sample_2000_2019` | `fundamental_anchor_reversal` | `watch_needs_robustness_review` | 0.002948 | 1.098460 | 2.415404 |
| `in_sample_2000_2019` | `idiosyncratic_volatility_proxy` | `reject_or_reweight` | -0.014755 | -4.703716 | 5.936464 |
| `in_sample_2000_2019` | `valuation_extreme_spread` | `reject_or_reweight` | -0.001967 | -1.531937 | 1.723286 |
| `observation_2020_2026_ytd` | `fundamental_anchor_reversal` | `watch` | 0.002251 | 0.457923 | 2.835862 |
| `observation_2020_2026_ytd` | `idiosyncratic_volatility_proxy` | `reject_or_reweight` | -0.026684 | -3.525218 | 4.241411 |
| `observation_2020_2026_ytd` | `valuation_extreme_spread` | `reject_or_reweight` | -0.006537 | -2.813429 | 3.645934 |

## 验证结果（2026-06-10）

| 检查 | 命令 | 结果 |
|---|---|---|
| 单元测试 | `PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' uv run --python 3.11 pytest -q tests/test_chapter5_anomalies.py` | PASS，4 passed |
| 编译检查 | `PYTHONPYCACHEPREFIX=/tmp/cr036-chapter5-pycompile uv run --python 3.11 python -m py_compile engine/chapter5_anomalies.py scripts/run_chapter5_anomalies.py tests/test_chapter5_anomalies.py` | PASS |
| 真实本地运行 | `OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 uv run --python 3.11 python scripts/run_chapter5_anomalies.py --run-id run-cr036-chapter5-anomalies-20260610 --max-memory-gb 16` | PASS |

## 剩余风险与交接

| 风险 | 状态 | 处理 |
|---|---|---|
| 第5章书籍 Markdown 原文缺失 | `open-with-proxy-implemented` | 已在 gap register 保留；报告不得声明逐字严格复刻。 |
| 估值、基本面锚定、特质波动率使用代理定义 | `open-with-proxy-implemented` | CR-037 必须先做稳健性和 strict gap 复验；CR-038 / CR-039 只能在复验后消费。 |
| 异象显著性误读为可交易策略 | `blocked` | `ANOMALY-ADMISSION-SUMMARY.json` 中明确 `not_authorization=true`，并阻断 production / QMT / simulation / live-ready 声明。 |

## 关闭结果（2026-06-10）

| 项目 | 结论 |
|---|---|
| 关闭状态 | `closed-user-approved` |
| 用户指令 | 用户要求“关闭 cr36，@meta-po 开始分析和实现 cr37”。 |
| 交付物 | 第5章异象面板、异象收益、α 检验、异象准入摘要、gap register 和 CP6/CP7 已完成。 |
| 后续消费 | CR-037 已消费 CR-036 anomaly panel，执行第6章稳健性复验；CR-038 / CR-039 只能在 CR-037 结论基础上消费 baseline / candidate。 |
| 不授权范围 | 关闭 CR-036 不授权 provider fetch、lake write、catalog publish、QMT、simulation、live、账户 / 订单、凭据读取或生产有效声明。 |
| 剩余风险 | 第5章书籍 Markdown 原文缺失和代理定义缺口继续作为 CR-037 / CR-038 / CR-039 的风险输入，不被关闭动作消除。 |
