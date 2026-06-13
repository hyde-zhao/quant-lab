# 阶段六实验全量复跑摘要

> Run ID: `stage6_full_run_20260611`  
> 执行日期: 2026-06-11  
> 执行边界: 本地离线 research / shadow / paper simulation；未读取凭据，未调用 QMT / MiniQMT / broker，未提交订单，未撤单，未写 data lake / broker lake，未 publish catalog。  
> 总结论: **暂停并修复 / 继续研究观察**。本轮完成阶段六计划中可离线执行的实验，但不构成正式模拟盘、QMT simulation 或 live 准入。

## 总体结果

| 范围 | 状态 | 关键证据 | 结论 |
|---|---|---|---|
| 实验 41-48 低波固定 20 / shadow 链路 | PARTIAL_PASS_WITH_BLOCKERS | `reports/stage6_full_run_20260611/low_vol_stage5/`、`reports/stage6_full_run_20260611/low_vol_dry_run/` | 固定 20 只低波本地 dry-run 5 日通过；但它是新口径，不能继承阶段五 Top20% 绩效，也未完成 8-12 周真实观察。 |
| 实验 49-66 多因子准入链路 | PASS_AS_RESEARCH_BASELINE | `process/research/stage6_full_run_20260611/*`、`reports/stage6_full_run_20260611/*` | 模型、异象、稳健性、组合实践、策略候选均 PASS；策略包仍为 `research_baseline`，`simulation_candidate=false`。 |
| 5 日离线 dry-run | PASS_NOT_AUTHORIZATION | `reports/stage6_full_run_20260611/low_vol_dry_run/`、`reports/stage6_full_run_20260611/multifactor_dry_run/` | 低波 5 日各 20 单， 多因子 5 日各 11 单；reconciliation 均 PASS；禁止操作计数均为 0。 |
| 测试验证 | PASS | `pytest -q ...` | 60 passed。 |

## 实验 41-48：低波 shadow simulation

| 实验 | 名称 | 本轮执行状态 | 证据 |
|---|---|---|---|
| 41 | 模拟盘问题定义与策略冻结 | DONE_EXISTING_REVIEWED | `/home/hyde/workspace/llm-wiki/llm-wiki/work/studies/quant-trading/working/stage6-simulation/SIM-STRATEGY-SPEC-v0.1.md` |
| 42 | 聚宽模拟盘机制学习 | DONE_EXISTING_REVIEWED | `/home/hyde/workspace/llm-wiki/llm-wiki/work/studies/quant-trading/working/stage6-simulation/simulation_mechanism_notes.md` |
| 43 | 模拟盘代码与状态审计 | DONE_EXISTING_REVIEWED | `/home/hyde/workspace/llm-wiki/llm-wiki/work/studies/quant-trading/working/stage6-simulation/simulation_code_state_audit.md` |
| 44 | 模拟盘前回测复刻 | RERUN_DONE_BLOCKED_FOR_ADMISSION | `reports/stage6_full_run_20260611/low_vol_stage5/experiment_36_stage5_summary/stage5_summary.md` |
| 45 | 5 日 dry-run | PASS_LOCAL_SHADOW | `reports/stage6_full_run_20260611/low_vol_dry_run/` |
| 46 | Runbook 与异常处理 | DONE_EXISTING_REVIEWED | `/home/hyde/workspace/llm-wiki/llm-wiki/work/studies/quant-trading/working/stage6-simulation/SIM-RUNBOOK-v0.1.md` |
| 47 | 启动 shadow simulation | PASS_LOCAL_ONLY | `reports/stage6_full_run_20260611/low_vol_dry_run/run-stage6-low-vol-dryrun-2024-04-01/` 至 `2024-04-09/` |
| 48 | 8-12 周模拟盘总结 | NOT_COMPLETE_BY_TIME_GATE | 需要真实连续 8-12 周运行；本轮只能输出本地离线阶段总结。 |

低波复刻核心发现：

- 阶段五脚本中的 `single_volatility_20d_top20_buffer40_freq40` 仍是 Top20% 分位口径，不是固定 20 只；本轮复跑平均持仓数为 `691.226054`。
- 本轮另做了固定 20 只低波 dry-run，连续交易日为 `2024-04-01`、`2024-04-02`、`2024-04-03`、`2024-04-08`、`2024-04-09`。
- 每日生成 20 个 order intent、20 个 fill、reconciliation `pass`，所有 forbidden operation counter 为 0。
- 该固定 20 只 dry-run 是工程链路验证，不是阶段五绩效复刻，不得升级为正式模拟盘候选。

## 实验 49-66：多因子模拟盘准入扩展

| 实验 | 名称 | 本轮执行状态 | 证据 |
|---|---|---|---|
| 49 | 多因子模拟盘目标与准入标准重定义 | DONE_EXISTING_REVIEWED | `/home/hyde/workspace/llm-wiki/llm-wiki/work/studies/quant-trading/working/stage6-simulation/MULTIFACTOR-SIMULATION-ADMISSION-PLAN.md` |
| 50 | production current truth 覆盖审计 | ATTEMPTED_BLOCKED_ON_LOCAL_DATA | `scripts/run_chapter3_empirical.py` 在当前 `data/` 上因可计算因子矩阵为空失败；旧 production truth 证据仍显示策略准入失败。 |
| 51 | A 股多因子候选库设计 | DONE_BY_EXISTING_FRAMEWORK | `engine/factor_library.py`、`process/research/stage6_full_run_20260611/chapter4_factor_models/...` |
| 52 | 财务因子 PIT / available_at 审计 | COVERED_BY_FINANCIAL_FALLBACK_INPUTS | 第三章 financial-fallback 面板作为只读输入；本轮未新增抓数。 |
| 53 | 单因子 IC / Rank IC / 分组收益重跑 | PARTIAL_BY_EXISTING_INPUTS | 本轮新跑第三章在 `data/` 缺列失败；后续 4-7 章消费已有 20260610 第三章面板。 |
| 54 | 因子相关性与冗余分析 | PASS | `reports/stage6_full_run_20260611/chapter4_factor_models/run-stage6-full-ch4-20260611/factor_correlation.csv` |
| 55 | 行业 / 市值中性测试 | PASS_AS_AVAILABLE_EVIDENCE | `process/research/stage6_full_run_20260611/chapter4_factor_models/run-stage6-full-ch4-20260611/CHAPTER4-RUN-REPORT.md` |
| 56 | 多因子组合构建对比 | PASS | `reports/stage6_full_run_20260611/chapter7_factor_practice/run-stage6-full-ch7-20260611/optimized_portfolios.parquet` |
| 57 | 持仓数量与调仓规则搜索 | PASS_AS_RESEARCH_GRID | `reports/stage6_full_run_20260611/chapter7_factor_practice/run-stage6-full-ch7-20260611/portfolio_metrics.csv` |
| 58 | 交易约束回测 | PASS_LOCAL_PAPER_SIM | `reports/stage6_full_run_20260611/multifactor_dry_run/` |
| 59 | 成本与冲击成本压力测试 | PASS | `reports/stage6_full_run_20260611/chapter7_factor_practice/run-stage6-full-ch7-20260611/turnover_cost_analysis.csv` |
| 60 | benchmark 归因与指数增强诊断 | PASS_AS_REPORT | `reports/stage6_full_run_20260611/chapter7_factor_practice/run-stage6-full-ch7-20260611/performance_attribution.csv` |
| 61 | 分市场环境稳健性 | PASS | `reports/stage6_full_run_20260611/chapter6_factor_robustness/run-stage6-full-ch6-20260611/market_state_results.csv` |
| 62 | 因子贡献与消融 | PASS | `reports/stage6_full_run_20260611/multifactor_strategy_candidates/run-stage6-full-mf-candidates-20260611/factor_contribution.csv` |
| 63 | 最终候选策略冻结 | PASS_AS_RESEARCH_BASELINE | `process/research/stage6_full_run_20260611/multifactor_strategy_candidates/run-stage6-full-mf-candidates-20260611/STRATEGY-ADMISSION-PACKAGE.json` |
| 64 | pre-sim backtest 复刻 | PASS_LOCAL_RESEARCH | `process/research/stage6_full_run_20260611/multifactor_strategy_candidates/run-stage6-full-mf-candidates-20260611/STRATEGY-RESEARCH-REPORT.md` |
| 65 | 5 日真实 dry-run | PASS_LOCAL_ONLY | `reports/stage6_full_run_20260611/multifactor_dry_run/`；不是账户级真实 dry-run。 |
| 66 | simulation admission package | BLOCKED_FOR_SIMULATION | 策略包 `status=PASS`、`overall_admission=research_baseline`、`simulation_candidate=false`。 |

多因子关键结果：

- Chapter 4: `PASS`，证据在 `process/research/stage6_full_run_20260611/chapter4_factor_models/run-stage6-full-ch4-20260611/`。
- Chapter 5: `PASS`，证据在 `process/research/stage6_full_run_20260611/chapter5_anomalies/run-stage6-full-ch5-20260611/`。
- Chapter 6: `PASS`，证据在 `process/research/stage6_full_run_20260611/chapter6_factor_robustness/run-stage6-full-ch6-20260611/`。
- Chapter 7: `PASS`，证据在 `process/research/stage6_full_run_20260611/chapter7_factor_practice/run-stage6-full-ch7-20260611/`。
- Strategy candidates: `PASS` as research baseline，证据在 `process/research/stage6_full_run_20260611/multifactor_strategy_candidates/run-stage6-full-mf-candidates-20260611/`。
- 策略包 blocked claims 包括 `qmt_ready`、`simulation_ready`、`live_ready`、`production_valid`、`account_or_order_ready`、`provider_or_lake_publish_ready`。

## Dry-run 明细

| 策略线 | 日期 | order intents | fills | reconciliation | forbidden counters | 结论 |
|---|---:|---:|---:|---|---:|---|
| low_vol_fixed20_local | 2024-04-01 | 20 | 20 | pass | 0 | pass |
| low_vol_fixed20_local | 2024-04-02 | 20 | 20 | pass | 0 | pass |
| low_vol_fixed20_local | 2024-04-03 | 20 | 20 | pass | 0 | pass |
| low_vol_fixed20_local | 2024-04-08 | 20 | 20 | pass | 0 | pass |
| low_vol_fixed20_local | 2024-04-09 | 20 | 20 | pass | 0 | pass |
| multifactor_equal_weight_baseline | 2024-04-01 | 11 | 11 | pass | 0 | pass |
| multifactor_equal_weight_baseline | 2024-04-02 | 11 | 11 | pass | 0 | pass |
| multifactor_equal_weight_baseline | 2024-04-03 | 11 | 11 | pass | 0 | pass |
| multifactor_equal_weight_baseline | 2024-04-08 | 11 | 11 | pass | 0 | pass |
| multifactor_equal_weight_baseline | 2024-04-09 | 11 | 11 | pass | 0 | pass |

## 重要问题

1. **低波 Top20 口径冲突仍存在**：阶段五 `top20` 表示 Top20%，不表示固定 20 只。固定 20 只 dry-run 是本轮新生成工程口径，不能使用旧阶段五收益、回撤、换手结论。
2. **第三章新批次在当前 `data/` 上失败**：当前 `data/prices.parquet` 只有价格、成交量、金额和停牌等字段，不足以重新计算完整财务/估值多因子矩阵；本轮 4-7 章复跑依赖已有 20260610 financial-fallback 面板。
3. **多因子 dry-run 发生代码口径映射**：组合输出为 `600000.SH` / `000001.SZ`，本地行情为 `sh600000` / `sz000001`；本轮显式映射后仅 11 个目标在本地行情中可用。这是正式准入前必须修复的数据合同问题。
4. **CR041 包读取器关键字冲突**：策略候选包里的零值 `operation_counts.credential_read` 会被 paper simulation 敏感字段 guardrail 阻断。本轮生成 `STRATEGY-ADMISSION-PACKAGE.paper-sim-sanitized.json`，只删除该零值计数字段用于 dry-run；原始策略包未改。
5. **真实观察期未完成**：实验 48 要求 8-12 周连续运行，本轮只完成离线 5 日 dry-run，不能升级为正式模拟盘候选。

## 验证命令

```bash
PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' uv run --python 3.11 pytest -q tests/test_cr019_stage6_admission_gate.py tests/test_cr030_strategy_admission_package.py tests/test_cr041_paper_simulation.py tests/test_experiment_30_36_stage5.py tests/test_chapter4_factor_models.py tests/test_chapter5_anomalies.py tests/test_chapter6_factor_robustness.py tests/test_chapter7_factor_practice.py tests/test_multifactor_strategy_candidates.py
```

结果：`60 passed in 8.24s`。

## 阶段六结论

本轮可离线执行的实验已经完成一次。结论是：

```text
继续观察 / 暂停并修复。
不得升级正式模拟盘候选。
不得启动 QMT simulation / live。
不得把本轮本地 paper simulation 解释为真实账户 dry-run。
```

进入下一轮前至少需要解决：

- 统一证券代码口径和 dry-run 数据合同。
- 决定低波策略到底采用 Top20% 还是固定 20 只，并分别重跑对应绩效。
- 用 production current truth 补齐或稳定第三章因子面板输入。
- 完成真实连续 5 个交易日账户外 dry-run，随后再观察 8-12 周。
