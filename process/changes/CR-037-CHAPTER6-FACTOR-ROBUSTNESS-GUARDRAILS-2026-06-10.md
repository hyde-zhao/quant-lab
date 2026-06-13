---
cr_id: CR-037
title: 第6章因子稳健性、失效风险与研究规范
status: closed-user-approved
created_at: 2026-06-10
created_by: codex
owner: meta-po
source: user
change_type: add
impact_level: high
workflow_mode_after_change: standard
activation_policy: "activated by user request on 2026-06-10 after CR-036 was closed; local offline implementation passed; CR-038/CR-039 handoff gates completed and closed by user request on 2026-06-10"
parent_cr: CR-034
source_decision_id: USER-20260610-BOOK-RESEARCH-PLAN
related_changes:
  - CR-030
  - CR-034
  - CR-035
  - CR-036
---

# CR-037 第6章因子稳健性、失效风险与研究规范

## 背景与上下文

第6章讨论 p-hacking、因子动物园、因子大战、行为金融解释、投资者情绪、风险补偿 / 错误定价 / 数据窥探、样本外失效风险、机器学习与因子投资。它不是单个因子复刻 CR，而是给第3章因子、第5章异象和第7章策略实践建立研究质量护栏。

CR-030 已建立多因子研究合同，CR-034 已关闭第三章七因子数据和复刻，CR-035/CR-036 将分别输出模型和异象候选。CR-037 的职责是防止后续策略研究只依赖样本内显著性，补齐样本外、滚动、分市场状态、参数敏感性和数据窥探风险证据。

## 目标

1. 建立项目内因子研究 guardrails，覆盖 p-hacking、多重检验、样本外和失效风险。
2. 对第3章七因子和第5章异象候选执行 rolling IC、rolling long-short、decay、年度分解和市场状态分层。
3. 建立因子失效监控指标：RankIC 衰减、收益衰减、换手漂移、相关性漂移、容量 / 成本敏感性。
4. 为机器学习研究建立 leakage guard、purge / embargo、样本切分和可解释性边界。
5. 输出因子 / 异象准入分级：baseline、candidate、watch、reject、needs-more-data。

## Non-Goals

- 不训练复杂 ML 模型作为默认交付。
- 不把样本内显著性自动转为策略准入。
- 不做 QMT、simulation、live 或真实订单。
- 不触发 provider fetch、lake write、catalog publish。
- 不覆盖 CR-035/036 的原始报告，只生成稳健性补充证据。

## 影响范围

| 维度 | 影响 | 处理 |
|---|---|---|
| 需求层 | 新增因子稳健性、样本外失效和研究规范 | 写入 docs/quality 和 process/research |
| 场景层 | 增加滚动、年度、市场状态、参数敏感性和 ML leakage 场景 | 作为后续策略准入前置 |
| 计划层 | 依赖 CR-035/036 产物 | 可分批先覆盖第三章七因子 |
| 安全层 | 只读研究 artifact | 禁止 provider/lake/publish/交易 |
| 交付层 | 新增 guardrail 文档和 robustness reports | 小型 CSV/报告可提交，大型中间数据不默认提交 |

## 输出规划

| 输出 | 路径 | 说明 |
|---|---|---|
| 因子研究护栏 | `docs/quality/FACTOR-RESEARCH-GUARDRAILS.md` | 长期规范 |
| rolling IC | `reports/chapter6_factor_robustness/<run_id>/rolling_ic.csv` | 滚动稳定性 |
| 年度分解 | `reports/chapter6_factor_robustness/<run_id>/annual_factor_metrics.csv` | 年度收益 / IC / turnover |
| 市场状态结果 | `reports/chapter6_factor_robustness/<run_id>/market_state_results.csv` | 牛熊 / 波动 / 流动性 / 情绪 proxy 分层 |
| 衰减报告 | `reports/chapter6_factor_robustness/<run_id>/decay_report.csv` | 持有期 / 标签窗口敏感性 |
| ML leakage audit | `reports/chapter6_factor_robustness/<run_id>/ml_leakage_audit.md` | purge / embargo / label overlap 审计 |
| 人读报告 | `process/research/chapter6_factor_robustness/<run_id>/CHAPTER6-RUN-REPORT.md` | 第6章研究报告 |
| 准入摘要 | `process/research/chapter6_factor_robustness/<run_id>/ROBUSTNESS-ADMISSION-SUMMARY.json` | 给 CR-038/039 消费 |

## 分级规则草案

| 分级 | 条件 |
|---|---|
| baseline | 样本内、验证期、2020-2026 YTD 均方向稳定，rolling 指标不过度衰减，成本敏感性可接受 |
| candidate | 样本内有效，样本外部分有效，需要组合层约束 |
| watch | 显著性或方向不稳定，但有经济解释或特定市场状态有效 |
| reject | 多窗口方向反转或完全由数据窥探 / 不可交易假设驱动 |
| needs-more-data | 数据字段、样本长度或质量不足 |

## 验收标准

- [x] 至少覆盖第三章七因子的 rolling / annual / sample-out 稳健性。
- [x] CR-036 已完成，已覆盖第5章三类异象候选。
- [x] 明确所有因子 / 异象的准入分级和理由。
- [x] 明确哪些指标只用于研究，不得直接用于 production。
- [x] ML 相关内容通过 leakage audit，未发现标签前视或 overlap。
- [x] operation counts 中 provider fetch、lake write、publish、QMT、simulation、live 均为 0。
- [x] 峰值内存低于 16GB。

## 激活条件

本 CR 已于 2026-06-10 在用户关闭 CR-036 后启动。CR-034 第三章因子面板、CR-035 模型 baseline 和 CR-036 anomaly panel 均已可读；本 CR 未触碰 QMT / simulation / live / provider / lake / publish 路径。

## 冲突预检（2026-06-10）

| 维度 | 结论 |
|---|---|
| 与 CR-020 | 无执行面冲突。CR-020 影响 Windows/QMT gateway、只读 `query_positions`、凭据与 runtime；CR-037 只读消费本地 CR-034 / CR-036 研究产物并写 `reports/chapter6_factor_robustness/`、`process/research/chapter6_factor_robustness/` 和 `docs/quality/FACTOR-RESEARCH-GUARDRAILS.md`。 |
| 与 CR-036 | 依赖满足。CR-036 已关闭并产出 `reports/chapter5_anomalies/run-cr036-chapter5-anomalies-20260610/anomaly_panel.parquet`。 |
| 禁止操作 | 未触发 provider fetch、lake write、catalog publish、QMT、simulation、live、账户 / 订单操作、凭据读取或依赖变更。 |
| ML 边界 | 只执行 leakage audit 和 purge / embargo 规范输出，不训练、不调参、不准入 ML 模型。 |

## 实现结果（2026-06-10）

| 类别 | 路径 / 结果 |
|---|---|
| 引擎 | `engine/chapter6_factor_robustness.py` |
| Runner | `scripts/run_chapter6_factor_robustness.py` |
| 测试 | `tests/test_chapter6_factor_robustness.py` |
| run_id | `run-cr037-chapter6-robustness-20260610` |
| 运行状态 | `PASS` |
| 人读报告 | `process/research/chapter6_factor_robustness/run-cr037-chapter6-robustness-20260610/CHAPTER6-RUN-REPORT.md` |
| JSON 报告 | `process/research/chapter6_factor_robustness/run-cr037-chapter6-robustness-20260610/CHAPTER6-RUN-REPORT.json` |
| 准入摘要 | `process/research/chapter6_factor_robustness/run-cr037-chapter6-robustness-20260610/ROBUSTNESS-ADMISSION-SUMMARY.json` |
| 研究护栏 | `docs/quality/FACTOR-RESEARCH-GUARDRAILS.md` |
| rolling IC | `reports/chapter6_factor_robustness/run-cr037-chapter6-robustness-20260610/rolling_ic.csv` |
| 年度分解 | `reports/chapter6_factor_robustness/run-cr037-chapter6-robustness-20260610/annual_factor_metrics.csv` |
| 市场状态分层 | `reports/chapter6_factor_robustness/run-cr037-chapter6-robustness-20260610/market_state_results.csv` |
| 衰减报告 | `reports/chapter6_factor_robustness/run-cr037-chapter6-robustness-20260610/decay_report.csv` |
| ML leakage audit | `reports/chapter6_factor_robustness/run-cr037-chapter6-robustness-20260610/ml_leakage_audit.md` |

## 样本摘要

| sample_id | status | asset_count | return_rows | rolling_ic_rows | annual_rows | market_state_rows | decay_rows | leakage_status |
|---|---|---:|---:|---:|---:|---:|---:|---|
| `in_sample_2000_2019` | `PASS` | 10 | 2219 | 2109 | 193 | 30 | 30 | `PASS` |
| `observation_2020_2026_ytd` | `PASS` | 10 | 681 | 571 | 66 | 30 | 30 | `PASS` |

## 准入摘要

| sample_id | baseline / candidate | watch | reject |
|---|---|---|---|
| `in_sample_2000_2019` | baseline: `abnormal_turnover_21_252`, `profitability_roe_ttm`, `size_total_market_cap`, `value_bm` | `fundamental_anchor_reversal`, `momentum_12_1` | `idiosyncratic_volatility_proxy`, `valuation_extreme_spread`, `investment_asset_growth`, `market_beta_252` |
| `observation_2020_2026_ytd` | baseline: `abnormal_turnover_21_252`, `size_total_market_cap`; candidate: `value_bm` | `fundamental_anchor_reversal`, `investment_asset_growth`, `market_beta_252` | `idiosyncratic_volatility_proxy`, `valuation_extreme_spread`, `momentum_12_1`, `profitability_roe_ttm` |

## 验证结果（2026-06-10）

| 检查 | 命令 | 结果 |
|---|---|---|
| 单元测试 | `PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' uv run --python 3.11 pytest -q tests/test_chapter6_factor_robustness.py` | PASS，4 passed |
| 编译检查 | `PYTHONPYCACHEPREFIX=/tmp/cr037-chapter6-pycompile uv run --python 3.11 python -m py_compile engine/chapter6_factor_robustness.py scripts/run_chapter6_factor_robustness.py tests/test_chapter6_factor_robustness.py` | PASS |
| 真实本地运行 | `OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 uv run --python 3.11 python scripts/run_chapter6_factor_robustness.py --run-id run-cr037-chapter6-robustness-20260610 --max-memory-gb 16` | PASS |

## 剩余风险与交接

| 风险 | 状态 | 处理 |
|---|---|---|
| 第5章异象代理定义缺口 | `open-with-risk` | CR-037 已复验并将两个异象判为 reject、一个判为 watch；CR-038 / CR-039 不得直接消费 reject 项。 |
| 成本 / 容量未完全建模 | `open` | 当前 CR 只做收益、IC、年度、市场状态和衰减稳健性；组合实践前仍需成本 / 容量敏感性。 |
| ML 只做 leakage audit | `intentional-boundary` | 后续 ML 研究必须另起 CR 或明确 purge / embargo、解释性和调参边界。 |
| 误读为交易授权 | `blocked` | `ROBUSTNESS-ADMISSION-SUMMARY.json` 中明确 `not_authorization=true`，并阻断 production / QMT / simulation / live / ML model ready 声明。 |

## 关闭结果（2026-06-10）

| 项目 | 结论 |
|---|---|
| 关闭状态 | `closed-user-approved` |
| 用户指令 | 用户要求“将 CR038 和 CR039 补充完整后，关闭 CR037”。 |
| 交接补充 | 已在 CR-038 增加 CR-037 分级消费、成本 / 容量敏感性、watch/reject、CR-036 异象缺口、ML 边界和不授权门禁；已在 CR-039 增加 CR-037 / CR-038 策略准入硬门禁。 |
| 后续消费 | CR-038 默认只消费 CR-037 `baseline` / `candidate`；`watch` 需要显式风险接受和组合约束；`reject` / `needs-more-data` / `blocked_missing_evidence` 默认 fail-closed。CR-039 缺少 CR-038 成本 / 容量证据时不得输出 `simulation_candidate`。 |
| 不授权范围 | 关闭 CR-037 不授权 provider fetch、lake write、catalog publish、QMT、simulation、live、账户 / 订单、凭据读取、依赖变更或 ML 模型训练。 |
| 剩余风险 | 成本 / 容量、CR-036 异象代理缺口、ML 边界和交易授权误读均已作为 CR-038 / CR-039 门禁承接，不再阻塞 CR-037 关闭。 |
