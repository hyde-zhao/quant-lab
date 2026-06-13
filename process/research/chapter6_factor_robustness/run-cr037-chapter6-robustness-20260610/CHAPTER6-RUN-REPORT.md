# CR-037 第六章因子稳健性报告

- run_id: `run-cr037-chapter6-robustness-20260610`
- status: `PASS`
- provider_fetch: `0`
- lake_write: `0`
- catalog_publish: `0`
- qmt_operation: `0`
- simulation_or_live: `0`
- ml_training_authorized: `false`

## 样本摘要

| sample_id | status | asset_count | return_rows | rolling_ic_rows | annual_rows | market_state_rows | decay_rows | leakage_status |
|---|---|---:|---:|---:|---:|---:|---:|---|
| `in_sample_2000_2019` | `PASS` | 10 | 2219 | 2109 | 193 | 30 | 30 | `PASS` |
| `observation_2020_2026_ytd` | `PASS` | 10 | 681 | 571 | 66 | 30 | 30 | `PASS` |

## 准入摘要

| sample_id | asset_type | asset_id | admission | mean_ls | t_stat | mean_rank_ic | positive_year_ratio |
|---|---|---|---|---:|---:|---:|---:|
| `in_sample_2000_2019` | `anomaly` | `fundamental_anchor_reversal` | `watch` | 0.002948 | 1.098460 | 0.023815 | 0.473684 |
| `in_sample_2000_2019` | `anomaly` | `idiosyncratic_volatility_proxy` | `reject` | -0.014755 | -4.703716 | 0.012702 | 0.117647 |
| `in_sample_2000_2019` | `anomaly` | `valuation_extreme_spread` | `reject` | -0.001967 | -1.531937 | 0.000937 | 0.350000 |
| `in_sample_2000_2019` | `factor` | `abnormal_turnover_21_252` | `baseline` | 0.013717 | 6.045736 | 0.073406 | 1.000000 |
| `in_sample_2000_2019` | `factor` | `investment_asset_growth` | `reject` | -0.002689 | -1.313802 | -0.005526 | 0.263158 |
| `in_sample_2000_2019` | `factor` | `market_beta_252` | `reject` | -0.002218 | -1.096211 | -0.022485 | 0.300000 |
| `in_sample_2000_2019` | `factor` | `momentum_12_1` | `watch` | 0.000255 | 0.090982 | -0.001428 | 0.473684 |
| `in_sample_2000_2019` | `factor` | `profitability_roe_ttm` | `baseline` | 0.012535 | 2.842686 | 0.051946 | 0.789474 |
| `in_sample_2000_2019` | `factor` | `size_total_market_cap` | `baseline` | 0.012422 | 3.092362 | 0.043882 | 0.750000 |
| `in_sample_2000_2019` | `factor` | `value_bm` | `baseline` | 0.009350 | 3.185837 | 0.051312 | 0.700000 |
| `observation_2020_2026_ytd` | `anomaly` | `fundamental_anchor_reversal` | `watch` | 0.002251 | 0.457923 | 0.052743 | 0.666667 |
| `observation_2020_2026_ytd` | `anomaly` | `idiosyncratic_volatility_proxy` | `reject` | -0.026684 | -3.525218 | 0.023791 | 0.000000 |
| `observation_2020_2026_ytd` | `anomaly` | `valuation_extreme_spread` | `reject` | -0.006537 | -2.813429 | -0.024051 | 0.142857 |
| `observation_2020_2026_ytd` | `factor` | `abnormal_turnover_21_252` | `baseline` | 0.011714 | 2.733317 | 0.077073 | 0.714286 |
| `observation_2020_2026_ytd` | `factor` | `investment_asset_growth` | `watch` | 0.003524 | 0.952384 | 0.013819 | 0.666667 |
| `observation_2020_2026_ytd` | `factor` | `market_beta_252` | `watch` | 0.002496 | 0.438902 | -0.021428 | 0.571429 |
| `observation_2020_2026_ytd` | `factor` | `momentum_12_1` | `reject` | -0.000737 | -0.166639 | -0.032827 | 0.500000 |
| `observation_2020_2026_ytd` | `factor` | `profitability_roe_ttm` | `reject` | -0.003521 | -0.715643 | 0.001538 | 0.285714 |
| `observation_2020_2026_ytd` | `factor` | `size_total_market_cap` | `baseline` | 0.016798 | 2.575765 | 0.057385 | 0.714286 |
| `observation_2020_2026_ytd` | `factor` | `value_bm` | `candidate` | 0.006445 | 1.401979 | 0.059436 | 0.571429 |

## 护栏摘要

| sample_id | guardrail_id | status | rule |
|---|---|---|---|
| `in_sample_2000_2019` | `G-CR037-PHACKING-001` | `active` | 任何新增因子或异象必须报告全量候选、参数网格和未通过对象，禁止只汇报样本内显著结果。 |
| `in_sample_2000_2019` | `G-CR037-OOS-001` | `active` | 进入组合实践前必须至少有样本外或观察期证据，不能只凭 2000-2019 样本内 t 值准入。 |
| `in_sample_2000_2019` | `G-CR037-LEAKAGE-001` | `PASS` | feature available_at 必须早于 label_available_at；ML 研究必须使用 purge / embargo 时间切分。 |
| `in_sample_2000_2019` | `G-CR037-RUNTIME-001` | `active` | CR-037 不授权 provider fetch、lake write、publish、QMT、simulation、live、账户、订单或凭据读取。 |
| `observation_2020_2026_ytd` | `G-CR037-PHACKING-001` | `active` | 任何新增因子或异象必须报告全量候选、参数网格和未通过对象，禁止只汇报样本内显著结果。 |
| `observation_2020_2026_ytd` | `G-CR037-OOS-001` | `active` | 进入组合实践前必须至少有样本外或观察期证据，不能只凭 2000-2019 样本内 t 值准入。 |
| `observation_2020_2026_ytd` | `G-CR037-LEAKAGE-001` | `PASS` | feature available_at 必须早于 label_available_at；ML 研究必须使用 purge / embargo 时间切分。 |
| `observation_2020_2026_ytd` | `G-CR037-RUNTIME-001` | `active` | CR-037 不授权 provider fetch、lake write、publish、QMT、simulation、live、账户、订单或凭据读取。 |

## 产物

- guardrails: `docs/quality/FACTOR-RESEARCH-GUARDRAILS.md`
- robustness_returns: `reports/chapter6_factor_robustness/run-cr037-chapter6-robustness-20260610/robustness_returns.csv`
- rolling_ic: `reports/chapter6_factor_robustness/run-cr037-chapter6-robustness-20260610/rolling_ic.csv`
- annual_factor_metrics: `reports/chapter6_factor_robustness/run-cr037-chapter6-robustness-20260610/annual_factor_metrics.csv`
- market_state_results: `reports/chapter6_factor_robustness/run-cr037-chapter6-robustness-20260610/market_state_results.csv`
- decay_report: `reports/chapter6_factor_robustness/run-cr037-chapter6-robustness-20260610/decay_report.csv`
- ml_leakage_audit: `reports/chapter6_factor_robustness/run-cr037-chapter6-robustness-20260610/ml_leakage_audit.md`
- robustness_admission_summary: `process/research/chapter6_factor_robustness/run-cr037-chapter6-robustness-20260610/ROBUSTNESS-ADMISSION-SUMMARY.json`

## 边界

本报告只允许作为项目内部因子 / 异象稳健性证据和 CR-038/CR-039 输入，不构成 production-valid、QMT-ready、simulation-ready、live-ready 或 ML-model-ready 声明。
