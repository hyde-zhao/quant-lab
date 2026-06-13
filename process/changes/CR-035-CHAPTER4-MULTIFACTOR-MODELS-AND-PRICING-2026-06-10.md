---
cr_id: CR-035
title: 第4章多因子模型复刻与 A 股定价检验
status: closed-user-approved
created_at: 2026-06-10
created_by: codex
owner: meta-po
source: user
change_type: add
impact_level: high
workflow_mode_after_change: standard
activation_policy: "activated by user request on 2026-06-10; conflict precheck passed because CR-035 is local offline research and does not touch CR-020 QMT gateway/runtime surfaces; closed by user request on 2026-06-10"
parent_cr: CR-034
source_decision_id: USER-20260610-BOOK-RESEARCH-PLAN
related_changes:
  - CR-030
  - CR-034
---

# CR-035 第4章多因子模型复刻与 A 股定价检验

## 背景与上下文

《因子投资：方法与实践》第4章在第3章七个主流因子基础上，研究主流多因子模型和 A 股中哪些因子被定价。第3章已经由 CR-034 关闭，形成可用于后续研究的七因子面板：

| 输入 | 状态 | 路径 |
|---|---|---|
| 2000-2019 第三章七因子面板 | PASS；2,550,289 行；239 期调仓；峰值 RSS 3.49GB | `reports/chapter3_factor_panel/run-chapter3-empirical-2000-2019-financial-fallback-20260610/factor_panel.parquet` |
| 2020-2026 YTD 第三章七因子面板 | PASS；1,957,024 行；76 期调仓；峰值 RSS 5.67GB | `reports/chapter3_factor_panel/run-chapter3-empirical-2020-2026-ytd-financial-fallback-20260610/factor_panel.parquet` |
| 第三章因子口径 | 七因子已复刻：市场、规模、价值、动量、盈利、投资、异常换手率 | `process/research/chapter3_factor_replication/README.md` |
| 多因子研究合同 | FactorSpec、FactorRunSpec、FactorPanelContract、LabelWindowSpec、FactorEvaluationReport、StrategyAdmissionPackage 已由 CR-030 建立 | `docs/CR030-MULTIFACTOR-RESEARCH-LOOP.md` |

本 CR 是第三章研究的直接下游，目标是把“单因子复刻和基础评价”推进到“多因子模型定价检验与模型比较”。它不进入组合优化和交易准入，后者由 CR-038 / CR-039 或后续 QMT CR 单独处理。

## 目标

1. 复刻第4章“主流多因子模型综述”的项目内模型定义和因子组合输入。
2. 基于第三章七因子面板，执行第4章 `4.2 A股中被定价的因子` 的 Fama-MacBeth 回归检验。
3. 输出每个因子的横截面风险溢价、t 值、样本数、窗口、稳定性和方向解释。
4. 复刻第4章 `4.3 多因子模型比较` 的项目内可执行版本，包括模型收益、相关性、α 检验、GRS 或等价比较。
5. 落地第4章 `4.4 多因子模型的简约性`，给出进入后续策略研究的基线模型建议。
6. 形成第7章组合实践前的“模型准入摘要”：哪些因子进入 baseline、哪些只观察、哪些需要在第6章稳健性中重点复验。

## Non-Goals

- 不新增第5章异象变量。
- 不做第7章组合优化、Smart Beta、因子择时或风险归因。
- 不接入 QMT、simulation、live、账户、订单或 broker lake。
- 不触发 provider fetch、lake write、catalog current pointer publish。
- 不把任何模型声明为 production-valid、QMT-ready、simulation-ready 或 live-ready。
- 不把外部论文模型未验证地作为项目 current truth。

## 影响范围

| 维度 | 影响 | 处理 |
|---|---|---|
| 需求层 | 新增第4章模型复刻、Fama-MacBeth、模型比较和简约性结论 | 建立 CR-035 研究需求，不修改 CR-034 历史基线 |
| 场景层 | 增加多因子模型检验、样本内 / 样本外切分、模型冗余分析 | 新增 chapter4 研究场景和报告 |
| 计划层 | 依赖 CR-034 因子面板；为 CR-036/037/038 提供模型解释输入 | CR-035 完成前不启动依赖第4章模型结果的异象解释和组合优化 |
| 安全层 | 只读本地 parquet / manifest / 报告 | 禁止 provider、lake write、publish、QMT、simulation、live |
| 交付层 | 新增 reports/chapter4_factor_models 和 process/research/chapter4_factor_models | 小型报告可提交，大型 parquet 默认不提交 |

## CR 冲突预检（2026-06-10）

| 检查项 | 结论 |
|---|---|
| 当前 active CR | `CR-020` 仍为 `active-manual-validation-pending`，等待 MiniQMT 权限和 Windows/QMT 只读实机验证。 |
| 文件所有权冲突 | 无重叠。CR-035 只新增 `engine/chapter4_factor_models.py`、`scripts/run_chapter4_factor_models.py`、`tests/test_chapter4_factor_models.py`、`reports/chapter4_factor_models/` 和 `process/research/chapter4_factor_models/`。 |
| 外部接口 / 运行权限 | 无重叠。CR-035 只读取本地第三章 parquet 与 label parts，不读取凭据、不访问 provider、不触发 QMT / simulation / live。 |
| 数据写入 / publish | 无。CR-035 不写 data lake、不发布 catalog current pointer，只写本地 research artifact。 |
| 结论 | 允许与 CR-020 并行推进。CR-020 顶层 `active_change` 保持不变；CR-035 记录为离线研究 active item，完成后等待人工审查关闭。 |

## 输入合同

| 输入 | 必需字段 | 失败行为 |
|---|---|---|
| 第三章 factor panel | `trade_date`、`symbol`、`factor_id`、`zscore_value`、`available_at`、`run_id`、`data_lineage` | 缺 P0 字段 fail-closed |
| 标签 / forward returns | `trade_date`、`symbol`、`forward_return`、`label_available_at` | 标签窗口与因子 available_at 重叠或前视时 fail-closed |
| 因子定义 | `engine.factor_library` canonical factor definitions | 因子 ID 未注册或方向不明时 fail-closed |
| 第三章报告 | 两段 empirical report | report status 非 PASS 或 limitations 非空时阻断模型准入 |

## 输出规划

| 输出 | 路径 | 说明 |
|---|---|---|
| 因子收益 / Fama-MacBeth 结果 | `reports/chapter4_factor_models/<run_id>/fama_macbeth_results.csv` | 因子溢价、t 值、样本数、窗口 |
| 模型收益 | `reports/chapter4_factor_models/<run_id>/factor_model_returns.parquet` | 各模型月度收益和因子组合 |
| 模型比较 | `reports/chapter4_factor_models/<run_id>/model_comparison.csv` | α、GRS 或等价统计、相关性和冗余性 |
| 因子相关性 | `reports/chapter4_factor_models/<run_id>/factor_correlation.csv` | 七因子相关结构 |
| manifest | `reports/chapter4_factor_models/<run_id>/factor_model_manifest.json` | 输入 run、参数、窗口、资源和限制 |
| 运行报告 | `process/research/chapter4_factor_models/<run_id>/CHAPTER4-RUN-REPORT.md` | 人读报告 |
| 机器报告 | `process/research/chapter4_factor_models/<run_id>/CHAPTER4-RUN-REPORT.json` | 机器可读 |
| 模型准入摘要 | `process/research/chapter4_factor_models/<run_id>/MODEL-ADMISSION-SUMMARY.json` | 给 CR-038/039 消费 |

## 资源与运行边界

- 默认串行运行，不并发跑重型任务。
- 默认 `OMP_NUM_THREADS=1`、`OPENBLAS_NUM_THREADS=1`、`MKL_NUM_THREADS=1`、`NUMEXPR_NUM_THREADS=1`。
- 默认使用 chunked / 按窗口处理，单次运行 `--max-memory-gb 16`。
- 大型 parquet 只作为本地研究 artifact，不默认提交 Git。

## 验收标准

- [x] Fama-MacBeth 回归覆盖七个第三章因子，并输出 t 值和样本数。
- [x] 模型比较至少覆盖书中第4章涉及的主流模型和 A 股示例模型的项目内可执行版本。
- [x] 报告区分样本内、验证期和 2020-2026 YTD 观察期。
- [x] 输出模型准入结论：baseline / watch / reject / needs-robustness-review。
- [x] operation counts 中 provider fetch、lake write、publish、QMT、simulation、live 均为 0。
- [x] 峰值内存低于 16GB。
- [x] 报告不声明 production-valid、QMT-ready、simulation-ready 或 live-ready。

## 实现与验证结果（2026-06-10）

### 实现对象

| 类型 | 路径 | 说明 |
|---|---|---|
| 计算模块 | `engine/chapter4_factor_models.py` | 第四章模型定义、输入校验、Fama-MacBeth、模型收益、模型比较、相关性和准入摘要。 |
| Runner | `scripts/run_chapter4_factor_models.py` | 只读消费第三章 factor panel 与 label parts，输出 CR-035 research artifacts。 |
| 测试 | `tests/test_chapter4_factor_models.py` | 覆盖输入字段、前视阻断、模型输出、runner artifact 和第三章报告限制阻断。 |
| 报告产物 | `reports/chapter4_factor_models/run-cr035-chapter4-factor-models-20260610/` | Fama-MacBeth、模型收益、模型比较、相关性、manifest。 |
| 过程产物 | `process/research/chapter4_factor_models/run-cr035-chapter4-factor-models-20260610/` | 人读报告、机器报告和模型准入摘要。 |

### 实证摘要

| 样本 | 状态 | panel 行数 | label 行数 | 匹配行数 | 调仓期数 | FMB 行数 | 模型收益行数 |
|---|---|---:|---:|---:|---:|---:|---:|
| `in_sample_2000_2019` | PASS | 2,550,289 | 447,186 | 407,599 | 239 | 37 | 1,378 |
| `observation_2020_2026_ytd` | PASS | 1,957,024 | 371,877 | 317,132 | 76 | 37 | 419 |

### 关键产物

| 产物 | 路径 |
|---|---|
| 运行报告 | `process/research/chapter4_factor_models/run-cr035-chapter4-factor-models-20260610/CHAPTER4-RUN-REPORT.md` |
| 机器报告 | `process/research/chapter4_factor_models/run-cr035-chapter4-factor-models-20260610/CHAPTER4-RUN-REPORT.json` |
| 模型准入摘要 | `process/research/chapter4_factor_models/run-cr035-chapter4-factor-models-20260610/MODEL-ADMISSION-SUMMARY.json` |
| Fama-MacBeth | `reports/chapter4_factor_models/run-cr035-chapter4-factor-models-20260610/fama_macbeth_results.csv` |
| 模型比较 | `reports/chapter4_factor_models/run-cr035-chapter4-factor-models-20260610/model_comparison.csv` |
| manifest | `reports/chapter4_factor_models/run-cr035-chapter4-factor-models-20260610/factor_model_manifest.json` |

### 验证命令

```bash
PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' uv run --python 3.11 pytest -q tests/test_chapter4_factor_models.py
PYTHONPYCACHEPREFIX=/tmp/cr035-chapter4-pycompile uv run --python 3.11 python -m py_compile engine/chapter4_factor_models.py scripts/run_chapter4_factor_models.py tests/test_chapter4_factor_models.py
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 uv run --python 3.11 python scripts/run_chapter4_factor_models.py --run-id run-cr035-chapter4-factor-models-20260610 --max-memory-gb 16
```

结果：

| 验证 | 结果 |
|---|---|
| focused pytest | 4 passed |
| py_compile | passed |
| CR-035 真实本地离线 runner | PASS |
| 禁止操作计数 | provider/lake/publish/QMT/simulation/live/account/credential 均为 0 |

### 模型准入结论

2000-2019 样本内，`ff3_equity_core`、`carhart4_momentum`、`ashare_pricing_candidate` 和 `seven_factor_full` 为 baseline candidate；`ff5_like_profit_investment` 与 `q_factor_like` 需要 CR-037 稳健性复验；`capm_market` 只能观察或重加权。

2020-2026 YTD 观察期，多数模型表现为 baseline candidate，但仍不得跳过 CR-037 稳健性、样本外和数据窥探复验。所有结论只作为研究输入，不构成 production-valid、QMT-ready、simulation-ready 或 live-ready。

## 关闭结果（2026-06-10）

用户已明确要求“关闭 CR35”。关闭范围如下：

| 项目 | 结论 |
|---|---|
| 交付状态 | `closed-user-approved` |
| 已交付 | 第4章 Fama-MacBeth、模型收益、模型比较、相关性、manifest、运行报告和模型准入摘要 |
| 不授权项 | provider fetch、lake write、catalog publish、QMT、simulation、live、账户、订单、凭据读取均仍不授权 |
| 后续输入 | `process/research/chapter4_factor_models/run-cr035-chapter4-factor-models-20260610/MODEL-ADMISSION-SUMMARY.json` 作为 CR-036/CR-037/CR-038/CR-039 的研究输入 |
| 剩余风险 | 模型候选仍需 CR-037 稳健性、样本外和数据窥探复验；CR-035 结果不得直接解释为 production-valid、QMT-ready、simulation-ready 或 live-ready |

## 激活条件

本 CR 已于 2026-06-10 由用户请求启动并完成本地离线实现。原激活条件处理如下：

1. CR 冲突预检：已通过，CR-035 与 CR-020 无文件、运行权限和外部接口冲突。
2. 用户确认启动 CR-035：已由 `@meta-po 请帮我完成出cr-35的分析和实现` 触发。
3. 新增 runner 与报告：已按离线只读研究边界完成；当前状态为 `implemented-local-pass-pending-review`，等待人工审查后关闭。
