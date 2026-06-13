# CR-039 多因子策略候选研究报告

- run_id: `run-stage6-full-mf-candidates-20260611`
- status: `PASS`
- provider_fetch: `0`
- lake_write: `0`
- catalog_publish: `0`
- qmt_operation: `0`
- simulation_or_live: `0`
- credential_read: `0`

## 策略候选

| strategy_id | source_portfolio_id | admission | simulation_candidate | mean_net_25bps | mean_turnover | capacity_evidence |
|---|---|---|---|---:|---:|---|
| `strategy_equal_weight_baseline` | `equal_weight_baseline` | `research_baseline` | `false` | 0.021705 | 0.499984 | `proxy_available` |

## 窗口覆盖

| evaluation_window | strategy_count | rows | mean_net_25bps |
|---|---:|---:|---:|
| `in_sample_2000_2014` | 1 | 1 | 0.025280 |
| `out_of_sample_2020_2026_ytd` | 1 | 1 | 0.021234 |
| `validation_2015_2019` | 1 | 1 | 0.012706 |

## 产物

- strategy_scores: `reports/stage6_full_run_20260611/multifactor_strategy_candidates/run-stage6-full-mf-candidates-20260611/strategy_scores.parquet`
- backtest_results: `reports/stage6_full_run_20260611/multifactor_strategy_candidates/run-stage6-full-mf-candidates-20260611/backtest_results.csv`
- factor_contribution: `reports/stage6_full_run_20260611/multifactor_strategy_candidates/run-stage6-full-mf-candidates-20260611/factor_contribution.csv`
- risk_cost_summary: `reports/stage6_full_run_20260611/multifactor_strategy_candidates/run-stage6-full-mf-candidates-20260611/risk_cost_summary.csv`
- strategy_admission_package: `process/research/stage6_full_run_20260611/multifactor_strategy_candidates/run-stage6-full-mf-candidates-20260611/STRATEGY-ADMISSION-PACKAGE.json`

## 边界

本报告只允许作为本地离线研究候选和后续人工决策输入，不构成 QMT-ready、simulation-ready、live-ready、production-valid、account/order-ready、provider-ready、lake-ready 或 publish-ready 声明。
