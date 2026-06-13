# CR-038 第七章因子投资实践报告

- run_id: `run-cr038-chapter7-factor-practice-20260610`
- status: `PASS`
- provider_fetch: `0`
- lake_write: `0`
- catalog_publish: `0`
- qmt_operation: `0`
- simulation_or_live: `0`
- credential_read: `0`

## 样本摘要

| sample_id | status | allowed_assets | alpha_rows | weight_rows | metric_rows | risk_rows | attribution_rows | cost_rows | capacity_rows |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `in_sample_2000_2019` | `PASS` | 4 | 418838 | 14340 | 478 | 3346 | 3346 | 2390 | 478 |
| `observation_2020_2026_ytd` | `PASS` | 3 | 317802 | 4560 | 152 | 1064 | 1064 | 760 | 152 |

## 组合准入摘要

| sample_id | portfolio_id | admission | capacity_evidence | simulation_candidate | mean_net_25bps |
|---|---|---|---|---|---:|
| `in_sample_2000_2019` | `equal_weight_baseline` | `research_candidate` | `proxy_available` | `false` | 0.022176 |
| `in_sample_2000_2019` | `risk_adjusted_constrained` | `research_candidate` | `proxy_available` | `false` | 0.022628 |
| `observation_2020_2026_ytd` | `equal_weight_baseline` | `research_candidate` | `proxy_available` | `false` | 0.021234 |
| `observation_2020_2026_ytd` | `risk_adjusted_constrained` | `research_watch` | `proxy_available` | `false` | 0.020553 |

## 产物

- alpha_scores: `reports/chapter7_factor_practice/run-cr038-chapter7-factor-practice-20260610/alpha_scores.parquet`
- optimized_portfolios: `reports/chapter7_factor_practice/run-cr038-chapter7-factor-practice-20260610/optimized_portfolios.parquet`
- portfolio_metrics: `reports/chapter7_factor_practice/run-cr038-chapter7-factor-practice-20260610/portfolio_metrics.csv`
- risk_exposure: `reports/chapter7_factor_practice/run-cr038-chapter7-factor-practice-20260610/risk_exposure.csv`
- performance_attribution: `reports/chapter7_factor_practice/run-cr038-chapter7-factor-practice-20260610/performance_attribution.csv`
- turnover_cost_analysis: `reports/chapter7_factor_practice/run-cr038-chapter7-factor-practice-20260610/turnover_cost_analysis.csv`
- capacity_liquidity_analysis: `reports/chapter7_factor_practice/run-cr038-chapter7-factor-practice-20260610/capacity_liquidity_analysis.csv`
- portfolio_admission_summary: `process/research/chapter7_factor_practice/run-cr038-chapter7-factor-practice-20260610/PORTFOLIO-ADMISSION-SUMMARY.json`

## 边界

本报告只允许作为项目内部组合研究证据和 CR-039 研究输入，不构成 production-valid、QMT-ready、simulation-ready、live-ready、provider-ready、lake-ready 或 publish-ready 声明。
